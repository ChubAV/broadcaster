import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.billing.subscription_period import next_expiry
from app.config import get_settings
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.billing_service import add_messages
from app.services.billing_cache import invalidate_balance_cache

logger = structlog.get_logger()

# Предметы покупки. Строки живут здесь, потому что их читает и пишет один этот
# модуль; ревизия 0017 выписывает свои копии отдельно и намеренно (правило 0013).
KIND_PACKAGE = "package"
KIND_SUBSCRIPTION = "subscription"


def _configure_yookassa():
    settings = get_settings()
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key


async def create_payment(
    db: AsyncSession,
    user_id: int,
    price: str,
    *,
    kind: str,
    package_name: str | None = None,
    messages_count: int | None = None,
    plan: str | None = None,
) -> dict:
    """Создаёт платёж в ЮKassa и строку `payments` под него.

    `kind` ОБЯЗАТЕЛЕН И KEYWORD-ONLY намеренно. Сигнатура стала строже, чем
    была: необновлённый вызывающий обязан упасть громко на вызове, а не тихо
    записать платёж с угаданным предметом покупки — угаданный предмет
    обнаружился бы только на вебхуке, то есть после того, как деньги списаны.
    """
    _configure_yookassa()
    settings = get_settings()

    if kind == KIND_SUBSCRIPTION:
        description = f"Подписка «{plan}»"
        # Ключ `kind` в metadata обязателен: без него в личном кабинете ЮKassa
        # два предмета покупки неразличимы, и вопрос «за что этот платёж»
        # разрешается только сверкой со своей базой (T-05-08).
        metadata = {
            "user_id": str(user_id),
            "kind": kind,
            "plan": str(plan or ""),
        }
    else:
        description = f"Пополнение баланса: {package_name}"
        metadata = {
            "user_id": str(user_id),
            "kind": kind,
            "messages_count": str(messages_count),
            "package_name": str(package_name or ""),
        }

    idempotency_key = str(uuid.uuid4())
    payment = YooPayment.create(
        {
            "amount": {"value": price, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
            },
            "capture": True,
            "description": description,
            "metadata": metadata,
        },
        idempotency_key,
    )

    db_payment = Payment(
        user_id=user_id,
        yookassa_payment_id=payment.id,
        status="pending",
        amount_value=price,
        amount_currency="RUB",
        kind=kind,
        plan=plan,
        messages_count=messages_count,
        package_name=package_name,
    )
    db.add(db_payment)
    await db.commit()

    logger.info(
        "payment_created",
        user_id=user_id,
        yookassa_id=payment.id,
        amount=price,
        kind=kind,
        plan=plan,
        messages=messages_count,
    )

    return {
        "confirmation_url": payment.confirmation.confirmation_url,
        "payment_id": payment.id,
    }


async def handle_webhook(
    db: AsyncSession, event: str, payment_data: dict
) -> bool:
    """Выдаёт оплаченное по подтверждённому уведомлению об успешном платеже.

    ПОРЯДОК ПРОВЕРОК ЗНАЧИМ И МЕНЯТЬСЯ НЕ ДОЛЖЕН: событие → наличие `id` →
    строка платежа в СВОЕЙ базе → идемпотентность → и только потом ветвление по
    предмету покупки.

    Проверка идемпотентности стоит ДО ветвления намеренно. Это единственное
    место, где живёт защита от двойного начисления (T-05-04); её копия внутри
    каждой ветки рано или поздно разойдётся с остальными — достаточно, чтобы
    третью ветку добавили, забыв скопировать.

    ПРЕДМЕТ ПОКУПКИ РЕШАЕТ КОЛОНКА `kind` ИЗ БД, никогда `metadata`
    уведомления: тело уведомления приезжает из сети и источником истины быть не
    может (T-05-02). Пользователь берётся оттуда же — из строки платежа.
    """
    if event != WebhookNotificationEventType.PAYMENT_SUCCEEDED:
        return False

    obj = payment_data.get("object", {})
    yookassa_id = obj.get("id")
    if not yookassa_id:
        logger.warning("webhook_missing_payment_id")
        return False

    result = await db.execute(
        select(Payment).where(Payment.yookassa_payment_id == yookassa_id)
    )
    db_payment = result.scalar_one_or_none()
    if db_payment is None:
        logger.warning("webhook_payment_not_found", yookassa_id=yookassa_id)
        return False

    if db_payment.status == "succeeded":
        logger.info("webhook_payment_already_processed", yookassa_id=yookassa_id)
        return True

    now = datetime.now(timezone.utc)
    db_payment.status = "succeeded"
    db_payment.confirmed_at = now

    if db_payment.kind == KIND_SUBSCRIPTION:
        await _extend_subscription(db, db_payment, now)
        await db.commit()
        logger.info(
            "subscription_payment_succeeded",
            user_id=db_payment.user_id,
            yookassa_id=yookassa_id,
            amount=db_payment.amount_value,
            plan=db_payment.plan,
        )
        return True

    new_balance = await add_messages(
        db,
        db_payment.user_id,
        db_payment.messages_count,
        type="purchase",
        description=f"Покупка: {db_payment.package_name}",
        payment_id=yookassa_id,
    )
    await db.commit()
    await invalidate_balance_cache(db_payment.user_id)

    logger.info(
        "payment_succeeded",
        user_id=db_payment.user_id,
        yookassa_id=yookassa_id,
        messages=db_payment.messages_count,
        new_balance=new_balance,
    )
    return True


async def _extend_subscription(
    db: AsyncSession, db_payment: Payment, now: datetime
) -> None:
    """Двигает срок подписки владельца платежа или заводит её впервые.

    ЗАПРОС АКТИВНОЙ ПОДПИСКИ ПОВТОРЯЕТ `get_shell_context` ДОСЛОВНО
    (app/pages/common.py:397-404): те же три условия, та же сортировка, тот же
    `limit(1)`. Уникального ограничения на `subscriptions.user_id` в схеме нет,
    поэтому строк у одного пользователя может оказаться несколько — и
    одинаковый запрос у ЧИТАТЕЛЯ (шелл показывает тариф и срок) и у ПИСАТЕЛЯ
    (этот код) единственное, что держит их в согласии. Разойдись они, продление
    двигало бы одну строку, а пользователь видел бы другую.

    Срок двигается ТОЛЬКО ЗДЕСЬ — то есть только по подтверждённому платежу.
    Возврат браузера с `return_url` доказательством оплаты не является и
    происходит в том числе при отказе (D-05, T-05-05).
    """
    subscription = (
        await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == db_payment.user_id,
                Subscription.is_active.is_(True),
            )
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if subscription is not None:
        subscription.expires_at = next_expiry(subscription.expires_at, now)
        if db_payment.plan:
            subscription.plan = db_payment.plan
        return

    db.add(
        Subscription(
            user_id=db_payment.user_id,
            plan=db_payment.plan or "free",
            expires_at=next_expiry(None, now),
            is_active=True,
        )
    )

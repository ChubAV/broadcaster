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

STATUS_PENDING = "pending"
STATUS_SUCCEEDED = "succeeded"
STATUS_CANCELED = "canceled"

# ТЕРМИНАЛЬНЫЕ СТАТУСЫ — те, из которых платёж больше не выходит. Их два, и
# защита от повторной обработки написана через это множество, а не через
# перечисление в каждой ветке: копия в ветке рано или поздно разойдётся с
# оригиналом — достаточно, чтобы третью ветку добавили, забыв её скопировать.
TERMINAL_STATUSES = frozenset({STATUS_SUCCEEDED, STATUS_CANCELED})

# ЗНАКОМЫЕ СОБЫТИЯ — КОНСТАНТАМИ SDK, НИКОГДА СТРОКОВЫМИ ЛИТЕРАЛАМИ (T-05-12).
# Опечатка в литерале не поднимает ошибку: событие просто молча не
# обрабатывается, платёж остаётся pending, а обнаруживается это на боевом
# приёме денег. Константа с опечаткой падает AttributeError на импорте модуля.
#
# В SDK объявлено семь событий; refund.succeeded, payout.* и deal.closed этой
# фазе не принадлежат и по-прежнему возвращают False.
KNOWN_EVENTS = frozenset(
    {
        WebhookNotificationEventType.PAYMENT_SUCCEEDED,
        WebhookNotificationEventType.PAYMENT_CANCELED,
    }
)


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
    """Доводит платёж до терминального статуса по подтверждённому уведомлению.

    ПОРЯДОК ПРОВЕРОК ЗНАЧИМ И МЕНЯТЬСЯ НЕ ДОЛЖЕН: событие → наличие `id` →
    строка платежа в СВОЕЙ базе → терминальный статус → и только потом
    ветвление по исходу платежа и по предмету покупки.

    Проверка терминального статуса стоит ДО ветвления намеренно. Это
    единственное место, где живёт защита от двойного начисления (T-05-04), и
    ровно она же не даёт припоздавшему уведомлению об отмене отнять уже
    выданное (T-05-10): платёж в `succeeded` не переводится в `canceled`.

    ЗНАКОМЫХ СОБЫТИЙ ДВА — успех и отмена (D-16). До этого отмена возвращала
    False, и отменённый платёж навсегда оставался `pending`: история показывала
    бы «в обработке» там, где денег не взяли вовсе — то есть неправду, а не
    отсутствие данных (BILL-07).

    ПРЕДМЕТ ПОКУПКИ РЕШАЕТ КОЛОНКА `kind` ИЗ БД, никогда `metadata`
    уведомления: тело уведомления приезжает из сети и источником истины быть не
    может (T-05-02). Пользователь берётся оттуда же — из строки платежа.
    """
    if event not in KNOWN_EVENTS:
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

    if db_payment.status in TERMINAL_STATUSES:
        logger.info("webhook_payment_already_processed", yookassa_id=yookassa_id)
        return True

    now = datetime.now(timezone.utc)

    if event == WebhookNotificationEventType.PAYMENT_CANCELED:
        # ВЕТКА ОТМЕНЫ НАМЕРЕННО НИЧЕГО НЕ НАЧИСЛЯЕТ: ни сообщений, ни дней
        # подписки. Она только записывает исход — и тем снимает платёж с вечного
        # `pending`. Баланс при этом не изменился, поэтому и инвалидировать
        # кэш нечего.
        #
        # Момент решения пишется в СУЩЕСТВУЮЩУЮ колонку времени подтверждения:
        # колонка одна, и её смысл — «когда платёж перешёл в терминальное
        # состояние». Второй колонки под отмену D-15 не заводит, а расширять
        # решение владельца этот код не вправе.
        #
        # Причина отмены (`cancellation_details` в теле уведомления) не пишется
        # и не логируется (T-05-13): её не называет ни требование, ни макет, а
        # разбор чужой структуры ради неиспользуемого поля — лишний контракт с
        # внешним форматом.
        db_payment.status = STATUS_CANCELED
        db_payment.confirmed_at = now
        await db.commit()

        logger.info(
            "payment_canceled",
            user_id=db_payment.user_id,
            yookassa_id=yookassa_id,
            kind=db_payment.kind,
        )
        return True

    db_payment.status = STATUS_SUCCEEDED
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

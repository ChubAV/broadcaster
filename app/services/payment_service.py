import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration, Payment as YooPayment

from app.config import get_settings
from app.models.payment import Payment
from app.services.billing_service import add_messages
from app.services.billing_cache import invalidate_balance_cache

logger = structlog.get_logger()


def _configure_yookassa():
    settings = get_settings()
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key


async def create_payment(
    db: AsyncSession,
    user_id: int,
    package_name: str,
    messages_count: int,
    price: str,
) -> dict:
    _configure_yookassa()
    settings = get_settings()

    idempotency_key = str(uuid.uuid4())
    payment = YooPayment.create(
        {
            "amount": {"value": price, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
            },
            "capture": True,
            "description": f"Пополнение баланса: {package_name}",
            "metadata": {
                "user_id": str(user_id),
                "messages_count": str(messages_count),
                "package_name": package_name,
            },
        },
        idempotency_key,
    )

    db_payment = Payment(
        user_id=user_id,
        yookassa_payment_id=payment.id,
        status="pending",
        amount_value=price,
        amount_currency="RUB",
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
        messages=messages_count,
    )

    return {
        "confirmation_url": payment.confirmation.confirmation_url,
        "payment_id": payment.id,
    }


async def handle_webhook(
    db: AsyncSession, event: str, payment_data: dict
) -> bool:
    if event != "payment.succeeded":
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

    db_payment.status = "succeeded"
    db_payment.confirmed_at = datetime.now(timezone.utc)

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

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.models.user import User
from app.models.payment import Payment
from app.services.payment_service import create_payment, handle_webhook
from app.services.billing_service import get_balance, add_messages


@pytest.mark.asyncio
async def test_create_payment(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    mock_yoo_payment = MagicMock()
    mock_yoo_payment.id = "yoo_123"
    mock_yoo_payment.confirmation = MagicMock()
    mock_yoo_payment.confirmation.confirmation_url = "https://yookassa.ru/pay/123"

    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "https://app.com/billing"
    mock_settings.app_name = "Broadcaster"

    with patch("app.services.payment_service.get_settings", return_value=mock_settings), \
         patch("app.services.payment_service.YooPayment.create", return_value=mock_yoo_payment):
        result = await create_payment(
            db_session,
            user_id=user.id,
            kind="package",
            package_name="100 messages",
            messages_count=100,
            price="149.00",
        )

    assert result["confirmation_url"] == "https://yookassa.ru/pay/123"
    assert result["payment_id"] == "yoo_123"


@pytest.mark.asyncio
async def test_handle_webhook_success(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    payment = Payment(
        user_id=user.id,
        yookassa_payment_id="yoo_456",
        status="pending",
        amount_value="149.00",
        amount_currency="RUB",
        messages_count=100,
        package_name="100 messages",
    )
    db_session.add(payment)
    await db_session.commit()

    with patch("app.services.payment_service.invalidate_balance_cache", new_callable=AsyncMock):
        processed = await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_456"}},
        )

    assert processed is True
    assert await get_balance(db_session, user.id) == 100


@pytest.mark.asyncio
async def test_handle_webhook_wrong_event(db_session):
    processed = await handle_webhook(
        db_session,
        event="payment.canceled",
        payment_data={"object": {"id": "yoo_789"}},
    )
    assert processed is False


@pytest.mark.asyncio
async def test_handle_webhook_idempotent(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    payment = Payment(
        user_id=user.id,
        yookassa_payment_id="yoo_dup",
        status="succeeded",
        amount_value="149.00",
        amount_currency="RUB",
        messages_count=100,
        package_name="100 messages",
        confirmed_at=datetime.now(timezone.utc),
    )
    db_session.add(payment)
    await db_session.commit()

    # Already processed — should return True but not add more balance
    processed = await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": "yoo_dup"}},
    )
    assert processed is True
    assert await get_balance(db_session, user.id) == 0

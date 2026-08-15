"""Сквозная линия BILL-05: форма тарифа → ЮKassa → вебхук → сдвинутый срок.

Тест намеренно идёт ЧЕРЕЗ HTTP-форму, а не через вызов сервиса: предмет проверки —
что все семь слоёв (конфиг → страница → сервис → модель → вебхук → подписка →
шаблон) соединены, а не что каждый по отдельности работает. Единственная
подменённая часть — сеть ЮKassa.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import handle_webhook

SAME_ORIGIN = {"Origin": "http://test"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"


def _yoo_mocks(payment_id: str = "yoo_sub_1"):
    """Мок сети ЮKassa по образцу tests/test_services/test_payment_service.py."""
    mock_payment = MagicMock()
    mock_payment.id = payment_id
    mock_payment.confirmation = MagicMock()
    mock_payment.confirmation.confirmation_url = CONFIRMATION_URL

    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "http://test/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_payment, mock_settings


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _subscribe(client: AsyncClient, plan: str = "basic", headers=None):
    mock_payment, mock_settings = _yoo_mocks()
    with patch(
        "app.services.payment_service.get_settings", return_value=mock_settings
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=mock_payment
    ):
        return await client.post(
            "/billing/subscribe",
            data={"plan": plan},
            headers=SAME_ORIGIN if headers is None else headers,
            follow_redirects=False,
        )


@pytest.mark.asyncio
async def test_subscribe_redirects_to_the_yookassa_confirmation_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _subscribe(authed_client)

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL

    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.kind == "subscription"
    assert payment.plan == "basic"
    assert payment.messages_count is None
    # Цена приезжает ИЗ КОНФИГА по идентификатору плана и в машинном формате
    # ЮKassa — подпись макета с неразрывным пробелом здесь была бы отказом API.
    assert payment.amount_value == "1490.00"


@pytest.mark.asyncio
async def test_subscribe_reads_the_price_from_config_not_from_the_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Поле цены в форме игнорируется: покупатель не назначает себе цену."""
    mock_payment, mock_settings = _yoo_mocks()
    with patch(
        "app.services.payment_service.get_settings", return_value=mock_settings
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=mock_payment
    ):
        response = await authed_client.post(
            "/billing/subscribe",
            data={"plan": "basic", "price": "1.00"},
            headers=SAME_ORIGIN,
            follow_redirects=False,
        )

    assert response.status_code == 302
    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.amount_value == "1490.00"


@pytest.mark.asyncio
async def test_subscribe_rejects_a_cross_site_origin(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _subscribe(
        authed_client, headers={"Origin": "https://evil.example"}
    )

    assert response.status_code == 403
    count = await db_session.scalar(select(func.count()).select_from(Payment))
    assert count == 0, "отклонённый источник не должен создавать платёж"


@pytest.mark.asyncio
async def test_subscribe_rejects_the_free_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _subscribe(authed_client, plan="free")

    assert response.status_code == 302
    assert response.headers["location"] == "/billing"
    count = await db_session.scalar(select(func.count()).select_from(Payment))
    assert count == 0


@pytest.mark.asyncio
async def test_subscribe_rejects_an_unknown_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _subscribe(authed_client, plan="platinum")

    assert response.status_code == 302
    assert response.headers["location"] == "/billing"
    count = await db_session.scalar(select(func.count()).select_from(Payment))
    assert count == 0


@pytest.mark.asyncio
async def test_webhook_creates_the_first_subscription(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _subscribe(authed_client)
    user = await _current_user(db_session)

    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ) as add_messages:
        processed = await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_sub_1"}},
        )

    assert processed is True
    add_messages.assert_not_awaited(), "подписка не начисляет сообщений"

    subscription = (
        await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
    ).scalar_one()
    assert subscription.plan == "basic"
    assert subscription.is_active is True

    expires_at = subscription.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc) + timedelta(days=27)


@pytest.mark.asyncio
async def test_webhook_extends_an_active_subscription_without_burning_the_remainder(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _subscribe(authed_client)
    user = await _current_user(db_session)

    current = datetime.now(timezone.utc) + timedelta(days=10)
    db_session.add(
        Subscription(
            user_id=user.id, plan="basic", expires_at=current, is_active=True
        )
    )
    await db_session.commit()

    with patch("app.services.payment_service.add_messages", new_callable=AsyncMock):
        await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_sub_1"}},
        )

    rows = (
        (
            await db_session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1, "продление не должно заводить вторую строку"

    expires_at = rows[0].expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    # Считается от прежнего срока, а не от сегодняшнего дня: остаток оплачен.
    assert expires_at > current + timedelta(days=27)


@pytest.mark.asyncio
async def test_a_repeated_webhook_does_not_move_the_date_twice(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _subscribe(authed_client)
    user = await _current_user(db_session)

    with patch("app.services.payment_service.add_messages", new_callable=AsyncMock):
        await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_sub_1"}},
        )
    first = (
        await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
    ).scalar_one()
    first_expiry = first.expires_at

    with patch("app.services.payment_service.add_messages", new_callable=AsyncMock):
        processed = await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_sub_1"}},
        )

    assert processed is True
    rows = (
        (
            await db_session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].expires_at == first_expiry


@pytest.mark.asyncio
async def test_returning_to_billing_does_not_move_the_date(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Возврат браузера с ЮKassa — не доказательство оплаты (D-05, T-05-05)."""
    await _subscribe(authed_client)
    user = await _current_user(db_session)

    response = await authed_client.get("/billing")
    assert response.status_code == 200

    count = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user.id)
    )
    assert count == 0, "GET /billing не имеет права создавать подписку"


@pytest.mark.asyncio
async def test_the_billing_page_renders_a_real_form_per_paid_plan(
    authed_client: AsyncClient
):
    """Базовый путь покупки обязан работать без JavaScript."""
    response = await authed_client.get("/billing")

    assert response.status_code == 200
    body = response.text
    assert 'action="/billing/subscribe"' in body
    assert 'value="basic"' in body
    assert 'value="pro"' in body
    assert 'value="free"' not in body, "бесплатный тариф не продаётся"

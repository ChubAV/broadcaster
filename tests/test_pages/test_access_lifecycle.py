"""Сквозная дорожка плоской модели: пробный срок → истечение → оплата → доступ.

ПРЕДМЕТ ФАЙЛА — ОДИН ЧЕЛОВЕК, ПРОШЕДШИЙ ВЕСЬ ПУТЬ, А НЕ СЕМЬ РАЗРОЗНЕННЫХ
СВОЙСТВ. Каждый слой новой модели затрагивается здесь ровно один раз и на
настоящем коде: заведение пробной строки при регистрации, предикат доступа,
пер-роутерная зависимость отказа, плоская цена, уезжающая в SDK, и защита от
повторной доставки уведомления. Разложить это по семи файлам значило бы
проверить семь слоёв по отдельности и НЕ проверить, что они стыкуются, — а
стыковка и есть предмет плана 05.1-01.

ПОЧЕМУ ОДИН ТЕСТ, А НЕ СЕМЬ. Утверждения дорожки НЕ НЕЗАВИСИМЫ: пятое имеет
смысл только после третьего (просроченный доступ), шестое — только после пятого
(намерение оплаты существует), седьмое — только после шестого. Семь тестов
пересобирали бы состояние заново каждый, то есть проверяли бы семь РАЗНЫХ
пользователей вместо одного человека с историей. Точечные свойства этих же
слоёв закрепляют `test_trial.py` и `test_access_gate.py`; здесь проверяется
СВЯЗНОСТЬ.

УВЕДОМЛЕНИЕ ЮKASSA ВЫЗЫВАЕТСЯ НАПРЯМУЮ ЧЕРЕЗ `handle_webhook`, А НЕ HTTP-МАРШРУТОМ,
И ЭТО НЕ УПРОЩЕНИЕ. Гард подлинности уведомления по адресу источника
(`_is_trusted_source`, T-05.1-08) этой дорожке не принадлежит: она проверяет,
что подтверждённая оплата возвращает доступ, а не кто имеет право её подтвердить.
Пройти через маршрут значило бы либо ослабить гард настройкой, либо подделать
адрес источника — то есть тронуть защиту, которую план обязался не трогать ни
одной строкой. Сам гард закреплён своими тестами в
`tests/test_pages/test_billing_payment_errors.py`.
"""
from datetime import datetime, timedelta, timezone
import re

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, patch

from app.constants import TRIAL_DAYS
from app.models.email_verification import EmailVerificationCode
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import KIND_SUBSCRIPTION, handle_webhook

EMAIL = "lifecycle@test.com"
PASSWORD = "securepass123"

SAME_ORIGIN = {"Origin": "http://test"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"
YOOKASSA_PAYMENT_ID = "yoo_lifecycle"

# ЦЕНА ДОСТУПА ВЫПИСАНА ЗДЕСЬ ДОСЛОВНО И НЕ ЧИТАЕТСЯ ИЗ НАСТРОЙКИ. Предмет
# проверки — что в SDK уезжает ИМЕННО ЭТА строка машинного формата ЮKassa;
# тест, берущий значение из того же источника, что и код, утверждал бы лишь
# «значение равно самому себе» и пережил бы подмену умолчания на «3 000,00 ₽».
ACCESS_PRICE = "3000.00"

# Страницы, создающие ценность. Их закрывает истёкший доступ — и ровно они
# перечислены в гейте перечня `test_access_gate.py`.
VALUE_PAGE = "/ads"

EXPIRED_LOCATION = "/billing?expired=1"


def _yoo_settings():
    """Мок настроек ЮKassa по образцу tests/test_pages/test_billing_payment_errors.py."""
    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "http://test/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_settings


def _yoo_payment(payment_id: str):
    mock_payment = MagicMock()
    mock_payment.id = payment_id
    mock_payment.confirmation = MagicMock()
    mock_payment.confirmation.confirmation_url = CONFIRMATION_URL
    return mock_payment


async def _register_through_the_pages(client: AsyncClient, db: AsyncSession) -> None:
    """Три шага страничной регистрации — ровно как их проходит человек.

    Форма подтверждения кода взята из разметки, а не собрана токеном в тесте:
    предмет дорожки — настоящий путь регистрации, и токен, выданный в обход
    страницы, проверял бы наш способ его выдать, а не путь пользователя.
    """
    response = await client.post("/register/send-code", data={"email": EMAIL})
    token = re.search(r'name="token" value="([^"]+)"', response.text).group(1)

    code_record = (
        await db.execute(
            select(EmailVerificationCode).where(EmailVerificationCode.email == EMAIL)
        )
    ).scalar_one()

    response = await client.post(
        "/register/verify", data={"token": token, "code": code_record.code}
    )
    verified_token = re.search(r'name="token" value="([^"]+)"', response.text).group(1)

    response = await client.post(
        "/register/complete",
        data={"token": verified_token, "name": "Lifecycle", "password": PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302, "регистрация не завершилась"
    assert "/dashboard" in response.headers["location"]


async def _active_rows(db: AsyncSession, user_id: int) -> list[Subscription]:
    return list(
        (
            await db.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.is_active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )


def _aware(value: datetime) -> datetime:
    """SQLite отдаёт колонку с таймзоной NAIVE — сравнивать без приведения нельзя."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_the_trial_expires_and_payment_reopens_access(
    client: AsyncClient, db_session: AsyncSession
):
    """Весь путь плоской модели одним человеком, семью утверждениями подряд."""
    # --- 1. Регистрация заводит пробный срок --------------------------------
    before = datetime.now(timezone.utc)
    await _register_through_the_pages(client, db_session)

    user = (
        await db_session.execute(select(User).where(User.email == EMAIL))
    ).scalar_one()

    rows = await _active_rows(db_session, user.id)
    assert len(rows) == 1, (
        f"после регистрации активных подписок {len(rows)}, а обещана ровно одна"
    )
    trial_expiry = _aware(rows[0].expires_at)
    assert trial_expiry >= before + timedelta(days=TRIAL_DAYS) - timedelta(minutes=1)
    assert trial_expiry <= datetime.now(timezone.utc) + timedelta(
        days=TRIAL_DAYS
    ) + timedelta(minutes=1)

    # --- 2. Внутри пробного срока страница создания ценности открыта ---------
    response = await client.get(VALUE_PAGE, follow_redirects=False)
    assert response.status_code == 200, (
        "пробный срок обещан «в полном объёме», а страница закрыта"
    )

    # --- 3. Истёкший срок закрывает её и НАЗЫВАЕТ, куда идти ----------------
    rows[0].expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()

    response = await client.get(VALUE_PAGE, follow_redirects=False)
    assert response.status_code == 302, (
        f"истёкший доступ отвечает {response.status_code}, а обещан редирект"
    )
    assert response.headers["location"] == EXPIRED_LOCATION

    # --- 4. Путь к оплате и вход НЕ закрыты (T-05.1-03) ---------------------
    # Гейт доступа не имеет права запереть человека в системе, из которой он не
    # может ни заплатить, ни войти: это отказ продукта, а не защита.
    billing = await client.get("/billing", follow_redirects=False)
    assert billing.status_code == 200, (
        f"страница оплаты закрыта истёкшим доступом ({billing.status_code}) — "
        "человеку нечем восстановить доступ"
    )
    login = await client.get("/login", follow_redirects=False)
    assert login.status_code == 200, "страница входа закрыта истёкшим доступом"

    # --- 5. Форма оплаты не несёт НИ ОДНОГО поля, цена читается сервером ----
    with patch(
        "app.services.payment_service.get_settings", return_value=_yoo_settings()
    ), patch(
        "app.services.payment_service.YooPayment.create",
        return_value=_yoo_payment(YOOKASSA_PAYMENT_ID),
    ):
        paid = await client.post(
            "/billing/subscribe",
            data={},
            headers=SAME_ORIGIN,
            follow_redirects=False,
        )

    assert paid.status_code == 302
    assert paid.headers["location"] == CONFIRMATION_URL, (
        "пустая форма оплаты не увела на ЮKassa"
    )

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == YOOKASSA_PAYMENT_ID)
        )
    ).scalar_one()
    assert payment.kind == KIND_SUBSCRIPTION
    assert payment.amount_value == ACCESS_PRICE, (
        f"в SDK уехала сумма {payment.amount_value!r}, а доступ стоит "
        f"{ACCESS_PRICE!r} — одним литералом настройки"
    )
    assert payment.plan is None, (
        "тарифа больше нет, а платёж унёс его значение — второй источник правды"
    )

    # --- 6. Подтверждённое уведомление возвращает доступ --------------------
    now = datetime.now(timezone.utc)
    processed = await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": YOOKASSA_PAYMENT_ID}},
    )
    assert processed is True

    rows = await _active_rows(db_session, user.id)
    assert len(rows) == 1, "оплата завела вторую активную подписку"
    reopened = _aware(rows[0].expires_at)
    assert reopened > now, (
        "срок после оплаты остался в прошлом — доступ не восстановлен"
    )

    response = await client.get(VALUE_PAGE, follow_redirects=False)
    assert response.status_code == 200, (
        "оплата подтверждена, а страница создания ценности всё ещё закрыта"
    )

    # --- 7. Повторная доставка того же уведомления срок НЕ двигает ----------
    processed = await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": YOOKASSA_PAYMENT_ID}},
    )
    assert processed is True

    rows = await _active_rows(db_session, user.id)
    assert len(rows) == 1
    assert _aware(rows[0].expires_at) == reopened, (
        "повторная доставка сдвинула срок второй раз — месяц подарен"
    )

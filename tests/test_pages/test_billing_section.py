"""Раздел «Тарифы» целиком: один экран и обе оплаты настоящими формами.

Предмет файла — СБОРКА раздела (BILL-05 / BILL-06 / BILL-07): что один маршрут
`GET /billing` отдаёт все пять блоков экрана сразу (D-18), что список платежей
принадлежит владельцу и называет свой потолок (D-17), и что покупка пакета
сообщений идёт формой `POST`, а не асинхронным запросом из скрипта (D-20).

ЧЕГО ЗДЕСЬ НЕТ.

- Арифметики осей тарифа: её держит `tests/test_application/test_plan_usage.py`.
  Здесь проверяется, что оси ДОЕХАЛИ до контекста в нужном порядке, а не как
  они посчитаны — два теста одного свойства расходятся при первой правке.
- Разметки: её заводит план 05-05. Поэтому утверждения идут по КОНТЕКСТУ
  шаблона, а не по HTML: контекст — это контракт между обработчиком и
  разметкой, и он обязан быть верным до того, как разметку напишут.
- Сквозной линии подписки (форма → вебхук → срок): она целиком в
  `tests/test_pages/test_billing_subscription.py`.

ПОЧЕМУ КОНТЕКСТ СНИМАЕТСЯ ПОДМЕНОЙ, А НЕ ЧИТАЕТСЯ ИЗ ОТВЕТА. Транспорт httpx
отдаёт только тело ответа; расширение Starlette, кладущее контекст рядом с
ответом, этим транспортом не включается. Подменяется РОВНО метод отрисовки, и
подменённый зовёт настоящий: страница рендерится по-честному, а тест видит то,
что в неё уехало.
"""
import re
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.billing.plan_usage import AXIS_ORDER
from app.constants import PAYMENT_LIST_CAP
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.pages.common import templates

BILLING_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "billing.py"

SAME_ORIGIN = {"Origin": "http://test"}
CROSS_SITE = {"Origin": "https://evil.example"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"

# Первый пакет умолчания конфига: 100 сообщений за 149.00.
FIRST_PACKAGE_INDEX = "0"
FIRST_PACKAGE_PRICE = "149.00"
FIRST_PACKAGE_COUNT = 100


# --- Инструменты --------------------------------------------------------------


@contextmanager
def rendered_context():
    """Контекст, уехавший в шаблон последнего отрисованного ответа."""
    captured: dict = {}
    original = templates.TemplateResponse

    def spy(*args, **kwargs):
        context = args[1] if len(args) > 1 else (kwargs.get("context") or {})
        captured.clear()
        captured.update(context)
        return original(*args, **kwargs)

    with patch.object(templates, "TemplateResponse", spy):
        yield captured


def _handler_source(signature: str) -> str:
    """Тело обработчика — от его объявления до следующего маршрута."""
    source = BILLING_PY.read_text(encoding="utf-8")
    rest = source[source.index(signature) :]
    end = rest.find("\n@router")
    return rest if end == -1 else rest[:end]


def _yoo_mocks(payment_id: str = "yoo_pkg_1"):
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


async def _purchase(client: AsyncClient, data: dict | None = None, headers=None):
    mock_payment, mock_settings = _yoo_mocks()
    with patch(
        "app.services.payment_service.get_settings", return_value=mock_settings
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=mock_payment
    ):
        return await client.post(
            "/billing/purchase",
            data={"package_index": FIRST_PACKAGE_INDEX} if data is None else data,
            headers=SAME_ORIGIN if headers is None else headers,
            follow_redirects=False,
        )


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _stranger(db: AsyncSession) -> User:
    user = User(email="stranger@test.com", password_hash="h", name="S")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


_payment_seq = 0


def _payment_row(user_id: int, *, status: str = "succeeded", created_at=None) -> Payment:
    """Строка `payments`. `created_at` ставится ЯВНО: у колонки есть умолчание."""
    global _payment_seq
    _payment_seq += 1
    return Payment(
        user_id=user_id,
        yookassa_payment_id=f"yoo_seed_{_payment_seq}",
        status=status,
        amount_value="1490.00",
        amount_currency="RUB",
        kind="subscription",
        plan="basic",
        created_at=created_at or datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
    )


async def _seed_payments(db: AsyncSession, user_id: int, count: int) -> None:
    db.add_all([_payment_row(user_id) for _ in range(count)])
    await db.commit()


async def _payments_count(db: AsyncSession) -> int:
    return await db.scalar(select(func.count()).select_from(Payment))


# =============================================================================
# Экран раздела: все блоки одним маршрутом (D-18)
# =============================================================================


@pytest.mark.asyncio
async def test_the_section_redirects_an_anonymous_visitor_to_login(
    client: AsyncClient,
):
    response = await client.get("/billing", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_the_section_carries_every_block_of_the_screen(
    authed_client: AsyncClient,
):
    """Пять блоков макета приезжают ОДНИМ маршрутом: ни табов, ни второго пути."""
    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    for key in (
        "subscription",
        "usage",
        "plans",
        "balance_info",
        "packages",
        "transactions",
        "payments",
    ):
        assert key in context, f"блок «{key}» не доехал до разметки"
    assert context["active_page"] == "billing"


@pytest.mark.asyncio
async def test_the_section_carries_the_four_axes_in_the_layout_order(
    authed_client: AsyncClient,
):
    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    axes = context["usage"]
    assert len(axes) == 4
    assert tuple(axis.key for axis in axes) == AXIS_ORDER


@pytest.mark.asyncio
async def test_the_section_carries_the_plans_from_the_config(
    authed_client: AsyncClient,
):
    """Список планов разбирается В ОБРАБОТЧИКЕ и уезжает готовым (Pitfall 10)."""
    with rendered_context() as context:
        await authed_client.get("/billing")

    assert [plan["id"] for plan in context["plans"]] == ["free", "basic", "pro"]


@pytest.mark.asyncio
async def test_the_section_shows_only_the_owners_payments(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужой денежный журнал не виден: владение — предикатом (T-05-20)."""
    owner = await _current_user(db_session)
    stranger = await _stranger(db_session)
    await _seed_payments(db_session, owner.id, 2)
    await _seed_payments(db_session, stranger.id, 3)

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert len(context["payments"]) == 2
    assert {row.user_id for row in context["payments"]} == {owner.id}


@pytest.mark.asyncio
async def test_the_payment_list_cap_names_itself(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сработавший потолок ОБЪЯВЛЕН в контексте, а не выражен тихой обрезкой."""
    owner = await _current_user(db_session)
    await _seed_payments(db_session, owner.id, PAYMENT_LIST_CAP + 1)

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["payments_truncated"] is True
    assert context["payments_total"] == PAYMENT_LIST_CAP + 1
    assert len(context["payments"]) == PAYMENT_LIST_CAP


@pytest.mark.asyncio
async def test_a_full_list_at_the_cap_is_not_reported_truncated(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ровно на потолке список ПОЛОН — сказать «показано не всё» было бы ложью."""
    owner = await _current_user(db_session)
    await _seed_payments(db_session, owner.id, PAYMENT_LIST_CAP)

    with rendered_context() as context:
        await authed_client.get("/billing")

    assert context["payments_truncated"] is False
    assert len(context["payments"]) == PAYMENT_LIST_CAP


def test_the_handler_names_the_project_cap_and_checks_it_before_building():
    """Потолок сверяется ДО выборки списка, и это ТА ЖЕ константа проекта."""
    body = _handler_source("async def billing_page(")

    assert "PAYMENT_LIST_CAP" in body, "потолок выписан литералом мимо константы"
    assert body.index("count_payments(") < body.index("get_payment_history("), (
        "список строится раньше сверки потолка — тогда признак срабатывания "
        "выводится из длины уже обрезанного списка"
    )


# =============================================================================
# Подписка: истечение срока ничего не отключает (D-07)
# =============================================================================


@pytest.mark.asyncio
async def test_an_expired_subscription_is_reported_not_enforced(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Истёкший срок меняет ПОКАЗ и только его: ни 403, ни редиректа."""
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="basic",
            expires_at=datetime.now(timezone.utc) - timedelta(days=3),
            is_active=True,
        )
    )
    await db_session.commit()

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["subscription"]["expired"] is True
    assert context["subscription"]["plan"] == "basic"
    # Ничего не отключено: оси и планы на месте.
    assert len(context["usage"]) == 4
    assert len(context["plans"]) == 3


@pytest.mark.asyncio
async def test_a_live_subscription_is_not_reported_expired(
    authed_client: AsyncClient, db_session: AsyncSession
):
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="basic",
            expires_at=datetime.now(timezone.utc) + timedelta(days=10),
            is_active=True,
        )
    )
    await db_session.commit()

    with rendered_context() as context:
        await authed_client.get("/billing")

    assert context["subscription"]["expired"] is False


@pytest.mark.asyncio
async def test_a_user_without_a_subscription_is_not_reported_expired(
    authed_client: AsyncClient,
):
    """Отсутствие подписки — не истёкший срок: срока нет вовсе."""
    with rendered_context() as context:
        await authed_client.get("/billing")

    assert context["subscription"]["plan"] == "free"
    assert context["subscription"]["expired"] is False


# =============================================================================
# Рендер раздела ничего не пишет в БД (D-05, T-05-24)
# =============================================================================


@pytest.mark.asyncio
async def test_the_screen_creates_neither_a_subscription_nor_a_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Возврат браузера с ЮKassa приводит СЮДА — и не доказывает оплату."""
    owner = await _current_user(db_session)

    response = await authed_client.get("/billing")

    assert response.status_code == 200
    subscriptions = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == owner.id)
    )
    assert subscriptions == 0
    assert await _payments_count(db_session) == 0


def test_the_get_handler_contains_no_write_path():
    """Структурно: у обработчика раздела нет ни одного пути записи."""
    body = _handler_source("async def billing_page(")

    assert not re.search(r"\b(db|session)\.(add|commit|flush)\(", body), (
        "в GET-обработчике раздела появилась запись в БД"
    )


# =============================================================================
# Покупка пакета сообщений формой POST (D-20)
# =============================================================================


@pytest.mark.asyncio
async def test_purchase_redirects_an_anonymous_visitor_to_login(
    client: AsyncClient, db_session: AsyncSession
):
    response = await _purchase(client)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_purchase_redirects_to_the_yookassa_confirmation_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _purchase(authed_client)

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL

    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.kind == "package"
    assert payment.messages_count == FIRST_PACKAGE_COUNT
    assert payment.amount_value == FIRST_PACKAGE_PRICE


@pytest.mark.asyncio
async def test_purchase_reads_the_price_and_the_count_from_config(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Из формы приезжает ТОЛЬКО индекс: иначе покупатель назначает себе цену."""
    response = await _purchase(
        authed_client,
        data={
            "package_index": FIRST_PACKAGE_INDEX,
            "price": "1.00",
            "messages_count": "999999",
            "package_name": "Бесплатно",
        },
    )

    assert response.status_code == 302
    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.amount_value == FIRST_PACKAGE_PRICE
    assert payment.messages_count == FIRST_PACKAGE_COUNT


@pytest.mark.asyncio
async def test_purchase_rejects_a_cross_site_origin(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _purchase(authed_client, headers=CROSS_SITE)

    assert response.status_code == 403
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("index", ["99", "-1", "не число", ""])
async def test_purchase_rejects_an_index_the_config_does_not_have(
    authed_client: AsyncClient, db_session: AsyncSession, index: str
):
    """Неизвестный индекс возвращает в раздел, а НЕ выбирает «умолчание».

    Нечисловое значение обязано вести туда же: страничная форма не имеет права
    отвечать страницей ошибки разбора — её видел бы пользователь, а не клиент
    JSON-API.
    """
    response = await _purchase(authed_client, data={"package_index": index})

    assert response.status_code == 302
    assert response.headers["location"] == "/billing"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_purchase_creates_nothing_when_payments_are_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    test_settings.yookassa_enabled = False
    try:
        response = await _purchase(authed_client)
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 302
    assert response.headers["location"] == "/billing"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_the_section_still_carries_plans_and_axes_without_payments(
    authed_client: AsyncClient, test_settings
):
    """Выключенные платежи гасят КНОПКИ, а не витрину тарифов (D-21)."""
    test_settings.yookassa_enabled = False
    try:
        with rendered_context() as context:
            response = await authed_client.get("/billing")
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 200
    assert len(context["plans"]) == 3
    assert len(context["usage"]) == 4
    assert context["payments_enabled"] is False


def test_the_origin_check_runs_before_the_payment_is_created():
    """Сверка источника стоит ДО создания платежа.

    Проверка структурная: поведенчески «403 до» и «403 после» на клиенте
    неразличимы, а разница существенна — межсайтовый запрос не имеет права
    вызвать ни одного побочного эффекта, тем более платного.
    """
    body = _handler_source("async def purchase_package(")

    assert "is_same_origin(" in body, "сверки источника в обработчике покупки нет"
    assert body.index("is_same_origin(") < body.index("create_payment("), (
        "платёж создаётся раньше сверки источника"
    )

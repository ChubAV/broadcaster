"""Раздел «Тарифы» целиком: один экран и обе оплаты настоящими формами.

Предмет файла — СБОРКА раздела (BILL-05 / BILL-06 / BILL-07): что один маршрут
`GET /billing` отдаёт все пять блоков экрана сразу (D-18), что список платежей
принадлежит владельцу и называет свой потолок (D-17), и что покупка пакета
сообщений идёт формой `POST`, а не асинхронным запросом из скрипта (D-20).

ЧЕГО ЗДЕСЬ НЕТ.

- Арифметики осей тарифа: её держит `tests/test_application/test_plan_usage.py`.
  Здесь проверяется, что оси ДОЕХАЛИ до контекста в нужном порядке, а не как
  они посчитаны — два теста одного свойства расходятся при первой правке.
- Адаптивных примитивов и инвентаризации шаблонов: их держит
  `tests/test_pages/test_responsive_markup.py`, включая прямой рендер трёх
  макросов раздела.

ДВА СЛОЯ УТВЕРЖДЕНИЙ, А НЕ ОДИН. Верхняя половина файла проверяет КОНТЕКСТ
шаблона: это контракт между обработчиком и разметкой, и он был написан раньше
самой разметки (план 05-04). Нижняя половина, добавленная планом 05-05,
проверяет HTML: контекст, доехавший до шаблона, ещё ничего не говорит о том,
что его нарисовали — макрос, потерявший явный параметр, отрисуется ПУСТОТОЙ
при статусе 200. Оба слоя нужны, и ни один не заменяет другой.
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

from app.application.billing.plan_usage import AXIS_LABELS, AXIS_ORDER
from app.config import Settings
from app.constants import PAYMENT_LIST_CAP
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.pages.common import templates

BILLING_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "billing.py"
BALANCE_HTML = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "templates"
    / "billing"
    / "balance.html"
)

SAME_ORIGIN = {"Origin": "http://test"}
CROSS_SITE = {"Origin": "https://evil.example"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"

# Первый пакет умолчания конфига: 100 сообщений за 149.00.
FIRST_PACKAGE_INDEX = "0"
FIRST_PACKAGE_PRICE = "149.00"
FIRST_PACKAGE_COUNT = 100

# Та же сумма ПОДПИСЬЮ: разряды и отбивка перед знаком рубля — неразрывные
# пробелы (app/pages/common.py::format_amount). Ожидание выписано
# escape-последовательностью: невидимый символ в литерале теста читается как
# обычный пробел и «чинится» первым же редактором.
RENDERED_AMOUNT = "1\u00a0490\u00a0₽"


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


@pytest.mark.asyncio
async def test_the_screen_never_prints_the_yookassa_payment_id(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Идентификатор платежа не выходит в тело ответа НИ ОДНИМ маршрутом.

    Он служит ключом подделки уведомления об оплате, и именно из-за него снесён
    JSON-маршрут покупки (D-24). Контекст раздела несёт строки модели ЦЕЛИКОМ —
    так разметке достаётся настоящий `datetime` даты, — поэтому запрет на показ
    обязан держаться регрессией, а не аккуратностью автора шаблона: она
    переживёт разметку плана 05-05, которой этот тест старше.
    """
    owner = await _current_user(db_session)
    secret = "yoo_secret_never_render_me"
    payment = _payment_row(owner.id)
    payment.yookassa_payment_id = secret
    db_session.add(payment)
    await db_session.commit()

    response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert secret not in response.text, (
        "идентификатор платежа напечатан в разметке раздела"
    )


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


# =============================================================================
# Разметка раздела: пять блоков на экране, обе оплаты формами (план 05-05)
# =============================================================================
#
# Утверждения ниже идут по HTML, а не по контексту: контракт «обработчик →
# разметка» закрыт выше, а здесь проверяется вторая его половина — что данные
# ДОЕХАЛИ до экрана. Макрос, потерявший явный параметр, отрисуется пустотой при
# статусе 200, и проверка контекста этого не увидит.


async def _seed_subscription(
    db: AsyncSession, *, plan: str = "basic", days: int = 30
) -> None:
    db.add(
        Subscription(
            user_id=(await _current_user(db)).id,
            plan=plan,
            expires_at=datetime.now(timezone.utc) + timedelta(days=days),
            is_active=True,
        )
    )
    await db.commit()


def _payment_forms(html: str) -> list[str]:
    """Формы обеих оплат раздела ЦЕЛИКОМ — открывающий тег и тело."""
    return re.findall(
        r'<form[^>]*action="/billing/(?:subscribe|purchase)"[^>]*>.*?</form>',
        html,
        re.S,
    )


def test_the_section_markup_carries_no_script_at_all():
    """В разделе не осталось ни скрипта, ни браузерного диалога (D-20).

    Раздел был ЕДИНСТВЕННЫМ местом проекта, где действие недоступно без
    JavaScript и где ошибка сообщается диалогом оповещения вместо разметки.
    Проверка идёт по исходнику шаблона, а не по выдаче: в выдаче есть теги
    скриптов шелла (htmx и Alpine), и утверждение по HTML было бы про них.
    """
    source = BALANCE_HTML.read_text(encoding="utf-8")

    for marker in ("<script", "alert(", "fetch(", "onclick", "purchasePackage"):
        assert marker not in source, marker


def test_the_section_markup_imports_all_three_partials():
    source = BALANCE_HTML.read_text(encoding="utf-8")

    for rel in (
        "billing/includes/plan_card.html",
        "billing/includes/usage_meters.html",
        "billing/includes/payment_row.html",
    ):
        assert rel in source, rel
    # Разбор конфига из Jinja запрещён: обработчик уже положил готовый список,
    # а свойство кэша не имеет и парсило бы строку на каждой итерации.
    assert "parsed_plan_limits" not in source


@pytest.mark.asyncio
async def test_the_screen_draws_all_four_axes(authed_client: AsyncClient):
    """Четыре метра на экране, подписи — из модуля осей, а не из разметки."""
    html = (await authed_client.get("/billing")).text

    for key in AXIS_ORDER:
        assert AXIS_LABELS[key] in html, AXIS_LABELS[key]


@pytest.mark.asyncio
async def test_the_screen_draws_three_plan_cards(authed_client: AsyncClient):
    html = (await authed_client.get("/billing")).text

    assert "data-plans" in html, "сетки карточек планов на экране нет"
    for name in ("Free", "Basic", "Pro"):
        assert name in html, name


@pytest.mark.asyncio
async def test_a_canceled_payment_is_named_rejected(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отменённый платёж подписан ТЕМ ЖЕ словом, что увидит админ (D-14, D-16)."""
    owner = await _current_user(db_session)
    db_session.add(_payment_row(owner.id, status="canceled"))
    await db_session.commit()

    html = (await authed_client.get("/billing")).text

    assert "отклонён" in html
    assert "canceled" not in html, "машинный статус вышел на экран как есть"


@pytest.mark.asyncio
async def test_a_succeeded_payment_is_named_completed_with_a_human_amount(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Проведённый платёж назван словом, а сумма показана подписью.

    В ЮKassa при этом уходит машинная строка из конфига: форматирование живёт
    ТОЛЬКО на стороне показа (A3).
    """
    owner = await _current_user(db_session)
    db_session.add(_payment_row(owner.id, status="succeeded"))
    await db_session.commit()

    html = (await authed_client.get("/billing")).text

    assert "проведён" in html
    assert RENDERED_AMOUNT in html, "сумма показана машинной строкой"
    assert "1490.00" not in html, "машинная строка платежа вышла на экран"


@pytest.mark.asyncio
async def test_the_screen_names_a_truncated_payment_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сработавший потолок НАЗЫВАЕТ СЕБЯ на экране, а не режет список молча."""
    owner = await _current_user(db_session)
    await _seed_payments(db_session, owner.id, PAYMENT_LIST_CAP + 1)

    html = (await authed_client.get("/billing")).text

    assert str(PAYMENT_LIST_CAP) in html, "потолок на экране не назван"
    assert str(PAYMENT_LIST_CAP + 1) in html, "общее число платежей не названо"


@pytest.mark.asyncio
async def test_an_expired_subscription_is_marked_and_offered_a_renewal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Истёкший срок помечен и сопровождается предложением продлить (D-07).

    Ничего при этом не отключено: карточки планов и метры на месте.
    """
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

    response = await authed_client.get("/billing")
    html = response.text

    assert response.status_code == 200
    assert "истёк" in html, "пометки истёкшего срока на экране нет"
    assert "data-plans" in html, "витрина погасла вместе со сроком"
    renewals = [f for f in _payment_forms(html) if 'value="basic"' in f]
    assert renewals, "предложения продлить нет"
    for form in renewals:
        assert 'action="/billing/subscribe"' in form


@pytest.mark.asyncio
async def test_a_live_subscription_is_not_marked_expired(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_subscription(db_session)

    html = (await authed_client.get("/billing")).text

    assert "истёк" not in html
    assert "Basic" in html


@pytest.mark.asyncio
async def test_both_payments_are_real_forms_and_degrade_without_alpine(
    authed_client: AsyncClient,
):
    """T-05-31: обе оплаты — формы POST, а не кнопки с обработчиком события.

    Кнопка type="button" рядом с асинхронным запросом из скрипта — это не
    оплата, а единственная точка отказа: раздел терял бы приём денег вместе с
    одним тегом <script>. Именованная регрессия по образцу четырёх
    существующих в проекте (WR-04).
    """
    html = (await authed_client.get("/billing")).text

    forms = _payment_forms(html)
    assert forms, "форм оплаты на экране нет вовсе"

    actions = {
        re.search(r'action="([^"]+)"', form).group(1) for form in forms
    }
    assert actions == {"/billing/subscribe", "/billing/purchase"}, actions

    for form in forms:
        assert re.search(r'method="post"', form, re.I), form[:200]
        assert 'type="submit"' in form, form[:200]
        assert 'type="button"' not in form, form[:200]

    purchases = [f for f in forms if "/billing/purchase" in f]
    for form in purchases:
        assert 'name="package_index"' in form, form[:200]


@pytest.mark.asyncio
async def test_the_screen_shows_the_showcase_but_no_payment_form_when_disabled(
    authed_client: AsyncClient, test_settings
):
    """D-21: выключенные платежи гасят КНОПКИ, а не витрину."""
    test_settings.yookassa_enabled = False
    try:
        response = await authed_client.get("/billing")
    finally:
        test_settings.yookassa_enabled = True

    html = response.text
    assert response.status_code == 200
    assert not _payment_forms(html), "форма оплаты осталась при выключенных платежах"
    assert "администратора" in html
    for name in ("Free", "Basic", "Pro"):
        assert name in html, name
    for key in AXIS_ORDER:
        assert AXIS_LABELS[key] in html, AXIS_LABELS[key]


@pytest.mark.asyncio
async def test_the_message_balance_stays_a_block_of_its_own(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Баланс сообщений и ось «Отправок в месяц» — РАЗНЫЕ блоки (D-10).

    Приравнять их значило бы поставить лимит тарифа в зависимость от того,
    сколько пакетов человек докупил.
    """
    html = (await authed_client.get("/billing")).text

    assert "Баланс сообщений" in html
    assert AXIS_LABELS["sends"] in html
    assert "История операций" in html or "Операций пока нет" in html


# =============================================================================
# Устойчивость денежной подписи к порче конфигурации (план 05-09, WR-01)
# =============================================================================
#
# ЧТО ЗДЕСЬ ПРОВЕРЯЕТСЯ И ЧЕГО НЕТ. Правильность самого форматирования держит
# test_billing_amount_format_is_a_display_concern_only в
# tests/test_pages/test_responsive_markup.py — это ДРУГОЕ свойство: там речь о
# том, что подпись живёт только на стороне показа. Здесь — об устойчивости:
# `format_amount` вызывается на КАЖДОЙ карточке плана, КАЖДОЙ плитке пакета и
# КАЖДОЙ строке платежа, поэтому одна непригодная строка в конфиге цен или в
# `payments.amount_value` роняла весь раздел вместе с балансом, планами и
# историей.
#
# `NaN` и `Infinity` — ВАЛИДНЫЕ значения `Decimal`: разбор их принимает, и
# прежний `except` вокруг разбора их не видел. Падение происходило ниже — на
# форматировании и на `int(...)`.

# Значения, которые `Decimal` разбирает успешно, а арифметика подписи не
# переживает. Непригодное возвращается КАК ЕСТЬ.
NON_FINITE_AMOUNTS = ("NaN", "Infinity", "-Infinity", "sNaN")

# Неразрывный пробел кодом, а не литералом: невидимый символ в исходнике теста
# читается как обычный пробел и «чинится» первым же редактором. Тем же приёмом
# выписан RENDERED_AMOUNT в шапке файла.
NBSP = chr(0x00A0)


@pytest.mark.parametrize("value", NON_FINITE_AMOUNTS)
def test_the_amount_label_survives_a_non_finite_value(value: str):
    """Неконечная сумма ПЕЧАТАЕТСЯ как есть, а не поднимает исключение.

    До плана 05-09 `NaN` и `sNaN` поднимали `decimal.InvalidOperation`, а
    `Infinity` и `-Infinity` — `ValueError` из `int(...)`.
    """
    format_amount = templates.env.globals["format_amount"]

    assert format_amount(value) == value


def test_the_amount_label_never_invents_a_zero():
    """Непригодное значение возвращается ИСХОДНЫМ, а не заменяется нулём.

    Выдуманный ноль в денежной подписи — правдоподобная ложь: пользователь
    прочитает его как настоящую цену. Исходная строка на экране хотя бы
    называет себя странной. Контракт выписан в докстринге функции и этой
    правкой НЕ меняется — меняется лишь то, что он исполняется для всего
    множества непригодных значений, а не для подмножества, которое отвергает
    разбор.
    """
    format_amount = templates.env.globals["format_amount"]

    for value in (*NON_FINITE_AMOUNTS, "не число"):
        assert format_amount(value) != f"0{NBSP}₽", value
        assert format_amount(value) == value, value


def test_the_amount_label_still_formats_a_valid_amount():
    """Парный тест: без него предыдущие зеленели бы на возврате входа целиком.

    Ожидания выписаны escape-последовательностью: неразрывный пробел в
    литерале читается как обычный и «чинится» первым же редактором.
    """
    format_amount = templates.env.globals["format_amount"]

    assert format_amount("1490.00") == f"1{NBSP}490{NBSP}₽"
    assert format_amount("4900.50") == f"4{NBSP}900,50{NBSP}₽"
    assert format_amount(None) == ""
    assert format_amount("") == ""


@pytest.mark.asyncio
async def test_the_section_survives_an_unusable_price_in_the_plan_config(
    authed_client: AsyncClient, test_settings
):
    """Одна плохая цена в конфиге не отнимает у пользователя ВЕСЬ раздел.

    Настоящий предмет предупреждения — не функция, а раздел: `format_amount`
    зовётся из трёх поверхностей сразу, и необработанное исключение уводило
    `/billing` в 500 вместе с балансом, планами и историей платежей.
    """
    test_settings.plan_limits = (
        '[{"id":"free","name":"Free","price":"0.00","ads":3,"groups":5,'
        '"sends":300,"accounts":1},'
        '{"id":"basic","name":"Basic","price":"NaN","ads":15,"groups":30,'
        '"sends":5000,"accounts":5}]'
    )
    try:
        response = await authed_client.get("/billing")
    finally:
        test_settings.plan_limits = Settings.model_fields["plan_limits"].default

    assert response.status_code == 200, "раздел упал из-за одной строки конфига"
    html = response.text
    assert "NaN" in html, "непригодная цена не напечатана как есть"
    assert "Basic" in html, "витрина потеряла план с непригодной ценой"

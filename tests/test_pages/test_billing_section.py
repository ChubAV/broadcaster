"""Раздел «Тарифы» целиком: один экран и обе оплаты настоящими формами.

Предмет файла — СБОРКА раздела (BILL-05 / BILL-06 / BILL-07): что один маршрут
`GET /billing` отдаёт все пять блоков экрана сразу (D-18), что список платежей
принадлежит владельцу и называет свой потолок (D-17), и что ЕДИНСТВЕННАЯ
оставшаяся оплата идёт формой `POST`, а не асинхронным запросом из скрипта
(D-20). Второй оплаты у раздела больше нет: валюта сообщений снята целиком, и
входа покупки не существует ни формой, ни маршрутом.

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
async def test_the_section_carries_only_what_is_left_of_the_screen(
    authed_client: AsyncClient,
):
    """Раздел приезжает ОДНИМ маршрутом, и в нём осталось ровно два блока.

    ⚠️ ТЕСТ ПЕРЕЦЕЛЕН, А НЕ УДАЛЁН. Он охраняет ту же границу — «контракт между
    обработчиком и разметкой объявлен целиком», — и сменил предмет вместе с
    экраном: пяти блоков больше нет, потому что четыре из них были счётом.
    Утверждение об ОТСУТСТВИИ снятых ключей столь же обязательно, сколько о
    наличии оставшихся: ключ, забытый в контексте, — это запрос, который никто
    не читает, и он оплачивается на каждом рендере.
    """
    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    for key in ("access", "ever_paid", "subscription_price", "payments"):
        assert key in context, f"ключ «{key}» не доехал до разметки"
    for key in (
        "subscription",
        "usage",
        "plans",
        "balance_info",
        "packages",
        "transactions",
        "free_plan_id",
        "refused_plan_ids",
        "downgrade_caption",
    ):
        assert key not in context, f"снятый ключ «{key}» остался в контексте"
    assert context["active_page"] == "billing"


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
# Подписка: истечение срока ПРЕКРАЩАЕТ ДОСТУП, но не ломает путь к оплате
# =============================================================================
#
# ⚠️ ЗАГОЛОВОК БЛОКА ОТМЕНЯЕТ ПРЕЖНИЙ, А НЕ УТОЧНЯЕТ ЕГО. Он гласил «истечение
# срока ничего не отключает (D-07)» и был правдой при плане фазы 5, где
# применения лимитов не существовало вовсе. С плана 05.1-01 истечение закрывает
# шесть роутеров создания ценности зависимостью `require_access`. Утверждения
# ниже проверяют вторую половину того же правила: сам раздел подписки остаётся
# ОТКРЫТЫМ и в закрытом доступе — иначе человек не смог бы заплатить.


@pytest.mark.asyncio
async def test_the_billing_page_stays_open_when_the_access_is_closed(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Закрытый доступ не закрывает путь к оплате: ни 403, ни редиректа.

    Признак истечения приезжает ГОТОВЫМ ВЕРДИКТОМ из контекста шелла, а не
    пересчитывается страницей: вторая копия правила разъехалась бы с гейтом
    молча — и экран сказал бы «доступ открыт» человеку, которому шесть
    роутеров уже отказывают.
    """
    await _move_access_expiry(db_session, days=-3)

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["access"]["state"] == "expired"
    # Журнал платежей и кнопка оплаты на месте: закрытый доступ закрывает
    # создание ценности, а не путь к оплате.
    assert "payments" in context
    assert context["payments_enabled"] is True


@pytest.mark.asyncio
async def test_a_live_access_period_is_not_reported_expired(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _move_access_expiry(db_session, days=10)

    with rendered_context() as context:
        await authed_client.get("/billing")

    assert context["access"]["state"] != "expired"


# ⚠️ ТЕСТ ОТСУТСТВУЮЩЕЙ СТРОКИ ПОДПИСКИ ПЕРЕЕХАЛ ВНИЗ, В БЛОК ЧЕТЫРЁХ СОСТОЯНИЙ
# (`test_a_user_without_a_subscription_row_gets_the_closed_state`): его предмет —
# состояние экрана, и жить ему рядом с остальными тремя. Здесь он снят как
# ВТОРАЯ копия того же утверждения, а не как потерявший предмет.


# =============================================================================
# Рендер раздела ничего не пишет в БД (D-05, T-05-24)
# =============================================================================


@pytest.mark.asyncio
async def test_the_screen_creates_neither_a_subscription_nor_a_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Возврат браузера с ЮKassa приводит СЮДА — и не доказывает оплату.

    Считается РАЗНИЦА до и после рендера, а не абсолютный ноль: пробную строку
    пользователю завела регистрация (план 05.1-01), и утверждение «строк ноль»
    проверяло бы теперь отсутствие пробного срока, то есть чужой предмет.
    Предмет здесь один — рендер раздела не создаёт НИ ОДНОЙ новой строки.
    """
    owner = await _current_user(db_session)

    async def _subscriptions() -> int:
        return await db_session.scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == owner.id)
        )

    before = await _subscriptions()

    response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert await _subscriptions() == before
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


@pytest.mark.asyncio
async def test_the_section_still_carries_the_price_and_the_date_without_payments(
    authed_client: AsyncClient, test_settings
):
    """Выключенные платежи гасят КНОПКУ, а не витрину (D-21).

    ⚠️ ПРЕДМЕТ СМЕНИЛСЯ ВМЕСТЕ С ВИТРИНОЙ, ГРАНИЦА ОСТАЛАСЬ ТОЙ ЖЕ. Витриной
    были три карточки тарифов и четыре оси; теперь витрина — это цена и дата,
    и они обязаны пережить выключение платежей ровно по тому же основанию:
    экран без цены и без даты читается как поломка, а не как «оплата
    недоступна».
    """
    test_settings.yookassa_enabled = False
    try:
        with rendered_context() as context:
            response = await authed_client.get("/billing")
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 200
    assert context["payments_enabled"] is False
    assert context["subscription_price"], "цена исчезла вместе с кнопкой"
    assert "state" in context["access"], "состояние исчезло вместе с кнопкой"


def test_the_origin_check_runs_before_the_payment_is_created():
    """Сверка источника стоит ДО создания платежа.

    Проверка структурная: поведенчески «403 до» и «403 после» на клиенте
    неразличимы, а разница существенна — межсайтовый запрос не имеет права
    вызвать ни одного побочного эффекта, тем более платного.

    ⚠️ ПРЕДМЕТ ПЕРЕЦЕЛЕН НА ЕДИНСТВЕННЫЙ ОСТАВШИЙСЯ ПЛАТЁЖНЫЙ ВХОД, А НЕ СНЯТ
    ВМЕСТЕ СО СВОИМ ПРЕЖНИМ. Раньше сторожем порядка был обработчик покупки
    пакета; его больше нет, но граница принадлежит не ему, а самому приёму
    денег. Удалить утверждение вместе с обработчиком значило бы оставить
    оплату доступа без единого сторожа порядка «сверка источника → создание
    платежа», а перестановка двух операторов вернула бы дефект молча.
    """
    body = _handler_source("async def subscribe_to_plan(")

    assert "is_same_origin(" in body, "сверки источника в обработчике оплаты нет"
    assert body.index("is_same_origin(") < body.index("create_payment("), (
        "платёж создаётся раньше сверки источника"
    )


# =============================================================================
# Разметка раздела: пять блоков на экране, единственная оплата формой (план 05-05)
# =============================================================================
#
# Утверждения ниже идут по HTML, а не по контексту: контракт «обработчик →
# разметка» закрыт выше, а здесь проверяется вторая его половина — что данные
# ДОЕХАЛИ до экрана. Макрос, потерявший явный параметр, отрисуется пустотой при
# статусе 200, и проверка контекста этого не увидит.


async def _access_row(db: AsyncSession) -> Subscription:
    """Активная строка подписки пользователя — её заводит регистрация."""
    return (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == (await _current_user(db)).id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one()


async def _move_access_expiry(db: AsyncSession, *, days: int = 30) -> datetime:
    """Сдвигает срок УЖЕ СУЩЕСТВУЮЩЕЙ строки, а не заводит вторую.

    Частичный уникальный индекс `uq_subscriptions_active_user` допускает у
    пользователя ровно одну активную строку, а пробный срок ему завела
    регистрация (план 05.1-01). Вторая вставка дала бы IntegrityError, то есть
    тест падал бы на посеве, а не на предмете, — ровно так и краснели эти
    четыре теста после сквозного плана фазы.
    """
    row = await _access_row(db)
    row.expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    await db.commit()
    return row.expires_at




def _payment_forms(html: str) -> list[str]:
    """Формы оплаты раздела ЦЕЛИКОМ — открывающий тег и тело.

    ⚠️ ВЕТКА ВТОРОГО АДРЕСА СНЯТА ВМЕСТЕ СО ВТОРОЙ ОПЛАТОЙ, А НЕ ОСТАВЛЕНА «НА
    ВСЯКИЙ СЛУЧАЙ». Оставленная альтернатива в образце — это утверждение
    «форма оплаты на экране одна», которое молча зазеленело бы и на двух
    формах, если бы вторая когда-нибудь вернулась под прежним адресом.
    """
    return re.findall(
        r'<form[^>]*action="/billing/subscribe"[^>]*>.*?</form>',
        html,
        re.S,
    )


def test_the_section_markup_carries_no_script_at_all():
    """В разделе не осталось ни скрипта, ни браузерного диалога (D-20).

    Раздел был ЕДИНСТВЕННЫМ местом проекта, где действие недоступно без
    JavaScript и где ошибка сообщается диалогом оповещения вместо разметки.
    Проверка идёт по исходнику шаблона, а не по выдаче: в выдаче есть теги
    скриптов шелла (htmx и Alpine), и утверждение по HTML было бы про них.

    ⚠️ МАРКЕР `alert(` СЧИТАЕТСЯ ТОЛЬКО ВНЕ ВЫРАЖЕНИЙ JINJA. Предмет запрета —
    БРАУЗЕРНЫЙ ДИАЛОГ `window.alert(...)`, стоявший здесь вместо разметки. Но
    точно так же называется общий макрос плашки (`components/alert.html`),
    которым план 05-10 рисует причину отказа оплаты, — и он ровно та самая
    разметка, ради которой диалог был убран. Голый поиск подстроки не различал
    эти два случая и запрещал бы правильное решение вместе с неправильным,
    поэтому конструкции Jinja вырезаются до сверки.
    """
    source = BALANCE_HTML.read_text(encoding="utf-8")

    for marker in ("<script", "fetch(", "onclick"):
        assert marker not in source, marker

    # `{{ ... }}`, `{% ... %}` и `{# ... #}` — не JavaScript ни при каких
    # условиях: они исполняются на сервере и до браузера не доезжают вовсе.
    without_jinja = re.sub(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", "", source, flags=re.S)
    assert "alert(" not in without_jinja, (
        "в разметке раздела снова появился браузерный диалог оповещения"
    )


def test_the_section_markup_imports_the_only_partial_it_has_left():
    """Паршал у раздела остался ОДИН, и два снятых не импортируются.

    ⚠️ ПРОВЕРЯЕТСЯ И ОТСУТСТВИЕ, А НЕ ТОЛЬКО НАЛИЧИЕ. Импорт удалённого шаблона
    — это `TemplateNotFound` на рендере, то есть пятисотка на разделе, который
    существует ради приёма денег; поймать её обязан тест исходника, а не
    пользователь.
    """
    source = BALANCE_HTML.read_text(encoding="utf-8")

    assert "billing/includes/payment_row.html" in source
    for gone in ("plan_card", "usage_meter"):
        assert gone not in source, gone
    # Разбор конфига из Jinja запрещён: обработчик уже положил готовые значения,
    # а свойство кэша не имеет и парсило бы строку на каждой итерации.
    assert "parsed_plan_limits" not in source


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
async def test_a_closed_access_is_named_and_offered_a_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Закрытый доступ НАЗВАН словами и сопровождается кнопкой оплаты.

    ⚠️ КОПИЯ ОТМЕНЕНА ВМЕСТЕ С УТВЕРЖДЕНИЕМ, КОТОРОЕ ЕЁ ПОРОДИЛО. Экран печатал
    «срок подписки истёк — ничего не отключено, продлите тариф, когда будет
    удобно». Это было правдой при D-07 фазы 5 и перестало ею быть: теперь
    истечение прекращает доступ. Закрытие называется ФАКТОМ С ПРОДОЛЖЕНИЕМ —
    без слов о сохранности «доступ закрыт» читается как потеря данных, а это
    неправда.

    Управляющий элемент при этом обязан существовать: панель без кнопки и без
    слов читается как сломанный платёжный путь.
    """
    await _move_access_expiry(db_session, days=-3)

    response = await authed_client.get("/billing")
    body = _body(response.text)

    assert response.status_code == 200
    assert "Доступ закрыт" in body, "закрытие доступа на экране не названо"
    assert "работа продолжится с того же места" in body, (
        "закрытие названо без продолжения — читается как потеря данных"
    )
    assert "ничего не отключено" not in body, (
        "экран печатает утверждение, переставшее быть правдой"
    )
    renewals = [f for f in _payment_forms(body) if "/billing/subscribe" in f]
    assert renewals, "предложения оплатить доступ нет"
    for form in renewals:
        assert 'action="/billing/subscribe"' in form


@pytest.mark.asyncio
async def test_a_live_access_period_is_not_marked_closed(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Живой оплаченный доступ назван открытым и своей датой.

    Сверяется ТЕЛО страницы: ту же дату печатает виджет сайдбара, и утверждение
    по целому документу прошло бы при неотрисованной панели раздела.
    """
    owner = await _current_user(db_session)
    expires_at = await _move_access_expiry(db_session, days=30)
    await _seed_subscription_payment(db_session, owner.id)
    user = await _current_user(db_session)

    from app.pages.common import format_datetime_for_user

    body = _body((await authed_client.get("/billing")).text)

    assert "Доступ закрыт" not in body
    assert f"доступ открыт до {format_datetime_for_user(expires_at, user)}" in body


@pytest.mark.asyncio
async def test_the_only_payment_left_is_a_real_form_and_degrades_without_alpine(
    authed_client: AsyncClient,
):
    """T-05-31: оплата — форма POST, а не кнопка с обработчиком события.

    Кнопка type="button" рядом с асинхронным запросом из скрипта — это не
    оплата, а единственная точка отказа: раздел терял бы приём денег вместе с
    одним тегом <script>. Именованная регрессия по образцу четырёх
    существующих в проекте (WR-04).

    ⚠️ ФОРМА НА ЭКРАНЕ ОДНА ВМЕСТО ТРЁХ, И ОНА НЕ НЕСЁТ НИ ОДНОГО ПОЛЯ: цену
    читает сервер из настройки, и поверхность подмены суммы схлопнута до нуля,
    а не отфильтрована (T-05.1-22).
    """
    body = _body((await authed_client.get("/billing")).text)

    forms = _payment_forms(body)
    assert len(forms) == 1, f"форм оплаты на экране не одна: {len(forms)}"

    form = forms[0]
    assert 'action="/billing/subscribe"' in form
    assert re.search(r'method="post"', form, re.I), form[:200]
    assert 'type="submit"' in form, form[:200]
    assert 'type="button"' not in form, form[:200]
    assert "<input" not in form, "форма оплаты снова несёт поле"


@pytest.mark.asyncio
async def test_the_screen_keeps_the_price_but_no_payment_form_when_disabled(
    authed_client: AsyncClient, test_settings
):
    """D-21: выключенные платежи гасят КНОПКУ, а не витрину.

    ⚠️ ЭТОТ ТЕСТ ПОГЛОТИЛ ПРЕЖНИЙ `test_disabled_payments_keep_their_own_words`.
    Тот утверждал ту же границу — «отказ назван словами администратора», — но
    его вторая половина различала два пустых состояния КАТАЛОГА ПАКЕТОВ,
    которого больше нет. Осталась одна пара слов, и живёт она здесь.
    """
    test_settings.yookassa_enabled = False
    try:
        response = await authed_client.get("/billing")
    finally:
        test_settings.yookassa_enabled = True

    body = _body(response.text)
    assert response.status_code == 200
    assert not _payment_forms(body), "форма оплаты осталась при выключенных платежах"
    assert "Оплатить доступ можно через администратора" in body
    assert templates.env.globals["format_amount"](SUBSCRIPTION_PRICE) in body, (
        "витрина погасла вместе с кнопкой"
    )


# ⚠️ `test_the_message_balance_stays_a_block_of_its_own` СНЯТ ВМЕСТЕ С ПРЕДМЕТОМ.
# Он утверждал, что баланс сообщений и ось «Отправок в месяц» — разные блоки
# (D-10). Обоих на экране больше нет: ни баланса, ни осей, ни пакетов, которые
# он разводил. Границу «лимит тарифа не зависит от докупленных пакетов» снял
# не этот тест, а решение D-D — предмет исчез, а не перестал проверяться.


# =============================================================================
# Устойчивость денежной подписи к порче конфигурации (план 05-09, WR-01)
# =============================================================================
#
# ЧТО ЗДЕСЬ ПРОВЕРЯЕТСЯ И ЧЕГО НЕТ. Правильность самого форматирования держит
# test_billing_amount_format_is_a_display_concern_only в
# tests/test_pages/test_responsive_markup.py — это ДРУГОЕ свойство: там речь о
# том, что подпись живёт только на стороне показа. Здесь — об устойчивости:
# `format_amount` зовётся и на цене доступа, и на КАЖДОЙ строке платежа,
# поэтому одна непригодная строка в настройке цены или в `payments.amount_value`
# роняла весь раздел вместе с датой, кнопкой и историей.
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
async def test_the_section_survives_an_unusable_subscription_price(
    authed_client: AsyncClient, test_settings
):
    """Непригодная цена в настройке не отнимает у пользователя ВЕСЬ раздел.

    ⚠️ ТЕСТ ПЕРЕЦЕЛЕН С ПРЕЙСКУРАНТА НА ЕДИНСТВЕННУЮ ЦЕНУ. Граница осталась той
    же: `format_amount` зовётся и на витрине, и на каждой строке платежа, и
    необработанное исключение уводило `/billing` в 500 целиком — то есть
    закрывало экран, с которого человек только и может заплатить. Сменился
    источник цены: прейскуранта нет, есть одна настройка.

    Непригодное значение печатается КАК ЕСТЬ: выдуманный ноль в денежной
    подписи — правдоподобная ложь, а исходная строка хотя бы называет себя
    странной.
    """
    test_settings.subscription_price = "NaN"
    try:
        response = await authed_client.get("/billing")
    finally:
        test_settings.subscription_price = Settings.model_fields[
            "subscription_price"
        ].default

    assert response.status_code == 200, "раздел упал из-за одной строки настройки"
    body = _body(response.text)
    assert "NaN" in body, "непригодная цена не напечатана как есть"


# ⚠️ ТРИ ТЕСТА КАТАЛОГА ПАКЕТОВ СНЯТЫ ВМЕСТЕ С САМИМ КАТАЛОГОМ (D-D):
# `…empty_package_catalogue_speaks…`, `…filled_package_catalogue_carries_no…` и
# `test_disabled_payments_keep_their_own_words`. Первые два различали два
# пустых состояния сетки пакетов, которой на экране больше нет. Третий охранял
# границу «выключенные платежи названы словами», и она НЕ потеряна: её держит
# `test_the_screen_keeps_the_price_but_no_payment_form_when_disabled` выше —
# там же, где живёт единственная оставшаяся строка про администратора.


# =============================================================================
# План 05.1-05: одно из ЧЕТЫРЁХ состояний считает ОБРАБОТЧИК, а не разметка
# =============================================================================
#
# Правило состояния одно на раздел, и вторая его копия в Jinja разъехалась бы с
# гардом доступа молча — тот же класс дефекта, за который фаза 5 получила шесть
# раундов гэпов подряд. Разметке достаётся ГОТОВЫЙ ответ `access.state`.
#
# ⚠️ УТВЕРЖДЕНИЯ О ВЕЛИЧИНЕ НА ЭКРАНЕ СВЕРЯЮТ ТЕЛО СТРАНИЦЫ, А НЕ ВСЮ ВЫДАЧУ.
# Виджет сайдбара печатает дату доступа на КАЖДОМ документе проекта, и проверка
# по целому HTML прошла бы при неотрисованной панели раздела (план 05.1-04,
# «Issues» №2).

STATE_TRIAL = "trial"
STATE_PAID = "paid"
STATE_EXPIRED = "expired"
STATE_COMPED = "comped"

# Цена доступа МАШИННОЙ СТРОКОЙ приезжает из настройки, а не выписывается
# литералом: копия числа в тесте разошлась бы с конфигом молча — ровно тем же
# правилом, каким её нет в разметке.
SUBSCRIPTION_PRICE = Settings.model_fields["subscription_price"].default

# Две строки объяснения закрытого доступа. Каждая называет ФАКТ и ПРОДОЛЖЕНИЕ:
# «доступ закрыт» без слов о сохранности читается как потеря данных, а это
# неправда — планировщик лишь не отправляет.
NOTICE_NEVER_PAID = "Пробный период закончился"
NOTICE_AFTER_PAYING = "Оплаченный срок закончился"
NOTICE_TAIL = "работа продолжится с того же места"


def _body(html: str) -> str:
    """Тело страницы — всё после открытия `[data-body]`, без шелла."""
    return html.split("<div data-body>", 1)[-1]


async def _seed_subscription_payment(
    db: AsyncSession, user_id: int, *, status: str = "succeeded"
) -> Payment:
    """Подписочный платёж с явным статусом. `plan` пуст — тарифов больше нет."""
    payment = _payment_row(user_id, status=status)
    payment.plan = None
    db.add(payment)
    await db.commit()
    return payment


@pytest.mark.asyncio
async def test_a_live_period_without_a_paid_subscription_is_a_trial(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Срок жив, успешных подписочных платежей нет — это ПРОБНЫЙ период."""
    await _move_access_expiry(db_session, days=3)

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["access"]["state"] == STATE_TRIAL
    assert context["ever_paid"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["pending", "canceled"])
async def test_an_unfinished_payment_does_not_make_the_period_paid(
    authed_client: AsyncClient, db_session: AsyncSession, status: str
):
    """Незавершённый и отклонённый платежи «оплаченным» состояние НЕ делают.

    Иначе человек, отказавшийся от оплаты на стороне ЮKassa, прочитал бы
    «подписка оплачена» — то есть экран подтвердил бы сделку, которой не было.
    """
    owner = await _current_user(db_session)
    await _move_access_expiry(db_session, days=3)
    await _seed_subscription_payment(db_session, owner.id, status=status)

    with rendered_context() as context:
        await authed_client.get("/billing")

    assert context["access"]["state"] == STATE_TRIAL
    assert context["ever_paid"] is False


@pytest.mark.asyncio
async def test_a_live_period_after_a_succeeded_payment_is_paid(
    authed_client: AsyncClient, db_session: AsyncSession
):
    owner = await _current_user(db_session)
    await _move_access_expiry(db_session, days=20)
    await _seed_subscription_payment(db_session, owner.id)

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["access"]["state"] == STATE_PAID
    assert context["ever_paid"] is True


@pytest.mark.asyncio
async def test_an_expired_period_is_named_closed(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _move_access_expiry(db_session, days=-3)

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["access"]["state"] == STATE_EXPIRED


@pytest.mark.asyncio
async def test_a_user_without_a_subscription_row_gets_the_closed_state(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отсутствие строки — ОПРЕДЕЛЁННОЕ состояние (доступа нет), а не падение.

    Пользователи, заведённые до ревизии 05.1-08, строки не имеют, и встретить
    их пятисоткой значило бы закрыть единственный экран, с которого они могут
    заплатить. Все чтения ключа доступа идут через умолчание именно поэтому.
    """
    row = await _access_row(db_session)
    await db_session.delete(row)
    await db_session.commit()

    with rendered_context() as context:
        response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert context["access"]["state"] == STATE_EXPIRED
    assert context["access"]["expires_at"] is None


@pytest.mark.asyncio
async def test_the_closed_access_explains_itself_and_prints_the_price(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Тело страницы несёт объяснение и цену, отформатированную глобалом."""
    await _move_access_expiry(db_session, days=-3)

    body = _body((await authed_client.get("/billing")).text)

    assert NOTICE_NEVER_PAID in body, "закрытие доступа не объяснено"
    assert NOTICE_TAIL in body, (
        "закрытие названо без продолжения — читается как потеря данных"
    )
    assert templates.env.globals["format_amount"](SUBSCRIPTION_PRICE) in body, (
        "цена доступа в теле раздела не напечатана"
    )
    assert SUBSCRIPTION_PRICE not in body, "машинная строка цены вышла на экран"


@pytest.mark.asyncio
async def test_the_explanation_differs_by_whether_the_person_ever_paid(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Одна из двух историй была бы неправдой для половины людей."""
    owner = await _current_user(db_session)
    await _move_access_expiry(db_session, days=-3)
    await _seed_subscription_payment(db_session, owner.id)

    body = _body((await authed_client.get("/billing")).text)

    assert NOTICE_AFTER_PAYING in body
    assert NOTICE_NEVER_PAID not in body, (
        "человеку, который платил, сказано, что у него кончился пробный период"
    )


@pytest.mark.asyncio
async def test_the_notice_does_not_depend_on_the_redirect_flag(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Плашка рисуется по СОСТОЯНИЮ с сервера, а не по параметру адреса.

    Человек, открывший раздел из меню, обязан прочитать те же слова: критерий
    требует, чтобы ему было СКАЗАНО, а не чтобы ему повезло с маршрутом.
    """
    await _move_access_expiry(db_session, days=-3)

    from_menu = _body((await authed_client.get("/billing")).text)
    from_gate = _body((await authed_client.get("/billing?expired=1")).text)

    assert NOTICE_NEVER_PAID in from_menu
    assert NOTICE_NEVER_PAID in from_gate


def test_the_handler_never_reads_the_redirect_flag():
    """Ни одной строкой: из адресной строки в разметку не уходит НИЧЕГО.

    Это недостижимость, а не экранирование — подставлять нечего, потому что
    вход в разметку не связан со входом из адреса (T-05.1-21).
    """
    body = _handler_source("async def billing_page(")

    assert 'query_params.get("expired")' not in body
    assert "query_params.get('expired')" not in body
    assert body.count("query_params") == 1, (
        "обработчик читает больше одного параметра адреса"
    )


@pytest.mark.asyncio
async def test_the_outcome_of_the_last_action_wins_over_the_background_notice(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Две плашки подряд читаются как две разные беды — рисуется одна.

    Исход только что нажатой кнопки важнее фонового состояния: человек нажал
    «Оплатить» и получил отказ, и именно про отказ он и спрашивает.
    """
    await _move_access_expiry(db_session, days=-3)

    body = _body((await authed_client.get("/billing?error=payment")).text)

    assert "Не удалось начать оплату" in body
    assert NOTICE_NEVER_PAID not in body, "фоновая плашка нарисована второй"


@pytest.mark.asyncio
async def test_the_section_is_named_subscription_on_every_surface(
    authed_client: AsyncClient,
):
    """Подпись раздела читают сайдбар, нижние табы и заголовок страницы.

    Она объявлена ОДИН раз в `NAV_ITEMS`, поэтому проверка идёт по выдаче: имя
    раздела обязано смениться сразу на всех трёх поверхностях, а не в одной.
    """
    from app.pages.common import NAV_ITEMS, nav_label

    html = (await authed_client.get("/billing")).text

    assert nav_label("billing") == "Подписка"
    assert [item["label"] for item in NAV_ITEMS if item["key"] == "billing"] == [
        "Подписка"
    ]
    assert "<title>Подписка — Broadcaster</title>" in html
    assert "Доступ к системе и история платежей" in html
    assert "Тарифы" not in html, "прежнее имя раздела осталось на экране"


# =============================================================================
# План 05.1-05, задача 3: раздел закрыт тестами по СВОЕМУ НОВОМУ предмету
# =============================================================================
#
# Снятое не проверяется, оставшееся проверяется полностью. Три регрессии,
# СТАРШИЕ этой разметки, не потеряны ни одной: запрет печати идентификатора
# платежа живёт выше, а обе регрессии нажимаемой высоты кнопки — в
# tests/test_pages/test_responsive_markup.py, перецеленные на единственную
# оставшуюся форму.

# Признаки снятых блоков. Каждый — ЛИТЕРАЛ С ЭКРАНА, а не имя переменной:
# проверяется, что человек их больше не видит, а не что код их не упоминает.
GONE_FROM_THE_SCREEN = (
    "Потребление тарифа",
    "Баланс сообщений",
    "История операций",
    "data-plans",
    "Пакеты сообщений",
    "progress__track",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("days", [3, 20, -3])
async def test_the_screen_carries_none_of_the_five_removed_blocks(
    authed_client: AsyncClient, db_session: AsyncSession, days: int
):
    """Снятые блоки не возвращаются НИ В ОДНОМ из достижимых состояний.

    Параметризация по сроку покрывает `trial`, `paid` и `expired`; четвёртое
    состояние (`comped`) проверяется отдельно — его источник приезжает планом
    05.1-08, и здесь оно достигается подменой готового ответа обработчика.
    """
    owner = await _current_user(db_session)
    await _move_access_expiry(db_session, days=days)
    if days == 20:
        await _seed_subscription_payment(db_session, owner.id)

    body = _body((await authed_client.get("/billing")).text)

    for marker in GONE_FROM_THE_SCREEN:
        assert marker not in body, marker


@pytest.mark.asyncio
async def test_the_free_access_state_stands_whole_without_a_date(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Бесплатный доступ печатает «бессрочно», цену и НИ ОДНОЙ кнопки оплаты.

    ⚠️ СОСТОЯНИЕ ДОСТИГАЕТСЯ ПОДМЕНОЙ ГОТОВОГО ОТВЕТА ОБРАБОТЧИКА, и это не
    обход: колонка `subscriptions.has_free_access` приезжает планом 05.1-08, а
    РАЗМЕТКА четырёх состояний написана здесь и обязана быть проверена здесь же.
    Подменяется ровно одно значение — то самое, которое обработчик вычислит сам,
    когда у него появится источник.

    Кнопки нет вовсе, и её место занимает подпись с причиной: кнопка предлагала
    бы купить то, что у человека уже есть бесплатно (P-3).
    """
    row = await _access_row(db_session)
    await db_session.delete(row)
    await db_session.commit()

    original = templates.TemplateResponse

    def as_comped(*args, **kwargs):
        context = args[1] if len(args) > 1 else (kwargs.get("context") or {})
        context["access"]["state"] = "comped"
        return original(*args, **kwargs)

    with patch.object(templates, "TemplateResponse", as_comped):
        response = await authed_client.get("/billing")

    body = _body(response.text)
    assert response.status_code == 200
    assert "доступ открыт бессрочно" in body
    assert "Оплата не требуется" in body
    assert not _payment_forms(body), "бесплатному доступу предложено купить доступ"
    assert templates.env.globals["format_amount"](SUBSCRIPTION_PRICE) in body, (
        "цена спрятана у бесплатного пользователя"
    )


@pytest.mark.asyncio
async def test_the_state_badge_stands_on_a_line_of_its_own(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Бейдж состояния вынесен ИЗ строки цены — единственный детектор M1.

    Строка цены объявлена без переноса, бейдж — без переноса и без сжатия; при
    полотне 303px запас около девяти пикселей. Проверка «помещается в карточку»
    проходит и при НАРУШЕННОМ контракте, поэтому проверяется структура: узел
    бейджа не лежит внутри узла строки цены.
    """
    await _move_access_expiry(db_session, days=-3)

    body = _body((await authed_client.get("/billing")).text)

    price_line = re.search(r"<div data-metric-line>(.*?)</div>", body, re.S)
    assert price_line, "строки цены на экране нет"
    assert "badge" not in price_line.group(1), (
        "бейдж состояния стоит ВНУТРИ строки цены — при выходе за полотно "
        "строка не сложится, а вылезет за карточку"
    )
    assert "data-access-state" in body, "бейджа состояния на экране нет вовсе"


@pytest.mark.asyncio
async def test_an_empty_payment_history_speaks_both_of_its_lines(
    authed_client: AsyncClient,
):
    """Ноль платежей — пустое состояние СЛОВАМИ, а не пустая таблица.

    Пустой блок под панелью читается как поломка интерфейса, а не как
    «показывать нечего», а отсутствие блока — как «истории у нас не бывает».
    """
    body = _body((await authed_client.get("/billing")).text)

    assert "Платежей пока нет" in body
    assert "Здесь появятся оплаты доступа" in body
    assert "data-rowhead" not in body, "шапка колонок нарисована над пустотой"


@pytest.mark.asyncio
async def test_one_payment_and_many_use_the_same_row_primitive(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Один платёж и много — ОДИН и тот же примитив строки (zero-one-many)."""
    owner = await _current_user(db_session)
    await _seed_payments(db_session, owner.id, 1)

    single = _body((await authed_client.get("/billing")).text)
    assert single.count("data-row") >= 1
    assert "Платежей пока нет" not in single

    await _seed_payments(db_session, owner.id, 3)
    many = _body((await authed_client.get("/billing")).text)
    # Пробел после атрибута обязателен: `<div data-rowhead` начинается теми же
    # знаками, и счёт без него прибавлял бы к строкам шапку колонок.
    assert many.count("<div data-row ") == 4, "строки журнала рисуются по-разному"


@pytest.mark.asyncio
async def test_an_unknown_payment_status_is_printed_as_it_is(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Неизвестный статус печатается моношрифтом КАК ЕСТЬ, а не прячется.

    Спрятанное состояние платежа читается как «платежа не было» — то есть как
    пропавшие деньги.
    """
    owner = await _current_user(db_session)
    db_session.add(_payment_row(owner.id, status="waiting_for_capture"))
    await db_session.commit()

    body = _body((await authed_client.get("/billing")).text)

    assert "waiting_for_capture" in body, "неизвестный статус спрятан"
    assert re.search(r'class="mono[^"]*">waiting_for_capture<', body), (
        "неизвестный статус напечатан не моношрифтом"
    )


@pytest.mark.asyncio
async def test_the_purpose_of_a_payment_has_three_sources(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Назначение выбирается ПО НАЛИЧИЮ ПОЛЯ, а не по эпохе платежа.

    ⚠️ ИСТОРИЧЕСКАЯ ПОКУПКА ОБЯЗАНА ОСТАТЬСЯ СОБОЙ. Переименовать чужой прошлый
    платёж за тариф в «Доступ к системе» — значит соврать в денежном журнале
    (T-05.1-10). Колонки `plan` и `package_name` ревизия фазы не трогает, и
    разметка читает их и после неё.
    """
    owner = await _current_user(db_session)
    fresh = _payment_row(owner.id)
    fresh.plan = None
    historic = _payment_row(owner.id)
    historic.plan = "basic"
    package = _payment_row(owner.id)
    package.kind = "package"
    package.plan = None
    package.package_name = "Пакет на 500 сообщений"
    nameless = _payment_row(owner.id)
    nameless.kind = "package"
    nameless.plan = None
    nameless.package_name = None
    db_session.add_all([fresh, historic, package, nameless])
    await db_session.commit()

    body = _body((await authed_client.get("/billing")).text)

    assert "Доступ к системе" in body, "платёж за доступ не подписан"
    assert "Basic" in body, "исторический платёж за тариф переименован"
    assert "Пакет на 500 сообщений" in body, "имя пакета потеряно"
    assert "Пакет сообщений" in body, "безымянный пакет остался без подписи"


@pytest.mark.asyncio
async def test_a_payment_without_a_date_still_draws_its_whole_row(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отсутствие даты даёт ПУСТУЮ ЯЧЕЙКУ, а не пропавшую строку.

    Строка платежа без даты — всё ещё запись о деньгах, и спрятать её значило бы
    показать журнал короче, чем он есть, не сказав об этом ни слова.
    """
    owner = await _current_user(db_session)
    payment = _payment_row(owner.id)
    payment.created_at = None
    db_session.add(payment)
    await db_session.commit()

    body = _body((await authed_client.get("/billing")).text)

    assert "проведён" in body, "строка без даты не нарисована"
    assert RENDERED_AMOUNT in body, "сумма строки без даты потеряна"


@pytest.mark.asyncio
async def test_the_amount_on_the_screen_carries_non_breaking_spaces(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Разряды и отбивка перед знаком рубля — НЕРАЗРЫВНЫЕ пробелы.

    Обычный пробел перенёс бы «1» и «490» на разные строки узкой карточки, и
    сумма на 375px прочиталась бы двумя числами вместо одного.
    """
    owner = await _current_user(db_session)
    db_session.add(_payment_row(owner.id))
    await db_session.commit()

    body = _body((await authed_client.get("/billing")).text)

    assert RENDERED_AMOUNT in body
    assert "1 490 ₽" not in body, "сумма напечатана обычными пробелами"
    # Цена доступа — тем же правилом и тем же глобалом.
    assert templates.env.globals["format_amount"](SUBSCRIPTION_PRICE) in body
    assert NBSP in templates.env.globals["format_amount"](SUBSCRIPTION_PRICE)


@pytest.mark.asyncio
async def test_the_payment_history_order_is_stable_on_equal_timestamps(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Равные даты создания НЕ отдают порядок на откуп плану запроса.

    У выборки объявлен ВТОРИЧНЫЙ ключ сортировки. Без него две строки с
    одинаковой секундой меняются местами от прогона к прогону, и денежный
    журнал перестаёт быть воспроизводимым — а его читают, чтобы сверить
    списание, то есть в ровно тот момент, когда порядок важен.
    """
    from app.services.billing_service import get_payment_history

    owner = await _current_user(db_session)
    stamp = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
    db_session.add_all([_payment_row(owner.id, created_at=stamp) for _ in range(5)])
    await db_session.commit()

    first = [row.id for row in await get_payment_history(db_session, owner.id, 10)]
    second = [row.id for row in await get_payment_history(db_session, owner.id, 10)]

    assert first == second, "порядок при равных датах не воспроизводится"
    assert first == sorted(first, reverse=True), (
        "вторичный ключ сортировки не объявлен — порядок зависит от плана запроса"
    )


def test_the_payment_history_query_declares_two_sort_keys():
    """Структурно: у выборки истории платежей ДВА ключа сортировки.

    Поведенческий тест выше на SQLite может зазеленеть случайно — движок волен
    вернуть строки в порядке вставки. Утверждение об ОБЪЯВЛЕНИИ ключа не зависит
    от движка и краснеет ровно тогда, когда ключ снимут.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "services"
        / "billing_service.py"
    ).read_text(encoding="utf-8")
    body = source[source.index("async def get_payment_history(") :]
    body = body[: body.index("async def count_payments(")]

    order_by = re.search(r"\.order_by\((.*)\)\n", body)
    assert order_by, "у выборки истории платежей нет сортировки вовсе"
    assert order_by.group(1).count(".desc(") >= 2, (
        "у выборки истории платежей объявлен один ключ сортировки: "
        f"{order_by.group(1)}"
    )


def test_the_long_package_name_wraps_inside_the_row_instead_of_scrolling():
    """Длинное назначение переносится ВНУТРИ строки, а не даёт прокрутку.

    ⚠️ ПРОВЕРЯЕТСЯ ОБЪЯВЛЕНИЕ, А НЕ ОТРИСОВКА: браузерного харнесса в проекте
    нет. Утверждение снимается по исходнику стилей и разметки: ячейка назначения
    объявлена растягиваемой, правила усечения у неё нет, а ниже 861px набор
    ширин колонок инертен — строка раскладывается правилами мобильного блока.
    """
    css = (
        Path(__file__).resolve().parents[2] / "app" / "static" / "css" / "app.css"
    ).read_text(encoding="utf-8")
    row_macro = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "templates"
        / "billing"
        / "includes"
        / "payment_row.html"
    ).read_text(encoding="utf-8")

    assert "grow=true" in row_macro, "ячейка назначения не объявлена растягиваемой"
    assert "text-overflow" not in row_macro
    assert "flex-wrap: wrap !important" in css, (
        "набор ширин колонок перестал быть инертным ниже 861px"
    )
    assert "flex: 1 1 100% !important" in css, (
        "растягиваемая ячейка перестала занимать всю ширину строки"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url,marker",
    [("/billing?error=payment", "Не удалось начать оплату"), ("/billing", NOTICE_NEVER_PAID)],
)
async def test_the_notice_stands_before_the_access_panel(
    authed_client: AsyncClient, db_session: AsyncSession, url: str, marker: str
):
    """Причина читается РАНЬШЕ цены и даты — обе плашки стоят ПЕРВЫМИ.

    ⚠️ ГРАНИЦА УНАСЛЕДОВАНА У `test_the_alert_stands_before_the_current_plan_block`
    (tests/test_pages/test_billing_payment_errors.py), чьим якорем был блок
    текущего тарифа: блока нет, якоря нет, а граница осталась той же и получила
    новый якорь — панель доступа. Плашка под панелью была бы прочитана после
    того, как человек уже сделал вывод «ничего не изменилось, кнопка сломана».

    Это же пятый пункт ручной приёмки на 375px: в закрытом доступе плашка видна
    БЕЗ ПРОКРУТКИ, то есть стоит первой.
    """
    await _move_access_expiry(db_session, days=-3)

    body = _body((await authed_client.get(url)).text)

    assert marker in body
    assert body.index(marker) < body.index("data-access-panel"), (
        "плашка причины стоит ниже панели доступа"
    )

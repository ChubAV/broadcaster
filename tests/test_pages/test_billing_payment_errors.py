"""Закрытое множество состояний отказа обеих форм оплаты (U1, U2, U3, IN-06).

Предмет файла — ОТВЕТ РАЗДЕЛА НА НЕУДАВШУЮСЯ ОПЛАТУ. До плана 05-10 его не было
вовсе: `create_payment` звался без обёртки, поэтому отказ API ЮKassa выходил
необработанной пятисоткой, а все пять веток гардов возвращали голый редирект на
`/billing` — то есть человек, нажавший «Оплатить», получал ту же самую страницу
без единого слова и следующим действием нажимал ещё раз.

ЧТО ЗДЕСЬ ПРОВЕРЯЕТСЯ И ЧЕГО НЕТ.

- Здесь: что КАЖДАЯ ветка отказа несёт свою причину, что причина приезжает из
  ЗАКРЫТОГО множества, а не из адресной строки, и что отказ создания платежа не
  оставляет строки в `payments`.
- Не здесь: сборка раздела (`test_billing_section.py`), сквозная линия подписки
  (`test_billing_subscription.py`), сам сервис платежей
  (`test_services/test_payment_service.py`).

ПОЧЕМУ МНОЖЕСТВО ПРИЧИН ЗАКРЫТО (T-05-46). В разметку уходит строка ИЗ
ОТОБРАЖЕНИЯ `_payment_error_message`, а не значение параметра запроса. Владелец
ссылки может подставить в адрес что угодно — на экран это не попадёт ни
значением, ни атрибутом, потому что подставлять нечего: вход в разметку не
связан со входом из адреса. Тем же приёмом закрыт признак исхода повтора
отправки (`RETRY_NOTICES` в `app/pages/history.py`).

ПОЧЕМУ ТЕКСТ ЧУЖОГО ИСКЛЮЧЕНИЯ НЕ ПОКАЗЫВАЕТСЯ (T-05-47). Прецедент R-03-09
Фазы 3 — раскрытие текста стороннего исключения в плашке — принят владельцем
риском severity medium. Повторять его на ДЕНЕЖНОМ пути не следует: текст SDK
уходит в журнал, на экран — фиксированная строка.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User

BILLING_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "billing.py"

SAME_ORIGIN = {"Origin": "http://test"}
CROSS_SITE = {"Origin": "https://evil.example"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"

FIRST_PACKAGE_INDEX = "0"

# Текст «стороннего исключения». Строка нарочно узнаваемая: она не встречается
# ни в одном шаблоне проекта, поэтому её появление в разметке однозначно значит
# «текст чужого исключения вышел на экран», а не совпадение со словом верстки.
SDK_FAILURE_TEXT = "yookassa_sdk_internal_boom_do_not_render_me"

# Строки закрытого множества. Выписаны здесь ДОСЛОВНО, потому что предмет
# проверки — что человек читает названную причину, а не что обработчик положил в
# контекст непустое значение.
MSG_PAYMENT = "Не удалось начать оплату — попробуйте ещё раз через минуту"
MSG_DISABLED = "Оплата сейчас недоступна — обратитесь к администратору"
MSG_PLAN = "Этот тариф больше не предлагается — обновите страницу и выберите другой"
MSG_PACKAGE = "Этот пакет больше не предлагается — обновите страницу и выберите другой"

# Признак нарисованной плашки отказа. Проверяется ИМЕННО он, а не наличие слова
# из текста: слово может прийти из соседнего блока экрана, обёртка — только из
# ветки показа причины.
ALERT_MARKER = "data-payment-error"


# --- Инструменты --------------------------------------------------------------


def _yoo_settings():
    """Мок настроек ЮKassa по образцу tests/test_services/test_payment_service.py."""
    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "http://test/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_settings


def _yoo_payment(payment_id: str = "yoo_1"):
    mock_payment = MagicMock()
    mock_payment.id = payment_id
    mock_payment.confirmation = MagicMock()
    mock_payment.confirmation.confirmation_url = CONFIRMATION_URL
    return mock_payment


def _failing_sdk():
    """Подмена вызова SDK, ПОДНИМАЮЩАЯ исключение вместо возврата платежа.

    Тот же способ подмены, что у успешного пути, — меняется только исход:
    настоящая сеть ЮKassa в суите не участвует ни в одном тесте.
    """
    return patch(
        "app.services.payment_service.YooPayment.create",
        side_effect=RuntimeError(SDK_FAILURE_TEXT),
    )


def _healthy_sdk(payment_id: str = "yoo_1"):
    return patch(
        "app.services.payment_service.YooPayment.create",
        return_value=_yoo_payment(payment_id),
    )


async def _post(
    client: AsyncClient,
    url: str,
    data: dict,
    *,
    failing: bool = False,
    headers=None,
):
    sdk = _failing_sdk() if failing else _healthy_sdk()
    with patch(
        "app.services.payment_service.get_settings", return_value=_yoo_settings()
    ), sdk:
        return await client.post(
            url,
            data=data,
            headers=SAME_ORIGIN if headers is None else headers,
            follow_redirects=False,
        )


async def _subscribe(
    client: AsyncClient, plan: str = "basic", *, failing: bool = False, headers=None
):
    return await _post(
        client,
        "/billing/subscribe",
        {"plan": plan},
        failing=failing,
        headers=headers,
    )


async def _purchase(
    client: AsyncClient,
    index: str = FIRST_PACKAGE_INDEX,
    *,
    failing: bool = False,
    headers=None,
):
    return await _post(
        client,
        "/billing/purchase",
        {"package_index": index},
        failing=failing,
        headers=headers,
    )


async def _payments_count(db: AsyncSession) -> int:
    return await db.scalar(select(func.count()).select_from(Payment))


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


# =============================================================================
# U1 / U2 — отказ API ЮKassa на форме тарифа
# =============================================================================


@pytest.mark.asyncio
async def test_a_failed_subscription_payment_returns_the_person_with_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отказ SDK — состояние раздела, а не необработанная пятисотка.

    До плана 05-10 исключение выходило наружу: `create_payment` звался без
    обёртки, и человек получал страницу ошибки сервера вместо ответа раздела.
    """
    response = await _subscribe(authed_client, failing=True)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=payment"


@pytest.mark.asyncio
async def test_a_failed_package_payment_returns_the_person_with_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Один порядок проверок на обоих входах означает один ответ на отказ."""
    response = await _purchase(authed_client, failing=True)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=payment"


@pytest.mark.asyncio
@pytest.mark.parametrize("form", ["subscribe", "purchase"])
async def test_a_failed_payment_leaves_no_row_in_the_journal(
    authed_client: AsyncClient, db_session: AsyncSession, form: str
):
    """Платёж не заводится в журнале, если ЮKassa его не создала (T-05-49).

    Порядок «сначала SDK, потом запись в БД» — не деталь реализации, а условие
    этого свойства: строка `payments`, оставшаяся после отказа, означала бы
    платёж, которого у ЮKassa нет вовсе.
    """
    if form == "subscribe":
        await _subscribe(authed_client, failing=True)
    else:
        await _purchase(authed_client, failing=True)

    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("form", ["subscribe", "purchase"])
async def test_the_third_party_exception_text_never_reaches_the_screen(
    authed_client: AsyncClient, form: str
):
    """T-05-47: текст исключения SDK уходит в журнал и НИКОГДА на экран.

    Проверяется вся линия: и заголовок перенаправления, и страница, на которую
    оно привело.
    """
    if form == "subscribe":
        response = await _subscribe(authed_client, failing=True)
    else:
        response = await _purchase(authed_client, failing=True)

    assert SDK_FAILURE_TEXT not in response.text
    landing = await authed_client.get(response.headers["location"])
    assert response.headers["location"] == "/billing?error=payment"
    assert SDK_FAILURE_TEXT not in landing.text


def test_the_failure_is_recorded_in_the_journal_by_its_own_key():
    """T-05-48: у отказа есть след — ключ `payment_create_failed`.

    Отказ без следа — это repudiation: жалоба «я нажал, ничего не произошло»
    не проверяема ничем.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "services"
        / "payment_service.py"
    ).read_text(encoding="utf-8")

    assert "payment_create_failed" in source
    assert "PaymentCreationError" in source


# =============================================================================
# U3 — каждая ветка гарда несёт СВОЮ причину
# =============================================================================


@pytest.mark.asyncio
async def test_subscribing_with_payments_disabled_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Устаревшая страница ДОСТИЖИМА: администратор выключил платежи после
    отрисовки, и голый редирект читался бы как «кнопка сломана»."""
    test_settings.yookassa_enabled = False
    try:
        response = await _subscribe(authed_client)
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=disabled"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_purchasing_with_payments_disabled_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    test_settings.yookassa_enabled = False
    try:
        response = await _purchase(authed_client)
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=disabled"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("plan", ["platinum", "free", ""])
async def test_subscribing_to_a_plan_the_config_does_not_sell_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, plan: str
):
    """План, ушедший из конфига, и бесплатный тариф — одна причина: продать
    нечего. Обе ветки различимы на экране, а не сливаются в возврат на
    неизменившуюся страницу."""
    response = await _subscribe(authed_client, plan=plan)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=plan"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("index", ["99", "-1", "не число", ""])
async def test_purchasing_an_index_the_config_does_not_have_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, index: str
):
    """Нечисловой и внедиапазонный индексы ведут в ОДНУ ветку с одной причиной:
    для человека это один и тот же случай — «этого пакета нет»."""
    response = await _purchase(authed_client, index=index)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=package"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["/billing/subscribe", "/billing/purchase"])
async def test_a_cross_site_post_is_refused_without_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession, url: str
):
    """Чужому источнику причина отказа НЕ сообщается.

    Порядок проверок не меняется: сначала кто пришёл, потом откуда, потом что
    просит. 403 без тела и без перенаправления — межсайтовый запрос не имеет
    права узнать даже, включены ли платежи.
    """
    response = await _post(
        authed_client,
        url,
        {"plan": "basic", "package_index": FIRST_PACKAGE_INDEX},
        headers=CROSS_SITE,
    )

    assert response.status_code == 403
    assert "location" not in response.headers
    assert await _payments_count(db_session) == 0


def test_no_bare_redirect_without_a_reason_is_left_in_the_section():
    """Структурно: голых редиректов на `/billing` в обработчиках не осталось.

    Поведенческие тесты выше проверяют известные ветки; этот держит инвариант
    для веток, которых ещё нет.
    """
    source = BILLING_PY.read_text(encoding="utf-8")

    assert 'url="/billing"' not in source, (
        "в разделе снова появился возврат на неизменившуюся страницу без причины"
    )


# =============================================================================
# T-05-46 — множество причин ЗАКРЫТО
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code,message",
    [
        ("payment", MSG_PAYMENT),
        ("disabled", MSG_DISABLED),
        ("plan", MSG_PLAN),
        ("package", MSG_PACKAGE),
    ],
)
async def test_a_known_reason_code_prints_its_own_words(
    authed_client: AsyncClient, code: str, message: str
):
    response = await authed_client.get(f"/billing?error={code}")

    assert response.status_code == 200
    assert ALERT_MARKER in response.text, "плашки отказа на экране нет"
    assert message in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code",
    ["zzz_unknown_reason", "<script>alert(1)</script>", "paymentt", "PAYMENT"],
)
async def test_an_unknown_reason_code_prints_nothing_at_all(
    authed_client: AsyncClient, code: str
):
    """Подставить произвольный текст через адрес невозможно (T-05-46).

    Проверяется НЕ экранирование, а недостижимость: в разметку уходит строка из
    закрытого отображения, поэтому значение параметра не попадает на экран ни
    значением, ни атрибутом.
    """
    response = await authed_client.get(f"/billing?error={code}")

    assert response.status_code == 200
    assert ALERT_MARKER not in response.text, "неизвестный код нарисовал плашку"
    assert code not in response.text, "значение параметра напечатано на экране"


@pytest.mark.asyncio
async def test_the_section_without_the_parameter_prints_no_alert(
    authed_client: AsyncClient,
):
    """Парный тест: без него предыдущие зеленели бы на разметке без плашки."""
    response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert ALERT_MARKER not in response.text


@pytest.mark.asyncio
async def test_the_alert_stands_before_the_current_plan_block(
    authed_client: AsyncClient,
):
    """Причина читается РАНЬШЕ неизменившихся чисел.

    Плашка под блоком тарифа была бы прочитана после того, как человек уже
    сделал вывод «ничего не изменилось, кнопка сломана».
    """
    html = (await authed_client.get("/billing?error=payment")).text

    assert html.index(ALERT_MARKER) < html.index("Текущий тариф")


def test_the_reason_codes_of_the_handlers_are_exactly_the_known_set():
    """Ни одного кода в редиректе мимо отображения — и ни одного лишнего ключа.

    Коды выписаны в редиректах ЛИТЕРАЛАМИ намеренно: адрес обязан читаться
    целиком в той строке, где он строится. Расхождение литерала с отображением
    даёт молчаливый редирект без слов — ровно тот дефект, который закрывает этот
    план, — поэтому связь держится этой регрессией, а не аккуратностью автора.
    """
    from app.pages import billing as billing_module

    source = BILLING_PY.read_text(encoding="utf-8")
    used = set(re.findall(r"/billing\?error=([a-z]+)", source))

    assert used == {"payment", "disabled", "plan", "package"}, used
    for code in used:
        assert billing_module._payment_error_message(code), code
    assert billing_module._payment_error_message("zzz") == ""
    assert billing_module._payment_error_message(None) == ""


def test_the_get_handler_still_contains_no_write_path():
    """Параметр запроса ничего не меняет — только показывает (D-05)."""
    source = BILLING_PY.read_text(encoding="utf-8")
    rest = source[source.index("async def billing_page(") :]
    body = rest[: rest.find("\n@router")]

    assert not re.search(r"\b(db|session)\.(add|commit|flush)\(", body)


# =============================================================================
# IN-06 — управляющий элемент, упирающийся в молчаливый отказ
# =============================================================================


@pytest.mark.asyncio
async def test_an_expired_free_plan_is_offered_no_renewal_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Кнопка «Продлить» у бесплатного тарифа обещала оплату, которой нет.

    `free` есть в перечне конфига, поэтому проверка `current_in_config`
    пропускала его, а обработчик такой платёж отвергал: управляющий элемент,
    упирающийся в отказ, читается как сломанный платёжный путь.
    """
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="free",
            expires_at=datetime.now(timezone.utc) - timedelta(days=3),
            is_active=True,
        )
    )
    await db_session.commit()

    html = (await authed_client.get("/billing")).text

    assert 'value="free"' not in html, "бесплатный тариф получил кнопку оплаты"


@pytest.mark.asyncio
async def test_an_expired_paid_plan_still_keeps_its_renewal_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: правка IN-06 не должна снести предложение продлить платный
    тариф — именно ради него блок и существует (D-07)."""
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

    html = (await authed_client.get("/billing")).text

    assert "истёк" in html
    assert 'value="basic"' in html

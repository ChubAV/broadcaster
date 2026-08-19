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
import ast
import inspect
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.billing.subscription_period import add_one_month
from app.config import Settings
from app.constants import PLAN_ORDER
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import create_payment, handle_webhook
from tests.test_pages.test_billing_section import NON_FINITE_AMOUNTS

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
MSG_DOWNGRADE = (
    "Перейти на младший тариф можно после окончания оплаченного срока — "
    "оплаченные дни не сгорают"
)
# Отказ по потолку одновременных подписочных намерений (план 05-17). Строка
# НАЗЫВАЕТ ПРИЧИНУ и говорит, ЧТО ДЕЛАТЬ: человек обязан понять, что незакрытой
# осталась ЕГО ПРЕДЫДУЩАЯ оплата, а не что кнопка сломана и не что с него
# списали деньги и не зачли — это отдельный класс беды, и путать их дороже, чем
# молчать. Числа часов срока давности здесь НЕТ: константа живёт в сервисе, и
# копия в копирайте разошлась бы с ней молча при первой же правке.
MSG_PENDING = (
    "Предыдущая оплата ещё не завершена — дождитесь её результата "
    "или попробуйте позже"
)

# Подпись четвёртого состояния CTA карточки плана. Она обязана НАЗЫВАТЬ ПРИЧИНУ,
# по которой кнопки нет: карточка без кнопки и без слов читается как поломка
# витрины, а не как правило продукта.
CAPTION_DOWNGRADE = (
    "Переход на младший тариф — после окончания оплаченного срока: "
    "оплаченные дни не сгорают"
)

# Признак нарисованной плашки отказа. Проверяется ИМЕННО он, а не наличие слова
# из текста: слово может прийти из соседнего блока экрана, обёртка — только из
# ветки показа причины.
ALERT_MARKER = "data-payment-error"

# ЦЕНЫ ПРЕЙСКУРАНТА — СТРОКАМИ В `Decimal`, НИКОГДА ЧИСЛАМИ С ПЛАВАЮЩЕЙ ТОЧКОЙ.
# Это те же значения, что отдаёт `parsed_plan_limits` умолчаний конфига и что
# читает `_plan_price` денежного пути (Basic 1490 ₽, Pro 4900 ₽). Двоичная дробь
# дала бы разные ответы на одинаковых суммах в зависимости от записи, а
# `payments.amount_value` объявлена строкой намеренно.
BASIC_PRICE = Decimal("1490.00")
PRO_PRICE = Decimal("4900.00")


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
    payment_id: str = "yoo_1",
):
    """POST формы оплаты с подменённым SDK.

    ИДЕНТИФИКАТОР ПЛАТЕЖА ПАРАМЕТРИЗОВАН, А НЕ ЗАШИТ. Пока тест заводил ровно
    один платёж, разницы не было; сценариям стадии ПРИМЕНЕНИЯ нужны ДВА платежа
    одного пользователя, и с одинаковым `yookassa_payment_id` второй заводился
    бы дубликатом — выборка платежа в `handle_webhook` поднимала бы
    `MultipleResultsFound` вместо воспроизведения дефекта. Значение по умолчанию
    оставлено прежним, поэтому ни один существующий тест не меняется.
    """
    sdk = _failing_sdk() if failing else _healthy_sdk(payment_id)
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
    client: AsyncClient,
    plan: str = "basic",
    *,
    failing: bool = False,
    headers=None,
    payment_id: str = "yoo_1",
):
    return await _post(
        client,
        "/billing/subscribe",
        {"plan": plan},
        failing=failing,
        headers=headers,
        payment_id=payment_id,
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
        ("downgrade", MSG_DOWNGRADE),
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
async def test_the_pending_reason_prints_its_own_words(authed_client: AsyncClient):
    """Попавший под потолок получает СЛОВА, а не молчаливый редирект.

    Отдельным именем, а не строкой в перечне соседа, потому что предмет у него
    свой: связь нового кода с его строкой — последнее звено цепи «отказ сервиса
    → код причины → отображение → плашка», и разрыв ЛЮБОГО звена даёт ту самую
    возвращённую без слов страницу, которую фаза закрывала планом 05-10.
    """
    response = await authed_client.get("/billing?error=pending")

    assert response.status_code == 200
    assert ALERT_MARKER in response.text, "плашки отказа на экране нет"
    assert MSG_PENDING in response.text


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

    assert used == {
        "payment",
        "disabled",
        "plan",
        "package",
        "downgrade",
        # Потолок одновременных подписочных намерений (план 05-17). Код обязан
        # войти в ОБА места сразу — в литерал редиректа и в отображение, — иначе
        # эта регрессия краснеет. Правка её множества и есть часть работы, а не
        # побочный эффект: тест держит связь, которую иначе держала бы только
        # аккуратность автора.
        "pending",
    }, used
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


# =============================================================================
# C2 / WR-02 — семантика смены тарифа, вариант `upgrade-only`
# =============================================================================
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА (чекпойнт плана 05-10): повышение разрешено и НЕ сжигает
# оплаченный остаток; понижение не предлагается и не принимается.
#
# ЧТО ЭТО ЗАКРЫВАЕТ. До решения `_extend_subscription` перезаписывал план
# безусловно, а срок двигал от существующего: подписчик Pro с 25 неистёкшими
# днями, купивший Basic, немедленно понижался и сохранял эти дни — то есть
# 4 900 ₽, уплаченные за них, превращались в дни младшего тарифа. Путь был
# ДОСТИЖИМ: карточка чужого платного плана рисовала «Перейти на {план}», а
# обработчик такой платёж принимал.
#
# ЧЕМ ЭТО ОПЛАЧЕНО (принятая цена варианта, а не недосмотр). Повышение отдаёт
# лимиты старшего тарифа на оставшиеся дни младшего бесплатно (T-05-51).
# Применения лимитов в системе нет вовсе (D-08), поэтому сегодня «лимиты Pro»
# не дают доступа ни к чему сверх показа.
#
# ЗАЩИТА НА ОБОИХ КОНЦАХ. Карточка младшего плана не рисует CTA, а обработчик
# отвергает такой платёж названной причиной — устаревшая страница безопасна.
# Прохибиция 05-01 («не сжигать неистраченный остаток») СОБЛЮДЕНА: ни один
# разрешённый переход остатка не сжигает, переопределять её не пришлось.

# Конфиг с планом, которого НЕТ в PLAN_ORDER. Отдельная константа, потому что
# её читают два теста отказа по умолчанию.
UNRANKED_PLAN_LIMITS = json.dumps(
    [
        {
            "id": "free",
            "name": "Free",
            "price": "0.00",
            "ads": 3,
            "groups": 5,
            "sends": 300,
            "accounts": 1,
        },
        {
            "id": "basic",
            "name": "Basic",
            "price": "1490.00",
            "ads": 15,
            "groups": 30,
            "sends": 5000,
            "accounts": 5,
        },
        {
            "id": "platinum",
            "name": "Platinum",
            "price": "9900.00",
            "ads": None,
            "groups": None,
            "sends": 50000,
            "accounts": 20,
        },
    ]
)

# Конфиг, из которого ВЫПАЛ `pro`. Имя константы называет ровно то, чего в ней
# нет, потому что предмет проверки — исход для плана, отсутствующего в перечне.
#
# ЧЕМ ОНА ОТЛИЧАЕТСЯ ОТ `UNRANKED_PLAN_LIMITS`, И БЕЗ ЭТОЙ ФРАЗЫ СЛЕДУЮЩИЙ
# ЧИТАТЕЛЬ СОЧТЁТ ИХ ДУБЛИКАТАМИ. Та описывает план, которого нет в `PLAN_ORDER`
# (ранг незнаком, отказ по умолчанию); эта — план, который в `PLAN_ORDER` ЕСТЬ,
# но которого нет в конфиге, то есть ранг известен, переход разрешён, а ЦЕНУ
# прочитать нельзя. Перечень тарифов правится ОКРУЖЕНИЕМ, и код называет такое
# расхождение нормальным состоянием (`payment_service.py:790-796`): одна правка
# `.env` — и каждое повышение на переименованный план идёт этим путём.
PLAN_LIMITS_WITHOUT_PRO = json.dumps(
    [
        {
            "id": "free",
            "name": "Free",
            "price": "0.00",
            "ads": 3,
            "groups": 5,
            "sends": 300,
            "accounts": 1,
        },
        {
            "id": "basic",
            "name": "Basic",
            "price": "1490.00",
            "ads": 15,
            "groups": 30,
            "sends": 5000,
            "accounts": 5,
        },
    ]
)


async def _seed_live_subscription(
    db: AsyncSession, plan: str, *, days: int = 25
) -> datetime:
    """Действующая (неистёкшая) подписка владельца. Возвращает её срок."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    db.add(
        Subscription(
            user_id=(await _current_user(db)).id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
        )
    )
    await db.commit()
    return expires_at


async def _subscription_rows(db: AsyncSession) -> list[Subscription]:
    owner = await _current_user(db)
    return list(
        (
            await db.execute(
                select(Subscription).where(Subscription.user_id == owner.id)
            )
        )
        .scalars()
        .all()
    )


def _aware(value: datetime) -> datetime:
    """SQLite отдаёт колонку с таймзоной NAIVE, PostgreSQL — aware."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def test_the_order_of_plans_is_declared_and_not_derived_from_price():
    """Порядок тарифов объявлен ЯВНО, а не выведен из цены.

    Цена настраивается окружением. Вывод порядка из неё сделал бы порядок
    тарифов конфигурируемым ПОБОЧНО: правка цены Basic выше цены Pro молча
    превратила бы понижение в повышение и разрешила бы отвергаемый сегодня
    переход.
    """
    assert isinstance(PLAN_ORDER, tuple), "порядок обязан быть неизменяемым"
    assert PLAN_ORDER == ("free", "basic", "pro")
    assert len(set(PLAN_ORDER)) == len(PLAN_ORDER), "повтор в порядке тарифов"


def test_every_shipped_plan_of_the_config_has_a_rank():
    """Ни один план УМОЛЧАНИЯ конфига не остаётся без ранга.

    Отказ по умолчанию — правильное поведение для незнакомого плана, но если в
    него попадает план, который проект отгружает сам, то отказ становится не
    защитой, а поломкой: пользователь Pro не смог бы даже продлиться.
    """
    shipped = {
        plan["id"]
        for plan in json.loads(Settings.model_fields["plan_limits"].default)
    }

    assert shipped <= set(PLAN_ORDER), shipped - set(PLAN_ORDER)


@pytest.mark.asyncio
async def test_an_upgrade_is_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повышение остаётся открытым: растущему клиенту не отказывают в продаже."""
    await _seed_live_subscription(db_session, "basic")

    response = await _subscribe(authed_client, plan="pro")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.plan == "pro"


@pytest.mark.asyncio
async def test_an_upgrade_does_not_burn_the_paid_remainder(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Прохибиция 05-01 соблюдена: оплаченный остаток переживает переход.

    ⚠️ ИМЯ ПРЕЖНЕЕ, А ЧИСЛО ДНЕЙ ДРУГОЕ, И ЭТО РЕШЕНИЕ ВЛАДЕЛЬЦА, А НЕ ПРАВКА
    ПОД РЕЗУЛЬТАТ (форма `convert-remainder`, чекпойнт задачи 1 плана 05-18).
    Прежняя редакция утверждала, что остаток переживает переход ДНЯМИ: 25 дней
    Basic оставались 25 днями Pro, и следующий оператор добавлял к ним полный
    оплаченный месяц. На безобидном масштабе 25 дней это выглядело щедростью, но
    ровно этот механизм на масштабе года и был гэпом 1 раунда 5: двенадцать
    предоплаченных месяцев Basic (17 880 ₽) плюс один платёж Pro (4 900 ₽) давали
    тринадцать месяцев Pro при прейскуранте 63 700 ₽. Тест закреплял механизм
    утечки как ЖЕЛАЕМОЕ поведение — поэтому переписан, а не удалён: удаление
    дефекта вместе с записью о нём запрещено этой фазой.

    КАКАЯ ВЕЛИЧИНА ТЕПЕРЬ ПЕРЕЖИВАЕТ ПЕРЕХОД — ДЕНЬГИ, А НЕ ДНИ. Остаток
    пересчитывается по отношению цен: 25 дней Basic по 1490 ₽/мес стоят столько
    же, сколько 7 дней Pro по 4900 ₽/мес. Обещание «оплаченный остаток не
    сгорает» остаётся верным — сгоревшим считался бы исход «ровно месяц от
    сегодня», и НИЖНЕЕ утверждение держит именно его. ВЕРХНЕЕ держит то, ради
    чего решение принято: остаток не переносится по дням.
    """
    current = await _seed_live_subscription(db_session, "basic", days=25)

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "переход не должен заводить вторую строку"
    assert rows[0].plan == "pro", "оплаченный старший тариф не применён"

    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > add_one_month(now), (
        "оплаченный остаток сгорел: повышение выдало ровно месяц от сегодня"
    )

    remainder_days = (_aware(current) - now).days
    converted_days = int(Decimal(remainder_days) * BASIC_PRICE / PRO_PRICE)
    expected = add_one_month(now + timedelta(days=converted_days))
    assert abs(_aware(rows[0].expires_at) - expected) <= timedelta(days=2), (
        "остаток перенесён ПО ДНЯМ, а не по деньгам: 25 дней Basic стоят "
        f"{converted_days} дней Pro, а не 25"
    )


@pytest.mark.asyncio
async def test_a_downgrade_is_refused_with_a_named_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Понижение отвергается НА ВХОДЕ и говорит, почему.

    Отвергнуть молча было бы тем же дефектом, который закрывает задача 1:
    устаревшая страница достижима, и голый редирект читался бы как «кнопка
    сломана».
    """
    await _seed_live_subscription(db_session, "pro")

    response = await _subscribe(authed_client, plan="basic")

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=downgrade"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_renewing_the_own_live_plan_is_still_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Гард смены плана не задевает продление СВОЕГО тарифа.

    Самый вероятный способ сломать этот вариант — отвергнуть вместе с
    понижением и продление, у которого план тоже «уже есть».
    """
    await _seed_live_subscription(db_session, "pro")

    response = await _subscribe(authed_client, plan="pro")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    assert await _payments_count(db_session) == 1


@pytest.mark.asyncio
async def test_a_first_purchase_from_free_is_still_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подписки нет вовсе — сжигать нечего, и гард не участвует."""
    response = await _subscribe(authed_client, plan="basic")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    assert await _payments_count(db_session) == 1


@pytest.mark.asyncio
async def test_a_downgrade_after_the_period_has_ended_is_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Истёкший срок снимает гард: остатка, который можно сжечь, больше нет.

    Правило защищает УПЛАЧЕННОЕ, а не запирает пользователя в тарифе навсегда.
    """
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="pro",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
        )
    )
    await db_session.commit()

    response = await _subscribe(authed_client, plan="basic")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "live_plan,requested", [("platinum", "basic"), ("basic", "platinum")]
)
async def test_a_plan_without_a_rank_fails_closed(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    test_settings,
    live_plan: str,
    requested: str,
):
    """ОТКАЗ ПО УМОЛЧАНИЮ: незнакомому плану ранг не угадывается.

    Перечень тарифов правится переменной окружения, а `PLAN_ORDER` — кодом.
    Разойтись они могут в любую сторону, и в обеих «догадка» стоила бы денег:
    угаданное повышение подарило бы месяц, угаданное понижение сожгло бы
    остаток. Отказ стоит одного лишнего экрана, догадка — уплаченных денег.
    """
    test_settings.plan_limits = UNRANKED_PLAN_LIMITS
    try:
        await _seed_live_subscription(db_session, live_plan)
        response = await _subscribe(authed_client, plan=requested)
    finally:
        test_settings.plan_limits = Settings.model_fields["plan_limits"].default

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=downgrade"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_the_lower_plan_card_explains_itself_instead_of_offering_a_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Четвёртое состояние CTA: подпись С ПРИЧИНОЙ вместо кнопки.

    Карточка без кнопки и без слов читается как поломка витрины. Асимметрия
    («вверх можно, вниз нельзя») обязана быть объяснена НА ЭКРАНЕ, а не только
    в коде: пользователь кода не читает.
    """
    await _seed_live_subscription(db_session, "pro")

    html = (await authed_client.get("/billing")).text

    assert CAPTION_DOWNGRADE in html, "младший тариф не объяснил отсутствие кнопки"
    assert 'value="basic"' not in html, "младший тариф всё ещё обещает оплату"
    # Витрина при этом НЕ гаснет: карточка младшего плана на месте целиком.
    assert "Basic" in html
    assert "data-plans" in html


@pytest.mark.asyncio
async def test_the_higher_plan_card_still_offers_the_upgrade(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: подпись не должна встать на карточки, которым она не нужна.

    Без него предыдущий тест зеленел бы на разметке, погасившей ВСЕ кнопки.
    """
    await _seed_live_subscription(db_session, "basic")

    html = (await authed_client.get("/billing")).text

    assert 'value="pro"' in html, "повышение перестало предлагаться"
    assert CAPTION_DOWNGRADE not in html, "подпись встала на карточку повышения"


@pytest.mark.asyncio
async def test_without_a_live_subscription_every_paid_card_keeps_its_button(
    authed_client: AsyncClient,
):
    """Гард не трогает витрину пользователя без действующей подписки."""
    html = (await authed_client.get("/billing")).text

    assert 'value="basic"' in html
    assert 'value="pro"' in html
    assert CAPTION_DOWNGRADE not in html


# =============================================================================
# СТАДИЯ ПРИМЕНЕНИЯ — правило `upgrade-only` там, где приходят деньги
# =============================================================================
#
# ЧЕМ ЭТИ ТЕСТЫ ОТЛИЧАЮТСЯ ОТ СОСЕДНИХ. Все тесты выше останавливаются на 302
# гарда формы — то есть на стадии НАМЕРЕНИЯ, где решается, продавать ли. Ниже
# проверяется вторая стадия: что подтверждённый платёж делает с УЖЕ ДЕЙСТВУЮЩЕЙ
# подпиской. До этого плана регрессии на неё не было ни одной, и правило
# `upgrade-only` существовало ровно на входе: `_apply_extension` перезаписывал
# `subscription.plan` безусловно.
#
# ВОСПРОИЗВЕДЁННЫЙ ДЕФЕКТ (гэп 1, 05-VERIFICATION.md). Пользователь без
# подписки нажимает «Оплатить» дважды — сначала Pro, потом Basic. Гард формы в
# этом сценарии не срабатывает ВОВСЕ: на момент ОБОИХ нажатий действующей
# подписки нет, сжигать нечего. Оба платежа подтверждаются, и оплаченный месяц
# старшего тарифа становится днями младшего.


def _app_settings(plan_limits: str | None = None) -> Settings:
    """Настоящие `Settings` с УМОЛЧАНИЯМИ конфига, а не MagicMock.

    Нужны стадии применения с решения D-29: цена действующего плана читается из
    `parsed_plan_limits`, то есть доля месяца считается по НАСТОЯЩИМ ценам
    проекта (Free 0 ₽, Basic 1490 ₽, Pro 4900 ₽). MagicMock здесь не годится
    принципиально: его `parsed_plan_limits` не список словарей, и тест зеленел бы
    на откате к полному месяцу — то есть ровно на том исходе, который D-29
    отменяет.

    Два обязательных поля задаются теми же значениями, что в `tests/conftest.py`:
    боевой `.env` в суите не читается, а `Settings()` без них не строится.

    `plan_limits` СО ЗНАЧЕНИЕМ `None` ОЗНАЧАЕТ «УМОЛЧАНИЕ КОНФИГА», и передаётся
    он в `Settings(...)` ТОЛЬКО когда задан явно. Умолчание выбрано так, что ни
    один существующий вызов помощника не меняется: перечень тарифов нужен ровно
    тем тестам, чей предмет — исход при плане, ВЫПАВШЕМ из перечня, а всем
    остальным подмена перечня молча сменила бы цены под ногами (T-05-143).
    """
    if plan_limits is None:
        return Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            secret_key="test-secret-key",
        )
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
        plan_limits=plan_limits,
    )


async def _confirm(db: AsyncSession, payment_id: str = "yoo_1") -> bool:
    """Подтверждённое уведомление ЮKassa по конкретному платежу.

    ⚠️ СИГНАТУРА ОСТАВЛЕНА ДОСЛОВНОЙ, И ЭТО ПРЕДМЕТ КРИТЕРИЯ ПРИЁМКИ, А НЕ ВКУС.
    Помощника зовут больше двадцати тестов файла; вписать перечень тарифов ПРЯМО
    В НЕГО значило бы тронуть объявление, которое читают все они, ради двух,
    которым перечень нужен. Общий случай вынесен в `_confirm_with_plan_limits`
    ниже, а здесь остался его частный вызов — тот же, что и был, с умолчаниями
    конфига.
    """
    return await _confirm_with_plan_limits(db, payment_id)


async def _confirm_with_plan_limits(
    db: AsyncSession,
    payment_id: str = "yoo_1",
    *,
    plan_limits: str | None = None,
) -> bool:
    """Подтверждённое уведомление ЮKassa при НАЗВАННОМ перечне тарифов.

    `add_messages` подменяется по образцу соседних тестов: подписочная ветка его
    не зовёт, но подмена держит тест независимым от порядка ветвления.

    `get_settings` подменяется по образцу `_post`, и с решения D-29 это не
    оформление: ветка отказа читает цену действующего плана из конфига, а
    `Settings()` в суите не строится — боевого `.env` здесь нет.

    ПОДМЕНА ЖИВЁТ ВНУТРИ `with` И НЕ ПЕРЕЖИВАЕТ ВЫЗОВА. Перечень тарифов —
    глобальное для денежного пути состояние, и утечка его на соседний тест
    сменила бы цены там, где предмет проверки другой (T-05-143). Поэтому он
    приезжает АРГУМЕНТОМ, а не правкой модульной переменной.
    """
    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ), patch(
        "app.services.payment_service.get_settings",
        return_value=_app_settings(plan_limits),
    ):
        return await handle_webhook(
            db,
            event="payment.succeeded",
            payment_data={"object": {"id": payment_id}},
        )


@pytest.mark.asyncio
async def test_a_confirmed_lower_plan_does_not_strip_the_higher_one_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Воспроизведение верификатора: младший тариф не снимает уплаченный старший.

    ПОРЯДОК ЗДЕСЬ — ПРЕДМЕТ ПРОВЕРКИ, А НЕ ОФОРМЛЕНИЕ. Оба платежа заводятся ДО
    первого уведомления, потому что именно так дефект и достижим: пока подписки
    нет, гард формы не участвует, и «понижение» проскакивает мимо него обоими
    нажатиями.

    РАЗДЕЛЕНИЕ СРОКОВ ЧИСЛОВОЕ. Один календарный месяц — не больше 31 дня, два —
    не меньше 59; порог в 45 дней лежит между ними, поэтому промах в любую
    сторону однозначен: «срок сдвинут один раз» и «сдвинут дважды» не могут
    оказаться по одну сторону порога.

    ⚠️ УТВЕРЖДЕНИЕ О СРОКЕ ПОМЕНЯЛО ЗНАК ВМЕСТЕ С РЕШЕНИЕМ ВЛАДЕЛЬЦА D-29, И ЭТО
    ГЛАВНОЕ В ЭТОЙ ПРАВКЕ. Раньше здесь стояло `> now + 45 дней` с пояснением
    «деньги второго платежа не превратились в дни» — и ровно это утверждение
    ЗАКРЕПЛЯЛО обход цены как ожидаемое поведение: платёж `basic` за 1490 ₽
    покупал полный календарный месяц действующего `pro` стоимостью 4900 ₽, и
    повторов не ограничивало ничто. Решение D-29: отвергнутый платёж продолжает
    давать дни, но ПО УПЛАЧЕННОМУ тарифу — долю месяца по отношению уплаченной
    суммы к цене действующего плана.

    Утверждение стало ДВУСТОРОННИМ, и обе стороны несущие: нижняя граница
    (`> now + 33 дня`) держит принцип «деньги ВСЕГДА превращаются в дни» — без
    неё тест зеленел бы на коде, не выдавшем ничего; верхняя (`< now + 45 дней`)
    держит то, ради чего решение принято, — второй платёж НЕ купил второго
    полного месяца старшего тарифа. Порог 45 дней сохранён и поменял сторону:
    именно это и делает регрессию доказательной.

    ⚠️ ВТОРОЙ ПЛАТЁЖ ЗАВОДИТСЯ НАПРЯМУЮ И БЕЗ ЗАПИСАННОГО ОТВЕТА (D-28). Пока
    ответа гарда на платеже не существовало, форма годилась: оба нажатия
    проходили мимо гарда, потому что подписки на их момент не было. С появлением
    колонки `switch_authorized` форма записывает на ОБА платежа разрешение
    `True` — и путь, который проверяет ЭТОТ тест (решение принимает ПРАВИЛО),
    через форму больше не достижим. Достижим он остаётся у строк, заведённых до
    ревизии `0019`, и именно они здесь и сеются. Путь, где оба платежа несут
    записанное `True`, ЭТИМ ПЛАНОМ НЕ ЗАКРЫТ и закрывается планом `05-17`
    потолком одновременных намерений (`cap-different-plan`).
    """
    await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None
    )

    assert await _confirm(db_session, "yoo_pro") is True
    assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "два платежа завели две подписки"
    assert rows[0].plan == "pro", "оплаченный старший тариф снят младшим платежом"
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=33), (
        "деньги второго платежа не превратились в дни — исход «взяли и не выдали "
        "ничего», названный решением D-29 худшим"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "платёж младшего тарифа купил ПОЛНЫЙ месяц действующего старшего: "
        "1490 ₽ за месяц Pro стоимостью 4900 ₽ (D-29 нарушен)"
    )


@pytest.mark.asyncio
async def test_the_preserved_plan_is_visible_in_the_log(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Расхождение уплаченного и действующего тарифа оставляет свой след.

    Без собственного ключа исход прячется за `subscription_payment_succeeded`,
    который печатает план ПЛАТЕЖА как обычный успех: разбирающему обращение
    пользователя опереться не на что. Уровень `warning`, а не `info` — платёж
    принят, дни выданы, но уплаченный тариф применён НЕ был.

    ⚠️ ВТОРОЙ ПЛАТЁЖ БЕЗ ЗАПИСАННОГО ОТВЕТА — по той же причине, что у соседа
    выше: ключ `subscription_plan_preserved` пишется только там, где переход
    ОТВЕРГНУТ, а через форму после D-28 оба платежа уносят разрешение `True` и
    отказа не возникает ни у одного.
    """
    await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None
    )

    await _confirm(db_session, "yoo_pro")
    with patch("app.services.payment_service.logger") as spy:
        await _confirm(db_session, "yoo_basic")

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved, "сохранение старшего тарифа не оставило следа в журнале"
    fields = preserved[0].kwargs
    assert fields.get("plan") == "pro", "не назван сохранённый тариф"
    assert fields.get("paid_plan") == "basic", "не назван уплаченный тариф"
    assert fields.get("yookassa_id") == "yoo_basic"
    assert fields.get("user_id") == (await _current_user(db_session)).id


@pytest.mark.asyncio
async def test_a_confirmed_higher_plan_is_applied_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повышение на стадии применения ОСТАЁТСЯ повышением.

    Самый вероятный способ сломать этот план — отвергнуть вместе с понижением и
    повышение, перепутав направление сравнения рангов.
    """
    await _seed_live_subscription(db_session, "basic")

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "оплаченное повышение не применено"


@pytest.mark.asyncio
async def test_renewing_the_own_plan_still_moves_the_date_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Продление СВОЕГО тарифа новой сверкой не задето: план тот же, срок дальше."""
    current = await _seed_live_subscription(db_session, "pro", days=25)

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "продление перестало двигать срок от существующего"
    )


async def _seed_subscription_payment(
    db: AsyncSession,
    plan: str | None,
    payment_id: str,
    *,
    switch_authorized: bool | None = None,
    amount: str = "1490.00",
) -> Payment:
    """Подписочный платёж в состоянии «уведомление ещё не приходило».

    Строка заводится НАПРЯМУЮ, а не формой: оба сценария ниже описывают платежи,
    которые форма завести не может вовсе — с пустым планом (поле обязательное) и
    с планом, которого нет в конфиге. Дефект при этом достижим: платёж мог быть
    заведён до того, как конфиг разошёлся с `PLAN_ORDER`.

    Владелец платежа — пользователь, которого заводит фикстура `authed_client`;
    поэтому тесты, ходящие только в БД, её всё равно запрашивают.

    `switch_authorized` — ЗАПИСАННЫЙ ОТВЕТ ГАРДА (D-28). Умолчание `None`
    означает «правило не спрашивали», то есть строку, заведённую ДО ревизии
    `0019`; именно на таких строках живёт остаточный путь, который форма после
    плана `05-17` завести уже не сможет. Умолчание оставлено прежним по смыслу,
    поэтому ни один существующий вызов помощника не меняется.

    `amount` — УПЛАЧЕННАЯ СУММА, и она перестала быть безразличной с решением
    D-29: платёж, чей план не применён, покупает долю месяца ПО НЕЙ, а не
    календарный месяц действующего тарифа. Умолчание — цена Basic, то есть
    прежнее зашитое значение; сценарии, где важна разница цен, называют её явно.
    """
    payment = Payment(
        user_id=(await _current_user(db)).id,
        yookassa_payment_id=payment_id,
        status="pending",
        amount_value=amount,
        amount_currency="RUB",
        kind="subscription",
        plan=plan,
        messages_count=None,
        package_name=None,
        switch_authorized=switch_authorized,
    )
    db.add(payment)
    await db.commit()
    return payment


@pytest.mark.asyncio
async def test_a_payment_without_a_plan_moves_the_date_and_leaves_the_plan_alone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пустой план платежа двигает срок и НЕ трогает действующий тариф.

    Ветка существовала в коде и до этого плана, но регрессии не имела ни одной.
    Сверка ранга встала рядом с ней, поэтому проверка нужна именно теперь:
    `switch_is_refused("pro", "")` вернул бы `True` — и без явного выхода по
    пустому плану ветка начала бы писать в журнал строку о расхождении, которого
    не было.
    """
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(db_session, None, "yoo_noplan")

    assert await _confirm(db_session, "yoo_noplan") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "пустой план платежа переписал действующий"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "оплаченные дни не выданы"
    )


@pytest.mark.asyncio
async def test_a_paid_plan_without_a_rank_keeps_the_live_plan_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Зеркало `test_a_plan_without_a_rank_fails_closed` на стадии применения.

    Тот держит отказ по умолчанию на входе, этот — там, где приходят деньги.
    Инвариант один и тот же: догадка о ранге незнакомого плана стоит денег в обе
    стороны. Разница только в цене отказа — на входе это лишний экран, здесь
    отказать платежу нельзя вовсе, поэтому «отказ» означает сохранение
    действующего тарифа при выданных днях.

    ⚠️ ЧИСЛО ДНЕЙ ИЗМЕНИЛОСЬ ВМЕСТЕ С РЕШЕНИЕМ D-29, ПРЕДМЕТ ТЕСТА — НЕТ. Раньше
    здесь стояло `> current + 27 дней`, то есть отказ покупал ПОЛНЫЙ месяц
    действующего Pro за 1490 ₽. Теперь он покупает долю по уплаченному. Держится
    ровно то же, что и раньше: ранг не угадан И дни выданы, — но верхняя граница
    добавлена, потому что без неё тест снова закреплял бы обход цены.
    """
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(db_session, "platinum", "yoo_unranked")

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_unranked") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "незнакомому плану угадали ранг"
    assert _aware(rows[0].expires_at) > current, "оплаченные дни не выданы"
    assert _aware(rows[0].expires_at) < current + timedelta(days=27), (
        "отвергнутый платёж купил полный месяц действующего тарифа (D-29)"
    )
    assert any(
        call.args and call.args[0] == "subscription_plan_preserved"
        for call in spy.warning.call_args_list
    ), "отказ по умолчанию не оставил следа"


@pytest.mark.asyncio
async def test_the_first_subscription_still_takes_its_plan_from_the_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Первая покупка с Free заводит подписку с планом ИЗ ПЛАТЕЖА.

    Ветка вставки сверку ранга не получила и получить не должна: подписки нет,
    защищать нечего, а сравнение ранга с пустотой отвергло бы первую же покупку.
    Тест держит её от правки «заодно».
    """
    await _subscribe(authed_client, plan="basic")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "basic", "первая подписка не взяла план из платежа"
    assert _aware(rows[0].expires_at) > datetime.now(timezone.utc)


# =============================================================================
# СТАДИЯ ПРИМЕНЕНИЯ НА ИСТЁКШЕМ СРОКЕ — ветка, которой у соседнего раздела нет
# =============================================================================
#
# ЧЕМ ЭТОТ РАЗДЕЛ ОТЛИЧАЕТСЯ ОТ ПРЕДЫДУЩЕГО. Там КАЖДЫЙ тест сеет ЖИВУЮ подписку
# (`_seed_live_subscription`), и ровно поэтому суита из 1665 тестов оставалась
# зелёной при работающем блокере: единственный тест истёкшего срока
# (`test_a_downgrade_after_the_period_has_ended_is_accepted`) останавливается на
# 302 гарда формы и до `handle_webhook` не доходит вовсе. Стадия ПРИМЕНЕНИЯ на
# истёкшем сроке не была покрыта ни одним тестом.
#
# ВОСПРОИЗВЕДЁННЫЙ ДЕФЕКТ (гэп 1 раунда 3, `05-VERIFICATION.md`). Подписка `pro`,
# срок истёк вчера; пользователь покупает `basic` — гард формы его ПРОПУСКАЕТ
# (защищать нечего). Уведомление подтверждает платёж, и `_apply_extension` зовёт
# правило БЕЗУСЛОВНО: план остаётся `pro`. Деньги взяты за тариф, который не
# выдан, а со следующей попытки подписка снова живая и гард отвечает
# `?error=downgrade` — понижение становится недостижимым на всё время жизни
# аккаунта.
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА (чекпойнт плана 05-13): `apply-after-expiry` — истёкший срок
# снимает отказ на ОБЕИХ стадиях, оплаченное понижение применяется.


async def _seed_expired_subscription(
    db: AsyncSession, plan: str, *, days_ago: int = 1
) -> datetime:
    """Зеркало `_seed_live_subscription` с ПРОШЕДШИМ сроком. Возвращает срок.

    Срок возвращается, чтобы тест умел отличить «сдвинут от старого срока» от
    «сдвинут от сегодня»: правило D-04 требует второго, и без возврата исходной
    величины разница была бы неотличима.
    """
    expires_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.add(
        Subscription(
            user_id=(await _current_user(db)).id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
        )
    )
    await db.commit()
    return expires_at


@pytest.mark.asyncio
async def test_an_expired_period_lets_the_paid_plan_through_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Прямое воспроизведение верификатора: истёкший срок ВЫДАЁТ уплаченный план.

    РАЗДЕЛЕНИЕ СРОКОВ ЧИСЛОВОЕ И ДВУСТОРОННЕЕ. Месяц от СЕГОДНЯ лежит между 28 и
    31 днём, поэтому проверяются ОБЕ границы — больше «сейчас + 27 дней» и меньше
    «сейчас + 45 дней». Одной верхней границы мало: без нижней тест зеленел бы на
    коде, который дней не выдал вовсе или посчитал их от прошедшей даты.
    """
    await _seed_expired_subscription(db_session, "pro")

    await _subscribe(authed_client, plan="basic")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "подтверждение завело вторую строку подписки"
    assert rows[0].plan == "basic", (
        "деньги взяты за тариф, который не выдан: истёкший срок оставил "
        "старший план на стадии применения"
    )
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=27), (
        "оплаченные дни не выданы"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "срок посчитан не от сегодня — D-04 нарушен"
    )


@pytest.mark.asyncio
async def test_the_expired_period_writes_no_preserved_plan_warning(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На этом пути сохранять нечего — значит и следа о сохранении быть не должно.

    Ключ `subscription_plan_preserved` читается разбирающим обращение как «тариф
    сохранён, уплаченный не применён». Написать его там, где тариф КАК РАЗ выдан,
    значило бы соврать журналу (T-05-65).
    """
    await _seed_expired_subscription(db_session, "pro")
    await _subscribe(authed_client, plan="basic")

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session) is True

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved == [], (
        "журнал сообщает о сохранении тарифа там, где тариф выдан"
    )


@pytest.mark.asyncio
async def test_an_expired_period_still_renews_the_own_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Продление СВОЕГО тарифа на истёкшем сроке не задето правкой «заодно».

    Равные планы правилом не задеваются вовсе, и снятие отказа по сроку не имеет
    права это изменить: подписчик Pro, пропустивший месяц, продлевает Pro.
    """
    await _seed_expired_subscription(db_session, "pro")

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "продление своего тарифа сменило план"
    now = datetime.now(timezone.utc)
    assert now + timedelta(days=27) < _aware(rows[0].expires_at) < now + timedelta(
        days=45
    ), "срок продления посчитан не от сегодня"


@pytest.mark.asyncio
async def test_a_live_period_still_keeps_the_higher_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПАРНЫЙ тест: истёкшего срока здесь НЕТ, и отказ обязан остаться.

    Без него первый тест раздела зеленел бы на коде, снявшем отказ вообще везде —
    то есть на возврате ровно того дефекта, который закрыл план 05-11. Платёж
    заводится напрямую, потому что гард формы такую покупку не пропустит.

    ⚠️ ЧИСЛО ДНЕЙ ИЗМЕНИЛОСЬ ВМЕСТЕ С РЕШЕНИЕМ D-29, ПРЕДМЕТ ТЕСТА — НЕТ.
    Отказ по-прежнему означает «действующий тариф сохранён, дни выданы»; менялась
    только МЕРА дней, и верхняя граница добавлена, чтобы полный месяц старшего
    тарифа за цену младшего не вернулся сюда молча.
    """
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(db_session, "basic", "yoo_live_basic")

    assert await _confirm(db_session, "yoo_live_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", (
        "живой оплаченный старший тариф снят младшим платежом"
    )
    assert _aware(rows[0].expires_at) > current, "оплаченные дни не выданы"
    assert _aware(rows[0].expires_at) < current + timedelta(days=27), (
        "отвергнутый платёж купил полный месяц действующего тарифа (D-29)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# ЛОВУШКА ПОРЯДКА: ПОМОЩНИК, ЕГО НЕГАТИВНЫЕ КОНТРОЛИ И ВЫВЕДЕНИЕ МНОЖЕСТВА ИМЁН
#
# Помощник вынесен из тела теста НЕ РАДИ ОФОРМЛЕНИЯ, а затем, чтобы его можно
# было применить к СИНТЕТИЧЕСКОМУ исходнику. Инвариант, проверяемый только на
# настоящем модуле, проверяем лишь собой: доказать его красноту можно тогда
# одноразовой мутацией `app/`, удаляемой до коммита, — то есть доказательства не
# остаётся вовсе, и следующий раунд перепроверить его не может. Планы 05-15 и
# 05-17 раскрыли эту фигуру как отсутствие RED-коммита; здесь оба негативных
# контроля живут в суите постоянно.
# ═══════════════════════════════════════════════════════════════════════════

_PERIOD_MODULE = "app.application.billing.subscription_period"

# Признак живости снят ПОСЛЕ сдвига, оба оператора на верхнем уровне. Этот
# случай видел и прежний перебор `function.body`.
_SYNTHETIC_MOVE_ABOVE_THE_SAMPLE = '''
def _apply_extension(subscription, db_payment, now):
    """Синтетический исходник: сдвиг срока стоит ВЫШЕ снятия признака."""
    subscription.expires_at = next_expiry(subscription.expires_at, now)
    period_is_live = subscription_is_live(subscription.expires_at, now)
    return period_is_live
'''

# Сдвиг спрятан ВНУТРИ ветви, признак снимается после неё. Прежний перебор
# операторов верхнего уровня не видел этого случая ВОВСЕ — находка WR-03
# раунда 5: из четырёх операторов, двигающих срок, он держал один.
_SYNTHETIC_MOVE_INSIDE_A_BRANCH = '''
def _apply_extension(subscription, db_payment, now):
    """Синтетический исходник: сдвиг спрятан ВНУТРИ ветви, снятие — после неё."""
    if not db_payment.plan:
        subscription.expires_at = prorated_expiry(
            subscription.expires_at, now, paid=1, price=2
        )
    period_is_live = subscription_is_live(subscription.expires_at, now)
    return period_is_live
'''


def _period_module_names() -> frozenset[str]:
    """Имена, ввезённые денежным путём из модуля отсчёта срока.

    ВЫВОДЯТСЯ ИЗ ИМПОРТА, А НЕ ПЕРЕЧИСЛЯЮТСЯ ЛИТЕРАЛОМ, И ЭТО ВЕСЬ СМЫСЛ. Литерал
    протух бы МОЛЧА в тот момент, когда очередной план добавил бы четвёртый
    оператор сдвига: тест остался бы зелёным, а инвариант перестал бы держать
    новое имя. Ровно это и случилось между планом 05-15 и раундом 5.
    """
    import app.services.payment_service as module

    tree = ast.parse(inspect.getsource(module))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == _PERIOD_MODULE:
            return frozenset(alias.asname or alias.name for alias in node.names)
    raise AssertionError(
        f"денежный путь больше не ввозит `{_PERIOD_MODULE}` — либо арифметика "
        "срока переехала, либо она снова размазана по вызывающему"
    )


def _liveness_sample(source: str, liveness: str) -> ast.Assign | None:
    """Присваивание, ЗНАЧЕНИЕ которого — вызов признака живости, либо `None`.

    СОВПАДЕНИЕ ИЩЕТСЯ ПО ТИПАМ УЗЛОВ, А НЕ ПОДСТРОКОЙ, и это несущее свойство:
    докстринги `_apply_extension` и `subscription_is_live` обязаны НАЗЫВАТЬ оба
    имени, поэтому поиск подстроки прочёл бы содержимое строкового литерала и
    краснел бы на ВЕРНОМ коде. Литерал узлом `ast.Call` не становится никогда.
    """
    function = ast.parse(source).body[0]
    hits = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and getattr(node.value.func, "id", None) == liveness
    ]
    return min(hits, key=lambda node: node.lineno) if hits else None


def _expiry_assignment_lines(source: str, *, attr: str = "expires_at") -> list[int]:
    """Строки КАЖДОГО присваивания, ЦЕЛЬ которого — поле срока подписки.

    Второй инвариант, независимый от имён: он ловит то, чего не ловит первый —
    сдвиг, сделанный не вызовом функции модуля отсчёта, а любым другим
    выражением.
    """
    function = ast.parse(source).body[0]
    return sorted(
        node.lineno
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute) and target.attr == attr
    )


def _movers_used(source: str, *, movers: frozenset[str]) -> frozenset[str]:
    """Какие из выведенных имён в теле функции ДЕЙСТВИТЕЛЬНО вызываются.

    Нужно затем, чтобы инвариант не стал вакуумным: помощник, проверяющий имена,
    которых в теле нет вовсе, зеленеет при любом порядке.
    """
    function = ast.parse(source).body[0]
    return frozenset(
        name
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        for name in [getattr(node.func, "id", None)]
        if name in movers
    )


def _order_violations(
    source: str,
    *,
    movers: frozenset[str],
    liveness: str = "subscription_is_live",
    moved_attr: str = "expires_at",
) -> list[str]:
    """Перечень нарушений порядка «признак снимается раньше КАЖДОГО сдвига».

    Пустой перечень означает, что нарушений нет.

    ОБХОД — `ast.walk` ПО ВСЕМУ ТЕЛУ, А НЕ ПЕРЕБОР ОПЕРАТОРОВ ВЕРХНЕГО УРОВНЯ.
    Перебор верхнего уровня держал ОДИН оператор из четырёх: сдвиги внутри
    ветвей ему не видны вовсе (WR-03 раунда 5), а именно в ветвях и стоят и доля
    месяца D-29, и откат к полному месяцу, и конверсия остатка формы
    `convert-remainder`.

    ПРИЗНАК ЖИВОСТИ ИСКЛЮЧАЕТСЯ ИЗ МНОЖЕСТВА ДВИГАЮЩИХ ЯВНО: он приезжает сюда
    вместе с остальными именами модуля отсчёта, потому что множество ВЫВОДИТСЯ
    из импорта, а требовать от него стоять раньше самого себя бессмысленно.
    Прочие имена модуля (`countdown_base` в их числе) остаются в множестве
    намеренно — они читают ту же величину, и снятый после них признак так же
    описывал бы уже сдвинутый срок.
    """
    function = ast.parse(source).body[0]
    sample = _liveness_sample(source, liveness)
    if sample is None:
        return [
            f"в теле нет присваивания из вызова `{liveness}`: признак живости не "
            "снимается вовсе, и порядок держать не над чем"
        ]

    violations: list[str] = []
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None)
            if name in movers - {liveness} and node.lineno < sample.lineno:
                violations.append(
                    f"строка {node.lineno}: `{name}` двигает срок ВЫШЕ снятия "
                    f"признака (строка {sample.lineno})"
                )
        elif isinstance(node, ast.Assign) and node.lineno < sample.lineno:
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == moved_attr:
                    violations.append(
                        f"строка {node.lineno}: `.{moved_attr}` перезаписывается "
                        f"ВЫШЕ снятия признака (строка {sample.lineno})"
                    )
    return sorted(set(violations))


def test_the_order_helper_reports_a_move_placed_above_the_sample():
    """НЕГАТИВНЫЙ КОНТРОЛЬ №1: перестановка на верхнем уровне обязана краснеть.

    Синтетический исходник, а не мутация настоящего модуля: доказательство
    красноты обязано пережить коммит, иначе следующий раунд не может его
    перепроверить (T-05-115).
    """
    violations = _order_violations(
        _SYNTHETIC_MOVE_ABOVE_THE_SAMPLE, movers=_period_module_names()
    )

    assert violations, (
        "помощник не нашёл нарушения на исходнике, где срок двигается ВЫШЕ "
        "снятия признака живости: инвариант ничего не держит"
    )


def test_the_order_helper_reports_a_move_hidden_inside_a_branch():
    """НЕГАТИВНЫЙ КОНТРОЛЬ №2: сдвиг ВНУТРИ ветви обязан краснеть тоже.

    Именно этот случай прежний перебор `function.body` не видел вовсе, и именно
    он описан находкой WR-03 раунда 5: тест держал последний оператор верхнего
    уровня, а сдвиги в ветвях (`prorated_expiry` в их числе) оставались вне
    инварианта.
    """
    violations = _order_violations(
        _SYNTHETIC_MOVE_INSIDE_A_BRANCH, movers=_period_module_names()
    )

    assert violations, (
        "помощник не нашёл нарушения на исходнике, где сдвиг спрятан ВНУТРИ "
        "ветви: обход идёт по операторам верхнего уровня, а не по всему телу"
    )


def test_the_liveness_is_sampled_before_the_date_moves():
    """ЛОВУШКА ПОРЯДКА, проверяемая машиной, а не прочтением.

    Признак живости, снятый ПОСЛЕ `next_expiry`, всегда отвечает «живо»: сдвиг
    срока перезаписывает ту самую величину, по которой принимается следующее
    решение в той же функции. Блокер восстанавливается молча, правкой, которая
    выглядит безобидной перестановкой двух строк (T-05-63).

    СОВПАДЕНИЕ ИЩЕТСЯ ПО ТИПАМ УЗЛОВ, А НЕ ПОДСТРОКОЙ. Докстринг самой
    `_apply_extension` обязан НАЗВАТЬ оба имени (задача 3 плана 05-13), поэтому
    поиск подстроки в тексте или в дампе дерева прочёл бы содержимое строкового
    литерала: при обоих именах оба индекса стали бы нулевыми и тест падал бы на
    ВЕРНОМ коде, при одном имени — зеленел бы при ЛЮБОМ порядке. Поэтому
    докстринг из перечня операторов вычёркивается, а ищется присваивание, ЗНАЧЕНИЕ
    которого — вызов функции с этим именем. Упоминание имени в комментарии
    оператором не является и тест не ломает; перестановка двух операторов — ломает.

    ⚠️ ТЕСТ ДЕРЖИТ И ВЕЛИЧИНУ, А НЕ ТОЛЬКО ПОРЯДОК (IN-02 раунда 4). Держа один
    порядок, он зеленел бы при подмене АРГУМЕНТА снятия на любое другое поле
    платежа или подписки — правило начинало бы решать по чужой величине, стоя
    при этом на верном месте. Проверяется, что признак снимается ИМЕННО от
    `subscription.expires_at`, то есть от той величины, которую перезаписывает
    `next_expiry`: только для неё порядок вообще что-то значит.

    ЧТО ТЕСТ ДЕРЖИТ СЕГОДНЯ — КАЖДЫЙ СДВИГ, А НЕ ОДИН ИЗ ЧЕТЫРЁХ. Прежняя
    редакция перебирала операторы ВЕРХНЕГО УРОВНЯ и утверждала при этом покрытие
    двух ветвей; фактически она держала последний оператор верхнего уровня, а
    сдвиги внутри ветвей — долю месяца D-29 в их числе — не видела вовсе
    (WR-03 раунда 5). Теперь обход идёт `ast.walk` по всему телу, и держатся ДВА
    независимых инварианта: по ИМЕНИ вызываемого (множество ВЫВОДИТСЯ из импорта
    модуля отсчёта, поэтому имя, добавленное будущим планом, попадает под
    проверку без правки теста) и по ЦЕЛИ присваивания (любое выражение,
    перезаписывающее поле срока, чем бы оно ни считалось).

    ⚠️ ЧЕГО ТЕСТ НЕ ДЕРЖИТ, НАЗВАНО ЗДЕСЬ, ЧТОБЫ ИМЯ СНОВА НЕ ОБЕЩАЛО БОЛЬШЕ
    ТЕЛА. Он не проверяет, что сдвиг вообще ВЕРЕН — только что он стоит ниже
    снятия признака; арифметику держат тесты `tests/test_application/`. Он ничего
    не знает о ветке, где признак не участвует вовсе. И он молчит о ПОРЯДКЕ
    сдвигов между собой: их взаимная перестановка инвариантом не запрещена.
    Краснота самого инварианта доказана не рассуждением, а двумя негативными
    контролями над синтетическими исходниками — `test_the_order_helper_*` выше.
    """
    import app.services.payment_service as module

    source = inspect.getsource(module._apply_extension)
    movers = _period_module_names()

    used = _movers_used(source, movers=movers)
    assert len(used) >= 2, (
        "инвариант стал вакуумным: в теле не осталось вызовов, ввезённых из "
        "`app.application.billing.subscription_period`, кроме признака живости "
        f"— проверять нечего ({sorted(used)})"
    )

    violations = _order_violations(source, movers=movers)
    assert violations == [], (
        "признак живости снимается ПОСЛЕ сдвига срока — правило всегда получит "
        f"«живо», и блокер восстановлен молча: {violations}"
    )

    moves = _expiry_assignment_lines(source, attr="expires_at")
    assert len(moves) >= 3, (
        "сдвигов срока стало меньше трёх: либо ветка исчезла, либо срок "
        f"двигается уже не присваиванием в поле подписки — {moves}"
    )

    sampled = _liveness_sample(source, "subscription_is_live").value.args[0]
    assert isinstance(sampled, ast.Attribute) and sampled.attr == "expires_at", (
        "признак снимается НЕ от той величины, которую перезаписывает "
        "`next_expiry`: порядок соблюдён, а правило решает по чужому полю "
        f"({ast.dump(sampled)})"
    )


def test_the_switch_semantics_are_named_in_the_place_that_moves_the_date():
    """Правило записано ТАМ, ГДЕ двигается срок, а не только в документах фазы.

    Докстринг `_extend_subscription` объясняет, почему запрос активной подписки
    повторяет читателя дословно, и до этого плана МОЛЧАЛ о том, что делается с
    планом. Читатель этой функции — тот самый человек, который завтра будет
    решать, можно ли поменять здесь порядок двух строк.

    НАЗВАТЬ СЕМАНТИКУ МАЛО — ОНА ОБЯЗАНА СОВПАДАТЬ С КОДОМ. Верификатор нашёл
    ровно это расхождение: докстринг утверждал, что понижение «не предлагается
    карточкой и не принимается гардом», умалчивая, что подтверждённый платёж его
    ПРИМЕНЯЕТ. Поэтому к двум словам добавлено утверждение об ИСХОДЕ: расхождение
    уплаченного и действующего тарифа названо своим ключом журнала, а ключ
    существует только вместе с поведением, которое его пишет.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "services"
        / "payment_service.py"
    ).read_text(encoding="utf-8")
    body = source[source.index("async def _extend_subscription(") :]
    docstring = body[: body.index('"""', body.index('"""') + 3)]

    assert "upgrade-only" in docstring, "выбранная семантика не названа"
    assert "05-01" in docstring, "решение не связано с прохибицией, которую щадит"
    assert "subscription_plan_preserved" in docstring, (
        "докстринг молчит о том, чем кончается подтверждённый платёж младшего "
        "тарифа — то есть снова описывает не исполняемое поведение"
    )
    # УРОК ПРЕДЫДУЩЕГО РАУНДА, ПРИМЕНЁННЫЙ ВТОРОЙ РАЗ. Проверка на два слова
    # зеленела при неверном поведении, поэтому КАЖДОЕ новое утверждение
    # докстринга получает своё утверждение теста. Подстрока «истёк» существует
    # только вместе с абзацем об исходе на ИСТЁКШЕМ сроке — том самом, о котором
    # докстринг молчал, пока код брал деньги за невыдаваемый тариф (гэп 1
    # раунда 3).
    assert "истёк" in docstring, (
        "докстринг молчит об исходе на ИСТЁКШЕМ сроке — стадии, где деньги уже "
        "ушли, а тариф мог остаться невыданным"
    )
    assert "subscription_is_live" in docstring, (
        "докстринг не называет, ЧЕМ считается признак живости и где он объявлен"
    )
    # ТРЕТЬЕ ПРИМЕНЕНИЕ ТОГО ЖЕ УРОКА. Подстрока `switch_authorized` существует
    # только вместе с абзацем о том, ЧТО решает, применять ли план: записанное
    # разрешение, а не сегодняшнее состояние подписки. Пока абзаца не было,
    # докстринг описывал стадию, которая принимает решение заново, — то есть
    # снова не исполняемое поведение (гэп 1 раунда 4).
    assert "switch_authorized" in docstring, (
        "докстринг молчит о том, что решение о плане принимается по ЗАПИСАННОМУ "
        "разрешению, а не по состоянию подписки в момент уведомления"
    )


# =============================================================================
# РАЗРЕШЕНИЕ СДЕЛКИ ЗАПИСАНО НА ПЛАТЕЖЕ — состояние подписки МЕНЯЕТСЯ между
# продажей и подтверждением
# =============================================================================
#
# ЧЕМ ЭТОТ РАЗДЕЛ ОТЛИЧАЕТСЯ ОТ ВСЕХ СОСЕДНИХ, И ЭТО ЕДИНСТВЕННОЕ ОТЛИЧИЕ.
# Соседние разделы держат состояние подписки НЕИЗМЕННЫМ между стадией ПРОДАЖИ
# и стадией ПОДТВЕРЖДЕНИЯ: подписка либо живая на обеих, либо истёкшая на
# обеих, либо отсутствует на обеих. Ровно поэтому суита из 1681 теста
# оставалась зелёной при работающем блокере — класса тестов, меняющих это
# состояние МЕЖДУ двумя стадиями, не было ни одного.
#
# Здесь состояние МЕНЯЕТСЯ. Между двумя моментами лежит вся сессия оплаты у
# ЮKassa, и за это время подписка успевает ожить (соседний платёж подтверждён),
# истечь (прошло время) или появиться впервые.
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА D-28: ответ гарда о разрешённом переходе записывается НА
# ПЛАТЁЖ (`payments.switch_authorized`, ревизия `0019`), и стадия применения
# читает записанный ФАКТ, а не пересчитывает предикат по изменившейся строке
# подписки. `True` — правило спросили и переход разрешило; `False` — спросили и
# отвергло; `NULL` — НЕ спрашивали (пакетный платёж либо строка старше ревизии).


@pytest.mark.asyncio
async def test_a_deal_sold_on_an_expired_period_is_delivered_after_the_period_revives(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Зеркальный путь WR-01 раунда 4: продано на истёкшем — выдано на ожившем.

    ВРЕД ЗДЕСЬ ДОСТАЁТСЯ ПОЛЬЗОВАТЕЛЮ, а не кассе, и этим путь отличается от
    денежного (CR-01). Подписка `pro` истекла вчера; пользователь покупает
    `basic` — гард ПРОПУСКАЕТ покупку, потому что защищать нечего, и обещание
    карточки «переход на младший тариф — после окончания оплаченного срока»
    исполнено ровно в этот момент. Дальше подтверждается соседний платёж `pro`,
    и период ОЖИВАЕТ. К моменту, когда приходит уведомление о проданном
    `basic`, состояние подписки уже другое — и правило, пересчитанное по нему,
    отвечает «отказ»: сделка продана под обещание и не выдана.

    Записанный ответ гарда (D-28) убирает эту переменную: платёж несёт то, что
    было ПРОДАНО, и стадия применения читает его, а не текущее состояние БД.
    """
    await _seed_expired_subscription(db_session, "pro")

    # ПРОДАЖА: период истёк, гард пропускает, ответ обязан быть записан.
    await _subscribe(authed_client, plan="basic", payment_id="yoo_basic")

    # ОКНО МЕЖДУ СТАДИЯМИ: соседний платёж оживляет период и ставит план `pro`.
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True
    )
    assert await _confirm(db_session, "yoo_pro") is True

    # ПРИМЕНЕНИЕ проданного: состояние подписки уже ДРУГОЕ.
    assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "два платежа завели две подписки"
    assert rows[0].plan == "basic", (
        "сделка продана под обещание «понижение будет применено» и НЕ выдана: "
        "стадия применения решила заново по состоянию, которого в момент "
        "продажи не было"
    )


@pytest.mark.asyncio
async def test_the_intent_stage_records_its_answer_on_the_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ответ гарда существует на строке платежа, а не только в стеке вызова.

    Пока ответ нигде не записан, любая пара «продали → выдали» решает заново по
    тому, что успело измениться. Утверждение самое простое из раздела и самое
    несущее: без него всё остальное чинило бы следствие.
    """
    await _subscribe(authed_client, plan="basic", payment_id="yoo_recorded")

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_recorded")
        )
    ).scalar_one()

    assert payment.switch_authorized is True, (
        "стадия намерения не записала СВОЙ ответ на платёж"
    )


@pytest.mark.asyncio
async def test_the_deal_cannot_be_sold_without_recording_its_authorization(
    db_session: AsyncSession,
):
    """Разрешение НЕЛЬЗЯ не записать: вызов без него падает громко.

    МАШИННАЯ ГАРАНТИЯ ВМЕСТО ДИСЦИПЛИНЫ ВЫЗЫВАЮЩЕГО. Параметр со значением по
    умолчанию однажды не подадут — ровно так разошлись две стадии дважды
    подряд, и ровно поэтому `kind` тоже объявлен обязательным keyword-only.
    Четвёртый вызывающий, заведённый завтра, обязан упасть НА ВЫЗОВЕ, а не
    тихо записать платёж, о котором неизвестно, что было продано.
    """
    with pytest.raises(TypeError):
        create_payment(
            db_session,
            user_id=1,
            kind="subscription",
            plan="basic",
            price="1490.00",
            package_name=None,
            messages_count=None,
        )


@pytest.mark.asyncio
async def test_a_package_payment_records_that_the_rule_was_not_asked(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пакетный платёж записывает `NULL` ЗНАЧЕНИЕМ, а не отсутствием поля.

    Правило смены тарифа пакета не касается вовсе, и это обязано быть выражено
    записанным `NULL`, а не «забыли записать». Разница видна на стадии
    применения: `NULL` означает «не спрашивали», а не «спрашивали и отказали».
    """
    await _purchase(authed_client)

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_1")
        )
    ).scalar_one()

    assert payment.kind == "package"
    assert payment.switch_authorized is None, (
        "пакетному платежу записан ответ правила, которое его не касается"
    )


@pytest.mark.asyncio
async def test_a_legacy_payment_without_a_recorded_answer_still_decides_by_the_rule(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПАРНЫЙ тест: строка старше ревизии `0019` по-прежнему решается правилом.

    Без него «читать записанный факт» можно было бы исполнить так, что строки
    без записанного ответа перестали бы решаться вовсе — и действующий старший
    тариф снимался бы любым подтверждённым младшим платежом, заведённым до
    ревизии. У такой строки записанному ответу взяться неоткуда, и выдумать его
    хуже, чем пересчитать.
    """
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_old", switch_authorized=None
    )

    assert await _confirm(db_session, "yoo_old") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", (
        "строка без записанного ответа перестала решаться правилом"
    )


# =============================================================================
# ГРАНИЦЫ ЗАПИСАННОГО ОТВЕТА — два объявления денежного пути, ОПРОВЕРГНУТЫХ
# ПРОГОНОМ верификации раунда 6
# =============================================================================
#
# ЧЕМ ЭТОТ РАЗДЕЛ ОТЛИЧАЕТСЯ ОТ ПРЕДЫДУЩЕГО, И ЭТО ЕДИНСТВЕННОЕ ОТЛИЧИЕ.
# Предыдущий описывает D-28 КАК ОН ЕСТЬ: ответ гарда записан на платёж, и стадия
# применения читает записанный ФАКТ, а не пересчитывает предикат по изменившейся
# строке подписки. Этот описывает его ГРАНИЦЫ — два места, где объявление
# расходилось с прогоном.
#
# (1) `WR-02`. Докстринг `_extend_subscription` утверждает БЕЗУСЛОВНО: когда
# оплаченный срок истёк, отказ снимается на ОБЕИХ стадиях, план платежа
# применяется, и следа `subscription_plan_preserved` на этом пути НЕТ. Код читал
# записанный ответ, ни разу не спросив `period_is_live`, — то есть записанный
# `False` переживал собственный период.
#
# (2) `WR-03`. Два объявления называли ИНВАРИАНТОМ «план только повышается».
# Прогон опроверг: подписка `pro` с ЖИВЫМ сроком плюс подтверждённый платёж
# `basic` с записанным разрешением `True` даёт `plan == "basic"` — и следа нет
# вовсе, потому что ветка отказа не берётся и `subscription_plan_preserved` не
# пишется. Достижимость: намерение младшего тарифа заводится, когда подписки
# нет; через `PENDING_INTENT_TTL_HOURS` оно перестаёт считаться потолком;
# соседнее намерение старшего тарифа подтверждается первым; затем подтверждается
# первое.
#
# ОТВЕТ ВЛАДЕЛЬЦА ПО КОНФЛИКТУ `upgrade-only` × D-28 (чекпойнт задачи 1 плана
# 05-24) — `record-wins`. Решение D-28 остаётся В СИЛЕ: записанное разрешение
# исполняется КАК ПРОДАНО, и поведение денежного пути не меняется ни на день.
# Объявление «план только повышается» снято из ОБОИХ мест и заменено описанием
# настоящего исхода: `upgrade-only` есть правило стадии НАМЕРЕНИЯ, а не инвариант
# обеих стадий. Ценой ответа названо то, что понижение через окно срока давности
# остаётся ДОСТИЖИМЫМ, — поэтому оно перестаёт быть БЕССЛЕДНЫМ и получает
# собственный ключ журнала.
#
# ПРАВИЛО УТВЕРЖДЕНИЙ РАЗДЕЛА (раздел «ГЭП 1 РАУНДА 5»). Оба теста утверждают
# НАБЛЮДАЕМОЕ: строку `subscriptions`, перечитанную из БД, и содержимое журнала.
# Ни один не называет символа, которого ещё нет.


@pytest.mark.asyncio
async def test_an_expired_period_lifts_the_recorded_refusal_and_leaves_no_trace(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Истёкший срок снимает ЗАПИСАННЫЙ отказ ровно так же, как отказ правила.

    ОТКУДА ВЗЯТО ЗНАЧЕНИЕ `False`, И ПОЧЕМУ ЕГО НЕДОСТИЖИМОСТЬ ЧЕРЕЗ ФОРМУ НЕ
    ДЕЛАЕТ ТЕСТ ГИПОТЕТИЧЕСКИМ. Колонка `payments.switch_authorized`
    (`app/models/payment.py`) и заводящая её ревизия `0019` ОБЕ явно требуют,
    чтобы значение `False` было выразимо, и обе называют его смысл — «правило
    спросили, и оно отвергло». То есть проект сам объявляет это значение живым
    контрактом; недостижимость через форму сегодня есть свойство ГАРДА
    (`app/pages/billing.py` не продаёт отвергнутого перехода), а не колонки, и
    находится она в одной правке гарда от достижимости.

    ЧТО УТВЕРЖДАЕТСЯ, И ПОЧЕМУ ДВУХ УТВЕРЖДЕНИЙ, А НЕ ОДНОГО. Докстринг
    `_extend_subscription` обещает на этом пути ДВЕ вещи сразу: план платежа
    применяется, каким бы он ни был, И следа `subscription_plan_preserved` не
    остаётся — сохранять нечего, тариф выдан. Тест, проверяющий только план,
    оставил бы вторую половину обещания непроверенной, а именно она и есть то,
    по чему разбирающий обращение отличает «тариф выдан» от «тариф сохранён».

    РАЗДЕЛЕНИЕ СРОКОВ СДЕЛАНО ПОСЕВОМ, А НЕ ПОРОГОМ. Срок истёк 200 дней назад
    (а не вчера) специально: календарный месяц от ПРОШЕДШЕЙ даты и календарный
    месяц от СЕГОДНЯ различаются тогда на две сотни дней, и утверждение о
    правиле D-04 становится доказательным, а не совпадающим по обеим ветвям.
    """
    expired = await _seed_expired_subscription(db_session, "pro", days_ago=200)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=False, amount="1490.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "подтверждение завело вторую строку подписки"
    assert rows[0].plan == "basic", (
        "записанный отказ пережил собственный период: срок истёк, защищать "
        "нечего, а уплаченный тариф так и не выдан — докстринг "
        "`_extend_subscription` утверждает обратное БЕЗУСЛОВНО"
    )

    granted = _aware(rows[0].expires_at)
    assert granted > _aware(expired) + timedelta(days=45), (
        "срок посчитан от ПРОШЕДШЕГО значения, а не от сегодня (D-04): от "
        "истёкшей даты месяц даёт около тридцати дней, от сегодня — больше "
        "двухсот"
    )
    now = datetime.now(timezone.utc)
    assert granted > now + timedelta(days=27), "оплаченные дни не выданы"
    assert granted < now + timedelta(days=45), (
        "выдан не календарный месяц от сегодня"
    )

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved == [], (
        "журнал сообщает о СОХРАНЕНИИ тарифа там, где тариф выдан: следа на "
        "этом пути докстринг не обещает вовсе (T-05-65, WR-02)"
    )


@pytest.mark.asyncio
async def test_a_demotion_by_the_recorded_answer_leaves_its_own_downgrade_trace(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Понижение действующего тарифа перестаёт происходить БЕЗ СЛЕДА.

    ПУТЬ ДОСТИЖИМОСТИ — СЛОВАМИ ОТЧЁТА ВЕРИФИКАЦИИ, А НЕ ГИПОТЕЗОЙ. Намерение
    младшего тарифа заводится тогда, когда подписки нет вовсе, — гард пропускает
    его, защищать нечего, и записанное разрешение уезжает на платёж значением
    `True`. Через `PENDING_INTENT_TTL_HOURS` это намерение перестаёт считаться
    потолком одновременных намерений; заводится и подтверждается соседнее
    намерение СТАРШЕГО тарифа, и подписка становится `pro` с живым сроком.
    Затем приходит уведомление по ПЕРВОМУ платежу.

    ПОСЕВ ВОСПРОИЗВОДИТ КОНЕЧНОЕ СОСТОЯНИЕ ЭТОГО ПУТИ НАПРЯМУЮ, а не проигрывает
    его по шагам, и это осознанно: сам путь к состоянию закреплён отдельным
    зелёным тестом проекта (`test_a_stale_intent_does_not_block_a_new_one`),
    и второй его экземпляр здесь проверял бы окно срока давности, а не исход
    подтверждения. Окно этим планом не закрывается и числится записанным долгом
    фазы.

    ЧТО ЗДЕСЬ КРАСНОЕ, А ЧТО ЗЕЛЁНОЕ НА ВХОДЕ, И ПУТАТЬ ИХ НЕЛЬЗЯ. Утверждение о
    плане ЗЕЛЁНОЕ уже сегодня — ответ владельца `record-wins` оставляет D-28 в
    силе, и сделка исполняется как продана; оно защищает исход от регрессии
    будущего. КРАСНОЕ здесь ровно одно — журнал: сегодня действующий тариф
    меняется ВНИЗ, не оставляя ни одной записи, потому что ветка отказа не
    берётся и `subscription_plan_preserved` не пишется. Именно это и делает
    исход неразбираемым по журналу (прохибиция BILL-05).
    """
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=True, amount="1490.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "подтверждение завело вторую строку подписки"
    assert rows[0].plan == "basic", (
        "сделка, проданная под записанное разрешение, НЕ выдана: решение D-28 "
        "отменено на самом достижимом своём пути"
    )

    downgrades = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_downgraded"
    ]
    assert len(downgrades) == 1, (
        "действующий тариф сменён ВНИЗ и не оставил в журнале ни одной записи: "
        "разбирающий обращение не может назвать человеку исход, а восстановить "
        "его по догадке — не то же самое (прохибиция BILL-05)"
    )

    fields = downgrades[0].kwargs
    assert fields.get("plan") == "pro", (
        "журнал не назвал ПРЕЖНЕГО тарифа — того самого, который человек "
        "потерял"
    )
    assert fields.get("paid_plan") == "basic", (
        "журнал не назвал плана платежа, по которому произошла смена"
    )
    assert fields.get("decided_by") == "recorded_answer", (
        "журнал не назвал ИСТОЧНИКА решения: понижение по записанному ответу "
        "неотличимо от понижения, которое пропустило правило"
    )
    assert fields.get("period_was_live") is True, (
        "журнал не назвал главного: тариф сменён вниз при ЖИВОМ оплаченном "
        "сроке — том состоянии, которое карточка младшего плана обещает не "
        "трогать до окончания срока"
    )


def test_neither_declaration_claims_the_plan_only_grows_at_the_apply_stage():
    """Ни одно объявление денежного пути не утверждает СНЯТОГО инварианта.

    ⚠️ ПОЧЕМУ ЭТО ТЕСТ, А НЕ `grep` В ОТЧЁТЕ. Критерий «объявлений инварианта
    ноль» подстрокой НЕ измеряется: после правки оба файла УПОМИНАЮТ снятое
    предложение — каждый абзац называет, что стояло прежде и чем прогон это
    опроверг, ровно затем, чтобы следующий читатель не вернул объявление как
    «потерянное при рефакторинге». Подсчёт вхождений вернул бы три и назвал бы
    работу несделанной. Считать надо УТВЕРЖДЕНИЯ, а не упоминания, и различает
    их форма предложения — поэтому проверяются ДОСЛОВНЫЕ прежние редакции.

    ЧЕГО ЭТОТ ТЕСТ НЕ ДЕЛАЕТ. Он не запрещает понижения и не утверждает ничего о
    поведении — поведение держат два теста выше. Он держит РАВЕНСТВО объявления
    и прогона: `T-05-154` описывает ровно тот способ провалиться, при котором
    правка снимает объявление в одном файле и оставляет во втором, и следующий
    раунд находит третью формулировку одной истины.
    """
    root = Path(__file__).resolve().parents[2]
    service = (root / "app" / "services" / "payment_service.py").read_text(
        encoding="utf-8"
    )
    rule = (
        root / "app" / "application" / "billing" / "plan_switch.py"
    ).read_text(encoding="utf-8")

    # ПРЕЖНИЕ РЕДАКЦИИ — ДОСЛОВНО. Каждая утверждала инвариант, и каждую
    # опроверг прогон верификации раунда 6 (`WR-03`).
    assert "этом только повышается." not in service, (
        "докстринг `_extend_subscription` снова объявляет ИНВАРИАНТОМ то, что "
        "код не исполняет: платёж с записанным разрешением понижает тариф"
    )
    assert "и НЕ ПРИМЕНЯЕТСЯ ЗДЕСЬ. Прохибиция" not in service, (
        "перечень запретов снова распространён на стадию ПРИМЕНЕНИЯ, где "
        "понижение по записанному разрешению происходит"
    )
    assert "применяет план — ТОЛЬКО ВВЕРХ." not in service, (
        "первая строка докстринга `_apply_extension` снова обещает движение "
        "плана только вверх"
    )
    assert "срок двигается всегда, план только растёт." not in rule, (
        "докстринг `switch_is_refused` снова объявляет инвариант обеих стадий "
        "там, где правило спрашивают только у строк без записанного ответа"
    )

    # ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА: снять объявление мало — на его место обязано
    # встать описание НАСТОЯЩЕГО исхода, иначе следующий читатель прочтёт
    # молчание как прежнее правило. Ответ владельца `record-wins` назвал его
    # словами: `upgrade-only` есть правило стадии НАМЕРЕНИЯ.
    for source, name in ((service, "payment_service.py"), (rule, "plan_switch.py")):
        assert "правило стадии НАМЕРЕНИЯ" in source, (
            f"{name}: объявление снято, а на его место ничего не встало — "
            "молчание о том, что делается с планом, и было первой редакцией "
            "этого же дефекта"
        )


# =============================================================================
# ДНИ ПО УПЛАЧЕННОМУ ТАРИФУ (D-29) — платёж, чей план не применён
# =============================================================================
#
# ДО ЭТОГО ПЛАНА `subscription.expires_at = next_expiry(...)` стоял БЕЗУСЛОВНО и
# ВЫШЕ решения о плане, поэтому отвергнутый платёж младшего тарифа покупал полный
# календарный месяц действующего СТАРШЕГО: 1490 ₽ давали месяц Pro стоимостью
# 4900 ₽, и повторов не ограничивало ничто.
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА D-29: платёж продолжает давать дни — принцип «деньги ВСЕГДА
# превращаются в дни» сохранён, и «не выдать ничего» остаётся худшим из исходов,
# — но дни считаются ПО УПЛАЧЕННОМУ: доля календарного месяца по отношению
# уплаченной суммы к цене действующего плана, не меньше одного дня.


@pytest.mark.asyncio
async def test_a_pro_deal_sold_before_any_subscription_is_not_erased_by_a_later_basic(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """СЛУЧАЙ (1) третьего пункта `missing:` — подписки НЕТ на момент ОБЕИХ продаж.

    ⚠️ ЧЕМ ЭТОТ СЛУЧАЙ ОТЛИЧАЕТСЯ ОТ СОСЕДНЕГО, И ОТЛИЧИЕ ПРИНЦИПИАЛЬНО.
    У соседа подписка к моменту второго подтверждения уже существует как
    ПРОДЛЕВАЕМАЯ. Здесь подписки нет ВОВСЕ, поэтому первый подтверждённый платёж
    идёт веткой ПЕРВОЙ ВСТАВКИ, а не веткой продления — ровно то состояние,
    которое воспроизводил верификатор. Считать эти два теста дубликатами и
    удалить один нельзя.

    У ТРЁХ УТВЕРЖДЕНИЙ ЗДЕСЬ РАЗНЫЕ РОЛИ, и путать их значило бы записать в
    отчёт величину, которой ни один прогон не даёт:

    * «строка одна» — ЗАЩИТНОЕ, на входе ЗЕЛЁНОЕ;
    * `plan == "pro"` — ЗАЩИТНОЕ, на входе ЗЕЛЁНОЕ. У строки без записанного
      ответа решение принимает правило: `switch_is_refused("pro", "basic",
      period_is_live=True)` отвечает `True`, ветка `subscription_plan_preserved`
      возвращает управление, и план НЕ перезаписывается уже сегодня.
      Утверждение ловит регрессию БУДУЩЕГО — снятие старшего плана записанным
      фактом или долей месяца, — а не сегодняшний дефект;
    * срок строго между «сейчас + 33 дня» и «сейчас + 45 дней» — ЕДИНСТВЕННОЕ
      КРАСНОЕ на входе: сегодня отвергнутый платёж двигает срок на полный
      календарный месяц, и итог уходит за 59 дней.

    Путь, на котором план ДЕЙСТВИТЕЛЬНО стирается последним подтверждением, —
    это путь строк С записанным разрешением `True`, то есть заведённых ФОРМОЙ.
    Он этим планом НЕ достижим и закрывается планом `05-17` (потолок
    одновременных намерений, форма `cap-different-plan`).
    """
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=None, amount="4900.00"
    )
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    assert await _confirm(db_session, "yoo_pro") is True
    assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "два платежа завели две подписки"
    assert rows[0].plan == "pro", (
        "сделка на 4900 ₽ продана и не выдана: старший тариф снят последним "
        "подтверждённым младшим платежом"
    )
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=33), (
        "деньги второго платежа не превратились в дни"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "второй платёж купил ВТОРОЙ полный месяц старшего тарифа за цену "
        "младшего (D-29 нарушен)"
    )


@pytest.mark.asyncio
async def test_an_upgrade_confirmed_last_is_still_applied_without_a_recorded_answer(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ЗЕРКАЛО предыдущего по ПОРЯДКУ подтверждений: тот же посев, обратный порядок.

    Целиком защитный. Без него предыдущий тест зеленел бы на коде, запретившем
    менять план ВООБЩЕ: повышение обязано остаться повышением, а оплаченный
    остаток — не сгореть.

    ⚠️ УТВЕРЖДЕНИЕ О СРОКЕ ПОМЕНЯЛО СТОРОНУ ВМЕСТЕ С РЕШЕНИЕМ ВЛАДЕЛЬЦА
    `convert-remainder` (чекпойнт задачи 1 плана 05-18), ровно как это уже
    случилось с порогом 45 дней у соседа `..._does_not_strip_the_higher_one_...`
    при решении D-29. Раньше здесь стояло `> now + 45 дней`: оплаченный месяц
    Basic переживал переход ДНЯМИ и складывался с оплаченным месяцем Pro в
    шестьдесят дней. Именно этот механизм на масштабе года и был гэпом 1 раунда
    5. Теперь остаток переносится ПО ДЕНЬГАМ: месяц Basic (1490 ₽) стоит девять
    дней Pro (4900 ₽), и срок выходит около тридцати девяти дней.

    Порог 45 дней сохранён и поменял сторону — именно это и делает утверждение
    доказательным. Обе стороны несущие: нижняя (`> месяц от сегодня`) держит
    обещание «оплаченный остаток не сгорает» — без неё тест зеленел бы на коде,
    отнявшем остаток целиком; верхняя держит то, ради чего решение принято.
    """
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=None, amount="4900.00"
    )
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    assert await _confirm(db_session, "yoo_basic") is True
    assert await _confirm(db_session, "yoo_pro") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "оплаченное повышение не применено"
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > add_one_month(now), (
        "повышение сожгло оплаченный остаток младшего тарифа: выдан ровно месяц "
        "от сегодня"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "оплаченный остаток перенесён ПО ДНЯМ, а не по деньгам: месяц Basic "
        "сложился с месяцем Pro в два полных месяца старшего тарифа"
    )


@pytest.mark.asyncio
async def test_a_refused_payment_buys_days_of_what_it_paid_for(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Журнал объясняет, ПОЧЕМУ дней девять, а не тридцать.

    НАЧАЛЬНОЕ СОСТОЯНИЕ НАЗВАНО ЗДЕСЬ ЯВНО, потому что соседних прогонов теперь
    три, а число выданных дней зависит от того, какой из них взят: ЖИВАЯ `pro`
    плюс отвергнутый `basic` без записанного ответа.

    Без своего ключа исход «выдано девять дней вместо тридцати» неотличим в
    журнале от «дни не выданы», и разбирающий обращение не сможет объяснить
    человеку ни числа, ни его основания.
    """
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_basic") is True

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved, "сохранение старшего тарифа не оставило следа в журнале"
    fields = preserved[0].kwargs
    assert fields.get("plan") == "pro"
    assert fields.get("paid_plan") == "basic"

    granted = fields.get("granted_days")
    assert isinstance(granted, int), "журнал не называет числа выданных дней"
    assert 1 <= granted <= 12, (
        f"выдано {granted} дней — это не доля месяца от 1490 ₽ при цене 4900 ₽"
    )
    assert str(fields.get("price_basis")) == "4900.00", (
        "журнал не называет цену, ПО КОТОРОЙ посчитаны дни — без неё число "
        "выданных дней нечем объяснить"
    )


@pytest.mark.asyncio
async def test_a_price_that_cannot_be_read_falls_back_to_the_whole_month(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Непрочитанная цена НЕ поднимает исключения и НЕ отнимает дней.

    ПРИЧИНА ТРЕБОВАНИЯ ПРИКЛАДНАЯ. Необработанное исключение в обработчике
    уведомления даёт 5xx, а 5xx на уведомлении ЮKassa запускает цикл повторов и
    оставляет платёж `pending` навсегда — класс отказа, уже стоивший фазе
    находки `WR-04` раунда 2.

    Перечень тарифов правится окружением, а действующий план записан в строке
    подписки: разойтись они могут в любую сторону, и тогда цены, по которой
    считать долю, взяться неоткуда. Откат к полному месяцу выбран в сторону
    пользователя — отнимать дни за расхождение конфига с базой не за что.
    """
    current = await _seed_live_subscription(db_session, "platinum", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "platinum", "незнакомому плану угадали ранг"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "откат к полному месяцу не сработал — дни отняты за расхождение конфига"
    )

    assert any(
        call.args and call.args[0] == "subscription_prorating_skipped"
        for call in spy.warning.call_args_list
    ), "непрочитанная цена не оставила следа в журнале"


# Перечень тарифов, в котором цена действующего плана есть ГОЛЫЙ ЛИТЕРАЛ `NaN`.
# Форма взята ДОСЛОВНО из отчёта раунда 8 и достижима штатной правкой оператора:
# `PLAN_LIMITS` — строка окружения, разбираемая `json.loads` без схемы
# (`app/config.py:120-121`), а `json.loads` принимает голые `NaN` и `Infinity`
# по умолчанию.
NON_FINITE_PLAN_LIMITS = '[{"id":"basic","price":NaN},{"id":"pro","price":"4900.00"}]'

SUCCEEDED_WEBHOOK_BODY = {"event": "payment.succeeded", "object": {"id": "yoo_pro"}}


@pytest.mark.asyncio
async def test_a_non_finite_price_does_not_five_hundred_the_notification(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings: Settings
):
    """Нефинитная цена НЕ даёт 500 на НАСТОЯЩЕМ маршруте уведомления ЮKassa.

    ПРЕДМЕТ УТВЕРЖДЕНИЯ — HTTP-КОД, А НЕ ВОЗВРАТ ФУНКЦИИ, и это не оформление.
    Исключение из `_plan_price` доходит до `app/routes/billing.py:200-202`, где
    `except Exception` превращает его в `HTTPException(500)`; именно 500
    запускает цикл повторов ЮKassa и оставляет платёж `pending` НАВСЕГДА при уже
    списанных деньгах (T-05-104). Прямой вызов `handle_webhook` через это место
    не проходит вовсе, поэтому четыре закреплённые формы соседнего теста 500 не
    стерегут — его стережёт этот случай.

    ГАРД ИСТОЧНИКА СНИМАЕТСЯ ЯВНО, аварийным выключателем — форма
    `test_the_kill_switch_lets_any_source_through`. Умолчание конфига
    (`app/config.py:88`) равно `True`, и фикстура `test_settings` его не
    переопределяет: запрос без заголовка адреса получил бы 403 и до предмета не
    дошёл бы. Выключатель выбран вместо доверенного адреса потому, что случай не
    должен уметь краснеть по причине, к предмету не относящейся: обновление
    списка сетей в SDK покрасило бы утверждение о цене поведением гарда.

    Посев обязателен ровно такой: план платежа ОТЛИЧАЕТСЯ от плана подписки, а
    оплаченный срок ЖИВОЙ. Без этого ветка конверсии, зовущая `_plan_price` для
    обоих планов, недостижима, и случай был бы зелёным всегда.
    """
    confirmed_at = datetime.now(timezone.utc)
    current = await _seed_live_subscription(db_session, "basic", days=25)
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )

    test_settings.yookassa_webhook_verify_ip = False

    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ), patch(
        "app.services.payment_service.get_settings",
        return_value=_app_settings(NON_FINITE_PLAN_LIMITS),
    ):
        response = await authed_client.post(
            "/api/billing/webhook", json=SUCCEEDED_WEBHOOK_BODY
        )

    assert response.status_code == 200, (
        f"маршрут ответил {response.status_code}. 500 — исключение на денежном "
        "пути: искомая краснота, деньги списаны, ЮKassa будет повторять "
        "уведомление при том же конфиге бесконечно. 403 — гард отверг источник: "
        "краснота ЛОЖНАЯ, случай до предмета не дошёл, и чинить надо тест, а не "
        "`_plan_price`"
    )

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_pro")
        )
    ).scalar_one()
    assert payment.status == "succeeded", (
        f"платёж остался в статусе {payment.status!r} — деньги списаны, дней нет"
    )

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    moved = _aware(rows[0].expires_at)
    assert moved > current, "срок не сдвинулся — деньги не превратились в дни"
    assert moved <= add_one_month(add_one_month(confirmed_at)), (
        "срок ушёл дальше двух календарных месяцев от подтверждения — верхняя "
        "граница `capped_carryover` не включилась, то есть откат пошёл мимо "
        "штатной ветки"
    )


# Формы испорченного `PLAN_LIMITS`. ИСТОЧНИКОВ НАБОРА ДВА, и каждый элемент
# отнесён к своему — набор не переписан из чужого прогона целиком.
#
# (1) ВОСПРОИЗВЕДЕНО ПРЕДЫДУЩИМИ РАУНДАМИ. Первые четыре сняты прогоном
#     верификации раунда 7, и каждая роняла `_plan_price` СВОИМ исключением:
#     `JSONDecodeError`, `AttributeError`, `AttributeError`, `TypeError`.
#     Формы `nan_price` и `infinite_price` даны ДОСЛОВНО отчётом раунда 8.
# (2) ВЫВЕДЕНО ИЗ СВОЙСТВА ВХОДА. Объём защиты, равный объёму того, что успел
#     попробовать предыдущий раунд, есть НЕДООБЪЯВЛЕННЫЙ КОНТРАКТ, а не честно
#     суженный объём. Свойство названо прямо: `json.loads` по умолчанию
#     принимает голые литералы `NaN`, `Infinity` и `-Infinity` И переполняет
#     числовой литерал избыточного порядка в бесконечность, а `Decimal(str(…))`
#     дополнительно принимает написания `nan` и `Infinity` в строках. Отсюда
#     `nan_price_as_string`, `infinite_price_as_string`,
#     `overflowing_price_literal` и `negative_infinite_price`.
#
# Имена форм — ярлыки для `ids=` у `parametrize`: отказ обязан называть ФОРМУ,
# а не индекс, потому что «случай 2 упал» разбирающему не говорит ничего.
MALFORMED_PLAN_LIMITS = (
    ("broken_json", "{not json"),
    ("object_instead_of_list", '{"id": "basic"}'),
    ("list_of_strings", '["basic"]'),
    ("json_null", "null"),
    ("nan_price", '[{"id":"basic","price":NaN},{"id":"pro","price":"4900.00"}]'),
    (
        "infinite_price",
        '[{"id":"basic","price":Infinity},{"id":"pro","price":"4900.00"}]',
    ),
    (
        "nan_price_as_string",
        '[{"id":"basic","price":"nan"},{"id":"pro","price":"4900.00"}]',
    ),
    (
        "infinite_price_as_string",
        '[{"id":"basic","price":"Infinity"},{"id":"pro","price":"4900.00"}]',
    ),
    (
        "overflowing_price_literal",
        '[{"id":"basic","price":1e400},{"id":"pro","price":"4900.00"}]',
    ),
    (
        "negative_infinite_price",
        '[{"id":"basic","price":-Infinity},{"id":"pro","price":"4900.00"}]',
    ),
)

# ДВА КЛАССА ПОЛОМКИ РАЗВЕДЕНЫ КОНСТАНТОЙ, А НЕ КОММЕНТАРИЕМ. Здесь — формы, у
# которых сломана ЦЕНА ОДНОГО ПЛАНА; остальные ломают ПЕРЕЧЕНЬ ЦЕЛИКОМ. Разница
# наблюдаема в журнале и утверждается ниже: авария окружения
# (`plan_limits_unreadable`, уровень `error`) объявляется ТОЛЬКО на второй, и
# утверждение краснеет при смешении двух смыслов — ровно тех, за разведение
# которых план 05-28 заводил отдельный ключ.
#
# ⚠️ `negative_infinite_price` — ГРАНИЦА НАБОРА, А НЕ ЕГО ЧЛЕН ПО ПРИЗНАКУ
# КРАСНОТЫ: она была зелёной и ДО правки плана 05-34, потому что отрицательная
# бесконечность отсеивалась классификацией «не больше нуля». Включена, чтобы
# граница была НАЗВАНА, а не подразумевалась.
PRICE_IS_NOT_FINITE_FORMS = frozenset(
    {
        "nan_price",
        "infinite_price",
        "nan_price_as_string",
        "infinite_price_as_string",
        "overflowing_price_literal",
        "negative_infinite_price",
    }
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("form", "plan_limits"),
    MALFORMED_PLAN_LIMITS,
    ids=[name for name, _ in MALFORMED_PLAN_LIMITS],
)
async def test_a_malformed_plan_list_does_not_break_the_notification(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    form: str,
    plan_limits: str,
):
    """Испорченный перечень тарифов НЕ роняет уведомление ЮKassa.

    ПРИЧИНА ТРЕБОВАНИЯ ПРИКЛАДНАЯ, А НЕ МЕХАНИЧЕСКАЯ. Необработанное исключение
    в обработчике уведомления даёт 5xx, а 5xx на уведомлении ЮKassa запускает
    цикл повторов и оставляет платёж `pending` НАВСЕГДА при уже списанных
    деньгах (T-05-104): при повторе конфиг тот же, и пятисотка та же.

    Форма отказа заводится не ошибкой программиста, а ШТАТНОЙ ОПЕРАЦИЕЙ.
    `PLAN_LIMITS` — строка окружения, разбираемая `json.loads` без схемы, и
    правит её оператор; достижимый путь гонки не требует вовсе: правка
    окружения плюс подтверждение платежа плана, отличного от действующего.

    Четыре формы сняты прогоном верификации, а не придуманы, и каждая роняла
    `_plan_price` СВОИМ исключением: битый JSON — `JSONDecodeError`, объект
    вместо списка и список строк — `AttributeError`, `null` — `TypeError`.

    ШЕСТЬ ФОРМ НЕФИНИТНОЙ ЦЕНЫ ВЫВЕДЕНЫ ИЗ СВОЙСТВА ВХОДА, а не переписаны из
    отчёта: пять из шести роняли `_plan_price` `InvalidOperation` или
    `OverflowError` до правки плана 05-34, шестая (`negative_infinite_price`)
    была зелёной и до неё и включена ГРАНИЦЕЙ набора. Разбор двух классов
    поломки ведёт `PRICE_IS_NOT_FINITE_FORMS`: сломанная ЦЕНА ОДНОГО ПЛАНА не
    объявляет аварии окружения, сломанный ПЕРЕЧЕНЬ объявляет.
    """
    confirmed_at = datetime.now(timezone.utc)
    current = await _seed_live_subscription(db_session, "basic", days=25)
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        accepted = await _confirm_with_plan_limits(
            db_session, "yoo_pro", plan_limits=plan_limits
        )

    assert accepted is True, (
        "уведомление не принято — платёж остаётся `pending`, и ЮKassa будет "
        "повторять его при том же конфиге бесконечно"
    )

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_pro")
        )
    ).scalar_one()
    assert payment.status == "succeeded", (
        f"платёж остался в статусе {payment.status!r} — деньги списаны, дней нет"
    )

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    moved = _aware(rows[0].expires_at)
    assert moved > current, "срок не сдвинулся — деньги не превратились в дни"
    assert moved <= add_one_month(add_one_month(confirmed_at)), (
        "срок ушёл дальше двух календарных месяцев от подтверждения — верхняя "
        "граница `capped_carryover` не включилась, то есть откат пошёл мимо "
        "штатной ветки"
    )

    unreadable_calls = [
        call
        for call in spy.error.call_args_list
        if call.args and call.args[0] == "plan_limits_unreadable"
    ]
    if form in PRICE_IS_NOT_FINITE_FORMS:
        assert not unreadable_calls, (
            f"форма {form!r} ломает ЦЕНУ ОДНОГО ПЛАНА, а журнал объявил АВАРИЮ "
            "ОКРУЖЕНИЯ: перечень разобран, остальные планы читаются, и "
            "`plan_limits_unreadable` здесь лишний — два разных смысла сложены "
            "в один ключ, и разбирающий обращение перестал их различать"
        )
    else:
        assert unreadable_calls, (
            f"форма {form!r} ломает ПЕРЕЧЕНЬ ЦЕЛИКОМ, но собственного следа не "
            "оставила: по журналу «конфиг сломан целиком» неотличимо от «цена "
            "этого плана не читается»"
        )

    # СНЯТО УТВЕРЖДЕНИЕ, КОТОРОЕ НЕ МОГЛО ПОКРАСНЕТЬ. Прежняя редакция искала
    # `subscription_prorating_skipped` в `spy.error` и утверждала его
    # ОТСУТСТВИЕ — истина ТОЖДЕСТВЕННАЯ: ключ пишется уровнем `warning`
    # (`app/services/payment_service.py:1227` и `:1321`) и в `error` не
    # пишется нигде в модуле. Утверждение, истинное при любой правке кода, есть
    # та же форма отказа, что и абзац, который не может оказаться ложным.
    # Взамен утверждается то, что закрепляется на самом деле.
    prorating_calls = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_prorating_skipped"
    ]
    assert prorating_calls, (
        "откат не оставил следа там, где ключ действительно пишется — уровень "
        "`warning`, а не `error`"
    )
    assert any(
        call.kwargs.get("stage") == "convert_remainder"
        for call in prorating_calls
    ), (
        "след не называет ВЕТКУ. Тот же ключ испускает ветка отказа, словари "
        "`unreadable` у двух испусканий ПЕРЕСЕКАЮТСЯ, и без поля `stage` "
        "разбирающий обращение получает два разных исхода в одном событии "
        "(`IN-04`)"
    )


# =============================================================================
# ПОТОЛОК ОДНОВРЕМЕННЫХ НАМЕРЕНИЙ — ЧЕРЕЗ НАСТОЯЩИЙ ОБРАБОТЧИК ФОРМЫ
# =============================================================================
#
# ЧТО ЗАКРЫВАЕТ ЭТОТ РАЗДЕЛ. Последний открытый путь случая (1) третьего пункта
# `missing:` раунда 4: два подписочных платежа РАЗНЫХ тарифов, заведённых ФОРМОЙ
# и потому несущих записанное разрешение `True` оба. Записанное разрешение
# (D-28) на нём бессильно по построению — когда подписки нет вовсе, гард
# пропускает любой план, — а доля месяца (D-29) не исполняется вовсе, потому что
# отказа не возникает ни у одного платежа. Лечится это не решением о сделке и не
# арифметикой дней, а НЕДОПУЩЕНИЕМ СОСТОЯНИЯ: пока два разрешённых намерения
# разных тарифов не могут висеть одновременно, `subscription.plan` не обязан
# вмещать два перехода в разные стороны.
#
# ФОРМА — `cap-different-plan` (решение владельца, чекпойнт задачи 1 плана
# 05-15): повтор оплаты ТОГО ЖЕ тарифа остаётся разрешённым.


@pytest.mark.asyncio
async def test_a_second_subscription_intent_from_the_form_is_refused_with_words(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Форма отвечает на потолок 302 с ПРИЧИНОЙ и не заводит второй строки.

    Голый редирект здесь был бы худшим из ответов: человек, нажавший «Оплатить»
    и получивший ту же страницу, читает это как поломку и нажимает снова —
    ровно то поведение, которое потолок и ловит.
    """
    first = await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")
    assert first.status_code == 302
    assert first.headers["location"] == CONFIRMATION_URL

    second = await _subscribe(authed_client, plan="basic", payment_id="yoo_basic")

    assert second.status_code == 302
    assert second.headers["location"] == "/billing?error=pending", (
        "второе намерение другого тарифа ушло на оплату либо вернулось без слов"
    )
    assert await _payments_count(db_session) == 1, "заведена вторая строка платежа"


@pytest.mark.asyncio
async def test_a_second_intent_of_another_plan_is_refused_while_the_first_is_fresh(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Второе намерение ДРУГОГО тарифа отвергается, пока первое СВЕЖЕЕ.

    ⚠️ ЧЕМ ЭТОТ ТЕСТ ОТЛИЧАЕТСЯ ОТ
    `test_a_pro_deal_sold_before_any_subscription_is_not_erased_by_a_later_basic`,
    И БЕЗ ЭТОЙ ФРАЗЫ СЛЕДУЮЩИЙ ЧИТАТЕЛЬ УДАЛИТ ОДИН ИЗ НИХ КАК ДУБЛИКАТ. Тот
    держит строки БЕЗ записанного ответа (`switch_authorized IS NULL`, то есть
    заведённые до ревизии `0019`): у них решение принимает правило, отказ
    возникает, и предмет проверки — доля месяца (D-29). ЗДЕСЬ строки заводит
    ФОРМА, и обе несут записанное разрешение `True`: отказа не возникает ни у
    одной, ветка доли месяца не исполняется вовсе, и вылечить это можно только
    тем, чтобы второй строки не появилось. Тот тест проверяет, СКОЛЬКО дней
    покупает отвергнутый платёж; этот — что второго платежа не существует.

    Именно на этом пути сделка на 4900 ₽ продавалась и стиралась последним
    подтверждённым `basic`.

    ⚠️ ЧЕГО ЭТОТ ТЕСТ НЕ ДЕРЖИТ, И ПОЧЕМУ ЕГО ИМЯ БОЛЬШЕ НЕ ГОВОРИТ
    «UNREACHABLE». Оба намерения он заводит ПОДРЯД, о сроке давности не знает
    вовсе, и потому доказывает ровно одно: пока первое намерение СВЕЖЕЕ, второго
    не появится. Состояние «два оплачиваемых намерения разных тарифов»
    недостижимым он НЕ объявляет — оно достижимо через сутки, и это доказывает
    `tests/test_services/test_payment_service.py::test_a_stale_intent_does_not_block_a_new_one`.
    Прежнее имя обещало инвариант шире тела, и читатель, искавший покрытие по
    имени, получал ложную уверенность (WR-05 раунда 5).
    """
    await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")
    refused = await _subscribe(authed_client, plan="basic", payment_id="yoo_basic")
    assert refused.headers["location"] == "/billing?error=pending"
    assert await _payments_count(db_session) == 1

    assert await _confirm(db_session, "yoo_pro") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "заведена вторая подписка"
    assert rows[0].plan == "pro", "проданный старший тариф не выдан"
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=27), (
        "оплаченный месяц не выдан вовсе"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "срок сдвинут дважды — второй платёж всё-таки существует"
    )


@pytest.mark.asyncio
async def test_a_package_purchase_is_not_blocked_by_a_pending_subscription_intent(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пакет потолком не задет: у него нет плана, и вмещать ему нечего.

    Защита от одновременных намерений существует из-за скалярности
    `subscription.plan`. Распространить её на пакеты значило бы запретить
    покупку сообщений человеку, у которого просто висит неоплаченная подписка.
    """
    await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")

    response = await _purchase(authed_client)

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    assert await _payments_count(db_session) == 2


# =============================================================================
# ГЭП 1 РАУНДА 5 — НАКОПЛЕННЫЙ ПРЕДОПЛАЧЕННЫЙ ГОРИЗОНТ И ЕГО ПЕРЕВОД НА
# СТАРШИЙ ТАРИФ ОДНИМ ПЛАТЕЖОМ
#
# ПРЕДМЕТ РАЗДЕЛА. Горизонт предоплаты — величина, которой управляет ПОКУПАТЕЛЬ:
# он предоплачивает младший тариф сколько угодно раз подряд, и ни гард формы, ни
# потолок одновременных намерений повтору СВОЕГО тарифа не мешают (и не должны).
# Затем один платёж старшего тарифа переводит на него ВЕСЬ накопленный горизонт,
# потому что `subscription.plan` — скаляр без истории: вместить два отрезка,
# купленных по разным ценам, эта величина не умеет.
#
# ЧИСЛА ОТЧЁТА (`05-VERIFICATION.md`, гэп 1, воспроизведено верификацией поверх
# настоящего кода, без единой правки `app/`): двенадцать платежей `basic`
# (17 880 ₽) плюс один платёж `pro` (4 900 ₽) — уплачено 22 780 ₽ — давали
# ТРИНАДЦАТЬ месяцев Pro при прейскуранте 63 700 ₽. Утечка растёт ЛИНЕЙНО с
# горизонтом предоплаты.
#
# ПРАВИЛО УТВЕРЖДЕНИЙ ЭТОГО РАЗДЕЛА. Каждое читает только СЕГОДНЯШНЕЕ
# наблюдаемое состояние — строку `subscriptions`, перечитанную из БД после
# операции (её `plan` и `expires_at`), и строки `payments` (их число и
# уплаченные суммы). Ни одно не называет символа, которого ещё нет: утверждение
# о несуществующем имени даёт ошибку импорта вместо доказательства красноты, и
# эта фигура уже раскрыта планами 05-15 и 05-17.
# =============================================================================


async def _accrue_confirmed_months(
    db: AsyncSession, plan: str, count: int, *, amount: str
) -> tuple[datetime, Decimal]:
    """`count` ПОДТВЕРЖДЁННЫХ платежей одного тарифа. Возвращает срок И уплаченное.

    ОБЕ ВЕЛИЧИНЫ НЕСУЩИЕ, И ВТОРАЯ — НЕ УДОБСТВО. Утверждение о прейскуранте
    есть отношение ДВУХ чисел: сколько срока накоплено и сколько за него отдано.
    Помощник, возвращающий только срок, заставил бы каждый тест считать сумму у
    себя — то есть завёл бы столько копий прейскуранта, сколько тестов.

    Платежи заводятся `_seed_subscription_payment` и подтверждаются `_confirm`
    поимённо: идентификаторы нумеруются, потому что одинаковый
    `yookassa_payment_id` сделал бы вторую строку дубликатом и выборка в
    `handle_webhook` подняла бы `MultipleResultsFound` вместо накопления срока.

    `switch_authorized=True` — то, что записывает форма на повторе СВОЕГО тарифа
    (D-28): гард спросили, и он разрешил. Умолчание `None` («правило не
    спрашивали») описывало бы строки старше ревизии `0019`, то есть другой путь.
    """
    paid = Decimal("0.00")
    for index in range(count):
        payment_id = f"yoo_{plan}_{index}"
        await _seed_subscription_payment(
            db, plan, payment_id, switch_authorized=True, amount=amount
        )
        assert await _confirm(db, payment_id) is True, (
            f"уведомление по платежу {payment_id} не обработано"
        )
        paid += Decimal(amount)

    rows = await _subscription_rows(db)
    assert len(rows) == 1, "посев завёл вторую строку подписки"
    return _aware(rows[0].expires_at), paid


@pytest.mark.asyncio
async def test_a_prepaid_horizon_is_not_converted_to_the_senior_plan_for_one_month(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Накопленный горизонт не переезжает на старший тариф за цену ОДНОГО месяца.

    ЭТО ЯДРО ГЭПА 1 РАУНДА 5. Уплачено 22 780 ₽ (двенадцать `basic` по 1490 ₽ и
    один `pro` за 4900 ₽); прейскурант тринадцати месяцев Pro — 63 700 ₽.
    Механизм воспроизведён верификацией НЕЗАВИСИМО, поверх настоящего кода и без
    единой правки `app/`, поэтому предмет теста — не гипотеза.

    ЧТО УТВЕРЖДАЕТСЯ (форма `convert-remainder`, решение владельца). Оплаченный
    остаток младшего тарифа переносится ПО ДЕНЬГАМ, а не по дням: он стоит
    столько дней старшего тарифа, сколько за него отдано по отношению цен.
    Сверху добавляется оплаченный месяц старшего тарифа — тот, за который
    заплачено тринадцатым платежом.

    ОЖИДАЕМОЕ ЧИСЛО СЧИТАЕТ АРИФМЕТИКА САМОГО ТЕСТА, а не вызов функции границы:
    тест, зовущий её, зеленел бы вместе с ней тавтологически, каким бы ни
    оказалось её содержимое. Допуск в два дня — цена того, что тест и денежный
    путь снимают `now` в разные микросекунды, а число дней округляется вниз.
    """
    accrued, paid_basic = await _accrue_confirmed_months(
        db_session, "basic", 12, amount="1490.00"
    )
    now = datetime.now(timezone.utc)
    remainder_days = (accrued - now).days
    assert remainder_days > 300, (
        "посев не накопил предоплаченного горизонта — проверять нечего"
    )

    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )
    assert await _confirm(db_session, "yoo_pro") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "тринадцатый платёж завёл вторую подписку"
    assert rows[0].plan == "pro", "оплаченное повышение не применено"

    converted_days = int(Decimal(remainder_days) * BASIC_PRICE / PRO_PRICE)
    expected = add_one_month(now + timedelta(days=converted_days))
    assert abs(_aware(rows[0].expires_at) - expected) <= timedelta(days=2), (
        f"уплачено {paid_basic + PRO_PRICE} ₽, а выдан горизонт "
        f"{(_aware(rows[0].expires_at) - now).days} дней на тарифе pro: "
        f"остаток {remainder_days} дней basic обязан стоить {converted_days} "
        "дней pro, а не переезжать на старший тариф днями"
    )


@pytest.mark.asyncio
async def test_repeated_payments_of_one_plan_stay_priced_at_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повтор СВОЕГО тарифа остаётся возможным и остаётся честным.

    N платежей одного тарифа дают N месяцев ЭТОГО тарифа по прейскуранту — и
    правило `upgrade-only` (`plan_switch.py:87-88`, повтор своего тарифа им не
    задевается) этой правкой не переоткрывается. Самый вероятный способ сломать
    закрытие гэпа 1 — запретить предоплату вообще, и тогда пользователь,
    оплативший год вперёд СВОЕГО тарифа, получил бы отказ там, где ничего дурного
    не сделал.

    ⚠️ РОЛЬ ЭТОГО УТВЕРЖДЕНИЯ — ХАРАКТЕРИЗУЮЩАЯ, А НЕ ПАДАЮЩАЯ, И ЭТО НАЗВАНО
    ЗДЕСЬ ЧЕСТНО. Пункт `missing:` №2 гэпа 1 требует от регрессии повторных
    платежей падения на текущем коде; падающей она является ТОЛЬКО при форме
    `cap-horizon`, где повтор упирался бы в новый потолок. Выбранная форма
    `convert-remainder` трогает ПОВЫШЕНИЕ и повтора своего тарифа не задевает
    вовсе — падать этому тесту не на чем, и написать его падающим можно было бы
    только утверждением, которое потом пришлось бы ослабить.
    """
    accrued, paid = await _accrue_confirmed_months(
        db_session, "basic", 12, amount="1490.00"
    )
    now = datetime.now(timezone.utc)

    rows = await _subscription_rows(db_session)
    assert rows[0].plan == "basic", "повтор своего тарифа сменил тариф"
    assert paid == BASIC_PRICE * 12, "уплачено не по прейскуранту"
    assert await _payments_count(db_session) == 12, (
        "часть повторов своего тарифа не продана"
    )
    # Двенадцать календарных месяцев — 365 или 366 дней; окно 362…368 лежит
    # между одиннадцатью (не больше 341) и тринадцатью (не меньше 393), поэтому
    # промах в любую сторону однозначен.
    assert now + timedelta(days=362) < accrued < now + timedelta(days=368), (
        "двенадцать оплаченных месяцев дали не двенадцать месяцев срока"
    )


@pytest.mark.asyncio
async def test_an_upgrade_with_one_paid_month_still_does_not_burn_the_remainder(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Защитная: на масштабе ОДНОГО месяца остаток по-прежнему не сгорает.

    Семантика D-04 («срок считается от СРОКА, а не от сегодня») правкой границы
    не отменяется, а измеряется: остаток переживает переход в виде своего
    ДЕНЕЖНОГО эквивалента, строго большего нуля дней. Сгоревшим считался бы
    исход «ровно один месяц от сегодня» — то есть повышение, отнявшее у человека
    всё, что он уже оплатил.

    ⚠️ РОЛЬ — ЗАЩИТНАЯ: утверждение зелено и на текущем коде (там остаток
    переносится днями, что тем более больше месяца от сегодня). Оно держит не
    дефект, а то, что правка не имеет права сломать.
    """
    await _accrue_confirmed_months(db_session, "basic", 1, amount="1490.00")
    now = datetime.now(timezone.utc)

    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )
    assert await _confirm(db_session, "yoo_pro") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "повышение завело вторую подписку"
    assert rows[0].plan == "pro", "оплаченное повышение не применено"
    assert _aware(rows[0].expires_at) > add_one_month(now), (
        "оплаченный остаток сгорел: повышение выдало ровно месяц от сегодня"
    )


# =============================================================================
# ГЭП 1 РАУНДА 6 — ВЕТКА ОТКАТА ДЕНЕЖНОГО ПУТИ, ГДЕ ЦЕНУ ПРОЧИТАТЬ НЕЛЬЗЯ
#
# ПРЕДМЕТ РАЗДЕЛА. Верхняя граница предоплаченного горизонта поставлена в ветке
# КОНВЕРСИИ (обе цены читаются) и ОТСУТСТВОВАЛА в ветке ОТКАТА: при
# `price_from is None or price_to is None` переменная `base` оставалась связанной
# с `subscription.expires_at`, после чего срок двигался от НЕЁ, а план
# перезаписывался платежом. Это дословно поведение до плана `05-18`, и
# верификация раунда 6 воспроизвела его численно поверх настоящего кода, без
# единой правки `app/`: тот же посев, что даёт 140 дней на соседней ветке, здесь
# давал 396 дней Pro за 22 780 ₽ при прейскуранте 63 700 ₽.
#
# ВЕТКА НЕ РЕДКАЯ, И ЭТО УТВЕРЖДАЕТ САМ КОД. Два входа, и ни один не требует ни
# гонки, ни правки кода:
#   * `price_to is None` — план ПЛАТЕЖА выпал из `parsed_plan_limits`. Перечень
#     правится окружением, и код называет это нормальным состоянием;
#   * `price_from is None` — цена ДЕЙСТВУЮЩЕГО плана не читается. Сюда попадает
#     `free` ПО ПОСТРОЕНИЮ: `_plan_price` объявляет непригодной цену, не большую
#     нуля (`payment_service.py:814`), а `free` объявлен `"0.00"`
#     (`app/config.py`).
#
# ФОРМА ГРАНИЦЫ — `cap-one-month` (РЕШЕНИЕ ВЛАДЕЛЬЦА, чекпойнт задачи 1 плана
# 05-22): перенос оплаченного остатка ограничен потолком в ОДИН календарный
# месяц. Остаток короче месяца переносится целиком и не сгорает; остаток длиннее
# месяца сгорает В ЧАСТИ, превышающей месяц, — цена формы названа числом и
# принята сознательно, а не пропущена.
#
# ПРАВИЛО УТВЕРЖДЕНИЙ ЭТОГО РАЗДЕЛА — ТО ЖЕ, ЧТО У РАЗДЕЛА ВЫШЕ. Каждый
# интеграционный тест читает СЕГОДНЯШНЕЕ наблюдаемое состояние (строку
# `subscriptions`, перечитанную из БД) и утверждает И величину горизонта, И
# значение в журнале. Тест, утверждающий только журнал, зелен от рождения:
# журнальную запись эта ветка испускала и до правки.
# =============================================================================

# Значения поля, называющего ВЕТКУ у двух испусканий одного журнального ключа
# (`IN-04` раунда 6). Ключ `subscription_prorating_skipped` намеренно один:
# событие ровно то же — «цену прочитать нельзя, дни считаем по-старому», — и
# второй ключ под тот же исход разошёлся бы с первым при первой же правке.
# Различает ветки ПОЛЕ, и обе строки выписаны здесь, потому что предмет
# проверки — что разбирающий обращение может НАЗВАТЬ ветку, а не что поле
# непустое.
STAGE_PRORATE_REFUSED = "prorate_refused"
STAGE_CONVERT_REMAINDER = "convert_remainder"


def _prorating_skips(spy) -> list:
    """Испускания `subscription_prorating_skipped` из перехваченного журнала."""
    return [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_prorating_skipped"
    ]


@pytest.mark.asyncio
async def test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Цена плана ПЛАТЕЖА нечитаема — весь горизонт на старший тариф не едет.

    ДОСТИЖИМОСТЬ — СВОЙСТВО ЭКСПЛУАТАЦИИ, А НЕ ГИПОТЕЗА. Перечень тарифов
    правится переменной окружения, а план записан в строке платежа: одна правка
    `.env` (переименовали `pro`, сняли его с продажи) — и КАЖДОЕ повышение на
    этот план идёт веткой отката. Ранг при этом известен (`pro` есть в
    `PLAN_ORDER`), переход разрешён, и отказа не возникает — не читается только
    ЦЕНА.

    ЧТО УТВЕРЖДАЕТСЯ (форма `cap-one-month`, решение владельца). Перенос
    оплаченного остатка ограничен одним календарным месяцем, поверх которого
    ложится оплаченный месяц старшего тарифа: горизонт не превышает двух
    календарных месяцев от сегодня. Нижним утверждением закреплено, что остаток
    при этом НЕ СГОРЕЛ дочиста — обещание «оплаченные дни не сгорают» держится в
    объёме границы.

    ОЖИДАЕМОЕ ЧИСЛО СЧИТАЕТ АРИФМЕТИКА САМОГО ТЕСТА, а не вызов функции границы:
    тест, зовущий её, зеленел бы вместе с ней тавтологически. Допуск в два дня —
    цена того, что тест и денежный путь снимают `now` в разные микросекунды.
    """
    current = await _seed_live_subscription(db_session, "basic", days=365)
    now = datetime.now(timezone.utc)
    remainder_days = (_aware(current) - now).days
    assert remainder_days > 300, (
        "посев не накопил предоплаченного горизонта — проверять нечего"
    )

    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        handled = await _confirm_with_plan_limits(
            db_session, "yoo_pro", plan_limits=PLAN_LIMITS_WITHOUT_PRO
        )
    assert handled is True, "уведомление по платежу не обработано"

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "повышение завело вторую подписку"
    assert rows[0].plan == "pro", "оплаченное повышение не применено"

    granted = _aware(rows[0].expires_at)
    ceiling = add_one_month(add_one_month(now))
    assert granted <= ceiling + timedelta(days=2), (
        f"уплачено {BASIC_PRICE * 12 + PRO_PRICE} ₽, а выдан горизонт "
        f"{(granted - now).days} дней на тарифе pro при прейскуранте "
        f"{PRO_PRICE * 13} ₽: остаток {remainder_days} дней перенесён ЦЕЛИКОМ — "
        "у ветки отката нет верхней границы"
    )
    assert granted > add_one_month(now), (
        "оплаченный остаток сгорел дочиста: повышение выдало ровно месяц от "
        "сегодня, хотя граница обязана переносить месяц остатка"
    )

    skips = _prorating_skips(spy)
    assert len(skips) == 1, "ветка отката не оставила ровно одного следа в журнале"
    fields = skips[0].kwargs
    assert fields.get("unreadable") == "paid_plan_price", (
        "журнал не назвал, ЧЬЯ именно цена не прочиталась — цена плана платежа "
        "и цена действующего плана дают разные исходы и разбираются по-разному"
    )
    assert fields.get("stage") == STAGE_CONVERT_REMAINDER, (
        "испускание не назвало своей ветки: тот же ключ приходит из ветки "
        f"{STAGE_PRORATE_REFUSED}, и без поля разбирающий обращение их не "
        "различит"
    )


@pytest.mark.asyncio
async def test_an_upgrade_from_free_does_not_carry_the_whole_horizon(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повышение с `free` с живым горизонтом не переносит горизонт целиком.

    ⚠️ МЕХАНИЗМ ДОСТИЖИМОСТИ НАЗВАН ЗДЕСЬ ПРЯМО, ПОТОМУ ЧТО ЭТО НЕ РЕДКИЙ ОТКАЗ,
    А СВОЙСТВО ПОСТРОЕНИЯ. Цена `free` объявлена `"0.00"` в `app/config.py`, а
    `_plan_price` объявляет непригодной цену, НЕ БОЛЬШУЮ НУЛЯ
    (`payment_service.py:814`) — и делает это не по недосмотру: деление на ноль
    было бы отказом обработчика уведомления на самом достижимом из планов.
    Значит, ЛЮБАЯ строка подписки на `free` с живым сроком берёт ветку отката на
    первом же платном повышении, без единой правки конфига и без гонки.

    Здесь не читается цена ДЕЙСТВУЮЩЕГО плана (`price_from is None`), поэтому
    журнал называет `price`, а не `paid_plan_price`: два разных входа в одну
    ветку различимы по этому полю, и оба обязаны быть ограничены.
    """
    current = await _seed_live_subscription(db_session, "free", days=365)
    now = datetime.now(timezone.utc)
    remainder_days = (_aware(current) - now).days
    assert remainder_days > 300, (
        "посев не накопил предоплаченного горизонта — проверять нечего"
    )

    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        handled = await _confirm(db_session, "yoo_pro")
    assert handled is True, "уведомление по платежу не обработано"

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "повышение завело вторую подписку"
    assert rows[0].plan == "pro", "оплаченное повышение не применено"

    granted = _aware(rows[0].expires_at)
    ceiling = add_one_month(add_one_month(now))
    assert granted <= ceiling + timedelta(days=2), (
        f"уплачено {PRO_PRICE} ₽, а выдан горизонт {(granted - now).days} дней "
        f"на тарифе pro при прейскуранте {PRO_PRICE * 13} ₽: остаток "
        f"{remainder_days} дней бесплатного тарифа перенесён ЦЕЛИКОМ"
    )
    assert granted > add_one_month(now), (
        "оплаченный остаток сгорел дочиста: повышение выдало ровно месяц от "
        "сегодня, хотя граница обязана переносить месяц остатка"
    )

    skips = _prorating_skips(spy)
    assert len(skips) == 1, "ветка отката не оставила ровно одного следа в журнале"
    fields = skips[0].kwargs
    assert fields.get("unreadable") == "price", (
        "журнал не назвал нечитаемой цену ДЕЙСТВУЮЩЕГО плана"
    )
    assert fields.get("stage") == STAGE_CONVERT_REMAINDER, (
        "испускание не назвало своей ветки: тот же ключ приходит из ветки "
        f"{STAGE_PRORATE_REFUSED}, и без поля разбирающий обращение их не "
        "различит"
    )


@pytest.mark.asyncio
async def test_the_refused_branch_names_its_own_stage_in_the_journal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Второе испускание того же ключа называет СВОЮ ветку — и другим значением.

    ⚠️ ЧЕМ ЭТОТ ТЕСТ ОТЛИЧАЕТСЯ ОТ
    `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`, И БЕЗ ЭТОЙ
    ФРАЗЫ СЛЕДУЮЩИЙ ЧИТАТЕЛЬ УДАЛИТ ОДИН ИЗ НИХ КАК ДУБЛИКАТ. Тот держит откат к
    полному месяцу при нечитаемой ЦЕНЕ и утверждает, что дни не отняты. Здесь
    нечитаема УПЛАЧЕННАЯ СУММА (`unreadable="amount"` — значение, которое до
    этого теста не утверждал ни один тест суиты), а предмет проверки — что
    испускание ветки ОТКАЗА несёт своё, ОТЛИЧНОЕ от ветки конверсии значение
    поля `stage`.

    БЕЗ ЭТОГО УТВЕРЖДЕНИЯ РАЗЛИЧИМОСТЬ ДВУХ ИСПУСКАНИЙ БЫЛА БЫ ЗАЯВЛЕНА, А НЕ
    ПРОВЕРЕНА: тесты выше видят только испускание ветки конверсии, и правка,
    поставившая обеим веткам одно значение, осталась бы для них зелёной.
    """
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="не-число"
    )

    with patch("app.services.payment_service.logger") as spy:
        handled = await _confirm(db_session, "yoo_basic")
    assert handled is True, "нечитаемая сумма уронила обработчик уведомления"

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "отвергнутый младший тариф всё-таки применён"

    skips = _prorating_skips(spy)
    assert len(skips) == 1, "ветка отказа не оставила следа в журнале"
    fields = skips[0].kwargs
    assert fields.get("unreadable") == "amount", (
        "журнал назвал нечитаемой цену, хотя не прочиталась уплаченная сумма"
    )
    assert fields.get("stage") == STAGE_PRORATE_REFUSED, (
        f"ветка отказа не назвала себя: значение {STAGE_CONVERT_REMAINDER} "
        "принадлежит ветке конверсии, и совпадение сделало бы два разных исхода "
        "неразличимыми в журнале"
    )


# =============================================================================
# ГЭП РАУНДА 9, ЭКЗЕМПЛЯР (б) — ЦЕНА, КУПЛЕННЫЙ КОТОРОЙ СРОК НЕ ВЫРАЖАЕТСЯ
# КАЛЕНДАРЁМ
#
# ПРЕДМЕТ РАЗДЕЛА. `prorated_days` не имеет верхнего потолка, и это ОБЪЯВЛЕННОЕ
# решение D-29: сумма больше цены покупает больше месяца, а обрезание было бы
# «взяли деньги и не дали ничего». Решение не отменяется и не сужается ни одним
# тестом этого раздела. Отменяется другое: доля месяца, у которой нет момента в
# календаре. `datetime` кончается 9999 годом, а цена `0.01` при уплаченных
# 1490 ₽ покупает около 4 619 000 дней — момента с такой датой не существует,
# `base + timedelta(...)` поднимает `OverflowError`, и он доходит до
# `app/routes/billing.py:200-202`, где становится HTTP 500 на уведомлении при
# УЖЕ СПИСАННЫХ деньгах (T-05-104). Закреплено
# `test_a_price_beyond_the_calendar_does_not_five_hundred_the_notification`.
#
# ГРАНИЦА НАЗВАНА ЧИСЛОМ И ПРОХОДИТ ПО ВЫРАЗИМОСТИ, А НЕ ПО ПРАВДОПОДОБИЮ
# ВЕЛИЧИНЫ. Цена `1.00` даёт 46 190 дней (2153 год), цена `0.05` — 923 800 дней
# (4555 год); ОБЕ выражаются календарём, обе остаются пропорциональными, и ни
# одна не уводит на откат. Делового потолка здесь нет и этой правкой не
# заводится — иначе она противоречила бы D-29 в том самом месте, где D-29
# объявлен. Закреплено
# `test_a_span_that_the_calendar_can_express_is_not_capped`.
#
# НЕПРИГОДНАЯ ЦЕНА ЛЕЧИТСЯ ТЕМ ЖЕ ОТКАТОМ, ЧТО И НЕЧИТАЕМАЯ: полный календарный
# месяц плюс `subscription_prorating_skipped` уровня `warning`. Исход назван
# СВОИМ значением поля `unreadable` (`IN-04`): «цену прочитать нельзя» и «срока,
# купленного этой ценой, не существует» — два разных исхода, и разбирающий
# обращение обязан их различать. Закреплено
# `test_a_price_beyond_the_calendar_does_not_break_the_conversion_branch`.
# =============================================================================

# Значение поля `unreadable`, называющее исход «момента с такой датой нет».
# Стоит рядом с `"price"`, `"amount"` и `"paid_plan_price"` — теми же словами,
# что и они, потому что читает их один и тот же человек.
UNREADABLE_SPAN = "span"
UNREADABLE_AMOUNT = "amount"

# Цена `pro` в перечне тарифов. Ни одна из трёх не является ошибкой формата:
# это правильно оформленные положительные значения, какие оператор ставит
# промо-тарифу.
PRICE_BEYOND_THE_CALENDAR = "0.01"  # ~4 619 000 дней — момента нет
PRICE_OF_MILLENNIA = "0.05"  # ~923 800 дней — 4555 год, момент ЕСТЬ
PRICE_OF_A_LONG_SPAN = "1.00"  # ~46 190 дней — 2153 год, момент ЕСТЬ


def _plan_limits_with_pro_priced(price: str) -> str:
    """Перечень тарифов, где у `pro` названная цена, а у `basic` — прейскурантная.

    Цена приезжает аргументом, а не правкой модульной переменной: перечень
    тарифов есть глобальное для денежного пути состояние, и утечка его на
    соседний тест сменила бы цены там, где предмет проверки другой (T-05-143).
    """
    return json.dumps(
        [{"id": "basic", "price": "1490.00"}, {"id": "pro", "price": price}]
    )


async def _post_succeeded_webhook(
    client: AsyncClient, payment_id: str, plan_limits: str | None = None
):
    """Настоящий маршрут `POST /api/billing/webhook` при названном перечне цен.

    `plan_limits` со значением `None` означает УМОЛЧАНИЕ конфига — прейскурант
    проекта без единой подмены; так ходят случаи, чей предмет не цена.

    Предмет утверждений этого раздела — HTTP-код, а не возврат функции.
    Исключение денежного пути доходит до `app/routes/billing.py:200-202`, где
    `except Exception` превращает его в `HTTPException(500)`; именно 500
    запускает цикл повторов ЮKassa и оставляет платёж `pending` навсегда при уже
    списанных деньгах (T-05-104). Прямой вызов `handle_webhook` через это место
    не проходит вовсе, поэтому стеречь 500 может только маршрут. Закреплено
    `test_a_price_beyond_the_calendar_does_not_five_hundred_the_notification`.
    """
    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ), patch(
        "app.services.payment_service.get_settings",
        return_value=_app_settings(plan_limits),
    ):
        return await client.post(
            "/api/billing/webhook",
            json={"event": "payment.succeeded", "object": {"id": payment_id}},
        )


@pytest.mark.asyncio
async def test_a_price_beyond_the_calendar_does_not_five_hundred_the_notification(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings: Settings
):
    """Цена, покупающая невыразимый срок, НЕ даёт 500 на маршруте уведомления.

    Посев — ветка ОТКАЗА: живая `pro` плюс отвергнутый ПО ПРАВИЛУ `basic`
    (`switch_authorized=None`), та же форма, что у
    `test_the_refused_branch_names_its_own_stage_in_the_journal`.

    Гард источника снимается явно, аварийным выключателем: умолчание конфига
    равно `True`, и запрос без заголовка адреса получил бы 403, то есть случай
    покраснел бы по причине, к предмету не относящейся.
    """
    confirmed_at = datetime.now(timezone.utc)
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    test_settings.yookassa_webhook_verify_ip = False

    with patch("app.services.payment_service.logger") as spy:
        response = await _post_succeeded_webhook(
            authed_client,
            "yoo_basic",
            _plan_limits_with_pro_priced(PRICE_BEYOND_THE_CALENDAR),
        )

    assert response.status_code == 200, (
        f"маршрут ответил {response.status_code}. 500 — `OverflowError: date "
        "value out of range` на денежном пути: деньги списаны, ЮKassa будет "
        "повторять уведомление при том же прейскуранте бесконечно. 403 — гард "
        "отверг источник: краснота ЛОЖНАЯ, случай до предмета не дошёл"
    )

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_basic")
        )
    ).scalar_one()
    assert payment.status == "succeeded", (
        f"платёж остался в статусе {payment.status!r} — деньги списаны, дней нет"
    )

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "отвергнутый младший тариф всё-таки применён"
    moved = _aware(rows[0].expires_at)
    assert moved > current, "срок не сдвинулся — деньги не превратились в дни"
    assert moved <= add_one_month(add_one_month(confirmed_at)), (
        f"записан срок {moved.date()} — откат к полному календарному месяцу не "
        "сработал, и в базу ушёл момент, которого никто не покупал"
    )

    skips = _prorating_skips(spy)
    assert len(skips) == 1, "непригодная цена не оставила ровно одного следа"
    fields = skips[0].kwargs
    assert fields.get("unreadable") == UNREADABLE_SPAN, (
        f"журнал назвал исход {fields.get('unreadable')!r}: цена ПРОЧИТАНА, не "
        "существует купленного ею СРОКА, и без своего значения этот исход "
        "неотличим от нечитаемой цены и от нечитаемой суммы"
    )
    assert fields.get("stage") == STAGE_PRORATE_REFUSED


@pytest.mark.asyncio
async def test_a_price_beyond_the_calendar_does_not_break_the_conversion_branch(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings: Settings
):
    """ВТОРАЯ ветка того же дефекта: конверсия остатка зовёт тот же `prorated_days`.

    Без этого случая объём защиты снова равнялся бы объёму того, что успел
    попробовать предыдущий раунд, — ровно тот НЕДООБЪЯВЛЕННЫЙ КОНТРАКТ, который
    раунд 8 назвал по имени, а D-35 объявил унаследованным суждением.

    Посев — РАЗРЕШЁННОЕ повышение при живом остатке: `basic` действует, оплачен
    `pro`, ответ гарда записан. Ветка отказа сюда не заходит вовсе.
    """
    confirmed_at = datetime.now(timezone.utc)
    await _seed_live_subscription(db_session, "basic", days=25)
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True, amount="4900.00"
    )

    test_settings.yookassa_webhook_verify_ip = False

    with patch("app.services.payment_service.logger") as spy:
        response = await _post_succeeded_webhook(
            authed_client,
            "yoo_pro",
            _plan_limits_with_pro_priced(PRICE_BEYOND_THE_CALENDAR),
        )

    assert response.status_code == 200, (
        f"маршрут ответил {response.status_code}. 500 — `OverflowError` из "
        "`converted_remainder`: та же арифметика, другая ветка, тот же вечный "
        "`pending` при списанных деньгах"
    )

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "оплаченный старший тариф не применён"
    moved = _aware(rows[0].expires_at)
    assert moved <= add_one_month(add_one_month(confirmed_at)), (
        f"записан срок {moved.date()} — зажим переноса не включился, и в базу "
        "ушёл момент, которого никто не покупал"
    )

    skips = _prorating_skips(spy)
    assert len(skips) == 1, "ветка конверсии не оставила ровно одного следа"
    fields = skips[0].kwargs
    assert fields.get("unreadable") == UNREADABLE_SPAN
    assert fields.get("stage") == STAGE_CONVERT_REMAINDER, (
        f"значение {STAGE_PRORATE_REFUSED} принадлежит ветке отказа, и "
        "совпадение сделало бы два разных исхода неразличимыми в журнале"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("form", "price"),
    (("long_span", PRICE_OF_A_LONG_SPAN), ("millennia", PRICE_OF_MILLENNIA)),
    ids=("long_span", "millennia"),
)
async def test_a_span_that_the_calendar_can_express_is_not_capped(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    test_settings: Settings,
    form: str,
    price: str,
):
    """ПАРНЫЙ СЛУЧАЙ: делового потолка нет, и соседняя защита его не заводит.

    Без него защита выше зеленела бы и от обрезания доли месяца — то есть от
    исхода «взяли деньги и не дали ничего», который D-29 называет ХУДШИМ из
    возможных. Цена `1.00` даёт 2153 год, цена `0.05` — 4555; обе выражаются
    календарём, обе остаются пропорциональными, и ни одна не уходит на откат.

    ⚠️ ЦЕНА ЭТОГО РЕШЕНИЯ НАЗВАНА, А НЕ ЗАМОЛЧАНА: в базу действительно уходит
    срок, отстоящий на века, и наблюдаемым он остаётся сознательно — это ответ
    D-29 на вопрос «что покупает сумма, во много раз превышающая цену». Граница
    этого утверждения — соседний
    `test_a_price_beyond_the_calendar_does_not_five_hundred_the_notification`.
    """
    confirmed_at = datetime.now(timezone.utc)
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    test_settings.yookassa_webhook_verify_ip = False

    with patch("app.services.payment_service.logger") as spy:
        response = await _post_succeeded_webhook(
            authed_client, "yoo_basic", _plan_limits_with_pro_priced(price)
        )

    assert response.status_code == 200, f"маршрут ответил {response.status_code}"

    rows = await _subscription_rows(db_session)
    moved = _aware(rows[0].expires_at)
    assert moved > add_one_month(add_one_month(confirmed_at)), (
        f"форма {form}: выразимая доля месяца обрезана до отката — заведён "
        "деловой потолок, которого D-29 не заводил, и сумма, во много раз "
        "превышающая цену, купила календарный месяц"
    )
    assert not _prorating_skips(spy), (
        f"форма {form}: пропорциональный срок ушёл на откат — граница проведена "
        "не по выразимости момента, а по правдоподобию величины"
    )


# =============================================================================
# ГЭП РАУНДА 9, ЭКЗЕМПЛЯР (а) — НЕПРИГОДНАЯ УПЛАЧЕННАЯ СУММА
#
# ПРЕДМЕТ РАЗДЕЛА. Ветка отказа уже ОБЪЯВЛЯЕТ «нечитаемую СУММУ» штатным,
# классифицированным и залогированным исходом: поле `unreadable="amount"`
# написано, ключ журнала написан, а комментарий над веткой говорит дословно
# «ОТКАТ К ПОЛНОМУ МЕСЯЦУ… и не исключение». Тело этого не делало: `Decimal`
# разбирает `NaN` и `Infinity` УСПЕШНО, `except` вокруг разбора их не видит, и
# отказ уезжал в `int(...)` внутри `prorated_days`, где ронял обработчик
# уведомления — HTTP 500, цикл повторов ЮKassa, вечный `pending` при списанных
# деньгах (T-05-104).
#
# НОВОЙ СЕМАНТИКИ ЗДЕСЬ НЕТ И НОВОГО ОБЪЯВЛЕНИЯ НЕ ЗАВОДИТСЯ. Ветка, в которую
# эти формы обязаны попадать, существует, объявлена и закреплена
# `test_the_refused_branch_names_its_own_stage_in_the_journal`; менялся только
# вход, который сегодня проходил мимо неё.
#
# МНОЖЕСТВО ФОРМ ВЫВЕДЕНО ИЗ СВОЙСТВА ВХОДА, А НЕ ПЕРЕПИСАНО ИЗ ЧУЖОГО ПРОГОНА.
# Класс «`Decimal` разбирает, арифметика не переживает» проект объявил живым для
# колонки `payments.amount_value` ещё планом 05-09 — константа
# `NON_FINITE_AMOUNTS` (`tests/test_pages/test_billing_section.py`), и она
# читается здесь, а не копируется пятый раз. Сверх неё взята форма
# `1e400` — ПЕРЕПОЛНЯЮЩИЙ ЛИТЕРАЛ, которого константа не несёт: он КОНЕЧЕН,
# поэтому классификацией конечности не отсеивается и уходит в соседний исход
# «срока не существует». Разные исходы у двух подмножеств названы таблицей, а не
# описаны прозой: испускание обязано быть разбираемо, а не просто существовать.
# =============================================================================

# Форма и ОЖИДАЕМОЕ значение поля `unreadable`. Пара, а не голый перечень:
# `1e400` конечен и потому попадает в исход `"span"`, а не `"amount"`, и слить
# два исхода в одно утверждение значило бы объявить их неразличимыми ровно там,
# где `IN-04` требует обратного.
UNUSABLE_AMOUNTS = tuple(
    (value, UNREADABLE_AMOUNT) for value in NON_FINITE_AMOUNTS
) + (("1e400", UNREADABLE_SPAN),)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("amount", "expected_unreadable"),
    UNUSABLE_AMOUNTS,
    ids=[value for value, _ in UNUSABLE_AMOUNTS],
)
async def test_an_unusable_amount_does_not_five_hundred_the_notification(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    test_settings: Settings,
    amount: str,
    expected_unreadable: str,
):
    """Непригодная уплаченная сумма НЕ даёт 500 на маршруте уведомления.

    Посев — тот же, что у `test_the_refused_branch_names_its_own_stage_in_the_journal`:
    живая `pro` плюс отвергнутый ПО ПРАВИЛУ `basic` (`switch_authorized=None`), а
    не через значение `False`, которое проект сам объявил недостижимым через
    форму. Прейскурант НЕ подменяется: предмет — сумма, а не цена.

    До правки формы давали пятисотку тремя разными исключениями: `NaN` —
    `ValueError`, `Infinity` и `-Infinity` — `OverflowError`, `sNaN` —
    `InvalidOperation`, `1e400` — `OverflowError` из `timedelta`.
    """
    confirmed_at = datetime.now(timezone.utc)
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount=amount
    )

    test_settings.yookassa_webhook_verify_ip = False

    with patch("app.services.payment_service.logger") as spy:
        response = await _post_succeeded_webhook(authed_client, "yoo_basic")

    assert response.status_code == 200, (
        f"сумма {amount!r}: маршрут ответил {response.status_code}. 500 — "
        "исключение на денежном пути там, где соседний комментарий обещает "
        "«откат к полному месяцу… и не исключение»: деньги списаны, ЮKassa "
        "будет повторять уведомление бесконечно"
    )

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_basic")
        )
    ).scalar_one()
    assert payment.status == "succeeded", (
        f"сумма {amount!r}: платёж остался в статусе {payment.status!r}"
    )

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "отвергнутый младший тариф всё-таки применён"
    moved = _aware(rows[0].expires_at)
    assert moved > current, "срок не сдвинулся — деньги не превратились в дни"
    assert moved <= add_one_month(add_one_month(confirmed_at)), (
        f"сумма {amount!r}: записан срок {moved.date()} — откат к полному "
        "календарному месяцу не сработал"
    )

    skips = _prorating_skips(spy)
    assert len(skips) == 1, f"сумма {amount!r}: следа в журнале ровно один не вышло"
    assert skips[0].kwargs.get("unreadable") == expected_unreadable, (
        f"сумма {amount!r}: журнал назвал исход "
        f"{skips[0].kwargs.get('unreadable')!r} вместо {expected_unreadable!r} — "
        "разбирающий обращение не сможет сказать, что именно оказалось "
        "непригодным"
    )
    assert skips[0].kwargs.get("stage") == STAGE_PRORATE_REFUSED

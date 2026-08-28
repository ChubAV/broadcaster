"""Закрытое множество состояний отказа ЕДИНСТВЕННОЙ формы оплаты (U1, U2, U3).

Предмет файла — ОТВЕТ РАЗДЕЛА НА НЕУДАВШУЮСЯ ОПЛАТУ. До плана 05-10 его не было
вовсе: `create_payment` звался без обёртки, поэтому отказ API ЮKassa выходил
необработанной пятисоткой, а все ветки гардов возвращали голый редирект на
`/billing` — то есть человек, нажавший «Оплатить», получал ту же самую страницу
без единого слова и следующим действием нажимал ещё раз.

⚠️ ФАЙЛ ПОХУДЕЛ ВТРОЕ ПЛАНОМ 05.1-07, И УБЫЛЬ — СНЯТИЕ ПРЕДМЕТА, А НЕ ПОКРЫТИЯ.
Больше двух третей его тестов проверяли МАТРИЦУ ТАРИФОВ: семантику `upgrade-only`,
записанное разрешение сделки, долю месяца отвергнутого перехода, конверсию
оплаченного остатка по отношению цен и верхнюю границу предоплаченного горизонта.
Тарифов Free/Basic/Pro не существует (D-A, D-D, D-F), переходить некуда, делить
уплаченную сумму не на что — и тест, переписанный «чтобы был», утверждал бы о
коде, которого нет. Что снятые имена не вернутся в приложение, держит
`tests/test_application/test_no_metering_remains.py`; что подтверждённый платёж
двигает ровно срок — `tests/test_services/test_payment_service.py`.

ЧТО ЗДЕСЬ ПРОВЕРЯЕТСЯ И ЧЕГО НЕТ.

- Здесь: что КАЖДАЯ ветка отказа несёт свою причину, что причина приезжает из
  ЗАКРЫТОГО множества, а не из адресной строки, что отказ создания платежа не
  оставляет строки в `payments`, и что признак живости срока снимается ДО сдвига
  даты.
- Не здесь: сборка раздела (`test_billing_section.py`), сквозная линия подписки
  (`test_billing_subscription.py`), сам сервис платежей
  (`test_services/test_payment_service.py`).

ПОЧЕМУ МНОЖЕСТВО ПРИЧИН ЗАКРЫТО (T-05-46). В разметку уходит строка ИЗ
ЗАКРЫТОГО РЕЕСТРА `app/pages/notices.py`, а не значение параметра запроса.
Владелец ссылки может подставить в адрес что угодно — на экран это не попадёт
ни значением, ни атрибутом, потому что подставлять нечего: вход в разметку не
связан со входом из адреса.

⚠️ ВЛАДЕЛЕЦ СЛОВ СМЕНИЛСЯ ПЛАНОМ 08-06, ГРАНИЦА ФАЙЛА — НЕТ. Прежде тот же
довод держало ЧАСТНОЕ отображение раздела, и таких частных отображений в
продукте было три: этот файл проверял одно из них. Три копии одного правила
расходились бы при первой правке любой из них, поэтому копий не осталось: слова
принадлежат одному реестру, а рисует их одна область шелла. Предмет ЭТОГО файла
не изменился — он по-прежнему про ответ раздела на неудавшуюся оплату.

ПОЧЕМУ ТЕКСТ ЧУЖОГО ИСКЛЮЧЕНИЯ НЕ ПОКАЗЫВАЕТСЯ (T-05-47). Прецедент R-03-09
Фазы 3 — раскрытие текста стороннего исключения в плашке — принят владельцем
риском severity medium. Повторять его на ДЕНЕЖНОМ пути не следует: текст SDK
уходит в журнал, на экран — фиксированная строка.
"""
import ast
import inspect
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.pages import notices
from app.services.payment_service import handle_webhook

BILLING_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "billing.py"

SAME_ORIGIN = {"Origin": "http://test"}
CROSS_SITE = {"Origin": "https://evil.example"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"

# Текст «стороннего исключения». Строка нарочно узнаваемая: она не встречается
# ни в одном шаблоне проекта, поэтому её появление в разметке однозначно значит
# «текст чужого исключения вышел на экран», а не совпадение со словом верстки.
SDK_FAILURE_TEXT = "yookassa_sdk_internal_boom_do_not_render_me"

# Строки закрытого множества. Выписаны здесь ДОСЛОВНО, потому что предмет
# проверки — что человек читает названную причину, а не что обработчик положил в
# контекст непустое значение.
MSG_PAYMENT = "Не удалось начать оплату — попробуйте ещё раз через минуту"
MSG_DISABLED = "Оплата сейчас недоступна — обратитесь к администратору"
# ⚠️ ДВЕ СТРОКИ СНЯТЫ ПЛАНОМ 05.1-07 ВМЕСТЕ СО СВОИМИ ВЕТКАМИ, И ЭТО ПАРА, А НЕ
# ЧИСТКА. Отказ «этот тариф больше не предлагается» и отказ «перейти на младший
# тариф можно после окончания срока» описывали выбор из трёх тарифов и переход
# между ними; ни того, ни другого в продукте нет. Держать половину пары нельзя в
# обе стороны: строка без обработчика недостижима и рано или поздно читается как
# живая, обработчик без строки возвращает голый редирект.
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

# Признак нарисованной плашки отказа. Проверяется ИМЕННО он, а не наличие слова
# из текста: слово может прийти из соседнего блока экрана, класс плашки — только
# из отрисованной плашки.
#
# ⚠️ ПРИЗНАК ПЕРЕЦЕЛЕН ВМЕСТЕ С МЕСТОМ ОТРИСОВКИ. Прежним признаком была
# СОБСТВЕННАЯ обёртка раздела (`data-payment-error`); её больше нет — исход
# рисует общая область уведомления шелла общим макросом.
ALERT_MARKER = 'class="alert alert--error"'

# Якоря двух областей уведомления шелла (includes/notice_area.html).
POLITE_AREA = 'id="notice"'
ASSERTIVE_AREA = 'id="notice-alert"'


def _notice_areas(html: str) -> str:
    """Содержимое ОБЕИХ областей уведомления шелла — и ничего кроме него.

    ⚠️ ИЗВЛЕЧЕНИЕ, А НЕ ПОИСК ПО ВСЕЙ СТРАНИЦЕ, И ЭТО НЕ ПЕДАНТИЗМ. Шелл
    доставляет в КАЖДЫЙ документ две СКРЫТЫЕ заготовки плашки отказа сервера и
    обрыва связи (includes/htmx_error_banner.html), и класс настойчивого
    варианта присутствует в них ВСЕГДА. Проверка по всей странице поэтому
    зеленела бы на пустом экране — то есть утверждала бы не то, что человеку
    что-то сказано, а то, что шелл собран.

    Границы области считаются по вложенности `div`, а не по первому `</div>`:
    плашка внутри области сама является элементом, и наивный поиск обрезал бы
    содержимое ровно по её закрытию.
    """
    parts = []
    for anchor in (POLITE_AREA, ASSERTIVE_AREA):
        start = html.index(anchor)
        cursor = html.index(">", start) + 1
        depth, scan = 1, cursor
        while depth:
            nxt_open = html.find("<div", scan)
            nxt_close = html.find("</div>", scan)
            assert nxt_close != -1, f"область {anchor} не закрыта"
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                scan = nxt_open + 4
            else:
                depth -= 1
                scan = nxt_close + 6
        parts.append(html[cursor : scan - 6])
    return "\n".join(parts)


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
    *,
    failing: bool = False,
    headers=None,
    payment_id: str = "yoo_1",
):
    """POST формы оплаты — БЕЗ ЕДИНОГО ПОЛЯ.

    ⚠️ ПАРАМЕТР ТАРИФА СНЯТ ЗДЕСЬ ПОТОМУ, ЧТО ЕГО НЕТ У ФОРМЫ, А НЕ РАДИ КРАТКОСТИ
    (T-05.1-06). Обработчик читает цену из настроек СЕРВЕРА, и покупателю нечего
    подменить. Помощник, продолжавший бы слать поле, которого обработчик не
    читает, описывал бы поверхность подмены, схлопнутую до нуля, как живую.
    """
    return await _post(
        client,
        "/billing/subscribe",
        {},
        failing=failing,
        headers=headers,
        payment_id=payment_id,
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
    assert response.headers["location"] == f"/billing?notice={notices.PAYMENT_FAILED}"


@pytest.mark.asyncio
async def test_a_failed_subscription_payment_leaves_its_reserve_expired(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отказ SDK оставляет резерв ПОГАШЕННЫМ — ровно одной строкой `expired`.

    ⚠️ ПОРЯДОК У ПОДПИСКИ СМЕНИЛСЯ, И ЭТОТ ТЕСТ ПЕРЕЦЕЛЕН ВМЕСТЕ С НИМ (D-05).
    Прежде он звался `test_a_failed_payment_leaves_no_row_in_the_journal` и
    утверждал, что после отказа ЮKassa строки не остаётся — свойство порядка
    «сначала SDK, потом запись в БД» (T-05-49). У подписочного платежа порядок
    теперь ОБРАТНЫЙ: строка-намерение резервируется ДО обращения к ЮKassa, иначе
    отказ ограничения схемы приходил бы проигравшему гонку уже ПОСЛЕ создания
    платежа у ЮKassa — записать его было бы некуда.

    Опасность при этом не исчезла, а ПОМЕНЯЛА СТОРОНУ, и утверждение следует за
    ней: локальная строка без удалённого платежа восстановима — она гасится в
    `expired`, остаётся следом попытки и остаётся ОПЛАЧИВАЕМОЙ; удалённый платёж
    без локальной строки не восстановим ничем. Поэтому проверяется не отсутствие
    строки, а её ПОГАШЕНИЕ: одна строка, статус `expired`, идентификатор платежа
    пуст (его неоткуда взять — ЮKassa платежа не создала).

    ⚠️ ПАКЕТНАЯ ПОЛОВИНА ПРЕЖНЕГО УТВЕРЖДЕНИЯ НЕ ПОТЕРЯНА, А ПЕРЕЕХАЛА НА
    УРОВЕНЬ СЕРВИСА — `tests/test_services/test_payment_intent_cap.py::
    test_a_failed_package_payment_leaves_no_row_in_the_journal`. У пакета порядок
    «сеть → запись» СОХРАНЁН, и свидетель ему нужен по-прежнему; написать его
    здесь не из чего: платёжный вход у раздела остался ОДИН — валюта сообщений
    снята целиком, и покупать пакет больше негде. Порядок принадлежит сервису, а
    не форме, и утверждение стало ближе к своему предмету.
    """
    await _subscribe(authed_client, failing=True)

    rows = list((await db_session.execute(select(Payment))).scalars().all())
    assert len(rows) == 1, f"резерв не сохранился либо продублирован: {len(rows)} строк"
    assert rows[0].status == "expired", (
        f"резерв остался в статусе {rows[0].status!r}: `pending` запер бы человека "
        "потолком за платёж, которого ЮKassa не создала"
    )
    assert rows[0].yookassa_payment_id is None, (
        "у строки появился идентификатор платежа, которого ЮKassa не создавала"
    )


@pytest.mark.asyncio
async def test_the_third_party_exception_text_never_reaches_the_screen(
    authed_client: AsyncClient,
):
    """T-05-47: текст исключения SDK уходит в журнал и НИКОГДА на экран.

    Проверяется вся линия: и заголовок перенаправления, и страница, на которую
    оно привело.
    """
    response = await _subscribe(authed_client, failing=True)

    assert SDK_FAILURE_TEXT not in response.text
    landing = await authed_client.get(response.headers["location"])
    assert response.headers["location"] == f"/billing?notice={notices.PAYMENT_FAILED}"
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
    assert response.headers["location"] == f"/billing?notice={notices.PAYMENT_DISABLED}"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_a_cross_site_post_is_refused_without_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужому источнику причина отказа НЕ сообщается.

    Порядок проверок не меняется: сначала кто пришёл, потом откуда, потом что
    просит. 403 без тела и без перенаправления — межсайтовый запрос не имеет
    права узнать даже, включены ли платежи.

    ⚠️ ВТОРОЙ АДРЕС СНЯТ ВМЕСТЕ СО ВТОРЫМ ПЛАТЁЖНЫМ ВХОДОМ, А ГРАНИЦА ОСТАЛАСЬ
    ТОЙ ЖЕ И НЕ ОСЛАБЛА: у раздела остался ровно один вход, принимающий деньги,
    и именно он обязан отвечать 403 без слов.
    """
    response = await _post(
        authed_client,
        "/billing/subscribe",
        {},
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
        (notices.PAYMENT_FAILED, MSG_PAYMENT),
        (notices.PAYMENT_DISABLED, MSG_DISABLED),
    ],
)
async def test_a_known_reason_code_prints_its_own_words(
    authed_client: AsyncClient, code: str, message: str
):
    response = await authed_client.get(f"/billing?notice={code}")

    assert response.status_code == 200
    areas = _notice_areas(response.text)
    assert ALERT_MARKER in areas, "плашки отказа в области уведомления нет"
    assert message in areas


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code",
    ["zzz_unknown_reason", "<script>alert(1)</script>", "payment_failedd", "PAYMENT_FAILED"],
)
async def test_an_unknown_reason_code_prints_nothing_at_all(
    authed_client: AsyncClient, code: str
):
    """Подставить произвольный текст через адрес невозможно (T-05-46).

    Проверяется НЕ экранирование, а недостижимость: в разметку уходит строка из
    ЗАКРЫТОГО РЕЕСТРА, поэтому значение параметра не попадает на экран ни
    значением, ни атрибутом.

    ⚠️ РАДИУС ЭТОГО СВОЙСТВА ВЫРОС ПЛАНОМ 08-06, И ИМЕННО ПОЭТОМУ ОНО ВАЖНЕЕ
    ПРЕЖНЕГО. Параметр рисует плашку теперь НА КАЖДОЙ странице обоих шеллов, а
    не на пяти экранах: сравнение ЦЕЛИКОМ по закрытому множеству и есть то
    единственное, что не даёт владельцу ссылки написать человеку сообщение от
    имени приложения где угодно (T-08-08).
    """
    response = await authed_client.get(f"/billing?notice={code}")

    assert response.status_code == 200
    assert ALERT_MARKER not in _notice_areas(response.text), (
        "неизвестный код нарисовал плашку"
    )
    assert code not in response.text, "значение параметра напечатано на экране"


@pytest.mark.asyncio
async def test_the_pending_reason_prints_its_own_words(authed_client: AsyncClient):
    """Попавший под потолок получает СЛОВА, а не молчаливый редирект.

    Отдельным именем, а не строкой в перечне соседа, потому что предмет у него
    свой: связь нового кода с его строкой — последнее звено цепи «отказ сервиса
    → код причины → отображение → плашка», и разрыв ЛЮБОГО звена даёт ту самую
    возвращённую без слов страницу, которую фаза закрывала планом 05-10.
    """
    response = await authed_client.get(f"/billing?notice={notices.PAYMENT_PENDING}")

    assert response.status_code == 200
    areas = _notice_areas(response.text)
    assert ALERT_MARKER in areas, "плашки отказа в области уведомления нет"
    assert MSG_PENDING in areas


@pytest.mark.asyncio
async def test_the_section_without_the_parameter_prints_no_alert(
    authed_client: AsyncClient,
):
    """Парный тест: без него предыдущие зеленели бы на разметке без плашки.

    ⚠️ ОБЛАСТЬ УВЕДОМЛЕНИЯ ПРИ ЭТОМ СУЩЕСТВУЕТ ВСЕГДА, ДАЖЕ ПУСТАЯ, И ЭТО НЕ
    ПРОТИВОРЕЧИЕ. Правило «нет кода — нет плашки» относится к ПЛАШКЕ: узел
    области стабилен, потому что внеполосная подмена целится в него по
    идентификатору. Проверяется поэтому пустота области, а не отсутствие узла.
    """
    response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert ALERT_MARKER not in _notice_areas(response.text)


# ⚠️ `test_the_alert_stands_before_the_current_plan_block` СНЯТ ОТСЮДА, А ЕГО
# ГРАНИЦА — НЕТ. Он утверждал, что плашка причины стоит ВЫШЕ блока текущего
# тарифа; блока не существует с плана 05.1-05, и якорь «Текущий тариф» перестал
# встречаться в разметке. Утверждение ПЕРЕЕХАЛО вместе с якорем в
# `tests/test_pages/test_billing_section.py::test_the_notice_stands_before_the_access_panel`,
# где новым якорем служит панель доступа, а сам переезд назван в его докстринге.
# Вторая копия одного свойства здесь разошлась бы с первой при первой же правке
# разметки — поэтому строка снята, а не перенацелена.


def test_the_reason_codes_of_the_handlers_are_exactly_the_known_set():
    """Ни одного кода в редиректе мимо РЕЕСТРА — и ни одного лишнего.

    ⚠️ ГЕЙТ ПЕРЕЦЕЛЕН ВМЕСТЕ С ВЛАДЕЛЬЦЕМ СЛОВ, А НЕ ОСЛАБЛЕН. Прежде он держал
    связь литерала редиректа с ЧАСТНЫМ отображением раздела; частного
    отображения больше нет — слова принадлежат закрытому реестру
    (`app/pages/notices.py`), общему на весь продукт. Утверждение осталось тем
    же: расхождение того, что раздел ПИШЕТ, с тем, по чему есть что нарисовать,
    даёт молчаливый редирект без слов — ровно тот дефект, ради которого гейт и
    заведён.

    ⚠️ КОДЫ БОЛЬШЕ НЕ ЛИТЕРАЛЫ, И ЭТО УСИЛЕНИЕ. Опечатка в литерале не падала
    ничем и давала кнопку, вернувшую ту же страницу без единого слова; опечатка
    в имени константы падает на импорте модуля. Поэтому обход собирает ИМЕНА
    констант реестра, использованные в адресах раздела.
    """
    source = BILLING_PY.read_text(encoding="utf-8")
    used = set(re.findall(r"/billing\?notice=\{notices\.([A-Z_]+)\}", source))

    assert used == {
        "PAYMENT_FAILED",
        "PAYMENT_DISABLED",
        # ⚠️ ВЕТОК БЫЛО ПЯТЬ, СТАЛО ТРИ. Две сняты планом 05.1-07 ВМЕСТЕ СО
        # СВОИМИ ГАРДАМИ: тарифов нет, выбирать не из чего, переходить некуда.
        # Множество здесь сужалось ТЕМ ЖЕ коммитом, что снял ветки, — иначе
        # регрессия краснела бы по причине, к предмету правки отношения не
        # имеющей.
        # Потолок одновременных подписочных намерений (план 05-17). Код обязан
        # войти в ОБА места сразу — в адрес редиректа и в реестр, — иначе эта
        # регрессия краснеет. Правка её множества и есть часть работы, а не
        # побочный эффект: тест держит связь, которую иначе держала бы только
        # аккуратность автора.
        "PAYMENT_PENDING",
    }, used
    for name in used:
        code = getattr(notices, name)
        assert notices.notice_for(code) is not None, (
            f"раздел пишет код {code!r}, которого нет в реестре: человек "
            "получил бы ту же страницу без единого слова"
        )
    assert notices.notice_for("zzz") is None
    assert notices.notice_for(None) is None


def test_the_get_handler_still_contains_no_write_path():
    """Параметр запроса ничего не меняет — только показывает (D-05)."""
    source = BILLING_PY.read_text(encoding="utf-8")
    rest = source[source.index("async def billing_page(") :]
    body = rest[: rest.find("\n@router")]

    assert not re.search(r"\b(db|session)\.(add|commit|flush)\(", body)


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


def _app_settings() -> Settings:
    """Настоящие `Settings` с УМОЛЧАНИЯМИ конфига, а не MagicMock.

    ⚠️ ПАРАМЕТР ПЕРЕЧНЯ ТАРИФОВ СНЯТ ПЛАНОМ 05.1-07 ВМЕСТЕ С САМИМ ПЕРЕЧНЕМ.
    Прежде помощник умел подменить прейскурант, потому что денежный путь читал из
    него цену действующего плана; поля `plan_limits` в настройках больше нет
    вовсе, и передача его в `Settings(...)` была бы отвергнута валидацией.
    Помощник остался ровно затем, зачем нужен и сейчас: `Settings()` в суите не
    строится — боевого `.env` здесь нет, — а MagicMock подсунул бы вместо цены
    доступа объект, на котором ветка отказа зеленела бы по неверной причине.

    Два обязательных поля задаются теми же значениями, что в `tests/conftest.py`.
    """
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
    )


async def _confirm(db: AsyncSession, payment_id: str = "yoo_1") -> bool:
    """Подтверждённое уведомление ЮKassa по конкретному платежу.

    ПОДМЕНА ЖИВЁТ ВНУТРИ `with` И НЕ ПЕРЕЖИВАЕТ ВЫЗОВА: настройки — глобальное
    для денежного пути состояние, и утечка их на соседний тест сменила бы цену
    там, где предмет проверки другой (T-05-143).
    """
    with patch(
        "app.services.payment_service.get_settings",
        return_value=_app_settings(),
    ):
        return await handle_webhook(
            db,
            event="payment.succeeded",
            payment_data={"object": {"id": payment_id}},
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
        subscription.expires_at = next_expiry(subscription.expires_at, now)
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
    уровня, а сдвиги в ветвях оставались вне инварианта.

    ⚠️ КОНТРОЛЬ ОСТАЁТСЯ НУЖНЫМ, ХОТЯ ВЕТВЕЙ В `_apply_extension` СЕГОДНЯ НЕТ.
    План 05.1-07 снял их вместе с матрицей тарифов, но обход `ast.walk` заведён
    не ради вчерашних ветвей: следующая ветка появится раньше, чем кто-нибудь
    вспомнит, что перебор верхнего уровня её не увидит. Синтетический исходник
    поэтому и синтетический — он переживает любую форму настоящего тела.
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

    # ⚠️ ПОРОГ ПОНИЖЕН С ТРЁХ ДО ОДНОГО ПЛАНОМ 05.1-07 ВМЕСТЕ С ЧИСЛОМ ВЕТВЕЙ, И
    # ЭТО НЕ ОСЛАБЛЕНИЕ ИНВАРИАНТА. Зубы держит `_order_violations` выше: он
    # обходит `ast.walk` ВСЁ тело и краснеет на КАЖДОМ сдвиге, поставленном выше
    # снятия признака, — сколько бы их ни было. Эта проверка не про порядок, а
    # против ВАКУУМА: она утверждает, что сдвиг вообще существует, иначе
    # предыдущее утверждение зеленело бы на функции, срок не двигающей вовсе.
    # Троек больше нет, потому что нет трёх ветвей: доля месяца отвергнутого
    # перехода, откат к полному месяцу и конверсия остатка сняты вместе с
    # матрицей тарифов, и остался ОДИН сдвиг.
    moves = _expiry_assignment_lines(source, attr="expires_at")
    assert len(moves) >= 1, (
        "срок не двигается присваиванием в поле подписки ни разу — инвариант "
        f"порядка держать не над чем ({moves})"
    )

    sampled = _liveness_sample(source, "subscription_is_live").value.args[0]
    assert isinstance(sampled, ast.Attribute) and sampled.attr == "expires_at", (
        "признак снимается НЕ от той величины, которую перезаписывает "
        "`next_expiry`: порядок соблюдён, а правило решает по чужому полю "
        f"({ast.dump(sampled)})"
    )


def test_the_extension_semantics_are_named_in_the_place_that_moves_the_date():
    """Правило записано ТАМ, ГДЕ двигается срок, а не только в документах фазы.

    Читатель `_extend_subscription` — тот самый человек, который завтра будет
    решать, можно ли поменять здесь порядок двух строк. До плана 05-13 докстринг
    молчал о том, чем кончается подтверждённый платёж, и молчание стоило фазе
    трёх раундов верификации подряд.

    ⚠️ ПРЕДМЕТ ТЕСТА ПЕРЕНАЦЕЛЕН ПЛАНОМ 05.1-07, А НЕ ОСЛАБЛЕН, И ПРЕЖНИЙ НАЗВАН.
    Он требовал, чтобы докстринг называл семантику `upgrade-only`, прохибицию
    05-01, ключ сохранённого тарифа и записанное разрешение сделки. Ни одного из
    четырёх предметов в коде не осталось: тарифов нет, переходить некуда, план
    здесь не решается вовсе. Граница, однако, ТА ЖЕ — «правило живёт там, где
    двигается срок», — и сегодня правил ровно два: отсчёт от позднейшей из двух
    точек и порядок снятия признака живости. Оба обязаны быть НАЗВАНЫ здесь.

    НАЗВАТЬ МАЛО — ИМЯ ОБЯЗАНО СОВПАДАТЬ С КОДОМ. Каждая подстрока ниже
    существует только вместе с абзацем, который объясняет исполняемое поведение,
    и вычёркивание абзаца краснит этот тест, а не проходит незамеченным.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "services"
        / "payment_service.py"
    ).read_text(encoding="utf-8")
    body = source[source.index("async def _extend_subscription(") :]
    docstring = body[: body.index('"""', body.index('"""') + 3)]

    assert "subscription_is_live" in docstring, (
        "докстринг не называет, ЧЕМ считается признак живости и где он объявлен"
    )
    assert "test_the_liveness_is_sampled_before_the_date_moves" in docstring, (
        "докстринг не называет исполняемого сторожа порядка — читатель решит, "
        "что порядок двух операторов держится вниманием автора"
    )
    # Подстрока «истёк» существует только вместе с абзацем об исходе на ИСТЁКШЕМ
    # сроке — том самом, о котором докстринг молчал, пока код брал деньги за
    # невыдаваемый тариф (гэп 1 раунда 3). Предмет абзаца сменился (сегодня это
    # точка отсчёта, а не выдача тарифа), граница — нет.
    assert "истёк" in docstring.lower(), (
        "докстринг молчит об исходе на ИСТЁКШЕМ сроке — стадии, где деньги уже "
        "ушли, а срок мог остаться в прошлом"
    )
    assert "countdown_base" in docstring, (
        "докстринг не называет ЕДИНСТВЕННОГО объявления правила отсчёта D-04 — "
        "то есть не говорит читателю, где эта арифметика живёт"
    )
    assert "D-04" in docstring, (
        "правило отсчёта не связано с решением, которым оно принято"
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
# ФОРМА — «НЕ БОЛЕЕ ОДНОГО НЕЗАКРЫТОГО ПОДПИСОЧНОГО НАМЕРЕНИЯ» (решение
# владельца D-I, фаза 05.1). Прежняя форма `cap-different-plan` отбирала
# намерения по несовпадению тарифа и в плоской модели выродилась бы МОЛЧА:
# тарифа у платежа нет, сравнение ложно всегда, защита не срабатывает и не
# краснеет. Повтор оплаты теперь отвергается — цена этого названа в докстринге
# `create_payment` и разменена на второй счёт за один и тот же месяц доступа.


@pytest.mark.asyncio
async def test_a_second_subscription_intent_from_the_form_is_refused_with_words(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Форма отвечает на потолок 302 с ПРИЧИНОЙ и не заводит второй строки.

    Голый редирект здесь был бы худшим из ответов: человек, нажавший «Оплатить»
    и получивший ту же страницу, читает это как поломку и нажимает снова —
    ровно то поведение, которое потолок и ловит.

    ⚠️ ИСТОЧНИК ОТКАЗА СМЕНИЛСЯ, АДРЕС И СЛОВА — НЕТ (план 08-05, D-06). Отказ
    принимает теперь СУБД — частичный уникальный индекс
    `uq_payments_open_subscription_intent`, — а сервис переводит его в свой тип
    `PendingIntentCapError`. Ветка обработчика различает отказ ПО ТИПУ и этим
    планом не правится вовсе, поэтому UI-контракт остался тем же: тот же код
    причины, тот же адрес, те же слова. Внутренности СУБД до экрана не доходят —
    текст исключения ФИКСИРОВАН и не несёт ни имени ограничения, ни цифр.
    """
    first = await _subscribe(authed_client, payment_id="yoo_first")
    assert first.status_code == 302
    assert first.headers["location"] == CONFIRMATION_URL

    second = await _subscribe(authed_client, payment_id="yoo_second")

    assert second.status_code == 302
    assert second.headers["location"] == f"/billing?notice={notices.PAYMENT_PENDING}", (
        "второе намерение ушло на оплату либо вернулось без слов"
    )
    assert await _payments_count(db_session) == 1, "заведена вторая строка платежа"


@pytest.mark.asyncio
async def test_a_second_intent_is_refused_while_the_first_is_fresh(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пока первое намерение СВЕЖЕЕ, второго не появится — и срок не сдвинется дважды.

    ⚠️ ЧЕГО ЭТОТ ТЕСТ НЕ ДЕРЖИТ. Оба намерения он заводит ПОДРЯД, о сроке
    давности не знает вовсе, и потому доказывает ровно одно: пока первое
    намерение свежее, второго не появится. Состояние «два оплачиваемых
    намерения» недостижимым он НЕ объявляет — оно достижимо через сутки, и это
    доказывает
    `tests/test_services/test_payment_service.py::test_a_stale_intent_does_not_block_a_new_one`.
    Имя, обещающее инвариант шире тела, давало бы читателю ложную уверенность
    (WR-05 раунда 5).

    ⚠️ ПОСЛЕДНИЕ ДВА УТВЕРЖДЕНИЯ — ГЛАВНЫЕ, И ОНИ О ДЕНЬГАХ, А НЕ О СТРОКАХ.
    Срок обязан уехать вперёд РОВНО НА ОДИН месяц: сдвиг на два означал бы, что
    второе намерение всё-таки существует и было подтверждено, то есть человек
    заплатил дважды за один и тот же доступ.

    ⚠️ ОТКАЗ ПРИНИМАЕТ ТЕПЕРЬ СУБД, А НЕ ПРОВЕРКА В КОДЕ (план 08-05). Предмет
    и границы теста от этого не изменились ни на букву; изменилось то, что между
    проверкой и записью больше нет зазора ВОВСЕ — они стали одним оператором
    вставки, и обойти их порядком запросов нельзя.
    """
    await _subscribe(authed_client, payment_id="yoo_first")
    refused = await _subscribe(authed_client, payment_id="yoo_second")
    assert refused.headers["location"] == f"/billing?notice={notices.PAYMENT_PENDING}"
    assert await _payments_count(db_session) == 1

    assert await _confirm(db_session, "yoo_first") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "заведена вторая подписка"
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=27), (
        "оплаченный месяц не выдан вовсе"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "срок сдвинут дважды — второй платёж всё-таки существует"
    )

"""ТРАНСПОРТ СТАРТА ПОДКЛЮЧЕНИЯ MAX (Фаза 11, план 11-18; FORM-03, FORM-08).

Последний обработчик фазы на слое ответа и второй авторский 422 вехи.

⚠️ МОСТ И ОЖИДАНИЕ ПОДМЕНЯЮТСЯ, А НЕ ОПЛАЧИВАЮТСЯ. Обработчик зовёт мост MAX и
ждёт пять секунд между стартом сессии и запросом QR. Мост в прогоне недоступен,
а пять секунд на каждый случай — цена, которую суита на хосте с ограниченной
памятью платить не должна. Подменяется ровно ожидание в пять секунд: прочие
вызовы `asyncio.sleep` (цикл событий, транспорт клиента) идут настоящим нулевым
ожиданием. Сами пять секунд из обработчика НЕ сняты — это утверждается
записанными задержками, а не обещанием.

⚠️ ЭХО ТЕЛЕФОНА ЗДЕСЬ НАСТОЯЩЕЕ, И БЕЗОПАСНОСТЬ ЕГО — ЭКРАНИРОВАНИЕ, А НЕ
НЕДОСТИЖИМОСТЬ (поколение Фазы 19, D-09). Номер телефона — свободный текст, и
ветка ошибки возвращает его в поле. Ветка достижима ЛЮБЫМ неверным вводом
(`abc`, слишком длинная строка, враждебная разметка): их разбирает
`normalize_manual`, а текст ошибки — константа `PhoneError` без введённого.
Экранирование канала эха доказывается и на сборке тела 422, и HTTP-путём до 422
(правило 4 ниже). Прежний текст абзаца — «до Фазы 19: ветка ошибки достижима
только значением из одних пробелов, поэтому враждебная разметка HTTP-путём до
422 не доезжает никогда; экранирование канала эха доказывается на ТОЙ ЖЕ
сборке тела, которой обработчик собирает фрагмент 422».
"""
import asyncio
import contextlib
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount
from app.services.phone import (
    PHONE_ERROR_BLANK,
    PHONE_ERROR_MESSAGES,
    PHONE_ERROR_NOT_A_NUMBER,
    PHONE_ERROR_TOO_LONG,
)
from tests.test_pages.test_confirm_delete_transport import DOCUMENT_MARK, HTMX_HEADERS

START_URL = "/accounts/connect/max/start"
STEP_TARGET = 'hx-target="#max-connect-step"'
CONNECT_ERROR = "Ошибка подключения к MAX"
QR_LINK = "https://max.example/qr/login"
HANDSHAKE_WAIT = 5

# Враждебное значение: закрытие атрибута, внедрение тега и атрибут события.
HOSTILE_PHONE = '"><script>alert(1)</script><x " onfocus="alert(2)" autofocus="'
HOSTILE_RAW_MARKS = ("<script>alert(1)</script>", '" onfocus="alert(2)"')
HOSTILE_ESCAPED_MARK = "&lt;script&gt;alert(1)&lt;/script&gt;"

_real_sleep = asyncio.sleep


@contextlib.contextmanager
def max_bridge(*, start_session=None, get_qr=None):
    """Подмена моста MAX и пятисекундного ожидания; отдаёт записанные задержки."""
    delays: list[float] = []

    async def _sleep(delay, *args, **kwargs):
        delays.append(delay)
        if delay == HANDSHAKE_WAIT:
            return None
        return await _real_sleep(delay, *args, **kwargs)

    with patch("app.pages.accounts.MaxMessenger") as messenger, patch(
        "asyncio.sleep", new=_sleep
    ):
        instance = messenger.return_value
        instance.start_session = start_session or AsyncMock(return_value={"status": "ok"})
        instance.get_qr = get_qr or AsyncMock(return_value={"qr": QR_LINK})
        yield delays


async def _max_accounts(db: AsyncSession) -> list[MessengerAccount]:
    result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.type == "max")
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_max_start_over_htmx_returns_the_step_container(
    authed_client: AsyncClient,
):
    """Старт на htmx — 200 и содержимое контейнера шага мастера (FORM-03, D-02).

    Ответ подменяет СОДЕРЖИМОЕ `#max-connect-step`, поэтому целого документа в
    нём быть не должно, а узел опроса статуса — обязан: без него QR виден, но
    подключение никогда не завершается (завершает его только опрос).
    """
    with max_bridge() as delays:
        response = await authed_client.post(
            START_URL,
            data={"phone": "+79990001122"},
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert response.status_code == 200, (
        f"старт MAX на htmx ответил {response.status_code} вместо 200"
    )
    body = response.text
    assert DOCUMENT_MARK not in body, (
        "слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ: подмена содержимого шага вставила бы "
        "страницу внутрь страницы"
    )
    assert "<img" in body, "во фрагменте шага нет QR-кода"
    assert 'id="max-status"' in body and 'hx-get="/accounts/connect/max/status"' in body, (
        "во фрагменте нет узла опроса статуса — подключение не завершится никогда"
    )
    assert HANDSHAKE_WAIT in delays, (
        "обработчик больше не ждёт пять секунд между стартом сессии и запросом "
        "QR — ожидание мосту нужно, и снимать его план не вправе"
    )

    with max_bridge(start_session=AsyncMock(side_effect=RuntimeError("bridge offline"))):
        failed = await authed_client.post(
            START_URL,
            data={"phone": "+79990001122"},
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert failed.status_code == 200, (
        f"отказ моста на htmx ответил {failed.status_code} вместо 200"
    )
    assert CONNECT_ERROR in failed.text, "фрагмент отказа моста не несёт текста ошибки"
    assert DOCUMENT_MARK not in failed.text, "фрагмент отказа моста — целый документ"


@pytest.mark.asyncio
@pytest.mark.parametrize("typed", ["8 999 123 45 67", "+7 999 123-45-67"])
async def test_a_free_form_number_starts_the_session_with_the_normalized_value(
    authed_client: AsyncClient, db_session: AsyncSession, typed: str
):
    """Свободный ввод номера доходит до `credentials` и воркера как E.164 (D-09, D-10).

    Номер формы — ЗАПАСНЫЙ источник опроса статуса (план 19-07 читает его строгим
    нормализатором писателя, который отвергает даже плейсхолдер поля), поэтому
    сырой ввод в `credentials` лежать не может. Колонку `phone` старт не пишет:
    номер, записанный при POST, заблокировал бы номер, сообщённый самим MAX.
    """
    start_session = AsyncMock(return_value={"status": "ok"})
    with max_bridge(start_session=start_session):
        response = await authed_client.post(
            START_URL, data={"phone": typed}, headers=HTMX_HEADERS, follow_redirects=True
        )

    assert response.status_code == 200, (
        f"старт MAX со свободным вводом ответил {response.status_code} вместо 200"
    )
    assert "<img" in response.text, "после свободного ввода QR не открылся"

    accounts = await _max_accounts(db_session)
    assert len(accounts) == 1, f"ожидалась одна строка MAX, найдено {len(accounts)}"
    assert accounts[0].status == "connecting"
    assert accounts[0].credentials == "+79991234567", (
        "форма MAX положила в credentials ненормализованный номер"
    )
    assert accounts[0].phone is None, (
        "старт записал номер формы в колонку phone: он запас опроса, а не известный номер"
    )
    start_session.assert_awaited_once_with(phone="+79991234567")


@pytest.mark.asyncio
async def test_an_empty_phone_answers_422_with_the_echo_on_both_transports(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Телефон из пробелов — 422 на обоих транспортах с эхом в поле (FORM-08, D-06).

    ⚠️ ЦЕЛЬ ПОДМЕНЫ 422 РАВНА ЦЕЛИ УСПЕХА. Правило 422 блока конфигурации
    подменяет цель ЗАПРОСА, то есть `#max-connect-step` формы телефона; фрагмент
    ошибки поэтому обязан нести ту же форму с той же целью — иначе второй
    отправки после исправления номера не было бы куда приземлять. Реестр
    `HX-Retarget`/`HX-Reswap` остаётся пустым именно благодаря этому равенству.
    """
    blank = "   "

    with max_bridge():
        over_htmx = await authed_client.post(
            START_URL, data={"phone": blank}, headers=HTMX_HEADERS, follow_redirects=True
        )

    assert over_htmx.status_code == 422, (
        f"пустой телефон на htmx ответил {over_htmx.status_code} вместо 422"
    )
    assert PHONE_ERROR_BLANK in over_htmx.text, "во фрагменте нет текста ошибки"
    assert DOCUMENT_MARK not in over_htmx.text, (
        "слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ: правило 422 подменит им шаг мастера"
    )
    assert f'value="{blank}"' in over_htmx.text, (
        "введённое значение не вернулось в поле телефона"
    )
    assert STEP_TARGET in over_htmx.text, (
        "фрагмент ошибки несёт форму с другой целью подмены, чем форма успеха"
    )

    with max_bridge():
        without = await authed_client.post(
            START_URL, data={"phone": blank}, follow_redirects=False
        )

    assert without.status_code == 422, (
        f"путь без htmx ответил {without.status_code} вместо 422 — код обязан быть "
        "ОДНИМ на обоих транспортах"
    )
    assert DOCUMENT_MARK in without.text, (
        "человеку без JavaScript приехал фрагмент без шелла вместо страницы"
    )
    assert PHONE_ERROR_BLANK in without.text, "на странице нет текста ошибки"
    assert f'value="{blank}"' in without.text, (
        "введённое значение не вернулось в поле телефона на странице"
    )

    assert await _max_accounts(db_session) == [], (
        "ветка ошибки завела аккаунт — пустой телефон обязан остановить действие "
        "до записи"
    )


def test_the_phone_echo_is_autoescaped_in_the_step_markup():
    """Канал эха телефона — только автоэкранирование (T-11-31).

    Утверждение снимается со сборки, которой обработчик собирает тело 422: и
    потерянное экранирование, и попытка напечатать значение «как есть»
    краснеют здесь, хотя HTTP-путём враждебное значение до 422 не доезжает.
    """
    from app.pages import accounts

    _max_step_markup = getattr(accounts, "_max_step_markup", None)
    assert _max_step_markup is not None, (
        "у модуля аккаунтов нет сборки шага мастера MAX — тело 422 собирается "
        "не из включаемого шаблона, и канал эха доказывать не на чем"
    )
    markup = _max_step_markup(step="phone", error=PHONE_ERROR_BLANK, phone=HOSTILE_PHONE)

    for raw in HOSTILE_RAW_MARKS:
        assert raw not in markup, (
            f"присланное значение напечатано НЕЭКРАНИРОВАННЫМ: {raw!r}"
        )
    assert HOSTILE_ESCAPED_MARK in markup, (
        "экранированной формы значения в поле нет — эхо не доехало вовсе или "
        "доехало иначе, чем через автоэкранирование"
    )
    assert STEP_TARGET in markup, "шаг телефона потерял цель подмены формы"


@pytest.mark.asyncio
async def test_a_hostile_phone_never_reaches_the_response_raw(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Враждебное значение идёт веткой 422 с эхом — и в ответ не попадает сырым.

    ⚠️ ПОСЛЕ D-09 ВЕТКА ОШИБКИ ДОСТИЖИМА ВРАЖДЕБНЫМ ЗНАЧЕНИЕМ (Фаза 19). Раньше
    до неё доезжали только пробелы, и тест оставался зелёным по причине
    недостижимости; теперь значение возвращается в поле, а безопасность держит
    автоэкранирование макроса поля. Текст ошибки — константа `PhoneError`,
    введённого в нём нет.
    """
    start_session = AsyncMock(return_value={"status": "ok"})
    with max_bridge(start_session=start_session):
        response = await authed_client.post(
            START_URL,
            data={"phone": HOSTILE_PHONE},
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    assert response.status_code == 422, (
        f"враждебный номер ответил {response.status_code} вместо 422"
    )
    for raw in HOSTILE_RAW_MARKS:
        assert raw not in response.text, (
            f"присланный номер попал в ответ 422 НЕЭКРАНИРОВАННЫМ: {raw!r}"
        )
    assert HOSTILE_ESCAPED_MARK in response.text, (
        "экранированного эха враждебного значения в поле нет — канал эха не работает"
    )
    shown = [message for message in PHONE_ERROR_MESSAGES if message in response.text]
    assert shown, "в теле 422 нет ни одного текста PhoneError"
    assert response.text.count(HOSTILE_ESCAPED_MARK) == 1, (
        "введённое значение встречается в теле 422 не один раз (эхо в поле): "
        "его подставили в текст ошибки"
    )
    start_session.assert_not_awaited()
    assert await _max_accounts(db_session) == [], "враждебный номер завёл аккаунт"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("typed", "expected_error", "expected_echo"),
    [
        ("abc", PHONE_ERROR_NOT_A_NUMBER, 'value="abc"'),
        ("1" * 33, PHONE_ERROR_TOO_LONG, None),
    ],
)
async def test_an_invalid_number_answers_422_and_opens_no_qr(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    typed: str,
    expected_error: str,
    expected_echo: str | None,
):
    """Неверный номер — 422 на обоих транспортах, QR не открывается (D-09)."""
    start_session = AsyncMock(return_value={"status": "ok"})
    with max_bridge(start_session=start_session):
        over_htmx = await authed_client.post(
            START_URL, data={"phone": typed}, headers=HTMX_HEADERS, follow_redirects=True
        )
        without = await authed_client.post(
            START_URL, data={"phone": typed}, follow_redirects=False
        )

    assert over_htmx.status_code == 422, (
        f"неверный номер на htmx ответил {over_htmx.status_code} вместо 422"
    )
    assert without.status_code == 422, (
        f"неверный номер без htmx ответил {without.status_code} вместо 422"
    )
    assert expected_error in over_htmx.text, "во фрагменте нет текста PhoneError"
    assert expected_error in without.text, "на странице нет текста PhoneError"
    assert DOCUMENT_MARK not in over_htmx.text, "фрагмент 422 — целый документ"
    assert DOCUMENT_MARK in without.text, "без htmx приехал фрагмент вместо страницы мастера"
    if expected_echo is not None:
        assert expected_echo in over_htmx.text, "введённое значение не вернулось в поле"
        assert expected_echo in without.text, "введённое значение не вернулось на странице"
    for body in (over_htmx.text, without.text):
        assert "<img" not in body, "после неверного номера открылся QR"
    start_session.assert_not_awaited()
    assert await _max_accounts(db_session) == [], (
        "неверный номер завёл аккаунт: 422 обязан остановить действие до записи"
    )


HINT = "Покажем его в списке аккаунтов, если MAX не сообщит номер сам"


@pytest.mark.asyncio
async def test_the_phone_field_explains_why_the_number_is_asked(
    authed_client: AsyncClient,
):
    """Под полем номера — подсказка о запасном номере, без значения номера (D-10, D-12).

    Подсказка стоит на странице мастера и во фрагменте 422 (одна разметка шага).
    Она не повторяет пример написания — его несёт текст ошибки — и цифр не несёт.
    """
    page = await authed_client.get("/accounts/connect/max")
    with max_bridge():
        fragment = await authed_client.post(
            START_URL, data={"phone": "abc"}, headers=HTMX_HEADERS, follow_redirects=True
        )

    assert page.status_code == 200
    assert fragment.status_code == 422
    for where, body in (("странице мастера", page.text), ("фрагменте 422", fragment.text)):
        assert HINT in body, "под полем номера MAX нет подсказки о запасном номере"
        assert f'<span class="field__hint">{HINT}</span>' in body, (
            f"подсказка на {where} не стоит в узле подсказки поля"
        )
    assert not any(ch.isdigit() for ch in HINT), "в подсказке есть цифры"


@pytest.mark.asyncio
async def test_max_start_without_htmx_lands_on_the_accounts_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Без htmx успешный старт — 302 на `/accounts`, и заведённый аккаунт там виден.

    ⚠️ АДРЕС ВЫБРАН ИЗМЕРЕНИЕМ, А НЕ УДОБСТВОМ. Завершает подключение только
    опрос htmx, а GET шага мастера удаляет аккаунты в статусе подключения:
    приземление на мастер уничтожило бы только что заведённую запись.
    """
    with max_bridge():
        response = await authed_client.post(
            START_URL, data={"phone": "+79990001122"}, follow_redirects=False
        )

    assert response.status_code == 302, (
        f"путь без htmx ответил {response.status_code} вместо 302"
    )
    assert response.headers["location"] == "/accounts", (
        f"адрес деградации {response.headers['location']!r} вместо '/accounts'"
    )

    accounts = await _max_accounts(db_session)
    assert [a.status for a in accounts] == ["connecting"], (
        "после старта должен существовать ровно один аккаунт MAX в статусе "
        f"подключения, а найдено {[(a.id, a.status) for a in accounts]}"
    )

    landed = await authed_client.get("/accounts")
    assert landed.status_code == 200
    assert f'id="account-row-{accounts[0].id}"' in landed.text, (
        "на экране приземления заведённого аккаунта не видно"
    )
    assert [a.status for a in await _max_accounts(db_session)] == ["connecting"], (
        "приземление уничтожило заведённый аккаунт"
    )

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
НЕДОСТИЖИМОСТЬ. У профиля (план 11-09) присланное значение сравнивалось с
закрытым списком и в документ не попадало вовсе. Номер телефона — свободный
текст: на ветке ошибки он возвращается в поле. Ветка ошибки достижима только
значением из одних пробелов, поэтому враждебная разметка HTTP-путём до 422 не
доезжает никогда; экранирование канала эха доказывается на ТОЙ ЖЕ сборке тела,
которой обработчик собирает фрагмент 422, — отдельным правилом ниже.
"""
import asyncio
import contextlib
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount
from tests.test_pages.test_confirm_delete_transport import DOCUMENT_MARK, HTMX_HEADERS

START_URL = "/accounts/connect/max/start"
STEP_TARGET = 'hx-target="#max-connect-step"'
EMPTY_PHONE_ERROR = "Введите номер телефона"
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
    assert EMPTY_PHONE_ERROR in over_htmx.text, "во фрагменте нет текста ошибки"
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
    assert EMPTY_PHONE_ERROR in without.text, "на странице нет текста ошибки"
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
    markup = _max_step_markup(step="phone", error=EMPTY_PHONE_ERROR, phone=HOSTILE_PHONE)

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
    authed_client: AsyncClient,
):
    """Непустое враждебное значение идёт веткой старта — и в ответ не попадает."""
    with max_bridge():
        response = await authed_client.post(
            START_URL,
            data={"phone": HOSTILE_PHONE},
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )

    for raw in HOSTILE_RAW_MARKS:
        assert raw not in response.text, (
            f"присланный номер попал в ответ старта НЕЭКРАНИРОВАННЫМ: {raw!r}"
        )


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

"""МАСТЕР ПОДКЛЮЧЕНИЯ TELEGRAM ПО QR НА ФРАГМЕНТАХ (Фаза 13, план 13-01; FETCH-02).

Модуль был набором JSON-контрактов пяти ручных запросов скрипта мастера. План
13-01 переводит старт и опрос на слой ответа, снимает маршрут завершения (D-01:
аккаунт сохраняет сам запрос опроса, первым увидевший «отсканировано») и снимает
скрипт страницы целиком (D-12). JSON-контракты старта, опроса и завершения НЕ
удалены молча, а переписаны на фрагменты ниже; JSON-тесты обновления кода и
пароля 2FA остаются, пока их обработчики не переведены (планы 13-02, 13-03).

⚠️ ТРАСЕР ИДЁТ НА НАСТОЯЩЕМ СЛОЕ СЕССИЙ. Подменяется только клиент Telethon;
`start_qr_auth`, фоновое ожидание сканирования и `complete_auth` — настоящие,
поэтому сквозной путь измеряет и снятие сессии `pop`, и сохранение аккаунта
запросом опроса, а не договорённость подмен между собой.

⚠️ КАНАЛ ИДЕНТИФИКАТОРА СЕССИИ ПРОВЕРЯЕТСЯ, А НЕ ПОДСТАВЛЯЕТСЯ (D-06). Трасер
достаёт `session_id` из скрытого поля фрагмента ожидания — ровно так, как его
отправит форма-опросчик браузера; подставленное тестом значение доказало бы
обработчик, но не канал.

⚠️ ОПРОС ОСТАНАВЛИВАЕТСЯ ОТВЕТОМ, И ЭТО ДОКАЗЫВАЕТСЯ ОТРИСОВАННЫМИ ОТВЕТАМИ.
Гейт опросов инвентаря шаблонов видит только расписание, написанное в теге
литералом; опросчик мастера рождён макросом-обёрткой, и его останов держит
реестр `POLLING_CASES` с правилом `test_polling_stops_by_a_response_without_trigger`.
"""
import asyncio
import re
from dataclasses import dataclass
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.messengers.telegram_user import QRAuthState, _qr_sessions
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from tests.test_pages.test_confirm_delete_transport import DOCUMENT_MARK, HTMX_HEADERS

WIZARD_URL = "/accounts/connect/tg_user"
START_URL = "/accounts/connect/tg_user/start-qr"
POLL_URL = "/accounts/connect/tg_user/qr-status"
ANCHOR_ID = 'id="tg-connect-step"'
POLL_TRIGGER = 'hx-trigger="every 3s"'
SESSION_FIELD = re.compile(r'name="session_id" value="([^"]+)"')

API_NOT_CONFIGURED = "Telegram API не настроен. Обратитесь к администратору."
START_FAILED = "Ошибка запуска QR авторизации: Connection failed"
SESSION_EXPIRED = "Сессия авторизации истекла. Начните заново."
AUTH_FAILED = "Ошибка авторизации"
START_AGAIN_FORM = 'hx-post="/accounts/connect/tg_user/start-qr"'
EXPORTED_SESSION = "exported-session"


@pytest_asyncio.fixture(autouse=True)
async def _no_qr_session_outlives_its_test():
    """Сессии мастера живут в памяти процесса — ни одна не переживает тест.

    Задачи ожидания сканирования отменяются ВНУТРИ цикла событий теста: отмена
    после его закрытия подняла бы отказ закрытого цикла на чужом тесте.
    """
    yield
    tasks = [s._wait_task for s in _qr_sessions.values() if s._wait_task]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _qr_sessions.clear()


class _ScannableQRLogin:
    """QR-вход Telethon, чьё «отсканировано» выставляет тест, а не телефон."""

    def __init__(self, scanned: asyncio.Event):
        self.url = "tg://login?token=tracer"
        self._scanned = scanned

    async def wait(self, timeout=None):
        await self._scanned.wait()


def _telethon_client_factory(scanned: asyncio.Event):
    """Фабрика клиента Telethon для НАСТОЯЩЕГО `start_qr_auth`."""

    def factory(*args, **kwargs):
        client = MagicMock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.qr_login = AsyncMock(return_value=_ScannableQRLogin(scanned))
        client.session.save.return_value = EXPORTED_SESSION
        return client

    return factory


def _seed_state(session_id: str, *, status: str, error: str | None = None,
                session_string: str | None = None) -> None:
    """Настоящее состояние сессии мастера в словаре слоя сессий."""
    client = MagicMock()
    client.disconnect = AsyncMock()
    _qr_sessions[session_id] = QRAuthState(
        client=client, status=status, error=error, session_string=session_string
    )


async def _current_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == "testuser@test.com"))
    return result.scalar_one()


async def _tg_accounts(db: AsyncSession) -> list[MessengerAccount]:
    result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.type == "tg_user")
    )
    return list(result.scalars().all())


def _content_of_the_wizard(page: str) -> str:
    """Содержимое страницы от постоянного якоря мастера, без HTML-комментариев.

    Шелл страницы несёт свои сценарии (слой письма, баннер отказа) ДО блока
    содержимого и комментарий с именем триггера ПОСЛЕ него; предмет проверки —
    мастер, а не шелл.
    """
    start = page.find('<div class="connect-shell" id="tg-connect-step">')
    assert start != -1, (
        "на странице мастера нет постоянного якоря шага — ответам старта и опроса "
        "некуда приземлиться, человек не увидит QR"
    )
    return re.sub(r"<!--.*?-->", "", page[start:], flags=re.S)


# --- ТРАСЕР: от «Начать подключение» до «Подключено» одним путём ------------


@pytest.mark.asyncio
async def test_the_wizard_walks_from_start_to_connected(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сквозной путь мастера на настоящем слое сессий (критерии 1 и 2, D-01, D-06).

    Страница → старт (QR и опросчик) → опрос в ожидании (204, экран не
    трогается) → «отсканировано» → опрос видит успех, сохраняет ОДИН аккаунт и
    отвечает «Подключено» без триггера — опрос остановлен ответом.
    """
    page = await authed_client.get(WIZARD_URL)
    assert page.status_code == 200, f"страница мастера ответила {page.status_code}"
    assert page.text.count(ANCHOR_ID) == 1, (
        "на странице мастера должен быть РОВНО ОДИН постоянный якорь шага — "
        f"найдено {page.text.count(ANCHOR_ID)}; без него QR не появится"
    )

    scanned = asyncio.Event()
    with patch(
        "app.messengers.telegram_user.TelegramClient",
        new=_telethon_client_factory(scanned),
    ):
        started = await authed_client.post(START_URL, headers=HTMX_HEADERS)

    assert started.status_code == 200, (
        f"старт на htmx ответил {started.status_code} вместо 200 — QR не появится"
    )
    body = started.text
    assert DOCUMENT_MARK not in body, "старт вернул целый документ вместо шага мастера"
    assert "data:image/png;base64," in body, "во фрагменте ожидания нет QR-кода"
    assert body.count(POLL_TRIGGER) == 1, (
        f"во фрагменте ожидания {body.count(POLL_TRIGGER)} опросчиков вместо одного — "
        "экран не узнает о сканировании"
    )
    found = SESSION_FIELD.search(body)
    assert found, "во фрагменте ожидания нет скрытого поля session_id — опросу нечего слать"
    session_id = found.group(1)

    waiting = await authed_client.post(
        POLL_URL, data={"session_id": session_id}, headers=HTMX_HEADERS
    )
    assert waiting.status_code == 204, (
        f"опрос в ожидании ответил {waiting.status_code} вместо 204 — экран с QR "
        "перерисовывался бы каждые 3 с"
    )
    assert waiting.content == b"", "ответ 204 опроса в ожидании несёт тело"

    scanned.set()
    for _ in range(100):
        if _qr_sessions[session_id].status == "success":
            break
        await asyncio.sleep(0)
    assert _qr_sessions[session_id].status == "success", (
        "фоновое ожидание сканирования не дошло до успеха — подмена Telethon не сработала"
    )

    connected = await authed_client.post(
        POLL_URL, data={"session_id": session_id}, headers=HTMX_HEADERS
    )
    assert connected.status_code == 200, (
        f"опрос, увидевший успех, ответил {connected.status_code} вместо 200"
    )
    assert "Подключено" in connected.text, "человек не увидел «Подключено» после сканирования"
    assert 'href="/accounts"' in connected.text, "на шаге «Подключено» нет ссылки «К аккаунтам»"
    assert "hx-trigger" not in connected.text, (
        "ответ «Подключено» несёт триггер — опрос не остановится никогда"
    )
    assert "HX-Location" not in connected.headers, (
        "ответ «Подключено» уводит со страницы — автоперехода быть не должно (D-07)"
    )

    user = await _current_user(db_session)
    accounts = await _tg_accounts(db_session)
    assert len(accounts) == 1, (
        f"после одного сканирования сохранено {len(accounts)} аккаунтов вместо одного"
    )
    account = accounts[0]
    assert account.credentials == EXPORTED_SESSION, "аккаунт сохранён не со строкой сессии Telethon"
    assert account.status == "active", f"аккаунт сохранён в статусе {account.status!r}"
    assert account.user_id == user.id, "аккаунт сохранён не на текущего пользователя"
    assert session_id not in _qr_sessions, "сессия мастера пережила сохранение аккаунта"


@pytest.mark.asyncio
async def test_the_waiting_fragment_polls_into_the_persistent_anchor(
    authed_client: AsyncClient,
):
    """Опросчик — форма ВНУТРИ фрагмента ожидания с целью в якорь (Pitfall 1, D-06).

    Якорь во фрагменте означал бы, что опрос висит на элементе, переживающем
    подмену своего содержимого, — такой опрос вечен и стирает экран 2FA.
    """
    with patch(
        "app.pages.accounts.start_qr_auth",
        new=AsyncMock(return_value=("sid-anchor", "tg://login?token=anchor")),
    ):
        started = await authed_client.post(START_URL, headers=HTMX_HEADERS)

    body = started.text
    assert f'hx-post="{POLL_URL}"' in body, "форма-опросчик не шлёт POST на адрес опроса"
    assert 'hx-target="#tg-connect-step"' in body, "опросчик не целится в постоянный якорь"
    assert 'hx-swap="innerHTML"' in body, "опросчик подменяет не содержимое якоря"
    assert ANCHOR_ID not in body, (
        "фрагмент ожидания несёт идентификатор якоря — опрос переживёт свой ответ "
        "и не остановится"
    )
    assert "?session_id" not in body, "идентификатор сессии уехал в адрес запроса (D-06)"

    page = await authed_client.get(WIZARD_URL)
    assert "?session_id" not in page.text, "страница мастера кладёт session_id в адрес"


@pytest.mark.asyncio
async def test_the_wizard_page_carries_no_client_script(authed_client: AsyncClient):
    """Скрипт мастера снят целиком: ни сценария, ни обработчиков нажатия (D-12)."""
    page = await authed_client.get(WIZARD_URL)
    wizard = _content_of_the_wizard(page.text)

    for mark, meaning in (
        ("<script", "инлайн-сценарий"),
        ("onclick", "атрибут-обработчик нажатия"),
        ("fetch(", "ручная сборка запроса"),
        ("setInterval", "таймер браузера"),
        ("hx-trigger", "опрос на странице до старта"),
    ):
        assert mark not in wizard, f"на странице мастера остался {meaning}: {mark!r}"


# --- Отказы: фрагмент с алертом и «Начать заново», опрос остановлен ---------


@pytest.mark.asyncio
async def test_polling_an_unknown_session_offers_to_start_again(authed_client: AsyncClient):
    """Неизвестная сессия — алерт и форма старта, без триггера (D-09)."""
    response = await authed_client.post(
        POLL_URL, data={"session_id": "no-such-session"}, headers=HTMX_HEADERS
    )

    assert response.status_code == 200, f"опрос неизвестной сессии ответил {response.status_code}"
    assert SESSION_EXPIRED in response.text, "человек не узнал, что сессия истекла"
    assert START_AGAIN_FORM in response.text, "после истёкшей сессии нечем начать заново"
    assert "Начать заново" in response.text, "кнопка «Начать заново» не подписана"
    assert "hx-trigger" not in response.text, "ответ отказа продолжает опрос"


@pytest.mark.asyncio
async def test_polling_an_errored_session_shows_the_error(authed_client: AsyncClient):
    """Статус `error` — текст ошибки либо «Ошибка авторизации»; опрос остановлен."""
    _seed_state("sid-error-text", status="error", error="FloodWait 30")
    _seed_state("sid-error-bare", status="error")

    with_text = await authed_client.post(
        POLL_URL, data={"session_id": "sid-error-text"}, headers=HTMX_HEADERS
    )
    bare = await authed_client.post(
        POLL_URL, data={"session_id": "sid-error-bare"}, headers=HTMX_HEADERS
    )

    assert with_text.status_code == 200 and bare.status_code == 200, (
        f"опрос ошибки ответил {with_text.status_code} / {bare.status_code}"
    )
    assert "FloodWait 30" in with_text.text, "текст ошибки Telethon до человека не дошёл"
    assert AUTH_FAILED in bare.text, "ошибка без текста не показала «Ошибка авторизации»"
    for response in (with_text, bare):
        assert "hx-trigger" not in response.text, "ответ ошибки продолжает опрос"
        assert START_AGAIN_FORM in response.text, "после ошибки нечем начать заново"


@pytest.mark.asyncio
async def test_start_refusals_are_fragments_with_verbatim_texts(
    authed_client: AsyncClient, test_settings: Settings, monkeypatch: pytest.MonkeyPatch
):
    """Отказы старта — фрагмент с прежним текстом дословно и «Начать заново» (D-09)."""
    with patch(
        "app.pages.accounts.start_qr_auth",
        new=AsyncMock(side_effect=Exception("Connection failed")),
    ):
        failed = await authed_client.post(START_URL, headers=HTMX_HEADERS)

    monkeypatch.setattr(test_settings, "telegram_api_id", 0)
    not_configured = await authed_client.post(START_URL, headers=HTMX_HEADERS)

    assert failed.status_code == 200, f"отказ старта ответил {failed.status_code}"
    assert START_FAILED in failed.text, "текст отказа старта не переехал дословно"
    assert not_configured.status_code == 200, f"старт без API ответил {not_configured.status_code}"
    assert API_NOT_CONFIGURED in not_configured.text, "текст «API не настроен» не переехал дословно"
    for response in (failed, not_configured):
        assert "hx-trigger" not in response.text, "отказ старта запустил опрос"
        assert "Начать заново" in response.text, "после отказа старта нечем начать заново"
        assert DOCUMENT_MARK not in response.text, "отказ старта вернул целый документ"


# --- Пути деградации и входа (D-10, D-11) -----------------------------------


@pytest.mark.asyncio
async def test_the_wizard_degrades_to_its_page_without_js(authed_client: AsyncClient):
    """Без признака htmx оба обработчика приземляют на страницу мастера (D-11).

    Адреса стоят литералом первым аргументом `.post(…)` в этой же функции: по
    ним обход утверждений 302 модуля пар называет обработчик.
    """
    with patch(
        "app.pages.accounts.start_qr_auth",
        new=AsyncMock(return_value=("sid-nojs", "tg://login?token=nojs")),
    ):
        started = await authed_client.post("/accounts/connect/tg_user/start-qr")
    polled = await authed_client.post(
        "/accounts/connect/tg_user/qr-status", data={"session_id": "sid-nojs"}
    )

    assert started.status_code == 302, f"старт без JS ответил {started.status_code} вместо 302"
    assert started.headers["location"] == "/accounts/connect/tg_user", (
        f"старт без JS приземлил на {started.headers['location']!r}"
    )
    assert polled.status_code == 302, f"опрос без JS ответил {polled.status_code} вместо 302"
    assert polled.headers["location"] == "/accounts/connect/tg_user", (
        f"опрос без JS приземлил на {polled.headers['location']!r}"
    )


@pytest.mark.asyncio
async def test_the_wizard_without_a_session_goes_to_login(client: AsyncClient):
    """Без сессии входа — на `/login` на обоих транспортах, без JSON (D-10).

    Адреса стоят литералом первым аргументом `.post(…)`: по ним обход
    утверждений 302 модуля пар называет обработчик.
    """
    start_htmx = await client.post("/accounts/connect/tg_user/start-qr", headers=HTMX_HEADERS)
    poll_htmx = await client.post(
        "/accounts/connect/tg_user/qr-status", data={"session_id": "x"}, headers=HTMX_HEADERS
    )
    for name, over_htmx in (("старт", start_htmx), ("опрос", poll_htmx)):
        assert over_htmx.status_code == 204, (
            f"{name} без входа на htmx ответил {over_htmx.status_code} вместо 204"
        )
        assert over_htmx.headers.get("HX-Location") == "/login", (
            f"{name} без входа на htmx не уводит на /login"
        )

    start_plain = await client.post("/accounts/connect/tg_user/start-qr")
    assert start_plain.status_code == 302, f"старт без входа без JS ответил {start_plain.status_code}"
    assert start_plain.headers["location"] == "/login", (
        f"старт без входа без JS приземлил на {start_plain.headers['location']!r}"
    )
    poll_plain = await client.post("/accounts/connect/tg_user/qr-status", data={"session_id": "x"})
    assert poll_plain.status_code == 302, f"опрос без входа без JS ответил {poll_plain.status_code}"
    assert poll_plain.headers["location"] == "/login", (
        f"опрос без входа без JS приземлил на {poll_plain.headers['location']!r}"
    )


@pytest.mark.asyncio
async def test_the_complete_route_and_the_get_poll_are_gone(authed_client: AsyncClient):
    """Маршрута завершения нет, опрос сменил метод GET → POST (D-01)."""
    complete = await authed_client.post(
        "/accounts/connect/tg_user/complete", data={"session_id": "x"}
    )
    get_poll = await authed_client.get(f"{POLL_URL}?session_id=x")

    assert complete.status_code in (404, 405), (
        f"маршрут завершения всё ещё отвечает {complete.status_code} — аккаунт "
        "сохранялся бы вторым путём мимо опроса"
    )
    assert get_poll.status_code == 405, (
        f"GET опроса ответил {get_poll.status_code} вместо 405 — опрос пишет в базу "
        "и обязан быть POST"
    )


# --- Реестр останова опроса (критерий 2) ------------------------------------


@dataclass(frozen=True)
class _PollingCase:
    """Запись реестра: исход обработчика мастера и ждём ли от него опроса."""

    slug: str
    name: str
    route: str
    seed: Callable[[pytest.MonkeyPatch, Settings], dict]
    polls: bool


def _seed_start_success(monkeypatch, settings):
    monkeypatch.setattr(
        "app.pages.accounts.start_qr_auth",
        AsyncMock(return_value=("sid-registry", "tg://login?token=registry")),
    )
    return {}


def _seed_start_not_configured(monkeypatch, settings):
    monkeypatch.setattr(settings, "telegram_api_id", 0)
    return {}


def _seed_start_exception(monkeypatch, settings):
    monkeypatch.setattr(
        "app.pages.accounts.start_qr_auth",
        AsyncMock(side_effect=Exception("Connection failed")),
    )
    return {}


def _seed_poll_success(monkeypatch, settings):
    _seed_state("sid-success", status="success", session_string=EXPORTED_SESSION)
    return {"session_id": "sid-success"}


def _seed_poll_unknown(monkeypatch, settings):
    return {"session_id": "no-such-session"}


def _seed_poll_error(monkeypatch, settings):
    _seed_state("sid-error", status="error", error="FloodWait 30")
    return {"session_id": "sid-error"}


# Планы 13-02 и 13-03 дописывают свои записи (шаг пароля, код истёк),
# план 13-05 замыкает реестр.
POLLING_CASES: tuple[_PollingCase, ...] = (
    _PollingCase("start-waiting", "старт — QR и опросчик", START_URL, _seed_start_success, True),
    _PollingCase("start-not-configured", "старт — API не настроен", START_URL, _seed_start_not_configured, False),
    _PollingCase("start-exception", "старт — исключение Telethon", START_URL, _seed_start_exception, False),
    _PollingCase("poll-success", "опрос — успех, «Подключено»", POLL_URL, _seed_poll_success, False),
    _PollingCase("poll-unknown", "опрос — неизвестная сессия", POLL_URL, _seed_poll_unknown, False),
    _PollingCase("poll-error", "опрос — ошибка Telethon", POLL_URL, _seed_poll_error, False),
)


def test_the_polling_registry_holds_both_sides_of_the_pair():
    """Без обеих сторон пары правило ниже зеленело бы вакуумом."""
    assert any(case.polls for case in POLLING_CASES), (
        "в реестре нет ни одного ответа с опросом — правило останова вакуумно"
    )
    assert any(not case.polls and case.route == POLL_URL for case in POLLING_CASES), (
        "в реестре нет ни одного ответа опроса без триггера — останов не доказан"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("case", POLLING_CASES, ids=[c.slug for c in POLLING_CASES])
async def test_polling_stops_by_a_response_without_trigger(
    case: _PollingCase,
    authed_client: AsyncClient,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
):
    """Триггер опроса несёт ТОЛЬКО ответ ожидания; любой иной 200 его не несёт."""
    data = case.seed(monkeypatch, test_settings)
    response = await authed_client.post(case.route, data=data, headers=HTMX_HEADERS)

    assert response.status_code == 200, f"{case.name}: ответ {response.status_code} вместо 200"
    if case.polls:
        assert POLL_TRIGGER in response.text, f"{case.name}: опрос не запущен — экран замрёт на QR"
    else:
        assert "hx-trigger" not in response.text, (
            f"{case.name}: ответ несёт триггер — опрос не остановится"
        )


# --- JSON-контракты обновления кода и пароля 2FA (до планов 13-02, 13-03) ---


@pytest_asyncio.fixture
async def auth_setup():
    """Отдельное приложение для ещё не переведённых `refresh-qr` / `verify-2fa`."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
    )
    app = create_app(settings=settings)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        async with AsyncClient(
            transport=transport, base_url="http://test", follow_redirects=True
        ) as reg_client:
            await reg_client.post("/api/auth/register", json={
                "email": "tgauth@test.com", "password": "pass123", "name": "TG User",
            })
            await reg_client.post("/login", data={"email": "tgauth@test.com", "password": "pass123"})
            cookies = reg_client.cookies

        for name, value in cookies.items():
            client.cookies.set(name, value)

        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_verify_2fa_success_creates_account(auth_setup):
    client, session_factory = auth_setup

    with patch("app.pages.accounts.submit_2fa", new_callable=AsyncMock) as mock_2fa:
        mock_2fa.return_value = "session_string_2fa"

        with patch("app.pages.accounts.complete_auth", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "session_string_2fa"

            resp = await client.post(
                "/accounts/connect/tg_user/verify-2fa",
                content='{"session_id": "test_session", "password": "my2fapass"}',
                headers={"Content-Type": "application/json"},
            )

    data = resp.json()
    assert data["status"] == "success"

    async with session_factory() as session:
        result = await session.execute(select(MessengerAccount))
        account = result.scalar_one()
        assert account.credentials == "session_string_2fa"
        assert account.status == "active"


@pytest.mark.asyncio
async def test_verify_2fa_wrong_password_returns_error(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.submit_2fa", new_callable=AsyncMock) as mock_2fa:
        mock_2fa.side_effect = ValueError("Неверный пароль 2FA.")

        resp = await client.post(
            "/accounts/connect/tg_user/verify-2fa",
            content='{"session_id": "test_session", "password": "wrongpass"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "error" in data
    assert "Неверный пароль" in data["error"]


@pytest.mark.asyncio
async def test_refresh_qr_returns_new_image(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.refresh_qr", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = "tg://login?token=newtoken"

        resp = await client.post(
            "/accounts/connect/tg_user/refresh-qr",
            content='{"session_id": "test_session"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "qr_image" in data
    assert data["qr_image"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_refresh_qr_failure_returns_error(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.refresh_qr", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = None

        resp = await client.post(
            "/accounts/connect/tg_user/refresh-qr",
            content='{"session_id": "test_session"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "error" in data

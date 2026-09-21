"""МАСТЕР ПОДКЛЮЧЕНИЯ TELEGRAM ПО QR НА ФРАГМЕНТАХ (Фаза 13, план 13-01; FETCH-02).

Модуль был набором JSON-контрактов пяти ручных запросов скрипта мастера. План
13-01 переводит старт и опрос на слой ответа, снимает маршрут завершения (D-01:
аккаунт сохраняет сам запрос опроса, первым увидевший «отсканировано») и снимает
скрипт страницы целиком (D-12). JSON-контракты старта, опроса и завершения НЕ
удалены молча, а переписаны на фрагменты ниже. План 13-02 переводит `verify-2fa`
и снимает его JSON-тесты: их предмет переписан правилами шага пароля и двух
гонок ниже. JSON-тесты обновления кода остаются до плана 13-03.

⚠️ ОДНО СКАНИРОВАНИЕ — ОДИН АККАУНТ, И ЭТО ДОКАЗЫВАЕТСЯ ГОНКОЙ, А НЕ ОБЕЩАНИЕМ
(D-01, RESEARCH §Pitfall 3). Мест сохранения два — опрос, увидевший успех, и
верный пароль 2FA; оба правила гонки идут на НАСТОЯЩЕМ `complete_auth`, и каждый
запрос получает СВОЮ сессию базы (фикстура `race_client`).

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
from sqlalchemy import func, select
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

VERIFY_URL = "/accounts/connect/tg_user/verify-2fa"
VERIFY_FORM = f'hx-post="{VERIFY_URL}"'
WRONG_PASSWORD = "Неверный пароль 2FA."
EMPTY_PASSWORD = "Введите пароль"
PASSWORD_2FA_SESSION = "session-2fa"
# Присланный пароль нарочно ни на что в разметке не похож: его появление в теле
# ответа — эхо, а не совпадение с текстом шаблона (D-08, T-06-02).
SUBMITTED_PASSWORD = "Zx9-пароль-qW7"
PASSWORD_INPUT = re.compile(r'<input[^>]*\bname="password"[^>]*>')

REFRESH_URL = "/accounts/connect/tg_user/refresh-qr"
REFRESH_FORM = f'hx-post="{REFRESH_URL}"'
QR_EXPIRED_TEXT = "QR-код истёк. Обновите его, чтобы продолжить."
REFRESH_BUTTON = "Обновить QR-код"


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


def _seed_2fa_state(session_id: str, *, sign_in=None) -> MagicMock:
    """Настоящее состояние `needs_2fa` с клиентом Telethon, чей вход подменён.

    Клиент — `AsyncMock`, но его `session` — синхронный `MagicMock`: у
    `AsyncMock` вызов `session.save()` вернул бы корутину, и в аккаунт уехала бы
    не строка сессии. `submit_2fa` и `complete_auth` остаются настоящими.
    """
    client = AsyncMock()
    client.session = MagicMock()
    client.session.save.return_value = PASSWORD_2FA_SESSION
    client.sign_in = sign_in if sign_in is not None else AsyncMock()
    _qr_sessions[session_id] = QRAuthState(client=client, status="needs_2fa")
    return client


def _raises_password_hash_invalid() -> AsyncMock:
    """Вход с паролем, который Telegram отвергает: настоящая ошибка Telethon."""
    from telethon.errors import PasswordHashInvalidError

    return AsyncMock(side_effect=PasswordHashInvalidError(request=None))


def _password_input(body: str) -> str:
    """Тег поля пароля — единственный во фрагменте шага."""
    found = PASSWORD_INPUT.findall(body)
    assert len(found) == 1, (
        f"полей пароля во фрагменте {len(found)} вместо одного — человеку с 2FA "
        "некуда ввести пароль"
    )
    return found[0]


def _assert_the_password_field_is_empty(body: str) -> None:
    """Поле пароля приходит ПУСТЫМ, а присланный пароль нигде не эхается (D-08).

    Макрос `field` печатает атрибут `value` всегда; пустой он — и есть «поле
    без значения». Присланная строка ищется во ВСЁМ теле, а не только в поле:
    перенос пароля в любой другой атрибут — та же утечка (T-06-02).
    """
    tag = _password_input(body)
    value = re.search(r'\bvalue="([^"]*)"', tag)
    assert value is None or value.group(1) == "", (
        f"поле пароля пришло со значением {value.group(1)!r} — пароль эхается (D-08)"
    )
    assert SUBMITTED_PASSWORD not in body, "присланный пароль вернулся в теле ответа (D-08)"


async def _count_tg_accounts(factory: async_sessionmaker) -> int:
    async with factory() as session:
        result = await session.execute(
            select(func.count()).select_from(MessengerAccount).where(
                MessengerAccount.type == "tg_user"
            )
        )
        return result.scalar_one()


@pytest_asyncio.fixture
async def race_client(tmp_path, test_settings: Settings):
    """Клиент, у которого КАЖДЫЙ запрос получает СВОЮ сессию базы (D-01).

    ⚠️ ОБЩАЯ СЕССИЯ ФИКСТУРЫ `db_session` ЗДЕСЬ НЕ ГОДИТСЯ. Два конкурентных
    запроса делили бы один `AsyncSession`, чего SQLAlchemy не допускает: правило
    гонки краснело бы по чужой причине (отказ сессии, а не второй аккаунт) либо
    сериализовалось бы на её блокировке и зеленело вакуумом. Поэтому движок
    стоит на ВРЕМЕННОМ ФАЙЛЕ — база в памяти у каждого соединения своя, — и
    `get_db` отдаёт новую сессию на каждый запрос, как в эксплуатации.
    """
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'race.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = create_app(settings=test_settings)

    async def per_request_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = per_request_session
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/auth/register", json={
            "email": "racer@test.com", "password": "testpass123", "name": "Racer",
        })
        await client.post(
            "/login",
            data={"email": "racer@test.com", "password": "testpass123"},
            follow_redirects=False,
        )
        yield client, factory

    await engine.dispose()


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


# --- «Код истёк» и «Обновить QR-код» (план 13-03; D-02, D-03) ---------------


@pytest.mark.asyncio
async def test_polling_an_expired_code_offers_a_refresh(authed_client: AsyncClient):
    """Опрос в `qr_expired` — шаг «код истёк» с кнопкой обновления, опрос остановлен.

    Автоматического обновления нет (D-02, решение владельца): забытая вкладка
    не должна продолжать обращаться к Telegram, поэтому в ответе нет триггера.
    """
    _seed_state("sid-qr-expired", status="qr_expired")

    response = await authed_client.post(
        POLL_URL, data={"session_id": "sid-qr-expired"}, headers=HTMX_HEADERS
    )

    assert response.status_code == 200, f"опрос истёкшего кода ответил {response.status_code}"
    body = response.text
    assert QR_EXPIRED_TEXT in body, (
        "человек не узнал, что QR-код истёк, — через ~30 с он видит тупик (D-03)"
    )
    assert body.count(REFRESH_FORM) == 1, (
        f"форм обновления кода {body.count(REFRESH_FORM)} вместо одной — "
        "истёкший код нечем обновить (D-02)"
    )
    assert REFRESH_BUTTON in body, "кнопка «Обновить QR-код» не подписана"
    found = SESSION_FIELD.search(body)
    assert found and found.group(1) == "sid-qr-expired", (
        "форма обновления не несёт session_id скрытым полем — обновлять нечего (D-06)"
    )
    assert 'hx-target="#tg-connect-step"' in body, "ответ обновления некуда приземлить"
    assert "hx-trigger" not in body, (
        "шаг «код истёк» продолжает опрос — забытая вкладка обращалась бы к Telegram (D-02)"
    )
    assert "data:image/png;base64," not in body, (
        "на шаге «код истёк» показан мёртвый QR — он приглашает к бесполезному сканированию"
    )


# --- Шаг пароля 2FA (план 13-02; D-08, D-09) --------------------------------


@pytest.mark.asyncio
async def test_polling_needs_2fa_answers_the_password_step(authed_client: AsyncClient):
    """Опрос в `needs_2fa` — шаг пароля без опросчика: опрос остановлен ответом.

    Шаг пароля — форма `verify-2fa` со скрытым `session_id` в постоянный якорь и
    полем `password` с `required` без значения. Триггера в ответе нет: вечный
    опрос стёр бы экран пароля через 3 с (RESEARCH §Pitfall 1).
    """
    _seed_state("sid-needs-2fa", status="needs_2fa")

    response = await authed_client.post(
        POLL_URL, data={"session_id": "sid-needs-2fa"}, headers=HTMX_HEADERS
    )

    assert response.status_code == 200, f"опрос в needs_2fa ответил {response.status_code}"
    body = response.text
    assert 'name="password"' in body, (
        "опрос в needs_2fa не показал поле пароля — человек с 2FA не подключится"
    )
    tag = _password_input(body)
    assert re.search(r"\srequired\b", tag), "поле пароля не обязательно — пустой пароль уйдёт"
    assert 'type="password"' in tag, "поле пароля показывает вводимое открытым текстом"
    assert 'id="password"' in tag, (
        "у поля пароля нет постоянного id — после подмены 422 фокус не вернётся (QUAL-06)"
    )
    _assert_the_password_field_is_empty(body)
    assert VERIFY_FORM in body, "шаг пароля не шлёт форму на verify-2fa"
    assert 'hx-target="#tg-connect-step"' in body, "форма пароля не целится в постоянный якорь"
    assert 'name="session_id" value="sid-needs-2fa"' in body, (
        "в форме пароля нет скрытого session_id — подтверждать нечего"
    )
    assert "hx-trigger" not in body, "шаг пароля продолжает опрос — экран сотрётся"
    assert "Подтвердить" in body, "кнопка шага пароля не подписана"
    assert "двухфакторная аутентификация" in body, "шаг пароля не объясняет, что спрашивает"
    assert DOCUMENT_MARK not in body, "опрос вернул целый документ вместо шага"


@pytest.mark.asyncio
async def test_a_wrong_password_answers_422_at_the_field_without_echo(authed_client: AsyncClient):
    """Неверный пароль — 422 и шаг пароля с ошибкой у поля; пароль не эхается (D-08).

    Отказ поднимает НАСТОЯЩИЙ `submit_2fa` из настоящей ошибки Telethon: так
    измеряется дословный текст «Неверный пароль 2FA.», а не подставленный тестом.
    """
    _seed_2fa_state("sid-wrong", sign_in=_raises_password_hash_invalid())

    over_htmx = await authed_client.post(
        VERIFY_URL,
        data={"session_id": "sid-wrong", "password": SUBMITTED_PASSWORD},
        headers=HTMX_HEADERS,
    )

    assert over_htmx.status_code == 422, (
        f"неверный пароль на htmx ответил {over_htmx.status_code} вместо 422"
    )
    assert WRONG_PASSWORD in over_htmx.text, "текст «Неверный пароль 2FA.» не дошёл до человека"
    assert 'class="field__error"' in over_htmx.text, "ошибка пароля стоит не у поля"
    _assert_the_password_field_is_empty(over_htmx.text)
    assert "hx-trigger" not in over_htmx.text, "ответ неверного пароля запустил опрос"
    assert 'name="session_id" value="sid-wrong"' in over_htmx.text, (
        "после неверного пароля форма потеряла session_id — повторить нечем"
    )
    assert DOCUMENT_MARK not in over_htmx.text, "ошибка пароля на htmx вернула целый документ"
    assert "sid-wrong" in _qr_sessions, "неверный пароль уничтожил сессию — повторить нельзя"

    plain = await authed_client.post(
        VERIFY_URL, data={"session_id": "sid-wrong", "password": SUBMITTED_PASSWORD}
    )
    assert plain.status_code == 422, f"неверный пароль без JS ответил {plain.status_code}"
    assert WRONG_PASSWORD in plain.text, "страница мастера без JS не несёт ошибку пароля"
    assert ANCHOR_ID in plain.text, "без JS ошибка пароля пришла не страницей мастера"
    _assert_the_password_field_is_empty(plain.text)


@pytest.mark.asyncio
async def test_an_empty_password_answers_422_with_the_client_text(authed_client: AsyncClient):
    """Пустой и отсутствующий пароль — 422 «Введите пароль»; Telegram не зовётся (D-08)."""
    _seed_2fa_state("sid-empty")

    with patch("app.pages.accounts.submit_2fa", new_callable=AsyncMock) as submitted:
        blank = await authed_client.post(
            VERIFY_URL, data={"session_id": "sid-empty", "password": "   "}, headers=HTMX_HEADERS
        )
        missing = await authed_client.post(
            VERIFY_URL, data={"session_id": "sid-empty"}, headers=HTMX_HEADERS
        )
        plain = await authed_client.post(
            VERIFY_URL, data={"session_id": "sid-empty", "password": ""}
        )

    # Шелл страницы несёт свои триггеры вне мастера — у пути без JS
    # проверяется содержимое мастера от постоянного якоря.
    for name, response, body in (
        ("пробелы", blank, blank.text),
        ("нет поля", missing, missing.text),
        ("без JS", plain, _content_of_the_wizard(plain.text)),
    ):
        assert response.status_code == 422, f"пустой пароль ({name}) ответил {response.status_code}"
        assert EMPTY_PASSWORD in body, f"пустой пароль ({name}) без «Введите пароль»"
        assert "hx-trigger" not in body, f"пустой пароль ({name}) запустил опрос"
    submitted.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_right_password_saves_one_account_from_complete_auth(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Верный пароль — «Подключено» и ровно один аккаунт со строкой сессии (D-01, D-07)."""
    client = _seed_2fa_state("sid-right")

    response = await authed_client.post(
        VERIFY_URL,
        data={"session_id": "sid-right", "password": SUBMITTED_PASSWORD},
        headers=HTMX_HEADERS,
    )

    assert response.status_code == 200, f"верный пароль ответил {response.status_code}"
    assert "Подключено" in response.text, "после верного пароля человек не увидел «Подключено»"
    assert "hx-trigger" not in response.text, "ответ «Подключено» продолжает опрос"
    assert "HX-Location" not in response.headers, "«Подключено» уводит со страницы (D-07)"
    assert SUBMITTED_PASSWORD not in response.text, "пароль вернулся в ответе «Подключено»"
    client.sign_in.assert_awaited_once_with(password=SUBMITTED_PASSWORD)

    accounts = await _tg_accounts(db_session)
    assert len(accounts) == 1, f"верный пароль сохранил {len(accounts)} аккаунтов вместо одного"
    assert accounts[0].credentials == PASSWORD_2FA_SESSION, (
        "аккаунт сохранён не со строкой сессии Telethon"
    )
    assert accounts[0].status == "active", f"аккаунт сохранён в статусе {accounts[0].status!r}"
    assert "sid-right" not in _qr_sessions, "сессия мастера пережила сохранение аккаунта"


@pytest.mark.asyncio
async def test_a_telethon_failure_on_the_password_step_is_a_fragment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Иная ошибка Telethon — шаг ошибки с «Начать заново», не 500 (D-09, Pitfall 5).

    500 здесь поднял бы общий баннер отказа вместо шага. Запись журнала об
    отказе не несёт пароля (T-13-05).
    """
    _seed_2fa_state("sid-flood", sign_in=AsyncMock(side_effect=Exception("FloodWait 30")))

    with patch("structlog.get_logger") as get_logger:
        response = await authed_client.post(
            VERIFY_URL,
            data={"session_id": "sid-flood", "password": SUBMITTED_PASSWORD},
            headers=HTMX_HEADERS,
        )

    assert response.status_code == 200, (
        f"ошибка Telethon на шаге пароля ответила {response.status_code} вместо 200"
    )
    assert AUTH_FAILED in response.text, "ошибка Telethon не показала «Ошибка авторизации»"
    assert START_AGAIN_FORM in response.text, "после ошибки Telethon нечем начать заново"
    assert "hx-trigger" not in response.text, "ответ ошибки продолжает опрос"
    assert SUBMITTED_PASSWORD not in response.text, "пароль вернулся в ответе ошибки"
    assert get_logger.return_value.error.called or get_logger.return_value.warning.called, (
        "ошибка Telethon на шаге пароля не записана в журнал"
    )
    assert SUBMITTED_PASSWORD not in repr(get_logger.mock_calls), "пароль попал в журнал"
    assert await _tg_accounts(db_session) == [], "ошибка Telethon сохранила аккаунт"


@pytest.mark.asyncio
async def test_verify_2fa_degrades_and_requires_a_session(authed_client: AsyncClient):
    """Без JS — на страницу мастера; без входа — на `/login`; чужая сессия — шаг ошибки.

    Адреса стоят литералом первым аргументом `.post(…)` в этой же функции: по
    ним обход утверждений 302 модуля пар называет обработчик (D-10, D-11).
    """
    _seed_2fa_state("sid-nojs-2fa")
    plain = await authed_client.post(
        "/accounts/connect/tg_user/verify-2fa",
        data={"session_id": "sid-nojs-2fa", "password": SUBMITTED_PASSWORD},
    )
    assert plain.status_code == 302, f"верный пароль без JS ответил {plain.status_code} вместо 302"
    assert plain.headers["location"] == "/accounts/connect/tg_user", (
        f"верный пароль без JS приземлил на {plain.headers['location']!r}"
    )

    unknown = await authed_client.post(
        VERIFY_URL,
        data={"session_id": "no-such-session", "password": SUBMITTED_PASSWORD},
        headers=HTMX_HEADERS,
    )
    assert unknown.status_code == 200, f"неизвестная сессия ответила {unknown.status_code}"
    assert SESSION_EXPIRED in unknown.text, "неизвестная сессия не сказала, что сессия истекла"
    assert START_AGAIN_FORM in unknown.text, "после неизвестной сессии нечем начать заново"

    authed_client.cookies.clear()
    over_htmx = await authed_client.post(
        "/accounts/connect/tg_user/verify-2fa",
        data={"session_id": "x", "password": SUBMITTED_PASSWORD},
        headers=HTMX_HEADERS,
    )
    assert over_htmx.status_code == 204, f"verify-2fa без входа на htmx ответил {over_htmx.status_code}"
    assert over_htmx.headers.get("HX-Location") == "/login", "verify-2fa без входа не уводит на /login"
    no_session = await authed_client.post(
        "/accounts/connect/tg_user/verify-2fa",
        data={"session_id": "x", "password": SUBMITTED_PASSWORD},
    )
    assert no_session.status_code == 302, f"verify-2fa без входа без JS ответил {no_session.status_code}"
    assert no_session.headers["location"] == "/login", (
        f"verify-2fa без входа без JS приземлил на {no_session.headers['location']!r}"
    )


# --- Ровно один аккаунт на сканирование под гонкой (D-01, Pitfall 3) --------


@pytest.mark.asyncio
async def test_two_concurrent_password_submits_save_one_account(race_client):
    """Два конкурентных верных пароля — ОДИН аккаунт; строка берётся из `complete_auth`.

    ⚠️ ВХОД С ПАРОЛЕМ — ТОЧКА ВСТРЕЧИ ДВУХ ЗАПРОСОВ. Каждый вызов `sign_in` ждёт,
    пока в него войдёт второй (с потолком ожидания), и отдаёт управление: так оба
    запроса гарантированно проходят `submit_2fa` до того, как любой из них снимет
    сессию. Обработчик, берущий строку для записи из `submit_2fa`, дал бы здесь
    ДВА аккаунта (замер мутанта — в SUMMARY плана 13-02); настоящий
    `complete_auth` снимает сессию `pop` до первого ожидания, и второму
    достаётся пустота.
    """
    client, factory = race_client
    both_inside = asyncio.Event()
    entered = 0

    async def sign_in(password):
        nonlocal entered
        entered += 1
        if entered >= 2:
            both_inside.set()
        try:
            await asyncio.wait_for(both_inside.wait(), timeout=2)
        except asyncio.TimeoutError:
            pass
        await asyncio.sleep(0)

    _seed_2fa_state("sid-race-2fa", sign_in=AsyncMock(side_effect=sign_in))

    responses = await asyncio.gather(*(
        client.post(
            VERIFY_URL,
            data={"session_id": "sid-race-2fa", "password": SUBMITTED_PASSWORD},
            headers=HTMX_HEADERS,
        )
        for _ in range(2)
    ))

    assert entered == 2, (
        f"в вход с паролем вошли {entered} запросов из двух — гонка не состоялась, "
        "и правило зеленело бы вакуумом"
    )
    assert await _count_tg_accounts(factory) == 1, (
        "два конкурентных верных пароля сохранили не один аккаунт — одно сканирование, "
        "два аккаунта (RESEARCH §Pitfall 3)"
    )
    connected = [r for r in responses if "Подключено" in r.text]
    assert len(connected) == 1, f"«Подключено» получили {len(connected)} ответов из двух"
    for response in responses:
        assert response.status_code == 200, f"ответ гонки {response.status_code} вместо 200"
        assert "hx-trigger" not in response.text, "ответ гонки продолжает опрос"


@pytest.mark.asyncio
async def test_two_concurrent_polls_after_success_save_one_account(race_client):
    """Два конкурентных опроса после успеха — ОДИН аккаунт; `complete_auth` настоящий."""
    client, factory = race_client
    tg_client = MagicMock()

    async def disconnect():
        await asyncio.sleep(0)

    tg_client.disconnect = AsyncMock(side_effect=disconnect)
    _qr_sessions["sid-race-poll"] = QRAuthState(
        client=tg_client, status="success", session_string=EXPORTED_SESSION
    )

    responses = await asyncio.gather(*(
        client.post(POLL_URL, data={"session_id": "sid-race-poll"}, headers=HTMX_HEADERS)
        for _ in range(2)
    ))

    assert await _count_tg_accounts(factory) == 1, (
        "два конкурентных опроса после успеха сохранили не один аккаунт (D-01)"
    )
    connected = [r for r in responses if "Подключено" in r.text]
    assert len(connected) == 1, f"«Подключено» получили {len(connected)} ответов из двух"
    for response in responses:
        assert response.status_code == 200, f"ответ гонки {response.status_code} вместо 200"
        assert "hx-trigger" not in response.text, "ответ гонки продолжает опрос"


@pytest.mark.asyncio
async def test_a_second_poll_after_success_does_not_save_again(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Второй опрос тем же `session_id` после «Подключено» — шаг ошибки, аккаунт один."""
    _seed_state("sid-twice", status="success", session_string=EXPORTED_SESSION)

    first = await authed_client.post(
        POLL_URL, data={"session_id": "sid-twice"}, headers=HTMX_HEADERS
    )
    second = await authed_client.post(
        POLL_URL, data={"session_id": "sid-twice"}, headers=HTMX_HEADERS
    )

    assert "Подключено" in first.text, "первый опрос после успеха не показал «Подключено»"
    assert second.status_code == 200, f"второй опрос ответил {second.status_code}"
    assert "Подключено" not in second.text, "второй опрос снова показал «Подключено»"
    assert START_AGAIN_FORM in second.text, "второй опрос не предложил начать заново"
    assert len(await _tg_accounts(db_session)) == 1, "второй опрос сохранил аккаунт ещё раз"


# --- Реестр останова опроса (критерий 2) ------------------------------------


@dataclass(frozen=True)
class _PollingCase:
    """Запись реестра: исход обработчика мастера и ждём ли от него опроса."""

    slug: str
    name: str
    route: str
    seed: Callable[[pytest.MonkeyPatch, Settings], dict]
    polls: bool
    # Ошибка поля шага пароля отвечает 422 (D-08): её тело подменяет якорь
    # правилом блока конфигурации так же, как 200, и обязано не нести триггер.
    status: int = 200


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


def _seed_poll_needs_2fa(monkeypatch, settings):
    _seed_state("sid-needs-2fa", status="needs_2fa")
    return {"session_id": "sid-needs-2fa"}


def _seed_poll_qr_expired(monkeypatch, settings):
    _seed_state("sid-qr-expired", status="qr_expired")
    return {"session_id": "sid-qr-expired"}


def _seed_verify_success(monkeypatch, settings):
    _seed_2fa_state("sid-2fa-right")
    return {"session_id": "sid-2fa-right", "password": SUBMITTED_PASSWORD}


def _seed_verify_wrong(monkeypatch, settings):
    _seed_2fa_state("sid-2fa-wrong", sign_in=_raises_password_hash_invalid())
    return {"session_id": "sid-2fa-wrong", "password": SUBMITTED_PASSWORD}


def _seed_verify_empty(monkeypatch, settings):
    _seed_2fa_state("sid-2fa-empty")
    return {"session_id": "sid-2fa-empty", "password": ""}


def _seed_verify_telethon_failure(monkeypatch, settings):
    _seed_2fa_state("sid-2fa-flood", sign_in=AsyncMock(side_effect=Exception("FloodWait 30")))
    return {"session_id": "sid-2fa-flood", "password": SUBMITTED_PASSWORD}


# План 13-02 дописал шаг пароля (опрос в `needs_2fa` и четыре исхода
# `verify-2fa`); план 13-03 дописал «код истёк» и исходы `refresh-qr`, план
# 13-05 замыкает реестр.
POLLING_CASES: tuple[_PollingCase, ...] = (
    _PollingCase("start-waiting", "старт — QR и опросчик", START_URL, _seed_start_success, True),
    _PollingCase("start-not-configured", "старт — API не настроен", START_URL, _seed_start_not_configured, False),
    _PollingCase("start-exception", "старт — исключение Telethon", START_URL, _seed_start_exception, False),
    _PollingCase("poll-success", "опрос — успех, «Подключено»", POLL_URL, _seed_poll_success, False),
    _PollingCase("poll-unknown", "опрос — неизвестная сессия", POLL_URL, _seed_poll_unknown, False),
    _PollingCase("poll-error", "опрос — ошибка Telethon", POLL_URL, _seed_poll_error, False),
    _PollingCase("poll-needs-2fa", "опрос — шаг пароля 2FA", POLL_URL, _seed_poll_needs_2fa, False),
    _PollingCase("poll-qr-expired", "опрос — код истёк, кнопка обновления", POLL_URL, _seed_poll_qr_expired, False),
    _PollingCase("verify-success", "пароль 2FA — «Подключено»", VERIFY_URL, _seed_verify_success, False),
    _PollingCase("verify-wrong", "пароль 2FA — неверный, 422", VERIFY_URL, _seed_verify_wrong, False, 422),
    _PollingCase("verify-empty", "пароль 2FA — пустой, 422", VERIFY_URL, _seed_verify_empty, False, 422),
    _PollingCase("verify-telethon", "пароль 2FA — ошибка Telethon", VERIFY_URL, _seed_verify_telethon_failure, False),
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
    """Триггер опроса несёт ТОЛЬКО ответ ожидания; любой иной ответ с телом его не несёт."""
    data = case.seed(monkeypatch, test_settings)
    response = await authed_client.post(case.route, data=data, headers=HTMX_HEADERS)

    assert response.status_code == case.status, (
        f"{case.name}: ответ {response.status_code} вместо {case.status}"
    )
    if case.polls:
        assert POLL_TRIGGER in response.text, f"{case.name}: опрос не запущен — экран замрёт на QR"
    else:
        assert "hx-trigger" not in response.text, (
            f"{case.name}: ответ несёт триггер — опрос не остановится"
        )


# --- JSON-контракты обновления кода (до плана 13-03) -----------------------


@pytest_asyncio.fixture
async def auth_setup():
    """Отдельное приложение для ещё не переведённого `refresh-qr` (план 13-03)."""
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

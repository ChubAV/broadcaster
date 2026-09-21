"""МАСТЕР ПОДКЛЮЧЕНИЯ TELEGRAM ПО QR НА ФРАГМЕНТАХ (Фаза 13, план 13-01; FETCH-02).

Модуль был набором JSON-контрактов пяти ручных запросов скрипта мастера. План
13-01 переводит старт и опрос на слой ответа, снимает маршрут завершения (D-01:
аккаунт сохраняет сам запрос опроса, первым увидевший «отсканировано») и снимает
скрипт страницы целиком (D-12). JSON-контракты старта, опроса и завершения НЕ
удалены молча, а переписаны на фрагменты ниже. План 13-02 переводит `verify-2fa`
и снимает его JSON-тесты: их предмет переписан правилами шага пароля и двух
гонок ниже. План 13-03 переводит `refresh-qr` и снимает последние JSON-тесты
мастера: их предмет переписан правилами «код истёк» и «Обновить QR-код» ниже.

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

⚠️ СЕССИЯ ПРИНАДЛЕЖИТ ТОМУ, КТО ЕЁ НАЧАЛ (план 13-04, D-04). До плана проверки
владения не было: любой вошедший, зная чужой `session_id` (он пишется в журнал),
сохранял чужой Telegram себе. Каждый посев поэтому несёт владельца, а правила
«чужая сессия» сравнивают ответ на неё с ответом на неизвестную ПОБАЙТНО.

⚠️ ОПРОС ОСТАНАВЛИВАЕТСЯ ОТВЕТОМ, И ЭТО ДОКАЗЫВАЕТСЯ ОТРИСОВАННЫМИ ОТВЕТАМИ.
Гейт опросов инвентаря шаблонов видит только расписание, написанное в теге
литералом; опросчик мастера рождён макросом-обёрткой, и его останов держит
реестр `POLLING_CASES` с правилом `test_polling_stops_by_a_response_without_trigger`.
"""
import asyncio
import datetime
import re
import time
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from telethon.tl.custom.qrlogin import QRLogin

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.messengers.telegram_user import QR_SESSION_TTL, QRAuthState, _qr_sessions, _wait_for_qr
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from tests.test_pages.test_confirm_delete_transport import DOCUMENT_MARK, HTMX_HEADERS
from tests.test_pages.test_impersonation import _enter, _seed_target, _user

WIZARD_URL = "/accounts/connect/tg_user"
START_URL = "/accounts/connect/tg_user/start-qr"
POLL_URL = "/accounts/connect/tg_user/qr-status"
ANCHOR_ID = 'id="tg-connect-step"'
POLL_TRIGGER = 'hx-trigger="every 3s"'
SESSION_FIELD = re.compile(r'name="session_id" value="([^"]+)"')

API_NOT_CONFIGURED = "Telegram API не настроен. Обратитесь к администратору."
START_FAILED = "Ошибка запуска QR авторизации: Connection failed"
SESSION_EXPIRED = "Сессия авторизации истекла. Начните заново."
# Неизвестная ИЛИ чужая сессия (план 13-04, D-04): существование чужой сессии не
# раскрывается, различие «истекла / не найдена» видит только владелец.
SESSION_NOT_FOUND = "Сессия подключения не найдена. Начните заново."
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
REFRESH_FAILED = "Не удалось обновить QR. Начните заново."


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


def _seed_state(session_id: str, *, owner: int, status: str, error: str | None = None,
                session_string: str | None = None) -> None:
    """Настоящее состояние сессии мастера в словаре слоя сессий, с владельцем (D-04)."""
    client = MagicMock()
    client.disconnect = AsyncMock()
    _qr_sessions[session_id] = QRAuthState(
        client=client, user_id=owner, status=status, error=error,
        session_string=session_string,
    )


class _RenewableCode:
    """Объект кода Telethon для исходов `refresh-qr`: `recreate` и адрес кода.

    `wait()` ждёт вечно: задача ожидания, запущенная `refresh_qr`, живёт до
    отмены автоматической фикстурой модуля.
    """

    def __init__(self):
        self.recreate = AsyncMock()
        self.url = "tg://login?token=renewed"
        self._never = asyncio.Event()

    async def wait(self, timeout=None):
        await self._never.wait()


def _seed_expired_code(session_id: str, *, owner: int, status: str = "qr_expired",
                       age: float = 0.0) -> _RenewableCode:
    """Настоящее состояние сессии с кодом, который `refresh_qr` может пересоздать."""
    code = _RenewableCode()
    client = MagicMock()
    client.disconnect = AsyncMock()
    _qr_sessions[session_id] = QRAuthState(
        client=client, user_id=owner, qr_login=code, status=status,
        created_at=time.time() - age,
    )
    return code


def _seed_2fa_state(session_id: str, *, owner: int, sign_in=None) -> MagicMock:
    """Настоящее состояние `needs_2fa` с клиентом Telethon, чей вход подменён.

    Клиент — `AsyncMock`, но его `session` — синхронный `MagicMock`: у
    `AsyncMock` вызов `session.save()` вернул бы корутину, и в аккаунт уехала бы
    не строка сессии. `submit_2fa` и `complete_auth` остаются настоящими.
    """
    client = AsyncMock()
    client.session = MagicMock()
    client.session.save.return_value = PASSWORD_2FA_SESSION
    client.sign_in = sign_in if sign_in is not None else AsyncMock()
    _qr_sessions[session_id] = QRAuthState(client=client, user_id=owner, status="needs_2fa")
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


async def _racer_id(factory: async_sessionmaker) -> int:
    """Владелец сессий гонки — пользователь фикстуры `race_client` (D-04)."""
    async with factory() as session:
        result = await session.execute(select(User.id).where(User.email == "racer@test.com"))
        return result.scalar_one()


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


@pytest_asyncio.fixture
async def owner_id(authed_client: AsyncClient, db_session: AsyncSession) -> int:
    """Идентификатор вошедшего пользователя — владельца посеянных сессий (D-04).

    Сессия мастера принадлежит тому, кто её начал; посев на чужого владельца
    отвечал бы «не найдена», и правило про свой исход краснело бы по чужой
    причине.
    """
    return (await _current_user(db_session)).id


FOREIGN_EMAIL = "stranger@test.com"
OWNER_EMAIL = "testuser@test.com"
PASSWORD = "testpass123"


async def _sign_in_as(client: AsyncClient, email: str, *, register: bool = False) -> None:
    """Вход ТЕМ ЖЕ клиентом под другим пользователем: cookie входа подменяется."""
    if register:
        registered = await client.post("/api/auth/register", json={
            "email": email, "password": PASSWORD, "name": "Чужой",
        })
        assert registered.status_code == 201, (
            f"второй пользователь не зарегистрирован ({registered.status_code}) — "
            "правило про чужую сессию проверяло бы владельца"
        )
    signed = await client.post(
        "/login", data={"email": email, "password": PASSWORD}, follow_redirects=False
    )
    assert signed.status_code == 302, f"вход под {email} не состоялся ({signed.status_code})"


def _unknown_session_id() -> str:
    """Случайный `session_id` той же формы, что выдаёт слой сессий."""
    return uuid.uuid4().hex[:16]


def _same_answer(foreign, unknown) -> None:
    """Ответ на чужую сессию ПОБАЙТНО равен ответу на неизвестную (D-04).

    Сравниваются код, тело и заголовки, кроме даты и идентификатора запроса
    (оба свои у КАЖДОГО ответа): поиск подстроки пропустил бы различие в
    разметке, раскрывающее существование чужой сессии.
    """
    assert foreign.status_code == unknown.status_code, (
        f"код ответа на чужую сессию {foreign.status_code}, на неизвестную "
        f"{unknown.status_code} — существование сессии раскрыто (D-04)"
    )
    assert foreign.content == unknown.content, (
        "тело ответа на чужую сессию отличается от ответа на неизвестную — "
        "существование сессии раскрыто (D-04)"
    )

    def _headers(response):
        return {
            k: v for k, v in response.headers.items()
            if k.lower() not in {"date", "x-request-id"}
        }

    assert _headers(foreign) == _headers(unknown), (
        "заголовки ответа на чужую сессию отличаются от ответа на неизвестную (D-04)"
    )


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
    """Неизвестная сессия — «не найдена», алерт и форма старта, без триггера (D-04, D-09)."""
    response = await authed_client.post(
        POLL_URL, data={"session_id": "no-such-session"}, headers=HTMX_HEADERS
    )

    assert response.status_code == 200, f"опрос неизвестной сессии ответил {response.status_code}"
    assert SESSION_NOT_FOUND in response.text, "человек не узнал, что сессия не найдена"
    assert SESSION_EXPIRED not in response.text, (
        "неизвестная сессия названа истёкшей — «истекла» видит только владелец (D-04)"
    )
    assert START_AGAIN_FORM in response.text, "после ненайденной сессии нечем начать заново"
    assert "Начать заново" in response.text, "кнопка «Начать заново» не подписана"
    assert "hx-trigger" not in response.text, "ответ отказа продолжает опрос"


@pytest.mark.asyncio
async def test_polling_an_errored_session_shows_the_error(
    authed_client: AsyncClient, owner_id: int
):
    """Статус `error` — текст ошибки либо «Ошибка авторизации»; опрос остановлен."""
    _seed_state("sid-error-text", owner=owner_id, status="error", error="FloodWait 30")
    _seed_state("sid-error-bare", owner=owner_id, status="error")

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
async def test_polling_an_expired_code_offers_a_refresh(authed_client: AsyncClient, owner_id: int):
    """Опрос в `qr_expired` — шаг «код истёк» с кнопкой обновления, опрос остановлен.

    Автоматического обновления нет (D-02, решение владельца): забытая вкладка
    не должна продолжать обращаться к Telegram, поэтому в ответе нет триггера.
    """
    _seed_state("sid-qr-expired", owner=owner_id, status="qr_expired")

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


@pytest.mark.asyncio
async def test_refreshing_an_expired_code_resumes_polling(
    authed_client: AsyncClient, owner_id: int
):
    """Сквозной срез: код истёк → «Обновить QR-код» → новый код и опрос (D-02, D-03).

    ⚠️ ИСТЕЧЕНИЕ ВОСПРОИЗВОДИТСЯ НАСТОЯЩИМ `QRLogin` И НАСТОЯЩИМ `_wait_for_qr`
    (CONTEXT §Landmines): таймаут `wait()` поднимается сам, а не ставится
    статусом. Клиент Telethon — заглушка, чей вызов (`ExportLoginToken` внутри
    `recreate`) отдаёт новый токен со сроком 30 с.
    """
    client = AsyncMock()
    client.add_event_handler = MagicMock()
    client.remove_event_handler = MagicMock()
    client.return_value = SimpleNamespace(
        token=b"new",
        expires=datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=30),
    )
    code = QRLogin(client, [])
    code._resp = SimpleNamespace(
        token=b"old",
        expires=datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=0.05),
    )
    state = QRAuthState(client=client, user_id=owner_id, qr_login=code)
    _qr_sessions["sid-renew"] = state
    state._wait_task = asyncio.create_task(_wait_for_qr("sid-renew"))
    await asyncio.wait_for(asyncio.shield(state._wait_task), timeout=2)
    assert state.status == "qr_expired", (
        f"настоящий таймаут кода дал статус {state.status!r} вместо «код истёк»"
    )

    expired = await authed_client.post(
        POLL_URL, data={"session_id": "sid-renew"}, headers=HTMX_HEADERS
    )
    assert expired.status_code == 200 and QR_EXPIRED_TEXT in expired.text, (
        "опрос после истечения кода не показал «QR-код истёк»"
    )
    assert "hx-trigger" not in expired.text, "шаг «код истёк» продолжает опрос (D-02)"
    found = SESSION_FIELD.search(expired.text)
    assert found, "форма обновления не несёт session_id — обновлять нечего"

    refreshed = await authed_client.post(
        REFRESH_URL, data={"session_id": found.group(1)}, headers=HTMX_HEADERS
    )

    assert refreshed.status_code == 200, (
        f"«Обновить QR-код» ответил {refreshed.status_code} вместо 200"
    )
    body = refreshed.text
    assert DOCUMENT_MARK not in body, "обновление вернуло целый документ вместо шага"
    assert "data:image/png;base64," in body, "после обновления нет нового QR-кода"
    assert body.count(POLL_TRIGGER) == 1, (
        f"после обновления {body.count(POLL_TRIGGER)} опросчиков вместо одного — "
        "новый код отсканируют, но экран не узнает (D-02)"
    )
    again = SESSION_FIELD.search(body)
    assert again and again.group(1) == "sid-renew", (
        "шаг ожидания после обновления потерял session_id — опросу нечего слать"
    )
    assert client.await_count == 1, (
        f"новый токен запрошен у Telegram {client.await_count} раз вместо одного"
    )
    assert state.qr_login.token == b"new", "код не пересоздан — показан старый токен"

    polled = await authed_client.post(
        POLL_URL, data={"session_id": "sid-renew"}, headers=HTMX_HEADERS
    )
    assert polled.status_code == 204, (
        f"опрос после обновления ответил {polled.status_code} вместо 204 — "
        "ожидание сканирования не возобновилось"
    )


@pytest.mark.asyncio
async def test_refreshing_an_outdated_session_says_it_expired(
    authed_client: AsyncClient, owner_id: int
):
    """Сессия старше срока — «Сессия истекла», форма старта; код не пересоздаётся (D-03)."""
    code = _seed_expired_code("sid-outdated", owner=owner_id, age=QR_SESSION_TTL + 1)

    response = await authed_client.post(
        REFRESH_URL, data={"session_id": "sid-outdated"}, headers=HTMX_HEADERS
    )

    assert response.status_code == 200, f"обновление устаревшей сессии ответило {response.status_code}"
    assert SESSION_EXPIRED in response.text, (
        "устаревшая сессия не сказала, что истекла, — человек обновлял бы мёртвую сессию"
    )
    assert START_AGAIN_FORM in response.text, "после истёкшей сессии нечем начать заново"
    assert "hx-trigger" not in response.text, "ответ истёкшей сессии запустил опрос"
    assert not code.recreate.await_count, "устаревшая сессия ожила новым кодом (Pitfall 2)"


@pytest.mark.asyncio
async def test_refreshing_a_non_expired_code_is_refused(
    authed_client: AsyncClient, owner_id: int
):
    """Код не истёк — отказ прежним текстом, сессия не тронута (D-03, D-09)."""
    code = _seed_expired_code("sid-still-waiting", owner=owner_id, status="waiting")

    response = await authed_client.post(
        REFRESH_URL, data={"session_id": "sid-still-waiting"}, headers=HTMX_HEADERS
    )

    assert response.status_code == 200, f"обновление живого кода ответило {response.status_code}"
    assert REFRESH_FAILED in response.text, "отказ обновления не показал прежний текст дословно"
    assert START_AGAIN_FORM in response.text, "после отказа обновления нечем начать заново"
    assert "hx-trigger" not in response.text, "отказ обновления запустил опрос"
    assert not code.recreate.await_count, "живой код пересоздан подделанным запросом"
    assert _qr_sessions["sid-still-waiting"].status == "waiting", "отказ сменил статус сессии"


@pytest.mark.asyncio
async def test_refresh_degrades_and_requires_a_session(authed_client: AsyncClient, owner_id: int):
    """Без JS — на страницу мастера; без входа — на `/login`; чужая сессия — шаг ошибки.

    Адреса стоят литералом первым аргументом `.post(…)` в этой же функции: по
    ним обход утверждений 302 модуля пар называет обработчик (D-10, D-11).
    """
    _seed_expired_code("sid-nojs-refresh", owner=owner_id)
    plain = await authed_client.post(
        "/accounts/connect/tg_user/refresh-qr", data={"session_id": "sid-nojs-refresh"}
    )
    assert plain.status_code == 302, f"обновление без JS ответило {plain.status_code} вместо 302"
    assert plain.headers["location"] == "/accounts/connect/tg_user", (
        f"обновление без JS приземлило на {plain.headers['location']!r}"
    )

    unknown = await authed_client.post(
        REFRESH_URL, data={"session_id": "no-such-session"}, headers=HTMX_HEADERS
    )
    assert unknown.status_code == 200, f"неизвестная сессия ответила {unknown.status_code}"
    assert SESSION_NOT_FOUND in unknown.text, "неизвестная сессия не сказала, что не найдена"
    assert START_AGAIN_FORM in unknown.text, "после неизвестной сессии нечем начать заново"

    authed_client.cookies.clear()
    over_htmx = await authed_client.post(
        "/accounts/connect/tg_user/refresh-qr", data={"session_id": "x"}, headers=HTMX_HEADERS
    )
    assert over_htmx.status_code == 204, f"refresh-qr без входа на htmx ответил {over_htmx.status_code}"
    assert over_htmx.headers.get("HX-Location") == "/login", "refresh-qr без входа не уводит на /login"
    no_session = await authed_client.post(
        "/accounts/connect/tg_user/refresh-qr", data={"session_id": "x"}
    )
    assert no_session.status_code == 302, f"refresh-qr без входа без JS ответил {no_session.status_code}"
    assert no_session.headers["location"] == "/login", (
        f"refresh-qr без входа без JS приземлил на {no_session.headers['location']!r}"
    )


# --- Шаг пароля 2FA (план 13-02; D-08, D-09) --------------------------------


@pytest.mark.asyncio
async def test_polling_needs_2fa_answers_the_password_step(
    authed_client: AsyncClient, owner_id: int
):
    """Опрос в `needs_2fa` — шаг пароля без опросчика: опрос остановлен ответом.

    Шаг пароля — форма `verify-2fa` со скрытым `session_id` в постоянный якорь и
    полем `password` с `required` без значения. Триггера в ответе нет: вечный
    опрос стёр бы экран пароля через 3 с (RESEARCH §Pitfall 1).
    """
    _seed_state("sid-needs-2fa", owner=owner_id, status="needs_2fa")

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
async def test_a_wrong_password_answers_422_at_the_field_without_echo(
    authed_client: AsyncClient, owner_id: int
):
    """Неверный пароль — 422 и шаг пароля с ошибкой у поля; пароль не эхается (D-08).

    Отказ поднимает НАСТОЯЩИЙ `submit_2fa` из настоящей ошибки Telethon: так
    измеряется дословный текст «Неверный пароль 2FA.», а не подставленный тестом.
    """
    _seed_2fa_state("sid-wrong", owner=owner_id, sign_in=_raises_password_hash_invalid())

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
async def test_an_empty_password_answers_422_with_the_client_text(
    authed_client: AsyncClient, owner_id: int
):
    """Пустой и отсутствующий пароль — 422 «Введите пароль»; Telegram не зовётся (D-08)."""
    _seed_2fa_state("sid-empty", owner=owner_id)

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
    authed_client: AsyncClient, db_session: AsyncSession, owner_id: int
):
    """Верный пароль — «Подключено» и ровно один аккаунт со строкой сессии (D-01, D-07)."""
    client = _seed_2fa_state("sid-right", owner=owner_id)

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
    authed_client: AsyncClient, db_session: AsyncSession, owner_id: int
):
    """Иная ошибка Telethon — шаг ошибки с «Начать заново», не 500 (D-09, Pitfall 5).

    500 здесь поднял бы общий баннер отказа вместо шага. Запись журнала об
    отказе не несёт пароля (T-13-05).
    """
    _seed_2fa_state(
        "sid-flood", owner=owner_id, sign_in=AsyncMock(side_effect=Exception("FloodWait 30"))
    )

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
async def test_verify_2fa_degrades_and_requires_a_session(authed_client: AsyncClient, owner_id: int):
    """Без JS — на страницу мастера; без входа — на `/login`; чужая сессия — шаг ошибки.

    Адреса стоят литералом первым аргументом `.post(…)` в этой же функции: по
    ним обход утверждений 302 модуля пар называет обработчик (D-10, D-11).
    """
    _seed_2fa_state("sid-nojs-2fa", owner=owner_id)
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
    assert SESSION_NOT_FOUND in unknown.text, "неизвестная сессия не сказала, что не найдена"
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


# --- Чужая сессия — как неизвестная, и без следа (план 13-04, D-04) ---------


async def _start_as_the_current_user(client: AsyncClient) -> tuple[str, asyncio.Event]:
    """НАСТОЯЩИЙ старт мастера текущим пользователем; подменён только Telethon.

    Сессия заводится `start_qr_auth`, а не посевом состояния: так владелец
    записывается тем же путём, что в эксплуатации, а `session_id` берётся из
    скрытого поля фрагмента ожидания (D-06).
    """
    scanned = asyncio.Event()
    with patch(
        "app.messengers.telegram_user.TelegramClient",
        new=_telethon_client_factory(scanned),
    ):
        started = await client.post(START_URL, headers=HTMX_HEADERS)
    assert started.status_code == 200, f"старт ответил {started.status_code}"
    found = SESSION_FIELD.search(started.text)
    assert found, "во фрагменте ожидания нет скрытого поля session_id"
    return found.group(1), scanned


async def _until_scanned(session_id: str, scanned: asyncio.Event) -> None:
    scanned.set()
    for _ in range(100):
        if _qr_sessions[session_id].status == "success":
            break
        await asyncio.sleep(0)
    assert _qr_sessions[session_id].status == "success", (
        "фоновое ожидание сканирования не дошло до успеха — подмена Telethon не сработала"
    )


@pytest.mark.asyncio
async def test_a_foreign_poll_is_answered_as_unknown_and_leaves_no_trace(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чужой опрос сессии в `success` — ответ неизвестной сессии; сессия владельца цела.

    Без проверки владения посторонний с чужим `session_id` сохранял чужой
    Telegram СЕБЕ (D-04). Сессия заводится настоящим стартом владельца; затем
    тем же клиентом входит посторонний и опрашивает её. После этого владелец
    опрашивает сам и доходит до «Подключено» с аккаунтом на себя.
    """
    owner = await _current_user(db_session)
    session_id, scanned = await _start_as_the_current_user(authed_client)
    await _until_scanned(session_id, scanned)
    victim = _qr_sessions[session_id]

    await _sign_in_as(authed_client, FOREIGN_EMAIL, register=True)
    foreign = await authed_client.post(
        POLL_URL, data={"session_id": session_id}, headers=HTMX_HEADERS
    )

    stolen = await _tg_accounts(db_session)
    assert stolen == [], (
        f"посторонний опросом чужой сессии сохранил {len(stolen)} аккаунт(ов) — "
        "чужой Telegram записан не на владельца (D-04)"
    )
    unknown = await authed_client.post(
        POLL_URL, data={"session_id": _unknown_session_id()}, headers=HTMX_HEADERS
    )
    _same_answer(foreign, unknown)
    assert SESSION_NOT_FOUND in foreign.text, "чужая сессия не ответила «не найдена»"
    assert "hx-trigger" not in foreign.text, "ответ на чужую сессию продолжает опрос"

    assert _qr_sessions.get(session_id) is victim, "чужой опрос снял сессию владельца (D-04)"
    assert victim.status == "success", f"чужой опрос сменил статус на {victim.status!r}"
    assert victim.session_string == EXPORTED_SESSION, "чужой опрос тронул строку сессии"
    assert not victim.client.disconnect.await_count, (
        "чужой опрос отключил клиента Telegram владельца"
    )

    await _sign_in_as(authed_client, OWNER_EMAIL)
    connected = await authed_client.post(
        POLL_URL, data={"session_id": session_id}, headers=HTMX_HEADERS
    )
    assert "Подключено" in connected.text, (
        "владелец после чужого опроса не дошёл до «Подключено»"
    )
    accounts = await _tg_accounts(db_session)
    assert [a.user_id for a in accounts] == [owner.id], (
        f"после чужого опроса аккаунты на {[a.user_id for a in accounts]!r} вместо "
        f"одного на владельца {owner.id}"
    )


@pytest.mark.asyncio
async def test_the_wizard_binds_the_session_to_the_impersonated_subject(
    admin_client: AsyncClient, db_session: AsyncSession, test_settings: Settings
):
    """Под имперсонацией сессия и аккаунт — на СУБЪЕКТА, не на администратора (D-04).

    `get_user_from_cookie` возвращает субъекта (`payload["sub"]`), администратор
    висит атрибутом. Привязка к администратору отвергла бы собственный опрос
    субъекта либо записала бы его Telegram на администратора.
    """
    admin = await _user(db_session, test_settings.admin_email)
    target_id = await _seed_target(admin_client, db_session)
    assert target_id != admin.id, "субъект совпал с администратором — правило вакуумно"
    await _enter(admin_client, target_id)

    session_id, scanned = await _start_as_the_current_user(admin_client)
    assert _qr_sessions[session_id].user_id == target_id, (
        f"сессия под имперсонацией записана на {_qr_sessions[session_id].user_id!r} "
        f"вместо субъекта {target_id} (D-04)"
    )

    await _until_scanned(session_id, scanned)
    connected = await admin_client.post(
        POLL_URL, data={"session_id": session_id}, headers=HTMX_HEADERS
    )
    assert "Подключено" in connected.text, "опрос под имперсонацией не дошёл до «Подключено»"
    accounts = await _tg_accounts(db_session)
    assert [a.user_id for a in accounts] == [target_id], (
        f"аккаунт под имперсонацией записан на {[a.user_id for a in accounts]!r} "
        f"вместо субъекта {target_id}"
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
    racer = await _racer_id(factory)
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

    _seed_2fa_state("sid-race-2fa", owner=racer, sign_in=AsyncMock(side_effect=sign_in))

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
    racer = await _racer_id(factory)
    tg_client = MagicMock()

    async def disconnect():
        await asyncio.sleep(0)

    tg_client.disconnect = AsyncMock(side_effect=disconnect)
    _qr_sessions["sid-race-poll"] = QRAuthState(
        client=tg_client, user_id=racer, status="success", session_string=EXPORTED_SESSION
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
    authed_client: AsyncClient, db_session: AsyncSession, owner_id: int
):
    """Второй опрос тем же `session_id` после «Подключено» — шаг ошибки, аккаунт один."""
    _seed_state("sid-twice", owner=owner_id, status="success", session_string=EXPORTED_SESSION)

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
    # Посев получает владельца — вошедшего пользователя (D-04, план 13-04).
    seed: Callable[[pytest.MonkeyPatch, Settings, int], dict]
    polls: bool
    # Ошибка поля шага пароля отвечает 422 (D-08): её тело подменяет якорь
    # правилом блока конфигурации так же, как 200, и обязано не нести триггер.
    status: int = 200


def _seed_start_success(monkeypatch, settings, owner):
    monkeypatch.setattr(
        "app.pages.accounts.start_qr_auth",
        AsyncMock(return_value=("sid-registry", "tg://login?token=registry")),
    )
    return {}


def _seed_start_not_configured(monkeypatch, settings, owner):
    monkeypatch.setattr(settings, "telegram_api_id", 0)
    return {}


def _seed_start_exception(monkeypatch, settings, owner):
    monkeypatch.setattr(
        "app.pages.accounts.start_qr_auth",
        AsyncMock(side_effect=Exception("Connection failed")),
    )
    return {}


def _seed_poll_success(monkeypatch, settings, owner):
    _seed_state("sid-success", owner=owner, status="success", session_string=EXPORTED_SESSION)
    return {"session_id": "sid-success"}


def _seed_poll_unknown(monkeypatch, settings, owner):
    return {"session_id": "no-such-session"}


def _seed_poll_error(monkeypatch, settings, owner):
    _seed_state("sid-error", owner=owner, status="error", error="FloodWait 30")
    return {"session_id": "sid-error"}


def _seed_poll_needs_2fa(monkeypatch, settings, owner):
    _seed_state("sid-needs-2fa", owner=owner, status="needs_2fa")
    return {"session_id": "sid-needs-2fa"}


def _seed_poll_qr_expired(monkeypatch, settings, owner):
    _seed_state("sid-qr-expired", owner=owner, status="qr_expired")
    return {"session_id": "sid-qr-expired"}


def _seed_poll_foreign(monkeypatch, settings, owner):
    # Чужая сессия в `success`: владелец — другой пользователь (D-04).
    _seed_state("sid-foreign", owner=owner + 1, status="success", session_string=EXPORTED_SESSION)
    return {"session_id": "sid-foreign"}


def _seed_refresh_success(monkeypatch, settings, owner):
    _seed_expired_code("sid-refresh", owner=owner)
    return {"session_id": "sid-refresh"}


def _seed_refresh_outdated(monkeypatch, settings, owner):
    _seed_expired_code("sid-refresh-outdated", owner=owner, age=QR_SESSION_TTL + 1)
    return {"session_id": "sid-refresh-outdated"}


def _seed_refresh_not_expired(monkeypatch, settings, owner):
    _seed_expired_code("sid-refresh-waiting", owner=owner, status="waiting")
    return {"session_id": "sid-refresh-waiting"}


def _seed_refresh_unknown(monkeypatch, settings, owner):
    return {"session_id": "no-such-session"}


def _seed_verify_success(monkeypatch, settings, owner):
    _seed_2fa_state("sid-2fa-right", owner=owner)
    return {"session_id": "sid-2fa-right", "password": SUBMITTED_PASSWORD}


def _seed_verify_wrong(monkeypatch, settings, owner):
    _seed_2fa_state("sid-2fa-wrong", owner=owner, sign_in=_raises_password_hash_invalid())
    return {"session_id": "sid-2fa-wrong", "password": SUBMITTED_PASSWORD}


def _seed_verify_empty(monkeypatch, settings, owner):
    _seed_2fa_state("sid-2fa-empty", owner=owner)
    return {"session_id": "sid-2fa-empty", "password": ""}


def _seed_verify_telethon_failure(monkeypatch, settings, owner):
    _seed_2fa_state("sid-2fa-flood", owner=owner, sign_in=AsyncMock(side_effect=Exception("FloodWait 30")))
    return {"session_id": "sid-2fa-flood", "password": SUBMITTED_PASSWORD}


# План 13-02 дописал шаг пароля (опрос в `needs_2fa` и четыре исхода
# `verify-2fa`); план 13-03 дописал «код истёк» и исходы `refresh-qr`; план
# 13-04 дописал чужие сессии; план 13-05 замыкает реестр.
POLLING_CASES: tuple[_PollingCase, ...] = (
    _PollingCase("start-waiting", "старт — QR и опросчик", START_URL, _seed_start_success, True),
    _PollingCase("start-not-configured", "старт — API не настроен", START_URL, _seed_start_not_configured, False),
    _PollingCase("start-exception", "старт — исключение Telethon", START_URL, _seed_start_exception, False),
    _PollingCase("poll-success", "опрос — успех, «Подключено»", POLL_URL, _seed_poll_success, False),
    _PollingCase("poll-unknown", "опрос — неизвестная сессия", POLL_URL, _seed_poll_unknown, False),
    _PollingCase("poll-error", "опрос — ошибка Telethon", POLL_URL, _seed_poll_error, False),
    _PollingCase("poll-needs-2fa", "опрос — шаг пароля 2FA", POLL_URL, _seed_poll_needs_2fa, False),
    _PollingCase("poll-qr-expired", "опрос — код истёк, кнопка обновления", POLL_URL, _seed_poll_qr_expired, False),
    _PollingCase("poll-foreign", "опрос — чужая сессия, «не найдена»", POLL_URL, _seed_poll_foreign, False),
    _PollingCase("refresh-success", "обновление — новый код и опросчик", REFRESH_URL, _seed_refresh_success, True),
    _PollingCase("refresh-outdated", "обновление — сессия старше срока", REFRESH_URL, _seed_refresh_outdated, False),
    _PollingCase("refresh-not-expired", "обновление — код не истёк", REFRESH_URL, _seed_refresh_not_expired, False),
    _PollingCase("refresh-unknown", "обновление — неизвестная сессия", REFRESH_URL, _seed_refresh_unknown, False),
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
    owner_id: int,
):
    """Триггер опроса несёт ТОЛЬКО ответ ожидания; любой иной ответ с телом его не несёт."""
    data = case.seed(monkeypatch, test_settings, owner_id)
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

import asyncio
import datetime
import time
from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from telethon.errors import ForbiddenError, PeerIdInvalidError
from telethon.tl.custom.qrlogin import QRLogin
from app.messengers.base import MessengerFetchError
from app.messengers.telegram_user import (
    PEER_UNREACHABLE_MESSAGE,
    TelegramUserMessenger,
    start_qr_auth,
    get_qr_status,
    submit_2fa,
    complete_auth,
    cleanup_qr_session,
    _qr_sessions,
    _wait_for_qr,
    QR_SESSION_TTL,
    QRAuthState,
    refresh_qr,
)


# Владелец и посторонний QR-сессии (D-04): сессия принадлежит тому, кто её
# начал, и каждая функция слоя сверяет её с текущим пользователем.
OWNER = 7
STRANGER = 8


@pytest.fixture
def messenger():
    with patch("app.messengers.telegram_user.TelegramClient") as MockClient, \
         patch("app.messengers.telegram_user.StringSession") as MockSession:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=False)
        MockClient.return_value = mock_client

        m = TelegramUserMessenger(
            session_string="fake-session",
            api_id=12345,
            api_hash="fake-api-hash",
        )
        m.client = mock_client
        yield m


@pytest.mark.asyncio
async def test_send_text_message(messenger):
    messenger.client.send_message = AsyncMock()
    result = await messenger.send_message("-100123", "Hello!")
    assert result["ok"] is True
    messenger.client.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_with_image(messenger):
    """Одна картинка уезжает ОДИНОЧНЫМ файлом, а не списком из одного элемента.

    Список уводит telethon в альбомную ветку `_send_album`, где первым же
    запросом идёт `messages.uploadMedia` — тот самый, что получал от сервера
    400 PEER_ID_INVALID. Одиночный файл идёт через `messages.sendMedia` и
    `uploadMedia` не будит вовсе, поэтому утверждение здесь прямое: это НЕ
    список.
    """
    messenger.client.send_file = AsyncMock()

    with patch(
        "app.messengers.telegram_user.httpx.AsyncClient",
        return_value=_http_client_returning_image_bytes(),
    ):
        result = await messenger.send_message(
            "-100123", "Hello!", images=["https://cdn.example.com/bucket/img.jpg"]
        )

    assert result["ok"] is True
    messenger.client.send_file.assert_called_once()
    sent = messenger.client.send_file.call_args[0][1]
    assert not isinstance(sent, list)
    assert sent.name == "img.jpg"
    assert sent.read() == b"fake-image-bytes"


@pytest.mark.asyncio
async def test_two_images_still_go_as_an_album(messenger):
    """Две картинки продолжают уходить списком: граница живёт между 1 и 2.

    Существующий тест на ТРИ картинки этой границы не держит: перепутанное
    сравнение «не больше единицы» вместо «ровно один» он пропустил бы, и
    альбом из двух картинок уехал бы одиночным файлом, потеряв вторую.
    """
    messenger.client.send_file = AsyncMock()
    imgs = [
        "https://cdn.example.com/bucket/img1.jpg",
        "https://cdn.example.com/bucket/img2.jpg",
    ]

    with patch(
        "app.messengers.telegram_user.httpx.AsyncClient",
        return_value=_http_client_returning_image_bytes(),
    ):
        result = await messenger.send_message("-100123", "Hello!", images=imgs)

    assert result["ok"] is True
    sent = messenger.client.send_file.call_args[0][1]
    assert isinstance(sent, list)
    assert len(sent) == 2
    assert sent[0].name == "img1.jpg"
    assert sent[1].name == "img2.jpg"


@pytest.mark.asyncio
async def test_send_message_with_multiple_images(messenger):
    messenger.client.send_file = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.raise_for_status = MagicMock()
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)

    imgs = [
        "https://cdn.example.com/bucket/img1.jpg",
        "https://cdn.example.com/bucket/img2.jpg",
        "https://cdn.example.com/bucket/img3.jpg",
    ]
    with patch("app.messengers.telegram_user.httpx.AsyncClient", return_value=mock_http):
        result = await messenger.send_message("-100123", "Hello!", images=imgs)
    assert result["ok"] is True
    call_args = messenger.client.send_file.call_args
    sent_files = call_args[0][1]
    assert len(sent_files) == 3
    # Each file should be a BytesIO with correct filename
    assert sent_files[0].name == "img1.jpg"
    assert sent_files[1].name == "img2.jpg"
    assert sent_files[2].name == "img3.jpg"


@pytest.mark.asyncio
async def test_send_message_error(messenger):
    messenger.client.send_message = AsyncMock(side_effect=Exception("Flood wait"))
    result = await messenger.send_message("-100123", "Hello!")
    assert result["ok"] is False
    assert "Flood wait" in result["error"]


# --- Разрешение peer перед отправкой ---


def _http_client_returning_image_bytes():
    """Подменённый `httpx.AsyncClient`, отдающий одни и те же байты картинки.

    Заведён, чтобы тесты про адресата отправки не тонули в шести строках
    настройки загрузки: их предмет — какая сущность уехала в telethon, а не
    какие байты приехали из S3.
    """
    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.raise_for_status = MagicMock()
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    return mock_http


@pytest.mark.asyncio
async def test_send_file_receives_a_resolved_peer_not_a_bare_id(messenger):
    """Ветка картинок адресуется разрешённой сущностью, а не голым числом.

    Голое число и получало от сервера 400 PEER_ID_INVALID на
    `messages.uploadMedia`: строка сессии не хранит `access_hash`, кэш
    сущностей у свежего клиента пуст, и telethon вынужден угадывать peer по
    знаку числа. Сравнение идёт через `is` с объектом, который вернул
    подменённый `get_input_entity`: фикстура отдаёт `AsyncMock`, поэтому
    проверка «не число» была бы зелёной и на сломанном коде.
    """
    peer = object()
    messenger.client.get_input_entity = AsyncMock(return_value=peer)
    messenger.client.send_file = AsyncMock()

    with patch(
        "app.messengers.telegram_user.httpx.AsyncClient",
        return_value=_http_client_returning_image_bytes(),
    ):
        result = await messenger.send_message(
            "-100123", "Hello!", images=["https://cdn.example.com/bucket/img.jpg"]
        )

    assert result["ok"] is True
    assert messenger.client.send_file.call_args[0][0] is peer


@pytest.mark.asyncio
async def test_the_text_path_sends_to_a_resolved_peer(messenger):
    """Текстовая ветка адресуется той же разрешённой сущностью.

    Текст доходит и с голым числом — `messages.sendMessage` не проверяет peer
    так строго, как `uploadMedia`. Поэтому ветка выглядит исправной, и её
    легко оставить с `int(group_id)`; разойдясь с остальными, она вернёт
    исходный дефект на первом же изменении соседнего кода.
    """
    peer = object()
    messenger.client.get_input_entity = AsyncMock(return_value=peer)
    messenger.client.send_message = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is True
    assert messenger.client.send_message.call_args[0][0] is peer


@pytest.mark.asyncio
async def test_the_forbidden_media_fallback_also_uses_the_resolved_peer(messenger):
    """Текстовый откат после `ForbiddenError` адресуется той же сущностью.

    Точка отправки третья и самая незаметная: она срабатывает только в
    группах, где запрещены медиа. Без собственного теста она остаётся с
    голым числом, и отказ всплывает не на прогоне, а в бою и только у части
    групп — то есть выглядит как беда конкретной группы, а не как дефект.
    """
    peer = object()
    messenger.client.get_input_entity = AsyncMock(return_value=peer)
    messenger.client.send_file = AsyncMock(
        side_effect=ForbiddenError(request=None, message="CHAT_SEND_MEDIA_FORBIDDEN")
    )
    messenger.client.send_message = AsyncMock()

    with patch(
        "app.messengers.telegram_user.httpx.AsyncClient",
        return_value=_http_client_returning_image_bytes(),
    ):
        result = await messenger.send_message(
            "-100123", "Hello!", images=["https://cdn.example.com/bucket/img.jpg"]
        )

    assert result["ok"] is True
    assert messenger.client.send_message.call_args[0][0] is peer


@pytest.mark.asyncio
async def test_a_cold_entity_cache_is_warmed_exactly_once(messenger):
    """Холодный кэш сущностей прогревается одним `get_dialogs` и ровно раз.

    Клиент создаётся заново на каждую отправку, поэтому кэш сущностей пуст и
    первый `get_input_entity` законно поднимает `ValueError`. Прогрев обязан
    стоить РОВНО один запрос: `get_dialogs()` у свежего клиента не бесплатен,
    а отправка идёт по расписанию раз за разом.
    """
    peer = object()
    messenger.client.get_input_entity = AsyncMock(side_effect=[ValueError("cold"), peer])
    messenger.client.get_dialogs = AsyncMock(return_value=[])
    messenger.client.send_message = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is True
    assert messenger.client.get_dialogs.await_count == 1
    assert messenger.client.get_input_entity.await_count == 2
    assert messenger.client.send_message.call_args[0][0] is peer


@pytest.mark.asyncio
async def test_a_peer_that_stays_unresolved_reads_as_a_lost_group(messenger):
    """Неразрешимый peer — это «группа потеряна», а не неизвестный сбой.

    `ValueError` из `get_input_entity` после прогрева типом неотличим от
    любого другого `ValueError` в теле отправки и утекал в catch-all, показывая
    пользователю английскую строку. Здесь же закреплён потолок прогрева:
    второй `get_dialogs` превратил бы навсегда потерянную группу, которой
    расписание шлёт отправку раз за разом, в источник FloodWait на аккаунте.
    """
    messenger.client.get_input_entity = AsyncMock(side_effect=ValueError("cold"))
    messenger.client.get_dialogs = AsyncMock(return_value=[])
    messenger.client.send_message = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is False
    assert result["no_retry"] is True
    assert result["error"] == PEER_UNREACHABLE_MESSAGE
    assert messenger.client.get_dialogs.await_count == 1
    messenger.client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_peer_id_invalid_is_not_reported_to_the_user_in_english(messenger):
    """Отказ сервера PEER_ID_INVALID доходит до экрана по-русски.

    `result["error"]` уезжает в `group.last_error` и в `SendLog`, то есть прямо
    в историю отправок пользователя. `str(e)` от telethon несёт имя класса
    запроса и подсказку про ботов — это строка лога, а не текст экрана.
    Отсутствие подстроки "Peer" и есть проверка того, что наружу ушла
    константа, а не текст библиотеки.
    """
    messenger.client.send_message = AsyncMock(side_effect=PeerIdInvalidError(request=None))

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is False
    assert result["no_retry"] is True
    assert result["error"] == PEER_UNREACHABLE_MESSAGE
    assert "Peer" not in result["error"]


@pytest.mark.asyncio
async def test_get_groups(messenger):
    mock_dialog1 = MagicMock()
    mock_dialog1.is_group = True
    mock_dialog1.id = -100123
    mock_dialog1.title = "Test Group"

    mock_dialog2 = MagicMock()
    mock_dialog2.is_group = False
    mock_dialog2.id = 456
    mock_dialog2.title = "Some User"

    messenger.client.get_dialogs = AsyncMock(return_value=[mock_dialog1, mock_dialog2])
    groups = await messenger.get_groups()
    assert len(groups) == 1
    assert groups[0]["id"] == "-100123"
    assert groups[0]["name"] == "Test Group"


@pytest.mark.asyncio
async def test_check_connection_success(messenger):
    messenger.client.get_me = AsyncMock()
    assert await messenger.check_connection() is True


@pytest.mark.asyncio
async def test_check_connection_failure(messenger):
    messenger.client.get_me = AsyncMock(side_effect=Exception("Session expired"))
    assert await messenger.check_connection() is False


# --- QR Auth function tests ---


@pytest.mark.asyncio
async def test_start_qr_auth():
    with patch("app.messengers.telegram_user.TelegramClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_qr_login = AsyncMock()
        mock_qr_login.url = "tg://login?token=abc123"
        mock_qr_login.wait = AsyncMock()
        mock_client.qr_login = AsyncMock(return_value=mock_qr_login)
        MockClient.return_value = mock_client

        session_id, url = await start_qr_auth(api_id=12345, api_hash="test_hash", user_id=OWNER)

    assert session_id is not None
    assert url == "tg://login?token=abc123"
    assert session_id in _qr_sessions
    # Cleanup
    cleanup_qr_session(session_id)


def test_get_qr_status_missing():
    result = get_qr_status("nonexistent", OWNER)
    assert result["status"] == "gone", (
        "неизвестная сессия отвечает не «не найдена» — различие «истекла / не найдена» "
        "видит только владелец (D-04)"
    )


def test_get_qr_status_waiting():
    import time
    _qr_sessions["test123"] = QRAuthState(
        client=AsyncMock(), user_id=OWNER, status="waiting", created_at=time.time()
    )
    result = get_qr_status("test123", OWNER)
    assert result["status"] == "waiting"
    _qr_sessions.pop("test123", None)


@pytest.mark.asyncio
async def test_submit_2fa_expired():
    with pytest.raises(RuntimeError, match="Сессия авторизации истекла"):
        await submit_2fa("nonexistent", OWNER, "password")


@pytest.mark.asyncio
async def test_complete_auth():
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()
    _qr_sessions["complete_test"] = QRAuthState(
        client=mock_client, user_id=OWNER, session_string="saved_session_123", status="success"
    )
    result = await complete_auth("complete_test", OWNER)
    assert result == "saved_session_123"
    assert "complete_test" not in _qr_sessions


def test_cleanup_qr_session():
    mock_client = AsyncMock()
    _qr_sessions["cleanup_test"] = QRAuthState(client=mock_client, user_id=OWNER)
    cleanup_qr_session("cleanup_test")
    assert "cleanup_test" not in _qr_sessions


def test_cleanup_qr_session_nonexistent():
    cleanup_qr_session("does_not_exist")  # Should not raise


# --- «Код истёк» — статус, а не ошибка (Фаза 13, план 13-03; D-03) ---------


def _telethon_client_stub() -> MagicMock:
    """Клиент Telethon для НАСТОЯЩЕГО `QRLogin`: обработчики событий синхронны.

    `QRLogin.wait()` вешает обработчик `UpdateLoginToken` и снимает его в
    `finally` — у настоящего клиента оба вызова синхронные, у заглушки тоже.
    Вызов клиента (запрос `ExportLoginToken` в `recreate`) — корутина.
    """
    client = MagicMock()
    client.add_event_handler = MagicMock()
    client.remove_event_handler = MagicMock()
    client.disconnect = AsyncMock()
    return client


def _real_qr_login(client, *, expires_in: float, token: bytes = b"x") -> QRLogin:
    """НАСТОЯЩИЙ `QRLogin` с ответом токена, истекающим через `expires_in` с."""
    qr_login = QRLogin(client, [])
    qr_login._resp = SimpleNamespace(
        expires=datetime.datetime.now(tz=datetime.timezone.utc)
        + datetime.timedelta(seconds=expires_in),
        token=token,
    )
    return qr_login


@pytest.mark.asyncio
async def test_an_expired_qr_token_is_a_status_not_an_error():
    """Таймаут `QRLogin.wait()` — статус `qr_expired`, без ошибки и трассировки (D-03).

    ⚠️ ТАЙМАУТ ВОСПРОИЗВОДИТСЯ НАСТОЯЩИМ `QRLogin`, А НЕ ПОДМЕНОЙ `wait()`
    (CONTEXT §Landmines). `wait()` сам считает таймаут как `expires − now` и
    поднимает `asyncio.TimeoutError` из `wait_for` — ровно то, что через ~30 с
    получает эксплуатация. Правило, ставящее `status` напрямую, зеленело бы
    вакуумом. Токен QR живёт ~30 с, сессия — 300 с: истёкший токен — «код
    истёк» с кнопкой, а не «Ошибка авторизации» без выхода.
    """
    client = _telethon_client_stub()
    state = QRAuthState(
        client=client, user_id=OWNER, qr_login=_real_qr_login(client, expires_in=0.05)
    )
    _qr_sessions["sid-token-expired"] = state
    try:
        with patch("app.messengers.telegram_user.logger") as module_logger:
            await _wait_for_qr("sid-token-expired")

        assert client.add_event_handler.called, (
            "настоящий `QRLogin.wait()` не вешал обработчик — таймаут не воспроизведён"
        )
        assert state.status == "qr_expired", (
            f"истёкший токен QR дал status={state.status!r} error={state.error!r} "
            "вместо «код истёк» — человек увидит «Ошибку авторизации» без выхода (D-03)"
        )
        assert not state.error, f"истёкший токен QR записал ошибку {state.error!r}"
        assert not module_logger.error.called, (
            "нормальное истечение кода записано в журнал как ошибка: "
            f"{module_logger.error.call_args!r}"
        )
        assert get_qr_status("sid-token-expired", OWNER) == {"status": "qr_expired"}, (
            "опрос не узнает, что код истёк"
        )
    finally:
        _qr_sessions.pop("sid-token-expired", None)


# --- «Обновить QR-код» — только из «код истёк» и только в сроке (D-03) -------


class _ExpiredCodeDouble:
    """Объект кода Telethon для правил `refresh_qr`: `recreate` и адрес кода.

    `wait()` ждёт вечно — новая задача ожидания, которую запускает
    `refresh_qr`, должна жить до отмены, а не завершаться сама.
    """

    def __init__(self):
        self.recreate = AsyncMock()
        self.url = "tg://login?token=renewed"
        self._never = asyncio.Event()

    async def wait(self, timeout=None):
        await self._never.wait()


async def _cancel_wait_task(state: QRAuthState) -> None:
    if state._wait_task:
        state._wait_task.cancel()
        await asyncio.gather(state._wait_task, return_exceptions=True)


@pytest.mark.asyncio
async def test_refresh_qr_recreates_only_an_expired_code():
    """Пересоздание пускается ТОЛЬКО из `qr_expired` (D-03, RESEARCH §Pattern 4).

    Подделанный запрос из `success` или `needs_2fa` иначе вернул бы сессию в
    `waiting` и стёр бы готовый вход; из `waiting` — выпустил бы лишний код.
    """
    code = _ExpiredCodeDouble()
    issued_at = time.time() - 100
    state = QRAuthState(
        client=MagicMock(), user_id=OWNER, qr_login=code, status="qr_expired",
        created_at=issued_at,
    )
    _qr_sessions["sid-renew"] = state
    try:
        url = await refresh_qr("sid-renew", OWNER)

        assert code.recreate.await_count == 1, (
            f"`recreate` ожидан {code.recreate.await_count} раз вместо одного — "
            "истёкший код не обновлён"
        )
        assert url == "tg://login?token=renewed", f"refresh_qr вернул {url!r} вместо адреса кода"
        assert state.status == "waiting", f"после обновления статус {state.status!r}"
        assert state.created_at > issued_at, "срок сессии не отсчитывается от нового кода"
        assert state._wait_task is not None and not state._wait_task.done(), (
            "новая задача ожидания сканирования не запущена — новый код не отсканировать"
        )
    finally:
        await _cancel_wait_task(state)
        _qr_sessions.pop("sid-renew", None)

    for status in ("waiting", "needs_2fa", "success"):
        other = _ExpiredCodeDouble()
        live = QRAuthState(client=MagicMock(), user_id=OWNER, qr_login=other, status=status)
        _qr_sessions["sid-live"] = live
        try:
            result = await refresh_qr("sid-live", OWNER)

            assert not other.recreate.await_count, (
                f"`recreate` не ожидался из статуса {status!r} — готовый вход стёрт "
                "подделанным запросом (D-03)"
            )
            assert result is None, f"refresh_qr из {status!r} вернул {result!r} вместо None"
            assert live.status == status, (
                f"refresh_qr сменил статус {status!r} на {live.status!r}"
            )
            assert live._wait_task is None, f"refresh_qr из {status!r} запустил ожидание"
        finally:
            await _cancel_wait_task(live)
            _qr_sessions.pop("sid-live", None)


@pytest.mark.asyncio
async def test_refresh_qr_does_not_revive_an_outdated_session():
    """Сессия старше `QR_SESSION_TTL` не оживает (RESEARCH §Pitfall 2).

    Чистка по сроку зовётся только из `start_qr_auth`, поэтому устаревшая
    сессия может лежать в памяти; без проверки срока «Обновить QR-код» через
    10 минут простоя выдал бы новый код вместо «Сессия истекла».
    """
    code = _ExpiredCodeDouble()
    state = QRAuthState(
        client=MagicMock(),
        user_id=OWNER,
        qr_login=code,
        status="qr_expired",
        created_at=time.time() - QR_SESSION_TTL - 1,
    )
    _qr_sessions["sid-outdated"] = state
    try:
        result = await refresh_qr("sid-outdated", OWNER)

        assert not code.recreate.await_count, (
            "`recreate` не ожидался: сессия старше срока ожила новым кодом (Pitfall 2)"
        )
        assert result is None, f"refresh_qr устаревшей сессии вернул {result!r} вместо None"
        assert state.status == "qr_expired", f"статус устаревшей сессии сменился на {state.status!r}"
    finally:
        await _cancel_wait_task(state)
        _qr_sessions.pop("sid-outdated", None)


# --- Сессия принадлежит тому, кто её начал (Фаза 13, план 13-04; D-04) --------
#
# ⚠️ ПРОВЕРКА ВЛАДЕЛЬЦА — ЕДИНСТВЕННАЯ ЗАЩИТА ОТ СОХРАНЕНИЯ ЧУЖОГО АККАУНТА.
# `session_id` пишется в журнал (`qr_auth_error`, `qr_refresh_error`), поэтому
# знать чужой `session_id` может любой читатель журнала. Правила ниже меряют
# слой сессий: чужая сессия для него — то же, что отсутствующая, и чужой вызов
# не трогает её ни снятием, ни отменой ожидания.


class _WaitForever:
    """Код Telethon, чьё ожидание сканирования живёт до отмены."""

    def __init__(self):
        self.url = "tg://login?token=owned"
        self._never = asyncio.Event()

    async def wait(self, timeout=None):
        await self._never.wait()


@pytest.mark.asyncio
async def test_a_session_is_owned_by_the_user_who_started_it():
    """Настоящий `start_qr_auth` пишет владельца в состояние сессии (D-04)."""
    with patch("app.messengers.telegram_user.TelegramClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.qr_login = AsyncMock(return_value=_WaitForever())
        MockClient.return_value = mock_client

        session_id, _ = await start_qr_auth(api_id=12345, api_hash="test_hash", user_id=OWNER)

    try:
        assert _qr_sessions[session_id].user_id == OWNER, (
            f"сессия записана на {_qr_sessions[session_id].user_id!r} вместо начавшего "
            "её пользователя — чужой запрос нечем отличить от своего (D-04)"
        )
    finally:
        await _cancel_wait_task(_qr_sessions[session_id])
        _qr_sessions.pop(session_id, None)


def test_a_foreign_user_sees_no_session():
    """Чужая сессия для слоя — отсутствующая: `gone`, как у неизвестной (D-04)."""
    _qr_sessions["sid-owned"] = QRAuthState(
        client=MagicMock(), user_id=OWNER, status="success", session_string="s"
    )
    try:
        assert get_qr_status("sid-owned", STRANGER) == {"status": "gone"}, (
            "посторонний узнал статус чужой сессии — её существование раскрыто (D-04)"
        )
        assert get_qr_status("sid-no-such", STRANGER) == {"status": "gone"}, (
            "неизвестная сессия отвечает иначе, чем чужая"
        )
        assert get_qr_status("sid-owned", OWNER) == {"status": "success"}, (
            "владелец не видит статуса своей сессии"
        )
    finally:
        _qr_sessions.pop("sid-owned", None)


@pytest.mark.asyncio
async def test_a_foreign_complete_leaves_the_session_alone():
    """Чужой `complete_auth` — None; сессия, её ожидание и клиент не тронуты (D-04)."""
    client = MagicMock()
    client.disconnect = AsyncMock()
    wait_task = MagicMock()
    state = QRAuthState(
        client=client, user_id=OWNER, status="success", session_string="owner-session"
    )
    state._wait_task = wait_task
    _qr_sessions["sid-victim"] = state
    try:
        assert await complete_auth("sid-victim", STRANGER) is None, (
            "посторонний получил строку чужой сессии Telegram (D-04)"
        )
        assert "sid-victim" in _qr_sessions, "чужой вызов снял сессию владельца (D-04)"
        assert not wait_task.cancel.called, "чужой вызов отменил ожидание сканирования владельца"
        assert not client.disconnect.await_count, "чужой вызов отключил клиента владельца"

        assert await complete_auth("sid-victim", OWNER) == "owner-session", (
            "владелец после чужого вызова не получил строку своей сессии"
        )
        assert "sid-victim" not in _qr_sessions, "сессия пережила завершение владельцем"
    finally:
        _qr_sessions.pop("sid-victim", None)


@pytest.mark.asyncio
async def test_complete_auth_takes_only_a_successful_session():
    """`complete_auth` вне `success` — None, сессия цела (D-01).

    Правило «звать только при успехе» закреплено слоем: вызов в ином статусе
    молча уничтожал бы живую сессию.
    """
    client = MagicMock()
    client.disconnect = AsyncMock()
    _qr_sessions["sid-still-waiting"] = QRAuthState(client=client, user_id=OWNER, status="waiting")
    try:
        assert await complete_auth("sid-still-waiting", OWNER) is None, (
            "complete_auth в ожидании вернул строку сессии"
        )
        assert "sid-still-waiting" in _qr_sessions, (
            "complete_auth в ожидании снял живую сессию — сканирование потеряно (D-01)"
        )
        assert not client.disconnect.await_count, "complete_auth в ожидании отключил клиента"
    finally:
        _qr_sessions.pop("sid-still-waiting", None)


@pytest.mark.asyncio
async def test_concurrent_completes_yield_one_session_string():
    """Два конкурентных `complete_auth` владельца — одна строка сессии (D-01).

    Проверка владельца стоит перед `pop` без ожидания между ними: точка
    переключения в `disconnect` отдаёт управление второму вызову уже ПОСЛЕ
    снятия, и ему достаётся пустота.
    """
    client = MagicMock()

    async def disconnect():
        await asyncio.sleep(0)

    client.disconnect = AsyncMock(side_effect=disconnect)
    _qr_sessions["sid-race"] = QRAuthState(
        client=client, user_id=OWNER, status="success", session_string="one-scan"
    )
    try:
        results = await asyncio.gather(
            complete_auth("sid-race", OWNER), complete_auth("sid-race", OWNER)
        )
        assert [r for r in results if r] == ["one-scan"], (
            f"два конкурентных завершения дали {results!r} — одно сканирование, "
            "два аккаунта (D-01)"
        )
    finally:
        _qr_sessions.pop("sid-race", None)


def test_a_late_scan_is_still_a_success():
    """Сканирование, завершённое после срока, но до чистки, — успех (Pitfall 10).

    Срок не меняется (D-13): сканирование на 299-й секунде не должно стать
    «истекло» на 301-й. Та же давность в ожидании — «истекло».
    """
    late = time.time() - QR_SESSION_TTL - 5
    _qr_sessions["sid-late"] = QRAuthState(
        client=MagicMock(), user_id=OWNER, status="success", session_string="s",
        created_at=late,
    )
    _qr_sessions["sid-stale"] = QRAuthState(
        client=MagicMock(), user_id=OWNER, status="waiting", created_at=late
    )
    try:
        assert get_qr_status("sid-late", OWNER) == {"status": "success"}, (
            "отсканированная сессия после срока ответила «истекло» — вход потерян"
        )
        assert get_qr_status("sid-stale", OWNER) == {"status": "expired"}, (
            "ожидание старше срока не истекло"
        )
    finally:
        _qr_sessions.pop("sid-late", None)
        _qr_sessions.pop("sid-stale", None)


@pytest.mark.asyncio
async def test_a_foreign_refresh_changes_nothing():
    """Чужой `refresh_qr` — None; код не пересоздан, сессия владельца та же (D-04).

    Иначе посторонний пересоздавал бы код жертвы, сбрасывал её срок и
    перезапускал ожидание сканирования — чужой QR на чужом экране.
    """
    code = _ExpiredCodeDouble()
    issued_at = time.time() - 100
    wait_task = MagicMock()
    state = QRAuthState(
        client=MagicMock(), user_id=OWNER, qr_login=code, status="qr_expired",
        created_at=issued_at,
    )
    state._wait_task = wait_task
    _qr_sessions["sid-foreign-renew"] = state
    try:
        result = await refresh_qr("sid-foreign-renew", STRANGER)

        assert not code.recreate.await_count, (
            "`recreate` не ожидался: посторонний пересоздал код чужой сессии (D-04)"
        )
        assert result is None, f"чужой refresh_qr вернул {result!r} вместо None"
        assert state.status == "qr_expired", f"чужой refresh_qr сменил статус на {state.status!r}"
        assert state.created_at == issued_at, "чужой refresh_qr сбросил срок сессии владельца"
        assert state._wait_task is wait_task, "чужой refresh_qr подменил задачу ожидания"
        assert not wait_task.cancel.called, "чужой refresh_qr отменил ожидание владельца"
    finally:
        # Без проверки владельца `refresh_qr` запустил бы настоящую задачу
        # ожидания — её отменяют внутри цикла событий теста.
        if not isinstance(state._wait_task, MagicMock):
            await _cancel_wait_task(state)
        _qr_sessions.pop("sid-foreign-renew", None)


@pytest.mark.asyncio
async def test_a_foreign_password_is_never_submitted():
    """Чужой `submit_2fa` — отказ «Сессия истекла»; пароль в Telegram не уходит (D-04)."""
    client = AsyncMock()
    client.session = MagicMock()
    client.session.save.return_value = "owner-session"
    state = QRAuthState(client=client, user_id=OWNER, status="needs_2fa")
    _qr_sessions["sid-foreign-2fa"] = state
    try:
        with pytest.raises(RuntimeError) as refused:
            await submit_2fa("sid-foreign-2fa", STRANGER, "x")

        assert str(refused.value) == "Сессия авторизации истекла. Начните заново.", (
            f"чужой submit_2fa отказал текстом {str(refused.value)!r}"
        )
        assert not client.sign_in.await_count, (
            "`sign_in` не ожидался: пароль постороннего ушёл в Telegram на чужой сессии (D-04)"
        )
        assert state.status == "needs_2fa", f"чужой submit_2fa сменил статус на {state.status!r}"
        assert state.session_string is None, "чужой submit_2fa записал строку сессии"
    finally:
        _qr_sessions.pop("sid-foreign-2fa", None)


@pytest.mark.asyncio
async def test_get_groups_logs_error_on_failure(messenger, caplog):
    """Протухшая сессия Telethon — отказ, а не аккаунт без единой группы.

    Раньше исключение только логировалось, наружу уходил `[]`, и полная
    переинвентаризация (D-10) помечала пропавшими все группы аккаунта разом,
    записав при этом сводку успеха.
    """
    import logging
    messenger.client.get_dialogs = AsyncMock(side_effect=Exception("Session expired"))

    with caplog.at_level(logging.ERROR, logger="app.messengers.telegram_user"):
        with pytest.raises(MessengerFetchError) as exc_info:
            await messenger.get_groups()

    assert "Session expired" in str(exc_info.value)
    assert any("get_groups_error" in r.message or "Session expired" in r.message for r in caplog.records)
    # Сессия закрывается и на пути отказа: `finally` обязан пережить raise.
    messenger.client.disconnect.assert_awaited()


@pytest.mark.asyncio
async def test_check_connection_logs_warning_on_failure(messenger, caplog):
    """check_connection logs warning when check fails."""
    import logging
    messenger.client.get_me = AsyncMock(side_effect=Exception("Auth key expired"))

    with caplog.at_level(logging.WARNING, logger="app.messengers.telegram_user"):
        result = await messenger.check_connection()

    assert result is False
    assert any("check_connection_failed" in r.message or "Auth key expired" in r.message for r in caplog.records)

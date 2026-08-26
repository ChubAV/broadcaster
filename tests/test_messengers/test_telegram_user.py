import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from telethon.errors import ForbiddenError, PeerIdInvalidError
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
    QRAuthState,
)


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

        session_id, url = await start_qr_auth(api_id=12345, api_hash="test_hash")

    assert session_id is not None
    assert url == "tg://login?token=abc123"
    assert session_id in _qr_sessions
    # Cleanup
    cleanup_qr_session(session_id)


def test_get_qr_status_missing():
    result = get_qr_status("nonexistent")
    assert result["status"] == "expired"


def test_get_qr_status_waiting():
    import time
    _qr_sessions["test123"] = QRAuthState(
        client=AsyncMock(), status="waiting", created_at=time.time()
    )
    result = get_qr_status("test123")
    assert result["status"] == "waiting"
    _qr_sessions.pop("test123", None)


@pytest.mark.asyncio
async def test_submit_2fa_expired():
    with pytest.raises(RuntimeError, match="Сессия авторизации истекла"):
        await submit_2fa("nonexistent", "password")


@pytest.mark.asyncio
async def test_complete_auth():
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()
    _qr_sessions["complete_test"] = QRAuthState(
        client=mock_client, session_string="saved_session_123", status="success"
    )
    result = await complete_auth("complete_test")
    assert result == "saved_session_123"
    assert "complete_test" not in _qr_sessions


def test_cleanup_qr_session():
    mock_client = AsyncMock()
    _qr_sessions["cleanup_test"] = QRAuthState(client=mock_client)
    cleanup_qr_session("cleanup_test")
    assert "cleanup_test" not in _qr_sessions


def test_cleanup_qr_session_nonexistent():
    cleanup_qr_session("does_not_exist")  # Should not raise


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

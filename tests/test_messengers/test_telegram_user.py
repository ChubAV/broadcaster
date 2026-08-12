import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.base import MessengerFetchError
from app.messengers.telegram_user import (
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
    messenger.client.send_file = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.raise_for_status = MagicMock()
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)

    with patch("app.messengers.telegram_user.httpx.AsyncClient", return_value=mock_http):
        result = await messenger.send_message(
            "-100123", "Hello!", images=["https://cdn.example.com/bucket/img.jpg"]
        )
    assert result["ok"] is True
    messenger.client.send_file.assert_called_once()
    # Verify BytesIO with filename was passed
    sent_files = messenger.client.send_file.call_args[0][1]
    assert len(sent_files) == 1
    assert sent_files[0].name == "img.jpg"
    assert sent_files[0].read() == b"fake-image-bytes"


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

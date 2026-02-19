import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.telegram_user import (
    TelegramUserMessenger,
    start_auth,
    verify_code,
    verify_password,
    cleanup_auth_client,
    _auth_clients,
)


@pytest.fixture
def messenger():
    with patch("app.messengers.telegram_user.Client") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        m = TelegramUserMessenger(
            session_string="fake-session",
            api_id=12345,
            api_hash="fake-api-hash",
        )
        # Replace client with our mock that supports async context manager
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
    messenger.client.send_photo = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!", images=["path/to/img.jpg"])

    assert result["ok"] is True
    messenger.client.send_photo.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_error(messenger):
    messenger.client.send_message = AsyncMock(side_effect=Exception("Flood wait"))

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is False
    assert "Flood wait" in result["error"]


@pytest.mark.asyncio
async def test_get_groups(messenger):
    mock_dialog1 = MagicMock()
    mock_dialog1.chat.type = "supergroup"
    mock_dialog1.chat.id = -100123
    mock_dialog1.chat.title = "Test Group"

    mock_dialog2 = MagicMock()
    mock_dialog2.chat.type = "private"
    mock_dialog2.chat.id = 456
    mock_dialog2.chat.title = "Some User"

    async def mock_get_dialogs():
        for d in [mock_dialog1, mock_dialog2]:
            yield d

    messenger.client.get_dialogs = mock_get_dialogs

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


# --- Auth functions tests ---


@pytest.mark.asyncio
async def test_start_auth_success():
    with patch("app.messengers.telegram_user.Client") as MockClient:
        mock_client = AsyncMock()
        mock_sent_code = MagicMock()
        mock_sent_code.phone_code_hash = "abc123hash"
        mock_client.send_code = AsyncMock(return_value=mock_sent_code)
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        MockClient.return_value = mock_client

        result = await start_auth(
            auth_session_id=100,
            phone="+79001234567",
            api_id=12345,
            api_hash="test_hash",
        )

    assert result == "abc123hash"
    assert 100 in _auth_clients
    # Cleanup
    _auth_clients.pop(100, None)


@pytest.mark.asyncio
async def test_start_auth_error_disconnects():
    with patch("app.messengers.telegram_user.Client") as MockClient:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.send_code = AsyncMock(side_effect=Exception("Phone invalid"))
        MockClient.return_value = mock_client

        with pytest.raises(Exception, match="Phone invalid"):
            await start_auth(
                auth_session_id=101,
                phone="+invalid",
                api_id=12345,
                api_hash="test_hash",
            )

    mock_client.disconnect.assert_called_once()
    assert 101 not in _auth_clients


@pytest.mark.asyncio
async def test_verify_code_success():
    mock_client = AsyncMock()
    mock_client.sign_in = AsyncMock()
    mock_client.export_session_string = AsyncMock(return_value="session_str_123")
    mock_client.disconnect = AsyncMock()

    import time
    _auth_clients[200] = (mock_client, time.time())

    result = await verify_code(
        auth_session_id=200,
        phone="+79001234567",
        phone_code_hash="hash123",
        code="12345",
    )

    assert result == "session_str_123"
    assert 200 not in _auth_clients
    mock_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_verify_code_expired_session():
    # No client in _auth_clients
    with pytest.raises(RuntimeError, match="Сессия авторизации истекла"):
        await verify_code(
            auth_session_id=999,
            phone="+79001234567",
            phone_code_hash="hash",
            code="12345",
        )


@pytest.mark.asyncio
async def test_verify_code_needs_2fa():
    from pyrogram.errors import SessionPasswordNeeded

    mock_client = AsyncMock()
    mock_client.sign_in = AsyncMock(side_effect=SessionPasswordNeeded())
    mock_client.disconnect = AsyncMock()

    import time
    _auth_clients[201] = (mock_client, time.time())

    with pytest.raises(SessionPasswordNeeded):
        await verify_code(
            auth_session_id=201,
            phone="+79001234567",
            phone_code_hash="hash123",
            code="12345",
        )

    # Client should still be in store for 2FA step
    assert 201 in _auth_clients
    _auth_clients.pop(201, None)


@pytest.mark.asyncio
async def test_verify_password_success():
    mock_client = AsyncMock()
    mock_client.check_password = AsyncMock()
    mock_client.export_session_string = AsyncMock(return_value="session_2fa_str")
    mock_client.disconnect = AsyncMock()

    import time
    _auth_clients[300] = (mock_client, time.time())

    result = await verify_password(
        auth_session_id=300,
        password="my2fapassword",
    )

    assert result == "session_2fa_str"
    assert 300 not in _auth_clients


@pytest.mark.asyncio
async def test_verify_password_expired_session():
    with pytest.raises(RuntimeError, match="Сессия авторизации истекла"):
        await verify_password(
            auth_session_id=999,
            password="password",
        )


def test_cleanup_auth_client():
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()

    import time
    _auth_clients[400] = (mock_client, time.time())

    cleanup_auth_client(400)

    assert 400 not in _auth_clients


def test_cleanup_auth_client_nonexistent():
    # Should not raise
    cleanup_auth_client(99999)

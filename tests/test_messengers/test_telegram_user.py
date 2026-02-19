import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.telegram_user import TelegramUserMessenger


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

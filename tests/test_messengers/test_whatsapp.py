import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.whatsapp import WhatsAppMessenger


@pytest.mark.asyncio
async def test_send_message_success():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!")
        assert result["ok"] is True
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/send"


@pytest.mark.asyncio
async def test_send_message_with_image():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!", images=["path/to/img.jpg"])
        assert result["ok"] is True
        assert mock_client.post.call_count == 1
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/send"
        assert call_args[1]["json"]["image_paths"] == ["path/to/img.jpg"]


@pytest.mark.asyncio
async def test_send_message_with_multiple_images():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!", images=["img1.jpg", "img2.jpg"])
        assert result["ok"] is True
        # Single request with all images batched
        assert mock_client.post.call_count == 1
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["image_paths"] == ["img1.jpg", "img2.jpg"]
        assert call_args[1]["json"]["text"] == "Hello!"


@pytest.mark.asyncio
async def test_send_message_failure():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal error"

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!")
        assert result["ok"] is False
        assert "Internal error" in result["error"]


@pytest.mark.asyncio
async def test_get_groups_success():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "group1", "name": "Test Group"},
        {"id": "group2", "name": "Another Group"},
    ]

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        groups = await messenger.get_groups()
        assert len(groups) == 2
        assert groups[0]["name"] == "Test Group"
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/groups"


@pytest.mark.asyncio
async def test_get_groups_failure():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        groups = await messenger.get_groups()
        assert groups == []


@pytest.mark.asyncio
async def test_check_connection_connected():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": True}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        assert await messenger.check_connection() is True
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/status"


@pytest.mark.asyncio
async def test_check_connection_disconnected():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": False}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        assert await messenger.check_connection() is False


@pytest.mark.asyncio
async def test_check_connection_bridge_down():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        assert await messenger.check_connection() is False


@pytest.mark.asyncio
async def test_start_session():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.start_session()
        assert result is True
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/start"


@pytest.mark.asyncio
async def test_destroy_session():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.destroy_session()
        assert result is True
        call_args = mock_client.delete.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42"


@pytest.mark.asyncio
async def test_get_qr():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "qr", "qr": "data:image/png;base64,abc123"}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.get_qr()
        assert result["status"] == "qr"
        assert result["qr"] == "data:image/png;base64,abc123"
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/qr"

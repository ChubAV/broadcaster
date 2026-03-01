import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messengers.max import MaxMessenger


@pytest.mark.asyncio
async def test_send_message_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("123", "test text")
        assert result == {"ok": True}
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/send"


@pytest.mark.asyncio
async def test_send_message_with_images():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("123", "test text", images=["img1.jpg", "img2.jpg"])
        assert result["ok"] is True
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["image_urls"] == ["img1.jpg", "img2.jpg"]
        assert call_args[1]["json"]["text"] == "test text"


@pytest.mark.asyncio
async def test_send_message_http_500():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal error"}
    mock_response.text = "Internal error"

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("123", "test text")
        assert result["ok"] is False
        assert "500" in result["error"]


@pytest.mark.asyncio
async def test_send_message_403_no_retry():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {"error": "Forbidden"}
    mock_response.text = "Forbidden"

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("123", "test text")
        assert result["ok"] is False
        assert result["no_retry"] is True


@pytest.mark.asyncio
async def test_send_message_connection_error():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("123", "test text")
        assert result["ok"] is False
        assert "Connection" in result["error"]


@pytest.mark.asyncio
async def test_check_connection_true():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": True}

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.check_connection()
        assert result is True
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/status"


@pytest.mark.asyncio
async def test_check_connection_false():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": False}

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.check_connection()
        assert result is False


@pytest.mark.asyncio
async def test_check_connection_exception():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        result = await messenger.check_connection()
        assert result is False


@pytest.mark.asyncio
async def test_get_groups_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "1", "name": "Group 1"}]

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_groups()
        assert len(result) == 1
        assert result[0]["name"] == "Group 1"
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/groups"


@pytest.mark.asyncio
async def test_get_groups_error():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_groups()
        assert result == []


@pytest.mark.asyncio
async def test_get_groups_exception():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        mock_get_client.return_value = mock_client

        result = await messenger.get_groups()
        assert result == []


@pytest.mark.asyncio
async def test_get_sync_status_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"state": "ready", "groups": [{"id": "1", "name": "G"}]}

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_sync_status()
        assert result["state"] == "ready"
        assert len(result["groups"]) == 1
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/sync-status"


@pytest.mark.asyncio
async def test_get_sync_status_error():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_sync_status()
        assert result["state"] == "error"
        assert result["groups"] is None


@pytest.mark.asyncio
async def test_get_sync_status_exception():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        result = await messenger.get_sync_status()
        assert result["state"] == "error"
        assert result["groups"] is None


@pytest.mark.asyncio
async def test_start_session_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.start_session()
        assert result is True
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/start"


@pytest.mark.asyncio
async def test_start_session_with_phone():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.start_session(phone="+79001234567")
        assert result is True
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["phone"] == "+79001234567"


@pytest.mark.asyncio
async def test_start_session_failure():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.start_session()
        assert result is False


@pytest.mark.asyncio
async def test_destroy_session_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.destroy_session()
        assert result is True
        call_args = mock_client.delete.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1"


@pytest.mark.asyncio
async def test_destroy_session_failure():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        result = await messenger.destroy_session()
        assert result is False


@pytest.mark.asyncio
async def test_get_qr_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "qr", "qr": "data:image/png;base64,abc123"}

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_qr()
        assert result["status"] == "qr"
        assert result["qr"] == "data:image/png;base64,abc123"
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/qr"


@pytest.mark.asyncio
async def test_get_qr_error():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_qr()
        assert result["status"] == "error"
        assert result["qr"] is None


@pytest.mark.asyncio
async def test_retry_sync_success():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "syncing"}

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.retry_sync()
        assert result["status"] == "syncing"
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://fake:3000/api/sessions/1/retry-sync"


@pytest.mark.asyncio
async def test_retry_sync_error():
    messenger = MaxMessenger(bridge_url="http://fake:3000", session_id="1")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.max.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.retry_sync()
        assert result["status"] == "error"


def test_messenger_factory_creates_max():
    from unittest.mock import MagicMock
    from app.services.messenger_factory import create_messenger

    account = MagicMock()
    account.type = "max"
    account.id = 42

    settings = MagicMock()

    messenger = create_messenger(account, settings)
    assert isinstance(messenger, MaxMessenger)
    assert messenger.session_id == "42"
    assert messenger._bridge_url is None

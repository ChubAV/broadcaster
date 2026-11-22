import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.base import MessengerFetchError
from app.messengers.whatsapp import WhatsAppMessenger, ensure_wa_container


@patch("app.services.wa_container_manager.wait_for_container_ready")
@patch("app.services.wa_container_manager.start_container")
@patch("app.services.wa_container_manager.get_container_endpoint")
@patch("app.messengers.whatsapp.get_wa_endpoint")
def test_ensure_wa_container_replaces_stale_cached_endpoint(
    mock_get_wa_endpoint,
    mock_get_container_endpoint,
    mock_start_container,
    mock_wait_for_ready,
):
    mock_get_wa_endpoint.return_value = "http://wa-worker-42:3000"
    mock_get_container_endpoint.return_value = None
    mock_start_container.return_value = "http://wa-worker-42:3000"
    mock_wait_for_ready.return_value = True

    assert ensure_wa_container(42) == "http://wa-worker-42:3000"
    mock_start_container.assert_called_once_with(42)
    mock_wait_for_ready.assert_called_once_with(42)


@patch("app.services.wa_container_manager.wait_for_container_ready")
@patch("app.services.wa_container_manager.start_container")
@patch("app.services.wa_container_manager.get_container_endpoint")
@patch("app.messengers.whatsapp.get_wa_endpoint")
def test_ensure_wa_container_returns_none_when_worker_never_becomes_ready(
    mock_get_wa_endpoint,
    mock_get_container_endpoint,
    mock_start_container,
    mock_wait_for_ready,
):
    mock_get_wa_endpoint.return_value = None
    mock_get_container_endpoint.return_value = None
    mock_start_container.return_value = "http://wa-worker-42:3000"
    mock_wait_for_ready.return_value = False

    assert ensure_wa_container(42) is None


@pytest.mark.asyncio
async def test_send_message_success():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("group123", "Hello!")
        assert result["ok"] is True
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/send"


@pytest.mark.asyncio
async def test_send_message_with_image():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("group123", "Hello!", images=["path/to/img.jpg"])
        assert result["ok"] is True
        assert mock_client.post.call_count == 1
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/send"
        assert call_args[1]["json"]["image_urls"] == ["path/to/img.jpg"]


@pytest.mark.asyncio
async def test_send_message_with_multiple_images():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("group123", "Hello!", images=["img1.jpg", "img2.jpg"])
        assert result["ok"] is True
        # Single request with all images batched
        assert mock_client.post.call_count == 1
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["image_urls"] == ["img1.jpg", "img2.jpg"]
        assert call_args[1]["json"]["text"] == "Hello!"


@pytest.mark.asyncio
async def test_send_message_failure():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal error"}

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.send_message("group123", "Hello!")
        assert result["ok"] is False
        assert "500" in result["error"]
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

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        groups = await messenger.get_groups()
        assert len(groups) == 2
        assert groups[0]["name"] == "Test Group"
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/groups"


@pytest.mark.asyncio
async def test_get_groups_failure():
    """Не-200 от моста — это ОТКАЗ, а не пустой состав групп.

    Тест поднимает настоящий `WhatsAppMessenger` и подменяет только HTTP-слой:
    мок самого `get_groups` проверял бы контракт, которого у класса нет.
    Возврат `[]` здесь означал бы, что вызывающий примет молчание моста за
    авторитетную опись и пометит пропавшими все группы аккаунта.
    """
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        with pytest.raises(MessengerFetchError) as exc_info:
            await messenger.get_groups()

    assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_groups_empty_list_is_not_an_error():
    """Пустой ответ 200 — это РОВНО «групп нет», и он не исключение.

    Парная к test_get_groups_failure: различие пустоты и отказа — весь смысл
    `MessengerFetchError`, поэтому обе стороны различия закреплены.
    """
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        assert await messenger.get_groups() == []


@pytest.mark.asyncio
async def test_check_connection_connected():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": True}

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        assert await messenger.check_connection() is True
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/status"


@pytest.mark.asyncio
async def test_check_connection_disconnected():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": False}

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        assert await messenger.check_connection() is False


@pytest.mark.asyncio
async def test_check_connection_bridge_down():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        assert await messenger.check_connection() is False


def _status_client(*, status_code=200, body=None, json_raises=None, get_raises=None):
    """Подмена HTTP-клиента: один ответ `/status` или сбой на нужном шаге."""
    response = MagicMock()
    response.status_code = status_code
    if json_raises is not None:
        response.json.side_effect = json_raises
    else:
        response.json.return_value = body
    client = AsyncMock()
    client.get = AsyncMock(side_effect=get_raises) if get_raises else AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body, expected",
    [
        ({"connected": True, "phone": "79991234567"}, "79991234567"),
        ({"connected": True, "phone": 79991234567}, "79991234567"),
        ({"connected": True}, None),
        ({"connected": True, "phone": None}, None),
        ({"connected": True, "phone": ""}, None),
        ({"connected": True, "phone": True}, None),
        ({"connected": True, "phone": 0}, None),
        ({"connected": True, "phone": []}, None),
        (["79991234567"], None),
    ],
    ids=[
        "string", "integer", "old-shape", "null", "empty", "bool", "zero", "list", "not-a-dict",
    ],
)
async def test_get_own_phone_reads_only_a_usable_phone_field(body, expected):
    """D-14: `phone` — непустая строка или целое > 0; всё прочее — «неизвестен»."""
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    client = _status_client(body=body)

    with patch("app.messengers.whatsapp.get_http_client", return_value=client):
        assert await messenger.get_own_phone() == expected

    assert client.get.call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/status"


@pytest.mark.asyncio
async def test_get_own_phone_is_none_when_the_worker_answers_with_an_error_status():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    client = _status_client(status_code=500, body={"phone": "79991234567"})

    with patch("app.messengers.whatsapp.get_http_client", return_value=client):
        assert await messenger.get_own_phone() is None


@pytest.mark.asyncio
async def test_get_own_phone_is_none_when_the_body_is_not_json():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    client = _status_client(json_raises=ValueError("not json"))

    with patch("app.messengers.whatsapp.get_http_client", return_value=client):
        assert await messenger.get_own_phone() is None


@pytest.mark.asyncio
async def test_get_own_phone_logs_only_the_error_type_when_the_transport_fails():
    """PHONE-21: запись `get_own_phone_failed` без текста исключения."""
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    client = _status_client(get_raises=ConnectionError("refused 79991234567"))

    with patch("app.messengers.whatsapp.get_http_client", return_value=client):
        with patch.object(messenger, "log") as log:
            assert await messenger.get_own_phone() is None

    log.warning.assert_called_once_with("get_own_phone_failed", error_type="ConnectionError")


@pytest.mark.asyncio
async def test_start_session():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.start_session()
        assert result is True
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/start"


@pytest.mark.asyncio
async def test_destroy_session():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

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

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await messenger.get_qr()
        assert result["status"] == "qr"
        assert result["qr"] == "data:image/png;base64,abc123"
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://wa-bridge:3000/api/sessions/42/qr"


@pytest.mark.asyncio
async def test_send_message_logs_error_on_http_failure(caplog):
    """send_message logs error when HTTP call fails."""
    import logging
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.ERROR, logger="app.messengers.whatsapp"):
            result = await messenger.send_message("group123", "Hello!")

    assert result["ok"] is False
    assert any("send_message_error" in r.message or "Connection refused" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_get_groups_logs_error_on_failure(caplog):
    """get_groups logs error when HTTP call fails."""
    import logging
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.ERROR, logger="app.messengers.whatsapp"):
            with pytest.raises(MessengerFetchError):
                await messenger.get_groups()

    assert any("get_groups_error" in r.message or "Timeout" in r.message for r in caplog.records)

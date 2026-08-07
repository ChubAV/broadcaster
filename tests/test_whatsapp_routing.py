from unittest.mock import patch, MagicMock

import pytest

from app.messengers.whatsapp import get_wa_endpoint, ensure_wa_container, WhatsAppMessenger


class TestGetWaEndpoint:
    """Tests for Redis-based endpoint lookup."""

    @patch("app.config.get_settings")
    @patch("redis.from_url")
    def test_returns_endpoint_when_registered(self, mock_from_url, mock_settings):
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"http://wa-worker-42:3000"
        mock_from_url.return_value = mock_redis

        result = get_wa_endpoint(42)
        assert result == "http://wa-worker-42:3000"
        mock_redis.get.assert_called_once_with("wa:endpoint:42")
        mock_redis.close.assert_called_once()

    @patch("app.config.get_settings")
    @patch("redis.from_url")
    def test_returns_none_when_not_registered(self, mock_from_url, mock_settings):
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_from_url.return_value = mock_redis

        result = get_wa_endpoint(99)
        assert result is None
        mock_redis.close.assert_called_once()


class TestEnsureWaContainer:
    """Tests for ensure_wa_container with start-on-demand."""

    @patch("app.services.wa_container_manager.start_container")
    @patch("app.services.wa_container_manager.wait_for_container_ready")
    @patch("app.services.wa_container_manager.get_container_endpoint")
    @patch("app.messengers.whatsapp.get_wa_endpoint")
    def test_returns_existing_endpoint(
        self, mock_get_endpoint, mock_get_container_endpoint, mock_wait, mock_start
    ):
        # Кеш в Redis сам по себе не считается достоверным: эндпоинт возвращается
        # только когда Docker подтверждает, что контейнер жив и готов.
        mock_get_endpoint.return_value = "http://wa-worker-10:3000"
        mock_get_container_endpoint.return_value = "http://wa-worker-10:3000"
        mock_wait.return_value = True

        result = ensure_wa_container(10)
        assert result == "http://wa-worker-10:3000"
        mock_start.assert_not_called()

    @patch("app.services.wa_container_manager.wait_for_container_ready")
    @patch("app.services.wa_container_manager.start_container")
    @patch("app.messengers.whatsapp.get_wa_endpoint")
    def test_starts_container_when_not_registered(self, mock_get_endpoint, mock_start, mock_wait):
        mock_get_endpoint.return_value = None
        mock_start.return_value = "http://wa-worker-10:3000"
        mock_wait.return_value = True

        result = ensure_wa_container(10)
        assert result == "http://wa-worker-10:3000"
        mock_start.assert_called_once_with(10)
        mock_wait.assert_called_once_with(10)

    @patch("app.services.wa_container_manager.start_container")
    @patch("app.messengers.whatsapp.get_wa_endpoint")
    def test_returns_none_when_start_fails(self, mock_get_endpoint, mock_start):
        mock_get_endpoint.return_value = None
        mock_start.return_value = None

        result = ensure_wa_container(10)
        assert result is None


class TestWhatsAppMessengerDynamicRouting:
    """Tests for WhatsAppMessenger with dynamic bridge_url property."""

    def test_static_bridge_url(self):
        messenger = WhatsAppMessenger(bridge_url="http://static:3000", session_id="5")
        assert messenger.bridge_url == "http://static:3000"

    @patch("app.messengers.whatsapp.ensure_wa_container")
    def test_dynamic_bridge_url(self, mock_ensure):
        mock_ensure.return_value = "http://wa-worker-5:3000"
        messenger = WhatsAppMessenger(session_id="5")
        assert messenger.bridge_url == "http://wa-worker-5:3000"
        mock_ensure.assert_called_once_with(5)

    @patch("app.messengers.whatsapp.ensure_wa_container")
    def test_dynamic_bridge_url_raises_on_failure(self, mock_ensure):
        mock_ensure.return_value = None
        messenger = WhatsAppMessenger(session_id="5")
        with pytest.raises(RuntimeError, match="Cannot start wa-worker for account 5"):
            _ = messenger.bridge_url

    @patch("app.messengers.whatsapp.ensure_wa_container")
    def test_url_method_uses_dynamic_endpoint(self, mock_ensure):
        mock_ensure.return_value = "http://wa-worker-7:3000"
        messenger = WhatsAppMessenger(session_id="7")
        assert messenger._url("send") == "http://wa-worker-7:3000/api/sessions/7/send"

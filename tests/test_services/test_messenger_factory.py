import pytest
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.models.messenger_account import MessengerAccount
from app.services.messenger_factory import create_messenger
from app.messengers.telegram_user import TelegramUserMessenger
from app.messengers.whatsapp import WhatsAppMessenger


@patch("app.messengers.telegram_user.TelegramClient")
@patch("app.messengers.telegram_user.StringSession")
def test_create_telegram_user_messenger(mock_string_session, mock_client):
    account = MagicMock(spec=MessengerAccount)
    account.type = "tg_user"
    account.credentials = "session_string_here"
    account.id = 1

    settings = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
        telegram_api_id=12345,
        telegram_api_hash="abc123",
    )
    messenger = create_messenger(account, settings)
    assert isinstance(messenger, TelegramUserMessenger)


def test_create_whatsapp_messenger():
    account = MagicMock(spec=MessengerAccount)
    account.type = "wa"
    account.credentials = "session_id"
    account.id = 42

    settings = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
        wa_bridge_url="http://localhost:3000",
    )
    messenger = create_messenger(account, settings)
    assert isinstance(messenger, WhatsAppMessenger)


def test_create_unknown_type_raises():
    account = MagicMock(spec=MessengerAccount)
    account.type = "unknown"

    settings = Settings(database_url="sqlite:///:memory:", secret_key="test")
    with pytest.raises(ValueError, match="Unknown account type"):
        create_messenger(account, settings)

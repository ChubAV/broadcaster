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
        wa_bridge_urls=["http://localhost:3000"],
    )
    messenger = create_messenger(account, settings)
    assert isinstance(messenger, WhatsAppMessenger)


def test_create_unknown_type_raises():
    account = MagicMock(spec=MessengerAccount)
    account.type = "unknown"

    settings = Settings(database_url="sqlite:///:memory:", secret_key="test")
    with pytest.raises(ValueError, match="Unknown account type"):
        create_messenger(account, settings)


def test_create_whatsapp_messenger_uses_session_id():
    """WhatsApp messenger is created with session_id=str(account.id), no bridge_url."""
    account = MagicMock()
    account.type = "wa"
    account.id = 5
    account.credentials = ""

    settings = MagicMock()

    messenger = create_messenger(account, settings)
    assert isinstance(messenger, WhatsAppMessenger)
    assert messenger.session_id == "5"
    assert messenger._bridge_url is None


def test_create_whatsapp_single_account():
    """Each WA account gets its own messenger with matching session_id."""
    account = MagicMock()
    account.type = "wa"
    account.id = 42

    settings = MagicMock()

    messenger = create_messenger(account, settings)
    assert isinstance(messenger, WhatsAppMessenger)
    assert messenger.session_id == "42"
    assert messenger._bridge_url is None


@patch("app.services.messenger_factory.TelegramUserMessenger")
def test_create_messenger_tg_user_from_settings(mock_tg_messenger):
    """create_messenger uses telegram_api_id/api_hash from settings."""
    account = MessengerAccount(
        type="tg_user",
        credentials="session-string",
        user_id=1,
        status="active",
    )
    mock_settings = MagicMock()
    mock_settings.telegram_api_id = 12345
    mock_settings.telegram_api_hash = "settings_hash"

    m = create_messenger(account, mock_settings)
    mock_tg_messenger.assert_called_once_with(
        session_string="session-string",
        api_id=12345,
        api_hash="settings_hash",
    )
    assert m is mock_tg_messenger.return_value


@patch("app.services.messenger_factory.TelegramUserMessenger")
def test_create_messenger_tg_user_with_defaults(mock_tg_messenger):
    """create_messenger passes settings values even when zero/empty."""
    account = MessengerAccount(
        type="tg_user",
        credentials="session-string",
        user_id=1,
        status="active",
    )
    mock_settings = MagicMock()
    mock_settings.telegram_api_id = 0
    mock_settings.telegram_api_hash = ""

    m = create_messenger(account, mock_settings)
    mock_tg_messenger.assert_called_once_with(
        session_string="session-string",
        api_id=0,
        api_hash="",
    )
    assert m is mock_tg_messenger.return_value

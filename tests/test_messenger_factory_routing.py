import pytest
from unittest.mock import MagicMock

from app.services.messenger_factory import create_messenger
from app.messengers.whatsapp import WhatsAppMessenger


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

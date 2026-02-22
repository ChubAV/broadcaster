import pytest
from unittest.mock import MagicMock

from app.services.messenger_factory import create_messenger


def test_create_whatsapp_messenger_uses_routing():
    """WhatsApp messenger gets bridge URL based on account.id % len(bridges)."""
    account = MagicMock()
    account.type = "wa"
    account.id = 5
    account.credentials = ""

    settings = MagicMock()
    settings.wa_bridge_urls = [
        "http://bridge-0:3000",
        "http://bridge-1:3000",
        "http://bridge-2:3000",
    ]

    messenger = create_messenger(account, settings)
    # id=5 % 3 = 2 → bridge-2
    assert messenger.bridge_url == "http://bridge-2:3000"
    assert messenger.session_id == "5"


def test_create_whatsapp_single_bridge():
    """With a single bridge, all sessions go to it."""
    account = MagicMock()
    account.type = "wa"
    account.id = 42

    settings = MagicMock()
    settings.wa_bridge_urls = ["http://bridge:3000"]

    messenger = create_messenger(account, settings)
    assert messenger.bridge_url == "http://bridge:3000"

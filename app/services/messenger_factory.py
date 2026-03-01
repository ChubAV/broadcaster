from app.config import Settings
from app.messengers.base import BaseMessenger
from app.messengers.max import MaxMessenger
from app.messengers.telegram_user import TelegramUserMessenger
from app.messengers.whatsapp import WhatsAppMessenger
from app.models.messenger_account import MessengerAccount


def create_messenger(account: MessengerAccount, settings: Settings) -> BaseMessenger:
    """Create appropriate messenger adapter based on account type."""
    if account.type == "tg_user":
        return TelegramUserMessenger(
            session_string=account.credentials,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
    elif account.type == "wa":
        return WhatsAppMessenger(session_id=str(account.id))
    elif account.type == "max":
        return MaxMessenger(session_id=str(account.id))
    else:
        raise ValueError(f"Unknown account type: {account.type}")

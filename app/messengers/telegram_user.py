import asyncio
import logging
import time

from pyrogram import Client
from pyrogram.errors import (
    FloodWait,
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
)

from app.messengers.base import BaseMessenger

logger = logging.getLogger(__name__)

# In-memory store for Pyrogram clients between auth steps.
# Key: auth_session_id, Value: (Client, created_timestamp)
_auth_clients: dict[int, tuple[Client, float]] = {}

AUTH_CLIENT_TTL = 600  # 10 minutes


def _cleanup_expired_clients() -> None:
    """Remove auth clients older than TTL."""
    now = time.time()
    expired = [k for k, (_, ts) in _auth_clients.items() if now - ts > AUTH_CLIENT_TTL]
    for k in expired:
        _auth_clients.pop(k, None)


async def start_auth(
    auth_session_id: int,
    phone: str,
    api_id: int,
    api_hash: str,
) -> str:
    """Send auth code to phone. Returns phone_code_hash.

    Raises PhoneNumberInvalid, FloodWait, or generic Exception.
    """
    _cleanup_expired_clients()

    client = Client(
        name=f"auth_{auth_session_id}",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    )
    await client.connect()

    try:
        logger.info("Sending code to %s (api_id=%s)", phone, api_id)
        sent_code = await client.send_code(phone)
        logger.info(
            "send_code result: type=%s, phone_code_hash=%s",
            getattr(sent_code, "type", "unknown"),
            sent_code.phone_code_hash,
        )
    except Exception as e:
        logger.error("send_code failed: %s", e)
        await client.disconnect()
        raise

    _auth_clients[auth_session_id] = (client, time.time())
    return sent_code.phone_code_hash


async def verify_code(
    auth_session_id: int,
    phone: str,
    phone_code_hash: str,
    code: str,
) -> str:
    """Verify SMS/Telegram code. Returns session_string.

    Raises PhoneCodeInvalid, PhoneCodeExpired, SessionPasswordNeeded, or generic Exception.
    """
    entry = _auth_clients.get(auth_session_id)
    if not entry:
        raise RuntimeError("Сессия авторизации истекла. Начните заново.")

    client, _ = entry

    try:
        await client.sign_in(phone, phone_code_hash, code)
    except SessionPasswordNeeded:
        raise
    except Exception:
        raise

    session_string = await client.export_session_string()
    await client.disconnect()
    _auth_clients.pop(auth_session_id, None)
    return session_string


async def verify_password(
    auth_session_id: int,
    password: str,
) -> str:
    """Verify 2FA password. Returns session_string.

    Raises PasswordHashInvalid or generic Exception.
    """
    entry = _auth_clients.get(auth_session_id)
    if not entry:
        raise RuntimeError("Сессия авторизации истекла. Начните заново.")

    client, _ = entry

    await client.check_password(password)

    session_string = await client.export_session_string()
    await client.disconnect()
    _auth_clients.pop(auth_session_id, None)
    return session_string


def cleanup_auth_client(auth_session_id: int) -> None:
    """Remove client from in-memory store."""
    entry = _auth_clients.pop(auth_session_id, None)
    if entry:
        client, _ = entry
        # Best-effort disconnect
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(client.disconnect())
            else:
                loop.run_until_complete(client.disconnect())
        except Exception:
            pass


class TelegramUserMessenger(BaseMessenger):
    def __init__(self, session_string: str, api_id: int, api_hash: str):
        self.client = Client(
            name="broadcaster_user",
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            in_memory=True,
        )

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        try:
            async with self.client:
                if images:
                    await self.client.send_photo(chat_id=int(group_id), photo=images[0], caption=text)
                else:
                    await self.client.send_message(chat_id=int(group_id), text=text)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_groups(self) -> list[dict]:
        groups = []
        try:
            async with self.client:
                async for dialog in self.client.get_dialogs():
                    if dialog.chat.type in ("group", "supergroup"):
                        groups.append({"id": str(dialog.chat.id), "name": dialog.chat.title})
        except Exception:
            pass
        return groups

    async def check_connection(self) -> bool:
        try:
            async with self.client:
                await self.client.get_me()
            return True
        except Exception:
            return False

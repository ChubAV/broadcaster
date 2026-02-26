import asyncio
import structlog
import time
import uuid
from dataclasses import dataclass, field

import httpx
from telethon import TelegramClient
from telethon.errors import (
    ChatWriteForbiddenError,
    ForbiddenError,
    SlowModeWaitError,
    UserBannedInChannelError,
)
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat

from app.messengers.base import BaseMessenger

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# QR Auth in-memory state
# ---------------------------------------------------------------------------

QR_SESSION_TTL = 300  # 5 minutes


@dataclass
class QRAuthState:
    client: TelegramClient
    qr_login: object | None = None
    status: str = "waiting"  # waiting | needs_2fa | success | error
    session_string: str | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    _wait_task: asyncio.Task | None = field(default=None, repr=False)


_qr_sessions: dict[str, QRAuthState] = {}


def _cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [k for k, v in _qr_sessions.items() if now - v.created_at > QR_SESSION_TTL]
    for k in expired:
        state = _qr_sessions.pop(k, None)
        if state and state._wait_task:
            state._wait_task.cancel()


async def start_qr_auth(api_id: int, api_hash: str) -> tuple[str, str]:
    """Start QR auth flow. Returns (session_id, login_url for QR)."""
    _cleanup_expired_sessions()

    session_id = uuid.uuid4().hex[:16]
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    try:
        qr_login = await client.qr_login()
    except Exception as e:
        await client.disconnect()
        raise RuntimeError(f"Failed to start QR login: {e}") from e

    state = QRAuthState(client=client, qr_login=qr_login)
    _qr_sessions[session_id] = state

    # Start background task to wait for scan
    state._wait_task = asyncio.create_task(_wait_for_qr(session_id))

    return session_id, qr_login.url


async def _wait_for_qr(session_id: str) -> None:
    """Background task: wait for QR scan result."""
    state = _qr_sessions.get(session_id)
    if not state or not state.qr_login:
        return

    try:
        await state.qr_login.wait()
        # Success — user scanned and authorized
        state.session_string = state.client.session.save()
        state.status = "success"
    except asyncio.CancelledError:
        pass
    except Exception as e:
        err_name = type(e).__name__
        if "SessionPasswordNeeded" in err_name or "SessionPasswordNeededError" in err_name:
            state.status = "needs_2fa"
        else:
            state.status = "error"
            state.error = str(e)
            logger.error("qr_auth_error", session_id=session_id, error=str(e), exc_info=True)


def get_qr_status(session_id: str) -> dict:
    """Get current QR auth status."""
    state = _qr_sessions.get(session_id)
    if not state:
        return {"status": "expired"}

    if time.time() - state.created_at > QR_SESSION_TTL:
        return {"status": "expired"}

    result = {"status": state.status}
    if state.error:
        result["error"] = state.error
    return result


async def refresh_qr(session_id: str) -> str | None:
    """Recreate QR if expired. Returns new login_url or None."""
    state = _qr_sessions.get(session_id)
    if not state or not state.qr_login:
        return None

    try:
        await state.qr_login.recreate()
        state.status = "waiting"
        state.created_at = time.time()

        # Restart wait task
        if state._wait_task:
            state._wait_task.cancel()
        state._wait_task = asyncio.create_task(_wait_for_qr(session_id))

        return state.qr_login.url
    except Exception as e:
        logger.error("qr_refresh_error", session_id=session_id, error=str(e))
        return None


async def submit_2fa(session_id: str, password: str) -> str:
    """Submit 2FA password. Returns session_string on success."""
    state = _qr_sessions.get(session_id)
    if not state:
        raise RuntimeError("Сессия авторизации истекла. Начните заново.")

    from telethon.errors import PasswordHashInvalidError

    try:
        await state.client.sign_in(password=password)
    except PasswordHashInvalidError:
        raise ValueError("Неверный пароль 2FA.")

    state.session_string = state.client.session.save()
    state.status = "success"
    return state.session_string


async def complete_auth(session_id: str) -> str | None:
    """Get session string and clean up. Returns session_string or None."""
    state = _qr_sessions.pop(session_id, None)
    if not state:
        return None

    if state._wait_task:
        state._wait_task.cancel()

    session_string = state.session_string

    try:
        await state.client.disconnect()
    except Exception:
        pass

    return session_string


def cleanup_qr_session(session_id: str) -> None:
    """Clean up a QR auth session."""
    state = _qr_sessions.pop(session_id, None)
    if state:
        if state._wait_task:
            state._wait_task.cancel()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(state.client.disconnect())
            else:
                loop.run_until_complete(state.client.disconnect())
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Messenger adapter
# ---------------------------------------------------------------------------


class TelegramUserMessenger(BaseMessenger):
    def __init__(self, session_string: str, api_id: int, api_hash: str):
        self.client = TelegramClient(
            StringSession(session_string), api_id, api_hash
        )
        self.log = logger.bind(messenger="telegram")

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        try:
            await self.client.connect()
            if images:
                # Download images from URLs and send as in-memory files
                import io
                from pathlib import PurePosixPath
                files = []
                async with httpx.AsyncClient() as http:
                    for url in images:
                        resp = await http.get(url)
                        resp.raise_for_status()
                        # Extract filename from URL to preserve extension
                        filename = PurePosixPath(url.split("?")[0]).name or "image.jpg"
                        buf = io.BytesIO(resp.content)
                        buf.name = filename
                        files.append(buf)
                try:
                    await self.client.send_file(
                        int(group_id), files, caption=text,
                        force_document=False,
                    )
                except ForbiddenError:
                    self.log.warning(
                        "send_media_forbidden_fallback_text",
                        group_id=group_id,
                    )
                    await self.client.send_message(int(group_id), text)
            else:
                await self.client.send_message(int(group_id), text)
            return {"ok": True}
        except SlowModeWaitError as e:
            self.log.warning("send_slow_mode", group_id=group_id, wait_seconds=e.seconds, error=str(e))
            return {"ok": False, "error": str(e), "no_retry": True}
        except (ChatWriteForbiddenError, UserBannedInChannelError, ForbiddenError) as e:
            self.log.warning("send_forbidden", group_id=group_id, error=str(e))
            return {"ok": False, "error": str(e), "no_retry": True}
        except Exception as e:
            self.log.error("send_message_error", group_id=group_id, error=str(e), exc_info=True)
            return {"ok": False, "error": str(e)}
        finally:
            try:
                await self.client.disconnect()
            except Exception:
                pass

    async def get_groups(self) -> list[dict]:
        groups = []
        try:
            await self.client.connect()
            dialogs = await self.client.get_dialogs()
            for dialog in dialogs:
                if dialog.is_group:
                    groups.append({"id": str(dialog.id), "name": dialog.title})
        except Exception as e:
            self.log.error("get_groups_error", error=str(e), exc_info=True)
        finally:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        return groups

    async def check_connection(self) -> bool:
        try:
            await self.client.connect()
            await self.client.get_me()
            return True
        except Exception as e:
            self.log.warning("check_connection_failed", error=str(e))
            return False
        finally:
            try:
                await self.client.disconnect()
            except Exception:
                pass


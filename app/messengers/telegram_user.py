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
    PeerIdInvalidError,
    SlowModeWaitError,
    UserBannedInChannelError,
)
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import Channel, ChannelParticipantsAdmins, Chat

from app.messengers.base import BaseMessenger, MessengerFetchError

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

# Текст для ПОЛЬЗОВАТЕЛЯ, а не для разработчика: значение отсюда уезжает в
# `group.last_error` (`app/application/scheduling/use_cases.py:484`) и в
# `SendLog`, то есть прямо на экран истории отправок. Константа заведена вместо
# литерала в местах возврата потому, что о потере доступа сообщают ДВА разных
# исхода — отказ сервера PEER_ID_INVALID и неразрешимый peer после прогрева
# кэша, — и, разъехавшись, они показали бы пользователю два разных объяснения
# одной и той же беды.
PEER_UNREACHABLE_MESSAGE = (
    "Аккаунт больше не имеет доступа к этой группе — "
    "пересинхронизируйте группы аккаунта."
)


class PeerUnreachableError(RuntimeError):
    """Группа окончательно не разрешается в сущность — доступ к ней потерян.

    Заведено собственным типом, потому что `get_input_entity` на недоступной
    группе поднимает голый `ValueError`, а это ровно то же самое «аккаунт
    больше не состоит в группе», что и ответ сервера `PeerIdInvalidError`.
    Ловить оба исхода одной веткой через `except ValueError` было бы нельзя:
    такая ветка проглотила бы и негодный идентификатор группы, и любой другой
    `ValueError` из тела отправки, и выдала бы их за потерю доступа — то есть
    посоветовала бы пересинхронизировать группы там, где это не поможет.
    """


class TelegramUserMessenger(BaseMessenger):
    def __init__(self, session_string: str, api_id: int, api_hash: str):
        self.client = TelegramClient(
            StringSession(session_string), api_id, api_hash
        )
        self.log = logger.bind(messenger="telegram")

    async def _resolve_peer(self, group_id: str):
        """Разрешает идентификатор группы в сущность telethon перед отправкой.

        Без этого в запрос уезжает голое число, и сервер отвечает 400
        PEER_ID_INVALID. Причина в том, что клиент здесь создаётся заново на
        КАЖДУЮ отправку, а `StringSession.save()` хранит только dc_id, адрес и
        `auth_key` — соответствий `id → access_hash` в строке сессии нет. Кэш
        сущностей у свежего клиента поэтому пуст, и telethon вынужден угадывать
        тип peer по знаку числа: `-100…` он превращает в `PeerChannel` с
        до-разрешением через `channels.getChannels(access_hash=0)`, прочее
        отрицательное — в `InputPeerChat(id)` вообще без проверки. Эту догадку
        сервер и отвергает.

        Прогрев кэша стоит РОВНО один `get_dialogs()`, и повторная попытка
        РОВНО одна. Запрос этот у свежего клиента не бесплатен, а группа,
        потерянная навсегда, получает отправку по расписанию раз за разом:
        прогрев без потолка превратил бы её в постоянный источник лишних
        обращений к Telegram и приблизил бы FloodWait на аккаунте пользователя.
        """
        # Разбор числа стоит ВНЕ `try`: негодный идентификатор группы — это не
        # холодный кэш, и тянуть из-за него тяжёлый `get_dialogs()` незачем.
        peer_id = int(group_id)
        try:
            return await self.client.get_input_entity(peer_id)
        except ValueError:
            await self.client.get_dialogs()
            try:
                return await self.client.get_input_entity(peer_id)
            except ValueError as e:
                raise PeerUnreachableError(PEER_UNREACHABLE_MESSAGE) from e

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        try:
            await self.client.connect()
            # Разрешение стоит ОДНО на отправку и ДО ветвления на картинки/текст:
            # разнесённое по веткам, оно дало бы до трёх прогревов кэша диалогов
            # на одну-единственную отправку.
            peer = await self._resolve_peer(group_id)
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
                # Одна картинка уходит ОДИНОЧНЫМ файлом, а не списком из
                # одного элемента. На список telethon сворачивает в альбомную
                # ветку `_send_album` (`telethon/client/uploads.py`, около
                # строки 540), где каждый файл сперва конвертируется в
                # `InputPhoto` через `messages.uploadMedia` — это ПЕРВЫЙ запрос
                # альбома, несущий peer, и именно он получал от сервера отказ.
                # Одиночный файл идёт через `messages.sendMedia`, и
                # `uploadMedia` не вызывается вовсе.
                #
                # Это ВТОРАЯ независимая мера, а не замена разрешению peer выше:
                # разрешённый peer чинит и альбом тоже, а одиночный файл убирает
                # с пути самый хрупкий запрос у самого частого случая — одной
                # картинки в объявлении.
                payload = files[0] if len(files) == 1 else files
                try:
                    await self.client.send_file(
                        peer, payload, caption=text,
                        force_document=False,
                    )
                except ForbiddenError:
                    self.log.warning(
                        "send_media_forbidden_fallback_text",
                        group_id=group_id,
                    )
                    await self.client.send_message(peer, text)
            else:
                await self.client.send_message(peer, text)
            return {"ok": True}
        except SlowModeWaitError as e:
            self.log.warning("send_slow_mode", group_id=group_id, wait_seconds=e.seconds, error=str(e))
            return {"ok": False, "error": str(e), "no_retry": True}
        except (ChatWriteForbiddenError, UserBannedInChannelError, ForbiddenError) as e:
            self.log.warning("send_forbidden", group_id=group_id, error=str(e))
            return {"ok": False, "error": str(e), "no_retry": True}
        except (PeerIdInvalidError, PeerUnreachableError) as e:
            # Порядок относительно ветки запретов выше безразличен, и это стоит
            # сказать вслух: `PeerIdInvalidError` наследует `BadRequestError`
            # (400), а не `ForbiddenError` (403) — пересечения между ветками нет.
            #
            # `no_retry` стоит потому, что peer не станет валидным сам собой:
            # повтор пошлёт Telegram ТОТ ЖЕ отвергаемый запрос и лишь приблизит
            # FloodWait на аккаунте.
            #
            # Наружу уходит КОНСТАНТА, а не `str(e)`: текст telethon несёт имя
            # класса запроса и подсказку про ботов, а `result["error"]` — это не
            # строка лога, а надпись на экране истории отправок. Диагностика
            # остаётся в `log.warning` ниже, где ей и место.
            self.log.warning("send_peer_invalid", group_id=group_id, error=str(e))
            return {"ok": False, "error": PEER_UNREACHABLE_MESSAGE, "no_retry": True}
        except Exception as e:
            self.log.error("send_message_error", group_id=group_id, error=str(e), exc_info=True)
            return {"ok": False, "error": str(e), "no_retry": True}
        finally:
            try:
                await self.client.disconnect()
            except Exception:
                pass

    async def get_groups(self) -> list[dict]:
        """Состав групп аккаунта. Отказ поднимает `MessengerFetchError`.

        Раньше исключение здесь только логировалось, а наружу уходил частично
        заполненный (обычно пустой) список — то есть протухшая сессия Telethon
        выглядела как аккаунт без единой группы. С полной переинвентаризацией
        (D-10) это помечало пропавшими все группы разом, поэтому отказ обязан
        быть отличим от пустоты.
        """
        groups = []
        try:
            await self.client.connect()
            dialogs = await self.client.get_dialogs()
            for dialog in dialogs:
                if dialog.is_group:
                    groups.append({"id": str(dialog.id), "name": dialog.title})
        except Exception as e:
            self.log.error("get_groups_error", error=str(e), exc_info=True)
            raise MessengerFetchError(f"{type(e).__name__}: {e}") from e
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

    async def get_group_details(self, group_external_id: str) -> dict | None:
        try:
            await self.client.connect()
            entity = await self.client.get_entity(int(group_external_id))

            if not isinstance(entity, (Channel, Chat)):
                return None

            result = {
                "name": getattr(entity, "title", None) or str(group_external_id),
                "member_count": getattr(entity, "participants_count", None),
                "admins": [],
                "raw": {
                    "id": entity.id,
                    "title": getattr(entity, "title", None),
                    "username": getattr(entity, "username", None),
                    "participants_count": getattr(entity, "participants_count", None),
                },
            }

            # Try to fetch admins (works for supergroups/channels)
            if isinstance(entity, Channel):
                try:
                    admins_result = await self.client(
                        GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsAdmins(),
                            offset=0,
                            limit=100,
                            hash=0,
                        )
                    )
                    for user in admins_result.users:
                        result["admins"].append({
                            "id": str(user.id),
                            "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                            "username": user.username,
                        })
                except Exception as e:
                    self.log.debug("get_admins_failed", group_id=group_external_id, error=str(e))

            return result
        except Exception as e:
            self.log.error("get_group_details_error", group_id=group_external_id, error=str(e), exc_info=True)
            return None
        finally:
            try:
                await self.client.disconnect()
            except Exception:
                pass


# Telethon QR Auth Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace Pyrogram with Telethon for the Telegram userbot, using QR code login instead of phone+SMS.

**Architecture:** Full rewrite of `app/messengers/telegram_user.py` to use Telethon's `TelegramClient` with `StringSession`. QR auth flow via in-memory state + polling API. Web UI shows QR image and polls status via JS.

**Tech Stack:** Telethon, qrcode[pil], FastAPI, Jinja2, JavaScript polling

---

### Task 1: Update dependencies (Pyrogram → Telethon)

**Files:**
- Modify: `pyproject.toml`

**Step 1: Remove pyrogram and tgcrypto, add telethon and qrcode**

In `pyproject.toml`, replace these two lines in `dependencies`:
```
    "pyrogram>=2.0.106",
    "tgcrypto>=1.2.5",
```
with:
```
    "telethon>=1.37.0",
    "qrcode[pil]>=8.0",
```

**Step 2: Sync the environment**

Run: `uv sync`
Expected: Dependencies install without errors. Pyrogram removed, telethon and qrcode installed.

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: replace pyrogram with telethon and qrcode dependencies"
```

---

### Task 2: Rewrite TelegramUserMessenger adapter

**Files:**
- Rewrite: `app/messengers/telegram_user.py`
- Test: `tests/test_messengers/test_telegram_user.py`

**Step 1: Write failing tests for Telethon-based TelegramUserMessenger**

Rewrite `tests/test_messengers/test_telegram_user.py` completely:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.telegram_user import TelegramUserMessenger


@pytest.fixture
def messenger():
    with patch("app.messengers.telegram_user.TelegramClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=False)
        MockClient.return_value = mock_client

        m = TelegramUserMessenger(
            session_string="fake-session",
            api_id=12345,
            api_hash="fake-api-hash",
        )
        m.client = mock_client
        yield m


@pytest.mark.asyncio
async def test_send_text_message(messenger):
    messenger.client.send_message = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is True
    messenger.client.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_with_image(messenger):
    messenger.client.send_file = AsyncMock()

    result = await messenger.send_message("-100123", "Hello!", images=["path/to/img.jpg"])

    assert result["ok"] is True
    messenger.client.send_file.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_error(messenger):
    messenger.client.send_message = AsyncMock(side_effect=Exception("Flood wait"))

    result = await messenger.send_message("-100123", "Hello!")

    assert result["ok"] is False
    assert "Flood wait" in result["error"]


@pytest.mark.asyncio
async def test_get_groups(messenger):
    mock_dialog1 = MagicMock()
    mock_dialog1.is_group = True
    mock_dialog1.id = -100123
    mock_dialog1.title = "Test Group"

    mock_dialog2 = MagicMock()
    mock_dialog2.is_group = False
    mock_dialog2.id = 456
    mock_dialog2.title = "Some User"

    messenger.client.get_dialogs = AsyncMock(return_value=[mock_dialog1, mock_dialog2])

    groups = await messenger.get_groups()

    assert len(groups) == 1
    assert groups[0]["id"] == "-100123"
    assert groups[0]["name"] == "Test Group"


@pytest.mark.asyncio
async def test_check_connection_success(messenger):
    messenger.client.get_me = AsyncMock()

    assert await messenger.check_connection() is True


@pytest.mark.asyncio
async def test_check_connection_failure(messenger):
    messenger.client.get_me = AsyncMock(side_effect=Exception("Session expired"))

    assert await messenger.check_connection() is False
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_messengers/test_telegram_user.py -v`
Expected: FAIL (imports from old pyrogram-based module)

**Step 3: Rewrite the messenger adapter**

Replace `app/messengers/telegram_user.py` entirely:

```python
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat

from app.messengers.base import BaseMessenger

logger = logging.getLogger(__name__)

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
            logger.error("QR auth error for %s: %s", session_id, e)


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
        logger.error("Failed to refresh QR for %s: %s", session_id, e)
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

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        try:
            await self.client.connect()
            if images:
                await self.client.send_file(
                    int(group_id), images[0], caption=text
                )
            else:
                await self.client.send_message(int(group_id), text)
            return {"ok": True}
        except Exception as e:
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
        except Exception:
            pass
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
        except Exception:
            return False
        finally:
            try:
                await self.client.disconnect()
            except Exception:
                pass
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_messengers/test_telegram_user.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add app/messengers/telegram_user.py tests/test_messengers/test_telegram_user.py
git commit -m "feat: rewrite telegram userbot adapter from Pyrogram to Telethon"
```

---

### Task 3: Write tests for QR auth functions

**Files:**
- Test: `tests/test_messengers/test_telegram_user.py` (append to existing)

**Step 1: Add QR auth tests**

Append to `tests/test_messengers/test_telegram_user.py`:

```python
from app.messengers.telegram_user import (
    start_qr_auth,
    get_qr_status,
    submit_2fa,
    complete_auth,
    cleanup_qr_session,
    _qr_sessions,
)


@pytest.mark.asyncio
async def test_start_qr_auth():
    with patch("app.messengers.telegram_user.TelegramClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_qr_login = AsyncMock()
        mock_qr_login.url = "tg://login?token=abc123"
        mock_qr_login.wait = AsyncMock()
        mock_client.qr_login = AsyncMock(return_value=mock_qr_login)
        MockClient.return_value = mock_client

        session_id, url = await start_qr_auth(api_id=12345, api_hash="test_hash")

    assert session_id is not None
    assert url == "tg://login?token=abc123"
    assert session_id in _qr_sessions
    # Cleanup
    cleanup_qr_session(session_id)


def test_get_qr_status_missing():
    result = get_qr_status("nonexistent")
    assert result["status"] == "expired"


def test_get_qr_status_waiting():
    import time
    from app.messengers.telegram_user import QRAuthState
    _qr_sessions["test123"] = QRAuthState(
        client=AsyncMock(), status="waiting", created_at=time.time()
    )
    result = get_qr_status("test123")
    assert result["status"] == "waiting"
    _qr_sessions.pop("test123", None)


@pytest.mark.asyncio
async def test_submit_2fa_expired():
    with pytest.raises(RuntimeError, match="Сессия авторизации истекла"):
        await submit_2fa("nonexistent", "password")


@pytest.mark.asyncio
async def test_complete_auth():
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()
    from app.messengers.telegram_user import QRAuthState
    _qr_sessions["complete_test"] = QRAuthState(
        client=mock_client, session_string="saved_session_123", status="success"
    )

    result = await complete_auth("complete_test")

    assert result == "saved_session_123"
    assert "complete_test" not in _qr_sessions


def test_cleanup_qr_session():
    mock_client = AsyncMock()
    from app.messengers.telegram_user import QRAuthState
    _qr_sessions["cleanup_test"] = QRAuthState(client=mock_client)

    cleanup_qr_session("cleanup_test")

    assert "cleanup_test" not in _qr_sessions


def test_cleanup_qr_session_nonexistent():
    cleanup_qr_session("does_not_exist")  # Should not raise
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_messengers/test_telegram_user.py -v`
Expected: All tests PASS (implementation was written in Task 2)

**Step 3: Commit**

```bash
git add tests/test_messengers/test_telegram_user.py
git commit -m "test: add QR auth function tests for Telethon adapter"
```

---

### Task 4: Update routes in pages.py — replace phone+code flow with QR

**Files:**
- Modify: `app/routes/pages.py` (lines 24-33 imports, lines 409-669 endpoints)

**Step 1: Update imports in pages.py**

Replace the existing telegram_user imports (lines 26-33):
```python
from app.messengers.telegram_user import (
    TelegramUserMessenger,
    start_auth,
    resend_code,
    verify_code,
    verify_password as tg_verify_password,
    cleanup_auth_client,
)
```

with:
```python
from app.messengers.telegram_user import (
    TelegramUserMessenger,
    start_qr_auth,
    get_qr_status,
    refresh_qr,
    submit_2fa,
    complete_auth,
    cleanup_qr_session,
)
```

Also remove the `TelegramAuthSession` import on line 24 (no longer needed for new flow):
```python
from app.models.telegram_auth_session import TelegramAuthSession
```

**Step 2: Replace the tg_user connect page handler**

Replace the `accounts_connect_tg_user_page` handler (line 409-421) to render the new QR template:

```python
@router.get("/accounts/connect/tg_user", response_class=HTMLResponse)
async def accounts_connect_tg_user_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "accounts/connect_tg_user.html",
        {"request": request, "user": user, "active_page": "accounts"},
    )
```

(This stays the same — the template will change.)

**Step 3: Replace old endpoints with QR endpoints**

Remove these handlers entirely (lines 424-669):
- `accounts_connect_tg_user_send_code`
- `accounts_connect_tg_user_verify_page`
- `accounts_connect_tg_user_resend_code`
- `accounts_connect_tg_user_verify_submit`

Add these new handlers right after `accounts_connect_tg_user_page`:

```python
@router.post("/accounts/connect/tg_user/start-qr")
async def accounts_connect_tg_user_start_qr(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        return {"error": "Telegram API не настроен. Обратитесь к администратору."}

    try:
        session_id, login_url = await start_qr_auth(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
    except Exception as e:
        return {"error": f"Ошибка запуска QR авторизации: {e}"}

    # Generate QR code as base64 PNG
    import qrcode
    import io
    import base64

    img = qrcode.make(login_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "session_id": session_id,
        "qr_image": f"data:image/png;base64,{qr_base64}",
    }


@router.get("/accounts/connect/tg_user/qr-status")
async def accounts_connect_tg_user_qr_status(
    request: Request,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"status": "error", "error": "Не авторизован"}

    return get_qr_status(session_id)


@router.post("/accounts/connect/tg_user/refresh-qr")
async def accounts_connect_tg_user_refresh_qr(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id required"}

    new_url = await refresh_qr(session_id)
    if not new_url:
        return {"error": "Не удалось обновить QR. Начните заново."}

    import qrcode
    import io
    import base64

    img = qrcode.make(new_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return {"qr_image": f"data:image/png;base64,{qr_base64}"}


@router.post("/accounts/connect/tg_user/verify-2fa")
async def accounts_connect_tg_user_verify_2fa(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    data = await request.json()
    session_id = data.get("session_id")
    password = data.get("password")

    if not session_id or not password:
        return {"error": "session_id и password обязательны"}

    try:
        session_string = await submit_2fa(session_id, password)
    except ValueError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}

    # Clean up auth client
    await complete_auth(session_id)

    # Create MessengerAccount
    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials=session_string,
        status="active",
    )
    db.add(account)
    await db.commit()

    return {"status": "success"}


@router.post("/accounts/connect/tg_user/complete")
async def accounts_connect_tg_user_complete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id required"}

    session_string = await complete_auth(session_id)
    if not session_string:
        return {"error": "Сессия не найдена или авторизация не завершена."}

    # Create MessengerAccount
    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials=session_string,
        status="active",
    )
    db.add(account)
    await db.commit()

    return {"status": "success"}
```

**Step 4: Update the sync-groups handler**

In `accounts_sync_groups` (around line 833-849), update the tg_user branch. Remove the `session_data` fallback and legacy `json.loads`:

```python
    if account.type == "tg_user":
        messenger = TelegramUserMessenger(
            session_string=account.credentials,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
        fetched_groups = await messenger.get_groups()
        messenger_type = "tg_user"
```

**Step 5: Run full test suite to check nothing is broken**

Run: `uv run pytest tests/ -v`
Expected: All existing tests pass (some route tests may fail if they test old endpoints — fix in next task)

**Step 6: Commit**

```bash
git add app/routes/pages.py
git commit -m "feat: replace phone+code auth with QR code flow in pages routes"
```

---

### Task 5: Rewrite the tg_user connect template for QR

**Files:**
- Rewrite: `app/templates/accounts/connect_tg_user.html`
- Delete: `app/templates/accounts/verify_tg_user.html`

**Step 1: Rewrite the connect template**

Replace `app/templates/accounts/connect_tg_user.html` with:

```html
{% extends "base.html" %}
{% block title %}Подключение Telegram аккаунта - Broadcaster{% endblock %}
{% block content %}
<div class="max-w-lg">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Подключение Telegram аккаунта</h1>

    <div id="error-box" class="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700 hidden"></div>

    <div class="bg-white shadow rounded-lg p-6">
        <!-- Initial state: start button -->
        <div id="start-section">
            <p class="text-sm text-gray-600 mb-4">
                Нажмите кнопку, чтобы получить QR-код. Отсканируйте его в приложении Telegram (Настройки → Устройства → Подключить устройство).
            </p>
            <div class="flex gap-3">
                <button onclick="startQR()" id="start-btn" class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
                    Получить QR-код
                </button>
                <a href="/accounts" class="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50">Отмена</a>
            </div>
        </div>

        <!-- QR code display -->
        <div id="qr-section" class="hidden text-center">
            <img id="qr-image" src="" alt="QR-код" class="mx-auto mb-4" style="max-width: 256px;">
            <p id="qr-status-text" class="text-sm text-yellow-600 mb-4">Ожидание сканирования...</p>
            <button onclick="refreshQR()" id="refresh-btn" class="hidden rounded-md bg-gray-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-500">
                Обновить QR-код
            </button>
        </div>

        <!-- 2FA section -->
        <div id="2fa-section" class="hidden">
            <p class="text-sm text-gray-600 mb-4">
                У вашего аккаунта включена двухфакторная аутентификация. Введите пароль.
            </p>
            <div class="space-y-4">
                <div>
                    <label for="password" class="block text-sm font-medium text-gray-900">Пароль 2FA</label>
                    <input id="password" type="password" required placeholder="Пароль двухфакторной аутентификации"
                        class="mt-2 block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm">
                </div>
                <button onclick="submit2FA()" class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
                    Подтвердить
                </button>
            </div>
        </div>

        <!-- Success section -->
        <div id="success-section" class="hidden text-center">
            <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <p class="text-lg font-medium text-gray-900">Telegram аккаунт подключён!</p>
            <a href="/accounts" class="mt-4 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">К аккаунтам</a>
        </div>
    </div>
</div>

<script>
let currentSessionId = null;
let pollInterval = null;

function showError(msg) {
    const box = document.getElementById('error-box');
    box.textContent = msg;
    box.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error-box').classList.add('hidden');
}

function showSection(name) {
    ['start-section', 'qr-section', '2fa-section', 'success-section'].forEach(id => {
        document.getElementById(id).classList.add('hidden');
    });
    document.getElementById(name + '-section').classList.remove('hidden');
}

async function startQR() {
    hideError();
    const btn = document.getElementById('start-btn');
    btn.disabled = true;
    btn.textContent = 'Загрузка...';

    try {
        const resp = await fetch('/accounts/connect/tg_user/start-qr', {method: 'POST'});
        const data = await resp.json();
        if (data.error) {
            showError(data.error);
            btn.disabled = false;
            btn.textContent = 'Получить QR-код';
            return;
        }

        currentSessionId = data.session_id;
        document.getElementById('qr-image').src = data.qr_image;
        showSection('qr');
        startPolling();
    } catch (e) {
        showError('Ошибка сети: ' + e.message);
        btn.disabled = false;
        btn.textContent = 'Получить QR-код';
    }
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(checkStatus, 3000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function checkStatus() {
    if (!currentSessionId) return;

    try {
        const resp = await fetch(`/accounts/connect/tg_user/qr-status?session_id=${currentSessionId}`);
        const data = await resp.json();

        if (data.status === 'success') {
            stopPolling();
            // Complete the auth — create account
            const completeResp = await fetch('/accounts/connect/tg_user/complete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: currentSessionId}),
            });
            const completeData = await completeResp.json();
            if (completeData.error) {
                showError(completeData.error);
                return;
            }
            showSection('success');
        } else if (data.status === 'needs_2fa') {
            stopPolling();
            showSection('2fa');
        } else if (data.status === 'expired') {
            stopPolling();
            document.getElementById('qr-status-text').textContent = 'QR-код истёк.';
            document.getElementById('refresh-btn').classList.remove('hidden');
        } else if (data.status === 'error') {
            stopPolling();
            showError(data.error || 'Ошибка авторизации');
        }
        // else status === 'waiting' — keep polling
    } catch (e) {
        // Network error — keep trying
    }
}

async function refreshQR() {
    hideError();
    document.getElementById('refresh-btn').classList.add('hidden');

    try {
        const resp = await fetch('/accounts/connect/tg_user/refresh-qr', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId}),
        });
        const data = await resp.json();
        if (data.error) {
            showError(data.error);
            showSection('start');
            return;
        }

        document.getElementById('qr-image').src = data.qr_image;
        document.getElementById('qr-status-text').textContent = 'Ожидание сканирования...';
        startPolling();
    } catch (e) {
        showError('Ошибка сети: ' + e.message);
    }
}

async function submit2FA() {
    hideError();
    const password = document.getElementById('password').value;
    if (!password) {
        showError('Введите пароль');
        return;
    }

    try {
        const resp = await fetch('/accounts/connect/tg_user/verify-2fa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId, password: password}),
        });
        const data = await resp.json();
        if (data.error) {
            showError(data.error);
            return;
        }
        showSection('success');
    } catch (e) {
        showError('Ошибка сети: ' + e.message);
    }
}
</script>
{% endblock %}
```

**Step 2: Delete the old verify template**

Delete: `app/templates/accounts/verify_tg_user.html`

**Step 3: Add the "Connect Telegram account" button back to accounts list**

In `app/templates/accounts/list.html`, add the tg_user button in the button group (after the tg_bot button on line 7):

```html
        <a href="/accounts/connect/tg_user" class="rounded-md bg-violet-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-violet-500">Подключить TG аккаунт</a>
```

**Step 4: Verify UI works manually** (optional)

Start the app, navigate to `/accounts/connect/tg_user`, verify the page loads.

**Step 5: Commit**

```bash
git add app/templates/accounts/connect_tg_user.html app/templates/accounts/list.html
git rm app/templates/accounts/verify_tg_user.html
git commit -m "feat: QR code UI for Telegram userbot connection"
```

---

### Task 6: Update worker factory and remove legacy code

**Files:**
- Modify: `app/worker/tasks.py` (lines 25-38, get_messenger)

**Step 1: Simplify the tg_user branch in get_messenger**

In `app/worker/tasks.py`, replace the tg_user section of `get_messenger()` (lines 24-38):

```python
    elif account.type == "tg_user":
        from app.config import Settings
        settings = Settings()
        api_id = settings.telegram_api_id
        api_hash = settings.telegram_api_hash
        # Fallback to session_data for legacy accounts
        if not api_id or not api_hash:
            import json
            meta = json.loads(account.session_data or "{}")
            api_id = meta.get("api_id", 0)
            api_hash = meta.get("api_hash", "")
        return TelegramUserMessenger(
            session_string=account.credentials,
            api_id=api_id,
            api_hash=api_hash,
        )
```

with (no legacy fallback needed):

```python
    elif account.type == "tg_user":
        from app.config import Settings
        settings = Settings()
        return TelegramUserMessenger(
            session_string=account.credentials,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
```

**Step 2: Run full tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add app/worker/tasks.py
git commit -m "refactor: simplify tg_user factory, remove Pyrogram legacy fallback"
```

---

### Task 7: Update/fix tests for route changes

**Files:**
- Modify: `tests/test_routes/test_accounts.py` (if it tests old tg_user endpoints)
- Modify: `tests/test_models/test_telegram_auth_session.py` (keep or skip)

**Step 1: Check and fix route tests**

Read `tests/test_routes/test_accounts.py`. If it tests the old `/accounts/connect/tg_user/send-code` or `/accounts/connect/tg_user/verify` endpoints, remove those tests or replace them with tests for the new QR endpoints.

If it only tests the API routes (`/api/accounts`), no changes needed.

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 3: Commit if needed**

```bash
git add tests/
git commit -m "test: update tests for Telethon QR auth migration"
```

---

### Task 8: Final cleanup and verification

**Files:**
- Check all `import pyrogram` references (should be zero)

**Step 1: Search for any remaining Pyrogram references**

Run: `grep -r "pyrogram\|from pyrogram\|import pyrogram" app/ tests/`
Expected: No results (zero references)

**Step 2: Run the full test suite with coverage**

Run: `uv run pytest tests/ --cov=app --cov-report=term-missing -v`
Expected: All tests pass, reasonable coverage

**Step 3: Final commit (if any cleanups were needed)**

```bash
git add -A
git commit -m "chore: final cleanup after Pyrogram to Telethon migration"
```

# WhatsApp Multi-Session Bridge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert wa-bridge from single-client to multi-session architecture so each user gets their own WhatsApp session.

**Architecture:** Replace the single global whatsapp-web.js Client with a `Map<sessionId, SessionState>`. All API endpoints become per-session via `/:sessionId/` path prefix. Python adapter passes `session_id=account.id` to all bridge calls.

**Tech Stack:** Node.js/Express (wa-bridge), Python/FastAPI (app), whatsapp-web.js LocalAuth with clientId

---

### Task 1: Rewrite wa-bridge to multi-session

**Files:**
- Modify: `wa_bridge/index.js` (full rewrite)

**Step 1: Rewrite index.js with multi-session support**

Replace the entire contents of `wa_bridge/index.js` with:

```javascript
const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const fs = require('fs');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Map of sessionId -> { client, qrCode, isConnected, initializing }
const sessions = new Map();

function createClient(sessionId) {
    const client = new Client({
        authStrategy: new LocalAuth({
            clientId: sessionId,
            dataPath: './.wwebjs_auth',
        }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        },
    });

    const session = { client, qrCode: null, isConnected: false, initializing: true };

    client.on('qr', async (qr) => {
        session.qrCode = await qrcode.toDataURL(qr);
        console.log(`[${sessionId}] QR code generated`);
    });

    client.on('ready', () => {
        session.isConnected = true;
        session.initializing = false;
        session.qrCode = null;
        console.log(`[${sessionId}] Client ready`);
    });

    client.on('disconnected', (reason) => {
        session.isConnected = false;
        session.initializing = false;
        console.log(`[${sessionId}] Disconnected: ${reason}`);
    });

    client.on('auth_failure', (msg) => {
        session.isConnected = false;
        session.initializing = false;
        console.log(`[${sessionId}] Auth failure: ${msg}`);
    });

    sessions.set(sessionId, session);
    return session;
}

// POST /api/sessions/:id/start - Create and initialize a session
app.post('/api/sessions/:id/start', async (req, res) => {
    const { id } = req.params;

    // If session already exists and is connected, return ok
    if (sessions.has(id)) {
        const existing = sessions.get(id);
        if (existing.isConnected) {
            return res.json({ status: 'connected' });
        }
        if (existing.initializing) {
            return res.json({ status: 'initializing' });
        }
    }

    try {
        const session = createClient(id);
        await session.client.initialize();
        res.json({ status: 'initializing' });
    } catch (error) {
        console.error(`[${id}] Init error:`, error.message);
        sessions.delete(id);
        res.status(500).json({ error: error.message });
    }
});

// DELETE /api/sessions/:id - Destroy a session
app.delete('/api/sessions/:id', async (req, res) => {
    const { id } = req.params;
    const session = sessions.get(id);
    if (!session) {
        return res.json({ ok: true });
    }

    try {
        await session.client.destroy();
    } catch (e) {
        console.error(`[${id}] Destroy error:`, e.message);
    }
    sessions.delete(id);
    res.json({ ok: true });
});

// GET /api/sessions/:id/status - Connection status
app.get('/api/sessions/:id/status', (req, res) => {
    const session = sessions.get(req.params.id);
    if (!session) {
        return res.json({ connected: false, exists: false });
    }
    res.json({ connected: session.isConnected, exists: true });
});

// GET /api/sessions/:id/qr - Get QR code
app.get('/api/sessions/:id/qr', (req, res) => {
    const session = sessions.get(req.params.id);
    if (!session) {
        return res.json({ status: 'not_found', qr: null });
    }
    if (session.isConnected) {
        return res.json({ status: 'connected', qr: null });
    }
    if (!session.qrCode) {
        return res.json({ status: 'waiting', qr: null });
    }
    res.json({ status: 'pending', qr: session.qrCode });
});

// POST /api/sessions/:id/send - Send message
app.post('/api/sessions/:id/send', async (req, res) => {
    const session = sessions.get(req.params.id);
    if (!session || !session.isConnected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }

    const { group_id, text, image_path } = req.body;
    if (!group_id || !text) {
        return res.status(400).json({ error: 'group_id and text are required' });
    }

    try {
        if (image_path && fs.existsSync(image_path)) {
            const media = MessageMedia.fromFilePath(image_path);
            await session.client.sendMessage(group_id, media, { caption: text });
        } else {
            await session.client.sendMessage(group_id, text);
        }
        res.json({ ok: true });
    } catch (error) {
        console.error(`[${req.params.id}] Send error:`, error.message);
        res.status(500).json({ error: error.message });
    }
});

// GET /api/sessions/:id/groups - List groups
app.get('/api/sessions/:id/groups', async (req, res) => {
    const session = sessions.get(req.params.id);
    if (!session || !session.isConnected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }

    try {
        const chats = await session.client.getChats();
        const groups = chats
            .filter(chat => chat.isGroup)
            .map(chat => ({
                id: chat.id._serialized,
                name: chat.name,
            }));
        res.json(groups);
    } catch (error) {
        console.error(`[${req.params.id}] Groups error:`, error.message);
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`WA Bridge (multi-session) running on port ${PORT}`);
});
```

**Step 2: Commit**

```bash
git add wa_bridge/index.js
git commit -m "feat(wa-bridge): rewrite to multi-session architecture

Replace single global Client with sessions Map. All endpoints
now take :sessionId path param. Each session gets its own
LocalAuth with clientId for isolated storage."
```

---

### Task 2: Update WhatsAppMessenger adapter

**Files:**
- Modify: `app/messengers/whatsapp.py`
- Test: `tests/test_messengers/test_whatsapp.py`

**Step 1: Update the tests to expect session_id**

Replace `tests/test_messengers/test_whatsapp.py` with:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.messengers.whatsapp import WhatsAppMessenger


@pytest.mark.asyncio
async def test_send_message_success():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!")
        assert result["ok"] is True
        mock_client.post.assert_called_once()
        url = mock_client.post.call_args[0][0]
        assert "/api/sessions/42/send" in url


@pytest.mark.asyncio
async def test_send_message_with_image():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!", images=["path/to/img.jpg"])
        assert result["ok"] is True
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["image_path"] == "path/to/img.jpg"


@pytest.mark.asyncio
async def test_send_message_failure():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal error"

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.send_message("group123", "Hello!")
        assert result["ok"] is False
        assert "Internal error" in result["error"]


@pytest.mark.asyncio
async def test_get_groups_success():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "group1", "name": "Test Group"},
        {"id": "group2", "name": "Another Group"},
    ]

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        groups = await messenger.get_groups()
        assert len(groups) == 2
        url = mock_client.get.call_args[0][0]
        assert "/api/sessions/42/groups" in url


@pytest.mark.asyncio
async def test_get_groups_failure():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        groups = await messenger.get_groups()
        assert groups == []


@pytest.mark.asyncio
async def test_check_connection_connected():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": True}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        assert await messenger.check_connection() is True
        url = mock_client.get.call_args[0][0]
        assert "/api/sessions/42/status" in url


@pytest.mark.asyncio
async def test_check_connection_disconnected():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"connected": False}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        assert await messenger.check_connection() is False


@pytest.mark.asyncio
async def test_check_connection_bridge_down():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        assert await messenger.check_connection() is False


@pytest.mark.asyncio
async def test_start_session():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "initializing"}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.start_session()
        assert result is True
        url = mock_client.post.call_args[0][0]
        assert "/api/sessions/42/start" in url


@pytest.mark.asyncio
async def test_destroy_session():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.destroy_session()
        assert result is True
        url = mock_client.delete.call_args[0][0]
        assert "/api/sessions/42" in url


@pytest.mark.asyncio
async def test_get_qr():
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "pending", "qr": "data:image/png;base64,abc"}

    with patch("app.messengers.whatsapp.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await messenger.get_qr()
        assert result["status"] == "pending"
        assert result["qr"] == "data:image/png;base64,abc"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_messengers/test_whatsapp.py -v`
Expected: FAIL — `session_id` parameter not accepted yet

**Step 3: Update WhatsAppMessenger implementation**

Replace `app/messengers/whatsapp.py` with:

```python
import httpx

from app.messengers.base import BaseMessenger


class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str, session_id: str):
        self.bridge_url = bridge_url.rstrip("/")
        self.session_id = session_id

    def _url(self, path: str) -> str:
        return f"{self.bridge_url}/api/sessions/{self.session_id}/{path}"

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            payload = {"group_id": group_id, "text": text}
            if images:
                payload["image_path"] = images[0]
            response = await client.post(self._url("send"), json=payload)
            if response.status_code == 200:
                return {"ok": True}
            return {"ok": False, "error": response.text}

    async def get_groups(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self._url("groups"))
            if response.status_code == 200:
                return response.json()
            return []

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._url("status"))
                return response.status_code == 200 and response.json().get("connected", False)
        except Exception:
            return False

    async def start_session(self) -> bool:
        """Tell bridge to create and initialize a Client for this session."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self._url("start"))
                return response.status_code == 200
        except Exception:
            return False

    async def destroy_session(self) -> bool:
        """Tell bridge to destroy this session's Client."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.bridge_url}/api/sessions/{self.session_id}"
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_qr(self) -> dict:
        """Get QR code for this session. Returns {"status": "...", "qr": "..." | null}."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._url("qr"))
                if response.status_code == 200:
                    return response.json()
                return {"status": "error", "qr": None}
        except Exception:
            return {"status": "error", "qr": None}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_messengers/test_whatsapp.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add app/messengers/whatsapp.py tests/test_messengers/test_whatsapp.py
git commit -m "feat: add session_id to WhatsAppMessenger, add start/destroy/get_qr methods"
```

---

### Task 3: Update worker tasks to pass session_id

**Files:**
- Modify: `app/worker/tasks.py:40-43`
- Test: `tests/test_worker/test_tasks.py`

**Step 1: Update get_messenger for WA to pass session_id**

In `app/worker/tasks.py`, change the WA branch of `get_messenger` (lines 40-43):

```python
    elif account.type == "wa":
        from app.config import Settings
        settings = Settings()
        return WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=str(account.id))
```

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS (existing worker tests use `tg_bot` type, so unaffected)

**Step 3: Commit**

```bash
git add app/worker/tasks.py
git commit -m "feat: pass session_id=account.id when creating WhatsAppMessenger in worker"
```

---

### Task 4: Update WA connect flow in routes

**Files:**
- Modify: `app/routes/pages.py:672-782`

**Step 1: Update `accounts_connect_wa_page` (line 672)**

Replace the route at lines 672-713 with:

```python
@router.get("/accounts/connect/wa", response_class=HTMLResponse)
async def accounts_connect_wa_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from app.messengers.whatsapp import WhatsAppMessenger

    # Check if user already has an active WA account
    existing = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "active",
        )
    )
    existing_account = existing.scalar_one_or_none()
    if existing_account:
        return RedirectResponse(url="/accounts", status_code=302)

    # Create a pending WA account to get a session_id
    account = MessengerAccount(
        user_id=user.id,
        type="wa",
        credentials="pending",
        status="connecting",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    session_id = str(account.id)
    messenger = WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=session_id)

    qr_code = None
    connected = False
    error = None

    try:
        await messenger.start_session()
        qr_data = await messenger.get_qr()
        qr_code = qr_data.get("qr")
        if qr_data.get("status") == "connected":
            connected = True
    except Exception as e:
        error = f"Ошибка подключения к WA Bridge: {e}"

    return templates.TemplateResponse(
        "accounts/connect_wa.html",
        {
            "request": request,
            "user": user,
            "active_page": "accounts",
            "qr_code": qr_code,
            "connected": connected,
            "error": error,
            "account_id": account.id,
        },
    )
```

**Step 2: Update `accounts_connect_wa_status` (line 716)**

Replace the route at lines 716-781 with:

```python
@router.get("/accounts/connect/wa/status", response_class=HTMLResponse)
async def accounts_connect_wa_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return HTMLResponse('<span class="text-sm text-red-600">Не авторизован</span>')

    from app.messengers.whatsapp import WhatsAppMessenger

    # Find the pending/connecting WA account for this user
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "connecting",
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return HTMLResponse('<span class="text-sm text-red-600">Нет активной сессии подключения</span>')

    session_id = str(account.id)
    messenger = WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=session_id)

    try:
        is_connected = await messenger.check_connection()
        if is_connected:
            account.credentials = session_id
            account.status = "active"
            await db.commit()

            return HTMLResponse(
                '<div class="text-center">'
                '<div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">'
                '<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>'
                '</svg></div>'
                '<p class="text-lg font-medium text-gray-900">WhatsApp подключён!</p>'
                '<a href="/accounts" class="mt-4 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">К аккаунтам</a>'
                '</div>'
            )

        # Not connected — get fresh QR
        qr_data = await messenger.get_qr()
        qr = qr_data.get("qr")
        if qr:
            return HTMLResponse(
                f'<div class="text-center">'
                f'<div class="inline-block p-4 bg-white border rounded-lg">'
                f'<img src="{qr}" alt="WhatsApp QR-код" class="mx-auto" style="max-width: 256px;">'
                f'</div>'
                f'<p class="mt-2 text-sm text-yellow-600">Ожидание сканирования...</p>'
                f'</div>'
            )

        return HTMLResponse('<span class="text-sm text-yellow-600">Ожидание QR-кода...</span>')

    except Exception:
        return HTMLResponse('<span class="text-sm text-red-600">Ошибка соединения с WA Bridge</span>')
```

**Step 3: Run tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add app/routes/pages.py
git commit -m "feat: update WA connect flow for per-session bridge API

Create MessengerAccount with status=connecting before starting
bridge session. Use account.id as session_id for all bridge calls."
```

---

### Task 5: Update WA group sync to pass session_id

**Files:**
- Modify: `app/routes/pages.py:823-828`

**Step 1: Update the WA branch of sync-groups**

In `app/routes/pages.py`, find the WA branch of `accounts_sync_groups` (lines 823-828) and change to:

```python
    elif account.type == "wa":
        from app.messengers.whatsapp import WhatsAppMessenger

        messenger = WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=str(account.id))
        fetched_groups = await messenger.get_groups()
        messenger_type = "wa"
```

**Step 2: Run tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add app/routes/pages.py
git commit -m "feat: pass session_id to WhatsAppMessenger in group sync"
```

---

### Task 6: Update connect_wa.html template for account_id

**Files:**
- Modify: `app/templates/accounts/connect_wa.html`

**Step 1: No changes needed**

The template uses HTMX polling to `/accounts/connect/wa/status` which now looks up the connecting account from the database. The template already works correctly — it just needs the `account_id` passed in context (done in Task 4). No template changes required.

**Step 2: Verify template still works**

Inspect the template: the HTMX `hx-get="/accounts/connect/wa/status"` already polls correctly. The status endpoint finds the connecting account by user_id + status="connecting". No changes needed.

---

### Task 7: Handle stale connecting accounts cleanup

**Files:**
- Modify: `app/routes/pages.py` (in `accounts_connect_wa_page`)

**Step 1: Add cleanup of stale connecting accounts**

In the `accounts_connect_wa_page` route (Task 4), before creating a new account, clean up any previous stale "connecting" accounts for this user. Add this block before the `account = MessengerAccount(...)` line:

```python
    # Clean up any previous stale connecting accounts
    stale = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "connecting",
        )
    )
    for old in stale.scalars().all():
        await db.delete(old)
    await db.commit()
```

**Step 2: Run tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add app/routes/pages.py
git commit -m "fix: clean up stale WA connecting accounts before new connect attempt"
```

---

### Task 8: Final integration test

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All PASS

**Step 2: Verify no regressions**

Run: `uv run pytest tests/ --cov=app --cov-report=term-missing`

**Step 3: Final commit if any remaining changes**

```bash
git status
# If clean, no commit needed
```

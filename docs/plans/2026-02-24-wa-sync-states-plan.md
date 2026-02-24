# WhatsApp Two-Phase Sync — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow large WhatsApp accounts (240+ groups) to connect without timeout by splitting connection into two phases: QR auth and background group sync.

**Architecture:** WA Bridge (Node.js) gains a `syncState` field and background group-fetching with retries after `connection: 'open'`. Python tracks new account statuses (`syncing`, `sync_failed`), polls bridge for sync completion, auto-saves groups, and shows progress via HTMX polling on the accounts page.

**Tech Stack:** Node.js/Express (wa_bridge), Python/FastAPI + SQLAlchemy async, Jinja2 + HTMX templates.

---

### Task 1: WA Bridge — Add syncState and background group fetch

**Files:**
- Modify: `wa_bridge/index.js:131-155` (sessionState + readyPromise timeout)
- Modify: `wa_bridge/index.js:168-181` (connection: 'open' handler)
- Modify: `wa_bridge/index.js:345-353` (idle timeout)

**Step 1: Add `syncState` and `groups` to sessionState**

In `wa_bridge/index.js`, modify the `sessionState` object (line 131) to add two new fields:

```javascript
const sessionState = {
    sock,
    saveCreds,
    qrCode: null,
    isConnected: false,
    initializing: true,
    lastActivity: Date.now(),
    reconnectAttempts: 0,
    readyResolve: null,
    readyReject: null,
    readyPromise: null,
    syncState: null,    // null | 'syncing' | 'ready' | 'failed'
    groups: null,       // Array of {id, name} when synced
};
```

**Step 2: Increase readyPromise timeout from 120s to 600s**

Change line 153 from `120000` to `600000` and update error message:

```javascript
sessionState._readyTimeout = setTimeout(() => {
    sessionState.initializing = false;
    try { sock.end(); } catch (_) {}
    sessions.delete(sessionId);
    reject(new Error('Session initialization timeout (600s)'));
}, 600000);
```

**Step 3: Add background group sync function**

Add a new function `startGroupSync(sessionId)` after `deleteSessionFiles` (after line 107):

```javascript
/**
 * Background group sync with retries after connection is established.
 * Waits, then fetches groups with exponential backoff.
 */
async function startGroupSync(sessionId) {
    const INITIAL_DELAY = 30000;  // 30s — let Baileys finish internal sync
    const RETRY_DELAYS = [30000, 60000, 120000];  // 30s, 60s, 120s retries
    const MAX_ATTEMPTS = RETRY_DELAYS.length + 1;  // 4 total (1 initial + 3 retries)

    const state = sessions.get(sessionId);
    if (!state) return;

    state.syncState = 'syncing';
    console.log(`[${sessionId}] Starting group sync (waiting ${INITIAL_DELAY / 1000}s)...`);

    await new Promise(r => setTimeout(r, INITIAL_DELAY));

    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        const currentState = sessions.get(sessionId);
        if (!currentState || !currentState.isConnected) {
            console.log(`[${sessionId}] Session gone or disconnected during sync, aborting`);
            return;
        }

        try {
            console.log(`[${sessionId}] Fetching groups (attempt ${attempt + 1}/${MAX_ATTEMPTS})...`);
            const groupsObj = await currentState.sock.groupFetchAllParticipating();
            const groups = Object.entries(groupsObj).map(([jid, metadata]) => ({
                id: jid,
                name: metadata.subject,
            }));
            currentState.syncState = 'ready';
            currentState.groups = groups;
            console.log(`[${sessionId}] Group sync complete: ${groups.length} groups`);
            return;
        } catch (err) {
            console.error(`[${sessionId}] Group fetch failed (attempt ${attempt + 1}/${MAX_ATTEMPTS}): ${err.message}`);
            if (attempt < RETRY_DELAYS.length) {
                const delay = RETRY_DELAYS[attempt];
                console.log(`[${sessionId}] Retrying group fetch in ${delay / 1000}s...`);
                await new Promise(r => setTimeout(r, delay));
            }
        }
    }

    // All attempts failed
    const finalState = sessions.get(sessionId);
    if (finalState) {
        finalState.syncState = 'failed';
        console.log(`[${sessionId}] Group sync failed after ${MAX_ATTEMPTS} attempts`);
    }
}
```

**Step 4: Trigger group sync on connection open**

Modify the `connection === 'open'` block (line 168-181) to start background sync:

```javascript
if (connection === 'open') {
    sessionState.isConnected = true;
    sessionState.initializing = false;
    sessionState.qrCode = null;
    sessionState.lastActivity = Date.now();
    sessionState.reconnectAttempts = 0;
    clearTimeout(sessionState._readyTimeout);
    if (sessionState.readyResolve) {
        sessionState.readyResolve();
        sessionState.readyResolve = null;
        sessionState.readyReject = null;
    }
    console.log(`[${sessionId}] Connected`);

    // Start background group sync (don't await — runs in background)
    if (!sessionState.syncState || sessionState.syncState === 'failed') {
        startGroupSync(sessionId).catch(err => {
            console.error(`[${sessionId}] Group sync error: ${err.message}`);
        });
    }
}
```

**Step 5: Skip syncing sessions in idle timeout**

Modify the idle timeout interval (line 345-353) to skip sessions with `syncState === 'syncing'`:

```javascript
setInterval(() => {
    const now = Date.now();
    for (const [id, state] of sessions) {
        if (state.syncState === 'syncing') {
            continue; // Don't unload sessions that are syncing
        }
        if (state.isConnected && (now - state.lastActivity > IDLE_TIMEOUT_MS)) {
            console.log(`[${id}] Idle for ${Math.round(IDLE_TIMEOUT_MS / 1000)}s, unloading`);
            unloadSession(id);
        }
    }
}, 60000);
```

**Step 6: Verify bridge starts and logs are clean**

Run: `docker compose restart wa-bridge && docker compose logs --tail=20 wa-bridge`
Expected: Bridge starts without errors, shows version and port.

**Step 7: Commit**

```bash
git add wa_bridge/index.js
git commit -m "feat(wa-bridge): add syncState and background group sync with retries"
```

---

### Task 2: WA Bridge — Add sync-status endpoint and modify status endpoint

**Files:**
- Modify: `wa_bridge/index.js:394-405` (status endpoint)
- Add new endpoint after line 422

**Step 1: Add GET /api/sessions/:id/sync-status endpoint**

Add after the `/qr` endpoint (after line 422):

```javascript
// GET /api/sessions/:id/sync-status - Group sync status
app.get('/api/sessions/:id/sync-status', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        // Session not in memory — check disk
        if (sessionExistsOnDisk(sessionId)) {
            return res.json({ state: 'unknown', groups: null });
        }
        return res.json({ state: 'not_found', groups: null });
    }

    return res.json({
        state: state.syncState || 'none',
        groups: state.groups,
    });
});
```

**Step 2: Add `syncState` to existing status endpoint**

Modify the status endpoint (line 394-405) to include sync state:

```javascript
app.get('/api/sessions/:id/status', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        const exists = sessionExistsOnDisk(sessionId);
        return res.json({ connected: false, exists, syncState: null });
    }
    res.json({
        connected: state.isConnected,
        exists: true,
        syncState: state.syncState,
    });
});
```

**Step 3: Add POST /api/sessions/:id/retry-sync endpoint**

Add after the sync-status endpoint:

```javascript
// POST /api/sessions/:id/retry-sync - Retry failed group sync
app.post('/api/sessions/:id/retry-sync', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state || !state.isConnected) {
        return res.status(404).json({ error: 'Session not connected' });
    }

    if (state.syncState === 'syncing') {
        return res.json({ status: 'already_syncing' });
    }

    // Reset and retry
    state.syncState = null;
    state.groups = null;
    startGroupSync(sessionId).catch(err => {
        console.error(`[${sessionId}] Retry group sync error: ${err.message}`);
    });

    res.json({ status: 'sync_started' });
});
```

**Step 4: Commit**

```bash
git add wa_bridge/index.js
git commit -m "feat(wa-bridge): add sync-status and retry-sync endpoints"
```

---

### Task 3: Python — Add `get_sync_status` and `retry_sync` to WhatsAppMessenger

**Files:**
- Modify: `app/messengers/whatsapp.py:83-90` (after check_connection)

**Step 1: Add `get_sync_status` method**

Add after `check_connection` (after line 90):

```python
async def get_sync_status(self) -> dict:
    """Get group sync status from bridge.
    Returns: {"state": "syncing"|"ready"|"failed"|"none"|"not_found", "groups": [...] | None}
    """
    client = get_http_client()
    try:
        response = await client.get(self._url("sync-status"))
        if response.status_code == 200:
            return response.json()
        self.log.warning("get_sync_status_error", http_status=response.status_code)
        return {"state": "error", "groups": None}
    except Exception as e:
        self.log.error("get_sync_status_error", error=str(e), exc_info=True)
        return {"state": "error", "groups": None}

async def retry_sync(self) -> dict:
    """Trigger retry of failed group sync."""
    client = get_http_client()
    try:
        response = await client.post(self._url("retry-sync"), json={})
        if response.status_code == 200:
            return response.json()
        return {"status": "error"}
    except Exception as e:
        self.log.error("retry_sync_error", error=str(e), exc_info=True)
        return {"status": "error"}
```

**Step 2: Commit**

```bash
git add app/messengers/whatsapp.py
git commit -m "feat(wa): add get_sync_status and retry_sync methods"
```

---

### Task 4: Python — Update QR status polling to set `syncing` status

**Files:**
- Modify: `app/pages/accounts.py:290-351` (accounts_connect_wa_status)

**Step 1: Modify the connected branch to set status `syncing` instead of `active`**

Replace the `is_connected` block in `accounts_connect_wa_status` (lines 315-331). When connected, set account status to `syncing` and show a redirect message instead of the final "connected" state:

```python
try:
    is_connected = await messenger.check_connection()
    if is_connected:
        account.credentials = session_id
        account.status = "syncing"
        await db.commit()

        return HTMLResponse(
            '<div class="text-center">'
            '<div class="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">'
            '<svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>'
            '</svg></div>'
            '<p class="text-lg font-medium text-gray-900">WhatsApp подключён!</p>'
            '<p class="mt-2 text-sm text-slate-500">Начинаем синхронизацию групп...</p>'
            '<script>setTimeout(() => window.location.href = "/accounts", 2000);</script>'
            '</div>'
        )
```

**Step 2: Also look for `syncing` status accounts in the query (not just `connecting`)**

The status polling query at line 301-307 only finds `connecting` accounts. This is correct — by the time the account is `syncing`, the user is already redirected to accounts page. No change needed here.

**Step 3: Commit**

```bash
git add app/pages/accounts.py
git commit -m "feat(wa): set syncing status after QR connection, auto-redirect"
```

---

### Task 5: Python — Add sync-status polling endpoint and retry endpoint

**Files:**
- Modify: `app/pages/accounts.py` (add two new routes after `accounts_connect_wa_status`)

**Step 1: Add `GET /accounts/{account_id}/sync-status` endpoint**

Add after `accounts_connect_wa_status` (after line 351):

```python
@router.get("/accounts/{account_id}/sync-status", response_class=HTMLResponse)
async def accounts_sync_status(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """HTMX polling endpoint: check group sync progress and auto-save groups."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return HTMLResponse('<span class="text-sm text-red-600">Не авторизован</span>')

    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return HTMLResponse('<span class="text-sm text-red-600">Аккаунт не найден</span>')

    # Only poll for syncing accounts
    if account.status != "syncing":
        return HTMLResponse("")

    session_id = str(account.id)
    messenger = WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=session_id)

    try:
        sync_data = await messenger.get_sync_status()
        state = sync_data.get("state")

        if state == "ready":
            # Save groups to DB
            groups = sync_data.get("groups") or []
            existing = await db.execute(
                select(Group.group_external_id).where(
                    Group.account_id == account_id,
                    Group.user_id == user.id,
                )
            )
            existing_ids = {row[0] for row in existing}

            for g in groups:
                if g["id"] not in existing_ids:
                    db.add(
                        Group(
                            user_id=user.id,
                            account_id=account_id,
                            messenger_type="wa",
                            group_external_id=g["id"],
                            name=g["name"],
                        )
                    )

            account.status = "active"
            await db.commit()

            group_count = len(groups)
            return HTMLResponse(
                f'<tr id="account-row-{account_id}" class="hover:bg-slate-50/80 transition-colors duration-150">'
                f'<td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-900">{account.id}</td>'
                f'<td class="px-3 sm:px-6 py-4 text-sm text-slate-900">WhatsApp</td>'
                f'<td class="px-3 sm:px-6 py-4">'
                f'<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800">active</span>'
                f'<span class="ml-2 text-xs text-slate-500">Загружено {group_count} групп</span>'
                f'</td>'
                f'<td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-500">{account.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
                f'<td class="px-3 sm:px-6 py-4 text-right text-sm">'
                f'<form method="POST" action="/accounts/{account.id}/delete" class="inline">'
                f'<button type="submit" class="font-medium text-red-600 hover:text-red-700 transition-colors" onclick="return confirm(\'Удалить этот аккаунт?\')">Удалить</button>'
                f'</form></td></tr>'
            )

        if state == "failed":
            account.status = "sync_failed"
            await db.commit()

            return HTMLResponse(
                f'<tr id="account-row-{account_id}" class="hover:bg-slate-50/80 transition-colors duration-150">'
                f'<td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-900">{account.id}</td>'
                f'<td class="px-3 sm:px-6 py-4 text-sm text-slate-900">WhatsApp</td>'
                f'<td class="px-3 sm:px-6 py-4">'
                f'<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold bg-red-100 text-red-800">Ошибка синхронизации</span>'
                f'</td>'
                f'<td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-500">{account.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
                f'<td class="px-3 sm:px-6 py-4 text-right text-sm">'
                f'<form method="POST" action="/accounts/{account.id}/retry-sync" class="inline">'
                f'<button type="submit" class="font-medium text-amber-600 hover:text-amber-700 transition-colors mr-3">Повторить</button>'
                f'</form>'
                f'<form method="POST" action="/accounts/{account.id}/delete" class="inline">'
                f'<button type="submit" class="font-medium text-red-600 hover:text-red-700 transition-colors" onclick="return confirm(\'Удалить этот аккаунт?\')">Удалить</button>'
                f'</form></td></tr>'
            )

        # Still syncing — return spinner row (HTMX will keep polling)
        return HTMLResponse(
            f'<tr id="account-row-{account_id}" hx-get="/accounts/{account_id}/sync-status" hx-trigger="every 5s" hx-swap="outerHTML"'
            f' class="hover:bg-slate-50/80 transition-colors duration-150">'
            f'<td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-900">{account.id}</td>'
            f'<td class="px-3 sm:px-6 py-4 text-sm text-slate-900">WhatsApp</td>'
            f'<td class="px-3 sm:px-6 py-4">'
            f'<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800">'
            f'<svg class="animate-spin -ml-0.5 mr-1.5 h-3 w-3 text-amber-600" fill="none" viewBox="0 0 24 24">'
            f'<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>'
            f'<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>'
            f'Синхронизация...</span>'
            f'<span class="ml-2 text-xs text-slate-500">Загружаем группы из WhatsApp...</span>'
            f'</td>'
            f'<td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-500">{account.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            f'<td class="px-3 sm:px-6 py-4 text-right text-sm text-slate-400">Подождите...</td></tr>'
        )

    except Exception:
        return HTMLResponse(
            f'<tr id="account-row-{account_id}" hx-get="/accounts/{account_id}/sync-status" hx-trigger="every 5s" hx-swap="outerHTML"'
            f' class="hover:bg-slate-50/80 transition-colors duration-150">'
            f'<td colspan="5" class="px-3 sm:px-6 py-4 text-sm text-amber-600">Проверяем статус синхронизации...</td></tr>'
        )
```

**Step 2: Add `POST /accounts/{account_id}/retry-sync` endpoint**

Add after the sync-status endpoint:

```python
@router.post("/accounts/{account_id}/retry-sync")
async def accounts_retry_sync(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Retry failed group sync."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return RedirectResponse(url="/accounts", status_code=302)

    session_id = str(account.id)
    messenger = WhatsAppMessenger(bridge_url=settings.wa_bridge_url, session_id=session_id)
    await messenger.retry_sync()

    account.status = "syncing"
    await db.commit()

    return RedirectResponse(url="/accounts", status_code=302)
```

**Step 3: Commit**

```bash
git add app/pages/accounts.py
git commit -m "feat(wa): add sync-status polling and retry-sync endpoints"
```

---

### Task 6: Template — Update accounts list for syncing/sync_failed statuses

**Files:**
- Modify: `app/templates/accounts/list.html:26-46` (table rows)

**Step 1: Update the account row in the table body to handle syncing and sync_failed**

Replace the `{% for account in accounts %}` loop body (lines 26-46) with status-aware rows:

```html
{% for account in accounts %}
{% if account.status == 'syncing' and account.type == 'wa' %}
<tr id="account-row-{{ account.id }}" hx-get="/accounts/{{ account.id }}/sync-status" hx-trigger="every 5s" hx-swap="outerHTML" class="hover:bg-slate-50/80 transition-colors duration-150">
    <td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-900">{{ account.id }}</td>
    <td class="px-3 sm:px-6 py-4 text-sm text-slate-900">WhatsApp</td>
    <td class="px-3 sm:px-6 py-4">
        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800">
            <svg class="animate-spin -ml-0.5 mr-1.5 h-3 w-3 text-amber-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            Синхронизация...
        </span>
        <span class="ml-2 text-xs text-slate-500">Загружаем группы из WhatsApp. Это может занять несколько минут.</span>
    </td>
    <td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-500">{{ account.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
    <td class="px-3 sm:px-6 py-4 text-right text-sm text-slate-400">Подождите...</td>
</tr>
{% elif account.status == 'sync_failed' and account.type == 'wa' %}
<tr class="hover:bg-slate-50/80 transition-colors duration-150">
    <td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-900">{{ account.id }}</td>
    <td class="px-3 sm:px-6 py-4 text-sm text-slate-900">WhatsApp</td>
    <td class="px-3 sm:px-6 py-4">
        <span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold bg-red-100 text-red-800">Ошибка синхронизации</span>
    </td>
    <td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-500">{{ account.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
    <td class="px-3 sm:px-6 py-4 text-right text-sm">
        <form method="POST" action="/accounts/{{ account.id }}/retry-sync" class="inline">
            <button type="submit" class="font-medium text-amber-600 hover:text-amber-700 transition-colors mr-3">Повторить</button>
        </form>
        <form method="POST" action="/accounts/{{ account.id }}/delete" class="inline">
            <button type="submit" class="font-medium text-red-600 hover:text-red-700 transition-colors" onclick="return confirm('Удалить этот аккаунт?')">Удалить</button>
        </form>
    </td>
</tr>
{% else %}
<tr class="hover:bg-slate-50/80 transition-colors duration-150">
    <td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-900">{{ account.id }}</td>
    <td class="px-3 sm:px-6 py-4 text-sm text-slate-900">
        {% if account.type == 'tg_user' %}Telegram аккаунт
        {% elif account.type == 'wa' %}WhatsApp
        {% else %}{{ account.type }}{% endif %}
    </td>
    <td class="px-3 sm:px-6 py-4">
        <span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold {% if account.status == 'active' %}bg-emerald-100 text-emerald-800{% elif account.status == 'disconnected' %}bg-red-100 text-red-800{% else %}bg-amber-100 text-amber-800{% endif %}">
            {{ account.status }}
        </span>
    </td>
    <td class="hidden sm:table-cell px-3 sm:px-6 py-4 text-sm text-slate-500">{{ account.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
    <td class="px-3 sm:px-6 py-4 text-right text-sm">
        <form method="POST" action="/accounts/{{ account.id }}/delete" class="inline">
            <button type="submit" class="font-medium text-red-600 hover:text-red-700 transition-colors" onclick="return confirm('Удалить этот аккаунт?')">Удалить</button>
        </form>
    </td>
</tr>
{% endif %}
{% endfor %}
```

**Step 2: Commit**

```bash
git add app/templates/accounts/list.html
git commit -m "feat(wa): show syncing/sync_failed status in accounts list with HTMX polling"
```

---

### Task 7: Python — Also clean up `syncing` stale accounts on QR page

**Files:**
- Modify: `app/pages/accounts.py:224-245` (accounts_connect_wa_page)

**Step 1: Extend stale account cleanup to also clean `syncing` and `sync_failed` accounts**

Modify the stale cleanup query (lines 236-245) to also catch `syncing` and `sync_failed` status accounts, in addition to `connecting`:

```python
# Clean up stale connecting/failed accounts
stale = await db.execute(
    select(MessengerAccount).where(
        MessengerAccount.user_id == user.id,
        MessengerAccount.type == "wa",
        MessengerAccount.status.in_(["connecting", "syncing", "sync_failed"]),
    )
)
for old in stale.scalars().all():
    await db.delete(old)
await db.commit()
```

Also update the "already has active WA account" check (lines 225-233) to also redirect if `syncing` — user shouldn't start a new QR session while one is syncing:

```python
# Check if user already has an active or syncing WA account
existing = await db.execute(
    select(MessengerAccount).where(
        MessengerAccount.user_id == user.id,
        MessengerAccount.type == "wa",
        MessengerAccount.status.in_(["active", "syncing"]),
    )
)
if existing.scalar_one_or_none():
    return RedirectResponse(url="/accounts", status_code=302)
```

**Step 2: Commit**

```bash
git add app/pages/accounts.py
git commit -m "fix(wa): clean up stale syncing/sync_failed accounts, block new QR during sync"
```

---

### Task 8: Tests — Add test for sync-status polling endpoint

**Files:**
- Create: `tests/test_routes/test_wa_sync_status.py`

**Step 1: Write tests**

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.group import Group
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def wa_sync_setup():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
        wa_bridge_urls=["http://localhost:3000"],
    )
    app = create_app(settings=settings)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as client:
        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _login(client: AsyncClient) -> None:
    await client.post(
        "/register",
        data={"email": "wasync@test.com", "password": "pass123", "name": "WA Sync User"},
    )


@pytest.mark.asyncio
async def test_sync_status_returns_syncing_html(wa_sync_setup):
    """While bridge reports syncing, endpoint returns spinning row."""
    client, session_factory = wa_sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User
        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id, type="wa", credentials="1", status="syncing"
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockWA:
        instance = MockWA.return_value
        instance.get_sync_status = AsyncMock(return_value={"state": "syncing", "groups": None})

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "Синхронизация..." in resp.text


@pytest.mark.asyncio
async def test_sync_status_ready_saves_groups(wa_sync_setup):
    """When bridge reports ready, groups are saved and account becomes active."""
    client, session_factory = wa_sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User
        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id, type="wa", credentials="1", status="syncing"
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    mock_groups = [
        {"id": "111@g.us", "name": "Group A"},
        {"id": "222@g.us", "name": "Group B"},
    ]

    with patch("app.pages.accounts.WhatsAppMessenger") as MockWA:
        instance = MockWA.return_value
        instance.get_sync_status = AsyncMock(return_value={"state": "ready", "groups": mock_groups})

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "active" in resp.text

    async with session_factory() as session:
        groups = (await session.execute(
            select(Group).where(Group.account_id == account_id).order_by(Group.id)
        )).scalars().all()
        assert len(groups) == 2
        assert groups[0].group_external_id == "111@g.us"
        assert groups[1].group_external_id == "222@g.us"

        acc = (await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )).scalar_one()
        assert acc.status == "active"


@pytest.mark.asyncio
async def test_sync_status_failed_sets_sync_failed(wa_sync_setup):
    """When bridge reports failed, account status becomes sync_failed."""
    client, session_factory = wa_sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User
        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id, type="wa", credentials="1", status="syncing"
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockWA:
        instance = MockWA.return_value
        instance.get_sync_status = AsyncMock(return_value={"state": "failed", "groups": None})

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "Ошибка синхронизации" in resp.text

    async with session_factory() as session:
        acc = (await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )).scalar_one()
        assert acc.status == "sync_failed"


@pytest.mark.asyncio
async def test_retry_sync_resets_status(wa_sync_setup):
    """Retry sync resets sync_failed to syncing and calls bridge."""
    client, session_factory = wa_sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User
        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id, type="wa", credentials="1", status="sync_failed"
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockWA:
        instance = MockWA.return_value
        instance.retry_sync = AsyncMock(return_value={"status": "sync_started"})

        resp = await client.post(f"/accounts/{account_id}/retry-sync")

    assert resp.status_code == 200  # followed redirect

    async with session_factory() as session:
        acc = (await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )).scalar_one()
        assert acc.status == "syncing"
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_routes/test_wa_sync_status.py -v`
Expected: All 4 tests pass.

**Step 3: Commit**

```bash
git add tests/test_routes/test_wa_sync_status.py
git commit -m "test(wa): add tests for sync-status polling and retry-sync endpoints"
```

---

### Task 9: Run full test suite and verify

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All 223+ tests pass (existing + 4 new).

**Step 2: If any tests fail, fix them**

Common issues:
- Tests that check for `status == "active"` immediately after QR connection may need updating to expect `"syncing"` first
- Tests referencing the stale cleanup query may need `"syncing"` added to expected statuses

**Step 3: Final commit if fixes were needed**

```bash
git add -A
git commit -m "fix: update tests for new wa sync states"
```

---

### Summary of all files changed

| File | Action | Description |
|------|--------|-------------|
| `wa_bridge/index.js` | Modify | Add syncState, background group sync, increased timeout, new endpoints |
| `app/messengers/whatsapp.py` | Modify | Add `get_sync_status()` and `retry_sync()` methods |
| `app/pages/accounts.py` | Modify | Change connected→syncing, add sync-status + retry-sync endpoints, fix stale cleanup |
| `app/templates/accounts/list.html` | Modify | Add syncing/sync_failed row templates with HTMX polling |
| `tests/test_routes/test_wa_sync_status.py` | Create | 4 tests for sync-status and retry-sync |

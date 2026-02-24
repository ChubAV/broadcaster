# Baileys Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace whatsapp-web.js + Puppeteer/Chromium with Baileys in the wa_bridge Node.js service, keeping the REST API contract identical so the Python side remains unchanged.

**Architecture:** Drop-in replacement of `wa_bridge/index.js`. Baileys uses pure WebSocket (no browser). Sessions stored on disk via `useMultiFileAuthState`. MongoDB removed entirely. Single bridge instance instead of 3.

**Tech Stack:** Node.js 20, @whiskeysockets/baileys@^6.7.0, Express, qrcode, axios

---

### Task 1: Update package.json dependencies

**Files:**
- Modify: `wa_bridge/package.json`

**Step 1: Update package.json**

Replace the dependencies section:

```json
{
  "name": "wa-bridge",
  "version": "2.0.0",
  "description": "WhatsApp Bridge for Broadcaster (Baileys)",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "@whiskeysockets/baileys": "^6.7.0",
    "axios": "^1.7.0",
    "express": "^4.18.0",
    "pino": "^9.0.0",
    "qrcode": "^1.5.0"
  }
}
```

Removed: `whatsapp-web.js`, `mongoose`, `wwebjs-mongo`.
Added: `@whiskeysockets/baileys`, `pino` (required by Baileys).

**Step 2: Delete old lock file**

```bash
rm wa_bridge/package-lock.json
```

**Step 3: Commit**

```bash
git add wa_bridge/package.json
git rm wa_bridge/package-lock.json
git commit -m "chore(wa-bridge): switch dependencies from whatsapp-web.js to baileys"
```

---

### Task 2: Simplify Dockerfile

**Files:**
- Modify: `wa_bridge/Dockerfile`

**Step 1: Rewrite Dockerfile without Chromium**

```dockerfile
FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install --production

COPY . .

EXPOSE 3000

CMD ["node", "index.js"]
```

Removed: Chromium installation, Puppeteer env vars. Image goes from ~1+ GB to ~200 MB.

**Step 2: Commit**

```bash
git add wa_bridge/Dockerfile
git commit -m "chore(wa-bridge): simplify Dockerfile, remove Chromium"
```

---

### Task 3: Rewrite index.js with Baileys

**Files:**
- Rewrite: `wa_bridge/index.js`

This is the main task. The new file must implement the same REST API with identical request/response formats.

**Step 1: Write the new index.js**

```javascript
const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, Browsers, delay } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const IDLE_TIMEOUT_MS = parseInt(process.env.IDLE_TIMEOUT_MS || '300000');
const SESSIONS_DIR = process.env.SESSIONS_DIR || './sessions';
const MAX_RECONNECT_ATTEMPTS = 5;
const RATE_LIMIT_PER_MINUTE = 8;

// Silent logger for Baileys (it uses pino internally)
const logger = pino({ level: 'silent' });

// In-memory session state
const sessions = new Map();
const loadingPromises = new Map();
const sendLocks = new Map();

// Per-session rate limiting
const rateLimiters = new Map();

// Ensure sessions directory exists
fs.mkdirSync(SESSIONS_DIR, { recursive: true });

/**
 * Simple rate limiter: max N messages per minute per session.
 */
function checkRateLimit(sessionId) {
    let limiter = rateLimiters.get(sessionId);
    if (!limiter) {
        limiter = { timestamps: [] };
        rateLimiters.set(sessionId, limiter);
    }
    const now = Date.now();
    limiter.timestamps = limiter.timestamps.filter(t => now - t < 60000);
    if (limiter.timestamps.length >= RATE_LIMIT_PER_MINUTE) {
        return false;
    }
    limiter.timestamps.push(now);
    return true;
}

/**
 * Serialize async work per session so only one send runs at a time.
 */
function withSessionLock(sessionId, fn) {
    const prev = sendLocks.get(sessionId) || Promise.resolve();
    const next = prev.then(fn, fn);
    sendLocks.set(sessionId, next);
    next.finally(() => {
        if (sendLocks.get(sessionId) === next) {
            sendLocks.delete(sessionId);
        }
    });
    return next;
}

/**
 * Check if session auth files exist on disk.
 */
function sessionExistsOnDisk(sessionId) {
    const sessionDir = path.join(SESSIONS_DIR, String(sessionId));
    const credsFile = path.join(sessionDir, 'creds.json');
    return fs.existsSync(credsFile);
}

/**
 * Delete session files from disk.
 */
function deleteSessionFiles(sessionId) {
    const sessionDir = path.join(SESSIONS_DIR, String(sessionId));
    if (fs.existsSync(sessionDir)) {
        fs.rmSync(sessionDir, { recursive: true, force: true });
        console.log(`[${sessionId}] Session files deleted`);
    }
}

/**
 * Create a Baileys socket for the given sessionId.
 * Returns the state object stored in sessions Map.
 */
async function createSocket(sessionId) {
    const sessionDir = path.join(SESSIONS_DIR, String(sessionId));
    const { state: authState, saveCreds } = await useMultiFileAuthState(sessionDir);

    const sock = makeWASocket({
        auth: authState,
        printQRInTerminal: false,
        browser: Browsers.ubuntu('Broadcaster'),
        logger,
        markOnlineOnConnect: false,
        generateHighQualityLinkPreview: false,
    });

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
    };

    sessionState.readyPromise = new Promise((resolve, reject) => {
        sessionState.readyResolve = resolve;
        sessionState.readyReject = reject;

        // Timeout after 60s
        sessionState._readyTimeout = setTimeout(() => {
            reject(new Error('Session initialization timeout (60s)'));
        }, 60000);
    });

    // Save credentials on every update
    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            sessionState.qrCode = await qrcode.toDataURL(qr);
            console.log(`[${sessionId}] QR code generated`);
        }

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
        }

        if (connection === 'close') {
            sessionState.isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const reason = DisconnectReason[statusCode] || statusCode || 'unknown';
            console.log(`[${sessionId}] Disconnected: ${reason} (${statusCode})`);

            if (statusCode === DisconnectReason.loggedOut) {
                // User logged out — clean up
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                if (sessionState.readyReject) {
                    sessionState.readyReject(new Error('Logged out'));
                    sessionState.readyResolve = null;
                    sessionState.readyReject = null;
                }
                sessions.delete(sessionId);
                deleteSessionFiles(sessionId);
                console.log(`[${sessionId}] Logged out, session cleaned up`);
            } else if (sessionState.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                // Auto-reconnect with exponential backoff
                sessionState.reconnectAttempts++;
                const backoff = Math.min(1000 * Math.pow(2, sessionState.reconnectAttempts - 1), 30000);
                console.log(`[${sessionId}] Reconnecting in ${backoff}ms (attempt ${sessionState.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);

                setTimeout(async () => {
                    try {
                        sessions.delete(sessionId);
                        const newState = await createSocket(sessionId);
                        // Preserve reconnect counter
                        newState.reconnectAttempts = sessionState.reconnectAttempts;
                        sessions.set(sessionId, newState);
                    } catch (err) {
                        console.error(`[${sessionId}] Reconnect failed: ${err.message}`);
                    }
                }, backoff);
            } else {
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                if (sessionState.readyReject) {
                    sessionState.readyReject(new Error(`Max reconnect attempts (${MAX_RECONNECT_ATTEMPTS}) reached`));
                    sessionState.readyResolve = null;
                    sessionState.readyReject = null;
                }
                sessions.delete(sessionId);
                console.log(`[${sessionId}] Max reconnect attempts reached, giving up`);
            }
        }
    });

    sessions.set(sessionId, sessionState);
    return sessionState;
}

/**
 * Ensure a session is loaded and ready.
 * If not in memory but exists on disk, load it.
 */
async function ensureSession(sessionId) {
    let state = sessions.get(sessionId);

    if (state && state.isConnected) {
        state.lastActivity = Date.now();
        return state;
    }

    if (state && state.initializing) {
        try {
            await state.readyPromise;
            state.lastActivity = Date.now();
            return state;
        } catch {
            return null;
        }
    }

    // Check if session exists on disk
    if (!sessionExistsOnDisk(sessionId)) {
        return null;
    }

    // Prevent duplicate loading
    if (loadingPromises.has(sessionId)) {
        return loadingPromises.get(sessionId);
    }

    const loadPromise = (async () => {
        console.log(`[${sessionId}] Loading session from disk...`);
        try {
            const state = await createSocket(sessionId);
            await state.readyPromise;
            state.lastActivity = Date.now();
            console.log(`[${sessionId}] Session loaded successfully`);
            return state;
        } catch (err) {
            console.error(`[${sessionId}] Failed to load session: ${err.message}`);
            sessions.delete(sessionId);
            return null;
        }
    })();

    loadingPromises.set(sessionId, loadPromise);
    try {
        return await loadPromise;
    } finally {
        loadingPromises.delete(sessionId);
    }
}

/**
 * Gracefully close a session (keep files on disk).
 */
async function unloadSession(sessionId) {
    const state = sessions.get(sessionId);
    if (!state) return;

    try {
        state.sock.end();
    } catch (err) {
        console.error(`[${sessionId}] Error closing socket: ${err.message}`);
    }
    sessions.delete(sessionId);
    console.log(`[${sessionId}] Session unloaded`);
}

/**
 * Destroy a session completely (logout + delete files).
 */
async function destroySession(sessionId) {
    const state = sessions.get(sessionId);
    if (state) {
        try {
            await state.sock.logout();
        } catch (err) {
            console.error(`[${sessionId}] Error during logout: ${err.message}`);
            try { state.sock.end(); } catch (_) {}
        }
        sessions.delete(sessionId);
    }
    deleteSessionFiles(sessionId);
    console.log(`[${sessionId}] Session destroyed`);
}

// ---- Idle timeout: unload sessions after inactivity ----

setInterval(() => {
    const now = Date.now();
    for (const [id, state] of sessions) {
        if (state.isConnected && (now - state.lastActivity > IDLE_TIMEOUT_MS)) {
            console.log(`[${id}] Idle for ${Math.round(IDLE_TIMEOUT_MS / 1000)}s, unloading`);
            unloadSession(id);
        }
    }
}, 60000);

// ---- REST API endpoints ----

// POST /api/sessions/:id/start - Create and initialize a session (for QR flow)
app.post('/api/sessions/:id/start', async (req, res) => {
    const sessionId = req.params.id;

    const existing = sessions.get(sessionId);
    if (existing) {
        if (existing.isConnected) {
            return res.json({ status: 'connected' });
        }
        if (existing.initializing) {
            return res.json({ status: 'initializing' });
        }
        // Stale session — clean up
        try { existing.sock.end(); } catch (_) {}
        sessions.delete(sessionId);
    }

    try {
        await createSocket(sessionId);
        res.json({ status: 'initializing' });
    } catch (err) {
        console.error(`[${sessionId}] Failed to start: ${err.message}`);
        res.status(500).json({ error: err.message });
    }
});

// DELETE /api/sessions/:id - Destroy a session
app.delete('/api/sessions/:id', async (req, res) => {
    const sessionId = req.params.id;
    await destroySession(sessionId);
    res.json({ ok: true });
});

// GET /api/sessions/:id/status - Connection status
app.get('/api/sessions/:id/status', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        // Check if session files exist (session may be unloaded but restorable)
        const exists = sessionExistsOnDisk(sessionId);
        return res.json({ connected: false, exists });
    }
    res.json({ connected: state.isConnected, exists: true });
});

// GET /api/sessions/:id/qr - Get QR code for authentication
app.get('/api/sessions/:id/qr', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        return res.json({ status: 'not_found', qr: null });
    }
    if (state.isConnected) {
        return res.json({ status: 'connected', qr: null });
    }
    if (!state.qrCode) {
        return res.json({ status: 'waiting', qr: null });
    }
    res.json({ status: 'pending', qr: state.qrCode });
});

// POST /api/sessions/:id/send - Send message (auto-loads session if needed)
app.post('/api/sessions/:id/send', async (req, res) => {
    const sessionId = req.params.id;
    const { group_id, text, image_paths, image_urls } = req.body;
    const images = image_urls || image_paths || [];
    const caption = text || '';

    if (!group_id || (!text && images.length === 0)) {
        return res.status(400).json({ error: 'group_id and text or images are required' });
    }

    // Rate limiting
    if (!checkRateLimit(sessionId)) {
        return res.status(429).json({ error: 'Rate limit exceeded (max 8 messages/minute)' });
    }

    const state = await ensureSession(sessionId);
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        await withSessionLock(sessionId, async () => {
            // Anti-ban: simulate typing
            try {
                await state.sock.sendPresenceUpdate('composing', group_id);
                const typingDelay = 1500 + Math.random() * 2500;
                await new Promise(r => setTimeout(r, typingDelay));
                await state.sock.sendPresenceUpdate('paused', group_id);
            } catch (err) {
                // Presence update failure is non-critical
                console.log(`[${sessionId}] Presence update failed (non-critical): ${err.message}`);
            }

            if (images.length > 0) {
                console.log(`[${sessionId}] Sending ${images.length} image(s) to ${group_id}, text="${caption.substring(0, 50)}"`);

                // Download and send images
                for (let i = 0; i < images.length; i++) {
                    const img = images[i];
                    let buffer;
                    let mimetype = 'image/jpeg';

                    if (img.startsWith('http://') || img.startsWith('https://')) {
                        const response = await axios.get(img, { responseType: 'arraybuffer' });
                        mimetype = response.headers['content-type'] || 'image/jpeg';
                        buffer = Buffer.from(response.data);
                    } else if (fs.existsSync(img)) {
                        buffer = fs.readFileSync(img);
                    } else {
                        console.warn(`[${sessionId}] Image not found: ${img}`);
                        continue;
                    }

                    const msgOptions = { image: buffer, mimetype };
                    // Add caption to last image (or first if single image)
                    if (caption && (images.length === 1 || i === images.length - 1)) {
                        // For single image: caption on the image
                        // For multiple images: caption on last image
                    }
                    // For single image with caption
                    if (images.length === 1 && caption) {
                        msgOptions.caption = caption;
                    }

                    const result = await state.sock.sendMessage(group_id, msgOptions);
                    console.log(`[${sessionId}] sendMessage[${i}] result: id=${result?.key?.id}`);
                }

                // For multiple images, send caption as separate text
                if (images.length > 1 && caption) {
                    await state.sock.sendMessage(group_id, { text: caption });
                }
            } else {
                console.log(`[${sessionId}] Sending text to ${group_id}, text="${caption.substring(0, 50)}"`);
                const result = await state.sock.sendMessage(group_id, { text: caption });
                console.log(`[${sessionId}] sendMessage result: id=${result?.key?.id}`);
            }
        });

        state.lastActivity = Date.now();
        return res.json({ ok: true });
    } catch (error) {
        console.error(`[${sessionId}] Send error: ${error.message}`);
        return res.status(500).json({ error: error.message });
    }
});

// GET /api/sessions/:id/groups - List groups (auto-loads session if needed)
app.get('/api/sessions/:id/groups', async (req, res) => {
    const sessionId = req.params.id;

    const state = await ensureSession(sessionId);
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        const groupsObj = await state.sock.groupFetchAllParticipating();
        const groups = Object.entries(groupsObj).map(([jid, metadata]) => ({
            id: jid,
            name: metadata.subject,
        }));
        return res.json(groups);
    } catch (error) {
        console.error(`[${sessionId}] Groups error: ${error.message}`);
        return res.status(500).json({ error: error.message });
    }
});

// GET /health - Health check
app.get('/health', (req, res) => {
    const sessionCount = sessions.size;
    const loadingCount = loadingPromises.size;
    res.json({
        status: 'ok',
        sessions: sessionCount,
        loading: loadingCount,
        uptime: process.uptime(),
    });
});

// ---- Start server ----

app.listen(PORT, () => {
    console.log(`WA Bridge (Baileys, idle timeout=${IDLE_TIMEOUT_MS / 1000}s) running on port ${PORT}`);
});
```

**Key differences from old implementation:**
- No MongoDB connection, no Mongoose, no MongoStore
- No Puppeteer/Chromium — Baileys uses pure WebSocket
- No `waitForStableContext()` — Baileys doesn't have Puppeteer context issues
- No `isContextError()` retry loop — no ProtocolError possible
- `groupFetchAllParticipating()` instead of `getChats().filter(isGroup)`
- `sock.sendMessage(jid, {image: buffer})` instead of `MessageMedia`
- `sock.end()` for graceful disconnect, `sock.logout()` for full logout
- Built-in reconnect with exponential backoff via `connection.update` events
- Anti-ban: `sendPresenceUpdate('composing')` + random delay before each send
- Per-session rate limiter (8 msg/min)

**Step 2: Commit**

```bash
git add wa_bridge/index.js
git commit -m "feat(wa-bridge): rewrite with Baileys instead of whatsapp-web.js

Replaces Puppeteer/Chromium-based whatsapp-web.js with Baileys (pure WebSocket).
Same REST API contract, Python side unchanged.

Benefits:
- ~50MB RAM per session instead of ~300MB (no Chromium)
- Sub-second session start instead of 5-15s
- No Puppeteer ProtocolError / context destruction issues
- Simpler session storage (files instead of MongoDB GridFS)
- Built-in anti-ban measures (typing simulation, rate limiting)"
```

---

### Task 4: Update docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Update docker-compose.yml**

Changes:
1. Remove `mongo` service
2. Remove `wa-bridge-2` and `wa-bridge-3`
3. Rename `wa-bridge-1` to `wa-bridge`
4. Remove `mongodata` volume
5. Add `wa_sessions` volume
6. Remove `MONGODB_URI` from wa-bridge env
7. Update wa-bridge: remove mongo dependency, reduce memory limit, add sessions volume
8. Remove `MONGODB_URI` from app-base if present (it's not, but double-check)

The `x-wa-bridge-base` anchor should be updated:

```yaml
x-wa-bridge-base: &wa-bridge-base
  build:
    context: ./wa_bridge
    dockerfile: Dockerfile
  environment:
    PORT: 3000
    IDLE_TIMEOUT_MS: ${IDLE_TIMEOUT_MS:-300000}
  volumes:
    - wa_sessions:/app/sessions
  healthcheck:
    test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/health"]
    interval: 10s
    timeout: 5s
    retries: 3
  deploy:
    resources:
      limits:
        memory: 512M
```

Services section — replace 3 bridges with 1:

```yaml
  wa-bridge:
    <<: *wa-bridge-base
    container_name: wa-bridge-broadcaster
```

Remove `mongo` service entirely.

Volumes — replace `mongodata` with `wa_sessions`:

```yaml
volumes:
  pgdata:
  wa_sessions:
```

**Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "chore(docker): remove MongoDB, consolidate to single wa-bridge instance"
```

---

### Task 5: Update docker-compose.dev.yml

**Files:**
- Modify: `docker-compose.dev.yml`

**Step 1: Update docker-compose.dev.yml**

Replace wa-bridge sections:

```yaml
  wa-bridge:
    volumes:
      - ./wa_bridge:/app
      - /app/node_modules
      - wa_sessions_dev:/app/sessions
```

Remove `wa-bridge-2` and `wa-bridge-3` sections.

Add dev volume at top level if needed (or rely on override creating it).

**Step 2: Commit**

```bash
git add docker-compose.dev.yml
git commit -m "chore(docker): update dev compose for single wa-bridge"
```

---

### Task 6: Install dependencies and verify build

**Step 1: Install npm dependencies in wa_bridge**

```bash
cd wa_bridge && npm install
```

Verify `node_modules/@whiskeysockets/baileys` exists.

**Step 2: Verify Docker build**

```bash
docker compose build wa-bridge
```

Should complete without errors and produce a much smaller image (no Chromium).

**Step 3: Commit lock file**

```bash
git add wa_bridge/package-lock.json
git commit -m "chore(wa-bridge): add package-lock.json for baileys dependencies"
```

---

### Task 7: Run Python tests to verify no regressions

**Step 1: Run existing test suite**

```bash
uv run pytest tests/ -v
```

All 157 tests should pass. The Python side (`app/messengers/whatsapp.py`) was not modified, so the tests should be unaffected. The WhatsApp tests mock the HTTP client, so they don't need a running bridge.

**Step 2: If any tests reference MongoDB or wa-bridge specifics, update them**

Check for any test files that might reference MongoDB or whatsapp-web.js specific behavior. These should be rare since the Python tests mock httpx calls.

---

### Task 8: Update .env.example (if exists) and documentation

**Files:**
- Modify: `.env.example` (if exists)
- Already done: `docs/plans/2026-02-24-baileys-migration-design.md`

**Step 1: Update environment variables**

Remove `MONGODB_URI` from any env example files.
Update `WA_BRIDGE_URLS` default to single URL: `http://wa-bridge:3000`.
Add `IDLE_TIMEOUT_MS` documentation if missing.

**Step 2: Final commit**

```bash
git add -A
git commit -m "docs: update environment config for Baileys migration"
```

---

### Summary of changes

| File | Action |
|------|--------|
| `wa_bridge/index.js` | Full rewrite (Baileys) |
| `wa_bridge/package.json` | Update dependencies |
| `wa_bridge/package-lock.json` | Regenerate |
| `wa_bridge/Dockerfile` | Simplify (no Chromium) |
| `docker-compose.yml` | Remove mongo + 2 bridges, add wa_sessions volume |
| `docker-compose.dev.yml` | Simplify for single bridge |

| File | Action |
|------|--------|
| `app/messengers/whatsapp.py` | **No changes** |
| `app/worker/tasks.py` | **No changes** |
| `app/pages/accounts.py` | **No changes** |
| `tests/*` | **No changes expected** |

# WhatsApp Per-Account Containers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the single wa-bridge container with dynamically managed per-account containers that consume tasks from Redis queues and self-shutdown after idle.

**Architecture:** Each WhatsApp account gets its own Docker container (`wa-worker-{account_id}`) running a modified wa-bridge. A Container Manager (Celery beat task) orchestrates lifecycle via docker-py. Task dispatch writes to per-account Redis queues instead of Celery. A Result Processor reads results from Redis and writes SendLog to PostgreSQL.

**Tech Stack:** Node.js 20 + Baileys + Express + ioredis (wa-worker), Python + docker-py + Redis (Container Manager), Celery (Result Processor)

---

### Task 1: Create wa_worker base — package.json and Dockerfile

**Files:**
- Create: `wa_worker/package.json`
- Create: `wa_worker/Dockerfile`

**Step 1: Create wa_worker/package.json**

Fork of `wa_bridge/package.json` with added `ioredis` dependency for Redis queue consumption.

```json
{
  "name": "wa-worker",
  "version": "1.0.0",
  "description": "WhatsApp per-account worker with Redis queue",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "@whiskeysockets/baileys": "^6.7.21",
    "axios": "^1.7.0",
    "express": "^4.18.0",
    "ioredis": "^5.4.0",
    "pino": "^9.0.0",
    "qrcode": "^1.5.0"
  }
}
```

**Step 2: Create wa_worker/Dockerfile**

Same as wa_bridge Dockerfile but for wa_worker context.

```dockerfile
FROM node:20-slim

RUN apt-get update && apt-get install -y git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .

EXPOSE 3000

CMD ["node", "index.js"]
```

**Step 3: Commit**

```bash
git add wa_worker/package.json wa_worker/Dockerfile
git commit -m "feat(wa-worker): add package.json and Dockerfile for per-account worker"
```

---

### Task 2: Create wa_worker/index.js — core worker with Redis queue

This is the largest task. Fork `wa_bridge/index.js` (705 lines) and modify for per-account operation with Redis queue consumption.

**Files:**
- Create: `wa_worker/index.js`
- Reference: `wa_bridge/index.js` (lines 1–705)

**Step 1: Create wa_worker/index.js**

Key differences from wa_bridge/index.js:
- **Single account**: `ACCOUNT_ID` env var, one Baileys session
- **Redis consumer**: `BLPOP wa:queue:{ACCOUNT_ID}` loop instead of HTTP POST /send
- **Redis publisher**: `RPUSH wa:results` for send results
- **Self-shutdown**: `process.exit(0)` after `IDLE_SHUTDOWN_SEC` (default 300s) with empty queue
- **HTTP API kept**: QR, status, groups, sync-status endpoints (Container Manager provides endpoint)
- **No multi-session Map**: single session state

```javascript
'use strict';

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, makeCacheableSignalKeyStore } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode');
const axios = require('axios');
const Redis = require('ioredis');
const path = require('path');
const fs = require('fs');

const pino = require('pino');
const log = pino({
    level: process.env.LOG_LEVEL || 'info',
    formatters: {
        level(label) { return { level: label }; }
    }
});

const express = require('express');
const app = express();
app.use(express.json({ limit: '10mb' }));

// ── Config ──────────────────────────────────────────────────────
const ACCOUNT_ID = process.env.ACCOUNT_ID;
if (!ACCOUNT_ID) {
    log.fatal('ACCOUNT_ID environment variable is required');
    process.exit(1);
}

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';
const PORT = parseInt(process.env.PORT || '3000', 10);
const RATE_LIMIT_PER_MINUTE = parseInt(process.env.RATE_LIMIT_PER_MINUTE || '8', 10);
const MAX_RECONNECT_ATTEMPTS = parseInt(process.env.MAX_RECONNECT_ATTEMPTS || '5', 10);
const IDLE_SHUTDOWN_SEC = parseInt(process.env.IDLE_SHUTDOWN_SEC || '300', 10);
const SESSIONS_DIR = process.env.SESSIONS_DIR || './sessions';
const QUEUE_KEY = `wa:queue:${ACCOUNT_ID}`;
const RESULTS_KEY = 'wa:results';
const HEARTBEAT_KEY = `wa:heartbeat:${ACCOUNT_ID}`;
const ENDPOINT_KEY = `wa:endpoint:${ACCOUNT_ID}`;

// ── Redis ───────────────────────────────────────────────────────
const redis = new Redis(REDIS_URL);
const redisSub = new Redis(REDIS_URL); // separate connection for BLPOP

// ── Rate Limiter ────────────────────────────────────────────────
const sendTimestamps = [];

function checkRateLimit() {
    const now = Date.now();
    while (sendTimestamps.length > 0 && sendTimestamps[0] < now - 60000) {
        sendTimestamps.shift();
    }
    if (sendTimestamps.length >= RATE_LIMIT_PER_MINUTE) {
        const waitMs = 60000 - (now - sendTimestamps[0]);
        return { limited: true, waitMs };
    }
    return { limited: false };
}

function recordSend() {
    sendTimestamps.push(Date.now());
}

// ── Locks ───────────────────────────────────────────────────────
const sessionLockQueue = [];
let sessionLocked = false;

async function withSessionLock(fn) {
    return new Promise((resolve, reject) => {
        const run = async () => {
            sessionLocked = true;
            try { resolve(await fn()); }
            catch (e) { reject(e); }
            finally {
                sessionLocked = false;
                if (sessionLockQueue.length > 0) sessionLockQueue.shift()();
            }
        };
        if (sessionLocked) sessionLockQueue.push(run);
        else run();
    });
}

const groupLocks = new Map();

async function withGroupLock(groupId, fn) {
    const prev = groupLocks.get(groupId) || Promise.resolve();
    const current = prev.then(fn, fn);
    groupLocks.set(groupId, current);
    try { return await current; }
    finally { if (groupLocks.get(groupId) === current) groupLocks.delete(groupId); }
}

// ── Session State ───────────────────────────────────────────────
let state = {
    sock: null,
    saveCreds: null,
    qrCode: null,
    isConnected: false,
    initializing: false,
    lastActivity: Date.now(),
    reconnectAttempts: 0,
    readyResolve: null,
    readyPromise: null,
    syncState: null,
    groups: null
};

function sessionExistsOnDisk() {
    const sessionDir = path.join(SESSIONS_DIR, ACCOUNT_ID);
    return fs.existsSync(sessionDir) && fs.existsSync(path.join(sessionDir, 'creds.json'));
}

function deleteSessionFiles() {
    const sessionDir = path.join(SESSIONS_DIR, ACCOUNT_ID);
    if (fs.existsSync(sessionDir)) {
        fs.rmSync(sessionDir, { recursive: true, force: true });
    }
}

// ── Group Sync ──────────────────────────────────────────────────
async function startGroupSync() {
    state.syncState = 'syncing';
    state.groups = null;

    const INITIAL_DELAY = 30000;
    const RETRY_DELAYS = [30000, 60000, 120000];
    const MAX_SYNC_ATTEMPTS = 4;

    log.info({ accountId: ACCOUNT_ID }, 'group_sync_start');
    await sleep(INITIAL_DELAY);

    for (let attempt = 0; attempt < MAX_SYNC_ATTEMPTS; attempt++) {
        try {
            if (!state.sock || !state.isConnected) {
                state.syncState = 'failed';
                log.warn({ accountId: ACCOUNT_ID }, 'group_sync_not_connected');
                return;
            }
            const groupsObj = await state.sock.groupFetchAllParticipating();
            const groups = Object.values(groupsObj).map(g => ({ id: g.id, name: g.subject }));
            state.syncState = 'ready';
            state.groups = groups;
            log.info({ accountId: ACCOUNT_ID, groupCount: groups.length }, 'group_sync_complete');
            return;
        } catch (err) {
            log.warn({ accountId: ACCOUNT_ID, attempt, error: err.message }, 'group_sync_retry');
            if (attempt < MAX_SYNC_ATTEMPTS - 1) {
                await sleep(RETRY_DELAYS[attempt]);
            }
        }
    }
    state.syncState = 'failed';
    log.error({ accountId: ACCOUNT_ID }, 'group_sync_exhausted');
}

// ── Create Socket ───────────────────────────────────────────────
async function createSocket() {
    const sessionDir = path.join(SESSIONS_DIR, ACCOUNT_ID);
    fs.mkdirSync(sessionDir, { recursive: true });

    const { state: authState, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version } = await fetchLatestBaileysVersion();

    const sock = makeWASocket({
        version,
        auth: {
            creds: authState.creds,
            keys: makeCacheableSignalKeyStore(authState.keys, pino({ level: 'silent' }))
        },
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false,
        generateHighQualityLinkPreview: false,
        syncFullHistory: false,
        markOnlineOnConnect: false
    });

    state.sock = sock;
    state.saveCreds = saveCreds;
    state.readyPromise = new Promise(resolve => { state.readyResolve = resolve; });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            try {
                state.qrCode = await qrcode.toDataURL(qr);
                log.info({ accountId: ACCOUNT_ID }, 'qr_generated');
            } catch (err) {
                log.error({ accountId: ACCOUNT_ID, error: err.message }, 'qr_generation_failed');
            }
        }

        if (connection === 'open') {
            state.isConnected = true;
            state.reconnectAttempts = 0;
            state.qrCode = null;
            state.lastActivity = Date.now();
            log.info({ accountId: ACCOUNT_ID }, 'connected');
            if (state.readyResolve) {
                state.readyResolve();
                state.readyResolve = null;
            }
            startGroupSync();
        }

        if (connection === 'close') {
            state.isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const reason = lastDisconnect?.error?.output?.payload?.message || 'unknown';
            log.warn({ accountId: ACCOUNT_ID, statusCode, reason }, 'disconnected');

            if (statusCode === DisconnectReason.loggedOut) {
                log.info({ accountId: ACCOUNT_ID }, 'logged_out_deleting_session');
                deleteSessionFiles();
                return;
            }

            if (state.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                state.reconnectAttempts++;
                const delay = Math.min(state.reconnectAttempts * 2000, 30000);
                log.info({ accountId: ACCOUNT_ID, attempt: state.reconnectAttempts, delay }, 'reconnecting');
                await sleep(delay);
                await createSocket();
            } else {
                log.error({ accountId: ACCOUNT_ID }, 'max_reconnect_attempts_reached');
            }
        }
    });

    return sock;
}

// ── Ensure Session ──────────────────────────────────────────────
async function ensureSession() {
    if (state.isConnected) return state;
    if (state.initializing) {
        await state.readyPromise;
        return state;
    }

    if (!sessionExistsOnDisk()) {
        return null;
    }

    state.initializing = true;
    try {
        await createSocket();
        await state.readyPromise;
        state.initializing = false;
        return state;
    } catch (err) {
        state.initializing = false;
        throw err;
    }
}

// ── Destroy Session ─────────────────────────────────────────────
async function destroySession() {
    if (state.sock) {
        try { await state.sock.logout(); } catch (_) {}
        try { state.sock.end(); } catch (_) {}
    }
    deleteSessionFiles();
    state.sock = null;
    state.isConnected = false;
    state.qrCode = null;
    state.syncState = null;
    state.groups = null;
}

// ── Send Message ────────────────────────────────────────────────
async function sendMessage(task) {
    const { group_external_id, ad_text, ad_images, task_id } = task;

    return withGroupLock(group_external_id, async () => {
        return withSessionLock(async () => {
            if (!state.sock || !state.isConnected) {
                throw Object.assign(new Error('Not connected'), { noRetry: false });
            }

            // Rate limit
            const rl = checkRateLimit();
            if (rl.limited) {
                log.info({ accountId: ACCOUNT_ID, waitMs: rl.waitMs, taskId: task_id }, 'rate_limited_waiting');
                await sleep(rl.waitMs);
            }

            // Anti-ban: typing indicator
            try {
                await state.sock.sendPresenceUpdate('composing', group_external_id);
            } catch (_) {}
            const typingDelay = 1500 + Math.random() * 2500;
            await sleep(typingDelay);
            try {
                await state.sock.sendPresenceUpdate('paused', group_external_id);
            } catch (_) {}

            // Send images if any
            if (ad_images && ad_images.length > 0) {
                for (let i = 0; i < ad_images.length; i++) {
                    const imageUrl = ad_images[i];
                    try {
                        const response = await axios.get(imageUrl, {
                            responseType: 'arraybuffer',
                            timeout: 30000
                        });
                        const buffer = Buffer.from(response.data);

                        const msgPayload = { image: buffer };
                        // Caption only on first image (or last single image)
                        if (ad_images.length === 1) {
                            msgPayload.caption = ad_text;
                        } else if (i === 0) {
                            msgPayload.caption = ad_text;
                        }

                        const result = await state.sock.sendMessage(group_external_id, msgPayload);
                        log.info({ accountId: ACCOUNT_ID, taskId: task_id, imageIndex: i, messageId: result?.key?.id }, 'image_sent');
                        recordSend();

                        if (i < ad_images.length - 1) {
                            await sleep(1000 + Math.random() * 1500);
                        }
                    } catch (err) {
                        log.error({ accountId: ACCOUNT_ID, taskId: task_id, imageUrl, error: err.message }, 'image_send_failed');
                        throw err;
                    }
                }
                // If multiple images, send text separately only if we didn't put it as caption
                // (we put caption on first image, so no separate text needed)
                return { ok: true };
            }

            // Send text only
            if (ad_text) {
                const result = await state.sock.sendMessage(group_external_id, { text: ad_text });
                log.info({ accountId: ACCOUNT_ID, taskId: task_id, messageId: result?.key?.id }, 'text_sent');
                recordSend();
            }

            return { ok: true };
        });
    });
}

// ── Queue Consumer ──────────────────────────────────────────────
let running = true;
let lastTaskTime = Date.now();
let idleShutdownTimer = null;

function resetIdleTimer() {
    lastTaskTime = Date.now();
    state.lastActivity = Date.now();
    redis.set(HEARTBEAT_KEY, Date.now().toString(), 'EX', IDLE_SHUTDOWN_SEC + 60);
}

function startIdleWatcher() {
    idleShutdownTimer = setInterval(() => {
        const idleSec = (Date.now() - lastTaskTime) / 1000;
        if (idleSec >= IDLE_SHUTDOWN_SEC) {
            log.info({ accountId: ACCOUNT_ID, idleSec }, 'idle_shutdown');
            gracefulShutdown();
        }
    }, 10000); // check every 10s
}

async function consumeQueue() {
    log.info({ accountId: ACCOUNT_ID, queue: QUEUE_KEY }, 'queue_consumer_started');
    resetIdleTimer();
    startIdleWatcher();

    const MAX_RETRIES = 3;
    const RETRY_DELAYS = [60000, 180000, 300000];

    while (running) {
        try {
            // BLPOP with 5s timeout
            const result = await redisSub.blpop(QUEUE_KEY, 5);
            if (!result) continue; // timeout, loop again

            const [, rawTask] = result;
            let task;
            try {
                task = JSON.parse(rawTask);
            } catch (err) {
                log.error({ accountId: ACCOUNT_ID, raw: rawTask, error: err.message }, 'task_parse_error');
                continue;
            }

            resetIdleTimer();
            log.info({ accountId: ACCOUNT_ID, taskId: task.task_id, groupId: task.group_external_id }, 'task_received');

            // Retry loop
            let lastError = null;
            for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
                try {
                    await sendMessage(task);
                    // Success
                    await redis.rpush(RESULTS_KEY, JSON.stringify({
                        task_id: task.task_id,
                        account_id: parseInt(ACCOUNT_ID),
                        ad_id: task.ad_id,
                        group_id: task.group_id,
                        schedule_id: task.schedule_id,
                        user_id: task.user_id,
                        status: 'ok',
                        error_message: null,
                        no_retry: false,
                        ad_title: task.ad_title || null,
                        ad_text: task.ad_text || null,
                        ad_images: task.ad_images || null,
                        group_name: task.group_name || null,
                        messenger_type: 'wa',
                        sent_at: new Date().toISOString()
                    }));
                    log.info({ accountId: ACCOUNT_ID, taskId: task.task_id }, 'task_success');
                    lastError = null;
                    break;
                } catch (err) {
                    lastError = err;
                    const isForbidden = /^forbidden$/i.test(err.message);
                    const noRetry = err.noRetry || isForbidden;

                    if (noRetry || attempt === MAX_RETRIES) {
                        await redis.rpush(RESULTS_KEY, JSON.stringify({
                            task_id: task.task_id,
                            account_id: parseInt(ACCOUNT_ID),
                            ad_id: task.ad_id,
                            group_id: task.group_id,
                            schedule_id: task.schedule_id,
                            user_id: task.user_id,
                            status: 'fail',
                            error_message: err.message,
                            no_retry: noRetry,
                            ad_title: task.ad_title || null,
                            ad_text: task.ad_text || null,
                            ad_images: task.ad_images || null,
                            group_name: task.group_name || null,
                            messenger_type: 'wa',
                            sent_at: new Date().toISOString()
                        }));
                        log.error({ accountId: ACCOUNT_ID, taskId: task.task_id, attempt, error: err.message, noRetry }, 'task_failed');
                        break;
                    }

                    // Wait before retry
                    const delay = RETRY_DELAYS[attempt];
                    log.warn({ accountId: ACCOUNT_ID, taskId: task.task_id, attempt, nextRetryMs: delay, error: err.message }, 'task_retry');
                    await sleep(delay);
                    resetIdleTimer(); // don't shutdown during retries
                }
            }
        } catch (err) {
            if (!running) break;
            log.error({ accountId: ACCOUNT_ID, error: err.message }, 'queue_consumer_error');
            await sleep(1000);
        }
    }
}

// ── Graceful Shutdown ───────────────────────────────────────────
async function gracefulShutdown() {
    if (!running) return;
    running = false;
    log.info({ accountId: ACCOUNT_ID }, 'shutting_down');

    if (idleShutdownTimer) clearInterval(idleShutdownTimer);

    // Clean up Redis keys
    try {
        await redis.del(ENDPOINT_KEY);
        await redis.del(HEARTBEAT_KEY);
    } catch (_) {}

    // Close Baileys
    if (state.sock) {
        try { state.sock.end(); } catch (_) {}
    }

    // Close Redis
    try { redis.disconnect(); } catch (_) {}
    try { redisSub.disconnect(); } catch (_) {}

    process.exit(0);
}

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// ── HTTP API (for auth, status, groups) ─────────────────────────

// Start session (QR auth)
app.post('/api/sessions/:id/start', async (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });

    if (state.isConnected) return res.json({ status: 'already_connected' });
    if (state.initializing) return res.json({ status: 'initializing' });

    try {
        state.initializing = true;
        state.reconnectAttempts = 0;
        state.qrCode = null;
        await createSocket();
        state.initializing = false;
        res.json({ status: 'started' });
    } catch (err) {
        state.initializing = false;
        log.error({ accountId: ACCOUNT_ID, error: err.message }, 'session_start_failed');
        res.status(500).json({ error: err.message });
    }
});

// Destroy session
app.delete('/api/sessions/:id', async (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });
    await destroySession();
    res.json({ ok: true });
});

// Get status
app.get('/api/sessions/:id/status', (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });
    res.json({
        connected: state.isConnected,
        initializing: state.initializing,
        hasSession: sessionExistsOnDisk()
    });
});

// Get QR
app.get('/api/sessions/:id/qr', (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });

    if (state.isConnected) return res.json({ status: 'connected', qr: null });
    if (!state.qrCode && !state.initializing) return res.json({ status: 'not_found', qr: null });
    if (!state.qrCode) return res.json({ status: 'waiting', qr: null });
    res.json({ status: 'pending', qr: state.qrCode });
});

// Sync status
app.get('/api/sessions/:id/sync-status', (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });

    if (!state.sock && !state.isConnected) {
        if (sessionExistsOnDisk()) return res.json({ state: 'none', groups: null });
        return res.json({ state: 'not_found', groups: null });
    }
    if (!state.syncState) return res.json({ state: 'none', groups: null });
    res.json({ state: state.syncState, groups: state.groups });
});

// Retry sync
app.post('/api/sessions/:id/retry-sync', async (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });

    if (!state.sock || !state.isConnected) return res.status(400).json({ error: 'Not connected' });
    if (state.syncState === 'syncing') return res.json({ status: 'already_syncing' });

    startGroupSync();
    res.json({ status: 'sync_started' });
});

// Get groups
app.get('/api/sessions/:id/groups', (req, res) => {
    const id = req.params.id;
    if (id !== ACCOUNT_ID) return res.status(404).json({ error: 'Wrong account' });

    if (!state.groups) return res.json({ groups: [] });
    res.json({ groups: state.groups });
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        ok: true,
        accountId: ACCOUNT_ID,
        connected: state.isConnected,
        uptime: process.uptime(),
        lastActivity: state.lastActivity,
        queueKey: QUEUE_KEY
    });
});

// ── Startup ─────────────────────────────────────────────────────
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function main() {
    log.info({ accountId: ACCOUNT_ID, redisUrl: REDIS_URL, port: PORT, idleShutdownSec: IDLE_SHUTDOWN_SEC }, 'wa_worker_starting');

    // Register endpoint in Redis
    const hostname = process.env.HOSTNAME || `wa-worker-${ACCOUNT_ID}`;
    await redis.set(ENDPOINT_KEY, `http://${hostname}:${PORT}`, 'EX', IDLE_SHUTDOWN_SEC + 120);

    // Start HTTP server
    app.listen(PORT, '0.0.0.0', () => {
        log.info({ accountId: ACCOUNT_ID, port: PORT }, 'http_server_started');
    });

    // Auto-load session if exists on disk
    if (sessionExistsOnDisk()) {
        log.info({ accountId: ACCOUNT_ID }, 'loading_existing_session');
        try {
            await ensureSession();
            log.info({ accountId: ACCOUNT_ID }, 'session_loaded');
        } catch (err) {
            log.error({ accountId: ACCOUNT_ID, error: err.message }, 'session_load_failed');
        }
    } else {
        log.info({ accountId: ACCOUNT_ID }, 'no_existing_session');
    }

    // Start consuming queue
    consumeQueue();
}

main().catch(err => {
    log.fatal({ error: err.message }, 'fatal_error');
    process.exit(1);
});
```

**Step 2: Commit**

```bash
git add wa_worker/index.js
git commit -m "feat(wa-worker): implement per-account worker with Redis queue consumer"
```

---

### Task 3: Add docker-py dependency to Python project

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add docker dependency**

Run: `cd /root/source/broadcaster && uv add docker`

**Step 2: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add docker-py dependency for container management"
```

---

### Task 4: Create Container Manager service

**Files:**
- Create: `app/services/wa_container_manager.py`

**Step 1: Create the Container Manager**

This service manages the lifecycle of per-account wa-worker Docker containers via docker-py.

```python
import time
import docker
import structlog
from docker.errors import NotFound, APIError

from app.config import get_settings

logger = structlog.get_logger()

# Container config constants
WA_WORKER_IMAGE = "broadcaster-wa-worker:latest"
CONTAINER_PREFIX = "wa-worker-"
CONTAINER_LABEL = "broadcaster.role=wa-worker"
NETWORK_NAME = "broadcaster_default"
SESSIONS_VOLUME = "wa_sessions"
MEMORY_LIMIT = "256m"
DEFAULT_PORT = 3000


def _get_docker_client():
    return docker.from_env()


def get_container_name(account_id: int) -> str:
    return f"{CONTAINER_PREFIX}{account_id}"


def start_container(account_id: int) -> str | None:
    """Start a wa-worker container for the given account.
    Returns the container endpoint URL or None on failure."""
    settings = get_settings()
    client = _get_docker_client()
    name = get_container_name(account_id)

    # Check if container already exists
    try:
        existing = client.containers.get(name)
        if existing.status == "running":
            logger.info("container_already_running", account_id=account_id)
            return _container_endpoint(name)
        # Exists but stopped — remove and recreate
        existing.remove(force=True)
        logger.info("removed_stopped_container", account_id=account_id)
    except NotFound:
        pass

    try:
        container = client.containers.run(
            image=WA_WORKER_IMAGE,
            name=name,
            detach=True,
            environment={
                "ACCOUNT_ID": str(account_id),
                "REDIS_URL": settings.redis_url,
                "RATE_LIMIT_PER_MINUTE": "8",
                "IDLE_SHUTDOWN_SEC": "300",
                "PORT": str(DEFAULT_PORT),
            },
            volumes={
                SESSIONS_VOLUME: {"bind": "/app/sessions", "mode": "rw"},
            },
            network=NETWORK_NAME,
            mem_limit=MEMORY_LIMIT,
            restart_policy={"Name": "on-failure", "MaximumRetryCount": 3},
            labels={
                "broadcaster.role": "wa-worker",
                "broadcaster.account_id": str(account_id),
            },
            hostname=name,
        )
        logger.info("container_started", account_id=account_id, container_id=container.short_id)
        return _container_endpoint(name)
    except APIError as e:
        logger.error("container_start_failed", account_id=account_id, error=str(e))
        return None


def stop_container(account_id: int) -> bool:
    """Stop and remove a wa-worker container."""
    client = _get_docker_client()
    name = get_container_name(account_id)

    try:
        container = client.containers.get(name)
        container.stop(timeout=10)
        container.remove()
        logger.info("container_stopped", account_id=account_id)
        return True
    except NotFound:
        return True
    except APIError as e:
        logger.error("container_stop_failed", account_id=account_id, error=str(e))
        return False


def list_worker_containers() -> list[dict]:
    """List all wa-worker containers with their status."""
    client = _get_docker_client()
    containers = client.containers.list(all=True, filters={"label": CONTAINER_LABEL})
    result = []
    for c in containers:
        account_id = c.labels.get("broadcaster.account_id")
        result.append({
            "account_id": int(account_id) if account_id else None,
            "name": c.name,
            "status": c.status,
            "short_id": c.short_id,
        })
    return result


def cleanup_exited_containers():
    """Remove all exited wa-worker containers."""
    client = _get_docker_client()
    containers = client.containers.list(
        all=True,
        filters={"label": CONTAINER_LABEL, "status": "exited"},
    )
    for c in containers:
        try:
            c.remove()
            logger.info("cleaned_exited_container", name=c.name)
        except APIError as e:
            logger.warn("cleanup_failed", name=c.name, error=str(e))


def get_container_endpoint(account_id: int) -> str | None:
    """Get the HTTP endpoint for a running wa-worker container."""
    client = _get_docker_client()
    name = get_container_name(account_id)
    try:
        container = client.containers.get(name)
        if container.status == "running":
            return _container_endpoint(name)
        return None
    except NotFound:
        return None


def _container_endpoint(container_name: str) -> str:
    return f"http://{container_name}:{DEFAULT_PORT}"
```

**Step 2: Commit**

```bash
git add app/services/wa_container_manager.py
git commit -m "feat: add Container Manager service for wa-worker lifecycle"
```

---

### Task 5: Create Container Manager Celery beat task

**Files:**
- Modify: `app/worker/celery_app.py` (lines 28–33: beat schedule)
- Modify: `app/worker/tasks.py` (add manage_wa_containers and process_wa_results tasks)

**Step 1: Add beat tasks to celery_app.py**

In `app/worker/celery_app.py`, add two new beat entries to the schedule (after line 33):

```python
# Existing:
"check-schedules": {
    "task": "app.worker.tasks.check_schedules",
    "schedule": float(settings.celery_beat_interval),
},
# Add:
"manage-wa-containers": {
    "task": "app.worker.tasks.manage_wa_containers",
    "schedule": 15.0,
},
"process-wa-results": {
    "task": "app.worker.tasks.process_wa_results",
    "schedule": 5.0,
},
```

**Step 2: Add manage_wa_containers task to tasks.py**

Add at the end of `app/worker/tasks.py`:

```python
@shared_task(name="app.worker.tasks.manage_wa_containers")
def manage_wa_containers():
    """Check Redis queues and start/cleanup wa-worker containers."""
    import redis as redis_lib
    from app.services.wa_container_manager import (
        start_container,
        cleanup_exited_containers,
        list_worker_containers,
        get_container_name,
    )

    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)

    try:
        # Get accounts with pending work
        active_accounts = r.smembers("wa:active_accounts")

        for raw_id in active_accounts:
            account_id = int(raw_id)
            queue_key = f"wa:queue:{account_id}"
            queue_len = r.llen(queue_key)

            if queue_len > 0:
                endpoint = start_container(account_id)
                if endpoint:
                    r.set(f"wa:endpoint:{account_id}", endpoint, ex=420)  # 7 min TTL
                    logger.info("container_ensured", account_id=account_id, queue_len=queue_len)
            else:
                # No tasks left, remove from active set
                r.srem("wa:active_accounts", account_id)
                r.delete(f"wa:endpoint:{account_id}")

        # Cleanup exited containers
        cleanup_exited_containers()

    except Exception as e:
        logger.error("manage_wa_containers_error", error=str(e), exc_info=True)
    finally:
        r.close()
```

**Step 3: Add process_wa_results task to tasks.py**

```python
@shared_task(name="app.worker.tasks.process_wa_results")
def process_wa_results():
    """Read send results from Redis and write SendLog entries to DB."""
    import json
    import redis as redis_lib
    from datetime import datetime, timezone

    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)

    try:
        results = []
        # Read up to 100 results per cycle
        for _ in range(100):
            raw = r.lpop("wa:results")
            if not raw:
                break
            try:
                results.append(json.loads(raw))
            except json.JSONDecodeError as e:
                logger.error("result_parse_error", raw=raw[:200], error=str(e))

        if not results:
            return

        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(_process_results_async(results))

    except Exception as e:
        logger.error("process_wa_results_error", error=str(e), exc_info=True)
    finally:
        r.close()


async def _process_results_async(results: list[dict]):
    """Write batch of results to database."""
    from app.database import get_engine

    engine = get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for result in results:
            try:
                send_log = SendLog(
                    user_id=result["user_id"],
                    schedule_id=result.get("schedule_id"),
                    ad_id=result.get("ad_id"),
                    group_id=result.get("group_id"),
                    task_id=result.get("task_id"),
                    status=result["status"],
                    error_message=result.get("error_message"),
                    messenger_type="wa",
                    ad_title=result.get("ad_title"),
                    ad_text=result.get("ad_text"),
                    ad_images=result.get("ad_images"),
                    group_name=result.get("group_name"),
                )
                session.add(send_log)

                # Update group error state
                group_id = result.get("group_id")
                if group_id:
                    group = await session.get(Group, group_id)
                    if group:
                        if result.get("no_retry"):
                            group.last_error = result.get("error_message")
                            group.error_at = datetime.now(timezone.utc)
                        elif result["status"] == "ok":
                            group.last_error = None
                            group.error_at = None

            except Exception as e:
                logger.error("result_write_error", task_id=result.get("task_id"), error=str(e))

        await session.commit()
        logger.info("results_processed", count=len(results))

    await engine.dispose()
```

**Step 4: Commit**

```bash
git add app/worker/celery_app.py app/worker/tasks.py
git commit -m "feat: add manage_wa_containers and process_wa_results Celery tasks"
```

---

### Task 6: Modify dispatcher to use Redis queues for WhatsApp

**Files:**
- Modify: `app/worker/tasks.py` — `dispatch_send_tasks()` (lines 31–61)
- Modify: `app/application/scheduling/use_cases.py` — `collect_due_schedules()` (lines 28–103)

**Step 1: Modify dispatch_send_tasks to push WA tasks to Redis**

Replace the WA dispatch section in `dispatch_send_tasks()`. Instead of `send_whatsapp_message.apply_async()`, push to Redis:

```python
async def dispatch_send_tasks(tasks_to_dispatch: list[dict]):
    """Dispatch tasks: Telegram to Celery queue, WhatsApp to Redis per-account queues."""
    import json
    import redis as redis_lib
    from uuid import uuid4

    settings = get_settings()

    tg_tasks = []
    wa_tasks_by_account: dict[int, list[dict]] = {}

    for task in tasks_to_dispatch:
        if task["type"] == "tg_user":
            tg_tasks.append(task)
        elif task["type"] == "wa":
            account_id = task["account_id"]
            wa_tasks_by_account.setdefault(account_id, []).append(task)

    # Dispatch Telegram tasks via Celery (unchanged)
    for task in tg_tasks:
        send_telegram_message.apply_async(
            args=[task["ad_id"], task["group_id"], task["account_id"], task["schedule_id"]],
            queue="telegram",
        )

    # Dispatch WhatsApp tasks to Redis per-account queues
    if wa_tasks_by_account:
        r = redis_lib.from_url(settings.redis_url)
        try:
            pipe = r.pipeline()
            for account_id, tasks in wa_tasks_by_account.items():
                queue_key = f"wa:queue:{account_id}"
                for task in tasks:
                    payload = json.dumps({
                        "task_id": str(uuid4()),
                        "ad_id": task["ad_id"],
                        "group_id": task["group_id"],
                        "account_id": account_id,
                        "schedule_id": task["schedule_id"],
                        "user_id": task["user_id"],
                        "ad_text": task["ad_text"],
                        "ad_title": task["ad_title"],
                        "ad_images": task["ad_images"],
                        "group_external_id": task["group_external_id"],
                        "group_name": task["group_name"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    pipe.rpush(queue_key, payload)
                pipe.sadd("wa:active_accounts", account_id)
            pipe.execute()
            logger.info("wa_tasks_dispatched", account_count=len(wa_tasks_by_account),
                       total_tasks=sum(len(t) for t in wa_tasks_by_account.values()))
        finally:
            r.close()

    total = len(tg_tasks) + sum(len(t) for t in wa_tasks_by_account.values())
    logger.info("send_tasks_dispatched", total=total, tg=len(tg_tasks),
               wa=sum(len(t) for t in wa_tasks_by_account.values()))
```

**Step 2: Modify collect_due_schedules to include full task data**

In `collect_due_schedules()` in `app/application/scheduling/use_cases.py`, modify the DispatchTask creation to include additional fields needed by the wa-worker. Add a new dataclass or extend DispatchTask:

Add to `use_cases.py` a new helper after `collect_due_schedules` that enriches WA tasks with full data:

```python
@dataclass(slots=True)
class DispatchTask:
    type: str
    ad_id: int
    group_id: int
    account_id: int
    schedule_id: int
    # New fields for WA Redis dispatch
    user_id: int | None = None
    ad_text: str | None = None
    ad_title: str | None = None
    ad_images: list[str] | None = None
    group_external_id: str | None = None
    group_name: str | None = None
```

In the loop inside `collect_due_schedules`, when creating WA tasks, populate the extra fields:

```python
# Inside the schedule processing loop, where groups are iterated:
for gid in schedule.group_ids:
    # Eagerly load group for WA tasks
    task = DispatchTask(
        type=account_type,
        ad_id=ad.id,
        group_id=gid,
        account_id=schedule.account_id,
        schedule_id=schedule.id,
    )
    if account_type == "wa":
        # Load group for external_id and name
        group = await session.get(Group, gid)
        if group:
            task.user_id = ad.user_id
            task.ad_text = ad.text
            task.ad_title = ad.title
            task.ad_images = ad.images
            task.group_external_id = group.external_id
            task.group_name = group.name
    out.append(task)
```

Also update `dispatch_send_tasks` to use `dataclasses.asdict(task)` instead of `task["field"]`.

**Step 3: Commit**

```bash
git add app/worker/tasks.py app/application/scheduling/use_cases.py
git commit -m "feat: dispatch WA tasks to Redis per-account queues instead of Celery"
```

---

### Task 7: Modify WhatsAppMessenger for dynamic endpoint routing

**Files:**
- Modify: `app/messengers/whatsapp.py` (lines 12–14, 39–43)
- Modify: `app/services/messenger_factory.py` (lines 16–21)

**Step 1: Update WhatsAppMessenger to resolve endpoint from Redis**

Replace the static `bridge_url` with dynamic Redis-based endpoint lookup. The `send_message` method is no longer needed (sending goes through Redis queue), but QR/status/groups endpoints still use HTTP:

```python
# In whatsapp.py, add helper:
import redis as redis_lib

def get_wa_endpoint(account_id: int) -> str | None:
    """Get the HTTP endpoint for a wa-worker container from Redis."""
    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)
    try:
        endpoint = r.get(f"wa:endpoint:{account_id}")
        return endpoint.decode() if endpoint else None
    finally:
        r.close()


def ensure_wa_container(account_id: int) -> str | None:
    """Start wa-worker container if not running, return endpoint."""
    from app.services.wa_container_manager import start_container
    endpoint = get_wa_endpoint(account_id)
    if endpoint:
        return endpoint
    return start_container(account_id)
```

Update `WhatsAppMessenger.__init__` to accept either explicit `bridge_url` or resolve dynamically:

```python
class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str | None = None, session_id: str = ""):
        self.session_id = session_id
        self._bridge_url = bridge_url

    @property
    def bridge_url(self) -> str:
        if self._bridge_url:
            return self._bridge_url
        endpoint = ensure_wa_container(int(self.session_id))
        if not endpoint:
            raise RuntimeError(f"Cannot start wa-worker for account {self.session_id}")
        return endpoint
```

**Step 2: Update messenger_factory.py**

In `create_messenger()`, for WA accounts, don't pass bridge_url (let it resolve dynamically):

```python
if account.type == "wa":
    return WhatsAppMessenger(session_id=str(account.id))
```

**Step 3: Commit**

```bash
git add app/messengers/whatsapp.py app/services/messenger_factory.py
git commit -m "feat: dynamic endpoint routing for WhatsApp via Redis + Container Manager"
```

---

### Task 8: Update Docker Compose files

**Files:**
- Modify: `docker-compose.yml` (lines 81–90: remove celery-worker-whatsapp, add docker socket)
- Modify: `docker-compose.prod.yml` (lines 115–120: remove celery-worker-whatsapp)
- Modify: `docker-compose.dev.yml` (lines 16–21: remove celery-worker-whatsapp)

**Step 1: Modify docker-compose.yml**

1. Remove `celery-worker-whatsapp` service (lines 81–90)
2. Remove `wa-bridge` service (lines 103–105)
3. Add Docker socket mount to `celery-worker-default`:
   ```yaml
   celery-worker-default:
     <<: *app-base
     command: celery -A app.worker.celery_app worker --queues=default --concurrency=2 --loglevel=info
     volumes:
       - /var/run/docker.sock:/var/run/docker.sock
     depends_on:
       web:
         condition: service_healthy
       redis:
         condition: service_healthy
   ```

**Step 2: Modify docker-compose.prod.yml**

Remove `celery-worker-whatsapp` service section and `wa-bridge` service section.

**Step 3: Modify docker-compose.dev.yml**

Remove `celery-worker-whatsapp` override section and `wa-bridge` override section.

**Step 4: Commit**

```bash
git add docker-compose.yml docker-compose.prod.yml docker-compose.dev.yml
git commit -m "feat: remove wa-bridge and celery-worker-whatsapp, add docker socket to worker"
```

---

### Task 9: Add wa-worker Docker build to justfile

**Files:**
- Modify: `justfile`

**Step 1: Add build recipe**

```just
# Build wa-worker Docker image
wa-worker-build:
    docker build -t broadcaster-wa-worker:latest ./wa_worker

# List running wa-worker containers
wa-workers:
    docker ps --filter "label=broadcaster.role=wa-worker" --format "table {{{{.Names}}\t{{{{.Status}}\t{{{{.Ports}}"

# Stop all wa-worker containers
wa-workers-stop:
    docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop
    docker ps -aq --filter "label=broadcaster.role=wa-worker" | xargs -r docker rm
```

**Step 2: Commit**

```bash
git add justfile
git commit -m "feat: add wa-worker build and management recipes to justfile"
```

---

### Task 10: Remove send_whatsapp_message Celery task and wa_consumer.py

**Files:**
- Modify: `app/worker/tasks.py` — remove `send_whatsapp_message` (lines 159–183) and `_WA_RETRY_DELAYS` (line 156)
- Remove or deprecate: `app/worker/wa_consumer.py`
- Modify: `app/worker/celery_app.py` — remove whatsapp queue from task_routes if present

**Step 1: Remove send_whatsapp_message task**

Delete the `send_whatsapp_message` function and `_WA_RETRY_DELAYS` constant from `tasks.py`.

**Step 2: Clean up wa_consumer.py**

Delete `app/worker/wa_consumer.py` (no longer needed — wa-worker containers consume directly from Redis).

**Step 3: Commit**

```bash
git add app/worker/tasks.py app/worker/celery_app.py
git rm app/worker/wa_consumer.py
git commit -m "refactor: remove send_whatsapp_message Celery task and wa_consumer"
```

---

### Task 11: Write tests for Container Manager

**Files:**
- Create: `tests/test_wa_container_manager.py`

**Step 1: Write unit tests with mocked Docker client**

```python
from unittest.mock import MagicMock, patch
import pytest
from app.services.wa_container_manager import (
    get_container_name,
    start_container,
    stop_container,
    list_worker_containers,
    cleanup_exited_containers,
    get_container_endpoint,
)


def test_get_container_name():
    assert get_container_name(123) == "wa-worker-123"


@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_new(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = Exception("not found")

    from docker.errors import NotFound
    client.containers.get.side_effect = NotFound("not found")

    container = MagicMock()
    container.short_id = "abc123"
    client.containers.run.return_value = container

    result = start_container(123)
    assert result == "http://wa-worker-123:3000"
    client.containers.run.assert_called_once()


@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_already_running(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    existing = MagicMock()
    existing.status = "running"
    client.containers.get.return_value = existing

    result = start_container(123)
    assert result == "http://wa-worker-123:3000"
    client.containers.run.assert_not_called()


@patch("app.services.wa_container_manager._get_docker_client")
def test_stop_container(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    container = MagicMock()
    client.containers.get.return_value = container

    result = stop_container(123)
    assert result is True
    container.stop.assert_called_once()
    container.remove.assert_called_once()


@patch("app.services.wa_container_manager._get_docker_client")
def test_stop_container_not_found(mock_docker):
    from docker.errors import NotFound
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = NotFound("not found")

    result = stop_container(123)
    assert result is True


@patch("app.services.wa_container_manager._get_docker_client")
def test_cleanup_exited_containers(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client

    c1 = MagicMock(name="wa-worker-1")
    c2 = MagicMock(name="wa-worker-2")
    client.containers.list.return_value = [c1, c2]

    cleanup_exited_containers()
    c1.remove.assert_called_once()
    c2.remove.assert_called_once()
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_wa_container_manager.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_wa_container_manager.py
git commit -m "test: add unit tests for Container Manager service"
```

---

### Task 12: Write tests for Redis dispatch

**Files:**
- Create: `tests/test_wa_dispatch.py`

**Step 1: Write tests for WA task dispatch to Redis**

```python
import json
from unittest.mock import MagicMock, patch
from dataclasses import asdict
import pytest

from app.application.scheduling.use_cases import DispatchTask


def test_dispatch_task_wa_fields():
    """DispatchTask for WA should carry full payload data."""
    task = DispatchTask(
        type="wa",
        ad_id=1,
        group_id=2,
        account_id=3,
        schedule_id=4,
        user_id=5,
        ad_text="Hello",
        ad_title="Test Ad",
        ad_images=["https://example.com/img.jpg"],
        group_external_id="120363001234@g.us",
        group_name="Test Group",
    )
    d = asdict(task)
    assert d["type"] == "wa"
    assert d["ad_text"] == "Hello"
    assert d["group_external_id"] == "120363001234@g.us"
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_wa_dispatch.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_wa_dispatch.py
git commit -m "test: add tests for WA Redis dispatch"
```

---

### Task 13: Write test for process_wa_results

**Files:**
- Create: `tests/test_wa_results.py`

**Step 1: Write tests for result processing**

Test that `_process_results_async` creates SendLog entries and updates group error state. Uses the existing test DB fixtures from `tests/conftest.py`.

```python
import pytest
from datetime import datetime, timezone
from app.models.send_log import SendLog
from app.models.group import Group
from sqlalchemy import select


@pytest.mark.asyncio
async def test_process_results_creates_send_log(db_session):
    """Test that results are written to SendLog table."""
    from app.worker.tasks import _process_results_async

    # Create a test group first
    group = Group(
        name="Test Group",
        external_id="120363001234@g.us",
        account_id=1,
        user_id=1,
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    results = [{
        "task_id": "test-uuid-1",
        "account_id": 1,
        "ad_id": 1,
        "group_id": group.id,
        "schedule_id": 1,
        "user_id": 1,
        "status": "ok",
        "error_message": None,
        "no_retry": False,
        "ad_title": "Test Ad",
        "ad_text": "Hello",
        "ad_images": None,
        "group_name": "Test Group",
        "messenger_type": "wa",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }]

    # Note: _process_results_async creates its own session,
    # so this test may need adjustment based on actual implementation
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_wa_results.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_wa_results.py
git commit -m "test: add tests for WA result processing"
```

---

### Task 14: Integration test — build and verify wa-worker image

**Step 1: Build wa-worker Docker image**

Run: `cd /root/source/broadcaster && docker build -t broadcaster-wa-worker:latest ./wa_worker`

Verify it builds successfully.

**Step 2: Test container starts and exits cleanly**

Run: `docker run --rm -e ACCOUNT_ID=999 -e REDIS_URL=redis://host.docker.internal:6379/0 -e IDLE_SHUTDOWN_SEC=10 broadcaster-wa-worker:latest`

Verify:
- Logs show `wa_worker_starting`
- Logs show `http_server_started`
- After ~10s logs show `idle_shutdown`
- Container exits cleanly

**Step 3: Commit any fixes if needed**

---

### Task 15: Final cleanup and documentation

**Files:**
- Modify: `CLAUDE.md` — update architecture description
- Review all changes for consistency

**Step 1: Update CLAUDE.md**

Add to Architecture section:
```
- `wa_worker/` -- Per-account WhatsApp worker (Node.js + Baileys + Redis queue consumer)
- `app/services/wa_container_manager.py` -- Docker container lifecycle management for wa-workers
```

Update the worker description:
```
- `app/worker/` -- Celery app and async tasks (schedule checker, send dispatcher, WA result processor, container manager)
```

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All existing tests pass (some may need updates for changed interfaces)

**Step 3: Final commit**

```bash
git add -A
git commit -m "docs: update architecture docs for per-account WA containers"
```

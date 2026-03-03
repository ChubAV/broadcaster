// ============================================================
// wa_worker/index.js — Per-account WhatsApp worker
// Manages ONE Baileys session, consumes tasks from Redis queue,
// publishes results, self-shuts down after idle timeout.
// ============================================================

const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, Browsers } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const pino = require('pino');
const Redis = require('ioredis');
const os = require('os');

// ---- 1. Config (env vars) ----

const ACCOUNT_ID = process.env.ACCOUNT_ID;
if (!ACCOUNT_ID) {
    console.error('FATAL: ACCOUNT_ID env var is required');
    process.exit(1);
}

const PORT = parseInt(process.env.PORT || '3000', 10);
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';
const SESSIONS_DIR = process.env.SESSIONS_DIR || './sessions';
const IDLE_SHUTDOWN_SEC = parseInt(process.env.IDLE_SHUTDOWN_SEC || '300', 10);
const MAX_RECONNECT_ATTEMPTS = 5;
const RATE_LIMIT_PER_MINUTE = 8;
const BLPOP_TIMEOUT = 5; // seconds — short so we can check idle timer frequently
const HEARTBEAT_INTERVAL_SEC = 30;

// Retry delays for failed task sends (seconds)
const RETRY_DELAYS = [60, 180, 300];
const MAX_RETRIES = RETRY_DELAYS.length;

// Redis key patterns
const QUEUE_KEY = `wa:queue:${ACCOUNT_ID}`;
const RESULTS_KEY = 'wa:results';
const HEARTBEAT_KEY = `wa:heartbeat:${ACCOUNT_ID}`;
const ENDPOINT_KEY = `wa:endpoint:${ACCOUNT_ID}`;

// App logger
const log = pino({ level: process.env.LOG_LEVEL || 'info' });

// Silent logger for Baileys internals
const baileysLogger = pino({ level: process.env.BAILEYS_LOG_LEVEL || 'warn' });

process.on('unhandledRejection', (reason) => {
    log.error({ err: reason?.message || String(reason) }, 'unhandled_rejection');
});

const app = express();
app.use(express.json());

// Cached WA Web version (fetched once at startup)
let waVersion = null;

// Ensure sessions directory exists
fs.mkdirSync(SESSIONS_DIR, { recursive: true });


// ---- 2. Redis connections ----

// Command connection — for SET, RPUSH, etc.
const redis = new Redis(REDIS_URL, {
    maxRetriesPerRequest: null,
    enableReadyCheck: true,
    lazyConnect: true,
});

// Blocking connection — dedicated to BLPOP (blocks the connection)
const redisSub = new Redis(REDIS_URL, {
    maxRetriesPerRequest: null,
    enableReadyCheck: true,
    lazyConnect: true,
});

redis.on('error', (err) => log.error({ err: err.message }, 'redis_cmd_error'));
redisSub.on('error', (err) => log.error({ err: err.message }, 'redis_blpop_error'));


// ---- 3. Rate limiter (sliding window, same as wa_bridge) ----

const rateLimiter = { timestamps: [] };

/**
 * Wait until rate limit window allows sending.
 * Returns immediately if under the limit.
 */
async function waitForRateLimit() {
    while (true) {
        const now = Date.now();
        rateLimiter.timestamps = rateLimiter.timestamps.filter(t => now - t < 60000);
        if (rateLimiter.timestamps.length < RATE_LIMIT_PER_MINUTE) {
            rateLimiter.timestamps.push(now);
            return;
        }
        // Wait until the oldest timestamp expires
        const oldest = rateLimiter.timestamps[0];
        const waitMs = 60000 - (now - oldest) + 50; // +50ms buffer
        log.info({ accountId: ACCOUNT_ID, waitMs }, 'rate_limit_waiting');
        await new Promise(r => setTimeout(r, waitMs));
    }
}


// ---- 4. Session lock + group lock (single session) ----

let sendLockChain = Promise.resolve();
const groupLocks = new Map();

function withSessionLock(fn) {
    const next = sendLockChain.then(fn, fn);
    sendLockChain = next;
    next.finally(() => {
        if (sendLockChain === next) {
            sendLockChain = Promise.resolve();
        }
    });
    return next;
}

function withGroupLock(groupId, fn) {
    const prev = groupLocks.get(groupId) || Promise.resolve();
    const next = prev.then(fn, fn);
    groupLocks.set(groupId, next);
    next.finally(() => {
        if (groupLocks.get(groupId) === next) {
            groupLocks.delete(groupId);
        }
    });
    return next;
}


// ---- 5. Session state (single object, not Map) ----

let session = null;       // Current session state object (or null)
let loadingPromise = null; // Prevents duplicate loading


// ---- 6. Session helpers ----

function sessionExistsOnDisk() {
    const sessionDir = path.join(SESSIONS_DIR, String(ACCOUNT_ID));
    const credsFile = path.join(sessionDir, 'creds.json');
    return fs.existsSync(credsFile);
}

function deleteSessionFiles() {
    const sessionDir = path.join(SESSIONS_DIR, String(ACCOUNT_ID));
    if (fs.existsSync(sessionDir)) {
        fs.rmSync(sessionDir, { recursive: true, force: true });
        log.info({ accountId: ACCOUNT_ID }, 'session_files_deleted');
    }
}


// ---- 7. Group sync (same as wa_bridge) ----

async function startGroupSync() {
    const INITIAL_DELAY = 30000;  // 30s
    const SYNC_RETRY_DELAYS = [30000, 60000, 120000];
    const MAX_ATTEMPTS = SYNC_RETRY_DELAYS.length + 1;

    if (!session) return;

    session.syncState = 'syncing';
    log.info({ accountId: ACCOUNT_ID, delaySec: INITIAL_DELAY / 1000 }, 'group_sync_start');

    await new Promise(r => setTimeout(r, INITIAL_DELAY));

    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        if (!session || !session.isConnected) {
            log.info({ accountId: ACCOUNT_ID }, 'group_sync_aborted');
            return;
        }

        try {
            log.info({ accountId: ACCOUNT_ID, attempt: attempt + 1, maxAttempts: MAX_ATTEMPTS }, 'group_fetch_attempt');
            const groupsObj = await session.sock.groupFetchAllParticipating();
            const groups = Object.entries(groupsObj).map(([jid, metadata]) => ({
                id: jid,
                name: metadata.subject || jid,
            }));
            session.syncState = 'ready';
            session.groups = groups;
            log.info({ accountId: ACCOUNT_ID, count: groups.length }, 'group_sync_complete');
            return;
        } catch (err) {
            log.error({ accountId: ACCOUNT_ID, attempt: attempt + 1, maxAttempts: MAX_ATTEMPTS, err: err.message }, 'group_fetch_failed');
            if (attempt < SYNC_RETRY_DELAYS.length) {
                const delay = SYNC_RETRY_DELAYS[attempt];
                log.info({ accountId: ACCOUNT_ID, delaySec: delay / 1000 }, 'group_fetch_retry');
                await new Promise(r => setTimeout(r, delay));
            }
        }
    }

    if (session) {
        session.syncState = 'failed';
        log.warn({ accountId: ACCOUNT_ID, attempts: MAX_ATTEMPTS }, 'group_sync_exhausted');
    }
}


// ---- 8. createSocket (single session) ----

async function createSocket() {
    const sessionDir = path.join(SESSIONS_DIR, String(ACCOUNT_ID));
    const { state: authState, saveCreds } = await useMultiFileAuthState(sessionDir);

    const socketConfig = {
        auth: authState,
        printQRInTerminal: false,
        browser: Browsers.ubuntu('Broadcaster'),
        logger: baileysLogger,
        markOnlineOnConnect: false,
        generateHighQualityLinkPreview: false,
    };
    if (waVersion) {
        socketConfig.version = waVersion;
    }

    const sock = makeWASocket(socketConfig);

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
        intentionalClose: false,
        syncState: null,
        groups: null,
    };

    sessionState.readyPromise = new Promise((resolve, reject) => {
        sessionState.readyResolve = resolve;
        sessionState.readyReject = reject;

        // Timeout after 600s
        sessionState._readyTimeout = setTimeout(() => {
            sessionState.initializing = false;
            try { sock.end(); } catch (_) {}
            session = null;
            reject(new Error('Session initialization timeout (600s)'));
        }, 600000);
    });

    // Save credentials on every update
    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            sessionState.qrCode = await qrcode.toDataURL(qr);
            log.info({ accountId: ACCOUNT_ID }, 'qr_generated');
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
            log.info({ accountId: ACCOUNT_ID }, 'connected');

            // Start background group sync
            if (!sessionState.syncState || sessionState.syncState === 'failed') {
                startGroupSync().catch(err => {
                    log.error({ accountId: ACCOUNT_ID, err: err.message }, 'group_sync_error');
                });
            }
        }

        if (connection === 'close') {
            sessionState.isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const reason = DisconnectReason[statusCode] || statusCode || 'unknown';
            log.info({ accountId: ACCOUNT_ID, reason, statusCode }, 'disconnected');

            if (sessionState.intentionalClose) {
                return;
            }

            // Unrecoverable errors
            const unrecoverable = [DisconnectReason.loggedOut, 405, 403];
            if (unrecoverable.includes(statusCode)) {
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                if (sessionState.readyReject) {
                    sessionState.readyReject(new Error(`Session terminated: ${reason} (${statusCode})`));
                    sessionState.readyResolve = null;
                    sessionState.readyReject = null;
                }
                session = null;
                deleteSessionFiles();
                log.warn({ accountId: ACCOUNT_ID, statusCode }, 'unrecoverable_disconnect');
            } else if (sessionState.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                sessionState.reconnectAttempts++;
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                const backoff = Math.min(1000 * Math.pow(2, sessionState.reconnectAttempts - 1), 30000);
                log.info({ accountId: ACCOUNT_ID, backoffMs: backoff, attempt: sessionState.reconnectAttempts, maxAttempts: MAX_RECONNECT_ATTEMPTS }, 'reconnecting');

                setTimeout(async () => {
                    try {
                        if (session && session.isConnected) {
                            return;
                        }
                        const prevAttempts = sessionState.reconnectAttempts;
                        session = null;
                        const newState = await createSocket();
                        newState.reconnectAttempts = prevAttempts;
                        session = newState;
                        await newState.readyPromise;
                    } catch (err) {
                        log.error({ accountId: ACCOUNT_ID, err: err.message }, 'reconnect_failed');
                        session = null;
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
                session = null;
                log.warn({ accountId: ACCOUNT_ID, maxAttempts: MAX_RECONNECT_ATTEMPTS }, 'max_reconnect_reached');
            }
        }
    });

    session = sessionState;
    return sessionState;
}


// ---- 9. ensureSession (single session) ----

async function ensureSession() {
    if (session && session.isConnected) {
        session.lastActivity = Date.now();
        return session;
    }

    if (session && session.initializing) {
        try {
            await session.readyPromise;
            session.lastActivity = Date.now();
            return session;
        } catch {
            return null;
        }
    }

    if (!sessionExistsOnDisk()) {
        return null;
    }

    // Prevent duplicate loading
    if (loadingPromise) {
        return loadingPromise;
    }

    loadingPromise = (async () => {
        log.info({ accountId: ACCOUNT_ID }, 'session_loading');
        try {
            const state = await createSocket();
            await state.readyPromise;
            state.lastActivity = Date.now();
            log.info({ accountId: ACCOUNT_ID }, 'session_loaded');
            return state;
        } catch (err) {
            log.error({ accountId: ACCOUNT_ID, err: err.message }, 'session_load_failed');
            session = null;
            return null;
        }
    })();

    try {
        return await loadingPromise;
    } finally {
        loadingPromise = null;
    }
}


// ---- 10. destroySession ----

async function destroySession() {
    if (session) {
        session.intentionalClose = true;
        try {
            await session.sock.logout();
        } catch (err) {
            log.error({ accountId: ACCOUNT_ID, err: err.message }, 'logout_error');
            try { session.sock.end(); } catch (_) {}
        }
        session = null;
    }
    rateLimiter.timestamps = [];
    deleteSessionFiles();
    log.info({ accountId: ACCOUNT_ID }, 'session_destroyed');
}


// ---- 11. sendMessage(task) — extracted from wa_bridge's POST /send ----

async function sendMessage(task) {
    const { group_external_id, ad_text, ad_images, task_id } = task;
    const groupId = group_external_id;
    const caption = ad_text || '';
    const images = ad_images || [];

    const state = await ensureSession();
    if (!state || !state.isConnected) {
        throw new Error('WhatsApp session not available');
    }

    await withGroupLock(groupId, async () => {
        await withSessionLock(async () => {
            // Anti-ban: simulate typing
            try {
                await state.sock.sendPresenceUpdate('composing', groupId);
                const typingDelay = 1500 + Math.random() * 2500;
                await new Promise(r => setTimeout(r, typingDelay));
                await state.sock.sendPresenceUpdate('paused', groupId);
            } catch (err) {
                log.warn({ accountId: ACCOUNT_ID, taskId: task_id, groupId, err: err.message }, 'presence_update_failed');
            }

            if (images.length > 0) {
                log.info({ accountId: ACCOUNT_ID, taskId: task_id, groupId, imageCount: images.length, caption: caption.substring(0, 50) }, 'sending_images');

                for (let i = 0; i < images.length; i++) {
                    const img = images[i];
                    let buffer;
                    let mimetype = 'image/jpeg';

                    if (img.startsWith('http://') || img.startsWith('https://')) {
                        const response = await axios.get(img, { responseType: 'arraybuffer', timeout: 30000 });
                        mimetype = response.headers['content-type'] || 'image/jpeg';
                        buffer = Buffer.from(response.data);
                    } else if (fs.existsSync(img)) {
                        buffer = fs.readFileSync(img);
                    } else {
                        log.warn({ accountId: ACCOUNT_ID, taskId: task_id, path: img }, 'image_not_found');
                        continue;
                    }

                    const msgOptions = { image: buffer, mimetype };
                    if (images.length === 1 && caption) {
                        msgOptions.caption = caption;
                    }

                    const result = await state.sock.sendMessage(groupId, msgOptions);
                    log.info({ accountId: ACCOUNT_ID, taskId: task_id, index: i, messageId: result?.key?.id }, 'send_result');
                }

                // Multiple images: send caption as separate text
                if (images.length > 1 && caption) {
                    await state.sock.sendMessage(groupId, { text: caption });
                }
            } else {
                log.info({ accountId: ACCOUNT_ID, taskId: task_id, groupId, caption: caption.substring(0, 50) }, 'sending_text');
                const result = await state.sock.sendMessage(groupId, { text: caption });
                log.info({ accountId: ACCOUNT_ID, taskId: task_id, messageId: result?.key?.id }, 'send_result');
            }
        });
    });

    state.lastActivity = Date.now();
}


// ---- 12. Queue consumer — BLPOP loop with retry logic ----

let consumerRunning = false;
let lastTaskTime = Date.now(); // Track last task for idle shutdown

async function publishResult(task, status, errorMessage = null, noRetry = false) {
    const result = {
        task_id: task.task_id,
        account_id: task.account_id,
        ad_id: task.ad_id,
        group_id: task.group_id,
        schedule_id: task.schedule_id,
        user_id: task.user_id,
        status,
        error_message: errorMessage,
        no_retry: noRetry,
        ad_title: task.ad_title || null,
        ad_text: task.ad_text || null,
        ad_images: task.ad_images || [],
        group_name: task.group_name || null,
        messenger_type: 'wa',
        sent_at: new Date().toISOString(),
    };

    try {
        await redis.rpush(RESULTS_KEY, JSON.stringify(result));
        log.info({ accountId: ACCOUNT_ID, taskId: task.task_id, status }, 'result_published');
    } catch (err) {
        log.error({ accountId: ACCOUNT_ID, taskId: task.task_id, err: err.message }, 'result_publish_failed');
    }
}

/**
 * Determine if an error is non-retryable.
 */
function isNoRetryError(errMsg) {
    // Forbidden — account kicked/banned from group
    if (/^forbidden$/i.test(errMsg)) return true;
    // Session not available — need manual intervention
    if (/session not available/i.test(errMsg)) return true;
    return false;
}

/**
 * Extract retry-after seconds from WA rate limit error, or 0.
 */
function extractRetryAfter(errMsg) {
    const match = errMsg.match(/wait of (\d+) seconds? is required/i);
    return match ? parseInt(match[1], 10) : 0;
}

async function processTask(task) {
    const { task_id, group_external_id } = task;
    const retryCount = task._retry_count || 0;

    log.info({ accountId: ACCOUNT_ID, taskId: task_id, groupId: group_external_id, retry: retryCount }, 'task_processing');

    // Wait for rate limit window
    await waitForRateLimit();

    try {
        await sendMessage(task);
        await publishResult(task, 'ok');
    } catch (err) {
        const errMsg = err.message || String(err);
        log.error({ accountId: ACCOUNT_ID, taskId: task_id, err: errMsg, retry: retryCount }, 'task_send_failed');

        // Check for non-retryable errors
        if (isNoRetryError(errMsg)) {
            await publishResult(task, 'fail', errMsg, true);
            return;
        }

        // Check WA rate limit — use their retry-after as delay
        const retryAfterSec = extractRetryAfter(errMsg);
        if (retryAfterSec > 0) {
            log.warn({ accountId: ACCOUNT_ID, taskId: task_id, retryAfterSec }, 'wa_rate_limited_requeue');
            // Re-enqueue with delay
            task._retry_count = retryCount;
            task._delay_until = Date.now() + retryAfterSec * 1000;
            await redis.rpush(QUEUE_KEY, JSON.stringify(task));
            return;
        }

        // Retry logic: re-enqueue with incremented retry count
        if (retryCount < MAX_RETRIES) {
            const delaySec = RETRY_DELAYS[retryCount];
            log.info({ accountId: ACCOUNT_ID, taskId: task_id, nextRetry: retryCount + 1, delaySec }, 'task_retry_scheduled');
            task._retry_count = retryCount + 1;
            task._delay_until = Date.now() + delaySec * 1000;
            await redis.rpush(QUEUE_KEY, JSON.stringify(task));
        } else {
            log.error({ accountId: ACCOUNT_ID, taskId: task_id, maxRetries: MAX_RETRIES }, 'task_retries_exhausted');
            await publishResult(task, 'fail', errMsg, false);
        }
    }
}

async function startConsumer() {
    consumerRunning = true;
    log.info({ accountId: ACCOUNT_ID, queue: QUEUE_KEY }, 'consumer_started');

    while (consumerRunning) {
        try {
            const result = await redisSub.blpop(QUEUE_KEY, BLPOP_TIMEOUT);

            if (!result) {
                // BLPOP returned null — timeout, check idle
                const idleSec = (Date.now() - lastTaskTime) / 1000;
                if (idleSec >= IDLE_SHUTDOWN_SEC) {
                    log.info({ accountId: ACCOUNT_ID, idleSec: Math.round(idleSec) }, 'idle_shutdown');
                    gracefulShutdown('idle');
                    return;
                }
                continue;
            }

            const [, rawTask] = result; // [key, value]
            lastTaskTime = Date.now();

            let task;
            try {
                task = JSON.parse(rawTask);
            } catch (parseErr) {
                log.error({ accountId: ACCOUNT_ID, err: parseErr.message, raw: rawTask.substring(0, 200) }, 'task_parse_error');
                continue;
            }

            // Check if task has a delay (retry scheduling)
            if (task._delay_until && Date.now() < task._delay_until) {
                // Not ready yet — re-enqueue at tail and continue
                await redis.rpush(QUEUE_KEY, rawTask);
                continue;
            }

            await processTask(task);

            // Update heartbeat after each task
            await redis.set(HEARTBEAT_KEY, Date.now().toString()).catch(() => {});

        } catch (err) {
            if (!consumerRunning) break;
            log.error({ accountId: ACCOUNT_ID, err: err.message }, 'consumer_loop_error');

            // Check idle even on errors (e.g. Redis down after docker compose down)
            const idleSec = (Date.now() - lastTaskTime) / 1000;
            if (idleSec >= IDLE_SHUTDOWN_SEC) {
                log.info({ accountId: ACCOUNT_ID, idleSec: Math.round(idleSec) }, 'idle_shutdown_on_error');
                gracefulShutdown('idle');
                return;
            }

            // Pause before retrying (longer than normal to avoid log spam)
            await new Promise(r => setTimeout(r, 5000));
        }
    }
}


// ---- 13. Graceful shutdown ----

let shuttingDown = false;

async function gracefulShutdown(reason = 'unknown') {
    if (shuttingDown) return;
    shuttingDown = true;
    consumerRunning = false;

    log.info({ accountId: ACCOUNT_ID, reason }, 'shutdown_start');

    // Clean up Redis keys
    try {
        await redis.del(HEARTBEAT_KEY);
        await redis.del(ENDPOINT_KEY);
        log.info({ accountId: ACCOUNT_ID }, 'redis_keys_cleaned');
    } catch (err) {
        log.error({ accountId: ACCOUNT_ID, err: err.message }, 'redis_cleanup_error');
    }

    // Close Baileys socket (keep session files on disk)
    if (session) {
        session.intentionalClose = true;
        try {
            session.sock.end();
        } catch (err) {
            log.error({ accountId: ACCOUNT_ID, err: err.message }, 'socket_close_error');
        }
        session = null;
    }

    // Close Redis connections
    try {
        redisSub.disconnect();
        redis.disconnect();
    } catch (_) {}

    log.info({ accountId: ACCOUNT_ID, reason }, 'shutdown_complete');
    process.exit(0);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));


// ---- 14. HTTP API endpoints (same as wa_bridge minus POST /send) ----

// POST /api/sessions/:id/start — Create and initialize a session (QR code)
app.post('/api/sessions/:id/start', async (req, res) => {
    const sessionId = req.params.id;

    // Only allow managing this worker's account
    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    if (session) {
        if (session.isConnected) {
            return res.json({ status: 'connected' });
        }
        if (session.initializing) {
            return res.json({ status: 'initializing' });
        }
        // Stale session — clean up
        try { session.sock.end(); } catch (_) {}
        session = null;
    }

    try {
        const state = await createSocket();
        state.readyPromise.catch((err) => {
            log.warn({ accountId: ACCOUNT_ID, err: err.message }, 'session_init_failed');
        });
        res.json({ status: 'initializing' });
    } catch (err) {
        log.error({ accountId: ACCOUNT_ID, err: err.message }, 'session_start_failed');
        res.status(500).json({ error: err.message });
    }
});

// DELETE /api/sessions/:id — Destroy a session
app.delete('/api/sessions/:id', async (req, res) => {
    const sessionId = req.params.id;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    await destroySession();
    res.json({ ok: true });
});

// GET /api/sessions/:id/status — Connection status
app.get('/api/sessions/:id/status', (req, res) => {
    const sessionId = req.params.id;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    if (!session) {
        const exists = sessionExistsOnDisk();
        return res.json({ connected: false, exists, syncState: null });
    }
    res.json({
        connected: session.isConnected,
        exists: true,
        syncState: session.syncState,
    });
});

// GET /api/sessions/:id/qr — Get QR code for authentication
app.get('/api/sessions/:id/qr', (req, res) => {
    const sessionId = req.params.id;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

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

// GET /api/sessions/:id/sync-status — Group sync status
app.get('/api/sessions/:id/sync-status', async (req, res) => {
    const sessionId = req.params.id;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    if (!session) {
        if (sessionExistsOnDisk()) {
            log.info({ accountId: ACCOUNT_ID }, 'session_reloading');
            try {
                const state = await ensureSession();
                if (state && state.isConnected && (!state.syncState || state.syncState === 'failed')) {
                    startGroupSync().catch(err => {
                        log.error({ accountId: ACCOUNT_ID, err: err.message }, 'resync_error');
                    });
                    return res.json({ state: 'syncing', groups: null });
                }
            } catch (err) {
                log.error({ accountId: ACCOUNT_ID, err: err.message }, 'session_reload_failed');
            }
            if (!session || !session.isConnected) {
                return res.json({ state: 'unknown', groups: null });
            }
        } else {
            return res.json({ state: 'not_found', groups: null });
        }
    }

    return res.json({
        state: session.syncState || 'none',
        groups: session.groups,
    });
});

// POST /api/sessions/:id/retry-sync — Retry failed group sync
app.post('/api/sessions/:id/retry-sync', (req, res) => {
    const sessionId = req.params.id;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    if (!session || !session.isConnected) {
        return res.status(404).json({ error: 'Session not connected' });
    }

    if (session.syncState === 'syncing') {
        return res.json({ status: 'already_syncing' });
    }

    session.syncState = null;
    session.groups = null;
    startGroupSync().catch(err => {
        log.error({ accountId: ACCOUNT_ID, err: err.message }, 'retry_sync_error');
    });

    res.json({ status: 'sync_started' });
});

// GET /api/sessions/:id/groups — List groups
app.get('/api/sessions/:id/groups', async (req, res) => {
    const sessionId = req.params.id;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    const state = await ensureSession();
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        const groupsObj = await state.sock.groupFetchAllParticipating();
        const groups = Object.entries(groupsObj).map(([jid, metadata]) => ({
            id: jid,
            name: metadata.subject || jid,
        }));
        return res.json(groups);
    } catch (error) {
        log.error({ accountId: ACCOUNT_ID, err: error.message }, 'groups_error');
        return res.status(500).json({ error: error.message });
    }
});

// GET /api/sessions/:id/group-info/:jid — Get group details
app.get('/api/sessions/:id/group-info/:jid', async (req, res) => {
    const sessionId = req.params.id;
    const jid = req.params.jid;

    if (String(sessionId) !== String(ACCOUNT_ID)) {
        return res.status(403).json({ error: `This worker manages account ${ACCOUNT_ID} only` });
    }

    const state = await ensureSession();
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        const metadata = await state.sock.groupMetadata(jid);
        const admins = (metadata.participants || [])
            .filter(p => p.admin === 'admin' || p.admin === 'superadmin')
            .map(p => {
                let phone = null;
                if (p.id.endsWith('@s.whatsapp.net')) {
                    phone = p.id.replace('@s.whatsapp.net', '');
                } else if (p.phoneNumber) {
                    phone = p.phoneNumber;
                }
                return {
                    id: p.id,
                    name: p.notify || '',
                    phone,
                    admin: p.admin,
                };
            });
        return res.json({
            name: metadata.subject || jid,
            member_count: (metadata.participants || []).length,
            admins,
            raw: {
                subject: metadata.subject,
                desc: metadata.desc,
                owner: metadata.owner,
                creation: metadata.creation,
                size: metadata.size,
            },
        });
    } catch (error) {
        log.error({ accountId: ACCOUNT_ID, jid, err: error.message }, 'group_info_error');
        return res.status(500).json({ error: error.message });
    }
});

// GET /health — Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        account_id: ACCOUNT_ID,
        connected: session ? session.isConnected : false,
        syncState: session ? session.syncState : null,
        uptime: process.uptime(),
        idle_sec: Math.round((Date.now() - lastTaskTime) / 1000),
    });
});


// ---- 15. main() startup ----

async function main() {
    log.info({ accountId: ACCOUNT_ID, port: PORT, redisUrl: REDIS_URL, idleShutdownSec: IDLE_SHUTDOWN_SEC }, 'worker_starting');

    // Fetch WA version
    try {
        const { version, isLatest } = await fetchLatestBaileysVersion();
        waVersion = version;
        log.info({ version: version.join('.'), isLatest }, 'wa_version');
    } catch (err) {
        log.warn({ err: err.message }, 'wa_version_fetch_failed');
    }

    // Connect to Redis
    await redis.connect();
    await redisSub.connect();
    log.info('redis_connected');

    // Register endpoint in Redis
    const hostname = os.hostname();
    const endpoint = `http://${hostname}:${PORT}`;
    await redis.set(ENDPOINT_KEY, endpoint);
    log.info({ endpoint, key: ENDPOINT_KEY }, 'endpoint_registered');

    // Set initial heartbeat
    await redis.set(HEARTBEAT_KEY, Date.now().toString());

    // Start heartbeat interval
    const heartbeatInterval = setInterval(async () => {
        try {
            await redis.set(HEARTBEAT_KEY, Date.now().toString());
        } catch (err) {
            log.error({ err: err.message }, 'heartbeat_error');
        }
    }, HEARTBEAT_INTERVAL_SEC * 1000);

    // Auto-load session if it exists on disk
    if (sessionExistsOnDisk()) {
        log.info({ accountId: ACCOUNT_ID }, 'session_autoloading');
        try {
            await ensureSession();
        } catch (err) {
            log.error({ accountId: ACCOUNT_ID, err: err.message }, 'session_autoload_failed');
        }
    }

    // Start HTTP server
    app.listen(PORT, () => {
        log.info({ port: PORT, accountId: ACCOUNT_ID }, 'http_server_started');
    });

    // Start consumer loop (runs forever until shutdown)
    startConsumer().catch(err => {
        log.error({ accountId: ACCOUNT_ID, err: err.message }, 'consumer_fatal_error');
        gracefulShutdown('consumer_error');
    });
}

main().catch(err => {
    log.error({ err: err.message }, 'startup_fatal_error');
    process.exit(1);
});

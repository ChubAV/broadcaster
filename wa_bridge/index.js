const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, Browsers } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

// App logger — structured JSON to stdout
const log = pino({ level: process.env.LOG_LEVEL || 'info' });

// Silent logger for Baileys internals
const baileysLogger = pino({ level: process.env.BAILEYS_LOG_LEVEL || 'warn' });

process.on('unhandledRejection', (reason) => {
    log.error({ err: reason?.message || String(reason) }, 'unhandled_rejection');
});

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const IDLE_TIMEOUT_MS = parseInt(process.env.IDLE_TIMEOUT_MS || '300000');
const SESSIONS_DIR = process.env.SESSIONS_DIR || './sessions';
const MAX_RECONNECT_ATTEMPTS = 5;
const RATE_LIMIT_PER_MINUTE = 8;

// Cached WA Web version (fetched once at startup)
let waVersion = null;

// In-memory session state
const sessions = new Map();
const loadingPromises = new Map();
const sendLocks = new Map();
const groupLocks = new Map();

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
 * Serialize sends per group so messages from different sessions
 * don't interleave in the same chat.
 */
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
        log.info({ sessionId }, 'session_files_deleted');
    }
}

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
    log.info({ sessionId, delaySec: INITIAL_DELAY / 1000 }, 'group_sync_start');

    await new Promise(r => setTimeout(r, INITIAL_DELAY));

    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        const currentState = sessions.get(sessionId);
        if (!currentState || !currentState.isConnected) {
            log.info({ sessionId }, 'group_sync_aborted');
            return;
        }

        try {
            log.info({ sessionId, attempt: attempt + 1, maxAttempts: MAX_ATTEMPTS }, 'group_fetch_attempt');
            const groupsObj = await currentState.sock.groupFetchAllParticipating();
            const groups = Object.entries(groupsObj).map(([jid, metadata]) => ({
                id: jid,
                name: metadata.subject || jid,
            }));
            currentState.syncState = 'ready';
            currentState.groups = groups;
            log.info({ sessionId, count: groups.length }, 'group_sync_complete');
            return;
        } catch (err) {
            log.error({ sessionId, attempt: attempt + 1, maxAttempts: MAX_ATTEMPTS, err: err.message }, 'group_fetch_failed');
            if (attempt < RETRY_DELAYS.length) {
                const delay = RETRY_DELAYS[attempt];
                log.info({ sessionId, delaySec: delay / 1000 }, 'group_fetch_retry');
                await new Promise(r => setTimeout(r, delay));
            }
        }
    }

    // All attempts failed
    const finalState = sessions.get(sessionId);
    if (finalState) {
        finalState.syncState = 'failed';
        log.warn({ sessionId, attempts: MAX_ATTEMPTS }, 'group_sync_exhausted');
    }
}

/**
 * Create a Baileys socket for the given sessionId.
 * Returns the state object stored in sessions Map.
 */
async function createSocket(sessionId) {
    const sessionDir = path.join(SESSIONS_DIR, String(sessionId));
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
        syncState: null,    // null | 'syncing' | 'ready' | 'failed'
        groups: null,       // Array of {id, name} when synced
    };

    sessionState.readyPromise = new Promise((resolve, reject) => {
        sessionState.readyResolve = resolve;
        sessionState.readyReject = reject;

        // Timeout after 600s — clean up socket to stop QR generation
        sessionState._readyTimeout = setTimeout(() => {
            sessionState.initializing = false;
            try { sock.end(); } catch (_) {}
            sessions.delete(sessionId);
            reject(new Error('Session initialization timeout (600s)'));
        }, 600000);
    });

    // Save credentials on every update
    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            sessionState.qrCode = await qrcode.toDataURL(qr);
            log.info({ sessionId }, 'qr_generated');
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
            log.info({ sessionId }, 'connected');

            // Start background group sync (don't await — runs in background)
            if (!sessionState.syncState || sessionState.syncState === 'failed') {
                startGroupSync(sessionId).catch(err => {
                    log.error({ sessionId, err: err.message }, 'group_sync_error');
                });
            }
        }

        if (connection === 'close') {
            sessionState.isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const reason = DisconnectReason[statusCode] || statusCode || 'unknown';
            log.info({ sessionId, reason, statusCode }, 'disconnected');

            // Intentional close (idle unload, destroy) — do not reconnect
            if (sessionState.intentionalClose) {
                return;
            }

            // Unrecoverable errors: loggedOut (401), 405, 403 — clean up and require fresh QR
            const unrecoverable = [DisconnectReason.loggedOut, 405, 403];
            if (unrecoverable.includes(statusCode)) {
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                if (sessionState.readyReject) {
                    sessionState.readyReject(new Error(`Session terminated: ${reason} (${statusCode})`));
                    sessionState.readyResolve = null;
                    sessionState.readyReject = null;
                }
                sessions.delete(sessionId);
                deleteSessionFiles(sessionId);
                log.warn({ sessionId, statusCode }, 'unrecoverable_disconnect');
            } else if (sessionState.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                // Auto-reconnect with exponential backoff
                sessionState.reconnectAttempts++;
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                const backoff = Math.min(1000 * Math.pow(2, sessionState.reconnectAttempts - 1), 30000);
                log.info({ sessionId, backoffMs: backoff, attempt: sessionState.reconnectAttempts, maxAttempts: MAX_RECONNECT_ATTEMPTS }, 'reconnecting');

                setTimeout(async () => {
                    try {
                        // If someone else already reconnected, skip
                        const current = sessions.get(sessionId);
                        if (current && current.isConnected) {
                            return;
                        }
                        sessions.delete(sessionId);
                        const newState = await createSocket(sessionId);
                        newState.reconnectAttempts = sessionState.reconnectAttempts;
                        sessions.set(sessionId, newState);
                        await newState.readyPromise;
                    } catch (err) {
                        log.error({ sessionId, err: err.message }, 'reconnect_failed');
                        sessions.delete(sessionId);
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
                log.warn({ sessionId, maxAttempts: MAX_RECONNECT_ATTEMPTS }, 'max_reconnect_reached');
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
        log.info({ sessionId }, 'session_loading');
        try {
            const state = await createSocket(sessionId);
            await state.readyPromise;
            state.lastActivity = Date.now();
            log.info({ sessionId }, 'session_loaded');
            return state;
        } catch (err) {
            log.error({ sessionId, err: err.message }, 'session_load_failed');
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

    state.intentionalClose = true;
    try {
        state.sock.end();
    } catch (err) {
        log.error({ sessionId, err: err.message }, 'socket_close_error');
    }
    rateLimiters.delete(sessionId);
    sessions.delete(sessionId);
    log.info({ sessionId }, 'session_unloaded');
}

/**
 * Destroy a session completely (logout + delete files).
 */
async function destroySession(sessionId) {
    const state = sessions.get(sessionId);
    if (state) {
        state.intentionalClose = true;
        try {
            await state.sock.logout();
        } catch (err) {
            log.error({ sessionId, err: err.message }, 'logout_error');
            try { state.sock.end(); } catch (_) {}
        }
        sessions.delete(sessionId);
    }
    rateLimiters.delete(sessionId);
    deleteSessionFiles(sessionId);
    log.info({ sessionId }, 'session_destroyed');
}

// ---- Idle timeout: unload sessions after inactivity ----

setInterval(() => {
    const now = Date.now();
    for (const [id, state] of sessions) {
        if (state.syncState === 'syncing') {
            continue; // Don't unload sessions that are syncing
        }
        if (state.isConnected && (now - state.lastActivity > IDLE_TIMEOUT_MS)) {
            log.info({ sessionId: id, idleTimeoutSec: Math.round(IDLE_TIMEOUT_MS / 1000) }, 'idle_unload');
            unloadSession(id);
        }
    }
}, 60000);

// ---- REST API endpoints ----

// POST /api/sessions/:id/start - Create and initialize a session (QR code)
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
        const state = await createSocket(sessionId);
        // Don't await readyPromise (caller polls for QR/status), but catch rejection
        state.readyPromise.catch((err) => {
            log.warn({ sessionId, err: err.message }, 'session_init_failed');
        });
        res.json({ status: 'initializing' });
    } catch (err) {
        log.error({ sessionId, err: err.message }, 'session_start_failed');
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
        const exists = sessionExistsOnDisk(sessionId);
        return res.json({ connected: false, exists, syncState: null });
    }
    res.json({
        connected: state.isConnected,
        exists: true,
        syncState: state.syncState,
    });
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

// GET /api/sessions/:id/sync-status - Group sync status
app.get('/api/sessions/:id/sync-status', async (req, res) => {
    const sessionId = req.params.id;
    let state = sessions.get(sessionId);

    if (!state) {
        if (sessionExistsOnDisk(sessionId)) {
            // Session was unloaded (idle timeout) — reload and re-sync
            log.info({ sessionId }, 'session_reloading');
            try {
                state = await ensureSession(sessionId);
                if (state && state.isConnected && (!state.syncState || state.syncState === 'failed')) {
                    startGroupSync(sessionId).catch(err => {
                        log.error({ sessionId, err: err.message }, 'resync_error');
                    });
                    return res.json({ state: 'syncing', groups: null });
                }
            } catch (err) {
                log.error({ sessionId, err: err.message }, 'session_reload_failed');
            }
            // If reload failed or not connected
            if (!state || !state.isConnected) {
                return res.json({ state: 'unknown', groups: null });
            }
        } else {
            return res.json({ state: 'not_found', groups: null });
        }
    }

    return res.json({
        state: state.syncState || 'none',
        groups: state.groups,
    });
});

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
        log.error({ sessionId, err: err.message }, 'retry_sync_error');
    });

    res.json({ status: 'sync_started' });
});

// POST /api/sessions/:id/send - Send message (auto-loads session if needed)
app.post('/api/sessions/:id/send', async (req, res) => {
    const sessionId = req.params.id;
    const { group_id, text, image_paths, image_urls, trace_id } = req.body;
    const images = image_urls || image_paths || [];
    const caption = text || '';
    const taskId = trace_id || null;

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
        // Group lock prevents interleaving when multiple sessions send to the same chat
        await withGroupLock(group_id, async () => {
            await withSessionLock(sessionId, async () => {
                // Anti-ban: simulate typing
                try {
                    await state.sock.sendPresenceUpdate('composing', group_id);
                    const typingDelay = 1500 + Math.random() * 2500;
                    await new Promise(r => setTimeout(r, typingDelay));
                    await state.sock.sendPresenceUpdate('paused', group_id);
                } catch (err) {
                    // Presence update failure is non-critical
                    log.warn({ sessionId, taskId, groupId: group_id, err: err.message }, 'presence_update_failed');
                }

                if (images.length > 0) {
                    log.info({ sessionId, taskId, groupId: group_id, imageCount: images.length, caption: caption.substring(0, 50) }, 'sending_images');

                    // Download and send images
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
                            log.warn({ sessionId, taskId, path: img }, 'image_not_found');
                            continue;
                        }

                        const msgOptions = { image: buffer, mimetype };
                        // Single image: attach caption directly
                        if (images.length === 1 && caption) {
                            msgOptions.caption = caption;
                        }

                        const result = await state.sock.sendMessage(group_id, msgOptions);
                        log.info({ sessionId, taskId, index: i, messageId: result?.key?.id }, 'send_result');
                    }

                    // Multiple images: send caption as separate text
                    if (images.length > 1 && caption) {
                        await state.sock.sendMessage(group_id, { text: caption });
                    }
                } else {
                    log.info({ sessionId, taskId, groupId: group_id, caption: caption.substring(0, 50) }, 'sending_text');
                    const result = await state.sock.sendMessage(group_id, { text: caption });
                    log.info({ sessionId, taskId, messageId: result?.key?.id }, 'send_result');
                }
            });
        });

        state.lastActivity = Date.now();
        return res.json({ ok: true, trace_id: taskId });
    } catch (error) {
        const errMsg = error.message || String(error);

        // Detect WhatsApp rate-limit error (per-chat cooldown)
        const rateLimitMatch = errMsg.match(/wait of (\d+) seconds? is required/i);
        if (rateLimitMatch) {
            const retryAfter = parseInt(rateLimitMatch[1], 10);
            log.warn({ sessionId, taskId, groupId: group_id, retryAfter }, 'wa_rate_limited');
            return res.status(429).json({ error: errMsg, retry_after: retryAfter, trace_id: taskId });
        }

        // Detect "forbidden" — account kicked/banned from group, no point retrying
        if (/^forbidden$/i.test(errMsg)) {
            log.warn({ sessionId, taskId, groupId: group_id }, 'wa_forbidden');
            return res.status(403).json({ error: errMsg, trace_id: taskId });
        }

        log.error({ sessionId, taskId, groupId: group_id, err: errMsg }, 'send_error');
        return res.status(500).json({ error: errMsg, trace_id: taskId });
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
            name: metadata.subject || jid,
        }));
        return res.json(groups);
    } catch (error) {
        log.error({ sessionId, err: error.message }, 'groups_error');
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

(async () => {
    try {
        const { version, isLatest } = await fetchLatestBaileysVersion();
        waVersion = version;
        log.info({ version: version.join('.'), isLatest }, 'wa_version');
    } catch (err) {
        log.warn({ err: err.message }, 'wa_version_fetch_failed');
    }

    app.listen(PORT, () => {
        log.info({ port: PORT, idleTimeoutSec: IDLE_TIMEOUT_MS / 1000 }, 'server_started');
    });
})();

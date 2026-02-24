const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, Browsers } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

process.on('unhandledRejection', (reason) => {
    console.error('[process] Unhandled rejection:', reason?.message || reason);
});

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const IDLE_TIMEOUT_MS = parseInt(process.env.IDLE_TIMEOUT_MS || '300000');
const SESSIONS_DIR = process.env.SESSIONS_DIR || './sessions';
const MAX_RECONNECT_ATTEMPTS = 5;
const RATE_LIMIT_PER_MINUTE = 8;

// Silent logger for Baileys (it uses pino internally)
const logger = pino({ level: process.env.BAILEYS_LOG_LEVEL || 'warn' });

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
        console.log(`[${sessionId}] Session files deleted`);
    }
}

/**
 * Create a Baileys socket for the given sessionId.
 * Returns the state object stored in sessions Map.
 */
async function createSocket(sessionId, phoneNumber) {
    const sessionDir = path.join(SESSIONS_DIR, String(sessionId));
    const { state: authState, saveCreds } = await useMultiFileAuthState(sessionDir);

    const socketConfig = {
        auth: authState,
        printQRInTerminal: false,
        browser: Browsers.ubuntu('Broadcaster'),
        logger,
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
        pairingCode: null,
        phoneNumber: (phoneNumber && !authState.creds.registered) ? phoneNumber : null,
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

        // Timeout after 120s — clean up socket to stop QR generation
        sessionState._readyTimeout = setTimeout(() => {
            sessionState.initializing = false;
            try { sock.end(); } catch (_) {}
            sessions.delete(sessionId);
            reject(new Error('Session initialization timeout (120s)'));
        }, 120000);
    });

    // Save credentials on every update
    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            // If phone number provided, request pairing code instead of QR
            if (sessionState.phoneNumber && !sessionState.pairingCode) {
                try {
                    const code = await sock.requestPairingCode(sessionState.phoneNumber);
                    sessionState.pairingCode = code;
                    sessionState.phoneNumber = null; // Don't request again
                    console.log(`[${sessionId}] Pairing code: ${code}`);
                    return; // Skip QR generation
                } catch (err) {
                    console.error(`[${sessionId}] Failed to request pairing code: ${err.message}`);
                    // Fall through to QR as fallback
                }
            }
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
                console.log(`[${sessionId}] Unrecoverable disconnect (${statusCode}), session cleaned up`);
            } else if (sessionState.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                // Auto-reconnect with exponential backoff
                sessionState.reconnectAttempts++;
                sessionState.initializing = false;
                clearTimeout(sessionState._readyTimeout);
                const backoff = Math.min(1000 * Math.pow(2, sessionState.reconnectAttempts - 1), 30000);
                console.log(`[${sessionId}] Reconnecting in ${backoff}ms (attempt ${sessionState.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);

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
                        console.error(`[${sessionId}] Reconnect failed: ${err.message}`);
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

    state.intentionalClose = true;
    try {
        state.sock.end();
    } catch (err) {
        console.error(`[${sessionId}] Error closing socket: ${err.message}`);
    }
    rateLimiters.delete(sessionId);
    sessions.delete(sessionId);
    console.log(`[${sessionId}] Session unloaded`);
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
            console.error(`[${sessionId}] Error during logout: ${err.message}`);
            try { state.sock.end(); } catch (_) {}
        }
        sessions.delete(sessionId);
    }
    rateLimiters.delete(sessionId);
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

// POST /api/sessions/:id/start - Create and initialize a session (QR or pairing code)
// Body: { phone_number?: "79991234567" } — if provided, uses pairing code instead of QR
app.post('/api/sessions/:id/start', async (req, res) => {
    const sessionId = req.params.id;
    const phoneNumber = req.body.phone_number || null;

    const existing = sessions.get(sessionId);
    if (existing) {
        if (existing.isConnected) {
            return res.json({ status: 'connected' });
        }
        if (existing.initializing) {
            return res.json({ status: 'initializing', pairing_code: existing.pairingCode || null });
        }
        // Stale session — clean up
        try { existing.sock.end(); } catch (_) {}
        sessions.delete(sessionId);
    }

    try {
        const state = await createSocket(sessionId, phoneNumber);
        // Don't await readyPromise (caller polls for QR/status), but catch rejection
        state.readyPromise.catch((err) => {
            console.log(`[${sessionId}] Session init failed: ${err.message}`);
        });
        res.json({ status: 'initializing', pairing_code: state.pairingCode || null });
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

// GET /api/sessions/:id/qr - Get QR code or pairing code for authentication
app.get('/api/sessions/:id/qr', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        return res.json({ status: 'not_found', qr: null, pairing_code: null });
    }
    if (state.isConnected) {
        return res.json({ status: 'connected', qr: null, pairing_code: null });
    }
    if (state.pairingCode) {
        return res.json({ status: 'pairing', qr: null, pairing_code: state.pairingCode });
    }
    if (!state.qrCode) {
        return res.json({ status: 'waiting', qr: null, pairing_code: null });
    }
    res.json({ status: 'pending', qr: state.qrCode, pairing_code: null });
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
                            const response = await axios.get(img, { responseType: 'arraybuffer', timeout: 30000 });
                            mimetype = response.headers['content-type'] || 'image/jpeg';
                            buffer = Buffer.from(response.data);
                        } else if (fs.existsSync(img)) {
                            buffer = fs.readFileSync(img);
                        } else {
                            console.warn(`[${sessionId}] Image not found: ${img}`);
                            continue;
                        }

                        const msgOptions = { image: buffer, mimetype };
                        // Single image: attach caption directly
                        if (images.length === 1 && caption) {
                            msgOptions.caption = caption;
                        }

                        const result = await state.sock.sendMessage(group_id, msgOptions);
                        console.log(`[${sessionId}] sendMessage[${i}] result: id=${result?.key?.id}`);
                    }

                    // Multiple images: send caption as separate text
                    if (images.length > 1 && caption) {
                        await state.sock.sendMessage(group_id, { text: caption });
                    }
                } else {
                    console.log(`[${sessionId}] Sending text to ${group_id}, text="${caption.substring(0, 50)}"`);
                    const result = await state.sock.sendMessage(group_id, { text: caption });
                    console.log(`[${sessionId}] sendMessage result: id=${result?.key?.id}`);
                }
            });
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

(async () => {
    try {
        const { version, isLatest } = await fetchLatestBaileysVersion();
        waVersion = version;
        console.log(`WA Web version: ${version.join('.')}${isLatest ? '' : ' (not latest)'}`);
    } catch (err) {
        console.warn(`Failed to fetch WA version, using default: ${err.message}`);
    }

    app.listen(PORT, () => {
        console.log(`WA Bridge (Baileys, idle timeout=${IDLE_TIMEOUT_MS / 1000}s) running on port ${PORT}`);
    });
})();

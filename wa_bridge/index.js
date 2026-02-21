const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const IDLE_TIMEOUT_MS = parseInt(process.env.IDLE_TIMEOUT_MS || '300000'); // 5 min default

// Multi-session map: sessionId -> { client, qrCode, isConnected, initializing, lastActivity }
const sessions = new Map();

/**
 * Remove stale Chromium lock files from session directory.
 * These get left behind when the container restarts and prevent
 * new browser instances from launching.
 */
function cleanStaleLocks(sessionId) {
    const sessionDir = path.join('.wwebjs_auth', `session-${sessionId}`);
    if (!fs.existsSync(sessionDir)) return;

    const lockFiles = ['SingletonLock', 'SingletonSocket', 'SingletonCookie'];
    const walkAndClean = (dir) => {
        try {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                if (entry.isDirectory()) {
                    walkAndClean(fullPath);
                } else if (lockFiles.includes(entry.name)) {
                    fs.unlinkSync(fullPath);
                    console.log(`[${sessionId}] Removed stale lock: ${fullPath}`);
                }
            }
        } catch (err) {
            // Ignore errors during cleanup
        }
    };
    walkAndClean(sessionDir);
}

/**
 * Create a whatsapp-web.js Client for the given sessionId,
 * wire up event handlers, and call client.initialize().
 * Returns a Promise that resolves when the client is ready
 * or rejects on auth failure / timeout.
 */
function createClient(sessionId) {
    // Clean up stale Chromium lock files before launching
    cleanStaleLocks(sessionId);
    const client = new Client({
        authStrategy: new LocalAuth({
            clientId: sessionId,
            dataPath: './.wwebjs_auth',
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ],
        },
    });

    const state = {
        client,
        qrCode: null,
        isConnected: false,
        initializing: true,
        lastActivity: Date.now(),
        readyPromise: null,
    };

    // Create a promise that resolves when client is ready
    state.readyPromise = new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Session initialization timeout (90s)'));
        }, 90000);

        client.on('ready', () => {
            clearTimeout(timeout);
            resolve();
        });

        client.on('auth_failure', (msg) => {
            clearTimeout(timeout);
            reject(new Error(`Auth failure: ${msg}`));
        });
    });

    client.on('qr', async (qr) => {
        state.qrCode = await qrcode.toDataURL(qr);
        console.log(`[${sessionId}] QR code generated`);
    });

    client.on('ready', () => {
        state.isConnected = true;
        state.initializing = false;
        state.qrCode = null;
        state.lastActivity = Date.now();
        console.log(`[${sessionId}] Client ready`);
    });

    client.on('disconnected', (reason) => {
        state.isConnected = false;
        state.initializing = false;
        console.log(`[${sessionId}] Disconnected: ${reason}`);
    });

    client.on('auth_failure', (msg) => {
        state.isConnected = false;
        state.initializing = false;
        console.log(`[${sessionId}] Auth failure: ${msg}`);
    });

    sessions.set(sessionId, state);

    client.initialize().catch((err) => {
        state.initializing = false;
        console.error(`[${sessionId}] Failed to initialize: ${err.message}`);
    });

    return state;
}

/**
 * Ensure a session is loaded and ready. If not loaded, start it
 * from volume and wait for ready. Returns the state or null.
 */
async function ensureSession(sessionId) {
    let state = sessions.get(sessionId);

    // Already connected — just update activity
    if (state && state.isConnected) {
        state.lastActivity = Date.now();
        return state;
    }

    // Currently initializing — wait for it
    if (state && state.initializing) {
        try {
            await state.readyPromise;
            state.lastActivity = Date.now();
            return state;
        } catch {
            return null;
        }
    }

    // Not loaded — check if session data exists in volume
    const sessionDir = `./.wwebjs_auth/session-${sessionId}`;
    if (!fs.existsSync(sessionDir)) {
        return null; // No stored session, can't auto-start
    }

    // Load session from volume
    console.log(`[${sessionId}] Loading session on demand...`);
    state = createClient(sessionId);

    try {
        await state.readyPromise;
        state.lastActivity = Date.now();
        return state;
    } catch (err) {
        console.error(`[${sessionId}] Failed to load: ${err.message}`);
        return null;
    }
}

/**
 * Destroy a session and free resources.
 */
async function destroySession(sessionId) {
    const state = sessions.get(sessionId);
    if (!state) return;

    try {
        await state.client.destroy();
    } catch (err) {
        console.error(`[${sessionId}] Error destroying: ${err.message}`);
    }
    sessions.delete(sessionId);
    console.log(`[${sessionId}] Session unloaded`);
}

// ---- Idle timeout: unload sessions after inactivity ----

setInterval(() => {
    const now = Date.now();
    for (const [id, state] of sessions) {
        if (state.isConnected && (now - state.lastActivity > IDLE_TIMEOUT_MS)) {
            console.log(`[${id}] Idle for ${Math.round(IDLE_TIMEOUT_MS / 1000)}s, unloading`);
            destroySession(id);
        }
    }
}, 60000); // Check every minute

// ---- REST API endpoints ----

// POST /api/sessions/:id/start - Create and initialize a session (for QR flow)
app.post('/api/sessions/:id/start', (req, res) => {
    const sessionId = req.params.id;
    const existing = sessions.get(sessionId);

    if (existing) {
        if (existing.isConnected) {
            return res.json({ status: 'connected' });
        }
        if (existing.initializing) {
            return res.json({ status: 'initializing' });
        }
        // Stale session — destroy and recreate
        existing.client.destroy().catch(() => {});
        sessions.delete(sessionId);
    }

    createClient(sessionId);
    res.json({ status: 'initializing' });
});

// DELETE /api/sessions/:id - Destroy a session
app.delete('/api/sessions/:id', async (req, res) => {
    const sessionId = req.params.id;
    if (!sessions.has(sessionId)) {
        return res.json({ ok: true });
    }
    await destroySession(sessionId);
    res.json({ ok: true });
});

// GET /api/sessions/:id/status - Connection status
app.get('/api/sessions/:id/status', (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        return res.json({ connected: false, exists: false });
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

    const { group_id, text, image_path, image_paths } = req.body;
    // Support both single image_path and batch image_paths
    const images = image_paths || (image_path ? [image_path] : []);
    if (!group_id || (!text && images.length === 0)) {
        return res.status(400).json({ error: 'group_id and text or image_path(s) are required' });
    }

    // Auto-load session on demand
    const state = await ensureSession(sessionId);
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        const caption = text || '';

        if (images.length > 0) {
            // Filter to existing files
            const validImages = images.filter(p => fs.existsSync(p));
            console.log(`[${sessionId}] Sending ${validImages.length} image(s) to group_id=${group_id}, text="${caption.substring(0, 50)}"`);

            if (validImages.length === 0) {
                // No valid images, send text only
                if (caption) {
                    const result = await state.client.sendMessage(group_id, caption);
                    console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
                }
            } else if (validImages.length === 1) {
                // Single image: send with caption directly
                const media = MessageMedia.fromFilePath(validImages[0]);
                const opts = caption ? { caption } : {};
                const result = await state.client.sendMessage(group_id, media, opts);
                console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
            } else {
                // Multiple images: send all except last without caption,
                // last image gets the caption
                const allButLast = validImages.slice(0, -1);
                const lastImage = validImages[validImages.length - 1];

                // Send first images without caption
                const sendPromises = allButLast.map((imgPath) => {
                    const media = MessageMedia.fromFilePath(imgPath);
                    return state.client.sendMessage(group_id, media);
                });
                const results = await Promise.all(sendPromises);
                results.forEach((result, i) => {
                    console.log(`[${sessionId}] sendMessage[${i}] result: id=${result?.id?._serialized}, ack=${result?.ack}`);
                });

                // Send last image with caption
                const lastMedia = MessageMedia.fromFilePath(lastImage);
                const opts = caption ? { caption } : {};
                const lastResult = await state.client.sendMessage(group_id, lastMedia, opts);
                console.log(`[${sessionId}] sendMessage[last] result: id=${lastResult?.id?._serialized}, ack=${lastResult?.ack}`);
            }
        } else {
            console.log(`[${sessionId}] Sending text to group_id=${group_id}, text="${caption.substring(0, 50)}"`);
            const result = await state.client.sendMessage(group_id, caption);
            console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
        }

        res.json({ ok: true });
    } catch (error) {
        console.error(`[${sessionId}] Send error: ${error.message}`);
        res.status(500).json({ error: error.message });
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
        const chats = await state.client.getChats();
        const groups = chats
            .filter((chat) => chat.isGroup)
            .map((chat) => ({
                id: chat.id._serialized,
                name: chat.name,
            }));
        res.json(groups);
    } catch (error) {
        console.error(`[${sessionId}] Groups error: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});

// No auto-restore on startup — sessions are loaded on demand

app.listen(PORT, () => {
    console.log(`WA Bridge (multi-session, idle timeout=${IDLE_TIMEOUT_MS / 1000}s) running on port ${PORT}`);
});

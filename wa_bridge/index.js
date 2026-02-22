const express = require('express');
const { Client, RemoteAuth, MessageMedia } = require('whatsapp-web.js');
const { MongoStore } = require('wwebjs-mongo');
const mongoose = require('mongoose');
const qrcode = require('qrcode');
const fs = require('fs');
const axios = require('axios');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const IDLE_TIMEOUT_MS = parseInt(process.env.IDLE_TIMEOUT_MS || '300000');
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/whatsapp_sessions';

const sessions = new Map();
const loadingPromises = new Map(); // Prevents duplicate session loading
let store; // MongoStore instance, initialized on startup

/**
 * Create a whatsapp-web.js Client for the given sessionId,
 * wire up event handlers, and call client.initialize().
 * Returns the state object.
 */
function createClient(sessionId) {
    const client = new Client({
        authStrategy: new RemoteAuth({
            store,
            clientId: sessionId,
            backupSyncIntervalMs: 60000, // First backup ~1 min after connection
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

    client.on('remote_session_saved', () => {
        console.log(`[${sessionId}] Session saved to MongoDB`);
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
 * Load a session from MongoDB. Called only from ensureSession
 * under the loadingPromises lock.
 */
async function loadSessionFromMongo(sessionId) {
    // Clean up stale in-memory state if present
    const stale = sessions.get(sessionId);
    if (stale) {
        try { await stale.client.destroy(); } catch (_) {}
        sessions.delete(sessionId);
    }

    // Check if session exists in MongoDB
    // RemoteAuth stores sessions with dataPath prefix (e.g. /app/.wwebjs_auth/RemoteAuth-{id})
    // so we search collections by suffix instead of exact name
    let sessionExists;
    try {
        const collections = await mongoose.connection.db.listCollections().toArray();
        sessionExists = collections.some(c => c.name.endsWith(`RemoteAuth-${sessionId}.files`));
    } catch (err) {
        console.error(`[${sessionId}] MongoDB lookup failed: ${err.message}`);
        return null;
    }
    if (!sessionExists) {
        return null;
    }

    console.log(`[${sessionId}] Loading session from MongoDB on demand...`);
    const state = createClient(sessionId);

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
 * Ensure a session is loaded and ready. If not loaded, check MongoDB
 * and start it on demand. Returns the state or null.
 * Uses loadingPromises to prevent duplicate Chromium instances for the same session.
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

    // If another request is already loading this session, wait for it
    if (loadingPromises.has(sessionId)) {
        return loadingPromises.get(sessionId);
    }

    const loadPromise = loadSessionFromMongo(sessionId);
    loadingPromises.set(sessionId, loadPromise);

    try {
        return await loadPromise;
    } finally {
        loadingPromises.delete(sessionId);
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

    const { group_id, text, image_paths, image_urls } = req.body;
    // Support both URL-based (S3) and legacy local paths
    const images = image_urls || image_paths || [];
    const isUrlMode = !!image_urls;
    if (!group_id || (!text && images.length === 0)) {
        return res.status(400).json({ error: 'group_id and text or images are required' });
    }

    // Auto-load session on demand
    const state = await ensureSession(sessionId);
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        const caption = text || '';

        if (images.length > 0) {
            // Load media from URLs or local paths
            const mediaItems = [];
            for (const img of images) {
                if (isUrlMode || img.startsWith('http://') || img.startsWith('https://')) {
                    const response = await axios.get(img, { responseType: 'arraybuffer' });
                    const mime = response.headers['content-type'] || 'image/jpeg';
                    const base64 = Buffer.from(response.data).toString('base64');
                    mediaItems.push(new MessageMedia(mime, base64));
                } else if (fs.existsSync(img)) {
                    mediaItems.push(MessageMedia.fromFilePath(img));
                }
            }

            console.log(`[${sessionId}] Sending ${mediaItems.length} image(s) to group_id=${group_id}, text="${caption.substring(0, 50)}"`);

            if (mediaItems.length === 0) {
                if (caption) {
                    const result = await state.client.sendMessage(group_id, caption);
                    console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
                }
            } else if (mediaItems.length === 1) {
                const opts = caption ? { caption } : {};
                const result = await state.client.sendMessage(group_id, mediaItems[0], opts);
                console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
            } else {
                const sendPromises = mediaItems.map((media) => {
                    return state.client.sendMessage(group_id, media);
                });
                const results = await Promise.all(sendPromises);
                results.forEach((result, i) => {
                    console.log(`[${sessionId}] sendMessage[${i}] result: id=${result?.id?._serialized}, ack=${result?.ack}`);
                });
                if (caption) {
                    await state.client.sendMessage(group_id, caption);
                }
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

async function main() {
    // Ensure dataPath directory exists for RemoteAuth session extraction
    fs.mkdirSync('.wwebjs_auth', { recursive: true });

    await mongoose.connect(MONGODB_URI);
    console.log('Connected to MongoDB');

    mongoose.connection.on('error', (err) => {
        console.error('MongoDB connection error:', err.message);
    });
    mongoose.connection.on('disconnected', () => {
        console.warn('MongoDB disconnected');
    });

    const rawStore = new MongoStore({ mongoose });

    // RemoteAuth bug: save() uses full dataPath (e.g. "/app/.wwebjs_auth/RemoteAuth-14")
    // but sessionExists()/extract() use short name (e.g. "RemoteAuth-14").
    // This wrapper resolves the short name to the actual collection name.
    async function resolveSessionName(shortName) {
        const exactExists = await rawStore.sessionExists({ session: shortName });
        if (exactExists) return shortName;

        const collections = await mongoose.connection.db.listCollections().toArray();
        const match = collections.find(c => c.name.endsWith(`${shortName}.files`));
        if (match) {
            return match.name.slice('whatsapp-'.length, -'.files'.length);
        }
        return shortName;
    }

    store = {
        sessionExists: async (opts) => {
            const resolved = await resolveSessionName(opts.session);
            const result = await rawStore.sessionExists({ session: resolved });
            console.log(`[store] sessionExists("${opts.session}" -> "${resolved}") = ${result}`);
            return result;
        },
        save: async (opts) => {
            console.log(`[store] save("${opts.session}")`);
            return rawStore.save(opts);
        },
        extract: async (opts) => {
            const resolved = await resolveSessionName(opts.session);
            console.log(`[store] extract("${opts.session}" -> "${resolved}")`);
            return rawStore.extract({ ...opts, session: resolved });
        },
        delete: async (opts) => {
            const resolved = await resolveSessionName(opts.session);
            console.log(`[store] delete("${opts.session}" -> "${resolved}")`);
            return rawStore.delete({ ...opts, session: resolved });
        },
    };

    app.listen(PORT, () => {
        console.log(`WA Bridge (RemoteAuth/MongoDB, idle timeout=${IDLE_TIMEOUT_MS / 1000}s) running on port ${PORT}`);
    });
}

main().catch((err) => {
    console.error('Failed to start:', err);
    process.exit(1);
});

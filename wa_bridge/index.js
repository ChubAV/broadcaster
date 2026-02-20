const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const fs = require('fs');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Multi-session map: sessionId -> { client, qrCode, isConnected, initializing }
const sessions = new Map();

/**
 * Create a whatsapp-web.js Client for the given sessionId,
 * wire up event handlers, and call client.initialize().
 */
function createClient(sessionId) {
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
    };

    client.on('qr', async (qr) => {
        state.qrCode = await qrcode.toDataURL(qr);
        console.log(`[${sessionId}] QR code generated`);
    });

    client.on('ready', () => {
        state.isConnected = true;
        state.initializing = false;
        state.qrCode = null;
        console.log(`[${sessionId}] WhatsApp client is ready`);
    });

    client.on('disconnected', (reason) => {
        state.isConnected = false;
        state.initializing = false;
        console.log(`[${sessionId}] WhatsApp client disconnected: ${reason}`);
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

// ---- REST API endpoints ----

// POST /api/sessions/:id/start - Create and initialize a session
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
        // Session exists but is neither connected nor initializing (e.g. disconnected).
        // Destroy old client and create a fresh one.
        existing.client.destroy().catch(() => {});
        sessions.delete(sessionId);
    }

    createClient(sessionId);
    res.json({ status: 'initializing' });
});

// DELETE /api/sessions/:id - Destroy a session
app.delete('/api/sessions/:id', async (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        await state.client.destroy();
    } catch (err) {
        console.error(`[${sessionId}] Error destroying client: ${err.message}`);
    }

    sessions.delete(sessionId);
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

// POST /api/sessions/:id/send - Send message to a group
app.post('/api/sessions/:id/send', async (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }

    const { group_id, text, image_path } = req.body;

    if (!group_id || !text) {
        return res.status(400).json({ error: 'group_id and text are required' });
    }

    try {
        console.log(`[${sessionId}] Sending to group_id=${group_id}, text="${text.substring(0, 50)}...", image_path=${image_path || 'none'}`);
        let result;
        if (image_path && fs.existsSync(image_path)) {
            const media = MessageMedia.fromFilePath(image_path);
            result = await state.client.sendMessage(group_id, media, { caption: text });
        } else {
            result = await state.client.sendMessage(group_id, text);
        }
        console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
        res.json({ ok: true });
    } catch (error) {
        console.error(`[${sessionId}] Send error: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});

// GET /api/sessions/:id/groups - List groups for a session
app.get('/api/sessions/:id/groups', async (req, res) => {
    const sessionId = req.params.id;
    const state = sessions.get(sessionId);

    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
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

// No auto-initialization on startup - sessions are created on demand via POST /start

app.listen(PORT, () => {
    console.log(`WA Bridge (multi-session) running on port ${PORT}`);
});

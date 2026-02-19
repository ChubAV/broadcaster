const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './.wwebjs_auth' }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    },
});

let qrCode = null;
let isConnected = false;

client.on('qr', async (qr) => {
    qrCode = await qrcode.toDataURL(qr);
    console.log('QR code generated');
});

client.on('ready', () => {
    isConnected = true;
    qrCode = null;
    console.log('WhatsApp client is ready');
});

client.on('disconnected', (reason) => {
    isConnected = false;
    console.log('WhatsApp client disconnected:', reason);
});

client.on('auth_failure', (msg) => {
    isConnected = false;
    console.log('Auth failure:', msg);
});

// REST API endpoints

// GET /api/status - connection status
app.get('/api/status', (req, res) => {
    res.json({ connected: isConnected });
});

// GET /api/qr - get QR code for authentication
app.get('/api/qr', (req, res) => {
    if (isConnected) {
        return res.json({ status: 'connected', qr: null });
    }
    if (!qrCode) {
        return res.json({ status: 'waiting', qr: null });
    }
    res.json({ status: 'pending', qr: qrCode });
});

// POST /api/send - send message to group
app.post('/api/send', async (req, res) => {
    if (!isConnected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }

    const { group_id, text, image_path } = req.body;

    if (!group_id || !text) {
        return res.status(400).json({ error: 'group_id and text are required' });
    }

    try {
        if (image_path && fs.existsSync(image_path)) {
            const media = MessageMedia.fromFilePath(image_path);
            await client.sendMessage(group_id, media, { caption: text });
        } else {
            await client.sendMessage(group_id, text);
        }
        res.json({ ok: true });
    } catch (error) {
        console.error('Send error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// GET /api/groups - list groups
app.get('/api/groups', async (req, res) => {
    if (!isConnected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }

    try {
        const chats = await client.getChats();
        const groups = chats
            .filter(chat => chat.isGroup)
            .map(chat => ({
                id: chat.id._serialized,
                name: chat.name,
            }));
        res.json(groups);
    } catch (error) {
        console.error('Groups error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Initialize WhatsApp client
client.initialize().catch((err) => {
    console.error('Failed to initialize WhatsApp client:', err.message);
});

app.listen(PORT, () => {
    console.log(`WA Bridge running on port ${PORT}`);
});

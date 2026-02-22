# WhatsApp RemoteAuth + MongoDB Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace WhatsApp LocalAuth (Docker volume) with RemoteAuth + MongoDB for reliable, scalable session storage.

**Architecture:** The WA Bridge (Node.js) switches from `LocalAuth` (filesystem) to `RemoteAuth` with `MongoStore` from `wwebjs-mongo`. MongoDB runs as a Docker Compose service. Python code is untouched — the REST API contract stays the same.

**Tech Stack:** whatsapp-web.js RemoteAuth, wwebjs-mongo, mongoose, MongoDB 7

---

### Task 1: Add MongoDB to Docker Compose

**Files:**
- Modify: `docker-compose.yml:71-83`
- Modify: `docker-compose.dev.yml:19-23`

**Step 1: Add mongo service and update wa-bridge in docker-compose.yml**

In `docker-compose.yml`, add `mongo` service before `wa-bridge`, update `wa-bridge` to depend on mongo and pass `MONGODB_URI`, remove `wa_session` volume:

```yaml
  mongo:
    image: mongo:7
    container_name: mongo-broadcaster
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 5s
      timeout: 5s
      retries: 5

  wa-bridge:
    build:
      context: ./wa_bridge
      dockerfile: Dockerfile
    container_name: wa-bridge-broadcaster
    ports:
      - "3000:3000"
    depends_on:
      mongo:
        condition: service_healthy
    environment:
      - MONGODB_URI=mongodb://mongo:27017/whatsapp_sessions

volumes:
  pgdata:
  mongodata:
```

Key changes:
- Remove `wa_session` volume from `wa-bridge` and from `volumes:` section
- Add `mongodata` volume
- Add `mongo` service with healthcheck
- Add `depends_on` and `environment` to `wa-bridge`

**Step 2: Update docker-compose.dev.yml**

Remove `wa_session` volume reference from wa-bridge override:

```yaml
  wa-bridge:
    volumes:
      - ./wa_bridge:/app
      - /app/node_modules
```

**Step 3: Commit**

```bash
git add docker-compose.yml docker-compose.dev.yml
git commit -m "infra: add MongoDB service, remove wa_session volume"
```

---

### Task 2: Add npm dependencies

**Files:**
- Modify: `wa_bridge/package.json`

**Step 1: Add mongoose and wwebjs-mongo to package.json**

```json
{
  "name": "wa-bridge",
  "version": "1.0.0",
  "description": "WhatsApp Web Bridge for Broadcaster",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "axios": "^1.7.0",
    "express": "^4.18.0",
    "mongoose": "^8.0.0",
    "whatsapp-web.js": "^1.25.0",
    "wwebjs-mongo": "^1.1.0",
    "qrcode": "^1.5.0"
  }
}
```

Changes:
- Add `mongoose` (^8.0.0) — MongoDB ODM, required by wwebjs-mongo
- Add `wwebjs-mongo` (^1.1.0) — MongoStore for RemoteAuth
- Remove `multer` — unused dependency

**Step 2: Commit**

```bash
git add wa_bridge/package.json
git commit -m "deps: add mongoose and wwebjs-mongo, remove unused multer"
```

---

### Task 3: Rewrite wa_bridge/index.js to use RemoteAuth

**Files:**
- Modify: `wa_bridge/index.js` (full rewrite of auth strategy and session management)

**Step 1: Replace imports and add MongoDB connection**

Replace lines 1-15 of `index.js`. Remove `LocalAuth`, `fs`, `path` imports. Add `RemoteAuth`, `mongoose`, `MongoStore`:

```js
const express = require('express');
const { Client, RemoteAuth, MessageMedia } = require('whatsapp-web.js');
const { MongoStore } = require('wwebjs-mongo');
const mongoose = require('mongoose');
const qrcode = require('qrcode');
const axios = require('axios');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const IDLE_TIMEOUT_MS = parseInt(process.env.IDLE_TIMEOUT_MS || '300000');
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/whatsapp_sessions';

const sessions = new Map();
let store; // MongoStore instance, initialized on startup
```

**Step 2: Remove cleanStaleLocks function**

Delete the entire `cleanStaleLocks` function (lines 17-44). It's no longer needed — RemoteAuth doesn't use local Chrome profile directories.

**Step 3: Rewrite createClient to use RemoteAuth**

Replace the `createClient` function (lines 52-129) with:

```js
function createClient(sessionId) {
    const client = new Client({
        authStrategy: new RemoteAuth({
            store,
            clientId: sessionId,
            backupSyncIntervalMs: 300000, // Sync to MongoDB every 5 min
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
```

Key differences from original:
- `LocalAuth` → `RemoteAuth` with `store` and `backupSyncIntervalMs`
- No `cleanStaleLocks` call
- Added `remote_session_saved` event handler for logging

**Step 4: Rewrite ensureSession to use MongoStore**

Replace the `ensureSession` function (lines 135-173) with:

```js
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

    // Not loaded — check if session exists in MongoDB
    const sessionExists = await store.sessionExists({ session: `RemoteAuth-${sessionId}` });
    if (!sessionExists) {
        return null;
    }

    // Load session from MongoDB
    console.log(`[${sessionId}] Loading session from MongoDB on demand...`);
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
```

Key difference: replaced `fs.existsSync(sessionDir)` with `store.sessionExists()`.

**Step 5: Replace app startup with async MongoDB init**

Replace lines 359-363 (the `app.listen` block) with:

```js
async function main() {
    await mongoose.connect(MONGODB_URI);
    console.log('Connected to MongoDB');

    store = new MongoStore({ mongoose });

    app.listen(PORT, () => {
        console.log(`WA Bridge (RemoteAuth/MongoDB, idle timeout=${IDLE_TIMEOUT_MS / 1000}s) running on port ${PORT}`);
    });
}

main().catch((err) => {
    console.error('Failed to start:', err);
    process.exit(1);
});
```

**Step 6: Commit**

```bash
git add wa_bridge/index.js
git commit -m "feat: switch WhatsApp sessions from LocalAuth to RemoteAuth + MongoDB"
```

---

### Task 4: Update .env.example and documentation

**Files:**
- Modify: `.env.example`
- Modify: `docs/plans/2026-02-22-whatsapp-remoteauth-mongodb-design.md` (mark complete)

**Step 1: Add MONGODB_URI to .env.example**

Add after the `WA_BRIDGE_URL` line:

```
MONGODB_URI=mongodb://mongo:27017/whatsapp_sessions
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: add MONGODB_URI to .env.example"
```

---

### Task 5: Build and verify

**Step 1: Install new npm dependencies**

```bash
cd wa_bridge && npm install && cd ..
```

Expected: `mongoose` and `wwebjs-mongo` installed, package-lock.json updated.

**Step 2: Verify docker-compose config is valid**

```bash
docker compose config --quiet
```

Expected: no errors.

**Step 3: Commit package-lock.json**

```bash
git add wa_bridge/package-lock.json
git commit -m "chore: update package-lock.json with new dependencies"
```

---

## Summary of Changes

| File | Change |
|------|--------|
| `docker-compose.yml` | Add `mongo` service, remove `wa_session` volume, add env to wa-bridge |
| `docker-compose.dev.yml` | Remove `wa_session` volume from wa-bridge |
| `wa_bridge/package.json` | Add `mongoose`, `wwebjs-mongo`; remove `multer` |
| `wa_bridge/index.js` | `LocalAuth` → `RemoteAuth` + `MongoStore`, remove filesystem ops |
| `.env.example` | Add `MONGODB_URI` |

**Python code unchanged.** REST API contract unchanged. Users re-scan QR after deployment.

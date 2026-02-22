# WhatsApp RemoteAuth + MongoDB Design

## Problem

WhatsApp sessions are stored via `LocalAuth` in a Docker volume (`wa_session`). This has two issues:

1. **Reliability** — sessions can be lost when containers are recreated or volumes pruned
2. **Scalability** — sessions are local to one wa-bridge instance, preventing horizontal scaling

## Solution

Replace `LocalAuth` with `RemoteAuth` using `wwebjs-mongo` to store sessions in MongoDB.

## Architecture

### Current Flow
```
wa-bridge (Node.js) → LocalAuth → Docker volume (.wwebjs_auth/session-{id}/)
```

### New Flow
```
wa-bridge (Node.js) → RemoteAuth → MongoStore (wwebjs-mongo) → MongoDB (GridFS)
```

## Changes

### 1. Infrastructure (docker-compose.yml)

- Add `mongo` service (image: `mongo:7`) with persistent volume `mongo_data`
- Pass `MONGODB_URI` env var to `wa-bridge` service
- Remove `wa_session` volume (no longer needed)

### 2. WA Bridge (wa_bridge/index.js)

- Add dependencies: `wwebjs-mongo`, `mongoose`
- Connect to MongoDB via mongoose on startup
- Replace `LocalAuth` with `RemoteAuth`:
  ```js
  const { RemoteAuth } = require('whatsapp-web.js');
  const { MongoStore } = require('wwebjs-mongo');

  const store = new MongoStore({ mongoose });

  // Per client:
  new RemoteAuth({
    store,
    clientId: sessionId,
    backupSyncIntervalMs: 300000  // 5 min sync interval
  })
  ```
- Handle `remote_session_saved` event for logging
- Remove filesystem-based session directory checks and lock file cleanup

### 3. Configuration

- `.env.example`: add `MONGODB_URI=mongodb://mongo:27017/whatsapp_sessions`
- `wa_bridge/index.js`: read `process.env.MONGODB_URI`

### 4. Unchanged

- Python code (`app/messengers/whatsapp.py`) — no changes
- REST API endpoints — same interface
- `MessengerAccount` model — no changes
- QR connection flow — no changes
- Idle timeout management — no changes

## Migration

No migration needed. Users will re-scan QR codes after deployment. The `wa_session` Docker volume can be safely removed.

## New Dependencies

- `wwebjs-mongo` (npm) — MongoDB store for whatsapp-web.js RemoteAuth
- `mongoose` (npm) — MongoDB ODM, required by wwebjs-mongo
- `mongo:7` (Docker image) — MongoDB server

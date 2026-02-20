# WhatsApp Multi-Session Bridge Design

**Date:** 2026-02-20
**Status:** Approved

## Problem

- Single global whatsapp-web.js Client in wa-bridge — only one WhatsApp account for the entire service
- Multi-user SaaS requires each user to connect their own WhatsApp account

## Solution

Multi-session wa-bridge: one container manages multiple whatsapp-web.js Client instances, each identified by a `sessionId` (= MessengerAccount.id).

## Architecture

### wa-bridge (Node.js)

- `sessions` Map: `sessionId -> {client, qrCode, isConnected}`
- `LocalAuth` with `clientId = sessionId` (creates subdirectories automatically)
- Docker volume `wa_session` stores all sessions in `/app/.wwebjs_auth/session-{id}/`

### API Endpoints (all per-session)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/sessions/:id/start` | POST | Create Client with LocalAuth(clientId=id), initialize |
| `/api/sessions/:id` | DELETE | Disconnect Client, remove session data |
| `/api/sessions/:id/qr` | GET | QR code for this session |
| `/api/sessions/:id/status` | GET | Connection status |
| `/api/sessions/:id/send` | POST | Send message (group_id, text, image_path) |
| `/api/sessions/:id/groups` | GET | List WhatsApp groups |

### Python Side

- `WhatsAppMessenger` accepts `session_id`, passes it in bridge URL path
- Connect flow: create MessengerAccount -> `POST /sessions/{account_id}/start` -> poll QR/status
- Group sync, send — all via per-session endpoints
- `MessengerAccount.credentials` stores sessionId (= account.id as string)

### Session Lifecycle

1. User clicks "Connect WA" -> Python creates MessengerAccount -> `POST /sessions/{id}/start`
2. Bridge creates Client -> generates QR -> user scans
3. Client connected -> `LocalAuth` saves data to `/app/.wwebjs_auth/session-{id}/`
4. On bridge restart -> Python calls `POST /sessions/{id}/start` for all active WA accounts -> bridge restores from volume

### Session Storage

- Docker volume with per-session subdirectories (LocalAuth handles this natively)
- No database storage of session data (session files can be 10-50MB each)
- Volume is tied to the server

### Changes Required

**wa-bridge/index.js:**
- Replace single global Client with sessions Map
- Parameterize all endpoints with `:sessionId`
- Add session create/destroy endpoints
- Handle per-session events (qr, ready, disconnected, auth_failure)

**app/messengers/whatsapp.py:**
- Add `session_id` parameter to constructor and all methods
- Update all bridge URLs to include session_id path segment

**app/routes/pages.py:**
- Update WA connect flow to create session on bridge
- Update QR/status polling to use per-session endpoints
- Update group sync to use per-session endpoint
- Add session restoration on app startup (or lazy on first use)

**app/worker/tasks.py:**
- Pass session_id when creating WhatsAppMessenger
- Use account.id as session_id

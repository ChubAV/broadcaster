# WhatsApp Two-Phase Sync Design

## Problem

Large WhatsApp accounts (240+ groups) fail during initial connection:
- `readyPromise` times out at 120s while Baileys syncs
- Session enters bad state → `loggedOut (401)` → session files deleted → all progress lost
- User sees "Internal server error"

## Solution: Two-Phase Connection

Split connection into two phases: **connecting** (QR auth) and **syncing** (group loading).

## Account Status Flow

```
disconnected → connecting → syncing → active
                                ↓
                            sync_failed
```

- `connecting` — QR scanned, waiting for `connection: 'open'`
- `syncing` — Baileys connected, loading groups in background
- `active` — groups loaded, account fully ready
- `sync_failed` — group loading failed after all retries

## WA Bridge Changes (wa_bridge/index.js)

### New session state field: `syncState`

Values: `null` | `'syncing'` | `'ready'` | `'failed'`

### Connection flow

1. `connection: 'open'` → set `syncState: 'syncing'`
2. Wait 30 seconds (let Baileys sync internally)
3. Call `groupFetchAllParticipating()`
4. On error → retry with exponential backoff (30s, 60s, 120s), max 3 attempts
5. On success → store groups in `sessionState.groups`, set `syncState: 'ready'`
6. On final failure → set `syncState: 'failed'`

### New endpoint

`GET /api/sessions/:id/sync-status` → `{ state: 'syncing'|'ready'|'failed', groups: [...] | null }`

### Timeout changes

- `readyPromise` timeout: 120s → 600s (10 min)
- Idle timeout: skip sessions in `syncState: 'syncing'`

## Python Changes

### Model: MessengerAccount

Add `sync_failed` as valid status value (already has `disconnected`, `connecting`, `active`).
Add `syncing` status.

### Pages: accounts.py

**QR status polling:**
- On `connected: true` → update account to `syncing`, redirect to accounts page

**New endpoint: `GET /accounts/{id}/sync-status`**
- Polls bridge `GET /sync-status`
- When `ready` → save groups to DB, update account → `active`
- When `failed` → update account → `sync_failed`
- Returns HTML partial for HTMX

**New endpoint: `POST /accounts/{id}/retry-sync`**
- Resets `sync_failed` → `syncing`, triggers bridge retry

### Template: accounts list

For `syncing` accounts:
- Yellow badge "Синхронизация..." with spinner
- "Загружаем группы из WhatsApp..." text
- Disabled action buttons
- HTMX polling every 5 seconds

For `sync_failed` accounts:
- Red badge "Ошибка синхронизации"
- "Повторить" button

### Template: QR page

After successful scan: show "Подключено! Начинаем синхронизацию..." then redirect to accounts after 2 seconds.

## Error Handling

- **Idle timeout during sync**: Do NOT unload syncing sessions
- **restartRequired (515)**: Reconnect preserves sync state
- **loggedOut (401)**: Full reset (existing behavior)
- **groupFetchAllParticipating() failure**: 3 retries, then `sync_failed`
- **User navigates away and back**: Polling picks up current state

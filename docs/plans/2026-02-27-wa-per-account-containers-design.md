# WhatsApp Per-Account Container Architecture

## Date: 2026-02-27

## Problem

Current architecture uses a single `wa-bridge` container for all WhatsApp accounts. This means:
- One session crash affects all sessions
- No memory isolation between accounts
- Rate limiting is shared across accounts
- Cannot scale independently per account

## Solution

Replace the single `wa-bridge` with dynamically managed per-account containers (`wa-worker-{account_id}`). Each container handles one WhatsApp account exclusively: auth, sync, sending, and queue consumption.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Container responsibility | Unified (auth + sync + send + queue) | No session lock conflicts, single codebase |
| Orchestration | Docker API (docker-py) via Celery beat | Full control, programmatic management |
| Shutdown | Self-shutdown (process.exit after 5min idle) | Reliable, no external dependency for timing |

## Architecture

```
check_schedules (Celery Beat)
      │
      ▼
RPUSH wa:queue:{account_id}  ←── per-account Redis queue
SADD wa:active_accounts
      │
      ▼
Container Manager (Beat task, 15s interval)
      │  docker-py
      ▼
wa-worker-{account_id}       ←── one container per account
├── Baileys session (sole owner)
├── HTTP API (QR, status, groups)
├── Redis BLPOP consumer
├── Redis RPUSH result publisher
└── Self-shutdown after 5min idle
      │
      ▼
RPUSH wa:results
      │
      ▼
Result Processor (Beat task, 5s interval)
      │
      ▼
SendLog (PostgreSQL)
```

## Components

### 1. wa-worker (Node.js container, fork of wa_bridge)

- **Image**: `broadcaster-wa-worker:latest`
- **Env**: `ACCOUNT_ID`, `REDIS_URL`, `RATE_LIMIT_PER_MINUTE=8`, `IDLE_SHUTDOWN_SEC=300`
- **Volume**: `wa_sessions:/app/sessions` (shared, reads only `sessions/{ACCOUNT_ID}/`)
- **Memory**: 256MB limit
- **Network**: `broadcaster_default` (access to Redis)

Lifecycle:
1. Connect to Redis
2. Load Baileys session from `/app/sessions/{ACCOUNT_ID}/`
3. Wait for `connection.update` → connected
4. Start BLPOP loop on `wa:queue:{ACCOUNT_ID}`
5. Process tasks with rate limiting (8/min) and anti-ban (composing + 1.5-4s delay)
6. Push results to `wa:results`
7. After 5 min with empty queue → graceful shutdown (sock.end(), process.exit(0))

HTTP API preserved from wa-bridge:
- `POST /api/sessions/:id/start` — start QR auth
- `GET /api/sessions/:id/qr` — get QR code
- `GET /api/sessions/:id/status` — connection status
- `GET /api/sessions/:id/groups` — list groups
- `GET /api/sessions/:id/sync-status` — sync state
- `POST /api/sessions/:id/retry-sync` — retry sync
- `DELETE /api/sessions/:id` — destroy session

### 2. Container Manager (Python, Celery beat task)

Beat task `manage_wa_containers` every 15 seconds:
1. Read `wa:active_accounts` from Redis
2. For each account with non-empty queue and no running container → start container
3. For each exited container → remove (docker.remove)
4. Write container endpoint to `wa:endpoint:{account_id}` (e.g., `http://wa-worker-{id}:3000`)

Uses `docker-py` library. Requires `/var/run/docker.sock` mount on celery-beat/worker-default.

### 3. Dispatcher (modified check_schedules)

Instead of `send_whatsapp_message.apply_async(queue="whatsapp")`:
1. Collect full task data (ad_text, ad_images URLs, group_external_id, group_name, user_id)
2. `RPUSH wa:queue:{account_id}` with JSON payload
3. `SADD wa:active_accounts, account_id`

Task payload format:
```json
{
    "task_id": "uuid",
    "ad_id": 123,
    "group_id": 456,
    "account_id": 789,
    "schedule_id": 10,
    "user_id": 5,
    "ad_text": "...",
    "ad_title": "...",
    "ad_images": ["https://s3.../img1.jpg"],
    "group_external_id": "120363001234@g.us",
    "group_name": "...",
    "created_at": "2026-02-27T12:00:00Z"
}
```

### 4. Result Processor (Python, Celery beat task)

Beat task `process_wa_results` every 5 seconds:
1. LPOP batch from `wa:results`
2. Create SendLog entries in PostgreSQL
3. Update group.last_error / group.error_at

Result format:
```json
{
    "task_id": "uuid",
    "account_id": 789,
    "ad_id": 123,
    "group_id": 456,
    "schedule_id": 10,
    "user_id": 5,
    "status": "ok|fail",
    "error_message": null,
    "no_retry": false,
    "ad_title": "...",
    "group_name": "...",
    "messenger_type": "wa",
    "sent_at": "2026-02-27T12:00:05Z"
}
```

### 5. HTTP Router (modified WhatsAppMessenger)

For QR/status/groups requests:
1. Check `wa:endpoint:{account_id}` in Redis
2. If no endpoint → trigger Container Manager to start container, wait
3. Proxy HTTP request to container endpoint

### 6. Retry Logic (inside wa-worker)

- Max 3 retries per task
- Backoff: 60s, 180s, 300s
- `no_retry` errors (403 Forbidden): report failure immediately
- Rate limit errors (429): respect retry_after

## What Gets Removed

- `celery-worker-whatsapp` service (entire Celery worker)
- `send_whatsapp_message` Celery task
- Single `wa-bridge` container
- HTTP POST `/api/sessions/:id/send` endpoint (replaced by Redis queue)

## What Stays Unchanged

- Telegram logic (celery-worker-telegram, send_telegram_message)
- Schedule model, schedule_service, compute_next_run_at
- SendLog model
- Web UI for account management
- S3 image storage

## Redis Keys

| Key | Type | Purpose |
|-----|------|---------|
| `wa:queue:{account_id}` | List | Task queue per account |
| `wa:active_accounts` | Set | Accounts with pending work |
| `wa:results` | List | Send results for processing |
| `wa:endpoint:{account_id}` | String | HTTP endpoint of running container |
| `wa:heartbeat:{account_id}` | String | Last activity timestamp |

## Docker Configuration

```yaml
# wa-worker containers created dynamically, NOT in compose
# Container Manager needs Docker socket access:
celery-worker-default:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - wa_sessions:/app/sessions  # for session path reference
```

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Docker socket security | Limit to container management operations only |
| Cold start delay (5-15s) | Container Manager can pre-start before scheduled time |
| Zombie containers | Beat task cleanup + Docker labels for identification |
| 50+ accounts = ~12GB RAM | mem_limit=256m per container + monitoring alerts |
| Container Manager failure | Watchdog + existing containers continue working |

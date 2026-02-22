# Scaling Design: Distributed Queue Architecture

**Date:** 2026-02-22
**Approach:** B — Distributed Celery Queue with session affinity
**Infrastructure:** Single VPS, Docker Compose
**Target:** 200+ users, 100+ ads each, simultaneous hundreds of messages

## Problem

Current system runs all sends inside a single `asyncio.gather()` within one Celery task. No parallelism, no retry, no rate limiting. WhatsApp bridge is a single Node.js instance. N+1 DB queries on every schedule check.

## Architecture Overview

```
celery-beat (30s)
  └─ check_schedules
       ├─ Telegram tasks → queue "telegram"
       └─ WhatsApp tasks → queue "whatsapp.session.{id}" (per session)

celery-worker-telegram (×2, concurrency=4)
  └─ send_telegram_message (retry ×3, backoff 3/10/30s, rate_limit=20/m)

celery-worker-whatsapp (×2, concurrency=2)
  └─ send_whatsapp_message (retry ×3, backoff 3/10/30s, rate_limit=30/m)
       └─ routes to wa-bridge via session_id % N

celery-worker-default (×1)
  └─ billing checks, cleanup, etc.

wa-bridge-1 (port 3001) ─┐
wa-bridge-2 (port 3002) ─┼─ Python routing: session_id % N
wa-bridge-3 (port 3003) ─┘
```

## 1. Celery Task Architecture

### Current (broken)
- `check_schedules` fetches all due schedules
- Calls `send_ad_to_group_async()` for each via `asyncio.gather()`
- All sends run in a single process, no retry, no rate limiting

### New
- `check_schedules` only creates individual Celery tasks, no sending
- Each send = atomic Celery task with own retry policy
- Separate queues: `telegram`, `whatsapp.session.{id}`, `default`
- Billing check once per schedule check cycle, cached in Redis

### Task definitions

```python
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="20/m",
    queue="telegram",
)
def send_telegram_message(self, ad_id, group_id, account_id):
    ...

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="30/m",
)
def send_whatsapp_message(self, ad_id, group_id, session_id):
    ...
```

## 2. WhatsApp Session Affinity

### Problem
Loading a WA session = launching Chromium + restoring from MongoDB = 10-30 seconds.
Without affinity, each message could trigger a separate load cycle.

### Solution: Per-session queues
- `check_schedules` groups WA tasks by session_id
- Each group goes to queue `whatsapp.session.{session_id}`
- Worker drains one session queue before moving to the next
- Chromium stays loaded while messages are being sent

### Dispatch
```python
tasks_by_session = defaultdict(list)
for schedule in due_whatsapp_schedules:
    tasks_by_session[schedule.account_id].append(schedule)

for session_id, schedules in tasks_by_session.items():
    queue_name = f"whatsapp.session.{session_id}"
    redis.sadd("wa:active_queues", queue_name)
    for s in schedules:
        send_whatsapp_message.apply_async(
            args=[s.ad_id, s.group_ids, session_id],
            queue=queue_name,
        )
```

### Worker
Custom consumer reads `wa:active_queues` from Redis, subscribes dynamically, processes one session queue until empty.

## 3. WA-Bridge Scaling

### Python routing (no nginx)
```python
WA_BRIDGES = ["http://wa-bridge-1:3000", "http://wa-bridge-2:3000", "http://wa-bridge-3:3000"]

def get_bridge_url(session_id: int) -> str:
    return WA_BRIDGES[session_id % len(WA_BRIDGES)]
```

### Why not round-robin
Same session on different bridges = duplicate Chromium instances = memory waste + WhatsApp ban risk.

### Resource limits
Each wa-bridge: ~2 GB RAM limit, ~50 concurrent sessions.
Total: 3 bridges × 50 = ~150 concurrent WA sessions.

## 4. Database Optimization

### Indexes (Alembic migration)
- `Schedule.next_run_at` — schedule checker filter
- `Schedule.is_active` — schedule checker filter
- `SendLog.sent_at` + `SendLog.account_id` — billing counter
- `Ad.user_id`, `Group.user_id` — user isolation queries

### Eager loading
Replace N+1 pattern with joinedload:
```python
select(Schedule)
    .options(joinedload(Schedule.ad), joinedload(Schedule.account))
    .where(Schedule.is_active == True, Schedule.next_run_at <= now)
```

### Billing cache
Cache `check_limit()` result in Redis for 60 seconds per user_id.
Eliminates 3 COUNT queries per schedule per check cycle.

### Batch updates
Update `next_run_at` for all processed schedules in one `UPDATE ... WHERE id IN (...)`.

## 5. Telegram Connection Pool

### Current
`TelegramClient.connect()` on every send → 1-2 sec overhead per message.

### New
Worker-level pool: client created once, reused across sends.
```python
telegram_pool: dict[int, TelegramClient] = {}

async def get_telegram_client(account_id, ...) -> TelegramClient:
    if account_id not in telegram_pool:
        client = TelegramClient(...)
        await client.connect()
        telegram_pool[account_id] = client
    return telegram_pool[account_id]
```
Graceful disconnect on worker shutdown via signal handler.

## 6. WhatsApp httpx Pool

### Current
New `httpx.AsyncClient` per send request — no connection reuse.

### New
Single `httpx.AsyncClient` per worker with connection pooling:
```python
wa_http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=20),
    timeout=httpx.Timeout(30.0),
)
```

## 7. Docker Compose Topology

```
web (1x) ─────────── port 8000
celery-beat (1x)
celery-worker-telegram (2x) ── queue "telegram", --concurrency=4
celery-worker-whatsapp (2x) ── queue "whatsapp.*", --concurrency=2
celery-worker-default (1x) ── queue "default"
wa-bridge-1 ─── port 3001
wa-bridge-2 ─── port 3002
wa-bridge-3 ─── port 3003
flower (1x) ─── port 5555 (monitoring)
db (PostgreSQL 16)
redis (Redis 7)
mongo (MongoDB 7)
```

### Resource estimates (16 GB RAM server)
- wa-bridge × 3: ~6 GB (2 GB each, ~50 sessions)
- PostgreSQL: ~2 GB
- Celery workers (5 total): ~2 GB
- Redis + Mongo + Web + Flower: ~2 GB
- Headroom: ~4 GB

## 8. Monitoring

- **Flower**: Celery task dashboard — queues, rates, failures, retries
- **SendLog statuses**: `queued` → `sending` → `sent` / `failed` / `retrying`
- **wa-bridge healthcheck**: `/health` endpoint + docker healthcheck
- **Structured logging**: session_id, task_id, account_id in every log line

## 9. Estimated Throughput

| Component | Current | After scaling |
|---|---|---|
| Telegram | ~60 msgs/min per account | ~240 msgs/min (4 concurrent × rate limit) |
| WhatsApp | ~60 msgs/min per account (serial) | ~180 msgs/min (3 bridges × rate limit) |
| Schedule check | Every 60s, single thread, N+1 | Every 30s, optimized queries, batch dispatch |
| DB writes | ~100/s (N+1 overhead) | ~500/s (indexes + joinedload + caching) |

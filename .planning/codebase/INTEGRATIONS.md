# External Integrations

**Analysis Date:** 2026-08-03

## APIs & External Services

**Telegram:**
- Telegram user sessions send messages and synchronize groups through Telethon (`app/messengers/telegram_user.py`)
  - SDK/Client: `telethon`
  - Auth: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, per-account session credentials in database

**WhatsApp:**
- Baileys-based bridge or per-account workers expose HTTP session APIs (`app/messengers/whatsapp.py`, `wa_bridge/`, `wa_worker/`)
  - SDK/Client: `@whiskeysockets/baileys`, Express, httpx
  - Auth: worker session state persisted in Docker volumes/worker runtime; endpoints discovered via Redis

**Max messenger:**
- Max per-account workers use the same HTTP session contract (`app/messengers/max.py`, `max_worker/`)
  - SDK/Client: httpx client from Python; worker implementation in `max_worker/main.py`
  - Auth: account session state and Redis endpoint keys

**Payments:**
- YooKassa creates RUB redirect payments and receives `payment.succeeded` callbacks (`app/services/payment_service.py`, `app/routes/billing.py`)
  - SDK/Client: `yookassa`
  - Auth: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`

## Data Storage

**Databases:**
- PostgreSQL 16 - primary production relational store (`docker-compose.yml`, `app/database.py`)
  - Connection: `DATABASE_URL`
  - Client: SQLAlchemy async with `asyncpg`; migrations via Alembic
- In-memory SQLite - test-only database (`tests/conftest.py`)
  - Connection: `sqlite+aiosqlite:///:memory:`

**File Storage:**
- S3-compatible object storage for ad images (`app/services/s3.py`)
  - Connection: `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET_NAME`
  - Credentials: `S3_ACCESS_KEY`, `S3_SECRET_KEY`; public links use `S3_PUBLIC_URL`

**Caching:**
- Redis 7 - Celery broker/backend, billing cache, worker queues and endpoint registry (`app/worker/celery_app.py`, `app/services/billing_cache.py`)
  - Connection: `REDIS_URL`

## Authentication & Identity

**Auth Provider:**
- Custom application auth with bcrypt password hashes and JWT access tokens (`app/services/auth_service.py`, `app/routes/auth.py`)
  - Signing secret: `SECRET_KEY`
- Telegram login uses Telethon code/session flow (`app/pages/accounts.py`, `app/messengers/telegram_user.py`)

## Monitoring & Observability

**Error Tracking:**
- Not detected; errors are logged through structured logs

**Logs:**
- `structlog` JSON/console logging (`app/logging_config.py`), scraped from Docker by Promtail into Loki (`monitoring/`)
- Prometheus metrics instrument FastAPI and custom gauges (`app/main.py`, `app/metrics.py`)

## CI/CD & Deployment

**Hosting:**
- Docker Compose deployment; Nginx reverse proxy and optional Let’s Encrypt helper (`docker-compose.prod.yml`, `nginx/`, `init-letsencrypt.sh`)

**CI Pipeline:**
- Not detected; operational commands are provided by `justfile`

## Environment Configuration

**Required env vars:**
- `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`
- Integration credentials: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `S3_*`, `SMTP_*`, `YOOKASSA_*`
- Worker routing: `WA_BRIDGE_URLS`

**Secrets location:**
- Runtime `.env` (存在ence documented by `.env.example` and Compose `env_file`); secret values are not committed

## Webhooks & Callbacks

**Incoming:**
- YooKassa payment webhook endpoint handled by `app/routes/billing.py` and `app/services/payment_service.py`
- Internal WhatsApp/Max worker HTTP APIs are polled/called by messenger adapters

**Outgoing:**
- Application sends payment creation requests to YooKassa, SMTP messages to configured mail server, S3 `PutObject` requests, and messenger HTTP send requests

---

*Integration audit: 2026-08-03*

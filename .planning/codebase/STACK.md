# Technology Stack

**Analysis Date:** 2026-08-03

## Languages

**Primary:**
- Python 3.12+ - FastAPI application, SQLAlchemy models, repositories, services, Celery tasks (`app/`, `main.py`)

**Secondary:**
- JavaScript (ES modules, Node.js) - WhatsApp bridge and per-account worker (`wa_bridge/`, `wa_worker/`)
- YAML - Docker Compose, reverse proxy, monitoring configuration (`docker-compose.yml`, `monitoring/`, `nginx/`)

## Runtime

**Environment:**
- Python 3.12 slim container (`Dockerfile`, `.python-version`)
- Node.js containers for Baileys workers (`wa_bridge/Dockerfile`, `wa_worker/Dockerfile`)

**Package Manager:**
- uv for Python dependency resolution and execution (`pyproject.toml`, `uv.lock`)
- npm for Node workers (`wa_bridge/package.json`, `wa_worker/package.json`)
- Lockfile: `uv.lock` present; Node lockfiles not detected

## Frameworks

**Core:**
- FastAPI with Uvicorn - async HTTP API and server-rendered routes (`app/main.py`)
- SQLAlchemy asyncio - PostgreSQL ORM and async sessions (`app/database.py`)
- Jinja2 - HTML templates (`app/templates/`)
- Celery with Redis transport - scheduled and background dispatch (`app/worker/`)
- Express + Baileys - WhatsApp bridge/worker HTTP services (`wa_bridge/`, `wa_worker/`)

**Testing:**
- pytest, pytest-asyncio, pytest-cov - async API and service tests (`tests/`)

**Build/Dev:**
- Alembic - database migrations (`alembic/`)
- Docker Compose - development, production, worker, and monitoring orchestration (`docker-compose*.yml`)
- just - command runner (`justfile`)

## Key Dependencies

**Critical:**
- `asyncpg` and `sqlalchemy[asyncio]` - production PostgreSQL connectivity
- `celery[redis]` and Redis client - task queues, broker/backend, caching
- `telethon` - Telegram user-account messaging
- `yookassa` - Russian payment processing
- `aiobotocore` - asynchronous S3-compatible object uploads
- `aiosmtplib` - verification and password-reset mail

**Infrastructure:**
- `docker` - starts/stops isolated WhatsApp and Max worker containers
- `prometheus-fastapi-instrumentator` and `prometheus-client` - metrics
- `structlog` - structured application logging
- `python-jose`, `passlib[bcrypt]` - JWT and password hashing
- `httpx` - internal bridge and worker HTTP clients

## Configuration

**Environment:**
- Pydantic Settings loads `.env` through `app/config.py`; `.env.example` documents expected variables
- Required secrets include `DATABASE_URL` and `SECRET_KEY`; integrations use `TELEGRAM_*`, `S3_*`, `SMTP_*`, `YOOKASSA_*`, and `WA_BRIDGE_URLS`

**Build:**
- Python image installs frozen dependencies from `pyproject.toml`/`uv.lock` (`Dockerfile`)
- Compose files inject environment and mount Docker socket for dynamic workers (`docker-compose.yml`)
- Nginx templates provide HTTP/HTTPS reverse proxy (`nginx/`)

## Platform Requirements

**Development:**
- Python 3.12, uv, PostgreSQL 16, Redis 7, Docker (for messenger workers), and just

**Production:**
- Docker Compose deployment with web, Celery beat/workers, PostgreSQL, Redis, Nginx, and optional monitoring stack

---

*Stack analysis: 2026-08-03*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Broadcaster is a SaaS platform for scheduling and sending product ads to messenger groups (Telegram, WhatsApp). Built with Python 3.12, managed with [uv](https://docs.astral.sh/uv/).

**Stack:** FastAPI + SQLAlchemy async (PostgreSQL) + Celery/Redis + Jinja2 templates.

## Commands

Project uses [just](https://github.com/casey/just) as a command runner. Run `just` to see all available recipes.

### Local development
- **Run**: `just run` (`uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload`)
- **Test**: `just test` (`uv run pytest tests/ -v`)
- **Test with coverage**: `just test-cov`
- **Sync environment**: `just sync` (`uv sync`)
- **Add dependency**: `just add <package>`
- **Celery worker**: `just worker`
- **Celery beat**: `just beat`
- **Celery worker+beat**: `just celery`
- **Alembic migration**: `just migrate "description"`
- **Alembic upgrade**: `just upgrade`

### WA Worker
- **Build image**: `just wa-worker-build`
- **List workers**: `just wa-workers`
- **Stop all workers**: `just wa-workers-stop`

### Docker
- **Docker dev**: `just dev`
- **Docker stop**: `just down`
- **Prod start**: `just prod-start`
- **Prod stop**: `just prod-stop`
- **Prod restart**: `just prod-restart` / `just prod-hard-restart`
- **Prod deploy**: `just prod-deploy` (build + deploy) / `just prod-hard-deploy` (--no-cache)
- **Prod build**: `just prod-build`
- **Prod logs**: `just prod-logs [service]`
- **Prod cleanup schedules**: `just prod-cleanup-schedules [args]`

### Monitoring
- **Start**: `just monitoring-start`
- **Stop**: `just monitoring-down`
- **Restart**: `just monitoring-restart`
- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3000 (admin/admin)
- **Loki API**: http://localhost:3100/ready
- **Grafana Explore**: Loki datasource → `{container_name=~".*broadcaster.*"}`

## Architecture

- `app/routes/` -- FastAPI API routers (auth, ads, accounts, groups, schedules, history, billing, uploads)
- `app/pages/` -- Server-rendered HTML pages (auth, dashboard, ads, accounts, groups, schedules, history, billing, admin, profile)
- `app/models/` -- SQLAlchemy ORM models (User, Ad, Group, MessengerAccount, Schedule, SendLog, Subscription, TelegramAuthSession)
- `app/repositories/` -- Data access layer: generic `BaseRepository[T]` + domain repositories
- `app/services/` -- Business logic (auth, billing, billing_cache, schedule, messenger_factory, s3, wa_container_manager)
- `app/messengers/` -- Messenger adapters (Telegram userbot via Telethon, Telegram pool, WhatsApp via dynamic wa-worker containers)
- `app/worker/` -- Celery app and async tasks (schedule checker, send dispatcher, WA container manager, WA result processor)
- `app/application/` -- DDD use cases (accounts, scheduling)
- `app/domain/` -- Domain repository interfaces
- `app/infrastructure/` -- Unit of Work implementation
- `app/templates/` -- Jinja2 HTML templates (21 files across 8 subdirectories)
- `wa_bridge/` -- WhatsApp bridge: Node.js + Express + Baileys (legacy, used for reference)
- `wa_worker/` -- Per-account WhatsApp worker: Node.js + Baileys + Redis queue consumer (one container per account)
- `monitoring/` -- Prometheus, Loki, Promtail, Grafana configs and dashboards
- `nginx/` -- Nginx reverse proxy configs (HTTP and HTTPS templates)
- `scripts/` -- Maintenance scripts (cleanup_schedules)
- `tests/` -- pytest suite (52 files) with asyncio, in-memory SQLite, httpx AsyncClient

## Testing

Tests use `sqlite+aiosqlite:///:memory:` with full schema creation per test. Fixtures in `tests/conftest.py` provide `client`, `db_session`, `auth_headers`. Run all tests with `uv run pytest tests/ -v`.

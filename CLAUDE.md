# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Broadcaster is a SaaS platform for scheduling and sending product ads to messenger groups (Telegram, WhatsApp). Built with Python 3.12, managed with [uv](https://docs.astral.sh/uv/).

**Stack:** FastAPI + SQLAlchemy async (PostgreSQL) + Celery/Redis + Jinja2 templates.

## Commands

- **Run**: `uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- **Test**: `uv run pytest tests/ -v`
- **Test with coverage**: `uv run pytest tests/ --cov=app --cov-report=term-missing`
- **Docker dev**: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`
- **Docker prod**: `docker compose up -d`
- **Alembic migration**: `uv run alembic revision --autogenerate -m "description"`
- **Alembic upgrade**: `uv run alembic upgrade head`
- **Celery worker**: `uv run celery -A app.worker.celery_app worker --loglevel=info`
- **Celery beat**: `uv run celery -A app.worker.celery_app beat --loglevel=info`
- **Add dependency**: `uv add <package>`
- **Sync environment**: `uv sync`
- **Monitoring stack**: `docker compose -f docker-compose.monitoring.yml up -d`
- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3001 (admin/admin)

## Architecture

- `app/routes/` -- FastAPI routers (auth, ads, accounts, groups, schedules, history, billing, uploads, pages)
- `app/models/` -- SQLAlchemy ORM models (User, Ad, Group, MessengerAccount, Schedule, SendLog, Subscription)
- `app/services/` -- Business logic (auth, billing limits, schedule computation)
- `app/messengers/` -- Messenger adapters (Telegram bot, Telegram userbot, WhatsApp bridge)
- `app/worker/` -- Celery app and async tasks (schedule checker, send dispatcher)
- `tests/` -- pytest suite with asyncio, in-memory SQLite, httpx AsyncClient

## Testing

Tests use `sqlite+aiosqlite:///:memory:` with full schema creation per test. Fixtures in `tests/conftest.py` provide `client`, `db_session`, `auth_headers`. Run all tests with `uv run pytest tests/ -v`.

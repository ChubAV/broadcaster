# Broadcaster

A SaaS platform for scheduling and sending product advertisements to messenger groups. Supports Telegram bots, Telegram userbots, and WhatsApp via a bridge service.

## Features

- **Multi-messenger support** -- Telegram Bot API, Telegram userbot (Pyrogram), and WhatsApp (via whatsapp-web.js bridge)
- **Ad management** -- Create, edit, and organize product ads with images
- **Group management** -- Connect and manage messenger groups per account
- **Schedule engine** -- Flexible scheduling by day of week and time of day with automatic next-run computation
- **Automated sending** -- Celery Beat triggers schedule checks; Celery workers dispatch messages
- **Send history and stats** -- Full send log with per-user statistics
- **Billing and plan limits** -- Free, Basic, and Pro plans with configurable limits on ads, groups, and daily sends
- **JWT authentication** -- Secure user registration and login
- **Web UI** -- Server-rendered pages using Jinja2 templates

## Tech Stack

- **Python 3.12** with [uv](https://docs.astral.sh/uv/) for dependency management
- **FastAPI** -- async web framework
- **SQLAlchemy 2.0** (async) -- ORM with PostgreSQL (asyncpg)
- **Alembic** -- database migrations
- **Celery + Redis** -- task queue for scheduled sends
- **Jinja2** -- server-side HTML templates
- **Docker Compose** -- full-stack orchestration
- **WhatsApp Bridge** -- Node.js service using whatsapp-web.js

## Quick Start (Docker Compose)

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd broadcaster
   ```

2. Create a `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://broadcaster:broadcaster@db:5432/broadcaster
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=change-me-to-a-random-string
   ```

3. Start all services:
   ```bash
   docker compose up -d
   ```

4. Run database migrations:
   ```bash
   docker compose exec web uv run alembic upgrade head
   ```

5. Open http://localhost:8000 in your browser.

### Development Mode

Use the dev override for hot-reload and debug logging:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Development Setup (Local)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up PostgreSQL and Redis (or use Docker for just these services):
   ```bash
   docker compose up db redis -d
   ```

4. Create a `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://broadcaster:broadcaster@localhost:5432/broadcaster
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=dev-secret-key
   ```

5. Run migrations:
   ```bash
   uv run alembic upgrade head
   ```

6. Start the application:
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. In separate terminals, start the Celery worker and beat:
   ```bash
   uv run celery -A app.worker.celery_app worker --loglevel=info
   uv run celery -A app.worker.celery_app beat --loglevel=info
   ```

8. Run tests:
   ```bash
   uv run pytest tests/ -v
   ```

## Project Structure

```
broadcaster/
├── app/
│   ├── config.py              # Pydantic settings
│   ├── database.py            # SQLAlchemy engine and session
│   ├── dependencies.py        # FastAPI dependencies (auth, db)
│   ├── main.py                # App factory
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── ad.py
│   │   ├── group.py
│   │   ├── messenger_account.py
│   │   ├── schedule.py
│   │   ├── send_log.py
│   │   └── subscription.py
│   ├── routes/                # FastAPI routers
│   │   ├── auth.py            # Registration and login
│   │   ├── ads.py             # Ad CRUD
│   │   ├── accounts.py        # Messenger account management
│   │   ├── groups.py          # Group CRUD
│   │   ├── schedules.py       # Schedule CRUD
│   │   ├── history.py         # Send logs and stats
│   │   ├── billing.py         # Plans and subscriptions
│   │   ├── uploads.py         # Image uploads
│   │   └── pages.py           # Server-rendered HTML pages
│   ├── services/
│   │   ├── auth_service.py    # Password hashing, JWT
│   │   ├── billing_service.py # Plan limits and usage checks
│   │   └── schedule_service.py # Next-run computation
│   ├── messengers/            # Messenger adapters
│   │   ├── base.py            # Abstract base class
│   │   ├── telegram_bot.py    # Telegram Bot API (aiogram)
│   │   ├── telegram_user.py   # Telegram userbot (Pyrogram)
│   │   └── whatsapp.py        # WhatsApp via bridge
│   └── worker/
│       ├── celery_app.py      # Celery configuration
│       └── tasks.py           # Schedule checker and send tasks
├── wa_bridge/                 # WhatsApp bridge (Node.js)
├── tests/                     # pytest test suite
├── docker-compose.yml         # Production stack
├── docker-compose.dev.yml     # Dev overrides (hot-reload)
├── Dockerfile                 # Python app image
└── pyproject.toml             # Project metadata and dependencies
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET/POST | `/api/ads` | List or create ads |
| GET/PUT/DELETE | `/api/ads/{id}` | Get, update, or delete an ad |
| GET/POST | `/api/accounts` | List or create messenger accounts |
| DELETE | `/api/accounts/{id}` | Delete a messenger account |
| GET | `/api/accounts/{id}/status` | Check account connection status |
| GET/POST | `/api/groups` | List or create groups |
| DELETE | `/api/groups/{id}` | Delete a group |
| PATCH | `/api/groups/{id}/toggle` | Toggle group active status |
| GET/POST | `/api/schedules` | List or create schedules |
| PUT/DELETE | `/api/schedules/{id}` | Update or delete a schedule |
| POST | `/api/schedules/{id}/toggle` | Toggle schedule active status |
| GET | `/api/history` | List send history |
| GET | `/api/history/stats` | Get send statistics |
| GET | `/api/billing/plans` | List available plans |
| GET | `/api/billing/usage` | Get current usage and limits |
| POST | `/api/uploads/image` | Upload an ad image |
| GET | `/health` | Health check |

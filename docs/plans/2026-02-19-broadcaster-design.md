# Broadcaster - Design Document

## Overview

Broadcaster is a SaaS product for small businesses/sole proprietors to schedule and send product advertisements to messenger groups (Telegram, WhatsApp).

## Requirements

- **Target audience**: Small business, sole proprietors (sellers)
- **Messengers**: Telegram (bot + userbot) and WhatsApp (via whatsapp-web.js unofficial)
- **Content**: Text + photos
- **Schedule**: Specific days of week + times of day
- **Monetization**: Subscription (SaaS) with tiered plans
- **Accounts**: One TG account + one WA account per user

## Architecture

Modular monolith (FastAPI) with a separate Node.js WhatsApp bridge.

```
Docker Compose
├── PostgreSQL (data storage)
├── Redis (Celery task queue + cache)
├── Python Monolith (FastAPI)
│   ├── Web API + UI (Jinja2 + HTMX + TailwindCSS)
│   ├── Scheduler (Celery Beat)
│   └── Workers (Celery)
└── WA Bridge (Node.js, whatsapp-web.js + Express)
```

## Data Models

### User
- id, email, password_hash, name, timezone, created_at

### Subscription
- id, user_id (FK), plan (free/basic/pro), expires_at, is_active

### MessengerAccount
- id, user_id (FK), type (tg_bot/tg_user/wa), credentials (encrypted), status (active/disconnected), session_data (encrypted)

### Ad (Advertisement)
- id, user_id (FK), title, text, images[], is_active, created_at

### Group
- id, user_id (FK), account_id (FK), messenger_type, group_external_id, name, is_active

### Schedule
- id, ad_id (FK), group_ids[] (FK), days_of_week[], times_of_day[], account_id (FK), is_active, next_run_at

### SendLog
- id, schedule_id (FK), ad_id (FK), group_id (FK), status (ok/fail), error_message, sent_at

## Web UI Screens

1. **Registration / Login** - email + password, JWT auth
2. **Dashboard** - overview: active ads count, next send time, account statuses, recent sends
3. **Ads** - list, create/edit (text + photo upload), preview
4. **Messenger Accounts** - connect TG bot (token), TG userbot (phone + code), WA (QR code scan), connection status
5. **Groups** - list available groups from connected accounts, select for broadcasting
6. **Schedules** - bind ad to groups + select days and times
7. **Send History** - send log with statuses (success/error)
8. **Subscription** - current plan, limits, payment

## Message Sending Flow

1. Celery Beat checks Schedule table every minute (WHERE is_active AND next_run_at <= now())
2. Creates Celery task `send_ad_to_group` for each group in matching schedules
3. Checks subscription limits before creating tasks
4. Celery Worker executes:
   - TG Bot: aiogram `bot.send_message()`
   - TG User: Pyrogram `client.send_message()`
   - WA: HTTP POST to WA Bridge `/api/send`
5. Records result in SendLog
6. Updates `next_run_at` in Schedule

## Error Handling

- Account disconnected: skip, log as `account_disconnected`
- Messenger error (rate limit, banned): retry with exponential backoff (up to 3 attempts)
- WA Bridge unavailable: task returns to queue

## Project Structure

```
broadcaster/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── alembic.ini
├── alembic/versions/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py             # pydantic-settings
│   ├── database.py           # SQLAlchemy async engine/session
│   ├── models/               # SQLAlchemy models
│   ├── routes/               # FastAPI routes
│   ├── services/             # Business logic
│   ├── messengers/           # Messenger adapters (base, tg_bot, tg_user, wa)
│   ├── worker/               # Celery app, tasks, beat schedule
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS, JS, images
├── wa_bridge/                # Node.js WhatsApp Bridge
│   ├── Dockerfile
│   ├── package.json
│   └── index.js
└── tests/
```

## Tech Stack

**Python:**
- fastapi, uvicorn - web server
- sqlalchemy[asyncio], asyncpg - ORM + PostgreSQL
- alembic - migrations
- celery[redis] - task queue
- pyrogram, tgcrypto - Telegram userbot
- aiogram - Telegram bot
- jinja2 - templates
- pydantic-settings - configuration
- python-jose, passlib[bcrypt] - JWT, password hashing
- httpx - HTTP client for WA Bridge
- pillow - image processing

**Node.js (WA Bridge):**
- express - REST API
- whatsapp-web.js - WhatsApp Web client

**Infrastructure:**
- PostgreSQL - primary data store
- Redis - Celery broker + cache
- Docker Compose - deployment

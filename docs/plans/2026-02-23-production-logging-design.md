# Production Logging Improvement Design

**Date:** 2026-02-23
**Goal:** Improve logging to catch messenger errors (Telegram/WhatsApp) in production

## Current State

- `logging.basicConfig(level=logging.INFO)` in `main.py` — default format, no structure
- WhatsApp module has NO logger — all errors silently swallowed
- Telegram silent `try/except` in `get_groups()`, `check_connection()`
- No logging in FastAPI exception handlers
- No request tracing (no request_id)
- No structured logging (JSON)
- No Celery `on_failure` callback — final retry failures invisible
- Worker `create_messenger()` ValueError uncaught

## Design

### 1. Structured Logging with structlog

**New file:** `app/logging_config.py`
- `structlog` for structured logging with JSON output in production, console renderer in dev
- `LOG_LEVEL` environment variable (default: `INFO`)
- `LOG_FORMAT` env var: `json` (default) or `console`
- Configure stdlib logging integration for uvicorn/celery compatibility
- Add `LOG_LEVEL` to `app/config.py` Settings

**Dependencies:** `structlog`

### 2. Messenger Logging

**`app/messengers/whatsapp.py`:**
- Add `logger = structlog.get_logger(__name__)`
- `send_message()` — log attempt (DEBUG), HTTP response (DEBUG), errors with `account_id`, `group_jid`, HTTP status/body (ERROR)
- `get_groups()` — log error with `account_id` (ERROR)
- `check_connection()`, `start_session()`, `destroy_session()`, `get_qr()` — log errors with `session_id` (WARNING/ERROR)

**`app/messengers/telegram_user.py`:**
- Replace `logging.getLogger` with `structlog.get_logger`
- `send_message()` — add context: `account_id`, `group_id` in errors (ERROR)
- `get_groups()` — log error instead of silent return (ERROR)
- `check_connection()` — log disconnect reason (WARNING)

**`app/messengers/telegram_pool.py`:**
- Replace `logging.getLogger` with `structlog.get_logger`
- `get()` — wrap `_create_client()` in try/except, log connection error (ERROR)

### 3. Worker & Celery Logging

**`app/worker/tasks.py`:**
- `_send_message()` — log send start (INFO), result (INFO/ERROR) with context: `schedule_id`, `ad_id`, `group_id`, `account_id`, `messenger_type`
- `send_telegram_message()` / `send_whatsapp_message()` — add `on_failure` callback: log final error after all retries exhausted (ERROR with exc_info)
- `check_schedules_async()` — wrap in try/except, log DB errors (ERROR)
- Catch `create_messenger()` ValueError (ERROR)

**`app/worker/wa_consumer.py`:**
- `_get_redis()` — log connection error (ERROR)
- `register_wa_queue()` / `unregister_wa_queue()` — log instead of `pass` (WARNING)

### 4. FastAPI Middleware & Exception Handlers

**New file:** `app/middleware.py`
- Request ID middleware: generate UUID per request, bind to structlog context
- Add `X-Request-ID` response header
- Measure request duration, log as INFO with `duration_ms`

**`app/main.py` exception handlers:**
- Add logging in each handler (`logger.warning()` for 4xx, `logger.error()` for 5xx)
- Add generic `Exception` handler — catch unhandled 500s, log full traceback (ERROR)
- Context: `request_id`, `path`, `method`

## Files to Modify

| File | Action |
|------|--------|
| `app/logging_config.py` | Create — structlog configuration |
| `app/middleware.py` | Create — request_id + duration middleware |
| `app/config.py` | Edit — add LOG_LEVEL, LOG_FORMAT settings |
| `app/main.py` | Edit — use logging_config, add middleware, improve exception handlers |
| `app/messengers/whatsapp.py` | Edit — add logger, log all errors |
| `app/messengers/telegram_user.py` | Edit — improve error logging |
| `app/messengers/telegram_pool.py` | Edit — add error handling in get() |
| `app/worker/tasks.py` | Edit — add on_failure, improve logging |
| `app/worker/wa_consumer.py` | Edit — log instead of silent pass |
| `pyproject.toml` | Edit — add structlog dependency |

## Non-Goals

- No external monitoring (Sentry, Datadog)
- No log aggregation stack (ELK/EFK)
- No audit logging of user actions
- No changes to WA bridge (Node.js) logging

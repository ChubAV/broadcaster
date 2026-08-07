<!-- refreshed: 2026-08-03 -->
# Architecture

**Analysis Date:** 2026-08-03

## System Overview

```text
Browser/API clients -> FastAPI app (`app/main.py`)
        |-> API routers (`app/routes/`) and HTML pages (`app/pages/`)
        |-> dependencies/auth (`app/dependencies.py`)
        |-> repositories/services (`app/repositories/`, `app/services/`)
        |-> SQLAlchemy async PostgreSQL (`app/database.py`, `app/models/`)
        `-> Celery/Redis workers (`app/worker/`) -> messenger adapters (`app/messengers/`)
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Application factory | Lifespan, routers, middleware, errors, metrics | `app/main.py` |
| API routers | JSON CRUD and command endpoints | `app/routes/*.py` |
| Page routers | Server-rendered Jinja views | `app/pages/*.py` |
| Repositories | Async persistence queries and mutations | `app/repositories/` |
| Services | Auth, billing, schedules, storage, messenger orchestration | `app/services/` |
| Domain use cases | Scheduling/account workflows independent of Celery | `app/application/` |
| Messenger adapters | Telegram, WhatsApp, and MAX transport implementations | `app/messengers/` |
| Worker tasks | Periodic schedule checks and asynchronous sends | `app/worker/tasks.py` |

## Pattern Overview

**Overall:** Layered FastAPI application with repository/service modules and a small DDD-style application layer.

**Key Characteristics:**
- Async I/O throughout HTTP handlers, SQLAlchemy sessions, and background tasks.
- Routers obtain `AsyncSession` through dependency injection and usually instantiate domain repositories directly.
- Scheduling use cases isolate database/domain decisions from Celery dispatch details.

## Layers

**Presentation:** `app/routes/` exposes `/api/*`; `app/pages/` composes Jinja responses and browser flows. Depends on dependencies and repositories/services.

**Application/domain:** `app/application/accounts/`, `app/application/scheduling/`, and `app/domain/repositories.py` define use cases, DTOs, and contracts. `app/infrastructure/uow.py` supplies SQLAlchemy UoW.

**Persistence:** `app/models/` contains SQLAlchemy entities; `app/repositories/` wraps queries over `AsyncSession`; `app/database.py` builds engine/session factory.

**Infrastructure/services:** `app/services/` integrates billing, S3, email, messenger creation, and container managers. `app/messengers/` implements transport protocols.

**Background execution:** `app/worker/celery_app.py` configures Celery/Redis queues and beat schedules; `app/worker/tasks.py` performs periodic checks and dispatches Telegram, WhatsApp, and MAX work.

## Data Flow

### Primary HTTP Request Path

1. `main.py` imports `create_app` and exposes the ASGI app.
2. `app/main.py:create_app` installs middleware, metrics, exception handlers, and routers.
3. A router such as `app/routes/ads.py` resolves `get_current_user_id` and `get_db` from `app/dependencies.py`.
4. The handler calls a repository (for example `app/repositories/ad.py`) against an async SQLAlchemy session.
5. ORM entities in `app/models/` are serialized as Pydantic responses or rendered by `app/templates/`.

### Scheduled Send Flow

1. Celery beat invokes `check_schedules` in `app/worker/tasks.py`.
2. `collect_due_schedules` in `app/application/scheduling/use_cases.py` loads due schedules and advances `next_run_at`.
3. `dispatch_send_tasks` routes Telegram to Celery and WhatsApp/MAX payloads to Redis per-account queues.
4. Send workers call `send_message_once`, create a messenger through `app/services/messenger_factory.py`, and persist `SendLog` records.

**State Management:** PostgreSQL is authoritative for users, ads, groups, accounts, schedules, billing, and send logs. Redis carries Celery and per-account worker queues; process state includes app lifespan UoW factory and messenger/container caches.

## Key Abstractions

**BaseRepository[T]:** Generic CRUD/query behavior in `app/repositories/base.py`; domain repositories specialize it per model.

**Unit of Work:** `app/application/unit_of_work.py` defines the contract and `app/infrastructure/uow.py` commits/rolls back an `AsyncSession` context.

**Messenger interface:** `app/messengers/base.py` is implemented by `telegram_user.py`, `whatsapp.py`, and `max.py`; `app/services/messenger_factory.py` selects by account type.

## Entry Points

**ASGI:** `main.py` (`app = create_app()`) is the web deployment entry point.

**Celery:** `app/worker/celery_app.py` exports `celery`; beat schedules tasks from `app/worker/tasks.py`.

**Container workers:** `wa_worker/index.js` and `max_worker/main.py` consume account-specific queues; `wa_bridge/index.js` is a legacy bridge.

## Architectural Constraints

- **Async model:** FastAPI and SQLAlchemy use asyncio; Celery sync task wrappers bridge into async with `asyncio.run`.
- **Global state:** `app/dependencies.py` stores a module-level session factory initialized during lifespan; Celery creates engines per task.
- **Transactions:** Repository methods commit immediately, while application use cases may commit batches and UoW provides explicit transaction boundaries.
- **External delivery:** Messenger credentials and transport availability are runtime concerns; adapters must preserve `BaseMessenger` behavior.

## Anti-Patterns

### Direct ORM access in presentation
**What happens:** Handlers can bypass repositories and query models directly (notably `app/dependencies.py`).
**Why it's wrong:** Persistence policy becomes scattered.
**Do this instead:** Put reusable queries in `app/repositories/` and keep routers thin.

### Mixing dispatch with domain decisions
**What happens:** Queue-specific logic belongs in `app/worker/tasks.py`.
**Why it's wrong:** It makes scheduling logic hard to test outside Celery.
**Do this instead:** Keep selection/state transitions in `app/application/scheduling/use_cases.py`.

## Error Handling

**Strategy:** Domain exceptions are translated centrally in `app/main.py`; handlers also use FastAPI `HTTPException` for validation/auth/resource failures. Unexpected exceptions return a generic 500 and are logged with structlog.

## Cross-Cutting Concerns

**Logging:** `app/logging_config.py` and structlog; request IDs via `app/middleware.py`.
**Validation:** Pydantic request/response models in route modules.
**Authentication:** JWT from Bearer headers or `access_token` cookies via `app/dependencies.py`.

---

*Architecture analysis: 2026-08-03*

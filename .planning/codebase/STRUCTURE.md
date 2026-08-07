# Codebase Structure

**Analysis Date:** 2026-08-03

## Directory Layout

```text
broadcaster/
├── app/                 # Python web application and domain layers
│   ├── routes/           # JSON API routers
│   ├── pages/            # HTML page routers
│   ├── models/           # SQLAlchemy ORM models
│   ├── repositories/     # Persistence query objects
│   ├── services/         # Business/integration services
│   ├── application/      # Use cases and UoW contracts
│   ├── domain/           # Domain interfaces
│   ├── infrastructure/   # Concrete adapters
│   ├── messengers/       # Telegram/WhatsApp/MAX adapters
│   ├── worker/           # Celery app and tasks
│   └── templates/        # Jinja2 views
├── tests/                # pytest suites and fixtures
├── alembic/              # Database migrations
├── wa_worker/            # Per-account WhatsApp Node worker
├── wa_bridge/            # Legacy WhatsApp bridge
├── max_worker/           # MAX worker container
├── monitoring/           # Prometheus/Loki/Grafana configuration
├── nginx/                # Reverse proxy templates
└── scripts/              # Maintenance utilities
```

## Directory Purposes

**`app/routes/`:** API modules (`auth.py`, `ads.py`, `accounts.py`, `groups.py`, `schedules.py`, `history.py`, `billing.py`, `uploads.py`) define request schemas and route handlers.

**`app/pages/`:** Browser-facing routers mirror product areas and render templates through `app/pages/common.py`.

**`app/templates/`:** `base.html`, top-level dashboard/profile views, and feature subdirectories (`ads/`, `accounts/`, `groups/`, `schedules/`, `billing/`, `auth/`, `admin/`, `history/`, `includes/`).

**`app/models/`:** One model module per persistent entity, including `user.py`, `ad.py`, `group.py`, `schedule.py`, `messenger_account.py`, subscription/payment and logging models.

**`app/repositories/`:** `base.py` provides generic operations; feature repositories (`ad.py`, `group.py`, `schedule.py`, `account.py`, `user.py`, `send_log.py`) add domain queries.

**`app/services/`:** Cross-cutting business logic such as `auth_service.py`, `billing_service.py`, `schedule_service.py`, `email_service.py`, `s3.py`, and messenger/container managers.

**`app/application/`:** Use-case code and DTOs. Scheduling dispatch logic is in `app/application/scheduling/use_cases.py`; account workflows are in `app/application/accounts/`.

**`tests/`:** pytest files are grouped by feature (routes, services, repositories, workers, application); shared async fixtures live in `tests/conftest.py`.

## Key File Locations

**Entry Points:** `main.py` (Uvicorn/ASGI), `app/main.py` (factory/lifespan), `app/worker/celery_app.py` (Celery).

**Configuration:** `app/config.py`, `pyproject.toml`, `justfile`, `alembic.ini`, and Docker compose files. `.env.example` documents environment names; do not commit secret values.

**Core Logic:** `app/application/scheduling/use_cases.py`, `app/services/schedule_service.py`, and `app/services/messenger_factory.py`.

**Testing:** `tests/conftest.py` plus feature test modules under `tests/`.

**Database:** `app/database.py` and migration revisions under `alembic/versions/`.

## Naming Conventions

**Files:** Lowercase snake_case Python modules (`app/routes/send_logs.py` style); JavaScript workers use `index.js`.

**Directories:** Lowercase snake_case for Python packages; template folders use lowercase feature names.

**Symbols:** Classes are PascalCase (`AdRepository`, `SqlAlchemyUnitOfWork`); functions, route handlers, and variables are snake_case; constants are uppercase in `app/constants.py`.

## Where to Add New Code

**New API feature:** Add a router module under `app/routes/`, register it in `app/main.py`, add a repository under `app/repositories/`, and place ORM entities in `app/models/`.

**New browser page:** Add a router under `app/pages/`, include it in `app/pages/__init__.py`, and add templates beneath `app/templates/<feature>/`.

**New business workflow:** Prefer a use case under `app/application/<area>/`; define DTOs alongside it and inject `SupportsUnitOfWorkFactory` where transactional boundaries matter.

**New integration:** Put provider/client code in `app/services/` or a dedicated adapter in `app/messengers/`; keep credentials in settings and expose a factory when selecting implementations.

**New background job:** Define Celery tasks in `app/worker/tasks.py`, register periodic execution in `app/worker/celery_app.py`, and add integration tests under `tests/`.

## Special Directories

**`alembic/`:** Versioned schema migrations; generated migration files are committed and applied with `just upgrade`.

**`monitoring/`:** Deployment configuration for metrics/log aggregation, not application runtime code.

**`wa_worker/`, `wa_bridge/`, `max_worker/`:** Separate worker images with independent package manifests and Dockerfiles.

**`.planning/`:** GSD planning artifacts and generated codebase maps; committed as project documentation.

---

*Structure analysis: 2026-08-03*

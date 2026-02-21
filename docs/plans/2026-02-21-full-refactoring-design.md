# Full Project Refactoring — Design Document

**Date:** 2026-02-21
**Approach:** Layer-by-layer (bottom-up), tests green at every step

## Problem Statement

The codebase has grown organically and accumulated:
- `pages.py` — 1,219 LOC god file mixing 8 feature domains
- 27+ duplicated SQL query patterns across routes
- 48+ manual `user_id ==` ownership checks
- 31 repetitions of `get_user_from_cookie()` in pages.py
- 5+ places recreating messenger instances manually
- Inconsistent error handling (mixed status code styles, silent exceptions)
- `Settings()` instantiated 20+ times (creates new instance each call)
- No repository/DAO layer — queries scattered across routes

## Target Architecture

```
app/
├── config.py              # Settings singleton via lru_cache
├── database.py            # Engine + session factory
├── dependencies.py        # get_db, get_current_user, get_settings
├── exceptions.py          # Custom exceptions + global handlers
├── main.py                # Lifespan + app creation
│
├── repositories/          # Data access layer
│   ├── base.py            # BaseRepository[T] — generic CRUD
│   ├── user.py            # UserRepository
│   ├── ad.py              # AdRepository
│   ├── group.py           # GroupRepository
│   ├── account.py         # MessengerAccountRepository
│   ├── schedule.py        # ScheduleRepository
│   └── send_log.py        # SendLogRepository
│
├── services/              # Business logic
│   ├── auth_service.py    # Existing (API unchanged)
│   ├── billing_service.py # Existing (plan constants refactored)
│   ├── schedule_service.py# Existing
│   ├── authorization.py   # Resource ownership checks
│   └── messenger_factory.py # Messenger instance creation
│
├── models/                # SQLAlchemy models (unchanged)
├── messengers/            # Messenger adapters (unchanged)
├── worker/                # Celery tasks (minimal changes)
│
├── routes/                # API routers (use repositories/services)
│   ├── auth.py, ads.py, accounts.py, groups.py
│   ├── schedules.py, history.py, billing.py, uploads.py
│
└── pages/                 # HTML pages (split from pages.py)
    ├── __init__.py        # Aggregates all sub-routers
    ├── common.py          # get_user_from_cookie as dependency
    ├── auth.py            # Login/register pages (~60 LOC)
    ├── dashboard.py       # Dashboard (~80 LOC)
    ├── ads.py             # Ad CRUD pages (~120 LOC)
    ├── accounts.py        # Account connection (~300 LOC)
    ├── groups.py          # Group management (~85 LOC)
    ├── schedules.py       # Schedule pages (~200 LOC)
    ├── history.py         # Send history (~60 LOC)
    └── billing.py         # Billing page (~40 LOC)
```

## Design Details

### 1. Repository Layer (`app/repositories/`)

Generic base with typed CRUD operations:

```python
class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None
    async def get_by_id_and_user(self, id: int, user_id: int) -> T | None
    async def list_by_user(self, user_id: int) -> list[T]
    async def create(self, **kwargs) -> T
    async def update(self, entity: T, **kwargs) -> T
    async def delete(self, entity: T) -> None
    async def count_by_user(self, user_id: int) -> int
```

Specific repositories add domain queries:
- `AdRepository` — `get_with_images(id, user_id)`
- `ScheduleRepository` — `get_pending_schedules()`, `get_with_relations(id, user_id)`
- `SendLogRepository` — `get_history_page(user_id, offset, limit, status_filter)`, `get_stats(user_id)`

### 2. Authorization Service (`app/services/authorization.py`)

Centralizes resource ownership and billing limit checks:

```python
class AuthorizationService:
    async def get_owned_or_404(self, repo: BaseRepository, id: int, user_id: int) -> T:
        """Get resource or raise NotFoundError if missing/not owned."""

    async def check_billing_limit(self, user: User, resource: str, db: AsyncSession):
        """Raise BillingLimitError if plan limit exceeded."""
```

Replaces 48+ manual ownership checks.

### 3. Custom Exceptions (`app/exceptions.py`)

```python
class AppError(Exception):
    """Base application error."""

class NotFoundError(AppError):
    """Resource not found or not accessible."""

class ForbiddenError(AppError):
    """Action not permitted."""

class BillingLimitError(AppError):
    """Plan limit exceeded."""

class MessengerConnectionError(AppError):
    """Messenger connection failed."""
```

Global exception handlers in `main.py`:
- `NotFoundError` → 404
- `ForbiddenError` → 403
- `BillingLimitError` → 403 with limit info
- `MessengerConnectionError` → 502

### 4. Messenger Factory (`app/services/messenger_factory.py`)

Single place for creating messenger instances:

```python
def create_messenger(account: MessengerAccount, settings: Settings) -> BaseMessenger:
    """Create appropriate messenger based on account type."""
```

Replaces 5+ manual instantiation sites in routes and worker.

### 5. Settings Singleton

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Replaces 20+ `Settings()` instantiations throughout the codebase.

### 6. Split pages.py

`get_user_from_cookie()` becomes a FastAPI dependency in `pages/common.py` — eliminates 31 repetitions. Each page module gets its own `APIRouter` with prefix and tags.

### 7. Consistent Error Handling

All error responses use `status.HTTP_4XX_*` constants (not bare integers). Silent `except: pass` blocks replaced with logging.

## Refactoring Phases

### Phase 1: Infrastructure
- Settings singleton (`lru_cache`)
- Custom exceptions + global handlers
- Structured logging setup

### Phase 2: Repository Layer
- `BaseRepository[T]` with generic CRUD
- Concrete repositories for each model
- Migrate existing queries from routes

### Phase 3: Services
- Authorization service
- Messenger factory
- Refactor billing_service to use repository

### Phase 4: Route Refactoring
- API routes use repositories + services
- Split pages.py → `app/pages/` package
- `get_user_from_cookie` as dependency

### Phase 5: Cleanup
- Remove dead code and duplicate imports
- Consistent status code style
- Update all tests

## Constraints

- Tests must pass after each phase
- No public API changes (routes, response shapes)
- No database schema changes
- No new dependencies added

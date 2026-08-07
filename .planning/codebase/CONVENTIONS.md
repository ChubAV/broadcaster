# Coding Conventions

**Analysis Date:** 2026-08-03

## Naming Patterns

**Files:**
- Python modules use lowercase snake_case, grouped by layer (`app/services/auth_service.py`, `app/routes/auth.py`).
- Tests mirror production areas and use `test_*.py` (`tests/test_services/test_auth_service.py`).

**Functions:**
- Functions and async handlers use snake_case; private helpers are prefixed with `_` (`app/services/billing_cache.py`).
- FastAPI route functions are named after the operation (`register`, `login` in `app/routes/auth.py`).

**Variables:**
- Local variables and parameters use snake_case (`session_factory`, `test_settings`).
- Constants are uppercase where module-wide (`app/constants.py`); module singletons use descriptive lowercase names.

**Types:**
- Classes use PascalCase (`User`, `BaseRepository`, request/response models).
- SQLAlchemy models use typed `Mapped[...]` attributes (`app/models/user.py`).

## Code Style

**Formatting:**
- Code follows standard 4-space Python indentation and PEP 8 spacing.
- No repository formatter configuration was detected; preserve existing wrapping and trailing commas in multiline calls.

**Linting:**
- No dedicated Ruff/Flake8 configuration was detected. Keep imports explicit and remove unused imports.

## Import Organization

**Order:**
1. Python standard library (`datetime`, `typing`, `json`)
2. Third-party packages (`fastapi`, `sqlalchemy`, `structlog`)
3. Local `app.*` modules

**Path Aliases:**
- No path aliases; imports use absolute package paths such as `from app.dependencies import get_db`.

## Error Handling

**Patterns:**
- API validation/auth failures raise `fastapi.HTTPException` with status and detail (`app/routes/auth.py`).
- Infrastructure failures are caught at integration boundaries, logged, and converted to safe fallback values (`app/services/billing_cache.py`).
- Repository methods return `None` for missing entities and typed collections for list queries (`app/repositories/base.py`).

## Logging

**Framework:** structlog (`app/logging_config.py`, `app/worker/tasks.py`).

**Patterns:**
- Create module loggers with `structlog.get_logger(__name__)`.
- Use event-style names and keyword context (`logger.error("...", error=str(e), exc_info=True)`).
- Bind request/task identifiers when processing asynchronous work (`app/worker/tasks.py`).

## Comments

**When to Comment:**
- Comments/docstrings explain non-obvious integration behavior and fallback policy; straightforward code is generally self-documenting.

**JSDoc/TSDoc:**
- Python docstrings are short and operation-focused on public service helpers; extensive API documentation is provided by FastAPI models/routes.

## Function Design

**Size:**
- Keep route handlers thin: validate input, call repository/service, and shape the response (`app/routes/*.py`).

**Parameters:**
- Prefer typed parameters and dependency injection (`AsyncSession = Depends(get_db)`, `Settings = Depends(get_settings)`).

**Return Values:**
- Annotate return types, including `T | None`, `list[T]`, and tuples for service outcomes.
- Pydantic response models define externally visible API shapes (`app/routes/auth.py`).

## Module Design

**Exports:**
- Modules expose focused functions/classes; imports generally target concrete modules rather than broad re-exports.

**Barrel Files:**
- Package `__init__.py` files are present for package discovery, but no broad barrel-export convention is used.

---

*Convention analysis: 2026-08-03*

# Testing Patterns

**Analysis Date:** 2026-08-03

## Test Framework

**Runner:**
- pytest 9.x with pytest-asyncio 1.x (`pyproject.toml`).
- No standalone pytest config file was detected.

**Assertion Library:**
- Native pytest `assert` statements; HTTP tests inspect `response.status_code` and `response.json()`.

**Run Commands:**
```bash
uv run pytest tests/ -v       # Run all tests (also exposed as `just test`)
just test-cov                  # Run with coverage
```

## Test File Organization

**Location:**
- Tests live under top-level `tests/`, organized by layer (`tests/test_services/`, `tests/test_repositories/`, `tests/test_pages/`, `tests/test_messengers/`).

**Naming:**
- Files use `test_<subject>.py`; test functions use `test_<behavior>`.

**Structure:**
```text
tests/conftest.py             # shared async DB/client/auth fixtures
tests/test_services/*.py      # service unit tests
tests/test_repositories/*.py  # repository integration tests
tests/test_pages/*.py         # server-rendered page endpoint tests
```

## Test Structure

**Suite Organization:**
```python
@pytest.mark.asyncio
async def test_get_by_id(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    found = await ad_repo.get_by_id(ad.id)
    assert found is not None
```

**Patterns:**
- Async tests are explicitly marked `@pytest.mark.asyncio` (or use `pytest_asyncio.fixture`).
- Fixtures create prerequisite entities and commit/refresh them before yielding.
- Tests assert both success values and negative paths (missing records, invalid tokens, blocked users).

## Mocking

**Framework:** `unittest.mock` (`AsyncMock`, `MagicMock`, `patch`).

**Patterns:**
```python
with patch("app.services.s3.AioSession", return_value=mock_session):
    key = await upload_file_to_s3(...)
mock_client.put_object.assert_called_once_with(...)
```

**What to Mock:**
- Mock network clients and external SDKs (Telethon, S3, HTTPX, Redis, Docker) at the module import path used by the subject.
- Use `AsyncMock` for awaited methods and async context-manager enter/exit methods.

**What NOT to Mock:**
- Keep repository/database behavior real using the in-memory SQLite fixture; avoid mocking SQLAlchemy queries in repository tests.

## Fixtures and Factories

**Test Data:**
- `tests/conftest.py` provides `test_settings`, `db_session`, `client`, and `auth_headers`.
- `db_session` creates all `Base.metadata` tables per test and drops/disposes the engine afterward.

**Location:**
- Shared fixtures belong in `tests/conftest.py`; subject-specific fixtures are colocated in the relevant test module.

## Coverage

**Requirements:**
- Coverage tooling is available through `pytest-cov`; no enforced percentage target was detected.

**View Coverage:**
```bash
just test-cov
```

## Test Types

**Unit Tests:**
- Pure service helpers and token/password logic run without application startup (`tests/test_services/test_auth_service.py`).

**Integration Tests:**
- Repository and route tests exercise real SQLAlchemy sessions and FastAPI dependency overrides with SQLite (`tests/test_repositories/`, `tests/conftest.py`).

**E2E Tests:**
- HTTP workflow coverage exists in `tests/test_e2e.py`; no browser automation framework was detected.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_operation(client):
    response = await client.post("/api/...", json={...})
    assert response.status_code == 201
```

**Error Testing:**
- Invalid input and integration exceptions are tested by asserting status codes, `None` returns, or boolean failure results; mock failures use `side_effect=Exception(...)` (`tests/test_messengers/test_telegram_user.py`).

---

*Testing analysis: 2026-08-03*

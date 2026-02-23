# Production Logging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add structured logging with structlog to catch messenger errors (Telegram/WhatsApp) in production

**Architecture:** Configure structlog with JSON output in prod, console in dev. Add logging to all silent error paths in messengers, worker tasks, and FastAPI exception handlers. Add request_id middleware for tracing.

**Tech Stack:** structlog, FastAPI middleware, Celery signals

---

### Task 1: Add structlog dependency

**Files:**
- Modify: `pyproject.toml:7-26`

**Step 1: Add structlog to dependencies**

In `pyproject.toml`, add `"structlog>=24.1.0"` to the `dependencies` list, after `"sqlalchemy[asyncio]>=2.0.46"`:

```toml
    "structlog>=24.1.0",
```

**Step 2: Sync environment**

Run: `uv sync`
Expected: structlog installed successfully

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add structlog dependency"
```

---

### Task 2: Add LOG_LEVEL and LOG_FORMAT to Settings

**Files:**
- Modify: `app/config.py:6-48`
- Modify: `tests/conftest.py:12-20`

**Step 1: Write the failing test**

Add to `tests/test_config.py`:

```python
def test_log_level_default():
    """LOG_LEVEL defaults to INFO."""
    from app.config import Settings
    s = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
    )
    assert s.log_level == "INFO"
    assert s.log_format == "json"


def test_log_level_override():
    """LOG_LEVEL can be set via env."""
    import os
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOG_FORMAT"] = "console"
    from app.config import Settings
    s = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
    )
    assert s.log_level == "DEBUG"
    assert s.log_format == "console"
    del os.environ["LOG_LEVEL"]
    del os.environ["LOG_FORMAT"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py::test_log_level_default -v`
Expected: FAIL with AttributeError (no `log_level` attribute)

**Step 3: Add settings fields**

In `app/config.py`, add after the `debug` field (line 8):

```python
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: add LOG_LEVEL and LOG_FORMAT settings"
```

---

### Task 3: Create logging configuration module

**Files:**
- Create: `app/logging_config.py`
- Test: `tests/test_logging_config.py`

**Step 1: Write the failing test**

Create `tests/test_logging_config.py`:

```python
import logging
import structlog
import pytest
from app.logging_config import setup_logging


def test_setup_logging_json_mode():
    """setup_logging configures structlog with JSON output."""
    setup_logging(log_level="INFO", log_format="json")
    logger = structlog.get_logger("test.json")
    # Should not raise
    assert logger is not None


def test_setup_logging_console_mode():
    """setup_logging configures structlog with console output."""
    setup_logging(log_level="DEBUG", log_format="console")
    logger = structlog.get_logger("test.console")
    assert logger is not None


def test_setup_logging_sets_level():
    """setup_logging sets root logger level."""
    setup_logging(log_level="WARNING", log_format="json")
    root = logging.getLogger()
    assert root.level == logging.WARNING
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_logging_config.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create logging_config.py**

Create `app/logging_config.py`:

```python
import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure structlog + stdlib logging.

    Args:
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR).
        log_format: "json" for production, "console" for dev.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_logging_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/logging_config.py tests/test_logging_config.py
git commit -m "feat: add structlog logging configuration module"
```

---

### Task 4: Create request_id middleware

**Files:**
- Create: `app/middleware.py`
- Test: `tests/test_middleware.py`

**Step 1: Write the failing test**

Create `tests/test_middleware.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.middleware import RequestIdMiddleware


@pytest.mark.asyncio
async def test_request_id_header_added():
    """Middleware adds X-Request-ID to response."""
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/test")

    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    # UUID hex format: 32 chars
    assert len(resp.headers["x-request-id"]) == 32


@pytest.mark.asyncio
async def test_request_id_unique_per_request():
    """Each request gets a unique request_id."""
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.get("/test")
        resp2 = await client.get("/test")

    assert resp1.headers["x-request-id"] != resp2.headers["x-request-id"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_middleware.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create middleware.py**

Create `app/middleware.py`:

```python
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = structlog.get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add request_id to every request, log request duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_middleware.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/middleware.py tests/test_middleware.py
git commit -m "feat: add request_id middleware with duration logging"
```

---

### Task 5: Integrate structlog and middleware into main.py

**Files:**
- Modify: `app/main.py:1-67`
- Modify: `tests/test_main.py`

**Step 1: Write the failing test**

Add to `tests/test_main.py`:

```python
@pytest.mark.asyncio
async def test_unhandled_exception_returns_500():
    """Generic exceptions return 500 JSON and include request_id."""
    from app.main import create_app
    app = create_app()

    @app.get("/explode")
    async def explode():
        raise RuntimeError("Unexpected error")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/explode")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert "x-request-id" in response.headers
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py::test_unhandled_exception_returns_500 -v`
Expected: FAIL (no generic handler, no middleware)

**Step 3: Update main.py**

Replace the full content of `app/main.py`:

```python
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse

from app.logging_config import setup_logging
from app.config import Settings, get_settings
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError, MessengerConnectionError
from app.database import get_engine, get_session_factory
from app.dependencies import init_db
from app.middleware import RequestIdMiddleware
from app.routes.auth import router as auth_router
from app.routes.ads import router as ads_router
from app.routes.uploads import router as uploads_router
from app.routes.accounts import router as accounts_router
from app.routes.groups import router as groups_router
from app.routes.schedules import router as schedules_router
from app.routes.history import router as history_router
from app.routes.billing import router as billing_router
from app.pages import router as pages_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)
    init_db(session_factory)
    yield
    await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    app = FastAPI(title="Broadcaster", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    app.include_router(auth_router)
    app.include_router(ads_router)
    app.include_router(uploads_router)
    app.include_router(accounts_router)
    app.include_router(groups_router)
    app.include_router(schedules_router)
    app.include_router(history_router)
    app.include_router(billing_router)
    app.include_router(pages_router)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: FastAPIRequest, exc: NotFoundError):
        logger.warning("not_found", error=str(exc))
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: FastAPIRequest, exc: ForbiddenError):
        logger.warning("forbidden", error=str(exc))
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(BillingLimitError)
    async def billing_limit_handler(request: FastAPIRequest, exc: BillingLimitError):
        logger.warning("billing_limit", error=str(exc))
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(MessengerConnectionError)
    async def messenger_error_handler(request: FastAPIRequest, exc: MessengerConnectionError):
        logger.error("messenger_connection_error", error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: FastAPIRequest, exc: Exception):
        logger.error(
            "unhandled_exception",
            error=str(exc),
            exc_type=type(exc).__name__,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app
```

**Step 4: Update test_main.py**

The existing `test_health_check` test should still pass. Update the import in `tests/test_main.py` — the test file already uses `create_app()`, so no changes needed to existing tests.

**Step 5: Run tests to verify**

Run: `uv run pytest tests/test_main.py -v`
Expected: PASS (both old and new tests)

**Step 6: Commit**

```bash
git add app/main.py tests/test_main.py
git commit -m "feat: integrate structlog, middleware, and exception logging into main.py"
```

---

### Task 6: Add logging to WhatsApp messenger

**Files:**
- Modify: `app/messengers/whatsapp.py:1-102`
- Modify: `tests/test_messengers/test_whatsapp.py`

**Step 1: Write the failing test**

Add to `tests/test_messengers/test_whatsapp.py`:

```python
@pytest.mark.asyncio
async def test_send_message_logs_error_on_http_failure(caplog):
    """send_message logs error when HTTP call fails."""
    import logging
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.ERROR, logger="app.messengers.whatsapp"):
            result = await messenger.send_message("group123", "Hello!")

    assert result["ok"] is False
    assert any("send_message_error" in r.message or "Connection refused" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_get_groups_logs_error_on_failure(caplog):
    """get_groups logs error when HTTP call fails."""
    import logging
    messenger = WhatsAppMessenger("http://wa-bridge:3000", session_id="42")

    with patch("app.messengers.whatsapp.get_http_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        mock_get_client.return_value = mock_client

        with caplog.at_level(logging.ERROR, logger="app.messengers.whatsapp"):
            groups = await messenger.get_groups()

    assert groups == []
    assert any("get_groups_error" in r.message or "Timeout" in r.message for r in caplog.records)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_messengers/test_whatsapp.py::test_send_message_logs_error_on_http_failure -v`
Expected: FAIL (no logging in whatsapp.py)

**Step 3: Update whatsapp.py**

Replace the full content of `app/messengers/whatsapp.py`:

```python
import httpx
import structlog

from app.messengers.base import BaseMessenger

logger = structlog.get_logger(__name__)


def get_bridge_url(session_id: int, bridge_urls: list[str]) -> str:
    """Consistent routing: same session always goes to same bridge."""
    return bridge_urls[session_id % len(bridge_urls)]


# Module-level shared HTTP client (created lazily)
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create shared httpx client with connection pooling."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _http_client


class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str, session_id: str):
        self.bridge_url = bridge_url.rstrip("/")
        self.session_id = session_id
        self.log = logger.bind(messenger="whatsapp", session_id=session_id)

    def _url(self, path: str) -> str:
        return f"{self.bridge_url}/api/sessions/{self.session_id}/{path}"

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        client = get_http_client()
        try:
            payload = {"group_id": group_id, "text": text}
            if images:
                payload["image_urls"] = images
            response = await client.post(self._url("send"), json=payload)
            if response.status_code != 200:
                # Try to extract error message from JSON response
                error_msg = ""
                try:
                    body = response.json()
                    error_msg = body.get("error", "")
                except Exception:
                    error_msg = response.text
                error = f"[HTTP {response.status_code}] {error_msg}" if error_msg else f"[HTTP {response.status_code}] empty response"
                self.log.error("send_message_error", group_id=group_id, http_status=response.status_code, error=error)
                return {"ok": False, "error": error}
            self.log.debug("send_message_ok", group_id=group_id)
            return {"ok": True}
        except httpx.HTTPError as e:
            error = f"[Connection] {type(e).__name__}: {e}"
            self.log.error("send_message_error", group_id=group_id, error=error, exc_info=True)
            return {"ok": False, "error": error}

    async def get_groups(self) -> list[dict]:
        client = get_http_client()
        try:
            response = await client.get(self._url("groups"))
            if response.status_code == 200:
                return response.json()
            self.log.error("get_groups_error", http_status=response.status_code)
            return []
        except Exception as e:
            self.log.error("get_groups_error", error=str(e), exc_info=True)
            return []

    async def check_connection(self) -> bool:
        client = get_http_client()
        try:
            response = await client.get(self._url("status"))
            return response.status_code == 200 and response.json().get("connected", False)
        except Exception as e:
            self.log.warning("check_connection_failed", error=str(e))
            return False

    async def start_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.post(self._url("start"), timeout=30)
            return response.status_code == 200
        except Exception as e:
            self.log.error("start_session_error", error=str(e), exc_info=True)
            return False

    async def destroy_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.delete(
                f"{self.bridge_url}/api/sessions/{self.session_id}"
            )
            return response.status_code == 200
        except Exception as e:
            self.log.error("destroy_session_error", error=str(e), exc_info=True)
            return False

    async def get_qr(self) -> dict:
        client = get_http_client()
        try:
            response = await client.get(self._url("qr"))
            if response.status_code == 200:
                return response.json()
            self.log.warning("get_qr_error", http_status=response.status_code)
            return {"status": "error", "qr": None}
        except Exception as e:
            self.log.error("get_qr_error", error=str(e), exc_info=True)
            return {"status": "error", "qr": None}
```

**Step 4: Run tests to verify**

Run: `uv run pytest tests/test_messengers/test_whatsapp.py -v`
Expected: ALL PASS (old tests + new logging tests)

**Step 5: Commit**

```bash
git add app/messengers/whatsapp.py tests/test_messengers/test_whatsapp.py
git commit -m "feat: add structured logging to WhatsApp messenger"
```

---

### Task 7: Add logging to Telegram user messenger

**Files:**
- Modify: `app/messengers/telegram_user.py:1-254`
- Modify: `tests/test_messengers/test_telegram_user.py`

**Step 1: Write the failing test**

Add to `tests/test_messengers/test_telegram_user.py`:

```python
@pytest.mark.asyncio
async def test_get_groups_logs_error_on_failure(messenger, caplog):
    """get_groups logs error when Telegram API fails."""
    import logging
    messenger.client.get_dialogs = AsyncMock(side_effect=Exception("Session expired"))

    with caplog.at_level(logging.ERROR, logger="app.messengers.telegram_user"):
        groups = await messenger.get_groups()

    assert groups == []
    assert any("get_groups_error" in r.message or "Session expired" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_check_connection_logs_warning_on_failure(messenger, caplog):
    """check_connection logs warning when check fails."""
    import logging
    messenger.client.get_me = AsyncMock(side_effect=Exception("Auth key expired"))

    with caplog.at_level(logging.WARNING, logger="app.messengers.telegram_user"):
        result = await messenger.check_connection()

    assert result is False
    assert any("check_connection_failed" in r.message or "Auth key expired" in r.message for r in caplog.records)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest "tests/test_messengers/test_telegram_user.py::test_get_groups_logs_error_on_failure" -v`
Expected: FAIL (get_groups has `pass` instead of logging)

**Step 3: Update telegram_user.py**

Replace `import logging` with `import structlog` and update logger creation. Then update the messenger class methods:

Change line 1-14:
```python
import asyncio
import structlog
import time
import uuid
from dataclasses import dataclass, field

import httpx
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat

from app.messengers.base import BaseMessenger

logger = structlog.get_logger(__name__)
```

Update `TelegramUserMessenger.__init__` (add self.log):
```python
class TelegramUserMessenger(BaseMessenger):
    def __init__(self, session_string: str, api_id: int, api_hash: str):
        self.client = TelegramClient(
            StringSession(session_string), api_id, api_hash
        )
        self.log = logger.bind(messenger="telegram")
```

Update `send_message` except block (line 217-218):
```python
        except Exception as e:
            self.log.error("send_message_error", group_id=group_id, error=str(e), exc_info=True)
            return {"ok": False, "error": str(e)}
```

Update `get_groups` except block (line 233-234):
```python
        except Exception as e:
            self.log.error("get_groups_error", error=str(e), exc_info=True)
```

Update `check_connection` except block (line 247-248):
```python
        except Exception as e:
            self.log.warning("check_connection_failed", error=str(e))
            return False
```

**Step 4: Run tests to verify**

Run: `uv run pytest tests/test_messengers/test_telegram_user.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/messengers/telegram_user.py tests/test_messengers/test_telegram_user.py
git commit -m "feat: add structured logging to Telegram user messenger"
```

---

### Task 8: Add logging to Telegram pool

**Files:**
- Modify: `app/messengers/telegram_pool.py:1-67`

**Step 1: Update telegram_pool.py**

Replace `import logging` with `import structlog`:

```python
import structlog

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = structlog.get_logger(__name__)
```

Wrap `_create_client()` call in `get()` method (around line 42) with try/except:

```python
    async def get(
        self,
        account_id: int,
        session_string: str,
        api_id: int,
        api_hash: str,
    ) -> TelegramClient:
        """Get or create a connected TelegramClient for the given account."""
        client = self._clients.get(account_id)

        if client and client.is_connected():
            return client

        # Reconnect or create new
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

        try:
            client = await self._create_client(session_string, api_id, api_hash)
        except Exception as e:
            logger.error("telegram_pool_connect_error", account_id=account_id, error=str(e), exc_info=True)
            raise

        self._clients[account_id] = client
        logger.info("telegram_pool_connected", account_id=account_id)
        return client
```

**Step 2: Run existing tests**

Run: `uv run pytest tests/test_telegram_pool.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add app/messengers/telegram_pool.py
git commit -m "feat: add structured logging to Telegram pool"
```

---

### Task 9: Add logging to worker tasks

**Files:**
- Modify: `app/worker/tasks.py:1-247`

**Step 1: Update imports and logger**

Replace lines 1-22:

```python
import asyncio
import structlog
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.billing_cache import check_limit_cached
from app.services.messenger_factory import create_messenger
from app.services.s3 import get_image_url
from app.services.schedule_service import compute_next_run_at

logger = structlog.get_logger(__name__)
```

**Step 2: Add logging to _send_message**

Update `_send_message` function (lines 150-203) to add logging:

```python
async def _send_message(ad_id: int, group_id: int, account_id: int, schedule_id: int):
    """Shared send logic for both Telegram and WhatsApp tasks."""
    log = logger.bind(ad_id=ad_id, group_id=group_id, account_id=account_id, schedule_id=schedule_id)
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        ad = await session.get(Ad, ad_id)
        group = await session.get(Group, group_id)
        account = await session.get(MessengerAccount, account_id)

        if not ad or not group or not account:
            log.warning("send_skipped", reason="missing_record", ad=bool(ad), group=bool(group), account=bool(account))
            log_entry = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="fail", error_message="Missing ad, group, or account",
            )
            session.add(log_entry)
            await session.commit()
            return

        if account.status != "active":
            log.warning("send_skipped", reason="account_disconnected", account_status=account.status)
            log_entry = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="account_disconnected",
                error_message=f"Account {account.id} is {account.status}",
            )
            session.add(log_entry)
            await session.commit()
            return

        images = None
        if ad.images:
            s3_public_url = settings.s3_public_url
            images = [get_image_url(img, s3_public_url) for img in ad.images]

        try:
            messenger = create_messenger(account, settings)
        except ValueError as e:
            log.error("create_messenger_error", error=str(e), account_type=account.type)
            log_entry = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="fail", error_message=str(e),
            )
            session.add(log_entry)
            await session.commit()
            return

        result = await messenger.send_message(
            group_id=group.group_external_id,
            text=ad.text,
            images=images,
        )

        log_entry = SendLog(
            schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
            status="ok" if result["ok"] else "fail",
            error_message=result.get("error"),
        )
        session.add(log_entry)
        await session.commit()

        if not result["ok"]:
            log.error("send_failed", error=result.get("error"))
            raise Exception(f"Send failed: {result.get('error')}")

        log.info("send_ok")

    await engine.dispose()
```

**Step 3: Add on_failure logging to Celery tasks**

Update the Celery task definitions to add `on_failure` logging:

```python
def _on_send_failure(self, exc, task_id, args, kwargs, einfo):
    """Log when all retries are exhausted."""
    ad_id, group_id, account_id, schedule_id = args
    logger.error(
        "send_task_final_failure",
        task_id=task_id,
        ad_id=ad_id,
        group_id=group_id,
        account_id=account_id,
        schedule_id=schedule_id,
        error=str(exc),
        exc_info=exc,
    )


@shared_task(
    name="app.worker.tasks.send_telegram_message",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="20/m",
)
def send_telegram_message(self, ad_id, group_id, account_id, schedule_id):
    """Send a single Telegram message. Auto-retries with backoff."""
    asyncio.run(_send_message(ad_id, group_id, account_id, schedule_id))


send_telegram_message.on_failure = _on_send_failure


@shared_task(
    name="app.worker.tasks.send_whatsapp_message",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="30/m",
)
def send_whatsapp_message(self, ad_id, group_id, account_id, schedule_id):
    """Send a single WhatsApp message. Auto-retries with backoff."""
    asyncio.run(_send_message(ad_id, group_id, account_id, schedule_id))


send_whatsapp_message.on_failure = _on_send_failure
```

**Step 4: Add try/except to check_schedules**

Update `check_schedules` function:

```python
@shared_task(name="app.worker.tasks.check_schedules")
def check_schedules():
    """Celery task: check all due schedules and dispatch individual send tasks."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        try:
            async with session_factory() as session:
                await check_schedules_async(session)
        except Exception as e:
            logger.error("check_schedules_error", error=str(e), exc_info=True)
            raise
        finally:
            await engine.dispose()

    asyncio.run(_run())
```

**Step 5: Run tests to verify**

Run: `uv run pytest tests/test_worker/test_tasks.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add app/worker/tasks.py
git commit -m "feat: add structured logging to worker tasks with on_failure handler"
```

---

### Task 10: Add logging to WA consumer and billing cache

**Files:**
- Modify: `app/worker/wa_consumer.py:1-61`
- Modify: `app/services/billing_cache.py:1-57`

**Step 1: Update wa_consumer.py**

Replace `import logging` with `import structlog`:

```python
"""Dynamic queue discovery for WhatsApp session-affinity workers.

WhatsApp workers consume from dynamically-created queues
(whatsapp.session.{id}). This module handles registering/discovering those queues
in Redis.

The check_schedules task routes WA tasks to whatsapp.session.{id} queues.
Celery workers configured with task_create_missing_queues=True will
auto-create these queues when tasks are dispatched.
"""
import structlog

logger = structlog.get_logger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio
            from app.config import get_settings
            _redis_client = redis.asyncio.from_url(get_settings().redis_url)
        except Exception as e:
            logger.error("wa_consumer_redis_connect_error", error=str(e))
            return None
    return _redis_client


async def get_active_wa_queues() -> list[str]:
    """Get list of active WhatsApp session queues from Redis."""
    r = _get_redis()
    if not r:
        return []
    try:
        members = await r.smembers("wa:active_queues")
        return [m.decode() if isinstance(m, bytes) else m for m in members]
    except Exception as e:
        logger.warning("wa_consumer_get_queues_error", error=str(e))
        return []


async def register_wa_queue(queue_name: str) -> None:
    """Register a WhatsApp session queue as active."""
    r = _get_redis()
    if r:
        try:
            await r.sadd("wa:active_queues", queue_name)
        except Exception as e:
            logger.warning("wa_consumer_register_error", queue=queue_name, error=str(e))


async def unregister_wa_queue(queue_name: str) -> None:
    """Remove a WhatsApp session queue from active set."""
    r = _get_redis()
    if r:
        try:
            await r.srem("wa:active_queues", queue_name)
        except Exception as e:
            logger.warning("wa_consumer_unregister_error", queue=queue_name, error=str(e))
```

**Step 2: Update billing_cache.py**

Replace `import logging` with `import structlog`:

```python
import json
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing_service import check_limit
from app.config import get_settings

logger = structlog.get_logger(__name__)
```

No other changes needed — billing_cache already uses `logger.warning`.

**Step 3: Run tests to verify**

Run: `uv run pytest tests/test_wa_consumer.py tests/test_billing_cache.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add app/worker/wa_consumer.py app/services/billing_cache.py
git commit -m "feat: add structured logging to WA consumer and billing cache"
```

---

### Task 11: Configure structlog for Celery workers

**Files:**
- Modify: `app/worker/celery_app.py:1-39`

**Step 1: Add logging setup to Celery app**

Update `app/worker/celery_app.py` to initialize structlog when Celery starts:

```python
from celery import Celery
from celery.signals import worker_init


def create_celery_app() -> Celery:
    """Create Celery app. Reads config from environment."""
    from app.config import get_settings
    settings = get_settings()

    app = Celery(
        "broadcaster",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        imports=["app.worker.tasks"],
        task_default_queue="default",
        task_create_missing_queues=True,
        task_routes={
            "app.worker.tasks.send_telegram_message": {"queue": "telegram"},
        },
        beat_schedule={
            "check-schedules": {
                "task": "app.worker.tasks.check_schedules",
                "schedule": float(settings.celery_beat_interval),
            },
        },
        worker_prefetch_multiplier=1,
    )

    return app


celery = create_celery_app()


@worker_init.connect
def setup_worker_logging(**kwargs):
    """Initialize structlog when Celery worker starts."""
    from app.config import get_settings
    from app.logging_config import setup_logging
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)
```

**Step 2: Run tests to verify**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add app/worker/celery_app.py
git commit -m "feat: initialize structlog in Celery workers via worker_init signal"
```

---

### Task 12: Run full test suite and verify

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL 157+ tests PASS

**Step 2: If any test failures, fix them**

Common issues to watch for:
- Tests that capture log output with `caplog` may need `structlog` test configuration
- Import changes from `logging` to `structlog` may affect mocks

**Step 3: Final commit if fixes were needed**

```bash
git add -A
git commit -m "fix: resolve test issues after structlog migration"
```

---

## Summary of Changes

| File | Change |
|------|--------|
| `pyproject.toml` | Add `structlog` dependency |
| `app/config.py` | Add `log_level`, `log_format` settings |
| `app/logging_config.py` | **New** — structlog configuration |
| `app/middleware.py` | **New** — request_id + duration middleware |
| `app/main.py` | Integrate structlog, middleware, exception logging |
| `app/messengers/whatsapp.py` | Add logger, log all errors |
| `app/messengers/telegram_user.py` | Switch to structlog, log all errors |
| `app/messengers/telegram_pool.py` | Switch to structlog, catch connection errors |
| `app/worker/tasks.py` | Switch to structlog, on_failure handler, error context |
| `app/worker/wa_consumer.py` | Switch to structlog, log instead of pass |
| `app/worker/celery_app.py` | Init structlog on worker_init signal |
| `app/services/billing_cache.py` | Switch to structlog |

## What You'll See After Implementation

**In `docker compose logs`:**
```json
{"timestamp": "2026-02-23T12:00:00Z", "level": "error", "logger": "app.messengers.whatsapp", "event": "send_message_error", "session_id": "42", "group_id": "120363XXX", "http_status": 500, "error": "[HTTP 500] Session not found"}
{"timestamp": "2026-02-23T12:00:01Z", "level": "error", "logger": "app.worker.tasks", "event": "send_failed", "ad_id": 5, "group_id": 12, "account_id": 42, "schedule_id": 3, "error": "[HTTP 500] Session not found"}
{"timestamp": "2026-02-23T12:00:31Z", "level": "error", "logger": "app.worker.tasks", "event": "send_task_final_failure", "task_id": "abc-123", "ad_id": 5, "error": "Send failed: [HTTP 500] Session not found"}
```

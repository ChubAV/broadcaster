# Scaling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scale Broadcaster to handle 200+ users sending hundreds of simultaneous messages via Telegram and WhatsApp, with retry, rate limiting, and session affinity.

**Architecture:** Replace monolithic `asyncio.gather()` with distributed Celery tasks per message. WhatsApp tasks routed to per-session queues for Chromium reuse. Multiple wa-bridge instances with Python-side consistent routing. DB optimized with indexes, eager loading, and Redis billing cache.

**Tech Stack:** Celery (queues, retry, rate_limit), Redis (cache, broker), SQLAlchemy (joinedload, indexes), httpx (connection pool), Flower (monitoring)

**Design doc:** `docs/plans/2026-02-22-scaling-design.md`

---

### Task 1: Add DB indexes via Alembic migration

**Files:**
- Create: `alembic/versions/xxxx_add_scaling_indexes.py` (auto-generated)
- Modify: `app/models/schedule.py`
- Modify: `app/models/send_log.py`
- Modify: `app/models/ad.py`
- Modify: `app/models/group.py`

**Step 1: Add index declarations to models**

In `app/models/schedule.py`, add `index=True` to `next_run_at` and `is_active`:

```python
# app/models/schedule.py — change lines 21-23
next_run_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True, index=True
)
```

Add `index=True` to `is_active` (line 20):
```python
is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
```

In `app/models/send_log.py`, add `index=True` to `sent_at` (line 21):
```python
sent_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), index=True
)
```

In `app/models/ad.py`, `user_id` already has FK — add `index=True` (line 13):
```python
user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"), index=True
)
```

In `app/models/group.py`, `user_id` already has FK — add `index=True` (line 13):
```python
user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"), index=True
)
```

**Step 2: Generate Alembic migration**

Run: `uv run alembic revision --autogenerate -m "add scaling indexes"`
Expected: Migration file created in `alembic/versions/`

**Step 3: Review and apply migration**

Run: `uv run alembic upgrade head`
Expected: Indexes created on schedule.next_run_at, schedule.is_active, send_logs.sent_at, ads.user_id, groups.user_id

**Step 4: Run tests to verify no breakage**

Run: `uv run pytest tests/ -v`
Expected: All 157 tests pass

**Step 5: Commit**

```bash
git add app/models/schedule.py app/models/send_log.py app/models/ad.py app/models/group.py alembic/
git commit -m "perf: add database indexes for scaling"
```

---

### Task 2: Add ORM relationships to Schedule model for eager loading

**Files:**
- Modify: `app/models/schedule.py`
- Test: `tests/test_schedule_relationships.py`

**Step 1: Write the failing test**

```python
# tests/test_schedule_relationships.py
import pytest
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.schedule import Schedule
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount


@pytest.mark.asyncio
async def test_schedule_eager_load_ad_and_account(db_session):
    """Schedule.ad and Schedule.account relationships support joinedload."""
    account = MessengerAccount(
        user_id=1, type="tg_user", credentials="test", status="active"
    )
    db_session.add(account)
    await db_session.flush()

    ad = Ad(user_id=1, title="Test", text="Hello", images=[])
    db_session.add(ad)
    await db_session.flush()

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[1],
        days_of_week=[0, 1],
        times_of_day=["10:00"],
        is_active=True,
    )
    db_session.add(schedule)
    await db_session.commit()

    result = await db_session.execute(
        select(Schedule)
        .options(joinedload(Schedule.ad), joinedload(Schedule.account))
        .where(Schedule.id == schedule.id)
    )
    loaded = result.unique().scalars().first()
    assert loaded is not None
    assert loaded.ad.title == "Test"
    assert loaded.account.type == "tg_user"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_schedule_relationships.py -v`
Expected: FAIL — `Schedule` has no attribute `ad` or `account`

**Step 3: Add relationships to Schedule model**

In `app/models/schedule.py`, add imports and relationships:

```python
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_id: Mapped[int] = mapped_column(
        ForeignKey("ads.id", ondelete="CASCADE")
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("messenger_accounts.id", ondelete="CASCADE")
    )
    group_ids: Mapped[list] = mapped_column(JSON, default=list)
    days_of_week: Mapped[list] = mapped_column(JSON, default=list)
    times_of_day: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships for eager loading
    ad = relationship("Ad", lazy="raise")
    account = relationship("MessengerAccount", lazy="raise")
```

Note: `lazy="raise"` ensures we never accidentally trigger lazy loads — forces explicit `joinedload()` usage.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_schedule_relationships.py -v`
Expected: PASS

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add app/models/schedule.py tests/test_schedule_relationships.py
git commit -m "feat: add Schedule.ad and Schedule.account relationships for eager loading"
```

---

### Task 3: Add Settings for WA bridge URLs and queue config

**Files:**
- Modify: `app/config.py:34-35`
- Modify: `tests/conftest.py:12-17` (update test_settings)

**Step 1: Add new settings fields**

In `app/config.py`, replace `wa_bridge_url` with `wa_bridge_urls` (line 35) and add queue settings:

```python
# WA Bridge
wa_bridge_urls: list[str] = ["http://wa-bridge:3000"]

# Celery scaling
celery_beat_interval: int = 30  # seconds
billing_cache_ttl: int = 60  # seconds
```

Keep backward compatibility: leave the old `wa_bridge_url` as a property that returns the first bridge URL:

```python
@property
def wa_bridge_url(self) -> str:
    """Backward-compatible: returns first bridge URL."""
    return self.wa_bridge_urls[0]
```

**Step 2: Update test_settings in conftest.py**

In `tests/conftest.py`, add `wa_bridge_urls` to test settings (line 13):

```python
@pytest_asyncio.fixture
async def test_settings():
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
        wa_bridge_urls=["http://localhost:3000"],
    )
```

**Step 3: Run tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add app/config.py tests/conftest.py
git commit -m "feat: add wa_bridge_urls and scaling settings to config"
```

---

### Task 4: Billing cache in Redis

**Files:**
- Create: `app/services/billing_cache.py`
- Test: `tests/test_billing_cache.py`

**Step 1: Write the failing test**

```python
# tests/test_billing_cache.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.billing_cache import check_limit_cached


@pytest.mark.asyncio
async def test_check_limit_cached_returns_result():
    """check_limit_cached returns (allowed, reason) like check_limit."""
    mock_db = AsyncMock()
    # Mock the underlying check_limit
    with patch("app.services.billing_cache.check_limit", return_value=(True, "")) as mock_check:
        with patch("app.services.billing_cache._get_redis", return_value=None):
            result = await check_limit_cached(mock_db, user_id=1, action="send")
    assert result == (True, "")
    mock_check.assert_called_once_with(mock_db, 1, "send")


@pytest.mark.asyncio
async def test_check_limit_cached_uses_cache():
    """Second call uses cached result, not DB."""
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value='{"allowed": true, "reason": ""}')

    with patch("app.services.billing_cache._get_redis", return_value=mock_redis):
        with patch("app.services.billing_cache.check_limit") as mock_check:
            result = await check_limit_cached(mock_db, user_id=1, action="send")
    assert result == (True, "")
    mock_check.assert_not_called()  # Should use cache, not DB
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_billing_cache.py -v`
Expected: FAIL — module not found

**Step 3: Implement billing cache**

```python
# app/services/billing_cache.py
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing_service import check_limit
from app.config import get_settings

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    """Lazy-init Redis client for billing cache."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            settings = get_settings()
            _redis_client = redis.asyncio.from_url(settings.redis_url)
        except Exception:
            logger.warning("Redis not available for billing cache")
            return None
    return _redis_client


async def check_limit_cached(
    db: AsyncSession, user_id: int, action: str
) -> tuple[bool, str]:
    """check_limit with Redis cache. Falls back to DB on cache miss/error."""
    cache_key = f"billing:{user_id}:{action}"
    ttl = get_settings().billing_cache_ttl

    r = _get_redis()
    if r:
        try:
            cached = await r.get(cache_key)
            if cached:
                data = json.loads(cached)
                return data["allowed"], data["reason"]
        except Exception:
            pass

    allowed, reason = await check_limit(db, user_id, action)

    if r:
        try:
            await r.setex(
                cache_key,
                ttl,
                json.dumps({"allowed": allowed, "reason": reason}),
            )
        except Exception:
            pass

    return allowed, reason
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_billing_cache.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/billing_cache.py tests/test_billing_cache.py
git commit -m "feat: add Redis-cached billing limit checks"
```

---

### Task 5: WhatsApp httpx connection pool + bridge routing

**Files:**
- Modify: `app/messengers/whatsapp.py` (full rewrite)
- Test: `tests/test_whatsapp_routing.py`

**Step 1: Write the failing test**

```python
# tests/test_whatsapp_routing.py
import pytest
from app.messengers.whatsapp import get_bridge_url


def test_get_bridge_url_consistent_routing():
    """Same session_id always routes to same bridge."""
    bridges = ["http://bridge-1:3000", "http://bridge-2:3000", "http://bridge-3:3000"]
    url1 = get_bridge_url(42, bridges)
    url2 = get_bridge_url(42, bridges)
    assert url1 == url2  # Consistent


def test_get_bridge_url_distributes():
    """Different session_ids distribute across bridges."""
    bridges = ["http://bridge-1:3000", "http://bridge-2:3000", "http://bridge-3:3000"]
    urls = {get_bridge_url(i, bridges) for i in range(10)}
    assert len(urls) > 1  # Not all same bridge
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_whatsapp_routing.py -v`
Expected: FAIL — `get_bridge_url` not found

**Step 3: Rewrite WhatsApp messenger with pool and routing**

```python
# app/messengers/whatsapp.py
import httpx

from app.messengers.base import BaseMessenger


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
                return {"ok": False, "error": response.text}
            return {"ok": True}
        except httpx.HTTPError as e:
            return {"ok": False, "error": str(e)}

    async def get_groups(self) -> list[dict]:
        client = get_http_client()
        try:
            response = await client.get(self._url("groups"))
            if response.status_code == 200:
                return response.json()
            return []
        except httpx.HTTPError:
            return []

    async def check_connection(self) -> bool:
        client = get_http_client()
        try:
            response = await client.get(self._url("status"))
            return response.status_code == 200 and response.json().get("connected", False)
        except Exception:
            return False

    async def start_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.post(self._url("start"), timeout=30)
            return response.status_code == 200
        except Exception:
            return False

    async def destroy_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.delete(
                f"{self.bridge_url}/api/sessions/{self.session_id}"
            )
            return response.status_code == 200
        except Exception:
            return False

    async def get_qr(self) -> dict:
        client = get_http_client()
        try:
            response = await client.get(self._url("qr"))
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "qr": None}
        except Exception:
            return {"status": "error", "qr": None}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_whatsapp_routing.py -v`
Expected: PASS

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add app/messengers/whatsapp.py tests/test_whatsapp_routing.py
git commit -m "feat: add WA bridge routing and httpx connection pool"
```

---

### Task 6: Telegram connection pool

**Files:**
- Create: `app/messengers/telegram_pool.py`
- Test: `tests/test_telegram_pool.py`
- Modify: `app/messengers/telegram_user.py:141-154` (use pool in send_message)

**Step 1: Write the failing test**

```python
# tests/test_telegram_pool.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messengers.telegram_pool import TelegramPool


@pytest.mark.asyncio
async def test_pool_reuses_client():
    """Getting the same account_id twice returns the same client."""
    pool = TelegramPool()
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)

    with patch.object(pool, "_create_client", return_value=mock_client):
        client1 = await pool.get(account_id=1, session_string="s", api_id=1, api_hash="h")
        client2 = await pool.get(account_id=1, session_string="s", api_id=1, api_hash="h")

    assert client1 is client2  # Same object reused


@pytest.mark.asyncio
async def test_pool_disconnect_all():
    """disconnect_all cleans up all clients."""
    pool = TelegramPool()
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    mock_client.disconnect = AsyncMock()

    with patch.object(pool, "_create_client", return_value=mock_client):
        await pool.get(account_id=1, session_string="s", api_id=1, api_hash="h")

    await pool.disconnect_all()
    mock_client.disconnect.assert_called_once()
    assert len(pool._clients) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_telegram_pool.py -v`
Expected: FAIL — module not found

**Step 3: Implement Telegram pool**

```python
# app/messengers/telegram_pool.py
import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger(__name__)


class TelegramPool:
    """Maintains persistent TelegramClient connections per account."""

    def __init__(self):
        self._clients: dict[int, TelegramClient] = {}

    async def _create_client(
        self, session_string: str, api_id: int, api_hash: str
    ) -> TelegramClient:
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()
        return client

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

        client = await self._create_client(session_string, api_id, api_hash)
        self._clients[account_id] = client
        logger.info("Telegram pool: connected account %d", account_id)
        return client

    async def disconnect_all(self):
        """Disconnect all clients. Call on worker shutdown."""
        for account_id, client in self._clients.items():
            try:
                await client.disconnect()
                logger.info("Telegram pool: disconnected account %d", account_id)
            except Exception as e:
                logger.warning("Telegram pool: error disconnecting %d: %s", account_id, e)
        self._clients.clear()

    async def remove(self, account_id: int):
        """Remove and disconnect a single client."""
        client = self._clients.pop(account_id, None)
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_telegram_pool.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/messengers/telegram_pool.py tests/test_telegram_pool.py
git commit -m "feat: add Telegram connection pool for worker reuse"
```

---

### Task 7: Update messenger_factory for bridge routing

**Files:**
- Modify: `app/services/messenger_factory.py`
- Test: `tests/test_messenger_factory_routing.py`

**Step 1: Write the failing test**

```python
# tests/test_messenger_factory_routing.py
import pytest
from unittest.mock import MagicMock

from app.services.messenger_factory import create_messenger
from app.config import Settings


def test_create_whatsapp_messenger_uses_routing():
    """WhatsApp messenger gets bridge URL based on account.id % len(bridges)."""
    account = MagicMock()
    account.type = "wa"
    account.id = 5
    account.credentials = ""

    settings = MagicMock(spec=Settings)
    settings.wa_bridge_urls = [
        "http://bridge-0:3000",
        "http://bridge-1:3000",
        "http://bridge-2:3000",
    ]

    messenger = create_messenger(account, settings)
    # id=5 % 3 = 2 → bridge-2
    assert messenger.bridge_url == "http://bridge-2:3000"
    assert messenger.session_id == "5"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_messenger_factory_routing.py -v`
Expected: FAIL — factory doesn't use wa_bridge_urls

**Step 3: Update messenger_factory.py**

```python
# app/services/messenger_factory.py
from app.config import Settings
from app.messengers.base import BaseMessenger
from app.messengers.telegram_user import TelegramUserMessenger
from app.messengers.whatsapp import WhatsAppMessenger, get_bridge_url
from app.models.messenger_account import MessengerAccount


def create_messenger(account: MessengerAccount, settings: Settings) -> BaseMessenger:
    """Create appropriate messenger adapter based on account type."""
    if account.type == "tg_user":
        return TelegramUserMessenger(
            session_string=account.credentials,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
    elif account.type == "wa":
        bridge_url = get_bridge_url(account.id, settings.wa_bridge_urls)
        return WhatsAppMessenger(
            bridge_url=bridge_url,
            session_id=str(account.id),
        )
    else:
        raise ValueError(f"Unknown account type: {account.type}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_messenger_factory_routing.py -v`
Expected: PASS

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add app/services/messenger_factory.py tests/test_messenger_factory_routing.py
git commit -m "feat: route WhatsApp messages to bridge by session_id"
```

---

### Task 8: New Celery task architecture — send tasks with retry

**Files:**
- Modify: `app/worker/celery_app.py` (add queue config, beat interval)
- Modify: `app/worker/tasks.py` (full rewrite)
- Test: `tests/test_worker_tasks.py`

**Step 1: Write the failing test**

```python
# tests/test_worker_tasks.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.worker.tasks import dispatch_send_tasks


@pytest.mark.asyncio
async def test_dispatch_groups_wa_by_session(db_session):
    """WhatsApp tasks are dispatched to per-session queues."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(kw.get("queue"))

    with patch("app.worker.tasks.send_whatsapp_message", mock_task):
        with patch("app.worker.tasks.send_telegram_message", MagicMock()):
            await dispatch_send_tasks(
                session=db_session,
                tasks_to_dispatch=[
                    {"type": "wa", "ad_id": 1, "group_id": 10, "account_id": 5, "schedule_id": 1},
                    {"type": "wa", "ad_id": 2, "group_id": 20, "account_id": 5, "schedule_id": 2},
                    {"type": "wa", "ad_id": 3, "group_id": 30, "account_id": 7, "schedule_id": 3},
                ],
            )

    # Two tasks for session 5, one for session 7
    assert dispatched.count("whatsapp.session.5") == 2
    assert dispatched.count("whatsapp.session.7") == 1


@pytest.mark.asyncio
async def test_dispatch_telegram_to_telegram_queue(db_session):
    """Telegram tasks are dispatched to the 'telegram' queue."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(kw.get("queue"))

    with patch("app.worker.tasks.send_telegram_message", mock_task):
        with patch("app.worker.tasks.send_whatsapp_message", MagicMock()):
            await dispatch_send_tasks(
                session=db_session,
                tasks_to_dispatch=[
                    {"type": "tg_user", "ad_id": 1, "group_id": 10, "account_id": 3, "schedule_id": 1},
                ],
            )

    assert dispatched == ["telegram"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_worker_tasks.py -v`
Expected: FAIL — `dispatch_send_tasks` not found

**Step 3: Update celery_app.py — add queue config**

```python
# app/worker/celery_app.py
from celery import Celery


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
        # Default queue config
        task_default_queue="default",
        task_routes={
            "app.worker.tasks.send_telegram_message": {"queue": "telegram"},
            # WhatsApp tasks are routed dynamically per-session
        },
        beat_schedule={
            "check-schedules": {
                "task": "app.worker.tasks.check_schedules",
                "schedule": settings.celery_beat_interval,
            },
        },
        # Worker prefetch: 1 task at a time for fair distribution
        worker_prefetch_multiplier=1,
    )

    return app


celery_app = create_celery_app()
```

**Step 4: Rewrite tasks.py**

```python
# app/worker/tasks.py
import asyncio
import logging
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

logger = logging.getLogger(__name__)


async def dispatch_send_tasks(
    session: AsyncSession,
    tasks_to_dispatch: list[dict],
) -> None:
    """Dispatch individual Celery tasks for each send. Groups WA tasks by session."""
    for task_info in tasks_to_dispatch:
        account_id = task_info["account_id"]
        args = [task_info["ad_id"], task_info["group_id"], task_info["account_id"], task_info["schedule_id"]]

        if task_info["type"] == "wa":
            queue_name = f"whatsapp.session.{account_id}"
            send_whatsapp_message.apply_async(args=args, queue=queue_name)
        else:
            send_telegram_message.apply_async(args=args, queue="telegram")


async def check_schedules_async(session: AsyncSession):
    """Find all due schedules and dispatch individual send tasks."""
    now = datetime.now(timezone.utc)

    # Eager load ad and account to avoid N+1
    result = await session.execute(
        select(Schedule)
        .options(joinedload(Schedule.ad), joinedload(Schedule.account))
        .where(
            Schedule.is_active == True,
            Schedule.next_run_at <= now,
        )
    )
    schedules = result.unique().scalars().all()

    if not schedules:
        return

    # Collect tasks to dispatch and check billing per user (cached)
    tasks_to_dispatch = []
    checked_users: dict[int, tuple[bool, str]] = {}

    for schedule in schedules:
        ad = schedule.ad
        account = schedule.account

        if not ad or not account or account.status != "active":
            # Update next_run_at and skip
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name="UTC",
                now=now,
            )
            continue

        # Check billing limit (cached per user)
        user_id = ad.user_id
        if user_id not in checked_users:
            checked_users[user_id] = await check_limit_cached(session, user_id, "send")

        allowed, reason = checked_users[user_id]
        if not allowed:
            logger.info("User %d skipped: %s", user_id, reason)
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name="UTC",
                now=now,
            )
            continue

        # Create send task for each group
        for group_id in schedule.group_ids:
            tasks_to_dispatch.append({
                "type": account.type,
                "ad_id": schedule.ad_id,
                "group_id": group_id,
                "account_id": schedule.account_id,
                "schedule_id": schedule.id,
            })

        # Update next_run_at
        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name="UTC",
            now=now,
        )

    # Batch commit all next_run_at updates
    await session.commit()

    # Dispatch all send tasks
    if tasks_to_dispatch:
        await dispatch_send_tasks(session, tasks_to_dispatch)
        logger.info("Dispatched %d send tasks", len(tasks_to_dispatch))


async def _send_message(ad_id: int, group_id: int, account_id: int, schedule_id: int):
    """Shared send logic for both Telegram and WhatsApp tasks."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        ad = await session.get(Ad, ad_id)
        group = await session.get(Group, group_id)
        account = await session.get(MessengerAccount, account_id)

        if not ad or not group or not account:
            log = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="fail", error_message="Missing ad, group, or account",
            )
            session.add(log)
            await session.commit()
            return

        if account.status != "active":
            log = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="account_disconnected",
                error_message=f"Account {account.id} is {account.status}",
            )
            session.add(log)
            await session.commit()
            return

        # Build image URLs
        images = None
        if ad.images:
            s3_public_url = settings.s3_public_url
            images = [get_image_url(img, s3_public_url) for img in ad.images]

        # Send via messenger adapter
        messenger = create_messenger(account, settings)
        result = await messenger.send_message(
            group_id=group.group_external_id,
            text=ad.text,
            images=images,
        )

        log = SendLog(
            schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
            status="ok" if result["ok"] else "fail",
            error_message=result.get("error"),
        )
        session.add(log)
        await session.commit()

        if not result["ok"]:
            raise Exception(f"Send failed: {result.get('error')}")

    await engine.dispose()


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


@shared_task(name="app.worker.tasks.check_schedules")
def check_schedules():
    """Celery task: check all due schedules and dispatch individual send tasks."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        async with session_factory() as session:
            await check_schedules_async(session)
        await engine.dispose()

    asyncio.run(_run())
```

**Step 5: Run tests**

Run: `uv run pytest tests/test_worker_tasks.py -v`
Expected: PASS

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add app/worker/celery_app.py app/worker/tasks.py tests/test_worker_tasks.py
git commit -m "feat: distributed Celery tasks with retry, rate limiting, and WA session affinity"
```

---

### Task 9: WA bridge healthcheck endpoint

**Files:**
- Modify: `wa_bridge/index.js`

**Step 1: Add /health endpoint**

Add before the `main()` function in `wa_bridge/index.js` (before line 370):

```javascript
// GET /health - Health check for Docker
app.get('/health', (req, res) => {
    const sessionCount = sessions.size;
    const loadingCount = loadingPromises.size;
    res.json({
        status: 'ok',
        sessions: sessionCount,
        loading: loadingCount,
        uptime: process.uptime(),
    });
});
```

**Step 2: Verify manually**

Run: `curl http://localhost:3000/health` (when bridge is running)
Expected: `{"status":"ok","sessions":0,"loading":0,"uptime":...}`

**Step 3: Commit**

```bash
git add wa_bridge/index.js
git commit -m "feat: add /health endpoint to wa-bridge"
```

---

### Task 10: Docker Compose — scaled topology

**Files:**
- Modify: `docker-compose.yml` (full rewrite)
- Modify: `docker-compose.dev.yml` (update for new services)

**Step 1: Rewrite docker-compose.yml**

```yaml
# docker-compose.yml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    command: uv run uvicorn main:app --host 0.0.0.0 --port 8000
    container_name: web-broadcaster
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file: .env

  db:
    image: postgres:16-alpine
    container_name: db-broadcaster
    environment:
      POSTGRES_DB: broadcaster
      POSTGRES_USER: broadcaster
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-broadcaster}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U broadcaster"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis-broadcaster
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # --- Celery workers ---

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: celery-beat-broadcaster
    command: uv run celery -A app.worker.celery_app beat --loglevel=info
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file: .env

  celery-worker-telegram:
    build:
      context: .
      dockerfile: Dockerfile
    command: uv run celery -A app.worker.celery_app worker --loglevel=info --queues=telegram --concurrency=4
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file: .env
    deploy:
      replicas: 2

  celery-worker-whatsapp:
    build:
      context: .
      dockerfile: Dockerfile
    command: uv run celery -A app.worker.celery_app worker --loglevel=info --queues=whatsapp --concurrency=2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      wa-bridge-1:
        condition: service_healthy
    env_file: .env
    deploy:
      replicas: 2

  celery-worker-default:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: celery-worker-default-broadcaster
    command: uv run celery -A app.worker.celery_app worker --loglevel=info --queues=default --concurrency=2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file: .env

  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flower-broadcaster
    command: uv run celery -A app.worker.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      redis:
        condition: service_healthy
    env_file: .env

  # --- MongoDB ---

  mongo:
    image: mongo:7
    container_name: mongo-broadcaster
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 5s
      timeout: 5s
      retries: 5

  # --- WhatsApp bridges ---

  wa-bridge-1:
    build:
      context: ./wa_bridge
      dockerfile: Dockerfile
    container_name: wa-bridge-1-broadcaster
    depends_on:
      mongo:
        condition: service_healthy
    environment:
      - MONGODB_URI=mongodb://mongo:27017/whatsapp_sessions
      - PORT=3000
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G

  wa-bridge-2:
    build:
      context: ./wa_bridge
      dockerfile: Dockerfile
    container_name: wa-bridge-2-broadcaster
    depends_on:
      mongo:
        condition: service_healthy
    environment:
      - MONGODB_URI=mongodb://mongo:27017/whatsapp_sessions
      - PORT=3000
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G

  wa-bridge-3:
    build:
      context: ./wa_bridge
      dockerfile: Dockerfile
    container_name: wa-bridge-3-broadcaster
    depends_on:
      mongo:
        condition: service_healthy
    environment:
      - MONGODB_URI=mongodb://mongo:27017/whatsapp_sessions
      - PORT=3000
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G

volumes:
  pgdata:
  mongodata:
```

**Step 2: Update .env — add WA_BRIDGE_URLS**

Add to `.env`:
```
WA_BRIDGE_URLS=["http://wa-bridge-1:3000","http://wa-bridge-2:3000","http://wa-bridge-3:3000"]
```

**Step 3: Update docker-compose.dev.yml**

```yaml
# docker-compose.dev.yml
services:
  web:
    command: uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    environment:
      - DEBUG=true

  celery-worker-telegram:
    command: uv run celery -A app.worker.celery_app worker --loglevel=debug --queues=telegram --concurrency=2
    volumes:
      - .:/app
    deploy:
      replicas: 1

  celery-worker-whatsapp:
    command: uv run celery -A app.worker.celery_app worker --loglevel=debug --queues=whatsapp --concurrency=1
    volumes:
      - .:/app
    deploy:
      replicas: 1

  celery-worker-default:
    command: uv run celery -A app.worker.celery_app worker --loglevel=debug --queues=default --concurrency=1
    volumes:
      - .:/app

  celery-beat:
    command: uv run celery -A app.worker.celery_app beat --loglevel=debug
    volumes:
      - .:/app

  wa-bridge-1:
    volumes:
      - ./wa_bridge:/app
      - /app/node_modules

  # Dev: only 1 bridge instead of 3
  wa-bridge-2:
    profiles: ["full"]

  wa-bridge-3:
    profiles: ["full"]
```

**Step 4: Commit**

```bash
git add docker-compose.yml docker-compose.dev.yml
git commit -m "feat: scaled Docker Compose with multiple workers and bridges"
```

---

### Task 11: Add flower dependency

**Step 1: Add flower package**

Run: `uv add flower`

**Step 2: Verify**

Run: `uv run celery -A app.worker.celery_app flower --help`
Expected: Shows flower help

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add flower for Celery monitoring"
```

---

### Task 12: Add redis async dependency for billing cache

**Step 1: Check if redis[hiredis] is already installed**

Run: `uv run python -c "import redis.asyncio; print('ok')"`

If FAIL:

Run: `uv add redis[hiredis]`

**Step 2: Verify**

Run: `uv run python -c "import redis.asyncio; print('ok')"`
Expected: `ok`

**Step 3: Commit (only if new dependency)**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add redis async client for billing cache"
```

---

### Task 13: WhatsApp worker dynamic queue consumption

**Files:**
- Create: `app/worker/wa_consumer.py`
- Test: `tests/test_wa_consumer.py`

**Step 1: Write the failing test**

```python
# tests/test_wa_consumer.py
import pytest
from unittest.mock import AsyncMock, patch

from app.worker.wa_consumer import get_active_wa_queues


@pytest.mark.asyncio
async def test_get_active_wa_queues_returns_queue_list():
    """Returns list of active WA queue names from Redis."""
    mock_redis = AsyncMock()
    mock_redis.smembers = AsyncMock(return_value={
        b"whatsapp.session.5",
        b"whatsapp.session.10",
    })

    with patch("app.worker.wa_consumer._get_redis", return_value=mock_redis):
        queues = await get_active_wa_queues()

    assert set(queues) == {"whatsapp.session.5", "whatsapp.session.10"}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_wa_consumer.py -v`
Expected: FAIL — module not found

**Step 3: Implement wa_consumer.py**

```python
# app/worker/wa_consumer.py
"""Dynamic queue discovery for WhatsApp session-affinity workers.

WhatsApp workers need to consume from dynamically-created queues
(whatsapp.session.{id}). This module handles discovering those queues.

Usage in celery worker startup:
    celery -A app.worker.celery_app worker --queues=whatsapp

The worker listens to the base 'whatsapp' queue. The check_schedules task
routes WA tasks to whatsapp.session.{id} queues. Celery workers configured
with --queues=whatsapp will also pick up tasks from queues matching the
'whatsapp.*' pattern when task_create_missing_queues=True (default).
"""
import logging

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio
            from app.config import get_settings
            _redis_client = redis.asyncio.from_url(get_settings().redis_url)
        except Exception:
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
        logger.warning("Failed to get active WA queues: %s", e)
        return []


async def register_wa_queue(queue_name: str) -> None:
    """Register a WhatsApp session queue as active."""
    r = _get_redis()
    if r:
        try:
            await r.sadd("wa:active_queues", queue_name)
        except Exception:
            pass


async def unregister_wa_queue(queue_name: str) -> None:
    """Remove a WhatsApp session queue from active set."""
    r = _get_redis()
    if r:
        try:
            await r.srem("wa:active_queues", queue_name)
        except Exception:
            pass
```

**Step 4: Update dispatch_send_tasks in tasks.py to register queues**

In `app/worker/tasks.py`, update `dispatch_send_tasks`:

```python
async def dispatch_send_tasks(
    session: AsyncSession,
    tasks_to_dispatch: list[dict],
) -> None:
    """Dispatch individual Celery tasks for each send. Groups WA tasks by session."""
    from app.worker.wa_consumer import register_wa_queue

    for task_info in tasks_to_dispatch:
        account_id = task_info["account_id"]
        args = [task_info["ad_id"], task_info["group_id"], task_info["account_id"], task_info["schedule_id"]]

        if task_info["type"] == "wa":
            queue_name = f"whatsapp.session.{account_id}"
            await register_wa_queue(queue_name)
            send_whatsapp_message.apply_async(args=args, queue=queue_name)
        else:
            send_telegram_message.apply_async(args=args, queue="telegram")
```

**Step 5: Run tests**

Run: `uv run pytest tests/test_wa_consumer.py tests/test_worker_tasks.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add app/worker/wa_consumer.py tests/test_wa_consumer.py app/worker/tasks.py
git commit -m "feat: dynamic WA queue registration for session affinity"
```

---

### Task 14: Update celery_app.py for WA queue auto-creation

**Files:**
- Modify: `app/worker/celery_app.py`

**Step 1: Add task_create_missing_queues setting**

In `app/worker/celery_app.py`, add to `app.conf.update(...)`:

```python
# Allow dynamic queue creation for whatsapp.session.{id} queues
task_create_missing_queues=True,
```

**Step 2: Verify by running worker**

Run: `uv run celery -A app.worker.celery_app worker --queues=whatsapp --loglevel=debug`
Expected: Worker starts, ready to consume from whatsapp queue

Ctrl+C to stop.

**Step 3: Commit**

```bash
git add app/worker/celery_app.py
git commit -m "feat: enable dynamic queue creation for WA session queues"
```

---

### Task 15: Run full test suite and verify

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests pass (157 original + new tests)

**Step 2: Run with coverage**

Run: `uv run pytest tests/ --cov=app --cov-report=term-missing`
Expected: Coverage report shows worker and messenger modules covered

**Step 3: Final commit if needed**

Fix any issues found during testing.

---

### Summary of changes

| Task | Component | Files changed |
|------|-----------|---------------|
| 1 | DB indexes | 4 models + migration |
| 2 | Schedule relationships | schedule.py + test |
| 3 | Config settings | config.py, conftest.py |
| 4 | Billing cache | billing_cache.py + test |
| 5 | WA httpx pool + routing | whatsapp.py + test |
| 6 | Telegram pool | telegram_pool.py + test |
| 7 | Messenger factory routing | messenger_factory.py + test |
| 8 | Celery tasks | celery_app.py, tasks.py + test |
| 9 | WA bridge healthcheck | wa_bridge/index.js |
| 10 | Docker Compose | docker-compose.yml, dev.yml |
| 11 | Flower dep | pyproject.toml |
| 12 | Redis dep | pyproject.toml |
| 13 | WA queue consumer | wa_consumer.py + test |
| 14 | Queue auto-creation | celery_app.py |
| 15 | Full test verification | — |

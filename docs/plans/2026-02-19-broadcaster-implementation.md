# Broadcaster Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a SaaS product that sends product advertisements to Telegram and WhatsApp groups on a schedule.

**Architecture:** Modular Python monolith (FastAPI + Celery) with a separate Node.js WhatsApp bridge. PostgreSQL for data, Redis for task queue. Docker Compose for deployment.

**Tech Stack:** FastAPI, SQLAlchemy (async), Celery, Pyrogram, aiogram, Jinja2+HTMX+Tailwind, whatsapp-web.js (Node.js), PostgreSQL, Redis

---

## Phase 1: Foundation

### Task 1: Install Python dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add all Python dependencies**

```bash
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic celery[redis] \
  pyrogram tgcrypto aiogram jinja2 pydantic-settings python-jose[cryptography] \
  passlib[bcrypt] httpx pillow python-multipart aiofiles
```

**Step 2: Add dev dependencies**

```bash
uv add --dev pytest pytest-asyncio httpx pytest-cov factory-boy
```

**Step 3: Verify installation**

```bash
uv run python -c "import fastapi; import sqlalchemy; import celery; print('OK')"
```
Expected: `OK`

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add project dependencies"
```

---

### Task 2: App config and settings

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `.env.example`
- Test: `tests/__init__.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Create `tests/__init__.py` (empty) and `tests/test_config.py`:

```python
from app.config import Settings


def test_settings_defaults():
    s = Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
    )
    assert s.app_name == "Broadcaster"
    assert s.database_url == "postgresql+asyncpg://u:p@localhost/db"
    assert s.secret_key == "test-secret"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

**Step 3: Write implementation**

Create `app/__init__.py` (empty).

Create `app/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Broadcaster"
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # File uploads
    upload_dir: str = "uploads"
    max_image_size_mb: int = 5
    max_images_per_ad: int = 10

    # WA Bridge
    wa_bridge_url: str = "http://wa-bridge:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
```

Create `.env.example`:

```
DATABASE_URL=postgresql+asyncpg://broadcaster:broadcaster@localhost:5432/broadcaster
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
WA_BRIDGE_URL=http://wa-bridge:3000
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_config.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add app/ tests/ .env.example
git commit -m "feat: add app config with pydantic-settings"
```

---

### Task 3: Database setup (SQLAlchemy async)

**Files:**
- Create: `app/database.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing test**

```python
import pytest
from app.database import Base, get_engine


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_engine_returns_engine():
    engine = get_engine("sqlite+aiosqlite:///test.db")
    assert engine is not None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_database.py -v
```
Expected: FAIL

**Step 3: Add aiosqlite for testing, then write implementation**

```bash
uv add --dev aiosqlite
```

Create `app/database.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def get_engine(database_url: str):
    return create_async_engine(database_url, echo=False)


def get_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_database.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add app/database.py tests/test_database.py
git commit -m "feat: add async SQLAlchemy database setup"
```

---

### Task 4: User model

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/user.py`
- Test: `tests/test_models/__init__.py`
- Test: `tests/test_models/test_user.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(email="test@example.com", password_hash="hashed", name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.timezone == "UTC"
    assert user.created_at is not None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_user.py -v
```
Expected: FAIL

**Step 3: Write implementation**

Create `app/models/__init__.py`:

```python
from app.models.user import User

__all__ = ["User"]
```

Create `app/models/user.py`:

```python
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_models/test_user.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/ tests/test_models/
git commit -m "feat: add User model"
```

---

### Task 5: Subscription model

**Files:**
- Create: `app/models/subscription.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_models/test_subscription.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.subscription import Subscription


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_subscription(db_session):
    user = User(email="test@example.com", password_hash="hashed", name="Test")
    db_session.add(user)
    await db_session.commit()

    sub = Subscription(
        user_id=user.id,
        plan="basic",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    assert sub.id is not None
    assert sub.plan == "basic"
    assert sub.is_active is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_subscription.py -v
```

**Step 3: Write implementation**

Create `app/models/subscription.py`:

```python
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free, basic, pro
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Update `app/models/__init__.py`:

```python
from app.models.user import User
from app.models.subscription import Subscription

__all__ = ["User", "Subscription"]
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_models/test_subscription.py -v
```

**Step 5: Commit**

```bash
git add app/models/ tests/test_models/test_subscription.py
git commit -m "feat: add Subscription model"
```

---

### Task 6: MessengerAccount model

**Files:**
- Create: `app/models/messenger_account.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_models/test_messenger_account.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_messenger_account(db_session):
    user = User(email="test@example.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    account = MessengerAccount(
        user_id=user.id,
        type="tg_bot",
        credentials="encrypted-token",
        status="active",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    assert account.id is not None
    assert account.type == "tg_bot"
    assert account.status == "active"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_messenger_account.py -v
```

**Step 3: Write implementation**

Create `app/models/messenger_account.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessengerAccount(Base):
    __tablename__ = "messenger_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(20))  # tg_bot, tg_user, wa
    credentials: Mapped[str] = mapped_column(Text)  # encrypted
    session_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted
    status: Mapped[str] = mapped_column(String(20), default="disconnected")  # active, disconnected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Update `app/models/__init__.py` to add `MessengerAccount`.

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_models/test_messenger_account.py -v
```

**Step 5: Commit**

```bash
git add app/models/ tests/test_models/test_messenger_account.py
git commit -m "feat: add MessengerAccount model"
```

---

### Task 7: Ad model

**Files:**
- Create: `app/models/ad.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_models/test_ad.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import JSON
from app.database import Base
from app.models.user import User
from app.models.ad import Ad


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_ad(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    ad = Ad(
        user_id=user.id,
        title="iPhone 15",
        text="Selling iPhone 15, like new",
        images=["uploads/img1.jpg", "uploads/img2.jpg"],
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    assert ad.id is not None
    assert ad.title == "iPhone 15"
    assert ad.images == ["uploads/img1.jpg", "uploads/img2.jpg"]
    assert ad.is_active is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_ad.py -v
```

**Step 3: Write implementation**

Create `app/models/ad.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    images: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Update `app/models/__init__.py` to add `Ad`.

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_models/test_ad.py -v
```

**Step 5: Commit**

```bash
git add app/models/ tests/test_models/test_ad.py
git commit -m "feat: add Ad model"
```

---

### Task 8: Group model

**Files:**
- Create: `app/models/group.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_models/test_group.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.messenger_account import MessengerAccount
from app.models.group import Group


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_group(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    account = MessengerAccount(user_id=user.id, type="tg_bot", credentials="tok", status="active")
    db_session.add(account)
    await db_session.commit()

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="telegram",
        group_external_id="-100123456789",
        name="Sales Group",
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    assert group.id is not None
    assert group.group_external_id == "-100123456789"
    assert group.is_active is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_group.py -v
```

**Step 3: Write implementation**

Create `app/models/group.py`:

```python
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("messenger_accounts.id", ondelete="CASCADE"))
    messenger_type: Mapped[str] = mapped_column(String(20))  # telegram, whatsapp
    group_external_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Update `app/models/__init__.py` to add `Group`.

**Step 4: Run test, commit**

```bash
uv run pytest tests/test_models/test_group.py -v
git add app/models/ tests/test_models/test_group.py
git commit -m "feat: add Group model"
```

---

### Task 9: Schedule model

**Files:**
- Create: `app/models/schedule.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_models/test_schedule.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from datetime import datetime, timezone, time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_schedule(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    ad = Ad(user_id=user.id, title="Test", text="Text", images=[])
    account = MessengerAccount(user_id=user.id, type="tg_bot", credentials="tok", status="active")
    db_session.add_all([ad, account])
    await db_session.commit()

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[1, 2, 3],
        days_of_week=[0, 1, 2, 3, 4],  # Mon-Fri
        times_of_day=["09:00", "18:00"],
        next_run_at=datetime.now(timezone.utc),
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.id is not None
    assert schedule.days_of_week == [0, 1, 2, 3, 4]
    assert schedule.times_of_day == ["09:00", "18:00"]
    assert schedule.is_active is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_schedule.py -v
```

**Step 3: Write implementation**

Create `app/models/schedule.py`:

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("messenger_accounts.id", ondelete="CASCADE"))
    group_ids: Mapped[list] = mapped_column(JSON, default=list)  # list of group IDs
    days_of_week: Mapped[list] = mapped_column(JSON, default=list)  # 0=Mon, 6=Sun
    times_of_day: Mapped[list] = mapped_column(JSON, default=list)  # ["09:00", "18:00"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Update `app/models/__init__.py` to add `Schedule`.

**Step 4: Run test, commit**

```bash
uv run pytest tests/test_models/test_schedule.py -v
git add app/models/ tests/test_models/test_schedule.py
git commit -m "feat: add Schedule model"
```

---

### Task 10: SendLog model

**Files:**
- Create: `app/models/send_log.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_models/test_send_log.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_send_log(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    ad = Ad(user_id=user.id, title="Test", text="Text", images=[])
    account = MessengerAccount(user_id=user.id, type="tg_bot", credentials="tok", status="active")
    db_session.add_all([ad, account])
    await db_session.commit()

    group = Group(user_id=user.id, account_id=account.id, messenger_type="telegram",
                  group_external_id="-100123", name="G")
    schedule = Schedule(ad_id=ad.id, account_id=account.id, group_ids=[],
                        days_of_week=[], times_of_day=[],
                        next_run_at=datetime.now(timezone.utc))
    db_session.add_all([group, schedule])
    await db_session.commit()

    log = SendLog(
        schedule_id=schedule.id,
        ad_id=ad.id,
        group_id=group.id,
        status="ok",
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.id is not None
    assert log.status == "ok"
    assert log.error_message is None
    assert log.sent_at is not None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models/test_send_log.py -v
```

**Step 3: Write implementation**

Create `app/models/send_log.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SendLog(Base):
    __tablename__ = "send_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id", ondelete="CASCADE"))
    ad_id: Mapped[int] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20))  # ok, fail, account_disconnected
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Update `app/models/__init__.py` to add `SendLog`.

**Step 4: Run ALL model tests**

```bash
uv run pytest tests/test_models/ -v
```
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/models/ tests/test_models/test_send_log.py
git commit -m "feat: add SendLog model — all data models complete"
```

---

### Task 11: Alembic setup + initial migration

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/` (directory)

**Step 1: Initialize alembic**

```bash
uv run alembic init alembic
```

**Step 2: Edit `alembic/env.py`**

Replace the `target_metadata` line and configure async:

```python
# At the top, add:
from app.database import Base
from app.models import User, Subscription, MessengerAccount, Ad, Group, Schedule, SendLog

# Set target_metadata:
target_metadata = Base.metadata
```

Configure the `run_migrations_online` function for async (SQLAlchemy async pattern). Use `connectable = create_async_engine(config.get_main_option("sqlalchemy.url"))`.

**Step 3: Edit `alembic.ini`**

Set `sqlalchemy.url`:
```ini
sqlalchemy.url = postgresql+asyncpg://broadcaster:broadcaster@localhost:5432/broadcaster
```

**Step 4: Commit**

```bash
git add alembic.ini alembic/
git commit -m "feat: initialize Alembic for database migrations"
```

---

### Task 12: FastAPI app factory + health check

**Files:**
- Modify: `app/main.py` (create new, replace old `main.py` at root)
- Test: `tests/test_main.py`

**Step 1: Write the failing test**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.mark.asyncio
async def test_health_check():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_main.py -v
```

**Step 3: Write implementation**

Create `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app
```

Remove or replace root `main.py`:

```python
import uvicorn
from app.main import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_main.py -v
```

**Step 5: Commit**

```bash
git add app/main.py main.py tests/test_main.py
git commit -m "feat: add FastAPI app factory with health check"
```

---

## Phase 2: Authentication

### Task 13: Auth service (password hashing + JWT)

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/auth_service.py`
- Test: `tests/test_services/__init__.py`
- Test: `tests/test_services/test_auth_service.py`

**Step 1: Write the failing test**

```python
import pytest
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(user_id=42, secret_key="test-secret")
    payload = decode_access_token(token, secret_key="test-secret")
    assert payload["sub"] == 42


def test_decode_invalid_token():
    payload = decode_access_token("invalid-token", secret_key="test-secret")
    assert payload is None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_services/test_auth_service.py -v
```

**Step 3: Write implementation**

Create `app/services/__init__.py` (empty).

Create `app/services/auth_service.py`:

```python
from datetime import datetime, timezone, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, secret_key: str, expires_minutes: int = 1440) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_services/test_auth_service.py -v
```

**Step 5: Commit**

```bash
git add app/services/ tests/test_services/
git commit -m "feat: add auth service (password hashing + JWT)"
```

---

### Task 14: Auth routes (register + login)

**Files:**
- Create: `app/routes/__init__.py`
- Create: `app/routes/auth.py`
- Create: `app/dependencies.py`
- Test: `tests/test_routes/__init__.py`
- Test: `tests/test_routes/test_auth.py`

**Step 1: Write the failing test**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.main import create_app
from app.dependencies import get_db, get_settings
from app.config import Settings


@pytest_asyncio.fixture
async def test_settings():
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
    )


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session, test_settings):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "strongpass123",
        "name": "Test User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@test.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/auth/register", json={
        "email": "dup@test.com", "password": "pass123", "name": "A",
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@test.com", "password": "pass123", "name": "B",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/auth/register", json={
        "email": "login@test.com", "password": "pass123", "name": "A",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@test.com", "password": "pass123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "wrong@test.com", "password": "pass123", "name": "A",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrong@test.com", "password": "wrongpass",
    })
    assert response.status_code == 401
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_routes/test_auth.py -v
```

**Step 3: Write implementation**

Create `app/dependencies.py`:

```python
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)

# These will be overridden by app startup or tests
_settings: Settings | None = None
_session_factory = None


def get_settings() -> Settings:
    if _settings is None:
        return Settings()
    return _settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    async with _session_factory() as session:
        yield session


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> int:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials, settings.secret_key)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload["sub"]
```

Create `app/routes/__init__.py` (empty).

Create `app/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_settings
from app.config import Settings
from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id, settings.secret_key, settings.access_token_expire_minutes)
    return TokenResponse(access_token=token)
```

Update `app/main.py` to include the auth router:

```python
from fastapi import FastAPI
from app.routes.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0")
    app.include_router(auth_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app
```

Also add `email-validator` dependency:

```bash
uv add email-validator
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_routes/test_auth.py -v
```

**Step 5: Commit**

```bash
git add app/ tests/ pyproject.toml uv.lock
git commit -m "feat: add auth routes (register + login with JWT)"
```

---

## Phase 3: Core CRUD Features

### Task 15: Ads CRUD routes

**Files:**
- Create: `app/routes/ads.py`
- Test: `tests/test_routes/test_ads.py`

Implement REST endpoints:
- `POST /api/ads` — create ad (title, text, images)
- `GET /api/ads` — list user's ads
- `GET /api/ads/{id}` — get single ad
- `PUT /api/ads/{id}` — update ad
- `DELETE /api/ads/{id}` — delete ad

All endpoints require auth (`get_current_user_id` dependency). Tests follow same pattern as Task 14 — create user, get token, use token for requests. Use test fixtures from a shared `tests/conftest.py` (extract the common db_session/client fixtures from Task 14 into conftest).

**Step 1:** Extract common fixtures into `tests/conftest.py`
**Step 2:** Write failing tests for all 5 endpoints
**Step 3:** Implement `app/routes/ads.py`
**Step 4:** Register router in `app/main.py`
**Step 5:** Run tests, commit

---

### Task 16: Image upload endpoint

**Files:**
- Create: `app/routes/uploads.py`
- Test: `tests/test_routes/test_uploads.py`

Implement `POST /api/uploads/image` — accepts multipart file, validates it's an image, saves to `uploads/` dir, returns the file path. Uses `Pillow` for validation.

**Step 1:** Write failing test (upload a valid image, upload an invalid file)
**Step 2:** Implement upload route
**Step 3:** Register in `app/main.py`, run tests, commit

---

### Task 17: Messenger accounts CRUD routes

**Files:**
- Create: `app/routes/accounts.py`
- Test: `tests/test_routes/test_accounts.py`

Implement:
- `POST /api/accounts` — add messenger account (type + credentials)
- `GET /api/accounts` — list user's accounts
- `DELETE /api/accounts/{id}` — remove account
- `GET /api/accounts/{id}/status` — check account connection status

**Step 1-5:** Same TDD pattern.

---

### Task 18: Groups CRUD routes

**Files:**
- Create: `app/routes/groups.py`
- Test: `tests/test_routes/test_groups.py`

Implement:
- `POST /api/groups` — add group manually
- `GET /api/groups` — list user's groups
- `POST /api/groups/sync/{account_id}` — sync groups from messenger account (fetches list of groups the bot/user is in)
- `DELETE /api/groups/{id}` — remove group

**Step 1-5:** Same TDD pattern.

---

### Task 19: Schedules CRUD routes

**Files:**
- Create: `app/routes/schedules.py`
- Create: `app/services/schedule_service.py`
- Test: `tests/test_routes/test_schedules.py`
- Test: `tests/test_services/test_schedule_service.py`

Implement:
- `POST /api/schedules` — create schedule (ad_id, group_ids, days_of_week, times_of_day, account_id)
- `GET /api/schedules` — list user's schedules
- `PUT /api/schedules/{id}` — update schedule
- `DELETE /api/schedules/{id}` — delete schedule
- `POST /api/schedules/{id}/toggle` — enable/disable schedule

`schedule_service.py` contains `compute_next_run_at(days_of_week, times_of_day, timezone, now)` — calculates the next scheduled run time. This is critical logic and must be well tested.

**Step 1:** Write tests for `compute_next_run_at` with multiple scenarios (today later, tomorrow, next week, weekend skip)
**Step 2:** Implement `schedule_service.py`
**Step 3:** Write tests for schedule routes
**Step 4:** Implement schedule routes
**Step 5:** Run all tests, commit

---

### Task 20: Send history routes

**Files:**
- Create: `app/routes/history.py`
- Test: `tests/test_routes/test_history.py`

Implement:
- `GET /api/history` — list send logs for current user (paginated, with filters by date/status)
- `GET /api/history/stats` — summary stats (total sent, success rate, last 24h)

**Step 1-5:** Same TDD pattern.

---

## Phase 4: Messenger Adapters

### Task 21: Base messenger adapter interface

**Files:**
- Create: `app/messengers/__init__.py`
- Create: `app/messengers/base.py`

Define abstract base class:

```python
from abc import ABC, abstractmethod


class BaseMessenger(ABC):
    @abstractmethod
    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        """Send message to group. Returns {"ok": True} or {"ok": False, "error": "..."}"""
        pass

    @abstractmethod
    async def get_groups(self) -> list[dict]:
        """Returns list of groups: [{"id": "...", "name": "..."}]"""
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """Check if account is connected and working."""
        pass
```

**Step 1:** Create the base class
**Step 2:** Commit

---

### Task 22: Telegram bot adapter

**Files:**
- Create: `app/messengers/telegram_bot.py`
- Test: `tests/test_messengers/test_telegram_bot.py`

Implement `TelegramBotMessenger(BaseMessenger)` using `aiogram`. Use mocks in tests (don't call real Telegram API).

**Step 1:** Write tests with mocked aiogram Bot
**Step 2:** Implement adapter
**Step 3:** Run tests, commit

---

### Task 23: Telegram userbot adapter

**Files:**
- Create: `app/messengers/telegram_user.py`
- Test: `tests/test_messengers/test_telegram_user.py`

Implement `TelegramUserMessenger(BaseMessenger)` using `Pyrogram`. Use mocks in tests.

**Step 1:** Write tests with mocked Pyrogram Client
**Step 2:** Implement adapter
**Step 3:** Run tests, commit

---

### Task 24: WhatsApp adapter (HTTP client to WA Bridge)

**Files:**
- Create: `app/messengers/whatsapp.py`
- Test: `tests/test_messengers/test_whatsapp.py`

Implement `WhatsAppMessenger(BaseMessenger)` using `httpx` to call the WA Bridge REST API. Use `httpx` mock/respx in tests.

**Step 1:** Write tests with mocked HTTP responses
**Step 2:** Implement adapter
**Step 3:** Run tests, commit

---

## Phase 5: Celery Workers

### Task 25: Celery app setup

**Files:**
- Create: `app/worker/__init__.py`
- Create: `app/worker/celery_app.py`

```python
from celery import Celery
from app.config import Settings

settings = Settings()

celery_app = Celery(
    "broadcaster",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-schedules": {
            "task": "app.worker.tasks.check_schedules",
            "schedule": 60.0,  # every minute
        },
    },
)
```

**Step 1:** Create celery app config
**Step 2:** Commit

---

### Task 26: Send task implementation

**Files:**
- Create: `app/worker/tasks.py`
- Test: `tests/test_worker/test_tasks.py`

Implement two Celery tasks:

1. `check_schedules()` — queries Schedule table for due schedules, dispatches `send_ad_to_group` for each group
2. `send_ad_to_group(schedule_id, ad_id, group_id, account_id)` — loads messenger adapter, sends message, writes SendLog

Tests use mocked database and messenger adapters.

**Step 1:** Write tests for `check_schedules` (finds due schedules, dispatches tasks)
**Step 2:** Write tests for `send_ad_to_group` (sends message, logs result, handles errors)
**Step 3:** Implement both tasks
**Step 4:** Run tests, commit

---

## Phase 6: WhatsApp Bridge (Node.js)

### Task 27: WA Bridge service

**Files:**
- Create: `wa_bridge/package.json`
- Create: `wa_bridge/index.js`
- Create: `wa_bridge/Dockerfile`

Implement Express REST API:
- `POST /api/send` — send message to group `{group_id, text, image_url?}`
- `GET /api/groups` — list groups the WA account is in
- `GET /api/status` — connection status
- `GET /api/qr` — get QR code for authentication

Uses `whatsapp-web.js` for WhatsApp connection. Stores session data in a volume.

**Step 1:** Initialize Node.js project, install dependencies
**Step 2:** Implement Express server with whatsapp-web.js
**Step 3:** Create Dockerfile
**Step 4:** Commit

---

## Phase 7: Docker & Infrastructure

### Task 28: Dockerfiles and docker-compose

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `docker-compose.dev.yml`

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: broadcaster
      POSTGRES_USER: broadcaster
      POSTGRES_PASSWORD: broadcaster
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file: .env
    volumes:
      - uploads:/app/uploads

  celery-worker:
    build: .
    command: celery -A app.worker.celery_app worker --loglevel=info
    depends_on:
      - db
      - redis
    env_file: .env

  celery-beat:
    build: .
    command: celery -A app.worker.celery_app beat --loglevel=info
    depends_on:
      - db
      - redis
    env_file: .env

  wa-bridge:
    build: ./wa_bridge
    ports:
      - "3000:3000"
    volumes:
      - wa_session:/app/.wwebjs_auth

volumes:
  pgdata:
  uploads:
  wa_session:
```

**Step 1:** Create Python Dockerfile
**Step 2:** Create docker-compose.yml
**Step 3:** Create docker-compose.dev.yml (with volume mounts for live reload)
**Step 4:** Test `docker compose config`
**Step 5:** Commit

---

## Phase 8: UI Templates

### Task 29: Base layout + TailwindCSS setup

**Files:**
- Create: `app/templates/base.html`
- Create: `app/templates/components/nav.html`
- Create: `app/static/css/input.css` (Tailwind input)

Set up Jinja2 base template with TailwindCSS CDN (for simplicity in MVP), HTMX, sidebar navigation.

**Step 1:** Create base.html with Tailwind CDN + HTMX
**Step 2:** Create nav component with links to all screens
**Step 3:** Configure Jinja2 templates in `app/main.py`
**Step 4:** Commit

---

### Task 30: Auth pages (login + register)

**Files:**
- Create: `app/templates/auth/login.html`
- Create: `app/templates/auth/register.html`
- Create: `app/routes/pages.py`

Server-rendered login/register forms. On success, store JWT in cookie and redirect to dashboard.

**Step 1-4:** Create templates, add page routes, commit

---

### Task 31: Dashboard page

**Files:**
- Create: `app/templates/dashboard.html`

Shows: active ads count, connected accounts status, next scheduled send, recent send log entries.

**Step 1-4:** Create template, add route, commit

---

### Task 32: Ads management pages

**Files:**
- Create: `app/templates/ads/list.html`
- Create: `app/templates/ads/form.html`

List of ads with create/edit/delete. Form with text editor + image upload (drag & drop). HTMX for inline operations.

**Step 1-4:** Create templates, commit

---

### Task 33: Accounts management page

**Files:**
- Create: `app/templates/accounts/list.html`
- Create: `app/templates/accounts/connect_tg_bot.html`
- Create: `app/templates/accounts/connect_tg_user.html`
- Create: `app/templates/accounts/connect_wa.html`

Forms for connecting each account type. WA page shows QR code fetched from WA Bridge.

**Step 1-4:** Create templates, commit

---

### Task 34: Groups management page

**Files:**
- Create: `app/templates/groups/list.html`

List of groups with sync button. Toggle active/inactive.

**Step 1-4:** Create template, commit

---

### Task 35: Schedule management pages

**Files:**
- Create: `app/templates/schedules/list.html`
- Create: `app/templates/schedules/form.html`

Form: select ad, select groups (multi-select), pick days of week (checkboxes), pick times (time inputs, add multiple). Toggle enable/disable.

**Step 1-4:** Create templates, commit

---

### Task 36: Send history page

**Files:**
- Create: `app/templates/history/list.html`

Paginated table with filters by date/status. Shows ad title, group name, status, timestamp, error message.

**Step 1-4:** Create template, commit

---

## Phase 9: Billing

### Task 37: Subscription plans and billing service

**Files:**
- Create: `app/services/billing_service.py`
- Test: `tests/test_services/test_billing_service.py`

Define plan limits:

```python
PLANS = {
    "free": {"max_ads": 3, "max_groups": 5, "max_sends_per_day": 10},
    "basic": {"max_ads": 20, "max_groups": 50, "max_sends_per_day": 200},
    "pro": {"max_ads": 100, "max_groups": 500, "max_sends_per_day": 2000},
}
```

Functions: `check_limit(user_id, action)`, `get_usage(user_id)`, `get_plan_limits(plan)`.

**Step 1:** Write tests for limit checking
**Step 2:** Implement billing service
**Step 3:** Run tests, commit

---

### Task 38: Billing routes and page

**Files:**
- Create: `app/routes/billing.py`
- Create: `app/templates/billing/plans.html`

Show current plan, usage stats, upgrade options. Payment integration can be added later — for now, plan management via admin.

**Step 1-4:** Implement routes, templates, commit

---

## Phase 10: Final Integration

### Task 39: Integrate limit checks into send flow

**Files:**
- Modify: `app/worker/tasks.py`
- Modify: `app/routes/ads.py`
- Modify: `app/routes/schedules.py`

Add billing limit checks to:
- Creating ads (check max_ads)
- Creating schedules (check max_groups)
- Sending messages (check max_sends_per_day)

**Step 1:** Write tests for limit enforcement
**Step 2:** Add checks, run tests, commit

---

### Task 40: End-to-end smoke test

**Files:**
- Create: `tests/test_e2e.py`

Test full flow: register → create ad → connect account → add group → create schedule → verify task dispatching (with mocked messengers).

**Step 1:** Write E2E test
**Step 2:** Run full test suite
**Step 3:** Commit

---

### Task 41: Final cleanup and README

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

Update README with setup instructions, architecture overview, and usage guide. Update CLAUDE.md with full command reference.

**Step 1:** Write docs, commit

---

**Total: 41 tasks across 10 phases.**

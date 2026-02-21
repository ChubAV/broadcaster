# Full Project Refactoring — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the Broadcaster codebase to eliminate code duplication, add proper layering (repositories, services), split the 1219-line pages.py, and unify error handling — while keeping all 138 tests green at every step.

**Architecture:** Bottom-up refactoring in 5 phases: (1) infrastructure (settings singleton, exceptions, logging), (2) repository layer for all models, (3) service layer (authorization, messenger factory), (4) route refactoring (API routes use repos, pages.py split into package), (5) cleanup. Each phase ends with a commit and green tests.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, pytest-asyncio, uv

---

## Phase 1: Infrastructure

### Task 1: Settings Singleton

**Files:**
- Modify: `app/config.py`
- Modify: `app/dependencies.py`
- Test: `tests/test_config.py` (existing tests must still pass)

**Step 1: Make get_settings() use lru_cache in config.py**

Replace `app/config.py` lines 33-34:

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 2: Update dependencies.py to import from config instead of recreating**

Replace `app/dependencies.py` lines 5,18-19:

```python
from app.config import get_settings
```

Remove the duplicate `get_settings` function from dependencies.py (lines 18-19). Import it from config instead.

**Step 3: Run tests to verify nothing broke**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 138 passed

**Step 4: Commit**

```bash
git add app/config.py app/dependencies.py
git commit -m "refactor: make Settings a singleton via lru_cache"
```

---

### Task 2: Custom Exceptions

**Files:**
- Create: `app/exceptions.py`
- Modify: `app/main.py`
- Create: `tests/test_exceptions.py`

**Step 1: Write tests for custom exceptions**

Create `tests/test_exceptions.py`:

```python
import pytest
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError


def test_not_found_error_message():
    err = NotFoundError("Ad", 42)
    assert str(err) == "Ad not found"
    assert err.resource == "Ad"
    assert err.resource_id == 42


def test_forbidden_error_message():
    err = ForbiddenError("Not allowed")
    assert str(err) == "Not allowed"


def test_billing_limit_error_message():
    err = BillingLimitError("Ad limit reached (3 on free plan)")
    assert str(err) == "Ad limit reached (3 on free plan)"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_exceptions.py -v`
Expected: FAIL (module not found)

**Step 3: Create app/exceptions.py**

```python
class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    """Resource not found or not accessible."""

    def __init__(self, resource: str, resource_id: int | None = None):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} not found")


class ForbiddenError(AppError):
    """Action not permitted."""


class BillingLimitError(AppError):
    """Plan limit exceeded."""


class MessengerConnectionError(AppError):
    """Messenger connection failed."""
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_exceptions.py -v`
Expected: 3 passed

**Step 5: Add exception handlers to main.py**

Add to `app/main.py` inside `create_app()`, after the router includes:

```python
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError, MessengerConnectionError
from fastapi import Request as FastAPIRequest
from fastapi.responses import JSONResponse

@app.exception_handler(NotFoundError)
async def not_found_handler(request: FastAPIRequest, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: FastAPIRequest, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.exception_handler(BillingLimitError)
async def billing_limit_handler(request: FastAPIRequest, exc: BillingLimitError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.exception_handler(MessengerConnectionError)
async def messenger_error_handler(request: FastAPIRequest, exc: MessengerConnectionError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})
```

**Step 6: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 141 passed (138 old + 3 new)

**Step 7: Commit**

```bash
git add app/exceptions.py app/main.py tests/test_exceptions.py
git commit -m "refactor: add custom exception classes with global handlers"
```

---

## Phase 2: Repository Layer

### Task 3: BaseRepository

**Files:**
- Create: `app/repositories/__init__.py`
- Create: `app/repositories/base.py`
- Create: `tests/test_repositories/__init__.py`
- Create: `tests/test_repositories/test_base.py`

**Step 1: Write tests for BaseRepository**

Create `tests/test_repositories/__init__.py` (empty) and `tests/test_repositories/test_base.py`:

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.user import User
from app.repositories.base import BaseRepository
from app.services.auth_service import hash_password


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    user = User(email="repo@test.com", password_hash=hash_password("pass"), name="Repo")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def ad_repo(db_session: AsyncSession) -> BaseRepository[Ad]:
    return BaseRepository(db_session, Ad)


@pytest.mark.asyncio
async def test_create(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    assert ad.id is not None
    assert ad.title == "Test"


@pytest.mark.asyncio
async def test_get_by_id(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    found = await ad_repo.get_by_id(ad.id)
    assert found is not None
    assert found.id == ad.id


@pytest.mark.asyncio
async def test_get_by_id_returns_none(ad_repo):
    found = await ad_repo.get_by_id(9999)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_and_user(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Test", text="Body")
    found = await ad_repo.get_by_id_and_user(ad.id, user.id)
    assert found is not None
    not_found = await ad_repo.get_by_id_and_user(ad.id, 9999)
    assert not_found is None


@pytest.mark.asyncio
async def test_list_by_user(ad_repo, user):
    await ad_repo.create(user_id=user.id, title="A1", text="Body")
    await ad_repo.create(user_id=user.id, title="A2", text="Body")
    items = await ad_repo.list_by_user(user.id)
    assert len(items) == 2


@pytest.mark.asyncio
async def test_update(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Old", text="Body")
    updated = await ad_repo.update(ad, title="New")
    assert updated.title == "New"


@pytest.mark.asyncio
async def test_delete(ad_repo, user):
    ad = await ad_repo.create(user_id=user.id, title="Del", text="Body")
    await ad_repo.delete(ad)
    assert await ad_repo.get_by_id(ad.id) is None


@pytest.mark.asyncio
async def test_count_by_user(ad_repo, user):
    await ad_repo.create(user_id=user.id, title="A1", text="Body")
    await ad_repo.create(user_id=user.id, title="A2", text="Body")
    assert await ad_repo.count_by_user(user.id) == 2
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_repositories/test_base.py -v`
Expected: FAIL (module not found)

**Step 3: Implement BaseRepository**

Create `app/repositories/__init__.py` (empty) and `app/repositories/base.py`:

```python
from typing import Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def get_by_id_and_user(self, id: int, user_id: int) -> T | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[T]:
        result = await self.session.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.id)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T, **kwargs) -> T:
        for field, value in kwargs.items():
            setattr(entity, field, value)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.commit()

    async def count_by_user(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(self.model.id)).where(
                self.model.user_id == user_id
            )
        )
        return result.scalar() or 0
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_repositories/test_base.py -v`
Expected: 8 passed

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 149 passed

**Step 6: Commit**

```bash
git add app/repositories/ tests/test_repositories/
git commit -m "refactor: add BaseRepository with generic CRUD operations"
```

---

### Task 4: Domain Repositories

**Files:**
- Create: `app/repositories/ad.py`
- Create: `app/repositories/account.py`
- Create: `app/repositories/group.py`
- Create: `app/repositories/schedule.py`
- Create: `app/repositories/send_log.py`
- Create: `app/repositories/user.py`

**Step 1: Create domain repositories with specific queries**

Create `app/repositories/ad.py`:

```python
from app.models.ad import Ad
from app.repositories.base import BaseRepository


class AdRepository(BaseRepository[Ad]):
    def __init__(self, session):
        super().__init__(session, Ad)
```

Create `app/repositories/user.py`:

```python
from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

Create `app/repositories/account.py`:

```python
from sqlalchemy import select

from app.models.messenger_account import MessengerAccount
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[MessengerAccount]):
    def __init__(self, session):
        super().__init__(session, MessengerAccount)

    async def get_by_type_and_status(
        self, user_id: int, account_type: str, status: str
    ) -> MessengerAccount | None:
        result = await self.session.execute(
            select(MessengerAccount).where(
                MessengerAccount.user_id == user_id,
                MessengerAccount.type == account_type,
                MessengerAccount.status == status,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_type_and_status(
        self, user_id: int, account_type: str, status: str
    ) -> list[MessengerAccount]:
        result = await self.session.execute(
            select(MessengerAccount).where(
                MessengerAccount.user_id == user_id,
                MessengerAccount.type == account_type,
                MessengerAccount.status == status,
            )
        )
        return list(result.scalars().all())
```

Create `app/repositories/group.py`:

```python
from sqlalchemy import select

from app.models.group import Group
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, session):
        super().__init__(session, Group)

    async def list_by_account(self, account_id: int, user_id: int) -> list[Group]:
        result = await self.session.execute(
            select(Group).where(
                Group.account_id == account_id,
                Group.user_id == user_id,
            ).order_by(Group.id)
        )
        return list(result.scalars().all())

    async def get_external_ids(self, account_id: int, user_id: int) -> set[str]:
        result = await self.session.execute(
            select(Group.group_external_id).where(
                Group.account_id == account_id,
                Group.user_id == user_id,
            )
        )
        return {row[0] for row in result}

    async def list_by_user_filtered(
        self, user_id: int, account_id: int | None = None
    ) -> list[Group]:
        query = select(Group).where(Group.user_id == user_id)
        if account_id is not None:
            query = query.where(Group.account_id == account_id)
        query = query.order_by(Group.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
```

Create `app/repositories/schedule.py`:

```python
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.schedule import Schedule
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Schedule)

    async def get_for_user(self, schedule_id: int, user_id: int) -> Schedule | None:
        """Get schedule, verifying ownership through ad.user_id."""
        result = await self.session.execute(
            select(Schedule)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Schedule.id == schedule_id, Ad.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Ad.user_id == user_id)
            .order_by(Schedule.id)
        )
        return list(result.scalars().all())

    async def get_due_schedules(self, now: datetime) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule).where(
                Schedule.is_active == True,
                Schedule.next_run_at <= now,
            )
        )
        return list(result.scalars().all())
```

Create `app/repositories/send_log.py`:

```python
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.repositories.base import BaseRepository


class SendLogRepository(BaseRepository[SendLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SendLog)

    async def get_stats(self, user_id: int, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.count(SendLog.id).label("total_sent"),
                func.sum(case((SendLog.status == "ok", 1), else_=0)).label("success_count"),
                func.sum(case((SendLog.status == "fail", 1), else_=0)).label("fail_count"),
            )
            .join(Schedule, SendLog.schedule_id == Schedule.id)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Ad.user_id == user_id, SendLog.sent_at >= cutoff)
        )
        row = result.one()
        return {
            "total_sent": row.total_sent or 0,
            "success_count": row.success_count or 0,
            "fail_count": row.fail_count or 0,
        }

    async def list_for_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[SendLog]:
        query = (
            select(SendLog)
            .join(Schedule, SendLog.schedule_id == Schedule.id)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Ad.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_for_user_with_details(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[dict]:
        """Return send logs with ad_title and group_name joined."""
        query = (
            select(
                SendLog,
                Ad.title.label("ad_title"),
                Group.name.label("group_name"),
            )
            .join(Ad, SendLog.ad_id == Ad.id)
            .join(Group, SendLog.group_id == Group.id)
            .where(Ad.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return [
            {
                "ad_title": r.ad_title,
                "group_name": r.group_name,
                "status": r.SendLog.status,
                "error_message": r.SendLog.error_message,
                "sent_at": r.SendLog.sent_at,
            }
            for r in result
        ]
```

**Step 2: Run all tests to verify nothing broke**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 149 passed (new files don't break anything since nothing imports them yet)

**Step 3: Commit**

```bash
git add app/repositories/
git commit -m "refactor: add domain repositories for all models"
```

---

## Phase 3: Services

### Task 5: Messenger Factory Service

**Files:**
- Create: `app/services/messenger_factory.py`
- Create: `tests/test_services/test_messenger_factory.py`

**Step 1: Write tests**

Create `tests/test_services/test_messenger_factory.py`:

```python
import pytest
from unittest.mock import MagicMock

from app.config import Settings
from app.models.messenger_account import MessengerAccount
from app.services.messenger_factory import create_messenger
from app.messengers.telegram_user import TelegramUserMessenger
from app.messengers.whatsapp import WhatsAppMessenger


def test_create_telegram_user_messenger():
    account = MagicMock(spec=MessengerAccount)
    account.type = "tg_user"
    account.credentials = "session_string_here"
    account.id = 1

    settings = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
        telegram_api_id=12345,
        telegram_api_hash="abc123",
    )
    messenger = create_messenger(account, settings)
    assert isinstance(messenger, TelegramUserMessenger)


def test_create_whatsapp_messenger():
    account = MagicMock(spec=MessengerAccount)
    account.type = "wa"
    account.credentials = "session_id"
    account.id = 42

    settings = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
        wa_bridge_url="http://localhost:3000",
    )
    messenger = create_messenger(account, settings)
    assert isinstance(messenger, WhatsAppMessenger)


def test_create_unknown_type_raises():
    account = MagicMock(spec=MessengerAccount)
    account.type = "unknown"

    settings = Settings(database_url="sqlite:///:memory:", secret_key="test")
    with pytest.raises(ValueError, match="Unknown account type"):
        create_messenger(account, settings)
```

**Step 2: Run to verify failure**

Run: `uv run pytest tests/test_services/test_messenger_factory.py -v`
Expected: FAIL

**Step 3: Implement**

Create `app/services/messenger_factory.py`:

```python
from app.config import Settings
from app.messengers.base import BaseMessenger
from app.messengers.telegram_user import TelegramUserMessenger
from app.messengers.whatsapp import WhatsAppMessenger
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
        return WhatsAppMessenger(
            bridge_url=settings.wa_bridge_url,
            session_id=str(account.id),
        )
    else:
        raise ValueError(f"Unknown account type: {account.type}")
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_services/test_messenger_factory.py -v`
Expected: 3 passed

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 152 passed

**Step 6: Commit**

```bash
git add app/services/messenger_factory.py tests/test_services/test_messenger_factory.py
git commit -m "refactor: add messenger factory service"
```

---

### Task 6: Update worker/tasks.py to use messenger factory

**Files:**
- Modify: `app/worker/tasks.py`

**Step 1: Replace get_messenger and Settings() calls in tasks.py**

Replace the `get_messenger` function (lines 21-36) and update imports:

```python
from app.config import get_settings
from app.services.messenger_factory import create_messenger
```

Remove the old `get_messenger` function entirely.

Replace `Settings()` calls on lines 25-26, 33-34, 134-135, 160-161 with `get_settings()`.

In `send_ad_to_group_async` (line 134-136), replace:
```python
from app.config import Settings
upload_dir = Path(Settings().upload_dir).resolve()
```
with:
```python
upload_dir = Path(get_settings().upload_dir).resolve()
```

Replace line 139 `messenger = get_messenger(account)` with:
```python
messenger = create_messenger(account, get_settings())
```

In `check_schedules` (lines 160-161), replace:
```python
from app.config import Settings
settings = Settings()
```
with:
```python
settings = get_settings()
```

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 152 passed

**Step 3: Commit**

```bash
git add app/worker/tasks.py
git commit -m "refactor: use messenger factory and settings singleton in worker"
```

---

## Phase 4: Route Refactoring

### Task 7: Refactor API routes to use repositories

**Files:**
- Modify: `app/routes/ads.py`
- Modify: `app/routes/accounts.py`
- Modify: `app/routes/groups.py`
- Modify: `app/routes/schedules.py`
- Modify: `app/routes/history.py`
- Modify: `app/routes/auth.py`

**Step 1: Refactor ads.py**

Replace the entire file with repository-based implementation:

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.ad import AdRepository
from app.services.billing_service import check_limit

router = APIRouter(prefix="/api/ads", tags=["ads"])


class CreateAdRequest(BaseModel):
    title: str
    text: str
    images: list[str] = []


class UpdateAdRequest(BaseModel):
    title: str | None = None
    text: str | None = None
    images: list[str] | None = None
    is_active: bool | None = None


class AdResponse(BaseModel):
    id: int
    title: str
    text: str
    images: list
    is_active: bool
    created_at: datetime


@router.post("", response_model=AdResponse, status_code=status.HTTP_201_CREATED)
async def create_ad(
    data: CreateAdRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    allowed, reason = await check_limit(db, user_id, "create_ad")
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)

    repo = AdRepository(db)
    return await repo.create(
        user_id=user_id, title=data.title, text=data.text, images=data.images
    )


@router.get("", response_model=list[AdResponse])
async def list_ads(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    return await repo.list_by_user(user_id)


@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )
    return ad


@router.put("/{ad_id}", response_model=AdResponse)
async def update_ad(
    ad_id: int,
    data: UpdateAdRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )
    return await repo.update(ad, **data.model_dump(exclude_unset=True))


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(
    ad_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )
    await repo.delete(ad)
```

**Step 2: Run ads tests**

Run: `uv run pytest tests/test_routes/test_ads.py -v`
Expected: all passed

**Step 3: Refactor accounts.py similarly**

Replace with repository-based:

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.account import AccountRepository

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    type: str
    credentials: str


class AccountResponse(BaseModel):
    id: int
    type: str
    status: str
    created_at: datetime


class AccountStatusResponse(BaseModel):
    id: int
    status: str


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: CreateAccountRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    return await repo.create(user_id=user_id, type=data.type, credentials=data.credentials)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    return await repo.list_by_user(user_id)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    account = await repo.get_by_id_and_user(account_id, user_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    await repo.delete(account)


@router.get("/{account_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    account = await repo.get_by_id_and_user(account_id, user_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return account
```

**Step 4: Refactor groups.py**

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.group import GroupRepository
from app.services.billing_service import check_limit

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    account_id: int
    messenger_type: str
    group_external_id: str
    name: str


class GroupResponse(BaseModel):
    id: int
    account_id: int
    messenger_type: str
    group_external_id: str
    name: str
    is_active: bool
    created_at: datetime


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: CreateGroupRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    allowed, reason = await check_limit(db, user_id, "create_group")
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)

    repo = GroupRepository(db)
    return await repo.create(
        user_id=user_id,
        account_id=data.account_id,
        messenger_type=data.messenger_type,
        group_external_id=data.group_external_id,
        name=data.name,
    )


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    account_id: int | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    return await repo.list_by_user_filtered(user_id, account_id)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    group = await repo.get_by_id_and_user(group_id, user_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    await repo.delete(group)


@router.patch("/{group_id}/toggle", response_model=GroupResponse)
async def toggle_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    group = await repo.get_by_id_and_user(group_id, user_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return await repo.update(group, is_active=not group.is_active)
```

**Step 5: Refactor schedules.py**

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.ad import AdRepository
from app.repositories.schedule import ScheduleRepository
from app.services.schedule_service import compute_next_run_at

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class CreateScheduleRequest(BaseModel):
    ad_id: int
    account_id: int
    group_ids: list[int] = []
    days_of_week: list[int] = []
    times_of_day: list[str] = []


class UpdateScheduleRequest(BaseModel):
    group_ids: list[int] | None = None
    days_of_week: list[int] | None = None
    times_of_day: list[str] | None = None


class ScheduleResponse(BaseModel):
    id: int
    ad_id: int
    account_id: int
    group_ids: list
    days_of_week: list
    times_of_day: list
    is_active: bool
    next_run_at: datetime | None
    created_at: datetime


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: CreateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ad_repo = AdRepository(db)
    ad = await ad_repo.get_by_id_and_user(data.ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found"
        )

    next_run = compute_next_run_at(
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        tz_name="UTC",
    )

    repo = ScheduleRepository(db)
    return await repo.create(
        ad_id=data.ad_id,
        account_id=data.account_id,
        group_ids=data.group_ids,
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        next_run_at=next_run,
    )


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    return await repo.list_for_user(user_id)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: UpdateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    schedule.next_run_at = compute_next_run_at(
        days_of_week=schedule.days_of_week,
        times_of_day=schedule.times_of_day,
        tz_name="UTC",
    )

    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    await repo.delete(schedule)


@router.post("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    schedule.is_active = not schedule.is_active
    if schedule.is_active:
        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name="UTC",
        )
    else:
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    return schedule
```

**Step 6: Refactor history.py**

```python
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.send_log import SendLogRepository

router = APIRouter(prefix="/api/history", tags=["history"])


class SendLogResponse(BaseModel):
    id: int
    schedule_id: int
    ad_id: int
    group_id: int
    status: str
    error_message: str | None
    sent_at: datetime


class StatsResponse(BaseModel):
    total_sent: int
    success_count: int
    fail_count: int


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SendLogRepository(db)
    stats = await repo.get_stats(user_id)
    return StatsResponse(**stats)


@router.get("", response_model=list[SendLogResponse])
async def list_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SendLogRepository(db)
    return await repo.list_for_user(user_id, offset=skip, limit=limit)
```

**Step 7: Refactor auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.repositories.user import UserRepository
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
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await repo.create(
        email=data.email, password_hash=hash_password(data.password), name=data.name
    )
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id, settings.secret_key, settings.access_token_expire_minutes)
    return TokenResponse(access_token=token)
```

**Step 8: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 152 passed

**Step 9: Commit**

```bash
git add app/routes/ads.py app/routes/accounts.py app/routes/groups.py app/routes/schedules.py app/routes/history.py app/routes/auth.py
git commit -m "refactor: migrate API routes to use repository layer"
```

---

### Task 8: Split pages.py into package

This is the largest refactoring task. We split the 1220-line `app/routes/pages.py` into `app/pages/` package.

**Files:**
- Create: `app/pages/__init__.py`
- Create: `app/pages/common.py`
- Create: `app/pages/auth.py`
- Create: `app/pages/dashboard.py`
- Create: `app/pages/ads.py`
- Create: `app/pages/accounts.py`
- Create: `app/pages/groups.py`
- Create: `app/pages/schedules.py`
- Create: `app/pages/billing.py`
- Create: `app/pages/history.py`
- Delete: `app/routes/pages.py`
- Modify: `app/main.py`

**Step 1: Create app/pages/common.py with shared helpers**

```python
from pathlib import Path

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.user import User
from app.services.auth_service import decode_access_token

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


async def get_user_from_cookie(
    request: Request, db: AsyncSession, settings: Settings
) -> User | None:
    """Read JWT from httpOnly cookie and return the User, or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token, settings.secret_key)
    if not payload:
        return None
    user = await db.get(User, payload["sub"])
    return user
```

**Step 2: Create app/pages/auth.py**

```python
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.pages.common import templates

router = APIRouter(tags=["pages"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html", {"request": request, "error": "Неверный email или пароль"}
        )
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Этот email уже зарегистрирован"},
        )
    user = User(email=email, password_hash=hash_password(password), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)
```

**Step 3: Create app/pages/dashboard.py**

```python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(
                Ad.user_id == user.id, Ad.is_active == True  # noqa: E712
            )
        )
    ).scalar() or 0
    accounts_count = (
        await db.execute(
            select(func.count(MessengerAccount.id)).where(
                MessengerAccount.user_id == user.id,
                MessengerAccount.status == "active",
            )
        )
    ).scalar() or 0
    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == user.id, Group.is_active == True  # noqa: E712
            )
        )
    ).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sent_today = (
        await db.execute(
            select(func.count(SendLog.id))
            .join(Ad, SendLog.ad_id == Ad.id)
            .where(Ad.user_id == user.id, SendLog.sent_at >= today_start)
        )
    ).scalar() or 0

    stats = {
        "active_ads": ads_count,
        "active_accounts": accounts_count,
        "active_groups": groups_count,
        "sent_today": sent_today,
    }

    recent_query = (
        select(SendLog, Ad.title.label("ad_title"), Group.name.label("group_name"))
        .join(Ad, SendLog.ad_id == Ad.id)
        .join(Group, SendLog.group_id == Group.id)
        .where(Ad.user_id == user.id)
        .order_by(SendLog.sent_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_query)
    recent_sends = [
        {
            "ad_title": r.ad_title,
            "group_name": r.group_name,
            "status": r.SendLog.status,
            "sent_at": r.SendLog.sent_at,
        }
        for r in recent_result
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "recent_sends": recent_sends,
            "active_page": "dashboard",
        },
    )
```

**Step 4: Create app/pages/ads.py**

```python
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/ads", response_class=HTMLResponse)
async def ads_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc())
    )
    ads = result.scalars().all()
    return templates.TemplateResponse(
        "ads/list.html",
        {"request": request, "user": user, "ads": ads, "active_page": "ads"},
    )


@router.get("/ads/new", response_class=HTMLResponse)
async def ads_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "ad": None, "active_page": "ads"},
    )


@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad = Ad(user_id=user.id, title=title, text=text, images=image_list)
    db.add(ad)
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_edit(
    request: Request,
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "ad": ad, "active_page": "ads"},
    )


@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad.title = title
    ad.text = text
    ad.images = image_list
    ad.is_active = is_active
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.post("/ads/{ad_id}/delete")
async def ads_delete(
    request: Request,
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if ad:
        await db.delete(ad)
        await db.commit()
    return RedirectResponse(url="/ads", status_code=302)
```

**Step 5: Create app/pages/accounts.py**

Copy lines 347-764 from `app/routes/pages.py`, replacing:
- `from app.dependencies import get_db, get_settings` (keep)
- Replace `get_user_from_cookie` import to come from `app.pages.common`
- Replace `templates` import to come from `app.pages.common`
- Add `router = APIRouter(tags=["pages"])` at top

```python
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.messengers.telegram_user import (
    TelegramUserMessenger,
    start_qr_auth,
    get_qr_status,
    refresh_qr,
    submit_2fa,
    complete_auth,
)
from app.messengers.whatsapp import WhatsAppMessenger
from app.services.messenger_factory import create_messenger
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
```

Then copy all account-related route functions (lines 347-764 of original pages.py) exactly as they are, keeping the same route paths and logic. The only changes are:
1. Import `get_user_from_cookie` and `templates` from `app.pages.common`
2. Import `WhatsAppMessenger` at top level (remove inline imports)
3. Replace QR code generation duplication with a helper function:

Add at top of file after imports:
```python
import base64
import io
import qrcode


def _generate_qr_base64(data: str) -> str:
    """Generate QR code as base64 PNG data URI."""
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
```

Then replace the two duplicated QR generation blocks (lines 410-417 and 458-465 in original) with calls to `_generate_qr_base64(login_url)` and `_generate_qr_base64(new_url)`.

**Step 6: Create app/pages/groups.py**

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/groups", response_class=HTMLResponse)
async def groups_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.user_id == user.id).order_by(Group.id)
    )
    groups = result.scalars().all()

    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "tg_user",
        )
    )
    tg_user_accounts = accounts_result.scalars().all()

    wa_accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "active",
        )
    )
    wa_accounts = wa_accounts_result.scalars().all()

    return templates.TemplateResponse(
        "groups/list.html",
        {
            "request": request,
            "user": user,
            "groups": groups,
            "tg_user_accounts": tg_user_accounts,
            "wa_accounts": wa_accounts,
            "active_page": "groups",
        },
    )


@router.post("/groups/{group_id}/toggle")
async def groups_toggle(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        group.is_active = not group.is_active
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)


@router.post("/groups/{group_id}/delete")
async def groups_delete(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        await db.delete(group)
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)
```

**Step 7: Create app/pages/schedules.py**

Copy schedule-related routes (lines 858-1113 from original pages.py), with same import changes. Remove redundant `from app.services.schedule_service import compute_next_run_at` inline imports (lines 950, 1046, 1080) — import once at top.

```python
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.services.schedule_service import compute_next_run_at
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
```

Then copy all schedule page routes exactly, using the single top-level import for `compute_next_run_at`.

**Step 8: Create app/pages/billing.py**

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.services.billing_service import get_user_plan, get_plan_limits, get_usage, PLANS
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    plan = await get_user_plan(db, user.id)
    limits = get_plan_limits(plan)
    usage = await get_usage(db, user.id)
    return templates.TemplateResponse(
        "billing/plans.html",
        {
            "request": request,
            "user": user,
            "plan": plan,
            "limits": limits,
            "usage": usage,
            "all_plans": PLANS,
            "active_page": "billing",
        },
    )
```

**Step 9: Create app/pages/history.py**

```python
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.send_log import SendLog
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/history", response_class=HTMLResponse)
async def history_list(
    request: Request,
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    page_size = 50

    query = (
        select(
            SendLog,
            Ad.title.label("ad_title"),
            Group.name.label("group_name"),
        )
        .join(Ad, SendLog.ad_id == Ad.id)
        .join(Group, SendLog.group_id == Group.id)
        .where(Ad.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result)

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    logs = [
        {
            "ad_title": r.ad_title,
            "group_name": r.group_name,
            "status": r.SendLog.status,
            "error_message": r.SendLog.error_message,
            "sent_at": r.SendLog.sent_at,
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "logs": logs,
            "status_filter": status,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "active_page": "history",
        },
    )
```

**Step 10: Create app/pages/__init__.py**

```python
from fastapi import APIRouter

from app.pages.auth import router as auth_router
from app.pages.dashboard import router as dashboard_router
from app.pages.ads import router as ads_router
from app.pages.accounts import router as accounts_router
from app.pages.groups import router as groups_router
from app.pages.schedules import router as schedules_router
from app.pages.billing import router as billing_router
from app.pages.history import router as history_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(ads_router)
router.include_router(accounts_router)
router.include_router(groups_router)
router.include_router(schedules_router)
router.include_router(billing_router)
router.include_router(history_router)
```

**Step 11: Update app/main.py to import from pages package**

Replace line 21:
```python
from app.routes.pages import router as pages_router
```
with:
```python
from app.pages import router as pages_router
```

**Step 12: Delete app/routes/pages.py**

Remove the old monolithic file.

**Step 13: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 152 passed

**Step 14: Commit**

```bash
git add app/pages/ app/main.py
git rm app/routes/pages.py
git commit -m "refactor: split pages.py (1220 LOC) into app/pages/ package (8 modules)"
```

---

## Phase 5: Cleanup

### Task 9: Unify error handling style and remove dead code

**Files:**
- Modify: `app/routes/ads.py` (already done in Task 7 — verify consistency)
- Modify: `app/routes/groups.py` (already done — verify)
- Modify: `app/worker/celery_app.py`

**Step 1: Update celery_app.py to use settings singleton**

In `app/worker/celery_app.py`, replace lines 6-7:
```python
from app.config import Settings
settings = Settings()
```
with:
```python
from app.config import get_settings
settings = get_settings()
```

**Step 2: Remove duplicate get_settings from dependencies.py if still present**

Verify that `app/dependencies.py` imports `get_settings` from `app.config` and doesn't define its own version.

**Step 3: Run all tests**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 152 passed

**Step 4: Commit**

```bash
git add app/worker/celery_app.py app/dependencies.py
git commit -m "refactor: cleanup settings usage and remove dead code"
```

---

### Task 10: Final verification

**Step 1: Run full test suite with verbose output**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 2: Verify no imports of old pages.py remain**

Run: `grep -r "from app.routes.pages" app/ tests/`
Expected: No results (all references removed)

Run: `grep -r "routes.pages" app/ tests/`
Expected: No results

**Step 3: Verify no duplicate Settings() instantiations remain**

Run: `grep -rn "Settings()" app/ --include="*.py" | grep -v "test\|def get_settings\|lru_cache"`
Expected: Only `config.py` inside `get_settings()` function

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "refactor: complete full project refactoring"
```

---

## Summary of Changes

| Phase | What Changed | Files Added | Files Modified | Files Removed |
|-------|-------------|-------------|----------------|---------------|
| 1: Infrastructure | Settings singleton, exceptions | 2 | 3 | 0 |
| 2: Repositories | BaseRepository + 6 domain repos | 9 | 0 | 0 |
| 3: Services | Messenger factory, worker update | 2 | 1 | 0 |
| 4: Routes | API routes use repos, pages split | 9 | 7 | 1 |
| 5: Cleanup | Unified style, dead code removal | 0 | 2 | 0 |
| **Total** | | **22** | **13** | **1** |

## Test Commands Reference

- Run all tests: `uv run pytest tests/ -v --tb=short -q`
- Run specific test file: `uv run pytest tests/test_repositories/test_base.py -v`
- Run with coverage: `uv run pytest tests/ --cov=app --cov-report=term-missing`

# Admin Panel Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add admin panel for managing user tariffs, viewing stats, blocking/deleting users.

**Architecture:** Single superadmin identified by `ADMIN_EMAIL` env var. Admin pages at `/admin/*` with `require_admin` dependency. New `is_blocked` field on User model to support user blocking.

**Tech Stack:** FastAPI, SQLAlchemy async, Jinja2+Tailwind+HTMX (existing stack), Alembic for migration.

---

### Task 1: Add `admin_email` to Settings

**Files:**
- Modify: `app/config.py:6-52`
- Modify: `tests/conftest.py:12-20`

**Step 1: Add field to Settings**

In `app/config.py`, add after line 45 (`billing_cache_ttl`):

```python
    # Admin
    admin_email: str = ""
```

**Step 2: Add `admin_email` to test_settings fixture**

In `tests/conftest.py`, add to the Settings constructor:

```python
        admin_email="admin@test.com",
```

**Step 3: Commit**

```bash
git add app/config.py tests/conftest.py
git commit -m "feat(admin): add admin_email setting"
```

---

### Task 2: Add `is_blocked` field to User model

**Files:**
- Modify: `app/models/user.py`

**Step 1: Add is_blocked field**

In `app/models/user.py`, add import `Boolean` and the field after `timezone`:

```python
from sqlalchemy import Boolean, DateTime, String, func
```

Add field after `timezone` line:

```python
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
```

**Step 2: Create Alembic migration**

```bash
uv run alembic revision --autogenerate -m "add is_blocked to users"
```

**Step 3: Commit**

```bash
git add app/models/user.py alembic/versions/
git commit -m "feat(admin): add is_blocked field to User model"
```

---

### Task 3: Add `require_admin` dependency and block check

**Files:**
- Modify: `app/dependencies.py`
- Modify: `app/pages/common.py`
- Test: `tests/test_admin_auth.py`

**Step 1: Write failing tests**

Create `tests/test_admin_auth.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_page(client: AsyncClient, auth_headers):
    """Regular user gets 403 on /admin."""
    resp = await client.get("/admin", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_admin_page(client: AsyncClient):
    """Admin user can access /admin."""
    # Register as admin (admin@test.com matches test_settings.admin_email)
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin", headers=admin_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_blocked_user_cannot_login(client: AsyncClient, db_session):
    """Blocked user gets rejected."""
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(
        email="blocked@test.com",
        password_hash=hash_password("pass123"),
        name="Blocked",
        is_blocked=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "email": "blocked@test.com",
        "password": "pass123",
    })
    assert resp.status_code == 403
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_admin_auth.py -v
```

Expected: FAIL (no /admin route, no block check)

**Step 3: Add `require_admin` to `app/dependencies.py`**

Add at the end of the file:

```python
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "User":
    """Get current user object (not just ID). Checks is_blocked."""
    from app.models.user import User

    user_id = await get_current_user_id(request, settings=settings)
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is blocked")
    return user


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "User":
    """Require current user to be admin. Returns User object."""
    user = await get_current_user(request, db, settings)
    if user.email != settings.admin_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
```

**Step 4: Add block check to `get_user_from_cookie`**

In `app/pages/common.py`, update `get_user_from_cookie` to return `None` if user is blocked:

```python
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
    if user and user.is_blocked:
        return None
    return user
```

**Step 5: Add block check to login route**

In `app/routes/auth.py`, after verifying password in login endpoint, add check:

```python
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is blocked")
```

(Find the login route, add this check after `if not verify_password(...)` block and before creating the token.)

**Step 6: Run tests — they'll still fail because /admin route doesn't exist yet**

Tests for blocked user should pass. Admin access tests need Task 7.

**Step 7: Commit**

```bash
git add app/dependencies.py app/pages/common.py app/routes/auth.py tests/test_admin_auth.py
git commit -m "feat(admin): add require_admin dependency and block check"
```

---

### Task 4: Extend UserRepository

**Files:**
- Modify: `app/repositories/user.py`
- Test: `tests/test_repositories/test_user_repo.py`

**Step 1: Write failing tests**

Create `tests/test_repositories/test_user_repo.py`:

```python
import pytest
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth_service import hash_password


@pytest.mark.asyncio
async def test_get_all_users(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="a@test.com", password_hash=hash_password("p"), name="A")
    u2 = User(email="b@test.com", password_hash=hash_password("p"), name="B")
    db_session.add_all([u1, u2])
    await db_session.commit()

    users = await repo.get_all_users()
    assert len(users) == 2


@pytest.mark.asyncio
async def test_search_users(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="alice@test.com", password_hash=hash_password("p"), name="Alice")
    u2 = User(email="bob@test.com", password_hash=hash_password("p"), name="Bob")
    db_session.add_all([u1, u2])
    await db_session.commit()

    results = await repo.search_users("alice")
    assert len(results) == 1
    assert results[0].email == "alice@test.com"

    results = await repo.search_users("bob")
    assert len(results) == 1
    assert results[0].name == "Bob"


@pytest.mark.asyncio
async def test_count_all(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="a@test.com", password_hash=hash_password("p"), name="A")
    db_session.add(u1)
    await db_session.commit()

    count = await repo.count_all()
    assert count == 1
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_repositories/test_user_repo.py -v
```

**Step 3: Implement methods in `app/repositories/user.py`**

```python
from sqlalchemy import select, func, or_

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

    async def get_all_users(self) -> list[User]:
        result = await self.session.execute(
            select(User).order_by(User.id)
        )
        return list(result.scalars().all())

    async def search_users(self, query: str) -> list[User]:
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(User)
            .where(or_(User.email.ilike(pattern), User.name.ilike(pattern)))
            .order_by(User.id)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_repositories/test_user_repo.py -v
```

**Step 5: Commit**

```bash
git add app/repositories/user.py tests/test_repositories/test_user_repo.py
git commit -m "feat(admin): extend UserRepository with get_all, search, count"
```

---

### Task 5: Add `set_user_plan` to billing service

**Files:**
- Modify: `app/services/billing_service.py`
- Test: `tests/test_services/test_billing_service.py`

**Step 1: Write failing test**

Create or append to `tests/test_services/test_billing_service.py`:

```python
import pytest
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.subscription import Subscription
from app.services.auth_service import hash_password
from app.services.billing_service import set_user_plan, get_user_plan


@pytest.mark.asyncio
async def test_set_user_plan_creates_subscription(db_session):
    user = User(email="u@test.com", password_hash=hash_password("p"), name="U")
    db_session.add(user)
    await db_session.commit()

    expires = datetime.now(timezone.utc) + timedelta(days=30)
    await set_user_plan(db_session, user.id, "pro", expires)

    plan = await get_user_plan(db_session, user.id)
    assert plan == "pro"


@pytest.mark.asyncio
async def test_set_user_plan_deactivates_old(db_session):
    user = User(email="u@test.com", password_hash=hash_password("p"), name="U")
    db_session.add(user)
    await db_session.commit()

    expires = datetime.now(timezone.utc) + timedelta(days=30)
    await set_user_plan(db_session, user.id, "basic", expires)
    await set_user_plan(db_session, user.id, "pro", expires)

    plan = await get_user_plan(db_session, user.id)
    assert plan == "pro"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_services/test_billing_service.py -v
```

**Step 3: Implement `set_user_plan` in `app/services/billing_service.py`**

Add at the end of the file:

```python
async def set_user_plan(
    db: AsyncSession, user_id: int, plan: str, expires_at: datetime
) -> Subscription:
    """Set user plan. Deactivates any existing active subscription first."""
    # Deactivate existing active subscriptions
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    for sub in result.scalars().all():
        sub.is_active = False

    # Create new subscription
    new_sub = Subscription(
        user_id=user_id,
        plan=plan,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(new_sub)
    await db.commit()
    await db.refresh(new_sub)
    return new_sub
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_services/test_billing_service.py -v
```

**Step 5: Commit**

```bash
git add app/services/billing_service.py tests/test_services/test_billing_service.py
git commit -m "feat(admin): add set_user_plan to billing service"
```

---

### Task 6: Create admin pages module

**Files:**
- Create: `app/pages/admin.py`
- Modify: `app/pages/__init__.py`

**Step 1: Create `app/pages/admin.py`**

```python
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings, require_admin
from app.models.user import User
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.pages.common import templates
from app.repositories.user import UserRepository
from app.services.billing_service import (
    PLANS,
    get_user_plan,
    get_usage,
    set_user_plan,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_repo = UserRepository(db)
    total_users = await user_repo.count_all()

    total_accounts = (
        await db.execute(select(func.count(MessengerAccount.id)))
    ).scalar() or 0

    total_active_accounts = (
        await db.execute(
            select(func.count(MessengerAccount.id)).where(
                MessengerAccount.status == "active"
            )
        )
    ).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sends_today = (
        await db.execute(
            select(func.count(SendLog.id)).where(
                SendLog.sent_at >= today_start
            )
        )
    ).scalar() or 0

    active_subs = (
        await db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.is_active == True,  # noqa: E712
                Subscription.expires_at > datetime.now(timezone.utc),
            )
        )
    ).scalar() or 0

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "stats": {
                "total_users": total_users,
                "total_accounts": total_accounts,
                "active_accounts": total_active_accounts,
                "sends_today": sends_today,
                "active_subscriptions": active_subs,
            },
        },
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: str = "",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_repo = UserRepository(db)
    if q:
        users = await user_repo.search_users(q)
    else:
        users = await user_repo.get_all_users()

    # Get plan for each user
    user_data = []
    for u in users:
        plan = await get_user_plan(db, u.id)
        user_data.append({"user": u, "plan": plan})

    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "users": user_data,
            "search_query": q,
        },
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    plan = await get_user_plan(db, target_user.id)
    usage = await get_usage(db, target_user.id)

    # Get user's accounts
    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == target_user.id
        )
    )
    accounts = list(accounts_result.scalars().all())

    # Get user's ads count
    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(Ad.user_id == target_user.id)
        )
    ).scalar() or 0

    # Get user's groups count
    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == target_user.id
            )
        )
    ).scalar() or 0

    # Get active subscription details
    sub_result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == target_user.id,
            Subscription.is_active == True,  # noqa: E712
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    active_sub = sub_result.scalar_one_or_none()

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "plan": plan,
            "usage": usage,
            "accounts": accounts,
            "ads_count": ads_count,
            "groups_count": groups_count,
            "active_sub": active_sub,
            "all_plans": PLANS,
        },
    )


@router.post("/users/{user_id}/plan")
async def admin_set_plan(
    request: Request,
    user_id: int,
    plan: str = Form(...),
    expires_days: int = Form(30),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
    await set_user_plan(db, user_id, plan, expires_at)

    return RedirectResponse(
        url=f"/admin/users/{user_id}", status_code=302
    )


@router.post("/users/{user_id}/block")
async def admin_toggle_block(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Don't allow admin to block themselves
    if target_user.id == admin.id:
        return RedirectResponse(
            url=f"/admin/users/{user_id}", status_code=302
        )

    target_user.is_blocked = not target_user.is_blocked
    await db.commit()

    return RedirectResponse(
        url=f"/admin/users/{user_id}", status_code=302
    )


@router.post("/users/{user_id}/delete")
async def admin_delete_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Don't allow admin to delete themselves
    if target_user.id == admin.id:
        return RedirectResponse(
            url=f"/admin/users/{user_id}", status_code=302
        )

    await db.delete(target_user)
    await db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)
```

**Step 2: Register admin router in `app/pages/__init__.py`**

Add import and include:

```python
from app.pages.admin import router as admin_router
```

And:

```python
router.include_router(admin_router)
```

**Step 3: Commit**

```bash
git add app/pages/admin.py app/pages/__init__.py
git commit -m "feat(admin): add admin pages module with routes"
```

---

### Task 7: Create admin templates

**Files:**
- Create: `app/templates/admin/dashboard.html`
- Create: `app/templates/admin/users.html`
- Create: `app/templates/admin/user_detail.html`

**Step 1: Create `app/templates/admin/dashboard.html`**

```html
{% extends "base.html" %}
{% block title %}Админ-панель - Broadcaster{% endblock %}
{% block content %}
<div class="space-y-8">
    <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">Админ-панель</h1>
        <p class="mt-1 text-sm text-slate-600">Общая статистика платформы.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
            <p class="text-sm font-medium text-slate-600">Пользователей</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.total_users }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
            <p class="text-sm font-medium text-slate-600">Аккаунтов (активных)</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.active_accounts }} <span class="text-base font-normal text-slate-500">/ {{ stats.total_accounts }}</span></p>
        </div>
        <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
            <p class="text-sm font-medium text-slate-600">Отправок сегодня</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.sends_today }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
            <p class="text-sm font-medium text-slate-600">Активных подписок</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.active_subscriptions }}</p>
        </div>
    </div>

    <div>
        <a href="/admin/users" class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 transition-colors">
            Управление пользователями
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
        </a>
    </div>
</div>
{% endblock %}
```

**Step 2: Create `app/templates/admin/users.html`**

```html
{% extends "base.html" %}
{% block title %}Пользователи - Админ{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold tracking-tight text-slate-900">Пользователи</h1>
            <p class="mt-1 text-sm text-slate-600">Всего: {{ users|length }}</p>
        </div>
        <form method="get" action="/admin/users" class="flex gap-2">
            <input type="text" name="q" value="{{ search_query }}" placeholder="Поиск по email или имени..."
                   class="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200 w-64">
            <button type="submit" class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors">Найти</button>
        </form>
    </div>

    <div class="bg-white rounded-xl shadow-card border border-slate-200/80 overflow-hidden">
        <table class="min-w-full divide-y divide-slate-200">
            <thead class="bg-slate-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Пользователь</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">План</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Статус</th>
                    <th class="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Регистрация</th>
                    <th class="px-6 py-3"></th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
                {% for item in users %}
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-3">
                            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-700 text-sm font-semibold">{{ item.user.name[0]|upper }}</span>
                            <div>
                                <p class="text-sm font-medium text-slate-900">{{ item.user.name }}</p>
                                <p class="text-xs text-slate-500">{{ item.user.email }}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        <span class="inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full
                            {% if item.plan == 'pro' %}bg-purple-100 text-purple-800
                            {% elif item.plan == 'basic' %}bg-blue-100 text-blue-800
                            {% else %}bg-slate-100 text-slate-700{% endif %}">{{ item.plan }}</span>
                    </td>
                    <td class="px-6 py-4">
                        {% if item.user.is_blocked %}
                        <span class="inline-block px-2.5 py-0.5 text-xs font-semibold bg-red-100 text-red-800 rounded-full">Заблокирован</span>
                        {% else %}
                        <span class="inline-block px-2.5 py-0.5 text-xs font-semibold bg-green-100 text-green-800 rounded-full">Активен</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-sm text-slate-600">{{ item.user.created_at.strftime('%d.%m.%Y') }}</td>
                    <td class="px-6 py-4 text-right">
                        <a href="/admin/users/{{ item.user.id }}" class="text-sm font-medium text-primary-600 hover:text-primary-700">Подробнее</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

**Step 3: Create `app/templates/admin/user_detail.html`**

```html
{% extends "base.html" %}
{% block title %}{{ target_user.name }} - Админ{% endblock %}
{% block content %}
<div class="space-y-8">
    <div class="flex items-center gap-4">
        <a href="/admin/users" class="text-sm text-slate-500 hover:text-slate-700">&larr; К списку</a>
    </div>

    <!-- User Info -->
    <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
                <span class="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-primary-700 text-lg font-bold">{{ target_user.name[0]|upper }}</span>
                <div>
                    <h1 class="text-xl font-bold text-slate-900">{{ target_user.name }}</h1>
                    <p class="text-sm text-slate-500">{{ target_user.email }}</p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                {% if target_user.is_blocked %}
                <span class="px-3 py-1 text-sm font-semibold bg-red-100 text-red-800 rounded-full">Заблокирован</span>
                {% else %}
                <span class="px-3 py-1 text-sm font-semibold bg-green-100 text-green-800 rounded-full">Активен</span>
                {% endif %}
            </div>
        </div>
        <div class="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
                <p class="text-slate-500">ID</p>
                <p class="font-medium text-slate-900">{{ target_user.id }}</p>
            </div>
            <div>
                <p class="text-slate-500">Регистрация</p>
                <p class="font-medium text-slate-900">{{ target_user.created_at.strftime('%d.%m.%Y %H:%M') }}</p>
            </div>
            <div>
                <p class="text-slate-500">Часовой пояс</p>
                <p class="font-medium text-slate-900">{{ target_user.timezone }}</p>
            </div>
            <div>
                <p class="text-slate-500">Текущий план</p>
                <p class="font-medium text-slate-900 capitalize">{{ plan }}</p>
            </div>
        </div>
    </div>

    <!-- Usage Stats -->
    <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Использование</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-slate-900">{{ usage.ads_count }}</p>
                <p class="text-sm text-slate-600">Объявлений</p>
            </div>
            <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-slate-900">{{ usage.groups_count }}</p>
                <p class="text-sm text-slate-600">Групп</p>
            </div>
            <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-slate-900">{{ usage.sends_today }}</p>
                <p class="text-sm text-slate-600">Отправок сегодня</p>
            </div>
        </div>
    </div>

    <!-- Accounts -->
    <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Аккаунты ({{ accounts|length }})</h2>
        {% if accounts %}
        <div class="space-y-2">
            {% for acc in accounts %}
            <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div class="flex items-center gap-3">
                    <span class="text-sm font-medium text-slate-900">{{ acc.type }}</span>
                    <span class="text-xs text-slate-500">ID: {{ acc.id }}</span>
                </div>
                <span class="px-2 py-0.5 text-xs font-medium rounded-full
                    {% if acc.status == 'active' %}bg-green-100 text-green-800
                    {% else %}bg-slate-100 text-slate-600{% endif %}">{{ acc.status }}</span>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p class="text-sm text-slate-500">Нет аккаунтов</p>
        {% endif %}
    </div>

    <!-- Plan Management -->
    <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Управление тарифом</h2>
        {% if active_sub %}
        <p class="text-sm text-slate-600 mb-4">
            Текущая подписка: <strong class="capitalize">{{ plan }}</strong>,
            истекает: <strong>{{ active_sub.expires_at.strftime('%d.%m.%Y %H:%M') }}</strong>
        </p>
        {% else %}
        <p class="text-sm text-slate-600 mb-4">Нет активной подписки (план: free)</p>
        {% endif %}
        <form method="post" action="/admin/users/{{ target_user.id }}/plan" class="flex flex-wrap items-end gap-4">
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">План</label>
                <select name="plan" class="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200">
                    {% for plan_name in all_plans %}
                    <option value="{{ plan_name }}" {% if plan_name == plan %}selected{% endif %}>{{ plan_name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Срок (дней)</label>
                <input type="number" name="expires_days" value="30" min="1" max="365"
                       class="rounded-lg border border-slate-300 px-3 py-2 text-sm w-24 focus:border-primary-500 focus:ring-2 focus:ring-primary-200">
            </div>
            <button type="submit" class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors">
                Назначить
            </button>
        </form>
    </div>

    <!-- Actions -->
    <div class="bg-white rounded-xl shadow-card border border-slate-200/80 p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Действия</h2>
        <div class="flex flex-wrap gap-3">
            <form method="post" action="/admin/users/{{ target_user.id }}/block">
                {% if target_user.is_blocked %}
                <button type="submit" class="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors">
                    Разблокировать
                </button>
                {% else %}
                <button type="submit" class="rounded-lg bg-yellow-600 px-4 py-2 text-sm font-medium text-white hover:bg-yellow-700 transition-colors"
                        onclick="return confirm('Заблокировать пользователя {{ target_user.name }}?')">
                    Заблокировать
                </button>
                {% endif %}
            </form>
            <form method="post" action="/admin/users/{{ target_user.id }}/delete">
                <button type="submit" class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
                        onclick="return confirm('УДАЛИТЬ пользователя {{ target_user.name }}? Это действие необратимо!')">
                    Удалить
                </button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 4: Commit**

```bash
git add app/templates/admin/
git commit -m "feat(admin): add admin panel templates"
```

---

### Task 8: Update navigation to show admin link

**Files:**
- Modify: `app/templates/base.html`
- Modify: `app/pages/common.py`
- Modify: all page handlers that pass context to templates (or use a middleware approach)

**Step 1: Add `is_admin` to template context**

The simplest approach: add a helper function in `app/pages/common.py`:

```python
def check_is_admin(user: User | None, settings: Settings) -> bool:
    """Check if user is admin."""
    if not user or not settings.admin_email:
        return False
    return user.email == settings.admin_email
```

**Step 2: Update `base.html` — add admin link in desktop nav**

After the "Тарифы" link (line 56), add:

```html
                            {% if is_admin %}
                            <a href="/admin" class="inline-flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 {% if active_page == 'admin' %}bg-primary-50 text-primary-700{% else %}text-slate-600 hover:bg-slate-100 hover:text-slate-900{% endif %}">Админ</a>
                            {% endif %}
```

**Step 3: Update `base.html` — add admin link in mobile nav**

After the "Тарифы" mobile link (line 74), add:

```html
                                    {% if is_admin %}
                                    <a href="/admin" class="block rounded-lg px-3 py-2 text-sm font-medium {% if active_page == 'admin' %}bg-primary-50 text-primary-700{% else %}text-slate-700 hover:bg-slate-100{% endif %}">Админ</a>
                                    {% endif %}
```

**Step 4: Pass `is_admin` from each page handler**

In each existing page handler (dashboard, ads, accounts, groups, schedules, history, billing), add `is_admin` to the template context. For example, in `app/pages/dashboard.py`, change the return to include:

```python
from app.pages.common import get_user_from_cookie, templates, check_is_admin
```

And in the template response dict:

```python
            "is_admin": check_is_admin(user, settings),
```

This needs to be done in all 7 page files:
- `app/pages/dashboard.py`
- `app/pages/ads.py`
- `app/pages/accounts.py`
- `app/pages/groups.py`
- `app/pages/schedules.py`
- `app/pages/history.py`
- `app/pages/billing.py`

Each file needs:
1. Import `check_is_admin` from `app/pages/common`
2. Add `"is_admin": check_is_admin(user, settings)` to every `TemplateResponse` context dict

**Step 5: Commit**

```bash
git add app/templates/base.html app/pages/
git commit -m "feat(admin): show admin link in nav for admin user"
```

---

### Task 9: Write integration tests for admin pages

**Files:**
- Modify: `tests/test_admin_auth.py` (extend with more tests)

**Step 1: Add comprehensive admin tests**

Append to `tests/test_admin_auth.py`:

```python
@pytest.mark.asyncio
async def test_admin_users_list(client: AsyncClient):
    """Admin can see users list."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin/users", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_set_plan(client: AsyncClient, db_session):
    """Admin can set user plan."""
    # Create admin
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create regular user
    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "User",
    })

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    # Set plan
    resp = await client.post(
        f"/admin/users/{target.id}/plan",
        data={"plan": "pro", "expires_days": "30"},
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302


@pytest.mark.asyncio
async def test_admin_block_user(client: AsyncClient, db_session):
    """Admin can block a user."""
    await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "adminpass123",
        "name": "Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpass123",
    })
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create regular user
    await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "userpass123",
        "name": "User",
    })

    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    target = result.scalar_one()

    # Block
    resp = await client.post(
        f"/admin/users/{target.id}/block",
        headers=admin_headers,
        follow_redirects=False,
    )
    assert resp.status_code == 302

    # Verify blocked
    await db_session.refresh(target)
    assert target.is_blocked is True
```

**Step 2: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/test_admin_auth.py
git commit -m "test(admin): add integration tests for admin panel"
```

---

### Task 10: Run full test suite and verify

**Step 1: Run all tests with coverage**

```bash
uv run pytest tests/ -v --tb=short
```

Expected: All tests pass, no regressions.

**Step 2: Final commit if any fixes needed**

---

### Summary of all files changed/created:

**Modified:**
- `app/config.py` — add `admin_email` setting
- `app/models/user.py` — add `is_blocked` field
- `app/dependencies.py` — add `get_current_user`, `require_admin`
- `app/pages/common.py` — add block check, `check_is_admin`
- `app/routes/auth.py` — add block check on login
- `app/repositories/user.py` — add `get_all_users`, `search_users`, `count_all`
- `app/services/billing_service.py` — add `set_user_plan`
- `app/pages/__init__.py` — register admin router
- `app/templates/base.html` — add admin nav link
- `app/pages/dashboard.py` — pass `is_admin` to context
- `app/pages/ads.py` — pass `is_admin` to context
- `app/pages/accounts.py` — pass `is_admin` to context
- `app/pages/groups.py` — pass `is_admin` to context
- `app/pages/schedules.py` — pass `is_admin` to context
- `app/pages/history.py` — pass `is_admin` to context
- `app/pages/billing.py` — pass `is_admin` to context

**Created:**
- `app/pages/admin.py` — admin page routes
- `app/templates/admin/dashboard.html` — admin dashboard
- `app/templates/admin/users.html` — users list
- `app/templates/admin/user_detail.html` — user detail + management
- `alembic/versions/xxx_add_is_blocked_to_users.py` — migration
- `tests/test_admin_auth.py` — admin auth + integration tests
- `tests/test_repositories/test_user_repo.py` — user repo tests
- `tests/test_services/test_billing_service.py` — billing service tests

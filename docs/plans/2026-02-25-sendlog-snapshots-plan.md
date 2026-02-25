# SendLog: Remove FK + Add Snapshots — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make SendLog independent of parent entities so deleting ads/groups/accounts/schedules preserves full send history.

**Architecture:** Remove all ForeignKey constraints from SendLog. Add `user_id` column (plain integer, no FK) for direct user filtering. Add snapshot fields (ad_title, ad_text, ad_images, group_name, account_name, messenger_type) populated at send time. Update all queries to read from SendLog directly without JOINs.

**Tech Stack:** SQLAlchemy, Alembic, FastAPI, Pydantic, pytest

---

### Task 1: Update SendLog model

**Files:**
- Modify: `app/models/send_log.py`

**Step 1: Rewrite SendLog model**

Replace the entire model with FK-free version + snapshot fields:

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SendLog(Base):
    __tablename__ = "send_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Snapshots
    ad_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ad_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ad_images: Mapped[list | None] = mapped_column(JSON, nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    messenger_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
```

**Step 2: Run tests to see what breaks**

Run: `uv run pytest tests/test_models/test_send_log.py -v`
Expected: Tests may fail because they don't pass `user_id`.

**Step 3: Commit**

```bash
git add app/models/send_log.py
git commit -m "refactor: remove FK from SendLog, add snapshot fields and user_id"
```

---

### Task 2: Update send_message_once to populate snapshots

**Files:**
- Modify: `app/application/scheduling/use_cases.py:106-200`

**Step 1: Update all SendLog() calls in send_message_once**

There are 4 places where SendLog is created. Each must include `user_id` and snapshot fields.

First SendLog (line 125, missing entities):
```python
    if not ad or not group or not account:
        log_entry = SendLog(
            user_id=ad.user_id if ad else 0,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title if ad else None,
            ad_text=ad.text if ad else None,
            ad_images=ad.images if ad else None,
            group_name=group.name if group else None,
            account_name=account.name if account else None,
            messenger_type=account.type if account else None,
            status="fail",
            error_message="Missing ad, group, or account",
        )
```

Note: `account.name` doesn't exist — MessengerAccount has no `name` field, only `type` and `credentials`. Use `account.type` as display name. Let's check: MessengerAccount fields are `id, user_id, type, credentials, session_data, status, created_at`. There's no `name`. We'll store `account.type` in `account_name` (e.g. "tg_user", "wa").

Second SendLog (line 137, account disconnected):
```python
    if account.status != "active":
        log_entry = SendLog(
            user_id=ad.user_id,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title,
            ad_text=ad.text,
            ad_images=ad.images,
            group_name=group.name,
            account_name=account.type,
            messenger_type=account.type,
            status="account_disconnected",
            error_message=f"Account {account.id} is {account.status}",
        )
```

Third SendLog (line 159, messenger factory error):
```python
        log_entry = SendLog(
            user_id=ad.user_id,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title,
            ad_text=ad.text,
            ad_images=ad.images,
            group_name=group.name,
            account_name=account.type,
            messenger_type=account.type,
            status="fail",
            error_message=str(e),
        )
```

Fourth SendLog (line 176, actual send result):
```python
    log_entry = SendLog(
        user_id=ad.user_id,
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        ad_title=ad.title,
        ad_text=ad.text,
        ad_images=ad.images,
        group_name=group.name,
        account_name=account.type,
        messenger_type=account.type,
        status="ok" if result.get("ok") else "fail",
        error_message=result.get("error"),
    )
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_worker/test_tasks.py -v`
Expected: PASS (tests check status/error_message, not snapshots)

**Step 3: Commit**

```bash
git add app/application/scheduling/use_cases.py
git commit -m "feat: populate SendLog snapshots and user_id in send_message_once"
```

---

### Task 3: Update SendLogRepository (remove JOINs)

**Files:**
- Modify: `app/repositories/send_log.py`

**Step 1: Rewrite repository methods**

`get_stats` — filter by `SendLog.user_id` directly, no JOIN:
```python
    async def get_stats(self, user_id: int, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.count(SendLog.id).label("total_sent"),
                func.sum(case((SendLog.status == "ok", 1), else_=0)).label("success_count"),
                func.sum(case((SendLog.status == "fail", 1), else_=0)).label("fail_count"),
            )
            .where(SendLog.user_id == user_id, SendLog.sent_at >= cutoff)
        )
        row = result.one()
        return {
            "total_sent": row.total_sent or 0,
            "success_count": row.success_count or 0,
            "fail_count": row.fail_count or 0,
        }
```

`list_for_user` — filter by `SendLog.user_id`, no JOIN:
```python
    async def list_for_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[SendLog]:
        query = (
            select(SendLog)
            .where(SendLog.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
```

`list_for_user_with_details` — no JOIN, data is in SendLog:
```python
    async def list_for_user_with_details(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[dict]:
        query = (
            select(SendLog)
            .where(SendLog.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return [
            {
                "ad_title": log.ad_title or "—",
                "group_name": log.group_name or "—",
                "status": log.status,
                "error_message": log.error_message,
                "sent_at": log.sent_at,
            }
            for log in result.scalars()
        ]
```

Remove unused imports (`Ad`, `Group`, `Schedule`).

**Step 2: Run tests**

Run: `uv run pytest tests/test_routes/test_history.py -v`
Expected: FAIL — tests create SendLog without `user_id`.

**Step 3: Commit**

```bash
git add app/repositories/send_log.py
git commit -m "refactor: remove JOINs from SendLogRepository, use user_id directly"
```

---

### Task 4: Update history pages and API routes

**Files:**
- Modify: `app/pages/history.py`
- Modify: `app/routes/history.py`

**Step 1: Update pages/history.py**

Replace the query to use SendLog directly:

```python
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
        select(SendLog)
        .where(SendLog.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    logs = [
        {
            "ad_title": r.ad_title or "—",
            "group_name": r.group_name or "—",
            "status": r.status,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "logs": logs,
            "status_filter": status,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "active_page": "history",
        },
    )
```

Remove unused imports (`Ad`, `Group`).

**Step 2: Update routes/history.py**

Update `SendLogResponse` to include snapshots and make IDs optional:

```python
class SendLogResponse(BaseModel):
    id: int
    schedule_id: int | None
    ad_id: int | None
    group_id: int | None
    ad_title: str | None = None
    ad_text: str | None = None
    group_name: str | None = None
    account_name: str | None = None
    messenger_type: str | None = None
    status: str
    error_message: str | None
    sent_at: datetime
```

**Step 3: Commit**

```bash
git add app/pages/history.py app/routes/history.py
git commit -m "refactor: history pages/API read snapshots from SendLog directly"
```

---

### Task 5: Update billing service (remove JOIN)

**Files:**
- Modify: `app/services/billing_service.py:50-59`

**Step 1: Replace the sends_today query**

Change from JOIN through Ad to direct user_id filter:

```python
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    sends_today = (await db.execute(
        select(func.count(SendLog.id))
        .where(
            SendLog.user_id == user_id,
            SendLog.sent_at >= today_start,
            SendLog.status == "ok",
        )
    )).scalar() or 0
```

Remove unused `Ad` import from the SendLog query section (keep it if used elsewhere in the file).

**Step 2: Run tests**

Run: `uv run pytest tests/test_services/test_billing_service.py -v`
Expected: FAIL — tests create SendLog without `user_id`.

**Step 3: Commit**

```bash
git add app/services/billing_service.py
git commit -m "refactor: billing service queries SendLog.user_id directly"
```

---

### Task 6: Update all tests

**Files:**
- Modify: `tests/test_models/test_send_log.py`
- Modify: `tests/test_routes/test_history.py`
- Modify: `tests/test_services/test_billing_service.py`
- Modify: `tests/test_worker/test_tasks.py`
- Modify: `tests/test_e2e.py`

**Step 1: Update test_models/test_send_log.py**

Add `user_id` to both SendLog creations:

In `test_create_send_log` (line 62):
```python
    send_log = SendLog(
        user_id=user.id,
        schedule_id=schedule.id,
        ad_id=ad.id,
        group_id=group.id,
        ad_title=ad.title,
        ad_text=ad.text,
        ad_images=ad.images,
        group_name=group.name,
        account_name=account.type,
        messenger_type=account.type,
        status="sent",
        error_message=None,
    )
```

Update assertions to check new fields:
```python
    assert send_log.user_id == user.id
    assert send_log.ad_title == "Logged Ad"
    assert send_log.group_name == "Log Group"
```

In `test_send_log_with_error` (line 131):
```python
    send_log = SendLog(
        user_id=user.id,
        schedule_id=schedule.id,
        ad_id=ad.id,
        group_id=group.id,
        ad_title=ad.title,
        group_name=group.name,
        account_name=account.type,
        messenger_type=account.type,
        status="failed",
        error_message="Connection timeout: could not reach Telegram API",
    )
```

**Step 2: Update test_routes/test_history.py**

Add `user_id` to all SendLog creations. The `setup_dependencies` creates entities via API, so we need the user_id. The auth_headers fixture creates a user with email "testuser@test.com". We need to get the user_id.

In `test_list_history_with_data` (line 58), add user_id=1 (the first registered user):
```python
    # Get user ID from auth
    from app.models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User))
    user = result.scalar_one()

    log1 = SendLog(
        user_id=user.id,
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="ok",
        sent_at=now - timedelta(hours=2),
    )
    log2 = SendLog(
        user_id=user.id,
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="fail",
        error_message="Connection timeout",
        sent_at=now - timedelta(hours=1),
    )
```

Apply same pattern to `test_list_history_pagination` and `test_stats_endpoint`.

**Step 3: Update test_services/test_billing_service.py**

Add `user_id=user.id` to SendLog creations (lines 104, 115):
```python
    for i in range(10):
        db_session.add(SendLog(
            user_id=user.id,
            schedule_id=schedule.id, ad_id=ad.id, group_id=group.id,
            status="fail", error_message="Chromium error",
        ))
```

**Step 4: Update tests/test_worker/test_tasks.py**

The `_send_message` function creates SendLog internally via `send_message_once`, so test assertions need updating.

In `test_send_message_success` (line 155-158), add snapshot assertions:
```python
    async with factory() as session:
        result = await session.execute(select(SendLog))
        log = result.scalar_one()
        assert log.status == "ok"
        assert log.error_message is None
        assert log.user_id == user.id
        assert log.ad_title == "Test Ad"
        assert log.group_name == "Sales"
```

In `test_send_message_failure` (line 185-189), similar.

**Step 5: Update tests/test_e2e.py**

In the SendLog verification section (line 146-150), add snapshot checks:
```python
    async with session_factory() as session:
        result = await session.execute(select(SendLog))
        logs = result.scalars().all()
        assert len(logs) == 1
        assert logs[0].status == "ok"
        assert logs[0].ad_title is not None
```

**Step 6: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 7: Commit**

```bash
git add tests/
git commit -m "test: update all tests for SendLog without FK + snapshot fields"
```

---

### Task 7: Generate Alembic migration

**Files:**
- Create: `alembic/versions/xxx_sendlog_remove_fk_add_snapshots.py`

**Step 1: Generate migration**

Run: `uv run alembic revision --autogenerate -m "sendlog remove fk add snapshots"`

**Step 2: Review and fix generated migration**

Alembic should detect:
- Drop 3 FK constraints (schedule_id, ad_id, group_id)
- Make schedule_id, ad_id, group_id nullable
- Add columns: user_id, ad_title, ad_text, ad_images, group_name, account_name, messenger_type
- Add index on user_id

**Step 3: Add data migration to populate existing records**

After the schema changes, add in `upgrade()`:

```python
    # Populate snapshots for existing records
    op.execute("""
        UPDATE send_logs SET
            user_id = ads.user_id,
            ad_title = ads.title,
            ad_text = ads.text,
            ad_images = ads.images,
            group_name = groups.name,
            account_name = messenger_accounts.type,
            messenger_type = groups.messenger_type
        FROM ads, groups, messenger_accounts
        WHERE send_logs.ad_id = ads.id
          AND send_logs.group_id = groups.id
          AND groups.account_id = messenger_accounts.id
    """)
```

**Step 4: Commit**

```bash
git add alembic/
git commit -m "migration: sendlog remove FK, add snapshots, backfill existing data"
```

---

### Task 8: Final verification

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 2: Verify deletion preserves history**

Write a quick manual check or add a test: create entities → create SendLog → delete Ad → verify SendLog still exists.

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: final adjustments for sendlog snapshot migration"
```

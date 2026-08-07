from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.scheduling.use_cases import collect_due_schedules
from app.database import Base
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.services.schedule_service import compute_next_run_at


@pytest.mark.asyncio
async def test_moscow_1730_is_due_at_1431_utc():
    created_at = datetime(2026, 8, 3, 14, 0, tzinfo=timezone.utc)
    checked_at = datetime(2026, 8, 3, 14, 31, tzinfo=timezone.utc)
    next_run_at = compute_next_run_at(
        days_of_week=[0],
        times_of_day=["17:30"],
        tz_name="Europe/Moscow",
        now=created_at,
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as db_session:
        user = User(email="telegram-due@example.com", password_hash="x", name="Due")
        db_session.add(user)
        await db_session.flush()
        ad = Ad(user_id=user.id, title="Due ad", text="Due body", images=[])
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session",
            status="active",
        )
        db_session.add_all([ad, account])
        await db_session.flush()
        group = Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type="telegram",
            group_external_id="-100123",
            name="Due group",
        )
        db_session.add(group)
        await db_session.flush()
        schedule = Schedule(
            ad_id=ad.id,
            account_id=account.id,
            group_ids=[group.id],
            days_of_week=[0],
            times_of_day=["17:30"],
            timezone="Europe/Moscow",
            is_active=True,
            next_run_at=next_run_at,
        )
        db_session.add(schedule)
        await db_session.commit()

        async def allow_send(_session, _user_id, _action):
            return True, ""

        tasks = await collect_due_schedules(
            db_session,
            now=checked_at,
            check_limit=allow_send,
        )

        assert next_run_at == datetime(2026, 8, 3, 14, 30, tzinfo=timezone.utc)
        assert len(tasks) == 1
        assert tasks[0].type == "tg_user"

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

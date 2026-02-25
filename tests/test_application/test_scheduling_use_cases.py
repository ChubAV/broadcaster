from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.scheduling.use_cases import collect_due_schedules, DispatchTask
from app.database import Base
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User


@pytest.mark.asyncio
async def test_collect_due_schedules_respects_billing_limit():
    """collect_due_schedules не создаёт задач, если billing limit не позволяет."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        user = User(email="u@test.com", password_hash="x", name="U")
        session.add(user)
        await session.commit()

        ad = Ad(user_id=user.id, title="T", text="Body", images=[])
        account = MessengerAccount(user_id=user.id, type="tg_user", credentials="sess", status="active")
        session.add_all([ad, account])
        await session.commit()

        group = Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type="telegram",
            group_external_id="-100",
            name="G",
        )
        session.add(group)
        await session.commit()

        schedule = Schedule(
            ad_id=ad.id,
            account_id=account.id,
            group_ids=[group.id],
            days_of_week=[0],
            times_of_day=["09:00"],
            is_active=True,
            next_run_at=datetime.now(timezone.utc),
            timezone="UTC",
        )
        session.add(schedule)
        await session.commit()

        async def fake_check_limit(db_session, user_id: int, action: str):
            assert db_session is session
            assert action == "send"
            return False, "limit"

        tasks = await collect_due_schedules(
            session,
            now=datetime.now(timezone.utc),
            check_limit=fake_check_limit,
        )

        assert tasks == []

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


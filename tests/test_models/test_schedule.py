import pytest
from datetime import datetime, timezone

from app.models.user import User
from app.models.messenger_account import MessengerAccount
from app.models.ad import Ad
from app.models.schedule import Schedule


@pytest.mark.asyncio
async def test_create_schedule(db_session):
    user = User(
        email="schedule@example.com",
        password_hash="hashed",
        name="Schedule User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials='{"token": "bot_token"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    ad = Ad(
        user_id=user.id,
        title="Scheduled Ad",
        text="Ad text",
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    next_run = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[1, 2, 3],
        days_of_week=[1, 3, 5],
        times_of_day=["09:00", "15:00"],
        is_active=True,
        next_run_at=next_run,
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.id is not None
    assert schedule.ad_id == ad.id
    assert schedule.account_id == account.id
    assert schedule.group_ids == [1, 2, 3]
    assert schedule.days_of_week == [1, 3, 5]
    assert schedule.times_of_day == ["09:00", "15:00"]
    assert schedule.is_active is True
    # SQLite strips timezone info; compare naive datetime values
    assert schedule.next_run_at.replace(tzinfo=None) == next_run.replace(tzinfo=None)
    assert schedule.created_at is not None


@pytest.mark.asyncio
async def test_schedule_default_values(db_session):
    user = User(
        email="schedule_default@example.com",
        password_hash="hashed",
        name="Default Schedule User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials='{"token": "token"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    ad = Ad(
        user_id=user.id,
        title="Default Schedule Ad",
        text="Text",
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.group_ids == []
    assert schedule.days_of_week == []
    assert schedule.times_of_day == []
    assert schedule.is_active is True
    assert schedule.next_run_at is None

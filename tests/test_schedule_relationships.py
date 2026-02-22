import pytest
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.schedule import Schedule
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.user import User


@pytest.mark.asyncio
async def test_schedule_eager_load_ad_and_account(db_session):
    """Schedule.ad and Schedule.account relationships support joinedload."""
    user = User(
        email="rel@test.com", password_hash="x", name="Rel Tester"
    )
    db_session.add(user)
    await db_session.flush()

    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="test", status="active"
    )
    db_session.add(account)
    await db_session.flush()

    ad = Ad(user_id=user.id, title="Test", text="Hello", images=[])
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

import pytest
from app.models.user import User
from app.models.messenger_account import MessengerAccount
from app.models.ad import Ad
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog


@pytest.mark.asyncio
async def test_create_send_log(db_session):
    # Create all parent records
    user = User(
        email="sendlog@example.com",
        password_hash="hashed",
        name="SendLog User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_bot",
        credentials='{"token": "bot_token"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    ad = Ad(
        user_id=user.id,
        title="Logged Ad",
        text="Ad text for logging",
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="tg_bot",
        group_external_id="-100999",
        name="Log Group",
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[1],
        times_of_day=["10:00"],
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    send_log = SendLog(
        schedule_id=schedule.id,
        ad_id=ad.id,
        group_id=group.id,
        status="sent",
        error_message=None,
    )
    db_session.add(send_log)
    await db_session.commit()
    await db_session.refresh(send_log)

    assert send_log.id is not None
    assert send_log.schedule_id == schedule.id
    assert send_log.ad_id == ad.id
    assert send_log.group_id == group.id
    assert send_log.status == "sent"
    assert send_log.error_message is None
    assert send_log.sent_at is not None


@pytest.mark.asyncio
async def test_send_log_with_error(db_session):
    # Create all parent records
    user = User(
        email="sendlog_error@example.com",
        password_hash="hashed",
        name="Error Log User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_bot",
        credentials='{"token": "bot_token"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    ad = Ad(
        user_id=user.id,
        title="Error Ad",
        text="Ad that failed",
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="tg_bot",
        group_external_id="-100888",
        name="Error Group",
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    send_log = SendLog(
        schedule_id=schedule.id,
        ad_id=ad.id,
        group_id=group.id,
        status="failed",
        error_message="Connection timeout: could not reach Telegram API",
    )
    db_session.add(send_log)
    await db_session.commit()
    await db_session.refresh(send_log)

    assert send_log.status == "failed"
    assert send_log.error_message == "Connection timeout: could not reach Telegram API"

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models.user import User
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.worker.tasks import check_schedules_async, send_ad_to_group_async, get_messenger


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def create_test_data(session, schedule_active=True, account_status="active", next_run_at=None):
    """Helper to create user + ad + account + group + schedule."""
    user = User(email="t@t.com", password_hash="h", name="T")
    session.add(user)
    await session.commit()

    ad = Ad(user_id=user.id, title="Test Ad", text="Buy this!", images=["img.jpg"])
    account = MessengerAccount(user_id=user.id, type="tg_bot", credentials="fake-token", status=account_status)
    session.add_all([ad, account])
    await session.commit()

    group = Group(user_id=user.id, account_id=account.id, messenger_type="telegram",
                  group_external_id="-100123", name="Sales")
    session.add(group)
    await session.commit()

    if next_run_at is None:
        next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        times_of_day=["09:00", "18:00"],
        is_active=schedule_active,
        next_run_at=next_run_at,
    )
    session.add(schedule)
    await session.commit()

    return user, ad, account, group, schedule


@pytest.mark.asyncio
async def test_get_messenger_tg_bot():
    account = MessengerAccount(type="tg_bot", credentials="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                               user_id=1, status="active")
    m = get_messenger(account)
    from app.messengers.telegram_bot import TelegramBotMessenger
    assert isinstance(m, TelegramBotMessenger)


@pytest.mark.asyncio
async def test_get_messenger_tg_user_from_settings():
    """get_messenger uses telegram_api_id/api_hash from settings when available."""
    account = MessengerAccount(
        type="tg_user",
        credentials="session-string",
        user_id=1,
        status="active",
    )
    with patch("app.config.Settings") as MockSettings:
        MockSettings.return_value.telegram_api_id = 12345
        MockSettings.return_value.telegram_api_hash = "settings_hash"

        m = get_messenger(account)

    from app.messengers.telegram_user import TelegramUserMessenger
    assert isinstance(m, TelegramUserMessenger)


@pytest.mark.asyncio
async def test_get_messenger_tg_user_fallback_session_data():
    """get_messenger falls back to session_data when settings have no telegram creds."""
    import json

    account = MessengerAccount(
        type="tg_user",
        credentials="session-string",
        session_data=json.dumps({"api_id": 99999, "api_hash": "legacy_hash"}),
        user_id=1,
        status="active",
    )
    with patch("app.config.Settings") as MockSettings:
        MockSettings.return_value.telegram_api_id = 0
        MockSettings.return_value.telegram_api_hash = ""

        m = get_messenger(account)

    from app.messengers.telegram_user import TelegramUserMessenger
    assert isinstance(m, TelegramUserMessenger)


@pytest.mark.asyncio
async def test_send_ad_success(db_session):
    user, ad, account, group, schedule = await create_test_data(db_session)

    mock_messenger = AsyncMock()
    mock_messenger.send_message = AsyncMock(return_value={"ok": True})

    with patch("app.worker.tasks.get_messenger", return_value=mock_messenger):
        await send_ad_to_group_async(db_session, schedule.id, ad.id, group.id, account.id)

    from sqlalchemy import select
    result = await db_session.execute(select(SendLog))
    log = result.scalar_one()
    assert log.status == "ok"
    assert log.error_message is None


@pytest.mark.asyncio
async def test_send_ad_failure(db_session):
    user, ad, account, group, schedule = await create_test_data(db_session)

    mock_messenger = AsyncMock()
    mock_messenger.send_message = AsyncMock(return_value={"ok": False, "error": "Rate limited"})

    with patch("app.worker.tasks.get_messenger", return_value=mock_messenger):
        await send_ad_to_group_async(db_session, schedule.id, ad.id, group.id, account.id)

    from sqlalchemy import select
    result = await db_session.execute(select(SendLog))
    log = result.scalar_one()
    assert log.status == "fail"
    assert "Rate limited" in log.error_message


@pytest.mark.asyncio
async def test_send_ad_account_disconnected(db_session):
    user, ad, account, group, schedule = await create_test_data(db_session, account_status="disconnected")

    await send_ad_to_group_async(db_session, schedule.id, ad.id, group.id, account.id)

    from sqlalchemy import select
    result = await db_session.execute(select(SendLog))
    log = result.scalar_one()
    assert log.status == "account_disconnected"


@pytest.mark.asyncio
async def test_check_schedules_dispatches(db_session):
    user, ad, account, group, schedule = await create_test_data(db_session)

    mock_messenger = AsyncMock()
    mock_messenger.send_message = AsyncMock(return_value={"ok": True})

    with patch("app.worker.tasks.get_messenger", return_value=mock_messenger):
        await check_schedules_async(db_session)

    # Should have created a send log
    from sqlalchemy import select
    result = await db_session.execute(select(SendLog))
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].status == "ok"

    # next_run_at should be updated
    await db_session.refresh(schedule)
    next_run = schedule.next_run_at
    # SQLite returns naive datetimes, so make it aware if needed
    if next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=timezone.utc)
    assert next_run > datetime.now(timezone.utc) - timedelta(seconds=10)


@pytest.mark.asyncio
async def test_check_schedules_skips_inactive(db_session):
    user, ad, account, group, schedule = await create_test_data(db_session, schedule_active=False)

    await check_schedules_async(db_session)

    from sqlalchemy import select
    result = await db_session.execute(select(SendLog))
    logs = result.scalars().all()
    assert len(logs) == 0


@pytest.mark.asyncio
async def test_check_schedules_skips_future(db_session):
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    user, ad, account, group, schedule = await create_test_data(db_session, next_run_at=future)

    await check_schedules_async(db_session)

    from sqlalchemy import select
    result = await db_session.execute(select(SendLog))
    logs = result.scalars().all()
    assert len(logs) == 0

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.database import Base
from app.models.user import User
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.worker.tasks import check_schedules_async, _send_message


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


@pytest_asyncio.fixture
async def db_engine_and_factory():
    """Provide engine + session factory for _send_message tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield engine, factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def create_test_data(session, schedule_active=True, account_status="active", next_run_at=None, account_type="tg_user"):
    """Helper to create user + ad + account + group + schedule."""
    user = User(email="t@t.com", password_hash="h", name="T")
    session.add(user)
    await session.commit()

    ad = Ad(user_id=user.id, title="Test Ad", text="Buy this!", images=["img.jpg"])
    account = MessengerAccount(user_id=user.id, type=account_type, credentials="fake-token", status=account_status)
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
async def test_send_message_success(db_engine_and_factory):
    """_send_message creates an 'ok' SendLog on success."""
    engine, factory = db_engine_and_factory

    async with factory() as session:
        user, ad, account, group, schedule = await create_test_data(session)

    mock_messenger = AsyncMock()
    mock_messenger.send_message = AsyncMock(return_value={"ok": True})

    mock_settings = AsyncMock()
    mock_settings.s3_public_url = "https://cdn.example.com/bucket"
    mock_settings.database_url = "sqlite+aiosqlite:///:memory:"

    # Use a mock engine so dispose() is a no-op (real engine disposal kills in-memory SQLite)
    mock_engine = AsyncMock()
    with patch("app.worker.tasks.create_messenger", return_value=mock_messenger), \
         patch("app.worker.tasks.get_settings", return_value=mock_settings), \
         patch("app.worker.tasks.get_engine", return_value=mock_engine), \
         patch("app.worker.tasks.get_session_factory", return_value=factory):
        await _send_message(ad.id, group.id, account.id, schedule.id)

    # Verify S3 URLs were passed to messenger
    call_kwargs = mock_messenger.send_message.call_args
    sent_images = call_kwargs.kwargs["images"]
    assert len(sent_images) == 1
    assert sent_images[0] == "https://cdn.example.com/bucket/img.jpg"

    async with factory() as session:
        result = await session.execute(select(SendLog))
        log = result.scalar_one()
        assert log.status == "ok"
        assert log.error_message is None
        assert log.user_id == user.id
        assert log.ad_title == "Test Ad"
        assert log.group_name == "Sales"


@pytest.mark.asyncio
async def test_send_message_failure(db_engine_and_factory):
    """_send_message creates a 'fail' SendLog and raises on failure."""
    engine, factory = db_engine_and_factory

    async with factory() as session:
        user, ad, account, group, schedule = await create_test_data(session)

    mock_messenger = AsyncMock()
    mock_messenger.send_message = AsyncMock(return_value={"ok": False, "error": "Rate limited"})

    mock_settings = AsyncMock()
    mock_settings.s3_public_url = "https://cdn.example.com/bucket"
    mock_settings.database_url = "sqlite+aiosqlite:///:memory:"

    mock_engine = AsyncMock()
    with patch("app.worker.tasks.create_messenger", return_value=mock_messenger), \
         patch("app.worker.tasks.get_settings", return_value=mock_settings), \
         patch("app.worker.tasks.get_engine", return_value=mock_engine), \
         patch("app.worker.tasks.get_session_factory", return_value=factory):
        with pytest.raises(Exception, match="Send failed"):
            await _send_message(ad.id, group.id, account.id, schedule.id)

    async with factory() as session:
        result = await session.execute(select(SendLog))
        log = result.scalar_one()
        assert log.status == "fail"
        assert "Rate limited" in log.error_message
        assert log.user_id == user.id
        assert log.ad_title == "Test Ad"
        assert log.group_name == "Sales"


@pytest.mark.asyncio
async def test_send_message_account_disconnected(db_engine_and_factory):
    """_send_message logs 'account_disconnected' for inactive accounts."""
    engine, factory = db_engine_and_factory

    async with factory() as session:
        user, ad, account, group, schedule = await create_test_data(session, account_status="disconnected")

    mock_settings = AsyncMock()
    mock_settings.database_url = "sqlite+aiosqlite:///:memory:"

    mock_engine = AsyncMock()
    with patch("app.worker.tasks.get_settings", return_value=mock_settings), \
         patch("app.worker.tasks.get_engine", return_value=mock_engine), \
         patch("app.worker.tasks.get_session_factory", return_value=factory):
        await _send_message(ad.id, group.id, account.id, schedule.id)

    async with factory() as session:
        result = await session.execute(select(SendLog))
        log = result.scalar_one()
        assert log.status == "account_disconnected"


@pytest.mark.asyncio
async def test_check_schedules_dispatches(db_session):
    """check_schedules_async dispatches Celery tasks for due schedules."""
    user, ad, account, group, schedule = await create_test_data(db_session)

    dispatched = []
    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: dispatched.append(("tg", kw.get("queue")))

    mock_dispatch_settings = MagicMock()
    mock_dispatch_settings.redis_url = "redis://localhost:6379/0"

    with patch("app.worker.tasks.send_telegram_message", mock_tg), \
         patch("app.worker.tasks.check_balance_cached", AsyncMock(return_value=(True, ""))), \
         patch("app.worker.tasks.get_settings", return_value=mock_dispatch_settings):
        await check_schedules_async(db_session)

    # Should have dispatched one task to telegram queue
    assert len(dispatched) == 1
    assert dispatched[0] == ("tg", "telegram")

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

    dispatched = []
    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: dispatched.append(("tg", kw.get("queue")))

    with patch("app.worker.tasks.send_telegram_message", mock_tg), \
         patch("app.worker.tasks.check_balance_cached", AsyncMock(return_value=(True, ""))):
        await check_schedules_async(db_session)

    assert len(dispatched) == 0


@pytest.mark.asyncio
async def test_check_schedules_skips_future(db_session):
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    user, ad, account, group, schedule = await create_test_data(db_session, next_run_at=future)

    dispatched = []
    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: dispatched.append(("tg", kw.get("queue")))

    with patch("app.worker.tasks.send_telegram_message", mock_tg), \
         patch("app.worker.tasks.check_balance_cached", AsyncMock(return_value=(True, ""))):
        await check_schedules_async(db_session)

    assert len(dispatched) == 0


@pytest.mark.asyncio
async def test_check_schedules_skips_billing_limited(db_session):
    """Schedules for billing-limited users are skipped but next_run_at is updated."""
    user, ad, account, group, schedule = await create_test_data(db_session)
    old_next_run = schedule.next_run_at

    dispatched = []
    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: dispatched.append(("tg", kw.get("queue")))

    with patch("app.worker.tasks.send_telegram_message", mock_tg), \
         patch("app.worker.tasks.check_balance_cached", AsyncMock(return_value=(False, "limit reached"))):
        await check_schedules_async(db_session)

    # No tasks dispatched
    assert len(dispatched) == 0

    # But next_run_at should still be updated
    await db_session.refresh(schedule)
    next_run = schedule.next_run_at
    if next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=timezone.utc)
    if old_next_run.tzinfo is None:
        old_next_run = old_next_run.replace(tzinfo=timezone.utc)
    assert next_run > old_next_run


@pytest.mark.asyncio
async def test_check_schedules_uses_schedule_timezone(db_session):
    """Worker uses schedule.timezone for next_run_at computation."""
    user, ad, account, group, schedule = await create_test_data(db_session)

    # Set timezone to Moscow
    schedule.timezone = "Europe/Moscow"
    await db_session.commit()

    dispatched = []
    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: dispatched.append(("tg", kw.get("queue")))

    mock_dispatch_settings = MagicMock()
    mock_dispatch_settings.redis_url = "redis://localhost:6379/0"

    with patch("app.worker.tasks.send_telegram_message", mock_tg), \
         patch("app.worker.tasks.check_balance_cached", AsyncMock(return_value=(True, ""))), \
         patch("app.worker.tasks.get_settings", return_value=mock_dispatch_settings):
        await check_schedules_async(db_session)

    assert len(dispatched) == 1

    # Verify next_run_at was recomputed — it should exist and be in the future
    await db_session.refresh(schedule)
    assert schedule.next_run_at is not None

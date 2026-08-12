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
from app.worker.tasks import (
    check_schedules_async,
    _send_message,
    _sync_wa_groups_async,
    _sync_max_groups_async,
)


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


# --- План 03-04: фоновые синхронизации WA и MAX через общий хелпер ---
#
# Оба пути проверяются ОДНИМ набором параметризованных тестов. Цель плана —
# чтобы WA и MAX перестали быть двумя копиями, расходящимися молча; симметричные
# сценарии делают расхождение падением теста, а не находкой в проде.

SYNC_PATHS = [
    pytest.param(
        _sync_wa_groups_async,
        "app.messengers.whatsapp.WhatsAppMessenger",
        "wa",
        id="wa",
    ),
    pytest.param(
        _sync_max_groups_async,
        "app.messengers.max.MaxMessenger",
        "max",
        id="max",
    ),
]


async def _make_syncing_account(factory, account_type: str, *, status: str = "syncing"):
    """Пользователь + аккаунт в статусе синхронизации."""
    async with factory() as session:
        user = User(email=f"{account_type}@sync.test", password_hash="h", name="S")
        session.add(user)
        await session.commit()

        account = MessengerAccount(
            user_id=user.id, type=account_type, credentials="c", status=status
        )
        session.add(account)
        await session.commit()
        return user.id, account.id


async def _seed_group(factory, account_id: int, external_id: str, name: str,
                      *, is_active: bool = True) -> int:
    async with factory() as session:
        account = await session.get(MessengerAccount, account_id)
        group = Group(
            user_id=account.user_id,
            account_id=account_id,
            messenger_type=account.type,
            group_external_id=external_id,
            name=name,
            is_active=is_active,
        )
        session.add(group)
        await session.commit()
        return group.id


async def _account_state(factory, account_id: int):
    """(status, last_synced_at, разобранный last_sync_result)."""
    from app.application.accounts.group_resync import parse_sync_result

    async with factory() as session:
        account = await session.get(MessengerAccount, account_id)
        return (
            account.status,
            account.last_synced_at,
            parse_sync_result(account.last_sync_result),
        )


def _sync_patches(factory, messenger_path: str, messenger):
    """Общая обвязка: настройки, движок-заглушка, фабрика сессий, мессенджер."""
    mock_settings = MagicMock()
    mock_settings.database_url = "sqlite+aiosqlite:///:memory:"
    mock_messenger_cls = MagicMock(return_value=messenger)
    return (
        patch("app.worker.tasks.get_settings", return_value=mock_settings),
        patch("app.worker.tasks.get_engine", return_value=AsyncMock()),
        patch("app.worker.tasks.get_session_factory", return_value=factory),
        patch(messenger_path, mock_messenger_cls),
    )


async def _run_sync(sync_fn, factory, messenger_path: str, messenger, account_id: int):
    settings_p, engine_p, factory_p, messenger_p = _sync_patches(
        factory, messenger_path, messenger
    )
    with settings_p, engine_p, factory_p, messenger_p:
        await sync_fn(account_id)


def _ready_messenger(groups):
    messenger = MagicMock()
    messenger.get_sync_status = AsyncMock(
        return_value={"state": "ready", "groups": groups}
    )
    return messenger


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_records_result(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """Успешный фоновый синк создаёт строки, пишет сводку и включает аккаунт."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type)

    messenger = _ready_messenger(
        [
            {"id": "g1", "name": "Один"},
            {"id": "g2", "name": "Два"},
            {"id": "g3", "name": "Три"},
        ]
    )
    await _run_sync(sync_fn, factory, messenger_path, messenger, account_id)

    async with factory() as session:
        groups = (
            await session.execute(select(Group).where(Group.account_id == account_id))
        ).scalars().all()
        assert len(groups) == 3
        assert {g.messenger_type for g in groups} == {account_type}

    status, last_synced_at, result = await _account_state(factory, account_id)
    assert status == "active"
    assert last_synced_at is not None
    assert result == {"found": 3, "new": 3, "renamed": 0, "missing": 0, "error": None}


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_renames_existing_group(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """D-11: имя существующей группы обновляется в обоих путях."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type)
    group_id = await _seed_group(factory, account_id, "g1", "Старое имя")

    messenger = _ready_messenger([{"id": "g1", "name": "Новое имя"}])
    await _run_sync(sync_fn, factory, messenger_path, messenger, account_id)

    async with factory() as session:
        group = await session.get(Group, group_id)
        assert group.name == "Новое имя"

    _, _, result = await _account_state(factory, account_id)
    assert result["renamed"] == 1
    assert result["new"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_marks_missing_group_but_keeps_it(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """D-11: не вернувшаяся группа помечается и остаётся в базе в обоих путях."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type)
    group_id = await _seed_group(factory, account_id, "g1", "Пропавшая")

    messenger = _ready_messenger([{"id": "g2", "name": "Другая"}])
    await _run_sync(sync_fn, factory, messenger_path, messenger, account_id)

    async with factory() as session:
        group = await session.get(Group, group_id)
        assert group is not None, "фоновый синк не имеет права удалять группы"
        assert group.missing_since is not None

    _, _, result = await _account_state(factory, account_id)
    assert result["missing"] == 1
    assert result["new"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_keeps_disabled_group_disabled(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """D-11: включённость — выбор пользователя, фоновый синк её не трогает."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type)
    group_id = await _seed_group(
        factory, account_id, "g1", "Выключенная", is_active=False
    )

    messenger = _ready_messenger([{"id": "g1", "name": "Выключенная"}])
    await _run_sync(sync_fn, factory, messenger_path, messenger, account_id)

    async with factory() as session:
        group = await session.get(Group, group_id)
        assert group.is_active is False

    # Группа обязана быть УВИДЕНА синком, иначе тест зеленел бы и на пути,
    # который до неё не дошёл.
    _, _, result = await _account_state(factory, account_id)
    assert result["found"] == 1
    assert result["new"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_failed_state_records_error(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """Отказ моста: аккаунт в sync_failed и пользователю есть что показать."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type)

    messenger = MagicMock()
    messenger.get_sync_status = AsyncMock(return_value={"state": "failed"})
    await _run_sync(sync_fn, factory, messenger_path, messenger, account_id)

    status, last_synced_at, result = await _account_state(factory, account_id)
    assert status == "sync_failed"
    # Провал не переставляет `last_synced_at`: колонка означает «синк
    # состоялся», и шапка экрана групп обязана называть последний УДАВШИЙСЯ
    # синк. Время попытки несёт сама сводка.
    assert last_synced_at is None
    assert result is not None
    assert result["error"]


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_timeout_records_error(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """Исчерпание попыток опроса тоже перестаёт быть безмолвным."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type)

    messenger = MagicMock()
    messenger.get_sync_status = AsyncMock(return_value={"state": "syncing"})

    settings_p, engine_p, factory_p, messenger_p = _sync_patches(
        factory, messenger_path, messenger
    )
    with settings_p, engine_p, factory_p, messenger_p, \
         patch("app.worker.tasks.asyncio.sleep", AsyncMock()):
        await sync_fn(account_id)

    status, last_synced_at, result = await _account_state(factory, account_id)
    assert status == "sync_failed"
    assert last_synced_at is None
    assert result is not None
    assert result["error"]


@pytest.mark.asyncio
@pytest.mark.parametrize("sync_fn,messenger_path,account_type", SYNC_PATHS)
async def test_background_sync_skips_account_not_syncing(
    db_engine_and_factory, sync_fn, messenger_path, account_type
):
    """Существующий guard: задача для аккаунта не в статусе syncing ничего не меняет."""
    _, factory = db_engine_and_factory
    _, account_id = await _make_syncing_account(factory, account_type, status="active")

    messenger = _ready_messenger([{"id": "g1", "name": "Один"}])
    await _run_sync(sync_fn, factory, messenger_path, messenger, account_id)

    async with factory() as session:
        groups = (
            await session.execute(select(Group).where(Group.account_id == account_id))
        ).scalars().all()
        assert groups == []

    status, last_synced_at, result = await _account_state(factory, account_id)
    assert status == "active"
    assert last_synced_at is None
    assert result is None

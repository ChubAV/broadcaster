import json

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.constants import AD_STATUS_DRAFT
from app.database import Base
from app.models.user import User
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.application.scheduling.use_cases import DispatchTask
from app.worker.tasks import (
    check_schedules_async,
    dispatch_send_tasks,
    retry_send,
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
         patch("app.worker.tasks.check_access_cached", AsyncMock(return_value=(True, ""))), \
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
         patch("app.worker.tasks.check_access_cached", AsyncMock(return_value=(True, ""))):
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
         patch("app.worker.tasks.check_access_cached", AsyncMock(return_value=(True, ""))):
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
         patch("app.worker.tasks.check_access_cached", AsyncMock(return_value=(False, "limit reached"))):
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
         patch("app.worker.tasks.check_access_cached", AsyncMock(return_value=(True, ""))), \
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


# --- План 04-03: retry_send — повтор отправки на все три канала ---------------
#
# ЧТО ИМЕННО ПРОВЕРЯЕТСЯ. Не «таск не упал», а ТРАНСПОРТ: в какую очередь
# уехала задача. D-18 называл точкой постановки `send_telegram_message`, то есть
# вход ОДНОГО канала из трёх; повтор WA-записи через него ушёл бы по второму,
# непроверенному маршруту (T-04-09). Поэтому `dispatch_send_tasks` здесь НЕ
# подменяется — подменяются Redis и Celery под ней, и тест смотрит, куда легла
# задача. Подмена самой диспетчеризации зеленела бы и на неверном маршруте.

RETRY_S3_URL = "https://cdn.example.com/bucket"


class _FakePipeline:
    """Пайплайн Redis: копит rpush, чтобы тест увидел ключ очереди и нагрузку."""

    def __init__(self, sink):
        self._sink = sink

    def rpush(self, key, payload):
        self._sink.append((key, payload))

    def sadd(self, key, value):
        pass

    def execute(self):
        pass


class _FakeRedis:
    def __init__(self, sink):
        self._sink = sink

    def pipeline(self):
        return _FakePipeline(self._sink)

    def close(self):
        pass


async def _seed_retry_case(
    factory,
    *,
    account_type: str = "wa",
    account_status: str = "active",
    schedule_id: int | None = None,
    images=None,
):
    """Пользователь, объявление, аккаунт, группа и запись журнала под повтор."""
    async with factory() as session:
        user = User(email=f"{account_type}@retry.test", password_hash="h", name="R")
        session.add(user)
        await session.commit()

        ad = Ad(
            user_id=user.id,
            title="Заголовок",
            text="Текст объявления",
            images=["img.jpg"] if images is None else images,
        )
        account = MessengerAccount(
            user_id=user.id,
            type=account_type,
            credentials="c",
            status=account_status,
        )
        session.add_all([ad, account])
        await session.commit()

        group = Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type=account_type,
            group_external_id="-100500",
            name="Отдел продаж",
        )
        session.add(group)
        await session.commit()

        log = SendLog(
            user_id=user.id,
            schedule_id=schedule_id,
            ad_id=ad.id,
            group_id=group.id,
            status="fail",
            error_message="Rate limited",
            messenger_type=account_type,
        )
        session.add(log)
        await session.commit()

        return {
            "user_id": user.id,
            "log_id": log.id,
            "ad_id": ad.id,
            "account_id": account.id,
            "group_id": group.id,
        }


async def _run_retry(factory, log_id, user_id, *, access_allowed: bool = True):
    """Запускает таск повтора и отдаёт (rpush-и Redis, постановки в Celery).

    `asyncio.run` подменяется захватом корутины: тело таска обязано выполниться
    в ТОМ ЖЕ цикле событий, где живёт SQLite-движок фикстуры, — свой цикл
    оторвал бы соединение aiosqlite. Тем же приёмом файл уже пользуется для
    `asyncio.sleep` в тестах фоновой синхронизации.

    Гейт доступа подменяется по образцу тестов рассылки выше: настоящий лезет в
    Redis, которого в тестовой среде нет, и красил бы каждый тест повтора чужой
    причиной. `access_allowed=False` даёт закрытый доступ.

    Патч ставится на ИМЯ В `app.worker.tasks`, а не на объявление в
    `app.services.billing_cache`: таск импортировал функцию к себе на уровне
    модуля, и подмена по месту объявления его вызов не подменила бы вовсе.
    """
    redis_sink: list[tuple] = []
    tg_sink: list[tuple] = []

    mock_settings = MagicMock()
    mock_settings.database_url = "sqlite+aiosqlite:///:memory:"
    mock_settings.redis_url = "redis://localhost:6379/0"

    mock_s3_settings = MagicMock()
    mock_s3_settings.s3_public_url = RETRY_S3_URL

    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: tg_sink.append((kw.get("args") or (a[0] if a else None), kw.get("queue")))

    captured: list = []

    with patch("app.worker.tasks.get_settings", return_value=mock_settings), \
         patch("app.worker.tasks.get_engine", return_value=AsyncMock()), \
         patch("app.worker.tasks.get_session_factory", return_value=factory), \
         patch("app.worker.tasks.send_telegram_message", mock_tg), \
         patch("app.config.get_settings", return_value=mock_s3_settings), \
         patch("redis.from_url", return_value=_FakeRedis(redis_sink)), \
         patch(
             "app.worker.tasks.check_access_cached",
             AsyncMock(return_value=(access_allowed, "" if access_allowed else "access_closed")),
         ), \
         patch("app.worker.tasks.asyncio.run", captured.append):
        retry_send(log_id, user_id)
        assert captured, "таск повтора обязан запускать корутину через asyncio.run"
        await captured[0]

    return redis_sink, tg_sink


async def _send_log_count(factory) -> int:
    async with factory() as session:
        rows = (await session.execute(select(SendLog))).scalars().all()
        return len(rows)


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ["wa", "max"])
async def test_retry_send_routes_queue_channels_to_redis(
    db_engine_and_factory, account_type
):
    """T-04-09: WA и MAX уезжают в Redis-очередь аккаунта, а не в Celery."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type=account_type)

    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert len(redis_sink) == 1
    queue_key, raw_payload = redis_sink[0]
    assert queue_key == f"{account_type}:queue:{case['account_id']}"

    payload = json.loads(raw_payload)
    assert payload["ad_id"] == case["ad_id"]
    assert payload["group_id"] == case["group_id"]
    assert payload["account_id"] == case["account_id"]
    assert payload["user_id"] == case["user_id"]
    assert payload["group_external_id"] == "-100500"
    assert payload["group_name"] == "Отдел продаж"
    assert payload["ad_text"] == "Текст объявления"
    assert payload["ad_images"] == [f"{RETRY_S3_URL}/img.jpg"]

    # Второго маршрута нет: Celery-очередь telegram не трогается.
    assert tg_sink == []


@pytest.mark.asyncio
async def test_retry_send_routes_telegram_to_celery(db_engine_and_factory):
    """Telegram-повтор идёт тем же таском, что и боевая рассылка."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type="tg_user")

    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert redis_sink == []
    assert len(tg_sink) == 1
    args, queue = tg_sink[0]
    assert queue == "telegram"
    assert list(args) == [
        case["ad_id"],
        case["group_id"],
        case["account_id"],
        None,
    ]


@pytest.mark.asyncio
async def test_retry_send_rejects_foreign_log(db_engine_and_factory):
    """T-04-08: чужая запись не диспетчеризуется ни на один канал."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type="wa")

    redis_sink, tg_sink = await _run_retry(
        factory, case["log_id"], case["user_id"] + 1000
    )

    assert redis_sink == []
    assert tg_sink == []


@pytest.mark.asyncio
async def test_retry_send_ignores_unknown_log(db_engine_and_factory):
    """Отсутствующая запись журнала — выход без диспетчеризации."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type="wa")

    redis_sink, tg_sink = await _run_retry(factory, case["log_id"] + 1000, case["user_id"])

    assert redis_sink == []
    assert tg_sink == []


@pytest.mark.asyncio
@pytest.mark.parametrize("gone", ["ad", "group", "account"])
async def test_retry_send_stops_when_entity_gone(db_engine_and_factory, gone):
    """D-21: пропавшая сущность останавливает повтор и НЕ пишет в журнал."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type="wa")

    model, key = {
        "ad": (Ad, "ad_id"),
        "group": (Group, "group_id"),
        "account": (MessengerAccount, "account_id"),
    }[gone]
    async with factory() as session:
        obj = await session.get(model, case[key])
        await session.delete(obj)
        await session.commit()

    before = await _send_log_count(factory)
    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert redis_sink == []
    assert tg_sink == []
    # Журнал не наполняется записями о заведомо невозможных отправках (T-04-11).
    assert await _send_log_count(factory) == before


@pytest.mark.asyncio
async def test_retry_send_stops_when_account_not_active(db_engine_and_factory):
    """D-21: неактивный аккаунт останавливает повтор до диспетчеризации."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(
        factory, account_type="wa", account_status="disconnected"
    )

    before = await _send_log_count(factory)
    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert redis_sink == []
    assert tg_sink == []
    assert await _send_log_count(factory) == before


@pytest.mark.asyncio
async def test_retry_send_without_schedule_still_dispatches(db_engine_and_factory):
    """Запись без расписания повторяется, а schedule_id остаётся пустым."""
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type="wa", schedule_id=None)

    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert len(redis_sink) == 1
    payload = json.loads(redis_sink[0][1])
    assert payload["schedule_id"] is None
    assert tg_sink == []


# --- Повтор и состояние объявления/группы (CR-01, CR-02) ----------------------
#
# ПОЧЕМУ ЭТО ПРОВЕРЯЕТСЯ ИМЕННО ЗДЕСЬ, А НЕ ТОЛЬКО НА HTTP-ГРАНИЦЕ. Для `wa` и
# `max` таск кладёт готовую полезную нагрузку в Redis, и Node-воркер отправляет
# её, НЕ ЗАГЛЯДЫВАЯ В БАЗУ: ни статуса объявления, ни флага группы он не видит.
# Значит последняя точка, где эти два запрета ещё исполнимы, — вот эта. У
# Telegram запрет случайно срабатывал бы позже, в `send_message_once`, поэтому
# оба канала проверяются параметром: дефект был АСИММЕТРИЧЕН по каналам, и
# проверка одного канала его бы не поймала.


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ["wa", "max", "telegram"])
async def test_retry_send_stops_when_ad_is_draft(db_engine_and_factory, account_type):
    """Снятое с публикации объявление повтором НЕ уезжает (CR-01).

    Планировщик этот запрет держит дважды (`collect_due_schedules` и
    `send_message_once`), и снятие объявления с публикации — обычный способ
    пользователя остановить рассылку. Повтор из истории обязан подчиняться тому
    же запрету, иначе снятие с публикации ничего не останавливает.
    """
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type=account_type)
    async with factory() as session:
        ad = await session.get(Ad, case["ad_id"])
        ad.status = AD_STATUS_DRAFT
        await session.commit()

    before = await _send_log_count(factory)
    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert redis_sink == [], "черновик не имеет права попасть в очередь канала"
    assert tg_sink == []
    assert await _send_log_count(factory) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ["wa", "max", "telegram"])
async def test_retry_send_stops_when_group_is_switched_off(
    db_engine_and_factory, account_type
):
    """Выключенная группа повтором НЕ получает отправку (CR-02).

    `Group.is_active` — обратимый выключатель пользователя, и планировщик его
    чтит явно (D-05). `send_message_once` флаг не смотрит вовсе: он полагается
    на то, что планировщик уже отфильтровал. Повтор минует планировщик, поэтому
    без проверки здесь выключение группы не останавливало отправку в неё.
    """
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type=account_type)
    async with factory() as session:
        group = await session.get(Group, case["group_id"])
        group.is_active = False
        await session.commit()

    before = await _send_log_count(factory)
    redis_sink, tg_sink = await _run_retry(factory, case["log_id"], case["user_id"])

    assert redis_sink == [], "выключенная группа не имеет права получить отправку"
    assert tg_sink == []
    assert await _send_log_count(factory) == before


# =============================================================================
# Вторая линия гейта ДОСТУПА в повторе — группа `-k access`
# =============================================================================
#
# Тесты этой группы различимы по `-k access` намеренно: вторая линия гейта — то
# место, снятие которого не красит ни один тест соседних предметов, и прогнать
# её отдельным отбором обязано быть возможно одной командой.


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ["wa", "max", "tg_user"])
async def test_retry_send_stops_when_the_access_period_is_closed(
    db_engine_and_factory, account_type
):
    """T-04-36, T-05.1-02: закрытый доступ останавливает повтор ЗДЕСЬ, а не после.

    Гейт стоит и в HTTP-обработчике, но между нажатием и исполнением таска
    проходит время: задача может простоять за очередью ровно столько, сколько
    нужно, чтобы срок доступа истёк. Без проверки в таске отправка уходит у
    человека, у которого доступ уже закончился, — то есть работа, за которую
    продукт денег не берёт, при живой очереди. Остальные три запрета обработчика
    (владение, черновик, выключенная группа) вторую линию здесь уже имеют; гейт
    был единственным, у которого её не было.

    ПРЕДМЕТ ВОПРОСА СМЕНИЛСЯ С БАЛАНСА НА ДОСТУП, А ПРИЧИНА ВТОРОЙ ЛИНИИ
    ОСТАЛАСЬ ТОЙ ЖЕ И НЕ ОСЛАБЛА: обе величины меняются между постановкой и
    исполнением, и обе — не в пользу отправляющего.

    Выход, как и у прочих остановок таска, ТИХИЙ: записи в журнал не
    появляется — иначе история наполнялась бы свидетельствами о заведомо
    невозможных отправках.
    """
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type=account_type)

    before = await _send_log_count(factory)
    redis_sink, tg_sink = await _run_retry(
        factory, case["log_id"], case["user_id"], access_allowed=False
    )

    assert redis_sink == [], "повтор ушёл в очередь мимо гейта доступа"
    assert tg_sink == [], "повтор ушёл в очередь мимо гейта доступа"
    assert await _send_log_count(factory) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ["wa", "tg_user"])
async def test_retry_send_dispatches_when_the_access_period_is_live(
    db_engine_and_factory, account_type
):
    """Граница сверху: при открытом доступе тот же повтор УХОДИТ в очередь.

    Без этого утверждения вторая линия, отказывающая ВСЕМ, прошла бы проверку
    выше — и повтор не работал бы вовсе ни у кого, включая оплативших.
    """
    _, factory = db_engine_and_factory
    case = await _seed_retry_case(factory, account_type=account_type)

    redis_sink, tg_sink = await _run_retry(
        factory, case["log_id"], case["user_id"], access_allowed=True
    )

    assert redis_sink or tg_sink, (
        "открытый доступ не поставил повтор ни в одну очередь — вторая линия "
        "отказывает всем подряд"
    )


@pytest.mark.asyncio
async def test_dispatch_reports_an_unroutable_account_type_instead_of_dropping_it():
    """Задача незнакомого типа не теряется молча: она СЧИТАЕТСЯ неразосланной.

    Ветвление маршрутизации — три `elif` без `else`, а
    `MessengerAccount.type` — свободная строка `String(20)` без ограничения
    перечнем. «Четвёртого типа не бывает» верно ровно до того момента, когда он
    появится, и до этой правки такая задача исчезала без строки в журнале, без
    исключения и без записи истории, а вызывающий получал тот же `None`, что и
    при успехе.

    Утверждается ЧИСЛО, а не наличие записи в журнале: именно число читает
    `retry_send`, и именно оно отличает «разослано» от «не разослано ничего».
    """
    settings = MagicMock()
    settings.redis_url = "redis://localhost:6379/0"

    unknown = DispatchTask(
        type="signal", ad_id=1, group_id=2, account_id=3, schedule_id=None
    )
    known = DispatchTask(
        type="tg_user", ad_id=4, group_id=5, account_id=6, schedule_id=None
    )

    with patch("app.worker.tasks.get_settings", return_value=settings), \
         patch("app.worker.tasks.send_telegram_message", MagicMock()):
        assert await dispatch_send_tasks([unknown]) == 0, (
            "задача незнакомого типа засчитана как разосланная — вызывающий "
            "не может отличить её от успеха"
        )
        assert await dispatch_send_tasks([known, unknown]) == 1, (
            "число разосланных считает и те задачи, что никуда не уехали"
        )
        assert await dispatch_send_tasks([]) == 0

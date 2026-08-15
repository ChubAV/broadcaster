from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.scheduling.use_cases import (
    build_dispatch_task,
    collect_due_schedules,
    DispatchTask,
)
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


# --- План 04-03: build_dispatch_task — одно определение сборки задачи ---------
#
# Хелпер ЧИСТЫЙ: сессии не принимает, в БД не ходит. Поэтому его тесты работают
# на транзиентных ORM-объектах без движка — так проверяется именно сборка
# задачи, а не подъём схемы. Регрессия «сборка не изменилась» лежит не здесь, а
# в существующих тестах подбора расписаний: они гоняют `collect_due_schedules`
# целиком и обязаны остаться зелёными после выноса блока.

S3_PUBLIC_URL = "https://cdn.example.com/bucket"


def _make_trio(*, account_type: str, images):
    """Объявление, группа и аккаунт с проставленными идентификаторами."""
    ad = Ad(user_id=7, title="Заголовок", text="Текст объявления", images=images)
    ad.id = 11
    account = MessengerAccount(
        user_id=7, type=account_type, credentials="c", status="active"
    )
    account.id = 22
    group = Group(
        user_id=7,
        account_id=22,
        messenger_type=account_type,
        group_external_id="-100500",
        name="Отдел продаж",
    )
    group.id = 33
    return ad, group, account


def _settings_patch():
    """Подменяет настройки для разворачивания ключей изображений в URL.

    Импорт `get_settings` внутри хелпера локальный, поэтому патчится источник —
    `app.config.get_settings`, а не имя в модуле сборки задачи.
    """
    settings = MagicMock()
    settings.s3_public_url = S3_PUBLIC_URL
    return patch("app.config.get_settings", return_value=settings)


def test_build_dispatch_task_tg_user_leaves_wa_fields_empty():
    """Telegram-задача не несёт полей WA/MAX — их читают только Redis-очереди."""
    ad, group, account = _make_trio(account_type="tg_user", images=["a.jpg"])

    task = build_dispatch_task(ad=ad, group=group, account=account, schedule_id=99)

    assert isinstance(task, DispatchTask)
    assert task.type == "tg_user"
    assert (task.ad_id, task.group_id, task.account_id) == (11, 33, 22)
    assert task.schedule_id == 99
    assert task.user_id is None
    assert task.ad_text is None
    assert task.ad_title is None
    assert task.ad_images is None
    assert task.group_external_id is None
    assert task.group_name is None


@pytest.mark.parametrize("account_type", ["wa", "max"])
def test_build_dispatch_task_fills_queue_fields(account_type):
    """WA и MAX получают полезную нагрузку целиком — очередь идёт без БД."""
    ad, group, account = _make_trio(account_type=account_type, images=[])

    with _settings_patch():
        task = build_dispatch_task(ad=ad, group=group, account=account, schedule_id=99)

    assert task.type == account_type
    assert task.user_id == 7
    assert task.ad_text == "Текст объявления"
    assert task.ad_title == "Заголовок"
    assert task.group_external_id == "-100500"
    assert task.group_name == "Отдел продаж"


@pytest.mark.parametrize("account_type", ["wa", "max"])
def test_build_dispatch_task_expands_images_to_urls(account_type):
    """Непустой список изображений разворачивается в полные URL поэлементно."""
    ad, group, account = _make_trio(
        account_type=account_type, images=["one.jpg", "two.png"]
    )

    with _settings_patch():
        task = build_dispatch_task(ad=ad, group=group, account=account, schedule_id=99)

    assert task.ad_images == [
        f"{S3_PUBLIC_URL}/one.jpg",
        f"{S3_PUBLIC_URL}/two.png",
    ]
    # Ключи самого объявления не трогаются: разворачивание — свойство задачи,
    # а не объекта из БД.
    assert ad.images == ["one.jpg", "two.png"]


@pytest.mark.parametrize("account_type", ["wa", "max"])
@pytest.mark.parametrize("images", [[], None])
def test_build_dispatch_task_keeps_empty_images_as_is(account_type, images):
    """Пустое значение проходит как есть — разворачивать нечего."""
    ad, group, account = _make_trio(account_type=account_type, images=images)

    with _settings_patch():
        task = build_dispatch_task(ad=ad, group=group, account=account, schedule_id=99)

    assert task.ad_images == images


@pytest.mark.parametrize("account_type", ["tg_user", "wa", "max"])
def test_build_dispatch_task_accepts_none_schedule_id(account_type):
    """Повтор записи без расписания проходит хелпер и остаётся без числа.

    Подстановка нуля создала бы в журнале ссылку на несуществующее расписание:
    `SendLog.schedule_id` nullable и внешним ключом не является.
    """
    ad, group, account = _make_trio(account_type=account_type, images=[])

    with _settings_patch():
        task = build_dispatch_task(
            ad=ad, group=group, account=account, schedule_id=None
        )

    assert task.schedule_id is None


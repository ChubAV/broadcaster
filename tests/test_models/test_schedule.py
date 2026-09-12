import pytest
from datetime import datetime, timezone

from app.models.user import User
from app.models.messenger_account import MessengerAccount
from app.models.ad import Ad
from app.models.schedule import Schedule
from tests.conftest import a_future_run_moment


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

    # ⚠️ МОМЕНТ ЗАПУСКА ЗАДАН ЗДЕСЬ НЕ ДЛЯ КРАСОТЫ, И ПРЕЖНЯЯ ВЕРСИЯ ЭТОГО ТЕСТА
    # УТВЕРЖДАЛА РОВНО ТО, ЧТО СХЕМА ТЕПЕРЬ ЗАПРЕЩАЕТ.
    #
    # Она проверяла пару «`is_active` по умолчанию True» И «`next_run_at` пуст» —
    # то есть описывала как нормальное состояние строку, которую отбор к отправке
    # не выберет НИКОГДА (`NULL <= now` в SQL не истинно) и которая не сможет себя
    # починить (пересчёт идёт только по выбранным строкам). Именно эта пара и
    # пролежала на бою мёртвой (sched=48), и именно её запрещает
    # CHECK ck_schedules_active_requires_next_run (ревизия 0022).
    #
    # ⚠️ УМОЛЧАНИЕ КОЛОНКИ ПРИ ЭТОМ НЕ ИЗМЕНИЛОСЬ И ПРОВЕРЯЕТСЯ НИЖЕ ПО-ПРЕЖНЕМУ:
    # `is_active` НЕ ПЕРЕДАЁТСЯ и обязан прийти True. Это умолчание «в открытую»
    # (fail-open) — вторая половина причины дефекта 7833844: пропущенный аргумент
    # означал ВКЛЮЧЕНО, а не выключено. Само умолчание оставлено как есть, потому
    # что теперь его цена — отказ базы на записи, а не мёртвая строка в таблице;
    # отказ на попытке сохранить пару проверяет
    # tests/test_models/test_schedule_active_requires_next_run.py.
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        next_run_at=a_future_run_moment(),
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.group_ids == []
    assert schedule.days_of_week == []
    assert schedule.times_of_day == []
    assert schedule.is_active is True


@pytest.mark.asyncio
async def test_schedule_timezone_default(db_session):
    """Schedule.timezone defaults to 'UTC'."""
    user = User(email="tz@example.com", password_hash="h", name="TZ User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(user_id=user.id, type="tg_user", credentials="tok")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    ad = Ad(user_id=user.id, title="TZ Ad", text="text")
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    schedule = Schedule(ad_id=ad.id, account_id=account.id, next_run_at=a_future_run_moment())
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.timezone == "UTC"


@pytest.mark.asyncio
async def test_schedule_timezone_custom(db_session):
    """Schedule.timezone can be set to a custom value."""
    user = User(email="tz2@example.com", password_hash="h", name="TZ2")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(user_id=user.id, type="tg_user", credentials="tok")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    ad = Ad(user_id=user.id, title="TZ2 Ad", text="text")
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        timezone="Europe/Moscow",
        next_run_at=a_future_run_moment(),
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.timezone == "Europe/Moscow"

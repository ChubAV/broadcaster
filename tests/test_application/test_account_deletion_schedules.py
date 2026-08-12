"""Регрессионные тесты к issue #35.

При удалении messenger-аккаунта расписания НЕ должны удаляться: они остаются в
базе, переходят в статус «приостановлено» (is_active=False, next_run_at=None) и
отвязываются от удалённого аккаунта (account_id=None).
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.use_cases import (
    delete_account,
    detach_schedules_from_account,
)
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from tests.conftest import seed_group


async def _get_user(db_session: AsyncSession) -> User:
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    return result.scalar_one()


async def _seed(
    db_session: AsyncSession,
    user: User,
    account_type: str = "tg_user",
    title: str = "Ad #35",
) -> tuple[Ad, MessengerAccount, Schedule]:
    ad = Ad(user_id=user.id, title=title, text="text", images=[])
    account = MessengerAccount(
        user_id=user.id,
        type=account_type,
        credentials="creds",
        status="active",
    )
    db_session.add_all([ad, account])
    await db_session.commit()
    await db_session.refresh(ad)
    await db_session.refresh(account)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[1],
        days_of_week=[0],
        times_of_day=["09:00"],
        timezone="UTC",
        is_active=True,
        next_run_at=datetime(2030, 1, 1, 9, 0, tzinfo=timezone.utc),
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    return ad, account, schedule


async def _reload_schedule(db_session: AsyncSession, schedule_id: int) -> Schedule | None:
    db_session.expire_all()
    result = await db_session.execute(
        select(Schedule).where(Schedule.id == schedule_id)
    )
    return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_api_delete_account_preserves_and_pauses_schedule(
    client, db_session: AsyncSession, auth_headers: dict
):
    ad_resp = await client.post(
        "/api/ads", json={"title": "Ad for #35", "text": "text"}, headers=auth_headers
    )
    ad_id = ad_resp.json()["id"]

    account_resp = await client.post(
        "/api/accounts",
        json={"type": "tg_user", "credentials": "session-data"},
        headers=auth_headers,
    )
    account_id = account_resp.json()["id"]

    # РЕАЛЬНАЯ группа этого аккаунта: JSON-вход расписаний сводит `group_ids` к
    # группам владельца И выбранного аккаунта, и выдуманный идентификатор даёт
    # 404 (план 02-09, CR-02). Проверяемое здесь — судьба расписания при
    # удалении аккаунта — от состава групп не зависит.
    #
    # Посев прямой вставкой через ORM: прикладного входа создания группы нет
    # (GRP-08 снято, JSON-маршрут групп удалён — план 03-07).
    group_id = (
        await seed_group(
            db_session,
            account_id,
            group_external_id="-1001000000035",
            name="Группа для #35",
        )
    ).id

    sched_resp = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id],
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )
    assert sched_resp.status_code == 201
    schedule_id = sched_resp.json()["id"]
    assert sched_resp.json()["is_active"] is True

    delete_resp = await client.delete(
        f"/api/accounts/{account_id}", headers=auth_headers
    )
    assert delete_resp.status_code == 204

    list_resp = await client.get("/api/accounts", headers=auth_headers)
    assert list_resp.json() == []

    schedule = await _reload_schedule(db_session, schedule_id)
    assert schedule is not None, "расписание не должно удаляться вместе с аккаунтом"
    assert schedule.is_active is False
    assert schedule.next_run_at is None
    assert schedule.account_id is None


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ["tg_user", "wa", "max"])
async def test_delete_account_use_case_preserves_and_pauses_schedule(
    client, db_session: AsyncSession, auth_headers: dict, account_type: str
):
    user = await _get_user(db_session)
    _, account, schedule = await _seed(db_session, user, account_type=account_type)
    schedule_id = schedule.id

    deleted = await delete_account(db_session, user.id, account.id)
    assert deleted is True

    remaining = await db_session.execute(
        select(MessengerAccount).where(MessengerAccount.id == account.id)
    )
    assert remaining.scalar_one_or_none() is None

    reloaded = await _reload_schedule(db_session, schedule_id)
    assert reloaded is not None
    assert reloaded.is_active is False
    assert reloaded.next_run_at is None
    assert reloaded.account_id is None


@pytest.mark.asyncio
async def test_detach_does_not_touch_other_accounts_schedules(
    client, db_session: AsyncSession, auth_headers: dict
):
    user = await _get_user(db_session)
    _, account_a, schedule_a = await _seed(db_session, user, title="Ad A")
    _, account_b, schedule_b = await _seed(db_session, user, title="Ad B")
    schedule_a_id, schedule_b_id = schedule_a.id, schedule_b.id
    account_b_id = account_b.id

    await delete_account(db_session, user.id, account_a.id)

    detached = await _reload_schedule(db_session, schedule_a_id)
    assert detached is not None
    assert detached.account_id is None
    assert detached.is_active is False

    untouched = await _reload_schedule(db_session, schedule_b_id)
    assert untouched is not None
    assert untouched.account_id == account_b_id
    assert untouched.is_active is True
    assert untouched.next_run_at is not None


@pytest.mark.asyncio
async def test_detach_helper_returns_number_of_detached_schedules(
    client, db_session: AsyncSession, auth_headers: dict
):
    user = await _get_user(db_session)
    ad, account, _ = await _seed(db_session, user)

    extra = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[],
        days_of_week=[1],
        times_of_day=["10:00"],
        timezone="UTC",
        is_active=True,
        next_run_at=datetime(2030, 1, 2, 10, 0, tzinfo=timezone.utc),
    )
    db_session.add(extra)
    await db_session.commit()

    count = await detach_schedules_from_account(db_session, account.id)
    await db_session.commit()
    assert count == 2

    empty_account = MessengerAccount(
        user_id=user.id, type="wa", credentials="creds", status="active"
    )
    db_session.add(empty_account)
    await db_session.commit()
    await db_session.refresh(empty_account)

    assert await detach_schedules_from_account(db_session, empty_account.id) == 0


@pytest.mark.asyncio
async def test_detach_helper_does_not_commit(
    client, db_session: AsyncSession, auth_headers: dict
):
    """Хелпер не должен коммитить: транзакцией владеет вызывающая сторона."""
    user = await _get_user(db_session)
    _, account, schedule = await _seed(db_session, user)
    schedule_id = schedule.id
    account_id = account.id

    await detach_schedules_from_account(db_session, account_id)
    await db_session.rollback()

    reloaded = await _reload_schedule(db_session, schedule_id)
    assert reloaded is not None
    assert reloaded.account_id == account_id
    assert reloaded.is_active is True

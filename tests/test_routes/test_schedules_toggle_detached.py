"""issue #35: расписание без аккаунта нельзя возобновить.

Отвязанное расписание с is_active=True попало бы в collect_due_schedules,
упало бы в ветку «нет аккаунта» и бесконечно переносило бы next_run_at,
ничего не отправляя. Возобновление запрещено до привязки нового аккаунта.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule


async def _login(client: AsyncClient) -> None:
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )


async def _create_account(client: AsyncClient, auth_headers: dict) -> int:
    return (
        await client.post(
            "/api/accounts",
            json={"type": "tg_user", "credentials": "creds"},
            headers=auth_headers,
        )
    ).json()["id"]


async def _create_ad(client: AsyncClient, auth_headers: dict) -> int:
    return (
        await client.post(
            "/api/ads",
            json={"title": "Toggle Ad", "text": "text"},
            headers=auth_headers,
        )
    ).json()["id"]


async def _create_schedule(
    client: AsyncClient, auth_headers: dict, ad_id: int, account_id: int
) -> int:
    return (
        await client.post(
            "/api/schedules",
            json={
                "ad_id": ad_id,
                "account_id": account_id,
                "group_ids": [1],
                "days_of_week": [0, 1, 2, 3, 4, 5, 6],
                "times_of_day": ["09:00"],
            },
            headers=auth_headers,
        )
    ).json()["id"]


async def _setup_detached(client: AsyncClient, auth_headers: dict) -> int:
    ad_id = await _create_ad(client, auth_headers)
    account_id = await _create_account(client, auth_headers)
    schedule_id = await _create_schedule(client, auth_headers, ad_id, account_id)
    resp = await client.delete(f"/api/accounts/{account_id}", headers=auth_headers)
    assert resp.status_code == 204
    return schedule_id


async def _reload(db_session: AsyncSession, schedule_id: int) -> Schedule:
    db_session.expire_all()
    return (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()


@pytest.mark.asyncio
async def test_api_toggle_refuses_to_resume_detached_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    schedule_id = await _setup_detached(client, auth_headers)

    response = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )
    assert response.status_code == 400

    row = await _reload(db_session, schedule_id)
    assert row.is_active is False
    assert row.next_run_at is None


@pytest.mark.asyncio
async def test_page_toggle_refuses_to_resume_detached_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    schedule_id = await _setup_detached(client, auth_headers)
    await _login(client)

    response = await client.post(
        f"/schedules/{schedule_id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/schedules"

    row = await _reload(db_session, schedule_id)
    assert row.is_active is False
    assert row.next_run_at is None


@pytest.mark.asyncio
async def test_api_toggle_still_works_with_attached_account(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id = await _create_ad(client, auth_headers)
    account_id = await _create_account(client, auth_headers)
    schedule_id = await _create_schedule(client, auth_headers, ad_id, account_id)

    paused = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )
    assert paused.status_code == 200
    assert paused.json()["is_active"] is False
    assert paused.json()["next_run_at"] is None

    resumed = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )
    assert resumed.status_code == 200
    assert resumed.json()["is_active"] is True
    assert resumed.json()["next_run_at"] is not None


@pytest.mark.asyncio
async def test_page_toggle_still_works_with_attached_account(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id = await _create_ad(client, auth_headers)
    account_id = await _create_account(client, auth_headers)
    schedule_id = await _create_schedule(client, auth_headers, ad_id, account_id)
    await _login(client)

    paused = await client.post(
        f"/schedules/{schedule_id}/toggle", follow_redirects=False
    )
    assert paused.status_code == 302
    row = await _reload(db_session, schedule_id)
    assert row.is_active is False
    assert row.next_run_at is None

    resumed = await client.post(
        f"/schedules/{schedule_id}/toggle", follow_redirects=False
    )
    assert resumed.status_code == 302
    row = await _reload(db_session, schedule_id)
    assert row.is_active is True
    assert row.next_run_at is not None


@pytest.mark.asyncio
async def test_toggle_works_again_after_reattaching_account(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id = await _create_ad(client, auth_headers)
    schedule_id = await _setup_detached(client, auth_headers)
    await _login(client)

    new_account_id = await _create_account(client, auth_headers)

    edit = await client.post(
        f"/schedules/{schedule_id}/edit",
        data={
            "ad_id": str(ad_id),
            "account_id": str(new_account_id),
            "days_of_week": ["0", "1", "2", "3", "4", "5", "6"],
            "times_of_day": ["09:00"],
            "timezone": "UTC",
        },
        follow_redirects=False,
    )
    assert edit.status_code == 302

    row = await _reload(db_session, schedule_id)
    assert row.account_id == new_account_id

    response = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert response.json()["next_run_at"] is not None

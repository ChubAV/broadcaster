"""issue #35: расписание с удалённым аккаунтом остаётся видимым в UI и API.

Раньше список расписаний использовал INNER JOIN по messenger_accounts, поэтому
отвязанное расписание (account_id IS NULL) молча пропадало из выдачи.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule


async def _login(client: AsyncClient) -> None:
    """Ставит cookie access_token через page-роут."""
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )


async def _seed_detached_schedule(
    client: AsyncClient, auth_headers: dict, title: str = "Detached Ad"
) -> int:
    """Создаёт объявление, аккаунт и расписание, затем удаляет аккаунт."""
    ad_id = (
        await client.post(
            "/api/ads", json={"title": title, "text": "text"}, headers=auth_headers
        )
    ).json()["id"]

    account_id = (
        await client.post(
            "/api/accounts",
            json={"type": "tg_user", "credentials": "creds"},
            headers=auth_headers,
        )
    ).json()["id"]

    schedule_id = (
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

    resp = await client.delete(f"/api/accounts/{account_id}", headers=auth_headers)
    assert resp.status_code == 204
    return schedule_id


@pytest.mark.asyncio
async def test_schedules_list_page_shows_detached_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    await _seed_detached_schedule(client, auth_headers)
    await _login(client)

    response = await client.get("/schedules")
    assert response.status_code == 200
    assert "Detached Ad" in response.text
    assert "Пауза" in response.text


@pytest.mark.asyncio
async def test_schedules_partial_shows_detached_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    await _seed_detached_schedule(client, auth_headers)
    await _login(client)

    response = await client.get("/schedules/partial")
    assert response.status_code == 200
    assert "Detached Ad" in response.text

    cards = await client.get("/schedules/partial?layout=cards")
    assert cards.status_code == 200
    assert "Detached Ad" in cards.text


@pytest.mark.asyncio
async def test_schedules_edit_page_renders_for_detached_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    schedule_id = await _seed_detached_schedule(client, auth_headers)
    await _login(client)

    response = await client.get(f"/schedules/{schedule_id}/edit")
    assert response.status_code == 200
    html = response.text
    assert 'name="account_id"' in html
    # Ни один вариант аккаунта не может быть выбран: аккаунт удалён
    assert "selected" not in html.split('name="account_id"')[1].split("</select>")[0]


@pytest.mark.asyncio
async def test_api_list_schedules_returns_detached_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    schedule_id = await _seed_detached_schedule(client, auth_headers)

    response = await client.get("/api/schedules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == schedule_id
    assert data[0]["account_id"] is None
    assert data[0]["is_active"] is False


@pytest.mark.asyncio
async def test_detached_schedule_row_survives_in_db(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    schedule_id = await _seed_detached_schedule(client, auth_headers)

    db_session.expire_all()
    row = (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()
    assert row.account_id is None
    assert row.is_active is False
    assert row.next_run_at is None

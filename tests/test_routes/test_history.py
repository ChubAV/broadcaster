import pytest
from datetime import datetime, timezone, timedelta

from app.models.send_log import SendLog
from app.models.schedule import Schedule
from app.models.group import Group


async def setup_dependencies(client, auth_headers, db_session):
    """Create ad, account, group, and schedule for history tests."""
    ad_resp = await client.post("/api/ads", json={
        "title": "History Ad",
        "text": "Ad for history",
    }, headers=auth_headers)
    ad_id = ad_resp.json()["id"]

    account_resp = await client.post("/api/accounts", json={
        "type": "tg_bot",
        "credentials": "bot-token-hist",
    }, headers=auth_headers)
    account_id = account_resp.json()["id"]

    group_resp = await client.post("/api/groups", json={
        "account_id": account_id,
        "messenger_type": "tg_bot",
        "group_external_id": "ext-hist-1",
        "name": "History Group",
    }, headers=auth_headers)
    group_id = group_resp.json()["id"]

    schedule_resp = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": [group_id],
        "days_of_week": [0, 1, 2, 3, 4],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)
    schedule_id = schedule_resp.json()["id"]

    return ad_id, account_id, group_id, schedule_id


@pytest.mark.asyncio
async def test_list_history_empty(client, auth_headers):
    response = await client.get("/api/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_history_with_data(client, auth_headers, db_session):
    ad_id, account_id, group_id, schedule_id = await setup_dependencies(
        client, auth_headers, db_session
    )

    # Insert send logs directly into DB
    now = datetime.now(timezone.utc)
    log1 = SendLog(
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="sent",
        sent_at=now - timedelta(hours=2),
    )
    log2 = SendLog(
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="failed",
        error_message="Connection timeout",
        sent_at=now - timedelta(hours=1),
    )
    db_session.add_all([log1, log2])
    await db_session.commit()

    response = await client.get("/api/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Should be ordered by sent_at DESC (most recent first)
    assert data[0]["status"] == "failed"
    assert data[1]["status"] == "sent"


@pytest.mark.asyncio
async def test_list_history_pagination(client, auth_headers, db_session):
    ad_id, account_id, group_id, schedule_id = await setup_dependencies(
        client, auth_headers, db_session
    )

    now = datetime.now(timezone.utc)
    for i in range(5):
        log = SendLog(
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="sent",
            sent_at=now - timedelta(hours=5 - i),
        )
        db_session.add(log)
    await db_session.commit()

    # Get first 2
    response = await client.get("/api/history?skip=0&limit=2", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Get next 2
    response = await client.get("/api/history?skip=2&limit=2", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Get remaining
    response = await client.get("/api/history?skip=4&limit=2", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_stats_endpoint(client, auth_headers, db_session):
    ad_id, account_id, group_id, schedule_id = await setup_dependencies(
        client, auth_headers, db_session
    )

    now = datetime.now(timezone.utc)
    # Create some send logs within last 30 days
    logs = [
        SendLog(schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="sent", sent_at=now - timedelta(days=1)),
        SendLog(schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="sent", sent_at=now - timedelta(days=2)),
        SendLog(schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="failed", error_message="error",
                sent_at=now - timedelta(days=3)),
    ]
    db_session.add_all(logs)
    await db_session.commit()

    response = await client.get("/api/history/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_sent"] == 3
    assert data["success_count"] == 2
    assert data["fail_count"] == 1


@pytest.mark.asyncio
async def test_stats_endpoint_empty(client, auth_headers):
    response = await client.get("/api/history/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_sent"] == 0
    assert data["success_count"] == 0
    assert data["fail_count"] == 0


@pytest.mark.asyncio
async def test_unauthenticated_request(client):
    response = await client.get("/api/history")
    assert response.status_code == 401

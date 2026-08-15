import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from app.models.user import User
from app.models.send_log import SendLog
from app.models.schedule import Schedule
from app.models.group import Group
from tests.conftest import seed_group


async def setup_dependencies(client, auth_headers, db_session):
    """Create ad, account, group, and schedule for history tests."""
    ad_resp = await client.post("/api/ads", json={
        "title": "History Ad",
        "text": "Ad for history",
    }, headers=auth_headers)
    ad_id = ad_resp.json()["id"]

    account_resp = await client.post("/api/accounts", json={
        "type": "tg_user",
        "credentials": "bot-token-hist",
    }, headers=auth_headers)
    account_id = account_resp.json()["id"]

    group_id = (
        await seed_group(
            db_session, account_id, group_external_id="ext-hist-1", name="History Group"
        )
    ).id

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

    result = await db_session.execute(select(User))
    user = result.scalar_one()

    # Insert send logs directly into DB
    now = datetime.now(timezone.utc)
    log1 = SendLog(
        user_id=user.id,
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="ok",
        sent_at=now - timedelta(hours=2),
    )
    log2 = SendLog(
        user_id=user.id,
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="fail",
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
    assert data[0]["status"] == "fail"
    assert data[1]["status"] == "ok"


@pytest.mark.asyncio
async def test_list_history_pagination(client, auth_headers, db_session):
    ad_id, account_id, group_id, schedule_id = await setup_dependencies(
        client, auth_headers, db_session
    )

    result = await db_session.execute(select(User))
    user = result.scalar_one()

    now = datetime.now(timezone.utc)
    for i in range(5):
        log = SendLog(
            user_id=user.id,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="ok",
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

    result = await db_session.execute(select(User))
    user = result.scalar_one()

    now = datetime.now(timezone.utc)
    # Create some send logs within last 30 days
    logs = [
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="ok", sent_at=now - timedelta(days=1)),
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="ok", sent_at=now - timedelta(days=2)),
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="fail", error_message="error",
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
async def test_stats_counts_account_disconnected_as_failure(
    client, auth_headers, db_session
):
    """Отправка с отвалившимся аккаунтом — неуспешная, а не потерянная.

    Устаревший счёт по журналу знал два статуса из трёх и складывал в
    `fail_count` только `fail`: отправка со статусом `account_disconnected` не
    попадала ни в успешные, ни в неуспешные и молча исчезала из ответа. Здесь
    закреплено обратное: `fail_count` — это «не `ok`», поэтому сумма успешных и
    неуспешных обязана сходиться с общим числом.
    """
    ad_id, account_id, group_id, schedule_id = await setup_dependencies(
        client, auth_headers, db_session
    )

    result = await db_session.execute(select(User))
    user = result.scalar_one()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id,
                group_id=group_id, status="ok", sent_at=now - timedelta(days=1)),
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id,
                group_id=group_id, status="fail", error_message="timeout",
                sent_at=now - timedelta(days=2)),
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id,
                group_id=group_id, status="account_disconnected",
                error_message="session dropped",
                sent_at=now - timedelta(days=3)),
    ])
    await db_session.commit()

    response = await client.get("/api/history/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Форма ответа не изменилась: те же три имени полей.
    assert set(data) == {"total_sent", "success_count", "fail_count"}

    assert data["total_sent"] == 3
    assert data["success_count"] == 1
    # Отвалившийся аккаунт считается неуспешной отправкой наравне с `fail`.
    assert data["fail_count"] == 2
    # Ни одна запись не потерялась между двумя числами.
    assert data["success_count"] + data["fail_count"] == data["total_sent"]


@pytest.mark.asyncio
async def test_stats_counts_only_own_records(client, auth_headers, db_session):
    """Сводка отдаёт числа только по записям текущего пользователя."""
    ad_id, account_id, group_id, schedule_id = await setup_dependencies(
        client, auth_headers, db_session
    )

    result = await db_session.execute(select(User))
    user = result.scalar_one()

    stranger = User(
        email="stranger-stats@example.com", password_hash="x", name="Stranger"
    )
    db_session.add(stranger)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        SendLog(user_id=user.id, schedule_id=schedule_id, ad_id=ad_id,
                group_id=group_id, status="ok", sent_at=now - timedelta(days=1)),
        SendLog(user_id=stranger.id, schedule_id=schedule_id, ad_id=ad_id,
                group_id=group_id, status="fail", error_message="not mine",
                sent_at=now - timedelta(days=1)),
        SendLog(user_id=stranger.id, schedule_id=schedule_id, ad_id=ad_id,
                group_id=group_id, status="account_disconnected",
                sent_at=now - timedelta(days=2)),
    ])
    await db_session.commit()

    response = await client.get("/api/history/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_sent"] == 1
    assert data["success_count"] == 1
    assert data["fail_count"] == 0


@pytest.mark.asyncio
async def test_stats_unauthenticated_request(client):
    """Неавторизованный запрос к сводке по-прежнему отклоняется."""
    response = await client.get("/api/history/stats")
    assert response.status_code == 401


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

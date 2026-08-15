import pytest

from tests.conftest import seed_group


async def setup_ad_and_account(client, auth_headers, db_session):
    """Объявление, аккаунт и ТРИ РЕАЛЬНЫЕ группы этого аккаунта.

    Группы настоящие, а не выдуманные значения вида `[1, 2, 3]`: расписание,
    сохранённое с идентификатором группы, которой нет или которая чужая, — это
    межарендная дыра (02-REVIEW.md, CR-02), а тест на выдуманных значениях её
    закреплял бы. Ожидания тестов от этого не меняются: меняются только данные,
    на которых они выполняются.

    Группы сеются прямой вставкой через ORM: прикладного входа их создания в
    приложении нет (GRP-08 снято, JSON-маршрут групп удалён — план 03-07).
    """
    ad_resp = await client.post("/api/ads", json={
        "title": "Schedule Ad",
        "text": "Ad for scheduling",
    }, headers=auth_headers)
    ad_id = ad_resp.json()["id"]

    account_resp = await client.post("/api/accounts", json={
        "type": "tg_user",
        "credentials": "bot-token-sched",
    }, headers=auth_headers)
    account_id = account_resp.json()["id"]

    group_ids = []
    for index in range(3):
        group = await seed_group(
            db_session,
            account_id,
            group_external_id=f"-100100000000{index}",
            name=f"Группа {index + 1}",
        )
        group_ids.append(group.id)

    return ad_id, account_id, group_ids


@pytest.mark.asyncio
async def test_create_schedule(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    response = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids,
        "days_of_week": [0, 2, 4],
        "times_of_day": ["09:00", "18:00"],
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["ad_id"] == ad_id
    assert data["account_id"] == account_id
    assert data["group_ids"] == group_ids
    assert data["days_of_week"] == [0, 2, 4]
    assert data["times_of_day"] == ["09:00", "18:00"]
    assert data["is_active"] is True
    assert data["next_run_at"] is not None
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_schedules(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)
    await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[1:2],
        "days_of_week": [1],
        "times_of_day": ["10:00"],
    }, headers=auth_headers)

    response = await client.get("/api/schedules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_schedule(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    create_resp = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)
    schedule_id = create_resp.json()["id"]

    response = await client.put(f"/api/schedules/{schedule_id}", json={
        "group_ids": group_ids,
        "days_of_week": [0, 1, 2],
        "times_of_day": ["10:00", "15:00"],
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["group_ids"] == group_ids
    assert data["days_of_week"] == [0, 1, 2]
    assert data["times_of_day"] == ["10:00", "15:00"]
    assert data["next_run_at"] is not None


@pytest.mark.asyncio
async def test_delete_schedule(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    create_resp = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)
    schedule_id = create_resp.json()["id"]

    response = await client.delete(f"/api/schedules/{schedule_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    list_resp = await client.get("/api/schedules", headers=auth_headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_toggle_schedule(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    create_resp = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)
    schedule_id = create_resp.json()["id"]
    assert create_resp.json()["is_active"] is True

    # Toggle off
    response = await client.post(f"/api/schedules/{schedule_id}/toggle", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    # When deactivated, next_run_at can be None or unchanged (implementation choice)

    # Toggle back on — should recompute next_run_at
    response = await client.post(f"/api/schedules/{schedule_id}/toggle", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert response.json()["next_run_at"] is not None


@pytest.mark.asyncio
async def test_create_schedule_with_timezone(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    response = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0, 1, 2, 3, 4],
        "times_of_day": ["09:00"],
        "timezone": "Europe/Moscow",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["timezone"] == "Europe/Moscow"
    assert data["next_run_at"] is not None


@pytest.mark.asyncio
async def test_update_schedule_timezone(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    create_resp = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)
    schedule_id = create_resp.json()["id"]

    response = await client.put(f"/api/schedules/{schedule_id}", json={
        "timezone": "Asia/Vladivostok",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["timezone"] == "Asia/Vladivostok"


@pytest.mark.asyncio
async def test_create_schedule_invalid_timezone(client, auth_headers, db_session):
    ad_id, account_id, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    response = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
        "timezone": "Not/A/Timezone",
    }, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unauthenticated_request(client):
    response = await client.get("/api/schedules")
    assert response.status_code == 401


# --- CR-01 / D-20: владение аккаунтом на JSON-входе ----------------------------
#
# Владение объявлением здесь проверялось с самого начала, владение аккаунтом —
# нет. Асимметрия и есть находка: чужой `account_id` принимался, и рассылка
# уходила бы через чужую подключённую сессию мессенджера.


@pytest.mark.asyncio
async def test_create_schedule_rejects_foreign_account(
    client, auth_headers, db_session
):
    from sqlalchemy import select

    from app.models.messenger_account import MessengerAccount
    from app.models.schedule import Schedule
    from app.models.user import User

    ad_id, _, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    stranger = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)
    foreign_account = MessengerAccount(
        user_id=stranger.id, type="tg_user", credentials="creds"
    )
    db_session.add(foreign_account)
    await db_session.commit()
    await db_session.refresh(foreign_account)
    foreign_account_id = foreign_account.id

    response = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": foreign_account_id,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)

    assert response.status_code == 404
    db_session.expire_all()
    stored = (await db_session.execute(select(Schedule))).scalars().all()
    assert list(stored) == []


@pytest.mark.asyncio
async def test_create_schedule_rejects_nonexistent_account(client, auth_headers, db_session):
    ad_id, _, group_ids = await setup_ad_and_account(client, auth_headers, db_session)

    response = await client.post("/api/schedules", json={
        "ad_id": ad_id,
        "account_id": 999999,
        "group_ids": group_ids[:1],
        "days_of_week": [0],
        "times_of_day": ["09:00"],
    }, headers=auth_headers)

    assert response.status_code == 404

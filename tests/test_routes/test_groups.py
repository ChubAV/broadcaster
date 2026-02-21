import pytest


async def create_account(client, auth_headers):
    """Helper to create a messenger account for group tests."""
    resp = await client.post("/api/accounts", json={
        "type": "tg_user",
        "credentials": "bot-token-123",
    }, headers=auth_headers)
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_group(client, auth_headers):
    account_id = await create_account(client, auth_headers)

    response = await client.post("/api/groups", json={
        "account_id": account_id,
        "messenger_type": "tg_user",
        "group_external_id": "ext-group-1",
        "name": "Test Group",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Group"
    assert data["account_id"] == account_id
    assert data["messenger_type"] == "tg_user"
    assert data["group_external_id"] == "ext-group-1"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_groups(client, auth_headers):
    account_id = await create_account(client, auth_headers)

    await client.post("/api/groups", json={
        "account_id": account_id,
        "messenger_type": "tg_user",
        "group_external_id": "ext-1",
        "name": "Group 1",
    }, headers=auth_headers)
    await client.post("/api/groups", json={
        "account_id": account_id,
        "messenger_type": "tg_user",
        "group_external_id": "ext-2",
        "name": "Group 2",
    }, headers=auth_headers)

    response = await client.get("/api/groups", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Group 1"
    assert data[1]["name"] == "Group 2"


@pytest.mark.asyncio
async def test_list_groups_filter_by_account(client, auth_headers):
    account_id_1 = await create_account(client, auth_headers)
    # Create a second account
    resp2 = await client.post("/api/accounts", json={
        "type": "wa",
        "credentials": "wa-creds",
    }, headers=auth_headers)
    account_id_2 = resp2.json()["id"]

    await client.post("/api/groups", json={
        "account_id": account_id_1,
        "messenger_type": "tg_user",
        "group_external_id": "ext-a",
        "name": "TG Group",
    }, headers=auth_headers)
    await client.post("/api/groups", json={
        "account_id": account_id_2,
        "messenger_type": "wa",
        "group_external_id": "ext-b",
        "name": "WA Group",
    }, headers=auth_headers)

    # Filter by first account
    response = await client.get(f"/api/groups?account_id={account_id_1}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "TG Group"

    # Filter by second account
    response = await client.get(f"/api/groups?account_id={account_id_2}", headers=auth_headers)
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "WA Group"


@pytest.mark.asyncio
async def test_delete_group(client, auth_headers):
    account_id = await create_account(client, auth_headers)

    create_resp = await client.post("/api/groups", json={
        "account_id": account_id,
        "messenger_type": "tg_user",
        "group_external_id": "ext-del",
        "name": "Delete Me",
    }, headers=auth_headers)
    group_id = create_resp.json()["id"]

    response = await client.delete(f"/api/groups/{group_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    list_resp = await client.get("/api/groups", headers=auth_headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_toggle_group(client, auth_headers):
    account_id = await create_account(client, auth_headers)

    create_resp = await client.post("/api/groups", json={
        "account_id": account_id,
        "messenger_type": "tg_user",
        "group_external_id": "ext-toggle",
        "name": "Toggle Group",
    }, headers=auth_headers)
    group_id = create_resp.json()["id"]
    assert create_resp.json()["is_active"] is True

    # Toggle off
    response = await client.patch(f"/api/groups/{group_id}/toggle", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Toggle back on
    response = await client.patch(f"/api/groups/{group_id}/toggle", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_unauthenticated_request(client):
    response = await client.get("/api/groups")
    assert response.status_code == 401

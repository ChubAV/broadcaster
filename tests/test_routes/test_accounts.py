import pytest


@pytest.mark.asyncio
async def test_create_account(client, auth_headers):
    response = await client.post("/api/accounts", json={
        "type": "tg_bot",
        "credentials": "bot-token-123",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "tg_bot"
    assert data["status"] == "disconnected"
    assert "id" in data
    assert "created_at" in data
    # credentials must NOT be exposed
    assert "credentials" not in data
    assert "session_data" not in data


@pytest.mark.asyncio
async def test_list_accounts(client, auth_headers):
    await client.post("/api/accounts", json={
        "type": "tg_bot",
        "credentials": "bot-token-1",
    }, headers=auth_headers)
    await client.post("/api/accounts", json={
        "type": "wa",
        "credentials": "wa-creds-2",
    }, headers=auth_headers)

    response = await client.get("/api/accounts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["type"] == "tg_bot"
    assert data[1]["type"] == "wa"
    # credentials must NOT be exposed in list
    for account in data:
        assert "credentials" not in account
        assert "session_data" not in account


@pytest.mark.asyncio
async def test_delete_account(client, auth_headers):
    create_resp = await client.post("/api/accounts", json={
        "type": "tg_user",
        "credentials": "user-session-data",
    }, headers=auth_headers)
    account_id = create_resp.json()["id"]

    response = await client.delete(f"/api/accounts/{account_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    list_resp = await client.get("/api/accounts", headers=auth_headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_get_account_status(client, auth_headers):
    create_resp = await client.post("/api/accounts", json={
        "type": "tg_bot",
        "credentials": "bot-token-status",
    }, headers=auth_headers)
    account_id = create_resp.json()["id"]

    response = await client.get(f"/api/accounts/{account_id}/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == account_id
    assert data["status"] == "disconnected"


@pytest.mark.asyncio
async def test_unauthenticated_request(client):
    response = await client.get("/api/accounts")
    assert response.status_code == 401

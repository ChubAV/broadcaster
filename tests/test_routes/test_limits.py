import pytest


@pytest.mark.asyncio
async def test_create_ads_no_limit(client, auth_headers):
    """No limit on ads — creating many should succeed."""
    for i in range(5):
        resp = await client.post("/api/ads", headers=auth_headers, json={
            "title": f"Ad {i}", "text": "text"
        })
        assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_groups_no_limit(client, auth_headers):
    """No limit on groups — creating many should succeed."""
    resp = await client.post("/api/accounts", headers=auth_headers, json={
        "type": "tg_user", "credentials": "bot-token-123"
    })
    assert resp.status_code == 201
    account_id = resp.json()["id"]

    for i in range(7):
        resp = await client.post("/api/groups", headers=auth_headers, json={
            "account_id": account_id, "messenger_type": "telegram",
            "group_external_id": f"ext-{i}", "name": f"Group {i}"
        })
        assert resp.status_code == 201

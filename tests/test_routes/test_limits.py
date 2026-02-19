import pytest


@pytest.mark.asyncio
async def test_create_ad_over_limit(client, auth_headers):
    """Free plan allows 3 ads. Creating 4th should be rejected."""
    for i in range(3):
        resp = await client.post("/api/ads", headers=auth_headers, json={
            "title": f"Ad {i}", "text": "text"
        })
        assert resp.status_code == 201

    resp = await client.post("/api/ads", headers=auth_headers, json={
        "title": "Ad 4", "text": "text"
    })
    assert resp.status_code == 403
    assert "limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_group_over_limit(client, auth_headers):
    """Free plan allows 5 groups. Creating 6th should be rejected."""
    # Create an account first
    resp = await client.post("/api/accounts", headers=auth_headers, json={
        "type": "tg_bot", "credentials": "bot-token-123"
    })
    assert resp.status_code == 201
    account_id = resp.json()["id"]

    for i in range(5):
        resp = await client.post("/api/groups", headers=auth_headers, json={
            "account_id": account_id, "messenger_type": "telegram",
            "group_external_id": f"ext-{i}", "name": f"Group {i}"
        })
        assert resp.status_code == 201

    resp = await client.post("/api/groups", headers=auth_headers, json={
        "account_id": account_id, "messenger_type": "telegram",
        "group_external_id": "ext-6", "name": "Group 6"
    })
    assert resp.status_code == 403
    assert "limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_ad_within_limit(client, auth_headers):
    """Creating ads within limit should succeed."""
    for i in range(3):
        resp = await client.post("/api/ads", headers=auth_headers, json={
            "title": f"Ad {i}", "text": "text"
        })
        assert resp.status_code == 201

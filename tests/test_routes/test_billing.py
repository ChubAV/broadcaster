import pytest


@pytest.mark.asyncio
async def test_get_current_plan(client, auth_headers):
    response = await client.get("/api/billing/plan", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "free"
    assert "limits" in data
    assert "usage" in data


@pytest.mark.asyncio
async def test_list_plans(client, auth_headers):
    response = await client.get("/api/billing/plans", headers=auth_headers)
    assert response.status_code == 200
    assert "plans" in response.json()

import pytest


@pytest.mark.asyncio
async def test_get_balance(client, auth_headers):
    response = await client.get("/api/billing/balance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data


@pytest.mark.asyncio
async def test_list_packages(client, auth_headers):
    response = await client.get("/api/billing/packages", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "packages" in data
    assert len(data["packages"]) == 3


@pytest.mark.asyncio
async def test_get_transactions(client, auth_headers):
    response = await client.get("/api/billing/transactions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data

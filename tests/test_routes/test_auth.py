import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "strongpass123",
        "name": "Test User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@test.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/auth/register", json={
        "email": "dup@test.com", "password": "pass123", "name": "A",
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@test.com", "password": "pass123", "name": "B",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/auth/register", json={
        "email": "login@test.com", "password": "pass123", "name": "A",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@test.com", "password": "pass123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "wrong@test.com", "password": "pass123", "name": "A",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrong@test.com", "password": "wrongpass",
    })
    assert response.status_code == 401

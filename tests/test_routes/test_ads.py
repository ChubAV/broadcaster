import pytest


@pytest.mark.asyncio
async def test_create_ad(client, auth_headers):
    response = await client.post("/api/ads", json={
        "title": "Test Ad",
        "text": "This is a test advertisement",
        "images": ["img1.jpg", "img2.jpg"],
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Ad"
    assert data["text"] == "This is a test advertisement"
    assert data["images"] == ["img1.jpg", "img2.jpg"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_ad_default_images(client, auth_headers):
    response = await client.post("/api/ads", json={
        "title": "No Images Ad",
        "text": "Ad without images",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["images"] == []


@pytest.mark.asyncio
async def test_list_ads(client, auth_headers):
    # Create two ads
    await client.post("/api/ads", json={
        "title": "Ad 1", "text": "First ad",
    }, headers=auth_headers)
    await client.post("/api/ads", json={
        "title": "Ad 2", "text": "Second ad",
    }, headers=auth_headers)

    response = await client.get("/api/ads", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Ad 1"
    assert data[1]["title"] == "Ad 2"


@pytest.mark.asyncio
async def test_get_single_ad(client, auth_headers):
    create_resp = await client.post("/api/ads", json={
        "title": "Single Ad", "text": "Get me",
    }, headers=auth_headers)
    ad_id = create_resp.json()["id"]

    response = await client.get(f"/api/ads/{ad_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Ad"
    assert data["id"] == ad_id


@pytest.mark.asyncio
async def test_get_nonexistent_ad(client, auth_headers):
    response = await client.get("/api/ads/9999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_ad(client, auth_headers):
    create_resp = await client.post("/api/ads", json={
        "title": "Old Title", "text": "Old text",
    }, headers=auth_headers)
    ad_id = create_resp.json()["id"]

    response = await client.put(f"/api/ads/{ad_id}", json={
        "title": "New Title",
        "text": "New text",
        "is_active": False,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["text"] == "New text"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_ad(client, auth_headers):
    create_resp = await client.post("/api/ads", json={
        "title": "Delete Me", "text": "Bye",
    }, headers=auth_headers)
    ad_id = create_resp.json()["id"]

    response = await client.delete(f"/api/ads/{ad_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    get_resp = await client.get(f"/api/ads/{ad_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_request(client):
    response = await client.get("/api/ads")
    assert response.status_code == 401

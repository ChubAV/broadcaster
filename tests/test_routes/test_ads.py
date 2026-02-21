from urllib.parse import urlencode

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


@pytest.mark.asyncio
async def test_create_ad_with_multiple_image_fields(client, auth_headers):
    """Form sends multiple 'images' fields instead of newline-separated textarea."""
    # Login via cookie
    await client.post("/api/auth/register", json={
        "email": "imgform@test.com", "password": "testpass123", "name": "Img User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "imgform@test.com", "password": "testpass123",
    })
    token = resp.json()["access_token"]
    client.cookies.set("access_token", token)

    form_body = urlencode([
        ("title", "Multi Image Ad"),
        ("text", "Test text"),
        ("images", "1/img1.jpg"),
        ("images", "1/img2.jpg"),
    ])
    resp = await client.post("/ads/new",
        content=form_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    # Verify the ad was created with images
    resp = await client.get("/api/ads", headers={"Authorization": f"Bearer {token}"})
    ads = resp.json()
    assert len(ads) >= 1
    ad = [a for a in ads if a["title"] == "Multi Image Ad"][0]
    assert ad["images"] == ["1/img1.jpg", "1/img2.jpg"]


@pytest.mark.asyncio
async def test_update_ad_with_multiple_image_fields(client, auth_headers):
    """Form sends multiple 'images' fields on update instead of newline-separated textarea."""
    # Login via cookie
    await client.post("/api/auth/register", json={
        "email": "imgupdate@test.com", "password": "testpass123", "name": "Img Updater",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "imgupdate@test.com", "password": "testpass123",
    })
    token = resp.json()["access_token"]
    client.cookies.set("access_token", token)

    # Create ad via API
    create_resp = await client.post("/api/ads", json={
        "title": "Update Me", "text": "Old text", "images": ["old.jpg"],
    }, headers={"Authorization": f"Bearer {token}"})
    ad_id = create_resp.json()["id"]

    # Update via form with multiple image fields
    form_body = urlencode([
        ("title", "Updated Ad"),
        ("text", "New text"),
        ("images", "2/new1.jpg"),
        ("images", "2/new2.jpg"),
        ("images", "2/new3.jpg"),
        ("is_active", "on"),
    ])
    resp = await client.post(f"/ads/{ad_id}/edit",
        content=form_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    # Verify the ad was updated
    resp = await client.get(f"/api/ads/{ad_id}", headers={"Authorization": f"Bearer {token}"})
    ad = resp.json()
    assert ad["title"] == "Updated Ad"
    assert ad["images"] == ["2/new1.jpg", "2/new2.jpg", "2/new3.jpg"]

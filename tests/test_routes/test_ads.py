from urllib.parse import urlencode
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.ad import Ad
from app.models.user import User


def image_key(user_id: int, name: str = "photo.jpg") -> str:
    """Ключ вложения в форме, которую выдаёт `/api/uploads/image`.

    Источник формы — `app/routes/uploads.py`: `{user_id}/{uuid4().hex}_{имя}`.
    Ключи в тестах строятся этим помощником, а не пишутся от руки: правило
    владения проверяет форму ключа, и произвольная строка ему не удовлетворяет.
    """
    return f"{user_id}/{uuid4().hex}_{name}"


@pytest_asyncio.fixture
async def auth_user_id(db_session, auth_headers) -> int:
    """Идентификатор пользователя из `auth_headers` — префикс его ключей."""
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    return result.scalar_one().id


@pytest.mark.asyncio
async def test_create_ad(client, auth_headers, auth_user_id):
    images = [image_key(auth_user_id, "img1.jpg"), image_key(auth_user_id, "img2.jpg")]
    response = await client.post("/api/ads", json={
        "title": "Test Ad",
        "text": "This is a test advertisement",
        "images": images,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Ad"
    assert data["text"] == "This is a test advertisement"
    assert data["images"] == images
    # D-02: созданное объявление опубликовано; черновиком оно становится только
    # явным действием пользователя.
    assert data["status"] == "published"
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
        "status": "draft",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["text"] == "New text"
    assert data["status"] == "draft"


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
    reg = await client.post("/api/auth/register", json={
        "email": "imgform@test.com", "password": "testpass123", "name": "Img User",
    })
    user_id = reg.json()["id"]
    resp = await client.post("/api/auth/login", json={
        "email": "imgform@test.com", "password": "testpass123",
    })
    token = resp.json()["access_token"]
    client.cookies.set("access_token", token)

    keys = [image_key(user_id, "img1.jpg"), image_key(user_id, "img2.jpg")]
    form_body = urlencode([
        ("title", "Multi Image Ad"),
        ("text", "Test text"),
        ("images", keys[0]),
        ("images", keys[1]),
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
    assert ad["images"] == keys


@pytest.mark.asyncio
async def test_update_ad_with_multiple_image_fields(client, auth_headers):
    """Form sends multiple 'images' fields on update instead of newline-separated textarea."""
    # Login via cookie
    reg = await client.post("/api/auth/register", json={
        "email": "imgupdate@test.com", "password": "testpass123", "name": "Img Updater",
    })
    user_id = reg.json()["id"]
    resp = await client.post("/api/auth/login", json={
        "email": "imgupdate@test.com", "password": "testpass123",
    })
    token = resp.json()["access_token"]
    client.cookies.set("access_token", token)

    # Create ad via API
    create_resp = await client.post("/api/ads", json={
        "title": "Update Me", "text": "Old text",
        "images": [image_key(user_id, "old.jpg")],
    }, headers={"Authorization": f"Bearer {token}"})
    ad_id = create_resp.json()["id"]

    # Update via form with multiple image fields
    new_keys = [image_key(user_id, f"new{i}.jpg") for i in (1, 2, 3)]
    form_body = urlencode([
        ("title", "Updated Ad"),
        ("text", "New text"),
        *[("images", key) for key in new_keys],
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
    assert ad["images"] == new_keys


# --- WR-01 / T-10-04: владение ключом вложения на JSON-входе -------------------
#
# До этого плана JSON-API принимал в `images` произвольные строки: чужой префикс
# того же хранилища и внешний URL сохранялись без вопросов. Тест, стоявший здесь
# раньше, закреплял этот приём как поведение — то есть фиксировал уязвимость.


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hostile",
    [
        pytest.param("foreign", id="foreign-prefix"),
        pytest.param("http://evil.example.com/steal.png", id="external-url"),
        pytest.param("old.jpg", id="no-prefix"),
        pytest.param("2/new1.jpg", id="malformed-token"),
    ],
)
async def test_create_ad_rejects_key_outside_owner_prefix(
    hostile, client, auth_headers, auth_user_id, db_session
):
    value = image_key(auth_user_id + 1000) if hostile == "foreign" else hostile

    response = await client.post("/api/ads", json={
        "title": "Чужое вложение", "text": "Текст", "images": [value],
    }, headers=auth_headers)

    assert response.status_code == 400
    stored = (await db_session.execute(select(Ad))).scalars().all()
    assert stored == []


@pytest.mark.asyncio
async def test_update_ad_rejects_foreign_key_and_leaves_ad_untouched(
    client, auth_headers, auth_user_id, db_session
):
    original = [image_key(auth_user_id, "original.jpg")]
    create_resp = await client.post("/api/ads", json={
        "title": "Update Me", "text": "Old text", "images": original,
    }, headers=auth_headers)
    ad_id = create_resp.json()["id"]

    response = await client.put(f"/api/ads/{ad_id}", json={
        "title": "Подменённое", "images": [image_key(auth_user_id + 1000)],
    }, headers=auth_headers)

    assert response.status_code == 400
    check = await client.get(f"/api/ads/{ad_id}", headers=auth_headers)
    assert check.json()["images"] == original
    assert check.json()["title"] == "Update Me"


@pytest.mark.asyncio
async def test_update_ad_without_images_field_keeps_stored_images(
    client, auth_headers, auth_user_id
):
    """Отсутствие поля `images` — не то же самое, что пустой список.

    `exclude_unset` уже несёт это различие; проверка владения не должна его
    стирать, иначе правка одного заголовка обнуляла бы вложения.
    """
    original = [image_key(auth_user_id, "original.jpg")]
    create_resp = await client.post("/api/ads", json={
        "title": "Keep Images", "text": "Text", "images": original,
    }, headers=auth_headers)
    ad_id = create_resp.json()["id"]

    response = await client.put(f"/api/ads/{ad_id}", json={
        "title": "Только заголовок",
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["images"] == original


@pytest.mark.asyncio
async def test_create_ad_rejects_more_attachments_than_limit(
    client, auth_headers, auth_user_id, test_settings
):
    """D-13: лимит вложений — серверное правило и на JSON-входе."""
    limit = test_settings.max_images_per_ad
    response = await client.post("/api/ads", json={
        "title": "Слишком много", "text": "Текст",
        "images": [image_key(auth_user_id, f"p{i}.jpg") for i in range(limit + 1)],
    }, headers=auth_headers)

    assert response.status_code == 400
    assert str(limit) in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_ad_rejects_more_attachments_than_limit(
    client, auth_headers, auth_user_id, test_settings
):
    limit = test_settings.max_images_per_ad
    create_resp = await client.post("/api/ads", json={
        "title": "Update Me", "text": "Text",
    }, headers=auth_headers)
    ad_id = create_resp.json()["id"]

    response = await client.put(f"/api/ads/{ad_id}", json={
        "images": [image_key(auth_user_id, f"p{i}.jpg") for i in range(limit + 1)],
    }, headers=auth_headers)

    assert response.status_code == 400

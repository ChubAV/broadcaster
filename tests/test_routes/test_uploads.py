import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app


@pytest_asyncio.fixture
async def upload_settings(tmp_path):
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        s3_endpoint_url="https://s3.example.com",
        s3_access_key="AKID",
        s3_secret_key="SECRET",
        s3_bucket_name="test-bucket",
        s3_public_url="https://cdn.example.com/test-bucket",
    )


@pytest_asyncio.fixture
async def upload_client(db_session, upload_settings):
    app = create_app(settings=upload_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: upload_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def upload_auth_headers(upload_client):
    """Register a user and return auth headers for the upload client."""
    await upload_client.post("/api/auth/register", json={
        "email": "uploader@test.com",
        "password": "testpass123",
        "name": "Upload User",
    })
    resp = await upload_client.post("/api/auth/login", json={
        "email": "uploader@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_png_bytes():
    """Create a minimal valid 1x1 PNG image in bytes."""
    import struct
    import zlib

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)
    raw_data = b"\x00\x00\x00\x00"  # filter byte + 1 pixel RGB
    idat = chunk(b"IDAT", zlib.compress(raw_data))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_valid_image(mock_s3, upload_client, upload_auth_headers):
    mock_s3.return_value = "1/abc_test_image.png"
    png_bytes = make_png_bytes()

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("test_image.png", png_bytes, "image/png")},
        headers=upload_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "test_image.png" in data["path"]

    # Verify S3 was called
    mock_s3.assert_called_once()
    call_kwargs = mock_s3.call_args.kwargs
    assert call_kwargs["content"] == png_bytes
    assert call_kwargs["content_type"] == "image/png"
    assert call_kwargs["bucket"] == "test-bucket"


@pytest.mark.asyncio
async def test_upload_non_image_file(upload_client, upload_auth_headers):
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("document.txt", b"hello world", "text/plain")},
        headers=upload_auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_unauthenticated(upload_client):
    png_bytes = make_png_bytes()
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("test.png", png_bytes, "image/png")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_image_with_cookie_auth(mock_s3, upload_client):
    """Upload should work with cookie-based auth (used by web UI)."""
    mock_s3.return_value = "1/abc_cookie_image.png"
    await upload_client.post("/api/auth/register", json={
        "email": "cookie@test.com",
        "password": "testpass123",
        "name": "Cookie User",
    })
    resp = await upload_client.post("/api/auth/login", json={
        "email": "cookie@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    upload_client.cookies.set("access_token", token)

    png_bytes = make_png_bytes()
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("cookie_image.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "cookie_image.png" in data["path"]

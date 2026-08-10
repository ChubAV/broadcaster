import re

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.routes.uploads import safe_filename


@pytest_asyncio.fixture
async def upload_settings():
    return Settings(
        _env_file=None,
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


# --- CR-01: нормализация клиентского имени файла ------------------------------
#
# Клиентское имя файла в составном запросе полностью подконтрольно отправителю и
# участвует в построении ключа объекта хранилища. Без нормализации сегменты пути
# в имени выводят ключ за префикс пользователя, то есть в чужую область того же
# хранилища. Функция проверяется напрямую, без HTTP: у неё определённые вход и
# выход, и классы входов проверяются каждый отдельно.

SAFE_FILENAME_CHARS = re.compile(r"^[A-Za-z0-9._-]+$")


def test_safe_filename_keeps_plain_name():
    assert safe_filename("test_image.png") == "test_image.png"
    assert safe_filename("photo-01.JPEG") == "photo-01.JPEG"


def test_safe_filename_strips_path_components():
    result = safe_filename("../../etc/passwd.png")

    assert "/" not in result
    assert "\\" not in result
    assert result == "passwd.png"
    assert safe_filename("..\\..\\windows\\evil.png") == "evil.png"
    assert "/" not in safe_filename("/absolute/path/img.png")


def test_safe_filename_drops_quotes_and_spaces():
    result = safe_filename('x" onerror="alert(1)<img>.png')

    assert SAFE_FILENAME_CHARS.match(result), result
    assert '"' not in result
    assert " " not in result
    assert "<" not in result
    assert ">" not in result


def test_safe_filename_falls_back_on_empty():
    assert safe_filename("") != ""
    assert safe_filename(None) != ""
    # Имя, от которого после нормализации не остаётся ни одного звена пути.
    assert safe_filename("../") != ""


def test_safe_filename_truncates():
    result = safe_filename("a" * 300 + ".png")

    assert len(result) <= 100
    assert SAFE_FILENAME_CHARS.match(result), result


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_key_stays_inside_user_prefix(
    mock_s3, upload_client, upload_auth_headers
):
    """Ключ объекта не выходит за префикс пользователя ни при каком имени файла."""
    png_bytes = make_png_bytes()
    hostile = '../../evil x" onerror="alert(1)>.png'

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": (hostile, png_bytes, "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    key = response.json()["path"]
    assert re.fullmatch(r"\d+/[0-9a-f]{32}_[A-Za-z0-9._-]+", key), key
    # Ключ, ушедший в хранилище, — тот же самый, что вернулся клиенту.
    assert mock_s3.call_args.kwargs["key"] == key


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

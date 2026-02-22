# S3 Image Storage Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace local filesystem image storage with S3-compatible object storage.

**Architecture:** Upload route writes to S3 via `aiobotocore` instead of local disk. DB continues storing relative keys (`user_id/filename`). A helper `get_image_url(key)` builds public URLs dynamically. Templates and messengers use full S3 URLs. WhatsApp bridge downloads images from URL instead of reading local files.

**Tech Stack:** `aiobotocore` (async S3 client), existing FastAPI/Jinja2/Celery stack.

---

### Task 1: Add `aiobotocore` dependency

**Files:**
- Modify: `pyproject.toml:7-26`

**Step 1: Add aiobotocore to dependencies**

In `pyproject.toml`, add `"aiobotocore>=2.21.0"` to the `dependencies` list (after `"aiofiles>=25.1.0"`):

```toml
dependencies = [
    "aiobotocore>=2.21.0",
    "aiofiles>=25.1.0",
    ...
]
```

**Step 2: Sync environment**

Run: `uv sync`
Expected: resolves and installs aiobotocore + botocore + aiohttp deps

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add aiobotocore dependency for S3 storage"
```

---

### Task 2: Add S3 settings to config

**Files:**
- Modify: `app/config.py:6-32`
- Test: `tests/test_config_s3.py` (new)

**Step 1: Write the failing test**

Create `tests/test_config_s3.py`:

```python
from app.config import Settings


def test_s3_settings_defaults():
    s = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test",
    )
    assert s.s3_endpoint_url == ""
    assert s.s3_access_key == ""
    assert s.s3_secret_key == ""
    assert s.s3_bucket_name == "broadcaster"
    assert s.s3_region == ""
    assert s.s3_public_url == ""


def test_s3_settings_custom():
    s = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test",
        s3_endpoint_url="https://s3.example.com",
        s3_access_key="AKID",
        s3_secret_key="SECRET",
        s3_bucket_name="my-bucket",
        s3_region="us-east-1",
        s3_public_url="https://cdn.example.com/my-bucket",
    )
    assert s.s3_endpoint_url == "https://s3.example.com"
    assert s.s3_bucket_name == "my-bucket"
    assert s.s3_public_url == "https://cdn.example.com/my-bucket"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config_s3.py -v`
Expected: FAIL — `Settings` has no field `s3_endpoint_url`

**Step 3: Write implementation**

In `app/config.py`, add these fields to `Settings` class after the "File uploads" section:

```python
    # S3 storage
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "broadcaster"
    s3_region: str = ""
    s3_public_url: str = ""  # public base URL for serving images
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config_s3.py -v`
Expected: PASS

**Step 5: Run all tests to check nothing broke**

Run: `uv run pytest tests/ -v`
Expected: all tests pass

**Step 6: Commit**

```bash
git add app/config.py tests/test_config_s3.py
git commit -m "feat: add S3 configuration settings"
```

---

### Task 3: Create S3 service

**Files:**
- Create: `app/services/s3.py`
- Test: `tests/test_services/test_s3.py` (new)

**Step 1: Write the failing tests**

Create `tests/test_services/test_s3.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.s3 import upload_file_to_s3, get_image_url


def test_get_image_url():
    """get_image_url builds URL from s3_public_url + key."""
    url = get_image_url("1/abc123_photo.jpg", "https://cdn.example.com/bucket")
    assert url == "https://cdn.example.com/bucket/1/abc123_photo.jpg"


def test_get_image_url_strips_trailing_slash():
    url = get_image_url("1/photo.jpg", "https://cdn.example.com/bucket/")
    assert url == "https://cdn.example.com/bucket/1/photo.jpg"


def test_get_image_url_empty_key():
    url = get_image_url("", "https://cdn.example.com/bucket")
    assert url == ""


@pytest.mark.asyncio
async def test_upload_file_to_s3():
    """upload_file_to_s3 calls S3 put_object with correct params."""
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock()

    mock_session = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session.create_client.return_value = mock_ctx

    with patch("app.services.s3.AioSession", return_value=mock_session):
        key = await upload_file_to_s3(
            content=b"image-bytes",
            key="1/photo.jpg",
            content_type="image/png",
            endpoint_url="https://s3.example.com",
            access_key="AKID",
            secret_key="SECRET",
            bucket="my-bucket",
            region="us-east-1",
        )

    assert key == "1/photo.jpg"
    mock_client.put_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="1/photo.jpg",
        Body=b"image-bytes",
        ContentType="image/png",
    )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_services/test_s3.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.s3'`

**Step 3: Write implementation**

Create `app/services/s3.py`:

```python
from aiobotocore.session import AioSession


def get_image_url(key: str, s3_public_url: str) -> str:
    """Build a public URL for an S3 object key."""
    if not key:
        return ""
    base = s3_public_url.rstrip("/")
    return f"{base}/{key}"


async def upload_file_to_s3(
    content: bytes,
    key: str,
    content_type: str,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    region: str = "",
) -> str:
    """Upload file to S3 and return the object key."""
    session = AioSession()
    client_kwargs = {
        "service_name": "s3",
        "endpoint_url": endpoint_url,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if region:
        client_kwargs["region_name"] = region

    async with session.create_client(**client_kwargs) as client:
        await client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    return key
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_services/test_s3.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/s3.py tests/test_services/test_s3.py
git commit -m "feat: add S3 service with upload and URL helper"
```

---

### Task 4: Rewrite upload route to use S3

**Files:**
- Modify: `app/routes/uploads.py` (full rewrite)
- Modify: `tests/test_routes/test_uploads.py` (rewrite tests for S3)

**Step 1: Write the failing tests**

Rewrite `tests/test_routes/test_uploads.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_routes/test_uploads.py -v`
Expected: FAIL — upload route still writes to disk, no `upload_file_to_s3` import

**Step 3: Rewrite the upload route**

Replace `app/routes/uploads.py` entirely:

```python
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.config import Settings
from app.dependencies import get_current_user_id, get_settings
from app.services.s3 import upload_file_to_s3

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/image")
async def upload_image(
    file: UploadFile,
    user_id: int = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    # Validate file is an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read file content and validate size
    content = await file.read()
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.max_image_size_mb}MB limit",
        )

    # Generate unique key
    filename = f"{uuid4().hex}_{file.filename}"
    key = f"{user_id}/{filename}"

    # Upload to S3
    await upload_file_to_s3(
        content=content,
        key=key,
        content_type=file.content_type,
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket_name,
        region=settings.s3_region,
    )

    return {"path": key}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_routes/test_uploads.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/uploads.py tests/test_routes/test_uploads.py
git commit -m "feat: rewrite upload route to use S3 instead of local disk"
```

---

### Task 5: Remove StaticFiles mount and add Jinja2 `get_image_url` global

**Files:**
- Modify: `app/main.py:64-68` (remove StaticFiles mount)
- Modify: `app/pages/common.py:11-12` (add get_image_url to Jinja2 globals)

**Step 1: Remove StaticFiles mount from main.py**

In `app/main.py`, remove these lines (64-68):

```python
    # Serve uploaded files
    upload_dir = settings.upload_dir if settings else "uploads"
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")
```

Also remove unused imports: `Path` from `pathlib` and `StaticFiles` from `fastapi.staticfiles`.

The final `create_app` function should end with:

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0", lifespan=lifespan)
    app.include_router(auth_router)
    app.include_router(ads_router)
    app.include_router(uploads_router)
    app.include_router(accounts_router)
    app.include_router(groups_router)
    app.include_router(schedules_router)
    app.include_router(history_router)
    app.include_router(billing_router)
    app.include_router(pages_router)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: FastAPIRequest, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: FastAPIRequest, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(BillingLimitError)
    async def billing_limit_handler(request: FastAPIRequest, exc: BillingLimitError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(MessengerConnectionError)
    async def messenger_error_handler(request: FastAPIRequest, exc: MessengerConnectionError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app
```

**Step 2: Add `get_image_url` as Jinja2 global**

In `app/pages/common.py`, add the import and register the global function:

```python
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.user import User
from app.services.auth_service import decode_access_token
from app.services.s3 import get_image_url

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

# Register get_image_url as Jinja2 global so templates can use {{ get_image_url(key) }}
_settings = get_settings()
templates.env.globals["get_image_url"] = lambda key: get_image_url(key, _settings.s3_public_url)


async def get_user_from_cookie(
    request: Request, db: AsyncSession, settings: Settings
) -> User | None:
    """Read JWT from httpOnly cookie and return the User, or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token, settings.secret_key)
    if not payload:
        return None
    user = await db.get(User, payload["sub"])
    return user
```

**Step 3: Run all tests to verify nothing broke**

Run: `uv run pytest tests/ -v`
Expected: all pass (the old `test_uploaded_image_is_served` was already removed in Task 4)

**Step 4: Commit**

```bash
git add app/main.py app/pages/common.py
git commit -m "feat: remove StaticFiles mount, add get_image_url Jinja2 global"
```

---

### Task 6: Update template to use S3 URLs

**Files:**
- Modify: `app/templates/ads/form.html:168`

**Step 1: Update image src in form.html**

In `app/templates/ads/form.html`, line 168, change:

```javascript
img.src = '/uploads/' + path;
```

to:

```javascript
img.src = '{{ get_image_url("") }}' + path;
```

This will output the S3 public URL base, and the JS will append the key.

**Step 2: Verify by reading the template**

Read the file to confirm the change is correct.

**Step 3: Commit**

```bash
git add app/templates/ads/form.html
git commit -m "feat: update ad form template to use S3 image URLs"
```

---

### Task 7: Update worker to pass S3 URLs to messengers

**Files:**
- Modify: `app/worker/tasks.py:113-117`
- Modify: `tests/test_worker/test_tasks.py`

**Step 1: Write the updated test**

In `tests/test_worker/test_tasks.py`, update `test_send_ad_success` — the worker should now pass S3 public URLs instead of local absolute paths:

Update `mock_settings` in all relevant tests to include S3 fields:

```python
    mock_settings = AsyncMock()
    mock_settings.s3_public_url = "https://cdn.example.com/bucket"
```

Update the assertion in `test_send_ad_success`:

```python
    # Verify S3 URLs were passed to messenger
    call_kwargs = mock_messenger.send_message.call_args
    sent_images = call_kwargs.kwargs["images"]
    assert len(sent_images) == 1
    assert sent_images[0] == "https://cdn.example.com/bucket/img.jpg"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_worker/test_tasks.py::test_send_ad_success -v`
Expected: FAIL — worker still builds local paths

**Step 3: Update worker code**

In `app/worker/tasks.py`, replace lines 113-117:

```python
    # Resolve image paths relative to upload_dir
    images = None
    if ad.images:
        upload_dir = Path(get_settings().upload_dir).resolve()
        images = [str(upload_dir / img) for img in ad.images]
```

with:

```python
    # Build S3 URLs for images
    images = None
    if ad.images:
        from app.services.s3 import get_image_url
        s3_public_url = get_settings().s3_public_url
        images = [get_image_url(img, s3_public_url) for img in ad.images]
```

Also remove unused `Path` import from the top of the file (line 3: `from pathlib import Path`).

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_worker/test_tasks.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/worker/tasks.py tests/test_worker/test_tasks.py
git commit -m "feat: worker sends S3 URLs to messengers instead of local paths"
```

---

### Task 8: Update WhatsApp bridge to handle URLs

**Files:**
- Modify: `wa_bridge/index.js:264-315` (send endpoint)
- Modify: `wa_bridge/package.json` (add `axios` dependency)

**Step 1: Add axios dependency**

In `wa_bridge/package.json`, add `"axios": "^1.7.0"` to dependencies:

```json
  "dependencies": {
    "axios": "^1.7.0",
    "express": "^4.18.0",
    "whatsapp-web.js": "^1.25.0",
    "qrcode": "^1.5.0",
    "multer": "^1.4.5-lts.1"
  }
```

**Step 2: Update send endpoint in index.js**

At the top of `wa_bridge/index.js`, add axios import (after line 5):

```javascript
const axios = require('axios');
```

Replace the send endpoint's image handling section. Change the key portion — instead of `image_paths` with `fs.existsSync` and `MessageMedia.fromFilePath`, accept `image_urls` (URLs) alongside legacy `image_paths`:

Replace the send handler (lines 264-327) with:

```javascript
// POST /api/sessions/:id/send - Send message (auto-loads session if needed)
app.post('/api/sessions/:id/send', async (req, res) => {
    const sessionId = req.params.id;

    const { group_id, text, image_paths, image_urls } = req.body;
    // Support both URL-based (S3) and legacy local paths
    const images = image_urls || image_paths || [];
    const isUrlMode = !!image_urls;
    if (!group_id || (!text && images.length === 0)) {
        return res.status(400).json({ error: 'group_id and text or images are required' });
    }

    // Auto-load session on demand
    const state = await ensureSession(sessionId);
    if (!state || !state.isConnected) {
        return res.status(503).json({ error: 'WhatsApp session not available' });
    }

    try {
        const caption = text || '';

        if (images.length > 0) {
            // Load media from URLs or local paths
            const mediaItems = [];
            for (const img of images) {
                if (isUrlMode || img.startsWith('http://') || img.startsWith('https://')) {
                    const response = await axios.get(img, { responseType: 'arraybuffer' });
                    const mime = response.headers['content-type'] || 'image/jpeg';
                    const base64 = Buffer.from(response.data).toString('base64');
                    mediaItems.push(new MessageMedia(mime, base64));
                } else if (fs.existsSync(img)) {
                    mediaItems.push(MessageMedia.fromFilePath(img));
                }
            }

            console.log(`[${sessionId}] Sending ${mediaItems.length} image(s) to group_id=${group_id}, text="${caption.substring(0, 50)}"`);

            if (mediaItems.length === 0) {
                if (caption) {
                    const result = await state.client.sendMessage(group_id, caption);
                    console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
                }
            } else if (mediaItems.length === 1) {
                const opts = caption ? { caption } : {};
                const result = await state.client.sendMessage(group_id, mediaItems[0], opts);
                console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
            } else {
                const sendPromises = mediaItems.map((media) => {
                    return state.client.sendMessage(group_id, media);
                });
                const results = await Promise.all(sendPromises);
                results.forEach((result, i) => {
                    console.log(`[${sessionId}] sendMessage[${i}] result: id=${result?.id?._serialized}, ack=${result?.ack}`);
                });
                if (caption) {
                    await state.client.sendMessage(group_id, caption);
                }
            }
        } else {
            console.log(`[${sessionId}] Sending text to group_id=${group_id}, text="${caption.substring(0, 50)}"`);
            const result = await state.client.sendMessage(group_id, caption);
            console.log(`[${sessionId}] sendMessage result: id=${result?.id?._serialized}, ack=${result?.ack}`);
        }

        res.json({ ok: true });
    } catch (error) {
        console.error(`[${sessionId}] Send error: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});
```

**Step 3: Update WhatsApp Python adapter to send URLs**

In `app/messengers/whatsapp.py`, change the payload key from `image_paths` to `image_urls` (line 20):

```python
            if images:
                payload = {
                    "group_id": group_id,
                    "text": text,
                    "image_urls": images,
                }
```

**Step 4: Install axios in wa_bridge**

Run: `cd wa_bridge && npm install`

**Step 5: Commit**

```bash
git add wa_bridge/index.js wa_bridge/package.json wa_bridge/package-lock.json app/messengers/whatsapp.py
git commit -m "feat: WhatsApp bridge downloads images from S3 URLs"
```

---

### Task 9: Clean up Docker volumes

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.dev.yml`

**Step 1: Remove uploads volume from docker-compose.yml**

In `docker-compose.yml`:
- Remove `- uploads:/app/uploads` from `web` service (line 11)
- Remove `- uploads:/app/uploads` from `celery-worker` service (line 60)
- Remove `- uploads:/app/uploads` from `wa-bridge` service (line 84)
- Remove `uploads:` from the `volumes:` section (line 88)

**Step 2: Remove uploads volume from docker-compose.dev.yml**

In `docker-compose.dev.yml`:
- Remove `- uploads:/app/uploads` from `web` service (line 6)
- Remove `- uploads:/app/uploads` from `celery-worker` service (line 14)
- Remove `- uploads:/app/uploads` from `wa-bridge` service (line 21)

**Step 3: Commit**

```bash
git add docker-compose.yml docker-compose.dev.yml
git commit -m "feat: remove uploads volume from Docker (now using S3)"
```

---

### Task 10: Clean up unused code and remove `upload_dir` setting

**Files:**
- Modify: `app/config.py` (remove `upload_dir` field)
- Modify: `pyproject.toml` (remove `aiofiles` dependency — no longer writing to disk)

**Step 1: Remove `upload_dir` from Settings**

In `app/config.py`, remove:

```python
    upload_dir: str = "uploads"
```

Keep `max_image_size_mb` and `max_images_per_ad` — they're still used.

**Step 2: Remove `aiofiles` from dependencies**

In `pyproject.toml`, remove `"aiofiles>=25.1.0"` from dependencies (it's no longer used).

**Step 3: Sync environment**

Run: `uv sync`

**Step 4: Update test fixtures that reference upload_dir**

In `tests/test_routes/test_uploads.py`, remove `tmp_path` from `upload_settings` fixture (no longer needed):

```python
@pytest_asyncio.fixture
async def upload_settings():
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
```

In `tests/test_worker/test_tasks.py`, remove `mock_settings.upload_dir = "uploads"` from all tests (already removed in Task 7).

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: all pass

**Step 6: Commit**

```bash
git add app/config.py pyproject.toml uv.lock tests/
git commit -m "chore: remove upload_dir setting and aiofiles dependency"
```

---

### Task 11: Final verification

**Step 1: Run full test suite with coverage**

Run: `uv run pytest tests/ --cov=app --cov-report=term-missing -v`
Expected: all tests pass, S3 code covered

**Step 2: Verify Docker build works**

Run: `docker compose -f docker-compose.yml config`
Expected: valid config without uploads volume

**Step 3: Update .env.example with S3 vars**

Add to `.env.example` (if it exists):

```
# S3 Storage
S3_ENDPOINT_URL=https://s3.your-provider.com
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=broadcaster
S3_REGION=
S3_PUBLIC_URL=https://s3.your-provider.com/broadcaster
```

**Step 4: Commit**

```bash
git add .env.example
git commit -m "docs: add S3 environment variables to .env.example"
```

# Image Upload UI Improvement Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the manual textarea image path input with a drag-and-drop upload zone with previews in the ad form.

**Architecture:** Add cookie auth fallback to upload endpoint so JS can call it from the web UI. Mount StaticFiles to serve uploaded images for previews. Rewrite the ad form template with a drag-and-drop zone that uploads files immediately via fetch and shows thumbnails. Update form handlers to accept multiple `images` values via getlist instead of splitlines.

**Tech Stack:** FastAPI StaticFiles, vanilla JS (no frameworks), Tailwind CSS (already in use), existing `/api/uploads/image` endpoint.

---

### Task 1: Add cookie auth fallback to upload endpoint

The upload API uses `get_current_user_id` which only accepts Bearer tokens. The web UI stores auth in an httpOnly cookie called `access_token`. We need the upload endpoint to work when called from the browser via fetch (which sends cookies automatically).

**Files:**
- Modify: `app/dependencies.py:29-38`
- Test: `tests/test_routes/test_uploads.py`

**Step 1: Write the failing test**

Add to `tests/test_routes/test_uploads.py`:

```python
@pytest.mark.asyncio
async def test_upload_image_with_cookie_auth(upload_client, upload_settings):
    """Upload should work with cookie-based auth (used by web UI)."""
    # Register and login to get cookie
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

    # Set cookie instead of Authorization header
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

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes/test_uploads.py::test_upload_image_with_cookie_auth -v`
Expected: FAIL with 401 Unauthorized

**Step 3: Write minimal implementation**

Modify `app/dependencies.py` — update `get_current_user_id` to also check the `access_token` cookie:

```python
from fastapi import Depends, HTTPException, Request, status

async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> int:
    token = None

    # Try Bearer token first
    if credentials is not None:
        token = credentials.credentials

    # Fall back to cookie
    if token is None:
        token = request.cookies.get("access_token")

    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token, settings.secret_key)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload["sub"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes/test_uploads.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/dependencies.py tests/test_routes/test_uploads.py
git commit -m "feat: add cookie auth fallback to upload endpoint"
```

---

### Task 2: Mount StaticFiles for uploads directory

Serve uploaded images at `/uploads/` so the browser can display previews.

**Files:**
- Modify: `app/main.py`
- Test: `tests/test_routes/test_uploads.py`

**Step 1: Write the failing test**

Add to `tests/test_routes/test_uploads.py`:

```python
@pytest.mark.asyncio
async def test_uploaded_image_is_served(upload_client, upload_auth_headers, upload_settings):
    """Uploaded images should be accessible via /uploads/ URL."""
    png_bytes = make_png_bytes()

    # Upload the image
    resp = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("serve_test.png", png_bytes, "image/png")},
        headers=upload_auth_headers,
    )
    path = resp.json()["path"]

    # Fetch it back via static URL
    resp = await upload_client.get(f"/uploads/{path}")
    assert resp.status_code == 200
    assert resp.content == png_bytes
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes/test_uploads.py::test_uploaded_image_is_served -v`
Expected: FAIL with 404 Not Found

**Step 3: Write minimal implementation**

Modify `app/main.py`:

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0", lifespan=lifespan)
    # ... existing routers ...

    # Serve uploaded files
    settings = Settings()
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app
```

**Step 4: Run all tests to verify nothing broke**

Run: `uv run pytest tests/test_routes/test_uploads.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/main.py tests/test_routes/test_uploads.py
git commit -m "feat: mount StaticFiles to serve uploaded images"
```

---

### Task 3: Rewrite ad form template with drag-and-drop image upload

Replace the textarea with a drag-and-drop zone, file picker button, thumbnail previews, and remove buttons. Images upload immediately via fetch to `/api/uploads/image`.

**Files:**
- Modify: `app/templates/ads/form.html`

**Step 1: Rewrite the template**

Replace the entire images `<div>` block (lines 20-25) in `app/templates/ads/form.html` with:

```html
<div>
    <label class="block text-sm font-medium text-gray-900">Изображения</label>
    <p class="mt-1 text-xs text-gray-500">Максимум 10 изображений, до 5 МБ каждое</p>

    <!-- Drop zone -->
    <div id="drop-zone" class="mt-2 flex justify-center rounded-lg border-2 border-dashed border-gray-300 px-6 py-8 transition-colors hover:border-indigo-400 cursor-pointer">
        <div class="text-center">
            <svg class="mx-auto h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M6.75 8.25h.008v.008H6.75V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
            </svg>
            <p class="mt-2 text-sm text-gray-600">Перетащите изображения сюда</p>
            <p class="mt-1 text-xs text-gray-500">или</p>
            <button type="button" id="pick-files-btn" class="mt-2 rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-indigo-600 shadow-sm ring-1 ring-indigo-200 hover:bg-indigo-50">Выбрать файлы</button>
            <input type="file" id="file-input" multiple accept="image/*" class="hidden">
        </div>
    </div>

    <!-- Thumbnails -->
    <div id="image-list" class="mt-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3"></div>

    <!-- Upload error messages -->
    <div id="upload-errors"></div>
</div>
```

Then add a `<script>` block before `{% endblock %}` with the upload logic:

```javascript
<script>
(function() {
    const MAX_IMAGES = 10;
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const pickBtn = document.getElementById('pick-files-btn');
    const imageList = document.getElementById('image-list');
    const errorsDiv = document.getElementById('upload-errors');

    // Track current image paths
    const images = [];

    // Load existing images on edit
    {% if ad and ad.images %}
    {% for img in ad.images %}
    images.push("{{ img }}");
    {% endfor %}
    renderImages();
    {% endif %}

    // Pick files button
    pickBtn.addEventListener('click', function(e) {
        e.preventDefault();
        fileInput.click();
    });

    // Also click drop zone to pick
    dropZone.addEventListener('click', function(e) {
        if (e.target === dropZone || dropZone.contains(e.target)) {
            if (e.target !== pickBtn && !pickBtn.contains(e.target)) {
                fileInput.click();
            }
        }
    });

    fileInput.addEventListener('change', function() {
        handleFiles(fileInput.files);
        fileInput.value = '';
    });

    // Drag and drop
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('border-indigo-500', 'bg-indigo-50');
    });
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
    });
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
        handleFiles(e.dataTransfer.files);
    });

    function handleFiles(files) {
        errorsDiv.innerHTML = '';
        for (const file of files) {
            if (images.length >= MAX_IMAGES) {
                showError('Максимум ' + MAX_IMAGES + ' изображений');
                break;
            }
            if (!file.type.startsWith('image/')) {
                showError(file.name + ': не является изображением');
                continue;
            }
            uploadFile(file);
        }
    }

    function uploadFile(file) {
        const placeholder = addPlaceholder(file.name);
        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/uploads/image', {
            method: 'POST',
            body: formData,
            credentials: 'include',
        })
        .then(function(resp) {
            if (!resp.ok) return resp.json().then(function(d) { throw new Error(d.detail || 'Ошибка загрузки'); });
            return resp.json();
        })
        .then(function(data) {
            images.push(data.path);
            placeholder.remove();
            renderImages();
        })
        .catch(function(err) {
            placeholder.remove();
            showError(file.name + ': ' + err.message);
        });
    }

    function addPlaceholder(name) {
        const div = document.createElement('div');
        div.className = 'relative rounded-lg border border-gray-200 bg-gray-50 p-2 flex items-center justify-center aspect-square';
        div.innerHTML = '<div class="text-center"><div class="animate-spin h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto"></div><p class="mt-1 text-xs text-gray-500 truncate max-w-full">' + name + '</p></div>';
        imageList.appendChild(div);
        return div;
    }

    function renderImages() {
        imageList.innerHTML = '';
        images.forEach(function(path, idx) {
            const div = document.createElement('div');
            div.className = 'relative group rounded-lg border border-gray-200 overflow-hidden aspect-square';
            div.innerHTML =
                '<img src="/uploads/' + path + '" class="w-full h-full object-cover" alt="">' +
                '<input type="hidden" name="images" value="' + path + '">' +
                '<button type="button" data-idx="' + idx + '" class="remove-btn absolute top-1 right-1 hidden group-hover:flex items-center justify-center w-6 h-6 rounded-full bg-red-600 text-white text-xs shadow hover:bg-red-700">&times;</button>';
            imageList.appendChild(div);
        });

        // If no images, add empty hidden input so form submits empty
        if (images.length === 0) {
            const empty = document.createElement('input');
            empty.type = 'hidden';
            empty.name = 'images';
            empty.value = '';
            imageList.appendChild(empty);
        }

        // Bind remove buttons
        imageList.querySelectorAll('.remove-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const idx = parseInt(btn.dataset.idx);
                images.splice(idx, 1);
                renderImages();
            });
        });
    }

    function showError(msg) {
        const div = document.createElement('div');
        div.className = 'mt-2 text-sm text-red-600';
        div.textContent = msg;
        errorsDiv.appendChild(div);
        setTimeout(function() { div.remove(); }, 5000);
    }
})();
</script>
```

**Step 2: Visually verify in browser**

Run: `uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
Check: Navigate to `/ads/new`, verify drag-and-drop zone renders, upload works, thumbnails show.

**Step 3: Commit**

```bash
git add app/templates/ads/form.html
git commit -m "feat: drag-and-drop image upload UI in ad form"
```

---

### Task 4: Update form handlers to use getlist for images

Currently `ads_create` and `ads_update` accept `images: str = Form("")` and split by newlines. The new form sends multiple `images` hidden inputs. Update handlers to use `request.form().getlist("images")`.

**Files:**
- Modify: `app/routes/pages.py:250-267` (ads_create)
- Modify: `app/routes/pages.py:292-319` (ads_update)
- Test: `tests/test_routes/test_ads.py` (verify existing tests still pass)

**Step 1: Write a test for multi-value form submission**

Add to `tests/test_routes/test_ads.py` or create an inline test. Since we're testing pages (not API), we test via the page routes. Add to existing test file:

```python
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

    resp = await client.post("/ads/new", data={
        "title": "Multi Image Ad",
        "text": "Test text",
        "images": ["1/img1.jpg", "1/img2.jpg"],
    }, follow_redirects=False)
    assert resp.status_code == 302

    # Verify the ad was created with images
    resp = await client.get("/api/ads", headers={"Authorization": f"Bearer {token}"})
    ads = resp.json()
    assert len(ads) == 1
    assert ads[0]["images"] == ["1/img1.jpg", "1/img2.jpg"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes/test_ads.py::test_create_ad_with_multiple_image_fields -v`
Expected: FAIL (images will be mangled by splitlines)

**Step 3: Update ads_create and ads_update**

In `app/routes/pages.py`, update `ads_create`:

```python
@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad = Ad(user_id=user.id, title=title, text=text, images=image_list)
    db.add(ad)
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)
```

Update `ads_update`:

```python
@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)

    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad.title = title
    ad.text = text
    ad.images = image_list
    ad.is_active = is_active
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)
```

**Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add app/routes/pages.py tests/test_routes/test_ads.py
git commit -m "feat: update ad form handlers for multi-value image fields"
```

---

### Task 5: Run full test suite and verify

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 2: Manual verification**

Run: `uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

Verify:
- `/ads/new`: drag-and-drop zone visible, can drop images, previews appear
- Upload button works as alternative to drag-and-drop
- Uploaded images show thumbnails with remove buttons
- Creating ad saves image paths correctly
- `/ads/{id}/edit`: existing images show as thumbnails
- Removing an image and saving updates correctly
- Max 10 images limit is enforced in UI

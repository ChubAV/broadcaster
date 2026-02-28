# Email Verification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add email verification via 6-digit code before account creation during registration.

**Architecture:** 3-step registration flow (enter email → verify code → set name/password). Verification codes stored in DB table `email_verification_codes`. Emails sent via SMTP through Celery background task. Signed JWT tokens carry email between steps.

**Tech Stack:** aiosmtplib (async SMTP), python-jose (JWT), Celery (background email sending), SQLAlchemy async (code storage), Alembic (migration)

---

### Task 1: Add SMTP Settings to Config

**Files:**
- Modify: `app/config.py:6-55`

**Step 1: Add SMTP fields to Settings class**

In `app/config.py`, add after the `admin_email` field (line 48):

```python
    # SMTP (email verification)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
```

**Step 2: Add SMTP settings to test fixture**

In `tests/conftest.py`, add to the `test_settings` fixture inside `Settings(...)`:

```python
        smtp_host="localhost",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="testpass",
        smtp_from="noreply@test.com",
```

**Step 3: Verify imports work**

Run: `cd /root/source/broadcaster && uv run python -c "from app.config import Settings; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add app/config.py tests/conftest.py
git commit -m "feat: add SMTP settings to config"
```

---

### Task 2: Create EmailVerificationCode Model

**Files:**
- Create: `app/models/email_verification.py`
- Modify: `app/models/__init__.py`

**Step 1: Write the model**

Create `app/models/email_verification.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(6))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

**Step 2: Register in models __init__.py**

In `app/models/__init__.py`, add:

```python
from app.models.email_verification import EmailVerificationCode
```

And add `"EmailVerificationCode"` to `__all__`.

**Step 3: Verify model loads**

Run: `cd /root/source/broadcaster && uv run python -c "from app.models.email_verification import EmailVerificationCode; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add app/models/email_verification.py app/models/__init__.py
git commit -m "feat: add EmailVerificationCode model"
```

---

### Task 3: Create Alembic Migration

**Files:**
- Create: `alembic/versions/<auto>_add_email_verification_codes.py`

**Step 1: Generate migration**

Run: `cd /root/source/broadcaster && just migrate "add email verification codes table"`

**Step 2: Review the generated migration file**

Check the generated file in `alembic/versions/` — it should create table `email_verification_codes` with columns: id, email, code, attempts, verified_at, expires_at, created_at. It should also create an index on `email`.

**Step 3: Commit**

```bash
git add alembic/
git commit -m "feat: add migration for email_verification_codes table"
```

---

### Task 4: Create Email Service

**Files:**
- Create: `app/services/email_service.py`
- Test: `tests/test_services/test_email_service.py`

**Step 1: Write the failing test**

Create `tests/test_services/test_email_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch

from app.services.email_service import send_verification_email


@pytest.mark.asyncio
async def test_send_verification_email_calls_smtp():
    with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = ({}, "OK")
        await send_verification_email(
            to_email="user@example.com",
            code="123456",
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="sender@test.com",
            smtp_password="pass",
            smtp_from="noreply@test.com",
            smtp_use_tls=True,
        )
        mock_send.assert_called_once()
        # Check the message was constructed correctly
        call_kwargs = mock_send.call_args
        message = call_kwargs.kwargs.get("message") or call_kwargs.args[0]
        assert "123456" in str(message)
        assert message["To"] == "user@example.com"
        assert message["From"] == "noreply@test.com"
```

**Step 2: Run test to verify it fails**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_services/test_email_service.py -v`
Expected: FAIL (module not found)

**Step 3: Install aiosmtplib**

Run: `cd /root/source/broadcaster && just add aiosmtplib`

**Step 4: Write the email service**

Create `app/services/email_service.py`:

```python
from email.message import EmailMessage

import aiosmtplib


async def send_verification_email(
    to_email: str,
    code: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    smtp_use_tls: bool = True,
) -> None:
    """Send a verification code email via SMTP."""
    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = f"Код подтверждения: {code}"
    msg.set_content(
        f"Ваш код подтверждения для регистрации в Broadcaster: {code}\n\n"
        f"Код действителен 10 минут.\n\n"
        f"Если вы не запрашивали этот код, проигнорируйте это письмо."
    )

    await aiosmtplib.send(
        message=msg,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_password,
        use_tls=smtp_use_tls,
    )
```

**Step 5: Run test to verify it passes**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_services/test_email_service.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add app/services/email_service.py tests/test_services/test_email_service.py pyproject.toml uv.lock
git commit -m "feat: add email service for sending verification codes via SMTP"
```

---

### Task 5: Add Celery Task for Email Sending

**Files:**
- Modify: `app/worker/tasks.py`

**Step 1: Add the Celery task**

At the end of `app/worker/tasks.py`, add:

```python
@shared_task(name="app.worker.tasks.send_verification_email")
def send_verification_email_task(email: str, code: str):
    """Send verification code email in background."""
    from app.services.email_service import send_verification_email

    settings = get_settings()
    if not settings.smtp_host:
        logger.warning("smtp_not_configured", email=email)
        return

    asyncio.run(send_verification_email(
        to_email=email,
        code=code,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        smtp_from=settings.smtp_from,
        smtp_use_tls=settings.smtp_use_tls,
    ))
    logger.info("verification_email_sent", email=email)
```

**Step 2: Commit**

```bash
git add app/worker/tasks.py
git commit -m "feat: add Celery task for sending verification emails"
```

---

### Task 6: Add Verification Token Helpers to Auth Service

**Files:**
- Modify: `app/services/auth_service.py`
- Test: `tests/test_services/test_auth_service.py`

**Step 1: Write the failing tests**

Add to `tests/test_services/test_auth_service.py`:

```python
from app.services.auth_service import create_verification_token, decode_verification_token


def test_create_and_decode_verification_token():
    token = create_verification_token(
        email="user@test.com", secret_key="test-secret"
    )
    payload = decode_verification_token(token, secret_key="test-secret")
    assert payload is not None
    assert payload["email"] == "user@test.com"
    assert payload["verified"] is False


def test_create_and_decode_verified_token():
    token = create_verification_token(
        email="user@test.com", secret_key="test-secret", verified=True
    )
    payload = decode_verification_token(token, secret_key="test-secret")
    assert payload is not None
    assert payload["email"] == "user@test.com"
    assert payload["verified"] is True


def test_decode_verification_token_invalid():
    payload = decode_verification_token("bad-token", secret_key="test-secret")
    assert payload is None
```

**Step 2: Run tests to verify they fail**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_services/test_auth_service.py -v`
Expected: FAIL (ImportError)

**Step 3: Add the functions to auth_service.py**

Add to `app/services/auth_service.py`:

```python
def create_verification_token(
    email: str, secret_key: str, verified: bool = False, expires_minutes: int = 30
) -> str:
    """Create a JWT token for email verification flow."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"email": email, "verified": verified, "exp": expire, "purpose": "email_verification"}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_verification_token(token: str, secret_key: str) -> dict | None:
    """Decode a verification JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if payload.get("purpose") != "email_verification":
            return None
        return payload
    except (JWTError, KeyError, ValueError):
        return None
```

**Step 4: Run tests to verify they pass**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_services/test_auth_service.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add app/services/auth_service.py tests/test_services/test_auth_service.py
git commit -m "feat: add verification token helpers to auth service"
```

---

### Task 7: Create Registration Step Templates

**Files:**
- Modify: `app/templates/auth/register.html` (becomes Step 1: email input)
- Create: `app/templates/auth/register_verify.html` (Step 2: code input)
- Create: `app/templates/auth/register_complete.html` (Step 3: name + password)

**Step 1: Replace register.html with Step 1 (email only)**

Replace `app/templates/auth/register.html` with:

```html
{% extends "base.html" %}
{% block title %}Регистрация — Broadcaster{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
  <div class="bg-white rounded-xl border border-gray-200 p-8 w-full max-w-sm">
    <div class="text-center mb-8">
      <h1 class="text-xl font-semibold text-gray-900">Broadcaster</h1>
      <p class="text-sm text-gray-500 mt-1">Создайте аккаунт</p>
    </div>

    {% if error %}
    <div class="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{{ error }}</div>
    {% endif %}

    <form method="post" action="/register/send-code" class="space-y-4">
      <div>
        <label for="email" class="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
        <input type="email" name="email" id="email" required autocomplete="email"
          value="{{ email|default('', true) }}"
          class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-colors"
          placeholder="you@example.com">
      </div>
      <button type="submit" class="w-full bg-indigo-600 text-white rounded-lg px-3.5 py-2.5 text-sm font-medium hover:bg-indigo-700 transition-colors">
        Отправить код
      </button>
    </form>

    <p class="text-center text-sm text-gray-500 mt-6">
      Уже есть аккаунт? <a href="/login" class="text-indigo-600 hover:text-indigo-700 font-medium">Войти</a>
    </p>
  </div>
</div>
{% endblock %}
```

**Step 2: Create register_verify.html (Step 2: code input)**

Create `app/templates/auth/register_verify.html`:

```html
{% extends "base.html" %}
{% block title %}Подтверждение email — Broadcaster{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
  <div class="bg-white rounded-xl border border-gray-200 p-8 w-full max-w-sm">
    <div class="text-center mb-8">
      <h1 class="text-xl font-semibold text-gray-900">Broadcaster</h1>
      <p class="text-sm text-gray-500 mt-1">Введите код из письма</p>
    </div>

    {% if success %}
    <div class="bg-green-50 text-green-700 text-sm rounded-lg px-4 py-3 mb-4">{{ success }}</div>
    {% endif %}

    {% if error %}
    <div class="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{{ error }}</div>
    {% endif %}

    <p class="text-sm text-gray-600 mb-4">
      Мы отправили 6-значный код на <strong>{{ email }}</strong>
    </p>

    <form method="post" action="/register/verify" class="space-y-4">
      <input type="hidden" name="token" value="{{ token }}">
      <div>
        <label for="code" class="block text-sm font-medium text-gray-700 mb-1.5">Код подтверждения</label>
        <input type="text" name="code" id="code" required autocomplete="one-time-code"
          maxlength="6" pattern="[0-9]{6}" inputmode="numeric"
          class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-colors text-center text-lg tracking-widest"
          placeholder="000000">
      </div>
      <button type="submit" class="w-full bg-indigo-600 text-white rounded-lg px-3.5 py-2.5 text-sm font-medium hover:bg-indigo-700 transition-colors">
        Подтвердить
      </button>
    </form>

    <form method="post" action="/register/resend-code" class="mt-4">
      <input type="hidden" name="token" value="{{ token }}">
      <button type="submit" class="w-full text-sm text-indigo-600 hover:text-indigo-700 font-medium">
        Отправить код повторно
      </button>
    </form>

    <p class="text-center text-sm text-gray-500 mt-6">
      <a href="/register" class="text-indigo-600 hover:text-indigo-700 font-medium">Назад</a>
    </p>
  </div>
</div>
{% endblock %}
```

**Step 3: Create register_complete.html (Step 3: name + password)**

Create `app/templates/auth/register_complete.html`:

```html
{% extends "base.html" %}
{% block title %}Завершение регистрации — Broadcaster{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
  <div class="bg-white rounded-xl border border-gray-200 p-8 w-full max-w-sm">
    <div class="text-center mb-8">
      <h1 class="text-xl font-semibold text-gray-900">Broadcaster</h1>
      <p class="text-sm text-gray-500 mt-1">Завершите регистрацию</p>
    </div>

    {% if error %}
    <div class="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{{ error }}</div>
    {% endif %}

    <p class="text-sm text-gray-600 mb-4">
      Email <strong>{{ email }}</strong> подтверждён
    </p>

    <form method="post" action="/register/complete" class="space-y-4">
      <input type="hidden" name="token" value="{{ token }}">
      <div>
        <label for="name" class="block text-sm font-medium text-gray-700 mb-1.5">Имя</label>
        <input type="text" name="name" id="name" required autocomplete="name"
          class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-colors"
          placeholder="Ваше имя">
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700 mb-1.5">Пароль</label>
        <input type="password" name="password" id="password" required autocomplete="new-password"
          class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none transition-colors"
          placeholder="Минимум 6 символов" minlength="6">
      </div>
      <button type="submit" class="w-full bg-indigo-600 text-white rounded-lg px-3.5 py-2.5 text-sm font-medium hover:bg-indigo-700 transition-colors">
        Зарегистрироваться
      </button>
    </form>
  </div>
</div>
{% endblock %}
```

**Step 4: Commit**

```bash
git add app/templates/auth/register.html app/templates/auth/register_verify.html app/templates/auth/register_complete.html
git commit -m "feat: add 3-step registration templates"
```

---

### Task 8: Implement Registration Page Routes (3-Step Flow)

**Files:**
- Modify: `app/pages/auth.py`
- Test: `tests/test_pages/test_registration.py`

**Step 1: Write the failing tests**

Create `tests/test_pages/test_registration.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.email_verification import EmailVerificationCode
from app.services.auth_service import decode_verification_token


@pytest.mark.asyncio
async def test_register_page_shows_email_form(client: AsyncClient):
    """Step 1: GET /register shows email input form."""
    response = await client.get("/register")
    assert response.status_code == 200
    html = response.text
    assert 'name="email"' in html
    assert "Отправить код" in html
    # Should NOT have name/password fields
    assert 'name="password"' not in html


@pytest.mark.asyncio
async def test_send_code_creates_verification_and_redirects(
    client: AsyncClient, db_session: AsyncSession
):
    """Step 1: POST /register/send-code creates code in DB and shows verify page."""
    with patch("app.pages.auth.send_verification_email_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(
            "/register/send-code",
            data={"email": "newuser@test.com"},
            follow_redirects=False,
        )

    assert response.status_code == 200
    html = response.text
    assert "newuser@test.com" in html
    assert 'name="code"' in html

    # Verify code was saved in DB
    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "newuser@test.com"
        )
    )
    code_record = result.scalar_one()
    assert len(code_record.code) == 6
    assert code_record.code.isdigit()
    assert code_record.attempts == 0


@pytest.mark.asyncio
async def test_send_code_rejects_existing_email(
    client: AsyncClient, db_session: AsyncSession
):
    """POST /register/send-code rejects already registered email."""
    # Create existing user
    user = User(email="existing@test.com", password_hash="hash", name="Existing")
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/register/send-code",
        data={"email": "existing@test.com"},
    )
    assert response.status_code == 200
    html = response.text
    assert "уже зарегистрирован" in html


@pytest.mark.asyncio
async def test_verify_code_correct(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Step 2: POST /register/verify with correct code shows complete form."""
    with patch("app.pages.auth.send_verification_email_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(
            "/register/send-code",
            data={"email": "verify@test.com"},
        )

    # Extract token from response HTML
    html = response.text
    import re
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    assert token_match, "Token not found in verify page"
    token = token_match.group(1)

    # Get the code from DB
    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "verify@test.com"
        )
    )
    code_record = result.scalar_one()

    # Submit correct code
    response = await client.post(
        "/register/verify",
        data={"token": token, "code": code_record.code},
    )
    assert response.status_code == 200
    html = response.text
    assert 'name="password"' in html
    assert 'name="name"' in html
    assert "verify@test.com" in html


@pytest.mark.asyncio
async def test_verify_code_wrong(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Step 2: POST /register/verify with wrong code shows error."""
    with patch("app.pages.auth.send_verification_email_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(
            "/register/send-code",
            data={"email": "wrong@test.com"},
        )

    html = response.text
    import re
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    token = token_match.group(1)

    response = await client.post(
        "/register/verify",
        data={"token": token, "code": "000000"},
    )
    assert response.status_code == 200
    html = response.text
    assert "Неверный код" in html


@pytest.mark.asyncio
async def test_complete_registration_creates_user(
    client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Step 3: POST /register/complete with valid verified token creates user."""
    with patch("app.pages.auth.send_verification_email_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(
            "/register/send-code",
            data={"email": "complete@test.com"},
        )

    html = response.text
    import re
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    token = token_match.group(1)

    # Get the code and verify it
    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "complete@test.com"
        )
    )
    code_record = result.scalar_one()

    response = await client.post(
        "/register/verify",
        data={"token": token, "code": code_record.code},
    )

    # Extract the verified token
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    verified_token = token_match.group(1)

    # Complete registration
    response = await client.post(
        "/register/complete",
        data={"token": verified_token, "name": "New User", "password": "securepass123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers.get("location", "")

    # Verify user was created
    result = await db_session.execute(
        select(User).where(User.email == "complete@test.com")
    )
    user = result.scalar_one()
    assert user.name == "New User"
```

**Step 2: Run tests to verify they fail**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_pages/test_registration.py -v`
Expected: FAIL (routes don't exist yet)

**Step 3: Implement the registration routes**

Replace the registration routes in `app/pages/auth.py`. The full updated file should be:

```python
import random
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.user import User
from app.models.email_verification import EmailVerificationCode
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_verification_token,
    decode_verification_token,
)
from app.pages.common import templates
from app.worker.tasks import send_verification_email_task

router = APIRouter(tags=["pages"])

CODE_LENGTH = 6
CODE_TTL_MINUTES = 10
CODE_MAX_ATTEMPTS = 5
CODE_RESEND_COOLDOWN_SECONDS = 60


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html", {"request": request, "error": "Неверный email или пароль"}
        )
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


# ---- Step 1: Enter email ----

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register/send-code", response_class=HTMLResponse)
async def register_send_code(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Check if email already registered
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Этот email уже зарегистрирован", "email": email},
        )

    # Rate limit: check last code sent to this email
    result = await db.execute(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == email)
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
        token = create_verification_token(email, settings.secret_key)
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Код уже отправлен. Подождите минуту перед повторной отправкой.",
            },
        )

    # Generate and save code
    code = "".join([str(random.randint(0, 9)) for _ in range(CODE_LENGTH)])
    verification = EmailVerificationCode(
        email=email,
        code=code,
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(verification)
    await db.commit()

    # Send email via Celery
    send_verification_email_task.delay(email, code)

    # Create token and show verify page
    token = create_verification_token(email, settings.secret_key)
    return templates.TemplateResponse(
        "auth/register_verify.html",
        {"request": request, "email": email, "token": token},
    )


# ---- Step 2: Verify code ----

@router.post("/register/verify", response_class=HTMLResponse)
async def register_verify(
    request: Request,
    token: str = Form(...),
    code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Decode token to get email
    payload = decode_verification_token(token, settings.secret_key)
    if not payload:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Ссылка устарела. Начните регистрацию заново."},
        )
    email = payload["email"]

    # Find latest non-expired, non-verified code for this email
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.verified_at.is_(None),
            EmailVerificationCode.expires_at > now,
            EmailVerificationCode.attempts < CODE_MAX_ATTEMPTS,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    code_record = result.scalar_one_or_none()

    if not code_record:
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Код истёк или превышено число попыток. Отправьте код заново.",
            },
        )

    if code_record.code != code.strip():
        code_record.attempts += 1
        await db.commit()
        remaining = CODE_MAX_ATTEMPTS - code_record.attempts
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": f"Неверный код. Осталось попыток: {remaining}",
            },
        )

    # Mark as verified
    code_record.verified_at = now
    await db.commit()

    # Issue verified token
    verified_token = create_verification_token(email, settings.secret_key, verified=True)
    return templates.TemplateResponse(
        "auth/register_complete.html",
        {"request": request, "email": email, "token": verified_token},
    )


@router.post("/register/resend-code", response_class=HTMLResponse)
async def register_resend_code(
    request: Request,
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Ссылка устарела. Начните регистрацию заново."},
        )
    email = payload["email"]

    # Rate limit check
    result = await db.execute(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == email)
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Подождите минуту перед повторной отправкой.",
            },
        )

    # Generate new code
    code = "".join([str(random.randint(0, 9)) for _ in range(CODE_LENGTH)])
    verification = EmailVerificationCode(
        email=email,
        code=code,
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(verification)
    await db.commit()

    send_verification_email_task.delay(email, code)

    new_token = create_verification_token(email, settings.secret_key)
    return templates.TemplateResponse(
        "auth/register_verify.html",
        {
            "request": request,
            "email": email,
            "token": new_token,
            "success": "Новый код отправлен на вашу почту.",
        },
    )


# ---- Step 3: Complete registration ----

@router.post("/register/complete", response_class=HTMLResponse)
async def register_complete(
    request: Request,
    token: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or not payload.get("verified"):
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Ссылка устарела. Начните регистрацию заново."},
        )
    email = payload["email"]

    # Double-check email not taken
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Этот email уже зарегистрирован"},
        )

    if len(password) < 6:
        verified_token = create_verification_token(email, settings.secret_key, verified=True)
        return templates.TemplateResponse(
            "auth/register_complete.html",
            {"request": request, "email": email, "token": verified_token, "error": "Пароль должен быть не менее 6 символов"},
        )

    user = User(email=email, password_hash=hash_password(password), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)
```

**Step 4: Run tests to verify they pass**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_pages/test_registration.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add app/pages/auth.py tests/test_pages/test_registration.py
git commit -m "feat: implement 3-step email verification registration flow"
```

---

### Task 9: Update REST API Registration

**Files:**
- Modify: `app/routes/auth.py`
- Modify: `tests/test_routes/test_auth.py`

The REST API `/api/auth/register` needs updating. Since the API is used by the `auth_headers` test fixture (and possibly external clients), we keep backward compatibility: the API still creates users directly but now also accepts an optional `verification_token` field. If SMTP is configured, registration without a valid verified token is rejected.

**Step 1: Update API route**

In `app/routes/auth.py`, update the `RegisterRequest` and `register` endpoint:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_settings
from app.config import Settings
from app.repositories.user import UserRepository
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_verification_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    verification_token: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # If SMTP is configured, require verified token
    if settings.smtp_host and not data.verification_token:
        raise HTTPException(status_code=400, detail="Email verification required")
    if data.verification_token:
        payload = decode_verification_token(data.verification_token, settings.secret_key)
        if not payload or not payload.get("verified") or payload.get("email") != data.email:
            raise HTTPException(status_code=400, detail="Invalid verification token")

    repo = UserRepository(db)
    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await repo.create(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)):
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is blocked")
    token = create_access_token(user.id, settings.secret_key, settings.access_token_expire_minutes)
    return TokenResponse(access_token=token)
```

**Note:** The existing tests set `smtp_host=""` (empty) in `test_settings`, so they won't require verification tokens. This preserves backward compatibility for tests.

**Step 2: Run existing auth tests to verify no regression**

Run: `cd /root/source/broadcaster && uv run pytest tests/test_routes/test_auth.py -v`
Expected: All PASS (smtp_host is empty in test settings, so verification is not required)

**Step 3: Commit**

```bash
git add app/routes/auth.py
git commit -m "feat: update REST API registration to support email verification"
```

---

### Task 10: Run Full Test Suite

**Step 1: Run all tests**

Run: `cd /root/source/broadcaster && uv run pytest tests/ -v`
Expected: All tests PASS

**Step 2: Fix any failures**

If any tests fail, investigate and fix. Common issues:
- `auth_headers` fixture uses `/api/auth/register` — this should still work since `smtp_host=""` in test settings
- Templates referencing old register form — verify register.html was updated correctly

**Step 3: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: resolve test failures after email verification integration"
```

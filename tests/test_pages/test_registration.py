import pytest
import re
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.email_verification import EmailVerificationCode


@pytest.mark.asyncio
async def test_register_page_shows_email_form(client: AsyncClient):
    """Step 1: GET /register shows email input form."""
    response = await client.get("/register")
    assert response.status_code == 200
    html = response.text
    assert 'name="email"' in html
    assert "Отправить код" in html
    assert 'name="password"' not in html


@pytest.mark.asyncio
async def test_send_code_creates_verification_and_shows_verify(
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

    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    assert token_match, "Token not found in verify page"
    token = token_match.group(1)

    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "verify@test.com"
        )
    )
    code_record = result.scalar_one()

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
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    token = token_match.group(1)

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

    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    verified_token = token_match.group(1)

    response = await client.post(
        "/register/complete",
        data={"token": verified_token, "name": "New User", "password": "securepass123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers.get("location", "")

    result = await db_session.execute(
        select(User).where(User.email == "complete@test.com")
    )
    user = result.scalar_one()
    assert user.name == "New User"

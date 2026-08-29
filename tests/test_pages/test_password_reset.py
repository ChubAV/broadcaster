import pytest
import pytest_asyncio
import re
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.email_verification import EmailVerificationCode
from app.pages import notices
from app.services.auth_service import hash_password


@pytest_asyncio.fixture
async def registered_user(db_session: AsyncSession) -> User:
    """Create a registered user for password reset tests."""
    user = User(email="reset@test.com", password_hash=hash_password("oldpassword"), name="Reset User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_forgot_password_page(client: AsyncClient):
    """GET /forgot-password shows email form."""
    response = await client.get("/forgot-password")
    assert response.status_code == 200
    html = response.text
    assert 'name="email"' in html
    assert "Отправить код" in html


@pytest.mark.asyncio
async def test_send_code_unknown_email(client: AsyncClient):
    """POST /forgot-password/send-code with unknown email shows error."""
    response = await client.post(
        "/forgot-password/send-code",
        data={"email": "unknown@test.com"},
    )
    assert response.status_code == 200
    assert "не найден" in response.text


@pytest.mark.asyncio
async def test_send_code_creates_code(
    client: AsyncClient, db_session: AsyncSession, registered_user: User
):
    """POST /forgot-password/send-code creates code in DB."""
    response = await client.post(
        "/forgot-password/send-code",
        data={"email": "reset@test.com"},
    )
    assert response.status_code == 200
    html = response.text
    assert "reset@test.com" in html
    assert 'name="code"' in html

    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "reset@test.com",
            EmailVerificationCode.purpose == "password_reset",
        )
    )
    code_record = result.scalar_one()
    assert len(code_record.code) == 6
    assert code_record.purpose == "password_reset"


@pytest.mark.asyncio
async def test_verify_correct_code(
    client: AsyncClient, db_session: AsyncSession, registered_user: User, test_settings
):
    """POST /forgot-password/verify with correct code shows reset form."""
    response = await client.post(
        "/forgot-password/send-code",
        data={"email": "reset@test.com"},
    )
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    assert token_match
    token = token_match.group(1)

    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "reset@test.com",
            EmailVerificationCode.purpose == "password_reset",
        )
    )
    code_record = result.scalar_one()

    response = await client.post(
        "/forgot-password/verify",
        data={"token": token, "code": code_record.code},
    )
    assert response.status_code == 200
    html = response.text
    assert 'name="password"' in html
    assert "reset@test.com" in html


@pytest.mark.asyncio
async def test_verify_wrong_code(
    client: AsyncClient, db_session: AsyncSession, registered_user: User, test_settings
):
    """POST /forgot-password/verify with wrong code shows error."""
    response = await client.post(
        "/forgot-password/send-code",
        data={"email": "reset@test.com"},
    )
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    token = token_match.group(1)

    response = await client.post(
        "/forgot-password/verify",
        data={"token": token, "code": "000000"},
    )
    assert response.status_code == 200
    assert "Неверный код" in response.text


@pytest.mark.asyncio
async def test_complete_password_reset(
    client: AsyncClient, db_session: AsyncSession, registered_user: User, test_settings
):
    """Full flow: send code -> verify -> reset password -> login with new password."""
    # Step 1: Send code
    response = await client.post(
        "/forgot-password/send-code",
        data={"email": "reset@test.com"},
    )
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    token = token_match.group(1)

    # Get code from DB
    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "reset@test.com",
            EmailVerificationCode.purpose == "password_reset",
        )
    )
    code_record = result.scalar_one()

    # Step 2: Verify code
    response = await client.post(
        "/forgot-password/verify",
        data={"token": token, "code": code_record.code},
    )
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    verified_token = token_match.group(1)

    # Step 3: Reset password
    response = await client.post(
        "/forgot-password/reset",
        data={"token": verified_token, "password": "newpassword123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers.get("location", "")
    # АДРЕС СМЕНИЛСЯ, УТВЕРЖДЕНИЕ — НЕТ: исход по-прежнему обязан доехать до
    # человека, но едет он ОБЩИМ параметром и кодом закрытого реестра, а не
    # собственным написанием этого одного экрана.
    assert f"notice={notices.PASSWORD_RESET_DONE}" in response.headers.get("location", "")

    # Step 4: Login with new password
    response = await client.post(
        "/login",
        data={"email": "reset@test.com", "password": "newpassword123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard" in response.headers.get("location", "")

    # Old password should not work
    response = await client.post(
        "/login",
        data={"email": "reset@test.com", "password": "oldpassword"},
    )
    assert response.status_code == 200
    assert "Неверный" in response.text


@pytest.mark.asyncio
async def test_reset_short_password(
    client: AsyncClient, db_session: AsyncSession, registered_user: User, test_settings
):
    """POST /forgot-password/reset with short password shows error."""
    response = await client.post(
        "/forgot-password/send-code",
        data={"email": "reset@test.com"},
    )
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    token = token_match.group(1)

    result = await db_session.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == "reset@test.com",
            EmailVerificationCode.purpose == "password_reset",
        )
    )
    code_record = result.scalar_one()

    response = await client.post(
        "/forgot-password/verify",
        data={"token": token, "code": code_record.code},
    )
    html = response.text
    token_match = re.search(r'name="token" value="([^"]+)"', html)
    verified_token = token_match.group(1)

    response = await client.post(
        "/forgot-password/reset",
        data={"token": verified_token, "password": "abc"},
    )
    assert response.status_code == 200
    assert "не менее 6 символов" in response.text

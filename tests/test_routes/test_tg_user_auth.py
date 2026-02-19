import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.messenger_account import MessengerAccount
from app.models.telegram_auth_session import TelegramAuthSession


@pytest_asyncio.fixture
async def auth_setup():
    """Full setup for tg_user auth flow tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
    )
    app = create_app()

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        # Register a user
        async with AsyncClient(
            transport=transport, base_url="http://test", follow_redirects=True
        ) as reg_client:
            await reg_client.post(
                "/register",
                data={"email": "tgauth@test.com", "password": "pass123", "name": "TG User"},
            )
            # Get the cookie
            cookies = reg_client.cookies

        # Set cookies on non-redirect client
        for name, value in cookies.items():
            client.cookies.set(name, value)

        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_connect_tg_user_page_shows_phone_form(auth_setup):
    client, _ = auth_setup
    resp = await client.get("/accounts/connect/tg_user")
    assert resp.status_code == 200
    assert "phone_number" in resp.text
    assert "Отправить код" in resp.text


@pytest.mark.asyncio
async def test_send_code_success_redirects_to_verify(auth_setup):
    client, session_factory = auth_setup

    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = "test_code_hash"

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    assert resp.status_code == 302
    assert "/accounts/connect/tg_user/verify?session_id=" in resp.headers["location"]

    # Verify auth session was created
    async with session_factory() as session:
        result = await session.execute(select(TelegramAuthSession))
        auth_session = result.scalar_one()
        assert auth_session.phone_number == "+79001234567"
        assert auth_session.phone_code_hash == "test_code_hash"
        assert auth_session.status == "code_sent"


@pytest.mark.asyncio
async def test_send_code_error_shows_error_on_form(auth_setup):
    client, session_factory = auth_setup

    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.side_effect = Exception("Phone number invalid")

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+invalid"},
        )

    assert resp.status_code == 200
    assert "Phone number invalid" in resp.text

    # Verify auth session was created with error status
    async with session_factory() as session:
        result = await session.execute(select(TelegramAuthSession))
        auth_session = result.scalar_one()
        assert auth_session.status == "error"


@pytest.mark.asyncio
async def test_send_code_no_api_config_shows_error(auth_setup):
    """When telegram_api_id is 0, should show error."""
    client, session_factory = auth_setup

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    settings_no_api = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=0,
        telegram_api_hash="",
    )
    app = create_app()

    async def override_db():
        async with sf() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings_no_api

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as c:
        await c.post(
            "/register",
            data={"email": "noapi@test.com", "password": "pass123", "name": "No API"},
        )
        resp = await c.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    assert resp.status_code == 200
    assert "Telegram API не настроен" in resp.text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_verify_code_success_creates_account(auth_setup):
    client, session_factory = auth_setup

    # Step 1: send code
    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = "test_code_hash"

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    location = resp.headers["location"]
    session_id = location.split("session_id=")[1]

    # Step 2: verify code
    with patch("app.routes.pages.verify_code", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = "exported_session_string"

        resp = await client.post(
            "/accounts/connect/tg_user/verify",
            data={"session_id": session_id, "step": "code", "code": "12345"},
        )

    assert resp.status_code == 302
    assert resp.headers["location"] == "/accounts"

    # Verify account was created
    async with session_factory() as session:
        result = await session.execute(select(MessengerAccount))
        account = result.scalar_one()
        assert account.type == "tg_user"
        assert account.credentials == "exported_session_string"
        assert account.status == "active"

        # Auth session should be completed
        auth_result = await session.execute(select(TelegramAuthSession))
        auth_session = auth_result.scalar_one()
        assert auth_session.status == "completed"


@pytest.mark.asyncio
async def test_verify_code_needs_2fa_redirects(auth_setup):
    client, session_factory = auth_setup

    # Step 1: send code
    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = "test_code_hash"

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    location = resp.headers["location"]
    session_id = location.split("session_id=")[1]

    # Step 2: verify code raises SessionPasswordNeeded
    from pyrogram.errors import SessionPasswordNeeded

    with patch("app.routes.pages.verify_code", new_callable=AsyncMock) as mock_verify:
        mock_verify.side_effect = SessionPasswordNeeded()

        resp = await client.post(
            "/accounts/connect/tg_user/verify",
            data={"session_id": session_id, "step": "code", "code": "12345"},
        )

    assert resp.status_code == 302
    assert f"session_id={session_id}" in resp.headers["location"]

    # Auth session should be needs_2fa
    async with session_factory() as session:
        auth_result = await session.execute(select(TelegramAuthSession))
        auth_session = auth_result.scalar_one()
        assert auth_session.status == "needs_2fa"


@pytest.mark.asyncio
async def test_verify_2fa_success_creates_account(auth_setup):
    client, session_factory = auth_setup

    # Step 1: send code
    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = "test_code_hash"

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    location = resp.headers["location"]
    session_id = location.split("session_id=")[1]

    # Step 2: code → needs 2FA
    from pyrogram.errors import SessionPasswordNeeded

    with patch("app.routes.pages.verify_code", new_callable=AsyncMock) as mock_verify:
        mock_verify.side_effect = SessionPasswordNeeded()
        await client.post(
            "/accounts/connect/tg_user/verify",
            data={"session_id": session_id, "step": "code", "code": "12345"},
        )

    # Step 3: verify 2FA password
    with patch("app.routes.pages.tg_verify_password", new_callable=AsyncMock) as mock_2fa:
        mock_2fa.return_value = "exported_session_string_2fa"

        resp = await client.post(
            "/accounts/connect/tg_user/verify",
            data={"session_id": session_id, "step": "2fa", "password": "my2fapass"},
        )

    assert resp.status_code == 302
    assert resp.headers["location"] == "/accounts"

    async with session_factory() as session:
        result = await session.execute(select(MessengerAccount))
        account = result.scalar_one()
        assert account.credentials == "exported_session_string_2fa"


@pytest.mark.asyncio
async def test_verify_wrong_code_shows_error(auth_setup):
    client, session_factory = auth_setup

    # Step 1: send code
    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = "test_code_hash"

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    location = resp.headers["location"]
    session_id = location.split("session_id=")[1]

    # Step 2: wrong code
    with patch("app.routes.pages.verify_code", new_callable=AsyncMock) as mock_verify:
        mock_verify.side_effect = Exception("The phone code you provided is invalid")

        resp = await client.post(
            "/accounts/connect/tg_user/verify",
            data={"session_id": session_id, "step": "code", "code": "00000"},
        )

    assert resp.status_code == 200
    assert "phone code you provided is invalid" in resp.text

    # No account should be created
    async with session_factory() as session:
        result = await session.execute(select(MessengerAccount))
        accounts = result.scalars().all()
        assert len(accounts) == 0


@pytest.mark.asyncio
async def test_verify_page_shows_2fa_form_when_needed(auth_setup):
    client, session_factory = auth_setup

    # Step 1: send code
    with patch("app.routes.pages.start_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = "test_code_hash"

        resp = await client.post(
            "/accounts/connect/tg_user/send-code",
            data={"phone_number": "+79001234567"},
        )

    location = resp.headers["location"]
    session_id = location.split("session_id=")[1]

    # Mark session as needs_2fa
    async with session_factory() as session:
        auth_session = (await session.execute(select(TelegramAuthSession))).scalar_one()
        auth_session.status = "needs_2fa"
        await session.commit()

    # GET verify page should show 2FA form
    resp = await client.get(f"/accounts/connect/tg_user/verify?session_id={session_id}")
    assert resp.status_code == 200
    assert "password" in resp.text
    assert "Пароль 2FA" in resp.text

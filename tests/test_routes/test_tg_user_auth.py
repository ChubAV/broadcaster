import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def auth_setup():
    """Full setup for tg_user QR auth flow tests."""
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
    app = create_app(settings=settings)

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
            await reg_client.post("/api/auth/register", json={
                "email": "tgauth@test.com", "password": "pass123", "name": "TG User",
            })
            await reg_client.post("/login", data={"email": "tgauth@test.com", "password": "pass123"})
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
async def test_connect_tg_user_page_shows_qr_button(auth_setup):
    client, _ = auth_setup
    resp = await client.get("/accounts/connect/tg_user")
    assert resp.status_code == 200
    assert "QR" in resp.text
    assert "start-btn" in resp.text


@pytest.mark.asyncio
async def test_start_qr_returns_session_and_image(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.start_qr_auth", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = ("test_session_id", "tg://login?token=abc123")

        resp = await client.post("/accounts/connect/tg_user/start-qr")

    data = resp.json()
    assert "session_id" in data
    assert data["session_id"] == "test_session_id"
    assert "qr_image" in data
    assert data["qr_image"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_start_qr_no_api_config_returns_error(auth_setup):
    """When telegram_api_id is 0, should return error."""
    client, _ = auth_setup

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
    app = create_app(settings=settings_no_api)

    async def override_db():
        async with sf() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings_no_api

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as c:
        await c.post("/api/auth/register", json={
            "email": "noapi@test.com", "password": "pass123", "name": "No API",
        })
        await c.post("/login", data={"email": "noapi@test.com", "password": "pass123"})
        resp = await c.post("/accounts/connect/tg_user/start-qr")

    data = resp.json()
    assert "error" in data
    assert "Telegram API не настроен" in data["error"]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_start_qr_error_returns_error(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.start_qr_auth", new_callable=AsyncMock) as mock_start:
        mock_start.side_effect = Exception("Connection failed")

        resp = await client.post("/accounts/connect/tg_user/start-qr")

    data = resp.json()
    assert "error" in data
    assert "Connection failed" in data["error"]


@pytest.mark.asyncio
async def test_qr_status_returns_status(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.get_qr_status") as mock_status:
        mock_status.return_value = {"status": "waiting"}

        resp = await client.get("/accounts/connect/tg_user/qr-status?session_id=test123")

    data = resp.json()
    assert data["status"] == "waiting"


@pytest.mark.asyncio
async def test_qr_status_success(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.get_qr_status") as mock_status:
        mock_status.return_value = {"status": "success"}

        resp = await client.get("/accounts/connect/tg_user/qr-status?session_id=test123")

    data = resp.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_complete_auth_creates_account(auth_setup):
    client, session_factory = auth_setup

    with patch("app.pages.accounts.complete_auth", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = "exported_session_string"

        resp = await client.post(
            "/accounts/connect/tg_user/complete",
            content='{"session_id": "test_session_id"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert data["status"] == "success"

    # Verify account was created
    async with session_factory() as session:
        result = await session.execute(select(MessengerAccount))
        account = result.scalar_one()
        assert account.type == "tg_user"
        assert account.credentials == "exported_session_string"
        assert account.status == "active"


@pytest.mark.asyncio
async def test_complete_auth_no_session_returns_error(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.complete_auth", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = None

        resp = await client.post(
            "/accounts/connect/tg_user/complete",
            content='{"session_id": "nonexistent"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_verify_2fa_success_creates_account(auth_setup):
    client, session_factory = auth_setup

    with patch("app.pages.accounts.submit_2fa", new_callable=AsyncMock) as mock_2fa:
        mock_2fa.return_value = "session_string_2fa"

        with patch("app.pages.accounts.complete_auth", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "session_string_2fa"

            resp = await client.post(
                "/accounts/connect/tg_user/verify-2fa",
                content='{"session_id": "test_session", "password": "my2fapass"}',
                headers={"Content-Type": "application/json"},
            )

    data = resp.json()
    assert data["status"] == "success"

    async with session_factory() as session:
        result = await session.execute(select(MessengerAccount))
        account = result.scalar_one()
        assert account.credentials == "session_string_2fa"
        assert account.status == "active"


@pytest.mark.asyncio
async def test_verify_2fa_wrong_password_returns_error(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.submit_2fa", new_callable=AsyncMock) as mock_2fa:
        mock_2fa.side_effect = ValueError("Неверный пароль 2FA.")

        resp = await client.post(
            "/accounts/connect/tg_user/verify-2fa",
            content='{"session_id": "test_session", "password": "wrongpass"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "error" in data
    assert "Неверный пароль" in data["error"]


@pytest.mark.asyncio
async def test_refresh_qr_returns_new_image(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.refresh_qr", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = "tg://login?token=newtoken"

        resp = await client.post(
            "/accounts/connect/tg_user/refresh-qr",
            content='{"session_id": "test_session"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "qr_image" in data
    assert data["qr_image"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_refresh_qr_failure_returns_error(auth_setup):
    client, _ = auth_setup

    with patch("app.pages.accounts.refresh_qr", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = None

        resp = await client.post(
            "/accounts/connect/tg_user/refresh-qr",
            content='{"session_id": "test_session"}',
            headers={"Content-Type": "application/json"},
        )

    data = resp.json()
    assert "error" in data

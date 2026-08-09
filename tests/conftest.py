import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app


@pytest_asyncio.fixture
async def test_settings():
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
        wa_bridge_urls=["http://localhost:3000"],
        admin_email="admin@test.com",
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        smtp_from="noreply@test.com",
    )


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session, test_settings):
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register a user and return auth headers."""
    await client.post("/api/auth/register", json={
        "email": "testuser@test.com",
        "password": "testpass123",
        "name": "Test User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "testuser@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authed_client(client, auth_headers):
    """Client with the httpOnly access_token cookie of a regular user.

    Page routes read the cookie, not the Bearer header — auth_headers alone
    does not authorize a page request.
    """
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )
    return client


@pytest_asyncio.fixture
async def admin_client(client, test_settings):
    """Client with the httpOnly access_token cookie of the admin user.

    check_is_admin compares user.email to settings.admin_email, so the user
    must be registered with exactly that address.
    """
    await client.post("/api/auth/register", json={
        "email": test_settings.admin_email,
        "password": "testpass123",
        "name": "Admin User",
    })
    await client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": "testpass123"},
        follow_redirects=False,
    )
    return client

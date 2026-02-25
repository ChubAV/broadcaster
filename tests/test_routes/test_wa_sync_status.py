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
from app.models.group import Group
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def sync_setup():
    """Full setup with db session factory for WA sync-status tests."""
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
        wa_bridge_urls=["http://localhost:3000"],
    )
    app = create_app(settings=settings)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as client:
        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _login(client: AsyncClient) -> None:
    """Register and login via page forms, storing cookie on the client."""
    await client.post(
        "/register",
        data={"email": "wasync@test.com", "password": "pass123", "name": "WA Sync User"},
    )


@pytest.mark.asyncio
async def test_sync_status_returns_syncing_html(sync_setup):
    """When bridge reports state='syncing', endpoint returns HTML with spinner text."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="syncing",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_sync_status = AsyncMock(
            return_value={"state": "syncing", "groups": None}
        )

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    html = resp.text
    assert "Синхронизация..." in html


@pytest.mark.asyncio
async def test_sync_status_ready_saves_groups(sync_setup):
    """When bridge reports state='ready' with groups, groups are saved and account becomes active."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="syncing",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    mock_groups = [
        {"id": "120363001@g.us", "name": "WA Group Alpha"},
        {"id": "120363002@g.us", "name": "WA Group Beta"},
    ]

    with patch("app.pages.accounts.WhatsAppMessenger") as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_sync_status = AsyncMock(
            return_value={"state": "ready", "groups": mock_groups}
        )

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    html = resp.text
    assert "active" in html

    # Verify groups saved in DB
    async with session_factory() as session:
        result = await session.execute(
            select(Group).where(Group.account_id == account_id).order_by(Group.id)
        )
        groups = result.scalars().all()
        assert len(groups) == 2
        assert groups[0].name == "WA Group Alpha"
        assert groups[0].group_external_id == "120363001@g.us"
        assert groups[1].name == "WA Group Beta"
        assert groups[1].group_external_id == "120363002@g.us"

    # Verify account status changed to active
    async with session_factory() as session:
        result = await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )
        account = result.scalar_one()
        assert account.status == "active"


@pytest.mark.asyncio
async def test_sync_status_failed_sets_sync_failed(sync_setup):
    """When bridge reports state='failed', account status becomes sync_failed."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="syncing",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_sync_status = AsyncMock(
            return_value={"state": "failed", "groups": None}
        )

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    html = resp.text
    assert "Ошибка синхронизации" in html

    # Verify account status changed to sync_failed
    async with session_factory() as session:
        result = await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )
        account = result.scalar_one()
        assert account.status == "sync_failed"


@pytest.mark.asyncio
async def test_retry_sync_resets_status(sync_setup):
    """POST retry-sync resets sync_failed to syncing and calls bridge."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="sync_failed",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockMessenger:
        instance = MockMessenger.return_value
        instance.retry_sync = AsyncMock(return_value={"status": "ok"})

        resp = await client.post(f"/accounts/{account_id}/retry-sync")

    assert resp.status_code == 200  # followed redirect to /accounts

    # Verify bridge retry_sync was called
    instance.retry_sync.assert_called_once()

    # Verify account status reset to syncing
    async with session_factory() as session:
        result = await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )
        account = result.scalar_one()
        assert account.status == "syncing"


@pytest.mark.asyncio
async def test_sync_status_unknown_sets_sync_failed(sync_setup):
    """When bridge returns unknown (session unloaded, reload failed), set sync_failed."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="syncing",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch("app.pages.accounts.WhatsAppMessenger") as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_sync_status = AsyncMock(
            return_value={"state": "unknown", "groups": None}
        )

        resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "Ошибка синхронизации" in resp.text

    async with session_factory() as session:
        result = await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )
        account = result.scalar_one()
        assert account.status == "sync_failed"

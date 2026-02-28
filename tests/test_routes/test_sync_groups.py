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
from app.models.group import Group
from app.models.messenger_account import MessengerAccount


@pytest_asyncio.fixture
async def sync_setup():
    """Full setup with db session factory for sync-groups tests."""
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
        transport=transport, base_url="http://test", follow_redirects=True
    ) as client:
        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _login(client: AsyncClient) -> None:
    """Register and login via API + page forms, storing cookie on the client."""
    await client.post("/api/auth/register", json={
        "email": "sync@test.com", "password": "pass123", "name": "Sync User",
    })
    await client.post("/login", data={"email": "sync@test.com", "password": "pass123"})


@pytest.mark.asyncio
async def test_sync_groups_creates_groups(sync_setup):
    client, session_factory = sync_setup
    await _login(client)

    # Create tg_user account directly in DB
    async with session_factory() as session:
        # Find user
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session-string",
            status="active",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    # Mock TelegramUserMessenger.get_groups
    mock_groups = [
        {"id": "-100111", "name": "Group A"},
        {"id": "-100222", "name": "Group B"},
    ]

    with patch(
        "app.pages.accounts.TelegramUserMessenger"
    ) as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_groups = AsyncMock(return_value=mock_groups)

        resp = await client.post(f"/accounts/{account_id}/sync-groups")

    assert resp.status_code == 200  # followed redirect to /groups

    async with session_factory() as session:
        result = await session.execute(
            select(Group).where(Group.account_id == account_id).order_by(Group.id)
        )
        groups = result.scalars().all()
        assert len(groups) == 2
        assert groups[0].name == "Group A"
        assert groups[0].group_external_id == "-100111"
        assert groups[1].name == "Group B"
        assert groups[1].group_external_id == "-100222"


@pytest.mark.asyncio
async def test_sync_groups_uses_settings_api_credentials(sync_setup):
    """Verify that sync_groups passes api_id/api_hash from settings to TelegramUserMessenger."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session-string",
            status="active",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    with patch(
        "app.pages.accounts.TelegramUserMessenger"
    ) as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_groups = AsyncMock(return_value=[])

        await client.post(f"/accounts/{account_id}/sync-groups")

        MockMessenger.assert_called_once_with(
            session_string="session-string",
            api_id=12345,
            api_hash="test_api_hash",
        )


@pytest.mark.asyncio
async def test_sync_groups_always_uses_settings_credentials(sync_setup):
    """Sync groups always uses api_id/api_hash from settings, even when zero."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    # Settings with no telegram_api_id
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
        telegram_api_id=0,
        telegram_api_hash="",
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
        await client.post("/api/auth/register", json={
            "email": "fallback@test.com", "password": "pass123", "name": "Fallback User",
        })
        await client.post("/login", data={"email": "fallback@test.com", "password": "pass123"})

        async with session_factory() as session:
            from app.models.user import User

            user = (await session.execute(select(User))).scalar_one()
            account = MessengerAccount(
                user_id=user.id,
                type="tg_user",
                credentials="session-string",
                status="active",
            )
            session.add(account)
            await session.commit()
            account_id = account.id

        with patch(
            "app.pages.accounts.TelegramUserMessenger"
        ) as MockMessenger:
            instance = MockMessenger.return_value
            instance.get_groups = AsyncMock(return_value=[])

            await client.post(f"/accounts/{account_id}/sync-groups")

            MockMessenger.assert_called_once_with(
                session_string="session-string",
                api_id=0,
                api_hash="",
            )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_sync_groups_skips_existing(sync_setup):
    client, session_factory = sync_setup
    await _login(client)

    # Create tg_user account and one existing group
    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="tg_user",
            credentials="session-string",
            status="active",
        )
        session.add(account)
        await session.flush()

        existing_group = Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type="tg_user",
            group_external_id="-100111",
            name="Existing Group A",
        )
        session.add(existing_group)
        await session.commit()
        account_id = account.id

    mock_groups = [
        {"id": "-100111", "name": "Group A (updated name)"},
        {"id": "-100333", "name": "Group C"},
    ]

    with patch(
        "app.pages.accounts.TelegramUserMessenger"
    ) as MockMessenger:
        instance = MockMessenger.return_value
        instance.get_groups = AsyncMock(return_value=mock_groups)

        await client.post(f"/accounts/{account_id}/sync-groups")

    async with session_factory() as session:
        result = await session.execute(
            select(Group).where(Group.account_id == account_id).order_by(Group.id)
        )
        groups = result.scalars().all()
        # Should have 2: existing + new, no duplicate
        assert len(groups) == 2
        # Existing keeps its original name
        assert groups[0].name == "Existing Group A"
        assert groups[0].group_external_id == "-100111"
        # New group created
        assert groups[1].name == "Group C"
        assert groups[1].group_external_id == "-100333"



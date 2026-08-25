import re
import sys

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
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
        _env_file=None,
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
    """Register and login via API + page forms, storing cookie on the client."""
    await client.post("/api/auth/register", json={
        "email": "wasync@test.com", "password": "pass123", "name": "WA Sync User",
    })
    await client.post("/login", data={"email": "wasync@test.com", "password": "pass123"})


@pytest.mark.asyncio
async def test_sync_status_returns_syncing_html(sync_setup):
    """Account with status=syncing returns spinner HTML."""
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

    resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "Синхронизация..." in resp.text


@pytest.mark.asyncio
async def test_sync_status_active_shows_groups(sync_setup):
    """Account with status=active returns active row with group count."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="active",
        )
        session.add(account)
        await session.flush()

        # Add some groups
        for i in range(3):
            session.add(
                Group(
                    user_id=user.id,
                    account_id=account.id,
                    messenger_type="wa",
                    group_external_id=f"group{i}@g.us",
                    name=f"Group {i}",
                )
            )
        await session.commit()
        account_id = account.id

    resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "Активно" in resp.text
    # Задача 260825-of5: ответ опроса заменяет КАРТОЧКУ сетки целиком, и число
    # групп называет себя КЛЮЧОМ карточки, а не подписью ячейки таблицы —
    # шапки колонок у сетки нет, компенсировать её скрытие нечем.
    #
    # Ключ и число проверяются ОДНИМ утверждением, как это было сделано для
    # ячейки: число «3» без своего ключа тест пройти не должно, иначе покрытие
    # свелось бы к «где-то на странице есть тройка».
    assert re.search(
        r'<span class="kv__k">Групп</span>\s*<span class="kv__v">3</span>',
        resp.text,
    ), resp.text


@pytest.mark.asyncio
async def test_sync_status_failed_shows_error(sync_setup):
    """Account with status=sync_failed returns error row with retry button."""
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

    resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert "Ошибка синхронизации" in resp.text
    assert "retry-sync" in resp.text


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

        with patch.dict(sys.modules, {"app.worker.celery_app": MagicMock()}):
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
async def test_sync_status_empty_for_other_statuses(sync_setup):
    """Account with status other than syncing/active/sync_failed returns empty."""
    client, session_factory = sync_setup
    await _login(client)

    async with session_factory() as session:
        from app.models.user import User

        user = (await session.execute(select(User))).scalar_one()
        account = MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials="wa-session",
            status="disconnected",
        )
        session.add(account)
        await session.commit()
        account_id = account.id

    resp = await client.get(f"/accounts/{account_id}/sync-status")

    assert resp.status_code == 200
    assert resp.text.strip() == ""


@pytest.mark.asyncio
async def test_delete_allowed_while_syncing(sync_setup):
    """Can delete account even while status=syncing."""
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

    resp = await client.post(f"/accounts/{account_id}/delete")

    assert resp.status_code == 200  # followed redirect to /accounts

    # Account should be deleted
    async with session_factory() as session:
        result = await session.execute(
            select(MessengerAccount).where(MessengerAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        assert account is None


@pytest.mark.asyncio
async def test_sync_groups_blocked_while_syncing(sync_setup):
    """Cannot manually sync groups while account status=syncing."""
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

    resp = await client.post(f"/accounts/{account_id}/sync-groups")

    assert resp.status_code == 200  # followed redirect to /groups

    # No groups should have been created
    async with session_factory() as session:
        result = await session.execute(
            select(Group).where(Group.account_id == account_id)
        )
        groups = result.scalars().all()
        assert len(groups) == 0

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.user import User


@pytest.mark.asyncio
async def test_bulk_deactivate_and_delete():
    """Bulk deactivate and delete groups via /groups/bulk."""
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
        # Register and login to get cookie-based session
        await client.post(
            "/register",
            data={
                "email": "bulk@test.com",
                "password": "pass123",
                "name": "Bulk User",
            },
        )

        # Prepare data in DB
        async with session_factory() as session:
            user = (await session.execute(select(User))).scalar_one()
            account = MessengerAccount(
                user_id=user.id,
                type="tg_user",
                credentials="token",
                status="active",
            )
            session.add(account)
            await session.flush()

            # Two active groups and one already inactive
            g1 = Group(
                user_id=user.id,
                account_id=account.id,
                messenger_type="tg_user",
                group_external_id="ext-1",
                name="G1",
                is_active=True,
            )
            g2 = Group(
                user_id=user.id,
                account_id=account.id,
                messenger_type="tg_user",
                group_external_id="ext-2",
                name="G2",
                is_active=True,
            )
            g3 = Group(
                user_id=user.id,
                account_id=account.id,
                messenger_type="tg_user",
                group_external_id="ext-3",
                name="G3",
                is_active=False,
            )
            session.add_all([g1, g2, g3])
            await session.commit()
            g1_id, g2_id, g3_id = g1.id, g2.id, g3.id

        # Deactivate selected groups (including one already inactive)
        resp = await client.post(
            "/groups/bulk",
            data={"action": "deactivate", "group_ids": [str(g1_id), str(g3_id)]},
        )
        assert resp.status_code == 200  # followed redirect to /groups

        async with session_factory() as session:
            result = await session.execute(
                select(Group).where(Group.id.in_([g1_id, g2_id, g3_id]))
            )
            groups = {g.id: g for g in result.scalars().all()}
            assert groups[g1_id].is_active is False
            assert groups[g2_id].is_active is True
            assert groups[g3_id].is_active is False

        # Delete selected groups
        resp = await client.post(
            "/groups/bulk",
            data={"action": "delete", "group_ids": [str(g1_id), str(g2_id)]},
        )
        assert resp.status_code == 200  # followed redirect to /groups

        async with session_factory() as session:
            result = await session.execute(
                select(Group).where(Group.id.in_([g1_id, g2_id, g3_id]))
            )
            remaining = {g.id for g in result.scalars().all()}
            assert remaining == {g3_id}

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


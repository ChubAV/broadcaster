import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timezone, timedelta
from app.database import Base
from app.main import create_app
from app.dependencies import get_db, get_settings
from app.config import Settings
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.worker.tasks import check_schedules_async
from sqlalchemy import select


@pytest_asyncio.fixture
async def e2e_setup():
    """Full setup: app + db + client."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
    )

    app = create_app()

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_full_flow(e2e_setup):
    client, session_factory = e2e_setup

    # 1. Register
    resp = await client.post("/api/auth/register", json={
        "email": "seller@test.com", "password": "pass123", "name": "Seller"
    })
    assert resp.status_code == 201

    # 2. Login
    resp = await client.post("/api/auth/login", json={
        "email": "seller@test.com", "password": "pass123"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create ad
    resp = await client.post("/api/ads", headers=headers, json={
        "title": "iPhone 15 Pro", "text": "Like new, selling cheap!", "images": []
    })
    assert resp.status_code == 201
    ad_id = resp.json()["id"]

    # 4. Connect messenger account
    resp = await client.post("/api/accounts", headers=headers, json={
        "type": "tg_user", "credentials": "123456:ABC-token"
    })
    assert resp.status_code == 201
    account_id = resp.json()["id"]

    # 4b. Activate account (simulates successful bot connection)
    async with session_factory() as session:
        account = await session.get(MessengerAccount, account_id)
        account.status = "active"
        await session.commit()

    # 5. Add group
    resp = await client.post("/api/groups", headers=headers, json={
        "account_id": account_id, "messenger_type": "telegram",
        "group_external_id": "-100123456789", "name": "Sales Group"
    })
    assert resp.status_code == 201
    group_id = resp.json()["id"]

    # 6. Create schedule (runs now)
    resp = await client.post("/api/schedules", headers=headers, json={
        "ad_id": ad_id, "account_id": account_id, "group_ids": [group_id],
        "days_of_week": [0, 1, 2, 3, 4, 5, 6],
        "times_of_day": ["00:00"]
    })
    assert resp.status_code == 201
    schedule_id = resp.json()["id"]

    # 7. Manually trigger schedule check (simulates celery beat)
    async with session_factory() as session:
        # Set next_run_at to past so it triggers
        sched = await session.get(Schedule, schedule_id)
        sched.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await session.commit()

    # 8. Run check_schedules with mocked messenger
    mock_messenger = AsyncMock()
    mock_messenger.send_message = AsyncMock(return_value={"ok": True})

    mock_settings = AsyncMock()
    mock_settings.upload_dir = "uploads"

    async with session_factory() as session:
        with patch("app.worker.tasks.create_messenger", return_value=mock_messenger), \
             patch("app.worker.tasks.get_settings", return_value=mock_settings):
            await check_schedules_async(session)

    # 9. Verify send log was created
    async with session_factory() as session:
        result = await session.execute(select(SendLog))
        logs = result.scalars().all()
        assert len(logs) == 1
        assert logs[0].status == "ok"

    # 10. Check history endpoint
    resp = await client.get("/api/history", headers=headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 1
    assert history[0]["status"] == "ok"

    # 11. Check stats
    resp = await client.get("/api/history/stats", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_sent"] == 1
    assert stats["success_count"] == 1

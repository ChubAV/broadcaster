import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.subscription import Subscription
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.services.billing_service import get_plan_limits, get_user_plan, get_usage, check_limit, PLANS


def test_get_plan_limits():
    assert get_plan_limits("free")["max_ads"] == 3
    assert get_plan_limits("basic")["max_ads"] == 20
    assert get_plan_limits("pro")["max_ads"] == 100
    assert get_plan_limits("unknown")["max_ads"] == 3  # defaults to free


@pytest.mark.asyncio
async def test_get_user_plan_free(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    plan = await get_user_plan(db_session, user.id)
    assert plan == "free"


@pytest.mark.asyncio
async def test_get_user_plan_active(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    sub = Subscription(user_id=user.id, plan="basic", expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    db_session.add(sub)
    await db_session.commit()
    plan = await get_user_plan(db_session, user.id)
    assert plan == "basic"


@pytest.mark.asyncio
async def test_get_user_plan_expired(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    sub = Subscription(user_id=user.id, plan="pro", expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    db_session.add(sub)
    await db_session.commit()
    plan = await get_user_plan(db_session, user.id)
    assert plan == "free"


@pytest.mark.asyncio
async def test_check_limit_allowed(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    allowed, reason = await check_limit(db_session, user.id, "create_ad")
    assert allowed is True
    assert reason == ""


@pytest.mark.asyncio
async def test_check_limit_exceeded(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    # Create 3 ads (free plan limit)
    for i in range(3):
        db_session.add(Ad(user_id=user.id, title=f"Ad {i}", text="text", images=[]))
    await db_session.commit()
    allowed, reason = await check_limit(db_session, user.id, "create_ad")
    assert allowed is False
    assert "limit reached" in reason.lower()

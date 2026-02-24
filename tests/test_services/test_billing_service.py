import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.subscription import Subscription
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.services.billing_service import get_plan_limits, get_user_plan, get_usage, check_limit, set_user_plan, PLANS
from app.services.auth_service import hash_password


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


@pytest.mark.asyncio
async def test_check_send_limit_ignores_failed(db_session):
    """Failed sends should NOT count toward the daily send limit."""
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    ad = Ad(user_id=user.id, title="Ad", text="text", images=[])
    account = MessengerAccount(user_id=user.id, type="wa", status="active", credentials="{}")
    db_session.add_all([ad, account])
    await db_session.commit()

    group = Group(user_id=user.id, account_id=account.id, name="G", group_external_id="ext1", messenger_type="wa")
    db_session.add(group)
    await db_session.commit()

    from app.models.schedule import Schedule
    schedule = Schedule(
        ad_id=ad.id, account_id=account.id,
        group_ids=[group.id], days_of_week=[0, 1, 2, 3, 4, 5, 6], times_of_day=["12:00"],
    )
    db_session.add(schedule)
    await db_session.commit()

    # Add 10 failed send logs (should NOT block)
    for i in range(10):
        db_session.add(SendLog(
            schedule_id=schedule.id, ad_id=ad.id, group_id=group.id,
            status="fail", error_message="Chromium error",
        ))
    await db_session.commit()

    allowed, reason = await check_limit(db_session, user.id, "send")
    assert allowed is True

    # Now add 10 successful send logs (should block on free plan)
    for i in range(10):
        db_session.add(SendLog(
            schedule_id=schedule.id, ad_id=ad.id, group_id=group.id,
            status="ok",
        ))
    await db_session.commit()

    allowed, reason = await check_limit(db_session, user.id, "send")
    assert allowed is False
    assert "send limit" in reason.lower()


@pytest.mark.asyncio
async def test_set_user_plan_creates_subscription(db_session):
    user = User(email="u@test.com", password_hash=hash_password("p"), name="U")
    db_session.add(user)
    await db_session.commit()

    expires = datetime.now(timezone.utc) + timedelta(days=30)
    await set_user_plan(db_session, user.id, "pro", expires)

    plan = await get_user_plan(db_session, user.id)
    assert plan == "pro"


@pytest.mark.asyncio
async def test_set_user_plan_deactivates_old(db_session):
    user = User(email="u@test.com", password_hash=hash_password("p"), name="U")
    db_session.add(user)
    await db_session.commit()

    expires = datetime.now(timezone.utc) + timedelta(days=30)
    await set_user_plan(db_session, user.id, "basic", expires)
    await set_user_plan(db_session, user.id, "pro", expires)

    plan = await get_user_plan(db_session, user.id)
    assert plan == "pro"

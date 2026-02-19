import pytest
from datetime import datetime, timezone

from app.models.user import User
from app.models.subscription import Subscription


@pytest.mark.asyncio
async def test_create_subscription(db_session):
    user = User(
        email="sub@example.com",
        password_hash="hashed",
        name="Sub User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires = datetime(2026, 12, 31, tzinfo=timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        plan="pro",
        expires_at=expires,
        is_active=True,
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)

    assert subscription.id is not None
    assert subscription.user_id == user.id
    assert subscription.plan == "pro"
    # SQLite strips timezone info; compare naive datetime values
    assert subscription.expires_at.replace(tzinfo=None) == expires.replace(tzinfo=None)
    assert subscription.is_active is True
    assert subscription.created_at is not None


@pytest.mark.asyncio
async def test_subscription_default_plan(db_session):
    user = User(
        email="free@example.com",
        password_hash="hashed",
        name="Free User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    subscription = Subscription(
        user_id=user.id,
        expires_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)

    assert subscription.plan == "free"
    assert subscription.is_active is True

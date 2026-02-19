import pytest
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(
        email="test@example.com",
        password_hash="hashed_password_123",
        name="Test User",
        timezone="America/New_York",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed_password_123"
    assert user.name == "Test User"
    assert user.timezone == "America/New_York"
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_default_timezone(db_session):
    user = User(
        email="default@example.com",
        password_hash="hashed",
        name="Default TZ User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.timezone == "UTC"


@pytest.mark.asyncio
async def test_user_email_unique(db_session):
    user1 = User(
        email="unique@example.com",
        password_hash="hash1",
        name="User 1",
    )
    db_session.add(user1)
    await db_session.commit()

    user2 = User(
        email="unique@example.com",
        password_hash="hash2",
        name="User 2",
    )
    db_session.add(user2)
    with pytest.raises(Exception):
        await db_session.commit()

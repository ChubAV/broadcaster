import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.database import Base
from app.models.user import User
from app.models.telegram_auth_session import TelegramAuthSession


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _create_user(session):
    user = User(email="test@test.com", password_hash="hash", name="Test")
    session.add(user)
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_create_telegram_auth_session(db_session):
    user = await _create_user(db_session)
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    auth_session = TelegramAuthSession(
        user_id=user.id,
        phone_number="+79001234567",
        status="pending",
        expires_at=expires,
    )
    db_session.add(auth_session)
    await db_session.commit()
    await db_session.refresh(auth_session)

    assert auth_session.id is not None
    assert auth_session.user_id == user.id
    assert auth_session.phone_number == "+79001234567"
    assert auth_session.status == "pending"
    assert auth_session.phone_code_hash is None
    assert auth_session.partial_session_string is None
    assert auth_session.error_message is None


@pytest.mark.asyncio
async def test_auth_session_status_transitions(db_session):
    user = await _create_user(db_session)
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    auth_session = TelegramAuthSession(
        user_id=user.id,
        phone_number="+79001234567",
        status="pending",
        expires_at=expires,
    )
    db_session.add(auth_session)
    await db_session.commit()

    # Transition to code_sent
    auth_session.status = "code_sent"
    auth_session.phone_code_hash = "abc123"
    await db_session.commit()
    await db_session.refresh(auth_session)
    assert auth_session.status == "code_sent"
    assert auth_session.phone_code_hash == "abc123"

    # Transition to needs_2fa
    auth_session.status = "needs_2fa"
    await db_session.commit()
    await db_session.refresh(auth_session)
    assert auth_session.status == "needs_2fa"

    # Transition to completed
    auth_session.status = "completed"
    await db_session.commit()
    await db_session.refresh(auth_session)
    assert auth_session.status == "completed"


@pytest.mark.asyncio
async def test_auth_session_error_state(db_session):
    user = await _create_user(db_session)
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    auth_session = TelegramAuthSession(
        user_id=user.id,
        phone_number="+79001234567",
        status="error",
        error_message="Phone number invalid",
        expires_at=expires,
    )
    db_session.add(auth_session)
    await db_session.commit()
    await db_session.refresh(auth_session)

    assert auth_session.status == "error"
    assert auth_session.error_message == "Phone number invalid"


@pytest.mark.asyncio
async def test_auth_session_has_user_fk(db_session):
    user = await _create_user(db_session)
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    auth_session = TelegramAuthSession(
        user_id=user.id,
        phone_number="+79001234567",
        status="pending",
        expires_at=expires,
    )
    db_session.add(auth_session)
    await db_session.commit()
    await db_session.refresh(auth_session)

    assert auth_session.user_id == user.id

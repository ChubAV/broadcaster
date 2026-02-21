import pytest
from app.models.user import User
from app.models.messenger_account import MessengerAccount


@pytest.mark.asyncio
async def test_create_messenger_account(db_session):
    user = User(
        email="messenger@example.com",
        password_hash="hashed",
        name="Messenger User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials='{"token": "abc123"}',
        session_data=None,
        status="connected",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    assert account.id is not None
    assert account.user_id == user.id
    assert account.type == "tg_user"
    assert account.credentials == '{"token": "abc123"}'
    assert account.session_data is None
    assert account.status == "connected"
    assert account.created_at is not None


@pytest.mark.asyncio
async def test_messenger_account_default_status(db_session):
    user = User(
        email="default_status@example.com",
        password_hash="hashed",
        name="Default Status User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="wa",
        credentials='{"phone": "+1234567890"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    assert account.status == "disconnected"


@pytest.mark.asyncio
async def test_messenger_account_with_session_data(db_session):
    user = User(
        email="session@example.com",
        password_hash="hashed",
        name="Session User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials='{"api_id": "123"}',
        session_data="session_string_data_here",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    assert account.session_data == "session_string_data_here"

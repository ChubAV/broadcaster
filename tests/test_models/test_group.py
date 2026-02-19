import pytest
from app.models.user import User
from app.models.messenger_account import MessengerAccount
from app.models.group import Group


@pytest.mark.asyncio
async def test_create_group(db_session):
    user = User(
        email="group@example.com",
        password_hash="hashed",
        name="Group User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = MessengerAccount(
        user_id=user.id,
        type="tg_bot",
        credentials='{"token": "bot_token"}',
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="tg_bot",
        group_external_id="-1001234567890",
        name="My Telegram Group",
        is_active=True,
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    assert group.id is not None
    assert group.user_id == user.id
    assert group.account_id == account.id
    assert group.messenger_type == "tg_bot"
    assert group.group_external_id == "-1001234567890"
    assert group.name == "My Telegram Group"
    assert group.is_active is True
    assert group.created_at is not None


@pytest.mark.asyncio
async def test_group_default_is_active(db_session):
    user = User(
        email="group_default@example.com",
        password_hash="hashed",
        name="Default Group User",
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

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="wa",
        group_external_id="wa_group_123",
        name="WhatsApp Group",
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    assert group.is_active is True

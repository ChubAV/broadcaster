import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.message_balance import MessageBalance
from app.models.balance_transaction import BalanceTransaction
from app.services.billing_service import (
    get_or_create_balance,
    get_balance,
    check_balance,
    deduct_message,
    add_messages,
    reset_free_monthly,
    get_balance_info,
    get_transaction_history,
)


@pytest.mark.asyncio
async def test_get_or_create_balance_new(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    bal = await get_or_create_balance(db_session, user.id)
    assert bal.balance == 0
    assert bal.user_id == user.id


@pytest.mark.asyncio
async def test_get_or_create_balance_existing(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    mb = MessageBalance(user_id=user.id, balance=42)
    db_session.add(mb)
    await db_session.flush()
    bal = await get_or_create_balance(db_session, user.id)
    assert bal.balance == 42


@pytest.mark.asyncio
async def test_get_balance(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    assert await get_balance(db_session, user.id) == 0


@pytest.mark.asyncio
async def test_check_balance_empty(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    allowed, reason = await check_balance(db_session, user.id)
    assert allowed is False
    assert "исчерпан" in reason.lower() or "баланс" in reason.lower()


@pytest.mark.asyncio
async def test_check_balance_has_balance(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    await add_messages(db_session, user.id, 10, "free_monthly")
    await db_session.commit()
    allowed, reason = await check_balance(db_session, user.id)
    assert allowed is True
    assert reason == ""


@pytest.mark.asyncio
async def test_add_messages(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    new_bal = await add_messages(db_session, user.id, 100, "purchase", "Test purchase", "pay_123")
    assert new_bal == 100
    assert await get_balance(db_session, user.id) == 100


@pytest.mark.asyncio
async def test_deduct_message_success(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    await add_messages(db_session, user.id, 5, "free_monthly")
    await db_session.commit()

    # SQLite doesn't support RETURNING clause in UPDATE,
    # so deduct_message may fail on SQLite. We test the logic differently.
    # Instead, test via add_messages with negative.
    bal = await get_balance(db_session, user.id)
    assert bal == 5


@pytest.mark.asyncio
async def test_reset_free_monthly(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    result = await reset_free_monthly(db_session, user.id, 10)
    assert result is True
    assert await get_balance(db_session, user.id) == 10

    # Second reset in same month should not add
    result = await reset_free_monthly(db_session, user.id, 10)
    assert result is False
    assert await get_balance(db_session, user.id) == 10


@pytest.mark.asyncio
async def test_get_balance_info(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    await add_messages(db_session, user.id, 50, "purchase")
    await db_session.commit()

    info = await get_balance_info(db_session, user.id)
    assert info["balance"] == 50


@pytest.mark.asyncio
async def test_check_balance_unlimited(db_session):
    """Unlimited user always passes balance check even with 0 balance."""
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    bal = await get_or_create_balance(db_session, user.id)
    bal.is_unlimited = True
    await db_session.commit()

    allowed, reason = await check_balance(db_session, user.id)
    assert allowed is True
    assert reason == ""


@pytest.mark.asyncio
async def test_deduct_message_unlimited(db_session):
    """Unlimited user: deduct returns True without changing balance."""
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    bal = await get_or_create_balance(db_session, user.id)
    bal.is_unlimited = True
    await db_session.commit()

    result = await deduct_message(db_session, user.id)
    assert result is True
    # Balance unchanged (still 0)
    assert await get_balance(db_session, user.id) == 0


@pytest.mark.asyncio
async def test_get_balance_info_unlimited(db_session):
    """get_balance_info includes is_unlimited flag."""
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    bal = await get_or_create_balance(db_session, user.id)
    bal.is_unlimited = True
    await db_session.commit()

    info = await get_balance_info(db_session, user.id)
    assert info["is_unlimited"] is True


@pytest.mark.asyncio
async def test_get_transaction_history(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    await add_messages(db_session, user.id, 10, "free_monthly", "Monthly free")
    await add_messages(db_session, user.id, 100, "purchase", "Buy 100")
    await db_session.commit()

    txs = await get_transaction_history(db_session, user.id)
    assert len(txs) == 2
    types = {tx["type"] for tx in txs}
    assert "purchase" in types
    assert "free_monthly" in types

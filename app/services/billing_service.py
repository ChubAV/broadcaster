from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message_balance import MessageBalance
from app.models.balance_transaction import BalanceTransaction

logger = structlog.get_logger()


async def get_or_create_balance(db: AsyncSession, user_id: int) -> MessageBalance:
    result = await db.execute(
        select(MessageBalance).where(MessageBalance.user_id == user_id)
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = MessageBalance(user_id=user_id, balance=0)
        db.add(balance)
        await db.flush()
    return balance


async def get_balance(db: AsyncSession, user_id: int) -> int:
    bal = await get_or_create_balance(db, user_id)
    return bal.balance


async def check_balance(db: AsyncSession, user_id: int) -> tuple[bool, str]:
    bal = await get_or_create_balance(db, user_id)
    if bal.is_unlimited:
        return True, ""
    if bal.balance <= 0:
        return False, "Баланс сообщений исчерпан. Пополните баланс для продолжения отправки."
    return True, ""


async def deduct_message(db: AsyncSession, user_id: int) -> bool:
    """Atomically deduct 1 message. Returns True if deducted, False if insufficient."""
    bal = await get_or_create_balance(db, user_id)
    if bal.is_unlimited:
        return True
    result = await db.execute(
        update(MessageBalance)
        .where(MessageBalance.user_id == user_id, MessageBalance.balance > 0)
        .values(balance=MessageBalance.balance - 1)
        .returning(MessageBalance.balance)
    )
    row = result.first()
    if row is None:
        return False

    new_balance = row[0]
    tx = BalanceTransaction(
        user_id=user_id,
        amount=-1,
        balance_after=new_balance,
        type="send_deduction",
    )
    db.add(tx)
    return True


async def add_messages(
    db: AsyncSession,
    user_id: int,
    amount: int,
    type: str,
    description: str | None = None,
    payment_id: str | None = None,
) -> int:
    """Add messages to balance. Returns new balance."""
    bal = await get_or_create_balance(db, user_id)
    bal.balance += amount
    await db.flush()

    tx = BalanceTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=bal.balance,
        type=type,
        description=description,
        payment_id=payment_id,
    )
    db.add(tx)
    await db.flush()
    return bal.balance


async def reset_free_monthly(db: AsyncSession, user_id: int, free_limit: int) -> bool:
    """Reset free monthly messages for a single user. Returns True if reset."""
    bal = await get_or_create_balance(db, user_id)
    now = datetime.now(timezone.utc)

    if bal.free_balance_reset_at is not None:
        reset_at = bal.free_balance_reset_at
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if reset_at.month == now.month and reset_at.year == now.year:
            return False

    bal.balance += free_limit
    bal.free_balance_reset_at = now
    await db.flush()

    tx = BalanceTransaction(
        user_id=user_id,
        amount=free_limit,
        balance_after=bal.balance,
        type="free_monthly",
        description=f"Ежемесячное начисление {free_limit} бесплатных сообщений",
    )
    db.add(tx)
    return True


async def reset_all_free_monthly(db: AsyncSession, free_limit: int) -> int:
    """Reset free monthly for all users. Returns count of users reset."""
    now = datetime.now(timezone.utc)
    from app.models.user import User

    result = await db.execute(select(User.id))
    user_ids = [row[0] for row in result.all()]

    count = 0
    for uid in user_ids:
        if await reset_free_monthly(db, uid, free_limit):
            count += 1
    return count


async def get_balance_info(db: AsyncSession, user_id: int) -> dict:
    bal = await get_or_create_balance(db, user_id)
    return {
        "balance": bal.balance,
        "is_unlimited": bal.is_unlimited,
        "free_balance_reset_at": bal.free_balance_reset_at.isoformat() if bal.free_balance_reset_at else None,
    }


async def get_transaction_history(
    db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0
) -> list[dict]:
    result = await db.execute(
        select(BalanceTransaction)
        .where(BalanceTransaction.user_id == user_id)
        .order_by(BalanceTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    txs = result.scalars().all()
    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "type": tx.type,
            "description": tx.description,
            "payment_id": tx.payment_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
        for tx in txs
    ]

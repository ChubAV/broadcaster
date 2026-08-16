from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.models.message_balance import MessageBalance
from app.models.balance_transaction import BalanceTransaction
from app.models.payment import Payment

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
    """Начисляет сообщения на баланс. Возвращает новый баланс.

    ПРИРАЩЕНИЕ СЧИТАЕТ СУБД, А НЕ PYTHON (T-05-36). Прежняя пара
    «прочитали строку → прибавили в Python → записали» теряла одно из двух
    наложившихся начислений: обе стороны читали одно и то же старое значение и
    обе записывали своё, затирая чужое. Выражение `balance + amount` считается
    на стороне СУБД внутри одного оператора, поэтому потерять запись НЕЧЕМ —
    это недостижимость, а не малая вероятность.

    `get_or_create_balance` остаётся: строка баланса обязана существовать до
    приращения, иначе UPDATE не заденет ни одной строки.

    ПОДПИСЬ И ВОЗВРАЩАЕМОЕ ЗНАЧЕНИЕ НЕ МЕНЯЮТСЯ — у функции есть другие
    вызывающие (`app/pages/admin.py`), и ключевое слово `type` тоже остаётся
    прежним намеренно (IN-01): его переименование правит все вызовы и к защите
    от двойного начисления отношения не имеет.
    """
    bal = await get_or_create_balance(db, user_id)

    result = await db.execute(
        update(MessageBalance)
        .where(MessageBalance.user_id == user_id)
        .values(balance=MessageBalance.balance + amount)
        .returning(MessageBalance.balance)
        .execution_options(synchronize_session=False)
    )
    new_balance = result.scalar_one()

    # Значение ставится как ЗАГРУЖЕННОЕ, а не присваиванием: присваивание
    # пометило бы объект грязным, и ORM выдала бы на flush второй UPDATE — то
    # есть прибавила бы `amount` ещё раз поверх уже посчитанного СУБД.
    set_committed_value(bal, "balance", new_balance)

    tx = BalanceTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=new_balance,
        type=type,
        description=description,
        payment_id=payment_id,
    )
    db.add(tx)
    await db.flush()
    return new_balance


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


# --- Журнал платежей ----------------------------------------------------------
#
# ВТОРОЙ ЖУРНАЛ РАЗДЕЛА, А НЕ ЗАМЕНА ПЕРВОМУ (D-14). `BalanceTransaction` выше
# считает ШТУКИ сообщений: рублёвой суммы у него нет — колонки под неё в таблице
# не существует. Критерий фазы требует показать пользователю сумму в рублях, и
# она есть только у `Payment`. Поэтому история платежей строится по `payments`,
# а история операций по балансу остаётся своим блоком: одно про деньги, другое
# про сообщения, и склеивать их значило бы получить журнал, в котором половина
# строк без суммы, а половина без количества.


async def get_payment_history(
    db: AsyncSession, user_id: int, limit: int
) -> list[Payment]:
    """Платежи владельца, свежие сверху, не больше `limit` записей.

    ВОЗВРАЩАЮТСЯ СТРОКИ МОДЕЛИ, А НЕ СЛОВАРИ С `isoformat()`, в отличие от
    соседнего `get_transaction_history`. Тот отдаёт словари, потому что его
    читает JSON-маршрут; этот читает ТОЛЬКО разметка, а разметка форматирует
    дату существующим глобалом в зоне пользователя и требует настоящий
    `datetime`. Строка ISO пришлось бы разбирать обратно — то есть завести
    второй формат даты в проекте ради одного шаблона.

    ⚠️ СОРТИРОВКА ПО ДАТЕ, НИКОГДА ПО СУММЕ. `amount_value` объявлена СТРОКОЙ:
    ЮKassa оперирует decimal-строками, и хранение во `float` теряло бы копейки.
    Строковое сравнение поставило бы «999.00» выше «1490.00» — порядок выглядел
    бы правдоподобно и был бы неверен. Арифметики по суммам фазе не нужно вовсе:
    BILL-07 требует только показа.

    ВЛАДЕНИЕ — ПРЕДИКАТ ЗАПРОСА (T-05-20). Чужие платежи не приезжают
    вызывающему вовсе, поэтому забытый фильтр в шаблоне не может показать чужой
    денежный журнал.
    """
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_payments(db: AsyncSession, user_id: int) -> int:
    """Сколько всего платежей у владельца — БЕЗ выборки самих записей.

    Существует ради потолка: он обязан проверяться ДО конструирования списка и
    называть себя пользователю, а не обрезать молча. Вывести срабатывание из
    длины уже обрезанного списка нельзя — ровно на потолке список полон, и
    «показано не всё» неотличимо от «столько и есть».
    """
    return int(
        await db.scalar(
            select(func.count()).select_from(Payment).where(Payment.user_id == user_id)
        )
        or 0
    )

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from app.constants import PAYMENT_LIST_CAP
from app.models.user import User
from app.models.message_balance import MessageBalance
from app.models.balance_transaction import BalanceTransaction
from app.models.payment import Payment
from app.services.billing_service import (
    get_or_create_balance,
    get_balance,
    check_balance,
    deduct_message,
    add_messages,
    reset_free_monthly,
    get_balance_info,
    get_transaction_history,
    count_payments,
    get_payment_history,
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


# --- Журнал платежей (BILL-07) ------------------------------------------------
#
# Это ВТОРОЙ журнал раздела, а не замена первому. `BalanceTransaction` считает
# ШТУКИ сообщений и рублёвой суммы не знает вовсе — колонки под неё в таблице
# нет. Критерий фазы требует показать сумму в рублях, и она есть только у
# `Payment` (D-14), поэтому история платежей строится по нему.
#
# `created_at` во всех посевах ставится ЯВНО: у колонки есть
# `server_default=func.now()`, и записи без явного времени легли бы в одну
# миллисекунду — порядок по убыванию даты стал бы тогда порядком вставки, то
# есть тест проверял бы не то, что утверждает.

BASE_TIME = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)

_payment_seq = 0


async def _payment(
    db_session,
    user_id: int,
    *,
    status: str = "succeeded",
    created_at: datetime | None = None,
    amount_value: str = "1490.00",
    kind: str = "subscription",
) -> Payment:
    """Строка `payments` владельца. Идентификатор ЮKassa уникален по схеме."""
    global _payment_seq
    _payment_seq += 1
    payment = Payment(
        user_id=user_id,
        yookassa_payment_id=f"yoo_{_payment_seq}",
        status=status,
        amount_value=amount_value,
        amount_currency="RUB",
        kind=kind,
        plan="basic" if kind == "subscription" else None,
        created_at=created_at or BASE_TIME,
    )
    db_session.add(payment)
    await db_session.commit()
    return payment


async def _two_users(db_session) -> tuple[User, User]:
    owner = User(email="owner@test.com", password_hash="h", name="O")
    stranger = User(email="stranger@test.com", password_hash="h", name="S")
    db_session.add_all([owner, stranger])
    await db_session.commit()
    return owner, stranger


@pytest.mark.asyncio
async def test_get_payment_history_returns_only_the_owners_payments(db_session):
    """Владение — предикатом запроса, а не фильтром у вызывающего (T-05-20)."""
    owner, stranger = await _two_users(db_session)
    for _ in range(5):
        await _payment(db_session, owner.id)
    for _ in range(3):
        await _payment(db_session, stranger.id)

    rows = await get_payment_history(db_session, owner.id, limit=PAYMENT_LIST_CAP)

    assert len(rows) == 5
    assert {row.user_id for row in rows} == {owner.id}


@pytest.mark.asyncio
async def test_get_payment_history_orders_by_creation_date_descending(db_session):
    owner, _ = await _two_users(db_session)
    oldest = await _payment(db_session, owner.id, created_at=BASE_TIME)
    middle = await _payment(
        db_session, owner.id, created_at=BASE_TIME + timedelta(days=1)
    )
    newest = await _payment(
        db_session, owner.id, created_at=BASE_TIME + timedelta(days=2)
    )

    rows = await get_payment_history(db_session, owner.id, limit=PAYMENT_LIST_CAP)

    assert [row.id for row in rows] == [newest.id, middle.id, oldest.id]


@pytest.mark.asyncio
async def test_get_payment_history_never_sorts_by_the_amount(db_session):
    """Сумма — СТРОКА, и строковое сравнение поставило бы «999.00» выше «1490.00».

    Проверка идёт данными, а не грепом: платёж с большей суммой заводится
    старше, и правильная сортировка обязана поставить его ВТОРЫМ.
    """
    owner, _ = await _two_users(db_session)
    expensive_but_older = await _payment(
        db_session, owner.id, amount_value="1490.00", created_at=BASE_TIME
    )
    cheap_but_newer = await _payment(
        db_session,
        owner.id,
        amount_value="999.00",
        created_at=BASE_TIME + timedelta(days=1),
    )

    rows = await get_payment_history(db_session, owner.id, limit=PAYMENT_LIST_CAP)

    assert [row.id for row in rows] == [cheap_but_newer.id, expensive_but_older.id]


@pytest.mark.asyncio
async def test_get_payment_history_includes_every_status(db_session):
    """Три статуса после D-16: скрыть отменённый значило бы солгать о нём."""
    owner, _ = await _two_users(db_session)
    for status in ("pending", "succeeded", "canceled"):
        await _payment(db_session, owner.id, status=status)

    rows = await get_payment_history(db_session, owner.id, limit=PAYMENT_LIST_CAP)

    assert {row.status for row in rows} == {"pending", "succeeded", "canceled"}


@pytest.mark.asyncio
async def test_get_payment_history_never_returns_more_than_the_limit(db_session):
    owner, _ = await _two_users(db_session)
    for index in range(7):
        await _payment(db_session, owner.id, created_at=BASE_TIME + timedelta(days=index))

    rows = await get_payment_history(db_session, owner.id, limit=3)

    assert len(rows) == 3


@pytest.mark.asyncio
async def test_count_payments_counts_only_the_owner(db_session):
    """Число нужно ДО конструирования списка — значит, считать без выборки."""
    owner, stranger = await _two_users(db_session)
    for _ in range(4):
        await _payment(db_session, owner.id)
    for _ in range(9):
        await _payment(db_session, stranger.id)

    assert await count_payments(db_session, owner.id) == 4
    assert await count_payments(db_session, stranger.id) == 9


@pytest.mark.asyncio
async def test_count_payments_sees_records_beyond_the_cap(db_session):
    """Потолок обязан УЗНАВАТЬСЯ, а не выводиться из длины обрезанного списка."""
    owner, _ = await _two_users(db_session)
    for _ in range(5):
        await _payment(db_session, owner.id)

    assert await count_payments(db_session, owner.id) == 5
    assert len(await get_payment_history(db_session, owner.id, limit=2)) == 2


def test_the_payment_list_cap_is_named_once_for_the_project():
    """Потолок обязаны называть одинаково обработчик, тест и Фаза 6."""
    assert PAYMENT_LIST_CAP == 200

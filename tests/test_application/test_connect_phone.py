"""Помощник захвата номера при подключении: порядок источников и устойчивость (Фаза 19, план 19-05).

Файл — спецификация `app/application/accounts/connect_phone.py`. Помощник пишет
сначала номер, который сообщил сам мессенджер, а запасной (введённый человеком в
форме MAX, план 19-07) — ТОЛЬКО когда первый — мусор (D-10). Оба пути идут через
единственного писателя Фазы 16, признак «указан вручную» не ставится ни в одном
из них. Транзакцией владеет вызывающий: помощник открывает сейвпоинт и не
коммитит, а сбой внутри него обязан оставить внешнюю транзакцию живой (D-05).

Итог строки читается свежим `select` КОЛОНОК: писатель идёт мимо identity map.
Номер сеется только через `tests/account_label_support.py::seed_account`.
"""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts import connect_phone as connect_phone_module
from app.application.accounts.connect_phone import capture_connect_phone
from app.application.accounts.phone import PhoneWrite
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from tests.account_label_support import seed_account

REPORTED = "79991234567"
REPORTED_E164 = "+79991234567"
ENTERED = "+79990001122"


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    row = User(email="connect-phone@t.com", password_hash="h", name="T")
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _columns(db: AsyncSession, account_id: int) -> tuple[str | None, bool]:
    result = await db.execute(
        select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
            MessengerAccount.id == account_id
        )
    )
    return tuple(result.one())


@pytest.mark.asyncio
async def test_the_number_the_messenger_reported_wins_over_the_entered_one(
    db_session: AsyncSession, user: User
):
    """D-10: ввёл A, отсканировал B — пишется B; запасной не пробуется."""
    account_id = await seed_account(db_session, user.id, "max", status="connecting")

    outcome = await capture_connect_phone(db_session, account_id, REPORTED, ENTERED)
    await db_session.commit()

    assert outcome is PhoneWrite.WRITTEN
    assert await _columns(db_session, account_id) == (REPORTED_E164, False)


@pytest.mark.asyncio
async def test_the_entered_number_is_the_fallback_when_nothing_was_reported(
    db_session: AsyncSession, user: User
):
    account_id = await seed_account(db_session, user.id, "max", status="connecting")

    outcome = await capture_connect_phone(db_session, account_id, None, ENTERED)
    await db_session.commit()

    assert outcome is PhoneWrite.WRITTEN
    assert await _columns(db_session, account_id) == (ENTERED, False), (
        "запасной номер пишется автоисточником, признак «вручную» не ставится"
    )


@pytest.mark.asyncio
async def test_two_unusable_sources_leave_the_number_unknown(db_session: AsyncSession, user: User):
    account_id = await seed_account(db_session, user.id, "max", status="connecting")

    outcome = await capture_connect_phone(db_session, account_id, None, "not a number")
    await db_session.commit()

    assert outcome is PhoneWrite.UNPARSEABLE
    assert await _columns(db_session, account_id) == (None, False)


@pytest.mark.asyncio
async def test_a_known_number_is_kept_and_the_fallback_is_not_tried(
    db_session: AsyncSession, user: User, monkeypatch
):
    """T-19-16: у строки уже есть номер — сообщённый другой не пишется, запасной не пробуется."""
    account_id = await seed_account(
        db_session, user.id, "max", phone="79995554433", status="connecting"
    )
    writer = AsyncMock(wraps=connect_phone_module.fill_reported_phone)
    monkeypatch.setattr(connect_phone_module, "fill_reported_phone", writer)

    outcome = await capture_connect_phone(db_session, account_id, REPORTED, ENTERED)
    await db_session.commit()

    assert outcome is PhoneWrite.KEPT
    assert writer.await_count == 1, "запасной номер пробовался после KEPT"
    assert await _columns(db_session, account_id) == ("+79995554433", False)


@pytest.mark.asyncio
async def test_a_missing_account_is_reported_and_the_fallback_is_not_tried(
    db_session: AsyncSession, user: User, monkeypatch
):
    writer = AsyncMock(wraps=connect_phone_module.fill_reported_phone)
    monkeypatch.setattr(connect_phone_module, "fill_reported_phone", writer)

    outcome = await capture_connect_phone(db_session, 999_999, REPORTED, ENTERED)

    assert outcome is PhoneWrite.MISSING
    assert writer.await_count == 1, "запасной номер пробовался после MISSING"


@pytest.mark.asyncio
async def test_a_failing_writer_is_swallowed_and_the_outer_transaction_survives(
    db_session: AsyncSession, user: User, monkeypatch
):
    """D-05: писатель бросает — помощник отвечает `None`, внешняя транзакция и чужая правка живы."""
    account_id = await seed_account(db_session, user.id, "max", status="connecting")
    monkeypatch.setattr(
        "app.application.accounts.connect_phone.fill_reported_phone",
        AsyncMock(side_effect=RuntimeError("boom")),
    )
    row = await db_session.get(MessengerAccount, account_id)
    row.status = "syncing"  # посторонняя правка той же сессии, ещё не закоммиченная

    outcome = await capture_connect_phone(db_session, account_id, REPORTED, ENTERED)
    await db_session.commit()

    assert outcome is None
    db_session.expire_all()
    stored = await db_session.get(MessengerAccount, account_id)
    assert stored.status == "syncing", "сбой захвата откатил чужую правку внешней транзакции"
    assert stored.phone is None

"""Загрузчик строк аккаунтов пользователя (Фаза 17, D-14, D-18, T-17-02, T-17-03).

Признак двойника обязан совпадать на всех экранах одного пользователя, поэтому
карта «аккаунты пользователя» читается ПО ПОЛЬЗОВАТЕЛЮ, а не по порции
идентификаторов. Здесь закреплено: границу владельца держит запрос, строки
всех статусов входят в счёт, проекция — четыре колонки (без `credentials` и
строки сессии), а читает загрузчик одной инструкцией.
"""

from __future__ import annotations

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.labels import load_account_rows
from app.models.user import User
from app.services.account_label import AccountRow, build_labels
from tests.account_label_support import seed_account

STATUSES = ["active", "syncing", "connecting", "disconnected", "sync_failed"]


async def _user(session: AsyncSession, email: str) -> int:
    user = User(email=email, password_hash="x", name=email)
    session.add(user)
    await session.commit()
    return user.id


async def _loaded(session: AsyncSession, user_id: int) -> tuple[list[AccountRow], list[str]]:
    """Строки загрузчика и тексты инструкций, которые он исполнил."""
    statements: list[str] = []
    sync_engine = session.bind.sync_engine

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(sync_engine, "before_cursor_execute", _record)
    try:
        rows = await load_account_rows(session, user_id)
    finally:
        event.remove(sync_engine, "before_cursor_execute", _record)
    return rows, statements


async def _seed_two_users(session: AsyncSession) -> tuple[int, int, list[int], list[int]]:
    owner = await _user(session, "rows-owner@test.com")
    stranger = await _user(session, "rows-stranger@test.com")
    mine = [
        await seed_account(session, owner, "tg_user", phone="+79991234567", status=STATUSES[0]),
        await seed_account(session, owner, "wa", status=STATUSES[1]),
        await seed_account(session, owner, "wa", status=STATUSES[2]),
        await seed_account(session, owner, "max", stored_as_is="abc", status=STATUSES[3]),
        await seed_account(session, owner, "tg_user", status=STATUSES[4]),
    ]
    theirs = [
        await seed_account(session, stranger, "tg_user", phone="+79991234567"),
        await seed_account(session, stranger, "wa"),
    ]
    return owner, stranger, mine, theirs


@pytest.mark.asyncio
async def test_rows_cover_every_account_of_the_user_in_one_statement(db_session: AsyncSession):
    """Живой аккаунт — строка, которая существует: все пять статусов входят, запрос один."""
    owner, _stranger, mine, _theirs = await _seed_two_users(db_session)

    rows, statements = await _loaded(db_session, owner)

    assert len(rows) == 5, "загрузчик должен отдать все пять аккаунтов пользователя"
    assert {row.id for row in rows} == set(mine)
    by_id = {row.id: row for row in rows}
    assert by_id[mine[0]] == AccountRow(mine[0], "tg_user", "+79991234567", False)
    assert by_id[mine[1]].phone is None
    assert by_id[mine[3]] == AccountRow(mine[3], "max", "abc", False), "неразбираемый номер приезжает как есть"
    selects = [s for s in statements if s.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 1, f"загрузчик сделал {len(selects)} запросов, ожидался один"


@pytest.mark.asyncio
async def test_rows_never_carry_another_users_account(db_session: AsyncSession):
    """T-17-02: условие владельца стоит в запросе, чужие аккаунты не читаются."""
    owner, stranger, mine, theirs = await _seed_two_users(db_session)

    own_rows, _ = await _loaded(db_session, owner)
    strangers_rows, _ = await _loaded(db_session, stranger)

    assert {row.id for row in own_rows} == set(mine), "свои аккаунты не вернулись"
    assert not ({row.id for row in own_rows} & set(theirs)), "в ответе чужой аккаунт"
    assert {row.id for row in strangers_rows} == set(theirs)


@pytest.mark.asyncio
async def test_the_statement_reads_only_four_columns(db_session: AsyncSession):
    """T-17-03: ни `credentials`, ни строка сессии в памяти страницы не поднимаются."""
    owner, _stranger, _mine, _theirs = await _seed_two_users(db_session)

    _rows, statements = await _loaded(db_session, owner)

    assert len(statements) == 1, "ожидалась ровно одна инструкция"
    text = statements[0]
    assert "credentials" not in text and "session_data" not in text, text
    for column in ("id", "type", "phone", "phone_is_manual"):
        assert f"messenger_accounts.{column}" in text, f"в проекции нет колонки {column}"


@pytest.mark.asyncio
async def test_twins_come_from_the_whole_set(db_session: AsyncSession):
    """D-14: два WhatsApp без номера в разных статусах — оба двойники по ВСЕМ строкам."""
    owner, _stranger, mine, _theirs = await _seed_two_users(db_session)

    rows, _ = await _loaded(db_session, owner)
    labels = build_labels(rows)

    assert labels[mine[1]].twin and labels[mine[2]].twin, "оба WhatsApp без номера — двойники"
    assert not labels[mine[0]].twin, "Telegram с номером двойником не является"
    assert not labels[mine[3]].twin, "MAX с неразбираемым номером двойником не является"


@pytest.mark.asyncio
async def test_rows_carry_the_manual_flag(db_session: AsyncSession):
    """D-10: четвёртая колонка — признак ручного номера: ручной, автоматический, без номера."""
    owner = await _user(db_session, "rows-manual@test.com")
    manual = await seed_account(db_session, owner, "tg_user", manual_phone="8 999 123 45 67")
    automatic = await seed_account(db_session, owner, "tg_user", phone="+79991234567")
    without = await seed_account(db_session, owner, "wa")

    rows, _ = await _loaded(db_session, owner)

    by_id = {row.id: row for row in rows}
    assert by_id[manual] == AccountRow(manual, "tg_user", "+79991234567", True)
    assert by_id[automatic] == AccountRow(automatic, "tg_user", "+79991234567", False)
    assert by_id[without] == AccountRow(without, "wa", None, False)

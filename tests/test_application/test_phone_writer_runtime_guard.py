"""Защита единственного писателя номера НА ИСПОЛНЕНИИ (О-23 (а), свойство 3; D-07, D-13).

ЧТО ДОКАЗЫВАЕТСЯ. Статический гейт D-13
(`tests/test_application/test_phone_single_writer_gate.py`) судит исходник, и
его обещание «любое написание записи найдено» за раунды 6–10 не сошлось:
каждый новый корпус находил следующее написание. Решение владельца О-23 (а)
(2026-10-22) добавило вторую линию — сам процесс: запись колонок `phone` и
`phone_is_manual` вне модуля-писателя `app/application/accounts/phone.py`
отказывает В МОМЕНТ ЗАПИСИ исключением `PhoneWriteOutsideWriter`, и строка в
базе не меняется. Писатель пишет под своим разрешением `writer_scope()`.

Здесь — настоящая модель и настоящая сессия (SQLite в памяти, фикстура
`db_session`), а не разбор исходника: правило краснеет, если запись прошла.
Модуль защиты ввозится ВНУТРИ правил (`_guard()`), а признак отказа читается по
имени класса и модулю исключения: без модуля защиты правило падает
утверждением с причиной, а не ошибкой сбора.

Текст отказа не несёт номера (D-11): правила сверяют, что цифр номера в нём нет.
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import functools
import operator
import pathlib
import types

import pytest
import sqlalchemy
from sqlalchemy import delete, event, func, insert, literal, select, text, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm.attributes import (
    flag_modified,
    instance_dict,
    instance_state,
    set_attribute,
    set_committed_value,
)

from app.application.accounts.phone import PhoneWrite, fill_reported_phone
from app.database import Base
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.repositories.account import AccountRepository
from app.services.phone import normalize_reported
from tests.test_application.test_account_phone_race import read_check_write

GUARD_MODULE = "app.models.phone_guard"
GUARD_REFUSAL = "PhoneWriteOutsideWriter"
RAW = "79991234567"
NUMBER = "+79991234567"
DIGITS = "9991234567"

# Причинный литерал RED трасера (задача 1 плана 16-51).
TRACER_RED = (
    "присваивание номера атрибуту вне писателя не отказало защитой на исполнении — "
    "сценарий записал колонку мимо app/application/accounts/phone.py"
)
CONSTRUCTOR_RED = "аргумент конструктора колонки номера не отказал защитой на исполнении"
SCOPE_RED = "разрешение писателя осталось открытым после исключения внутри writer_scope()"


def _guard():
    """Модуль защиты — ввозом внутри правила, а не на уровне модуля теста."""
    from app.models import phone_guard

    return phone_guard


def _is_guard_refusal(exc: BaseException | None) -> bool:
    return (
        exc is not None
        and type(exc).__name__ == GUARD_REFUSAL
        and type(exc).__module__ == GUARD_MODULE
    )


async def _refusal_of(awaitable) -> BaseException | None:
    """Исключение, которым кончилась запись, или `None`, если запись прошла."""
    try:
        await awaitable
    except Exception as exc:  # noqa: BLE001 — правило судит тип сам
        return exc
    return None


def _refusal_of_call(write) -> BaseException | None:
    try:
        write()
    except Exception as exc:  # noqa: BLE001 — правило судит тип сам
        return exc
    return None


async def _seed(session) -> int:
    """Пользователь и аккаунт без номера `(NULL, false)`, закоммиченные."""
    user = User(email="runtime-guard@test.com", name="Владелец", password_hash="x")
    session.add(user)
    await session.flush()
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="cred", status="active"
    )
    session.add(account)
    await session.commit()
    return account.id


async def _columns(session, account_id: int) -> tuple:
    result = await session.execute(
        select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
            MessengerAccount.id == account_id
        )
    )
    return tuple(result.one())


async def planted_backfill(session, account_id: int, raw: object) -> None:
    """Подложенный сценарий дозаполнения Фазы 20 БЕЗ писателя.

    Так его написал бы скрипт, не знающий про D-13: загрузить аккаунт,
    присвоить нормализованный номер атрибуту, закоммитить. Ручной номер такая
    запись затёрла бы молча (D-07).
    """
    account = await session.get(MessengerAccount, account_id)
    account.phone = normalize_reported(raw)
    await session.commit()


@pytest.mark.asyncio
async def test_a_planted_backfill_assigning_the_phone_is_refused_and_the_writer_writes(
    db_session,
):
    """ТРАСЕР: сценарий с `account.phone = …` отказывает, писатель пишет."""
    account_id = await _seed(db_session)

    refusal = await _refusal_of(planted_backfill(db_session, account_id, RAW))

    assert _is_guard_refusal(refusal), f"{TRACER_RED}; исход: {type(refusal).__name__}"
    guard = _guard()
    assert isinstance(refusal, guard.PhoneWriteOutsideWriter)
    assert str(refusal) == guard.PHONE_WRITE_OUTSIDE_WRITER
    assert DIGITS not in str(refusal)

    await db_session.rollback()
    assert await _columns(db_session, account_id) == (None, False)

    outcome = await fill_reported_phone(db_session, account_id, RAW)

    assert outcome is PhoneWrite.WRITTEN
    assert await _columns(db_session, account_id) == (NUMBER, False)


@pytest.mark.parametrize(
    "column,value",
    [
        pytest.param("phone", NUMBER, id="phone"),
        pytest.param("phone_is_manual", True, id="phone_is_manual"),
        # План 16-61 (WR-37): у нового объекта загруженного значения нет — и `None`
        # / `False` в конструкторе отказывают, сравнивать не с чем.
        pytest.param("phone", None, id="phone-none"),
        pytest.param("phone_is_manual", False, id="phone-is-manual-false"),
    ],
)
def test_a_constructor_argument_of_a_phone_column_is_refused(column, value):
    """Аргумент конструктора — та же запись атрибута: отказ до `session.add`."""
    fields = {"user_id": 1, "type": "tg_user", "credentials": "cred", column: value}

    refusal = _refusal_of_call(lambda: MessengerAccount(**fields))

    assert _is_guard_refusal(refusal), f"{CONSTRUCTOR_RED}: {column}"
    assert DIGITS not in str(refusal)


def test_the_scope_is_closed_after_an_exception_inside_it():
    """Исключение внутри разрешения не оставляет его открытым (T-16-117)."""
    guard = _guard()
    account = MessengerAccount(user_id=1, type="tg_user", credentials="cred")

    with contextlib.suppress(LookupError):
        with guard.writer_scope():
            raise LookupError("сбой внутри писателя")

    def assign():
        account.phone = NUMBER

    refusal = _refusal_of_call(assign)

    assert _is_guard_refusal(refusal), SCOPE_RED


# ---------------------------------------------------------------------------
# Задача 2: вторая линия (`before_flush`) и операторы сессии (`do_orm_execute`).
# ---------------------------------------------------------------------------

# Причинные литералы RED задачи 2.
FOREIGN_RED = "запись колонки номера вне писателя не отказала защитой на исполнении"
LEGITIMATE_RED = "законная запись аккаунта отказала или дала не тот итог"
ROUND_TEN_RED = "форма раунда 10 записала колонку номера на исполнении"
REPOSITORY_RED = "путь репозитория записал колонку номера мимо писателя"
READ_CHECK_WRITE_RED = (
    "отрицание гонки вне разрешения писателя не отказало — без writer_scope() оно "
    "писало бы мимо защиты"
)


async def _seed_with_a_number(session) -> int:
    """Аккаунт с номером автоисточника, записанным ПИСАТЕЛЕМ, закоммиченный."""
    account_id = await _seed(session)
    assert await fill_reported_phone(session, account_id, RAW) is PhoneWrite.WRITTEN
    await session.commit()
    return account_id


async def _state(session, account_id: int) -> tuple:
    """Колонки посеянной строки и число строк с номером — до и после записи."""
    count = await session.scalar(
        select(func.count()).select_from(MessengerAccount).where(MessengerAccount.phone == NUMBER)
    )
    return await _columns(session, account_id), count


# --- чужие записи: каждая — вне разрешения писателя ---------------------------


async def _assignment(session, account):
    account.phone = NUMBER
    await session.flush()


async def _setattr(session, account):
    setattr(account, "phone", NUMBER)
    await session.flush()


async def _set_attribute(session, account):
    set_attribute(account, "phone", NUMBER)
    await session.flush()


async def _descriptor_set(session, account):
    MessengerAccount.phone.__set__(account, NUMBER)
    await session.flush()


async def _object_setattr(session, account):
    object.__setattr__(account, "phone", NUMBER)
    await session.flush()


async def _delete_attribute(session, account):
    del account.phone
    await session.flush()


async def _flag_modified(session, account):
    flag_modified(account, "phone")
    await session.flush()


async def _flush_of_a_value_set_inside_the_scope(session, account):
    with _guard().writer_scope():
        account.phone = NUMBER
    await session.flush()


async def _orm_update_values(session, account):
    await session.execute(
        update(MessengerAccount).where(MessengerAccount.id == account.id).values(phone=NUMBER)
    )


async def _orm_update_values_mapping(session, account):
    await session.execute(
        update(MessengerAccount)
        .where(MessengerAccount.id == account.id)
        .values({MessengerAccount.phone: NUMBER})
    )


async def _orm_update_manual_flag(session, account):
    await session.execute(
        update(MessengerAccount)
        .where(MessengerAccount.id == account.id)
        .values(phone_is_manual=True)
    )


async def _orm_update_ordered_values(session, account):
    await session.execute(
        update(MessengerAccount)
        .where(MessengerAccount.id == account.id)
        .ordered_values((MessengerAccount.phone, NUMBER))
    )


async def _core_table_update(session, account):
    table = MessengerAccount.__table__
    await session.execute(update(table).where(table.c.id == account.id).values(phone=NUMBER))


async def _bulk_update_by_primary_key(session, account):
    await session.execute(update(MessengerAccount), [{"id": account.id, "phone": NUMBER}])


async def _orm_insert_values(session, account):
    await session.execute(
        insert(MessengerAccount).values(
            user_id=account.user_id, type="wa", credentials="cred", phone=NUMBER
        )
    )


async def _orm_insert_from_select(session, account):
    await session.execute(
        insert(MessengerAccount).from_select(
            ["user_id", "type", "credentials", "phone"],
            select(
                MessengerAccount.user_id,
                literal("wa"),
                literal("cred"),
                literal(NUMBER),
            ).where(MessengerAccount.id == account.id),
        )
    )


# --- пути мимо событий ORM (план 16-58; формы B1–B6 и W36 верификатора раунда 11,
# CR-08, WR-36): их отказывает линия движка `before_cursor_execute` ---------------


def backfill(sync, rows):
    """Помощник скрипта дозаполнения: строки приходят параметром (форма B2)."""
    sync.bulk_update_mappings(MessengerAccount, rows)


async def _bulk_update_mappings_rows_from_a_variable(session, account):
    payload = [dict(id=account.id, phone=NUMBER, phone_is_manual=True)]
    await session.run_sync(lambda sync: sync.bulk_update_mappings(MessengerAccount, payload))


async def _bulk_update_mappings_rows_as_a_parameter(session, account):
    rows = [{"id": account.id, "phone": NUMBER}]
    await session.run_sync(backfill, rows)


async def _bulk_insert_mappings_rows_built_in_a_loop(session, account):
    rows = []
    for raw in (RAW,):
        rows.append(
            {
                "user_id": account.user_id,
                "type": "wa",
                "credentials": "cred",
                "phone": normalize_reported(raw),
                "phone_is_manual": True,
            }
        )
    await session.run_sync(lambda sync: sync.bulk_insert_mappings(MessengerAccount, rows))


async def _bulk_save_objects_with_a_committed_number(session, account):
    created = MessengerAccount(user_id=account.user_id, type="wa", credentials="cred")
    set_committed_value(created, "phone", NUMBER)
    await session.run_sync(lambda sync: sync.bulk_save_objects([created]))


async def _table_update_through_the_connection(session, account):
    changes = {"phone": NUMBER, "phone_is_manual": True}
    accounts = MessengerAccount.__table__
    conn = await session.connection()
    await conn.execute(accounts.update().where(accounts.c.id == account.id).values(changes))


async def _core_insert_through_the_connection_with_execution_rows(session, account):
    rows = [
        {
            "user_id": account.user_id,
            "type": "wa",
            "credentials": "cred",
            "phone": NUMBER,
            "phone_is_manual": True,
        }
    ]
    conn = await session.connection()
    await conn.execute(insert(MessengerAccount.__table__), rows)


async def _upsert_on_conflict_set_from_a_variable(session, account):
    changes = {"phone": NUMBER, "phone_is_manual": True}
    await session.execute(
        sqlite_insert(MessengerAccount.__table__)
        .values(
            id=account.id, user_id=account.user_id, type="tg_user", credentials="cred"
        )
        .on_conflict_do_update(index_elements=["id"], set_=changes)
    )


def _lightweight_accounts_table():
    """Лёгкая таблица: другой объект, то же имя `messenger_accounts`."""
    return sqlalchemy.table(
        "messenger_accounts", sqlalchemy.column("id"), sqlalchemy.column("phone")
    )


async def _lightweight_table_update_through_the_session(session, account):
    light = _lightweight_accounts_table()
    await session.execute(update(light).where(light.c.id == account.id).values(phone=NUMBER))


async def _lightweight_table_update_through_the_connection(session, account):
    light = _lightweight_accounts_table()
    conn = await session.connection()
    await conn.execute(update(light).where(light.c.id == account.id).values(phone=NUMBER))


async def _new_object_with_a_committed_number_then_add(session, account):
    created = MessengerAccount(user_id=account.user_id, type="wa", credentials="cred")
    set_committed_value(created, "phone", NUMBER)
    set_committed_value(created, "phone_is_manual", True)
    session.add(created)
    await session.flush()


# --- план 16-61 (WR-37): соседи послабления слушателя `set` — перенос объекта
# (`merge`) и присваивание, несущие ДРУГОЕ значение или без загруженного старого,
# и запись того же номера мимо событий атрибута — отказ ------------------------


async def _detached_copy(session, account_id: int) -> MessengerAccount:
    """Копия аккаунта, загруженная другой сессией и отсоединённая (`expunge`)."""
    async with AsyncSession(session.bind) as other:
        copy = await other.get(MessengerAccount, account_id)
        other.expunge(copy)
    return copy


async def _merge_carrying_a_different_number(session, account):
    copy = await _detached_copy(session, account.id)
    set_committed_value(copy, "phone", NUMBER)
    await session.merge(copy, load=True)
    await session.flush()


async def _merge_changing_only_the_manual_flag(session, account):
    copy = await _detached_copy(session, account.id)
    set_committed_value(copy, "phone_is_manual", True)
    await session.merge(copy, load=True)
    await session.flush()


async def _merge_of_a_new_object_carrying_a_number(session, account):
    created = MessengerAccount(user_id=account.user_id, type="wa", credentials="cred")
    set_committed_value(created, "phone", NUMBER)
    await session.merge(created, load=True)
    await session.flush()


async def _assignment_to_an_expired_attribute(session, account):
    session.expire(account, ["phone"])
    account.phone = None
    await session.flush()


async def _assignment_of_a_sql_expression(session, account):
    account.phone = sqlalchemy.null()
    await session.flush()


async def _same_value_over_a_committed_number_on_a_new_object(session, account):
    created = MessengerAccount(user_id=account.user_id, type="wa", credentials="cred")
    set_committed_value(created, "phone", NUMBER)
    created.phone = NUMBER
    session.add(created)
    await session.flush()


async def _bulk_update_mappings_of_the_same_number(session, account):
    rows = [{"id": account.id, "phone": NUMBER}]
    await session.run_sync(lambda sync: sync.bulk_update_mappings(MessengerAccount, rows))


async def _connection_update_of_the_same_number(session, account):
    accounts = MessengerAccount.__table__
    conn = await session.connection()
    await conn.execute(
        update(accounts).where(accounts.c.id == account.id).values(phone=NUMBER)
    )


# (id, запись, посеять номер писателем)
FOREIGN_WRITES = [
    pytest.param(_assignment, False, id="assignment"),
    pytest.param(_setattr, False, id="setattr"),
    pytest.param(_set_attribute, False, id="set-attribute"),
    pytest.param(_descriptor_set, False, id="descriptor-set"),
    pytest.param(_object_setattr, False, id="object-setattr"),
    pytest.param(_delete_attribute, True, id="delete-attribute"),
    pytest.param(_flag_modified, False, id="flag-modified"),
    pytest.param(
        _flush_of_a_value_set_inside_the_scope, False, id="flush-of-a-value-set-inside-the-scope"
    ),
    pytest.param(_orm_update_values, False, id="orm-update-values"),
    pytest.param(_orm_update_values_mapping, False, id="orm-update-values-mapping"),
    pytest.param(_orm_update_manual_flag, True, id="orm-update-manual-flag"),
    pytest.param(_orm_update_ordered_values, False, id="orm-update-ordered-values"),
    pytest.param(_core_table_update, False, id="core-table-update"),
    pytest.param(_bulk_update_by_primary_key, False, id="bulk-update-by-primary-key"),
    pytest.param(_orm_insert_values, False, id="orm-insert-values"),
    pytest.param(_orm_insert_from_select, False, id="orm-insert-from-select"),
    # План 16-58: пути мимо событий ORM — отказ линии движка (CR-08, WR-36).
    pytest.param(
        _bulk_update_mappings_rows_from_a_variable,
        False,
        id="bulk-update-mappings-rows-from-a-variable",
    ),
    pytest.param(
        _bulk_update_mappings_rows_as_a_parameter,
        False,
        id="bulk-update-mappings-rows-as-a-parameter",
    ),
    pytest.param(
        _bulk_insert_mappings_rows_built_in_a_loop,
        False,
        id="bulk-insert-mappings-rows-built-in-a-loop",
    ),
    pytest.param(
        _bulk_save_objects_with_a_committed_number,
        False,
        id="bulk-save-objects-of-a-new-account-with-a-committed-number",
    ),
    pytest.param(
        _table_update_through_the_connection,
        False,
        id="table-update-through-the-connection",
    ),
    pytest.param(
        _core_insert_through_the_connection_with_execution_rows,
        False,
        id="core-insert-through-the-connection-with-execution-rows",
    ),
    pytest.param(
        _upsert_on_conflict_set_from_a_variable,
        False,
        id="upsert-on-conflict-set-from-a-variable",
    ),
    pytest.param(
        _lightweight_table_update_through_the_session,
        False,
        id="lightweight-table-update-through-the-session",
    ),
    pytest.param(
        _lightweight_table_update_through_the_connection,
        False,
        id="lightweight-table-update-through-the-connection",
    ),
    pytest.param(
        _new_object_with_a_committed_number_then_add,
        False,
        id="new-object-with-a-committed-number-then-add",
    ),
    # План 16-61 (WR-37): соседи послабления слушателя `set` — отказ и после него.
    pytest.param(
        _merge_carrying_a_different_number, False, id="merge-carrying-a-different-number"
    ),
    pytest.param(
        _merge_changing_only_the_manual_flag,
        True,
        id="merge-changing-only-the-manual-flag",
    ),
    pytest.param(
        _merge_of_a_new_object_carrying_a_number,
        False,
        id="merge-of-a-new-object-carrying-a-number",
    ),
    pytest.param(
        _assignment_to_an_expired_attribute, False, id="assignment-to-an-expired-attribute"
    ),
    pytest.param(
        _assignment_of_a_sql_expression, False, id="assignment-of-a-sql-expression"
    ),
    pytest.param(
        _same_value_over_a_committed_number_on_a_new_object,
        False,
        id="same-value-over-a-committed-number-on-a-new-object",
    ),
    pytest.param(
        _bulk_update_mappings_of_the_same_number,
        True,
        id="bulk-update-mappings-of-the-same-number",
    ),
    pytest.param(
        _connection_update_of_the_same_number,
        True,
        id="connection-update-of-the-same-number",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("write,with_a_number", FOREIGN_WRITES)
async def test_a_foreign_write_is_refused(db_session, write, with_a_number):
    """Каждый путь ORM записи колонок номера вне писателя отказывает; строка прежняя."""
    seed = _seed_with_a_number if with_a_number else _seed
    account_id = await seed(db_session)
    before = await _state(db_session, account_id)
    account = await db_session.get(MessengerAccount, account_id)
    await db_session.refresh(account)

    refusal = await _refusal_of(write(db_session, account))

    assert _is_guard_refusal(refusal), f"{FOREIGN_RED}; исход: {type(refusal).__name__}"
    assert DIGITS not in str(refusal)
    await db_session.rollback()
    assert await _state(db_session, account_id) == before


# --- законные записи: без отказа и с ожидаемым итогом ------------------------


async def _create_without_a_number(session, account):
    created = MessengerAccount(
        user_id=account.user_id, type="wa", credentials="cred", status="active"
    )
    session.add(created)
    await session.flush()
    assert await _columns(session, created.id) == (None, False)


async def _status_assignment(session, account):
    account.status = "disconnected"
    await session.flush()
    status = await session.scalar(
        select(MessengerAccount.status).where(MessengerAccount.id == account.id)
    )
    assert status == "disconnected"


async def _status_update_statement(session, account):
    await session.execute(
        update(MessengerAccount)
        .where(MessengerAccount.id == account.id)
        .values(status="paused")
    )
    status = await session.scalar(
        select(MessengerAccount.status).where(MessengerAccount.id == account.id)
    )
    assert status == "paused"


async def _select_filtered_by_the_number(session, account):
    found = await session.scalars(
        select(MessengerAccount.id).where(MessengerAccount.phone == NUMBER)
    )
    assert list(found) == []


async def _repository_create_without_a_number(session, account):
    created = await AccountRepository(session).create(
        user_id=account.user_id, type="wa", credentials="cred", status="active"
    )
    assert (created.phone, created.phone_is_manual) == (None, False)


async def _repository_update_of_the_status(session, account):
    updated = await AccountRepository(session).update(account, status="error")
    assert updated.status == "error"
    assert (updated.phone, updated.phone_is_manual) == (None, False)


async def _delete_statement(session, account):
    await session.execute(
        delete(MessengerAccount).where(MessengerAccount.id == account.id)
    )
    left = await session.scalar(
        select(func.count())
        .select_from(MessengerAccount)
        .where(MessengerAccount.id == account.id)
    )
    assert left == 0


# --- законные пути мимо событий ORM (план 16-58): линия движка их не отказывает --


async def _status_of(session, account_id: int) -> str:
    return await session.scalar(
        select(MessengerAccount.status).where(MessengerAccount.id == account_id)
    )


async def _status_update_through_the_connection(session, account):
    accounts = MessengerAccount.__table__
    conn = await session.connection()
    await conn.execute(
        update(accounts).where(accounts.c.id == account.id).values(status="paused")
    )
    assert await _status_of(session, account.id) == "paused"


async def _status_bulk_update_mappings(session, account):
    rows = [{"id": account.id, "status": "paused"}]
    await session.run_sync(lambda sync: sync.bulk_update_mappings(MessengerAccount, rows))
    assert await _status_of(session, account.id) == "paused"
    assert await _columns(session, account.id) == (None, False)


async def _accounts_of(session, user_id: int) -> list[tuple]:
    result = await session.execute(
        select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
            MessengerAccount.user_id == user_id
        )
    )
    return [tuple(row) for row in result]


async def _bulk_insert_mappings_without_a_number(session, account):
    rows = [{"user_id": account.user_id, "type": "wa", "credentials": "cred"}]
    await session.run_sync(lambda sync: sync.bulk_insert_mappings(MessengerAccount, rows))
    assert await _accounts_of(session, account.user_id) == [(None, False), (None, False)]


async def _core_insert_with_an_unknown_number(session, account):
    conn = await session.connection()
    await conn.execute(
        insert(MessengerAccount.__table__).values(
            user_id=account.user_id,
            type="wa",
            credentials="cred",
            phone=None,
            phone_is_manual=False,
        )
    )
    assert await _accounts_of(session, account.user_id) == [(None, False), (None, False)]


async def _create_several_without_a_number(session, account):
    created = [
        MessengerAccount(user_id=account.user_id, type="wa", credentials=f"cred-{n}")
        for n in range(3)
    ]
    session.add_all(created)
    await session.flush()
    assert await _accounts_of(session, account.user_id) == [(None, False)] * 4


async def _status_update_filtered_by_the_number_through_the_connection(session, account):
    accounts = MessengerAccount.__table__
    conn = await session.connection()
    result = await conn.execute(
        update(accounts).where(accounts.c.phone == NUMBER).values(status="paused")
    )
    assert result.rowcount == 0


async def _delete_through_the_connection(session, account):
    accounts = MessengerAccount.__table__
    conn = await session.connection()
    await conn.execute(delete(accounts).where(accounts.c.id == account.id))
    assert await _accounts_of(session, account.user_id) == []


# --- план 16-61 (WR-37): перенос объекта и присваивание того же значения — не запись


async def _merge_of_a_loaded_account(session, account):
    """Перенос копии из другой сессии (`merge` при `load=True`) — значения те же."""
    before = await _state(session, account.id)
    copy = await _detached_copy(session, account.id)

    merged = await session.merge(copy, load=True)
    await session.flush()

    assert merged is account
    assert await _state(session, account.id) == before


async def _same_value_assignment_of_a_loaded_account(session, account):
    """Присваивание загруженному атрибуту его же значения: истории нет, UPDATE нет."""
    before = await _state(session, account.id)

    account.phone = account.phone
    account.phone_is_manual = account.phone_is_manual

    attributes = sqlalchemy.inspect(account).attrs
    assert not attributes.phone.history.has_changes()
    assert not attributes.phone_is_manual.history.has_changes()
    await session.flush()
    assert await _state(session, account.id) == before


LEGITIMATE_WRITES = [
    pytest.param(_create_without_a_number, id="create-without-a-number"),
    pytest.param(_status_assignment, id="status-assignment"),
    pytest.param(_status_update_statement, id="status-update-statement"),
    pytest.param(_select_filtered_by_the_number, id="select-filtered-by-the-number"),
    pytest.param(
        _repository_create_without_a_number, id="repository-create-without-a-number"
    ),
    pytest.param(
        _repository_update_of_the_status, id="repository-update-of-the-status"
    ),
    pytest.param(_delete_statement, id="delete-statement"),
    # План 16-58: законные пути мимо событий ORM (О-25 (а), свойство 4).
    pytest.param(
        _status_update_through_the_connection, id="status-update-through-the-connection"
    ),
    pytest.param(_status_bulk_update_mappings, id="status-bulk-update-mappings"),
    pytest.param(
        _bulk_insert_mappings_without_a_number, id="bulk-insert-mappings-without-a-number"
    ),
    pytest.param(
        _core_insert_with_an_unknown_number, id="core-insert-with-an-unknown-number"
    ),
    pytest.param(_create_several_without_a_number, id="create-several-without-a-number"),
    pytest.param(
        _status_update_filtered_by_the_number_through_the_connection,
        id="status-update-filtered-by-the-number-through-the-connection",
    ),
    pytest.param(_delete_through_the_connection, id="delete-through-the-connection"),
    # План 16-61 (WR-37; О-25 (а), свойство 6): перенос объекта и то же значение.
    pytest.param(_merge_of_a_loaded_account, id="merge-of-a-loaded-account"),
    pytest.param(
        _same_value_assignment_of_a_loaded_account,
        id="same-value-assignment-of-a-loaded-account",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("write", LEGITIMATE_WRITES)
async def test_a_legitimate_write_passes(db_session, write):
    """Законные пути не отказывают (T-16-118): защита судит только колонки номера."""
    account_id = await _seed(db_session)
    account = await db_session.get(MessengerAccount, account_id)

    refusal = await _refusal_of(write(db_session, account))

    assert refusal is None, (
        f"{LEGITIMATE_RED}; исход: {type(refusal).__name__}: {refusal}"
    )


# --- формы раунда 10 стороны писателя, исполненные над настоящей моделью --------
#
# Исходник каждой формы — из ревью WR-33 (16-REVIEW.md) и верификации V10-1,
# V10-2 (16-VERIFICATION.md, гэпы 3 и 4). Носитель `asyncio.to_thread` подменён
# прямым вызовом: правило судит ЗАПИСЬ, а не поток.

_WR33_GETATTR_CARRIER_SETATTR = '''
async def form(account, x):
    to_thread = getattr
    await asyncio.to_thread(setattr, account, "phone", x)
'''

_WR33_METHODCALLER_CARRIER_DESCRIPTOR = '''
async def form(account, x):
    to_thread = operator.methodcaller
    await asyncio.to_thread(
        operator.methodcaller("__set__", account, x), MessengerAccount.phone
    )
'''

_WR33_PARTIAL_SETATTR_ACCOUNT = '''
async def form(account, x):
    to_thread = getattr
    await asyncio.to_thread(functools.partial(setattr, account), "phone", x)
'''

_V10_1_FUNCTION_GETATTR_CLASS_SETATTR = '''
def pick(obj, name):
    f = getattr
    return f(obj, name)


class Backfill:
    def __init__(self):
        self.f = setattr

    def write(self, account, x):
        self.f(account, "phone", x)


async def form(account, x):
    Backfill().write(account, x)
'''

_V10_2_GETATTR_STRING_OF_A_SETATTR_ATTRIBUTE = '''
def pick(obj, name):
    f = getattr
    return f(obj, name)


class Backfill:
    def __init__(self):
        self.f = setattr

    def write(self, account, x):
        getattr(self, "f")(account, "phone", x)


async def form(account, x):
    Backfill().write(account, x)
'''

_WR33_SET_COMMITTED_VALUE_CARRIER = '''
async def form(account, x):
    to_thread = getattr
    await asyncio.to_thread(set_committed_value, account, "phone", x)
'''

# (исходник формы, отказывает ли защита)
ROUND_TEN_WRITER_FORMS = [
    pytest.param(
        _WR33_GETATTR_CARRIER_SETATTR, True, id="wr33-getattr-name-of-a-carrier-setattr"
    ),
    pytest.param(
        _WR33_METHODCALLER_CARRIER_DESCRIPTOR,
        True,
        id="wr33-methodcaller-name-of-a-carrier-descriptor",
    ),
    pytest.param(
        _WR33_PARTIAL_SETATTR_ACCOUNT, True, id="wr33-partial-setattr-account"
    ),
    pytest.param(
        _V10_1_FUNCTION_GETATTR_CLASS_SETATTR,
        True,
        id="v10-1-function-binds-getattr-class-binds-setattr",
    ),
    pytest.param(
        _V10_2_GETATTR_STRING_OF_A_SETATTR_ATTRIBUTE,
        True,
        id="v10-2-getattr-string-of-a-setattr-attribute",
    ),
    pytest.param(
        _WR33_SET_COMMITTED_VALUE_CARRIER,
        False,
        id="wr33-set-committed-value-handed-to-a-carrier",
    ),
]


async def _direct_call(function, /, *args, **kwargs):
    """Носитель `asyncio.to_thread`, исполняющий поданный вызов синхронно."""
    return function(*args, **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize("source,refused", ROUND_TEN_WRITER_FORMS)
async def test_a_round_ten_writer_form_is_safe_at_run_time(db_session, source, refused):
    """Свойство 4 О-23: формы WR-33, V10-1, V10-2 безопасны на исполнении."""
    account_id = await _seed(db_session)
    account = await db_session.get(MessengerAccount, account_id)
    namespace = {
        "MessengerAccount": MessengerAccount,
        "setattr": setattr,
        "operator": operator,
        "functools": functools,
        "asyncio": types.SimpleNamespace(to_thread=_direct_call),
        "set_committed_value": set_committed_value,
    }
    exec(compile(source, "<форма раунда 10>", "exec"), namespace)

    refusal = await _refusal_of(namespace["form"](account, NUMBER))

    if refused:
        assert _is_guard_refusal(refusal), (
            f"{ROUND_TEN_RED}; исход: {type(refusal).__name__}"
        )
        await db_session.rollback()
        assert await _columns(db_session, account_id) == (None, False)
        return
    # `set_committed_value` в базу не пишет: значение остаётся в памяти объекта.
    assert refusal is None, f"{ROUND_TEN_RED}; исход: {type(refusal).__name__}"
    assert account.phone == NUMBER
    await db_session.commit()
    async with AsyncSession(db_session.bind) as fresh:
        assert await _columns(fresh, account_id) == (None, False), ROUND_TEN_RED


@pytest.mark.asyncio
async def test_the_repository_paths_of_a_phone_column_are_refused(db_session):
    """`AccountRepository.create(…, phone=x)` и `.update(account, phone=x)` отказывают."""
    account_id = await _seed(db_session)
    account = await db_session.get(MessengerAccount, account_id)
    repository = AccountRepository(db_session)
    before = await _state(db_session, account_id)

    created = await _refusal_of(
        repository.create(
            user_id=account.user_id, type="wa", credentials="cred", phone=NUMBER
        )
    )
    await db_session.rollback()
    account = await db_session.get(MessengerAccount, account_id)
    updated = await _refusal_of(repository.update(account, phone=NUMBER))
    await db_session.rollback()

    assert _is_guard_refusal(created), f"{REPOSITORY_RED}: create"
    assert _is_guard_refusal(updated), f"{REPOSITORY_RED}: update"
    assert await _state(db_session, account_id) == before


@pytest.mark.asyncio
async def test_a_read_check_write_outside_the_writer_scope_is_refused(db_session):
    """Отрицание гонки БЕЗ разрешения писателя отказывает защитой до записи.

    Свидетель того, что разрешение в `read_check_write` теста гонки необходимо:
    без него контроль-отрицание D-08 краснело бы отказом защиты, а не потерей
    ручного номера, и стало бы вакуумом.
    """
    account_id = await _seed(db_session)

    refusal = await _refusal_of(
        read_check_write(db_session, account_id, RAW, scope=contextlib.nullcontext)
    )

    assert _is_guard_refusal(refusal), (
        f"{READ_CHECK_WRITE_RED}; исход: {type(refusal).__name__}"
    )
    await db_session.rollback()
    assert await _columns(db_session, account_id) == (None, False)


# ---------------------------------------------------------------------------
# План 16-58: запись мимо событий ORM — линия движка `before_cursor_execute`
# (гэп 3 раунда 11, CR-08, WR-36; решение владельца О-25 (а), свойство 4).
# ---------------------------------------------------------------------------

# Причинный литерал RED трасера плана 16-58 (задача 1).
ENGINE_LINE_RED = "запись номера мимо событий ORM не отказала на курсоре (CR-08)"


async def planted_backfill_with_a_list_of_rows(session, pairs) -> None:
    """Подложенный сценарий дозаполнения Фазы 20 со СПИСКОМ СТРОК, без писателя.

    Так его написал бы скрипт, собирающий строки циклом из выгрузки воркеров:
    `bulk_update_mappings` событий атрибута и `do_orm_execute` не даёт, а
    строки из переменной не судит ни предикат гейта, ни канал запрета (CR-08).
    """
    rows = []
    for account_id, raw in pairs:
        rows.append({"id": account_id, "phone": normalize_reported(raw)})
    await session.run_sync(lambda sync: sync.bulk_update_mappings(MessengerAccount, rows))
    await session.commit()


@pytest.mark.asyncio
async def test_a_planted_backfill_with_a_list_of_rows_is_refused_and_the_writer_writes(
    db_session,
):
    """ТРАСЕР 16-58: дозаполнение списком строк отказывает на курсоре, писатель пишет."""
    account_id = await _seed(db_session)

    refusal = await _refusal_of(
        planted_backfill_with_a_list_of_rows(db_session, [(account_id, RAW)])
    )

    assert _is_guard_refusal(refusal), f"{ENGINE_LINE_RED}; исход: {type(refusal).__name__}"
    assert DIGITS not in str(refusal)

    await db_session.rollback()
    assert await _columns(db_session, account_id) == (None, False)

    outcome = await fill_reported_phone(db_session, account_id, RAW)

    assert outcome is PhoneWrite.WRITTEN
    assert await _columns(db_session, account_id) == (NUMBER, False)


@pytest.mark.asyncio
async def test_the_engine_line_stands_on_the_engine_class():
    """Линия движка стоит на классе `Engine`: и на движке, созданном после ввоза моделей."""
    guard = _guard()
    listener = vars(guard).get("_refuse_unscoped_cursor")

    assert listener is not None, f"{ENGINE_LINE_RED}: в модуле защиты нет слушателя курсора"
    assert event.contains(Engine, "before_cursor_execute", listener), (
        f"{ENGINE_LINE_RED}: слушатель курсора не стоит на классе Engine"
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.connect() as conn:
            refusal = await _refusal_of(
                conn.execute(update(MessengerAccount.__table__).values(phone=NUMBER))
            )
    finally:
        await engine.dispose()

    assert _is_guard_refusal(refusal), (
        f"{ENGINE_LINE_RED}: движок, созданный после ввоза моделей; "
        f"исход: {type(refusal).__name__}"
    )
    assert DIGITS not in str(refusal)


# --- цена «отказ в закрытую» (план 16-58; D-11): значение колонки номера на
# курсоре не находится по ключу колонки — вставка отказывает и без номера -------

# Причинные литералы RED задачи 2 плана 16-58.
CLOSED_RED = (
    "вставка с несудимым на курсоре значением колонки номера не отказала в закрытую"
)
SECOND_LINE_RED = (
    "новый аккаунт с номером, поставленным set_committed_value, не отказал во второй "
    "линии — before_flush судит историю, а не значения (WR-36)"
)


async def _core_insert_multi_values_with_an_unknown_number(session, account):
    conn = await session.connection()
    await conn.execute(
        insert(MessengerAccount.__table__).values(
            [
                {
                    "user_id": account.user_id,
                    "type": "wa",
                    "credentials": "cred",
                    "phone": None,
                }
            ]
        )
    )


async def _core_insert_of_a_sql_expression_for_the_number(session, account):
    conn = await session.connection()
    await conn.execute(
        insert(MessengerAccount.__table__).values(
            user_id=account.user_id,
            type="wa",
            credentials="cred",
            phone=sqlalchemy.null(),
        )
    )


async def _merge_into_a_session_holding_an_expired_copy(session, account):
    """План 16-61 (WR-37): старое значение не загружено — сравнивать не с чем, отказ."""
    copy = await _detached_copy(session, account.id)
    session.expire(account, ["phone"])
    await session.merge(copy, load=True)


CLOSED_FAILING_WRITES = [
    pytest.param(
        _core_insert_multi_values_with_an_unknown_number,
        id="core-insert-multi-values-with-an-unknown-number",
    ),
    pytest.param(
        _core_insert_of_a_sql_expression_for_the_number,
        id="core-insert-of-a-sql-expression-for-the-number",
    ),
    # План 16-61: цена линии атрибута — `merge` поверх истёкшей копии в сессии.
    pytest.param(
        _merge_into_a_session_holding_an_expired_copy,
        id="merge-into-a-session-holding-an-expired-copy",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("write", CLOSED_FAILING_WRITES)
async def test_a_write_whose_values_cannot_be_judged_is_refused_closed(db_session, write):
    """Названная цена защиты: несудимое значение колонки номера — отказ, номера нет.

    Строки 16-58 — цена линии движка (значение на курсоре не находится по ключу
    колонки); строка 16-61 — цена линии атрибута (старое значение не загружено).
    """
    account_id = await _seed(db_session)
    before = await _state(db_session, account_id)
    account = await db_session.get(MessengerAccount, account_id)
    user_id = account.user_id

    refusal = await _refusal_of(write(db_session, account))

    assert _is_guard_refusal(refusal), f"{CLOSED_RED}; исход: {type(refusal).__name__}"
    await db_session.rollback()
    assert await _state(db_session, account_id) == before
    assert await _accounts_of(db_session, user_id) == [(None, False)]


@pytest.mark.asyncio
async def test_a_new_account_is_judged_by_its_values_before_the_flush(db_session):
    """Вторая линия судит новый объект по значениям (WR-36), а не по истории.

    Линия движка в этом вызове не участвует: слушатель `before_flush` зовётся
    напрямую над сессией, в которой лежит новый аккаунт.
    """
    account_id = await _seed(db_session)
    account = await db_session.get(MessengerAccount, account_id)
    created = MessengerAccount(user_id=account.user_id, type="wa", credentials="cred")
    set_committed_value(created, "phone", NUMBER)
    set_committed_value(created, "phone_is_manual", True)
    db_session.add(created)

    refusal = _refusal_of_call(
        lambda: _guard()._refuse_unscoped_flush(db_session.sync_session, None, None)
    )

    assert _is_guard_refusal(refusal), f"{SECOND_LINE_RED}; исход: {type(refusal).__name__}"
    assert DIGITS not in str(refusal)
    db_session.expunge(created)


# ---------------------------------------------------------------------------
# Задача 3: правдивые тексты — шапка защиты, абзац писателя, комментарий модели.
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
GUARD_PATH = REPO_ROOT / "app" / "models" / "phone_guard.py"
WRITER_PATH = REPO_ROOT / "app" / "application" / "accounts" / "phone.py"
MODEL_PATH = REPO_ROOT / "app" / "models" / "messenger_account.py"

# Причинный литерал RED задачи 3.
HEADER_RED = "шапка защиты не называет, что отказывает и где её граница"

GUARD_HEADER_NAMES = (
    "О-23 (а)",
    "свойство 3",
    "D-13",
    "writer_scope",
    "set",
    "remove",
    "modified",
    "before_flush",
    "do_orm_execute",
    "set_committed_value",
    "bulk_update_mappings",
    "session.connection()",
    "сырой SQL",
    "план 16-53",
    "план 16-55",
    # План 16-58: четвёртая линия, её место и граница по замеру (О-25 (а), свойство 5).
    "before_cursor_execute",
    "Engine",
    "messenger_accounts",
    "bulk_insert_mappings",
    "on_conflict_do_update",
    "text(",
    "exec_driver_sql",
    "сырое соединение DBAPI",
    "CLOSED_FAILING_WRITES",
    "О-25 (а)",
    # План 16-61: сравнение у `set`, автосброс писателя, копия разрешения в задаче
    # и таблица измеренной границы (WR-37, IN-23, IN-24; О-25 (а), свойство 5).
    "merge",
    "autoflush=False",
    "create_task",
    "IN-23",
    "IN-24",
    "WR-37",
    "GUARD_BOUNDARY_WRITES",
    # Принятые границы раунда 12 (ревью CR-09, WR-40, IN-29; WR-43 — сброс до разрешения).
    "CR-09",
    "WR-40",
    "IN-29",
    "WR-43",
)
# Фраза прежнего обещания: после плана 16-58 — только в летописи, с причиной.
RETIRED_PROMISE = "каким бы написанием она ни была сделана"
CHRONICLE_HEAD = "Летопись"
CHRONICLE_CAUSES = ("CR-08", "WR-36")
WRITER_PARAGRAPH_HEAD = "ЗАЩИТА НА ИСПОЛНЕНИИ"
WRITER_PARAGRAPH_NAMES = (
    "app/models/phone_guard.py",
    "writer_scope",
    "autoflush=False",
    "IN-23",
)
# План 16-61 (IN-24): `finally` снимает разрешение только в ТЕКУЩЕМ контексте —
# фраза о снятии стоит в шапке лишь рядом с этим словом.
SCOPE_RELEASE_PHRASE = "снимается токеном в `finally`"
SCOPE_RELEASE_QUALIFIER = "текущем"
SCOPE_RELEASE_WINDOW = 300


def _docstring(path: pathlib.Path) -> str:
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""


def _phone_column_comment() -> str:
    """Комментарий над объявлением колонки `phone` модели, строки подряд."""
    lines = MODEL_PATH.read_text(encoding="utf-8").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("    phone: Mapped"))
    comment: list[str] = []
    for line in reversed(lines[:index]):
        if not line.strip().startswith("#"):
            break
        comment.insert(0, line.strip().lstrip("#").strip())
    return " ".join(comment)


def test_the_guard_module_names_what_it_refuses_and_its_boundary():
    """Шапка защиты, абзац писателя и комментарий модели называют защиту правдиво."""
    guard = " ".join(_docstring(GUARD_PATH).split())
    paragraphs = [" ".join(p.split()) for p in _docstring(WRITER_PATH).split("\n\n")]
    writer = next((p for p in paragraphs if p.startswith(WRITER_PARAGRAPH_HEAD)), "")
    comment = " ".join(_phone_column_comment().split())

    missing = [f"шапка защиты: {name}" for name in GUARD_HEADER_NAMES if name not in guard]
    chronicle_at = guard.find(CHRONICLE_HEAD)
    promise = guard[:chronicle_at] if chronicle_at >= 0 else guard
    chronicle = guard[chronicle_at:] if chronicle_at >= 0 else ""
    if RETIRED_PROMISE in promise:
        missing.append(f"шапка защиты: «{RETIRED_PROMISE}» вне летописи")
    if RETIRED_PROMISE in chronicle:
        missing += [
            f"летопись шапки защиты: {cause}"
            for cause in CHRONICLE_CAUSES
            if cause not in chronicle
        ]
    at = guard.find(SCOPE_RELEASE_PHRASE)
    while at >= 0:
        near = guard[max(0, at - SCOPE_RELEASE_WINDOW) : at + SCOPE_RELEASE_WINDOW]
        if SCOPE_RELEASE_QUALIFIER not in near:
            missing.append(
                f"шапка защиты: «{SCOPE_RELEASE_PHRASE}» без «{SCOPE_RELEASE_QUALIFIER}» (IN-24)"
            )
        at = guard.find(SCOPE_RELEASE_PHRASE, at + 1)
    if not writer:
        missing.append(f"писатель: абзац «{WRITER_PARAGRAPH_HEAD}»")
    missing += [
        f"абзац писателя: {name}" for name in WRITER_PARAGRAPH_NAMES if name not in writer
    ]
    if "app/models/phone_guard.py" not in comment:
        missing.append("комментарий колонки phone: app/models/phone_guard.py")

    assert not missing, f"{HEADER_RED}: {missing}"


# ---------------------------------------------------------------------------
# План 16-61: автосброс под разрешением писателя (IN-23) и измеренная граница
# защиты (IN-24; О-25 (а), свойства 5, 6).
# ---------------------------------------------------------------------------

# Причинный литерал RED правила автосброса (задача 2 плана 16-61).
PENDING_RED = "чужое отложенное изменение номера сброшено под разрешением писателя (IN-23)"
FOREIGN_PENDING_NUMBER = "+79990000001"


async def _fill_then_commit(session, account_id: int) -> None:
    assert await fill_reported_phone(session, account_id, RAW) is PhoneWrite.WRITTEN
    await session.commit()


@pytest.mark.asyncio
async def test_a_foreign_pending_change_is_not_flushed_under_the_writer_scope(db_session):
    """Отложенное изменение колонок номера чужого кода не сбрасывается писателем.

    История помечена мимо события атрибута (приватный API — публичного пути
    нет: `flag_modified` отказывает событием `modified`). Оператор писателя
    исполняется с `autoflush=False`, поэтому чужое изменение сбрасывается
    позже, на коммите вне `writer_scope()`, и отказывает второй линией.
    """
    first_id = await _seed(db_session)
    first = await db_session.get(MessengerAccount, first_id)
    second = MessengerAccount(
        user_id=first.user_id, type="wa", credentials="cred", status="active"
    )
    db_session.add(second)
    await db_session.commit()
    second_id = second.id

    state, values = instance_state(first), instance_dict(first)
    for column, value in (("phone", FOREIGN_PENDING_NUMBER), ("phone_is_manual", True)):
        state._modified_event(values, state.manager[column].impl, values.get(column))
        values[column] = value

    refusal = await _refusal_of(_fill_then_commit(db_session, second_id))

    assert _is_guard_refusal(refusal), f"{PENDING_RED}; исход: {type(refusal).__name__}"
    assert DIGITS not in str(refusal)
    await db_session.rollback()
    assert await _columns(db_session, first_id) == (None, False), PENDING_RED
    assert await _columns(db_session, second_id) == (None, False)


# --- измеренная граница защиты: каждая строка исполнением ПИШЕТ номер ----------
#
# Это мера границы для шапки, а не норма поведения (урок «тесты фазы закрепляют
# старые дефекты»): если строка однажды начнёт отказывать, граница закрылась —
# строку убирают из таблицы и из шапки, а не чинят тест.

GUARD_BOUNDARY_RED = (
    "граница закрылась: строка отказывает — уберите её из `GUARD_BOUNDARY_WRITES` "
    "и из шапки защиты (это не поломка)"
)
BOUNDARY_HEADER_RED = "шапка защиты не называет измеренную границу"
_RAW_UPDATE = "UPDATE messenger_accounts SET phone = ? WHERE id = ?"


async def _text_update_through_the_session(session, account):
    await session.execute(
        text("UPDATE messenger_accounts SET phone = :phone WHERE id = :id"),
        {"phone": NUMBER, "id": account.id},
    )


async def _exec_driver_sql_update(session, account):
    conn = await session.connection()
    await conn.exec_driver_sql(_RAW_UPDATE, (NUMBER, account.id))


async def _raw_dbapi_driver_connection_update(session, account):
    raw = await (await session.connection()).get_raw_connection()
    await raw.driver_connection.execute(_RAW_UPDATE, (NUMBER, account.id))


async def _task_spawned_inside_the_writer_scope(session, account):
    """Задача, порождённая внутри разрешения, исполняет UPDATE после выхода из него."""

    async def late_write():
        await session.execute(
            update(MessengerAccount)
            .where(MessengerAccount.id == account.id)
            .values(phone=NUMBER)
            .execution_options(synchronize_session=False)
        )

    with _guard().writer_scope():
        task = asyncio.create_task(late_write())
    await task


async def _update_through_an_upper_case_table_name(session, account):
    """Имя таблицы в другом регистре: СУБД складывает его, линия движка — нет (WR-40)."""
    upper = sqlalchemy.table(
        "MESSENGER_ACCOUNTS", sqlalchemy.column("id"), sqlalchemy.column("phone")
    )
    conn = await session.connection()
    await conn.execute(
        sqlalchemy.update(upper).where(upper.c.id == account.id).values(phone=NUMBER)
    )


# (запись, фраза шапки защиты, называющая строку)
GUARD_BOUNDARY_WRITES = [
    pytest.param(_text_update_through_the_session, "text(", id="text-update-through-the-session"),
    pytest.param(_exec_driver_sql_update, "exec_driver_sql", id="exec-driver-sql-update"),
    pytest.param(
        _raw_dbapi_driver_connection_update,
        "сырое соединение DBAPI",
        id="raw-dbapi-driver-connection-update",
    ),
    pytest.param(
        _task_spawned_inside_the_writer_scope,
        "create_task",
        id="task-spawned-inside-the-writer-scope",
    ),
    pytest.param(
        _update_through_an_upper_case_table_name,
        "MESSENGER_ACCOUNTS",
        id="update-through-an-upper-case-table-name",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("write,header_phrase", GUARD_BOUNDARY_WRITES)
async def test_a_named_boundary_of_the_guard_is_measured_and_named(
    db_session, write, header_phrase
):
    """Строка границы исполнением пишет номер, и шапка защиты её называет."""
    account_id = await _seed(db_session)
    account = await db_session.get(MessengerAccount, account_id)

    refusal = await _refusal_of(write(db_session, account))

    assert refusal is None, f"{GUARD_BOUNDARY_RED}; исход: {type(refusal).__name__}"
    await db_session.commit()
    assert await _columns(db_session, account_id) == (NUMBER, False), GUARD_BOUNDARY_RED
    guard = " ".join(_docstring(GUARD_PATH).split())
    assert header_phrase in guard, f"{BOUNDARY_HEADER_RED}: «{header_phrase}»"

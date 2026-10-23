"""Защита единственного писателя номера на исполнении (О-23 (а), свойство 3; D-07, D-13)."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import ORMExecuteState, Session, UOWTransaction
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.sql.dml import Insert, Update
from sqlalchemy.sql.elements import ColumnElement

from app.models.messenger_account import MessengerAccount

# Колонки номера — те же две, что судит статический гейт писателя (`PHONE_COLUMNS`).
GUARDED_COLUMNS: tuple[str, ...] = ("phone", "phone_is_manual")

# Постоянный текст отказа: без значения колонки и без номера (D-11).
PHONE_WRITE_OUTSIDE_WRITER = (
    "колонки номера аккаунта пишет только app/application/accounts/phone.py (D-13)"
)


class PhoneWriteOutsideWriter(RuntimeError):
    """Запись колонки номера вне разрешения писателя `writer_scope()`."""


_WRITER_ACTIVE: ContextVar[bool] = ContextVar("phone_writer_active", default=False)


@contextlib.contextmanager
def writer_scope() -> Iterator[None]:
    """Разрешение писателя: внутри него запись колонок номера не отказывает.

    Снимается токеном в `finally` — и после исключения внутри (T-16-117).
    """
    token = _WRITER_ACTIVE.set(True)
    try:
        yield
    finally:
        _WRITER_ACTIVE.reset(token)


def _refuse_attribute_write(*args: object, **kwargs: object) -> None:
    """Слушатель `set` / `remove` / `modified` колонок номера."""
    if not _WRITER_ACTIVE.get():
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)


_GUARDED_ATTRIBUTES = (MessengerAccount.phone, MessengerAccount.phone_is_manual)
_ATTRIBUTE_EVENTS = ("set", "remove", "modified")

for _attribute in _GUARDED_ATTRIBUTES:
    for _event_name in _ATTRIBUTE_EVENTS:
        event.listen(_attribute, _event_name, _refuse_attribute_write)


def _refuse_unscoped_flush(
    session: Session, flush_context: UOWTransaction, instances: object
) -> None:
    """Слушатель `before_flush`: значение колонки номера сбрасывается без разрешения.

    Вторая линия после событий атрибута: значение, поставленное под
    `writer_scope()`, а сброшенное вне его, тоже отказывает.
    """
    if _WRITER_ACTIVE.get():
        return
    for instance in (*session.new, *session.dirty):
        if not isinstance(instance, MessengerAccount):
            continue
        attributes = sa_inspect(instance).attrs
        for column in GUARDED_COLUMNS:
            if attributes[column].history.added:
                raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)


_ACCOUNTS_TABLE = sa_inspect(MessengerAccount).local_table


def _column_name(key: object) -> str:
    if isinstance(key, str):
        return key
    if isinstance(key, (ColumnElement, QueryableAttribute)):
        return str(key.key)
    return str(key)


def _statement_columns(orm_execute_state: ORMExecuteState) -> frozenset[str]:
    """Имена колонок, которые задаёт оператор UPDATE / INSERT, исполняемый сессией.

    Ключи `values(…)`, `ordered_values(…)`, многострочных `values([…])`,
    `from_select([…])` и параметров исполнения (словарь или список словарей —
    групповой UPDATE по ключу, групповой INSERT). У оператора без значений —
    пустое множество.
    """
    statement = orm_execute_state.statement
    keys: list[object] = []
    if isinstance(statement, (Update, Insert)):
        keys.extend(statement._values or ())
        keys.extend(key for key, _value in statement._ordered_values or ())
        positional = list(statement.table.c.keys())
        for rows in statement._multi_values or ():
            for row in rows:
                if isinstance(row, dict):
                    keys.extend(row)
                else:
                    keys.extend(positional[: len(row)])
        if isinstance(statement, Insert):
            keys.extend(statement._select_names or ())
    parameters = orm_execute_state.parameters
    if isinstance(parameters, dict):
        keys.extend(parameters)
    else:
        for row in parameters or ():
            if isinstance(row, dict):
                keys.extend(row)
    return frozenset(_column_name(key) for key in keys)


def _refuse_unscoped_statement(orm_execute_state: ORMExecuteState) -> None:
    """Слушатель `do_orm_execute`: UPDATE / INSERT колонки номера без разрешения."""
    if not (orm_execute_state.is_update or orm_execute_state.is_insert):
        return
    if _WRITER_ACTIVE.get():
        return
    statement = orm_execute_state.statement
    if not isinstance(statement, (Update, Insert)):
        return
    if not statement.table.is_derived_from(_ACCOUNTS_TABLE):
        return
    if _statement_columns(orm_execute_state) & set(GUARDED_COLUMNS):
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)


event.listen(Session, "before_flush", _refuse_unscoped_flush)
event.listen(Session, "do_orm_execute", _refuse_unscoped_statement)

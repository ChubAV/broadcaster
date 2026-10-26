"""Защита единственного писателя номера НА ИСПОЛНЕНИИ (О-23 (а), свойство 3; D-07, D-13).

ЗАЧЕМ. Правило «ручной номер автоисточник не затирает» (D-07) держится, пока
писатель один (D-13): второй писатель — форма, мастер, скрипт дозаполнения —
своей записью в колонку обходит условный UPDATE писателя разом. До плана 16-51
единственность держал только статический гейт
(`tests/test_application/test_phone_single_writer_gate.py`), который судит
ИСХОДНИК, и его обещание «любое написание записи найдено» за раунды 6–10 не
сошлось: каждый новый корпус находил следующее написание динамического вызова.
Решение владельца О-23 (а), 2026-10-22, свойство 3: запись колонок номера вне
модуля-писателя `app/application/accounts/phone.py` отказывает НА ИСПОЛНЕНИИ.
Обещание названо через механизм, а не через написание: отказывает каждая
запись, которая проходит через события атрибута, проверку сессии перед
сбросом, `Session.execute` или курсор `Connection` SQLAlchemy конструкцией DML
(UPDATE / INSERT), — со значениями из литерала, переменной, параметра или
цикла одинаково. Прежняя, более широкая формулировка снята (см. летопись в
конце шапки); чего защита не судит — в разделе ГРАНИЦА.

ЧТО ОТКАЗЫВАЕТ — ЧЕТЫРЕ ЛИНИИ, все вне разрешения писателя, все исключением
`PhoneWriteOutsideWriter` с постоянным текстом `PHONE_WRITE_OUTSIDE_WRITER`:
1. события атрибута `set`, `remove`, `modified` обеих колонок
   (`GUARDED_COLUMNS`): присваивание, аргумент конструктора, `setattr`,
   `set_attribute`, дескриптор колонки, `object.__setattr__`, `del`,
   `flag_modified` — отказ до того, как значение попало в объект;
2. `before_flush` сессии: объект `MessengerAccount` из `session.new` /
   `session.dirty`, у которого история колонки номера несёт добавленное
   значение, — например, значение, поставленное под разрешением, а сброшенное
   без него. Новый объект (`session.new`) судится ещё и по ЗНАЧЕНИЯМ
   (`state.dict`): номер или поднятый признак «ручной» отказывает, потому что
   INSERT ORM собирается из словаря объекта, а `set_committed_value` истории не
   оставляет (WR-36, план 16-58);
3. `do_orm_execute` сессии: оператор UPDATE / INSERT по таблице
   `messenger_accounts`, задающий колонку номера, — в `values(…)`,
   `ordered_values(…)`, многострочных `values([…])`, `from_select([…])` или в
   параметрах исполнения (групповой UPDATE по ключу, групповой INSERT);
4. `before_cursor_execute` класса `sqlalchemy.engine.Engine` (план 16-58;
   О-25 (а), свойство 4): скомпилированный `Update` / `Insert` таблицы
   `messenger_accounts`, задающий колонку номера. Таблица судится по ИМЕНИ, а
   не по тождеству объекта: видны лёгкая `sqlalchemy.table(…)`, отражённая
   таблица и таблица миграции (копия batch Alembic
   `_alembic_tmp_messenger_accounts` — другое имя). UPDATE и ветка
   `ON CONFLICT DO UPDATE SET` (`on_conflict_do_update`) отказывают при любом
   значении — очистка номера тоже запись (D-13); INSERT судится по значениям
   строк параметров (`compiled_parameters`): номер не `None` или признак
   «ручной» истинен — отказ, неизвестный номер и `phone_is_manual = false`
   законны. Линия закрывает `bulk_update_mappings`, `bulk_insert_mappings`,
   `bulk_save_objects`, оператор через `session.connection()` или движок, Core
   `insert` / `update` с параметрами исполнения и upsert: она судит оператор на
   курсоре, а не исходник.
Строка в базе после отказа прежняя: до оператора записи дело не доходит.
Линии не заменяют друг друга: первые три отказывают раньше и называют путь
ORM, линия движка — последняя, на курсоре.

ГДЕ СТОИТ ЛИНИЯ ДВИЖКА. Слушатель регистрируется на КЛАССЕ `Engine` при ввозе
этого модуля, а не на конкретном движке: async-движок оборачивает синхронный, и
слушатель класса стоит на каждом движке процесса, ввозящего `app.models` (веб,
воркеры Celery, скрипты, Alembic, тестовые движки), — и на движке, созданном до
ввоза, тоже (замер планирования 2026-10-26 и замер исполнения плана 16-58:
синхронный и async-движки, созданные до и после регистрации). Отдельной
регистрации в `app/database.py` и `tests/conftest.py` нет. На каждом операторе
сначала идут дешёвые проверки — признак INSERT / UPDATE контекста, тип
оператора, имя таблицы — и лишь затем разбор колонок: SELECT, DELETE, DDL и
чужие таблицы выходят сразу, оператор ради суда не компилируется.

ЧЕМ РАЗРЕШЕНО. `writer_scope()` — менеджер контекста над переменной контекста
`_WRITER_ACTIVE`; снимается токеном в `finally`, и после исключения внутри
тоже. Переменная контекста, поставленная в корутине перед
`await session.execute(…)`, видна слушателям внутри greenlet SQLAlchemy. В
разрешение входит ТОЛЬКО писатель — вокруг своих операторов UPDATE; вход в него
из иного места `app/` и `scripts/` краснит гейт писателя (правило плана 16-55).
Тесты, строящие невозможное состояние ради доказательства CHECK базы, входят в
него сами: они моделируют писателя с ошибкой, а не обходят защиту.

ПОЧЕМУ В ПАКЕТЕ МОДЕЛЕЙ. Слушатели регистрируются при ввозе этого модуля, а
его ввозит последняя строка `app/models/__init__.py`: ввоз любого модуля
моделей сначала исполняет пакет, поэтому защита стоит в каждом процессе, где
есть модель (веб, воркеры Celery, скрипты, Alembic). Разрешение живёт здесь, а
не у писателя: писатель (`app/application/…`) ввозит модели, и обратный ввоз из
пакета моделей дал бы цикл.

ГРАНИЦА, НАЗВАННАЯ ПРЯМО (по замеру исполнения плана 16-58, а не по замыслу).
Защита НЕ судит:
- текст SQL — `text("UPDATE …")` через сессию и через соединение (конструкции
  DML нет: `compiled.statement` — `TextClause`, признаки INSERT / UPDATE
  ложны) и `exec_driver_sql` (оператор без компиляции): сырой SQL держит не
  исполнение, а исходник — статический гейт писателя (литерал SQL — вид 5) и
  канал запрета динамической конструкции (вычисленный текст SQL; план 16-53,
  план 16-55);
- сырое соединение DBAPI (`get_raw_connection()`, `driver_connection`) —
  мимо движка, событий нет;
- `set_committed_value` на СОХРАНЁННОМ объекте — меняет только объект в
  памяти и оператора не порождает (писатель пользуется им ровно для зеркала
  уже записанного); на НОВОМ объекте он отказывает второй и четвёртой линией;
- процесс, не ввозящий `app.models`, — слушателей в нём нет.

ЦЕНА — ОТКАЗ В ЗАКРЫТУЮ. Вставка таблицы аккаунтов, задающая колонку номера,
у которой значение этой колонки на курсоре не находится в строке параметров по
ключу колонки — многострочный `values([…])` (привязки с суффиксом `_m0`, …),
`from_select`, выражение SQL (`sqlalchemy.null()` и иные), — отказывает и БЕЗ
номера: судить её значение линия не может, а молча пропустить — значит снова
обещать больше поведения. Ветка вставки после `VALUES`, которую линия не
читает (не `ON CONFLICT DO UPDATE` / `DO NOTHING` SQLite и PostgreSQL), судится
как задающая обе колонки номера — тоже отказ в закрытую. Цена закреплена
таблицей `CLOSED_FAILING_WRITES` модуля
`tests/test_application/test_phone_writer_runtime_guard.py`; в `app/` и
`scripts/` таких вставок нет (замер планирования 2026-10-26: `insert(`,
`bulk_`, `.connection()` — 0).

Текст отказа — без значения колонки и без номера (D-11); вызовов журнала в
модуле нет.

Летопись (снятая фраза обещания). До плана 16-58 шапка обещала, что запись
колонок номера вне писателя отказывает «в момент записи, каким бы написанием
она ни была сделана», и относила `set_committed_value`, `bulk_*`, оператор
через соединение, сырой SQL и ветку `ON CONFLICT` к границе, которую «держат
статический гейт писателя (виды 2–6) и запрет динамической конструкции».
Верификация раунда 11 (`553933d8`, гэп 3) и повторное ревью раунда 10 (CR-08,
WR-36) показали: строки из переменной, параметра или цикла в этих путях не
судит ни предикат гейта, ни канал запрета, а `set_committed_value` на НОВОМ
объекте порождает INSERT с номером и `phone_is_manual = 1` (ущерб D-07).
Решение владельца О-25 (а), свойство 4, закрыло их линией движка и судом
нового объекта по значениям; обещание переписано через механизм (свойство 5),
а фраза о любом написании оставлена только здесь, с причиной.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects.postgresql.dml import (
    OnConflictDoNothing as PostgresOnConflictDoNothing,
)
from sqlalchemy.dialects.postgresql.dml import (
    OnConflictDoUpdate as PostgresOnConflictDoUpdate,
)
from sqlalchemy.dialects.sqlite.dml import OnConflictDoNothing as SqliteOnConflictDoNothing
from sqlalchemy.dialects.sqlite.dml import OnConflictDoUpdate as SqliteOnConflictDoUpdate
from sqlalchemy.engine import Engine
from sqlalchemy.orm import ORMExecuteState, Session, UOWTransaction
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.sql.dml import Insert, Update
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Alias, TableClause

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
    `writer_scope()`, а сброшенное вне его, тоже отказывает. Новый объект
    (`session.new`) судится по ЗНАЧЕНИЯМ, а не только по истории: INSERT ORM
    собирает из `state.dict`, а `set_committed_value` истории не оставляет
    (WR-36) — номер или поднятый признак «ручной» у нового объекта отказывает.
    """
    if _WRITER_ACTIVE.get():
        return
    for instance in session.new:
        if not isinstance(instance, MessengerAccount):
            continue
        values = sa_inspect(instance).dict
        if values.get("phone") is not None or values.get("phone_is_manual"):
            raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
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


# Таблица аккаунтов судится ПО ИМЕНИ, а не по тождеству объекта: так видны
# лёгкая `sqlalchemy.table(…)`, отражённая таблица и таблица миграции.
_ACCOUNTS_TABLE_NAME = MessengerAccount.__tablename__
_GUARDED = frozenset(GUARDED_COLUMNS)
_UPSERT_UPDATES = (SqliteOnConflictDoUpdate, PostgresOnConflictDoUpdate)
_UPSERT_NOTHING = (SqliteOnConflictDoNothing, PostgresOnConflictDoNothing)


def _target_table(table: object) -> object:
    """Таблица оператора без псевдонимов: `Alias` разворачивается до своей таблицы."""
    while isinstance(table, Alias):
        table = table.element
    return table


def _cursor_columns(
    statement: Insert | Update, compiled: object
) -> tuple[frozenset[str], frozenset[str]]:
    """Колонки, которые задаёт скомпилированный оператор, и колонки ветки upsert.

    Первая часть — ключи `values(…)`, `ordered_values(…)`, строк многострочных
    `values([…])`, `from_select([…])` и ключи параметров исполнения
    (`compiled.column_keys`), пересечённые с колонками таблицы: имя привязки,
    совпадающее с колонкой, в `WHERE` оператора DML SQLAlchemy запрещает.
    Вторая — ключи `ON CONFLICT DO UPDATE SET`; ветка, которую защита не
    читает, судится как задающая обе колонки номера (отказ в закрытую).
    """
    table = _target_table(statement.table)
    positional = list(table.c.keys())
    keys: list[object] = []
    keys.extend(statement._values or ())
    keys.extend(key for key, _value in statement._ordered_values or ())
    for rows in statement._multi_values or ():
        for row in rows:
            if isinstance(row, dict):
                keys.extend(row)
            else:
                keys.extend(positional[: len(row)])
    upsert: list[object] = []
    if isinstance(statement, Insert):
        keys.extend(statement._select_names or ())
        post_values = statement._post_values_clause
        if isinstance(post_values, _UPSERT_UPDATES):
            upsert.extend(key for key, _value in post_values.update_values_to_set)
        elif post_values is not None and not isinstance(post_values, _UPSERT_NOTHING):
            upsert.extend(GUARDED_COLUMNS)
    names = {_column_name(key) for key in keys}
    names.update(set(positional) & set(compiled.column_keys or ()))
    return frozenset(names), frozenset(_column_name(key) for key in upsert)


def _refuse_unscoped_cursor(
    conn: object,
    cursor: object,
    statement: str,
    parameters: object,
    context: object,
    executemany: bool,
) -> None:
    """Слушатель `before_cursor_execute` класса `Engine`: запись колонки номера мимо событий ORM."""
    if context is None or not (context.isinsert or context.isupdate):
        return
    compiled = context.compiled
    if compiled is None:
        return
    dml = compiled.statement
    if not isinstance(dml, (Update, Insert)):
        return
    table = _target_table(dml.table)
    if not isinstance(table, TableClause) or table.name != _ACCOUNTS_TABLE_NAME:
        return
    if _WRITER_ACTIVE.get():
        return
    columns, upsert = _cursor_columns(dml, compiled)
    if upsert & _GUARDED:
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
    written = columns & _GUARDED
    if not written:
        return
    if isinstance(dml, Update):
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
    for row in context.compiled_parameters or ({},):
        if any(column not in row for column in written):
            raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
        if row.get("phone") is not None or row.get("phone_is_manual"):
            raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)


event.listen(Session, "before_flush", _refuse_unscoped_flush)
event.listen(Session, "do_orm_execute", _refuse_unscoped_statement)
event.listen(Engine, "before_cursor_execute", _refuse_unscoped_cursor)

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

import contextlib
import functools
import operator
import types

import pytest
from sqlalchemy import delete, func, insert, literal, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified, set_attribute, set_committed_value

from app.application.accounts.phone import PhoneWrite, fill_reported_phone
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

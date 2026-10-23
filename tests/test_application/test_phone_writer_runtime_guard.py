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

import pytest
from sqlalchemy import select

from app.application.accounts.phone import PhoneWrite, fill_reported_phone
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.services.phone import normalize_reported

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

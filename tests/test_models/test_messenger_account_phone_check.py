"""ИНВАРИАНТ В СХЕМЕ: `phone_is_manual = true` несовместимо с `phone IS NULL`.

Предмет файла — не поведение обработчика, а СВОЙСТВО ТАБЛИЦЫ (D-03). Признак
«номер указал пользователь» существует ради одного правила: автоисточник такой
номер не затирает (D-07). Признак без номера означал бы «пользователь указал
ничто» — состояние, в котором автоисточник навсегда лишён права записать номер
(условная запись требует `NOT phone_is_manual`), а показывать нечего. Строка
молча и навсегда осталась бы «неизвестен».

Прикладная проверка в модуле-писателе (`app/application/accounts/phone.py`,
план 16-05) делает состояние НЕДОСТИЖИМЫМ ЧЕРЕЗ ПРИЛОЖЕНИЕ, а не НЕВОЗМОЖНЫМ:
прямой psql, ручной UPDATE на бою, миграция данных и любой будущий второй
писатель обходят её разом. Слово «невозможно» правдиво в одном месте — в
ограничении СУБД. Довод тот же, что у `0021`/`0022`, и он про класс.

ЧТО ИМЕННО ЗАПРЕЩЕНО, СЛОВАМИ. Запрещена ОДНА пара из четырёх. Законны:

  - `phone IS NULL`, `phone_is_manual = false` — «неизвестен», состояние
    каждой строки сразу после ревизии `0023` и после очистки номера;
  - номер задан, `phone_is_manual = false` — номер сообщил автоисточник;
  - номер задан, `phone_is_manual = true` — номер указал пользователь.

⚠️ ЗАПРЕТ ДЕРЖИТСЯ С ОБЕИХ СТОРОН UPDATE. Поднять признак без номера нельзя, и
стереть номер под поднятым признаком — тоже. Второе — не педантизм: из него
следует, что очистка номера обязана менять ОБЕ колонки одним оператором
(`phone = NULL, phone_is_manual = false`), иначе ограничение её отвергнет.

ЭТОТ ФАЙЛ ПРОВЕРЯЕТ МОДЕЛЬНУЮ ПОЛОВИНУ. Схему суиты строит
`Base.metadata.create_all` (tests/conftest.py), то есть ИЗ МОДЕЛИ, и SQLite
исполняет CHECK сам. Половина ревизии — у
`tests/test_migrations/test_0023_messenger_account_phone.py`; без неё
ограничение существовало бы в модели и отсутствовало в очереди накатов, а это
расхождение для остальной суиты невидимо ПО ПОСТРОЕНИЮ.
"""

import pytest
from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.exc import IntegrityError

from app.models.messenger_account import MessengerAccount
from app.models.user import User

CONSTRAINT_NAME = "ck_messenger_accounts_manual_requires_phone"
NUMBER = "+79991234567"


async def _user(db_session) -> User:
    user = User(email="phone-check@test.com", name="Владелец", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    return user


def _account(user: User, **fields) -> MessengerAccount:
    fields.setdefault("type", "tg_user")
    return MessengerAccount(
        user_id=user.id, credentials="cred", status="active", **fields
    )


@pytest.mark.asyncio
async def test_a_manual_flag_without_a_number_is_refused_on_insert(db_session):
    """⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ: такую строку не принимает САМА ТАБЛИЦА.

    Запись идёт мимо модуля-писателя — прямым ORM-вызовом, как её сделал бы
    ручной скрипт обслуживания или писатель, не знающий про D-03. Именно этот
    путь прикладная проверка не покрывает и покрыть не может.
    """
    user = await _user(db_session)
    db_session.add(_account(user, phone=None, phone_is_manual=True))

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_raising_the_flag_without_a_number_is_refused_on_update(db_session):
    """Первая сторона UPDATE: «неизвестен» нельзя пометить ручным."""
    user = await _user(db_session)
    account = _account(user)
    db_session.add(account)
    await db_session.flush()

    account.phone_is_manual = True

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_erasing_the_number_under_a_raised_flag_is_refused(db_session):
    """Вторая сторона UPDATE: номер нельзя стереть, оставив признак поднятым.

    Отсюда следствие для писателя (план 16-05): очистка меняет обе колонки ОДНИМ
    оператором, иначе её отвергнет ограничение.
    """
    user = await _user(db_session)
    account = _account(user, phone=NUMBER, phone_is_manual=True)
    db_session.add(account)
    await db_session.flush()

    account.phone = None

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "phone,is_manual,case",
    [
        pytest.param(None, False, "неизвестен", id="unknown"),
        pytest.param(NUMBER, False, "сообщён автоисточником", id="reported"),
        pytest.param(NUMBER, True, "указан пользователем", id="manual"),
    ],
)
async def test_the_three_legal_pairs_are_accepted(
    db_session, phone, is_manual, case
):
    """⚠️ БЕЗ ЭТОГО ТЕСТА ОГРАНИЧЕНИЕ «ЗАПРЕТИТЬ ВСЁ» БЫЛО БЫ ЗЕЛЁНЫМ.

    Запрещена ОДНА пара из четырёх. Особенно важна первая строка: «неизвестен» —
    состояние каждой существующей строки после ревизии, и ограничение, задевшее
    его, не дало бы ревизии пройти вовсе.
    """
    user = await _user(db_session)
    db_session.add(_account(user, phone=phone, phone_is_manual=is_manual))

    await db_session.flush()  # падение здесь и есть провал теста (id называет пару)


@pytest.mark.asyncio
async def test_a_new_account_has_an_unknown_number_by_default(db_session):
    """Аккаунт, созданный без упоминания номера, — «неизвестен», а не «ручной»."""
    user = await _user(db_session)
    account = _account(user)
    db_session.add(account)
    await db_session.flush()
    await db_session.refresh(account)

    assert account.phone is None
    assert account.phone_is_manual is False


@pytest.mark.asyncio
async def test_two_accounts_share_one_number(db_session):
    """Уникальности по номеру нет (D-02): один SIM законно даёт TG и WA разом."""
    user = await _user(db_session)
    db_session.add_all(
        [
            _account(user, type="tg_user", phone=NUMBER),
            _account(user, type="wa", phone=NUMBER),
        ]
    )

    await db_session.flush()  # падение здесь и есть провал теста


def test_the_column_forms_postgres_would_distinguish():
    """Форма колонок, которую SQLite не проверяет, а PostgreSQL проверяет.

    SQLite длину `VARCHAR` не соблюдает вовсе, поэтому утверждение о типе
    снимается с самой таблицы модели: иначе `phone` мог бы уехать в
    `String(15)` и отвергать на бою законный номер из 15 цифр с `+` (D-14).
    """
    columns = MessengerAccount.__table__.c

    assert isinstance(columns.phone.type, String)
    assert columns.phone.type.length == 16
    assert columns.phone.nullable is True

    assert isinstance(columns.phone_is_manual.type, Boolean)
    assert columns.phone_is_manual.nullable is False
    assert columns.phone_is_manual.server_default is not None


def test_the_constraint_is_named_and_belongs_to_the_model():
    """Имя ограничения — общий шов модели и ревизии, и он проверяется.

    Безымянный CHECK получил бы от СУБД произвольное имя, и `downgrade` ревизии
    не смог бы его снять, а разбор отказа на бою не смог бы его назвать.
    """
    names = {
        constraint.name
        for constraint in MessengerAccount.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert CONSTRAINT_NAME in names, (
        f"в модели нет именованного CHECK {CONSTRAINT_NAME!r}; найдено: {names}"
    )

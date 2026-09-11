"""ИНВАРИАНТ В СХЕМЕ: `is_active = true` несовместимо с `next_run_at IS NULL`.

Предмет файла — не поведение обработчика, а СВОЙСТВО ТАБЛИЦЫ. Разница
существенная и ради неё файл и заведён.

Правка 7833844 закрыла единственное место записи, которое такую строку
порождало, и `test_schedules_api_create_completeness.py` держит его закрытым.
Но прикладная проверка делает состояние НЕДОСТИЖИМЫМ ЧЕРЕЗ ПРИЛОЖЕНИЕ, а не
НЕВОЗМОЖНЫМ: прямой psql, ручной UPDATE в проде, миграция данных и любой
будущий восьмой писатель проходят мимо всех семи существующих проверок разом.
Слово «невозможно» правдиво ровно в одном месте — в ограничении СУБД. Тот же
довод выписан в шапке ревизии `0021`, и он не про платежи, а про класс.

⚠️ ПОЧЕМУ ЭТО НЕ ПЕРЕСТРАХОВКА, А ЗАКРЫТИЕ ЖИВОЙ ДЫРЫ. На момент этого файла
форма `is_active=true` + `next_run_at=NULL` ДОСТИЖИМА ЧЕРЕЗ JSON-ВХОД И ПОСЛЕ
правки 7833844: день недели вне 0..6 непуст, поэтому `is_schedule_complete`
отвечает True, а `compute_next_run_at` не находит такого дня в своём окне и
возвращает None. Вход закрывается в этом же круге
(`tests/test_routes/test_schedules_api_value_domain.py`), и порядок здесь не
случаен: ограничение без той правки превратило бы тихую мёртвую строку в 500 на
живом пользователе.

ЧТО ИМЕННО ЗАПРЕЩЕНО, СЛОВАМИ. Запрещена ОДНА пара значений. Разрешены все
остальные три:

  - `is_active=false`, `next_run_at IS NULL` — приостановленное расписание,
    обычнейшее состояние (тумблер обнуляет момент запуска, WR-06);
  - `is_active=false`, `next_run_at` задан — законно и встречается у строки,
    которую приостановили между пересчётами;
  - `is_active=true`, `next_run_at` задан — работающее расписание.

⚠️ ГРАНИЦА: НЕПОЛНОТА ЗДЕСЬ НИ ПРИ ЧЁМ. Ограничение НЕ требует заполненности
(D-08) и не знает о ней: строка с пустыми группами, но выключенная и без момента
запуска, законна для него. Полноту стережёт `is_schedule_complete` на входах;
схема стережёт ровно одно — чтобы включённое расписание нельзя было сохранить
без момента, в который оно сработает.

ЭТОТ ФАЙЛ ПРОВЕРЯЕТ МОДЕЛЬНУЮ ПОЛОВИНУ. Схему суиты строит
`Base.metadata.create_all` (tests/conftest.py), то есть ИЗ МОДЕЛИ, и SQLite
исполняет CHECK самостоятельно. Половина ревизии — у
`tests/test_migrations/test_0022_schedules_active_requires_next_run.py`: без неё
ограничение существовало бы в модели и отсутствовало в очереди накатов, а
расхождение модели с очередью для остальной суиты невидимо ПО ПОСТРОЕНИЮ
(тот же довод, что в шапке `test_model_matches_head.py`).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

CONSTRAINT_NAME = "ck_schedules_active_requires_next_run"


async def _ad_and_account(db_session):
    user = User(email="domain@test.com", name="Владелец", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    ad = Ad(user_id=user.id, title="Объявление", text="Текст")
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="cred", status="active"
    )
    db_session.add_all([ad, account])
    await db_session.flush()
    return ad, account


@pytest.mark.asyncio
async def test_an_active_schedule_without_a_next_run_is_refused_by_the_schema(
    db_session,
):
    """⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ: такую строку не принимает САМА ТАБЛИЦА.

    Запись идёт мимо всех обработчиков — прямым ORM-вызовом, как её сделал бы
    ручной скрипт обслуживания или новый писатель, не знающий про D-08. Именно
    этот путь прикладная проверка не покрывает и покрыть не может.
    """
    ad, account = await _ad_and_account(db_session)

    db_session.add(
        Schedule(
            ad_id=ad.id,
            account_id=account.id,
            group_ids=[1],
            days_of_week=[0],
            times_of_day=["09:00"],
            is_active=True,
            next_run_at=None,
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_the_column_default_alone_cannot_smuggle_the_row_in(db_session):
    """Та же строка, но `is_active` НЕ ПЕРЕДАН — ровно механизм дефекта 7833844.

    Отдельный тест, а не повтор предыдущего: дыра состояла именно в ОТСУТСТВИИ
    аргумента, из-за которого бралось умолчание колонки `default=True`. Проверка
    с явным `is_active=True` эту ветвь не трогает вовсе — умолчание в ней не
    участвует.
    """
    ad, account = await _ad_and_account(db_session)

    db_session.add(
        Schedule(
            ad_id=ad.id,
            account_id=account.id,
            group_ids=[1],
            days_of_week=[0],
            times_of_day=["09:00"],
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_an_active_schedule_moved_to_a_null_next_run_is_refused_too(db_session):
    """Запрет держится и на UPDATE, а не только на вставке.

    Утверждение не декоративное: живую строку убивает именно обновление —
    расписание было отправляемым, ему обнулили момент запуска, и оно замолчало.
    CHECK в SQLite и в PostgreSQL проверяется на каждой записи строки, и это
    свойство закрепляется здесь, а не предполагается.
    """
    ad, account = await _ad_and_account(db_session)
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[1],
        days_of_week=[0],
        times_of_day=["09:00"],
        is_active=True,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(schedule)
    await db_session.flush()

    schedule.next_run_at = None

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "is_active,has_next_run,case",
    [
        pytest.param(False, False, "приостановленное без момента запуска", id="paused_null"),
        pytest.param(False, True, "приостановленное с сохранённым моментом", id="paused_with_next_run"),
        pytest.param(True, True, "работающее расписание", id="active_with_next_run"),
    ],
)
async def test_the_three_legal_combinations_are_accepted(
    db_session, is_active, has_next_run, case
):
    """⚠️ БЕЗ ЭТОГО ТЕСТА ОГРАНИЧЕНИЕ «ЗАПРЕТИТЬ ВСЁ» БЫЛО БЫ ЗЕЛЁНЫМ.

    Запрещена ОДНА пара из четырёх. Перечисление остальных трёх поимённо — это
    то, что отличает проверку ограничения от проверки «база что-то не приняла»;
    особенно важна первая строка: приостановленное расписание без момента
    запуска — самое частое состояние в таблице, и ограничение, задевшее его,
    сломало бы тумблер целиком.
    """
    ad, account = await _ad_and_account(db_session)

    db_session.add(
        Schedule(
            ad_id=ad.id,
            account_id=account.id,
            group_ids=[1],
            days_of_week=[0],
            times_of_day=["09:00"],
            is_active=is_active,
            next_run_at=(
                datetime.now(timezone.utc) + timedelta(hours=1) if has_next_run else None
            ),
        )
    )

    await db_session.flush()  # падение здесь и есть провал теста


def test_the_constraint_is_named_and_belongs_to_the_model():
    """Имя ограничения — общий шов модели и ревизии, и он проверяется.

    Безымянный CHECK получил бы от СУБД произвольное имя, и `downgrade` ревизии
    не смог бы его снять, а разбор отказа на бою не смог бы его назвать. Имя
    выписано здесь литералом намеренно: ревизия по правилу проекта не
    импортирует из `app.*`, поэтому единственное место, где две половины
    сверяются, — тест.
    """
    from sqlalchemy import CheckConstraint

    names = {
        constraint.name
        for constraint in Schedule.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert CONSTRAINT_NAME in names, (
        f"в модели нет именованного CHECK {CONSTRAINT_NAME!r}; найдено: {names}"
    )

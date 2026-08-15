"""D-05: выключенная группа не получает задач отправки при диспетчеризации.

Это второе — и последнее — вторжение milestone v2.0 в боевой пайплайн отправки
(первое, D-01, живёт рядом в test_collect_due_draft.py), поэтому тест стоит
вплотную к нему, а не на страничном слое.

Ключевых утверждений файла ДВА, и «задача не создана» — ни одно из них:

* `test_next_run_at_moves_forward_when_every_group_is_off`. Пропускается ГРУППА,
  а не расписание: расписание остаётся живым и продолжает двигать `next_run_at`.
  Условие, поставленное на уровень расписания (или в `WHERE` выборки), тоже не
  создало бы задач, но оставило бы `next_run_at` в прошлом — и включение группы
  обратно выстрелило бы всеми накопленными пропущенными слотами сразу.
* `test_skipping_writes_nothing_to_the_send_log`. Пропуск ТИХИЙ (D-06): история
  обязана отражать реальные попытки отправки, а не намерения. Запись в `SendLog`
  со специальным статусом выглядела бы для пользователя как неудачная отправка
  в группу, в которую он сам запретил слать.

Пара к ним — `test_enabling_the_group_resumes_dispatch`: без неё все утверждения
о пропуске зеленели бы на функции, не создающей задач вовсе.

СОСЕДНИЙ ПРОПУСК — висячая ссылка (секция «Пропуск несуществующей группы»).
Идентификатор, которому не соответствует ни одной строки, — не то же самое, что
выключенная группа, и раньше он проходил насквозь: задача создавалась, а дефект
становился ТИХИМ. Для wa/max в очередь уезжал адресат `group_external_id=None`,
для tg_user — журнальная запись «Missing ad, group, or account», то есть отказ
отправки без причины. Тесты этой секции держат оба пропуска различимыми.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.scheduling.use_cases import collect_due_schedules
from app.constants import AD_STATUS_PUBLISHED
from app.database import Base
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.user import User

# Каждый день недели и два времени в сутках: `compute_next_run_at` при таком
# наборе всегда находит строго будущий слот, поэтому утверждение о сдвиге не
# зависит от того, в какой момент суток запущены тесты.
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]
TWO_TIMES = ["00:30", "12:30"]

# Все три канала: условие пропуска обязано стоять ВЫШЕ ветвления по типу
# аккаунта. Врезка внутри ветки WA/MAX (там, где группа уже запрашивалась)
# оставила бы Telegram без пропуска — и это самый населённый канал продукта.
ACCOUNT_TYPES = ["tg_user", "wa", "max"]


async def _allow_everything(session, user_id: int, action: str):
    return True, "ok"


def _as_utc(value: datetime) -> datetime:
    """SQLite не хранит смещение — восстанавливаем UTC для сравнения."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class _Db:
    """Собственный движок: collect_due_schedules коммитит сама."""

    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def __aenter__(self) -> AsyncSession:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.session = factory()
        return self.session

    async def __aexit__(self, *exc):
        await self.session.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()


async def _seed(
    session: AsyncSession,
    *,
    account_type: str = "tg_user",
    group_flags: list[bool],
) -> tuple[Schedule, list[Group]]:
    """Одно просроченное расписание с группами в состояниях `group_flags`."""
    user = User(email="inactive@test.com", password_hash="x", name="U")
    session.add(user)
    await session.commit()

    ad = Ad(
        user_id=user.id,
        title="T",
        text="Body",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    account = MessengerAccount(
        user_id=user.id, type=account_type, credentials="sess", status="active"
    )
    session.add_all([ad, account])
    await session.commit()

    groups = []
    for index, is_active in enumerate(group_flags):
        group = Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type=account_type,
            group_external_id=f"-10{index}",
            name=f"G{index}",
            is_active=is_active,
        )
        session.add(group)
        groups.append(group)
    await session.commit()

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[g.id for g in groups],
        days_of_week=ALL_DAYS,
        times_of_day=TWO_TIMES,
        is_active=True,
        # Просрочено на сутки: именно такое расписание и выстрелило бы залпом,
        # если бы пропуск был сделан на уровне расписания.
        next_run_at=datetime.now(timezone.utc) - timedelta(days=1),
        timezone="UTC",
    )
    session.add(schedule)
    await session.commit()
    return schedule, groups


# --- Пропуск выключенной группы ----------------------------------------------


@pytest.mark.asyncio
async def test_only_the_active_group_of_a_schedule_gets_a_task():
    """Пропускается ГРУППА, а не расписание: соседняя активная задачу получает.

    Расписание с двумя группами — минимальный посев, различающий пропуск группы
    и пропуск расписания: условие, поставленное на расписание, обнулило бы обе.
    """
    async with _Db() as session:
        _, groups = await _seed(session, group_flags=[True, False])
        active, inactive = groups

        tasks = await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        assert [t.group_id for t in tasks] == [active.id], (
            "состав задач не совпал с составом ВКЛЮЧЁННЫХ групп расписания"
        )
        assert inactive.id not in [t.group_id for t in tasks]


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ACCOUNT_TYPES)
async def test_inactive_group_produces_no_task_for_any_channel(account_type: str):
    """Пропуск работает на всех трёх каналах, а не только на WA/MAX.

    Объект группы до правки запрашивался ТОЛЬКО в ветке WA/MAX. Условие,
    оставленное внутри неё, пропустило бы Telegram — и надпись экрана
    «выключенные группы пропускаются при рассылке» врала бы большинству
    пользователей.
    """
    async with _Db() as session:
        await _seed(session, account_type=account_type, group_flags=[False])

        tasks = await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        assert tasks == [], f"выключенная группа получила задачу на канале {account_type}"


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ACCOUNT_TYPES)
async def test_enabling_the_group_resumes_dispatch(account_type: str):
    """Парный тест: без него утверждения о пропуске зеленели бы вакуумно.

    Тумблер обратим (D-08): включение группы немедленно возобновляет рассылку,
    потому что состав расписания выключением не менялся (D-05).
    """
    async with _Db() as session:
        schedule, (group,) = await _seed(
            session, account_type=account_type, group_flags=[False]
        )

        assert (
            await collect_due_schedules(
                session, now=datetime.now(timezone.utc), check_limit=_allow_everything
            )
            == []
        )

        # Первый сбор УЖЕ сдвинул next_run_at в будущее — расписание живо, и это
        # ровно то, что утверждает test_next_run_at_moves_forward_when_every_
        # group_is_off. Поэтому перед вторым сбором расписание возвращается в
        # просроченное состояние: иначе второй вызов не выбрал бы его вовсе, и
        # тест зеленел бы (или краснел) по причине, к пропуску не относящейся.
        group.is_active = True
        schedule.next_run_at = datetime.now(timezone.utc) - timedelta(days=1)
        await session.commit()

        tasks = await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        assert [t.group_id for t in tasks] == [group.id], (
            f"включённая обратно группа не возобновила рассылку на канале {account_type}"
        )


# --- Пропуск несуществующей группы --------------------------------------------

# Идентификатор, которого в таблице заведомо нет. Расписание переживает удаление
# группы (маршрут удаления чистит `group_ids`, но ревизии, ручные правки и
# рассинхрон пользователей — нет), поэтому висячая ссылка достижима.
MISSING_GROUP_ID = 987654


@pytest.mark.asyncio
@pytest.mark.parametrize("account_type", ACCOUNT_TYPES)
async def test_missing_group_produces_no_task_for_any_channel(account_type: str):
    """Строки нет — задачи нет, ни на одном канале.

    До правки задача создавалась: ветка пропуска читалась как
    `if group and not group.is_active`, и `group is None` её не проходил. Для
    wa/max в Redis уезжал payload с `group_external_id=None` — воркер получал
    адресата `null`; для tg_user задача доезжала до `send_message_once` и
    становилась записью журнала «Missing ad, group, or account».
    """
    async with _Db() as session:
        schedule, _ = await _seed(
            session, account_type=account_type, group_flags=[True]
        )
        schedule.group_ids = [MISSING_GROUP_ID]
        await session.commit()

        tasks = await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        assert tasks == [], (
            f"висячая ссылка получила задачу отправки на канале {account_type}"
        )


@pytest.mark.asyncio
async def test_missing_group_does_not_take_down_its_neighbours():
    """Пропускается ГРУППА, а не расписание: соседняя живая строка шлёт дальше.

    Отказ всего расписания из-за одной висячей ссылки был бы вторым тихим
    дефектом на месте первого.
    """
    async with _Db() as session:
        schedule, (alive,) = await _seed(session, group_flags=[True])
        schedule.group_ids = [MISSING_GROUP_ID, alive.id]
        await session.commit()

        tasks = await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        assert [t.group_id for t in tasks] == [alive.id]


@pytest.mark.asyncio
async def test_missing_group_writes_nothing_to_the_send_log():
    """Пропуск висячей ссылки тоже тихий: попытки отправки не было (D-06)."""
    async with _Db() as session:
        schedule, _ = await _seed(session, group_flags=[True])
        schedule.group_ids = [MISSING_GROUP_ID]
        await session.commit()

        await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        logged = (
            await session.execute(select(func.count()).select_from(SendLog))
        ).scalar_one()
        assert logged == 0


# --- Что пропуск НЕ трогает ---------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_group_ids_are_not_edited_by_the_skip():
    """Диспетчеризация не редактирует пользовательскую настройку рассылки.

    Вычистить выключенную группу из `group_ids` «чтобы не проверять каждый раз»
    значит сделать выключение необратимым: включив группу обратно, пользователь
    не вернул бы её в расписание и молча перестал бы рассылать.
    """
    async with _Db() as session:
        schedule, _ = await _seed(session, group_flags=[True, False])
        before = list(schedule.group_ids)

        await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        await session.refresh(schedule)
        assert schedule.group_ids == before, (
            "сбор расписаний изменил состав группы расписания"
        )


@pytest.mark.asyncio
async def test_next_run_at_moves_forward_when_every_group_is_off():
    """Расписание живо, даже когда выключены ВСЕ его группы.

    Условие пропуска стоит в per-group цикле, а не на уровне расписания:
    оставленный в прошлом `next_run_at` превратил бы включение группы в залп
    всеми накопленными пропущенными слотами.
    """
    async with _Db() as session:
        schedule, _ = await _seed(session, group_flags=[False, False])
        before = _as_utc(schedule.next_run_at)
        now = datetime.now(timezone.utc)
        assert before < now, "предусловие теста: расписание просрочено"

        tasks = await collect_due_schedules(
            session, now=now, check_limit=_allow_everything
        )

        assert tasks == []
        after = _as_utc(schedule.next_run_at)
        assert after > now, (
            "next_run_at остался в прошлом: включение группы вызовет залп ранее "
            "пропущенных отправок"
        )


@pytest.mark.asyncio
async def test_skipping_writes_nothing_to_the_send_log():
    """D-06: пропуск тихий — следа в истории отправок он не оставляет.

    Запись со специальным статусом выглядела бы для пользователя как неудачная
    попытка отправки в группу, в которую он сам запретил слать; история обязана
    отражать реальные попытки, а не намерения. Единственный след — structlog.
    """
    async with _Db() as session:
        await _seed(session, group_flags=[False, False])

        await collect_due_schedules(
            session, now=datetime.now(timezone.utc), check_limit=_allow_everything
        )

        logged = (
            await session.execute(select(func.count()).select_from(SendLog))
        ).scalar_one()
        assert logged == 0, (
            "пропуск выключенной группы попал в журнал отправок — новый статус "
            "истории не вводится (D-06)"
        )

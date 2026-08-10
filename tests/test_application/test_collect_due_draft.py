"""D-01: расписание объявления-черновика не уходит в группы.

Это единственное вторжение Фазы 2 в боевой пайплайн отправки, поэтому тест
стоит рядом с ним, а не на страничном слое.

Ключевое утверждение файла — НЕ «задача не создана», а
`test_draft_schedule_next_run_at_moves_forward`. Пропуск черновика реализован
веткой со сдвигом `next_run_at`, а не условием в `WHERE` запроса. Разница видна
только на второй проверке: фильтр в `WHERE` тоже не создал бы задачу, но
оставил бы `next_run_at` в прошлом — и в момент публикации черновика расписание
выстрелило бы всеми накопленными пропущенными слотами сразу. Это рассылка
задним числом в чужие Telegram/WhatsApp/MAX-группы от имени аккаунта
пользователя: её нельзя отозвать, и отвечает за неё владелец аккаунта
(прохибиция плана 02-03, T-02-12).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.scheduling.use_cases import collect_due_schedules
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.database import Base
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

# Каждый день недели и два времени в сутках: `compute_next_run_at` при таком
# наборе всегда находит строго будущий слот, поэтому утверждение о сдвиге не
# зависит от того, в какой момент суток запущены тесты.
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]
TWO_TIMES = ["00:30", "12:30"]


async def _allow_everything(session, user_id: int, action: str):
    return True, "ok"


def _as_utc(value: datetime) -> datetime:
    """SQLite не хранит смещение — восстанавливаем UTC для сравнения."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _seed(session: AsyncSession, ad_status: str) -> Schedule:
    """Одно просроченное расписание объявления в состоянии `ad_status`."""
    user = User(email="draft@test.com", password_hash="x", name="U")
    session.add(user)
    await session.commit()

    ad = Ad(user_id=user.id, title="T", text="Body", images=[], status=ad_status)
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="sess", status="active"
    )
    session.add_all([ad, account])
    await session.commit()

    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="telegram",
        group_external_id="-100",
        name="G",
    )
    session.add(group)
    await session.commit()

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=ALL_DAYS,
        times_of_day=TWO_TIMES,
        is_active=True,
        # Просрочено на сутки: именно такое расписание и выстрелило бы залпом,
        # если бы пропуск был сделан условием в WHERE.
        next_run_at=datetime.now(timezone.utc) - timedelta(days=1),
        timezone="UTC",
    )
    session.add(schedule)
    await session.commit()
    return schedule


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "ad_status",
    [
        pytest.param(AD_STATUS_DRAFT, id="draft"),
        # Нераспознанное значение обязано вести себя как черновик: безопасный
        # дефолт — не отправлять (UI-SPEC E15 error).
        pytest.param("something-else", id="unrecognised"),
    ],
)
async def test_draft_schedule_produces_no_dispatch_task(ad_status):
    async with _Db() as session:
        await _seed(session, ad_status)

        tasks = await collect_due_schedules(
            session,
            now=datetime.now(timezone.utc),
            check_limit=_allow_everything,
        )

        assert tasks == []


@pytest.mark.asyncio
async def test_draft_schedule_next_run_at_moves_forward():
    """Пропуск черновика СДВИГАЕТ next_run_at, а не оставляет его в прошлом.

    Прохибиция плана: публикация черновика не должна вызывать залп ранее
    пропущенных отправок.
    """
    async with _Db() as session:
        schedule = await _seed(session, AD_STATUS_DRAFT)
        before = _as_utc(schedule.next_run_at)
        now = datetime.now(timezone.utc)
        assert before < now, "предусловие теста: расписание просрочено"

        await collect_due_schedules(
            session, now=now, check_limit=_allow_everything
        )

        after = _as_utc(schedule.next_run_at)
        assert after > now, (
            "next_run_at черновика остался в прошлом: при публикации расписание "
            "выстрелит всеми пропущенными слотами сразу"
        )


@pytest.mark.asyncio
async def test_published_schedule_still_dispatches():
    """Контрольная точка: срез не сломал обычную отправку."""
    async with _Db() as session:
        schedule = await _seed(session, AD_STATUS_PUBLISHED)

        tasks = await collect_due_schedules(
            session,
            now=datetime.now(timezone.utc),
            check_limit=_allow_everything,
        )

        assert len(tasks) == 1
        assert tasks[0].schedule_id == schedule.id

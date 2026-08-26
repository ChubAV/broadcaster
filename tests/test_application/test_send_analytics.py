"""Юнит-покрытие модуля аналитики отправок (app/application/analytics).

Модуль — единственный источник агрегатов журнала для дашборда, истории и
Фазы 6 (D-35). Этот файл держит его контракт: окно скользящих суток, три
статуса, охват групп, изоляция по владельцу и перенос фильтров истории.

Все посевы ставят `sent_at` ЯВНО. У колонки есть `server_default=func.now()`,
и запись без явного времени попала бы в окно «сейчас» — то есть в текущее окно
всегда, независимо от того, что проверяет тест.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    FAILED_STATUSES,
    HISTORY_PERIODS,
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
    SendMetrics,
    UpcomingSend,
    apply_history_filters,
    history_count,
    history_filter_params,
    normalize_utc,
    send_metrics,
    upcoming_sends,
)
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.user import User

NOW = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)


async def _user(
    db: AsyncSession,
    email: str = "metrics@test.com",
    tz_name: str = "UTC",
) -> User:
    user = User(email=email, password_hash="x", name="U", timezone=tz_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_send_log(
    db: AsyncSession,
    user_id: int,
    *,
    sent_at: datetime,
    status: str = STATUS_OK,
    group_id: int | None = None,
    messenger_type: str | None = "wa",
) -> SendLog:
    """Запись журнала с явным временем отправки."""
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title="Объявление",
        ad_text="Текст",
        ad_images=[],
        group_name="Группа",
        messenger_type=messenger_type,
        task_id="task-1",
        status=status,
        sent_at=sent_at,
    )
    db.add(log)
    await db.commit()
    return log


async def _seed_group(db: AsyncSession, user: User, external_id: str) -> Group:
    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="creds", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="wa",
        group_external_id=external_id,
        name=f"Группа {external_id}",
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


# --- normalize_utc ------------------------------------------------------------


def test_normalize_utc_marks_naive_value_as_utc():
    """SQLite отдаёт DateTime(timezone=True) naive, PostgreSQL — aware."""
    naive = datetime(2026, 5, 20, 12, 0)
    assert normalize_utc(naive) == datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)


def test_normalize_utc_keeps_aware_value_untouched():
    aware = datetime(2026, 5, 20, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    assert normalize_utc(aware) is aware


def test_normalize_utc_passes_none_through():
    assert normalize_utc(None) is None


# --- Окно суток ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_metrics_splits_current_and_previous_window(db_session):
    """Пять записей за сутки и три за предыдущие сутки разъезжаются по окнам."""
    user = await _user(db_session)
    for i in range(5):
        await _seed_send_log(db_session, user.id, sent_at=NOW - timedelta(hours=i + 1))
    for i in range(3):
        await _seed_send_log(db_session, user.id, sent_at=NOW - timedelta(hours=30 + i))

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total == 5
    assert metrics.total_prev == 3
    assert metrics.total_delta == 2


@pytest.mark.asyncio
async def test_send_metrics_window_boundary_belongs_to_current(db_session):
    """Запись ровно на границе now-24h — в ТЕКУЩЕМ окне (граница включающая)."""
    user = await _user(db_session)
    await _seed_send_log(db_session, user.id, sent_at=NOW - timedelta(hours=24))
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=24, seconds=1)
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total == 1
    assert metrics.total_prev == 1


@pytest.mark.asyncio
async def test_send_metrics_ignores_records_older_than_two_windows(db_session):
    user = await _user(db_session)
    await _seed_send_log(db_session, user.id, sent_at=NOW - timedelta(hours=49))

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total == 0
    assert metrics.total_prev == 0


@pytest.mark.asyncio
async def test_send_metrics_ignores_records_from_the_future(db_session):
    """Окно ограничено и СВЕРХУ: запись «после now» плитку не завышает.

    Оба окна были ограничены только снизу, поэтому запись с `sent_at` в
    будущем — расхождение часов Celery-воркера и базы либо явный `now` от
    вызывающего — попадала в ТЕКУЩЕЕ окно. Плитка «Отправок за сутки» считала
    бы отправку, которой ещё не было, а на экране это неотличимо от правды.

    Граница включающая: запись ровно в `now` окну принадлежит.
    """
    user = await _user(db_session)
    await _seed_send_log(db_session, user.id, sent_at=NOW)
    await _seed_send_log(db_session, user.id, sent_at=NOW + timedelta(seconds=1))
    await _seed_send_log(db_session, user.id, sent_at=NOW + timedelta(days=3))

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total == 1, (
        "запись из будущего попала в текущее окно и завысила плитку"
    )
    assert metrics.total_prev == 0


# --- Три статуса --------------------------------------------------------------


@pytest.mark.asyncio
async def test_account_disconnected_counts_as_failed(db_session):
    """Плитка «Ошибок» считает ОБА неуспешных статуса, и сумма сходится с итогом."""
    user = await _user(db_session)
    await _seed_send_log(db_session, user.id, sent_at=NOW - timedelta(hours=1))
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=2), status=STATUS_FAIL
    )
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=NOW - timedelta(hours=3),
        status=STATUS_ACCOUNT_DISCONNECTED,
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total == 3
    assert metrics.ok == 1
    assert metrics.failed == 2
    assert metrics.ok + metrics.failed == metrics.total


def test_failed_statuses_names_both_unsuccessful_values():
    assert STATUS_FAIL in FAILED_STATUSES
    assert STATUS_ACCOUNT_DISCONNECTED in FAILED_STATUSES
    assert STATUS_OK not in FAILED_STATUSES


@pytest.mark.asyncio
async def test_unclassifiable_status_is_still_counted(db_session):
    """Прохибиция P-04-01: запись, которую нельзя классифицировать, не теряется.

    Статус, не входящий ни в один известный набор, обязан остаться в итоге и
    попасть в «Ошибки» — молчаливое исключение ради ровной суммы запрещено.
    """
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=1), status="weird"
    )
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=2), messenger_type=None
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total == 2
    assert metrics.ok == 1
    assert metrics.failed == 1
    assert metrics.ok + metrics.failed == metrics.total


# --- Охват групп --------------------------------------------------------------


@pytest.mark.asyncio
async def test_groups_counts_distinct_group_ids(db_session):
    user = await _user(db_session)
    group = await _seed_group(db_session, user, "-100111")
    other = await _seed_group(db_session, user, "-100222")
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=1), group_id=group.id
    )
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=2), group_id=group.id
    )
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=3), group_id=other.id
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.groups == 2
    assert metrics.total == 3


@pytest.mark.asyncio
async def test_record_without_group_counts_in_total_but_not_in_groups(db_session):
    """Пустой group_id не роняет плитку и не считается отдельной группой."""
    user = await _user(db_session)
    group = await _seed_group(db_session, user, "-100333")
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=1), group_id=group.id
    )
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(hours=2), group_id=None
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.groups == 1
    assert metrics.total == 2


# --- Вырожденные случаи и владение --------------------------------------------


@pytest.mark.asyncio
async def test_empty_dataset_gives_zeros_not_none(db_session):
    """func.sum над пустым набором отдаёт NULL — наружу обязан выйти ноль."""
    user = await _user(db_session)

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics == SendMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    for value in (
        metrics.total,
        metrics.ok,
        metrics.failed,
        metrics.groups,
        metrics.total_prev,
        metrics.ok_prev,
        metrics.failed_prev,
        metrics.groups_prev,
    ):
        assert value == 0
        assert isinstance(value, int)


@pytest.mark.asyncio
async def test_other_users_records_are_invisible(db_session):
    """T-04-01: чужие записи не попадают ни в одно поле."""
    user = await _user(db_session)
    stranger = await _user(db_session, email="stranger@test.com")
    stranger_group = await _seed_group(db_session, stranger, "-100999")
    await _seed_send_log(
        db_session,
        stranger.id,
        sent_at=NOW - timedelta(hours=1),
        group_id=stranger_group.id,
    )
    await _seed_send_log(
        db_session,
        stranger.id,
        sent_at=NOW - timedelta(hours=30),
        status=STATUS_FAIL,
        group_id=stranger_group.id,
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics == SendMetrics(0, 0, 0, 0, 0, 0, 0, 0)


@pytest.mark.asyncio
async def test_previous_window_fields_are_filled(db_session):
    user = await _user(db_session)
    group = await _seed_group(db_session, user, "-100444")
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=NOW - timedelta(hours=30),
        status=STATUS_OK,
        group_id=group.id,
    )
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=NOW - timedelta(hours=31),
        status=STATUS_ACCOUNT_DISCONNECTED,
        group_id=group.id,
    )

    metrics = await send_metrics(db_session, user_id=user.id, now=NOW)

    assert metrics.total_prev == 2
    assert metrics.ok_prev == 1
    assert metrics.failed_prev == 1
    assert metrics.groups_prev == 1
    assert metrics.ok_delta == -1
    assert metrics.failed_delta == -1
    assert metrics.groups_delta == -1


def test_send_metrics_deltas_are_differences_of_windows():
    metrics = SendMetrics(10, 7, 3, 2, 4, 4, 0, 1)

    assert metrics.total_delta == 6
    assert metrics.ok_delta == 3
    assert metrics.failed_delta == 3
    assert metrics.groups_delta == 1


# --- Переносимость агрегации ---------------------------------------------------


def test_module_has_no_dialect_specific_calendar_functions():
    """RESEARCH §Pitfall 2: ветка под PostgreSQL не исполнилась бы тестами ни разу.

    Календарная группировка средствами БД разъезжается между SQLite и
    PostgreSQL, поэтому бакетирование модуль делает в Python.
    """
    from pathlib import Path

    import app.application.analytics.send_analytics as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    code = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    for banned in ("strftime", "date_trunc", "to_char", "julianday", "func.extract"):
        assert banned not in code, f"диалект-специфичная функция {banned!r} в модуле"


# --- Фильтры истории (задача 2) ------------------------------------------------


def _history_query():
    return (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
    )


async def _rows(db: AsyncSession, query) -> list:
    return list((await db.execute(query)).all())


def test_history_periods_names_three_values():
    assert HISTORY_PERIODS == ("today", "7d", "30d")


def test_history_filter_params_keeps_the_same_keys():
    """Разметка проброса фильтров в URL зависит от этих четырёх ключей."""
    assert history_filter_params(None, None, None, None) == {}
    assert history_filter_params("ok", "wa", 7, "7d") == {
        "status": "ok",
        "messenger": "wa",
        "account_id": 7,
        "period": "7d",
    }
    assert history_filter_params(None, None, 0, None) == {"account_id": 0}


@pytest.mark.asyncio
async def test_apply_history_filters_filters_by_status_and_messenger(db_session):
    user = await _user(db_session)
    await _seed_send_log(db_session, user.id, sent_at=NOW, status=STATUS_OK)
    await _seed_send_log(
        db_session, user.id, sent_at=NOW, status=STATUS_FAIL, messenger_type="tg_user"
    )

    query = _history_query().where(SendLog.user_id == user.id)
    rows = await _rows(db_session, apply_history_filters(query, status=STATUS_FAIL))
    assert len(rows) == 1

    rows = await _rows(db_session, apply_history_filters(query, messenger_type="wa"))
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_apply_history_filters_filters_by_account(db_session):
    """Фильтр по аккаунту строится через outerjoin(Group) — без него он молчит."""
    user = await _user(db_session)
    group = await _seed_group(db_session, user, "-100555")
    other = await _seed_group(db_session, user, "-100666")
    await _seed_send_log(db_session, user.id, sent_at=NOW, group_id=group.id)
    await _seed_send_log(db_session, user.id, sent_at=NOW, group_id=other.id)

    query = _history_query().where(SendLog.user_id == user.id)
    rows = await _rows(
        db_session, apply_history_filters(query, account_id=group.account_id)
    )

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_apply_history_filters_period_7d_and_30d(db_session):
    user = await _user(db_session)
    now = datetime.now(timezone.utc)
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(days=1))
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(days=10))
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(days=40))

    query = _history_query().where(SendLog.user_id == user.id)

    assert len(await _rows(db_session, apply_history_filters(query, period="7d"))) == 1
    assert len(await _rows(db_session, apply_history_filters(query, period="30d"))) == 2


@pytest.mark.asyncio
async def test_apply_history_filters_unknown_period_applies_nothing(db_session):
    """V5: неизвестное значение даёт «фильтр не применён», а не 500."""
    user = await _user(db_session)
    await _seed_send_log(db_session, user.id, sent_at=NOW - timedelta(days=400))

    query = _history_query().where(SendLog.user_id == user.id)
    rows = await _rows(db_session, apply_history_filters(query, period="'; DROP--"))

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_period_today_cuts_at_user_local_midnight(db_session):
    """Период today отсчитывается от ЛОКАЛЬНОЙ полуночи пользователя (D-30).

    Границы считаются той же формулой, что и в модуле, поэтому тест
    детерминирован в любой час суток. Реализация, отсекающая по UTC-полуночи,
    краснеет здесь при любом запуске: у пользователя UTC+3 локальная полночь
    отстоит от UTC-полуночи на три часа, и одна из двух записей всегда падает
    не на ту сторону.
    """
    user = await _user(db_session, tz_name="Europe/Moscow")
    tz = ZoneInfo("Europe/Moscow")
    local_midnight = datetime.now(tz).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    cutoff = local_midnight.astimezone(timezone.utc)

    await _seed_send_log(
        db_session, user.id, sent_at=cutoff + timedelta(minutes=1), status=STATUS_OK
    )
    await _seed_send_log(
        db_session, user.id, sent_at=cutoff - timedelta(minutes=1), status=STATUS_FAIL
    )

    query = _history_query().where(SendLog.user_id == user.id)
    rows = await _rows(
        db_session, apply_history_filters(query, period="today", user=user)
    )

    assert len(rows) == 1
    assert rows[0][0].status == STATUS_OK


@pytest.mark.asyncio
async def test_period_today_without_user_falls_back_to_utc_midnight(db_session):
    user = await _user(db_session)
    utc_midnight = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    await _seed_send_log(db_session, user.id, sent_at=utc_midnight + timedelta(minutes=1))
    await _seed_send_log(db_session, user.id, sent_at=utc_midnight - timedelta(minutes=1))

    query = _history_query().where(SendLog.user_id == user.id)
    rows = await _rows(db_session, apply_history_filters(query, period="today"))

    assert len(rows) == 1


# --- history_count ------------------------------------------------------------


@pytest.mark.asyncio
async def test_history_count_matches_list_length(db_session):
    """D-31: счётчик и список отвечают на один вопрос одним числом."""
    user = await _user(db_session)
    group = await _seed_group(db_session, user, "-100777")
    other = await _seed_group(db_session, user, "-100888")
    await _seed_send_log(db_session, user.id, sent_at=NOW, group_id=group.id)
    await _seed_send_log(
        db_session, user.id, sent_at=NOW, group_id=group.id, status=STATUS_FAIL
    )
    await _seed_send_log(db_session, user.id, sent_at=NOW, group_id=other.id)

    filters = dict(status=STATUS_OK, account_id=group.account_id)

    query = _history_query().where(SendLog.user_id == user.id)
    rows = await _rows(db_session, apply_history_filters(query, **filters))
    counted = await history_count(db_session, user_id=user.id, **filters)

    assert counted == len(rows) == 1


@pytest.mark.asyncio
async def test_history_count_without_filters_counts_everything(db_session):
    user = await _user(db_session)
    for _ in range(4):
        await _seed_send_log(db_session, user.id, sent_at=NOW)

    assert await history_count(db_session, user_id=user.id) == 4


@pytest.mark.asyncio
async def test_history_count_is_zero_for_empty_journal(db_session):
    user = await _user(db_session)

    counted = await history_count(db_session, user_id=user.id)

    assert counted == 0
    assert isinstance(counted, int)


@pytest.mark.asyncio
async def test_history_count_ignores_other_users(db_session):
    user = await _user(db_session)
    stranger = await _user(db_session, email="stranger2@test.com")
    await _seed_send_log(db_session, stranger.id, sent_at=NOW)

    assert await history_count(db_session, user_id=user.id) == 0


# --- upcoming_sends -----------------------------------------------------------
#
# Принадлежность расписания идёт через `Ad.user_id`: колонки владельца у
# расписания НЕТ (app/models/schedule.py). Поэтому каждый посев здесь заводит
# объявление, и владение проверяется через него.

# Пометки причин — те же строки, что рендерит бейдж строки дашборда.
REASON_DRAFT = "Объявление в черновике"
REASON_ACCOUNT = "Аккаунт отключён"
REASON_GROUPS = "Все группы выключены"


async def _seed_ad(
    db: AsyncSession,
    user: User,
    *,
    title: str = "Объявление рассылки",
    status: str = AD_STATUS_PUBLISHED,
) -> Ad:
    ad = Ad(user_id=user.id, title=title, text="Текст", images=[], status=status)
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(
    db: AsyncSession, user: User, *, status: str = "active", type_: str = "wa"
) -> MessengerAccount:
    account = MessengerAccount(
        user_id=user.id, type=type_, credentials="creds", status=status
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_group_in_account(
    db: AsyncSession,
    user: User,
    account: MessengerAccount,
    *,
    external_id: str,
    is_active: bool = True,
) -> Group:
    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type=account.type,
        group_external_id=external_id,
        name=f"Группа {external_id}",
        is_active=is_active,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _seed_schedule(
    db: AsyncSession,
    user: User,
    *,
    next_run_at: datetime | None,
    ad_status: str = AD_STATUS_PUBLISHED,
    account_status: str = "active",
    with_account: bool = True,
    group_flags: tuple[bool, ...] = (True,),
    is_active: bool = True,
    title: str = "Объявление рассылки",
    seq: str = "1",
) -> Schedule:
    """Расписание вместе с объявлением, аккаунтом и составом групп."""
    ad = await _seed_ad(db, user, title=title, status=ad_status)
    account = None
    group_ids: list[int] = []
    if with_account:
        account = await _seed_account(db, user, status=account_status)
        for index, flag in enumerate(group_flags):
            group = await _seed_group_in_account(
                db, user, account, external_id=f"-100{seq}{index}", is_active=flag
            )
            group_ids.append(group.id)
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id if account else None,
        group_ids=group_ids,
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        times_of_day=["10:00"],
        timezone="UTC",
        is_active=is_active,
        next_run_at=next_run_at,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@pytest.mark.asyncio
async def test_upcoming_sends_orders_by_next_run_at(db_session):
    user = await _user(db_session)
    await _seed_schedule(
        db_session, user, next_run_at=NOW + timedelta(hours=5), title="Позже", seq="1"
    )
    await _seed_schedule(
        db_session, user, next_run_at=NOW + timedelta(hours=1), title="Раньше", seq="2"
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert [item.ad_title for item in items] == ["Раньше", "Позже"]


@pytest.mark.asyncio
async def test_upcoming_sends_respects_the_limit(db_session):
    user = await _user(db_session)
    for i in range(5):
        await _seed_schedule(
            db_session, user, next_run_at=NOW + timedelta(hours=i + 1), seq=str(i)
        )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW, limit=3)

    assert len(items) == 3


@pytest.mark.asyncio
async def test_upcoming_sends_skips_inactive_and_unscheduled(db_session):
    """Приостановленное расписание и расписание без next_run_at не выстрелят."""
    user = await _user(db_session)
    await _seed_schedule(
        db_session,
        user,
        next_run_at=NOW + timedelta(hours=1),
        is_active=False,
        title="Пауза",
        seq="1",
    )
    await _seed_schedule(db_session, user, next_run_at=None, title="Без слота", seq="2")

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert items == []


@pytest.mark.asyncio
async def test_upcoming_sends_has_no_forward_time_bound(db_session):
    """D-14: расписание через месяц попадает в список, если ближе ничего нет."""
    user = await _user(db_session)
    await _seed_schedule(
        db_session, user, next_run_at=NOW + timedelta(days=30), title="Через месяц"
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert [item.ad_title for item in items] == ["Через месяц"]


@pytest.mark.asyncio
async def test_upcoming_sends_ignores_other_users(db_session):
    """T-04-13: владение идёт через Ad.user_id — своей колонки у расписания нет."""
    user = await _user(db_session)
    stranger = await _user(db_session, email="stranger-up@test.com")
    await _seed_schedule(
        db_session, stranger, next_run_at=NOW + timedelta(hours=1), title="Чужое"
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert items == []


@pytest.mark.asyncio
async def test_upcoming_sends_does_not_trip_lazy_raise(db_session):
    """`Schedule.ad` и `Schedule.account` объявлены lazy="raise".

    Объявление и аккаунт обязаны приезжать ЗАПРОСОМ. Обращение к ним как к
    атрибутам расписания поднимает InvalidRequestError — на боевом стеке это
    пятисотка на самом дашборде, а не тихая деградация блока.
    """
    user = await _user(db_session)
    await _seed_schedule(db_session, user, next_run_at=NOW + timedelta(hours=1))

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert len(items) == 1
    item = items[0]
    # Данные объявления и канала уже в результате: доступ к ним ничего не грузит.
    assert item.ad_title == "Объявление рассылки"
    assert item.messenger_type == "wa"
    assert item.ad_id and item.schedule_id


@pytest.mark.asyncio
async def test_upcoming_sends_keeps_schedule_with_detached_account(db_session):
    """D-15: аккаунт удалён — расписание остаётся в списке с пометкой.

    `Schedule.account_id` nullable с `ondelete="SET NULL"`, поэтому ВНУТРЕННИЙ
    join потерял бы ровно те строки, ради которых D-15 написан: пользователь не
    увидел бы, что его рассылка больше никуда не уйдёт.
    """
    user = await _user(db_session)
    await _seed_schedule(
        db_session,
        user,
        next_run_at=NOW + timedelta(hours=1),
        with_account=False,
        title="Отвязанное",
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert len(items) == 1
    assert items[0].ad_title == "Отвязанное"
    assert items[0].reason == REASON_ACCOUNT


@pytest.mark.asyncio
async def test_upcoming_sends_marks_disconnected_account(db_session):
    user = await _user(db_session)
    await _seed_schedule(
        db_session,
        user,
        next_run_at=NOW + timedelta(hours=1),
        account_status="disconnected",
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert items[0].reason == REASON_ACCOUNT


@pytest.mark.asyncio
async def test_upcoming_sends_marks_draft_ad(db_session):
    user = await _user(db_session)
    await _seed_schedule(
        db_session,
        user,
        next_run_at=NOW + timedelta(hours=1),
        ad_status=AD_STATUS_DRAFT,
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert items[0].reason == REASON_DRAFT


@pytest.mark.asyncio
async def test_upcoming_sends_marks_all_groups_off(db_session):
    """Третья причина D-15 — та, ради которой берётся второй запрос."""
    user = await _user(db_session)
    await _seed_schedule(
        db_session,
        user,
        next_run_at=NOW + timedelta(hours=1),
        group_flags=(False, False),
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert items[0].reason == REASON_GROUPS


@pytest.mark.asyncio
async def test_upcoming_sends_leaves_a_healthy_schedule_unmarked(db_session):
    """Парный случай: без него пометки зеленели бы «всегда есть причина»."""
    user = await _user(db_session)
    await _seed_schedule(
        db_session,
        user,
        next_run_at=NOW + timedelta(hours=1),
        group_flags=(True, False),
    )

    items = await upcoming_sends(db_session, user_id=user.id, now=NOW)

    assert items[0].reason == ""
    assert items[0].group_count == 2


@pytest.mark.asyncio
async def test_upcoming_sends_takes_two_queries_regardless_of_group_count(db_session):
    """T-04-19: второй запрос ОДИН на блок, а не по запросу на строку.

    Отступление от D-38 названо и ограничено: флаги групп берутся одним
    запросом по объединению идентификаторов показываемых строк. Обращение к БД
    внутри цикла превратило бы отступление в дефект N+1, который на восьми
    строках по десять групп стоит восемьдесят round-trip на каждый рендер
    дашборда.
    """
    user = await _user(db_session)
    for i in range(4):
        await _seed_schedule(
            db_session,
            user,
            next_run_at=NOW + timedelta(hours=i + 1),
            group_flags=(True, True, False),
            seq=str(i),
        )

    statements: list[str] = []
    sync_engine = db_session.bind.sync_engine

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(sync_engine, "before_cursor_execute", _record)
    try:
        items = await upcoming_sends(db_session, user_id=user.id, now=NOW)
    finally:
        event.remove(sync_engine, "before_cursor_execute", _record)

    assert len(items) == 4
    selects = [s for s in statements if s.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 2, f"запросов не два, а {len(selects)}: {selects}"


def test_upcoming_send_carries_the_row_of_the_block():
    """Контракт датакласса: строка блока целиком, без обращений к БД из шаблона."""
    item = UpcomingSend(
        schedule_id=1,
        ad_id=2,
        ad_title="Объявление",
        next_run_at=NOW,
        group_count=3,
        messenger_type="wa",
        reason="",
    )

    assert item.schedule_id == 1
    assert item.ad_id == 2
    assert item.group_count == 3
    assert item.reason == ""


# --- ЗАПРЕТ НА ВОЗВРАТ НЕДЕЛЬНОЙ АКТИВНОСТИ В МОДУЛЬ (задача 260826-9vv) -----


def test_the_module_no_longer_carries_the_weekly_activity_surface():
    """Пяти снятых имён у модуля нет, четыре живых на месте.

    Обе секции — «Heatmap активности» и «Столбцы активности за неделю» —
    существовали ради одного экрана, и после снятия карточки дашборда
    потребителей у них не осталось. Часовая раскладка стримила недельное окно
    журнала отправок батчами на КАЖДОЙ загрузке страницы: снят блок — снято и
    чтение, и вернуться оно не должно.

    Проверка идёт через ОБЪЕКТЫ модуля, а не по его тексту: объяснение снятия
    оставлено в файле комментарием, и запрет, поставленный по сырому тексту,
    краснел бы на собственной причине.

    Этим же запретом закрыт и модуль маршрута: несуществующее имя он
    импортировать не сможет, и любой страничный тест увидит это первым.

    Живые функции проверяются ТЕМ ЖЕ ТЕСТОМ: запрет, прошедший на вычищенном
    заодно модуле, запретом не является — их читают дашборд, история, админка
    и биллинг.
    """
    from app.application.analytics import send_analytics

    for name in (
        "activity_heatmap",
        "activity_chart",
        "HeatmapView",
        "ActivityChartView",
        "CHART_BUCKETS_PER_DAY",
    ):
        assert not hasattr(send_analytics, name), (
            f"снятая поверхность недельной активности вернулась в модуль: {name}"
        )

    for name in ("send_metrics", "upcoming_sends", "recent_feed", "history_count"):
        assert hasattr(send_analytics, name), (
            f"вместе с недельной активностью снесена живая функция модуля: {name}"
        )

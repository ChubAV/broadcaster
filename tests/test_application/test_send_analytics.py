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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    FAILED_STATUSES,
    HISTORY_PERIODS,
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
    HeatmapView,
    SendMetrics,
    activity_heatmap,
    apply_history_filters,
    history_count,
    history_filter_params,
    normalize_utc,
    send_metrics,
)
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
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


# --- activity_heatmap ---------------------------------------------------------
#
# Окно heatmap — СКОЛЬЗЯЩИЕ семь суток от `now` (D-12), а не календарная неделя
# ПН-ВС макета. Поэтому все ожидания здесь считаются от `now - 7 суток`, и ни
# одно не выписано календарной датой: тест, привязанный к фиксированному
# понедельнику, зеленел бы ровно один день в неделю.

# Короткие имена дней НЕЗАВИСИМО от локали процесса: `strftime('%a')` отдаёт
# английские сокращения на любой машине без установленной русской локали, то
# есть проверка через него утверждала бы не то, что видит пользователь.
SHORT_DAYS = ("ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС")

# UTC+3 круглый год: ни у одной из 12 зон проекта (app/constants.py) перехода на
# летнее время нет, поэтому смещение в тестах постоянно.
MOSCOW = ZoneInfo("Europe/Moscow")


def _filled_cells(view: HeatmapView) -> dict[tuple[int, int], int]:
    """Непустые ячейки сетки в виде {(ряд, локальный час): число}."""
    return {
        (row_index, hour): value
        for row_index, row in enumerate(view.grid)
        for hour, value in enumerate(row)
        if value
    }


@pytest.mark.asyncio
async def test_heatmap_empty_journal_gives_a_grid_of_zeros(db_session):
    """Пустой набор данных — сетка нулей, а не пустой список.

    Шаблон обходит `view.grid` рядами и ячейками; пустой список отрисовал бы
    вместо сетки ничего, и блок «Активность за неделю» выглядел бы сломанным, а
    не пустым.
    """
    user = await _user(db_session)

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    assert len(view.grid) == 7
    assert all(len(row) == 24 for row in view.grid)
    assert _filled_cells(view) == {}
    assert view.peak == 0


@pytest.mark.asyncio
async def test_heatmap_same_records_land_in_different_cells_per_timezone(db_session):
    """D-10: ОДИН набор записей раскладывается по локальному часу ЧИТАТЕЛЯ.

    Прямая проверка того, ради чего heatmap считается в Python: запись в 23:30
    UTC для пользователя в UTC — вечер, а для пользователя в UTC+3 — половина
    третьего ночи СЛЕДУЮЩИХ локальных суток. Раскладка по UTC-часу показала бы
    москвичу чужой график активности.
    """
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 19, 23, 30, tzinfo=timezone.utc)
    )

    in_utc = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )
    in_moscow = await activity_heatmap(db_session, user_id=user.id, now=NOW, tz=MOSCOW)

    utc_cells = _filled_cells(in_utc)
    moscow_cells = _filled_cells(in_moscow)

    assert list(utc_cells.values()) == [1]
    assert list(moscow_cells.values()) == [1]
    assert next(iter(utc_cells))[1] == 23, "в UTC запись обязана попасть в час 23"
    assert next(iter(moscow_cells))[1] == 2, "в UTC+3 запись обязана попасть в час 2"
    assert utc_cells != moscow_cells


@pytest.mark.asyncio
async def test_heatmap_reads_naive_dates_without_raising(db_session):
    """Naive-дата SQLite обрабатывается, а не роняет расчёт.

    Колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE.
    Сравнение naive и aware в Python поднимает TypeError, поэтому нормализация
    обязана жить В МОДУЛЕ: без неё дефект существовал бы только на одном из двух
    диалектов. Тест утверждает и отсутствие исключения, и попадание в нужный час.
    """
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 19, 7, 15, tzinfo=timezone.utc)
    )

    raw = (await db_session.execute(select(SendLog.sent_at))).scalar_one()
    assert raw.tzinfo is None, "SQLite перестал отдавать naive — тест потерял смысл"

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    assert list(_filled_cells(view)) == [(6, 7)]


@pytest.mark.asyncio
async def test_heatmap_row_labels_follow_the_window_not_a_fixed_monday(db_session):
    """D-12: подписи рядов — дни ОКНА, а не ПН-ВС макета."""
    user = await _user(db_session)
    origin = NOW - timedelta(days=7)

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    expected = [
        SHORT_DAYS[(origin + timedelta(days=i)).weekday()] for i in range(7)
    ]
    assert view.day_labels == expected
    # Окно начинается в среду, поэтому фиксированная раскладка макета краснеет.
    assert view.day_labels[0] != "ПН"


@pytest.mark.asyncio
async def test_heatmap_ignores_records_outside_the_window(db_session):
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=NOW - timedelta(days=7, hours=2)
    )

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    assert _filled_cells(view) == {}


@pytest.mark.asyncio
async def test_heatmap_ignores_other_users(db_session):
    """T-04-13: владение стоит в базовом WHERE, а не в фильтре поверх."""
    user = await _user(db_session)
    stranger = await _user(db_session, email="stranger-heat@test.com")
    await _seed_send_log(db_session, stranger.id, sent_at=NOW - timedelta(hours=3))

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    assert _filled_cells(view) == {}
    assert view.peak == 0


@pytest.mark.asyncio
async def test_heatmap_counts_record_without_group_or_messenger(db_session):
    """Прохибиция плана: неклассифицируемая запись из сетки НЕ выпадает.

    Отправка без `group_id` и без `messenger_type` произошла в реальный час, и
    выбросить её ради «чистой» сетки значило бы соврать о том, работала система
    в этот час или стояла.
    """
    user = await _user(db_session)
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=datetime(2026, 5, 19, 9, 0, tzinfo=timezone.utc),
        group_id=None,
        messenger_type=None,
    )

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    assert _filled_cells(view) == {(6, 9): 1}
    assert view.peak == 1


@pytest.mark.asyncio
async def test_heatmap_cell_counts_every_send_of_the_hour_and_peak_is_the_max(
    db_session,
):
    """D-11: в ячейке ВСЕ отправки часа, а пик — самый горячий час окна."""
    user = await _user(db_session)
    hot = datetime(2026, 5, 19, 14, 0, tzinfo=timezone.utc)
    for minutes in (0, 17, 59):
        await _seed_send_log(db_session, user.id, sent_at=hot + timedelta(minutes=minutes))
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 18, 5, 30, tzinfo=timezone.utc)
    )

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc
    )

    assert _filled_cells(view) == {(6, 14): 3, (5, 5): 1}
    assert view.peak == 3


@pytest.mark.asyncio
async def test_heatmap_window_width_follows_the_days_argument(db_session):
    """Ширина окна — параметр, а не константа: Фаза 6 попросит другое число."""
    user = await _user(db_session)

    view = await activity_heatmap(
        db_session, user_id=user.id, now=NOW, tz=timezone.utc, days=3
    )

    assert len(view.grid) == 3
    assert len(view.day_labels) == 3


def test_heatmap_view_carries_grid_labels_and_peak():
    """Контракт датакласса: сетка, подписи рядов и пик — три отдельных поля."""
    view = HeatmapView(grid=[[0] * 24], day_labels=["ПН"], peak=0)

    assert view.grid == [[0] * 24]
    assert view.day_labels == ["ПН"]
    assert view.peak == 0

"""Юнит-покрытие осей тарифа (app/application/billing/plan_usage.py).

Модуль — единственный источник чисел «израсходовано / положено» на экране
тарифов (BILL-06). Этот файл держит его контракт: четыре оси в порядке макета,
календарный месяц в зоне пользователя, безлимит и превышение, изоляция по
владельцу и один round-trip к БД.

Все посевы журнала отправок ставят `sent_at` ЯВНО. У колонки есть
`server_default=func.now()`, и запись без явного времени попала бы в окно
«сейчас» ВСЕГДА, независимо от того, что проверяет тест. Для оси месяца это
правило критично вдвойне: тест границы, посеявший запись неявно, зелёный в
любой день года и не проверяет ничего.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
    current_month_bounds_utc,
    sends_in_current_month,
)
from app.application.billing.plan_usage import (
    AXIS_ACCOUNTS,
    AXIS_ADS,
    AXIS_GROUPS,
    AXIS_LABELS,
    AXIS_ORDER,
    AXIS_SENDS,
    PlanAxis,
    plan_axes,
)
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.user import User
from app.pages.common import get_shell_context

# Середина мая 2026 — «сейчас» по умолчанию. Фиксировано, потому что окно оси
# календарное: от бегущих часов тест зависеть не имеет права.
NOW = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)

MSK = "Europe/Moscow"


async def _user(
    db: AsyncSession,
    email: str = "plan@test.com",
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
) -> SendLog:
    """Запись журнала с ЯВНЫМ временем отправки."""
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title="Объявление",
        ad_text="Текст",
        ad_images=[],
        group_name="Группа",
        messenger_type="wa",
        task_id="task-1",
        status=status,
        sent_at=sent_at,
    )
    db.add(log)
    await db.commit()
    return log


async def _seed_ad(
    db: AsyncSession, user: User, title: str, status: str = AD_STATUS_PUBLISHED
) -> Ad:
    ad = Ad(user_id=user.id, title=title, text="Текст", images=[], status=status)
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(
    db: AsyncSession, user: User, status: str = "active"
) -> MessengerAccount:
    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="creds", status=status
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_group(
    db: AsyncSession,
    user: User,
    external_id: str,
    account: MessengerAccount | None = None,
) -> Group:
    """Группа владельца. Аккаунт переиспользуется: у оси «Аккаунты» свой счёт."""
    if account is None:
        account = await _seed_account(db, user)
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


# --- Границы календарного месяца ----------------------------------------------


def test_current_month_bounds_utc_spans_the_calendar_month_for_a_utc_user():
    user = User(email="u@test.com", password_hash="x", name="U", timezone="UTC")

    start, end = current_month_bounds_utc(user, now=NOW)

    assert start == datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)


def test_current_month_bounds_utc_month_boundary_follows_the_users_timezone():
    """31.05 21:30 UTC — это уже 01.06 00:30 по Москве, значит окно ИЮНЬСКОЕ."""
    user = User(email="u@test.com", password_hash="x", name="U", timezone=MSK)

    start, end = current_month_bounds_utc(
        user, now=datetime(2026, 5, 31, 21, 30, tzinfo=timezone.utc)
    )

    # 01.06 00:00 по Москве = 31.05 21:00 UTC; верхняя граница — 01.07 00:00 МСК.
    assert start == datetime(2026, 5, 31, 21, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 30, 21, 0, tzinfo=timezone.utc)


def test_current_month_bounds_utc_month_boundary_of_december_rolls_the_year():
    """Декабрь: верхняя граница — 01 января СЛЕДУЮЩЕГО года, а не month=13."""
    user = User(email="u@test.com", password_hash="x", name="U", timezone="UTC")

    start, end = current_month_bounds_utc(
        user, now=datetime(2026, 12, 15, 12, 0, tzinfo=timezone.utc)
    )

    assert start == datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_current_month_bounds_utc_month_boundary_of_a_leap_february():
    user = User(email="u@test.com", password_hash="x", name="U", timezone="UTC")

    start, end = current_month_bounds_utc(
        user, now=datetime(2028, 2, 10, 12, 0, tzinfo=timezone.utc)
    )

    assert start == datetime(2028, 2, 1, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2028, 3, 1, 0, 0, tzinfo=timezone.utc)


def test_current_month_bounds_utc_treats_a_broken_timezone_as_utc():
    """Строка зоны приходит из профиля: мусор обязан давать UTC, а не 500."""
    user = User(
        email="u@test.com", password_hash="x", name="U", timezone="Nowhere/Nothing"
    )

    start, end = current_month_bounds_utc(user, now=NOW)

    assert start == datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)


def test_current_month_bounds_utc_accepts_a_naive_now():
    """`now` приезжает и из теста, и из `datetime.now` — naive не должен ронять."""
    user = User(email="u@test.com", password_hash="x", name="U", timezone="UTC")

    start, end = current_month_bounds_utc(user, now=datetime(2026, 5, 20, 12, 0))

    assert start == datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)


# --- Счёт отправок за календарный месяц ----------------------------------------


@pytest.mark.asyncio
async def test_sends_in_current_month_counts_every_status(db_session):
    """D-25: квоту месяца расходует ЛЮБАЯ попытка отправки, а не только `ok`."""
    user = await _user(db_session)
    for status in (STATUS_OK, STATUS_FAIL, STATUS_ACCOUNT_DISCONNECTED):
        await _seed_send_log(
            db_session,
            user.id,
            sent_at=datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc),
            status=status,
        )

    count = await sends_in_current_month(
        db_session, user_id=user.id, user=user, now=NOW
    )

    assert count == 3


@pytest.mark.asyncio
async def test_sends_in_current_month_ignores_the_previous_month(db_session):
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 4, 30, 23, 59, tzinfo=timezone.utc)
    )
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    )

    count = await sends_in_current_month(
        db_session, user_id=user.id, user=user, now=NOW
    )

    assert count == 1


@pytest.mark.asyncio
async def test_sends_in_current_month_ignores_the_next_month(db_session):
    """Верхняя граница СТРОГАЯ: запись 01.06 00:00 принадлежит уже июню."""
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    )

    count = await sends_in_current_month(
        db_session, user_id=user.id, user=user, now=NOW
    )

    assert count == 0


@pytest.mark.asyncio
async def test_sends_in_current_month_month_boundary_uses_the_users_timezone(db_session):
    """Отправка 1-го числа в 00:30 по Москве принадлежит НОВОМУ месяцу."""
    user = await _user(db_session, tz_name=MSK)
    # 01.06 00:30 МСК = 31.05 21:30 UTC.
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 31, 21, 30, tzinfo=timezone.utc)
    )
    # 31.05 23:30 МСК = 31.05 20:30 UTC — ещё МАЙ.
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 31, 20, 30, tzinfo=timezone.utc)
    )

    june = await sends_in_current_month(
        db_session,
        user_id=user.id,
        user=user,
        now=datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc),
    )
    may = await sends_in_current_month(
        db_session, user_id=user.id, user=user, now=NOW
    )

    assert june == 1
    assert may == 1


@pytest.mark.asyncio
async def test_sends_in_current_month_ignores_another_users_sends(db_session):
    user = await _user(db_session)
    other = await _user(db_session, email="other@test.com")
    await _seed_send_log(
        db_session, other.id, sent_at=datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc)
    )

    count = await sends_in_current_month(
        db_session, user_id=user.id, user=user, now=NOW
    )

    assert count == 0


# --- Четыре оси тарифа ---------------------------------------------------------

# Лимиты тарифа Basic из умолчания `Settings.plan_limits`: значения приходят в
# модуль осей готовым отображением, конфиг он не читает.
BASIC_LIMITS = {"ads": 15, "groups": 30, "sends": 5000, "accounts": 5}

# Шелл считает больше ключей, чем нужно осям: оси берут ровно два.
EMPTY_NAV_COUNTS = {"ads": 0, "accounts": 0, "schedules": 0, "history": 0}


def _nav_counts(**overrides) -> dict:
    return {**EMPTY_NAV_COUNTS, **overrides}


@pytest.mark.asyncio
async def test_plan_axes_returns_four_axes_in_the_layout_order(db_session):
    """D-09: осей ЧЕТЫРЕ и в порядке макета, а не три, как в старом шаблоне."""
    user = await _user(db_session)

    axes = await plan_axes(
        db_session,
        user=user,
        limits=BASIC_LIMITS,
        nav_counts=_nav_counts(),
        now=NOW,
    )

    assert [axis.key for axis in axes] == [
        AXIS_ADS,
        AXIS_GROUPS,
        AXIS_SENDS,
        AXIS_ACCOUNTS,
    ]
    assert [axis.key for axis in axes] == list(AXIS_ORDER)
    assert [axis.label for axis in axes] == [AXIS_LABELS[key] for key in AXIS_ORDER]
    assert all(isinstance(axis, PlanAxis) for axis in axes)


@pytest.mark.asyncio
async def test_plan_axes_ads_axis_equals_the_shell_counter_including_drafts(db_session):
    """D-23: число на экране тарифов обязано совпасть со счётчиком рядом с ним."""
    user = await _user(db_session)
    await _seed_ad(db_session, user, "Опубликованное")
    await _seed_ad(db_session, user, "Черновик", status=AD_STATUS_DRAFT)
    shell = await get_shell_context(db_session, user)

    axes = await plan_axes(
        db_session,
        user=user,
        limits=BASIC_LIMITS,
        nav_counts=shell["nav_counts"],
        now=NOW,
    )

    ads_axis = next(axis for axis in axes if axis.key == AXIS_ADS)
    assert shell["nav_counts"]["ads"] == 2
    assert ads_axis.used == 2
    assert ads_axis.limit == 15


@pytest.mark.asyncio
async def test_plan_axes_accounts_axis_counts_created_accounts_not_online_ones(
    db_session,
):
    """Упавшая сессия НЕ освобождает слот тарифа: ось берёт `accounts`."""
    user = await _user(db_session)
    await _seed_account(db_session, user, status="active")
    await _seed_account(db_session, user, status="disconnected")
    shell = await get_shell_context(db_session, user)

    axes = await plan_axes(
        db_session,
        user=user,
        limits=BASIC_LIMITS,
        nav_counts=shell["nav_counts"],
        now=NOW,
    )

    accounts_axis = next(axis for axis in axes if axis.key == AXIS_ACCOUNTS)
    assert shell["sessions_online"] == 1
    assert accounts_axis.used == 2


@pytest.mark.asyncio
async def test_plan_axes_groups_axis_counts_only_the_owners_groups(db_session):
    user = await _user(db_session)
    other = await _user(db_session, email="other@test.com")
    account = await _seed_account(db_session, user)
    await _seed_group(db_session, user, "g-1", account=account)
    await _seed_group(db_session, user, "g-2", account=account)
    await _seed_group(db_session, other, "g-3")

    axes = await plan_axes(
        db_session,
        user=user,
        limits=BASIC_LIMITS,
        nav_counts=_nav_counts(),
        now=NOW,
    )

    groups_axis = next(axis for axis in axes if axis.key == AXIS_GROUPS)
    assert groups_axis.used == 2


@pytest.mark.asyncio
async def test_plan_axes_sends_axis_counts_the_current_calendar_month(db_session):
    """Ось идёт через модуль аналитики: то же окно, что у sends_in_current_month."""
    user = await _user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 5, 2, 8, 0, tzinfo=timezone.utc)
    )
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=datetime(2026, 5, 3, 8, 0, tzinfo=timezone.utc),
        status=STATUS_FAIL,
    )
    await _seed_send_log(
        db_session, user.id, sent_at=datetime(2026, 4, 30, 8, 0, tzinfo=timezone.utc)
    )

    axes = await plan_axes(
        db_session,
        user=user,
        limits=BASIC_LIMITS,
        nav_counts=_nav_counts(),
        now=NOW,
    )

    sends_axis = next(axis for axis in axes if axis.key == AXIS_SENDS)
    assert sends_axis.used == 2
    assert sends_axis.used == await sends_in_current_month(
        db_session, user_id=user.id, user=user, now=NOW
    )


@pytest.mark.asyncio
async def test_plan_axes_unlimited_axis_reports_none_and_zero_percent(db_session):
    """A2: безлимит — это None, а не 0 и не большое число."""
    user = await _user(db_session)

    axes = await plan_axes(
        db_session,
        user=user,
        limits={**BASIC_LIMITS, "ads": None},
        nav_counts=_nav_counts(ads=3),
        now=NOW,
    )

    ads_axis = next(axis for axis in axes if axis.key == AXIS_ADS)
    assert ads_axis.limit is None
    assert ads_axis.used == 3
    assert ads_axis.percent == 0


@pytest.mark.asyncio
async def test_plan_axes_zero_limit_does_not_divide_by_zero(db_session):
    """Ноль отличим от безлимита: `limit == 0` остаётся нулём, а не None."""
    user = await _user(db_session)

    axes = await plan_axes(
        db_session,
        user=user,
        limits={**BASIC_LIMITS, "ads": 0},
        nav_counts=_nav_counts(ads=3),
        now=NOW,
    )

    ads_axis = next(axis for axis in axes if axis.key == AXIS_ADS)
    assert ads_axis.limit == 0
    assert ads_axis.percent == 0


@pytest.mark.asyncio
async def test_plan_axes_over_the_limit_is_not_an_error(db_session):
    """D-08: витрина, а не механизм принуждения — превышение честно показывается."""
    user = await _user(db_session)

    axes = await plan_axes(
        db_session,
        user=user,
        limits={**BASIC_LIMITS, "ads": 15},
        nav_counts=_nav_counts(ads=20),
        now=NOW,
    )

    ads_axis = next(axis for axis in axes if axis.key == AXIS_ADS)
    assert ads_axis.used == 20
    assert ads_axis.limit == 15
    assert ads_axis.percent <= 100


@pytest.mark.asyncio
async def test_plan_axes_tolerates_a_plan_without_an_axis_key(db_session):
    """Отсутствие ключа в лимитах читается как безлимит, а не как падение."""
    user = await _user(db_session)

    axes = await plan_axes(
        db_session, user=user, limits={}, nav_counts=_nav_counts(ads=3), now=NOW
    )

    assert len(axes) == 4
    assert all(axis.limit is None for axis in axes)
    assert all(axis.percent == 0 for axis in axes)


# --- Границы модуля -------------------------------------------------------------


def _plan_usage_source() -> str:
    from pathlib import Path

    import app.application.billing.plan_usage as module

    return Path(module.__file__).read_text(encoding="utf-8")


def test_plan_usage_module_has_no_dialect_specific_calendar_functions():
    """RESEARCH §Pitfall 2: ветка под PostgreSQL не исполнилась бы тестами ни разу.

    Календарная группировка средствами БД разъезжается между SQLite и
    PostgreSQL, поэтому границы окна считаются в Python.
    """
    code = "\n".join(
        line
        for line in _plan_usage_source().splitlines()
        if not line.lstrip().startswith("#")
    )
    for banned in ("strftime", "date_trunc", "to_char", "julianday", "func.extract"):
        assert banned not in code, f"диалект-специфичная функция {banned!r} в модуле"


def test_plan_usage_module_writes_nothing_and_knows_nothing_about_http():
    """T-05-17 и T-05-19: модуль только читает и не видит `Request`.

    Отсутствие пути записи — проверяемая форма D-08: показанный лимит не
    может превратиться в гейт в модуле, который ничего не меняет.
    """
    import re

    code = "\n".join(
        line
        for line in _plan_usage_source().splitlines()
        if not line.lstrip().startswith("#")
    )
    assert not re.search(r"(db|session)\.(add|commit|flush)\(", code)
    assert not re.search(r"\bRequest\b|request\.", code)
    # Ось «Аккаунты» — заведённые аккаунты, а не онлайн-сессии.
    assert "accounts_online" not in code

"""Окно календарного месяца и счёт отправок за него (app/application/analytics/send_analytics.py).

ЭТОТ ФАЙЛ — ПЕРЕНЕСЁННОЕ ПОКРЫТИЕ, А НЕ НОВОЕ. Все тесты ниже жили в
`tests/test_application/test_plan_usage.py`, снятом планом 05.1-07 вместе с
модулем осей тарифа. Предметом они, однако, имели НЕ оси, а две функции модуля
АНАЛИТИКИ: границы календарного месяца в зоне пользователя (D-11) и счёт
отправок за это окно (D-25). Обе живут и после снятия тарифной модели —
`sends_in_current_month` имеет второго вызывающего в собственном модуле, — и
удалить их покрытие вместе с файлом осей значило бы отнять у чужого модуля
страховку в биллинговой фазе. Поэтому тесты перенесены ДОСЛОВНО, правкой одних
только импортов.

Все посевы журнала отправок ставят `sent_at` ЯВНО. У колонки есть
`server_default=func.now()`, и запись без явного времени попала бы в окно
«сейчас» ВСЕГДА, независимо от того, что проверяет тест. Для окна месяца
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
from app.models.send_log import SendLog
from app.models.user import User

# Середина мая 2026 — «сейчас» по умолчанию. Фиксировано, потому что окно
# календарное: от бегущих часов тест зависеть не имеет права.
NOW = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)

MSK = "Europe/Moscow"


async def _user(
    db: AsyncSession,
    email: str = "month@test.com",
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

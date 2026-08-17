"""Арифметика срока подписки — чистые функции, без БД и без Jinja.

Краевые даты здесь не декоративны. Наивное `value.replace(month=month + 1)`
проходит все тесты, написанные на 15-е число, и падает ValueError ровно 31
января — то есть у пользователя, а не в суите. Поэтому каждый край выписан
отдельным тестом, а сверх них идёт проход по КАЖДОМУ дню обычного и високосного
года: он ловит не конкретную известную дату, а целый класс «календарь не сошёлся».
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.application.billing.subscription_period import (
    add_one_month,
    next_expiry,
    subscription_is_live,
)


def test_add_one_month_clamps_to_a_shorter_month():
    # 31 февраля не существует: день ЗАЖИМАЕТСЯ до последнего дня месяца, а не
    # переносится на 3 марта — иначе оплаченный месяц молча становится длиннее.
    assert add_one_month(datetime(2026, 1, 31)) == datetime(2026, 2, 28)


def test_add_one_month_rolls_over_the_year():
    assert add_one_month(datetime(2026, 12, 31)) == datetime(2027, 1, 31)


def test_add_one_month_hits_the_leap_day():
    assert add_one_month(datetime(2028, 1, 29)) == datetime(2028, 2, 29)


@pytest.mark.parametrize("year", [2026, 2028])
def test_add_one_month_never_raises_on_any_day_of_the_year(year):
    """Ни один день обычного и високосного года не поднимает ValueError."""
    day = datetime(year, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, 12, 0, tzinfo=timezone.utc)
    while day < end:
        result = add_one_month(day)
        assert result > day, f"{day.date()} не сдвинулась вперёд"
        day += timedelta(days=1)


def test_next_expiry_without_a_subscription_counts_from_now():
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    assert next_expiry(None, now) == add_one_month(now)


def test_next_expiry_keeps_the_unused_remainder():
    """Досрочное продление НЕ сжигает оплаченный остаток (D-04)."""
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=10)
    assert next_expiry(current, now) == add_one_month(current)


def test_next_expiry_of_an_expired_subscription_counts_from_today():
    """Истёкшая подписка считается от сегодня, а не от прошедшего срока."""
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now - timedelta(days=40)
    assert next_expiry(current, now) == add_one_month(now)


def test_next_expiry_accepts_a_naive_current_value():
    """SQLite отдаёт `expires_at` naive — сравнение не должно падать TypeError."""
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    naive_current = datetime(2026, 3, 20, 9, 0)
    result = next_expiry(naive_current, now)
    assert result == add_one_month(naive_current.replace(tzinfo=timezone.utc))


def test_next_expiry_accepts_an_aware_current_value():
    """PostgreSQL отдаёт `expires_at` aware — тот же путь, тот же ответ."""
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    aware_current = datetime(2026, 3, 20, 9, 0, tzinfo=timezone.utc)
    assert next_expiry(aware_current, now) == add_one_month(aware_current)


def test_next_expiry_accepts_a_naive_now():
    """Наивный `now` не роняет функцию: обе стороны нормализуются."""
    now = datetime(2026, 3, 10, 9, 0)
    assert next_expiry(None, now) is not None


# --- Признак живости оплаченного срока: таблица решений -----------------------
#
# ПРЕДМЕТ РАЗДЕЛА. `subscription_is_live` — единственное объявление признака, по
# которому решают ОБЕ стадии правила смены тарифа: гард формы (продавать ли) и
# `_apply_extension` (что делать с уже уплаченным). Пока признак жил приватной
# копией в `app/pages/billing.py`, вторая стадия его не получала вовсе, и
# подтверждённый платёж на истёкшем сроке брал деньги за тариф, который не
# выдавался (гэп 1 раунда 3, `05-VERIFICATION.md`).
#
# ДВА ПРЕДСТАВЛЕНИЯ ВРЕМЕНИ ПРОВЕРЯЮТСЯ НЕ ДЛЯ ПОЛНОТЫ. Колонка
# `subscriptions.expires_at` объявлена `DateTime(timezone=True)`, но SQLite
# отдаёт её NAIVE, а PostgreSQL aware. Дефект сравнения существовал бы ровно на
# одном из двух диалектов — то есть ловился бы пользователем, а не суитой.

NOW = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)


def test_a_missing_subscription_has_no_live_period():
    """Подписки нет — живого оплаченного срока нет, защищать нечего."""
    assert subscription_is_live(None, NOW) is False


@pytest.mark.parametrize(
    "expires_at,expected",
    [
        (NOW - timedelta(days=1), False),
        (NOW - timedelta(seconds=1), False),
        (NOW + timedelta(seconds=1), True),
        (NOW + timedelta(days=1), True),
    ],
)
def test_the_liveness_follows_the_paid_date(expires_at: datetime, expected: bool):
    """Прошедший срок — не живой, будущий — живой. Границы взяты вплотную.

    Секундные отступы стоят рядом с суточными намеренно: ошибка направления
    сравнения (`<` вместо `>`) роняет суточные пары, а ошибка строгости —
    только секундные и «ровно сейчас».
    """
    assert subscription_is_live(expires_at, NOW) is expected


@pytest.mark.parametrize("offset_days,expected", [(-1, False), (1, True)])
def test_a_naive_and_an_aware_value_of_one_moment_answer_the_same(
    offset_days: int, expected: bool
):
    """SQLite отдаёт naive, PostgreSQL aware — ответ обязан быть ОДИН.

    Проверяются ОБА представления ОДНОГО момента: naive-значение считается
    временем UTC (`normalize_utc`), поэтому расходиться им негде. Без этой пары
    сравнение без приведения падало бы TypeError только в проде.
    """
    aware = NOW + timedelta(days=offset_days)
    naive = aware.replace(tzinfo=None)

    assert subscription_is_live(aware, NOW) is expected
    assert subscription_is_live(naive, NOW) is expected
    assert subscription_is_live(naive, NOW) is subscription_is_live(aware, NOW)


def test_the_moment_of_expiry_itself_is_not_live():
    """Граница «срок ровно сейчас» — НЕ живой: оплаченный момент уже прошёл.

    Сравнение строгое. Нестрогое дало бы ровно одну секунду, в которую отказ
    ещё действует, а защищать уже нечего — то есть неопределённость на самом
    денежном краю правила.
    """
    assert subscription_is_live(NOW, NOW) is False


def test_a_naive_now_does_not_break_the_liveness_term():
    """Наивный `now` не роняет признак: нормализуются ОБА операнда.

    Зеркало `test_next_expiry_accepts_a_naive_now`: обе функции модуля читают
    одну и ту же колонку и обязаны переживать оба диалекта одинаково.
    """
    naive_now = datetime(2026, 3, 10, 9, 0)

    assert subscription_is_live(NOW + timedelta(days=1), naive_now) is True
    assert subscription_is_live(NOW - timedelta(days=1), naive_now) is False

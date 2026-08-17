"""Арифметика срока подписки — чистые функции, без БД и без Jinja.

Краевые даты здесь не декоративны. Наивное `value.replace(month=month + 1)`
проходит все тесты, написанные на 15-е число, и падает ValueError ровно 31
января — то есть у пользователя, а не в суите. Поэтому каждый край выписан
отдельным тестом, а сверх них идёт проход по КАЖДОМУ дню обычного и високосного
года: он ловит не конкретную известную дату, а целый класс «календарь не сошёлся».
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.application.billing.subscription_period import (
    add_one_month,
    next_expiry,
    prorated_expiry,
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


# --- Доля месяца по уплаченному тарифу: таблица решений ------------------------
#
# ПРЕДМЕТ РАЗДЕЛА (D-29). До него `next_expiry` вызывался БЕЗУСЛОВНО, поэтому
# платёж, чей план НЕ применён, покупал полный календарный месяц ДЕЙСТВУЮЩЕГО
# тарифа: 1490 ₽ давали месяц Pro стоимостью 4900 ₽, и повторов не ограничивало
# ничто. Решение владельца: дни выдаются по УПЛАЧЕННОМУ — доля месяца по
# отношению уплаченной суммы к цене действующего плана.
#
# ДЛИНА МЕСЯЦА ПРОВЕРЯЕТСЯ ДИАПАЗОНОМ, А НЕ ТОЧНЫМ ЧИСЛОМ, там где она участвует
# множителем: календарный месяц длится от 28 до 31 дня, и точное число дней
# зависело бы от даты прогона. Там, где ответ обязан СОВПАСТЬ с `next_expiry`,
# проверяется именно совпадение — на равенство диапазон не нужен.

PRICE_PRO = Decimal("4900.00")
PRICE_BASIC = Decimal("1490.00")


def test_a_partial_payment_buys_a_fraction_of_the_month():
    """1490 ₽ при цене 4900 ₽ — около девяти дней, а не тридцать.

    Это и есть денежное содержание решения D-29, выраженное числом.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    result = prorated_expiry(None, now, paid=PRICE_BASIC, price=PRICE_PRO)

    assert timedelta(days=7) <= result - now <= timedelta(days=11), result - now


def test_paying_the_full_price_buys_the_whole_month():
    """Сумма, равная цене, даёт РОВНО `next_expiry` — ни днём меньше.

    Граница с полным периодом обязана совпадать точно: расхождение на день
    означало бы, что у полного месяца два разных определения.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    assert prorated_expiry(None, now, paid=PRICE_PRO, price=PRICE_PRO) == next_expiry(
        None, now
    )


def test_a_sum_smaller_than_a_day_still_buys_one_day():
    """⚠️ ДЕНЬГИ ВСЕГДА ПРЕВРАЩАЮТСЯ В ДНИ — ноль дней не выдаётся никогда.

    Решение D-29 сохраняет принцип дословно: исход «взяли деньги и не дали
    ничего» назван худшим и не вводится ни на одной ветке. Целая часть доли
    здесь равна нулю, и именно поэтому нижняя граница в один день не
    декоративна.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    result = prorated_expiry(None, now, paid=Decimal("1.00"), price=PRICE_PRO)

    assert result - now == timedelta(days=1)


def test_a_sum_larger_than_the_price_buys_more_than_a_month():
    """Верхнего потолка НЕТ намеренно: обрезание было бы взятием без выдачи.

    Дни выдаются по тому, ЧТО УПЛАЧЕНО. Переплативший получает больше месяца —
    это прямое следствие того же принципа, что и нижняя граница в один день.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    result = prorated_expiry(None, now, paid=PRICE_PRO, price=PRICE_BASIC)

    assert result > next_expiry(None, now)


def test_the_fraction_counts_from_the_live_date_and_not_from_today():
    """Точка отсчёта — та же, что у `next_expiry` (D-04): оплаченный остаток цел.

    Доля месяца не имеет права сжигать неистраченный остаток: она ДОБАВЛЯЕТСЯ к
    действующему сроку, а не заменяет его отсчётом от сегодня.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=10)

    result = prorated_expiry(current, now, paid=PRICE_BASIC, price=PRICE_PRO)

    assert result > current, "оплаченный остаток сожжён долей месяца"
    assert result - current <= timedelta(days=11)


def test_the_fraction_of_an_expired_period_counts_from_today():
    """Истёкший срок считается от сегодня, а не воскрешает прошедший месяц.

    Зеркало `test_next_expiry_of_an_expired_subscription_counts_from_today`:
    обе функции читают одну колонку и обязаны выбирать точку отсчёта одинаково.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now - timedelta(days=40)

    result = prorated_expiry(current, now, paid=PRICE_BASIC, price=PRICE_PRO)

    assert result > now, "срок посчитан от прошедшей даты и остался в прошлом"
    assert result - now <= timedelta(days=11)


@pytest.mark.parametrize("offset_days", [-40, 10])
def test_a_naive_and_an_aware_date_give_the_same_fraction(offset_days: int):
    """SQLite отдаёт `expires_at` naive, PostgreSQL aware — ответ ОДИН.

    Без этой пары дефект сравнения жил бы ровно на одном из двух диалектов, то
    есть ловился бы пользователем на PostgreSQL, а не суитой на SQLite.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    aware = now + timedelta(days=offset_days)
    naive = aware.replace(tzinfo=None)

    assert prorated_expiry(aware, now, paid=PRICE_BASIC, price=PRICE_PRO) == (
        prorated_expiry(naive, now, paid=PRICE_BASIC, price=PRICE_PRO)
    )

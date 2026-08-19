"""Арифметика срока подписки — чистые функции, без БД и без Jinja.

Краевые даты здесь не декоративны. Наивное `value.replace(month=month + 1)`
проходит все тесты, написанные на 15-е число, и падает ValueError ровно 31
января — то есть у пользователя, а не в суите. Поэтому каждый край выписан
отдельным тестом, а сверх них идёт проход по КАЖДОМУ дню обычного и високосного
года: он ловит не конкретную известную дату, а целый класс «календарь не сошёлся».
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import pytest

from app.application.billing.subscription_period import (
    add_one_month,
    capped_carryover,
    converted_remainder,
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


# --- Потолок переноса при нечитаемой цене: таблица решений ---------------------
#
# ПРЕДМЕТ РАЗДЕЛА. Когда цену любого из двух планов прочитать нельзя, конвертиро-
# вать остаток по деньгам не из чего, а переносить его ЦЕЛИКОМ нельзя: покупатель
# управляет горизонтом предоплаты сам, и без верхней границы один платёж старшего
# тарифа переводил на него весь накопленный срок — 396 дней Pro за 22 780 ₽ при
# прейскуранте 63 700 ₽ (гэп 1 раунда 6, воспроизведён верификацией поверх
# настоящего кода).
#
# ФОРМА `cap-one-month` — РЕШЕНИЕ ВЛАДЕЛЬЦА (чекпойнт задачи 1 плана 05-22):
# перенос ограничен потолком в ОДИН календарный месяц остатка. Остаток короче
# месяца переносится целиком и не сгорает; часть остатка СВЕРХ месяца сгорает —
# это названная числом цена формы, а не упущение.
#
# ЭТО АРИФМЕТИКА ВРЕМЕНИ, А НЕ ДЕНЕГ, и таблица проверяет её без единой цены:
# соседний `converted_remainder` переносит остаток ПО ДЕНЬГАМ и потому берёт две
# цены, а здесь ни одной цены нет — их-то и нельзя прочитать.


def test_the_capped_carryover_of_a_missing_period_is_today():
    """Подписки не было — переносить нечего, точка отсчёта равна сегодня."""
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    assert capped_carryover(None, now) == now


def test_the_capped_carryover_of_an_expired_period_is_today():
    """Истёкший срок не воскрешается: зеркало `next_expiry` на той же колонке.

    Решение `apply-after-expiry` (чекпойнт плана 05-13) этим не задевается —
    план платежа применяется, а срок считается от сегодня.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    assert capped_carryover(now - timedelta(days=40), now) == now


def test_a_remainder_shorter_than_a_month_is_carried_whole():
    """⚠️ ОСТАТОК КОРОЧЕ МЕСЯЦА НЕ СГОРАЕТ НИ НА ДЕНЬ.

    Это главное свойство формы `cap-one-month` и единственное, чем она
    отличается от отвергнутой формы `no-carry`. Защитная семантика 25 дней
    (D-04) держится именно здесь: потолок обязан РЕЗАТЬ длинный горизонт, а не
    обнулять короткий.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=25)

    assert capped_carryover(current, now) == current


def test_a_remainder_longer_than_a_month_is_capped_at_one_month():
    """Остаток длиннее месяца зажимается РОВНО календарным месяцем от сегодня.

    Календарным, а не константой 30: расхождение с `next_expiry` в феврале и в
    декабре дало бы «полному месяцу» два разных определения — ровно тот класс
    расхождения, ради устранения которого заведён этот модуль.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=365)

    assert capped_carryover(current, now) == add_one_month(now)


@pytest.mark.parametrize("offset_days", [-40, 25, 365])
def test_a_naive_and_an_aware_date_give_the_same_capped_carryover(offset_days: int):
    """SQLite отдаёт `expires_at` naive, PostgreSQL aware — ответ ОДИН.

    Без этой пары дефект сравнения жил бы ровно на одном из двух диалектов, то
    есть ловился бы пользователем на PostgreSQL, а не суитой на SQLite.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    aware = now + timedelta(days=offset_days)
    naive = aware.replace(tzinfo=None)

    assert capped_carryover(aware, now) == capped_carryover(naive, now)


@pytest.mark.parametrize("year", [2026, 2028])
def test_the_capped_carryover_never_exceeds_one_month_on_any_day_of_the_year(year):
    """Ни один день обычного и високосного года не пробивает потолка.

    Проход по календарю ловит не конкретную известную дату, а целый класс
    «календарь не сошёлся»: длина месяца меняется от 28 до 31 дня, и граница,
    посчитанная не тем месяцем, дала бы покупателю лишние дни старшего тарифа на
    краю, которого нет ни в одном точечном тесте.
    """
    day = datetime(year, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, 12, 0, tzinfo=timezone.utc)
    while day < end:
        result = capped_carryover(day + timedelta(days=400), day)
        assert result <= add_one_month(day), f"{day.date()}: потолок пробит"
        assert result > day, f"{day.date()}: живой остаток сгорел дочиста"
        day += timedelta(days=1)


# --- Перенос остатка ПО ДЕНЬГАМ: таблица решений -------------------------------
#
# ПРЕДМЕТ РАЗДЕЛА (решение владельца D-30, форма `convert-remainder`, чекпойнт
# задачи 1 плана 05-18). Повышение тарифа СЧИТАЕТ ДОПЛАТУ: неистраченный остаток,
# купленный по цене старого плана, пересчитывается в дни по цене нового, и уже к
# этой точке вызывающий добавляет оплаченный месяц. Это тот же аппарат D-29,
# запущенный в другую сторону, а не вторая арифметика денег.
#
# ПОЧЕМУ ТАБЛИЦА ПОНАДОБИЛАСЬ ИМЕННО ТЕПЕРЬ. `add_one_month`, `subscription_is_live`,
# `next_expiry`, `prorated_expiry` и `capped_carryover` держат в этом файле по
# полной таблице краёв каждая, а `converted_remainder` — ЕДИНСТВЕННАЯ новая
# арифметика денежного пути — не была здесь даже импортирована (`IN-01` раунда 6).
# Всё её покрытие жило интеграционными утверждениями с допуском ±2 дня
# (`test_billing_payment_errors.py`, `test_payment_concurrency.py`), а такой допуск
# не видит НИ ОДНОГО из трёх дефектов, ради которых модуль вынесен из БД: усечения
# неполного дня, расхождения февраля с декабрём и разницы naive/aware.
#
# ПРАВИЛО УТВЕРЖДЕНИЙ РАЗДЕЛА. Здесь проверяется то, что функция ДЕЛАЕТ, а не то,
# что о ней написано: абзац докстринга о длине месяца утверждал зависимость,
# которой у ответа нет, и опровергнут он был прогоном настоящей функции, а не
# чтением. Поэтому длина месяца проверяется ТОЧНЫМ числом (её в ответе нет вовсе),
# в отличие от таблицы `prorated_expiry`, где та же величина действительно входит
# в ответ множителем и потому проверяется диапазоном.
#
# Все моменты `now` сняты литералами с `timezone.utc`: раздел проверяет арифметику,
# а не сегодняшний день.


def test_a_missing_period_converts_to_today():
    """Подписки не было — конвертировать нечего, точка отсчёта равна сегодня."""
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    assert converted_remainder(None, now, old_price=PRICE_BASIC, new_price=PRICE_PRO) == now


def test_an_expired_period_converts_to_today():
    """Истёкший срок не воскрешается: зеркало `next_expiry` на той же колонке.

    Прямое зеркало `test_next_expiry_of_an_expired_subscription_counts_from_today`:
    обе функции читают одну колонку и обязаны выбирать точку отсчёта одинаково.
    Решение `apply-after-expiry` (чекпойнт плана 05-13) этим не задевается — план
    платежа применяется, а срок считается от сегодня.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    assert converted_remainder(
        now - timedelta(days=40), now, old_price=PRICE_BASIC, new_price=PRICE_PRO
    ) == now


def test_a_live_remainder_never_converts_to_zero_days():
    """⚠️ ЖИВОЙ ОСТАТОК НИКОГДА НЕ КОНВЕРТИРУЕТСЯ В НОЛЬ ДНЕЙ.

    Самый дешёвый живой остаток — один день `basic`, пересчитанный по цене `pro`, —
    даёт РОВНО один день, а не ноль. Целая часть доли здесь равна нулю, и именно
    поэтому нижняя граница `prorated_days` не декоративна: без неё обещание
    «оплаченный остаток не сгорает» ломалось бы молча на самом незаметном краю, то
    есть возник бы исход «взяли деньги и не дали ничего», названный D-29 худшим.

    Зеркало `test_a_sum_smaller_than_a_day_still_buys_one_day`.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    result = converted_remainder(
        now + timedelta(days=1), now, old_price=PRICE_BASIC, new_price=PRICE_PRO
    )

    assert result - now == timedelta(days=1)


@pytest.mark.parametrize("offset_days", [-40, 10, 365])
def test_a_naive_and_an_aware_date_give_the_same_conversion(offset_days: int):
    """SQLite отдаёт `expires_at` naive, PostgreSQL aware — ответ ОДИН.

    Зеркало `test_a_naive_and_an_aware_date_give_the_same_fraction`. Без этой пары
    дефект сравнения жил бы ровно на одном из двух диалектов, то есть ловился бы
    пользователем на PostgreSQL, а не суитой на SQLite; допуск ±2 дня в
    интеграционных регрессиях такой разницы не видит вовсе.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    aware = now + timedelta(days=offset_days)
    naive = aware.replace(tzinfo=None)

    assert converted_remainder(
        aware, now, old_price=PRICE_BASIC, new_price=PRICE_PRO
    ) == converted_remainder(naive, now, old_price=PRICE_BASIC, new_price=PRICE_PRO)


def test_equal_prices_return_the_remainder_in_whole_days():
    """⚠️ ПРИ РАВНЫХ ЦЕНАХ ОСТАТОК ВОЗВРАЩАЕТСЯ СЕБЕ — НО В ЦЕЛЫХ ДНЯХ.

    Утверждение о точном равенстве действующему сроку было бы ЛОЖНЫМ, и тест
    закрепляет настоящее поведение, а не желаемое: `prorated_days` берёт ЦЕЛУЮ
    часть, поэтому неполный день переноса теряется — до 23 ч 59 м уже оплаченного
    времени. Обещание «оплаченный остаток не сгорает» верно в днях и слегка
    неверно в последнем дне (`IN-02` раунда 6); та же целая часть даёт и нижнюю
    границу в один день, закреплённую тестом выше.

    Цена того, что срок хранится днями, а не решение о деньгах.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=10, hours=5)

    result = converted_remainder(current, now, old_price=PRICE_PRO, new_price=PRICE_PRO)

    assert result == now + timedelta(days=(current - now).days)
    assert result < current, "неполный день обязан теряться — иначе усечения нет"


def test_the_conversion_does_not_depend_on_the_length_of_the_month():
    """⚠️ ДЛИНА КАЛЕНДАРНОГО МЕСЯЦА В ОТВЕТ НЕ ВХОДИТ — И ЭТО СВОЙСТВО ФУНКЦИИ.

    Величина стоит знаменателем стоимости остатка и множителем внутри
    `prorated_days`, и два вхождения СОКРАЩАЮТСЯ: ответ равен целой части от
    произведения остатка в днях на отношение цен — форме, в которой длины месяца
    нет вовсе. Абзац докстринга, утверждавший обратное («длина месяца берётся у
    `add_one_month` от той же базы»), был опровергнут верификацией раунда 6 ровно
    этим вычислением, прогоном настоящей функции.

    Три базы выбраны так, чтобы `add_one_month` дал ТРИ РАЗНЫЕ длины месяца — 28,
    31 и 30 дней, — и это утверждается здесь же, чтобы тест не проходил молча,
    если календарь выберет одинаковые. Ответ обязан быть ОДИН на всех трёх.

    ⚠️ Тест закрепляет утверждение машиной: правка, вводящая настоящую зависимость
    от календаря, красит его, а не проходит незамеченной. Такая правка была бы
    правкой ПОВЕДЕНИЯ — она меняет величину, которую наблюдает покупатель, — и
    потребовала бы решения владельца, а не правки комментария.
    """
    remainder_days = 365
    month_lengths = {
        datetime(2026, 1, 31, 9, 0, tzinfo=timezone.utc): 28,
        datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc): 31,
        datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc): 30,
    }
    expected = timedelta(days=int(Decimal(remainder_days) * PRICE_BASIC / PRICE_PRO))

    answers = {}
    for now, month_days in month_lengths.items():
        assert (add_one_month(now) - now).days == month_days, (
            f"{now.date()}: длина месяца не та, ради которой база выбрана"
        )
        answers[now.date()] = (
            converted_remainder(
                now + timedelta(days=remainder_days),
                now,
                old_price=PRICE_BASIC,
                new_price=PRICE_PRO,
            )
            - now
        )

    assert set(answers.values()) == {expected}, answers


def test_a_downgrade_converts_the_remainder_into_more_days():
    """Аппарат симметричен: понижение УВЕЛИЧИВАЕТ остаток, повышение уменьшает.

    Остаток, купленный по дорогой цене, стоит больше дней дешёвого плана. Сторона
    повышения закреплена тестом длины месяца выше (365 дней `basic` дают 110 дней
    `pro`); здесь утверждается вторая сторона — сравнением с исходным остатком, без
    точного числа: точное число здесь ничего не добавило бы к утверждению о
    направлении.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=10)

    result = converted_remainder(current, now, old_price=PRICE_PRO, new_price=PRICE_BASIC)

    assert result > current, "понижение обязано давать БОЛЬШЕ дней, а не меньше"


# --- Срок, которого нет в календаре -------------------------------------------
#
# ПРЕДМЕТ РАЗДЕЛА И ЕГО ГРАНИЦА. Верхнего потолка у доли месяца НЕТ, и это
# решение D-29: сумма больше цены покупает больше месяца, обрезание было бы
# «взяли деньги и не дали ничего». Раздел его не отменяет и не сужает — соседний
# `test_a_sum_larger_than_the_price_buys_more_than_a_month` остаётся зелёным без
# единой правки. Здесь другое: `datetime` кончается 9999 годом, и доля месяца,
# у которой нет момента, обязана вернуться `None`-ом, а не исключением, потому
# что решение принимает денежный путь — там есть журнал, откат к полному месяцу
# и обязанность не уронить обработчик уведомления пятисоткой (T-05-104).
#
# ЦЕНА ВЗЯТА ТА ЖЕ, ЧТО ВОСПРОИЗВЕЛ РАУНД 9 — одна копейка: правильно
# оформленное положительное значение, какое оператор ставит промо-тарифу, а не
# ошибка формата.

PRICE_BEYOND_THE_CALENDAR = Decimal("0.01")


def test_a_span_that_the_calendar_cannot_express_returns_no_moment():
    """Доля месяца без момента в календаре возвращается `None`-ом.

    До правки эта же цена поднимала `OverflowError: date value out of range`,
    который доходил до маршрута уведомления и становился 500 при уже списанных
    деньгах.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    assert (
        prorated_expiry(None, now, paid=PRICE_BASIC, price=PRICE_BEYOND_THE_CALENDAR)
        is None
    )


def test_a_conversion_that_the_calendar_cannot_express_returns_no_moment():
    """ВТОРАЯ ветка того же дефекта: перенос остатка зовёт тот же `prorated_days`.

    Без этого случая объём защиты равнялся бы объёму того, что успел попробовать
    предыдущий раунд, — тот самый НЕДООБЪЯВЛЕННЫЙ КОНТРАКТ, который назван
    решением D-35.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)
    current = now + timedelta(days=25)

    assert (
        converted_remainder(
            current, now, old_price=PRICE_BASIC, new_price=PRICE_BEYOND_THE_CALENDAR
        )
        is None
    )


def test_a_non_finite_amount_is_not_named_an_unrepresentable_span():
    """ГРАНИЦА ПЕРЕХВАТА НАЗВАНА: нефинитная сумма сюда не относится.

    Перехват в `_shifted_by_days` закрыт `OverflowError` намеренно. Нечитаемая
    (нефинитная) сумма — ДРУГОЙ исход с другим словом в журнале (`"amount"`), и
    он классифицируется денежным путём, а не глушится арифметикой: `int()`
    внутри `prorated_days` роняет её РАНЬШЕ сдвига. Без этого случая правка,
    заменившая перечень на `Exception`, слила бы два исхода в один и осталась бы
    зелёной.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    with pytest.raises((ValueError, OverflowError, InvalidOperation)):
        prorated_expiry(None, now, paid=Decimal("NaN"), price=PRICE_PRO)


def test_a_span_the_calendar_can_express_is_still_a_moment():
    """Позитивный контроль: без него оба случая выше зеленели бы от `None` всегда.

    Цена `1.00` при уплаченных 1490 ₽ даёт 2153 год — величина невероятная, но
    выразимая, и потолком она не режется.
    """
    now = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)

    result = prorated_expiry(None, now, paid=PRICE_BASIC, price=Decimal("1.00"))

    assert result is not None
    assert result > next_expiry(None, now)

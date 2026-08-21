"""Арифметика срока подписки — чистые функции, без БД и без Jinja.

Краевые даты здесь не декоративны. Наивное `value.replace(month=month + 1)`
проходит все тесты, написанные на 15-е число, и падает ValueError ровно 31
января — то есть у пользователя, а не в суите. Поэтому каждый край выписан
отдельным тестом, а сверх них идёт проход по КАЖДОМУ дню обычного и високосного
года: он ловит не конкретную известную дату, а целый класс «календарь не сошёлся».
"""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import app.application.billing as app_billing
from app.application.billing.subscription_period import (
    access_is_open,
    add_one_month,
    days_left,
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


# =============================================================================
# ВЕРДИКТ ДОСТУПА И ОСТАТОК СРОКА (фаза 05.1, плоская модель)
#
# Обе функции — чистые, как и весь модуль: строку подписки они получают
# ЗНАЧЕНИЕМ, в БД не ходят и о сессии SQLAlchemy не знают. Поэтому подделка
# строки простым объектом здесь не «мок вместо настоящего», а ровно тот вход,
# который функция и принимает.
# =============================================================================


class _Row:
    """Строка подписки в объёме, который читает `access_is_open`.

    Настоящая модель здесь не нужна и была бы хуже: `Subscription` тянет за
    собой метаданные таблицы и создание схемы, а вердикт доступа читает ровно
    три атрибута. Третий — признак бесплатного доступа — дописан планом
    `05.1-09` вместе со своей веткой в предикате. Тест на настоящей строке живёт в
    `tests/test_pages/test_access_lifecycle.py`, где предмет — стыковка слоёв.
    """

    def __init__(self, expires_at, is_active=True, has_free_access=False):
        self.expires_at = expires_at
        self.is_active = is_active
        self.has_free_access = has_free_access


NOW = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)


def test_a_user_without_a_subscription_row_has_a_definite_verdict():
    """Отсутствие строки — это «доступа нет», а не «ответа нет».

    Свидетель абзаца «ПОЛЬЗОВАТЕЛЬ БЕЗ СТРОКИ ПОДПИСКИ ИМЕЕТ ОПРЕДЕЛЁННОЕ
    СОСТОЯНИЕ». Возвращается БУЛЕВО, а не `None` и не исключение: до плоской
    модели строка была у меньшинства пользователей, и такой пользователь
    переживёт выкат.
    """
    verdict = access_is_open(None, NOW)

    assert verdict is False
    assert isinstance(verdict, bool), "вердикт доступа обязан быть булевым"


def test_a_deactivated_row_gives_no_access_however_late_its_date():
    """Признак снимается С ДВУХ величин: активности строки И живости срока.

    История подписок лежит в тех же строках. Читать срок, не спросив про
    активность, значило бы выдать доступ по отменённому периоду — на входе у
    этого теста ровно такая строка: срок на год вперёд, `is_active` ложно.
    """
    far_future = NOW + timedelta(days=365)

    assert access_is_open(_Row(far_future, is_active=False), NOW) is False
    assert access_is_open(_Row(far_future, is_active=True), NOW) is True, (
        "позитивный контроль: без него тест зеленел бы от вердикта «нет» всегда"
    )


def test_the_verdict_follows_the_liveness_of_the_period():
    """Живой срок открывает доступ, истёкший — закрывает; равный `now` закрыт.

    Строгость сравнения достаётся от `subscription_is_live` и здесь только
    ПЕРЕПРОВЕРЯЕТСЯ на границе: оплаченный момент, равный `now`, уже прошёл.
    Второго сравнения дат `access_is_open` не заводит.
    """
    assert access_is_open(_Row(NOW + timedelta(seconds=1)), NOW) is True
    assert access_is_open(_Row(NOW), NOW) is False
    assert access_is_open(_Row(NOW - timedelta(seconds=1)), NOW) is False


def _access_is_open_body() -> str:
    """Тело `access_is_open` по синтаксическому дереву, БЕЗ узла докстринга.

    ⚠️ ДОКСТРИНГ ИСКЛЮЧАЕТСЯ, И БЕЗ ЭТОГО ПРОВЕРКА ПОРЯДКА БЫЛА БЫ НЕВОЗМОЖНА:
    он НАЗЫВАЕТ и колонку, и обе сравниваемые проверки, объясняя их порядок.
    Проверка по сырому тексту читала бы позиции слов В ОБЪЯСНЕНИИ, а не в коде,
    и зеленела бы от абзаца при переставленных операторах. Приём унаследован от
    снятого `test_the_verdict_does_not_read_a_free_access_column_yet`, который
    этим же способом доказывал ОТСУТСТВИЕ ветки; ветка появилась планом
    `05.1-09`, и способ снятия утверждения пережил смену его знака.
    """
    source = (
        Path(app_billing.__file__).parent / "subscription_period.py"
    ).read_text(encoding="utf-8")
    function = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "access_is_open"
    )
    statements = function.body
    if ast.get_docstring(function) is not None:
        statements = statements[1:]
    return "\n".join(ast.unparse(statement) for statement in statements)


def test_free_access_opens_the_verdict_over_a_dead_date():
    """Выданный бесплатный доступ ВЫИГРЫВАЕТ у истёкшего срока (D-E, критерий 5).

    Главное утверждение критерия 5 фазы. Человеку, которому администратор выдал
    бесплатный доступ, дата окончания не читается вовсе: показать ему «доступ
    закрыт» из-за просроченной колонки значило бы отменить его собственную
    льготу молча. Дата на входе МЁРТВАЯ намеренно — именно на ней ветка,
    приписанная в конец каскада, дала бы ложь.
    """
    dead = NOW - timedelta(days=365)

    assert access_is_open(_Row(dead, has_free_access=True), NOW) is True
    assert access_is_open(_Row(dead, has_free_access=False), NOW) is False, (
        "отрицательный контроль: без него тест зеленел бы от вердикта «да» всегда"
    )


def test_free_access_does_not_resurrect_a_deactivated_row():
    """Признак не отменяет проверку АКТИВНОСТИ строки, и это граница ветки.

    ⚠️ РЕШЕНИЕ, А НЕ НЕДОСМОТР. «Первым в порядке состояний» означает «раньше
    живости СРОКА» — ровно ту проверку, которую льгота обязана победить.
    Активность строки состоянием доступа не является: это ответ на вопрос
    «считается ли эта строка вообще», и история подписок пользователя лежит в
    тех же строках. Поставь ветку льготы ВЫШЕ него — и деактивированный
    исторический период с когда-то выданной льготой открывал бы доступ навсегда,
    причём в обход частичного уникального индекса, который стережёт ровно одну
    АКТИВНУЮ строку.
    """
    far_future = NOW + timedelta(days=365)

    assert access_is_open(
        _Row(far_future, is_active=False, has_free_access=True), NOW
    ) is False
    assert access_is_open(
        _Row(far_future, is_active=True, has_free_access=True), NOW
    ) is True, "позитивный контроль: строка активна — льгота обязана сработать"


def test_the_free_access_check_stands_before_the_liveness_call():
    """ПОРЯДОК — ПРАВИЛО, И ОН ЗАКРЕПЛЁН МАШИНОЙ, А НЕ АБЗАЦЕМ.

    Признак читается РАНЬШЕ вызова `subscription_is_live`. Переставленные
    местами, две строки выглядят безобидной перестановкой и меняют поведение
    ровно у той популяции, ради которой ветка и заведена, — у людей с мёртвой
    датой и выданной льготой. Поведенческий сосед
    (`test_free_access_opens_the_verdict_over_a_dead_date`) поймал бы это тоже,
    но только пока ветка возвращает РАНО; утверждение по дереву держит сам
    порядок и переживает переписывание тела в один `return`.
    """
    body = _access_is_open_body()

    assert "has_free_access" in body, (
        "ветка бесплатного доступа исчезла из предиката — критерий 5 фазы "
        "перестал быть закрытым (D-E)"
    )
    assert "subscription_is_live" in body, (
        "предикат перестал звать единственное объявление живости срока"
    )
    assert body.index("has_free_access") < body.index("subscription_is_live"), (
        "признак бесплатного доступа читается ПОСЛЕ живости срока — истёкшая "
        "дата закрывает доступ человеку, которому льгота выдана"
    )


def test_a_period_that_does_not_exist_has_no_number_of_days():
    """`None` означает РОВНО ОДНО — срока не существует."""
    assert days_left(None, NOW) is None


def test_the_last_day_of_access_is_zero_and_not_absent():
    """Ноль — ЖИВОЙ последний день доступа, а не край и не отсутствие ответа.

    Правило P-6 UI-контракта опирается на достижимость нуля: разметка обязана
    уметь сказать «последний день». Слить его с `None` значило бы показать
    человеку в его последний оплаченный день то же, что человеку без подписки.
    """
    assert days_left(NOW + timedelta(hours=23), NOW) == 0
    assert days_left(NOW + timedelta(hours=23), NOW) is not None


@pytest.mark.parametrize("hours", [1, 6, 12, 23])
def test_the_last_day_is_zero_while_the_period_is_still_live(hours: int):
    """Ноль и ЖИВОСТЬ срока выпадают ОДНОВРЕМЕННО — ветка P-6 достижима.

    Соседний тест показывает, что ноль отличим от `None`. Здесь показано
    большее и именно то, на что опирается правило P-6: ноль выпадает у
    человека, чей доступ ЕЩЁ РАБОТАЕТ. Без этой пары утверждений ветка
    «последний день» могла бы оказаться мёртвым кодом — веткой, в которую
    попадает только тот, кому и так уже отказано, — и тогда её место занял бы
    бейдж «закрыт», а не слова про последний день.

    Проверено на всём диапазоне последних суток, а не на одной точке: ноль,
    выпадающий лишь в одном часе из двадцати четырёх, был бы достижим
    формально и недостижим практически.
    """
    expires_at = NOW + timedelta(hours=hours)

    assert days_left(expires_at, NOW) == 0
    assert subscription_is_live(expires_at, NOW) is True


def test_an_expired_period_never_reports_zero_days_left():
    """У закрытого доступа ноль не выпадает НИ ПРИ КАКОМ смещении в прошлое.

    Это вторая половина достижимости: если бы истёкший срок тоже давал ноль,
    ветка «последний день» печаталась бы человеку, которому уже отказано, —
    то есть худшую из возможных подмен, обратную той, от которой защищает P-6.
    Целая часть отрицательной разности округляется ВНИЗ (`timedelta.days`),
    поэтому даже секунда просрочки даёт −1, а не ноль.
    """
    for seconds in (1, 60, 3600, 86_399, 86_400):
        expires_at = NOW - timedelta(seconds=seconds)
        assert days_left(expires_at, NOW) < 0, seconds
        assert subscription_is_live(expires_at, NOW) is False, seconds


def test_whole_days_are_counted_and_not_hours_rounded():
    """Считается целая часть разности, а не округление часов.

    23 часа — ещё ноль полных суток, 25 часов — уже одни. Округление дало бы
    единицу в первом случае, то есть обещало бы человеку день, которого нет.
    """
    assert days_left(NOW + timedelta(hours=23), NOW) == 0
    assert days_left(NOW + timedelta(hours=25), NOW) == 1
    assert days_left(NOW + timedelta(days=5), NOW) == 5


def test_the_remaining_days_accept_a_naive_moment():
    """Оба момента проходят через `normalize_utc` — иначе TypeError на SQLite.

    Колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а
    PostgreSQL — aware. Вычитание без приведения падало бы ровно на одном из
    двух диалектов, то есть у пользователя, а не в суите.
    """
    naive_expiry = (NOW + timedelta(days=3)).replace(tzinfo=None)

    assert days_left(naive_expiry, NOW) == 3
    assert days_left(NOW + timedelta(days=3), NOW.replace(tzinfo=None)) == 3

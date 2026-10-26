"""Маска номера в выводе журнала — `app/services/log_masking.py`.

Защита на исполнении (решение владельца О-23 (а), свойство 2): номер, дошедший до вывода журнала
любым написанием, заменяется маской `mask_phone` (D-10) в любом поле события; статический гейт
приватности остаётся вторым рубежом, а место вызова номер не кладёт и маской (D-11).

ЧТО «ПОХОЖЕ НА НОМЕР» — решение владельца О-24 (а): подстрока, которую нормализатор фазы признаёт
номером хотя бы одним путём, плюс разбивка показа `format_phone`. Таблицы ниже — из замера
планирования и решения владельца; их не подгоняют под маску:

- `MASKED_SUBSTRINGS` — номер в любом написании → точный вывод маски;
- `VISIBLE_SUBSTRINGS` — то, что О-24 (а) велит оставить видным (ID групп `-100…`, JID групп,
  метки времени, UUID, уже наложенная маска): вывод равен входу;
- `NAMED_COST_SUBSTRINGS` — названная безвредная цена О-24 (а): цепочка 7–10 цифр, которую
  автопуть читает номером, маскируется.
"""

import io
import logging
import random
import sys
import time

import pytest

NUMBER = "+79991234567"
NUMBER_DIGITS = "9991234567"
MASK = "+7 *** ***-**-67"

# Бюджет судов нормализатора на один вызов `mask_numbers` (CR-07; решение владельца О-25 (а),
# свойство 3): сверх него кандидат маскируется без суда — отказ в закрытую.
MASK_JUDGMENT_BUDGET = 64
# Предел времени маски на одно поле журнала. Замер планирования 2026-10-26, HEAD `19c99ffb`
# (код как на `2816cfb2`): прототип ограниченного кандидата — не больше 25 мс на 8 000 знаков
# разбитого входа (`"(1) " * 2000` — 22,5 мс); на HEAD путь запроса из 1 801 знака через
# `setup_logging` и `RequestIdMiddleware` стоил 2,45 с (CR-07). Запас ×10 — на занятую машину.
MASK_FIELD_TIME_BOUND_SECONDS = 0.25

MASKED_SUBSTRINGS = [
    # Истина 1 плана 16-52: 25 форм, которые нормализатор фазы признаёт номером.
    pytest.param("+79991234567", MASK, id="e164"),
    pytest.param("79991234567", MASK, id="reported-without-plus"),
    pytest.param("89991234567", MASK, id="russian-eight"),
    pytest.param("+7 999 123-45-67", MASK, id="display-form"),
    pytest.param("8 (999) 123-45-67", MASK, id="eight-brackets"),
    pytest.param("8-999-123-45-67", MASK, id="eight-dashes"),
    pytest.param("+88812345678", "+888 ******78", id="fragment-auto-path"),
    pytest.param("+888 0123 4567", "+888 ******67", id="fragment-display-split"),
    pytest.param("79991234567@s.whatsapp.net", MASK + "@s.whatsapp.net", id="whatsapp-jid"),
    pytest.param(
        "[parameters: ('+79991234567', 5)]", "[parameters: ('" + MASK + "', 5)]", id="sqlalchemy-parameters"
    ),
    pytest.param("+7 (999) 123-45-67", MASK, id="plus-seven-brackets"),
    pytest.param("88812345678", "+888 ******78", id="fragment-without-plus"),
    pytest.param("8 999 123 45 67", MASK, id="eight-spaces"),
    pytest.param("+7-999-123-45-67", MASK, id="plus-seven-dashes"),
    pytest.param("8(999)123-45-67", MASK, id="eight-brackets-tight"),
    pytest.param("+7(999)1234567", MASK, id="plus-seven-brackets-tight"),
    pytest.param("phone=+79991234567", "phone=" + MASK, id="key-value"),
    pytest.param('{"phone": "+79991234567"}', '{"phone": "' + MASK + '"}', id="json-text"),
    pytest.param("79991234567:12@s.whatsapp.net", MASK + ":12@s.whatsapp.net", id="whatsapp-device-jid"),
    pytest.param(
        "DETAIL:  Key (phone)=(+79991234567) already exists.",
        "DETAIL:  Key (phone)=(" + MASK + ") already exists.",
        id="postgres-detail",
    ),
    pytest.param("+7 999 1234567", MASK, id="plus-seven-two-groups"),
    pytest.param("tel:+79991234567", "tel:" + MASK, id="tel-uri"),
    pytest.param("call +79991234567 now", "call " + MASK + " now", id="inside-prose"),
    pytest.param("8 999 123-45-67", MASK, id="eight-mixed"),
    pytest.param("+888 01234567", "+888 ******67", id="fragment-display-form"),
    # Соседи замера.
    pytest.param("+375 29 123 45 67", "+375 ** ***-**-67", id="belarus"),
    pytest.param("(999) 123-45-67", MASK, id="brackets-without-country"),
    pytest.param("+77011234567", "+7 *** *** **67", id="kazakhstan"),
    pytest.param("+7 701 123 4567", "+7 *** *** **67", id="kazakhstan-display"),
    pytest.param("+1 202-555-0143", "+1 ***-***-**43", id="usa"),
    pytest.param("звонок 79991234567.", "звонок " + MASK + ".", id="sentence-end"),
    pytest.param("{'phone': 79991234567}", "{'phone': " + MASK + "}", id="dict-repr"),
    pytest.param("x 79991234567:12 y", "x " + MASK + ":12 y", id="raw-jid-in-text"),
    pytest.param("id=79991234567", "id=" + MASK, id="assignment"),
    # Разбивка Юникода, которую нормализатор читает номером (WR-39; О-25 (а), свойство 2): маска
    # судит копию текста, где эти знаки свёрнуты в знаки грамматики (`_NUMBER_FOLD`).
    pytest.param("+7\xa0999\xa0123\xa045\xa067", MASK, id="nbsp-split"),
    pytest.param("+7 999 123‑45‑67", MASK, id="non-breaking-hyphen"),
    pytest.param("＋７９９９１２３４５６７", MASK, id="fullwidth-plus-and-digits"),
    pytest.param("+７９９９１２３４５６７", MASK, id="fullwidth-digits"),
    pytest.param("8\xa0(999)\xa0123-45-67", MASK, id="russian-eight-with-nbsp"),
    pytest.param("+" + "".join(chr(0x0660 + int(d)) for d in "79991234567"), MASK, id="arabic-indic-digits"),
    pytest.param("+7–999–123–45–67", MASK, id="en-dash-split"),
    pytest.param("+7　999　123　45　67", MASK, id="ideographic-space-split"),
]

VISIBLE_SUBSTRINGS = [
    # Истина 2 плана 16-52, значения решения владельца О-24 (а) — дословно.
    pytest.param("-1001234567890", id="telegram-group-id"),
    pytest.param("1001234567890", id="telegram-group-id-unsigned"),
    pytest.param("+1001234567890", id="telegram-group-id-plus"),
    pytest.param("120363012345678901@g.us", id="whatsapp-group-jid"),
    pytest.param("1729500000000", id="timestamp-ms"),
    pytest.param("20261022063000", id="timestamp-compact"),
    pytest.param("2026-10-22T06:30:00.123456Z", id="timestamp-iso"),
    pytest.param("2026-10-22 06:30:00+00:00", id="timestamp-with-offset"),
    pytest.param("550e8400-e29b-41d4-a716-446655440000", id="uuid"),
    pytest.param("55084001-e29b-41d4-a716-446655440000", id="uuid-digit-group"),
    pytest.param("127.0.0.1:8000", id="address"),
    pytest.param("account_id=42", id="account-id"),
    pytest.param("phone_set=True", id="phone-set"),
    pytest.param("12345678.90", id="decimal"),
    pytest.param("-123456789", id="small-group-id"),
    pytest.param("+7 *** ***-**-67", id="applied-mask"),
    pytest.param("+888 ******78", id="applied-fragment-mask"),
    pytest.param("d41d8cd98f00b204e9800998ecf8427e", id="hex-32"),
    pytest.param("1234567890123456789", id="nineteen-digits"),
    pytest.param("group_id=-1001234567890", id="group-id-field"),
    pytest.param("{'group_id': -1001234567890}", id="group-id-dict-repr"),
    pytest.param("send_forbidden -1001234567890", id="group-id-in-prose"),
    pytest.param("+51 ******89", id="applied-cost-mask"),
    pytest.param("+49 **** **67", id="applied-cost-mask-spaced"),
    pytest.param("+1 ******89", id="applied-short-mask"),
    pytest.param("2026-10-22", id="date"),
    pytest.param("1729500000000-0", id="redis-stream-id"),
    pytest.param("ts=1729500000.123456", id="timestamp-float-seconds"),
]

NAMED_COST_SUBSTRINGS = [
    # Истина 3 плана 16-52: цепочка 7–10 цифр, которую автопуть читает номером.
    pytest.param("5123456789", "+51 ******89", id="peru"),
    pytest.param("123456789", "+1 ******89", id="nine-digits"),
    pytest.param("1234567", "+1 ****67", id="seven-digits"),
    pytest.param("4951234567", "+49 **** **67", id="germany"),
]


def _plain(table: list) -> list[str]:
    return [row.values[0] for row in table]


@pytest.mark.parametrize(("text", "expected"), MASKED_SUBSTRINGS)
def test_a_number_the_normalizer_recognises_is_masked(text, expected):
    from app.services.log_masking import mask_numbers

    assert mask_numbers(text) == expected, f"номер не замаскирован или маска не та: {text!r}"


@pytest.mark.parametrize("text", VISIBLE_SUBSTRINGS)
def test_what_the_normalizer_does_not_read_as_a_number_stays_visible(text):
    from app.services.log_masking import mask_numbers

    assert mask_numbers(text) == text, f"маска спрятала то, что О-24 (а) велит оставить видным: {text!r}"


@pytest.mark.parametrize(("text", "expected"), NAMED_COST_SUBSTRINGS)
def test_the_named_cost_masks_an_id_the_auto_path_reads_as_a_number(text, expected):
    from app.services.log_masking import mask_numbers

    assert mask_numbers(text) == expected, f"названная цена О-24 (а) разошлась с таблицей: {text!r}"


def test_masking_is_idempotent():
    from app.services.log_masking import mask_numbers

    texts = _plain(MASKED_SUBSTRINGS) + _plain(VISIBLE_SUBSTRINGS) + _plain(NAMED_COST_SUBSTRINGS)
    changed = [text for text in texts if mask_numbers(mask_numbers(text)) != mask_numbers(text)]
    assert changed == [], f"повторное наложение маски изменило вывод: {changed}"


def test_masking_never_raises():
    from app.services.log_masking import mask_numbers

    many = " ".join([NUMBER] * 1000)
    texts = ["1" * 100, "+" * 50 + "()" * 50, "\x00", "", many, "8 " * 500, "(" * 300 + "8" * 300]
    for text in texts:
        masked = mask_numbers(text)
        assert isinstance(masked, str), f"маска вернула не строку на {text[:40]!r}"
    assert NUMBER_DIGITS not in mask_numbers(many), "в длинном тексте с тысячей номеров номер уцелел"


# --- Стоимость маски на поле журнала (CR-07; решение владельца О-25 (а), свойство 3) -----------


def _random_split_inputs(length: int) -> dict[str, str]:
    """Пять случайных разбитых входов длины `length` (зерно 11) — формы замера планирования."""
    rnd = random.Random(11)

    def digits(count: int) -> str:
        return "".join(rnd.choice("0123456789") for _ in range(count))

    makers = (
        ("(d) ", lambda: f"({digits(1)}) "),
        ("8 d ", lambda: f"8 {digits(1)} "),
        ("(dd)", lambda: f"({digits(2)})"),
        ("8 (ddd) ", lambda: f"8 ({digits(3)}) "),
        ("nine-digit-chains", lambda: digits(9) + " "),
    )
    inputs = {}
    for name, make in makers:
        pieces: list[str] = []
        size = 0
        while size < length:
            piece = make()
            pieces.append(piece)
            size += len(piece)
        inputs[name] = "".join(pieces)[:length]
    return inputs


def _counting_judge(monkeypatch) -> list[int]:
    """Счётчик судов: обёртка над судьёй маски `log_masking._recognised`."""
    from app.services import log_masking

    calls = [0]
    judge = log_masking._recognised

    def counted(text: str) -> str | None:
        calls[0] += 1
        return judge(text)

    monkeypatch.setattr(log_masking, "_recognised", counted)
    return calls


def test_the_mask_judges_at_most_the_budget_per_field(monkeypatch):
    """Один вызов маски судит не больше `MASK_JUDGMENT_BUDGET` кандидатов (CR-07)."""
    from app.services import log_masking

    calls = _counting_judge(monkeypatch)
    judged = {}
    for name, text in _random_split_inputs(400).items():
        calls[0] = 0
        log_masking.mask_numbers(text)
        judged[name] = calls[0]
    module_budget = vars(log_masking).get("MASK_JUDGMENT_BUDGET")
    assert module_budget == MASK_JUDGMENT_BUDGET and max(judged.values()) <= MASK_JUDGMENT_BUDGET, (
        f"маска судит больше кандидатов, чем названный бюджет поля (CR-07): судов {judged}, "
        f"бюджет модуля маски {module_budget!r}, названный {MASK_JUDGMENT_BUDGET}"
    )


# Входы правила стоимости: повторы замера ревью CR-07 и пять случайных разбитых входов по 8 000
# знаков (8 КБ — предел строки запроса nginx). Замер исполнения 16-60 (2026-10-26, лучшее из трёх):
# 11,5 / 3,6 / 3,1 мс у повторов и 3,4…6,3 мс у случайных; на базе `"(1) " * 2000` шёл бы минутами.
MASK_COST_INPUTS = [
    pytest.param("(1) " * 2000, id="bracket-one-x2000"),
    pytest.param("8 " * 4000, id="eight-x4000"),
    pytest.param("(12)" * 2000, id="bracket-twelve-x2000"),
    *(pytest.param(text, id=f"random-{name.strip()}") for name, text in _random_split_inputs(8000).items()),
]


@pytest.mark.parametrize("text", MASK_COST_INPUTS)
def test_a_long_split_field_is_masked_in_bounded_time(monkeypatch, text):
    """Поле из 8 000 знаков разбитого входа — в предел времени и в бюджет судов; номера не остаётся."""
    import gc

    from app.services import log_masking

    calls = _counting_judge(monkeypatch)
    gc.collect()  # сборка мусора большой суиты — не цена маски: до окна замера
    started = time.perf_counter()
    masked = log_masking.mask_numbers(text)
    elapsed = time.perf_counter() - started

    assert elapsed <= MASK_FIELD_TIME_BOUND_SECONDS, (
        f"поле из {len(text)} знаков маскируется {elapsed:.3f} с — дольше названного предела "
        f"{MASK_FIELD_TIME_BOUND_SECONDS} с (CR-07)"
    )
    assert calls[0] <= MASK_JUDGMENT_BUDGET, f"судов {calls[0]} — больше бюджета {MASK_JUDGMENT_BUDGET} (CR-07)"
    assert log_masking.mask_numbers(masked) == masked, (
        "в выводе маски остался кандидат, который маска признаёт номером: замаскировано не всё"
    )


def test_beyond_the_budget_a_candidate_is_masked_closed():
    """Сверх бюджета судов кандидат получает `*` вместо цифр — номер не утекает (отказ в закрытую)."""
    from app.services.log_masking import mask_numbers

    numbers = [f"+7 999 123-45-{index:02d}" for index in range(70)]
    masked = mask_numbers(", ".join(numbers))

    closed = "+* *** ***-**-**"
    assert masked.count(closed) == 70 - MASK_JUDGMENT_BUDGET, (
        f"сверх бюджета {MASK_JUDGMENT_BUDGET} судов кандидат не замаскирован в закрытую: {masked[-120:]!r}"
    )
    assert masked.count("+7 *** ***-**-") == MASK_JUDGMENT_BUDGET, "в пределах бюджета маска не та"
    assert "999" not in masked and "123" not in masked, f"номер уцелел в поле сверх бюджета: {masked!r}"
    assert mask_numbers(masked) == masked, "повторное наложение маски изменило поле с отказом в закрытую"


# --- Знаки, которые нормализатор читает в номере (WR-39; О-25 (а), свойство 2) ------------------

# Знаки, которые нормализатор читает внутри номера, а маска НЕ сворачивает — граница 16-52:
# `.`, `/`, `[`, `]` (дроби, адреса, пути) и их полноширинные двойники; `*` — знак самой маски
# (свёртка сломала бы идемпотентность). Замер планирования: перебор U+0021…U+FFFF под прототипом
# свёртки дал ровно эти девять.
MASK_BOUNDARY_CHARACTERS = ("*", ".", "/", "[", "]", "．", "／", "［", "］")

_NOT_READ = "нормализатор номером не читает (замер) — по О-24 (а) это не номер"
_BOUNDARY_SPLIT = "нормализатор читает, маска не сворачивает — граница 16-52 (дроби, адреса, пути)"
_LETTER_EDGE = "номер, прилегающий к букве, — край `_LEFT` грамматики (ID, хэши, слитный текст)"
_GRAMMAR_START = (
    "начало вне грамматики разбивки (`8` перед `)`, шесть цифр в скобках начала): нормализатор читает, "
    "маска не маскировала и до плана 16-60 — замер сверки «база ↔ HEAD», семейство (b)"
)

MASK_BOUNDARY_SUBSTRINGS = [
    pytest.param("+7.999.123.45.67", _BOUNDARY_SPLIT, id="full-stop-split"),
    pytest.param("+7*999*123*45*67", "звезда — знак самой маски; свёртка сломала бы идемпотентность", id="asterisk-split"),
    pytest.param("+7/999/123/45/67", _BOUNDARY_SPLIT, id="solidus-split"),
    pytest.param("+7[999]123[45]67", _BOUNDARY_SPLIT, id="square-bracket-split"),
    pytest.param("+7．999．123．45．67", _BOUNDARY_SPLIT, id="fullwidth-full-stop-split"),
    pytest.param("+7 999 123 45 67", _NOT_READ, id="narrow-nbsp-split"),
    pytest.param("+7 999 123 45 67", _NOT_READ, id="thin-space-split"),
    pytest.param("id79991234567", _LETTER_EDGE, id="number-after-a-letter"),
    pytest.param("x+79991234567", _LETTER_EDGE, id="plus-after-a-letter"),
    pytest.param("8)999)123)45)67", _GRAMMAR_START, id="eight-before-closing-bracket"),
    pytest.param("(999123) 45 67", _GRAMMAR_START, id="six-digit-bracket-start"),
]


def _reads_the_number(text: str) -> bool:
    from app.services.phone import PhoneError, normalize_manual

    try:
        return normalize_manual(text) == NUMBER
    except PhoneError:
        return False


@pytest.mark.parametrize(("text", "reason"), MASK_BOUNDARY_SUBSTRINGS)
def test_a_named_boundary_substring_stays_visible_and_is_named(text, reason):
    """Строка границы видна как есть; у U+202F и U+2009 утверждается и причина — нормализатор не читает."""
    from app.services.log_masking import mask_numbers

    assert mask_numbers(text) == text, f"строка границы изменена маской: {text!r} ({reason})"
    if reason == _NOT_READ:
        assert not _reads_the_number(text), f"нормализатор читает номером строку, названную нечитаемой: {text!r}"


def test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named():
    """Каждый знак U+0021…U+FFFF и каждый блок цифр `Nd`, которые нормализатор читает в номере, —
    маскируются или названы в `MASK_BOUNDARY_CHARACTERS` (лишнее имя краснит тоже)."""
    import unicodedata

    from app.services.log_masking import mask_numbers

    grammar = set("0123456789 -()+")
    read_unmasked: set[str] = set()
    problems: list[str] = []
    for code in range(0x21, 0x10000):
        if 0xD800 <= code <= 0xDFFF or chr(code) in grammar:
            continue
        ch = chr(code)
        form = f"+7{ch}999{ch}123{ch}45{ch}67"
        if not _reads_the_number(form):
            continue
        masked = mask_numbers(form)
        if masked == MASK:
            continue
        if masked == form:
            read_unmasked.add(ch)
        else:
            problems.append(f"U+{code:04X}: частичная маска")
    for zero in range(0x110000):
        ch = chr(zero)
        if zero == 0x30 or unicodedata.category(ch) != "Nd" or unicodedata.digit(ch) != 0:
            continue
        form = "+" + "".join(chr(zero + int(digit)) for digit in "79991234567")
        if _reads_the_number(form) and mask_numbers(form) != MASK:
            problems.append(f"блок цифр U+{zero:04X}")
    unnamed = sorted(f"U+{ord(ch):04X}" for ch in read_unmasked - set(MASK_BOUNDARY_CHARACTERS))
    extra = sorted(f"U+{ord(ch):04X}" for ch in set(MASK_BOUNDARY_CHARACTERS) - read_unmasked)
    assert not unnamed and not extra and not problems, (
        f"знак, который нормализатор читает в номере, маска не маскирует и граница его не называет "
        f"(WR-39): не названы {unnamed}; лишние имена границы {extra}; {problems[:12]} "
        f"(всего {len(problems)})"
    )


class _Carrier:
    """Объект, чей `repr` несёт номер."""

    def __repr__(self) -> str:
        return f"Carrier({NUMBER})"


def test_the_processor_masks_every_kind_of_value():
    """Процессор проходит любое поле события и не меняет исходный словарь."""
    from app.services.log_masking import mask_numbers_in_event

    carrier = _Carrier()
    event = {
        "event": f"call {NUMBER}",
        "phone_raw": 79991234567,
        "group_id": -1001234567890,
        "flag": True,
        "nothing": None,
        "ratio": 1.5,
        "nested": {"inner": [NUMBER, ("x", {"k": NUMBER})]},
        "tags": {NUMBER},
        "positional_args": (NUMBER, 7),
        "carrier": carrier,
        NUMBER: "key",
    }
    before = repr(event)

    masked = mask_numbers_in_event(None, "info", event)

    assert masked is not event, "процессор вернул тот же словарь, а не новый"
    assert repr(event) == before, "процессор изменил исходный словарь события"
    assert masked["event"] == f"call {MASK}"
    assert masked["phone_raw"] == MASK, "номер-целое не стал строкой маски"
    assert masked["group_id"] == -1001234567890, "ID группы-целое изменён (О-24 (а))"
    assert masked["flag"] is True and masked["nothing"] is None and masked["ratio"] == 1.5
    assert masked["nested"] == {"inner": [MASK, ("x", {"k": MASK})]}
    assert masked["tags"] == [MASK]
    assert masked["positional_args"] == (MASK, 7)
    assert masked["carrier"] == f"Carrier({MASK})"
    assert masked[MASK] == "key", "номер в ключе поля не замаскирован"
    assert NUMBER_DIGITS not in repr(masked), f"номер уцелел в событии: {masked!r}"


def _masking_filter_class():
    from app.services import log_masking

    found = log_masking.__dict__.get("NumberMaskingFilter")
    assert found is not None, "фильтра stdlib `NumberMaskingFilter` нет: запись мимо процессора печатает номер"
    return found


def _record(msg, args, exc_info=None, stack_info=None) -> logging.LogRecord:
    return logging.LogRecord("app.form", logging.WARNING, __file__, 1, msg, args, exc_info, sinfo=stack_info)


def test_the_filter_masks_a_stdlib_record_and_keeps_argument_types():
    masking = _masking_filter_class()()

    record = _record("x %s and %d", (NUMBER, 7))
    assert masking.filter(record) is True, "фильтр уронил запись"
    assert record.getMessage() == f"x {MASK} and 7", f"сообщение записи не замаскировано: {record.getMessage()!r}"
    assert record.args[1] == 7 and type(record.args[1]) is int, f"тип аргумента `%d` изменён: {record.args!r}"

    whole = _record("x %d", (79991234567,))
    assert masking.filter(whole) is True
    assert whole.getMessage() == f"x {MASK}", f"номер-целое под `%d` не замаскирован: {whole.getMessage()!r}"


class _Unprintable:
    def __str__(self) -> str:
        raise RuntimeError("no text")

    def __repr__(self) -> str:
        raise RuntimeError("no repr")


def test_the_filter_never_raises_and_masks_the_logging_error_report(monkeypatch):
    masking_class = _masking_filter_class()
    from app.services.log_masking import attach_number_masking

    report = io.StringIO()
    monkeypatch.setattr(sys, "stderr", report)
    handler = logging.StreamHandler(io.StringIO())
    attach_number_masking(handler)
    assert any(isinstance(item, masking_class) for item in handler.filters)

    handler.handle(_record("bad %d", (NUMBER,)))

    text = report.getvalue()
    assert "--- Logging error ---" in text, f"отчёт об ошибке подстановки не напечатан: {text!r}"
    assert NUMBER_DIGITS not in text, f"отчёт `--- Logging error ---` напечатал номер: {text!r}"

    unprintable = _record(_Unprintable(), ())
    assert masking_class().filter(unprintable) is True, "фильтр уронил запись с непечатаемым сообщением"


def test_the_filter_masks_exception_text_and_stack_info():
    masking = _masking_filter_class()()
    try:
        raise ValueError(f"duplicate {NUMBER}")
    except ValueError:
        exc_info = sys.exc_info()
    record = _record("failed", (), exc_info=exc_info, stack_info=f"Stack (most recent call last):\n  phone {NUMBER}")

    assert masking.filter(record) is True
    rendered = logging.Formatter().format(record)

    assert "duplicate" in rendered and "Stack (most recent call last)" in rendered
    assert NUMBER_DIGITS not in rendered, f"текст исключения или `stack_info` несёт номер: {rendered!r}"
    assert MASK in rendered


HEADER_TERMS = (
    "О-23 (а)",
    "свойство 2",
    "О-24 (а)",
    "normalize_reported",
    "normalize_manual",
    "format_phone",
    "-100",
    "JID",
    "метки времени",
    "названная цена",
    "print",
    "max_worker",
    "wa_worker",
    "uvicorn",
    "второй рубеж",
    # План 16-60 (О-25 (а), свойства 1, 3, 5; О-26 (а)): где маска стоит, стоимость, края.
    "О-25 (а)",
    "celery.signals.setup_logging",
    "beat",
    "prefork",
    "MASK_JUDGMENT_BUDGET",
    "отказ в закрытую",
    "отказ в обслуживании",
    "CR-07",
    "WR-39",
    "IN-25",
    "flower",
    "Alembic",
    "U+00A0",
    "U+2011",
    "U+202F",
    "U+2009",
)

BOUNDARY_SECTION = "ГРАНИЦА, НАЗВАННАЯ ПРЯМО"


def _boundary_section(header: str) -> str:
    found = header.find(BOUNDARY_SECTION)
    return "" if found < 0 else header[found:]


def _boundary_names(text: str) -> tuple[str, ...]:
    """Как строка границы может быть названа в шапке: сама строка, имя её знака или знак в кавычках."""
    if text.startswith("+7") and not text[2].isdigit():
        separator = text[2]
        return text, f"U+{ord(separator):04X}", f"`{separator}`"
    return (text,)


def test_the_masking_module_names_what_it_masks_and_its_boundary():
    """Шапка модуля маски называет решение, что маскируется, что видно, цену и границу; докстринг
    `mask_phone` говорит правду о маске в журнале (D-11: место вызова номер не кладёт, маска —
    последний рубеж процессора). Каждая строка `MASK_BOUNDARY_SUBSTRINGS` названа в «ГРАНИЦЕ»."""
    from app.services import log_masking, phone

    header = " ".join((log_masking.__doc__ or "").split())
    missing = [term for term in HEADER_TERMS if term not in header]
    section = _boundary_section(header)
    missing += [
        f"ГРАНИЦА: {row.id}"
        for row in MASK_BOUNDARY_SUBSTRINGS
        if not any(name in section for name in _boundary_names(row.values[0]))
    ]
    mask_doc = " ".join((phone.mask_phone.__doc__ or "").split())
    untrue = [
        problem
        for problem, present in (
            ("докстринг `mask_phone` утверждает «НЕ ПОПАДАЕТ ДАЖЕ МАСКОЙ»", "НЕ ПОПАДАЕТ ДАЖЕ МАСКОЙ" in mask_doc),
            ("докстринг `mask_phone` не называет «последний рубеж»", "последний рубеж" not in mask_doc),
            ("докстринг `mask_phone` не называет D-11", "D-11" not in mask_doc),
        )
        if present
    ]
    assert not missing and not untrue, (
        f"шапка маски не называет, что маскирует и где её граница: нет {missing}; {untrue}"
    )


# --- Процессы без `setup_logging` (О-25 (а), свойство 5; О-26 (а)) ------------------------------


def _repo_root():
    from pathlib import Path

    return Path(__file__).resolve().parents[2]


def _calls_or_imports_setup_logging(path) -> bool:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "setup_logging" for alias in node.names):
            return True
        if isinstance(node, ast.Name) and node.id == "setup_logging":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "setup_logging":
            return True
    return False


def _measure_scripts() -> str | None:
    scripts = sorted((_repo_root() / "scripts").glob("*.py"))
    found = [path.name for path in scripts if _calls_or_imports_setup_logging(path)]
    return f"скрипты ввозят или зовут `setup_logging`: {found}" if found else None


def _measure_alembic() -> str | None:
    import ast

    path = _repo_root() / "alembic" / "env.py"
    called = {
        node.func.id
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if "fileConfig" not in called or _calls_or_imports_setup_logging(path):
        return "`alembic/env.py` не зовёт `fileConfig` или зовёт `setup_logging`"
    return None


def _measure_max_worker() -> str | None:
    sources = sorted((_repo_root() / "max_worker").rglob("*.py"))
    found = [path.name for path in sources if _calls_or_imports_setup_logging(path)]
    return f"`max_worker` ввозит `setup_logging`: {found}" if found else None


def _measure_flower() -> str | None:
    import inspect

    import flower.command

    source = inspect.getsource(flower.command)
    if "def setup_logging" not in source or "log.setup(" in source:
        return "`flower.command` больше не настраивает журнал сам (свой `setup_logging` tornado)"
    return None


def _measure_wa_worker() -> str | None:
    found = [
        str(path)
        for path in (_repo_root() / "wa_worker").rglob("*.py")
        if "node_modules" not in path.parts
    ]
    return f"в `wa_worker` есть файлы Python: {found}" if found else None


# Процессы, где маски на исполнении нет: `setup_logging` в них не вызывается (имя в шапке, замер).
# Там остаётся только статический гейт приватности (D-17) — единственный рубеж.
PROCESSES_WITHOUT_SETUP_LOGGING = (
    ("scripts/", _measure_scripts),
    ("Alembic", _measure_alembic),
    ("max_worker", _measure_max_worker),
    ("flower", _measure_flower),
    ("wa_worker", _measure_wa_worker),
)


def test_the_processes_without_setup_logging_are_measured_and_named():
    """Каждый процесс без `setup_logging` — замер держится и процесс назван в «ГРАНИЦЕ» шапки маски."""
    from app.services import log_masking

    section = _boundary_section(" ".join((log_masking.__doc__ or "").split()))
    unmeasured = [
        f"{name}: {problem}" for name, measure in PROCESSES_WITHOUT_SETUP_LOGGING if (problem := measure())
    ]
    unnamed = [name for name, _measure in PROCESSES_WITHOUT_SETUP_LOGGING if name not in section]
    assert not unmeasured, (
        f"замер процесса без `setup_logging` не держится: {unmeasured} — процесс начал настраивать "
        "журнал маской; убрать строку из шапки маски и из `PROCESSES_WITHOUT_SETUP_LOGGING` (это не поломка)"
    )
    assert not unnamed, f"шапка маски не называет в «ГРАНИЦЕ» процессы без `setup_logging`: {unnamed}"

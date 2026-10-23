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
import sys

import pytest

NUMBER = "+79991234567"
NUMBER_DIGITS = "9991234567"
MASK = "+7 *** ***-**-67"

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
)


def test_the_masking_module_names_what_it_masks_and_its_boundary():
    """Шапка модуля маски называет решение, что маскируется, что видно, цену и границу; докстринг
    `mask_phone` говорит правду о маске в журнале (D-11: место вызова номер не кладёт, маска —
    последний рубеж процессора)."""
    from app.services import log_masking, phone

    header = " ".join((log_masking.__doc__ or "").split())
    missing = [term for term in HEADER_TERMS if term not in header]
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

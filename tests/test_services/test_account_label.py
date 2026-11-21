"""Правило подписи аккаунта (Фаза 17, D-02, D-03, D-07, D-12, D-14): таблицы без БД.

Образец — `tests/test_services/test_phone.py`: чистая функция, `parametrize` с
поимёнными `id`. Здесь закреплено то, чего экраны не должны решать сами:
пустое значение читается как «Номер неизвестен», неразбираемое — показывается
как есть, двойник определяется по ГОТОВОЙ подписи внутри мессенджера, а
плоская форма для `<title>`, `<option>` и `title=` собирается из того же правила.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from app.services import account_label as module
from app.services.account_label import (
    PHONE_UNKNOWN_TEXT,
    AccountRow,
    build_labels,
    label_of,
    shown_phone,
)
from tests.account_label_support import MANUAL_MARK

# Значение колонки → то, что показывает экран (None — «Номер неизвестен», D-02, D-07).
SHOWN = [
    pytest.param(None, None, id="null"),
    pytest.param("", None, id="empty"),
    pytest.param("   ", None, id="blank"),
    pytest.param("+79991234567", "+7 999 123-45-67", id="russia"),
    pytest.param("+77011234567", "+7 701 123 4567", id="kazakhstan"),
    pytest.param("+88801234567", "+888 01234567", id="fragment"),
    pytest.param("abc", "abc", id="unparseable-word"),
    pytest.param("=1+1", "=1+1", id="unparseable-formula"),
    pytest.param("<b>x</b>", "<b>x</b>", id="unparseable-markup"),
]

# Двойники (D-03, D-14): наборы строк (id, type, phone) и id, которые должны стать двойниками.
TWINS = [
    pytest.param(
        [(1, "wa", None), (2, "wa", None)], {1, 2}, id="two-whatsapp-without-a-number"
    ),
    pytest.param(
        [(1, "wa", None), (2, "wa", "")], {1, 2}, id="null-and-empty-are-the-same-label"
    ),
    pytest.param(
        [(1, "tg_user", "+79991234567"), (2, "tg_user", "+7 999 123-45-67")],
        {1, 2},
        id="one-number-spelled-two-ways",
    ),
    pytest.param(
        [(1, "tg_user", "+79991234567"), (2, "wa", "+79991234567")],
        set(),
        id="telegram-and-whatsapp-with-one-number-are-not-twins",
    ),
    pytest.param(
        [(1, "tg_user", None), (2, "wa", None)], set(), id="unknown-in-two-messengers-are-not-twins"
    ),
    pytest.param(
        [(1, "tg_user", "+79991234567"), (2, "tg_user", "+77011234567")],
        set(),
        id="unique-numbers-carry-no-id",
    ),
    pytest.param(
        [(1, "tg_user", "abc"), (2, "tg_user", "abc")], {1, 2}, id="two-equal-unparseable-values"
    ),
    pytest.param(
        [(1, "wa", None), (2, "wa", None), (3, "wa", "+79991234567")],
        {1, 2},
        id="a-third-account-with-a-number-is-not-dragged-in",
    ),
]


def _rows(table: list[tuple[int, str, str | None]]) -> list[AccountRow]:
    return [AccountRow(*item) for item in table]


@pytest.mark.parametrize("stored,expected", SHOWN)
def test_shown_phone_table(stored, expected):
    assert shown_phone(stored) == expected


@pytest.mark.parametrize("blank", ["", "   "], ids=["empty", "blank"])
def test_a_blank_stored_number_reads_as_unknown(blank):
    """D-02: пустая и пробельная строка — «Номер неизвестен», а не пустая подпись."""
    label = build_labels([AccountRow(1, "wa", blank)])[1]

    assert label.phone_text is None, "пустое значение колонки не должно давать подпись"
    assert label.text == PHONE_UNKNOWN_TEXT == "Номер неизвестен"


@pytest.mark.parametrize("stored", ["abc", "=1+1", "<b>x</b>"])
def test_an_unparseable_number_is_shown_as_it_is_not_as_unknown(stored):
    """D-07: сохранённый, но неразбираемый номер — как есть."""
    label = build_labels([AccountRow(1, "tg_user", stored)])[1]

    assert label.phone_text == stored
    assert label.text == stored
    assert label.plain == f"Telegram {stored}"


@pytest.mark.parametrize("table,twins", TWINS)
def test_twins_are_found_by_the_ready_label_inside_one_messenger(table, twins):
    labels = build_labels(_rows(table))

    assert {i for i, label in labels.items() if label.twin} == twins


@pytest.mark.parametrize("table,twins", TWINS)
def test_the_plain_form_carries_the_id_only_for_a_twin(table, twins):
    labels = build_labels(_rows(table))

    for account_id, label in labels.items():
        assert ("#" in label.plain) is (account_id in twins), (
            f"#id у {account_id}: ожидали {account_id in twins}, подпись {label.plain!r}"
        )


def test_a_twin_plain_label_reads_whatsapp_unknown_with_its_id():
    labels = build_labels(_rows([(12, "wa", None), (13, "wa", None)]))

    assert labels[12].plain == "WhatsApp Номер неизвестен #12"
    assert labels[13].plain == "WhatsApp Номер неизвестен #13"


def test_a_unique_plain_label_reads_channel_and_number():
    labels = build_labels(_rows([(5, "tg_user", "+79991234567")]))

    assert labels[5].plain == "Telegram +7 999 123-45-67"
    assert "#" not in labels[5].plain


def test_plain_with_id_always_carries_the_id():
    labels = build_labels(_rows([(5, "tg_user", "+79991234567"), (6, "wa", None)]))

    assert labels[5].plain_with_id == "Telegram +7 999 123-45-67 #5"
    assert labels[6].plain_with_id == "WhatsApp Номер неизвестен #6"


def test_an_unfamiliar_type_keeps_its_own_word_as_the_channel():
    labels = build_labels(_rows([(7, "viber", None)]))

    assert labels[7].channel == "viber"
    assert labels[7].plain == "viber Номер неизвестен"


@pytest.mark.parametrize("table,_twins", TWINS)
def test_label_of_agrees_with_build_labels(table, _twins):
    rows = _rows(table)
    labels = build_labels(rows)

    for row in rows:
        assert label_of(row, rows) == labels[row.id]
        assert label_of(row, ()).twin is False, "без соседей двойника быть не может"


def test_label_of_does_not_need_the_subject_among_the_rows():
    twin_of_a_stranger = AccountRow(9, "wa", None)

    assert label_of(twin_of_a_stranger, [AccountRow(1, "wa", None)]).twin is True
    assert label_of(twin_of_a_stranger, [AccountRow(1, "tg_user", None)]).twin is False


def test_a_manual_number_carries_the_flag_and_the_text_stays_the_same():
    """D-10: признак приезжает в подпись, а `text` и `plain` остаются прежними."""
    label = build_labels([AccountRow(1, "tg_user", "+79991234567", True)])[1]

    assert label.phone_is_manual is True
    assert label.text == "+7 999 123-45-67"
    assert label.plain == "Telegram +7 999 123-45-67"


def test_a_manual_and_an_automatic_number_with_the_same_text_are_still_twins():
    """D-10: признак вне ключа двойника — ручной и автоматический одинаковые номера двойники."""
    rows = [
        AccountRow(1, "tg_user", "+79991234567", True),
        AccountRow(2, "tg_user", "+7 999 123-45-67", False),
    ]

    labels = build_labels(rows)

    assert labels[1].twin is True and labels[2].twin is True
    for row in rows:
        assert label_of(row, rows).twin is True, "label_of обязан судить двойника так же, как build_labels"
        assert label_of(row, rows) == labels[row.id]
    assert labels[1].phone_is_manual is True and labels[2].phone_is_manual is False


@pytest.mark.parametrize("twin", [False, True], ids=["unique", "twin"])
def test_plain_forms_never_carry_the_manual_mark(twin):
    """D-10: `text`, `plain`, `plain_with_id` — только простой текст подписи."""
    rows = [AccountRow(1, "tg_user", "+79991234567", True)]
    if twin:
        rows.append(AccountRow(2, "tg_user", "+79991234567", False))

    label = build_labels(rows)[1]

    assert label.phone_is_manual is True, "контроль: флаг у подписи есть, иначе проверка вакуумна"
    for form in (label.text, label.plain, label.plain_with_id):
        assert MANUAL_MARK not in form, f"плоская форма несёт пометку: {form!r}"


@pytest.mark.parametrize("stored", [None, "", "   "], ids=["null", "empty", "blank"])
def test_a_flag_without_a_number_never_marks_the_unknown_label(stored):
    """T-18-01: «Номер неизвестен» с пометкой был бы ложью — флаг без номера не доезжает."""
    rows = [AccountRow(1, "wa", stored, True)]

    label = build_labels(rows)[1]

    assert label.phone_is_manual is False
    assert label.text == PHONE_UNKNOWN_TEXT
    assert label_of(rows[0], rows).phone_is_manual is False


def test_the_module_is_pure():
    """Правило без БД и без Jinja: ввозы — стандартная библиотека и два модуля проекта."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module)

    assert imported, "модуль ничего не ввозит — проверка вакуумна"
    for name in imported:
        root = name.split(".")[0]
        assert root not in {"markupsafe", "jinja2", "sqlalchemy"}, f"{name}: разметка и БД не здесь"
        assert root in sys.stdlib_module_names or name in {"app.constants", "app.services.phone"}, (
            f"{name}: чистое правило ввозит только стандартную библиотеку, app.constants и app.services.phone"
        )

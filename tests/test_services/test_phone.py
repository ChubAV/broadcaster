"""Форма номера телефона аккаунта: критерий 3 Фазы 16, D-05, D-06, D-15, D-18.

Файл — спецификация `app/services/phone.py`, единственного места, где решается
форма номера. Модуль зовут писатель (16-05), подпись Фазы 17, форма ручной
правки Фазы 18 и скрипт Фазы 20, поэтому правила закреплены здесь один раз,
таблицами с поимёнными строками, а не в каждом вызывающем.

Ключевое утверждение файла — трасер
`test_an_automatic_number_lands_in_e164_and_shows_in_the_display_form`: номер,
пришедший от мессенджера ЦЕЛЫМ числом, проходит весь путь до строки показа.
Остальные таблицы закрывают края, на которых правило ломается молча:

- автопуть (`REPORTED_*`) — номер Fragment `+888…` обязан пройти, хотя проверка
  «возможности» библиотеки считает его слишком коротким; мусор источника (сырой
  JID, скобки, лишние цифры, `None`, `bool`) обязан дать `None`, а не «номер»;
- показ (`DISPLAYED`) — разбивка своя у каждой страны, а сохранённое, но
  неразбираемое значение показывается как есть, а не «неизвестен» (D-06).
"""

import pytest

from app.services.phone import format_phone, normalize_reported

E164_RUSSIAN = "+79991234567"
DISPLAY_RUSSIAN = "+7 999 123-45-67"


def test_an_automatic_number_lands_in_e164_and_shows_in_the_display_form():
    """⚠️ ТРАСЕР: целое от мессенджера → E.164 → показ, одним путём.

    Целое — не выдумка: библиотеки мессенджеров отдают номер то строкой без
    `+`, то числом. Если автопуть потеряет целое, номер аккаунта навсегда
    останется неизвестным, хотя источник его сообщил.
    """
    stored = normalize_reported(79991234567)
    assert stored == E164_RUSSIAN, "целое от мессенджера обязано стать строкой E.164"

    shown = format_phone(stored)
    assert shown == DISPLAY_RUSSIAN, "показ — международная разбивка России"
    assert "\xa0" not in shown, "в показе обычные пробелы, а не неразрывные"


REPORTED_ACCEPTED = [
    pytest.param("79991234567", "+79991234567", id="digits_string"),
    pytest.param(79991234567, "+79991234567", id="digits_int"),
    pytest.param(" 79991234567 ", "+79991234567", id="digits_with_spaces_around"),
    pytest.param("+79991234567", "+79991234567", id="already_e164"),
    pytest.param("88801234567", "+88801234567", id="fragment_string"),
    pytest.param(888012345678, "+888012345678", id="fragment_int_12_digits"),
    pytest.param("77011234567", "+77011234567", id="kazakhstan"),
    pytest.param("998901234567", "+998901234567", id="uzbekistan"),
    pytest.param("12345", "+12345", id="five_digits_lower_bound"),
]


@pytest.mark.parametrize("raw,expected", REPORTED_ACCEPTED)
def test_a_reported_number_is_normalized_to_e164(raw, expected):
    """Автопуть: строка или целое от мессенджера → E.164 (D-05, D-15).

    Строка Fragment здесь ОБЯЗАНА пройти: проверка «возможности» назвала бы её
    слишком короткой, поэтому в автопути её нет. Fragment попадает в базу только
    этим путём (решение владельца О-1).
    """
    assert normalize_reported(raw) == expected, f"автопуть обязан принять {raw!r}"


REPORTED_REFUSED = [
    pytest.param("1234", id="four_digits"),
    pytest.param("7999123456789012", id="sixteen_digits"),
    pytest.param("7(999)1234567", id="not_only_digits"),
    pytest.param("79991234567:12", id="raw_jid"),
    pytest.param("999123456", id="unknown_country_code"),
    pytest.param("0", id="zero"),
    pytest.param("abc", id="letters"),
    pytest.param("", id="empty"),
    pytest.param(None, id="none"),
    pytest.param(True, id="bool"),
]


@pytest.mark.parametrize("raw", REPORTED_REFUSED)
def test_garbage_from_a_source_leaves_the_number_unknown(raw):
    """Мусор источника молча даёт `None` (D-18): номер остаётся неизвестным.

    Автопуть не объясняет отказ — объяснять некому, а исключение уронило бы
    вход аккаунта из-за сбоя источника. Скобки и сырой JID — именно сбой:
    автоисточник отдаёт одни цифры.
    """
    assert normalize_reported(raw) is None, f"мусор {raw!r} не должен стать номером"


DISPLAYED = [
    pytest.param("+79991234567", "+7 999 123-45-67", id="russia"),
    pytest.param("+77011234567", "+7 701 123 4567", id="kazakhstan"),
    pytest.param("+88801234567", "+888 01234567", id="fragment"),
    pytest.param("+888012345678", "+888 012345678", id="fragment_12_digits"),
    pytest.param("+998901234567", "+998 90 123 45 67", id="uzbekistan"),
    pytest.param("+12025550123", "+1 202-555-0123", id="usa"),
    pytest.param("+4915123456789", "+49 1512 3456789", id="germany"),
    pytest.param("+79991234", "+7 9991234", id="short_but_parseable"),
    pytest.param("+999123456", "+999123456", id="unparseable_country_as_is"),
    pytest.param("garbage", "garbage", id="unparseable_garbage_as_is"),
    pytest.param("+7abc", "+7abc", id="unparseable_letters_as_is"),
]


@pytest.mark.parametrize("stored,expected", DISPLAYED)
def test_a_stored_number_is_shown_in_the_international_form(stored, expected):
    """Показ — разбивка своей страны; неразбираемое — как есть (D-06).

    «Как есть», а не «неизвестен»: значение в колонке есть, и спрятать его
    значило бы солгать пользователю о состоянии аккаунта.
    """
    shown = format_phone(stored)
    assert shown == expected, f"показ {stored!r}"
    assert "\xa0" not in shown, "в показе обычные пробелы, а не неразрывные"

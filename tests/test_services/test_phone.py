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
  неразбираемое значение показывается как есть, а не «неизвестен» (D-06);
- ручной ввод (`MANUAL_*`) — свободное написание человека сводится к E.164,
  а местный номер без кода, добавочный, мусор и слишком длинный ввод
  отвергаются одним из четырёх русских текстов с примером (D-06, D-14, D-18);
- решение владельца О-1 закреплено строками явно: ручной `+888 0123 4567`
  отвергается, ручной `88801234567` без `+` становится российским
  `+78801234567`; Fragment попадает в базу только автопутём;
- строки `cr01_*` (план 16-07, ревью CR-01; решение владельца О-3 (а),
  2026-10-09, прогон `/gsd-plan-phase 16 --gaps`): ввод с префиксом `00` и
  местный номер чужой страны с ведущим нулём разбираются под `RU` в код 7 с
  национальной частью на 0 и ОТВЕРГАЮТСЯ, а не сохраняются несуществующим
  `+7 0…`; вариант «понимать `00` как `+`» владелец отверг. Строка
  `italian_leading_zero_is_not_plus_seven` — положительный контроль области
  отказа: у Италии `+39 06 …` ведущий ноль законен;
- строки `wr06_*` и правило-перебор над `EXTRA_DIGIT_BASES` (план 16-11, ревью
  WR-06, верификация 2026-10-09): настоящий номер зоны +7 с лишними цифрами,
  дописанными без маркера добавочного (`+7 999 123-45-67 1234`), разбирается в
  код 7 с национальной частью не из 10 цифр и ОТВЕРГАЕТСЯ при любом числе
  лишних цифр, а не сохраняется выдуманным `+799912345671234` под признаком
  «ручной» (D-07);
- маска (`MASKED`, D-10) — видны код страны и две последние цифры, не больше;
  у национальной части не длиннее двух цифр не видна ни одна её цифра (план
  16-07, ревью WR-03);
- разбор `ast` модуля — модуль чист (D-12) и не спрашивает «действительность»
  номера (D-05).
"""

import ast
import sys
from pathlib import Path

import phonenumbers
import pytest

from app.services.phone import (
    EXAMPLE_PHONE,
    MANUAL_INPUT_MAX_CHARS,
    PHONE_ERROR_BLANK,
    PHONE_ERROR_EXTENSION,
    PHONE_ERROR_MESSAGES,
    PHONE_ERROR_NOT_A_NUMBER,
    PHONE_ERROR_TOO_LONG,
    PhoneError,
    format_phone,
    mask_phone,
    normalize_manual,
    normalize_reported,
)

PHONE_MODULE = Path(__file__).resolve().parents[2] / "app" / "services" / "phone.py"

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


# Летопись (план 16-07, 2026-10-09): до плана здесь стояла строка
# `five_digits_lower_bound` ("12345" → "+12345") — она утверждала границу 5 как
# верную, а это был дефект (ревью WR-04, верификация 2026-10-08: обрывок
# источника хранился как номер); строка перенесена в `REPORTED_REFUSED` под
# именем `five_digits_fragment_was_the_lower_bound`, граница теперь 7 — самый
# короткий настоящий номер с кодом страны (Ниуэ +683, Токелау +690; замер
# метаданных 9.0.41 оркестратором 2026-10-09).
REPORTED_ACCEPTED = [
    pytest.param("79991234567", "+79991234567", id="digits_string"),
    pytest.param(79991234567, "+79991234567", id="digits_int"),
    pytest.param(" 79991234567 ", "+79991234567", id="digits_with_spaces_around"),
    pytest.param("+79991234567", "+79991234567", id="already_e164"),
    pytest.param("88801234567", "+88801234567", id="fragment_string"),
    pytest.param(888012345678, "+888012345678", id="fragment_int_12_digits"),
    pytest.param("77011234567", "+77011234567", id="kazakhstan"),
    pytest.param("998901234567", "+998901234567", id="uzbekistan"),
    pytest.param("6831234", "+6831234", id="seven_digits_lower_bound_niue"),
    pytest.param("6901234", "+6901234", id="seven_digits_tokelau"),
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
    pytest.param("12345", id="five_digits_fragment_was_the_lower_bound"),
    pytest.param("123456", id="six_digits_below_the_floor"),
    pytest.param("88812", id="fragment_cut_to_five_digits"),
    pytest.param("4412345", id="uk_fragment_local_only"),
    pytest.param("71234567", id="russian_number_without_area_code_local_only"),
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

    Строки плана 16-07 (ревью WR-04): пять и шесть цифр отвергает граница 7;
    `4412345` (`+44 12345`) и `71234567` — номер без кода зоны
    (`IS_POSSIBLE_LOCAL_ONLY`), который автопуть отвергает тем же правилом, что
    ручной путь (Ф-1).
    """
    assert normalize_reported(raw) is None, f"мусор {raw!r} не должен стать номером"


def test_a_short_fragment_from_a_source_is_not_stored_as_a_number():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 2 ПЛАНА 16-07: обрывок `12345` — не номер (WR-04).

    До плана граница автопути была 5 цифр, и обрывок источника хранился как
    `+12345` — «номер», которого не бывает. Самый короткий настоящий номер с
    кодом страны — 7 цифр (Ниуэ `+683 1234`).
    """
    assert normalize_reported("12345") is None, "обрывок из пяти цифр не должен стать номером"


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


# Граница D-14: тот же верный номер, дополненный пробелами до предела и за него.
# Строки собираются из одного номера, чтобы отказ на 33 символах нельзя было
# списать ни на что, кроме длины.
VALID_TYPED = "+7 999 123 45 67"
AT_INPUT_LIMIT = VALID_TYPED.center(MANUAL_INPUT_MAX_CHARS)
OVER_INPUT_LIMIT = VALID_TYPED.center(MANUAL_INPUT_MAX_CHARS + 1)


def test_the_length_boundary_rows_are_exactly_at_and_over_the_limit():
    """Граничные строки таблиц — ровно 32 и 33 символа, иначе граница не проверена."""
    assert len(AT_INPUT_LIMIT) == 32, "строка на пределе обязана быть ровно 32 символа"
    assert len(OVER_INPUT_LIMIT) == 33, "строка за пределом обязана быть ровно 33 символа"


def test_a_russian_number_typed_by_hand_lands_in_e164():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 3: самое частое русское написание → E.164.

    `8 999 …` — привычная форма междугороднего набора; ведущая `8` значит `+7`
    только при региональном разборе, поэтому ручной путь разбирает с `RU`.
    """
    assert normalize_manual("8 999 123-45-67") == "+79991234567", (
        "ручное «8 999 123-45-67» обязано стать +79991234567"
    )


MANUAL_ACCEPTED = [
    pytest.param("8 999 123-45-67", "+79991234567", id="eight_prefix"),
    pytest.param("+7 (999) 123-45-67", "+79991234567", id="plus_seven_brackets"),
    pytest.param("79991234567", "+79991234567", id="digits_with_country"),
    pytest.param("89991234567", "+79991234567", id="digits_eight_prefix"),
    pytest.param("9991234567", "+79991234567", id="ten_digits_no_prefix"),
    pytest.param("(999) 123-45-67", "+79991234567", id="brackets_no_prefix"),
    pytest.param("+7-999-123-45-67", "+79991234567", id="dashes"),
    pytest.param("   +7 999 123 45 67   ", "+79991234567", id="spaces_around"),
    pytest.param("８ ９９９ １２３ ４５ ６７", "+79991234567", id="fullwidth_digits"),
    pytest.param("tel:+79991234567", "+79991234567", id="tel_uri"),
    pytest.param("+77011234567", "+77011234567", id="kazakhstan_e164"),
    pytest.param("8 701 123 4567", "+77011234567", id="kazakhstan_eight_prefix"),
    pytest.param("77011234567", "+77011234567", id="kazakhstan_digits"),
    pytest.param("+998901234567", "+998901234567", id="uzbekistan"),
    pytest.param("8-800-555-35-35", "+78005553535", id="toll_free_800"),
    pytest.param("88801234567", "+78801234567", id="o1_fragment_without_plus_becomes_russian"),
    pytest.param(AT_INPUT_LIMIT, "+79991234567", id="exactly_32_chars"),
    pytest.param("+39 06 1234 5678", "+390612345678", id="italian_leading_zero_is_not_plus_seven"),
]


@pytest.mark.parametrize("text,expected", MANUAL_ACCEPTED)
def test_a_number_typed_by_hand_is_normalized_to_e164(text, expected):
    """Ручной ввод в свободной форме → одна строка E.164 (критерий 3, D-05).

    Строка `o1_fragment_without_plus_becomes_russian` — НЕ ошибка таблицы, а
    решение владельца О-1 (2026-10-08): буква D-05 разбирает ручной ввод с
    регионом `RU`, и `888…` без `+` читается как российский номер с ведущей `8`.
    Строка закрепляет это поведение, чтобы оно было решением, а не случайностью.

    Строка `italian_leading_zero_is_not_plus_seven` держит область отказа CR-01
    (план 16-07): признак разбора «ведущий ноль» законен у Италии, поэтому отказ
    ограничен кодом страны 7, и итальянский номер обязан пройти.
    """
    assert normalize_manual(text) == expected, f"ручной ввод {text!r}"


def test_a_number_typed_with_the_00_prefix_is_refused_not_saved_as_plus_seven_zero():
    """⚠️ ТРАСЕР ПЛАНА 16-07: `00 44 7911 123456` — отказ, а не `+700447911123456`.

    Под регионом `RU` международный префикс — `810`, а не `00`, и разбор читает
    ведущие `00` как начало российской национальной части. RU-метаданные
    допускают 14 цифр, поэтому строгая «возможность» такой ввод пропускала, и
    сохранялся несуществующий `+7 0…` под признаком «ручной», закрытый для
    автоисправления (D-07). Решение владельца О-3 (а), 2026-10-09: отказ текстом
    `PHONE_ERROR_NOT_A_NUMBER`; вариант «понимать `00` как `+`» отвергнут.
    """
    with pytest.raises(PhoneError) as excinfo:
        normalize_manual("00 44 7911 123456")
    assert str(excinfo.value) == PHONE_ERROR_NOT_A_NUMBER, (
        "ввод с префиксом 00 обязан получить отказ «Не похоже на номер телефона»"
    )


def test_a_russian_number_with_four_extra_digits_typed_by_hand_is_refused():
    """⚠️ ТРАСЕР ПЛАНА 16-11: `+7 999 123-45-67 1234` — отказ, а не `+799912345671234`.

    Человек дописал добавочный без маркера (`доб`, `ext`). Разбор под `RU`
    читает 14 национальных цифр, а RU-метаданные допускают и 14 — но только у
    бесплатного шаблона `8108…`, который аккаунтом мессенджера быть не может.
    До плана 16-11 (ревью WR-06, верификация 2026-10-09) такой ввод сохранялся
    выдуманным номером под признаком «ручной», закрытым для автоисправления
    (D-07). Отказ — прежним текстом `PHONE_ERROR_NOT_A_NUMBER` (D-18).
    """
    with pytest.raises(PhoneError) as excinfo:
        normalize_manual("+7 999 123-45-67 1234")
    assert str(excinfo.value) == PHONE_ERROR_NOT_A_NUMBER, (
        "номер +7 с четырьмя лишними цифрами обязан получить отказ «Не похоже на номер телефона»"
    )


MANUAL_REJECTED = [
    pytest.param("123-45-67", PHONE_ERROR_NOT_A_NUMBER, id="local_only_dashed"),
    pytest.param("1234567", PHONE_ERROR_NOT_A_NUMBER, id="local_only_digits"),
    pytest.param("+7 999 123-45-6", PHONE_ERROR_NOT_A_NUMBER, id="one_digit_short"),
    pytest.param("+7 999 123-45-678", PHONE_ERROR_NOT_A_NUMBER, id="one_digit_long"),
    pytest.param("+799912345678", PHONE_ERROR_NOT_A_NUMBER, id="twelve_digits"),
    pytest.param("+7999123456789012", PHONE_ERROR_NOT_A_NUMBER, id="sixteen_digits"),
    pytest.param("1234567890123456", PHONE_ERROR_NOT_A_NUMBER, id="sixteen_digits_no_plus"),
    pytest.param("12", PHONE_ERROR_NOT_A_NUMBER, id="two_digits"),
    pytest.param("+888 0123 4567", PHONE_ERROR_NOT_A_NUMBER, id="o1_fragment_by_hand_refused"),
    pytest.param("00 44 7911 123456", PHONE_ERROR_NOT_A_NUMBER, id="cr01_00_prefix_uk"),
    pytest.param("00 380 50 123 4567", PHONE_ERROR_NOT_A_NUMBER, id="cr01_00_prefix_ukraine"),
    pytest.param("00 90 532 123 4567", PHONE_ERROR_NOT_A_NUMBER, id="cr01_00_prefix_turkey"),
    pytest.param("00 1 202 555 01234", PHONE_ERROR_NOT_A_NUMBER, id="cr01_00_prefix_usa"),
    pytest.param("050 123 4567", PHONE_ERROR_NOT_A_NUMBER, id="cr01_ukrainian_local_leading_zero"),
    pytest.param(
        "8 029 123 45 67", PHONE_ERROR_NOT_A_NUMBER, id="cr01_belarus_long_distance_eight_zero"
    ),
    pytest.param("+7 012 345 67 89", PHONE_ERROR_NOT_A_NUMBER, id="cr01_plus_seven_then_zero"),
    pytest.param(
        "+7 999 123-45-67 1234", PHONE_ERROR_NOT_A_NUMBER, id="wr06_plus_seven_four_extra_digits"
    ),
    pytest.param(
        "8 999 123 45 67 8901", PHONE_ERROR_NOT_A_NUMBER, id="wr06_eight_prefix_four_extra_digits"
    ),
    pytest.param(
        "89991234567 8901", PHONE_ERROR_NOT_A_NUMBER, id="wr06_digits_then_unmarked_extension"
    ),
    pytest.param(
        "8 800 123 45 67 890", PHONE_ERROR_NOT_A_NUMBER, id="wr06_toll_free_three_extra_digits"
    ),
    pytest.param("+7 999 123 45 67 доб 5", PHONE_ERROR_EXTENSION, id="extension_russian"),
    pytest.param("+7 999 123 45 67 ext 12", PHONE_ERROR_EXTENSION, id="extension_ext"),
    pytest.param("abc", PHONE_ERROR_NOT_A_NUMBER, id="latin_letters"),
    pytest.param("привет", PHONE_ERROR_NOT_A_NUMBER, id="cyrillic_letters"),
    pytest.param("+", PHONE_ERROR_NOT_A_NUMBER, id="plus_only"),
    pytest.param("+1", PHONE_ERROR_NOT_A_NUMBER, id="country_code_only"),
    pytest.param("+0 999 123", PHONE_ERROR_NOT_A_NUMBER, id="invalid_country_code"),
    pytest.param("", PHONE_ERROR_BLANK, id="empty"),
    pytest.param("   ", PHONE_ERROR_BLANK, id="spaces_only"),
    pytest.param("x" * 33, PHONE_ERROR_TOO_LONG, id="garbage_33_chars"),
    pytest.param(OVER_INPUT_LIMIT, PHONE_ERROR_TOO_LONG, id="valid_number_padded_to_33_chars"),
]


@pytest.mark.parametrize("text,message", MANUAL_REJECTED)
def test_a_number_typed_by_hand_is_refused_with_an_explanation(text, message):
    """Мусор, местный номер, добавочный и длинный ввод — отказ, а не «номер».

    - `local_only_*`: библиотека считает `123-45-67` «возможным» местным
      номером (`IS_POSSIBLE_LOCAL_ONLY`) и дала бы `+71234567` — поэтому
      ручной путь требует строго `IS_POSSIBLE` (Ф-1 RESEARCH, D-06).
    - `extension_*`: E.164 молча отбросил бы добавочный, и сохранился бы не
      тот номер, что ввёл человек (Ф-3).
    - `o1_fragment_by_hand_refused`: решение владельца О-1 — ручной `+888…`
      отвергается, Fragment попадает в базу только автопутём.
    - `valid_number_padded_to_33_chars`: тот же верный номер, но на символ
      длиннее предела D-14 — отказ до разбора.

    Строки `cr01_*` (план 16-07, ревью CR-01, решение владельца О-3 (а),
    2026-10-09): префикс `00` и местный номер чужой страны с ведущим нулём
    (`050 …`, `8 029 …`) разбираются под `RU` в код 7 с национальной частью на
    0. Такого номера не бывает, а строгая «возможность» его пропускала, потому
    что RU-метаданные допускают 10 и 14 цифр. До плана 16-07 эти вводы
    сохранялись как `+700…` / `+70…`; теперь — отказ `PHONE_ERROR_NOT_A_NUMBER`.

    Строки `wr06_*` (план 16-11, ревью WR-06, верификация 2026-10-09): настоящий
    номер зоны +7 с лишними цифрами без маркера добавочного разбирается в код 7
    с национальной частью не из 10 цифр. До плана 16-11 четыре такие строки
    сохранялись выдуманными номерами (`+799912345671234`, `+788001234567890`);
    теперь — отказ `PHONE_ERROR_NOT_A_NUMBER`.
    """
    with pytest.raises(PhoneError) as excinfo:
        normalize_manual(text)
    assert str(excinfo.value) == message, f"текст отказа для {text!r}"


# Настоящие номера зоны +7, к которым правило-перебор дописывает лишние цифры
# (план 16-11, ревью WR-06): мобильный России в двух написаниях, бесплатный
# 8-800 и Казахстан.
EXTRA_DIGIT_BASES = [
    pytest.param("+7 999 123-45-67", id="plus_seven_mobile"),
    pytest.param("8 999 123-45-67", id="eight_prefix_mobile"),
    pytest.param("8 800 555-35-35", id="eight_prefix_toll_free"),
    pytest.param("+7 701 123 4567", id="kazakhstan"),
]
EXTRA_DIGITS = "12345"


@pytest.mark.parametrize(
    "extra_count",
    [pytest.param(k, id=f"extra_{k}") for k in range(1, len(EXTRA_DIGITS) + 1)],
)
@pytest.mark.parametrize("base", EXTRA_DIGIT_BASES)
def test_a_number_with_extra_digits_typed_by_hand_is_refused_whatever_their_count(
    base, extra_count
):
    """Номер +7 с 1…5 лишними цифрами — отказ при ЛЮБОМ их числе (WR-06, D-06).

    Зачем перебор, а не четыре строки: верификатор (2026-10-09) нашёл
    немонотонность — у `+7 999 123-45-67` одна, две и три лишние цифры давали
    отказ, а четыре давали «номер»; замер планирования нашёл ещё и три лишние
    у баз с ведущей `8` (`8 999 123-45-67 123` → `+789991234567123`,
    `8 800 555-35-35 123` → `+788005553535123`). Правило закрывает класс, а не
    отдельные вводы.

    Антивакуум: сначала сама база обязана приниматься и давать E.164 с ровно 10
    национальными цифрами — отказ должен идти от лишних цифр, а не от базы.
    """
    stored = normalize_manual(base)
    assert stored.startswith("+7") and len(stored) == len("+7") + 10, (
        f"антивакуум: база {base!r} обязана приниматься как номер +7 с 10 национальными цифрами"
    )

    typed = f"{base} {EXTRA_DIGITS[:extra_count]}"
    with pytest.raises(PhoneError) as excinfo:
        normalize_manual(typed)
    assert str(excinfo.value) == PHONE_ERROR_NOT_A_NUMBER, (
        f"номер +7 с {extra_count} лишними цифрами обязан получить отказ «Не похоже на номер телефона»"
    )


@pytest.mark.parametrize("text,message", MANUAL_REJECTED)
def test_every_refusal_text_is_a_declared_constant_with_the_example(text, message):
    """⚠️ ТЕКСТ ОТКАЗА — ИЗ ЗАКРЫТОГО НАБОРА И БЕЗ ПРИЧИНЫ (D-18, PHONE-21).

    Исключение может уйти в журнал. Если бы текст собирался из ввода или к
    исключению цеплялась причина библиотеки, номер человека оказался бы в
    журнале. Поэтому: текст — ровно одна из констант модуля, в нём пример
    правильного написания, а `__cause__` и `__context__` пусты.
    """
    with pytest.raises(PhoneError) as excinfo:
        normalize_manual(text)
    error = excinfo.value
    assert str(error) in PHONE_ERROR_MESSAGES, "текст отказа обязан быть константой модуля"
    assert f"Пример: {EXAMPLE_PHONE}" in str(error), "в тексте отказа обязан быть пример"
    assert error.__cause__ is None, "к отказу не цепляется причина"
    assert error.__context__ is None, "у отказа нет контекста чужого исключения"


def test_the_refusal_texts_are_exactly_four_distinct_russian_constants():
    """Набор закрыт: четыре разных текста, каждый с примером `+7 999 123-45-67`."""
    assert EXAMPLE_PHONE == "+7 999 123-45-67"
    assert PHONE_ERROR_MESSAGES == (
        PHONE_ERROR_BLANK,
        PHONE_ERROR_TOO_LONG,
        PHONE_ERROR_EXTENSION,
        PHONE_ERROR_NOT_A_NUMBER,
    )
    assert len(set(PHONE_ERROR_MESSAGES)) == 4, "тексты отказа не повторяются"


MASKED = [
    pytest.param("+79991234567", "+7 *** ***-**-67", id="russia"),
    pytest.param("+77011234567", "+7 *** *** **67", id="kazakhstan"),
    pytest.param("+88801234567", "+888 ******67", id="fragment"),
    pytest.param("+998901234567", "+998 ** *** ** 67", id="uzbekistan"),
    pytest.param("+12025550123", "+1 ***-***-**23", id="usa"),
    pytest.param("+88812", "+888 ***", id="short_national_part_two_digits"),
    pytest.param("+712", "+7 ***", id="short_national_part_russia"),
    pytest.param("+999123456", "+*******56", id="unparseable_with_digits"),
    pytest.param("garbage", "+***", id="unparseable_without_digits"),
]


@pytest.mark.parametrize("stored,expected", MASKED)
def test_a_stored_number_is_masked_for_a_human(stored, expected):
    """Маска D-10 повторяет форму показа: код страны и две последние цифры.

    Неразбираемое значение — `+`, звёзды по числу цифр минус две и две
    последние цифры; меньше четырёх цифр — сплошные `+***`. Разбираемый номер
    с национальной частью не длиннее двух цифр — код страны и `***` (строки
    `short_national_part_*`, план 16-07, ревью WR-03).
    """
    assert mask_phone(stored) == expected, f"маска {stored!r}"


def test_a_short_national_part_is_masked_entirely():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 3 ПЛАНА 16-07: `+88812` → `+888 ***` (WR-03, PHONE-21).

    До плана порог «сплошные звёзды» был только у неразбираемого значения, а
    разбираемый `+88812` давал `+888 12`: маска не прятала ни одной цифры.
    """
    assert mask_phone("+88812") == "+888 ***", "маска короткого номера раскрыла его целиком"


PARSEABLE_MASKED = [
    pytest.param(row.values[0], id=row.id)
    for row in MASKED
    if not row.id.startswith("unparseable")
]


@pytest.mark.parametrize("stored", PARSEABLE_MASKED)
def test_a_mask_shows_only_the_country_code_and_two_last_digits(stored):
    """В маске цифр — код страны плюс две, а у короткого номера — плюс ноль (D-10).

    Сравнение со строкой образца ловит разбивку, а этот счёт — утечку: маска,
    раскрывшая лишнюю цифру, выдала бы её при любой разбивке.

    Если в национальной части больше двух цифр, видны код страны и две
    последние; если не больше двух — ни одной цифры национальной части. Число
    цифр национальной части берётся из формы показа `format_phone(stored)` за
    вычетом цифр кода страны, а не из `national_number`: целое теряет ведущие
    нули Fragment. Летопись (план 16-07, ревью WR-03): прежняя форма правила
    проверяла только номера с 8 и более национальными цифрами и потому
    короткий случай `+88812` → `+888 12` не видела.
    """
    country_code = str(phonenumbers.parse(stored, None).country_code)
    shown_number_digits = sum(1 for ch in format_phone(stored) if ch.isdigit())
    national_digits = shown_number_digits - len(country_code)
    visible_national = 2 if national_digits > 2 else 0
    shown_digits = [ch for ch in mask_phone(stored) if ch.isdigit()]
    assert len(shown_digits) == len(country_code) + visible_national, (
        f"маска {stored!r} раскрывает лишнее"
    )


FORBIDDEN_CALLS = {"is_valid_number", "is_possible_number"}


def _imported_modules(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


def _called_names(tree: ast.Module) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
            elif isinstance(node.func, ast.Name):
                called.add(node.func.id)
    return called


def test_the_module_is_pure_and_never_asks_validity():
    """⚠️ МОДУЛЬ ЧИСТ И НЕ СПРАШИВАЕТ «ДЕЙСТВИТЕЛЬНОСТЬ» (D-05, D-12, Ф-1).

    - Ввозы — только `phonenumbers*` и стандартная библиотека: ни базы, ни
      слоёв приложения (D-12).
    - Валидатор «действительности» не зовётся вовсе: метаданные отстают, а
      Fragment он отвергает (D-05).
    - Голая проверка «возможности» не зовётся: она пропускает местный номер
      `IS_POSSIBLE_LOCAL_ONLY`; разрешена только форма `…_with_reason`.
    """
    tree = ast.parse(PHONE_MODULE.read_text(encoding="utf-8"))

    imported = _imported_modules(tree)
    assert imported, "антивакуум: в модуле обязан быть хотя бы ввоз phonenumbers"
    foreign = [
        name
        for name in imported
        if name.split(".")[0] != "phonenumbers"
        and name.split(".")[0] not in sys.stdlib_module_names
    ]
    assert foreign == [], f"модуль номера ввозит лишнее: {foreign}"

    called = _called_names(tree)
    assert "parse" in called, "антивакуум: разбор обязан найтись среди вызовов"
    assert called & FORBIDDEN_CALLS == set(), (
        f"запрещённые вызовы: {sorted(called & FORBIDDEN_CALLS)}"
    )


def test_the_ast_rule_catches_a_validity_call_and_a_database_import():
    """Контроль-отрицание: правило выше краснеет на подложенном исходнике."""
    planted = ast.parse(
        "import phonenumbers\n"
        "from sqlalchemy import select\n"
        "def f(n):\n"
        "    return phonenumbers.is_valid_number(n) or phonenumbers.is_possible_number(n)\n"
    )
    assert "sqlalchemy" in _imported_modules(planted)
    assert _called_names(planted) & FORBIDDEN_CALLS == FORBIDDEN_CALLS

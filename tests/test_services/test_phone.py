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
  строки `wr07_*`, правило-перебор «код страны × длина 7…15» и правило-сторож
  номеров-образцов метаданных (план 16-11, ревью WR-07, решение владельца
  О-5 (а), 2026-10-09): автопуть отвергает у кода 7 то же, что ручной путь
  (ведущий ноль, национальная часть не из 10 цифр), и вердикты `TOO_LONG` /
  `INVALID_LENGTH`, но не теряет ни Fragment, ни ни одного номера-образца
  метаданных; правило-сверка шапки (план 16-16, ревью IN-08, решение
  владельца О-8): абзац границы автопути в шапке модуля называет оба
  принимаемых класса с числами того же перебора, посчитанными вживую;
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
- строки `wr09_*`, контроли `*_mobile` и правило-перебор над
  `FOREIGN_EXTRA_DIGIT_BASES` (план 16-16, ревью WR-09, верификация раунда 3
  2026-10-10; решение владельца О-7 (а), 2026-10-12): настоящий мобильный номер
  чужой зоны (Беларусь, Украина, Киргизия, Турция, Китай; Израиль — при одной
  лишней цифре) с лишними цифрами без маркера добавочного ОТВЕРГАЕТСЯ — его
  длина не возможна ни для одного типа, каким бывает аккаунт мессенджера; сами
  номера без лишних цифр принимаются. Граница правила О-7 (а) — не две
  страны, а остаток, который пункт 5 докстринга `normalize_manual` называет с
  замером и который правило
  `test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement`
  пересчитывает вживую (ревью WR-11, решение владельца О-9 (а), 2026-10-13):
  вводы, чью длину с лишними цифрами допускает какой-либо тип аккаунта, в том
  числе сам `MOBILE` или только `VOIP`; часть остатка метаданные считают
  действительными номерами. Строкой таблицы остаток нормой не утверждён.
  Летопись: до 2026-10-13 (ревью WR-11) граница называлась Германией и
  Израилем (переменная длина `FIXED_LINE`). Правило-сторож номеров-
  образцов четырёх типов аккаунта доказывает, что отказ не режет ни одного из
  830 образцов метаданных, а правило негеографических кодов закрепляет отказ
  `+800` / `+808` / `+888` / `+979` ручным путём как решение (О-7 (а), О-1);
- маска (`MASKED`, D-10) — видны код страны и две последние цифры, не больше;
  у национальной части не длиннее двух цифр не видна ни одна её цифра (план
  16-07, ревью WR-03);
- разбор `ast` модуля — модуль чист (D-12) и не спрашивает «действительность»
  номера (D-05).
"""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple

import phonenumbers
import pytest

from app.services.phone import (
    ACCOUNT_NUMBER_TYPES,
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


# Летопись (план 16-11, решение владельца О-5 (а), 2026-10-09): строки `wr07_*`
# до плана хранились как номера (замер верификатора, раунд 2, ревью WR-07) —
# код 7 с ведущим нулём или с национальной частью не из 10 цифр и вердикты
# `TOO_LONG` / `INVALID_LENGTH`. `7999123` план 16-07 называл примером
# оставшейся границы (флаг П-1); теперь его отвергает правило кода 7.
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
    pytest.param("70123456789", id="wr07_plus_seven_then_zero"),
    pytest.param("799912345678", id="wr07_russian_mobile_plus_one_digit"),
    pytest.param("79991234567890", id="wr07_russian_mobile_plus_three_digits"),
    pytest.param("1234567890123", id="wr07_too_long_code_one"),
    pytest.param("441234567890123", id="wr07_too_long_code_forty_four"),
    pytest.param("700447911123456", id="wr07_cr01_number_from_a_source"),
    pytest.param("799912345671234", id="wr07_wr06_number_from_a_source"),
    pytest.param("7999123", id="wr07_russian_six_national_digits"),
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

    Строки `wr07_*` (план 16-11, ревью WR-07, решение владельца О-5 (а)): код 7
    с ведущим нулём или с национальной частью не из 10 цифр — общее с ручным
    путём правило; вердикты `TOO_LONG` и `INVALID_LENGTH` — Fragment их не даёт.
    """
    assert normalize_reported(raw) is None, f"мусор {raw!r} не должен стать номером"


def test_a_short_fragment_from_a_source_is_not_stored_as_a_number():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 2 ПЛАНА 16-07: обрывок `12345` — не номер (WR-04).

    До плана граница автопути была 5 цифр, и обрывок источника хранился как
    `+12345` — «номер», которого не бывает. Самый короткий настоящий номер с
    кодом страны — 7 цифр (Ниуэ `+683 1234`).
    """
    assert normalize_reported("12345") is None, "обрывок из пяти цифр не должен стать номером"


def test_the_auto_path_refuses_what_the_owner_named_before_execution():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 2 ПЛАНА 16-11: исход владельца О-5 (а), названный заранее.

    Решение владельца О-5 (а) «отказ», 2026-10-09, второй прогон
    `/gsd-plan-phase 16 --gaps`; исход `human_verification` 2 верификации
    назван ДО исполнения: `70123456789` (`+7 0…`), `799912345678` (у кода 7
    11 национальных цифр, `INVALID_LENGTH`) и `1234567890123` (`TOO_LONG`) —
    `None`, а Fragment `88801234567` по-прежнему `+88801234567`. Вариант (б)
    «принимать, как сейчас, и переписать шапку» владелец отверг.
    """
    got = [
        normalize_reported(raw)
        for raw in ("70123456789", "799912345678", "1234567890123", "88801234567")
    ]
    assert got == [None, None, None, "+88801234567"], (
        "автопуть обязан отвергнуть три значения владельца и принять Fragment"
    )


# Отвергнутые владельцем вердикты (О-5 (а)); `TOO_SHORT` сюда НЕ входит — его
# дают настоящие номера Fragment (О-1).
OWNER_REFUSED_VERDICTS = {
    phonenumbers.ValidationResult.IS_POSSIBLE_LOCAL_ONLY,
    phonenumbers.ValidationResult.TOO_LONG,
    phonenumbers.ValidationResult.INVALID_LENGTH,
}
VERDICT_NAMES = {
    value: name
    for name, value in vars(phonenumbers.ValidationResult).items()
    if name.isupper() and isinstance(value, int)
}
ENUMERATION_FILLER = "2345678901234567"


class AutoPathEnumeration(NamedTuple):
    """Итог перебора автопути «каждый код страны × общая длина 7…15»."""

    total: int
    refused_verdict_inputs: int
    accepted_by_verdict: dict[str, int]
    invalid_possible: int
    offences: list[tuple[str, str, str]]


def _auto_path_enumeration() -> AutoPathEnumeration:
    """Перебор «каждый код страны метаданных × общая длина 7…15» через автопуть.

    Входы — код страны, дополненный цифрами `ENUMERATION_FILLER` до общей длины
    7…15. Итог: число входов; число входов с отвергнутым владельцем вердиктом;
    число принятых `normalize_reported` по имени вердикта; число принятых
    `IS_POSSIBLE`-значений, которые валидатор «действительности» назвал бы
    недействительными; принятые значения, которые автопуть хранить не вправе.

    Валидатор зовёт ТЕСТ, а не модуль: запрет D-05 касается модуля номера, и
    правило чистоты читает только его исходник. Числа перебора стоят в шапке
    модуля (план 16-16, IN-08), и правило ниже сверяет их вживую.
    """
    inputs = [
        str(code) + ENUMERATION_FILLER[: total - len(str(code))]
        for code in phonenumbers.COUNTRY_CODE_TO_REGION_CODE
        for total in range(7, 16)
    ]
    accepted_by_verdict: dict[str, int] = {}
    refused_verdict_inputs = 0
    invalid_possible = 0
    offences: list[tuple[str, str, str]] = []
    for raw in inputs:
        number = phonenumbers.parse("+" + raw, None)
        verdict = phonenumbers.is_possible_number_with_reason(number)
        if verdict in OWNER_REFUSED_VERDICTS:
            refused_verdict_inputs += 1
        stored = normalize_reported(raw)
        if stored is None:
            continue
        name = VERDICT_NAMES[verdict]
        accepted_by_verdict[name] = accepted_by_verdict.get(name, 0) + 1
        if verdict == phonenumbers.ValidationResult.IS_POSSIBLE and not (
            phonenumbers.is_valid_number(number)
        ):
            invalid_possible += 1
        impossible_zone_seven = number.country_code == 7 and (
            bool(number.italian_leading_zero) or len(str(number.national_number)) != 10
        )
        if verdict in OWNER_REFUSED_VERDICTS or impossible_zone_seven:
            offences.append((raw, stored, name))
    return AutoPathEnumeration(
        total=len(inputs),
        refused_verdict_inputs=refused_verdict_inputs,
        accepted_by_verdict=accepted_by_verdict,
        invalid_possible=invalid_possible,
        offences=offences,
    )


def test_the_auto_path_never_stores_a_verdict_the_owner_refused():
    """Перебор «каждый код страны × длина 7…15»: отказ автопути держится на классе.

    Входы — каждый код страны метаданных, дополненный цифрами до общей длины
    7…15 (замер планирования 2026-10-09: 1935 входов, 215 кодов). Ни одно
    принятое значение не несёт вердикта `IS_POSSIBLE_LOCAL_ONLY`, `TOO_LONG`
    или `INVALID_LENGTH`, и ни одно значение кода 7 — национальной части не из
    10 цифр или с ведущим нулём (план 16-11, ревью WR-07, решение владельца
    О-5 (а)).

    Сообщение печатает число принятых по вердиктам: оставшаяся граница —
    `TOO_SHORT` у кода, отличного от 7, — называется, а не утверждается нормой.
    Перебор считает помощник `_auto_path_enumeration` (план 16-16): его же
    числа сверяются с шапкой модуля.
    """
    enumeration = _auto_path_enumeration()
    refused_verdict_inputs = enumeration.refused_verdict_inputs
    accepted_by_verdict = enumeration.accepted_by_verdict
    offences = enumeration.offences

    assert enumeration.total >= 1900, (
        f"антивакуум: входов перебора {enumeration.total}, ждали не меньше 1900"
    )
    assert refused_verdict_inputs >= 700, (
        f"антивакуум: входов с отвергнутым вердиктом {refused_verdict_inputs}, ждали не меньше 700"
    )
    assert sum(accepted_by_verdict.values()) > 0, "антивакуум: автопуть не принял ни одного входа"
    assert offences == [], (
        f"автопуть хранит отвергнутое владельцем: {len(offences)} значений, "
        f"первые {offences[:5]}; принятые по вердиктам: {accepted_by_verdict}"
    )


AUTO_PATH_BOUNDARY_HEADING = "⚠️ ГРАНИЦА ПРАВИЛА АВТОПУТИ"


def test_the_module_header_names_the_auto_path_boundary_with_its_measurement():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 3 ПЛАНА 16-16: шапка называет настоящее множество автопути.

    Ревью IN-08, верификация раунда 3 (2026-10-10), решение владельца О-8
    (2026-10-12). Абзац «⚠️ ГРАНИЦА ПРАВИЛА АВТОПУТИ» в шапке модуля обязан
    назвать оба класса значений, которые принимает автопуть, с замером рядом:
    `TOO_SHORT` у кода, отличного от 7 («583 из 1935» входов перебора), и
    значения, которые метаданные считают возможными, В ТОМ ЧИСЛЕ
    НЕДЕЙСТВИТЕЛЬНЫЕ («400 из 558» принятых `IS_POSSIBLE`-значений; валидатор
    «действительности» модуль не зовёт, D-05). До плана абзац начинался словами
    «Кроме настоящих номеров…» и выдавал каждое принятое `IS_POSSIBLE`-значение
    за настоящий номер.

    Числа считаются перебором вживую: подъём пина `phonenumberslite` (IN-02,
    отложено владельцем) изменит их — и правило покраснеет, а не оставит шапку
    устаревшей молча.
    """
    docstring = ast.get_docstring(ast.parse(PHONE_MODULE.read_text(encoding="utf-8")))
    assert docstring, "антивакуум: у модуля номера обязана быть шапка"
    paragraphs = [
        " ".join(line.strip() for line in block.splitlines())
        for block in docstring.split("\n\n")
    ]
    boundary = [p for p in paragraphs if p.startswith(AUTO_PATH_BOUNDARY_HEADING)]
    assert len(boundary) == 1, (
        f"в шапке обязан быть ровно один абзац «{AUTO_PATH_BOUNDARY_HEADING}»"
    )
    paragraph = boundary[0]

    enumeration = _auto_path_enumeration()
    too_short = enumeration.accepted_by_verdict.get("TOO_SHORT", 0)
    possible = enumeration.accepted_by_verdict.get("IS_POSSIBLE", 0)
    assert enumeration.total >= 1900, (
        f"антивакуум: входов перебора {enumeration.total}, ждали не меньше 1900"
    )
    assert possible > 0, "антивакуум: автопуть не принял ни одного IS_POSSIBLE-значения"

    assert f"{too_short} из {enumeration.total}" in paragraph, (
        f"шапка не называет замер «{too_short} из {enumeration.total}» значений TOO_SHORT"
    )
    assert f"{enumeration.invalid_possible} из {possible}" in paragraph, (
        f"шапка не называет замер «{enumeration.invalid_possible} из {possible}» "
        "недействительных среди принятых IS_POSSIBLE-значений"
    )
    assert "в том числе недействительн" in paragraph.lower(), (
        "шапка обязана сказать, что автопуть принимает возможные, в том числе недействительные"
    )


EXAMPLE_NUMBER_TYPES = (
    phonenumbers.PhoneNumberType.MOBILE,
    phonenumbers.PhoneNumberType.FIXED_LINE,
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE,
    phonenumbers.PhoneNumberType.TOLL_FREE,
    phonenumbers.PhoneNumberType.VOIP,
)


def test_every_example_number_of_the_metadata_is_still_accepted_from_a_source():
    """⚠️ СТОРОЖ ЗАПРЕТА 16-07 №3: отказ автопути не теряет настоящий номер.

    Каждый номер-образец метаданных (`phonenumberslite==9.0.41`: типы MOBILE,
    FIXED_LINE, FIXED_LINE_OR_MOBILE, TOLL_FREE, VOIP по всем регионам, плюс
    негеографические коды — замер планирования 1014 + 9) автопуть обязан
    вернуть тем же E.164. Правило проходит и до, и после отказа плана 16-11:
    оно доказывает, что отказ не режет ни одной формы номера, известной
    метаданным, — но не больше: образцы не перечень всех настоящих номеров.
    """
    examples: list[str] = []
    for region in sorted(phonenumbers.SUPPORTED_REGIONS):
        for kind in EXAMPLE_NUMBER_TYPES:
            example = phonenumbers.example_number_for_type(region, kind)
            if example is not None:
                examples.append(
                    phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.E164)
                )
    for code in sorted(phonenumbers.COUNTRY_CODES_FOR_NON_GEO_REGIONS):
        example = phonenumbers.example_number_for_non_geo_entity(code)
        if example is not None:
            examples.append(
                phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.E164)
            )

    assert len(examples) >= 1000, f"антивакуум: образцов {len(examples)}, ждали не меньше 1000"
    lost = [e164 for e164 in examples if normalize_reported(e164[1:]) != e164]
    assert lost == [], f"автопуть потерял номера-образцы метаданных: {len(lost)}, первые {lost[:10]}"


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
    # Контроли плана 16-16 (ревью WR-09, решение владельца О-7 (а)): настоящие
    # мобильные номера чужих зон без лишних цифр принимаются и до, и после отказа
    # по типам аккаунта — отказ строк `wr09_*` идёт от лишних цифр.
    pytest.param("+375 29 123 45 67", "+375291234567", id="belarus_mobile"),
    pytest.param("+380 50 123 4567", "+380501234567", id="ukraine_mobile"),
    pytest.param("+90 532 123 45 67", "+905321234567", id="turkey_mobile"),
    pytest.param("+996 700 123 456", "+996700123456", id="kyrgyzstan_mobile"),
    pytest.param("+972 50 123 4567", "+972501234567", id="israel_mobile"),
    pytest.param("+86 138 0013 8000", "+8613800138000", id="china_mobile"),
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


def test_a_foreign_number_with_an_extra_digit_typed_by_hand_is_refused():
    """⚠️ ТРАСЕР ПЛАНА 16-16: исход владельца О-7 (а), названный до исполнения.

    Решение владельца О-7 (а) «отказ по типам аккаунта», 2026-10-12, третий
    прогон `/gsd-plan-phase 16 --gaps`; исход `human_verification` 2
    верификации раунда 3 назван ДО исполнения: `+375 29 123 45 67 1` (Беларусь)
    и `+380 50 123 4567 1` (Украина) — отказ `PHONE_ERROR_NOT_A_NUMBER`, а
    `+375 29 123 45 67` → `+375291234567` и `8-800-555-35-35` → `+78005553535`.

    До плана 16-16 (ревью WR-09) класс «номер плюс лишние цифры» был закрыт
    только у кода 7: общая «возможность» берёт объединение длин всех типов
    номеров, и номер чужой зоны с цифрой, дописанной без маркера добавочного,
    сохранялся выдуманным «ручным» номером, закрытым для автоисправления (D-07).
    Вариант (б) «принимать как сейчас, граница — только код 7» владелец отверг.
    """
    for typed in ("+375 29 123 45 67 1", "+380 50 123 4567 1"):
        with pytest.raises(PhoneError) as excinfo:
            normalize_manual(typed)
        assert str(excinfo.value) == PHONE_ERROR_NOT_A_NUMBER, (
            f"номер чужой зоны с лишней цифрой {typed!r} обязан получить отказ "
            "«Не похоже на номер телефона»"
        )

    assert normalize_manual("+375 29 123 45 67") == "+375291234567", (
        "контроль: настоящий номер Беларуси без лишней цифры обязан приниматься"
    )
    assert normalize_manual("8-800-555-35-35") == "+78005553535", (
        "контроль: бесплатный 8-800 по-прежнему принимается"
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
    # Летопись (план 16-16, ревью WR-09, верификация раунда 3 2026-10-10): до плана
    # строки `wr09_*` сохранялись выдуманными «ручными» номерами (`+3752912345671`,
    # `+37529123456712`, `+3805012345671`, `+9967001234561`, `+90532123456712`,
    # `+905321234567123`, `+9725012345671`, `+86138001380001`), закрытыми для
    # автоисправления (D-07). Решение владельца О-7 (а), 2026-10-12 — отказ по
    # типам аккаунта.
    pytest.param(
        "+375 29 123 45 67 1", PHONE_ERROR_NOT_A_NUMBER, id="wr09_belarus_one_extra_digit"
    ),
    pytest.param(
        "+375 29 123 45 67 12", PHONE_ERROR_NOT_A_NUMBER, id="wr09_belarus_two_extra_digits"
    ),
    pytest.param(
        "+380 50 123 4567 1", PHONE_ERROR_NOT_A_NUMBER, id="wr09_ukraine_one_extra_digit"
    ),
    pytest.param(
        "+996 700 123 456 1", PHONE_ERROR_NOT_A_NUMBER, id="wr09_kyrgyzstan_one_extra_digit"
    ),
    pytest.param(
        "+90 532 123 45 67 12", PHONE_ERROR_NOT_A_NUMBER, id="wr09_turkey_two_extra_digits"
    ),
    pytest.param(
        "+90 532 123 45 67 123", PHONE_ERROR_NOT_A_NUMBER, id="wr09_turkey_three_extra_digits"
    ),
    pytest.param(
        "+972 50 123 4567 1", PHONE_ERROR_NOT_A_NUMBER, id="wr09_israel_one_extra_digit"
    ),
    pytest.param(
        "+86 138 0013 8000 1", PHONE_ERROR_NOT_A_NUMBER, id="wr09_china_one_extra_digit"
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

    Строки `wr09_*` (план 16-16, ревью WR-09, решение владельца О-7 (а),
    2026-10-12): то же у чужих зон — Беларусь, Украина, Киргизия, Турция,
    Израиль, Китай. Длина такого ввода возможна лишь для типа, каким аккаунт
    мессенджера не бывает (бесплатный, платный, UAN), и до плана 16-16 он
    сохранялся выдуманным «ручным» номером; теперь — отказ
    `PHONE_ERROR_NOT_A_NUMBER`.
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


# Настоящие мобильные номера чужих зон, к которым правило-перебор дописывает
# лишние цифры (план 16-16, ревью WR-09, решение владельца О-7 (а)). Израиля и
# Германии здесь нет намеренно: их номера с частью лишних цифр остаются
# принятыми. Они — часть остатка правила О-7 (а), который пункт 5 докстринга
# `normalize_manual` называет с замером, а правило
# `test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement`
# пересчитывает вживую: длина с лишними цифрами, допустимая для какого-либо
# типа аккаунта, в том числе для самого `MOBILE` или только `VOIP`; часть
# остатка метаданные считают действительными номерами. Строка таблицы
# утверждала бы остаток нормой. Летопись: до 2026-10-13 (ревью WR-11) граница
# называлась Германией и Израилем.
FOREIGN_EXTRA_DIGIT_BASES = [
    pytest.param("+375 29 123 45 67", id="belarus"),
    pytest.param("+380 50 123 4567", id="ukraine"),
    pytest.param("+996 700 123 456", id="kyrgyzstan"),
    pytest.param("+90 532 123 45 67", id="turkey"),
    pytest.param("+86 138 0013 8000", id="china"),
]


@pytest.mark.parametrize(
    "extra_count",
    [pytest.param(k, id=f"extra_{k}") for k in range(1, len(EXTRA_DIGITS) + 1)],
)
@pytest.mark.parametrize("base", FOREIGN_EXTRA_DIGIT_BASES)
def test_a_foreign_number_with_extra_digits_typed_by_hand_is_refused_whatever_their_count(
    base, extra_count
):
    """Мобильный номер чужой зоны с 1…5 лишними цифрами — отказ при ЛЮБОМ их числе.

    План 16-16, ревью WR-09, решение владельца О-7 (а), 2026-10-12. Зачем
    перебор, а не строки: исход до плана был немонотонен — у Турции одна лишняя
    цифра давала отказ (`INVALID_LENGTH`), а две и три давали «номер»
    (`+90532123456712`, `+905321234567123`); у Беларуси «номером» становились
    одна и две. Замер исполнения 2026-10-12: до плана 16-16 из 25 строк
    сохранялись 7. Правило закрывает класс, а не отдельные вводы.

    Израиля и Германии в таблице нет: часть их вводов с лишними цифрами
    остаётся принятой. Это остаток правила О-7 (а), а не норма; его называет с
    замером пункт 5 докстринга `normalize_manual`, а правило
    `test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement`
    пересчитывает вживую: длина с лишними цифрами, допустимая для какого-либо
    типа аккаунта, в том числе для самого `MOBILE` или только `VOIP`; часть
    остатка метаданные считают действительными номерами. Одна лишняя цифра
    Израиля закреплена строкой `wr09_israel_one_extra_digit`. Летопись: до
    2026-10-13 (ревью WR-11) граница называлась Германией и Израилем, с
    причиной «переменная длина `FIXED_LINE` / `FIXED_LINE_OR_MOBILE`».

    Антивакуум: база обязана приниматься и быть возможной как `MOBILE` — отказ
    должен идти от лишних цифр, а не от базы.
    """
    parsed = phonenumbers.parse(base, "RU")
    assert normalize_manual(base) == phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.E164
    ), f"антивакуум: база {base!r} обязана приниматься"
    assert (
        phonenumbers.is_possible_number_for_type_with_reason(
            parsed, phonenumbers.PhoneNumberType.MOBILE
        )
        == phonenumbers.ValidationResult.IS_POSSIBLE
    ), f"антивакуум: база {base!r} обязана быть возможной как мобильный номер"

    typed = f"{base} {EXTRA_DIGITS[:extra_count]}"
    with pytest.raises(PhoneError) as excinfo:
        normalize_manual(typed)
    assert str(excinfo.value) == PHONE_ERROR_NOT_A_NUMBER, (
        f"номер чужой зоны с {extra_count} лишними цифрами обязан получить отказ "
        "«Не похоже на номер телефона»"
    )


MANUAL_EXTRA_DIGIT_TAILS = ("1", "12", "123", "1234")


class ManualExtraDigitEnumeration(NamedTuple):
    """Итог перебора ручного пути «номер-образец `MOBILE` региона + лишние цифры»."""

    total: int
    accepted: int
    regions: frozenset[str]
    valid: int
    admitting: dict[str, list[frozenset[str]]]


def _manual_extra_digit_enumeration() -> ManualExtraDigitEnumeration:
    """Перебор «номер-образец `MOBILE` каждого региона в E.164 + хвост» через ручной путь.

    Перебор ревью WR-11 и верификации раунда 4 (2026-10-12): для каждого региона
    `phonenumbers.SUPPORTED_REGIONS` номер-образец `MOBILE` в записи E.164, к
    нему дописан хвост из `MANUAL_EXTRA_DIGIT_TAILS`, ввод подан
    `normalize_manual`. Регион без образца `MOBILE` пропускается. Итог: число
    вводов; число принятых; регионы принятых; число принятых, которые
    метаданные считают действительными номерами; для каждого региона — по
    каждому принятому вводу набор имён типов `ACCOUNT_NUMBER_TYPES`, у которых
    длина ввода `IS_POSSIBLE`.

    Валидатор «действительности» зовёт ТЕСТ, а не модуль: запрет D-05 касается
    модуля номера, и правило чистоты читает только его исходник (тот же довод,
    что у `_auto_path_enumeration`). Числа перебора стоят в пункте 5 докстринга
    `normalize_manual`, и правило-сверка ниже сверяет их вживую.
    """
    total = accepted = valid = 0
    regions: set[str] = set()
    admitting: dict[str, list[frozenset[str]]] = {}
    for region in sorted(phonenumbers.SUPPORTED_REGIONS):
        example = phonenumbers.example_number_for_type(region, phonenumbers.PhoneNumberType.MOBILE)
        if example is None:
            continue
        base = phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.E164)
        for tail in MANUAL_EXTRA_DIGIT_TAILS:
            total += 1
            typed = base + tail
            try:
                normalize_manual(typed)
            except PhoneError:
                continue
            accepted += 1
            regions.add(region)
            parsed = phonenumbers.parse(typed, None)
            admitting.setdefault(region, []).append(
                frozenset(
                    phonenumbers.PhoneNumberType.to_string(kind)
                    for kind in ACCOUNT_NUMBER_TYPES
                    if phonenumbers.is_possible_number_for_type_with_reason(parsed, kind)
                    == phonenumbers.ValidationResult.IS_POSSIBLE
                )
            )
            if phonenumbers.is_valid_number(parsed):
                valid += 1
    return ManualExtraDigitEnumeration(
        total=total,
        accepted=accepted,
        regions=frozenset(regions),
        valid=valid,
        admitting=admitting,
    )


# Регионы-примеры пункта 5 докстринга `normalize_manual` и класс причины, по
# которой правило по длинам не закрывает у них класс «номер плюс лишние цифры»:
# `MOBILE` — длину допускает сам `MOBILE`; `VOIP_ONLY` — только `VOIP`;
# `FIXED_LINE` — только `FIXED_LINE` / `FIXED_LINE_OR_MOBILE`. Регион, названный
# прозой пункта 5, обязан стоять здесь (запрет №3 плана 16-21).
MANUAL_BOUNDARY_EXAMPLES: dict[str, str] = {
    "NL": "MOBILE",
    "FI": "MOBILE",
    "ID": "MOBILE",
    "MY": "MOBILE",
    "AT": "MOBILE",
    "TW": "VOIP_ONLY",
    "ZW": "VOIP_ONLY",
    "DE": "FIXED_LINE",
    "IL": "FIXED_LINE",
    "IT": "FIXED_LINE",
}


def _manual_item_five() -> str:
    """Пункт 5 докстринга `normalize_manual`: строки от «5. » до «6. », склеенные пробелом."""
    tree = ast.parse(PHONE_MODULE.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "normalize_manual"
    )
    lines: list[str] = []
    inside = False
    for line in (ast.get_docstring(function) or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("5. "):
            inside = True
        elif stripped.startswith("6. "):
            break
        if inside:
            lines.append(stripped)
    return " ".join(lines)


def _boundary_cause_holds(cause: str, admitting: list[frozenset[str]]) -> bool:
    """Класс причины региона подтверждён замером по типам его принятых вводов."""
    if not admitting:
        return False
    if cause == "MOBILE":
        return any("MOBILE" in kinds for kinds in admitting)
    if cause == "VOIP_ONLY":
        return any(kinds == {"VOIP"} for kinds in admitting)
    if cause == "FIXED_LINE":
        return all(
            "MOBILE" not in kinds and bool(kinds & {"FIXED_LINE", "FIXED_LINE_OR_MOBILE"})
            for kinds in admitting
        )
    return False


def _item_five_boundary_problems(
    item: str, enumeration: ManualExtraDigitEnumeration
) -> list[str]:
    """Расхождения текста пункта 5 с замером перебора и таблицей `MANUAL_BOUNDARY_EXAMPLES`.

    Чистая функция над текстом: правило-сверка зовёт её на живом пункте 5, а
    правила-контроли — на тексте, мутированном в памяти (зубы правила
    доказываются контролями, а не правкой настоящего файла). Пустой список —
    проза верна.
    """
    problems: list[str] = []
    for claim in (
        f"{enumeration.accepted} из {enumeration.total}",
        f"{len(enumeration.regions)} регион",
        f"{enumeration.valid} из {enumeration.accepted}",
    ):
        if claim not in item:
            problems.append(f"нет «{claim}»")
    for region, cause in MANUAL_BOUNDARY_EXAMPLES.items():
        if not re.search(rf"(?<![A-Za-z]){region}(?![A-Za-z])", item):
            problems.append(f"регион {region} не назван")
        if region not in enumeration.regions:
            problems.append(f"регион {region} не принят перебором")
        elif not _boundary_cause_holds(cause, enumeration.admitting[region]):
            problems.append(
                f"причина {cause} у {region} не подтверждена замером: "
                f"{[sorted(kinds) for kinds in enumeration.admitting[region]]}"
            )
    return problems


def test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement():
    """⚠️ ЦЕЛЬ RED ЗАДАЧИ 1 ПЛАНА 16-21: пункт 5 называет настоящий остаток правила О-7 (а).

    Ревью WR-11, верификация раунда 4 (2026-10-12), решение владельца О-9 (а)
    (2026-10-13). До плана пункт 5 докстринга `normalize_manual` называл
    остатком класса «номер плюс лишние цифры» вне кода 7 только Германию и
    Израиль, с причиной «переменная длина `FIXED_LINE`», а перебор ручного пути
    принимал вводы в десятках регионов, и у части из них длину допускает сам
    `MOBILE` или только `VOIP`. Правило утверждает, что пункт 5 называет замер
    перебора `_manual_extra_digit_enumeration` — «{принято} из {всего}» вводов,
    «{число регионов} регион…», «{действительных} из {принято}», — и что каждый
    регион `MANUAL_BOUNDARY_EXAMPLES` назван пунктом и его причина подтверждена
    замером по типам.

    Зачем живой пересчёт: подъём пина `phonenumberslite` (IN-02, отложено
    владельцем) изменит числа — и правило покраснеет, а не оставит прозу
    устаревшей молча. Замер на 2026-10-13 (`phonenumberslite==9.0.41`):
    «56 из 976» вводов, 36 регионов, «15 из 56» действительных.
    """
    item = _manual_item_five()
    assert item.startswith("5. "), "антивакуум: в докстринге normalize_manual нет пункта 5"
    enumeration = _manual_extra_digit_enumeration()
    assert enumeration.total >= 900, (
        f"антивакуум: вводов перебора {enumeration.total}, ждали не меньше 900"
    )
    assert enumeration.accepted > 0, "антивакуум: ручной путь не принял ни одного ввода перебора"

    problems = _item_five_boundary_problems(item, enumeration)
    assert problems == [], (
        f"пункт 5 не называет замер остатка: {problems}; замер — принято "
        f"{enumeration.accepted} из {enumeration.total}, регионов {len(enumeration.regions)}, "
        f"действительных {enumeration.valid}"
    )


def test_the_item_five_rule_reddens_a_region_filed_under_another_cause():
    """Контроль правила-сверки: регион остатка в чужой скобке пункта 5 краснит правило.

    Ревью IN-13, верификация раунда 5 (2026-10-13), решение владельца О-13. Мутация
    верификатора в памяти: `TW` перенесён из скобки «только `VOIP`» в скобку «сам
    `MOBILE`». Проза стала бы ложной (у TW длину допускает только `VOIP`), а
    правило, проверявшее лишь называние региона и его причину по таблице,
    оставалось зелёным. Настоящий файл не правится — мутируется текст пункта.
    """
    item = _manual_item_five()
    mutated = item.replace("(NL, FI, ID, MY, AT)", "(NL, FI, ID, MY, AT, TW)").replace(
        "(TW, ZW)", "(ZW)"
    )
    assert mutated != item, "антивакуум: мутация не изменила текст пункта 5"
    problems = _item_five_boundary_problems(mutated, _manual_extra_digit_enumeration())
    assert any("TW" in problem for problem in problems), (
        f"мутация не покраснила правило пункта 5: TW в скобке `MOBILE`, проблемы {problems}"
    )


@pytest.mark.parametrize(
    ("before", "after"),
    [
        pytest.param("(TW, ZW)", "(TW, ZW, RS)", id="in_the_voip_bracket"),
        pytest.param(" Замер:", " Так же и RS. Замер:", id="in_the_remainder_sentence"),
    ],
)
def test_the_item_five_rule_reddens_a_region_named_without_a_table_row(before, after):
    """Контроль правила-сверки: регион прозы без строки `MANUAL_BOUNDARY_EXAMPLES` краснит правило.

    Ревью IN-13, верификация раунда 5 (2026-10-13), решение владельца О-13.
    Комментарий над таблицей обещает обратное вложение «регион, названный прозой
    пункта 5, стоит в таблице»; `RS`, дописанный в скобку «только `VOIP`» или в
    предложение остатка вне скобок, — регион без замера причины. Настоящий файл
    не правится — мутируется текст пункта.
    """
    item = _manual_item_five()
    assert item.count(before) == 1, f"антивакуум: якорь мутации {before!r} не единственный"
    mutated = item.replace(before, after)
    assert mutated != item, "антивакуум: мутация не изменила текст пункта 5"
    problems = _item_five_boundary_problems(mutated, _manual_extra_digit_enumeration())
    assert any("RS" in problem for problem in problems), (
        f"мутация не покраснила правило пункта 5: RS без строки таблицы, проблемы {problems}"
    )


def test_every_account_type_example_number_of_the_metadata_is_accepted_by_hand():
    """⚠️ СТОРОЖ ЗАПРЕТА 16-07 №3 ДЛЯ РУЧНОГО ПУТИ: отказ по типам не теряет номер.

    План 16-16, решение владельца О-7 (а), D-05. Каждый номер-образец метаданных
    (`phonenumberslite==9.0.41`) каждого типа из `ACCOUNT_NUMBER_TYPES` по всем
    регионам, поданный в международной записи, ручной путь обязан вернуть тем
    же E.164 (замер планирования и исполнения 2026-10-12 — 830 образцов).
    Правило проходит и до, и после отказа по типам: оно доказывает, что отказ
    не режет ни одной формы номера типа аккаунта, известной метаданным, — но не
    больше. Образцы — не перечень всех настоящих номеров; риск ложного отказа
    при отставании метаданных владелец принял в О-7 (а).
    """
    examples: list[tuple[str, str]] = []
    for region in sorted(phonenumbers.SUPPORTED_REGIONS):
        for kind in ACCOUNT_NUMBER_TYPES:
            example = phonenumbers.example_number_for_type(region, kind)
            if example is not None:
                examples.append(
                    (
                        phonenumbers.format_number(
                            example, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                        ),
                        phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.E164),
                    )
                )

    assert len(examples) >= 800, f"антивакуум: образцов {len(examples)}, ждали не меньше 800"
    lost: list[str] = []
    for typed, e164 in examples:
        try:
            stored = normalize_manual(typed)
        except PhoneError:
            stored = None
        if stored != e164:
            lost.append(typed)
    assert lost == [], (
        f"ручной путь потерял номера-образцы типов аккаунта: {len(lost)}, первые {lost[:10]}"
    )


# Решение владельца О-7 (а), согласовано с О-1: негеографические номера-образцы,
# которые ручной путь отвергает по типу (план 16-16), и которые принимает.
NON_GEO_REFUSED_BY_HAND = {800, 808, 888, 979}
NON_GEO_ACCEPTED_BY_HAND = {870, 878, 881, 882, 883}


def test_the_non_geographic_examples_split_by_account_type():
    """Попутное следствие отказа по типам — решение, а не случайность (О-7 (а)).

    Номера-образцы негеографических кодов ручным путём:
    - ОТВЕРГАЮТСЯ `+800` (бесплатный UIFN), `+808` (shared cost), `+888`
      (образец OCHA `+888 123 456 78901`, тип UAN) и `+979` (премиальный) —
      аккаунтом мессенджера такие номера не бывают;
    - ПРИНИМАЮТСЯ `+870`, `+881`, `+882` (спутниковые и сетевые мобильные) и
      `+878`, `+883` (VoIP).

    Связь с О-1: ручной `+888…` отвергается и раньше — номер Fragment для
    библиотеки слишком короткий (`TOO_SHORT`, строка
    `o1_fragment_by_hand_refused`); образец OCHA теперь отвергается по типу.
    Fragment попадает в базу только автопутём.
    """
    accepted: set[int] = set()
    refused: set[int] = set()
    for code in sorted(phonenumbers.COUNTRY_CODES_FOR_NON_GEO_REGIONS):
        example = phonenumbers.example_number_for_non_geo_entity(code)
        assert example is not None, f"антивакуум: у кода {code} нет номера-образца"
        typed = phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        try:
            normalize_manual(typed)
        except PhoneError as error:
            assert str(error) == PHONE_ERROR_NOT_A_NUMBER, f"текст отказа для {typed!r}"
            refused.add(code)
        else:
            accepted.add(code)

    assert refused == NON_GEO_REFUSED_BY_HAND, f"отвергнутые ручным путём коды: {sorted(refused)}"
    assert accepted == NON_GEO_ACCEPTED_BY_HAND, f"принятые ручным путём коды: {sorted(accepted)}"


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


# Голая проверка «возможности по типу» запрещена наравне с общей голой (план
# 16-16, D-05): в 9.0.41 она тоже считает возможным `IS_POSSIBLE_LOCAL_ONLY`.
FORBIDDEN_CALLS = {"is_valid_number", "is_possible_number", "is_possible_number_for_type"}


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
      `IS_POSSIBLE_LOCAL_ONLY`; разрешена только форма `…_with_reason`. То же
      у проверки «возможности по типу» (план 16-16): правило по типам аккаунта
      обязано стоять в форме `is_possible_number_for_type_with_reason`.
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
    assert "is_possible_number_for_type_with_reason" in called, (
        "антивакуум: правило по типам аккаунта обязано стоять в форме …_with_reason"
    )
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
        "def g(n, kind):\n"
        "    return phonenumbers.is_possible_number_for_type(n, kind)\n"
    )
    assert "sqlalchemy" in _imported_modules(planted)
    assert _called_names(planted) & FORBIDDEN_CALLS == FORBIDDEN_CALLS

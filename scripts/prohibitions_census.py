"""Перепись запретов планов вехи — ЧЕЛОВЕЧЕСКАЯ половина прибора.

Прибор один, половин две. Эта печатает перепись глазам человека и засевает скелет реестра;
принуждающая половина — `tests/test_planning/test_plan_prohibitions_census.py` — входит в
`just test` и импортирует РАЗБОРЩИК ОТСЮДА, а не держит второй. Обоснования, летописи чисел и
абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» живут в докстринге модуля теста: одно место одной
летописи.

ВСЕЛЕННАЯ — шапки файлов `.planning/phases/*/[0-9]*-PLAN.md`, текст между первой и второй
строкой-ограждением `---`, разобранный `yaml.safe_load`. ПЕРЕПИСЬ — элементы БЛОКА
`must_haves.prohibitions`; ключевание ПО БЛОКУ, а не по строке, поэтому порядок ключей элемента
на счёт не влияет (летопись D-01 — в модуле теста). ТОЖДЕСТВО — путь файла плана плюс
порядковый индекс элемента внутри блока; ключ по тексту формулировки не применяется нигде.

Все функции переписи — ЧИСТЫЕ функции от поданного отображения «путь → текст»: модульного
изменяемого состояния прибор не держит, поэтому ни порядок сбора pytest, ни параллельный
прогон его вердикт изменить не могут, а контроль может подать изменённую копию словаря.

Режимы:
  --check           число элементов и разбивка по фазам; код 1, если перепись разошлась с
                    реестром (число, `rows_declared`, биекция тождеств); печатает число ключей
                    разрешения в строках и ответ владельца по классам (`class_decisions`)
  --list [--phase N] [--class NAME]
                    перечень записей глазам человека: тождество, фаза, `verification`, класс и
                    диспозиция из реестра, первые ~100 символов формулировки; `--class` —
                    перечень одного класса предмета
  --breakdown       разбивка по фазам, по значениям `verification`, по диспозициям и по КЛАССАМ
                    реестра; для области решений (Фаза 10) — число запретов класса, число
                    среди них с `verification: test` и ветвь ответа владельца по классу
  --draft-classes   ЧЕРНОВАЯ разбивка области решений по классам ключевыми словами: по каждому
                    запрету печатаются ВСЕ классы-кандидаты, а не первый, рядом — класс,
                    записанный в реестр. ⚠️ Режим — для человека и для улики в сводке; гейт
                    его НЕ ЗОВЁТ: класс есть записанное поле, а не вывод в момент прогона
  --reconcile       таблица сличения: разбор по блоку, наивная сеть по строке над вехой и
                    четыре исторические сети над планами Фазы 10 — каждая со СЛАГАЕМЫМИ
                    своего расхождения с переписью, а не только с разностью; веха — тремя
                    множествами: без планов Фазы 15, ФИКСИРОВАННЫЙ НАБОР (`through_fixed_set`,
                    по план 15-14 включительно — предмет чисел с именем Фазы 15) и целиком
  --seed-registry   засев скелета реестра; идемпотентен по тождествам — уже записанные поля
                    строк не двигаются, новые строки получают засеянные значения; блок ответа
                    владельца по классам (`class_decisions`) переносится как есть, не пишется
  --record ТОЖДЕСТВО --disposition D --rule tests/…::имя [--rule …] [--coverage-note ТЕКСТ]
           [--permit-uncovered]
                    запись МЕРЫ ПОКРЫТИЯ одной строки области решений (план 15-22): диспозиция
                    `enforced` / `partially-enforced`, имена правил и их координаты через
                    `RULE_SEPARATOR`, непокрытая часть у частичной; `--permit-uncovered` — её
                    разрешение классом строки (`permit_scope_uncovered`), только у частичной
                    строки класса с ветвью `permit-class`. Каждое правило ищется
                    разбором `ast` в файле своей ссылки; всё, чего записывать нельзя, — отказ
                    `CensusError` по имени, и реестр тогда не пишется вовсе. ⚠️ Режим пишет
                    ТОЛЬКО меру покрытия: класса, разрешения владельца и вердикта он не пишет
                    (снимает лишь поля, которые запись меры делает ложными, — причину
                    «неразобрано» и область разрешения строки)

Зависимость: PyYAML приходит транзитивно (`uvicorn[standard]`), объявленной не является; риск
назван в модуле теста. Решение оставить её транзитивной записано в журнале решений
(`.planning/STATE.md`, раздел `### Decisions`, 2026-09-25, план 15-15, находка IN-06); этот
модуль — один из прямых импортёров, объявленных перечнем `YAML_DIRECT_IMPORTERS` модуля теста.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

import yaml

TREE_ROOT = Path(__file__).resolve().parents[1]
PLAN_GLOB = ".planning/phases/*/[0-9]*-PLAN.md"
REGISTRY_RELATIVE_PATH = (
    ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml"
)

FRONTMATTER_FENCE = "---"
MUST_HAVES = "must_haves"
PROHIBITIONS_BLOCK = "prohibitions"
TRUTHS_BLOCK = "truths"
ASSUMPTIONS_BLOCK = "assumptions"
STATEMENT_KEY = "statement"
VERIFICATION_KEY = "verification"
# Подпись отсутствующего ключа `verification` в выводе (`--list`, `--breakdown`). Пустая строка
# ею не подписывается: ключ без значения — отказ разбора, а не «ключа нет» (IN-01).
ABSENT_VERIFICATION_LABEL = "—"

# Наивная сеть по строке — ради РАЗЛОЖЕНИЯ расхождения, а не ради счёта: перепись её не
# использует. Сопоставляется построчно, чтобы `\s*` не перешагнул через перевод строки.
NAIVE_STATEMENT_LINE = re.compile(r"\s*- statement:")

DIGEST_LENGTH = 12

# Засеянные значения строки реестра. ⚠️ Это ПРЕДМЕТ решения, а не решение: класс пишет план
# 15-12, диспозицию — план 15-13 по ответу владельца. Полей `permit_*` засев не пишет вовсе.
SEED_CLASS = "unclassified"
SEED_DISPOSITION = "unresolved"
# Признак ключа разрешения. Такие ключи заводит ОТВЕТ ВЛАДЕЛЬЦА; `--check` их только считает.
PERMIT_PREFIX = "permit"

# Блок документа реестра с ОТВЕТОМ ВЛАДЕЛЬЦА по классам (план 15-12, задача 3). Засев его НЕ
# пишет и не правит — только переносит из существующего документа: иначе перезасев стёр бы
# решение владельца, а идемпотентность засева краснела бы на законной записи ответа.
CLASS_DECISIONS_KEY = "class_decisions"
# Поля, которыми решение называет свой класс: у разрешения — поле образца, у иного решения —
# своё, без признака разрешения в имени. Прибор их только ПЕЧАТАЕТ; форму судит модуль теста.
PERMIT_SCOPE_FIELD = "permit_scope"
DECISION_SCOPE_FIELD = "decision_scope"
DECISION_BRANCH_FIELD = "decision_branch"

# Порядок полей строки реестра — ради воспроизводимого вывода засева.
REGISTRY_FIELD_ORDER = (
    "plan",
    "index",
    "phase",
    "verification",
    "statement_digest",
    "class",
    "disposition",
    "declared_rule",
    # Мера покрытия по 61 запрету D-05 (план 15-13, задача 1): имя найденного правила, его
    # координата на день замера и непокрытая часть у «принуждается частично». Засев этих полей
    # не пишет — их пишет человеческое суждение, а засев только сохраняет их порядок.
    "rule_name",
    "rule_site",
    "coverage_note",
    # Решение по строке области решений (план 15-13, задача 2): названная причина у строки,
    # оставшейся «неразобрано», и область разрешения — имя класса — у строки «разрешено».
    "unresolved_reason",
    "permit_scope",
    # Разрешение НЕПОКРЫТОЙ части частичной строки разрешённого класса (план 15-22, задача 2):
    # имя класса строки. Пишет его только режим `--record --permit-uncovered`.
    "permit_scope_uncovered",
)

# Группа D-05: у запрета Фазы 10 с `verification: test` реестр несёт `declared_rule` — имя
# правила, которое НАЗВАЛ автор запрета, либо признак «имя не объявлено». Признак — отдельное
# значение, не пустая строка и не ноль, и именем Python-функции или модуля быть не может
# (угловые скобки): спутать его с объявленным именем нечем.
DECLARED_RULE_PHASE = "10"
DECLARED_RULE_VERIFICATION = "test"
RULE_UNDECLARED = "<undeclared>"
# Объявленное имя — формулировка запрета, ЦЕЛИКОМ заключённая в обратные кавычки и
# являющаяся голым идентификатором `test_…`. Путь (`tests/…/test_x.py`) и имя каталога внутри
# пути объявлением правила не считаются: они называют место, а не правило. Снимается ОДИН РАЗ
# засевом и коммитится; гейт предъявляет существование имени разбором `ast`, а не этим
# выражением.
DECLARED_RULE_TOKEN = re.compile(r"`(test_\w+)`")

# МЕРА ПОКРЫТИЯ И ЕЁ ЗАПИСЬ (план 15-22, задача 1). Строка реестра может назвать НЕСКОЛЬКО правил:
# `rule_name` и `rule_site` несут значения через `RULE_SEPARATOR` равной длины, и пары сличаются
# ПО ПОЗИЦИИ. Летопись: до плана 15-22 строка называла одно правило, и запрет, который держат два
# правила вместе, так не выражался. Одна строка YAML на запрет сохраняется. Модуль теста ввозит
# разделитель отсюда — второго носителя у него нет.
RULE_SEPARATOR = "; "
# Ссылка на правило в режиме записи: `tests/…/файл.py::имя` — путь от корня дерева и имя функции.
RULE_REFERENCE_SEPARATOR = "::"
SUITE_PREFIX = "tests/"
ENFORCED = "enforced"
PARTIALLY_ENFORCED = "partially-enforced"
COVERAGE_DISPOSITIONS = (ENFORCED, PARTIALLY_ENFORCED)
RULE_NAME_FIELD = "rule_name"
RULE_SITE_FIELD = "rule_site"
COVERAGE_NOTE_FIELD = "coverage_note"
UNRESOLVED_REASON_FIELD = "unresolved_reason"
# Разрешение непокрытой части (план 15-22, задача 2) стоит только у частичной строки класса, чей
# ответ владельца — ветвь `permit-class`; значение — имя класса строки (D-04).
PERMIT_SCOPE_UNCOVERED_FIELD = "permit_scope_uncovered"
PERMIT_CLASS_BRANCH = "permit-class"

REGISTRY_HEADER = """\
# Реестр тождеств запретов планов вехи v2.1 — строка на каждый элемент переписи.
#
# Источник строк — `scripts/prohibitions_census.py --seed-registry`; принуждение биекции
# «перепись ↔ реестр» — `tests/test_planning/test_plan_prohibitions_census.py`.
# Тождество строки — `plan` + `index` (порядковый номер элемента в блоке
# `must_haves.prohibitions`). `statement_digest` служит ОБНАРУЖЕНИЮ ПРАВКИ формулировки,
# а не ключеванию. `verification` отсутствует там, где элемент ключа не несёт: отсутствие
# есть признак «не объявлено», а не значение `none`.
#
# ⚠️ ПОЛЯ ВЕРДИКТА ЗДЕСЬ НЕТ НАМЕРЕННО, и поле разрешения в СТРОКЕ стоит ТОЛЬКО по ответу
# владельца: `permit_scope` (имя класса) несёт строка, чей класс получил в блоке
# `class_decisions` ветвь `permit-class`, — по своему усмотрению исполнитель его не пишет.
# `class: unclassified` и `disposition: unresolved` — засеянный ПРЕДМЕТ решения, а не решение:
# класс пишет план 15-12, диспозицию по ответу владельца — план 15-13. Исполнитель, поставивший
# поле вердикта сам, вынес бы вердикт вместо владельца. (Летопись первой фразы: до плана 15-13 она
# кончалась словами «и полей разрешения в СТРОКАХ исполнитель не пишет» — верными, пока строки
# диспозиций не несли; план 15-13 поставил `permit_scope` строкам разрешённых классов по
# записанному ответу. Летопись абзаца: до ответа владельца
# 2026-09-24 он начинался словами «ПОЛЕЙ `permit_*` И ЛЮБОГО ПОЛЯ ВЕРДИКТА ЗДЕСЬ НЕТ НАМЕРЕННО» —
# верными на день засева; поля разрешения с тех пор есть, но их завёл ОТВЕТ ВЛАДЕЛЬЦА, и стоят
# они только в блоке `class_decisions` ниже.)
#
# ⚠️ БЛОК `class_decisions` ЗАВОДИТ ОТВЕТ ВЛАДЕЛЬЦА, И ИДЁТ ОН СВЕРХ ШАПКИ ЗАМЕРА И ПОСЛЕ НЕЁ.
# Форма полей разрешения — образца `10-PROHIBITIONS-SUBJECT.md:1-36`; область разрешения —
# ИМЯ КЛАССА (D-04), и оно не распространяется ни на фазу целиком, ни на веху. Ответ `chubav`
# на чекпойнте плана 15-12 (задача 3), 2026-09-24T16:45Z, по классу: `product-invariant` (70) —
# требовать принуждения; остальные десять классов (251) — разрешить класс; построчного разбора
# не выбрано ни по одному. Основания СВОИМИ СЛОВАМИ владелец не дал — только выбор варианта;
# слова варианта принадлежат оркестратору, а не владельцу, и записаны дословно в
# `15-12-SUMMARY.md`. ⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ: запреты разрешённого класса остаются
# непринуждёнными машинно. Засев блок не пишет и не правит — только переносит; диспозиции строк
# по этому ответу ставит план 15-13.
#
# `declared_rule` стоит только у запретов Фазы 10 с `verification: test` (группа D-05): имя
# правила, названное формулировкой запрета, либо `<undeclared>` — признак «имя не объявлено».
# Это ОБЪЯВЛЕНИЕ автора запрета, снятое засевом, а не вердикт о соблюдении.
#
# ДИСПОЗИЦИИ ОБЛАСТИ РЕШЕНИЙ (план 15-13). По 61 запрету с `verification: test` — МЕРА ПОКРЫТИЯ,
# снятая чтением предмета запрета и предмета правила: `enforced` / `partially-enforced` с
# `rule_name` и `rule_site` (координата — на день замера) и, у частичной, `coverage_note` —
# непокрытой частью; `unresolved` с причиной `declared-rule-absent`, если правила с таким
# предметом в дереве нет (находка D-05, не разрешение). Остальным — по ответу владельца:
# `permitted` с `permit_scope` у разрешённых классов, `unresolved` с причиной
# `enforcement-required` у класса `require-enforcement`. ⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ.
# Строки вне Фазы 10 не несут ни одного поля решения (D-02).
#
# `rows_declared` — длина реестра, равная переписи ВСЕЙ вселенной; строк, чьё тождество лежит в
# ФИКСИРОВАННОМ НАБОРЕ (планы по 15-14 включительно), ровно столько, сколько объявляет литерал
# модуля теста, а строки планов после набора засеяны и стоят вне области решений (D-02).
# Перегенерация реестра в другой размер краснит модуль. (Летопись: до плана 15-15 абзац гласил
# «`rows_declared` — второй носитель числа переписи (первый — литерал модуля теста)» — верно,
# пока набор и вселенная совпадали, то есть до 2026-09-25, когда легли планы закрытия гэпов.)
#
# `class` у строк Фазы 10 (область решений D-02) записан планом 15-12 ОДИН раз — чтением
# формулировки, а не порядком правил регулярных выражений; перечень классов объявлен в модуле
# теста (`PROHIBITION_CLASSES`). Строки вне области решений сохраняют `unclassified`. Черновая
# разбивка ключевыми словами (`--draft-classes`) есть улика для человека: гейт её не зовёт.
# Верность отнесения — человеческое суждение; гейт утверждает ПОЛНОТУ, а не правильность.
"""


def _safe_yaml(text: str):
    """Безопасный разбор YAML. Загрузчик ОДИН по смыслу — безопасный; реализация — libyaml.

    `yaml.CSafeLoader` есть тот же безопасный загрузчик, написанный на C: замер 2026-09-24 на
    всех 156 шапках планов и на реестре дал ПОСИМВОЛЬНО РАВНЫЕ результаты с `yaml.safe_load`
    при десятикратной разнице во времени (0.14 s против 1.39 s за проход). Правила переписи
    проходят вселенную несколько раз, и чистый загрузчик вывел бы каталог
    `tests/test_planning/` из бюджета быстрого прогона (T-15-06). Где libyaml нет, разбор идёт
    `yaml.safe_load` — сеть от этого не меняется.
    """
    loader = getattr(yaml, "CSafeLoader", None)
    if loader is None:
        return yaml.safe_load(text)
    return yaml.load(text, Loader=loader)  # noqa: S506 — загрузчик безопасный


class CensusError(ValueError):
    """Отказ разбора: шапка не YAML, блок не список, элемент не словарь с формулировкой."""


@dataclass(frozen=True, order=True)
class ProhibitionIdentity:
    """Тождество запрета: путь файла плана плюс порядковый индекс элемента в блоке."""

    plan_path: str
    index: int

    def __str__(self) -> str:
        return f"{self.plan_path}#{self.index}"


@dataclass(frozen=True)
class ProhibitionRecord:
    """Элемент блока `must_haves.prohibitions`.

    `verification` — значение ключа либо `None` — ПРИЗНАК «ключа нет», а не значение `none`:
    смешение двух вещей изъяло бы элемент из правила молча. Третьего состояния в записи НЕТ:
    ключ, присутствующий без значения (`verification:` или `verification: ""`), — отказ разбора
    `CensusError` с тождеством элемента, а не «ключа нет» (находка ревью IN-01, план 15-20).
    `first_key` — ключ, на котором стоит дефис списка; на счёт он не влияет и хранится ради
    разложения наивной сети.
    """

    identity: ProhibitionIdentity
    phase: str
    statement: str
    verification: str | None
    status: str | None
    first_key: str

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.statement.encode("utf-8")).hexdigest()[:DIGEST_LENGTH]


@dataclass(frozen=True)
class NetDecomposition:
    """Слагаемые расхождения переписи с наивной сетью по строке `- statement:`.

    Каждое слагаемое — отдельная величина прибора. `reconstructed` собирает сеть из разбора,
    `line_net` снимает её счётом строк: две величины, полученные РАЗНЫМИ путями из одного
    источника, и их расхождение есть ошибка разбора, а не пропажа запрета.
    """

    prohibitions: int
    first_key_elsewhere: int
    truths: int
    assumptions: int
    line_net: int

    @property
    def reconstructed(self) -> int:
        return self.prohibitions - self.first_key_elsewhere + self.truths + self.assumptions


def phase_of(plan_path: str) -> str:
    """Номер фазы — префикс имени каталога фазы до первого дефиса (`10-rychag…` → `10`)."""
    return Path(plan_path).parent.name.split("-", 1)[0]


# ФИКСИРОВАННЫЙ НАБОР — предмет чисел, названных именем Фазы 15 (WR-04, план 15-15). Вселенная
# обхода растёт с каждым новым планом; числа, чьё имя утверждает состояние дня, растут вместе с
# ней только ложью. Поэтому объявленные числа меряются над набором, заданным НОМЕРАМИ, а не
# датой и не порядком обхода: все планы фаз до `FIXED_SET_PHASE` и планы самой этой фазы с
# номером не больше `FIXED_SET_LAST_PLAN`.
FIXED_SET_PHASE = "15"
FIXED_SET_LAST_PLAN = 14
PLAN_FILE_NAME = re.compile(r"(\d+)-(\d+)-PLAN\.md")


def plan_number_of(plan_path: str) -> int:
    """Номер плана — вторая часть имени файла `NN-MM-PLAN.md` (`15-14-PLAN.md` → 14).

    Имя другой формы — `CensusError`, а не пропуск: план, которого набор не умеет отнести,
    молча выпал бы из чисел либо из растущей половины.
    """
    match = PLAN_FILE_NAME.fullmatch(Path(plan_path).name)
    if match is None:
        raise CensusError(f"`{plan_path}`: имя файла плана не имеет формы `NN-MM-PLAN.md`")
    return int(match.group(2))


def _phase_number_of(plan_path: str) -> int:
    phase = phase_of(plan_path)
    if not phase.isdigit():
        raise CensusError(f"`{plan_path}`: номер фазы `{phase}` — не число")
    return int(phase)


def through_fixed_set(sources: Mapping[str, str]) -> dict[str, str]:
    """Подмножество вселенной — ФИКСИРОВАННЫЙ НАБОР планов, предмет чисел с именем Фазы 15.

    Набор — файлы планов, существовавшие 2026-09-24, — 156 штук; предмет чисел, названных
    именем Фазы 15. План входит в набор, если его фаза меньше `FIXED_SET_PHASE` либо равна ей
    при номере плана не больше `FIXED_SET_LAST_PLAN`. Отбор — по номерам фазы (каталог) и плана
    (имя файла), поэтому порядок подачи словаря на результат не влияет. Чистая функция: второй
    копии отбора нет ни здесь, ни в модуле теста.
    """
    boundary = (int(FIXED_SET_PHASE), FIXED_SET_LAST_PLAN)
    return {
        path: sources[path]
        for path in sorted(sources)
        if (_phase_number_of(path), plan_number_of(path)) <= boundary
    }


def _plan_sources(root: Path) -> dict[str, str]:
    """Отображение «путь плана относительно корня → текст файла», по `sorted(glob)`."""
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.glob(PLAN_GLOB))
    }


def _frontmatter(text: str) -> dict:
    """Шапка плана: YAML между первой и второй строкой-ограждением `---`.

    Файл без шапки даёт пустой словарь — у него нет блока, и это не отказ разбора.
    Шапка, не являющаяся YAML-отображением, — отказ, и он поднимается `CensusError`.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return {}
    block: list[str] = []
    for line in lines[1:]:
        if line.strip() == FRONTMATTER_FENCE:
            break
        block.append(line)
    try:
        parsed = _safe_yaml("\n".join(block))
    except yaml.YAMLError as error:
        raise CensusError(f"шапка не разбирается YAML: {error}") from error
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise CensusError(f"шапка — не отображение, а {type(parsed).__name__}")
    return parsed


def _block_elements(frontmatter: Mapping, block: str) -> list:
    """Элементы блока `must_haves.<block>`; отсутствие блока — пустой список."""
    must_haves = frontmatter.get(MUST_HAVES) or {}
    if not isinstance(must_haves, dict):
        raise CensusError(f"`{MUST_HAVES}` — не отображение")
    elements = must_haves.get(block) or []
    if not isinstance(elements, list):
        raise CensusError(f"`{MUST_HAVES}.{block}` — не список")
    return elements


def _verification_of(identity: ProhibitionIdentity, element: Mapping) -> str | None:
    """Значение ключа `verification` элемента: строка, либо `None` — ПРИЗНАК «ключа нет».

    Три случая, и третий — не значение: ключа нет → `None`; ключ есть, а значения нет (`None`
    YAML или пустая строка) → `CensusError` с тождеством; иначе строка значения. Слить второй
    случай с первым значило бы изъять элемент из правила двух значений молча (IN-01).
    """
    if VERIFICATION_KEY not in element:
        return None
    value = element[VERIFICATION_KEY]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise CensusError(
            f"`{identity}`: ключ `{VERIFICATION_KEY}` присутствует без значения — объявите "
            f"значение или уберите ключ"
        )
    return str(value)


def verification_label(record: ProhibitionRecord) -> str:
    """Подпись значения `verification` в выводе прибора: «—» — ТОЛЬКО у записи без ключа."""
    return ABSENT_VERIFICATION_LABEL if record.verification is None else record.verification


def _records_of(plan_path: str, text: str) -> list[ProhibitionRecord]:
    records: list[ProhibitionRecord] = []
    for index, element in enumerate(_block_elements(_frontmatter(text), PROHIBITIONS_BLOCK)):
        if not isinstance(element, dict) or STATEMENT_KEY not in element:
            raise CensusError(
                f"элемент #{index} блока `{MUST_HAVES}.{PROHIBITIONS_BLOCK}` — не словарь с "
                f"ключом `{STATEMENT_KEY}`: форма записи, которую прибор не знает, называется, "
                f"а не пропускается"
            )
        identity = ProhibitionIdentity(plan_path, index)
        verification = _verification_of(identity, element)
        status = element.get("status")
        records.append(
            ProhibitionRecord(
                identity=identity,
                phase=phase_of(plan_path),
                statement=str(element[STATEMENT_KEY]),
                verification=verification,
                status=None if status is None else str(status),
                first_key=str(next(iter(element))),
            )
        )
    return records


def _sweep(sources: Mapping[str, str]) -> tuple[list[ProhibitionRecord], list[str]]:
    """ОДИН проход вселенной: записи переписи и ВСЕ отказы разбора («путь: причина»)."""
    records: list[ProhibitionRecord] = []
    failures: list[str] = []
    for plan_path in sorted(sources):
        try:
            records.extend(_records_of(plan_path, sources[plan_path]))
        except CensusError as error:
            failures.append(f"{plan_path}: {error}")
    return records, failures


def parse_failures(sources: Mapping[str, str]) -> list[str]:
    """ВСЕ отказы разбора одним списком, «путь: причина», а не первый."""
    return _sweep(sources)[1]


def census(sources: Mapping[str, str]) -> list[ProhibitionRecord]:
    """Перепись: элементы блока `must_haves.prohibitions` по всем поданным планам.

    Порядок записей — по пути плана, затем по индексу в блоке; порядок подачи словаря на
    результат не влияет. Отказ разбора хоть одного плана — `CensusError`, называющая ВСЕ
    отказы: пропуск плана молча выбросил бы его запреты из переписи.
    """
    records, failures = _sweep(sources)
    if failures:
        raise CensusError("отказы разбора шапок планов:\n" + "\n".join(failures))
    return records


def _statement_first(elements: Iterable) -> int:
    """Элементы-словари, у которых дефис списка стоит на ключе формулировки."""
    return sum(
        1
        for element in elements
        if isinstance(element, dict) and element and next(iter(element)) == STATEMENT_KEY
    )


def _naive_line_net(sources: Mapping[str, str]) -> int:
    """Наивная сеть: строки, начинающиеся (после пробелов) с `- statement:`, по файлу целиком."""
    return sum(
        1
        for text in sources.values()
        for line in text.splitlines()
        if NAIVE_STATEMENT_LINE.match(line)
    )


def decomposition(sources: Mapping[str, str]) -> NetDecomposition:
    """Разложение наивной сети на слагаемые, каждое — отдельная величина прибора."""
    records = census(sources)
    truths = assumptions = 0
    for plan_path in sorted(sources):
        frontmatter = _frontmatter(sources[plan_path])
        truths += _statement_first(_block_elements(frontmatter, TRUTHS_BLOCK))
        assumptions += _statement_first(_block_elements(frontmatter, ASSUMPTIONS_BLOCK))
    return NetDecomposition(
        prohibitions=len(records),
        first_key_elsewhere=sum(1 for record in records if record.first_key != STATEMENT_KEY),
        truths=truths,
        assumptions=assumptions,
        line_net=_naive_line_net(sources),
    )


def phase_breakdown(records: Iterable[ProhibitionRecord]) -> dict[str, int]:
    """Число записей по фазам, фазы по возрастанию."""
    counts = Counter(record.phase for record in records)
    return {phase: counts[phase] for phase in sorted(counts)}


# --- реестр ------------------------------------------------------------------------


def load_registry(path: Path) -> dict:
    """Документ реестра как есть; отсутствие файла или пустой документ — пустой реестр.

    Документ, не являющийся отображением, — `CensusError` с его типом, а не `AttributeError`
    мимо пути отказа `main()` (находка ревью IN-02, план 15-20). Строки судит `_registry_rows`,
    решения по классам — `_class_decisions`: порча называется, а не чинится подстановкой.
    """
    if not path.exists():
        return {"rows_declared": 0, "rows": []}
    try:
        document = _safe_yaml(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise CensusError(f"реестр `{path.name}` не разбирается YAML: {error}") from error
    if document is None:
        document = {}
    if not isinstance(document, dict):
        raise CensusError(
            f"реестр `{path.name}` — не отображение, а {type(document).__name__}"
        )
    document.setdefault("rows", [])
    return document


def _registry_row_problem(row: object) -> str:
    """Порча одной строки реестра словами, либо пустая строка. Чистая функция строки."""
    if not isinstance(row, dict):
        return f"строка — не отображение, а {type(row).__name__}"
    if "plan" not in row:
        return "нет ключа `plan`"
    if not isinstance(row["plan"], str):
        return f"`plan` — не строка, а {type(row['plan']).__name__}"
    if "index" not in row:
        return "нет ключа `index`"
    # Булево в Python — подкласс целого: `index: true` иначе прошёл бы как 1.
    if isinstance(row["index"], bool) or not isinstance(row["index"], int):
        return f"`index` — не целое, а {type(row['index']).__name__}"
    return ""


def _registry_rows(document: Mapping) -> dict[ProhibitionIdentity, dict]:
    """Строки реестра по тождеству. Повтор тождества — отказ: биекция не терпит дублей.

    Каждая строка — отображение с `plan` (строка) и `index` (целое, не булево); иначе
    `CensusError` с позицией строки и найденным. Проверка формы — чистая функция поданного
    документа: порча отказывает, в каком бы месте списка она ни стояла.
    """
    listed = document.get("rows") or []
    if not isinstance(listed, list):
        raise CensusError(f"блок `rows` реестра — не список, а {type(listed).__name__}")
    rows: dict[ProhibitionIdentity, dict] = {}
    for position, row in enumerate(listed):
        problem = _registry_row_problem(row)
        if problem:
            raise CensusError(f"строка реестра на позиции {position}: {problem}; найдено {row!r}")
        identity = ProhibitionIdentity(row["plan"], row["index"])
        if identity in rows:
            raise CensusError(f"тождество `{identity}` встречается в реестре дважды")
        rows[identity] = row
    return rows


def _class_decisions(document: Mapping) -> list[dict]:
    """Блок `CLASS_DECISIONS_KEY` — список отображений, либо `CensusError` с позицией.

    Единственный вход в блок для `_check` и `_branch_by_class`: решение-строка иначе прошло бы
    подстрочным тестом `in` и упало бы `TypeError` на индексации (IN-02). Отсутствие блока —
    пустой список, как прежде.
    """
    decisions = document.get(CLASS_DECISIONS_KEY) or []
    if not isinstance(decisions, list):
        raise CensusError(
            f"блок `{CLASS_DECISIONS_KEY}` реестра — не список, а {type(decisions).__name__}"
        )
    for position, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            raise CensusError(
                f"решение блока `{CLASS_DECISIONS_KEY}` на позиции {position} — не "
                f"отображение, а {type(decision).__name__}; найдено {decision!r}"
            )
    return decisions


def declared_rule_of(record: ProhibitionRecord) -> str:
    """Имя правила, объявленное формулировкой запрета, либо `RULE_UNDECLARED`.

    Больше одного объявленного имени — отказ: какое из них стережёт запрет, решает человек,
    и засев молча выбрать не вправе.
    """
    names = DECLARED_RULE_TOKEN.findall(record.statement)
    if len(names) > 1:
        raise CensusError(f"`{record.identity}` объявляет больше одного правила: {names}")
    return names[0] if names else RULE_UNDECLARED


def _carries_declared_rule(record: ProhibitionRecord) -> bool:
    return (
        record.phase == DECLARED_RULE_PHASE
        and record.verification == DECLARED_RULE_VERIFICATION
    )


def registry_row(record: ProhibitionRecord) -> dict:
    """Засеянная строка реестра для записи переписи."""
    row: dict = {
        "plan": record.identity.plan_path,
        "index": record.identity.index,
        "phase": record.phase,
    }
    if record.verification is not None:
        row["verification"] = record.verification
    row["statement_digest"] = record.digest
    row["class"] = SEED_CLASS
    row["disposition"] = SEED_DISPOSITION
    if _carries_declared_rule(record):
        row["declared_rule"] = declared_rule_of(record)
    return row


def _ordered(row: Mapping) -> dict:
    ordered = {field: row[field] for field in REGISTRY_FIELD_ORDER if field in row}
    ordered.update({field: value for field, value in row.items() if field not in ordered})
    return ordered


def seed_registry(
    records: list[ProhibitionRecord], existing: Mapping | None, measured: str
) -> dict:
    """Новый документ реестра. ИДЕМПОТЕНТЕН ПО ТОЖДЕСТВАМ.

    Строка с уже записанным тождеством сохраняет ВСЕ свои поля — в том числе `class`,
    `disposition` и отпечаток: правка формулировки не «лечится» перезасевом, её ловит правило
    согласия строки с элементом. Недостающие поля строки добавляются засеянными. Строка
    реестра, чьего тождества в переписи нет, — отказ: снять её молча значило бы потерять
    записанное решение, и это решает человек.

    Блок `CLASS_DECISIONS_KEY` (ответ владельца по классам) ПЕРЕНОСИТСЯ как есть и встаёт
    после шапки замера, перед строками; засев его не пишет, не дополняет и не правит.
    """
    old_rows = _registry_rows(existing or {})
    current = {record.identity for record in records}
    vanished = sorted(set(old_rows) - current)
    if vanished:
        raise CensusError(
            "строки реестра без запрета в переписи — засев их не снимает:\n"
            + "\n".join(f"  {identity}" for identity in vanished)
        )
    rows: list[dict] = []
    added = 0
    for record in sorted(records, key=lambda item: item.identity):
        fresh = registry_row(record)
        old = old_rows.get(record.identity)
        if old is None:
            added += 1
            rows.append(_ordered(fresh))
            continue
        merged = dict(old)
        for field, value in fresh.items():
            merged.setdefault(field, value)
        rows.append(_ordered(merged))
    keep_date = existing and not added and existing.get("measured")
    document: dict = {
        "measured": str(existing["measured"]) if keep_date else measured,
        "rows_declared": len(rows),
    }
    if existing and CLASS_DECISIONS_KEY in existing:
        document[CLASS_DECISIONS_KEY] = existing[CLASS_DECISIONS_KEY]
    document["rows"] = rows
    return document


def dump_registry(document: Mapping) -> str:
    """Текст реестра: шапка-комментарий и по одной строке YAML на запрет."""
    body = yaml.safe_dump(
        dict(document),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=None,
        width=100_000,
    )
    return REGISTRY_HEADER + "\n" + body


# --- запись меры покрытия (план 15-22) ---------------------------------------------


def _resolve_identity(
    records: Iterable[ProhibitionRecord], identity: str
) -> ProhibitionRecord:
    """Запись переписи по тождеству: полный путь `…/10-01-PLAN.md#2` либо уникальный хвост.

    Хвост сличается по границе сегмента пути (`10-01-PLAN.md#2` не совпадает с
    `110-01-PLAN.md#2`). Ни одного совпадения — «вне переписи»; больше одного — отказ, а не
    первая попавшаяся строка.
    """
    matches = [
        record
        for record in records
        if str(record.identity) == identity or str(record.identity).endswith(f"/{identity}")
    ]
    if not matches:
        raise CensusError(f"тождество `{identity}` вне переписи")
    if len(matches) > 1:
        listed = ", ".join(str(record.identity) for record in matches)
        raise CensusError(f"тождество `{identity}` неоднозначно: {listed}")
    return matches[0]


def _definition_line(path: Path, name: str) -> int | None:
    """Строка первого определения функции `name` в файле — по дереву `ast`, а не по тексту."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as error:
        raise CensusError(f"`{path.name}` не разбирается `ast`: {error}") from error
    lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    return min(lines) if lines else None


def _rule_pairs(row: Mapping) -> list[tuple[str, str]]:
    """Записанные пары «имя, координата» строки; строка без правил — пустой список."""
    names, sites = row.get(RULE_NAME_FIELD), row.get(RULE_SITE_FIELD)
    if not isinstance(names, str) or not isinstance(sites, str):
        return []
    return list(zip(names.split(RULE_SEPARATOR), sites.split(RULE_SEPARATOR)))


def _measured_rules(
    rules: list[str], recorded: list[tuple[str, str]], suite_root: Path
) -> list[tuple[str, str]]:
    """Пары «имя, координата» по ссылкам `tests/…::имя`; каждое правило найдено деревом.

    Координата — `путь:строка` определения, снятая разбором `ast`. ⚠️ КООРДИНАТА ЕСТЬ ДЕНЬ
    ЗАМЕРА: если строка уже называет то же правило в том же файле, записанная координата
    сохраняется — иначе запись меры по одной строке двигала бы номер строки у каждой
    перезаписанной строки, чей файл с тех пор вырос (гейт номер строки не утверждает). Новое
    правило получает координату, снятую сейчас.
    """
    if not rules:
        raise CensusError("не названо ни одного правила: мера покрытия без правил не пишется")
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for reference in rules:
        path, separator, name = reference.rpartition(RULE_REFERENCE_SEPARATOR)
        if not separator or not path or not name:
            raise CensusError(
                f"ссылка на правило `{reference}` не в форме `tests/…py{RULE_REFERENCE_SEPARATOR}имя`"
            )
        if not path.startswith(SUITE_PREFIX) or not path.endswith(".py"):
            raise CensusError(f"ссылка `{reference}`: файл правила не в каталоге `{SUITE_PREFIX}`")
        if reference in seen:
            raise CensusError(f"правило `{reference}` названо дважды")
        seen.add(reference)
        source = suite_root / path[len(SUITE_PREFIX):]
        if not source.is_file():
            raise CensusError(f"ссылка `{reference}`: файла `{path}` в дереве суиты нет")
        line = _definition_line(source, name)
        if line is None:
            raise CensusError(
                f"правила `{name}` в `{path}` по разбору `ast` нет — объявление правила не есть "
                f"правило"
            )
        kept = next(
            (
                site
                for recorded_name, site in recorded
                if recorded_name == name and site.rpartition(":")[0] == path
            ),
            None,
        )
        pairs.append((name, kept or f"{path}:{line}"))
    return pairs


def record_coverage(
    document: dict,
    records: list[ProhibitionRecord],
    identity: str,
    disposition: str,
    rules: list[str],
    coverage_note: str | None,
    permit_uncovered: bool,
    suite_root: Path,
) -> dict:
    """ЕДИНСТВЕННОЕ место записи меры покрытия строки области решений; возвращает строку.

    Находит строку по тождеству (полный путь либо уникальный хвост), требует область решений
    (D-02), диспозицию из `COVERAGE_DISPOSITIONS`, правило каждой ссылки `tests/…::имя` —
    найденным разбором `ast` в файле ссылки, непустую непокрытую часть у частичной и её
    отсутствие у полной. Пишет `disposition`, `rule_name` и `rule_site` (через
    `RULE_SEPARATOR`), `coverage_note` у частичной; снимает `unresolved_reason` и
    `permit_scope` — поля, которые запись меры делает ложными. По `permit_uncovered` ставит
    `permit_scope_uncovered` = класс строки — только частичной строке класса с ветвью
    `permit-class` (план 15-22, задача 2; правила — `_permit_uncovered_fields`). Класса, блока
    `class_decisions` и вердикта не пишет.

    Любой отказ — `CensusError` ДО первой записи: документ либо изменён целиком, либо не изменён
    вовсе. `suite_root` — каталог суиты (`tests/`), от которого разрешаются ссылки.
    """
    record = _resolve_identity(records, identity)
    row = _registry_rows(document).get(record.identity)
    if row is None:
        raise CensusError(f"тождество `{record.identity}` без строки реестра — засейте реестр")
    if record.phase != DECISION_SCOPE_PHASE:
        raise CensusError(
            f"`{record.identity}` вне области решений (D-02, фаза {DECISION_SCOPE_PHASE}): "
            f"мера покрытия там не пишется"
        )
    if disposition not in COVERAGE_DISPOSITIONS:
        raise CensusError(
            f"диспозиция `{disposition}` не есть мера покрытия: режим записи пишет только "
            f"{', '.join(f'`{value}`' for value in COVERAGE_DISPOSITIONS)}"
        )
    note = coverage_note.strip() if isinstance(coverage_note, str) else ""
    if disposition == PARTIALLY_ENFORCED and not note:
        raise CensusError(
            f"`{record.identity}`: частичная диспозиция без `{COVERAGE_NOTE_FIELD}` — непокрытая "
            f"часть называется, а не подразумевается"
        )
    if disposition == ENFORCED and note:
        raise CensusError(
            f"`{record.identity}`: `{COVERAGE_NOTE_FIELD}` при полной диспозиции — непокрытой "
            f"части у неё нет"
        )
    pairs = _measured_rules(rules, _rule_pairs(row), suite_root)
    permit_fields = _permit_uncovered_fields(document, row, disposition, permit_uncovered)

    updated = {
        field: value
        for field, value in row.items()
        if field not in (UNRESOLVED_REASON_FIELD, PERMIT_SCOPE_FIELD, COVERAGE_NOTE_FIELD)
        and field not in permit_fields
    }
    updated["disposition"] = disposition
    updated[RULE_NAME_FIELD] = RULE_SEPARATOR.join(name for name, _ in pairs)
    updated[RULE_SITE_FIELD] = RULE_SEPARATOR.join(site for _, site in pairs)
    if disposition == PARTIALLY_ENFORCED:
        updated[COVERAGE_NOTE_FIELD] = coverage_note.strip()
    updated.update({field: value for field, value in permit_fields.items() if value is not None})
    ordered = _ordered(updated)
    position = next(index for index, item in enumerate(document["rows"]) if item is row)
    document["rows"][position] = ordered
    return ordered


def _permit_uncovered_fields(
    document: Mapping, row: Mapping, disposition: str, permit_uncovered: bool
) -> dict:
    """Поля разрешения непокрытой части, которые запись ставит (значение) или снимает (`None`).

    Флаг ставит `permit_scope_uncovered` = класс строки и отказывает, если диспозиция не
    частичная или ветвь ответа владельца по классу не `permit-class`. Без флага поле снимается;
    но частичная строка разрешённого класса без флага — отказ: запись оставила бы остаток её
    предмета не закрытым ничем, и гейт назвал бы строку. Отказ поднимается ДО первой записи.
    """
    klass = str(row.get("class"))
    branch = _branch_by_class(document).get(klass)
    permitted_class = branch == PERMIT_CLASS_BRANCH
    identity = f"{row.get('plan')}#{row.get('index')}"
    if permit_uncovered:
        if disposition != PARTIALLY_ENFORCED:
            raise CensusError(
                f"`{identity}`: `{PERMIT_SCOPE_UNCOVERED_FIELD}` только у `{PARTIALLY_ENFORCED}`, "
                f"а записывается `{disposition}` — у полной непокрытой части нет"
            )
        if not permitted_class:
            raise CensusError(
                f"`{identity}`: класс `{klass}` получил ветвь `{branch}`, а не "
                f"`{PERMIT_CLASS_BRANCH}` — разрешения остатка владелец не давал"
            )
        return {PERMIT_SCOPE_UNCOVERED_FIELD: klass}
    if disposition == PARTIALLY_ENFORCED and permitted_class:
        raise CensusError(
            f"`{identity}`: частичная строка разрешённого класса `{klass}` без "
            f"`{PERMIT_SCOPE_UNCOVERED_FIELD}` — передайте `--permit-uncovered`, иначе остаток "
            f"её предмета не закрыт ничем"
        )
    return {PERMIT_SCOPE_UNCOVERED_FIELD: None}


# --- исторические сети ------------------------------------------------------------
#
# Четыре сети, давшие на 57 планах Фазы 10 четыре числа (374 / 76 / 57 / 38; критерий 6 ROADMAP
# называет их предметом расхождения). Прибор их ВОСПРОИЗВОДИТ и раскладывает каждую на
# слагаемые: это доказывает СОГЛАСИЕ прибора с тем множеством, которое сеть измеряет, и умение
# это множество назвать, — а не верность сети. Сеть считает СТРОКИ файла целиком (шапка и
# тело), как `grep` по склеенным файлам.
#
# ⚠️ СЛАГАЕМЫЕ СНИМАЮТСЯ НЕЗАВИСИМО ОТ ЧИСЛА СЕТИ: элементы блоков — разбором шапки, тело плана
# и проза шапки — счётом строк. Остатка «число сети минус известное» среди слагаемых НЕТ: он
# сошёлся бы всегда. Равенство суммы слагаемых числу сети есть проверка, а не определение.

HISTORIC_PHASE = "10"
HISTORIC_PROHIBITIONS_KEY_LINE = re.compile(r"\s*prohibitions:")
HISTORIC_VERIFICATION_TEST_TEXT = "verification: test"
HISTORIC_VERIFICATION_TEST_KEY_LINE = re.compile(r"\s*(?:- )?verification:\s*test\s*$")
HISTORIC_PROSE_MARKERS = re.compile(r"MUST NOT|НЕ ДОЛЖ|ЗАПРЕЩ")

# Имена слагаемых — одно место на прибор; на них ссылаются правила согласия модуля теста.
ADDEND_CENSUS = "элементы переписи"
ADDEND_DASH_ELSEWHERE = "элементы переписи с дефисом на чужом ключе"
ADDEND_TRUTHS_STATEMENT_FIRST = "элементы truths с дефисом на формулировке"
ADDEND_ASSUMPTIONS_STATEMENT_FIRST = "элементы assumptions с дефисом на формулировке"
ADDEND_BODY_LINES = "строки тела плана"
ADDEND_VERIFICATION_TEST_CENSUS = "элементы переписи с `verification: test`"
ADDEND_VERIFICATION_TEST_TRUTHS = "элементы truths с `verification: test`"
ADDEND_VERIFICATION_TEST_ASSUMPTIONS = "элементы assumptions с `verification: test`"
ADDEND_VERIFICATION_TEST_FRONTMATTER_PROSE = "упоминания фразы в прозе шапки"
ADDEND_VERIFICATION_TEST_BODY_PROSE = "упоминания фразы в теле плана"
ADDEND_PLANS_WITH_BLOCK = "планы с блоком `must_haves.prohibitions` (блоки, а не элементы)"
ADDEND_MARKERS_CENSUS = "элементы переписи с маркером"
ADDEND_MARKERS_TRUTHS = "элементы truths с маркером"
ADDEND_MARKERS_ASSUMPTIONS = "элементы assumptions с маркером"

ADD, SUBTRACT = 1, -1


@dataclass(frozen=True)
class HistoricNet:
    """Историческая сеть: образец, число и слагаемые «знак, имя, величина».

    Знак хранится отдельно от величины: вычитаемое слагаемое, равное нулю, остаётся
    ВЫЧИТАЕМЫМ — его имя говорит, что сеть теряет такие элементы, даже когда их ноль.
    """

    pattern: str
    count: int
    addends: tuple[tuple[int, str, int], ...]

    @property
    def addends_total(self) -> int:
        return sum(sign * value for sign, _, value in self.addends)

    def addend(self, name: str) -> int:
        return next(value for _, label, value in self.addends if label == name)


def historic_sources(sources: Mapping[str, str]) -> dict[str, str]:
    """Подмножество вселенной — планы Фазы 10, на которых сняты четыре исторические сети."""
    return {path: text for path, text in sources.items() if phase_of(path) == HISTORIC_PHASE}


def _split_frontmatter(text: str) -> tuple[list[str], list[str]]:
    """Строки шапки (с ограждениями) и строки тела. Файл без шапки — всё тело."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return [], lines
    for position in range(1, len(lines)):
        if lines[position].strip() == FRONTMATTER_FENCE:
            return lines[: position + 1], lines[position + 1 :]
    return lines, []


def _element_text(element) -> str:
    if isinstance(element, dict):
        return str(element.get(STATEMENT_KEY, ""))
    return str(element)


def _verification_test(elements: Iterable) -> int:
    return sum(
        1
        for element in elements
        if isinstance(element, dict)
        and str(element.get(VERIFICATION_KEY)) == DECLARED_RULE_VERIFICATION
    )


def _with_markers(elements: Iterable) -> int:
    return sum(1 for element in elements if HISTORIC_PROSE_MARKERS.search(_element_text(element)))


def historic_nets(sources: Mapping[str, str]) -> list[HistoricNet]:
    """Четыре исторические сети над поданными исходниками — со слагаемыми расхождения."""
    records = census(sources)
    parsed = [_frontmatter(sources[path]) for path in sorted(sources)]
    split = [_split_frontmatter(sources[path]) for path in sorted(sources)]

    def elements(block: str) -> list:
        return [item for frontmatter in parsed for item in _block_elements(frontmatter, block)]

    prohibitions = elements(PROHIBITIONS_BLOCK)
    truths = elements(TRUTHS_BLOCK)
    assumptions = elements(ASSUMPTIONS_BLOCK)

    def frontmatter_lines(predicate) -> int:
        return sum(1 for head, _ in split for line in head if predicate(line))

    def body_lines(predicate) -> int:
        return sum(1 for _, body in split for line in body if predicate(line))

    def all_lines(predicate) -> int:
        return frontmatter_lines(predicate) + body_lines(predicate)

    def is_statement(line: str) -> bool:
        return bool(NAIVE_STATEMENT_LINE.match(line))

    def is_prohibitions_key(line: str) -> bool:
        return bool(HISTORIC_PROHIBITIONS_KEY_LINE.match(line))

    def is_verification_test(line: str) -> bool:
        return HISTORIC_VERIFICATION_TEST_TEXT in line

    def is_verification_test_prose(line: str) -> bool:
        return is_verification_test(line) and not HISTORIC_VERIFICATION_TEST_KEY_LINE.match(line)

    def has_marker(line: str) -> bool:
        return bool(HISTORIC_PROSE_MARKERS.search(line))

    plans_with_block = sum(
        1 for frontmatter in parsed if PROHIBITIONS_BLOCK in (frontmatter.get(MUST_HAVES) or {})
    )
    return [
        HistoricNet(
            pattern=r"^\s*- statement:",
            count=all_lines(is_statement),
            addends=(
                (ADD, ADDEND_CENSUS, len(records)),
                (
                    SUBTRACT,
                    ADDEND_DASH_ELSEWHERE,
                    sum(1 for record in records if record.first_key != STATEMENT_KEY),
                ),
                (ADD, ADDEND_TRUTHS_STATEMENT_FIRST, _statement_first(truths)),
                (ADD, ADDEND_ASSUMPTIONS_STATEMENT_FIRST, _statement_first(assumptions)),
                (ADD, ADDEND_BODY_LINES, body_lines(is_statement)),
            ),
        ),
        HistoricNet(
            pattern=HISTORIC_VERIFICATION_TEST_TEXT,
            count=all_lines(is_verification_test),
            addends=(
                (ADD, ADDEND_VERIFICATION_TEST_CENSUS, _verification_test(prohibitions)),
                (ADD, ADDEND_VERIFICATION_TEST_TRUTHS, _verification_test(truths)),
                (ADD, ADDEND_VERIFICATION_TEST_ASSUMPTIONS, _verification_test(assumptions)),
                (
                    ADD,
                    ADDEND_VERIFICATION_TEST_FRONTMATTER_PROSE,
                    frontmatter_lines(is_verification_test_prose),
                ),
                (ADD, ADDEND_VERIFICATION_TEST_BODY_PROSE, body_lines(is_verification_test)),
            ),
        ),
        HistoricNet(
            pattern=r"^\s*prohibitions:",
            count=all_lines(is_prohibitions_key),
            addends=(
                (ADD, ADDEND_PLANS_WITH_BLOCK, plans_with_block),
                (ADD, ADDEND_BODY_LINES, body_lines(is_prohibitions_key)),
            ),
        ),
        HistoricNet(
            pattern=HISTORIC_PROSE_MARKERS.pattern,
            count=all_lines(has_marker),
            addends=(
                (ADD, ADDEND_MARKERS_CENSUS, _with_markers(prohibitions)),
                (ADD, ADDEND_MARKERS_TRUTHS, _with_markers(truths)),
                (ADD, ADDEND_MARKERS_ASSUMPTIONS, _with_markers(assumptions)),
                (ADD, ADDEND_BODY_LINES, body_lines(has_marker)),
            ),
        ),
    ]


def _terms(addends) -> str:
    terms = []
    for position, (sign, name, value) in enumerate(addends):
        prefix = "" if position == 0 and sign == ADD else ("+ " if sign == ADD else "− ")
        terms.append(f"{prefix}{value} {name}")
    return " ".join(terms)


def reconcile_lines(sources: Mapping[str, str]) -> list[str]:
    """Таблица сличения «сеть → число → чем отличается от переписи», по строке на сеть."""
    before = {path: text for path, text in sources.items() if phase_of(path) != "15"}
    lines = [
        "| Сеть | Множество | Число | Слагаемые расхождения с переписью |",
        "|---|---|---:|---|",
    ]
    universes = (
        ("веха без планов Фазы 15", before),
        (
            f"веха по план {FIXED_SET_PHASE}-{FIXED_SET_LAST_PLAN} включительно",
            through_fixed_set(sources),
        ),
        ("веха целиком", sources),
    )
    for label, universe in universes:
        parts = decomposition(universe)
        lines.append(
            f"| разбор блока `must_haves.prohibitions` | {label}, планов {len(universe)} | "
            f"{parts.prohibitions} | целевое множество — перепись |"
        )
        addends = (
            (ADD, ADDEND_CENSUS, parts.prohibitions),
            (SUBTRACT, ADDEND_DASH_ELSEWHERE, parts.first_key_elsewhere),
            (ADD, ADDEND_TRUTHS_STATEMENT_FIRST, parts.truths),
            (ADD, ADDEND_ASSUMPTIONS_STATEMENT_FIRST, parts.assumptions),
        )
        lines.append(
            f"| `^\\s*- statement:` | {label}, планов {len(universe)} | {parts.line_net} | "
            f"{_terms(addends)} = {parts.reconstructed} |"
        )
    phase_10 = historic_sources(sources)
    for net in historic_nets(phase_10):
        pattern = net.pattern.replace("|", "\\|")
        lines.append(
            f"| `{pattern}` | Фаза 10, планов {len(phase_10)} | {net.count} | "
            f"{_terms(net.addends)} = {net.addends_total} |"
        )
    return lines


# --- черновая разбивка по классам ---------------------------------------------------
#
# ⚠️ ЧЕРНОВИК, А НЕ КЛАССИФИКАТОР. Замер разведки (15-RESEARCH.md Ф-04) на восьми классах: 139
# запретов из 321 попадают в два и более класса, 64 — ни в один, и «первое совпадение
# выигрывает» делает класс функцией ПОРЯДКА правил в этом перечне: переставьте два правила — и
# `permit_scope` сотни запретов сменит имя. Поэтому функция ниже возвращает ВСЕ классы-кандидаты
# (в порядке имён, чтобы и порядок вывода не зависел от порядка правил), класс записывается в
# реестр ЧТЕНИЕМ формулировки один раз, а принуждающая половина прибора этот раздел не
# импортирует и не зовёт. Имена классов — те же, что в `PROHIBITION_CLASSES` модуля теста;
# расхождение имён видно в выводе `--draft-classes` как класс реестра вне всех кандидатов.

DECISION_SCOPE_PHASE = "10"

DRAFT_CLASS_PATTERNS: dict[str, re.Pattern] = {
    "gate-integrity": re.compile(
        r"правил|контрол|вакуум|литерал|объявленн\w* числ|подгон|pytest\.skip|синтетик|"
        r"констант|подмен\w* \w*\s?рантайм|D-33|зелен|зелён|изъяти|вселенн",
        re.IGNORECASE,
    ),
    "live-environment-safety": re.compile(
        r"посев|DATABASE_URL|боев\w* баз|live_dom_uat|\bпрод\b|стенд", re.IGNORECASE
    ),
    "owner-decision-reserved": re.compile(
        r"решени\w* владельц|владел\w* вехи|не принимается внутри|имя принявшего|не сочиняется|"
        r"запер|решени\w* вехи|решение уровня вехи|ветв\w* не предлагается|D-01|D-11|D-13",
        re.IGNORECASE,
    ),
    "plan-file-scope": re.compile(
        r"этим планом|настоящим планом|files_modified|`app/|app\.css|не правится ни на|"
        r"не правятся ни на|не трогается|не трогаются",
        re.IGNORECASE,
    ),
    "product-invariant": re.compile(
        r"оптимистичн|панел|плашк|заготовк|уведомлен|notice|гард|фокус|селектор|"
        r"идентификатор|скоуп|x-data|hx-on|hx-confirm|T-\d\d-\d\d|WR-04|отказ",
        re.IGNORECASE,
    ),
    "record-immutability": re.compile(
        r"исполненн\w* план|сводк|\.planning/research|ROADMAP|роадмап|CONTEXT\.md|реестр\w* окон|"
        r"PROHIBITIONS-SUBJECT|задним числом|переписанн\w* истори",
        re.IGNORECASE,
    ),
    "requirement-flag": re.compile(
        r"FORM-06|REQUIREMENTS\.md|требовани\w* не помечается|отмечается выполненным",
        re.IGNORECASE,
    ),
    "self-certification": re.compile(
        r"UAT|отметк|терминальн|самозаверен|вердикт|VERIFICATION|гэп|G-10-7|обход",
        re.IGNORECASE,
    ),
    "superseded-text-kept": re.compile(
        r"вычёркива|вычеркива|стира|опровергнут|D-30/D-32|летопис", re.IGNORECASE
    ),
    "vendored-runtime-and-dependencies": re.compile(
        r"вендорен|htmx\.min|alpine\.min|строки JS|зависимост|build-шаг|playwright|selenium",
        re.IGNORECASE,
    ),
    "work-owned-elsewhere": re.compile(
        r"Фаз[еыаи] 1[15]|отложен|предсуществующ|IN-0\d|UI-\d|не чинится|не чинятся|"
        r"не втягивается|перемаршрутиз|владел\w* котор",
        re.IGNORECASE,
    ),
}


def _draft_class_candidates(record: ProhibitionRecord) -> tuple[str, ...]:
    """ВСЕ классы-кандидаты формулировки по ключевым словам — в порядке имён, а не правил."""
    return tuple(
        name
        for name in sorted(DRAFT_CLASS_PATTERNS)
        if DRAFT_CLASS_PATTERNS[name].search(record.statement)
    )


def _decision_scope(records: Iterable[ProhibitionRecord]) -> list[ProhibitionRecord]:
    return [record for record in records if record.phase == DECISION_SCOPE_PHASE]


# --- режимы ------------------------------------------------------------------------


def _print_breakdown(records: list[ProhibitionRecord]) -> None:
    print(f"элементов блока must_haves.prohibitions: {len(records)}")
    for phase, count in phase_breakdown(records).items():
        print(f"  фаза {phase}: {count}")


def _check(root: Path) -> int:
    records = census(_plan_sources(root))
    _print_breakdown(records)
    document = load_registry(root / REGISTRY_RELATIVE_PATH)
    registry = _registry_rows(document)
    problems: list[str] = []
    if document.get("rows_declared") != len(records):
        problems.append(
            f"`rows_declared` реестра {document.get('rows_declared')}, перепись {len(records)}"
        )
    if len(registry) != len(records):
        problems.append(f"строк реестра {len(registry)}, перепись {len(records)}")
    census_ids = {record.identity for record in records}
    for identity in sorted(census_ids - set(registry)):
        problems.append(f"запрет без строки реестра: {identity}")
    for identity in sorted(set(registry) - census_ids):
        problems.append(f"строка реестра без запрета: {identity}")
    # Ключи разрешения в строках реестра — ПЕЧАТАЮТСЯ, а не судятся: их заводит ответ владельца
    # (план 15-12, задача 3; строки — план 15-13), и число здесь есть улика для человека.
    permit_keys = sum(
        1 for row in registry.values() for field in row if str(field).startswith(PERMIT_PREFIX)
    )
    print(f"ключей разрешения (`{PERMIT_PREFIX}*`) в строках реестра: {permit_keys}")
    # Ответ владельца по классам — ПЕЧАТАЕТСЯ, а не судится: форму судит модуль теста.
    decisions = _class_decisions(document)
    permitted = sorted(
        str(decision[PERMIT_SCOPE_FIELD])
        for decision in decisions
        if PERMIT_SCOPE_FIELD in decision
    )
    print(
        f"решений владельца по классам (`{CLASS_DECISIONS_KEY}`): {len(decisions)}; "
        f"разрешённых классов (`{PERMIT_SCOPE_FIELD}`): {len(permitted)}"
    )
    for name in permitted:
        print(f"  разрешён класс: {name}")
    for decision in decisions:
        if DECISION_SCOPE_FIELD in decision:
            print(
                f"  класс {decision[DECISION_SCOPE_FIELD]}: "
                f"{decision.get(DECISION_BRANCH_FIELD)}"
            )
    if problems:
        print("РАСХОЖДЕНИЕ переписи с реестром:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"реестр: {len(registry)} строк, биекция с переписью — согласие")
    return 0


def _list(root: Path, phase: str | None, klass: str | None = None) -> int:
    registry = _registry_rows(load_registry(root / REGISTRY_RELATIVE_PATH))
    for record in census(_plan_sources(root)):
        if phase is not None and record.phase != phase:
            continue
        row = registry.get(record.identity, {})
        if klass is not None and row.get("class") != klass:
            continue
        verification = verification_label(record)
        statement = " ".join(record.statement.split())[:100]
        print(
            f"{record.identity}  фаза {record.phase}  verification={verification}  "
            f"class={row.get('class', '?')}  disposition={row.get('disposition', '?')}  "
            f"{statement}"
        )
    return 0


def _branch_by_class(document: Mapping) -> dict[str, str]:
    """Ветвь ответа владельца по имени класса — для глаз человека и режима записи, не для гейта.

    Режим `--record` берёт отсюда ветвь класса строки, чтобы поставить либо отказать в
    `permit_scope_uncovered`; гейт судит то же своим помощником `_branch_of_class`.
    """
    branches: dict[str, str] = {}
    for decision in _class_decisions(document):
        if PERMIT_SCOPE_FIELD in decision:
            branches[str(decision[PERMIT_SCOPE_FIELD])] = str(decision.get("permit_branch"))
        elif DECISION_SCOPE_FIELD in decision:
            branches[str(decision[DECISION_SCOPE_FIELD])] = str(
                decision.get(DECISION_BRANCH_FIELD)
            )
    return branches


def _breakdown(root: Path) -> int:
    records = census(_plan_sources(root))
    document = load_registry(root / REGISTRY_RELATIVE_PATH)
    registry = _registry_rows(document)
    branches = _branch_by_class(document)
    print("по фазам:")
    for phase, count in phase_breakdown(records).items():
        print(f"  фаза {phase}: {count}")
    print("по значениям `verification` (— ключа нет):")
    values = Counter(verification_label(record) for record in records)
    for value, count in sorted(values.items()):
        print(f"  {value}: {count}")
    print("по диспозициям реестра (? — строки нет):")
    dispositions = Counter(
        str(registry.get(record.identity, {}).get("disposition", "?")) for record in records
    )
    for value, count in sorted(dispositions.items()):
        print(f"  {value}: {count}")

    def class_of(record: ProhibitionRecord) -> str:
        return str(registry.get(record.identity, {}).get("class", "?"))

    print("по классам реестра, вся веха (? — строки нет):")
    for value, count in sorted(Counter(class_of(record) for record in records).items()):
        print(f"  {value}: {count}")
    scope = _decision_scope(records)
    print(
        f"по классам области решений (фаза {DECISION_SCOPE_PHASE}): запретов / из них с "
        f"`verification: {DECLARED_RULE_VERIFICATION}` — ветвь ответа владельца "
        f"(`{CLASS_DECISIONS_KEY}`; «—» — ответа нет)"
    )
    by_class = Counter(class_of(record) for record in scope)
    tested = Counter(
        class_of(record) for record in scope if record.verification == DECLARED_RULE_VERIFICATION
    )
    for value in sorted(by_class):
        branch = branches.get(value, "—")
        print(f"  {value}: {by_class[value]} / {tested[value]} — {branch}")
    print(
        f"  сумма по классам области решений: {sum(by_class.values())} "
        f"(классов {len(by_class)})"
    )

    def row_of(record: ProhibitionRecord) -> Mapping:
        return registry.get(record.identity, {})

    # Диспозиции ОБЛАСТИ РЕШЕНИЙ (план 15-13) — для глаз человека: сумма обязана быть числом
    # области, а распределение ПЕЧАТАЕТСЯ, а не судится (судит его модуль теста принадлежностью).
    print(f"по диспозициям области решений (фаза {DECISION_SCOPE_PHASE}):")
    scope_dispositions = Counter(str(row_of(record).get("disposition", "?")) for record in scope)
    for value, count in sorted(scope_dispositions.items()):
        print(f"  {value}: {count}")
    print(f"  сумма по диспозициям области решений: {sum(scope_dispositions.values())}")
    reasons = Counter(
        str(row_of(record).get("unresolved_reason", "— (причины нет)"))
        for record in scope
        if row_of(record).get("disposition") == SEED_DISPOSITION
    )
    print(f"причины «{SEED_DISPOSITION}» в области решений:")
    for value, count in sorted(reasons.items()):
        print(f"  {value}: {count}")
    print(
        f"по диспозициям области решений и классам (класс: диспозиция — число; "
        f"`verification: {DECLARED_RULE_VERIFICATION}` — в скобках):"
    )
    for value in sorted(by_class):
        members = [record for record in scope if class_of(record) == value]
        cells = Counter(str(row_of(record).get("disposition", "?")) for record in members)
        tested_cells = Counter(
            str(row_of(record).get("disposition", "?"))
            for record in members
            if record.verification == DECLARED_RULE_VERIFICATION
        )
        listed = ", ".join(
            f"{name} {count} ({tested_cells[name]})" for name, count in sorted(cells.items())
        )
        print(f"  {value}: {listed}")
    tested_scope = [
        record for record in scope if record.verification == DECLARED_RULE_VERIFICATION
    ]
    print(
        f"мера покрытия запретов с `verification: {DECLARED_RULE_VERIFICATION}` "
        f"(D-05, {len(tested_scope)}):"
    )
    for value, count in sorted(
        Counter(str(row_of(record).get("disposition", "?")) for record in tested_scope).items()
    ):
        print(f"  {value}: {count}")
    # Разрешение непокрытой части (план 15-22, задача 2) — ПЕЧАТАЕТСЯ, а не судится: форму поля
    # судит модуль теста принадлежностью.
    partial_scope = [
        record
        for record in scope
        if row_of(record).get("disposition") == PARTIALLY_ENFORCED
    ]
    carrying = [
        record for record in partial_scope if PERMIT_SCOPE_UNCOVERED_FIELD in row_of(record)
    ]
    print(
        f"частичных строк области решений с `{PERMIT_SCOPE_UNCOVERED_FIELD}`: {len(carrying)}; "
        f"без поля: {len(partial_scope) - len(carrying)}"
    )
    for value, count in sorted(
        Counter(
            f"{class_of(record)} — "
            f"{'с полем' if PERMIT_SCOPE_UNCOVERED_FIELD in row_of(record) else 'без поля'} "
            f"(ветвь {branches.get(class_of(record), '—')})"
            for record in partial_scope
        ).items()
    ):
        print(f"  {value}: {count}")
    print(f"итого элементов блока must_haves.prohibitions: {len(records)}")
    return 0


def _draft(root: Path) -> int:
    records = _decision_scope(census(_plan_sources(root)))
    registry = _registry_rows(load_registry(root / REGISTRY_RELATIVE_PATH))
    widths: Counter = Counter()
    recorded_among = 0
    for record in records:
        candidates = _draft_class_candidates(record)
        widths[len(candidates)] += 1
        recorded = str(registry.get(record.identity, {}).get("class", "?"))
        mark = "∈" if recorded in candidates else "∉"
        recorded_among += recorded in candidates
        listed = ", ".join(candidates) if candidates else "—"
        print(f"{record.identity}  записан={recorded} {mark} кандидаты[{len(candidates)}]: {listed}")
    print(f"ЧЕРНОВАЯ РАЗБИВКА: область решений (фаза {DECISION_SCOPE_PHASE}) — {len(records)}")
    for width in sorted(widths):
        print(f"  кандидатов {width}: {widths[width]}")
    print(f"  многозначных (кандидатов ≥ 2): {sum(c for w, c in widths.items() if w >= 2)}")
    print(f"  беспризорных (кандидатов 0): {widths[0]}")
    print(f"  записанный класс среди кандидатов черновика: {recorded_among} из {len(records)}")
    return 0


def _reconcile(root: Path) -> int:
    for line in reconcile_lines(_plan_sources(root)):
        print(line)
    return 0


def _seed(root: Path) -> int:
    path = root / REGISTRY_RELATIVE_PATH
    existing = load_registry(path) if path.exists() else None
    document = seed_registry(census(_plan_sources(root)), existing, date.today().isoformat())
    text = dump_registry(document)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        print(f"реестр не изменился: {document['rows_declared']} строк")
        return 0
    path.write_text(text, encoding="utf-8")
    print(f"реестр записан: {document['rows_declared']} строк → {path.relative_to(root)}")
    return 0


def _record(root: Path, arguments: argparse.Namespace) -> int:
    """Режим `--record`: одна запись меры покрытия и реестр, записанный `dump_registry`.

    Формат строки прежний — одна строка YAML на запрет; отказ `record_coverage` поднимается до
    записи файла, и файл тогда не меняется ни на символ.
    """
    path = root / REGISTRY_RELATIVE_PATH
    document = load_registry(path)
    row = record_coverage(
        document,
        census(_plan_sources(root)),
        arguments.record,
        arguments.disposition,
        arguments.rule or [],
        arguments.coverage_note,
        arguments.permit_uncovered,
        root / SUITE_PREFIX.rstrip("/"),
    )
    path.write_text(dump_registry(document), encoding="utf-8")
    print(
        f"записано: {row['plan']}#{row['index']} — {row['disposition']}; "
        f"{RULE_NAME_FIELD}: {row[RULE_NAME_FIELD]}; {RULE_SITE_FIELD}: {row[RULE_SITE_FIELD]}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Вход прибора. Каждый вид порчи ввода проходит путём `ОТКАЗ:`.

    Порча шапки плана, ключ без значения, испорченный документ реестра, его строка или решение
    по классу — `CensusError`, и она печатается строкой `ОТКАЗ: …` в поток ошибок с кодом 1,
    а не трассой мимо этого пути (IN-01, IN-02, план 15-20).
    """
    parser = argparse.ArgumentParser(description="Перепись запретов планов вехи.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="число, разбивка, согласие с реестром")
    mode.add_argument("--list", action="store_true", help="перечень записей")
    mode.add_argument("--breakdown", action="store_true", help="разбивка по фазам и полям")
    mode.add_argument("--reconcile", action="store_true", help="сличение с сетями по строке")
    mode.add_argument("--seed-registry", action="store_true", help="засев скелета реестра")
    mode.add_argument(
        "--draft-classes", action="store_true", help="черновая разбивка: ВСЕ кандидаты"
    )
    mode.add_argument(
        "--record",
        metavar="ТОЖДЕСТВО",
        help="запись меры покрытия строки области решений (путь#N либо уникальный хвост)",
    )
    parser.add_argument("--phase", help="только эта фаза (с --list), например 10")
    parser.add_argument("--class", dest="klass", help="только этот класс (с --list)")
    parser.add_argument(
        "--disposition", choices=COVERAGE_DISPOSITIONS, help="мера покрытия (с --record)"
    )
    parser.add_argument(
        "--rule",
        action="append",
        metavar="tests/…py::имя",
        help="правило меры покрытия (с --record); повторяется для нескольких правил",
    )
    parser.add_argument(
        "--coverage-note", help="непокрытая часть предмета у частичной (с --record)"
    )
    parser.add_argument(
        "--permit-uncovered",
        action="store_true",
        help="непокрытая часть частичной строки разрешена разрешением её класса (с --record)",
    )
    arguments = parser.parse_args(argv)
    if arguments.phase is not None and not arguments.list:
        parser.error("--phase применим только с --list")
    if arguments.klass is not None and not arguments.list:
        parser.error("--class применим только с --list")
    record_flags = (
        arguments.disposition is not None
        or arguments.rule is not None
        or arguments.coverage_note is not None
        or arguments.permit_uncovered
    )
    if record_flags and arguments.record is None:
        parser.error("--disposition, --rule, --coverage-note и --permit-uncovered — только с --record")
    if arguments.record is not None and arguments.disposition is None:
        parser.error("--record требует --disposition")
    try:
        if arguments.record is not None:
            return _record(TREE_ROOT, arguments)
        if arguments.check:
            return _check(TREE_ROOT)
        if arguments.list:
            return _list(TREE_ROOT, arguments.phase, arguments.klass)
        if arguments.breakdown:
            return _breakdown(TREE_ROOT)
        if arguments.reconcile:
            return _reconcile(TREE_ROOT)
        if arguments.draft_classes:
            return _draft(TREE_ROOT)
        return _seed(TREE_ROOT)
    except CensusError as error:
        print(f"ОТКАЗ: {error}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # Читатель закрыл канал (`--list | head`): перечень ему больше не нужен, и это не
        # отказ прибора. Поток вывода переводится в пустоту, чтобы интерпретатор не упал при
        # его закрытии на выходе.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())

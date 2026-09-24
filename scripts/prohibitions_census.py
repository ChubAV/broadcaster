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
                    реестром (число, `rows_declared`, биекция тождеств)
  --list [--phase N]
                    перечень записей глазам человека: тождество, фаза, `verification`,
                    диспозиция из реестра, первые ~100 символов формулировки
  --breakdown       разбивка по фазам, по значениям `verification` и по диспозициям реестра
  --reconcile       таблица сличения: разбор по блоку, наивная сеть по строке над вехой и
                    четыре исторические сети над планами Фазы 10 — каждая со СЛАГАЕМЫМИ
                    своего расхождения с переписью, а не только с разностью
  --seed-registry   засев скелета реестра; идемпотентен по тождествам — уже записанные поля
                    строк не двигаются, новые строки получают засеянные значения

Зависимость: PyYAML приходит транзитивно (`uvicorn[standard]`), объявленной не является; риск
назван в модуле теста.
"""

from __future__ import annotations

import argparse
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

# Наивная сеть по строке — ради РАЗЛОЖЕНИЯ расхождения, а не ради счёта: перепись её не
# использует. Сопоставляется построчно, чтобы `\s*` не перешагнул через перевод строки.
NAIVE_STATEMENT_LINE = re.compile(r"\s*- statement:")

DIGEST_LENGTH = 12

# Засеянные значения строки реестра. ⚠️ Это ПРЕДМЕТ решения, а не решение: класс пишет план
# 15-12, диспозицию — план 15-13 по ответу владельца. Полей `permit_*` засев не пишет вовсе.
SEED_CLASS = "unclassified"
SEED_DISPOSITION = "unresolved"

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
# ⚠️ ПОЛЕЙ `permit_*` И ЛЮБОГО ПОЛЯ ВЕРДИКТА ЗДЕСЬ НЕТ НАМЕРЕННО. `class: unclassified` и
# `disposition: unresolved` — засеянный ПРЕДМЕТ решения, а не решение: класс пишет план
# 15-12, диспозицию по ответу владельца — план 15-13. Исполнитель, поставивший поле вердикта
# сам, вынес бы вердикт вместо владельца.
#
# `declared_rule` стоит только у запретов Фазы 10 с `verification: test` (группа D-05): имя
# правила, названное формулировкой запрета, либо `<undeclared>` — признак «имя не объявлено».
# Это ОБЪЯВЛЕНИЕ автора запрета, снятое засевом, а не вердикт о соблюдении.
#
# `rows_declared` — второй носитель числа переписи (первый — литерал модуля теста);
# перегенерация реестра в другой размер краснит модуль.
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
    смешение двух вещей изъяло бы элемент из правила молча.
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


def _records_of(plan_path: str, text: str) -> list[ProhibitionRecord]:
    records: list[ProhibitionRecord] = []
    for index, element in enumerate(_block_elements(_frontmatter(text), PROHIBITIONS_BLOCK)):
        if not isinstance(element, dict) or STATEMENT_KEY not in element:
            raise CensusError(
                f"элемент #{index} блока `{MUST_HAVES}.{PROHIBITIONS_BLOCK}` — не словарь с "
                f"ключом `{STATEMENT_KEY}`: форма записи, которую прибор не знает, называется, "
                f"а не пропускается"
            )
        verification = element.get(VERIFICATION_KEY) if VERIFICATION_KEY in element else None
        status = element.get("status")
        records.append(
            ProhibitionRecord(
                identity=ProhibitionIdentity(plan_path, index),
                phase=phase_of(plan_path),
                statement=str(element[STATEMENT_KEY]),
                verification=None if verification is None else str(verification),
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
    """Документ реестра как есть; отсутствие файла — пустой реестр, а не падение."""
    if not path.exists():
        return {"rows_declared": 0, "rows": []}
    document = _safe_yaml(path.read_text(encoding="utf-8")) or {}
    document.setdefault("rows", [])
    return document


def _registry_rows(document: Mapping) -> dict[ProhibitionIdentity, dict]:
    """Строки реестра по тождеству. Повтор тождества — отказ: биекция не терпит дублей."""
    rows: dict[ProhibitionIdentity, dict] = {}
    for row in document.get("rows") or []:
        identity = ProhibitionIdentity(str(row["plan"]), int(row["index"]))
        if identity in rows:
            raise CensusError(f"тождество `{identity}` встречается в реестре дважды")
        rows[identity] = row
    return rows


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
    return {
        "measured": str(existing["measured"]) if keep_date else measured,
        "rows_declared": len(rows),
        "rows": rows,
    }


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
    for label, universe in (("веха без планов Фазы 15", before), ("веха целиком", sources)):
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
    if problems:
        print("РАСХОЖДЕНИЕ переписи с реестром:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"реестр: {len(registry)} строк, биекция с переписью — согласие")
    return 0


def _list(root: Path, phase: str | None) -> int:
    registry = _registry_rows(load_registry(root / REGISTRY_RELATIVE_PATH))
    for record in census(_plan_sources(root)):
        if phase is not None and record.phase != phase:
            continue
        row = registry.get(record.identity, {})
        verification = record.verification if record.verification is not None else "—"
        statement = " ".join(record.statement.split())[:100]
        print(
            f"{record.identity}  фаза {record.phase}  verification={verification}  "
            f"disposition={row.get('disposition', '?')}  {statement}"
        )
    return 0


def _breakdown(root: Path) -> int:
    records = census(_plan_sources(root))
    registry = _registry_rows(load_registry(root / REGISTRY_RELATIVE_PATH))
    print("по фазам:")
    for phase, count in phase_breakdown(records).items():
        print(f"  фаза {phase}: {count}")
    print("по значениям `verification` (— ключа нет):")
    values = Counter(record.verification or "—" for record in records)
    for value, count in sorted(values.items()):
        print(f"  {value}: {count}")
    print("по диспозициям реестра (? — строки нет):")
    dispositions = Counter(
        str(registry.get(record.identity, {}).get("disposition", "?")) for record in records
    )
    for value, count in sorted(dispositions.items()):
        print(f"  {value}: {count}")
    print(f"итого элементов блока must_haves.prohibitions: {len(records)}")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Перепись запретов планов вехи.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="число, разбивка, согласие с реестром")
    mode.add_argument("--list", action="store_true", help="перечень записей")
    mode.add_argument("--breakdown", action="store_true", help="разбивка по фазам и полям")
    mode.add_argument("--reconcile", action="store_true", help="сличение с сетями по строке")
    mode.add_argument("--seed-registry", action="store_true", help="засев скелета реестра")
    parser.add_argument("--phase", help="только эта фаза (с --list), например 10")
    arguments = parser.parse_args(argv)
    if arguments.phase is not None and not arguments.list:
        parser.error("--phase применим только с --list")
    try:
        if arguments.check:
            return _check(TREE_ROOT)
        if arguments.list:
            return _list(TREE_ROOT, arguments.phase)
        if arguments.breakdown:
            return _breakdown(TREE_ROOT)
        if arguments.reconcile:
            return _reconcile(TREE_ROOT)
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

"""Запись о прохождении ручного обхода НЕ БЫВАЕТ ШИРЕ его собственных отметок.

ЗАЧЕМ. Правило записал САМ артефакт обхода Фазы 10 своими словами: «отметка без
наблюдённого признака закрытием не считается» (шесть раз, по одному под каждой
таблицей отметок) и «значение `status: passed` до этого ставить ЗАПРЕЩЕНО» (шапка).
Правило есть; ПРИНУЖДЕНИЯ у него нет ни одного. Ровно так же за месяц до этого
выглядел регламент отметок требований — записан словами проекта, не принуждён ничем,
— и его обошёл коммит `0ea886d`, поставивший требованию отметку завершённости при
открытом блокере. Поймал это следующий круг верификации, а не прогон. Настоящий модуль
и есть недостающее принуждение: он живёт в `tests/` и потому входит в `just test`, так
что артефакт, объявивший себя закрытым при пустых таблицах отметок, краснит прогон.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он НЕ утверждает, что обход ПРОЙДЕН, и не может
этого утверждать: правило, объявившее прохождение ручного обхода, было бы
самозаверением на один уровень выше — ровно тем, что оно призвано запретить. Он
утверждает единственное: ЗАПИСЬ о прохождении не шире собственных отметок артефакта.
Он не судит прозы шагов, не проверяет ВЕРНОСТИ ожиданий и ни одной строкой не говорит
о рантайме разметки: машинной подмены рантайма здесь не заводится ни в каком виде —
суита не свопает фрагментов и внеполосных узлов не применяет. Правило якорей ниже
утверждает ПРИСУТСТВИЕ узла в шаблоне, а не то, что рантайм что-либо с ним сделал.

⚠️ ЛИТЕРАЛА НЕПРОЙДЕННОГО СОСТОЯНИЯ ЗДЕСЬ НЕТ ВОВСЕ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ. Правило,
знающее имя того состояния, в котором дерево находится СЕГОДНЯ, зеленело бы ровно при
условии, что фаза не достигла цели, — дословно тот блокер, который четвёртый круг
верификации нашёл у соседнего модуля каталога. Нетерминальность выражается ОТРИЦАНИЕМ
принадлежности объявленному перечню, а не именем; полное распределение значений поля
состояния по дереву записано в сводке плана 10-20, а не в исходнике.

ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. Решение D-33 отказало машинному гейту на ПРОЗЕ
операционного документа с названной причиной: отличить «константу величины, которую
документ не может держать истинной» от законного числа того же документа машине нечем.
Здесь предмет ДРУГОЙ: ДВА машинно читаемых поля (значение поля состояния шапки и число
заполненных строк таблиц отметок) и ОДНО объявленное между ними соответствие.
Суждения этот предмет не требует, поэтому D-33 настоящим модулем НЕ ПЕРЕОТКРЫВАЕТСЯ и
НЕ ОТМЕНЯЕТСЯ; документная половина по-прежнему судится человеком.

Разбор ведётся ПО ФОРМЕ СТРОКИ, а не по тексту шага: правка формулировки шага обхода
не имеет права ронять правило — хрупкое правило отключают вместе со свойством.
"""

import re
from dataclasses import dataclass
from pathlib import Path

TREE_ROOT = Path(__file__).resolve().parents[2]
RECORD_ROOT = TREE_ROOT / ".planning"
TEMPLATES_ROOT = TREE_ROOT / "app" / "templates"

# Образец имени артефакта ручного обхода. ⚠️ ОБРАЗЕЦ ШИРЕ, ЧЕМ `*-UAT.md`, И ЭТО
# ЗАМЕР, А НЕ ВОЛЬНОСТЬ: два артефакта вехи v2.0 названы `03-UAT-round-1.md` и
# `04-UAT-round-1.md` — узкий образец не нашёл бы их, дав 11 артефактов вместо 13.
# Обход, не видящий двух артефактов из тринадцати, судил бы меньше, чем объявил.
WALKTHROUGH_GLOB = "*UAT*.md"

# ПЕРЕЧЕНЬ литералов состояния, которыми артефакт обхода объявляет себя ЗАКРЫТЫМ.
# ⚠️ ПОЧЕМУ ПЕРЕЧЕНЬ, А НЕ ОДИН ЛИТЕРАЛ. Доминирующая в дереве форма объявления
# обхода закрытым — `complete` (11 артефактов из 13), а вовсе не `passed` (1 из 13).
# Правило, знающее одно слово `passed`, МОЛЧАЛО БЫ на одиннадцати артефактах, и
# артефакт, объявленный `complete` при пустых таблицах отметок, прошёл бы гейт
# беспрепятственно — то есть коммит класса `0ea886d` повторился бы при живом
# принуждении, которое здесь и заводится.
TERMINAL_WALKTHROUGH_STATES = frozenset({"complete", "passed"})

# ЛЕТОПИСЬ ЧИСЛА: 2. ОТКУДА ВЗЯЛОСЬ — ЗАМЕР ПО ДЕРЕВУ, а не память: обойдено 13
# артефактов по образцу `*UAT*.md` под каталогом записи, у каждого прочитано поле
# состояния ПЕРВОГО блока frontmatter; получено `complete` — 11, `passed` — 1,
# НЕтерминальное значение — 1 у одного артефакта (его имя в исходник не попадает по
# основанию, записанному в шапке файла). ЧЕМ ИЗМЕРЕНО — собственным обходом тем же
# приёмом, каким состояние читает `walkthrough_counts` ниже, а не счётом глазом.
# КАКИМ ПЛАНОМ — 10-20 (2026-09-07, четвёртая партия закрытия гейпов Фазы 10).
# ⚠️ СОСТОЯНИЕ, ПРИШЕДШЕЕ В ДЕРЕВО и не внесённое в перечень, краснит правило
# объявленных чисел ниже, а не проходит молча: иначе следующая эпоха артефактов
# вышла бы из-под правила НЕЗАМЕТНО.
# ⚠️ ЭТО ДРУГОЙ СЛОВАРЬ, ЧЕМ ВЕРДИКТЫ ОТЧЁТОВ ВЕРИФИКАЦИИ: он снят по артефактам
# обхода, а не по отчётам, и общих имён у двух словарей быть не обязано.
TERMINAL_STATES_DECLARED = 2

# ЛЕТОПИСЬ ЧИСЛА: 11. Число артефактов, ИЗЪЯТЫХ из вселенной несущего правила.
# ОСНОВАНИЕ ИЗЪЯТИЯ, названное честно: у артефакта без таблиц отметок отметок НЕТ
# ВОВСЕ, и утверждение «заполненных отметок не меньше числа таблиц» вырождается на
# нём в `0 >= 0`, то есть ЗЕЛЕНЕЕТ ВАКУУМОМ. Эти одиннадцать артефактов настоящим
# правилом НЕ СТЕРЕЖЁТСЯ, и это записано, а не оставлено умолчанию: они другой эпохи
# и другой формы (`## Current Test`, `## Tests` вместо разделов проверок и отметок).
# ЧЕМ ИЗМЕРЕНО — собственным обходом `walkthrough_sources()`; КАКИМ ПЛАНОМ — 10-20.
# ⚠️ ИЗЪЯТИЕ ЗАПЕРТО ЧИСЛОМ, ПОЭТОМУ ОНО НЕ УМЕЕТ РАСТИ МОЛЧА: артефакт, у которого
# таблицы отметок СНЯЛИ, увеличит число изъятых и покраснит прогон.
MARKED_FORM_EXEMPT_DECLARED = 11

# ЛЕТОПИСЬ ЧИСЛА: 12. Число артефактов, ИЗЪЯТЫХ из вселенной правила трёх счётов.
# ОСНОВАНИЕ ИЗЪЯТИЯ: сравнивать нечего — объявленного шапкой числа проверок у них
# нет вовсе. ⚠️ ОТДЕЛЬНО НАЗВАН АРТЕФАКТ ОБХОДА ФАЗЫ 9: он в терминальном состоянии,
# отметки его заполнены, форма отметок ТА ЖЕ — то есть в вселенную НЕСУЩЕГО правила
# он входит, — но объявленного числа проверок и разделов вида «Проверка N» у него
# НЕТ, и из правила трёх счётов он изъят. Оба факта записаны, а не подразумеваются.
# ЧЕМ ИЗМЕРЕНО — собственным обходом; КАКИМ ПЛАНОМ — 10-20.
# ⚠️ ПЕРЕЧИСЛЯТЬ ИЗЫМАЕМОЕ СПИСКОМ ПУТЕЙ ЗАПРЕЩЕНО: список путей не переживёт ни
# переезда артефакта в архив, ни появления нового, — а признак самого артефакта
# переживёт и то и другое.
DECLARED_COUNT_EXEMPT_DECLARED = 12

_FRONTMATTER_FENCE = "---"
_STATE_FIELD_RE = re.compile(r"^status:\s*(?P<value>[^\s#]+)\s*$")
_DECLARED_CHECKS_RE = re.compile(r"^checks_declared:\s*(?P<value>\d+)\s*$")
_CHECK_SECTION_RE = re.compile(r"^##\s+Проверка\s+\d+", re.M)
_MARK_HEADING_RE = re.compile(r"^###\s+Отметка\b")
_ANY_HEADING_RE = re.compile(r"^#{1,6}\s")
_RULE_LINE_RE = re.compile(r"^-{3,}\s*$")


@dataclass(frozen=True)
class WalkthroughCounts:
    """Величины артефакта обхода, снятые с ЕГО ИСХОДНИКА.

    `state` — значение поля состояния шапки либо `None`, если шапки нет вовсе.
    `declared_checks` — объявленное шапкой число проверок либо `None` — ПРИЗНАК
    «не объявлено», а не ноль: ноль означал бы «объявлено ноль проверок», и
    смешение этих двух вещей изъяло бы артефакт из правила молча.
    """

    state: str | None
    declared_checks: int | None
    check_sections: int
    mark_tables: int
    filled_marks: int

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_WALKTHROUGH_STATES


def _frontmatter_lines(text: str) -> list[str]:
    """Строки ПЕРВОГО блока frontmatter. Проза артефакта не читается вовсе."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_FENCE:
        return []
    block: list[str] = []
    for line in lines[1:]:
        if line.strip() == _FRONTMATTER_FENCE:
            break
        block.append(line)
    return block


def _mark_table_rows(lines: list[str], start: int) -> list[str]:
    """Строки ДАННЫХ первой таблицы, стоящей под подзаголовком отметки.

    Шапка и строка-разделитель отбрасываются по ПОЛОЖЕНИЮ (первая и вторая строки
    таблицы), а не по виду: разделитель, отличённый по виду, спутался бы с пустой
    строкой значений, которая тоже состоит из одних разделителей и пробелов.

    Поиск прекращается на следующем заголовке любого уровня и на горизонтальной
    черте: ниже них живёт уже другой раздел, и его таблицы отметкой не являются.
    """
    table: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not table and (_ANY_HEADING_RE.match(line) or _RULE_LINE_RE.match(stripped)):
            break
        if stripped.startswith("|"):
            table.append(stripped)
            continue
        if table:
            break
    return table[2:]


def _row_is_filled(row: str) -> bool:
    """Строка отметки ЗАПОЛНЕНА, если хоть одна её клетка несёт непробельное.

    Пустая строка значений состоит из разделителей и пробелов — именно так её и
    печатает артефакт, ожидающий человека на приёмке.
    """
    return any(cell.strip() for cell in row.strip("|").split("|"))


def walkthrough_counts(source: str) -> WalkthroughCounts:
    """Разборщик артефакта обхода. ИСХОДНИК ПРИХОДИТ ТЕКСТОМ, а не путём.

    Без параметра-исходника контроль зубов был бы невыразим, и зубы правила
    пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы их ПОКАЗЫВАТЬ, — идиома каталога,
    записанная у обоих соседних модулей по той же причине.
    """
    state: str | None = None
    declared: int | None = None
    for line in _frontmatter_lines(source):
        if state is None:
            field = _STATE_FIELD_RE.match(line)
            if field:
                state = field.group("value").strip("\"'")
        if declared is None:
            field = _DECLARED_CHECKS_RE.match(line)
            if field:
                declared = int(field.group("value"))

    lines = source.splitlines()
    mark_tables = 0
    filled = 0
    for index, line in enumerate(lines):
        if not _MARK_HEADING_RE.match(line):
            continue
        mark_tables += 1
        filled += sum(1 for row in _mark_table_rows(lines, index) if _row_is_filled(row))

    return WalkthroughCounts(
        state=state,
        declared_checks=declared,
        check_sections=len(_CHECK_SECTION_RE.findall(source)),
        mark_tables=mark_tables,
        filled_marks=filled,
    )


def walkthrough_sources() -> list[tuple[str, str]]:
    """Пары «путь, исходник» для ВСЕХ артефактов обхода дерева записи.

    Обход РЕКУРСИВНЫЙ по той же причине, по какой рекурсивен обход отчётов
    верификации у соседа: переезд артефакта в архив не имеет права молча выключить
    правило — обход, выродившийся в чтение одного каталога, зеленел бы от переезда.
    """
    return [
        (str(path.relative_to(TREE_ROOT)), path.read_text(encoding="utf-8"))
        for path in sorted(RECORD_ROOT.rglob(WALKTHROUGH_GLOB))
    ]


def marked_walkthroughs(
    sources: list[tuple[str, str]],
) -> list[tuple[str, WalkthroughCounts]]:
    """ВСЕЛЕННАЯ НЕСУЩЕГО ПРАВИЛА — артефакты, несущие хотя бы одну таблицу отметок.

    Отбор идёт ПО ПРИЗНАКУ САМОГО АРТЕФАКТА, а не по списку путей: признак
    переживает и переезд артефакта в архив, и появление нового, а список путей —
    это тот же «перечень того, до чего дошли руки».
    """
    return [
        (name, counts)
        for name, counts in ((name, walkthrough_counts(text)) for name, text in sources)
        if counts.mark_tables
    ]


def declared_count_walkthroughs(
    sources: list[tuple[str, str]],
) -> list[tuple[str, WalkthroughCounts]]:
    """ВСЕЛЕННАЯ ПРАВИЛА ТРЁХ СЧЁТОВ — артефакты, ОБЪЯВЛЯЮЩИЕ число проверок."""
    return [
        (name, counts)
        for name, counts in ((name, walkthrough_counts(text)) for name, text in sources)
        if counts.declared_checks is not None
    ]


@dataclass(frozen=True)
class SelfCertification:
    """Артефакт, объявивший себя закрытым шире собственных отметок."""

    path: str
    state: str
    mark_tables: int
    filled_marks: int

    def __str__(self) -> str:
        return (
            f"`{self.path}`: состояние `{self.state}` ТЕРМИНАЛЬНО (совпало с "
            f"элементом объявленного перечня), то есть артефакт объявил обход "
            f"закрытым, — а таблиц отметок у него {self.mark_tables} при "
            f"{self.filled_marks} заполненных. Правило записал сам артефакт: "
            f"отметка без наблюдённого признака закрытием не считается"
        )


def self_certifying_walkthroughs(
    sources: list[tuple[str, str]],
) -> list[SelfCertification]:
    """ВСЕ несогласные артефакты одним списком, а не первый.

    Артефакт в НЕтерминальном состоянии не судится о заполненности ВОВСЕ:
    непройденный обход с пустыми таблицами — штатное состояние дерева, а не дефект.
    """
    return [
        SelfCertification(
            path=name,
            state=counts.state or "",
            mark_tables=counts.mark_tables,
            filled_marks=counts.filled_marks,
        )
        for name, counts in marked_walkthroughs(sources)
        if counts.is_terminal and counts.filled_marks < counts.mark_tables
    ]


@dataclass(frozen=True)
class CountDisagreement:
    """Три счёта проверок одного артефакта, не сошедшиеся между собой."""

    path: str
    declared: int
    sections: int
    tables: int

    def __str__(self) -> str:
        return (
            f"`{self.path}`: шапка объявляет {self.declared} проверок, разделов "
            f"проверок {self.sections}, таблиц отметок {self.tables} — проверка "
            f"исчезла из обхода либо пришла в него, не объявившись"
        )


def check_count_disagreements(
    sources: list[tuple[str, str]],
) -> list[CountDisagreement]:
    """Артефакты, у которых три счёта проверок разошлись."""
    disagreements: list[CountDisagreement] = []
    for name, counts in declared_count_walkthroughs(sources):
        declared = counts.declared_checks
        assert declared is not None  # вселенная отобрана по этому же признаку
        if declared == counts.check_sections == counts.mark_tables:
            continue
        disagreements.append(
            CountDisagreement(
                path=name,
                declared=declared,
                sections=counts.check_sections,
                tables=counts.mark_tables,
            )
        )
    return disagreements


def _report(items) -> str:
    return "\n".join(str(item) for item in items)


# --- сами правила ------------------------------------------------------------------


def test_no_walkthrough_declares_itself_passed_with_empty_marks():
    """НЕСУЩЕЕ ПРАВИЛО: запись о прохождении не шире собственных отметок.

    ⚠️ СРАВНЕНИЕ ВЕДЁТСЯ С ЧИСЛОМ ТАБЛИЦ ОТМЕТОК, А НЕ С ОБЪЯВЛЕННЫМ ЧИСЛОМ
    ПРОВЕРОК, и основание записано: объявленное число несёт ОДИН артефакт дерева, а
    таблицы отметок — ОБА артефакта вселенной. Правило, опершееся на объявленное
    число, было бы неопределено на единственном сегодня артефакте, находящемся в
    терминальном состоянии, — то есть ровно на том, на котором обязано работать.
    """
    universe = marked_walkthroughs(walkthrough_sources())
    assert universe, (
        "артефактов с таблицами отметок не найдено ни одного — обход выродился, и "
        "правило зеленело бы ВАКУУМОМ"
    )

    found = self_certifying_walkthroughs(walkthrough_sources())
    assert not found, (
        "артефакты обхода, объявившие себя закрытыми шире собственных отметок:\n"
        + _report(found)
        + "\n\nЧТО ДЕЛАТЬ: либо обход ДЕЙСТВИТЕЛЬНО пройден и отметки заполняет "
        "ЧЕЛОВЕК наблюдёнными признаками, либо состояние шапки возвращается в "
        "нетерминальное. Заполнение отметок ради зелени правила есть самозаверение, "
        "а не приёмка"
    )


def test_the_number_of_walkthrough_checks_agrees_three_ways():
    """ТРИ СЧЁТА СХОДЯТСЯ ТАМ, ГДЕ ТРИ СЧЁТА ЕСТЬ.

    Без этого правила проверка исчезала бы из обхода МОЛЧА: несущее правило судит
    только те таблицы отметок, которые видит, и снятие раздела проверки вместе с
    его таблицей прошло бы незамеченным.
    """
    universe = declared_count_walkthroughs(walkthrough_sources())
    assert universe, (
        "артефактов, ОБЪЯВЛЯЮЩИХ число проверок, не найдено ни одного — правило "
        "зеленело бы ВАКУУМОМ ровно в тот момент, когда поле объявленного числа "
        "снимут отовсюду"
    )

    disagreements = check_count_disagreements(walkthrough_sources())
    assert not disagreements, _report(disagreements)


def test_the_declared_vocabularies_and_exemptions_agree():
    """ОДНО ПРАВИЛО, ТРИ РАВЕНСТВА: словарь состояний и два числа изъятий.

    ⚠️ ТРИ РАВЕНСТВА В ОДНОМ ПРАВИЛЕ, А НЕ В ТРЁХ: предмет у них ОДИН — объявленные
    числа настоящего модуля, — и разведение его на три имени завело бы ТРИ МЕСТА
    ОДНОЙ ЛЕТОПИСИ, то есть ровно тот класс расхождения, против которого написана
    вся партия.
    """
    assert len(TERMINAL_WALKTHROUGH_STATES) == TERMINAL_STATES_DECLARED, (
        f"терминальных состояний в перечне {len(TERMINAL_WALKTHROUGH_STATES)}, а "
        f"объявлено {TERMINAL_STATES_DECLARED}. Состояние, ПРИШЕДШЕЕ в дерево, "
        f"вносится в перечень ВМЕСТЕ С ЛЕТОПИСЬЮ — иначе следующая эпоха артефактов "
        f"выйдет из-под несущего правила НЕЗАМЕТНО"
    )

    sources = walkthrough_sources()

    marked_exempt = len(sources) - len(marked_walkthroughs(sources))
    assert marked_exempt == MARKED_FORM_EXEMPT_DECLARED, (
        f"из несущего правила изъято {marked_exempt} артефактов, а объявлено "
        f"{MARKED_FORM_EXEMPT_DECLARED}. ВЫРОСШЕЕ изъятие — это либо новый артефакт "
        f"другой эпохи (решение принимается ЯВНО и записывается летописью), либо "
        f"СНЯТЫЕ с артефакта таблицы отметок, то есть побег из-под правила. "
        f"ПОХУДЕВШЕЕ — форма таблиц разошлась с разборщиком"
    )

    declared_exempt = len(sources) - len(declared_count_walkthroughs(sources))
    assert declared_exempt == DECLARED_COUNT_EXEMPT_DECLARED, (
        f"из правила трёх счётов изъято {declared_exempt} артефактов, а объявлено "
        f"{DECLARED_COUNT_EXEMPT_DECLARED}. ВЫРОСШЕЕ изъятие означает СНЯТОЕ поле "
        f"объявленного числа проверок — побег из-под правила через удаление поля; "
        f"ПОХУДЕВШЕЕ — форма шапки разошлась с разборщиком"
    )


# --- зубы: синтетические исходники, а не правка артефактов дерева -------------------

# ⚠️ СИНТЕТИЧЕСКОЕ СОСТОЯНИЕ ВНЕ ПЕРЕЧНЯ — НЕ ИМЯ ИЗ ДЕРЕВА. Оно ЗАДАНО КОНТРОЛЕМ и
# его нетерминальность УТВЕРЖДАЕТСЯ ниже, а не предполагается: контроль, взявший
# сегодняшнее имя непройденного состояния из дерева, вшил бы состояние дерева ровно
# так, как это запрещено шапкой файла.
_SYNTHETIC_STATE_OUTSIDE_THE_LIST = "состояние-вне-перечня"


def _synthetic_walkthrough(state: str, marks: list[list[str]], *, tables: int) -> str:
    """Синтетический артефакт обхода: `tables` разделов проверок и их отметки.

    ФОРМА СНЯТА ЧТЕНИЕМ ЖИВЫХ АРТЕФАКТОВ, а не взята из памяти: ограда frontmatter,
    заголовок раздела вида «## Проверка N», подзаголовок «### Отметка о закрытии
    проверки N», шапка таблицы, строка-разделитель и строка значений. Иначе
    синтетика молча давала бы нули, и контроль зеленел бы ВАКУУМОМ.

    `marks` — по строке значений на каждую таблицу; пустой список внутри означает
    ПУСТУЮ строку отметки, то есть ту самую, которую печатает артефакт, ожидающий
    человека на приёмке.
    """
    lines = [
        _FRONTMATTER_FENCE,
        f"status: {state}",
        f"checks_declared: {len(marks)}",
        _FRONTMATTER_FENCE,
        "",
        "# Синтетический обход",
        "",
    ]
    for number in range(1, tables + 1):
        lines += [
            f"## Проверка {number} — синтетическая",
            "",
            "| # | Шаг | Ожидаемый наблюдаемый признак |",
            "|---|---|---|",
            f"| {number}.1 | синтетический шаг | синтетический признак |",
            "",
            f"### Отметка о закрытии проверки {number}",
            "",
            "*(заполняет человек на приёмке)*",
            "",
            "| Дата | Наблюдение | Исход |",
            "|---|---|---|",
        ]
        row = marks[number - 1] if number - 1 < len(marks) else []
        lines += ["| " + " | ".join(row) + " |" if row else "|  |  |  |", "", "---", ""]
    return "\n".join(lines)


_EMPTY_MARKS = [[], []]
_FILLED_MARKS = [
    ["2026-09-07", "наблюдено на стенде", "пройдено"],
    ["2026-09-07", "наблюдено на стенде", "пройдено"],
]


def test_control_a_walkthrough_claiming_passage_with_empty_marks_reddens():
    """ЗУБЫ НЕСУЩЕГО ПРАВИЛА — ТРЕМЯ ПОЛОВИНАМИ, НА СИНТЕТИКЕ.

    (а) ПО КАЖДОМУ элементу перечня терминальных состояний: артефакт, объявивший
    себя закрытым при пустых отметках, краснит правило. ⚠️ ИМЕННО «по каждому», а не
    по одному: доминирующая в дереве форма объявления обхода закрытым вошла бы в
    правило НЕПРОВЕРЕННОЙ, и блокер повторился бы в собственном контроле.

    (б) те же терминальные состояния при ЗАПОЛНЕННЫХ отметках — находок ноль.

    (в) НЕСУЩАЯ: состояние ВНЕ перечня при пустых отметках — находок ноль. Она и
    есть доказательство того, что правило зелено в ОБОИХ законных состояниях дерева,
    а не вшило одно из них.
    """
    assert TERMINAL_WALKTHROUGH_STATES, "перечень терминальных состояний пуст"

    # (а) КАЖДОЕ терминальное состояние при ПУСТЫХ отметках — нарушение найдено.
    for state in sorted(TERMINAL_WALKTHROUGH_STATES):
        source = _synthetic_walkthrough(state, _EMPTY_MARKS, tables=2)
        counts = walkthrough_counts(source)
        assert counts.state == state and counts.mark_tables == 2, (
            f"синтетика разобралась не так, как задана ({counts}) — контроль "
            f"зеленел бы ВАКУУМОМ"
        )

        found = self_certifying_walkthroughs([(f"синтетика-{state}.md", source)])
        assert len(found) == 1, _report(found)
        assert found[0].state == state, str(found[0])
        assert found[0].filled_marks == 0 and found[0].mark_tables == 2, str(found[0])
        assert state in str(found[0]), str(found[0])

    # (б) КАЖДОЕ терминальное состояние при ЗАПОЛНЕННЫХ отметках — находок ноль.
    for state in sorted(TERMINAL_WALKTHROUGH_STATES):
        source = _synthetic_walkthrough(state, _FILLED_MARKS, tables=2)
        counts = walkthrough_counts(source)
        assert counts.filled_marks == 2, (
            f"синтетика с заполненными отметками дала {counts.filled_marks} "
            f"заполненных строк вместо 2 — контроль проверял бы не то"
        )
        assert not self_certifying_walkthroughs([(f"синтетика-{state}.md", source)])

    # (в) СОСТОЯНИЕ ВНЕ ПЕРЕЧНЯ при ПУСТЫХ отметках — находок ноль.
    assert _SYNTHETIC_STATE_OUTSIDE_THE_LIST not in TERMINAL_WALKTHROUGH_STATES, (
        "синтетическое состояние половины (в) попало в перечень терминальных — "
        "половина проверяла бы ту же ветвь, что и половина (а)"
    )
    outside = _synthetic_walkthrough(
        _SYNTHETIC_STATE_OUTSIDE_THE_LIST, _EMPTY_MARKS, tables=2
    )
    assert walkthrough_counts(outside).filled_marks == 0
    assert not self_certifying_walkthroughs([("синтетика-вне-перечня.md", outside)]), (
        "правило судило о заполненности артефакт, НЕ объявивший себя закрытым, — "
        "значит оно вшило сегодняшнее состояние дерева и краснело бы от штатного "
        "продвижения проекта"
    )


def test_control_a_walkthrough_with_a_lost_mark_table_reddens_the_count():
    """ЗУБЫ ПРАВИЛА ТРЁХ СЧЁТОВ — ДВУМЯ ПОЛОВИНАМИ.

    (а) объявлено две проверки, разделов два, а таблица отметок ОДНА: правило
    краснеет и печатает все три числа.

    (б) артефакт БЕЗ объявленного числа проверок в вселенную НЕ ПОПАДАЕТ — находок
    ноль. Половина несущая: без неё изъятие было бы ОБЪЯВЛЕНО, но не ПОКАЗАНО
    работающим, и правило краснело бы на одиннадцати артефактах другой эпохи.
    """
    # (а) ТАБЛИЦА ОТМЕТКИ ПОТЕРЯНА — три счёта разошлись.
    lost = _synthetic_walkthrough("complete", _FILLED_MARKS, tables=2)
    lost = lost.replace("### Отметка о закрытии проверки 2\n", "### Прочее\n", 1)
    counts = walkthrough_counts(lost)
    assert counts.declared_checks == 2 and counts.check_sections == 2, str(counts)
    assert counts.mark_tables == 1, (
        f"синтетика с потерянной таблицей дала {counts.mark_tables} таблиц вместо "
        f"1 — контроль проверял бы не то"
    )

    disagreements = check_count_disagreements([("синтетика-счёт.md", lost)])
    assert len(disagreements) == 1, _report(disagreements)
    message = str(disagreements[0])
    assert "2" in message and "1" in message, message

    # (б) БЕЗ ОБЪЯВЛЕННОГО ЧИСЛА — изъятие работает, находок ноль.
    undeclared = "\n".join(
        line
        for line in lost.splitlines()
        if not _DECLARED_CHECKS_RE.match(line)
    )
    assert walkthrough_counts(undeclared).declared_checks is None, (
        "синтетика половины (б) сохранила объявленное число — изъятие осталось бы "
        "ОБЪЯВЛЕННЫМ, а не показанным работающим"
    )
    assert not declared_count_walkthroughs([("синтетика-без-числа.md", undeclared)])
    assert not check_count_disagreements([("синтетика-без-числа.md", undeclared)])


# --- якоря наблюдения: шаг обхода не ссылается на узел, которого в разметке нет -----
#
# ЗАЧЕМ ЭТО ЖИВЁТ В ОДНОМ МОДУЛЕ С ПРАВИЛАМИ ВЫШЕ. Предмет один — «обход обязан быть
# ПРОХОДИМЫМ»: артефакт, объявивший себя закрытым без отметок, и шаг, называющий
# несуществующий узел, суть две половины ОДНОГО отказа. Во втором случае человек на
# приёмке записывает отказ, которого нет, и ищет несуществующую причину, — обход
# обесценивается при первом же прохождении.
#
# ⚠️ ЧТО ЭТО ПРАВИЛО НЕ УТВЕРЖДАЕТ: оно говорит о ПРИСУТСТВИИ узла в шаблоне и ни
# одной строкой не утверждает, что рантайм разметки что-либо с этим узлом сделал.
# Разница между «узел в разметке есть» и «узел применён к документу» и есть предмет
# самого ручного обхода, машине недоступный.


@dataclass(frozen=True)
class Anchor:
    """Один якорь наблюдения: чем шаг обхода адресует узел и где узел живёт.

    ⚠️ ПОЛЕЙ ДВА ТАМ, ГДЕ МОГЛО БЫ БЫТЬ ОДНО, И ОСНОВАНИЕ ЗАПИСАНО. `selector` —
    как узел называет ШАГ ОБХОДА (то, что человек наберёт в консоли); `marker` —
    литеральная подстрока, которой узел присутствует В ШАБЛОНЕ. Свести их в одно
    нельзя: идентификаторы печатаются подстановкой (`id="sched-{{ s.id }}"`), и
    селектор консоли в исходнике шаблона не встречается ВООБЩЕ. Правило, искавшее бы
    селектор, краснело бы на работающей разметке — то есть на работе, а не на дефекте.

    `step` — ОСНОВАНИЕ записи: какой шаг обхода этот якорь читает или нажимает.
    Якорь без названного шага-читателя есть узел, добавленный в реестр «на будущее».
    """

    selector: str
    marker: str
    source: str
    step: str

    def __str__(self) -> str:
        return f"`{self.selector}` → {self.source} (шаг {self.step})"


# ⚠️ ЧТО В РЕЕСТР НЕ ЗАНОСИТСЯ — РЕШЕНИЕ, А НЕ НЕДОСМОТР. Признаки, НЕ ЯВЛЯЮЩИЕСЯ
# УЗЛАМИ, сюда не попадают: состояние корневого элемента (признак блокировки
# прокрутки, вычисленное значение переполнения), заголовки и коды состояния ответа
# (204, признак перехода), строки консоли, переменные окна документа и документы
# записи, читаемые проверкой 6 глазами. Реестр, смешавший узлы с признаками, стерёг
# бы ДВА РАЗНЫХ ПРЕДМЕТА ОДНИМ ЧИСЛОМ, и похудевший он не отличал бы снятый узел от
# снятого признака.
WALKTHROUGH_ANCHORS: tuple[Anchor, ...] = (
    Anchor('[role="dialog"]', 'role="dialog"', "components/modal.html", "1.1"),
    Anchor(
        '[id^="sched-del-"]', "sched-del-", "ads/includes/sched_card.html", "1.2"
    ),
    Anchor(
        "[data-sched-card]", "data-sched-card", "ads/includes/sched_card.html", "1.3"
    ),
    Anchor(
        "#sched-{N} — карточка расписания",
        'id="sched-{{ s.id }}"',
        "ads/includes/sched_card.html",
        "1.3",
    ),
    Anchor(
        "#sched-{N} — внеполосное снятие карточки",
        'id="sched-{{ schedule_id }}"',
        "ads/partials/sched_delete_response.html",
        "1.6",
    ),
    Anchor(
        "#sched-del-{N} — внеполосное снятие панели",
        'id="sched-del-{{ schedule_id }}"',
        "ads/partials/sched_delete_response.html",
        "1.6",
    ),
    Anchor("#sched-count — линейка счётчика", 'id="sched-count"', "ads/form.html", "1.8"),
    Anchor(
        "#sched-count — цель внеполосного включения",
        "innerHTML:#sched-count",
        "ads/partials/sched_delete_response.html",
        "1.8",
    ),
    Anchor(
        "#ad-del-{id} — панель удаления объявления",
        "ad-del-",
        "ads/form.html",
        "1.1",
    ),
    Anchor("#text — поле текста", "textarea_field(name='text'", "ads/form.html", "1.14"),
    Anchor("#text-counter", 'id="text-counter"', "ads/form.html", "1.14"),
    Anchor(".media-tile__remove", "media-tile__remove", "ads/form.html", "1.15"),
    Anchor("#file-input", 'id="file-input"', "ads/form.html", "1.15"),
    Anchor(
        ".modal__panel — сама панель подтверждения",
        "modal__panel",
        "components/modal.html",
        "2.4",
    ),
    Anchor(
        ".modal__overlay — оверлей панели",
        "modal__overlay",
        "components/modal.html",
        "3.3",
    ),
    Anchor(
        "кнопка «Отмена» панели", 'x-ref="cancel"', "components/modal.html", "3.4"
    ),
    Anchor(
        "кнопка подтверждения панели",
        'x-bind:disabled="sending"',
        "components/modal.html",
        "3.6",
    ),
    Anchor(
        ".form-busy — индикатор занятости",
        'class="form-busy"',
        "components/modal.html",
        "3.5",
    ),
    Anchor("#notice — площадка приземления фокуса", 'id="notice"', "includes/notice_area.html", "5.1"),
    Anchor("#notice-alert", 'id="notice-alert"', "includes/notice_area.html", "5.5"),
)

# ЛЕТОПИСЬ ЧИСЛА: 20. ОТКУДА ВЗЯЛОСЬ — ВЫПИСКА ИЗ ШАГОВ ВСЕХ ШЕСТИ ПРОВЕРОК обхода
# Фазы 10: выписан каждый узел, который шаг ЧИТАЕТ либо НАЖИМАЕТ, вместе с файлом,
# который артефакт сам называет источником. ЧЕМ ИЗМЕРЕНО — чтением шести проверок и
# проверкой КАЖДОГО якоря ЧТЕНИЕМ файла-источника (не найденных — ноль), а не
# памятью о шаге: якорь, вписанный по памяти, превратил бы правило в проверку самого
# себя. КАКИМ ПЛАНОМ — 10-20 (2026-09-07, четвёртая партия закрытия гейпов Фазы 10).
# ⚠️ МОЛЧА ПОХУДЕВШИЙ РЕЕСТР означает, что наблюдение сняли, не тронув обхода; молча
# выросший — что якорь добавили, не назвав шага, который его читает.
WALKTHROUGH_ANCHORS_DECLARED = 20

NO_SOURCE_FILE = "файла-источника нет в дереве"
NO_ANCHOR_IN_FILE = "якоря нет в файле-источнике"


@dataclass(frozen=True)
class MissingAnchor:
    """Один якорь, которого правило не нашло, и ЧЕМ именно не нашло."""

    anchor: Anchor
    reason: str

    def __str__(self) -> str:
        return f"{self.anchor}: {self.reason}"


def missing_anchors(anchors: tuple[Anchor, ...]) -> list[MissingAnchor]:
    """ВСЕ ненайденные якоря одним списком, а не первый.

    РЕЕСТР ПРИХОДИТ ПАРАМЕТРОМ по той же причине, по какой параметром приходит
    исходник артефакта у разборщика выше: без параметра контроль зубов был бы
    невыразим, и зубы правила пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы их ПОКАЗЫВАТЬ.

    Отсутствие ФАЙЛА и отсутствие ЯКОРЯ В ФАЙЛЕ названы РАЗНЫМИ основаниями:
    реестр, ссылающийся на несуществующий файл, стерёг бы ПУСТОТУ, и слитый отказ
    заставил бы следующего читателя разбирать, какое из двух событий случилось.
    """
    missing: list[MissingAnchor] = []
    for anchor in anchors:
        path = TEMPLATES_ROOT / anchor.source
        if not path.is_file():
            missing.append(MissingAnchor(anchor, NO_SOURCE_FILE))
            continue
        if anchor.marker not in path.read_text(encoding="utf-8"):
            missing.append(MissingAnchor(anchor, NO_ANCHOR_IN_FILE))
    return missing


def test_every_walkthrough_anchor_exists_in_its_source_template():
    """ШАГ ОБХОДА НЕ МОЖЕТ ССЫЛАТЬСЯ НА УЗЕЛ, КОТОРОГО В РАЗМЕТКЕ НЕТ."""
    assert WALKTHROUGH_ANCHORS, "реестр якорей пуст — правило зеленело бы ВАКУУМОМ"

    missing = missing_anchors(WALKTHROUGH_ANCHORS)
    assert not missing, (
        "якоря наблюдения обхода, которых в разметке нет:\n"
        + _report(missing)
        + "\n\n⚠️ ДВА СЛУЧАЯ РАЗЛИЧАЕТ ЧЕЛОВЕК, И ПРАВИЛО НЕ ПРЕДЛАГАЕТ ОДНОЙ "
        "ПОЧИНКИ: (1) шаг обхода ссылается НЕ ТУДА — правится ШАГ и запись реестра; "
        "(2) узел УШЁЛ ИЗ РАЗМЕТКИ — это РЕГРЕССИЯ ПРОДУКТА, и правится продукт. "
        "Дописать узел в шаблон РАДИ ЗЕЛЕНИ ПРАВИЛА нельзя: это подгонка кода под "
        "тест, зеркальная подгонке теста под код"
    )


def test_the_number_of_walkthrough_anchors_is_declared():
    """ЧИСЛО ЯКОРЕЙ ОБЪЯВЛЕНО: реестр не умеет худеть и расти молча."""
    assert len(WALKTHROUGH_ANCHORS) == WALKTHROUGH_ANCHORS_DECLARED, (
        f"якорей в реестре {len(WALKTHROUGH_ANCHORS)}, а объявлено "
        f"{WALKTHROUGH_ANCHORS_DECLARED}. ПОХУДЕВШИЙ реестр означает, что наблюдение "
        f"СНЯЛИ, не тронув обхода; ВЫРОСШИЙ — что якорь добавили, не назвав шага, "
        f"который его читает. Осознанная правка приводит ОБЪЯВЛЕННОЕ ЧИСЛО и "
        f"дописывает летопись"
    )


def test_control_a_missing_anchor_is_named_by_the_rule():
    """ЗУБЫ ПРАВИЛА ЯКОРЕЙ — ДВУМЯ ПОЛОВИНАМИ, НА КОПИИ РЕЕСТРА В ПАМЯТИ.

    (а) один якорь подменён на заведомо отсутствующий в его файле — правило находит
    РОВНО ЕГО и называет по имени; (б) непрáвленый реестр — находок ноль.

    Ни реестр модуля, ни файлы разметки при этом не правятся: подмена живёт в
    памяти, потому что предмет контроля обязан задаваться САМИМ контролем.
    """
    # (б) НЕПРÁВЛЕНЫЙ РЕЕСТР — находок ноль (положительная половина идёт первой:
    # без неё половина (а) не отличала бы работу правила от разборщика, находящего
    # нарушение ВСЕГДА).
    assert not missing_anchors(WALKTHROUGH_ANCHORS)

    # (а) ОДИН ЯКОРЬ ПОДМЕНЁН.
    victim = WALKTHROUGH_ANCHORS[0]
    absent = Anchor(
        selector="[data-заведомо-отсутствующий-якорь]",
        marker="data-заведомо-отсутствующий-якорь",
        source=victim.source,
        step=victim.step,
    )
    doctored = (absent,) + WALKTHROUGH_ANCHORS[1:]
    assert len(doctored) == len(WALKTHROUGH_ANCHORS), "копия реестра потеряла запись"

    missing = missing_anchors(doctored)
    assert len(missing) == 1, _report(missing)
    assert missing[0].anchor.selector == absent.selector, str(missing[0])
    assert missing[0].reason == NO_ANCHOR_IN_FILE, str(missing[0])
    message = str(missing[0])
    assert absent.selector in message and absent.source in message, message

    # (в) ГРАНИЦА ВТОРОГО ОСНОВАНИЯ: файла-источника нет вовсе — отказ говорит ДРУГОЕ.
    nowhere = Anchor(
        selector="[data-якорь-без-файла]",
        marker="data-якорь-без-файла",
        source="заведомо/несуществующий.html",
        step=victim.step,
    )
    absent_file = missing_anchors((nowhere,))
    assert len(absent_file) == 1, _report(absent_file)
    assert absent_file[0].reason == NO_SOURCE_FILE, str(absent_file[0])

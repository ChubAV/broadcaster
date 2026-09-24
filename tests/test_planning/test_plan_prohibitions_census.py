"""Перепись запретов планов вехи: ОДИН прибор, ОДНО число, БИЕКЦИЯ с реестром.

ЗАЧЕМ. Критерий 6 ROADMAP §Phase 15 — долг Фазы 10 (решение `chubav` 2026-09-14,
`phase-10-only`) — требует разрешить каждый запрет Фазы 10. Пока четыре сети над одним
набором планов давали четыре числа (374 / 76 / 57 / 38 на 57 планах Фазы 10), «разрешить
каждый» было работой с неопределённым перечнем, и её результат был неповторим. Прибор
определяет перечень. Настоящий модуль — его ПРИНУЖДАЮЩАЯ половина: он живёт в `tests/` и
потому входит в `just test`. Человеческая половина — `scripts/prohibitions_census.py` — в
`just test` не входит, и разборщик у двух половин ОДИН: модуль импортирует его из скрипта, а
не держит второй (15-RESEARCH.md §Alternatives Considered, «и то, и то»).

КАК СНИМАЕТСЯ ПЕРЕПИСЬ. Шапка каждого файла `.planning/phases/*/[0-9]*-PLAN.md` — текст между
первой и второй строкой-ограждением `---` — разбирается `yaml.safe_load`, и перепись есть
элементы БЛОКА `must_haves.prohibitions`. Соседние блоки той же шапки (`must_haves.truths`,
`must_haves.assumptions`) в перепись не входят, но их длины прибор возвращает ОТДЕЛЬНЫМИ
величинами: через них течёт наивная сеть по строке, и прибор обязан уметь предъявить слагаемые
своего расхождения с ней — это его защита от ловушки «число совпало ≠ сеть верна».

ТОЖДЕСТВО ЗАПРЕТА — ПУТЬ ФАЙЛА ПЛАНА ПЛЮС ПОРЯДКОВЫЙ ИНДЕКС ЭЛЕМЕНТА В БЛОКЕ. Ключ по ТЕКСТУ
формулировки не применяется нигде. Машинный довод, снятый разбором: уникальных формулировок
Фазы 10 — 314 из 321, пять повторяющихся формулировок покрывают 12 запретов, и ключ по тексту
схлопнул бы их в одну запись — решение о втором не принимал бы никто (идиома
`tests/test_templates/test_htmx_inventory.py:726-736`). Число уникальности, названное D-04 в
`15-CONTEXT.md`, воспроизвести не удалось ни одной из пяти нормализаций (15-RESEARCH.md
§Assumptions Log A5), и в этот модуль как измеренное оно не переносится.

ЛЕТОПИСЬ ФОРМУЛИРОВКИ D-01 (решение владельца `chubav` 2026-09-23, 15-RESEARCH.md §Open
Questions #5: «исполнить по смыслу + летопись»). Буква D-01 требовала от прибора «знать обе
формы записи элемента запрета: `- statement:` и `- requirement_id:`». Замер Ф-01 уточнил
посылку: второй ФОРМЫ записи в дереве нет — все элементы блока суть словари с ключом
`statement`, а 24 элемента Фазы 08 несут `requirement_id` ВДОБАВОК, и отличается у них только
порядок ключей в YAML, из-за которого дефис списка приходится на `requirement_id`. Посылка
решения («две формы записи») уточнена до «дефис списка на другом ключе»; ВЫВОД решения («сеть,
знающая одну форму, молча теряет другую») верен и исполняется — прибор ключует по БЛОКУ, а не по
строке, и потому порядку ключей безразличен. Прибор, написанный по букве, дал бы 745 + 24 = 769
и стал бы ПЯТОЙ сетью с пятым числом. ⚠️ ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей
записи он был верным, и правится не он, а числа, которые он пережил. Текст D-01 в
`15-CONTEXT.md` не правится и не вычёркивается; поправка живёт здесь, рядом с исполнением.

ЛЕТОПИСЬ ЧИСЛА ВЕХИ: 650 → 697. 650 — веха без планов Фазы 15, замер 2026-09-23 на 142 файлах
планов, воспроизведён дважды независимо (разведка Ф-02 и планирование), 0 отказов разбора. 697 —
веха с планами Фазы 15, снято прибором 2026-09-24 на 156 файлах, 0 отказов разбора. Причина
роста названа, а не сглажена: планы Фазы 15 сами несут блоки `must_haves.prohibitions` (47
элементов в 14 планах) и потому входят в область прибора ПО ПОСТРОЕНИЮ. ⚠️ 650 НЕ БЫЛО
ОШИБКОЙ — оно устарело внутри собственной фазы, и это ровно тот класс «число пережило свой
прогноз», ради прекращения которого фаза заведена. Прежнее число не вычеркнуто: оно
воспроизводится ПРАВИЛОМ над подмножеством без планов Фазы 15 и стоит литералом
`PROHIBITIONS_BEFORE_PHASE_15_PLANS`. Область решений D-02 — Фаза 10, 321 — от роста не
меняется и объявлена отдельной величиной `PROHIBITIONS_IN_DECISION_SCOPE`.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16). Зелёный цвет означает ровно одно: перепись воспроизводима,
её число равно объявленному, и она БИЕКТИВНА реестру
`.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml`. Он НЕ
означает, что хоть один запрет СОБЛЮДЁН: разрешение не есть соблюдение, и образец
`10-PROHIBITIONS-SUBJECT.md` говорит это прямо полем `prohibitions_fully_enforced: 0`. Он НЕ
означает правильности классификации: гейт утверждает ПОЛНОТУ реестра и принадлежность
диспозиции объявленному перечню, а не верность класса. И он не судит вердикт отчёта своей фазы.
D-06, ОБЕ ПОЛОВИНЫ: этот модуль — ПЕРВЫЙ в проекте читатель блока `must_haves.prohibitions`
(до него, по замеру 2026-09-23, принуждения в дереве ноль); а два вхождения слова
`prohibition` в `tests/test_pages/test_impersonation_gate.py` за принуждение запретов планов НЕ
ИДУТ — это сторож подстановки личности, другой предмет, — и попасть в счёт даже случайно они не
могут: вселенная прибора есть блок шапки файла плана, а не текст исходника теста. Оговорка
стоит ЗДЕСЬ потому, что тот же файл этот план читает как идиому `ast`-разбора («по дереву, а не
по строке», `:462`, `:628-632`), и следующий счёт, увидевший его в области зрения фазы, мог бы
объявить два принуждения там, где их ноль, — то есть повторить «зелено вакуумом» на самом
приборе.

⚠️ ЛИТЕРАЛА СЕГОДНЯШНЕГО НЕЗАКРЫТОГО СОСТОЯНИЯ ЗДЕСЬ НЕТ ВОВСЕ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ. Правило,
знающее, сколько запретов сегодня не разобрано, зеленело бы ровно при условии, что фаза не
достигла цели, — дословно тот блокер, который четвёртый круг верификации нашёл у соседнего
модуля каталога (`test_planning_gates_are_independent_of_the_live_verdict.py:10-16`). Диспозиция
каждой строки судится ПРИНАДЛЕЖНОСТЬЮ объявленному перечню `DISPOSITIONS`, а распределение
диспозиций ДОКЛАДЫВАЕТСЯ в сообщении об отказе и не входит ни в одно утверждение.

ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. Решение D-33 отказало машинному гейту на ПРОЗЕ операционного
документа с названной причиной: отличить «константу величины, которую документ не может держать
истинной» от законного числа того же документа машине нечем. Здесь предмет ДРУГОЙ: машинно
читаемые ПОЛЯ — элементы блока шапки и строки реестра — и объявленное между ними соответствие.
Суждения этот предмет не требует, поэтому D-33 настоящим модулем НЕ ПЕРЕОТКРЫВАЕТСЯ и НЕ
ОТМЕНЯЕТСЯ; документная половина прохибиций по-прежнему судится человеком.

ГРАНИЦА: ПЕРЕЕЗД В АРХИВ. Вселенная прибора — `.planning/phases/`. Закрытие вехи переносит
каталоги фаз в архив, и тогда правила ниже покраснеют пустой вселенной, а не позеленеют молча:
контроль пустоты это доказывает. Переезд области прибора — решение того, кто закрывает веху, и
делается он вместе с реестром, а не сужением сети.

ЗАВИСИМОСТЬ. `import yaml` голый, по прецеденту `test_state_progress_matches_roadmap.py`:
PyYAML 6.0.3 закреплён в `uv.lock` и приходит транзитивно через объявленную
`uvicorn[standard]>=0.41.0`. Риск назван строкой, а не закрыт правкой `pyproject.toml` (рамка
вехи «0 новых Python-зависимостей», допущение A4 разведки): смена экстры `uvicorn` унесёт PyYAML
и уронит прибор отказом импорта — громко, а не молча.
"""

import ast
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

from scripts import prohibitions_census as tool

# Предмет модуля — ЗАПИСЬ проекта, а не его продукт. Основание маркера, его
# граница годности и запрет выключать каталог — `tests/test_planning/__init__.py`;
# само имя объявлено хуком в `tests/conftest.py`.
pytestmark = pytest.mark.planning

TREE_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = TREE_ROOT / tool.REGISTRY_RELATIVE_PATH

# ЛЕТОПИСЬ ЧИСЕЛ. Перечни и числа ниже выписаны ЗДЕСЬ, а не выведены из проверяемого
# источника в момент прогона: тест, считающий ожидание по коду в момент прогона,
# согласится с любой правкой и молча переживёт исчезновение элемента — ровно тот отказ,
# ради которого инвентарные гейты в проекте и заведены (прецедент формулировки —
# `tests/test_templates/test_htmx_inventory.py:63-67`).

# Число вехи С планами Фазы 15. Снято прибором 2026-09-24 на 156 файлах планов (летопись
# 650 → 697 — в шапке модуля). ⚠️ ИМЯ НАЗЫВАЕТ ФАЗУ, В КОТОРОЙ ЧИСЛО СНЯТО: поднять его можно
# только переписав величину, чьё имя утверждает, чему она была равна в Фазе 15, — то есть
# солгать в опознаваемом месте. Второй носитель того же числа — `rows_declared` в шапке
# реестра; перегенерация реестра в другой размер краснит модуль.
PROHIBITIONS_DECLARED_AT_PHASE_15 = 697

# Разбивка по фазам — тем же замером. Фазы 07…14 — числа 2026-09-23 (разведка Ф-02),
# воспроизведённые прибором; Фаза 15 — 47 элементов в 14 планах, снято 2026-09-24.
PROHIBITIONS_BY_PHASE_DECLARED = {
    "07": 31,
    "08": 24,
    "09": 153,
    "10": 321,
    "11": 68,
    "12": 22,
    "13": 8,
    "14": 23,
    "15": 47,
}

# Замер 2026-09-23 — веха БЕЗ планов Фазы 15: 142 файла, 650 элементов, 0 отказов разбора.
# Не вычеркнут, а воспроизводится правилом над подмножеством без каталога Фазы 15.
PROHIBITIONS_BEFORE_PHASE_15_PLANS = 650
PLAN_FILES_BEFORE_PHASE_15 = 142
PHASE_15 = "15"

# Область РЕШЕНИЙ по D-02 — Фаза 10. Это не число вехи и от роста вехи не меняется.
PROHIBITIONS_IN_DECISION_SCOPE = 321
DECISION_SCOPE_PHASE = "10"

# Разложение наивной сети по строке `- statement:` до единицы (15-RESEARCH.md Ф-01), замер
# 2026-09-23 на 142 планах: 650 − 24 + 102 + 17 = 745.
NAIVE_LINE_NET_DECLARED = 745
TRUTHS_DECLARED = 102
ASSUMPTIONS_DECLARED = 17
PHASE_08_KEY_ORDER_ELEMENTS = 24

# То же разложение С планами Фазы 15, снято прибором 2026-09-24: 697 − 24 + 119 + 17 = 809.
# Рост слагаемого `truths` (102 → 119) — 17 элементов-словарей `must_haves.truths` планов
# Фазы 15; `assumptions` и дефис на чужом ключе планами Фазы 15 не пополнились.
NAIVE_LINE_NET_AT_PHASE_15 = 809
TRUTHS_AT_PHASE_15 = 119

# Контроль от вакуума, положительный: вселенная обхода на неизменённом дереве непуста.
PLAN_FILES_FLOOR = 100

# ПЕРЕЧЕНЬ ДИСПОЗИЦИЙ СТРОКИ РЕЕСТРА. ⚠️ ПЕРЕЧЕНЬ, А НЕ ОДИН ЛИТЕРАЛ: нетерминальность строки
# выражается отрицанием принадлежности, а не именем сегодняшнего состояния (форма
# `TERMINAL_WALKTHROUGH_STATES` / `TERMINAL_STATES_DECLARED`). Состав объявлен по 15-RESEARCH.md
# Ф-03 и окончательным НЕ является: четвёртое значение («принуждается частично», доминирующее в
# образце `10-PROHIBITIONS-SUBJECT.md:120-137`) вводит план 15-12 вместе со схемой диспозиций, и
# тогда же поднимается число ниже. Объявить значение в перечне не значит записать его в строку:
# ни одной строке этот план диспозиции, кроме засеянной, не пишет.
DISPOSITIONS = frozenset({"enforced", "permitted", "unresolved"})
DISPOSITIONS_DECLARED = 3

# ПЕРЕЧЕНЬ ПОЛЕЙ СТРОКИ РЕЕСТРА. ⚠️ Полей `permit_*` и любого поля вердикта здесь НЕТ
# НАМЕРЕННО: их заводит ответ владельца на чекпойнте плана 15-12, а записывает по классам план
# 15-13; исполнитель, поставивший такое поле сам, вынес бы вердикт вместо владельца. Поле,
# пришедшее в реестр, вносится сюда ВМЕСТЕ С ЛЕТОПИСЬЮ — иначе оно войдёт в реестр незаметно.
#
# ЛЕТОПИСЬ ЧИСЛА: 7 → 8, план 15-01, задача 2 — пришло поле `declared_rule` (группа D-05 ниже).
# Оно есть ОБЪЯВЛЕНИЕ, снятое засевом с формулировки запрета, а не вердикт: имя правила, которое
# назвал автор запрета, либо признак «имя не объявлено».
REGISTRY_ROW_FIELDS = frozenset(
    {
        "plan",
        "index",
        "phase",
        "verification",
        "statement_digest",
        "class",
        "disposition",
        "declared_rule",
    }
)
REGISTRY_ROW_FIELDS_DECLARED = 8

# --- группа D-05: объявленные числа поля `verification` Фазы 10 ----------------------------
# Замер 2026-09-23 (15-CONTEXT.md D-05, воспроизведён разведкой Ф-02), воспроизведён прибором
# 2026-09-24: у всех 321 запрета Фазы 10 `status: flagged-unverified`; `verification: test` —
# 61, `verification: none` — 199, ключа нет — 61. Три значения поля суммируются к области
# решений: это ВТОРОЙ НЕЗАВИСИМЫЙ счёт того же множества, и расхождение читается как ошибка
# разбора, а не как пропажа запрета.
PHASE_10_VERIFICATION_TEST = 61
PHASE_10_VERIFICATION_NONE = 199
PHASE_10_VERIFICATION_ABSENT = 61
PHASE_10_STATUS_FLAGGED_UNVERIFIED = 321
VERIFICATION_TEST = "test"
VERIFICATION_NONE = "none"
STATUS_FLAGGED_UNVERIFIED = "flagged-unverified"

# Контроль от вакуума, положительный: вселенная имён функций суиты непуста. Замер 2026-09-24:
# 190 модулей `tests/**/*.py`, 4225 имён функций.
SUITE_FUNCTION_NAMES_FLOOR = 1000
SUITE_ROOT = TREE_ROOT / "tests"

# Синтетика контролей. Путь лежит в фазе, которой в дереве нет, чтобы подмена словаря
# исходников не могла совпасть с живым файлом.
SYNTHETIC_PLAN = ".planning/phases/99-synthetic/99-01-PLAN.md"
SYNTHETIC_PLAN_SOURCE = """---
phase: 99-synthetic
plan: 01
must_haves:
  truths:
    - statement: "истина синтетического плана"
      verification: test
  prohibitions:
    - statement: "MUST NOT синтетический запрет, которого нет в реестре"
      status: flagged-unverified
---

Тело синтетического плана: `- statement:` в прозе в перепись не входит.
"""


# --- правила-помощники: чистые функции над поданными величинами -----------------------


def count_offence(records, declared: int) -> str:
    """Пустая строка, если число записей переписи равно объявленному."""
    if len(records) == declared:
        return ""
    return (
        f"перепись дала {len(records)} элементов блока `must_haves.prohibitions`, "
        f"объявлено {declared}; разбивка по фазам: {tool.phase_breakdown(records)}. "
        f"Число двигается ЗАМЕРОМ, а не переопределением прибора: перезасейте реестр "
        f"(`scripts/prohibitions_census.py --seed-registry`) и поднимите литерал ВМЕСТЕ С "
        f"ЛЕТОПИСЬЮ, назвав, чем и когда заменено прежнее число"
    )


def bijection_offences(census_ids, registry_ids):
    """Пара списков: сироты переписи (нет в реестре) и лишние строки реестра."""
    census_set, registry_set = set(census_ids), set(registry_ids)
    return sorted(census_set - registry_set), sorted(registry_set - census_set)


def disposition_distribution(rows) -> str:
    """Распределение диспозиций — ДОКЛАДЫВАЕТСЯ в отказе, в утверждения не входит."""
    counts = Counter(str(row.get("disposition")) for row in rows)
    return ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))


def disposition_offences(rows) -> list[str]:
    """Строки реестра, чья диспозиция НЕ принадлежит объявленному перечню."""
    return [
        f"{row.get('plan')}#{row.get('index')}: диспозиция `{row.get('disposition')}`"
        for row in rows
        if row.get("disposition") not in DISPOSITIONS
    ]


def _before_phase_15(sources):
    return {path: text for path, text in sources.items() if tool.phase_of(path) != PHASE_15}


def _names(identities) -> str:
    return "\n".join(f"  {identity.plan_path}#{identity.index}" for identity in identities)


@pytest.fixture(scope="module")
def live_sources():
    return tool._plan_sources(TREE_ROOT)


@pytest.fixture(scope="module")
def live_census(live_sources):
    return tool.census(live_sources)


@pytest.fixture(scope="module")
def registry_document():
    return tool.load_registry(REGISTRY_FILE)


# --- перепись ----------------------------------------------------------------------


def test_the_census_of_the_milestone_matches_the_declared_number(live_census):
    """СКВОЗНОЕ ПРАВИЛО: шапки планов вехи → одно объявленное число и одна разбивка."""
    offence = count_offence(live_census, PROHIBITIONS_DECLARED_AT_PHASE_15)
    assert not offence, offence
    assert tool.phase_breakdown(live_census) == PROHIBITIONS_BY_PHASE_DECLARED


def test_the_census_reproduces_the_measurement_taken_before_phase_15_plans(live_sources):
    """Замер 2026-09-23 не вычеркнут: подмножество без планов Фазы 15 даёт 650 на 142."""
    before = _before_phase_15(live_sources)
    assert len(before) == PLAN_FILES_BEFORE_PHASE_15, sorted(before)
    records = tool.census(before)
    offence = count_offence(records, PROHIBITIONS_BEFORE_PHASE_15_PLANS)
    assert not offence, offence
    expected = {
        phase: count
        for phase, count in PROHIBITIONS_BY_PHASE_DECLARED.items()
        if phase != PHASE_15
    }
    assert tool.phase_breakdown(records) == expected


def test_the_decision_scope_of_phase_10_is_declared_apart_from_the_milestone(live_census):
    """Область решений D-02 — отдельная величина, а не число вехи."""
    in_scope = [record for record in live_census if record.phase == DECISION_SCOPE_PHASE]
    assert len(in_scope) == PROHIBITIONS_IN_DECISION_SCOPE, tool.phase_breakdown(live_census)
    assert PROHIBITIONS_IN_DECISION_SCOPE < PROHIBITIONS_DECLARED_AT_PHASE_15


def test_the_census_parses_every_plan_without_refusal(live_sources):
    """0 отказов разбора на живом дереве — и отказ, поданный синтетикой, НАЗЫВАЕТСЯ."""
    assert tool.parse_failures(live_sources) == []

    broken = dict(live_sources)
    broken[SYNTHETIC_PLAN] = "---\nmust_haves: [незакрытая скобка\n---\n"
    failures = tool.parse_failures(broken)
    assert len(failures) == 1 and SYNTHETIC_PLAN in failures[0], failures
    with pytest.raises(tool.CensusError, match="99-01-PLAN.md"):
        tool.census(broken)


def test_identity_is_the_plan_path_and_the_index_not_the_statement_text(live_census):
    """Две посимвольно равные формулировки одного блока — ДВА тождества, а не одно."""
    twin = """---
must_haves:
  prohibitions:
    - statement: "MUST NOT одна и та же формулировка"
    - statement: "MUST NOT одна и та же формулировка"
---
"""
    records = tool.census({SYNTHETIC_PLAN: twin})
    assert [record.identity for record in records] == [
        tool.ProhibitionIdentity(SYNTHETIC_PLAN, 0),
        tool.ProhibitionIdentity(SYNTHETIC_PLAN, 1),
    ]
    assert records[0].statement == records[1].statement

    identities = [record.identity for record in live_census]
    assert len(set(identities)) == len(identities)


def test_the_order_of_keys_in_an_element_does_not_move_the_count(live_census):
    """Дефис списка на `requirement_id` (Фаза 08) — такой же элемент блока, как прочие."""
    reordered = """---
must_haves:
  prohibitions:
    - requirement_id: SYN-01
      statement: "MUST NOT синтетика с дефисом на чужом ключе"
    - statement: "MUST NOT синтетика с дефисом на формулировке"
      requirement_id: SYN-02
---
"""
    records = tool.census({SYNTHETIC_PLAN: reordered})
    assert len(records) == 2
    assert [record.first_key for record in records] == ["requirement_id", "statement"]

    elsewhere = [record for record in live_census if record.first_key != "statement"]
    assert len(elsewhere) == PHASE_08_KEY_ORDER_ELEMENTS
    assert {record.phase for record in elsewhere} == {"08"}


def test_truths_and_assumptions_are_counted_apart_from_prohibitions():
    """Соседние блоки в перепись НЕ входят, но их длины предъявляются отдельно."""
    records = tool.census({SYNTHETIC_PLAN: SYNTHETIC_PLAN_SOURCE})
    assert len(records) == 1
    assert records[0].statement.startswith("MUST NOT синтетический")

    parts = tool.decomposition({SYNTHETIC_PLAN: SYNTHETIC_PLAN_SOURCE})
    assert (parts.prohibitions, parts.truths, parts.assumptions) == (1, 1, 0)


def test_the_naive_line_net_decomposes_to_the_unit_before_phase_15_plans(live_sources):
    """650 − 24 + 102 + 17 = 745: КАЖДОЕ слагаемое — отдельная величина прибора.

    Равенство суммы сети — сверка ДВУХ величин, снятых РАЗНЫМИ путями из одного источника
    (разбор блока против счёта строк); расхождение читается как ошибка разбора, а не как
    пропажа запрета. Целочисленная перепись округления не имеет — это её аналог точности.
    """
    parts = tool.decomposition(_before_phase_15(live_sources))
    assert parts.reconstructed == parts.line_net, parts
    assert (
        parts.prohibitions,
        parts.first_key_elsewhere,
        parts.truths,
        parts.assumptions,
        parts.line_net,
    ) == (
        PROHIBITIONS_BEFORE_PHASE_15_PLANS,
        PHASE_08_KEY_ORDER_ELEMENTS,
        TRUTHS_DECLARED,
        ASSUMPTIONS_DECLARED,
        NAIVE_LINE_NET_DECLARED,
    )


def test_the_naive_line_net_decomposes_to_the_unit_with_phase_15_plans(live_sources):
    """697 − 24 + 119 + 17 = 809: то же разложение на вселенной прибора целиком."""
    parts = tool.decomposition(live_sources)
    assert parts.reconstructed == parts.line_net, parts
    assert (
        parts.prohibitions,
        parts.first_key_elsewhere,
        parts.truths,
        parts.assumptions,
        parts.line_net,
    ) == (
        PROHIBITIONS_DECLARED_AT_PHASE_15,
        PHASE_08_KEY_ORDER_ELEMENTS,
        TRUTHS_AT_PHASE_15,
        ASSUMPTIONS_DECLARED,
        NAIVE_LINE_NET_AT_PHASE_15,
    )


def test_the_order_of_sources_does_not_move_the_identities(live_sources, live_census):
    """Порядок подачи исходников не несущий: сравниваются МНОЖЕСТВА тождеств."""
    reversed_sources = dict(reversed(list(live_sources.items())))
    again = tool.census(reversed_sources)
    assert {record.identity for record in again} == {
        record.identity for record in live_census
    }
    assert sorted(again, key=lambda record: record.identity) == sorted(
        live_census, key=lambda record: record.identity
    )


# --- реестр ------------------------------------------------------------------------


def test_the_census_and_the_registry_are_a_bijection(live_census, registry_document):
    """Ни сироты в переписи, ни лишней строки в реестре."""
    registry = tool._registry_rows(registry_document)
    orphans, extras = bijection_offences(
        [record.identity for record in live_census], registry
    )
    assert not orphans and not extras, (
        f"запреты переписи без строки реестра ({len(orphans)}):\n{_names(orphans)}\n"
        f"строки реестра без запрета в переписи ({len(extras)}):\n{_names(extras)}\n"
        f"распределение диспозиций реестра: "
        f"{disposition_distribution(registry_document['rows'])}"
    )


def test_the_registry_declares_its_own_length(registry_document):
    """Два носителя одного числа: шапка реестра и литерал этого модуля."""
    rows = registry_document["rows"]
    assert registry_document["rows_declared"] == len(rows)
    assert len(rows) == PROHIBITIONS_DECLARED_AT_PHASE_15, (
        f"строк реестра {len(rows)}, объявлено {PROHIBITIONS_DECLARED_AT_PHASE_15} — "
        f"реестр перегенерирован в другой размер"
    )


def test_every_registry_row_agrees_with_its_census_element(live_census, registry_document):
    """Фаза, дескриптор проверки и отпечаток формулировки строки — те же, что у элемента.

    Отпечаток служит ОБНАРУЖЕНИЮ ПРАВКИ текста запрета, а не ключеванию: правка формулировки
    в исполненном плане краснит здесь, а не проходит молча.
    """
    registry = tool._registry_rows(registry_document)
    disagreements = []
    for record in live_census:
        row = registry.get(record.identity)
        if row is None:
            continue  # сирота — предмет правила биекции, а не этого
        expected = tool.registry_row(record)
        for field in ("phase", "verification", "statement_digest"):
            if row.get(field) != expected.get(field):
                disagreements.append(
                    f"{record.identity.plan_path}#{record.identity.index}: поле `{field}` "
                    f"в реестре `{row.get(field)}`, в переписи `{expected.get(field)}`"
                )
    assert not disagreements, "\n".join(disagreements)


def test_every_registry_row_carries_only_declared_fields(registry_document):
    """Поле строки принадлежит объявленному перечню; поле вне перечня называется."""
    strays = sorted(
        {field for row in registry_document["rows"] for field in row}
        - REGISTRY_ROW_FIELDS
    )
    assert not strays, f"поля строк реестра вне объявленного перечня: {strays}"


def test_every_disposition_belongs_to_the_declared_vocabulary(registry_document):
    """ПРИНАДЛЕЖНОСТЬ, а не значение: числа неразобранных это правило не знает."""
    rows = registry_document["rows"]
    offences = disposition_offences(rows)
    assert not offences, (
        "диспозиции вне объявленного перечня:\n"
        + "\n".join(offences)
        + f"\n\nраспределение диспозиций реестра: {disposition_distribution(rows)}"
    )


def test_the_declared_vocabularies_and_numbers_agree():
    """Объявленные перечни и числа модуля согласны между собой."""
    assert len(DISPOSITIONS) == DISPOSITIONS_DECLARED, sorted(DISPOSITIONS)
    assert len(REGISTRY_ROW_FIELDS) == REGISTRY_ROW_FIELDS_DECLARED, sorted(REGISTRY_ROW_FIELDS)
    assert sum(PROHIBITIONS_BY_PHASE_DECLARED.values()) == PROHIBITIONS_DECLARED_AT_PHASE_15
    assert (
        PROHIBITIONS_DECLARED_AT_PHASE_15 - PROHIBITIONS_BY_PHASE_DECLARED[PHASE_15]
        == PROHIBITIONS_BEFORE_PHASE_15_PLANS
    )


# --- зубы: подмена словаря исходников, а не правка дерева -------------------------------


def test_control_positive_the_universe_of_plans_is_not_empty(live_sources):
    """На НЕИЗМЕНЁННОМ дереве вселенная обхода непуста — правило не зеленеет вакуумом."""
    assert len(live_sources) > PLAN_FILES_FLOOR, len(live_sources)


def test_control_negative_a_synthetic_prohibition_is_found_and_named(
    live_sources, registry_document
):
    """Синтетический ключ с одним новым запретом: перепись его НАХОДИТ и НАЗЫВАЕТ."""
    doctored = dict(live_sources)
    doctored[SYNTHETIC_PLAN] = SYNTHETIC_PLAN_SOURCE
    records = tool.census(doctored)

    offence = count_offence(records, PROHIBITIONS_DECLARED_AT_PHASE_15)
    assert offence, "равенство объявленному числу не покраснело на лишнем запрете"
    assert f"{PROHIBITIONS_DECLARED_AT_PHASE_15 + 1} элементов" in offence, offence

    orphans, extras = bijection_offences(
        [record.identity for record in records], tool._registry_rows(registry_document)
    )
    assert orphans == [tool.ProhibitionIdentity(SYNTHETIC_PLAN, 0)], _names(orphans)
    assert not extras, _names(extras)


def test_control_empty_universe_reddens_the_declared_number(registry_document):
    """Пустая вселенная КРАСНИТ утверждение о ненулевом числе и не роняет прогон."""
    records = tool.census({})
    assert records == []
    assert count_offence(records, PROHIBITIONS_DECLARED_AT_PHASE_15)

    parts = tool.decomposition({})
    assert (parts.prohibitions, parts.line_net, parts.reconstructed) == (0, 0, 0)

    orphans, extras = bijection_offences([], tool._registry_rows(registry_document))
    assert not orphans
    assert len(extras) == PROHIBITIONS_DECLARED_AT_PHASE_15


# --- группа D-05: у запрета с `verification: test` предъявляется СУЩЕСТВОВАНИЕ правила -----
#
# ПРЕДМЕТ ГРУППЫ — СУЩЕСТВОВАНИЕ ОБЪЯВЛЕННОГО ПРАВИЛА, а не человеческое разрешение
# (15-CONTEXT.md D-05): объявление о тесте, которого нет, есть ровно тот класс «зелено
# вакуумом», от которого фаза защищается. Измеренный экземпляр класса — `test_no_manual_fetch_remains`,
# объявленный в GATE-08 и в дереве отсутствующий (15-RESEARCH.md Ф-06).


def _suite_sources(root: Path) -> dict[str, str]:
    """Отображение «путь модуля суиты → исходник» по `sorted(rglob)`."""
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.py"))
    }


def _suite_function_names(sources) -> frozenset[str]:
    """Имена `ast.FunctionDef` и `ast.AsyncFunctionDef` поданных исходников — по ДЕРЕВУ.

    Довод «по дереву, а не по строке» — `tests/test_pages/test_impersonation_gate.py:462`,
    `:628-632`: поиск по тексту нашёл бы имя и в комментарии, и в докстринге, и в
    закомментированном коде, то есть абзац мог бы «назвать свидетеля», процитировав себя.
    """
    names: set[str] = set()
    for source in sources.values():
        names |= _functions_defined_in(source)
    return frozenset(names)


@lru_cache(maxsize=None)
def _functions_defined_in(source: str) -> frozenset[str]:
    """Имена функций ОДНОГО исходника. Кэш ключуется ТЕКСТОМ исходника, а не путём.

    Поэтому он прозрачен: подменённая копия исходника есть другой ключ и разбирается заново,
    а неизменённый исходник не разбирается второй раз ни контролем, ни правилом. Без кэша три
    прохода по 190 модулям суиты стоили бы ~4.5 s и вывели бы каталог из бюджета T-15-06.
    """
    return frozenset(
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _suite_module_names(sources) -> frozenset[str]:
    """Имена модулей суиты, чей исходник РАЗБИРАЕТСЯ деревом: основа имени файла.

    Правило в дереве суиты бывает функцией и бывает МОДУЛЕМ правил, и запреты называют оба:
    замер 2026-09-24 — из двух имён, объявленных запретами Фазы 10, одно есть функция
    (`10-36-PLAN.md#1`), другое — модуль (`10-44-PLAN.md#3`, «правило
    `test_requirement_completion_follows_verification`»). Вселенная из одних функций объявила
    бы существующий модуль отсутствующим — то есть краснела бы на работе, а не на дефекте.
    """
    names: set[str] = set()
    for path, source in sources.items():
        _functions_defined_in(source)  # исходник, не разбирающийся деревом, — отказ, а не модуль
        names.add(Path(path).stem)
    return frozenset(names)


def _declared_rule_missing(declared, sources) -> list[str]:
    """Объявленные имена правил, которых в поданной вселенной суиты НЕТ — все, а не первое.

    `declared` — отображение «тождество запрета → объявленное имя»; признак «имя не
    объявлено» сюда не подаётся. Вселенная суиты приходит ПАРАМЕТРОМ, чтобы контроль мог
    подать изменённую копию.
    """
    universe = _suite_function_names(sources) | _suite_module_names(sources)
    return sorted(
        f"{identity.plan_path}#{identity.index}: объявлено правило `{name}`"
        for identity, name in declared.items()
        if name not in universe
    )


def _phase_10_verification_test(records):
    return [
        record
        for record in records
        if record.phase == DECISION_SCOPE_PHASE and record.verification == VERIFICATION_TEST
    ]


def _declared_rules(records, registry) -> dict:
    """Объявленные имена по тождеству — без признака «имя не объявлено»."""
    declared = {}
    for record in _phase_10_verification_test(records):
        name = registry[record.identity].get("declared_rule")
        if name != tool.RULE_UNDECLARED:
            declared[record.identity] = name
    return declared


@pytest.fixture(scope="module")
def suite_sources():
    return _suite_sources(SUITE_ROOT)


def test_phase_10_verification_test_count_is_declared(live_census):
    """Запретов Фазы 10 с `verification: test` — 61, по разбору блока, а не по строке."""
    assert len(_phase_10_verification_test(live_census)) == PHASE_10_VERIFICATION_TEST


def test_phase_10_verification_values_sum_to_the_decision_scope(live_census):
    """Три значения поля — `test`, `none` и ОТСУТСТВИЕ ключа — сходятся к 321 вторым путём."""
    in_scope = [record for record in live_census if record.phase == DECISION_SCOPE_PHASE]
    counts = Counter(record.verification for record in in_scope)
    assert (counts[VERIFICATION_TEST], counts[VERIFICATION_NONE], counts[None]) == (
        PHASE_10_VERIFICATION_TEST,
        PHASE_10_VERIFICATION_NONE,
        PHASE_10_VERIFICATION_ABSENT,
    ), counts
    assert sum(counts.values()) == len(in_scope)
    assert (
        PHASE_10_VERIFICATION_TEST + PHASE_10_VERIFICATION_NONE + PHASE_10_VERIFICATION_ABSENT
        == PROHIBITIONS_IN_DECISION_SCOPE
    )


def test_phase_10_verification_status_is_counted_a_second_way(live_census):
    """Поле `status` — третий счёт того же множества: все 321 — `flagged-unverified`."""
    in_scope = [record for record in live_census if record.phase == DECISION_SCOPE_PHASE]
    flagged = [record for record in in_scope if record.status == STATUS_FLAGGED_UNVERIFIED]
    assert len(flagged) == PHASE_10_STATUS_FLAGGED_UNVERIFIED == PROHIBITIONS_IN_DECISION_SCOPE


def test_verification_none_and_an_absent_key_are_not_mixed():
    """`verification: none` и отсутствие ключа — РАЗНЫЕ значения, и в реестре тоже."""
    source = """---
must_haves:
  prohibitions:
    - statement: "MUST NOT синтетика, объявившая none"
      verification: none
    - statement: "MUST NOT синтетика без ключа"
---
"""
    declared_none, absent = tool.census({SYNTHETIC_PLAN: source})
    assert declared_none.verification == VERIFICATION_NONE
    assert absent.verification is None
    assert tool.registry_row(declared_none)["verification"] == VERIFICATION_NONE
    assert "verification" not in tool.registry_row(absent)


def test_every_phase_10_verification_test_row_carries_a_declared_rule(
    live_census, registry_document
):
    """По каждому из 61 запрета — поле `declared_rule`: имя правила ЛИБО признак «не объявлено».

    Признак — отдельное значение, а не пустая строка и не ноль: ноль означал бы «объявлено
    ноль правил», и смешение изъяло бы элемент из правила молча (идиома
    `WalkthroughCounts.declared_checks`). Строки вне этого множества поля не несут вовсе.
    """
    registry = tool._registry_rows(registry_document)
    subject = {record.identity for record in _phase_10_verification_test(live_census)}
    without = sorted(identity for identity in subject if "declared_rule" not in registry[identity])
    assert not without, (
        f"строки реестра без поля `declared_rule` ({len(without)}):\n{_names(without)}"
    )
    malformed = sorted(
        identity
        for identity in subject
        if not isinstance(registry[identity]["declared_rule"], str)
        or not registry[identity]["declared_rule"].strip()
    )
    assert not malformed, _names(malformed)
    strays = sorted(
        identity
        for identity, row in registry.items()
        if "declared_rule" in row and identity not in subject
    )
    assert not strays, f"поле `declared_rule` вне множества D-05:\n{_names(strays)}"


def test_every_declared_rule_exists_in_the_suite_tree(
    live_census, registry_document, suite_sources
):
    """У каждого ОБЪЯВЛЕННОГО имени правила предъявлено существование в дереве суиты.

    ЧЕГО ГРУППА НЕ УТВЕРЖДАЕТ. Первое: совпадение имени не есть совпадение предмета — группа НЕ
    утверждает, что найденное правило действительно СТЕРЕЖЁТ предмет своего запрета, — это
    предмет человеческого суждения по D-33. Второе: о `verification: none` группа не судит — она не
    утверждает, что у таких запретов правила быть не должно, — это предмет решения владельца в
    плане 15-13. Число запретов БЕЗ объявленного имени не знает ни одно утверждение: это
    литерал сегодняшнего незакрытого состояния, и оно ДОКЛАДЫВАЕТСЯ в сообщении об отказе.
    """
    registry = tool._registry_rows(registry_document)
    declared = _declared_rules(live_census, registry)
    missing = _declared_rule_missing(declared, suite_sources)
    undeclared = len(_phase_10_verification_test(live_census)) - len(declared)
    assert not missing, (
        "объявленные правила, которых в дереве суиты нет:\n"
        + "\n".join(missing)
        + f"\n\nобъявлено имён {len(declared)}, запретов с признаком «имя не объявлено» "
        f"{undeclared}"
    )


def test_control_negative_a_declared_rule_absent_from_the_suite_is_named(suite_sources):
    """Имя, которого в суите нет, объявляется отсутствующим и НАЗЫВАЕТСЯ — двумя путями.

    (а) в перечень объявленного добавлено синтетическое имя; (б) из ПОДАННОЙ КОПИИ вселенной
    суиты вынут модуль, объявляющий существующее правило. Дерево не правится ни одним путём.
    """
    live_name = "test_control_a_missing_anchor_is_named_by_the_rule"
    synthetic = tool.ProhibitionIdentity(SYNTHETIC_PLAN, 0)
    real = tool.ProhibitionIdentity(SYNTHETIC_PLAN, 1)
    declared = {synthetic: "test_no_such_rule_was_ever_written", real: live_name}

    missing = _declared_rule_missing(declared, suite_sources)
    assert missing == [
        f"{SYNTHETIC_PLAN}#0: объявлено правило `test_no_such_rule_was_ever_written`"
    ], missing

    holder = [
        path for path, text in suite_sources.items() if live_name in _functions_defined_in(text)
    ]
    assert len(holder) == 1, holder
    doctored = {path: text for path, text in suite_sources.items() if path not in holder}
    assert sorted(_declared_rule_missing(declared, doctored)) == [
        f"{SYNTHETIC_PLAN}#0: объявлено правило `test_no_such_rule_was_ever_written`",
        f"{SYNTHETIC_PLAN}#1: объявлено правило `{live_name}`",
    ]


def test_control_positive_the_suite_function_universe_is_not_empty(suite_sources):
    """На неизменённом дереве вселенная имён функций суиты непуста — больше 1000 имён."""
    assert len(_suite_function_names(suite_sources)) > SUITE_FUNCTION_NAMES_FLOOR


# --- группа согласия с четырьмя историческими сетями ---------------------------------------
#
# Критерий 6 ROADMAP называет предметом расхождения четыре числа, снятые четырьмя сетями на 57
# планах Фазы 10 (15-RESEARCH.md Ф-03, воспроизведены разведкой). Замер прибором 2026-09-24
# воспроизвёл все четыре. Прибор, не умеющий их воспроизвести, не доказал бы, что заменяет их,
# а не просто даёт пятое число.
HISTORIC_NET_STATEMENT_LINES = 374
HISTORIC_NET_VERIFICATION_TEST_LINES = 76
HISTORIC_NET_PROHIBITIONS_KEYS = 57
HISTORIC_NET_PROSE_MARKERS = 38

# Сети сняты с ЭТОГО набора файлов; иначе их воспроизведение ничего не доказывает.
PHASE_10_PLAN_FILES = 57

# ПОПРАВКА РАЗЛОЖЕНИЯ «76 − 61 = 15 — соседние блоки» → 15 = 10 + 0 + 1 + 4 (план 15-01,
# задача 3, замер прибором 2026-09-24). 15-RESEARCH.md Ф-03 и задача 3 плана 15-01 записали
# разницу сети `verification: test` (76) с переписью (61) как «те же соседние блоки
# `truths`/`assumptions`». Счёт по слагаемым дал: 10 — ключи `verification: test` у элементов
# `truths`, 0 — у элементов `assumptions`, 1 — упоминание фразы в прозе шапки (строковый
# элемент блока `must_haves.key_links`, `10-47-PLAN.md:52`), 4 — упоминания фразы в теле
# `10-47-PLAN.md`. Сумма 15 верна,
# разбивка — нет: соседние блоки дают 10, а 5 — проза, а не блок вовсе. Принята величина,
# полученная счётом, а не перенесённая из ожидания; прежняя формулировка не вычёркивается —
# она названа здесь ПЕРВОЙ записью летописи, и её доминирующее слагаемое (соседние блоки) верно.
HISTORIC_VERIFICATION_TEST_IN_TRUTHS = 10
HISTORIC_VERIFICATION_TEST_IN_ASSUMPTIONS = 0
HISTORIC_VERIFICATION_TEST_IN_FRONTMATTER_PROSE = 1
HISTORIC_VERIFICATION_TEST_IN_BODY_PROSE = 4
HISTORIC_VERIFICATION_TEST_SURPLUS = 15


def _historic_nets_by_pattern(sources) -> dict:
    return {net.pattern: net for net in tool.historic_nets(tool.historic_sources(sources))}


def test_historic_nets_are_measured_on_the_declared_phase_10_plan_files(live_sources):
    """Четыре сети сняты с 57 файлов `10-*-PLAN.md` — тот же набор, что у исторического замера."""
    assert len(tool.historic_sources(live_sources)) == PHASE_10_PLAN_FILES


def test_historic_nets_are_reproduced_by_the_instrument(live_sources):
    """Прибор воспроизводит ВСЕ ЧЕТЫРЕ исторические сети: 374 / 76 / 57 / 38.

    ⚠️ ЭТО ДОКАЗЫВАЕТ СОГЛАСИЕ ПРИБОРА С ИХ МНОЖЕСТВАМИ, А НЕ ИХ ВЕРНОСТЬ. Каждая сеть честно
    считает СВОЁ множество — строки с формулировкой, строки с дескриптором, блоки, строки с
    маркером прозы, — и ни одно из них не есть множество запретов. Воспроизведение говорит,
    что прибор видит то же, что видели они, и умеет назвать, ЧТО именно каждая измеряла; перепись
    от этого не становится ни одной из четырёх.
    """
    nets = _historic_nets_by_pattern(live_sources)
    assert {pattern: net.count for pattern, net in nets.items()} == {
        r"^\s*- statement:": HISTORIC_NET_STATEMENT_LINES,
        "verification: test": HISTORIC_NET_VERIFICATION_TEST_LINES,
        r"^\s*prohibitions:": HISTORIC_NET_PROHIBITIONS_KEYS,
        "MUST NOT|НЕ ДОЛЖ|ЗАПРЕЩ": HISTORIC_NET_PROSE_MARKERS,
    }


def test_historic_nets_decompose_into_named_addends(live_sources):
    """Каждая сеть = сумма НАЗВАННЫХ слагаемых, снятых независимо от её числа; слагаемое
    переписи в каждой сети равно числу переписи того же множества."""
    nets = _historic_nets_by_pattern(live_sources)
    for net in nets.values():
        assert net.addends_total == net.count, net
    assert nets[r"^\s*- statement:"].addend(tool.ADDEND_CENSUS) == PROHIBITIONS_IN_DECISION_SCOPE
    assert (
        nets["verification: test"].addend(tool.ADDEND_VERIFICATION_TEST_CENSUS)
        == PHASE_10_VERIFICATION_TEST
    )
    assert (
        nets[r"^\s*prohibitions:"].addend(tool.ADDEND_PLANS_WITH_BLOCK) == PHASE_10_PLAN_FILES
    )


def test_historic_verification_test_net_and_the_census_differ_by_named_addends(live_sources):
    """76 и 61 утверждаются ОБА, и их разность 15 — слагаемыми, а не одним вычитанием."""
    net = _historic_nets_by_pattern(live_sources)["verification: test"]
    assert net.count == HISTORIC_NET_VERIFICATION_TEST_LINES
    assert net.addend(tool.ADDEND_VERIFICATION_TEST_CENSUS) == PHASE_10_VERIFICATION_TEST
    assert (
        net.addend(tool.ADDEND_VERIFICATION_TEST_TRUTHS),
        net.addend(tool.ADDEND_VERIFICATION_TEST_ASSUMPTIONS),
        net.addend(tool.ADDEND_VERIFICATION_TEST_FRONTMATTER_PROSE),
        net.addend(tool.ADDEND_VERIFICATION_TEST_BODY_PROSE),
    ) == (
        HISTORIC_VERIFICATION_TEST_IN_TRUTHS,
        HISTORIC_VERIFICATION_TEST_IN_ASSUMPTIONS,
        HISTORIC_VERIFICATION_TEST_IN_FRONTMATTER_PROSE,
        HISTORIC_VERIFICATION_TEST_IN_BODY_PROSE,
    )
    assert (
        HISTORIC_NET_VERIFICATION_TEST_LINES - PHASE_10_VERIFICATION_TEST
        == HISTORIC_VERIFICATION_TEST_IN_TRUTHS
        + HISTORIC_VERIFICATION_TEST_IN_ASSUMPTIONS
        + HISTORIC_VERIFICATION_TEST_IN_FRONTMATTER_PROSE
        + HISTORIC_VERIFICATION_TEST_IN_BODY_PROSE
        == HISTORIC_VERIFICATION_TEST_SURPLUS
    )


def test_control_historic_decomposition_reddens_on_an_unattributed_block():
    """Строка сети из блока, которого разложение не знает, ломает равенство — не растворяется.

    Синтетика: элемент с ключом `statement` в блоке `key_links` — такой строкой наивная сеть
    пополнится, а ни одно слагаемое её не назовёт. Остатка среди слагаемых нет, поэтому сумма
    обязана разойтись с числом сети.
    """
    source = """---
must_haves:
  key_links:
    - statement: "элемент блока, которого разложение не знает"
  prohibitions:
    - statement: "MUST NOT синтетический запрет"
---
"""
    net = _historic_nets_by_pattern({".planning/phases/10-synthetic/10-99-PLAN.md": source})[
        r"^\s*- statement:"
    ]
    assert net.count == 2
    assert net.addends_total == 1


def test_reconcile_table_carries_the_historic_and_the_census_numbers(live_sources):
    """Таблица сличения предъявляет и четыре исторических числа, и оба своих семейства."""
    table = "\n".join(tool.reconcile_lines(live_sources))
    for number in (
        HISTORIC_NET_STATEMENT_LINES,
        HISTORIC_NET_VERIFICATION_TEST_LINES,
        HISTORIC_NET_PROHIBITIONS_KEYS,
        HISTORIC_NET_PROSE_MARKERS,
        PROHIBITIONS_BEFORE_PHASE_15_PLANS,
        NAIVE_LINE_NET_DECLARED,
        PROHIBITIONS_DECLARED_AT_PHASE_15,
        NAIVE_LINE_NET_AT_PHASE_15,
    ):
        assert f"| {number} |" in table, (number, table)


def test_reconcile_seed_of_the_registry_is_idempotent_by_identity(
    live_census, registry_document
):
    """Повторный засев не меняет реестра ни на символ: дата замера и поля строк остаются."""
    again = tool.dump_registry(tool.seed_registry(live_census, registry_document, "1999-01-01"))
    assert again == REGISTRY_FILE.read_text(encoding="utf-8")

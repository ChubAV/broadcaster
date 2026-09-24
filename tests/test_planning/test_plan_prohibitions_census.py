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

from collections import Counter
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
REGISTRY_ROW_FIELDS = frozenset(
    {"plan", "index", "phase", "verification", "statement_digest", "class", "disposition"}
)
REGISTRY_ROW_FIELDS_DECLARED = 7

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

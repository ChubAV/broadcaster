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
Класс предмета (план 15-12) — тот же довод: предмет — ДВА машинно читаемых поля (`class` строки
реестра и перечень `PROHIBITION_CLASSES` модуля) и ОДНО объявленное между ними соответствие
(принадлежность); класс из прозы формулировки гейт не выводит, и суждения этот предмет не требует.

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
#
# ЛЕТОПИСЬ ЧИСЛА: 3 → 4, план 15-12, задача 1. План 15-01 объявил перечень
# `frozenset({"enforced", "permitted", "unresolved"})` и `DISPOSITIONS_DECLARED = 3` — по схеме,
# которую разведка (15-RESEARCH.md Ф-03) набросала сама и сама назвала наброском. ЧЕМ СНЯТО
# ЧЕТВЁРТОЕ ЗНАЧЕНИЕ — ЗАМЕРОМ, а не вкусом: построчная таблица действующего образца
# `10-PROHIBITIONS-SUBJECT.md:118-160` (39 запретов седьмой партии) применяет итог «принуждается
# частично», и среди записей, у которых правило вообще есть, он единственный: свод образца по 25
# записям с дескриптором `test` даёт «принуждается» 0, «принуждается частично» 8, «не
# принуждается» 17. (Формулировка плана «частичность в таблице ДОМИНИРУЕТ» верна для записей с
# правилом — 8 из 8, — а не для всех 25: там большинство у «не принуждается», которое здесь есть
# `unresolved`. Замер записан рядом со словом плана, слово не правится.) Пример образца дословно:
# у запрета плана 10-35 есть правило `test_the_failure_banner_registers_its_handlers_once_per_body`,
# но «половина „файл не правится ни на строку“ не покрыта ничем» — правило есть и закрывает ЧАСТЬ
# предмета. Трёхзначная схема заставила бы писать по такому запрету `enforced` (неправда: покрыта
# часть), `permitted` (неправда: разрешения не было) либо `unresolved` (неправда: правило есть), —
# и перепись 61 запрета D-05 стала бы ложным утверждением о дереве. ⚠️ ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН
# УСТАРЕЛ: на момент своей записи он был верным, и правится не он, а числа, которые он пережил.
# ⚠️ ЗНАЧЕНИЕ, ПРИШЕДШЕЕ В РЕЕСТР и не внесённое в перечень, краснит правило принадлежности ниже, а
# значение, внесённое в перечень без подъёма числа, краснит правило объявленных чисел, — иначе
# следующая эпоха диспозиций вышла бы из-под правила НЕЗАМЕТНО.
#
# ⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ (оговорка образца дословно; образец держит её полем
# `prohibitions_fully_enforced: 0` при 39 разрешённых запретах). Строка со значением `permitted` НЕ
# утверждает, что запрет соблюдён, и ни одно правило этого модуля так её не читает.
#
# Что предъявлено при каждом значении:
DISPOSITIONS = frozenset(
    {
        # принуждается полностью — предъявлено машинное правило, покрывающее ВЕСЬ предмет запрета;
        "enforced",
        # принуждается частично — правило есть, но покрывает часть предмета; НЕПОКРЫТАЯ часть
        # названа полем строки реестра `UNCOVERED_PART_FIELD`, а не подразумевается;
        "partially-enforced",
        # разрешено — человеческое разрешение владельца с машинно читаемой областью (`permit_scope`
        # именем класса). ⚠️ Поле разрешения заводит ОТВЕТ ВЛАДЕЛЬЦА; исполнитель его не пишет;
        "permitted",
        # неразобрано — решения не принималось: значение области D-02 (строки вне Фазы 10) и
        # переходное состояние строк Фазы 10 до решений плана 15-13.
        "unresolved",
    }
)
DISPOSITIONS_DECLARED = 4
PARTIALLY_ENFORCED = "partially-enforced"
PERMITTED = "permitted"
# Поле строки реестра, называющее НЕПОКРЫТУЮ часть предмета у диспозиции «принуждается частично».
# ⚠️ В `REGISTRY_ROW_FIELDS` оно НЕ внесено: ни одна строка его сегодня не несёт, и внесёт его план
# 15-13 вместе с первой такой диспозицией и летописью числа полей — по общему правилу перечня.
UNCOVERED_PART_FIELD = "uncovered_part"

# ПЕРЕЧЕНЬ КЛАССОВ ПРЕДМЕТА ЗАПРЕТА (D-04: владелец решает ПО КЛАССУ, `permit_scope` пишется
# ИМЕНЕМ класса, каждый запрет несёт СВОЮ строку со своим классом). ⚠️ КЛАСС — ЗАПИСАННОЕ ПОЛЕ
# РЕЕСТРА, А НЕ ВЫВОД В МОМЕНТ ПРОГОНА: замер 15-RESEARCH.md Ф-04 — 139 запретов из 321 попадают в
# два и более класса ключевых слов, 64 ни в один, и «первое совпадение выигрывает» сделало бы
# класс функцией ПОРЯДКА правил, то есть переименовало бы молча область решений владельца.
#
# ЛЕТОПИСЬ ЧИСЛА: 11. Выведено планом 15-12 (задача 2, 2026-09-24) ЧТЕНИЕМ всех 321 формулировки
# Фазы 10, ОДИН раз; восемь имён замера Ф-04 были отправной точкой, четыре примера D-04 вошли
# (`vendored-runtime-and-dependencies`, `record-immutability`, `requirement-flag`,
# `owner-decision-reserved`). Граница обозримости — от 5 до 12: один класс есть оптовое
# разрешение, тридцать — поштучное, и обе крайности владелец отверг. ⚠️ Класс, пришедший в реестр
# и не внесённый сюда, краснит правило принадлежности; внесённый без подъёма числа — правило
# объявленных чисел.
#
# ЧЕГО ПЕРЕЧЕНЬ НЕ УТВЕРЖДАЕТ: верность отнесения запрета к классу есть человеческое суждение, и
# правила ниже его не судят — они утверждают ПОЛНОТУ разнесения (D-33 не переоткрывается).
PROHIBITION_CLASSES = frozenset(
    {
        # продукт: записанное свойство поведения или устройства (панель, плашка, гард, границы
        # величин, коды уведомлений, тексты) не меняется;
        "product-invariant",
        # вендоренные рантаймы, строки JS, шаг сборки и новые зависимости, в том числе браузерная;
        "vendored-runtime-and-dependencies",
        # файлы, которых исполнение ОДНОГО плана не касается: «этим планом не правится» — чужая
        # область, не тот предмет, отказ стал бы неатрибутируемым;
        "plan-file-scope",
        # работа с названным владельцем вне плана: другая фаза, отложенная находка, предсуществующий
        # красный прогон, UI-находки;
        "work-owned-elsewhere",
        # записи проекта не правятся задним числом: исполненные планы и сводки, `.planning/research/`,
        # формулировки ROADMAP и CONTEXT, реестр окон, реестр запретов;
        "record-immutability",
        # опровергнутое не стирается, а помечается с названным преемником (идиома D-30/D-32);
        "superseded-text-kept",
        # вердикт и приёмка не выносятся исполнителем: поля отчёта верификации, состояние и отметки
        # артефакта обхода, состояния гэпов и окон;
        "self-certification",
        # требование не отмечается выполненным раньше вердикта своей фазы;
        "requirement-flag",
        # решение принадлежит владельцу или вехе: не принимается внутри задачи, не сочиняется, запертые
        # решения не переоткрываются;
        "owner-decision-reserved",
        # честность правил суиты: без подгонки под дерево, без литерала сегодняшнего состояния, без
        # второй копии числа, без зелени вакуумом и без утверждения, что рантайм что-то исполнил;
        "gate-integrity",
        # живая база и стенд: посев не запускается исполнителем, рабочее дерево смотрит в прод.
        "live-environment-safety",
    }
)
PROHIBITION_CLASSES_DECLARED = 11

# ПЕРЕЧЕНЬ ПОЛЕЙ СТРОКИ РЕЕСТРА. ⚠️ Полей `permit_*` и любого поля вердикта здесь НЕТ
# НАМЕРЕННО: их заводит ответ владельца на чекпойнте плана 15-12, а записывает по классам план
# 15-13; исполнитель, поставивший такое поле сам, вынес бы вердикт вместо владельца. Поле,
# пришедшее в реестр, вносится сюда ВМЕСТЕ С ЛЕТОПИСЬЮ — иначе оно войдёт в реестр незаметно.
# Сам ответ владельца (план 15-12, задача 3) записан НЕ в строки, а блоком документа
# `class_decisions` — его ключ и форма объявлены ниже (`REGISTRY_DOCUMENT_KEYS`).
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

# ПЕРЕЧЕНЬ КЛЮЧЕЙ ДОКУМЕНТА РЕЕСТРА. ЛЕТОПИСЬ ЧИСЛА: 3 → 4, план 15-12, задача 3 — пришёл блок
# `class_decisions` с ОТВЕТОМ ВЛАДЕЛЬЦА по классам (`chubav`, 2026-09-24T16:45Z). До ответа документ
# нёс три ключа — `measured`, `rows_declared`, `rows`, — и засев писал ровно их; ответ владельца
# записан не в строки (поле строки разрешения ставит план 15-13 вместе с диспозицией), а отдельным
# блоком после шапки замера, по форме образца `10-PROHIBITIONS-SUBJECT.md:1-36`. ⚠️ Ключ, пришедший
# в документ и не внесённый сюда, краснит правило ниже — в том числе поле вердикта, поставленное
# шапкой реестра: исполнитель, поставивший его сам, вынес бы вердикт вместо владельца.
REGISTRY_DOCUMENT_KEYS = frozenset({"measured", "rows_declared", "class_decisions", "rows"})
REGISTRY_DOCUMENT_KEYS_DECLARED = 4

# ВЕТВИ РЕШЕНИЯ ПО КЛАССУ — три ветви чекпойнта плана 15-12 (задача 3), дословно их `option id`.
# ⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ: ветвь `permit-class` закрывает долг класса РЕШЕНИЕМ, а не
# работой, и запреты класса остаются непринуждёнными машинно.
CLASS_DECISION_BRANCHES = frozenset({"permit-class", "require-enforcement", "row-by-row"})
CLASS_DECISION_BRANCHES_DECLARED = 3
PERMIT_CLASS_BRANCH = "permit-class"

# ФОРМА ЗАПИСИ РАЗРЕШЕНИЯ КЛАССА — поля образца `10-PROHIBITIONS-SUBJECT.md:1-36`, кроме
# `permit_covers_plans`: область здесь — КЛАСС (D-04), а не партия планов, и перечень планов
# разрешения не сужал бы, а читался бы как вторая область. Оба флага распространения обязаны быть
# `false`: разрешение класса не распространяется ни на фазу целиком, ни на веху.
PERMIT_DECISION_FIELDS = frozenset(
    {
        "permit_branch",
        "permitted_by",
        "permitted_on",
        "permit_basis",
        "permit_scope",
        "permit_applies_to_phase",
        "permit_applies_to_milestone",
        "permit_covers_prohibitions",
    }
)
PERMIT_DECISION_FIELDS_DECLARED = 8
PERMIT_SPREAD_FLAGS = ("permit_applies_to_phase", "permit_applies_to_milestone")

# ФОРМА ЗАПИСИ ИНОГО РЕШЕНИЯ ПО КЛАССУ (`require-enforcement`, `row-by-row`). ⚠️ Признака разрешения
# в именах её полей НЕТ НАМЕРЕННО: решение «требовать принуждения» разрешением не является, и
# машинный потребитель, считающий ключи `permit*`, не должен прочесть его как разрешение.
# `work_addressee` — адресат работы, которую решение оставляет открытой.
OTHER_DECISION_FIELDS = frozenset(
    {
        "decision_branch",
        "decided_by",
        "decided_on",
        "decision_basis",
        "decision_scope",
        "decision_covers_prohibitions",
        "work_addressee",
    }
)
OTHER_DECISION_FIELDS_DECLARED = 7

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


def partial_disposition_offences(rows) -> list[str]:
    """Строки «принуждается частично», не назвавшие НЕПОКРЫТУЮ часть предмета строкой."""
    offences = []
    for row in rows:
        if row.get("disposition") != PARTIALLY_ENFORCED:
            continue
        uncovered = row.get(UNCOVERED_PART_FIELD)
        if not isinstance(uncovered, str) or not uncovered.strip():
            offences.append(
                f"{row.get('plan')}#{row.get('index')}: диспозиция `{PARTIALLY_ENFORCED}` без "
                f"поля `{UNCOVERED_PART_FIELD}`"
            )
    return offences


def _row_name(row) -> str:
    return f"{row.get('plan')}#{row.get('index')}"


def _decision_scope_rows(rows) -> list:
    """Строки области решений D-02 — Фаза 10. Число их этот помощник не знает."""
    return [row for row in rows if str(row.get("phase")) == DECISION_SCOPE_PHASE]


def _class_offences(rows) -> list[str]:
    """Нарушения полноты разнесения по классам — ВСЕ, с тождествами, а не первое.

    Три предмета: (1) класс строки принадлежит словарю поля — объявленным классам и засеянному
    `unclassified`; (2) строка области решений не несёт `unclassified`; (3) строка ВНЕ области
    решений сохраняет `unclassified` и засеянную диспозицию (D-02 — ПРИНАДЛЕЖНОСТЬЮ, не числом).
    """
    vocabulary = PROHIBITION_CLASSES | {tool.SEED_CLASS}
    offences = []
    for row in rows:
        klass = row.get("class")
        in_scope = str(row.get("phase")) == DECISION_SCOPE_PHASE
        if klass not in vocabulary:
            offences.append(f"{_row_name(row)}: класс `{klass}` вне объявленного перечня")
        elif in_scope and klass == tool.SEED_CLASS:
            offences.append(f"{_row_name(row)}: строка области решений не классифицирована")
        elif not in_scope and (
            klass != tool.SEED_CLASS or row.get("disposition") != tool.SEED_DISPOSITION
        ):
            offences.append(
                f"{_row_name(row)}: строка вне области решений несёт класс `{klass}` и "
                f"диспозицию `{row.get('disposition')}` — D-02 оставляет её неразобранной"
            )
    return offences


def _decided_before_class(rows) -> list[str]:
    """Строки, чья диспозиция ушла от засеянной раньше, чем записан класс (D-03, D-04)."""
    return [
        f"{_row_name(row)}: диспозиция `{row.get('disposition')}` при классе `{row.get('class')}`"
        for row in rows
        if row.get("disposition") != tool.SEED_DISPOSITION
        and row.get("class") not in PROHIBITION_CLASSES
    ]


def _statement_digest_mismatches(records, registry) -> list[str]:
    """Тождества, у которых отпечаток строки реестра разошёлся с формулировкой по тождеству.

    Класс записан ДЛЯ ФОРМУЛИРОВКИ: правка её текста при неизменном тождестве унаследовала бы
    чужой класс молча. Отказ называет тождество и оба отпечатка.
    """
    mismatches = []
    for record in records:
        row = registry.get(record.identity)
        if row is not None and row.get("statement_digest") != record.digest:
            mismatches.append(
                f"{record.identity}: отпечаток реестра `{row.get('statement_digest')}`, "
                f"формулировки `{record.digest}` — класс `{row.get('class')}` записан для "
                f"другого текста"
            )
    return mismatches


def class_distribution(rows) -> str:
    """Распределение классов — ДОКЛАДЫВАЕТСЯ в отказе, в утверждения не входит."""
    counts = Counter(str(row.get("class")) for row in rows)
    return ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))


def _decision_class(decision) -> object:
    """Класс, который решение называет своей областью, — из поля своей формы."""
    return decision.get("permit_scope", decision.get("decision_scope"))


def _class_decision_offences(decisions, rows) -> list[str]:
    """Нарушения формы ответа владельца по классам — ВСЕ, с номером решения, а не первое.

    Предметы: (1) поля решения совпадают с одной из двух объявленных форм; (2) ветвь принадлежит
    своей форме; (3) класс решения принадлежит `PROHIBITION_CLASSES` и решён не дважды; (4) кто,
    когда и основание — непустые строки; (5) у разрешения оба флага распространения — `false`;
    (6) объявленное число покрываемых запретов равно числу строк области решений с этим классом —
    число решения и реестр не расходятся молча. Ни одно из них не знает, СКОЛЬКО классов
    разрешено: это ответ владельца, а не свойство формы.
    """
    covered = Counter(str(row.get("class")) for row in _decision_scope_rows(rows))
    offences: list[str] = []
    seen: Counter = Counter()
    for position, decision in enumerate(decisions):
        name = f"решение #{position}"
        fields = set(decision)
        if fields == PERMIT_DECISION_FIELDS:
            branch, who, when, basis, covers = (
                decision[field]
                for field in (
                    "permit_branch",
                    "permitted_by",
                    "permitted_on",
                    "permit_basis",
                    "permit_covers_prohibitions",
                )
            )
            if branch != PERMIT_CLASS_BRANCH:
                offences.append(f"{name}: форма разрешения при ветви `{branch}`")
            for flag in PERMIT_SPREAD_FLAGS:
                if decision[flag] is not False:
                    offences.append(
                        f"{name}: `{flag}` = `{decision[flag]}` — разрешение класса читалось бы "
                        f"шире класса"
                    )
        elif fields == OTHER_DECISION_FIELDS:
            branch, who, when, basis, covers = (
                decision[field]
                for field in (
                    "decision_branch",
                    "decided_by",
                    "decided_on",
                    "decision_basis",
                    "decision_covers_prohibitions",
                )
            )
            if branch not in CLASS_DECISION_BRANCHES - {PERMIT_CLASS_BRANCH}:
                offences.append(f"{name}: ветвь `{branch}` вне ветвей иного решения")
            addressee = decision["work_addressee"]
            if not isinstance(addressee, str) or not addressee.strip():
                offences.append(f"{name}: адресат работы не назван")
        else:
            offences.append(
                f"{name}: поля {sorted(fields)} не совпадают ни с формой разрешения, ни с формой "
                f"иного решения"
            )
            continue
        klass = _decision_class(decision)
        if klass not in PROHIBITION_CLASSES:
            offences.append(f"{name}: класс `{klass}` вне объявленного перечня")
        seen[klass] += 1
        for label, value in (("кто", who), ("когда", when), ("основание", basis)):
            if not isinstance(value, str) or not value.strip():
                offences.append(f"{name}: поле «{label}» пусто или не строка")
        if type(covers) is not int or covers != covered[str(klass)]:
            offences.append(
                f"{name}: класс `{klass}` объявляет покрытыми {covers!r} запретов, в реестре "
                f"строк области решений с этим классом {covered[str(klass)]}"
            )
    for klass, times in sorted(seen.items(), key=lambda item: str(item[0])):
        if times > 1:
            offences.append(f"класс `{klass}` решён {times} раза — ответ владельца двузначен")
    return offences


def _permitted_classes(decisions) -> frozenset:
    return frozenset(
        decision["permit_scope"]
        for decision in decisions
        if set(decision) == PERMIT_DECISION_FIELDS
        and decision["permit_branch"] == PERMIT_CLASS_BRANCH
    )


def _permitted_without_permission(rows, decisions) -> list[str]:
    """Строки с диспозицией «разрешено», чей класс РАЗРЕШЕНИЯ владельца не получил."""
    permitted = _permitted_classes(decisions)
    return [
        f"{_row_name(row)}: диспозиция `{PERMITTED}` при классе `{row.get('class')}` без "
        f"разрешения владельца"
        for row in rows
        if row.get("disposition") == PERMITTED and row.get("class") not in permitted
    ]


def decision_distribution(decisions) -> str:
    """Ветви ответа владельца по классам — ДОКЛАДЫВАЮТСЯ в отказе, в утверждения не входят."""
    return ", ".join(
        f"{_decision_class(decision)}: "
        f"{decision.get('permit_branch', decision.get('decision_branch'))}"
        for decision in decisions
    )


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


def test_the_disposition_vocabulary_declares_four_values_with_the_partial_one():
    """Четыре значения, и среди них «принуждается частично», снятое замером образца.

    Засеянное значение строки реестра обязано принадлежать перечню: иначе засев сам писал бы
    диспозицию вне словаря, и правило принадлежности краснело бы на каждой новой строке.
    """
    assert len(DISPOSITIONS) == DISPOSITIONS_DECLARED, sorted(DISPOSITIONS)
    assert PARTIALLY_ENFORCED in DISPOSITIONS
    assert tool.SEED_DISPOSITION in DISPOSITIONS


def test_every_partially_enforced_disposition_names_its_uncovered_part(registry_document):
    """«Частично» без названной непокрытой части есть «полностью» под другим именем."""
    rows = registry_document["rows"]
    offences = partial_disposition_offences(rows)
    assert not offences, (
        "частичные диспозиции без названной непокрытой части:\n"
        + "\n".join(offences)
        + f"\n\nраспределение диспозиций реестра: {disposition_distribution(rows)}"
    )


def test_control_a_disposition_outside_the_vocabulary_is_named():
    """Синтетическая строка с пятым значением НАЗЫВАЕТСЯ правилом принадлежности."""
    rows = [
        {"plan": SYNTHETIC_PLAN, "index": 0, "disposition": "unresolved"},
        {"plan": SYNTHETIC_PLAN, "index": 1, "disposition": "waived"},
    ]
    assert disposition_offences(rows) == [f"{SYNTHETIC_PLAN}#1: диспозиция `waived`"]


def test_control_a_partial_disposition_without_the_uncovered_part_is_named():
    """Три синтетические строки: без поля, с пустым полем и с названной частью — краснеют две."""
    rows = [
        {"plan": SYNTHETIC_PLAN, "index": 0, "disposition": PARTIALLY_ENFORCED},
        {
            "plan": SYNTHETIC_PLAN,
            "index": 1,
            "disposition": PARTIALLY_ENFORCED,
            UNCOVERED_PART_FIELD: "  ",
        },
        {
            "plan": SYNTHETIC_PLAN,
            "index": 2,
            "disposition": PARTIALLY_ENFORCED,
            UNCOVERED_PART_FIELD: "половина «файл не правится ни на строку»",
        },
    ]
    offences = partial_disposition_offences(rows)
    assert [offence.split(":")[0] for offence in offences] == [
        f"{SYNTHETIC_PLAN}#0",
        f"{SYNTHETIC_PLAN}#1",
    ], offences


# --- классы предмета: полнота разнесения, а не его правильность ---------------------------


def test_the_prohibition_class_vocabulary_is_declared_and_not_empty():
    """Число классов объявлено литералом и равно длине перечня; перечень непуст (антивакуум).

    Перечень, опустевший молча, оставил бы правило принадлежности зелёным ровно тогда, когда
    классов не стало. Засеянное `unclassified` классом НЕ является.
    """
    assert PROHIBITION_CLASSES_DECLARED > 0
    assert len(PROHIBITION_CLASSES) == PROHIBITION_CLASSES_DECLARED, sorted(PROHIBITION_CLASSES)
    assert tool.SEED_CLASS not in PROHIBITION_CLASSES


def test_every_row_class_is_complete_for_the_decision_scope(registry_document):
    """Каждый класс — из перечня; ни одна строка Фазы 10 не `unclassified`; вне области — да.

    Отказ НАЗЫВАЕТ тождества; распределение классов ДОКЛАДЫВАЕТСЯ и в утверждение не входит.
    """
    rows = registry_document["rows"]
    offences = _class_offences(rows)
    assert not offences, (
        f"нарушения полноты разнесения по классам ({len(offences)}):\n"
        + "\n".join(offences)
        + f"\n\nраспределение классов реестра: {class_distribution(rows)}"
    )


def test_the_decision_scope_is_not_empty_and_carries_no_unclassified_row(registry_document):
    """Антивакуум полноты: область решений в реестре НЕПУСТА, и `unclassified` в ней нет."""
    scope = _decision_scope_rows(registry_document["rows"])
    assert len(scope) == PROHIBITIONS_IN_DECISION_SCOPE
    unclassified = [_row_name(row) for row in scope if row.get("class") == tool.SEED_CLASS]
    assert not unclassified, "\n".join(unclassified)


def test_no_disposition_is_decided_before_its_class(registry_document):
    """Решение идёт ПОСЛЕ класса (D-03, D-04): диспозиция вне засеянной требует класса."""
    offences = _decided_before_class(registry_document["rows"])
    assert not offences, "\n".join(offences)


def test_every_statement_digest_matches_the_statement_found_by_identity(
    live_census, registry_document
):
    """Класс не наследуется чужой формулировкой: отпечаток строки равен отпечатку по тождеству."""
    mismatches = _statement_digest_mismatches(
        live_census, tool._registry_rows(registry_document)
    )
    assert not mismatches, "\n".join(mismatches)


def test_control_a_doctored_statement_is_named_by_the_digest_rule(
    live_sources, registry_document
):
    """Подменённая КОПИЯ исходников: формулировка одного запрета Фазы 10 правится на символ."""
    registry = tool._registry_rows(registry_document)
    victim = next(
        record for record in tool.census(live_sources) if record.phase == DECISION_SCOPE_PHASE
    )
    doctored = dict(live_sources)
    text = doctored[victim.identity.plan_path]
    first_line = victim.statement.splitlines()[0]
    assert first_line in text, victim.identity
    doctored[victim.identity.plan_path] = text.replace(first_line, first_line + " ПРАВКА", 1)
    mismatches = _statement_digest_mismatches(tool.census(doctored), registry)
    assert len(mismatches) == 1 and mismatches[0].startswith(f"{victim.identity}:"), mismatches


def test_control_class_offences_are_named_for_every_kind():
    """Синтетические строки: класс вне перечня, неразобранная строка области, чужая строка."""
    rows = [
        {"plan": SYNTHETIC_PLAN, "index": 0, "phase": DECISION_SCOPE_PHASE,
         "class": "no-such-class", "disposition": tool.SEED_DISPOSITION},
        {"plan": SYNTHETIC_PLAN, "index": 1, "phase": DECISION_SCOPE_PHASE,
         "class": tool.SEED_CLASS, "disposition": tool.SEED_DISPOSITION},
        {"plan": SYNTHETIC_PLAN, "index": 2, "phase": "99",
         "class": sorted(PROHIBITION_CLASSES)[0], "disposition": tool.SEED_DISPOSITION},
        {"plan": SYNTHETIC_PLAN, "index": 3, "phase": "99",
         "class": tool.SEED_CLASS, "disposition": PARTIALLY_ENFORCED},
        {"plan": SYNTHETIC_PLAN, "index": 4, "phase": DECISION_SCOPE_PHASE,
         "class": sorted(PROHIBITION_CLASSES)[0], "disposition": tool.SEED_DISPOSITION},
    ]
    named = [offence.split(":")[0] for offence in _class_offences(rows)]
    assert named == [f"{SYNTHETIC_PLAN}#{index}" for index in (0, 1, 2, 3)], named
    assert _decided_before_class(rows) == [
        f"{SYNTHETIC_PLAN}#3: диспозиция `{PARTIALLY_ENFORCED}` при классе `{tool.SEED_CLASS}`"
    ]


def test_the_gate_never_calls_the_draft_classifier():
    """Черновая разбивка ключевыми словами — для человека; ни одно правило её не зовёт.

    Читается ДЕРЕВО этого модуля, а не текст: имя в докстринге или строке не в счёт. Ни одно
    обращение к прибору не называет черновой раздел — ни функцию, ни перечень образцов.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    touched = sorted(
        {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "tool"
            and "draft" in node.attr.lower()
        }
    )
    imported = sorted(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if "draft" in alias.name.lower()
    )
    assert not touched and not imported, (touched, imported)


def test_the_declared_vocabularies_and_numbers_agree():
    """Объявленные перечни и числа модуля согласны между собой."""
    assert len(DISPOSITIONS) == DISPOSITIONS_DECLARED, sorted(DISPOSITIONS)
    assert len(REGISTRY_ROW_FIELDS) == REGISTRY_ROW_FIELDS_DECLARED, sorted(REGISTRY_ROW_FIELDS)
    assert sum(PROHIBITIONS_BY_PHASE_DECLARED.values()) == PROHIBITIONS_DECLARED_AT_PHASE_15
    assert (
        PROHIBITIONS_DECLARED_AT_PHASE_15 - PROHIBITIONS_BY_PHASE_DECLARED[PHASE_15]
        == PROHIBITIONS_BEFORE_PHASE_15_PLANS
    )


# --- ответ владельца по классам: форма записи, а не её содержание ---------------------------
#
# ЧЕГО ГРУППА НЕ УТВЕРЖДАЕТ. Она не знает, СКОЛЬКО классов разрешено и какие: это ответ владельца,
# и правило, знающее его, переписывалось бы при каждом новом ответе. Она не утверждает, что КАЖДЫЙ
# класс получил ответ: `resume-signal` чекпойнта прямо разрешает не отвечать, и класс без ответа
# есть законное состояние (его запреты остаются «неразобрано», и план 15-13 называет их числом).
# И она не утверждает, что хоть один запрет СОБЛЮДЁН: РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ.


def test_the_registry_document_carries_only_declared_keys(registry_document):
    """Ключ документа реестра принадлежит объявленному перечню; ключ вне перечня называется."""
    strays = sorted(set(registry_document) - REGISTRY_DOCUMENT_KEYS)
    assert not strays, f"ключи документа реестра вне объявленного перечня: {strays}"


def test_the_class_decision_vocabularies_agree():
    """Объявленные перечни ответа владельца согласны со своими числами и между собой."""
    assert len(REGISTRY_DOCUMENT_KEYS) == REGISTRY_DOCUMENT_KEYS_DECLARED
    assert tool.CLASS_DECISIONS_KEY in REGISTRY_DOCUMENT_KEYS
    assert len(CLASS_DECISION_BRANCHES) == CLASS_DECISION_BRANCHES_DECLARED
    assert PERMIT_CLASS_BRANCH in CLASS_DECISION_BRANCHES
    assert len(PERMIT_DECISION_FIELDS) == PERMIT_DECISION_FIELDS_DECLARED
    assert len(OTHER_DECISION_FIELDS) == OTHER_DECISION_FIELDS_DECLARED
    assert set(PERMIT_SPREAD_FLAGS) <= PERMIT_DECISION_FIELDS
    assert all(field.startswith(tool.PERMIT_PREFIX) for field in PERMIT_DECISION_FIELDS)
    assert not any(field.startswith(tool.PERMIT_PREFIX) for field in OTHER_DECISION_FIELDS)


def test_every_class_decision_has_the_declared_form_and_agrees_with_the_registry(
    registry_document,
):
    """Каждое решение по классу — одной из двух форм, по классу перечня, с числом по реестру.

    Антивакуум: блок ответа непуст — ответ владельца получен 2026-09-24, и его исчезновение из
    реестра молча сняло бы все разрешения. Ветви ДОКЛАДЫВАЮТСЯ в отказе.
    """
    decisions = registry_document.get(tool.CLASS_DECISIONS_KEY) or []
    assert decisions, "блок ответа владельца по классам пуст или отсутствует"
    offences = _class_decision_offences(decisions, registry_document["rows"])
    assert not offences, (
        "нарушения формы ответа владельца по классам:\n"
        + "\n".join(offences)
        + f"\n\nветви ответа: {decision_distribution(decisions)}"
    )


def test_no_row_is_permitted_unless_its_class_was_permitted(registry_document):
    """«Разрешено» стоит только там, где владелец разрешил КЛАСС: иначе это вердикт за него."""
    rows = registry_document["rows"]
    decisions = registry_document.get(tool.CLASS_DECISIONS_KEY) or []
    offences = _permitted_without_permission(rows, decisions)
    assert not offences, (
        "\n".join(offences)
        + f"\n\nраспределение диспозиций реестра: {disposition_distribution(rows)}"
        + f"\nветви ответа: {decision_distribution(decisions)}"
    )


def test_control_class_decision_offences_are_named_for_every_kind():
    """Синтетические решения — по одному на каждый вид нарушения; каждое НАЗЫВАЕТСЯ."""
    klass, other = sorted(PROHIBITION_CLASSES)[:2]
    rows = [
        {"plan": SYNTHETIC_PLAN, "index": 0, "phase": DECISION_SCOPE_PHASE, "class": klass},
        {"plan": SYNTHETIC_PLAN, "index": 1, "phase": DECISION_SCOPE_PHASE, "class": other},
    ]
    good_permit = {
        "permit_branch": PERMIT_CLASS_BRANCH,
        "permitted_by": "синтетика",
        "permitted_on": "1999-01-01",
        "permit_basis": "синтетика",
        "permit_scope": klass,
        "permit_applies_to_phase": False,
        "permit_applies_to_milestone": False,
        "permit_covers_prohibitions": 1,
    }
    good_other = {
        "decision_branch": "require-enforcement",
        "decided_by": "синтетика",
        "decided_on": "1999-01-01",
        "decision_basis": "синтетика",
        "decision_scope": other,
        "decision_covers_prohibitions": 1,
        "work_addressee": "синтетика",
    }
    assert _class_decision_offences([good_permit, good_other], rows) == []

    broken = [
        {**good_permit, "permit_applies_to_milestone": True},
        {**good_other, "decision_branch": PERMIT_CLASS_BRANCH},
        {**good_permit, "permit_scope": "no-such-class", "permit_covers_prohibitions": 0},
        {**good_other, "decision_covers_prohibitions": True},
        {**good_other, "work_addressee": " ", "decided_by": ""},
        {**good_permit, "verdict_of_the_phase": "синтетика"},
    ]
    offences = _class_decision_offences(broken, rows)
    named = sorted({offence.split(":")[0] for offence in offences})
    assert named == sorted(
        [f"решение #{position}" for position in range(6)]
        + [f"класс `{other}` решён 3 раза — ответ владельца двузначен"]
    ), offences


def test_control_a_permitted_row_without_a_permitted_class_is_named():
    """Две строки «разрешено»: класс с разрешением — молчит, класс без разрешения — назван."""
    klass, other = sorted(PROHIBITION_CLASSES)[:2]
    decisions = [
        {
            "permit_branch": PERMIT_CLASS_BRANCH,
            "permitted_by": "синтетика",
            "permitted_on": "1999-01-01",
            "permit_basis": "синтетика",
            "permit_scope": klass,
            "permit_applies_to_phase": False,
            "permit_applies_to_milestone": False,
            "permit_covers_prohibitions": 1,
        }
    ]
    rows = [
        {"plan": SYNTHETIC_PLAN, "index": 0, "class": klass, "disposition": PERMITTED},
        {"plan": SYNTHETIC_PLAN, "index": 1, "class": other, "disposition": PERMITTED},
    ]
    offences = _permitted_without_permission(rows, decisions)
    assert [offence.split(":")[0] for offence in offences] == [f"{SYNTHETIC_PLAN}#1"], offences


def test_control_the_seed_carries_the_owner_answer_and_never_writes_it(live_census):
    """Засев переносит блок ответа как есть и НЕ заводит его там, где ответа не было."""
    answer = [{"decision_scope": "синтетика"}]
    carried = tool.seed_registry(live_census, {"rows": [], tool.CLASS_DECISIONS_KEY: answer}, "x")
    assert carried[tool.CLASS_DECISIONS_KEY] is answer
    assert list(carried) == ["measured", "rows_declared", tool.CLASS_DECISIONS_KEY, "rows"]
    fresh = tool.seed_registry(live_census, None, "x")
    assert tool.CLASS_DECISIONS_KEY not in fresh


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

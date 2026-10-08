---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 21
subsystem: ui
tags: [css, jinja2, htmx, form_wrapper, layout, gap-closure]

# Dependency graph
requires:
  - phase: 09-htmx-formy-i-svoystva-kachestva
    provides: "макрос `components/form_wrapper.html` и класс индикатора `.form-busy` — ОДНО место, раздающее свойства качества формам вехи (D-14)"
  - phase: 10-modalnye-paneli-i-shell
    provides: "компонент панели подтверждения `components/modal.html` с собственной копией узла индикатора и принятой высотой (10-UAT 3.5)"
provides:
  - "Класс области `form-wrapper` в теге формы макроса-обёртки — единственная точка, которой правило стилей отличает форму обёртки от формы панели"
  - "Два правила стилей: форма обёртки — контекст позиционирования; её индикатор выведен из потока в правый нижний угол коробки формы, прозрачен для указателя"
  - "Исключение строки группы (`position: static`) — точка остаётся рядом с тумблером по решению владельца 3"
  - "Машинный гейт `test_a_wrapped_form_gives_its_indicator_no_layout_footprint` с двумя подстановками"
  - "Машинный гейт `test_the_confirmation_panel_indicator_keeps_its_accepted_place` с тремя подстановками — неподвижность 18 мест подтверждения"
  - "Перечень `IN_FLOW_INDICATOR_EXCEPTIONS` с обоснованием на запись и числом `= 1` (идиома SP-1)"
affects: [верификация Фазы 11, будущие потребители form_wrapper, любая правка раздела индикатора app.css]

actuals:
  tokens: 14048
  tasks: 2
  commits: 3
  plan_head_before: 073ba7527edd307643edac27770990750fc8c8fa

tech-stack:
  added: []
  patterns:
    - "Область правки задаётся ТРЕТЬИМ именем (класс формы), когда две копии одного узла обязаны разъехаться по поведению, но остаться равными по разметке"
    - "RED правила, зелёного по замыслу на правильном дереве, измеряется МУТАНТАМИ рабочей копии с возвратом через `git checkout --` и сверкой порцелана"

key-files:
  created: []
  modified:
    - app/templates/components/form_wrapper.html
    - app/static/css/app.css
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_templates/test_components.py

key-decisions:
  - "Область правила «индикатор вне потока» задаёт класс формы обёртки (`form-wrapper`), а не класс индикатора и не значение `hx-indicator`: панель подтверждения печатает дословно тот же узел с тем же селектором поиска, и правило по индикатору сдвинуло бы разом все 18 мест подтверждения (решение владельца 1 от 2026-09-17)"
  - "Смещения нулевые, точка остаётся ВНУТРИ коробки формы: `.card` несёт `overflow: hidden` и срезал бы выступ, а в рядах с промежутком 8–9 px вынесенная наружу точка легла бы на соседний орган; отрицательное смещение подсказки UI-ревизии отвергнуто"
  - "`pointer-events: none` — не украшение, а митигация T-11-42: точка стои́т поверх угла органа, у тумблеров расписания цель блокировки пустая, и перехваченное нажатие пропало бы молча"
  - "Точка формы тумблера строки группы ОСТАЁТСЯ в потоке рядом с тумблером — второе исключение объёма и решение владельца 3 от 2026-09-17, объявленное одной записью перечня с обоснованием и числом"
  - "Обоснование различия «имя класса формы» получило ПОКОЛЕНИЕ, а не исправление (D-30/D-32): прежний текст «обёртка класса формы не знает вовсе» был верен для дерева до плана 11-21 и ошибкой не был"
  - "Управление пробелами в теле макроса не тронуто: у выведенного из потока узла ведущий пробел становится хвостовым сворачиваемым пробелом строки и места не занимает — смена управления сдвинула бы разметку четырнадцати форм ради нулевого выигрыша"

patterns-established:
  - "Гейт неподвижности: правило утверждает не «моё правило есть», а «до чужого узла не дотягивается НИЧЬЁ правило вне объявленного множества» — множество селекторов собирается из констант и перечня исключений"
  - "Подстановка обязана краснеть В ОЖИДАЕМОМ МЕСТЕ: ключ словаря нарушений сверяется, иначе «покраснело хоть на чём-то» сходит за доказательство зубов"

requirements-completed: [FORM-03, FORM-04, FORM-08]

coverage:
  - id: D1
    description: "Индикатор формы обёртки выведен из потока одним правилом области: класс в теге макроса, контекст позиционирования формы, правило индикатора в области с нулевыми смещениями и прозрачностью для указателя"
    requirement: FORM-03
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_a_wrapped_form_gives_its_indicator_no_layout_footprint"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_the_reported_profile_form_carries_the_indicator_scope"
        status: pass
    human_judgment: false
  - id: D2
    description: "Панели подтверждения (18 мест) не задеты ни разметкой, ни стилями: тег формы панели класса области не несёт, базовые правила индикатора позиции не объявляют, колонка панели сохраняет промежуток 14px"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_confirmation_panel_indicator_keeps_its_accepted_place"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_the_panel_form_stays_outside_the_indicator_scope"
        status: pass
      - kind: other
        ref: "мутант А (селектор без области) — «2 failed, 2 passed, 1 warning in 0.58s»; мутант Б (класс области на теге панели) — «2 failed, 2 passed, 1 warning in 0.61s»"
        status: pass
    human_judgment: false
  - id: D3
    description: "Точка строки группы осталась рядом с тумблером — исключение объявлено одной записью перечня с обоснованием и числом `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED = 1`"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_a_wrapped_form_gives_its_indicator_no_layout_footprint"
        status: pass
    human_judgment: false
  - id: D4
    description: "Гейты, названные диагнозом, зелены без ослабления; полный прогон `uv run pytest tests/ -q` без отбора маркером зелен"
    verification:
      - kind: unit
        ref: "uv run pytest tests/ -q → 3410 passed, 1000 warnings in 2268.42s"
        status: pass
      - kind: unit
        ref: "uv run pytest <11 названных диагнозом идентификаторов> -q → 25 passed"
        status: pass
    human_judgment: false
  - id: D5
    description: "В браузере под «Сохранить» (профиль), «Продолжить» (MAX) и «Сохранить расписание» нет лишней полосы; промежутки рядов ровные; точка появляется во время медленного запроса в нижнем правом углу формы, не садится на ручку тумблера и не гасит нажатие; панель подтверждения выглядит как прежде"
    verification: []
    human_judgment: true
    rationale: "Проверка 6 `11-UAT.md` — замер высот и наблюдение наложения точки поверх угла органа в живом Chrome на боевых стилях. Машинно утверждается объявление правил, а не отрисовка; отметку ставит человек в `/gsd-verify-work 11`, и `11-UAT.md` исполнителем не правится"

duration: 63 min
completed: 2026-09-17
status: complete
---

# Phase 11 Plan 21: Индикатор формы обёртки вне потока (G-11-6) Summary

**Скрытый индикатор `.form-busy` выведен из потока внутри форм обёртки классом области `form-wrapper` — одна правка в макросе и два правила стилей вместо четырнадцати правок у вызывающих, при доказанной неподвижности 18 панелей подтверждения.**

## Performance

- **Duration:** 63 min
- **Started:** 2026-09-17T19:00:21Z
- **Completed:** 2026-09-17T20:03:55Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- **Корневая причина снята одним местом.** `form_wrapper.html` печатает литеральный класс `form-wrapper` сразу после адреса запроса и до ветвей цели; `app.css` даёт форме обёртки контекст позиционирования и выводит её индикатор в правый нижний угол коробки формы (`position: absolute; right: 0; bottom: 0; pointer-events: none`). Замеренные диагнозом 21 px (профиль), 18,5 px (мастер MAX), 24 px (правка расписания) и ~12 px хвоста в рядах исчезают по построению.
- **Панели подтверждения доказанно не задеты.** `test_the_confirmation_panel_indicator_keeps_its_accepted_place` утверждает пять вещей (тег панели без класса области; класс области только в обёртке; множество селекторов, достающих индикатор; базовые правила без `position`; колонка панели в принятом состоянии) и краснеет на трёх подстановках. Сверх подстановок сняты два мутанта рабочей копии.
- **Исключение строки группы объявлено решением, а не умолчанием.** `IN_FLOW_INDICATOR_EXCEPTIONS` — одна запись с обоснованием (09-UAT 6.1.2 + решение владельца 3 от 2026-09-17) и числом `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED = 1`.
- **Летопись сохранена, а не переписана.** Обоснование различия «имя класса формы» и абзац раздела сличения двух копий набора качества получили поколение по идиоме D-30/D-32; прежний текст не вычеркнут.
- **Полный прогон без отбора маркером зелен целиком:** `3410 passed, 1000 warnings in 2268.42s (0:37:48)`, rc=0. Известное ночное окно `test_the_overview_error_number_matches_the_users_own_dashboard` не сработало — прогон шёл вне 00:00–05:00 UTC.

## Task Commits

1. **Задача 1 (RED): тесты первыми, продукт не тронут** — `ec33c8e` (test)
2. **Задача 1 (GREEN): макрос и стили** — `810eaa7` (fix)
3. **Задача 2: гейт неподвижности панели и поколение обоснования** — `bf3cb65` (test)

**Plan metadata:** см. коммит `docs(11-21)` ниже по истории.

_Задача 1 — `type="tracer"` с `tdd="true"`: RED → GREEN двумя коммитами, REFACTOR не понадобился (правка — один атрибут и три правила). Задача 2 правит только тестовые модули; её RED измерен мутантами, как предписал план._

## TDD Gate Compliance

| Gate | Commit | Статус |
|------|--------|--------|
| RED | `ec33c8e` `test(11-21)` | ✓ «2 failed», оба отказа — отказы утверждений, четыре нарушения (а)–(г) названы поимённо; прибор `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` |
| GREEN | `810eaa7` `fix(11-21)` | ✓ «2 passed, 1 warning in 0.33s» |
| REFACTOR | — | не потребовался (изменений сверх минимальных нет) |

⚠️ **Тип коммита GREEN — `fix`, а не `feat`, и это осознанно:** план закрывает ГЭП UAT (дефект вёрстки), а не добавляет функциональность. Последовательность RED → GREEN соблюдена: коммит с тестами предшествует коммиту с продуктом, и на дереве RED продукт не тронут ни одним байтом.

**Задача 2 (RED мутантами).** Оба теста задачи 2 на правильном дереве зелены ПО ЗАМЫСЛУ — они утверждают отсутствие воздействия. Поэтому RED измерен временными мутантами рабочей копии:

- **Мутант А** (селектор правила индикатора лишён области → `form > .form-busy`): `2 failed, 2 passed, 1 warning in 0.58s`; отказ гейта панели назвал селектор `form > .form-busy`.
- **Мутант Б** (класс области дописан в тег формы панели): `2 failed, 2 passed, 1 warning in 0.61s`; отказ назвал тег панели с классом области, второй отказ — потерю точного `class="modal__form"` на рендере.

Оба файла возвращены `git checkout --`; `git status --porcelain -- app/static/css/app.css app/templates/components/modal.html` после возврата — пустой вывод.

## Прогоны, записанные дословно

| Прогон | Итоговая строка |
|--------|-----------------|
| RED задачи 1 (первая команда `<verify>`) | `2 failed, 1 warning in 1.15s` |
| GREEN задачи 1 (та же команда) | `2 passed, 1 warning in 0.33s` |
| Задача 1, вторая команда `<verify>` | `323 passed, 114 warnings in 137.34s (0:02:17)` |
| Задача 1, третья команда `<verify>` | `172 passed, 102 warnings in 158.06s (0:02:38)` |
| Задача 2, первая команда `<verify>` (живое дерево) | `4 passed` в составе прогона `5 passed, 1 warning in 1.22s` |
| Задача 2, мутант А | `2 failed, 2 passed, 1 warning in 0.58s` |
| Задача 2, мутант Б | `2 failed, 2 passed, 1 warning in 0.61s` |
| Задача 2, вторая команда `<verify>` | `506 passed, 215 warnings in 295.63s (0:04:55)` |
| Гейты, названные диагнозом (11 идентификаторов + модуль якорей) | `25 passed, 1 warning in 1.87s` |
| ПОЛНЫЙ прогон без отбора маркером (`just test`) | `3410 passed, 1000 warnings in 2268.42s (0:37:48)`, rc=0 |
| `uv run python -m compileall -q app main.py tests` | rc=0 |
| `graphify update .` | `21059 nodes, 36784 edges, 1114 communities` |

## Числа, снятые до и после правки

| Величина | До | После |
|----------|----|-------|
| `grep -c 'pointer-events: none;' app/static/css/app.css` | 1 | 2 |
| `grep -c '^\.form-busy {$' app/static/css/app.css` | 1 | 1 |
| `grep -c '^def test_control\|^async def test_control' tests/test_templates/test_htmx_markup_gates.py` | 24 | 24 |
| `PANEL_QUALITY_DIFFERENCES_ALLOWED` | 2 | 2 |
| `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED` | — | 1 |

## Files Created/Modified

- `app/templates/components/form_wrapper.html` — литерал `class="form-wrapper"` в теге формы сразу после `hx-post`; пункт шапки-комментария о классе как области действия правила, о том, почему панель этого класса не получает, и почему атрибут стои́т именно там (сличение формы запуска синхронизации читает префикс тега; опора подстановки занимает хвост).
- `app/static/css/app.css` — правило `.form-wrapper { position: relative; }`, правило `.form-wrapper > .form-busy { position: absolute; right: 0; bottom: 0; pointer-events: none; }`, исключение `[data-group-row] form[action$="/toggle"] > .form-busy { position: static; }`; пять абзацев комментария раздела индикатора с замерами, основанием области, причиной нулевых смещений, ценой прозрачности для указателя и перечислением двух потребителей строчно-блочной коробки.
- `tests/test_templates/test_htmx_markup_gates.py` — константы области и величин, `InFlowIndicatorException` + перечень + число, помощники `_offenders_wrapped_indicator_footprint` и `_offenders_panel_indicator_reach`, тесты `test_a_wrapped_form_gives_its_indicator_no_layout_footprint` и `test_the_confirmation_panel_indicator_keeps_its_accepted_place`, опоры `CSS_WRAPPED_INDICATOR_OUT_OF_FLOW`, `CSS_WRAPPED_INDICATOR_RULE_OPEN`, `PANEL_FORM_TAG_OPEN`, поколения обоснования «имя класса формы» и абзаца раздела сличения.
- `tests/test_templates/test_components.py` — импорт сборщика обработчика профиля, тесты `test_the_reported_profile_form_carries_the_indicator_scope` и `test_the_panel_form_stays_outside_the_indicator_scope`.

## Decisions Made

Все шесть решений перечислены во frontmatter (`key-decisions`). Коротко: область задаёт третье имя; смещения нулевые; прозрачность для указателя есть митигация T-11-42; строка группы — объявленное исключение владельца; обоснование различия получило поколение, а не правку; управление пробелами не тронуто.

## Deviations from Plan

None — plan executed exactly as written.

Отдельно названы два места, где исполнитель принял решение ВНУТРИ рамки плана, а не отступил от неё:

1. **Ключи словаря нарушений помощника панели разведены** (`components/modal.html` для тега и `components/modal.html [класс области]` для набранного вне обёртки имени). План требовал «нарушение с селектором в ключе» и «нарушение обязано назвать тег панели»; под мутантом Б срабатывают ОБА условия, и общий ключ затёр бы одно другим.
2. **Порядок восстановления строки летописи в STATE.md.** Переустановка позиции перед партией закрытия гэпов затёрла строку `Last activity` плана 11-20 целиком (не понизив её в «устарело»). Строка восстановлена понижённой по идиоме D-30/D-32 — это бухгалтерия состояния, а не правка продукта.

## Issues Encountered

- **`check tdd-red-evidence` принимает TAP-запись `node --test`, а суита проекта — pytest.** Улика RED собрана МЕХАНИЧЕСКОЙ транскрипцией настоящего прогона (идентификаторы отказавших тестов и счётчики извлечены скриптом из вывода pytest, а не набраны руками) в форму, которую читает прибор; вердикт — `RED_EVIDENCE_OK`. Ручного сочинения улики не было.
- **Полный прогон идёт 38 минут** и через `| tail` не даёт промежуточного вывода; ожидание разрешено опросом процесса. На результат не влияет.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Готово к `/gsd-verify-work 11`.** Все 21 план фазы имеют сводки; полная суита зелена целиком (3410 passed, 0 failed).
- ⚠️ **Проверка 6 `11-UAT.md` остаётся открытой и ждёт ЧЕЛОВЕКА.** Файл обхода планом не тронут, таблица отметки пуста. Наблюдать нужно шесть пунктов, и пункт 5а — предмет отдельного взгляда: точка теперь стои́т ПОВЕРХ угла органа, поэтому смотреть надо (i) обёрнутую кнопку ряда — точка 8 px в её правом нижнем углу не должна закрывать подпись; (ii) тумблер шапки расписания высотой 40 px во ВКЛЮЧЁННОМ положении — точка не должна садиться на ручку, а нажатие по самому углу тумблера во время запроса обязано доходить до тумблера (`pointer-events: none`).
- **Остальные находки `11-UI-REVIEW.md` (2 и 3) в эту партию не входили** и остаются открытыми: ошибка поля баннером, цель блокировки формы правки расписания, фокус после подмены.

## Self-Check: PASSED

- `app/templates/components/form_wrapper.html` — FOUND (1 вхождение `class="form-wrapper"`, строка 163, сразу после `hx-post="{{ action }}"`)
- `app/static/css/app.css` — FOUND (`pointer-events: none;` 1 → 2, базовое правило `.form-busy` по-прежнему одно)
- `tests/test_templates/test_htmx_markup_gates.py` — FOUND (`IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED = 1`, `PANEL_QUALITY_DIFFERENCES_ALLOWED = 2`, оба новых теста по одному вхождению)
- `tests/test_templates/test_components.py` — FOUND (оба новых теста по одному вхождению)
- Коммиты `ec33c8e`, `810eaa7`, `bf3cb65` — FOUND в `git log`
- `git log --grep='11-21' -- app/templates/components/modal.html .planning/.../11-UAT.md` — пустой вывод (оба неприкосновенных файла не тронуты)
- `git status --porcelain -- app/static/css/app.css app/templates/components/modal.html` после возврата мутантов — пустой вывод
- Все `<acceptance_criteria>` обеих задач исполнены и сняты командами (таблицы выше)

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-17*

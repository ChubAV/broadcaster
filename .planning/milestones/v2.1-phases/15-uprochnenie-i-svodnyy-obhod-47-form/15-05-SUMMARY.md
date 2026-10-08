---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 05
subsystem: testing
tags: [htmx, jinja, markup-gates, pytest, gate-09, blind-zone, css]

requires:
  - phase: 08
    provides: "каркас гейтов разметки `test_htmx_markup_gates.py` (`_all_templates`, `_strip_comments`, `_sites`, `_attribute_count`, `_tree_with`, `_css_rules`, `_declaration`)"
  - phase: 15
    provides: "форма именованного нуля запрета FETCH-03 (`MANUAL_FETCH_SITES`, план 15-04)"
provides:
  - "ЗАПРЕТ условной сборки `hx-post` с явно пустым перечнем `CONDITIONAL_HX_POST_SITES` и контролями от вакуума (первая ветвь критерия 5 ROADMAP)"
  - "инвентарь настоящей слепой зоны: 12 мест вне макроса в трёх классах (2/2/8) + 6 раздающих ветвей `form_wrapper`, с полем приоритета наблюдения"
  - "машинная половина пункта 2 `human_verification`: правило `.banner-dismiss:focus-visible` объявлено в CSS"
affects: [15-10, 15-14, 15-07, "15-UAT.md пункт 9"]

actuals:
  tokens: 14120
  tasks: 3
  commits: 6
plan_head_before: 7cc15cfe8745499087e25cd69c37fc571eeb9fdd

tech-stack:
  added: []
  patterns:
    - "RED без стаба, переписываемого GREEN-ом: сборщик в RED — `found = {}` / `return found`, GREEN вставляет цикл между ними; каждый коммит — только добавления"
    - "предикат объявляется комментарием группы ВЫШЕ первого числа; числа сняты счётом по нему"
    - "перечень мест — отображение `путь#порядковый_номер` → запись; гейт сравнивает МНОЖЕСТВА ключей"

key-files:
  created: []
  modified:
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "RED обеих TDD-задач построен пустыми телами сборщиков, а не стабом, который GREEN переписал бы: критерий «в файл только добавления» и RED на утверждении (а не NameError) выполнены одновременно"
  - "HX_POST_MARKUP_PLACES = 3 заведён, как требует план, но как второй носитель числа HX_POST_PLACES — их равенство утверждает тот же тест"
  - "Число правил `.failure-stack` здесь НЕ объявлено (по action и acceptance задачи 3); строка <done> задачи 3, говорящая «объявлено равным 4», противоречит им и не исполнена — носитель числа план 15-07"
  - "Исключённые ветви form_wrapper утверждаются по (причина, условие), номера строк :182/:196 только в отказе — правка шапки макроса не краснит правило за форму"

patterns-established:
  - "Сеть «место условной сборки»: `_if_blocks` (стек, все ветви, незакрытое считается) + `_conditional_attributes` по тегу без комментариев"
  - "Две раздельные группы над одним исходником без дедупликации: `hx-post` — одна, прочие `hx-*` — другая"

requirements-completed: [GATE-09]

coverage:
  - id: D1
    description: "ЗАПРЕТ условной сборки `hx-post`: перечень объявлен ПУСТЫМ явно, найденное сравнивается с перечнем, пустота доказана синтетическим шаблоном `{% if x %}hx-post=\"/y\"{% endif %}`, изъятие тернарного значения `ads/form.html` утверждено на файле, 3 места разметки и 4 упоминания в прозе объявлены, разность отдельно"
    requirement: "GATE-09"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k conditional_hx_post (7 passed)"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_synthetic_conditional_hx_post_is_found_and_named"
        status: pass
    human_judgment: false
  - id: D2
    description: "Инвентарь слепой зоны: 12 мест вне макроса (вооружение опроса 2, внеполосная область 2, каскадная строка запроса 8) + 6 раздающих ветвей `form_wrapper`; летопись 8 → 6 доказана машинно; приоритет наблюдения — поле; контроли добавления (13) и снятия (11)"
    requirement: "GATE-09"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k \"conditional_hx_attributes or blind_zone or form_wrapper_branches\" (11 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Машинная половина пункта 2 `human_verification`: `.banner-dismiss:focus-visible` несёт `outline` на `var(--focus-ring)` и `outline-offset`; два контроля исчезновения"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k focus_ring (3 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Пункт 9 ручного UAT — наблюдение 12 мест слепой зоны в объявленном порядке приоритета"
    requirement: "GATE-09"
    verification: []
    human_judgment: true
    rationale: "Зелень гейтов пункт 9 НЕ закрывает: буквальный предмет пуст замером, а условия 12 мест вычисляются на рантайме, которого суита не исполняет (JS не исполняется, состояния `syncing` в браузере нет). Отметку ставит человек (D-17); раздел улики пишет план 15-14"
  - id: D5
    description: "Вторая половина пункта 2 `human_verification`: обвод фокуса ВИДЕН, не перекрыт, контрастен; пробел на `<input type=\"checkbox\">` снимает плашку"
    verification: []
    human_judgment: true
    rationale: "Суита CSS не раскладывает, страниц не рендерит и клавиш не нажимает; `app/static/css/app.css:1255-1258` запрещает объявлять отрисовку пройденной по зелени правил дословно"

duration: 20min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 05: Запрет условного `hx-post` и инвентарь слепой зоны Summary

**Запрет условной сборки `hx-post` с явно пустым перечнем, доказанный от вакуума синтетическим шаблоном; слепая зона пункта 9, объявленная числом и составом (12 мест в трёх классах вне макроса + 6 ветвей `form_wrapper`) с полем приоритета; и машинное утверждение обвода фокуса органа снятия в CSS. Всё в `tests/test_templates/test_htmx_markup_gates.py`, только добавления.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-24T07:49:45Z
- **Completed:** 2026-09-24T08:10Z
- **Tasks:** 3 (из них 2 TDD)
- **Files modified:** 1 (`tests/test_templates/test_htmx_markup_gates.py`, +1145 строк, 0 удалённых по всему плану)

## Accomplishments

- Первая ветвь критерия 5 ROADMAP закрыта гейтом: `CONDITIONAL_HX_POST_SITES: dict[str, str] = {}` с оговоркой «⚠️ ПЕРЕЧЕНЬ ПУСТ — ИМЕНОВАННЫЙ НОЛЬ, А НЕ ЗАБЫТОЕ ОБЪЯВЛЕНИЕ»; запрет сравнивает множество найденных ключей с перечнем, а не с `0`.
- Слепая зона объявлена числом, составом и приоритетом наблюдения; обе летописи записаны, вторая (8 → 6) доказана машинно называнием исключённых ветвей.
- Машинная половина пункта 2 `human_verification` утверждена; вторая половина прямо оставлена человеку с дословной цитатой запрета из CSS.

## Объявленный предикат (дословно, из шапки группы)

> МЕСТО УСЛОВНОЙ СБОРКИ — атрибут `hx-*`, чьё ПРИСУТСТВИЕ в теге зависит от Jinja-ветвления
> (`{% if %}` / `{%- if %}` внутри открывающего тега), либо чья строка запроса собрана
> `{% for %}`-циклом. Атрибут, присутствующий БЕЗУСЛОВНО, но получающий условное ЗНАЧЕНИЕ
> (тернарник Jinja внутри строки), местом условной сборки НЕ ЯВЛЯЕТСЯ: гейт разметки его видит, и
> слепой зоны он не создаёт.

Изъятие поимённо: `app/templates/ads/form.html:152` — `hx-post`, чьё значение есть тернарник, а сам
атрибут безусловен. Следствия, записанные в шапке: тег, целиком стоящий под `{% if %}` снаружи
(например `{% if has_next %}<div hx-get=…>`), местом не является; сеть считает условным атрибут,
напечатанный внутри блока `if`, даже если его печатают обе ветви `if`/`else` (строже предиката;
вне макроса таких мест 0, внутри одно — `hx-swap` ветви `target`).

## Замер буквального предмета пункта 9

Вхождений `hx-post` внутри `{% if %}` — **НОЛЬ**. Места разметки с `hx-post` — **3**
(`ads/form.html:152`, `components/form_wrapper.html:188`, `components/modal.html:807`); упоминаний
в прозе — **4** (`base.html:77`, `ads/includes/autosave_response.html:142`,
`components/form_wrapper.html:38`, `components/modal.html:465`); сырых вхождений 7, 7 − 3 = 4
утверждено отдельно и вторым путём (позиции внутри комментариев).

## Перечень слепой зоны (для раздела улики плана 15-14)

| Приоритет | Ключ | Класс | Раздаваемые `hx-*` | Строка (2026-09-24) |
|---|---|---|---|---|
| 1 | `account_groups/partials/sync_result.html#0` | вооружение опроса | `hx-get`, `hx-trigger`, `hx-swap` | :50 |
| 2 | `accounts/partials/sync_status_card.html#0` | вооружение опроса | `hx-get`, `hx-trigger`, `hx-swap` | :48 |
| 3 | `ads/includes/autosave.html#0` | внеполосная область | `hx-swap-oob` | :28 |
| 4 | `ads/includes/media_add_tile.html#0` | внеполосная область | `hx-swap-oob` | :55 |
| 5 | `ads/list.html#0` | каскадная строка запроса | `hx-get` | :61 |
| 6 | `ads/partial_cards.html#0` | каскадная строка запроса | `hx-get` | :7 |
| 7 | `schedules/list.html#0` | каскадная строка запроса | `hx-get` | :66 |
| 8 | `schedules/partial_cards.html#0` | каскадная строка запроса | `hx-get` | :12 |
| 9 | `history/list.html#0` | каскадная строка запроса | `hx-get` | :119 |
| 10 | `history/partial_cards.html#0` | каскадная строка запроса | `hx-get` | :6 |
| 11 | `admin/user_history.html#0` | каскадная строка запроса | `hx-get` | :63 |
| 12 | `admin/history_partial_cards.html#0` | каскадная строка запроса | `hx-get` | :7 |

Класс 4 (внутри макроса), `components/form_wrapper.html`: 6 раздающих ветвей — `target` (`hx-target`,
`hx-swap`, :189), `trigger` (:191), `sync` (:192), `encoding` (`hx-encoding`, :193), `include` (:194),
`disabled_elt` (:195). `hx-post` и `hx-indicator` макроса безусловны — это утверждено машинно и есть
довод, почему запрет условного `hx-post` законно пуст.

Основание приоритета: класс 1 несёт `hx-trigger="every 5s"` только в ветке `status == 'syncing'`, то
есть контракт останова опроса GATE-08 держится на ветвлении, которого гейт разметки не видит;
поломка условия — застывший экран или бесконечный опрос.

## Летописи

1. **«12 мест в ЧЕТЫРЁХ классах» → «12 мест в ТРЁХ классах вне макроса + 6 ветвей внутри, всего 18»**
   (план 15-05). Замер Ф-08 верен по числу 12 и составу трёх классов; ярлык «четыре класса» относил
   к двенадцати класс макроса, в 12 не входивший. «ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ…» Новое число
   снято счётом по объявленному предикату.
2. **«8 ветвей `{%- if %}` в `form_wrapper`» → «6 раздающих `hx-*`»** (план 15-05). Наивная сеть даёт 8
   (верный замер своей сети); исключены `:182` (внутри докстринга макроса) и `:196`
   (`{%- if caller is defined %}{{ caller() }}`). Разность доказана тестом
   `test_form_wrapper_branches_naive_count_exceeds_the_dispensing_by_the_two_named_lines`, прогон
   назвал ровно эти строки.

## Замер «атрибуты `hx-*` из `app/pages/`»

`grep -rn 'hx-' app/pages/` — 6 строк, все проза: 3 в докстрингах (`ads.py:733`, `:830`, `:833`) и 3 в
комментариях (`ads.py:1073`, `account_groups.py:543`, `schedules.py:1635`); сеть плана с
`grep -v '^.*#'` оставляет 3 докстринговые. Атрибутов `hx-*`, приходящих в контекст готовой строкой,
**0**; в прочем Python-коде `app/` строк `hx-` нет. Появление первого такого места сеть по тексту
шаблона не заметит, и в шапке группы это записано как граница, а не как покрытие.

## ⚠️ Пункт 9 НЕ закрыт

Зелень обеих групп пункт 9 ручного UAT **не закрывает**. Буквальный предмет пуст по замеру. Человеку
подаются 12 мест в порядке приоритета из таблицы выше, и отметку о закрытии ставит он (D-17). Раздел
улики в `15-UAT.md` пишет план 15-14.

## Task Commits

1. **Task 1: запрет условного `hx-post`**: RED `5104c871` (test), GREEN `87091108` (feat)
2. **Task 2: инвентарь слепой зоны**: RED `c5bdba58` (test), GREEN `5c3491ae` (feat); перенос строки в формуле летописи `16351ade` (style)
3. **Task 3: обвод фокуса в CSS**: `8b8211fa` (feat)

## TDD Gate Compliance

- Задача 1: `test(15-05)` 5104c871 → `feat(15-05)` 87091108. RED-улика: `-k conditional_hx_post`, код 1,
  7 тестов / 1 провал, целевой `test_control_negative_a_synthetic_conditional_hx_post_is_found_and_named`
  упал на `AssertionError` (`'synthetic/conditional_post.html#0' in {}`); `check tdd-red-evidence` →
  `RED_EVIDENCE_OK`. Сам запрет в RED был зелен (вакуумно), и это ровно то, что план предсказал.
- Задача 2: `test(15-05)` c5bdba58 → `feat(15-05)` 5c3491ae. RED-улика: 11 тестов / 11 провалов, целевой
  `test_conditional_hx_attributes_outside_the_macro_are_the_declared_twelve` упал на `assert 0 == 12`;
  `RED_EVIDENCE_OK`.
- Запись улики собрана из того же прогона (`--junit-xml`, переведённый в TAP одноразовым скриптом во
  временном каталоге; скрипт не закоммичен). Шагов REFACTOR не было.

## Verification

| Команда | Итог |
|---|---|
| `-k conditional_hx_post` | 7 passed (≥ 7) |
| `-k "conditional_hx_attributes or blind_zone or form_wrapper_branches"` | 11 passed (≥ 9) |
| `-k focus_ring` | 3 passed (≥ 3) |
| `tests/test_templates/test_htmx_markup_gates.py` | 104 passed (до правки 83) |
| `tests/test_templates/` | 307 passed (до правки 286; порог плана 236 устарел: планы 15-02…04 уже подняли его до 286) |
| `uv run python -m compileall -q app main.py tests` | молчание, код 0 |
| `tests/test_planning/` | 78 passed |
| `grep -c rglob` модуля | 2 до и после |
| `grep -c FAILURE_STACK_RULES` модуля | 0 |
| удалённых строк по плану (`git diff 7cc15cfe..HEAD`) | 0; тронут один файл, `app/` не тронут |

Полная суита не запускалась: её после волны гонит оркестратор, и окно 101 уже покрывает этот
прогон. Вместо неё прогнаны целевой модуль, весь `tests/test_templates/` и `tests/test_planning/`.

## Decisions Made

См. `key-decisions` во frontmatter. Главное: RED без стаба, который GREEN переписал бы (пустые тела
сборщиков, GREEN вставляет цикл). Так соблюдаются одновременно критерий «только добавления» и RED на
утверждении.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Формула летописи разорвана переносом строки**
- **Found during:** Task 2 (проверка приёмки)
- **Issue:** в первой летописи «ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН / УСТАРЕЛ» стояла на двух строках
  комментария, и грепом дословная фраза находилась лишь один раз из двух.
- **Fix:** перенос строки убран. Тронуты только строки, добавленные этим планом; по плану в целом
  удалённых строк 0.
- **Files modified:** tests/test_templates/test_htmx_markup_gates.py
- **Verification:** `grep -c 'ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ'` → 2; модуль 101 passed
- **Committed in:** 16351ade (отдельный `style(15-05)`; в диффе этого коммита есть строки `-`, но все
  они принадлежат тексту, добавленному в c5bdba58)

### Plan-text inconsistencies resolved (not code deviations)

- `<done>` задачи 3 говорит «число правил `.failure-stack` объявлено равным 4 с летописью 6 → 4», а
  `<action>` и `<acceptance_criteria>` той же задачи это ЗАПРЕЩАЮТ (`grep -c FAILURE_STACK_RULES` = 0,
  носитель — план 15-07). Исполнено по action и acceptance: число здесь не объявлено, граница и
  адресат названы.
- Артефакт `FAILURE_STACK_SELECTOR_BOUNDARY_NOTE` назван «только докстринг, без литерала числа».
  Поэтому он записан абзацем комментария с этим именем, а не константой.
- Сверх перечисленных тестов добавлены два, закрывающие must_haves явно: смежность (место с условными
  `hx-post` и `hx-swap` считают обе группы) и кодировка (узкий пробел в `every 5s` не классифицируется
  как опрос).

**Total deviations:** 1 auto-fixed (Rule 1). **Impact:** только форма комментария; утверждения не менялись.

## Issues Encountered

None.

## Known Stubs

None. `CONDITIONAL_HX_POST_SITES = {}` — объявленный именованный ноль, а не заглушка: он стережётся
синтетическим контролем и контролем пустой вселенной.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 15-10 (волна 2) может строить на `_conditional_attributes`, `_if_blocks`, `_conditional_hx_sites`,
  `CONDITIONAL_HX_SITES`.
- План 15-14 берёт таблицу слепой зоны выше в раздел улики пункта 9 `15-UAT.md`.
- План 15-07 — единственный носитель числа правил `.failure-stack` и летописи `6 → 4 → 5`.
- `requirements.ready-ids` для GATE-09 (только чтение): `ready: []`, `blocked: [GATE-09]` — его
  объявляют и соседние планы. `mark-complete` не вызывался: требование отмечает закрытие фазы после
  верификации.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- Файл `tests/test_templates/test_htmx_markup_gates.py` на месте; коммиты 5104c871, 87091108, c5bdba58, 5c3491ae, 16351ade, 8b8211fa, 8f2d768f найдены.
- `tests/test_planning/` после коммита сводки — 78 passed.

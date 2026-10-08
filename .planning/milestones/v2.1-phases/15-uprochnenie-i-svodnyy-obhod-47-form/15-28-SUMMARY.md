---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 28
subsystem: testing
tags: [prohibitions-census, registry, record-mode, failure-banner, app-css, lift, stack, scroll-lock, criterion-6, g-1, d-16, pytest]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-27 — модуль `tests/test_pages/test_failure_banner_invariants.py` и образец замера мутацией дерева; план 15-24 — протокол строки; план 15-22 — режим `--record`; план 15-19 — записи `app.css` о стопке (поправка поля набора, непрозрачный `--focus-ring`)"
  - phase: 10-rychag-components-modal-html
    provides: "девять запретов `product-invariant` о блоке подъёма, стопке и блокировке прокрутки (планы 10-33, 10-51, 10-56, 10-57); безусловный подъём (план 10-51)"
provides:
  - "девять строк группы «подъём и стопка заготовок в таблице стилей» — `enforced`; у каждой правило, покрасневшее на временной правке `app.css` (или рычага) по формулировке ИМЕННО этой строки"
  - "в модуле плашки: 6 правил, 6 контролей; `FAILURE_BANNER_LIFT_BLOCK`, `FAILURE_BANNER_BASE_OFFSET`, `SCROLL_LOCK_SELECTORS`, разбор достижимости узла по селектору (`_selector_reaches`, узел снят из шаблона)"
  - "замещённая строка `10-33#0` передана чекпойнту плана 15-32 поимённо, с обеими формулировками"
affects: [15-29, 15-30, 15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 8760
  tasks: 2
  commits: 3
plan_head_before: b2a6b3998ab7778579b333f1ccdcbdd58c4da12b

tech-stack:
  added: []
  patterns:
    - "Достижимость узла блоком таблицы — разбором: последняя составная часть одного из селекторов списка сличается с открывающим тегом узла, снятым из шаблона, и обязана НАЗЫВАТЬ узел идентификатором, классом или признаком; часть из одного `*`/тега/псевдокласса не считается (иначе правило краснело бы за чужие блоки вида `[data-row] > *`)"
    - "Запрет «блок не правится» при законно правленных соседях — посимвольное сличение ОДНОГО блока (селектор и тело раздельно в отказе) и контроль точности на правке соседнего блока"

key-files:
  created: []
  modified:
    - tests/test_pages/test_failure_banner_invariants.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-28: одна строка (`10-56#1`) держится действующими правилами целиком — четыре правила подъёма `test_shell.py` покраснели на втором блоке с идентификатором заготовки (l3, l5, l5b); у восьми остальных найдены формы нарушения, на которых действующие правила зелены"
  - "15-28: сверх двух правил плана написаны ещё четыре — на `10-56#2`/`10-57#8` (перестановка частей и пробелы в селекторе, правка тела блока подъёма зелены), `10-56#4` (согласованный сдвиг базы, смещения и снятия зелен), `10-56#3`/`10-57#8`/`10-57#9` (`all: initial`/`all: unset`, признак идентификатора `[id^=…]` зелены), `10-33#3` (собственный блок подъёма `#notice-alert` зелен)"
  - "15-28: достижимость считается только у части, НАЗЫВАЮЩЕЙ узел; замер дерева — пять блоков с универсальным субъектом (`*`, `[data-row] > *` и др.) иначе «достигали» узлов, и будущая правка любого из них краснила бы правило подъёма за форму"
  - "15-28: `10-33#0` («безусловный подъём не заводится») не записан — замещён планом 10-51 (`34ac7747`), правило условного подъёма не писалось; передан чекпойнту 15-32"
  - "15-28: запись `10-51#2` называет и `test_failure_stack_rule_count_is_declared` (`test_banner_dismiss.py`) — оно покраснело на втором блоке класса стопки (l4, l4c), но не на признаке идентификатора (l4b)"

patterns-established:
  - "Для запрета о блоке таблицы замерять ВСЕ формы правки по отдельности: приписку, перестановку, пробелы, правку тела, второй блок иным селектором (класс, признак, пара классов), сокращение `all`"

requirements-completed: []

coverage:
  - id: D1
    description: "`10-56#1` записан `enforced` четырьмя действующими правилами подъёма, каждое покраснело на l3, l5, l5b"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_lift_is_unconditional"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_is_declared_above_the_panel"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_lift_declares_no_display_mode"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_two_failure_banners_do_not_share_one_rectangle"
        status: pass
      - kind: other
        ref: "red28.sh l5/l5b × 4 правила, l3 × 1 → RED_EVIDENCE_OK ×9"
        status: pass
    human_judgment: false
  - id: D2
    description: "6 новых правил и 6 контролей в модуле плашки; восемь строк записаны `enforced` с действующими и новыми правилами; каждое новое правило покраснело на мутации, где действующие зелены"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_failure_banner_invariants.py (20 passed)"
        status: pass
      - kind: other
        ref: "node .claude/gsd-core/bin/gsd-tools.cjs check tdd-red-evidence <запись> → RED_EVIDENCE_OK ×44 (22 действующих + 22 новых, новые перемерены после правки достижимости)"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
      - kind: integration
        ref: "uv run pytest <модуль> test_htmx_gates.py test_htmx_post_pairs.py test_hx_location_destinations.py test_shell.py test_responsive_markup.py tests/test_templates/ tests/test_planning/ -q -p no:randomly → 1124 passed (b7a16728)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Передача `10-33#0` чекпойнту 15-32 и верность суждения «правило держит ВЕСЬ предмет формулировки» по девяти строкам"
    verification: []
    human_judgment: true
    rationale: "Снятие замещённой формулировки (D-30/D-32) — решение владельца. Полноту перечня форм нарушения (какие формы правки «ни на символ», «ни в каком виде» считать) машина не выводит — суждение исполнителя (D-33 плана 15-13)"

duration: 55min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 28: Принуждение девяти запретов о подъёме и стопке заготовок в таблице стилей Summary

**Все девять запретов `product-invariant` группы «подъём и стопка заготовок в таблице стилей» записаны `enforced`. `10-56#1` держат четыре действующих правила подъёма `test_shell.py` целиком. У восьми остальных нашлись формы нарушения, на которых действующие правила зелены, и их держат шесть новых правил модуля `tests/test_pages/test_failure_banner_invariants.py` вместе с действующими: блок подъёма один (счёт по разбору селектора), `overflow: hidden` у признака блокировки прокрутки, блок подъёма посимвольно, база первой заготовки `12px`, у узла заготовки нет показывающего `display` и нет `all`, область `#notice-alert` не поднимается. Каждое правило записи покраснело на временной правке `app.css` (или рычага) по формулировке своей строки. Замещённый `10-33#0` не записан и передан плану 15-32. `app/` не правился.**

## Performance

- **Duration:** 55 min (из них около 30 мин — прогоны: широкая сеть 28 мутаций, 44 целевых RED-прогона, гейты 15.6 мин)
- **Started:** 2026-09-25T19:51:30Z
- **Completed:** 2026-09-25T20:47:18Z
- **Tasks:** 2
- **Files modified:** 2 (модуль правил, реестр)

## Замер направления

Каждая мутация — временная правка `app/static/css/app.css` (у l15 — `app/templates/components/modal.html`). Порядок: запись, прогон, `git checkout -- <файл>`, затем `git diff --exit-code -- app/`. Драйвер в scratchpad (`mutate28.py`, не в дереве) отказывает до правки, если якорь не единствен. Так было с l12/l12b: якорь базового блока оказался хвостом блока снятия (`.failure-stack[hidden] + .failure-stack {…`). Якорь удлинили строкой шага и прогнали заново. После каждой мутации было `clean=True`, в конце `APP_CLEAN`.

Широкая сеть действующих правил — `test_shell.py`, `test_components.py`, `test_banner_dismiss.py`, `test_htmx_markup_gates.py` с `-k "lift or stack or banner or scroll_lock or display or panel or layer or offset or ancestor or lever or notice or dismiss or focus"`: 137 тестов, на чистом дереве все зелены. Полные модули на мутацию не гонялись: один прогон четырёх модулей идёт 11.5 мин.

| Мутация | Правка | Действующие правила (сеть) | Новые правила |
|---|---|---|---|
| l1 | `#notice-alert` дописан в селектор блока подъёма | `3 failed`: `lift_is_unconditional` («ПОДЪЁМ ЗАГОТОВОК ОБУСЛОВЛЕН … получен селектор: …, #notice-alert») и два его контроля | область: «`#htmx-failure-server, #htmx-failure-network, #notice-alert`: position: fixed — область `#notice-alert` включена в подъём»; блок подъёма: «ИЗМЕНЁН (СЕЛЕКТОР)» |
| l2 | собственный блок `#notice-alert { position: fixed; top: 12px; z-index: 70; }` | **`137 passed`** | область: «`#notice-alert`: position: fixed …», «z-index: 70 …» |
| l3 | второй блок `#htmx-failure-network { z-index: 71; }` | `10 failed`: `is_declared_above_the_panel` («блоков подъёма … 2, а не один»), `lift_is_unconditional`, `declares_no_display_mode`, `two_banners_do_not_share_one_rectangle` и шесть контролей (отказ «на настоящей таблице» — не названная причина) | один блок: «БЛОКОВ ПОДЪЁМА ЗАГОТОВОК В ТАБЛИЦЕ 2» |
| l4 | второй блок `.failure-stack { z-index: 71; }` (контроль плана) | `1 failed`: `test_failure_stack_rule_count_is_declared` («перечень правил `.failure-stack` разошёлся … получено (6)») | один блок: «… 2 …» |
| l4b | второй блок `[id="htmx-failure-server"] { position: fixed; top: 40px; }` | **`137 passed`** | один блок: «… 2 …» |
| l4c | второй блок `.failure-stack + .failure-stack { z-index: 71; }` | `1 failed`: `failure_stack_rule_count_is_declared` | один блок: «… 2 …» |
| l5 / l5b | второй блок с идентификатором без слоя: `#htmx-failure-server:focus-within { outline: 0; }` / `body #htmx-failure-network { color: red; }` | `10 failed` каждая, те же четыре правила подъёма («блоков подъёма в таблице 2») | один блок **зелен** (слоя и положения нет — это не подъём); блок подъёма: «сличать не с чем» |
| l6 | `:not([hidden])` у части селектора подъёма | `3 failed`: `lift_is_unconditional` | блок подъёма: «ИЗМЕНЁН (СЕЛЕКТОР)» |
| l7 | перестановка частей селектора | **`137 passed`** | блок подъёма: «ИЗМЕНЁН (СЕЛЕКТОР) с символа …» |
| l8 | `#htmx-failure-server, #htmx-failure-network` (только пробелы) | **`137 passed`** | блок подъёма: «ИЗМЕНЁН (СЕЛЕКТОР)» |
| l9 | `display: block` в блоке подъёма | `5 failed`: `declares_no_display_mode` («ОБЪЯВЛЯЕТ способ отображения (block)»), `no_banner_rule_declares_a_display_mode_that_shows`, `dismissing_one_banner_leaves_the_other_shown` и два контроля | способ отображения: «display: block»; блок подъёма: «ИЗМЕНЁН (ТЕЛО)» |
| l9b | `display: none` в блоке подъёма | `4 failed`: `declares_no_display_mode` («(none)») и др. | блок подъёма: «ИЗМЕНЁН (ТЕЛО)»; способ отображения **зелен** (`none` допустим) |
| l10 | `all: initial;` первым объявлением блока подъёма | **`137 passed`** | способ отображения: «all: initial — сокращение объявляет и способ отображения»; блок подъёма: «ИЗМЕНЁН (ТЕЛО)» |
| l11 / l11b | ширина `560px` → `600px` / слой `70` → `75` | **`137 passed`** | блок подъёма: «ИЗМЕНЁН (ТЕЛО)» |
| l12 | база `.failure-stack` `12px` → `16px` | `1 failed`: `a_single_shown_banner_keeps_the_base_offset` («БЛОК СНЯТИЯ СМЕЩЕНИЯ ОБЪЯВЛЯЕТ НЕ БАЗОВОЕ ЗНАЧЕНИЕ … 16px … 12px») | база: «ПОЛОЖЕНИЕ ПЕРВОЙ ЗАГОТОВКИ СДВИНУТО … 16px» |
| l12b | согласованный сдвиг базы, смещения `calc(16px + …)` и снятия на `16px` | **`137 passed`** | база: «… СДВИНУТО … 16px» |
| l13 / l13b | правило скрытия `display: block` / `display: contents` | `3–4 failed`: `no_banner_rule_declares_a_display_mode_that_shows` («получено: display: block / contents»), сторож 15-19 и его контроль | способ отображения: названо |
| l13c | иной блок `.failure-stack + .failure-stack { display: flex; }` | `4 failed`: `no_banner_rule_declares_…` («display: flex»), `dismissing_one_banner_…`, `failure_stack_rule_count_…` | способ отображения: названо |
| l13d | `[id^="htmx-failure"] { display: block; }` | **`137 passed`** | способ отображения: «`[id^="htmx-failure"]`: display: block» |
| l13e | правило скрытия `{ display: none; all: unset; }` | `1 failed` — только контроль 15-19 `control_a_silently_fixed_or_dropped_consequence_reddens` на отсутствии якоря («встречается 0 раз») — **не названная причина** | способ отображения: «all: unset» |
| l14 | блок `.is-modal-open, .is-modal-open body {}` без объявления | **`137 passed`** | блокировка: две находки «селектор жив, а объявления `overflow` … НЕТ» |
| l14b | `overflow: auto` | **`137 passed`** | блокировка: «объявлено `overflow: auto`» ×2 |
| l14c | блок блокировки снят целиком | `1 failed`: `the_panel_raises_the_scroll_lock_when_it_opens` («селектора .is-modal-open в app.css нет») | блокировка: «блока с этим селектором в таблице НЕТ» ×2 |
| l14d | снята часть `.is-modal-open body` | **`137 passed`** | блокировка: «`.is-modal-open body`: блока … НЕТ» |
| l15 | рычаг перестал поднимать признак (`classList.add('is-modal-open')` снят) | `11 failed`: `the_lever_raises_the_scroll_lock_flag` («рычаг перестал поднимать признак `is-modal-open` ГЛАГОЛОМ»), `the_panel_raises_the_scroll_lock_when_it_opens` («после show() признака is-modal-open на документе нет») и др. | новые **зелены** (предмет — таблица, не рычаг) |

## Таблица строк

| Строка | Формулировка (сокращённо) | Правило(а) записи | Замер, давший красное | Запись |
|---|---|---|---|---|
| `10-56#1` | второго блока, чей селектор содержит идентификатор заготовки, не заводится | `test_shell.py::test_the_failure_banner_lift_is_unconditional`, `…::test_the_failure_banner_is_declared_above_the_panel`, `…::test_the_failure_banner_lift_declares_no_display_mode`, `…::test_the_two_failure_banners_do_not_share_one_rectangle` | l3, l5, l5b (все четыре) | задача 1, `enforced` |
| `10-33#3` | `#notice-alert` в подъём не включается | `…::test_the_failure_banner_lift_is_unconditional`; **новое** `test_failure_banner_invariants.py::test_the_notice_region_is_not_lifted` | l1 (оба); **l2 — только новое** | задача 2, `enforced` |
| `10-51#2` | второго блока подъёма не заводится (было `partially-enforced`) | `…::test_the_failure_banner_lift_is_unconditional`; `test_banner_dismiss.py::test_failure_stack_rule_count_is_declared`; **новое** `…::test_exactly_one_stylesheet_block_lifts_the_failure_banners` | l3 (первое и новое); l4, l4c (счёт стопки и новое); **l4b — только новое** | задача 2, `enforced` |
| `10-51#3` | правило блокировки прокрутки и признак `is-modal-open` не снимаются (было `partially-enforced`) | `test_components.py::test_the_panel_raises_the_scroll_lock_when_it_opens`; `test_shell.py::test_the_lever_raises_the_scroll_lock_flag`; **новое** `…::test_the_modal_open_mark_declares_the_scroll_lock` | l14c, l15 (действующие); **l14, l14b, l14d — только новое**; l14c — и новое | задача 2, `enforced` |
| `10-56#2` | селектор блока подъёма не правится ни на символ | `…::test_the_failure_banner_lift_is_unconditional`; **новое** `…::test_the_failure_banner_lift_block_is_unchanged` | l6 (оба); **l7, l8 — только новое** | задача 2, `enforced` |
| `10-56#3` | блок подъёма не объявляет способа отображения ни в каком виде | `…::test_the_failure_banner_lift_declares_no_display_mode`; **новое** `…::test_no_block_reaching_a_failure_banner_shows_it_through_display_or_all` | l9, l9b (действующее), l9 (и новое); **l10 — только новое** | задача 2, `enforced` |
| `10-56#4` | положение первой заготовки не сдвигается | `…::test_a_single_shown_banner_keeps_the_base_offset`; **новое** `…::test_the_first_failure_banner_keeps_its_measured_offset` | l12 (оба); **l12b — только новое** | задача 2, `enforced` |
| `10-57#8` | блок подъёма и селектор не правятся, способ отображения не объявляется | `…::test_the_failure_banner_lift_is_unconditional`; `…::test_the_failure_banner_lift_declares_no_display_mode`; **новые** `…::test_the_failure_banner_lift_block_is_unchanged`, `…::test_no_block_reaching_a_failure_banner_shows_it_through_display_or_all` | l6, l9 (действующие); **l7, l8, l11, l11b — только блок подъёма; l10 — оба новых** | задача 2, `enforced` |
| `10-57#9` | правило скрытия объявляет способ отображения только значением «нет» | `…::test_no_banner_rule_declares_a_display_mode_that_shows`; **новое** `…::test_no_block_reaching_a_failure_banner_shows_it_through_display_or_all` | l13, l13b, l13c (действующее и новое); **l13d, l13e — только новое** | задача 2, `enforced` |

## Передано плану 15-32

Не записан этим планом. Прежняя диспозиция не тронута (`--list`: `10-33#0` — `unresolved`, `enforcement-required`).

**`10-33#0` — формулировка замещена.**
- Формулировка: «БЕЗУСЛОВНЫЙ подъём плашки не заводится: сценарий включения снятую плашку обратно НЕ ПРЯЧЕТ (записанное допущение Фазы 8), и подъём вне состояния открытой панели оставил бы человеку вечный прямоугольник поверх экрана после одного обрыва связи».
- Чем замещена: план 10-51 (`34ac7747`, 2026-09-11, «подъём заготовок плашки отказа становится безусловным»; гэп G-10-7 обхода `walkthrough_3`) снял с селектора признак-предок `.is-modal-open`. Формулировка `10-51#2` той же ветви: «…блок остаётся ОДИН, меняется его селектор». Опасение формулировки («вечный прямоугольник после одного обрыва связи») закрыли ПОЗДНЕЕ: третий обработчик плана 10-49 гасит заготовки на удачном обмене, а выход у плашки завёл план 10-57 (ветвь `A`).
- Замер: блок подъёма в дереве — `#htmx-failure-server,\n#htmx-failure-network {…}` без условия. Действующее правило `test_the_failure_banner_lift_is_unconditional` утверждает обратное формулировке и краснеет на возвращённом условии (l6, `:not([hidden])`). Правило по формулировке было бы красно на дереве, поэтому оно не писалось (запрет плана: «MUST NOT писать правило условного подъёма»).
- Решение за владельцем: снять формулировку как замещённую (D-30/D-32).

## Accomplishments

- **Задача 1.** 28 мутаций. `10-56#1` записан `enforced` четырьмя действующими правилами, каждое покраснело по названной причине («блоков подъёма в таблице 2, а не один»). Для восьми остальных строк найдены формы нарушения, на которых вся сеть из 137 действующих правил зелена: l2, l4b, l7, l8, l10, l11, l11b, l12b, l13d, l14, l14b, l14d. Сверх них — l13e, где красен только контроль 15-19 и только на отсутствии якоря.
- **Задача 2.** В модуль плашки добавлено 6 правил и 6 контролей. Из `test_shell.py` ввезены разборщики таблицы (`_css_rules_of`, `_css_declarations`, `_css_rule_block`, `_selector_compounds`, `_compound_simple_selectors`, `_banner_elevation_rules`, `_stack_blocks`, `_scratch_stylesheet`, `_stylesheet_source`) и константы. Второго разбора таблицы модуль не заводит. Свои в нём только сличение составной части с узлом, снятым из шаблона (`_node_of`, `_compound_may_match`, `_attribute_may_match`), и деление списка селекторов по запятой вне скобок. Докстринг модуля дополнен по форме D-16: предмет с тождествами, замещённый `10-33#0` назван, в «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» появились границы разбора.
- **Реестр.** `product-invariant` было `enforced 41 / partially-enforced 6 / unresolved 23`, стало `50 / 4 / 16`. Сумма по диспозициям области решений — 321, биекция в согласии. Дифф реестра — ровно 9 строк: 1 в задаче 1 и 8 в задаче 2.

## Task Commits

1. **Задача 1: замер по действующим правилам** — `a658fe17` (chore): `10-56#1` записан `enforced`.
2. **Задача 2: новые правила** — `b758c8dc` (test): шесть правил и шесть контролей; `b7a16728` (chore): восемь строк записаны `enforced`.

**Plan metadata:** коммит сводки `docs(15-28)`, следом коммит учёта STATE/ROADMAP.

## TDD

План имеет `type: execute` при `workflow.tdd_mode: true`, поэтому гейт TDD на нём инертен. Продукт не правится, и цикла «красный тест → правка продукта → зелёный» здесь нет. **RED каждой строки измерен по правилу владельца (Г-1): правило засчитано, только если покраснело на нарушении формулировки своей строки.**

- **Как измерено.** `red28.sh <мутация> <узел>` (scratchpad) прогоняет ОДИН узел правила на мутированном дереве: `uv run pytest -q -p no:randomly --junit-xml=… <узел>`. Затем идёт возврат и проверка `git diff --exit-code -- app/`. Одноразовый `junit2red.py` (scratchpad 15-27, не в дереве) собирает запись `{command, exitCode, targetTest, output}` с выводом в форме node:test TAP, и по ней отрабатывает `check tdd-red-evidence`.
- **Действующие правила:** 22 целевых прогона на l1, l3, l4, l4c, l5, l5b, l6, l9, l9b, l12, l13, l13b, l13c, l14c, l15. У каждого `FAILED <узел>`, `1 failed, 1 warning`, `exit=1`, `RED_EVIDENCE_OK/target_test_failed`. Причинные литералы приведены в таблице замера. Отказы контролей «правило КРАСНО на настоящей таблице» (l3, l5, l9) — это отказ гарнира контроля, а не названная причина, и уликой RED они **не** заявлены. Не заявлен и l13e: там покраснел только контроль 15-19 на пропавшем якоре.
- **Новые правила:** 22 целевых прогона. Один блок — l3, l4, l4b, l4c. Блокировка — l14, l14b, l14c, l14d. Блок подъёма — l6, l7, l8, l10, l11, l11b. База — l12, l12b. Способ отображения — l9, l10, l13d, l13e. Область — l1, l2. Каждый дал `FAILED tests/test_pages/test_failure_banner_invariants.py::<правило>`, `1 failed, 1 warning`, `exit=1`, `RED_EVIDENCE_OK/target_test_failed`. Все 22 прогона **перемерены** после правки достижимости (см. отклонение 2), и итог тот же. Прогон шести правил по всем 28 мутациям до и после правки дал один и тот же перечень красных (`diff` пуст).
- **Контроли точности на дереве:** l5/l5b (второй блок с идентификатором, без слоя) — правило «один блок» зелено: это не подъём, и его держат четыре правила `10-56#1`. l9b (`display: none` в подъёме) — правило способа отображения зелено, этот случай держит `declares_no_display_mode`. l15 (правка рычага) — все шесть новых правил зелены.
- **Контроли на синтетике** (в модуле). Второй блок подъёма назван в четырёх формах (класс, пара классов, признак, идентификатор). Не названы блок потомка `.failure-stack > .alert`, псевдоэлемент `::before`, чужой класс и `[data-row] > *`. Снятое, ослабленное и половинное `overflow` названы, а `overflow` у `.modal` — нет. Перестановка, пробелы, признак состояния и ширина в блоке подъёма названы с частью (СЕЛЕКТОР/ТЕЛО), правка шага стопки — нет. Согласованный сдвиг базы назван, правка шага — нет. Показывающее значение в правиле скрытия, `[id^=…]`, `all: initial`, `all: unset` названы; псевдоэлемент, потомок и `[data-dashpair] > *` — нет. `#notice-alert` в селекторе подъёма и собственным блоком назван, а `position: relative` и `[data-row] > *` — нет. Каждый контроль сначала утверждает, что боевое дерево по его правилу чисто.
- Коммит `test(15-28)` предшествует записям второй задачи. Коммита `feat(15-28)` нет: продукт не правился. REFACTOR не было.

## Files Created/Modified

- `tests/test_pages/test_failure_banner_invariants.py` — раздел «Подъём и стопка» (+677 строк), докстринг модуля дополнен.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поля меры покрытия у 9 строк, записаны только через `--record`.

## Decisions Made

См. `key-decisions`. Кратко:
- Литералы сняты с дерева и сличены по истории `app.css`. Блок подъёма не менялся с `9583ca4e` (план 10-56), селектор — с `34ac7747` (план 10-51). База `12px` стояла литералом `top: 12px` с `48d5788e` (план 10-33) и перенесена величиной планом 10-56. Блок блокировки прокрутки стоит с `03266943` (план 09-13).
- «Блок подъёма» в `10-51#2` — это блок, достигающий узла заготовки и объявляющий `z-index` или `position`. План назвал только `z-index`, положение добавлено как вторая величина той же копии («вторая копия величин»). На дереве такой блок один.
- «Ни в каком виде» (`10-56#3`) и «только значением «нет»» (`10-57#9`) включают сокращение `all`: `all: initial`/`unset` объявляют `display` автором и перебивают атрибут скрытия. Правило называет любое `all` у узла заготовки.
- Правило блокировки прокрутки требует оба замеренных селектора (`.is-modal-open` и `.is-modal-open body`) с последним `overflow: hidden`. Перенос на `overflow-y` правило назовёт. Граница записана в докстринге: это новое решение владельца, а не починка.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Четыре правила сверх двух запланированных**
- **Found during:** задача 1 (l2, l7, l8, l10, l11, l11b, l12b, l13d, l13e)
- **Issue:** план поручал `10-33#3`, `10-56#2`, `10-56#3`, `10-56#4`, `10-57#8`, `10-57#9` действующим кандидатам («кандидат найден»). Замер показал, что на этих формах нарушения вся сеть из 137 правил зелена.
- **Fix:** по протоколу строки (шаг 4, частичное покрытие) написаны правила на остаток — `test_the_failure_banner_lift_block_is_unchanged`, `test_the_first_failure_banner_keeps_its_measured_offset`, `test_no_block_reaching_a_failure_banner_shows_it_through_display_or_all`, `test_the_notice_region_is_not_lifted` — каждое со своим контролем. Строки записаны с действующими и новыми правилами.
- **Files modified:** модуль правил, реестр
- **Commit:** `b758c8dc`, `b7a16728`

**2. [Rule 1 - Bug] Достижимость узла считала блоки с универсальным субъектом**
- **Found during:** задача 2, перечень достигающих блоков на дереве до коммита
- **Issue:** предки в разбор не входят, поэтому узлы заготовок и `#notice-alert` «достигали» блоки `*`, `[data-row] > *`, `[data-dashpair] > *`, `.sched-card__sum > *`, `.acct-card__kv .kv > :last-child`. Сегодня ни один из них не объявляет слоя, положения или способа отображения. Но будущая правка вида `[data-row] > * { position: relative; }` покраснила бы правило подъёма за форму чужой правки — ровно довод `10-56#1`.
- **Fix:** составная часть считается достигающей, только если НАЗЫВАЕТ узел идентификатором, классом или признаком. Добавлены три контроля точности на универсальный субъект. Все 22 RED-прогона новых правил перемерены, итог тот же.
- **Files modified:** `tests/test_pages/test_failure_banner_invariants.py` (до коммита)
- **Commit:** `b758c8dc`

**3. [Rule 3 - Blocking] Неоднозначный якорь базового блока**
- **Found during:** задача 1 (l12, l12b) и контроль базы
- **Issue:** `.failure-stack {\n  --failure-banner-top: 12px;` — это хвост и блока снятия `.failure-stack[hidden] + .failure-stack {…}`, то есть якорь встречается дважды. Драйвер отказал до правки, `app/` чист.
- **Fix:** якорь удлинён строкой шага (`--failure-stack-step`) в драйвере и в контроле.
- **Commit:** `b758c8dc` (контроль)

---

**Total deviations:** 3 auto-fixed (1 Rule 2, 1 Rule 1, 1 Rule 3). Строка `10-33#0` передана чекпойнту замером планирования, как план и предписывал.
**Impact on plan:** записи несут только правила с замеренным красным. Продукт не правился, ни одна формулировка не облегчена, замещённая строка не тронута.

## Issues Encountered

- Полные модули `test_shell.py`, `test_components.py`, `test_banner_dismiss.py`, `test_htmx_markup_gates.py` и модуль плашки идут 11.5 мин (`496 passed`), что слишком долго для прогона на каждую мутацию. Сеть поэтому собрана по `-k` (137 тестов). Правила, читающие `app.css` под другими именами, в сеть могли не попасть. Для строк, записанных с действующими правилами, это ничего не меняет: каждое такое правило покраснело само. Для форм «зелено всем» это значит, что они зелены всей СЕТИ, а не всей суите. Новые правила написаны по формулировке, и на дереве они зелены.
- `test_failure_stack_rule_count_is_declared` (15-07/15-19) краснеет на любом новом блоке класса стопки (l4, l4c, l13c). Для `10-51#2` это законный соучастник, и запись его называет. Для формы с признаком (l4b) он слеп.

## Verification

- `uv run pytest tests/test_pages/test_failure_banner_invariants.py -q -p no:randomly` → `20 passed`.
- `<verify>` задачи 1: `uv run pytest tests/test_pages/test_shell.py tests/test_templates/test_components.py -q -p no:randomly -k "lift or stack or banner or scroll_lock or display"` → `45 passed, 292 deselected`; `git diff --exit-code -- app/` → пусто.
- Гейты на закоммиченном дереве `b7a16728`: `uv run pytest tests/test_pages/test_failure_banner_invariants.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_shell.py tests/test_pages/test_responsive_markup.py tests/test_templates/ tests/test_planning/ -q -p no:randomly` → `1124 passed`, `exit=0` (936 с).
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed` после записей задачи 1 и после записей задачи 2; вместе с модулем правил — `160 passed`.
- `uv run python scripts/prohibitions_census.py --check` → «реестр: 741 строк, биекция с переписью — согласие». `--breakdown` → `product-invariant: enforced 50 (7), partially-enforced 4 (4), unresolved 16 (1)`, «сумма по диспозициям области решений: 321».
- `--list --phase 10 --class product-invariant`: девять строк группы несут `disposition=enforced`. `10-33#0` — `unresolved` (прежняя диспозиция, не тронута).
- `grep -c 'ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ'` → `1`. `git diff --exit-code -- app/` → пусто; `git diff b2a6b399..HEAD --name-only -- app/` → 0 файлов.
- Счётные гейты не сдвинулись. В модуле нет HTTP-вызовов, `status_code`, целей перехода и имён `*_degrades_without_htmx`. `PAIRED_302_ASSERTIONS_DECLARED` 191, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5 — гейты зелены в прогоне выше. Нового `import yaml` нет.
- `graphify update .` выполнен после правки кода.
- **Подмена полного прогона названа:** полную суиту (`just test`, около 40 мин) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют модуль плашки, `test_shell.py`, `test_responsive_markup.py`, три гейта страниц (`test_htmx_gates.py`, `test_htmx_post_pairs.py`, `test_hx_location_destinations.py`), каталоги `tests/test_templates/` и `tests/test_planning/` целиком. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None — заглушек в модуле нет. Литералы блока подъёма, базы и селекторов блокировки сняты с дерева и сличены по истории файла.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-29…15-31 проходят свои группы тем же протоколом. Образец этого плана: для запрета о блоке таблицы замерять по отдельности приписку, перестановку, пробелы, правку тела, второй блок иной формой селектора и сокращение `all`. Достижимость узла считать разбором, а не вхождением имени, и только у части, называющей узел.
- Остаток `product-invariant`: 4 частичные строки и 16 неразобранных. Шесть строк переданы 15-32: две — планом 15-26, три — планом 15-27, одна — этим.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: tests/test_pages/test_failure_banner_invariants.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: a658fe17, b758c8dc, b7a16728 (ledger `b2a6b399..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

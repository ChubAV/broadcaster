---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 09
subsystem: testing
tags: [def-09-03, page-size, oob-target-exceptions, inventory-gate, jinja, htmx, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-08 — сдвиги строк app/pages/schedules.py и tests/test_pages/test_editor_schedules.py"
  - phase: 09-sinhronizatsiya-grupp-akkaunta
    provides: "долг DEF-09-03 (литерал limit=30) и перечень OOB_TARGET_EXCEPTIONS (план 09-14) с назначенной Фазой 15"
provides:
  - "tests/test_templates/test_markup_literal_inventory.py — гейт ОТСУТСТВИЯ литерала размера страницы в app/templates/**/*.html, летопись 6 → 0, 12 правил (4 контроля)"
  - "шесть шаблонов трёх пар «страница + порция» собирают адрес порции из контекста (`limit={{ page_size }}`)"
  - "оба обработчика ads / accounts / schedules кладут в контекст `page_size` = `PAGE_SIZE` своего модуля"
  - "OOB_TARGET_EXCEPTIONS: сирота экрана редактора введён (2 → 4), у всех записей диспозиция назначения Фазе 15 и адресат"
  - "правило полноты перечня отступлений, правило диспозиции, правило адресата, три контроля, поведенческое правило холостого пути редактора"
  - "флагированное допущение: замер достижимости снятия внеполосных узлов (три величины) и две ветви развития с ценой — решение за владельцем"
affects: [15-14, 15-verification, GATE-09, GATE-10, account_groups, schedules-editor]

actuals:
  tokens: 16489
  tasks: 3
  commits: 5
plan_head_before: f532fe8a389751c0ffc75387d1a37f3206e5e73f

tech-stack:
  added: []
  patterns:
    - "Гейт ОТСУТСТВИЯ литерала: разборщик берёт исходники СЛОВАРЁМ, контроль кладёт синтетический ключ, положительный контроль утверждает непустоту вселенной, контроль вырезания комментариев утверждает оба счёта и разность"
    - "Носитель числа проверяется в рантайме: шпион на common.templates.TemplateResponse ловит контекст, порция запрашивается с limit, отличным от страничного, — так видно, что в контекст кладётся PAGE_SIZE, а не присланное клиентом"
    - "Правило полноты перечня: места прозы находятся ОБХОДОМ дерева по признаку «перечн* `ИМЯ`», каждое сопоставлено печатающему шаблону, ключи узлов выводятся из шаблона"
    - "Замер продуктовой правки мутантом на снимке `git archive HEAD` в scratchpad: рабочая копия не трогается, коммитится только запись"

key-files:
  created:
    - tests/test_templates/test_markup_literal_inventory.py
  modified:
    - app/pages/ads.py
    - app/pages/accounts.py
    - app/pages/schedules.py
    - app/templates/ads/list.html
    - app/templates/ads/partial_cards.html
    - app/templates/accounts/list.html
    - app/templates/accounts/partial_cards.html
    - app/templates/schedules/list.html
    - app/templates/schedules/partial_cards.html
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_editor_schedules.py

key-decisions:
  - "В контекст кладётся ИМЕННО PAGE_SIZE, а не присланный `limit`: литерал был тридцатью при любом `limit` порции, и только так отрендеренный адрес остаётся прежним до символа (утверждено правилом 7 с `limit=7`)"
  - "Сирота экрана редактора (`sched-{schedule_id}`, `sched-del-{schedule_id}`, печатает ads/partials/sched_delete_response.html) введён в ТОТ ЖЕ перечень, а не объявлен изъятием: узлы того же семейства, и изъятие скрыло бы их"
  - "Диспозиция всех четырёх записей — «перезаписано», адресат — владелец продукта (решение по замеру задачи 3 при закрытии вехи v2.1). «Снято» выразимо, но исполнитель права снимать не имеет"
  - "Правило холостого пути экрана групп читает только записи своего шаблона — одна строка фильтра; имя и утверждения правила не тронуты. Без этого ключ `{schedule_id}` ронял `key.format(group_id=…)` KeyError"
  - "Продукт account_groups и редактора не тронут ни строкой; мутант задачи 3 жил только в снимке scratchpad"

patterns-established:
  - "Литерал, заменённый значением контекста, держится правилом отсутствия в ИСХОДНИКЕ; правило отрендеренного адреса остаётся рядом как страховочное и предмета не держит"

requirements-completed: [GATE-09, GATE-10]

coverage:
  - id: D1
    description: "Литерала размера страницы в исходниках app/templates/ нет (6 → 0); сеть доказана от вакуума синтетическим ключом, непустотой вселенной и вырезанием комментариев"
    requirement: "GATE-09"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_markup_literal_inventory.py -q -p no:randomly"
        status: pass
      - kind: other
        ref: "grep -rc 'limit=30' app/templates/ — ноль во всех файлах"
        status: pass
    human_judgment: false
  - id: D2
    description: "Число живёт в одном носителе: оба обработчика трёх модулей кладут PAGE_SIZE в контекст, пары совпадают посимвольно, отрендеренный адрес порции прежний"
    requirement: "GATE-10"
    verification:
      - kind: integration
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_the_page_size_in_the_context_is_the_module_constant"
        status: pass
      - kind: integration
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_the_rendered_portion_url_is_unchanged"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_both_halves_of_every_pair_build_the_portion_url_with_the_same_line"
        status: pass
    human_judgment: false
  - id: D3
    description: "Перечень OOB_TARGET_EXCEPTIONS полон (сирота введён, 2 → 4), у каждой записи диспозиция назначения Фазе 15 и адресат, правило полноты краснеет на новом сироте"
    requirement: "GATE-10"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_account_groups.py -q -p no:randomly -k \"oob_target or exceptions\""
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_the_idle_editor_delete_path_really_ships_the_recorded_oob_nodes"
        status: pass
    human_judgment: false
  - id: D4
    description: "Замер достижимости снятия двух (теперь четырёх) внеполосных отступлений записан флагированным допущением; решение о снятии за владельцем"
    verification: []
    human_judgment: true
    rationale: "Замер — наблюдение, а не контракт: выбор между «снять продуктовой правкой» (цена — 9 правил неотличимости D-04-A) и «оставить с новым адресатом» (цена — две строки консоли на холостой запрос) принадлежит владельцу продукта"

duration: 1h 43m
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 09: литерал размера страницы и перечень внеполосных отступлений Summary

**Размер страницы доезжает до шести шаблонов из контекста (`PAGE_SIZE` — единственный носитель), и гейт утверждает ОТСУТСТВИЕ литерала `limit=30` в исходниках. Перечень `OOB_TARGET_EXCEPTIONS` полон: сирота экрана редактора введён (2 → 4), у каждой записи записана судьба назначения Фазе 15, а замер цены продуктового снятия вынесен владельцу.**

## Performance

- **Duration:** 1h 43m
- **Started:** 2026-09-24T11:07:36Z
- **Completed:** 2026-09-24T12:51:24Z
- **Tasks:** 3 (все)
- **Files modified:** 12 (1 создан, 11 изменены)
- **Commits:** 5 кода и записей (`git rev-list --count f532fe8a..HEAD` при записи сводки)

## Accomplishments

- **DEF-09-03 закрыт правилом ОТСУТСТВИЯ (задача 1).** Шесть шаблонов собирают адрес порции как `limit={{ page_size }}`. Все шесть контекстов кладут `PAGE_SIZE` своего модуля. Новый гейт `tests/test_templates/test_markup_literal_inventory.py` держит ноль: 12 правил, из них 4 контроля.
- **Перечень отступлений инвентаризован (задача 2).** Сирота экрана редактора введён в тот же перечень, число поднято летописью. Каждой записи назначена диспозиция из объявленного перечня (2 значения) и назван адресат. Правило полноты находит места прозы обходом дерева.
- **Замер снят и записан, решение не принято (задача 3).** Три величины измерены исполнением. Обе ветви развития названы с ценой. Продукт не тронут.

## Задача 1: литерал размера страницы

**`grep -rc 'limit=30' app/templates/` ДО** (дерево `f532fe8a`): шесть файлов по 1: `ads/list.html`, `ads/partial_cards.html`, `accounts/list.html`, `accounts/partial_cards.html`, `schedules/list.html`, `schedules/partial_cards.html`. **ПОСЛЕ** (`a674e8e5`): 0 во всех файлах, ненулевых строк вывода нет.

`grep -n 'PAGE_SIZE = 30'`: `ads.py:80`, `accounts.py:64`, `schedules.py:84`, по одной строке, носитель не задвоился. Новые ключи `page_size`: `ads.py:250`, `:300`; `accounts.py:175`, `:213`; `schedules.py:877`, `:938`.

**Текст летописи 6 → 0** (докстринг гейта):

> ЛЕТОПИСЬ ЧИСЛА МЕСТ: 6 → 0 (план 15-09, задача 1, 2026-09-24).
> - БЫЛО: шесть мест, все в строке сборки адреса порции, три пары «страница + карточки порции»: `app/templates/ads/list.html:61`, `app/templates/ads/partial_cards.html:7`, `app/templates/accounts/list.html:203`, `app/templates/accounts/partial_cards.html:146`, `app/templates/schedules/list.html:66`, `app/templates/schedules/partial_cards.html:12`. Замер: `grep -rc 'limit=30' app/templates/` на дереве `f532fe8a`: шесть файлов по одному вхождению.
> - ЧЕМ СНЯТО: литерал заменён значением контекста `page_size`. Оба обработчика каждого модуля (страница и порция) кладут в контекст ИМЕННО `PAGE_SIZE`. Новых носителей числа не заведено. Пара правлена одним ходом в обе половины. […]
> - ⚠️ ПРЕЖНЕЕ ПРИНУЖДЕНИЕ ИЗМЕРЕНО И ПРИЗНАНО НЕДОСТАТОЧНЫМ, А НЕ ЗАБЫТО. Вхождений `limit=30` в `tests/` до этого файла было 30 (`grep -rc`, шесть модулей), и ни одно не утверждает ОТСУТСТВИЯ. Ближайшее из них, `test_page_shows_thirty_rows_and_a_sentinel` (`tests/test_pages/test_account_groups.py`), сверяет ОТРЕНДЕРЕННЫЙ адрес и остаётся зелёным и при параметре, и при вернувшемся литерале. […]
> - Оговорка к прежним записям, называвшим шесть живых мест: ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей записи он был верным, и правится не он, а числа, которые он пережил.

Докстринг несёт и абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» с границей вселенной `app/templates/**/*.html`. После файла вхождений `limit=30` в `tests/` стало 33: три новых лежат в самом гейте (синтетический шаблон контролей и летопись).

Семь правил поведения — это восемь функций, три из них параметризованы по разделам. Правило 5 дополнено своим контролем (`test_control_negative_a_diverged_pair_is_named`). Правило 7 страховочное: оно зелено и до правки, и после неё, что и видно по RED-прогону (7 passed / 5 failed). Прежние правила адреса (`test_infinite_scroll_chain`, `test_infinite_scroll_keeps_filters`) зелены.

## Задача 2: перечень OOB_TARGET_EXCEPTIONS

**Сирота найден по содержанию, а не по номеру.** Строка `test_editor_schedules.py:2182` из плана после 15-08 стала `:2188`. Это докстринг `test_repeated_editor_delete_is_harmless`: остаток «наследуется перечнем `OOB_TARGET_EXCEPTIONS` с назначенной Фазой 15». Та же фраза стоит ещё в двух местах: докстринг `schedules_delete` (`app/pages/schedules.py`) и шаблон `ads/partials/sched_delete_response.html` (дважды). Узлов этого экрана в перечне не было ни одного. Узлы — `sched-{schedule_id}` и `sched-del-{schedule_id}`.

**Новое значение `OOB_TARGET_EXCEPTIONS_DECLARED = 4`** (`test_account_groups.py:5149`). Запись летописи:

> 2 → 4, Фаза 15, план 15-09, задача 2 — число поставлено ВВЕДЕНИЕМ ДВУХ ЗАПИСЕЙ, а не арифметикой: `sched-{schedule_id}` и `sched-del-{schedule_id}` (экран редактора объявления) были объявлены остатком «перечня `OOB_TARGET_EXCEPTIONS` с назначенной Фазой 15» только прозой — в трёх местах […] — а записей в перечне не имели. Сироту назвало правило полноты […]; узлы измерены поведенческим правилом […]. Тем же планом у всех четырёх записей записана диспозиция назначения Фазе 15: «перезаписано», адресат — владелец продукта (_REASSIGNED_TO).

**Диспозиция по КАЖДОЙ записи:**

| Запись | Печатает | `assigned_phase` (история) | `phase_15_disposition` | Адресат |
|---|---|---|---|---|
| `group-row-{group_id}` | `account_groups/partials/delete_response.html` | Фаза 15 — Упрочнение и сводный обход 47 форм | перезаписано | Владелец продукта — решение по замеру плана 15-09 (задача 3) при закрытии вехи v2.1: снять отступления продуктовой правкой либо оставить их принятыми с новым назначением |
| `group-del-{group_id}` | то же | то же | перезаписано | то же |
| `sched-{schedule_id}` | `ads/partials/sched_delete_response.html` | то же (по прозе трёх мест) | перезаписано | то же |
| `sched-del-{schedule_id}` | то же | то же | перезаписано | то же |

Перечень диспозиций: `PHASE_15_DISPOSITIONS = {"снято", "перезаписано"}`, `PHASE_15_DISPOSITIONS_DECLARED = 2`. Запись «снято» в живом перечне правило не пропускает: такая запись закрывается по форме `INCLUDE_TARGET_EXCEPTIONS`, с формулой «ПРЕДМЕТ СНЯТ, А НЕ ОТЛОЖЕН». Сегодня таких записей нет.

**Новые правила** (`test_account_groups.py`, с `:5462`): полнота, диспозиция, адресат и три контроля: запись без диспозиции, убранная запись при оставшейся прозе, новое место прозы без шаблона. Поведенческое правило экрана редактора стоит в хвосте `test_editor_schedules.py:4538`. Оба действующих правила (`test_every_claim_about_a_missing_oob_target_names_the_runtime_event`, `test_the_idle_delete_path_really_ships_the_recorded_nodes`) не переименованы, удалённых строк с их именами в диффе 0.

Счёты до и после: `-k "oob_target or exceptions"` 4 → 9 passed; `-k control` 5 → 8; `assigned_phase` в двух файлах 10 → 15 (≥ 3); `grep -c 'Фаза 15' test_account_groups.py` 3 → 11. Рост — это две новые записи, запись летописи, комментарии диспозиции и замера и значение, подставленное контролем. Каждое вхождение стоит при записи летописи или при её обосновании.

## Задача 3: замер достижимости снятия (флагированное допущение, `test_account_groups.py:4965-5059`)

**Величина 1: ветви обработчика удаления.** Снята одноразовым модулем в scratchpad (не коммитится). Модуль гонится суитой с фикстурами `tests/conftest.py`: `python -m pytest <scratch>/test_measure_oob_branches.py`.

| Экран | Ветвь | Ответ | Узлы печатаются | Цель в документе |
|---|---|---|---|---|
| группы | удачное удаление | 200, фрагмент | да | ЕСТЬ |
| группы | уже удалённая группа | 200, фрагмент | да | НЕТ |
| группы | чужая группа | 200, фрагмент | да | НЕТ |
| группы | несуществующая группа | 200, фрагмент | да | НЕТ |
| группы | последняя строка | 204, переход (HX-Location) | нет | — |
| редактор | удачное удаление | 200, фрагмент | да | ЕСТЬ |
| редактор | уже удалённое / чужое / несуществующее | 200, фрагмент | да | НЕТ |
| редактор | последнее расписание | 204, переход | нет | — |

**Величина 2: ветвей «узлы есть, цели нет».** По три на каждом экране (уже удалённая, чужая, несуществующая строка), всего шесть. На каждой — два узла без цели, то есть две строки `htmx:oobErrorNoTarget` в консоли на запрос.

**Величина 3: если узлы на холостых ветвях не печатать.** Мутант собран на снимке `git archive HEAD` плюс тестовые файлы задачи 2, в scratchpad, и не закоммичен. В нём обработчики передают `deleted=<строка найдена>`, а узлы снятия обёрнуты в `{% if deleted %}`. Прогон: `pytest tests/test_pages/ tests/test_templates/ -q -p no:randomly`. Итог **13 failed / 2298 passed**; то же дерево без мутанта даёт 2311 passed. Документ остаётся целым: тот же модуль по мутанту показал ноль узлов без цели на всех шести холостых ветвях. Краснеют:
- **9 правил держат неотличимость** (D-04-A, T-09-05-06, T-10-01): `test_repeated_delete_is_harmless_over_htmx`, `test_a_no_op_delete_does_not_double_a_row`, `test_the_delete_response_is_indistinguishable_for_a_foreign_and_a_missing_group`, `test_the_delete_branch_does_not_reveal_a_foreign_group_under_search`, `test_delete_out_of_column_is_indistinguishable_from_missing_and_foreign`, `test_confirm_delete_transport.py::…on_the_account_group_route_answers_the_same_shape`, `test_htmx_post_pairs.py::test_every_pair_case_answers_both_transports` (случай «группа вне колонки»), `test_repeated_editor_delete_is_harmless`, `test_confirm_delete_transport.py::…on_the_fragment_route_answers_the_same_shape`.
- **2 правила держат записи перечня:** `test_the_idle_delete_path_really_ships_the_recorded_nodes`, `test_the_idle_editor_delete_path_really_ships_the_recorded_oob_nodes`. Они снимаются вместе с записями.
- **2 правила держат безусловность узлов в разметке:** `test_components.py::test_the_delete_response_removes_the_very_node_that_owns_the_scroll_lock`, `test_control_negative_a_conditional_removal_node_reddens_the_gate`.

**Две ветви развития и цена каждой:**
- **«Снять продуктовой правкой».** Консоль холостого пути чиста. Цена: ответ начинает различать найденную и ненайденную строку. Краснеют девять правил неотличимости, и снять их значит отменить записанное решение D-04-A. Ещё четыре правила правятся вместе с продуктом. Записи закрываются диспозицией «снято».
- **«Оставить с перезаписанным назначением».** Продукт не трогается. Цена: две строки консоли на каждый холостой запрос на шести ветвях. Признак «200 и чистая консоль» на них остаётся неверным.

**Решает владелец продукта при закрытии Фазы 15 либо вехи v2.1.** Правил, закрепляющих сегодняшнее число ветвей, не написано: в `assert` числа ветвей нет, `characterisation` = 0.

**Продукт `account_groups` не тронут ни строкой.** `git show --format= --unified=0 HEAD -- app/templates/account_groups/partials/delete_response.html app/pages/account_groups.py` печатает пустоту. Во всём плане ни `app/pages/account_groups.py`, ни шаблоны `account_groups/`, ни `ads/partials/sched_delete_response.html` не менялись.

## Где номера плана устарели (найдено по содержанию)

- `.planning/REQUIREMENTS.md:429` (запись `DEF-09-03`): на деле `:432`.
- `tests/test_pages/test_editor_schedules.py:2182` и `:2170-2195`: после 15-08 это `:2188` и `:2176-2201`.
- Контексты `schedules.py:867-871` / `:925-929`: до правки это `:859-871` / `:918-935`. `ads.py` и `accounts.py` совпали с планом с точностью до строки-двух.
- `test_account_groups.py:4916 / :4952 / :4990` на старте были верны. После плана `OOB_TARGET_EXCEPTIONS` стоит на `:5074`, `…_DECLARED` на `:5149`, `test_the_number_of_oob_target_exceptions_is_the_declared_one` на `:5180`.

**Сдвиги, внесённые этим планом (для 15-10…15-14):** в `app/pages/schedules.py` добавлено +6 строк после `:866` и +3 после `:935`. Итого `schedules_update` 1181-1399 → **1190-1408**, `next_run_or_none` в нём → `:1343`; `schedules_toggle` 1403-1617 → **1412-1626**, его `next_run_or_none` 1512 → **1521**; `schedules_delete` → **1630-1906**. `ads.py`: `ads_partial` 207-253, `ads_list` 257-307. `accounts.py`: `accounts_partial` 137-177, `accounts_list` 181-216. `test_editor_schedules.py`: строки до `:4518` не сдвинуты, новое правило в хвосте (`:4521-4606`). `test_account_groups.py`: сдвиг начинается с `:4855` (класс `OobTargetException`).

## Task Commits

1. **Задача 1: литерал уходит из разметки**
   - `5215e136` test(15-09): RED — 5 failed / 7 passed; цель `test_no_page_size_literal_is_left_in_the_template_sources` называет все шесть мест
   - `a674e8e5` feat(15-09): GREEN
2. **Задача 2: перечень инвентаризован**
   - `17b11e74` test(15-09): RED — 3 failed / 10 passed; цель `test_every_oob_target_exception_declared_in_prose_stands_in_the_list` называет `sched-{schedule_id}` и `sched-del-{schedule_id}`
   - `94bdeb68` feat(15-09): GREEN
3. **Задача 3: замер записан** — `33a3223a` docs(15-09)

## TDD Gate Compliance

У обеих TDD-задач RED стоит до GREEN: `test(15-09)` `5215e136` → `feat(15-09)` `a674e8e5`; `test(15-09)` `17b11e74` → `feat(15-09)` `94bdeb68`. REFACTOR-коммитов нет, чистить было нечего. RED-улика снята прогоном `--junit-xml` и переложена в TAP одноразовым скриптом в scratchpad (не закоммичен). `gsd-tools check tdd-red-evidence` вернул **RED_EVIDENCE_OK** (`target_test_failed`, exit 1) на обеих: задача 1 — `test_no_page_size_literal_is_left_in_the_template_sources`, задача 2 — `test_every_oob_target_exception_declared_in_prose_stands_in_the_list`. Задача 3 не TDD (`type="auto"`).

## Files Created/Modified

- `tests/test_templates/test_markup_literal_inventory.py` — новый гейт отсутствия литерала
- `app/pages/ads.py`, `app/pages/accounts.py`, `app/pages/schedules.py` — ключ `page_size` в двух контекстах каждого
- шесть шаблонов `ads/`, `accounts/`, `schedules/` (`list.html`, `partial_cards.html`) — `limit={{ page_size }}`
- `tests/test_pages/test_account_groups.py` — поля диспозиции, две записи, летопись 2 → 4, правила полноты, диспозиции и адресата, контроли, запись замера
- `tests/test_pages/test_editor_schedules.py` — поведенческое правило холостого пути редактора (хвост файла)

## Decisions Made

См. `key-decisions`. Главное: отступления живы, их назначение перезаписано на владельца, а не снято. Снятие есть продуктовая правка, которая отменяет решение D-04-A, и принимать её исполнитель права не имеет.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - критерий невыполним буквально] `grep -rc 'page_size' app/templates/` — ровно шесть файлов**
- **Found during:** Задача 1
- **Issue:** Семь файлов несли `page_size` ещё до плана: `history/list.html`, `history/partial_cards.html`, `admin/user_history.html`, `admin/history_partial_cards.html`, `account_groups/list.html`, `account_groups/partial_cards.html`, `account_groups/includes/sentinel.html`. После плана файлов 13.
- **Fix:** Проверена разность: прибавилось ровно шесть файлов, названных в `read_first`. Имя ключа взято у этих экранов намеренно, чтобы не заводить второго имени.
- **Committed in:** `a674e8e5`

**2. [Rule 3 - Blocking] Ввод сироты требовал однострочного сужения охраняемого правила**
- **Found during:** Задача 2
- **Issue:** `test_the_idle_delete_path_really_ships_the_recorded_nodes` делает `key.format(group_id=…)` по ВСЕМ ключам перечня. Ключ `sched-{schedule_id}` дал бы KeyError. Проверка `id` в `test_every_oob_target_exception_carries_a_reason_and_an_assigned_phase` умела подставлять только `{group_id}`.
- **Fix:** В правиле холостого пути множество записей отфильтровано по своему шаблону (`record.where_printed == GROUP_DELETE_RESPONSE`); имя и утверждения правила не тронуты. Проверка `id` подставляет любую `{переменную}`. Альтернатива — отдельный перечень для редактора — нарушила бы связь плана «один перечень, а не сирота рядом с ним».
- **Verification:** правило зелено, удалённых строк с его именем в диффе 0.
- **Committed in:** `94bdeb68`

**3. [Rule 2 - недостающая проверка] Поведенческое правило для новых записей**
- **Found during:** Задача 2
- **Issue:** Записи экрана групп держит третье, поведенческое утверждение идиомы SP-1. Без него новые записи проверялись бы только по тексту.
- **Fix:** Добавлено `test_the_idle_editor_delete_path_really_ships_the_recorded_oob_nodes`. Оно краснеет в обе стороны; в RED назвало `sched-1` и `sched-del-1`.
- **Committed in:** `17b11e74`

**4. [Уточнение] Замер задачи 3 снят на обоих экранах и мутантом в снимке, а не в рабочей копии**
- План называл два отступления, но после задачи 2 записей четыре. Замер без экрана редактора оставил бы владельца без числа для половины перечня.
- Мутант собран в `git archive`-снимке в scratchpad. Это тот же приём «мутант рабочей копии», только живое дерево не трогается и откатывать нечего.

**5. [Уточнение] Контроль диспозиции переписан до RED-коммита**
- Первая версия контроля зависела от состояния перечня. Переписана так, чтобы стартовать с перечня, полного по построению. Все контроли зелены и в RED, и в GREEN.

---

**Total deviations:** 5: 2 по Rule 3, 1 по Rule 2, 2 уточнения.
**Impact on plan:** Предметы обоих долгов закрыты так, как требовал план. Отступление от «не переписывать» свелось к одной строке фильтра, и оно названо. В область продукта ничего не добавлено.

## Проверки (подстановка вместо полной суиты названа прямо)

Полную суиту и `-m "not planning"` по всему `tests/` по договорённости гонит оркестратор после волны. Эта подстановка названа здесь; окна в WINDOWS.md для неё не открывалось. Прогнаны:
- `tests/test_pages/ tests/test_templates/`: **ДО** (снимок `f532fe8a`) — **2292 passed / 0 failed**. **ПОСЛЕ** (`33a3223a`) — **2311 passed / 0 failed** (+19: 12 правил задачи 1, 6 и 1 правило задачи 2). Прогон шёл вместе с модулями ниже: всего **2471 passed / 0 failed** (37 мин).
- Модули вне этих каталогов, которые исполняют правленые обработчики или ввозят правленые модули: `tests/test_routes/test_ads.py`, `test_schedules_profile_timezone.py`, `test_schedules_toggle_detached.py`, `test_sync_groups.py`, `test_tg_user_auth.py`, `tests/test_services/test_schedule_rules_gate.py`, `tests/test_schedules_out_of_domain_resume.py`. Все вошли в прогон на 2471.
- Сквозные гейты, читающие исходники тестов: `test_htmx_post_pairs.py` (число 302 не сдвинулось, `PAIRED_302_ASSERTIONS_DECLARED` = 190 не тронут), `test_degradation_pairs.py`, `test_htmx_inventory.py`, `test_components.py`, `test_htmx_gates.py`, `test_shell.py`, `tests/test_planning/test_the_walkthrough_stand_is_seedable.py`. Все зелены.
- `tests/test_planning/`: **78 passed**. `uv run python -m compileall -q app main.py tests` молчит.
- `graphify update .` прогнан после задачи 1 и после задач 2–3 (exit 0).
- `requirements.ready-ids` (только чтение) для `[GATE-09, GATE-10]`: `ready: [GATE-10]`, `blocked: [GATE-09]`. `requirements.mark-complete` НЕ вызывался: требования фазы 15 закрываются после её верификации.

## Known Stubs

Нет.

## Issues Encountered

- Первый прогон итоговой проверки упал на пути `tests/test_schedules_poisoned_row.py`: файл живёт в `tests/test_pages/`, куда и так входил. Перезапущен без этого пути.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Владельцу при закрытии фазы или вехи нужно решить судьбу четырёх внеполосных отступлений. Замер и цена обеих ветвей записаны у перечня (`test_account_groups.py:4965-5059`).
- Для планов 15-10…15-14 сдвиги строк перечислены выше.

## Self-Check: PASSED

- FOUND: `tests/test_templates/test_markup_literal_inventory.py` и все 11 изменённых файлов
- FOUND: коммиты `5215e136`, `a674e8e5`, `17b11e74`, `94bdeb68`, `33a3223a`

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

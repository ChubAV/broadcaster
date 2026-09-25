---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 29
subsystem: testing
tags: [prohibitions-census, registry, record-mode, schedules, delete-response, owner-scope, d-05, criterion-6, g-1, d-16, pytest, ast, jinja]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-28 — образец замера мутацией дерева и драйвер; план 15-24 — протокол строки; план 15-22 — режим `--record`; планы 15-16/15-23 — нынешний код расписаний (`next_run_or_none` на второй строке, `profile_timezone_or_utc`)"
  - phase: 10-rychag-components-modal-html
    provides: "семь запретов `product-invariant` о вычислителе, входах и посеве (план 10-55) и об ответе удаления из редактора (план 10-50), включая находку D-05 `10-50#3`"
provides:
  - "семь строк группы «правила расписания и ответ удаления» — `enforced`; у каждой правила, покрасневшие на временной правке дерева по формулировке ИМЕННО этой строки"
  - "новый модуль `tests/test_pages/test_schedule_invariants.py`: 8 правил, 7 контролей; `NEXT_RUN_CALCULATOR_SOURCE_DIGEST`, разбор чтений ответа удаления (транзитивно, со связью `join`), разбор сайтов снятия проверок СУБД"
  - "находка D-05 `10-50#3` закрыта правилами (чтения напрямую, HTTP, дерево); `unresolved_reason: declared-rule-absent` снят"
affects: [15-30, 15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 15895
  tasks: 2
  commits: 3
plan_head_before: d69a8025a9f8146e498c985655fea2c4dca3a730

tech-stack:
  added: []
  patterns:
    - "Запрет «функция не правится ни на символ» — отпечаток sha256[:12] исходника ОДНОЙ функции (`ast.get_source_segment`), форма `statement_digest` прибора; контроль точности — помощник рядом, которого формулировка разрешает"
    - "Скоуп владельца у чтений обработчика — транзитивный обход помощников из сборки ответа: у каждого `execute` сравнение `Ad.user_id == <владелец>`, у выборки расписаний — `join(Ad, Schedule.ad_id == Ad.id)`, у вызова — владелец вызывающего (`user.id`), помощник без параметра владельца назван"
    - "Сайт снятия проверок СУБД — вызов со строковым аргументом `ignore_check_constraints = ON`; судится объемлющая функция, один отказ на функцию"

key-files:
  created:
    - tests/test_pages/test_schedule_invariants.py
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-29: две строки держатся действующими правилами целиком — `10-55#4` (гейт `test_schedule_rules_gate.py` краснел на шести формах расширения) и `10-50#1` (`test_editor_delete_returns_oob_nodes` и `test_every_oob_node_is_a_top_level_node_of_its_response` краснели на обёртке трёх узлов и одной линейки); запись меры 15-13 «обёртка вокруг остальных узлов не видна» опровергнута замером"
  - "15-29: запланированное правило `test_every_out_of_band_node_of_the_delete_response_is_top_level` не заведено — оно было бы вторым экземпляром утверждения `test_editor_delete_returns_oob_nodes`"
  - "15-29: у `10-55#2` правил на валидатор зоны ОБНОВЛЕНИЯ не было вовсе — ослабленный `UpdateScheduleRequest.validate_timezone` был зелен на 528 правилах (выключенная строка получала 200 и зону вне перечня в базе); заведено поведенческое правило 422 с полем `timezone` в `loc`"
  - "15-29: `10-50#0` держат два действующих правила повтора (сличение идентификаторов узлов и тела целиком) и новое правило «в шаблоне ответа нет ни одной ветви»; зелены на действующих были `{% if ad %}`, условное выражение и ветвь «идентификатор занят где-либо в базе» — последняя и есть перебор чужих идентификаторов, названный формулировкой"
  - "15-29: `10-55#9` — посев плана 10-55 это `_seed_out_of_domain_schedule` (`10-55-SUMMARY.md`), а не только программа посева стенда; правило видит обе и порядок `rollback()` утверждает у любого сайта `app/`, `scripts/`, `tests/`, исключая отложенный образец `IN-04` по паре «файл, функция»"
  - "15-29: плану 15-32 ничего не передано — ни одна формулировка группы не утверждает замещённого состояния (второй строки и тихого выключения, решение Г-2, группа не касается)"

patterns-established:
  - "Поведенческая половина скоупа чтений зовёт чтение НАПРЯМУЮ, если путь запроса к нему с чужим ключом закрыт выше (здесь — предикат ветки); HTTP-половина названа как краснеющая только при снятом скоупе и у предиката"

requirements-completed: []

coverage:
  - id: D1
    description: "`10-55#4` и `10-50#1` записаны `enforced` действующими правилами; каждое покраснело на своей мутации"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_services/test_schedule_rules_gate.py#test_no_blanket_catch_in_the_schedule_rules_body"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_delete_returns_oob_nodes"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_oob_node_is_a_top_level_node_of_its_response"
        status: pass
      - kind: other
        ref: "red29.sh e1/e2/e4/e5/e6, w1/w2/w3 → check tdd-red-evidence RED_EVIDENCE_OK ×11"
        status: pass
    human_judgment: false
  - id: D2
    description: "Модуль `test_schedule_invariants.py` (8 правил, 7 контролей); пять строк записаны `enforced`; каждое новое правило покраснело на мутации, где действующие зелены"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_schedule_invariants.py (15 passed)"
        status: pass
      - kind: other
        ref: "red29.sh (33 целевых прогона) → RED_EVIDENCE_OK ×33"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
      - kind: integration
        ref: "uv run pytest <модуль> test_editor_schedules.py test_confirm_delete_transport.py test_htmx_gates.py test_htmx_post_pairs.py test_hx_location_destinations.py tests/test_services/ tests/test_routes/ tests/test_templates/ tests/test_planning/ -q -p no:randomly → 1549 passed (b2a89c95)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Верность суждения «правило держит ВЕСЬ предмет формулировки» по семи строкам (полнота перечня форм нарушения)"
    verification: []
    human_judgment: true
    rationale: "Какие формы правки считать нарушением «ни на символ», «ни в каком виде», «всех новых чтений», машина не выводит — суждение исполнителя (D-33 плана 15-13). Строгость правила шаблона (любая ветвь, а не только ветвь по факту) — прочтение формулировки, названное в сводке"

duration: 111min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 29: Принуждение семи запретов о правилах расписания и ответе удаления Summary

**Все семь запретов `product-invariant` группы «правила расписания и ответ удаления» записаны `enforced`, находка D-05 `10-50#3` закрыта. `10-55#4` и `10-50#1` держат действующие правила целиком. Остальное держат 8 новых правил модуля `tests/test_pages/test_schedule_invariants.py`, где нужно вместе с действующими. Правила: отпечаток исходника `compute_next_run_at`; три отсечки входов на месте; 422 на незнакомую зону при создании и обновлении; `rollback()` первой строкой `finally` у любого снятия проверок СУБД; ни одной ветви в шаблоне ответа удаления; скоуп владельца у чтений ответа удаления (напрямую, по HTTP и по дереву). Каждое правило записи покраснело на временной правке дерева по формулировке своей строки. Плану 15-32 ничего не передано. `app/` не правился.**

## Performance

- **Duration:** 111 min (из них около 75 мин — прогоны: 35 мутаций по сетям, 44 целевых RED-прогона, гейты 8.9 мин)
- **Started:** 2026-09-25T21:32:30Z
- **Completed:** 2026-09-25T23:23:46Z
- **Tasks:** 2
- **Files modified:** 2 (модуль правил, реестр)

## Замер направления

Каждая мутация — временная правка файла дерева через драйвер `mutate29.py` (лежит в scratchpad, в дерево не входит). Порядок: запись, прогон, `git checkout -- <файл>`, затем `git diff --exit-code -- app/ tests/test_schedules_out_of_domain_resume.py`. Если якорь не единствен, драйвер отказывает до правки. После каждой из 35 мутаций было `clean=True`, в конце трёх пакетов — `ALL_CLEAN`.

Сети действующих правил:
- **С** (вычислитель): `tests/test_services/`, `test_schedules_out_of_domain_resume.py`, `tests/test_worker/`, `test_schedules_api_value_domain.py` — 515 тестов.
- **Е** (перехват): `tests/test_services/`, `test_schedules_out_of_domain_resume.py` — 332 теста.
- **Т** (входы): `test_schedules_api_value_domain.py`, `…_create_completeness.py`, `test_schedules.py`, `…_api_null.py`, `test_schedules_out_of_domain_resume.py`, `tests/test_services/`, `test_editor_schedules.py -k "malformed or time or zone or clean"` — 528 тестов.
- **У** (ответ удаления): `test_editor_schedules.py` и `test_confirm_delete_transport.py` целиком, `test_schedule_ownership.py`, `test_confirmation_panel_invariants.py`, `test_walkthrough_anchors.py`, `test_htmx_markup_gates.py`, `test_components.py -k "sched or delete or oob"`, `test_schedules_api_ownership.py` — 385 тестов.

| Мутация | Правка | Действующие правила | Новые правила |
|---|---|---|---|
| c1 | один знак докстринга `compute_next_run_at` | С: **`515 passed`** | отпечаток: «ИЗМЕНЁН: отпечаток 9daedfb10848, объявлен 698f47d4e018» |
| c2 | `try … except Exception: return None` вокруг `ZoneInfo` (пример самой формулировки) | С: **`515 passed`** | отпечаток: «… 62dd35b762ab …» |
| c3 | окно просмотра `range(8)` → `range(9)` | С: **`515 passed`** | отпечаток: «… 896c862fdcae …» |
| c4 | помощник рядом с вычислителем (разрешён формулировкой) | С: `515 passed` | **все 15 зелены** (контроль точности) |
| e1 | `except Exception:` в `next_run_or_none` | Е: `4 failed`: `no_blanket_catch` («перехват базового типа Exception»), `helper_catches_exactly_the_declared_list_by_name` и два контроля гейта | — |
| e2 | `Exception` дописан в `UNRUNNABLE_STORED_VALUE_ERRORS` | Е: `1 failed`: `declared_list_holds_exactly_the_measured_names` («6 имён, объявлено 5») | — |
| e3 | `except (UNRUNNABLE_STORED_VALUE_ERRORS, Exception)` | Е: `21 failed` (гейт и 17 поведенческих: `TypeError: catching classes …`) | — |
| e4 / e5 | `except BaseException:` / голое `except:` | Е: `4 failed` каждая, `no_blanket_catch` («BaseException» / «без указания типа») | — |
| e6 | второй обработчик `except Exception:` после именованного | Е: `4 failed`, `no_blanket_catch` («строка 210 … Exception») | — |
| t1 | `_clean_times` перестал отбрасывать негодное | Т: `2 failed`: `test_malformed_time_does_not_crash_and_is_dropped` («0 == 1»), `…_on_update_does_not_crash` («['24:00'] == []») | зелены (предмет — место отсечки) |
| t2 | `_reject_malformed_times` перестал отказывать | Т: `19 failed`: `test_create_with_malformed_time_answers_422…` ×9 («Получен 500 / 201»), `…create_with_one_bad_time…`, `test_update_with_malformed_time_answers_422…` ×9 («400 / 200 == 422») | зелены |
| t3 | `CreateScheduleRequest.validate_timezone` перестал отказывать | Т: `1 failed`: `test_create_schedule_invalid_timezone` («500 == 422») | место: «`CreateScheduleRequest.validate_timezone` не отказывает по перечню»; зона: «создание … 500» |
| **t4** | `UpdateScheduleRequest.validate_timezone` перестал отказывать | Т: **`528 passed`** | место: «`UpdateScheduleRequest…` не отказывает по перечню»; зона: «обновление строки 1 … 200 {… "timezone":"Not/A/Timezone","is_active":false …}» |
| t5 | оба валидатора зоны | Т: `1 failed`: `test_create_schedule_invalid_timezone` | — |
| **t6** | `UpdateScheduleRequest.validate_timezone` снят целиком | Т: **зелены** (`540 passed` вместе с модулем; красны только новые) | место: «`UpdateScheduleRequest.validate_timezone` снят»; зона: «обновление … 200» |
| b1 | обработчик передаёт `deleted`, шаблон `{% if deleted %}` вокруг узлов снятия | У: `test_a_repeated_confirmed_delete_on_the_fragment_route_answers_the_same_shape` («узлы повтора … отличны»), `test_repeated_editor_delete_is_harmless` («повторный ответ отличим»), `…the_idle_editor_delete_path_really_ships…`, контроль 15-? на своём предусловии | шаблон: «If в строке 132» |
| b2 | `{% if deleted %}` ВНУТРИ узла сводки (идентификаторы те же) | У: `1 failed`: `test_repeated_editor_delete_is_harmless` | шаблон: «If в строке 143» |
| **b3** | `{% if ad %}` вокруг узла сводки | У: **`399 passed`** | шаблон: «If в строке 143» |
| **b4** | `hx-swap-oob="{{ 'delete' if ad else 'none' }}"` | У: зелены (краснеет только контроль `…conditional_removal_node…` на своём предусловии) | шаблон: «CondExpr в строке 132» |
| **b5** | `taken=(await db.get(Schedule, id)) is not None`, `{% if not taken %}` вокруг сводки — ветвь «занят ли идентификатор где-либо», то есть перебор чужих | У: зелены по причине; красен `test_an_unusable_path_identifier_never_reaches_the_database` — **артефакт мутации** (`db.get` с идентификатором вне колонки), не названная причина | шаблон: «If в строке 143» |
| w1 | обёртка `<div>` вокруг трёх узлов (сводка вне её) | У: `test_editor_delete_returns_oob_nodes` («не все узлы … прямые дети тела: [('sched-1', 1) …]»), `test_every_oob_node_is_a_top_level_node_of_its_response` («на глубине 1»), три правила повтора | — |
| w2 | обёртка вокруг всех четырёх | У: те же и `test_the_summary_node_is_a_top_level_child_of_the_response` | — |
| w3 | `<section>` только вокруг линейки счётчика | У: `test_editor_delete_returns_oob_nodes`, `test_every_oob_node_is_a_top_level_node…` | — |
| **s1** | `_ad_row` без `Ad.user_id == user_id` | У: **`398 passed`** | дерево: «`_ad_row`: выборка без сравнения `Ad.user_id == user_id`»; чтения: «отдало ЧУЖОЕ объявление» |
| **s2** | `_ad_next_run_at` без сравнения владельца | У: **зелены** | дерево: «`_ad_next_run_at`: выборка без сравнения …»; чтения: «отдало момент ЧУЖОГО объявления» |
| **s3** | `_ad_next_run_at` без `join` (перекрёстное произведение с объявлениями владельца) | У: **зелены** | дерево: «выборка расписаний без связи `join(Ad, Schedule.ad_id == Ad.id)`»; чтения: «отдало момент ЧУЖОГО» |
| **s4** | скоуп снят у всех четырёх (предикат, счёт, объявление, момент) | У: **зелены** | дерево ×3 находки; чтения; HTTP: «статус ЧУЖОГО объявления ушёл в ответ удаления» |
| **s5** | `_ad_row` зовётся с владельцем объявления, а не запрашивающего | У: **`399 passed`** | дерево: «`_ad_row` зовётся с владельцем `(await db.get(Ad, ad_id)).user_id …`, а не `user.id`» |
| **p1** | в `_seed_out_of_domain_schedule` снятие проверок в очерёдности образца `IN-04` | `test_schedules_out_of_domain_resume.py`, `tests/test_planning/`, `test_send_analytics.py`: **зелены** | посев: «`_seed_out_of_domain_schedule`: первая строка `finally` — не `rollback()`» |
| p2 | то же с `rollback()` первой строкой `finally` (разрешено формулировкой) | зелены | **все 15 зелены** (контроль точности) |

## Таблица строк

| Строка | Формулировка (сокращённо) | Правило(а) записи | Замер, давший красное | Запись |
|---|---|---|---|---|
| `10-55#4` | перечень ловимых классов не расширяется до `except Exception` | `test_schedule_rules_gate.py::test_no_blanket_catch_in_the_schedule_rules_body`, `…::test_the_helper_catches_exactly_the_declared_list_by_name`, `…::test_the_declared_list_holds_exactly_the_measured_names` | e1, e3–e6 (первое), e1, e3 (второе), e2 (третье) | задача 1, `enforced` |
| `10-50#1` | общей обёртки у узлов ответа не появляется (было `partially-enforced`) | `test_editor_schedules.py::test_editor_delete_returns_oob_nodes`, `test_htmx_markup_gates.py::test_every_oob_node_is_a_top_level_node_of_its_response`, `test_editor_schedules.py::test_the_summary_node_is_a_top_level_child_of_the_response` | w1, w2, w3 (первые два); w2 (третье) | задача 1, `enforced` |
| `10-55#0` | вычислитель `compute_next_run_at` не правится ни на символ | **новое** `test_schedule_invariants.py::test_the_next_run_calculator_source_is_unchanged` | **c1, c2, c3 — только новое** | задача 2, `enforced` |
| `10-55#2` | `_clean_times`, `_reject_malformed_times`, `validate_timezone` на месте и отказывают | `test_editor_schedules.py::test_malformed_time_does_not_crash_and_is_dropped`, `…::test_malformed_time_on_update_does_not_crash`, `test_schedules_api_value_domain.py::test_create_with_malformed_time_answers_422_instead_of_crashing`, `…::test_update_with_malformed_time_answers_422_instead_of_crashing`, `test_schedules.py::test_create_schedule_invalid_timezone`; **новые** `…::test_the_input_gates_of_create_and_update_stay_in_place`, `…::test_an_unknown_timezone_is_refused_by_the_input_gate_on_create_and_update` | t1, t2, t3 (действующие); t3 (и новые); **t4, t6 — только новые** | задача 2, `enforced` |
| `10-55#9` | снятие `PRAGMA ignore_check_constraints` — с `rollback()` первой строкой `finally` | **новое** `…::test_no_seed_lifts_check_constraints_without_rolling_back_first` | **p1 — только новое** | задача 2, `enforced` |
| `10-50#0` | ветви по факту удаления в шаблоне ответа нет ни в каком виде (было `partially-enforced`) | `test_confirm_delete_transport.py::test_a_repeated_confirmed_delete_on_the_fragment_route_answers_the_same_shape`, `test_editor_schedules.py::test_repeated_editor_delete_is_harmless`; **новое** `…::test_the_delete_response_template_has_no_branch_on_the_delete_fact` | b1 (все три), b2 (второе и новое); **b3, b4, b5 — только новое** | задача 2, `enforced` |
| `10-50#3` (D-05) | скоуп владельца у всех новых чтений обязателен | **новые** `…::test_the_delete_response_reads_are_scoped_to_the_owner`, `…::test_a_delete_naming_a_foreign_ad_carries_no_field_of_it`, `…::test_the_delete_response_reads_carry_the_owner_link_in_the_tree` | **s1–s5 — только новые** (чтения: s1–s4; HTTP: s4; дерево: s1–s5) | задача 2, `enforced` |

## Передано плану 15-32

Ничего. Ни одна из семи формулировок не утверждает состояния, которое отменило позднейшее решение владельца. Решение Г-2 (вторая строка: отказ с плашкой вместо тихого выключения, план 15-16) предметов группы не касается. Ни одно правило не требует отката одобренной работы, и ни одно не красно на дереве.

## Accomplishments

- **Задача 1.** 35 мутаций по четырём сетям. `10-55#4` и `10-50#1` записаны `enforced` действующими правилами, каждое покраснело по названной причине. Запись меры плана 15-13 о `10-50#1` («обёртка вокруг остальных внеполосных узлов этим правилом не видна») опровергнута замером: два других действующих правила видят обёртку любого узла.
- **Задача 2.** Модуль `tests/test_pages/test_schedule_invariants.py`: 8 правил и 7 контролей. Докстринг по форме D-16: предмет с тождествами, отдельный абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» по каждой строке. Ввезены посев и разборщики `test_editor_schedules.py` (`_seed_*`, `_stranger`, `_oob_region`, `_summary_row`, `_form`) и программа посева `test_the_walkthrough_stand_is_seedable.py`. Второго разбора тела и второго посева модуль не заводит.
- **Реестр.** `product-invariant` было `enforced 50 / partially-enforced 4 / unresolved 16`, стало `57 / 2 / 11`. Сумма по диспозициям области решений — 321, биекция в согласии. Дифф реестра — ровно 7 строк: 2 в задаче 1 и 5 в задаче 2.

## Task Commits

1. **Задача 1: замер по действующим правилам** — `2034a549` (chore): `10-55#4` и `10-50#1` записаны `enforced`.
2. **Задача 2: новые правила** — `3f62b392` (test): модуль правил; `b2a89c95` (chore): пять строк записаны `enforced`.

**Plan metadata:** коммит сводки `docs(15-29)`, следом коммит учёта STATE/ROADMAP.

## TDD

План имеет `type: execute` при `workflow.tdd_mode: true`, поэтому гейт TDD на нём инертен. Продукт не правится, и цикла «красный тест → правка продукта → зелёный» здесь нет. **RED каждой строки измерен по правилу владельца (Г-1): правило засчитано, только если покраснело на нарушении формулировки своей строки.**

- **Как измерено.** `red29.sh <мутация> <узел>` (scratchpad) прогоняет ОДИН узел правила на мутированном дереве: `uv run pytest -q -p no:randomly --junit-xml=… <узел>`. Затем возврат и проверка чистоты дерева. `junit2red.py` (scratchpad, не в дереве) собирает запись `{command, exitCode, targetTest, output}` с выводом в форме node:test TAP, по ней отрабатывает `check tdd-red-evidence`.
- **Действующие правила, задача 1:** 11 прогонов — e1 ×2, e2, e4, e5, e6, w1 ×2, w2, w3 ×2. У каждого `FAILED <узел>`, `1 failed, 1 warning`, `exit=1`, `RED_EVIDENCE_OK/target_test_failed`. Причинные литералы — в таблице замера.
- **Задача 2, 33 прогона.** Действующие: t1 ×2, t2 ×2 (узлы `[abc]`), t3, b1 ×2, b2. Новые: отпечаток — c1, c2, c3; место отсечек — t3, t4, t6; зона — t3, t4, t6; посев — p1; шаблон — b1–b5; дерево — s1–s5; чтения — s1–s4; HTTP — s4. Каждый дал `FAILED …::<правило>`, `1 failed`, `exit=1`, `RED_EVIDENCE_OK/target_test_failed`. Итого 44 × `RED_EVIDENCE_OK`.
- **Не заявлено уликой RED.** Отказы контролей, упавших на СВОЁМ предусловии («боевое дерево чисто»): мои контроли на всех мутациях, контроль `test_control_negative_a_conditional_removal_node_reddens_the_gate` на b1/b4, контроли гейта перехвата на e1. Отказ `test_an_unusable_path_identifier_never_reaches_the_database` на b5 — артефакт самой мутации.
- **Контроли точности на дереве:** c4 (помощник рядом с вычислителем) и p2 (снятие проверок с `rollback()` первым) — все 15 тестов модуля зелены.
- Коммит `test(15-29)` предшествует записям второй задачи. Коммита `feat(15-29)` нет: продукт не правился. REFACTOR не было.

## Files Created/Modified

- `tests/test_pages/test_schedule_invariants.py` — новый модуль (927 строк): 8 правил, 7 контролей.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поля меры покрытия у 7 строк, записаны только через `--record`.

## Decisions Made

См. `key-decisions`. Кратко:
- Отпечаток `698f47d4e018` снят с дерева `d69a8025` и сличён по истории: `app/services/schedule_service.py` не менялся с `65b6e902` (2026-02-19, «Task 19»), а план 10-55 записал дифф модуля ПУСТЫМ. Формулировка говорит о «ДВЕНАДЦАТИ правилах» `test_schedule_service.py`, а функций-тестов в файле сегодня 8. Это число из ОБОСНОВАНИЯ запрета, а не его предмет, поэтому правило его не считает.
- Правило шаблона `10-50#0` отказывает на ЛЮБОЙ ветви (`If`, `CondExpr`), а не только на ветви «по факту удаления». Все узлы файла — внеполосные, и ветвь по любому признаку контекста может нести факт удаления (b5 это показывает). Ветвь по иному признаку в этом файле потребует решения владельца. Это прочтение «ни в каком виде», а не починка.
- `10-50#3`: путь запроса с чужим объявлением закрыт ВЫШЕ чтений — предикатом `_ad_has_a_schedule`. Поэтому снятие скоупа у одного чтения ответом маршрута не наблюдается (s1, s2, s3, s5 — HTTP зелёный). Чтения зовутся напрямую, дерево читается транзитивно, HTTP-половина краснеет на s4. Граница названа в шапке модуля.
- `10-55#2`: формулировка складывает `_clean_times` вместе с «отвечать 422», но страничная политика отбрасывает негодное, а не отказывает (`app/pages/schedules.py`, абзац над `DEFAULT_TIME`). Утверждается измеренное поведение: отбрасывание держат действующие правила t1. Правило 422 для `_clean_times` не писалось — это закрепило бы то, чего в дереве нет.
- `10-55#9`: исключён один сайт — образец `IN-04` (`test_send_analytics.py::test_upcoming_sends_skips_the_shape_the_schema_now_forbids`). Находку формулировка оставляет отложенной. Исключение не утверждает, что образец неверен: его починка правило не краснит.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Запланированное правило обёртки `10-50#1` было бы дублем**
- **Found during:** задача 1 (w1, w2, w3)
- **Issue:** план поручал новое правило `test_every_out_of_band_node_of_the_delete_response_is_top_level` на остаток «обёртка вокруг прочих узлов». Замер показал, что этот остаток держат `test_editor_delete_returns_oob_nodes` и `test_every_oob_node_is_a_top_level_node_of_its_response`, а запись меры 15-13 его просто не учла.
- **Fix:** правило написано, прогнано на w1–w3 и снято до коммита, потому что второй экземпляр утверждения разошёлся бы с первым. Строка записана в задаче 1 действующими правилами (шаг 4 протокола: «держит весь предмет»).
- **Files modified:** модуль (до коммита), реестр
- **Commit:** `2034a549`

**2. [Rule 2 - Missing critical] Правила `10-55#2` сверх «поиска действующих»**
- **Found during:** задача 1 (t4, t6)
- **Issue:** план поручал `10-55#2` действующим кандидатам. У валидатора зоны ОБНОВЛЕНИЯ правил не было: ослабленный или снятый, он был зелен на 528 правилах. Выключенная строка при этом получала 200 и сохраняла зону вне перечня.
- **Fix:** `test_an_unknown_timezone_is_refused_by_the_input_gate_on_create_and_update` (422 с полем `timezone` в `loc`, зона строки не меняется, на выключенной и включённой строке) и `test_the_input_gates_of_create_and_update_stay_in_place` (место трёх отсечек — по `ast`), каждое с контролем.
- **Commit:** `3f62b392`

**3. [Rule 2 - Missing critical] Поведенческая половина `10-50#3` разделена на два правила**
- **Found during:** задача 2 (s4)
- **Issue:** в одном правиле HTTP-половина не исполнялась ни на одной мутации: прямые чтения падали раньше. Её зубы оставались бы не измерены.
- **Fix:** `test_the_delete_response_reads_are_scoped_to_the_owner` (чтения напрямую) и `test_a_delete_naming_a_foreign_ad_carries_no_field_of_it` (HTTP), у обоих общий посев `_two_owners`. HTTP-правило покраснело на s4 («статус ЧУЖОГО объявления ушёл в ответ удаления»).
- **Commit:** `3f62b392`

**4. [Rule 1 - Bug] Правило посева судило функцию по разу на КАЖДЫЙ сайт**
- **Found during:** задача 2, мутация p2 (контроль посева)
- **Issue:** два снятия в одной функции давали два одинаковых отказа.
- **Fix:** судится функция, отказ о ней — один. Добавлен контроль «верная и неверная очерёдность в одной функции — один отказ».
- **Commit:** `3f62b392` (до коммита)

**5. [Rule 1 - Bug] Контроль шаблона был привязан к номеру строки**
- **Found during:** пакет У (w1 сдвинул строки шаблона)
- **Issue:** контроль сличал «CondExpr в строке 132» и покраснел бы на законной правке шапки шаблона.
- **Fix:** сличается только вид ветви.
- **Commit:** `3f62b392` (до коммита)

**6. [Уточнение предмета] Посев `10-55#9`**
- **Found during:** задача 1 (чтение `10-55-SUMMARY.md`)
- **Issue:** план называл кандидатом программу посева стенда (`test_the_walkthrough_stand_is_seedable.py`). Посев самого плана 10-55 — `_seed_out_of_domain_schedule` (`tests/test_schedules_out_of_domain_resume.py`).
- **Fix:** правило обязано увидеть обе программы (антивакуум) и судит порядок у любого сайта `app/`, `scripts/`, `tests/`. Сегодня в обоих посевах снятия проверок нет, и правило держит это отсутствием сайтов, а не порядком (запрет плана).

---

**Total deviations:** 5 auto-fixed (3 Rule 1, 2 Rule 2) и одно уточнение предмета.
**Impact on plan:** в записях стоят только правила с замеренным красным. Продукт не правился, ни одна формулировка не облегчена, второго экземпляра действующего утверждения нет.

## Issues Encountered

- Сети мутаций не полная суита. Правила, читающие те же файлы под другими именами, в сеть могли не попасть. Для строк, записанных с действующими правилами, это ничего не меняет: каждое такое правило покраснело само. Для форм «зелено всем» это значит «зелено всей СЕТИ».
- `10-55#4`: гейт `test_schedule_rules_gate.py` судит модуль `schedule_rules.py`. Огульный `try` вокруг ВЫЗОВА `next_run_or_none` в обработчике перечня не расширяет, и ни гейт, ни этот план его не видят. Граница формулировки («перечень ловимых классов»), а не пробел записи.
- Правило `test_the_counter_node_belongs_to_the_ad_named_by_the_request` (WR-02/WR-05 Фазы 10) закрепляет давнее поведение нормой, как и сказано в его записях. Этот план его не трогал и на него не опирался.

## Verification

- `uv run pytest tests/test_pages/test_schedule_invariants.py -q -p no:randomly` → `15 passed`.
- `<verify>` задачи 1: `uv run pytest tests/test_services/ tests/test_routes/test_schedules_api_value_domain.py tests/test_routes/test_schedules_api_create_completeness.py tests/test_pages/test_confirm_delete_transport.py -q -p no:randomly` → `479 passed`; `git diff --exit-code -- app/` → пусто.
- Гейты на закоммиченном дереве `b2a89c95`: `uv run pytest tests/test_pages/test_schedule_invariants.py tests/test_pages/test_editor_schedules.py tests/test_pages/test_confirm_delete_transport.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_services/ tests/test_routes/ tests/test_templates/ tests/test_planning/ -q -p no:randomly` → `1549 passed`, `exit=0` (8.9 мин).
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed` после записей задачи 1 и после записей задачи 2.
- `uv run python scripts/prohibitions_census.py --check` → «реестр: 741 строк, биекция с переписью — согласие». `--breakdown` → `product-invariant: enforced 57 (10), partially-enforced 2 (2), unresolved 11 (0)`, «сумма по диспозициям области решений: 321».
- `--list --phase 10 --class product-invariant`: семь строк группы несут `disposition=enforced`. У `10-50#3` поля `unresolved_reason` больше нет.
- `grep -c '^NEXT_RUN_CALCULATOR_SOURCE_DIGEST' tests/test_pages/test_schedule_invariants.py` → `1`. `git diff d69a8025..HEAD --name-only -- app/` → 0 файлов.
- Счётные гейты не сдвинулись. В модуле нет утверждений `302`, заголовка перехода и имён `*_degrades_without_htmx`. `PAIRED_302_ASSERTIONS_DECLARED` 191, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5 — гейты зелены в прогоне выше. Нового `import yaml` нет.
- `graphify update .` выполнен после правки кода.
- **Подмена полного прогона названа:** полную суиту (`just test`, около 40 мин) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют модуль правил, `test_editor_schedules.py`, `test_confirm_delete_transport.py`, три гейта страниц, каталоги `tests/test_services/`, `tests/test_routes/`, `tests/test_templates/` и `tests/test_planning/` целиком. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None — заглушек в модуле нет. Отпечаток снят с дерева и сличён по истории файла, поля посева различимы по построению.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-30 и 15-31 проходят свои группы тем же протоколом. Образец этого плана: если путь запроса к чтению закрыт выше, звать чтение напрямую и называть границу. Действующее правило искать и по ИМЕНИ ПРЕДМЕТА (так нашлись два правила обёртки, которых запись 15-13 не знала).
- Остаток `product-invariant`: 2 частичные строки и 11 неразобранных. Шесть строк переданы 15-32 прежними планами (15-26, 15-27, 15-28), этим — ни одной.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: tests/test_pages/test_schedule_invariants.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: 2034a549, 3f62b392, b2a89c95 (ledger `d69a8025..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

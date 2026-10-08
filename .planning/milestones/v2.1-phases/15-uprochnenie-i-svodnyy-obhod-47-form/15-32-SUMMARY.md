---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 32
subsystem: planning-records
tags: [prohibitions-census, registry, record-mode, owner-decision, superseded-by, row-decisions, git-history, ast, d-05, criterion-6, g-1, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-22 — `--record`, `permit_scope_uncovered`; планы 15-26…15-31 — разделы «Передано плану 15-32»; план 15-30/15-31 — модуль исторических фактов; задача 1 этого плана — `15-SUPERSEDED-ROWS.md` (16 строк)"
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "решение D-07 и план 11-02 — преемник формулировки `10-22#0`"
provides:
  - "ответ владельца по 16 строкам чекпойнта записан дословно выбранными вариантами (`15-SUPERSEDED-ROWS.md`, раздел «Ответ владельца») и машинно — полями реестра"
  - "формы ТОЛЬКО выбранных ветвей: поле строки `superseded_by` (ветвь (а)), блок документа `row_decisions` с записью `permit-row` (ветвь (б)); историческое прочтение (а′) — записи `HISTORY_FACTS` и область фазы"
  - "режим прибора: `--record … --superseded-by` (преемники проверены переписью и файлами планов), `--record … --disposition permitted` (только при записи ответа, никогда у D-05), `--permit-uncovered` принимает разрешение остатка строкой"
  - "модуль исторических фактов: область фазы `10` без коммитов `тип(10):`, три вида предиката (предикаты отказа, граница на каждом источнике идентификатора, перенос видимого текста — вид коммита), 7 записей"
  - "два правила `test_shell.py`: слои таблицы не выписаны в код правил (прочтение Б) и `_template_chain` только вычитаемым"
  - "область решений: `unresolved` 14 → 0, сумма 321; мера D-05: `enforced` 37, `partially-enforced` 24, `unresolved` 0"
affects: [15-33, критерий-6]

actuals:
  tokens: 40565
  tasks: 3
  commits: 6
plan_head_before: 66dd63eec62e44ed7dc4cd1c3e465c65200eb2b0

tech-stack:
  added: []
  patterns:
    - "Ответ владельца по строке пишется БЛОКОМ документа (`row_decisions`) в форме полей разрешения класса, но с областью-тождеством строки; поле разрешения в строке правила принимают только при записи блока с той же областью"
    - "Строка, закрытая преемником, несёт `superseded_by`: каждый преемник — тождество переписи, чья строка сама принуждена, либо номер файла плана; запись без преемников поле снимает"
    - "Вид исторического факта может судить ВЕСЬ КОММИТ, а не пару одного пути (`COMMIT_PREDICATES`): перенос текста между файлами законен"
    - "Контроль, бравший жертву из живого реестра, берёт её возвратом в копии, когда живых строк такого вида не осталось; живая строка, если есть, берётся как прежде"

key-files:
  created: []
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-SUPERSEDED-ROWS.md
    - scripts/prohibitions_census.py
    - tests/test_planning/test_plan_prohibitions_census.py
    - tests/test_planning/test_executed_plans_kept_their_scope.py
    - tests/test_pages/test_shell.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-32: ответ владельца (`chubav`, 2026-09-26, AskUserQuestion в `/gsd-execute-phase 15 --gaps-only`) записан ВЫБРАННЫМИ ВАРИАНТАМИ, а не словами владельца: Q1 «Accept all 8 (Recommended)», Q2 «22#0 (а), 18#3 (б)», Q3 «(а′), plan commits only (Recommended)», Q4 «(а) subtraction reading (Recommended)». Ветвь (в) не выбрана ни для одной строки, (г) тоже"
  - "15-32: строки прочтений (`10-37#5`, `10-51#1`, `10-38#1`) записаны `enforced` без `superseded_by`: они не замещены, а прочитаны; прочтение названо в комментарии над правилом и в артефакте"
  - "15-32: факты «фаза не заводит кодов реестра» (`10-01#3`, `10-24#2`) держатся областью ФАЗЫ над коммитами `тип(10-NN):` видом «пути не тронуты» — строже буквы (файл реестра целиком); `aa516a2e fix(10):` вне отбора по выбору владельца"
  - "15-32: `10-03#6` держится областью ПЛАНА 10-03 (как в замере артефакта); половину «ответ без слоя письма» разрешил владелец записью `row_decisions`, её поведение держит `test_every_pair_case_answers_both_transports`"
  - "15-32: `10-22#1` судит только шаблоны (цель узла живёт в разметке): правка докстринга `app/pages/schedules.py` коммитом `a3972cfd` в предмет не входит"
  - "15-32: правило согласия модуля истории больше не требует `verification: test` — владелец выбрал (а′) для строк `verification: none`"

patterns-established:
  - "Форма ответа владельца заводится только для выбранной ветви; невыбранные ветви форм не получают (нет `owner-kept-open`, нет правки правил ради буквы)"

requirements-completed: []

coverage:
  - id: D1
    description: "Ответ владельца по 16 строкам сохранён дословно выбранными вариантами с пометкой, что это слова вариантов, а не владельца"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "grep -c 'Ответ владельца' .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-SUPERSEDED-ROWS.md → 1; grep -c '### Отметка' → 0"
        status: pass
    human_judgment: true
    rationale: "Верно ли слова вариантов переданы по каждой строке, судит владелец (`chubav`): машина проверяет только наличие раздела"
  - id: D2
    description: "Формы выбранных ветвей в гейте реестра: `superseded_by` и `row_decisions`, три правила разрешения принимают область-тождество только при записи ответа; режим записи отказывает по имени на всём, чего записывать нельзя"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_superseded_by_offences_are_named_for_every_kind"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_row_decision_offences_are_named_for_every_kind"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_row_scoped_permission_is_accepted_only_with_its_record"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_record_mode_writes_superseded_by_only_with_named_successors"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_record_mode_writes_a_row_permission_only_with_its_record"
        status: pass
      - kind: integration
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_main_records_a_successor_and_a_row_permission_or_refuses"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_row_decision_has_the_permit_row_form_and_its_row_carries_it"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_superseded_by_names_existing_successors_of_an_enforced_row"
        status: pass
    human_judgment: false
  - id: D3
    description: "Исторические прочтения (а′): область фазы без `fix(10):`, три вида предиката, 7 записей; каждая краснеет на синтетическом коммите либо на доктóренной стороне «после» настоящего коммита своего плана"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_every_declared_history_fact_holds_over_its_plans_commits"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_doctored_real_revision_reddens_each_plan_15_32_content_fact"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_synthetic_plan_commit_on_the_notice_registry_reddens"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_phase_scope_selects_every_plan_of_the_phase_and_no_unscoped_commit"
        status: pass
    human_judgment: false
  - id: D4
    description: "Два правила `test_shell.py` для строк прочтений: слои таблицы (читаются разбором таблицы) не выписаны в исполняемый код модуля; `_template_chain` вне своего модуля — только вызов правым операндом вычитания"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_no_layer_of_the_table_is_written_into_the_shell_rules"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_a_layer_number_written_into_a_rule_reddens"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_template_chain_is_reused_only_as_a_subtrahend"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_a_template_chain_reused_to_build_a_chain_reddens"
        status: pass
    human_judgment: false
  - id: D5
    description: "16 строк записаны только через `--record` (15 закрыты правилом, одна разрешена); правила преемников покраснели на временной правке продукта (6 мутаций, `app/` чист после каждой)"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»; --breakdown → сумма 321, unresolved 0"
        status: pass
      - kind: other
        ref: "git diff --stat 66dd63ee..HEAD -- app/ .planning/phases/10-rychag-components-modal-html/ → пусто"
        status: pass
    human_judgment: true
    rationale: "Верность прочтений (что предикат держит именно формулировку строки, что преемник назван верно) — суждение исполнителя, записанное над каждой записью; решают владелец и верификатор фазы (D-33)"

duration: 47min
completed: 2026-09-26
status: complete
---

# Phase 15 Plan 32: Ответ владельца по 16 строкам, которые нельзя было принудить как написаны Summary

**Владелец выбрал ветвь для каждой из 16 строк, и ни одна не осталась открытой. Пять строк закрыты правилом преемника и называют его полем `superseded_by`. Три закрыты правилом по выбранному прочтению, шесть держатся коммитами своего плана или фазы. У `10-03#6` одна половина держится историей, другую владелец разрешил. `10-18#3` разрешена целиком, и её дефект WR-03 назван. Каждое правило покраснело на нарушении своей строки или своего преемника до записи. В области решений Фазы 10 не осталось ни одной строки `unresolved`.**

## Состояние критерия 6

Ветвь (в) «оставить открытой» не выбрана ни для одной строки. Поэтому этот план критерий 6 **не переоткрывает**, и строки «⚠️ КРИТЕРИЙ 6 ОСТАЁТСЯ ОТКРЫТЫМ» здесь нет. Все 321 строка области решений решены: `enforced` 93, `partially-enforced` 25 (остаток у всех 25 разрешён), `permitted` 203, `unresolved` 0. Сильная форма закрывающего правила (план 15-33) открытыми строками не заблокирована. Требование `критерий-6` не отмечалось, вердикт фазы не выносился. ⚠️ **РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ.** `10-18#3` и остаток `10-03#6` разрешены, а не принуждены.

## Performance

- **Duration:** 47 min (продолжение после чекпойнта; задачу 1 исполнял предыдущий исполнитель, коммит `5a9aa07f`)
- **Started:** 2026-09-26T06:39:50Z
- **Completed:** 2026-09-26T07:27:18Z
- **Tasks:** 3 (задача 1 — предыдущим исполнителем, задача 2 — чекпойнт с ответом, задача 3 — здесь)
- **Files modified:** 6

## Ответ владельца — дословно

Отвечал `chubav` 2026-09-26 через AskUserQuestion в `/gsd-execute-phase 15 --gaps-only`, выбирая из вариантов, которые составил оркестратор. **Своими словами оснований он не дал.** Метки ниже — слова выбранных вариантов, а не владельца.

| Вопрос | Выбранный вариант (дословно) | Строки и ветвь |
|---|---|---|
| Q1 «Recommended» | «Accept all 8 (Recommended)» | `10-33#1`, `10-35#0`, `10-56#5`, `10-33#0` — (а) преемник; `10-37#5`, `10-51#1` — (а) прочтение Б; `10-31#1`, `10-22#1` — (а′) коммиты своего плана |
| Q2 «22#0 / 18#3» | «22#0 (а), 18#3 (б)» | `10-22#0` — (а) преемник D-07 / план 11-02; `10-18#3` — (б) разрешение строки, WR-03 назван известным неисправленным дефектом |
| Q3 «Scoped rows» | «(а′), plan commits only (Recommended)» | `10-01#3`, `10-24#2`, `10-01#6`, `10-12#1` — (а′) только коммиты `(10-NN)`, `fix(10):` вне отбора; `10-03#6` — (а′) для предиката отказа плюс (б) для ответа без слоя |
| Q4 «10-38#1» | «(а) subtraction reading (Recommended)» | `10-38#1` — (а) «не строит цепь; ввоз только вычитаемым» |

Тот же ответ записан в `15-SUPERSEDED-ROWS.md` (раздел «Ответ владельца», коммит `bbc728db`).

## Запись каждой строки

Каждая запись сделана командой `--record`. «Красный» — замер до записи: временная правка продукта (m*), после которой `git checkout -- <файл>` и `git diff --exit-code -- app/` чист, либо контроль в суите на синтетике или на доктóренной копии.

| Строка | Ветвь | Диспозиция | Правило(а) | `superseded_by` / разрешение | Красный |
|---|---|---|---|---|---|
| `10-33#1` | (а) | enforced (было partially) | `test_the_third_failure_handler_body_is_unchanged`; `test_the_failure_banner_registers_its_handlers_once_per_body` | `10-52-PLAN.md#0; 10-53-PLAN.md#1; 10-57-PLAN.md#3; 10-49` | m1 (третий обработчик снят): оба `FAILED`, «регистраций `htmx:afterRequest` в сценарии 0, а не одна»; m1b (пробел в теле третьего) — первое `FAILED`, «ТЕЛО ТРЕТЬЕГО ОБРАБОТЧИКА ИЗМЕНЕНО с символа 336» |
| `10-35#0` | (а) | enforced (было partially) | те же два | то же + `10-57` | m1, m1b |
| `10-56#5` | (а) | enforced | `test_the_third_failure_handler_body_is_unchanged`; `test_a_dismissed_banner_returns_on_the_next_failure` | `10-57-PLAN.md#4; 10-57` | m1b; m2 (снята строка сброса `server_close.checked = false`): `FAILED`, «состояние органа снятия НЕ СБРОШЕНО новым отказом» |
| `10-33#0` | (а) | enforced | `test_the_failure_banner_lift_is_unconditional` | `10-51-PLAN.md#2; 10-51` | m3 (селектор подъёма под `.is-modal-open`): `FAILED`, «ПОДЪЁМ ЗАГОТОВОК ОБУСЛОВЛЕН ПРИЗНАКОМ СОСТОЯНИЯ ДОКУМЕНТА» |
| `10-22#0` | (а) | enforced | `test_the_identifier_bound_is_declared_exactly_once_in_the_whole_app`; `test_every_post_identifier_is_checked_before_its_first_use` | `11-02` | m4a (вторая копия `2_147_483_647` в `history.py`): первое `FAILED`, «объявлений величины границы … не одно, а 2»; m4b (проверка `id_in_column(log_id)` снята): второе `FAILED`, «POST-ВХОД … НЕ ПРОВЕРЕН ДО ПЕРВОГО ИСПОЛЬЗОВАНИЯ» |
| `10-37#5` | (а) Б | enforced | `test_no_layer_of_the_table_is_written_into_the_shell_rules` | — (прочтение, не замещение) | контроль: слой целым, строкой объявления и отдельным числом назван (строки 1, 6, 7 синтетики); доктóренная копия модуля — 1 находка |
| `10-51#1` | (а) Б | enforced | то же | — | то же |
| `10-38#1` | (а) вычитаемое | enforced | `test_the_template_chain_is_reused_only_as_a_subtrahend` | — | контроль: псевдоним, атрибут модуля, левый операнд, голая ссылка, `getattr` — по 1; копия модуля с `&` вместо `-` — 1 |
| `10-01#3` | (а′) фаза | enforced | `test_every_declared_history_fact_holds_over_its_plans_commits` | — | синтетический `feat(10-99)` на `app/pages/notices.py` назван; `fix(10):` на том же пути — нет |
| `10-24#2` | (а′) фаза | enforced | то же | — | то же |
| `10-31#1` | (а′) план | enforced | то же | — | синтетический `feat(10-31)` на реестре назван |
| `10-01#6` | (а′) план | enforced | то же | — | сторона «после» `14face55` (`sched_card.html`, «Заполните группы» → «Выберите группы») названа ровно этим коммитом и путём |
| `10-12#1` | (а′) план | enforced | то же | — | сторона «после» `73df7780` (`schedule_id: ScheduleIdPath` → `int`) названа |
| `10-22#1` | (а′) план | enforced | то же | — | сторона «после» `a3972cfd` (цель `innerHTML:#sched-count` → `#{{ count_target }}`) названа |
| `10-03#6` | (а′) + (б) | partially-enforced, `permit_scope_uncovered` = тождество | то же | запись `row_decisions` (остаток) | сторона «после» `1889ac05` (`if not user:` → `if user is None:`) названа |
| `10-18#3` | (б) | permitted, `permit_scope` = тождество | — | запись `row_decisions` (целиком, WR-03 назван) | правила нет по выбору владельца |

Итог реестра: `--breakdown` показывает «строк области решений с `superseded_by`: 5; с разрешением строки: 2», «частичных строк с `permit_scope_uncovered`: 25; без поля: 0», «сумма по диспозициям области решений: 321». Дифф реестра над `e3080e0c` — 16 строк заменены и добавлен блок `row_decisions` (19+/16−).

## Заведённые формы (только выбранных ветвей)

- **(а) `superseded_by`** — поле строки, `REGISTRY_ROW_FIELDS` 14 → 15 (с летописью). Правило `test_every_superseded_by_names_existing_successors_of_an_enforced_row` требует, чтобы поле стояло только у принуждённой строки области решений. Каждый преемник — номер файла плана или тождество переписи, чья строка сама принуждена, и не сама строка. Повторов и пустых частей быть не должно. Номер `11-02` принимается: поле берёт номер любого плана, не только `10-NN`.
- **(а′)** — модуль исторических фактов: область фазы `10` (коммиты `тип(10-NN):` любого плана, без `тип(10):`), виды `refusal-predicates-kept`, `identifier-sources-bounded` и `visible-text-carried` (вид коммита, `COMMIT_PREDICATES`), 7 записей `HISTORY_FACTS` с прочтением над каждой. Правило согласия принимает любую строку Фазы 10 (летопись: раньше только `verification: test`).
- **(б) `row_decisions`** — ключ документа, `REGISTRY_DOCUMENT_KEYS` 4 → 5 (с летописью), ветвь `permit-row` (`ROW_DECISION_BRANCHES_DECLARED = 1`). У записи форма полей разрешения класса, область — тождество строки, покрывает она 1 запрет, флаги распространения `false`. `_permit_scope_offences`, `_permitted_without_permission` и `_permit_scope_uncovered_offences` принимают область-тождество только при записи блока. Строка с `verification: test` разрешения строки не получает ни в гейте, ни в приборе (D-05 не ослаблен). Засев переносит блок после блока по классам.
- **Не заведены:** причина `owner-kept-open`, форма `keep-open`, правка правил `test_shell.py` ради буквы (ветви (в) и (г) не выбраны).

## Task Commits

1. **Задача 1: предмет решения** — `5a9aa07f` (docs), предыдущий исполнитель.
2. **Задача 2: ответ владельца** — `bbc728db` (docs): раздел «Ответ владельца» в `15-SUPERSEDED-ROWS.md`.
3. **Задача 3: запись ответа** — `e3c3a52b` (test, RED), `e3080e0c` (feat, GREEN), `36d8d380` (test: контроль флага берёт жертву в копии), `5bd175d7` (chore: блок `row_decisions` и 16 записей `--record`).

**Plan metadata:** коммит этой сводки `docs(15-32)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute` при `workflow.tdd_mode: true`: гейт TDD на таком плане инертен, поэтому RED назван здесь. Задача 3 добавляет поведение и прошла RED → GREEN отдельными коммитами.

- **RED `e3c3a52b`.** Три модуля с правилами и контролями. Тела семи помощников — заглушки `return []`: `_row_decision_offences`, `_superseded_by_offences`, `_refusal_predicate_changes`, `_identifier_source_offences`, `_visible_text_losses`, `layer_literals_in`, `template_chain_reuses`. Каждый из семи контролей прогнан отдельно (`uv run pytest -q -p no:randomly --junit-xml=… <модуль>::<контроль>`). Все семь дали `FAILED …::<контроль>`, строку `1 failed, 1 warning`, `exit=1`. Причинные литералы: `assert [] == ['.planning/p...AN.md#2', ...]` (преемники), `assert [] == ['решение стр...роки #5', ...]` (ответ по строкам), `assert [] == [('a.html', '...ён дословно')]`, `assert [] == ['`delete`: п...ed` добавлен']`, `assert [] == ['источник ид... без границы']`, `assert [] == ['строка 1', ...]`, `('псевдоним', [])` / `assert 0 == 1`. Запись `{command, exitCode, targetTest, output}` собрана из junit-xml в форме node:test TAP одноразовым `junit2red.py` (scratchpad, не в дереве). `check tdd-red-evidence` дал `RED_EVIDENCE_OK / target_test_failed` ×7. RED гонялся при неподготовленном приборе в рабочем дереве. Ни один из семи контролей новых атрибутов прибора не касается.
- **GREEN `e3080e0c`.** Тела помощников, прибор, записи истории, два правила шелла. `tests/test_planning/` — 205 passed, `test_shell.py` вместе с `test_failure_banner_invariants.py` — 271 passed.
- REFACTOR не было. Красный правил преемников — мутации продукта m1…m4b (таблица выше): на живом дереве такое правило красным быть не может, дерево уже в состоянии преемника.

## Files Created/Modified

- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-SUPERSEDED-ROWS.md` — раздел «Ответ владельца».
- `scripts/prohibitions_census.py` — `SUPERSEDED_BY_FIELD`, `ROW_DECISIONS_KEY`, `PERMIT_ROW_BRANCH`, `plan_numbers`, `_row_decisions`/`_row_permits`, `_successors`, `record_row_permission`, флаги `--superseded-by` и `--disposition permitted`, печать в `--check`/`--breakdown`, шапка реестра, перенос блока засевом.
- `tests/test_planning/test_plan_prohibitions_census.py` — перечни 14 → 15 и 4 → 5 с летописью, `_row_decision_offences`, `_superseded_by_offences`, область-тождество в трёх правилах разрешения, 12 новых тестов, помощники жертвы в копии (`_awaiting_enforcement`, `_partial_awaiting_enforcement`).
- `tests/test_planning/test_executed_plans_kept_their_scope.py` — область фазы, три вида, `COMMIT_PREDICATES`, 7 записей, 6 контролей (10 случаев), правило согласия.
- `tests/test_pages/test_shell.py` — `_table_layers`, `layer_literals_in`, `template_chain_reuses`, два правила и два контроля.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — шапка (засев в GREEN), блок `row_decisions` (ответ владельца) и 16 строк, записанных `--record`.

## Decisions Made

См. `key-decisions`. Отдельно о трёх прочтениях, которые решил исполнитель внутри выбранных ветвей:
- «Фаза не заводит кодов реестра» проверяется так: коммиты всех планов фазы не трогали `app/pages/notices.py` вовсе. Это строже буквы, файл судится целиком. Замер: 306 коммитов `(10-NN)`, 0 касаний. Единственный коммит, коснувшийся реестра, — `aa516a2e fix(10):`, и он вне отбора по выбору владельца.
- «Правка не ставится только там, где предмет замерен» проверяется так: после коммита плана каждый параметр-идентификатор каждого обработчика маршрута тронутого модуля несёт верхнюю границу. Вид утверждает СОСТОЯНИЕ после коммита, и это названо летописью в докстринге модуля. Поле формы, прочитанное руками (`_ad_id_from_form`), вид не судит.
- «Тексты переносятся дословно» проверяется так: в каждом коммите плана каждый фрагмент видимого текста, ушедший из шаблона, пришёл добавленным в том же коммите. Перенос между файлами законен. Замер `14face55`: 7 шаблонов, фрагменты до и после равны.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Четыре контроля брали из живого реестра строки, которых после ответа владельца не осталось**
- **Found during:** Задача 3 (до GREEN — `enforcement-required`; после записи реестра — частичная `require-enforcement` без разрешения)
- **Issue:** Два правила режима записи, контроль закрывающего правила и контроль флага `--permit-uncovered` выбирали жертву через `next(…)` по живому реестру. Ответ владельца решил последние такие строки, и `next` упал бы `StopIteration`.
- **Fix:** Помощники `_awaiting_enforcement` и `_partial_awaiting_enforcement` берут живую строку, если она есть. Иначе принуждённая целиком строка класса `require-enforcement` без `verification: test` возвращается в копии к прежнему состоянию. Летопись записана в докстринге помощников. Дерево не правится.
- **Files modified:** `tests/test_planning/test_plan_prohibitions_census.py`
- **Verification:** `tests/test_planning/` — 205 passed на записанном реестре
- **Committed in:** `e3080e0c`, `36d8d380`

**2. [Rule 3 - Blocking] Шапка реестра разошлась с прибором**
- **Found during:** Задача 3, GREEN
- **Issue:** Прибор получил абзац о `row_decisions`/`superseded_by` в `REGISTRY_HEADER`, и правило идемпотентности засева покраснело на старой шапке файла.
- **Fix:** `--seed-registry` в GREEN-коммите, изменились только 11 строк комментария шапки, строки реестра не тронуты.
- **Committed in:** `e3080e0c`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Обе правки держат существующие правила зелёными на законном состоянии, ни одно правило не ослаблено. Область файлов плана не расширена.

## Issues Encountered

- `tests/test_pages/test_shell.py` идёт около 11,5 минуты, дольше предела одного вызова. Он прогнан фоновой командой с записью вывода в файл.
- **Чего записи не держат (названо, а не скрыто).** (1) `10-22#0`: возврат границы в аннотацию POST-входа оба правила преемника оставят зелёным, потому что правило первого использования принимает «объявление ЛИБО проверку». Эту форму нарушения D-07 не замерял ни этот план, ни 15-26. (2) Строки (а′) держат только коммиты с областью плана, будущее они не запрещают (цена ветви названа в артефакте). (3) `10-18#3`: литерал WR-03 в `app/dependencies.py:323` остаётся, строка разрешена, а не соблюдена.
- `ruff` в окружении не установлен (прецедент 15-30/15-31), линтер не прогонялся.

## Verification

- `uv run pytest tests/test_planning/ -q -p no:randomly` → `205 passed` (было 177) на итоговом дереве `5bd175d7`.
- `uv run pytest tests/test_templates/ tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` → `581 passed` на `5bd175d7`.
- `uv run pytest tests/test_pages/test_shell.py tests/test_pages/test_failure_banner_invariants.py -q -p no:randomly` → `271 passed` (11:38) на `e3080e0c`. После этого коммита оба файла не менялись, изменился только реестр, а их правила реестр не читают.
- `--check` → «реестр: 741 строк, биекция с переписью — согласие», «решений владельца по строкам (`row_decisions`): 2». `--breakdown` → сумма области решений 321, `unresolved` 0, D-05: `enforced` 37, `partially-enforced` 24.
- Ни одна строка с `verification: test` не `permitted` (`--list --phase 10 | grep verification=test | grep -c disposition=permitted` → 0).
- Счётные гейты не сдвинулись: `PAIRED_302_ASSERTIONS_DECLARED` 191, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5, гейты зелены. Нового `import yaml` нет, `YAML_DIRECT_IMPORTERS` не менялся.
- `git diff --stat 66dd63ee..HEAD -- app/ .planning/phases/10-rychag-components-modal-html/` → пусто. Ни один `*-PLAN.md` и ни один дескриптор исполненного плана не правился. После каждой из шести мутаций продукта `git diff --exit-code -- app/` был чист.
- `graphify update .` выполнен.
- **Подмена полного прогона названа.** Полную суиту (`just test`) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют `tests/test_planning/`, `tests/test_templates/`, `test_shell.py`, `test_failure_banner_invariants.py` и три гейта страниц. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None. Заглушки RED-коммита (`return []  # RED: …`) заменены телами в GREEN-коммите, `grep` по трём модулям → 0.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 15-33 (сильная форма закрывающего правила): открытых строк в области решений нет, ветвь (в) не выбрана, и его предусловие открытыми строками не заблокировано. Формы, которые ему нужно судить: `superseded_by` (5 строк), `row_decisions` (2 записи), `permit_scope_uncovered` с областью-тождеством (1 строка).
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: все шесть файлов `key-files.modified`
- FOUND commits: 5a9aa07f, bbc728db, e3c3a52b, e3080e0c, 36d8d380, 5bd175d7 (ledger `66dd63ee..HEAD` = 6 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-26*

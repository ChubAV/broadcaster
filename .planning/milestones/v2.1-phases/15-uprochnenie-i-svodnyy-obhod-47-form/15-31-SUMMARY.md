---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 31
subsystem: planning-records
tags: [prohibitions-census, registry, record-mode, git-history, ast, d-05, criterion-6, g-1, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-30 — модуль `test_executed_plans_kept_their_scope.py` (журнал git, `HISTORY_FACTS`, несущее правило); план 15-13 — находки D-05 `declared-rule-absent`; план 15-22 — `--record`, `--permit-uncovered`, поле `permit_scope_uncovered`"
  - phase: 10-rychag-components-modal-html
    provides: "девять запретов D-05 без чекпойнта (10-36#1, 10-36#3, 10-37#3, 10-38#5, 10-39#2, 10-40#1, 10-40#2, 10-46#3, 10-48#3) и коммиты их планов в истории"
provides:
  - "пять видов факта содержания правки в модуле исторических фактов: исходник определений группы, поля шапки, строка пункта раздела, строки `status:` в диффе, равенство без комментариев; пара «до / после» читается `git ls-tree` + `git show` один раз за прогон"
  - "пять записей `HISTORY_FACTS` содержания (10-37#3, 10-39#2, 10-40#1, 10-40#2, 10-46#3); правило состава группы против истории плана-владельца; направление вида содержания на настоящей паре коммита `415b0cfe`"
  - "четыре правила предметов D-05 рядом с предметами: индекс 0 реестра якорей, ввозы модуля якорей, литералы свойств в контролях плана 10-38, годность посева на схеме тестовой базы"
  - "девять строк реестра записаны через `--record` (8 `enforced`, `10-48#3` — `partially-enforced` с `permit_scope_uncovered: live-environment-safety`); `declared-rule-absent` в области решений 12 → 3"
affects: [15-32, 15-33, критерий-6]

actuals:
  tokens: 18150
  tasks: 2
  commits: 5
plan_head_before: 8706da6f9002b31b2c391b2ddcdc97f8f713f861

tech-stack:
  added: []
  patterns:
    - "Факт о СОДЕРЖАНИИ правки держится парой «до / после» каждого коммита плана, коснувшегося наблюдаемого пути, и чистым предикатом вида над этой парой; каждый вид показан контролем на синтетической паре"
    - "Состав группы, который запрет называет словами («группа правил плана 10-35», «контроли плана 10-38»), снимается ИСТОРИЕЙ (определения, заведённые коммитами плана) и сверяется с объявленным литералом правилом, а не набирается руками"
    - "Правило о ввозах или чтении настроек модуля читает ТЕКСТ модуля разбором `ast` стандартной библиотеки и ничего не ввозит ради себя"

key-files:
  created: []
  modified:
    - tests/test_planning/test_executed_plans_kept_their_scope.py
    - tests/test_templates/test_walkthrough_anchors.py
    - tests/test_pages/test_shell.py
    - tests/test_planning/test_the_walkthrough_stand_is_seedable.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-31: группа правил снятия заготовок плана 10-35 (`10-37#3`) прочитана как ВСЕ определения верхнего уровня, заведённые коммитами `(10-35)` в `test_shell.py`: 8 функций и 5 констант, а не только функции таблицы планирования. «Ни на символ» и «группа правил» включают данные, на которых правила стоят"
  - "15-31: `10-46#3` держится над обоими названными файлами и над всем ПРОДУКТОМ (22 корня плана 15-30): любой файл продукта, которого коснулся коммит плана 10-46, равен себе без комментариев (`.py` — `ast.dump`, `.html` — без `{# … #}`, прочее — целиком)"
  - "15-31: `10-38#5` держится над контролями, которые коммит `9809b643` завёл и которые стоят в дереве (2 функции). Третий контроль коммита (`test_control_a_trapping_ancestor_reddens`) снят планом 10-42; канон `ANCESTOR_TRAP_CANON` выписан литералами по решению плана 10-42 и в состав не входит. Строка записана `enforced`: буква исполнима на сегодняшнем составе, замещённого состояния правило не утверждает"
  - "15-31: строки `10-37#5`, `10-38#1`, `10-51#1` не записывались: их буква расходится с прочтением дерева, решение за владельцем на чекпойнте плана 15-32 (раздел «Передано плану 15-32» с обеими формулировками)"

patterns-established:
  - "Вид факта содержания отказывает, а не зеленеет, когда сличать нечего: группы нет до коммита, поля нет в шапке, раздела нет или пункт неоднозначен, дифф пуст, коммиты плана не коснулись ни одного наблюдаемого пути"

requirements-completed: []

coverage:
  - id: D1
    description: "Пять видов факта содержания: каждый называет изменение своего предмета на синтетической паре и молчит на изменении вне предмета; пара без предмета — отказ; разводка читает только тронутые наблюдаемые пути"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_changed_group_definition_is_named_and_an_outside_one_is_not"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_changed_header_field_is_named_and_an_added_one_is_not"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_changed_section_line_is_named_and_a_neighbour_is_not"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_removed_status_line_is_named_and_an_insertion_is_not"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_an_executable_change_is_named_and_a_comment_change_is_not"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_content_fact_reads_every_touched_watched_path_and_refuses_on_none"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пять исторических запретов содержания держатся коммитами своих планов; состав группы 10-37#3 сверен с историей плана 10-35; направление показано на настоящей паре 415b0cfe"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_every_declared_history_fact_holds_over_its_plans_commits"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_every_definition_group_is_what_its_owner_plan_introduced"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_doctored_revision_of_a_real_commit_reddens_10_40_1"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_every_history_fact_names_a_phase_10_prohibition_by_identity"
        status: pass
    human_judgment: false
  - id: D3
    description: "Четыре правила предметов D-05 в суите с контролями на синтетике: индекс 0 реестра якорей, ввозы модуля якорей, литералы свойств в контролях плана 10-38 (состав сверен с историей), годность посева на схеме тестовой базы"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_walkthrough_anchors.py#test_the_record_at_index_zero_is_the_declared_victim_of_the_control"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_walkthrough_anchors.py#test_control_a_registry_with_its_first_records_swapped_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_walkthrough_anchors.py#test_this_module_imports_nothing_from_the_records_and_pages_suites"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_walkthrough_anchors.py#test_control_every_cross_suite_import_form_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_ancestor_chain_controls_take_property_names_from_the_canon"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_a_control_that_writes_a_property_name_literally_reddens"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_the_plan_10_38_control_group_in_the_shell_suite_is_what_history_introduced"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_the_walkthrough_stand_is_seedable.py#test_the_seed_validity_is_shown_on_the_test_schema_only"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_the_walkthrough_stand_is_seedable.py#test_control_every_live_database_read_form_is_named"
        status: pass
    human_judgment: false
  - id: D4
    description: "Девять строк реестра записаны только через `--record`; `declared-rule-absent` осталась ровно у трёх строк; биекция 741 строки в согласии"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --breakdown → «declared-rule-absent: 3»; «мера покрытия … (D-05, 61): enforced 32, partially-enforced 26, unresolved 3»"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
    human_judgment: false
  - id: D5
    description: "Прочтение формулировок в предикаты: группа 10-35 = 13 определений, 10-46#3 над всем ПРОДУКТОМ, 10-38#5 над двумя сохранившимися контролями, 10-39#2 строже буквы (все строки `status:` файла)"
    requirement: "критерий-6"
    verification: []
    human_judgment: true
    rationale: "Перевод прозы запрета в предикат — суждение исполнителя, записанное комментарием над каждой записью и в докстрингах правил. Верно ли оно читает формулировки, решают владелец (`chubav`) и верификатор фазы"

duration: 30min
completed: 2026-09-26
status: complete
---

# Phase 15 Plan 31: Факты содержания правки и правила предметов D-05 Summary

**Модуль исторических фактов теперь проверяет и содержание правки. Для каждого коммита плана он читает пару «до / после» наблюдаемого пути и судит её чистым предикатом одного из пяти видов. Так держатся пять запретов вида «в тронутом файле не изменено вот это». Ещё четыре запрета держатся правилами рядом со своими предметами в суите. Из 27 находок D-05 без правила осталось три, их прочтение решает владелец на чекпойнте плана 15-32.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-09-26T00:21:34Z
- **Completed:** 2026-09-26T00:51:36Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- **Задача 1 (TDD).** `HistoryFact` получил вид предиката (`kind`), наблюдаемые пути (`watched`), данные вида (`subject`) и план-владельца группы (`owner`). Пять чистых предикатов пары: `_definition_source_changes`, `_header_field_changes` (шапку разбирает `_frontmatter` прибора, PyYAML не ввозится), `_section_line_changes`, `_status_line_changes` (`difflib` без эвристики «мусора»), `_executable_changes`. Разводка `_content_offences` читает только пути, которых коснулся коммит плана и которые покрыты `watched`. Пара берётся через `git ls-tree` и `git show`, кэшируется. Правило согласия различает виды: у вида путей только `forbidden`; у видов содержания `watched`, при нужде `subject`, у группы определений ещё `owner`.
- **Задача 2.** Четыре правила в модулях своих предметов. Контроль каждого — на синтетике (подробно в таблице ниже).
- **Реестр.** Девять строк переведены из `unresolved` (`declared-rule-absent`) через `--record`. `declared-rule-absent` в области решений 12 → 3. Мера покрытия D-05 (61): `enforced` 32, `partially-enforced` 26, `unresolved` 3. Строк с `permit_scope_uncovered` стало 24 вместо 23, добавилась `live-environment-safety`: 1.

## Девять записей

| Тождество | Класс | Вид / место правила | Предмет по полной формулировке | Пар (коммит, путь) | Живое | Синтетика / подмена | Диспозиция |
|---|---|---|---|---|---|---|---|
| `10-37#3` | plan-file-scope | исходник определений группы | 13 определений плана 10-35 в `test_shell.py` не меняются коммитами `(10-37)` | 6 | 0 | правка `_scratch_lever` → 6 названий | enforced |
| `10-39#2` | self-certification | строки `status:` в диффе | ни одна строка `status:` в `10-UAT.md` не удалена и не изменена | 2 (`9a7ca686`, `e6c655a9`) | 0 | `failed` → `resolved` → 2 | enforced |
| `10-40#1` | self-certification | поля шапки | `status`, `score`, `gaps`, `re_verification` шапки `10-VERIFICATION.md` | 1 (`415b0cfe`) | 0 | `status: passed` → 1 (контроль в суите) | enforced |
| `10-40#2` | record-immutability | строка пункта раздела | пункт 3 раздела `### Phase 10:` в `ROADMAP.md` | 1 (`d942693f`) | 0 | правка критерия → 1 | enforced |
| `10-46#3` | plan-file-scope | равенство без комментариев | `modal.html`, `schedules.py` и весь ПРОДУКТ | 2 (`77d0c207`) | 0 | исполняемая строка → 2 | enforced |
| `10-36#1` | gate-integrity | `test_walkthrough_anchors.py` | запись на индексе 0 = `FIRST_ANCHOR_DECLARED` (`[role="dialog"]`, `components/modal.html`, шаг 1.1) | — | 0 | переставленные первые записи → 1 | enforced |
| `10-36#3` | gate-integrity | `test_walkthrough_anchors.py` | ни одного ввоза из `tests.test_planning*`, `tests.test_pages*` и ввоза `_strip_comments` (по `ast` своего текста) | — | 0 | 6 форм ввоза → по 1 | enforced |
| `10-38#5` | gate-integrity | `test_shell.py` | в исполняемом теле `PLAN_10_38_ANCESTOR_CHAIN_CONTROLS` нет литерала имени свойства (19 имён перечней, `LAYER_PROPERTY`, `INTENT_PROPERTY`, канона) | — | 0 | `"opacity"`, `"opacity: 0.5"` → 2; подмена `f"{LAYER_PROPERTY}: 3"` на `"z-index: 3"` в живой функции → 1 | enforced |
| `10-48#3` | live-environment-safety | `test_the_walkthrough_stand_is_seedable.py` | правило берёт `db_session` и исполняет цикл посева; фикстура строит движок на `sqlite+aiosqlite:///:memory:`; модуль не читает адреса боевой базы | — | 0 | 8 форм чтения → каждая названа | **partially-enforced** |

Для `10-48#3` записаны два правила: `test_the_seeded_row_satisfies_todays_schema` и `test_the_seed_validity_is_shown_on_the_test_schema_only`. Заметка покрытия: «действие исполнителя «посев не запускался на живой базе» следа в дереве не оставляет». Поле `permit_scope_uncovered: live-environment-safety`.

## Составы групп, снятые историей

- **Группа плана 10-35 (`10-37#3`)** — определения верхнего уровня, заведённые в `tests/test_pages/test_shell.py` коммитами `(10-35)`:
  - `ba908912` — пять констант (`MODAL_OPEN_METHOD`, `MODAL_CLOSE_METHOD`, `FAILURE_BANNER_HIDDEN_ATTR`, `_JS_BLOCK_COMMENT_RE`, `_MODAL_OPEN_METHOD_RE`) и три функции (`_lever_show_body`, `_lever_clearing_findings`, `test_the_lever_clears_both_failure_banners_when_the_panel_opens`);
  - `6f3b8b55` — пять функций (`_lever_raises_the_scroll_lock`, `_scratch_lever`, `_lever_clearing_chunk`, `test_control_a_lever_that_keeps_a_stale_banner_reddens`, `test_control_a_lever_that_names_the_flag_only_in_prose_reddens`);
  - `b3a3fa3c` новых определений не завёл: он правил чужую `test_failure_banner_has_single_source`.

  Литерал `PLAN_10_35_GROUP` сверяет с историей правило `test_every_definition_group_is_what_its_owner_plan_introduced`. Коммиты `(10-37)` не меняли ни одного из 13 определений: 6 пар, 0 изменений.
- **Контроли плана 10-38 (`10-38#5`)** — коммит `9809b643` завёл три контроля: `test_control_a_banner_lift_block_without_a_fixed_position_reddens`, `test_control_a_trapping_ancestor_reddens`, `test_control_a_layer_on_an_in_flow_ancestor_does_not_redden`. Второй снят планом 10-42 (`a4b3947c`). Литерал `PLAN_10_38_ANCESTOR_CHAIN_CONTROLS` — два сохранившихся контроля. С историей его сверяет `test_the_plan_10_38_control_group_in_the_shell_suite_is_what_history_introduced`: модуль `test_shell.py` там читается текстом, а не ввозится.

## Передано плану 15-32

Три строки не записывались. Буква каждой расходится с прочтением дерева, а решать, что закрепить, — владельцу. Координаты сняты на дереве после этого плана: правило `10-38#5` вставлено выше, и строки `test_shell.py` сдвинулись на 107.

**`10-37#5`** (gate-integrity). Формулировка запрета: «ЛИТЕРАЛОВ СЛОЯ В ИСПОЛНЯЕМОМ КОДЕ ПРАВИЛ НЕ ПОЯВЛЯЕТСЯ: инвариант объявлен блоком подъёма и соблюдён партией 10-33; числа читаются из таблицы и сличаются между собой».
- *Прочтение А (план 15-13, запись нарушения):* литерал слоя стоит в исполняемом коде правил. Это `test_shell.py:6896` (было `:6789`), `AncestorTrapCase("z-index", LAYER_GROUP, "auto", "3", …)`, и `:7509` (было `:7402`), `"z-index: 3"` в контроле плана 10-37 `test_control_an_ancestor_layer_split_across_two_blocks_reddens`.
- *Прочтение Б (замер планирования и этого плана):* «литерал слоя» — это числа слоёв таблицы (`app.css:946` `z-index: 60`, `:1196` `z-index: 70`). Разбор `ast` находит 60/70 в исполняемом коде функций `test_shell.py` 0 раз. Значение `3` в этих местах — значение синтетического доктóривания, а не слой таблицы.
- По прочтению А правило красно на дереве сегодня, по прочтению Б зелено. Писать его в более лёгкой форме план запрещает.

**`10-51#1`** (gate-integrity). Формулировка запрета: «ЧИСЛО СЛОЯ В ПРАВИЛО НЕ ВЫПИСЫВАЕТСЯ: оба слоя читаются из таблицы и сличаются между собой, и правка любого из двух не имеет права разойтись с правилом молча».
- Прочтения те же, что у `10-37#5`, и места те же (`:6896`, `:7509`). По А литерал `3` — «число слоя, выписанное в правило». По Б числа слоёв таблицы (60, 70) в правило не выписаны (0 по `ast`).

**`10-38#1`** (gate-integrity). Формулировка запрета: «`_template_chain` ИЗ `tests/test_pages/test_hx_location_destinations.py` НЕ ПЕРЕИСПОЛЬЗУЕТСЯ: его докстринг объявляет границей ИЗЪЯТИЕ подключения макросов, а рычаг подключается именно им — правило на этой цепи было бы вакуумно зелёным при любой разметке. Предмет другой, и это называется в комментарии, а не решается молча».
- *Буква:* нарушена самим планом 10-38. Коммит `2bfa658c` (`feat(10-38)`) ввёз `_template_chain` в `test_shell.py:8161` (было `:8054`) и вычитает его: `macro_only = _template_graph_from(AUTH_SHELL_ROOT) - _template_chain(AUTH_SHELL_ROOT)` (`:8163`).
- *Дух:* «правило рычага не строится на этой цепи» соблюдён. Цепь служит вычитаемым, чтобы выделить рёбра подключения макросов, а не основой правила. Разница названа в комментариях `:7698`, `:7885`, `:8037`.
- Закрепить букву значит закрепить красное. Закрепить дух значит переформулировать запрет, а это делает только владелец.

**К сведению владельца (строка записана, а не передана): `10-38#5`.** Контроль, о котором запрет говорит «представитель группы выбирается ИНДЕКСОМ», снят планом 10-42. Его преемник `test_control_every_canon_case_reddens_on_its_trapping_value` перебирает канон `ANCESTOR_TRAP_CANON`. Канон выписан литералами намеренно: «довод плана 10-38 против литеральной копии остаётся верным и закрывается здесь, а не отменяется» — правилом согласия канона с перечнями. Правило этого плана держит букву на двух сохранившихся контролях плана 10-38. Канон и преемник в состав не входят. Замер тем же предикатом по всем `test_control_*` модуля: литералы имён свойств есть ещё в шести контролях других планов, например `test_control_an_individual_transform_on_an_ancestor_reddens` (10-37). Ни один из них не входит в предмет запрета, который здесь закреплён.

## Task Commits

1. **Задача 1: пять фактов содержания** — `aa4c89ba` (test, RED), `9eb783aa` (feat, GREEN), `d5cb2ecd` (chore: 5 строк реестра).
2. **Задача 2: четыре правила предметов** — `180ed7b4` (feat), `7a3f73e5` (chore: 4 строки реестра, одна частичная).

**Plan metadata:** коммит сводки `docs(15-31)`, за ним коммит учёта STATE/ROADMAP.

## TDD

План имеет `type: execute`, задача 1 — `tdd="true"`.

- **RED** `aa4c89ba`. Шесть контролей и пять предикатов с разводкой без тел (возвращают `[]`). Каждый контроль прогнан отдельно: `uv run pytest -q -p no:randomly --junit-xml=… <модуль>::<контроль>`. Каждый дал `FAILED …::<контроль>`, `1 failed, 1 warning`, `exit=1`. Причинный литерал везде — утверждение «назван»: `AssertionError: assert [] == ['`kept_rule`...ения изменён']` (первый контроль), `assert [] == ["поле шапки ...' → 'passed'"]`, `assert [] == ["строка пунк... добавляет']"]`, `assert [] == ['строка `sta...или изменена']`, `assert [] == ['исполняемое...омментариев)']`, `assert [] == [ContentOffen...ли изменена')]`. Запись `{command, exitCode, targetTest, output}` собрана из junit-xml в форме node:test TAP одноразовым `junit2red.py` (scratchpad, не в дереве). `check tdd-red-evidence` → `RED_EVIDENCE_OK / target_test_failed` ×6.
- **GREEN** `9eb783aa`. Тела предикатов, пять записей и два правила над живой историей. Модуль — `34 passed`.
- REFACTOR не было. RED у записей над живой историей — подмена стороны «после» настоящей пары (таблица выше). Правило над историей не может быть красным на живом дереве: история чиста.

## Files Created/Modified

- `tests/test_planning/test_executed_plans_kept_their_scope.py` — виды фактов содержания, `_revisions`/`_blob`, `_definitions`, `_introduced_definitions`, 5 записей, 6 контролей, 3 правила (+720 строк).
- `tests/test_templates/test_walkthrough_anchors.py` — `FIRST_ANCHOR_DECLARED`, `index_zero_findings`, `cross_suite_imports`, 2 правила, 2 контроля, ввоз `ast` (+153).
- `tests/test_pages/test_shell.py` — `PLAN_10_38_ANCESTOR_CHAIN_CONTROLS`, `property_literals_in`, правило и контроль (+107).
- `tests/test_planning/test_the_walkthrough_stand_is_seedable.py` — `live_database_reads`, правило и контроль (+149).
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — 9 строк, записаны только через `--record` (дифф 9/9).

## Decisions Made

См. `key-decisions`. Все прочтения записаны комментарием над записью или в докстринге правила.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Состав групп сверяется с историей правилом, а не только объявлен литералом**
- **Found during:** Задачи 1 и 2
- **Issue:** План велит снять составы `10-37#3` и `10-38#5` историей и объявить литералом с летописью. Литерал без сверки мог бы разойтись с историей молча, и правило над ним ослабло бы, не покраснев.
- **Fix:** Два правила: `test_every_definition_group_is_what_its_owner_plan_introduced` и `test_the_plan_10_38_control_group_in_the_shell_suite_is_what_history_introduced`. Второе стоит в модуле исторических фактов: модуль есть в `files_modified` плана, но не в `<files>` задачи 2. Добавлено в конец модуля, чтобы не сдвигать координату несущего правила.
- **Files modified:** `tests/test_planning/test_executed_plans_kept_their_scope.py`
- **Verification:** оба правила зелены; литерал с лишним или пропущенным именем даёт красное с названием расхождения.
- **Committed in:** `9eb783aa`, `180ed7b4`

**2. [Rule 3 - Blocking] `import ast` в модуле якорей**
- **Found during:** Задача 2 (`10-36#3`)
- **Issue:** Правило «модуль ничего не ввозит из каталогов записи и страниц» читает свой текст разбором `ast`.
- **Fix:** Ввоз `ast` из стандартной библиотеки. Запрету он не противоречит, и правило его не называет.
- **Committed in:** `180ed7b4`

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Обе правки усиливают правила, область плана не расширена. Число записанных строк, их диспозиции и три переданные строки совпадают с планом.

## Issues Encountered

- **Координаты `rule_site`.** Правила плана 15-30 стоят теперь ниже, чем записано у их 14 строк (`:414` при фактическом `:1015`). Повторная запись через `--record` координату не двигает, так задумано прибором: «КООРДИНАТА ЕСТЬ ДЕНЬ ЗАМЕРА», гейт номер строки не утверждает. Замер по реестру: 36 из 169 координат и до этого плана не совпадали с деревом. Реестр не правился.
- `ruff` в окружении не установлен, линтер не прогонялся. Сборка и суиты зелены.

## Verification

- `uv run pytest tests/test_planning/test_executed_plans_kept_their_scope.py -q -p no:randomly` → `35 passed`. Из них 19 случаев несущего правила: 14 путей и 5 содержания.
- `uv run pytest tests/test_pages/test_shell.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_planning/ -q -p no:randomly` → `608 passed` (12:48). Счётные гейты не сдвинулись и чисел не переставляли.
- `uv run pytest tests/test_templates/ -q -p no:randomly` → `397 passed`.
- `grep -c '^import yaml\|^from yaml' tests/test_planning/test_executed_plans_kept_their_scope.py` → `0`. Новых прямых импортёров PyYAML нет, `YAML_DIRECT_IMPORTERS` не менялся.
- `grep -c '^from tests\|^import tests' tests/test_templates/test_walkthrough_anchors.py` → `0`.
- `--breakdown` → `declared-rule-absent: 3`. Это ровно `10-37#5`, `10-38#1`, `10-51#1` (`--list --phase 10 | grep unresolved | grep -v product-invariant`).
- `--check` → «реестр: 741 строк, биекция с переписью — согласие».
- `git diff --stat 8706da6f..HEAD -- .planning/phases/10-rychag-components-modal-html/` → пусто. Ни один `*-PLAN.md` и ни один дескриптор исполненного плана не правился. `15-UAT.md` не тронут.
- `graphify update .` выполнен.
- **Подмена полного прогона названа.** Полную суиту (`just test`) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют `tests/test_planning/`, `tests/test_templates/`, `tests/test_pages/test_shell.py` и три гейта страниц целиком. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None. Тела предикатов из RED-коммита заменены в GREEN-коммите.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Плану 15-32 переданы три строки с обеими формулировками (раздел выше). Строка `10-38#5` записана, но её контекст (план 10-42) вынесен к сведению владельца.
- Правила над историей читают её от `HEAD`. Коммиты `(15-31)` области `(10-NN)` не несут, поэтому после учётного коммита правила остаются зелёными.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: все пять файлов `key-files.modified`
- FOUND commits: aa4c89ba, 9eb783aa, d5cb2ecd, 180ed7b4, 7a3f73e5 (ledger `8706da6f..HEAD` = 5 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-26*

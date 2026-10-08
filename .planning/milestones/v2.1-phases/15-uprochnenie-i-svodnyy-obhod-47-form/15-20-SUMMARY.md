---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 20
subsystem: planning-records
tags: [prohibitions, census, registry, in-01, in-02, census-error, refusal-path, criterion-6]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-15: прибор переписи с фиксированным набором и реестром на 741 строку; 15-REVIEW.md §IN-01 / §IN-02"
provides:
  - "IN-01: ключ `verification`, присутствующий без значения (`verification:` или `verification: \"\"`), — `CensusError` с тождеством элемента; отсутствие ключа — `None`, как прежде; подпись «—» (`verification_label`) — только у записи без ключа"
  - "IN-02: испорченный реестр — `ОТКАЗ:` и код 1 вместо трассы: документ не отображение (или не YAML), `rows` не список, строка не отображение / без `plan` / без `index` / `plan` не строка / `index` не целое или булево, блок `class_decisions` не список, решение не отображение"
  - "`_class_decisions` — единственный вход `_check` и `_branch_by_class` в блок ответа владельца"
affects: [15-21, 15-22, 15-23, 15-24, 15-25, 15-26, 15-27, 15-28, 15-29, 15-30, 15-31, 15-32, 15-33, phase-15-verification, criterion-6]

actuals:
  tokens: 4422
  tasks: 2
  commits: 4
plan_head_before: 2566a0bd8a9efda618c1b8141d7dd7100ec1df15

tech-stack:
  added: []
  patterns:
    - "у отсутствия ключа и у ключа без значения разные исходы: первое — признак `None`, второе — отказ по имени; третьего состояния в записи нет"
    - "проверка формы строки реестра — чистая функция строки (`_registry_row_problem`), отказ называет позицию и найденное; порядок строк на вердикт не влияет"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-20-SUMMARY.md
  modified:
    - scripts/prohibitions_census.py
    - tests/test_planning/test_plan_prohibitions_census.py

key-decisions:
  - "15-20: IN-01 закрыт отказом, а не третьим значением: ключ `verification` без значения (null или пустая строка) — `CensusError` с тождеством `…#N`; смысл `None` в записи не менялся, строки реестра без поля остаются без поля (живое дерево пустых ключей не несёт: `--check` зелен, разбивка `--breakdown` посимвольно та же)"
  - "15-20: IN-02 — испорченный реестр называется и не чинится: проверки формы в `load_registry` / `_registry_rows` / новой `_class_decisions`; пустой документ остаётся пустым реестром; формат реестра на диске не менялся, перезасев не делался (`--seed-registry` → «реестр не изменился: 741 строк»)"

patterns-established:
  - "Любой новый путь чтения ввода прибора переписи обязан отказывать `CensusError`, а не трассой: `main()` печатает `ОТКАЗ:` только для неё"

requirements-completed: ["критерий-6"]

coverage:
  - id: D1
    description: "Ключ `verification` без значения (`verification:` и `verification: \"\"`) — отказ по имени с тождеством `99-01-PLAN.md#0`; отсутствие ключа — `None`, `none` — строка `none`; «—» разбивки только у записи без ключа"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_a_present_but_empty_verification_key_is_refused_by_name"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_an_empty_string_verification_key_is_refused_by_name"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_verification_label_is_a_dash_only_for_an_absent_key"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_verification_none_and_an_absent_key_are_not_mixed"
        status: pass
    human_judgment: false
  - id: D2
    description: "Испорченный реестр отказывает `CensusError` с позицией / типом: документ-список, `rows` не список, шесть видов порчи строки в обоих порядках, решение по классу — строка, блок решений — не список; пустой документ — пустой реестр"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_a_registry_that_is_not_a_mapping_is_refused_by_name"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_malformed_registry_row_is_refused_by_its_position"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_a_malformed_class_decision_is_refused_by_name"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_a_registry_whose_rows_are_not_a_list_is_refused_by_name"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_an_empty_registry_document_is_still_an_empty_registry"
        status: pass
    human_judgment: false
  - id: D3
    description: "Сквозной контроль: `main([\"--check\"])` при `TREE_ROOT` в `tmp_path` с синтетическим планом и испорченным реестром (три вида порчи) — код 1 и строка `ОТКАЗ:` в потоке ошибок; на живом дереве `--check`, `--breakdown`, `--list`, `--reconcile`, `--draft-classes` — код 0"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_main_prints_the_refusal_line_on_a_malformed_registry"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие», код 0"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 20: прибор переписи отказывает по имени (IN-01, IN-02) Summary

**Ключ `verification` без значения и испорченный реестр (документ-список, строка без `plan`/`index`, `index` не целое или булево, решение по классу — строка) теперь дают `CensusError` с тождеством или позицией, а `main()` печатает `ОТКАЗ:` с кодом 1 вместо трассы `AttributeError` / `KeyError` / `ValueError` / `TypeError`**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-25T09:12:14Z
- **Completed:** 2026-09-25T09:18:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- IN-01: `_verification_of` различает три случая. Ключа нет — `None`. Ключ без значения (null YAML или пустая строка) — `CensusError` «`…#N`: ключ `verification` присутствует без значения — объявите значение или уберите ключ». Иначе — строка значения. Подпись `verification_label` («—» только при `None`) общая у `--list` и `--breakdown`. `record.verification or "—"` из прибора ушёл.
- IN-02: `load_registry` принимает только отображение. Пустой документ по-прежнему даёт пустой реестр, текст не-YAML тоже отказывает. `_registry_rows` проверяет каждую строку чистой функцией `_registry_row_problem` и называет позицию и найденное. `_class_decisions` — единственный вход в блок `class_decisions` для `_check` и `_branch_by_class`.
- Живое дерево не сдвинуто: `--check` даёт «741 строк, биекция с переписью — согласие». Вывод `--breakdown` посимвольно совпадает с выводом до правки. `--seed-registry` даёт «реестр не изменился». `tests/test_planning/` — 130 passed (было 114, прибавилось 16 новых правил и параметров).

## TDD

План `type: tdd`. На каждую задачу RED закоммичен отдельным `test(15-20)`, GREEN — отдельным `feat(15-20)`. Каждый RED-запуск шёл из одного целевого теста с `-p no:randomly`. Запись переведена из `--junit-xml` в TAP одноразовым скриптом в scratchpad (не закоммичен). `check tdd-red-evidence` оба раза вернул `RED_EVIDENCE_OK` (`target_test_failed`).

| Задача | RED-коммит | Упавший тест (`FAILED …`, последняя строка `1 failed, 1 warning in …`) | Причинный литерал отказа | GREEN |
|---|---|---|---|---|
| 1 (IN-01) | `f9c71719` | `FAILED tests/test_planning/test_plan_prohibitions_census.py::test_a_present_but_empty_verification_key_is_refused_by_name` | `Failed: DID NOT RAISE <class 'scripts.prohibitions_census.CensusError'>` | `07ca356b` (feat) |
| 2 (IN-02) | `b4ea3068` | `FAILED tests/test_planning/test_plan_prohibitions_census.py::test_a_registry_that_is_not_a_mapping_is_refused_by_name` | `AttributeError: 'list' object has no attribute 'setdefault'` (`scripts/prohibitions_census.py`, `document.setdefault("rows", [])`) | `91b07ebd` (feat) |

В RED-коммите задачи 2 вместе с целью падали ещё 11 правил и параметров той же задачи. Правило `test_an_empty_registry_document_is_still_an_empty_registry` было зелёным до правки, и это задумано: оно проверяет, что проверка формы не превращает пустой документ в отказ. REFACTOR-коммита нет.

## Task Commits

1. **Задача 1 RED** — `f9c71719` (test)
2. **Задача 1: ключ без значения — отказ по имени** — `07ca356b` (feat)
3. **Задача 2 RED** — `b4ea3068` (test)
4. **Задача 2: проверки формы реестра, `_class_decisions`** — `91b07ebd` (feat)

**Plan metadata:** docs(15-20) — коммит сводки и трекинга.

## Files Created/Modified

- `scripts/prohibitions_census.py`: добавлены `ABSENT_VERIFICATION_LABEL`, `_verification_of`, `verification_label`, `_registry_row_problem`, `_class_decisions`. Проверки формы встали в `load_registry` и `_registry_rows`. `_check` и `_branch_by_class` читают решения через одну проверку. Дополнены докстринги `ProhibitionRecord` и `main`.
- `tests/test_planning/test_plan_prohibitions_census.py`: добавлены 8 функций правил (16 прогонов с параметрами), синтетика IN-01 / IN-02 и объявленные литералы `SYNTHETIC_FIRST_IDENTITY`, `REFUSAL_PREFIX`, `REFUSAL_EXIT_CODE` и другие. `import yaml` модуль по-прежнему не несёт: реестр пишется текстом.

## Decisions Made

- Пустая строка приравнена к null: обе дают отказ (так требует `<behavior>` плана). Строка из одних пробелов тоже считается пустой (`not value.strip()`), потому что значения она не объявляет.
- `plan` строки реестра обязан быть строкой. План называл `plan` (строка), и прежний код молча делал `str(row["plan"])`, то есть подставлял значение. Эта подстановка убрана.
- Правило «—» проверено на функции подписи, а не на выводе `--breakdown`. После правки IN-01 пустую строку в записи через разбор уже не получить, поэтому контракт подписи проверен на записи, построенной вручную.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Текст реестра, не разбираемый YAML, тоже идёт путём `ОТКАЗ:`**
- **Found during:** Задача 2
- **Issue:** Проверка формы документа в `load_registry` закрывала четыре вида порчи из §IN-02. При этом `yaml.YAMLError` испорченного текста всё ещё уходил трассой мимо `except CensusError`, а докстринг `main` по плану обещает, что каждый вид порчи ввода идёт путём `ОТКАЗ:`.
- **Fix:** `yaml.YAMLError` перехватывается и превращается в `CensusError` «реестр … не разбирается YAML». Так же шапки планов уже обрабатывает `_frontmatter`.
- **Files modified:** `scripts/prohibitions_census.py`
- **Verification:** весь каталог `tests/test_planning/` зелен; `--check` на живом дереве — код 0.
- **Committed in:** `91b07ebd`

**2. [Scope] Правил на пять больше, чем называет план**
- **Found during:** задачи 1 и 2
- **Issue:** `<artifacts_this_phase_produces>` называет пять имён правил. `<behavior>` плана требует ещё три случая: пустую строку, подпись «—» и `rows` не списком. Отдельным контролем добавлен пустой документ.
- **Fix:** добавлены `test_an_empty_string_verification_key_is_refused_by_name`, `test_the_verification_label_is_a_dash_only_for_an_absent_key`, `test_a_registry_whose_rows_are_not_a_list_is_refused_by_name`, `test_an_empty_registry_document_is_still_an_empty_registry`. Все пять названных планом имён есть дословно.
- **Committed in:** `f9c71719`, `b4ea3068`

---

**Total deviations:** 2 (1 Rule 2, 1 scope: правил больше названных)
**Impact on plan:** обе правки обслуживают обещание плана «каждый вид порчи — `ОТКАЗ:`». Формат реестра и смысл `None` не менялись.

## Issues Encountered

None.

## Verification

- `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k "verification"` → 10 passed.
- `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k "refused or malformed or registry"` → 23 passed.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → 130 passed.
- `uv run pytest tests/test_templates/test_htmx_inventory.py -q -p no:randomly` → 30 passed (единственный другой модуль, который упоминает прибор, и тот только в комментариях).
- `grep -c 'record.verification or' scripts/prohibitions_census.py` → 0; `grep -c 'def _class_decisions' scripts/prohibitions_census.py` → 1.
- `scripts/prohibitions_census.py --check` / `--breakdown` / `--list` / `--reconcile` / `--draft-classes` → код 0 у каждого. `--seed-registry` → «реестр не изменился: 741 строк».
- **Замена полного прогона:** полный `just test` (около 40 мин) после волны 6 (после 15-21) запускает оркестратор. Здесь он не запускался по указанию диспетчера, а запись в `WINDOWS.md` не открывалась. Вместо него прогнан весь каталог `tests/test_planning/` и модуль, упоминающий прибор.

## Known Stubs

None.

## User Setup Required

None: внешней настройки план не требует.

## Next Phase Readiness

- Готов план 15-21 (второй план волны 6). Планы 15-22…15-33 правят реестр. Формат реестра на диске не менялся, и порча, внесённая при их правках, теперь выйдет строкой `ОТКАЗ:` с позицией, а не трассой.
- Требование `критерий-6` в `REQUIREMENTS.md` не помечалось: по указанию диспетчера это делает закрытие фазы.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

## Self-Check: PASSED

- Файлы на месте: `scripts/prohibitions_census.py`, `tests/test_planning/test_plan_prohibitions_census.py`, `15-20-SUMMARY.md`.
- Коммиты в дереве: `f9c71719`, `07ca356b`, `b4ea3068`, `91b07ebd`. Счёт `git rev-list --count 2566a0bd..HEAD` = 4 до коммита сводки.
- Гейт TDD: коммитов `test(15-20)` — 2, `feat(15-20)` — 2; каждый RED предшествует своему GREEN. Удалений файлов нет.

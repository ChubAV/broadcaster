---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 01
subsystem: testing
tags: [records, test_planning, prohibitions-census, milestone-start, pytest]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "суита записей tests/test_planning, прибор scripts/prohibitions_census.py, реестр запретов в архиве v2.1"
provides:
  - "развилки «законная пустота старта вехи / вакуум» в трёх модулях записей с синтетическими контролями"
  - "REQUIREMENT_ROWS_DECLARED картой по вехе записи {v2.1: 44, v2.2: 21}"
  - "отбор «до Фазы 15» по номеру фазы в модуле теста и в reconcile_lines прибора"
  - "реестр запретов засеян 13 строками планов 16-01…16-06; шапка несёт летопись О-2"
affects: [16-02, 16-03, 16-04, 16-05, 16-06, закрытие-вехи-v2.2]

actuals:
  tokens: 10036
  tasks: 3
  commits: 3
plan_head_before: 1a0c1bb5e17a77e9b41b22f3d2d985d70b019f6d
plan_head_after: e6a83f2e4f2cb383ea476ca3291e22a300b707cb

tech-stack:
  added: []
  patterns:
    - "Чистая функция состояния (str-константа, не совпадающая с вердиктом) + ветвление на pytest.skip/pytest.fail в правиле; мета-гейт вердиктов не задет"
    - "Объявленное число — карта по вехе записи с летописью прежнего значения"
    - "Субъект контроля-отрицания выводится из поданной записи, а не литералом"

key-files:
  created: []
  modified:
    - tests/test_planning/test_deferred_items_are_idempotent.py
    - tests/test_planning/test_requirement_completion_follows_verification.py
    - tests/test_planning/test_state_progress_matches_roadmap.py
    - tests/test_planning/test_plan_prohibitions_census.py
    - scripts/prohibitions_census.py
    - .planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "Различитель законной пустоты в каждом из трёх семейств — признак, обязанный присутствовать при вакууме: кандидат deferred-items.md под phases/; строка Complete; отметки плана в ROADMAP"
  - "Отбор «до Фазы 15» — по номеру фазы < 15 (как through_fixed_set), числа 142/650/745 не менялись"
  - "Реестр v2.2 сеется в существующий файл архива v2.1 штатным --seed-registry (О-2); летопись — в константе REGISTRY_HEADER, потому что засев переписывает шапку из неё"

patterns-established:
  - "Развилка старта вехи: skip только в названном состоянии законной пустоты с причиной; вакуум — fail прежним текстом; каждое состояние доказано на tmp_path/литералах"

requirements-completed: ["записи-старт-вехи"]

coverage:
  - id: D1
    description: "Два правила отложенного: пропуск с причиной при отсутствии живого кандидата, отказ с именем файла при неопознанном кандидате, проверка архива пропуском не снимается"
    requirement: "записи-старт-вехи"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_deferred_items_are_idempotent.py#test_control_an_unrecognised_live_candidate_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_deferred_items_are_idempotent.py#test_control_a_recognised_live_candidate_is_live"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_deferred_items_are_idempotent.py#test_control_an_archive_only_tree_has_no_live_candidates"
        status: pass
    human_judgment: false
  - id: D2
    description: "Счёт строк записи требований по вехе (44 v2.1 сохранено, 21 v2.2), незнакомая веха называется"
    requirement: "записи-старт-вехи"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_a_record_of_an_undeclared_milestone_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_the_archived_v2_1_record_still_meets_its_number"
        status: pass
    human_judgment: false
  - id: D3
    description: "Вывод вехи: пропуск только без отчётов и без Complete; Complete без отчётов — вакуум"
    requirement: "записи-старт-вехи"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_a_completed_row_without_reports_is_the_vacuum"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_a_record_without_completions_or_reports_is_milestone_start"
        status: pass
    human_judgment: false
  - id: D4
    description: "Контроли-отрицания согласия флажка и клетки на выведенных субъектах, с антивакуумом"
    requirement: "записи-старт-вехи"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_negative_a_disagreeing_flag_reddens_the_agreement_rule"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_negative_the_three_kinds_of_disagreement_are_named_apart"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_requirement_completion_follows_verification.py#test_control_the_subjects_refuse_a_record_with_fewer_than_two"
        status: pass
    human_judgment: false
  - id: D5
    description: "Проза роадмапа: пропуск без отметок, вакуум при отметках без опознанной прозы, сличение после волны судит отметки"
    requirement: "записи-старт-вехи"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_state_progress_matches_roadmap.py#test_control_a_roadmap_of_only_tbd_sections_has_no_marks"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_state_progress_matches_roadmap.py#test_control_marks_with_english_prose_are_the_vacuum"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_state_progress_matches_roadmap.py#test_control_marks_with_recognised_prose_are_ready_and_judged"
        status: pass
    human_judgment: false
  - id: D6
    description: "Отбор «до Фазы 15» по номеру фазы и засев реестра строками фазы 16; каталог tests/test_planning без failed"
    requirement: "записи-старт-вехи"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_plan_after_phase_15_stays_out_of_the_before_set"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check (exit 0, биекция — согласие)"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_planning -q -p no:randomly (217 passed, 3 skipped, 0 failed)"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-08
status: complete
---

# Phase 16 Plan 01: Суита записей учится старту вехи Summary

**Суита записей `tests/test_planning` отличает законную пустоту старта вехи v2.2 от вакуума (три чистые функции состояния с синтетическими контролями), счёт строк требований стал картой по вехе, отбор «до Фазы 15» идёт по номеру фазы, а реестр запретов засеян 13 строками планов фазы 16 с летописью О-2 в шапке: `15 failed, 193 passed` → `217 passed, 3 skipped, 0 failed`.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-10-08T16:11:52Z
- **Completed:** 2026-10-08T16:22:13Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- `live_deferred_state` / `_live_deferred_or_skip`: пропуск только когда под `.planning/phases/` нет ни одного кандидата `deferred-items.md`; кандидат без раздела плана — отказ с путём. Проверка всех файлов дерева (архив включительно) идёт до живой половины, поэтому пропуск её не снимает.
- `REQUIREMENT_ROWS_DECLARED = {"v2.1": 44, "v2.2": 21}` с летописью (44 отнесено к v2.1, коммит `d46514cd`); `requirement_rows_offence` называет необъявленную веху.
- `milestone_reports_state`: пропуск правила вывода вехи только без отчётов и без строки `Complete`; `Complete` без отчётов — прежний отказ.
- `_control_subjects`: субъекты двух контролей-отрицаний выводятся из записи (сейчас `PHONE-01`, `PHONE-02`); прежние `FORM-01`/`QUAL-04` названы летописью.
- `prose_rule_state`: пропуск только без отметок плана нигде; отметки без опознанной прозы — красное. Форма после волны (4 из 6 отмечены) проверена на литерале: правило судит её, а не пропускает.
- `_before_phase_15` и `reconcile_lines`: отбор `_phase_number_of(path) < 15`. Контроль: план фазы 17 в это множество не входит, а прежний отбор его бы взял.
- Реестр: `--check` до засева — 754 запрета, 13 сирот (`16-01#0..2`, `16-02#0..1`, `16-03#0..1`, `16-04#0..1`, `16-05#0..1`, `16-06#0..1`). После засева `rows_declared: 741 → 754`, строки `unclassified`/`unresolved` без полей решения, блоки `class_decisions`/`row_decisions` перенесены как есть. Повторный засев: «реестр не изменился». `--check` — exit 0.

## Task Commits

1. **Задача 1 (tracer): правила отложенного** — `f31ccf79` (test). Шлюз tracer: интерактивный режим, `end-of-phase`, в verify только automated. Verify перезапущен, зелёный, после чего работа пошла дальше.
2. **Задача 2: веха записи и проза роадмапа** — `2899fcd8` (test)
3. **Задача 3: отбор по номеру фазы, засев реестра, летопись шапки** — `e6a83f2e` (chore)

## Files Created/Modified

- `tests/test_planning/test_deferred_items_are_idempotent.py` — три состояния, `_live_deferred_or_skip`, `unrecognised_report`, три контроля
- `tests/test_planning/test_requirement_completion_follows_verification.py` — карта числа строк, `requirement_rows_offence`, `milestone_reports_state`, `_control_subjects`, пять новых контролей
- `tests/test_planning/test_state_progress_matches_roadmap.py` — `prose_rule_state`, три контроля
- `tests/test_planning/test_plan_prohibitions_census.py` — `_before_phase_15` по номеру фазы, контроль плана фазы 17
- `scripts/prohibitions_census.py` — отбор в `reconcile_lines` по номеру фазы; абзац летописи О-2 в `REGISTRY_HEADER`
- `.planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — 13 строк фазы 16, `measured: '2026-10-08'`, `rows_declared: 754`, шапка из константы

## Decisions Made

- Значения констант состояний — русские фразы, не совпадающие с `passed`/`gaps_found`/`human_needed`. Мета-гейт вердиктов зелёный (3 passed).
- В контроле архивной записи v2.1 добавлена вторая половина: та же запись без одной строки краснит правило. Она показывает, что число действительно сторожится, а не только сходится.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающий контроль] Антивакуум `_control_subjects` показан на синтетике**
- **Found during:** Задача 2
- **Issue:** план требует антивакуума «субъектов не меньше двух», но контроля, который показал бы его отказ, в плане нет.
- **Fix:** добавлен `test_control_the_subjects_refuse_a_record_with_fewer_than_two`: литеральная запись с одним годным субъектом даёт отказ «найдено 1».
- **Files modified:** tests/test_planning/test_requirement_completion_follows_verification.py
- **Committed in:** `2899fcd8`

**2. [Rule 2 — выразимость контроля] Текст отказа вынесен в чистую функцию `unrecognised_report`**
- **Found during:** Задача 1
- **Issue:** критерий «путь назван» нельзя проверить на `tmp_path`, пока текст строится только внутри помощника, читающего живой корень.
- **Fix:** `unrecognised_report(candidates, base)` строит текст, а `_live_deferred_or_skip` его вызывает. Контроль проверяет, что путь назван. Вдобавок одноразовой пробой в scratchpad (вне репозитория) показано, что `_live_deferred_or_skip` с подменённым корнем даёт fail на неопознанном кандидате, skip на пустом наборе и возвращает живой файл.
- **Committed in:** `f31ccf79`

---

**Total deviations:** 2 auto-fixed (оба по Rule 2, ради выразимости и зубов контролей)
**Impact on plan:** правила не ослаблены. Добавлены только контроли и чистые функции, сфера плана прежняя.

## Issues Encountered

- В первой правке докстринга правила вывода вехи абзац летописи оказался вне строки, и сбор упал с `SyntaxError`. Исправлено до коммита, в коммит ошибка не попала.

## Substitutions (orchestrator notes)

- `graphify update .` в worktree НЕ запускался: `graphify-out/` здесь gitignored. Граф обновляет оркестратор в основном checkout после слияния.
- Полная суита (`just test`, около 40 мин) не запускалась, это пост-мердж гейт оркестратора. Запущено вместо неё: весь `tests/test_planning` (217 passed, 3 skipped, 0 failed), сквозные гейты `test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py` (576 passed, совпадает с замером планирования) и `compileall` (exit 0). Каждый pytest шёл под общим `flock`.

## Post-wave shape (обосновано на синтетике)

- Если у фазы 16 появится `deferred-items.md` с разделом плана и якорем, оба правила отложенного перестанут пропускаться и начнут его судить (контроль `…_recognised_live_candidate_is_live`).
- После волны в ROADMAP Фазы 16 будут отметки и проза «6 планов, из них 4 исполнено». Правило прозы перейдёт в `PROSE_READY` и будет сверять отметки (контроль `…_ready_and_judged`: на согласной прозе 0 расхождений, при одной снятой отметке ровно одно).
- Строк `Complete` нет, `16-VERIFICATION.md` нет, поэтому правило вывода вехи по-прежнему пропускается с причиной. Как только появится строка `Complete` без отчёта, правило покраснеет (контроль `…_completed_row_without_reports_is_the_vacuum`).

## Next Phase Readiness

- Каталог записей зелёный на дереве волны. Если состав `must_haves.prohibitions` любого плана `16-0N` поменяется (например, при закрытии разрывов), засев нужно повторить той же командой.
- Граница, названная планом и здесь не чинившаяся: при архивации вехи v2.2 строки фазы 16 станут лишними строками реестра (класс памяти «Архивация вехи краснит суиту записей»). Это забота закрытия вехи.

## Self-Check: PASSED

- FOUND: все 6 изменённых файлов на диске
- FOUND: коммиты `f31ccf79`, `2899fcd8`, `e6a83f2e` в истории HEAD
- Повторно выполнены приёмочные грепы трёх задач (счёты 1/1/≥1/≥1; 1/1/3/1/≥1/≥1/≥1; 1/1/13/754/≥1/1/≥1), все прошли.

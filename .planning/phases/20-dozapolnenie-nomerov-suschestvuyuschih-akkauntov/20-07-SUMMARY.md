---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 07
subsystem: scripts
tags: [backfill, dry-run, sqlalchemy, exists, phone-privacy, tdd]

requires:
  - phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
    provides: "20-01 core (`run`, `_preview`, `Outcome`, test helpers `_count_writer`, `RecordingSource`, `_snapshot`); 20-06 CLI shell"
provides:
  - "dry-run branch of `run` predicts kept / gone / no-number by reading the row (two `select(exists().where(...))` in a fresh session), writer never called"
  - "pinning rules: dry run writes nothing, summary counts all eight outcomes in enum order, output is masked and free of credentials / exception text"
affects: [phase-20-verification]

actuals:
  tokens: 11000
  tasks: 2
  commits: 3
plan_head_before: 5d7f72f434c604d8092c53a3eee9af776d482a92
plan_head_after: b456d8cc1a461d41a92c03ca5b28f312ffc7e13b

tech-stack:
  added: []
  patterns:
    - "dry-run predicts by reading (`exists`) instead of calling the writer under a rollback"

key-files:
  created: []
  modified:
    - scripts/backfill_account_phones.py
    - tests/test_scripts/test_backfill_account_phones.py

key-decisions:
  - "`_preview` became async and takes `(session_factory, row, reply)`: the prediction needs a fresh session and the account id; the plan said 'a branch in `run`', the tree already had a pure `_preview` helper, so the read lives there and `run` only awaits it"
  - "Task 2 rules were green on the task 1 code, so they went in as one `test(20-07)` commit; no GREEN change was needed"

requirements-completed: [PHONE-18, PHONE-17]

coverage:
  - id: D1
    description: "Dry run predicts 'ручной / уже заполнен', 'удалён во время прогона' and 'номера нет' by reading the row; the writer is never called"
    requirement: PHONE-18
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_dry_run_predicts_kept_and_gone_by_reading"
        status: pass
    human_judgment: false
  - id: D2
    description: "Dry run does not call the writer wrapper and leaves every row unchanged; banner, masked 'было бы заполнено' line and summary header are as specified"
    requirement: PHONE-18
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_dry_run_writes_nothing_and_predicts"
        status: pass
    human_judgment: false
  - id: D3
    description: "Summary prints all eight outcome counters in `list(Outcome)` order and 'Всего: 8'"
    requirement: PHONE-17
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_summary_counts_every_outcome_in_enum_order"
        status: pass
    human_judgment: false
  - id: D4
    description: "Write and dry-run output carry no 7+ digit run, keep a masked filled line, and never print credentials or exception text (class name only)"
    requirement: PHONE-17
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_output_masks_numbers_and_has_a_filled_line"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 07: Dry-run prediction and output guarantees Summary

**Dry run of the phone backfill now predicts kept / gone / no-number outcomes by reading the account row with two `exists` selects (writer never called), and the core's eight-outcome summary and number masking are pinned by tests.**

## Performance

- **Duration:** about 10 min
- **Started:** 2026-11-23T19:44:00Z
- **Completed:** 2026-11-23T19:52:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `scripts/backfill_account_phones.py`: `_preview(session_factory, row, reply)` is now an async read. Unparseable value -> "номера нет"; otherwise a fresh session reads `select(exists().where(id, phone IS NULL, phone_is_manual IS FALSE))` -> "заполнено" (printed "было бы заполнено" with `mask_phone(e164)`), else `select(exists().where(id))` -> "ручной / уже заполнен" or "удалён во время прогона". No write, no writer call, no form that bypasses the Phase 16 write guard.
- Tracer `test_dry_run_predicts_kept_and_gone_by_reading`: a manual number set by a second session during the poll and a row deleted during the poll are predicted correctly, writer wrapper called 0 times.
- Three pinning rules: `test_dry_run_writes_nothing_and_predicts`, `test_summary_counts_every_outcome_in_enum_order`, `test_output_masks_numbers_and_has_a_filled_line` (parametrized write / dry-run).

## Task Commits

1. **Task 1 (tracer) RED** - `0393ca2d` (test)
2. **Task 1 (tracer) GREEN** - `b740ab3d` (feat)
3. **Task 2 pinning rules** - `b456d8cc` (test; rules were green on the task 1 code, no GREEN commit needed)

**Plan metadata:** the docs commit that carries this file.

## TDD

### RED (task 1)

- Target: `tests/test_scripts/test_backfill_account_phones.py::test_dry_run_predicts_kept_and_gone_by_reading`.
- Command: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -k test_dry_run_predicts_kept_and_gone_by_reading -q -p no:randomly --junitxml=.gsd/tdd-evidence/20-07/red-1.xml`; exit 1, `1 failed, 150 deselected`.
- Output: `FAILED tests/test_scripts/test_backfill_account_phones.py::test_dry_run_predicts_kept_and_gone_by_reading`, `AssertionError: просмотр не предсказал ручной номер`.
- `gsd_run check tdd-red-evidence`: `RED_EVIDENCE_OK` (reason `target_test_failed`, format `junit`).
- Semantic assessment: the target executed and failed on the planned assertion (the kept-prediction line was absent because the preview still printed "было бы заполнено"); no import, fixture or collection fault.
- The evidence files live under the self-ignoring `.gsd/tdd-evidence/20-07/` of the worktree and are not committed.

### GREEN (task 1)

`_preview` reads the row; scripts/test_scripts: 151 passed at that point; privacy / parity / single-writer gates: 1161 passed.

### Negative controls (task 2; temporary mutations of the script, reverted with `git checkout -- scripts/backfill_account_phones.py`, never committed)

1. Writer called in preview then session rolled back -> `test_dry_run_writes_nothing_and_predicts` FAILED: `AssertionError: просмотр вызвал писатель Фазы 16`.
2. `e164` printed without `mask_phone` -> `test_output_masks_numbers_and_has_a_filled_line[write]` and `[dry-run]` FAILED: `AssertionError: в выводе номер целиком`.
3. Exception text (`str(exc)`) instead of class name in the note -> the same rule FAILED (both parameters) on `в выводе номер целиком` (the text carries `79991234567`).
4. Summary rendered over three outcomes instead of `for outcome in Outcome` -> `test_summary_counts_every_outcome_in_enum_order` FAILED (summary lines list of 3 != 8 expected).

## Files Created/Modified

- `scripts/backfill_account_phones.py` - async read-based `_preview`, `exists` import, `run` awaits it.
- `tests/test_scripts/test_backfill_account_phones.py` - tracer and three pinning rules (+135 lines).

## Decisions Made

- Prediction lives in `_preview` (already the dry-run seam from 20-01/20-03) rather than inlined into `run`; `run`'s print path is unchanged, so the masked "было бы заполнено" form from 20-01 is preserved.
- KEPT / ACCOUNT_GONE replies carry no `reported`, so the print path takes the generic `#<id> <kind>: <outcome>` form and no number reaches output.

## Deviations from Plan

The plan text predates the merged tree on one point: it describes the prediction as a branch inside `run`, but `run` already delegated dry-run to a pure `_preview(reply)` helper (20-01, extended in 20-03 to carry `note`). Its signature changed to `async _preview(session_factory, row, reply)`; the only caller is `run`. No test called `_preview` directly. Behavior matches the plan exactly.

**Total deviations:** 1 (structural placement, no behavior change). **Impact:** none.

## Gate results

- `tests/test_scripts/test_backfill_account_phones.py`: 155 passed.
- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py`: 1161 passed, no new exemptions; `git diff --stat` on the gate files is empty.
- `tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_services/test_log_masking.py -k "phone or without_setup_logging"`: 33 passed; `tests/test_services/test_log_masking.py` whole file: 106 passed.
- `tests/test_scripts/ tests/test_wa_worker_deployment.py tests/test_max_worker_deployment.py`: 186 passed.
- `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_schedule_invariants.py tests/test_application/test_declared_invariants.py tests/test_application/test_phone_writer_runtime_guard.py`: 189 passed.
- `uv run python -m compileall -q scripts tests/test_scripts`: exit 0.
- `grep -c "\.cte(\|add_cte\|exec_driver_sql\|INSERT OR REPLACE\|prefix_with" scripts/backfill_account_phones.py`: 0; `exists().where`: 2; `for outcome in Outcome`: 1.
- `just --dry-run backfill-phones --dry-run` and `just --dry-run prod-backfill-phones --dry-run` print their commands.
- Not run here by design: the whole `tests/` suite and `just test` (orchestrator gate), `graphify update .` (orchestrator, main checkout), `tests/test_planning` (run after the metadata commit, see return note).

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. The prediction adds two read-only `exists` selects; no new endpoint, auth path or write form (T-20-05 mitigated by the writer-call journal, snapshot equality and the tracer).

## Next Phase Readiness

Wave 7 of 7 done; phase 20 is ready for the end-of-phase gates (TDD review, verification, full suite). PHONE-17..PHONE-20 stay `Pending` in REQUIREMENTS.md for the verifier, as instructed.

## Self-Check: PASSED

- `scripts/backfill_account_phones.py` and `tests/test_scripts/test_backfill_account_phones.py` exist; commits `0393ca2d`, `b740ab3d`, `b456d8cc` are ancestors of HEAD.

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

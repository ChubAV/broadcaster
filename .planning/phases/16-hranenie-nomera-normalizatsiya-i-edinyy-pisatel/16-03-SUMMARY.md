---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 03
subsystem: database
tags: [alembic, sqlalchemy, sqlite, postgresql, check-constraint, messenger-accounts, phone, tdd]

requires:
  - phase: 08 (v2.1 records)
    provides: "revision 0022 — canon of CHECK + dialect branches + explicit copy_from; test_model_matches_head.py snapshot at 0019"
provides:
  - "alembic revision 0023 (down_revision 0022, single head): messenger_accounts.phone String(16) NULL, phone_is_manual Boolean NOT NULL server_default false, CHECK ck_messenger_accounts_manual_requires_phone"
  - "MessengerAccount.phone / phone_is_manual; constants MANUAL_REQUIRES_PHONE, MANUAL_REQUIRES_PHONE_NAME; __table_args__ CheckConstraint"
  - "test_model_matches_head.py: full messenger_accounts snapshot at 0019 + test_every_mapped_messenger_account_column_exists_at_head + negative control naming `phone` (D-04)"
  - "tests/test_migrations/test_0023_messenger_account_phone.py — real upgrade/downgrade on file SQLite"
  - "tests/test_models/test_messenger_account_phone_check.py — model half of the CHECK and column forms"
affects: [16-05 writer, 16-06 single-writer gate, 16-04 privacy gate, phase 17 label, phase 18 form, phase 19 capture, phase 20 backfill]

actuals:
  tokens: 15459
  tasks: 2
  commits: 4
plan_head_before: 1a0c1bb5e17a77e9b41b22f3d2d985d70b019f6d
plan_head_after: a9117ac8456f85c46f48e83c9adf866e31e7ef68

tech-stack:
  added: []
  patterns:
    - "Revision helper `_accounts(*, with_new, with_constraint)` on a private sa.MetaData passed as copy_from both ways (0022 canon extended to added columns)"
    - "`_new_columns()` returns fresh sa.Column objects so the PG and batch branches share one description"
    - "Revision-test snapshot DDL written in Alembic's own SQLite rendering so PRAGMA table_info before upgrade == after downgrade compares the revision, not two spellings"

key-files:
  created:
    - alembic/versions/0023_messenger_account_phone.py
    - tests/test_migrations/test_0023_messenger_account_phone.py
    - tests/test_models/test_messenger_account_phone_check.py
  modified:
    - app/models/messenger_account.py
    - tests/test_migrations/test_model_matches_head.py

key-decisions:
  - "CHECK name ck_messenger_accounts_manual_requires_phone, condition NOT (phone_is_manual AND phone IS NULL) — the 0022 form (Claude's Discretion per plan scope_note)"
  - "Revision touches no data: columns are new, every row is the legal pair (NULL, false), so no cleanup step unlike 0022; MAX credentials untouched (D-01)"
  - "No uniqueness and no index on messenger_accounts at all; revision test asserts PRAGMA index_list is empty (D-02)"
  - "Added a model-side test that the CHECK is named and belongs to MessengerAccount (mirrors test_schedule_active_requires_next_run.py) beyond the six behaviors listed"

patterns-established:
  - "A model column without a revision reddens the suite for messenger_accounts as it already did for payments (D-04)"

requirements-completed: [PHONE-01]

coverage:
  - id: D1
    description: "Revision 0023 adds phone and phone_is_manual; after upgrade every account is unknown (phone NULL, flag 0) including MAX with a number in credentials, credentials unchanged; downgrade restores the exact table"
    requirement: PHONE-01
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0023_messenger_account_phone.py#test_after_the_upgrade_every_account_is_unknown"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0023_messenger_account_phone.py#test_downgrade_restores_the_exact_table"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0023_messenger_account_phone.py#test_the_on_delete_rules_survive_the_recreate"
        status: pass
    human_judgment: false
  - id: D2
    description: "A mapped messenger_accounts column without a revision reddens the suite (D-04), shown by a real RED run before the revision existed"
    requirement: PHONE-01
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_model_matches_head.py#test_every_mapped_messenger_account_column_exists_at_head"
        status: pass
      - kind: unit
        ref: "tests/test_migrations/test_model_matches_head.py#test_control_a_mapped_phone_column_absent_at_head_is_named"
        status: pass
    human_judgment: false
  - id: D3
    description: "Schema refuses phone_is_manual=true with phone NULL on INSERT and both UPDATE sides, accepts the three legal pairs; two accounts share one number; no index"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_models/test_messenger_account_phone_check.py"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0023_messenger_account_phone.py#test_the_check_refuses_a_manual_flag_without_a_number"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0023_messenger_account_phone.py#test_two_accounts_with_one_number_coexist_and_no_index_exists"
        status: pass
    human_judgment: false
  - id: D4
    description: "PostgreSQL branch of 0023 (op.add_column with DEFAULT false, op.create_check_constraint without table recreate)"
    requirement: PHONE-01
    verification: []
    human_judgment: true
    rationale: "No test PostgreSQL in the environment and production containers on the host (A1); the branch is checked by the owner's deploy gate D-26 / R-08-06 together with the 0020..0023 queue, as for 0022"

duration: 15min
completed: 2026-10-08
status: complete
---

# Phase 16 Plan 03: Account phone storage (revision 0023) Summary

**Hand-written revision 0023 adds `messenger_accounts.phone` (String(16), NULL = unknown) and `phone_is_manual` (Boolean NOT NULL, DB default false) with the named CHECK `ck_messenger_accounts_manual_requires_phone`. The model mirrors the condition word for word, and a model column without a revision now reddens `test_model_matches_head.py`.**

## Performance

- **Duration:** about 15 min
- **Started:** 2026-10-08T16:13:01Z
- **Completed:** 2026-10-08T16:27:33Z
- **Tasks:** 2 (both TDD; task 1 was a tracer)
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- Revision `0023` behind `0022`, the single head. It is hand-written and imports nothing from `app.*`.
  - On PostgreSQL it runs two `op.add_column` calls and `op.create_check_constraint`.
  - On SQLite it uses `batch_alter_table` with an explicit `copy_from=_accounts(with_new, with_constraint)`, so `user_id ON DELETE CASCADE` and the rules of the child tables (`groups` CASCADE, `schedules` SET NULL) survive both directions.
- After `upgrade head` every existing account has `phone IS NULL` and `phone_is_manual = 0`. This includes MAX, whose number stays only in `credentials`. The revision moves, fills and guesses no data (D-01).
- The schema now rejects the state "manual flag set, number missing": on INSERT, on raising the flag without a number, and on erasing the number while the flag is set. The three legal pairs are accepted. There is no uniqueness on the number and no index at all (D-02, D-03).
- `test_model_matches_head.py` now snapshots the full `messenger_accounts` table at `0019`, with a chronicle entry in the header. It checks every mapped account column against the head and has a negative control that names `phone`. The D-04 property ("a model column without a revision fails the suite") was demonstrated by a real RED run, not just asserted.

## Task Commits

1. **Task 1: Columns from revision 0023 to the model; a model column without a revision fails the suite (tracer)**
   - RED `da4e3fcd`: `test(16-03)`, snapshot + two checks + model columns, no revision yet
   - GREEN `90e97cf6`: `feat(16-03)`, revision 0023 columns
2. **Task 2: "Manual without a number" impossible in schema and model; full revision test**
   - RED `bdf60e20`: `test(16-03)`, model CHECK module + revision test module
   - GREEN `a9117ac8`: `feat(16-03)`, constants, `__table_args__`, revision CHECK in both branches

The SUMMARY commit follows separately (`docs(16-03)`).

## TDD Gate Compliance

| Cycle | RED | GREEN | REFACTOR |
|-------|-----|-------|----------|
| Task 1 (tracer) | `da4e3fcd` test(16-03) | `90e97cf6` feat(16-03) | not needed |
| Task 2 | `bdf60e20` test(16-03) | `a9117ac8` feat(16-03) | not needed |

**RED evidence, task 1.**
- Command: `uv run pytest tests/test_migrations/test_model_matches_head.py -q -p no:randomly` (with `--junit-xml`, run under the shared lock).
- Exit code 1. The run output contained all three required matches:
  - `FAILED tests/test_migrations/test_model_matches_head.py::test_every_mapped_messenger_account_column_exists_at_head`
  - `1 failed, 4 passed`
  - the expected literal: `AssertionError: отображены моделью, но не заведены ни одной ревизией до головы: ['phone', 'phone_is_manual']`
- `check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`).
- Semantic assessment: the fixture's real `upgrade head` reached `0022` cleanly, as the log shows. The target failed on its own assertion, for the planned reason: the model maps the columns and no revision creates them. It was not a setup, collection or import failure.

**RED evidence, task 2.**
- Command: `uv run pytest tests/test_models/test_messenger_account_phone_check.py::test_a_manual_flag_without_a_number_is_refused_on_insert -q -p no:randomly` (with `--junit-xml`).
- Exit code 1. The run output contained all three required matches:
  - `FAILED tests/test_models/test_messenger_account_phone_check.py::test_a_manual_flag_without_a_number_is_refused_on_insert`
  - `1 failed`
  - the expected literal: `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>`
- `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- Semantic assessment: the insert succeeded because the CHECK did not exist yet, which is exactly the planned assertion.
- In the same RED state, the whole two-module run showed exactly the six constraint-dependent tests red (`6 failed, 17 passed`). The tests that do not depend on the constraint (unknown by default, shared number, column forms, exact-table downgrade, ON DELETE rules) were already green.

How the evidence was recorded: the junit-xml was converted to node:test TAP by a throwaway scratchpad script (not committed). The record files were kept under the gitignored `.pytest_cache/red-evidence/`, because the verb refuses paths outside the project.

## Files Created/Modified

- `alembic/versions/0023_messenger_account_phone.py`: the revision.
  - Long header covering why it exists, why the CHECK is in the schema, why no data is touched, why `copy_from` is used, the untested PG branch, and that rollout happens only together with the `0020…0023` queue.
  - Constants `TABLE`, `CONSTRAINT_NAME`, `CONDITION`; helpers `_new_columns()` and `_accounts(*, with_new, with_constraint)`.
- `app/models/messenger_account.py`: `phone`, `phone_is_manual`, `MANUAL_REQUIRES_PHONE`, `MANUAL_REQUIRES_PHONE_NAME`, `__table_args__`.
- `tests/test_migrations/test_model_matches_head.py`:
  - two chronicle lines naming plan 16-03 (the original paragraphs are kept verbatim);
  - full `messenger_accounts` snapshot;
  - the account-column check and its negative control.
- `tests/test_migrations/test_0023_messenger_account_phone.py`: 14 tests (16 with parametrization) on real `upgrade 0023` / `downgrade 0022`, with an explicit `DATABASE_URL`.
- `tests/test_models/test_messenger_account_phone_check.py`: 9 tests (11 with parametrization) on the model half.

## Decisions Made

- Constraint name and condition follow the plan's scope_note (the `0022` form).
- The two new columns are described once in `_new_columns()`, shared by the PG and batch branches. Each call returns fresh `Column` objects, so no column ends up attached to two tables.
- The revision test's snapshot of `messenger_accounts` is written in Alembic's own SQLite rendering (`DEFAULT (CURRENT_TIMESTAMP)`, `PRIMARY KEY (id)`, table-level FK). That way the `PRAGMA table_info` comparison before upgrade and after downgrade measures the revision, not two ways of writing the same DDL.
- One test was added beyond the listed behaviors: `test_the_constraint_is_named_and_belongs_to_the_model`, mirroring the schedule precedent. It guards that `downgrade` can drop the constraint by name.

## Deviations from Plan

None. The plan was executed as written. Two small additions stay inside the plan's scope:
- the `_new_columns()` helper;
- one extra named-constraint test plus `test_the_upgrade_changes_no_existing_value`.

**Total deviations:** 0 auto-fixed.

## Verification Run (final tree, all pytest under the shared host lock)

- Task 1 `<verify>`: `test_model_matches_head.py`, 5 passed. `tests/test_migrations tests/test_models`, 170 passed.
- Tracer feedback gate (interactive, `end-of-phase`, automated-only `<verify>`): the verify re-run was green, so the run continued to task 2 without a checkpoint.
- Task 2 `<verify>`: three modules, 28 passed. `tests/test_migrations tests/test_models tests/test_application/test_account_deletion_schedules.py`, 200 passed.
- Cross-cutting batch (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`): 576 passed, matching the planning measurement.
- Broad `app/` source gates (`test_no_metering_remains`, `test_payment_status_vocabulary`, `test_schedule_invariants`, `test_ops_state`, `test_notices_channel`, `test_declared_invariants`): 130 passed.
- `uv run python -m compileall -q app main.py tests`: exit 0.
- `tests/test_planning`: `15 failed, 193 passed`, the same as the base measurement on 1a0c1bb5.
  - The failing set covers `test_deferred_items_are_idempotent` (2), `test_plan_prohibitions_census` (9) and `test_requirement_completion_follows_verification` (4). Plan 16-01 owns all of them.
  - This plan wrote nothing under `.planning/` except this SUMMARY.
- Acceptance greps for both tasks all pass. In particular, `create_check_constraint` appears exactly 2 times and `monkeypatch.setenv("DATABASE_URL"` exactly 1 time.

**Checks deliberately not run here:**
- `just test` (the full suite, about 40 min): this is the orchestrator's post-merge gate.
- `graphify update .`: the orchestrator runs it in the main checkout after the merge, because `graphify-out/` is gitignored and would be lost with the worktree.
- `tests/test_phone_privacy_gate.py` (plan 16-04): it only exists after the wave merge. The changed files contain no log or print calls at all.

## Live-database safety

No command in this plan opened the `.env` `DATABASE_URL`.
- The revision ran only inside tests, on file SQLite under `tmp_path`, with `monkeypatch.setenv("DATABASE_URL", url)`.
- No `just upgrade`, `just migrate`, `alembic upgrade`/`downgrade`/`revision` command was run, and no docker command either.

## Issues Encountered

- The first RED record was rejected as `INVALID_RED (invalid_record)`: the multi-line assertion message broke the TAP YAML block. Fixed by flattening the message to one line in the throwaway converter, then re-validated. Nothing in the repository changed.

## User Setup Required

None.

## Next Phase Readiness

- Plan 16-05 (the writer) can now use `phone` and `phone_is_manual` and must clear both columns in one statement. The CHECK enforces this, and the test proves it.
- Plan 16-06 (the single-writer gate) will see the model and revision declarations. Neither assigns a value.
- The PostgreSQL branch is still unverified (A1) and goes through the owner's deploy gate together with the `0020…0023` queue.

## Self-Check: PASSED

- FOUND: alembic/versions/0023_messenger_account_phone.py
- FOUND: tests/test_migrations/test_0023_messenger_account_phone.py
- FOUND: tests/test_models/test_messenger_account_phone_check.py
- FOUND: da4e3fcd, 90e97cf6, bdf60e20, a9117ac8 (all ancestors of HEAD)

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-08*

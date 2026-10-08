---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 05
subsystem: application
tags: [sqlalchemy, conditional-update, compare-and-swap, sqlite, race-test, phone, tdd]

requires:
  - phase: 16-02
    provides: "normalize_reported, normalize_manual, PhoneError, format_phone (app/services/phone.py)"
  - phase: 16-03
    provides: "messenger_accounts.phone / phone_is_manual and CHECK ck_messenger_accounts_manual_requires_phone"
  - phase: 16-04
    provides: "privacy gate PHONE-21 the new module must pass"
provides:
  - "app/application/accounts/phone.py — PhoneWrite (WRITTEN/KEPT/UNPARSEABLE), _fill_if_unknown, fill_reported_phone, record_reported_phone, set_manual_phone"
  - "tests/test_application/test_account_phone_writer.py — 12 sequential rules (14 with parametrization)"
  - "tests/test_application/test_account_phone_race.py — RaceOutcome, run_interleaved, measure_statements, race_violations, read_check_write; 4 rules"
affects: [16-06 single-writer gate, phase 18 manual form, phase 19 capture on connect, phase 20 backfill]

actuals:
  tokens: 7166      # chars/4 over the three files this plan created (28665 chars), same scale as the estimate
  tasks: 2
  commits: 4        # git rev-list --count plan_head_before..plan_head_after
plan_head_before: aecdca46a3319ae5d3676d18d28286eb12127d1d
plan_head_after: 365bf71c32d50bb45d92007f5144b3b35a27f2ec

tech-stack:
  added: []
  patterns:
    - "Automatic source writes with one conditional UPDATE (WHERE phone IS NULL AND NOT phone_is_manual); outcome by rowcount, never read-check-write"
    - "Writer mirrors onto a freshly created ORM object with set_committed_value; no attribute assignment anywhere in the writer"
    - "Race harness: positions from the measured statement count plus a per-position manual_fired flag, so a position beyond the writer is named as vacuum"

key-files:
  created:
    - app/application/accounts/phone.py
    - tests/test_application/test_account_phone_writer.py
    - tests/test_application/test_account_phone_race.py
  modified: []

key-decisions:
  - "set_manual_phone builds the statement with explicit values(phone=..., phone_is_manual=...) keywords in both branches rather than values(**dict), so the 16-06 AST gate sees every write"
  - "Blank detection (None / empty / whitespace-only) happens before normalize_manual: blank means clearing, not PHONE_ERROR_BLANK"
  - "LookupError text carries only the account_id, never the number (PHONE-21)"
  - "Task 2 commits are both test(16-05), as the plan's tdd_notes say: the harness changes no product code"

patterns-established:
  - "Single writer: every write of phone / phone_is_manual goes through app/application/accounts/phone.py"

requirements-completed: [PHONE-02, PHONE-01]

coverage:
  - id: D1
    description: "An automatic number (int 79991234567) fills an unknown account as +79991234567 with the manual flag false and shows as +7 999 123-45-67"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_an_automatic_number_fills_an_unknown_account_and_shows_in_display_form"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sequential rules: manual survives a later automatic write (KEPT); manual replaces an automatic number and raises the flag; automatic never replaces an automatic number; automatic writers never set the manual flag"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_a_manual_number_survives_a_later_automatic_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_a_manual_write_replaces_an_automatic_number_and_raises_the_flag"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_an_automatic_write_never_replaces_an_automatic_number"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_an_automatic_writer_never_marks_the_number_manual"
        status: pass
    human_judgment: false
  - id: D3
    description: "Clearing ('' / spaces / None) returns (NULL, false) in one statement and reopens automatic sources (WRITTEN afterwards)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_clearing_returns_the_unknown_state_and_reopens_automatic_sources (3 rows)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Refusals before the database: garbage gives UNPARSEABLE with zero execute calls; a rejected manual text raises PhoneError with zero execute calls; a missing account raises LookupError"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_an_unparseable_automatic_number_leaves_the_row_untouched"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_a_rejected_manual_text_raises_before_the_database_is_touched"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_setting_a_manual_number_on_a_missing_account_raises"
        status: pass
    human_judgment: false
  - id: D5
    description: "record_reported_phone flushes a new wizard row, writes conditionally, mirrors the number without dirtying the object, and keeps a manual number; writers never commit"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_a_new_account_flushes_and_mirrors_the_number"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_keeps_a_manual_number"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_the_writers_do_not_commit"
        status: pass
    human_judgment: false
  - id: D6
    description: "Race: the production writer keeps the manual number in every measured interleaving position with the manual write proven to have happened; the read-check-write control loses it exactly at position 2; a position beyond the writer is named as vacuum; the stand is one file SQLite with independent sessions"
    requirement: PHONE-02
    verification:
      - kind: integration
        ref: "tests/test_application/test_account_phone_race.py#test_the_production_writer_keeps_the_manual_number_in_every_position"
        status: pass
      - kind: integration
        ref: "tests/test_application/test_account_phone_race.py#test_control_read_check_write_loses_the_manual_number_between_read_and_write"
        status: pass
      - kind: integration
        ref: "tests/test_application/test_account_phone_race.py#test_control_a_position_beyond_the_writer_statements_is_named_as_vacuum"
        status: pass
      - kind: integration
        ref: "tests/test_application/test_account_phone_race.py#test_the_race_runs_on_one_file_database_with_independent_sessions"
        status: pass
    human_judgment: false
  - id: D7
    description: "rowcount of the conditional UPDATE on asyncpg/PostgreSQL (A2): not executed here, no PostgreSQL in the environment"
    requirement: PHONE-02
    verification: []
    human_judgment: true
    rationale: "No test PostgreSQL and the live database must not be touched; the in-repo precedent _claim_payment already relies on rowcount == 1 on asyncpg in production. Verified by the owner's deploy gate together with revision 0023."

duration: 10min
completed: 2026-10-08
status: complete
---

# Phase 16 Plan 05: Single phone writer Summary

**`app/application/accounts/phone.py` is the only place a number reaches `messenger_accounts.phone`. Automatic sources write with one conditional `UPDATE … WHERE phone IS NULL AND NOT phone_is_manual` and read the outcome from `rowcount` (`WRITTEN` / `KEPT` / `UNPARSEABLE`). The manual write always writes and raises the flag, and clearing resets both columns in one statement. A race harness on file SQLite shows the manual number survives in every measured interleaving position, while a read-check-write control loses it exactly between its read and its write.**

## Performance

- **Duration:** about 10 min
- **Started:** 2026-10-08T17:40:33Z
- **Completed:** 2026-10-08T17:50:02Z
- **Tasks:** 2 (both `tdd="true"`; task 1 is a tracer)
- **Files modified:** 3 (all created)

## Accomplishments

- **Writer module** (`PhoneWrite`, `_fill_if_unknown`, `fill_reported_phone`, `record_reported_phone`, `set_manual_phone`). Each takes an `AsyncSession` first and never commits. There is no ORM attribute assignment anywhere; every write is an `UPDATE` with `synchronize_session=False`.
  - `record_reported_phone` flushes a row that has no `id` yet. On `WRITTEN` it mirrors the value onto the object with `set_committed_value`, so the object is not dirty and the commit does not issue a second `UPDATE`.
  - The Russian header explains, in prose: why this is the only writer, why the condition lives in the statement (compare-and-swap, decided by the database the same way on PostgreSQL and SQLite), that the caller owns the transaction and the ownership check, why an object in the same session goes stale, and that the number is never logged or put into an exception.
- **Sequential rules:** 12 rules (14 tests with parametrization) on `db_session`.
  - Every rule reads the final row with a fresh column `select`.
  - The refusals before the database (garbage, rejected manual text) are proven with an `execute` counter that must stay at zero, not just with an unchanged row.
- **Race harness** (D-16):
  - one file SQLite under `tmp_path`, with independent sessions from one factory;
  - `execute` replaced on the automatic source's session, so the code under test is not changed;
  - interleaving positions come from the measured statement count `N`, plus position 0 (after the automatic commit);
  - each position must show `manual_fired is True`.
- **Negative control** (D-08): `read_check_write` goes through the same `run_interleaved` helper as the production writer. It loses the manual number exactly at position 2 and leaves `('+79990000002', True)`, a foreign number under the manual flag.

## Task Commits

1. **Task 1 (tracer): single writer and its sequential rules**
   - RED `bccefc36` `test(16-05): add failing tests for the single phone writer`
   - GREEN `7cf8575f` `feat(16-05): implement the single phone writer with a conditional UPDATE`
2. **Task 2: race harness, every position, negative control**
   - RED `bd9f0033` `test(16-05): add failing race harness for manual vs automatic phone writes`
   - GREEN `365bf71c` `test(16-05): implement race_violations naming lost manual numbers and vacuum positions`

There are no REFACTOR commits; nothing needed cleaning up after GREEN. The SUMMARY commit follows separately (`docs(16-05)`).

## TDD Gate Compliance

| Cycle | RED | GREEN | REFACTOR |
|-------|-----|-------|----------|
| Task 1 (tracer) | `bccefc36` test(16-05) | `7cf8575f` feat(16-05) | not needed |
| Task 2 | `bd9f0033` test(16-05) | `365bf71c` test(16-05), as the plan's tdd_notes require: harness only, no product code | not needed |

**RED, Task 1.** Command: `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly -k test_an_automatic_number_fills_an_unknown_account_and_shows_in_display_form --junit-xml=.pytest_cache/gsd-red/red1.xml`, under the host lock. Exit 1. The output has all three required matches:
- `FAILED tests/test_application/test_account_phone_writer.py::test_an_automatic_number_fills_an_unknown_account_and_shows_in_display_form`
- `1 failed, 13 deselected, 1 warning in 0.32s`
- `E       AssertionError: assert <PhoneWrite.KEPT: 'kept'> is <PhoneWrite.WRITTEN: 'written'>` (causal literal `PhoneWrite.KEPT`)

`check tdd-red-evidence` on the unchanged JUnit record returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`, tests 1, fail 1, `report_errors: []`).
**semanticAssessment:** the target ran. Seeding committed and `fill_reported_phone` was called. The test then failed on its first planned assertion, because the RED stub returns `PhoneWrite.KEPT` without touching the database. There was no collection, import or fixture fault. A whole-file run in the same RED state gave `14 failed` and no ERROR rows; every failure was a behavioral assertion (`KEPT is WRITTEN`, `DID NOT RAISE PhoneError/LookupError`, and wrong row tuples).

**RED, Task 2.** Command: `uv run pytest tests/test_application/test_account_phone_race.py -q -p no:randomly -k test_control_read_check_write_loses_the_manual_number_between_read_and_write --junit-xml=.pytest_cache/gsd-red/red2.xml`, under the host lock. Exit 1. The three required matches:
- `FAILED tests/test_application/test_account_phone_race.py::test_control_read_check_write_loses_the_manual_number_between_read_and_write`
- `1 failed, 3 deselected, 1 warning in 0.29s`
- `E       assert [] == ['позиция 2']` (causal literal «позиция 2»)

`check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`).
**semanticAssessment:** the target ran on the file database. It measured `N == 2` for `read_check_write`, produced outcomes for positions 0, 1 and 2, and passed `manual_fired` at every position. It then failed on the planned assertion, because the stub `race_violations` returns `[]`. A whole-file run in RED gave `2 failed, 2 passed`. The two failures were the rules that depend on `race_violations`. The production-writer rule and the stand rule were already green, because they assert `manual_fired` and the final row directly; the production-writer rule does not lean on the stub.

**GREEN.** Task 1: `14 passed`; with `test_phone.py`, the model CHECK tests and the privacy gate, `193 passed`. Task 2: `4 passed` (`-v` lists all four rules by name); the `-k "race or control or every_position or writer or manual or automatic or concurrency or claim"` selection across the race, writer and payment-concurrency modules gave `25 passed`.

How the evidence was recorded: the records and JUnit XML were written to the worktree's gitignored `.pytest_cache/gsd-red/`, because the verb refuses paths outside the project, and nothing there was committed. The record builder `mkred.py` stayed in the scratchpad. The verb accepted pytest JUnit directly, so no TAP conversion was needed.

## Harness teeth: mutation probe (not committed)

The production `_fill_if_unknown` was temporarily rewritten as read-check-write: a `select`, a Python check, then an unconditional `UPDATE`. The writer and race modules were then run together:
- `1 failed, 17 passed`;
- the only failure was `test_the_production_writer_keeps_the_manual_number_in_every_position`, with `позиция 2: итог ('+79990000002', True), ручной номер затёрт`;
- all 14 sequential rules stayed green, which shows that only the race test can catch this simplification.

The file was then restored with `git checkout -- app/application/accounts/phone.py`, and `git status` confirmed it was unchanged.

## Files Created/Modified

- `app/application/accounts/phone.py`: the single phone writer. It has a Russian header, the `PhoneWrite` enum, and four async functions, with no logging.
- `tests/test_application/test_account_phone_writer.py`: the sequential specification. It has a header stating the reasoning, the `_seed_account` / `_row` / `_count_executes` helpers, and 12 rules.
- `tests/test_application/test_account_phone_race.py`: the race harness. It has a header covering the file DB, the method replacement, measured positions, the vacuum trap and the negative control. It defines `RaceOutcome`, the `sessions` fixture, `run_interleaved`, `measure_statements`, `race_violations` and `read_check_write`, and has 4 rules.

## Decisions Made

- **Explicit `values(...)` keywords in `set_manual_phone`.** Both branches use explicit keywords instead of a `values(**dict)` built elsewhere. The 16-06 AST gate looks for `phone=` / `phone_is_manual=` keywords inside `values(...)`, so a `**dict` would hide the manual write from it. The gate's anti-vacuum rule (it must find a write in this module when no exception applies) is met by `_fill_if_unknown` and by both manual branches.
- **Blank means clearing.** `None`, `""` and whitespace-only text clear the number. This check runs before `normalize_manual`, which would otherwise raise `PHONE_ERROR_BLANK`.
- **`LookupError` names only the `account_id`.**
- **`measure_statements` runs `run_interleaved` with position `-1`.** That position never matches a statement and is not 0, so this is literally the same run without interleaving. It also asserts `manual_fired is False`.
- **Rule 4 checks session identity with a recording factory** passed to `run_interleaved`, and leaves the four planned `RaceOutcome` fields unchanged. It shows three distinct sessions: the automatic one is opened first, and the manual one is a different object.

## Deviations from Plan

None. The plan was executed as written. Two additions stay inside its scope:
- the explicit-keyword form of `set_manual_phone` (see Decisions);
- the uncommitted mutation probe that confirms the harness catches the forbidden simplification.

**Total deviations:** 0 auto-fixed.

## Verification Run (final tree, all pytest under the shared host lock)

- Phase set (`test_phone.py`, writer, race, privacy gate, model CHECK, `tests/test_migrations`): **334 passed**.
- Privacy gate `tests/test_phone_privacy_gate.py`: **64 passed**, green with the new module in `app/`.
- Cross-cutting gates (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`): **576 passed** in 150 s, matching the planning measurement.
- All of `tests/test_application/`: **275 passed**.
- Broad `app/` source gates (`test_no_metering_remains`, `test_payment_status_vocabulary`, `test_schedule_invariants`, `test_ops_state`, `test_notices_channel`, `test_declared_invariants`): **130 passed**.
- `uv run python -m compileall -q app main.py tests`: exit 0.
- `tests/test_planning`, run on the tree with this SUMMARY present: **217 passed, 3 skipped, 0 failed**. Together with the privacy gate's 64 that makes 281 passed / 3 skipped, the orchestrator's base shape.
- Acceptance greps, Task 1: 4 writer defs, 1 `class PhoneWrite(enum.Enum)`, 1 `phone_is_manual.is_(False)`, 3 `synchronize_session=False`, 1 `set_committed_value(account, "phone"`, and 0 commit/assignment forms in the function bodies.
- Acceptance greps, Task 2: 4 harness defs, 1 `class RaceOutcome`, 2 `race.db`, 11 `manual_fired`.

**Checks deliberately not run here:**
- `just test` (the full suite, about 44 min): this is the orchestrator's post-merge gate.
- `graphify update .`: the orchestrator runs it in the main checkout after the merge, because `graphify-out/` is gitignored and absent from the worktree.

## Live-database safety

No command in this plan opened the `.env` `DATABASE_URL`. The writer tests ran on in-memory SQLite (`db_session`), and the race tests ran on a file SQLite under `tmp_path`. No `just upgrade` / `migrate`, alembic or docker command was run.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- 16-06 (the single-writer gate) has a real writer to exempt by name. That writer contains no attribute assignment to `phone` / `phone_is_manual`, and its `values(...)` writes and `set_committed_value` mirror are what the gate's anti-vacuum rule will find.
- Phases 18, 19 and 20 call `set_manual_phone`, `record_reported_phone` and `fill_reported_phone` respectively. Phase 18 must check ownership (`WHERE id AND user_id`) before it calls the writer.
- A2 is still open: `rowcount` on asyncpg was not run here. The risk is reduced by the `_claim_payment` precedent, and it goes through the owner's deploy gate.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-08*

## Self-Check: PASSED

- FOUND: app/application/accounts/phone.py, tests/test_application/test_account_phone_writer.py, tests/test_application/test_account_phone_race.py
- FOUND on branch (aecdca46..HEAD): bccefc36, 7cf8575f, bd9f0033, 365bf71c

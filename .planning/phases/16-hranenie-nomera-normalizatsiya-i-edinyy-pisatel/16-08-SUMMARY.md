---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 08
subsystem: application
tags: [sqlalchemy, conditional-update, exists-probe, phone, single-writer, tdd, gap-closure]

requires:
  - phase: 16-05
    provides: "app/application/accounts/phone.py (PhoneWrite, _fill_if_unknown, fill_reported_phone, record_reported_phone, set_manual_phone) and the race harness run_interleaved / measure_statements"
  - phase: 16-06
    provides: "single-writer gate and privacy gate the changed module must keep green"
provides:
  - "PhoneWrite.MISSING = \"missing\" — automatic write to an absent row is its own outcome, no longer KEPT (WR-05)"
  - "_fill_if_unknown: select(exists()) probe via session.execute ONLY after the single conditional UPDATE touched 0 rows; it classifies KEPT vs MISSING and never precedes the write (D-07)"
  - "ACCOUNT_NOT_IN_SESSION constant; record_reported_phone raises ValueError(ACCOUNT_NOT_IN_SESSION) after flush when the object still has no id, with zero statements issued"
  - "tests/test_application/test_account_phone_writer.py — _record_statements, _add_account helpers; rules test_an_automatic_write_to_a_missing_account_is_named_missing, test_the_existence_probe_runs_only_after_an_update_that_touched_no_row, test_recording_an_account_never_added_to_the_session_raises"
affects: [phase 19 capture on connect (wizard outcome), phase 20 backfill (per-outcome totals), 16-09 single-writer gate widening, 16-10 review disposition]

actuals:
  tokens: 3321      # chars/4 over the realized diff of the two changed files (13283 chars), same scale as the estimate (55000)
  tasks: 2
  commits: 4        # git rev-list --count plan_head_before..plan_head_after, measured before the SUMMARY commit
plan_head_before: 2b9f64bd410a815000fc2cbac595bbbb5f53721b
plan_head_after: bee23ee2c41fd0dbaf87b66f7926f7f1bcae171a

tech-stack:
  added: []
  patterns:
    - "Classify a zero-row conditional UPDATE with a post-write select(exists()) probe; the probe never gates the write"
    - "Statement-order rule: a recording wrapper over session.execute asserts [Update] on the write path and [Update, Select] on the zero paths"
    - "Caller errors (object never added to the session) raise a closed-text ValueError before any statement instead of returning an outcome"

key-files:
  created: []
  modified:
    - app/application/accounts/phone.py
    - tests/test_application/test_account_phone_writer.py

key-decisions:
  - "Missing row on the automatic path is a fourth outcome PhoneWrite.MISSING, not an exception: the Phase 19 wizard and the Phase 20 script total by outcome; set_manual_phone keeps LookupError (one row from the Phase 18 form). The asymmetry is named in the module header"
  - "The existence probe runs through session.execute, not session.scalar, so the race harness and the writer test counters see it"
  - "ACCOUNT_NOT_IN_SESSION was added in the Task 2 RED commit without logic (like PhoneWrite.MISSING in Task 1), so RED failed on DID NOT RAISE rather than ImportError"
  - "The refusal check sits after the existing conditional flush (if id is None: flush; if id is None: raise), so the flush keeps its place and an already-persisted object still skips it"

patterns-established:
  - "Absent row is named, never hidden: automatic writers return MISSING, the manual writer raises LookupError"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "An automatic write to a non-existent account id returns PhoneWrite.MISSING (not KEPT); the seeded row stays unknown"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_an_automatic_write_to_a_missing_account_is_named_missing"
        status: pass
    human_judgment: false
  - id: D2
    description: "The existence probe runs only after an UPDATE that touched no row: WRITTEN path issues exactly [Update]; KEPT and MISSING paths issue [Update, Select]"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_the_existence_probe_runs_only_after_an_update_that_touched_no_row"
        status: pass
    human_judgment: false
  - id: D3
    description: "record_reported_phone on an object never added to the session raises ValueError(ACCOUNT_NOT_IN_SESSION) with zero statements; account.id stays None"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_an_account_never_added_to_the_session_raises"
        status: pass
    human_judgment: false
  - id: D4
    description: "Race test and its read-check-write control are unchanged and green: the production writer keeps the manual number in every measured position; the control still reddens position 2"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py (exit 0)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_race.py#test_the_production_writer_keeps_the_manual_number_in_every_position"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_race.py#test_control_read_check_write_loses_the_manual_number_between_read_and_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_race.py#test_control_a_position_beyond_the_writer_statements_is_named_as_vacuum"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-09
status: complete
---

# Phase 16 Plan 08: Distinct MISSING outcome and the loud refusal for an account outside the session (WR-05)

**`_fill_if_unknown` now returns `PhoneWrite.MISSING` for an absent row. It decides this with a `select(exists())` probe, which runs only after the unchanged conditional UPDATE has touched 0 rows. `record_reported_phone` raises `ValueError(ACCOUNT_NOT_IN_SESSION)` before any statement when the object was never added to the session.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-09T14:24:08Z
- **Completed:** 2026-10-09T14:33:19Z
- **Tasks:** 2 (each one full RED/GREEN cycle)
- **Files modified:** 2

## Accomplishments

- Automatic sources no longer report a missing row as `KEPT`. In the Phase 20 backfill totals, a deleted account now has its own outcome instead of counting as "user was first".
- The write path is still a single statement, so the race harness's measured statement count on a fresh seed stays 1. The probe appears only as the second statement on the zero-row paths, and the statement-order rule pins this order.
- If the Phase 19 wizard forgets `session.add`, it now fails loudly. Previously it silently got an outcome from `UPDATE … WHERE id IS NULL`.
- The module header explains the asymmetry. The automatic writer returns `MISSING`; the manual writer raises `LookupError`. Neither one presents an absent row as some other outcome.

## Task Commits

1. **Task 1 (tracer): MISSING outcome and post-write existence probe**
   - RED `4a6a6150` — `test(16-08): add failing rules for the MISSING outcome and probe order (WR-05)`
   - GREEN `67a25113` — `feat(16-08): name an automatic write to a missing account MISSING (WR-05)`
2. **Task 2: refusal for an account never added to the session**
   - RED `cc3744ba` — `test(16-08): add failing rule for an account never added to the session (WR-05)`
   - GREEN `bee23ee2` — `feat(16-08): refuse to record a number on an account never added to the session (WR-05)`

No REFACTOR commits: the GREEN code needed no cleanup.

## TDD Gate Compliance

`git log --grep="^(test|feat|refactor)\(16-08\):"` shows two RED→GREEN pairs, in order (test 4a6a6150 → feat 67a25113; test cc3744ba → feat bee23ee2). No violations.

**RED evidence, Task 1:** `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly -rf -k test_an_automatic_write_to_a_missing_account_is_named_missing --junit-xml=.pytest_cache/gsd-red/16-08-t1.xml`, exit 1. All three conjuncts were present in the output:
- `FAILED tests/test_application/test_account_phone_writer.py::test_an_automatic_write_to_a_missing_account_is_named_missing`
- `1 failed, 15 deselected`
- the causal literal `PhoneWrite.KEPT` (`AssertionError: отсутствующая строка названа PhoneWrite.KEPT (WR-05)`)

`gsd_run check tdd-red-evidence` on the JUnit record returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`, tests 1 / fail 1). Semantic assessment: the target ran and failed on the planned outcome assertion. `PhoneWrite.MISSING` already existed, so the failure is the wrong value, not an `AttributeError`. There was no collection or fixture fault. I removed a first draft's message, which hard-coded the literal `PhoneWrite.KEPT` as static text. Now both occurrences of the literal in the output come from the observed value. The companion order rule failed in the same RED state, as expected, because the KEPT/MISSING paths had one statement and not two.

**RED evidence, Task 2:** `uv run pytest … -k test_recording_an_account_never_added_to_the_session_raises --junit-xml=.pytest_cache/gsd-red/16-08-t2.xml`, exit 1. Conjuncts:
- `FAILED tests/test_application/test_account_phone_writer.py::test_recording_an_account_never_added_to_the_session_raises`
- `1 failed, 16 deselected`
- causal literal `Failed: DID NOT RAISE <class 'ValueError'>`

The classifier returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`). Semantic assessment: the target ran and failed on the planned `pytest.raises(ValueError)`. `ACCOUNT_NOT_IN_SESSION` was importable, so this is not an ImportError. The evidence files live in the gitignored `.pytest_cache/gsd-red/` and are not committed.

## Files Created/Modified

- `app/application/accounts/phone.py` — adds `PhoneWrite.MISSING`, `ACCOUNT_NOT_IN_SESSION`, the zero-row `select(exists())` probe in `_fill_if_unknown`, and the refusal in `record_reported_phone`. Also updates the module header paragraph and the docstrings, including the WR-05 history.
- `tests/test_application/test_account_phone_writer.py` — adds the `_record_statements` and `_add_account` helpers and three rules (3 new tests; the file has 17 tests in total).

## Decisions Made

See `key-decisions` in the frontmatter. In short:
- The automatic path gets a fourth outcome, `MISSING`, while the manual path keeps `LookupError`.
- The probe goes through `session.execute`.
- The Task 2 RED commit carried the constant without logic.
- The refusal check comes right after the existing conditional flush.

## Deviations from Plan

None. The plan was executed as written. One note: the plan's `<tdd_notes>` say only that Task 1's RED carries `PhoneWrite.MISSING` without logic. I applied the same reasoning to Task 2's RED, which carries `ACCOUNT_NOT_IN_SESSION` without logic. Without it the rule's import would fail, and RED would never reach the planned `DID NOT RAISE` literal.

**Total deviations:** 0. **Impact:** none.

## Gates on the final tree (all under the shared pytest lock, no xdist)

| Gate | Result |
|------|--------|
| `tests/test_application/test_account_phone_writer.py` (Task 1 verify) | 16 passed after Task 1; 17 passed final |
| `test_account_phone_race.py test_phone_single_writer_gate.py test_phone_privacy_gate.py` (Task 1 verify) | 99 passed |
| `test_account_phone_writer.py test_account_phone_race.py` (Task 2 verify) | 21 passed |
| `git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py` | exit 0 (race file byte-identical) |
| race `-k "control_read_check_write or every_position or beyond_the_writer"` | 3 passed, exit 0 |
| `-v` listing: `test_setting_a_manual_number_on_a_missing_account_raises` | PASSED (`set_manual_phone` / `LookupError` unchanged) |
| Plan phase set (`test_phone.py`, writer, race, single-writer gate, privacy gate, `test_messenger_account_phone_check.py`, `tests/test_migrations`) | 368 passed |
| `tests/test_application tests/test_phone_privacy_gate.py tests/test_services/test_phone.py` | 478 passed (base 306+64+105 = 475, plus 3 new rules) |
| Cross-cutting: `test_htmx_post_pairs.py test_htmx_gates.py tests/test_templates test_declared_invariants.py` | 576 passed (equals the base) |
| Wide `app/` gates (`test_no_metering_remains`, `test_payment_status_vocabulary`, `test_schedule_invariants`, `test_ops_state`, `test_notices_channel`, `test_declared_invariants`) | 130 passed |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 |
| Acceptance greps | `MISSING = "missing"` 1; `exists()` 1; `WR-05` 3; `phone_is_manual.is_(False)` 1; `synchronize_session=False` 3; `^ACCOUNT_NOT_IN_SESSION` 1; `raise ValueError(ACCOUNT_NOT_IN_SESSION)` 1; commit/ORM assignment in writer bodies 0 |
| `tests/test_planning -q` | run after the SUMMARY commit; the count is reported in the executor's return message (expected 218 passed, 2 skipped) |

**Substitutions, named:**
- The full suite (`just test`, about 4300 tests, about 45 min) was not run, per orchestrator note 4. The orchestrator's post-merge gate runs it on the merged tree.
- `graphify update .` was not run, per orchestrator note 3. The orchestrator runs it after the merge.
- Wave-mates 16-07 and 16-09 are not in this worktree. The orchestrator re-runs every gate over the merged union. That includes 16-09's widened single-writer gate, which this module must pass: it has no attribute assignment or `setattr` of the phone, no phone value in a log or binding, and `ACCOUNT_NOT_IN_SESSION` carries no number.

## Issues Encountered

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- WR-05 is closed in code. 16-10 records the disposition.
- Phases 19 and 20 can now total their results by `PhoneWrite` with four distinct outcomes.

## Self-Check: PASSED

- FOUND: app/application/accounts/phone.py
- FOUND: tests/test_application/test_account_phone_writer.py
- FOUND commits on this branch: 4a6a6150, 67a25113, cc3744ba, bee23ee2

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-09*

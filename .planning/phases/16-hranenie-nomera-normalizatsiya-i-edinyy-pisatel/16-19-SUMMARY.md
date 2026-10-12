---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 19
subsystem: database
tags: [sqlalchemy, asyncsession, phone, single-writer, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-14: membership check runs first in record_reported_phone, before normalization, with no statement and no flush"
provides:
  - "ACCOUNT_NOT_IN_SESSION with neutral text 'аккаунт не принадлежит сессии писателя', no session.add advice (IN-10, O-8)"
  - "ACCOUNT_WITHOUT_ID_AFTER_FLUSH = 'после flush у аккаунта нет id', raised by the second line after flush"
  - "rule test_each_refusal_of_the_recorder_names_its_own_cause"
  - "row 'foreign' (object in an unbound AsyncSession()) with an anti-vacuum check in test_recording_an_account_outside_this_session_raises"
affects: [phase-19-connection-wizard, phase-18-phone-form, phase-20-backfill]

actuals:
  tokens: 3100      # chars/4 over the realized diff e9141128..27cfc105 (12399 chars)
  tasks: 2
  commits: 3        # MEASURED: git rev-list --count e9141128..HEAD at SUMMARY write
plan_head_before: e9141128e929fca8d4ed3ab7cbe75d743d3c068d
plan_head_after: 27cfc1057672eba0faad677c04933d97c8627dd5

tech-stack:
  added: []
  patterns:
    - "Each refusal path of a writer raises its own closed constant; the test compares against the module constant, never a literal"
    - "A foreign session in a test is an unbound AsyncSession(): the membership check reads only inspect(obj).session, so it needs no database"

key-files:
  created: []
  modified:
    - app/application/accounts/phone.py
    - tests/test_application/test_account_phone_writer.py

key-decisions:
  - "ACCOUNT_NOT_IN_SESSION stays the same symbol with neutral text and no advice: the right action depends on where the object came from, and session.add of a foreign-session object fails with InvalidRequestError (IN-10, O-8)"
  - "The second line after flush gets its own constant ACCOUNT_WITHOUT_ID_AFTER_FLUSH: the object there is already in the session, so the membership text was wrong for it"
  - "The 'foreign' row is a guard, not a RED: it already passed before the plan (planner's measurement), so it went in as test(16-19)"

patterns-established:
  - "One refusal cause, one constant: a refusal text names a cause that is true in every case where it is raised"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "ACCOUNT_NOT_IN_SESSION reads 'аккаунт не принадлежит сессии писателя', with no session.add advice and no digits"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_each_refusal_of_the_recorder_names_its_own_cause"
        status: pass
      - kind: other
        ref: "uv run python -c \"from app.application.accounts.phone import ACCOUNT_NOT_IN_SESSION as a, ACCOUNT_WITHOUT_ID_AFTER_FLUSH as b; ...\" -> OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "The second line after flush raises ACCOUNT_WITHOUT_ID_AFTER_FLUSH with zero statements; the account id stays None"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_each_refusal_of_the_recorder_names_its_own_cause"
        status: pass
    human_judgment: false
  - id: D3
    description: "A foreign-session object (unbound AsyncSession) is refused with ACCOUNT_NOT_IN_SESSION: zero statements, row stays (None, False), anti-vacuum on inspect(account).session"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_an_account_outside_this_session_raises[foreign]"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_an_account_outside_this_session_raises[detached]"
        status: pass
    human_judgment: false
  - id: D4
    description: "16-14 mechanics unchanged; race test untouched and green; both phase gates green with the changed module"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py -> exit 0"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_race.py -k 'control_read_check_write or every_position or beyond_the_writer' -> 3 passed"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py -> 119 passed; tests/test_phone_privacy_gate.py -> 94 passed"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-12
status: complete
---

# Phase 16 Plan 19: Recorder Refusal Causes Summary

**`record_reported_phone` now gives each refusal its own cause. Membership failures raise the neutral `ACCOUNT_NOT_IN_SESSION` ("аккаунт не принадлежит сессии писателя"), which no longer carries the `session.add` advice. The post-flush line raises its own `ACCOUNT_WITHOUT_ID_AFTER_FLUSH`. A test now pins the foreign-session case with an unbound `AsyncSession()` (IN-10, owner decision O-8).**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-12T18:22:55Z
- **Completed:** 2026-10-12T18:32:07Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `ACCOUNT_NOT_IN_SESSION` keeps its symbol and now has neutral text. The old advice "добавьте его через session.add" is gone, because for a foreign-session object it fails with `InvalidRequestError`.
- New closed constant `ACCOUNT_WITHOUT_ID_AFTER_FLUSH = "после flush у аккаунта нет id"`. The second line (`if account.id is None:` after `await session.flush()`) now raises it.
- The `record_reported_phone` docstring names both causes and both constants, with an IN-10 chronicle entry in the D-30/D-32 idiom.
- New tracer rule `test_each_refusal_of_the_recorder_names_its_own_cause`. It reaches the second line by replacing `flush` on a pending member with an empty coroutine. It checks the constant, 0 statements and `id is None`.
- `test_recording_an_account_outside_this_session_raises` now has two real rows, `detached` and `foreign`. `foreign` uses an unbound `AsyncSession()` and has an anti-vacuum check `inspect(account).session is other.sync_session`. The false `:memory:` premise is gone from the docstring and recorded as a chronicle entry.
- The mechanics are unchanged. The membership check is still the first line, before `normalize_reported`, with no statement and no flush. The module still holds its 6 raw writes and has no logging or commit.

## Task Commits

1. **Task 1 RED: failing rule for each refusal naming its own cause** - `80347a94` (test)
2. **Task 1 GREEN: neutral membership text + ACCOUNT_WITHOUT_ID_AFTER_FLUSH** - `b2758f43` (feat)
3. **Task 2: foreign-session row guard, docstring premise fixed** - `27cfc105` (test)

**Plan metadata:** recorded in the `docs(16-19)` commit that adds this SUMMARY.

## TDD Gate Compliance

- **RED (`80347a94`):** I ran `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly -k test_each_refusal_of_the_recorder_names_its_own_cause --junit-xml=.pytest_cache/gsd-red/red.xml` with exit 1. The output had all three conjuncts:
  - `FAILED tests/test_application/test_account_phone_writer.py::test_each_refusal_of_the_recorder_names_its_own_cause`
  - `1 failed, 22 deselected, 1 warning in 0.34s`
  - the causal literal `AssertionError: совет session.add неверен для объекта чужой сессии — там он падает InvalidRequestError`

  `gsd-tools check tdd-red-evidence` on the JUnit-XML record returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`, tests 1 / fail 1, `report_errors: []`). The record is in the gitignored `.pytest_cache/gsd-red/` and was not committed.
  **Semantic assessment:** the target test ran and failed on its first planned assertion, the `session.add` advice inside `ACCOUNT_NOT_IN_SESSION`. There was no collection, import or fixture fault. The body after that assertion reads the not-yet-existing constant as a module attribute (`writer_module.ACCOUNT_WITHOUT_ID_AFTER_FLUSH`), so the RED commit still imports cleanly.
- **GREEN (`b2758f43`):** writer file 23 passed. The `-k` selection `names_its_own_cause or never_added_to_the_session or outside_this_session or pending_member` gave 7 passed. Phase quick run: 560 passed.
- **REFACTOR:** none needed.
- **Tracer feedback gate:** this was an interactive run, `human_verify_mode: end-of-phase`, and task 1's verify is `<automated>`-only. I re-ran the verify, it passed, and I continued to task 2 with no checkpoint.

## Files Created/Modified
- `app/application/accounts/phone.py` - neutral `ACCOUNT_NOT_IN_SESSION` text, the new `ACCOUNT_WITHOUT_ID_AFTER_FLUSH`, the second line raising it, and the docstring with both causes and the IN-10 chronicle.
- `tests/test_application/test_account_phone_writer.py` - module import `writer_module` and `inspect`, the new tracer rule, and the `detached`/`foreign` parametrization with the corrected docstring.

## Decisions Made
- The `foreign` row closes the unbound session in `finally` (`await other.close()`), before `monkeypatch.undo()` and the row re-read. The row read on `db_session` therefore runs after the foreign session releases the object.
- The `detached` row also creates (and closes) an unused `AsyncSession()`. This keeps one code path for both rows. An unbound session that is never used opens no connection.

## Gate Results (final tree `27cfc105`, all under the shared pytest lock)

| Gate | Result | Baseline |
|------|--------|----------|
| `tests/test_application/test_account_phone_writer.py` | 24 passed | 22 |
| writer `-k outside_this_session` | 2 passed (`[detached]`, `[foreign]`) | 1 |
| race `-k "control_read_check_write or every_position or beyond_the_writer"` | 3 passed | — |
| `git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py` | exit 0 | — |
| phase quick-run set (7 paths incl. `tests/test_migrations`) | 561 passed | 559 |
| `tests/test_application` | 404 passed | 402 |
| `tests/test_application/test_phone_single_writer_gate.py` | 119 passed | 119 |
| `tests/test_phone_privacy_gate.py` | 94 passed | 94 |
| `tests/test_services/test_phone.py` | 173 passed | 173 |
| cross-cutting (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed | 576 |
| broad `app/` source gates (6 files) | 130 passed | 130 |
| `uv run python -m compileall -q app main.py tests` | exit 0 | — |
| `uv run python scripts/prohibitions_census.py --check` | exit 0 | exit 0 |
| `tests/test_planning -q` | run after the SUMMARY commit; the count is in the executor's return message | 218 passed, 2 skipped |

**Substitutions (named):**
- I did not run the full suite (`just test`, ~45 min) here, per orchestrator note 4. The orchestrator's post-merge gate runs it on the merged wave tree.
- I did not run `graphify update .` in the worktree, per orchestrator note 3. The orchestrator runs it after the merge.

## Deviations from Plan

None. The plan was executed as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 19's connection wizard, the first product caller of `record_reported_phone`, now gets a true cause for each refusal.
- Wave-mate interaction: the module keeps 6 raw writes, 0 logging calls and no phone value in any exception text. The pinned counts of 16-17 (single-writer gate) and 16-18 (privacy gate) should therefore stay where they are on the merged tree. The orchestrator re-runs both gates after the merge.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-12*

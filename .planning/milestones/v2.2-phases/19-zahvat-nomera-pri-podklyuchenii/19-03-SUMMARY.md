---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 03
subsystem: messengers
tags: [max, pymax, worker, status-endpoint, phone-capture, tdd]

requires:
  - phase: 16-account-phone
    provides: phone privacy gates that judge max_worker/main.py (no phone-named value in a log call)
  - phase: 19-zahvat-nomera-pri-podklyuchenii
    provides: "19-01 set the pattern: the number a messenger reports is captured in the connect handler and never logged"
provides:
  - own_phone_of(client) - total extractor of the number from client.me.contact.phone (pymax 2.3.1)
  - SessionState.own_phone - the number MAX reported, held between on_start and /status
  - GET /api/sessions/{id}/status of a live MAX session carries phone (digit string or null); the no-session answer does not
affects: [19-07, 19-08]

actuals:
  tokens: 2700
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "capture is the first operation of on_start, inside try/except, before is_connected (an exception after it would skip ready_event.set() and the group sync)"
    - "log events carry account_id and error_type only; the exception text is never logged"

key-files:
  created: []
  modified:
    - max_worker/main.py
    - tests/test_worker/test_max_worker.py

key-decisions:
  - "own_phone_of is total (a raising me property returns None) and on_start keeps its own try/except as a second guard; the two are pinned by separate failure shapes"
  - "Only a positive int that is not a bool counts as a number; a string is refused because pymax coerces strings itself and a string here would be the form number"
  - "The form number (SessionState.phone, phone.txt) is never served from /status (owner decision OQ1, 2026-11-22)"

requirements-completed: [PHONE-14, PHONE-15]

duration: 14min
completed: 2026-11-22
status: complete

plan_head_before: f65ed0f516177d79ffe433df74f7a1823fcb6b21
plan_head_after: 0be63e7a1e908b1123e610faeda230975d31716e
commits: 3

coverage:
  - id: D1
    description: "A live MAX session reports the number MAX gave (client.me.contact.phone = 79991234567) as \"phone\": \"79991234567\" in /status; response keys are exactly connected, exists, syncState, phone"
    requirement: PHONE-14
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_the_own_number_from_client_me_reaches_the_status_answer"
        status: pass
    human_judgment: false
  - id: D2
    description: "The form number never reaches /status: contact.phone None gives phone null while SessionState.phone stays the form value"
    requirement: PHONE-14
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_the_form_number_never_leaks_into_the_status_answer"
        status: pass
    human_judgment: false
  - id: D3
    description: "Boundary and precision: no me / me None / contact None / phone None / bool / 0 / negative / string give None; a 15-digit integer converts to the exact digit string"
    requirement: PHONE-14
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_own_phone_of_answers_none_at_every_boundary"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_own_phone_of_converts_an_integer_exactly"
        status: pass
    human_judgment: false
  - id: D4
    description: "A failing capture (raising me property, or the extractor itself raising) keeps the connection: is_connected, ready_event, sync_state ready, own_phone None, /status phone null"
    requirement: PHONE-15
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_a_failing_capture_does_not_break_the_connection"
        status: pass
    human_judgment: false
  - id: D5
    description: "The capture writes no number to the worker log; the failure event own_phone_capture_failed carries account_id and error_type only"
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_the_capture_writes_no_number_to_the_log"
        status: pass
      - kind: integration
        ref: "tests/test_phone_privacy_gate.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "The no-session /status answer is unchanged (no phone key)"
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_the_no_session_answer_carries_no_phone_field"
        status: pass
    human_judgment: false
  - id: D7
    description: "Assumption A3 (RESEARCH): the MAX server fills profile.contact.phone for a QR login of WebClient. The worker is correct in both outcomes (number or null); whether the number is actually present needs a live MAX account"
    requirement: PHONE-14
    verification: []
    human_judgment: true
    rationale: "Needs a live MAX account scanning a QR; owned by the owner's walkthrough, plan 19-08 (W-1). Not faked here."
---

# Phase 19 Plan 03: MAX worker reports its own number Summary

**MAX worker now serves the account's own number from pymax `client.me.contact.phone` in `/status`, captured first in `on_start` inside try/except so a failed capture can never stall the connection, with the form number kept out of the answer and the number kept out of the log.**

## Performance

- **Duration:** about 14 min
- **Started:** 2026-11-22T15:50Z (approx., first test run)
- **Completed:** 2026-11-22T16:05Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `own_phone_of(client)` in `max_worker/main.py`: chained `getattr` over `me.contact.phone`, any exception gives `None`, only a positive non-bool `int` is accepted and returned as an exact decimal string.
- `SessionState.own_phone` and the capture as the first statement of `on_start`, before `state.is_connected = True`; failure logs `own_phone_capture_failed account_id=... error_type=...` only.
- `get_session_status` adds `"phone": session.own_phone` to the live-session answer; the no-session answer and the pymax pin (`maxapi-python==2.3.1`) are untouched.
- Seven new test functions (19 collected cases with parametrization: 2 tracer + 17 pinning) in `tests/test_worker/test_max_worker.py`; five negative controls by mutation each reddened exactly the intended rule.

## Task Commits

1. **Task 1 (tracer): `client.me.contact.phone` from `on_start` to `/status`**
   - RED `cddd079e` (`test(19-03)`): tracer + form-number-leak test
   - GREEN `28977e0f` (`feat(19-03)`): `own_phone_of`, `SessionState.own_phone`, capture, `phone` field
2. **Task 2: boundary, precision, resilience, log silence** - `0be63e7a` (`test(19-03)`): pinning tests only (see TDD Gate Compliance)

**Plan metadata:** committed separately (`docs(19-03)`).

## TDD Gate Compliance

- Gate sequence for the plan: RED `cddd079e` precedes GREEN `28977e0f`; no REFACTOR commit (nothing to clean).
- **RED evidence (task 1):** command `uv run pytest tests/test_worker/test_max_worker.py -q -p no:randomly --junit-xml=...`, exit code 1, `2 failed, 44 passed`. Targets: `FAILED tests/test_worker/test_max_worker.py::test_the_own_number_from_client_me_reaches_the_status_answer` and `...::test_the_form_number_never_leaks_into_the_status_answer`. Causal literal in the report: `AssertionError: воркер MAX не отдал номер из client.me в /status`. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (reason `target_test_failed`, format junit, 46 tests, 2 failing). Semantic assessment: the target ran and failed on the planned assertion (the `phone` field was absent), not on import, setup or collection.
- **Tracer gate:** after the GREEN commit the tracer `<verify>` was re-run end to end (worker tests 46 passed; privacy/parity/single-writer/declared-invariants gates 1171 passed; `tests/test_worker` + deployment 103 passed) - "Tracer verified end-to-end - expanding".
- **Task 2 has no RED commit, by design.** The plan says a RED/GREEN pair is needed only "if the rule is red on the task 1 code". All 17 pinning cases were green on the task 1 code because `own_phone_of` was already total and `on_start` already guarded, so a failing commit would have been faked. The substitute for RED is the negative-control mutations below. This is a recorded exception to the per-task RED rule, not an INVALID_RED.
- **Negative controls (mutation of `max_worker/main.py`, reverted with `git checkout -- max_worker/main.py`, never committed):**

| # | Mutation | Reddened |
|---|----------|----------|
| 1 | drop the `bool` refusal | `test_own_phone_of_answers_none_at_every_boundary[bool-true]` |
| 2 | `str(float(value))` instead of `str(value)` | tracer test, `test_own_phone_of_converts_an_integer_exactly[79991234567]` and `[999999999999999]` |
| 3 | capture taken out of the `try` in `on_start` | `test_a_failing_capture_does_not_break_the_connection[capture-raises]`, `test_the_capture_writes_no_number_to_the_log[capture-raises]` |
| 4 | exception text added to the failure log record | `test_the_capture_writes_no_number_to_the_log[capture-raises]` |
| 5 | `"phone": None` added to the no-session answer | `test_the_no_session_answer_carries_no_phone_field` |

Five of five controls failed the intended test; none was committed.

## Files Created/Modified

- `max_worker/main.py` - `own_phone_of`, `SessionState.own_phone`, capture in `on_start`, `phone` in the live `/status` answer.
- `tests/test_worker/test_max_worker.py` - tracer and pinning tests; `ThrowingMeWebClient`; `install_fake_client` gained an optional `client_class` argument.

## Decisions Made

- Kept `own_phone_of` total and `on_start`'s `try/except` as a second line of defence (as the plan specifies); tests exercise each separately so removing either is detected.
- Exception text is never logged (the failure event carries only the exception type): a RuntimeError message could carry the number, and the test puts the number in the message on purpose.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan inconsistency] Failure-event log assertion cannot be reached through a raising `me` property**
- **Found during:** Task 2
- **Issue:** the plan wants `own_phone_of` to swallow every exception (returns `None`) and also wants `test_the_capture_writes_no_number_to_the_log` to find an `own_phone_capture_failed` record on the "throwing `me`" path. A total `own_phone_of` never lets the exception reach `on_start`, so no such record is written on that path; likewise negative control 3 (take the capture out of `on_start`'s `try`) would not redden a test that only breaks `me`.
- **Fix:** two failure shapes in the tests: a raising `me` property (proves `own_phone_of` totality and that the connection survives) and a monkeypatched `own_phone_of` that raises (reaches `on_start`'s guard, where the `own_phone_capture_failed` record and negative controls 3 and 4 live). Production code is exactly as the plan states.
- **Files modified:** `tests/test_worker/test_max_worker.py`
- **Committed in:** `0be63e7a`

**2. [Rule 3 - Blocking] `install_fake_client` helper extended**
- **Found during:** Task 2
- **Issue:** the failure shape needs a `WebClient` subclass with a raising `me` property; the helper hard-coded `FakeWebClient`.
- **Fix:** optional `client_class=FakeWebClient` parameter (existing callers unchanged); no existing test edited.
- **Committed in:** `0be63e7a`

---

**Total deviations:** 2 auto-fixed (1 plan inconsistency in the test shape, 1 test-helper extension). **Impact on plan:** none on production code; both changes strengthen the pinning tests.

## Issues Encountered

None. `tests/test_planning` is left to the orchestrator's post-merge gate per the dispatch notes; STATE.md and ROADMAP.md were not touched; `requirements mark-complete` was not run (PHONE-12..16 stay Pending).

## Assumptions (not verified here)

- **A3 (RESEARCH):** that the MAX server fills `profile.contact.phone` for a QR login of `WebClient`. pymax source does not say; the worker answers correctly either way (number or `null`, the app then falls back to the form number in plan 19-07). The live check is W-1 of plan 19-08.

## Verification run

- `tests/test_worker/test_max_worker.py`: 63 passed.
- `tests/test_worker tests/test_max_worker_deployment.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_declared_invariants.py`: 1291 passed.
- `tests/test_services/test_log_masking.py tests/test_services/test_ops_state.py tests/test_application/test_queue_rows.py` (modules that read `max_worker/`): 148 passed.
- `uv run python -m compileall -q max_worker tests`: exit 0. `graphify update .` deliberately not run (orchestrator hazard note).
- Acceptance greps: `def own_phone_of` 1, `"phone": session.own_phone` 1, `self.own_phone: str | None = None` 1, `"phone": session.phone` 0, `maxapi-python==2.3.1` 1; capture precedes `state.is_connected = True`.

## Known Stubs

None.

## Threat Flags

None. T-19-09, T-19-10 and T-19-11 are mitigated as planned (tests above); the new `phone` field rides an existing endpoint and adds no new trust boundary.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The app side (plan 19-07) can read `phone` from the MAX worker `/status` and fall back to the form number when it is `null`.
- The worker image must be rebuilt to serve the new field; an older image omits it and the app reads it as `null`.
- Plan 19-08 owns the live check of A3.

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

## Self-Check: PASSED

- `max_worker/main.py`, `tests/test_worker/test_max_worker.py` exist; commits `cddd079e`, `28977e0f`, `0be63e7a` are ancestors of HEAD.

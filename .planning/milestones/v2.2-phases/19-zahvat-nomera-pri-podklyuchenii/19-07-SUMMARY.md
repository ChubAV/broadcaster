---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 07
subsystem: messengers
tags: [max, phone-capture, status-poll, fallback, savepoint, tdd]

requires:
  - phase: 19-zahvat-nomera-pri-podklyuchenii
    provides: "19-05: capture_connect_phone(session, account_id, reported, entered) and reported_phone_from_status; 19-06: normalize_manual E.164 form number in account.credentials; 19-03: MAX worker /status field phone"
provides:
  - "MaxMessenger.get_own_phone() - one extra GET /status after connected true, only the error type is logged"
  - "accounts_connect_max_status reads the form number from credentials before it is overwritten and passes it to capture_connect_phone as the fallback"
  - "MAX number captured in the same commit as the syncing transition: reported number first, form number as an automatic (never manual) fallback"
affects: [19-08, 20-backfill]

actuals:
  tokens: 8500
  tasks: 2
  commits: 3

plan_head_before: 1ab32ae61205bc55cd9061ed5130852cb264c600
plan_head_after: 95d9075d31525b7af53f7488175ab8b3969df243

tech-stack:
  added: []
  patterns:
    - "fallback source read from the connecting row before the poller overwrites credentials, handed to the single savepoint helper"
    - "pinning task proven by seven mutation controls instead of a RED commit"

key-files:
  created: []
  modified:
    - app/messengers/max.py
    - app/pages/accounts.py
    - tests/test_pages/test_connect_phone_capture.py
    - tests/test_messengers/test_max.py

key-decisions:
  - "get_own_phone is a second GET of /status (mirror of the WA method), check_connection untouched"
  - "No new helper or writer: the poller only reads credentials and calls the 19-05 helper; the Phase 16 writer stays the only place that writes the phone column"
  - "Owner decision OQ1 (2026-11-22): an old MAX worker image connects with the form number; the literal 'number stays unknown' of roadmap criterion 4 is proven for WA only"

requirements-completed: [PHONE-14, PHONE-15]

coverage:
  - id: D1
    description: "Entered A, scanned B: the account shows B (+7 999 555-44-33), not manual, no manual mark, connected step shows no number, same commit as syncing, sync_max_groups queued"
    requirement: PHONE-14
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_entered_a_scanned_b_shows_b"
        status: pass
    human_judgment: false
  - id: D2
    description: "MAX reports no number (null, empty, 0, false) or an old worker /status without phone: the form number is stored as automatic and shown without the manual mark"
    requirement: PHONE-14
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_max_without_a_reported_number_shows_the_form_number_without_the_manual_mark"
        status: pass
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_an_old_max_worker_status_connects_with_the_form_number"
        status: pass
    human_judgment: false
  - id: D3
    description: "Legacy raw credentials give no fallback, a failing capture still connects the account and leaves no number in the log, a known number is never overwritten, the number is not asked before connected"
    requirement: PHONE-15
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_a_legacy_raw_form_value_gives_no_fallback"
        status: pass
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_a_failing_max_capture_still_connects_the_account"
        status: pass
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_a_known_max_number_survives_both_sources"
        status: pass
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_the_max_number_is_not_asked_before_the_account_connects"
        status: pass
    human_judgment: false
  - id: D4
    description: "MaxMessenger.get_own_phone parses only a usable phone field and logs only the exception type"
    requirement: PHONE-14
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_max.py#test_get_own_phone_reads_only_a_usable_phone_field"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_max.py#test_get_own_phone_logs_only_the_error_type_when_the_transport_fails"
        status: pass
    human_judgment: false
  - id: D5
    description: "A real MAX worker (19-03 image) reports phone in /status and a real MAX account shows the right number end to end"
    requirement: PHONE-14
    verification: []
    human_judgment: true
    rationale: "Tests replace the worker HTTP client; whether the live MAX server exposes contact.phone at QR login is open (RESEARCH A3) and belongs to the owner walkthrough 19-08."

duration: 40min
completed: 2026-11-22
status: complete
---

# Phase 19 Plan 07: MAX number capture at connect Summary

**The MAX connection poll now reads the worker's `/status` `phone` with one extra GET after `connected: true` and, when MAX reports none, falls back to the E.164 number the connect form stored in `credentials`; either number is written by the single Phase 16 writer as an automatic number, in the same commit as `syncing`.**

## Performance

- **Duration:** about 40 min (including the ~27 min full `tests/test_pages` run)
- **Started:** 2026-11-22T19:19:00Z
- **Completed:** 2026-11-22T19:58:00Z
- **Tasks:** 2 (tracer + pinning, both TDD)
- **Files modified:** 4 (0 created, 4 modified)

## Accomplishments

- `MaxMessenger.get_own_phone` (`app/messengers/max.py`): second GET `.../status`, `None` on non-200, non-JSON, missing field (old worker image), junk and transport failure; logs `get_own_phone_failed` with `error_type` only. `check_connection` is unchanged.
- `accounts_connect_max_status` (`app/pages/accounts.py`): `account_id` local, `entered_phone = account.credentials` before the overwrite, `get_own_phone`, `capture_connect_phone(db, account_id, reported_phone, entered_phone)`, then `credentials = session_id`, `syncing`, one commit, then the sync task with `args=[account_id]`. The not-connected branch, the general `except` and `accounts_connect_max_start` are untouched.
- "Entered A, scanned B shows B": form `8 999 123 45 67`, worker reports `79995554433`, the list shows `+7 999 555-44-33` with no manual mark and no trace of A.
- MAX reporting nothing (`null`, `""`, `0`, `false`) or an old `/status` without `phone` leaves the form number as the automatic number (`+7 999 123-45-67`, `phone_is_manual = false`).
- 11 new page cases (7 test functions, two of them parametrized) plus 12 adapter cases; no production change in task 2.

## Task Commits

1. **Task 1 (tracer): entered A, scanned B shows B**
   - RED `b4ad3106` (test)
   - GREEN `84f414d6` (feat)
2. **Task 2: form-number fallback, old worker image (owner OQ1), failing capture, known number, not-asked-before-connect, `get_own_phone` cases** - `95d9075d` (test, pinning; no production change)

Tracer verified end-to-end - expanding (task 1 verify re-run green before task 2).

**Plan metadata:** the docs commit that carries this file.

## TDD Gate Compliance

`test(19-07)` `b4ad3106` precedes `feat(19-07)` `84f414d6`; no `refactor(19-07)` commit (nothing to clean up). Task 2 had no red rule on the task-1 code (the behaviour was delivered by task 1 and plan 19-06), so it is a pinning commit proven by negative controls below.

### RED evidence (task 1)

- Command: `uv run pytest tests/test_pages/test_connect_phone_capture.py -q -p no:randomly --junit-xml=.gsd/tdd-evidence/19-07/red1.xml`, exit code 1, `1 failed, 8 passed`.
- Failing line: `FAILED tests/test_pages/test_connect_phone_capture.py::test_entered_a_scanned_b_shows_b`.
- Causal literal: `AssertionError: опрос подключения MAX не записал номер, сообщённый мессенджером` with `assert None == ('+' + '79995554433')`.
- Classifier: camelCase record `{command, exitCode, targetTest, output}` wrapping the JUnit XML fed to `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK / target_test_failed`.
- `semanticAssessment`: the target executed through the real `MaxMessenger` and the real handler (only worker address, HTTP client and queue module replaced), reached the phone assertion and failed because the poll did not write the reported number; no import, fixture or collection fault.

### Negative controls of the pinning tests (mutation, not committed)

| # | Mutation | Tests that went red |
|---|----------|---------------------|
| 1 | helper receives `entered_phone=None` | four `without_a_reported_number` params, `old_max_worker_status` (5 failed) |
| 2 | poller answers "Ожидание..." when the reported number is `None` | the same five plus `legacy_raw_form_value`, `known_max_number...[no-field]` (7 failed) |
| 3 | poller normalizes `credentials` with the manual normalizer | `test_a_legacy_raw_form_value_gives_no_fallback` |
| 4 | helper `try/except Exception` removed | `test_a_failing_max_capture_still_connects_the_account` (and the WA twin) |
| 5 | form number written with `set_manual_phone` | four `without_a_reported_number` params, old-worker, legacy raw, known-number `no-field` (7 failed) |
| 6 | `get_own_phone()` called before `check_connection()` | `test_the_max_number_is_not_asked_before_the_account_connects`, the tracer |
| 7 | status-200 check removed from `get_own_phone` | `test_get_own_phone_is_none_when_the_worker_answers_with_an_error_status` |

Every mutation reverted with `git checkout -- <file>`; `git status --short` showed only the two test files afterwards.

## Files Created/Modified

- `app/messengers/max.py` - `get_own_phone`, import of `reported_phone_from_status`
- `app/pages/accounts.py` - capture with the form-number fallback in `accounts_connect_max_status`
- `tests/test_pages/test_connect_phone_capture.py` - `max_worker_answers`, tracer, six pinning rules (docstring of the old-image rule names owner decision OQ1)
- `tests/test_messengers/test_max.py` - `get_own_phone` cases mirroring WA

## Decisions Made

- As planned: second GET instead of touching `check_connection`; helper reuse from 19-05; no POST or `302` assertions (the form POST goes to the `START_URL` constant with `HTMX_HEADERS`, status 200), no new routes or notice codes.
- The owner decision OQ1 is carried in the must-have truth and in the docstring of `test_an_old_max_worker_status_connects_with_the_form_number`; the literal "number stays unknown" half of roadmap criterion 4 is proven for WA by `test_an_old_worker_status_connects_the_wa_account_with_an_unknown_number` (19-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Plan text vs tree] connected-step text and merged state**
- **Found during:** Task 1 test authoring
- **Issue:** the plan says the poll answer reads "Подключено"; the tree's `connected` macro renders `MAX подключён!` (same as WA in 19-05). The plan's tree description of `accounts_connect_max_start` predates 19-06 (`MAX_EMPTY_PHONE_ERROR` is gone, `credentials` holds E.164); the tests start the session through the real form so they follow the merged tree.
- **Fix:** tests assert `MAX подключён!`; no production change.
- **Files modified:** `tests/test_pages/test_connect_phone_capture.py`
- **Commit:** `b4ad3106`

**2. [Rule 3 - Plan text vs tree] `MaxMessenger` patched at the class for the not-asked rule**
- **Found during:** Task 2
- **Issue:** rule 6 of the plan says "`get_own_phone` не вызван"; the adapter is the real one, so the rule patches `app.messengers.max.MaxMessenger.get_own_phone` with an `AsyncMock` and asserts `assert_not_awaited`, in addition to the address list (`/status` once, then `/qr`).
- **Commit:** `95d9075d`

**3. [Rule 3 - Acceptance grep] literal count of the status address**
- **Issue:** the criterion `grep -c "accounts/connect/max/status" >= 6` assumes each rule spells the address; the rules share `_max_poll_and_read` and the `MAX_STATUS_URL` constant, so the literal appears twice. The intent (six rules poll the MAX status route) holds: every pinning rule calls the helper, and the six MAX tests (plus the tracer) exercise the route.
- **Fix:** none; recorded instead of duplicating the literal to satisfy the count.

**Total deviations:** 3 (two plan-text versus tree, one grep-literal). **Impact:** none on scope or behaviour.

### Environment notes

- The `gsd-plan-head-before-19-07` sentinel could not be written from the sandboxed worktree shell (git-dir paths are refused by the harness); `plan_head_before` is the dispatch base `1ab32ae6`, and `commits: 3` was measured with `git rev-list --count 1ab32ae6..HEAD` before the docs commit.
- `graphify update .` was not run (orchestrator instruction: graph lives in the main checkout only).
- Heredoc appends to files were refused by the sandbox; test code was added through the Edit tool.

## Issues Encountered

None beyond the deviations. Assumption left for the owner walkthrough (19-08): whether the live MAX server returns `contact.phone` at QR login is unconfirmed (RESEARCH A3); the realistic MAX path is the form number.

## Verification Results

- Task 1 verify: `test_connect_phone_capture.py` + `test_max_connect_transport.py` 19 passed; phone gates (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`, `test_phone_writer_runtime_guard`, `test_account_phone_writer`) 1265 passed; `test_htmx_post_pairs`, `test_htmx_gates`, `test_impersonation_gate`, `test_htmx_validation_sink`, `test_htmx_preserved`, `test_money_perimeter_gate` 234 passed.
- Task 2 verify: `test_connect_phone_capture.py` + `test_max.py` + `test_application/test_connect_phone.py` 62 passed.
- Full catalog `uv run pytest tests/test_pages -q -p no:randomly` (documented exception, 19-VALIDATION.md section Sampling Rate): **2314 passed, 1081 warnings in 1645.74s (0:27:25), exit 0** - no `failed`.
- Third gate run: `tests/test_templates`, the five phone gates, `test_declared_invariants`, `tests/test_messengers`, `tests/test_worker`, `tests/test_routes/test_tg_user_auth.py`, `test_notices_registry.py`: 1993 passed in 174.84s.
- Acceptance greps: `async def get_own_phone` in `max.py` = 1; `capture_connect_phone(db, account_id, reported_phone, entered_phone)` = 1; the `inspect.getsource` ordering one-liner exits 0; `grep -c OQ1` in the capture test >= 1; `grep -c "accounts/connect/max/status"` there is 2, not the >= 6 of the plan: the address is one `MAX_STATUS_URL` constant used by the tracer and by the shared `_max_poll_and_read` helper that every pinning rule goes through (see Deviation 3).
- `compileall -q app tests`: exit 0.

## Known Stubs

None.

## Threat Flags

None - no new route, auth path, file access or schema change. T-19-20 (reported number wins, fallback only on an unparseable report, automatic write; `test_entered_a_scanned_b_shows_b`), T-19-21 (savepoint wrapper, old-image and failing-capture tests), T-19-27 (adapter logs `error_type` only, helper logs `account_id`/`outcome`/`error_type`, privacy gates green, no number in the log in the failing-capture test) are covered.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- PHONE-14 and PHONE-15 (MAX side, app side) are implemented; both stay `Pending` in REQUIREMENTS.md until the phase verdict (not marked here).
- 19-08 owner walkthrough needs a live MAX account to confirm the worker field `phone` and the A-then-B case on the real server.

## Self-Check: PASSED

Created/modified files exist; commits `b4ad3106`, `84f414d6`, `95d9075d` are ancestors of HEAD.

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

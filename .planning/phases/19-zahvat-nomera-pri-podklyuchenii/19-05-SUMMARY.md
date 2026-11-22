---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 05
subsystem: messengers
tags: [whatsapp, phone-capture, savepoint, status-poll, tdd]

requires:
  - phase: 16-account-phone
    provides: fill_reported_phone (single conditional writer of the phone column), PhoneWrite outcomes
  - phase: 19-zahvat-nomera-pri-podklyuchenii
    provides: "19-01: module logger and the account-label wiring in app/pages/accounts.py"
provides:
  - reported_phone_from_status(body) - pure parser of the worker /status phone field
  - WhatsAppMessenger.get_own_phone() - one extra GET /status after connected true
  - capture_connect_phone(session, account_id, reported_phone, entered_phone=None) - savepoint-wrapped capture, reported-then-entered order (reused by 19-07 for MAX)
  - WA connection poll stores the number in the same commit as the syncing transition
affects: [19-02, 19-07, 19-08, 20-backfill]

actuals:
  tokens: 7000
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "capture helper opens only a savepoint and never commits: the handler owns the transaction, a capture failure rolls back the savepoint only"
    - "account_id read into a local before the capture so the attribute read does not depend on object load state after a savepoint rollback"
    - "untrusted worker JSON parsed by a total pure function; the writer normalizes"

key-files:
  created:
    - app/application/accounts/connect_phone.py
    - tests/test_pages/test_connect_phone_capture.py
    - tests/test_application/test_connect_phone.py
  modified:
    - app/messengers/base.py
    - app/messengers/whatsapp.py
    - app/pages/accounts.py
    - tests/test_messengers/test_whatsapp.py

key-decisions:
  - "get_own_phone is a second GET of /status, not a change of check_connection (pinned by check_connection_failed tests); one extra local request per connection, only after connected true"
  - "Helper lives in the application layer (not a page-private function): two pollers call it (WA here, MAX in 19-07) and it is testable alone"
  - "Task 2 is a pinning task: every rule passed on the task-1 code, so no RED commit; each rule was proven by a mutation control instead"

requirements-completed: [PHONE-13, PHONE-15]

duration: 55min
completed: 2026-11-22
status: complete

plan_head_before: f65ed0f516177d79ffe433df74f7a1823fcb6b21
plan_head_after: 8f0af56d2bbe980b3c8bd93e1ec64e9454e82cc6
commits: 3

coverage:
  - id: D1
    description: "A WA connection whose /status carries phone stores the number (+79991234567, not manual) in the same commit as syncing, queues sync_wa_groups, and the accounts list shows +7 999 123-45-67 without the manual mark"
    requirement: PHONE-13
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_a_wa_connection_stores_the_number_the_worker_reported"
        status: pass
    human_judgment: false
  - id: D2
    description: "phone null (LID) or an old worker status without the field connects the account with an unknown number"
    requirement: PHONE-15
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_an_old_worker_status_connects_the_wa_account_with_an_unknown_number"
        status: pass
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_a_lid_only_session_leaves_the_number_unknown"
        status: pass
    human_judgment: false
  - id: D3
    description: "A failing capture does not break the connection and leaves no number in the log"
    requirement: PHONE-15
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_a_failing_capture_still_connects_the_account"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_connect_phone.py#test_a_failing_writer_is_swallowed_and_the_outer_transaction_survives"
        status: pass
    human_judgment: false
  - id: D4
    description: "An empty or different report never overwrites a known number; the entered fallback is tried only after an unparseable reported number"
    requirement: PHONE-15
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_an_empty_or_other_report_never_overwrites_a_known_number"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_connect_phone.py#test_the_number_the_messenger_reported_wins_over_the_entered_one"
        status: pass
    human_judgment: false
  - id: D5
    description: "The number is read by one extra GET and only after connected true"
    requirement: PHONE-13
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_connect_phone_capture.py#test_the_number_is_not_asked_before_the_account_connects"
        status: pass
    human_judgment: false
  - id: D6
    description: "A real WA worker (plan 19-02 image) reports phone in /status and the app picks it up end to end"
    requirement: PHONE-13
    verification: []
    human_judgment: true
    rationale: "Tests replace the worker HTTP client; the live worker field is delivered by 19-02 and checked in the phase UAT (19-08)."
---

# Phase 19 Plan 05: WhatsApp number capture at connect Summary

**The WA connection poll now reads the `phone` field of the worker's `/status` with one extra GET after `connected: true` and writes it through the single Phase 16 writer inside a savepoint, in the same commit as the `syncing` transition; old worker images, LID sessions and a failing capture all still connect the account with an unknown number.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-11-22T15:45:00Z
- **Completed:** 2026-11-22T16:20:00Z
- **Tasks:** 2 (tracer + pinning, both TDD)
- **Files modified:** 7 (3 created, 4 modified)

## Accomplishments

- `reported_phone_from_status` (base.py): dict only; non-empty string returned as is, int > 0 (not bool) returned as a string, everything else `None`.
- `WhatsAppMessenger.get_own_phone` (whatsapp.py): second GET `.../status`, `None` on non-200, non-JSON, missing field, junk and transport failure; logs only `error_type`.
- `capture_connect_phone` (new `app/application/accounts/connect_phone.py`): savepoint, writes the reported number first and the entered fallback only on `UNPARSEABLE`; never commits; log events `connect_phone_captured` (`account_id`, `outcome`) and `connect_phone_capture_failed` (`account_id`, `error_type`).
- `accounts_connect_wa_status`: `account_id` local, `get_own_phone`, `capture_connect_phone`, then credentials, `syncing`, the single commit, then the sync task with `args=[account_id]`.
- 16 new tests across three modules (pages 8 cases, helper 6, adapter 13 parametrized/plain), all through the real `WhatsAppMessenger` with only the worker address, HTTP client and queue module replaced.

## Task Commits

1. **Task 1 (tracer): worker `phone` to the account label**
   - RED `a097ac0c` (test)
   - GREEN `7a86b0bc` (feat)
2. **Task 2: old shape, LID, capture failure, source order** - `8f0af56d` (test, pinning; no production change)

Tracer verified end-to-end - expanding (task 1 verify re-run green before task 2).

## TDD Gate Compliance

`test(19-05)` precedes `feat(19-05)`; no `refactor(19-05)` commit (nothing to clean up). Task 2 had no red rule on the task-1 code (all 43 tests of the three modules were green on first run except one wrong assertion of my own, see Deviations), so it is a pinning commit proven by negative controls below.

### RED evidence (task 1)

JUnit XML from `pytest --junit-xml` fed to `gsd_run check tdd-red-evidence` -> `RED_EVIDENCE_OK`, reason `target_test_failed`. Line `FAILED tests/test_pages/test_connect_phone_capture.py::test_a_wa_connection_stores_the_number_the_worker_reported`, summary `1 failed`, cause literal `опрос подключения WA не записал номер из /status` (`assert None == '+79991234567'`). Semantic assessment: the target executed through the real adapter and handler and failed on the planned phone assertion; no import or fixture fault.

### Negative controls of the pinning tests (mutation, not committed)

| # | Mutation | Tests that went red |
|---|----------|---------------------|
| 1, 2 | handler answers "Ожидание..." when the reported number is `None` | old-shape, LID-only, empty-report `no-field` and `null` (4 failed) |
| 3 | `try/except` removed from the helper | `test_a_failing_capture_still_connects_the_account`, `test_a_failing_writer_is_swallowed_and_the_outer_transaction_survives` |
| 4 | on `KEPT` the helper writes the reported number with `set_manual_phone` | `other-number` case, `test_a_known_number_is_kept_and_the_fallback_is_not_tried` (`('+79991234567', True) == ('+79995554433', False)`) |
| 5 | `get_own_phone()` called before `check_connection()` | `test_the_number_is_not_asked_before_the_account_connects`, the tracer (answer order shifted) |
| 6 | status-200 check removed from `get_own_phone` | `test_get_own_phone_is_none_when_the_worker_answers_with_an_error_status` |
| 7 | fallback tried on every outcome | `test_the_number_the_messenger_reported_wins_over_the_entered_one`, `..._known_number_is_kept...`, `..._missing_account...` |

All mutations reverted with `git checkout -- <file>`; `git diff HEAD -- app` empty afterwards.

## Files Created/Modified

- `app/messengers/base.py` - `reported_phone_from_status`
- `app/messengers/whatsapp.py` - `get_own_phone`
- `app/application/accounts/connect_phone.py` - `capture_connect_phone`
- `app/pages/accounts.py` - wiring in `accounts_connect_wa_status`
- `tests/test_pages/test_connect_phone_capture.py`, `tests/test_application/test_connect_phone.py`, `tests/test_messengers/test_whatsapp.py` - tests

## Decisions Made

- As planned: second GET instead of touching `check_connection`; helper in the application layer; no POST or `302` assertions, no new routes or notice codes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan text vs tree] "Подключено" text and label wording**
- **Found during:** Task 1 and Task 2 test authoring
- **Issue:** the plan says the poll answer reads "Подключено"; the tree's `connected` macro renders `WhatsApp подключён!`. The WA list label for an unknown number renders `Номер неизвестен` without a channel word (plan assumed `WhatsApp Номер неизвестен`; my first assertion failed on it).
- **Fix:** tests assert the real text `WhatsApp подключён!` and `"Номер неизвестен" in label` plus no manual mark. No production change.
- **Files modified:** `tests/test_pages/test_connect_phone_capture.py`
- **Commit:** `a097ac0c`, `8f0af56d`

**2. [Rule 3 - Plan text vs tree] `app/pages/accounts.py` already changed by 19-01**
- Module `logger`, the `record_reported_phone` import and the `tg_phone_captured` event came from 19-01; this plan only added the `capture_connect_phone` import and the branch edit. Nothing in the plan's `app/pages/accounts.py` contract needed to change.

**3. [Rule 3 - Acceptance grep] docstring mentioned `session.begin_nested()`**
- The criterion `grep -c "begin_nested()" connect_phone.py = 1` counted the docstring too (2); reworded the docstring so only the call matches. **Commit:** `7a86b0bc`.

**Total deviations:** 3 (1 plan-text mismatch in assertions, 1 tree-state note, 1 grep-literal). **Impact:** none on behaviour.

### Environment notes

- The `gsd-plan-head-before-19-05` sentinel file in the shared git dir could not be written from the sandboxed worktree shell (the harness refuses git-dir paths); `plan_head_before` is the dispatch base `f65ed0f5`, and `commits: 3` was measured with `git rev-list --count f65ed0f5..HEAD`.
- Plan-level `graphify update .` was not run (orchestrator instruction: graphify-out is main-checkout only).

## Issues Encountered

None beyond the deviations.

## Threat Flags

None - no new route, auth path, file access or schema change. T-19-14 (parser + writer normalization, adapter parametrized test), T-19-15 (savepoint wrapper, failing-capture test), T-19-16 (conditional writer, `KEPT` tests), T-19-17 (log carries only `account_id`/`outcome`/`error_type`, privacy gates green), T-19-18 (handler selection unchanged) are covered.

## Known Stubs

None.

## Gates run

Green: `tests/test_pages/test_connect_phone_capture.py tests/test_application/test_connect_phone.py tests/test_messengers` (full dir), the phone gates (`test_phone_privacy_gate.py`, `test_phone_gates_parity.py`, `test_phone_single_writer_gate.py`, `test_phone_writer_runtime_guard.py`, `test_account_phone_writer.py`), `tests/test_application/test_declared_invariants.py`, `tests/test_routes/test_tg_user_auth.py` (1443 passed together); `tests/test_pages/test_htmx_post_pairs.py test_htmx_gates.py test_impersonation_gate.py test_money_perimeter_gate.py` (201 passed after task 1); `compileall -q app tests` exit 0. The final combined run over `tests/test_templates`, `test_notices_registry.py`, `test_shell.py`, `test_htmx_preserved.py`, `test_telegram_pool.py` and the htmx/impersonation/money gates is reported in the handback message.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- PHONE-13 and PHONE-15 (WA side) are implemented; both stay `Pending` in REQUIREMENTS.md until the phase verdict (not marked here).
- 19-07 can call `capture_connect_phone(db, account_id, reported_phone, entered_phone)` and `reported_phone_from_status` for MAX.
- The live `phone` field of the worker `/status` comes from 19-02; an old image reads as an unknown number.

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

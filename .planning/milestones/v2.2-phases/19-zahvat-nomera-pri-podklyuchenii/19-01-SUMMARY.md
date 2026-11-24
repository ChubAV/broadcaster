---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 01
subsystem: messengers
tags: [telegram, telethon, qr-login, 2fa, phone-capture, tdd]

requires:
  - phase: 16-account-phone
    provides: record_reported_phone (single writer of the phone column), PhoneWrite outcomes
  - phase: 18-account-phone-ui
    provides: account label shows the stored phone, manual mark only for manual numbers
provides:
  - QrAuthResult(session_string, phone) returned by complete_auth
  - reported_phone_of — total extractor of the number from a Telethon User
  - Telegram accounts created by the QR wizard keep the number from the sign-in answer (QR and 2FA paths)
affects: [19-05, 19-07, 19-08, 20-backfill]

actuals:
  tokens: 7800
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "number rides the same synchronous pop as the session string (no await between _owned check and pop)"
    - "log events carry account_id and outcome only; dataclass fields holding a phone use repr=False"

key-files:
  created: []
  modified:
    - app/messengers/telegram_user.py
    - app/pages/accounts.py
    - tests/test_routes/test_tg_user_auth.py
    - tests/test_messengers/test_telegram_user.py

key-decisions:
  - "complete_auth returns QrAuthResult | None instead of adding a second pop-twin function: one place holds the D-02 invariant"
  - "No savepoint on the TG path: reported_phone_of never raises and the writer answers UNPARSEABLE without touching the DB; ACCOUNT_NOT_IN_SESSION stays loud"
  - "Fourth case (property that raises on read) added to the unparseable-phone test so the user.phone negative control actually reddens it"

requirements-completed: [PHONE-12]

duration: 33min
completed: 2026-11-22
status: complete

plan_head_before: 4ca2f7dd8179f85d184a49c0a968d0415bdf82ca
plan_head_after: 49791b601d6b1c898ee045ec6f4e1bed40f7dc71
commits: 5

coverage:
  - id: D1
    description: "QR sign-in: the new Telegram account stores the number from qr_login.wait() (phone +79990001122, phone_is_manual false, status active, one row)"
    requirement: PHONE-12
    verification:
      - kind: e2e
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_qr_scan_gives_the_new_account_its_number_without_a_second_connection"
        status: pass
    human_judgment: false
  - id: D2
    description: "2FA sign-in: the new account stores the number from sign_in(password=...)"
    requirement: PHONE-12
    verification:
      - kind: e2e
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_right_password_gives_the_new_account_its_number"
        status: pass
    human_judgment: false
  - id: D3
    description: "No second connection to Telegram: one client factory call, one connect, get_me never called"
    requirement: PHONE-12
    verification:
      - kind: e2e
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_qr_scan_gives_the_new_account_its_number_without_a_second_connection"
        status: pass
    human_judgment: false
  - id: D4
    description: "Capture is total and private: junk phone still connects the account; log carries only account_id and outcome; repr hides the number"
    requirement: PHONE-12
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_reported_phone_of_takes_only_a_non_empty_string"
        status: pass
      - kind: e2e
        ref: "tests/test_routes/test_tg_user_auth.py#test_an_unparseable_phone_still_connects_the_account"
        status: pass
      - kind: e2e
        ref: "tests/test_routes/test_tg_user_auth.py#test_the_capture_log_carries_no_number"
        status: pass
    human_judgment: false
  - id: D5
    description: "First connection on a live Telegram account yields a User.phone that is a non-empty digit string (assumption A1 of the research)"
    requirement: PHONE-12
    verification: []
    human_judgment: true
    rationale: "Depends on real Telegram behaviour; unit tests use a stub User. Checked by the first live connection after rollout (phase UAT)."
---

# Phase 19 Plan 01: Telegram number capture at connect Summary

**Telegram QR and 2FA sign-ins now hand the `User.phone` from Telethon's own sign-in answer to `record_reported_phone`, so the new account is created `active` with its number in one commit and no second connection.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-11-22T14:28:00Z
- **Completed:** 2026-11-22T15:01:00Z
- **Tasks:** 2 (tracer + auto, both TDD)
- **Files modified:** 4

## Accomplishments

- `QRAuthState.own_phone` (`repr=False`), `QrAuthResult` (frozen, `phone` `repr=False`), `reported_phone_of` (never raises) in `app/messengers/telegram_user.py`; capture in `_wait_for_qr` and `submit_2fa` as the first statement of the synchronous block that also sets `session_string` and `status`.
- `complete_auth` now returns `QrAuthResult | None`; the `_owned` check and `_qr_sessions.pop` still have no `await` between them (verified with `inspect.getsource`), so of two concurrent calls exactly one gets the result.
- `_save_tg_account(db, user, result)` calls `record_reported_phone` after `db.add`, then a single `await db.commit()`; module logger event `tg_phone_captured` carries `account_id` and `outcome` only.
- The "Connected" step shows no number (D-12); the accounts list shows `+7 999 000-11-22` without the "указан вручную" mark.

## Task Commits

1. **Task 1 (tracer): number from the QR sign-in answer to the account label**
   - RED `d7c4eba1` (test)
   - GREEN `b529d7fd` (feat)
2. **Task 2: 2FA path, totality, privacy**
   - RED `a0167c3e` (test)
   - GREEN `08c4c0ef` (feat)
   - Pin strengthening `49791b60` (test) — fourth unparseable case, see Deviations

Tracer verified end-to-end — expanding (task 1 verify re-run green before task 2).

## TDD Gate Compliance

RED/GREEN gate commits present for both tasks (`test(19-01)` precedes each `feat(19-01)`); no `refactor(19-01)` commit — nothing to clean up.

### RED evidence

Both records validated with `gsd_run check tdd-red-evidence` (JUnit XML from `pytest --junit-xml`) -> `RED_EVIDENCE_OK`, reason `target_test_failed`.

- **Task 1:** `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly -k a_qr_scan_gives` — line `FAILED tests/test_routes/test_tg_user_auth.py::test_a_qr_scan_gives_the_new_account_its_number_without_a_second_connection`, summary `1 failed, 56 deselected`, cause literal `аккаунт Telegram сохранён без номера из ответа входа: phone=None`. Semantic assessment: the target executed and failed on the planned phone assertion after the helper extension; no import or fixture fault.
- **Task 2:** `... -k a_right_password_gives_the_new_account` — line `FAILED tests/test_routes/test_tg_user_auth.py::test_a_right_password_gives_the_new_account_its_number`, summary `1 failed, 61 deselected`, cause literal `аккаунт Telegram после пароля 2FA сохранён без номера: phone=None`. Semantic assessment: same. (`test_the_capture_log_carries_no_number` also failed at RED — its outcome stays `unparseable` until the 2FA capture exists — and went green with the same GREEN commit.)

### Negative controls of the pinning tests (mutation, not committed)

| # | Mutation | Test | Result |
|---|----------|------|--------|
| 2 | `reported_phone_of`: `isinstance`/strip check replaced by `if phone:` | `test_reported_phone_of_takes_only_a_non_empty_string` | FAILED: `namespace(phone='   ') дал номер вместо «неизвестен»` |
| 3 | `own_phone` without `repr=False` | `test_the_number_stays_out_of_the_state_and_result_repr` | FAILED: `repr состояния мастера вывел номер` |
| 4 | `complete_auth` returns `QrAuthResult(state.session_string, None)` | `test_complete_auth_hands_over_the_number_from_the_same_pop` | FAILED: `номер не доехал вместе со строкой сессии` |
| 5 | `state.own_phone = user.phone` in place of `reported_phone_of(user)` | `test_an_unparseable_phone_still_connects_the_account` | with the planned three cases: PASSED (writer is total on its own) — control did not redden; added the `unreadable-phone` case, then FAILED: `мусорный номер сорвал подключение` |
| 6 | `phone=result.phone` added to the `tg_phone_captured` log call | `test_the_capture_log_carries_no_number` | FAILED: `ключи события захвата: [..., 'phone', ...]` |

All mutations reverted with `git checkout -- <file>`; none committed (`git diff HEAD` empty on `app/`).

## Files Created/Modified

- `app/messengers/telegram_user.py` — `own_phone`, `QrAuthResult`, `reported_phone_of`, capture in `_wait_for_qr`/`submit_2fa`, new return of `complete_auth`
- `app/pages/accounts.py` — module `logger`, `record_reported_phone` import, `_save_tg_account(db, user, result)`, both call sites pass the result
- `tests/test_routes/test_tg_user_auth.py` — helper extension (`user=`, `created=`, `get_me`), tracer, 2FA test, unparseable (4 cases), capture-log privacy test
- `tests/test_messengers/test_telegram_user.py` — three `complete_auth` return tests moved to `.session_string`; totality, repr, same-pop handover tests

## Decisions Made

- `complete_auth` returns `QrAuthResult | None` (no pop-twin function), as planned.
- No savepoint on the TG path, as planned; the loud `ACCOUNT_NOT_IN_SESSION` is preserved.
- The route-level log test treats `request_id`, `method`, `path` (bound by the request middleware) as service keys next to structlog's own; the meaningful keys remain exactly `account_id` and `outcome`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test gap] Negative control 5 did not redden the planned test**
- **Found during:** Task 2 (negative controls)
- **Issue:** with `user.phone` in place of `reported_phone_of(user)`, the three planned unparseable cases all passed, because the Phase 16 writer is itself total on `None`, `"garbage"` and `MagicMock`; the pin did not guard `reported_phone_of`'s exception safety at route level.
- **Fix:** added a fourth case `unreadable-phone` (a user whose `phone` property raises) to `test_an_unparseable_phone_still_connects_the_account`; the mutation now fails it.
- **Files modified:** `tests/test_routes/test_tg_user_auth.py`
- **Commit:** `49791b60`

**2. [Rule 3 - Blocking] Capture-log test saw request-context keys**
- **Found during:** Task 2 GREEN
- **Issue:** the event also carried `request_id`, `method`, `path` bound by middleware; the exact-key-set assertion failed.
- **Fix:** allow those as service keys (the plan already said "plus служебные ключи structlog"); the two meaningful keys are still asserted exactly.
- **Files modified:** `tests/test_routes/test_tg_user_auth.py`
- **Commit:** `08c4c0ef`

**Total deviations:** 2 auto-fixed (1 test gap, 1 blocking). **Impact:** none on production behaviour; both only tighten or correct tests.

## Issues Encountered

None beyond the deviations. Worth noting for later plans: an unreadable `phone` attribute on the user object in the route test surfaces the exception text in the error alert if `reported_phone_of` is bypassed (visible in the mutation run) — not reachable with the committed code.

## Threat Flags

None — no new endpoint, auth path, file access or schema change; T-19-01…T-19-05 mitigations are implemented and covered by the tests above.

## Known Stubs

None.

## Gates run

`tests/test_routes/test_tg_user_auth.py tests/test_messengers` (full dir), `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_phone_writer_runtime_guard.py tests/test_application/test_account_phone_writer.py`, `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_notices_registry.py`, `tests/test_application/test_declared_invariants.py`, all of `tests/test_templates/` — all green; `compileall -q app tests` exit 0. Callers of `complete_auth` in `tests/` are only the two modules above (plus a comment in `tests/test_templates/test_htmx_markup_gates.py`). `graphify update .` was not run (orchestrator refreshes the graph after the merge).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Telegram part of PHONE-12 is in place; PHONE-12 stays `Pending` in REQUIREMENTS.md until the phase verdict (not marked here).
- Assumption A1 (live `User.phone` is a digit string) is checked on the first live Telegram connection after rollout.

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

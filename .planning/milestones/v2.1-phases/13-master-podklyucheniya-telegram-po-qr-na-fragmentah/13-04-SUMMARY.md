---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
plan: 04
subsystem: auth
tags: [telethon, qr-auth, access-control, impersonation, htmx, tdd]

requires:
  - phase: 13-03
    provides: "qr_expired status, refresh_qr limited to qr_expired and QR_SESSION_TTL, refresh-qr on respond()"
  - phase: 13-02
    provides: "verify-2fa on respond(), account saved from complete_auth's result, race_client and the two race rules"
  - phase: 13-01
    provides: "anchor #tg-connect-step, step include, POST qr-status saving the account, POLLING_CASES"
provides:
  - "QRAuthState.user_id (required, no default); start_qr_auth(api_id, api_hash, user_id)"
  - "_owned(session_id, user_id): a foreign session is a missing one; status gone from get_qr_status"
  - "get_qr_status/refresh_qr/submit_2fa/complete_auth take user_id and read state only through _owned"
  - "complete_auth takes only the owner's session in success; owner check before pop with no await between"
  - "success is reported before the TTL check (a late scan is not «expired»)"
  - "TG_SESSION_NOT_FOUND_MESSAGE; user.id (the impersonation subject) in every session-layer call"
affects: [13-05, 13-06]

actuals:
  tokens: 19595
  tasks: 2
  commits: 4
plan_head_before: cce4ace1512636d23c8a60e99d34f6806d41d454

tech-stack:
  added: []
  patterns:
    - "Ownership check in the session layer: every accessor reads state through one helper that treats a foreign session as missing"
    - "Foreign-vs-unknown byte equality: status, body and headers (minus date and x-request-id) of two responses compared, not a substring"
    - "Second user on the same test client: register + POST /login replaces the access_token cookie"

key-files:
  created: []
  modified:
    - app/messengers/telegram_user.py
    - app/pages/accounts.py
    - tests/test_messengers/test_telegram_user.py
    - tests/test_routes/test_tg_user_auth.py

key-decisions:
  - "Phase 13-04: a QR session belongs to the user who started it; QRAuthState.user_id is required with no default, and under impersonation it is the subject (payload sub), the same user the account is saved on (D-04)"
  - "Phase 13-04: an unknown or foreign session_id gets status gone and one answer on poll, refresh-qr and verify-2fa: «Сессия подключения не найдена. Начните заново.»; only the owner's outdated session answers «Сессия авторизации истекла» because the owner check runs before the TTL check (D-03, D-04)"
  - "Phase 13-04: complete_auth returns None and touches nothing unless the caller owns the session and it is in success; the owner check and pop have no await between them, so one scan still gives one account (D-01)"
  - "Phase 13-04: get_qr_status reports success before the TTL check, so a scan finished after QR_SESSION_TTL but before cleanup is not lost as «expired» (Pitfall 10, planner's decision within D-01; the TTL itself is unchanged)"

patterns-established:
  - "Only _owned and the background _wait_for_qr read _qr_sessions directly (AST check in the plan's acceptance)"

requirements-completed: [FETCH-02]

coverage:
  - id: D1
    description: "The session binds to the user who started it; the constructor without an owner does not build; under impersonation the session and the account are on the subject, not the admin"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_session_is_owned_by_the_user_who_started_it"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_the_wizard_binds_the_session_to_the_impersonated_subject"
        status: pass
    human_judgment: false
  - id: D2
    description: "A foreign poll of a scanned session answers byte-equal to an unknown session_id, saves no account, leaves the session, its status, string and client alone; the owner then reaches «Подключено» with the account on the owner"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_foreign_poll_is_answered_as_unknown_and_leaves_no_trace"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_foreign_user_sees_no_session"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_foreign_complete_leaves_the_session_alone"
        status: pass
    human_judgment: false
  - id: D3
    description: "A foreign refresh-qr and a foreign verify-2fa answer byte-equal to an unknown session_id; recreate and sign_in are never awaited; the owner then refreshes / connects"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_foreign_refresh_is_answered_as_unknown_and_leaves_no_trace"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_foreign_password_is_answered_as_unknown_and_leaves_no_trace"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_foreign_refresh_changes_nothing"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_foreign_password_is_never_submitted"
        status: pass
    human_judgment: false
  - id: D4
    description: "One scan, one account after the owner check: concurrent completes give one string; complete_auth outside success leaves the session; 13-02's two race rules still green with unchanged assertions; a late scan stays success"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_concurrent_completes_yield_one_session_string"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_complete_auth_takes_only_a_successful_session"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_late_scan_is_still_a_success"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_two_concurrent_password_submits_save_one_account"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_two_concurrent_polls_after_success_save_one_account"
        status: pass
    human_judgment: false
  - id: D5
    description: "Foreign answers stop polling (POLLING_CASES rows poll-foreign, refresh-foreign, verify-foreign) and no response-layer or markup registry moved (11-file wave-gate run)"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_stops_by_a_response_without_trigger"
        status: pass
      - kind: other
        ref: "uv run pytest <11-file wave-gate run from the plan's task 2 verify> -q -p no:randomly (385 passed)"
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-09-21
status: complete
---

# Phase 13 Plan 04: QR session ownership Summary

**A QR session now belongs to the user who started it. `QRAuthState.user_id` is required, and under impersonation it is the subject. Every session-layer accessor reads state through `_owned`, which treats a foreign session as a missing one. A signed-in user who holds someone else's `session_id` (it is written to logs) now gets «Сессия подключения не найдена. Начните заново.» on the poll, `refresh-qr` and `verify-2fa`, byte for byte the same response as for an unknown id. Nothing happens to the owner's session, and the owner still reaches «Подключено».**

## Performance

- **Duration:** about 16 min
- **Started:** 2026-09-21T15:11:39Z
- **Completed:** 2026-09-21T15:27:28Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 4. These are the 4 files the plan lists. No gate registry moved.

## Accomplishments
- **Session layer (D-01, D-03, D-04):**
  - `QRAuthState.user_id: int` sits right after `client`, with no default.
  - `start_qr_auth(api_id, api_hash, user_id)` writes the owner.
  - `_owned(session_id, user_id)` returns the state only if it exists and `state.user_id == user_id`.
  - `get_qr_status(session_id, user_id)` has this order: `_owned`, and None gives `gone`. Then `success` is reported **before** the TTL check (Pitfall 10). Then the TTL check gives `expired`. Otherwise the status and error text are returned as before.
  - `complete_auth(session_id, user_id)` does `_owned`, then checks for `success`, then `pop`, with no `await` in between.
  - `refresh_qr` and `submit_2fa` read state through `_owned` first.
  - The comment above `_owned` explains why this check is the only protection, and that it must run before any mutation.
- **Page layer:**
  - New constant `TG_SESSION_NOT_FOUND_MESSAGE`.
  - `start_qr_auth(..., user_id=user.id)`, and `user.id` is passed to every `get_qr_status`, `refresh_qr`, `submit_2fa` and `complete_auth` call.
  - `gone` answers the error step with the not-found text in all three handlers. So does losing the race (`complete_auth` returns None).
  - `expired` keeps `TG_SESSION_EXPIRED_MESSAGE`.
- **Tests:**
  - 8 new session-layer rules and 4 new route rules.
  - 3 new `POLLING_CASES` rows: `poll-foreign`, `refresh-foreign`, `verify-foreign`.
  - An `owner_id` fixture, and an `owner` argument on every seed. `POLLING_CASES` seeds now receive the owner.
  - Unknown-session tests now expect «не найдена», and `test_get_qr_status_missing` expects `gone`.

## Task Commits

1. **Task 1 (TDD): the session belongs to the user who started it: binding, poll, completion**
   - RED `dcb28996` (test): add failing tests for QR session ownership on the poll
   - GREEN `3211993e` (feat): a QR session belongs to the user who started it
2. **Task 2 (TDD): foreign `refresh-qr` and `verify-2fa` are refused and leave no trace**
   - RED `1bf4a996` (test): add failing tests for foreign refresh-qr and verify-2fa
   - GREEN `b1da2a17` (feat): foreign refresh-qr and verify-2fa change nothing on the owner's session

No REFACTOR commit was needed.

## TDD Gate Compliance

| Task | RED commit | Target test and exact red assertion | GREEN commit |
|---|---|---|---|
| 1 | `dcb28996` | `test_a_foreign_poll_is_answered_as_unknown_and_leaves_no_trace`: `AssertionError: посторонний опросом чужой сессии сохранил 1 аккаунт(ов) — чужой Telegram записан не на владельца (D-04)` (`assert [<MessengerAccount …>] == []`) | `3211993e` |
| 2 | `1bf4a996` | `test_a_foreign_refresh_changes_nothing`: `AssertionError: \`recreate\` не ожидался: посторонний пересоздал код чужой сессии (D-04)` | `b1da2a17` |

- **RED evidence, task 1:** `uv run pytest tests/test_messengers/test_telegram_user.py tests/test_routes/test_tg_user_auth.py -q -p no:randomly --junit-xml=<scratchpad>/red1.xml` exited 1, with 45 failed and 30 passed. A throwaway scratchpad script (not committed) converted that run's own junit to node:test TAP. `check tdd-red-evidence` returned **`RED_EVIDENCE_OK` / `target_test_failed`**.
  - The target test creates the victim's session through a REAL start by user A, with only `TelegramClient` patched. It fails on the planned behaviour: on the old tree, user B's poll saved A's Telegram account to B.
  - The other 44 failures are what `<tdd_notes>` predicts, and none is a RED target:
    - 38 × `TypeError: QRAuthState.__init__() got an unexpected keyword argument 'user_id'`, from seeds that now carry the owner
    - 2 × `start_qr_auth() … 'user_id'`
    - 1 × `get_qr_status() takes 1 positional argument`
    - 1 × `submit_2fa() takes 2 positional arguments`
    - 1 × `AttributeError: … no attribute 'user_id'` (the impersonation rule)
    - 1 named `AssertionError: человек не узнал, что сессия не найдена`
- **RED evidence, task 2:** the same command (`red2.xml`) exited 1, with 2 failed and 79 passed, and gave **`RED_EVIDENCE_OK` / `target_test_failed`**.
  - The second failure is `test_a_foreign_password_is_never_submitted`: `Failed: DID NOT RAISE <class 'RuntimeError'>`, which is the planned behaviour.
  - The two route rules and the two new registry rows for a foreign `refresh-qr` / `verify-2fa` were **already green** on the task 1 tree. Since task 1 the handlers classify through `get_qr_status(session_id, user.id)`, which answers `gone` for a foreign session before `refresh_qr` / `submit_2fa` are called. The session-layer rules measure the second check, the one at the mutation itself.
- **Mutant measurements (task 1 GREEN tree, working copy, restored from a scratchpad copy afterwards):**
  - With the owner and status check removed from `complete_auth` (plain `pop` as before), 2 tests failed:
    - `посторонний получил строку чужой сессии Telegram (D-04)`
    - `complete_auth в ожидании снял живую сессию — сканирование потеряно (D-01)`
  - With the TTL check put back before the success check, `test_a_late_scan_is_still_a_success` failed: `отсканированная сессия после срока ответила «истекло» — вход потерян`.
- Gate validation: `git log --grep "^test(13-04):"` and `--grep "^feat(13-04):"` each return two commits, and every `test` commit comes before its `feat`.

## Acceptance evidence

- **Task 1, order in `complete_auth`:** `awk '/^async def complete_auth/,/^def cleanup_qr_session/' … | grep -n '_owned(\|_qr_sessions.pop(\|await '` printed:
  ```
  12:    state = _owned(session_id, user_id)
  15:    _qr_sessions.pop(session_id, None)
  23:        await state.client.disconnect()
  ```
  `_owned` comes before `pop`, and there is no `await` between them.
- Task 1 counts: `def _owned(session_id: str, user_id: int)` = 1, `async def start_qr_auth(api_id: int, api_hash: str, user_id: int)` = 1, and `TG_SESSION_NOT_FOUND_MESSAGE = "…"` = 1. All three were 0 on `cce4ace1`.
- Task 2 counts:
  - Each of the four signatures = 1.
  - `_owned(session_id, user_id)` = 4.
  - The AST check printed `['_owned', '_wait_for_qr']` and exited 0.
  - `-k foreign` in the route module gave 6 passed: 3 rules and 3 registry rows.

## D-13 bound (diff scope of `app/messengers/telegram_user.py` against `cce4ace1`)

```
@@ -31,6 +31,9 @@   QRAuthState: user_id field
@@ -51,8 +54,8 @@   start_qr_auth signature (hunk context shows the preceding function)
@@ -65,7 +68,7 @@   QRAuthState(..., user_id=user_id) in start_qr_auth
@@ -106,11 +109,36 @@ _owned (new) and get_qr_status
@@ -121,9 +149,11 @@  refresh_qr through _owned
@@ -153,9 +183,10 @@  submit_2fa through _owned
@@ -171,11 +202,21 @@ complete_auth: _owned, success check, then pop
1 file changed, 57 insertions(+), 16 deletions(-)
```

The plan's three D-13 diffs are all empty with exit 0: the `# Messenger adapter` section (class `TelegramUserMessenger`), `_cleanup_expired_sessions` and `cleanup_qr_session`. `QR_SESSION_TTL = 300` is unchanged. `_wait_for_qr` is untouched. This plan is the last one allowed to touch this file.

## Verification

- Task 1 verify: the two-module run gave 75 passed. The `-k "foreign or impersonated or owned or concurrent_completes"` selection gave 7 passed.
- Task 2 verify: the two-module run gave 81 passed. The 11-file wave-gate run gave **385 passed** with no registry red.
- The 13-02 race rules (`test_two_concurrent_password_submits_save_one_account`, `test_two_concurrent_polls_after_success_save_one_account`) pass. Their diff is only the owner in the seed (`owner=racer` / `user_id=racer`), and their assertions are unchanged.
- `uv run python -m compileall -q app main.py tests` is clean, and `graphify update .` was run.
- I did not run the full suite. The plan does not require it, and the orchestrator runs it after this plan.

## Decisions Made
- See `key-decisions`. Within Claude's Discretion:
  - A second user on the same test client is created by `/api/auth/register` followed by `POST /login`, which replaces the `access_token` cookie. The owner signs back in the same way.
  - The foreign seeds in `POLLING_CASES` use `owner + 1` as the owner. The session layer compares ids only, so no second database row is needed for a registry row.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking for a valid RED] The `refresh_qr` / `submit_2fa` signatures moved from task 2 to task 1 GREEN**
- **Found during:** Task 1 planning of the RED sequence
- **Issue:** Task 2's session-layer rules call `refresh_qr(sid, other)` and `submit_2fa(sid, other, "x")`. On a tree with the old signatures they fail with `TypeError`, which is a build error and not RED. `<tdd_notes>` excludes that. Task 2 would have had no valid RED target.
- **Fix:** Task 1 GREEN (`3211993e`) gave both functions the `user_id` parameter, and the page layer passes `user.id`, but it added no owner check yet. Task 2 GREEN (`b1da2a17`) added `_owned` to both. The window between the two commits was guarded by the handlers' `get_qr_status(session_id, user.id)`. Task 2 RED then failed on the named assertion (`recreate` awaited), which is valid evidence.
- **Files modified:** app/messengers/telegram_user.py, app/pages/accounts.py
- **Committed in:** `3211993e`

**2. [Rule 1 - Test defect found in GREEN] The byte-equality helper compared `x-request-id`**
- **Found during:** Task 1 GREEN
- **Issue:** The status and body of the foreign and unknown responses were already equal. The only difference was `x-request-id`, which the app sets differently on every response.
- **Fix:** The header comparison now excludes `date` and `x-request-id`, and the docstring says why. Status and body are still compared in full.
- **Files modified:** tests/test_routes/test_tg_user_auth.py
- **Committed in:** `3211993e`

### Acceptance-criterion discrimination (reported as the brief asks)
- **Task 1:** `grep -c 'user_id=user.id' app/pages/accounts.py` ≥ 1 was **3 on the prior tree `cce4ace1`**, from the `MessengerAccount(user_id=user.id, …)` writes. On its own it does not measure the change. It went 3 → 4. What proves the binding: the `start_qr_auth(…, user_id=user.id)` call and `test_the_wizard_binds_the_session_to_the_impersonated_subject`, which was red before (`AttributeError`, no `user_id`) and is green now. The D-13 diffs are no-change guards, so they were green before by design. The `_owned`, `start_qr_auth` signature and `TG_SESSION_NOT_FOUND_MESSAGE` counts were 0 on `cce4ace1`.
- **Task 2:** Because of deviation 1, the four signature greps were already 1 on the task 1 tree `3211993e`. They were 0 on `cce4ace1`. What measures task 2: the `_owned(session_id, user_id)` count went 2 → 4, the AST check went from exit 1 (`['_owned', '_wait_for_qr', 'refresh_qr', 'submit_2fa']`) to exit 0, and the two session-layer rules were red before GREEN. The `-k foreign` route criterion was green on the task 1 tree, as explained under TDD evidence.

---

**Total deviations:** 2 auto-fixed (1 task-split change to get a valid RED, 1 test defect), plus 2 non-discriminating criteria reported, each proven another way. **Impact:** no scope creep. No gate registry moved, so there is no registry file outside `files_modified`, which is unlike 13-01…13-03. The 13-05 items (criterion-2 gate closure, `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES`, stale docstrings) and the 13-06 items (the criterion-3 «проверка владения СОХРАНЕНА» false-premise chronicle) were not touched.

## Issues Encountered
- None blocking.

## Threat Flags

None. T-13-01 (foreign `session_id` saves someone else's account), T-13-02 (a foreign request destroys the victim's session), T-13-03 (the response reveals that a session exists) and T-13-10 (impersonation binds to the subject) are mitigated as the plan's register states, and each is covered by named rules. T-13-11 (CSRF) is accepted: an attacker would need the victim's `session_id`, and the owner check rejects it. No new endpoint or trust boundary was added.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness
- 13-05 closes `POLLING_CASES`, which now also has the three foreign rows, and handles the stale registries and docstrings.
- 13-06 writes the criterion-3 chronicle («проверка владения не сохранена, а заведена»). The code it describes is these four commits.
- FETCH-02 is **not** marked Complete: sibling plans 13-05 and 13-06 declare it and have no SUMMARY yet.

## Self-Check: PASSED

- FOUND: app/messengers/telegram_user.py, app/pages/accounts.py, tests/test_messengers/test_telegram_user.py, tests/test_routes/test_tg_user_auth.py
- FOUND commits: dcb28996, 3211993e, 1bf4a996, b1da2a17 (`git rev-list --count cce4ace1..HEAD` = 4 before this SUMMARY commit)

---
*Phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah*
*Completed: 2026-09-21*

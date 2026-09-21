---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
plan: 03
subsystem: ui
tags: [htmx, fastapi, jinja2, telethon, qr-auth, polling, tdd]

requires:
  - phase: 13-02
    provides: "password step, verify-2fa on respond(), POLLING_CASES with an expected status, pair seed pattern for the TG wizard"
  - phase: 13-01
    provides: "anchor #tg-connect-step, step include tg_connect_step.html, _tg_step_markup, POST qr-status, POLLING_CASES registry"
provides:
  - "status qr_expired: asyncio.TimeoutError from QRLogin.wait() is a status, not an error (D-03)"
  - "refresh_qr recreates only from qr_expired and only within QR_SESSION_TTL"
  - "qr_expired branch of tg_connect_step.html (refresh form, «Обновить QR-код», no poller, no dead QR)"
  - "POST /accounts/connect/tg_user/refresh-qr on respond(); TG_REFRESH_FAILED_MESSAGE; the wizard's last JSON handler removed"
  - "pair seed ACCOUNTS_CONNECT_TG_USER_REFRESH_QR; NOT_YET_CONVERTED holds no wizard key"
affects: [13-04, 13-05, 13-06]

actuals:
  tokens: 11709
  tasks: 3
  commits: 5
plan_head_before: 91be580ec3ae17827e6a593f3a9f80727ad44a0b

tech-stack:
  added: []
  patterns:
    - "Token expiry is reproduced by a REAL Telethon QRLogin with a short expires; wait() raises asyncio.TimeoutError itself"
    - "Session-layer refusal (refresh_qr -> None) happens before any Telegram call and changes no state"

key-files:
  created: []
  modified:
    - app/messengers/telegram_user.py
    - app/pages/accounts.py
    - app/templates/accounts/includes/tg_connect_step.html
    - tests/test_messengers/test_telegram_user.py
    - tests/test_routes/test_tg_user_auth.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Phase 13-03: a timeout of QRLogin.wait() sets status qr_expired with no error text and no logger.error; the QR token (~30 s) and the session (300 s) are different lifetimes (D-03)"
  - "Phase 13-03: refresh_qr recreates the code only from qr_expired and only within QR_SESSION_TTL; otherwise None, no recreate, no status change (D-03, Pitfall 2, T-13-12)"
  - "Phase 13-03: refresh-qr classifies by get_qr_status first: expired -> «Сессия авторизации истекла», not qr_expired -> «Не удалось обновить QR. Начните заново.», qr_expired -> refresh_qr -> waiting step with the new QR and the same poller (D-02)"
  - "Phase 13-03: the qr_expired step shows no QR (the poll response carries no code URL, and a dead code invites a useless scan); its refresh form keeps the default blocking target (real submit button), so UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED went 18 -> 19"

patterns-established:
  - "POLLING_CASES now covers all four wizard handlers that answer with a body: start, poll, verify-2fa, refresh-qr"

requirements-completed: [FETCH-02]

coverage:
  - id: D1
    description: "A QR token timeout (real QRLogin.wait() raising asyncio.TimeoutError) sets status qr_expired, with no error text and no logger.error call"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_an_expired_qr_token_is_a_status_not_an_error"
        status: pass
    human_judgment: false
  - id: D2
    description: "Poll in qr_expired answers 200 with «QR-код истёк. Обновите его, чтобы продолжить.», a refresh form (hidden session_id, «Обновить QR-код») into #tg-connect-step, no hx-trigger and no QR image"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_an_expired_code_offers_a_refresh"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_stops_by_a_response_without_trigger[poll-qr-expired]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Expired code -> «Обновить QR-код» -> new QR, exactly one poller, same session_id; the next poll is 204 (real QRLogin and real _wait_for_qr)"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_refreshing_an_expired_code_resumes_polling"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_stops_by_a_response_without_trigger[refresh-success]"
        status: pass
    human_judgment: false
  - id: D4
    description: "An outdated session is not revived and a non-expired code is not recreated, on the session layer and through the handler; no-JS lands on the wizard page, no login goes to /login, an unknown session answers the error step"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_refresh_qr_does_not_revive_an_outdated_session"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_refresh_qr_recreates_only_an_expired_code"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_refreshing_an_outdated_session_says_it_expired"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_refreshing_a_non_expired_code_is_refused"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_refresh_degrades_and_requires_a_session"
        status: pass
    human_judgment: false
  - id: D5
    description: "Response-layer and markup registries moved by the conversion, each set from a run with a «Фаза 13, план 13-03» chronicle; no wizard key left in the backlog"
    verification:
      - kind: other
        ref: "uv run pytest <11-file wave-gate run from the plan's task 3 verify> -q -p no:randomly (370 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "In a real browser, ~30 s after the QR is issued the screen shows «QR-код истёк» and the button; pressing it gives a new QR and polling resumes; idling on the expired screen for more than ~270 s gives «Сессия авторизации истекла» (criterion 4, backstop)"
    requirement: FETCH-02
    verification: []
    human_judgment: true
    rationale: "Needs a live Telegram account, a phone scan and wall-clock waits; the stand's clock must be NTP-synced (Pitfall 6). The CDP browser runs on another machine. This is phase UAT."

duration: 19min
completed: 2026-09-21
status: complete
---

# Phase 13 Plan 03: expired QR code as a status, and refresh-qr on fragments Summary

**When the ~30-second QR token expires, the wizard now shows «QR-код истёк» with an «Обновить QR-код» button, instead of a dead-end «Ошибка авторизации». The refresh button posts to `refresh-qr`, which now runs on `respond()`: it returns a new QR and a poller in the same fragment, so polling resumes. `refresh_qr` recreates the code only from `qr_expired` and only while the session is younger than `QR_SESSION_TTL`, so an outdated session is not revived. After this plan the wizard has no JSON handler left.**

## Performance

- **Duration:** about 19 min
- **Started:** 2026-09-21T14:07:37Z
- **Completed:** 2026-09-21T14:26:30Z
- **Tasks:** 3 (tasks 1 and 2 TDD)
- **Files modified:** 9. That is the 8 the plan lists, plus `tests/test_templates/test_htmx_markup_gates.py` (deviation 1).

## Accomplishments
- **`_wait_for_qr` (D-03).** A new `except asyncio.TimeoutError:` branch sits between `CancelledError` and the general `Exception` branch. It sets `state.status = "qr_expired"` and writes no error text, no log record and no traceback. The status comment of `QRAuthState` now lists `qr_expired`.
- **`refresh_qr` (D-03).** Two checks run before `recreate`. If the status is not `qr_expired`, it returns None. If `time.time() - created_at > QR_SESSION_TTL`, it returns None. The recreate mechanics are unchanged.
- **Step template.** New `qr_expired` branch: the text «QR-код истёк. Обновите его, чтобы продолжить.», a `form_wrapper` to `refresh-qr` into `#tg-connect-step` with a hidden `session_id`, the «Обновить QR-код» button and «Отмена». It shows no QR and has no poller.
- **Poll.** `qr_expired` now answers the `qr_expired` step with the `session_id`.
- **`accounts_connect_tg_user_refresh_qr`.** Converted to `@router.post(..., response_class=HTMLResponse)`. The field is read from the form body. Outcomes:
  - `expired` → `TG_SESSION_EXPIRED_MESSAGE`
  - any status other than `qr_expired` → the new `TG_REFRESH_FAILED_MESSAGE` (the pre-phase text, verbatim)
  - `refresh_qr` returns None → `TG_REFRESH_FAILED_MESSAGE`
  - success → the waiting step with the new QR and the poller

  Every outcome goes through `respond(redirect="/accounts/connect/tg_user", fragment=_step)`, and no login goes to `respond(redirect="/login")`.
- **Tests.** Seven new named rules (3 on the session layer, 4 on routes) and 5 new `POLLING_CASES` rows. The two JSON `refresh-qr` tests and their private `auth_setup` app fixture are removed.

## Registry movements (every number set from a run)

| Registry | Before -> after | Measured failure text that set it |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 11 -> 10 | `число непереведённых обработчиков стало 10, а в файле записано 11` (+ overlap: `…остался в перечне отставания: ['app/pages/accounts.py::accounts_connect_tg_user_refresh_qr']`) |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 16 -> 17 | `обработчиков, отдающих фрагмент, найдено 17, объявлено 16` |
| `POST_PAIR_CASES_DECLARED` | 56 -> 58 | `случаев пар в реестре 58, объявлено 56` (before the cases: `…пары транспортов у них нет…`) |
| `PAIRED_302_ASSERTIONS_DECLARED` | 165 -> 167 | `утверждений 302 о переведённых обработчиках 167, объявлено 165` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 76 -> 77 | `вызовов слоя ответа БЕЗ фрагмента найдено 77, а объявлено 76` |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` (not in the plan) | 18 -> 19 | `блоков вызова макроса-обёртки разобрано 19, объявлено 18` |

- The same first run also reddened `test_control_positive_the_untouched_source_tree_keeps_every_gate_green` and `test_control_negative_an_undeclared_fragment_handler_reddens_the_gate`. Both follow from the two counters above, and both went green once the counters were set, with no edits of their own.
- **Plan-quoted vs measured.** The plan expected 11 -> 10, 16 -> 17 and 76 -> 77, and those are the measured numbers. The plan named no numbers for pairs or 302 assertions; both were set from the run.
- `NOT_YET_CONVERTED_COUNT` also has the **Phase 13 summary chronicle** (14 -> 10). It names the four wizard handlers in words: start (conversion, 13-01), complete (removal, D-01, 13-01), 2FA (conversion, 13-02) and refresh (conversion, 13-03). The remaining 10 are exactly the Phase 14 auth handlers.

## Task Commits

1. **Task 1 (TDD): an expired QR token as a status**
   - RED `6ddd451b` (test): add failing tests for an expired QR token as a status
   - GREEN `0216d2c3` (feat): an expired QR token is a status with a refresh button
2. **Task 2 (TDD): refresh-qr on fragments**
   - RED `338d9931` (test): add failing tests for refresh-qr on fragments
   - GREEN `122569a3` (feat): refresh-qr on fragments, a new code resumes polling
3. **Task 3: registries.** `0fbe64e7` (test): record response-layer registries after the refresh-qr conversion

No REFACTOR commit was needed.

## TDD Gate Compliance

| Task | RED commit | Target test and exact red assertion | GREEN commit |
|---|---|---|---|
| 1 | `6ddd451b` | `test_an_expired_qr_token_is_a_status_not_an_error`: `AssertionError: истёкший токен QR дал status='error' error='' вместо «код истёк» — человек увидит «Ошибку авторизации» без выхода (D-03)` (`assert 'error' == 'qr_expired'`) | `0216d2c3` |
| 2 | `338d9931` | `test_refresh_qr_does_not_revive_an_outdated_session`: `AssertionError: \`recreate\` не ожидался: сессия старше срока ожила новым кодом (Pitfall 2)` | `122569a3` |

- **RED evidence, task 1:** `uv run pytest tests/test_messengers/test_telegram_user.py tests/test_routes/test_tg_user_auth.py -q -p no:randomly --junit-xml=<scratchpad>/red1.xml` exited 1, with 2 failed and 56 passed. A throwaway scratchpad script (not committed) converted that run's own junit to node:test TAP. `check tdd-red-evidence` returned **`RED_EVIDENCE_OK` / `target_test_failed`**. The red text reproduces the RESEARCH §Pattern 4 probe word for word (`status='error' error=''`). The second failure was `test_polling_an_expired_code_offers_a_refresh`, a named `AssertionError: человек не узнал, что QR-код истёк…`. The `poll-qr-expired` registry row passed on the prior tree. That is expected: the error step it answered carried no trigger. It is not a RED target.
- **RED evidence, task 2:** the same command (`red2.xml`) exited 1, with 10 failed and 56 passed, and gave **`RED_EVIDENCE_OK` / `target_test_failed`**. All 10 failures were named `AssertionError`s:
  - Both session-layer rules failed on «`recreate` не ожидался…».
  - The 8 route rules and registry rows failed on `ответил 500`. The JSON handler cannot parse a form body, and the app answers 500. The plan says these are not RED targets.
- **D-03 non-vacuity.** The D-03 test uses a real `QRLogin(client, [])` whose `_resp.expires` is 50 ms ahead, so `wait()` raises `asyncio.TimeoutError` itself. It also asserts that `add_event_handler` was called, which proves the real `wait()` ran. The end-to-end route rule uses a real `QRLogin` and a real `_wait_for_qr` task. It waits for the task to finish, then asserts `qr_expired` before the first poll. **Mutant measurement:** I added `logger.error("qr_auth_error", …, exc_info=True)` to the timeout branch in the working copy and ran `-k expired_qr_token`. It failed with `AssertionError: нормальное истечение кода записано в журнал как ошибка: call('qr_auth_error', session_id='sid-token-expired', exc_info=True)`. I restored the file from a scratchpad copy, and `git diff` showed only the intended GREEN changes.
- Gate validation: `git log --grep "^test(13-03):"` and `--grep "^feat(13-03):"` each return commits, and every `test` commit comes before its `feat`.

## D-13 bound (diff scope of `app/messengers/telegram_user.py` against the merge base with master)

```
@@ -32,7 +32,7 @@ QR_SESSION_TTL = 300          <- status comment of QRAuthState gains qr_expired
@@ -87,6 +87,15 @@ async def _wait_for_qr       <- except asyncio.TimeoutError branch
@@ -117,6 +126,16 @@ async def refresh_qr      <- status check and QR_SESSION_TTL check
1 file changed, 20 insertions(+), 1 deletion(-)
```

The acceptance diffs for the `# Messenger adapter` section (class `TelegramUserMessenger`) and for `_cleanup_expired_sessions` are both empty with exit 0. `QR_SESSION_TTL = 300` is unchanged, and so are `get_qr_status`, `submit_2fa` and `complete_auth`. Ownership (`user_id`, `_owned`, `gone`) is not touched; that is 13-04.

## Verification

- Task 1 verify: `-k expired` gave 2 passed. The two-module run gave 58 passed.
- Task 2 verify: the two-module run gave 66 passed. `-k refresh` gave 9 passed.
- Task 3 verify: the 3-file run gave 129 passed. The 11-file wave-gate run gave **370 passed**.
- `uv run python -m compileall -q app main.py tests` is clean, and `graphify update .` was run.
- I did not run the full suite. The plan does not require it, and the orchestrator runs it after this plan.

## Decisions Made
- See `key-decisions`. Within Claude's Discretion:
  - The handler classifies by `get_qr_status` before it calls `refresh_qr`, so an outdated session answers «Сессия авторизации истекла» (D-03), not the generic refusal. The TTL check inside `refresh_qr` stays as defence in depth, and the session-layer rule measures it directly.
  - The error step receives `session_id` as well, which is harmless: the start/error branch does not print it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Registry not named in the plan] `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` went red (18 -> 19)**
- **Found during:** Task 3, first wave-gate run
- **Issue:** The refresh form in the `qr_expired` step is the fourth `form_wrapper` call block in `tg_connect_step.html`. 13-01 and 13-02 hit the same unnamed registry, and the orchestrator predicted it would happen again.
- **Fix:** Set 19 from the run, with a «Фаза 13, план 13-03» chronicle. The form has a real submit button («Обновить QR-код»), so the default blocking target is reachable and no `DISABLED_ELT_EXCEPTIONS` entry is needed. That same default also stops a double click from asking Telegram for two tokens.
- **Files modified:** tests/test_templates/test_htmx_markup_gates.py (outside the plan's `files_modified`)
- **Committed in:** `0fbe64e7`

### Acceptance-criterion discrimination (reported as the brief asks)
- **Task 1:** `awk '/except asyncio.TimeoutError/,/except Exception/' … | grep -c 'logger.error'` = 0 was **also 0 on the prior tree**, because the awk range was empty and the criterion was satisfied vacuously. The property was proven by the mutant measurement above instead. `QR_SESSION_TTL = 300` is a no-change guard, so it was green before by design. Every other task 1 criterion was 0 on `91be580e`.
- **Task 2:** The two D-13 diff criteria (adapter class, `_cleanup_expired_sessions`) are no-change guards, so they were green before by design. What proves the change: the `qr_expired` and `QR_SESSION_TTL` counts inside `refresh_qr`, the `TG_REFRESH_FAILED_MESSAGE =` constant and the HTMLResponse decorator were all 0 on `91be580e`. The two session-layer rules were red before GREEN.
- **Task 3:** `every_converted_handler_has_a_pair` was measured red before the two cases were added.

---

**Total deviations:** 1 auto-fixed (a registry the plan did not name), plus 3 non-discriminating criteria reported, each proven another way. **Impact:** no scope creep. Ownership (13-04), stale registries and docstrings (13-05) and criterion chronicles (13-06) were not touched.

## Issues Encountered
- None blocking.

## Intentional interim windows (named by the plan, not stubs)
- `refresh-qr` for an unknown session answers «Сессия авторизации истекла. Начните заново.», because `get_qr_status` returns `expired` for a missing session. Plan 13-04 separates «not found» from «expired» and adds the ownership check. The pair case uses a structural mark (the start-again form) so that text change will not break it.
- `app/messengers/telegram_user.py:1` still carries the pre-phase `import structlog` pattern, and `verify-2fa` logs through a local import. Neither was touched.

## Threat Flags

None. T-13-12 (revival and state reset through `refresh_qr`), T-13-15 (no `logger.error` on normal expiry) and T-13-07 (no auto-refresh) are mitigated as the plan's register states, and each is covered by a named rule. T-13-13 (clock skew) is accepted, with NTP as a UAT precondition.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness
- 13-04 adds the ownership check. All four wizard handlers now read `session_id` from the form body and classify by `get_qr_status`, which is where the owner binding and the `gone` status will go.
- 13-05 closes `POLLING_CASES`, which now has rows for all four wizard handlers that answer with a body, and handles the stale registries.
- FETCH-02 is **not** marked Complete: sibling plans 13-04…13-06 declare it and have no SUMMARY yet.

## Self-Check: PASSED

- FOUND: app/messengers/telegram_user.py, app/pages/accounts.py, app/templates/accounts/includes/tg_connect_step.html, tests/test_messengers/test_telegram_user.py, tests/test_routes/test_tg_user_auth.py, tests/test_pages/test_htmx_gates.py, tests/test_pages/test_htmx_post_pairs.py, tests/test_pages/test_hx_location_destinations.py, tests/test_templates/test_htmx_markup_gates.py
- FOUND commits: 6ddd451b, 0216d2c3, 338d9931, 122569a3, 0fbe64e7 (`git rev-list --count 91be580e..HEAD` = 5 before this SUMMARY commit)

---
*Phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah*
*Completed: 2026-09-21*

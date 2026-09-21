---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
plan: 02
subsystem: ui
tags: [htmx, fastapi, jinja2, telethon, 2fa, race, respond_field_error]

requires:
  - phase: 13-01
    provides: "anchor #tg-connect-step, step include tg_connect_step.html, _tg_step_markup, _save_tg_account, POST qr-status, POLLING_CASES"
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "respond_field_error (422 on both transports, config-block swap rule for 422)"
provides:
  - "password branch of accounts/includes/tg_connect_step.html (form_wrapper to verify-2fa, hidden session_id, password field without a value)"
  - "POST /accounts/connect/tg_user/verify-2fa on respond()/respond_field_error(); TG_EMPTY_PASSWORD_MESSAGE"
  - "poll in needs_2fa answers the password step (no poller)"
  - "race_client fixture (per-request DB session on temp-file SQLite) and the two D-01 race rules"
  - "pair seed ACCOUNTS_CONNECT_TG_USER_VERIFY_2FA in test_htmx_post_pairs.py"
affects: [13-03, 13-04, 13-05, 13-06]

actuals:
  tokens: 16317
  tasks: 2
  commits: 3
plan_head_before: be404d384290a8f03dced8c753ab01da42d8304c

tech-stack:
  added: []
  patterns:
    - "Session string for the account comes only from complete_auth's result; the submit_2fa return value is never written"
    - "Field error of a wizard step: one 422 exit through respond_field_error with a page builder and a fragment builder that both omit the password"
    - "Race rules with a per-request AsyncSession and a rendezvous inside the Telethon call so both requests pass submit_2fa before either pops the session"

key-files:
  created: []
  modified:
    - app/pages/accounts.py
    - app/templates/accounts/includes/tg_connect_step.html
    - tests/test_routes/test_tg_user_auth.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "verify-2fa writes the account from complete_auth's result through _save_tg_account; a request that loses the race gets the error step (TG_SESSION_EXPIRED_MESSAGE until 13-04)"
  - "Other Telethon errors on the password step become the error fragment; the log record carries only the exception type, not the message, so no password can reach the log"
  - "The password field uses the field macro, which always prints value=\"\"; the rule asserts the value is empty and the submitted string is absent from the whole body, not that the attribute is missing"
  - "The concurrent verify-2fa rule uses a rendezvous in sign_in (both requests wait for each other, 2 s cap) on top of the plan's sleep(0), so the race cannot pass vacuously; the rule also asserts both requests entered sign_in"
  - "UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED 17 -> 18 (not named by the plan): the password form is a third form_wrapper block; its real «Подтвердить» button keeps the default blocking target"

patterns-established:
  - "POLLING_CASES rows carry an expected status (default 200); 422 field-error rows must also carry no hx-trigger"

requirements-completed: [FETCH-02]

coverage:
  - id: D1
    description: "Poll in needs_2fa answers 200 with the password step: form hx-post verify-2fa into #tg-connect-step, hidden session_id, required password field with an empty value, no hx-trigger"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_needs_2fa_answers_the_password_step"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_stops_by_a_response_without_trigger[poll-needs-2fa]"
        status: pass
    human_judgment: false
  - id: D2
    description: "Wrong password -> 422 with «Неверный пароль 2FA.» at the field on both transports; empty or missing password -> 422 «Введите пароль» without calling Telegram; the password is never echoed"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_wrong_password_answers_422_at_the_field_without_echo"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_an_empty_password_answers_422_with_the_client_text"
        status: pass
    human_judgment: false
  - id: D3
    description: "Right password saves exactly one account from complete_auth and answers «Подключено» without a trigger; other Telethon errors answer the error step, not 500, logged without the password; no-JS lands on the wizard page, no session goes to /login"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_right_password_saves_one_account_from_complete_auth"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_telethon_failure_on_the_password_step_is_a_fragment"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_verify_2fa_degrades_and_requires_a_session"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-01 under a race: two concurrent verify-2fa and two concurrent polls after success each save exactly one account; a second sequential poll does not save again"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_two_concurrent_password_submits_save_one_account"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_two_concurrent_polls_after_success_save_one_account"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_a_second_poll_after_success_does_not_save_again"
        status: pass
    human_judgment: false
  - id: D5
    description: "Response-layer registries moved by the conversion, each set from a run with a «Фаза 13, план 13-02» chronicle"
    verification:
      - kind: other
        ref: "uv run pytest <11-file wave-gate run from the plan's task 2 verify> -q -p no:randomly (357 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "In a real browser, an account with 2FA goes through the password step: a wrong password keeps the person on the step with the error at the field, the right one leads to «Подключено» (criterion 4, backstop)"
    requirement: FETCH-02
    verification: []
    human_judgment: true
    rationale: "Needs a live Telegram account with 2FA and a phone scan; the CDP browser runs on another machine. This is phase UAT."

duration: 22min
completed: 2026-09-21
status: complete
---

# Phase 13 Plan 02: 2FA password step on fragments and one account per scan Summary

**When the poll sees `needs_2fa`, it now answers with a password step: a `form_wrapper` form that posts to `verify-2fa` into `#tg-connect-step`. `verify-2fa` runs on `respond()` / `respond_field_error()`. A wrong or empty password answers 422 with the error at the field and never echoes the password. The right password saves the account from `complete_auth`'s result through `_save_tg_account`, so two concurrent submits save one account instead of two.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-21T13:01:31Z
- **Completed:** 2026-09-21T13:23:01Z
- **Tasks:** 2 (task 1 TDD)
- **Files modified:** 7 (the 6 the plan lists, plus `tests/test_templates/test_htmx_markup_gates.py`; see deviation 2)

## Accomplishments
- New `password` branch in `tg_connect_step.html`, with the pre-phase texts copied verbatim (the paragraph, «Пароль 2FA», the placeholder, «Подтвердить», `autocomplete='off'`). The field has a fixed `id='password'` and `required`, with `error=password_error` and no value. The form uses the wrapper's default blocking target, which is the client-side guard against a double click.
- `accounts_connect_tg_user_verify_2fa` is rewritten. The form fields are read from the body. An empty password gives 422 with `TG_EMPTY_PASSWORD_MESSAGE`. An expired or unknown session gives the error step. A status other than `needs_2fa` gives «Ошибка авторизации». On `submit_2fa`: `ValueError` gives 422 with the verbatim text at the field, `RuntimeError` gives the error step, and any other exception gives the error step plus a log record that carries only the exception type. Only then does the handler call `complete_auth` and save through `_save_tg_account`. All outcomes except 422 go through `respond(redirect="/accounts/connect/tg_user", fragment=...)`.
- The poll's `needs_2fa` branch now answers the password step with `session_id`.
- The test module adds 9 named rules, 5 `POLLING_CASES` rows (the registry now carries an expected status), and the `race_client` fixture. The two JSON `verify-2fa` tests are removed. The `refresh-qr` JSON tests are left untouched for 13-03.

## Registry movements (every number set from a run)

| Registry | Before -> after | Measured failure text that set it |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 12 -> 11 | `число непереведённых обработчиков стало 11, а в файле записано 12` (+ overlap rule: `…остался в перечне отставания: ['app/pages/accounts.py::accounts_connect_tg_user_verify_2fa']`) |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 15 -> 16 | `обработчиков, отдающих фрагмент, найдено 16, объявлено 15` |
| `POST_PAIR_CASES_DECLARED` | 54 -> 56 | `случаев пар в реестре 56, объявлено 54` (before the cases: `…пары транспортов у них нет…: app/pages/accounts.py::accounts_connect_tg_user_verify_2fa`) |
| `PAIRED_302_ASSERTIONS_DECLARED` | 163 -> 165 | `утверждений 302 о переведённых обработчиках 165, объявлено 163` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 75 -> 76 | `вызовов слоя ответа БЕЗ фрагмента найдено 76, а объявлено 75` |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` (not in the plan) | 17 -> 18 | `блоков вызова макроса-обёртки разобрано 18, объявлено 17` |

Plan-quoted and measured numbers match (12 -> 11, 15 -> 16, 75 -> 76). The plan named no numbers for pairs or 302 assertions; both were set from the run. The markup registry was not named by the plan and was measured.

## Task Commits

1. **Task 1 (TDD): 2FA password step and the two save races**
   - RED `528366b3` (test): add failing tests for the 2FA password step and the two save races
   - GREEN `b1ce9854` (feat): 2FA password step on fragments, one account per scan under a race
2. **Task 2: response-layer registries.** `d93f461e` (test): record response-layer registries after the verify-2fa conversion

No REFACTOR commit was needed.

## TDD Gate Compliance

| Gate | Commit | Evidence |
|---|---|---|
| RED | `528366b3` | Target `test_polling_needs_2fa_answers_the_password_step` failed on `AssertionError: опрос в needs_2fa не показал поле пароля — человек с 2FA не подключится` (`assert 'name="password"' in '…<div class="alert alert--error" role="alert">Ошибка авторизации</div>…'`) |
| GREEN | `b1ce9854` | `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly` gives 32 passed; the `-k "concurrent or second_poll"` selection gives 3 passed |

- **RED evidence:** `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly --junit-xml=<scratchpad>/red.xml` exited 1 with 11 failed and 21 passed. A throwaway scratchpad script (not committed) converted that run's own junit to node:test TAP. `check tdd-red-evidence` returned **`RED_EVIDENCE_OK` / `target_test_failed`**.
- All 11 RED failures were named `AssertionError`s. The target failed on the password field. The eight `verify-2fa` rules and registry rows failed on `500 вместо 422/200/302`: on the 13-01 tree the JSON handler cannot parse a form body, and the app turns that into a 500 response instead of raising it into the test. The concurrent `verify-2fa` rule failed on its non-vacuity guard, `в вход с паролем вошли 0 запросов из двух`.
- On the 13-01 tree, three rules passed: the concurrent-poll rule, the second-poll rule and the `poll-needs-2fa` registry row. That is expected. The poll path was already race-safe in 13-01, and the error step it answered carried no trigger. These rules are proofs of D-01 and criterion 2, not RED targets.
- **Race mutant measurement (non-vacuity of `test_two_concurrent_password_submits_save_one_account`).** On the GREEN tree I edited `app/pages/accounts.py` in the working copy so the handler writes the string returned by `submit_2fa` (`mutant_string = await submit_2fa(...)`, a bare `await complete_auth(session_id)`, then `_save_tg_account(db, user, mutant_string)`). Then I ran:
  `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly -k "concurrent"`
  Output: `AssertionError: два конкурентных верных пароля сохранили не один аккаунт — одно сканирование, два аккаунта (RESEARCH §Pitfall 3)` / `assert 2 == 1`, **1 failed, 1 passed**. That is two accounts under the same race. I restored the file with `git checkout -- app/pages/accounts.py`, and `git status --porcelain` came back empty apart from the orchestrator's untracked `milestone.lock`.
- The concurrent-poll rule has no matching mutant. In the poll handler there is no `await` between `get_qr_status` and the synchronous `pop` inside `complete_auth`, so no source for the saved string that is not `complete_auth` could produce two accounts under `gather`. The rule guards against a future reordering. It is not proven non-vacuous against today's code.

## Verification

- Task 1 verify: 32 passed. The `-k "concurrent or second_poll"` selection gave 3 passed.
- Task 2 verify: the 3-file gate run gave 127 passed. The 11-file wave-gate run gave **357 passed**.
- `uv run python -m compileall -q app main.py tests` is clean, and `graphify update .` was run.
- I did not run the full suite. The plan does not require it, and the orchestrator runs it after this plan.

## Decisions Made
- See `key-decisions`. Inside Claude's Discretion: the log record on a Telethon failure is `tg_verify_2fa_error` with `error_type` only. `str(e)` is left out on purpose, because the threat register T-13-05 requires the log to carry no password and the exception text is not under our control.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test defect found in GREEN] The no-JS empty-password check read the whole page**
- **Found during:** Task 1 GREEN
- **Issue:** `hx-trigger` legitimately appears in the page shell outside the wizard, so `assert "hx-trigger" not in plain.text` failed on the shell and not on the wizard.
- **Fix:** For the no-JS response, the check now reads `_content_of_the_wizard(plain.text)`, the same helper the 13-01 page test uses. The htmx responses are still checked in full.
- **Files modified:** tests/test_routes/test_tg_user_auth.py
- **Committed in:** `b1ce9854`

**2. [Rule 1 - Registry not named in the plan] `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` went red (17 -> 18)**
- **Found during:** Task 2, wave-gate run
- **Issue:** The password form is the third `form_wrapper` call block in `tg_connect_step.html`. 13-01 hit the same unnamed registry.
- **Fix:** Set 18 from the run, with a chronicle. The form has a real submit button, so the default blocking target is reachable and no `DISABLED_ELT_EXCEPTIONS` entry is needed. The other markup registries (callers, parametric targets) did not move, because the file was already a caller.
- **Files modified:** tests/test_templates/test_htmx_markup_gates.py (outside the plan's `files_modified`)
- **Committed in:** `d93f461e`

**3. [Plan-internal inconsistency] «строки `value=` у поля пароля нет» vs «`field(...)` БЕЗ `value`»**
- The `field` macro always prints `value="{{ value }}"`, so a password field built with the macro, as the action requires, carries `value=""`. `field.html` is not in this plan's files. The rule therefore asserts that the value attribute is **empty** and that the submitted password is absent from the **whole** response body. That is the substance of D-08 and T-06-02.

**4. [Strengthening] The concurrent `verify-2fa` rule uses a rendezvous inside `sign_in` instead of only `await asyncio.sleep(0)`**
- With only `sleep(0)`, the first request can pop the session before the second one reaches `submit_2fa`, because the second is waiting on its own aiosqlite user lookup. The mutant would then not produce two accounts, and the rule would pass vacuously. Each `sign_in` now waits for the other to enter (capped at 2 s) and then yields with `sleep(0)`. The rule also asserts that both requests entered.

### Acceptance-criterion discrimination (reported as the brief asks)
- `awk … accounts_connect_tg_user_verify_2fa … | grep -c 'await complete_auth('` returns `1`. **It also returned 1 on the 13-01 tree**, because the old JSON handler called `await complete_auth(session_id)` and threw the result away. On its own this criterion does not measure the change. What does measure it: `MessengerAccount(` in the handler went 1 -> 0 (baseline measured with `git show HEAD:app/pages/accounts.py` while HEAD was the RED commit `528366b3`), `_save_tg_account(` went 0 -> 1, and the mutant measurement above. Every other criterion was 0 or red before the change. `every_converted_handler_has_a_pair` was measured red before the two cases were added.

---

**Total deviations:** 2 auto-fixed (1 test defect, 1 unnamed registry), plus 1 plan-inconsistency resolution, 1 strengthening, and 1 non-discriminating criterion reported. **Impact:** no scope creep. `app/messengers/telegram_user.py` was not touched, and the `refresh-qr` handler and its JSON tests were not touched.

## Issues Encountered
- None blocking.

## Intentional interim windows (named by the plan, not stubs)
- A `verify-2fa` request that loses the race, or that names an unknown session, answers «Сессия авторизации истекла. Начните заново.». Plan 13-04 separates «not found» from «expired» and adds the ownership check.
- `refresh-qr` is still JSON (plan 13-03).

## Threat Flags

None. T-13-04, T-13-05 and T-13-08 are all mitigated as the plan's register states, and each is covered by a named rule.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness
- 13-03 adds `qr_expired` and converts `refresh-qr`. `POLLING_CASES` accepts rows with a non-200 status if one is needed.
- 13-04 adds the ownership check. Both save paths now go through `_save_tg_account` from `complete_auth`'s result, which is where the owner binding will be checked.
- FETCH-02 is **not** marked Complete: sibling plans 13-03…13-06 declare it and have no SUMMARY yet.

## Self-Check: PASSED

- FOUND: app/pages/accounts.py, app/templates/accounts/includes/tg_connect_step.html, tests/test_routes/test_tg_user_auth.py, tests/test_pages/test_htmx_gates.py, tests/test_pages/test_htmx_post_pairs.py, tests/test_pages/test_hx_location_destinations.py, tests/test_templates/test_htmx_markup_gates.py
- FOUND commits: 528366b3, b1ce9854, d93f461e (`git rev-list --count be404d38..HEAD` = 3 before this SUMMARY commit)

---
*Phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah*
*Completed: 2026-09-21*

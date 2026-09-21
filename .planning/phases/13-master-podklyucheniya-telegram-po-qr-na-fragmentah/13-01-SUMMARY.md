---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
plan: 01
subsystem: ui
tags: [htmx, fastapi, jinja2, telethon, qr-auth, polling, tracer]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "respond() response layer, form_wrapper macro, the MAX wizard step as an include (plan 11-18)"
  - phase: 12-zagruzka-izobrazheniy-bez-fetch
    provides: "manual-fetch counter at 5 (all five in the TG wizard), form_wrapper trigger/disabled_elt parameters"
provides:
  - "One permanent anchor #tg-connect-step on /accounts/connect/tg_user; the step include accounts/includes/tg_connect_step.html (start, waiting, connected, error)"
  - "POST /accounts/connect/tg_user/start-qr and POST /accounts/connect/tg_user/qr-status on respond(); waiting -> 204; success -> complete_auth + _save_tg_account + Connected"
  - "_tg_step_markup, _save_tg_account, TG_CONNECT_STEP_TEMPLATE and the TG_* refusal-text constants in app/pages/accounts.py"
  - "POLLING_CASES registry with test_polling_stops_by_a_response_without_trigger (13-02/13-03 add rows, 13-05 closes it)"
  - "Pair seeds ACCOUNTS_CONNECT_TG_USER_START_QR / ACCOUNTS_CONNECT_TG_USER_QR_STATUS in test_htmx_post_pairs.py"
affects: [13-02, 13-03, 13-04, 13-05, 13-06, 15-FETCH-03]

actuals:
  tokens: 18253
  tasks: 3
  commits: 4
plan_head_before: f21a6316cd05fd47b657415ca509dc028e06825f

tech-stack:
  added: []
  patterns:
    - "Polling stopped by the response: the poller is a child form of the waiting fragment and targets the permanent anchor explicitly; the anchor carries no trigger"
    - "Poll in the waiting state answers 204 from a builder passed to respond() by name"
    - "Form field read from the body inside the handler (not Form(...) in the signature)"

key-files:
  created:
    - app/templates/accounts/includes/tg_connect_step.html
  modified:
    - app/pages/accounts.py
    - app/templates/accounts/connect_tg_user.html
    - tests/test_routes/test_tg_user_auth.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_impersonation_gate.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_templates/test_htmx_inventory.py

key-decisions:
  - "The D-05 correction is built as the plan wrote it: the anchor #tg-connect-step is on the page with no trigger, and the poller is a form_wrapper form inside the waiting branch with hx-target=#tg-connect-step. Any 200 removes the poller, so polling stops."
  - "Start and error are one template branch. The button reads «Начать подключение» on step=start and «Начать заново» on step=error."
  - "The identifier-catalogue appendix entry for the TG poll's session_id was REMOVED, not rekeyed to POST (10 -> 9, measured by a run). session_id is now read from the form body, and the catalogue only watches signature parameters."
  - "UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED 15 -> 17 (not named in the plan): the step file has two form_wrapper call blocks. The start form's button keeps the default blocking target. The poller passes an empty target and is recorded as the fifth DISABLED_ELT_EXCEPTIONS caller."

patterns-established:
  - "Tracer on the real session layer: only the Telethon client is patched; start_qr_auth, _wait_for_qr and complete_auth are real, and session_id is taken from the fragment's hidden field"
  - "Stop-by-response registry: POLLING_CASES rows (slug, name, route, seed, polls) with a both-sides-present pair assertion"

requirements-completed: [FETCH-02]

coverage:
  - id: D1
    description: "Start -> QR -> 204 poll -> scan -> «Подключено» on fragments behind one anchor; exactly one MessengerAccount saved by the poll request; session removed"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_the_wizard_walks_from_start_to_connected"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_the_waiting_fragment_polls_into_the_persistent_anchor"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every 200 without polling carries no hx-trigger; waiting poll is 204 (criterion 2)"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_stops_by_a_response_without_trigger"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_tg_user_auth.py#test_the_polling_registry_holds_both_sides_of_the_pair"
        status: pass
    human_judgment: false
  - id: D3
    description: "Wizard page has no script, no onclick, no manual request assembly; complete route gone; GET poll is 405; refusals are fragments with verbatim texts; no-JS lands on the wizard page; no session goes to /login on both transports"
    requirement: FETCH-02
    verification:
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py (9 named tests besides the tracer and registry)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Gate registries moved by the conversion and removal, each set from a run with a «Фаза 13, план 13-01» chronicle"
    verification:
      - kind: other
        ref: "uv run pytest tests/test_pages/test_htmx_gates.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_markup_security.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_htmx_preserved.py tests/test_pages/test_htmx_post_pairs.py tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q (343 passed)"
        status: pass
      - kind: other
        ref: "uv run pytest tests/ -q (3459 passed, 0 failed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "In a real browser, «Начать подключение» shows the QR without a reload, the screen changes to «Подключено» after a phone scan, and the stream of poll requests stops (criterion 4, backstop)"
    requirement: FETCH-02
    verification: []
    human_judgment: true
    rationale: "Needs a live Telegram account and a phone scan. The CDP browser runs on another machine, so this is phase UAT and not automatable here."

duration: 1h 4m
completed: 2026-09-21
status: complete
---

# Phase 13 Plan 01: TG QR wizard on fragments, tracer slice Summary

**The Telegram QR wizard now runs on server-rendered fragments behind one permanent anchor, `#tg-connect-step`. The poller is a `form_wrapper` form inside the waiting fragment and stops when a response comes back without it. The POST poll saves the account itself. The `complete` route and the whole 152-line page script are gone.**

## Performance

- **Duration:** 1h 4m (40 min of that is the single full-suite run)
- **Started:** 2026-09-21T11:13:06Z
- **Completed:** 2026-09-21T12:17:22Z
- **Tasks:** 3 (task 1 tracer + TDD)
- **Files modified:** 11 (1 created, 10 modified). This is the owner-accepted overrun in the plan's §scope_acceptance.

## Accomplishments
- New include `accounts/includes/tg_connect_step.html`. It is the only markup source for the step, with branches start/error (one branch), waiting and connected. The poller is `form_wrapper(action=qr-status, target='#tg-connect-step', swap='innerHTML', trigger='every 3s', disabled_elt='')` with a hidden `session_id` and no button. There is no `|safe` or `Markup(`.
- The page `connect_tg_user.html` is reduced to the shell plus the permanent anchor `<div class="connect-shell" id="tg-connect-step">` and the include. Removed: the script, the three onclick handlers, the four hidden sections and `#error-box`.
- `accounts_connect_tg_user_start_qr` and `accounts_connect_tg_user_qr_status` (now POST, same name and address) answer through `respond()`, with literal `redirect=` addresses. In the waiting state the poll returns a 204 builder passed by name. `complete_auth` is called only on `success`, and its result goes to `_save_tg_account`, the single place that writes the account.
- The test module was rewritten onto the conftest fixtures. It has the tracer on the real session layer, the `POLLING_CASES` registry with the stop-by-response rule, and the refusal, no-JS, no-session and gone-route contracts. The `refresh-qr` / `verify-2fa` JSON tests are kept until 13-02 and 13-03.
- Nine gate registries were moved, each number set from a run of the rule that went red, with a «Фаза 13, план 13-01» chronicle (table below).

## Registry movements (every number set from a run)

| Registry | Before -> after | Measured failure text that set it |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 14 -> 12 | `число непереведённых обработчиков стало 12, а в файле записано 14` |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 13 -> 15 | `обработчиков, отдающих фрагмент, найдено 15, объявлено 13` |
| `POST_HANDLERS` | 37 -> 37 (no movement) | rule stayed green (minus complete, plus the POST poll) |
| `POST_PAIR_CASES_DECLARED` | 50 -> 54 | `случаев пар в реестре 54, объявлено 50` |
| `PAIRED_302_ASSERTIONS_DECLARED` | 159 -> 163 | `утверждений 302 о переведённых обработчиках 163, объявлено 159` |
| `ALLOWED_ROUTES` / `MUTATING_ROUTE_COUNT` | complete -> qr_status; 49 -> 49 | `изменяющие маршруты, о которых этот гейт не знает: …accounts_connect_tg_user_qr_status` |
| `CATALOGUE_APPENDIX_DECLARED` | 10 -> 9 (entry removed) | `заявлено и не найдено: ['app/pages/accounts.py::GET /accounts/connect/tg_user/qr-status → session_id']` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 73 -> 75 | `вызовов слоя ответа БЕЗ фрагмента найдено 75, а объявлено 73` |
| `MACRO_DEFINITION_SITES_CALLERS_DECLARED` | 23 -> 24 | `спрятано вызывающих 24, объявлено 23` |
| `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` | 8 -> 9 | `параметрических целей подмены спрятано вызывающих 9, объявлено 8` |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 15 -> 17 | `блоков вызова макроса-обёртки разобрано 17, объявлено 15` |
| `DISABLED_ELT_EXCEPTIONS[form_wrapper].callers` | 4 -> 5 callers; `_DECLARED` 2 unchanged | `множество вызывающих записи разошлось с измеренным` |
| `MANUAL_FETCH_SITES` / `_PLACES` / `_CEILING_AT_PHASE_08` | 5 -> 0 (named zero) | `мест ручной сборки запроса 0, объявлено 5 — ЧИСЛО УПАЛО ДО 0` |
| `POLLING_FRAGMENTS` | 10 -> 10 | stayed green. Assumption A2 held: the gate cannot see a poller generated by the macro, and this blind spot is now recorded above the constant |

## Task Commits

1. **Task 1 (tracer, TDD): end-to-end slice**
   - RED `6c1edd9e` (test): add failing tracer for the TG QR wizard on fragments
   - GREEN `2a94e800` (feat): TG QR wizard on fragments behind one persistent anchor
2. **Task 2: response-layer registries.** `8054140c` (test): record response-layer registries after the TG wizard conversion
3. **Task 3: markup registries.** `1f91850c` (test): record markup registries (form_wrapper callers, manual fetch to a named zero)

No REFACTOR commit was needed.

## TDD Gate Compliance

| Task | RED commit | Assertion that was red (target test `test_the_wizard_walks_from_start_to_connected`) | GREEN commit |
|---|---|---|---|
| 1 | `6c1edd9e` | `AssertionError: на странице мастера должен быть РОВНО ОДИН постоянный якорь шага — найдено 0; без него QR не появится` (`assert 0 == 1`) | `2a94e800` |

- RED evidence: `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly --junit-xml=…` gave exit 1 with 13 failed and 7 passed. The junit output was converted mechanically to node:test TAP with a throwaway scratchpad script (not committed). `check tdd-red-evidence` returned **`RED_EVIDENCE_OK` / `target_test_failed`**.
- All 13 RED failures were named `AssertionError`s on the planned behaviour: missing anchor, JSON instead of a fragment, 405 on POST qr-status, 200 instead of 302/204, and 500 on the old complete route. None were collection or import errors. The 7 passing cases were the four kept JSON tests, the registry's pair assertion, and two registry rows that were not supposed to poll: their JSON answers contained no `hx-trigger`, which is expected and not a vacuous RED.
- The tracer feedback gate was row 3 (interactive, end-of-phase, `<automated>`-only verify). I re-ran the verify after `2a94e800`: 20 passed, `-k` selection 7 passed, compileall clean. **Tracer verified end-to-end, then expanded.**

## Verification

- Task 1 verify: 20 passed. Task 2 verify: 161 passed. Task 3 verify (11-file cross run): 343 passed.
- **Full suite, once:** `uv run pytest tests/ -q -p no:randomly` (pytest-randomly is not installed, so the flag is a no-op). Result: **3459 passed, 0 failed**, 2402 s (40m02s), started **2026-09-21T11:37:01Z** and ended 12:17:13Z UTC. The run was outside the 00:00–05:00 UTC window and the admin-overview night flake did not appear. `tests/test_planning` was included.
- `uv run python -m compileall -q app main.py tests` is clean. `graphify update .` was run.

## Decisions Made
- See `key-decisions` above. Inside Claude's Discretion: the waiting indicator uses the macro default (`find .form-busy`, 300 ms threshold), and `hx-sync` is not set on the poller (RESEARCH §Pattern 2).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The no-session wizard test built its address in a loop, so the 302 walk could not name the handler**
- **Found during:** Task 2, first gate run: `tests/test_routes/test_tg_user_auth.py:376 (test_the_wizard_without_a_session_goes_to_login): обработчик не назван — адрес POST собран выражением`
- **Fix:** I rewrote the test with literal addresses as the first argument to `.post(…)` (four explicit calls), which is the form the plan's behaviour item 7 already required for the no-JS test.
- **Files modified:** tests/test_routes/test_tg_user_auth.py
- **Committed in:** `8054140c`

**2. [Rule 1 - Registry not named in the plan] `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` went red (15 -> 17)**
- **Found during:** Task 3
- **Issue:** The plan counted the call-block registry by files, but this constant counts form_wrapper call blocks, and the step file has two (start form and poller).
- **Fix:** Set 17 from the run, with a chronicle that separates the two blocking-target decisions (the start form's button keeps the default; the poller has an empty target and an exception entry).
- **Files modified:** tests/test_templates/test_htmx_markup_gates.py
- **Committed in:** `1f91850c`

**3. [Forecast vs measurement] The identifier catalogue entry was removed, not rekeyed.** This is the plan's own corrected premise (action item 4), and the run confirmed it: no entry under a new key was found, so `CATALOGUE_APPENDIX_DECLARED` went 10 -> 9 and the acceptance check `len(a) == n and no 'tg_user' key` exits 0.

**4. [Cosmetic, before the RED commit] The `POLLING_CASES` rows got an ASCII `slug` for pytest ids.** Cyrillic ids were escaped into unreadable `\u…` node ids. RED was re-run afterwards, so the RED evidence matches the committed file.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 registry the plan did not name), plus 1 forecast/measurement note and 1 cosmetic change. **Impact:** no scope creep. Every number was set from a run.

## Issues Encountered
- RESEARCH §Инвентарь row 8 predicted that `test_hx_location_destinations.py`'s `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` non-empty rule would go red when the script was removed. **It did not go red in any run of this plan** (task 2 gates and the full suite). The entry is now stale but not red, and it stays with plan 13-05 as the plan's §scope_acceptance says.
- The `refresh-qr` / `verify-2fa` handlers are still JSON (13-02 and 13-03), as §scope_note says.

## Intentional interim windows (named by §scope_note, not stubs)
- `needs_2fa` from the poll currently answers the error step with «Ошибка авторизации». The password step is plan 13-02.
- An unknown session answers «Сессия авторизации истекла. Начните заново.» because `get_qr_status` returns `expired` for a missing session. Plan 13-04 separates «not found» from «expired» and adds the ownership check.
- `_tg_step_markup(password_error=…)` and the `field` macro import in the step include are not used by any branch yet. They are the contract for 13-02.
- In-process state: a tab still running the old script after deploy will see «Ошибка сети» (GET qr-status is now 405 and POST complete is gone). This is expected, as RESEARCH §Runtime State Inventory says, and it is the same as any deploy that loses `_qr_sessions`.

## Threat Flags

None. The POST poll writing to the database is T-13-04 / T-13-10 in the plan's threat model. The ALLOWED_ROUTES entry for impersonation moved from `complete` to `qr_status` with its reason.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness
- The architecture the later plans build on is proven by one path: one permanent anchor, the poller inside the waiting fragment, polling stopped by a response without a trigger, `session_id` as a hidden field, and the account saved by the poll. 13-02 adds the password step and the `verify-2fa` conversion, and must write accounts through `_save_tg_account`. 13-03 adds `qr_expired` and `refresh-qr`. 13-04 adds the ownership check. 13-05 closes `POLLING_CASES` and the stale registries.
- FETCH-02 is **not** marked Complete: sibling plans 13-02…13-06 declare it and have no SUMMARY yet.

## Self-Check: PASSED

- FOUND: app/templates/accounts/includes/tg_connect_step.html
- FOUND: app/templates/accounts/connect_tg_user.html, app/pages/accounts.py, tests/test_routes/test_tg_user_auth.py
- FOUND commits: 6c1edd9e, 2a94e800, 8054140c, 1f91850c (`git rev-list --count f21a6316..HEAD` = 4 before this SUMMARY commit)

---
*Phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah*
*Completed: 2026-09-21*

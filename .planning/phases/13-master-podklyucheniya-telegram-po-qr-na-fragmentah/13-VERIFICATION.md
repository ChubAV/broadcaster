---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
verified: 2026-09-21T17:40:19Z
status: passed
score: 31/32 must-haves verified
covered_files:

  - .planning/REQUIREMENTS.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-01-PLAN.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-01-SUMMARY.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-02-PLAN.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-02-SUMMARY.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-03-PLAN.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-03-SUMMARY.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-04-PLAN.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-04-SUMMARY.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-05-PLAN.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-05-SUMMARY.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-06-PLAN.md
  - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-06-SUMMARY.md
  - app/messengers/telegram_user.py
  - app/pages/accounts.py
  - app/templates/accounts/connect_tg_user.html
  - app/templates/accounts/includes/tg_connect_step.html
  - tests/test_messengers/test_telegram_user.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_impersonation_gate.py
  - tests/test_routes/test_tg_user_auth.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_htmx_markup_security.py

covered_digest: "v1:sha256:152df17c6043e72976a7d24220782888a13f2421b7ca0b4a10dee3ca85aa1720"
behavior_unverified: 0
overrides_applied: 0
deferred: # owner-named deferrals, not later-phase coverage — neither item is claimed by any later phase

  - truth: "IN-03 — abandoned QR sessions keep a connected (possibly authorized) Telethon client"
    addressed_in: "владелец"
    evidence: "13-CONTEXT.md §Deferred Ideas: «Закрытие Telethon-клиента при уходе со страницы / «Отмене» — сегодня клиент живёт до чистки по сроку. Отдельная работа.»; D-13 bounds the session-layer edit; pre-existing (reviewer agrees)"
  - truth: "UI-17 — «Ошибка запуска QR авторизации: {e}» shows raw exception text"
    addressed_in: "владелец"
    evidence: "13-CONTEXT.md §Landmines: «Текст переезжает дословно, решение о нём — не предмет фазы»; D-09 moved refusal texts verbatim"
advisory:

  - finding: "WR-01 — refresh_qr «only from qr_expired» guard is check-then-await; two concurrent owner refreshes both call recreate()"
    category: other
    reason: "Real under concurrency (telegram_user.py:162-178: status flips to waiting only after `await recreate()`). Reachable only by the session OWNER (two tabs on one session_id, replay, no-JS resubmit); htmx `hx-disabled-elt` covers the single tab. Worst case: the rendered QR is the earlier of two tokens. Does not defeat criteria 2/3/4. Fix: claim the transition synchronously before the await (reviewer's patch), map the interim status to 204."
    evidence_status: "code reading; not reproduced by a test"
  - finding: "WR-02 — asyncio.TimeoutError branch classifies a post-scan timeout (DC migration / export request) as qr_expired"
    category: other
    reason: "Confirmed against Telethon 1.42.0 source: QRLogin.wait() awaits `self._client(self._request)` and `_switch_dc()` AFTER the event, and those can raise TimeoutError. Before the phase such a timeout surfaced as «Ошибка авторизации»; now as «QR-код истёк» → refresh on a half-switched client. Rare (scan + other-DC account + network timeout); the main criterion-4 path is unaffected. Fix: compare against qr_login.expires before classifying (reviewer's patch)."
    evidence_status: "library source read; no test reproduces it"
  - finding: "WR-03 — complete_auth pops/disconnects before _save_tg_account commits; a commit failure loses the scan and returns 500"
    category: other
    reason: "Real, but the pop-then-commit order is pre-existing: the removed POST /complete route (base 344dc789) did `complete_auth` then `db.commit()` identically. The phase moved it into one helper; the 500 now raises the global banner instead of a JSON error. Pop-before-persist is what gives one account per scan. Fix: wrap the save, rollback, answer the error step, log without the session string."
    evidence_status: "code reading + git show 344dc789"
  - finding: "WR-04 — the two ROUTE race tests do not discriminate the reorder mutant; the one-account property is held by the unit rule only"
    category: other
    reason: "Re-measured by this verifier with a scratch pytest plugin (disconnect moved before pop, patched in the session layer, the page module and the unit test's own binding): unit `test_concurrent_completes_yield_one_session_string` RED 3/3; `test_two_concurrent_password_submits_save_one_account` GREEN 3/3; `test_two_concurrent_polls_after_success_save_one_account` GREEN 5/6 (one incidental red). Unmutated control: 3 passed. The PROPERTY holds (code: no await between `_owned` check and `pop`; the handlers reach complete_auth with no yield after get_qr_status; unit rule discriminates), so the D-01 truths of 13-02/13-04 are VERIFIED. What is false is the plans'/docstrings' claim that the ROUTE tests prove it. Fix: rendezvous at get_qr_status in the poll race; yielding `disconnect` in the 2FA seed."
    evidence_status: "mutant runs in this verification"
  - finding: "IN-01 — ValueError/RuntimeError branches in verify-2fa catch unrelated Telethon errors and echo their text"
    category: other
    reason: "Real (accounts.py:563-567): a Telethon ValueError from compute_check would render as a 422 field error with internal text. Not the password; does not breach the no-echo prohibition. Fix: a dedicated WrongPassword exception."
    evidence_status: "code reading"
  - finding: "IN-02 — submit_2fa does not enforce needs_2fa at the session layer"
    category: other
    reason: "Real asymmetry (telegram_user.py:186-202); the only caller checks needs_2fa right before calling. Defensive hardening for future callers."
    evidence_status: "code reading"
  - finding: "UI-1 — 2FA step: 0px between the password field and «Подтвердить» (regression)"
    category: other
    reason: "Confirmed from markup+CSS: pre-phase field and actions were direct children of the 14px-gap `.connect-step`; now inside `form.form-wrapper` (only `position: relative`, app.css:2207), `.field` has no margin, and `.connect-step__form` (app.css:1934, used by MAX) is not applied. A phase-introduced visual regression; does not defeat any success criterion. Recommend fixing with the `.connect-step__form` wrapper before or with the UAT."
    evidence_status: "rendered-markup/CSS reading"
  - finding: "UI-2 — qr_expired: «Обновить QR-код»/«Отмена» left-aligned under centred text (regression)"
    category: other
    reason: "Confirmed from CSS: `.connect-step > form { align-self: stretch }` + `.connect-step__actions` without justify-content. Pre-phase the row sat directly in the centred column. Visual only."
    evidence_status: "CSS reading"
  - finding: "UI-3 — start/refresh lost the «Загрузка...» label (regression)"
    category: other
    reason: "Confirmed: base template script line 101 `setBtnLabel(btn, 'Загрузка...')`; now only a disabled button and the form-busy dot. Feedback degraded, not absent; does not defeat the goal."
    evidence_status: "git show 344dc789 + template reading"
  - finding: "UI-4 — scanning instruction shown on start/error, not on the waiting step"
    category: other
    reason: "Pre-existing (old #start-section carried the same text); copy improvement."
    evidence_status: "template reading"
  - finding: "UI-6 — qr_expired has no status colour treatment"
    category: other
    reason: "Design consistency; no criterion touches it."
    evidence_status: "template reading"
  - finding: "UI-7 — no typographic hierarchy between state message and instruction"
    category: other
    reason: "Design polish; shared style is pre-existing."
    evidence_status: "template reading"
  - finding: "UI-8 — waiting: ~28px doubled gap around the zero-height poller form"
    category: other
    reason: "Minor spacing side effect of the poller form being a flex item; fix by moving the poller after the actions row."
    evidence_status: "CSS reading"
  - finding: "UI-9 — #tg-connect-step has no aria-live"
    category: other
    reason: "Accessibility improvement; the MAX wizard has the same gap, so not a phase regression."
    evidence_status: "template reading"
  - finding: "UI-10 — password step does not take focus when swapped in"
    category: other
    reason: "Real (no autofocus); pre-phase script did not focus either. UX improvement."
    evidence_status: "template reading"
  - finding: "UI-11 — «Начать заново» is a dead end for «API не настроен»"
    category: other
    reason: "Text bound by D-09; the action beside it could be hidden for non-retryable errors."
    evidence_status: "template reading"
  - finding: "UI-12 — near-synonyms «Сессия подключения не найдена» / «Сессия авторизации истекла»"
    category: other
    reason: "Deliberate per D-04 (owner-only «истекла» vs unknown/foreign «не найдена» — the difference must exist so the foreign answer equals the unknown answer). No action recommended."
    evidence_status: "13-CONTEXT D-04"
  - finding: "UI-13 — no step orientation («шаг N из M»)"
    category: other
    reason: "Consistent with the MAX wizard; enhancement."
    evidence_status: "template reading"
  - finding: "UI-14 — stale CSS comment app.css:1925-1927 and dead `.connect-step[hidden]` rule"
    category: other
    reason: "Checked for criterion 1: nothing toggles `hidden` any more — no `hidden` attribute on any element in app/templates/accounts/ except `type=\"hidden\"` inputs, no script on the page, no JS in app/static/js touching connect steps. The rule is dead residue, the comment is false; criterion 1 holds. Cleanup only."
    evidence_status: "grep over templates and static js"
  - finding: "UI-15 — no «Отмена» on the password step"
    category: other
    reason: "Pre-existing; header «К аккаунтам» remains an exit."
    evidence_status: "git show 344dc789"
  - finding: "UI-16 — autocomplete='off' on the password field"
    category: other
    reason: "Carried verbatim from the pre-phase template; `current-password` would be better."
    evidence_status: "git show 344dc789"
human_verification:

  - test: "Criterion 4a — scan without 2FA: open /accounts/connect/tg_user, «Начать подключение», scan in Telegram (Настройки → Устройства → Подключить устройство)"
    expected: "QR appears without reload; screen switches to «Подключено» by itself; one tg_user account on the list; uvicorn log shows no further POST …/qr-status after «Подключено»"
    why_human: "Needs a real Telegram account and phone; the Telegram server is not substitutable; live browser requires owner consent (workflow.live_dom_uat: false)"
  - test: "Criterion 4b — account with 2FA: scan, enter a wrong password, then the right one"
    expected: "Wrong → stays on the password step, «Неверный пароль 2FA.» at the field, field empty; right → «Подключено», one account"
    why_human: "Live Telethon session with a 2FA password"
  - test: "Criterion 4c — expired code: get a QR and do NOT scan for ≥ ~30 s, then press «Обновить QR-код» and scan the new code"
    expected: "Screen shows «QR-код истёк. Обновите его, чтобы продолжить.» by itself (no «Ошибка авторизации»); refresh shows a new QR and polling resumes; scanning it reaches «Подключено». While on the qr_expired step, note whether the card-height jump (UI-5) is acceptable."
    why_human: "Token lifetime is set by Telegram (~30 s); host clock must be NTP-synced. UI-5 is a visual judgement only a live look settles."
  - test: "Criterion 4d — whole-session expiry: reach «код истёк», wait ≥ 270 s more, press «Обновить QR-код»"
    expected: "Error step «Сессия авторизации истекла. Начните заново.» with the «Начать заново» form"
    why_human: "Needs ≥ 5 minutes of real session time against a live Telethon client"
  - test: "Prohibitions (8 items, all `verification: none` in the plans) — confirm or reject the verifier's non-authoritative verdicts listed in the report section «Prohibitions»"
    expected: "Owner accepts each verdict (all eight judged HOLDING by the verifier) or names the one that does not hold"
    why_human: "Prohibitions carry no wired test enforcement; the verifier's reading is an LLM judgement and must not silently pass (ADR-550 D4)"
---

# Phase 13: Мастер подключения Telegram по QR на фрагментах — Verification Report

**Phase Goal:** мастер подключения работает на HTML-фрагментах с состоянием на сервере — без `setInterval`, без пяти JSON-контрактов и без ручного переключения `hidden`
**Verified:** 2026-09-21T17:40:19Z (HEAD `bff29f7a`)
**Status:** human_needed
**Re-verification:** No. This is the initial verification; no earlier VERIFICATION.md existed.

**Why `human_needed` and not `passed`:** every machine-checkable must-have holds, and there are no gaps. But criterion 4 (the live Telethon scenario) cannot be settled by any machine check. It routes to the owner, together with one visual finding (UI-5) and the eight prohibitions, which have no test enforcement. `passed` is not justifiable while criterion 4 is open, so FETCH-02 stays `[ ]` / `Pending`, which is correct.

## Goal Achievement

### Roadmap Success Criteria (read with the 13-06 chronicles)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| SC1 | Five `fetch()` gone with `setInterval` and manual `hidden`; routes answer HTML fragments. **Chronicle:** four routes, `complete` removed by D-01, poll moved GET → POST | ✓ VERIFIED | `grep -rn 'fetch(' app/templates/` = 0. Wizard page = anchor + include, with no `<script>`/`onclick`/`setInterval`. The only `hidden` in the step template is on three `type="hidden"` `session_id` inputs. No template in `accounts/` carries a `hidden` attribute, and no static JS touches connect steps. Live route table: GET page + POST `start-qr`, `qr-status`, `refresh-qr`, `verify-2fa`, and no `complete`. No `JSONResponse`/json in `app/pages/accounts.py`. Tests: `test_the_wizard_page_carries_no_client_script`, `test_the_complete_route_and_the_get_poll_are_gone` (GET poll → 405) |
| SC2 | Polling via `hx-trigger`, stopped by a response without it; each `every` fragment has a trigger-less pair. **Chronicle:** proven by a rule over rendered responses, not by the markup gate | ✓ VERIFIED | The poller exists only in the `waiting` branch (`form_wrapper(... trigger='every 3s')` targeting `#tg-connect-step`). The anchor has no trigger. Waiting poll → 204. `test_polling_stops_by_a_response_without_trigger` × 20 `POLLING_CASES`, closure rules `test_every_wizard_step_is_reached_by_a_polling_case` / `test_every_polling_fragment_has_a_terminal_pair`, and six `test_control_*` negative controls: all green in this run |
| SC3 | Server state, `session_id` in a hidden field, and the ownership check "preserved": a foreign `session_id` is rejected. **Chronicle:** the check was INTRODUCED, because it did not exist | ✓ VERIFIED | `QRAuthState.user_id` is mandatory with no default. `_owned()` guards `get_qr_status`/`refresh_qr`/`submit_2fa`/`complete_auth` before any mutation. Foreign-vs-unknown answers are compared byte for byte by `_same_answer` (status, body, headers minus `date`/`x-request-id`) on all three handlers, with victim-untouched assertions and the owner then reaching «Подключено»: `test_a_foreign_{poll,refresh,password}_is_answered_as_unknown_and_leaves_no_trace` green |
| SC4 | Live scenario: QR scan by phone, refresh of an expired code, 2FA entry (manual UAT) | ? HUMAN | Cannot be machine-verified: the Telegram server is not substitutable and the live browser needs owner consent. The four manual-only rows of `13-VALIDATION.md` appear as human_verification items 1–4. **Not passed, not failed.** |
| SC5 | Recorded plainly: there is no no-JS degradation **today either** (document record) | ✓ VERIFIED | Re-measured: `git merge-base HEAD master` = `344dc789`. `grep -c '<form'` on the base template prints `0` (exit 1). The chronicle sits beside SC5 in ROADMAP, and the «Критерий 5» section in `13-06-SUMMARY.md` carries the same command and output. Each wizard POST without HX-Request → 302 to the wizard page (`test_the_wizard_degrades_to_its_page_without_js`) |

### Plan Must-Have Truths (deduplicated against the SCs)

| # | Truth (plan) | Status | Evidence |
|---|--------------|--------|----------|
| 1 | start-qr (htmx) → 200, waiting fragment: data-URI QR, exactly one poller form, hidden `session_id`, no anchor id in the fragment (13-01) | ✓ VERIFIED | `accounts.py` `_waiting` → `_tg_step_markup(step="waiting")`. `test_the_waiting_fragment_polls_into_the_persistent_anchor`. The `_anchor_in_fragment` guard sits in the polling rule |
| 2 | qr-status in `waiting` → 204, empty body (13-01) | ✓ VERIFIED | `_unchanged` → `Response(status_code=204)`. POLLING_CASES waiting row |
| 3 | First poll that sees `success` calls the real `complete_auth`, saves one `MessengerAccount(tg_user, active)` and answers «Подключено» with no trigger and no HX-Location (13-01) | ✓ VERIFIED | Handler code. `test_the_wizard_walks_from_start_to_connected`, `test_a_second_poll_after_success_does_not_save_again` |
| 4 | All other outcomes → fragment without trigger, with an alert and «Начать заново»; texts moved verbatim (13-01) | ✓ VERIFIED | `TG_*_MESSAGE` constants. `test_start_refusals_are_fragments_with_verbatim_texts`, `test_polling_an_{unknown,errored}_session_*` |
| 5 | No-JS → 302 to the wizard; no login session → `/login` on both transports; no JSON (13-01) | ✓ VERIFIED | `respond(request, redirect=…)` on every exit. `test_the_wizard_degrades_to_its_page_without_js`, `test_the_wizard_without_a_session_goes_to_login` |
| 6 | Gate registries moved by a run (NOT_YET_CONVERTED_COUNT, MANUAL_FETCH_*, etc.) (13-01) | ✓ VERIFIED | `NOT_YET_CONVERTED_COUNT = 10`, `MANUAL_FETCH_PLACES = 0`, and 441 gate+records tests pass in this run. That the numbers came "from a run" is a process claim, recorded under Prohibitions |
| 7 | Poll in `needs_2fa` → password step with no trigger, `required`, empty value (13-02) | ✓ VERIFIED | `test_polling_needs_2fa_answers_the_password_step` |
| 8 | Wrong password → 422, «Неверный пароль 2FA.» at the field, no echo (13-02) | ✓ VERIFIED | `test_a_wrong_password_answers_422_at_the_field_without_echo` |
| 9 | Empty/missing password → 422 «Введите пароль» (13-02) | ✓ VERIFIED | `test_an_empty_password_answers_422_with_the_client_text` |
| 10 | Right password saves one account from the RESULT of `complete_auth`, not from `submit_2fa` (13-02) | ✓ VERIFIED | Handler: `submit_2fa` return value is discarded; `session_string = await complete_auth(...)`. `test_a_right_password_saves_one_account_from_complete_auth` |
| 11 | Two concurrent verify-2fa → one account; two concurrent polls after success → one account (13-02, D-01) | ✓ VERIFIED | The property holds: there is no `await` between the `_owned` check and `pop` in `complete_auth`, and the handlers reach it with no yield after `get_qr_status`. The unit rule `test_concurrent_completes_yield_one_session_string` passes and goes RED 3/3 on the reorder mutant (re-measured here). ⚠️ The route race tests do NOT carry this proof (WR-04, advisory) |
| 12 | Other Telethon errors on 2FA → error fragment, not a 500 (13-02) | ✓ VERIFIED | Generic `except Exception` logs `error_type` only. `test_a_telethon_failure_on_the_password_step_is_a_fragment` |
| 13 | verify-2fa no-JS: 302; field error → wizard page with 422; no session → `/login` (13-02) | ✓ VERIFIED | `respond_field_error(page=_page, …)`. `test_verify_2fa_degrades_and_requires_a_session` |
| 14 | `wait()` timeout → `qr_expired` with no error text and no `logger.error` traceback; session alive (13-03, D-03) | ✓ VERIFIED | `test_an_expired_qr_token_is_a_status_not_an_error` runs the REAL `QRLogin` with `expires_in=0.05` (landmine respected). ⚠️ The classification is too wide for post-event timeouts (WR-02, advisory) |
| 15 | Poll in `qr_expired` → «QR-код истёк…» step with a refresh form, no trigger (D-02) | ✓ VERIFIED | `test_polling_an_expired_code_offers_a_refresh`. Template branch has no poller |
| 16 | refresh-qr within TTL → new QR + poller, polling resumes (13-03) | ✓ VERIFIED | `test_refreshing_an_expired_code_resumes_polling`, `test_refresh_qr_recreates_only_an_expired_code` |
| 17 | Outdated session → «Сессия авторизации истекла…», `recreate` not called (13-03) | ✓ VERIFIED | `test_refreshing_an_outdated_session_says_it_expired`, `test_refresh_qr_does_not_revive_an_outdated_session` |
| 18 | `refresh_qr` recreates only from `qr_expired`; otherwise None and «Не удалось обновить QR…» (13-03) | ✓ VERIFIED | `test_refreshing_a_non_expired_code_is_refused`. ⚠️ Holds sequentially, not under concurrent owner refreshes (WR-01, advisory) |
| 19 | D-13: session layer changed only for D-01/D-03/D-04; `QR_SESSION_TTL = 300`, `_cleanup_expired_sessions`, `cleanup_qr_session`, `TelegramUserMessenger` untouched (13-03/13-04) | ✓ VERIFIED | `git diff -U0 344dc789 HEAD -- app/messengers/telegram_user.py`: hunks only in `QRAuthState`, the `start_qr_auth` signature, `_wait_for_qr`, `_owned`/`get_qr_status`, `refresh_qr`, `submit_2fa` and `complete_auth`. The hunk headed `_cleanup_expired_sessions` is the `start_qr_auth` signature line. Nothing past `complete_auth` |
| 20 | refresh-qr no-JS 302; no session → `/login`; no JSON (13-03) | ✓ VERIFIED | `test_refresh_degrades_and_requires_a_session` |
| 21 | Session bound to the user at start-qr; `user_id` mandatory (13-04) | ✓ VERIFIED | Dataclass field with no default. `start_qr_auth(..., user_id=user.id)`. `test_a_session_is_owned_by_the_user_who_started_it` |
| 22 | Under impersonation, bound to the SUBJECT; account saved on the subject (13-04) | ✓ VERIFIED | `test_the_wizard_binds_the_session_to_the_impersonated_subject` (asserts target ≠ admin, then `[a.user_id] == [target_id]`) |
| 23 | Foreign request does NOTHING to the owner's session, and the owner then reaches «Подключено» (13-04) | ✓ VERIFIED | The victim `is` object is still in `_qr_sessions`, status is unchanged, `disconnect`/`sign_in` are not awaited, and the owner then connects (three route tests + `test_a_foreign_{complete,refresh,password}_*` unit tests) |
| 24 | Owner check before any `pop`/`cancel`/`recreate`/`sign_in`; `complete_auth` only in `success` (13-04) | ✓ VERIFIED | Code order in all four functions. `test_complete_auth_takes_only_a_successful_session`, `test_a_foreign_complete_leaves_the_session_alone` |
| 25 | A late scan (past TTL, before cleanup) is `success`; own expired session → «истекла», never shown to a foreign caller (13-04) | ✓ VERIFIED | The `success` check precedes the TTL check, and `_owned` precedes both. `test_a_late_scan_is_still_a_success`. The foreign cases answer «не найдена» |
| 26 | Criterion-2 gate closed over template branches with negative controls; `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` a named zero; docstring chronicles (13-05) | ✓ VERIFIED | Rules and 6 controls green. Branches are parsed from the template text, so a new branch without a case reddens the rule |
| 27 | Chronicles beside SC1/2/3/5 and FETCH-02; criterion/requirement texts not rewritten; research untouched; FETCH-02 not marked (13-06) | ✓ VERIFIED | Chronicles read in ROADMAP/REQUIREMENTS. No removed diff line touches the criterion texts or the FETCH-02 text. `git diff 344dc789 HEAD -- .planning/research/` is empty. FETCH-02 is `[ ]` / `Pending`. `tests/test_planning` passes |

The three `verification: backstop` truths of 13-01/02/03 (live browser behaviour) are the content of SC4 and are routed with it. They do not count separately.

**Score:** 31/32 verified (5 SC + 27 plan truths). The one unverified item is SC4, routed to a human. 0 truths are present but behaviour-unverified: every behaviour-dependent truth (concurrency, ownership non-mutation, timeout classification) has a passing test that exercises it.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/templates/accounts/includes/tg_connect_step.html` | single source of step markup, six branches | ✓ VERIFIED | 137 lines; start/waiting/qr_expired/password/connected/error. Included by the page and rendered by `_tg_step_markup` |
| `app/templates/accounts/connect_tg_user.html` | permanent anchor `#tg-connect-step` + include, no script | ✓ VERIFIED | 27 lines; anchor on `.connect-shell` |
| `app/pages/accounts.py` | four handlers on `respond()`/`respond_field_error()`, `_tg_step_markup`, `_save_tg_account`, constants | ✓ VERIFIED | Lines 211-616 |
| `app/messengers/telegram_user.py` | `user_id`, `_owned`, timeout branch, refresh guards | ✓ VERIFIED | Wired: imported by `accounts.py` (the only consumer) |
| `tests/test_routes/test_tg_user_auth.py` | tracer path, POLLING_CASES, race, foreign, controls | ✓ VERIFIED | 56 tests pass |
| `tests/test_messengers/test_telegram_user.py` | real-QRLogin timeout, ownership rules, complete race | ✓ VERIFIED | 34 tests pass |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| start form (`hx-target=#tg-connect-step`) | `accounts_connect_tg_user_start_qr` → `start_qr_auth(user_id=user.id)` | `form_wrapper` action | ✓ WIRED |
| poller form inside the waiting fragment | `accounts_connect_tg_user_qr_status` | `hx-post` every 3s, hidden `session_id` | ✓ WIRED (not on the anchor, per the D-05 correction) |
| qr-status `success` | `complete_auth` → `_save_tg_account` | direct call | ✓ WIRED |
| password step | `verify_2fa` → `submit_2fa` → `complete_auth` → `_save_tg_account` | `form_wrapper` | ✓ WIRED |
| `respond_field_error` | 422 swap of the password step | htmx response-handling config | ✓ WIRED (test asserts 422 fragment content) |
| `QRLogin.wait()` TimeoutError | `_wait_for_qr` → `qr_expired` → poll → refresh step | status field | ✓ WIRED |
| «Обновить QR-код» | `refresh_qr` (`recreate` + new wait task) → waiting step with poller | `form_wrapper` | ✓ WIRED |
| `get_user_from_cookie` → `user.id` | `QRAuthState.user_id` → `_owned` in every handler | parameter | ✓ WIRED |
| `POLLING_CASES` ↔ template branches | closure rule | template text parse | ✓ WIRED |
| SC3 chronicle ↔ FETCH-02 chronicle | cross-reference | both present | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| waiting step `qr_code` | login URL | `start_qr_auth` / `refresh_qr` → `qr_login.url` → `_generate_qr_base64` | yes (Telethon) | ✓ FLOWING |
| step selection | `status` | `_qr_sessions[...]` written by `_wait_for_qr` / `submit_2fa` | yes | ✓ FLOWING |
| saved account | `session_string` | `complete_auth` → `client.session.save()` | yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Wizard route + session-layer modules | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q -p no:randomly` | 90 passed | ✓ PASS |
| Gates + records | the 10 gate files from VALIDATION's gate command + `tests/test_components.py` + `tests/test_planning` | 441 passed (2:37) | ✓ PASS |
| Live route table | `app.routes` filtered on `tg_user` | GET page; POST start-qr/qr-status/refresh-qr/verify-2fa; no complete | ✓ PASS |
| Reorder mutant vs the race rules (WR-04) | scratch plugin, 3 runs | unit RED 3/3; 2FA route GREEN 3/3; poll route GREEN 5/6; control 3 passed | ✓ measured (see advisory WR-04) |
| SC5 base measurement | `git show $(git merge-base HEAD master):…connect_tg_user.html \| grep -c '<form'` | `0` | ✓ PASS |

I did not re-run the full suite. I rely on the orchestrator's measurement (3511 passed at `e5c1288c`); since then only `.planning/` files changed, and `tests/test_planning` was re-run green above.

### Probe Execution

None declared. The phase plans name no `scripts/*/tests/probe-*.sh`. Step 7c: SKIPPED.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FETCH-02 | 13-01…13-06 (all declare it) | QR wizard on HTML fragments: `hx-trigger` polling, stop by a trigger-less response, server state, hidden `session_id`, server ownership check (chronicle: introduced, not preserved) | ✓ SATISFIED (machine-checkable part) | SC1–SC3, truths 1–26. The flag stays `[ ]`/`Pending` until `phase.complete` follows a `passed` verdict, which waits on the criterion-4 UAT |

REQUIREMENTS.md maps only FETCH-02 to Phase 13, so no requirement is orphaned.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/*` phase files | — | TBD/FIXME/XXX | none found | — |
| `app/*` phase files | — | TODO/HACK/PLACEHOLDER | none found | — |
| `app/static/css/app.css` | 1925-1929 | stale comment + dead `.connect-step[hidden]` rule | ℹ️ Info | UI-14; not a phase-modified file |

### Prohibitions (all `verification: none` → flagged; non-authoritative LLM-judge verdicts)

| # | Plan | Prohibition | Verifier's verdict (non-authoritative) |
|---|------|-------------|----------------------------------------|
| P1 | 13-01 | `session_id` never in the URL, JS variables or browser storage; hidden field only (D-06) | HOLDS. There is no script on the page; `session_id` appears only in `type="hidden"` inputs of POST forms; the GET poll is gone (405) |
| P2 | 13-01 | No new script, browser timer or auto-redirect after «Подключено» (D-07, D-12) | HOLDS. `connected` branch = badge + text + `link_button` only; the page has no `<script>` |
| P3 | 13-01 | Inventory numbers set by a run of the reddened rule, not by mental arithmetic | HOLDS by the SUMMARY disclosures (every registry move is recorded with its red run). This is a process claim the code cannot show |
| P4 | 13-02 | 2FA password not echoed, not in foreign attributes, storage or log | HOLDS. The field renders `value=""` (test). The handler never puts the password in the context. The log carries `error_type` only. IN-01 echoes Telethon text, not the password |
| P5 | 13-03 | An expired code is not refreshed automatically (D-02) | HOLDS. The `qr_expired` branch has no poller; the POLLING_CASES row asserts no trigger |
| P6 | 13-04 | A foreign answer does not differ from an unknown one in text, code or markup | HOLDS. `_same_answer` compares byte for byte on three handlers (headers exclude only `date`/`x-request-id`) |
| P7 | 13-05 | A gate rule is not deleted for green; it is rewritten as a named zero or on synthetic input | HOLDS. The exempt list is a declared zero with rewritten non-vacuity rules, and there are six controls |
| P8 | 13-06 | Criterion and requirement texts are not rewritten; chronicles sit beside them | HOLDS. No removed diff line touches the SC or FETCH-02 texts |

These are listed as one human_verification item so they do not pass silently.

## Findings Disposition (REVIEW.md + UI-REVIEW.md)

Each finding has exactly one disposition. **Split: 0 gaps · 21 advisory · 1 human_verification · 2 deferred (owner) = 24.**

| Finding | Source | Disposition | One-line reason |
|---------|--------|-------------|-----------------|
| WR-01 | REVIEW | Advisory | Real owner-only concurrency hole in the refresh guard; affects neither criterion 2/3 nor the D-02 no-auto-refresh prohibition |
| WR-02 | REVIEW | Advisory | Confirmed in Telethon source; rare post-scan DC-migration timeout mislabelled «истёк»; the main path is intact |
| WR-03 | REVIEW | Advisory | Pop-before-commit is pre-existing (old `/complete` did the same); failure-path hardening |
| WR-04 | REVIEW | Advisory | Re-measured: the route race tests don't discriminate the reorder mutant; the property holds via code + unit rule (truth 11 VERIFIED); the plans' "route tests prove it" claim is overstated |
| IN-01 | REVIEW | Advisory | Broad except echoes Telethon internals at the field; not a password leak |
| IN-02 | REVIEW | Advisory | Layer asymmetry; the only caller enforces `needs_2fa` |
| IN-03 | REVIEW | Deferred → «владелец» | CONTEXT §Deferred names it separate work; D-13 bound; pre-existing |
| UI-1 | UI-REVIEW | Advisory | Confirmed regression (0px field/button); visual, no SC defeated. Recommended fix before close |
| UI-2 | UI-REVIEW | Advisory | Confirmed regression (left-aligned actions); visual only |
| UI-3 | UI-REVIEW | Advisory | Confirmed regression (lost «Загрузка...»); disabled button + busy dot remain |
| UI-4 | UI-REVIEW | Advisory | Pre-existing copy placement |
| UI-5 | UI-REVIEW | Human verification | Card-height jump is a visual judgement; folded into UAT item 3 (`qr_expired` is on screen there) |
| UI-6 | UI-REVIEW | Advisory | Colour consistency polish |
| UI-7 | UI-REVIEW | Advisory | Typography polish |
| UI-8 | UI-REVIEW | Advisory | Minor doubled gap from the zero-height poller |
| UI-9 | UI-REVIEW | Advisory | a11y; the MAX wizard has the same gap, so not a phase regression |
| UI-10 | UI-REVIEW | Advisory | No autofocus; the pre-phase script had none either |
| UI-11 | UI-REVIEW | Advisory | Retry is pointless for a config refusal; text bound by D-09 |
| UI-12 | UI-REVIEW | Advisory | Deliberate per D-04; no action recommended |
| UI-13 | UI-REVIEW | Advisory | Consistent with MAX; enhancement |
| UI-14 | UI-REVIEW | Advisory | Checked for SC1: nothing toggles `hidden`; the CSS rule/comment is dead residue |
| UI-15 | UI-REVIEW | Advisory | Pre-existing; the header link is an exit |
| UI-16 | UI-REVIEW | Advisory | Carried verbatim; `current-password` suggested |
| UI-17 | UI-REVIEW | Deferred → «владелец» | CONTEXT §Landmines: moved verbatim, «решение о нём — не предмет фазы» |

Locked decisions D-02, D-07, D-08, D-09, D-11 and D-13 were treated as intended behaviour, not findings.

## Human Verification Required

### 1. Criterion 4a: scan without 2FA

**Test:** open `/accounts/connect/tg_user`, press «Начать подключение», then scan with the phone (Настройки → Устройства → Подключить устройство).
**Expected:** «Подключено» appears by itself; one account is created; the uvicorn log shows no further `POST …/qr-status` afterwards.
**Why human:** needs a real Telegram account; the server can't be substituted; the live browser needs owner consent.

### 2. Criterion 4b: 2FA account

**Test:** enter a wrong password, then the right one.
**Expected:** «Неверный пароль 2FA.» appears at the field with the field empty, then «Подключено» with one account.
**Why human:** needs a live Telethon session with a 2FA password.

### 3. Criterion 4c: expired code + UI-5

**Test:** don't scan for ≥ ~30 s, then press «Обновить QR-код» and scan the new code.
**Expected:** the «QR-код истёк» step appears by itself; the refresh brings a new QR and polling resumes; the scan connects. Also judge whether the card-height jump on this step is acceptable (UI-5).
**Why human:** Telegram sets the token lifetime; the visual judgement needs a live look.

### 4. Criterion 4d: whole-session expiry

**Test:** stay on «код истёк» for ≥ 270 s, then press refresh.
**Expected:** «Сессия авторизации истекла. Начните заново.»
**Why human:** needs real elapsed session time.

### 5. Prohibitions P1–P8

**Test:** review the verdict table above.
**Expected:** each verdict is accepted, or the one that fails is named.
**Why human:** there is no wired enforcement, so the verifier's reading is not authoritative.

## Gaps Summary

There are none. The phase goal is achieved in the codebase:

- Four wizard routes answer HTML step fragments through `respond()`, from one include behind a permanent anchor.
- `complete` is removed, and the poll is a POST that saves the account itself.
- There is no script, `setInterval`, `fetch(`, JSON or `hidden` toggling left.
- Polling stops by a trigger-less response, proven by a closed rule over rendered responses with negative controls.
- The ownership check exists and is proven non-mutating and indistinguishable from an unknown session.

What remains is a human item, not a gap: the live criterion-4 UAT, plus one visual judgement (UI-5) and confirmation of the eight prohibition verdicts.

Of the 21 advisories, the ones most worth acting on before or with the UAT:

- **UI-1/UI-2/UI-3:** visual regressions this phase introduced. All three are cheap CSS or markup fixes.
- **WR-04:** strengthen the two route race tests so they actually discriminate.
- **WR-02:** narrow the timeout classification.

None of them blocks the phase goal. The owner decides whether any becomes a gap-closure plan. The `--gaps` flow reads this file, so each item is here with its reason.

---

_Verified: 2026-09-21T17:40:19Z_
_Verifier: Claude (gsd-verifier)_

---

## Канонизация вердикта 2026-09-21: `human_needed` → `passed`

Вердикт переведён НЕ пересчётом истин и НЕ повторным прогоном верификатора: счёт остался
**31/32**, и ни одна истина заново не мерялась. Переведены ровно те причины, которые отчёт выше
называл своими словами, — **живой сценарий критерия 4, визуальное суждение UI-5 и восемь
запретов P1–P8**. Все три — пункты ручного обхода, решений владельца вне обхода отчёт не ждал:
гапов ноль, 21 рекомендация помечена как не блокирующая цель.

**Что закрыло причину.** `13-UAT.md` 2026-09-21: `status: complete`, пять ответов `pass`, ноль
расхождений, ноль гапов, **все пять таблиц отметок заполнены**. Правило
`tests/test_planning/test_the_walkthrough_cannot_self_certify.py` зелено при сошедшихся трёх счётах
(`declared=5`, `sections=5`, `tables=5`, `filled=5`); каталог `tests/test_planning/` — 44 passed.
Обход шёл на живом стенде с реальными аккаунтами Telegram (Александр, Chrome 152 / macOS 15).

⚠️ **РАЗНИЦА ДВУХ ФОРМ ЗАКРЫТИЯ, НАЗВАННАЯ ЗДЕСЬ, А НЕ ТОЛЬКО В ОБХОДЕ.**

| Пункты | Чем закрыты |
|---|---|
| 3 (UI-5), 5 (P1–P8) | ДОСЛОВНЫМИ словами владельца: «по высоте меня все устраивает»; `pass` на явный список P1–P8, отвергнутых нет |
| 1, 2, 4 и шаги 3.1, 3.3, 3.4 | ПОДТВЕРЖДЕНИЕМ личного наблюдения владельца на прямой вопрос приёмки: «все было на живом стенде с реальными аккаунтами telegram». Дословного описания признака нет — в клетках стоит подтверждение наблюдения, а не его описание |

Без дословного значения осталась, в частности, обязательная клетка 1.4 (нет новых
`POST …/qr-status` в журнале uvicorn после «Подключено»); названо поимённо в ключе `unrecorded`
шапки обхода.

**Свежесть вердикта сверена ДО перевода.** `git diff --stat bff29f7a..HEAD` по списку
`covered_files` пуст — ни один покрытый вход не менялся с момента вердикта; `verification.status`
до перевода читался `human_needed`, а не `stale`. Отпечаток не пересчитывался.

**Что этой канонизацией НЕ закрыто и закрыто быть не могло:** 21 рекомендация раздела
«Findings Disposition» (в том числе визуальные регрессии фазы UI-1/UI-2/UI-3, WR-04, WR-02) и две
отсрочки владельца (IN-03, UI-17) остаются в прежнем виде; перевод любой из них в гап — решение
владельца, отдельное от вердикта.

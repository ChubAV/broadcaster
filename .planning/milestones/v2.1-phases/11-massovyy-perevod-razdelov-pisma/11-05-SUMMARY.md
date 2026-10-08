---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 05
subsystem: ui
tags: [htmx, jinja2, fastapi, respond, oob, beforeend, form-wrapper, tdd]

requires:
  - phase: 11-01
    provides: "respond() fragment branch for the editor, sched_card_article/sched_card_panel_text macros, GATE-02 pair registry"
  - phase: 11-02
    provides: "id_in_column and the «проверка первым использованием» rule used by the create handler"
  - phase: 11-04
    provides: "form_wrapper as the third schedules-section caller; the parametric-target registry shape"
provides:
  - "schedules_create on the response layer: a new card for beforeend insertion, «было ноль» by HX-Location"
  - "app/templates/ads/partials/sched_create_response.html: full card (article + panel) + OOB counter rule + OOB #ad-summary"
  - "permanent container id sched-list in ads/form.html; the create form on form_wrapper with a CONDITIONAL target"
  - "_PairCase.resolve_after: landing substitutions resolved AFTER the request, for creating actions"
  - "both legacy editor redirect helpers removed — the schedules module builds no redirect of its own"
affects: [11-06, 11-20, schedules, ads-editor, gate-02]

actuals:
  tokens: 20152
  tasks: 2
  commits: 4
plan_head_before: 6b453313f4df1f8121333517d611203863ad015e

tech-stack:
  added: []
  patterns:
    - "Creating action: the branch «was zero» is decided by a count BEFORE the response layer, never by reading the htmx flag"
    - "Conditional swap target: a target is printed only where the container exists — the runtime resolves targets before sending"
    - "Pair case for a creating action: landing ids are read back from the database after the request, not predicted"

key-files:
  created:
    - app/templates/ads/partials/sched_create_response.html
  modified:
    - app/pages/schedules.py
    - app/templates/ads/form.html
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_pages/test_notices_channel.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "The «was zero» branch is decided by _ad_schedule_count AFTER the write, before the response layer: the question is not «how to answer» but «does the insertion container exist on screen», and the htmx flag must stay read in exactly one place"
  - "The create form's target is CONDITIONAL: the vendored htmx 2.0.10 resolves the target BEFORE sending and, not finding it, raises htmx:targetError and returns — an unconditional target would make «+ ДОБАВИТЬ ПЕРВОЕ» send nothing at all"
  - "Ruler and summary take ONE value (editor.schedules_count); _ad_schedule_count serves only the transport branch"
  - "Pair cases for a creating action resolve their landing ids from the database after the request instead of predicting autoincrement"

patterns-established:
  - "Gate numbers moved only after the red run, each chronicle quoting the failing text verbatim"
  - "A superseded docstring claim is marked with what refuted it, never deleted (D-30/D-32)"

requirements-completed: [FORM-07, FORM-03]

coverage:
  - id: D1
    description: "Create over htmx with a non-empty list answers 200; the top node is the new expanded card #sched-N with its panel; no <!DOCTYPE; OOB innerHTML:#sched-count and #ad-summary; the ruler equals the full page's after F5"
    requirement: FORM-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_create_over_htmx_appends_the_card_to_the_list"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_create-создание расписания — в непустой список]"
        status: pass
    human_judgment: false
  - id: D2
    description: "The first schedule answers 204 with HX-Location /ads/{ad}/edit?sched=N#sched-N and an empty body; the degraded half lands on the same address character-for-character"
    requirement: FORM-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_the_first_schedule_over_htmx_lands_by_a_location_header"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_create-создание расписания — было ноль]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ownership outcomes: a foreign ad lands on /schedules, an unavailable account on /ads/{ad}/edit?notice=schedule_account_gone — identical on both transports"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_create-создание расписания — объявление чужое]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_create-создание расписания — аккаунт недоступен]"
        status: pass
    human_judgment: false
  - id: D4
    description: "The create form declares its target only where the container exists: no hx-target on an empty editor, hx-target=#sched-list with hx-swap=beforeend on a non-empty one"
    requirement: FORM-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_the_create_form_targets_the_list_only_when_the_list_exists"
        status: pass
    human_judgment: false
  - id: D5
    description: "Gate numbers set by red runs: NOT_YET_CONVERTED_COUNT 23, FRAGMENT_RESPONSE_HANDLERS_DECLARED 6, HX_HEADER_WRITES unmoved at 2, plus five markup/records constants"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_hx_location_destinations.py tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_notices_channel.py -q"
        status: pass
    human_judgment: false
  - id: D6
    description: "In a browser, with 8+ schedules and the page scrolled to the bottom, creating a schedule does not reset scroll; the new card appears expanded at the END of the list; ruler and summary show the new number; on an ad with no schedules the first create navigates to the editor with the card expanded"
    requirement: FORM-07
    verification: []
    human_judgment: true
    rationale: "The ASGI transport executes no htmx runtime: insertion position, scroll preservation and the absence of a targetError are observable only in a browser — phase UAT, criterion 3"

# Metrics
duration: 1h 19m
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 05: Schedule creation inserted into the list Summary

**`schedules_create` goes through `respond()`: over htmx a non-empty list receives the new expanded card for `beforeend` insertion into the permanent `#sched-list` container plus OOB counter and summary from one value, while «было ноль» lands by `HX-Location`; both legacy editor redirect helpers are gone.**

## Performance

- **Duration:** 1h 19m (measured from the previous plan's last commit `6b45331` 03:47:28Z to the metadata commit; implementation ~38 min, full suite 39:13)
- **Started:** 2026-09-16T03:47:28Z
- **Completed:** 2026-09-16T05:07Z
- **Tasks:** 2
- **Files modified:** 9 (1 created, 8 modified)

## Accomplishments

- Creating a schedule in the editor with a non-empty list answers htmx with 200 and a body whose first node is the new card, **expanded**, with its confirmation panel alongside — both belong to the list container on the full page, so a response carrying the article alone would have produced a card whose delete button opens nothing. No `<!DOCTYPE`, container not repainted, neighbouring cards untouched.
- The counter ruler and `#ad-summary` are refreshed from **one** value (`editor.schedules_count`); the ruler's OOB content was compared against the full page after F5 and is identical.
- The first schedule («было ноль») answers 204 + `HX-Location` on `/ads/{ad}/edit?sched=N#sched-N` — the same address the degraded path receives as a 302, asserted character-for-character by the pair module. No second mechanism for drawing the empty/non-empty state was introduced.
- `ads/form.html`: the list container gained the permanent `id="sched-list"`, and the create form moved onto `form_wrapper` with `swap='beforeend'`.
- Both legacy editor redirect helpers were deleted (no callers left); the schedules module now builds no redirect of its own on this handler. `NOTICE_WRITE_PLACES` fell 6 → 5 as a result, and the notices-channel gate's documented boundary — which named that helper as the single place assembling an address by substitution — was updated: **no such place remains in the product**.

## Task Commits

1. **Task 1: create on the response layer** — RED `aa5fb87` (test), GREEN `2135c10` (feat)
2. **Task 2: permanent container and the create form on the wrapper** — `dfcade8` (feat)

⚠️ **Two counts, stated apart, because they answer different questions.** **Task commits: 3** (the three above). **Ledger range: `git rev-list --count 6b45331..HEAD` = 4**, and `actuals.commits` carries that four — the range also contains the metadata commit that brings this file, and `/gsd-verify-work` re-measures it with the same instrument. Quoting the task-commit total in a field the verifier measures as a range is the mismatch plan 11-04 already paid for; the invariant is written here instead of a number that goes stale the moment this file is committed.

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `aa5fb87` | `2135c10` | — (not needed) |
| 2 | n/a (`type="auto"`, no `tdd` attribute) | `dfcade8` | — |

RED evidence was verified with `gsd-tools check tdd-red-evidence`, verdict **`RED_EVIDENCE_OK`** (`reason: target_test_failed`, `exit_code: 1`, `tests: 2`, `pass: 0`, `fail: 2`) on **both** target tests. The record was built from `--junitxml` of that same run converted to TAP lines.

- Target 1 — `test_schedule_create_over_htmx_appends_the_card_to_the_list`: `AssertionError: слою письма приехал целый документ / assert '<!DOCTYPE' not in '\n\n<!DOCTY...dy>\n</html>'`. Causal literal `<!DOCTYPE` **verified present** in the tree at `app/templates/base.html:14` (and `auth_base.html:13`).
- Target 2 — `test_the_first_schedule_over_htmx_lands_by_a_location_header`: `AssertionError: 200 / assert 200 == 204`.
- In the same RED state the pair module failed on **exactly** the four new `schedules_create` cases (`4 failed, 14 passed`), the eleven pre-existing cases staying green.

Exit-code inversion was **not** used anywhere: every RED claim above names the failing target, the `N failed` summary line, and a causal literal checked against the tree.

## Gate numbers — verbatim texts of the red rules that set them

| Constant | Move | Verbatim text of the failing rule |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 24 → 23 | «число непереведённых обработчиков стало 23, а в файле записано 24. ЕСЛИ ЧИСЛО УПАЛО — ЭТО ПРОГРЕСС ВЕХИ, а не поломка» / `assert 23 == 24` |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 5 → 6 | «обработчиков, отдающих фрагмент, найдено 6, объявлено 5» / `assert 6 == 5` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 41 → 46 | «вызовов слоя ответа БЕЗ фрагмента найдено 46, а объявлено 41» |
| `OOB_BLOCKS` | 15 → 17 | «внеполосных блоков найдено 17, объявлено 15» |
| `NOTICE_WRITE_PLACES` | 6 → 5 | «мест записи в страничном слое 5, а объявлено 6» |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 4 → 5 | «блоков вызова макроса-обёртки разобрано 5, объявлено 4» |
| `MACRO_DEFINITION_SITES_CALLERS_DECLARED` | 13 → 14 | «за перечнем мест определения макросов спрятано вызывающих 14, объявлено 13» |
| `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` | 3 → 4 | «за перечнем параметрических целей подмены спрятано вызывающих 4, объявлено 3» |
| `POST_PAIR_CASES_DECLARED` | 11 → 15 | four new create cases |

Constants that did **not** move, checked deliberately: `HX_HEADER_WRITES = 2` (success criterion 3), `HX_POST_PLACES = 3` and `HX_TARGETS = 1` (both count *places*, and the wrapper's single place already counted), `CLIENT_STATE_NODES = 24`, `PARAMETRIC_SWAP_TARGETS_DECLARED = 1` (the registry is keyed by file), `FRAGMENT_ROUTES_DECLARED = 11` (counts routes with no degraded path; this one has one).

## Decisions Made

- **The «was zero» branch is decided before the response layer.** `_ad_schedule_count` runs after the write and its result selects the transport, because the question it answers is not «how do I answer» but «does the insertion container exist on this screen». Reading the htmx flag in the handler instead would have created a second reading of that flag in the application, and its single reading is a milestone-level property. The named cost: one counting query on the degraded path.
- **Ruler and summary take one value.** Both areas render from `editor.schedules_count`; `_ad_schedule_count` is used only for the branch. Two independent counts would have diverged silently — gap `G-10-6` of walkthrough 3, already paid for once on the deletion ruler.
- **Pair cases for a creating action resolve their landing after the request.** A created row's id does not exist before the request, and predicting it as «seeded + 1» would assert the driver's autoincrement rather than the handler's behaviour. `_PairCase.resolve_after` reads the row back, scoped by the ad from the form body, so the two halves cannot see each other's rows.
- `_editor_url` and `_ad_schedule_count` docstrings received new generations rather than edits; the refuted claims are marked with what refuted them (D-30/D-32).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The create form's swap target had to be conditional, not unconditional**
- **Found during:** Task 2
- **Issue:** The plan specified `form_wrapper(action='/schedules/new', target='#sched-list', swap='beforeend')` flatly. The container lives inside the «расписания есть» condition, so on an empty editor it does not exist. I measured the vendored runtime (`app/static/js/htmx.min.js`, htmx 2.0.10): `issueAjaxRequest` resolves the target **before** sending — `const u = i.targetOverride || ue(Se(r)); if (u == null || u == be) { fe(r,"htmx:targetError",...); return }` — so it raises `htmx:targetError` and **returns without sending the request**. An unconditional target would have made the «+ ДОБАВИТЬ ПЕРВОЕ» button do nothing at all with JavaScript on, silently: no status, no body, nothing but a console line. The plan's own `key_links` anticipated the targetError but its action text did not carry the consequence through.
- **Fix:** `target=('#sched-list' if editor.schedules else none)`. With no target the wrapper prints `hx-swap="none"`, the request is sent, and the handler lands the person by `HX-Location` — exactly the D-05 branch. The idiom is the project's own: the conditional-parameter form used to close walkthrough divergence DIV-09-01.
- **Files modified:** `app/templates/ads/form.html`
- **Verification:** `test_the_create_form_targets_the_list_only_when_the_list_exists`; the plan's acceptance greps still hold (`swap='beforeend'` = 1, `data-sched-list id="sched-list"` = 1, `hx-push-url` = 0).
- **Committed in:** `dfcade8`

**2. [Rule 2 - Missing critical] A test for the conditional target**
- **Found during:** Task 2
- **Issue:** Nothing in the suite could catch deviation 1. The ASGI transport executes no JavaScript, so a form that never sends its request still leaves every request-level test green; the markup gates are blind to it too, because the target is parametric and printed by the macro.
- **Fix:** Added `test_the_create_form_targets_the_list_only_when_the_list_exists`, asserting the rendered form tag for both states (no `hx-target` + `hx-swap="none"` when empty; `hx-target="#sched-list"` + `hx-swap="beforeend"` when not).
- **Files modified:** `tests/test_pages/test_editor_schedules.py`
- **Committed in:** `dfcade8`

**3. [Rule 1 - Bug] `AD_SUMMARY_RULE_USERS` was stale and silently unenforceable**
- **Found during:** Task 1
- **Issue:** My response template includes `ads/includes/summary.html`, so it joins that registry. Measuring the tree showed the registry declared three consumers while **five** exist: plan 11-01's `ads/partials/sched_card_response.html` includes the summary source and was never declared. The rule asserts that each *declared* consumer includes the source, not that all consumers are declared, so the omission was invisible by construction.
- **Fix:** Declared both missing consumers with a note naming the measurement and why the rule stayed green.
- **Files modified:** `tests/test_pages/test_editor_schedules.py`
- **Committed in:** `2135c10`

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing-critical test).
**Impact on plan:** No scope change. Deviation 1 prevented a silently dead button on the empty-editor path; deviations 2 and 3 close the blind spots that let it and a stale registry go unnoticed.

## Issues Encountered

- The first RED run **errored** instead of failing: my two tests requested only `htmx_client`, which does not register the user the `owner` fixture looks up. The fixtures compose deliberately in this file (both `authed_client` and `htmx_client` return the same client object). Fixed the signatures and re-ran; an error is not RED, so no evidence was taken from that run.
- The RED evidence record was rejected once as `invalid_record`: the checker reads `command` / `exitCode` / `targetTest` / `output`-as-TAP, not the snake_case shape I first wrote. Rebuilt from `--junitxml` of the same run.

## Verification

- Task 1 verify set (`test_editor_schedules`, `test_htmx_post_pairs`, `test_htmx_gates`, `test_hx_location_destinations`, `test_htmx_markup_gates`): **226 passed**.
- Task 2 verify set (`test_htmx_markup_gates`, `test_components`, `test_editor_schedules`, `test_ads_editor`): **287 passed**. Acceptance `-k "counter_rule or schedule_counter or swap_target"`: 10 passed.
- Adjacent acceptance suites (`test_schedule_ownership`, `test_schedule_creation_path_exists`, `test_routes/test_schedules_profile_timezone`): 17 passed. Notices channel: 47 passed. Collateral on the `form.html` edit (`test_ads_form_security`, `test_walkthrough_anchors`, `test_responsive_markup`): 159 passed.
- **Full suite `uv run pytest tests/ -q`: 3293 passed, 1 FAILED, 39:13.** The suite is **not** fully green and is not reported as such. The single failure is `tests/test_pages/test_admin_panel.py::test_the_overview_error_number_matches_the_users_own_dashboard` — the known pre-existing midnight window (`WINDOWS.md` windows 14, 27, 79, 85: the admin overview counts a rolling 24h window while the dashboard counts the reader's calendar day). The run spanned 04:25–05:05 UTC, inside the 00:00–05:00 window where it fires. It is outside this phase's subject; `app/pages/admin.py`, `app/pages/dashboard.py` and `app/application/analytics/send_analytics.py` were not touched. No new `WINDOWS.md` entry was appended — the defect is already open as window 85, and a duplicate would corrupt the ledger.
- `uv run python -m compileall -q app main.py tests`: clean. `graphify update .`: graph refreshed (20406 nodes; `graphify-out/` is git-ignored).
- Nothing in the verify blocks was left unrun. The `<human-check>` for criterion 3 is deferred to the end-of-phase UAT by `human_verify_mode: end-of-phase`.

## Known Stubs

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 11-06 (ads module and its window 51) can proceed: the schedules section is fully on the response layer, and no caller of the old redirect helpers remains anywhere in the module.
- `REQUIREMENTS.md` was **deliberately not** flipped: FORM-03 and FORM-07 stay `Pending` because phase 11 verification has not run, and `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` enforces that.
- The `#sched-list` container and the conditional-target idiom are available to any later plan that needs list insertion.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

## Self-Check: PASSED

- **Files — all FOUND on disk:** `app/templates/ads/partials/sched_create_response.html` (created); `app/pages/schedules.py`, `app/templates/ads/form.html`, `tests/test_pages/test_editor_schedules.py`, `tests/test_pages/test_htmx_post_pairs.py`, `tests/test_pages/test_htmx_gates.py`, `tests/test_pages/test_hx_location_destinations.py`, `tests/test_pages/test_notices_channel.py`, `tests/test_templates/test_htmx_markup_gates.py` (modified); this SUMMARY.
- **Commits — all FOUND:** `aa5fb87` (RED), `2135c10` (GREEN task 1), `dfcade8` (task 2), plus the metadata commit carrying this file (its hash is not quoted here: this section is amended into that very commit, so any hash written would be the pre-amend one).
- **Records gate:** `uv run pytest tests/test_planning/ -q` → 44 passed, run AFTER the ROADMAP mark, the prose count and every STATE edit.
- **Working tree:** clean apart from two untracked files that predate this plan (`.planning/milestone.lock`, `.planning/state.json`) and are not mine to commit.

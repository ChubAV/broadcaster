---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 01
subsystem: ui
tags: [htmx, jinja2, fastapi, respond, oob, gate-02, tdd]

requires:
  - phase: 10-podtverzhdenie-udaleniya
    provides: "respond() fragment/location branches, schedules_delete fragment pattern, CONFIRMED_DELETE_ROUTES pair traversal, _Arranged"
  - phase: 09
    provides: "form_wrapper macro, G-11 resolution form for parametric swap targets, long-lived region idiom (D-12)"
provides:
  - "schedules_update on the response layer: htmx fragment of its own expanded card #sched-N, HX-Location on off-screen outcomes"
  - "sched_card_article and sched_card_panel_text macros; sched_card composed from them"
  - "ads/partials/sched_card_response.html: card + OOB #ad-summary + innerHTML:#sched-del-N-text"
  - "permanent id {{ id }}-text on the confirmation panel text paragraph (components/modal.html)"
  - "tests/test_pages/test_htmx_post_pairs.py: GATE-02 pair registry, declared count, closure over converted handlers, negative control"
affects: [11-03, 11-05, 11-15, 11-20, schedules, ads-editor, gate-02]

actuals:
  tokens: 16706
  tasks: 2
  commits: 4
plan_head_before: c1d1086a32dac63a6348423da19b2eab8dbd4e8d

tech-stack:
  added: []
  patterns:
    - "Pair registry + closure: a handler that calls respond() must have a _PairCase or a CONFIRMED_DELETE_ROUTES entry"
    - "Card split: article macro is the swap target; panel stays outside; panel text is one macro value used in header, panel body and OOB node"
    - "Long-lived panel text replaced by content via permanent id, never the Alpine-stateful panel root"

key-files:
  created:
    - app/templates/ads/partials/sched_card_response.html
    - tests/test_pages/test_htmx_post_pairs.py
  modified:
    - app/pages/schedules.py
    - app/templates/ads/includes/sched_card.html
    - app/templates/components/modal.html
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "schedules_update over htmx returns only the card article plus OOB #ad-summary and innerHTML:#sched-del-N-text; the panel root never rides in the body or becomes a target"
  - "GATE-02 closure counts a converted handler as covered by POST_PAIR_CASES or CONFIRMED_DELETE_ROUTES — Phase 10 confirm-delete pairs are not duplicated"
  - "_editor_context is imported at module level into app/pages/schedules.py: measured no import cycle (ads.py does not import the schedules module)"

patterns-established:
  - "Pair case: frozen _PairCase(key, name, identity, arrange, landing, transport, fragment_mark); both halves on fresh state; htmx half follow_redirects=True"
  - "Gate numbers moved only after the red run, chronicle quotes the failing text verbatim and names the handler in words"

requirements-completed: [FORM-03, GATE-02]

coverage:
  - id: D1
    description: "schedules_update answers htmx with 200 and its own expanded card #sched-N first, no <!DOCTYPE, no sched-del-N root; degraded path unchanged 302"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_edit_over_htmx_swaps_only_its_card"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_update-правка расписания — успех]"
        status: pass
    human_judgment: false
  - id: D2
    description: "Off-screen outcomes (schedule missing with own ad, foreign ad, account gone, no return marker) answer htmx with 204 and HX-Location equal character-for-character to the 302 address, notice code where issued today"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports"
        status: pass
    human_judgment: false
  - id: D3
    description: "Edit response refreshes #ad-summary and the panel text by content of sched-del-N-text; OOB text equals the full page text after reload"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_edit_over_htmx_refreshes_the_summary_and_the_panel_text"
        status: pass
    human_judgment: false
  - id: D4
    description: "GATE-02 pair module: registry with declared count 6, closure over converted POST handlers, negative control naming schedules_update"
    requirement: GATE-02
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_the_number_of_pair_cases_is_the_declared_one"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_converted_handler_has_a_pair"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_control_a_handler_without_a_case_reddens_the_closure"
        status: pass
    human_judgment: false
  - id: D5
    description: "Gate numbers set by red runs: NOT_YET_CONVERTED_COUNT 25, FRAGMENT_RESPONSE_HANDLERS_DECLARED 4, HX_HEADER_WRITES stays 2, OOB_BLOCKS 15, CLIENT_STATE_NODES stays 24"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_htmx_gates.py tests/test_templates/ tests/test_pages/test_hx_location_destinations.py -q"
        status: pass
    human_judgment: false
  - id: D6
    description: "In the browser the expanded card stays expanded after save, scroll does not jump, exactly one sched-del-N panel remains and opens with current text after ten saves without reload"
    verification: []
    human_judgment: true
    rationale: "ASGI transport executes no htmx/Alpine runtime; swap effect, scroll and panel duplication are observable only in a browser — phase UAT item 5"

duration: 1h 13m
completed: 2026-09-15
status: complete
---

# Phase 11 Plan 01: Schedule edit as the tracer slice Summary

**`schedules_update` goes through `respond()`: over htmx it returns its own expanded `#sched-N` card via `form_wrapper` + `outerHTML`, with OOB `#ad-summary` and panel text by permanent id; off-screen outcomes go `HX-Location`; GATE-02 gets a single parametrized pair module with a closure over every converted handler.**

## Performance

- **Duration:** 1h 13m (implementation 30 min; full suite 40 min 47 s)
- **Started:** 2026-09-15T18:04:36Z
- **Completed:** 2026-09-15T19:17Z
- **Tasks:** 2
- **Files modified:** 9 (2 created, 7 modified)

## Accomplishments

- Schedule edit in the ad editor answers htmx with a 200 fragment whose first node is the card, expanded, no `<!DOCTYPE`, no `sched-del-N` root; without htmx the 302 to `/ads/{ad}/edit?sched=N#sched-N` is unchanged.
- Every other exit (no session, schedule missing with own ad → `?notice=schedule_ad_missing`, schedule missing otherwise, foreign ad → `/schedules`, account gone → `?notice=schedule_account_gone`, no return marker → `/schedules`) goes `respond()` without a fragment. The handler writes to the database exactly as before.
- `sched_card` split into `sched_card_article` and `sched_card_panel_text`. The panel text is now one macro value used in three places: card header, panel body and OOB node. Rendered markup was compared against HEAD templates: the collapsed card is byte-identical, and in the expanded card only the edit form tag changed (now `form_wrapper`).
- The OOB nodes in the edit response are `#ad-summary` (node, the single `summary.html` source) and `innerHTML:#sched-del-N-text`, so the Alpine-stateful panel root is never touched.
- `tests/test_pages/test_htmx_post_pairs.py` holds 6 cases: 5 edit outcomes plus the Phase 9 group toggle success. It has a declared count, a closure over `_post_handlers` with `calls_respond` minus (registry ∪ `CONFIRMED_DELETE_ROUTES`), and a negative control.

## Task Commits

1. **Task 1 (tracer): schedule edit end-to-end slice**
   - RED `95c0aa9` (test)
   - GREEN `5348f64` (feat)
2. **Task 2: summary and panel text refresh**
   - RED `ff0f0cc` (test)
   - GREEN `3045b37` (feat)

**Plan metadata:** see the docs commits that follow.

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `95c0aa9` | `5348f64` | — (not needed) |
| 2 | `ff0f0cc` | `3045b37` | — (not needed) |

RED evidence was verified with `gsd-tools check tdd-red-evidence`, verdict `RED_EVIDENCE_OK` on both tasks. The record was built from pytest junit output converted to TAP lines.

- **Task 1**
  - Target: `test_schedule_edit_over_htmx_swaps_only_its_card`, `1 failed`, exit 1.
  - Causal literal: `assert '<!DOCTYPE' not in '\n\n<!DOCTY...dy>\n</html>'` (the literal exists in `app/templates/base.html`).
  - In the same run, all five `schedules_update` htmx halves failed on the same literal after their 302 halves passed with exact landings.
  - The closure control failed: `assert 'app/pages/schedules.py::schedules_update' in []`.
- **Task 2**
  - Target: `test_schedule_edit_over_htmx_refreshes_the_summary_and_the_panel_text`, `1 failed`, exit 1.
  - Causal text: `AssertionError: узла сводки нет среди внеполосных: set()`.

## Gate numbers — verbatim texts of the red rules that set them

| Constant | Move | Red rule and verbatim text |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 26 → 25 | `test_the_backlog_matches_the_declared_count`: «число непереведённых обработчиков стало 25, а в файле записано 26. ЕСЛИ ЧИСЛО УПАЛО — ЭТО ПРОГРЕСС ВЕХИ, а не поломка» / `assert 25 == 26` |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 3 → 4 | `test_the_number_of_fragment_response_handlers_is_the_declared_one`: «обработчиков, отдающих фрагмент, найдено 4, объявлено 3» / `assert 4 == 3` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 32 → 38 | `test_the_number_of_transition_answering_calls_is_declared`: «вызовов слоя ответа БЕЗ фрагмента найдено 38, а объявлено 32» |
| `MACRO_DEFINITION_SITES_CALLERS_DECLARED` (+ `form_wrapper` callers) | 11 → 12 | `test_the_number_of_hidden_callers_is_the_declared_one`: «объявленные вызывающие разошлись с измеренными: {'components/form_wrapper.html': "объявлено ('account_groups/includes/group_row.html',), измерено ('account_groups/includes/group_row.html', 'ads/includes/sched_card.html')"}» |
| `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` (+ `PARAMETRIC_SWAP_TARGETS` callers) | 1 → 2 | `test_the_number_of_hidden_callers_is_the_declared_one`: «за перечнем параметрических целей подмены спрятано вызывающих 2, объявлено 1» |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 1 → 2 | `test_no_caller_declares_a_blocking_target_its_form_cannot_have`: «блоков вызова макроса-обёртки разобрано 2, объявлено 1» |
| `OOB_BLOCKS` | 13 → 15 | `test_the_number_of_oob_blocks_is_the_declared_one`: «внеполосных блоков найдено 15, объявлено 13» |

Constants that did not move:
- `HX_HEADER_WRITES = 2`
- `CLIENT_STATE_NODES = 24`
- `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 23`
- `OWN_RESPONSE_EXITS_DECLARED = 9`

## G-11 collision

`test_no_id_is_both_a_swap_target_and_an_oob_target` **did not go red**: `sched-N` is a parametric target printed through `form_wrapper`'s `{{ target }}`, which the literal-target scanner does not see. The Phase 9 resolution form was still applied and recorded in the `PARAMETRIC_SWAP_TARGETS['components/form_wrapper.html'].reason` entry. The two operations are different responses, not two swaps of one response:
- The edit response has no OOB `#sched-N` node.
- The delete response (`hx-swap="none"`) has no main swap.

The rule was not removed.

## Files Created/Modified

- `app/pages/schedules.py`
  - `schedules_update`: every exit goes through `respond()`.
  - New zero-arity async `_fragment` built from `_editor_context`.
  - Module-level import of `_editor_context`.
- `app/templates/ads/includes/sched_card.html`
  - New macros `sched_card_panel_text` and `sched_card_article`.
  - `sched_card` is now composed from them.
  - The edit form goes through `form_wrapper`.
- `app/templates/ads/partials/sched_card_response.html` — new: card article, OOB `#ad-summary`, OOB panel text.
- `app/templates/components/modal.html` — `id="{{ id }}-text"` on `.modal__text`.
- `tests/test_pages/test_htmx_post_pairs.py` — new pair module.
- `tests/test_pages/test_editor_schedules.py` — two htmx tests added; existing 302 assertions untouched.
- `tests/test_pages/test_htmx_gates.py`, `tests/test_pages/test_hx_location_destinations.py`, `tests/test_templates/test_htmx_markup_gates.py` — constants and chronicles.

## Decisions Made

- The success fragment takes the card object from `_editor_context`'s fresh selection, not the handler's `schedule`: after `commit()` its attributes may be expired.
- `_editor_redirect` and `_editor_error_redirect` stay in the module; create and toggle still call them until 11-03 and 11-05.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Markup and transition constants moved in Task 1, not Task 2**
- **Found during:** Task 1 (GREEN run)
- **Issue:** The plan assigned the markup-gate and `HX_LOCATION_DESTINATION_CALLS_DECLARED` moves to Task 2. But Task 1's `form_wrapper` switch and its six new `respond()` calls without a fragment already turned red:
  - `test_the_number_of_hidden_callers_is_the_declared_one`
  - `test_no_caller_declares_a_blocking_target_its_form_cannot_have`
  - `test_every_declared_parametric_caller_actually_calls_the_macro`
  - `test_the_number_of_transition_answering_calls_is_declared`

  Committing Task 1 without those moves would have left a red tree.
- **Fix:** Moved each constant after its own red run, with verbatim chronicles, inside the Task 1 GREEN commit. Task 2 moved only `OOB_BLOCKS`.
- **Files modified:** `tests/test_templates/test_htmx_markup_gates.py`, `tests/test_pages/test_hx_location_destinations.py`
- **Verification:** Task 1 verify set plus markup gates: 346 passed.
- **Committed in:** `5348f64`

**2. [Rule 1 - Precision] Closure red-state for the group toggle proven by the helper, not by the RED run**
- **Found during:** Task 1 (RED)
- **Issue:** The behavior said the closure goes red without the `account_groups_toggle` case. That case is in the registry from the first commit, so `test_every_converted_handler_has_a_pair` was green in RED.
- **Fix:** Measured the helper directly: `_closure_complaints(registry without the group toggle)` → `['app/pages/account_groups.py::account_groups_toggle']`. The committed control proves the same property for `schedules_update`.
- **Files modified:** none
- **Committed in:** n/a

---

**Total deviations:** 2 (1 blocking-order fix, 1 evidence precision note)
**Impact on plan:** No scope change. Every commit leaves the affected suites green.

## Issues Encountered

None.

## Verification

- Plan-level gates run in random order (`uv run pytest tests/test_templates/ tests/test_pages/test_htmx_gates.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_editor_schedules.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_confirm_delete_transport.py tests/test_pages/test_ads_editor.py -q`): 459 passed.
- Full suite `uv run pytest tests/ -q`: **3273 passed, rc=0, 40:47**. The known flaky `full-suite-ads-editor-order-pollution` did not fire.
- `uv run python -m compileall -q app main.py tests`: clean.
- `graphify update .`: graph refreshed; `graphify-out/` is git-ignored.
- Nothing in the verify blocks was left unrun. The browser half of D6 (the `<human-check>` for phase UAT item 5) is deferred to the end-of-phase UAT by `human_verify_mode: end-of-phase`.

## Known Stubs

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 11-02 (window 51 in the schedules module) can proceed: `schedules_update` is on the response layer, and the pair module accepts new cases.
- 11-03 and 11-05 inherit `sched_card_article`, `sched_card_panel_text` and the response-template shape. The two remaining callers of the old redirect helpers are toggle and create.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-15*

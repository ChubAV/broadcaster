---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 03
subsystem: ui
tags: [htmx, fastapi, jinja2, respond, form_wrapper, tdd, gate-02]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-01: schedules_update on respond(), ads/partials/sched_card_response.html, sched_card_article macro, POST_PAIR_CASES registry; 11-02: id_in_column first-use bound in schedules_toggle"
  - phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
    provides: "Toggle form shape (form_wrapper trigger=change, disabled_elt='', sync=this:drop, Apply span removing itself when htmx is live), DIV-09-02 precedent"
provides:
  - "schedules_toggle on respond(): editor screen answers 200 + #sched-N card with server state and expansion from keep_sched; missing/foreign, out-of-domain (notice) and summary list answer a transition to the same address as the 302"
  - "Card toggle form in ads/includes/sched_card.html on form_wrapper; Alpine submit-on-change removed"
  - "DISABLED_ELT_EXCEPTIONS form_wrapper entry gains caller ads/includes/sched_card.html (D-11)"
  - "Four toggle pair cases in POST_PAIR_CASES (7 -> 11)"
affects: [11-04, 11-20, schedules, ads-editor]

actuals:
  tokens: 9612
  tasks: 2
  commits: 3
plan_head_before: ee8e3974bb96014ba17724edb631f12643a72395

tech-stack:
  added: []
  patterns:
    - "Two-screen handler: return_to marker read once selects the response form only (editor card vs transition); write rights unchanged"
    - "Blocked resume answers the unchanged card so the optimistic checkbox is reverted by the server"
    - "Form body parsed before the first write (WR-07 reasoning, as in schedules_delete)"

key-files:
  created: []
  modified:
    - app/pages/schedules.py
    - app/templates/ads/includes/sched_card.html
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "schedules_toggle summary-list branch answers a transition to /schedules with no fragment; the row fragment and its markup belong to plan 11-04"
  - "Card toggle form takes the empty blocking target and this:drop sync by the DIV-09-02 precedent under D-11; recorded as a second caller of the form_wrapper entry in DISABLED_ELT_EXCEPTIONS, entry count unchanged"
  - "Editor tests that sliced the page after the toggle route path now read the label.toggle node by its for attribute: form_wrapper prints the path twice (action and hx-post)"

patterns-established:
  - "Toggle fragment builder is nullary and async, context from _editor_context with the keep_sched value as selected id (same source as the full editor page)"

requirements-completed: [FORM-03]

coverage:
  - id: D1
    description: "htmx toggle in the editor answers 200 with the pressed card collapsed while the expanded neighbour stays expanded; degraded path 302 to /ads/{ad}/edit?sched=A#sched-A"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_toggle_over_htmx_keeps_the_expanded_neighbour"
        status: pass
    human_judgment: false
  - id: D2
    description: "Blocked resume over htmx returns the unchanged card (checkbox without checked, is_active false in the database)"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_a_blocked_resume_over_htmx_returns_the_unchanged_card"
        status: pass
    human_judgment: false
  - id: D3
    description: "Both transports per outcome: editor success (fragment), out-of-domain (transition with schedule_values_out_of_domain), missing schedule and summary list (transition to /schedules)"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (four schedules_toggle cases)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_converted_handler_has_a_pair"
        status: pass
    human_judgment: false
  - id: D4
    description: "Counters set by run: NOT_YET_CONVERTED_COUNT 25 -> 24, FRAGMENT_RESPONSE_HANDLERS_DECLARED 4 -> 5, HX_LOCATION_DESTINATION_CALLS_DECLARED 38 -> 42, UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED 2 -> 3"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py (57 passed with test_hx_location_destinations.py)"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_no_caller_declares_a_blocking_target_its_form_cannot_have"
        status: pass
    human_judgment: false
  - id: D5
    description: "Card toggle form on form_wrapper (trigger change, drop sync, empty blocking target), Alpine intercept removed, Apply span kept for the Alpine-alive/htmx-dead world"
    requirement: FORM-03
    verification:
      - kind: other
        ref: "grep -c 'x-on:change=\"$el.submit()\"' app/templates/ads/includes/sched_card.html -> 0; trigger='change' -> 1; sync='this:drop' -> 1"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -k 'disabled_elt or two_roles or client_state' (10 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "In the browser the card toggle switches with one press, a fast double press sends one request, focus stays on the toggle, the expanded neighbour does not collapse (phase UAT item 5)"
    requirement: FORM-03
    verification: []
    human_judgment: true
    rationale: "Request count in the Network tab, focus placement and visual expansion need a live browser; the suite has no browser stand"

duration: 29min
completed: 2026-09-15
status: complete
---

# Phase 11 Plan 03: Schedule toggle on the response layer Summary

**`schedules_toggle` answers through `respond()`: in the editor it swaps the `#sched-N` card with server state and keeps the expansion from `keep_sched`; missing, out-of-domain and summary-list outcomes answer a transition to the same address as the 302. The card toggle form now submits via `form_wrapper` on change with drop sync.**

## Performance

- **Duration:** 29 min of task work (the regression run over `tests/test_pages` and `tests/test_templates` took another 32 min)
- **Started:** 2026-09-15T21:30:48Z
- **Completed:** 2026-09-15T22:00:33Z (task commits); metadata after the regression run
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- The toggle handler has no redirect of its own on any branch. The body is parsed before the write, and the screen marker is read once.
- A blocked resume returns the card unchanged, so the checkbox the browser flipped optimistically goes back to the server state.
- The card toggle form uses the Phase 9 toggle shape. Its exception is recorded under D-11 with the DIV-09-02 precedent.
- Counters were moved only after the reddened rule printed the measured value.

## Task Commits

1. **Task 1 RED:** `7bd0cb1` (test): two editor tests plus four pair cases
2. **Task 1 GREEN:** `39adcdc` (feat): handler on `respond()`, gate counters
3. **Task 2:** `05240b2` (feat): card toggle form on `form_wrapper`, exception list entry, markup counter, test instrument

## TDD Gate Compliance

- **RED** `7bd0cb1`: `FAILED tests/test_pages/test_editor_schedules.py::test_schedule_toggle_over_htmx_keeps_the_expanded_neighbour` and `FAILED ...::test_a_blocked_resume_over_htmx_returns_the_unchanged_card`, summary `2 failed, 69 deselected`, rc=1, cause `assert 302 == 200`. The 302 came from the old handler's own redirect in `app/pages/schedules.py`.
  - All four toggle pair cases failed on their htmx half with `слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ`; their degraded halves passed.
  - Checker verdict: `RED_EVIDENCE_OK` (`target_test_failed`) for each target test.
  - How the record was built: the first record, from plain pytest text, came back `INVALID_RED (invalid_record)`, because the checker reads camelCase fields and node TAP. It was rebuilt from JUnit XML of a re-run in the same RED state, converted by a scratchpad script (same method as 11-01 and 11-02). No line was written by hand.
- **GREEN** `39adcdc`: the two named tests went to `2 passed`. The task 1 verify command as written: `186 passed`, rc=0.
- **REFACTOR:** none.

## Verification

- Task 1 `<automated>` (six files): 186 passed, rc=0.
- Task 2 `<automated>` (markup gates, components, editor schedules, htmx gates): 281 passed, rc=0.
- `tests/test_pages/test_htmx_post_pairs.py`: 14 passed.
- `uv run python -m compileall -q app main.py tests`: no errors.
- Regression run `uv run pytest tests/test_pages tests/test_templates -q`: 1911 passed, rc=0. It ran in the background and finished; it was not killed.
- Not run inside the plan: the full `tests/` suite, which is the orchestrator's gate, and `tests/test_planning/` until the metadata step.
- `graphify update .`: done.

## Files Created/Modified

- `app/pages/schedules.py`: `schedules_toggle` on `respond()` with two screens and a nullary card fragment builder.
- `app/templates/ads/includes/sched_card.html`: toggle form through `form_wrapper`; Apply span with bare `x-data`/`x-init`.
- `tests/test_pages/test_editor_schedules.py`: two new tests; the `_toggle_markup` helper replaces the path slice in two existing tests.
- `tests/test_pages/test_htmx_post_pairs.py`: four toggle cases, 7 → 11.
- `tests/test_pages/test_htmx_gates.py`:
  - Toggle key moved from `NOT_YET_CONVERTED` to `FRAGMENT_RESPONSE_HANDLERS`.
  - Backlog count 25 → 24 and fragment-handler count 4 → 5, each with a chronicle entry.
- `tests/test_pages/test_hx_location_destinations.py`: 38 → 42 with a chronicle entry.
- `tests/test_templates/test_htmx_markup_gates.py`:
  - `DISABLED_ELT_EXCEPTIONS` callers and reason chronicle.
  - `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 2 → 3.

## Decisions Made

See `key-decisions` in the frontmatter.

Measured non-movements:
- `MACRO_DEFINITION_SITES_CALLERS_DECLARED`, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` and `CLIENT_STATE_NODES` did not redden in the task 2 run. The bare marker moved from the form to the span, one out and one in, so none of them was edited.
- `DISABLED_ELT_EXCEPTIONS_DECLARED` also stays: a caller was added, not an entry.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two editor tests sliced the page after the toggle route path**
- **Found during:** Task 2
- **Issue:** `test_account_without_groups_says_so` and `test_active_incomplete_schedule_can_still_be_paused_from_the_editor` used `html.split("/schedules/N/toggle")[1][:400]`. `form_wrapper` prints the path in `action` and again in `hx-post`, so the slice became `" hx-post="`: `assert 'disabled' in '" hx-post="'`.
- **Fix:** a `_toggle_markup` helper reads the `label.toggle` node by `for="sched-toggle-N"`. The assertions are unchanged.
- **Files modified:** `tests/test_pages/test_editor_schedules.py`
- **Verification:** task 2 verify, 281 passed
- **Committed in:** `05240b2`

**2. [Rule 3 - Blocking] `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` not named in the plan**
- **Found during:** Task 2
- **Issue:** the anti-vacuum count of `form_wrapper` call blocks reddened: `разобрано 3, объявлено 2`.
- **Fix:** 2 → 3 with a chronicle entry.
- **Files modified:** `tests/test_templates/test_htmx_markup_gates.py`
- **Committed in:** `05240b2`

---

**Total deviations:** 2 auto-fixed (both Rule 3, test instruments and counters driven by the planned markup change).
**Impact on plan:** no scope change; product behaviour is as planned.

## Issues Encountered

The RED evidence checker rejected the plain pytest record, which was resolved by the JUnit XML conversion described above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 11-04 can bring the summary-list row fragment and cursor. The list branch of `schedules_toggle` is a transition today, and `schedules/includes/schedule_row.html` is untouched.
- Human check pending: phase UAT item 5 (D6), to be recorded in `11-UAT.md` at end of phase.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-15*

---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 04
subsystem: ui
tags: [htmx, fastapi, jinja2, keyset, pagination, respond, form_wrapper, tdd, form-03]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-03: schedules_toggle on respond() with the two-screen marker and the editor card fragment; 11-02: id_in_column bound at first use; 11-01: POST_PAIR_CASES registry"
  - phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
    provides: "keyset cursor branch (after_id) chosen by the owner for CR-01; toggle form shape (form_wrapper trigger=change, disabled_elt='', sync=this:drop, Apply span removing itself under live htmx); DIV-09-02 precedent"
provides:
  - "/schedules/partial on a keyset cursor: after_id replaces the offset, next_after_id is the key of the last rendered row, both sentinels byte-identical"
  - "schedules_toggle summary-list branch answers 200 with the row #schedule-row-N carrying server state (blocked resume reverts the optimistic checkbox)"
  - "app/templates/schedules/partials/schedule_row_response.html — flat one-node row response"
  - "Row toggle form on form_wrapper; Alpine submit-on-change removed; caller recorded in DISABLED_ELT_EXCEPTIONS, MACRO_DEFINITION_SITES_CALLERS and PARAMETRIC_SWAP_TARGETS"
  - "The schedules signature gate now recognises the inline bound (Query ge/le), pinned by a new half-bound negative control"
affects: [11-05, 11-06, 11-20, schedules, ads-editor]

actuals:
  tokens: 17947
  tasks: 2
  commits: 5
plan_head_before: 3c68187dd62c2ec3c51caa79d2ad5fa886001ff6

tech-stack:
  added: []
  patterns:
    - "Keyset cursor for a filtered list: the toggled-out row cannot shift the next portion, so CR-01 becomes inexpressible by the shape of the contract rather than caught by a comparison"
    - "One handler, two screens, two fragments: the return marker selects the response form only; the row fragment is built by the same functions as the list itself"
    - "A widened gate predicate ships with its own negative control (half an inline bound must redden)"

key-files:
  created:
    - app/templates/schedules/partials/schedule_row_response.html
  modified:
    - app/pages/schedules.py
    - app/templates/schedules/list.html
    - app/templates/schedules/partial_cards.html
    - app/templates/schedules/includes/schedule_row.html
    - tests/test_pages/test_schedules_list.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_pages/test_editor_schedules.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "The cursor landed in task 1, BEFORE the row fragment: on no commit of this plan could a toggle under the state filter eat a row of the next portion (D-11 ordering honoured literally)"
  - "The row response carries NO out-of-band nodes: the `total` line is deliberately left unrepainted until reload — the named, accepted price of 'the row does not vanish from under the hand'"
  - "after_id was NOT added to SIGNATURE_GATE_EXEMPTIONS: its value IS sender-controlled, so it fails that registry's own criterion; instead the gate learned the second form of the bound the catalogue gate already accepts, keeping the input inside the counted universe"
  - "The vacuous acceptance criterion (-k sentinel selects nothing) was NOT counted as passed; real sentinel coverage came from the hx-get inventory, the scroll-chain gate and the byte-identity diff"

patterns-established:
  - "Tests follow the sentinel address the page emitted instead of assembling a cursor URL themselves — a self-assembled address knows the cursor form by heart and blames the form instead of a broken chain"

requirements-completed: [FORM-03]

coverage:
  - id: D1
    description: "/schedules/partial pages on the key of the last row: after a toggle under the state filter the next portion skips no row"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_the_next_portion_does_not_skip_a_row_after_a_toggle_under_the_state_filter"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain (schedules section, cursor form unchanged along the chain)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sentinel markup is byte-identical in list.html and partial_cards.html and carries no offset; schedules_partial has no .offset( call"
    requirement: FORM-03
    verification:
      - kind: other
        ref: "diff <(grep 'hx-get=\"/schedules/partial' list.html) <(grep ... partial_cards.html) -> empty; grep -c 'offset=' both -> 0; awk schedules_partial | grep -c '.offset(' -> 0"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py (REVEALED_SITES, 19 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The summary-list toggle answers 200 with <article class=\"sched-item\" id=\"schedule-row-N\"> and no <!DOCTYPE; without htmx it still 302s to /schedules"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_the_list_toggle_answers_with_its_own_row_over_htmx"
        status: pass
    human_judgment: false
  - id: D4
    description: "A blocked resume of an incomplete schedule returns the row unchanged: the optimistically flipped checkbox goes back, is_active stays false"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_a_blocked_resume_from_the_list_returns_the_row_unchanged"
        status: pass
    human_judgment: false
  - id: D5
    description: "Both transports for the summary-list branch: 302 to /schedules without the marker, 200 + row fragment with it (case class LOCATION -> FRAGMENT)"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_toggle-со сводного списка]"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_converted_handler_has_a_pair"
        status: pass
    human_judgment: false
  - id: D6
    description: "Row toggle form lives by the Phase 9 shape: form_wrapper with change trigger, drop sync, empty blocking target; Alpine change-intercept removed; Apply button kept for the Alpine-alive/htmx-dead world"
    requirement: FORM-03
    verification:
      - kind: other
        ref: "grep -c 'x-on:change=\"$el.submit()\"' schedule_row.html -> 0; grep -c 'schedules/includes/schedule_row.html' test_htmx_markup_gates.py -> 5"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_no_caller_declares_a_blocking_target_its_form_cannot_have"
        status: pass
    human_judgment: false
  - id: D7
    description: "Gate numbers moved by run, each with a chronicle entry: catalogue universe 35->36, pagination exclusion 13->12, hidden callers 12->13, parametric callers 2->3, wrapper call blocks 3->4, transition calls 42->41, bounded route inputs 7->8"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py, tests/test_templates/test_htmx_markup_gates.py, tests/test_pages/test_hx_location_destinations.py, tests/test_pages/test_editor_schedules.py (all green after each number was read off the reddened rule)"
        status: pass
    human_judgment: false
  - id: D8
    description: "In the browser the row toggle switches with one press, a fast double press sends one request, focus stays on the toggle, the filtered row stays at hand, and scrolling to the second portion loses no rows — phase UAT item 5"
    verification: []
    human_judgment: true
    rationale: "Request count in the Network tab, focus placement and scroll behaviour need a live browser; the suite has no browser stand"

duration: 47min
completed: 2026-09-15
status: complete
---

# Phase 11 Plan 04: Summary schedules list — keyset cursor and row fragment Summary

**`/schedules/partial` now pages on the key of the last rendered row, and the summary-list toggle answers with its own `#schedule-row-N` carrying server state — so a row switched out from under the state filter can no longer make the next portion skip a card (CR-01 of Phase 9, made inexpressible rather than caught).**

## Performance

- **Duration:** 47 min
- **Started:** 2026-09-15T23:06:06Z
- **Completed:** 2026-09-15T23:53Z
- **Tasks:** 2
- **Files modified:** 11 (1 created)

## Accomplishments

- The cursor landed **before** the row fragment, exactly as D-11 orders: on no commit of this plan could a toggle under the filter eat a row.
- The list branch of `schedules_toggle` answers the row of its own screen; the editor branch is untouched, and neither fragment can land on the other's screen.
- A blocked resume returns the row unchanged, so the browser's optimistic checkbox is put back by the server.
- Every gate number was moved only after the reddened rule printed the measured value, each with a chronicle entry.
- A regression the plan did not foresee was found and fixed at its own gate, with a new negative control so the fix cannot rot.

## Task Commits

1. **Task 1 RED:** `8646d5d` (test): the next portion must not skip a row after a toggle under the state filter
2. **Task 1 GREEN:** `b8e6de6` (feat): keyset cursor, both sentinels, two catalogue counters
3. **Task 2 RED:** `052afb3` (test): row fragment, blocked resume, pair case LOCATION -> FRAGMENT
4. **Task 2 GREEN:** `0729eca` (feat): row response template, list branch on a fragment, form on the wrapper, four counters
5. **Deviation fix:** `5cb11b9` (test): the schedules signature gate learns the inline bound + half-bound control

_No REFACTOR commit: neither cycle left cleanup that would not have changed behaviour._

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `8646d5d` | `b8e6de6` | — (not needed) |
| 2 | `052afb3` | `0729eca` | — (not needed) |

RED evidence was verified with `gsd-tools check tdd-red-evidence`, verdict **`RED_EVIDENCE_OK`** (`target_test_failed`) on both tasks. Records were built from pytest JUnit XML converted to node TAP (the checker reads camelCase input fields and TAP counts) — the same method as plans 11-01…11-03. No line was written by hand.

- **Task 1** — target `test_the_next_portion_does_not_skip_a_row_after_a_toggle_under_the_state_filter`, `1 failed, 42 deselected`, exit 1.
  - Causal literal, verified present in the tree: the sentinel requested `/schedules/partial?offset=30&limit=30&state=active` (`app/templates/schedules/list.html:61`, `.offset(offset)` at `app/pages/schedules.py:839`).
  - Failure was the planned one, not an incidental error: `assert [32, 33, 34, 35] == [31, 32, 33, 34, 35]` — exactly one row skipped.
- **Task 2** — target `test_the_list_toggle_answers_with_its_own_row_over_htmx`, `3 failed, 12 passed`, exit 1.
  - Causal text: «слою письма ответили 204 вместо 200 со строкой» — the list branch answered a transition (`respond(redirect=…)` without a fragment).
  - The other two RED rules failed on the same cause; the 12 passing tests in the same run (untouched pair cases + the closure rule) show the RED was scoped to the new behaviour.

## Verification

| Run | Result |
|---|---|
| Task 1 `<automated>` (schedules list, identifier bounds, markup gates) | 139 passed → after counters, green |
| Task 1 + direct cursor consumers (preserved, detached account, poisoned row) | 174 passed |
| Task 2 `<automated>` (schedules list, pairs, markup gates, hx-location, htmx gates) | 193 passed |
| Plan `<verification>` triple on the final tree | 134 passed |
| AC suites (`test_schedules_out_of_domain_resume.py`, `test_schedules_toggle_detached.py`) | 44 passed |
| Regression (responsive markup, poisoned row, detached, editor, preserved) | 242 passed — **2 failures found here and fixed**, see Deviations |
| `test_editor_schedules.py` after the fix | 72 passed |
| `hx-get` inventory | 19 passed |
| `uv run python -m compileall -q app main.py tests` | no errors |
| `graphify update .` | done (20375 nodes, 35499 edges) |

**Not run inside the plan:** the full `tests/` suite, which is the orchestrator's gate, and `tests/test_planning/` until the metadata step. No test run of this plan was killed by the host's watchdog.

### Acceptance criteria

Task 1: offset gone from both sentinels (`2`), sentinels byte-identical (empty diff), no `.offset(` in `schedules_partial` (`0`), target rule green. **AC5 (`-k "sentinel"`) is VACUOUS and was not counted as passed** — see Issues.

Task 2: Alpine intercept grep `0`, caller declared in the markup gates `5`, `-k disabled_elt` green, both AC suites green, compileall clean.

## Files Created/Modified

- `app/pages/schedules.py` — `schedules_partial` on `after_id`; `schedules_list` and the partial hand out `next_after_id`; the list branch of `schedules_toggle` builds the row fragment with the same functions as the list.
- `app/templates/schedules/partials/schedule_row_response.html` (**new**) — flat body, one top-level node.
- `app/templates/schedules/list.html`, `partial_cards.html` — keyset sentinel, byte-identical.
- `app/templates/schedules/includes/schedule_row.html` — toggle form through `form_wrapper`; Apply span with bare `x-data`/`x-init`.
- `tests/test_pages/test_schedules_list.py` — three new rules; the order test now follows the emitted sentinel.
- `tests/test_pages/test_identifier_bounds.py` — universe 35→36, pagination 13→12.
- `tests/test_pages/test_htmx_post_pairs.py` — the summary-list case became `FRAGMENT`.
- `tests/test_pages/test_hx_location_destinations.py` — 42→41.
- `tests/test_templates/test_htmx_markup_gates.py` — three caller registries, 12→13, 2→3, 3→4.
- `tests/test_pages/test_editor_schedules.py` — inline bound recognised, new negative control, 7→8.

## Decisions Made

See `key-decisions` in the frontmatter.

**Measured non-movements** (each checked by run, not assumed): `OOB_BLOCKS`, `CLIENT_STATE_NODES`, `HX_TARGETS`, `FRAGMENT_ROUTES_DECLARED`, `DISABLED_ELT_EXCEPTIONS_DECLARED`, `POST_PAIR_CASES_DECLARED` did not move. The row response carries no out-of-band nodes, the bare client-state marker moved from the form to the span (one out, one in), a caller was added rather than an entry, and no pair case was added — its class changed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] The schedules signature gate reddened on the new cursor parameter**
- **Found during:** regression after Task 2 (the plan's own verify sets did not include this module)
- **Issue:** `test_every_identifier_input_of_the_schedule_routes_carries_the_shared_bound` knew the bound **only** as one of three aliases, and all three are built on `Path()`/`Form()`. `after_id` is a `Query` cursor, for which no alias exists in the project, so the gate called a bounded input unbounded and demanded an alias that cannot be written. Its negative control failed consequentially.
- **Fix:** the gate now recognises the **second form** of the bound — an inline record carrying both halves of the range — which is exactly the pair the catalogue gate (`_carries_the_bound`) already accepts, and for the same recorded reason. `after_id` was deliberately **not** exempted: its value is sender-controlled and therefore fails `SIGNATURE_GATE_EXEMPTIONS`' own stated criterion, and exempting it would have dropped it out of the counted universe. `BOUNDED_ROUTE_INPUTS_DECLARED` 7→8 by run; the letopis premise "partial and list carry no identifiers at all", falsified by this plan, is named rather than erased.
- **Guard against widening:** a new negative control `test_control_negative_half_an_inline_bound_reddens_the_signature_gate` proves that `Query(None, ge=1)` — the lower half only — still reddens. Without it, recognising the inline form would have been a hole rather than a замер, since it is the **upper** half that stops a value from reaching the DB driver.
- **Files modified:** `tests/test_pages/test_editor_schedules.py`
- **Verification:** 72 passed
- **Committed in:** `5cb11b9`

---

**Total deviations:** 1 auto-fixed (Rule 1), covering both observed failures (the rule and its control share one cause).
**Impact on plan:** no scope change and no product behaviour change — the deviation is confined to a gate's notion of "carries the bound", and it left the gate stricter than it found it (two negative controls where there was one).

## Issues Encountered

**An acceptance criterion of the plan is vacuous, and it was not counted as passed.** Task 1's AC5 prescribes `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -k "sentinel"` and expects green. Measured: `no tests collected (77 deselected)` — no rule of that name exists in the module, so the green means "nothing executed", not "the sentinel is proven". Per the project's own lesson («RED-гейт зеленеет вакуумом») this is recorded rather than banked: `.planning/WINDOWS.md` entry **84** (`kind: unrun-verify`, `status: open`). Actual sentinel coverage came from three rules that did run — the `hx-get` inventory (`REVEALED_SITES`), the infinite-scroll chain gate, and the byte-identity diff of AC2.

## Known Stubs

None. No hardcoded empty values, placeholder text, skipped tests or unwired components were introduced.

## Threat Flags

None new. The register's two `mitigate` items are implemented as planned: **T-11-09** — the cursor is bounded `Query(None, ge=1, le=ID_MAX)` and narrows the selection inside the owner's scope without widening it; **T-11-39** — the row element is built by `_summary_query(user.id)`, so ownership stands in the query itself and a forged identifier cannot assemble a foreign row.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 11-05 can take schedule creation (`beforeend` into `#sched-list`): the summary list is now fully fragment-capable and its cursor no longer shifts.
- Two offset cursors remain declared exemptions (`OFFSET_CURSOR_EXCEPTIONS`: accounts and ads) — untouched by this plan and still addressed to their own work.
- Human check pending: phase UAT item 5 (D8), to be recorded in `11-UAT.md` at end of phase.
- `.planning/WINDOWS.md` entry 84 is open for the planner of the next round.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-15*

## Self-Check: PASSED

- All 11 files named in `key-files` exist on disk (1 created, 10 modified), verified with `[ -f ]`.
- All five commits exist: `8646d5d`, `b8e6de6`, `052afb3`, `0729eca`, `5cb11b9`.
- `commits: 5` is MEASURED, not narrated, and the two figures are stated apart so neither is read as the other. FIVE is the count of this plan's TASK commits — `git rev-list --count 3c68187..HEAD` over the persisted plan ledger at the moment this file was written, before any docs commit existed. SEVEN is what the same command returns AFTER the close-out, because the SUMMARY commit (`e466585`) and the metadata commit (`e052d99`) land inside the same ledger range. `actuals.commits` keeps the task-commit figure, matching the `## Task Commits` list above and the sibling plan 11-03 (`commits: 3` with two further docs commits in its own range).
- Records: ROADMAP checkbox, progress row **and prose** (3 → 4, the count the verb leaves behind) and STATE position/metric/decisions/session are done; `progress.completed_plans` was left at the verb-derived 99 because `tests/test_planning/` was RUN after every record edit and returned 44 passed — the value is confirmed by the gate, not assumed.
- REQUIREMENTS.md is deliberately untouched: FORM-03 and the other six phase-11 IDs stay `Pending` until phase verification passes.

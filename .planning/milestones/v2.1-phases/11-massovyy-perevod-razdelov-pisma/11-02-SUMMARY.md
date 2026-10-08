---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 02
subsystem: ui
tags: [fastapi, identifiers, d-07, window-51, ast-gate, tdd, htmx]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-01: schedules_update on the response layer, POST_PAIR_CASES registry with closure"
  - phase: 10-rychag-components-modal-html
    provides: "ID_MAX in app/pages/identifiers.py, catalogue universe rule (plan 10-30), window 51 registry VALIDATION_REFUSAL_DIVERGENCES"
provides:
  - "app/pages/identifiers.py: PostIdPath, PostIdForm, OptionalPostIdForm (no framework bound) and id_in_column(value, *, optional=False)"
  - "Catalogue rule test_every_post_identifier_is_checked_before_its_first_use: a POST-alias parameter must be read first as an argument of id_in_column; POST alias allowed only on POST-only routes"
  - "Four schedule POST handlers check identifiers first and answer out-of-column values on their not-found/foreign branch"
  - "Window 51: seven schedules entries lifted by work, VALIDATION_REFUSAL_DIVERGENCES_DECLARED 23 -> 16"
affects: [11-03, 11-04, 11-05, 11-06, 11-07, 11-09, window-51, admin, account_groups, accounts, ads, history]

actuals:
  tokens: 20878
  tasks: 2
  commits: 4
plan_head_before: 849fa13b5d252caa6b05eda350e639ba08a31f3f

tech-stack:
  added: []
  patterns:
    - "POST identifier bound inside the handler: first read of the parameter is id_in_column(...), computed before any query; out-of-column value rides the same branch as a missing row"
    - "First-use analyser: earliest ast.Name load by (lineno, col_offset) in the handler body must be a direct argument of id_in_column"
    - "Same-branch assertion by equality with an in-column missing id (status, location, HX-Location), not by a literal address"

key-files:
  created: []
  modified:
    - app/pages/identifiers.py
    - app/pages/schedules.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_confirm_delete_transport.py

key-decisions:
  - "id_in_column is the single project helper for the in-handler bound (D-07); _ad_id_from_form moved onto it too"
  - "_ownership_verdict takes ad_usable/account_usable flags computed by the handler: unusable ad -> OWNERSHIP_AD_DENIED without a query, unusable account -> OWNERSHIP_ACCOUNT_DENIED after confirming the ad, without an account query"
  - "ID_MAX stays imported in app/pages/schedules.py (noqa F401) because two test modules import it from there; bounded aliases dropped from that import"
  - "Adjacency antivacuum re-based on SQL statements (schedules.id lookup present at ID_MAX, absent at ID_MAX+1) because D-07 makes the two outcomes equal by design"

patterns-established:
  - "POST_ALIAS_ROOTS_DECLARED read from identifiers.py by 'declarator without ge/le', not by name prefix"
  - "Registry numbers moved only after the reddened rule printed the measured value (stало 16, а объявлено 23)"

requirements-completed: [FORM-08]

coverage:
  - id: D1
    description: "id_in_column and three POST aliases in app/pages/identifiers.py; shared IdPath/IdForm/OptionalIdForm unchanged"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_post_identifier_is_checked_before_its_first_use"
        status: pass
      - kind: other
        ref: "grep -cE '^(IdPath = Annotated\\[int, Path\\(ge=1, le=ID_MAX\\)\\]|IdForm = Annotated\\[int, Form\\(ge=1, le=ID_MAX\\)\\])$' app/pages/identifiers.py -> 2"
        status: pass
    human_judgment: false
  - id: D2
    description: "Catalogue rule requires check-at-first-use on POST and reddens on a check below select and on a POST alias on a GET route"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_control_a_check_below_the_first_use_reddens_the_catalogue_rule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_control_a_post_alias_on_a_get_route_reddens_the_catalogue_rule"
        status: pass
    human_judgment: false
  - id: D3
    description: "Out-of-column identifiers (2147483648, 25 and 26 nines) on the five schedule inputs answer exactly like an in-column missing id on both transports; live values still execute"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_no_schedule_route_answers_with_a_handler_failure_on_an_out_of_range_identifier"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_the_column_bound_admits_its_own_value_and_refuses_the_next_one"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[schedules_update-правка расписания — идентификатор вне колонки при своём объявлении]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_confirm_delete_transport.py#test_an_unusable_path_identifier_never_reaches_the_database"
        status: pass
    human_judgment: false
  - id: D4
    description: "Window 51 registry: seven schedules entries removed, declared count 16, completeness by measure green"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_framework_bounded_input_is_declared_as_a_divergence"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_validation_refusal_divergences_is_declared"
        status: pass
    human_judgment: false
  - id: D5
    description: "JSON-API app/routes/ 422 contract untouched"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_identifier_bounds.py"
        status: pass
    human_judgment: false

duration: 29min
completed: 2026-09-15
status: complete
---

# Phase 11 Plan 02: In-handler identifier bound for schedules (window 51, D-07) Summary

**One project helper `id_in_column` plus three unbounded POST aliases; the four schedule POST handlers check each identifier at first use and send out-of-column values down their own not-found branch, guarded by an AST first-use rule; window 51 drops from 23 to 16.**

## Performance

- **Duration:** 29 min
- **Started:** 2026-09-15T20:17:22Z
- **Completed:** 2026-09-15T20:46:01Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `app/pages/identifiers.py`: `PostIdPath`, `PostIdForm`, `OptionalPostIdForm` and `id_in_column`, with comments on why the bound moved inside (D-07), what a handler owes, and why GET keeps the bounded aliases. The "boundary at the application edge" paragraph gets a generation note instead of being erased. The docstring names the type-parsing boundary (non-integer tokens, plan 11-07).
- Catalogue rule `test_every_post_identifier_is_checked_before_its_first_use`:
  - POST aliases are recognised as integers, so `CATALOGUE_UNIVERSE_DECLARED` stays at 35.
  - `POST_ALIAS_ROOTS_DECLARED = 3` is read from the module.
  - The first textual load of the parameter must be an argument of `id_in_column`.
  - Two synthetic controls redden: a check below `select`, and a POST alias on a GET route. A check at first use stays silent.
- `schedules_create`, `schedules_update`, `schedules_toggle` and `schedules_delete` compute `id_in_column` before any query:
  - An out-of-column `schedule_id` skips the lookup and lands on "row missing". With its own ad, `schedules_update` lands on `SCHEDULE_AD_MISSING`; otherwise it goes to `/schedules`.
  - An unusable `ad_id` goes to `/schedules`.
  - An unusable `account_id` goes to the account-gone branch once the ad is confirmed.
- Window 51: seven `schedules` entries removed from `VALIDATION_REFUSAL_DIVERGENCES`. The count moved 23 -> 16, and the chronicle quotes the reddened rules. `LIFTING_CONDITION_VALIDATION_REFUSAL` is unchanged.

## Task Commits

1. **Task 1 RED: catalogue rule for POST identifiers checked before first use** - `bd6cf12` (test)
2. **Task 1 GREEN: POST aliases and id_in_column** - `a51b284` (feat)
3. **Task 2 RED: out-of-column schedule ids on the not-found branch** - `a5d90bf` (test)
4. **Task 2 GREEN: schedule handlers check first, window 51 23 -> 16** - `5f08837` (feat)

No REFACTOR commits were needed.

## TDD Gate Compliance

- **Task 1 RED:** the target was `test_every_post_identifier_is_checked_before_its_first_use`.
  - Output: `3 failed, 17 deselected`, rc=1.
  - Causal literal: `корневых POST-псевдонимов в app/pages/identifiers.py найдено 0 ([]), объявлено 3`.
  - Checker verdict: `RED_EVIDENCE_OK` (`target_test_failed`).
- **Task 2 RED:** the target was `test_no_schedule_route_answers_with_a_handler_failure_on_an_out_of_range_identifier`.
  - Output: `4 failed, 7 passed`, rc=1.
  - Causal literals: `(422, None, None)`, `путь деградации ответил 422 вместо 302`, and `снято (422, '')`.
  - Checker verdict: `RED_EVIDENCE_OK`.
- **How the records were built:** the checker parses node-style TAP, so each record's TAP text was derived line for line from pytest's JUnit XML of the same run. The converter script lived in the session scratchpad and nothing was hand-written.
- **GREEN runs:**
  - Task 1: `tests/test_pages/test_identifier_bounds.py` 20 passed and `test_htmx_gates.py` 43 passed. Window 51 was unmoved at that point.
  - Task 2: the plan's verify command over five files gave 203 passed, and `tests/test_routes/test_schedules_api_identifier_bounds.py` gave 19 passed.

## Files Created/Modified

- `app/pages/identifiers.py` - POST aliases, `id_in_column`, generation note
- `app/pages/schedules.py` - module aliases on POST aliases, first-use checks in four handlers, `_ownership_verdict` usability flags, `_ad_id_from_form` on the helper, import generation note
- `tests/test_pages/test_identifier_bounds.py` - POST alias resolver, first-use analyser, new rule and controls, alias antivacuum re-based
- `tests/test_pages/test_editor_schedules.py` - out-of-range rule compares with an in-column missing id on both transports; adjacency rule observes schedule lookups
- `tests/test_pages/test_htmx_gates.py` - seven entries removed, count 16 with chronicle, header generation note
- `tests/test_pages/test_htmx_post_pairs.py` - out-of-column edit case, count 6 -> 7
- `tests/test_pages/test_confirm_delete_transport.py` - address-axis outcomes for `9…9`, `-1`, `0` moved from 422 to the not-found fragment

## Decisions Made

- The flags are computed in the handler and passed to `_ownership_verdict`. They are not re-checked inside it, because the catalogue rule requires the first read of the parameter to be the `id_in_column` argument in the handler body.
- `ID_MAX` is kept in the `schedules.py` import (`noqa: F401`) so the two test modules that import it from there are not touched. The executable use is gone, and the comment records both halves of the reason.
- A POST-alias parameter that is never read counts as unchecked. The rule treats "no check" as "no bound", whether or not the value reaches a query today.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated the delete address-axis expectations in a file outside the plan's list**
- **Found during:** Task 2
- **Issue:** `test_an_unusable_path_identifier_never_reaches_the_database` pinned `422` for `9…9`, `-1` and `0` on `POST /schedules/{id}/delete`. D-07 moves those values to the not-found branch by design.
- **Fix:** Those three outcomes now expect `(200, "")`, the same as `1_0`. `1e3` stays `422` because it is refused by type parsing, outside D-07. A generation note is added and the prior paragraphs are kept.
- **Files modified:** tests/test_pages/test_confirm_delete_transport.py
- **Committed in:** a5d90bf

**2. [Rule 1 - Bug] Adjacency antivacuum rebuilt, then its statement filter narrowed**
- **Found during:** Task 2
- **Issue:** The old antivacuum required `at_bound != past_bound`, which D-07 makes impossible. My first statement filter (`"schedules" in statement`) also matched the navigation counters query (`… AS schedules`) that runs on every authenticated request.
- **Fix:** The antivacuum now asserts that a `schedules.id = ` lookup runs at `ID_MAX` and none runs at `ID_MAX + 1`.
- **Files modified:** tests/test_pages/test_editor_schedules.py
- **Committed in:** a5d90bf (rule), 5f08837 (filter)

**3. [Rule 3 - Blocking] Inherited-alias antivacuum moved to POST alias resolution**
- **Found during:** Task 2
- **Issue:** `test_the_recognised_bound_aliases_come_from_a_single_place` required bounded-alias resolution to find an inherited name. After D-07 the only inheritors (`ScheduleIdPath`, `AdIdForm`, `AccountIdForm`) resolve through POST aliases, and the check failed with `assert 3 > 3`.
- **Fix:** The test now asserts that those three names are inherited through bounded or POST alias resolution, with a generation note.
- **Files modified:** tests/test_pages/test_identifier_bounds.py
- **Committed in:** 5f08837

**4. [Plan reference] No schedule rows exist in the `test_identifier_bounds.py` matrix**
- **Found during:** Task 2
- **Issue:** The plan's behaviour item 2 mentions rows for schedule inputs in `test_every_bounded_input_refuses_a_value_outside_the_column`. `BOUNDED_ENTRIES` has none, because schedule inputs are covered by `test_editor_schedules.py`.
- **Fix:** Nothing was changed there. The behaviour is asserted by the rewritten out-of-range rule and the pair case.

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking) plus 1 plan-reference note.
**Impact on plan:** All were needed for the D-07 change to be observable without weakening the guarded properties. No scope creep; `app/routes/` is untouched.

## Issues Encountered

- `gsd-tools check tdd-red-evidence` reads camelCase fields and parses node TAP. The first record, built from plain pytest text, came back `INVALID_RED (invalid_record)`. I rebuilt it from JUnit XML of a re-run in the same RED state.
- The host is memory-constrained, but no test run was killed. Every run reported here finished in the foreground with the counts quoted.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The 16 remaining window 51 entries (`admin` x6, `account_groups` x4, `accounts` x3, `ads` x2, `history` x1) can move to `PostIdPath`/`PostIdForm` and `id_in_column`. The catalogue rule already covers them once they switch.
- On the htmx path, the non-integer path token still answers with framework `{"detail": …}` until plan 11-07 (T-07-13).

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-15*

## Self-Check: PASSED

- Modified files exist on disk: app/pages/identifiers.py, app/pages/schedules.py, and the five test files listed above.
- Commits found in git log: bd6cf12, a51b284, a5d90bf, 5f08837 (`git rev-list --count 849fa13..HEAD` = 4).

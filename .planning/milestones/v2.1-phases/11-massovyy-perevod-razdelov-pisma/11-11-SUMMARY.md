---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 11
subsystem: ui
tags: [jinja2, fastapi, admin, identifiers, d-07, window-51, tdd, htmx]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-02: PostIdPath and id_in_column, first-use catalogue rule; 11-06: window 51 at 14"
provides:
  - "app/templates/admin/includes/user_actions.html, user_block_badge.html, user_access_tile.html: the only markup source for the admin user card's action block, block badge and access tile"
  - "Six admin POST handlers on PostIdPath, id_in_column after the origin check and before the first query"
  - "Window 51: VALIDATION_REFUSAL_DIVERGENCES_DECLARED 14 -> 8, no admin.py entries"
  - "Identifier matrix field `outside`: declared outcome for an out-of-column value (422 or 'code location' of the not-found branch)"
affects: [11-12, 11-13, 11-14, window-51, admin]

actuals:
  tokens: 12326
  tasks: 2
  commits: 3
plan_head_before: cfdbb83ac0644e43d1ff30c7fba175b24c97044c

tech-stack:
  added: []
  patterns:
    - "Byte-identical extraction check: render the page in every state before and after, diff the HTML"
    - "Included template keeps its original indentation and whitespace markers because they reach the output"
    - "Matrix row for a POST-alias input declares its not-found outcome (`302 /admin/users`) instead of being removed"

key-files:
  created:
    - app/templates/admin/includes/user_actions.html
    - app/templates/admin/includes/user_block_badge.html
    - app/templates/admin/includes/user_access_tile.html
  modified:
    - app/templates/admin/user_detail.html
    - app/pages/admin.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_templates/test_components.py

key-decisions:
  - "Only the CONTENT moves: the data-actions wrapper and the tile's card_open/card_close stay on the page; no ids, no htmx, no form_wrapper (planned for 11-12/11-13)"
  - "Matrix rows for the six inputs are kept with an `outside` outcome instead of being removed as in plan 11-06; the degradation address survives the later transport conversions"
  - "The six-admin-entries control is retargeted to the most populated module by measurement instead of being deleted"

patterns-established:
  - "Extraction proof by rendered-output diff over all states of the page"

requirements-completed: [FORM-03, FORM-08]

coverage:
  - id: D1
    description: "User card action block, block badge and access tile render from three included templates; page output unchanged byte for byte in four states"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "scratch snapshot of GET /admin/users/{id} (plain, blocked+comped, closed access, self) before and after — cmp identical after normalising the trial-expiry clock minute"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_admin_panel.py tests/test_pages/test_blocked_user.py tests/test_pages/test_free_access.py tests/test_templates/ tests/test_pages/test_responsive_markup.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Six admin POST inputs answer an out-of-column identifier on their not-found branch without reaching a query"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_post_identifier_is_checked_before_its_first_use"
        status: pass
    human_judgment: false
  - id: D3
    description: "Window 51 registry has no admin.py entries and declares 8"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_framework_bounded_input_is_declared_as_a_divergence"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_validation_refusal_divergences_is_declared"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_dropping_a_whole_module_reddens_the_completeness_rule"
        status: pass
    human_judgment: false

duration: 28min
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 11: Admin user card includes and window 51 for admin Summary

**The admin user card's action block, block badge and access tile now render from three included templates, and the page output is byte-identical in four states. Six admin POST handlers check their identifier with `id_in_column` before any query, which takes window 51 from 14 to 8.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-09-16T17:02:10Z
- **Completed:** 2026-09-16T17:30:00Z
- **Tasks:** 2
- **Files modified:** 8 (3 created)

## Accomplishments

- **The three includes are copied word for word.**
  - The content of `<div data-actions>` went to `admin/includes/user_actions.html`. That is four forms: the free-access toggle, the block toggle, and the impersonate and delete triggers.
  - The badge went to `user_block_badge.html` and the access tile's content to `user_access_tile.html`.
  - Each file opens with a Jinja comment naming its context (`target_user`, `target_access`, `user`). It also says the file is the single source for the page and for the toggle responses of plans 11-12 and 11-13.
  - The confirmation panels (`modal()`) stay on the page, outside the block.
- **I proved the extraction changes nothing rather than arguing it.** A temporary test rendered `GET /admin/users/{id}` in four states, before and after the change. The states were a plain user, a blocked user with free access, a user whose access is closed, and the admin's own card. The outputs matched byte for byte. The only difference was the clock minute inside the trial-expiry date, because the two runs were a minute apart. The temporary test was deleted and never committed.
- **Six handlers moved to `PostIdPath`:** `admin_restart_worker`, `admin_drop_task`, `admin_toggle_free_access`, `admin_impersonate`, `admin_toggle_block` and `admin_delete_user`.
  - In each one, the first use of the identifier is `id_in_column`. It sits after `is_same_origin` and before the first `db.get`.
  - An out-of-column value takes the handler's existing not-found branch:
    - the four user routes go to `/admin/users`;
    - restart goes to `/admin/workers`;
    - drop goes to `/admin/queue?result=unknown_account`.
  - The bare `403` on an origin failure is unchanged (D-08).
- **Window 51 went from 14 to 8.** The six `admin.py` entries were removed using the exact keys from the completeness rule's complaints. The count rule printed «расхождений формы отказа валидации стало 8, а объявлено 14» before I changed the number. The count's history log got a new entry.

## Task Commits

1. **Task 1: move the card state into included templates** - `34a6a3a` (refactor)
2. **Task 2 RED: the matrix expects the not-found branch on six admin inputs** - `3c765c0` (test)
3. **Task 2 GREEN: six admin inputs check the identifier on first use, window 51 14 -> 8** - `1b1d629` (feat)

## TDD Gate Compliance

- **RED** (`3c765c0`): the target was `test_every_bounded_input_refuses_a_value_outside_the_column`.
  - Output: `1 failed, 20 deselected`, rc=1.
  - All 18 disagreement lines are for the six admin inputs (6 inputs × 3 values), each in the form `… ← 2147483648 = 422 (ожидалось 302 /admin/users; …)`. No other input disagreed.
  - The cause is in the code: the handlers still had `user_id: IdPath` and `account_id: IdPath`.
  - The record was built mechanically from the run's JUnit XML. `check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`).
- **GREEN** (`1b1d629`): the plan's verify set passed with `254 passed`. It covers `test_identifier_bounds.py`, `test_htmx_gates.py`, `test_confirm_delete_transport.py` and `test_admin_panel.py`.
- No REFACTOR commit.
- Task 1 is not a TDD task. It is a pure restructure, checked by the rendered-output diff and by the existing suites, whose expectations did not change.

## Files Created/Modified

- `app/templates/admin/includes/user_actions.html`, `user_block_badge.html` and `user_access_tile.html` (new): the card state markup, each with a header comment.
- `app/templates/admin/user_detail.html`: three `include` lines in the old places. The `button` import was narrowed to `link_button`, since `button` is no longer used on the page.
- `app/pages/admin.py`: the `PostIdPath` / `id_in_column` import and six first-use checks.
- `tests/test_pages/test_identifier_bounds.py`:
  - a new field on `_BoundedEntry`, `outside`: the declared outcome for an out-of-column value;
  - `_entry_outcome(..., with_location=)`;
  - six admin rows with the not-found outcome;
  - generation notes.
- `tests/test_pages/test_htmx_gates.py`:
  - six entries removed, with a note left in their place;
  - the count set to 8, with a history entry;
  - the module control retargeted.
- `tests/test_templates/test_components.py`: the `ROW_DELETE_SITES` entry for the admin delete form now names `admin/includes/user_actions.html`. The number of places is unchanged.

## Decisions Made

- Only the content moved. The permanent wrapper `id`, htmx attributes and `form_wrapper` belong to plans 11-12 and 11-13. The indentation and whitespace markers were copied from the old place because they reach the output.
- The six matrix rows were kept with an `outside` outcome instead of being removed as in plan 11-06. The plan's scope note wants the matrix to stay stable through the later transport conversions, which keep the degradation address. The adjacency rule can no longer tell the two outcomes apart for these inputs, since D-07 makes them equal. That is written into the rule's docstring, and the AST first-use rule covers the ordering.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `ROW_DELETE_SITES` named the old file of the admin delete form**
- **Found during:** Task 1 (the full `tests/test_templates/` run the orchestrator asked for)
- **Issue:** `test_every_row_delete_site_keeps_a_real_form` reads template source by file and found 0 delete forms in `admin/user_detail.html`, because the form moved into the include as the plan says.
- **Fix:** The entry now names `admin/includes/user_actions.html`, with a comment saying the place moved and was neither added nor removed. `ROW_DELETE_PLACES` is unchanged.
- **Files modified:** tests/test_templates/test_components.py (not in the plan's file list)
- **Verification:** `tests/test_templates/test_components.py` 90 passed; `tests/test_templates/` 218 passed.
- **Committed in:** 34a6a3a

**2. [Rule 3 - Blocking] The control for the six admin entries lost its subject**
- **Found during:** Task 2 GREEN
- **Issue:** `test_control_dropping_the_admin_entries_reddens_the_completeness_rule` picked entries by the `app/pages/admin.py::` owner and asserted there were exactly six. Removing the entries by work left nothing to pick.
- **Fix:** It is now `test_control_dropping_a_whole_module_reddens_the_completeness_rule`. It picks the module with the most entries by measurement, requires at least two, and keeps the same three assertions. A generation note is left in place of the old constant.
- **Files modified:** tests/test_pages/test_htmx_gates.py
- **Verification:** `test_htmx_gates.py` green inside the 254-passed run.
- **Committed in:** 1b1d629

---

**Total deviations:** 2 auto-fixed (2 blocking).
**Impact on plan:** Both are test bookkeeping forced by the planned moves. No product behaviour beyond the plan changed.

## Issues Encountered

- I started a wider run of `tests/test_pages/` plus `tests/test_admin.py` in the background as an extra check beyond the plan. It was on pace to take well over an hour on this host, so I stopped it myself at about 4% with no failures reported. **It did NOT pass. It was not completed.** The full suite is left to the orchestrator's post-plan gate.
- The runs above were at 17:0x–17:3x UTC, outside the known 00:00–05:00 red window of `test_the_overview_error_number_matches_the_users_own_dashboard`. `test_admin_panel.py` was fully green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 11-12 (block) and 11-13 (free access) can now render their fragments from the three includes.
- Their pair-module case for an out-of-column value can reuse the matrix outcome `302 /admin/users` as the degradation half.
- The address of the drop not-found branch (`?result=unknown_account`) is still owned by plan 11-14.
- Window 51 has eight entries left: `account_groups` ×4, `accounts` ×3, `history` ×1.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

## Self-Check: PASSED

- FOUND: app/templates/admin/includes/user_actions.html, user_block_badge.html, user_access_tile.html
- FOUND commits: 34a6a3a, 3c765c0, 1b1d629

---
phase: 18-ruchnaya-pravka-nomera
plan: 08
subsystem: ui
tags: [htmx, oob-swap, jinja2, fastapi, tdd, notices]

requires:
  - phase: 18-ruchnaya-pravka-nomera
    provides: "18-02 phone form route and phone_response.html; 18-03 notices registry"
provides:
  - "account_groups/partials/phone_error_response.html: the 422 answer of the phone form for the htmx layer (bare form include plus an empty content-swap block on #notice)"
  - "OOB_BLOCKS 25 with a chronicle line for plan 18-08"
affects: [18-05, 18-07, phase-18-verification]

actuals:
  tokens: 3000
  tasks: 1
  commits: 2
plan_head_before: 889019ccfc2d072f8731fb63506b5aea8927c28f
plan_head_after: 7417bd03de6170c67155ce9a28cced674aba8d3c

tech-stack:
  added: []
  patterns:
    - "A 422 fragment may carry an empty out-of-band content swap on the polite notice area to drop a stale success banner, without touching the shared respond_field_error layer"

key-files:
  created:
    - app/templates/account_groups/partials/phone_error_response.html
  modified:
    - app/pages/account_groups.py
    - tests/test_pages/test_account_phone_form.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "The stale banner is cleared by the 422 response itself (empty innerHTML swap on #notice), not by client script: the app has no own JS and inline htmx handlers are forbidden by a gate"
  - "respond_field_error stays untouched; only the phone form's _error_fragment builder switches to the new file"
  - "The persistent #notice-alert area is not touched by this response"

patterns-established:
  - "Out-of-band block for a notice area swaps CONTENT (innerHTML:#notice), never the node, and is empty when it only clears"

requirements-completed: [PHONE-09]

coverage:
  - id: D1
    description: "A 422 htmx answer of the phone form clears the previous success banner: exactly one empty innerHTML:#notice block, no text, no outcome code, no digits of the number, nothing on #notice-alert"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_a_422_htmx_answer_clears_the_previous_notice"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_an_invalid_number_answers_422_with_the_echo_on_both_transports"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exactly one declared gate count moved: OOB_BLOCKS 24 -> 25 set by running the reddened rule; all other declared counts unmoved (2228 tests green across template gates, htmx gates, post pairs, validation sink, hx-location destinations, shell, notices, phone gates)"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_number_of_oob_blocks_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D3
    description: "In a JS browser, after 'Номер сохранён.' and a following invalid input 'abc' the green banner disappears and the error stands under the field, with no alert-area banner; without JS the 422 page shows no banners"
    verification: []
    human_judgment: true
    rationale: "The suite does not execute JS; applying an out-of-band swap is observable only in a browser (human-check in the plan, left to /gsd-verify-work 18)"

duration: 27min
completed: 2026-11-22
status: complete
---

# Phase 18 Plan 08: Clear the previous banner on a 422 Summary

**The phone form's 422 answer for htmx now carries an empty content-swap block on the polite `#notice` area, so a stale "Номер сохранён." banner no longer sits above a fresh error; the shared 422 layer is untouched and exactly one gate count (`OOB_BLOCKS` 24 -> 25) moved.**

## Performance

- **Duration:** ~27 min (the wall clock includes waiting for the shared pytest lock)
- **Completed:** 2026-11-22T06:41:54Z
- **Tasks:** 1 (tracer, TDD)
- **Files modified:** 4 (1 created)

## Accomplishments

- New `account_groups/partials/phone_error_response.html`: the bare `phone_form.html` include (so the swap target and the value echo stay in the included template, G-11) plus an empty `hx-swap-oob="innerHTML:#notice"` block.
- `_error_fragment` in `app/pages/account_groups.py` renders it; `respond_field_error` and its 28 sink routes are unchanged. Without JS the 422 page is the same as before: both notice areas empty.
- Tracer test and a rewritten assertion of test 4 pin the contract; `OOB_BLOCKS` moved by running the reddened rule (verbatim: "внеполосных блоков найдено 25, объявлено 24") with a chronicle line.

## TDD

### RED (`51b5a58b`)

- Wrote `test_a_422_htmx_answer_clears_the_previous_notice` (valid save with `HX-Request`, then `abc`; the 422 body must hold exactly one oob block with value `innerHTML:#notice`, empty, no `#notice-alert`, no outcome codes or digits) and rewrote the test 4 assertion that used to say "no oob blocks on 422" into "the only oob block is the empty `#notice` swap".
- Failed exactly as planned: 2 failed, 17 passed — the target test and test 4. Three matches in the target run output: `FAILED tests/test_pages/test_account_phone_form.py::test_a_422_htmx_answer_clears_the_previous_notice`, the `2 failed` summary, the causal literal `422 с JS не снимает прежнюю плашку`.
- Evidence: pytest JUnit XML, record `{command, exitCode, targetTest, output, ...}` in `.gsd/tdd-evidence/18-08/` (ignored, removed with the worktree); `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`, format junit, no report errors).
- Semantic assessment: the target test executed and failed on the planned assertion (`assert [] == ['innerHTML:#notice']` — the 422 body had no oob block), not on a syntax, import or fixture fault; the second failure is the intended rewritten assertion of test 4.

### GREEN (`7417bd03`)

New response file, builder switch and the `OOB_BLOCKS = 25` line with its chronicle in one commit (`git show --stat` names all three), so the tree is never red between commits.

### REFACTOR

None needed.

## Task Commits

1. **Task 1 (tracer): 422 with JS clears the previous success banner** - RED `51b5a58b` (test), GREEN `7417bd03` (feat)

**Plan metadata:** committed with this SUMMARY (docs).

## Files Created/Modified

- `app/templates/account_groups/partials/phone_error_response.html` - 422 answer for the htmx layer: form include plus the empty notice-clearing block
- `app/pages/account_groups.py` - `_error_fragment` renders the new file; docstring explains why the shared layer is unchanged
- `tests/test_pages/test_account_phone_form.py` - `_OobBlocks` helper, tracer test, rewritten test 4 assertion
- `tests/test_templates/test_htmx_markup_gates.py` - `OOB_BLOCKS` 25 and its chronicle line

## Decisions Made

- Cleared by the response, not by client script (no own JS; inline htmx handlers forbidden by a gate; client state on the swap target reddens G-12).
- Shared `respond_field_error` unchanged; `#notice-alert` untouched (clearing another source's refusal would be a second decision).
- One task, one GREEN commit: the new file reddens test 4 and `OOB_BLOCKS`, so all three must land together.

## Verification

Run under the shared pytest lock, one invocation, `-p no:randomly`: `tests/test_pages/test_account_phone_form.py`, all of `tests/test_templates/`, `tests/test_pages/test_account_groups.py`, `test_notices_surface.py`, `test_notices_registry.py`, `test_htmx_gates.py`, `test_htmx_post_pairs.py`, `test_htmx_validation_sink.py`, `test_hx_location_destinations.py`, `test_shell.py`, `test_impersonation_gate.py`, `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py` — **2228 passed**. No declared-count refusal; no gate count other than `OOB_BLOCKS` moved. `compileall -q app main.py tests` clean. Acceptance greps: `phone_error_response.html` in `account_groups.py` = 1; `innerHTML:#notice"` in the new file = 1; `OOB_BLOCKS = 25` = 1; `status_code == 302` in the phone-form test = 2 (unchanged).

Not run by me (left to the orchestrator's post-merge suite): the remaining names of the plan's wave gate command (`test_identifier_bounds`, `test_write_path_invariants`, `test_origin_guard_on_destructive_routes`, `test_phone_writer_runtime_guard`, `test_responsive_markup`) and `tests/test_planning`; `graphify update .` was not run.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Wall-clock time was dominated by waiting for the shared pytest lock while sibling executors ran.

## Known Stubs

None.

## Threat Flags

None. T-18-19 (XSS via echo) mitigated: the new file prints no value of its own, the echo lives in the included form with auto-escaping, and test 4's hostile-value case goes with `HX-Request` so it renders the new file. T-18-20 (leak in the clearing block) mitigated: the block is empty and the tracer asserts no text, children, outcome codes or digits.

## TDD Gate Compliance

`test(18-08)` commit `51b5a58b` precedes `feat(18-08)` commit `7417bd03` (descends from it); no REFACTOR commit. Gate sequence satisfied.

## Human verification outstanding

Per the plan, the manual half of OBS-422 (a JS browser: save a valid number, then `abc`; the green banner disappears, the error stands under the field, no alert-area banner; without JS the 422 page has no banners) is confirmed only by a human walk-through in `/gsd-verify-work 18`. PHONE-09 stays `Pending` in REQUIREMENTS.md; `requirements mark-complete` was not run.

## Next Phase Readiness

Plan 18-05 (focus after the response, hint without example repeat) edits the same `app/pages/account_groups.py` and `tests/test_pages/test_account_phone_form.py` and can now build on `_oob_blocks` and the new response file.

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-22*

## Self-Check: PASSED

- FOUND: app/templates/account_groups/partials/phone_error_response.html
- FOUND commits: 51b5a58b (RED), 7417bd03 (GREEN)

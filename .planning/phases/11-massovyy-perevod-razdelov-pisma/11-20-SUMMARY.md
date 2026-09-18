---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 20
subsystem: testing
tags: [htmx, gate-02, ast-traversal, pytest, response-layer, planning-records, broken-windows]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "pair registry POST_PAIR_CASES (48 cases, plans 11-01…11-19), closure over converted handlers, NOT_YET_CONVERTED = 14, window 51 closed by work (146d96c)"
provides:
  - "AST traversal of tests/ that attributes every `status_code == 302` assertion on a POST to a handler through the app's own route table, and reddens an unpaired one with file:line"
  - "PAIRED_302_ASSERTIONS_DECLARED = 158, set by the run, with the 160 / ~136 / 157 chronicle"
  - "UNATTRIBUTED_302_ASSERTIONS: 12 assertions the traversal cannot attribute, named per function with reader-named handlers that must also be paired"
  - "app/pages/htmx.py docstrings re-measured after the phase: 15 fragment calls, 1 with an outcome code, references by symbol"
  - "ROADMAP Phase 11 chronicles for criteria 1, 3, 4, 5, the Research line and the partial resolution of window 63; REQUIREMENTS chronicles at FORM-03/FORM-04 and GATE-02"
  - "window 51 marked fixed by the registry command; window 63 stays open"
affects: [phase-11-verification, phase-13, phase-14, phase-15]

actuals:
  tokens: 26500
  tasks: 3
  commits: 4
plan_head_before: 860e5f57cfff8b6ef7bbf515ec77c68880966880

tech-stack:
  added: []
  patterns:
    - "Assertion attributed to a handler by the ASSEMBLED app route table (create_app().routes), not by decorator text, so router prefixes come from the app itself"
    - "Non-vacuity by two independent instruments: AST-visited 302 comparisons == tokenize-level `status_code == 302` count"
    - "Unattributable assertions are declared by owner function with reader-named handlers, and a stale declaration reddens"

key-files:
  created: []
  modified:
    - tests/test_pages/test_htmx_post_pairs.py
    - app/pages/htmx.py
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/WINDOWS.md

key-decisions:
  - "GATE-02 number is 158, set by the traversal run (`утверждений 302 о переведённых обработчиках 158, объявлено 0`); 160, ~136 and 157 are recorded as forecasts that went stale, not errors"
  - "The traversal follows helpers through their `return` with call arguments bound to parameters (one `_post(client, \"/billing/subscribe\", …)` layer), so wrapped POSTs are counted instead of dropped; the D-14 universe written in the plan covered only direct `.post(` bindings"
  - "Assertions the traversal cannot attribute (registry halves on `degraded.url`, tuple-unpacked codes, responses stored in a dict, direct `respond()` unit calls) are declared in UNATTRIBUTED_302_ASSERTIONS with the handlers a reader names; those handlers must be paired too, and a stale entry reddens"
  - "Window 63 stays `open`: D-08 closed only its 'decision on form' part; the partial resolution is a ROADMAP chronicle, not `waive`/`fixed`"
  - "Requirement checkboxes and statuses untouched: GATE-02, FORM-03, FORM-04 stay Pending until phase verification"

patterns-established:
  - "302 traversal rule: every 302 assertion on a converted handler is paired or the rule names file:line → handler"

requirements-completed: [GATE-02, FORM-03, FORM-04]

coverage:
  - id: D1
    description: "Every `status_code == 302` assertion on a POST to a converted page handler has a pair; an unpaired one reddens with file and line"
    requirement: GATE-02
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_302_assertion_on_a_converted_handler_is_paired"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_control_an_unpaired_302_assertion_reddens_the_traversal"
        status: pass
    human_judgment: false
  - id: D2
    description: "The number of such assertions is declared (158) and set by the run; GET redirects and NOT_YET_CONVERTED handlers stay out; an empty tests root reddens the number rule"
    requirement: GATE-02
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_the_number_of_paired_302_assertions_is_the_declared_one"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_control_a_get_or_unconverted_302_stays_out_of_the_count"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_control_an_empty_tests_root_reddens_the_number_rule"
        status: pass
    human_judgment: false
  - id: D3
    description: "htmx.py docstrings re-measured: 15 fragment calls / 1 with an outcome code, named by handler and file; stale «ТРИ» / «НИ ОДИН» wording named as outdated; glue-notice safety boundary re-checked"
    verification:
      - kind: other
        ref: "uv run python -c \"…respond fragment/notice AST count…\" → 15 1; grep -c 'schedules.py:1240' app/pages/htmx.py → 0"
        status: pass
    human_judgment: true
    rationale: "Docstring prose accuracy (the boundary re-check reading of builders) is a reader judgment; automation only proves the numbers and the absence of line-number references"
  - id: D4
    description: "Milestone records carry reading chronicles (criteria 1/3/4/5, Research line, FORM-03/FORM-04, GATE-02), window 51 fixed, window 63 open with the D-08 partial-resolution chronicle, no checkbox or status changed"
    requirement: FORM-03
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_planning/ -q"
        status: pass
    human_judgment: true
    rationale: "Whether the chronicles read the criteria correctly for the verifier is a human reading; the planning gates prove only record consistency"

duration: 56min
completed: 2026-09-17
status: complete
---

# Phase 11 Plan 20: 302-assertion traversal, response-layer docstrings, milestone chronicles Summary

**An AST traversal of `tests/` attributes each `status_code == 302` assertion on a POST to its handler through the assembled app route table and requires a pair for every converted handler — it set GATE-02 at 158 by run; `htmx.py` docstrings are re-measured (15 fragment calls, 1 with an outcome code) and the milestone records carry the phase's reading chronicles, with window 51 fixed and window 63 left open.**

## Performance

- **Duration:** 56 min
- **Started:** 2026-09-17T07:04:40Z
- **Completed:** 2026-09-17T07:59:52Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- **The GATE-02 number is 158, and the run set it.** On the tree of this plan the traversal saw 206 `status_code == 302` comparisons, and the separate token count also gave 206. 184 of them are about POSTs. 14 are out of the universe: all belong to `auth.py` handlers that are still in `NOT_YET_CONVERTED` (login 7, register complete 4, stop impersonation 2, password reset 1). 12 cannot be attributed and are declared by name. The remaining 158 are all paired.
- **An unpaired assertion reddens with its name.** A synthetic `resp = await client.post(f"/schedules/{schedule_id}/edit")` plus `assert resp.status_code == 302`, checked against the registry without the schedule-edit cases, gives `tests/test_synthetic_unpaired.py:5 → app/pages/schedules.py::schedules_update: утверждение 302 есть, пары нет`. With the full registry the complaint goes away, which proves the missing pair is what reddens it.
- **What stays out of the count is proven, not assumed.** A GET 302, a POST to `/login` and a POST reassigned to a GET before its assert are all left out. The converted toggle is counted. Putting the toggle back into `NOT_YET_CONVERTED` removes it from the count, so handlers from Phases 13–14 will join the count on their own.
- **The traversal is checked against the app's key form.** The page keys in the route table must equal `_post_handlers(_pages_sources())`, so an assertion cannot be attributed to the wrong handler.
- **The docstrings were re-measured against the tree.** The reproducible command prints `15 1`. `_glue_notice` now lists the fifteen calls in eleven handlers by name. The safety boundary was re-checked by reading the builders: there is no `BackgroundTask` anywhere in `app/`. One exception is named: the ad-creation fragment carries `HX-Push-Url`, but it gets no outcome code, so no notice is glued onto it.
- **The records carry the chronicles.** They cover criteria 1, 3, 4 and 5, the Research line and window 63 in ROADMAP, and FORM-03/FORM-04 and GATE-02 in REQUIREMENTS. The twelve handlers are named in words. No checkbox or status changed.

## Task Commits

1. **Task 1 RED: traversal rules against a stub** — `176601b` (test)
2. **Task 1 GREEN: traversal, 158 set by run** — `f7b05ec` (feat)
3. **Task 2: htmx.py docstrings re-measured** — `85c8b10` (docs)
4. **Task 3: milestone chronicles, window 51 fixed** — `0bcf895` (docs)

## TDD Gate Compliance

- **RED** (`176601b`): the tests were committed with `_post_302_assertions` as a stub returning `_Traversal(visited=0, records=())`. The causal literal is `"""RED (план 11-20, задача 1): обход ещё не написан."""`. The run gave `3 failed, 2 passed` for the three named rules:
  - `FAILED …::test_the_number_of_paired_302_assertions_is_the_declared_one`: `обход не встретил ни одного сравнения` and `обход разобрал 0 сравнений …, счёт по лексемам даёт 206`.
  - `FAILED …::test_control_an_unpaired_302_assertion_reddens_the_traversal`: `обход не назвал непарное утверждение tests/test_synthetic_unpaired.py:5: []`.
  - `FAILED …::test_control_a_get_or_unconverted_302_stays_out_of_the_count`: `assert 0 == 4`.
  - `check tdd-red-evidence` returned `RED_EVIDENCE_OK` for each of the three records. They were built from JUnit XML, with the converter using `is not None`.
- **GREEN** (`f7b05ec`): the first run after implementing named 16 unattributed assertions. Binding call arguments to helper parameters brought that to 12, and those 12 were declared. The number rule then reported `утверждений 302 о переведённых обработчиках 158, объявлено 0`, and the constant was set to 158. The module then ran `56 passed`.
- There is no REFACTOR commit. Extracting `_covered(cases)`, which the closure and the traversal now share, was part of RED.

## Files Created/Modified

- `tests/test_pages/test_htmx_post_pairs.py` — adds `_post_302_assertions`, `_post_route_table`, `_lexical_302_comparisons`, `_pairing_complaints`, `_number_complaints`, `UNATTRIBUTED_302_ASSERTIONS`, `PAIRED_302_ASSERTIONS_DECLARED = 158` with its chronicle, two rules and three controls. The module docstring now states the D-14 universe.
- `app/pages/htmx.py` — module docstring checked against the tree (five exit kinds, `respond_field_error` callers, twelve own exits). `_glue_notice` gets a new generation that lists the calls by name and re-checks the boundary. `respond` gets a fifth generation with `15 1`. Line numbers in the older quotes are now written with the word «строка».
- `.planning/ROADMAP.md` — five chronicle paragraphs under Phase 11's criteria.
- `.planning/REQUIREMENTS.md` — chronicles at FORM-03/FORM-04 (one paragraph under FORM-04 covering both) and at GATE-02.
- `.planning/WINDOWS.md` — window 51 set to `fixed` by `gsd-tools windows fixed 51` (open 76 → 75, fixed 10 → 11). The ledger has no note field. The fix is the work of plans 11-02…11-19, with the last five inputs in `146d96c` (plan 11-19), as named in commit `0bcf895`.

## Decisions Made

- **Window 63 is left `open` on purpose.** The partial resolution is the ROADMAP paragraph «Летопись окна 63 (частичное решение)». D-08, the owner's decision of 2026-09-14, covers only the "decision on form" part. The machine gate still counts exits, and `stop_impersonation` is Phase 14's case.
- **Helper-wrapped POSTs are counted, not dropped.** Following `return` with bound arguments raised the count from 154 to 158. It attributed four `subscribe_to_plan` assertions sent through `_subscribe` → `_post(client, "/billing/subscribe", …)`.
- **Direct `respond()` / `redirect_external()` unit calls are declared unattributed with no handlers.** They are not HTTP requests. Declaring them keeps them visible without adding a special case to the traversal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] The traversal no longer silently drops POSTs it cannot read**
- **Found during:** Task 1 (GREEN)
- **Issue:** The plan's universe only covered `name = <x>.post(<literal or f-string>)`. On the real tree that would silently skip 12 assertions on converted handlers: the confirm-delete registry halves on `degraded.url`, `_press_page_toggle` tuples, `nested["resp"]`, and helper and constant addresses such as `_restart_url(...)`, `QUEUE_DROP_URL.format(...)`, `START_URL` and `_post(client, "/billing/subscribe")`. That is exactly the T-11-36 "silent weakening" threat.
- **Fix:** Addresses are now resolved through module constants, `.format`, local assignments and helper returns, with call arguments bound. Anything still unreadable becomes a record with a reason. The pairing rule requires each such record to be declared in `UNATTRIBUTED_302_ASSERTIONS` with the handlers a reader names, and those handlers must be paired. A declaration with no matching assertion reddens.
- **Files modified:** tests/test_pages/test_htmx_post_pairs.py
- **Verification:** 206 AST comparisons equal 206 lexical ones; the pairing rule is green with 12 declared entries.
- **Committed in:** f7b05ec

**2. [Rule 2 - Missing critical] Added a fifth rule: an empty tests root reddens the number rule**
- **Found during:** Task 1
- **Issue:** The must_haves truth requires "пустой корень тестов краснеет правилом числа", but the plan's artifact list has no test for it.
- **Fix:** Added `test_control_an_empty_tests_root_reddens_the_number_rule`, which calls the same `_number_complaints` as the rule.
- **Committed in:** 176601b

**3. [Rule 1 - Bug] The ROADMAP Research-line chronicle uses the measured line**
- **Found during:** Task 3
- **Issue:** The plan said the header "moved to `app/pages/ads.py` строка 548". On this tree it is line 616, inside `_save_from_editor`.
- **Fix:** The chronicle records 522 (ROADMAP), then 548 (CONTEXT), then 616 (this tree), and also gives the reference by symbol.
- **Committed in:** 0bcf895

---

**Total deviations:** 3 auto-fixed (2 missing critical, 1 bug)
**Impact on plan:** All three make the gate or the record truthful. There is no scope creep: no production behavior changed.

## Issues Encountered

- The full suite took 37 min 28 s (`3406 passed`, exit 0) on this memory-constrained host. The run was not killed. The known night-window red did not appear, since the run was after 07:00 UTC.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 11 is complete (20 of 20) and ready for verification. Criteria 1, 3, 4 and 5 should be read together with their ROADMAP chronicles.
- Phases 13–14: when handlers leave `NOT_YET_CONVERTED`, `test_the_number_of_paired_302_assertions_is_the_declared_one` will redden with a larger number. That is movement, not a regression. Set the number by the run, and pair the handler first.
- Window 63 remains `open` for its remaining part: the exits are still counted, and `stop_impersonation` belongs to Phase 14.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-17*

## Self-Check: PASSED

- FOUND: tests/test_pages/test_htmx_post_pairs.py, app/pages/htmx.py, .planning/ROADMAP.md, .planning/REQUIREMENTS.md, .planning/WINDOWS.md
- FOUND commits: 176601b, f7b05ec, 85c8b10, 0bcf895 (and 146d96c named for window 51)
- Acceptance re-run: task 1 (constant line, single helper, 3 named passed, 56 collected), task 2 (0/0, `15 1`, compileall), task 3 (7 chronicle lines, one `PAIRED_302_ASSERTIONS_DECLARED` per file, 51 fixed / 63 open, no checkbox diff, planning rules 44 passed)

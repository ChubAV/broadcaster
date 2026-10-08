---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 07
subsystem: ui
tags: [htmx, fastapi, validation, xss, t-07-13, response-layer, d-07, tdd]

requires:
  - phase: 07
    provides: "the six-key htmx config block whose 422 rule carries swap:false since the 07-05 security fix"
  - phase: 11-01
    provides: "the response layer (is_htmx, location_response) and the GATE-02 pair registry"
  - phase: 11-06
    provides: "the ads editor on the response layer; the tree this plan mitigates"
provides:
  - "malformed_request_response — an empty 400 for page-layer validation refusals over htmx, at any error place"
  - "_validated_by_the_page_layer — the second signal, so the htmx branch cannot reach the app/routes/ JSON API (D-07)"
  - "app/main.py registers RequestValidationError; the degraded path and the JSON API stay byte-identical"
  - "tests/test_pages/test_htmx_validation_sink.py — 27-pair page traversal, 8-pair JSON-API boundary traversal, template address gate, two negative controls"
  - "SERVER_SIDE_VALIDATION_RESPONSES 0 -> 1 with a chronicle naming a third outcome its ledger had not anticipated"
affects: [11-08, 11-09, 11-10, security, app-main, gate-02]

actuals:
  tokens: 17361
  tasks: 1
  commits: 3
plan_head_before: 92c15f68ed6b5c0a48e408a3189c11c09f946313

tech-stack:
  added: []
  patterns:
    - "A branch that must not reach a neighbouring transport is selected by TWO signals — the client-controlled header AND the failing handler's package — never by the header alone"
    - "An exception-handler exit deliberately does NOT read the error location, so path/body/query cannot diverge: the divergence becomes inexpressible rather than merely tested"
    - "A traversal asserts the MITIGATED form (400, b\"\"), not the absence of a marker — an answer that never reached validation then reddens instead of passing vacuously"

key-files:
  created:
    - tests/test_pages/test_htmx_validation_sink.py
  modified:
    - app/pages/htmx.py
    - app/main.py
    - tests/test_pages/test_htmx_response_layer.py
    - tests/test_pages/test_htmx_response_contract.py
    - tests/test_pages/test_confirm_delete_transport.py

key-decisions:
  - "The mitigation lands in a SEPARATE plan BEFORE 11-09 returns the swap, so no commit exists on which the sink is open; the 422 rule keeps swap:false here"
  - "The htmx branch is chosen by is_htmx AND app.pages membership read from scope['endpoint'] — a header-only branch would have turned an htmx-flagged request to the JSON API into an empty 400 and broken its 422 contract (D-07)"
  - "The exit answers 400, not 422: from 11-09 the 422 rule swaps while [45].. does not, so a 400 body can never be pasted into the DOM and the failure banner still rises; the named price is that a forged request gets the generic advice (T-11-14)"
  - "exc.errors() is never read, so one exit covers path, form body and query string — a place-dependent divergence is inexpressible, not merely untested"
  - "The page traversal runs as admin because ten admin routes refuse at Depends(require_admin) BEFORE parameter parsing — under a plain user the traversal silently covered 17 of 27 pairs"
  - "The negative control restores the FRAMEWORK DEFAULT instead of deleting the handler: deletion produced a 500 via the app's generic Exception handler, a tree that never existed"

patterns-established:
  - "Declared traversal counts are set by a measured run and guarded by an anti-vacuum rule that names both sides of the boundary"
  - "A refuted expectation is recorded with what refuted it and by whose measurement, never silently rewritten (D-30/D-32)"

requirements-completed: [FORM-08]

coverage:
  - id: D1
    description: "A page-layer validation refusal over htmx is an empty 400 at ALL THREE error places — path, form body and query string"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_a_malformed_htmx_request_gets_an_empty_bad_request"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_the_validation_sink_is_empty_for_the_page_layer_over_htmx"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every page-layer route with an integer path parameter answers the write layer with exactly (400, empty) — 27 route x method pairs, admin included"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_no_htmx_request_receives_a_framework_validation_body"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_the_number_of_traversed_routes_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D3
    description: "The app/routes/ JSON API answers byte-for-byte identically with and without the htmx header — 8 pairs plus a named body-refusal case; app/routes/ is untouched (D-07)"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_the_json_api_keeps_its_validation_contract"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_identifier_bounds.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "The page-layer signal is true for exactly the app.pages handlers across the whole route table, and false when scope carries no endpoint"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_the_page_branch_is_chosen_only_for_page_endpoints"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_the_validation_sink_keeps_the_framework_answer_everywhere_else"
        status: pass
    human_judgment: false
  - id: D5
    description: "No htmx request address in app/templates points at the JSON API, so the residual 'an htmx request to /api/ would get the framework body' is unreachable from markup"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_no_htmx_address_in_templates_points_at_the_json_api"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_validation_sink.py#test_control_a_synthetic_json_api_address_reddens_the_template_rule"
        status: pass
    human_judgment: false
  - id: D6
    description: "SERVER_SIDE_VALIDATION_RESPONSES 0 -> 1 set by the reddened run; the 422 config rule still carries swap:false, so the swap remains 11-09's subject"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_contract.py#test_the_swap_rule_and_the_server_response_body_do_not_diverge"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_contract.py#test_validation_rule_carries_both_swap_and_error"
        status: pass
    human_judgment: false
  - id: D7
    description: "In a browser, an htmx request with a path identifier tampered via DevTools raises the «Действие не выполнено» banner and pastes nothing into the page"
    requirement: FORM-08
    verification: []
    human_judgment: true
    rationale: "Declared `verification: backstop` by the plan. The suite executes no JavaScript and the project has no browser harness, so the banner rising on a 400 (the [45].. rule, with 422 excluded by htmx_error_banner.html) is asserted only as server-side shape. Belongs to the phase UAT walk."

duration: 1h 17m
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 07: T-07-13 mitigation — page-layer validation refusals over htmx are empty Summary

**A framework validation refusal on the htmx path of the page layer is now an empty 400 at any error place, while the `app/routes/` JSON API stays byte-for-byte identical on both transports — the script-execution sink is closed before plan 11-09 returns the swap to the 422 rule.**

## Performance

- **Duration:** 1h 17m
- **Started:** 2026-09-16T08:43:00Z
- **Completed:** 2026-09-16T10:00:00Z
- **Tasks:** 1
- **Files modified:** 6 (1 created, 5 modified; 986 insertions, 4 deletions)

## Accomplishments

- `malformed_request_response()` answers an **empty 400** when — and only when — both signals hold: the request carries the htmx flag *and* the handler whose signature failed to parse belongs to `app.pages`. Every other branch awaits FastAPI's own `request_validation_exception_handler`, so the answer is unchanged byte-for-byte.
- The exit **never reads `exc.errors()`**. Path, form body and query string are therefore closed by one exit, which makes a place-dependent divergence inexpressible rather than merely untested.
- `_validated_by_the_page_layer()` reads `request.scope["endpoint"]`, measured present at exception-handler time on FastAPI 0.129.0 / Starlette 0.52.1 for all three error places. A version dropping that key reddens the 27-pair traversal instead of silently disabling the mitigation.
- The htmx flag is read **only** through `is_htmx`, so `HX_HEADER_READS` stays 1.
- `SERVER_SIDE_VALIDATION_RESPONSES` 0 → 1, set by the reddened run, with a chronicle entry explaining why this site needs **neither** remedy its ledger anticipated: it never hands a 422 to the write layer at all.
- The 422 config rule is untouched (`"swap": false`); the swap remains plan 11-09's subject, landing together with the first author-written 422.

## Task Commits

1. **Task 1 — RED:** `0177fe9` (`test`) — the traversals, named cases, branch predicate, controls and template gate
2. **Task 1 — GREEN:** `cc72871` (`feat`) — the exit, the signal, the registration, the counter and the deviation

**Plan metadata:** this commit (`docs`)

_REFACTOR: not needed — the GREEN implementation is two functions and one registration; no cleanup was identified that tests would have to re-prove._

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `0177fe9` | `cc72871` | — (not needed) |

RED was verified with `gsd-tools check tdd-red-evidence` → **`RED_EVIDENCE_OK`** (`reason: target_test_failed`, `exit_code: 1`, `tests: 33`, `pass: 27`, `fail: 6`).

```json
{
  "command": "uv run pytest tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_htmx_response_layer.py -q -p no:randomly",
  "exit_code": 1,
  "failing_test": "tests/test_pages/test_htmx_validation_sink.py::test_a_malformed_htmx_request_gets_an_empty_bad_request",
  "target_test": "tests/test_pages/test_htmx_validation_sink.py::test_a_malformed_htmx_request_gets_an_empty_bad_request",
  "expected": "code 400 with an empty body at all three error places (path, form body, query string)",
  "actual": "422 application/json echoing the input: int_parsing on path schedule_id; greater_than_equal on query after_id; missing on body ad_id",
  "verdict": "RED_EVIDENCE_OK",
  "reason": "target_test_failed"
}
```

⚠️ **The instrument reads node TAP, the suite speaks pytest, and the adapter is named rather than left unsaid.** The output was converted to TAP from `--junitxml` of **that same run** (file in the scratchpad, not in the tree): the *serialisation* of a measurement was translated, not an alibi composed. The exit code is the real `pytest`'s. Identifiers were emitted in path form (`file.py::test`) immediately, because that mismatch already cost plan 10-49 a false `INVALID_RED`. Method inherited from plans 10-36/10-37/10-49 and 11-01…11-06.

**Exit-code inversion was not used.** The RED claim names the failing target, the `6 failed` summary, and the causal literals measured in the tree: `int_parsing` on the path, `greater_than_equal` on `after_id` (`Query(None, ge=1, le=ID_MAX)`, `app/pages/account_groups.py:299`), `missing` on `ad_id` (`AdIdForm`, `app/pages/schedules.py:974`).

## Verification

| Run | Result |
|---|---|
| Plan `<verify>` set (5 files) | **197 passed**, rc=0 |
| Deviation file + predicted-unaffected (`test_confirm_delete_transport`, `test_identifier_bounds`, `test_editor_schedules`) | **157 passed**, rc=0 |
| Counting / drift gates (`test_htmx_gates.py`) | **43 passed**, rc=0 |
| Records gate (`tests/test_planning/`, after records edits) | **44 passed**, rc=0 |
| **Full suite** `uv run pytest tests/ -q` | **3310 passed**, rc=0, 40:21 |
| `compileall app main.py tests` | clean |
| `graphify update .` | 20510 nodes, 35809 edges |

**Counters re-measured after the change, not reasoned about** (the 11-06 stale-counter lesson): `HX_HEADER_READS` = 1, `HX_LOCATION_DESTINATION_CALLS_DECLARED` = 51, `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` = 14 — all unmoved, proven by the gates run rather than by argument.

### Acceptance criteria

All seven pass: one `exception_handler(RequestValidationError)` line; one `malformed_request_response`; one `_validated_by_the_page_layer`; the 422 rule still `"swap": false`; `SERVER_SIDE_VALIDATION_RESPONSES = 1`; `git status --porcelain -- app/routes/` empty before the commit and `git show --name-only --format= cc72871 -- app/routes/` empty after it; `compileall` clean.

**Mitigation commit hash, quoted here because plan 11-09 cites it as proof that the sink was open on no commit: `cc72871`.**

## Files Created/Modified

- `tests/test_pages/test_htmx_validation_sink.py` *(new, 692 lines)* — traversals of both layers, the three named error places, the branch predicate over the whole route table, two negative controls, the template address gate, and the declared-count anti-vacuum rule
- `app/pages/htmx.py` — `_PAGE_LAYER_PACKAGE`, `_validated_by_the_page_layer`, `malformed_request_response`; module docstring gains a third exit as a new generation, the "ДВА ВЫХОДА" text left intact
- `app/main.py` — registers `RequestValidationError` beside `HtmxRefusal`, naming what it does *not* change
- `tests/test_pages/test_htmx_response_layer.py` — output tests for all three error places and all three non-mitigated branches
- `tests/test_pages/test_htmx_response_contract.py` — `SERVER_SIDE_VALIDATION_RESPONSES` 0 → 1 with its chronicle
- `tests/test_pages/test_confirm_delete_transport.py` — the Rule 3 deviation below

## Decisions Made

Recorded in the frontmatter `key-decisions`. The load-bearing one: **the branch needs two signals.** The handler is registered on the whole application — `APIRouter` has no exception handlers of its own — so "the JSON API is not touched" (D-07) had to be *implemented* as a property rather than achieved by not editing files. A header-only branch would have turned any htmx-flagged request to `/api/…` into an empty 400.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `test_confirm_delete_transport.py` encoded the pre-mitigation sink**

- **Found during:** Task 1 (pre-flight conflict scan, before writing RED)
- **Issue:** `UNUSABLE_PATH_ID_OUTCOMES["1e3"] = (422, "")` drives `POST /schedules/{value}/delete` — a **page** route — through `_post_with_path_identifier`, which sends `HTMX_HEADERS`. That expectation *is* the behaviour this plan removes. Its sibling guard `not in (200, 204, 422)` would likewise have flagged the new 400 as a "third response form".
- **Fix:** `"1e3"` → `(400, "")`; the guard now admits 400. Both carry a generation note recording that the plan **refuted** the expectation; the prose above each is left verbatim (D-30/D-32) because it was true for the tree it was written on.
- **Why it is a deviation:** the file is not in the plan's `files_modified`. The plan named `test_account_groups.py:895-910` as the 422 assertions that must stay green (they do — they are sent *without* the htmx header) but did not anticipate this one.
- **Verification:** 157 passed in run B; the same file's non-htmx 422 expectations still hold.
- **Committed in:** `cc72871`

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** none on scope. The change was forced by the mitigation itself and is the single place in the suite where a page route asserted a framework 422 under the htmx header — established by a whole-suite scan, not by trial.

## Issues Encountered

Two defects **in my own tests**, both found by measurement during RED and both recorded in the tests' docstrings rather than quietly repaired:

1. **The traversal silently covered 17 of 27 pairs.** Under `authed_client`, ten `/admin/...` routes answered `403 {"detail":"Admin access required"}` — `app/pages/admin.py` guards with `Depends(require_admin)`, and dependencies are solved *before* the route's own path-parameter validation, so those routes never reached the subject at all. My first predicate also counted that 403 `detail` as a "framework validation body". Fixed by running the traversal as admin and narrowing the predicate to "422 **and** JSON"; the assertion was strengthened from "no `detail`" to "exactly `(400, b"")`", so a route that never reaches validation now reddens instead of passing vacuously.
2. **The negative control proved nothing.** Deleting the `RequestValidationError` handler made all 27 pairs answer **500**, because `create_app` also registers a generic `@app.exception_handler(Exception)`; my earlier probe had used a bare `FastAPI()` with no such handler, and I over-generalised from it. The control now **restores the framework default** — the actual pre-plan tree — and consequently is red in RED (its premise "a custom handler is installed" is false then) and green in GREEN. That is stated in its docstring so a future reader does not read it as broken.

Both are the reason the traversal is worth anything: each would have produced a green rule that guarded a smaller surface than it claimed.

## Threat Flags

None. The plan's `<threat_model>` dispositions are discharged: **T-07-13** by the empty 400 at every error place; **T-11-37** by the two-signal branch plus the 8-pair byte-for-byte JSON-API traversal and an untouched `app/routes/`; **T-11-38** by the template address gate with its synthetic control; **T-11-14** accepted with the price named in the exit's docstring. No new network surface, auth path or trust-boundary schema change was introduced.

## Known Stubs

None. No stub, skipped test or unrun `<verify>` was introduced, so `.planning/WINDOWS.md` gains no entry. Window 86 (11-06, `_attachment_refusal`) is **not** closed by this plan: its subject is the degraded half answering 400 where `respond()` cannot express a code, which this mitigation does not touch.

## Self-Check: PASSED

- `tests/test_pages/test_htmx_validation_sink.py` exists and collects 8 tests; all `key-files` are present on disk (`compileall` clean over `app main.py tests`).
- Commits exist: `0177fe9` (RED) and `cc72871` (GREEN); `git rev-list --count 92c15f68..HEAD` = 2 before this metadata commit, which makes 3.
- All task acceptance criteria re-run and passing; the plan-level `<verification>` commands re-run and logged in the Verification table above.

## Next Phase Readiness

- **Plan 11-08** may add the single source of an author-written 422 (`respond_field_error`).
- **Plan 11-09** returns `"swap": true` to the 422 rule *together with* the first author-written 422 and writes the T-07-13 addendum to `07-SECURITY.md`. It should cite `cc72871` as the proof that the sink was open on no commit, and must re-run `test_htmx_response_contract.py`, whose `test_validation_rule_carries_both_swap_and_error` is deliberately inverted and will redden on the swap's return — that redness is to be fixed by the route, not by editing the config line.
- No blockers. `REQUIREMENTS.md` deliberately still shows FORM-08 `Pending`: phase 11 verification has not run, and `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` enforces that.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

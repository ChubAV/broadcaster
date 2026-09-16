---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 08
subsystem: ui
tags: [htmx, fastapi, jinja2, form-08, response-layer, field-error, 422, tdd, d-12]

requires:
  - phase: 08
    provides: "respond() and the D-12 boundary — the outcome belongs to the shell, the field error belongs to the form"
  - phase: 11-01
    provides: "the response layer (is_htmx, location_response) and the GATE-02 pair registry"
  - phase: 11-07
    provides: "malformed_request_response — the T-07-13 sink closed BEFORE any swap returns (commit cc72871)"
provides:
  - "respond_field_error(request, *, page, fragment) — one status on both transports, the body chosen by how the request arrived"
  - "the ONLY 422 status literal in app/ — grep-provable, and counted by SERVER_SIDE_VALIDATION_RESPONSES 1 -> 2"
  - "app/templates/includes/profile_settings.html — the single source of the profile form for the page and for both fragments plan 11-09 will return"
  - "the field error now renders AT the form instead of above the «Аккаунт» card (D-12 of Phase 8)"
  - "a deliberately unreachable exit: no route calls it and the 422 rule still carries swap:false, so plan 11-09 lands the swap in ONE commit"
affects: [11-09, 11-10, security, form-08, profile]

actuals:
  tokens: 6312
  tasks: 2
  commits: 5
plan_head_before: 943d1d5ffe7e166ba97b573b65b3aaeaf97b01ec

tech-stack:
  added: []
  patterns:
    - "A handler exit that answers a FIELD error degrades to the PAGE, not to a redirect — the action did not happen, so there is nowhere to send the person"
    - "The exit re-stamps a FRESH response instead of editing the builder's object; freshness is asserted by object identity, not by matching bodies"
    - "The unchosen builder is proven un-called by the list of calls that happened, not by the absence of its body from the answer"
    - "A capability may land one plan BEFORE its first caller when the caller's commit must stay indivisible; unreachability is then PROVEN by grep, not apologised for"
    - "Markup forbidden by a raw-source gate is described in prose, never spelled — the comment would otherwise satisfy the gate's own search"

key-files:
  created:
    - app/templates/includes/profile_settings.html
  modified:
    - app/pages/htmx.py
    - app/templates/profile.html
    - tests/test_pages/test_htmx_response_layer.py
    - tests/test_pages/test_htmx_response_contract.py

key-decisions:
  - "The exit does NOT inherit respond()'s mandatory degraded address: a field error leaves the person on the form he was filling, so a redirect target would be a required argument with no subject"
  - "A fresh HTMLResponse is built rather than re-stamping the builder's own response — editing an object this exit does not own is the boundary _glue_notice already warns about, and a builder that later attaches a BackgroundTask would ride along silently"
  - "SERVER_SIDE_VALIDATION_RESPONSES 1 -> 2 was set BY THE REDDENED RUN, never by arithmetic; the chronicle quotes the literal output and names which of its two anticipated outcomes this discharges"
  - "The 422 config rule and the deliberately inverted test_validation_rule_carries_both_swap_and_error were left untouched — that redness is plan 11-09's to fix BY THE ROUTE it adds, not by editing the config line"
  - "The `selected` default lives in the CALLING page, not in the include: hidden inside the include, the choice of where the value comes from would be invisible from the page that owns it"
  - "The escaping-invariant comment describes the two unescaping techniques instead of naming them — the gate reads the raw body, so naming them would make the comment itself the offender"

patterns-established:
  - "Declared counts are set by a measured reddened run and quoted verbatim in the chronicle"
  - "A refuted expectation is preserved and dated rather than erased (D-30/D-32)"
  - "RED evidence is classified by the instrument, never by exit-code inversion"

requirements-completed: [FORM-08]

coverage:
  - id: D1
    description: "respond_field_error answers 422 on BOTH transports, with the page body when the htmx flag is absent and the fragment body when it is present"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_field_error_answers_422_with_the_page_without_htmx_and_the_fragment_with_it"
        status: pass
    human_judgment: false
  - id: D2
    description: "The unchosen builder is never called, and the answer is a fresh HTMLResponse (text/html) carrying no background task — not the builder's own object"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_field_error_answers_422_with_the_page_without_htmx_and_the_fragment_with_it"
        status: pass
    human_judgment: false
  - id: D3
    description: "The 422 status literal exists in exactly one place in app/ — the new exit — and the count is guarded at 2 sites (the exit plus the 11-07 handler registration)"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_contract.py#test_the_swap_rule_and_the_server_response_body_do_not_diverge"
        status: pass
      - kind: other
        ref: "grep -rn --include='*.py' 'status_code=422' app/ | cut -d: -f1 | sort -u  ->  app/pages/htmx.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "The swap stays OFF and the exit is unreachable: the 422 rule still carries swap:false and no route calls respond_field_error"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_contract.py#test_validation_rule_carries_both_swap_and_error"
        status: pass
      - kind: other
        ref: "grep -rn 'respond_field_error' app/ -> only the definition in app/pages/htmx.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "The profile settings render from one included template — a single source for the page and for both fragments of plan 11-09 — with the page still rendering identically"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_profile.py (4 passed — form contract, selected option, error text)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_profile_form_contract"
        status: pass
    human_judgment: false
  - id: D6
    description: "No htmx markup and no handler change: the form still posts normally and app/pages/profile.py is untouched"
    requirement: FORM-08
    verification:
      - kind: other
        ref: "grep -c 'hx-post' app/templates/includes/profile_settings.html -> 0; git diff --name-only 943d1d5..HEAD contains no app/pages/profile.py"
        status: pass
    human_judgment: false
  - id: D7
    description: "The new template keeps the escaping invariant — no unescaping technique reaches the user-supplied timezone value"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_no_unsafe_escaping"
        status: pass
    human_judgment: false
  - id: D8
    description: "In a browser the field error is seen BESIDE the timezone form rather than above the «Аккаунт» card, and the card still reads as one coherent block"
    requirement: FORM-08
    verification: []
    human_judgment: true
    rationale: "The suite asserts that the error text is present in the response, not WHERE it sits visually. Moving the alert from above the card to inside it next to the form is a visual placement change (D-12 of Phase 8) that no server-side assertion can judge. Belongs to the phase UAT walk."

duration: 1h 46m
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 08: the field-error exit and the profile form's single source Summary

**`respond_field_error` gives the application its one and only 422 — the page body without the htmx flag, the fragment body with it — while the profile settings move into one included template; the swap stays OFF and no route calls the exit, so plan 11-09 can land the swap in a single indivisible commit.**

## Performance

- **Duration:** 1h 46m (wall clock; ~79 min of it is two full-suite runs at ~40 min each)
- **Started:** 2026-09-16T10:51:37Z
- **Completed:** 2026-09-16T12:37:00Z
- **Tasks:** 2
- **Files modified:** 5 (1 created, 4 modified; 303 insertions, 18 deletions)

## Accomplishments

- **`respond_field_error(request, *, page, fragment)`** answers a field error with **one status on both transports and a body chosen by how the request arrived**: the page builder without the htmx flag, the fragment builder with it. Both builders are nullary and async, matching `respond()`'s `fragment=`.
- **The degraded path here is the PAGE, not a redirect**, and that is why the exit deliberately does not inherit `respond()`'s mandatory `redirect=`: a field error means the action did **not** happen, so there is nowhere to send the person — he stays on the form he was filling. A required degraded address would have been an argument with no subject.
- **The answer is freshly built, never the builder's own object.** Re-stamping the status in place would edit a response this exit does not own — precisely the boundary `_glue_notice`'s docstring warns about, where a builder that one day attaches a `BackgroundTask` or its own headers would ride along unnoticed. The test asserts this by **object identity**, not by matching bodies.
- **The unchosen builder is never called**, asserted by the list of calls that actually happened. A body-only assertion would pass for an exit that called both and returned one — while assembling a whole document on every field error.
- **`SERVER_SIDE_VALIDATION_RESPONSES` 1 → 2, set by the reddened run**, with the literal output quoted in the chronicle. The entry names which of the two outcomes its ledger demands is discharged: the body of this answer is assembled by the caller through the template environment, not by the framework default.
- **The swap stayed off and the exit is unreachable — by construction, not by oversight.** `"swap": false` is untouched, the deliberately inverted `test_validation_rule_carries_both_swap_and_error` was left red-by-design, and `respond_field_error` has no caller anywhere in `app/`. Plan 11-09 lands the swap together with its first caller in one commit.
- **`app/templates/includes/profile_settings.html` is now the single source of the profile form** for the page and for both fragments plan 11-09 will return. The field error moved from above the «Аккаунт» card — where it sat over the identity block it had nothing to do with — to **beside the form** (D-12 of Phase 8).
- **The chosen timezone comes from `selected`, defaulted by the calling page.** Today no handler supplies the key, so the saved zone shows and the screen is unchanged to the character; on plan 11-09's error branch the handler will supply the **submitted** value, so what the person typed stops being lost on a typo.
- **`app/pages/profile.py` is untouched**, proven by an empty `git status` on the file and its absence from every commit of this plan.

## Task Commits

1. **Task 1 — RED:** `5bb8ab0` (`test`) — both transports, the un-called builder, freshness by identity
2. **Task 1 — GREEN:** `07c6a80` (`feat`) — the exit, the single 422 literal, the counter and its chronicle
3. **Task 2:** `da31dd0` (`feat`) — the included template, the error moved to the form, imports dropped with their subject
4. **Deviation fix:** `bedcbbe` (`fix`) — the escaping comment no longer trips the escaping gate

**Plan metadata:** this commit (`docs`)

_REFACTOR: not needed — the GREEN implementation is one function of six statements; no cleanup was identified that the tests would have to re-prove._

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `5bb8ab0` | `07c6a80` | — (not needed) |
| 2 | n/a (`type="auto"`, no `tdd="true"`) | `da31dd0` | — |

RED was verified with `gsd-tools check tdd-red-evidence` → **`RED_EVIDENCE_OK`** (`reason: target_test_failed`, `exit_code: 1`, `tests: 26`, `pass: 25`, `fail: 1`).

```json
{
  "command": "uv run pytest tests/test_pages/test_htmx_response_layer.py -q -p no:randomly",
  "exit_code": 1,
  "failing_test": "tests/test_pages/test_htmx_response_layer.py::test_a_field_error_answers_422_with_the_page_without_htmx_and_the_fragment_with_it",
  "target_test": "tests/test_pages/test_htmx_response_layer.py::test_a_field_error_answers_422_with_the_page_without_htmx_and_the_fragment_with_it",
  "expected": "respond_field_error отвечает 422 телом сборщика страницы без признака htmx и телом сборщика фрагмента с ним; невыбранный сборщик не зовётся; ответ — свежий HTMLResponse без фоновой задачи",
  "actual": "ImportError: cannot import name 'respond_field_error' from 'app.pages.htmx' (/source/broadcaster/app/pages/htmx.py)",
  "verdict": "RED_EVIDENCE_OK",
  "reason": "target_test_failed"
}
```

**Exit-code inversion was not used.** The claim names the failing target, the `1 failed, 25 passed` summary line, and the causal literal measured in the tree (the `ImportError` above — the exit did not exist yet, which is the honest RED for a new function).

⚠️ **The instrument reads node TAP, the suite speaks pytest, and the adapter is named rather than left unsaid.** The output was converted to TAP from `--junitxml` of **that same run** (file in the scratchpad, not in the tree): the *serialisation* of a measurement was translated, not an alibi composed. The exit code is the real pytest's. Method inherited from plans 10-36/10-37/10-49 and 11-01…11-07.

## Verification

| Run | Result |
|---|---|
| Task 1 `<verify>` set (response layer, contract, gates) | **71 passed**, rc=0 |
| Task 2 `<verify>` set (profile, impersonation, markup gates, responsive) | **259 passed**, rc=0 |
| Adjacent to the changed module (validation sink, notices surface) | **15 passed**, rc=0 |
| All template-source gates (`tests/test_templates/`) after the fix | **218 passed**, rc=0 |
| Records gate (`tests/test_planning/`, after every record edit) | **44 passed**, rc=0 |
| **Full suite** `uv run pytest tests/ -q` — pre-fix | 3310 passed, **1 failed** (`test_no_unsafe_escaping`; see Deviations) |
| **Full suite** `uv run pytest tests/ -q` — after `bedcbbe` | **3311 passed**, rc=0, 37:47 |
| `compileall app main.py tests` | clean |
| `graphify update .` | 20531 nodes, 35836 edges |

**Counters re-measured after the change rather than reasoned about** (the 11-06 stale-counter lesson): `HX_HEADER_READS` = 1, `HX_HEADER_WRITES` = 2, `HX_LOCATION_DESTINATION_CALLS_DECLARED` = 51, `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` = 14, `OWN_RESPONSE_EXITS_DECLARED` = 9, `NOT_YET_CONVERTED_COUNT` = 21 — all unmoved, proven by the gate run. The new exit lives **inside** the response layer, so it correctly does not register as an "own response exit"; the markup inventory constants did not move either, because the new template carries no `hx-*` attribute, no OOB node and no `x-data`.

### Acceptance criteria

All ten pass. Task 1: one `respond_field_error` definition line; `status_code=422` present in exactly one file (`app/pages/htmx.py`); `SERVER_SIDE_VALIDATION_RESPONSES = 2`; the 422 rule still `"swap": false`; the `-k field_error` run green. Task 2: the include referenced once from `profile.html`; `alert(error)` 0 there and 1 in the include; `hx-post` 0 in the include; `git status --porcelain -- app/pages/profile.py` empty.

## Files Created/Modified

- `app/templates/includes/profile_settings.html` *(new)* — the field-error alert and the whole timezone form, with a header naming its context (`timezone_choices`, `selected`, `error`) and stating that it is the single source for the page and both of plan 11-09's fragments
- `app/pages/htmx.py` — `respond_field_error`; `HTMLResponse` imported; the module docstring gains a **fourth** exit kind as a new generation, the earlier "ДВА ВЫХОДА" and "third kind" text left intact (D-30/D-32)
- `app/templates/profile.html` — includes the settings in the form's former place, supplies `selected`, drops the alert that stood above the card and the three imports that left with their subject
- `tests/test_pages/test_htmx_response_layer.py` — the two-transport rule with its call-list and identity assertions
- `tests/test_pages/test_htmx_response_contract.py` — `SERVER_SIDE_VALIDATION_RESPONSES` 1 → 2 with its chronicle

## Decisions Made

Recorded in the frontmatter `key-decisions`. The load-bearing one: **the exit re-stamps a fresh response and does not inherit a degraded address.** Both follow from the same fact — a field error is not an outcome of an action. There is nowhere to redirect, and the builder's response object belongs to the builder.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] The escaping comment tripped the escaping gate**

- **Found during:** Task 2, by the **full suite** — not by the plan's `<verify>` set
- **Issue:** the new include's header claimed the two unescaping techniques were absent while spelling both of them literally. `test_no_unsafe_escaping` (`tests/test_templates/test_components.py`) scans the **raw** template body with no comment stripping, so the prose asserting their absence was itself the match: `AssertionError: ['includes/profile_settings.html: |safe', 'includes/profile_settings.html: Markup(']`.
- **Fix:** the comment now *describes* the two techniques instead of naming them, and records **why** they are not typed literally so a later reader does not "restore" them. This is the idiom the codebase already uses for the removed attribute in `account_groups/includes/group_row.html` — "проза, называющая атрибут дословно, удовлетворила бы греп сама".
- **Why it escaped the task gate:** the plan's task-2 `<verify>` names `test_profile`, `test_impersonation`, `test_htmx_markup_gates` and `test_responsive_markup`; the escaping invariant lives in `tests/test_templates/test_components.py`, which none of them reach. Worth knowing for plans 11-09/11-10, which add markup to this same file.
- **Verification:** all 218 template-source gates pass; the full suite re-run is **3311 passed**, rc=0.
- **Committed in:** `bedcbbe`

---

**Total deviations:** 1 auto-fixed (1 bug, self-inflicted and caught by the full suite).
**Impact on plan:** none on scope or behaviour — the change is confined to a Jinja comment, which never reaches the rendered document.

## Issues Encountered

**The first RED classification was `INVALID_RED`, and the cause was my own serialiser, not the measurement.** pytest's `--junitxml` emits no `file` attribute on `<testcase>` in this project, so my converter fell back to the dotted `classname` and produced `tests.test_pages.test_htmx_response_layer::test_…`, which cannot equal the path-form `targetTest` the checker compares by exact string — verdict `no_target_test_failure`. This is the same identifier-form trap that cost plan 10-49 a false `INVALID_RED`. The underlying run was always sound (exit 1, `1 failed, 25 passed`, the target named in `FAILED`), so the fix was to **re-serialise that same junitxml** with a converter that derives the path from `classname` when `file` is absent — no re-measurement, no second pytest run. Recorded here because the next executor will hit it too: on this project the TAP identifier must be built, not read.

## Threat Flags

None. The plan's `<threat_model>` dispositions are discharged: **T-07-13** by the swap staying off while the only 422 literal is an exit whose body the application composes (and the 11-07 mitigation already in place); **T-11-13** by the timezone value reaching the document only through the macro's auto-escaping, now proven by `test_no_unsafe_escaping` — which this plan very nearly defeated with a comment and which therefore earned its keep; **T-11-SC** trivially, as no package was installed. No new network surface, auth path or trust-boundary schema change.

## Known Stubs

None. No stub, skipped test, `xfail` or unrun `<verify>` was introduced — the scan over all changed files is empty, so `.planning/WINDOWS.md` gains no entry. Window 86 (11-06, `_attachment_refusal`) is **not** closed by this plan and was not touched.

## Self-Check: PASSED

- `app/templates/includes/profile_settings.html` exists on disk; `compileall` clean over `app main.py tests`.
- All four task commits resolve: `5bb8ab0`, `07c6a80`, `da31dd0`, `bedcbbe`. `git rev-list --count 943d1d5..HEAD` = **4** before this metadata commit, which makes the recorded `commits: 5`.
- All ten acceptance criteria re-run and passing; both plan-level `<verification>` commands re-run and logged in the table above.
- `actuals.tokens` = 6312 is chars/4 over the realized diff (25251 added chars across 5 files), the same scale the plan's `estimate` used — not a harness token count. The estimate was 70000 against a realized 6312: the plan was projected **uncalibrated** (`sample_count 0`), and the gap is recorded unrounded rather than flattered.

## Next Phase Readiness

- **Plan 11-09** may now land the swap in ONE commit: it returns `"swap": true` to the 422 rule *together with* the first route calling `respond_field_error`, rewrites the deliberately inverted `test_validation_rule_carries_both_swap_and_error` **by the route**, updates the literal in `test_shell.py` and adds the T-07-13 addendum to `07-SECURITY.md`. Both things it consumes are now on disk: the exit and the single markup source.
- ⚠️ **For 11-09 and 11-10, which add markup to `includes/profile_settings.html`:** `tests/test_templates/test_components.py` is **not** in this phase's task `<verify>` sets, and it scans raw template bodies. Run `tests/test_templates/` when touching that file.
- `REQUIREMENTS.md` deliberately still shows FORM-08 `Pending`: phase 11 verification has not run, and `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` enforces that.
- No blockers.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

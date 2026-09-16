---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 10
subsystem: ui
tags: [htmx, jinja2, form-10, form-08, d-16, profile, registry, negative-control, tdd]

requires:
  - phase: 11-09
    provides: "profile_post already answers fragments on BOTH outcomes — 200 with the settings form on success, 422 with the same form on a field error — so markup added here targets a route that fragments already come back from"
  - phase: 11-08
    provides: "includes/profile_settings.html as the single markup source for the page and both fragments"
provides:
  - "the profile settings form submitted through form_wrapper(action='/profile', target='#profile-settings', swap='innerHTML'), over a permanent #profile-settings wrapper in profile.html"
  - "ONE target for both outcomes: success and field error both replace the CONTENT of #profile-settings"
  - "RETARGET_RESWAP_USES — an empty registry of HX-Retarget/HX-Reswap uses, declared zero, with a negative control that proves it reddens"
  - "an AST scanner over app/**/*.py and a comment-stripped scan of app/templates for the two header names"
affects: [11-18, form-10, form-08, profile, htmx-gates]

actuals:
  tokens: 7988
  tasks: 2
  commits: 4
plan_head_before: 719442476428d04d8b2973a28c2dfb49e9d249da

tech-stack:
  added: []
  patterns:
    - "An empty registry is not evidence of anything until a negative control proves the scanner behind it can SEE a violation"
    - "A registry's emptiness is recorded together with its GROUND (here: identical success and field-error targets), so the ground and the emptiness are invalidated together"
    - "A scanner compares a string constant's WHOLE value, so prose that names a forbidden header in a docstring is not a use"
    - "When a shared macro prints the form tag, a form-specific layout hook moves to an inner node rather than into the macro"

key-files:
  created: []
  modified:
    - app/templates/profile.html
    - app/templates/includes/profile_settings.html
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_htmx_gates.py

key-decisions:
  - "Success and field error share ONE target (#profile-settings); that identity is the stated ground for founding the HX-Retarget/HX-Reswap registry empty, and the record names it so a diverging target invalidates the emptiness with it"
  - "The empty registry got teeth: a negative control injects a synthetic module writing HX-Retarget and requires the scanner to FIND it under module::function — without it, 'no uses' is indistinguishable from 'blind scanner'"
  - "The scanner walks the AST and compares whole string-constant values, not grep: app/pages/htmx.py names both headers in docstring prose, which grep would have counted as a use"
  - "The vendored runtime (app/static/js/htmx.min.js) is deliberately outside both scan areas — it contains both names because it READS them, and scanning it would redden forever for an unfixable reason"
  - "data-form moved to an inner <div data-form> (the ads/form.html precedent), because form_wrapper now prints the form tag for every form in the milestone and cannot carry one form's layout hook"
  - "profile_post was not touched; 45 profile and impersonation tests stayed green without a single edit"

patterns-established:
  - "Registry with teeth: DECLARED constant + completeness rule + positive-control line + a negative control that proves the scanner finds a planted violation"
  - "A markup counter is set by the reddened run and carries the verbatim failure text in its chronicle; counters that did NOT move are recorded as measured non-movement"

requirements-completed: [FORM-10, FORM-08]

coverage:
  - id: D1
    description: "profile.html holds a permanent #profile-settings wrapper; the include submits through form_wrapper with target='#profile-settings' and swap='innerHTML'; no hx-push-url on the form"
    requirement: FORM-10
    verification:
      - kind: other
        ref: "grep -n 'id=\"profile-settings\"' app/templates/profile.html -> one line (62)"
        status: pass
      - kind: other
        ref: "grep -c \"target='#profile-settings'\" app/templates/includes/profile_settings.html -> 1"
        status: pass
      - kind: other
        ref: "grep -c 'hx-push-url' app/templates/includes/profile_settings.html -> 0"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py -k 'long_lived or swap_target or two_roles' (11 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Three markup counters set by reddened runs, each with a chronicle and verbatim failure text: hidden callers 14 -> 15, parametric-target callers 4 -> 5, wrapper call blocks 5 -> 6"
    requirement: FORM-10
    verification:
      - kind: unit
        ref: "tests/test_templates/ (218 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "RETARGET_RESWAP_USES is empty and RETARGET_RESWAP_USES_DECLARED = 0; measured uses equal the registry keys, every entry carries a reason, and no template names either header"
    requirement: FORM-10
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_retarget_or_reswap_use_is_declared"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_retarget_or_reswap_uses_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D4
    description: "The empty registry has teeth: a synthetic module writing HX-Retarget is FOUND by the scanner under module::function and reddens the completeness rule; the live tree reads back empty afterwards"
    requirement: FORM-10
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_an_undeclared_retarget_header_reddens_the_registry"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_positive_the_untouched_source_tree_keeps_every_gate_green"
        status: pass
    human_judgment: false
  - id: D5
    description: "The profile handler contract is unchanged: success over htmx answers the form plus the notice, a field error answers 422 with the echo on both transports, and editing under another identity is still refused"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_profile.py + tests/test_pages/test_impersonation.py (45 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "In a real browser, saving the timezone shows the 'saved' notice in the shell area without a reload, and a timezone value injected through DevTools redraws the form with the field error and no crash banner"
    verification: []
    human_judgment: true
    rationale: "The suite proves DELIVERY — status, headers, and markup in the response body. ASGI transport executes no JavaScript, so it cannot prove the 200 or 422 body actually REPLACED the wrapper's content in the DOM, that the notice landed in the shell region, or that no failure banner rose. This is the plan's backstop truth and belongs to the phase UAT walk (11-UAT.md)."

duration: 55 min
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 10: Profile form on a shared-target wrapper, and an empty FORM-10 registry with teeth Summary

**The profile settings form now submits through `form_wrapper` over a permanent `#profile-settings` wrapper, so success and field error replace the content of ONE target. That shared target is exactly why the `HX-Retarget`/`HX-Reswap` registry is founded empty — and a negative control proves the registry actually reddens when a real use appears, rather than staying green on a blind scanner.**

## Performance

- **Duration:** 55 min (wall clock; ~35 min of it is the full-suite run)
- **Started:** 2026-09-16T15:25:24Z
- **Completed:** 2026-09-16T16:20:55Z
- **Tasks:** 2
- **Files modified:** 4 (381 insertions, 19 deletions)

## Accomplishments

- **The form became an htmx form without touching the handler.** `profile.html` wraps the include in `<div id="profile-settings">`; the include calls `form_wrapper(action='/profile', target='#profile-settings', swap='innerHTML')`. Method and action are still real, so the form degrades without JavaScript. `profile_post` was not edited, and all 45 profile and impersonation tests stayed green untouched.
- **Both outcomes share one target — the property the orchestrator asked to be established, not asserted.** On success (200), the settings form comes back with the saved zone. On a field error (422), the same form comes back with the submitted value. Both replace the **content** of the same wrapper (D-12 of Phase 9), which survives any number of responses. The header prose in both templates, and the registry record, name this identity as the **ground** for the empty registry, so a diverging target invalidates the emptiness along with it.
- **The FORM-10 registry was founded empty (D-16).** It has `RETARGET_RESWAP_USES: dict[str, str] = {}`, `RETARGET_RESWAP_USES_DECLARED = 0` with its chronicle, a completeness rule, a count rule, and a line in the positive control.
- **The registry has teeth.** `test_control_an_undeclared_retarget_header_reddens_the_registry` plants a synthetic handler writing `HX-Retarget` and asserts four things:
  - the scanner **finds** it under `app/pages/profile.py::a_route_some_future_phase_will_retarget` (anti-vacuum);
  - it names the correct header;
  - the completeness rule no longer matches;
  - the live tree reads back empty afterwards (no leakage).

  This is the guard against a second empty-selection green; the phase already recorded one in window 84.
- **The scanner walks the tree; it does not grep.** It matches a string constant whose **whole value** equals a header name, in any position. The measured reason: `app/pages/htmx.py` names both headers in docstring prose, which grep would have counted as a use.
- **Three markup counters were set by reddened runs**, each with its chronicle and verbatim failure text. Four more counters were measured as unmoved (see Verification).

## Task Commits

1. **Task 1:** `4881663` (`feat`) — wrapper, form on `form_wrapper`, inner layout node, three markup counters
2. **Task 2 — RED:** `f2290a5` (`test`) — the three rules, before the registry and scanner existed
3. **Task 2 — GREEN:** `131e50b` (`feat`) — registry, declared zero, AST and markup scanners, positive-control lines

**Plan metadata:** this commit (`docs`)

_REFACTOR: not needed. The GREEN implementation is two small scanners and two constants, and nothing was identified that the tests would have to re-prove._

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | n/a (`type="auto"`, no `tdd="true"`) | `4881663` | — |
| 2 | `f2290a5` | `131e50b` | — (not needed) |

RED was verified with `gsd-tools check tdd-red-evidence` → **`RED_EVIDENCE_OK`** (`reason: target_test_failed`, `exit_code: 1`, `tests: 3`, `pass: 0`, `fail: 3`).

```json
{
  "command": "uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly -k \"retarget\"",
  "exit_code": 1,
  "failing_test": "test_control_an_undeclared_retarget_header_reddens_the_registry",
  "target_test": "test_control_an_undeclared_retarget_header_reddens_the_registry",
  "expected": "сканер находит применение HX-Retarget в синтетическом модуле ключом app/pages/profile.py::a_route_some_future_phase_will_retarget, и правило полноты краснеет на дереве с необъявленным применением",
  "actual": "правила нет в файле вовсе: NameError: name '_retarget_reswap_uses' is not defined (tests/test_pages/test_htmx_gates.py:4551) — перечень D-16/FORM-10 не заведён, применение заголовка сегодня не покраснело бы ничем",
  "verdict": "RED_EVIDENCE_OK",
  "reason": "target_test_failed"
}
```

**RED was not proven by exit-code inversion.** The claim rests on three things:
- the named target in a `FAILED …::test_control_an_undeclared_retarget_header_reddens_the_registry` line;
- the exact summary line `3 failed, 43 deselected`;
- the causal literal verified in the tree: `_retarget_reswap_uses` did not exist at `f2290a5`.

The TAP was converted from the `--junitxml` of **that same run**, using bare pytest test names (the identifier form plan 11-08 lost a cycle to). A note on honesty: the RED failure is a `NameError`, meaning the rule was absent, not an assertion about its output. The instrument accepts this as the target failing for the planned reason. It is also the natural shape of RED for a gate that does not yet exist.

## Verification

| Run | Result |
|---|---|
| Task 1: markup gates **before** setting counters | **3 failed, 74 passed** (the three counters below) |
| Task 1: profile + impersonation | **45 passed** — handler contract unchanged, no edits |
| Task 1: **all of `tests/test_templates/`** | **218 passed** |
| Task 1: `-k "long_lived or swap_target or two_roles"` | **11 passed** |
| Task 1: neighbours that reference `form_wrapper` (`test_htmx_gates`, `test_responsive_markup`, `test_htmx_validation_sink`, `test_account_groups`) | **333 passed** |
| Task 2 RED | **3 failed, 43 deselected**, rc=1 (`RED_EVIDENCE_OK`) |
| Task 2 `-k retarget` / whole gates module | **3 passed** / **46 passed** |
| Plan-level trio (gates, markup gates, profile) | **129 passed** |
| Records gate `tests/test_planning/`, after every record edit | **44 passed** |
| **Full suite** `uv run pytest tests/ -q` | **3318 passed**, rc=0, 35:19 |
| `compileall app main.py tests` | clean |
| `graphify update .` | 20586 nodes, 35916 edges |

**The full-suite count cross-checks exactly.** Plan 11-09 recorded 3315, and this plan added 3 tests, giving 3318. So no test was lost, skipped, or silently deselected. The run was foreground-tracked (not detached) and completed normally. The time-windowed admin red (00:00–05:00 UTC) did not fire, because the run ended at 16:20 UTC.

**Counters set by reddened runs**, each quoted from its own failure:

| Counter | Move | Failure text that set it |
|---|---|---|
| `MACRO_DEFINITION_SITES_CALLERS_DECLARED` | 14 → 15 | `объявлено (… 'schedules/includes/schedule_row.html'), измерено (… 'includes/profile_settings.html', …)` |
| `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` | 4 → 5 | `объявленные вызывающие [...] разошлись с измеренными [... 'includes/profile_settings.html' ...]` |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 5 → 6 | `блоков вызова макроса-обёртки разобрано 6, объявлено 5` |

**Counters measured as NOT moving**, green without edits:
- `HX_TARGETS` 1: the macro file holds the one target site, however many callers it has.
- `HX_POST_PLACES` 3.
- `OOB_BLOCKS` 17.
- `CLIENT_STATE_NODES` 24.
- `FRAGMENT_ROUTES_DECLARED` 11: `POST /profile` calls `respond`, so it degrades and is not a fragment-only route.

The plan's context table predicted a recount of `HX_TARGETS`. The run shows why it stays put.

### Acceptance criteria

All seven pass.

Task 1:
- `id="profile-settings"` appears on exactly one line (62).
- `target='#profile-settings'` occurs once.
- `hx-push-url` occurs 0 times.
- The `-k long_lived/swap_target/two_roles` selection is green.

Task 2:
- `^RETARGET_RESWAP_USES_DECLARED = 0$` appears on one line (4493).
- `-k retarget --collect-only` gives **3/46 collected**.
- The whole gates module is green (46 passed).

## Files Created/Modified

- `app/templates/profile.html` — the permanent `#profile-settings` wrapper around the include, plus prose naming it as the ONE target of both outcomes
- `app/templates/includes/profile_settings.html` — the form via a `form_wrapper` block call; `data-form` on an inner node; a new generation of the header recording that 11-08's "no htmx markup here yet" condition is now met
- `tests/test_templates/test_htmx_markup_gates.py` — the caller added to both registries, and three counters with chronicles
- `tests/test_pages/test_htmx_gates.py` — the FORM-10 registry, declared zero, two scanners, three rules, and positive-control lines

## Decisions Made

Recorded in the frontmatter `key-decisions`. The load-bearing one: **the registry's emptiness and its ground are recorded together.** Success and field error share one target, so there is nothing to retarget. Should the targets ever diverge, the ground goes and the emptiness goes with it, and the record says so where the next reader will look.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug, prevented] Moving the form into the macro would have silently dropped its layout**

- **Found during:** Task 1, while reading what the macro prints
- **Issue:** The old form carried `data-form`, a CSS layout hook (`app/static/css/app.css:1867`: `[data-form] { display: flex; flex-direction: column; gap: 14px; … }` and `[data-form] > .field { align-self: stretch; }`). `form_wrapper` prints its own `<form>` tag and has no such attribute. A straight swap would have collapsed the profile form's column layout, and **no test would have noticed**: the style rule keys on the attribute, not on the form.
- **Fix:** The fields now sit inside an inner `<div data-form>`, the same precedent `ads/form.html` uses. The macro was not changed, because it serves every form in the milestone and must not carry one form's layout.
- **Verification:** `select_field` is still a direct child of the `data-form` node, so `> .field` still matches. `tests/test_templates/` 218 passed; profile 45 passed.
- **Committed in:** `4881663`

**2. [Rule 2 — Missing critical] The new registry needed a place in the positive control**

- **Found during:** Task 2
- **Issue:** The plan named three rules but not the file's positive control. That file's own idiom holds that a registry whose number nobody reads there can be moved silently. For an **empty** registry this matters more, because its completeness rule is green in any scanner state.
- **Fix:** `test_control_positive_the_untouched_source_tree_keeps_every_gate_green` now reads `RETARGET_RESWAP_USES_DECLARED` and asserts both scanners return empty on the untouched tree.
- **Verification:** gates module 46 passed.
- **Committed in:** `131e50b`

---

**Total deviations:** 2 auto-fixed (1 prevented bug, 1 missing-critical).
**Impact on plan:** no scope change, and no file was touched beyond the plan's list. Deviation 1 is the kind of defect this phase keeps shipping past its own verify sets — invisible to the suite and caught only by reading what the new abstraction actually prints.

## Issues Encountered

**The layout hook was invisible to every automated check.** Deviation 1 is recorded as prevented, not merely fixed, because nothing would have caught it. `tests/test_templates/` checks markup structure, and the profile tests check response bodies. Neither renders CSS. It was found only by reading what `form_wrapper` prints and comparing it with the attributes the old tag carried. The same class of defect should be expected on every remaining form this phase moves onto the macro.

**The phase-11 prose count was out of sync, as the orchestrator predicted.** The `**Plans**` line read "из них 9 исполнено". It was brought to the marks by hand ("10"), together with the checkbox and the progress row (`10/20`), and `completed_plans` was set from the roadmap-derived total (105 of 115) as the last record edit. `state advance-plan` was **not** used, so no quoted `**Status:**` line could be rewritten; a diff audit confirmed none was.

## Threat Flags

None. The register's dispositions are discharged:
- **T-11-16** by the empty registry, its declared zero, and a negative control that plants a real `HX-Retarget` write and requires both detection and a named key.
- **T-11-13** is unchanged and still holds: the echo passes only through `select_field`'s closed option list (plan 11-09's hostile-value test is green on both transports within the 45 profile tests).
- **T-11-SC** trivially: no package was installed.

No new network surface, auth path, or trust-boundary schema change was introduced. The form posts to the same `/profile` route through the same impersonation guard.

## Known Stubs

None. No stub, skipped test, `xfail`, or unrun `<verify>` was introduced, so `.planning/WINDOWS.md` gains no entry. Window 86 (11-06, `_attachment_refusal`) is untouched and remains open.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- **The FORM-10 registry is live and empty.** Any later plan that needs a real `HX-Retarget`/`HX-Reswap` must add a named entry with a reason and move `RETARGET_RESWAP_USES_DECLARED`. The negative control guarantees an unrecorded use will redden.
- **Plan 11-18 (MAX wizard)** is the other case Finding B names. Its step container must be both the success and the field-error target, or the registry's ground no longer holds for it.
- ⚠️ **For every remaining form moved onto `form_wrapper`:** check the old `<form>` tag for layout hooks (`data-form` and similar) before the swap. The macro prints a bare tag, and the suite does not see lost CSS.
- `REQUIREMENTS.md` deliberately still shows FORM-10 and FORM-08 as `Pending`: phase 11 verification has not run, and `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` enforces that.
- The browser half (D6) belongs to the phase UAT walk.
- No blockers.

## Self-Check: PASSED

- All four `key-files.modified` exist on disk.
- All three task commits resolve: `4881663`, `f2290a5`, `131e50b`. `git rev-list --count 7194424..HEAD` = **3** before this metadata commit, which makes the recorded `commits: 4`.
- All seven acceptance criteria were re-run and pass. Both plan-level `<verification>` commands were re-run and logged above, including the full suite (3318 passed, rc=0).
- `actuals.tokens` = 7988 is chars/4 over the realized diff (31 951 added characters across 4 files), the same scale the plan's `estimate` used, not a harness token count. The estimate was 65000 against a realized 7988. The plan was projected **uncalibrated** (`sample_count 0`), and the gap is recorded unrounded rather than flattered.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

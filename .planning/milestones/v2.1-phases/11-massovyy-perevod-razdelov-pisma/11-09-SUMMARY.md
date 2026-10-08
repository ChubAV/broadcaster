---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 09
subsystem: ui
tags: [htmx, fastapi, jinja2, form-08, response-layer, 422, swap, profile, tdd, t-07-13]

requires:
  - phase: 11-07
    provides: "the T-07-13 mitigation — a page-layer htmx validation refusal answers an EMPTY 400 (commit cc72871), so the sink was closed before any swap returned"
  - phase: 11-08
    provides: "respond_field_error — the only 422 literal in app/ — and includes/profile_settings.html, the single markup source for the page and both fragments"
provides:
  - "the 422 rule carries the swap again — as a VALUE of the existing rule, not a sixth config key and not new JS"
  - "the first route in the application answering 422 with an AUTHOR-WRITTEN fragment: profile timezone save"
  - "the first handler in the milestone to hand the response layer BOTH a fragment and an outcome code (out-of-band notice block)"
  - "a dated addendum to 07-SECURITY.md recording that T-07-13 is mitigated in substance, not by keeping the swap off"
  - "the own-response-exit gate now honours the builder boundary for the FOURTH response-layer exit"
affects: [11-10, 11-18, form-08, security, profile]

actuals:
  tokens: 13931
  tasks: 2
  commits: 4
plan_head_before: a6b9e0ae934443967ab80fbf448e954708675dc8

tech-stack:
  added: []
  patterns:
    - "A config rule change that widens a sink lands in ONE commit with the code that makes the widened path safe — provable by history, not by promise"
    - "An inverted red-by-design assertion is cleared BY THE ROUTE that makes it true, never by editing the literal it guards"
    - "Every declared counter the change could move is re-run, including counters the plan does not name"
    - "Echoing a submitted value into a CLOSED option list is unreachability, not escaping — and the stronger claim is the one recorded"
    - "A gate's builder boundary follows the response layer: a builder handed BY NAME to any layer exit is the layer's decision, not the handler's"

key-files:
  created: []
  modified:
    - app/pages/profile.py
    - app/pages/htmx.py
    - app/templates/includes/htmx_config.html
    - tests/test_pages/test_profile.py
    - tests/test_pages/test_htmx_response_contract.py
    - tests/test_pages/test_shell.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_pages/test_notices_channel.py
    - .planning/phases/07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii/07-SECURITY.md

key-decisions:
  - "The swap returned as a VALUE of the existing 422 rule — no sixth config key, no htmx:beforeSwap listener, no response-targets extension (Finding B, D-03 of Phase 7)"
  - "The timezone field gained an empty-string default so a MISSING field takes the handler's error branch instead of the framework's refusal — which on the htmx page-layer path would be the empty 400 of the 11-07 mitigation: neither form nor reason"
  - "The inverted assertion, the shell literal and the security record all landed in the SAME commit as the swap; each number was set by its own reddened run, never by arithmetic"
  - "The hostile timezone never reaches the document at all: select_field renders a CLOSED option list and merely COMPARES the submitted value, so T-11-13 is discharged by unreachability — recorded as the stronger claim rather than reported as escaping"
  - "The 422 branch is deliberately NOT expressible in the pair registry (it asserts 200+fragment or 204+header); the limit is named in the chronicle instead of left looking like an omission"
  - "The no-session pair case clears the cookie in its own arrangement rather than adding an anonymous identity to the shared helper, which serves eight confirm-delete routes"

patterns-established:
  - "A counter moved by a plan that never named it is recorded with its own chronicle entry and the literal failure text"
  - "Prose in a raw-source-gated file describes a forbidden name instead of spelling it"

requirements-completed: [FORM-08, FORM-03]

coverage:
  - id: D1
    description: "The 422 config rule carries the swap again, in both shells, read from the RENDERED document rather than the template source"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_contract.py#test_validation_rule_carries_both_swap_and_error"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_main_shell_carries_htmx_config, test_auth_shell_carries_htmx_config"
        status: pass
    human_judgment: false
  - id: D2
    description: "Profile save over htmx answers 200 with the settings form (saved zone selected) plus the out-of-band profile_saved notice, and no <!DOCTYPE; without htmx the unchanged 302 to /profile?notice=profile_saved"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_profile.py#test_profile_save_over_htmx_returns_the_form_and_the_notice"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#сохранение часового пояса — успех"
        status: pass
    human_judgment: false
  - id: D3
    description: "An invalid OR MISSING timezone answers 422 on BOTH transports — fragment without <!DOCTYPE over htmx, full page with it otherwise — and the hostile value never appears in either body"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_profile.py#test_an_invalid_timezone_answers_422_with_the_echo_on_both_transports"
        status: pass
    human_judgment: false
  - id: D4
    description: "The sink was open on NO commit: the mitigation (cc72871, plan 11-07) precedes the swap (4ba02ef, this plan), and the page-layer validation walk stays green"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_validation_sink.py (27 route pairs + JSON-API boundary)"
        status: pass
      - kind: other
        ref: "git log --oneline: cc72871 (11-07) precedes 4ba02ef (11-09)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The only 422 literal in app/ remains the response layer's own exit; the profile calls the exit and writes no literal"
    requirement: FORM-08
    verification:
      - kind: other
        ref: "grep -rn --include='*.py' 'status_code=422' app/ | cut -d: -f1 | sort -u -> app/pages/htmx.py"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_contract.py#test_the_swap_rule_and_the_server_response_body_do_not_diverge"
        status: pass
    human_judgment: false
  - id: D6
    description: "Milestone counters moved by measured runs: backlog 21->20, fragment handlers 8->9, transition calls 51->52, pair cases 19->21, notice write places 5->4"
    requirement: FORM-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py (43 passed), test_hx_location_destinations.py, test_htmx_post_pairs.py, test_notices_channel.py"
        status: pass
    human_judgment: false
  - id: D7
    description: "Editing the profile under another identity is still refused, and the impersonation dependency is untouched"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_profile_change_is_refused_under_another_identity"
        status: pass
    human_judgment: false
  - id: D8
    description: "In a real browser, saving the timezone redraws the settings form in place and shows the notice, and a field error redraws the form instead of leaving a dead button"
    verification: []
    human_judgment: true
    rationale: "The suite proves DELIVERY — status, headers, and markup present in the response body. It does not execute the htmx runtime, so it cannot prove that the 422 body actually REPLACED the form in the DOM, nor that the notice landed in the shell's notice area. That half belongs to the phase UAT walk."

duration: 1h 22m
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 09: the 422 swap and the first author-written 422 Summary

**The 422 rule carries the swap again — landed in ONE commit with the first route that answers that code with an author-written fragment (profile timezone save), on top of the T-07-13 mitigation that shipped a plan earlier, so no commit in the milestone ever had the swap on without a handler behind it.**

## Performance

- **Duration:** 1h 22m (wall clock; ~34 min of it is the full-suite run)
- **Started:** 2026-09-16T13:18:24Z
- **Completed:** 2026-09-16T14:40:54Z
- **Tasks:** 2
- **Files modified:** 11 (660 insertions, 44 deletions)

## Accomplishments

- **The swap returned as a VALUE of the existing 422 rule** — not a sixth config key, not an `htmx:beforeSwap` listener, not a response-targets extension. The five rules keep their order and their six keys (Finding B, D-03 of Phase 7).
- **It landed in ONE commit (`4ba02ef`) with the first route answering 422 with an author-written fragment** — `profile_post`. The ordering claim is provable from history rather than asserted: the T-07-13 mitigation is commit `cc72871` (plan 11-07), which precedes it, so **the sink was open on no commit of this phase**.
- **`profile_post` moved onto the response layer** with three branches: success answers a fragment of the settings form **carrying the outcome code out-of-band**, "no session" answers a transition, and a field error answers **422 on both transports** — the fragment over htmx, the full page without it.
- **The profile is the FIRST consumer of the "outcome code on the fragment branch"** in the whole milestone. The glue existed since Phase 8 and no handler had ever used it; `respond`'s docstring now records that as a fourth generation, with the refuted "НИ ОДИН ОБРАБОТЧИК" wording preserved and named rather than erased.
- **A missing field now takes the handler's branch, not the framework's.** The timezone field gained an empty-string default. With a required field the signature parse would fail *before* the handler body, and on the htmx page-layer path that is the empty 400 of the 11-07 mitigation — the person would see neither the form nor the reason.
- **The hostile value never reaches the document at all.** `select_field` renders a CLOSED option list and only COMPARES the submitted value, so a non-matching value is not rendered by any path. This is **unreachability, not escaping** — recorded as the stronger claim, the same idiom the notices registry already uses.
- **All three locked places moved together with the swap**, each set by its own reddened run: the inverted assertion got a third generation, the `test_shell.py` rule literal was brought to true, and the count of 422 sites did not move (still 2) — proven by the run, not by reasoning.
- **`07-SECURITY.md` gained a dated addendum** recording that T-07-13 is now mitigated *in substance* (empty 400 on the htmx page-layer path) rather than by keeping the swap off. The record above it is not rewritten.

## Task Commits

1. **Task 1 — RED:** `0461b6d` (`test`) — both new profile expectations plus the 400→422 move
2. **Task 1 — GREEN:** `4ba02ef` (`feat`) — the swap, the converted handler, the three locked places, the counters, the security addendum
3. **Task 2:** `831cc85` (`docs`) — `respond`'s fourth-generation docstring

**Plan metadata:** this commit (`docs`)

_REFACTOR: not needed — the GREEN implementation is one handler and one six-line markup helper; no cleanup was identified that the tests would have to re-prove._

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `0461b6d` | `4ba02ef` | — (not needed) |
| 2 | n/a (`type="auto"`, no `tdd="true"`) | `831cc85` | — |

RED was verified with `gsd-tools check tdd-red-evidence` → **`RED_EVIDENCE_OK`** (`reason: target_test_failed`, `exit_code: 1`, `tests: 6`, `pass: 3`, `fail: 3`).

```json
{
  "command": "uv run pytest tests/test_pages/test_profile.py -q -p no:randomly",
  "exit_code": 1,
  "failing_test": "test_profile_save_over_htmx_returns_the_form_and_the_notice",
  "target_test": "test_profile_save_over_htmx_returns_the_form_and_the_notice",
  "expected": "200 и фрагмент включаемого шаблона настроек с сохранённым поясом и внеполосным блоком profile_saved; <!DOCTYPE нет",
  "actual": "обработчик ответил перенаправлением: клиент слоя письма прошёл по 302 прозрачно и получил ЦЕЛЫЙ документ — assert '<!DOCTYPE' not in '\\n\\n<!DOCTY...dy>\\n</html>'",
  "verdict": "RED_EVIDENCE_OK",
  "reason": "target_test_failed"
}
```

**Exit-code inversion was not used.** The claim names the failing target, the `3 failed, 3 passed` summary line, and the causal literal measured in the tree (the handler still answered 302 on both transports). The TAP was converted from the `--junitxml` of **that same run**, with bare pytest test names — the identifier form plan 11-08 lost a cycle to.

## Verification

| Run | Result |
|---|---|
| RED — profile module | **3 failed, 3 passed**, rc=1 (`RED_EVIDENCE_OK`) |
| Task 1 `<verify>` set (9 modules) | **388 passed**, rc=0 |
| Task 2 `<verify>` set (response layer, gates, notices surface) | **76 passed**, rc=0 |
| All template-source gates (`tests/test_templates/`) | **218 passed**, rc=0 |
| Records gate (`tests/test_planning/`), after every record edit | **44 passed**, rc=0 |
| **Full suite** `uv run pytest tests/ -q` | **3315 passed**, rc=0, 33:52 |
| `compileall app main.py tests` | clean |
| `graphify update .` | 20559 nodes, 35878 edges |

**Counters re-measured rather than reasoned about** (the 11-06 stale-counter lesson), each quoted from its own reddened run:

| Counter | Move | Failure text that set it |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 21 → 20 | `число непереведённых обработчиков стало 20, а в файле записано 21` |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 8 → 9 | `обработчиков, отдающих фрагмент, найдено 9, объявлено 8` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 51 → 52 | `вызовов слоя ответа БЕЗ фрагмента найдено 52, а объявлено 51` |
| `POST_PAIR_CASES_DECLARED` | 19 → 21 | `случаев пар в реестре 21, объявлено 19` |
| `NOTICE_WRITE_PLACES` | 5 → 4 | `мест записи в страничном слое 4, а объявлено 5` |
| `SERVER_SIDE_VALIDATION_RESPONSES` | 2 (unmoved) | green — the profile calls the exit and writes no literal |

### Acceptance criteria

All eight pass. The swapped 422 rule appears on exactly one line; `status_code=422` in `app/` resolves to `app/pages/htmx.py` alone; zero `RedirectResponse` and zero required-`Form` in `profile_post`; the three counters read 20 / 9 / 2; the security record carries `Фаза 11`; and the two named profile tests are green.

## Files Created/Modified

- `app/pages/profile.py` — `profile_post` on the response layer (three branches), the `_settings_markup` helper rendering the shared include, and the field-error text as a named constant
- `app/templates/includes/htmx_config.html` — the 422 rule's swap value; a new generation of the prose recording that the condition the earlier text set has now been met
- `app/pages/htmx.py` — `respond`'s fourth-generation docstring naming the profile as the first consumer
- `tests/test_pages/test_profile.py` — the two new transport tests; the field-error status moved 400 → 422
- `tests/test_pages/test_htmx_response_contract.py` — the assertion's third generation ("the swap did not disappear")
- `tests/test_pages/test_shell.py` — the expected rule literal plus its generation comment
- `tests/test_pages/test_htmx_gates.py` — backlog and fragment registries, and the builder-boundary fix
- `tests/test_pages/test_htmx_post_pairs.py` — two profile pair cases and their arrangements
- `tests/test_pages/test_hx_location_destinations.py`, `tests/test_pages/test_notices_channel.py` — counters with chronicles
- `.planning/phases/07-.../07-SECURITY.md` — the dated T-07-13 addendum

## Decisions Made

Recorded in the frontmatter `key-decisions`. The load-bearing one: **the swap is a value of the existing rule, and it is indivisible from its first consumer.** Everything else in the plan follows from keeping that commit single.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] My own config prose tripped the inline-script gate**

- **Found during:** Task 1, by the locked-places run — not by a plan `<verify>` command
- **Issue:** the new prose in `htmx_config.html` named the 11-07 exit literally, and that name contains the substring `request`. `test_history_cache_purge_touches_no_markup_sink` scans the **raw** file body with no comment stripping and asserts the inline script reads nothing from the request: `AssertionError: includes/htmx_config.html: появилось обращение к request`.
- **Fix:** the prose now *describes* the exit instead of spelling it, and records **why** it is not typed literally so a later reader does not "restore" it. Identical idiom to the one plan 11-08 had to adopt in `profile_settings.html`.
- **Verification:** `tests/test_templates/` 218 passed; the shell gate green.
- **Committed in:** `4ba02ef`

**2. [Rule 1 — Bug] A counter the plan never named moved: `NOTICE_WRITE_PLACES`**

- **Found during:** Task 1, by running modules *adjacent* to the plan's verify set
- **Issue:** converting the handler removed the last hand-built `?notice=` address from the page layer — the code now travels to the response layer as a parameter. The gate counting hand-built notice writers dropped 5 → 4 and reddened.
- **Fix:** the counter was set **by the reddened run** and given a chronicle entry recording the source of the movement, plus the check that this is not a LOST outcome (the code is still mentioned as a registry constant in its handler, so the orphaned-codes rule stays green).
- **Verification:** `test_the_number_of_notice_writers_is_the_declared_one` green; notice channel module green.
- **Committed in:** `4ba02ef`

**3. [Rule 2 — Missing critical] The own-response-exit gate was blind to the FOURTH response-layer exit**

- **Found during:** Task 1, by the gates module
- **Issue:** the gate excludes a response builder handed to `respond(fragment=…)` — that is how `account_groups_toggle` legitimately stays out ("девять из десяти"). It knew only `respond`, so the builders this plan hands to `respond_field_error(page=…, fragment=…)` were reported as an undeclared own exit: `НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/profile.py::profile_post (вид HTMLResponse())`.
- **Fix:** the boundary now follows the response layer rather than one of its exits. **Declaring the profile in the registry would have been the wrong repair** — the registry is for handlers that answer an unverified request source with their own response and whose form decision "awaits the owner"; these builders are exactly what the layer calls. The exclusion stays narrow: only a builder handed **by name** to a layer exit.
- **Verification:** gates module 43 passed, including the positive control and the negative control that proves the rule still reddens on a genuinely undeclared exit.
- **Committed in:** `4ba02ef`

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing-critical). Two of the three were invisible to the plan's own `<verify>` set and were caught only by running neighbouring modules — the same lesson 11-08 recorded.
**Impact on plan:** no scope change. Two files beyond the plan's list were touched (`test_notices_channel.py`, and the parser inside the already-listed `test_htmx_gates.py`), both forced by measured gate movement.

## Issues Encountered

**The pair registry has no anonymous identity, and the "no session" case needed one.** `_identify` signs the client in on both of its branches, so a session-less case is not expressible by choosing an identity. Rather than adding a third identity to the helper — which is imported from `test_confirm_delete_transport.py` and serves eight confirm-delete routes, whose conditions would then change for one case of a different registry — the arrangement clears the cookie itself. The arrangement runs before **each** half of the pair, so the clearing covers both the 302 and the transition header; that property is recorded in the arrangement's docstring rather than left to luck.

**The 422 branch cannot be expressed in the pair registry at all.** The walk asserts either 200-with-fragment or 204-with-header; a field error answers 422 on *both* transports, and there is no third shape. Forcing it into an existing shape would have asserted the wrong code, so the limit is named in the chronicle and both halves are asserted by name in `test_profile.py` instead.

## Threat Flags

None. The register's dispositions are discharged: **T-07-13** by the mitigation preceding the swap (`cc72871` before `4ba02ef`) and by the only 422 literal being an exit whose body the application composes; **T-11-13** by the closed option list, which makes the hostile value unreachable rather than merely escaped; **T-11-15** by leaving `forbid_when_impersonating` untouched, with the impersonation module green; **T-11-SC** trivially — no package was installed. No new network surface, auth path, or trust-boundary schema change.

## Known Stubs

None. No stub, skipped test, `xfail` or unrun `<verify>` was introduced, so `.planning/WINDOWS.md` gains no entry. Window 86 (11-06, `_attachment_refusal`) is untouched and remains open.

## Self-Check: PASSED

- All three task commits resolve: `0461b6d`, `4ba02ef`, `831cc85`. `git rev-list --count a6b9e0a..HEAD` = **3** before this metadata commit, which makes the recorded `commits: 4`.
- Every file listed under `key-files.modified` exists on disk; `compileall` clean over `app main.py tests`.
- All eight acceptance criteria re-run and passing; both plan-level `<verification>` commands re-run and logged above.
- `actuals.tokens` = 13931 is chars/4 over the realized diff (55 722 added chars across 11 files), the same scale the plan's `estimate` used — not a harness token count. The estimate was 85000 against a realized 13931: the plan was projected **uncalibrated** (`sample_count 0`), and the gap is recorded unrounded rather than flattered.

## Next Phase Readiness

- **Plan 11-10** may now add the htmx wrapper and submission attributes to `includes/profile_settings.html`: the handler already returns fragments, so the markup will point at a route that answers them. Its `#profile-settings` target is what the success fragment expects to replace.
- ⚠️ **For 11-10 and any plan touching that include:** `tests/test_templates/test_components.py` is **not** in this phase's task `<verify>` sets and scans raw template bodies. Run `tests/test_templates/` when touching it — and note that prose naming a gate-visible literal is itself a match (this plan hit that in `htmx_config.html`, plan 11-08 hit it in the include).
- `REQUIREMENTS.md` deliberately still shows FORM-08 and FORM-03 `Pending`: phase 11 verification has not run, and `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` enforces that.
- No blockers.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
reviewed: 2026-09-27T11:20:00Z
depth: standard
diff_base: c939cc8c
files_reviewed: 38
files_reviewed_list:
  - app/pages/accounts.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/schedules.py
  - app/services/schedule_rules.py
  - app/static/css/app.css
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/list.html
  - app/templates/ads/partial_cards.html
  - app/templates/ads/partials/sched_card_response.html
  - app/templates/ads/partials/sched_create_response.html
  - app/templates/includes/htmx_error_banner.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - scripts/prohibitions_census.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_failure_banner_invariants.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedule_invariants.py
  - tests/test_pages/test_shell.py
  - tests/test_pages/test_write_path_invariants.py
  - tests/test_planning/test_executed_plans_kept_their_scope.py
  - tests/test_planning/test_plan_prohibitions_census.py
  - tests/test_planning/test_the_walkthrough_stand_is_seedable.py
  - tests/test_templates/test_banner_dismiss.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_confirmation_panel_invariants.py
  - tests/test_templates/test_degradation_pairs.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_markup_literal_inventory.py
  - tests/test_templates/test_walkthrough_anchors.py
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
carried_forward:
  open: 0
  closed: 10
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-09-27T11:20:00Z
**Depth:** standard
**Files Reviewed:** 38
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

This pass covers `git diff c939cc8c..HEAD` over the 38 listed files: 108 commits from gap plans 15-15 to 15-33. Large test modules were reviewed only in their changed regions.

The product changes are:
- the second-line refusal in `schedules_create` and `schedules_update` (15-16)
- `profile_timezone_or_utc` and the card hint for an unrecognised zone (15-23)
- removal of `limit=` from six sentinels, plus `role="status"` (15-21)
- the new dismiss-label wording and the opaque `--focus-ring` (15-19)

The rest is census tooling and about 9,000 lines of new invariant tests.

**All ten prior findings are closed.** Evidence is in the disposition table below.

**Checks that came back clean:**
- **Access scoping.** Neither refusal moved the owner checks. Both refusal branches sit after `_ownership_verdict`.
- **Create refusal writes nothing.** The create refusal returns before `db.add` (`schedules.py:1135-1142`). The transient `Schedule` is built from FK ids only, so nothing cascades it into the session.
- **Update refusal writes nothing.** The update refusal calls `db.rollback()` before `respond()`, and `respond()` touches no ORM state.
- **Every card call passes the new argument.** Every caller of `sched_card` / `sched_card_article` passes the new required `fallback_timezone`: `form.html:333`, `sched_card_response.html:41`, `sched_create_response.html:55`. All three renderers (`schedules.py:1202`, `:1454`, `:1674`) supply `editor=`.
- **The hint escapes the stored zone.** It is printed only through autoescape.
- **No temporary product edits were committed.** Per-file commit counts for `app/`, `scripts/` and `main.py` match the net diff, with no add-then-revert pairs. Every product commit in range (`5fa0552f`, `0e86878a`, `dc851613`, `ace989f9`, `3d8557eb`, `5a95c970`, `5187b807`, `a74f2651`, plus the accounts/templates commits) survives into the tree.

**Test runs on this tree:**
- 170 passed: `tests/test_planning/` (census, scope-keeping, walkthrough-stand)
- 383 passed: `test_failure_banner_invariants`, `test_schedule_invariants`, `test_write_path_invariants`, `test_confirmation_panel_invariants`, `test_walkthrough_anchors`, `test_banner_dismiss`, `test_degradation_pairs`, `test_markup_literal_inventory`, `test_components`, `test_hx_location_destinations`, `test_editor_schedules`

**Main concerns:**
- The new refusal reuses the toggle's notice. Its text tells a person who has just saved in the editor to open the editor and save — the action that was just refused.
- The census gate crashes on any decimal-numbered phase. This project has used decimal phases before (`05.1`).
- A product test (not planning-marked) reads a Phase 10 planning artifact. It will fail on milestone archive, which is the next step for this milestone.
- A sha256 freeze of `compute_next_run_at` pins a function with a known two-way failure signal.

## Prior Findings Disposition

| ID | Finding | State | Evidence |
|----|---------|-------|----------|
| WR-01 | Editor save silently pauses a running schedule; tests lock it in | **closed** | `app/pages/schedules.py:1380-1414`: `None` from `next_run_or_none` now does `db.rollback()` and `respond(..., notice=SCHEDULE_VALUES_OUT_OF_DOMAIN)`, and nothing is written (commit `5fa0552f`). Tests `test_editor_schedules.py:4463-4511` / `:4538-4579` assert the notice in `Location`, `_snapshot(stored) == seeded` and `is_active is True`; `:4582` covers the htmx `HX-Location`. The new notice-text problem is WR-05. |
| WR-02 | AST rule forbids giving `schedules_create` the same second line | **closed** | `schedules.py:1121-1143`: create builds a transient row and asks `next_run_or_none`, refusing on `None` (commit `0e86878a`). The rule at `test_editor_schedules.py:4781-4855` now asserts `module_direct == []` and that both handlers call the helper. `test_create_on_the_second_line_*` (`:4708`, `:4742`) cover it. |
| WR-03 | Four GATE-10 degrade pairs pass on the "nothing deleted" branch | **closed** | Each pair asserts the exact `location` and that the row is gone after `expire_all()`: `test_responsive_markup.py:1263` (+`:1307-1314`), `:3507` (+`:3549-3556`), `:3590` (+`:3634-3642`), `test_ads_editor.py:1925` (+`:1975-1982`). The meta-rule `test_degradation_pairs.py:1215` (`test_every_redirecting_degradation_pair_asserts_the_exact_location`) enforces the exact-location half for every pair. |
| WR-04 | Census phase-stamped literals redden on the next plan | **closed** | The literals are now measured over `tool.through_fixed_set` (`scripts/prohibitions_census.py:363-406`, plans through 15-14). The growing half is `after_fixed_set_offences` (`test_plan_prohibitions_census.py:1211-1256`), which checks membership rather than counts. Verified live: 33 phase-15 plans exist and the module passes. New plans still need `--seed-registry`, and the failure message names it (`:1200`, `:1235`). That is the minimum the fix asked for. The decimal-phase crash is a new defect of the same mechanism (WR-06). |
| IN-01 | `verification: null` read as absent | **closed** | `_verification_of` (`prohibitions_census.py:453-468`) separates absent (`None`), present-empty (`CensusError`) and value. `verification_label` (`:471-473`) prints `—` only for an absent key. Test at `test_plan_prohibitions_census.py:3051`. |
| IN-02 | Malformed registry gives a raw traceback | **closed** | `load_registry` rejects a non-mapping document (`:591-594`). `_registry_row_problem` / `_registry_rows` name the position for a missing or ill-typed `plan` / `index`, including bools (`:599-634`). `_class_decisions` rejects non-dict entries (`:637-655`). Tests at `:3130-3183`, including `main()` printing `ОТКАЗ:`. |
| IN-03 | Two `_split_top_level` parsers | **closed** | There is one definition, at `test_htmx_markup_gates.py:9500` (multi-char separators, `{}` nesting, quotes). It is imported by `test_htmx_gates.py:125` and `test_components.py:54`, which also dropped a third copy. Behaviour is pinned at `:9559-9588`. |
| IN-04 | Comments point at shiftable line numbers | **closed** | `app.css:1392-1395` now points by quoted heading. `test_htmx_markup_gates.py:9130-9133` / `:9207-9209` do the same. The stale reason at `test_editor_schedules.py:5230-5236` is marked as outdated and the real reason is given. |
| IN-05 | Page-size literal pattern catches only `limit=<digit>` | **closed** | `test_markup_literal_inventory.py:133-139` now has five forms: address, `{{ N }}`, `{{ 'N' }}`, `hx-vals`, and hidden `<input>`. There is a synthetic positive per form (`:185-200`) and negatives for name-based expressions and `rate_limit` (`:206-211`). |
| IN-06 | PyYAML undeclared, new user | **closed** | Branch (b) of the fix was taken. The decision is recorded at `.planning/STATE.md:676` (transitive via `uvicorn[standard]`, pinned 6.0.3 in `uv.lock`). The importer set `YAML_DIRECT_IMPORTERS` (`test_plan_prohibitions_census.py:3960-3967`) is checked by `ast` against `app/`, `scripts/`, `tests/` and `main.py`. Verified by grep: it holds exactly the three declared modules. |

## Warnings

### WR-05: The new create/update refusal reuses the toggle's notice, whose text tells an editor user to repeat the action that was just refused

**File:** `app/pages/schedules.py:1136-1142` (create), `:1408-1413` (update); the text is at `app/pages/notices.py:272-279`. The code is pinned by `tests/test_pages/test_editor_schedules.py:4371` (`_refusal_landing`) and its uses at `:4506`, `:4574`, `:4604`, `:4726`, `:4777`.

**Issue:** Both new refusal branches reuse `SCHEDULE_VALUES_OUT_OF_DOMAIN`. That notice was written for the toggle (resume) entry: «Дни или часы этого расписания заданы значениями, которых система исполнить не может. Откройте расписание в редакторе объявления, выберите дни и время заново и сохраните — после этого включение сработает.»

On the two new entries this text is wrong:
- **Update.** The person is already in the editor and has just chosen days and times and pressed save. The handler rolls back their edits and redirects to `/ads/{ad_id}/edit` without `?sched=`, so the card comes back collapsed with the old values. The row stays **active**, so "после этого включение сработает" refers to an action nobody took. Following the text submits the same values through the same sanitizer and reaches the same refusal.
- **Create.** No schedule exists yet, so "Откройте расписание" points at nothing.

The branch is only reachable when the first line (`_clean_ints` / `_clean_times` / zone rollback) lets a value through. That lowers likelihood, not severity. When it fires, the only guidance the user gets sends them in a loop.

All five refusal tests assert `location == _refusal_landing(ad_id)`, which contains this exact code. Giving the save paths their own notice will redden five phase-15 tests. That is a mild case of "phase tests pin a defect": the tests pin a code whose registry text does not fit the entry.

**Fix:** Register a save-specific code in the closed registry. Use it on both new branches, and keep `SCHEDULE_VALUES_OUT_OF_DOMAIN` for the toggle. Also keep the card expanded:
```python
# notices.py
SCHEDULE_SAVE_VALUES_OUT_OF_DOMAIN = "schedule_save_values_out_of_domain"
Notice(SCHEDULE_SAVE_VALUES_OUT_OF_DOMAIN,
       "Расписание не сохранено: выбранные дни или время система исполнить не может. "
       "Изменения не записаны — выберите другие дни и время.", "error"),
# schedules.py (update branch)
return await respond(request, redirect=_editor_url(True, ad_id, schedule_id),
                     notice=notices.SCHEDULE_SAVE_VALUES_OUT_OF_DOMAIN)
```
Point `_refusal_landing` at the new code in the same commit, so the tests follow the fix rather than block it.

### WR-06: The census gate raises `CensusError` on any decimal-numbered phase, and this project has used one

**File:** `scripts/prohibitions_census.py:358-360` (`phase_of`), `:370-382` (`plan_number_of`), `:385-389` (`_phase_number_of`), `:392-406` (`through_fixed_set`); consumers include `tests/test_planning/test_plan_prohibitions_census.py:962`, `:1217`, `:2814`.

**Issue:** `PLAN_GLOB = ".planning/phases/*/[0-9]*-PLAN.md"` matches a decimal phase's plans, for example `.planning/phases/15.1-x/15.1-01-PLAN.md`. Two functions then refuse that path:
- `_phase_number_of` refuses because `"15.1".isdigit()` is false.
- `plan_number_of` would also refuse, because `(\d+)-(\d+)-PLAN\.md` does not `fullmatch` `15.1-01-PLAN.md`.

Reproduced on this tree:
```
through_fixed_set({'.planning/phases/15.1-x/15.1-01-PLAN.md': ...})
-> CensusError: `.planning/phases/15.1-x/15.1-01-PLAN.md`: номер фазы `15.1` — не число
```
`through_fixed_set` runs over the whole live universe in the fixed-set fixture and in the growing-half rule. One `/gsd-phase insert` (which creates decimal phases, per `.claude/gsd-core/workflows/insert-phase.md:4`) therefore turns the census module red with a tool refusal, not a named offence. The project has done this before: `.planning/milestones/v2.0-phases/05.1-edinaya-podpiska`.

Unlike the milestone-archive boundary (documented at `test_plan_prohibitions_census.py:103-106`), this one is not named anywhere. Per project memory, executors deselect `tests/test_planning/`, so the break will first appear at the orchestrator's full-suite gate.

**Fix:** Parse phase numbers as tuples, and let decimal phases compare after their integer parent:
```python
PLAN_FILE_NAME = re.compile(r"(\d+(?:\.\d+)?)-(\d+)-PLAN\.md")
def _phase_key(plan_path: str) -> tuple[int, ...]:
    phase = phase_of(plan_path)
    if not re.fullmatch(r"\d+(?:\.\d+)?", phase):
        raise CensusError(...)
    return tuple(int(p) for p in phase.split("."))
# through_fixed_set: (_phase_key(path), plan_number_of(path)) <= ((15,), 14)
```
Add a synthetic control with a `15.1-01-PLAN.md` path next to `test_control_a_plan_after_the_fixed_set_is_named_by_the_bijection`.

### WR-07: A product-suite test reads a Phase 10 planning artifact through a `test_planning` import, and will fail on milestone archive

**File:** `tests/test_pages/test_schedule_invariants.py:103-107` (import), `:417-418`, `:487-523` (`test_no_seed_lifts_check_constraints_without_rolling_back_first`)

**Issue:** The rule calls `seed_program(walkthrough_source())`. `walkthrough_source` (`tests/test_planning/test_the_walkthrough_stand_is_seedable.py:170-172`) reads `.planning/phases/10-rychag-components-modal-html/10-UAT.md`.

This module has no `pytestmark = pytest.mark.planning`. So:
1. `-m "not planning"`, the documented triage lever in `tests/conftest.py:477-488`, does not exclude it.
2. Phase 15 is the last phase of this milestone (`.planning/ROADMAP.md:77`). When `/gsd-complete-milestone` moves `.planning/phases/10-*` into the archive, this product test fails with `FileNotFoundError`. The census module does the same, but its boundary is documented; this one is not.

The phase itself added the rule that forbids this coupling for markup modules: `test_walkthrough_anchors.py` (`FORBIDDEN_IMPORT_PACKAGES = ("tests.test_planning", "tests.test_pages")`). Its reason applies word for word: a rule that reddens on someone else's work gets switched off together with its directory. `test_schedule_invariants.py` is the only file under `tests/test_pages/` that imports from `tests.test_planning`.

**Fix:** Move the walkthrough half of this rule into `tests/test_planning/test_the_walkthrough_stand_is_seedable.py`, which is already planning-marked, and keep only the tree scan (`SCANNED_TREES`) in `test_schedule_invariants.py`. Or split it into its own function with `@pytest.mark.planning`. Either way, drop the `tests.test_planning` import from the product module.

### WR-08: `compute_next_run_at` is frozen by a sha256 digest, pinning a function whose two-way failure signal is a known pre-existing defect

**File:** `tests/test_pages/test_schedule_invariants.py:130-150` (`NEXT_RUN_CALCULATOR_SOURCE_DIGEST = "698f47d4e018"`), rule `test_the_next_run_calculator_source_is_unchanged`

**Issue:** Prohibition `10-55#0` was a plan-scoped statement: plan 10-55 was not to put the guard inside the calculator, so that `None` keeps its meaning. This rule turns it into a permanent, character-level freeze of the whole function. Any edit reddens it: a docstring, a type hint, or a real fix.

The function's current behaviour is the defect the second-line helper exists to paper over. For unrunnable stored values it answers `None` on one form (`days-str-1`) and raises one of five exception classes on the others (`UNRUNNABLE_STORED_VALUE_ERRORS`, `app/services/schedule_rules.py`). The reason for plan 15-16 (WR-01/WR-02 of the prior review) was exactly this mixed failure signal.

A future fix that makes the calculator validate its input and return one signal will redden this phase-15 rule. The only instruction the rule gives is to get an owner decision. This is the "phase tests pin pre-existing defects" pattern. Here it pins product source rather than behaviour, which is the strongest form of it.

**Fix:** Assert the property the prohibition protects, not the text. Keep a behavioural rule that `None` still means "no moments" (already held by `tests/test_services/test_schedule_service.py`), and that the calculator has no bare `try/except` that turns an exception into `None`. That can be checked with `ast`: no `ast.Try` whose handler returns `None`. Drop the digest. If the owner wants a freeze anyway, name the known defect in the rule's failure message so a fixer knows the red is expected.

## Info

### IN-07: Five sentinels still carry `limit={{ page_size }}`, and two renderers echo the request's `limit` into markup (pre-existing, confirmed)

**File:** `app/templates/history/list.html:119`, `app/templates/history/partial_cards.html:6`, `app/templates/admin/user_history.html:63`, `app/templates/admin/history_partial_cards.html:7`, `app/templates/account_groups/includes/sentinel.html:73`; renderers `app/pages/history.py:633` and `app/pages/admin.py:1572` (`"page_size": limit`)

**Issue:** Plan 15-21 removed `limit=` from six sentinels because a missing context key under soft `Undefined` renders `limit=`, which gets a 422 and leaves the sentinel spinning forever. These five keep that failure path. `test_markup_literal_inventory.py:63-72` names them and defers them to the next milestone, so this is not a phase regression.

Two partial renderers pass the request's own `limit` back as `page_size`. That value is FastAPI-validated as an int, so it is not an injection. But the next portion size then follows whatever the client sent rather than the server constant, which is the DEF-09-03 concern in another form.

**Fix:** Next milestone: apply the 15-21 change to these five, and stop echoing `limit` in `history.py:633` / `admin.py:1572`.

### IN-08: `app/dependencies.py:323` still hand-spells the notice URL (pre-existing, not a phase regression)

**File:** `app/dependencies.py:323` (`IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"`)

**Issue:** This is confirmed as the Phase 8 WR-03 residue. It builds the URL outside `respond()`'s `_with_notice` and the `notices` constant, and it is duplicated as a literal in `tests/test_pages/test_htmx_response_layer.py:69` and `tests/test_pages/test_auth_transport.py:1121`. The owner permitted it under row `10-18#3` as a known unfixed defect. No phase-15 file changed it or pins it; `test_write_path_invariants.py` does not reference it.

**Fix:** When it is addressed, build it as `f"/dashboard?{NOTICE_QUERY_KEY}={notices.IMPERSONATION_FORBIDDEN}"`, and import the constant in the two tests.

### IN-09: The shell layer-literal rule reddens on any `60` or `70` anywhere in an 8,946-line module

**File:** `tests/test_pages/test_shell.py` (`layer_literals_in`, `test_no_layer_of_the_table_is_written_into_the_shell_rules`)

**Issue:** The rule scans every non-docstring constant in `test_shell.py` for integers equal to the table's z-index layers, which are 60 and 70 today. It also scans strings containing them as standalone numbers. An unrelated future literal such as `timeout=60` or `"max-width: 70ch"` will redden it with the message "число слоя таблицы выписано в код правил". If a layer is ever set to a small number such as 2, the rule's own `assert len(layers) == 2` becomes an offence.

**Fix:** Limit the scan to functions that parse the stylesheet, or to constants compared against `_css_layer(...)` results. At minimum, list the rule's own control constants as exempt.

### IN-10: The same seven-line history comment is pasted into six handlers

**File:** `app/pages/accounts.py:171-177`, `:213-219`; `app/pages/ads.py:249-255`, `:303-309`; `app/pages/schedules.py:872-878`, `:938-944`

**Issue:** The identical "ЛЕТОПИСЬ (DEF-09-03)…" block appears six times. The project's own templates avoid exactly this ("чтобы два экземпляра одного довода не разъехались", `schedules/partial_cards.html:8-10`). The next edit to one copy will leave five stale copies.

**Fix:** Keep the full text once, for example next to `PAGE_SIZE` or in `test_markup_literal_inventory.py`'s docstring, where it already lives. Replace the six copies with a one-line pointer by name.

### IN-11: A new rule asserts two accepted accessibility defects as the required state

**File:** `tests/test_templates/test_banner_dismiss.py:998-1013` (`test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed`); records at `app/static/css/app.css:1330-1348`

**Issue:** Per the carry contract, rules that pin pre-existing defects must be named. This one reddens if the dismiss control stops being a checkbox or if the hiding moves off `:has(> .banner-dismiss:checked)`. Either of those is what a fix for these two defects looks like:
- focus falls to `<body>` on Space (WCAG 2.4.3)
- the control is announced as a "checkbox" (the role half of D-18.3 is unfixed)

Unlike WR-08, this pin is loud: the owner accepted it (Г-3), and both the CSS record and the rule's message say the red is expected. So it is Info, not Warning. It is still a phase-15 rule that a future fix must remove together with the code.

**Fix:** None needed now. When branch A is replaced by a `<button>`, remove this rule and its control in the same commit.

---

_Reviewed: 2026-09-27T11:20:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

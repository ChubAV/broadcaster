---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
reviewed: 2026-09-24T00:00:00Z
depth: standard
files_reviewed: 29
files_reviewed_list:
  - app/pages/accounts.py
  - app/pages/ads.py
  - app/pages/schedules.py
  - app/services/schedule_rules.py
  - app/static/css/app.css
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/ads/list.html
  - app/templates/ads/partial_cards.html
  - app/templates/includes/htmx_error_banner.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - scripts/prohibitions_census.py
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_billing_section.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_planning/test_plan_prohibitions_census.py
  - tests/test_services/test_schedule_rules_gate.py
  - tests/test_templates/test_banner_dismiss.py
  - tests/test_templates/test_degradation_pairs.py
  - tests/test_templates/test_form_inventory.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_markup_literal_inventory.py
findings:
  critical: 0
  warning: 4
  info: 6
  total: 10
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-09-24T00:00:00Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

Scope: the phase diff `040f6a7e^..HEAD` of the 29 listed files. The product changes are:
- the CR-01 fourth-entry fix in `schedules_update` (timezone fallback to a checked value plus `next_run_or_none`)
- the `schedule_rules.py` docstring
- `page_size` in context for the six list and portion templates (DEF-09-03)
- the banner-dismiss `aria-label`s and `.failure-stack > .alert` padding

The test and script additions are large and mostly new gate modules.

Security-relevant checks that came back clean:
- **Owner scoping in `schedules_update` did not move.** The `Schedule JOIN Ad WHERE Ad.user_id` lookup and `_ownership_verdict` still run before the timezone fallback and before the first model write. A refusal writes nothing. `test_malformed_stored_zone_access_predicate_is_unchanged` exercises both refusal branches.
- **The malformed stored zone no longer reaches the calculator.** `stored_tz` is checked against `VALID_TIMEZONES` and falls back to the profile zone, then to `UTC`. All 12 entries of `VALID_TIMEZONES` load in `zoneinfo` on this host.
- **No user-controlled value reaches the rendered `limit=`.** Both handlers of each section put the module constant `PAGE_SIZE` in the context, never the request's `limit`. `next_offset` / `next_after_id` are FastAPI-validated ints or DB ids, and filter values still go through `urlencode`. Every renderer of the six templates passes `page_size` (grep of `app/pages/*.py`). The remaining paginated templates (history, admin history, account groups) already used `{{ page_size }}`.
- The dismiss-label change keeps both labels distinct. The single source is `BANNER_DISMISS_ACCESSIBLE_NAMES`, and `test_shell.py` no longer references the removed `FAILURE_BANNER_DISMISS_LABEL`.

No blockers were found. The main concerns:
- The new second-line branch of `schedules_update` silently pauses a running schedule. The phase's own tests lock that in, and it contradicts the policy the JSON API and the page toggle document.
- A new AST rule forbids giving `schedules_create` the same second line.
- Four new GATE-10 degradation pairs pass on the handlers' "nothing deleted" branch.
- The census gate's phase-stamped literals will turn `just test` red on the next plan written into `.planning/phases/`, including gap-closure plans made from this review.

A targeted run of the phase-relevant rules passed: 96 passed, 68 deselected.

## Warnings

### WR-01: Editor save silently pauses a running schedule, and the phase tests lock this in

**File:** `app/pages/schedules.py:1330-1353`; pinned by `tests/test_pages/test_editor_schedules.py:4393-4445` (`test_malformed_stored_form_on_the_second_line_lands_one_outcome`) and `:4448-4469` (`test_malformed_stored_days_str_form_goes_the_same_way`)
**Issue:** When `next_run_or_none(schedule)` returns `None` on a complete, active schedule, the handler sets `schedule.is_active = False`, commits, and returns the normal success response. It sends no `notice`. The htmx fragment arrives with the toggle off, and the no-JS path gets a plain redirect to the editor. A running schedule stops sending, and nothing tells the person the save caused it.

The comment cites `schedules_toggle` as its model ("образец — `schedules_toggle` ниже"), but the two handlers do opposite things:
- The toggle (`:1521-1533`) leaves the row untouched and redirects with `notices.SCHEDULE_VALUES_OUT_OF_DOMAIN`.
- The JSON-API update (`app/routes/schedules.py:400-417`) rejects this outcome by name: "ОТКАЗ ЦЕЛИКОМ, А НЕ ВЫКЛЮЧЕНИЕ СТРОКИ. Тихо погасить … работающее расписание … — решение, которого клиент не просил и о котором не узнает".

The same fault therefore gets two opposite policies on two entries of one rule. That is the WR-05 pattern the module docstring of `schedule_rules.py` warns against.

Both phase-15 tests assert `status == 302` and `is_active is False` and never look at `Location`. A later fix that adds the explanation, or refuses as the other two entries do, will read as a regression of this phase. That trips the rule "phase tests can pin pre-existing defects".

The branch is only reachable when the first line fails: a sanitizer regression or a new form field. That lowers the likelihood, not the severity. When it fires, it fires silently.
**Fix:** Pick one policy for all three entries. The smallest change that matches the toggle is to keep the refusal explicit:
```python
next_run = next_run_or_none(schedule)
if next_run is None:
    # same outcome as schedules_toggle: nothing written, path named by a notice
    await db.rollback()
    return await respond(
        request,
        redirect=f"/ads/{ad_id}/edit",
        notice=notices.SCHEDULE_VALUES_OUT_OF_DOMAIN,
    )
schedule.next_run_at = next_run
```
If keeping the person's edit is preferred, save it paused but still pass `notice=` so the pause is announced. Change the two tests so they assert the notice code in `Location` (or the chosen refusal) rather than only `is_active is False`.

### WR-02: A new AST rule forbids giving `schedules_create` the same second line

**File:** `tests/test_pages/test_editor_schedules.py:4472-4518` (the assertion at `:4515`); product side `app/pages/schedules.py:1093-1111`
**Issue:** `test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save` requires exactly one direct `compute_next_run_at` call in the module, and requires it to be in `schedules_create` (`create_direct == ["compute_next_run_at"]`).

`schedules_create` builds `Schedule(is_active=complete, next_run_at=next_run)` from a direct calculator call. If the calculator ever returns `None` on a complete schedule, or raises one of the five `UNRUNNABLE_STORED_VALUE_ERRORS`, create fails in one of two ways:
- the pair (active, no moment) breaks `ck_schedules_active_requires_next_run`, a 500 at `commit()`
- the exception goes straight to the global 500 handler

This is exactly the "second line" argument plan 15-08 made for update ("Помощник держит исход, если первая линия пропустит значение — регрессией санитайзера или новым полем"), and it applies to create word for word. The new rule makes the asymmetry mandatory: routing create through the same guard turns this phase-15 test red. It is a second case of "phase tests can pin pre-existing defects" (the direct call in create predates the phase).
**Fix:** Give create the same second line by building the transient row first and asking the helper, or add a values-level twin of the helper to `schedule_rules.py`. Then relax the rule to "no page handler calls `compute_next_run_at` directly":
```python
assert "compute_next_run_at" not in update_calls
assert "compute_next_run_at" not in [n for n, _ in calls_in(functions["schedules_create"])]
```

### WR-03: The four new GATE-10 "degrades without htmx" pairs pass on the handlers' "nothing deleted" branch

**File:** `tests/test_pages/test_responsive_markup.py:1263` (`test_accounts_delete_confirm_degrades_without_htmx`), `:3492` (`test_ads_delete_confirm_degrades_without_htmx`), `:3560` (`test_admin_user_delete_confirm_degrades_without_htmx`); `tests/test_pages/test_ads_editor.py:1925` (`test_editor_ad_delete_confirm_degrades_without_htmx`)
**Issue:** After checking the markup, each test asserts only four things:
- `status_code in (302, 303)`
- no `HX-Location` header
- following `Location` returns 200
- the followed page contains `<!DOCTYPE`

It never asserts that the entity is gone, and never asserts which address it was sent to. Every one of these handlers answers the same kind of 302 on its refusal and no-op branches:
- `/login` when unauthenticated
- `/ads` for an out-of-range or missing ad (`app/pages/ads.py:1604-1614`)
- `/accounts` for a missing or foreign account (`app/pages/accounts.py:1407-1410`)
- `/admin/users/{id}` on the admin refusal branch (`app/pages/admin.py:2010`)

Each of those targets renders a full 200 document. A regression that turns the no-JS delete into a no-op, or into a refusal, keeps all four pairs green. The pairs then count toward `DEGRADATION_PAIRS_DECLARED` in `test_degradation_pairs.py` as evidence of a working path without htmx.

The billing pair added in the same plan does it right: it pins the exact `location`.
**Fix:** In each test, assert both the outcome and the destination:
```python
assert response.headers["location"] == "/ads"          # exact, not any redirect
assert await db_session.get(Ad, ad.id) is None           # after db_session.expire_all()
```
Use `MessengerAccount` for accounts and `User` for the admin case, and `"/accounts"` or `"/admin/users"` as the expected location.

### WR-04: The census gate's phase-stamped literals will turn `just test` red on the next plan written into `.planning/phases/`

**File:** `tests/test_planning/test_plan_prohibitions_census.py:125-162` (`PROHIBITIONS_DECLARED_AT_PHASE_15`, `PROHIBITIONS_BY_PHASE_DECLARED`, `TRUTHS_AT_PHASE_15`, `NAIVE_LINE_NET_AT_PHASE_15`), plus the registry bijection rules (`:867-912`)
**Issue:** The census universe is `.planning/phases/*/[0-9]*-PLAN.md` (`scripts/prohibitions_census.py:61`). Several rules compare it to literals stamped "at Phase 15":
- the count 697 and its per-phase breakdown
- the decomposition 697 − 24 + 119 + 17 = 809
- a one-to-one match with `15-prohibitions-registry.yaml`, including `rows_declared`

Any new plan file with a `must_haves.prohibitions` or statement-first `must_haves.truths` element breaks at least one of them. That includes gap-closure plans written into this phase directory, some of which will come from this review.

The comment at `:120-124` also says the literal cannot be raised honestly ("поднять его можно только переписав величину, чьё имя утверждает, чему она была равна в Фазе 15, — то есть солгать"). So the module gives the next plan no legitimate way to go green other than editing a phase-15-named constant.

Executors deselect `tests/test_planning/` (project memory "Orchestrator gate catches records defects"). The break will therefore show up only at the orchestrator's full-suite gate, after the gap plans have already run.
**Fix:** Make the declared numbers cover a fixed set of plans rather than every file the glob will ever match:
- measure over an explicitly listed set of plan files (for example, the 156 paths that existed on 2026-09-24, or all paths whose plan number is at most `15-14`)
- keep a separate, growing rule that only checks the one-to-one match with the registry for any newer plan

At minimum, document in `15-VALIDATION.md` or the gap-planning prompt that every new plan must re-seed the registry (`--seed-registry`) and add a new, differently named literal.

## Info

### IN-01: `verification: null` is treated as an absent key, contradicting the record's own docstring

**File:** `scripts/prohibitions_census.py:322` (docstring `:226-227`)
**Issue:** `element.get(VERIFICATION_KEY) if VERIFICATION_KEY in element else None` evaluates to `None` both when the key is missing and when it is present with a null or empty YAML value (`verification:`). The conditional is a no-op, since it equals `element.get(...)`. The docstring says `None` means "the key is absent" and that mixing the two "изъяло бы элемент из правила молча". `_breakdown` (`:935`) adds a third case: `record.verification or "—"` also treats `""` as absent.
**Fix:** Use a sentinel for "absent", for example `verification = element[VERIFICATION_KEY] if VERIFICATION_KEY in element else _ABSENT`. Report a present-but-null value as a `CensusError`.

### IN-02: A malformed registry fails with a raw traceback instead of `CensusError`

**File:** `scripts/prohibitions_census.py:416-427`, `:869-884`, `:916-922`
**Issue:** Several malformed inputs crash with the wrong error type:
- a non-mapping registry document: `.setdefault` raises `AttributeError`
- a row without `plan` or `index`: `KeyError`
- a non-integer `index`: `ValueError`
- a `class_decisions` entry that is a string: `PERMIT_SCOPE_FIELD in decision` does a substring test, then `decision[...]` raises `TypeError`

None of these goes through the `except CensusError` in `main()`. The user gets a stack trace instead of the `ОТКАЗ:` line the tool promises.
**Fix:** Check the shape in `load_registry` and `_registry_rows` (document is a dict, each row is a dict with `plan` and an int `index`, each decision is a dict) and raise `CensusError` naming the row.

### IN-03: Two different `_split_top_level` parsers in two gate modules

**File:** `tests/test_pages/test_htmx_gates.py:7009`, `tests/test_templates/test_htmx_markup_gates.py:9496`
**Issue:** Both were added this phase and share a name, but they behave differently:
- the first ignores `{}` nesting and supports multi-character separators
- the second nests on `{}` but compares `char == separator`, so it silently never splits on a multi-character separator

`test_markup_literal_inventory.py` explicitly imports its walker instead of rewriting it, "второй обход того же дерева разошёлся бы с первым молча". The same risk applies here.
**Fix:** Keep one implementation, for example in `test_htmx_markup_gates.py` where other shared walkers already live, and import it from the other module.

### IN-04: Comments point at line numbers that the next edit will shift

**File:** `app/static/css/app.css:1361` ("строки 1255-1258"); `tests/test_pages/test_editor_schedules.py:4533-4535`
**Issue:** The CSS block quotes the stack paragraph by line range. That range is correct today and wrong after any edit above it. The project's own precedent (`test_the_lever_note_points_by_name_and_not_by_line_number`) forbids line pointers.

The test comment says the imports are placed inside the rule "а не в шапке модуля: строка в шапке сдвинула бы номера строк". But plan 15-08 already added a six-line header import at `:45-50`, so the stated reason no longer holds.
**Fix:** Point to the paragraph by its heading or quoted text instead of line numbers. Remove or correct the stale reason in the test comment.

### IN-05: The page-size literal pattern only catches `limit=<digit>`

**File:** `tests/test_templates/test_markup_literal_inventory.py:90`
**Issue:** `(?<![-\w])limit=\d` misses other ways to write the number back into markup:
- `limit={{ 30 }}`
- `limit={{ '30' }}`
- `hx-vals='{"limit": 30}'`
- a `<input name="limit" value="30">`

Any of these reintroduces the second copy of the number that DEF-09-03 is about.
**Fix:** Widen the net to also match `limit=\{\{\s*['"]?\d` and `"limit"\s*:\s*\d`, and add synthetic controls for each form.

### IN-06: PyYAML stays an undeclared dependency and now has a new user

**File:** `scripts/prohibitions_census.py:58`; `tests/test_planning/test_plan_prohibitions_census.py:90-94`
**Issue:** The script and its gate `import yaml`, which reaches the project only through `uvicorn[standard]`'s extras. The risk is named in the docstring. It is not new (`tests/test_planning/test_state_progress_matches_roadmap.py` and `tests/test_pages/test_https_asset_scheme.py` import it too), but this phase adds another module that depends on it.
**Fix:** Declare `pyyaml` in the dev dependency group, or record the milestone's "0 new Python dependencies" exception in the decision log together with the uvicorn-extras dependency.

---

_Reviewed: 2026-09-24T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

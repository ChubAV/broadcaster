---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
reviewed: 2026-10-06T09:50:17Z
depth: standard
diff_base: 1659d86f
incremental_over: 2026-09-27T11:20:00Z
files_reviewed: 4
files_reviewed_list:
  - app/static/css/app.css
  - app/templates/ads/includes/media_upload_form.html
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_schedule_invariants.py
findings:
  critical: 0
  warning: 6
  info: 7
  total: 13
carried_forward:
  open: 8
  resolved: 1
  previously_closed: 10
new_findings: 5
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-10-06T09:50:17Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found
**Mode:** incremental. This run builds on the full-phase review of 2026-09-27 (38 files, `diff_base: c939cc8c`). Its scope is `git diff 1659d86f..HEAD` over the four listed files.

## Narrative Findings (AI reviewer)

## Summary

There are two commits in scope:
- **`d0a31bd9`** «fix(15): make «+ ФАЙЛ» reachable from the keyboard». It takes `hidden` off `#file-input`, adds the `.media-file-input` visually-hidden rule, draws the focus ring on the tile through `body:has(#file-input:focus-visible) .media-tile--add`, and hides the field at the ceiling through `body:has(.media-tile--add[hidden]) .media-file-input { visibility: hidden; }`. It also adds `test_the_file_field_is_reachable_from_the_keyboard`. This answers the owner's H7 «починить сейчас» (15-19 D4).
- **`560ce871`** «test(15): mark the compute_next_run_at freeze as characterisation». This answers the owner's H4(б).

**Checks that came back clean:**
- **D-09 still holds.** Without JS, upload remains impossible. The form still has no submit control (`form_wrapper` is called with no button). The `change` trigger needs htmx. Enter or Space on a `type=file` field opens the picker and does not trigger implicit submission, because a file field is not a field that submits the form implicitly. With JS off, a keyboard user can now reach a field that does nothing. A mouse user could already do the same through the label, so this is not new.
- **Tab order matches the visual order.** `#file-input` is the first focusable node after `#media-strip` (`ads/form.html:240-251`). Tab goes from the last «Убрать вложение» to the field, and the ring is drawn on the tile, which is the last item in the strip.
- **OOB re-render.** The removal response's OOB `#media-add-tile` (`media_add_tile.html:55`) and the upload response's innerHTML swap of `#media-strip` both flip `[hidden]` on the tile. `:has()` is live, so the field's `visibility` follows with no script. The upload form sits outside the swap target, so focus on the field survives an upload that stays below the ceiling.
- **Cascade.** `.media-file-input` (`app.css:2179`) comes after `.field__input` (`:740`) at equal specificity, so it overrides `padding` and `border`. `box-sizing: border-box` is global (`:433`). `.form-wrapper { position: relative }` (`:2319`) gives the absolute field a local containing block, and with no offsets it stays at its static position.
- **Marker is registered.** `characterisation` is registered in `tests/conftest.py:491-497`. No hook consumes it; it is a label only.

**Test run on this tree:** 260 passed. Modules: `test_ads_editor`, `test_schedule_invariants`, `test_ads_image_upload`, `test_walkthrough_anchors`, `test_htmx_markup_gates`, `test_banner_dismiss`.

**Main concerns (new):**
- When a keyboard upload reaches the ceiling, the fix hides the field that has focus. The keyboard user loses the visible focus point (WR-09).
- The new regression test checks text, not reachability. It stays green under the most likely ways the field could become unreachable again (WR-10).
- `560ce871` contradicts the module's own header comment about how the freeze is lifted (WR-11).

## Prior Findings Disposition

Every finding of the 2026-09-27 report is listed. The ten findings that report already closed are carried as `resolved`, with that report's evidence. Each was re-checked on today's tree:

| ID | Finding (short) | Disposition | Evidence |
|----|-----------------|-------------|----------|
| WR-01 | Editor save silently pauses a running schedule | **resolved** | Closed in the 2026-09-27 report (`5fa0552f`). `app/pages/schedules.py:1408-1413` still rolls back and refuses. |
| WR-02 | AST rule forbade the create-side second line | **resolved** | Closed 2026-09-27 (`0e86878a`). `schedules.py:1136-1142` still calls `next_run_or_none`. |
| WR-03 | Four GATE-10 degrade pairs passed on "nothing deleted" | **resolved** | Closed 2026-09-27. The meta-rule `test_degradation_pairs.py` (`test_every_redirecting_degradation_pair_asserts_the_exact_location`) is unchanged in range. |
| WR-04 | Census phase-stamped literals redden on next plan | **resolved** | Closed 2026-09-27. Its decimal-phase residue is WR-06, below. |
| IN-01 | `verification: null` read as absent | **resolved** | Closed 2026-09-27. `scripts/` is untouched in range. |
| IN-02 | Malformed registry gives a raw traceback | **resolved** | Closed 2026-09-27. `scripts/` is untouched in range. |
| IN-03 | Two `_split_top_level` parsers | **resolved** | Closed 2026-09-27. |
| IN-04 | Comments point at shiftable line numbers | **resolved** | Closed 2026-09-27. The new comment at `app.css:2174-2176` and `media_upload_form.html:80-85` points by name (`15-UAT.md` У-12, `.media-tile--add`), not by line. |
| IN-05 | Page-size literal pattern only `limit=<digit>` | **resolved** | Closed 2026-09-27. |
| IN-06 | PyYAML undeclared | **resolved** | Closed 2026-09-27. |
| WR-05 | Create/update refusal reuses the toggle's notice | **open: owner-accepted 2026-10-06** | Still true: `schedules.py:1140` and `:1412` both pass `notices.SCHEDULE_VALUES_OUT_OF_DOMAIN`. The owner answered H7 / 15-16 D5 «понятен, оставить» (`15-OWNER-DECISIONS-2026-10-06.md:28`). That is an acceptance, not a fix, so the finding stays open with its full text. |
| WR-06 | Census gate raises on decimal-numbered phases | **open** | Still true: `scripts/prohibitions_census.py:370` is `(\d+)-(\d+)-PLAN\.md`, and `:387` is `if not phase.isdigit()`. No commit in range touched `scripts/`. |
| WR-07 | Product test reads a Phase 10 planning artifact | **open** | Still true: `tests/test_pages/test_schedule_invariants.py:104-106` imports `walkthrough_source` from `tests.test_planning…`, and `:509` calls it. The module still has no `pytestmark`. `560ce871` touched this module but not this coupling. |
| WR-08 | `compute_next_run_at` frozen by a sha256 digest | **resolved** (owner chose the freeze; see WR-11 for residue) | WR-08 offered two fixes. The second was: "if the owner wants a freeze anyway, name the known defect in the rule's failure message so a fixer knows the red is expected". The owner took that branch (H4(б), `15-OWNER-DECISIONS-2026-10-06.md:21`). `560ce871` adds `@pytest.mark.characterisation` (`test_schedule_invariants.py:154`). The docstring now says the calculator has a known defect and that a fix should rewrite the digest (`:158-162`), and the failure message says the same (`:180-181`). That answers WR-08's concern: a fixer seeing red now learns that red is expected. The same commit left a contradiction and two unguided controls; those are filed as new finding WR-11 rather than keeping WR-08 open. |
| IN-07 | Five sentinels keep `limit={{ page_size }}`; two renderers echo `limit` | **open** | Still true: `history/list.html:119`, `history/partial_cards.html:6`, `admin/user_history.html:63`, `admin/history_partial_cards.html:7`, `account_groups/includes/sentinel.html:73`; `history.py:633` and `admin.py:1572` still pass `"page_size": limit`. |
| IN-08 | `app/dependencies.py:323` hand-spells the notice URL | **open** | Still true: `dependencies.py:323` is unchanged. |
| IN-09 | Shell layer-literal rule reddens on any `60`/`70` | **open** | Still true: `test_shell.py:6861` (`layer_literals_in`) and `:6884` are unchanged. |
| IN-10 | Seven-line history comment pasted into six handlers | **open** | Still true: `grep -c "ЛЕТОПИСЬ (DEF-09-03)" app/pages` gives 6. |
| IN-11 | New rule asserts two accepted a11y defects as required | **open: owner-accepted** | Still true: `test_banner_dismiss.py:998`. The owner accepted it as a consequence twice: Г-3, then H2 п.2 «принять как есть» and H5(5) «принять следствием» (`15-OWNER-DECISIONS-2026-10-06.md:18`, `:26`). |

## Warnings

### WR-05: The new create/update refusal reuses the toggle's notice, whose text tells an editor user to repeat the action that was just refused — open, owner-accepted 2026-10-06

**Disposition:** open, owner-accepted 2026-10-06. H7 / 15-16 D5: «понятен, оставить». No code change.

**File:** `app/pages/schedules.py:1136-1142` (create), `:1408-1413` (update); the text is at `app/pages/notices.py:272-279`. The code is pinned by `tests/test_pages/test_editor_schedules.py:4371` (`_refusal_landing`) and its uses at `:4506`, `:4574`, `:4604`, `:4726`, `:4777`.

**Issue:** Both new refusal branches reuse `SCHEDULE_VALUES_OUT_OF_DOMAIN`. That notice was written for the toggle (resume) entry: «Дни или часы этого расписания заданы значениями, которых система исполнить не может. Откройте расписание в редакторе объявления, выберите дни и время заново и сохраните — после этого включение сработает.»

On the two new entries this text is wrong:
- **Update.** The person is already in the editor and has just chosen days and times and pressed save. The handler rolls back their edits and redirects to `/ads/{ad_id}/edit` without `?sched=`, so the card comes back collapsed with the old values. The row stays **active**, so "после этого включение сработает" refers to an action nobody took. Following the text submits the same values through the same sanitizer and reaches the same refusal.
- **Create.** No schedule exists yet, so "Откройте расписание" points at nothing.

The branch is only reachable when the first line (`_clean_ints` / `_clean_times` / zone rollback) lets a value through. That lowers likelihood, not severity. When it fires, the only guidance the user gets sends them in a loop.

All five refusal tests assert `location == _refusal_landing(ad_id)`, which contains this exact code. Giving the save paths their own notice will redden five phase-15 tests. That is a mild case of "phase tests pin a defect": the tests pin a code whose registry text does not fit the entry.

**Fix (if the owner revisits):** Register a save-specific code in the closed registry. Use it on both new branches, and keep `SCHEDULE_VALUES_OUT_OF_DOMAIN` for the toggle. Also keep the card expanded:
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

### WR-06: The census gate raises `CensusError` on any decimal-numbered phase, and this project has used one — open

**Disposition:** open. Re-checked: `scripts/prohibitions_census.py:370` and `:387` are unchanged.

**File:** `scripts/prohibitions_census.py:358-360` (`phase_of`), `:370-382` (`plan_number_of`), `:385-389` (`_phase_number_of`), `:392-406` (`through_fixed_set`); consumers include `tests/test_planning/test_plan_prohibitions_census.py:962`, `:1217`, `:2814`.

**Issue:** `PLAN_GLOB = ".planning/phases/*/[0-9]*-PLAN.md"` matches a decimal phase's plans, for example `.planning/phases/15.1-x/15.1-01-PLAN.md`. Two functions then refuse that path:
- `_phase_number_of` refuses because `"15.1".isdigit()` is false.
- `plan_number_of` would also refuse, because `(\d+)-(\d+)-PLAN\.md` does not `fullmatch` `15.1-01-PLAN.md`.

Reproduced on the 2026-09-27 tree:
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

### WR-07: A product-suite test reads a Phase 10 planning artifact through a `test_planning` import, and will fail on milestone archive — open

**Disposition:** open. Re-checked: `test_schedule_invariants.py:104-106` and `:509` are unchanged, and the module still has no `pytestmark`. `560ce871` edited this module without touching the coupling.

**File:** `tests/test_pages/test_schedule_invariants.py:104-106` (import), `:509` (`seed_program(walkthrough_source())` inside `test_no_seed_lifts_check_constraints_without_rolling_back_first`)

**Issue:** The rule calls `seed_program(walkthrough_source())`. `walkthrough_source` (`tests/test_planning/test_the_walkthrough_stand_is_seedable.py:170-172`) reads `.planning/phases/10-rychag-components-modal-html/10-UAT.md`.

This module has no `pytestmark = pytest.mark.planning`. So:
1. `-m "not planning"`, the documented triage lever in `tests/conftest.py:477-488`, does not exclude it.
2. Phase 15 is the last phase of this milestone (`.planning/ROADMAP.md:77`). When `/gsd-complete-milestone` moves `.planning/phases/10-*` into the archive, this product test fails with `FileNotFoundError`. The census module does the same, but its boundary is documented; this one is not.

The phase itself added the rule that forbids this coupling for markup modules: `test_walkthrough_anchors.py` (`FORBIDDEN_IMPORT_PACKAGES = ("tests.test_planning", "tests.test_pages")`). Its reason applies word for word: a rule that reddens on someone else's work gets switched off together with its directory. `test_schedule_invariants.py` is the only file under `tests/test_pages/` that imports from `tests.test_planning`.

**Fix:** Move the walkthrough half of this rule into `tests/test_planning/test_the_walkthrough_stand_is_seedable.py`, which is already planning-marked, and keep only the tree scan (`SCANNED_TREES`) in `test_schedule_invariants.py`. Or split it into its own function with `@pytest.mark.planning`. Either way, drop the `tests.test_planning` import from the product module.

### WR-09: A keyboard upload that reaches the ceiling hides the field that has focus, and the visible focus point disappears (new, `d0a31bd9`)

**File:** `app/static/css/app.css:2183` (`body:has(.media-tile--add[hidden]) .media-file-input { visibility: hidden; }`), together with `app/templates/ads/includes/media_add_tile.html:54-55` (tile gets `hidden` when `attached_count >= max_images`). The upload form is `app/templates/ads/includes/media_upload_form.html:58-65` (`target='#media-strip'`, `trigger='change'`).

**Issue:** This is the exact path the fix opened for keyboard users:
1. Tab to `#file-input`, press Enter, pick files.
2. The picker closes and focus returns to the field. `change` fires and htmx posts.
3. The response swaps `#media-strip` innerHTML. If the count is now at the ceiling, the swap brings the tile back with `hidden`.
4. `:has()` re-matches, and the **still-focused** `#file-input` becomes `visibility: hidden`.

A `visibility: hidden` element is not focusable. On engines that apply the HTML focus-fixup rule (Chromium), focus falls to `<body>`. On engines that keep focus on the now-invisible node, the ring is still lost, because the only place it was drawn is the tile, which is now `display: none` (`app.css:2187`). Either way the keyboard user loses their place right after a successful upload.

This is the WCAG 2.4.3 / 2.4.7 failure the owner accepted for the banner in H2 п.2. Here it is a **new** instance created by this fix, and the owner has not accepted it. The CSS comment (`:2176`, «поле уходит из обхода вместе с ней») names the exit from the Tab order but not the loss of focus. The new test does not cover the ceiling transition.

**Fix:** Give focus a landing spot on the ceiling transition without a handler. htmx 2.0.10 (vendored, `app/static/js/htmx.min.js`) honours `autofocus` on swapped-in content. When the **upload** response renders the strip at the ceiling, put `autofocus` on the last `.media-tile__remove`. That is the nearest control, and the one a person at the ceiling needs next.
```jinja
{# media_strip.html, last remove button, upload response only #}
<button class="media-tile__remove" ... {% if at_ceiling and focus_on_ceiling %} autofocus{% endif %}>×</button>
```
Pass `focus_on_ceiling=True` only from the upload route, so a full page load does not steal focus. Alternatively, record this as a named, owner-accepted consequence next to the CSS rule and in the test docstring, as was done for the banner.

### WR-10: `test_the_file_field_is_reachable_from_the_keyboard` checks text, not reachability, and stays green when the field becomes unreachable again (new, `d0a31bd9`)

**File:** `tests/test_pages/test_ads_editor.py:1890-1934` (asserts at `:1915`, `:1919`, `:1927-1934`)

**Issue:** This test is the only regression guard for the owner's «починить сейчас» item. It asserts four things:
- the tag has no `" hidden"` substring
- the tag has the class `media-file-input`
- two literal CSS strings are present

Each of the following regressions makes the field unreachable from the keyboard again, and all of them pass the test:
- `tabindex="-1"` or `disabled` added to the tag.
- `display: none` or `visibility: hidden` added **inside** `.media-file-input { … }` (`app.css:2179-2182`). That is a natural "cleanup" for a class called "visually hidden".
- The upload form moved before `#media-strip` in `ads/form.html`. The field stays focusable, but Tab then reaches it *before* the remove buttons while the ring appears on the tile at the end of the strip. The template comment at `media_upload_form.html:83-84` says the order is load-bearing («форма лежит сразу за полосой»), but nothing pins it.
- The tile losing `for="file-input"`. The field keeps its tab stop but loses its accessible name «+ ФАЙЛ».

It also fails in the opposite direction. `"… { visibility: hidden; }"` is matched character for character, so reformatting the rule onto three lines reddens the test with a message that claims the field "остаётся в обходе на потолке", which would be false.

**Fix:** Assert the properties, not the spelling:
```python
assert not re.search(r"\s(hidden|disabled)(\s|=|>|$)", tag) and 'tabindex="-1"' not in tag
body = _css_rule_body(css, ".media-file-input")          # parse, don't substring
assert "display" not in body and "visibility" not in body
assert re.search(r"body:has\(\.media-tile--add\[hidden\]\)\s*\.media-file-input\s*\{\s*visibility:\s*hidden;?\s*\}", css)
assert html.index('id="media-strip"') < html.index('id="file-input"')
assert 'for="file-input"' in html
```
`test_shell.py` and `test_htmx_markup_gates.py` already have CSS-rule extraction helpers; reuse one rather than adding a third.

### WR-11: `560ce871` tells the fixer to rewrite the digest in the same commit, while the module header still forbids exactly that; two unmarked controls pin the same digest (new)

**File:** `tests/test_pages/test_schedule_invariants.py:137-139` (header) vs `:158-162` (docstring) and `:180-181` (failure message); controls `:185-195`, `:198-206`

**Issue:** The two instructions now contradict each other, 20 lines apart:
- **Header comment, unchanged (`:138-139`):** «Правка ОБЯЗАНА сопровождаться решением владельца, снимающим запрет, а не подъёмом константы в том же коммите.»
- **New text (`:162`, `:181`):** «перепиши отпечаток вместе с починкой» / «перепиши отпечаток тем же коммитом».

A fixer who reads the module top-down gets opposite answers. An executor bound by the header is told to stop and escalate; one bound by the message is told to bump the constant. The H4(б) owner decision covers the marker. It does not say which of the two procedures now applies, so the header was simply not updated.

The marker also covers only one of three tests that pin `NEXT_RUN_CALCULATOR_SOURCE_DIGEST`:
- `test_control_a_body_edit_of_the_calculator_changes_its_digest` (`:187`) asserts the live digest **equals** the constant. It then needs the anchors `"    tz = ZoneInfo(tz_name)\n"` and `"range(8)"` to occur exactly once (`:190`, `:194`; today at `app/services/schedule_service.py:19`, `:31`). A real fix that validates `tz_name` or rewrites the look-ahead loop removes an anchor. The control then fails with «якорь контроля встречается 0 раз», with no `characterisation` mark and no hint that the red is expected.
- `test_control_a_helper_next_to_the_calculator_keeps_its_digest` (`:206`) has the same equality and is also unmarked.

**Fix:**
1. Rewrite `:137-139` to match the owner's H4(б) answer, for example: «Правка, ЧИНЯЩАЯ вычислитель, переписывает отпечаток тем же коммитом (решение владельца 2026-10-06, H4 (б)); правка, вносящая перехват внутрь, — нарушение `10-55#0`.»
2. Mark both controls `@pytest.mark.characterisation`. Make the body-edit control build its own synthetic source instead of anchoring on live calculator lines, so a fix that touches `ZoneInfo(...)` or `range(8)` does not redden it with a misleading anchor message.

## Info

### IN-07: Five sentinels still carry `limit={{ page_size }}`, and two renderers echo the request's `limit` into markup (pre-existing, confirmed) — open

**Disposition:** open. Re-checked: all seven sites are unchanged.

**File:** `app/templates/history/list.html:119`, `app/templates/history/partial_cards.html:6`, `app/templates/admin/user_history.html:63`, `app/templates/admin/history_partial_cards.html:7`, `app/templates/account_groups/includes/sentinel.html:73`; renderers `app/pages/history.py:633` and `app/pages/admin.py:1572` (`"page_size": limit`)

**Issue:** Plan 15-21 removed `limit=` from six sentinels because a missing context key under soft `Undefined` renders `limit=`, which gets a 422 and leaves the sentinel spinning forever. These five keep that failure path. `test_markup_literal_inventory.py:63-72` names them and defers them to the next milestone, so this is not a phase regression.

Two partial renderers pass the request's own `limit` back as `page_size`. That value is FastAPI-validated as an int, so it is not an injection. But the next portion size then follows whatever the client sent rather than the server constant, which is the DEF-09-03 concern in another form.

**Fix:** Next milestone: apply the 15-21 change to these five, and stop echoing `limit` in `history.py:633` / `admin.py:1572`.

### IN-08: `app/dependencies.py:323` still hand-spells the notice URL (pre-existing, not a phase regression) — open

**Disposition:** open. Re-checked: `dependencies.py:323` is unchanged.

**File:** `app/dependencies.py:323` (`IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"`)

**Issue:** This is confirmed as the Phase 8 WR-03 residue. It builds the URL outside `respond()`'s `_with_notice` and the `notices` constant, and it is duplicated as a literal in `tests/test_pages/test_htmx_response_layer.py:69` and `tests/test_pages/test_auth_transport.py:1121`. The owner permitted it under row `10-18#3` as a known unfixed defect. No phase-15 file changed it or pins it; `test_write_path_invariants.py` does not reference it.

**Fix:** When it is addressed, build it as `f"/dashboard?{NOTICE_QUERY_KEY}={notices.IMPERSONATION_FORBIDDEN}"`, and import the constant in the two tests.

### IN-09: The shell layer-literal rule reddens on any `60` or `70` anywhere in an 8,946-line module — open

**Disposition:** open. Re-checked: `test_shell.py:6861` and `:6884` are unchanged.

**File:** `tests/test_pages/test_shell.py:6861` (`layer_literals_in`), `:6884` (`test_no_layer_of_the_table_is_written_into_the_shell_rules`)

**Issue:** The rule scans every non-docstring constant in `test_shell.py` for integers equal to the table's z-index layers, which are 60 and 70 today. It also scans strings containing them as standalone numbers. An unrelated future literal such as `timeout=60` or `"max-width: 70ch"` will redden it with the message "число слоя таблицы выписано в код правил". If a layer is ever set to a small number such as 2, the rule's own `assert len(layers) == 2` becomes an offence.

**Fix:** Limit the scan to functions that parse the stylesheet, or to constants compared against `_css_layer(...)` results. At minimum, list the rule's own control constants as exempt.

### IN-10: The same seven-line history comment is pasted into six handlers — open

**Disposition:** open. Re-checked: `grep -c "ЛЕТОПИСЬ (DEF-09-03)"` over `app/pages` still gives 6.

**File:** `app/pages/accounts.py:171-177`, `:213-219`; `app/pages/ads.py:249-255`, `:303-309`; `app/pages/schedules.py:872-878`, `:938-944`

**Issue:** The identical "ЛЕТОПИСЬ (DEF-09-03)…" block appears six times. The project's own templates avoid exactly this ("чтобы два экземпляра одного довода не разъехались", `schedules/partial_cards.html:8-10`). The next edit to one copy will leave five stale copies.

**Fix:** Keep the full text once, for example next to `PAGE_SIZE` or in `test_markup_literal_inventory.py`'s docstring, where it already lives. Replace the six copies with a one-line pointer by name.

### IN-11: A new rule asserts two accepted accessibility defects as the required state — open, owner-accepted

**Disposition:** open, owner-accepted. Г-3, then on 2026-10-06 H2 п.2 «принять как есть» and H5(5) «принять следствием». Re-checked: `test_banner_dismiss.py:998` is unchanged.

**File:** `tests/test_templates/test_banner_dismiss.py:998-1013` (`test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed`); records at `app/static/css/app.css:1330-1348`

**Issue:** Per the carry contract, rules that pin pre-existing defects must be named. This one reddens if the dismiss control stops being a checkbox or if the hiding moves off `:has(> .banner-dismiss:checked)`. Either of those is what a fix for these two defects looks like:
- focus falls to `<body>` on Space (WCAG 2.4.3)
- the control is announced as a "checkbox" (the role half of D-18.3 is unfixed)

This pin is loud: the owner accepted it, and both the CSS record and the rule's message say the red is expected. So it is Info, not Warning. It is still a phase-15 rule that a future fix must remove together with the code.

**Fix:** None needed now. When branch A is replaced by a `<button>`, remove this rule and its control in the same commit.

### IN-12: `.media-tile--add:focus-visible` is dead, and sharing a selector list with `:has()` makes the whole ring rule all-or-nothing (new, `d0a31bd9`)

**File:** `app/static/css/app.css:2177-2178`

**Issue:** The comment right above (`:2174-2175`) says «подпись не фокусируема». A `<label>` with no `tabindex` never matches `:focus-visible`, so the first selector in the list can never apply. It is a leftover of the old rule, which the owner's H7 note described as never firing.

Because the dead selector shares a list with `body:has(...)`, an engine that cannot parse `:has()` drops the **whole** rule. On such an engine:
- The visually-hidden field has no visible focus indicator anywhere (WCAG 2.4.7).
- The ceiling rule at `:2183` is dropped too, so the field stays in the Tab order at the ceiling.

The project already relies on `:has()` in 14 places, so this is a baseline choice, not a regression. That is why it is Info.

**Fix:** Delete `.media-tile--add:focus-visible,` and leave only `body:has(#file-input:focus-visible) .media-tile--add`. Consider scoping both `:has()` rules to `[data-editor]` instead of `body`, so a second `.media-tile--add[hidden]` elsewhere on a page cannot hide every `.media-file-input`.

### IN-13: The visually-hidden declaration block is now duplicated (new, `d0a31bd9`)

**File:** `app/static/css/app.css:2179-2182` (`.media-file-input`) duplicates `:801-804` (`.toggle__input`) word for word

**Issue:** The same seven declarations now live in two places. If someone hardens one copy (for example, adding `clip-path: inset(50%)` alongside the deprecated `clip`), the other drifts silently. This is the duplication pattern the project's own comments warn against.

**Fix:** Use one shared selector list, `.toggle__input, .media-file-input { … }`, or a single `.visually-hidden` utility applied to both inputs.

---

_Reviewed: 2026-10-06T09:50:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental over the 2026-09-27 review; diff_base 1659d86f)_

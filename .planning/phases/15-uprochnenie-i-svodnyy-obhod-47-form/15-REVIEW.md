---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
reviewed: 2026-10-06T10:10:22Z
depth: standard
diff_base: 6711465e
incremental_over: 2026-10-06T09:50:17Z
files_reviewed: 5
files_reviewed_list:
  - app/pages/ads.py
  - app/templates/ads/includes/media_strip.html
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_ads_image_upload.py
  - tests/test_pages/test_schedule_invariants.py
findings:
  critical: 1
  warning: 3
  info: 10
  total: 14
carried_forward:
  open: 10
  resolved_this_run: 3
  previously_closed: 11
new_findings: 4
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-10-06T10:10:22Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found
**Mode:** incremental. This run builds on the 2026-10-06T09:50:17Z review (`diff_base: 1659d86f`), which itself built on the full-phase review of 2026-09-27. Its scope is `git diff 6711465e..HEAD` over the five listed files. The only code commit in range is **`568b8f75`** «fix(15): close review findings WR-09, WR-10, WR-11». `f12cf18d` is planning-only.

## Narrative Findings (AI reviewer)

## Summary

`568b8f75` does what it says for each of the three findings:
- **WR-09.** The upload route passes `focus_on_ceiling: True` (`app/pages/ads.py:1405-1407`). The strip puts `autofocus` on the last «Убрать вложение» only when that flag is set and the strip is at the ceiling (`media_strip.html:89`, `:114`). The vendored htmx focuses `[autofocus]` inside swapped-in nodes during settle (`htmx.min.js`, function `Ne`, called from the settle task `Ae`).
- **WR-10.** The keyboard rule now checks properties and parses the stylesheet with `test_shell.py`'s helpers.
- **WR-11.** The header now agrees with the rule. The controls run on a synthetic source.

**Checks that came back clean:**
- **No autofocus leaks into other responses.** The page render (`ads/form.html:240-245`) does not pass the flag. The removal response (`autosave_response.html`) does not include `media_strip.html` at all. The part-count refusal branch prints only `media_refusals.html`. The guard `focus_on_ceiling is defined and …` keeps the strip safe under either `Undefined` flavour.
- **Refusals at the ceiling.** Refusal rows are `role="alert"` (`media_refusals.html:42`), so they are announced even though focus moves past them to the remove button.
- **No duplicate test collection.** `tests/__init__.py` and `tests/test_pages/__init__.py` exist, so `from tests.test_pages.test_shell import …` reuses the module that pytest collected. Three other modules already import from `test_shell` (`test_components.py`, `test_htmx_response_contract.py`, `test_failure_banner_invariants.py`). The imported names start with `_`, so they are not collected.
- **Synthetic controls still guard the instrument.** The body-edit control asserts `original is not None`, which rules out a vacuous `None == None` in the helper control. Each anchor occurs exactly once in `_SYNTHETIC_CALCULATOR`. The live constant `698f47d4e018` is unchanged.
- **Test run:** the WR-09 test and the ceiling tests in `test_ads_image_upload.py` pass (3), as do the three calculator tests in `test_schedule_invariants.py` (3) and `test_the_file_field_is_reachable_from_the_keyboard` (1).

**Main concern (new):** the WR-09 fix moves focus without checking where focus is when the response lands. Uploads take time, the editor stays editable while they run (`disabled_elt=''`), and the ad form autosaves on `keyup`. Someone who keeps typing during an upload can have their next Space or Enter press «Убрать вложение» (CR-01).

## Prior Findings Disposition

| ID | Finding (short) | Disposition | Evidence |
|----|-----------------|-------------|----------|
| WR-01 | Editor save silently pauses a running schedule | **resolved** | Closed 2026-09-27 (`5fa0552f`). `app/pages/schedules.py` is untouched in range. |
| WR-02 | AST rule forbade the create-side second line | **resolved** | Closed 2026-09-27 (`0e86878a`). `schedules.py` is untouched in range. |
| WR-03 | Four GATE-10 degrade pairs passed on "nothing deleted" | **resolved** | Closed 2026-09-27. |
| WR-04 | Census phase-stamped literals redden on next plan | **resolved** | Closed 2026-09-27. The residue is WR-06. |
| WR-08 | `compute_next_run_at` frozen by a sha256 digest | **resolved** | Closed 2026-10-06T09:50 (`560ce871`, owner H4(б)). Its residue was WR-11, which is resolved below. |
| IN-01..IN-06 | (see 2026-09-27 report) | **resolved** | Closed 2026-09-27. `scripts/` is untouched in range. |
| WR-05 | Create/update refusal reuses the toggle's notice | **open: owner-accepted 2026-10-06** | `schedules.py` is untouched in range. Owner answer H7 / 15-16 D5 «понятен, оставить» (`15-OWNER-DECISIONS-2026-10-06.md:28`). |
| WR-06 | Census gate raises on decimal-numbered phases | **open** | `scripts/` is untouched in range (`git diff --stat 6711465e..HEAD -- scripts` is empty). |
| WR-07 | Product test reads a Phase 10 planning artifact | **open** | Still true: the import is at `test_schedule_invariants.py:104-107`, and the call moved to `:534` (`seed_program(walkthrough_source())`) because `568b8f75` added lines above it. The module still has no `pytestmark`. |
| WR-09 | Keyboard upload at the ceiling hides the focused field | **resolved** (residue: CR-01) | `568b8f75`: `app/pages/ads.py:1405-1407` passes the flag, `media_strip.html:89` and `:114` print `autofocus` on the last remove button at the ceiling, and `test_ads_image_upload.py:666-707` pins both cases (no `autofocus` below the ceiling, last button only at it). The orchestrator saw htmx 2.0.10 move focus in live Chrome. The landing is correct for the case WR-09 described. The new defect is that the move is unconditional; that is filed as CR-01. |
| WR-10 | Keyboard rule checks text, not reachability | **resolved** | `568b8f75`: `test_ads_editor.py:1924-1935` checks for `hidden`, `disabled`, `inert` and a negative `tabindex`. `:1936` checks the strip-before-field order, and `:1940-1944` checks `for="file-input"`. `:1946-1974` parses the stylesheet: no `display`/`visibility` in `.media-file-input`, `visibility: hidden` at the ceiling, and `var(--focus-ring)` in the ring. The orchestrator confirmed that all four WR-10 regressions now redden the rule and that a reformatted rule does not. Remaining gap (accepted as is): the property checks only see rules whose selector list contains exactly `.media-file-input`. A `#file-input { display: none }` or `input[type=file] { … }` rule would not be seen. |
| WR-11 | Header contradicts the rule; controls pin the live digest | **resolved** (residue: IN-16) | `568b8f75`: the header at `test_schedule_invariants.py:138-149` now agrees with the docstring and failure message, and it keeps the old wording as a named record. The controls at `:204-231` run on `_SYNTHETIC_CALCULATOR` (`:151-158`), so a calculator fix no longer trips them. The header ties the procedure to H4(б). That link holds because the `characterisation` marker the owner chose is registered as «красный при починке … означает "перепиши слепок"» (`tests/conftest.py:493-496`). |
| IN-07 | Five sentinels keep `limit={{ page_size }}`; two renderers echo `limit` | **open** | No touched file in range. |
| IN-08 | `app/dependencies.py:323` hand-spells the notice URL | **open** | Untouched in range. |
| IN-09 | Shell layer-literal rule reddens on any `60`/`70` | **open** | `test_shell.py` is untouched in range. |
| IN-10 | Seven-line history comment pasted into six handlers | **open** | Still 2 copies each in `accounts.py`, `ads.py` (`:249`, `:303`) and `schedules.py`, 6 in total. The `ads.py` edit in range is at `:1405` and does not touch them. |
| IN-11 | New rule asserts two accepted a11y defects | **open: owner-accepted** | `test_banner_dismiss.py` is untouched in range. Owner: Г-3, H2 п.2, H5(5). |
| IN-12 | Dead `.media-tile--add:focus-visible` shares a list with `:has()` | **open** | `app/static/css/app.css:2177-2178` is unchanged (`app/static` is untouched in range). |
| IN-13 | Visually-hidden block duplicated | **open** | `app.css:2179-2182` is unchanged. |

## Critical Issues

### CR-01: The ceiling autofocus takes focus from wherever the person is when the upload response arrives, and the next Space or Enter removes an attachment (new, `568b8f75`)

**File:** `app/templates/ads/includes/media_strip.html:114`, `app/pages/ads.py:1407`. Context: `app/templates/ads/includes/media_upload_form.html:58-65` (`disabled_elt=''`, `sync='this:queue last'`) and `app/templates/ads/form.html:149-155` (`#ad-form` autosaves on `keyup changed delay:2s`). Pinned by `tests/test_pages/test_ads_image_upload.py:704`.

**Issue:** The fix assumes focus is still on `#file-input` when the response lands. Nothing checks that:
- `autofocus` is printed on every upload response that reaches the ceiling.
- The vendored htmx calls `.focus()` on it during settle with no condition (`htmx.min.js`, `function Ne(e){…n.focus()}`).

An upload is not instant. It covers a multipart POST, content sniffing and an S3 write for each file. During that time the editor stays fully editable: the upload form disables nothing (`disabled_elt=''`), and the ad form is built for typing while things happen in the background (autosave on `keyup`). The likely sequence:
1. Pick 2 files with 2 already attached (`max_images_per_ad = 4`). The upload starts on `change`.
2. Click into «ТЕКСТ» or «НАЗВАНИЕ» and keep typing.
3. The response arrives at the ceiling, and htmx moves focus to the last `.media-tile__remove`.
4. The next Space in the person's text activates that button: `type="submit" name="remove_image" form="ad-form"`. Enter does the same. The ad form posts with `remove_image=<key>`, and the handler (`ads.py:713`) removes the attachment that was just uploaded. The tile disappears, and the typed character never reaches the text.

The same theft happens to a keyboard user who tabbed on during the upload, and to a mouse user who clicked elsewhere. Only the person who stayed on the field gets the intended result. WR-09 asked for a landing spot for focus that was **lost**. This commit moves focus that is **held**, and the remove button is the most destructive control in the strip. The test pins the unconditional form (`[False, False, False, True]` regardless of where focus is), so the correct fix will need to change it.

**Fix:** Move focus only when it was actually lost, meaning it is on the field or on `<body>` at settle time. Keep the server-side choice of target, but make it a data marker rather than `autofocus`:
```jinja
{# media_strip.html:114 #}
{%- if focus_on_ceiling is defined and focus_on_ceiling and loop.last and strip_at_ceiling %} data-ceiling-focus{% endif %}
```
```jinja
{# media_upload_form.html: on the upload form (or via the project's handler registry) #}
hx-on::after-settle="const a = document.activeElement;
  if (a === document.body || a && a.id === 'file-input') {
    document.querySelector('#media-strip [data-ceiling-focus]')?.focus();
  }"
```
Then:
- Update `test_ads_image_upload.py:704` to assert the marker, not `autofocus`.
- Add a rule that the strip never carries `autofocus`.

If handlers are off the table under the project's handler gates, the owner has to choose between this condition and WR-09's original fallback: an accepted, named consequence for the ceiling focus loss. Leaving focus loss in place is less harmful than letting a keystroke delete an attachment.

## Warnings

### WR-05: The new create/update refusal reuses the toggle's notice, whose text tells an editor user to repeat the action that was just refused — open, owner-accepted 2026-10-06

**Disposition:** open, owner-accepted 2026-10-06. H7 / 15-16 D5: «понятен, оставить». No code change. `schedules.py` is untouched in this range.

**File:** `app/pages/schedules.py:1136-1142` (create), `:1408-1413` (update). The text is at `app/pages/notices.py:272-279`. The code is pinned by `tests/test_pages/test_editor_schedules.py:4371` (`_refusal_landing`) and its uses at `:4506`, `:4574`, `:4604`, `:4726`, `:4777`.

**Issue:** Both new refusal branches reuse `SCHEDULE_VALUES_OUT_OF_DOMAIN`. That notice was written for the toggle (resume) entry: «Дни или часы этого расписания заданы значениями, которых система исполнить не может. Откройте расписание в редакторе объявления, выберите дни и время заново и сохраните — после этого включение сработает.»

On the two new entries this text is wrong:
- **Update.** The person is already in the editor and has just chosen days and times and pressed save. The handler rolls back their edits and redirects to `/ads/{ad_id}/edit` without `?sched=`, so the card comes back collapsed with the old values. The row stays **active**, so "после этого включение сработает" refers to an action nobody took. Following the text submits the same values through the same sanitizer and reaches the same refusal.
- **Create.** No schedule exists yet, so "Откройте расписание" points at nothing.

The branch is only reachable when the first line (`_clean_ints` / `_clean_times` / zone rollback) lets a value through. That lowers likelihood, not severity. When it fires, the only guidance the user gets sends them in a loop.

All five refusal tests assert `location == _refusal_landing(ad_id)`, which contains this exact code. Giving the save paths their own notice will redden five phase-15 tests.

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
Point `_refusal_landing` at the new code in the same commit.

### WR-06: The census gate raises `CensusError` on any decimal-numbered phase, and this project has used one — open

**Disposition:** open. `scripts/` is untouched in range.

**File:** `scripts/prohibitions_census.py:358-360` (`phase_of`), `:370-382` (`plan_number_of`), `:385-389` (`_phase_number_of`), `:392-406` (`through_fixed_set`). Consumers include `tests/test_planning/test_plan_prohibitions_census.py:962`, `:1217`, `:2814`.

**Issue:** `PLAN_GLOB = ".planning/phases/*/[0-9]*-PLAN.md"` matches a decimal phase's plans, for example `.planning/phases/15.1-x/15.1-01-PLAN.md`. Two functions then refuse that path:
- `_phase_number_of` refuses because `"15.1".isdigit()` is false.
- `plan_number_of` would also refuse, because `(\d+)-(\d+)-PLAN\.md` does not `fullmatch` `15.1-01-PLAN.md`.

Reproduced on the 2026-09-27 tree:
```
through_fixed_set({'.planning/phases/15.1-x/15.1-01-PLAN.md': ...})
-> CensusError: `.planning/phases/15.1-x/15.1-01-PLAN.md`: номер фазы `15.1` — не число
```
`through_fixed_set` runs over the whole live universe in the fixed-set fixture and in the growing-half rule. One `/gsd-phase insert` (which creates decimal phases, per `.claude/gsd-core/workflows/insert-phase.md:4`) therefore turns the census module red with a tool refusal, not a named offence. The project has done this before: `.planning/milestones/v2.0-phases/05.1-edinaya-podpiska`. Executors deselect `tests/test_planning/`, so the break would first show up at the orchestrator's full-suite gate.

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

**Disposition:** open. `568b8f75` edited this module but not this coupling. The call has moved from `:509` to `:534`.

**File:** `tests/test_pages/test_schedule_invariants.py:104-107` (import), `:534` (`seed_program(walkthrough_source())` inside `test_no_seed_lifts_check_constraints_without_rolling_back_first`)

**Issue:** The rule calls `seed_program(walkthrough_source())`. `walkthrough_source` (`tests/test_planning/test_the_walkthrough_stand_is_seedable.py:170-172`) reads `.planning/phases/10-rychag-components-modal-html/10-UAT.md`. This module has no `pytestmark = pytest.mark.planning`, which has two consequences:
1. `-m "not planning"`, the documented triage lever in `tests/conftest.py:477-488`, does not exclude it.
2. Phase 15 is the last phase of this milestone. When `/gsd-complete-milestone` moves `.planning/phases/10-*` into the archive, this product test fails with `FileNotFoundError`.

The phase itself added the rule that forbids this coupling for markup modules (`FORBIDDEN_IMPORT_PACKAGES = ("tests.test_planning", "tests.test_pages")`). Its reason applies word for word.

**Fix:** Move the walkthrough half of this rule into `tests/test_planning/test_the_walkthrough_stand_is_seedable.py`, and keep only the tree scan (`SCANNED_TREES`) here. Or split it into its own function with `@pytest.mark.planning`. Either way, drop the `tests.test_planning` import from the product module.

## Info

### IN-07: Five sentinels still carry `limit={{ page_size }}`, and two renderers echo the request's `limit` into markup (pre-existing, confirmed) — open

**Disposition:** open. No touched file in range.

**File:** `app/templates/history/list.html:119`, `app/templates/history/partial_cards.html:6`, `app/templates/admin/user_history.html:63`, `app/templates/admin/history_partial_cards.html:7`, `app/templates/account_groups/includes/sentinel.html:73`. Renderers: `app/pages/history.py:633` and `app/pages/admin.py:1572` (`"page_size": limit`).

**Issue:** Plan 15-21 removed `limit=` from six sentinels. The reason: when the context key is missing, soft `Undefined` renders `limit=`, which gets a 422 and leaves the sentinel spinning forever. These five keep that failure path. `test_markup_literal_inventory.py:63-72` names them and defers them to the next milestone. Two partial renderers pass the request's own `limit` back as `page_size`, so the next portion follows the client rather than the server constant.

**Fix:** Next milestone: apply the 15-21 change to these five, and stop echoing `limit`.

### IN-08: `app/dependencies.py:323` still hand-spells the notice URL (pre-existing) — open

**Disposition:** open. Untouched in range.

**File:** `app/dependencies.py:323` (`IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"`)

**Issue:** The URL is built outside `respond()`'s `_with_notice` and the `notices` constant. It is duplicated as a literal in `tests/test_pages/test_htmx_response_layer.py:69` and `tests/test_pages/test_auth_transport.py:1121`. The owner permitted it under row `10-18#3`.

**Fix:** Build it as `f"/dashboard?{NOTICE_QUERY_KEY}={notices.IMPERSONATION_FORBIDDEN}"`, and import the constant in the two tests.

### IN-09: The shell layer-literal rule reddens on any `60` or `70` anywhere in an 8,946-line module — open

**Disposition:** open. `test_shell.py` is untouched in range. Its private helpers now have one more importer (`test_ads_editor.py:54`), which makes the module's rules about its own constants slightly more coupled than before.

**File:** `tests/test_pages/test_shell.py:6861` (`layer_literals_in`), `:6884`

**Issue:** The rule scans every non-docstring constant in `test_shell.py` for integers equal to the table's z-index layers (60 and 70). An unrelated future `timeout=60` or `"max-width: 70ch"` would redden it.

**Fix:** Limit the scan to functions that parse the stylesheet, or list the rule's own control constants as exempt.

### IN-10: The same seven-line history comment is pasted into six handlers — open

**Disposition:** open. Still 6 copies.

**File:** `app/pages/accounts.py:171-177`, `:213-219`; `app/pages/ads.py:249-255`, `:303-309`; `app/pages/schedules.py:872-878`, `:938-944`

**Issue:** The identical «ЛЕТОПИСЬ (DEF-09-03)…» block appears six times. The next edit to one copy will leave five stale ones.

**Fix:** Keep the full text once and replace the six copies with a one-line pointer by name.

### IN-11: A new rule asserts two accepted accessibility defects as the required state — open, owner-accepted

**Disposition:** open, owner-accepted: Г-3, then H2 п.2 «принять как есть» and H5(5) «принять следствием» on 2026-10-06. Untouched in range.

**File:** `tests/test_templates/test_banner_dismiss.py:998-1013`. Records at `app/static/css/app.css:1330-1348`.

**Issue:** The rule reddens if the dismiss control stops being a checkbox, or if the hiding moves off `:has(> .banner-dismiss:checked)`. Either of those is what a fix for the two defects looks like: focus falling to `<body>` on Space, and the "checkbox" role. The pin is loud and accepted.

**Fix:** None now. When branch A becomes a `<button>`, remove this rule and its control in the same commit.

### IN-12: `.media-tile--add:focus-visible` is dead, and sharing a selector list with `:has()` makes the whole ring rule all-or-nothing — open

**Disposition:** open. `app.css:2177-2178` is unchanged. The new keyboard rule checks the ring with `any(...)` over rules whose selector list contains the `:has()` selector (`test_ads_editor.py:1967-1974`). That check passes with the dead selector still in the list, so the rule does not push this toward a fix.

**File:** `app/static/css/app.css:2177-2178`

**Issue:** A `<label>` without `tabindex` never matches `:focus-visible`. The dead selector shares a list with `body:has(...)`. An engine that cannot parse `:has()` therefore drops the whole ring rule, and the ceiling rule at `:2183` with it.

**Fix:** Delete `.media-tile--add:focus-visible,`. Consider scoping both `:has()` rules to `[data-editor]` instead of `body`.

### IN-13: The visually-hidden declaration block is duplicated — open

**Disposition:** open. `app.css:2179-2182` is unchanged.

**File:** `app/static/css/app.css:2179-2182` (`.media-file-input`) duplicates `:801-804` (`.toggle__input`)

**Issue:** The same seven declarations live in two places, and hardening one copy lets the other drift silently.

**Fix:** Use a shared selector list, or a single `.visually-hidden` utility.

### IN-14: Nothing pins the claim that the page render never prints `autofocus`, and the template header does not list the new variable (new, `568b8f75`)

**File:** `app/templates/ads/includes/media_strip.html:69-70` (the «Ожидаемые переменные» list), `:110` («Страница и ответ убирания признака не передают и фокуса не крадут»). The test is `tests/test_pages/test_ads_image_upload.py:666-707`.

**Issue:** The new test covers only the upload response. The comment's other half, that the **page** never steals focus, has no guard. On a full page load the browser honours `autofocus` natively, so a stray `focus_on_ceiling` in the editor's render context would steal focus on every visit to a full ad, before the user's first Tab. Examples: a shared context builder, or a `{% set %}` in `form.html`. The header of the file (`:69-70`) still lists only `image_keys`, `refusals` and `max_images`, so a reader of the include contract does not learn that the flag exists or that only one caller may pass it.

**Fix:** Add a check to an existing editor-page test at the ceiling (`images=[4 keys]`, `max_images_per_ad=4`): `assert "autofocus" not in html`. Add `focus_on_ceiling` (optional, upload response only) to the expected-variables list.

### IN-15: The ceiling predicate is now spelled twice in one render, and the two copies must agree for the focus landing to be correct (new, `568b8f75`)

**File:** `app/templates/ads/includes/media_strip.html:89` (`strip_at_ceiling = image_keys | length >= max_images`) vs `app/templates/ads/includes/media_add_tile.html:54` (`at_ceiling = attached_count >= max_images`), fed by `media_strip.html:139` (`attached_count = image_keys | length`)

**Issue:** The `autofocus` exists because the add tile is hidden. Whether the tile is hidden is decided by the second spelling, and whether focus moves is decided by the first. If one changes and the other does not, the two decisions split:
- The tile stays visible while focus moves: focus is taken from a field that is still usable.
- The tile hides without a landing: the WR-09 loss comes back.

This is the "second copy diverges silently" pattern the file's own header argues against.

**Fix:** Compute the predicate once in `media_strip.html` and pass it into the include:
```jinja
{%- set strip_at_ceiling = image_keys | length >= max_images %}
…
{%- with attached_count = image_keys | length, at_ceiling = strip_at_ceiling %}
```
Then have `media_add_tile.html` use the passed `at_ceiling` when it is defined. Or add a test asserting that `autofocus` appears exactly when `id="media-add-tile"` carries `hidden`.

### IN-16: The two synthetic controls are marked `characterisation`, which the marker's own definition says they are not (new, `568b8f75`)

**File:** `tests/test_pages/test_schedule_invariants.py:204`, `:220`. The marker definition is `tests/conftest.py:493-496`.

**Issue:** The marker is registered as «правило ОПИСЫВАЕТ сегодняшнее поведение, признанное дефектным… красный при починке предмета означает "перепиши слепок"». After `568b8f75` the two controls describe nothing in the product. They check that the digest instrument detects a body edit and ignores a neighbour, using `_SYNTHETIC_CALCULATOR`. The commit's own comment (`:147-149`) says a calculator fix "не обязана их трогать". If one of them reddens, the instrument is broken, and the marker's advice to "rewrite the snapshot" is wrong; there is no snapshot in these tests. The marking followed the prior review's WR-11 fix step 2, which made sense while the controls pinned the live digest. Once they moved to a synthetic source, the marker no longer applies. It is also inconsistent within the module: the other `test_control_*` functions (`:332`, `:582`, `:610`, `:656`, `:803`) are unmarked.

**Fix:** Remove `@pytest.mark.characterisation` from `:204` and `:220`. Keep it only on `test_the_next_run_calculator_source_is_unchanged` (`:173`).

---

_Reviewed: 2026-10-06T10:10:22Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental over the 2026-10-06T09:50:17Z review; diff_base 6711465e)_

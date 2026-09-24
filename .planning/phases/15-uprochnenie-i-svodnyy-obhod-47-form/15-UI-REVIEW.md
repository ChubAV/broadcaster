# Phase 15 — UI Review

**Audited:** 2026-09-24
**Baseline:** abstract 6-pillar standards. **No UI-SPEC.md exists for this phase.** The contract used is `15-CONTEXT.md` D-18.3 (the dismiss control has "neither appearance nor place", its accessible name is duplicated, and the deferral covered "APPEARANCE and ROLE, not behaviour"), the plan summaries 15-05, 15-07, 15-08, 15-09 and 15-11, and the pre-phase tree `b82099de` as the point of comparison.
**Screenshots:** not captured. No dev server answered on 3000, 5173, 8080 or 8000 (`curl` returned `000` on all four). No Playwright, no MCP browser and no CDP session were used in this audit.
**Method:** code only. Every statement below is read from `git diff b82099de..HEAD -- app/`, the templates and macros that produce the DOM, and the `app/static/css/app.css` rules that apply to it. Nothing here was seen rendered. Contrast figures are **estimates**: `--danger` was converted from oklch to sRGB and the `color-mix(in oklab …)` backgrounds were approximated with an sRGB mix. Items marked **needs_human_review** are inferred and are not scored as confirmed defects.
**Registry audit:** skipped. There is no `components.json`, no shadcn and no third-party registry.

**Scope (per orchestrator).** This is a hardening phase. Its user-facing changes are small, and only those are audited:
- `app/templates/includes/htmx_error_banner.html:300-301`: two distinct `aria-label`s on the banner dismiss controls (15-07).
- `app/static/css/app.css:1362`: `.failure-stack > .alert { padding-right: 38px; }` overlap clearance (15-07). The rule `app.css:1329` `.banner-dismiss:focus-visible` already existed; plan 15-05 added a test asserting it and did not change it.
- Six sentinel lines: `app/templates/{ads,accounts,schedules}/{list,partial_cards}.html`, where `limit=30` became `limit={{ page_size }}` (15-09). The handlers `ads.py:250,300`, `accounts.py:175,213` and `schedules.py:877,938` supply `page_size`.
- `app/pages/schedules.py:1287-1353` (`schedules_update`): editor save on a malformed stored timezone (15-08). Only the user-visible outcome is audited.
- 15-11 changed no code in `app/`. The owner's `case-three-server-header` decision for the 19 dual-branch handlers keeps today's address-bar behaviour, and that behaviour is reserved to the manual walkthrough (item 7, accepted by Phase 11's record under D-15). It is not graded here.

**Not findings (locked decisions — correct behaviour, not defects):**
- Owner branch `A`, 2026-09-13: dismissal works without a JS handler, so the control is a CSS-driven `<input type="checkbox">`, and no new listener may be added without a new owner decision.
- The CR-01 fix intentionally has no success notice (D-03 Phase 10: "no banner on a successful save").
- No data migration (owner `chubav`, 2026-09-23: "code only").
- `hx-push-url` is absent from markup (D-12, 15-11).

**Reserved for the human walkthrough (`15-UAT.md` У-8), not judged here as verified:**
1. Whether the focus ring on the dismiss control is visible, unobstructed and contrasting when reached by Tab.
2. Whether Space on the checkbox actually dismisses the banner.
3. Whether any text is drawn under the × glyph now that the clearance exists.
4. Whether a screen reader makes the two accessible names distinguishable by ear.
5. The known **second-banner offset** after the first banner is dismissed by its control.

This review adds analysis to items 1, 4 and 5 below but closes none of them.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | The two accessible names are now specific to their failure (WCAG 4.1.2 duplicate fixed). Remaining issues: the distinguishing word comes last, after an identical 22-character prefix; the editor silently swaps a broken timezone with no explanatory copy; the six edited sentinel lines keep `Загрузка...`. |
| 2. Visuals | 3/4 | The clearance is derived from the control box (24 + 6 + 8) and the selector matches the real DOM (`alert()` emits `.alert` as a direct child). Unchanged: the control has no visible boundary (a 13px × on a transparent 24px box), and dismissing the first banner leaves the second floating 96px down over an empty gap. |
| 3. Color | 3/4 | No new colours; everything uses tokens. The focus ring that 15-05 asserted, `--focus-ring: rgba(196,132,252,.5)`, is estimated at about 2.6:1 against the error-banner background, below the 3:1 non-text minimum. The × glyph at rest is about 4.1:1, which passes. |
| 4. Typography | 3/4 | No new sizes or weights. The × glyph is drawn at `--fs-md` (13px) inside a 24px target, which is small for the only exit from a full-width error. The stack-step derivation in the CSS prose still quotes the pre-15-07 text width. |
| 5. Spacing | 3/4 | 38px is derived, not guessed, and a gate holds it to the control box. The derivation comment for `--failure-stack-step` (`app.css:1240-1246`) says the text field is 346px at a 400px viewport; after this phase it is 322px. The step is still sufficient, but the recorded arithmetic no longer describes the code. |
| 6. Experience Design | 2/4 | CR-01 is a real recovery path restored: saving a row with zone `Mars/Phobos` from the editor used to return a 500 and now saves. Against that: the timezone is silently rewritten to the profile zone; dismissing a banner by keyboard drops focus to `<body>`; the control is still announced as a checkbox (the "role" half of D-18.3 is untouched); and the `page_size` swap created a fail-silent path in which a missing context key produces `limit=`, a 422, and no banner. |

**Overall: 17/24**

**Finding classification:** no BLOCKER. No pillar scored 1, and no defect found here stops a user from completing a flow. Banners dismiss and return, infinite scroll loads, and the editor saves. Everything below is a WARNING or a minor note. Experience Design scores 2 because four defects are present on the surfaces this phase touched. None is new to this phase except the silent timezone swap and the latent 422.

---

## Top 3 Priority Fixes

1. **Keyboard dismissal loses focus, and the control is announced as a checkbox** (`htmx_error_banner.html:300-301`, `app.css:1330`). *User impact:* a keyboard user who presses Space hides the whole `.failure-stack` with `display: none`, so the focused element disappears and focus falls to `<body>`, the top of the page (WCAG 2.4.3). A screen-reader user hears something like "Скрыть сообщение об отказе сервера, флажок, не отмечен", an on/off state for what is actually an action, which is the "role" half of D-18.3 that Phase 15 did not touch. *Concrete fix:* this needs a **new owner decision**, because branch `A` forbids a new listener. One option is `<button type="button" class="banner-dismiss" aria-label="…">` plus one `click` handler inside the existing wiring block. The handler would set `hidden` on the stack and move focus to `#main` or to the element that triggered the request. Setting `hidden` instead of relying on `:checked` also fixes item 2 below, because the existing `.failure-stack[hidden] + .failure-stack` block would then apply. If JS stays forbidden, record the focus loss and the checkbox role as accepted consequences next to the offset consequence (`app.css:1311-1317`), so they are not left unrecorded.

2. **The second banner stays offset after the first is dismissed by its control** (`app.css:1263-1268` vs `:1330`). *User impact:* in a double failure, a user who closes the server banner sees the network banner at `top: 108px` with an empty 96px gap above it. It floats away from the edge for no visible reason, which the stack's own design note (г) calls a defect. This is known and deferred to the milestone. *Concrete fix:* add `.failure-stack:has(> .banner-dismiss:checked) + .failure-stack { --failure-banner-top: 12px; }` and teach `_stack_blocks` / `test_banner_dismiss.py::test_boundary_the_open_banner_top_consequence_is_guarded_not_fixed` that there are four offset-declaring blocks instead of three. Fix 1, if taken, closes this as a side effect.

3. **The `page_size` substitution added a fail-silent path to infinite scroll** (six sentinels, e.g. `ads/list.html:61`). *User impact:* the Jinja environment (`app/pages/common.py:36`) uses the default lenient `Undefined`. Any future render path that omits `page_size` prints `limit=`. FastAPI answers 422 to `limit=` for `limit: int = Query(PAGE_SIZE, ge=1, le=100)` (reproduced during this audit). The `htmx:responseError` listener **returns early on 422** (`htmx_error_banner.html:306`), so no banner appears. The sentinel then reads `Загрузка...` forever. The old literal could not fail this way. The gate `test_the_page_size_in_the_context_is_the_module_constant` covers today's six render sites only. *Concrete fix:* remove `&limit={{ page_size }}` from all six sentinels. The server default is already `PAGE_SIZE`, and the gate's goal (one carrier of the number) is met even better when the markup carries no size at all. The other option is to render these templates under `StrictUndefined`, so that a missing key fails loudly in tests.

**Further WARNINGs and minor notes (ranked):**

4. **Timezone silently rewritten on editor save** (`schedules.py:1307-1313`). When the stored zone is invalid, the hidden field `sched_card.html:216` posts it back, it fails validation, and the row is saved under the profile zone or UTC. The only signal is that the caption `sched_card.html:299` «Время по Mars/Phobos» changes to «Время по Europe/Moscow». The times keep their digits but now mean a different zone. *Fix:* the no-notice rule (D-03 Phase 10) covers success banners, so use a card-level hint instead: when `schedule.timezone ∉ VALID_TIMEZONES`, show a line on the card before the save, for example «Часовой пояс «Mars/Phobos» не распознан — при сохранении расписание перейдёт на {profile_tz}». The user then learns about the change before it happens.
5. **Focus-ring contrast.** `--focus-ring` is a 50%-alpha violet, estimated at 2.6:1 on the error banner and 2.7:1 on `--surface`. WCAG 1.4.11 asks for 3:1. The token is project-wide and pre-existing, but 15-05 calls this rule the "machine half" of UAT item 2 and asserts only that the rule exists, not whether the ring can be seen. *Fix:* use an opaque ring (`rgb(196 132 252)`, about 7:1 on these backgrounds), or raise the alpha to at least .7, and keep the rest of the rule unchanged.
6. **Stale arithmetic in the stack-step note** (`app.css:1240-1246`). The note says «поле набора 346px». With 38px right padding it is now 376 − 2 − 14 − 38 = 322px. The server text still wraps to two lines, so the 96px step with its three-line reserve holds. Update the recorded figure the project's usual way: add a dated correction beside the old figure instead of deleting it.
7. **Accessible-name order** (`htmx_error_banner.html:300-301`). Both names share the prefix «Скрыть сообщение об о…» (22 characters) and differ only in the last word. In a form-controls list or with fast speech, the distinguishing part comes last. *Fix (nit):* «Скрыть: отказ сервера» / «Скрыть: обрыв связи», or «Закрыть сообщение об обрыве связи» with the subject earlier. Update `BANNER_DISMISS_ACCESSIBLE_NAMES` at the same time.
8. **Sentinel copy and semantics** (the six edited lines). `Загрузка...` uses three periods instead of `…`, and the loading sentinel borrows `class="empty__hint"` (the empty-state style) without `role="status"`. Both are carried from before this phase but sit on lines this phase edited. *Fix (minor):* `Загрузка…` plus `role="status"` in all six at once. The pair-identity gates will require both halves of each pair to change together.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **Fixed (credit).** `htmx_error_banner.html:300` now reads `aria-label="Скрыть сообщение об отказе сервера"` and `:301` reads `aria-label="Скрыть сообщение об обрыве связи"`. The double-failure duplicate `checkbox "Скрыть сообщение"` ×2 (D-18.3) is gone. Each name refers to the subject of its own banner. The alternative of numbering the names («1»/«2») was rejected correctly, since numbers carry no meaning when heard.
- **WARNING — silent timezone swap has no copy** (fix 4). The recovery path that three repaired handlers tell the user to take («откройте расписание в редакторе и сохраните заново») now succeeds, but nothing tells the user that the zone was replaced.
- **Minor — label/visible-text vocabulary.** The server banner's visible text begins «Действие не выполнено…», while its control says «…об отказе сервера». This is not a WCAG 2.5.3 failure, because the control has no visible text label and the × is a glyph. A sighted screen-reader user will still hear one term and see another.
- **Minor — name order** (fix 7) and **three-dot ellipsis** (fix 8).

### Pillar 2: Visuals (3/4)

- **Pass — the clearance reaches the real DOM.** `components/alert.html` emits `<div class="alert alert--error" role="alert">` as a direct child of `.failure-stack`, so `.failure-stack > .alert` (`app.css:1362`) matches. It has specificity (0,2,0) against `.alert`'s (0,1,0) `padding: 11px 14px` at `app.css:845`, and no media query redeclares `.alert` padding. The containing block for the absolute control is the `position: fixed` banner (`app.css:1188-1198`), so the 6px/24px geometry is measured from the banner edge as intended.
- **WARNING — second-banner offset after dismissal** (fix 2). The consequence is declared openly and guarded by a test that stops it from being fixed or removed without notice. That is honest record-keeping, but the defect is still visible. **needs_human_review:** confirm that the gap is exactly 96px and not larger at narrow widths, where the first banner may be taller.
- **Minor — the control has no visible boundary.** It is `border: 0; background: transparent` (`app.css:1322-1323`), with a single `\00d7` at 13px. That is a common close-button pattern and readable at 4.1:1, but D-18.3 named the missing "appearance", and Phase 15 addressed only "place" and "name". Consider a hover/focus background (`background: color-mix(in oklab, var(--danger) 14%, transparent)`) so the 24px target shows its size.
- **needs_human_review — drawn collision.** With 38px of padding and a text box ending 38px from the edge, the box maths leave a 9px visible gap (8px + 1px border). Only rendering can confirm it (У-8, item 3).

### Pillar 3: Color (3/4)

- No colour literal was added this phase. The 32 CSS lines added are one declaration plus a comment. All banner colours come from tokens (`--danger`, `--text-tertiary`, `--text`, `--focus-ring`, `--surface`).
- Estimated contrast on the error banner (≈ `rgb(37,22,27)`):
  - banner text `--danger` ≈ `rgb(247,93,89)`: **5.5:1** (pass)
  - × at rest `--text-tertiary` `#7a7a88`: **4.1:1** (pass for non-text)
  - × on hover `--text`: **15:1**
  - focus ring `rgba(196,132,252,.5)` blended: **≈2.6:1**, **below 3:1** (WARNING, fix 5)
- Accent discipline is unaffected. The banner uses only the danger family, and the ring is the project-wide focus token. **needs_human_review:** whether the ring *looks* sufficient on a real display (У-8, item 1). The estimate uses an sRGB approximation of an oklab mix.

### Pillar 4: Typography (3/4)

- No new font sizes or weights anywhere in the diff. Banner text stays at `--fs-md` 13px / 1.5 (`app.css:846`).
- **Minor — glyph size vs. target.** `.banner-dismiss::before { font-size: var(--fs-md) }` draws a 13px × inside a 24px box that just meets WCAG 2.5.8 (24×24 minimum). The target meets the size rule, but the glyph occupies only about half of the target visually. Raising the glyph to `--fs-lg`, or adding the hover/focus background from Pillar 2, would make the clickable area visible.
- **Minor — stale derivation prose** (fix 6). It does not affect typography today, but the recorded line-count argument depends on a width that no longer matches the code.

### Pillar 5: Spacing (3/4)

- **Pass — derived, not guessed.** 38 = 24 (width) + 6 (right) + 8 (gap). `test_the_clearance_is_derived_from_the_dismiss_box` reads both addends from the `.banner-dismiss` block of the same stylesheet, and a 37px value fails it. This is the right way to hold a spacing value.
- **Minor — asymmetry.** Horizontal padding is now 14px left and 38px right. This is the expected cost of a corner close button, and the text column's ragged right edge hides it. It is recorded here only so a later reviewer does not "fix" it into symmetry.
- **WARNING (low) — stale figures** (fix 6). At a 400px viewport the content width is 322px, not 346px. At 375px it is 297px, and the server text still takes two lines (about 370px of glyphs at 13px), so `--failure-stack-step: 96px` is still sufficient. Nothing recomputes this. `test_the_stack_step_clears_the_tallest_first_banner` reads vertical `.alert` values and the line count is a constant, so a longer server message combined with the narrower field could reach a third line without any test failing.

### Pillar 6: Experience Design (2/4)

- **Credit — CR-01 recovery path restored.** Before: editing a row with `timezone='Mars/Phobos'` raised `ZoneInfoNotFoundError` and returned 500. After: a 302 or fragment response, a valid zone written, and a card that re-renders expanded (`schedules.py:1356-1408`). On the second line of defence, an unrunnable complete schedule is saved **inactive** instead of hitting the `ck_schedules_active_requires_next_run` 500 (`:1343-1353`). The toggle then refuses with its existing explanation. That branch is unreachable through today's card path, so no UX copy is owed for it now.
- **WARNING — focus loss on keyboard dismissal** (fix 1). `display: none` on the ancestor of the focused checkbox moves focus to `<body>`. **needs_human_review:** where focus actually lands in Chrome and Firefox (Chrome typically starts the next Tab from the removed node's position; Firefox from the top).
- **WARNING — role still `checkbox`** (fix 1). D-18.3 scoped the deferral to "appearance and role". 15-07's must-haves cover the name and the clearance only (`15-07-PLAN.md` has no role item). The role gap is therefore neither fixed nor recorded as accepted in this phase. It should be one or the other.
- **WARNING — silent timezone swap** (fix 4).
- **WARNING — latent 422 swallow** (fix 3). This is latent, not present: all six render sites pass `page_size` today, and a test holds them. The failure mode is fully silent, though. The 422 early-return in the banner script and an empty `limit=` combine into a sentinel that never resolves, which is the "green by vacuum" class the phase exists to prevent, but in the product rather than the suite.
- **State coverage on the audited surfaces:**
  - error: banners, both kinds, return on the next failure because `server_close.checked = false` runs on each `responseError`/`sendError` (`:308`, `:313`).
  - loading: sentinel text only, with no `aria-busy` or live region.
  - empty: `{% elif filters_active %}` / `{% else %}` branches, unchanged.
  - destructive confirmation: out of scope this phase.
- **needs_human_review — Space toggles the checkbox** (У-8, item 2). Space on a focused `<input type="checkbox">` toggles it natively, and `:has(> .banner-dismiss:checked)` then hides the stack. Enter does **not** toggle a checkbox, so users who expect Enter to activate a close control will get no response. This follows from branch `A` and should be named in the walkthrough.

---

## Files Audited

- `app/templates/includes/htmx_error_banner.html` (lines 297-323: markup and wiring script)
- `app/templates/components/alert.html` (macro output shape)
- `app/static/css/app.css` (`:43-80` tokens, `:844-852` `.alert`, `:1188-1198` banner positioning, `:1225-1268` stack, `:1270-1330` dismiss control, `:1331-1362` clearance)
- `app/templates/ads/list.html:61`, `app/templates/ads/partial_cards.html:7`
- `app/templates/accounts/list.html:203`, `app/templates/accounts/partial_cards.html:146`
- `app/templates/schedules/list.html:66`, `app/templates/schedules/partial_cards.html:12`
- `app/pages/ads.py` (`:207-307`), `app/pages/accounts.py` (`:137-216`), `app/pages/schedules.py` (`:803-940`, `:1287-1408`), `app/pages/common.py:36`
- `app/templates/ads/includes/sched_card.html:216`, `:299` (hidden timezone field and caption)
- `git diff b82099de..HEAD -- app/` (12 files, +141 / −23)
- Context: `15-CONTEXT.md`, `15-05-SUMMARY.md`, `15-07-SUMMARY.md`, `15-07-PLAN.md` (grep only), `15-08-SUMMARY.md`, `15-09-SUMMARY.md`, `15-11-SUMMARY.md`, `15-UAT.md` (У-8 located)

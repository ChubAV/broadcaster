---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
audited: 2026-09-27
kind: re-audit after gap-closure batch 15-15…15-33 (executed 2026-09-25…27)
supersedes: "audit 2026-09-24, 17/24"
baseline: abstract 6-pillar standards (no UI-SPEC.md for this phase); 15-CONTEXT.md locked decisions as contract
screenshots: not_captured
score: 17/24
prior_findings: 13            # items 1–8 plus pillar-level P1-a, P2-a, P4-a, P5-a, P6-a
prior_closed: 8               # 3, 4, 5, 6, 7, 8 fixed; 1 and P6-a closed as owner-accepted consequences
prior_still_open: 5           # 2, P1-a, P2-a, P4-a, P5-a
new_findings: 8               # 9–16
blockers: 0
---

# Phase 15 — UI Review (re-audit)

**Audited:** 2026-09-27. This replaces the 2026-09-24 edition, which scored 17/24.
**Baseline:** abstract 6-pillar standards. **No UI-SPEC.md exists for this phase.** The contract is `15-CONTEXT.md` (D-18.3 in particular), the `must_haves.truths` of plans 15-16, 15-19, 15-21 and 15-23, and owner decisions Г-2 and Г-3 of 2026-09-25 as recorded in `STATE.md:675`.
**Screenshots:** not captured. No dev server answered: `curl` returned `000` on 3000, 5173, 8080 and 8000. No app was started, and no Playwright, MCP browser or CDP session was used.
**Method:** code only. The sources are `git diff b82099de..HEAD -- app/` (17 files, +343/−42), the gap-batch diff `git diff a674e8e5..HEAD -- app/templates app/static`, and the handlers and rules those templates depend on. Contrast figures are **estimates**: oklch tokens were converted by hand to sRGB luminance. Anything that needs a rendered page is marked **needs_human_review** and belongs to `15-UAT.md` У-8 (`15-UAT.md:429`). None of it is marked verified here.
**Registry audit:** skipped. There is no `components.json`, no shadcn and no third-party registry.

**Finding counts.** There are 13 prior findings: items 1–8 and five pillar-level findings, given IDs P1-a…P6-a here. Of those, **8 are closed**: six fixed, and two closed as owner-accepted consequences whose user impact persists. **5 are still open** and carried forward. **8 new findings** are numbered 9–16. There are no BLOCKERs.

**Scope of this re-audit.** Only the user-facing plans of the batch are audited:
- **15-16:** editor save and create now refuse with `schedule_values_out_of_domain` instead of silently deactivating the schedule (`app/pages/schedules.py:1380-1414`, `:1135-1142`).
- **15-19:** banner dismiss. Two accepted consequences are recorded (`app.css:1330-1348`), the names were reordered (`htmx_error_banner.html:308-309`), `--focus-ring` is opaque (`app.css:61`), and the stack-step arithmetic has a dated correction (`app.css:1251-1257`).
- **15-21:** six sentinels without `limit`, now showing `Загрузка…` with `role="status"`.
- **15-23:** an unrecognised-zone hint on the schedule card before save (`sched_card.html:313-315`).
- The other 15-2x/15-3x plans are test- or records-only and change nothing visible.

**Not findings (locked decisions):**
- Branch `A`: CSS-checkbox dismissal, with no new listener.
- D-03 of Phase 10: no success notice on save.
- No data migration.
- `hx-push-url` absent (D-12).
- Г-3: the focus loss and the checkbox role are recorded rather than fixed.

---

## Prior Findings Disposition

"Closed — accepted consequence" means the owner decided to keep the mechanism. **The user impact persists by decision**, and nothing in the tree mitigates it.

| ID | Prior finding (2026-09-24) | State | Evidence |
|----|----------------------------|-------|----------|
| 1 | Keyboard dismissal drops focus to `<body>`; the control is announced as a checkbox (role half of D-18.3) | **closed — accepted consequence**, recorded at `app/static/css/app.css:1330-1341` (focus) and `:1342-1348` (role) | Commit `3d8557eb`. Owner basis Г-3 (`chubav`, 2026-09-25) is quoted verbatim. Guarded by `test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed`. The mechanism is unchanged: `htmx_error_banner.html:308-309` is still `<input type="checkbox">`, and `app.css:1361` is still `display: none`. **Impact persists:** a keyboard user who presses Space still lands at the top of the page, and a screen reader still hears "флажок, не отмечен". |
| 2 | The second banner stays offset (96px gap) after the first is dismissed by its control | **still open**, deferred to the milestone (`STATE.md:675`: "UI priority 2 — известное отложенное следствие") | Verified against the tree, not assumed. `app.css:1274-1279` still has only `.failure-stack + .failure-stack` and `.failure-stack[hidden] + .failure-stack`, and there is no `:has(> .banner-dismiss:checked) + .failure-stack` block. The note `app.css:1322-1328` is unchanged. 15-19 did not touch it. |
| 3 | The `page_size` substitution created a fail-silent path: missing key → `limit=` → 422 → no banner → `Загрузка...` forever | **closed** for the six sentinels it named | Commit `5a95c970`. The six sentinels carry no `limit` (e.g. `ads/list.html:61`, `accounts/list.html:203`, `schedules/partial_cards.html:12`). The six contexts no longer set `page_size`. Rule 6 is `test_the_six_sentinels_carry_no_page_size_and_the_server_default_is_the_module_constant`. **The same path persists at five other sentinels**; see new finding 9. |
| 4 | Timezone silently rewritten on editor save; the only signal is the changed caption | **closed** | Commits `5187b807` and `a74f2651`. `sched_card.html:313-315` shows «Часовой пояс «…» не распознан — при сохранении расписание перейдёт на …» before save, on both render paths. The zone comes from the same helper as the save, `profile_timezone_or_utc` (`schedules.py:1344`). Whether a person understands the line is reserved to UAT (15-23 D4). See new findings 12 and 13 for residual copy and spacing issues. |
| 5 | Focus-ring contrast ≈2.6:1 (50% alpha) | **closed** | Commit `dc851613`. `app.css:61` is now `--focus-ring: rgb(196, 132, 252)`, with the old value kept as a record at `:57-60`. Re-estimated at **≈6.7:1** on the error-banner background (≈`rgb(37,22,27)`). Whether the ring is visible on a real display remains **needs_human_review** (У-8). |
| 6 | Stale arithmetic in the stack-step note (346px vs 322px) | **closed** | Commit `ace989f9`. The dated correction «ПОПРАВКА 2026-09-25» is at `app.css:1251-1257` (376 − 2 − 14 − 38 = 322px), and the old figure is kept. The adjacent "nothing recomputes the line count" concern is tracked separately as P5-a. |
| 7 | Both accessible names share a 21–22 character prefix; the distinguishing word comes last | **closed** | Commit `ace989f9`. `htmx_error_banner.html:308` reads «Отказ сервера: скрыть сообщение» and `:309` reads «Обрыв связи: скрыть сообщение». Guarded by `test_each_accessible_name_leads_with_its_own_failure`. |
| 8 | Sentinel copy `Загрузка...` (three periods) and no `role="status"` on the six edited lines | **closed** for the six lines | Commit `5a95c970`. All six carry `role="status"` and `Загрузка…`. The five sentinels outside item 8's scope still have the old form; see new finding 10. |
| P1-a | The control's name vocabulary differs from the visible banner text («…отказ сервера» vs «Действие не выполнено…») | **still open** (minor) | Now more noticeable, because the subject word leads the name: «Отказ сервера» names a banner whose visible text is «Действие не выполнено…», and «Обрыв связи» names one whose text is «Запрос не дошёл до сервера…» (`htmx_error_banner.html:308-309`). |
| P2-a | The dismiss control has no visible boundary (a 13px × on a transparent 24px box; the "appearance" half of D-18.3) | **still open** | `app.css:1349-1357` is unchanged (`border: 0; background: transparent`). The role note at `app.css:1345` says so itself: «имя и место исполнены планом 15-07, вид — нет». There is no owner acceptance for appearance; Г-3 covers focus and role only. |
| P4-a | The × glyph is drawn at `--fs-md` (13px) inside a 24px target | **still open** (minor) | `app.css:1358` is unchanged. |
| P5-a | Nothing recomputes the banner line count; a longer server message could reach another line with no test failing | **still open** (low) | `tests/test_pages/test_shell.py:4302` still has `FAILURE_BANNER_STACK_LINES = 3` as a constant. The 322px correction is prose only. |
| P6-a | Enter does not toggle a checkbox; only Space dismisses | **closed — accepted consequence**, recorded at `app.css:1334-1335` («Клавиша Enter флажок не переключает вовсе — снимает только пробел») | Same Г-3 basis and guard as item 1. **Impact persists:** a user who presses Enter gets no response. |
| P6-b | The loading sentinel had text only, with no live region | **closed** for the six audited sentinels (`role="status"`, `5a95c970`) | The other five sentinels are covered by new finding 10. Whether a screen reader actually announces anything is new finding 15. |

**Reserved for У-8 and unchanged by this batch (not findings):** whether the ring is visible; whether Space dismisses; whether text is drawn under the ×; whether screen readers distinguish the names by ear; the size of the 96px gap at narrow widths; where focus lands after dismissal in Chrome and Firefox.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | The names now lead with their subject, and the zone hint gives a warning before the action. Remaining: the second-line refusal copy (15-16) tells a user who just saved in the editor to "open the editor and save" and names "включение" (finding 11). The name and visible-text vocabulary still differ (P1-a). Loading copy is now split between `…` and `...` (finding 10). |
| 2. Visuals | 3/4 | The zone hint sits in the right place: expanded body, under the caption, before the save button. Unchanged: the second banner floats 96px down after the first is dismissed (item 2), and the × control still has no visible boundary (P2-a). |
| 3. Color | 3/4 | The ring is opaque (≈6.7:1 estimate, up from ≈2.6:1). The hint uses the `--warn` token (≈10.8:1 on `--surface-pill`), and no colour literals were added. Held at 3 because every contrast figure is an unobserved estimate, and the token change restyles all 16 focus indicators app-wide without having been seen on screen (finding 14). |
| 4. Typography | 3/4 | No new sizes or weights in the batch. The hint reuses `.sched-card__hint` at `--fs-lg`. The × glyph is still 13px in a 24px target (P4-a). |
| 5. Spacing | 3/4 | The stale 346px figure has a dated correction. New: the hint is a `<p>` with the browser's default 1em margin inside a 12px-gap flex column (finding 12). The line count is still a constant (P5-a). |
| 6. Experience Design | 2/4 | Real progress: the silent zone swap is replaced by a warning before the action, the silent deactivation became a named refusal, and the fail-silent 422 is gone on six sentinels. The score stays at 2 because the three live defects on the dismiss control are unchanged for users: focus loss, checkbox role and Enter (accepted, not mitigated), plus the second-banner offset (open). The same latent 422 path survives on five sentinels (finding 9), and the new refusal path discards the user's edits and collapses the card (finding 11). |

**Overall: 17/24**

**Why the total did not rise.** Five prior items were fixed. But two of the Experience Design defects were closed by *recording* them, which does not change what a keyboard or screen-reader user meets. The Color point regained on the ring is held back only by the lack of any on-screen observation. Scores measure the product, not the paperwork.

**Classification:** no BLOCKER. No pillar scored 1, and no flow is broken. Banners dismiss and return, infinite scroll resolves on all eleven sentinels today, and the editor saves. Everything below is a WARNING or a minor note.

---

## Top 3 Priority Fixes

1. **Second banner stays offset after the first is dismissed** (item 2, still open; `app.css:1274-1279`).
   - *User impact:* in a double failure, closing the server banner leaves the network banner at `top: 108px` over an empty 96px band. This is the only visible layout defect left on the surfaces this phase touched.
   - *Concrete fix:* add `.failure-stack:has(> .banner-dismiss:checked) + .failure-stack { --failure-banner-top: 12px; }`. Teach `_stack_blocks` (`tests/test_pages/test_shell.py`) and `test_boundary_the_open_banner_top_consequence_is_guarded_not_fixed` that four offset-declaring blocks are legitimate. Record the change beside `app.css:1322-1328` rather than deleting the note. This needs no JS and stays inside branch `A`, so no new owner decision on Г-3 is required. The milestone deferral itself is the owner's to lift.
2. **Five sentinels keep the fail-silent `limit={{ page_size }}` path** (new finding 9).
   - *User impact:* the same failure 15-21 removed from six screens is still possible on History, Admin → user history and account groups. If a future render path omits `page_size`, the result is `limit=`, a 422 that the banner script ignores (`htmx_error_banner.html:314`), and «Загрузка...» shown forever with no error.
   - *Concrete fix:* apply the 15-21 pattern to `history/list.html:119`, `history/partial_cards.html:6`, `admin/user_history.html:63`, `admin/history_partial_cards.html:7` and `account_groups/includes/sentinel.html:73`. That means dropping `&limit={{ page_size }}` and the macro's `page_size` parameter, removing the `page_size` keys from `history.py:633,1175`, `admin.py:1488,1572` and `account_groups.py:275,376`, and using the same pass to add `role="status"` and `Загрузка…` (closes finding 10).
3. **The second-line refusal on editor save and create points the user back to the action that just failed** (new finding 11; `schedules.py:1408-1414`, `:1135-1142`, text at `notices.py:273-277`).
   - *User impact:* the notice says «Откройте расписание в редакторе объявления, выберите дни и время заново и сохраните — после этого включение сработает». The user is already in the editor and has just pressed save (or create), and never pressed «включение». Because of the rollback, their edits are discarded, and the redirect has no `?sched=`, so the card comes back collapsed. Following the text reproduces the refusal.
   - *Why it ranks third:* it is latent. The branch is reachable only if `_clean_ints`/`_clean_times` let a bad value through (`schedules.py:1375-1379`).
   - *Concrete fix:* the owner needs to approve a registry addition, because a new code touches prohibitions `10-01#3`/`10-24#2`/`10-31#1`. Then add a save- and create-specific notice, for example «Расписание не сохранено: выбранные дни и время система исполнить не может. Проверьте значения и сохраните снова.». Redirect to `/ads/{ad_id}/edit?sched={id}#sched-{id}` on the update path so the card stays open. If a new code is refused, at minimum make the existing text action-neutral by dropping «после этого включение сработает».

**Needs a new owner decision (not a fix target under Г-3):** items 1 and P6-a. They are recorded as accepted, but the user impact they describe is the largest remaining a11y cost in the phase. Any reopening would use the `<button>` + single-handler route set out in the 2026-09-24 edition.

**Further WARNINGs and minor notes (ranked):**

4. **P2-a (open): the dismiss control has no visible boundary.** Add a hover and focus background, for example `.banner-dismiss:hover, .banner-dismiss:focus-visible { background: color-mix(in oklab, var(--danger) 14%, transparent); }`, so the 24px target shows its size. This is pure CSS inside branch `A`.
5. **Finding 10: inconsistent loading copy and semantics.** Six sentinels have `Загрузка…` with `role="status"`. Five have `Загрузка...` without a role. Three connect-step labels (`accounts/includes/tg_connect_step.html:83,150`, `connect_wa.html:44`, `max_connect_step.html:89`) keep three periods.
6. **Finding 13: the hint names the zone but not the consequence.**
7. **Finding 12: default `<p>` margin under the hint.**
8. **P1-a (open): name and visible-text vocabulary.**
9. **Finding 14: the opaque ring is an unobserved app-wide change.**
10. **Finding 15: `role="status"` on a node that is inserted with its content and then replaced.**
11. **P4-a and P5-a (open, minor).**
12. **Finding 16: pre-existing, not charged to this phase.** The caption «Время по …» that the hint qualifies is `--text-muted` #6a6a78 at 11px, estimated at ≈3.6:1 on `--surface-pill`, which is below 4.5:1.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **Credit:**
  - `htmx_error_banner.html:308-309`: each name now opens with its subject, so a form-controls list tells them apart at the first word.
  - `sched_card.html:314`: the hint is concrete. It quotes the stored zone, names the target zone, and appears before the action. This is exactly the placement the prior review asked for, and it adds no success banner (D-03 respected).
  - The six sentinels use a single-character ellipsis.
- **WARNING — finding 11 (refusal copy loops; details in Top 3 #3).** 15-16 reuses a notice written for the toggle on two new entry points. The 15-16 summary flags this itself as D5 (`human_judgment: true`). The problem is visible from the text alone: «Откройте … в редакторе … и сохраните» is addressed to someone who is already in the editor and has already saved.
- **Minor — finding 13 (hint consequence unstated).** «…при сохранении расписание перейдёт на Europe/Moscow» names the switch but not its effect. The digits «10:00» will stay the same but will mean 10:00 Moscow time, so actual send moments shift. There is also no alternative: the card has no zone picker, so the choices are to accept or not save. *Fix:* «Часовой пояс «Mars/Phobos» не распознан — при сохранении время будет считаться по Europe/Moscow (цифры не изменятся)». Mention the profile setting if that is the intended lever. Prohibition `10-01#6` protects the caption, not this new line.
- **Minor — finding 10 (inconsistent loading copy):** the spelling now depends on the screen, e.g. `history/list.html:119` and `account_groups/includes/sentinel.html:74` versus `ads/list.html:61`.
- **Minor — P1-a (open):** see the disposition table.

### Pillar 2: Visuals (3/4)

- **Pass — hint placement.** The hint sits in the expanded body only, directly under «Время по {{ s.timezone }}» and above «СОХРАНИТЬ РАСПИСАНИЕ» (`sched_card.html:299-319`), so it is visible exactly when saving is possible. Reusing `.sched-card__hint` ties it visually to the existing «Заполните группы, дни и время» warning (`:197`).
- **WARNING — item 2 (open).** See Top 3 #1. **needs_human_review:** the gap size at narrow widths (У-8).
- **WARNING — P2-a (open).** The control has no visible extent. D-18.3 named "appearance", and the tree records it as not done (`app.css:1345`).
- **Minor — hierarchy of the hint.** At `--fs-lg` (14px) in `--warn` colour, the hint is the loudest text in the «ДНИ И ВРЕМЯ» block, louder than the 11px mono caption it qualifies. For a pre-save warning that is appropriate. It is noted only so the pairing (small caption, large warning) is recognised as deliberate.

### Pillar 3: Color (3/4)

- **Item 5 closed.** `--focus-ring: rgb(196, 132, 252)`. Estimated luminance is ≈0.353 against ≈0.010 for the banner background, giving **≈6.7:1**. On `--surface` (#0e0e14) it is ≈7.5:1. This is an sRGB hand calculation, not a rendered measurement.
- **Hint colour:** `--warn` `oklch(0.82 0.16 85)` → Y ≈ 0.545 → **≈10.8:1** on `--surface-pill` #0f0f16 (estimate). This passes.
- **No colour literals added.** The only colour value in the diff is the token's own definition. The accent discipline is unchanged.
- **Minor — finding 14 (unobserved app-wide change).** The token feeds 16 rules: `app.css:587, 715, 748, 818, 1360, 1555, 1782, 1891, 2164, 2174, 2431, 2514, 2531, 2570, 2582, 2601`. The ring is now a fully saturated violet close to `--accent-cta` `oklch(0.79 0.14 305)`, the primary-button fill. With `outline-offset: 2px` on `.btn` a page-background gap separates them, but the inset rings (`.media-tile__remove`, `.time-pill__remove`, offset −2px) and `.field__input:focus` (a 1px border change only, `outline: none`) have not been seen since the change. Walkthroughs of phases 7–14 saw the old half-transparent ring. **needs_human_review** (У-8; the 15-19 summary names this). The score stays at 3 until this is observed. There is no confirmed colour defect.
- **Minor — finding 16 (pre-existing).** `.sched-card__tz` `--text-muted` #6a6a78 at 11px is ≈3.6:1 on `--surface-pill`, below the 4.5:1 WCAG 1.4.3 threshold for normal text. The phase did not change it, but the new hint depends on it.

### Pillar 4: Typography (3/4)

- **Distribution:** the batch adds no font sizes and no weights. The only `app.css` value change is the `:root` token (confirmed by the 15-19 summary's rule diff, 564 vs 564 rules). The hint uses the existing `--fs-lg` (14px) through the existing class. The token ladder `--fs-2xs`…`--fs-h3` (`app.css:81-90`) is unchanged.
- **Minor — P4-a (open).** A 13px × in a 24px target (`app.css:1358`). *Fix:* use `--fs-lg`, or rely on the P2-a background.
- **Minor — hint vs sibling hint.** The same class is used for a top-of-body notice (`:197`) and a line inside a sub-block (`:314`). Both render at 14px. That is consistent, and recorded only for reference.

### Pillar 5: Spacing (3/4)

- **Item 6 closed.** The correction is dated and derived (`app.css:1251-1257`).
- **Minor — finding 12 (default paragraph margin).** The project has no `p { margin: 0 }` reset: `app.css:433` resets only `box-sizing`, and there is no Tailwind preflight. `.sched-card__hint` sets no margin. Inside `.sched-card__block` (`display: flex; gap: 12px`, `app.css:2477`), flex items' margins do not collapse. So the hint is expected to sit about **12 + 14 = 26px** below the caption it qualifies, with another 14px below it before the 16px gap to the save row. Everything else in the block keeps a 12px rhythm, the rhythm issue #45 fixed deliberately (`app.css:2440-2452`). *Fix:* `.sched-card__hint { margin: 0; }`. That also normalises the `:197` instance, which shares the class; check that the 16px body gap still reads right there. **needs_human_review** for the rendered distance.
- **Low — P5-a (open).** See the disposition table.

### Pillar 6: Experience Design (2/4)

- **Credit (state coverage improved):**
  - *Pre-action warning:* the unrecognised zone is announced on the card before save, on both render paths (15-23 D2). Hint and save share one helper, so they cannot disagree (`test_hint_fallback_zone_comes_from_the_same_helper_as_the_save`).
  - *Named refusal instead of silent state change:* 15-16 makes save, create, toggle and the JSON API refuse one way, and nothing is written.
  - *Loading:* six sentinels cannot hang on an empty `limit` any more.
- **WARNING — items 1 and P6-a (closed as accepted; impact persists).** Space hides the whole stack and focus falls to `<body>` (WCAG 2.4.3). Enter does nothing. The control is announced as a checkbox. The record is honest and guarded; the experience is unchanged.
- **WARNING — item 2 (open).** See Top 3 #1.
- **WARNING — finding 9 (latent fail-silent path at five sentinels).**
  - The environment is `Jinja2Templates(directory=…)` with the default lenient `Undefined` (`app/pages/common.py:37`). The five sentinels still interpolate `limit={{ page_size }}`. The handlers declare `limit: int = Query(PAGE_SIZE, ge=1, le=100)` (`history.py:559`, `admin.py:1505`, `account_groups.py:298`), so an empty `limit=` is a 422. The banner listener returns early on 422 (`htmx_error_banner.html:314`).
  - This is **latent**: all current render sites pass `page_size` (`history.py:633,1175`, `admin.py:1488,1572`, `account_groups.py:275,376`). 15-21 names it as residue addressed to the next milestone. The prior item 3 analysis applies to it in full.
  - The same lenient-`Undefined` root sits under the new `fallback_timezone` macro parameter. If a caller omitted it, the hint would print «…перейдёт на » with nothing after it. `test_every_card_call_passes_the_hint_fallback_zone` holds that by source scan, so it is not scored.
- **WARNING (latent) — finding 11.** The refusal discards input and collapses the card. See Top 3 #3.
- **Minor — finding 15 (live region that may never speak).** `role="status"` sits on a node that is inserted already containing «Загрузка…» and is removed by `hx-swap="outerHTML"` when revealed. Most screen readers announce *changes* inside an existing live region, not a region inserted with content, so the attribute may add semantics without any announcement. **needs_human_review** (15-21 D4 names the browser step). If silence is confirmed, a persistent `aria-live="polite"` container outside the swapped node, or `aria-busy` on the grid, would be the working form.
- **State coverage on audited surfaces:**
  - *Error:* both banners return on the next failure (`server_close.checked = false` `:316`, `network_close.checked = false` `:321`).
  - *Loading:* 6/11 sentinels have `role="status"`.
  - *Empty:* branches unchanged.
  - *Pre-action warning:* new (hint).
  - *Destructive confirmation:* out of scope.

---

## Files Audited

- `app/templates/includes/htmx_error_banner.html` (`:270-330`: records, markup `:308-309`, wiring script `:310-330`)
- `app/static/css/app.css`:
  - `:24-90` tokens, including `--focus-ring`, `--warn`, `--text-muted` and the `--fs-*` ladder
  - `:433-434` resets
  - `:587, 715, 719, 748, 761-764, 818` and the other focus-ring consumers listed under Pillar 3
  - `:1188-1200` banner positioning; `:1244-1279` stack step, correction and blocks; `:1280-1361` dismiss records and control; `:1389-1396` clearance
  - `:2377-2381, 2435-2480` schedule card
- `app/templates/ads/includes/sched_card.html` (`:88-91, :133-137, :185-200, :270-345`)
- `app/templates/ads/form.html:330-335`, `app/templates/ads/partials/sched_card_response.html:38-43`, `app/templates/ads/partials/sched_create_response.html:52-57`
- Sentinels: `app/templates/{ads,accounts,schedules}/{list,partial_cards}.html` (the six); `app/templates/history/list.html:119`, `history/partial_cards.html:6`, `admin/user_history.html:63`, `admin/history_partial_cards.html:7`, `account_groups/includes/sentinel.html:72-74`, `account_groups/{list,partial_cards}.html` (macro calls), `account_groups/partials/*.html` (checked for sentinel inclusion: none)
- Loading labels: `app/templates/accounts/includes/tg_connect_step.html:83,150`, `accounts/connect_wa.html:44`, `accounts/includes/max_connect_step.html:89`
- `app/pages/schedules.py` (`:1096-1142`, `:1336-1420`, refusal-site grep), `app/pages/notices.py:134, :273-279`, `app/pages/common.py:30-48`
- `app/pages/history.py` (`:559`, `:620-633`, `:1140-1180`), `app/pages/admin.py` (`:1407-1488`, `:1505`, `:1561-1572`), `app/pages/account_groups.py` (`:241-280`, `:298`, `:362-376`); `page_size` grep across `app/pages`
- `tests/test_pages/test_shell.py:4302` (`FAILURE_BANNER_STACK_LINES`); `tests/test_templates/test_banner_dismiss.py:884` (reference to this file, prose only)
- `git diff --stat b82099de..HEAD -- app/`, `git diff a674e8e5..HEAD -- app/templates app/static`, `git log -- app/`
- Planning: `15-UI-REVIEW.md` (prior edition, 2026-09-24), `15-CONTEXT.md`, `15-16-SUMMARY.md`, `15-19-SUMMARY.md`, `15-21-SUMMARY.md`, `15-23-SUMMARY.md`, `must_haves.truths` of `15-16/19/21/23-PLAN.md`, `STATE.md:482-487, 657, 675, 683` (grep), `15-UAT.md:301, 429` (У-8 located; not edited)

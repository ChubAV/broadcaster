# Phase 11 — UI Review

**Audited:** 2026-09-18 (re-audit; replaces the 2026-09-17 edition of this file)
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for this phase); the phase's own contract (11-CONTEXT D-01…D-16, plan `must_haves`) used where it names visible behaviour
**Screenshots:** **not captured — CODE-ONLY AUDIT.** No dev server answered on 3000/5173/8080/8000, and this host carries a live production deployment, so none was started. Playwright/Chrome MCP tools were not available to this run. **Nothing below is a browser observation.** Every runtime claim cites the CSS rule, the template line, or the vendored `app/static/js/htmx.min.js` it rests on. Where a claim would need a browser, it is marked *unobserved* and named as arithmetic, not sight.

**What changed since the prior edition:** exactly one plan landed — 11-21 (`ec33c8e` RED, `810eaa7` GREEN, `bf3cb65` gates). `git diff 073ba75..bf3cb65 -- app/` is two files, +75/−1: `app/templates/components/form_wrapper.html` (one literal attribute + comment) and `app/static/css/app.css` (three rules + comment). No other product file moved. Every other finding below was re-derived against the current tree, not carried on the prior review's authority.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Unmoved since the prior edition: the MAX failure still interpolates a raw Python exception (`accounts.py:675`), and two refusal paths still give advice that cannot help |
| 2. Visuals | 2/4 | Both 422 paths still draw the field error as a detached banner (`alert(error)`) with the field's own invalid state unused; the MAX failure fragment still shows an error beside an endless «Ожидание QR-кода...» poll |
| 3. Color | 3/4 | ↓ from 4/4. 11-21 moved the 8px `--text-muted` dot **on top of** `--accent-cta`-filled buttons at two call sites; that token pair was never in contact before and computes to roughly 2–3:1 |
| 4. Typography | 4/4 | No font size or weight declaration added by the phase or by 11-21; all new text goes through existing macros |
| 5. Spacing | 3/4 | ↑ from 2/4. The `.form-busy` layout footprint is **closed** by 11-21 and machine-guarded; the profile alert's 0px gap is still open and the browser half of the closure is still unobserved |
| 6. Experience Design | 2/4 | Unmoved: `hx-disabled-elt` still disables «ВЫБРАТЬ ВСЕ» instead of «СОХРАНИТЬ РАСПИСАНИЕ», focus still drops to `<body>` on every swap, the MAX error state is still a dead end |

**Overall: 17/24**

⚠️ **The total is unchanged, and that is misleading on its own.** The composition moved in two directions: Spacing rose 2→3 on real, gated work, and Color fell 4→3 on a side effect of that same work. Read the pillars, not the sum.

*(Record note: the orchestrator brief for this re-audit cites the prior overall as 14/24; the prior file itself records **17/24**. The file is taken as the record.)*

---

## Top 3 Priority Fixes

1. **WARNING — Field errors on both new 422 paths are banners, not field errors.** `includes/profile_settings.html:85` renders `{% if error %}{{ alert(error) }}{% endif %}` as the first child of `#profile-settings`, and `select_field(name="timezone", …)` at `:88` gets no `error=`. `accounts/includes/max_connect_step.html:26` renders the alert as a sibling of the card inside `.connect-shell`, and `field(name="phone", …)` at `:66` gets no `error=`. `components/field.html` already implements `error=` → `field--invalid`, `aria-invalid="true"`, `.field__error`; neither screen uses it. The phase claims «ошибка поля рисуется у формы» (D-12 of Phase 8, FORM-08) — that is half true: the error reached the form's *area*, not the *field*.
   - **User impact:** in the MAX wizard the error sits above the card, a card-height away from the input it is about. Neither input is marked invalid for assistive technology. In the profile the banner butts against the «Часовой пояс» label with no gap (see Pillar 5).
   - **Fix:** `select_field(name="timezone", …, selected=selected, error=error, id='timezone')` in `profile_settings.html`; `field(name="phone", …, value=phone or '', error=(error if step == 'phone' else none), …)` in `max_connect_step.html`. Keep `alert()` only for non-field errors — the bridge failure on the `qr` step is the one that stays a banner.

2. **WARNING — The schedule edit form disables the wrong button and drops focus on every swap.** `ads/includes/sched_card.html:210` calls `form_wrapper(action='/schedules/{id}/edit', target='#sched-N', swap='outerHTML')` with the default `disabled_elt='find button[type=submit]'`. In the vendored htmx 2.0.10 `find` is `querySelector` — verified: `function f(e,t){if(typeof e!=="string"){return e.querySelector(t)}` in `app/static/js/htmx.min.js`. The first submit button inside that form is «ВЫБРАТЬ ВСЕ» (`:265`, `name=groups_preset`), always rendered; «СОХРАНИТЬ РАСПИСАНИЕ» is last (`:303`). So the save button stays live during the request and an unrelated preset greys out. Compounding: the `outerHTML` swap replaces the pressed button, htmx restores focus only to an element carrying an `id`, and `components/button.html:16-17` has no `id` parameter at all (`macro button(label, variant, type, name, value, icon, disabled, title, extra_class)`). `grep -rn "afterSwap\|afterSettle\|\.focus()" app/templates` returns only `components/modal.html` — no swap-time focus handling exists.
   - **User impact:** a double click on save sends two requests. A preset button flickers disabled for no reason a user can connect to their action. Keyboard users land on `<body>` after every «БУДНИ», «+ ВРЕМЯ», «×» and «СОХРАНИТЬ РАСПИСАНИЕ» in a form that needs several presses in a row.
   - **Fix:** pass `disabled_elt='find button[name=save_schedule]'` (`find` resolves one element, so this narrows rather than widens). Add an `id=` parameter to `components/button.html` and give the save button `sched-save-{{ s.id }}` so htmx restores focus after the swap; do the same for the admin toggles (`#user-actions`, `innerHTML`), the profile «Сохранить» and the MAX «Продолжить».

3. **BLOCKER — The MAX failure state leaks a raw exception and is a dead end.** `app/pages/accounts.py:675` sets `error = f"Ошибка подключения к MAX: {e}"`, then `_step()` renders `_max_step_markup(step="qr", qr_code=qr_code, error=error)` with `qr_code=None`. That lands in `max_connect_step.html:87-93`: «Загрузка QR-кода...» plus `<div id="max-status" hx-get="/accounts/connect/max/status" hx-trigger="every 3s">` showing «Ожидание QR-кода...» — forever. The phone form is gone from the fragment, so the screen offers no retry at all.
   - **User impact:** the user reads bridge/driver text (potential internal detail disclosure), next to a spinner claiming a QR is on its way that never arrives, with no control to try again except the page-level «К аккаунтам» link or a manual reload. This is the one finding in this report that stops a task outright: a failed MAX connection cannot be retried in place.
   - **Fix:** log `e` and render a fixed message («Не удалось подключиться к MAX. Проверьте номер и попробуйте ещё раз.»); on the error branch render the **phone step** (`step="phone"`, phone echoed) instead of a QR step with no QR, so the retry control comes back with the error.

### Further fixes (there are more than three)

4. **WARNING — The busy dot now paints over accent-filled buttons** (new, introduced by 11-21). See Pillar 3.
5. **WARNING — The busy dot is now far from the control that was pressed in wide forms** (new, introduced by 11-21). See Pillar 5.
6. **WARNING — The profile error banner touches the form with 0px gap** (`profile_settings.html:85`; `.alert` has no margin, `app.css:844-848`; `#profile-settings` has **no** CSS rule — `grep -n "profile-settings" app/static/css/app.css` is empty).
7. **WARNING — Two refusal paths give advice that cannot help:** the owner-accepted bare `403` (D-08) and the malformed-request `400` (T-11-14) both raise «Действие не выполнено. Попробуйте ещё раз через минуту.» (`includes/htmx_error_banner.html:300`), and retrying will not help in either case.
8. **Minor — «Применить» is a generic label** (`sched_card.html:184`, `schedule_row.html:113`), and the notice registry mixes final punctuation («Настройки сохранены.» `notices.py:291` vs «Задача снята из очереди» `:229`).

---

## Disposition of the 2026-09-17 findings

Every finding raised by the prior edition, re-derived against the current tree. Nothing from that edition is dropped.

| # | Prior finding | State | Evidence re-derived today |
|---|---|---|---|
| P1-a | MAX failure surfaces a raw exception `Ошибка подключения к MAX: {e}` | **still open** | `app/pages/accounts.py:675` unchanged |
| P1-b | Owner-accepted bare 403 shows «попробуйте ещё раз через минуту» — wrong advice | **still open** (accepted, D-08) | `includes/htmx_error_banner.html:300`; `OWN_RESPONSE_EXITS` record stands |
| P1-c | The same generic banner covers the new malformed-request 400 | **still open** (accepted, T-11-14) | same banner, same handler; no 400-specific rule added |
| P1-d | Inconsistent final punctuation in the notice registry | **still open** | `app/pages/notices.py:229` vs `:291` |
| P1-e | «Применить» is a generic label | **still open** | `sched_card.html:184`, `schedule_row.html:113` |
| P2-a | Both 422 paths render the field error as a detached banner, field's own error state unused | **still open** | `profile_settings.html:85,88` (no `error=` on `select_field`); `max_connect_step.html:26,66` (no `error=` on `field`) |
| P2-b | MAX failure fragment: error beside an endless «Ожидание QR-кода...» poll | **still open** | `accounts.py:675-680` → `max_connect_step.html:87-93` |
| P2-c | After creating a schedule two cards are expanded | **still open** (accepted, D-05) | `ads/partials/sched_create_response.html`, unchanged |
| P2-d | The «Применить» fallback button is in the markup of every toggle until Alpine removes it | **still open** | `<span x-data x-init="if (window.htmx) $el.remove()">` at `sched_card.html:184`, `schedule_row.html:113` |
| P3 | 4/4, no colour deviation | **superseded** | Re-derived: the phase still adds no hex/rgb/colour token (the only `style=` uses in `app/templates` pass `--cols`, `--avatar-size`, `width: %`). But 11-21 created a **new** colour contact — see Pillar 3 |
| P4 | 4/4; raw `<button class="btn …">` in `billing/balance.html` and `admin/*` noted for consistency | **still open** (minor, pre-phase) | `billing/balance.html:124` still writes the button by hand |
| **P5-a** | **Hidden `.form-busy` inline-block opens an empty line box under «Сохранить»/«Продолжить»** | **CLOSED** | `form_wrapper.html:163` now prints `class="form-wrapper"`; `app.css:2207-2210` gives that form `position: relative` and its child indicator `position: absolute; right: 0; bottom: 0; pointer-events: none`. Base `.form-busy` (`:2193`) untouched, still the only rule with that exact selector, still `display: inline-block`, both transition thresholds intact (`:2198`, `:2203`). Guarded by `test_a_wrapped_form_gives_its_indicator_no_layout_footprint` + `test_the_reported_profile_form_carries_the_indicator_scope` — I ran them plus the two panel gates and the two legacy indicator gates: **6 passed, 1 warning in 0.47s** |
| **P5-b** | **~12px trailing space after each wrapped button made flex action-row gaps uneven** | **CLOSED at code level; browser half unobserved** | Same rule: an absolutely positioned child contributes no width to the shrink-wrapped form, and the whitespace node before it becomes a collapsible trailing space. All 14 call sites inherit it from the macro (`grep -rn "call form_wrapper"` → 14, none patched individually). The horizontal-evenness observation is item 4 of UAT check 6 and is **not** recorded as seen |
| P5-c | The profile alert touches the form with 0px gap | **still open** | `.alert` carries no margin (`app.css:844-848`); `#profile-settings` still has no rule; the alert is still the first child of that plain block div (`profile_settings.html:85`, `profile.html:62`) |
| P5-fix-note | Prior fix text proposed `inset-inline-end: -14px; top: 50%` and a whitespace-control change in the macro | **superseded, with reasons on the record** | 11-21-PLAN rejected both: a negative offset would leave the form box and be clipped by `.card { overflow: hidden }` or land on a neighbouring control in 8–9px rows; with the node out of flow the leading whitespace collapses, so touching whitespace control would move the rendered markup of 14 forms for nothing. Both rejections are sound and are recorded in `app.css:2173-2179` |
| P6-a | `hx-disabled-elt` disables the wrong button on schedule edit | **still open** | `sched_card.html:210` (default `disabled_elt`), first submit `:265`, save `:303`; `find` = `querySelector` in the vendored htmx |
| P6-b | Focus lost on every swap whose trigger has no `id` | **still open** | `components/button.html:16-17` still has no `id` parameter; no `htmx:afterSwap`/`afterSettle` focus handling anywhere in `app/templates` |
| P6-c | MAX error state is a dead end | **still open** | see P2-b |
| P6-d | No visible confirmation on in-place success | **still open** (accepted, D-03 of Phase 10) | unchanged |
| P6-e | A filtered schedule list goes stale after a toggle | **still open** (accepted price, D-11) | unchanged |
| P6-manual | Four items the owner had to check by hand | **three observed by agent, one closed-then-reopened** | 11-UAT: scroll on create `pass` (test 2), Alpine after swaps `pass` (test 3), Back/F5 `pass` (test 4); «extra space under Продолжить» was `issue` → G-11-6 → fixed by 11-21 → **the browser observation is still unrecorded** (`11-UAT.md` check-6 table is empty; `.planning/WINDOWS.md` window **88**, `unrun-verify`, status `open`) |

**Confirmation panel: left alone, verified independently of the plan's word.** `components/modal.html:805` still opens `<form class="modal__form" method="post" …>` with no scope class. `grep -rn 'form-wrapper' app/templates app/static/css/app.css` outside the macro returns only the two CSS rules — the scope name exists in exactly three places and none of them is the panel. `.modal__form` is untouched at `app.css:1346` (`display: flex; flex-direction: column; gap: 14px`). The panel's accepted ~22px (owner decision 1, 10-UAT 3.5) survive. `test_the_confirmation_panel_indicator_keeps_its_accepted_place` passed in my run. **No panel regression to report.**

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

Unchanged by 11-21, which touched no user-visible string. Score held at 3/4 rather than lowered: the moved texts are genuinely specific, and the defects are concentrated in refusal paths.

**Passing evidence (re-derived):** the queue-drop outcomes read as outcomes, not statuses — «Задача снята из очереди», «Задача уже ушла из очереди — снимать нечего», «Не удалось снять задачу: Redis не отвечает, а очередь хранится только в нём», «Снимать нечего: у этого аккаунта нет своей очереди задач» (`app/pages/notices.py:229-243`). Field-error strings are specific and dictated to the field: «Неверный часовой пояс», «Введите номер телефона» (`accounts.py:542`). Toggle labels name the action on the new state («Снять/Выдать бесплатный доступ», `admin/includes/user_actions.html:71-72,84-85`).

**WARNING — raw exception text reaches the user** (`accounts.py:675`). Pre-phase in origin, moved verbatim into the new fragment by plan 11-18 rather than fixed. See Top fix 3.

**WARNING — two refusal paths give advice that cannot help.** The bare `403` (D-08, owner-accepted as unreachable from the UI) and the malformed-request `400` (T-11-14) both raise «Действие не выполнено. Попробуйте ещё раз через минуту.» (`htmx_error_banner.html:300`; only 422 is excepted). This pillar measures what a user would read, not whether the path is reachable, so it stays on the record in both cases.

**Minor — punctuation and one generic label.** `notices.py:291` «Настройки сохранены.» ends with a period; its neighbours at `:229`/`:194` do not. «Применить» (`sched_card.html:184`, `schedule_row.html:113`) says nothing about what it applies; its blast radius is small because it only exists in the Alpine-alive/htmx-dead world.

### Pillar 2: Visuals (2/4)

**WARNING — the 422 error is not shown in the field's error state.** See Top fix 1. This is the visual half of the same defect: `components/field.html` implements `field--invalid` / `.field__error` / `aria-invalid="true"`, and on both screens the phase introduced a field error for, that machinery goes unused. In the MAX wizard the alert is a sibling of the card inside `.connect-shell` (flex column, gap 14px, `app.css:1946`), so the error floats above the card instead of beside the phone input it describes.

**BLOCKER — the MAX failure state contradicts itself.** See Top fix 3. Error alert + «Загрузка QR-кода...» + a 3-second poll announcing «Ожидание QR-кода...», with the phone form removed from the fragment.

**WARNING — after creating a schedule, two cards are expanded** (accepted by D-05, but a real layout state): the new card arrives expanded and a previously expanded card stays expanded until F5, so a long editor can show two tall open forms and no single focal card.

**WARNING — the «Применить» fallback button is in the markup of every toggle** (`sched_card.html:184`, `schedule_row.html:113`), removed by `x-init="if (window.htmx) $el.remove()"`. Whether it paints for a frame on first paint and on every toggle fragment cannot be judged from code. Note that it also affects the new indicator geometry: until Alpine strips it, the rightmost element of those toggle forms is that button, not the toggle.

**Passing evidence:** only content is swapped — `sched_card_response.html` never carries the `sched-del-N` panel root, and panel text is replaced through the permanent `{{ id }}-text` id (`components/modal.html`), so the Alpine-stateful panel cannot be duplicated in markup. The admin card takes its state from one source (`user_actions.html`, `user_block_badge.html`, `user_access_tile.html`), and the empty badge wrapper gets `display: contents` so unblocked users get no phantom gap. `data-plan-cta` sits on the wrapper div, so `[data-plan-cta] .btn { min-height: 44px }` (`app.css:1612`) still reaches the payment button.

### Pillar 3: Color (3/4 — down from 4/4)

**WARNING (new, introduced by 11-21) — the busy dot is now painted on top of accent-filled buttons, a token pair that was never in contact before.** `.form-busy` has exactly one colour: `background: var(--text-muted)` (`app.css:2195`), and `--text-muted: #6a6a78` (`:47`) was chosen to read against the dark page surface (`--bg: #08080b`, `:24`). Before 11-21 the dot always sat on that surface. After 11-21 it sits at `right: 0; bottom: 0` **inside the form box**, and at two call sites the form box is exactly the button box:
- `accounts/includes/max_connect_step.html:67` — «Продолжить» is `extra_class='btn--block'` (`app.css:713`, `width: 100%`) inside `.connect-step__form` (`align-items: stretch`, `:1934`), so the form's right and bottom edges are the button's edges. The dot lands on `.btn--primary` → `background: var(--accent-cta)` (`:715`), `--accent-cta: oklch(0.79 0.14 305)` (`:54`) — a light violet.
- `account_groups/list.html:104-108` — «Синхронизировать всё» / «Синхронизация…», `variant='primary'`, the form shrink-wrapped around it in `.acct-head__actions`. Same contact.

Computed from the token values (not measured in a browser, and not eyeballed): `#6a6a78` against an oklch-0.79 violet is roughly **2–3:1**, i.e. at or below the 3:1 floor WCAG 1.4.11 sets for non-text UI components. The dot is the *only* signal of a request in flight on the MAX step, where `asyncio.sleep(5)` guarantees a wait of at least five seconds — so this is the one place the indicator matters most.
- **Fix:** give the indicator a contrast-safe colour when it sits on a filled control, e.g. `.btn--primary + .form-busy`-style scoping or a `currentColor`/`--text-on-accent` variant inside `.form-wrapper > .form-busy` when the last flow child is a filled button. Cheapest correct version: add a thin contrasting ring (`box-shadow: 0 0 0 1px var(--bg)`) so the dot reads on any background. Measure, do not eyeball.

**Passing evidence (re-derived):** the 11-21 diff to `app.css` adds **zero** colour declarations — the added product lines are `position`, `right`, `bottom`, `pointer-events` and one `position: static` exception. A scan of `app/templates` finds no colour literals introduced by this phase: the only hex values are the brand SVG in `includes/messenger_icon.html` and the `theme-color` meta, and all nine `style=` attributes in the template tree pass layout custom properties (`--cols`, `--avatar-size`, `width: %`), never colour. The retired `?result=` channel's four variants moved unchanged; `error` still renders in `#notice-alert` (`role="alert"`), success/warning in `#notice` (`role="status"`).

### Pillar 4: Typography (4/4)

The phase and plan 11-21 add no font-size, font-weight or line-height declaration. The 11-21 CSS diff contains four positioning properties and nothing else; `form_wrapper.html` gained one literal attribute.

All new text goes through existing macros — `button()`, `field()`/`select_field()`, `alert()`, `mono()`, `badge()`. The new partials (`sched_card_response.html`, `sched_create_response.html`, `schedule_row_response.html`, `user_actions_response.html`) include page templates rather than copying markup, so a fragment and its full page cannot drift typographically.

**Minor (pre-phase, not a regression):** `billing/balance.html:124` still hand-writes `<button class="btn btn--primary" type="submit"><span class="btn__label">…</span></button>` instead of calling `button()`. One more copy of the button's internal structure that a macro change would silently miss. Recorded for consistency only — it is the reason this pillar is a clean 4 rather than a fabricated one.

### Pillar 5: Spacing (3/4 — up from 2/4)

**CLOSED — the `.form-busy` layout footprint.** The mechanism named by the prior edition and by the debug session is gone, at the one place that serves all 14 call sites:
- `app/templates/components/form_wrapper.html:163` — `<form method="post" action="{{ action }}" hx-post="{{ action }}" class="form-wrapper" …>`; the literal sits after the request address and before the target branches, and the indicator node at `:170` is unchanged.
- `app/static/css/app.css:2207-2210` — `.form-wrapper { position: relative; }` and `.form-wrapper > .form-busy { position: absolute; right: 0; bottom: 0; pointer-events: none; }`.
- The base rule survives intact: `.form-busy` at `:2193` is still the only rule with that exact selector, still declares `display: inline-block`, declares no `position`, and both thresholds (`:2198` resting, `:2203` `.htmx-request` with the 300ms delay) are byte-identical.
- The group-row exception is real and wins on specificity: `[data-group-row] form[action$="/toggle"] > .form-busy { position: static; }` (`:2762`) at (0,3,2) beats the scope rule at (0,2,0) regardless of file order, so the accepted dot beside the group toggle (09-UAT 6.1.2) stays in flow.
- I ran the guarding gates myself rather than trusting the summary: `test_a_wrapped_form_gives_its_indicator_no_layout_footprint`, `test_the_confirmation_panel_indicator_keeps_its_accepted_place`, `test_the_reported_profile_form_carries_the_indicator_scope`, `test_the_panel_form_stays_outside_the_indicator_scope`, `test_the_indicator_class_is_self_sufficient`, `test_the_indicator_class_carries_a_visibility_threshold` → **6 passed, 1 warning in 0.47s**.

The uneven-gap half follows from the same rule: an out-of-flow child contributes no width to a shrink-wrapped form, and the leading whitespace becomes a collapsible trailing space. The three reported heights (21px profile, 18.5px MAX, 24px schedule edit) and the ~12px row tail have no mechanism left to come from.

**The browser half of this closure is UNOBSERVED, and is scored as unobserved, not as seen.** `11-UAT.md` check 6's mark table is empty; `.planning/WINDOWS.md` window **88** records it `unrun-verify`, status `open`: «наблюдение высот и наложения точки поверх угла органа в браузере не снято — ждёт человека». That is why this pillar is 3 and not 4.

**WARNING (new, from the same fix) — the indicator moved away from the control that was pressed, in exactly the forms the fix targeted.** The offsets are planner discretion (11-21-PLAN: «Место точки внутри коробки формы (усмотрение планировщика)»), not an owner decision, so this is in scope to report. In every *wide* wrapped form the dot now appears at the form box's bottom-right corner, which is not where the button is:
- `includes/profile_settings.html` — `[data-form] { align-items: flex-start }` (`app.css:1867`), so «Сохранить» is left-aligned while the form spans the card body: the dot appears at the far right of the card, roughly a card-width from the button.
- `ads/includes/sched_card.html:302-304` — `.sched-card__actions` is a left-aligned flex row (`app.css:2375`) at the bottom of a ~1686px-tall form; same displacement.
- `billing/balance.html:123-125` — `.btn--primary` is not `btn--block`, so the dot lands on the surface to the right of the CTA rather than on it.

Compounding on schedule edit: the disabled element is also the wrong button (Pillar 6), so during a save **nothing at the pressed control** indicates work in progress — a preset button greys out at the top of the form and a dot appears at the bottom-right corner.
- **Fix (cheap, keeps the owner's constraint):** keep the dot inside the form box, but anchor it to the actions row rather than the form box — e.g. `.form-wrapper { position: relative }` plus a scoped override for forms whose last flow child is an actions row, or place the indicator's containing block on `.sched-card__actions` / `[data-form]`'s last row. Do not revert to a negative offset: `.card { overflow: hidden }` and 8–9px row gaps rule that out, as 11-21 correctly recorded.

**WARNING — the profile alert still has 0px gap before the form.** `includes/profile_settings.html:85` renders the alert as the first child of `#profile-settings` (`profile.html:62`), which is a plain block div — `grep -n "profile-settings" app/static/css/app.css` returns nothing, and `.alert` declares no margin (`app.css:844-848`). The alert box touches the «Часовой пояс» label. 11-21 did not address this and was not asked to. It disappears entirely if Top fix 1 moves the error into `select_field(error=…)`; otherwise give `#profile-settings` the `[data-form]` column and gap.

**Unobserved overlap risk, named as arithmetic rather than sight.** UAT check 6 item 5a asks a human to look at exactly this: an 8px dot now sits over the bottom-right corner of a control. My geometry from the stylesheet says the two named fears do **not** reproduce, but this is arithmetic and must not be read as an observation:
- *Toggle knob:* `.sched-card__head .toggle` and `.sched-item__head .toggle` both carry `min-height: 40px` (`app.css:2319`, `:2578`) with `align-items: center` on the row, while `.toggle__track` is 22px (`:801`). The track therefore occupies the middle 22px of a 40px box and the dot's 8px band falls below it, not on the knob. The group-row toggle — the one place where a short toggle would put the dot on the knob — is excepted to `position: static`.
- *Button label:* `.btn { padding: 9px 16px }` (`app.css:705`) with a centred label, so an 8px dot in the corner sits in padding, not on text.
- What the arithmetic cannot settle: sub-pixel rounding, the `.sched-card__head` row when the «Применить» fallback is still in the DOM (which shifts the form's right edge onto that button), and whether the dot reads as an indicator or as a rendering artifact. Those need the human pass that window 88 is holding open.

### Pillar 6: Experience Design (2/4)

**State coverage**

| State | Coverage |
|---|---|
| Loading | Every converted form gets `hx-indicator="find .form-busy"` with the 300ms threshold. The MAX start (≥5s by `asyncio.sleep(5)`) gets both the indicator and a disabled button. The removed inline `onsubmit` label swap («Подключение…») is not replaced, so the only wait signal is an 8px dot — now sitting on a light accent button where its contrast is unverified (Pillar 3). |
| Error | 422 swaps back into the same target (`htmx_config.html`: `{"code":"422","swap":true,"error":true}`). 4xx/5xx raise the failure banner. The empty 400 for malformed htmx requests closes the T-07-13 sink. |
| Disabled | The wrapper disables the default target; on schedule edit that is the wrong button. Toggles use `disabled_elt=''` with `hx-sync="this:drop"` (DIV-09-02), a deliberate exception recorded in `DISABLED_ELT_EXCEPTIONS` because disabling the checkbox would disable the element QUAL-06 returns focus to. Payment keeps indicators across `HX-Redirect` (the vendored htmx sets `keepIndicators=true` before `location.href`). |
| Destructive confirmation | Unchanged. Delete panels stay outside swap targets and are verified untouched by 11-21. The admin block toggle has no confirmation (UI contract E5, intentional). |

**WARNING — wrong disabled element on schedule edit.** See Top fix 2. Re-derived today: `sched_card.html:210` default `disabled_elt`, first submit at `:265`, save at `:303`, `find` → `querySelector` in the vendored htmx.

**WARNING — focus is not restored after swaps.** `components/button.html` has no `id` parameter (`:16`), and `grep -rn "afterSwap\|afterSettle\|\.focus()" app/templates` returns only `components/modal.html`. htmx restores focus only to an element whose `id` exists in the new content, so focus drops to `<body>` after: the schedule edit form's presets, add/remove time and save (`outerHTML`); admin «Заблокировать»/«Выдать бесплатный доступ» (`innerHTML` of `#user-actions`); profile «Сохранить» (`innerHTML` of `#profile-settings`); MAX «Продолжить» (`innerHTML` of `#max-connect-step`). On a 422 focus is not moved to the invalid field either. The toggles are the exception — `sched-toggle-N` and `schedule-toggle-N` carry ids (`sched_card.html:180`, `schedule_row.html:109`), so QUAL-06 holds there.

**BLOCKER — the MAX failure step is a dead end.** See Top fix 3.

**WARNING (accepted, D-03 of Phase 10) — no visible confirmation on in-place success.** Schedule edit/toggle and the admin toggles return the re-rendered block with no notice. Saving a schedule with unchanged values looks identical to nothing happening, and the dot only appears after 300ms, so a fast save gives no feedback at all. Profile save is the one converted in-place action that confirms («Настройки сохранены.» out-of-band).

**WARNING (accepted price, D-11) — a filtered schedule list goes stale.** A row toggled out of an active `state=` filter stays visible in its new state and the `total` line is not repainted until reload. The keyset cursor (`after_id`) does prevent the next page from skipping a row, which was the more serious failure this phase fixed.

**Passing evidence:** the first-schedule case avoids a silently dead button through a conditional target (`ads/form.html:277`, `target=('#sched-list' if editor.schedules else none)`) — htmx 2.0.10 aborts on `htmx:targetError` before sending, and this is tested. `_SYNC_IN_FLIGHT` is released on every htmx exit (plan 11-17). The free-access tile renders after `invalidate_access_cache` (plan 11-13). `grep -rn hx-push-url app/templates` returns 0, matching D-13.

---

## Registry Safety

Skipped: `components.json` is absent (no shadcn), and there is no UI-SPEC registry table. No third-party UI blocks are installed.

---

## Files Audited

**Re-derived for the 11-21 delta**
- `app/templates/components/form_wrapper.html` (macro tag `:162-171`), `app/static/css/app.css` (`:2152-2210` indicator section, `:2762` group-row exception, `:1346` `.modal__form`)
- `app/templates/components/modal.html:805` (panel form tag — verified untouched)
- `tests/test_templates/test_htmx_markup_gates.py`, `tests/test_templates/test_components.py` (four new gates — executed, 6 passed)
- `git diff 073ba75..bf3cb65 -- app/`

**Re-derived for the carried findings**
- `app/templates/includes/profile_settings.html`, `app/templates/profile.html`
- `app/templates/accounts/includes/max_connect_step.html`, `app/templates/accounts/connect_max.html`, `accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html`
- `app/templates/ads/includes/sched_card.html`, `ads/form.html`, `app/templates/schedules/includes/schedule_row.html`
- `app/templates/admin/includes/user_actions.html`, `app/templates/account_groups/list.html`, `app/templates/account_groups/includes/group_row.html`, `app/templates/billing/balance.html`
- `app/templates/components/button.html`, `components/toggle.html`, `components/field.html`, `includes/htmx_error_banner.html`
- `app/pages/accounts.py` (MAX start branch `:655-681`), `app/pages/notices.py`, `app/pages/profile.py`
- `app/static/js/htmx.min.js` (vendored 2.0.10 — `find` → `querySelector` confirmed by source)

**Records**
- `11-UI-REVIEW.md` (2026-09-17 edition), `11-CONTEXT.md`, `11-UAT.md`, `11-21-PLAN.md`, `11-21-SUMMARY.md`, `.planning/WINDOWS.md` (window 88)

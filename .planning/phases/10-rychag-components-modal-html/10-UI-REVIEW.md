---
phase: 10-rychag-components-modal-html
audited: 2026-09-12
baseline: abstract 6-pillar standards (no UI-SPEC.md for this phase)
screenshots: not_captured
score: 15/24
---

# Phase 10 — UI Review

**Audited:** 2026-09-12
**Baseline:** abstract 6-pillar standards — **there is no UI-SPEC.md for this phase**, so no declared spacing scale, type ramp or 60/30/10 split exists to audit against. Every finding below is measured against house tokens actually present in `app/static/css/app.css` and against general UX standards, not against a contract.
**Screenshots:** **NOT CAPTURED.** No dev server responded on ports 3000 / 5173 / 8080 / 8000 (all `000`), and the repository has no browser driver at all (`playwright|selenium|puppeteer|splinter` → 0 occurrences tree-wide). **This audit is code-only.** Three behaviours of this phase are RECTANGLES, not declarations, and they remain owed to a human observer — they are named in "Owed to a human" below and are NOT scored as if seen.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Dialog copy is specific and consequence-bearing in 6 consumers, but two pass a bare identifier as `body`, and the failure banner promises a recovery time it cannot know |
| 2. Visuals | 2/4 | The two failure banners are declared at the SAME `top`/`z-index` — when both are shown one hides the other by construction (app.css:1188-1197) |
| 3. Color | 3/4 | Entirely token-driven except four hand-written `rgba(8, 8, 11, …)` literals; error-banner contrast never measured |
| 4. Typography | 3/4 | Only two sizes on the new surface, but a dialog title at 15px over 13px body is a 1.15× ratio — the weakest possible hierarchy |
| 5. Spacing | 2/4 | The project has NO spacing token at all (`--space*` → 0 hits); this phase added five more raw literals (22/20/14/12/9px) to that vacuum |
| 6. Experience Design | 2/4 | The failure banner has no dismiss control and is cleared ONLY by a later *successful* htmx request — on a screen with no further htmx it stays over the viewport for the rest of the session |

**Overall: 15/24**

---

## Owed to a human — not scored, not assumed

These cannot be settled by reading code, and nothing below treats them as passing:
1. **Rectangle of the network-failure banner at working scroll position** (walkthrough step 2.8). Only the declaration `position: fixed; top: 12px; z-index: 70` is verifiable here.
2. **Failure banner stacking over an open confirm panel** (step 4.4). `.modal` is `z-index: 60`, banner is `70` — ordering is declared, painting is not.
3. **Acceptance signature.** `10-UAT.md` is `status: partial`; both walkthrough blocks were taken by an agent, not by a human on acceptance.

The CSS block itself states this boundary at app.css:1170-1177, and window 77 already records that asserting a stylesheet DECLARATION is not the same subject as a rendered RECTANGLE. That record is correct and this audit does not weaken it.

---

## Top 3 Priority Fixes

1. **BLOCKER — the failure banner has no exit.** `app/templates/includes/htmx_error_banner.html:227-233` un-hides on failure and re-hides only inside `htmx:afterRequest` guarded by `if (!event.detail.successful) return;`. A user who hits a network drop on a screen that issues no further htmx request (or issues only failing ones) keeps a fixed, full-width rectangle pinned over the top of every screen until reload — the exact cost app.css:1225-1233 named for the unconditional lift, only partly paid by the third handler. *Fix:* add a close button inside each banner wrapper (`<button type="button" class="btn btn--ghost" aria-label="Скрыть сообщение">`) that sets `hidden`, and additionally auto-hide `#htmx-failure-network` on the next `htmx:beforeRequest` so a retry visibly clears the prior failure.

2. **BLOCKER — two banners occupy one rectangle.** `#htmx-failure-server` and `#htmx-failure-network` share `top: 12px; left: 0; right: 0; z-index: 70; width: min(560px, …); margin: auto` (app.css:1188-1197). Nothing offsets the second. A server error followed by a send error shows both, and the later one in DOM order paints over the earlier — the user loses one of two distinct recovery instructions. Window 76 recorded the overlap; the styling still does not fix it. *Fix:* wrap both in one `position: fixed` flex-column stack with `gap: 8px` and make the two children `position: static` inside it, so N banners stack instead of superimpose.

3. **WARNING — failure banners are not announced.** `notice_area.html:135-136` does this correctly: persistent containers carrying `role="status" aria-live="polite"` / `role="alert" aria-live="assertive"` into which content is injected. The failure banners do the opposite: the `role="alert"` node (from `components/alert.html:10`) is present in the DOM from page load inside a plain `<div hidden>`, and only the wrapper's `hidden` attribute is toggled. Toggling visibility of a pre-existing alert node is not a reliable announcement trigger for assistive tech. A blind user gets no signal that their delete failed. *Fix:* give the wrappers `aria-live="assertive"` and inject/clear the alert's text content rather than toggling `hidden` on a pre-rendered node — mirroring the pattern this phase's own `notice_area.html` already uses.

---

## Further findings (the list does not stop at three)

4. **WARNING — dialog bodies are inconsistent across the 10 consumers.** Six pass a consequence sentence; two pass an identifier. `ads/form.html:301` passes `body=ad.title`; `accounts/list.html:190` passes `body=label ~ ' #' ~ account.id`. Compare `admin/workers.html:57` ("Задача, которую воркер уже взял в работу, будет потеряна…") and `history/includes/history_card.html:177` ("Отправка в группу необратима и списывает сообщение с баланса"). Destroying an ad — which takes its schedules with it — is the case that most needs the consequence sentence and is the one that gets only a title echo.
5. **WARNING — `422` is swallowed silently on a `hx-swap="none"` path.** `htmx_error_banner.html:218` returns early on status 422, while the modal form posts with `hx-swap="none"` (`components/modal.html:807`). Any 422 reaching a modal-submitted form produces: no swap, no banner, no notice — the panel simply sits there after a click. The early return is deliberate for form re-render paths, but it is unguarded against the swap-less path.
6. **WARNING — no `aria-describedby` on the dialog.** `components/modal.html:715` sets `aria-labelledby="{{ id }}-title"` but never associates `.modal__text` (`:808`), so the consequence prose in six consumers is not part of the dialog's accessible description.
7. **INFO — focus return has a named hole, already documented not fixed.** `components/modal.html:22-30` records that on the htmx group-delete path the panel is removed out-of-band rather than hidden, `hide()` never runs, and focus lands on `<body>`. Honestly disclosed; still a keyboard-user defect shipped by this phase.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)
Strong overall and clearly deliberate. Titles are questions naming the object ("Удалить объявление?", "Перезапустить воркер?", "Войти под пользователем?"), confirm labels echo the title's verb rather than reading "OK" ("Удалить", "Перезапустить", "Повторить", "Войти"), and the default cancel is "Отмена" (`modal.html:693`). Generic-label greps find no "OK"/"Submit"/"Готово" in the confirm slot of any of the 10 consumers.

Deductions: finding 4 above (two consumers pass an identifier where every other passes a consequence). And `htmx_error_banner.html:213` — "Действие не выполнено. Попробуйте ещё раз через минуту." — states a wait duration the client cannot know and names no action, while its sibling at `:214` is a 180-character three-sentence paragraph. The pair is neither consistent in length nor in specificity.

### Pillar 2: Visuals (2/4)
Focal structure inside the panel is sound: overlay at `rgba(8,8,11,.72)` with `backdrop-filter: blur(6px)` (app.css:1199-1202), panel `min(420px, 100%)` with a `rise .2s` entry animation, actions right-aligned with `flex-wrap: wrap` (app.css:1216) so the two buttons survive a narrow viewport. No icon-only controls were introduced — every trigger is a labelled `<button>`/form submit.

The score is held at 2 by finding 2 (banner superimposition is guaranteed by the declarations, not merely possible) plus the unverifiable interaction of `z-70` banner with the `z-60` centred panel on short viewports — the panel is `place-items: center` inside 20px padding, so on a short viewport its top edge can reach the banner's 12px band. Whether it does is a rectangle, and rectangles are owed to a human.

### Pillar 3: Color (3/4)
Accent use is disciplined: every semantic colour routes through tokens with `color-mix(in oklab, …)` (app.css:849-852), and surfaces use `var(--surface)`, `var(--border)`, `var(--danger)`. Grep of the two phase templates for `#hex`/`rgb(` returns zero — no hardcoded colour entered the markup.

Deduction: `rgba(8, 8, 11, …)` appears 4 times in app.css as raw literals, two of them in this phase's own surface (panel shadow app.css:1207, overlay app.css:1201) and one in the banner shadow (app.css:1197) — the same near-black expressed three times instead of once as a token. Additionally, `.alert--error` sets `color: var(--danger)` on a 10%-danger tint, and the banner then re-parents it onto `background: var(--surface)` (app.css:1194) — a background swap that no contrast measurement in this phase covers.

### Pillar 4: Typography (3/4)
The new surface uses exactly two sizes and two weights: `--fs-xl` (15px) / weight 600 for `.modal__title` (app.css:1213), `--fs-md` (13px) / normal for `.modal__text` (app.css:1215) and `.alert` (app.css:846). That is well inside the ≤4 sizes / ≤2 weights bar, and `letter-spacing: -.015em` on the title is consistent with `.brand-name` house style.

Deduction: 15px over 13px is a 1.15× step. For the single most important line in a destructive-confirmation dialog that is the weakest hierarchy the house ramp can express, when `--fs-2xl` (16px) and `--fs-h1` (22px) are both available and unused here. On a 13px body the title reads as emphasised body text, not as a heading.

### Pillar 5: Spacing (2/4)
There is **no spacing scale in this project** — `grep -- '--space'` over app.css returns nothing; only `--r-*` (radius) and `--fs-*` (size) tokens exist. Every spacing value is a literal. This phase added: `.modal { padding: 20px }` (app.css:943), `.modal__panel { gap: 14px; padding: 22px }` (app.css:1205-1206), `.modal__form { gap: 14px }` (app.css:1214), `.modal__actions { gap: 9px }` (app.css:1216), banner `top: 12px` + `calc(100% - 24px)` (app.css:1190-1193), `.alert { padding: 11px 14px }` (app.css:845).

That is 20 / 22 / 14 / 12 / 11 / 9 px inside one component — six values from no system, where 22 and 20 differ by 2px for no expressed reason and the action-row gap (9) is unique in the file. The component is internally readable but contributes six more un-tokenised literals to a codebase that already cannot answer "what is one unit of space here". Score 2 reflects the absence of any scale to audit against plus the phase's net addition to the problem, not a claim that any single value is wrong.

### Pillar 6: Experience Design (2/4)
What is present and correct: busy state (`x-bind:disabled="sending"`, `x-bind:aria-busy="sending"`, `hx-disabled-elt`, `hx-indicator="find .form-busy"` — `modal.html:807,810,813`), double-submit guard on `x-on:submit` (`:806`), `x-cloak` to prevent flash, Escape and overlay-click close both gated by `if (sending) return` (`:713,716`), a real focus trap (`x-on:keydown.tab.prevent="trap($event)"`, `:714`), initial focus deliberately on Cancel so Enter cannot confirm a delete (`:717` panel + `x-ref="cancel"`), body scroll lock via `is-modal-open` (app.css:961-964), and a `destroy()` path so out-of-band panel removal also releases the lock. That is a genuinely careful destructive-confirmation flow.

What holds the score at 2: finding 1 (no dismiss; clears only on a subsequent *successful* request — a stuck full-width overlay is a task-blocking outcome, not a cosmetic one), finding 2 (one of two recovery messages is unreadable when both fire), finding 3 (no reliable announcement to assistive tech for the failure path specifically — the success/notice path got this right in the same phase), finding 5 (a swap-less 422 produces no user-visible response at all), and finding 7 (documented focus loss to `<body>` on the group-delete htmx path).

Note on scope: the phase's single open gap (`CR-01`, exception paths of `compute_next_run_at`) is a backend defect and is deliberately NOT counted against any pillar here.

---

## Registry Safety
Skipped — `components.json` is absent; this is a Jinja2/Alpine/htmx surface with no shadcn registry. No registry section applies.

---

## Files Audited
- `app/templates/components/modal.html` (818 lines; markup at 693-818)
- `app/templates/components/alert.html`
- `app/templates/includes/htmx_error_banner.html` (235 lines; markup/script at 213-235)
- `app/templates/includes/notice_area.html` (135-136)
- `app/static/css/app.css` (844-852, 941-964, 1170-1216, 2016-2023)
- `app/templates/ads/partials/sched_delete_response.html`
- `app/templates/ads/form.html`, `app/templates/accounts/list.html`, `app/templates/accounts/partial_cards.html`, `app/templates/accounts/partials/sync_status_card.html`, `app/templates/account_groups/includes/group_row.html`, `app/templates/ads/includes/sched_card.html`, `app/templates/ads/includes/ad_card.html`, `app/templates/admin/user_detail.html`, `app/templates/admin/workers.html`, `app/templates/admin/queue.html`, `app/templates/admin/includes/queue_row.html`, `app/templates/admin/includes/worker_row.html`, `app/templates/history/includes/history_card.html`
- Planning inputs: `10-VERIFICATION.md`, `10-UAT.md`, `10-REVIEW.md`, all 54 `10-NN-PLAN.md` frontmatter blocks

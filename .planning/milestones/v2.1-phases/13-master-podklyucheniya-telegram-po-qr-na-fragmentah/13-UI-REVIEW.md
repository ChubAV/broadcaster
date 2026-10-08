# Phase 13 — UI Review

**Audited:** 2026-09-21
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for this phase). Comparison points are the pre-phase template (`git show f21a6316:app/templates/accounts/connect_tg_user.html`) and the MAX wizard (`accounts/includes/max_connect_step.html`).
**Screenshots:** not captured. No dev server answered on 8000/3000/5173/8080, and the live CDP browser was not driven (`workflow.live_dom_uat: false`, no owner consent this session).
**Method:** code-only. All six step branches were rendered through `_tg_step_markup` (`uv run python`), and the rendered DOM was checked against the `app/static/css/app.css` rules that apply to it. Items marked **needs_human_review** are inferred from CSS and markup, not seen on screen. They are not scored as confirmed defects.

**Not findings (locked decisions):** no auto-redirect after «Подключено» (D-07); password errors shown at the field with 422 (D-08); refusal texts moved verbatim, including «Ошибка авторизации», «Ошибка запуска QR авторизации: {e}» and «Введите пароль» (D-09); no automatic refresh of an expired code (D-02); the wizard is JS-only (D-11). Criterion 4 (live Telethon scan, code expiry, 2FA) is still a pending human UAT, and this review does not claim it.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | The phone-path hint («Настройки → Устройства → Подключить устройство») appears only before the QR exists. It is missing on the step where the user actually scans. |
| 2. Visuals | 3/4 | The QR is a clear focal point, but the `qr_expired` card collapses to a single line and the steps have no progress cue. |
| 3. Color | 3/4 | Token-clean with one accent per step, but the «код истёк» state carries no status color while «Подключено» does. |
| 4. Typography | 3/4 | Every state message and every instruction share one style (`connect-step__text`, 13px, secondary). «QR-код истёк» reads the same as helper copy. |
| 5. Spacing | 2/4 | Wrapping steps in `form_wrapper` broke three layouts: 0px between the 2FA field and its button, left-aligned actions under centered text on `qr_expired`, and a doubled gap on `waiting`. |
| 6. Experience Design | 3/4 | State coverage is complete and failures surface through the global banners. Start/refresh lost the «Загрузка...» label, and step changes driven by polling are not announced. |

**Overall: 17/24**

---

## Top 3 Priority Fixes

1. **WARNING — 2FA step: the password field and «Подтвердить» touch (0px gap).** The step asks the user for a secret, and its form looks broken. This is a regression: before the phase, both elements were direct children of the 14px-gap `.connect-step` column. **Fix:** inside the `form_wrapper` call at `tg_connect_step.html:102-110`, wrap the field and the actions in `<div class="connect-step__form">…</div>`, the same way `max_connect_step.html:64-69` does. That class already declares `flex-direction: column; gap: 14px` (`app.css:1934`).
2. **WARNING — `qr_expired`: «Обновить QR-код» / «Отмена» are left-aligned under centered text.** The one action on this step looks detached from its message. This is a regression: before the phase, the actions row sat directly in the centered column. **Fix:** add `.connect-step--center .connect-step__actions { justify-content: center; }` to `app.css` near line 1933. As a general rule, this also protects any future centered step that nests its actions inside a form.
3. **WARNING — «Начать подключение» / «Обновить QR-код» lost their loading label.** Telethon connect plus token export takes seconds. The only feedback now is a disabled button and an 8px `--text-muted` dot. The dot appears after 300ms at the form's bottom-right corner (`app.css:2193-2210`), which in the start and error branches is the far edge of the card, away from the button. Before the phase, the label changed to «Загрузка...». **Fix:** add a step-local busy text that htmx shows during the request, e.g. `<span class="connect-step__busy">Получаем QR-код…</span>` next to the button, shown by `.form-wrapper.htmx-request .connect-step__busy`. Alternatively, pass `hx-indicator` to a visible inline element for these two forms. This needs no new JS.

Further recommendations, ranked below the top three: see Pillar 6 (live-region announcement, focus on the password step, no «Отмена» on the password step, dead-end retry for «API не настроен») and Pillar 5 (the doubled gap on `waiting`).

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING — the scanning instruction is on the wrong step.** `tg_connect_step.html:125-128` puts «Отсканируйте его в приложении Telegram (Настройки → Устройства → Подключить устройство)» in the start/error branch only. The `waiting` branch (`:48-66`) shows the QR with just «Ожидание сканирования...» (`:52`). So the user must remember the phone path from the previous screen at the exact moment they need it. This predates the phase (the old `#qr-section` had the same text), but the phase rewrote this branch and carried the gap forward. **Fix:** in the waiting branch, above or below the QR, add «Откройте Telegram → Настройки → Устройства → Подключить устройство и наведите камеру на код».
- **Minor — «Начать заново» is a dead end for a configuration refusal.** `TG_API_NOT_CONFIGURED_MESSAGE` («…Обратитесь к администратору.», `accounts.py:233`) renders the error branch, whose only primary action is «Начать заново» (`:131`), and that repeats the same refusal. The text itself is bound by D-09. The action next to it is not. Consider hiding the retry button when the error is non-retryable.
- **Minor — two near-synonyms for one concept.** «Сессия подключения не найдена» (`:239`, new) and «Сессия авторизации истекла» (`:235`, carried) name the same thing differently. The distinction is deliberate (owner-expired vs unknown/foreign, D-04), but the user-facing noun could be shared.
- **Positive:** the new copy is specific and actionable. «QR-код истёк. Обновите его, чтобы продолжить.» (`:77`) and «Обновить QR-код» (`:81`) name the state and the way out. The start button label switches correctly between «Начать подключение» and «Начать заново» (`:131`). No generic «Submit/OK» labels.

### Pillar 2: Visuals (3/4)

- **Positive:** the waiting step has a strong focal point: a 256px QR on an inset `connect-qr` tile (`app.css:1938-1943`), centered. Icon-only controls: none. The QR `alt="QR-код"` is present.
- **WARNING (needs_human_review) — `qr_expired` collapses the card.** The dead QR is deliberately removed (`:70-76`, a sound reason), but nothing replaces it. The card shrinks from about 330px (QR + text + actions) to one line of text plus buttons, so the layout jumps under the user's eyes. Consider a fixed-size placeholder tile in the QR slot (e.g. a `connect-qr` box with the «код истёк» message inside) so the geometry stays stable.
- **Minor — no step orientation.** None of the six branches has a card title or «шаг N из M» cue (`card_open()` is called without `title`, `:46`). The MAX wizard is the same, so this is consistent, but a three-stage flow (code → scan → optionally 2FA) would benefit from one.
- **Minor — stale CSS.** The comment at `app.css:1925-1927` («на экране Telegram шаги переключаются скриптом через hidden») and the rule `.connect-step[hidden]` (`:1929`) describe the removed script. No template in the phase emits `hidden` on a step anymore.

### Pillar 3: Color (3/4)

- **Positive:** no hardcoded colors in either template (grep for `#hex`, `rgb(`, `style=` returns 0). Everything goes through macros and tokens. Accent discipline is good, with exactly one primary control per step: start/error «Начать подключение|Начать заново», `qr_expired` «Обновить QR-код», password «Подтвердить», connected «К аккаунтам». `waiting` has only the ghost «Отмена», which correctly leaves the QR as the focal point. Body text `--text-secondary #8a8a98` on `--surface #0e0e14` is about 5.6:1 and passes AA.
- **WARNING — states are color-coded unevenly.** Success is a `badge('Подключено','success')` (`:116`), and errors are `alert` with `alert--error` (`:44`). The `qr_expired` state, which the phase itself describes as "not an error but a step" (D-03), gets no status treatment and is plain secondary text (`:77`). A `badge('Код истёк','warning')` or `alert(..., 'warning')` would make it glanceable and put it in the same visual language as its siblings.

### Pillar 4: Typography (3/4)

- **Distribution:** within the phase surface, one text style (`connect-step__text`, `--fs-md` 13px, `--text-secondary`) plus the component styles (button label, field label, field error `--fs-sm`, badge). There are no ad-hoc sizes or weights, so it is well within limits.
- **WARNING — no hierarchy between state and instruction.** The message that tells the user what happened («QR-код истёк…», `:77`; «Ожидание сканирования...», `:52`; «Telegram аккаунт успешно подключён.», `:117`) uses the same 13px secondary style as the helper instruction (`:125-128`, `:89-91`). On `qr_expired` the only text on the card is secondary-colored. Consider giving the state line primary text color or a `card__title`.
- **Nit:** «Ожидание сканирования...» uses three periods rather than «…» (carried, and matches MAX `:83`, so the two wizards are consistent).

### Pillar 5: Spacing (2/4)

The phase moved every actionable step into `form_wrapper`, which prints `<form class="form-wrapper">`. The only rule on that form is `position: relative` (`app.css:2207`), so it is a plain block box. The flex `gap: 14px` of `.connect-step` (`:1928`) therefore no longer reaches the children that used to sit directly in the column. The rendered DOM of each branch was checked. There are three effects. All three were measured from the DOM and CSS, and all three need a visual confirmation (**needs_human_review**).

- **WARNING — password step, 0px between field and button.** Rendered: `form.form-wrapper > [input hidden, label.field, div.connect-step__actions]`. `.field` has no margin (`app.css:731`), and there is no sibling or `margin-top` rule for `.connect-step__actions` (grep across `app.css`). Before the phase, the field and the actions were flex children at 14px. MAX avoids this with `.connect-step__form` (`max_connect_step.html:65`), and so does the codebase's own note at `app.css:2364` (listing `.connect-step__form` among the "формы-колонки"). → Fix 1.
- **WARNING — `qr_expired`, actions misaligned.** `.connect-step--center` centers its flex items (`:1930`), but `.connect-step > form { align-self: stretch }` (`:1931`) makes the form full-width. The `.connect-step__actions` flex row inside it has no `justify-content`, so «Обновить QR-код / Отмена» sit at the left edge under centered text. Before the phase, the same row was a direct child of the centered column. → Fix 2.
- **Minor — `waiting`, gap doubled to about 28px.** The poller form (`:59-62`) contains only a hidden input and an absolutely positioned `.form-busy`, so it is a 0-height flex item. The column still applies `gap` on both sides of it, so the space between «Ожидание сканирования...» and «Отмена» becomes 14+0+14px. **Fix:** move the poller form after the actions row. It then becomes the last flex item, and the column adds no gap after it. `display: contents` on the poller would also work, but the codebase has already rejected it for a11y reasons (`app.css:2355-2358`).
- **Positive:** no arbitrary pixel values in the templates. The outer rhythm (alert → card, 14px from `.connect-shell`, `:1946`) is preserved, because the anchor is the shell itself (`connect_tg_user.html:24`), matching MAX.

### Pillar 6: Experience Design (3/4)

**State coverage (measured):** all six branches exist and are reachable (`start`, `waiting`, `qr_expired`, `password`, `connected`, `error`; the POLLING_CASES registry has 20 rows, per 13-05-SUMMARY). The poll in the waiting state answers 204 with no swap (`accounts.py:374-382`; `htmx_config.html:160` `{"code":"204","swap":false}`). Every non-waiting answer removes the poller, so polling stops by the response. Double-submit is covered by `hx-disabled-elt` on the three buttoned forms, and on the server by `pop` in `complete_auth`. Network and 5xx failures on any request, including the silent poll, raise the global banners (`htmx_error_banner.html:305-321`). The banners clear on the next successful poll. That is an improvement over the old script, which swallowed poll failures (`catch (e) { // Network error — keep trying }`). The 422 password path keeps the field empty and shows the error at the field with `aria-invalid="true"` (verified in the rendered fragment).

- **WARNING — loading feedback regressed on start and refresh.** → Fix 3. The old script set «Загрузка...» on the button. Now the only cues are the disabled state and a muted 8px dot that appears after 300ms at the form's bottom-right. In the start and error branches the form spans the card width (`app.css:1931`), so the dot sits at the far right, away from the left-aligned button (**needs_human_review** for how noticeable it is live).
- **WARNING — state changes driven by polling are silent to assistive tech.** `#tg-connect-step` (`connect_tg_user.html:24`) has no `aria-live`. Transitions that happen without user action (waiting → «Подключено», → password, → «QR-код истёк») are not announced. Only the error alerts are, via `role="alert"`. **Fix:** `aria-live="polite"` on the anchor. It is a permanent element, so it survives every `innerHTML` swap and announces the new step text. MAX has the same gap.
- **WARNING — the password step does not take focus.** When polling swaps in the password step, focus stays wherever it was, and the user must find and click the field. **Fix:** in the `field()` call at `:104`, add `autofocus` (the macro needs an `autofocus` param); htmx 2 honors `autofocus` in swapped content. **needs_human_review:** the comment at `:97-98` says the stable `id="password"` returns focus after a 422 swap. htmx restores focus only if the element had it before the swap, so that holds for Enter-key submission but not for a mouse click on «Подтвердить».
- **Minor — no «Отмена» on the password step.** Every other step with an action pairs it with `link_button('Отмена','/accounts','ghost')` (`:64`, `:82`, `:132`), but the password step does not (`:107-109`). The header «К аккаунтам» (`connect_tg_user.html:7`) is still an exit, so this is an inconsistency, not a trap. It also predates the phase.
- **Minor — `autocomplete='off'` on a password field** (`:105`, carried). Browsers ignore it for passwords, and it blocks nothing useful. `current-password` would let a password manager fill the Telegram cloud password.
- **Carried, not scored:** «Ошибка запуска QR авторизации: {e}» shows the raw exception text to the user (`accounts.py:340`). The CONTEXT landmines record it as moved verbatim and outside this phase. It is listed here so it is not lost.

**needs_human_review (live look only, not scored as defects):** the three spacing effects in Pillar 5; how visible the busy dot is during a slow start; the card-height jump on `qr_expired`; focus after a click-submitted 422; screen-reader behavior across swaps; and all of criterion 4 (real scan, about 30s token expiry → «Обновить QR-код», 2FA), which is a pending human UAT.

---

## Registry Safety

Skipped: there is no UI-SPEC.md, so no third-party registries are declared.

---

## Files Audited

- `app/templates/accounts/connect_tg_user.html` (full)
- `app/templates/accounts/includes/tg_connect_step.html` (full; all six branches rendered via `_tg_step_markup`)
- `app/pages/accounts.py:211-600` (page, `TG_*_MESSAGE` constants, `_tg_step_markup`, start-qr / qr-status / refresh-qr / verify-2fa)
- `app/templates/accounts/includes/max_connect_step.html`, `app/templates/accounts/connect_max.html` (analog)
- `app/templates/components/form_wrapper.html`, `button.html`, `alert.html`, `badge.html`, `field.html`, `card.html`
- `app/templates/includes/htmx_config.html` (responseHandling), `app/templates/includes/htmx_error_banner.html`
- `app/static/css/app.css` (`.connect-*` 1925-1946, `.field` 731-754, `.form-busy`/`.form-wrapper` 2193-2210, tokens)
- Pre-phase baseline: `git show f21a6316:app/templates/accounts/connect_tg_user.html`
- `.planning/phases/13-…/13-CONTEXT.md`, `13-01…13-06-SUMMARY.md` (frontmatter and decisions)

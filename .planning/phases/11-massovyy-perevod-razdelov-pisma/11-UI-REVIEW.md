# Phase 11 — UI Review

**Audited:** 2026-09-17
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for this phase); the phase's own contract (11-CONTEXT D-01…D-16, plan must_haves) used where it names visible behaviour
**Screenshots:** not captured. No dev server was reachable on 3000/5173/8080/8000, and the task did not allow starting one on a host with a live production deployment. This is a code-only audit. Nothing below is a browser observation. Where a finding depends on runtime behaviour, it cites the vendored `app/static/js/htmx.min.js` or the CSS rule it rests on.

**Scope measured:** `git diff c1d1086a..HEAD -- app/templates app/static app/pages/notices.py` has 28 files, +946/−193. These are the schedule card and list, the ad editor list container, profile settings, the admin user card, the MAX wizard step, account sync forms, the billing CTA, the queue notices, the modal text id, and the 422 config rule.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Moved texts are verbatim and specific, but the MAX failure still shows a raw exception (`Ошибка подключения к MAX: {e}`), and the owner-accepted 403 path shows wrong advice |
| 2. Visuals | 2/4 | Both new 422s show the field error as a detached banner (`alert(error)`), not with the field's own error state. The MAX failure fragment shows an error next to an endless «Ожидание QR-кода...» poll |
| 3. Color | 4/4 | No new colour tokens, hex or rgb values, or inline styles. Moved notices keep their variants character for character |
| 4. Typography | 4/4 | No new font sizes or weights. All new markup goes through existing `button`/`field`/`alert`/`mono`/`badge` macros |
| 5. Spacing | 2/4 | The hidden `.form-busy` dot is inline-block after a flex column. That adds an empty line box under «Сохранить» and «Продолжить» and ~12px of trailing space after each wrapped button. The profile alert now touches the form with 0px gap |
| 6. Experience Design | 2/4 | On schedule edit, `hx-disabled-elt` disables the wrong button («ВЫБРАТЬ ВСЕ»/«БУДНИ», not «СОХРАНИТЬ РАСПИСАНИЕ»). Focus is lost on every swap whose trigger has no `id`. The MAX error state is a dead end |

**Overall: 17/24**

---

## Top 3 Priority Fixes

1. **The busy-indicator span adds vertical space and uneven horizontal gaps.** `components/form_wrapper.html` always prints `<span class="form-busy">` as the last child of `<form>`. `.form-busy` is `display:inline-block; visibility:hidden` (`app.css:2154`), so it keeps its layout box while invisible. `includes/profile_settings.html` and `accounts/includes/max_connect_step.html` put the fields in a flex `<div data-form>` / `<div class="connect-step__form">`, so the span starts a new anonymous line box under the button. That is the extra space the owner suspected under «Продолжить», and the same thing happens under «Сохранить» in the profile. In flex action rows (`[data-actions]` gap 9px, `.acct-card__actions`, `.sched-card__head > form`), each wrapped form gets a whitespace node plus 8px after its button. Those rows then have uneven gaps next to the plain `<form>` triggers («Войти под пользователем», «Удалить»).
   - **User impact:** a visible empty band at the bottom of the profile card and the MAX card, and uneven spacing between action buttons on the admin user card and account cards.
   - **Fix:** take the indicator out of flow. Add `position: relative` to forms printed by the macro (give the macro's `<form>` a class such as `form-htmx`) and `.form-htmx > .form-busy { position: absolute; inset-inline-end: -14px; top: 50%; margin-top: -4px; }`. Also remove the whitespace before the span in the macro (`{%- if caller is defined %}{{ caller() }}{% endif -%}<span …>`). Re-run `test_the_indicator_class_is_self_sufficient`.

2. **Field errors on the two new 422s are banners, not field errors.** `includes/profile_settings.html` renders `{% if error %}{{ alert(error) }}{% endif %}` above the form, and `select_field(... )` gets no `error=`. `max_connect_step.html` renders the «Введите номер телефона» alert above the card, outside it and away from the phone input, and `field(name="phone", …)` gets no `error=`. Yet `components/field.html` already supports `error=`: `field--invalid`, `aria-invalid="true"`, `.field__error`. The phase claims «ошибка поля рисуется у формы» (D-12 Фазы 8, FORM-08), but that is only half true.
   - **User impact:** in the MAX wizard the error sits above the card, away from the input. Neither input is marked invalid for assistive technology. In the profile the alert touches the select label with no gap (see Spacing).
   - **Fix:** pass the field error to the field. Use `select_field(name="timezone", …, selected=selected, error=error, id='timezone')` in `profile_settings.html`. In `max_connect_step.html`, use `field(name="phone", …, value=phone or '', error=(error if step == 'phone' else none), …)`. Keep the `alert()` only for non-field errors, such as the bridge failure on the `qr` step.

3. **The schedule edit form disables the wrong button and drops focus on every swap.** The edit form is `form_wrapper(action=…/edit, target='#sched-N', swap='outerHTML')` with the default `disabled_elt='find button[type=submit]'`. In the vendored htmx 2.0.10, `find` resolves with `querySelector` (first match: `f(e,t){…return e.querySelector(t)}`). The first submit button in that form is «ВЫБРАТЬ ВСЕ» (`groups_preset`) or «БУДНИ» (`days_preset`), which is always rendered. «СОХРАНИТЬ РАСПИСАНИЕ» is last (`sched_card.html` around line 302), so it stays enabled during the request and a preset button greys out instead. On top of that, the `outerHTML` swap replaces the pressed button. htmx only restores focus to an element with an `id`, and none of `button()`'s output has one. So after «БУДНИ», «+ ВРЕМЯ», «×» or «СОХРАНИТЬ РАСПИСАНИЕ», focus goes to `<body>`.
   - **User impact:** a double click on save sends two requests. A preset button flickers disabled for no visible reason. Keyboard users are thrown back to the top of the tab order after every edit step in a form that needs several presses.
   - **Fix:** pass `disabled_elt='find button[name=save_schedule]'` so the button the user actually pressed to save is the one that greys out (`find` only ever resolves one element, so a comma list would not widen it). Give the save button a stable id (`sched-save-{{ s.id }}`, via a new `id=` parameter on `components/button.html`) so htmx restores focus after the swap. Apply the same id treatment to the admin toggle buttons (`#user-actions` innerHTML swap) and the profile «Сохранить».

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**Passing evidence**
- The queue-drop outcomes moved into the registry verbatim (`app/pages/notices.py`). Each one says what happened and why: «Задача снята из очереди», «Задача уже ушла из очереди — снимать нечего», «Не удалось снять задачу: Redis не отвечает, а очередь хранится только в нём», «Снимать нечего: у этого аккаунта нет своей очереди задач». None of them is a generic «OK»/«Ошибка».
- The field-error strings are specific and dictated to the field: «Неверный часовой пояс» (`app/pages/profile.py:25`) and «Введите номер телефона» (`app/pages/accounts.py:542`).
- The state-bearing toggle labels read as actions on the new state: «Выдать/Снять бесплатный доступ», «Заблокировать/Разблокировать» (`admin/includes/user_actions.html`). The first-schedule CTA changes «+ ДОБАВИТЬ ПЕРВОЕ» to «+ РАСПИСАНИЕ» through a transition, as D-05 specifies.

**WARNING: raw exception text reaches the user** (`app/pages/accounts.py:675`). `error = f"Ошибка подключения к MAX: {e}"` interpolates the Python exception message into the fragment. This existed before the phase (introduced at `ba63893`), but plan 11-18 moved it verbatim into the new fragment body instead of fixing it. Users see driver or bridge text such as connection-refused strings, and internal detail may leak. Fix: log `e` and show a fixed message, for example «Не удалось подключиться к MAX. Проверьте номер и попробуйте ещё раз.»

**WARNING (owner-accepted, D-08): wrong advice on origin refusal.** A bare `Response(status_code=403)` on `admin_toggle_block`, `admin_toggle_free_access` and `subscribe_to_plan` raises the generic banner «Действие не выполнено. Попробуйте ещё раз через минуту.» (`includes/htmx_error_banner.html:300`). Retrying will not help. The owner accepted this as unreachable from the UI. It is recorded here because this pillar measures what a user would read, not whether it is reachable.

**WARNING: the same generic banner covers the new malformed-request 400** (plan 11-07, `malformed_request_response`). It is accepted as T-11-14, but it is the same wrong advice.

**Minor: inconsistent final punctuation in the registry.** «Настройки сохранены.» ends with a period. The neighbouring moved texts don't («Задача снята из очереди», «Не удалось начать оплату — попробуйте ещё раз через минуту»). The SCHEDULE_* texts use full sentences with periods. Pick one rule for one-clause notices.

**Minor: «Применить»** (`sched_card.html`, `schedule_row.html`) is a generic label. It only shows in the Alpine-alive/htmx-dead world, so its impact is low. «Сохранить состояние» would say what the button does.

### Pillar 2: Visuals (2/4)

**WARNING: the 422 error is not shown in the field's error state** (see Top fix 2). Both 422 fragments render `alert(error)`. The field components' built-in invalid state (`field--invalid`, `.field__error`, `aria-invalid`) goes unused on both screens this phase introduced a field error for. In the MAX wizard, the alert is a sibling of the card inside `.connect-shell` (`max_connect_step.html:169`), so the error sits above the card rather than next to the phone input.

**WARNING: the MAX failure state contradicts itself** (`accounts.py` `_step` renders `step="qr", qr_code=None, error=error`, then `max_connect_step.html:230-236`). When the bridge fails, the fragment shows the red error alert and, in the same card, «Загрузка QR-кода...» plus `#max-status` polling every 3s with «Ожидание QR-кода...». The phone form is gone, so the page offers no retry. This existed before the phase, but the phase moved it into a fragment that now replaces the step in place.

**WARNING: after creating a schedule, two cards are expanded** (`ads/partials/sched_create_response.html`, D-05). The new card arrives expanded, and a card the user had expanded earlier stays expanded until F5. On a long editor that means two tall forms open at once, and the page no longer has one clear focal card. D-05 names this as accepted, but it is a real layout state.

**WARNING: the «Применить» fallback button is in the markup of every toggle** (`sched_card.html`, `schedule_row.html`). It is removed by `x-init="if (window.htmx) $el.remove()"`. It is present until Alpine initialises: on first paint and on every toggle fragment. Whether it paints for a frame needs a browser. Note it for UAT item 5.

**Passing evidence**
- Only content is swapped. `sched_card_response.html` never carries the `sched-del-N` panel root, and the panel text is replaced by the permanent id `{{ id }}-text` (`components/modal.html`), so the Alpine-stateful panel is never duplicated in markup.
- The admin card gets its state from one source (`admin/includes/user_actions.html`, `user_block_badge.html`, `user_access_tile.html`). The empty badge wrapper gets `display: contents` (`app.css`) so non-blocked users do not get an extra 3px gap.
- `data-plan-cta` moved to the wrapper div, so `[data-plan-cta] .btn { min-height: 44px }` still reaches the payment button.

### Pillar 3: Color (4/4)

- A scan of added lines in `app/templates` and `app/static/css` found **0** hex colours, **0** `rgb(`, and **0** `style=` attributes.
- The CSS changes are selector-only: `[data-identity-meta] > #user-block-badge { display: contents; }`, and `[data-acct-head] form[data-syncing]` became `[data-acct-head] [data-syncing]` in both the animation rule and its `prefers-reduced-motion` counterpart. No colour value changed.
- The retired `?result=` channel's four variants moved unchanged (success / warning / error / warning, plan 11-14). The `error` notice still renders in `#notice-alert` (`role="alert"`), and success/warning in `#notice` (`role="status"`). Accent and danger usage stays on existing semantic components (`badge('Заблокирован','danger')`, `mono(…,'danger')` for a closed access tile).
- No deviation found. The phase is a transport conversion and did not touch the palette.

### Pillar 4: Typography (4/4)

- Added markup introduces no font-size or weight declarations. The added-line scan found 0 `font-size` rules and 0 new `px` sizes.
- All new text goes through existing macros: `button()`, `field()`/`select_field()`, `alert()`, `mono()`, `badge()`, `<span data-metric-value>`. The new partials (`sched_card_response.html`, `sched_create_response.html`, `schedule_row_response.html`, `user_actions_response.html`) include the page templates rather than copying markup, so a fragment and a full page cannot diverge typographically.
- Pre-existing, unchanged: `billing/balance.html` and `admin/includes/user_actions.html` still write raw `<button class="btn …">` instead of `button()`. This is not a phase regression; noted for consistency only.

### Pillar 5: Spacing (2/4)

**WARNING: empty line box under the button in the two column forms** (Top fix 1).
- In `profile_settings.html` the output is `<form …><div data-form>…Сохранить</div> <span class="form-busy"></span></form>`.
- In `max_connect_step.html` it is `<form …><div class="connect-step__form">…Продолжить</div> <span class="form-busy"></span></form>`.
- `<form>` has no display rule (block). `.form-busy` is `inline-block`, 8×8px, and hidden with `visibility`, not `display`. The result is an anonymous line box one inherited line-height tall under the column, between the button and the card's 18px bottom padding.
- This confirms, at code level, the owner's open question about extra space under «Продолжить». The same band exists under the profile «Сохранить».

**WARNING: uneven gaps in flex action rows.** The macro prints `{{ caller() }}` followed by a newline and two spaces before the span. That whitespace node plus the 8px inline-block trails every wrapped button.
- `[data-actions]` (`app.css:1897`, gap 9px), on the admin user card: «Выдать бесплатный доступ» and «Заблокировать» are wrapped, so each has about 9px gap plus ~12px trailing space. «Войти под пользователем» and «Удалить» are plain forms with 9px.
- `.acct-card__actions` (`list.html`, `partial_cards.html`, `sync_status_card.html`): «Повторить» (wrapped) sits next to «Удалить» (plain).
- `.sched-card__head > form` (`flex: none`): the toggle form is wider than before the phase, which pushes the expand link.

**WARNING: the profile alert has 0px gap before the form** (`includes/profile_settings.html`). Before plan 11-08, the alert was a child of `<div data-stack>` (22px gap) above the card. Now it is the first child of `<div id="profile-settings">`, a plain block inside `.card__body`. `.alert` has no margin (`app.css:844`), so the alert box touches the «Часовой пояс» label. This goes away if Top fix 2 moves the error into `select_field(error=…)`. Otherwise give `#profile-settings` the same flex column and gap as `[data-form]`.

**Passing evidence**
- `.connect-shell` keeps its 14px gap between the alert and the card. The id went on the column itself, and plan 11-18 kept the gap rather than adding a wrapper.
- `display: contents` on the badge wrapper avoids a phantom 3px flex gap.
- The phase adds no arbitrary `[..px]` or inline spacing.

### Pillar 6: Experience Design (2/4)

**Coverage of loading, error and disabled states**

| State | Coverage |
|---|---|
| Loading | Every converted form gets `hx-indicator="find .form-busy"` with a 300ms show delay. The MAX start (at least 5s) gets both the indicator and a disabled button. This replaces the removed inline `onsubmit` label swap («Подключение…»), so the visible wording of the wait is gone and only an 8px dot remains. |
| Error | 422 swaps back into the same target (`htmx_config.html`: `{"code":"422","swap":true,"error":true}`). 4xx/5xx raise the failure banner. The empty 400 for malformed htmx requests closes the T-07-13 sink. |
| Disabled | The wrapper disables the default target, but in the schedule edit form that is the wrong button (Top fix 3). Toggles use `disabled_elt=''` with `hx-sync="this:drop"` (DIV-09-02). Payment keeps indicators across `HX-Redirect`: the vendored htmx sets `keepIndicators=true` before `location.href`, so the CTA stays disabled while the browser leaves for YooKassa. |
| Destructive confirmation | Unchanged. Delete panels stay outside swap targets. The admin block toggle has no confirmation (UI contract E5, intentional). |

**WARNING: wrong disabled element on schedule edit.** See Top fix 3. In `sched_card.html`, `button('БУДНИ', … name='days_preset')` is always rendered before `button('СОХРАНИТЬ РАСПИСАНИЕ', …)`, and `find` means first match in htmx 2.0.10.

**WARNING: focus is not restored after swaps.** No `htmx:afterSwap` or `afterSettle` focus handling exists in `app/templates`. The only `.focus()` calls are in `components/modal.html`. htmx restores focus only when the focused element has an `id` that exists in the new content. Buttons from `components/button.html` have no `id`. Where focus drops:
- the schedule edit form's presets, add/remove time and save (`outerHTML`);
- admin «Заблокировать»/«Выдать бесплатный доступ» (`innerHTML` of `#user-actions`);
- profile «Сохранить» (`innerHTML` of `#profile-settings`);
- MAX «Продолжить» (`innerHTML` of `#max-connect-step`).

On a 422, focus is not moved to the invalid field. The toggles are the exception: `sched-toggle-N` and `schedule-toggle-N` carry ids, so QUAL-06 holds for them.

**WARNING: the MAX failure step is a dead end.** See Visuals. It shows an error plus a spinner that polls forever, and there is no way to try again except the page-level «К аккаунтам» link or a manual reload.

**WARNING: no visible confirmation on in-place success.** Schedule edit and toggle, and the admin toggles, return the re-rendered block and no notice (D-03 of Phase 10, REQUIREMENTS Out of Scope). For «СОХРАНИТЬ РАСПИСАНИЕ» with unchanged values, a saved result looks the same as nothing happening. The busy dot appears only after 300ms, so a fast save shows no feedback at all. This is intentional and recorded, not something to fix in this phase. Profile save is the one converted in-place action that does confirm («Настройки сохранены.» out-of-band).

**WARNING (accepted price, D-11): a filtered schedule list goes stale.** A row toggled out of an active `state=` filter stays visible in its new state, and the `total` rule is not repainted until reload (`schedule_row_response.html` header). The keyset cursor (`after_id`) does keep the next page from skipping a row, which is the more serious failure this phase fixed.

**Passing evidence**
- The first schedule («было ноль») avoids a silently dead button through a conditional target (`target=('#sched-list' if editor.schedules else none)`). Plan 11-05 measured that htmx 2.0.10 aborts on `htmx:targetError` before sending. This was a real experience fix and is tested (`test_the_create_form_targets_the_list_only_when_the_list_exists`).
- `_SYNC_IN_FLIGHT` is released on every htmx exit (plan 11-17), so the «Синхронизировать всё» button cannot become permanently no-op after one htmx request.
- The free-access tile is rendered after `invalidate_access_cache` (plan 11-13), so the admin sees the new state, not a cached one.

**Items the owner still has to check by hand (not verified here; code-level evidence only):**
- **Scroll after schedule create.** The `beforeend` insertion into `#sched-list` leaves the container in place, and the create form sits after it, so the new card appears directly above the button. The code gives no reason to expect a scroll jump. Only a browser can confirm it.
- **Alpine state after swaps.** Swap targets contain only bare `x-data` (the «Применить» span). Panels stay outside the targets, and panel text is replaced by id. Nothing in the markup duplicates panels. Listener leaks cannot be judged from code.
- **Back/F5.** No `hx-push-url` attribute appears anywhere (`grep -rn hx-push-url app/templates` returns 0). The only `HX-Push-Url` header is on draft-ad creation.
- **Extra space under «Продолжить».** Code-level evidence says yes (see Spacing, first WARNING).

---

## Registry Safety

Skipped: `components.json` is absent (no shadcn). There is no UI-SPEC registry table.

---

## Files Audited

- `app/templates/components/form_wrapper.html`, `components/modal.html`, `components/field.html`, `components/alert.html`, `components/button.html`
- `app/templates/ads/form.html`, `ads/includes/sched_card.html`, `ads/partials/sched_card_response.html`, `ads/partials/sched_create_response.html`
- `app/templates/schedules/list.html`, `schedules/partial_cards.html`, `schedules/includes/schedule_row.html`, `schedules/partials/schedule_row_response.html`
- `app/templates/profile.html`, `app/templates/includes/profile_settings.html`, `includes/htmx_config.html`, `includes/htmx_error_banner.html`, `includes/notice_area.html`
- `app/templates/admin/user_detail.html`, `admin/includes/user_actions.html`, `admin/includes/user_block_badge.html`, `admin/includes/user_access_tile.html`, `admin/partials/user_actions_response.html`, `admin/queue.html`
- `app/templates/accounts/connect_max.html`, `accounts/includes/max_connect_step.html`, `accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html`, `account_groups/list.html`
- `app/templates/billing/balance.html`
- `app/static/css/app.css` (phase diff, plus `.form-busy`, `[data-form]`, `.connect-step*`, `.connect-shell`, `[data-actions]`, `.acct-card__actions`, `.sched-card__head`, `.alert`, `.card__body`)
- `app/pages/notices.py`, `app/pages/profile.py` (copy constants), `app/pages/accounts.py` (MAX start branch, pre-phase comparison at `c1d1086a`)
- `app/static/js/htmx.min.js` (vendored 2.0.10: `find` selector resolution, `HX-Redirect` `keepIndicators`)
- Phase records: `11-CONTEXT.md`, `11-01…11-20-PLAN.md`, `11-01…11-20-SUMMARY.md`

# Phase 19 — UI Review

**Audited:** 2026-11-23
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md for this phase); phase decisions D-09, D-10, D-12 from 19-CONTEXT.md and 19-06-PLAN.md as the intended behaviour
**Screenshots:** not captured (code-only audit by orchestrator instruction; no dev server, no Playwright, no production stand)
**Interaction captures:** off (`interaction_capture: false`)

---

## Scope of phase-19 frontend changes

Derived from `git log --name-only 4ca2f7dd^..6b5ee03e -- app/templates app/pages`:

- `app/templates/accounts/includes/max_connect_step.html` — hint under the MAX phone field (19-06, commit `5d4f605a`)
- `app/pages/accounts.py` — 422 `PhoneError` path on MAX start (19-06), capture of the number on TG/WA/MAX status (19-01, 19-05, 19-07). Server-side only, no markup.

No other template changed in phase 19. The account label (`components/account_label.html`) and the accounts list were NOT touched; the "указан вручную" mark is driven by `label.phone_is_manual` (`app/services/account_label.py`), which the phase's writer never sets (D-01).

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | 422 error copy is clear and carries an example; the new field hint is a clumsy, jargon-heavy sentence that is visible before any input |
| 2. Visuals | 3/4 | Hint is placed inside the field label; step hierarchy unchanged; the success step deliberately shows no number, leaving no visual confirmation of what was captured |
| 3. Color | 4/4 | Phase adds no colour values; hint uses the existing muted token |
| 4. Typography | 4/4 | Phase adds no new sizes or weights; hint reuses `.field__hint` at `--fs-sm` |
| 5. Spacing | 3/4 | Hint reuses the field spacing, but the hint-to-button gap is not verifiable without a render; no spacing deviation found in code |
| 6. Experience Design | 2/4 | Hint is inside the `<label>` so it joins the field's accessible name and has no `aria-describedby`; MAX flow end-to-end unverified (UAT 2, 3 blocked by external server); success step gives no feedback on which number was captured |

**Overall: 19/24**

Blockers (pillar score 1 or task-breaking defect): **none found in the UI code.** The MAX walkthrough is blocked by an external WebSocket outage recorded in 19-UAT.md (tests 2 and 3), not by a markup defect.

---

## Top 3 Priority Fixes

1. **Hint joins the field's accessible name and is not programmatically linked** — screen-reader users hear the whole hint as part of the "Номер телефона" label, and the hint is not announced as a description — fix: in `components/field.html` (shared macro) render the hint as a sibling element with an id and pass `aria-describedby` from the `<input>`, or at minimum move the hint out of the `<label>` for this call site. Note: the macro is shared by all auth forms, so the change needs a regression check of the other fields.
2. **Hint copy is unclear and shown before the user has typed anything** — "Покажем его в списке аккаунтов, если MAX не сообщит номер сам" has no clear antecedent for "его" beyond the label, and "сообщит номер сам" is internal jargon for an end user — fix: at `app/templates/accounts/includes/max_connect_step.html:71` use a plain sentence such as «Если MAX не передаст номер при входе, укажем этот — он появится в списке аккаунтов». Keep the no-digits rule (D-10) and keep the example out of the hint (it belongs in the error text, as the comment at line 65–68 states).
3. **Success step gives no confirmation of the captured number** — `max_connect_step.html:30–34` shows only «Ваш аккаунт MAX готов к использованию.» and «К аккаунтам»; the user cannot tell whether the number was captured or which one (form number vs MAX-reported number) until they open the list. This follows D-12 and is a locked decision, so this is a recommendation to revisit with the owner, not a defect against the contract — fix (if the owner agrees): show the number only when it is the MAX-reported one, or add a line «Номер появится в списке аккаунтов» on the success step.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **Strength — 422 texts.** `app/services/phone.py:161–175` gives four constant texts (`PHONE_ERROR_BLANK`, `PHONE_ERROR_TOO_LONG`, `PHONE_ERROR_EXTENSION`, `PHONE_ERROR_NOT_A_NUMBER`), each ending in the example «Пример: +7 999 123-45-67». They are Russian, specific and actionable, and the typed value is never echoed into the text (D-18 Фазы 16). The old generic «Введите номер телефона» was replaced for the blank case by `PHONE_ERROR_BLANK` (`accounts.py` ~L890–930 comment; `MAX_EMPTY_PHONE_ERROR` removed).
- **Warning — hint wording.** `app/templates/accounts/includes/max_connect_step.html:71`: `hint='Покажем его в списке аккаунтов, если MAX не сообщит номер сам'`. Problems: (a) it is shown permanently, before the user types, so it reads as a pre-emptive notice rather than help; (b) "сообщит номер сам" is internal wording about the MAX protocol; (c) "его" depends on the label for its referent. Recommend the rewording in Priority Fix 2.
- **Warning — step text vs hint redundancy.** `max_connect_step.html:38` says «Введите номер телефона, привязанный к вашему аккаунту MAX» and the hint on line 71 repeats the purpose of the number. Two sentences of instruction for one field; consider keeping only the hint or only the step text.
- **Neutral — success text.** `max_connect_step.html:32` «Ваш аккаунт MAX готов к использованию.» is consistent with the WhatsApp success text (`accounts/connect_wa.html:22`: «Ваш аккаунт WhatsApp готов к использованию.»). Consistent.

### Pillar 2: Visuals (3/4)

- **Hierarchy unchanged.** The phone step keeps the same structure as before phase 19: one `.connect-step__text` paragraph, one field with a hint, one primary button (`max_connect_step.html:37–75`). No new focal competition.
- **Error placement is intentional.** `max_connect_step.html:26` renders the alert outside the card, as documented at lines 11–16 (flex gap of `.connect-shell`). Preserved; not a finding.
- **Warning — no visual confirmation of captured number.** `max_connect_step.html:30–34` (`connected` branch) omits the number by design (D-12). Combined with the list-side mark rules (no «указан вручную» for captured numbers, enforced by the writer per D-01), the user has no on-screen proof of the capture at connect time. See Priority Fix 3.

### Pillar 3: Color (4/4)

- No colour values or new colour classes in the phase diff. The hint uses the existing `.field__hint { color: var(--text-muted) }` (`app/static/css/app.css:774`) — the same token as all other field hints in the app.
- The "указан вручную" mark (`components/account_label.html:40`, `.acct-label__manual`) is not used for captured numbers: `capture_connect_phone` and `record_reported_phone` never set the manual flag (`accounts.py` `_save_tg_account` docstring; 19-UAT test 4 owner report «пометок нет»). Correct per D-01/D-12.
- Accent usage on the phase screens: unchanged (one primary button per step).

### Pillar 4: Typography (4/4)

- Hint: `.field__hint { font-size: var(--fs-sm) }` (`app.css:774`); step text: `.connect-step__text { font-size: var(--fs-md) }` (`app.css:2030`). Two sizes, both existing tokens. No new weights.
- Neighbouring steps (`accounts/connect_wa.html`, `accounts/includes/tg_connect_step.html`) use the same `connect-step__text` class, so the phone step is consistent with them.

### Pillar 5: Spacing (3/4)

- The hint is rendered inside the `<label class="field">` by the shared macro (`components/field.html:14–33`), so it inherits the field's existing spacing. No arbitrary spacing values were introduced by phase 19.
- Not verified: the vertical gap between the hint and the «Продолжить» button (`max_connect_step.html:70–72`, `.connect-step__form`). Without a render this cannot be confirmed; scored 3 for that reason, not for a found defect.

### Pillar 6: Experience Design (2/4)

- **Warning — hint inside label (accessibility).** `components/field.html:14` opens the `<label>` and `field.html:31` renders the hint inside it. The accessible name of the input becomes "Номер телефона Покажем его в списке…". There is no `aria-describedby` linking the hint, and the error at `field.html:32` has the same issue (it is also inside the label and not linked with `aria-describedby`; `aria-invalid` is set at `field.html:26`, which is good).
- **Warning — no error focus management.** On a 422 the alert at `max_connect_step.html:26` is `role="alert"` (`components/alert.html:10`), which is announced, but focus is not moved to the field or the alert. Acceptable for htmx swap, but worth a check.
- **Warning — success step gives no feedback on the captured number.** See Priority Fix 3 (D-12 locked; recommendation to revisit).
- **Positive — no number leak.** The phone value is echoed only through the autoescaped field macro (`max_connect_step.html:69–71`, comment at 62–63), never in the page title or in data attributes (T-06-02). Phone is not logged (`logger.info("tg_phone_captured", account_id=..., outcome=...)` in `accounts.py` `_save_tg_account`).
- **Positive — the 422 path is covered.** Blank, invalid, too long and extension inputs answer 422 on both transports with the constant error text (19-06 SUMMARY, D2; test `test_max_connect_transport.py`).
- **Blocked verification — MAX end-to-end.** `19-UAT.md` tests 2 and 3 are `blocked_by: server`: the MAX WebSocket (`wss://ws-api.oneme.ru/websocket`) did not open from the stand, so the QR step and the A-vs-B number outcome were never observed. The MAX UI path is therefore only code-verified for this phase. Test 5 (no «указан вручную» and no number on the MAX success step) is also pending for the MAX half.
- **Consistency — WA/TG.** WhatsApp connected flow (owner test 4) passed: number shown in list, no mark, groups synced (19-UAT.md test 4, `result: pass`).

---

## Registry Safety

Not applicable: no `components.json` audit scope for this phase; no third-party UI registry used.

---

## Files Audited

- `/source/broadcaster/app/templates/accounts/includes/max_connect_step.html`
- `/source/broadcaster/app/templates/components/field.html`
- `/source/broadcaster/app/templates/components/alert.html`
- `/source/broadcaster/app/templates/components/account_label.html`
- `/source/broadcaster/app/templates/accounts/connect_wa.html` (neighbour, consistency)
- `/source/broadcaster/app/templates/accounts/includes/tg_connect_step.html` (neighbour, consistency)
- `/source/broadcaster/app/pages/accounts.py` (phase-19 hunks: `_save_tg_account`, `accounts_connect_max_start`, WA and MAX status handlers)
- `/source/broadcaster/app/services/phone.py` (PhoneError copy, lines 156–175)
- `/source/broadcaster/app/services/account_label.py` (manual-flag source)
- `/source/broadcaster/app/static/css/app.css` (lines 774, 2028–2036)
- `/source/broadcaster/.planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-UAT.md` (evidence only)
- `/source/broadcaster/.planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-06-SUMMARY.md`

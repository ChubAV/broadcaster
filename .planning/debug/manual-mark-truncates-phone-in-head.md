---
status: diagnosed
trigger: "manual-mark-truncates-phone-in-head — На 320 и 375 px шапка экрана групп аккаунта с ручным номером должна показывать номер целиком — усекаться должна пометка «указан вручную», а не номер; шапка с формой не должна ломать раскладку."
created: 2026-11-21T00:00:00Z
updated: 2026-11-21T19:40:00Z
---

## Current Focus

bug_class: Bohrbug (deterministic CSS layout: the same width always gives the same px values, reproduced to 0.003 px)
hypothesis: CONFIRMED (H1). `flex-shrink` is a proportional weight, not a priority. Inside `.acct-head__name > .acct-label` and `.chip__label > .acct-label` (inline-flex), chan, number and mark all have `min-width: 0`. The negative free space is therefore split by flex-shrink x flex-basis (chan 1x69, number 1x116, mark 4x124 in the h2), and the number absorbs ~17% of ANY deficit, while the mark still has width. CONFIRMED separately (H2): the 320 px `.acct-head__actions` overflow is a pre-existing Phase 3 defect (`flex: none` defeats its own `flex-wrap`). It is identical at master 41e2396f and was not worsened by Phase 18.
test: done — real pages rendered via the test client and measured in the UAT's own Chrome 157 (CDP, fresh about:blank tab, mobile emulation 320x800 / 375x812), plus counterfactual CSS overrides in scratch fixtures.
expecting: n/a (diagnosed)
next_action: Return ROOT CAUSE FOUND to the orchestrator (goal: find_root_cause_only). No product edits.
reasoning_checkpoint:
  hypothesis: "The number is ellipsed while the mark is still visible because CSS flexbox distributes negative free space in proportion to flex-shrink x flex-basis across ALL shrinkable items at once (CSS Flexbox §9.7). `flex-shrink: 4` on the mark, against 1 on the number, only changes the shares (73% vs 17% in the h2). It cannot make the mark give way first, so any deficit > 0 cuts the number."
  confirming_evidence:
    - "The fixture in the same Chrome 157 reproduces the UAT exactly: 320 → chan 62/69, number 105/116, mark 78/124; 375 → 68/69, 115/116, 118/124."
    - "The §9.7 formula predicts the fractional widths to 0.003 px (320: 62.417/105.404/78.179 predicted vs 62.414/105.406/78.18 measured)."
    - "Counterfactual strict priority (mark `flex: 1 1 0; max-width: max-content`) gives a whole number at 320 and 375 (116.164/116.164); the mark absorbs the deficit (61 and 116 px) and twin #id stays 36/36."
    - "Counterfactual flex-shrink 1000 STILL leaves the number 0.06 px short (116.102 vs 116.164): weighting never reaches priority."
  falsification_test: "If the number stayed whole with the HEAD CSS while the mark was truncated, or if the shrink amounts did not follow fs x basis, H1 would be false. Neither happened."
  fix_rationale: "Not applied (diagnose-only). The direction is to replace the weight with a real priority (mark basis 0 + grow capped at max-content), so the number shrinks only once the mark is at 0, and to rewrite the test that pins `flex-shrink: 4`."
  blind_spots: "Measured under emulation in a desktop Chrome, not on a physical phone (same as the UAT). Not measured: Safari/Firefox, the `sync_failed` action row, the h1 of the shell, the admin/history one-line uses (none exist; only chip and h2 are one-line)."
  candidate_causes:
    - "code (CSS): proportional flex-shrink used as a priority — CONFIRMED"
    - "environment: fonts/emulation differ between prod and the fixture — ELIMINATED (the fixture with inlined IBM Plex reproduces prod numbers exactly)"
    - "data: a longer-than-usual number — ELIMINATED (any deficit > 0 cuts the number; standard 16-char display form used)"
    - "code (CSS, Phase 18 form row 25375c88): the form squeezes the h2 — ELIMINATED (h2 254 px at 320 in master, pre-18 and HEAD alike)"
  and_gate: "No for the truncation: the trigger condition (the label with the mark is wider than the h2 at 320/375, while without the mark it fit — 189 px in 254) is harmless under a correct priority mechanism, so the mechanism alone is the root cause. The actions overflow is an independent second defect, not an AND-partner."

## Symptoms

expected: (UAT test 6) Шапка экрана групп с формой номера и пометкой «указан вручную»; чип расписания с ручным номером; карточка аккаунта на `/accounts`: шапка с формой не ломает раскладку, форма на своей строке; пометка усекается раньше номера, `#id` двойника виден рядом; кнопка «Сохранить» стоит у поля; ряд действий карточки в `sync_failed` не ломается.
actual: Machine walkthrough (Chrome 157 CDP mobile emulation, prod, account #75 Telegram, manual phone +7 999 123-45-67, code = branch HEAD). `h2#acct-head-name` (.acct-head__name inside .acct-label) single line. 320x800: .acct-label__chan 62/69 px (shrink 1), .acct-label__text 105/116 (shrink 1), .acct-label__manual 78/124 (shrink 4) — phone shows "+7 999 123-45…". 375x812: chan 68/69, phone 115/116 ("67" replaced by ellipsis), mark 118/124. flex-shrink 4 vs 1 shrinks all parts simultaneously. Additionally at 320: .acct-head__actions (flex: none; flex-wrap: wrap) spans 33..351 px with parent 16..304 — "К аккаунтам" overflows card, innerWidth 351 with visualViewport 320. /accounts at 320: OK. Not observed: schedule chip with manual phone, twin #id, sync_failed.
errors: None reported
reproduction: UAT test 6 in .planning/phases/18-ruchnaya-pravka-nomera/18-UAT.md, section «Машинная улика обхода»
started: Discovered during UAT 2026-11-21; phase 18 (plan 18-01 D-10 mark and truncation; plan 18-02 form in head)

## Eliminated

- hypothesis: The number truncation in the h2 pre-exists Phase 18 (the Phase 17 label alone is too wide at 320/375)
  evidence: Pre-18 fixture (CSS 77d2d812^, no mark, no form). The h2 label box is 189 px in a 254 px h2 at 320; the number is 116.164/116.164 at 320 and 375. The Phase 18 mark (+4 px gap + 124 px at 16 px font) is what creates the deficit.
  timestamp: 2026-11-21T19:20:00Z

- hypothesis: The Phase 18 form row (25375c88, `[data-acct-phone] { flex: 1 1 100% }`) narrows the h2 or the head
  evidence: The h2 is 254 px wide at 320 in master, pre-18 and HEAD alike (33..287). The form sits on its own row [33, 287] below the actions and changes only vertical offsets.
  timestamp: 2026-11-21T19:20:00Z

- hypothesis: Phase 18 caused or worsened the `.acct-head__actions` overflow at 320
  evidence: The actions rect is [33, 351.5] with innerWidth 351 in master (CSS 41e2396f, h2 "Telegram #75", no form), pre-18 and HEAD alike. The actions markup and CSS rule are byte-identical at master and HEAD (rule from bef29322, 03-05, 2026-08-12). The Phase 17 UAT (17-UAT.md:52) already recorded `scrollWidth=351` on #75 with a short label, and its note (17-UAT.md:25) records the owner's ruling that old overflows ("кнопка «К аккаунтам» на 320 px") are not filed as findings.
  timestamp: 2026-11-21T19:25:00Z

- hypothesis: A larger flex-shrink on the mark would fix the order
  evidence: With flex-shrink 1000 the number is still 116.102 of 116.164 px at 320 and 116.156 at 375 (integer clientWidth/scrollWidth hide it). Proportional sharing never reaches exactly zero, so the number stays ellipsis-eligible.
  timestamp: 2026-11-21T19:30:00Z

- hypothesis: Making the number (and channel) non-shrinkable (`flex-shrink: 0`) is a safe fix
  evidence: It works in the h2 (number whole, mark absorbs). In the schedule chip, though, the label content becomes 221 px inside a 152 px `.chip__label` (320) and a 202 px one (375, twin). The overflow lands at the END of the label, where the twin `#id` sits, and `.chip__label { overflow: hidden }` clips it. That breaks the Phase 17 PHONE-05 guarantee. Rejected as a fix direction.
  timestamp: 2026-11-21T19:30:00Z

- hypothesis: Environment (fonts or emulation) differs between prod and local measurement, making the numbers unreliable
  evidence: The self-contained fixture (real rendered markup, branch app.css, IBM Plex woff2 inlined as data URLs) in the same Chrome 157 reproduced every UAT value exactly.
  timestamp: 2026-11-21T19:20:00Z

## Evidence

- timestamp: 2026-11-21T19:00:00Z
  checked: .planning/debug/knowledge-base.md (Phase 0)
  found: Two entries, both pymax/MAX worker protocol issues. No keyword overlap with CSS/flex/truncation.
  implication: No known-pattern candidate; investigate fresh.

- timestamp: 2026-11-21T19:02:00Z
  checked: 18-CONTEXT.md D-10 (lines 82-98) and 18-01-PLAN.md (truth line 42; "Контракт CSS пометки" lines 210-215; task 3 lines 441-494); 18-RESEARCH.md Pitfall 8 (line 521)
  found: CONTEXT D-10 only says the mark is muted text "after the number and before the twin #id", and that the 320-375 px layout contract (tests/test_pages/test_responsive_markup.py, plan 17-09) must survive a label with the mark. It does NOT name a truncation order. RESEARCH Pitfall 8 only requires that the mark be truncated instead of `#id`. The order was introduced by plan 18-01 itself: truth (line 42) "при нехватке ширины пометка «указан вручную» уступает место раньше номера и обрезается многоточием, а `#id` двойника не сжимается", with the chosen mechanism "`flex-shrink: 4` уступает место раньше номера" (lines 210-215). Task 3 RED/GREEN pins exactly the literal `flex-shrink: 4` by reading CSS text; the plan states the browser width is proven only by a human walkthrough.
  implication: The promise (mark gives way BEFORE the number) is the plan's own truth; the defect is that the chosen mechanism cannot deliver it.

- timestamp: 2026-11-21T19:04:00Z
  checked: app/static/css/app.css:2521-2561 (HEAD), app/templates/components/account_label.html, app/templates/account_groups/list.html:54-128
  found: `.chip__label > .acct-label, .acct-head__name > .acct-label { display: inline-flex; gap: .25em; max-width: 100%; min-width: 0 }`; chan and text get `min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap` (default flex-shrink 1); `.acct-label__manual` in the same two containers gets `flex-shrink: 4; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap`; `.acct-label__id { flex: none }`. Macro order: chan, text (mono), manual, id. The selectors cover `.chip__label` (ads/includes/sched_card.html:230) and `.acct-head__name` (list.html:59) identically.
  implication: Both one-line containers share the same weighted-shrink rules, so any defect in the head also applies to the schedule chip.

- timestamp: 2026-11-21T19:06:00Z
  checked: git log 41e2396f..HEAD for the layout files; git diff 41e2396f HEAD for app.css and list.html; git log -S'flex: none; margin-left: auto'
  found: The merge-base is master. The branch carries Phase 17 AND Phase 18: b610f785 (17-03) put the phone in the h2 (at master the h2 was `Telegram #75`); 7569f97e (17-09) added the one-line-container inline-flex block; 77d2d812 (18-01) added the mark with flex-shrink 4; 25375c88 (18-02) added `[data-acct-phone] { flex: 1 1 100% }` as the last child of the head. The `.acct-head__actions { flex: none; margin-left: auto; display: flex; flex-wrap: wrap }` rule dates from bef29322 (03-05, 2026-08-12). The actions markup (list.html, "Синхронизировать всё" + "К аккаунтам") is byte-identical at master and HEAD, and the branch diff does not touch the `.acct-head__actions` rule.
  implication: H2 (actions overflow) is very likely pre-existing; the form only adds a 100%-basis row after the actions and should not change the width of the actions box. Needs a measured master baseline.

- timestamp: 2026-11-21T19:15:00Z
  checked: Method — the real pages were rendered by the app via the test client (throwaway pytest file in the session scratchpad, `-p tests.conftest`; seeds: #75 tg_user manual "+7 999 123-45-67"; twins #7311/#7312 tg_user manual "+7 999 765-43-21"; ad with schedules on #7311 and #75). Pages: /accounts/75/groups, /accounts/7311/groups, /ads/{ad}/edit?sched=…, /accounts. Each became a self-contained fixture (branch app.css inline, IBM Plex woff2 as data URLs, scripts stripped). Measured in the UAT's Chrome 157.0.8103.79 over the CDP tunnel in ONE fresh about:blank tab (Page.setDocumentContent; no site navigation; the tab was closed afterwards), with Emulation mobile 320x800 / 375x812 at DPR 2.
  found: The HEAD h2 (#75) reproduces the UAT exactly. 320 → chan 62/69, number 105/116, mark 78/124 (fractional 62.414/105.406/78.18 of 68.789/116.164/124.195); innerWidth 351. 375 → chan 68/69, number 115/116, mark 118/124 (67.969/114.773/118.258).
  implication: Deterministic reproduction; the fixture is faithful to prod.

- timestamp: 2026-11-21T19:18:00Z
  checked: CSS Flexbox §9.7 (resolving flexible lengths, negative free space) against the measured fractional widths
  found: The scaled shrink factor is flex-shrink x flex-base-size, and each item loses deficit x scaled/Σscaled (min-width: 0 → no clamp until 0). h2 at 320: available 254 − 2 gaps x 4 = 246; natural sum 309.148 → D = 63.148; scaled 68.789 / 116.164 / 4x124.195 = 496.78 (Σ 681.733) → predicted 62.417 / 105.404 / 78.179 vs measured 62.414 / 105.406 / 78.18. At 375: D = 8.148 → predicted 67.967 / 114.776 / 118.258 vs measured 67.969 / 114.773 / 118.258. The number's share is 116.164/681.733 = 17.0% of any deficit; the mark's is 72.9%.
  implication: Mechanism confirmed. `flex-shrink: 4` cannot make the mark give way first; the number is ellipsed as soon as D > 0 (text-overflow fires on a sub-pixel overflow, so a 1.39 px loss at 375 replaces "67" with "…" in the monospace number).

- timestamp: 2026-11-21T19:22:00Z
  checked: Twin #id case — h2 of /accounts/7311/groups and schedule chips in the ad editor (HEAD)
  found: h2 twin at 320: chan 58/69, number 99/116, mark 49/124, #id 36/36; at 375: 64/69, 108/116, 89/124, #id 36/36. Chips (`.chip__label` is 150-152 px wide at 320 and 200-202 px at 375): unique #75 at 320 → chan 45/58, number 90/116, mark 9/105; at 375 → chan 50/58, number 99/116, mark 44/105 (predicted by §9.7: 49.96/99.29/43.78). Twin #7311 at 320 → chan 35/58, number 70/116, mark 0/105 (frozen at min-width 0, after which the rest of the deficit falls on chan and number alone), #id 36/36; at 375 → 46/58, 92/116, 17/105, #id 36/36.
  implication: The SAME defect hits `.chip__label`: at 375 (both chips) and 320 (unique) the number is cut while the mark still shows. The twin `#id` stays whole everywhere (`flex: none` works), so that half of D-10 holds.

- timestamp: 2026-11-21T19:24:00Z
  checked: Baselines — pre-18 (CSS 77d2d812^, mark and form removed) and master (CSS 41e2396f, h2 "Telegram #75", form removed), for both the groups head and the editor chip (pre-18)
  found: Pre-18 h2: number 116/116 at 320 and 375 (label 189 px). Pre-18 chip: number already cut at 320 (unique 92/116, twin 68/116) and in the twin chip at 375 (100/116); the unique chip at 375 was whole (116/116). Actions: [33, 351.5], innerWidth 351 at 320 in master, pre-18 and HEAD alike (head border-box 16..304, content box 33..287 = 254 px; buttons 33..232 and 240..351.5 = 318.5 px max-content). At 375 the actions end at 351.5 against a content-box right edge of 342 (9.5 px into the 16 px padding, inside the border at 359) — also identical at master.
  implication: (a) The h2 truncation is introduced by Phase 18 (77d2d812). (b) In the chip at 320, number truncation is partly a pre-existing Phase 17 condition (chan 58 + gap + number 116 = 178 > 150 px, accepted in Phase 17 with the full text in `title=`), but Phase 18 makes it worse (unique chip at 375: 116 → 99) and violates the order promise. (c) The actions overflow is pre-existing and unchanged by Phase 18.

- timestamp: 2026-11-21T19:28:00Z
  checked: Counterfactual CSS overrides in scratch fixtures (no product edits)
  found: (1) Mark `flex: 1 1 0; max-width: max-content` (strict priority): h2 unique → number 116.164/116.164 at 320 and 375, mark 61/124 and 116/124; h2 twin → number whole, mark 21 and 76 px, #id 36/36; chips → mark collapses first (0 at 320, 18 at 375 unique), and the number is cut only where geometry forces it (unique chip at 320 95/116; twin chip at 320 70/116 and at 375 103/116), with #id whole and no label overflow. (2) Chan+number `flex-shrink: 0`: h2 fine, but in the chip the label content is 221 px in a 152 px (320) or 202 px (375, twin) box; the end of the label (#id) passes the `overflow: hidden` edge of `.chip__label`. (3) Mark `flex-shrink: 1000`: number still 0.06 px short. (4) `.acct-head__actions { flex: 0 1 auto; min-width: 0 }`: actions become [33, 287], "К аккаунтам" wraps to its own row, innerWidth/docScroll back to 320 — in both HEAD and master.
  implication: Confirms both mechanisms. A real priority (basis 0 for the mark) delivers the plan's promise in the h2, while the naive non-shrinkable number breaks the chip's #id. The actions overflow comes from `flex: none` (= 0 0 auto) pinning the box at max-content, so its inner `flex-wrap: wrap` never gets a narrower line.

- timestamp: 2026-11-21T19:32:00Z
  checked: tests/ — grep for `flex-shrink`, `acct-label__manual`, `acct-head__actions`, `acct-head`
  found: `tests/test_pages/test_responsive_markup.py::test_account_label_keeps_the_twin_id_visible_in_a_one_line_container` (lines 5164-5198) asserts the literal `"flex-shrink: 4" in body` for `.chip__label .acct-label__manual` and `.acct-head__name .acct-label__manual`. Its failure message and docstring (5173-5175, 5197) equate the literal with "the mark gives way before the number". The same test also requires `min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap` on chan/text/manual in both containers. `test_account_label_rules_introduce_no_fixed_width` (5201-5213) forbids `width:` (the lookbehind allows `max-width`). `test_the_manual_mark_is_muted` (5242) is unaffected. No test pins `.acct-head__actions` (test_account_groups.py:2026 only checks that the `[data-acct-head]` selector exists). The false claim is also written into the app.css comment (2537-2541) and 18-01-SUMMARY.md (lines 17, 147).
  implication: A phase test pins the defective mechanism as the norm, so a correct fix will turn it red; it must be rewritten in the same change, not read as a regression. The actions rule is unpinned.

## Resolution

root_cause: "Plan 18-01 (commit 77d2d812) used `flex-shrink: 4` on `.acct-label__manual` as a truncation PRIORITY, but flex-shrink is a proportional WEIGHT. In `.acct-head__name > .acct-label` and `.chip__label > .acct-label` (inline-flex), chan, number and mark all carry `min-width: 0`, so per CSS Flexbox §9.7 every deficit is split by flex-shrink x flex-basis across all three at once. In the h2 the number takes 17% of it (mark 73%, chan 10%), so the number is ellipsed whenever the label does not fit, while the mark still has width (measured: 105/116 at 320, 115/116 at 375). The same rules produce the same defect in the schedule chip (unique #75 at 375: number 99/116 while the mark shows 44 px). The twin #id is not affected (`flex: none`). A phase test (test_responsive_markup.py:5195-5198) pins the literal `flex-shrink: 4` as the contract. Separate, pre-existing and NOT caused or worsened by Phase 18: `.acct-head__actions { flex: none }` (bef29322, Phase 3) pins the actions box at its max-content of 318.5 px, so its own `flex-wrap: wrap` never fires and it overflows the 254 px content box at 320 (innerWidth 351, identical at master 41e2396f; already recorded in 17-UAT.md:52 and waived by the owner at 17-UAT.md:25)."
fix: "(not applied — goal: find_root_cause_only)"
verification: "(diagnose-only) Reproduced deterministically in the UAT's Chrome 157 with real rendered markup; §9.7 arithmetic matches measurements to 0.003 px; counterfactuals confirm the mechanism and reject the naive fixes."
files_changed: []

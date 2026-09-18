---
status: resolved
trigger: "UAT gap G-11-6 (Phase 11, test 6): extra vertical gap under form buttons from hidden .form-busy"
created: 2026-09-17T17:00:00Z
updated: 2026-09-18T10:40:00Z
resolved_by: "Plan 11-21 (ec33c8e RED, 810eaa7 GREEN, bf3cb65 gates); rendering re-observed and accepted by the owner in /gsd-verify-work 11 round 2, 2026-09-18"
---

## Resolution — rendering observed 2026-09-18

Fix shipped by plan 11-21 (`.form-wrapper { position: relative }` + `.form-wrapper > .form-busy
{ position: absolute; right: 0; bottom: 0; pointer-events: none }`, scoped so the base `.form-busy`
rule stays the only one with that exact selector). Stand freshness was checked BEFORE measuring:
`app.css?v=12346d8c0f1f` on broadcaster.all-torgi.ru carries both rules and the group-row exception.

**Measured after the fix (Chrome, chrome-devtools MCP, 1440×900; method: form height with and
without the indicator node in the DOM):** profile 111 px (was 132), schedule edit form 369 px
(was +24), MAX phone step 111 px (was 129.5) — delta 0 in every case.

**Two of the three blind spots recorded above are now closed by direct measurement, not derivation:**

- *Horizontal flex-row effects (~12 px), previously "derived from CSS reading, not measured":*
  measured. Admin action row `/admin/users/2` — gaps 9, 9, 9 px, wrapped-form width delta 0;
  `/schedules` — seven `sched-item__head` rows, gaps 12, 12 px each, width delta 0.
- *Modal panel 22 px, previously "derived, not measured":* measured. `/accounts/5/delete` panel form
  is `modal__form`, NOT `form-wrapper`, so the scoped rule does not reach it; the indicator stays
  `position: static` and the panel is 89.14 px against 67.14 px without it — exactly the 22 px
  (8 px item + 14 px gap) accepted by owner decision 1 / 10-UAT 3.5. Unchanged, as intended.
- *MAX step, still a reconstruction:* `/accounts/connect/max` redirects while MAX #29 is active, so
  the step was rendered from `accounts/includes/max_connect_step.html` by the project's Jinja and
  injected into a live page with production CSS. Same limitation as the original diagnosis.

**One consequence the diagnosis did not predict:** with the indicator pinned to the form box's
bottom-right corner, its 8×8 box fully overlaps the wrapped button's bounding box and sits on the
`border-radius: 99px` pill edge, cutting a visible notch out of the button silhouette. Clicks are
unaffected — `pointer-events: none` holds, and a 4×4 `elementFromPoint` grid over the dot area was
byte-identical with and without the dot in the DOM. The owner was shown this, together with the
2.6:1 contrast of the dot on the filled CTA (below the WCAG 1.4.11 3:1 floor), and accepted both in
`11-UAT.md` tests 6 and 8.

## Current Focus

bug_class: Bohrbug (deterministic layout, CSS box model; reproduces every render)
known_pattern_candidate: none (knowledge-base.md has no form-busy/form_wrapper/layout entry)
hypothesis: CONFIRMED — form_wrapper.html prints `<span class="form-busy">` IN FLOW as the last child of every wrapped <form>; the .form-busy base rule gives it an atomic 8x8 box (display:inline-block) and hides it only with opacity+visibility, which keep the box. Nothing takes it out of flow. The layout effect depends on the form's own formatting context.
test: done (source read, render, git history, caller enumeration, gate parser probe in memory)
expecting: n/a
next_action: return ROOT CAUSE FOUND to orchestrator (goal: find_root_cause_only)

reasoning_checkpoint:
  hypothesis: "The always-rendered, in-flow, visibility-hidden inline-block .form-busy span that form_wrapper appends after caller() occupies layout space: in block forms it opens a line box under the inner flex column (profile 21 px, MAX 18.5 px); in the flex-column sched edit form it is an 8 px flex item plus one 16 px gap (24 px)."
  confirming_evidence:
    - "Orchestrator measurement: setting .form-busy to position:absolute removes exactly 21 / 24 / 18.5 px"
    - "Sched edit arithmetic is exact: 8 px box + 16 px gap = 24 px (app.css:2155 height 8px, app.css:2327 gap 16px)"
    - "Rendered markup: `</div>\\n  <span class=\"form-busy\" aria-hidden=\"true\"></span>\\n</form>` for profile and MAX"
    - "Only .form-busy rules in app.css are :2154 and :2161; neither sets position or display:none"
  falsification_test: "If the span were out of flow (or absent) and the gap persisted, the hypothesis would be false — the owner's measurement with position:absolute already shows the gap disappears exactly."
  fix_rationale: "Removing the indicator's layout footprint at the macro/CSS level fixes all callers at once, which matches D-14 (one place renders the indicator)."
  blind_spots: "MAX measured by injecting rendered markup into a live page, not on /accounts/connect/max itself; horizontal flex-row effects (~12 px) derived from CSS reading, not measured; modal panel 22 px derived, not measured."
  candidate_causes:
    - "code(template): unconditional trailing span + whitespace in form_wrapper.html:145-146"
    - "config(CSS): .form-busy base rule display:inline-block + visibility-only hiding, no out-of-flow positioning (app.css:2154-2160)"
    - "code(template, phase 11): column layout moved from <form> to inner div in 11-10/11-18 — shapes the manifestation (line box vs flex item), not its existence"
    - "environment(browser): Chrome-specific rendering — rejected, spec behavior"
  and_gate: "yes, weakly: the gap needs BOTH the span in flow with an atomic box (CSS) AND its placement as the trailing child of a vertically stacked form (macro). The macro always places it last, so in practice this is one design defect: the macro+CSS pair gives the hidden indicator a layout footprint."

## Symptoms

expected: Форма «Продолжить» (MAX connect phone step), «Сохранить» (profile settings), schedule edit form in the ad editor — no extra vertical gap under the buttons caused by the hidden `.form-busy` indicator (finding 1 in 11-UI-REVIEW.md).
actual: (Chrome 152 / macOS, deployed phase-11 build) extra space in all three forms.
  - Profile «Сохранить»: `#profile-settings form` 132 px; with `.form-busy` position:absolute 111 px -> 21 px extra. Form display:block, first child `<div data-form>` flex column (gap 14px), `<span class="form-busy">` (computed inline-block; visibility hidden; position static) after it, preceded by whitespace text node, starting an anonymous line box under the column.
  - Schedule edit form (`form[hx-post="/schedules/101/edit"]` in `#sched-101`, ad 38): form display:flex column gap 16px; `.form-busy` flex item (computed display block) 8 px after `.sched-card__actions` -> 1710 vs 1686 -> 24 px extra (8 px box + 16 px gap).
  - MAX «Продолжить» (accounts/includes/max_connect_step.html, step=phone): form 129.5 px vs 111 px out of flow -> 18.5 px extra.
errors: None reported
reproduction: Test 6 in .planning/phases/11-massovyy-perevod-razdelov-pisma/11-UAT.md
started: Discovered during UAT 2026-09-17; predicted by 11-UI-REVIEW.md finding 1

## Eliminated

- hypothesis: the whitespace text node before the span is what creates the vertical gap
  evidence: CSS 2.1 §9.4.2 — a line box holding only collapsible whitespace is zero-height; the atomic inline-block is what makes the line box non-empty. In the flex-column sched form whitespace-only text is discarded, yet the gap is exactly 8+16. Whitespace only adds about 4 px of horizontal trailing space in inline contexts.
  timestamp: 2026-09-17T17:25:00Z

- hypothesis: moving the column class off <form> onto an inner div (11-10, 11-18) is the root cause, so putting the column back on the form would fix it
  evidence: the sched edit form IS the flex column itself and still gains 24 px (span becomes a flex item plus one gap). Restoring the column would turn the profile/MAX line box into 8 + 14 = 22 px, not zero. This change shapes how the bug shows up, but it does not cause it.
  timestamp: 2026-09-17T17:25:00Z

- hypothesis: browser or data dependent (environment/data category)
  evidence: visibility:hidden keeping the box is spec behavior in all engines; the excess does not depend on form content (constant 8 px + container gap / one line-height).
  timestamp: 2026-09-17T17:25:00Z

## Evidence

- timestamp: 2026-09-17T17:05:00Z
  checked: app/templates/components/form_wrapper.html:138-148
  found: macro body is `<form ... hx-indicator="find .form-busy">{%- if caller is defined %}{{ caller() }}{% endif %}\n  <span class="form-busy" aria-hidden="true"></span>\n</form>`. The span is unconditional, the last child of the form, and preceded by a newline+2 spaces text node (no `-` whitespace control after `{% endif %}`).
  implication: every wrapped form carries an in-flow trailing span plus a whitespace text node.

- timestamp: 2026-09-17T17:05:00Z
  checked: app/static/css/app.css:2154-2165 (.form-busy base + .htmx-request)
  found: `.form-busy { flex: none; display: inline-block; width: 8px; height: 8px; ... opacity: 0; visibility: hidden; }`. No position rule anywhere. Hiding is by opacity+visibility only, which keeps the layout box. Comment 2135-2150 says display:inline-block was added (WARN-5 of phase 9) so the dot has a box in non-flex forms; guarded by test_the_indicator_class_is_self_sufficient.
  implication: the hidden indicator always occupies 8x8 in flow; in block formatting context the inline-block also forces a line box of the inherited line-height.

- timestamp: 2026-09-17T17:05:00Z
  checked: app/templates/includes/profile_settings.html:86-92, accounts/includes/max_connect_step.html:64-69, app.css:1867, 1928-1934
  found: both callers put their content in an inner flex column (`<div data-form>` = flex column gap 14; `<div class="connect-step__form">` = flex column gap 14). The <form> itself has no display rule (block); MAX form only gets `.connect-step > form { align-self: stretch }`.
  implication: block form -> [block-level flex div][whitespace + inline-block span] -> anonymous block box wrapping a line box under the column. Line box height = strut of inherited font (normal line-height) = the measured 21 px / 18.5 px.

- timestamp: 2026-09-17T17:05:00Z
  checked: ads/includes/sched_card.html:210-305, app.css:2326-2330
  found: edit form is `form_wrapper(...)` whose last caller child is `<div class="sched-card__actions">` with СОХРАНИТЬ РАСПИСАНИЕ; CSS `.sched-card__body > form:has(.sched-card__block) { display:flex; flex-direction:column; gap:16px }`.
  implication: span becomes a blockified flex item (8 px tall) after the actions row, and adds one 16 px gap -> 24 px, matching the measurement exactly. Whitespace text node is dropped in flex containers (no contribution).

- timestamp: 2026-09-17T17:05:00Z
  checked: 11-UI-REVIEW.md finding 1 / Pillar 5
  found: audit predicted the same mechanism from source and also flagged flex action rows ([data-actions] gap 9, .acct-card__actions, .sched-card__head > form).
  implication: independent source reading agrees; blast radius must be enumerated across all callers.

- timestamp: 2026-09-17T17:15:00Z
  checked: rendered includes/profile_settings.html and accounts/includes/max_connect_step.html (step=phone) via app.pages.common.templates.env
  found: profile tail `…Сохранить</span></button>\n  </div>\n\n  <span class="form-busy" aria-hidden="true"></span>\n</form>`; MAX tail `…Продолжить</span></button>\n    </div>\n    \n  <span class="form-busy" aria-hidden="true"></span>\n</form>`.
  implication: confirmed by render: block-level flex div, then whitespace + inline-block span as last in-flow content of a block <form> -> anonymous line box.

- timestamp: 2026-09-17T17:15:00Z
  checked: git history (git log -S) of form_wrapper span, .form-busy display rule, and form_wrapper adoption per template
  found: span printed since 13320ba (09-01); `display: inline-block` added d2b43fd (09-08, WARN-5). Phase 9 had only two consumers, both layout containers where the dot is intentionally a visible flex item: group-row toggle form (`[data-group-row] form[action$="/toggle"] { display:inline-flex; gap:6px }`) and `.modal__form` (own copy of the span). All other 13 call sites were adopted in phase 11 (5348f64 11-01 sched edit, 05240b2 11-03, 0729eca 11-04, dfcade8 11-05, 4881663 11-10 profile, b73fdfb 11-12, 124cb9e 11-13, b9db0db 11-15, 35aac92 11-16, 133561f 11-17, 7ef10a0 11-18 MAX). 11-10 and 11-18 moved the flex-column class from the <form> tag (`<form data-form>`, `<form class="connect-step__form">`) to an inner <div> because the macro prints the tag and takes no class.
  implication: regression is phase 11: the column moved off the form, leaving a block form whose trailing in-flow inline-block span now sits OUTSIDE the column.

- timestamp: 2026-09-17T17:20:00Z
  checked: all 14 form_wrapper call sites + container CSS
  found: |
    VERTICAL gap (reported):
      1. includes/profile_settings.html:86 — block form > div[data-form] flex col + inline-block span -> line box (21 px measured)
      2. accounts/includes/max_connect_step.html:64 — block form (flex item of .connect-step, align-self stretch) > div.connect-step__form flex col + span -> line box (18.5 px)
      3. ads/includes/sched_card.html:210 — form is flex col gap 16 (app.css:2326) -> span is 8 px flex item + 16 gap = 24 px
    HORIZONTAL trailing space / uneven gaps in flex rows (form = block, button inline-flex, then collapsed space ~4 px + 8 px inline-block on same line => form ~12 px wider than its button):
      4-5. admin/includes/user_actions.html:70,83 — two forms inside `[data-actions]` (flex row gap 9, app.css:1897) next to plain forms «Войти под пользователем» / «Удалить» -> ~21 px vs 9 px gaps
      6-8. accounts/list.html:133, accounts/partial_cards.html:87, accounts/partials/sync_status_card.html:109 — «Повторить» in `.acct-card__actions` (flex row gap 8, `form {flex:none}`) next to plain delete form -> ~20 px vs 8 px
      9. account_groups/list.html:104 — form inside `<div data-syncing?>` in `.acct-head__actions` (flex row gap 8) next to link «К аккаунтам» -> ~20 px vs 8 px
      10. ads/includes/sched_card.html:167 — toggle form in `.sched-card__head > form {flex:none}` (gap 12): form = toggle + (Alpine-removed «Применить» span) + space + 8 px -> head controls shifted ~12 px (pushes СВЕРНУТЬ/РАЗВЕРНУТЬ)
      11. schedules/includes/schedule_row.html:106 — same in `.sched-item__head > form {flex:none}` (gap 12), before «Открыть объявление»
    FLEX-ROW form (dot is a flex item by design):
      12. account_groups/includes/group_row.html:193 — toggle form is inline-flex gap 6 -> 6 + 8 = 14 px after toggle (phase 9, the original intended consumer)
    NO VISIBLE EFFECT (block form full width, button + span fit one line):
      13. ads/form.html:276 (schedules/new, in .card__body block)
      14. billing/balance.html:123 (inside div[data-plan-cta] in block panel)
    SAME NODE OUTSIDE form_wrapper:
      components/modal.html:816 — `.modal__form` flex col gap 14; span between body/slot and .modal__actions -> 8 + 14 = 22 px extra between text and buttons in every confirmation panel (18 sites). Any global .form-busy change affects it.
  implication: one mechanism, three layout outcomes (line box / flex-column item+gap / flex-row trailing width). Fix must be at the macro+CSS level, not per caller.

## Resolution

root_cause: The hidden busy indicator has a layout footprint. components/form_wrapper.html:145-146 always adds `<span class="form-busy" aria-hidden="true"></span>` in flow, as the last child of every wrapped form, after a whitespace text node. app.css:2154-2160 gives the span an atomic 8x8 box (`display:inline-block`, added in 09-08 so the dot would be visible in non-flex forms). It hides the span only with `opacity:0; visibility:hidden`, which keeps the box, and it never takes the span out of flow. Result by layout: (a) in a block form whose content is a flex-column div (profile_settings `[data-form]`, max_connect_step `.connect-step__form`), the span opens an anonymous line box one inherited line-height tall under the column (21 / 18.5 px). (b) In a flex-column form (sched_card edit form, app.css:2326), it is an 8 px flex item plus one 16 px gap (24 px). (c) In flex action rows, each wrapped form is about 12 px wider than its button (collapsed space + 8 px), so the gaps are uneven next to plain forms. Phase 9 hid this because its only wrapper consumer (the group-row toggle, inline-flex) wants the dot inline. Phase 11 exposed it by moving 13 forms onto the macro and moving column layouts from the <form> tag to inner divs.
fix: (not applied — goal find_root_cause_only)
guard_trap: a second CSS rule whose selector is exactly `.form-busy` turns test_the_indicator_class_is_self_sufficient red, because the parser keeps the LAST matching rule (checked in memory against _offenders_indicator_self_sufficiency). A scoped selector (e.g. `form > .form-busy`) stays green.
verification:
files_changed: []

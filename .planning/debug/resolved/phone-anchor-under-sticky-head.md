---
status: resolved
trigger: "phone-anchor-under-sticky-head — Переход по «Указать номер» / «Изменить» с карточки аккаунта (`/accounts/{id}/groups#phone`) должен оставлять поле «Номер телефона» в видимой области, не под липкой шапкой `[data-head]`."
created: 2026-11-21T19:00:00Z
updated: 2026-11-24T00:00:00Z
mode: find_root_cause_only
---

> **СТАТУС 2026-11-24: закрыто при закрытии вехи v2.2.** Причина (нет отступа прокрутки под липкую шапку) устранена планом 18-04 (`html { scroll-padding-top }`); проверка 8 `18-UAT.md` — pass, принято владельцем 2026-11-22 («принимаю все»); `18-VERIFICATION.md` — passed.

## Current Focus

hypothesis: "CONFIRMED — The sticky shell head `<header data-head>` (base.html:229; app.css:656-657 `position: sticky; top: 0; z-index: 5`) has no scroll-offset counterpart anywhere: no `scroll-padding-top` on the document scroller and no `scroll-margin-top` on the fragment target `#phone`. Native fragment navigation therefore aligns the input's border-box top with the viewport top (block: start), right where the head (0…86 px desktop, 0…172 px at ≤860 px) paints over it."
bug_class: Bohrbug (deterministic layout; reproduces at every measured width; no timing or JS involved)
known_pattern_candidate: none
test: "done — static evidence (CSS/template grep, git history) + live UAT geometry (getComputedStyle scrollMarginTop=0px, elementFromPoint→HEADER, field/head rectangles at three widths)"
expecting: n/a
next_action: "Return ROOT CAUSE FOUND to the orchestrator (diagnose-only mode). No product edits."

reasoning_checkpoint:
  hypothesis: "Field #phone lands under [data-head] because the app declares a sticky header at top:0 over the document scroller but declares NO scroll offset (scroll-padding-top on html / scroll-margin-top on #phone), so the browser's fragment scroll puts the target's top edge at viewport y=0, inside the header's box."
  confirming_evidence:
    - "grep of app/static/css/app.css: zero matches for scroll-margin, scroll-padding, scroll-behavior, --head-h; [data-head] sticky top:0 z-index:5 at :656-657"
    - "UAT live: getComputedStyle(#phone).scrollMarginTop = '0px'; 1280×800 scrollY=212 → field 0…45 under head 0…86; elementFromPoint(field centre) = HEADER; 375×812 field 0…45 under 0…172; 320×800 field 79…124 under 0…172"
    - "No project JS participates: no hx-boost, no scrollIntoView, no location.hash/hashchange, no autofocus on the page; link_button renders a plain <a href>; focus on #phone is the browser's own fragment-focusing step"
  falsification_test: "Adding `html { scroll-padding-top: <head height + caption + gap> }` (or `#phone { scroll-margin-top: … }`) in DevTools on the live page and re-navigating to #phone: if the field AND its caption still end up under [data-head], the hypothesis is wrong."
  fix_rationale: "(diagnose-only) The browser exposes exactly one mechanism to offset fragment/focus scrolling for obstructions: scroll-padding on the scroll container or scroll-margin on the target. Supplying it addresses the cause (missing offset), not a symptom."
  blind_spots: "(1) The fix-candidate rule was NOT exercised in a browser in this session (no headless browser locally; CDP browser lives on another machine). (2) The 79 px residual offset at 320×800 is unexplained (plausibly the layout-viewport overflow at 320 — innerWidth 351 vs visualViewport 320 — or a post-scroll layout shift); immaterial because 79…124 is still inside 0…172. (3) Head-height arithmetic below is derived from CSS + line-height≈1.3, matched to the measured 86/172, not separately measured."
  candidate_causes:
    - "code (CSS): no scroll-padding-top / scroll-margin-top compensating for the sticky [data-head] — CONFIRMED primary"
    - "code (template): fragment targets the <input>, while the visible caption «Номер телефона» sits ~20 px above it inside label.field — CONTRIBUTING (any target-local offset must cover the caption too)"
    - "environment (viewport): [data-head] height is not constant — 86 px desktop vs 172 px at ≤860 px (padding change + h1/subtitle wrapping + .head-actions wrapping to its own row) — CONTRIBUTING to fix design (a single literal is insufficient)"
    - "data: account with a long group list (54) makes the document tall enough for the scroll to reach the target — ENABLING CONDITION (with a short list the scroll clamps and the field stays below the head)"
    - "JS (htmx/Alpine/autofocus) — ELIMINATED"
  and_gate: "yes — the symptom needs (a) a sticky header over the document scroller AND (b) no scroll offset AND (c) a document long enough to scroll the target to y=0. (a) is intended design, (c) is the normal production case, so (b) is the actionable root cause; viewport-dependent head height (env) shapes how (b) must be supplied."

## Symptoms

expected: С `/accounts` нажать «Указать номер» / «Изменить» на аккаунте с длинным списком групп: открывается экран групп этого аккаунта, поле «Номер телефона» (`#phone`) в видимой области и НЕ скрыто липкой шапкой `[data-head]`.
actual: |
  Машинный обход (Chrome 157 через CDP, бой, аккаунт №75, 54 группы, код = HEAD ветки):
  - 1280×800, клик «Указать номер»: scrollY=212, поле `#phone` top 0…45 px, липкая `[data-head]` (position: sticky; top: 0) 0…86 px; elementFromPoint в центре поля → HEADER; на скриншоте поля не видно; фокус на #phone.
  - 320×800 (mobile emulation), клик «Изменить»: поле 79…124, шапка 0…172 — целиком под шапкой.
  - 375×812, адрес `#phone`: поле 0…45, шапка 0…172.
  - getComputedStyle(#phone).scrollMarginTop = "0px".
  Код-ревью фазы 18 заранее назвало это WR-02 (`18-REVIEW.md`).
errors: None reported
reproduction: Test 4 in UAT (`.planning/phases/18-ruchnaya-pravka-nomera/18-UAT.md`, раздел «Машинная улика обхода»)
started: Discovered during UAT 2026-11-21; фаза 18 (план 18-03 добавил ссылку с якорем `#phone`, план 18-02 — форму в шапке аккаунта)

## Eliminated

- hypothesis: "Project JS (htmx boost / Alpine x-init / autofocus / a hash handler) scrolls or focuses #phone and mis-positions it"
  evidence: "grep app/templates + app/static/js (excluding vendored minified files) for autofocus, scrollIntoView, location.hash, hashchange, hx-boost, scrollIntoViewOnBoost, defaultFocusScroll, focus(), show:/scroll: modifiers: no hit on the account-groups path (only modal.html focus trap and unrelated x-init button removers). link_button (components/button.html:20-22) renders a plain `<a class=\"btn …\" href=…>`, no hx-* attributes. The phone form (phone_form.html) has no autofocus. Focus on #phone after navigation is the browser's native fragment-focusing step."
  timestamp: 2026-11-21T19:20:00Z

- hypothesis: "An existing project convention for offsetting anchors under the sticky head exists but is not applied to #phone"
  evidence: "No such convention exists. app.css has zero scroll-margin / scroll-padding / --head-h. The only head-aware rule is `[data-editor-side] { position: sticky; top: 96px }` (app.css:2116-2117), a hardcoded literal for a sticky sidebar column (not anchor scrolling), switched to static at ≤900px (app.css:469). The older in-app anchor `#sched-{id}` (dashboard/includes/upcoming_row.html:35, ads/includes/sched_card.html:189 → `<article data-sched-card id=\"sched-N\">`, sched_card.html:132; since 06c099ae, 2026-08-14) has no offset either: same latent defect class, never reported."
  timestamp: 2026-11-21T19:30:00Z

## Evidence

- timestamp: 2026-11-21T19:00:00Z
  checked: ".planning/debug/knowledge-base.md (Phase 0)"
  found: "Two entries, both MAX/pymax backend (sticker setId, photoIds). No keyword overlap with sticky header / anchor / scroll-margin."
  implication: "No known-pattern candidate; proceed with open investigation."

- timestamp: 2026-11-21T19:05:00Z
  checked: "graphify query (worktree has no graphify-out/; ran against /source/broadcaster/graphify-out/graph.json)"
  found: "Query returned only test/model nodes; CSS rules and template markup are not graph nodes. Fell back to grep."
  implication: "Graph cannot localize CSS/template issues; raw grep is the right tool here."

- timestamp: 2026-11-21T19:06:00Z
  checked: "app/templates/base.html:225-260"
  found: "The sticky element is `<header data-head>` (base.html:229), a child of `[data-main]` inside the `[data-shell]` grid, sibling BEFORE `[data-body]` (:248) where page content (incl. the account head + phone form) renders. It holds `.head-titles` (h1#page-title + p.head-subtitle) and `.head-actions` (session-pill + block page_actions). The document (html/body) is the scroll container: no ancestor of [data-head] declares overflow."
  implication: "Hash navigation scrolls the document viewport; `[data-head]` sticks to viewport top at `top: 0`, so anything scrolled to y=0 lands under it."

- timestamp: 2026-11-21T19:07:00Z
  checked: "app/static/css/app.css — grep for data-head, scroll-margin, scroll-padding, scroll-behavior, scrollIntoView, --head-h, position: sticky"
  found: |
    - app.css:656-662 `[data-head] { position: sticky; top: 0; z-index: 5; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; padding: 18px 32px; background: rgba(8,8,11,.85); backdrop-filter: blur(14px); border-bottom: 1px solid ... }`
    - app.css:485 (inside `@media (max-width: 860px)`) `[data-head] { padding: 14px 16px !important; }`
    - ZERO matches for `scroll-margin`, `scroll-padding`, `scroll-behavior`, `--head-h` anywhere in app.css.
    - app.css:2116-2117 `[data-editor-side] { position: sticky; top: 96px; }` — the only other place that accounts for the head: a hardcoded literal (86px head + 10px), not a token, and only for sticky positioning (not anchor scrolling). It is switched to `position: static` at <=900px (app.css:469), so it never had to deal with the taller mobile head.
  implication: "No mechanism exists anywhere to offset anchor/focus scrolling for the sticky head. There is no head-height token to reuse — WR-02's suggested `var(--head-h, 72px)` references a token that does not exist (its fallback 72px is also below the measured 86px desktop height)."

- timestamp: 2026-11-21T19:10:00Z
  checked: "app/templates/account_groups/list.html:31-128, account_groups/includes/phone_form.html:49-56, components/field.html:7-28, app.css:735-745"
  found: |
    - The account head `[data-acct-head]` is the first content block in `[data-body]`; the phone form `#acct-phone[data-acct-phone]` is its last child (list.html:127).
    - The fragment target is the `<input class="field__input" id="phone">` emitted by the `field` macro, wrapped in `<label class="field">` = column flex, gap 7px: `span.field__label` («Номер телефона», 10px mono uppercase) ABOVE the input, then `span.field__hint` below.
    - So the visible caption sits ≈ 13 px (10px × normal line-height) + 7 px gap ≈ 20 px above the input's top edge; the input itself is 45 px tall (matches UAT 0…45).
  implication: "Whatever offset is chosen must clear head height + ~20 px caption, not just the head height, or the caption stays hidden even if the input clears."

- timestamp: 2026-11-21T19:12:00Z
  checked: "All producers of the `#phone` fragment"
  found: |
    - accounts/list.html:119, :145, :185; accounts/partial_cards.html:67, :93, :128; accounts/partials/sync_status_card.html:102, :119, :143 — `link_button('Изменить' | 'Указать номер', '/accounts/{id}/groups#phone', variant='ghost')`
    - app/pages/account_groups.py:521 — no-JS save redirect `/accounts/{id}/groups#phone` (tests pin it as `…/groups?notice=phone_saved#phone`, tests/test_pages/test_account_phone_form.py:159, :317, :540)
  implication: "Both the card links AND the no-JS save redirect hit the same native fragment scroll; one CSS-level fix covers all ten producers. The htmx save path swaps #acct-phone in place (no navigation, no fragment scroll) and is unaffected."

- timestamp: 2026-11-21T19:15:00Z
  checked: "Why the head is 86 px on desktop but 172 px at 320/375 (base.html:229-246, app.css:485, 656-667, body line-height normal)"
  found: |
    Derived (CSS + line-height ≈ 1.3, matched to measurement):
    - Desktop (padding 18/32): 18 + [h1 22px ≈ 28.6 + gap 3 + subtitle 13px ≈ 16.9] + 18 + border 1 ≈ 86 ✓ (session pill ≈ 33 px sits beside, shorter than the titles).
    - ≤860 px (padding 14/16 !important): `flex-wrap: wrap` pushes `.head-actions` (session pill) to its own row; `h1.head-title` has NO nowrap/ellipsis (the single-line rules at app.css:2542-2560 apply only to `.chip__label` and `.acct-head__name`, i.e. the <h2>, not the shell <h1>); the fixed subtitle «Группы аккаунта: включение, удаление и повторная синхронизация» wraps. 14 + [h1 2 lines 57.2 + 3 + subtitle 2 lines 33.8] + row-gap 16 + pill ≈ 33 + 14 + 1 ≈ 172 ✓.
  implication: "Head height depends on viewport AND content (account-label length — e.g. «… +7 999 123-45-67 указан вручную» vs «Номер неизвестен» — changes h1 line count, ±≈28.6 px/line). A single literal offset tuned to 86 px fails on mobile; a mobile literal must be sized for the worst case or the head height must be made predictable/measured."

- timestamp: 2026-11-21T19:18:00Z
  checked: "Browser mechanism (HTML 'scroll to the fragment' + CSSOM View scroll-into-view; CSS Scroll Snap scroll-margin/scroll-padding)"
  found: |
    - Fragment navigation scrolls the target into view with block 'start' (top edge to the scrollport's top edge), then runs the focusing steps on a focusable target (observed: focus on #phone). The only author controls that shift this alignment are `scroll-margin-*` on the TARGET element and `scroll-padding-*` on the SCROLL CONTAINER being scrolled (here the document → `html`). WPT covers both for scrollIntoView and fragment navigation.
    - Corollary: `scroll-margin-top` on an ANCESTOR of the target (e.g. `[data-acct-phone]`) is not consulted when the fragment names a descendant (`#phone` input). Both 18-REVIEW.md WR-02 (`[data-acct-phone] { scroll-margin-top: … }`) and 18-UI-REVIEW.md:101 prescribe the rule on the container — as written, it would be inert.
    - Focus scrolling is 'if needed': the input is geometrically inside the viewport (0…45), so focus does not re-scroll; sticky obstruction is invisible to the browser unless declared via scroll-padding/margin.
  implication: "The missing piece is precisely an author-declared scroll offset. Reviews named the right property but the wrong element."

- timestamp: 2026-11-21T19:25:00Z
  checked: "git history (-S) and review disposition"
  found: |
    - Sticky head `[data-head] { position: sticky; top: 0; z-index: 5 }` since 150ea446 (2026-08-09, plan 01-01).
    - Phone form since fccee5ed (18-02); `#phone` card links since f64d05a2 (18-03).
    - 18-REVIEW-DISPOSITION.md: WR-02 `disposition: open` (not triaged, not fixed) at UAT time.
    - tests/test_pages/test_account_phone_links.py:154 docstring: «Якорь `#phone` браузер прокручивает сам» — the suite asserts only that exactly one `id="phone"` exists; no test touches scroll offset; no `scroll-margin`/`scroll-padding` anywhere in tests/.
  implication: "Defect shipped knowingly-open (WR-02) with no gate able to catch it; layout geometry is only observable in a browser."

## Resolution

root_cause: "Missing scroll offset for the sticky shell header. `app/static/css/app.css:656-657` makes `<header data-head>` (`app/templates/base.html:229`) `position: sticky; top: 0; z-index: 5` over the document scroller, but nothing compensates for it: there is no `scroll-padding-top` on the scroll container (`html`) and no `scroll-margin-top` on the fragment target `<input id=\"phone\">` (computed 0px; zero scroll-margin/scroll-padding rules in the whole stylesheet, no head-height token). Native fragment navigation to `/accounts/{id}/groups#phone` (9 card links + the no-JS save redirect) aligns the input's top edge with viewport y=0 and focuses it, so the input and its caption «Номер телефона» (~20 px above it) fall inside the head's box: 0…86 px desktop, 0…172 px at ≤860 px. Contributing: (a) the head's height is viewport- and content-dependent (shell <h1> and subtitle wrap and .head-actions drops to its own row at ≤860 px), so one literal offset cannot fit all widths; (b) the target is the input, not the caption, so a target-local offset must also clear ~20 px of caption; (c) the review's suggested fix puts scroll-margin-top on the ancestor `[data-acct-phone]`, which browsers do not consult for a descendant target."
fix: "(diagnose-only — not applied)"
verification: "(diagnose-only) Evidence: UAT live geometry at 1280×800 / 375×812 / 320×800, computed scrollMarginTop 0px, elementFromPoint→HEADER; static grep of app.css/templates/JS; git history."
files_changed: []

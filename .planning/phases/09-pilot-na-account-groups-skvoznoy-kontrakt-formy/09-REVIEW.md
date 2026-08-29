---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
reviewed: 2026-08-29T23:40:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - app/pages/account_groups.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/group_row.html
  - app/templates/account_groups/list.html
  - app/templates/account_groups/partials/count_rule_oob.html
  - app/templates/account_groups/partials/delete_response.html
  - app/templates/account_groups/partials/toggle_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/includes/htmx_error_banner.html
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 1
  warning: 8
  info: 4
  total: 13
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-08-29T23:40:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Ownership scoping in both converted handlers is sound: the triple `WHERE`
(`id` + `user_id` + `account_id`) is applied in `account_groups_toggle` and
`account_groups_delete` before any transport branching, the "missing group" and
"another user's group" paths are literally the same `return`, and the toggle
inverts rather than assigns. `_local_path` in the response layer blocks open
redirect / header injection on the `HX-Location` value. Session cookies are
`SameSite=lax`, so the new `hx-post` surfaces add no CSRF exposure. Autoescaping
is on for the two templates rendered directly off `templates.env`, and every
interpolated value in the new fragments is an `int` path parameter or an
escaped attribute value. No injection, secret, or authorization defect was found.

The defects are in the *consequences* of turning a full-page redirect into an
in-place fragment. The delete handler now mutates the list without re-rendering
the page, and the infinite-scroll sentinel keeps a now-stale absolute offset —
one group silently vanishes from the screen. Several of the phase's own
single-source and single-guard claims are contradicted by the shipped markup
(a third verbatim copy of the counter rule; two owners of `disabled` on the
modal confirm button; the modal's focus-return contract bypassed by the OOB
delete). One new test is green by construction, and two comments in
`test_htmx_gates.py` still describe the pre-Phase-9 world.

Full suite for the files in scope was executed: 373 passed in
`test_account_groups.py`, `test_htmx_markup_gates.py`, `test_components.py`,
`test_htmx_gates.py`, `test_shell.py`. Nothing below is a test failure — all of
it passes today.

## Critical Issues

### CR-01: htmx delete desynchronises the infinite-scroll sentinel — one group is silently dropped from the list

**File:** `app/pages/account_groups.py:498-523`, `app/templates/account_groups/partials/delete_response.html:44-46`, `app/templates/account_groups/list.html:202`

**Issue:**
Pagination is **absolute-offset** (`.offset(offset).limit(limit + 1)` in
`account_groups_partial`, and the sentinel is rendered once with
`offset={{ next_offset }}` baked into its `hx-get` URL). Before this phase the
delete handler always answered `302` and the whole page — including the
sentinel and its offset — was rebuilt. It no longer is: on the htmx path the
response only removes `#group-row-N`, removes `#group-del-N` and re-renders the
counter. The sentinel keeps its stale offset while the underlying result set
has shrunk by one row.

Concrete trace with `PAGE_SIZE = 30` and 35 groups `g1..g35`:

1. Page 1 renders `g1..g30`; sentinel URL is `...?offset=30&limit=30`.
2. User deletes `g5` over htmx. `total_groups` is 34, so the fragment branch is
   taken (`account_groups.py:488` is false) and only that one row is removed.
3. Sentinel fires: `offset=30` over the new 34-row ordering returns
   `g32, g33, g34, g35`.
4. **`g31` is never rendered.** The screen shows 33 of 34 groups, the counter
   line says "34 групп", and there is no error in the console, the status, or
   the body.

`_build_groups_query`'s own docstring names exactly this failure class
("постраничная загрузка смещением … начала бы дублировать одни строки и терять
другие") for the missing-`ORDER BY` case; the same loss is now reachable
through a legitimate user action. It is reachable on precisely the accounts the
search box was added for — Telegram accounts with hundreds of chats.

**Fix:** the delete response must repair the pagination cursor, not just the
row. Cheapest correct options, in order of preference:

1. Switch the partial to keyset pagination so the cursor cannot go stale:
   ```python
   # app/pages/account_groups.py
   after_id: int | None = Query(None, ge=1),
   ...
   q = _build_groups_query(user.id, account_id, term)
   if after_id is not None:
       q = q.where(Group.id > after_id)
   ```
   and render the sentinel with `after_id={{ last_group_id }}` in both
   `list.html:202` and `partial_cards.html:17` (they are already asserted
   identical by `test_sentinel_markup_is_identical_in_both_templates`).
2. Or ship the sentinel as a fourth OOB node of `delete_response.html`,
   replacing it by id with a decremented `offset`. This needs the sentinel to
   carry a stable `id` and re-introduces the same arithmetic in two places.

Whichever is chosen, add a regression test that seeds `PAGE_SIZE + 5` groups,
deletes one from the first page over htmx, then fetches the partial the
sentinel would fetch and asserts no id is missing from the union of both pages.

## Warnings

### WR-01: the counter-rule markup exists in a third, uncontrolled copy

**File:** `app/templates/account_groups/list.html:180-185` vs `app/templates/account_groups/partials/count_rule_oob.html:37-42`

**Issue:** The two blocks are byte-identical markup (`div.count-rule`, the two
`mono()` calls with the same three `plural_ru` forms, `span.count-rule__line`),
written out twice. `delete_response.html:33-36` and
`count_rule_oob.html:30-33` both assert that a second copy of this markup
"разошлась бы с первой молча"; `_group_counts`'s docstring
(`account_groups.py:126-128`) names the exact harm — "линейка после действия
отличалась бы от линейки после перезагрузки — молча". That harm is live: the
guarantee was implemented only between the *two responses*, not between the
responses and the page. Change the wording or a plural form in one file and the
counter after a toggle/delete says something different from the counter after
F5, with no gate to catch it (`OOB_BLOCKS` counts files carrying
`hx-swap-oob`, and `list.html` carries none).

**Fix:** make `list.html` render the same source. Extract the inner block to
e.g. `account_groups/includes/count_rule.html` and have both `list.html` and
`count_rule_oob.html` include it:
```jinja
{# account_groups/list.html #}
<div id="account-groups-count">{% include "account_groups/includes/count_rule.html" %}</div>
```
```jinja
{# account_groups/partials/count_rule_oob.html #}
<div hx-swap-oob="innerHTML:#account-groups-count">{% include "account_groups/includes/count_rule.html" %}</div>
```

### WR-02: two owners of `disabled` on the modal confirm button — the Alpine double-submit guard is disarmed on the htmx path

**File:** `app/templates/components/modal.html:132-139`

**Issue:** With `hx_post=true` the same button is driven by
`x-bind:disabled="sending"` (Alpine) *and* by
`hx-disabled-elt="find button[type=submit]"` (htmx). Verified against the
vendored `htmx.min.js` 2.0.10: `nn()` only sets `disabled` when the attribute
is absent and tags it `data-disabled-by-htmx`; `rn()` removes `disabled` when
that tag is present. Alpine 3 flushes `x-bind` effects on a microtask, so the
synchronous htmx submit listener always wins the race and owns the attribute.
Two consequences after a failed request (5xx or a `sendError` — the exact case
the new banner text was written for):

* htmx re-enables the button, but `sending` is still `true`, so
  `aria-busy="true"` stays on an enabled, idle button. `sending` is only reset
  in `show()`.
* The claim in the component header (`modal.html:54-61`) — "вторая отправка
  отменяется тем же обработчиком `x-on:submit`" — is no longer true here.
  Alpine's handler calls `$event.preventDefault()` and returns, but that does
  not stop htmx's own `submit` listener, which issues the request anyway.

**Fix:** hand the state back to Alpine when the request ends, so one owner
remains authoritative:
```html
<form class="modal__form" method="{{ method }}" action="{{ action }}"
      x-on:submit="if (sending) { $event.preventDefault(); return; } sending = true"
      {%- if hx_post %} x-on:htmx:after-request="sending = false"
      hx-post="{{ action }}" hx-swap="none" hx-disabled-elt="find button[type=submit]" hx-indicator="find .form-busy"{% endif %}>
```
and amend the header paragraph so it describes the htmx path too.

### WR-03: the modal's focus-return contract is bypassed by the OOB delete

**File:** `app/templates/account_groups/partials/delete_response.html:45`, `app/templates/components/modal.html:117-119`

**Issue:** The component's documented accessibility contract is "возврат фокуса
на элемент, который окно открыл", implemented in `hide()` via `this.opener`.
On the htmx delete path the panel is never hidden — it is removed from the
document by `hx-swap-oob="delete"`, so `hide()` never runs and `opener.focus()`
never fires. Worse, the opener itself (`#group-row-N`'s "Удалить" button) is
removed by the sibling OOB node in the same response. Focus is therefore
dumped onto `<body>` after every successful group deletion, and a keyboard user
restarts the tab order from the top of the document. `test_cancel_is_never_disabled`
and the focus-trap prose guard the modal's a11y contract while it is open;
nothing guards its teardown.

**Fix:** move focus deliberately before the row disappears — e.g. give
`[data-group-list]` (or the counter region, which always exists) `tabindex="-1"`
and focus it from the panel's own teardown, or emit a fourth OOB node that
carries `hx-swap-oob` on a focusable landmark. Record the chosen landing spot
in the component header next to the existing focus paragraph.

### WR-04: `test_repeated_delete_is_harmless_over_htmx` is green by construction

**File:** `tests/test_pages/test_account_groups.py:1284-1330`

**Issue:** The test seeds **one** group, so both deletes take the
`total_groups == 0` branch (`account_groups.py:488`) and answer `204` with an
empty body. Verified by instrumented run: `first=204 body=b'' second=204 body=b''`.
Every assertion is therefore trivially satisfied — `"<!DOCTYPE" not in ""`,
`b"" == b""`, `None == None` for `HX-Location`… no, both carry the same header,
but the header is identical for *any* two 204s on this route. The property the
docstring claims to guard — "тело собирается из `group_id` ПУТИ, а не из
найденной строки", i.e. that the *fragment* is byte-identical for a found and
an already-deleted group — is never exercised, because no fragment is produced.
The sibling test `test_delete_returns_oob_nodes` uses `_seed_many(..., ["Первая", "Вторая"])`
precisely to reach the fragment branch, so the authors knew the difference.

**Fix:** seed at least two groups so both requests land on the fragment branch,
and keep a positive assertion that a fragment was actually returned:
```python
seeded = await _seed_many(db_session, account, ["Первая", "Вторая"])
target = seeded[0]
first = await htmx_client.post(f"/accounts/{account.id}/groups/{target.id}/delete")
second = await htmx_client.post(f"/accounts/{account.id}/groups/{target.id}/delete")
assert first.status_code == 200, "фрагментная ветка не достигнута — утверждение о равенстве тел вакуумно"
assert f'id="group-row-{target.id}"' in first.text
assert first.content == second.content
```

### WR-05: `.form-busy` has no `display` and works only because both current callers happen to be flex containers

**File:** `app/static/css/app.css:1735-1740`, `app/templates/components/form_wrapper.html:87`, `app/templates/components/modal.html:136`

**Issue:** The indicator node is a `<span>`, i.e. `display: inline`, on which
`width: 8px; height: 8px; border-radius` have no effect. It renders today only
because `.modal__form` is `display: flex` (`app.css:960`) and
`[data-group-row] form[action$="/toggle"]` is `display: inline-flex`
(`app.css:2289`) — both blockify it as a flex item. The macro is explicitly
sold as "ОДИН класс на сорок семь форм вехи"; the 3rd..47th caller whose form
is not a flex container gets a 0×0 invisible dot, and the failure is silent —
no gate covers it (`_offenders_indicator_threshold` only inspects `transition`
delays on the two selectors).

**Fix:** make the component self-sufficient:
```css
.form-busy {
  display: inline-block;
  flex: none; width: 8px; height: 8px; border-radius: var(--r-pill);
  ...
}
```

### WR-06: deleting the last *visible* row under an active search leaves an empty card with no empty state

**File:** `app/pages/account_groups.py:486-496`

**Issue:** The "list is empty" branch is decided on `total_groups`, which is
account-wide and search-independent by design (`_group_counts` docstring:
"Поиск в подсчёт НЕ входит"). So when a search narrows the list to one row and
the user deletes it, `total_groups` is still > 0, the fragment branch is taken,
the row is removed in place, and the user is left staring at an empty
`[data-group-list]` card. The three deliberately distinguishable empty states
in `list.html:207-232` — including the one that offers "Сбросить" — are never
shown, and there is no way back to the unfiltered list except editing the URL.
The same hole applies to deleting the last row of the currently loaded page
when more pages exist.

**Fix:** decide the branch on what the *current view* would contain, not on the
account total, e.g. re-run `_build_groups_query(...).limit(1)` with the search
term carried in the form (a hidden `search` field on the confirm form, echoed
back into the `redirect=` URL so degradation also keeps the filter), and take
the `HX-Location` branch when the filtered result is empty. At minimum, record
the accepted gap in the handler docstring next to the `total_groups == 0`
comment, which currently reads as if it covered every emptying path.

### WR-07: two comments in `test_htmx_gates.py` still describe the pre-Phase-9 world

**File:** `tests/test_pages/test_htmx_gates.py:63-69`, `tests/test_pages/test_htmx_gates.py:791-795`

**Issue:** Both blocks assert, in the present tense, that G-2 passes vacuously —
"⚠️ G-2 СЕГОДНЯ ПРОХОДИТ ВАКУУМНО … До Фазы 9 множество переведённых пусто" and
"⚠️ СЕГОДНЯ УТВЕРЖДЕНИЕ ИСТИННО НИ НА ЧЁМ". Phase 9 removed
`account_groups_toggle` and `account_groups_delete` from `NOT_YET_CONVERTED`
(same file, lines 191-194 of the diff), so G-2 now has two subjects. The
chronicle entry at lines 244-254 even says so. In a codebase where the reader is
routinely told to trust the prose over re-deriving the fact, a comment that
tells the next reader "this gate proves nothing" about a gate that now proves
something is a defect, and it will make the Phase 10 author hesitate to rely on
G-2.

**Fix:** rewrite both paragraphs in the past tense and state the current
subject count, e.g. "До Фазы 9 множество переведённых было пусто и утверждение
было истинно ни на чём; с планами 09-01/09-02 у него два предмета — оба
обработчика экрана групп аккаунта."

### WR-08: the macro-definition exemption removes the action-address rules from every form the milestone converts, and nothing counts how many

**File:** `tests/test_templates/test_htmx_markup_gates.py:968-1001`, `tests/test_templates/test_htmx_markup_gates.py:1010-1028`

**Issue:** `_action_sites` skips every template in `MACRO_DEFINITION_SITES`, so
`test_every_action_path_is_a_declared_route`,
`test_no_action_path_leads_to_a_fragment_route` and
`test_no_action_is_assembled_from_an_unknown_value` now apply to exactly one
form in the tree — the legacy `ads/form.html` — as
`test_both_branches_of_the_editor_action_are_extracted` (`len(paths) == 2`)
confirms. The exemption is argued and counted
(`MACRO_DEFINITION_SITES_DECLARED = 2`), but the *number of forms hidden behind
it* is not: `PARAMETRIC_SWAP_TARGETS`/`DISABLED_ELT_EXCEPTIONS` count callers,
`MACRO_DEFINITION_SITES` does not. Phases 10-15 can add 45 more callers with
mistyped or fragment-route actions and every one of these four rules stays
green with the declared count unchanged at 2. The same shape applies to
`PARAMETRIC_SWAP_TARGETS`, which switches off G-9/G-11/G-12 for the milestone's
only real swap target.

**Fix:** add the caller-side half now rather than in Phase 10 — a small rule
that collects `action=` / `target=` argument values from
`_macro_callers(templates, "form_wrapper", "action")` (the scanner already
exists) and runs the existing `_literal_paths` / route checks over them. Failing
that, add an explicit declared count of *callers* hidden by
`MACRO_DEFINITION_SITES`, so growth is not silent.

## Info

### IN-01: unreachable `{% if total_groups %}` branch in the OOB counter node

**File:** `app/templates/account_groups/partials/count_rule_oob.html:37,42`

**Issue:** Neither handler can reach the false branch. `account_groups_toggle`
only renders the fragment when a group exists (`total_groups >= 1`), and
`account_groups_delete` diverts `total_groups == 0` to `HX-Location` before the
fragment is built. The guard is dead in both consumers today; it only mirrors
the (live) guard in `list.html`. Harmless, but it is one more reason the two
copies flagged in WR-01 look interchangeable when they are not.

**Fix:** keep the guard (it becomes live if the empty-list branch is ever
removed) but note in the header that it is unreachable from both current
responses, so a future reader does not assume the empty-counter path is tested.

### IN-02: the CSS justification for toggling `visibility` cites a screen-reader effect that cannot occur

**File:** `app/static/css/app.css:1710-1713`

**Issue:** "Одна `opacity` оставляет узел в дереве доступности: скринридер
прочитал бы «идёт запрос» там, где глазами ничего нет." The node is
`<span class="form-busy" aria-hidden="true"></span>` — it has no text content
and is already removed from the accessibility tree by `aria-hidden`. There is
nothing for a screen reader to announce in either state. The `visibility`
toggle is still worth keeping (it makes the element non-interactive and
non-searchable), but the stated reason is not the real one.

**Fix:** restate the reason as it actually is — `visibility` removes the node
from hit-testing and find-in-page while `opacity` alone does not — or drop
`aria-hidden` and give the span an `aria-live` label if the announcement is in
fact wanted.

### IN-03: the group-delete modal is ~22 px taller than the other fifteen

**File:** `app/templates/components/modal.html:136`, `app/static/css/app.css:960`

**Issue:** `.modal__form` is `display: flex; flex-direction: column; gap: 14px`,
so the `.form-busy` flex item contributes 8 px of height plus a 14 px gap
permanently (it is `visibility: hidden`, not `display: none`, by design). The
single panel that received `hx_post=true` therefore has a blank strip between
the body text and the buttons that the other fifteen do not. The header claims
the other fifteen render "байт-в-байт как до правки", which is true — but the
sixteenth is now visually inconsistent with them.

**Fix:** either accept and record it, or give the indicator a zero-height slot
in column layouts (`.modal__form .form-busy { position: absolute; }` inside a
positioned `.modal__actions`, or `margin-block: -11px`).

### IN-04: `test_billing_component_library_did_not_grow` now guards a number that has nothing to do with billing

**File:** `tests/test_pages/test_responsive_markup.py:1761-1768`

**Issue:** The test name scopes it to the billing screens, but the assertion it
carries counts every file in `app/templates/components/` and had to be bumped
15 → 16 for `form_wrapper.html`, which no billing screen uses. The duplicate
assertion in `test_template_inventory` (line 3127) is the one that belongs
there. The comment added by this phase documents the double bump, so the trap is
at least visible — but the misplacement is what makes the double bump necessary.

**Fix:** move the component-directory count out of the billing test into
`test_template_inventory` only, and leave the billing test asserting the billing
partial set it names.

---

_Reviewed: 2026-08-29T23:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

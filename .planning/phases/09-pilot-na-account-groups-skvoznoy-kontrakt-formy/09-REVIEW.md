---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
reviewed: 2026-08-31T09:06:39Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - app/pages/account_groups.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/count_rule.html
  - app/templates/account_groups/includes/group_row.html
  - app/templates/account_groups/includes/sentinel.html
  - app/templates/account_groups/list.html
  - app/templates/account_groups/partial_cards.html
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
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-08-31T09:06:39Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Reviewed the `account_groups` htmx pilot as it stands after the second gap-closure
round (plans 09-10 … 09-12). The full suite for the reviewed files passes
(277 tests). Ownership checks are re-done on every entry point (page, partial,
sync-status, toggle, delete), the triple `WHERE` is present on both state-changing
routes, the search term travels as a bind parameter, `_local_path` closes open
redirect / header injection / latin-1 on the `HX-Location` channel, and the
`samesite="lax"` session cookie covers cross-site POST. No injection, secret,
authz-bypass or escaping defect was found in the reviewed diff.

The defects that were found are all in the *new* machinery — the fourth
out-of-band node (cursor repair), the degradation paths of the two converted
handlers, and three factual claims in the prose that the vendored htmx 2.0.10
does not honour.

The most serious one (CR-01) is a regression the phase introduced with the very
node that was added to fix CR-01 of the previous round: the cursor repair rewrites
the sentinel with an **absolute** offset captured at request time, so a response
that lands after the sentinel has already advanced drags the cursor backwards and
duplicates a whole portion of rows (with duplicated DOM ids). Before plan 09-05
the sentinel could only ever move forward, so this failure mode did not exist.

Two owner decisions (`record-kind`, `conditional-include`) and two deferrals
(DEF-09-01, DEF-09-02) were treated as out of scope and are not re-reported. I
traced the `conditional-include` residual independently and confirm it is
cosmetic-only: in every state where the row's declaration is stale, no sentinel
exists, so `rendered_rows` is legitimately absent and no repair is owed.

## Critical Issues

### CR-01: Cursor repair rewrites the sentinel with a stale absolute offset — duplicates a whole portion and duplicates DOM ids

**File:** `app/pages/account_groups.py:629-633`, `app/templates/account_groups/partials/delete_response.html:68-70`, `app/templates/account_groups/includes/sentinel.html:53-59`

**Issue:**
`repaired_offset` is computed from `rendered_rows`, which is read out of the live
document **at the moment the delete request is sent**, and is then applied to
whatever `#group-list-sentinel` exists **at the moment the response is applied**,
unconditionally (`hx-swap-oob="outerHTML"`). Those two moments are not the same
moment, and the sentinel can advance in between:

1. Page 1 renders rows 0–29; sentinel `next_offset=30`, hidden `rendered_rows=30`.
2. User confirms a delete. `hx-include` captures `rendered_rows=30`. Request in
   flight (slow DB / slow link / mobile).
3. Still in flight, the user scrolls. `.modal` is `position: fixed; inset: 0`
   with **no body scroll lock** (`app/static/css/app.css`, `.modal` rule), so the
   list behind the overlay keeps scrolling and `hx-trigger="revealed"` fires. The
   partial returns rows 30–59 and replaces the sentinel with `next_offset=60`.
   The document now shows 60 rows.
4. The delete response lands and rewrites the sentinel to
   `offset = 30 - 1 = 29`. The new node is at the bottom of the list, i.e. in
   view, so htmx's `maybeReveal` fires it **immediately** on processing.
5. `GET /accounts/{id}/groups/partial?offset=29&limit=30` appends rows that are
   already on screen: ~30 duplicated rows, each carrying a duplicated
   `id="group-row-N"` / `id="group-del-N"`, and the counter rule now contradicts
   what is visible.

This is the mirror image of the defect plan 09-05 classified as a blocker
("МОЛЧА теряет одну группу"): silent, no console signal, no non-200 status — only
now the list gains rows instead of losing them, and it breaks id uniqueness,
which every other `hx-target`/`hx-swap-oob` on the screen depends on.

The same window is reachable in the other order (delete response first, stale
portion response second), where the stale portion swap targets a detached node and
its rows are simply lost.

The four-node docstring in `account_groups.py:619-633` and the header of
`delete_response.html` both reason about the *value* of the offset and never about
the *identity* of the node the value is applied to; nothing in the code or in the
gates asserts that the sentinel being replaced is the same sentinel the number was
read from.

**Fix (server-side, minimal):** stop treating the number as a free-floating
absolute and make the repair verifiable — send the offset the client actually had,
and refuse to repair when it no longer describes the document. Concretely, have
the sentinel also carry its own offset under a second name and reject the repair
unless they still agree, or (preferred, removes the class of bug entirely) drop
absolute offsets for a keyset cursor:

```python
# app/pages/account_groups.py — keyset instead of offset
# sentinel carries the id of the last rendered row; the portion route reads
# `after_id` instead of `offset`, so deleting a row above the cursor cannot
# shift it at all and no repair node is needed.
q = _build_groups_query(user.id, account_id, term)
if after_id is not None:
    q = q.where(Group.id > after_id)
rows = list((await db.execute(q.limit(limit + 1))).scalars().all())
```

**Fix (client-side, if the offset contract must stay):** serialise the two
requests so they cannot interleave — put the sentinel and the confirmation form in
one sync group, e.g. `hx-sync="closest [data-group-list]:queue last"` on the
sentinel macro and on the modal form when `hx_post` is set — and add a regression
test that asserts a delete response applied after a portion response does not lower
the sentinel offset.

## Warnings

### WR-01: A missing out-of-band target is **not** silent — htmx logs `console.error`, contradicting the invariant three files rely on

**File:** `app/templates/account_groups/partials/delete_response.html:12-19`, `app/templates/account_groups/list.html:169-178`, `app/pages/account_groups.py:414-420, 642-646`

**Issue:** Four separate places assert that an out-of-band node whose target is
absent "не находит узла и не делает НИЧЕГО — молча и безвредно", and `list.html`
states it explicitly as "молчать об этом он будет так же, как молчит о ненайденной
цели любого другого свопа". The vendored runtime does the opposite. In
`app/static/js/htmx.min.js` (2.0.10):

```js
} else { o.parentNode.removeChild(o); fe(te().body,"htmx:oobErrorNoTarget",{content:o,target:n}) }
// fe -> ae(..., {error: ...}) -> if (n.error) { H(n.error + ...) }  // H = console.error
```

So every OOB node with no target produces a `console.error` line. On the idle
delete path (foreign / nonexistent / already-deleted group) the response ships two
such nodes (`#group-row-N`, `#group-del-N`), i.e. two console errors per request.

This matters twice over. (a) It is the same class of defect that plans 09-10 and
09-11 were written to remove — the phase's own acceptance signal is "ответ 200 и
чистая консоль", and the walkthrough leans on it in three places. (b) A future
author reading `list.html:169-178` will believe that dropping the always-present
`#account-groups-count` wrapper degrades silently; it does not, and more
dangerously the reverse holds — someone adding a *new* OOB node whose target is
only sometimes present will believe they are safe.

**Fix:** correct the four prose claims to name the real behaviour
(`htmx:oobErrorNoTarget` → `console.error`), and either (i) make the idle path
emit no row/modal removal nodes — which cannot be done without breaking
indistinguishability — or (ii) register the idle-path console lines the same way
`INCLUDE_TARGET_EXCEPTIONS` registers the `hx-include` residual, with an assigned
phase, so the "clean console" criterion stays meaningful:

```python
# tests/test_pages/test_account_groups.py
OOB_TARGET_EXCEPTIONS = {
    "group-row-N/group-del-N (холостой путь удаления)": OobTargetException(
        assigned_phase="Фаза 15",
        reason="узлы снятия строки и панели уезжают и когда тройной WHERE не "
               "нашёл строки — этого требует неотличимость (D-04-A); цена — две "
               "строки htmx:oobErrorNoTarget в консоли на КРАФТЕД запрос",
    ),
}
```

### WR-02: The toggle handler ignores the submitted checkbox value and blindly inverts — the degradation path can flip the group opposite to what the form shows

**File:** `app/pages/account_groups.py:432`, `app/templates/account_groups/includes/group_row.html:176-182`

**Issue:** `group.is_active = not group.is_active` never reads the posted body,
while the form does post one (`components/toggle.html` renders
`<input type="checkbox" name="is_active" value="1">`). Before this phase that was
harmless: Alpine removed the "Применить" button unconditionally
(`<span x-init="$el.remove()">`) and submitted the form on every `change`, so one
change always equalled one inversion.

Plan 09-07 changed the removal condition to `x-init="if (window.htmx) $el.remove()"`
and moved the auto-submit to `hx-trigger="change"`. That creates a **new reachable
world — Alpine alive, htmx dead** (blocking `<script>` in `<head>` failed to load)
— in which the submit button survives and there is no auto-submit. In that world:

* user clicks the toggle on, then off (net: no change on screen), then clicks
  "Применить";
* the server inverts anyway, so the group ends up **enabled** while the control
  the user is looking at reads **disabled**.

Because D-05 makes the toggle the only way to exclude a group from dispatch
without deleting it, a silent inversion here means messages go to a chat the user
believes is switched off.

**Fix:** honour the payload; it is idempotent too, so QUAL-01 is not weakened:

```python
@router.post("/accounts/{account_id}/groups/{group_id}/toggle")
async def account_groups_toggle(
    request: Request,
    account_id: int,
    group_id: int,
    is_active: str | None = Form(None),   # присланное значение чекбокса
    ...
):
    ...
    # СОСТОЯНИЕ БЕРЁТСЯ ИЗ ФОРМЫ, А НЕ ИНВЕРТИРУЕТСЯ ВСЛЕПУЮ: у формы есть
    # настоящая кнопка отправки в мире «Alpine жив, htmx мёртв», и между
    # отрисовкой и отправкой чекбокс может смениться чётное число раз.
    # Повторный запрос по-прежнему безвреден — присвоение идемпотентно.
    group.is_active = is_active is not None
```

### WR-03: The no-Alpine delete path drops the active search filter that the htmx path preserves

**File:** `app/templates/account_groups/includes/group_row.html:190-193`, `app/pages/account_groups.py:68-89, 596-605`

**Issue:** `_screen_url()` documents the invariant that "адрес после действия и
адрес после перезагрузки обязаны приходить из одного источника", and the delete
handler builds the landing URL from the `search` field posted with the
confirmation form. But the *trigger* form — the one that carries the base path
when Alpine never boots — has no hidden `search` field:

```html
<form method="post" action="/accounts/{{ account_id }}/groups/{{ group.id }}/delete"
      x-data x-on:submit.prevent="$dispatch('modal-open-group-del-{{ group.id }}')">
  {{- button('Удалить', ...) -}}
</form>
```

so `search` arrives as `None`, `_clean_search` returns `None`, and the user is
redirected to the **unfiltered** list. Worse, the branch decision itself moves:
`_current_listing_has_a_row(..., search=None)` asks about the whole account rather
than the listing the user was actually looking at, so the "выдача опустела →
переход" branch — the entire point of the WR-06 fix — cannot fire for a filtered
list on the base path.

**Fix:** put the same hidden field on the trigger form, so both paths post the
same body:

```html
<form method="post" action="/accounts/{{ account_id }}/groups/{{ group.id }}/delete"
      x-data x-on:submit.prevent="$dispatch('modal-open-group-del-{{ group.id }}')">
  <input type="hidden" name="search" value="{{ filter_search }}">
  {{- button('Удалить', variant='ghost', icon='trash', title='Удалить группу') -}}
</form>
```

### WR-04: The scroll partial answers an expired session with a 302 to `/login`, so htmx splices a whole login page into the list

**File:** `app/pages/account_groups.py:289-291`

**Issue:** `account_groups_partial` returns `RedirectResponse("/login", 302)` when
the cookie is gone. The caller is the sentinel, `hx-get` + `hx-swap="outerHTML"`;
XHR follows the redirect transparently, so htmx receives 200 + the full login
document and swaps its body into the middle of the group list — including a second
`<form>` posting to `/login`, and a second copy of whatever ids `auth_base.html`
carries.

The module already knows this hazard and rejects it one route above:
`account_groups_sync_status:342-345` says in as many words that a redirect "вернул
бы в подменяемый блок целую страницу логина". The partial route was never given
the same treatment, and the phase's htmx-first framing makes it more reachable
(the sentinel is now the single source of that markup and fires on every scroll).

**Fix:** make the fragment route refuse like the status route does, or use the
answer layer so htmx gets a real navigation instead of a body:

```python
user = await get_user_from_cookie(request, db, settings)
if not user:
    # Фрагмента нет — слой отвечает 302 без htmx и 204 с заголовком перехода
    # с ним; целая страница логина в середину списка не приезжает никогда.
    return await respond(request, redirect="/login")
```

### WR-05: `PAGE_SIZE` is duplicated as a literal `limit=30` inside the sentinel macro

**File:** `app/templates/account_groups/includes/sentinel.html:54`, `app/pages/account_groups.py:35`

**Issue:** the page size lives twice — `PAGE_SIZE = 30` in Python and `&limit=30`
hard-coded in the sentinel URL. The whole cursor arithmetic of this phase rests on
"число отрисованных строк = смещение следующей порции", and the sentinel file
spends a paragraph saying so; that invariant is currently kept by a literal that
no test and no import ties to `PAGE_SIZE`. The route clamps `limit` to `le=100`,
so a `PAGE_SIZE` raised above 100 would additionally start returning 422 on every
scroll. Changing `PAGE_SIZE` today silently produces a first page of N rows
followed by portions of 30.

**Fix:** pass the page size into the macro from the context the route already
controls, instead of writing it in the template:

```python
# route context
"page_size": PAGE_SIZE,
```
```jinja
{%- macro sentinel(account_id, next_offset, filter_params, page_size, oob=false) -%}
{%- set url %}/accounts/{{ account_id }}/groups/partial?offset={{ next_offset }}&limit={{ page_size }}...
```

## Info

### IN-01: `delete_response.html` header says "тремя узлами" and then lists four

**File:** `app/templates/account_groups/partials/delete_response.html:4-10`

**Issue:** plan 09-05 added the cursor-repair node and updated the enumeration but
not the count in the sentence above it. `account_groups.py:636` correctly says
"Четыре внеполосных узла". In a codebase where node counts are load-bearing
constants (`OOB_BLOCKS = 10`, `REVEALED_PLACES = 12`), a header that under-counts
its own file is exactly the kind of drift the surrounding gates exist to prevent.

**Fix:** `... он делает ВНЕПОЛОСНО, ЧЕТЫРЬМЯ узлами верхнего уровня:`.

### IN-02: A crafted cross-account delete removes a live row from the screen and swaps in another account's counter

**File:** `app/pages/account_groups.py:642-661`, `app/templates/account_groups/partials/delete_response.html:12-19`

**Issue:** the response body is built from the **path** `group_id` and `account_id`
regardless of whether the triple `WHERE` matched. The file states this is "молча и
безвредно" because a nonexistent id finds no node. That holds only when the id is
absent from the document. A user viewing account A who posts
`/accounts/B/groups/42/delete` (both accounts theirs, group 42 belongs to A) gets a
response that deletes the *live* `#group-row-42` and `#group-del-42` from account
A's page and replaces the counter rule with **account B's** numbers — while group
42 is still in the database.

No privilege boundary is crossed (both accounts belong to the caller, and the
"неотличимость" argument about status/body/headers is unaffected), so this is
informational rather than a security finding; the defect is that the stated
invariant is broader than what the code delivers, and a reader will carry the
broad version forward.

**Fix:** narrow the claim in the docstring and in the template header to
"идентификатор, ОТСУТСТВУЮЩИЙ в документе, не находит узла", and note that a
present-but-not-deleted id removes a live row.

### IN-03: `_group_counts` runs two COUNT queries on the delete path that discards them

**File:** `app/pages/account_groups.py:594, 607-617`

**Issue:** `active_groups, total_groups` are computed before
`_current_listing_has_a_row`, so on the "listing emptied → HX-Location" branch both
counts are executed and thrown away. The toggle handler deliberately defers the
same work into the async `_fragment` closure for exactly this reason
(`account_groups.py:442-446`: "на пути без htmx разметка не собирается вовсе, то
есть два лишних запроса подсчёта не выполняются"). The delete handler does not
follow its own sibling's rule.

**Fix:** move the two counts inside `_fragment`, matching the toggle handler.
`_current_listing_has_a_row` runs first either way, so no ordering guarantee is
lost.

---

_Reviewed: 2026-08-31T09:06:39Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

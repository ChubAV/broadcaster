---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-03T00:00:00Z
depth: standard
files_reviewed: 23
files_reviewed_list:
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/history.py
  - app/pages/schedules.py
  - app/templates/account_groups/includes/group_row.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/sched_count_rule.html
  - app/templates/ads/partials/sched_delete_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/includes/notice_area.html
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 1
  warning: 9
  info: 0
  total: 10
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-09-03
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

The phase does two things: it makes the htmx attributes on `components/modal.html` unconditional
(all 18 confirmation panels now submit over htmx) and it converts eight route handlers from
`RedirectResponse` to `respond()`.

Verified clean:

* **All nine routes reachable from a `modal()` call site go through `respond()`.** I enumerated
  every `modal(...)` caller in the template tree and mapped each `action=` to its handler:
  `accounts_delete`, `ads_delete`, `schedules_delete`, `account_groups_delete` (phase 9),
  `admin_delete_user`, `admin_impersonate`, `admin_drop_task`, `admin_restart_worker`,
  `history_retry`. None of them is left on the `NOT_YET_CONVERTED` backlog, so the phase does not
  ship a panel that posts over htmx to a handler that answers 302 — the failure mode the phase was
  designed to avoid.
* **The `schedules.py` ownership invariant holds.** `_ad_id_from_form()` is used strictly as a
  fallback (`ad_id = ad_id if ad_id is not None else _ad_id_from_form(form_data)`), the found row
  wins whenever it exists, and both the branch predicate (`_ad_has_a_schedule`) and the counter
  (`_ad_schedule_count`) scope through `join(Ad) … Ad.user_id == user.id`. The form value is coerced
  to `int` before it can reach `_editor_url`, so it cannot influence the landing URL beyond an
  integer. No authorization decision reads the form. There is **no Critical finding here.**
* `admin_impersonate` attaches the cookie to the object returned by `respond()`, so the cookie rides
  the 204 on the htmx path and the 302 on the degradation path. `set_session_cookie` works on both
  `Response` and `RedirectResponse`. The ordering is correct.
* `delete_account`, `ads_delete`, `schedules_delete` all scope their `WHERE` by owner; the origin
  guard (`is_same_origin`) accepts XHR because browsers send `Sec-Fetch-Site`/`Origin` on
  cross-origin and same-origin POSTs alike.

What is **not** clean: the new success branch in the modal's `htmx:after-request` expression is
inoperative on the transport that 16 of the 18 panels actually use, and the test that claims to
prove it feeds the expression an event shape that real htmx never produces. Several docstrings in
this phase assert runtime behaviour that contradicts the vendored runtime or the code beneath them —
in a codebase where prose is treated as a load-bearing contract, that is a defect, not a nit.

---

## Critical Issues

### CR-01: `$event.detail.successful` is never set on the `HX-Location` transport — the "close only on success" branch is dead for 16 of 18 panels

**File:** `app/templates/components/modal.html:467`
**Also:** `app/pages/htmx.py:location_response` (the 204 producer), `tests/test_templates/test_components.py:1759-1762, 2210`

The new expression is:

```html
x-on:htmx:after-request="sending = false; if ($event.detail.successful) hide()"
```

Traced through the vendored runtime (`app/static/js/htmx.min.js`, 2.0.10), `handleAjaxResponse`
(minified `Vn`) has this shape:

```js
function Vn(t,e){ const n=e.xhr; …
  if(!ae(t,"htmx:beforeOnLoad",e))return;
  if(T(n,/HX-Trigger:/i)){…}
  if(T(n,/HX-Location:/i)){ … Nn("get",e,s); return }   // <-- early return
  …
  if(!ae(r,"htmx:beforeSwap",m))return;
  …
  e.target=r; e.failed=a; e.successful=!a;              // <-- only assignment
```

`successful` is assigned **only after** the `HX-Location` early return. `htmx:afterRequest` is then
fired from `xhr.onload` with that same object (`ae(r,"htmx:afterRequest",T)`), so on every
`HX-Location` response `$event.detail.successful` is `undefined` → falsy → `hide()` is never called.

`respond()` produces exactly that response for every non-fragment branch
(`location_response()` → 204 + `HX-Location`), which is **every confirmation route in the phase
except the one fragment branch of `schedules_delete`**. Consequences:

1. `this.open` stays `true` and `document.documentElement.classList.remove('is-modal-open')` (the
   scroll lock) is never executed by `hide()`. Cleanup depends entirely on Alpine's `destroy()`
   firing when htmx's follow-up `GET` replaces `<body>`.
2. If that follow-up `GET` does not complete — network drop, 5xx from the landing page, a landing
   page that fails its own `responseHandling` rule (`[45]..` is `swap:false`) — the body is never
   swapped, `destroy()` never runs, and the user is left with a confirmation dialog frozen on top of
   a stale screen with `<html>` scroll-locked and no way out except Escape or the overlay.
3. The phase contract D-12 ("панель закрывается только при успешном обмене") is therefore
   unimplemented on 16 of 18 sites: the panel is removed by the body swap, not by the success
   branch, and the "stays open on failure" property that the milestone forbids trading away is
   accidental rather than expressed.

The accompanying gate does not catch this because it synthesises the event:

```python
# tests/test_templates/test_components.py:1759
function afterRequest(panel, successful) {
  const handler = new Function('$event', 'with (this) { ' + AFTER_REQUEST + ' }');
  handler.call(panel, { detail: { successful: successful } });
}
```

`{ detail: { successful: true } }` is a shape htmx never delivers on this path, so
`test_the_panel_closes_only_on_a_successful_exchange` is green against a fiction.

**Fix:** read a value htmx actually sets on both paths. The xhr is always present on
`htmx:afterRequest`:

```html
x-on:htmx:after-request="sending = false; if ($event.detail.xhr && $event.detail.xhr.status &gt;= 200 &amp;&amp; $event.detail.xhr.status &lt; 400) hide()"
```

If the "no second definition of success" rule must be preserved literally, keep
`$event.detail.successful` **and** add the `HX-Location` case explicitly, with the early return
named in a comment so the next reader does not "simplify" it back:

```html
x-on:htmx:after-request="sending = false; if ($event.detail.successful || $event.detail.xhr.getResponseHeader('HX-Location')) hide()"
```

Whichever form is chosen, the JS-interpreter gate must be re-pointed at the real event shapes: feed
it `{ detail: { xhr: {status: 204, getResponseHeader: () => '/ads'} } }` (no `successful` key) for
the location transport and `{ detail: { successful: true, xhr: {status: 200} } }` for the fragment
transport. As written the gate cannot distinguish a working panel from this one.

---

## Warnings

### WR-01: `schedules_delete` docstring claims a `return_to` guard that the code does not contain

**File:** `app/pages/schedules.py:942-962`

The comment on the redirect branch says:

> Вторая — ЗАЩИТНАЯ: признак возврата в редактор не пришёл, или `ad_id` неизвестен

The condition is `if not await _ad_has_a_schedule(db, user.id, ad_id):`. It never inspects
`return_to`. A POST that carries `HX-Request` but no `return_to` (or `return_to` set to anything
else) against a schedule of an ad that still has siblings takes the **fragment** branch: `screen_url`
is computed as `/schedules`, discarded, and the response ships three OOB nodes (`#sched-N`,
`#sched-del-N`, `innerHTML:#sched-count`) that have no targets on the summary screen — three
`htmx:oobErrorNoTarget` / `console.error` lines and zero visible effect, which is exactly the
"ответ 200 и чистая консоль" diagnostic the milestone relies on.

**Fix:** either make the guard match the prose —

```python
if form_data.get("return_to") != RETURN_TO_EDITOR or not await _ad_has_a_schedule(
    db, user.id, ad_id
):
    return await respond(request, redirect=screen_url)
```

— or correct the comment to say the branch is driven solely by "у объявления не осталось расписаний"
and that a missing `return_to` produces a fragment aimed at a screen that cannot receive it.

### WR-02: the unconditional `.form-busy` node adds ~22 px of dead space to 17 confirmation panels

**File:** `app/templates/components/modal.html:470`

```html
<span class="form-busy" aria-hidden="true"></span>
```

`app/static/css/app.css:1782` styles it `display: inline-block; width: 8px; height: 8px;
opacity: 0; visibility: hidden;` — `visibility: hidden` **retains the layout box**. The parent is
`app/static/css/app.css:980`: `.modal__form { display: flex; flex-direction: column; gap: 14px; }`.
Every panel therefore gains an invisible 8 px flex item plus a 14 px gap between the body text and
the action row. Until this phase that cost was paid by one panel (the group row); it is now paid by
all 18, on a phase that otherwise claims the remaining sites are "байт-в-байт прежними" apart from
the htmx attributes.

**Fix:** absolutely position the indicator or collapse it when idle, e.g.

```css
.form-busy { position: absolute; }            /* with .modal__form { position: relative } */
/* or */
.form-busy { height: 0; margin: 0; }
.form-busy.htmx-request { height: 8px; }
```

### WR-03: `modal()` still takes `method=` but the htmx path is hard-coded to POST

**File:** `app/templates/components/modal.html:444, 466-467`

```jinja
{% macro modal(id, title, action, confirm_label, …, method="post") -%}
  <form … method="{{ method }}" action="{{ action }}"
        … hx-post="{{ action }}" …>
```

Now that the attribute is unconditional, a caller passing `method="get"` gets a GET without
JavaScript and a POST with it — the exact base-path/enhanced-path divergence the response layer
exists to make inexpressible. The parameter has no non-`post` caller today, so this is latent, not
live; but leaving a divergence-producing knob on a macro that has just had its other knobs removed
for precisely this reason is inconsistent.

**Fix:** either drop the parameter (all 11 call sites use the default or pass `"post"` explicitly),
or derive the attribute: `hx-{{ method }}="{{ action }}"`.

### WR-04: the "all confirmation routes" traversal is a hand-maintained list with a hard-coded count, and it is already incomplete

**File:** `tests/test_pages/test_confirm_delete_transport.py:1-10, 587, 838`

The module docstring promises:

> маршрут, добавленный будущей фазой за панелью подтверждения, не уронил бы ни одной из них …
> Параметризованный обход превращает это в КРАСНОЕ

It does not. `CONFIRMED_DELETE_ROUTES` is a literal tuple and
`CONFIRMED_DELETE_ROUTES_DECLARED = 8` is a literal integer; nothing derives either from the
template tree. A new modal-backed route reddens `test_modal_site_inventory`
(`MODAL_CONSUMERS`/`MODAL_PLACES` in `tests/test_templates/test_components.py`) but leaves this
traversal green and the new route unproven on both transports. The gap is not hypothetical:
`app/pages/account_groups.py::account_groups_delete` is a live route behind a `modal()` panel and is
absent from the registry, while the header claims the module covers "ВСЕХ МАРШРУТОВ, СТОЯЩИХ ЗА
ПАНЕЛЬЮ ПОДТВЕРЖДЕНИЯ".

**Fix:** derive the expected route set from the modal inventory instead of asserting a constant —
parse `action=` out of every `modal(` call site (the machinery already exists in
`tests/test_pages/test_htmx_gates.py:1131 _PANEL_CALL`), resolve each to its handler, and assert
that set equals the registry's keys. Failing that, add `account_groups_delete` and narrow the
docstring to "маршруты, переведённые Фазой 10".

### WR-05: `_with_notice()` splits on `?` only and will bury the notice inside a URL fragment

**File:** `app/pages/htmx.py` (`_with_notice`), consumed via `app/pages/schedules.py:940`

```python
separator = "&" if "?" in redirect else "?"
return _local_path(f"{redirect}{separator}{NOTICE_QUERY_KEY}={notice}")
```

`_editor_url()` (`app/pages/schedules.py:254-283`) returns
`/ads/{ad_id}/edit?sched={sid}#sched-{sid}` whenever `schedule_id` is supplied. The moment any
caller passes such a URL to `respond(..., notice=...)` the result is
`/ads/1/edit?sched=2#sched-2&notice=…` — the code lands inside the fragment identifier, the landing
page never sees the parameter, and the outcome disappears silently. `_local_path()` does not reject
`#`, so nothing catches it. Today only `schedules_delete` calls `_editor_url` on the `respond` path
and it passes `schedule_id=None`, so this is one refactor away rather than live.

**Fix:** make the assembly fragment-aware, and keep the failure loud:

```python
path, sep, fragment = redirect.partition("#")
separator = "&" if "?" in path else "?"
return _local_path(f"{path}{separator}{NOTICE_QUERY_KEY}={notice}{sep}{fragment}")
```

### WR-06: the recorded justification for choosing `#notice` as the focus landing zone is false for error notices

**File:** `app/templates/includes/notice_area.html:88-91`, `app/templates/components/modal.html:453`

The record says:

> На отказном пути он приземляется точно на текст отказа, и там выбор окупается целиком.

`land()` focuses `document.getElementById('notice')`. But `includes/notice_oob.html` routes every
record whose `variant == 'error'` into `#notice-alert`, and only `#notice` received `tabindex="-1"`
(deliberately — "вторая фокусируемая область немедленно поставила бы вопрос, какая из них
площадка"). So on an error outcome the focus lands on an empty polite region while the text the user
needs sits in a sibling that cannot be focused. The two decisions are individually defensible and
jointly contradictory.

**Fix:** either land on whichever region actually received content
(`document.querySelector('#notice-alert:not(:empty)') || document.getElementById('notice')`), or
strike the "приземляется точно на текст отказа" sentence and record that error notices are announced
by `aria-live="assertive"` rather than by focus.

### WR-07: the documented attribution of the two landing branches is inverted against the real runtime

**File:** `app/templates/components/modal.html:57-63`

The record states:

> узел уехал вместе со строкой → `destroy()`, потому что на фрагментном пути `hide()` не вызывается
> ВОВСЕ: событие после запроса приходит ПОСЛЕ свопа, то есть после того, как внеполосный узел уже
> снял панель вместе с её формой.

Detaching a node does not remove its listeners. In the shipped runtime the OOB `delete` happens
synchronously inside `swap()` (default `swapDelay` 0), `htmx:afterRequest` is dispatched later in
the same synchronous task (`xhr.onload` → `ae(r,"htmx:afterRequest",T)`), and Alpine 3 tears the
component down from a `MutationObserver` callback, i.e. in a **microtask after** that task. So on the
fragment path `hide()` *does* run — it is `destroy()`'s landing branch that is dead there
(`if (this.open)` is already false). Combined with CR-01, the shipped truth is the mirror image of
the record: `hide()` fires only on the fragment path, `destroy()` lands only on the location path.

**Fix:** correct the record once CR-01 is fixed, and make the behavioural gate assert the branch
*attribution* (which of the two ran), not just the final focus position — otherwise the two branches
remain interchangeable to the test and the record stays unverifiable.

### WR-08: `schedules_delete` parses the request body after it has already committed the deletion

**File:** `app/pages/schedules.py:911-928`

```python
schedule = result.scalar_one_or_none()
ad_id = schedule.ad_id if schedule else None
if schedule:
    await db.delete(schedule)
    await db.commit()
form_data = await request.form()          # <-- after the commit
```

`await request.form()` can raise (malformed multipart boundary, oversized part, disconnect
mid-body). When it does, the row is already gone but the client receives a 500. With the panel now
posting over htmx and staying open on failure (CR-01 notwithstanding), the natural user response is
to press "Удалить" again against a row that no longer exists. Every other input this handler needs
(`return_to`, `ad_id`) is read from that same body, so there is no ordering constraint forcing the
current sequence.

**Fix:** hoist the parse above the mutation:

```python
form_data = await request.form()
result = await db.execute(...)
schedule = result.scalar_one_or_none()
ad_id = schedule.ad_id if schedule else None
if schedule:
    await db.delete(schedule)
    await db.commit()
```

### WR-09: Escape and the overlay dismiss the panel while a destructive request is in flight

**File:** `app/templates/components/modal.html:459, 462`

```html
x-on:keydown.escape.window="hide()"
<div class="modal__overlay" x-on:click="hide()"></div>
```

Neither consults `sending`. The submit button is disabled by `hx-disabled-elt`, but Escape or an
overlay click closes the panel mid-request; the XHR continues and completes against a component
whose `open` is already `false`, so the success branch short-circuits and, for the routes that emit
no notice on success (`ads_delete`, `accounts_delete`, `schedules_delete` — D-03), the user gets no
signal at all that the irreversible action ran. On a failure the panel that D-12 promises will stay
open is gone. This was a one-site behaviour in phase 9; the phase multiplies it by 18 without
revisiting it.

**Fix:** gate the dismissal on the in-flight state, matching the existing submit guard:

```html
x-on:keydown.escape.window="if (!sending) hide()"
<div class="modal__overlay" x-on:click="if (!sending) hide()"></div>
```

### WR-10: the fragment response overwrites `#sched-count` with a foreign ad's schedule count

**File:** `app/templates/ads/partials/sched_delete_response.html:73`, `app/pages/schedules.py:964-1006`

The docstring for `_fragment()` enumerates the cross-ad case honestly for the two removal nodes:

> Человек, у которого на экране открыт редактор объявления A, может послать удаление расписания,
> принадлежащего его же объявлению B … узлы снимут со страницы A ЖИВЫЕ `#sched-N` и `#sched-del-N`.

It omits the third node. `_ad_schedule_count(db, user.id, ad_id)` is computed for ad **B**, and
`<div hx-swap-oob="innerHTML:#sched-count">` writes it into ad **A**'s counter, which then disagrees
with the cards visible on screen until the next reload — the precise "человек видел бы РАЗНОЕ число"
failure that `sched_count_rule.html` was extracted to prevent. Owner-scoped and self-inflicted, so
not a privilege issue, but the counter is the one node whose whole justification is that it can
never disagree with the screen.

**Fix:** either extend the omitted sentence to name the counter (cheapest, keeps the record true),
or drop the counter node when `_editor_url`'s ad id does not match the ad whose editor issued the
request — which requires the `return_to`/`ad_id` pair to be checked against the found row, i.e. the
same guard WR-01 asks for.

---

_Reviewed: 2026-09-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

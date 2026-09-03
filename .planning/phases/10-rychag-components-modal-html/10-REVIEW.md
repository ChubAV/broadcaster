---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-03T22:51:14Z
depth: standard
head: 0ea886d
diff_base: 576cef07
files_reviewed: 26
files_reviewed_list:
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/history.py
  - app/pages/schedules.py
  - app/templates/account_groups/includes/group_row.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/ad_card.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/sched_count_rule.html
  - app/templates/ads/partials/sched_delete_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/history/includes/history_card.html
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
  critical: 3
  warning: 6
  info: 0
  total: 9
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-09-03T22:51:14Z
**Depth:** standard
**Files Reviewed:** 26
**Status:** issues_found

## Summary

This round re-checked the six findings of the prior review against the code at
`0ea886d` and then reviewed the phase's own delta (`576cef07..HEAD`) adversarially.

**Prior-round disposition (verified against current code, not against the plans):**

| Prior | Verdict | Evidence |
| --- | --- | --- |
| `CR-01` (blocker) — `_ad_id_from_form` bounded type, not magnitude | **Closed for the field it named, but the route it was reproduced on still 500s.** See `CR-01` below. | `app/pages/schedules.py:305-307` now clamps `1 .. _AD_ID_MAX`; reproduced 500 remains on the same route via the path id. |
| `WR-01` — response shape decided by a different predicate than the landing address | **Closed.** Both now read the single `returns_to_editor` value. | `app/pages/schedules.py:998,1003,1008` |
| `WR-02` — docs claimed a focus-landing payoff on a failure path that did not exist | **Closed** as prose; the underlying accessibility hole is now stated but shipped. See `WR-03`. | `app/templates/includes/notice_area.html:95-115` |
| `WR-03` — form verb parameter live while the submit attribute was hardcoded | **Closed.** `method` parameter removed from the signature; all five callers updated. | `app/templates/components/modal.html:656,677` |
| `WR-04` — after-request handler fires on ANY htmx request from the block-call slot | **Not closed — mitigated by a markup-only inventory, and the blast radius grew 1 → 18 in this same phase.** See `WR-01`. | `app/templates/components/modal.html:275-281,679` |
| `WR-05` — `_fragment` docstring's exclusion list covered two of three response nodes | **Closed for the docstring; the register the docstring points at contains none of the three nodes.** See `WR-02`. | `tests/test_pages/test_account_groups.py:4897-4933` |

**New findings.** The phase converted eight handlers from `RedirectResponse` to
`respond()` and made `hx-post` unconditional on all 18 confirm sites. That
combination turned nine POST routes into `204 + HX-Location` responses whose
follow-up GET replaces `document.body` — a transport that, before this phase,
only reached the account-groups screens. Three defects follow from that and from
an incomplete application of the phase's own `CR-01` fix. All three criticals
were reproduced by running the application, not inferred.

---

## Critical Issues

### CR-01: The route the closed blocker was reproduced on still returns HTTP 500 — the fix bounded the form field but not the path identifier

**File:** `app/pages/schedules.py:967` (query), `app/pages/schedules.py:951-957` (signature)

**Issue:**
The closed blocker was reproduced as "`POST /schedules/{id}/delete`, body
`return_to=editor&ad_id=` and twenty-five nines" — and the fix
(`_ad_id_from_form`, lines 301-307) bounds exactly that field. But the *same
handler*, twenty-six lines earlier, feeds an unbounded path parameter into the
same kind of comparison:

```python
schedule_id: int,            # line 954 — no bound
...
result = await db.execute(   # line 967
    select(Schedule)
    .join(Ad, Schedule.ad_id == Ad.id)
    .where(Schedule.id == schedule_id, Ad.user_id == user.id)
)
```

Reproduced against the running app (authenticated session, no htmx header):

```
POST /schedules/9999999999999999999999999/delete
  body: return_to=editor&ad_id=1
→ 500  OverflowError: Python int too large to convert to SQLite INTEGER
       at app/pages/schedules.py:967
```

This is the identical failure mode, the identical driver exception, the identical
route, and the identical stated invariant — the module's own rule, written at
`app/pages/schedules.py:37-47`, is that an out-of-column-range value is discarded
*before* the query so it "does not crash the query in the driver". The rule is
enforced at one call site out of five in the file.

The docstring at `app/pages/schedules.py:270-293` makes this worse rather than
better: it asserts, in point (в), that the bound is taken "по верхней границе
КОЛОНКИ" and "СТОИТ ДО ЗАПРОСА", and in point (г) names the reproducing request
by route. A reader is told the route is covered. It is not.

The guarding test never probes the path id — `MISSING_SCHEDULE_URL` is hardcoded
to `"/schedules/999999/delete"`
(`tests/test_pages/test_confirm_delete_transport.py:2272`), safely inside int32,
so the whole `UNUSABLE_AD_ID_VALUES` matrix runs against an in-range path.

**Fix:** Reject out-of-column-range identifiers at the boundary rather than at one
hand-picked field. Either constrain the path parameter declaratively —

```python
from fastapi import Path

AD_ID_MAX = 2_147_483_647  # promote _AD_ID_MAX to the module's public bound

@router.post("/schedules/{schedule_id}/delete")
async def schedules_delete(
    request: Request,
    schedule_id: int = Path(..., ge=1, le=AD_ID_MAX),
    ...
):
```

— which turns the 500 into FastAPI's 422 before the handler body runs, or add a
single shared coercion helper used by every identifier that reaches a comparison,
and extend `UNUSABLE_AD_ID_VALUES` coverage to the *path* as well as the body:

```python
MISSING_SCHEDULE_URL = "/schedules/999999/delete"
OUT_OF_RANGE_SCHEDULE_URL = "/schedules/" + "9" * 25 + "/delete"   # currently 500
```

---

### CR-02: Four sibling routes in the same file carry the identical unbounded-identifier 500

**File:** `app/pages/schedules.py:730` (`ad_id`), `:737` (`account_id`), `:822` (`schedule_id`), `:823` (`ad_id`), `:826` (`account_id`), `:903` (`schedule_id`)

**Issue:**
`_AD_ID_MAX` was introduced as a module-level rule but applied to one helper. Every
other identifier in the module that reaches a SQL comparison is still `int` with no
magnitude bound. All four reproduced against the running app:

| Request | Result | Crash site |
| --- | --- | --- |
| `POST /schedules/new` body `ad_id=<25 nines>` | **500** OverflowError | `schedules.py:476` via `_ownership_verdict` → `_owns_ad` |
| `POST /schedules/new` body `ad_id=<valid>&account_id=<25 nines>` | **500** OverflowError | `schedules.py:476` |
| `POST /schedules/<25 nines>/edit` body `ad_id=<valid>` | **500** OverflowError | `schedules.py:834` |
| `POST /schedules/<25 nines>/toggle` | **500** OverflowError | `schedules.py:911` |

The module's own comment (`:37-47`) declares this exact behaviour forbidden on a
"форменный POST" and cites `T-02-24` / `T-02-25`. On PostgreSQL these surface as
`DataError` out of int32 range, per the same comment — i.e. production is affected
identically, not just the SQLite suite.

Two of these are worse than the delete route, because `_ownership_verdict` runs
*before* any write and the 500 therefore aborts the ownership decision itself: the
failure mode is "authorization check crashed", not "lookup returned nothing".

**Fix:** Apply one bound at one place rather than five. Declare the column bound
once and use FastAPI's own validation on every identifier that reaches SQL:

```python
# app/pages/schedules.py
ID_MAX = 2_147_483_647          # upper bound of the identifier COLUMN (int32)
AdId = Annotated[int, Path(ge=1, le=ID_MAX)]
AdIdForm = Annotated[int, Form(ge=1, le=ID_MAX)]
AccountIdForm = Annotated[int | None, Form(ge=1, le=ID_MAX)]
```

then use `AdIdForm` / `AccountIdForm` / `AdId` in `schedules_create`,
`schedules_update`, `schedules_toggle` and `schedules_delete`. A `422` on a
hand-crafted body is the outcome the module already says it wants; nothing
reachable from the UI changes, because every id the UI sends is a real primary key.

Then add a gate that scans `app/pages/schedules.py` for identifier parameters
lacking a bound, so the sixth one does not ship unbounded either.

---

### CR-03: The new `HX-Location` transport re-executes the ad-editor's inline script, killing all of the editor's JavaScript after a routine delete

**File:** `app/pages/schedules.py:1042` (the response), `app/templates/ads/form.html:307-322` (the victim)

**Issue:**
Before this phase, `schedules_delete` returned a plain `302`
(`git show 576cef07:app/pages/schedules.py`) — a full document navigation. It now
returns `204 + HX-Location`, verified end to end:

```
POST /schedules/1/delete   (HX-Request: true, return_to=editor, ad_id=1)
→ 204   HX-Location: /ads/1/edit   body length 0
```

That is the redirect branch — the one taken when the ad has **no schedules left**,
i.e. the ordinary "delete my only schedule" flow.

htmx 2.0.10 handles `HX-Location` by issuing a GET and swapping the response into
`document.body` with `innerHTML` (`app/static/js/htmx.min.js`:
`s.push=s.push??"true";Nn("get",e,s);return`), and it **re-executes every
`<script>` in the swapped content** (`function D(e){Array.from(e.querySelectorAll("script")).forEach(...)}`,
gated on `allowScriptTags:true`, which this project leaves at the default —
`app/templates/includes/htmx_config.html:87` says so explicitly).

The swapped-in page is `/ads/{id}/edit` — **the same page the user is already on**
— and it carries 18 top-level `const`/`let` declarations in a classic inline
script (`app/templates/ads/form.html:311-339`: `IMAGE_BASE_URL`,
`THUMB_KEY_PREFIX`, `MAX_IMAGES`, `TEXT_LIMIT`, `TEXT_WARN_AT`, `CAPTION_LIMIT`,
`UPLOAD_*_ERROR`, `imagePaths`, `adForm`, `mediaStrip`, `imageInputs`,
`fileInput`, `errorBox`, `counter`, `textArea`, `addTile`). Those already exist in
the global lexical environment from the first page load. Re-running the script
throws at instantiation time, before a single statement executes:

```
SyntaxError: Identifier 'IMAGE_BASE_URL' has already been declared
```

(verified: `vm.runInThisContext` of the same source twice — first ok, second
throws.)

**Observable result:** after deleting the last schedule from the ad editor, the
page appears to reload but the editor's entire client layer is dead — no image
upload, no character counter, no remove-image interception, no add-tile
management — until the user performs a hard reload. The only signal is one line in
the console. This directly contradicts the milestone acceptance signal the phase
leans on throughout (`app/pages/schedules.py:1066`,
`app/templates/ads/partials/sched_delete_response.html`: "ответ 200 И ЧИСТАЯ
КОНСОЛЬ").

The project already knew this hazard: `app/templates/includes/htmx_error_banner.html`
guards its own re-execution with `document.body.dataset.htmxFailureWired`,
precisely because body swaps re-run scripts. The editor's script was not given the
same treatment when this phase made it a swap destination.

**Fix (pick one, but pick one before shipping):**

1. Make the editor script re-entrant — the smallest change, and consistent with
   the guard already used by `htmx_error_banner.html`:

```html
<script>
(function () {
  const IMAGE_BASE_URL = {{ s3_public_url() | tojson }};
  /* ... the rest of the existing body, unchanged ... */
})();
</script>
```

   An IIFE removes every global lexical binding, so re-execution is a no-op
   collision-wise and re-binds the DOM handlers to the freshly swapped nodes —
   which is what the swap actually needs.

2. Or keep the schedule-delete empty-editor path on a full navigation
   (`HX-Redirect`, or leave the branch on `RedirectResponse`) so the document is
   genuinely reloaded. This is cheaper but leaves the landmine armed for the next
   route that redirects into the editor.

Add a gate that fails when a template reachable as an `HX-Location` destination
contains a top-level `const`/`let`/`class` inside an inline `<script>`; today
`ads/form.html` (18 declarations) and `accounts/connect_tg_user.html` are the only
two files with that shape, so the gate is cheap and exact.

---

## Warnings

### WR-01: The panel's `htmx:after-request` handler is still un-scoped, and this phase multiplied its blast radius from 1 site to 18 without narrowing it

**File:** `app/templates/components/modal.html:679`, `:247-281`

**Issue:**
The prior `WR-04` was closed by an inventory that reads the *text* of every block
call and reddens a slot carrying an `hx-*` attribute
(`test_no_confirm_panel_slot_carries_a_request_of_its_own`). The handler itself was
deliberately left un-narrowed (`:268-273`), and the file states the reason: the
expression is load-bearing for criterion 3.

Two things make this a live warning rather than a settled decision:

1. The file itself concedes the mitigation covers only half the hole
   (`:275-281`): a request raised **programmatically** from inside the slot — an
   `htmx.ajax()` call, or an Alpine handler — is not distinguishable by the
   inventory "ВОВСЕ". That half is unguarded by anything.
2. The same phase (D-14/D-15, `:416-436`) made `hx-post` and the after-request
   handler **unconditional for all 18 confirm sites**. Before this phase exactly
   one site carried them. The defect's reach therefore grew 18× in the same commit
   range in which its narrowing was deferred to a `WINDOWS.md` entry.

Concretely: any htmx exchange that bubbles `htmx:afterRequest` to the panel form
sets `sending = false` and, on success, calls `hide()` — closing a destructive
confirmation panel out from under the user mid-decision, on any of 18 screens.

**Fix:** Narrow the handler to the form's own exchange. The cheapest form that does
not touch the criterion-3 expression's shape is an identity check on the event
target, added as a leading guard:

```html
x-on:htmx:after-request="if ($event.target !== $el) return; sending = false; if (...) hide()"
```

If that is genuinely blocked by the criterion-3 gate's teeth, then extend the
inventory's predicate to also reject `hx-` *free* request initiation in slots
(`htmx.ajax`, `x-on:*` calling into htmx) rather than only the attribute prefix, so
the conceded half is at least detectable.

---

### WR-02: `sched_delete_response.html`'s three OOB nodes claim membership in a machine-checked register that contains none of them

**File:** `app/pages/schedules.py:1066-1068`, `app/templates/ads/partials/sched_delete_response.html:40-45`, `tests/test_pages/test_account_groups.py:4897-4933`

**Issue:**
Both the handler docstring and the response template state that the idle-path
console-error cost is "уже назван поимённо перечнем `OOB_TARGET_EXCEPTIONS` с
назначенной Фазой 15" and that this phase "НАСЛЕДУЕТ" it.

The register contains exactly two entries, and both are group-screen nodes:

```python
OOB_TARGET_EXCEPTIONS = {
    "group-row-{group_id}": ...,   # app/templates/account_groups/partials/delete_response.html
    "group-del-{group_id}": ...,   # same file
}
OOB_TARGET_EXCEPTIONS_DECLARED = 2
```

Neither `sched-{id}`, nor `sched-del-{id}`, nor `#sched-count` appears anywhere in
it, and `test_the_number_of_oob_target_exceptions_is_the_declared_one` pins the
count at 2 — so an attempt to enrol the new nodes would have reddened, and no such
attempt was made. The three new no-target-capable nodes shipped outside the exact
register that exists to prevent that.

The imported reasoning also does not transfer for the third node. The group-side
comment justifies *excluding* the counter with "область `id="account-groups-count"`
в документе есть всегда" (`:4889-4891`). The schedule counter's wrapper is
**conditional** — `app/templates/ads/form.html:213` puts `<div id="sched-count">`
inside `{% if editor.schedules %}` — so on the cross-ad path the phase itself
documents (document open on ad A, request naming ad B), an editor A with zero
schedules has no `#sched-count` target at all, producing a third
`htmx:oobErrorNoTarget` the register does not account for.

**Fix:** Either enrol the three nodes and bump the declared count —

```python
OOB_TARGET_EXCEPTIONS = {
    ...,
    "sched-{schedule_id}":     OobTargetException(where_printed=".../sched_delete_response.html", ...),
    "sched-del-{schedule_id}": OobTargetException(...),
    "sched-count":             OobTargetException(reason="цель условна: обёртка стоит внутри {% if editor.schedules %}", ...),
}
OOB_TARGET_EXCEPTIONS_DECLARED = 5
```

— or correct both prose claims to say the schedule nodes are *not* in the register
and name where their exception is recorded instead. Leaving a false pointer to a
gated register is the failure mode the register was built to stop. The register
also currently lives in `tests/test_pages/test_account_groups.py`, which makes it
structurally invisible to schedule-side reviewers; moving it to a shared module
would remove the incentive to skip enrolment.

---

### WR-03: The focus landing region is guaranteed empty on the very path it was chosen for

**File:** `app/templates/components/modal.html:665`, `app/templates/includes/notice_area.html:95-112`, `:133`

**Issue:**
`land()` moves focus to `#notice` when the opener has left the document. On the
fragment path — the path the region was explicitly selected for — the phase's own
measurement (`notice_area.html:105-110`) is that the region is **always empty**:
`D-03` forbids a success notice, and neither fragment response of the phase carries
a notice code. So a keyboard or screen-reader user who confirms a deletion has
focus programmatically moved into an empty `role="status" aria-live="polite"`
container and receives no announcement whatsoever that the action completed. The
same user previously got a full page navigation, which at least re-announced the
document.

This is honestly recorded rather than hidden, which is why it is a warning and not
a blocker — but it is shipped behaviour on 18 confirm sites, and the record
("Фокус приезжает в осмысленное МЕСТО, но не в осмысленный ТЕКСТ") describes a
regression in announcement, not a neutral trade.

**Fix:** Give the landing an announcement rather than only a location. The cheapest
option that does not reopen `D-03` (no visual banner on success) is a
visually-hidden live message written by the same OOB channel:

```html
<div id="notice" role="status" aria-live="polite" tabindex="-1">
  ...
  <span class="visually-hidden" data-announce></span>
</div>
```

and have `sched_delete_response.html` / the group delete response set
`data-announce` text ("Расписание удалено") via the existing OOB mechanism. If that
is out of scope, the deferral should name the *announcement* gap specifically
rather than only the transition-transport gap currently assigned to `GATE-09`.

---

### WR-04: Destructive user-facing routes converted in this phase carry no origin guard, contradicting the doctrine this same phase asserts in `admin.py`

**File:** `app/pages/ads.py:722-760`, `app/pages/accounts.py:993-1021`, `app/pages/schedules.py:951-965`

**Issue:**
`admin.py`, edited in this phase, states the project's rule verbatim
(`app/pages/admin.py:1849-1868`):

> "…и без сверки источника единственным, что стоит между сторонней страницей и
> этим действием, остаётся умолчание `samesite="lax"` — одна политика браузера
> там, где проект в трёх соседних местах требует явной серверной проверки."

Four admin routes and three money/retry forms follow it. Meanwhile the three
user-facing destructive routes reworked by this same phase — delete ad, delete
messenger account, delete schedule — have no `is_same_origin` check in any branch.
All three are irreversible and all three now sit behind the same confirm panel.

The exposure is genuinely reduced by `samesite="lax"` on the session cookie
(`app/pages/auth.py:89-94`), which is why this is a warning and not a blocker: a
cross-site `POST` will not carry the cookie in current browsers. But that is
exactly the argument `admin.py` rejects for its own routes, in a docstring written
during this phase. The asymmetry is now self-contradictory in the same commit
range, which is the condition `CR-02 ревизии фазы 6` was raised under for
`admin_delete_user`.

**Fix:** Apply the same guard, in the same position (after auth, before any read):

```python
if not is_same_origin(request):
    return Response(status_code=403)
```

in `ads_delete`, `accounts_delete` and `schedules_delete`. If the decision is to
*not* extend it, record the asymmetry as a named exception with its lifting
condition, the way `OFFSET_CURSOR_EXCEPTIONS` records the response-shape
exceptions — so the next reader sees a decision rather than an omission.

---

### WR-05: `_expanded_from_form` remains unbounded on the invariant `_ad_id_from_form`'s correctness argument now rests on

**File:** `app/pages/schedules.py:202-225`, `:334-338`

**Issue:**
`_ad_id_from_form`'s docstring, point (б) (`:274-280`), states the distinction that
justifies bounding one helper and not the other:

> "Результат `_expanded_from_form` уезжает ТОЛЬКО в строку адреса (`?sched=N`) и
> до базы не доходит ни на одном пути, поэтому там ограничения ТИПА достаточно."

That is true today — `expanded_id` is compared against a Python set in
`app/pages/ads.py:363-365`, never bound into SQL. But nothing enforces it. Both
helpers now feed the *same* shared builder `_editor_url` (`:310-339`), introduced
by this phase specifically so that "адрес… СОБРАН ОДНИМ КОДОМ". A future caller
that passes `schedule_id` into a lookup — or an `ads.py` refactor that resolves
`sched` by query instead of by set membership — reinstates `CR-01` exactly, and no
test would go red: `tests/test_pages/test_editor_schedules.py` has no
out-of-range case for `keep_sched`.

**Fix:** Bound it too. The cost is one line and the argument the docstring has to
carry drops from a cross-module invariant to a local fact:

```python
def _expanded_from_form(form_data) -> int | None:
    try:
        value = int(form_data.get("keep_sched"))
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= ID_MAX else None
```

Alternatively, if the asymmetry is deliberate, guard the claim: a test that asserts
`Schedule.id` is never compared against the result of `_expanded_from_form`
anywhere in `app/pages/`.

---

### WR-06: The origin refusal on four admin routes is now reported to the user as a transient server failure with a "retry" instruction

**File:** `app/pages/admin.py:904,1100,1739,1867`, `app/templates/includes/htmx_error_banner.html`

**Issue:**
Making `hx-post` unconditional routed the four admin confirm panels through htmx.
Their origin guard still returns a bare `Response(status_code=403)`. On the htmx
path a 403 is classified `error: true` by the project's `responseHandling`
(`app/templates/includes/htmx_config.html`), which fires `htmx:responseError`,
which unhides the global banner:

> "Действие не выполнено. Попробуйте ещё раз через минуту."

For a *security* refusal that will never succeed on retry, this is the wrong
message: it invites a retry loop and, because the panel deliberately stays open on
failure (`D-12`), the user is left with an armed confirm button and an instruction
to press it again. Before this phase the same refusal produced a plain 403 document
— unfriendly, but not misleading.

The banner also never re-hides once shown, so a single refusal poisons every
subsequent screen until a full reload.

**Fix:** Distinguish the refusal from a server fault at the transport, e.g. return
the refusal through the response layer with a registered notice code rather than a
bare status —

```python
if not is_same_origin(request):
    logger.warning("cross_origin_refused", path=request.url.path)
    return await respond(request, redirect=location, notice=notices.CROSS_ORIGIN_REFUSED)
```

— or, if the current "чужому источнику причина отказа не сообщается" stance must
hold (it should: the message would be a signal to the attacker's page), then at
minimum re-hide the banner on the next successful exchange so one refusal does not
persist across the session:

```js
document.body.addEventListener('htmx:afterRequest', function (event) {
  if (event.detail && event.detail.successful) {
    var server = document.getElementById('htmx-failure-server');
    if (server) { server.setAttribute('hidden', ''); }
  }
});
```

---

_Reviewed: 2026-09-03T22:51:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_HEAD: 0ea886d — diff base: 576cef07_

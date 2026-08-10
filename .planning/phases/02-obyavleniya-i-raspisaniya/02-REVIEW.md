---
phase: 02-obyavleniya-i-raspisaniya
reviewed: 2026-08-10T18:05:00Z
depth: standard
files_reviewed: 54
files_reviewed_list:
  - alembic/versions/0013_ad_status.py
  - app/application/accounts/use_cases.py
  - app/application/scheduling/use_cases.py
  - app/constants.py
  - app/main.py
  - app/models/ad.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/dashboard.py
  - app/pages/schedules.py
  - app/routes/ads.py
  - app/routes/schedules.py
  - app/routes/uploads.py
  - app/static/css/app.css
  - app/templates/ads/form.html
  - app/templates/ads/includes/ad_card.html
  - app/templates/ads/includes/autosave.html
  - app/templates/ads/includes/autosave_response.html
  - app/templates/ads/includes/preview.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/summary.html
  - app/templates/schedules/includes/schedule_row.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - tests/conftest.py
  - tests/test_application/test_collect_due_draft.py
  - tests/test_config.py
  - tests/test_config_s3.py
  - tests/test_constants.py
  - tests/test_e2e.py
  - tests/test_main.py
  - tests/test_migrations/__init__.py
  - tests/test_migrations/test_0013_ad_status.py
  - tests/test_models/test_ad.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_ads_image_ownership.py
  - tests/test_pages/test_ads_status.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedule_creation_path_exists.py
  - tests/test_pages/test_schedule_ownership.py
  - tests/test_pages/test_schedules_detached_account.py
  - tests/test_pages/test_schedules_list.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_ads.py
  - tests/test_routes/test_groups_bulk.py
  - tests/test_routes/test_schedules.py
  - tests/test_routes/test_schedules_profile_timezone.py
  - tests/test_routes/test_schedules_toggle_detached.py
  - tests/test_routes/test_sync_groups.py
  - tests/test_routes/test_tg_user_auth.py
  - tests/test_services/test_messenger_factory.py
  - tests/test_templates/test_components.py
findings:
  critical: 2
  warning: 8
  info: 6
  total: 16
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-08-10T18:05:00Z
**Depth:** standard
**Files Reviewed:** 54
**Status:** issues_found

## Summary

The four security invariants named for this phase hold **on the paths they cover**:

- `sniff_image` is the only source of the stored type, and the client `Content-Type`
  header reaches neither the validation nor `upload_file_to_s3` (`app/routes/uploads.py:99-136`).
- `own_image_keys` guards all four write paths to `Ad.images` — page create/update via
  `_save_from_editor`, `POST /api/ads`, `PUT /api/ads/{id}`. A grep across
  `app/routes/`, `app/pages/` and `app/repositories/` finds no fifth writer.
- `_owns_ad_and_account` guards both page-layer schedule handlers before the first model
  write (`app/pages/schedules.py:514, 599`).
- `return_to` never reaches a `Location` header; `_editor_redirect` builds the URL from a
  verified `ad_id` (`app/pages/schedules.py:174-189`). No open redirect.
- No `|safe`, `Markup` or `{% autoescape false %}` exists anywhere under `app/templates/`;
  the modal `body` and all `title=` attributes are autoescaped. The editor builds media
  tiles node-by-node (`createElement`/`textContent`), and both JS-context injections use
  `| tojson` without surrounding quotes.

Two defects are nevertheless blocking, and both are of the exact class the phase context
flagged: an authorization check present on one path and absent on the alternate path
(CR-02), and a client/server contract that the tests assert on a route the browser never
calls (CR-01).

Targeted run of the phase suite (`test_ads_editor`, `test_ads_image_ownership`,
`test_editor_schedules`, `test_schedule_ownership`, `test_uploads`): **110 passed**. Tests
passing is not evidence of correctness here — CR-01 is green precisely because the test
substitutes a route the client does not use.

## Structural Findings (fallow)

No structural pre-pass was supplied with this review; no `<structural_findings>` block was
present in the prompt. All findings below are narrative.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Every autosave on `/ads/new` creates another draft — the form is never re-pointed at the edit route

**File:** `app/templates/ads/form.html:51-57`, `app/pages/ads.py:402-408`
**Severity:** BLOCKER

**Issue:**
For a new ad the form renders with a fixed target:

```html
<form id="ad-form" method="post"
      action="{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}"
      hx-post="{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}"
      hx-trigger="submit, keyup changed delay:2s, change delay:2s"
      hx-swap="none">
```

The first autosave creates the draft and the handler answers with `HX-Push-Url`
(`app/pages/ads.py:405-407`). `HX-Push-Url` only calls `history.pushState` — it changes the
address bar, nothing else. The form element itself is deliberately never swapped
(`hx-swap="none"`, and `autosave_response.html` contains no `<form>` by design and is
asserted to contain none by `test_autosave_response_carries_no_form`). No script in
`form.html` rewrites `adForm`'s `hx-post`/`action` either — the JS block only manages
tiles, the counter and the error class.

Consequence: the second `keyup changed delay:2s` — i.e. two more seconds of typing — POSTs
`/ads/new` **again**, `ads_create` calls `_save_from_editor(..., ad=None)`, and
`app/pages/ads.py:369-379` inserts a **second** `Ad`. Typing an ad of any length leaves a
trail of one draft per debounce window in `/ads`, and only the fragment typed before the
first save is stored in the ad the pushed URL points at: reloading `/ads/{first_id}/edit`
loses everything typed afterwards. Silent data loss plus list pollution, on the happy path,
with JavaScript enabled.

The regression test does not catch this because it does not perform the client's request.
`tests/test_pages/test_ads_editor.py:329-353` (`test_repeated_autosave_updates_the_same_ad`)
issues the first POST to `/ads/new` and then hand-addresses the second POST to
`/ads/{ad_id}/edit` — the very rewrite the browser never performs. The assertion
`_ads_count(...) == 1` is therefore vacuous.

**Fix:** re-point the live form when the draft is created, and add a test that repeats the
POST to the *same* URL the form carries.

```html
<!-- app/templates/ads/form.html, inside the existing <script> -->
adForm.addEventListener('htmx:afterRequest', event => {
    const pushed = event.detail.xhr && event.detail.xhr.getResponseHeader('HX-Push-Url');
    // Черновик только что создан: дальнейшие автосохранения обязаны уходить на
    // маршрут редактирования, иначе каждое создаёт новую запись.
    if (pushed && adForm.getAttribute('hx-post') === '/ads/new') {
        adForm.setAttribute('hx-post', pushed);
        adForm.setAttribute('action', pushed);
    }
});
```

```python
# tests/test_pages/test_ads_editor.py — второй запрос уходит ТУДА ЖЕ, куда его
# отправил бы браузер: на адрес из атрибута формы, а не на подставленный рукой.
second = await authed_client.post("/ads/new", content=form_body(...), headers=HX_HEADERS)
assert await _ads_count(db_session, owner_id) == 1
```

(An equivalent server-side fix — accepting an OOB-updated hidden `ad_id` on `/ads/new` and
routing to update when the caller owns it — is acceptable, but must keep the no-JavaScript
path unchanged.)

---

### CR-02: `group_ids` ownership is enforced on the page path and not on the JSON schedule API

**File:** `app/routes/schedules.py:96-112` (create), `app/routes/schedules.py:139-141` (update)
**Severity:** BLOCKER

**Issue:**
The page handlers reduce the submitted group ids to groups that belong to the caller *and*
to the chosen account before writing:

```python
# app/pages/schedules.py:524-532 and 607-613
available = await _groups_of_account(db, user.id, account_id)   # WHERE user_id AND account_id
group_ids = [gid for gid in group_ids if gid in available]
```

The JSON API — hardened in this same phase to check *account* ownership
(`app/routes/schedules.py:82-94`) — persists `group_ids` verbatim on create and assigns them
blindly on update:

```python
schedule = await schedule_repo.create(..., group_ids=data.group_ids, ...)   # :106
for field, value in update_data.items():                                    # :140
    setattr(schedule, field, value)
```

Nothing downstream re-checks the owner either. `collect_due_schedules` iterates
`schedule.group_ids` as given (`app/application/scheduling/use_cases.py:120`), and
`send_message_once` resolves the group by primary key only
(`app/application/scheduling/use_cases.py:173`), then writes the *victim's*
`group_name` into a `SendLog` row stamped with the **attacker's** `user_id`
(`:277-290`). The attacker's own history page and the dashboard then render it.

So an authenticated user can `POST /api/schedules` with their own `ad_id` and their own
`account_id` but a foreign `group_ids` list and (a) enumerate other tenants' group names
and external ids through their own history, and (b) drive their own connected messenger
session at another tenant's group external id, delivering a message wherever that session
happens to be a member. This is the "authorization check reachable via an unguarded
alternate path" case the phase context calls out.

`tests/test_routes/test_schedules.py:22-44` enshrines the gap: it creates a schedule with
`"group_ids": [1, 2, 3]` while no `Group` rows exist at all, and asserts the values come
back.

**Fix:** apply the same restriction the page path applies, in the API handler:

```python
# app/routes/schedules.py — create_schedule, после проверки владения аккаунтом
owned = set(
    (
        await db.execute(
            select(Group.id).where(
                Group.id.in_(data.group_ids),
                Group.user_id == user_id,
                Group.account_id == data.account_id,
            )
        )
    ).scalars().all()
)
if set(data.group_ids) - owned:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
```

and the same check in `update_schedule` whenever `"group_ids"` is present in
`model_dump(exclude_unset=True)`. Update `tests/test_routes/test_schedules.py` to seed real
groups and add a rejection case for a foreign group id.

---

## Warnings

### WR-01: Image-key pattern is anchored with `$` and normalises the prefix through `int()`

**File:** `app/pages/ads.py:49, 81-87`
**Issue:** `_IMAGE_KEY_PATTERN` ends in `$`, which in Python also matches immediately before
a trailing newline, and `re.match` (not `fullmatch`) is used. `"7/<32 hex>_a.png\n"`
therefore passes ownership validation for user 7 and is stored verbatim in `Ad.images`,
from where it is concatenated into a URL by `get_image_url` and handed to the messenger
adapters. Separately, `int(match.group(1)) != user_id` accepts `007/...` for user 7, so a
stored key need not be a key `/api/uploads/image` could ever have produced. Neither case
crosses a tenant boundary, but both break the stated invariant that the key is exactly the
value the upload endpoint issued for this caller.
**Fix:**

```python
_IMAGE_KEY_PATTERN = re.compile(r"[1-9]\d*/[0-9a-f]{32}_[A-Za-z0-9._-]{1,100}")
...
match = _IMAGE_KEY_PATTERN.fullmatch(value)
if match is None or value.split("/", 1)[0] != str(user_id):
    raise HTTPException(...)
```

### WR-02: Upload size limit is enforced only after the whole body is buffered in memory

**File:** `app/routes/uploads.py:99-114`
**Issue:** `content = await file.read()` materialises the entire upload before
`len(content) > max_bytes` is evaluated. `max_image_size_mb` (default 5) therefore bounds
what is *stored*, not what is *received*: any authenticated client can post a multi-gigabyte
body and force the ASGI worker to hold it in RAM, and the rejection path (`sniff_image`
returning `None`) has already paid the same cost. The phase moved this read one step
earlier without adding a bound.
**Fix:** read incrementally and abort as soon as the running total exceeds the limit:

```python
max_bytes = settings.max_image_size_mb * 1024 * 1024
chunks, size = [], 0
while chunk := await file.read(64 * 1024):
    size += len(chunk)
    if size > max_bytes:
        raise HTTPException(400, detail=f"File size exceeds {settings.max_image_size_mb}MB limit")
    chunks.append(chunk)
content = b"".join(chunks)
```

### WR-03: `.strip()` on form values raises 500 when the same field arrives as a file part

**File:** `app/pages/ads.py:346`, `app/pages/schedules.py:133`
**Issue:** Both helpers assume every repeated form value is a `str`:
`[v for v in form_data.getlist("images") if v.strip()]` and
`[v for v in values if _TIME_RE.match(v.strip())]`. A `multipart/form-data` POST carrying a
*file* part named `images` or `times_of_day` yields `UploadFile` objects from `getlist`, and
`.strip()` raises `AttributeError`, which the generic handler in `app/main.py:110-121`
converts to a 500. `_clean_ints` in the same module already defends against this class of
input with `except (TypeError, ValueError)`; these two paths do not, so the hardening is
inconsistent within one file.
**Fix:** filter by type before touching the value:

```python
[v for v in form_data.getlist("images") if isinstance(v, str) and v.strip()]
[v for v in values if isinstance(v, str) and _TIME_RE.match(v.strip())]
```

### WR-04: API layer imports from the page layer

**File:** `app/routes/ads.py:12`
**Issue:** `from app.pages.ads import own_image_keys` makes `app/routes/` depend on
`app/pages/`, which in turn pulls in `app.pages.common` (Jinja environment, template
globals, S3 URL binding, six model modules) into the JSON API import graph. The dependency
direction is inverted relative to the rest of the project and is one import away from a
cycle, since `app/pages/*` already imports repositories and services.
**Fix:** move `_IMAGE_KEY_PATTERN`, `own_image_keys`, `INACCESSIBLE_IMAGE_MESSAGE` into a
neutral module (e.g. `app/services/image_keys.py`) and import it from both layers. The
"one rule in one place" property the comment defends is preserved, without the layering
inversion.

### WR-05: Two different definitions of "may be resumed" — page toggle vs API toggle

**File:** `app/routes/schedules.py:187-191` vs `app/pages/schedules.py:667-672`
**Issue:** The page toggle refuses to resume a schedule that is incomplete by `_is_complete`
(account **and** groups **and** days **and** times). The API toggle refuses only when
`account_id is None`. `POST /api/schedules/{id}/toggle` therefore activates a schedule with
zero groups, zero days or zero times; `compute_next_run_at` returns `None` for empty days or
times (`app/services/schedule_service.py:16-17`), so the row lands in a state the UI
declares impossible and the summary list renders as `Активно` + `Не заполнено`
simultaneously (`app/templates/schedules/includes/schedule_row.html:47-48, 99-101`). D-08
explicitly requires one definition; there are two.
**Fix:** import/reuse the completeness predicate in the API handler:

```python
if not schedule.is_active and not _is_complete(
    schedule.account_id, schedule.group_ids, schedule.days_of_week, schedule.times_of_day
):
    raise HTTPException(400, detail="Сначала дозаполните расписание в редакторе объявления")
```

(promote `_is_complete` out of `app/pages/schedules.py` alongside the WR-04 move so the API
does not import the page module).

### WR-06: `PUT /api/schedules/{id}` recomputes `next_run_at` for paused schedules and never re-evaluates completeness

**File:** `app/routes/schedules.py:139-151`
**Issue:** After assigning the patch fields, the handler unconditionally recomputes
`next_run_at`, including for a schedule with `is_active=False`. The page path deliberately
does the opposite (`app/pages/schedules.py:628-638`: incomplete ⇒ `is_active=False` and
`next_run_at=None`; complete ⇒ recompute only when active). The result is paused rows
carrying a future run timestamp, which the editor's "Ближайший запуск" summary
(`_editor_context` takes `min` over **all** `next_run_at` values,
`app/pages/ads.py:214-215`) then advertises as an upcoming send that will never happen.
**Fix:** mirror the page-layer rule — clear `next_run_at` when the schedule is inactive or
incomplete, recompute only when it is active and complete.

### WR-07: Schedule handlers answer authorization and not-found failures with a silent redirect that discards the user's edits

**File:** `app/pages/schedules.py:514-515, 592-593, 599-600`
**Issue:** `schedules_create` and `schedules_update` return `RedirectResponse("/schedules")`
with no message when ownership fails or the row is gone. This is not only the tampering
case: a user whose messenger account was deleted in another tab still has the old
`account_id` in the rendered card, so a normal "СОХРАНИТЬ РАСПИСАНИЕ" click silently throws
them out of the editor onto the summary list, with every group/day/time edit discarded and
nothing said. The phase argues the opposite policy one file over — `own_image_keys` raises
rather than dropping, precisely because "a refusal on data is not navigation"
(`app/pages/ads.py:63-70`). The two handlers contradict that rule.
**Fix:** re-render the editor with a stated error (the same shape as the autosave error
path), or at minimum redirect back to `/ads/{ad_id}/edit` with an error marker the card can
show, instead of navigating away.

### WR-08: `status` form parameter shadows the imported FastAPI `status` module inside `ads_update`

**File:** `app/pages/ads.py:3, 502`
**Issue:** `app/pages/ads.py` imports `status` from `fastapi` and uses
`status.HTTP_400_BAD_REQUEST` at module level (`:74, :85`). `ads_update` then declares
`status: str | None = Form(None)`, which shadows that name for the whole function body. Any
future `status.HTTP_*` added to this 20-line handler resolves against a client-supplied
string and raises `AttributeError` at request time rather than failing at import.
**Fix:** rename the parameter and keep the wire name explicit:
`ad_status: str | None = Form(None, alias="status")`, passing `status_value=ad_status`.

---

## Info

### IN-01: Dead query parameter accepted on two routes

**File:** `app/pages/ads.py:125`, `app/pages/schedules.py:359`
**Issue:** `layout: str | None = Query(None)` is parsed and never read. The comment explains
the compatibility reason, but nothing records when it may be removed, so it will outlive the
open tabs it protects.
**Fix:** add a removal marker (milestone/date) next to the parameter so it can be deleted
deliberately rather than found later by grep.

### IN-02: Deprecated `TemplateResponse` call style, inconsistently within the same modules

**File:** `app/pages/ads.py:139, 167`, `app/pages/schedules.py:383, 437`, `app/pages/dashboard.py:98`
**Issue:** These use the legacy `TemplateResponse(name, {"request": request, ...})` signature
while `ads_new`, `ads_edit` and `_autosave_response` in the same file already use the
`(request, name, context)` form. Starlette emits a `DeprecationWarning` for the legacy form
(observed in the test run against `test_image_base_url_comes_from_app_settings` and
`test_summary_list_keeps_working`).
**Fix:** convert the five remaining call sites to `TemplateResponse(request, name, {...})`.

### IN-03: Warning threshold duplicated in the template instead of using the value the server already computes

**File:** `app/templates/ads/form.html:228`
**Issue:** `const TEXT_WARN_AT = {{ (editor.text_limit * 0.9) | round | int | tojson }};`
re-derives the ratio that `app/pages/ads.py:29` owns as `TEXT_WARN_RATIO`, while the
server-rendered counter one screen above (`form.html:80`) reads `editor.text_warn_at`. The
two agree today only because the JS re-applies the caption rule itself; changing
`TEXT_WARN_RATIO` moves one and not the other.
**Fix:** expose the plain-text threshold in `_editor_context` (e.g. `text_warn_plain`) and
render `{{ editor.text_warn_plain | tojson }}`.

### IN-04: `_build_schedule_items` recomputes the timezone its callers already resolved

**File:** `app/pages/schedules.py:310-347` (`:332`), callers `:366-367, 408-409`
**Issue:** Both callers compute `tz_name` and `tz` and pass `tz` in; the function then
recomputes `tz_name` from `user.timezone` for the label. Three copies of the same
`user.timezone if ... in VALID_TIMEZONES else "UTC"` expression exist in the module.
**Fix:** pass `tz_name` alongside `tz`, or return both from one helper.

### IN-05: Non-mapped attributes attached to ORM instances, then defaulted twice

**File:** `app/pages/ads.py:111-113`, `app/templates/ads/includes/ad_card.html:39-40`
**Issue:** `_enrich_ads_with_stats` sets `ad.sends_count`/`ad.schedules_count` on `Ad`
instances (attributes the model does not declare), already coalescing with `or 0`; the
template then coalesces again with `(ad.sends_count or 0)`. Any caller that forgets the
enrichment gets an `AttributeError` in the template rather than a missing number.
**Fix:** return a `{ad_id: (sends, schedules)}` mapping and pass it to the template, or
declare the two counters on the model as non-persisted defaults.

### IN-06: Test asserts a client behaviour it does not exercise

**File:** `tests/test_pages/test_ads_editor.py:329-353`
**Issue:** See CR-01 — `test_repeated_autosave_updates_the_same_ad` substitutes
`/ads/{id}/edit` for the URL the form actually carries, so it can only ever pass. This is
the test that would otherwise have caught the blocker.
**Fix:** covered by the test change proposed in CR-01.

### IN-07 (note, not a defect): known-and-accepted items re-verified

`0013_ad_status.py` remains unapplied and its `downgrade` data loss is documented and
covered by `tests/test_migrations/test_0013_ad_status.py:145-169`; `required` is absent from
the editor fields; `account_id` is `Form(None)` on both schedule handlers; a user with no
accounts cannot create a schedule (`app/templates/ads/form.html:149-166`); pre-existing
foreign/external image keys in `Ad.images` still render in history and admin
(`app/pages/history.py:95, 188`, `app/pages/admin.py:213, 287`). No new problem was found in
any of these areas beyond what is listed above.

---

_Reviewed: 2026-08-10T18:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

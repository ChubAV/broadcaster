---
phase: 12-zagruzka-izobrazheniy-bez-fetch
reviewed: 2026-09-19T00:00:00Z
depth: standard
files_reviewed: 32
files_reviewed_list:
  - README.md
  - app/main.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/services/image_keys.py
  - app/services/image_upload.py
  - app/services/images.py
  - app/templates/ads/form.html
  - app/templates/ads/includes/autosave_response.html
  - app/templates/ads/includes/media_strip.html
  - app/templates/ads/includes/media_upload_form.html
  - app/templates/components/form_wrapper.html
  - nginx/nginx-http.conf.template
  - nginx/nginx.conf.template
  - tests/test_nginx_body_limit.py
  - tests/test_pages/test_access_gate.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_ads_image_ownership.py
  - tests/test_pages/test_ads_image_upload.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_impersonation_gate.py
  - tests/test_pages/test_origin_guard_on_destructive_routes.py
  - tests/test_routes/test_ads.py
  - tests/test_services/test_image_upload.py
  - tests/test_templates/test_ads_form_security.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_walkthrough_anchors.py
findings:
  critical: 2
  warning: 6
  info: 6
  total: 14
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-09-19
**Depth:** standard
**Files Reviewed:** 32
**Status:** issues_found

## Summary

Phase 12 moved the ad-image upload from a JSON `fetch()` route to an htmx multipart page
route. The per-file service half (`app/services/image_upload.py`) is careful and its
security seams hold under test: content-sniffing beats the declared type, filenames are
normalised before they reach both the object key and the screen, `own_image_keys` rejects
forged/foreign keys before any storage write (verified — `mock_s3.call_count == 0`), the
key pattern uses `fullmatch` so a trailing newline cannot pass, and the thumbnail prefix
keeps derived objects out of `Ad.images`. The access gate genuinely moved (router-level
`require_access` + `get_user_from_cookie` blocking check), so removing the two entries from
`test_access_gate.py` is not a weakening. The three inventory re-points (49/14 impersonation,
37 POST handlers, 13 fragment handlers, 5 manual-fetch sites) are consistent with the tree,
and `test_ads_form_security.py` was inverted **upward** (`>= 3` → `== 0`), not relaxed.

The defects are all at the new **seam between the upload fragment and the ad form's autosave
fragment** — the one place the phase's own documentation does not examine. Two of them are
shipping blockers:

1. Every per-file refusal row is wiped off the screen by the autosave that the same response
   asks the ad form to perform. The phase's stated reason for answering `200` with a fragment
   ("человек читает точную причину") is therefore not achieved on the partial-batch path.
2. An ownership refusal answers with an **empty** strip, which detaches genuinely attached
   images from the DOM; the next autosave then persists `images=[]`. Verified by probe.

Two documented invariants are also factually false on the new transport: the chunked-read
"limit what is *accepted*, not what is *stored*" claim (WR-02 in the source) and
"overflow parts are refused WITHOUT reading their bodies" — `await request.form()` has already
buffered every part before the handler's first check runs.

The `test_admin_panel.py` edit is sound: the remaining `_tile_value(overview, TILE_ERRORS) == "2"`
against three seeds (`fail`, `account_disconnected`, success) still fails if either failure kind
is dropped or the success is counted, and the dashboard-side tile keeps its own coverage in
`tests/test_dashboard.py:246`. No finding.

Targeted suite run: `tests/test_pages/test_ads_image_upload.py tests/test_services/test_image_upload.py
tests/test_nginx_body_limit.py` — 71 passed. Green tests are not evidence of correctness here:
every finding below lives in an interaction no test exercises.

## Critical Issues

### CR-01: The refusal row is erased by the autosave the same response triggers

**File:** `app/pages/ads.py:915-925` (header write), `app/templates/ads/includes/autosave_response.html:40-43`, `app/templates/ads/form.html:153`

**Issue:** On a partial batch (≥1 accepted, ≥1 refused) the handler sets `attached = True` and
emits `HX-Trigger-After-Swap: ads-image-attached`. The ad form listens for exactly that event
(`hx-trigger="submit, keyup changed delay:2s, change delay:2s, ads-image-attached from:body"` —
no delay modifier), so an autosave fires immediately after the strip swap. The autosave response
re-renders the strip out-of-band with:

```jinja
{%- set image_keys = (ad.images if ad and ad.images else []) %}
{%- set refusals = [] %}
{% include "ads/includes/media_strip.html" %}
```

`#media-tray` is replaced wholesale, and the refusal `<p class="alert alert--error">` rows live
*inside* `#media-tray` (`media_strip.html:69-71`). The user therefore sees "подойдут только
изображения JPEG или PNG" for one autosave round trip (~100-300 ms) and then it vanishes — on
the most common mixed-batch path ("I dragged in a folder"). D-04 accepted a lying `200` status
specifically to buy this message; the message does not survive. No test covers the two fragments
interacting, which is why the suite is green.

**Fix:** Carry refusals across the autosave, or stop the autosave from repainting the tray.
The smallest correct change is to render refusals outside `#media-tray` (their own OOB target
that the autosave response does not touch):

```jinja
{# form.html: permanent sibling of #media-strip #}
<div id="media-refusals" aria-live="polite"></div>
```

with `media_strip.html` emitting the rows into `#media-refusals` via a separate OOB block, or —
if they must stay in the tray — having `_autosave_response` accept and re-emit the pending
refusal list instead of hardcoding `refusals = []`.

### CR-02: An ownership refusal returns an empty strip and detaches real attachments

**File:** `app/pages/ads.py:836-852`, `app/templates/ads/includes/media_strip.html:72-90`

**Issue:** `image_keys` is initialised to `[]`; when `own_image_keys` raises, the assignment never
happens and the fragment is rendered with `image_keys=[]`. Because `#media-strip` is swapped
`innerHTML`, **every** `<input type="hidden" name="images" ... form="ad-form">` is removed from
the document — including the keys that *did* validate. Verified by probe (own key + foreign key
in one request):

```
STATUS 200
KEYS IN FRAGMENT: []
REFUSALS: [('', 'Одно из вложений недоступно...')]
MY OWN KEY SURVIVED: False
```

The strip is now the *sole* DOM source of `images` for the ad form (12-03 removed the client
`imagePaths` state), so the next autosave — a single keystroke away — serialises zero `images`
fields, `own_image_keys([])` passes, and the ad is saved with its attachments stripped. The
handler cannot distinguish "the client forged this" from "our own database produced this", and
its reaction to that uncertainty is to destroy visible state. Preconditions that reach it without
an attacker: a key predating filename normalisation (`Ad.images` is never rewritten — stated at
`image_upload.py:371-374`), or `max_images_per_ad` lowered below an existing attachment count
(`own_image_keys` raises on `len(values) > max_images` before any per-key check).

**Fix:** Never answer a refusal with an authoritative-looking empty strip. Re-render from the
persisted truth rather than from the rejected client list:

```python
except HTTPException as exc:
    refusals.append(Rejected(display_name="", reason=str(exc.detail)))
    # Держать на экране то, что подтверждено БАЗОЙ, а не подделанным списком:
    # пустая полоса снимает с формы и те ключи, что владение прошли.
    image_keys = await _persisted_image_keys(db, user.id, request)  # or [] only when no ad
```

At minimum, keep the subset that individually satisfies `_IMAGE_KEY_PATTERN` and the caller's
prefix, and refuse only the offending values.

## Warnings

### WR-01: The documented streaming limit protects nothing — `request.form()` already buffered everything

**File:** `app/pages/ads.py:816-818`, `app/services/image_upload.py:297-326`

**Issue:** `store_upload` reads the part in 64 KB chunks and aborts past `max_image_size_mb`,
with a comment claiming this stops an authenticated client from making the ASGI worker hold an
arbitrary body in memory (WR-02). On this transport the claim is false: `await request.form()`
runs `MultiPartParser.parse()`, which consumes the **entire** request stream and spools every
file part into a `SpooledTemporaryFile(max_size=1MB)` *before* the handler's first line of logic
(starlette 0.52.1, `formparsers.py:160-267`). By the time the size check runs, the bytes are
already on the worker. The same fact falsifies the "ОСТАВШИЕСЯ части получают отказ по потолку
БЕЗ чтения тел" comment (`ads.py:868-875`): the ceiling refusal avoids the decode and the S3
write, but not the read. `test_ceiling_takes_the_free_slots_and_refuses_the_rest` asserts only
`mock_s3.call_count == 4`, which does not measure reading. Practical bound: 64 parts × ~1 MB
in-memory spool each, i.e. up to ~64 MB resident per request on the single production uvicorn
worker — the ceiling is nginx's `client_max_body_size`, not `max_image_size_mb`.

**Fix:** Either correct both comments to state the real boundary (the proxy limit is the only
pre-read bound; `max_image_size_mb` limits what is *stored* and *decoded*), or stream the parts
yourself instead of materialising the form — e.g. `starlette.formparsers.MultiPartParser` over
`request.stream()` with per-part handling, or an explicit `Content-Length` pre-check before
`request.form()`.

### WR-02: The 64M body ceiling is server-wide, not scoped to the upload route

**File:** `nginx/nginx.conf.template:59-82`, `nginx/nginx-http.conf.template:10-44`

**Issue:** `client_max_body_size 64M;` is declared in the `server` block, so it raises the
accepted body size for *every* endpoint (HTTPS: 20M → 64M; HTTP: previously unset → 64M) to
serve one route. Every authenticated POST — and every unauthenticated one, since the proxy
decides before the app does — may now push 64 MB through the worker. The formula the comment
derives (`max_images_per_ad × max_image_size_mb`) applies to `/ads/images` alone.

**Fix:** Scope it, and keep the server default tight:

```nginx
client_max_body_size 20M;

location = /ads/images {
    client_max_body_size 64M;
    proxy_pass http://app:8000;
    # ...same proxy headers as the generic location...
}
```

`tests/test_nginx_body_limit.py` then needs `_declared_ceilings` to identify *which* block each
value belongs to, rather than asserting "ровно одно объявление".

### WR-03: The new storage-writing route has no origin check

**File:** `app/pages/ads.py:764-779`

**Issue:** `ads_images_upload` never calls `is_same_origin` (`app/pages/common.py:704`). The
project authenticates by cookie and `multipart/form-data` is a CORS "simple" request, so any
third-party page can submit a cross-site form that writes JPEG/PNG objects into the victim's S3
prefix — up to the new 64 MB ceiling per request, repeatable. The response is opaque cross-origin,
so the impact is storage/cost abuse rather than disclosure. `test_origin_guard_on_destructive_routes.py:693-700`
records the absence explicitly ("гарда источника маршрут не зовёт"), so this is a decision, not an
oversight — but the decision was inherited from the deleted JSON route rather than re-taken for a
route that now lives in the page layer where the guard idiom exists.

**Fix:** Either call the guard (consistent with the page layer's other mutating routes):

```python
if not is_same_origin(request):
    return await respond(request, redirect="/ads/new")
```

…or record the accepted risk in the phase's security notes with the storage-abuse impact named,
so the next reader does not have to rediscover that a write-to-storage route is CSRF-reachable.

### WR-04: Concurrent batches clobber each other — accepted uploads are silently orphaned

**File:** `app/templates/ads/includes/media_upload_form.html:34-40`

**Issue:** The upload form declares no `hx-sync` (and `disabled_elt=''` removes the double-submit
guard, correctly, since it has no submit button). Two `change` events in quick succession — pick
files, then pick more before the first response lands — produce two in-flight POSTs. Both compute
`free` from the *same* hidden-field set, both accept up to the full ceiling, and the second
response's `innerHTML` swap overwrites the first's keys. The first batch's objects stay in S3,
unreferenced, and the user sees fewer tiles than files they chose, with no message. The same race
exists between the upload response and an in-flight autosave: the autosave's OOB `#media-tray`
(rendered from the DB, which does not yet know the new key) replaces the freshly swapped tray, and
the ad form's queued autosave then serialises the post-wipe DOM.

**Fix:** Serialise the upload form the way the ad form is serialised, and make the ad form's
autosave not repaint the tray while an upload is in flight:

```jinja
{% call form_wrapper(action='/ads/images', target='#media-strip', swap='innerHTML',
                     trigger='change', encoding=true,
                     include="#media-strip input[name='images']",
                     sync='this:queue last', disabled_elt='') %}
```

(The `sync` parameter already exists in `form_wrapper` — `components/form_wrapper.html:187`.)

### WR-05: A storage failure mid-batch discards the files already accepted

**File:** `app/services/image_upload.py:396-400`, `app/pages/ads.py:876-882`

**Issue:** `store_upload` raises `HTTPException(502)` when S3 write fails. For part *n* of a batch,
parts `1..n-1` have already been uploaded and their keys appended to `image_keys` — but the
exception escapes the handler, so no fragment is produced, the DOM never learns those keys, and
htmx makes no swap on 5xx (the user gets the generic "Действие не выполнено" banner). The
successfully stored objects become orphans and the user's work is lost. This is precisely the
scenario the handler guards against for the ownership refusal ("исключению нельзя дать доехать до
браузера") — the same reasoning was not applied to the storage failure.
`test_a_storage_failure_still_answers_bad_gateway` enshrines the current behaviour.

**Fix:** Treat an infrastructure failure as a per-file refusal within the batch so the accepted
keys still reach the DOM:

```python
try:
    result = await store_upload(part, user_id=user.id, settings=settings)
except HTTPException as exc:
    refusals.append(Rejected(display_name=safe_filename(part.filename),
                             reason=STORAGE_UNAVAILABLE_MESSAGE))
    logger.warning("upload_storage_failed", detail=str(exc.detail))
    continue
```

### WR-06: The part-count limit escapes the fragment contract as a raw JSON 400

**File:** `app/pages/ads.py:816-818`

**Issue:** `request.form(max_files=MAX_UPLOAD_PARTS, max_fields=MAX_UPLOAD_PARTS)` is not wrapped.
Starlette converts a `MultiPartException` into `HTTPException(400)` (`requests.py:286-289`), which
FastAPI renders as `{"detail": "Too many files..."}` — a JSON body on an HTML surface, and a 4xx on
which htmx performs no swap. So the one refusal reason the phase introduced as a *new* defence
(G-3 / ASVS V12) is the one refusal the user cannot read, contradicting D-04's "один код для всех
трёх исходов". The same applies to a non-file part exceeding `max_part_size` (1 MB).

**Fix:**

```python
try:
    form_data = await request.form(max_files=MAX_UPLOAD_PARTS, max_fields=MAX_UPLOAD_PARTS)
except HTTPException:
    refusals = [Rejected(display_name="", reason=upload_parts_message(MAX_UPLOAD_PARTS))]
    return await respond(request, redirect="/ads/new", fragment=_media_strip_fragment)
```

…with the refusal text living beside the other closed-set texts in `image_upload.py`.

## Info

### IN-01: Three suite files cite a module this phase deleted

**File:** `tests/test_nginx_body_limit.py:30`, `tests/test_pages/test_ads_image_upload.py:127`
(collateral: `tests/test_services/test_images.py:5`)

**Issue:** Both new files reference `tests/test_routes/test_uploads.py` by typed path — including
line numbers (`:103-151`) — and that module was removed by 12-05. The phase was disciplined about
this elsewhere (`test_ads.py`, `test_ads_image_ownership.py` were rewritten to name the source "in
words"); these three were missed.

**Fix:** Re-point to `tests/test_services/test_image_upload.py` (or describe in words, per the
convention the phase adopted).

### IN-02: `oob` reaches the strip by inheriting a variable set for a different include

**File:** `app/templates/ads/includes/autosave_response.html:36-43`

**Issue:** `{% set oob = true %}` is written for `ads/includes/autosave.html`; `media_strip.html`
picks it up only because it is included later in the same template scope. Reordering the two
includes silently drops `hx-swap-oob` from the tray, and the failure mode is "the removed tile
stays on screen" — exactly the bug 12-03 fixed.

**Fix:** Make the dependency explicit with `{% with oob = true %}{% include ... %}{% endwith %}`
around each include, or pass the flag per include.

### IN-03: The parsed form is never closed

**File:** `app/pages/ads.py:816-818`

**Issue:** `await request.form()` used bare (not `async with`, no `await form_data.close()`).
FastAPI only registers the close callback for endpoints that *declare* a body field, which this one
does not, so the spooled temp files rely on refcount collection rather than deterministic release.

**Fix:** `async with request.form(max_files=..., max_fields=...) as form_data:` and keep the batch
loop inside the block.

### IN-04: The no-JavaScript path performs the whole upload and then throws the keys away

**File:** `app/pages/ads.py:924-926`

**Issue:** A non-htmx POST runs the full batch (decode, two S3 writes per file) and then
`respond()` returns a 302 to `/ads/new`, where the strip is rendered from `ad.images`. The keys
are never delivered anywhere, so every accepted file becomes an orphan object. D-09 makes this
unreachable from the UI (the form has no submit button), but the code path is live and reachable by
direct POST.

**Fix:** Either refuse the non-htmx transport before doing the work, or carry the keys through the
redirect; a comment alone is not sufficient, since the cost is paid in storage.

### IN-05: The free-slot ceiling is derived from client-supplied state, so it bounds nothing in storage

**File:** `app/pages/ads.py:855-857`

**Issue:** `free = settings.max_images_per_ad - len(image_keys)` where `image_keys` comes from the
request's hidden fields. A client that simply omits `images` gets the full ceiling on every request,
so an authenticated user can write unbounded objects into their prefix by repeating the call. The
real per-ad limit is enforced at save time (`own_image_keys`), which is correct; the upload-time
value is a UI-consistency figure, not a quota. (No regression — the previous client-side check
bounded nothing server-side at all.)

**Fix:** If storage growth matters, add a per-user object/byte quota at the service boundary; if not,
say so where `free` is computed so nobody mistakes it for a resource limit.

### IN-06: The attach control has no keyboard path, and its focus style is dead CSS

**File:** `app/templates/ads/includes/media_upload_form.html:54`, `app/templates/ads/includes/media_strip.html:91`

**Issue:** The only trigger is `<label ... for="file-input">`, and the input carries `hidden`
(`display:none`). Labels are not focusable and a `display:none` input is out of the tab order, so
the "+ ФАЙЛ" control cannot be reached or activated by keyboard. `app/static/css/app.css:2071`
styles `.media-tile--add:focus-visible`, which can never match. Carried over from the pre-phase
markup rather than introduced here, but this phase rewrote both files.

**Fix:** Use the visually-hidden pattern instead of `hidden` (`position:absolute; width:1px;
height:1px; clip-path:inset(50%)`) so the file input keeps focus, and style
`.media-tile--add:has(+ input:focus-visible)` — or give the label `tabindex="0"` with a keydown
forwarding handler (which the phase's no-new-JS constraint disallows, so the first option is
preferred).

---

_Reviewed: 2026-09-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

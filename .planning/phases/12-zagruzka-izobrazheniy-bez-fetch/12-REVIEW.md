---
phase: 12-zagruzka-izobrazheniy-bez-fetch
reviewed: 2026-09-19T11:40:12Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - app/pages/ads.py
  - app/services/image_keys.py
  - app/services/image_upload.py
  - app/templates/ads/includes/autosave_response.html
  - app/templates/ads/includes/media_refusals.html
  - app/templates/ads/includes/media_strip.html
  - app/templates/ads/includes/media_upload_form.html
  - tests/test_nginx_body_limit.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_ads_image_upload.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_origin_guard_on_destructive_routes.py
  - tests/test_services/test_image_keys.py
  - tests/test_services/test_images.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 0
  warning: 3
  info: 9
  total: 12
status: issues_found
---

# Phase 12: Code Review Report (re-review after gap-closure plans 12-06…12-10)

**Reviewed:** 2026-09-19T11:40:12Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

This is a **re-review** that overwrites the 2026-09-19T00:00:00Z artifact (14 findings: 2 critical,
6 warning, 6 info). Every prior finding is dispositioned below — eight verified **closed** against
current source, six carried forward **open**. Two new warnings and four new info items are added.

Both shipping blockers are genuinely fixed, and fixed at the right seam rather than papered over:

* **CR-01** — the autosave that the upload response itself orders no longer repaints the tray.
  `repaint_media` (`app/pages/ads.py:451`) defaults to `False` and is set true by exactly one
  caller, and only when a key was actually removed (`ads.py:619-621, 681`); the include is
  conditional (`autosave_response.html:60-65`). Two regressions now render the two fragments
  against each other (`test_ads_image_upload.py:887`, `test_ads_editor.py:690`) — the exact
  cross-handler rule whose absence let the defect ship.
* **CR-02** — the ownership refusal answers with the **confirmed subset**, not an empty strip
  (`ads.py:1009-1011`, `partition_own_image_keys`). Verified by test at `:767` (`keys == [mine]`).

The suite additions are **not vacuous**. I checked the measuring rules specifically:
`test_nginx_body_limit.py:213` mutates a copy in memory and asserts the rule reddens;
`test_origin_guard_on_destructive_routes.py:925` asserts the AST walk complains on an empty
corpus; `test_htmx_markup_gates.py:7345` substitutes `this:drop` on **both** sides of the
overlay-strategy equality; `test_htmx_gates.py:5150` declares the single `HX-Reswap` use by a key
taken from a reddened run. `test_ads_image_upload.py:413` measures `mock_s3.call_count == 0` on
both guard branches, which is what proves the origin check sits *above* the work rather than
merely returning 403. Targeted run: `test_ads_image_upload.py test_ads_editor.py test_image_keys.py
test_nginx_body_limit.py` — **76 passed**.

What the gap closure did **not** reach, and what this review adds:

1. `hx-sync="this:queue last"` was put on the upload form, and a machine gate now holds it equal to
   the ad form's. But `this:` scopes a queue to **one element**, and these are two sibling forms —
   so the ad form's `×`-removal autosave and an in-flight upload still interleave, and the
   `repaint_media` gate is *open* on exactly that path (WR-07). The gate's own failure message
   claims equality prevents "плитки пропадают с экрана БЕЗ сообщения"; equality does not prevent it
   across forms.
2. The ownership-refusal branch skips the file loop entirely, so on the *non-attacker* reachability
   named as residual (б) the user's entire freshly picked batch is discarded with no message naming
   a single file (WR-08). The suite enshrines this at `:715` and `:767`.

All three review-driven behaviour changes agree on strip semantics and I could not break them:
key-check refusal / ceiling / per-file storage failure all **REPLACE** `#media-strip` from
`request-snapshot ∩ own-keys` plus newly stored keys; only the part-count branch **APPENDS**
(`HX-Reswap: beforeend`), correctly, because it never parsed a single `images` field.

## Structural Findings (fallow)

No structural pre-pass was supplied with this review invocation.

## Narrative Findings (AI reviewer)

### Disposition of prior findings

| ID | State | Evidence |
|---|---|---|
| CR-01 | **closed** (12-07) | `ads.py:451,486,619-621,681`; `autosave_response.html:60-65`; regressions `test_ads_image_upload.py:887`, `test_ads_editor.py:690,723` |
| CR-02 | **closed** (12-06) | `ads.py:1009-1011,1016,1043-1045`; regression `test_ads_image_upload.py:767` (`keys == [mine]`) — residual (б) carried below |
| WR-01 | **closed** as comment-truthfulness (12-10) | `image_upload.py:366-394`; `ads.py:886-895,1113-1126` now name the proxy ceiling as the only pre-read bound |
| WR-02 | **open** | still server-scoped; carried below |
| WR-03 | **closed** (12-10) | `ads.py:877-878`, after auth `:860`, before parse `:931`; idiom matches `ads_delete` `:1412-1413`; test `:413` asserts `call_count == 0` |
| WR-04 | **closed for the named case** (12-07) | `media_upload_form.html:64`; gate `test_htmx_markup_gates.py:7331` with two-sided teeth — residual D-16/D-17 carried; cross-form case becomes WR-07 |
| WR-05 | **closed** (12-08) | `ads.py:1165-1180`; test `:1109` (`keys == 1`, `call_count == 3`) |
| WR-06 | **closed** (12-09) | `ads.py:22,930-980`; `media_refusals.html`; registry `test_htmx_gates.py:5133-5150`; test `:1220` incl. scope control at `:1326` |
| IN-01 | **closed** (12-06 + 12-10) | `grep -rn "test_uploads\|routes/uploads" tests/` returns **nothing**; only survivor is a past-tense provenance line in `image_upload.py:10` |
| IN-02 | **open** | carried below |
| IN-03 | **open** | carried below |
| IN-04 | **open** | carried below |
| IN-05 | **open** (accepted assumption) | carried below |
| IN-06 | **open** | carried below |

**Named residuals kept on the record (documented, not defects of this batch):**

* **R-1 / 12-06 (б)** — a key already in `Ad.images` that fails today's `_IMAGE_KEY_PATTERN` is
  still detached and gets a nameless refusal row (`ads.py:1065-1079`). This is the reachability
  that makes WR-08 below matter without an attacker.
* **R-2 / 12-07 D-17** — an aborted batch orphans objects; two tabs count free slots from their own
  snapshots (`ads.py:1081-1096`).
* **R-3 / 12-07 D-16** — under `this:queue last`, a third rapid file pick evicts the second
  (`media_upload_form.html:37-43`).
* **R-4 / 12-08** — a client-aborted batch is not reached by the per-file `except HTTPException`
  (`ClientDisconnect` is not an `HTTPException`; it propagates out of the loop at `ads.py:1166`).

---

## Warnings

### WR-02: The 64M body ceiling is still server-wide, not scoped to the upload route (carried open)

**File:** `nginx/nginx.conf.template:82`, `nginx/nginx-http.conf.template:42`

**Issue:** Unchanged since the first review. `client_max_body_size 64M;` sits in the `server`
block, so every endpoint — including unauthenticated ones, since the proxy decides before the app
does — accepts a 64 MB body to serve one route. The formula the comment derives
(`max_images_per_ad × max_image_size_mb`) applies to `/ads/images` alone. No gap plan claimed it.

**New in this review:** the fix is now actively **cemented by a test**.
`tests/test_nginx_body_limit.py:164` asserts `len(declared) == 1` per template
("объявлений потолка тела запроса N, а нужно ровно одно"), and `_declared_ceilings`
(`:93-98`) has no notion of which block a value belongs to. Adding a scoped
`location = /ads/images { client_max_body_size 64M; }` under a tighter server default would
therefore redden the suite. Anyone fixing WR-02 must fix the rule in the same commit.

**Fix:**

```nginx
client_max_body_size 20M;

location = /ads/images {
    client_max_body_size 64M;
    proxy_pass http://app:8000;
    # ...same proxy headers as the generic location...
}
```

and teach `_declared_ceilings` to return `(block, bytes)` pairs, asserting "exactly one *server*
declaration, and the `/ads/images` location declaration ≥ `max_images_per_ad × max_image_size_mb`"
instead of "exactly one declaration in the file".

### WR-07: A `×` removal that overlaps an in-flight upload resurrects the deleted attachment or drops the fresh one (new)

**File:** `app/templates/ads/includes/media_upload_form.html:64`, `app/templates/ads/form.html:110-117`,
`app/pages/ads.py:619-621,681`, `app/pages/ads.py:1009-1011,1188-1203`

**Issue:** 12-07 closed the *upload-vs-upload* race with `hx-sync="this:queue last"` and holds it
equal to the ad form's strategy with a machine gate. But `this:` scopes an htmx queue to **that
element**, and the upload form and `#ad-form` are deliberately siblings — the include's own comment
(г) says so: «очередь одной на другую не распространяется». The `repaint_media` gate that closed
CR-01 is, by construction, **open** on the removal path (`media_changed == True`), which is exactly
the ad-form request that can be in flight beside an upload. Neither response carries a version
token, and both rewrite overlapping regions:

Starting DOM hidden fields `[A, B]`.

1. User picks file C → `POST /ads/images` in flight, carrying `images=A,B`.
2. User clicks `×` on A → `POST /ads/{id}/edit` with `images=A,B`, `remove_image=A` →
   `media_changed` true → commit `ad.images=[B]` → OOB `#media-tray` rendered from the DB as `[B]`.

* Removal response lands **last**: the tray becomes `[B]`. Key C is stored in S3 but its hidden
  field is gone from the document, so it is an **orphan object and lost work** — the user watched a
  tile appear and then vanish, with no message.
* Upload response lands **last**: the tray becomes `[A, B, C]`. A is **resurrected in the DOM**, and
  the `HX-Trigger-After-Swap: ads-image-attached` autosave that the same response orders
  (`ads.py:1233-1234`) writes A straight back into `ad.images`. The user's deletion is silently
  undone.

The window is not microscopic: an upload holds the request open for decode + resize + two S3 round
trips. This is classified **WARNING** rather than BLOCKER only because it needs an interleaving,
whereas CR-01/CR-02 fired on a single-user, single-action path.

Note also that the gate's failure text (`test_htmx_markup_gates.py:7318-7331`) justifies equality by
"плитки пропадают с экрана БЕЗ сообщения" — equality of two `this:`-scoped strategies does not buy
that property across two elements. The record over-claims what the gate measures.

**Fix:** make the two forms share one queue, and make the removal repaint safe against a
concurrently-arriving upload. Smallest correct change is a shared sync group plus rendering the
removal repaint from the union of DB state and the request snapshot:

```jinja
{# media_upload_form.html and form.html: one named group, not `this:` #}
sync='#media-strip:queue last'
```

```python
# ads.py::_save_from_editor — the repaint must not claim authority over keys
# that a concurrent upload has stored but this request never saw.
response = await _autosave_response(
    request, db, settings, user, saved, repaint_media=media_changed
)
```

If a shared group is rejected (it also serialises text autosaves behind uploads), then at minimum
gate the removal repaint on "no upload in flight" with an `hx-sync` group on the ad form's
`remove_image` submit, and record the residual the way D-16/D-17 were recorded.

### WR-08: The ownership refusal silently discards the entire freshly picked batch (new)

**File:** `app/pages/ads.py:1016-1045` (branch), `app/pages/ads.py:1046-1186` (skipped `else`)

**Issue:** When any hidden `images` value fails `partition_own_image_keys`, the handler appends one
nameless row and takes the `if` branch — **the whole file loop is skipped**. The files the user just
selected are never read, never stored, and **never mentioned**: the single row says «Одно из
вложений недоступно. Обновите страницу и добавьте изображение заново», which speaks about a *key*,
not about the five photos that just disappeared from the file dialog. `attached` stays `False`, so
no autosave, no event, no second signal of any kind.

For a forged request this is correct and deliberate ("работа ради запроса, уже признанного
подделанным, НЕ делается"). But the branch is reachable **without an attacker** — that is exactly
residual R-1: a key predating filename normalisation, sitting in `Ad.images`, arrives in the hidden
fields and fails today's pattern. In that state the user does not have a forged request; they have
a legacy attachment. Every upload attempt they make from then on is a silent no-op until they
happen to reload the page. The suite enshrines the behaviour at `:715-762` and `:767-820`
(`mock_s3.call_count == 0` with a valid `cat.png` in the batch), so nothing will notice.

The strip *is* rewritten authoritatively on this branch, so it is also the branch that answers with
an "authoritative-looking but incomplete" state in the sense the phase set out to avoid: the
document now believes the batch never happened.

**Fix:** separate "this value is not yours" from "therefore nothing else in the request counts".
Refuse the offending values, then still refuse each *file* by name so the user learns their files
did not land:

```python
if offending or len(string_images) != len(raw_images):
    refusals.append(Rejected(display_name="", reason=INACCESSIBLE_IMAGE_MESSAGE))
    # Файлы партии в хранилище не идут — но человек обязан прочесть, что они
    # НЕ прикрепились, иначе отказ по ключу молча съедает его выбор.
    for part in form_data.getlist(UPLOAD_FILE_FIELD):
        if isinstance(part, str):
            continue
        refusals.append(
            Rejected(display_name=safe_filename(part.filename),
                     reason=INACCESSIBLE_IMAGE_MESSAGE)
        )
```

and extend `test_an_own_key_survives_a_foreign_key_in_the_same_batch` to assert the batch's files
are each named (`mock_s3.call_count == 0` stays, so the anti-orphan property is preserved).

## Info

### IN-02: `oob` still reaches the strip by inheriting a variable set for a different include (carried open)

**File:** `app/templates/ads/includes/autosave_response.html:55,60-65`

**Issue:** `{% set oob = true %}` is written for `ads/includes/autosave.html`; `media_strip.html`
picks it up only because it is included later in the same scope. Reordering the two includes
silently drops `hx-swap-oob` from the tray — the failure mode is "the removed tile stays on screen",
the bug 12-03 fixed. 12-07 made the include *conditional*, which adds a second way to reason wrong
about it, and the template now documents the fragility (`:46-49`) as an owner-deferred open item.
Documented ≠ fixed.

**Fix:** `{% with oob = true %}{% include ... %}{% endwith %}` around each include, or pass the flag
per include.

### IN-03: The parsed form is still never closed (carried open)

**File:** `app/pages/ads.py:931-933`, `app/pages/ads.py:574`

**Issue:** `await request.form(...)` used bare — no `async with`, no `await form_data.close()`.
FastAPI only registers the close callback for endpoints that *declare* a body field, and neither of
these does, so the spooled temp files (now up to `MAX_UPLOAD_PARTS = 64` per request) rely on
refcount collection rather than deterministic release.

**Fix:** `async with request.form(max_files=..., max_fields=...) as form_data:` with the batch loop
inside the block. Note the `except StarletteHTTPException` must stay outside the `async with`.

### IN-04: The no-JavaScript path still performs the whole upload and throws the keys away (carried open)

**File:** `app/pages/ads.py:1237-1239`, `app/pages/htmx.py:830-831`

**Issue:** A non-htmx POST runs the full batch (decode + two S3 writes per accepted file) and then
`respond()` returns 302 to `/ads/new`, where the strip renders from `ad.images`. Every accepted key
is discarded and every stored object becomes an orphan. The new origin guard closes the *cross-site*
reachability but not a same-origin scripted or curl POST, and the parts-refusal branch has the same
shape (`:978-980`).

**Fix:** refuse the non-htmx transport before doing the work, or carry the keys through. A comment
is not sufficient when the cost is paid in storage.

### IN-05: The free-slot ceiling is still derived from client state (carried open, accepted assumption)

**File:** `app/pages/ads.py:1096`

**Issue:** `free = max(0, settings.max_images_per_ad - len(image_keys))` where `image_keys` comes
from the request's hidden fields. A request that omits `images` gets the full ceiling every time, so
an authenticated user can write unbounded objects into their own prefix by repeating the call. The
real per-ad limit is enforced at save time by `own_image_keys`, correctly. 12-07 recorded this as
`accepted-assumption` in `deferred-items.md` and annotated the line (`:1081-1095`) rather than
changing it — which is the right handling of a named assumption, so this stays Info.

**Fix (if storage growth ever matters):** a per-user object/byte quota at the service boundary.

### IN-06: The attach control still has no keyboard path; its focus style is still dead CSS (carried open)

**File:** `app/templates/ads/includes/media_upload_form.html:79`, `app/templates/ads/includes/media_strip.html:92`, `app/static/css/app.css:2071`

**Issue:** The only trigger is `<label for="file-input">` and the input still carries `hidden`
(`display:none`). Labels are not focusable and a `display:none` input is out of the tab order, so
"+ ФАЙЛ" cannot be reached or activated by keyboard. `.media-tile--add:focus-visible` can never
match. Verified unchanged in this batch.

**Fix:** use the visually-hidden pattern (`position:absolute; width:1px; height:1px;
clip-path:inset(50%)`) instead of `hidden`, and style `.media-tile--add:has(+ input:focus-visible)`.

### IN-07: Repeated part-count refusals accumulate duplicate rows (new)

**File:** `app/pages/ads.py:972`, `app/templates/ads/includes/media_refusals.html:41-43`

**Issue:** The part-count branch answers with `HX-Reswap: beforeend`, so its row is *appended* to
`#media-strip`. Nothing removes it except a later `/ads/images` response that swaps `innerHTML`.
A user who drops an over-large folder twice in a row gets two identical rows; the autosave's OOB
`#media-tray` repaint does not clear them (by design — they are siblings of the tray). The handler's
own comment claims "снимается строка сама", which is true only for the *next successful* upload.

**Fix:** either render the row into a dedicated `#media-refusals` sibling swapped `innerHTML`
(which also makes the row's lifetime readable from the markup), or note the accumulation where the
`beforeend` header is written so the next reader does not mistake it for self-clearing.

### IN-08: A string-valued part named `files` is silently skipped, while a file part named `images` is refused (new)

**File:** `app/pages/ads.py:1128-1129` vs `app/pages/ads.py:1016`

**Issue:** `if isinstance(part, str): continue` drops non-file parts under `UPLOAD_FILE_FIELD`
without a word, whereas the mirror case — a *file* part under `images` — is deliberately refused
rather than dropped, with the rationale written out twice ("молча выброшенная часть превратила бы
кривой запрос в «успешную загрузку без картинки»"). A request whose file field arrives as a text
part therefore gets a 200, an unchanged strip, and no refusal row — precisely the outcome the
sibling branch exists to prevent. Impact is confined to a broken or hostile client.

**Fix:** treat it the same way, or record why the asymmetry is intended at the `continue`.

### IN-09: The storage-failure log records a constant and drops the driver error from the structured fields (new)

**File:** `app/pages/ads.py:1168-1173`, `app/services/image_upload.py:487-491`

**Issue:** `store_upload` replaces the real exception with `HTTPException(502, detail="Failed to
upload image to storage")` and raises it **without `from exc`**, so `detail` is a constant. The
caller then logs `detail=str(exc.detail)` — a fixed English string in every record, carrying zero
diagnostic value. The bucket name / endpoint / driver error the comment at `image_upload.py:161-165`
says is "адресована ЖУРНАЛУ" survives only inside `exc_info`'s implicit `__context__` chain, and
only because the re-raise happens inside the `except` block. Neither the failing key nor the
filename is logged at all.

**Fix:**

```python
# image_upload.py
except Exception as exc:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to upload image to storage",
    ) from exc
```

```python
# ads.py — log what identifies the failure, not the constant
logger.warning("upload_storage_failed", user_id=user.id,
               filename=safe_filename(part.filename), exc_info=True)
```

### IN-10: The only machine gate over the new origin guard is a count, and the guard sits outside both gate universes (new)

**File:** `tests/test_pages/test_origin_guard_on_destructive_routes.py:729,736-752`

**Issue:** `ORIGIN_GUARD_CALL_SITES_MEASURED = 14` moved with the D-15 decision, and the file states
honestly that `ads_images_upload` joins the four routes that carry the guard while lying in neither
gate's universe — "снятый с любого из них гард не покраснит ничего". Concretely: delete
`ads.py:877-878` and add a guard call anywhere else and this gate stays green; the behavioural test
(`test_ads_image_upload.py:413`) is then the sole protection. That is adequate today, but it means
the phase's newest security decision rests on one test rather than on the structural gate the
docstring of `is_same_origin` points readers to.

**Fix:** no code change required. If D-15 is to be durable, widen the second gate's universe from
"confirmed-deletion path suffix" to "routes that write to object storage", or add
`ads.py::ads_images_upload` to an explicit `MUST_GUARD` set checked by name rather than by count.

---

_Reviewed: 2026-09-19T11:40:12Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

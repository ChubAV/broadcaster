---
phase: 01-interfeysnyy-fundament
reviewed: 2026-08-09T20:56:10Z
depth: standard
files_reviewed: 78
files_reviewed_list:
  - app/main.py
  - app/pages/__init__.py
  - app/pages/accounts.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/groups.py
  - app/pages/history.py
  - app/pages/schedules.py
  - app/routes/uploads.py
  - app/static/css/app.css
  - app/templates/accounts/connect_max.html
  - app/templates/accounts/connect_tg_user.html
  - app/templates/accounts/connect_wa.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/connect_status.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/admin/dashboard.html
  - app/templates/admin/group_info_detail.html
  - app/templates/admin/groups_info.html
  - app/templates/admin/history_partial_cards.html
  - app/templates/admin/user_detail.html
  - app/templates/admin/user_history.html
  - app/templates/admin/user_history_detail.html
  - app/templates/admin/users.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/ad_card.html
  - app/templates/ads/list.html
  - app/templates/ads/partial_cards.html
  - app/templates/auth/forgot_password.html
  - app/templates/auth/forgot_password_reset.html
  - app/templates/auth/forgot_password_verify.html
  - app/templates/auth/login.html
  - app/templates/auth/register.html
  - app/templates/auth/register_complete.html
  - app/templates/auth/register_verify.html
  - app/templates/auth_base.html
  - app/templates/base.html
  - app/templates/billing/balance.html
  - app/templates/billing/plans.html
  - app/templates/components/alert.html
  - app/templates/components/avatar.html
  - app/templates/components/badge.html
  - app/templates/components/button.html
  - app/templates/components/card.html
  - app/templates/components/empty_state.html
  - app/templates/components/field.html
  - app/templates/components/filters.html
  - app/templates/components/modal.html
  - app/templates/components/mono.html
  - app/templates/components/progress.html
  - app/templates/components/table.html
  - app/templates/components/toggle.html
  - app/templates/dashboard.html
  - app/templates/dashboard/includes/recent_send_card.html
  - app/templates/groups/includes/group_row.html
  - app/templates/groups/list.html
  - app/templates/groups/partial_cards.html
  - app/templates/history/detail.html
  - app/templates/history/includes/history_card.html
  - app/templates/history/list.html
  - app/templates/history/partial_cards.html
  - app/templates/includes/messenger_icon.html
  - app/templates/profile.html
  - app/templates/schedules/form.html
  - app/templates/schedules/includes/schedule_row.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - tests/conftest.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_schedules_profile_timezone.py
  - tests/test_routes/test_uploads.py
  - tests/test_routes/test_wa_sync_status.py
  - tests/test_templates/__init__.py
  - tests/test_templates/test_ads_form_security.py
  - tests/test_templates/test_components.py
findings:
  critical: 2
  warning: 10
  info: 9
  total: 21
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-08-09T20:56:10Z
**Depth:** standard
**Files Reviewed:** 78
**Status:** issues_found

## Summary

Phase 01 migrated 45 templates onto `base.html` + a shared component library, added a
confirm-modal component, and closed the CR-01 stored-XSS finding from the previous review.
The component library itself is in good shape: **no `|safe`, no `{% autoescape false %}`, no
`Markup(`, and no string-concatenated markup exists anywhere under `app/templates/`,
`app/pages/`, or `app/routes/`** (verified by grep). All 45 templates compile cleanly under a
`FileSystemLoader` sweep. Every macro takes text/number/boolean parameters and emits escaped
output; block-call slots (`cell`, `filters`, `modal`) keep caller markup in the caller.

### CR-01 closure: verified, holds

I traced the fix rather than assuming it. **CR-01 is genuinely closed.** Evidence:

1. `app/routes/uploads.py:21-38` — `safe_filename()` splits on `[\\/]` and keeps only the last
   segment, substitutes every character outside `[A-Za-z0-9._-]` with `_`, truncates *after*
   substitution, and falls back to a non-empty `"upload"`. The key is
   `f"{user_id}/{uuid4().hex}_{safe}"` (`uploads.py:66-67`), so the object key contains exactly
   one `/` and always begins with the caller's own `user_id` prefix. `..` survives the character
   filter but can never form a lone path segment because it is always prefixed by
   `{uuid4().hex}_`. Traversal, quote injection, angle brackets and NUL are all closed.
2. `app/templates/ads/form.html:56-91` — the preview is built with `createElement` +
   `replaceChildren` and populated by property assignment (`img.src`, `img.alt`,
   `label.textContent`, `hidden.value`) with the remove handler attached via `addEventListener`.
   There is no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, or
   markup-building template literal in the file.
3. `ads/form.html:54` seeds `imagePaths` through `| tojson`, which escapes `<`, `>`, `&`, `'`
   to `\uXXXX`, so a stored `</script>` cannot terminate the script element.
4. Every server-side rendering of `Ad.images` goes through an autoescaped attribute:
   `ads/includes/ad_card.html:28` (`get_image_url`), `history/detail.html:80-81` and
   `admin/user_history_detail.html:91-92` (`resolve_image_url`). `resolve_image_url`
   (`app/pages/common.py:27-33`) returns a value verbatim only when it starts with `http://` or
   `https://`, so no `javascript:` or `data:` scheme can reach an `href`.

Delete-confirmation panels also check out: **12 of the 13 panels are triggered by a real
`<form method="post" action="/…/delete">` carrying `x-on:submit.prevent`**, so the page degrades
to a plain POST when Alpine is unavailable (`ads/includes/ad_card.html:54`,
`groups/includes/group_row.html:73`, `schedules/includes/schedule_row.html:76`,
`accounts/list.html:72,93,119`, `accounts/partial_cards.html:46,67,93`,
`accounts/partials/sync_status_card.html:64,80,95`, `admin/user_detail.html:133`). The bulk
group delete is the one exception (see WR-04). I also verified the bulk snapshot logic in
`groups/list.html:111-133` and found **no TOCTOU or set-mismatch bug**: the checkbox set is read
exactly once, materialised into hidden inputs inside the modal's own form before the open event
is dispatched, and the counter is written from the same array; the injected inputs carry no
`.group-checkbox` class so they cannot re-enter the query, and `type=hidden` keeps them out of
the focus trap's `offsetParent !== null` filter.

**However, the review is not clean.** Two BLOCKERs remain, both in the files this phase touched:
a cross-tenant authorization gap in `app/pages/schedules.py` that lets one user schedule another
user's ad (exfiltrating its content and charging the victim's balance), and a second,
un-closed injection vector in `app/routes/uploads.py` — the phase normalised the *filename* but
left the *Content-Type* fully client-controlled, so an `image/svg+xml` payload is stored and then
linked with `<a href … target="_blank">` from two shipped templates. Ten warnings follow,
several of which concern the durability of the CR-01 fix itself (WR-02 and WR-03: the ads editor
has zero HTTP-level coverage, and its only security test greps template source text).

---

## Critical Issues

### CR-01: Schedule create/update accept `ad_id` and `account_id` with no ownership check — cross-tenant ad exfiltration and billing charged to the victim

**File:** `app/pages/schedules.py:166-215` (create), `app/pages/schedules.py:270-324` (update)

**Issue:**
`ad_id` and `account_id` arrive as `Form(...)` values and are written straight into the
`Schedule` row. Only `group_ids` is validated for ownership:

```python
# schedules.py:184-194 — group_ids IS validated
if group_ids:
    valid_groups = (await db.execute(
        select(Group.id).where(
            Group.id.in_(group_ids),
            Group.account_id == account_id,
            Group.user_id == user.id,        # <-- ownership enforced here
        ))).scalars().all()
    group_ids = [gid for gid in group_ids if gid in valid_groups]
...
# schedules.py:204-213 — ad_id / account_id are NOT validated
schedule = Schedule(ad_id=ad_id, account_id=account_id, group_ids=group_ids, ...)
```

`schedules_update` repeats the defect at lines 314-315 (`schedule.ad_id = ad_id`,
`schedule.account_id = account_id`) — the schedule row itself is ownership-scoped by the
`join(Ad).where(Ad.user_id == user.id)` lookup at 283-287, but the *new* `ad_id` written into it
is not.

Nothing downstream re-checks. `collect_due_schedules`
(`app/application/scheduling/use_cases.py:48-79`) selects due schedules and derives
`user_id = ad.user_id`; `send_message_once` (same file, 143-183) loads the ad, group and account
by id independently and never asserts they share an owner.

Concrete exploit, all steps available to any registered user A:

1. A posts `/schedules/new` with `ad_id` = victim B's ad id, `account_id` = A's own active
   account, `group_ids` = A's own groups. The `group_ids` filter passes (they really are A's
   groups on A's account), so nothing is stripped.
2. The scheduler dispatches: `ad` is B's ad, `account` is A's account with status `active`.
3. `send_message_once` sends **B's ad title, text and images into A's group** — a direct read of
   another tenant's content, including the S3 image keys.
4. The `SendLog` is written with `user_id=ad.user_id`, i.e. **B is billed** for the send and the
   send appears in B's history and in the admin's view of B.

Ad ids are small sequential integers, so enumeration is trivial.

**Fix:** validate both foreign keys against the caller before constructing/mutating the row, in
both handlers:

```python
ad = (await db.execute(
    select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
)).scalar_one_or_none()
account = (await db.execute(
    select(MessengerAccount).where(
        MessengerAccount.id == account_id,
        MessengerAccount.user_id == user.id,
    )
)).scalar_one_or_none()
if not ad or not account:
    return RedirectResponse(url="/schedules", status_code=302)
```

Then use `ad.id` / `account.id`. Add a defence-in-depth assertion in
`send_message_once` as well — refuse to send when
`ad.user_id != group.user_id or ad.user_id != account.user_id`, and log it — so an equivalent
gap in any future writer cannot become a silent cross-tenant send.

---

### CR-02: Upload endpoint trusts the client `Content-Type`; `image/svg+xml` is stored and then linked with `<a href target="_blank">`

**File:** `app/routes/uploads.py:48-52`, `app/routes/uploads.py:71-80`; sinks at
`app/templates/history/detail.html:80-81` and `app/templates/admin/user_history_detail.html:91-92`

**Issue:**
The only content check is a prefix test on the *client-supplied* multipart header, and that same
unvalidated string is then written to the object as its stored `ContentType`:

```python
# uploads.py:48-52
if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(400, "File must be an image")
...
# uploads.py:71-80 -> app/services/s3.py:35 -> put_object(ContentType=content_type)
await upload_file_to_s3(content=content, key=key, content_type=file.content_type, ...)
```

The file bytes are never sniffed. `image/svg+xml` passes the prefix test, and
`safe_filename()` happily preserves a `.svg` extension (`.` and letters are in the allowlist).
The object is therefore served from `s3_public_url` as an active SVG document.

This is not confined to `<img>` rendering. Two shipped templates wrap the image in a link that
navigates the browser directly to the object:

```jinja
{# history/detail.html:80-81 and admin/user_history_detail.html:91-92 #}
<a href="{{ resolve_image_url(img) }}" target="_blank" rel="noopener">
  <img src="{{ resolve_image_url(img) }}" alt="">
</a>
```

Following that link executes the SVG's `<script>` on the storage origin, with the victim's
cookies for that origin. The second of those two templates is the **admin** send-detail page, so
the click can be induced on a privileged operator. If `s3_public_url` is served from the
application's own registrable domain (a CDN path or an S3 gateway behind the same nginx — both
normal for this deployment), this is stored XSS against the application. If it is a genuinely
separate origin, the blast radius is that origin plus a credible phishing surface — still not
acceptable for user-uploaded content.

Combined with WR-01 (arbitrary `images` values accepted at ad save time), the attacker does not
even need the upload endpoint to place the key.

**Fix:** allowlist the type, sniff the bytes, and never echo the client header to storage:

```python
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff":      "image/jpeg",
    b"GIF87a":            "image/gif",
    b"GIF89a":            "image/gif",
}

if file.content_type not in ALLOWED_IMAGE_TYPES:
    raise HTTPException(400, "Unsupported image type")

content = await file.read()
sniffed = next((t for sig, t in _MAGIC.items() if content.startswith(sig)), None)
if sniffed is None and not (content[:4] == b"RIFF" and content[8:12] == b"WEBP"):
    raise HTTPException(400, "File content is not a supported image")
detected = sniffed or "image/webp"
if detected != file.content_type:
    raise HTTPException(400, "Declared type does not match file content")
```

Pass `detected` (not `file.content_type`) to `upload_file_to_s3`, and set
`ContentDisposition="attachment"` plus `X-Content-Type-Options: nosniff` on the bucket/CDN as
defence in depth.

---

## Warnings

### WR-01: Ad save accepts arbitrary `images` strings — no validation that the key belongs to the caller

**File:** `app/pages/ads.py:133-135`, `app/pages/ads.py:183-187`

**Issue:** Both handlers do `image_list = [v for v in form_data.getlist("images") if v.strip()]`
and persist it verbatim. Nothing checks that each value is a key under `{user.id}/`, that it
came from `/api/uploads/image` at all, that it is not an absolute external URL, or that the list
is bounded (the 10-image cap in `ads/form.html:99` is client-side only). Consequences:

- `resolve_image_url` returns `http(s)` values verbatim, so an ad author can plant
  `https://attacker.example/px.gif`. It is loaded **automatically** as `<img src>` in
  `admin/user_history_detail.html:92` and `history/detail.html:81`, leaking the viewing admin's
  IP and User-Agent, and the accompanying `<a href>` is a click-through phishing surface.
- A user can reference another tenant's S3 key (`{other_user_id}/{uuid}_name.png`) and have the
  app render and *send* it. The uuid makes this unguessable in isolation, but CR-01 above hands
  out exactly those keys.
- All 10 upload-cap and MIME guarantees earned by `uploads.py` are bypassable by posting the
  form directly.

**Fix:** validate on save.

```python
_KEY_RE = re.compile(r"^\d+/[0-9a-f]{32}_[A-Za-z0-9._-]{1,100}$")

def _own_image_keys(values: list[str], user_id: int) -> list[str]:
    out = []
    for v in values:
        v = v.strip()
        if _KEY_RE.fullmatch(v) and v.split("/", 1)[0] == str(user_id):
            out.append(v)
    return out[:10]

image_list = _own_image_keys(form_data.getlist("images"), user.id)
```

### WR-02: Template globals bypass dependency injection — the ads editor 500s and has no HTTP-level test coverage

**File:** `app/pages/common.py:36-38`

**Issue:**

```python
templates.env.globals["get_image_url"]   = lambda key: get_image_url(key, get_settings().s3_public_url)
templates.env.globals["resolve_image_url"] = _resolve_image_url          # also calls get_settings()
templates.env.globals["s3_public_url"]   = lambda: get_settings().s3_public_url
```

`get_settings` here is `app.config.get_settings`, which is `@lru_cache`-decorated and constructs
`Settings()` straight from the process environment. It is *not* the `app.dependencies` symbol
that `conftest.py:48` overrides, and it ignores the `settings` argument threaded through
`create_app(settings=...)` (`app/main.py:62-64`). So:

- In production, `create_app(settings=custom)` silently does not apply to any image URL, and the
  first call freezes whatever env was present at that moment.
- In tests, `/ads/new` and `/ads/{id}/edit` — which call `s3_public_url()` unconditionally at
  `ads/form.html:53` — return 500 in a clean checkout. The phase acknowledges this in
  `tests/test_templates/test_ads_form_security.py:1-17` as "WR-06 … deferred to Phase 2".

The consequence that matters for this review: **the single template that carried the CR-01
stored-XSS is the one template with no rendering test at all.** It is absent from
`DIALOG_SWEEP_URLS` (`test_responsive_markup.py:3000-3013`) and from `ROWHEAD_PAGES`, so no
sweep in the suite ever renders it.

**Fix:** make the globals take the resolved settings from the request instead of a module-level
cache — e.g. register them per-app in `create_app` with the injected `settings` bound:

```python
def register_template_globals(settings: Settings) -> None:
    templates.env.globals["get_image_url"]     = lambda key: get_image_url(key, settings.s3_public_url)
    templates.env.globals["resolve_image_url"] = lambda key: _resolve_image_url(key, settings.s3_public_url)
    templates.env.globals["s3_public_url"]     = lambda: settings.s3_public_url
```

Call it from `create_app`. Then add `/ads/new` and `/ads/{id}/edit` to the rendered-page sweeps.

### WR-03: The CR-01 regression test asserts on template *source text*, not on behaviour

**File:** `tests/test_templates/test_ads_form_security.py:52-98`

**Issue:** Every assertion in this module is a substring grep over
`app/templates/ads/form.html` read from disk:

```python
offenders = [sink for sink in MARKUP_SINKS if sink in body]   # "innerHTML" in body
assert body.count("createElement") >= 3
assert "addEventListener" in body
```

The property this is meant to protect — "attacker-controlled text never reaches a markup
parser" — is not what is being measured. This suite stays green if a sink is reintroduced in an
imported macro, in `app/static/js/`, in a sibling template, or in a handler that builds markup in
Python (exactly the class of hole the phase itself had to fix by moving the connect-status markup
out of `app/pages/accounts.py` into a partial). It also stays green if `createElement` is used
but the value is later assigned to `.innerHTML`.

**Fix:** keep the source greps as a cheap tripwire but *widen* them to the union of the template
and its imports (the resolver in `test_responsive_markup.py:_union_sources` already does this for
cell labels), and add a real behavioural assertion once WR-02 unblocks rendering:

```python
@pytest.mark.asyncio
async def test_ad_edit_does_not_reflect_hostile_image_key(authed_client, db_session):
    ad = await _seed_ad(db_session, images=['1/deadbeef_x" onerror="alert(1).png'])
    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    assert 'onerror="alert(1)' not in html
    assert "\\u0022" in html or "&#34;" in html   # value arrived escaped, in JSON or attribute
```

### WR-04: Bulk group delete is the only delete path that does not degrade, and fails silently

**File:** `app/templates/groups/list.html:58-59`, `app/templates/groups/list.html:118-132`

**Issue:** The two bulk buttons are plain `<button type="button" onclick="…">` with no enclosing
form, and the delete branch ends in
`window.dispatchEvent(new CustomEvent('modal-open-groups-bulk-del'))`. Alpine is loaded with
`defer` (`base.html:13`); if it fails to load or is blocked while the inline script still runs,
the event has no listener, the panel stays hidden by `[x-cloak] { display: none !important; }`
(`app.css:445`), and the user gets **no feedback whatsoever** — the button is simply dead. Every
other delete on the site was deliberately reworked to survive this exact case (see the rationale
comments at `ad_card.html:48-53` and `group_row.html:70-72`); bulk delete was not.

**Fix:** at minimum, fail loudly. Guard on Alpine's presence and fall back to the existing
form-построение path used by the `deactivate` branch:

```js
if (action === 'delete') {
    if (!window.Alpine) {
        // No confirmation layer available — do not delete silently, and do not
        // delete without a confirmation either.
        alert('Подтверждение недоступно: перезагрузите страницу.');
        return;
    }
    ...
}
```

Better: render the bulk controls inside a real `<form method="post" action="/groups/bulk">` with
a `name="action" value="delete"` submit button and the checkboxes named `group_ids`, then hang
`x-on:submit.prevent` on that form — identical to the per-row pattern, and it degrades.

### WR-05: The sync-status swap silently drops the "Подключён" date

**File:** `app/templates/accounts/partials/sync_status_card.html:61` vs
`app/templates/accounts/list.html:112` and `app/templates/accounts/partial_cards.html:86`

**Issue:** The three files are documented as rendering the same row and are held in sync by
`test_accounts_three_files_*`. They are not identical in the `active` branch. List and partial
render the real connection date:

```jinja
{{- cell(text=format_datetime_for_user(account.created_at, user, '%d.%m.%Y %H:%M'),
         mono=true, muted=true, label=ACCOUNT_COLUMNS[5]) }}
```

The swap card renders a placeholder:

```jinja
{{- cell(text='—', mono=true, muted=true, label=ACCOUNT_COLUMNS[5]) }}
```

So the moment a syncing account finishes and the 5-second poll swaps its row in, the "Подключён"
column goes from a real timestamp to `—` and stays that way until a full page reload. That is
data disappearing from the page as a side effect of a status refresh, and it is not covered by
the sync tests (they compare column *names* and label sets, not values).

**Fix:** pass the account's `created_at` into the render call in `accounts_sync_status`
(`app/pages/accounts.py:683-690`) and render it in the `active` branch, so the swapped row is a
faithful replacement.

### WR-06: Telegram connect endpoints accept a client-supplied `session_id` with no owner binding

**File:** `app/pages/accounts.py:235-246`, `249-268`, `271-308`, `311-340`

**Issue:** `qr-status`, `refresh-qr`, `verify-2fa` and `complete` all authenticate the caller and
then use whatever `session_id` the caller supplies against the process-global `_qr_sessions`
map, with no check that the session was started by that user:

```python
session_string = await complete_auth(session_id)     # accounts.py:326
...
account = MessengerAccount(user_id=user.id, type="tg_user",
                           credentials=session_string, status="active")   # 331-336
```

Any authenticated user who learns another user's in-flight `session_id` mints a
`MessengerAccount` under **their own** `user_id` holding the **victim's** Telegram session
string — i.e. full takeover of the victim's Telegram account. `verify-2fa` is worse still: it
lets an arbitrary caller submit 2FA passwords against someone else's login attempt.

The id is `uuid.uuid4().hex[:16]` (`app/messengers/telegram_user.py:57`) — 64 bits, not
brute-forceable, so this is a missing-authorization defect rather than an open door. But the
binding costs nothing and the value ends up in a URL query string (`connect_tg_user.html:140`),
where it is exposed to referrers, proxy logs and browser history.

**Fix:** record the owner when the session is created and check it on every use:

```python
# telegram_user.py — store owner alongside the client
_qr_sessions[session_id] = QRAuthState(client=client, qr_login=qr_login, user_id=user_id)

# accounts.py — every handler
if not owns_qr_session(session_id, user.id):
    raise HTTPException(status_code=404, detail="Сессия не найдена")
```

Also move `session_id` out of the query string into the POST body for `qr-status`.

### WR-07: Admin groups-info pager builds query strings by raw concatenation without `urlencode`

**File:** `app/templates/admin/groups_info.html:87-96`

**Issue:**

```jinja
{{ link_button('Далее', '/admin/groups-info?offset=' ~ (offset + page_size)
                        ~ ('&q=' ~ q if q else '') ~ ('&messenger=' ~ messenger if messenger else ''),
               variant='ghost', icon='arrow-right') }}
```

`q` and `messenger` are user-supplied query parameters echoed back into a URL with no
`|urlencode`. Autoescaping prevents attribute breakout, but a `q` containing `&`, `=` or `#`
injects or truncates parameters in the app's own pager link — the search silently changes or is
lost on page 2. Every other filter-forwarding site in the phase gets this right and uses
`{{ v|string|urlencode }}` (`groups/list.html:98`, `groups/partial_cards.html:6`,
`history/list.html:49`, `history/partial_cards.html:6`, `admin/user_history.html:63`,
`admin/history_partial_cards.html:7`); this one file is the outlier.

**Fix:** `~ ('&q=' ~ q|string|urlencode if q else '')` and the same for `messenger`.

### WR-08: Connect endpoints return HTTP 200 with an `{"error": …}` body for auth failures

**File:** `app/pages/accounts.py:216`, `244`, `257`, `279`, `319`

**Issue:** `return {"error": "Не авторизован"}` yields `200 OK`. Every one of these is a
JSON API called by `fetch()` from `connect_tg_user.html`. An unauthenticated request is
indistinguishable from a successful one to any monitoring, proxy, rate limiter or test that keys
off status codes, and the client only notices because it happens to inspect `data.error`.
`upload_image` in the same phase gets this right (401 via `Depends(get_current_user_id)`).

**Fix:** `raise HTTPException(status_code=401, detail="Не авторизован")`, and let the existing
`showError(data.detail)` path in the template surface it (the client already reads `data.error`;
normalise on `detail` or keep both).

### WR-09: No CSRF protection on any state-changing POST; SameSite=Lax is the only defence

**File:** all delete/toggle/bulk routes — `app/pages/ads.py:193`, `app/pages/groups.py:248,270`,
`app/pages/schedules.py:327,365`, `app/pages/accounts.py:807`; cookie set at
`app/pages/auth.py:55,329`

**Issue:** Every destructive route authenticates purely from the `access_token` cookie and
carries no CSRF token, nonce, `Origin`/`Referer` check or custom-header requirement. The only
thing standing between an attacker's page and
`POST /accounts/{id}/delete` is `samesite="lax"` on the cookie. That is load-bearing but thin:
it depends on browser version, it does not survive a future switch to `samesite="none"` (which a
cross-origin embed or a payment redirect flow could motivate), and the cookie is additionally set
**without `secure=True`**, so it is transmitted over plaintext HTTP if the app is ever reached
that way.

I am flagging this as a WARNING rather than a BLOCKER because Lax genuinely does block the
top-level cross-site form POST today, and the gap predates this phase. But the phase's whole
premise is that these delete routes are now the primary destructive surface behind a
confirmation UI, which makes it the right moment to close it.

**Fix:** add `secure=True` to both `set_cookie` calls, and add a double-submit CSRF token: issue
a random token in a readable cookie at login, emit it as a hidden field from the `modal()` macro
and every other state-changing form, and verify it in a shared dependency on all POST page
routes.

### WR-10: Toggle controls have no submit path without Alpine

**File:** `app/templates/groups/includes/group_row.html:66-69`,
`app/templates/schedules/includes/schedule_row.html:67-70`

**Issue:**

```jinja
<form method="post" action="/groups/{{ group.id }}/toggle" x-data x-on:change="$el.submit()">
  {{- toggle(name='is_active', checked=group.is_active, ...) -}}
</form>
```

The form contains only a checkbox — no submit button. With Alpine unavailable, flipping the
toggle changes nothing and there is no way to submit the form, so pausing/resuming a group or a
schedule becomes impossible. This is precisely the failure mode the phase eliminated for delete
(`WR-04`/`T-12-04` in the code comments), and the same reasoning applies here; the toggles were
simply not revisited.

**Fix:** include a submit control that is visually hidden but reachable without JS, and let
Alpine keep the change-to-submit shortcut:

```jinja
<form method="post" action="/groups/{{ group.id }}/toggle" x-data x-on:change="$el.submit()">
  {{- toggle(...) -}}
  <button class="btn btn--ghost" type="submit" x-cloak>{# visible only без Alpine #}
    <span class="btn__label">Применить</span>
  </button>
</form>
```

(`[x-cloak]` is already `display:none !important`, and Alpine strips the attribute on init — so
the fallback button shows only when Alpine never runs, which is exactly the intent.)

---

## Info

### IN-01: Divergent "is this an absolute URL" tests

**File:** `app/templates/ads/form.html:62` vs `app/pages/common.py:31`

`path.startsWith('http')` (client) accepts `httpfoo://…`; `key.startswith("http://") or
key.startswith("https://")` (server) does not. The same stored value can therefore be treated as
absolute in the editor and relative in the list. Align on the stricter server test.

### IN-02: HTML escaper used for a JavaScript string literal

**File:** `app/templates/ads/form.html:53`

`const IMAGE_BASE_URL = '{{ s3_public_url() }}';` relies on Jinja's *HTML* autoescaping inside a
`<script>` element, where entities are not decoded. The value is operator-controlled config, so
there is no injection today, and `</script>` is neutralised because `<` becomes `&lt;`. But a
quote in the setting would render as a literal `&#39;` and corrupt the URL, and this is the same
escaper/context mismatch class as CR-01. Prefer `{{ s3_public_url() | tojson }}` (no surrounding
quotes), which is correct in JS context.

### IN-03: `modal()` interpolates its `id` into an attribute *name*

**File:** `app/templates/components/modal.html:60`

`x-on:modal-open-{{ id }}.window="show()"` places `id` inside an attribute name, where Jinja's
escaping does not apply — a space or quote in `id` would produce attribute injection. All seven
call sites pass `'<prefix>-' ~ <int>`, so it is safe today. Add a guard in the macro
(`{% if id is not match('^[a-z0-9-]+$') %}{{ raise(...) }}{% endif %}`, or normalise via a filter)
so a future caller with a slug from user data cannot silently break the pattern.

### IN-04: Dead default argument in the sync swap card

**File:** `app/templates/accounts/partials/sync_status_card.html:52`

`stats.get('groups_count', group_count or 0)` — `_get_account_stats`
(`app/pages/accounts.py:99-106`) always populates `groups_count`, so the `group_count or 0`
fallback is unreachable whenever `stats` is non-empty, and `stats` is empty only for
non-`active` statuses where this branch does not run. Drop the parameter or the default.

### IN-05: Convoluted timezone resolution

**File:** `app/pages/common.py:90-99`

```python
tz_name = "UTC"
if user and getattr(user, "timezone", None):
    try:
        tz_name = user.timezone      # cannot raise
        return ZoneInfo(tz_name)
    except Exception:
        tz_name = "UTC"
return ZoneInfo(tz_name)
```

The assignment inside `try` cannot fail, and `tz_name` is reassigned only to be re-read on the
fall-through. Simplify to a single `try: return ZoneInfo(user.timezone) except Exception: return
ZoneInfo("UTC")`. Also, `app/pages/schedules.py:28,53,90` validates timezones against
`VALID_TIMEZONES` instead — two different fallback strategies for the same concept.

### IN-06: JWT decoded and the user row fetched twice per page request

**File:** `app/pages/__init__.py:36-37` and every handler in `app/pages/*.py`

`load_shell_context` runs `get_user_from_cookie` as a router-level dependency, and then each
handler calls `get_user_from_cookie` again. Every page request therefore decodes the JWT twice
and issues two `SELECT … FROM users` round-trips. The shell context (six scalar subqueries plus
two more selects) is also computed for HTMX partial endpoints — `/ads/partial`,
`/groups/partial`, `/history/partial`, `/accounts/{id}/sync-status` — whose templates never read
it, so the 5-second sync poll pays for it on every tick. Have `load_shell_context` stash the user
on `request.state` and have handlers read it, and skip shell computation for `*/partial` and
`sync-status` routes.

### IN-07: Possibly-unbound locals in the group sync handler

**File:** `app/pages/accounts.py:761-778`

`fetched_groups` and `messenger_type` are assigned only inside `if/elif/elif` branches. The guard
at line 755 (`account.type not in ("tg_user", "wa", "max")`) makes this correct today, but the
correctness lives 15 lines away from the use and static analysers will flag it. Add a final
`else: return RedirectResponse(url="/groups", status_code=302)` so the invariant is local.

### IN-08: `_qr_sessions` is process-local module state

**File:** `app/messengers/telegram_user.py:57,68` (used from `app/pages/accounts.py:235-340`)

The Telegram QR flow stores in-flight sessions in a module-level dict. With more than one uvicorn
worker (or more than one container behind nginx), `start-qr` and the subsequent `qr-status` /
`complete` calls can land on different processes, and the flow fails intermittently with
"Сессия не найдена". Move the session map into Redis, or pin the flow with a sticky cookie.

### IN-09: Two pages still leave columns unlabelled on narrow screens

**File:** `app/templates/billing/balance.html:97-99,112`, `app/templates/admin/groups_info.html:65-67,76-77`

Both bypass the `cell(label=…)` contract and hand-write `<span data-cell-label>` for some
columns only, so "Тип"/"Описание" (billing) and "Канал"/"Обновлено" (groups-info) lose their
names at ≤860px where `[data-rowhead] { display: none }` applies. `groups_info.html:76` uses
`title='Обновлено'` (a tooltip) where `label=INFO_COLUMNS[4]` was intended.

**This is already tracked** — `tests/test_responsive_markup.py:2793-2814` declares both as
explicit `unlabelled` sets with a note routing them to `/gsd-verify-work` (T-13-09), and the
comment is careful to call them observations rather than an accepted baseline. Recording here
only so the item is not lost; no new action beyond honouring that hand-off.

---

_Reviewed: 2026-08-09T20:56:10Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

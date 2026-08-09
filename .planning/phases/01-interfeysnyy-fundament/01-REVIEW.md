---
phase: 01-interfeysnyy-fundament
reviewed: 2026-08-09T00:00:00Z
depth: standard
files_reviewed: 76
files_reviewed_list:
  - app/main.py
  - app/pages/__init__.py
  - app/pages/accounts.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/groups.py
  - app/pages/history.py
  - app/pages/schedules.py
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
  - tests/test_routes/test_wa_sync_status.py
  - tests/test_templates/__init__.py
  - tests/test_templates/test_components.py
findings:
  critical: 1
  warning: 9
  info: 8
  total: 18
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-08-09
**Depth:** standard
**Files Reviewed:** 76
**Status:** issues_found

## Summary

Reviewed the full UI-framework replacement: shell (`base.html`, `auth_base.html`), the Jinja macro component library, every migrated page template, the four touched page routers, the new `load_shell_context` router dependency, `app.css`, and the new test suites.

Things that were verified to actually hold (not merely asserted by the implementation's own comments):

- **Autoescape is on** (`templates.env.autoescape is True`) and the extracted `connect_status.html` QR macro genuinely escapes bridge-supplied input — I rendered `qr('" onerror=alert(1) x="', 'WA')` and got `src="&#34; onerror=alert(1) x=&#34;"`. The f-string escaping bug the phase claims to have fixed is fixed.
- **No CDN references** anywhere in `app/templates/` or `app/static/css/app.css`; fonts, htmx and Alpine are all local.
- **Macro contracts match call sites.** I built a signature registry from all 54 loadable macros and cross-checked every call site in `app/templates/**/*.html` for unknown keyword arguments. Zero real mismatches (the 6 reported hits are false positives from URL literals like `'&q=' ~ q` inside `link_button(...)`).
- **Authorization holds.** Every admin route uses `Depends(require_admin)`; `get_sync_status_view`, `delete_account`, and all list/detail queries are scoped by `user_id`; `history_detail` and `admin_user_history_detail` both verify `log.user_id`. No IDOR found.
- The 119 new tests pass.

The findings below are what survived that. The one Critical is a stored-XSS sink that was carried forward verbatim into a rewritten file — it is not newly written code, but it is live code in a file this phase submitted, in the *one* template with zero HTTP-level test coverage.

Two items named in the phase context as already-tracked (the `get_settings()` bypass in `app/pages/common.py` template globals, and `billing/plans.html` having no route) are **not** re-reported here.

## Critical Issues

### CR-01: Stored XSS — unescaped image path interpolated into `innerHTML`

**File:** `app/templates/ads/form.html:55-62`

**Issue:** `renderImages()` builds DOM with template literals and `innerHTML`, interpolating `path` and `url` with no escaping:

```js
const url = path.startsWith('http') ? path : IMAGE_BASE_URL + '/' + path;
preview.innerHTML += `<span class="cell">
    <img class="avatar" src="${url}" alt="">
    ...`;
inputs.innerHTML += `<input type="hidden" name="images" value="${path}">`;
```

`path` is an S3 object key produced by `app/routes/uploads.py:34-35`:

```python
filename = f"{uuid4().hex}_{file.filename}"
key = f"{user_id}/{filename}"
return {"path": key}
```

`file.filename` is the attacker-supplied multipart filename and is **not sanitized at all**. Uploading a file named `x" onerror="fetch('/admin/users')` yields `src="https://cdn/1/<hex>_x" onerror="fetch('/admin/users')" alt="">` — the `src` is broken, so `onerror` fires. The key is persisted in `Ad.images` (JSON), so the payload re-executes on every subsequent visit to `/ads/{id}/edit`. This is stored, not reflected.

Escaping does *not* save this: `{{ (ad.images | tojson) }}` on line 48 is safe (Jinja's `tojson` is HTML-safe), but the values then flow into `innerHTML` client-side, well past any server-side escaping. The rest of the codebase renders these keys through `{{ get_image_url(...) }}`, which *is* escaped — this file is the sole sink.

Note: the same unsanitized `file.filename` also allows `../` in the S3 key, letting a user write objects outside their own `{user_id}/` prefix. `app/routes/uploads.py` is outside this phase's file scope, but the fix belongs in both places.

Carried forward verbatim from the pre-phase template (`git show 44f0134:app/templates/ads/form.html`), i.e. not newly introduced — but it is live in a submitted file, and see WR-06: this template has no HTTP-level test at all.

**Fix:** Build the nodes instead of concatenating markup, and sanitize the key server-side.

```js
function renderImages() {
    const preview = document.getElementById('image-preview');
    const inputs = document.getElementById('image-inputs');
    preview.replaceChildren();
    inputs.replaceChildren();
    imagePaths.forEach((path, i) => {
        const url = path.startsWith('http') ? path : IMAGE_BASE_URL + '/' + path;

        const wrap = document.createElement('span');
        wrap.className = 'cell';
        const img = document.createElement('img');
        img.className = 'avatar';
        img.src = url;              // property assignment, never parsed as markup
        img.alt = '';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn--ghost';
        btn.addEventListener('click', () => removeImage(i));
        const lbl = document.createElement('span');
        lbl.className = 'btn__label';
        lbl.textContent = 'Убрать';
        btn.appendChild(lbl);
        wrap.append(img, btn);
        preview.appendChild(wrap);

        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'images';
        hidden.value = path;        // property assignment, no attribute injection
        inputs.appendChild(hidden);
    });
}
```

And in `app/routes/uploads.py`, stop trusting the client filename:

```python
from pathlib import PurePosixPath
import re

raw = PurePosixPath(file.filename or "").name          # strips any path components
safe = re.sub(r"[^A-Za-z0-9._-]", "_", raw)[:100] or "image"
key = f"{user_id}/{uuid4().hex}_{safe}"
```

## Warnings

### WR-01: `load_shell_context` runs 5 discarded DB queries on every pages-router request, including the 3s/5s pollers

**File:** `app/pages/__init__.py:20-40`

**Issue:** The dependency is attached to the *router*, so it executes for every route under `app.pages` — not just full pages. Each execution does `get_user_from_cookie` (1 `User` fetch) plus `get_shell_context` (a 5-subquery counts statement, a `Subscription` query, a `MessageBalance` query, and a `BalanceTransaction` sum) = 5 round-trips.

The templates that never read `request.state.shell` are exactly the high-frequency ones:

- `/accounts/connect/wa/status` and `/accounts/connect/max/status` — polled `every 3s` (`connect_wa.html:34,45`, `connect_max.html:47,58`); these render `connect_status.html` macros, which take no context at all.
- `/accounts/{id}/sync-status` — polled `every 5s` (`accounts/list.html:50`); renders `sync_status_card.html` via `env.get_template(...).render(...)`, which never touches `request`.
- All five `*_partial_cards.html` infinite-scroll partials.
- Every POST handler (`/ads/{id}/delete`, `/groups/bulk`, `/logout`, …), which do a full shell read before their write and then redirect.

One user with a connect wizard open costs 100 wasted queries/minute. Handlers additionally call `get_user_from_cookie` a second time, so the cookie is decoded and the user re-fetched twice per request.

**Fix:** Move the dependency onto only the routers that render the shell, or make it lazy and cache the user on `request.state`:

```python
async def load_shell_context(request, db=Depends(get_db), settings=Depends(get_settings)) -> None:
    # Fragments and form posts never render the shell.
    if request.method != "GET" or request.headers.get("hx-request") == "true":
        request.state.shell = {}
        return
    user = await get_user_from_cookie(request, db, settings)
    request.state.user = user           # let handlers reuse it instead of re-reading
    request.state.shell = await get_shell_context(db, user)
```

(and have `base.html` keep its existing `request.state.shell or {}` guard).

### WR-02: Admin pager builds query strings without URL-encoding — parameter injection

**File:** `app/templates/admin/groups_info.html:88-95`

**Issue:** Unlike every other paginated section in this phase (which uses `{{ v|string|urlencode }}`), the groups-info pager concatenates raw values:

```jinja
{{ link_button('Далее', '/admin/groups-info?offset=' ~ (offset + page_size)
                        ~ ('&q=' ~ q if q else '') ~ ('&messenger=' ~ messenger if messenger else ''),
               variant='ghost', icon='arrow-right') }}
```

Rendered with `q = "a&messenger=wa&offset=999"` this produces:

```
/admin/groups-info?offset=30&amp;q=a&amp;messenger=wa&amp;offset=999
```

which the browser decodes into four parameters. A search term containing `&`, `#`, or `+` silently overrides `offset`/`messenger` or truncates the query. Not an XSS (autoescape still applies to the attribute), but pagination breaks and filters change under the user without any signal.

**Fix:**

```jinja
{% set page_qs = ('&q=' ~ q|urlencode if q else '') ~ ('&messenger=' ~ messenger|urlencode if messenger else '') %}
{{ link_button('Далее', '/admin/groups-info?offset=' ~ (offset + page_size) ~ page_qs,
               variant='ghost', icon='arrow-right') }}
```

Apply the same to the "Назад" link on line 88.

### WR-03: Polling swap drops the "Подключён" column — the row loses data it had before the swap

**File:** `app/templates/accounts/partials/sync_status_card.html:34-49`

**Issue:** The file's own header comment states the block "заменяет строку аккаунта ЦЕЛИКОМ… обязан быть строкой той же раскладки". The column *count* matches, but the sixth column's *content* does not. `accounts/list.html:103` renders the connection date there:

```jinja
{{- cell(text=format_datetime_for_user(account.created_at, user, '%d.%m.%Y %H:%M'), mono=true, muted=true) }}
```

while the `status == 'active'` branch of the swap card renders a placeholder (line 43):

```jinja
{{- cell(text='—', mono=true, muted=true) }}
```

I rendered the macro to confirm: the active row comes back with `…title="2 из 4">50%</span><span class="cell cell--mono cell--muted">—</span><span class="cell cell--mono cell--muted">—</span>…`. So when a sync completes and htmx swaps the row via `hx-swap="outerHTML"`, the account's connection date visibly disappears under the "Подключён" header and stays gone until a full page reload. No test covers this column.

**Fix:** Pass the account's `created_at` through the view and render it, so the swapped row is genuinely identical to the list row.

```python
# app/application/accounts/dto.py — add created_at to SyncStatusView
# app/application/accounts/use_cases.py::get_sync_status_view — populate it
# app/pages/accounts.py::accounts_sync_status
html = templates.env.get_template("accounts/partials/sync_status_card.html").render(
    account_id=account_id, status=view.status, group_count=view.group_count,
    messenger_type=view.messenger_type, created_at=view.created_at, user=user, stats=stats,
)
```

```jinja
{{- cell(text=format_datetime_for_user(created_at, user, '%d.%m.%Y %H:%M') if created_at else '—',
         mono=true, muted=true) }}
```

### WR-04: Destructive actions became entirely Alpine-dependent with no fallback

**File:** `app/templates/ads/includes/ad_card.html:42-56`, `app/templates/admin/user_detail.html:125-136`, `app/templates/components/modal.html:28`

**Issue:** The delete trigger is now `<button type="button" x-data x-on:click="$dispatch('modal-open-…')">`, and the actual `<form method="post" action="/ads/{id}/delete">` lives inside `.modal`, which carries `x-cloak`. `app.css:445` enforces `[x-cloak] { display: none !important; }`, and only Alpine removes that attribute. If `alpine.min.js` fails to load — blocked, corrupted cache, CSP change, JS error earlier in the page — the button does nothing *and* the form is permanently invisible. There is no other delete path on the page.

The previous markup degraded correctly (`git show 44f0134:app/templates/ads/includes/ad_card.html:34`):

```html
<form method="post" action="/ads/{{ ad.id }}/delete" onsubmit="return confirm('Удалить объявление?')">
  <button type="submit" …>
```

with JS unavailable the `onsubmit` is simply ignored and the form still submits. The same regression applies to the group/schedule toggles (`group_row.html:57`, `schedule_row.html:57`), which rely on `x-data x-on:change="$el.submit()"`.

**Fix:** Keep the modal as the enhancement, not the mechanism — render a real submit button inside a `<noscript>`-style fallback, or make the trigger itself the submit button of the real form and have Alpine `.prevent` it only once initialized:

```jinja
<form method="post" action="/ads/{{ ad.id }}/delete"
      x-data x-on:submit.prevent="$dispatch('modal-open-ad-del-{{ ad.id }}')">
  {{- button('Удалить', variant='ghost', icon='trash', title='Удалить объявление') -}}
</form>
```

Without Alpine the form posts directly; with Alpine the post is intercepted and the modal opens.

### WR-05: The "no utility classes" rendered-output tests use a 5-token marker list that misses the classes actually removed

**File:** `tests/test_pages/test_responsive_markup.py:34`

**Issue:**

```python
UTILITY_MARKERS = ("bg-white", "text-gray", "rounded-lg", "border-gray", "lg:")
```

This list drives 12 rendered-output assertions (`test_list_page_no_utility_classes`, `test_dashboard_no_utility_classes`, `test_billing_no_utility_classes`, `test_admin_no_utility_classes`, `test_admin_history_no_utility_classes`, …). The broad `TAILWIND_TOKENS` list (line 1251, 40+ tokens) is used *only* by `test_no_utility_classes_anywhere`, which reads template **source files** and only inside literal `class="…"` attributes.

Consequence: utility classes that arrive from anywhere other than a literal `class="…"` in a `.html` file — Python handler strings, `{{ }}`-built class values, third-party fragments — are checked only against the weak 5-token list. Concretely, the exact strings this phase removed from `app/pages/accounts.py` (`class="text-sm text-red-600"`, `class="text-sm text-amber-600"`) match **none** of the five markers. Had only those fragments been left behind, every rendered-output test would still be green.

**Fix:** Point the rendered-output assertions at the same broad list:

```python
UTILITY_MARKERS = TAILWIND_TOKENS   # single source of truth; move TAILWIND_TOKENS above line 34
```

and keep the source-level sweep as an additional check.

### WR-06: `ads/form.html` has zero HTTP-level coverage — including the XSS sink

**File:** `tests/test_pages/test_shell.py:105-111`, `tests/test_pages/test_responsive_markup.py:36-50`

**Issue:** The route list documents its own hole:

```python
# ИЗВЕСТНОЕ ОГРАНИЧЕНИЕ ОБХОДА. /ads/new в тестовой среде отдаёт 500 и в обход не включён.
```

`/ads/{id}/edit` renders the same template and 500s for the same reason, and is not in any test either. So `test_all_pages_render_new_shell`, which its own docstring calls "тест, доказывающий требование ЦЕЛИКОМ", proves it for 12 of 14 user-facing GET pages. The uncovered template is the largest JS block in the phase and the location of CR-01.

The underlying `get_settings()` bypass is already tracked in `deferred-items.md` and is not re-reported. The **coverage gap it leaves** is separate and is not tracked: nothing will notice if `ads/form.html` starts 500-ing in production, or if `handleFiles`/`renderImages` breaks.

**Fix:** Override the global for the test client so the page is reachable, then add `/ads/new` and `/ads/{id}/edit` to `SHELL_ROUTES`:

```python
# tests/conftest.py, in the client fixture
from app.pages.common import templates
templates.env.globals["s3_public_url"] = lambda: "http://s3.test"
templates.env.globals["get_image_url"] = lambda key: f"http://s3.test/{key}"
templates.env.globals["resolve_image_url"] = lambda key: key if str(key).startswith("http") else f"http://s3.test/{key}"
```

Add an escaping regression test alongside CR-01's fix:

```python
async def test_ads_form_escapes_image_path(authed_client, db_session):
    ad = await _seed_ad(db_session)
    ad.images = ['1/abc_x" onerror="alert(1)']
    await db_session.commit()
    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    assert 'onerror="alert(1)' not in html
```

### WR-07: `_get_group_stats` reads every schedule of every tenant

**File:** `app/pages/groups.py:51`

**Issue:**

```python
sched_r = await db.execute(select(Schedule.group_ids))
```

No `WHERE` clause at all. Every render of `/groups` and `/groups/partial` loads the `group_ids` JSON of all schedules in the database, then filters in Python. Two problems: the query grows with total tenants rather than with the requesting user's data, and correctness depends on group PKs never colliding across tenants — if any schedule row ever carries a stale or wrong `group_ids` entry, one tenant's schedule count silently leaks into another tenant's UI. Every sibling query in this file is scoped by `user_id`; this one is the exception.

Pre-existing (this phase changed only the `layout` parameter in this file), but it is the only unscoped tenant query in the reviewed set.

**Fix:** Scope through the owning `Ad`:

```python
sched_r = await db.execute(
    select(Schedule.group_ids)
    .join(Ad, Schedule.ad_id == Ad.id)
    .where(Ad.user_id == user_id)
)
```

### WR-08: Billing history renders raw ISO timestamps in UTC, bypassing the project's own date global

**File:** `app/templates/billing/balance.html:67,97`

**Issue:**

```jinja
{{- cell(text=tx.created_at[:16] if tx.created_at else '', mono=true, muted=true) }}
{{ mono('Последнее бесплатное начисление: ' ~ balance_info.free_balance_reset_at[:10]) }}
```

`get_transaction_history` returns `created_at` as `.isoformat()` (`app/services/billing_service.py:161`), so slicing to 16 characters displays `2026-08-09T10:03` — with a literal `T` — in UTC. Every other list in this phase uses `format_datetime_for_user(..., user, ...)` and shows the user's own timezone (`ad_card.html:36`, `history_card.html:39`, `group_row.html:44`, `schedule_row.html:47`). A user in `Europe/Moscow` sees their sends at 13:03 in History and the matching charge at 10:03 in Billing.

Carried over verbatim from the pre-phase table, but this phase's stated goal was one consistent presentation layer and it left this section behind.

**Fix:** Return real datetimes from the service and use the existing global:

```python
# app/services/billing_service.py
"created_at": tx.created_at,   # drop .isoformat()
"free_balance_reset_at": bal.free_balance_reset_at,
```

```jinja
{{- cell(text=format_datetime_for_user(tx.created_at, user, '%d.%m.%Y %H:%M'), mono=true, muted=true) }}
{{ mono('Последнее бесплатное начисление: ' ~ format_datetime_for_user(balance_info.free_balance_reset_at, user, '%d.%m.%Y')) }}
```

Check `app/routes/billing.py` for JSON consumers of these keys before changing the service return type.

### WR-09: The shell hand-rolls the avatar the component library exists to provide

**File:** `app/templates/base.html:69`

**Issue:**

```jinja
<span class="avatar">{{ user.name[0]|upper if user.name else '?' }}</span>
```

`components/avatar.html` implements exactly this, with `|trim` handling (a name of `"  Иван"` renders a blank initial here but `И` through the macro) and a `--avatar-size` hook. `profile.html:22` and `admin/user_detail.html:50` both use the macro; the shell is the one place that duplicates it. Any future change to the avatar (fallback glyph, size token, title attribute) will be applied in the macro and silently miss the sidebar — which is the single most-rendered avatar in the app.

**Fix:**

```jinja
{% from "components/avatar.html" import avatar %}
...
{{ avatar(user.name) }}
```

## Info

### IN-01: Duplicate SVG gradient IDs when more than one MAX icon renders

**File:** `app/templates/includes/messenger_icon.html:30-36`
**Issue:** The MAX branch hardcodes `id="mx-a"` … `id="mx-d"` inside the macro body. A user with two MAX accounts renders duplicate element IDs on `/accounts` (invalid HTML); every `url(#mx-c)` resolves to the first definition. Harmless today because all instances are identical, but it breaks the moment the gradients become parameterised, and it trips HTML validators.
**Fix:** Suffix the IDs with a unique token — e.g. add a `uid` parameter (`messenger_icon(type, uid=account.id)`) and emit `id="mx-a-{{ uid }}"` / `url(#mx-a-{{ uid }})`.

### IN-02: `group_count` parameter of the sync-status card is dead

**File:** `app/templates/accounts/partials/sync_status_card.html:35`
**Issue:** `cell(text=stats.get('groups_count', group_count or 0), …)` — `stats` is only non-empty when `status == 'active'`, and `_get_account_stats` always populates `groups_count` (defaulting to `0`, `app/pages/accounts.py:101`). The fallback can never fire, and `group_count` is unused in the other two branches, so `app/pages/accounts.py:686` passes a value that is always discarded.
**Fix:** Either drop `group_count` from the render call and the macro, or make it the single source and stop passing `stats['groups_count']`.

### IN-03: Empty response on unknown status deletes the account row from the DOM

**File:** `app/pages/accounts.py:693`
**Issue:** `return HTMLResponse("")` combined with the row's `hx-swap="outerHTML"` removes the row entirely. Reachable only if a `syncing` account transitions to a status outside `active`/`sync_failed`/`syncing` (the Celery tasks in `app/worker/tasks.py:302-435` only produce the first two, so this is currently unreachable) — but there is no comment saying so, and the failure mode is a row silently vanishing.
**Fix:** Return the row unchanged, without polling attributes, instead of an empty body — or add a comment stating the branch is defensive and unreachable.

### IN-04: Raw `&` instead of `&amp;` in infinite-scroll sentinel URLs

**File:** `app/templates/ads/list.html:28`, `accounts/list.html:121`, `groups/list.html:72`, `history/list.html:49`, `schedules/list.html:28`, and the matching `*_partial_cards.html`
**Issue:** `hx-get="/ads/partial?offset={{ next_offset }}&limit=30"` — the literal `&` is template text, so Jinja does not escape it. Browsers tolerate `&limit=` because the named-reference lookup fails, but this is invalid HTML and will break if a future parameter name ever collides with an entity name (`&amp`, `&lt`, `&copy`…).
**Fix:** Write `&amp;limit=30` in all ten sentinels.

### IN-05: `data-quota-expires` emits a Python datetime repr

**File:** `app/templates/base.html:57`
**Issue:** `data-quota-expires="{{ quota.get('expires_at') }}"` stringifies a `datetime` via `str()`, producing `2026-09-08 10:03:00+00:00` — a space separator, not the ISO `T`, so `new Date(...)` parsing is implementation-defined and `Date.parse` is unreliable in Safari.
**Fix:** `data-quota-expires="{{ quota.get('expires_at').isoformat() }}"` (guarded by the existing `{% if %}`).

### IN-06: Dead CSS — `[data-editor]` media query and `.animate-fade-in`

**File:** `app/static/css/app.css:446-447, 463-466`
**Issue:** `[data-editor]` and `[data-editor-side]` appear in no template or handler, and neither attribute can be produced by any macro — the entire `@media (max-width: 900px)` block is unreachable. Likewise `.animate-fade-in` and its `@keyframes fade-in` have no consumer (the class is referenced only by the reduced-motion rule on line 634, which is itself then dead). Both were transplanted from the mock-up.
**Fix:** Delete lines 446-447 and 463-466, and drop `.animate-fade-in` from the reduced-motion selector list on line 634. (`.field__input--center`, `.progress--ok/--warn/--danger`, `.mono--accent/--warn` and `.msg--plain` are *not* dead — they are reachable through macro variant parameters.)

### IN-07: `_get_timezone_for_user` has a redundant assignment and a misleading control flow

**File:** `app/pages/common.py:90-99`
**Issue:**
```python
tz_name = "UTC"
if user and getattr(user, "timezone", None):
    try:
        tz_name = user.timezone
        return ZoneInfo(tz_name)
    except Exception:
        tz_name = "UTC"
return ZoneInfo(tz_name)
```
The `tz_name = user.timezone` assignment is pointless (the value is only used on the very next line), the `except` branch re-assigns a variable that already held `"UTC"`, and there are two `return ZoneInfo(...)` sites for one decision. Behaviour is correct; the shape invites a wrong edit.
**Fix:**
```python
def _get_timezone_for_user(user: User | None) -> ZoneInfo:
    name = getattr(user, "timezone", None) if user else None
    try:
        return ZoneInfo(name) if name else ZoneInfo("UTC")
    except Exception:
        return ZoneInfo("UTC")
```

### IN-08: `assert "data-row" in html` is also satisfied by `data-rowhead`

**File:** `tests/test_pages/test_responsive_markup.py:225, 759, 863, 942`
**Issue:** `data-rowhead` contains `data-row` as a substring, so `test_list_page_has_responsive_primitives` and friends pass whenever the column header renders — even if zero data rows do. The seeded fixtures happen to guarantee rows, so the tests are green for the right reason today, but the assertion does not express what the docstring claims ("списочная страница собрана на примитивах").
**Fix:** `assert "<div data-row " in html` or `assert re.search(r'data-row\b(?!head)', html)`.

---

_Reviewed: 2026-08-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

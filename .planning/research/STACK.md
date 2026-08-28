# Stack Research

**Domain:** Server-rendered Python SaaS (FastAPI + Jinja2) converting all write interactions to htmx, with mandatory no-JS degradation
**Milestone:** v2.1 «HTMX-first»
**Researched:** 2026-08-26
**Confidence:** HIGH (every version number below was read from the npm/PyPI registry APIs or from the library's own source of record; the htmx dist file was downloaded and its embedded version string verified byte-for-byte)

---

## Headline Recommendation

**Add exactly two things: the htmx 2.0.10 dist file (vendored, replacing the 1.9.10 file) and one Python package, `jinja2-fragments==1.12.0`. Add nothing else.**

Everything else this milestone needs — HX-Request detection, response headers, fragment tests — is already achievable with what the project has. The only genuinely *new* capability the project cannot hand-roll cheaply is "render one `{% block %}` out of a full template", which is exactly the mechanism the chosen «фрагмент + OOB» contract (Key Decision, 2026-08-26) rests on.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **htmx** | **2.0.10** (published 2026-04-21) | The write layer: `hx-post` on all 47 forms, `hx-swap-oob`, `hx-disabled-elt`, `hx-indicator`, `hx-push-url` | Current stable (`dist-tags.latest` on npm). Upgrading BEFORE the form rewrite is already decided (D, 2026-08-26) and research confirms it is cheap: **not one of the 1.x→2.x breaking changes touches an attribute this project uses.** See the migration checklist below. |
| **jinja2-fragments** | **1.12.0** (PyPI, 2026-04-08) | Render a single `{% block %}`, or several blocks concatenated, from an existing full template | `Jinja2Blocks` **subclasses** `starlette.templating.Jinja2Templates`. One line changes in `app/pages/common.py:33`; all 66 existing `TemplateResponse` calls keep behaving identically. Its `block_names=[...]` renders main-fragment + OOB-fragments in a single response from a single context — literally the milestone's response contract. Sole dependency is `jinja2>=3.1.0,<4.0.0`, which the project already pins at `>=3.1.6`: **zero new transitive dependencies.** |

Nothing else is added. No JS package, no build step, no npm, no test-harness dependency.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| *(none)* | — | — | The correct answer for this milestone is an empty table. Every candidate below was evaluated and rejected — see «Alternatives Considered» and «What NOT to Use». |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| existing `pytest` + `pytest-asyncio` + `httpx.AsyncClient` | The entire htmx test surface | No new dev dependency. `AsyncClient` defaults to `follow_redirects=False`, so «302 became a 200 fragment» is directly assertable. See §3. |
| existing `tests/test_planning/` machine-gate pattern | Enforce the migration is complete and stays complete | The project already ships source-reading gates (access-gate router list, grep-gate on removed billing names). The same shape gives an "every `<form>` in `app/templates/` carries both `action=` and `hx-post=`" gate. |

---

## 1. htmx 1.9.10 → 2.0.10 — Exactly What Breaks

**Verified against:** `bigskysoftware/htmx@master` `www/content/migration-guide-htmx-1.md`, `CHANGELOG.md`, `www/content/reference.md`, `www/content/docs.md`, `www/content/attributes/hx-swap-oob.md` — the repository's own source of record. Confidence: HIGH.

### 1a. The complete 1.x → 2.x breaking-change list, scored against THIS project

| # | Breaking change | Before | After | **Hits this project?** |
|---|-----------------|--------|-------|------------------------|
| 1 | `hx-on` special syntax removed | `hx-on="htmx:beforeRequest: alert('x')"` | `hx-on:htmx:before-request="alert('x')"` (kebab-case mandatory — attributes are case-insensitive) | **NO.** `hx-on` occurrences in `app/templates/`: 0. The 79 `hx-*` attributes are only `hx-get`/`hx-trigger`/`hx-swap`/`hx-swap-oob`/`hx-post`/`hx-sync`. |
| 2 | Legacy `hx-ws` / `hx-sse` attributes removed | `hx-ws="connect:/x"` | `hx-ext="ws"` + `ws-connect="/x"` | **NO.** 0 occurrences. Live updates here are `hx-trigger` polling, not SSE/WS. |
| 3 | All extensions removed from core dist, versioned separately | bundled in htmx | separate npm packages | **NO — but note it.** The project loads 0 extensions today (`hx-ext`: 0 occurrences). Relevant only if the milestone chooses to add one; see §1c. |
| 4 | `htmx.config.scrollBehavior` default `'smooth'` → `'instant'` | smooth scroll on `hx-swap` `show:` | instant jump | **NO.** `show:` modifier: 0 occurrences. (If any `scroll:`/`show:` is added during the rewrite, this is a *cosmetic* difference, revertable via meta config.) |
| 5 | `htmx.config.methodsThatUseUrlParams` `["get"]` → `["get","delete"]` — **DELETE now encodes params in the URL, not a form-encoded body** | `hx-delete` sends a body | `hx-delete` sends query params | **NO today, LATENT TOMORROW.** `hx-delete`: 0 occurrences today. But 13 delete/confirm forms exist. **Rule for the roadmap: convert delete forms to `hx-post` against the existing `action`, not `hx-delete`.** The forms already POST to `/…/delete` routes; keeping `hx-post` keeps the no-JS path and the htmx path byte-identical on the wire, and sidesteps this change entirely. |
| 6 | `htmx.config.selfRequestsOnly` `false` → `true` | cross-domain allowed | same-origin only | **NO.** All 22 `hx-get` targets are relative same-origin paths. The new default is strictly safer and matches the project's «0 external resources» rule. |
| 7 | Module files split (`htmx.esm.js` / `.amd.js` / `.cjs.js`); `/dist/htmx.js` still browser-loadable | one file | four files | **NO.** No bundler, no module loader. The project loads `/dist/htmx.min.js` via a plain `<script src>` — that file still exists in 2.0.10 (51 238 bytes). |
| 8 | IE support dropped | — | — | **NO.** |
| 9 | `htmx.makeFragment()` always returns `DocumentFragment` | `Element \| DocumentFragment` | `DocumentFragment` | **NO.** Public JS API not called from any template. |
| 10 | Internal `selectAndSwap()` replaced by public `swap()` | — | — | **NO.** Extension-author API; no extensions here. |

**Verdict: the htmx 2.x upgrade breaks nothing in this codebase.** The migration is *literally* replacing one file. That is a strong, verified result — the roadmapper should size the upgrade phase as small, and spend the saved budget on the four *new-behaviour* traps below, which are where the actual risk lives.

### 1b. The four things that DO bite — new-in-2.x defaults, not breaking changes

These are not in the migration guide. They are new 2.x config knobs whose **defaults are wrong for this specific project**, and every one of them lands squarely on a milestone target feature. Each must be set in the `<meta name="htmx-config">` tag in `base.html` **and** `auth_base.html` (both load htmx).

| Config | 2.x default | Why it is wrong here | Set to |
|--------|-------------|----------------------|--------|
| **`responseHandling`** | `[{code:"204",swap:false},{code:"[23]..",swap:true},{code:"[45]..",swap:false,error:true},{code:"...",swap:false}]` — **4xx responses are NOT swapped** | The milestone's headline auth requirement is «ошибка перерисовывает форму без потери введённого». If the server answers a bad login with 400/422, htmx discards the body and the user sees **nothing happen at all**. Also breaks the planned global `htmx:responseError` UX if error bodies are meant to render. | Either (a) add `{"code":"422","swap":true}` to the array and have validation failures answer **422**, or (b) answer validation failures with **200** and carry the failure in the fragment. **Recommend (a):** it keeps HTTP honest, keeps the no-JS path's status code meaningful, and is the exact example the official docs give. |
| **`historyRestoreAsHxRequest`** | `true` | The htmx docs state verbatim: *"This should always be disabled when using HX-Request header to optionally return partial responses."* This project does exactly that in **4 places** (`app/pages/ads.py:435`, `:611`). On a history-cache miss htmx would send `HX-Request: true` on a **full-page** navigation and receive an ads-editor *fragment* as the whole document. | **`false`.** Non-negotiable. |
| **`allowNestedOobSwaps`** | `true` | The «фрагмент + OOB» contract means a card partial gets reused both as an OOB target and inside a larger fragment. With the default, the inner `hx-swap-oob` still fires when the bigger fragment is the main response — **and removes the element from the DOM**. The docs flag this precisely for template-fragment architectures, which is what `jinja2-fragments` produces. | **`false`.** With it off, OOB is processed only for elements *adjacent to* the main response element — which is the contract as written («побочные области — через `hx-swap-oob`»). |
| **`reportValidityOfForms`** | `false` (knob added in 2.0.7) | 47 forms are being put behind htmx. htmx blocks submission of an invalid form, but by default does **not** show the browser's native validation bubble or move focus. The user clicks Save on a form with an empty `required` field and gets silence. The no-JS path shows the bubble; the htmx path does not — a degradation *inversion*. The docs say: *"This should always be enabled as this matches default browser form submit behaviour."* | **`true`.** |

Concrete artifact for the upgrade phase (goes in `base.html` and `auth_base.html`, **before** the htmx `<script>` tag):

```html
<meta name="htmx-config" content='{
  "historyRestoreAsHxRequest": false,
  "allowNestedOobSwaps": false,
  "reportValidityOfForms": true,
  "responseHandling": [
    {"code":"204", "swap": false},
    {"code":"[23]..", "swap": true},
    {"code":"422", "swap": true},
    {"code":"[45]..", "swap": false, "error": true},
    {"code":"...", "swap": false}
  ]
}'>
```

### 1c. Extensions — which are now separate packages

In 2.x every extension left the core dist and is versioned independently. **This project needs none of them.** Recorded so a phase planner does not reach for one by reflex:

| Extension | Separate package | Latest | Would this project want it? |
|-----------|------------------|--------|------------------------------|
| `response-targets` | `htmx-ext-response-targets` | 2.0.4 (2025-10-18) | **No.** It would let 4xx be routed declaratively per-attribute — but `responseHandling` in the meta config solves the same problem globally, with **zero extra vendored files** and zero extra `hx-ext` attributes on 47 forms. Choosing the config keeps the «0 external resources / no build step» posture cleanest. |
| `sse` | `htmx-ext-sse` | 2.2.4 | No — the one extension the migration guide says *must* be upgraded, and the project uses 0 SSE. |
| `ws` | `htmx-ext-ws` | 2.0.4 | No. |
| `loading-states` | `htmx-ext-loading-states` | 2.0.2 | **No.** Tempting for the milestone's `hx-indicator` quality property — but `hx-indicator` + `hx-disabled-elt` are **core** attributes and already cover the requirement. |
| `head-support` | `htmx-ext-head-support` | 2.0.5 | No — relevant to `hx-boost`, which is explicitly out of scope. |
| `json-enc` | `htmx-ext-json-enc` | 2.0.3 | **No — actively harmful.** Sending JSON bodies would break the no-JS form path, which is a hard milestone frame. |

Note: htmx.org still ships legacy 1.x copies under `/dist/ext/` purely for CDN URL back-compat. Do not vendor from there.

### 1d. The exact file to commit

| | Value |
|---|---|
| **Version** | `2.0.10` (npm `htmx.org` `dist-tags.latest`, published `2026-04-21T16:29:49Z`) |
| **File** | `dist/htmx.min.js` |
| **Size** | 51 238 bytes (current vendored 1.9.10 file is 47 755 bytes) |
| **Embedded marker** | `version:"2.0.10"` — greppable, and worth asserting in a test |
| **SHA-384** | `sha384-H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V` |
| **Download (primary)** | `https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js` — jsDelivr is the officially recommended CDN since 2.0.5 |
| **Download (mirror, byte-identical — verified with `cmp`)** | `https://unpkg.com/htmx.org@2.0.10/dist/htmx.min.js` |
| **Destination** | `app/static/js/htmx.min.js` (overwrite) |
| **Runtime CDN use** | **None.** Download once at upgrade time, commit the file, keep the `<script src="{{ url_for('static', …) }}">` tags in `base.html:25` / `auth_base.html:24` unchanged. |

```bash
# One-shot upgrade, executed once by the upgrade phase:
curl -fsSL -o app/static/js/htmx.min.js \
  https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js
# verify before committing:
grep -c 'version:"2.0.10"' app/static/js/htmx.min.js   # must be 1
openssl dgst -sha384 -binary app/static/js/htmx.min.js | openssl base64 -A
# expect: H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V
```

**⚠️ Cache-busting trap found in this codebase.** `app/pages/common.py:142` computes `asset_version` from **`app.css`'s mtime only**:

```python
return str(int((_static_dir / "css" / "app.css").stat().st_mtime))
```

Replacing `htmx.min.js` therefore does **not** change `?v=…` on the htmx `<script>` tag, and every returning user keeps a cached htmx 1.9.10 against a server that now speaks the 2.x contract. **The upgrade phase must widen `_compute_asset_version()` to include the JS files' mtimes** (or, weaker, touch `app.css`). Widening the function is the right fix — it is a 3-line change and it makes the class of bug impossible rather than remembering to touch a file.

**Do NOT go to htmx 4.** The npm `next` tag is `4.0.0-beta6` (2026-07-23). It is a pre-release. This milestone's own decision says «1.9.10 → 2.x»; 2.0.10 is that target.

---

## 2. Server-Side Helper Libraries — Verdict

**Add `jinja2-fragments==1.12.0`. Hand-roll everything else.**

### The candidates, with real versions

| Package | Latest | Last release | Verdict |
|---------|--------|--------------|---------|
| **`jinja2-fragments`** | **1.12.0** | 2026-04-08 | ✅ **ADD** |
| `asgi-htmx` | 0.1.0 | **2022-05-30** | ❌ Reject — unmaintained for ~4 years, 0.1.0, and it only wraps `HX-Request` detection into a `request.htmx` object. That is the one thing this project already does correctly by hand. |
| `fastapi-htmx` | 0.5.0 | 2024-12-24 | ❌ Reject — introduces a `@htmx(...)` decorator that owns the template-selection convention. Rewiring 35 POST handlers around a third-party decorator to save `request.headers.get("HX-Request")` is a bad trade, and it constrains the *response* shape the milestone has already specified. |
| `fasthx` | 3.2.2 | 2026-07-23 | ❌ Reject — actively maintained and genuinely good, but it is a *decorator + typed-result* framework built for handlers that return data and get rendered by the decorator. This codebase's handlers return `TemplateResponse` directly, 66 times. Adopting it is a refactor of the page layer, not an addition to it — a scope the milestone did not open. Requires Python ≥3.11 (fine) but pulls its own opinions about the whole route signature. |
| `htmy` | 0.13.1 | 2026-07-22 | ❌ **Strongly reject** — it is a *replacement rendering engine* (components in Python instead of templates). Adopting it means abandoning 79 Jinja2 templates. Squarely against the standing constraint «интерфейс остаётся серверным на Jinja2». |
| `starlette-htmx` | 0.1.1 | **2022-01-22** | ❌ Reject — abandoned. |
| `htmx` (PyPI name) | 0.0.0 | 2023-07-15 | ❌ Reject — a `0.0.0` placeholder whose summary mentions Tailwind. Not a library. Named here only so nobody installs it by name-matching. |

### Why `jinja2-fragments` and not hand-rolling

The project's own «фрагмент + OOB» decision (Key Decision, 2026-08-26) creates a specific problem: **the same markup must be renderable both as part of a full page and standalone as a response fragment.** There are exactly three ways to do that, and only one of them is cheap here.

1. **Split every fragment into its own `.html` file and `{% include %}` it from the page.** This is what the project does today (`ads/partial_cards.html`, `history/partial_cards.html`, `dashboard/partial_feed.html`, `account_groups/partials/`, …). It works, and for 5 read-only partials it was fine. Scaled to 47 write paths each needing a main fragment *plus* one-to-several OOB side regions, it means **inventing and maintaining ~60–100 new tiny template files**, each with a hand-managed context contract, and it fragments each page's markup across a directory. Cost grows with the milestone.
2. **Hand-roll block extraction** (`env.get_template(n).blocks[b]`, build a context, `env.concat(...)`). This is ~40 lines including the async/exception handling. It is not *hard* — but it is precisely the 40 lines that `jinja2-fragments` is, tested across Jinja versions, with a named `BlockNotFoundError` and multi-block support. Writing it is choosing to own a maintained upstream's bug surface for no gain.
3. **`jinja2-fragments`.** Blocks stay *inside* the page template they belong to. The page renders whole for the no-JS path; the same file renders one named block for the htmx path. **The no-JS path and the htmx path are provably the same markup because they are the same lines of the same file** — which is exactly the property the milestone's degradation frame needs and which option 1 cannot guarantee (an `include` can drift from its caller's assumptions silently).

Verified integration facts (read from `jinja2_fragments/starlette.py` and `__init__.py` at `main`):

- `jinja2_fragments.fastapi` re-exports `jinja2_fragments.starlette`; `Jinja2Blocks` **subclasses `starlette.templating.Jinja2Templates`**.
- When neither `block_name` nor `block_names` is passed, it delegates to the stock `_TemplateResponse`. **All 66 existing call sites are untouched and behave bit-identically.**
- `block_names=["card", "counter_oob", "toast_oob"]` renders each block against a **shared context**, in order, concatenated — one response carrying the target fragment and all OOB regions. This is the milestone's response contract with no glue code.
- Requires Starlette ≥0.29 / FastAPI ≥0.108. The project has `fastapi>=0.129.0`. ✅
- Only runtime dep is `jinja2>=3.1.0,<4.0.0`; project has `jinja2>=3.1.6`. **The dependency graph does not grow.** ✅

**The entire integration is one line** in `app/pages/common.py:33`:

```python
# from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks

templates = Jinja2Blocks(directory=str(_templates_dir))
```

`templates.env.globals[...]` at `common.py:154` and every context processor keep working — `env` is inherited unchanged.

Two caveats worth putting in the phase plan:

- Responses produced with `block_name`/`block_names` are plain `HTMLResponse`, **not** `_TemplateResponse`. `status_code` and `headers` still work (so `HX-Push-Url`, `HX-Trigger`, `HX-Retarget` are all settable), but anything that introspects `response.template` / `response.context` — including some test helpers — will not find it. Assert on `response.text`, which is what this suite already does.
- **Keep the Jinja `Environment` synchronous.** If `enable_async=True` is ever set, `render_block` falls back to `loop.run_until_complete(...)`, which raises inside FastAPI's running event loop. The project's env is sync today; this is a "don't regress" note, not a change.

### Hand-roll: HX-Request detection

Keep it hand-rolled. `request.headers.get("HX-Request") is not None` is already the idiom in 4 places and it is correct. The only improvement worth making is **centralising it** so the milestone's ~35 handlers don't each re-spell it — a 3-line helper in `app/pages/common.py`, not a dependency:

```python
def is_htmx(request: Request) -> bool:
    """htmx sends HX-Request on every ajax request it issues."""
    return request.headers.get("HX-Request") is not None
```

(Pairs with `historyRestoreAsHxRequest: false` from §1b — without that config, this helper lies on history-cache misses.)

---

## 3. Testing the htmx Layer Without a Browser

**Verdict: the milestone's acceptance can be proven server-side. Do NOT add Playwright.** Confidence: MEDIUM-HIGH — the mechanism is verified, the "is it *enough*" call is judgement.

The reasoning is structural, not preferential: **htmx moves behaviour into the HTTP contract, and an HTTP contract is exactly what `httpx.AsyncClient` tests.** Everything the milestone promises is a statement about a request or a response:

| Milestone promise | Server-side assertion |
|---|---|
| «ни одно действие не перезагружает страницу» | POST with `HX-Request: true` returns **200**, not 302 |
| «фрагмент + OOB» | body contains the target fragment and **not** `<!DOCTYPE`/`<body`; contains `hx-swap-oob=` for each side region |
| «успех уходит `HX-Location`» (auth) | `response.headers["HX-Location"]` == expected path |
| «ошибка перерисовывает форму без потери введённого» | POST bad creds + `HX-Request` → 422, body contains the submitted email value |
| «деградация без JS сохраняется» | the same GET renders `method="post"` and `action="/…"` on every form |
| «канал уведомлений вместо `?saved=1`» | body carries the OOB notification region; `Location` header no longer carries `?saved=1` |

### Concrete pytest patterns for this suite

These build on the fixtures that already exist (`authed_client`, `db_session`) and the assertion style the suite already uses (substring checks on `response.text`, e.g. `test_editor_delete_form_degrades_without_alpine`).

**Pattern A — a shared `hx` header constant + fixture** (add to `tests/conftest.py`):

```python
HX = {"HX-Request": "true"}

@pytest_asyncio.fixture
def hx_client(authed_client):
    """authed_client that stamps HX-Request on every request, like htmx does."""
    authed_client.headers.update(HX)
    return authed_client
```

**Pattern B — «the same route answers two ways» (the load-bearing test of this milestone)**

```python
@pytest.mark.asyncio
async def test_schedule_toggle_answers_fragment_to_htmx_and_redirect_without_js(
    authed_client, db_session
):
    sch = await _seed_schedule(db_session)

    plain = await authed_client.post(f"/schedules/{sch.id}/toggle")
    assert plain.status_code == 302                    # no-JS path survives
    assert plain.headers["location"].startswith("/schedules")

    hx = await authed_client.post(f"/schedules/{sch.id}/toggle", headers=HX)
    assert hx.status_code == 200                       # no full reload
    assert "<!DOCTYPE" not in hx.text                  # a fragment, not a page
    assert f'id="schedule-{sch.id}"' in hx.text        # the target card
```

Note `follow_redirects` is `False` by default on `AsyncClient`, so the 302 is observed directly — no fixture change needed.

**Pattern C — response headers**

```python
resp = await authed_client.post("/login", data={...}, headers=HX)
assert resp.status_code == 200
assert resp.headers["HX-Location"] == "/dashboard"
assert "set-cookie" in resp.headers          # identity really changed
```

Same shape for `HX-Trigger`, `HX-Retarget`, `HX-Reswap`, `HX-Push-Url`. The existing `HX-Push-Url` behaviour in `app/pages/ads.py:522` is already testable this way and should get a named regression if it doesn't have one.

**Pattern D — degradation gate, parameterised over every form.** The project has an established habit of *machine gates that read the source* (the access-gate router list, the billing grep-gate). The degradation frame deserves the same treatment rather than 47 hand-written tests:

```python
@pytest.mark.parametrize("path", ALL_FORM_PAGES)
async def test_every_form_keeps_a_real_post_action(authed_client, path):
    """htmx перехватывает, а не заменяет: hx-post никогда не отменяет action."""
    html = (await authed_client.get(path)).text
    for form in _forms(html):                       # stdlib html.parser is enough
        assert 'method="post"' in form, f"{path}: форма без method"
        assert "action=" in form, f"{path}: форма без action"
        if "hx-post=" in form:
            assert _attr(form, "hx-post") == _attr(form, "action"), \
                f"{path}: hx-post и action разошлись"
```

That last equality is the strongest single assertion available to this milestone: it proves the htmx path and the no-JS path hit **the same endpoint**, which is what makes «htmx только перехватывает» a fact rather than an intention. The suite has no HTML parser dependency today — use `html.parser` from the stdlib, not BeautifulSoup.

**Pattern E — the upgrade itself.** Extend the existing `tests/test_pages/test_shell.py` (which already asserts `/static/js/htmx.min.js` is served) with a version assertion, so a silent revert to a stale vendored file is loud:

```python
def test_vendored_htmx_is_the_pinned_major():
    js = (STATIC / "js" / "htmx.min.js").read_text(errors="ignore")
    assert 'version:"2.0.10"' in js
```

And a config gate — the four settings in §1b are load-bearing, and a template edit could drop them:

```python
async def test_htmx_config_meta_disables_history_restore_as_hx_request(authed_client):
    """historyRestoreAsHxRequest=true + HX-Request-ветвление = фрагмент вместо страницы."""
    for page in ("/dashboard", "/login"):
        html = (await authed_client.get(page)).text
        cfg = _htmx_config(html)
        assert cfg["historyRestoreAsHxRequest"] is False
        assert cfg["allowNestedOobSwaps"] is False
        assert cfg["reportValidityOfForms"] is True
```

### What server-side tests genuinely cannot prove

Named honestly, so the roadmapper does not over-claim in acceptance criteria:

- that htmx **actually performed the swap**, and into the right element;
- the DOM state *after* a swap (did the OOB counter land where intended);
- `hx-indicator` / `hx-disabled-elt` visual behaviour and double-submit prevention;
- that the global `htmx:responseError` handler fires;
- `hx-push-url` actually changing the address bar;
- the interaction between htmx swaps and the 14 Alpine `x-data` templates (**this is the sharpest residual risk** — a swap replaces DOM that Alpine had initialised, and whether Alpine re-initialises is not observable from the server).

### Should Playwright be added anyway?

**No — not in this milestone.** Three reasons, in order of weight:

1. **It is not the cheapest way to close the residual risk.** The uncovered items above are ~6 behaviours, most of which are htmx's own well-tested behaviour rather than this project's logic. Buying a browser harness to re-test htmx is paying for the wrong thing.
2. **The cost is not the dependency, it is the second suite.** ~1700 tests run against in-memory SQLite via `ASGITransport` — no server process, no ports. Playwright needs a live uvicorn, a real Postgres or a served SQLite, browser binaries in CI and in the Docker build, plus flake management. That is a *new operational surface* on a milestone whose entire premise is "no build step, no new infrastructure".
3. **The project has already accepted this gap by precedent.** `.planning/PROJECT.md` records «браузерного стенда в суите нет» as a *named, accepted* limitation for the admin-panel responsive check, closed by manual UAT. The consistent move is to close the swap-level items the same way — an explicit manual UAT checklist item per phase — not to introduce a harness for the first time inside a milestone that has 47 forms to convert.

**Recommendation:** prove the contract server-side with patterns A–E; carry a short, *named* manual UAT list (one swap, one OOB, one indicator, one Alpine-containing card, one error path) per phase. If a browser harness is ever justified, it is its own milestone with its own decision — not a line item smuggled into this one.

---

## 4. What NOT to Add

| Avoid | Why — specifically | Use instead |
|-------|--------------------|-------------|
| **npm / package.json / any bundler (Vite, esbuild, Rollup)** | Violates decision D-02 («build-шага не вводится») head-on. htmx ships a ready 51 KB browser file; there is nothing to build. Adding npm also re-opens the "0 external resources" property, which is currently machine-verified per `<script>`/`<link>` host. | `curl` the dist file once, commit it, keep the two `<script src>` tags. |
| **Playwright / Selenium / any browser harness** | See §3. New CI surface, new Docker layers, a second test suite, flake — to cover ~6 behaviours that are htmx's own. Contradicts the milestone's "no new infrastructure" posture. | `httpx.AsyncClient` patterns A–E + a named manual UAT list per phase. |
| **A toast JS library (Toastify, Notyf, SweetAlert, …) or a hand-written toast component** | **Already decided against** (Key Decision, 2026-08-26): «Обратная связь — OOB-область… а НЕ тосты через `HX-Trigger`». Toasts need JS and therefore do not degrade — they would create a channel where the no-JS user is told nothing. | The OOB notification region in `base.html` over the existing `alert.html`, swapped by the same mechanism as every other response. |
| **`htmx-ext-response-targets`** | Solves a real problem (declarative 4xx routing) that `htmx.config.responseHandling` already solves globally, with one extra vendored file and an `hx-ext` attribute to place on 47 forms. | The `responseHandling` meta config from §1b. |
| **`htmx-ext-loading-states`** | The milestone's indicator requirement is satisfied by `hx-indicator` + `hx-disabled-elt`, both **core** attributes in 2.x (and improved in 2.0.5 with the `inherit` keyword, and in 2.0.9 for already-disabled elements). | `hx-indicator` / `hx-disabled-elt`. |
| **`htmx-ext-json-enc`** | Would send JSON request bodies — the *same form* then cannot be submitted natively by a browser without JS. Directly destroys the milestone's hardest frame. | Plain form encoding. `hx-post` on a real `<form>` posts exactly what the browser would. |
| **`hx-boost`** | Explicitly out of scope by decision. Enabling it also drags in `head-support`, `scrollIntoViewOnBoost` and history-restore concerns — i.e. it would make `historyRestoreAsHxRequest` an even sharper trap. | Leave link navigation as full document loads. |
| **`hx-delete` / `hx-put` on the 13 delete & confirm forms** | 2.x moved `delete` into `methodsThatUseUrlParams`, so `hx-delete` sends parameters in the **URL**, not the body — a silent divergence from the no-JS `<form method="post">` path, which cannot emit DELETE at all. | `hx-post` pointing at the form's existing `action`, so both paths are byte-identical on the wire. |
| **`htmx.org@4.0.0-beta*`** | Pre-release (`next` tag, beta6, 2026-07-23). The milestone decision says 2.x. | `2.0.10`. |
| **`htmy`, `fasthx`, `fastapi-htmx`, `asgi-htmx`, `starlette-htmx`** | See the table in §2 — respectively: replaces Jinja2 entirely; refactors all 35 handler signatures; owns the template-selection convention; abandoned since 2022; abandoned since 2022. | `jinja2-fragments` + a 3-line `is_htmx()` helper. |
| **An SPA framework (React/Vue/Svelte/HTMX+Alpine→Alpine-only rewrite)** | Standing `Out of Scope` entry since v2.0. Also: this milestone *removes* 6 hand-written `fetch()` calls — adding a framework would reintroduce the class. | Server-rendered Jinja2 fragments. |
| **Removing Alpine.js** | Explicitly out of scope («Alpine НЕ снимается»). 14 templates depend on it. | Leave `x-data` alone; test the swap/Alpine interaction manually. |
| **Tailwind (re-adding)** | Removed in v2.0 and its removal is what killed the build step. | The existing `app.css`. |
| **BeautifulSoup / lxml as a test dependency** | The suite currently parses zero HTML and asserts with substrings. Adding a parser for Pattern D is defensible but not required. | `html.parser` from the stdlib. |

---

## Installation

```bash
# 1. Python side — one package, zero new transitive deps
just add jinja2-fragments        # resolves to 1.12.0; requires only jinja2>=3.1.0,<4.0.0

# 2. JS side — no npm. Download once, commit the file.
curl -fsSL -o app/static/js/htmx.min.js \
  https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js

# 3. Verify before committing
grep -c 'version:"2.0.10"' app/static/js/htmx.min.js   # -> 1
test "$(stat -c%s app/static/js/htmx.min.js)" -eq 51238 && echo size-ok
openssl dgst -sha384 -binary app/static/js/htmx.min.js | openssl base64 -A
# -> H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V
```

No `npm install`. No dev dependencies added.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `jinja2-fragments` (blocks inside page templates) | More `{% include %}` partial files, as today | If the milestone ends up needing fewer than ~10 fragments total, or if a fragment must be shared across *unrelated* pages. The two coexist — `partial_cards.html` files do not have to be converted. |
| `jinja2-fragments` | Hand-rolled `env.get_template(n).blocks[b]` | If adding any dependency is politically blocked. ~40 lines; you then own multi-block, `BlockNotFoundError`, and the async-env footgun yourself. |
| `responseHandling` meta config | `htmx-ext-response-targets` 2.0.4 | If different forms need *different* error targets (e.g. 404 → one region, 422 → the form). Not the case here: one global rule serves all 47. |
| htmx 2.0.10 | Staying on htmx 1.9.10 | Never, for this milestone — the upgrade-first decision is already made, the break-list is empty for this codebase, and 1.x will not receive the `responseHandling`/`allowNestedOobSwaps` knobs the fragment+OOB contract needs. |
| `HX-Location` for auth success | `HX-Redirect` (hard redirect) | If a full document reload after login is acceptable/desired — it is simpler and guarantees a clean shell with the new identity. `HX-Location` is the milestone's stated choice and gives a smoother transition; `HX-Redirect` is the safer fallback if session-cookie + partial-swap interaction misbehaves. Worth naming as the escape hatch in the auth phase. |
| Server-side tests only | Playwright smoke suite | Only if manual UAT repeatedly finds swap-level or Alpine-reinit defects across ≥2 phases. Then it is its own milestone, not a line item. |

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `jinja2-fragments 1.12.0` | `jinja2 >=3.1.0,<4.0.0` | Project pins `jinja2>=3.1.6`. ✅ **Watch:** a future Jinja 4 would be excluded by jinja2-fragments' own cap. |
| `jinja2-fragments 1.12.0` | Starlette ≥0.29 / FastAPI ≥0.108 | Project has `fastapi>=0.129.0`. ✅ Uses the modern `TemplateResponse(request, name, …)` signature (supported since jinja2-fragments 1.9.0); the legacy signature emits a `DeprecationWarning`. |
| `jinja2-fragments 1.12.0` | Python ≥3.9 | Project is 3.12. ✅ |
| `htmx 2.0.10` | Alpine.js 3.x | No known conflict; both are attribute-driven and independent. **Unverified in this codebase:** whether Alpine re-initialises inside htmx-swapped DOM. `alpine-morph` exists as an extension for morph-based swaps — not needed unless morphing is adopted (it is not). Flag as the phase-level risk. |
| `htmx 2.0.10` | modern evergreen browsers | IE dropped in 2.0.0 — irrelevant for a 2026 SaaS. |
| `htmx 2.0.10` | this project's 79 existing `hx-*` attributes | **All 6 attribute kinds in use (`hx-get`, `hx-trigger`, `hx-swap`, `hx-swap-oob`, `hx-post`, `hx-sync`) are unchanged in 2.x.** `hx-sync` additionally got a Shadow-DOM fix in 2.0.8. |
| `htmx 2.0.10` | `HX-Request` / `HX-Push-Url` as used in `app/pages/ads.py` | Semantics unchanged — **but** `historyRestoreAsHxRequest` must be set `false` (see §1b), otherwise the 4 existing `HX-Request` branches misfire on history-cache misses. |

---

## Sources

- `https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/content/migration-guide-htmx-1.md` — full 1.x→2.x breaking-change list, verbatim. **HIGH** (project's own source of record)
- `https://raw.githubusercontent.com/bigskysoftware/htmx/master/CHANGELOG.md` — 2.0.0 through 2.0.10 entries; `reportValidityOfForms` origin (2.0.7), `HX-Trigger` on other elements (2.0.2), `hx-disabled-elt` fix (2.0.9), jsDelivr as recommended CDN (2.0.5). **HIGH**
- `https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/content/reference.md` — config-option defaults table (`selfRequestsOnly`, `methodsThatUseUrlParams`, `scrollBehavior`, `allowNestedOobSwaps`, `historyRestoreAsHxRequest`, `reportValidityOfForms`), request- and response-header reference. **HIGH**
- `https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/content/docs.md` — `responseHandling` array semantics and the 422 example. **HIGH**
- `https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/content/attributes/hx-swap-oob.md` — nested-OOB behaviour and the template-fragment warning; `<template>` wrapping for `<tr>`/`<li>`. **HIGH**
- `https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/content/headers/hx-location.md`, `.../hx-push-url.md` — «Response headers are not processed on 3xx response codes». **HIGH**
- `https://registry.npmjs.org/htmx.org` — `dist-tags.latest = 2.0.10`, publish dates, `next = 4.0.0-beta6`. **HIGH** (registry API)
- `https://registry.npmjs.org/htmx-ext-{sse,ws,response-targets,loading-states,head-support,json-enc}` — extension package versions. **HIGH**
- `https://data.jsdelivr.com/v1/packages/npm/htmx.org@2.0.10` — dist file listing; confirms `dist/htmx.min.js` (51 238 B) still ships. **HIGH**
- `https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js` and the unpkg mirror — downloaded, `cmp`-identical, embedded `version:"2.0.10"` confirmed, SHA-384 computed locally. **HIGH** (artifact verified, not quoted)
- `https://pypi.org/pypi/jinja2-fragments/json` — 1.12.0, 2026-04-08, `requires_dist`, `requires_python`. **HIGH** (registry API)
- `https://raw.githubusercontent.com/sponsfreixes/jinja2-fragments/main/src/jinja2_fragments/{starlette.py,__init__.py}` + `CHANGELOG.md` — `Jinja2Blocks` subclassing, `block_names` multi-block rendering, `HTMLResponse` return type, async-env `run_until_complete` caveat, Starlette support timeline. **HIGH** (source read directly)
- Context7 `/bigskysoftware/htmx` and `/sponsfreixes/jinja2-fragments` — corroborating snippets for the migration table and FastAPI integration. **MEDIUM**
- PyPI JSON API for `asgi-htmx`, `fastapi-htmx`, `htmy`, `fasthx`, `starlette-htmx`, `htmx` — versions and last-release dates used for the reject table. **HIGH**
- `https://github.com/bigskysoftware/htmx/discussions/680` (via web search) — community practice on testing htmx apps. **MEDIUM**
- This repository, read directly: `app/pages/common.py:33,142-154`, `app/pages/ads.py:435,522,611`, `app/templates/base.html:25`, `app/templates/auth_base.html:24`, `tests/conftest.py:56-93`, `tests/test_pages/test_shell.py:38`, attribute census over `app/templates/`. **HIGH**

---
*Stack research for: htmx-first write layer on FastAPI + Jinja2, no build step, no-JS degradation mandatory*
*Researched: 2026-08-26*

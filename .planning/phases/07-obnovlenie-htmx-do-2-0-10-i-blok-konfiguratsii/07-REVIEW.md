---
phase: 07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii
reviewed: 2026-08-27T11:49:25Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - app/pages/common.py
  - app/templates/auth_base.html
  - app/templates/base.html
  - app/templates/includes/htmx_config.html
  - tests/test_pages/test_asset_version.py
  - tests/test_pages/test_shell.py
  - tests/test_templates/test_htmx_inventory.py
  - app/static/js/htmx.min.js
findings:
  critical: 1
  warning: 7
  info: 3
  total: 11
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-08-27T11:49:25Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

The phase does three things: swaps the vendored htmx runtime 1.9.10 → 2.0.10, extracts the
`<meta name="htmx-config">` + runtime `<script>` pair into a single `{% include %}`, and
rewrites `_compute_asset_version()` from an mtime read to a content hash over the static tree.

**What holds up under adversarial checking:**

- The vendored artifact is exactly what the phase claims. Independently verified:
  51 238 bytes, `SHA-384 = H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V`,
  contains `version:"2.0.10"`. All three assertions in `test_vendored_htmx_is_the_declared_artifact`
  are true against the file on disk.
- All six config keys exist in the vendored runtime (`historyRestoreAsHxRequest`,
  `allowNestedOobSwaps`, `reportValidityOfForms`, `historyCacheSize`, `selfRequestsOnly`,
  `responseHandling` — each present in `htmx.min.js`), so none of them silently no-ops.
- The config block does render above the runtime tag in **both** shells — verified by running
  the suite (`test_auth_shell_carries_htmx_config`, `test_main_shell_carries_htmx_config` pass).
- `allowNestedOobSwaps: false` is safe here. Traced htmx 2.0.10's `$e()`: with the flag false an
  OOB element is only processed when `el.parentElement === null`, i.e. it must be a direct child
  of the response fragment. All five `hx-swap-oob` sites in the project
  (`ads/includes/autosave_response.html:19,20,34` and the root `<span>` of
  `ads/includes/autosave.html:27`) are top-level in their response. No silent breakage of the
  ad-editor autosave.
- The hash is deterministic and order-independent; independently confirmed the `hx-get` inventory
  count is genuinely 22 attribute occurrences across 22 distinct lines. No 1.x-only htmx
  attributes remain in templates (no `hx-on`, `hx-ws`, `hx-sse`, `hx-ext`, and — importantly for
  the `methodsThatUseUrlParams` change in 2.0 — no `hx-delete` at all).
- No `rglob` symlink-recursion hazard on Python 3.12 (`**` does not follow symlinks — verified).

**Key concerns:** one blocker, where the phase's residual-data mitigation targets a browser
storage that the runtime it just installed does not use, and the machine gate locks the error in.
The remaining warnings cluster around load-bearing comments that assert facts about the vendored
artifact which the artifact contradicts, plus one unguarded degradation path in
`_compute_asset_version()` that can abort module import.

---

## Critical Issues

### CR-01: History-cache purge targets `localStorage`, but htmx 2.0.10 uses `sessionStorage` — the mitigation is aimed at the wrong store and the gate enshrines it

**File:** `app/templates/auth_base.html:61` (rationale at `:25-59`);
`tests/test_pages/test_shell.py` (`HISTORY_CACHE_KEY` comment and
`test_main_shell_does_not_clear_history_cache`)

**Issue:**

The comment introduced by this phase in `tests/test_pages/test_shell.py` states:

> `# Ключ, под которым htmx складывает снимки страниц. Хранилище — localStorage,`
> `# а не sessionStorage: снимок переживает и закрытие вкладки, и выход из`
> `# системы. Имя снято по вендоренному артефакту (research/PITFALLS.md §9).`

That claim is false for the artifact the same phase vendored. Measured against both files:

| runtime | `localStorage` refs | `sessionStorage` refs |
|---|---|---|
| htmx 1.9.10 (removed by this phase) | 7 | 0 |
| htmx 2.0.10 (`app/static/js/htmx.min.js`, shipped) | **0** | **9** |

htmx 2.0.10's `zt()` (saveToHistoryCache) reads and writes
`sessionStorage.getItem("htmx-history-cache")` / `setItem(...)`, and on
`historyCacheSize <= 0` it calls `sessionStorage.removeItem("htmx-history-cache")`.
The string `localStorage` does not appear anywhere in the shipped runtime. The comment's
own justification — "снимок переживает и закрытие вкладки" — is precisely the property
`sessionStorage` does **not** have, so the research was done against the *outgoing* 1.9.10
runtime and never re-derived after the upgrade.

Two concrete consequences:

1. **The one-shell-only placement rests on a false premise.** `auth_base.html:39-47` argues the
   cleanup is redundant in `base.html` because "после нулевого размера кеша ключ больше не
   наполняется". True — but nothing in htmx 2.0.10 ever *empties* the `localStorage` key either
   (it has no `localStorage` code path at all). The legacy 1.9.10 snapshots — which is what this
   line exists to remove — are therefore cleared **only** when an auth-shell page renders. A user
   who stays signed in and never hits `/login` keeps snapshots of the admin panel, the payment
   forms and impersonated screens in `localStorage` indefinitely. That is exactly the residual
   data QUAL-05 names.
2. **The gate locks the defect in.** `test_main_shell_does_not_clear_history_cache` asserts
   `response.text.count("htmx-history-cache") == 0` on `/dashboard`, so the obvious fix (run the
   removal in both shells for a migration window) is *forbidden* by the suite. And the manual
   DevTools check the plan defers to (07-03 UAT) will be inspecting `localStorage` — where
   2.0.10 writes nothing — and will observe "clean" for a vacuous reason.

**Fix:**

Move the removal into the file that already owns the htmx pair, so both shells get it exactly
once and the single-owner invariant the phase argues for is preserved rather than violated:

```html
{# app/templates/includes/htmx_config.html — after the <meta>, before/after the runtime tag #}
{# МИГРАЦИОННАЯ ОЧИСТКА 1.9.10. Снимки, накопленные ПРЕЖНИМ рантаймом, лежат в
   localStorage: 2.0.10 хранит их в sessionStorage и localStorage не трогает вовсе
   (в артефакте ноль вхождений `localStorage`), поэтому сам он их не уберёт никогда.
   sessionStorage при historyCacheSize=0 рантайм чистит сам (zt(): removeItem + return).
   Строка снимается вместе с окончанием миграционного окна. #}
<script>
  try { localStorage.removeItem('htmx-history-cache'); } catch (error) { /* приватный режим */ }
</script>
```

Then:

- delete the block from `app/templates/auth_base.html:25-62`;
- correct the `HISTORY_CACHE_KEY` comment in `tests/test_pages/test_shell.py` to name
  `sessionStorage` as 2.0.10's store and `localStorage` as the 1.9.10 legacy store;
- replace `test_main_shell_does_not_clear_history_cache` with a *both-shells-exactly-once*
  assertion (`count(...) == 1` on `/login` and on `/dashboard`), which is the invariant the
  phase actually wants;
- correct the 07-03 UAT step to inspect `sessionStorage` for the "new snapshots" half and
  `localStorage` for the "legacy snapshots" half.

---

## Warnings

### WR-01: The `422 / swap: true` rule injects FastAPI's raw JSON validation body into the page

**File:** `app/templates/includes/htmx_config.html:50`

**Issue:** The rule `{"code":"422", "swap": true}` is justified (`:24-33`) by "Форма, вернувшая
422 с текстом ошибки валидации, станет … МЁРТВОЙ КНОПКОЙ". But the application has no route that
returns 422 with an HTML fragment: `grep -rn "422\|RequestValidationError\|exception_handler"
app/ --include=*.py` shows no `status_code=422` anywhere and no
`@app.exception_handler(RequestValidationError)` (`app/main.py:206-226` registers handlers for
`NotFoundError`, `ForbiddenError`, `BillingLimitError`, `MessengerConnectionError`, `Exception`
only). Every 422 this app can currently emit is FastAPI's default
`{"detail":[{"type":"int_parsing","loc":["query","page"],...}]}` JSON.

Under htmx 1.9.10 that response was caught by the default `[45]..` rule → no swap. Under the new
config it matches `422` first → **swapped into the target element**, dumping route/parameter
internals onto the screen, and — because the rule carries no `"error": true` — without firing
`htmx:responseError`. The phase turned a silent no-op into a visible malformed swap.

**Fix:** either add the HTML-fragment 422 handler the rule presupposes, or drop the rule until
one exists. The handler form:

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError):
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request, "components/form_error.html", {"detail": "Проверьте заполнение формы"},
            status_code=422,
        )
    return JSONResponse({"detail": exc.errors()}, status_code=422)
```

Whichever is chosen, the decision needs a gate — otherwise the rule and the server's 422 body
diverge silently, which is the exact failure class this phase was built to close.

### WR-02: `_compute_asset_version()` can raise at module import, violating its own documented degradation contract

**File:** `app/pages/common.py:209` (called at `:225`)

**Issue:** The docstring states "Деградация одна и явная: и ошибка чтения, и ПУСТОЙ охват дают
`dev`", and only `OSError` is caught. `f"{rel}\0{len(body)}\0".encode("utf-8")` raises
`UnicodeEncodeError` (a `ValueError`, **not** an `OSError`) when a filename under the static root
is not valid UTF-8 — `Path.as_posix()` returns a surrogate-escaped string. Reproduced:

```
$ uv run python -c "...; common._compute_asset_version(Path(d))"
RAISED UnicodeEncodeError 'utf-8' codec can't encode character '\udcff' in position 3: surrogates not allowed
```

Because the call is at module scope (`:225`), the escape aborts the import of
`app.pages.common` — which `app/main.py` imports — so the whole application fails to boot with
an `ImportError` instead of degrading to `dev`. The precondition (a non-UTF-8 filename in
`app/static`, e.g. from a mounted volume) is unlikely from the repo tree, which is why this is a
warning rather than a blocker; the fix is one line and the blast radius is total.

**Fix:**

```python
            digest.update(f"{rel}\0{len(body)}\0".encode("utf-8", "surrogateescape"))
```

or widen the guard so the documented contract is actually the contract:

```python
    except (OSError, ValueError):
        return _ASSET_VERSION_DEGRADED
```

### WR-03: Six comments still say the version reaches "шесть тегов" — this phase reduced it to five, and nothing gates the number

**File:** `app/pages/common.py:151`, `:183`, `:217`;
`tests/test_pages/test_asset_version.py:25`, `:197`, `:237`

**Issue:** Before the phase each shell carried its own htmx `<script>`, so `asset_version` was
delivered on six tags. Collapsing the pair into one include left five:

```
app/templates/auth_base.html:23  (css/app.css)
app/templates/auth_base.html:63  (js/alpine.min.js)
app/templates/base.html:24       (css/app.css)
app/templates/base.html:26       (js/alpine.min.js)
app/templates/includes/htmx_config.html:55  (js/htmx.min.js)
```

Every comment introduced or kept by the phase still says six — including the ones that lean on
the number as load-bearing ("значение видно в разметке на шести тегах", "Мест доставки шесть",
"шесть тегов получили бы стабильный `?v=dev`"). Plans 07-01 and 07-02 ran in parallel waves and
07-02 was written against the pre-merge count; nobody re-counted after the merge. This project
treats comment/code divergence as a first-class defect elsewhere in the same files, and the
number is the one thing here with no inventory gate.

**Fix:** change all six occurrences to five, and add the count to the existing inventory gate so
the next collapse or addition cannot pass silently:

```python
# tests/test_pages/test_asset_version.py
ASSET_VERSION_DELIVERY_SITES = 5

def test_asset_version_delivery_site_count():
    templates_dir = Path(__file__).resolve().parents[2] / "app" / "templates"
    sites = sum(
        source.count("?v={{ asset_version }}")
        for source in (p.read_text(encoding="utf-8") for p in templates_dir.rglob("*.html"))
    )
    assert sites == ASSET_VERSION_DELIVERY_SITES
```

### WR-04: The D-02 ordering rationale is false for htmx 2.0.10, and the gate asserts the wrong property

**File:** `app/templates/includes/htmx_config.html:14-22`;
`tests/test_pages/test_shell.py` (`_assert_config_precedes_runtime`)

**Issue:** The include's central justification reads "Рантайм читает конфигурацию ОДИН раз, при
разборе собственного тега: блок, оказавшийся ниже тега, не читается вовсе — молча". Traced
against the shipped artifact, that is not how 2.0.10 works:

```js
var Kn=false; te().addEventListener("DOMContentLoaded",function(){Kn=true});
function Gn(e){if(Kn||te().readyState==="complete"){e()}else{te().addEventListener("DOMContentLoaded",e)}}
function Zn(){const e=te().querySelector('meta[name="htmx-config"]');if(e){return v(e.content)}else{return null}}
function Yn(){const e=Zn();if(e){Q.config=le(Q.config,e)}}
Gn(function(){Yn(); Wn(); ...})
```

`Yn()` (mergeMetaConfig) runs inside `Gn()` (ready) — i.e. at **DOMContentLoaded**, not at script
parse time. A `<meta name="htmx-config">` anywhere in the server-rendered document is read,
above or below the runtime tag. The real safety property is "the meta is in the initial HTML,
not injected after DOMContentLoaded"; that property is untested, while
`_assert_config_precedes_runtime` tests a stricter one that carries no consequence.

Keeping the tags adjacent is still good practice — the problem is that a comment presented as the
architectural reason for D-02 states a mechanism the runtime does not have, and a future
maintainer will reason from it (e.g. concluding a `defer`-loaded runtime is unsafe, or that a
dynamically-injected meta would work).

**Fix:** correct the comment to describe the actual constraint, and keep the ordering assertion
but re-label it as a defensive style check, not the safety mechanism:

```
   Рантайм сливает мета-конфигурацию в `htmx.config` НА DOMContentLoaded
   (`Gn(function(){Yn(); ...})` в вендоренном 2.0.10), а не при разборе своего
   тега, поэтому требование к блоку — оказаться в ИСХОДНОМ документе, а не
   выше тега. Пара всё равно держится вместе и одним файлом: блок, вставленный
   скриптом ПОСЛЕ DOMContentLoaded, не читается вовсе и молчит об этом.
```

### WR-05: D-07's headline benefit is not delivered — no `Cache-Control`, and Starlette's ETag is mtime-derived

**File:** `app/pages/common.py:176-183` (claim); `app/main.py:82` (mount)

**Issue:** The rewrite is justified by two symmetric claims. The FOUND-03 half — "подмена байтов
ЛЮБОГО файла охвата меняет `?v=`" — is genuinely delivered. The D-07 half — "пересборка
контейнера из того же дерева сбрасывала кеш всем … два контейнера из одного дерева отдают
одинаковый `?v=`" — is not, end to end:

- `app.mount("/static", StaticFiles(directory=...))` sets **no** `Cache-Control` header at all,
  so there is no long-lived cache entry for the stable `?v=` to protect; browsers fall back to
  heuristic freshness and revalidate.
- On revalidation Starlette computes
  `etag = md5(f"{stat.st_mtime}-{stat.st_size}")` (`starlette/responses.py:335-341`).
  A container rebuild from the same tree changes `st_mtime` → new ETag → `200` with the full body,
  regardless of the identical `?v=`.

So a rebuild still re-ships `app.css` + htmx + Alpine to every returning user — the exact
behaviour the content hash was introduced to stop. This is a correctness-of-claim gap, not a
performance nit: a documented decision (D-07) records a benefit the deployment does not produce.

**Fix:** pair the content hash with an immutable cache policy, which is what makes a
content-addressed `?v=` meaningful:

```python
class ImmutableStatic(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers.setdefault("cache-control", "public, max-age=31536000, immutable")
        return response

app.mount("/static", ImmutableStatic(directory=str(_static_dir)), name="static")
```

If that is out of this phase's scope, strike the D-07 rebuild claim from the docstring rather
than leaving a recorded benefit that does not exist.

### WR-06: Shell divergence is only one-fifth fixed, and only the fixed fifth has a gate

**File:** `app/templates/includes/htmx_config.html:5-13`; `app/templates/base.html:24,26`;
`app/templates/auth_base.html:23,63`

**Issue:** The include's premise is that the two shells' `<head>`s "совпадают построчно" and that
literal duplication across them is the defect class ("правка, внесённая в один шелл и забытая во
втором, дала бы пользователю РАЗНОЕ поведение"). After the phase, four of the five asset tags are
still two literal copies each:

- `app.css` link: `base.html:24` and `auth_base.html:23`
- Alpine script: `base.html:26` and `auth_base.html:63`

plus `charset`, `viewport`, `theme-color`, `color-scheme` and both `apple-mobile-web-app-*` metas.
`test_htmx_runtime_tag_has_single_source` gates only the htmx reference, so the stated failure
mode remains fully live for everything else, with no gate at all. The include is explicit that
"Ссылка на таблицу стилей и тег Alpine остаются в шеллах — к этой паре они отношения не имеют",
but the *reason* given for extracting the htmx pair (drift between two hand-maintained copies)
applies identically to them.

**Fix:** either extract the common `<head>` prelude into a second include
(`includes/head_assets.html`) so the shells hold one line each, or extend the ownership gate to
cover every `?v={{ asset_version }}` tag by declared owner+count so a third copy cannot appear
unnoticed. At minimum, replace the "к этой паре они отношения не имеют" line with the real
reason (scope of this phase) so it does not read as a claim that those tags are immune.

### WR-07: The inventory gate's "place = line containing `hx-get`" heuristic reproduces the trap it warns about

**File:** `tests/test_templates/test_htmx_inventory.py:169-189`, `:143`, `:278-311`

**Issue:** `_hx_get_lines()` defines a place as *a line containing the substring `hx-get`*. The
file goes to considerable length to explain why counting `hx-trigger="revealed"` occurrences is
unsound (the prose comment at `base.html:241` makes the naive count 13), then applies the same
substring-per-line technique to `hx-get` itself with no equivalent guard. Concrete fragilities,
all currently latent:

- Two `hx-get` attributes on one line collapse to one place. Verified none exist today, so the
  gate is green by luck of formatting, not by construction.
- A prose comment mentioning `hx-get` counts as a real place, and if it also contains
  `hx-trigger="revealed"` it can mask a genuinely lost markup site — the exact substitution the
  file's own "ЛОВУШКА СЧЁТА" section describes.
- `_mechanism_of` requires `hx-get` and its trigger to sit on the **same** source line. A pure
  reformat that wraps attributes reclassifies the site (`revealed` → `conditional`/`unknown`) and
  fails the gate with a message about markup that did not change.
- `REVEALED_LITERAL_OCCURRENCES = 13` and `assert literal - sites == 1` couple the suite to one
  specific prose comment (`base.html:241`, a note about View Transitions). Deleting or rewording
  that unrelated comment turns the gate red with "место молча исчезло или появилось незаявленное"
  — blaming markup for a documentation edit.

**Fix:** count attribute occurrences rather than lines, and classify per element rather than per
line:

```python
HX_GET_ATTR = re.compile(r'\bhx-get\s*=')

def _hx_get_occurrences(source: str) -> int:
    return len(HX_GET_ATTR.findall(_strip_jinja_comments(source)))
```

and strip `{# ... #}` / `<!-- ... -->` before counting, which removes the `base.html:241`
coupling and lets `REVEALED_LITERAL_OCCURRENCES` drop to the honest 12.

---

## Info

### IN-01: `_asset_scope` suffix matching is case-sensitive

**File:** `app/pages/common.py:169`

**Issue:** `path.suffix in ASSET_SCOPE_SUFFIXES` with `(".css", ".js")` silently excludes
`.CSS`/`.JS`. On a case-insensitive filesystem (macOS dev machines) such a file would be served
by the mount but left out of the version, so byte changes to it would not bust caches — the
FOUND-03 failure mode, scoped to one file.

**Fix:** `if path.suffix.lower() in ASSET_SCOPE_SUFFIXES and path.is_file()`.

### IN-02: `test_htmx_runtime_tag_has_single_source` matches the path substring anywhere in a template, including prose

**File:** `tests/test_pages/test_shell.py` (`HTMX_RUNTIME_SOURCE_REF = "js/htmx.min.js"`)

**Issue:** The gate flags any template whose source contains `js/htmx.min.js`, so a Jinja comment
that merely *mentions* the runtime path in another template fails with "ссылка на рантайм htmx
перестала быть единственной в шаблонах". Given how comment-dense this codebase is, that is a
realistic false positive.

**Fix:** match the tag rather than the path, e.g.
`re.compile(r"<script[^>]*js/htmx\.min\.js")`, or strip Jinja comments before searching.

### IN-03: The include's filename understates its contents

**File:** `app/templates/includes/htmx_config.html`

**Issue:** The file owns both the config `<meta>` and the runtime `<script>` — deliberately, per
D-02 — but the name says only "config". A maintainer looking for where htmx is loaded will grep
`<script` in the shells and find nothing. The file's own header comment explains the pairing;
the filename does not.

**Fix:** rename to `includes/htmx.html` (or `includes/htmx_runtime.html`) and update the two
`{% include %}` sites and `HTMX_RUNTIME_OWNER` in `tests/test_pages/test_shell.py`.

---

_Reviewed: 2026-08-27T11:49:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

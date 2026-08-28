---
phase: 07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii
reviewed: 2026-08-27T21:50:37Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - app/pages/common.py
  - app/static/js/htmx.min.js
  - app/templates/auth_base.html
  - app/templates/base.html
  - app/templates/includes/htmx_config.html
  - tests/test_pages/test_asset_version.py
  - tests/test_pages/test_htmx_response_contract.py
  - tests/test_pages/test_shell.py
  - tests/test_templates/test_htmx_inventory.py
findings:
  critical: 1
  warning: 7
  info: 3
  total: 11
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-08-27T21:50:37Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Re-review after gap closure (plans 07-04 … 07-07). Findings are stated from a fresh
reading of the current files; no prior finding was assumed fixed or unfixed.

**Independently verified as sound (previously suspect classes now closed):**

- `app/static/js/htmx.min.js` **is** the artifact it claims to be. Measured directly:
  51 238 bytes, SHA-384 `H5Srcfyg…sK+V`, `version:"2.0.10"` present — all three match
  `HTMX_BYTES` / `HTMX_SHA384` / `HTMX_VERSION` in `tests/test_pages/test_shell.py:1256-1258`
  exactly. Predecessor size claim (47 755 B for 1.9.10) also checks out against git.
- Every factual claim the new prose makes about the runtime was re-derived from the
  vendored bytes and holds: `localStorage` occurrences = 0, `sessionStorage` = 9;
  `zt()` really does `sessionStorage.removeItem("htmx-history-cache")` and returns
  when `historyCacheSize <= 0`; the config block really is read by `querySelector`
  over the whole document and merged inside the ready wrapper (`Gn(function(){Yn();…})`),
  so the corrected claim in `htmx_config.html:14-33` is right and the old one was wrong.
- All six config keys exist in the 2.0.10 runtime — none is a silently-ignored typo.
- The `responseHandling` ordering argument is correct: rules are tested top-down with
  unanchored `RegExp`, so `"422"` above `"[45].."` is load-bearing, and `_assert_config_contract`
  gates it by index.
- `reportValidityOfForms: true` is safe for the one htmx-driven form: `#ad-form`
  carries no `required`/`pattern`/`min`/`max` (checked), which `ads/form.html:50-52`
  had already anticipated.
- `allowNestedOobSwaps: false` does not break the four existing OOB elements: all four
  in `ads/includes/autosave_response.html` are top-level in the response fragment, and
  htmx's guard is `e.parentElement === null`, which holds for `<template>.content` children.
- All four in-scope test modules run green locally: 142 passed
  (`test_asset_version.py`, `test_htmx_inventory.py`, `test_htmx_response_contract.py`,
  `test_shell.py`). This confirms the gates execute and pass; it is *not* evidence
  against the findings below, several of which are precisely about gates that stay
  green while the property they claim to guard is false or invisible to them.

**What is still wrong.** The version calculator has a silent fail-open path that
reinstates the exact defect the phase exists to close (CR-01). The new configuration
turns an application-*unauthored* response body into an HTML/script sink without
disabling htmx's script execution (WR-01). Two of the new gates do not gate what
their prose says they gate — one is blind to the codebase's own dominant idiom
(WR-02), one is blind to htmx's official `data-` attribute alias (WR-04). One
load-bearing prose claim is simply false and disprovable in one grep (WR-03). The
remaining warnings are gate brittleness and duplication that contradict the project's
own stated single-source doctrine.

Out of review scope but worth recording: the phase's core behavioural criterion
("22 places work on 2.0.10, no infinite-scroll cascade") is closed by manual UAT only,
and `tests/test_templates/test_htmx_inventory.py:22-28` itself records that half as
**open**. The green suite is not evidence for it, as that file honestly says.

## Critical Issues

### CR-01: Asset version fails open to a constant `"dev"` with no signal, silently restoring FOUND-03

**File:** `app/pages/common.py:232-243` (and `258`)

**Issue:** `_compute_asset_version` swallows `OSError` and `ValueError` and returns the
constant `_ASSET_VERSION_DEGRADED = "dev"`, and does the same for an empty scope. It
logs nothing, raises nothing, and exposes no runtime indicator. The value is computed
once at import (line 258) and frozen for the process lifetime.

Consequences, in order of severity:

1. `"dev"` is **constant across restarts**. Once a deploy hits the degraded path, every
   `<link>`/`<script>` on all five delivery sites emits `?v=dev` forever. Browsers that
   cached `…/htmx.min.js?v=dev` keep executing the *old* runtime against a 2.x server —
   which is FOUND-03 verbatim, the defect this phase was created to fix. The mitigation
   has a failure mode that reproduces the bug it mitigates.
2. It is **silent**. A single unreadable file on a mounted volume (permissions, a
   partially-synced bind mount, a `.js` that lost read bits) collapses the version for
   the *entire* scope. The docstring at lines 213-215 explicitly states that degradation
   "means cache invalidation does not work" — yet nothing anywhere says so at runtime.
3. It is **undetectable from outside**. `test_inventory_real_asset_version_is_not_degraded`
   (`tests/test_pages/test_asset_version.py:312`) catches this in CI only. CI does not
   run against the production volume; the one environment where the failure can actually
   occur is the one with no check.

Note the internal inconsistency: the same function goes to real trouble (`surrogatepass`
encoding, lines 239 and 219-224) so that *one* oddly-named file cannot "silently switch
off cache-busting for everyone else" — and then lets *one* unreadable file do exactly
that, silently.

**Fix:** log the degraded path so it is visible in the aggregated logs the project already
runs (Loki/Promtail are configured), and name the cause:

```python
import logging

logger = logging.getLogger(__name__)


def _compute_asset_version(root: Path = _static_dir) -> str:
    try:
        scope = _asset_scope(root)
        if not scope:
            logger.error(
                "asset_version degraded to %r: scope under %s is empty — "
                "cache-busting is OFF for every static link",
                _ASSET_VERSION_DEGRADED,
                root,
            )
            return _ASSET_VERSION_DEGRADED
        digest = hashlib.sha256()
        for rel in scope:
            body = (root / rel).read_bytes()
            digest.update(f"{rel}\0{len(body)}\0".encode("utf-8", "surrogatepass"))
            digest.update(body)
    except (OSError, ValueError):
        logger.exception(
            "asset_version degraded to %r while hashing %s — "
            "cache-busting is OFF for every static link",
            _ASSET_VERSION_DEGRADED,
            root,
        )
        return _ASSET_VERSION_DEGRADED
    return digest.hexdigest()[:ASSET_VERSION_LEN]
```

Consider additionally making the degraded value non-constant (e.g. `"dev-" + uuid4().hex[:8]`)
so a degraded container at least does not pin stale assets in returning browsers, and
adding the value to whatever health/readiness surface exists.

## Warnings

### WR-01: The `422 swap:true` rule newly makes an application-unauthored body an HTML/script sink, and the config leaves `allowScriptTags`/`allowEval` on

**File:** `app/templates/includes/htmx_config.html:112` (rule), `103-116` (block)

**Issue:** Before this phase there was no `responseHandling`, so htmx 1.9.10 never swapped
a non-2xx body into the page. This phase adds `{"code":"422","swap":true,"error":true}`,
which makes htmx parse and insert a 422 response body into the DOM.

The file's own risk analysis (lines 71-86) reasons this through and stops one step short.
It correctly establishes that no route in `app/` authors a 422 body, so any 422 today is
the framework default — a Pydantic error document that echoes the offending value verbatim
in `input`. It then states the worst case as: the user "gets machine text in a card".
That is not the worst case. Measured against the vendored artifact:

- htmx defaults are `allowScriptTags:true` and `allowEval:true` (confirmed in the
  artifact's defaults object), and the config block does not override either.
- The swap path parses the body via `<template>` and, when `allowScriptTags` is true,
  calls the script-reviving helper `D(r)` on the fragment — i.e. `<script>` elements in a
  swapped body are re-created and **executed**.

So the accurate statement is: a 422 body that the application does not control, and which
echoes raw user input, is parsed as HTML and script-executed in the page.

**Reachability today: none that I could prove**, and this is why the finding is a WARNING
rather than a blocker. I traced every one of the 22 `hx-get` URLs and both `hx-post` sites:

- All sentinel URLs take `offset`/`limit` from server-validated ints and `filter_params`
  values through `|urlencode`, and every endpoint types those filter params as `str | None`
  (`app/pages/history.py:590-597`, `app/pages/ads.py:151-158`, `app/pages/admin.py:1468-1474`)
  — a `str` param cannot produce a 422.
- `#ad-form` carries `hx-swap="none"`, so even a 422 there swaps nothing.

The guard is therefore "no htmx-issued URL currently carries a user-influenced typed
param", which is an accident of the current routes, gated by nothing. `tests/test_pages/test_htmx_response_contract.py`
gates the *server* side of the divergence; nothing gates the *client* side.

**Fix:** close the sink rather than rely on the absence of a path. Either disable script
execution in swapped content, which costs the project nothing (no swapped fragment in this
codebase contains a `<script>`):

```html
  "allowScriptTags": false,
  "allowEval": false,
```

or drop `swap` from the 422 rule until FORM-08 actually lands a route that authors an HTML
422 body — the gate at `test_htmx_response_contract.py:72` already forces that decision to
be made in one commit. If neither is taken, correct lines 71-86 to state the real worst
case; the current text understates it and a future reader will inherit the understatement.

### WR-02: The 422 gate matches only integer literals, and the codebase's dominant idiom is the symbolic constant

**File:** `tests/test_pages/test_htmx_response_contract.py:117-124`

**Issue:** `_status_code_literals` flags `status_code=` only when the value is
`ast.Constant` with `type(value.value) is int` and equal to 422. Its docstring (lines 78-88)
declares it searches "both ways to introduce a source of the code" and forbids simplifying
the helper. But there is a third, and in this repository a *prevailing*, form it does not
see:

```
$ grep -rEc "status_code=status\.HTTP" app --include=*.py   →  41 occurrences
$ grep -rEc "status_code=[0-9]"        app --include=*.py   → 136 occurrences
```

`status_code=status.HTTP_422_UNPROCESSABLE_ENTITY` parses to `ast.Attribute`, not
`ast.Constant`, so it passes the gate silently. Likewise `HTTPException(422)` (positional)
and `status_code=SOME_CONST`. The gate is guarding against exactly the change it cannot see:
23% of this codebase's existing status codes are written in the invisible form, so the odds
that the first 422 arrives in that form are high, and when it does the constant stays 0 and
the suite stays green.

**Fix:** resolve the symbolic form as well, and fail loudly on forms that cannot be resolved:

```python
VALIDATION_STATUS_NAMES = (
    "HTTP_422_UNPROCESSABLE_ENTITY",
    "HTTP_422_UNPROCESSABLE_CONTENT",  # starlette >= 0.47 spelling
)

def _is_validation_code(value: ast.expr) -> bool:
    if isinstance(value, ast.Constant) and type(value.value) is int:
        return value.value == VALIDATION_STATUS_CODE
    name = value.attr if isinstance(value, ast.Attribute) else getattr(value, "id", None)
    return name in VALIDATION_STATUS_NAMES
```

and apply it to positional `HTTPException(...)` / `JSONResponse(...)` first arguments too.

### WR-03: Load-bearing claim "the project's only inline script" is false

**File:** `app/templates/includes/htmx_config.html:118`

**Issue:** The comment opens `ЕДИНСТВЕННЫЙ ИНЛАЙН-СКРИПТ ПРОЕКТА, И ЭТО НАЗВАННОЕ
ОТСТУПЛЕНИЕ ОТ РАМКИ ВЕХИ «БЕЗ НОВОГО JS» (D-11)`. Three other inline `<script>` blocks
already exist in templates:

- `app/templates/ads/form.html:283` — a substantial block (server values via `| tojson`, DOM tile builder)
- `app/templates/accounts/connect_tg_user.html:71` — polling/session logic
- `app/templates/accounts/partials/connect_status.html:34` — `setTimeout(() => window.location.href = "/accounts", 2000);`

This is not pedantry about wording. The claim is what carries the risk framing ("a named
departure"), and it is also implicitly what justifies scoping
`test_history_cache_purge_touches_no_markup_sink` to this one file. In a codebase whose
whole method is "a stated claim must be true or gated", an ungated false claim is the
defect class the project is built to prevent — the same class WR-05 of the previous review
and the `test_asset_version_delivery_site_count` gate were created for.

**Fix:** correct the sentence to what is true and gate the number, e.g.
`ЧЕТВЁРТЫЙ ИНЛАЙН-СКРИПТ ПРОЕКТА И ЕДИНСТВЕННЫЙ В <head> ОБОИХ ШЕЛЛОВ` plus an inventory
gate in the shape the project already uses:

```python
INLINE_SCRIPT_SITES = {
    "includes/htmx_config.html",
    "ads/form.html",
    "accounts/connect_tg_user.html",
    "accounts/partials/connect_status.html",
}
```

### WR-04: The `hx-get` inventory is blind to `data-hx-get`, and says so for a wrong reason

**File:** `tests/test_templates/test_htmx_inventory.py:191-194`, `201`

**Issue:** `HX_GET_ATTR = re.compile(r"(?<![-\w])hx-get\s*=")`. The comment justifies the
negative lookbehind as excluding attributes "where `hx-get` is only the tail of a name
(`data-hx-get`)". That premise is wrong: `data-hx-get` is not an unrelated name with a
matching tail — it is htmx's official equivalent spelling of the same attribute. The
vendored runtime treats them as one everywhere (its own selectors read
`"[hx-swap-oob], [data-hx-swap-oob]"`, `"[hx-trigger='restored'],[data-hx-trigger='restored']"`,
`"[hx-history-elt],[data-hx-history-elt]"`).

The consequence is the one silent hole in an otherwise well-constructed gate: a real 23rd
place written as `data-hx-get` is invisible to the attribute count, invisible to the tag
count, and invisible to the mechanism buckets — so all three totals stay at 22 and every
assertion stays green while the inventory is wrong. Every other mis-shaped place in this
gate fails *loudly* (unknown mechanism, or tag/attribute count mismatch); this one does not.

**Fix:** count both spellings and keep `data-` out of the "tail of a name" story:

```python
HX_GET_ATTR = re.compile(r"(?<![-\w])(?:data-)?hx-get\s*=")
HX_GET_TAG = re.compile(r"<[^<>]*?(?<![-\w])(?:data-)?hx-get\s*=[^<>]*>")
REVEALED_TRIGGER_RE = re.compile(r'(?<![-\w])(?:data-)?hx-trigger="revealed"')
POLL_TRIGGER = re.compile(r'(?<![-\w])(?:data-)?hx-trigger="every\s')
```

(`REVEALED_LITERAL_OCCURRENCES` then counts regex matches rather than `str.count`.)

### WR-05: The purge gate scans prose, in the one module that defines a comment stripper for that exact reason

**File:** `tests/test_pages/test_shell.py:1687-1697`

**Issue:** `test_history_cache_purge_touches_no_markup_sink` runs two substring assertions
over the **raw** template source:

```python
offenders = [sink for sink in MARKUP_SINKS if sink in source]
...
assert "request" not in source
```

`MARKUP_SINKS` contains `"innerHTML"` and `"outerHTML"` — both are ordinary `hx-swap`
values used elsewhere in this project (`accounts/connect_wa.html:34`,
`accounts/connect_max.html:47`, all twelve `revealed` sentinels). The file under test is
100+ lines of justification prose about htmx swapping. One sentence naming `hx-swap="innerHTML"`,
or one English word "request", reds the gate with the message "a markup sink appeared" /
"the inline script started reading the request" — accusing the script of something the
edit did not do.

This is the precise false-positive class the same module already solved 340 lines earlier:
`_without_comments` (line 1360) exists, its docstring (lines 1370-1379) argues that a gate
which reds on prose "teaches edits to delete prose — i.e. exactly backwards", and the two
neighbouring single-source gates both call it. This gate does not. `"request" not in source`
is additionally over-broad by design: it fires on any substring occurrence anywhere in the
file, not on a `request` access inside the `<script>`.

**Fix:** reuse the module's own stripper and narrow the scope to the script body:

```python
_INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>", re.DOTALL)

source = (PROJECT_ROOT / "app" / "templates" / LEGACY_HISTORY_CACHE_OWNER).read_text("utf-8")
scripts = "\n".join(_INLINE_SCRIPT_RE.findall(_without_comments(source)))

offenders = [sink for sink in MARKUP_SINKS if sink in scripts]
assert not offenders, ...
assert "request" not in scripts, ...
```

### WR-06: `allowNestedOobSwaps: false` changes semantics for five existing OOB places, and is the one config key whose consequence is not written down or gated

**File:** `app/templates/includes/htmx_config.html:105`

**Issue:** The file goes to considerable length to state the consequence of one key
(`historyCacheSize`, lines 45-58: "the whole load is carried by this value; any future
edit silently cancels the property, and a gate `_assert_config_contract` watches it").
`allowNestedOobSwaps: false` gets no such paragraph, yet it is the key with a live
behavioural effect on existing markup.

Measured in the vendored runtime, the guard is:

```js
if (Q.config.allowNestedOobSwaps || e.parentElement === null) { …perform OOB swap… }
else { e.removeAttribute("hx-swap-oob"); e.removeAttribute("data-hx-swap-oob"); }
```

With the flag off, an `hx-swap-oob` element that is *not* a top-level node of the response
fragment does not perform an out-of-band swap. It is not an error and nothing is logged —
the attribute is stripped and the element is swapped inline instead, i.e. it lands in the
wrong place, or nowhere when the swap style is `none`.

The five existing places (`ads/includes/autosave_response.html:19,20,34` and the indicator
from `ads/includes/autosave.html:28` via line 21) are all top-level today — I verified each,
and this is why the flag is safe right now. But the property "every `hx-swap-oob` element is
a top-level node of its response fragment" is now load-bearing for the ad editor's autosave
(preview, summary, indicator, and the `#ad-id-field` whose loss the comment at
`autosave_response.html:22-33` describes as "silent loss of the user's work"), and nothing
gates it. Wrapping the two `<div>`s in a container "for tidiness" would break autosave
silently.

**Fix:** add the missing paragraph naming the consequence, and add a gate in the project's
existing inventory shape — e.g. assert that in every template that renders an OOB response
fragment, each `hx-swap-oob` occurrence is at nesting depth 0 of that template, or at
minimum inventory the five places with `OOB_SITES` so a sixth cannot appear unnoticed.

### WR-07: Comment stripping now exists in three non-identical copies across the new test modules

**File:** `tests/test_pages/test_shell.py:1349`; `tests/test_templates/test_htmx_inventory.py:203-204`, `226`; `tests/test_pages/test_asset_version.py:345-346`

**Issue:** Three modules landed by this phase each implement "template source without
comments", and two of the three are not the same algorithm:

- `test_shell.py:1349` — single pass, alternation: `re.compile(r"\{#.*?#\}|<!--.*?-->", re.DOTALL)`
- `test_htmx_inventory.py:226` — two passes, Jinja then HTML, with a docstring arguing the
  order is significant ("Jinja runs first")
- `test_asset_version.py:372` — the same two passes, third copy

The two forms are not equivalent on interleaved delimiters (e.g. `<!-- a {# b --> c #}`
yields `<!-- a ` under the two-pass form and ` c #}` under the alternation form), so the
argument that "the order of stripping is significant" is true for two of the three copies
and simply not implemented in the third.

More to the point, this contradicts the doctrine every one of these files invokes by name:
`htmx_config.html:5-12` and `test_shell.py:1364-1367` both argue that a second copy of a
rule "would diverge from the first exactly as two literal config blocks would (D-01)" — and
then the helper that enforces that doctrine is itself carried in three copies.

**Fix:** hoist one implementation into a shared test helper (`tests/support/templates.py`
or `tests/conftest.py`) and import it in all three, keeping the two-pass semantics that two
of the three modules argue for. This also removes the cross-module private import flagged
in IN-02.

## Info

### IN-01: htmx still injects an inline `<style>` into `<head>` on every page

**File:** `app/templates/includes/htmx_config.html:103-116`

**Issue:** `includeIndicatorStyles` is left at its default `true`, so on every page load the
runtime calls `head.insertAdjacentHTML("beforeend", "<style>…")` to define `.htmx-indicator`
rules. `app/static/css/app.css` defines no `.htmx-indicator` rules and no template uses the
class — the injected style is dead weight, and it is a second inline-`<style>` source to
account for when the deferred CSP (T-07-11) lands.

**Fix:** add `"includeIndicatorStyles": false` to the block (and update the "six keys" count
in `htmx_config.html`, `test_shell.py:HTMX_CONFIG`, and the `_assert_config_contract`
docstring together, as the file's own convention requires).

### IN-02: Cross-module import of a private helper couples the response-contract gate to a 1700-line module

**File:** `tests/test_pages/test_htmx_response_contract.py:38`

**Issue:** `from tests.test_pages.test_shell import _htmx_config_of` imports a leading-underscore
helper across test modules, which pulls in all of `test_shell.py`'s import-time work (regex
compilation, `PROJECT_ROOT` resolution, fixtures) and makes the response-contract gate fail
on any unrelated import-time breakage in a 1697-line neighbour. The single-source motive is
right; the placement is not.

**Fix:** move `_htmx_config_of`, `HTMX_CONFIG_RE` and the comment stripper (WR-07) into a
shared, public test-support module and import from there in both places.

### IN-03: Type discipline in `_assert_config_contract` stops at the top level

**File:** `tests/test_pages/test_shell.py:1401-1430`

**Issue:** The helper's docstring and the config comment at `htmx_config.html:54-58` both
advertise that the gate "checks not only the value but the TYPE, because in Python
`False == 0`". That check is applied only to the six top-level values. Inside
`responseHandling`, the rule dicts are compared with plain `==`, so `{"swap": 1}` and
`{"swap": 0}` would satisfy the gate. Behaviour is unaffected (htmx tests truthiness), so
this is informational — but the stated guarantee is broader than the implemented one, and
in this codebase that gap is itself the tracked defect class.

**Fix:** either extend the type check into the rule dicts, or narrow the two docstrings to
say the type check covers the top-level keys.

---

_Reviewed: 2026-08-27T21:50:37Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
reviewed: 2026-08-28T00:00:00Z
depth: standard
files_reviewed: 54
files_reviewed_list:
  - alembic/versions/0021_payments_open_intent_index.py
  - app/dependencies.py
  - app/main.py
  - app/models/payment.py
  - app/pages/__init__.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/auth.py
  - app/pages/billing.py
  - app/pages/common.py
  - app/pages/history.py
  - app/pages/htmx.py
  - app/pages/notices.py
  - app/pages/profile.py
  - app/pages/schedules.py
  - app/services/payment_service.py
  - app/templates/admin/payments.html
  - app/templates/admin/workers.html
  - app/templates/ads/form.html
  - app/templates/auth/login.html
  - app/templates/auth_base.html
  - app/templates/base.html
  - app/templates/billing/balance.html
  - app/templates/history/list.html
  - app/templates/includes/htmx_error_banner.html
  - app/templates/includes/notice_area.html
  - app/templates/includes/notice_oob.html
  - tests/conftest.py
  - tests/test_application/declared_invariants_without_witness.txt
  - tests/test_application/test_declared_invariants.py
  - tests/test_infra/__init__.py
  - tests/test_infra/test_web_service_is_single_process.py
  - tests/test_migrations/test_0021_payments_open_intent_index.py
  - tests/test_models/test_payment_open_intent_index.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_admin_payments.py
  - tests/test_pages/test_billing_payment_errors.py
  - tests/test_pages/test_billing_section.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_money_perimeter_gate.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_notices_registry.py
  - tests/test_pages/test_notices_surface.py
  - tests/test_pages/test_password_reset.py
  - tests/test_pages/test_schedule_ownership.py
  - tests/test_pages/test_shell.py
  - tests/test_services/test_payment_concurrency.py
  - tests/test_services/test_payment_intent_cap.py
  - tests/test_services/test_payment_service.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_htmx_markup_security.py
findings:
  critical: 1
  warning: 8
  info: 4
  total: 13
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-08-28
**Depth:** standard
**Files Reviewed:** 54
**Status:** issues_found

## Summary

Reviewed the four waves of Phase 08: the response layer (`app/pages/htmx.py`), the closed
notice registry (`app/pages/notices.py`), the notice surface templates, and the money cap
(migration `0021` + rewritten `create_payment`). Cross-referenced every consumer of the new
`expired` payment status, every writer of the new `?notice=` channel, and both transports of
`refuse()`.

The most serious defect is a **cross-module consequence of the new fourth payment status**.
`expired` was deliberately kept out of `TERMINAL_STATUSES` so that a swept intent stays payable —
but two *pre-existing* readers of "unclosed payment" are defined as `status NOT IN
TERMINAL_STATUSES` and were not updated. Every row the migration backfill or the lazy sweep
expires is, by construction, older than the stuck-payment threshold, so it becomes a permanent
false "payment stuck" incident on the admin overview and is listed under the admin filter chip
labelled "В обработке" while the same row prints as "просрочен". Because the incident block is
capped at 20 and sorted newest-first, accumulating expired intents can push genuinely stuck
payments out of view. Neither `app/application/admin/incidents.py` nor
`app/application/admin/payments_query.py` is in the phase diff, and no test covers the
interaction.

Secondary findings concentrate on the money path (an `IntegrityError` classifier that cannot
actually distinguish a foreign rejection when the user already has an open intent; a
money-without-goods window that the docstring claims is closed but is not) and on the response
layer being entirely unreachable from `app/` while the twelve notice writers bypass every
validation the layer provides.

The `is_htmx` empty-header decision and the name-free `IntegrityError` handling were excluded
from review per the phase brief. Machine gates were judged as gates.

## Critical Issues

### CR-01: The new `expired` status silently matches "unclosed payment" and manufactures false stuck-payment incidents

**File:** `app/services/payment_service.py:50,78`; `alembic/versions/0021_payments_open_intent_index.py:150`; consumers at `app/application/admin/incidents.py:434,447,475,631,635,669` and `app/application/admin/payments_query.py:105`

**Issue:**
`STATUS_EXPIRED` is deliberately excluded from `TERMINAL_STATUSES` (`payment_service.py:78`) so a
swept intent stays payable. But the project's single definition of "payment is not closed" is:

```python
# app/application/admin/incidents.py:434
def unclosed_payment_clause():
    return Payment.status.not_in(tuple(TERMINAL_STATUSES))
```

`'expired'` is not in `{'succeeded', 'canceled'}`, so every expired row matches. That clause has
two live readers, both of which now misreport:

1. **False stuck-payment incidents (money-grade alarm).**
   `unclosed_payments_stmt` (`incidents.py:475`) selects unclosed rows with
   `Payment.created_at <= payment_stuck_before(now)`, and `payment_stuck_before`
   (`incidents.py:447`) is `now - PENDING_INTENT_TTL_HOURS` — the *same* 24 h constant the sweep
   uses. Therefore **every row `_expire_stale_intents` gasses is, by construction, already past
   the stuck threshold**, and `detect_payment_stuck` (`incidents.py:385`) raises an incident for
   it on the very next admin overview load. The incident never clears, because `expired` is not
   terminal by design. Migration `0021`'s backfill (`0021:150`) mass-converts rows to `expired`,
   so this fires as an incident flood on the first admin page view after deploy — exactly the
   "число переведённых строк пишется в журнал" event the revision documents, but surfaced as an
   operational alarm nobody decided to raise.

2. **Real incidents get hidden.** `incidents.py:669/675` truncates to `INCIDENT_LIST_CAP = 20`
   after sorting newest-first. Freshly expired intents (25 h old) sort *above* genuinely stuck
   payments (weeks old), so accumulating expired intents evict real money incidents from the
   block that exists precisely to surface them.

3. **Contradictory admin filter.** `PAYMENT_STATUS_FILTERS["unclosed"]` is labelled
   `"В обработке"` (`payments_query.py:105`) and is backed by the same clause, so expired rows are
   returned under "in processing" while `app/templates/admin/payments.html:39` renders them as
   `просрочен`. The phase's own D-14 rule ("one state is called by one word for user and admin")
   is violated by the filter, not by the label.

This is the failure mode `unclosed_payment_clause`'s own docstring predicted ("достаточно, чтобы
платёжный провайдер завёл четвёртый статус") — inverted: *we* added the fourth status, and the
`NOT IN` form absorbed it silently. No test in the phase covers it; `test_admin_payments.py`
only asserts the new label renders.

**Fix:** Introduce an explicit "open intent" set and make the incident/filter readers use it,
rather than deriving "unclosed" from the complement of `TERMINAL_STATUSES`:

```python
# app/services/payment_service.py
TERMINAL_STATUSES = frozenset({STATUS_SUCCEEDED, STATUS_CANCELED})
# Статусы, из которых платёж ещё МОЖЕТ выйти сам, — то есть за которыми
# администратор наблюдает как за незакрытыми. `expired` сюда НЕ входит:
# строка погашена решением приложения, наблюдать за ней нечего, хотя
# оплачиваемой она остаётся (см. TERMINAL_STATUSES).
AWAITING_STATUSES = frozenset({STATUS_PENDING})

# app/application/admin/incidents.py
def unclosed_payment_clause():
    return Payment.status.in_(tuple(AWAITING_STATUSES))
```

and add a regression asserting that a row in `STATUS_EXPIRED` produces **no**
`INCIDENT_KIND_PAYMENT_STUCK` and does **not** appear under the `unclosed` chip. If the product
decision is instead that expired intents *should* be visible to the admin, add a fourth chip with
its own label and exclude them from the incident detector — but the current state (incident yes,
label "просрочен", filter "В обработке") is three answers to one question.

## Warnings

### WR-01: `_is_open_intent_conflict` cannot distinguish a foreign `IntegrityError` when the user already has an open intent

**File:** `app/services/payment_service.py:304-348`, used at `app/services/payment_service.py:405-424`

**Issue:** The classifier answers "was this our cap?" by counting rows matching the index
predicate. That is correct only in the direction the docstring tests
(`test_a_foreign_rejection_is_not_swallowed`: *no* pending row ⇒ re-raise). In the opposite
direction it is unconditionally wrong: if the user has an open pending subscription intent, **any**
`IntegrityError` raised by the reserve insert — FK violation on `user_id`, a `NOT NULL` violation
introduced by a future column, a unique violation on `yookassa_payment_id` — is reported as
`PendingIntentCapError`, and the user is told "предыдущая оплата ещё не завершена". The docstring
explicitly claims the opposite ("ПОЧЕМУ ОТВЕТ ОБЯЗАН БЫТЬ ТОЧНЫМ. Чужой отказ, принятый за свой,
показал бы человеку … и настоящая поломка осталась бы незамеченной"). The implementation
guarantees exactly that outcome for the common case, and the log line
`subscription_intent_cap_reached` will hide the real fault.

**Fix:** Narrow the classification with the facts already available at the raise site, and log the
original exception so the misclassification is at least diagnosable:

```python
except IntegrityError as rejection:
    if not await _is_open_intent_conflict(db, user_id):
        raise
    logger.warning(
        "subscription_intent_cap_reached",
        user_id=user_id,
        # Отказ различается перечитыванием состояния, а не текстом драйвера;
        # текст всё же пишется в ЖУРНАЛ, чтобы чужой отказ, совпавший с
        # открытым намерением, не остался невидимым.
        rejection_type=type(rejection.orig).__name__,
        rejection=str(rejection.orig),
    )
    raise PendingIntentCapError(...) from rejection
```

Additionally, on PostgreSQL (the production dialect) the constraint name *is* available via
`rejection.orig.diag.constraint_name`; using it when present, and falling back to the state re-read
on SQLite, removes the false positive on the dialect where it matters without breaking the suite.

### WR-02: The "money without goods" window is not closed by reserve-before-network; the docstring says it is

**File:** `app/services/payment_service.py:744-751` (write-back), docstring claim at `app/services/payment_service.py:369-381`

**Issue:** The reserve row is committed before `YooPayment.create` (good), but the row is linked to
the remote payment only *after* the network call returns:

```python
reserved.yookassa_payment_id = payment.id
await db.commit()
```

If the process dies, the connection drops, or that `commit()` fails between YooKassa creating the
payment and this write-back, the remote payment exists and the local row is `pending` with
`yookassa_payment_id IS NULL`. `handle_webhook` matches on `yookassa_payment_id`
(`payment_service.py:~875`), finds nothing, logs `webhook_payment_not_found` and returns `False` —
the user pays and never gets the month. The `idempotency_key` (`payment_service.py:661`) is a fresh
`uuid4()` that is never persisted, so there is no reconciliation key to recover from either. The
docstring asserts "локальная строка без удалённого платежа восстановима … удалённый платёж без
локальной строки — НЕТ", implying the second case is eliminated; it is only narrowed.

**Fix:** Persist the correlation key on the reserve row before the network call so the pair is
always recoverable, e.g. store `idempotency_key` in a column and add it to the webhook lookup
fallback, or generate the payment id client-side. At minimum, correct the docstring so the
remaining window is named (the phase's own doctrine is "цена размена названа, а не замолчана"), and
add a `payment_reserve_unlinked` log key on the write-back failure path.

### WR-03: The entire response layer is unreachable from `app/`; all twelve notice writers bypass its validation

**File:** `app/pages/htmx.py:180-367`; writers at `app/pages/billing.py:309,346,351`, `app/pages/history.py:911,958,962,998`, `app/pages/admin.py:926,945`, `app/pages/profile.py:77`, `app/pages/auth.py:813`, `app/pages/schedules.py:335`

**Issue:** `respond()` — declared "ГЛАВНЫЙ выход обработчика" and the sole enforcement point for the
mandatory degraded path — has **zero call sites in `app/`** (`NOT_YET_CONVERTED_COUNT = 36` in
`tests/test_pages/test_htmx_gates.py:236` confirms 36/36 handlers unconverted). Everything reachable
only through it is therefore dead in production: `_require_registered_notice`, `_notice_oob`,
`_glue_notice`, `_with_notice`, `NOTICE_QUERY_KEY`, `NOTICE_OOB_TEMPLATE`, and the whole
`includes/notice_oob.html` template. Consequences:

* The registry check at write time (`_require_registered_notice`, `htmx.py:180`) never runs on any
  real redirect — the check exists precisely to catch the typo that degrades silently.
* `_local_path` (`htmx.py:89`) never validates any real redirect target.
* The query key is declared once (`NOTICE_QUERY_KEY = "notice"`, `htmx.py:45`) and then hardcoded
  as the literal `?notice=` in twelve f-strings — the single-spelling doctrine the module argues
  for is not actually in force at any writer.
* The OOB channel (`notice_oob.html`) is exercised only by tests; its behaviour in a real browser
  is unverified.

This is defensible as staged work, but it should be recorded as a known gap rather than read as
"the notice channel is wired".

**Fix:** At minimum, route the twelve writers through a shared helper so the query key and the
registry check have one owner today, without waiting for the htmx cutover:

```python
# app/pages/htmx.py
def notice_redirect(path: str, notice: str) -> RedirectResponse:
    """302 с кодом исхода — единственная сборка на не-htmx пути."""
    _require_registered_notice(notice)
    return RedirectResponse(url=_with_notice(path, notice), status_code=302)
```

### WR-04: The impersonation notice code is written as a raw string literal, violating the registry's own rule

**File:** `app/dependencies.py:323`

**Issue:**
```python
IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"
```
`app/pages/notices.py:44-48` states the rule explicitly: "КОД ЕДЕТ КОНСТАНТОЙ, А НЕ ЛИТЕРАЛОМ …
опечатка в литерале даёт молчаливое «плашки нет»". This is the one place in the codebase that
breaks it, and it is the *worst* place to break it: the code travels via `refuse()`, which does
**not** call `_require_registered_notice`, so a typo produces a silent no-banner degradation with
no test and no log. The comment above the constant even anticipates this ("ДО ЭТОГО МОМЕНТА
ДЕГРАДАЦИЯ ТИХАЯ") but the constant was never converted after 08-02 registered the code.

The stated reason for not importing (`app.pages` circular import) is real for `app.pages.htmx`, but
`app.pages.notices` imports nothing from the app; a deferred module-level import inside the
function — the pattern already used for `refuse` two lines below — resolves it.

**Fix:**
```python
def _impersonation_refused_location() -> str:
    from app.pages.notices import IMPERSONATION_FORBIDDEN
    return f"/dashboard?notice={IMPERSONATION_FORBIDDEN}"
```
or assert the code's membership in the registry from `tests/test_pages/test_notices_registry.py`.

### WR-05: `_with_notice` drops the notice on any fragment-bearing or already-parameterised target

**File:** `app/pages/htmx.py:301-302`

**Issue:**
```python
separator = "&" if "?" in redirect else "?"
return _local_path(f"{redirect}{separator}{NOTICE_QUERY_KEY}={notice}")
```
Two latent failures for future callers:
* **Fragment.** `respond(request, redirect="/ads/7/edit#sched", notice=...)` yields
  `/ads/7/edit#sched?notice=x`. The notice becomes part of the fragment, is never sent to the
  server, and the banner silently does not render — the exact silent-outcome class the phase exists
  to eliminate.
* **Duplicate parameter.** If `redirect` already carries `?notice=…` (e.g. a caller reusing
  `IMPERSONATION_REFUSED_LOCATION`), the second value is appended and
  `request.query_params.get('notice')` returns the **first** one, so the argument is silently ignored.

**Fix:** Split on the fragment and refuse a pre-existing key:

```python
path, sep, fragment = redirect.partition("#")
if f"{NOTICE_QUERY_KEY}=" in path:
    raise ValueError("адрес приземления уже несёт код исхода: второй был бы проигнорирован")
separator = "&" if "?" in path else "?"
return _local_path(f"{path}{separator}{NOTICE_QUERY_KEY}={notice}{sep}{fragment}")
```

### WR-06: `htmx_client` mutates and returns the shared `client` object, silently converting any co-requested `client` into an htmx client

**File:** `tests/conftest.py:66-102` (mutation at `100-101`)

**Issue:**
```python
client.headers["HX-Request"] = "true"
client.follow_redirects = True
return client
```
The fixture returns the *same* object as `client`. Composition with `authed_client` is the stated
goal and works, but the side effect is unbounded: any test whose signature contains both `client`
and `htmx_client` — or which uses a helper that takes `client` — silently loses its non-htmx
baseline **and** its `follow_redirects=False` default. A test intending to assert "the non-htmx
path still returns 302" would then observe a followed 200 and pass for the wrong reason. There is
no guard preventing this composition.

**Fix:** Either make the fixture return a distinct client, or add an explicit incompatibility guard:

```python
@pytest_asyncio.fixture
async def htmx_client(client, request):
    assert "client" not in request.fixturenames or _only_via_htmx(request), (
        "тест просит и `client`, и `htmx_client` — это ОДИН объект, и не-htmx "
        "путь в нём уже недоступен"
    )
```
At minimum, state the hazard in the docstring alongside the composition benefit.

### WR-07: Both authorization gates deny by calling a function that must never return, with no `raise` at the call site

**File:** `app/pages/__init__.py:117-124`, `app/dependencies.py:389-396`

**Issue:**
```python
if not access_is_open(subscription, datetime.now(timezone.utc)):
    refuse(request, location=..., without_htmx=HTTPException(...))
# ← нет `raise`, нет `return`; исполнение продолжается, если refuse вернётся
```
`refuse` is annotated `NoReturn` and both branches raise today, so the behaviour is correct. But
the *deny* path of an access gate and of the impersonation gate is now a bare expression statement:
if a future edit adds any early-return branch to `refuse` (e.g. "if the request is a poll, do
nothing"), both gates fall through and grant access, with no syntax error, no type error at
runtime, and no visible diff at the call site. `NoReturn` is not enforced at runtime and the project
does not run a type checker in CI (no `mypy`/`ruff` in the environment).

**Fix:** Make the control flow local and explicit — the gate should be readable as a refusal without
reading the callee:

```python
raise refuse_error(request, location=..., without_htmx=HTTPException(...))
```
(i.e. have the helper *build and return* the exception, and let the caller `raise` it), or add a
defensive `raise AssertionError(...)` immediately after the `refuse(...)` call, plus a gate test
that asserts every call site of `refuse` is either `raise`d or immediately followed by an
unconditional raise.

### WR-08: Nested ARIA live regions — the notice areas and the `alert` macro both declare a role

**File:** `app/templates/includes/notice_area.html:62-63` with `app/templates/components/alert.html:10`

**Issue:** The outer area declares `role="status" aria-live="polite"` (or `role="alert"
aria-live="assertive"`), and the macro rendered *inside* it declares its own
`role="{{ 'alert' if variant == 'error' else 'status' }}"`. Nesting a live region inside a live
region is an ARIA anti-pattern: assistive technology may announce the message twice, or treat the
inner role as the authoritative one, defeating the file's own stated design ("признак живости
объявлен НА УЗЛЕ"). The same nesting exists in `includes/htmx_error_banner.html` (a wrapper `div`
around `alert(...)`).

**Fix:** Give the macro a way to render without its own role when it is placed inside a declared
live region:

```jinja
{% macro alert(message, variant='error', role=None) -%}
<div class="alert alert--{{ variant }}"{% if role %} role="{{ role }}"{% endif %}>{{ message }}</div>
{%- endmacro %}
```
and call it as `{{ alert(notice.text, notice.variant) }}` from the areas (no role) while standalone
call sites keep passing one. Verify with the existing markup gates that the role count per area
stays at one.

## Info

### IN-01: The money-perimeter gate asserts a decorative constant, not the hold

**File:** `tests/test_pages/test_money_perimeter_gate.py:121,416-449`

**Issue:** `MONEY_HOLD = "OPEN_INTENT_INDEX_NAME"`, and the check is "an `ast.Assign` to that name
exists in `payment_service.py`". That constant is documented as never read by code
(`app/services/payment_service.py:60-65`). Deleting the actual `Index(...)` from
`app/models/payment.py:__table_args__` — i.e. removing the cap from the schema the suite builds —
leaves this gate green. The gate acknowledges the delegation and
`tests/test_models/test_payment_open_intent_index.py` does cover the real index, so this is a
documentation/naming issue rather than a coverage hole.

**Fix:** Rename the assertion (`test_the_money_hold_is_named_in_the_source`) so the green does not
read as "the hold exists", or import the index name check from the model test.

### IN-02: Migration `0021` tie-break has dialect-divergent NULL ordering

**File:** `alembic/versions/0021_payments_open_intent_index.py:158`

**Issue:** `ORDER BY keeper.created_at DESC, keeper.id DESC` sorts NULLs first on PostgreSQL and
last on SQLite. A row with `created_at IS NULL` would be *kept* on production and *expired* in the
round-trip test. `Payment.created_at` is `NOT NULL` with a server default, so this is unreachable
today — but the revision reasons carefully about exactly this class of divergence elsewhere
(lines 139-147) and this instance is not named.

**Fix:** Make the intent explicit and dialect-independent, e.g. `ORDER BY keeper.created_at IS NULL,
keeper.created_at DESC, keeper.id DESC`, or name the assumption in the docstring.

### IN-03: `respond()` raises after the handler's side effects when the fragment is not HTML

**File:** `app/pages/htmx.py:364-367` with `_glue_notice` at `251-283`

**Issue:** The fragment is awaited (and therefore the handler's commit has already happened) before
`_glue_notice` validates the content type. A non-HTML fragment turns a *successful* mutation into a
500 for the user. The "loud refusal" rationale is sound for the developer, but the failure mode
should be named: the write is not rolled back.

**Fix:** Validate the fragment's declared content type before invoking it where possible, or state
in the docstring that the raise happens after the write and the user sees a 500 on a completed
action.

### IN-04: The htmx failure banners are never re-hidden

**File:** `app/templates/includes/htmx_error_banner.html:82-90`

**Issue:** `removeAttribute('hidden')` is one-way. After a single transient failure the red banner
stays on the page for the rest of the session, including after every subsequent successful action —
so "красное на экране" stops correlating with "что-то сломано", which is the exact
desensitisation the file's own comment warns about for the 422 case. The decision is recorded as an
accepted plan assumption, so this is a reminder rather than a defect.

**Fix:** Re-hide both banners on `htmx:afterRequest` with a successful `xhr.status`, or record the
follow-up explicitly in the phase backlog.

---

_Reviewed: 2026-08-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

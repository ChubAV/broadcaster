---
phase: 05-tarify
reviewed: 2026-08-16T05:35:12Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - alembic/versions/0017_payment_kind_and_plan.py
  - app/application/analytics/send_analytics.py
  - app/application/billing/__init__.py
  - app/application/billing/plan_usage.py
  - app/application/billing/subscription_period.py
  - app/config.py
  - app/constants.py
  - app/models/payment.py
  - app/pages/billing.py
  - app/pages/common.py
  - app/pages/history.py
  - app/routes/billing.py
  - app/services/billing_service.py
  - app/services/payment_service.py
  - app/static/css/app.css
  - app/templates/base.html
  - app/templates/billing/balance.html
  - app/templates/billing/includes/payment_row.html
  - app/templates/billing/includes/plan_card.html
  - app/templates/billing/includes/usage_meters.html
  - tests/test_application/test_plan_usage.py
  - tests/test_application/test_subscription_period.py
  - tests/test_migrations/test_0017_payment_kind_and_plan.py
  - tests/test_pages/test_billing_section.py
  - tests/test_pages/test_billing_subscription.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_routes/test_billing.py
  - tests/test_routes/test_billing_webhook_source.py
  - tests/test_services/test_billing_service.py
  - tests/test_services/test_payment_service.py
findings:
  critical: 2
  warning: 10
  info: 6
  total: 18
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-08-16T05:35:12Z
**Depth:** standard
**Files Reviewed:** 31
**Status:** issues_found

## Summary

Phase 05 adds YooKassa subscriptions, plan-usage metering, and the `/billing`
section. The suite is green (292 passed) and the documented design decisions
(rightmost source-IP read, `webhook_event` instead of `event=`, no payment id in
response bodies, purchase price read from config not from the form, ownership as
a query predicate) are all implemented as described and covered by tests.

The defects below are the places where the *implementation* and the *deployment
artifacts* disagree with the documented intent, or where a documented invariant
holds only in the single-request case:

1. The webhook source-IP guard is written correctly but is **inert in the
   shipped production configuration**: `yookassa_webhook_client_ip_header`
   defaults to empty, no compose file / `.env.example` / README sets it, and the
   prod `web` service runs uvicorn with `--forwarded-allow-ips=*`. In that
   combination `request.client.host` *is* the attacker-controlled leftmost
   `X-Forwarded-For` element — exactly the leftmost read the module docstring
   forbids.
2. The double-credit protection (`TERMINAL_STATUSES` check) is a check-then-act
   with no row lock and no unique constraint, so it protects against *sequential*
   redelivery only. `tests/test_services/test_payment_service.py` tests exactly
   the sequential case.

Everything else is warning-tier: a proven `format_amount` crash on `NaN`/
`Infinity`, undefined plan-switch semantics that destroy a paid remainder on
downgrade, and a migration that silently drops `ON DELETE CASCADE` on SQLite
while its round-trip test uses a fixture schema that omits the constraint.

## Structural Findings (fallow)

No `<structural_findings>` block was supplied with this review request; no
structural pre-pass results are incorporated below. All findings are narrative.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Webhook source-IP guard is bypassable in the shipped production configuration

**Severity:** BLOCKER (Critical)
**File:** `app/routes/billing.py:76-83`, `app/config.py:94`, `docker-compose.prod.yml:78`, `nginx/nginx.conf.template:40`

**Issue:**
`_webhook_client_ip` has two paths. The configured-header path reads the
rightmost element and is correct. The **fallback path is the one production
actually takes**, and it is forgeable:

```python
header_name = settings.yookassa_webhook_client_ip_header   # default: ""
if header_name:
    ...                       # rightmost read — correct
client = request.client       # <-- production path
return client.host if client else None
```

Chain of evidence, all verified in this repository:

- `app/config.py:94` — `yookassa_webhook_client_ip_header: str = ""` (default empty).
- No deployable artifact sets it. `grep -rn "yookassa_webhook" --include="*.yml"
  --include=".env.example" --include="*.md"` over the repo (excluding
  `.planning/`) returns **nothing**. `docker-compose.prod.yml` enumerates its
  env keys explicitly and does not include it.
- `docker-compose.prod.yml:78` — `uvicorn main:app ... --forwarded-allow-ips=*`.
- `.venv/.../uvicorn/middleware/proxy_headers.py` — with `always_trust`,
  `get_trusted_client_host()` returns `x_forwarded_for_hosts[0]`, i.e. the
  **leftmost** element, and `ProxyHeadersMiddleware` writes it into
  `scope["client"]`, which is what `request.client.host` returns.
- `nginx/nginx.conf.template:40` — `proxy_set_header X-Forwarded-For
  $proxy_add_x_forwarded_for;` appends the real peer on the **right**, so the
  leftmost element is whatever the client sent.

Net effect: `curl -H 'X-Forwarded-For: 77.75.156.11' -d '{"event":
"payment.succeeded","object":{"id":"<id>"}}' https://<host>/api/billing/webhook`
passes `_is_trusted_source()` and grants a paid resource. The victim payment id
is not the secret the code assumes it is either: the browser is redirected to
YooKassa's `confirmation_url`, which carries the payment id as a query parameter,
so a buyer can read their own pending payment id out of the URL bar and then
confirm it for free.

`tests/test_routes/test_billing_webhook_source.py:154-169` tests the empty-header
path but only asserts that the *test transport's* peer address is untrusted — it
cannot see the proxy-header rewrite, so the suite is green while production is
open.

**Fix:** make the guard refuse to fall back to `request.client` whenever the app
may be behind a trusted-everything proxy, and set the header in the deployment
artifacts.

```python
# app/routes/billing.py
def _webhook_client_ip(request: Request, settings: Settings) -> str | None:
    header_name = settings.yookassa_webhook_client_ip_header
    if not header_name:
        # НЕТ НАСТРОЕННОГО ЗАГОЛОВКА = НЕТ ДОВЕРЕННОГО ИСТОЧНИКА АДРЕСА.
        # За --forwarded-allow-ips=* request.client.host — это ЛЕВЫЙ элемент
        # X-Forwarded-For, то есть значение, которое присылает сам клиент.
        logger.error("webhook_ip_header_not_configured")
        return None
    raw = request.headers.get(header_name)
    if not raw:
        return None
    return raw.split(",")[-1].strip() or None
```

```yaml
# docker-compose.prod.yml, x-app-base environment:
  YOOKASSA_WEBHOOK_CLIENT_IP_HEADER: ${YOOKASSA_WEBHOOK_CLIENT_IP_HEADER:-X-Real-IP}
```

Add a regression test that the empty-header configuration cannot be satisfied by
any request header, and document the variable in `.env.example`.

---

### CR-02: Webhook double-credit protection is a check-then-act with no lock — concurrent redelivery double-credits and double-extends

**Severity:** BLOCKER (Critical)
**File:** `app/services/payment_service.py:171-181`, `app/services/payment_service.py:227-234`, `app/services/payment_service.py:265-290`, `app/services/billing_service.py:75-77`

**Issue:**
`handle_webhook` reads the payment row, checks `db_payment.status in
TERMINAL_STATUSES`, and only later commits the new status. Nothing serialises
two concurrent deliveries of the same notification:

```python
result = await db.execute(
    select(Payment).where(Payment.yookassa_payment_id == yookassa_id)
)          # <-- plain SELECT, no FOR UPDATE
db_payment = result.scalar_one_or_none()
if db_payment.status in TERMINAL_STATUSES:   # <-- check
    return True
...
db_payment.status = STATUS_SUCCEEDED         # <-- act, much later
```

Under PostgreSQL READ COMMITTED (the default), two overlapping requests both
observe `pending` and both proceed. Consequences:

- `add_messages` does a Python-side read-modify-write
  (`bal.balance += amount` at `billing_service.py:76`) on two separately loaded
  `MessageBalance` instances, so the credit is applied twice **and** one of the
  two writes is lost — the balance ends up wrong in a way that is not even
  `2 × amount`.
- `_extend_subscription` runs its "is there an active subscription?" SELECT
  twice; if there is none, both branches `db.add(Subscription(...))` and the
  user ends up with **two** subscription rows (`subscriptions` has no unique
  index on `user_id` — `app/models/subscription.py:12-14`). If there is one, the
  expiry is advanced two months for one month's payment.

This is directly exploitable in combination with CR-01: an attacker who can
reach the endpoint can fire N concurrent identical POSTs for a known payment id.
Even without CR-01, YooKassa redelivers notifications, and the docstring's claim
that this check is "единственное место, где живёт защита от двойного
начисления" is only true single-threaded — which is exactly what
`test_handle_webhook_idempotent` and
`test_a_repeated_subscription_webhook_moves_the_expiry_once` exercise.

**Fix:** take a row lock on the payment before the terminal-status check, and
make the balance update a SQL-side increment.

```python
# app/services/payment_service.py
result = await db.execute(
    select(Payment)
    .where(Payment.yookassa_payment_id == yookassa_id)
    .with_for_update()          # сериализует конкурирующие доставки
)
```

```python
# app/services/billing_service.py — вместо bal.balance += amount
await db.execute(
    update(MessageBalance)
    .where(MessageBalance.user_id == user_id)
    .values(balance=MessageBalance.balance + amount)
    .returning(MessageBalance.balance)
)
```

Also add `UniqueConstraint("user_id")` (or a partial unique index on
`user_id WHERE is_active`) to `subscriptions` in a follow-up revision so the
duplicate-row outcome is impossible rather than merely unlikely.

## Warnings

### WR-01: `format_amount` raises on `NaN` / `Infinity`, 500-ing the whole billing page

**Severity:** WARNING
**File:** `app/pages/common.py:270-281`

**Issue:** The function documents "непригодное значение возвращается КАК ЕСТЬ",
but the guard is in the wrong place. `Decimal("NaN")` and `Decimal("Infinity")`
parse successfully, then escape the `try`:

```
$ uv run python -c "from app.pages.common import format_amount; format_amount('NaN')"
decimal.InvalidOperation: [<class 'decimal.InvalidOperation'>]      # from f"{abs(amount):.2f}"
$ ... format_amount('Infinity')
ValueError: invalid literal for int() with base 10: 'Infinity'      # from int(whole)
```

(Verified by execution.) `format_amount` is a Jinja global called for every plan
card (`plan_card.html:49`), every package tile (`balance.html:148`) and every
payment row (`payment_row.html:57`), so one bad `price` in `PLAN_LIMITS` /
`MESSAGE_PACKAGES` — or one bad `payments.amount_value` — takes down `/billing`
with a 500 instead of showing the odd string.

**Fix:** reject non-finite values inside the guarded region.

```python
    try:
        amount = Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        return str(value)
    if not amount.is_finite():
        return str(value)
```

---

### WR-02: Plan switching destroys the paid remainder on downgrade (and gifts it on upgrade)

**Severity:** WARNING
**File:** `app/services/payment_service.py:277-281`

**Issue:**

```python
if subscription is not None:
    subscription.expires_at = next_expiry(subscription.expires_at, now)
    if db_payment.plan:
        subscription.plan = db_payment.plan
    return
```

The plan is overwritten unconditionally while the expiry is only pushed one
month from the *existing* expiry. A `pro` subscriber (4900 ₽/mo) with 25 days
left who buys `basic` (1490 ₽) is immediately downgraded to `basic` and keeps
the 25 days — i.e. the 4900 ₽ they already paid for those days is destroyed.
Symmetrically, a `basic` subscriber who buys `pro` gets `pro` limits for the
remaining `basic` days for free. `next_expiry`'s docstring is explicit that the
remainder must not be burned ("Пользователь уже заплатил за неистраченный
остаток"), and this path burns it whenever the plans differ.

No test covers a plan change: `test_payment_service.py` and
`test_billing_subscription.py` only exercise same-plan renewal and first
purchase.

**Fix:** make the semantics explicit. Minimum viable behaviour — a plan change
starts a fresh period from today rather than inheriting the old one, and an
upgrade/downgrade decision is recorded:

```python
if subscription is not None:
    changing_plan = bool(db_payment.plan) and db_payment.plan != subscription.plan
    base = None if changing_plan else subscription.expires_at
    subscription.expires_at = next_expiry(base, now)
    if db_payment.plan:
        subscription.plan = db_payment.plan
    return
```

and add tests for `basic → pro` and `pro → basic` with an unexpired remainder.

---

### WR-03: Revision 0017 silently drops `ON DELETE CASCADE` on SQLite; the round-trip test cannot see it

**Severity:** WARNING
**File:** `alembic/versions/0017_payment_kind_and_plan.py:63-66`, `tests/test_migrations/test_0017_payment_kind_and_plan.py:46-61`

**Issue:** `op.batch_alter_table("payments")` recreates the table on SQLite by
reflection. Reflection does not recover the referential action, so the FK comes
back as `NO ACTION`. Verified by running the real revision against a fixture
that includes the real constraint:

```
before: FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
after : FOREIGN KEY(user_id) REFERENCES users (id)
PRAGMA foreign_key_list(payments) -> (..., 'NO ACTION', 'NO ACTION', 'NONE')
```

The round-trip test cannot catch this because `PAYMENTS_AT_0016` in the fixture
(lines 46-61) is **not** the revision-0016 schema: it omits the
`REFERENCES users(id) ON DELETE CASCADE` that `0009_add_message_balance_and_payment_tables.py:67-73`
actually creates, and it omits the `status` / `amount_currency` server defaults.
The file's own docstring claims round-trip fidelity ("обязаны пережить откат без
потери строк"), so the test is weaker than it advertises. Production is
PostgreSQL, where batch mode degrades to a plain `ALTER ... DROP NOT NULL` and
the FK is untouched — that is why this is a warning and not a blocker — but the
same batch pattern will be copied into the next revision.

**Fix:** give batch mode the real table definition so nothing is inferred, and
fix the fixture:

```python
PAYMENTS = sa.Table(
    "payments", sa.MetaData(),
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.Integer,
              sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    ...  # остальные колонки на момент 0016 + kind/plan
)
with op.batch_alter_table("payments", copy_from=PAYMENTS) as batch_op:
    batch_op.alter_column("messages_count", existing_type=sa.Integer(), nullable=True)
```

and add `REFERENCES users(id) ON DELETE CASCADE` to `PAYMENTS_AT_0016` plus an
assertion on `PRAGMA foreign_key_list(payments)` after upgrade and downgrade.

---

### WR-04: `kind` is passed as a bare string literal by both callers, defeating the constants it was introduced for

**Severity:** WARNING
**File:** `app/pages/billing.py:197`, `app/pages/billing.py:259`

**Issue:** `payment_service` defines `KIND_PACKAGE` / `KIND_SUBSCRIPTION`
(lines 21-22) precisely so the writer and the webhook branch cannot drift, and
`create_payment` makes `kind` keyword-only so "необновлённый вызывающий обязан
упасть громко". Both call sites then hardcode the value:

```python
kind="subscription",   # app/pages/billing.py:197
kind="package",        # app/pages/billing.py:259
```

A typo here does not fail loudly — it produces a row that
`db_payment.kind == KIND_SUBSCRIPTION` evaluates false for, so the webhook takes
the package branch and calls `add_messages(db, user_id, None, ...)`, which does
`bal.balance += None` → `TypeError` → the route's `except Exception` returns
500 → YooKassa retries the same notification until it gives up. The payment stays
`pending` forever with the money taken.

**Fix:** import and use the constants, and defend the branch.

```python
from app.services.payment_service import KIND_PACKAGE, KIND_SUBSCRIPTION, create_payment
...
kind=KIND_SUBSCRIPTION,
```

```python
# payment_service.handle_webhook, package branch
if db_payment.messages_count is None:
    logger.error("payment_package_without_count", yookassa_id=yookassa_id,
                 kind=db_payment.kind)
    return False
```

---

### WR-05: Blocking YooKassa SDK call inside an async handler, with no timeout and no error handling

**Severity:** WARNING
**File:** `app/services/payment_service.py:95-107`, `app/pages/billing.py:193-202`, `app/pages/billing.py:256-263`

**Issue:** `YooPayment.create(...)` is the synchronous `requests`-based SDK call
executed directly in the event loop of an `async def` handler. Until YooKassa
answers, the worker serves no other request — and there is no timeout argument,
so a hung TLS connection stalls the whole process, not just this user. There is
also no `try/except`: any SDK error (network, 4xx from YooKassa, malformed
`price` in config) propagates out of a *page* handler and gives the user a raw
500 instead of a return to `/billing` with a notice, which is the pattern every
other rejection in these two handlers uses.

**Fix:**

```python
try:
    payment = await asyncio.to_thread(YooPayment.create, {...}, idempotency_key)
except Exception as exc:                      # SDK бросает своё дерево исключений
    logger.error("payment_create_failed", user_id=user_id, kind=kind, error=str(exc))
    raise PaymentCreationError from exc
```

and in both page handlers, catch `PaymentCreationError` and
`return RedirectResponse(url="/billing?error=payment", status_code=302)`.

---

### WR-06: An unprocessed webhook answers HTTP 200, so a payment YooKassa accepted is never retried and raises no alarm

**Severity:** WARNING
**File:** `app/routes/billing.py:171-172`, `app/services/payment_service.py:162-177`

**Issue:** `handle_webhook` returns `False` for an unknown event, a body without
`object.id`, and — most importantly — **a payment id that is not in our
database**; the route turns all three into `200 {"ok": false}`. YooKassa treats
2xx as delivered and stops retrying. The "payment id not in our database" case
is reachable whenever `create_payment` created the payment at YooKassa but the
subsequent `db.commit()` (line 121) failed: the customer can still pay, and the
one notification we would have got is acknowledged and dropped, with only a
`logger.warning` that nothing watches.

**Fix:** distinguish "not ours / not interesting" (200, correct) from "ours but
we could not process it" (5xx, so YooKassa retries), and alert on the unknown-id
case:

```python
if db_payment is None:
    logger.error("webhook_payment_not_found", yookassa_id=yookassa_id)
    # НЕ 200: платёж мог быть заведён нами и потерян на коммите.
    raise HTTPException(status_code=503, detail="Unknown payment")
```

At minimum, raise the unknown-id log from `warning` to `error` and add a metric
so an accepted-but-uncredited payment is visible.

---

### WR-07: "первый платёж" is mislabelled once the payment list hits its cap

**Severity:** WARNING
**File:** `app/templates/billing/balance.html:179-184`, `app/templates/billing/includes/payment_row.html:43-45`

**Issue:** `first_payment_at` is built by iterating the **already capped** list
(`get_payment_history(..., limit=PAYMENT_LIST_CAP)`), so "самая ранняя строка
плана" is only the true first payment when nothing was truncated. When
`payments_truncated` is true — the case the phase went out of its way to detect
and announce — the oldest *displayed* renewal is labelled «первый платёж». The
screen therefore prints a factual claim about payment history that is false in
exactly the situation the cap warning is telling the user about.

Secondary: the match is `first_payment_at.get(pay.plan) == pay.created_at`, so
two payments for one plan sharing a `created_at` are both labelled first.

**Fix:** suppress the label when the list is known to be incomplete.

```jinja
{{ payment_row(pay, user, PAY_COLS, PAY_LABELS,
               {} if payments_truncated else first_payment_at) }}
```

or compute the true first-payment date server-side with a
`min(created_at) GROUP BY plan` query.

---

### WR-08: `/api/billing/transactions` accepts unvalidated `limit` / `offset`

**Severity:** WARNING
**File:** `app/routes/billing.py:30-38`

**Issue:** (Pre-existing in a file this phase edits, and now the only remaining
JSON write-adjacent surface.) `limit` and `offset` go straight into
`.limit()` / `.offset()`:

- `?limit=-1` renders `LIMIT -1`. PostgreSQL raises `ERROR: LIMIT must not be
  negative`, i.e. an authenticated user can 500 the endpoint at will.
- `?limit=100000000` is unbounded — the whole transaction journal is
  materialised into dicts in memory.
- `?offset=-1` similarly errors on PostgreSQL.

**Fix:**

```python
from fastapi import Query

async def get_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ...
```

---

### WR-09: The webhook grants paid resources purely on the notification body; the payment is never re-fetched from YooKassa

**Severity:** WARNING
**File:** `app/services/payment_service.py:162-234`

**Issue:** The only inputs to "grant a subscription month / credit N messages"
are (a) the `event` string from the request body and (b) our own DB row. The
notification's `object.status` and `object.amount` are never read, and
`YooPayment.find_one(yookassa_id)` is never called. Since the SDK offers no
signature verification (correctly noted in the docstring), the source-IP check is
the *entire* authentication — and CR-01 shows that check currently fails open in
production. Re-fetching the payment over the authenticated API is the standard
YooKassa recommendation and turns a forged body into a no-op even if the IP guard
is bypassed.

**Fix:** confirm out-of-band before granting anything.

```python
_configure_yookassa()
remote = await asyncio.to_thread(YooPayment.find_one, yookassa_id)
if remote.status != "succeeded" or remote.amount.value != db_payment.amount_value:
    logger.error("webhook_payment_mismatch", yookassa_id=yookassa_id,
                 remote_status=remote.status)
    return False
```

---

### WR-10: Config-driven `KeyError` / `TypeError` paths surface as 500s

**Severity:** WARNING
**File:** `app/pages/billing.py:198`, `app/pages/billing.py:260-262`, `app/application/billing/plan_usage.py:116-118`

**Issue:** The phase is consistent about "опечатка в окружении обязана стоить
ненарисованной шкалы, а не пятисотки" — `plan_axes` and `billing_page` both use
`.get()` with defaults for that reason. The purchase paths do not:

- `selected["price"]` (line 198) — `KeyError` → 500 if a plan record has no price.
- `package["name"] / ["count"] / ["price"]` (lines 260-262) — same.
- `axis_percent`: `limit is None or limit <= 0` then `used * 100 / limit`. A
  JSON string limit (`"ads": "3"`) passes `<= 0` comparison with `TypeError`
  ("'<=' not supported between 'str' and 'int'") → 500 on `/billing`.

**Fix:** validate the parsed config once instead of trusting shape at every use
site — e.g. a `PlanRecord` / `PackageRecord` pydantic model on `Settings` with
`parsed_plan_limits` returning typed objects, so a malformed `PLAN_LIMITS` fails
at startup rather than on a customer's checkout click. Short of that, use
`.get()` with an explicit redirect back to `/billing` on missing keys, and
coerce `limit` with `isinstance(limit, int)` in `axis_percent`.

## Info

### IN-01: `add_messages(type=...)` shadows the `type` builtin

**Severity:** Info
**File:** `app/services/billing_service.py:70`, called from `app/services/payment_service.py:231`
**Issue:** Parameter named `type` shadows the builtin inside the function body.
**Fix:** rename to `tx_type` (the column is `BalanceTransaction.type`, so keep
the keyword at the call site via an explicit mapping).

---

### IN-02: Revision 0017 leaves `server_default='package'` permanently on `payments.kind`

**Severity:** Info
**File:** `alembic/versions/0017_payment_kind_and_plan.py:50-58`
**Issue:** The server default is the backfill mechanism (correctly explained),
but it is never dropped, so any future INSERT that forgets `kind` silently
becomes a package payment — the exact ambiguity the column was added to remove,
and the input to the WR-04 failure mode.
**Fix:** add `op.alter_column("payments", "kind", server_default=None)` after the
backfill, as is conventional for `ADD COLUMN NOT NULL DEFAULT` backfills.

---

### IN-03: `/api/billing/packages` advertises the catalogue even when payments are disabled

**Severity:** Info
**File:** `app/routes/billing.py:25-27`
**Issue:** `billing_page` passes `packages = [] if not yookassa_enabled`
(`app/pages/billing.py:137-139`) and the template shows "доступно через
администратора"; the JSON route ignores the flag entirely, so the two surfaces
disagree about whether packages are purchasable.
**Fix:** `return {"packages": settings.parsed_message_packages if settings.yookassa_enabled else []}`.

---

### IN-04: `plan_axes` is handed the whole plan record, not a limits mapping

**Severity:** Info
**File:** `app/pages/billing.py:91-93`, `app/application/billing/plan_usage.py:121-128`
**Issue:** `limits` is documented as "ключи осей, значения — целое либо None",
but the caller passes the full config record including `id`, `name` and `price`.
It works because only four keys are read, but the type hint
(`Mapping[str, int | None]`) is a lie about `price: str`. Related: an unknown
plan id yields `current_plan = {}`, so all four axes render `∞` — a user whose
plan was removed from `PLAN_LIMITS` is told they have no limits at all.
**Fix:** pass `{k: current_plan.get(k) for k in AXIS_ORDER}` and log once when
`current_plan_id` is not in the config.

---

### IN-05: A fresh idempotency key per call means a double-clicked form creates two YooKassa payments

**Severity:** Info
**File:** `app/services/payment_service.py:94`
**Issue:** `idempotency_key = str(uuid.uuid4())` is generated per invocation, so
the key provides no idempotency across retries of the *same user intent* — two
form submissions create two YooKassa payments and two `pending` rows in the
history. Only one will be paid, but the journal shows two "в обработке" lines.
**Fix:** derive the key from a stable intent (e.g. `f"{user_id}:{kind}:{plan or package_index}:{minute_bucket}"`),
or add a `data-plan-cta` submit-once guard as progressive enhancement.

---

### IN-06: The expired-subscription "Продлить" button can render for a plan the handler always rejects

**Severity:** Info
**File:** `app/templates/billing/balance.html:95-100`
**Issue:** The button is gated on `payments_enabled and current_in_config`, and
`free` *is* in the config — so a subscription row with `plan='free'` and a past
`expires_at` renders a "Продлить" button that posts `plan=free`, which
`subscribe_to_plan` rejects at `app/pages/billing.py:190` with a silent redirect
back to the same page. A control that does nothing reads as a broken payment
flow.
**Fix:** add `and subscription.plan != 'free'` to the condition, mirroring
`FREE_PLAN_ID` on the handler side.

---

_Reviewed: 2026-08-16T05:35:12Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

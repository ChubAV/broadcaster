---
phase: 05-tarify
reviewed: 2026-08-16T00:00:00Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - alembic/versions/0017_payment_kind_and_plan.py
  - alembic/versions/0018_subscriptions_unique_user.py
  - app/application/analytics/send_analytics.py
  - app/application/billing/__init__.py
  - app/application/billing/plan_usage.py
  - app/application/billing/subscription_period.py
  - app/config.py
  - app/constants.py
  - app/models/payment.py
  - app/models/subscription.py
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
  - app/templates/billing/plans.html
  - docker-compose.prod.yml
  - tests/test_application/test_plan_usage.py
  - tests/test_application/test_subscription_period.py
  - tests/test_migrations/test_0017_payment_kind_and_plan.py
  - tests/test_migrations/test_0018_subscriptions_unique_user.py
  - tests/test_pages/test_billing_payment_errors.py
  - tests/test_pages/test_billing_section.py
  - tests/test_pages/test_billing_subscription.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_routes/test_billing.py
  - tests/test_routes/test_billing_webhook_proxy_headers.py
  - tests/test_routes/test_billing_webhook_source.py
  - tests/test_services/test_billing_service.py
  - tests/test_services/test_payment_concurrency.py
  - tests/test_services/test_payment_service.py
findings:
  critical: 2
  warning: 9
  info: 7
  total: 18
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-08-16
**Depth:** standard
**Files Reviewed:** 38
**Status:** issues_found

## Summary

The webhook source guard, the claim-and-credit atomicity, and the `0018` backfill
hold up under adversarial reading. The rightmost-element parse is correct for the
shipped `X-Real-IP` header; the CAS claim is genuinely a compare-and-swap and works
on both dialects; the `0018` correlated-subquery backfill converges to the correct
keeper regardless of row order on both PostgreSQL and SQLite (`expires_at` and
`is_active` are `NOT NULL` per `0001`, so the NULL-ordering divergence between the
dialects cannot bite). 307 targeted tests pass.

Two blockers survive that review, and both are on the money path:

1. **`_apply_extension` overwrites the plan unconditionally.** The `upgrade-only`
   rule is enforced only at the *intent* stage (form guard) and nowhere at the
   *application* stage. Two ordinary pending payments — or one out-of-order webhook
   delivery — silently strip a user of a tier they paid for. Reproduced with a
   failing test against the real code path (see CR-01).
2. **`YooPayment.create()` is a synchronous, timeout-less HTTP call on the event
   loop** of a single-worker uvicorn. A blackholed YooKassa connection hangs the
   whole application, including `/health`.

The narrative below builds on those; nine warnings and seven info items follow.
Known debt WR-10 (string limit crashing `axis_percent`) was verified as reported
and is not re-listed, though WR-07 below is its unreported sibling one level up.

No structural pre-pass was supplied with this review, so there is no
`Structural Findings (fallow)` section.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A confirmed lower-tier payment silently downgrades an active higher tier

**File:** `app/services/payment_service.py:504-509`
**Severity:** BLOCKER

**Issue:**

```python
def _apply_extension(subscription, db_payment, now) -> None:
    subscription.expires_at = next_expiry(subscription.expires_at, now)
    if db_payment.plan:
        subscription.plan = db_payment.plan     # unconditional overwrite
```

`PLAN_ORDER` exists specifically to rank plans, and `app/constants.py:48-70` states
the owner decision that a downgrade "не предлагается и не принимается". That rule is
enforced in exactly two places — `plan_card.html` (CTA state) and the
`POST /billing/subscribe` guard — both of which act on *intent*. Nothing consults
`PLAN_ORDER` when the money actually lands. `_apply_extension` will lower the plan
on any confirmed payment.

The `_extend_subscription` docstring (lines 447-452) defends this as "ГАРД СТОИТ НА
ВХОДЕ", arguing that refusing a paid payment would be worse. That argument justifies
*not refusing the payment*; it does not justify *lowering the tier*. Extending the
period while keeping the higher plan satisfies both constraints, and is the only
behaviour consistent with the stated rule.

Two reachable paths, neither requiring an attacker:

*Path A — two pending payments (ordinary user indecision).* User on `free` clicks
"Перейти на Pro" → payment P1 created, redirected to YooKassa, does not pay yet.
Goes back, clicks "Перейти на Basic" → the subscribe guard sees no *live*
subscription (none exists), so it allows → P2 created. User pays both.
P1 lands: plan = `pro`. P2 lands: plan = `basic`. **The user paid 4 900 ₽ + 1 490 ₽
and ends on Basic.**

*Path B — out-of-order webhook delivery.* YooKassa delivery order is not guaranteed
and retries reorder. A user who correctly upgrades Basic → Pro, whose Basic webhook
is delayed past the Pro one, ends on Basic.

Reproduced against the real code path (test written, run, then removed — review is
read-only):

```
after pro  : pro   2026-09-16 ...
after basic: basic 2026-10-16 ...
AssertionError: PLAN WAS SILENTLY DOWNGRADED to 'basic' after paying for both
```

Note the aggravating detail: `expires_at` *is* advanced twice, so the payment is
visibly honoured in the period column while the tier is silently lost. There is no
log line recording the demotion.

**Fix:** consult the same rank table the form guard uses, and never lower the plan
from the webhook path.

```python
# app/services/payment_service.py
from app.constants import PLAN_ORDER

_PLAN_RANK = {plan: index for index, plan in enumerate(PLAN_ORDER)}


def _apply_extension(subscription, db_payment, now) -> None:
    subscription.expires_at = next_expiry(subscription.expires_at, now)
    if not db_payment.plan:
        return
    # ПЛАН ТОЛЬКО ПОВЫШАЕТСЯ. Подтверждённый платёж исполняется ЛЮБОЙ (срок
    # двинут выше), но тариф, за который уже заплачено, он не отнимает:
    # правило `upgrade-only` (C2/WR-02) обязано держаться и здесь, иначе оно
    # существует только на входе, а деньги приходят не через вход.
    paid = _PLAN_RANK.get(db_payment.plan)
    held = _PLAN_RANK.get(subscription.plan)
    if paid is None or held is None or paid >= held:
        subscription.plan = db_payment.plan
        return
    logger.info(
        "subscription_plan_kept_higher",
        user_id=db_payment.user_id,
        yookassa_id=db_payment.yookassa_payment_id,
        paid_plan=db_payment.plan,
        held_plan=subscription.plan,
    )
```

Add a regression test asserting that `pro` → `basic` (both confirmed) leaves
`plan == "pro"` with the period advanced twice.

---

### CR-02: Synchronous, timeout-less YooKassa call blocks the single-worker event loop

**File:** `app/services/payment_service.py:128-141`; `docker-compose.prod.yml:87`
**Severity:** BLOCKER

**Issue:** `create_payment` is `async def`, but line 129 calls `YooPayment.create(...)`
directly. That is a blocking `requests` call executed on the ASGI event loop. Two
compounding facts make it a whole-application hang rather than a slow request:

1. **The SDK sets no timeout.** `yookassa/client.py:83-92` calls
   `session.request(method, url, params=…, headers=…, json=…, verify=…)` with no
   `timeout=` argument. `requests` then blocks indefinitely on a blackholed TCP
   connection. The `Retry(total=self.max_attempts, backoff_factor=self.timeout/1000)`
   mounted at `client.py:97-102` multiplies the wait rather than bounding it.
2. **Prod runs one worker with one loop.**
   `command: uv run uvicorn main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips=*`
   — no `--workers`. There is also no `restart:` policy on the `web` service (nginx,
   certbot and flower have one; `web` does not), so a wedged process is not recycled.

Consequence: one user pressing "Оплатить"/"Перейти на …" while YooKassa is
unreachable stalls *every* route on the process — all 26 pages, the compose
healthcheck at `/health`, and `POST /api/billing/webhook` itself. Incoming webhooks
for already-paid subscriptions cannot be processed while the loop is parked, so
money is taken and nothing is credited until the socket eventually gives up.

This also contradicts the project's own stated boundary — `app/pages/common.py:406-410`
and `app/application/analytics/send_analytics.py:20-22` both explicitly forbid
synchronous blocking calls on the render path for exactly this reason.

**Fix:** bound the call and get it off the loop.

```python
# app/services/payment_service.py
import asyncio
from yookassa import Configuration


def _configure_yookassa():
    settings = get_settings()
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key
    # Таймаут ОБЯЗАТЕЛЕН: SDK зовёт requests без него вовсе
    # (yookassa/client.py:83-92), а без границы ожидания зависшее соединение
    # держит цикл событий бесконечно.
    Configuration.timeout = settings.yookassa_timeout_ms


# ... в create_payment:
    try:
        # ВЫЗОВ УХОДИТ В ПОТОК. `YooPayment.create` — синхронный requests-вызов,
        # а обработчик живёт в цикле событий одного воркера: блокировка здесь
        # останавливает ВЕСЬ сайт, включая приём вебхуков и healthcheck.
        payment = await asyncio.to_thread(
            YooPayment.create,
            {...},
            idempotency_key,
        )
    except Exception as exc:
        ...
```

Add `yookassa_timeout_ms: int = 10_000` to `Settings`. Consider `--workers 2+` in
`docker-compose.prod.yml` and `restart: unless-stopped` on `web` as defence in depth.

## Warnings

### WR-01: `reset_free_monthly` keeps the exact lost-update pattern `add_messages` was fixed to remove

**File:** `app/services/billing_service.py:121-145` (line 133)
**Severity:** WARNING

`add_messages` was hardened this phase (line 94-101) so the increment is computed
DB-side: `values(balance=MessageBalance.balance + amount)`. Its sibling in the same
file was left as a Python read-modify-write:

```python
bal = await get_or_create_balance(db, user_id)   # reads balance
...
bal.balance += free_limit                        # computes in Python
await db.flush()                                 # writes an absolute value
```

`reset_all_free_monthly` (line 148-160) loops over **every** user inside one
transaction and commits once (`app/worker/tasks.py:938-942`). Under READ COMMITTED,
any purchase webhook that commits between the read and the flush has its credit
overwritten by the absolute write. The docstring on `add_messages` calls the
eliminated race "недостижимость, а не малая вероятность" — that claim is only true
for one of the two crediting paths in the file.

**Fix:** same shape as `add_messages`.

```python
result = await db.execute(
    update(MessageBalance)
    .where(MessageBalance.user_id == user_id)
    .values(balance=MessageBalance.balance + free_limit,
            free_balance_reset_at=now)
    .returning(MessageBalance.balance)
    .execution_options(synchronize_session=False)
)
new_balance = result.scalar_one()
set_committed_value(bal, "balance", new_balance)
set_committed_value(bal, "free_balance_reset_at", now)
```

---

### WR-02: The webhook guard is re-openable by a single unvalidated env var, and reports itself as enabled while doing so

**File:** `app/config.py:102-108`; `app/routes/billing.py:100-103`
**Severity:** WARNING

`app/config.py:102-107` states the constraint as "⚠️ ЗАПРЕТ, А НЕ РЕКОМЕНДАЦИЯ" —
but nothing enforces it. `_webhook_client_ip` accepts *any* header name:

```python
header_name = settings.yookassa_webhook_client_ip_header
...
raw = request.headers.get(header_name)
```

Set `YOOKASSA_WEBHOOK_CLIENT_IP_HEADER=X-Client-IP` (or `True-Client-IP`, or
`CF-Connecting-IP` — any header the project's nginx does not touch) and the guard
becomes a no-op that an attacker satisfies with one request header:

```
POST /api/billing/webhook
X-Client-IP: 77.75.156.11
{"event":"payment.succeeded","object":{"id":"<known payment id>"}}
```

`yookassa_webhook_verify_ip` remains `True` throughout, so every log line, every
health signal and every operator dashboard reports the guard as *on*. This is a
strictly worse failure mode than the kill switch, which at least names itself.

The shipped default (`X-Real-IP`) is safe, is pinned in `docker-compose.prod.yml:27`,
and is asserted by `test_the_shipped_default_header_name_is_x_real_ip` — so this is
a hardening gap, not an active vulnerability. But the phase context asks explicitly
whether the guard can be re-opened by configuration, and the answer is yes, silently.

**Fix:** validate the header name against the set the project's own proxy
overwrites, and fail loudly at construction rather than silently at request time.

```python
# app/config.py
from pydantic import field_validator

# Заголовки, которые nginx проекта ПЕРЕЗАПИСЫВАЕТ (`$remote_addr` на каждом
# location). Заголовок, который прокси лишь ДОПИСЫВАЕТ либо не трогает вовсе,
# подконтролен клиенту, и гард на нём — декорация, отчитывающаяся как защита.
WEBHOOK_IP_HEADERS_OVERWRITTEN_BY_PROXY = frozenset({"", "x-real-ip"})

@field_validator("yookassa_webhook_client_ip_header")
@classmethod
def _only_proxy_owned_headers(cls, value: str) -> str:
    if value.strip().lower() not in WEBHOOK_IP_HEADERS_OVERWRITTEN_BY_PROXY:
        raise ValueError(
            f"YOOKASSA_WEBHOOK_CLIENT_IP_HEADER={value!r} не перезаписывается "
            "прокси проекта: гард стал бы декоративным. Допустимо: X-Real-IP "
            "или пусто (= отказ каждому уведомлению)."
        )
    return value
```

---

### WR-03: The kill switch bypasses the only authentication on a money-crediting endpoint and logs nothing

**File:** `app/routes/billing.py:179-185`
**Severity:** WARNING

```python
if settings.yookassa_webhook_verify_ip:
    client_ip = _webhook_client_ip(request, settings)
    ...
```

When the switch is off the entire block is skipped in silence. Compare the adjacent
failure mode: an unconfigured header name logs `webhook_ip_header_not_configured` at
`error` level, precisely because "молча остановленный приём неотличим от отсутствия
платежей" (line 91-98). The inverse — a silently *disabled* guard — is the more
dangerous of the two and produces no trace at all.

There is no compensating control behind it. The `yookassa` SDK carries no signature
verification (correctly noted at line 145-150), the JSON purchase route that leaked
`yookassa_payment_id` is gone, and there is no shared secret in the webhook URL. With
`verify_ip=False`, possession of any payment id is sufficient to credit a subscription.

**Fix:** make the bypass loud, so a forgotten `.env` line surfaces in log search.

```python
if settings.yookassa_webhook_verify_ip:
    ...
else:
    # Уровень `error`: выключатель — аварийный, а не режим работы. Пока он
    # выключен, вход не аутентифицирован ничем, и след об этом обязан быть в
    # журнале на КАЖДОМ уведомлении, а не в чьей-то памяти о правке .env.
    logger.error("webhook_ip_verification_disabled")
```

Longer term: register the webhook with YooKassa at a URL carrying a high-entropy
path segment from `Settings`, so the kill switch is not a full bypass.

---

### WR-04: `"object": null` in a webhook body produces a 500 and a YooKassa retry loop

**File:** `app/services/payment_service.py:282`
**Severity:** WARNING

```python
obj = payment_data.get("object", {})
yookassa_id = obj.get("id")
```

`dict.get(key, default)` returns the *stored* value when the key exists — so a body
of `{"event":"payment.succeeded","object":null}` yields `obj is None` and
`None.get("id")` raises `AttributeError`. That propagates to `yookassa_webhook`'s
`except Exception` (line 200-202) and becomes a 500, which YooKassa treats as
"retry later" — exactly the retry-storm outcome the module reasons about avoiding at
lines 355-356 and 116-118. The `if not yookassa_id` guard immediately below never
runs.

**Fix:**

```python
# `or {}`, а не значение по умолчанию: у `get` умолчание не применяется, когда
# ключ ЕСТЬ и несёт null, а тело приезжает из сети и обязано быть подозрительным.
obj = payment_data.get("object") or {}
if not isinstance(obj, dict):
    logger.warning("webhook_object_not_an_object", yookassa_id=None)
    return False
```

---

### WR-05: `GET /api/billing/transactions` passes unvalidated `limit`/`offset` straight to the query

**File:** `app/routes/billing.py:30-38`
**Severity:** WARNING

```python
async def get_transactions(limit: int = 50, offset: int = 0, ...):
    txs = await get_transaction_history(db, user_id, limit=limit, offset=offset)
```

Both values reach `.limit()` / `.offset()` unbounded (`app/services/billing_service.py:179-180`).
On PostgreSQL, `?limit=-1` and `?offset=-1` raise `LIMIT must not be negative` /
`OFFSET must not be negative` → uncaught → 500. `?limit=100000000` is an unbounded
result set materialised into a list of dicts. The rest of the phase is careful about
exactly this class — `PAYMENT_LIST_CAP` (`app/constants.py:73-94`) and
`WORKER_LIST_CAP` (`app/pages/common.py:386-395`) both exist because "число строк
задаёт пользователь". This route has no such cap.

**Fix:**

```python
from fastapi import Query

@router.get("/transactions")
async def get_transactions(
    limit: int = Query(50, ge=1, le=TRANSACTION_API_CAP),
    offset: int = Query(0, ge=0),
    ...
):
```

---

### WR-06: The sidebar widget shows "∞" to users who have zero messages and cannot send at all

**File:** `app/templates/base.html:76`; `app/pages/common.py:534-539`
**Severity:** WARNING

```python
# app/pages/common.py
if is_unlimited:
    limit = 0
else:
    limit = used + remaining      # 0 + 0 == 0 for a fresh user
```

```jinja
{# app/templates/base.html:76 #}
{% if quota.get('limit', 0) > 0 %}{{ used }} / {{ limit }}{% else %}∞{% endif %}
```

`limit == 0` is the encoding for *unlimited*, but it is also what a non-unlimited
user with no balance row produces. Registration does not create a `MessageBalance`
row (no caller of `get_or_create_balance` outside `admin.py` and the send path), and
`free_balance_reset_at` starts `None`, so every newly registered user renders `∞`
until the monthly Celery beat runs.

This phase changed the widget's label from `Тариф {{ plan }}` to `Баланс сообщений`
(base.html:75). Before the change the `∞` plausibly read as "unlimited plan"; now it
reads as "unlimited messages", which is the opposite of the truth —
`check_balance` (`app/services/billing_service.py:32-38`) refuses every send for the
same user. The `/billing` section is honest ("0 сообщений доступно"), so the two
surfaces now contradict each other.

Note the same conflation is called out in `app/config.py:69-73` and
`app/application/billing/plan_usage.py:77-82` as a design rule — "Ноль неотличим от
нулевого лимита" — and the shell quota is the one place that violates it.

**Fix:** carry the unlimited flag explicitly instead of overloading `0`.

```python
# app/pages/common.py — in the returned "quota" dict
"is_unlimited": is_unlimited,
"limit": 0 if is_unlimited else used + remaining,
```

```jinja
{# app/templates/base.html #}
{% if quota.get('is_unlimited') %}∞{% else %}{{ quota.get('used', 0) }} / {{ quota.get('limit', 0) }}{% endif %}
```

---

### WR-07: A malformed `PLAN_LIMITS` / `MESSAGE_PACKAGES` env var 500s the whole section, contradicting the module's stated invariant

**File:** `app/config.py:116-121`; `app/pages/billing.py:187`, `414`
**Severity:** WARNING

```python
@property
def parsed_message_packages(self) -> list[dict]:
    return json.loads(self.message_packages)

@property
def parsed_plan_limits(self) -> list[dict]:
    return json.loads(self.plan_limits)
```

Unguarded. A malformed value raises `json.JSONDecodeError` at
`app/pages/billing.py:187` (`billing_page`), `:326` (`subscribe_to_plan`), `:414`
(`purchase_package`) and `app/routes/billing.py:27` (`list_packages`) — none of which
catch it. The result is a 500 on the tariff section and both payment forms.

`app/pages/billing.py:189-191` and `app/application/billing/plan_usage.py:131-135`
both promise the opposite: "опечатка в ней обязана стоить одной ненарисованной
шкалы, а не пятисотки на странице тарифов". That promise is kept for a *missing key*
and broken for a *malformed document* — and a malformed document is the more likely
operator error, since the value is a single-line JSON string in `.env`.

This is the same family as known debt WR-10 (a string limit value crashing
`axis_percent`) one level up the stack, and is not covered by it.

**Fix:** validate once, at `Settings` construction, so a bad value fails at boot
rather than on the first customer page view.

```python
@field_validator("plan_limits", "message_packages")
@classmethod
def _must_be_a_json_list(cls, value: str) -> str:
    # Разбор ЗДЕСЬ, а не на рендере: опечатка в окружении обязана уронить
    # запуск, где её увидит выкатывающий, а не страницу тарифов, где её
    # увидит покупатель.
    try:
        parsed = json.loads(value)
    except ValueError as exc:
        raise ValueError(f"не разбирается как JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise ValueError("ожидался JSON-список записей")
    return value
```

---

### WR-08: "первый платёж" / "продление" is decided from a truncated, status-blind, in-page map

**File:** `app/templates/billing/balance.html:217-222`; `app/templates/billing/includes/payment_row.html:43-45`
**Severity:** WARNING

```jinja
{%- for pay in payments -%}
  {%- if pay.kind == 'subscription' and pay.plan -%}
    {%- set _ = first_payment_at.update({pay.plan: pay.created_at}) -%}
  {%- endif -%}
{%- endfor -%}
```

Three defects in one derivation:

1. **Truncation.** `payments` is capped at `PAYMENT_LIST_CAP = 200`
   (`app/pages/billing.py:214`). Past the cap, the oldest *visible* payment is
   labelled "первый платёж" although it is a renewal. The section is otherwise
   scrupulous about the cap naming itself (balance.html:207-211); this derived label
   silently ignores it.
2. **Status blindness.** `canceled` and `pending` rows enter the map. A failed first
   attempt therefore claims "первый платёж" and the real first successful payment is
   labelled "продление".
3. **Equality on `created_at`.** Two rows for one plan sharing a timestamp are both
   labelled first.

**Fix:** compute the label where the data is, not in Jinja — e.g. a
`first_subscription_payment_at(db, user_id) -> dict[str, datetime]` in
`billing_service.py` that queries `MIN(created_at) GROUP BY plan WHERE
status = 'succeeded'`, unaffected by the display cap, and pass the resulting map
into the template as it is passed today.

---

### WR-09: An unexpected SDK response shape leaves a committed orphan `pending` payment — the exact outcome the ordering comment exists to prevent

**File:** `app/services/payment_service.py:166-193`
**Severity:** WARNING

```python
    db.add(db_payment)
    await db.commit()          # line 178
    ...
    return {
        "confirmation_url": payment.confirmation.confirmation_url,   # line 191
        "payment_id": payment.id,
    }
```

Lines 116-121 argue at length that the SDK call must precede the DB write, because a
row left behind after a failure "означала бы платёж, которого у ЮKassa нет вовсе …
висел бы `pending` вечно". Line 191 reintroduces the mirror image: it dereferences
`payment.confirmation.confirmation_url` *after* the commit and *outside* the guarded
block. If `confirmation` is absent or `None` for any response shape the SDK returns,
the raised `AttributeError` is not a `PaymentCreationError`, so
`app/pages/billing.py:362` and `:435` do not catch it — the user gets an unhandled
500 while a committed `pending` row sits in `payments` forever.

`payment.id` is likewise dereferenced at line 167 before the guard.

**Fix:** validate the response before writing, and raise the module's own type.

```python
    confirmation_url = getattr(
        getattr(payment, "confirmation", None), "confirmation_url", None
    )
    if not payment.id or not confirmation_url:
        # Ответ без ссылки подтверждения — тот же исход, что и отказ создания:
        # платить некуда. Строка в `payments` под него не заводится, иначе она
        # повисла бы `pending` навсегда (тот же довод, что у порядка выше).
        logger.error(
            "payment_create_malformed_response",
            user_id=user_id, kind=kind, plan=plan, amount=price,
        )
        raise PaymentCreationError("ЮKassa не вернула ссылку подтверждения")

    db_payment = Payment(...)
    db.add(db_payment)
    await db.commit()
```

## Info

### IN-01: Unused import `text`

**File:** `app/services/billing_service.py:4`
`from sqlalchemy import select, update, func, text` — `text` has no use in the module
(confirmed by `ruff --select F`: `F401`).
**Fix:** `from sqlalchemy import select, update, func`

---

### IN-02: Unused local `now`

**File:** `app/services/billing_service.py:150`
`reset_all_free_monthly` computes `now = datetime.now(timezone.utc)` and never reads
it (`ruff`: `F841`). Each `reset_free_monthly` call computes its own.
**Fix:** delete the line.

---

### IN-03: Dead defensive branch on `rowcount`

**File:** `alembic/versions/0018_subscriptions_unique_user.py:112`
```python
deactivated = result.rowcount if result.rowcount is not None else -1
```
`CursorResult.rowcount` is documented to return `-1` when unavailable, never `None`,
so the `else` branch is unreachable and the sentinel is produced by the driver anyway.
**Fix:** `deactivated = result.rowcount`.

---

### IN-04: `GET /api/billing/packages` has no authentication, unlike its two neighbours

**File:** `app/routes/billing.py:25-27`
`get_balance` and `get_transactions` both depend on `get_current_user_id`;
`list_packages` depends only on `get_settings`. The data is low-sensitivity (prices
are on the public tariff page), but the asymmetry is unexplained in a file that
documents every other decision, and it is a second unauthenticated entry point that
inherits WR-07's 500-on-malformed-config.
**Fix:** add `user_id: int = Depends(get_current_user_id)`, or document why this one
route is public.

---

### IN-05: `datetime.now(timezone.utc)` sampled three times in one render

**File:** `app/pages/billing.py:228`, `237`
`expired` and `live` are computed from two separate `datetime.now()` calls describing
the same instant. Harmless today (the two predicates are strict complements around
the boundary), but it makes the two flags derivable from different clocks.
**Fix:** hoist `now = datetime.now(timezone.utc)` to the top of the handler and pass
it to both.

---

### IN-06: Loop-invariant `live` evaluated inside the set comprehension

**File:** `app/pages/billing.py:238-244`
```python
refused_plan_ids = {
    plan["id"] for plan in plans
    if plan.get("id") and live and _switch_is_refused(current_plan_id, plan["id"])
}
```
`live` does not depend on `plan`. Reads as if it might.
**Fix:** `refused_plan_ids = {...} if live else set()`.

---

### IN-07: A paid subscription can be recorded with `plan="free"`

**File:** `app/services/payment_service.py:466`
```python
Subscription(user_id=..., plan=db_payment.plan or "free", ...)
```
A `kind="subscription"` payment with a NULL `plan` silently creates a *free* tier
subscription for money taken. Not reachable through `subscribe_to_plan` (which always
passes `selected["id"]`), but the fallback converts a data defect into a plausible
lie rather than a loud failure — the opposite of the "плану, которого там нет, ранг
НЕ УГАДЫВАЕТСЯ" rule in `app/constants.py:61-65`.
**Fix:** log at `error` and skip the plan assignment rather than substituting `free`.

---

_Reviewed: 2026-08-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 05-tarify
round: 3
reviewed: 2026-08-16T18:40:00Z
depth: standard
files_reviewed: 39
files_reviewed_list:
  - alembic/versions/0017_payment_kind_and_plan.py
  - alembic/versions/0018_subscriptions_unique_user.py
  - app/application/analytics/send_analytics.py
  - app/application/billing/__init__.py
  - app/application/billing/plan_switch.py
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
  - docker-compose.prod.yml
  - tests/test_application/test_plan_switch.py
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
  critical: 1
  warning: 7
  info: 5
  total: 13
status: issues_found
---

# Phase 05 (tarify): Code Review Report — ROUND 3

**Reviewed:** 2026-08-16T18:40:00Z
**Depth:** standard
**Files Reviewed:** 39
**Status:** issues_found
**Round:** 3

## ⚠️ READ THIS BEFORE RESOLVING ANY FINDING NUMBER

Finding IDs are **NOT stable across rounds**. `CR-01` in this file is a DIFFERENT
defect from `CR-01` of round 1 and from `CR-01` of round 2. A bare number without
a round is ambiguous and has already caused confusion in this phase's records.

| Round | Where to read it | Result |
|-------|------------------|--------|
| 1 | `git show 4989f7a:.planning/phases/05-tarify/05-REVIEW.md` | critical 2, warning 10, info 6 |
| 2 | `git show 1d29360:.planning/phases/05-tarify/05-REVIEW.md` | critical 2, warning 9, info 7 |
| 3 | this file | critical 1, warning 7, info 5 |

Round 2 was written **before plan 05-11 landed**: it does not cover
`app/application/billing/plan_switch.py`, the `switch_is_refused` rule, or the
apply-stage behaviour of `_apply_extension`. That code is reviewed here for the
first time, and it is where the one Critical finding lives.

Dispositions for round-1/round-2 findings live in `.planning/STATE.md`
(§Deferred Items and the consolidated entry in §Blockers/Concerns). Items that are
already dispositioned are listed in "Previously Dispositioned" below and are
**not** re-opened here.

## Structural Findings (fallow)

No `<structural_findings>` block was supplied with this review request, so there
is no structural pre-pass substrate to reproduce. All findings below are narrative.

## Summary

The billing slice is unusually well-documented and its concurrency work
(`_claim_payment` compare-and-swap, the `0018` partial unique index, the
two-real-session tests in `test_payment_concurrency.py`) is genuine and holds up
under adversarial reading — those are not decorative tests.

The plan-switch work delivered by 05-11 is the weak point. It closes the exact
scenario the verifier named (two payments while no subscription exists) and
leaves an adjacent, equally reachable one open: **once a paid period has expired,
the intent stage sells a downgrade and the apply stage silently refuses to
deliver it.** The project's own tests contain both halves of this contradiction —
`test_a_downgrade_after_the_period_has_ended_is_accepted` proves the sale,
and no test exercises the apply stage with an expired subscription. I reproduced
the end-to-end path against the real handlers and the real webhook: money is
taken for Basic, the row stays `pro`, forever.

Secondary themes: several of the phase's own stated invariants are applied to
one artifact and not to its twin (the payments journal declares its ceiling, the
operations journal on the same screen truncates silently; `KIND_*` constants are
enforced but `STATUS_PENDING` is dead while the literal is written), and one
error string tells the user a factually wrong reason.

---

## Critical Issues

### CR-01: A downgrade bought after the paid period expires is charged but never applied — and downgrade is permanently unreachable

**File:** `app/services/payment_service.py:516-555` (`_apply_extension`),
with `app/application/billing/plan_switch.py:25-61` and
`app/pages/billing.py:99-112, 223-230, 329-333`

**Issue:**

The `upgrade-only` rule has two stages that are supposed to agree. They do not
agree on **expiry**:

- **Intent stage** (`app/pages/billing.py:330`) calls `switch_is_refused` only
  when `_subscription_is_live(...)` is true. Expiry lifts the guard — this is
  deliberate and documented (`plan_switch.py:36-38`: *"истёкший срок гард
  снимает, потому что защищать уже нечего"*), and it is locked in by
  `tests/test_pages/test_billing_payment_errors.py:761`
  (`test_a_downgrade_after_the_period_has_ended_is_accepted`), which asserts a
  302 to the YooKassa confirmation URL.
- **Apply stage** (`payment_service.py:540`) calls `switch_is_refused`
  **unconditionally**. `_active_subscription` (`payment_service.py:501-513`)
  filters on `is_active` only — there is no expiry predicate — and nothing in
  the codebase ever writes `is_active = False` on expiry (verified: the only
  writes to `Subscription.is_active` are the model default and the `0018`
  backfill).

So the expired-Pro row stays active forever, `switch_is_refused("pro","basic")`
stays `True` forever, and every Basic payment that user ever makes is charged,
converted to days, and stripped of its plan.

**Reproduced**, not inferred. Probe against the real page handler and the real
`handle_webhook` (probe file removed after the run; working tree is clean):

```
POST /billing/subscribe plan=basic  -> 302 (payment_created plan="basic", amount "1490.00")
handle_webhook payment.succeeded    -> True
WARNING subscription_plan_preserved {"plan": "pro", "paid_plan": "basic"}
INFO    subscription_payment_succeeded {"plan": "basic"}
PROBE plan after paid downgrade: ['pro']
```

Consequences, in order of severity:

1. **Money taken for a product never delivered.** The user chose Basic, paid the
   Basic price, and received nothing they asked for. The only record is a
   `warning` log line the user cannot see. The screen will keep saying "Pro".
2. **Downgrade is unreachable for the lifetime of the account.** There is no
   state from which `switch_is_refused` stops refusing: the guard's escape hatch
   (expiry) exists only on the stage that does not decide the outcome.
3. **Revenue leakage in the other direction.** The user now renews indefinitely
   at the Basic price (1490.00) while carrying the Pro plan value (4900.00),
   because every subsequent Basic payment also lands in the `preserved` branch.
4. `payment_service.py:461` asserts *"Платёж младшего тарифа **при действующем
   старшем**"* — the code does not test "действующем", so the docstring
   describes a narrower behaviour than the code implements.

This means the closure recorded in `.planning/STATE.md:119` ("CR-01 ревью
раунда 2 … ✓ Закрыто планом 05-11") is **incomplete**: 05-11 unified the
*declaration* of the rule but not its *inputs*. The regression test added by
05-11 (`test_a_confirmed_lower_plan_does_not_strip_the_higher_one_at_the_apply_stage`)
and every other apply-stage test seeds through `_seed_live_subscription`, so the
expired branch has zero coverage on the stage where money is already gone.

**Fix:** the apply stage must consume the *same* liveness input the intent stage
uses, not just the same rank comparison. Pass the moment into the decision and
refuse only while the period is live:

```python
# app/services/payment_service.py
from app.application.analytics.send_analytics import normalize_utc

def _apply_extension(
    subscription: Subscription, db_payment: Payment, now: datetime
) -> None:
    # Liveness is read BEFORE the date moves: after next_expiry the row is
    # always live, and the guard would never lift.
    was_live = _period_is_live(subscription.expires_at, now)
    subscription.expires_at = next_expiry(subscription.expires_at, now)

    if not db_payment.plan:
        return

    if was_live and switch_is_refused(subscription.plan, db_payment.plan):
        logger.warning("subscription_plan_preserved", ...)
        return

    subscription.plan = db_payment.plan
```

`_period_is_live` is `app/pages/billing.py:_subscription_is_live` — move it next
to `switch_is_refused` in `app/application/billing/plan_switch.py` so that the
*whole* rule, not half of it, has one declaration; `app/pages/billing.py` then
imports it instead of owning it. Note the ordering constraint above: reading
liveness after `next_expiry` would always report "live" and silently restore the
current bug.

Required regressions (none exist today):

- expired Pro + confirmed Basic → row becomes `basic`, date moves, **no**
  `subscription_plan_preserved` warning;
- live Pro + confirmed Basic → row stays `pro` (existing test, must stay green);
- expired Pro + confirmed Pro → renewal still works.

Note also that `switch_is_refused`'s docstring (`plan_switch.py:35-42`) states
the two-stage contract as if both stages already share the expiry input. Whatever
fix lands must correct that text too, or the next reader will re-derive the same
false confidence this round did.

---

## Warnings

### WR-01: An *upgrade* to an unranked plan is refused with the word "downgrade" — the user is told something factually untrue

**File:** `app/application/billing/plan_switch.py:59-60`,
`app/pages/billing.py:73-85, 333`,
locked in by `tests/test_pages/test_billing_payment_errors.py:786-812`

**Issue:** `switch_is_refused` returns `True` for an unknown rank on *either*
side — correct and deliberate (fail-closed). But the caller maps every `True` to
a single reason code, `downgrade`, whose copy is:

> "Перейти на младший тариф можно после окончания оплаченного срока — оплаченные
> дни не сгорают"

`test_a_plan_without_a_rank_fails_closed` is parametrized with
`("basic", "platinum")` — a user on Basic trying to buy the *higher* plan — and
asserts `location == "/billing?error=downgrade"`. The user is told they were
blocked from downgrading while they were in fact blocked from upgrading, and is
advised to wait for a period to end, which will not help. The plan card shows the
same wrong sentence (`DOWNGRADE_CARD_CAPTION`, rendered by
`plan_card.html:92`).

This is reachable exactly in the situation the code anticipates by design:
`PLAN_LIMITS` (env) drifting from `PLAN_ORDER` (code). The phase's own prohibition
against plausible falsehood (P-04-01, cited throughout this codebase) applies.

**Fix:** have the rule report *why* it refused, and map the two reasons to two
strings:

```python
# plan_switch.py
REFUSAL_DOWNGRADE = "downgrade"
REFUSAL_UNRANKED = "unranked"

def switch_refusal(current_plan: str, target_plan: str) -> str | None:
    if target_plan == current_plan:
        return None
    ranks = {plan: i for i, plan in enumerate(PLAN_ORDER)}
    current, target = ranks.get(current_plan), ranks.get(target_plan)
    if current is None or target is None:
        return REFUSAL_UNRANKED
    return REFUSAL_DOWNGRADE if target < current else None
```

Add `"unranked": "Этот тариф сейчас недоступен для перехода — обратитесь к
администратору"` to `PAYMENT_ERROR_MESSAGES` and update the parametrized test to
expect `error=unranked` for the upgrade direction. Keep `switch_is_refused` as a
thin `switch_refusal(...) is not None` wrapper if the boolean call sites are
worth preserving.

### WR-02: `yookassa_return_url` fallback builds a return URL out of the app's display name

**File:** `app/services/payment_service.py:135`

**Issue:**

```python
"return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
```

`app_name` defaults to `"Broadcaster"` (`app/config.py:8`) — it is a display
name, not a base URL. With `YOOKASSA_RETURN_URL` unset the payment is created
with `return_url = "Broadcaster/billing"`. Best case YooKassa rejects it, the
generic `PaymentCreationError` fires, and every buyer sees "попробуйте ещё раз
через минуту" for a defect a retry cannot fix; worse case it is accepted and the
buyer is stranded after paying. `YOOKASSA_RETURN_URL` is not listed in
`docker-compose.prod.yml`'s `x-app-base.environment` — it can only arrive via
`.env`, so the fallback is one missing line away from being live.

This predates phase 05 (introduced in `a853082`), but the phase moved the
subscription path — the most expensive purchase in the product — onto this same
call, and `payment_service.py` is in scope.

**Fix:** stop synthesising a URL from a name. Either make the setting required
for a payment to be created:

```python
if not settings.yookassa_return_url:
    logger.error("payment_return_url_not_configured", user_id=user_id)
    raise PaymentCreationError("return_url не настроен")
```

or introduce an explicit `app_base_url` setting and build from that. Pin
`YOOKASSA_RETURN_URL` in `docker-compose.prod.yml` the same way `05-07` pinned
`YOOKASSA_WEBHOOK_CLIENT_IP_HEADER`.

### WR-03: `STATUS_PENDING` is dead while the write path uses the bare literal — the module's own stated rule, broken at the one place it protects

**File:** `app/services/payment_service.py:27` (declared), `:170` (literal used)

**Issue:** the module declares `STATUS_PENDING = "pending"` and then writes

```python
db_payment = Payment(..., status="pending", ...)
```

`STATUS_PENDING` has zero references anywhere in the module (verified by grep).
This is exactly the anti-pattern the file argues against 130 lines earlier
(`:37-40`, "КОНСТАНТАМИ SDK, НИКОГДА СТРОКОВЫМИ ЛИТЕРАЛАМИ") and that
`app/pages/billing.py:339-341` enforces for `KIND_*`. A typo here does not fail
loudly: it produces a payment that `TERMINAL_STATUSES` does not match either, so
the row would be claimable but would render with an unknown status badge
(`payment_row.html:63` prints unknown statuses verbatim).

**Fix:** `status=STATUS_PENDING` at line 170. If the constant is genuinely
unwanted, delete it — but leaving both a constant and a literal for the same
value is the state that produces drift.

### WR-04: `plan_card.html` hardcodes `'free'` although the handler already hands it `free_plan_id`

**File:** `app/templates/billing/includes/plan_card.html:76`
(vs `app/pages/billing.py:38, 263` and `app/templates/billing/balance.html:119`)

**Issue:** `app/pages/billing.py` puts `free_plan_id` into the template context
precisely so the identifier has one source, and `balance.html:119` uses it. The
plan card — the surface that actually decides whether to draw a purchase form —
does not receive it and compares against the literal:

```jinja
{% if plan.get('id') == 'free' %}
```

Rename the free plan in `PLAN_LIMITS` (an env-editable list, as the code
repeatedly notes) and the card renders a "Перейти на …" form for a `0.00` plan.
The handler's own `FREE_PLAN_ID` check (`billing.py:314`) also compares against
`"free"`, so it will not catch it either — the purchase reaches `create_payment`
with `price="0.00"`, YooKassa rejects it, and the buyer gets the generic
"попробуйте ещё раз" screen forever.

Counting: `"free"` is written as a literal in six places
(`constants.py:70` inside `PLAN_ORDER`, `billing.py:38`, `common.py:549`,
`payment_service.py:477`, `subscription.py:34`, `plan_card.html:76`).

**Fix:** pass it through the macro, the way `switch_refused` already is:

```jinja
{% macro plan_card(plan, current_plan, payments_enabled,
                   switch_refused=false, refused_caption='', free_plan_id='free') -%}
...
{% if plan.get('id') == free_plan_id %}
```

and update the call site in `balance.html:141-142`. Longer term, promote the
identifier to `app/constants.py` next to `PLAN_ORDER` (whose first element is
already this value) and let `billing.py` read it from there rather than declaring
its own.

### WR-05: The operations journal truncates silently at 20 rows on the same screen where the payments journal declares its ceiling

**File:** `app/pages/billing.py:42, 190-192` and
`app/templates/billing/balance.html:235-263`

**Issue:** D-17 is stated across this phase as an invariant, not a preference —
`app/constants.py:86-90`: *"СРАБОТАВШИЙ ПОТОЛОК ОБЯЗАН НАЗЫВАТЬ СЕБЯ. Молча
короткий список читается как «других платежей не было»"*. The payments block
implements it in full: `count_payments` runs before the list, `payments_truncated`
reaches the context, and `balance.html:207-211` prints the notice.

The operations journal immediately below gets `limit=TRANSACTION_LIST_LIMIT`
(20) with no count, no `transactions_truncated` flag, and no notice. A user who
sent 40 messages this month opens "История операций", sees 20 rows, and has no
way to know the rest exist. The same argument that justified the notice for
payments applies verbatim: this is the journal that answers "where did my
messages go".

Twenty is also an order of magnitude tighter than the payments cap (200) on a
journal that grows once per *send* rather than once per *purchase*, so it will
trigger for ordinary users, not edge cases.

**Fix:** mirror the payments block exactly — add a `count_transactions` to
`app/services/billing_service.py` alongside `count_payments`, compute
`transactions_total` before the list, and render the same `mono(..., 'warn')`
notice. If a full count is unwanted, the alternative that keeps the invariant is
to request `limit + 1` rows and drop the extra, which detects truncation without
a second query.

### WR-06: A plan missing from `PLAN_LIMITS` renders all four axes as "без ограничений" — an unlimited plan the user does not have

**File:** `app/pages/billing.py:178-180`, `app/application/billing/plan_usage.py:184`,
`app/templates/billing/includes/usage_meters.html:30-34`

**Issue:** when the current plan id is not in the config, `current_plan` becomes
`{}`. `plan_axes` then reads `limits.get(key, UNLIMITED)` → `None` for all four
axes, and `usage_meter` renders `None` as `'∞'` + "без ограничений".

The handler's comment frames this as "лимитов нет, а не падение", which is the
right *failure mode* but the wrong *rendering*: "лимитов нет" and "ограничений
нет" are opposite claims. A Basic subscriber whose plan was removed from
`PLAN_LIMITS` is shown four unlimited meters. On the same screen the renewal
button disappears (`balance.html:119`, `current_in_config` is falsy), so the page
simultaneously says "you have unlimited everything" and "you cannot renew".

Same family as the `∞`-on-empty-balance issue in `base.html` (round-2 WR-06,
deferred) — but this one is on the tariff screen itself, which is the phase's
deliverable.

**Fix:** distinguish "no limit" from "limit unknown". Minimal version — carry the
distinction into the axis and render it:

```python
# plan_usage.py
UNKNOWN = object()          # or: limit_known: bool on PlanAxis
limit = limits.get(key, UNLIMITED) if limits else UNKNOWN
```

```jinja
{%- if axis.limit_known is false %}
  {{ mono(axis.label ~ ' — ' ~ axis.used ~ ' / —', 'warn') }}
  {{ mono('лимит тарифа не настроен') }}
{%- elif axis.limit is none %}
  ...
```

A cheaper stopgap that removes the false claim without touching the dataclass:
pass the plain absence up as a page-level flag and render the meters block as an
`empty_state` ("Лимиты тарифа не настроены") when `current_plan` is empty.

### WR-07: The web tier that parses webhook JSON also holds the host Docker socket

**File:** `docker-compose.prod.yml:91-92`

**Issue:**

```yaml
  web:
    ...
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

`/var/run/docker.sock` is root-equivalent access to the host. The same process
now terminates `POST /api/billing/webhook`, whose only authentication is an IP
read from a proxy-set header (`app/routes/billing.py:60-103`) and which can be
disabled outright by one env flag (`yookassa_webhook_verify_ip = False`, the
documented emergency switch). Any RCE-class bug on that path is a host
compromise, not a container compromise.

**Pre-existing, not introduced by phase 05** — the mount serves
`app/services/wa_container_manager.py`. It is raised here because
`docker-compose.prod.yml` is in this review's scope, the phase materially
enlarged what reaches this process, and a severe risk that goes unwritten becomes
an unknown risk after one refactor (the same argument `is_same_origin` makes
about its own named boundary).

**Fix:** not a code change for this phase. The correct shape is to move container
management out of `web` into a dedicated worker that owns the socket, and have
`web` reach it over the existing Redis queue. Failing that, put a
socket-filtering proxy (e.g. `tecnativa/docker-socket-proxy`) in front of the
socket with only the container verbs `wa_container_manager` actually uses, and
give `web` the proxy address instead of the raw socket. If neither is in budget,
record it as an accepted risk in `.planning/STATE.md` §Blockers/Concerns with an
owner, the way R-03-09 was recorded — the failure mode here is that it is
currently accepted by nobody in particular.

---

## Info

### IN-01: Unused import and unused logger in a money-handling module

**File:** `app/services/billing_service.py:4, 12`

`from sqlalchemy import select, update, func, text` — `text` is never used.
`logger = structlog.get_logger()` is never called (verified by grep for
`logger.` and `text(` — no hits). The second one is the more interesting signal:
this module performs every balance mutation in the product and emits no
structured log line of its own, while its callers
(`payment_service.py`, `app/pages/admin.py`) log on its behalf.

**Fix:** drop `text` from the import; either delete `logger` or use it —
`add_messages` and `reset_free_monthly` changing a balance are exactly the events
a support request will ask about.

### IN-02: `app/application/billing/__init__.py` is empty

**File:** `app/application/billing/__init__.py`

Every other module in this package opens with a substantial module docstring
stating its boundaries (`plan_switch.py`, `plan_usage.py`,
`subscription_period.py`, and `app/application/analytics/send_analytics.py`).
The package `__init__` is zero bytes.

**Fix:** a short docstring naming what the package is for and, critically, the
shared boundary rule the three modules repeat individually ("nothing here reads
or writes the DB, knows Jinja, or imports `Request`") — stating it once at the
package level is the same de-duplication argument the modules themselves make.

### IN-03: `subscription_period.py`'s boundary claim is untrue transitively, and nothing holds it

**File:** `app/application/billing/subscription_period.py:3-8, 22`

The docstring states the module "не знает ни про Jinja, ни про Request, ни про
сессию SQLAlchemy". Its one import,
`app.application.analytics.send_analytics`, imports `AsyncSession`, `select`,
five ORM models, and lazily imports `app.pages.common` inside two functions.
The claim holds for what the module *uses*, not for what it *pulls in*.

`plan_switch.py` has the same claim and does hold it — enforced by
`test_the_only_import_of_the_rule_is_the_declared_plan_order`
(`tests/test_application/test_plan_switch.py:96`). `subscription_period.py` has
no equivalent test, so the claim can decay silently.

**Fix:** either move `normalize_utc` into a genuinely dependency-free helper both
modules import, or add the AST import assertion to
`tests/test_application/test_subscription_period.py` and soften the docstring to
what is actually guaranteed.

### IN-04: `datetime.now(timezone.utc)` is sampled three times inside one render

**File:** `app/pages/billing.py:214, 223, 331`

`billing_page` samples the clock at line 214 (`expired`) and again at line 223
(`live`), and `subscribe_to_plan` samples it again at line 331. Two decisions
about the same subscription on the same request read two different instants.
The window is microseconds and the predicates are `<` and `>` on the same value,
so at the exact boundary both are false and nothing contradicts — but nothing
guarantees that as the predicates evolve.

**Fix:** sample once at the top of each handler and thread the value:
`now = datetime.now(timezone.utc)`. Cheap, and it makes the two derived booleans
provably consistent rather than incidentally consistent.

### IN-05: The downgrade refusal sentence exists twice in two wordings

**File:** `app/pages/billing.py:73-76` (`PAYMENT_ERROR_MESSAGES["downgrade"]`)
and `:82-85` (`DOWNGRADE_CARD_CAPTION`)

The comment at `:79-81` argues these two live side by side so they cannot drift —
but they are already two different sentences saying the same thing ("Перейти на
младший тариф можно после окончания оплаченного срока — оплаченные дни не
сгорают" vs "Переход на младший тариф — после окончания оплаченного срока:
оплаченные дни не сгорают"). Adjacency prevents *forgetting* one; it does not
prevent them meaning different things, which is the risk the comment claims to
address.

**Fix:** derive one from the other, or accept that they are two intentionally
different registers (banner vs card caption) and say so in the comment instead of
claiming they are one rule in two halves. Note WR-01 will need to touch both.

---

## Previously Dispositioned — NOT re-opened

These were found in earlier rounds and carry recorded dispositions in
`.planning/STATE.md`. All were re-observed as still present in the code; none is
being opened as a new finding.

| Item | Where | Disposition |
|------|-------|-------------|
| Blocking sync `YooPayment.create()` inside `async def`, single uvicorn worker (no `--workers` at `docker-compose.prod.yml:87`) | `app/services/payment_service.py:130-142` | Round-2 CR-02 — **deferred with rationale** (plan 05-10); STATE §Blockers/Concerns 🔴 entry. Re-confirmed: `command:` at `:87` still has no `--workers`. |
| Untyped `PLAN_LIMITS` / `MESSAGE_PACKAGES` — bad type breaks `axis_percent`, bad format breaks `json.loads` in `parsed_plan_limits` | `app/config.py:61, 74-78, 116-121` | Round-1 WR-10 + round-2 WR-07 — **deferred, one disposition** (typed plan record validated at `Settings` construction). Also covers the `selected["price"]` / `package["name"|"count"|"price"]` `KeyError` paths in `app/pages/billing.py:346, 417-419`. |
| Lost update in `reset_free_monthly` (`bal.balance += free_limit`) | `app/services/billing_service.py:133` | Round-2 WR-01 — deferred. |
| `"object": null` in the webhook body → `AttributeError` → 500 → YooKassa retry loop | `app/services/payment_service.py:283`, `app/routes/billing.py:200-202` | Round-2 WR-04 — deferred. Same root as a malformed (non-JSON) body at `routes/billing.py:188`. |
| Unvalidated `limit` / `offset` on `GET /api/billing/transactions` | `app/routes/billing.py:31-38` | Round-1 WR-08 / round-2 WR-05 — deferred. |
| `∞` in the sidebar balance widget when the limit is zero | `app/templates/base.html:74` | Round-2 WR-06 — deferred. |
| "первый платёж" / "продление" decided from the truncated payments page | `app/templates/billing/includes/payment_row.html:43-45`, `balance.html:217-222` | Round-1 + round-2 WR-08 — deferred. Also fires on two payments sharing a `created_at`. |
| Orphaned `pending` row when the SDK response has no `confirmation` | `app/services/payment_service.py:192` | Round-2 WR-09 — deferred. |
| Subscription payment with an empty plan recorded as `free` | `app/services/payment_service.py:477` | Round-2 IN-07 — deferred. |
| `handle_webhook` returning `False` still answers HTTP 200 | `app/routes/billing.py:198-199` | Round-1 WR-06 — deferred. |
| SQLite table recreation in revision `0017` | `alembic/versions/0017_payment_kind_and_plan.py:63-66` | Round-1 WR-03 — deferred; round-trip covered by `tests/test_migrations/test_0017_payment_kind_and_plan.py`. |
| Guard re-opened by one unverified variable / emergency switch leaves no trace | `app/routes/billing.py:176-185` | Round-2 WR-02, WR-03 — deferred. |

---

## What held up under adversarial reading

Recorded so the next round does not re-litigate it:

- `_claim_payment` (`payment_service.py:197-225`) is a real compare-and-swap;
  `rowcount == 1` is checked, the claim and the credit share one transaction, and
  `test_payment_concurrency.py` drives two genuinely separate `AsyncSession`s
  with deterministic interleaving rather than `asyncio.gather` theatre.
- `set_committed_value` in `_mirror_claim` and `add_messages` correctly avoids
  the double-UPDATE that plain assignment would emit.
- The `0018` partial unique index is declared in **both** the model and the
  revision, so `Base.metadata.create_all` in the test suite actually exercises it.
- `_extend_subscription`'s `IntegrityError` recovery re-raises the original
  exception object when the re-query finds no row — it does not swallow unrelated
  constraint failures.
- `_webhook_client_ip` reads the **right-most** element of the header list, which
  is the correct direction and the opposite of the intuitive one.
- `add_one_month` clamps to `calendar.monthrange` and handles the December
  year-rollover explicitly; `next_expiry` normalises both operands before
  comparing, so it is safe on both dialects.
- `format_amount` checks `is_finite()` *after* parsing, which is the only place
  that catches `NaN` / `Infinity` (round-1 WR-01, closed by 05-09).

---

_Reviewed: 2026-08-16T18:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Round: 3 — round 1 at `4989f7a`, round 2 at `1d29360`_

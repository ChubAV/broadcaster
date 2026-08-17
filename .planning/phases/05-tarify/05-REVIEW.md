---
phase: 05-tarify
reviewed: 2026-08-17T18:47:42Z
depth: standard
files_reviewed: 44
files_reviewed_list:
  - alembic/versions/0017_payment_kind_and_plan.py
  - alembic/versions/0018_subscriptions_unique_user.py
  - alembic/versions/0019_payment_switch_authorized.py
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
  - tests/test_migrations/test_0019_payment_switch_authorized.py
  - tests/test_migrations/test_deploy_applies_migrations_before_serving.py
  - tests/test_migrations/test_model_matches_head.py
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
  info: 4
  total: 12
status: issues_found
---

# Phase 05-tarify: Code Review Report

**Reviewed:** 2026-08-17T18:47:42Z
**Depth:** standard
**Files Reviewed:** 44
**Status:** issues_found

## Summary

Reviewed the billing/subscription surface with the money path as the primary target:
`create_payment` → YooKassa → `handle_webhook` → `_claim_payment` → `_extend_subscription`
→ `_apply_extension` → `subscription_period` arithmetic.

What holds up under attack:

- The webhook source guard is real end to end. Every proxying `location` in both
  `nginx/nginx.conf.template` and `nginx/nginx-http.conf.template` sets
  `X-Real-IP $remote_addr` (overwrite, not append), the default header name is pinned in
  `app/config.py:108` and in `docker-compose.prod.yml:27`, the rightmost-element read in
  `app/routes/billing.py:103` is correct for an overwriting proxy, an unconfigured header
  fails closed, and the guard sits outside the `try` so it cannot be downgraded to a 500.
- `_claim_payment` (`app/services/payment_service.py:422-431`) is a genuine compare-and-swap
  and works identically on both dialects; `_mirror_claim` correctly uses `set_committed_value`
  so no second UPDATE is emitted; `add_messages` increments in SQL, not in Python.
- The migration-order deploy gate is wired correctly: `entrypoint.sh` has `set -e` before
  `alembic upgrade head` before `exec "$@"`, and `web` is the only service bound to it.
  All three migration test fixtures monkeypatch `DATABASE_URL` *and* `set_main_option`, so
  none of them can be pointed at a developer's real database.
- The AST ordering invariant (`test_the_liveness_is_sampled_before_the_date_moves`) is not
  vacuous: it derives the mover set from the import, walks the whole body, and has two
  negative controls over synthetic sources.

What does not hold up: the newest money arithmetic, `converted_remainder` (plan 05-18), is
the least-verified code in the phase. It has **zero direct unit tests**, its stated rationale
for taking the month length from `add_one_month` is provably inoperative (the term cancels
algebraically), and its price-unreadable fallback silently restores the exact unbounded-carry
leak the function was written to close — in a branch no test exercises. Separately, three
docstring claims that plan 05-19 was supposed to make confirmable are still not confirmable
by the code beside them, and `GET /api/billing/transactions` accepts unvalidated `limit`/`offset`.

Known and recorded debt (second intent-cap window, `uq_subscriptions_active_user` not built
in prod, D-26 schema divergence) is **not** re-reported below.

---

## Critical Issues

### CR-01: `convert-remainder` fallback silently restores the unbounded prepaid-horizon leak, in a branch with zero test coverage

**File:** `app/services/payment_service.py:1019-1036` (fallback), `app/services/payment_service.py:787-815` (`_plan_price`)
**Severity:** BLOCKER

**Issue:**

In the allowed-upgrade path, when either plan price cannot be read, the code logs and falls
through with `base` still bound to `subscription.expires_at` (line 1014):

```python
base = subscription.expires_at
if period_is_live and db_payment.plan != subscription.plan:
    price_from = _plan_price(subscription.plan)
    price_to   = _plan_price(db_payment.plan)
    if price_from is None or price_to is None:
        logger.warning("subscription_prorating_skipped", ...)   # base stays == expires_at
    else:
        base = converted_remainder(...)

subscription.expires_at = next_expiry(base, now)
subscription.plan = db_payment.plan
```

"Fallback to prior behaviour" here *is* gap 1 of round 5: the entire accumulated prepaid
horizon is carried onto the senior plan by days, and then the plan is overwritten. The
docstrings quantify the damage themselves — twelve `basic` months (17 880 ₽) plus one `pro`
payment (4 900 ₽) yields thirteen months of Pro against a 63 700 ₽ list price, and the loss
grows linearly with a horizon the buyer controls.

Three things make this more than theoretical:

1. `_plan_price` returns `None` for any price that is absent, unparseable, **or not greater
   than zero**. The shipped `free` plan is priced `"0.00"` (`app/config.py:75`), so `free` is
   a *permanently* unreadable price by construction — any subscription row on `free` with a
   live `expires_at` takes this branch on its first paid upgrade. (See WR-05 for how such a
   row can be created.)
2. `price_to is None` fires whenever the payment's plan has left `PLAN_LIMITS` between sale
   and confirmation. The codebase repeatedly states this is normal operation
   (`app/services/payment_service.py:794-796`: "Перечень тарифов правится окружением, а
   действующий план записан в строке подписки — разойтись они могут в любую сторону и без
   нашего участия"). An operator renaming or dropping a plan id is a one-line env edit.
3. **The branch is untested.** `subscription_prorating_skipped` appears exactly once in the
   whole suite (`tests/test_pages/test_billing_payment_errors.py:2096`), and that test
   exercises the *refused* branch (`unreadable="price"` / seeded plan `"platinum"`), not this
   one. The value `"paid_plan_price"` — which only this branch can emit — is asserted nowhere.

The correct behaviour on an unreadable price is not to raise (a 5xx starts the YooKassa retry
cycle — that part of the design is right), but the current fallback chooses the *most*
expensive possible outcome for the platform rather than a bounded one.

**Fix:** bound the carry instead of restoring the unlimited one, and cover the branch.

```python
    if price_from is None or price_to is None:
        logger.warning(
            "subscription_prorating_skipped",
            user_id=db_payment.user_id,
            yookassa_id=db_payment.yookassa_payment_id,
            plan=subscription.plan,
            paid_plan=db_payment.plan,
            unreadable="price" if price_from is None else "paid_plan_price",
        )
        # ГРАНИЦА ПЕРЕНОСА ПРИ НЕПРОЧИТАННОЙ ЦЕНЕ. Конвертировать нечем, но
        # переносить ВЕСЬ горизонт нельзя — это и есть гэп 1 раунда 5. Остаток
        # переносится не более чем на один календарный месяц: «остаток не сгорает»
        # держится, а величина, которой управляет покупатель, перестаёт быть
        # неограниченной.
        capped = min(
            normalize_utc(subscription.expires_at),
            add_one_month(normalize_utc(now)),
        )
        base = capped
```

Add two regressions mirroring `test_a_prepaid_horizon_is_not_converted_to_the_senior_plan_for_one_month`:
one seeding `subscription.plan = "free"` (permanently unreadable price), one seeding a payment
whose `plan` is absent from `parsed_plan_limits`, both asserting the resulting `expires_at`
stays bounded and that `unreadable="paid_plan_price"` is logged.

---

## Warnings

### WR-01: `converted_remainder`'s month-length rationale is provably false; `month_days` cancels out of the formula

**File:** `app/application/billing/subscription_period.py:231-236`, `:249-256`
**Severity:** WARNING

**Issue:** The docstring states:

> ДЛИНА МЕСЯЦА БЕРЁТСЯ У `add_one_month` ОТ ТОЙ ЖЕ БАЗЫ, А НЕ КОНСТАНТОЙ 30 — по той же
> причине, что у `prorated_expiry`: константа разошлась бы с `next_expiry` в феврале и в
> декабре, и «полный месяц» получил бы два разных определения.

That is not true of this function. `month_days` appears once in the denominator of `paid` and
once as the multiplier inside `prorated_days`, and the two cancel:

```
days = floor( month_days · (old · rem_sec / (month_days · 86400)) / new )
     = floor( rem_days · old / new )
```

Verified numerically — the answer is byte-identical for `month_days` of 28, 30 and 31:

| now | month_days | remainder | converted days | `int(rem·1490/4900)` |
|---|---|---|---|---|
| 2026-01-31 | 28 | 365 d | 110 | 110 |
| 2026-03-01 | 31 | 365 d | 110 | 110 |
| 2026-04-01 | 30 | 365 d | 110 | 110 |

The phase's own regression already encodes the cancelled form
(`tests/test_pages/test_billing_payment_errors.py:2310`:
`int(Decimal(remainder_days) * BASIC_PRICE / PRO_PRICE)`), with no month-length term at all.

This is precisely the class plan 05-19 was chartered to remove: a paragraph asserting a
property the neighbouring code does not have. It is also live risk — `add_one_month(now_utc)`
and the `timedelta` round-trip on lines 249-254 are dead computation that a future reader will
"fix" in the wrong direction, believing the calendar matters here.

**Fix:** either state the truth, or make the claim real. Truth is cheaper:

```python
    # ДЛИНА МЕСЯЦА В ОТВЕТ НЕ ВХОДИТ, И ЭТО СВОЙСТВО, А НЕ УПУЩЕНИЕ: она стоит
    # знаменателем стоимости остатка и множителем в `prorated_days`, и два
    # вхождения сокращаются. Ответ равен floor(остаток_в_днях · old / new) при
    # любой длине месяца — проверено на 28, 30 и 31 дне. Единица месяца остаётся
    # здесь только затем, чтобы деление денег на цену жило ОДНИМ объявлением
    # (`prorated_days`), а не второй формулой.
```

If instead the intent was that a shorter calendar month should make a remainder worth *more*,
that requires two different month lengths (the one the remainder was bought in, and the one it
is being converted into) and is a behaviour change, not a comment change.

### WR-02: `switch_authorized = False` is honoured in one branch and silently ignored in the other; the "expiry lifts the refusal on both stages" claim is false for it

**File:** `app/services/payment_service.py:920-927`, `:743-754`, docstring `:712-720`
**Severity:** WARNING

**Issue:** Three inconsistencies around the recorded-refusal value:

1. `_apply_extension:920-921` reads the recorded answer *without ever consulting*
   `period_is_live`. A payment carrying `switch_authorized = False` therefore keeps
   `refused = True` even when the paid period has expired. The `_extend_subscription`
   docstring (`:712-720`) states the opposite as an unconditional property:
   "Когда оплаченный срок истёк, отказ снимается на ОБЕИХ стадиях … План платежа
   ПРИМЕНЯЕТСЯ, каким бы он ни был … и следа `subscription_plan_preserved` на этом пути НЕТ."
   For a recorded `False`, the plan is not applied and `subscription_plan_preserved` *is*
   written.
2. `_extend_subscription`'s first-insert branch (`:743-754`) applies `db_payment.plan`
   unconditionally and never reads `switch_authorized` at all. So the same recorded refusal is
   honoured when a subscription row exists and ignored when it does not.
3. `app/models/payment.py:40-46` and `alembic/versions/0019_...py:33-36` both state explicitly
   that the column "обязана уметь выразить" `False` and that a future writer will otherwise
   express refusal through `NULL`. The value is unreachable *today* only because
   `subscribe_to_plan` returns 302 before creating the payment (`app/pages/billing.py:348-349`)
   — a one-line change away from being live on the money path.

**Fix:** make the recorded answer obey the same expiry rule as the rule branch, and state the
insert branch's position explicitly rather than by omission.

```python
    if db_payment.switch_authorized is not None:
        # ⚠️ ИСТЁКШИЙ СРОК СНИМАЕТСЯ ОТКАЗ И У ЗАПИСАННОГО ОТВЕТА
        # (`apply-after-expiry`, чекпойнт 05-13): защищать нечего независимо от
        # того, кто отказ вынес. Без этого члена записанный `False` пережил бы
        # собственный период, а докстринг `_extend_subscription` утверждает
        # обратное безусловно.
        refused = period_is_live and not db_payment.switch_authorized
        decided_by = "recorded_answer"
```

and in the insert branch add one line of reasoning naming why a recorded refusal is not
consulted there (no prior plan exists, so there is nothing to refuse) — or consult it.

### WR-03: "план только повышается" is violated silently, with no journal entry, on a path the code itself documents as reachable

**File:** `app/services/payment_service.py:686-693`, `:1015`, `:1065`; `app/application/billing/plan_switch.py:70`
**Severity:** WARNING

**Issue:** Both declarations state the outcome as an invariant —
"срок двигается всегда, план только растёт" (`plan_switch.py:70`) and
"Но ПЛАН при этом только повышается" (`payment_service.py:688`). Neither is true once D-28
recorded answers exist. Concrete sequence, using only mechanisms the file documents as
reachable:

1. No subscription. `POST /billing/subscribe plan=basic` → guard passes (nothing to protect) →
   payment `P1` written with `switch_authorized = True`. Not paid.
2. 25 h later `P1` is past `PENDING_INTENT_TTL_HOURS` and stops counting
   (`_open_subscription_intents:150-159`; the docstring at `:219-232` names this window
   explicitly and `tests/test_services/test_payment_service.py::test_a_stale_intent_does_not_block_a_new_one`
   is a green test that reaches it). `POST /billing/subscribe plan=pro` → `P2`,
   `switch_authorized = True`.
3. `P2` confirms → subscription `pro`, live.
4. `P1` confirms → `refused = not True = False` → line 1015 converts the `pro` remainder into
   `basic` days and line 1065 sets `subscription.plan = "basic"`.

The user is demoted from `pro` to `basic`, and because the refusal branch was never entered,
`subscription_plan_preserved` is **not** logged — the outcome leaves no trace at all. Money is
approximately conserved by the conversion, so this is a correctness/observability defect
rather than a leak, but the stated product rule (`upgrade-only`) is not enforced and the
declarations claim it is.

**Fix:** either enforce the invariant at the apply stage, or stop declaring it. Enforcing is
one condition and keeps the existing journal key:

```python
    if db_payment.switch_authorized is not None:
        refused = period_is_live and (
            not db_payment.switch_authorized
            # ЗАПИСАННОЕ РАЗРЕШЕНИЕ НЕ ОТМЕНЯЕТ `upgrade-only`. Оно снято ДО того,
            # как появился действующий старший тариф (окно срока давности
            # намерения), и понижать по нему значило бы исполнить сделку, которой
            # на момент подтверждения уже не существует.
            or switch_is_refused(
                subscription.plan, db_payment.plan, period_is_live=True
            )
        )
```

If the owner prefers the current behaviour, delete the "план только растёт" sentence from both
declarations and name the demotion outcome in `_extend_subscription`'s docstring.

### WR-04: no error handling or log around the DB write that follows a successful YooKassa `create`

**File:** `app/services/payment_service.py:372-385`
**Severity:** WARNING

**Issue:** The module argues at length (`:322-333`, T-05-49) that the SDK call must precede the
DB write, and it handles every failure of the SDK call. It handles none of the DB write:

```python
    db_payment = Payment(...)
    db.add(db_payment)
    await db.commit()
```

If this `commit` raises (unique violation on `yookassa_payment_id`, connection drop, the
`UndefinedColumn` case D-26 names for the pre-`0019` schema), a real payment exists at YooKassa
with **no row in our database and no log entry naming its id**. Every later notification for it
takes `webhook_payment_not_found` (`:501-503`) and returns `{"ok": false}` with HTTP 200, so
YooKassa stops retrying. Exposure is limited today because the user never receives the
confirmation URL, but the orphan is untraceable: the only place `payment.id` appears in a log is
`payment_created`, which is emitted *after* the commit.

Note this is exactly the class the phase already fixed once, in
`webhook_package_without_messages_count`.

**Fix:**

```python
    db.add(db_payment)
    try:
        await db.commit()
    except Exception as exc:
        # СЛЕД ОБЯЗАТЕЛЕН, И ИМЕННО ЗДЕСЬ. Платёж у ЮKassa уже СОЗДАН; без этой
        # записи он остаётся сиротой, которого не с чем сверить: его
        # идентификатор не попадает ни в один журнал, а `webhook_payment_not_found`
        # отвечает 200 и повторов не вызывает.
        await db.rollback()
        logger.error(
            "payment_row_not_written",
            user_id=user_id,
            yookassa_id=payment.id,
            kind=kind,
            plan=plan,
            amount=price,
            error_type=type(exc).__name__,
        )
        raise PaymentCreationError("Платёж не записан в базу") from exc
```

### WR-05: `handle_webhook` guards the package branch against a missing `messages_count` but the subscription branch has no equivalent guard on `plan`

**File:** `app/services/payment_service.py:548-555`, `:743-754`, `:905-909`
**Severity:** WARNING

**Issue:** The package branch refuses to claim a payment whose `messages_count` is empty, and
the reasoning (`:542-547`) is that claiming it would mark a payment delivered while delivering
nothing. The subscription branch has no counterpart. A row with `kind = 'subscription'` and
`plan IS NULL` is claimed as `succeeded` and then:

- if no subscription row exists → `_extend_subscription:746-752` inserts
  `Subscription(plan=db_payment.plan or "free", expires_at=next_expiry(None, now))`, i.e. the
  user is put on the **free** plan with a month of paid expiry. Money taken, nothing sold
  delivered — and because `_plan_price("free")` is `None` by construction, that row is
  precisely the permanently-unreadable-price input that triggers CR-01 on the next upgrade;
- if a subscription row exists → `_apply_extension:905-909` extends the period and returns.

`create_payment` cannot produce such a row today, but neither can it produce a subscription
payment with an empty `messages_count` — the guard next door exists for exactly the same
"opechatka in the caller / data fix / admin script" reason.

**Fix:** mirror the existing guard, using the same fail-without-claiming shape:

```python
    if db_payment.kind == KIND_SUBSCRIPTION and not db_payment.plan:
        # СИММЕТРИЯ С ПРОВЕРКОЙ ПАКЕТА ВЫШЕ И ПО ТОЙ ЖЕ ПРИЧИНЕ. Подписочный
        # платёж без плана выдать нечем: ветка первой вставки положила бы человека
        # на `free` с оплаченным месяцем, то есть пометила бы платёж проведённым,
        # ничего не выдав. Заявка не берётся — платёж остаётся незакрытым и
        # разбирается человеком.
        logger.error(
            "webhook_subscription_without_plan",
            yookassa_id=yookassa_id,
            user_id=db_payment.user_id,
        )
        return False
```

and drop the `or "free"` default at `:747` once the guard is in place — a default that invents a
plan is the thing that made the outcome silent.

### WR-06: `GET /api/billing/transactions` accepts unvalidated `limit` / `offset`

**File:** `app/routes/billing.py:30-38`
**Severity:** WARNING

**Issue:**

```python
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    ...
):
    txs = await get_transaction_history(db, user_id, limit=limit, offset=offset)
```

Neither bound is validated, and `get_transaction_history`
(`app/services/billing_service.py:172-194`) passes both straight into `.offset()` / `.limit()`.

- `?limit=-1` → PostgreSQL raises `LIMIT must not be negative` → unhandled 500 for any
  authenticated caller. (SQLite treats `-1` as unlimited, so the test suite cannot see this —
  the same dialect-divergence trap the phase documents elsewhere.)
- `?offset=-1` → PostgreSQL `OFFSET must not be negative` → 500.
- `?limit=100000000` → unbounded result set materialised into a list of dicts.

Every other list in this phase carries an explicit cap and a stated reason
(`PAYMENT_LIST_CAP`, `TRANSACTION_LIST_LIMIT`, `WORKER_LIST_CAP`); this is the one reader that
does not.

**Fix:**

```python
from fastapi import Query

@router.get("/transactions")
async def get_transactions(
    # Границы объявлены В СИГНАТУРЕ, а не проверены телом: FastAPI отвергает
    # выход за них 422 до входа в обработчик, и второму месту проверки завестись
    # негде. Потолок — тот же, что у остальных перечней раздела.
    limit: int = Query(50, ge=1, le=PAYMENT_LIST_CAP),
    offset: int = Query(0, ge=0),
    ...
):
```

### WR-07: `test_model_matches_head.py` compares column *names* only — the deploy gate passes on a type/nullability divergence

**File:** `tests/test_migrations/test_model_matches_head.py:89-102`, `:188-208`
**Severity:** WARNING

**Issue:** `missing_columns` is `sorted(set(mapped) - set(actual))` over
`PRAGMA table_info` names. The gate therefore accepts any revision whose column *exists* but
whose shape disagrees with the model. The concrete hazard is live in this very phase:
`0019` adds `switch_authorized` as `nullable=True`, and both `app/models/payment.py:48-53` and
the revision docstring argue at length that a `server_default` or `NOT NULL` here would be
wrong. If a future revision adds it (or re-adds it after the documented lossy `downgrade`) as
`NOT NULL`, this test stays green while `create_payment` starts failing on every package
purchase, which passes `switch_authorized=None` explicitly (`app/pages/billing.py:456`).

The file's own "ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ" section names the prod-divergence limit but not
this one, so a reader reasonably concludes the model/head comparison is total.

**Fix:** extend the comparison to the two attributes the phase actually reasons about, and
name the remaining boundary:

```python
def _table_shape(db_path: Path, table: str) -> dict[str, tuple[str, bool]]:
    """Имя колонки → (тип, признак NOT NULL). Имени МАЛО, и вот почему.

    Колонка `switch_authorized` обязана быть NULLABLE (D-28: NULL означает
    «правило не спрашивали», и это не то же самое, что «нет»). Ревизия,
    заведшая её NOT NULL, сверку по одним ИМЕНАМ прошла бы, а
    `create_payment` начал бы падать на КАЖДОЙ пакетной покупке, которая
    подаёт `None` явно.
    """
    conn = sqlite3.connect(db_path)
    try:
        return {
            row[1]: (row[2].upper(), bool(row[3]))
            for row in conn.execute(f"PRAGMA table_info({table})")
        }
    finally:
        conn.close()


def test_every_mapped_payment_column_keeps_its_nullability_at_head(db_at_head):
    shape = _table_shape(db_at_head, "payments")
    divergent = sorted(
        column.name
        for column in Payment.__table__.columns
        if column.name in shape and shape[column.name][1] == column.nullable
    )
    assert not divergent, (
        "нулевость отображённой колонки расходится с головной ревизией: "
        f"{divergent}"
    )
```

---

## Info

### IN-01: `converted_remainder` has no direct unit tests in the module that owns the arithmetic

**File:** `tests/test_application/test_subscription_period.py` (whole file), `app/application/billing/subscription_period.py:186-256`

**Issue:** `add_one_month`, `subscription_is_live`, `next_expiry` and `prorated_expiry` each get a
full boundary table in this file — every day of a common and a leap year, naive/aware pairs,
the exact-equality case, the one-day floor, the no-upper-cap case. `converted_remainder`, added
by 05-18 and the only new arithmetic on the money path, is not imported here at all. Its entire
coverage is integration assertions with `± 2 days` tolerance
(`tests/test_pages/test_billing_payment_errors.py:2312`,
`tests/test_services/test_payment_concurrency.py:470`), which cannot see a one-day truncation, a
February/December divergence, or a naive/aware mismatch.

**Fix:** add the same shape of table this file already uses for `prorated_expiry` — expired and
absent `current` return `now`; a live remainder never converts to zero days; naive and aware
`current` give the identical answer; `old_price == new_price` round-trips; the answer is
invariant across `month_days ∈ {28, 30, 31}` (which is what WR-01 shows the code actually does).

### IN-02: every conversion truncates the sub-day part of the paid remainder

**File:** `app/application/billing/subscription_period.py:143`, `:256`

**Issue:** `prorated_days` uses `int(...)`, which truncates toward zero. Because `month_days`
cancels (WR-01), a switch between two plans priced identically yields
`now + floor(remainder_in_days)` — up to 23 h 59 m 59 s of already-paid time is dropped. The
docstring promises "обещание «оплаченный остаток не сгорает» остаётся верным … меняется единица
измерения переноса, а не сам факт переноса" (`:219-225`), which is true in spirit and slightly
false in the last day. Small in money, but it is the kind of statement this phase has been
rewriting for five rounds.

**Fix:** either say so in one clause ("целая часть, поэтому неполный день переноса теряется —
цена того, что срок хранится днями") or round the conversion to the nearest day rather than
down.

### IN-03: dead guard in `converted_remainder`

**File:** `app/application/billing/subscription_period.py:245-247`

**Issue:**

```python
    base = countdown_base(current, now_utc)
    if base <= now_utc:
        return now_utc
```

`countdown_base` (`:117-121`) already returns `now_utc` whenever `base is None or base <= now_utc`,
so the condition can never be true — the branch is unreachable. Harmless, but it reads as a
second, independent expiry rule sitting next to the real one, which is the duplication this
module exists to prevent.

**Fix:** replace with a comment stating that the clamp is `countdown_base`'s job, or invert the
guard to `if base == now_utc: return now_utc` and say why (nothing to convert).

### IN-04: `subscription_prorating_skipped` is reused across two branches with two different `unreadable` vocabularies and different field sets

**File:** `app/services/payment_service.py:964-971` vs `:1029-1036`

**Issue:** The key reuse is argued at `:1026-1028` ("событие ровно то же"), but the two emissions
are not interchangeable to anyone reading the log:

| | refused branch (`:964`) | conversion branch (`:1029`) |
|---|---|---|
| `unreadable` values | `"price"` \| `"amount"` | `"price"` \| `"paid_plan_price"` |
| `granted_days` | emitted (as `None`) | absent |
| `price_basis` | emitted by the paired `subscription_plan_preserved` | absent |

`unreadable="price"` means "the *active* plan's price is unreadable" in both, but the second
value differs in meaning and in name, and only one of the two branches is followed by a second
record naming the outcome. An operator filtering on the key gets two different events with
overlapping value vocabularies and no field that distinguishes the branch.

**Fix:** add one discriminating field rather than a second key:

```python
            logger.warning(
                "subscription_prorating_skipped",
                stage="convert_remainder",   # vs stage="prorate_refused" выше
                ...
            )
```

---

_Reviewed: 2026-08-17T18:47:42Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

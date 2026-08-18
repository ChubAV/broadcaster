---
phase: 05-tarify
reviewed: 2026-08-18T10:05:14Z
depth: standard
files_reviewed: 46
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
  - tests/test_application/declared_invariants_without_witness.txt
  - tests/test_application/test_declared_invariants.py
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
  warning: 6
  info: 6
  total: 13
status: issues_found
---

# Phase 05-tarify: Code Review Report

**Reviewed:** 2026-08-18T10:05:14Z
**Depth:** standard
**Files Reviewed:** 46
**Status:** issues_found

## Summary

Round 7. Re-attacked the money path end to end (`create_payment` → YooKassa →
`handle_webhook` → `_claim_payment` → `_extend_subscription` → `_apply_extension` →
`subscription_period` arithmetic), plus the two artefacts this run added
(`capped_carryover` and the declared-invariant gate).

**What round 6's fixes actually closed, verified by reading the code, not the plans:**

- `CR-01` is genuinely closed. `capped_carryover`
  (`app/application/billing/subscription_period.py:333-393`) is a pure `min(countdown_base,
  add_one_month(now))`, the money path reads it rather than recomputing
  (`app/services/payment_service.py:1257`), the horizon is bounded at two calendar months
  from `now`, and two integration tests seed a 365-day horizon and assert both halves of
  the cost (`test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`,
  `test_an_upgrade_from_free_does_not_carry_the_whole_horizon`). I traced the money on
  both directions of `converted_remainder` (12×basic + 1×pro = 22 780 ₽ → ~140 days Pro;
  12×pro + 1×basic → ~1200 days Basic) — the arithmetic is now money-preserving in both
  directions, and `month_days` cancels exactly as WR-01 said.
- `WR-02` is closed: `refused = period_is_live and not db_payment.switch_authorized`
  (`:1080`) — a recorded `False` no longer outlives its own period.
- `WR-03` is closed by decision plus a real trace: `subscription_plan_downgraded`
  (`:1320-1333`) fires on the record-wins demotion.
- `IN-04` is closed: both `subscription_prorating_skipped` emissions carry a distinct
  constant `stage` field, and `test_the_refused_branch_names_its_own_stage_in_the_journal`
  asserts the *other* value, so the two cannot be collapsed silently.
- `IN-02` (sub-day truncation) is closed by declaration — `converted_remainder:250-257`
  now names the truncation with the number, exactly as the finding asked. Not re-reported.
- Per the round brief, `IN-03` is treated as refuted by run and is not re-raised.

**What does not hold up:**

1. `_plan_price` breaks the very contract its docstring exists to guarantee. Its
   promise — "`None` вместо исключения… 5xx на уведомлении запускает цикл повторов и
   оставляет платёж `pending` навсегда" — is not kept for malformed or non-list
   `PLAN_LIMITS`, which the same codebase repeatedly calls normal operation ("перечень
   тарифов правится окружением"). Proven by run, four ways. That is CR-01.
2. **Wave 18 introduced a fresh instance of this phase's signature defect class in the
   same run that built the gate against it.** `_extend_subscription:691-698` declares the
   05-01 prohibition "СОБЛЮДЕНА, а не переопределена: ни один разрешённый переход остатка
   не сжигает" — while `capped_carryover:359-372` and `_apply_extension:1238-1246`, both
   written by 05-22, declare the same branch an *exception* to that prohibition, and the
   suite's own green test burns ~11 months of paid time on an allowed transition. Two
   declarations in one module contradict each other; the newer one matches the code. The
   new gate passed it because the paragraph *names* a test that exists but does not cover
   the claim — the gate's declared blind spot, realised on its first round (WR-01).
3. The gate's scope excludes the INTENT stage of the money path. `app/pages/billing.py`
   (34 selected declarations, **34 without a witness**), `app/routes/billing.py` (10/10,
   including the webhook trust guard), `app/pages/common.py` (13/13, including the CSRF
   guard) and `app/services/billing_service.py` (6/6) are all outside `checked_modules()`,
   although `plan_switch.py` itself calls `app/pages/billing.py` one of the rule's two
   stages (WR-02).
4. `WR-04`, `WR-05`, `WR-06`, `WR-07` of round 6 were not addressed and are re-reported
   verbatim in substance (WR-03…WR-06 below), each re-verified against the current tree.

Known and recorded debt (second intent-cap race window, `PENDING_INTENT_TTL_HOURS`
demotion window, `uq_subscriptions_active_user` not built on prod, D-26 schema
divergence) is **not** re-reported.

---

## Critical Issues

### CR-01: `_plan_price` raises instead of returning `None` on a malformed plan list — 500 on the YooKassa notification, payment stuck `pending` forever

**File:** `app/services/payment_service.py:905-937` (declaration `:906-927`, body `:928-936`)
**Severity:** BLOCKER

**Issue:**

`_plan_price` exists for exactly one reason, stated in its own docstring:

> `None` ВМЕСТО ИСКЛЮЧЕНИЯ — ТРЕБОВАНИЕ ВЫЗЫВАЮЩЕГО… Необработанное исключение там
> означает 5xx на уведомлении, а 5xx запускает цикл повторов и оставляет платёж `pending`
> навсегда: класс отказа, уже стоивший фазе находки `WR-04` раунда 2. **Перечень тарифов
> правится окружением**, а действующий план записан в строке подписки — разойтись они
> могут в любую сторону и без нашего участия.

The `try` covers only the `Decimal` conversion. The iteration itself is unguarded:

```python
    for plan in get_settings().parsed_plan_limits:   # <- outside the try
        if plan.get("id") != plan_id:                # <- assumes dict entries
            continue
        try:
            price = Decimal(str(plan.get("price")))
        except (InvalidOperation, TypeError, ValueError):
            return None
        return price if price > 0 else None
    return None
```

`Settings.parsed_plan_limits` (`app/config.py:119-121`) is a bare `json.loads` of the
`PLAN_LIMITS` env string, with no validation and no schema. Run against the real function
with `get_settings` patched to a real `Settings`:

```
malformed json         -> RAISED JSONDecodeError: Expecting value: line 1 column 33
json object not list   -> RAISED AttributeError: 'str' object has no attribute 'get'
list of strings        -> RAISED AttributeError: 'str' object has no attribute 'get'
null                   -> RAISED TypeError: 'NoneType' object is not iterable
```

Note that `JSONDecodeError` subclasses `ValueError`, so it *would* have been caught had
the call sat inside the existing `except` — the guard is one line away from working.

**Why this is a BLOCKER and not a config-hygiene note.** Trace the reachable path:

1. Operator edits `PLAN_LIMITS` (rename a plan, drop `pro` from sale, add a trailing
   comma). The phase names this as routine in three separate docstrings.
2. A subscription payment for a *different* plan than the current subscription is
   confirmed. `_apply_extension` reaches `_plan_price` at `:1116` (refused branch) or
   `:1253-1254` (convert branch).
3. The exception propagates through `_extend_subscription` → `handle_webhook` →
   `app/routes/billing.py:200-202` → **HTTP 500**.
4. `await db.commit()` at `:612` is never reached, so the `_claim_payment` UPDATE rolls
   back and the row returns to `pending`.
5. YooKassa retries the notification. Same config, same 500. **Forever.** Money taken,
   nothing delivered, and the payment never leaves `pending` — the precise outcome
   T-05-104 and the `capped_carryover` docstring ("⚠️ ИСКЛЮЧЕНИЯ ЗДЕСЬ НЕДОПУСТИМЫ НИ В
   КАКОМ ВИДЕ") declare impossible.

The same unguarded property also 500s `GET /billing` (`app/pages/billing.py:174`) and
`POST /billing/subscribe` (`:315`), and `parsed_message_packages` has the identical shape
for `GET /api/billing/packages` and `POST /billing/purchase` — but those cost a page, not
a stuck payment.

**Fix:** make the reader total, at the one place the money path already trusts to be
total. Do not "validate config at startup" instead — the phase's own reasoning is that
config and DB are allowed to diverge *at runtime*, and a startup check cannot see that.

```python
def _plan_price(plan_id: str | None) -> Decimal | None:
    """...

    ⚠️ НЕПРИГОДНЫМ СЧИТАЕТСЯ И САМ ПЕРЕЧЕНЬ, А НЕ ТОЛЬКО ЦЕНА В НЁМ. `PLAN_LIMITS`
    — строка окружения, разбираемая `json.loads` без схемы: битая запятая даёт
    `JSONDecodeError`, объект вместо списка и список строк дают `AttributeError`,
    `null` — `TypeError`. Прежняя редакция ловила только отказ `Decimal`, то есть
    держала обещание «`None` вместо исключения» ровно для той половины входа,
    которую правит не оператор. Вторая половина роняла обработчик уведомления
    пятисоткой, и платёж оставался `pending` навсегда (T-05-104) — тот самый
    исход, ради невозможности которого функция и заведена.
    Закреплено `test_a_malformed_plan_list_does_not_break_the_notification`.
    """
    try:
        plans = get_settings().parsed_plan_limits
        for plan in plans:
            if not isinstance(plan, dict) or plan.get("id") != plan_id:
                continue
            price = Decimal(str(plan.get("price")))
            return price if price > 0 else None
    except (InvalidOperation, TypeError, ValueError, AttributeError):
        # ЖУРНАЛ ОБЯЗАТЕЛЕН: расхождение конфига с базой — наша беда, и без следа
        # «дни посчитаны по-старому» неотличимо от «конфиг сломан целиком».
        logger.error("plan_limits_unreadable", plan_id=plan_id)
        return None
    return None
```

Add the regression next to `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`,
parametrised over the four shapes above, asserting `handle_webhook` returns `True`, the
payment reaches `succeeded`, and the expiry moved — i.e. the notification survives.
Consider the same treatment for `parsed_message_packages` at `app/routes/billing.py:26-27`
and `app/pages/billing.py:433`.

---

## Warnings

### WR-01: `_extend_subscription` declares the 05-01 prohibition OBSERVED while the same module, 550 lines away, declares the same branch an EXCEPTION to it — and the suite's own green test proves the exception

**File:** `app/services/payment_service.py:684-698` (the claim),
`app/application/billing/subscription_period.py:359-372` and
`app/services/payment_service.py:1238-1246` (the contradiction),
`tests/test_pages/test_billing_payment_errors.py:767-810` (the named witness)
**Severity:** WARNING

**Issue:** `_extend_subscription`'s docstring, as edited by plan 05-24, ends:

> Прохибиция плана `05-01` — «MUST NOT сжигать неистраченный остаток уже оплаченного
> периода» — тем самым **СОБЛЮДЕНА, а не переопределена: ни один разрешённый переход
> остатка не сжигает.** … что разрешённый переход остатка не сжигает —
> `test_an_upgrade_does_not_burn_the_paid_remainder`.

Plan 05-22, in the same run, wrote the opposite into `capped_carryover`:

> Остаток ДЛИННЕЕ месяца сгорает в части, превышающей месяц: человек, предоплативший год
> … теряет около одиннадцати месяцев оплаченного времени. Это **ИСКЛЮЧЕНИЕ из прохибиции
> плана `05-01`** … **а не её соблюдение**, и записано оно исключением намеренно.

Both statements describe the same branch: `period_is_live and db_payment.plan !=
subscription.plan` — an **allowed** transition (the refused branch returned at `:1224`).
`capped_carryover` is reached from inside it at `:1257`. So "ни один разрешённый переход
остатка не сжигает" is false, and it is false against the project's *own green test*:
`test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`
(`tests/test_pages/test_billing_payment_errors.py:2752-2818`) seeds a 365-day remainder
and asserts the result is `<= add_one_month(add_one_month(now)) + 2 days`. That is ~305
days of already-paid time burned, on an allowed transition, asserted as desired
behaviour.

The named witness cannot see it: `test_an_upgrade_does_not_burn_the_paid_remainder`
(`:790-810`) seeds 25 days of `basic` with both prices readable — it exercises only the
`converted_remainder` leg. This is the declared blind spot of the new gate ("Абзац,
называющий существующий, но НЕ ТОТ тест, гейт пропустит зелёным") firing on the gate's
first round, on a paragraph written in the same run.

This is the round-7 instance of the class that produced rounds 4, 5 and 6 findings. It is
reported as a declaration defect, not a behaviour defect: the code is bounded and correct.

**Fix:** make the claim match the branch set, and name both witnesses.

```
    Правило: повышение тарифа разрешено; понижение при действующей подписке не
    предлагается карточкой и не продаётся гардом `POST /billing/subscribe`.

    ⚠️ ПРОХИБИЦИЯ 05-01 СОБЛЮДЕНА С ОДНИМ НАЗВАННЫМ ИСКЛЮЧЕНИЕМ, И ВЕЛИЧИНА ЕГО
    ЗАПИСАНА ЧИСЛОМ. Переход, у которого обе цены читаются, остаток НЕ СЖИГАЕТ —
    он переносится по деньгам (`converted_remainder`), закреплено
    `test_an_upgrade_does_not_burn_the_paid_remainder`. Переход, у которого хотя
    бы одну цену прочитать нельзя, идёт на `capped_carryover` (форма
    `cap-one-month`, решение владельца, план 05-22) и переносит НЕ БОЛЕЕ одного
    календарного месяца остатка: предоплаченный год теряет около одиннадцати
    месяцев. Это ИСКЛЮЧЕНИЕ из прохибиции, допущенное сознательно, и
    утверждать здесь её безусловное соблюдение — ровно тот класс объявления,
    которого код не исполняет, за который фаза получила раунды 4, 5 и 6.
    Закреплено `test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`
    и `test_an_upgrade_from_free_does_not_carry_the_whole_horizon`.
```

### WR-02: the declared-invariant gate excludes the INTENT half of the money path — 63 selected declarations, all 63 without a witness, none of them under the ratchet

**File:** `tests/test_application/test_declared_invariants.py:66-69`, `:293-298`
**Severity:** WARNING

**Issue:** The gate defines its own scoping rule at `:66-68`:

> Модули денежного пути ВНЕ пакета. Выводить их неоткуда — их приходится называть, **и
> молчание о них было бы дырой в гейте**: денежный путь проходит через них.

and then names exactly one: `EXTRA_CHECKED_MODULES = ("app/services/payment_service.py",)`.

But `plan_switch.py:11-13` states the rule has **two** stages and names them: "`app/pages/billing.py` (стадия НАМЕРЕНИЯ) и `app/services/payment_service.py` (стадия ПРИМЕНЕНИЯ)". Only the second is checked. Running the gate's own helpers against the unchecked modules:

```
app/pages/billing.py           selected: 34   without witness: 34
app/pages/common.py            selected: 13   without witness: 13
app/routes/billing.py          selected: 10   without witness: 10
app/services/billing_service.py selected:  6   without witness:  6
```

These are not decorative paragraphs. They include the webhook trust guard's
`⚠️ СПИСОК АДРЕСОВ ЧИТАЕТСЯ СПРАВА, А НЕ СЛЕВА` and `⚠️ АДРЕС ПИРА ИСТОЧНИКОМ НЕ СЛУЖИТ
НИ ПРИ КАКОЙ НАСТРОЙКЕ` (`app/routes/billing.py`), the CSRF guard's
`⚠️ НАЗВАННАЯ ГРАНИЦА ЗАЩИТЫ` (`app/pages/common.py::is_same_origin`), and
`⚠️ ОБРАБОТЧИК НЕ ПИШЕТ В БД НИ ПРИ КАКИХ УСЛОВИЯХ` (`app/pages/billing.py::billing_page`).
Tests for several of them exist (`test_billing_webhook_proxy_headers.py`,
`test_billing_webhook_source.py`) — the paragraphs simply do not name them, which is
precisely the condition the gate was built to detect.

`test_the_checked_set_covers_every_module_of_the_billing_package` (`:552-562`) only proves
the *package* is covered; nothing asserts anything about `EXTRA_CHECKED_MODULES`
completeness, so the hole is invisible to the suite.

**Fix:** extend the set and land the new debt in the ledger in the same commit, raising
`WITHOUT_WITNESS_CEILING` **once, with the numbers written down**, so that subsequent
rounds ratchet from a real baseline rather than from a scoped-down one:

```python
# Модули денежного пути ВНЕ пакета. Выводить их неоткуда — их приходится называть,
# и молчание о них было бы дырой в гейте. Перечень отвечает ДВУМ стадиям правила,
# названным в `plan_switch.py`: применение (`payment_service`) и НАМЕРЕНИЕ
# (`pages/billing`), плюс вход уведомления и общий гард источника, через которые
# денежный путь проходит целиком.
EXTRA_CHECKED_MODULES = (
    "app/services/payment_service.py",
    "app/pages/billing.py",
    "app/routes/billing.py",
    "app/services/billing_service.py",
    "app/pages/common.py",
)
```

and add the missing counterpart control:

```python
def test_the_checked_set_names_both_stages_of_the_rule():
    """Гейт, видящий одну стадию из двух, проверяет половину денежного пути."""
    checked = set(checked_modules())
    for stage in ("app/services/payment_service.py", "app/pages/billing.py"):
        assert stage in checked, f"стадия правила вне проверяемого множества: {stage}"
```

### WR-03: no error handling or log around the DB write that follows a successful YooKassa `create` (round 6 `WR-04`, unaddressed)

**File:** `app/services/payment_service.py:404-427`
**Severity:** WARNING

**Issue:** Re-verified against the current tree — unchanged. The module argues at length
(`:348-363`, T-05-49) that the SDK call must precede the DB write and handles every
failure of the SDK call. It handles none of the DB write:

```python
    db_payment = Payment(...)
    db.add(db_payment)
    await db.commit()
```

If this `commit` raises (unique violation on `yookassa_payment_id`, connection drop, the
`UndefinedColumn` case D-26 names for the pre-`0019` prod schema), a real payment exists
at YooKassa with **no row in our database and no log entry naming its id**. Every later
notification takes `webhook_payment_not_found` (`:536`) and returns `{"ok": false}` with
HTTP 200, so YooKassa stops retrying. The only place `payment.id` reaches a log is
`payment_created` (`:419-427`), emitted *after* the commit.

Note this is the class the phase already fixed once, in
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

### WR-04: the subscription branch of `handle_webhook` has no guard on `plan`, and the insert branch invents `"free"` (round 6 `WR-05`, unaddressed)

**File:** `app/services/payment_service.py:586-593` (the package guard), `:866` (the
invented default), `:1046-1049` (the extend path)
**Severity:** WARNING

**Issue:** Re-verified — unchanged. The package branch refuses to claim a payment whose
`messages_count` is empty, reasoning (`:579-585`) that claiming it would mark a payment
delivered while delivering nothing. The subscription branch has no counterpart. A row with
`kind = 'subscription'` and `plan IS NULL` is claimed `succeeded` and then:

- no subscription row → `_extend_subscription:862-870` inserts
  `Subscription(plan=db_payment.plan or "free", expires_at=next_expiry(None, now))` — the
  user is put on **free** with a month of paid expiry. Money taken, nothing sold delivered;
- a subscription row exists → `_apply_extension:1046-1049` extends the period and returns
  with the plan untouched.

This round adds a second consequence the previous review could not state: because
`_plan_price("free")` is `None` **by construction** (`"0.00"` is not `> 0`), the row this
default creates is exactly the permanently-unreadable-price input that forces every later
upgrade down the `capped_carryover` leg — the branch whose *declared* cost is burning
everything past one month of remainder (WR-01). The phase's own test
`test_an_upgrade_from_free_does_not_carry_the_whole_horizon` names the mechanism
explicitly: "ЛЮБАЯ строка подписки на `free` с живым сроком берёт ветку отката на первом
же платном повышении, без единой правки конфига и без гонки." The only production maker
of such a row is the `or "free"` default flagged here.

Repeated null-plan payments compound it: `_apply_extension:1046-1049` adds a month per
payment while leaving `plan = "free"`, so the free horizon grows without bound and is then
truncated to one month on the first real upgrade.

**Fix:** mirror the existing guard, using the same fail-without-claiming shape, and drop
the invented default once it is in place:

```python
    if db_payment.kind == KIND_SUBSCRIPTION and not db_payment.plan:
        # СИММЕТРИЯ С ПРОВЕРКОЙ ПАКЕТА ВЫШЕ И ПО ТОЙ ЖЕ ПРИЧИНЕ. Подписочный
        # платёж без плана выдать нечем: ветка первой вставки положила бы человека
        # на `free` с оплаченным месяцем — то есть пометила бы платёж проведённым,
        # ничего не выдав, — и та же строка становится входом в ветку
        # `capped_carryover` при следующем повышении. Заявка не берётся: платёж
        # остаётся незакрытым и разбирается человеком.
        logger.error(
            "webhook_subscription_without_plan",
            yookassa_id=yookassa_id,
            user_id=db_payment.user_id,
        )
        return False
```

### WR-05: `GET /api/billing/transactions` accepts unvalidated `limit` / `offset` (round 6 `WR-06`, unaddressed)

**File:** `app/routes/billing.py:30-38`, `app/services/billing_service.py:172-194`
**Severity:** WARNING

**Issue:** Re-verified — unchanged.

```python
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    ...
):
    txs = await get_transaction_history(db, user_id, limit=limit, offset=offset)
```

Both bounds go straight into `.offset()` / `.limit()` (`billing_service.py:179-180`).

- `?limit=-1` → PostgreSQL `LIMIT must not be negative` → unhandled 500 for any
  authenticated caller. SQLite treats `-1` as unlimited, so the suite cannot see this —
  the same dialect-divergence trap this phase documents in four other places.
- `?offset=-1` → PostgreSQL `OFFSET must not be negative` → 500.
- `?limit=100000000` → unbounded result set materialised into a list of dicts.

Every other list in this phase carries an explicit cap and a stated reason
(`PAYMENT_LIST_CAP`, `TRANSACTION_LIST_LIMIT`, `WORKER_LIST_CAP`); this is the one reader
that does not.

**Fix:**

```python
from fastapi import Query
from app.constants import PAYMENT_LIST_CAP

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

### WR-06: `test_model_matches_head.py` compares column *names* only, and only for `payments` (round 6 `WR-07`, unaddressed)

**File:** `tests/test_migrations/test_model_matches_head.py:89-102`, `:188-208`
**Severity:** WARNING

**Issue:** Re-verified — unchanged. `missing_columns` is `sorted(set(mapped) -
set(actual))` over `PRAGMA table_info` **names**. The gate therefore accepts any revision
whose column exists but whose shape disagrees with the model.

The concrete hazard is live in this phase: `0019` adds `switch_authorized` as
`nullable=True`, and both `app/models/payment.py:57` and the revision docstring argue at
length that a `server_default` or `NOT NULL` here would be wrong (D-28: `NULL` means "the
rule was not asked", which is not "no"). A future revision adding it — or re-adding it
after the documented lossy `downgrade` — as `NOT NULL` keeps this test green while
`create_payment` starts failing on **every package purchase**, which passes
`switch_authorized=None` explicitly (`app/pages/billing.py:456`).

Second, narrower gap found this round: the fixture only creates and compares `payments`
(`PAYMENTS_AT_START`, `:72-86`). The `subscriptions` table gained a model-level
`__table_args__` index in this phase (`app/models/subscription.py:20-28`) and is not
compared to head here at all.

The file's own "ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ" section names the prod-divergence limit but
neither of these, so a reader reasonably concludes the model/head comparison is total.

**Fix:** extend the comparison to the attribute the phase actually reasons about, and name
the remaining boundary:

```python
def _table_shape(db_path: Path, table: str) -> dict[str, tuple[str, bool]]:
    """Имя колонки → (тип, признак NOT NULL). Имени МАЛО, и вот почему.

    Колонка `switch_authorized` обязана быть NULLABLE (D-28: NULL означает
    «правило не спрашивали», и это не то же самое, что «нет»). Ревизия,
    заведшая её NOT NULL, сверку по одним ИМЕНАМ прошла бы, а `create_payment`
    начал бы падать на КАЖДОЙ пакетной покупке, которая подаёт `None` явно.
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
        f"нулевость отображённой колонки расходится с головной ревизией: {divergent}"
    )
```

Add the `subscriptions` counterpart with the same fixture, or state in the file header
that only `payments` is compared and why.

---

## Info

### IN-01: an expired or config-dropped plan still renders as the user's live entitlement

**File:** `app/pages/billing.py:174-188`, `:207-216`

**Issue:** `current_plan_id` comes from `quota["plan"]`, which `get_shell_context` fills
from the subscription row **regardless of whether it expired**
(`app/pages/common.py:507-514`, `:549`). So a user whose Pro period lapsed still sees Pro
limits on all four meters and the "ВАШ ПЛАН" tag on the Pro card, next to the "срок истёк"
badge. Separately, `current_plan = next((...), {})` (`:179-181`) falls back to an **empty
dict**, so a plan id that has left `PLAN_LIMITS` renders all four axes as `limit=None` →
"без ограничений". `plan_usage`'s docstring authorises a missing *key* to read as
unlimited ("опечатка обязана стоить одной ненарисованной шкалы"), which is a much weaker
claim than "every axis unlimited". D-08 means nothing is enforced, so this is display
only — but the display is the entire deliverable of this phase.

**Fix:** decide the semantics explicitly. Either pass `FREE_PLAN_ID`'s record when the
period is expired or the id is unknown, or add a caption naming the state
("тариф снят с продажи — лимиты не показываются") rather than showing unlimited.

### IN-02: `decided_by` in `subscription_plan_downgraded` is constant by construction, and unlike its neighbour is not marked as such

**File:** `app/services/payment_service.py:1320-1333`

**Issue:** The branch is only reachable when `refused` is `False`. In the `decided_by ==
"rule"` case, `refused` was computed by the same `switch_is_refused` with the same
arguments, so the guard at `:1300-1302` cannot be `True`. The field is therefore always
`"recorded_answer"`. The sibling field `period_was_live` got an explicit "ПОЛЕ ПОСТОЯННО
ПО ПОСТРОЕНИЮ И ОСТАВЛЕНО НАМЕРЕННО" comment (`:1327-1332`); `decided_by` did not, so the
next reader will treat it as discriminating.

**Fix:** one clause next to `decided_by=decided_by` saying it is constant here and why it
is kept (uniform shape with `subscription_plan_preserved`), or drop it.

### IN-03: dead code and a redundant alias in the new gate

**File:** `tests/test_application/test_declared_invariants.py:383-397` (`render_ledger`),
`:124-127` (`Declaration.opening`)

**Issue:** `render_ledger` is called by no test and by nothing else in the tree — it was
the one-shot printer used to seed the ledger. `Declaration.opening` returns
`self.fingerprint` verbatim; two names for one value in a module whose whole subject is
"one declaration, one place".

**Fix:** delete `render_ledger` (the seeding procedure belongs in the plan, not the
suite), or keep it and name it in the module docstring as the ledger's printer. Collapse
`opening` into `fingerprint`.

### IN-04: the ledger parser fails closed on a separator collision, taking the gate down instead of reporting

**File:** `tests/test_application/test_declared_invariants.py:342-357`, ledger format
`LEDGER_SEPARATOR = "::"` (`:80`)

**Issue:** `ledger_entries()` splits on `"::"` and raises `AssertionError` when the result
is not exactly four parts. Fingerprints are the first 60 characters of a real paragraph
and reasons are free text; either may one day contain `::` (a doubled colon, a `C++`
reference, a path fragment). The failure then surfaces as a hard error in **five** tests
at once, none of which name the offending line usefully.

**Fix:** `line.split(LEDGER_SEPARATOR, 3)` with the reason taking the remainder, or use a
separator that cannot appear in prose (`\t`). Either way, name the constraint in the
ledger header.

### IN-05: `first_payment_at` mislabels a renewal as "первый платёж" once the journal is truncated

**File:** `app/templates/billing/balance.html:217-222`,
`app/templates/billing/includes/payment_row.html:28-31`, `:43-45`

**Issue:** The macro's contract states "в журнале, отсортированном по дате убыванием,
самая ранняя строка плана и есть его первый платёж". That holds only *within the window*.
`get_payment_history` caps at `PAYMENT_LIST_CAP = 200` and the page already knows it may
be truncated (`payments_truncated`). Past 200 payments, the oldest visible row for a plan
is labelled "первый платёж" although the real first payment is off-screen.

**Fix:** suppress the label when `payments_truncated` is true, or state the boundary in
the macro's docstring next to the existing contract sentence.

### IN-06: `/var/run/docker.sock` is mounted read-write into `web` (pre-dates this phase)

**File:** `docker-compose.prod.yml:89-90`, `:120-121`

**Issue:** The internet-facing application container gets the host Docker socket, which is
root-equivalent on the host. Any RCE in the FastAPI process escalates to full host
compromise. `celery-worker-default` plausibly needs it for `wa_container_manager`; `web`
mounting it as well widens the blast radius to the request-handling process. This is
outside the phase's change set — the only phase-05 edit to this file was pinning
`YOOKASSA_WEBHOOK_CLIENT_IP_HEADER` (commit 48d79c8) — and is recorded here for the
security backlog rather than as phase work.

**Fix:** move container management behind the worker only, or front the socket with a
proxy restricting it to the container lifecycle verbs actually used.

---

_Reviewed: 2026-08-18T10:05:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

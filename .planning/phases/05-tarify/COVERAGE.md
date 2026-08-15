# API Coverage — ЮKassa (`yookassa` 3.10.0)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.

**Why this file exists even though the detector said `detected: false`.** The
deterministic scan (`api-coverage.cjs`) is English-lexicon and this phase's scope
text (ROADMAP + CONTEXT) is Russian, so it returned `{"detected":false,"signals":[]}`
— the same lexicon blindness that made the edge probe return three `unclassified`
rows. The phase unambiguously integrates an external payment API (`app/services/payment_service.py`
already calls `yookassa.Payment.create`, and this phase adds a subscription branch
plus a webhook source guard), so the matrix is produced deliberately rather than
skipped on a false negative.

**Baseline re-decided from scratch.** The message-package integration that already
exists is NOT treated as a carried-over set of opt-outs; every capability below is
re-decided for the subscription surface as well.

| capability | decision | reason |
|---|---|---|
| `payments.create` | INTEGRATE | Core of D-01 — subscription purchase/renewal goes through the same `create_payment` contour as message packages, branched by `kind`. |
| `payments.confirmation` (type `redirect`) | INTEGRATE | D-20 — real form POST returns 302 to `confirmation_url`. |
| `payments.metadata` | INTEGRATE | Carries `user_id` / `kind` / `plan` so the two purchase kinds are distinguishable in the merchant cabinet. Never the source of truth for the handler (the `payments.kind` column is). |
| webhook notification `payment.succeeded` | INTEGRATE | The single writer of `Subscription.expires_at` (D-05). |
| webhook notification `payment.canceled` | INTEGRATE | D-16 — without it a rejected payment stays `pending` forever and Success Criterion 3 shows a falsehood. |
| `SecurityHelper.is_ip_trusted` | INTEGRATE | The only authenticity mechanism the installed SDK exposes; closes the unauthenticated-webhook hole this phase widens. |
| `payments.find_one` (re-read status) | OPT-OUT | not needed yet — the webhook is the single writer (D-05); tracked as a second anti-spoofing layer for a follow-up phase |
| `payments.list` | OPT-OUT | not needed — the local `payments` table is the journal of record for BILL-07 (D-14); a remote list would be a second source of the same truth. |
| `payments.capture` (two-stage) | OPT-OUT | not needed — `capture: True` is set at creation, so no separate capture step exists in this product. |
| `payments.cancel` | OPT-OUT | not needed — no product path cancels a payment from our side; cancellation originates at ЮKassa or the payer. |
| `refunds.create` / `refunds.get` / `refunds.list` | OPT-OUT | explicitly out of scope — «Возвраты средств» is a named Deferred Idea in `05-CONTEXT.md`; neither the model nor the webhook knows a refund today. |
| webhook notification `refund.succeeded` | OPT-OUT | explicitly out of scope — follows the refunds opt-out above; unknown events return `False` by design. |
| `receipts.*` (54-ФЗ фискализация) | OPT-OUT | explicitly out of scope — «Чеки и фискализация платежей» is a named Deferred Idea; requires an owner decision this phase did not take. |
| saved payment methods / recurring autopayments | OPT-OUT | explicitly out of scope — «Автопродление подписки» is a named Deferred Idea; BILL-05 says only «может продлить». |
| `webhooks.*` (event-subscription management API) | OPT-OUT | not needed — the merchant is not on OAuth, so event subscription is a cabinet setting the owner toggles by hand (`user_setup` in plan 05-06), not an API call. |
| `payouts.*` | OPT-OUT | not needed — Broadcaster receives money, it does not disburse it; no marketplace or self-employed payout surface exists. |
| `deals.*` (безопасная сделка) | OPT-OUT | not needed — no escrow/marketplace model in the product. |
| `personal_data.*` | OPT-OUT | not needed — only required by the payouts surface, which is opted out above. |
| `invoices.*` | OPT-OUT | not needed — no invoice/счёт flow exists in the product or the design mockup. |
| `sbp_banks` | OPT-OUT | not needed — confirmation is `redirect` only; ЮKassa's own payment page owns method selection. |
| `settings` (`me`) | OPT-OUT | not needed — shop identity is configured through `YOOKASSA_SHOP_ID` / `YOOKASSA_SECRET_KEY`; no runtime introspection is used. |

**Non-existent capability (documented for the record):** `SecurityHelper.verify_webhook_signature`
appears in Context7's documentation for this SDK but **does not exist** in the
installed `yookassa==3.10.0` (`security_helper.py` has exactly two methods, both
IP-based). It is not opted out — there is nothing to opt out of. Any plan task
importing it is wrong by construction.

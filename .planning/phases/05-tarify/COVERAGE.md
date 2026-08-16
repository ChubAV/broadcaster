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

---

## Line-by-line reconciliation against the code (plan 05-06, task 3, 2026-08-16)

Every INTEGRATE row was checked against `app/` at the end of the phase, and every
OPT-OUT row was checked for the opposite failure — a capability implemented «заодно»,
without a decision. An unplanned implementation is as much an unclosed question as a
missed one.

**INTEGRATE — all six have an implementation:**

| capability | implementation | verified |
|---|---|---|
| `payments.create` | `YooPayment.create(...)` — `app/services/payment_service.py:95` | ✅ the only SDK payment call in the project |
| `payments.confirmation` (type `redirect`) | `{"type": "redirect", "return_url": ...}` — `app/services/payment_service.py:98-101`; consumed as `RedirectResponse(..., 302)` — `app/pages/billing.py:202` (подписка) и `:264` (пакеты) | ✅ both purchase kinds |
| `payments.metadata` | `metadata` собирается по ветке `kind` — `app/services/payment_service.py:80-92`, передаётся `:104` | ✅ несёт `user_id`/`kind`/`plan`; источником истины на вебхуке НЕ служит (`:158`) |
| webhook `payment.succeeded` | `KNOWN_EVENTS` — `app/services/payment_service.py:41-46`; ветка успеха `:212-245`; `_extend_subscription` `:215-216` | ✅ единственный писатель `expires_at` (D-05) |
| webhook `payment.canceled` | `KNOWN_EVENTS` `:44`; ветка отмены `:185-210` | ⚠️ **зелёная в тестах, НЕ проверена в проде** — см. ниже |
| `SecurityHelper.is_ip_trusted` | `_is_trusted_source` — `app/routes/billing.py:101`; вызов гарда `:152-158` | ✅ стоит до `request.json()`, вне `try`, отказ остаётся 403 |

**OPT-OUT — ни одна не реализована «заодно».** Проверено grep'ом по `app/`: единственный
вызов SDK во всём приложении — `YooPayment.create` (`app/services/payment_service.py:95`),
поэтому `payments.find_one`, `payments.list`, `payments.capture` и `payments.cancel`
отсутствуют по построению (`capture: True` ставится при создании — `:102`, отдельного шага
захвата нет, ровно как записано в матрице). `refunds.*`, `receipts.*`, `payouts.*`,
`deals.*`, `personal_data.*`, `invoices.*`, `sbp_banks`, `settings (me)`, сохранённые
способы оплаты и `webhooks.*` не встречаются в `app/` ни одной строкой. `KNOWN_EVENTS`
содержит ровно два события, остальные пять объявленных SDK возвращают `False`
(`app/services/payment_service.py:39-46`).

**⚠️ Оговорка к строке `payment.canceled`, без которой матрица врёт.** Решение INTEGRATE
исполнено В КОДЕ и покрыто тестами, но состав рассылаемых событий задаётся ВНЕ
репозитория и кодом не проверяется (T-05-33). Владелец **не подтвердил** включение
подписки на это событие в кабинете ЮKassa (D-27). Пока она не включена, уведомление об
отмене просто не приходит, отменённый платёж в проде остаётся `pending` навсегда, и
критерий 3 фазы на боевом стенде показывает неправду. Включение: Личный кабинет ЮKassa →
Интеграция → HTTP-уведомления → выбор событий; URL уведомления обязан указывать на
`POST /api/billing/webhook` боевого домена.

**⚠️ Вторая оговорка ко всем шести строкам.** Решением D-26 (`defer-deploy`) ревизия `0017`
на боевую базу не выкачена — прод остаётся на `0012`. Колонок `payments.kind` и
`payments.plan` там нет, `messages_count` всё ещё `NOT NULL`, поэтому в проде НЕ работает
ни одна строка подписочной ветки: платёж не запишется. Матрица описывает состояние
репозитория, а не боевого стенда.

**⚠️ Третья оговорка — к строке `SecurityHelper.is_ip_trusted`.** Гард в проде читает адрес
заголовком, а не из `request.client.host`, поэтому до выката в `.env` прода обязана быть
задана переменная `YOOKASSA_WEBHOOK_CLIENT_IP_HEADER=X-Real-IP`. Без неё гард увидит адрес
контейнера nginx и отвергнет **каждое** настоящее уведомление, молча остановив приём
денег. Аварийный выход — `YOOKASSA_WEBHOOK_VERIFY_IP=false`. Правок nginx или
docker-compose не требуется: nginx проекта уже ставит `proxy_set_header X-Real-IP
$remote_addr` на каждом location, то есть затирает присланное клиентом.

> **ЗАКРЫТА планом `05-07`.** Текст выше оставлен как есть намеренно — он
> описывает состояние, в котором фаза сдавалась, и вычеркнуть его значило бы
> стереть причину, по которой мера понадобилась. Но организационной меры
> («до выката в `.env` прода обязана быть задана переменная») больше нет:
> умолчание переехало в `app/config.py`, а значение — в `docker-compose.prod.yml`.
> Сверка ниже.

---

## Сверка после закрытия гэпа 1 (план `05-07`, 2026-08-16)

Матрица выше **не перегенерирована**: гэп 1 не менял состав возможностей, он
менял то, исполняется ли принятое по ним решение. Затронуты ровно две строки.

**`SecurityHelper.is_ip_trusted` — решение `INTEGRATE` в силе, реализация та же.**
Изменился ИСТОЧНИК адреса, который в неё попадает. Прежде гард имел ветку «имя
заголовка не настроено → читать `request.client.host`», и на боевом стенде эта
ветка была не запасной, а основной: умолчание было пустым, а uvicorn запущен с
`--forwarded-allow-ips=*`, из-за чего адрес пира — левый элемент
`X-Forwarded-For`, то есть значение вызывающего. Проверка исполнялась над
адресом, который присылал сам атакующий. Ветка удалена целиком: ненастроенное
имя заголовка теперь означает «источник не подтверждён» и отвергает каждое
уведомление, а доверие может дать только заголовок, который свой прокси
ПЕРЕЗАПИСЫВАЕТ.

Третья оговорка внизу файла помечена закрытой: она была ОРГАНИЗАЦИОННОЙ мерой
(«не забыть задать переменную перед выкатом»), а стала свойством двух артефактов —
умолчание `X-Real-IP` в `app/config.py` и явная запись
`YOOKASSA_WEBHOOK_CLIENT_IP_HEADER` в `docker-compose.prod.yml`. Человеческим
остался ровно один пункт, и он не про конфигурацию репозитория: проверить, что
боевой nginx проставляет заголовок именно на маршруте вебхука (backstop).

**`payments.find_one` — решение `OPT-OUT` ОСТАЁТСЯ В СИЛЕ**, причина уточняется.
Код-ревью подняло эту возможность как второй слой защиты от подделки (WR-09).
Отложено с обоснованием: второй слой имеет смысл ПОСЛЕ того, как первый перестал
быть декоративным, а вводить его в одном плане с закрытием первого значило бы
менять две переменные разом на денежном пути — и при следующем сбое было бы
неизвестно, какая из них подействовала.

**Ни одна другая строка матрицы этой работой не затронута** — сказано прямо,
чтобы молчание не читалось как недосмотр. Обе прежние оговорки (`payment.canceled`
без подтверждённой подписки в кабинете, ревизия `0017` не выкачена по D-26)
остаются в силе дословно: гэп 1 их не касался.

---

**Non-existent capability (documented for the record):** `SecurityHelper.verify_webhook_signature`
appears in Context7's documentation for this SDK but **does not exist** in the
installed `yookassa==3.10.0` (`security_helper.py` has exactly two methods, both
IP-based). It is not opted out — there is nothing to opt out of. Any plan task
importing it is wrong by construction.

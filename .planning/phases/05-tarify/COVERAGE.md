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

## Сверка после закрытия гэпов раунда 5 (планы `05-18`…`05-21`, 2026-08-17)

Матрица выше **не перегенерирована** — ни одна её строка не переписана «для
единообразия». Три плана волн 15-16 закрыли гэпы раунда 5 (верхняя граница на
денежном пути, четыре опровергнутых утверждения кода, фактический радиус
поражения D-26), и вопрос сверки ровно один: изменили ли они ПОВЕРХНОСТЬ API
ЮKassa, которую матрица описывает.

**Первое — факт установлен грепом по коду, а не памятью.** `grep -rn
"YooPayment\.\|SecurityHelper" app/` на дереве после раунда 5 отдаёт:

| обращение | место сегодня | место в сверке плана `05-06` |
|---|---|---|
| `YooPayment.create(...)` | `app/services/payment_service.py:335` | `:95` |
| `{"type": "redirect", ...}` + `"capture": True` | `app/services/payment_service.py:339` и `:342` | `:98-101`, `:102` |
| `SecurityHelper().is_ip_trusted(ip)` | `app/routes/billing.py:121`, гард вызывается `:181` | `:101`, гард `:152-158` |

**Единственным вызовом SDK во всём приложении остался тот же `YooPayment.create`**
— новых обращений планы `05-18`, `05-19` и `05-20` не завели ни одного. Номера
строк сдвинулись (докстринги `create_payment` выросли планом `05-19`), сами
обращения — те же. `KNOWN_EVENTS` по-прежнему содержит РОВНО ДВА события
(`payment.succeeded`, `payment.canceled`, `app/services/payment_service.py:66-71`):
выбранная форма границы `convert-remainder` (D-30) считает деньги ВНУТРИ
приложения чистой функцией `converted_remainder` и ни нового обращения к SDK, ни
нового события вебхука не заводит. **Ни одна строка матрицы не меняет решения.**

**Второе — две возможности, поднятые раундом 5, пересмотрены ЯВНО.**

**`payments.find_one` (пере-запрос статуса платежа) — решение `OPT-OUT` ОСТАЁТСЯ
В СИЛЕ, причина уточняется по состоянию после раунда 5.** Прежняя причина
(«второй слой имеет смысл ПОСЛЕ того, как первый перестал быть декоративным»)
верна и после раунда 5, но неполна: раунд 5 поднял пере-запрос уже не как слой
защиты от подделки, а как способ узнать судьбу намерения, висящего дольше срока
давности (`WR-05 (раунд 5)`). Уточнение: пере-запрос отвечает на вопрос «что
сейчас с этим платежом», но САМ по себе окна срока давности не закрывает —
узнав статус, приложение всё равно обязано перевести строку в терминальный
статус, а это уже не чтение. Отдельным решением `OPT-OUT` не отменяется.

**`payments.cancel` (отмена платежа) — решение `OPT-OUT` ОСТАЁТСЯ В СИЛЕ, но его
прежняя причина после раунда 5 стала НЕПОЛНОЙ, и это сказано прямо.** Прежняя
формулировка — «ни один продуктовый путь не отменяет платёж с нашей стороны;
отмена рождается у ЮKassa или у плательщика» — описывала продукт, каким он был
до потолка одновременных намерений. После плана `05-17` продуктовый путь, которому
отмена НУЖНА, назван: снятие незакрытого подписочного намерения С ОПЛАТЫ при
истечении срока давности. Сегодня истёкшее намерение перестаёт СЧИТАТЬСЯ, но
оплачиваемым быть не перестаёт — это и есть второе остаточное окно потолка,
названное планом `05-19` и оставленное ОТКРЫТЫМ (§Blockers/Concerns, `WR-05
(раунд 5)`). Решение не меняется здесь по той же причине, по какой не менялось
раньше: `payments.cancel` — одна половина работы, вторая (перевод строки в
терминальный статус, обработка гонки с настоящим подтверждением, судьба уже
созданной ссылки на оплату) принадлежит своему плану со своим владельцем, и
включать половину механизма в матрицу значило бы записать решение, которого никто
не принимал. **Форсирующий признак пересмотра назван:** подтверждение подписки на
`payment.canceled` (D-27) — если она включится, окно закрывается ею, и
`payments.cancel` не понадобится вовсе; если владелец решит закрыть окно раньше
подтверждения, строка пересматривается на `INTEGRATE` вместе с планом снятия
намерения.

**Третье — какие строки НЕ затронуты.** **Ни одна другая строка матрицы этой
работой не затронута** — сказано прямо, чтобы молчание не читалось как
недосмотр. `payments.create`, `payments.confirmation`, `payments.metadata`, оба
события вебхука, `SecurityHelper.is_ip_trusted`, `payments.list`,
`payments.capture`, `refunds.*`, `refund.succeeded`, `receipts.*`, сохранённые
способы оплаты, `webhooks.*`, `payouts.*`, `deals.*`, `personal_data.*`,
`invoices.*`, `sbp_banks` и `settings (me)` сохраняют свои решения и свои
причины дословно.

Обе прежние оговорки остаются в силе. Оговорка о `payment.canceled` без
подтверждённой подписки в кабинете (D-27) — дословно. **Оговорка о невыкаченной
очереди ревизий (D-26) ДОПОЛНЯЕТСЯ, а не переписывается:** её нынешняя
формулировка («в проде не работает ни одна строка подписочной ветки: платёж не
запишется») описывает радиус поражения У́ЖЕ фактического — ровно тем же способом,
каким это делала запись `.planning/STATE.md` до плана `05-21`. Фактически
отказывает КАЖДОЕ чтение таблицы платежей, потому что ORM-выборка сущности
выписывает полный перечень отображённых колонок: раздел «Тарифы» отдаёт 500
любому вошедшему, а обработчик уведомления падает ДО ветвления по предмету
покупки и ломает приём ПАКЕТНЫХ платежей, работавший до этой фазы. Невыкаченных
ревизий теперь больше на `0019`. Полная формулировка — в докстринге
`alembic/versions/0019_payment_switch_authorized.py:51-95` и в §Blockers/Concerns
`.planning/STATE.md`; выкат кода и выкат очереди миграций разделить нельзя.
Прежний текст оговорки не вычеркнут намеренно: он описывает состояние, в котором
фаза сдавалась, и стереть его значило бы закрыть дефект удалением записи о нём.

**Итог сверки: решение не изменилось НИ ПО ОДНОЙ строке матрицы, и матрица
остаётся действительной без правок.** Изменились две ПРИЧИНЫ (`payments.find_one`
и `payments.cancel`) и одна оговорка (D-26) — уточнены по состоянию после раунда
5, а не скопированы.

---

**Non-existent capability (documented for the record):** `SecurityHelper.verify_webhook_signature`
appears in Context7's documentation for this SDK but **does not exist** in the
installed `yookassa==3.10.0` (`security_helper.py` has exactly two methods, both
IP-based). It is not opted out — there is nothing to opt out of. Any plan task
importing it is wrong by construction.

---

## Сверка после закрытия гэпов раунда 6 (планы `05-22`…`05-26`, 2026-08-18)

Матрица выше **не перегенерирована** — ни одна её строка не переписана «для
единообразия», ни одна прежняя формулировка не стёрта. Четыре плана волн 18-20
закрыли гэпы раунда 6 (верхняя граница на ВТОРОЙ ветке денежного пути, три
опровергнутых объявления кода, машинный гейт на класс «объявление против
кода»), и вопрос сверки ровно один: изменили ли они ПОВЕРХНОСТЬ API ЮKassa,
которую матрица описывает.

**Первое — факт установлен грепом по коду, а не памятью.** `grep -rn
"YooPayment\.\|SecurityHelper" app/` на дереве после раунда 6 отдаёт шесть
строк, из которых обращений к SDK — три (остальные три суть импорт и два
упоминания в докстрингах):

| обращение | место сегодня | место в сверке после раунда 5 |
|---|---|---|
| `YooPayment.create(...)` | `app/services/payment_service.py:365` | `:335` |
| `{"type": "redirect", ...}` + `"capture": True` | `app/services/payment_service.py:369` и `:372` | `:339`, `:342` |
| `SecurityHelper().is_ip_trusted(ip)` | `app/routes/billing.py:121`, гард вызывается `:181` | `:121`, гард `:181` |

**Единственным вызовом SDK во всём приложении остался тот же `YooPayment.create`**
— новых обращений планы `05-22`, `05-23`, `05-24` и `05-25` не завели ни одного,
и это сказано ПРЯМО, а не выводится читателем из молчания. Номера строк
`payment_service.py` сдвинулись на тридцать (докстринги и комментарии денежного
пути выросли планами `05-22` и `05-24`), номера `billing.py` не сдвинулись
вовсе; сами обращения — те же. `KNOWN_EVENTS` по-прежнему содержит РОВНО ДВА
события (`payment.succeeded`, `payment.canceled`,
`app/services/payment_service.py:67-72`). Причина, по которой поверхность не
изменилась, называется прямо: планы этой волны меняли **стадию ПРИМЕНЕНИЯ
подтверждённого платежа и объявления о ней** — верхнюю границу переноса
(`capped_carryover`, решение D-31), подчинение записанного ответа правилу
истечения, ключ журнала понижения (`subscription_plan_downgraded`, решение
D-32), машинный гейт на объявления, — а не обращения к API. Все эти правки
считают деньги и время ВНУТРИ приложения чистыми функциями и о ЮKassa не
спрашивают ничего. **Ни одна строка матрицы не меняет решения.**

**Второе — две возможности, поднятые раундами 5 и 6, пересмотрены ЯВНО.**

**`payments.find_one` (пере-запрос статуса платежа) — решение `OPT-OUT` ОСТАЁТСЯ
В СИЛЕ, причина уточняется по состоянию после раунда 6, а не копируется.**
Уточнение раунда 5 (пере-запрос отвечает на вопрос «что сейчас с этим
платежом», но сам по себе окна срока давности не закрывает) остаётся верным.
Раунд 6 добавляет к нему ВТОРУЮ причину, и она приходит с другой стороны:
`WR-04 (раунд 6)` показал, что запись в БД, следующая за УСПЕШНЫМ
`YooPayment.create`, не обёрнута ни обработкой ошибки, ни журналом — то есть
существует исход, при котором у ЮKassa платёж есть, а у нас его нет, и
`payments.find_one` есть ровно тот механизм, которым такой платёж можно было бы
найти. Строка **не** переводится в `INTEGRATE` здесь по прежнему правилу:
пере-запрос — половина работы, вторая половина (что делать с найденным
платежом, которого нет в нашей таблице) принадлежит своему плану со своим
владельцем, и включать половину механизма значило бы записать решение, которого
никто не принимал. **Форсирующий признак пересмотра назван:** распоряжение
владельца по `WR-04 (раунд 6)` — как только компенсирующее действие выбрано,
строка пересматривается вместе с планом.

**`payments.cancel` (отмена платежа) — решение `OPT-OUT` ОСТАЁТСЯ В СИЛЕ, и его
причина ДОПОЛНЯЕТСЯ вторым следствием, вскрытым раундом 6.** Формулировка после
раунда 5 называла продуктовый путь, которому отмена нужна: снятие незакрытого
подписочного намерения С ОПЛАТЫ при истечении срока давности. **Раунд 6 добавил
к цене этого окна ВТОРОЕ СЛЕДСТВИЕ, и оно записывается здесь, хотя решение по
строке не меняется:** через окно срока давности достижимо изменение
ДЕЙСТВУЮЩЕГО ТАРИФА ВНИЗ при живом старшем сроке (`WR-03 (раунд 6)`,
воспроизведено прогоном). План `05-24` по ответу владельца `record-wins`
(решение D-32) закрыл это следствие ВИДИМОСТЬЮ — понижение пишет
`subscription_plan_downgraded` уровня `warning`, — но не НЕВОЗМОЖНОСТЬЮ: само
окно остаётся открытым, и `payments.cancel` по-прежнему остаётся одной из двух
дорог к его закрытию. То есть цена `OPT-OUT` по этой строке выросла, а решение
не изменилось, и это сказано прямо, а не сглажено. **Форсирующий признак
пересмотра остаётся прежним и дополняется:** подтверждение подписки на
`payment.canceled` (D-27) — если она включится, окно закрывается ею, и
`payments.cancel` не понадобится вовсе; если владелец решит закрыть окно раньше
подтверждения либо сочтёт видимость понижения недостаточной мерой, строка
пересматривается на `INTEGRATE` вместе с планом снятия намерения.

**Третье — какие строки НЕ затронуты.** **Ни одна другая строка матрицы этой
работой не затронута** — сказано прямо, чтобы молчание не читалось как
недосмотр. `payments.create`, `payments.confirmation`, `payments.metadata`, оба
события вебхука, `SecurityHelper.is_ip_trusted`, `payments.list`,
`payments.capture`, `refunds.*`, `refund.succeeded`, `receipts.*`, сохранённые
способы оплаты, `webhooks.*`, `payouts.*`, `deals.*`, `personal_data.*`,
`invoices.*`, `sbp_banks` и `settings (me)` сохраняют свои решения и свои
причины дословно.

Обе прежние оговорки остаются в силе ДОСЛОВНО и здесь не переписываются:
оговорка о `payment.canceled` без подтверждённой подписки в кабинете (D-27) и
оговорка о невыкаченной очереди ревизий (D-26) вместе с её дополнением после
раунда 5 о фактическом радиусе поражения. Волна 21 не завела ни одной новой
ревизии Alembic — головной ревизией репозитория остаётся `0019`, — поэтому
состав невыкаченной очереди этой работой не изменился.

**Итог сверки: решение не изменилось НИ ПО ОДНОЙ строке матрицы, и матрица
остаётся действительной без правок.** Изменились две ПРИЧИНЫ
(`payments.find_one` и `payments.cancel`) — уточнены по состоянию после раунда
6, а не скопированы; ни одна оговорка не изменилась, потому что предмет ни
одной из них этой волной не затронут.

## Сверка после закрытия гэпов раунда 7 (планы `05-28`, `05-31`, `05-33`, 2026-08-18)

Матрица выше **не перегенерирована** — ни одна её строка не переписана «для
единообразия», ни одна прежняя формулировка не стёрта. Вопрос сверки тот же, что
и в трёх предыдущих: изменили ли исполненные планы раунда 7 ПОВЕРХНОСТЬ API
ЮKassa, которую матрица описывает.

**Затронутые строки названы поимённо, а решение по ним — отдельно от
реализации.** Волна правила ровно один участок денежного пути, обслуживающий
уведомление `payment.succeeded`:

| строка матрицы | что тронуто раундом 7 | решение | что изменилось |
|---|---|---|---|
| `payments.create` (создание платежа) | не тронута | `INTEGRATE` — **не изменилось** | ничего: `YooPayment.create` тот же |
| уведомление `payment.succeeded` | `_plan_price` получил защиту чтения перечня тарифов (план `05-28`) и журнальный ключ `plan_limits_unreadable`; три объявления той же ветки приведены к решению D-34 (план `05-33`, задача 2) | `INTEGRATE` — **не изменилось** | изменилась **РЕАЛИЗАЦИЯ обработчика на нашей стороне, а не РЕШЕНИЕ по строке**: испорченный `PLAN_LIMITS` больше не роняет обработчик исключением, то есть 5xx на уведомлении и вызванный им цикл повторов ЮKassa стали недостижимы этим путём. Состав запросов к API не изменился ни на один |
| `SecurityHelper.is_ip_trusted` (гард источника) | не тронута | `INTEGRATE` — **не изменилось** | ничего |

**Ни одного нового обращения к SDK волна не завела.** `KNOWN_EVENTS`
по-прежнему содержит РОВНО ДВА события (`payment.succeeded`,
`payment.canceled`); единственным вызовом SDK во всём приложении остаётся
`YooPayment.create`. Правки раунда 7 считают деньги и время ВНУТРИ приложения
чистыми функциями либо правят объявления о них и о ЮKassa не спрашивают ничего.

**Незатронутые строки названы прямо, а не молчанием** — молчание о них читалось
бы недосмотром. Все решения `OPT-OUT` остаются в прежнем решении и с прежней
причиной ДОСЛОВНО, раунд 7 к ним не прикасался: возвраты (`refunds.*`,
`refund.succeeded`), чеки (`receipts.*`), автоплатежи и сохранённые способы
оплаты, выплаты (`payouts.*`), сделки (`deals.*`), счета (`invoices.*`), СБП
(`sbp_banks`), `settings (me)`, `payments.list`, `payments.capture`,
`payments.cancel`, `payments.find_one`, `webhooks.*` и `personal_data.*`. Обе
уточнённые раундом 6 причины (`payments.find_one` и `payments.cancel`) остаются
в силе без изменений: их форсирующие признаки пересмотра — распоряжение
владельца по `WR-04 (раунд 6)` и подтверждение подписки на `payment.canceled`
(D-27) — раундом 7 не наступили.

**Что раунд 7 к матрице НЕ добавил — сказано прямо, чтобы отсутствие новых строк
не читалось пропуском.** Ни одна находка раунда 7 не требует новой возможности
API: `CR-01` есть чтение документа КОНФИГА (`PLAN_LIMITS`), а не обращение к
ЮKassa; остальные находки суть либо объявления в коде и в документах
планирования (гэпы 1-3), либо интерфейс, либо трекинг состояния планирования
(гэп 4). **Новых строк матрицы: ноль. Изменённых решений: ноль.**

**Сужение объёма названо, а не скрыто.** Спланированные планы `05-27`, `05-29`,
`05-30` и `05-32` сняты до исполнения решением владельца (запись **D-34**,
`05-CONTEXT.md`), поэтому настоящая сверка описывает правки ТРЁХ исполненных
планов, а не шести спланированных.

**Сверка не спорит с `### Requirements Coverage` отчёта раунда 7:** BILL-05,
BILL-06 и BILL-07 названы там `✓ SATISFIED`, и настоящий раздел этого вердикта
не пересматривает. Отметку `Complete` в `.planning/REQUIREMENTS.md` возвращает
верификация, а не план — файл в `files_modified` плана `05-33` не входит.

**Признак повторной сверки назван и он не календарный:** следующая сверка нужна
при переводе любой строки `OPT-OUT` в `INTEGRATE` — прежде всего возвраты
(`refunds.*`), чеки (`receipts.*`) и автопродление сохранённым способом оплаты,
— а не по расписанию и не «после каждого раунда».

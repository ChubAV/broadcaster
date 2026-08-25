---
phase: 05
slug: tarify
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-25
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

**Register origin:** `register_authored_at_plan_time: true` — all 30 PLAN files of the
phase carry a `<threat_model>` block. 261 register rows → **221 unique threat IDs**.
No retroactive STRIDE was performed; the auditor verified declared mitigations and did
not scan for new threats.

⚠️ **ЧИТАТЬ ПЕРЕД ТЕМ, КАК СЧИТАТЬ ЭТУ ФАЗУ ЗАЩИЩЁННОЙ.** `threats_open: 0` здесь
получен НЕ тем, что все угрозы закрыты кодом. Он получен тремя разными способами, и
смешивать их нельзя: 160 закрыты проверенной митигацией, 58 закрыты УДАЛЕНИЕМ
защищаемого компонента фазой 05.1, 2 переведены в принятый риск решением владельца
2026-08-25 и остаются ЖИВЫМИ в проде. Третья группа — не «починено», а «решено жить с
этим». Её строки помечены `accepted` и продублированы в журнале принятых рисков.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| ЮKassa (или кто угодно) → `POST /api/billing/webhook` | Вход, на котором принимается решение о выдаче платного ресурса. Подлинность источника держит сверка адреса из заголовка, проставляемого nginx | Тело уведомления о платеже: статус, `object.id`, суммы, реквизиты карты (`first6`/`last4`) |
| браузер → `POST /billing/subscribe` | Недоверенный ввод изменяющей формы; цена в форму не передаётся вовсе | Cookie сессии, Origin |
| приложение → ЮKassa API | Исходящий HTTPS с секретным ключом магазина | Идентификатор магазина, ключ, суммы, `metadata` |
| nginx → приложение | Адрес клиента теряется на прокси; заголовок сквозного адреса подделываем, если прокси его не перезаписывает | `X-Real-IP` |
| Alembic → боевая схема | Ревизии `0017`–`0020`, применяемые к живым данным | Строки `payments`, `subscriptions` |
| контейнер `web` → демон Docker | `/var/run/docker.sock` смонтирован rw в тот же процесс, который терминирует вебхук | Полный контроль над демоном Docker хоста |

---

## Threat Register

Полный реестр — 221 уникальная угроза — живёт в `<threat_model>`-блоках тридцати
планов фазы и здесь не дублируется построчно: дубль немедленно разошёлся бы с
источником. Ниже — сводка по исходам и поимённо всё, что НЕ закрыто проверенной
митигацией.

### Сводка

| Исход | Кол-во | Что это значит |
|---|---|---|
| Closed — митигация проверена в коде | 160 | Аудитор нашёл контроль и назвал `file:line` либо имя теста |
| Closed — компонент удалён фазой 05.1 | 58 | Защищать нечего: `PLAN_LIMITS`, `MessageBalance`, `plan_axes` и прочее вырезаны |
| Accepted — риск жив, принят владельцем | 2 | T-05-33, T-05-73 — см. журнал принятых рисков |
| Open — ниже порога блокировки | 1 | T-05-66 (medium), не считается в `threats_open` при `block_on: high` |
| **Всего** | **221** | |

Тяжесть исходного реестра: 10 critical, 149 high, 81 medium, 21 low.
Диспозиции: 236 mitigate, 22 accept, 1 transfer, 2 mitigate/accept (261 строка).

### Строки, не закрытые проверенной митигацией

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-33 | Repudiation | Подписка на событие `payment.canceled` в кабинете ЮKassa → ветка отмены `app/services/payment_service.py:588-620` | high | accept | Ветка отмены реализована и зелена (`test_a_canceled_webhook_gives_a_pending_payment_a_terminal_status`), но МЕРТВА в проде: событие не включено в кабинете. Кодового обходного пути нет — набор событий настраивается вне репозитория (`05-06-SUMMARY.md:168`) | accepted 2026-08-25 |
| T-05-73 | Elevation of Privilege | `docker-compose.prod.yml:108`, `:137` — `/var/run/docker.sock` смонтирован rw в контейнер `web`, терминирующий `POST /api/billing/webhook` | high | accept (было: transfer) | Ни `docker-socket-proxy`, ни отдельного воркера управления контейнерами в репозитории нет. Диспозиция `transfer` держалась семь раундов без названного получателя (`STATE.md:127`, `:155`, `:181`) — переведена в `accept` с названным акцептором | accepted 2026-08-25 |
| T-05-66 | Tampering | `Subscription.is_active` как вход решения о доступе — `app/application/billing/subscription_period.py:148`, `app/services/payment_service.py:833` | medium | mitigate | НЕ исполнено. Объявленная митигация — «решение перестаёт опираться на `is_active` вовсе» — не выполнена: флаг остался входом авторизации. При этом грep по `app/` не находит НИ ОДНОГО писателя, снимающего флаг у `Subscription` (только `Schedule` и `Group`) — то есть вход, который никакой путь не может изменить | open — below high threshold (non-blocking) |

*Status: open · closed · accepted · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Закрытые митигации — кластеры и свидетельства

| Кластер | Кол-во | Ключевое свидетельство |
|---|---|---|
| C1 · Подлинность источника вебхука | 9 | `app/routes/billing.py:148-154` — гард ДО `request.json()` на `:157`; `grep "request.client" app/routes/billing.py` → 0; `nginx/*.template` ставят `X-Real-IP` на всех шести локациях; `docker-compose.prod.yml:27` закрепляет имя заголовка |
| C2 · Идемпотентность, терминальный статус, источник истины | 16 | `payment_service.py:572-580` — пользователь из строки `Payment`, ноль чтений `metadata`; `:582-584` терминальный статус до ветвления; `:497-506` compare-and-swap; `:575` `with_for_update()`; частичный уникальный индекс `uq_subscriptions_active_user` |
| C3 · Порядок создания платежа и потолок намерений | 18 | `:318-344` потолок ДО вызова SDK (`test_the_refusal_never_reaches_yookassa` проверяет `call_count == 0`); `:407-460` порядок «SDK → БД»; у `GET /billing` ноль путей записи |
| C4 · Цена и CSRF на денежной форме | 2 | `app/pages/billing.py:374` цена с сервера; форма не несёт полей вовсе; `:353` `is_same_origin` до обращения к БД |
| C5 · Изоляция истории платежей и отрисовка | 9 | `billing_service.py:65` владение предикатом запроса; `yookassa_payment_id` в шаблонах только в комментариях; ноль `\|safe` / `Markup` в `app/templates/billing/` |
| C6 · Закрытое отображение кодов ошибок | 4 | `app/pages/billing.py:102-145` закрытый набор; неизвестный код → пустая строка; текст стороннего исключения на экран не попадает |
| C7 · Единственное объявление правила периода + инвариант порядка | 12 | `payment_service.py:886-888` живость снимается ДО сдвига `expires_at`; AST-тест порядка на `ast.walk` с отрицательным контролем |
| C8 · Гейт миграций и выката | 14 | `tests/test_migrations/test_deploy_applies_migrations_before_serving.py`, `test_model_matches_head.py` с отрицательным контролем. ⚠️ `WR-06` фиксирует: гейт сверяет ТОЛЬКО имена колонок — объявлено частичным |
| C9 · Храповик объявленных инвариантов | 12 | `tests/test_application/test_declared_invariants.py:451` + три теста-храповика; реестр без свидетеля на месте, потолок не поднят |
| C10 · Гейт ROADMAP ↔ STATE | 10 | `tests/test_planning/test_state_progress_matches_roadmap.py` выводит счёт из меток ROADMAP, а не из литерала; `justfile:22` |
| C11 · Целостность планировочных документов | 53 | Пять `🔴` в `STATE.md` на месте; гигиена секретов проверена грепом — только ИМЕНА переменных окружения, ни идентификатора магазина, ни ключа |
| C12 · RED-before-GREEN / дисциплина тестов | 7 | — |

**Прогон:** целевые тесты денежного пути и всех гейтов — **181 passed**.

### Обесценено фазой 05.1 — 58 угроз

Защищаемый компонент удалён. Проверено грепом по `app/`: `PLAN_LIMITS`,
`parsed_plan_limits`, `message_packages`, `MessageBalance`, `deduct_message`,
`add_messages`, `plan_switch`, `PLAN_ORDER`, `prorated_expiry`, `converted_remainder`,
`_plan_price`, `plan_axes`, `reset_free_monthly`, `axis_percent` → по нулю совпадений;
колонка `subscriptions.plan` снята ревизией `0020`.

T-05-16…19, 22, 23, 28, 29, 36, 43, 50…52, 54, 55, 62, 64, 65, 75, 76, 80, 82, 99, 101,
104, 105, 109, 111, 136…138, 140, 142…158, 188…190, 193…195, 197, 199, 200 —
удалившие планы: 05.1-03…05.1-07.

⚠️ Это закрыто УДАЛЕНИЕМ, а не проверенной митигацией. Если компонент вернётся,
угроза вернётся вместе с ним и её нужно будет открывать заново, а не считать закрытой.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-33 (high, Repudiation) | Событие `payment.canceled` не включено в кабинете ЮKassa. Следствие принято осознанно: отменённый платёж остаётся `pending` навсегда, и журнал платежей утверждает про деньги неправду. Ветка обработки в коде готова и покрыта тестом — включение события в кабинете закрывает риск без единой правки кода. Действие вне репозитория, поэтому кодом не принуждается | chubav | 2026-08-25 |
| AR-05-02 | T-05-73 (high, Elevation of Privilege) | `/var/run/docker.sock` остаётся смонтированным rw в контейнер, терминирующий вебхук. Компрометация процесса `web` даёт полный контроль над демоном Docker хоста; аутентификация вебхука на том же процессе — заголовок прокси, отключаемый одной переменной окружения (`YOOKASSA_WEBHOOK_VERIFY_IP`, `app/config.py:127`). Диспозиция переведена из `transfer` в `accept`, потому что передача без названного получателя держалась семь раундов и передачей не являлась. Названный акцептор устраняет бесхозность, но НЕ устраняет экспозицию | chubav | 2026-08-25 |

*Accepted risks do not resurface in future audit runs.*

⚠️ Оба принятых риска ЖИВЫ. `threats_open: 0` означает «фаза не заблокирована», а не
«поверхность чиста». Снятие AR-05-01 — одно действие в кабинете ЮKassa; снятие
AR-05-02 требует `docker-socket-proxy` либо выноса управления контейнерами в отдельный
процесс.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-25 | 221 | 219 (160 митигация + 58 удаление + 1 ниже порога) | 0 блокирующих (2 приняты решением владельца) | gsd-security-auditor (ASVS L1, block_on: high) |

### Предупреждения процесса (не блокируют)

1. **Секция `## Threat Flags` отсутствует у 8 из 30 SUMMARY** — `05-06`, `05-09`,
   `05-15`, `05-16`, `05-17`, `05-22`, `05-25`, `05-26`. Отчёта исполнителя по
   диспозициям для этих планов не существует; их угрозы судились напрямую по коду и
   артефактам.
2. **Коллизии идентификаторов в реестре** — 8 ID несут по две-три РАЗНЫЕ угрозы в
   разных планах: `T-05-30`, `31`, `32`, `33`, `34`, `35`, `51`, `104`. У `T-05-33` под
   одним ID сошлись открытая high (05-06, подписка на событие отмены) и закрытая
   medium (05-07, тело в логе). Судилось по худшему случаю. Дефект уже записан долгом
   фазы 9 в `STATE.md`.
3. **`unregistered_flag`: нет.** Все три записи `threat_flag: note` отображаются в
   зарегистрированные угрозы и впоследствии закрыты.
4. **Остаток по T-05-104, названный, а не утаённый:** `app/routes/billing.py:169-171`
   превращает любое необработанное исключение в HTTP 500, и один живой путь туда
   доходит — `payment_service.py:822` перевыбрасывает `IntegrityError`, не относящийся
   к `uq_subscriptions_active_user`. Это намеренный отказ погромче при порче данных, а
   не поверхность фазы 5.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-25

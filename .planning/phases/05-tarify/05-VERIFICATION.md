---
phase: 05-tarify
verified: 2026-08-16T06:20:00Z
status: gaps_found
score: 54/60 must-haves verified
behavior_unverified: 1
overrides_applied: 0
gaps:
  - truth: "Вебхук с недоверенного адреса отвергается 403 и не доходит до handle_webhook"
    status: failed
    reason: "Гард источника написан верно, но в ОТГРУЖЕННОЙ прод-конфигурации инертен и обходится подделкой заголовка. Проверено независимо: app/config.py:94 даёт yookassa_webhook_client_ip_header = \"\"; ни один деплойный артефакт репозитория его не задаёт (grep по *.yml / *.env* / *.md / *.template вне .planning — пусто); пустое значение уводит в ветку `return client.host` (app/routes/billing.py:82-83); docker-compose.prod.yml:78 запускает uvicorn с --forwarded-allow-ips=*, из-за чего ProxyHeadersMiddleware переписывает scope[\"client\"] ЛЕВЫМ элементом X-Forwarded-For — тем самым, который присылает вызывающий. Правильное чтение справа (строка 81) в проде не исполняется НИ РАЗУ. Эта дыра живая независимо от D-26: вебхук пакетов сообщений работает на текущей проде (ревизия 0012), и подделанное payment.succeeded начислит сообщения."
    artifacts:
      - path: "app/config.py"
        issue: "Строка 94: yookassa_webhook_client_ip_header: str = \"\" — небезопасное умолчание; отказ по умолчанию открывает гард, а не закрывает"
      - path: "docker-compose.prod.yml"
        issue: "Строка 78: --forwarded-allow-ips=* превращает request.client.host в подконтрольный вызывающему левый элемент X-Forwarded-For; переменная YOOKASSA_WEBHOOK_CLIENT_IP_HEADER в перечне env сервиса web отсутствует"
      - path: "tests/test_routes/test_billing_webhook_source.py"
        issue: "test_without_a_configured_header_the_peer_address_is_used фиксирует именно небезопасную ветку как корректную; тестовый транспорт не проходит через ProxyHeadersMiddleware, поэтому регрессия непокрыта"
    missing:
      - "Безопасное умолчание в app/config.py (например X-Real-IP) ЛИБО явная запись YOOKASSA_WEBHOOK_CLIENT_IP_HEADER в docker-compose.prod.yml — сейчас это исключительно организационная запись в STATE.md, а не свойство кода"
      - "Регрессия, поднимающая приложение с ProxyHeadersMiddleware и доказывающая, что подделанный X-Forwarded-For получает 403"
  - truth: "Подтверждённый платёж зачисляется ровно один раз (производная BILL-05/BILL-03: защита от двойного начисления)"
    status: failed
    reason: "Защита — check-then-act без блокировки. Проверено независимо: `select(Payment)` в app/services/payment_service.py:171-174 без with_for_update(); grep по app/ даёт НОЛЬ вхождений with_for_update; уникального ограничения на subscriptions.user_id в app/models/subscription.py нет; add_messages делает `bal.balance += amount` в Python (app/services/billing_service.py:76) на отдельно загруженной строке. Две одновременные доставки уведомления видят статус pending, обе проходят проверку TERMINAL_STATUSES и обе зачисляют; _extend_subscription может вставить ДВЕ строки Subscription. Тесты покрывают только последовательную повторную доставку. Риск прямо усиливается предыдущим гэпом: без работающего гарда источника подделанные параллельные доставки инициируются кем угодно."
    artifacts:
      - path: "app/services/payment_service.py"
        issue: "Строки 171-179: выборка платежа без блокировки строки, проверка терминального статуса и коммит разнесены; строки 265-290: _extend_subscription не защищён ни блокировкой, ни уникальным индексом"
      - path: "app/models/subscription.py"
        issue: "Нет уникального ограничения по user_id — вторая строка подписки вставляется молча"
    missing:
      - "Блокировка строки платежа (with_for_update) либо уникальное ограничение, делающее двойную обработку невозможной на уровне БД"
      - "Регрессия на конкурентную доставку уведомления (две сессии), а не только на последовательную"
deferred: []
behavior_unverified_items:
  - truth: "Раздел тарифов пригоден к использованию на мобильных ширинах (критерий 4; тот же backstop-пункт в must_haves плана 05-05)"
    test: "Открыть /billing в браузере на ширине 375px с реальными данными: три карточки планов, четыре метра, история платежей длиной больше экрана"
    expected: "Карточки планов складываются в одну колонку; подписи колонок истории ([data-cell-label]) едут вместе со значениями; ни один блок не требует горизонтальной прокрутки; кнопки оплаты нажимаемы"
    why_human: "Браузерного/e2e-харнесса в проекте нет (playwright/selenium отсутствуют в pyproject.toml). Оба относящихся теста — test_billing_plans_grid_is_declared_folding и test_billing_plans_grid_rule_does_not_redefine_the_dashboard_grid — проверяют ОБЪЯВЛЕНИЕ правила CSS и наличие атрибута в HTML, что прямо записано в докстринге теста («Проверяется ОБЪЯВЛЕНИЕ правила, а не отрисовка: браузера в суите нет»). Отрисовка, переполнение и попадание пальцем непроверяемы грепом. Пункт записан планом 05-06 как НЕ выполненный."
human_verification_carried_to_uat:
  - test: "Настоящий платёж в тестовом магазине ЮKassa: форма → confirmation_url → возврат → приход уведомления → сдвинутый срок на /billing"
    expected: "Срок НЕ двигается до прихода уведомления и двигается после него; вся цепочка идёт тем же контуром, что и пакеты сообщений"
    why_human: "Боевого доступа к API ЮKassa у исполнителя нет, всё покрытие идёт на моках. Backstop-пункт в must_haves планов 05-01 и 05-06; записан планом 05-06 как НЕ выполненный. При решении D-26 недостижим на проде (колонок payments.kind/plan там нет)."
  - test: "Отменённый платёж получает статус «отклонён» на экране истории"
    expected: "Строка платежа показывает бейдж «отклонён», а не «в обработке»"
    why_human: "Заблокирован: владелец не подтвердил включение подписки на событие payment.canceled в кабинете ЮKassa (D-27). Состав рассылаемых событий задаётся вне репозитория и кодом не проверяется. Ветка кода зелёная в тестах (8 тестов в test_payment_service.py) и мертва в проде."
  - test: "Пользователь, вернувшийся с ЮKassa до прихода вебхука, понимает, что платёж ещё в обработке"
    expected: "Человек читает строку истории со статусом «в обработке» как «деньги в обработке», а не как «оплата не прошла»"
    why_human: "Backstop-пункт must_haves плана 05-04: понятность формулировки — суждение человека, а не свойство разметки. Разметка на месте (PAY_LABELS['pending'] → «в обработке», app/templates/billing/balance.html:64)."
---

# Phase 5: Тарифы — Verification Report

**Phase Goal:** Пользователь понимает, сколько ресурса тарифа он израсходовал, за что платил и может продлить подписку не выходя из раздела.
**Verified:** 2026-08-16T06:20:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Область суждения

Фаза принята владельцем **на тестовом стенде** (D-26 `defer-deploy`). Критерии ниже судятся по кодовой базе и тестовому стенду, как предписано, но производственный разрыв называется прямо и не смягчается:

- **Боевая база остаётся на ревизии `0012`.** Не выкачены `0013`…`0017`. В проде нет колонок `payments.kind` / `payments.plan`, `messages_count` остаётся `NOT NULL`. Следствие: **критерий 1 в проде НЕ выполнен** — кнопка оплаты подписки доходит до ошибки записи. Проверено: `alembic/versions/0017_payment_kind_and_plan.py` объявляет `down_revision = "0016"`, то есть встаёт пятой в очереди.
- **Подписка на событие `payment.canceled` в кабинете ЮKassa не подтверждена** (D-27). Следствие: **критерий 3 в проде показывает неправду** — отменённый платёж остаётся `pending` навсегда и подписывается «в обработке». Это ровно то, что запрещает прохибиция плана 05-02.

Оба разрыва — принятые решения владельца, а не гэпы к закрытию. Гэпы ниже — другое: это дефекты кода и деплойных артефактов репозитория, найденные код-ревью и подтверждённые здесь независимо.

## Goal Achievement

### Observable Truths — критерии ROADMAP

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | Пользователь может продлить текущую подписку из раздела и сразу увидеть обновлённый срок | ✓ VERIFIED (тестовый стенд) | Цепочка прослежена целиком: форма `POST /billing/subscribe` (`plan_card.html:72`, `balance.html:96`) → `subscribe_to_plan` (`app/pages/billing.py:151`) → `create_payment(kind='subscription')` → 302 на `confirmation_url` → вебхук → `_extend_subscription` (`payment_service.py:248`) → `Subscription.expires_at`. Показ срока читает ТУ ЖЕ строку тем же запросом: `get_shell_context` (`app/pages/common.py:498-505`) — три условия, сортировка и `limit(1)` совпадают с писателем дословно. Поведенчески доказано: `test_webhook_extends_an_active_subscription_without_burning_the_remainder`, `test_an_active_subscription_is_extended_from_its_own_expiry`, `test_a_repeated_subscription_webhook_moves_the_expiry_once`. ⚠️ В проде не выполнен (D-26). |
| SC2 | Пользователь видит потребление и остаток по всем ЧЕТЫРЁМ осям | ✓ VERIFIED | `AXIS_ORDER = ('ads','groups','sends','accounts')` (`plan_usage.py:64`) → `plan_axes` (`:121`) → контекст `usage` (`billing.py:91`) → цикл метров (`balance.html:108`) → `usage_meter` (`usage_meters.html:29`). Данные настоящие: `ads`/`accounts` из `nav_counts` шелла, `groups`/`sends` — одним round-trip скалярными подзапросами (`plan_usage.py:160-173`). 22 поведенческих теста в `test_plan_usage.py`, включая владение, границы месяца в зоне пользователя, безлимит, нулевой лимит, превышение и счётчик запросов. |
| SC3 | Пользователь видит историю платежей с датой, суммой и статусом | ✓ VERIFIED (тестовый стенд) | `get_payment_history` + `count_payments` (`billing_service.py:179`, `:210`, владение предикатом запроса) → контекст `payments` (`billing.py:106`) → блок «История платежей» (`balance.html:166-192`) → `payment_row` (`payment_row.html:39`): дата через `format_datetime_for_user`, сумма через `format_amount`, статус бейджем по `PAY_LABELS`. Терминальный статус отмены закреплён `test_a_canceled_payment_is_named_rejected`. ⚠️ В проде статус «отклонён» не появится (D-27). |
| SC4 | Раздел пригоден к использованию на мобильных ширинах | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Правила объявлены и проверены: `[data-plans] { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)) }` (`app.css:1159-1161`), `[data-cell-label]` скрыт на широком и показан в `@media (max-width: 860px)` (`app.css:1479`, `:1489-1495`), табличные данные построены на примитивах строки (`test_billing_no_table_markup`). Но оба относящихся теста читают CSS и HTML как ТЕКСТ; браузера в суите нет (playwright/selenium в `pyproject.toml` отсутствуют), докстринг теста это признаёт явно. Ручная проверка на 375px планом 05-06 записана как НЕ выполненная. |

### Observable Truths — must_haves планов

**План 05-01 (10 truths)**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Успешный вебхук `kind='subscription'` создаёт Subscription и записывает plan | ✓ VERIFIED | `payment_service.py:283-290`; `test_webhook_creates_the_first_subscription`, `test_the_first_purchase_takes_the_plan_from_the_payment` |
| 2 | Продление действующей: `expires_at + 1 месяц`, остаток не сгорает | ✓ VERIFIED | `next_expiry` (`subscription_period.py:65-67`); прогон в процессе верификации: `next_expiry(2026-09-01, now=2026-08-16) → 2026-10-01` |
| 3 | Продление истёкшей считается от сегодня | ✓ VERIFIED | Тот же прогон: `next_expiry(2026-06-01, now=2026-08-16) → 2026-09-16`; `test_next_expiry_of_an_expired_subscription_counts_from_today` |
| 4 | `add_one_month` на краевых датах без ValueError | ✓ VERIFIED | Прогон: 31.01.2026→28.02.2026, 31.12.2026→31.01.2027, 29.01.2028→29.02.2028; `test_add_one_month_never_raises_on_any_day_of_the_year` |
| 5 | Возврат на /billing не меняет ни срок, ни статус | ✓ VERIFIED | `billing_page` не содержит ни одной записи (прочитан целиком, `billing.py:39-148`); `test_returning_to_billing_does_not_move_the_date`, `test_the_get_handler_contains_no_write_path` |
| 6 | В `amount.value` уходит машинная строка | ✓ VERIFIED | Конфиг отдаёт `'1490.00'` (прогон `parsed_plan_limits`); `create_payment` кладёт `price` напрямую (`payment_service.py:97`); `format_amount` — только показ, обратной функции нет (`common.py:252-281`) |
| 7 | Кросс-доменный POST /billing/subscribe → 403, платёж не создаётся | ✓ VERIFIED | `billing.py:181-182`; `test_subscribe_rejects_a_cross_site_origin`, `test_the_origin_check_runs_before_the_payment_is_created` |
| 8 | Вебхук с недоверенного адреса отвергается 403 | ✗ **FAILED (BLOCKER)** | Верно в тестах, **инертен в отгруженной прод-конфигурации** — см. гэп 1 |
| 9 | Ревизия 0017: `down_revision='0016'`, kind/plan, nullable messages_count, backfill 'package' | ✓ VERIFIED | Файл прочитан целиком; 7 тестов round-trip в `test_0017_payment_kind_and_plan.py` — все зелёные |
| 10 | *(backstop)* Настоящий платёж в тестовом магазине проходит весь путь | ? INSUFFICIENT_SPEC | НЕ выполнено, признано планом 05-06 → перенесено в UAT |

**План 05-02 (8 truths)** — все ✓ VERIFIED

`payment.canceled` → `canceled` + `confirmed_at`, без начислений (`payment_service.py:185-210`); отмена не воскрешает succeeded; повторная отмена ничего не пишет; неизвестное событие → False; имена событий взяты константами `WebhookNotificationEventType` (`:8`, `:43-44`), а не литералами; обе половины D-04 закреплены отдельными тестами; round-trip 0017 на схеме 0016; `messages_count` принимает NULL после upgrade и не принимает до. Поведенчески: 8 именованных canceled-тестов + 7 миграционных, все зелёные. ⚠️ Прохибиция «MUST NOT показывать терминальный платёж как в обработке» выполнена в коде и **нарушена в проде** отсутствием D-27.

**План 05-03 (11 truths)** — все ✓ VERIFIED

Четыре оси, не три; ось отправок по журналу `send_logs`, а не по балансу; календарное окно в зоне пользователя; каждая попытка расходует квоту (все статусы); числители `ads`/`accounts` из уже посчитанного шелла; черновики входят; безлимит = `None` (прогон: `axis_percent(3, None) → 0`); превышение не ошибка (`axis_percent(20,15) → 100`, `used` отдаётся как есть); владение предикатом запроса; календарь считается в Python (`test_plan_usage_module_has_no_dialect_specific_calendar_functions`); две оси одним round-trip (`test_plan_axes_takes_exactly_one_query`).

**План 05-04 (11 truths)** — 10 ✓ VERIFIED, 1 backstop → UAT

Один экран со всеми блоками; история по `Payment`, а не `BalanceTransaction`; баланс отдельным блоком; потолок называет себя (`payments_truncated = payments_total > PAYMENT_LIST_CAP`, `billing.py:144`, `PAYMENT_LIST_CAP=200`); чужие платежи не видны; покупка пакета настоящей формой; истёкшая подписка ничего не отключает; GET не пишет; JSON-маршрут покупки удалён (проверено: в `app/routes/billing.py` его нет, на его месте — обоснование сноса, `:41-57`); гард источника один на проект (`is_same_origin` в `common.py:318`, зовут `billing.py:181,241` и `history.py:913`). Backstop «пользователь понимает, что платёж в обработке» → UAT.

**План 05-05 (12 truths)** — 11 ✓ VERIFIED, 1 backstop = SC4 (behavior-unverified)

Три карточки по макету с моношрифтовым тегом, крупной ценой, четырьмя строками лимитов и рамкой акцентного цвета у текущего (`plan_card.html`, `app.css:1164`); четыре метра, безлимит знаком `∞` без деления (`usage_meters.html:30-34`); история с датой/суммой/статусом теми же словами, что увидит администратор; человеческий формат суммы только на показе (прогон: `'1490.00' → '1 490 ₽'`); истёкшая помечена и сопровождается формой «Продлить»; при выключенных платежах витрина видна, кнопки нет; ни одного скрипта в разделе (`test_the_section_markup_carries_no_script_at_all`); виджет сайдбара подписан «Баланс сообщений» (`base.html:75`), источник не менялся; `app/templates/billing/plans.html` удалён вместе со своей проверкой исходника (подтверждено `git log --diff-filter=D`, коммит `752db3a`; ссылок на файл в `app/` и `tests/` не осталось); табличные данные на примитивах строки; библиотека компонентов не выросла.

**План 05-06 (8 truths)** — 5 ✓ VERIFIED, 3 backstop (1 выполнен, 2 → UAT)

BILL-02 перепомечен `[ ]` (`REQUIREMENTS.md:48`) и `Partial` в матрице (`:187`); BILL-05/06/07 помечены выполненными в ОБЕИХ таблицах (`:115-117` и `:235-237`); заметка ROADMAP исправлена («сервиса применения тарифных лимитов в проекте нет», `ROADMAP.md:305`); полный прогон зелёный; граф обновлён (`graphify-out/graph.json` от 16.08 05:25 против последнего коммита кода 15.08 20:15). Backstop «владелец принял решение о выкате» — ✓ VERIFIED: D-26 записан в `05-CONTEXT.md:75` и `STATE.md`. Два остальных backstop'а → UAT.

**Score:** 54/60 truths verified (1 present, behavior-unverified; 3 backstop → UAT; 2 FAILED)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `alembic/versions/0017_payment_kind_and_plan.py` | ревизия 0017, down_revision '0016' | ✓ VERIFIED | 75 строк; `revision="0017"`, `down_revision="0016"`; `batch_alter_table` для SQLite; backfill через `server_default` |
| `app/application/billing/subscription_period.py` | add_one_month, next_expiry | ✓ VERIFIED | 67 строк; обе функции реальны, прогнаны в процессе верификации |
| `app/application/billing/plan_usage.py` | plan_axes + константы осей | ✓ VERIFIED | 195 строк; вызывается из `billing.py:91` |
| `app/config.py` | plan_limits, parsed_plan_limits, verify_ip, client_ip_header | ⚠️ ПРИСУТСТВУЕТ, УМОЛЧАНИЕ НЕБЕЗОПАСНО | Все четыре есть; `yookassa_webhook_client_ip_header = ""` (`:94`) — корень гэпа 1 |
| `app/pages/common.py` | is_same_origin + глобал format_amount | ✓ VERIFIED | `:318` и `:284`; переиспользуется историей и биллингом |
| `app/services/billing_service.py` | get_payment_history | ✓ VERIFIED | `:179`; владение предикатом, сортировка по дате |
| `app/constants.py` | потолок списка платежей | ✓ VERIFIED | `PAYMENT_LIST_CAP: int = 200` (`:69`) |
| `app/templates/billing/includes/plan_card.html` | макрос карточки | ✓ VERIFIED | 80 строк, макрос, импортируется `balance.html:8` |
| `app/templates/billing/includes/usage_meters.html` | макрос метра | ✓ VERIFIED | 40 строк, импорт `balance.html:9` |
| `app/templates/billing/includes/payment_row.html` | макрос строки истории | ✓ VERIFIED | 66 строк, импорт `balance.html:10` |
| `app/static/css/app.css` | `[data-plans]` с minmax(260px,1fr) | ✓ VERIFIED | `:1159-1161` |
| `app/templates/billing/plans.html` | ДОЛЖЕН отсутствовать (D-19) | ✓ VERIFIED | Удалён коммитом `752db3a`; ссылок не осталось |
| `tests/test_application/test_subscription_period.py` | 78 строк | ✓ VERIFIED | 10 тестов |
| `tests/test_application/test_plan_usage.py` | покрытие четырёх осей | ✓ VERIFIED | 680 строк, 22 теста |
| `tests/test_migrations/test_0017_payment_kind_and_plan.py` | round-trip ревизии | ✓ VERIFIED | 266 строк, 7 тестов |
| `tests/test_pages/test_billing_section.py` | интеграционное покрытие | ✓ VERIFIED | 785 строк, 22 теста |
| `tests/test_pages/test_billing_subscription.py` | сквозной тест слайса | ✓ VERIFIED | 284 строки, 10 тестов |
| `tests/test_routes/test_billing_webhook_source.py` | регрессия IP-гарда | ⚠️ ПРИСУТСТВУЕТ, ДЫРУ НЕ ЛОВИТ | 169 строк, 8 тестов; `test_without_a_configured_header_the_peer_address_is_used` фиксирует небезопасную ветку как корректную |
| `graphify-out/graph.json` | обновлённый граф | ✓ VERIFIED | mtime 16.08 05:25 > последний коммит кода 15.08 20:15 |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `POST /billing/subscribe` | `create_payment(kind='subscription')` | `billing.py:193-201` → 302 на confirmation_url (`:202`) | ✓ WIRED |
| `POST /api/billing/webhook` | `handle_webhook` | IP-гард (`routes/billing.py:152-158`) стоит ДО `request.json()` и вне `try` | ⚠️ WIRED, НО ГАРД ИНЕРТЕН В ПРОДЕ |
| `handle_webhook` | `_extend_subscription` | ветка `kind == KIND_SUBSCRIPTION` (`payment_service.py:215-216`) | ✓ WIRED |
| Идемпотентность | ДО ветвления по kind | `TERMINAL_STATUSES` на `:179`, ветвление на `:185`/`:215` | ✓ WIRED (последовательный случай); ✗ не держит конкурентный — гэп 2 |
| `settings.parsed_plan_limits` | форма подписки | `billing.py:79` → контекст `plans` → `balance.html:115-119` → `plan_card` | ✓ WIRED |
| `request.state.shell['nav_counts']` | числители осей ads/accounts | `billing.py:74` → `plan_axes(nav_counts=...)` (`:92`) → `plan_usage.py:176,179` | ✓ WIRED |
| `send_analytics.sends_in_current_month_query` | предикат `sent_at` | `plan_usage.py:46,168` | ✓ WIRED |
| `get_payment_history(limit=PAYMENT_LIST_CAP)` | контекст `payments` | `billing.py:106` → `balance.html:185-187` | ✓ WIRED |
| `is_same_origin` | обе формы оплаты + история | `common.py:318` ← `billing.py:181,241`, `history.py:913` | ✓ WIRED |
| `Subscription.expires_at` | показ срока | `get_shell_context` (`common.py:498-505`, запрос дословно совпадает с писателем) → `quota` → `billing.py:112` → `balance.html:82` | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Real Data | Status |
|---|---|---|---|---|
| `balance.html` блок 1 | `subscription.expires_at` | `Subscription` через шелл | Да | ✓ FLOWING |
| `balance.html` блок 2 | `usage` | `plan_axes`: `nav_counts` + один запрос (`Group`, `SendLog`) | Да | ✓ FLOWING |
| `balance.html` блок 3 | `plans` | `settings.parsed_plan_limits` (JSON конфига; прогон дал три плана с реальными ценами) | Да | ✓ FLOWING |
| `balance.html` блок 4 | `balance_info`, `packages` | `get_balance_info`, конфиг пакетов | Да | ✓ FLOWING |
| `balance.html` блок 5 | `payments`, `payments_total` | `get_payment_history`, `count_payments` — запросы к `payments` с предикатом владения | Да | ✓ FLOWING |

Ни одной статической подстановки, ни одного захардкоженного пустого пропса не найдено.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Тесты фазы (8 файлов) | `uv run pytest <8 файлов> -q` | `240 passed` за 169 с | ✓ PASS |
| Арифметика срока на краевых датах | `python -c "add_one_month(...)"` | 31.01→28.02, 31.12→31.01 (+год), 29.01.2028→29.02.2028 | ✓ PASS |
| D-04 обе половины | `python -c "next_expiry(...)"` | действующая 2026-09-01 → 2026-10-01; истёкшая 2026-06-01 → 2026-09-16 | ✓ PASS |
| Четыре оси и деление на ноль | `python -c "AXIS_ORDER, axis_percent(...)"` | `('ads','groups','sends','accounts')`; None→0, 0→0, 20/15→100 | ✓ PASS |
| Формат суммы только на показе | `python -c "format_amount(...)"` | `'1490.00' → '1 490 ₽'`, `'4900.50' → '4 900,50 ₽'` | ✓ PASS |
| Цены конфига машинной строкой | `python -c "parsed_plan_limits"` | `free 0.00 / basic 1490.00 / pro 4900.00`, у pro `ads=None, groups=None` | ✓ PASS |
| Отсутствие блокировки строки | `grep -rn with_for_update app/` | `none` | ✗ FAIL (гэп 2) |
| `format_amount` на NaN/Infinity | `python -c "format_amount('NaN')"` | `InvalidOperation` / `ValueError` — необработанное исключение | ✗ FAIL (warning-tier, WR) |

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| — | — | Конвенциональных `scripts/*/tests/probe-*.sh` в проекте нет; ни один план фазы probe не объявляет | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| BILL-05 | 05-01, 05-02, 05-04, 05-05, 05-06 | Пользователь может продлить текущую подписку | ✓ SATISFIED (тестовый стенд) | Формы `plan_card.html:72` и `balance.html:96` → `POST /billing/subscribe` → вебхук → `_extend_subscription`. `REQUIREMENTS.md:115` и `:235` — Complete. ⚠️ В проде не работает (D-26) |
| BILL-06 | 05-03, 05-04, 05-05, 05-06 | Потребление и остаток по четырём осям | ✓ SATISFIED | `AXIS_ORDER` → четыре метра; 22 теста. `REQUIREMENTS.md:116` и `:236` — Complete |
| BILL-07 | 05-02, 05-04, 05-05, 05-06 | История платежей | ✓ SATISFIED (тестовый стенд) | `get_payment_history` → блок истории с датой/суммой/статусом. `REQUIREMENTS.md:117` и `:237` — Complete. ⚠️ Статус «отклонён» в проде не появится (D-27) |

**Осиротевших требований нет.** `grep "Phase 5" REQUIREMENTS.md` даёт BILL-01…BILL-07; BILL-01, BILL-03, BILL-04 — baseline предыдущих фаз, BILL-02 сознательно перепомечен `Partial` планом 05-06 (D-13) и в эту фазу не входит (D-08). Все три заявленных ID (BILL-05, BILL-06, BILL-07) объявлены планами, реализованы и отмечены в ОБЕИХ таблицах трассировки.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `app/config.py` | 94 | Небезопасное умолчание (`""`), отключающее защиту | 🛑 Blocker | Гэп 1 |
| `docker-compose.prod.yml` | 78 | `--forwarded-allow-ips=*` без сопровождающей переменной заголовка | 🛑 Blocker | Гэп 1 |
| `app/services/payment_service.py` | 171-179 | Check-then-act без блокировки | 🛑 Blocker | Гэп 2 |
| `app/pages/common.py` | 272-281 | Необработанное `InvalidOperation`/`ValueError` на `NaN`/`Infinity` | ⚠️ Warning | Падение страницы тарифов при мусоре в конфиге цен или в `payments.amount_value`. Пользовательским вводом недостижимо |
| `app/services/payment_service.py` | 277-281 | Смена плана при продлении сохраняет накопленный срок | ⚠️ Warning | Понижение тарифа превращает оплаченный остаток старшего плана в дни младшего. Семантика смены плана нигде не объявлена — ни в must_haves, ни в D-решениях |
| — | — | Маркеры долга `TBD` / `FIXME` / `XXX` | ✓ Нет | Прогон по 19 файлам фазы — ноль вхождений. `TODO` / `HACK` / `PLACEHOLDER` — тоже ноль |

### Human Verification Required

Перечисленное ниже переносится в очередь UAT фазы. Три первых пункта записаны планом 05-06 как **НЕ выполненные** — собственный критерий плана «все три пункта пройдены» **не выполнен**, и это здесь не сглаживается.

#### 1. Мобильная ширина 375px (критерий 4)

**Test:** Открыть `/billing` в браузере на 375px с тремя планами, четырьмя осями и историей платежей длиннее экрана.
**Expected:** Карточки складываются в одну колонку; подписи `[data-cell-label]` едут вместе со значениями; горизонтальной прокрутки нет; кнопки нажимаемы.
**Why human:** Браузерного харнесса в проекте нет; относящиеся тесты читают CSS как текст и сами это признают.

#### 2. Настоящий платёж в тестовом магазине ЮKassa

**Test:** Форма → `confirmation_url` → возврат → приход уведомления → срок на `/billing`.
**Expected:** До прихода уведомления срок НЕ сдвинут; после — сдвинут.
**Why human:** Всё покрытие на моках; при D-26 на проде физически недостижимо.

#### 3. Отменённый платёж со статусом «отклонён»

**Test:** Отменить платёж и открыть историю.
**Expected:** Бейдж «отклонён».
**Why human:** Заблокировано D-27 — уведомление не приходит, проверять нечего.

#### 4. Понятность статуса «в обработке» при раннем возврате

**Test:** Вернуться с ЮKassa до прихода вебхука.
**Expected:** Человек читает строку как «деньги в обработке», а не «оплата не прошла».
**Why human:** Backstop-пункт плана 05-04 — суждение о формулировке.

### Прохибиции

| # | Prohibition | Tier | Status |
|---|---|---|---|
| 05-01 | MUST NOT продлевать подписку иначе как подтверждённым вебхуком | judgment | ⚠️ FLAGGED — non-authoritative LLM-judge: соблюдена. `_extend_subscription` зовётся только из `handle_webhook`; `billing_page` не пишет; обработчика возврата нет. **unverified-prohibition — human review recommended** |
| 05-01 | MUST NOT сжигать неистраченный остаток | test | ✓ VERIFIED — enforcement wired: `test_next_expiry_keeps_the_unused_remainder`, `test_webhook_extends_an_active_subscription_without_burning_the_remainder` |
| 05-01 | MUST NOT показывать цену, отличную от списываемой | judgment | ⚠️ FLAGGED — цена на экране и в платеже из одной записи конфига. Оговорка: при ПОНИЖЕНИИ плана списывается объявленное, но получаемое отличается от ожидаемого (warning выше). **human review recommended** |
| 05-02 | MUST NOT показывать терминальный платёж как «в обработке» | test | ⚠️ VERIFIED В КОДЕ, НАРУШЕНА В ПРОДЕ — enforcement wired (`test_a_canceled_payment_is_named_rejected`), но без D-27 отменённый платёж в проде остаётся `pending` навсегда |
| 05-03 | MUST NOT превращать показанный лимит в гейт | test | ✓ VERIFIED — `plan_axes` потребляется ТОЛЬКО страницей `/billing` (grep по `app/`); `check_balance_cached` разрешает всё, кроме `send`; `tests/test_routes/test_limits.py` на месте |
| 05-03 | MUST NOT показывать по оси число, противоречащее соседнему счётчику | judgment | ⚠️ FLAGGED — оба числителя из одного `nav_counts`; второго источника нет. **human review recommended** |
| 05-04 | MUST NOT молча обрезать список платежей | test | ✓ VERIFIED — `test_the_payment_list_cap_names_itself` + `test_a_full_list_at_the_cap_is_not_reported_truncated` |
| 05-05 | MUST NOT подписывать элемент величиной, которой он не показывает | test | ✓ VERIFIED — `base.html:75` «Баланс сообщений»; `test_the_sidebar_widget_names_the_message_balance_not_the_plan` |
| 05-05 | MUST NOT оформлять превышение лимита как провинность | judgment | ⚠️ FLAGGED — тревожного варианта у метра нет, шкала встаёт на 100, подпись называет настоящие числа. **human review recommended** |
| 05-06 | MUST NOT оставлять требование помеченным выполненным, когда код его не выполняет | judgment | ⚠️ FLAGGED — BILL-02 переведён в `Partial` в обеих таблицах. **human review recommended** |

### Gaps Summary

Функционально фаза сделана: все четыре критерия ROADMAP имеют настоящую реализацию с прослеженным потоком данных от БД до разметки, 240 тестов фазы зелёные, ни одного маркера долга, ни одной заглушки, ни одного осиротевшего требования. Заявленный снос долгов исполнен физически — неподключённый `plans.html` удалён, JSON-маршрут покупки удалён, виджет сайдбара переподписан.

Блокируют два дефекта, найденных код-ревью и подтверждённых здесь независимо, — оба на входе, где принимается решение выдать платный ресурс:

**Гэп 1 — гард вебхука инертен в отгруженной прод-конфигурации.** Это не «недонастроенное окружение», а свойство репозитория: умолчание в `app/config.py:94` пустое, `docker-compose.prod.yml:78` запускает uvicorn с `--forwarded-allow-ips=*`, и в этой комбинации `request.client.host` — это подделываемый заголовок вызывающего. Правильная логика чтения справа написана и в проде не исполняется. Дыра живая **независимо от D-26**: вебхук пакетов сообщений обслуживается текущей прод-ревизией `0012`. Фаза при этом сняла единственную прежнюю преграду — утечку `yookassa_payment_id` в браузер, — то есть заменила слабую защиту на видимость защиты. Существующая запись в `STATE.md` — организационная мера; свойством кода она не является, и следующий деплой без ручного шага её не соблюдёт.

**Гэп 2 — двойное зачисление при конкурентной доставке.** `select(Payment)` без `with_for_update()` (ноль вхождений во всём `app/`), `bal.balance += amount` в Python, отсутствие уникального ограничения на `subscriptions.user_id`. Две одновременные доставки зачисляют дважды и теряют одну запись; `_extend_subscription` вставляет вторую строку подписки, которую читатель шелла не увидит. Тесты покрывают только последовательную повторную доставку. Гэп 1 напрямую усиливает гэп 2: без работающего гарда конкурентные доставки инициирует кто угодно.

Отдельно и не как гэп: **производственный разрыв, принятый владельцем.** Критерий 1 в проде не выполнен (D-26, очередь `0013`…`0017`), критерий 3 в проде показывает неправду (D-27). Три пункта ручной проверки не выполнены; собственный критерий плана 05-06 «все три пункта пройдены» не достигнут. Критерий 4 доказан только на уровне объявления CSS — браузером его в этом проекте проверить нечем.

---

_Verified: 2026-08-16T06:20:00Z_
_Verifier: Claude (gsd-verifier)_

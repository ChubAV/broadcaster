---
phase: 05-tarify
verified: 2026-08-16T15:30:00Z
status: gaps_found
score: 106/121 must-haves verified
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/5
  previous_verified: 2026-08-16T06:20:00Z
  gaps_closed:
    - "Вебхук с недоверенного адреса отвергается 403 и не доходит до handle_webhook (гэп 1, план 05-07)"
    - "Подтверждённый платёж зачисляется ровно один раз (гэп 2, план 05-08)"
  gaps_remaining: []
  regressions:
    - "Новый блокер, не существовавший в прошлом раунде как отдельный пункт: `_apply_extension` безусловно перезаписывает `subscription.plan`, и подтверждённый платёж младшего тарифа МОЛЧА понижает действующий старший. Воспроизведено независимо на боевом пути кода."
gaps:
  - truth: "Понижение тарифа не превращает оплаченный остаток старшего плана в дни младшего молча (must_haves плана 05-10; та же прохибиция BILL-05/fairness, помеченная планом `resolved`)"
    status: failed
    reason: "Подтверждено НЕЗАВИСИМЫМ воспроизведением на настоящем пути кода (свой движок SQLite в памяти, вызов handle_webhook дважды, без единой правки app/). Пользователь на `free`, два `pending` платежа: `pro`, затем `basic`. После первого: plan=pro, expires_at=2026-09-16. После второго: plan=basic, expires_at=2026-10-16. Итог прогона: `CR-01 CONFIRMED — plan silently downgraded to 'basic' after paying for both`. Оплаченный МЕСЯЦ старшего тарифа превратился в дни младшего — ровно то, что must_have запрещает, и притом молча: строки журнала о понижении нет, `subscription_payment_succeeded` печатает `plan=basic` как обычный успех. Корень: `app/services/payment_service.py:504-509` — `if db_payment.plan: subscription.plan = db_payment.plan` без единой сверки ранга. `PLAN_ORDER` (`app/constants.py:70`) читается РОВНО В ОДНОМ файле — `app/pages/billing.py:133` — то есть только на стадии НАМЕРЕНИЯ (гард формы и состояние кнопки карточки); грep по `app/` даёт ноль вхождений `PLAN_ORDER` в `payment_service.py`. Правило `upgrade-only` существует на входе и не существует там, где приходят деньги. Заявленное планом покрытие «закреплена тестами на basic→pro и pro→basic с неистёкшим остатком» выполнено ПОЛОВИНОЙ: `test_an_upgrade_does_not_burn_the_paid_remainder` действительно доходит до `handle_webhook`, а `test_a_downgrade_is_refused_with_a_named_reason` останавливается на 302 гарда формы и стадию применения не трогает вовсе."
    artifacts:
      - path: "app/services/payment_service.py"
        issue: "Строки 504-509 `_apply_extension`: безусловная перезапись `subscription.plan`. Ни импорта `PLAN_ORDER`, ни сверки ранга, ни записи в журнал о понижении"
      - path: "tests/test_pages/test_billing_payment_errors.py"
        issue: "Строки 696-711 `test_a_downgrade_is_refused_with_a_named_reason` проверяет ТОЛЬКО гард намерения (302 на `?error=downgrade`, ноль платежей). Регрессии на стадию применения — подтверждённый платёж младшего тарифа при действующем старшем — в суите нет ни одной"
      - path: "app/services/payment_service.py"
        issue: "Докстринг `_extend_subscription` (строки 434-440) утверждает «понижение при действующей подписке не предлагается карточкой и не принимается гардом», умалчивая, что подтверждённый платёж понижение ПРИМЕНЯЕТ. Строки 447-452 объявляют это намеренным, но обоснование («отказать оплаченному платежу хуже») оправдывает НЕ-ОТКАЗ, а не понижение: сдвинуть срок и сохранить старший тариф удовлетворяет обоим ограничениям"
    missing:
      - "Сверка ранга в `_apply_extension` по тому же `PLAN_ORDER`, что читает гард формы: план ТОЛЬКО повышается, срок двигается всегда"
      - "Строка журнала о сохранении старшего тарифа — сегодня понижение не оставляет следа вообще"
      - "Регрессия на стадию ПРИМЕНЕНИЯ: два подтверждённых платежа `pro`, затем `basic` → `plan == 'pro'`, срок сдвинут дважды"
  - truth: "`.planning/STATE.md` — единственное место записи бухгалтерии фазы: CR-01 и CR-02 закрыты, отложенные находки собраны одной записью (объявленный артефакт планов 05-08 и 05-10)"
    status: failed
    reason: "Артефакт объявлен в `files_modified` ОБОИХ планов и не изменён ни одним. Проверено: mtime `.planning/STATE.md` — 16.08 11:09, то есть РАНЬШЕ исполнения 05-08 (12:30) и 05-10 (14:20). Строки 89 и 90 по-прежнему несут 🔴 открытые записи `[Phase 5, CR-01]` и `[Phase 5, CR-02]`, и их содержимое теперь ЛОЖНО: строка 89 утверждает «`app/config.py:94` даёт значение `\"\"`» (сейчас `X-Real-IP`, строка 108) и «правки docker-compose не нужны» (запись YOOKASSA_WEBHOOK_CLIENT_IP_HEADER добавлена, строка 27); строка 90 утверждает «`select(Payment)` без `with_for_update()`» и «уникального индекса по `user_id` нет» (обе половины закрыты — `payment_service.py:291`, ревизия `0018`). Грепа по `05-07`/`05-08`/`05-09`/`05-10`, `WR-07`, `WR-10` в STATE.md нет ни одного. Оба SUMMARY признают это честно («в режиме worktree STATE.md правит оркестратор», 05-08-SUMMARY:319, 05-10-SUMMARY:178-184) — то есть претензии SUMMARY тут верны, а артефакт всё равно отсутствует. Тяжесть не в бухгалтерии как таковой: единственный операционный документ проекта СЕЙЧАС говорит читателю, что дыра гарда вебхука и двойное зачисление открыты, а закрытое понижение тарифа не упоминает вовсе."
    artifacts:
      - path: ".planning/STATE.md"
        issue: "Строки 89-90: 🔴 записи CR-01/CR-02 не сняты и фактически устарели; ни одной записи о планах 05-07…05-10 и об отложенных находках"
    missing:
      - "Снятие 🔴 CR-01 и CR-02 со ссылкой на закрывшие их планы (05-07, 05-08) и на доказавшие закрытие регрессии"
      - "Запись о новом блокере `_apply_extension` — сегодня он не зафиксирован НИГДЕ, кроме 05-REVIEW.md и этого отчёта"
      - "Сводная запись отложенных находок (WR-07, WR-10 и прочие), объявленная планом 05-10"
deferred: []
behavior_unverified_items:
  - truth: "Раздел тарифов пригоден к использованию на мобильных ширинах (критерий 4 ROADMAP)"
    test: "Открыть /billing в браузере на ширине 375px с реальными данными: три карточки планов, четыре метра, история платежей длиннее экрана, блок пакетов"
    expected: "Карточки планов складываются в одну колонку; подписи колонок истории ([data-cell-label]) едут вместе со значениями; ни один блок не требует горизонтальной прокрутки; кнопки оплаты нажимаемы пальцем (порог проекта 44px)"
    why_human: "Браузерного/e2e-харнесса в проекте нет — grep по pyproject.toml на playwright/selenium/puppeteer пуст. Все относящиеся тесты (test_billing_plans_grid_is_declared_folding, test_billing_plans_grid_rule_does_not_redefine_the_dashboard_grid, test_billing_payment_buttons_declare_the_project_touch_height) читают CSS и HTML как ТЕКСТ и проверяют ОБЪЯВЛЕНИЕ правила, а не отрисовку. План 05-09 закрыл известный дефект порога 44px на уровне объявления; отрисовка, переполнение и попадание пальцем грепом непроверяемы."
human_verification:
  - test: "Открыть /billing на 375px и пройти раздел глазами (см. behavior_unverified_items выше)"
    expected: "Одна колонка, никакой горизонтальной прокрутки, кнопки нажимаемы"
    why_human: "Браузерного харнесса в проекте нет"
  - test: "Настоящий платёж в тестовом магазине ЮKassa: форма → confirmation_url → возврат → приход уведомления → сдвинутый срок на /billing"
    expected: "Срок НЕ двигается до прихода уведомления и двигается после него"
    why_human: "Боевого доступа к API ЮKassa у исполнителя нет, всё покрытие на моках. Backstop-пункт must_haves планов 05-01 и 05-06. При решении D-26 недостижим на проде (колонок payments.kind/plan там нет)."
  - test: "Первое настоящее уведомление ЮKassa после выката проходит гард источника"
    expected: "Боевой nginx действительно проставляет X-Real-IP именно на маршруте вебхука, и настоящее уведомление получает 200, а не 403"
    why_human: "Backstop-пункт must_haves плана 05-07. Поведение боевого nginx на боевом маршруте кодом репозитория не проверяется. Цена ошибки названа планом прямо: отказ гарда молча останавливает приём денег — теперь отказ пишется уровнем error (routes/billing.py:98), но подтвердить проход может только первое настоящее уведомление."
  - test: "Отменённый платёж получает статус «отклонён» на экране истории"
    expected: "Строка платежа показывает бейдж «отклонён», а не «в обработке»"
    why_human: "Заблокирован: владелец не подтвердил подписку на событие payment.canceled в кабинете ЮKassa (D-27). Состав событий задаётся вне репозитория."
  - test: "Пользователь, вернувшийся с ЮKassa до прихода вебхука, понимает, что платёж ещё в обработке"
    expected: "Человек читает строку истории со статусом «в обработке» как «деньги в обработке», а не как «оплата не прошла»"
    why_human: "Backstop-пункт must_haves планов 05-04 и 05-10: понятность формулировки — суждение человека."
  - test: "Сообщение об отказе оплаты («ЮKassa не создала платёж») прочитывается как «попробуйте ещё раз»"
    expected: "Не читается как «с вас списали и не зачли»"
    why_human: "Backstop-пункт must_haves плана 05-10: понятность формулировки судится человеком."
  - test: "ПРОХИБИЦИЯ (judgment-tier, НЕ ЗЕЛЁНАЯ): «MUST NOT превращать оплаченный остаток старшего тарифа в дни младшего без объявленного правила и без слова пользователю до нажатия кнопки» — план 05-10 пометил её `resolved`"
    expected: "Владелец решает: считать ли поведение `_apply_extension` нарушением этой прохибиции и требовать сверки ранга на стадии применения"
    why_human: "unverified-prohibition — human review recommended. Автономный вердикт LLM-судьи (НЕ АВТОРИТЕТНЫЙ): прохибиция НАРУШЕНА — воспроизведено, что остаток старшего тарифа становится днями младшего, и слова пользователю до нажатия кнопки в этом сценарии нет, потому что гард формы в нём не срабатывает вовсе (действующей подписки на момент нажатия нет). Пометка `resolved` в плане 05-10 доказательствами в коде не подтверждается."
---

# Phase 5: Тарифы — Verification Report (раунд 2, после закрытия гэпов)

**Phase Goal:** Пользователь понимает, сколько ресурса тарифа он израсходовал, за что платил и может продлить подписку не выходя из раздела.
**Verified:** 2026-08-16T15:30:00Z
**Status:** gaps_found
**Re-verification:** Да — после планов 05-07…05-10, закрывавших гэпы раунда 1

## Вердикт по CR-01 — прямой ответ на поставленный вопрос

Задание требует явно сказать, затрагивает ли CR-01 критерий 1 или это отдельный
дефект корректности вне четырёх критериев. **Ответ: отдельный дефект
корректности, ВНЕ четырёх критериев — и при этом блокер фазы.**

Обоснование, почему НЕ критерий 1. Критерий 1 звучит «пользователь может
**продлить текущую** подписку … и сразу увидеть **обновлённый срок действия**».
Оба наблюдаемых свойства держатся:

- На продлении СВОЕГО тарифа перезапись плана — тождественная операция:
  `db_payment.plan == subscription.plan`, и строка 509 записывает то же значение.
  Дефект в этом сценарии не наблюдаем вовсе.
- Даже в сценарии воспроизведения `expires_at` сдвигается КОРРЕКТНО и дважды
  (2026-09-16 → 2026-10-16). Срок — ровно то, что называет критерий 1, — верен.
  Теряется ТАРИФ, а тариф критерий 1 не называет.
- Путь показа срока не тронут: запрос читателя (`app/pages/common.py:509-513`)
  дословно совпадает с запросом писателя (`payment_service.py:493-500`).

Почему это тем не менее блокер. Дефект фальсифицирует **явно объявленный
must_have плана 05-10** («понижение не превращает оплаченный остаток старшего
плана в дни младшего молча») и **прохибицию того же плана**, помеченную
`resolved`. Он лежит на денежном пути, воспроизводится без атакующего, и цена
названа ревьюером верно: 4 900 ₽ + 1 490 ₽ уплачено, тариф — Basic. По дереву
решений шага 9 (правило 1: FAILED-истина или блокер-антипаттерн) фаза получает
`gaps_found` независимо от того, что все четыре критерия ROADMAP выполнены.

Побочное наблюдение, усиливающее вывод: ближайший к дефекту критерий — НЕ
первый, а **второй**. Молча подменённый тариф означает, что четыре метра
рисуются по лимитам ЧУЖОГО плана. Но механика показа при этом исправна —
испорчены данные на пути записи, а не витрина; поэтому критерий 2 засчитан
выполненным, а дефект отнесён к пути записи.

## Goal Achievement

### Observable Truths — критерии ROADMAP

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| SC1 | Пользователь может продлить текущую подписку из раздела и сразу увидеть обновлённый срок | ✓ VERIFIED (тестовый стенд) | Цепочка цела: формы `plan_card.html:94` и `balance.html:120` → `POST /billing/subscribe` (`app/pages/billing.py`) → `create_payment(kind='subscription')` → 302 на `confirmation_url` → вебхук → `_extend_subscription` (`payment_service.py:396`) → `Subscription.expires_at`. Показ читает ТУ ЖЕ строку тем же запросом (`common.py:509-513` ≡ `payment_service.py:493-500`). Продление своего тарифа принимается гардом (`test_renewing_the_own_live_plan_is_still_accepted`), остаток не сгорает (`test_an_upgrade_does_not_burn_the_paid_remainder` — доходит до `handle_webhook`). ⚠️ В проде не выполнен (D-26, база на ревизии 0012). |
| SC2 | Пользователь видит потребление и остаток по всем ЧЕТЫРЁМ осям | ✓ VERIFIED | `AXIS_ORDER = (ads, groups, sends, accounts)` (`plan_usage.py:64`) → `plan_axes` → контекст `usage` (`billing.py:199,257`) → цикл `usage_meter` (`balance.html:132`). Регрессия зелёная: 22 теста `test_plan_usage.py` в прогоне 303 passed. |
| SC3 | Пользователь видит историю платежей с датой, суммой и статусом | ✓ VERIFIED (тестовый стенд) | `get_payment_history` + `count_payments` (`billing_service.py:179`, `:210`) → контекст `payments` (`billing.py:213-214, 264-267`) → `rowhead(PAY_COLUMNS, PAY_COLS)` + `payment_row` (`balance.html:212,224`). ⚠️ Статус «отклонён» в проде не появится (D-27). |
| SC4 | Раздел пригоден к использованию на мобильных ширинах | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Известный дефект порога нажимаемости закрыт планом 05-09 на уровне ОБЪЯВЛЕНИЯ: `[data-plan-cta] .btn { min-height: 44px }` (`app.css:1190`), атрибут стоит на всех трёх формах оплаты (`plan_card.html:94`, `balance.html:120`, `balance.html:189`), правило адресовано атрибуту, а не голому `.btn`. Складывание объявлено (`[data-plans]` minmax 260px, `[data-metrics]` minmax 210px), `[data-quota]` скрыт на ≤860px (`app.css:475`). Но браузера в суите нет (playwright/selenium/puppeteer в pyproject.toml отсутствуют) — отрисовка не проверена ничем. |

**Score:** 3/4 критериев ROADMAP выполнены (1 присутствует, поведенчески не проверен)

### Observable Truths — гэпы раунда 1

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| Г1 | Вебхук с недоверенного адреса отвергается 403 и не доходит до handle_webhook | ✓ VERIFIED — **гэп закрыт** | Проверено независимо, не по SUMMARY. Умолчание непустое: `app/config.py:108` → `X-Real-IP`. Деплойный артефакт пинует значение: `docker-compose.prod.yml:27` → `YOOKASSA_WEBHOOK_CLIENT_IP_HEADER: ${…:-X-Real-IP}`. Отказ по умолчанию ЗАКРЫВАЕТ гард: пустое имя → `logger.error("webhook_ip_header_not_configured")` → `None` → 403 (`routes/billing.py:89-99, 181-185`). Ветка адреса пира УДАЛЕНА физически: `grep "request.client\|\.client\.host" app/routes/billing.py` → ноль строк. Чтение справа сохранено (`:103`). Регрессия ЧЕРЕЗ настоящий `ProxyHeadersMiddleware(trusted_hosts="*")` существует и зелёная: `tests/test_routes/test_billing_webhook_proxy_headers.py`, прогон в этой верификации — **10 passed**. |
| Г2 | Подтверждённый платёж зачисляется ровно один раз при КОНКУРЕНТНОЙ доставке | ✓ VERIFIED — **гэп закрыт** | Заявка — настоящий compare-and-swap: `update(Payment).where(id, status.not_in(TERMINAL_STATUSES)).values(...)`, `rowcount == 1` (`payment_service.py:215-224`). Стоит ПЕРЕД начислением и в той же транзакции (`:354`), проигравший делает rollback, пишет `webhook_claim_lost` и возвращает True (`:357-359`) — 5xx ЮKassa не получает. Блокировка строки на PostgreSQL добавлена: `.with_for_update()` (`:291`). Начисление ушло на сторону СУБД: `update(MessageBalance).values(balance=MessageBalance.balance + amount)` (`billing_service.py:95-97`) — потерянное обновление невозможно. Вторая строка подписки закрыта частичным уникальным индексом ревизии `0018` с обработкой `IntegrityError` в savepoint (`payment_service.py:460-486`). Прогон в этой верификации: `test_payment_concurrency.py` + `test_0018_subscriptions_unique_user.py` — **22 passed**. |

### Observable Truths — новые must_haves планов 05-07…05-10

| # | Truth (план) | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Отказ ненастроенного заголовка виден уровнем `error`, а не тишиной (05-07) | ✓ VERIFIED | `routes/billing.py:98`; `test_an_unconfigured_header_is_reported_at_error_level` |
| 2 | Аварийный выключатель `verify_ip=false` по-прежнему пропускает (05-07) | ✓ VERIFIED | `routes/billing.py:179`; `test_the_kill_switch_still_lets_any_source_through` |
| 3 | Ни один тест не восстанавливает зелёный отключением гарда (05-07) | ✓ VERIFIED | `test_billing_webhook_source.py` (8 тестов) зелёный в прогоне 303 passed; небезопасный `test_without_a_configured_header_the_peer_address_is_used` из прошлого раунда в файле отсутствует |
| 4 | Заявка стоит перед любым начислением и в той же транзакции (05-08) | ✓ VERIFIED | `payment_service.py:350-365`; единственный `commit` в конце ветки |
| 5 | Проигравшая доставка возвращает True, а не 5xx (05-08) | ✓ VERIFIED | `:359`; `test_the_losing_delivery_answers_accepted` |
| 6 | Проигрыш виден отдельным ключом журнала (05-08) | ✓ VERIFIED | `webhook_claim_lost` (`:321`, `:358`); `test_the_losing_delivery_is_visible_in_the_log` |
| 7 | Восемь тестов последовательной идемпотентности зелёные БЕЗ правки (05-08) | ✓ VERIFIED | `test_payment_service.py` в прогоне 303 passed; быстрый выход на `TERMINAL_STATUSES` сохранён (`:298-300`) |
| 8 | C1/M3: порог 44px на всех трёх формах оплаты, адресован `[data-plan-cta]` (05-09) | ✓ VERIFIED | `app.css:1190` + три места атрибута; правило не трогает голый `.btn` 26 страниц |
| 9 | `format_amount('NaN'/'Infinity')` возвращает исходную строку, а не падает (05-09) | ✓ VERIFIED — **прогнано поведенчески** | Прогон в этой верификации: `'NaN'→'NaN'`, `'Infinity'→'Infinity'`, `'-Infinity'→'-Infinity'`, `'abc'→'abc'`, `''→''`; годные значения не сломаны: `'1490.00'→'1 490 ₽'`, `'4900.50'→'4 900,50 ₽'`. Ноль не подставляется — возврат КАК ЕСТЬ |
| 10 | U4/U5: ноль пакетов рисует пустое состояние со словами (05-09) | ✓ VERIFIED | `balance.html:177-197` — `{% if packages %}` … `{% else %}` → `empty_state('Пакеты сообщений временно недоступны', …)`; пустое состояние при выключенных платежах отдельной строкой (`:201`) — причины пустоты не слиты |
| 11 | R23: `[data-quota]` скрыт при ≤860px (05-09) | ✓ VERIFIED | `app.css:475` |
| 12 | U1/U2/U3: отказ API ЮKassa возвращает человека на /billing с названной причиной, обе формы одинаково (05-10) | ✓ VERIFIED | `PaymentCreationError` (`payment_service.py:51`, поднимается на `:162` после `logger.error("payment_create_failed")` на `:151`) → обе формы ловят и редиректят на `/billing?error=payment` (`billing.py:362-366`, `:435-436`) → `_payment_error_message` (`:87`) → контекст `error_message` (`:271`) → плашка (`balance.html:80`). Покрытие: `test_billing_payment_errors.py` зелёный в прогоне 303 passed |
| 13 | Текст стороннего исключения не печатается; неизвестный код не печатает ничего (05-10) | ✓ VERIFIED | `_payment_error_message` — закрытое множество; `test_the_third_party_exception_text_never_reaches_the_screen`, `test_an_unknown_reason_code_prints_nothing_at_all`, `test_the_reason_codes_of_the_handlers_are_exactly_the_known_set` |
| 14 | Отказ создания платежа не оставляет строку payments (05-10) | ✓ VERIFIED | `raise` стоит ДО `Payment(...)` (`payment_service.py:162` против `:166`); `test_a_failed_payment_leaves_no_row_in_the_journal` |
| 15 | C2: судьба оплаченного остатка объявлена решением владельца (05-10) | ⚠️ ЧАСТИЧНО | Правило записано ТАМ, где двигается срок (докстринг `_extend_subscription:429-445`), и это закреплено `test_the_switch_semantics_are_named_in_the_place_that_moves_the_date`. Но объявленное правило и исполняемый код расходятся — см. гэп 1 ниже |
| 16 | Понижение не превращает оплаченный остаток старшего плана в дни младшего молча (05-10) | ✗ **FAILED (BLOCKER)** | Воспроизведено независимо на боевом пути кода. См. раздел «Вердикт по CR-01» и `gaps` |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `app/config.py` | непустое умолчание заголовка | ✓ VERIFIED | `:108` → `"X-Real-IP"`; корень гэпа 1 устранён |
| `docker-compose.prod.yml` | явная запись YOOKASSA_WEBHOOK_CLIENT_IP_HEADER | ✓ VERIFIED | `:27`, с безопасным умолчанием подстановки |
| `app/routes/billing.py` | отказ по умолчанию закрывает гард | ✓ VERIFIED | `:89-103`; ветки адреса пира нет ни одной строкой |
| `tests/test_routes/test_billing_webhook_proxy_headers.py` | регрессия через ProxyHeadersMiddleware | ✓ VERIFIED | 15879 байт, 10 тестов, настоящий `ProxyHeadersMiddleware(trusted_hosts="*")` (`:64`); прогон — 10 passed |
| `app/services/payment_service.py` | `_claim_payment` — атомарная заявка | ✓ VERIFIED | `:196-224`, условный UPDATE + `rowcount == 1`; `_mirror_claim` через `set_committed_value` |
| `app/services/billing_service.py` | приращение на стороне СУБД | ✓ VERIFIED | `:95-97` |
| `alembic/versions/0018_subscriptions_unique_user.py` | частичный уникальный индекс | ✓ VERIFIED | Файл на месте; `unique=True` (`app/models/subscription.py:24`); round-trip покрыт `test_0018_subscriptions_unique_user.py` |
| `tests/test_services/test_payment_concurrency.py` | регрессия на КОНКУРЕНТНУЮ доставку | ✓ VERIFIED | 8 тестов, две сессии, файловая SQLite; прогон зелёный |
| `app/static/css/app.css` | `[data-plan-cta] .btn { min-height: 44px }` | ✓ VERIFIED | `:1190` |
| `app/pages/common.py` | `format_amount` устойчив к негодной строке | ✓ VERIFIED | Прогнано поведенчески — см. истину 9 |
| `app/templates/billing/balance.html` | пустое состояние пакетов + плашка отказа | ✓ VERIFIED | `:177-201` и `:80` |
| `app/pages/billing.py` | `_payment_error_message`, закрытое множество | ✓ VERIFIED | `:87`, `:271` |
| `tests/test_pages/test_billing_payment_errors.py` | покрытие всех веток отказа | ✓ VERIFIED | 32 теста; зелёные |
| `.planning/STATE.md` | CR-01/CR-02 закрыты, отложенные находки одной записью | ✗ **MISSING** | Файл не изменён: mtime 16.08 11:09 < исполнение 05-08 (12:30) и 05-10 (14:20). Строки 89-90 несут устаревшие 🔴 записи. Оба SUMMARY признают это честно |

### Key Link Verification

| From | To | Via | Status |
| ---- | --- | --- | ------ |
| `ProxyHeadersMiddleware(trust all)` | 403 | перезапись пира левым `X-Forwarded-For` → `_webhook_client_ip` читает ТОЛЬКО настроенный заголовок → `_is_trusted_source` → 403 | ✓ WIRED (доказано регрессией) |
| `app/config.py` умолчание `X-Real-IP` | заголовок, который nginx ПЕРЕЗАПИСЫВАЕТ | `Settings` → `_webhook_client_ip` | ✓ WIRED |
| `docker-compose.prod.yml environment` | гард на боевом стенде | `:27` → `Settings` | ✓ WIRED (боевая проверка — backstop, в UAT) |
| `handle_webhook` → `_claim_payment` | ноль строк → выход без начисления | `:354-359` | ✓ WIRED |
| `handle_webhook` → `_claim_payment` → ветка `kind` | `add_messages` / `_extend_subscription` → один commit | `:361-383` | ✓ WIRED |
| уникальность `subscriptions` | невозможность второй активной строки | ревизия `0018` + savepoint-обработка `IntegrityError` | ✓ WIRED |
| `create_payment` → `PaymentCreationError` | 302 на `/billing?error=payment` | `billing.py:362-366`, `:435-436` | ✓ WIRED |
| `GET /billing?error=<code>` → `_payment_error_message` | плашка в `balance.html` | `billing.py:271` → `balance.html:80` | ✓ WIRED |
| `[data-plan-cta]` на трёх формах | правило `min-height` | `app.css:1190` | ✓ WIRED |
| **`PLAN_ORDER` → стадия ПРИМЕНЕНИЯ платежа** | **`_apply_extension`** | **связи нет** | ✗ **NOT_WIRED** — `PLAN_ORDER` читается только `app/pages/billing.py:133` (стадия намерения); в `payment_service.py` ноль вхождений |
| `Subscription.expires_at` | показ срока | `common.py:509-513` (запрос дословно совпадает с писателем) | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `balance.html` блок 1 | `subscription.expires_at` | `Subscription` через шелл | Да | ✓ FLOWING |
| `balance.html` блок 1 | `subscription.plan` | `Subscription.plan` — пишется `_apply_extension` | Да, но значение может быть **МОЛЧА ПОНИЖЕНО** | ⚠️ FLOWING, ИСТОЧНИК ПОРТИТ ЗНАЧЕНИЕ |
| `balance.html` блок 2 | `usage` | `plan_axes`: `nav_counts` + один запрос | Да | ✓ FLOWING |
| `balance.html` блок 3 | `plans` | `settings.parsed_plan_limits` | Да | ✓ FLOWING |
| `balance.html` блок 4 | `balance_info`, `packages` | `get_balance_info`, конфиг пакетов; ноль → `empty_state` | Да | ✓ FLOWING |
| `balance.html` блок 5 | `payments`, `payments_total` | `get_payment_history`, `count_payments` | Да | ✓ FLOWING |
| плашка отказа | `error_message` | `_payment_error_message` по коду из query | Да (закрытое множество) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Гэп 1 закрыт: подделанный `X-Forwarded-For` через настоящий ProxyHeadersMiddleware | `uv run pytest tests/test_routes/test_billing_webhook_proxy_headers.py -q` | `10 passed` | ✓ PASS |
| Гэп 2 закрыт: конкурентная доставка + round-trip 0018 | `uv run pytest tests/test_services/test_payment_concurrency.py tests/test_migrations/test_0018_... -q` | `22 passed` | ✓ PASS |
| Регрессия по фазе (8 файлов) | `uv run pytest <8 файлов> -q` | `303 passed` за 226 с | ✓ PASS |
| Устойчивость денежной подписи | `python -c "format_amount('NaN'/'Infinity'/'abc'/'1490.00')"` | `'NaN'`, `'Infinity'`, `'abc'`, `'1 490 ₽'` — ни одного исключения | ✓ PASS |
| Ветка адреса пира удалена | `grep "request.client\|\.client\.host" app/routes/billing.py` | ноль строк | ✓ PASS |
| **Сверка ранга плана на стадии применения** | `grep -rn PLAN_ORDER app/` | только `constants.py:70` и `pages/billing.py:10,133` — в `payment_service.py` НОЛЬ | ✗ **FAIL** |
| **Понижение тарифа подтверждённым платежом** | standalone-прогон `handle_webhook` дважды (pro → basic) на своём движке SQLite | `after pro: pro 2026-09-16` → `after basic: basic 2026-10-16` → `CR-01 CONFIRMED` | ✗ **FAIL** |
| Бухгалтерия фазы записана в STATE.md | `ls -la .planning/STATE.md` + `grep "05-07\|05-08\|05-09\|05-10\|WR-07\|WR-10"` | mtime 16.08 11:09 (раньше 05-08 и 05-10); грep пуст | ✗ **FAIL** |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | Конвенциональных `scripts/*/tests/probe-*.sh` в проекте нет; ни один план фазы probe не объявляет | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| BILL-05 | 05-01, 05-02, 05-04, 05-05, 05-06, 05-07, 05-08, 05-10 | Пользователь может продлить текущую подписку | ✓ SATISFIED (тестовый стенд), **с оговоркой** | Формы → `POST /billing/subscribe` → вебхук → `_extend_subscription`; `REQUIREMENTS.md:115`, `:235` — Complete. Продление СВОЕГО тарифа корректно. ⚠️ Смежный путь (смена плана) несёт блокер `_apply_extension`; ⚠️ в проде не работает (D-26) |
| BILL-06 | 05-03, 05-04, 05-05, 05-06, 05-09 | Потребление и остаток по четырём осям | ✓ SATISFIED | `AXIS_ORDER` → четыре метра; 22 теста `test_plan_usage.py` зелёные. `REQUIREMENTS.md:116`, `:236` — Complete |
| BILL-07 | 05-02, 05-04, 05-05, 05-06, 05-08, 05-09, 05-10 | История платежей | ✓ SATISFIED (тестовый стенд) | `get_payment_history` → блок истории с датой/суммой/статусом; пустое состояние и потолок покрыты. `REQUIREMENTS.md:117`, `:237` — Complete. ⚠️ Статус «отклонён» в проде не появится (D-27) |
| BILL-02 | — (НЕ заявлен ни одним планом фазы) | Применение тарифных лимитов | ℹ️ ВНЕ ОБЪЁМА, не orphaned | `REQUIREMENTS.md:187` помечает `Partial` с явным указанием, что долг забирает будущая работа; примечание ROADMAP к фазе 5 прямо запрещает считать это гэпом (D-08). Проверено: сирот среди ID нет — все три заявленных ID (BILL-05/06/07) прослежены выше |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `app/services/payment_service.py` | 504-509 | Правило владельца применяется только на стадии намерения; на стадии денег — безусловная перезапись | 🛑 Blocker | Молчаливое понижение оплаченного тарифа; воспроизведено |
| `.planning/STATE.md` | 89-90 | Устаревшие 🔴 записи, описывающие УЖЕ ЗАКРЫТЫЕ дефекты как открытые, с ложными ссылками на строки кода | ⚠️ Warning | Единственный операционный документ вводит читателя в заблуждение на денежном пути |
| `app/services/payment_service.py` | 128-141 | Синхронный HTTP-вызов `YooPayment.create()` без таймаута внутри `async def` | ⚠️ Warning (CR-02, вне четырёх критериев) | `docker-compose.prod.yml:87` не задаёт `--workers`, то есть воркер один: зависшее соединение с ЮKassa вешает всё приложение, включая `/health`. Не отменяет ни один критерий, но лежит на пути кнопки оплаты |
| — | — | Долговые маркеры `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | ✓ Чисто | Скан по 15 файлам фазы — ноль совпадений |

### Human Verification Required

Семь пунктов — см. `human_verification` во frontmatter. Из них один особый:

**Прохибиция judgment-tier, помеченная планом `resolved`, НЕ ЗЕЛЁНАЯ.**
`MUST NOT превращать оплаченный остаток старшего тарифа в дни младшего без
объявленного правила и без слова пользователю до нажатия кнопки` (план 05-10,
BILL-05/fairness). Автономный вердикт LLM-судьи — **НЕ АВТОРИТЕТНЫЙ** —
«нарушена»: в воспроизведённом сценарии слова пользователю до нажатия нет вовсе,
потому что действующей подписки на момент нажатия не существует и гард формы не
срабатывает. Требуется решение владельца. Флаг:
`unverified-prohibition — human review recommended`.

### Gaps Summary

Оба гэпа прошлого раунда закрыты по-настоящему, и это проверено кодом и прогонами,
а не заявлениями SUMMARY. Гард источника вебхука перестал быть декоративным:
ветка адреса пира физически удалена, умолчание стало безопасным, деплойный
артефакт пинует значение, а регрессия поднимает приложение через настоящий
`ProxyHeadersMiddleware` и доказывает 403 на подделке. Защита от двойного
зачисления стала настоящим compare-and-swap с приращением на стороне СУБД и
уникальным индексом под второй строкой подписки.

Взамен раскрыт другой блокер, лежащий на том же денежном пути и находкой прошлого
раунда не бывший. Правило `upgrade-only` — решение владельца — существует ровно на
входе и не существует там, где приходят деньги: `_apply_extension` перезаписывает
тариф безусловно. Я не принял это на веру от ревьюера: сценарий воспроизведён
независимо на боевом пути кода, и итог — пользователь, оплативший Pro и Basic,
остаётся на Basic, причём срок сдвинут дважды, а следа в журнале нет. Заявленное
планом 05-10 покрытие «тестами на basic→pro и pro→basic» выполнено половиной:
pro→basic проверен только на гарде формы, стадия применения не покрыта ничем.

Второй гэп — организационный, но не безобидный. `.planning/STATE.md` объявлен
артефактом двух планов и не тронут ни одним; сегодня он сообщает читателю, что
дыра гарда вебхука и двойное зачисление ОТКРЫТЫ, ссылаясь на строки кода, которых
в этом виде больше нет, и не упоминает нового блокера вовсе.

Четыре критерия ROADMAP при этом выполнены (четвёртый — с обязательной ручной
проверкой в браузере, которой в проекте нечем заменить). Цель фазы как
пользовательский результат достигнута; фаза не проходит из-за дефекта
корректности на смежном денежном пути и незаписанной бухгалтерии.

---

_Verified: 2026-08-16T15:30:00Z_
_Verifier: Claude (gsd-verifier), раунд 2_

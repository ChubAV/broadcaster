---
phase: 05-tarify
plan: 05
subsystem: billing
tags: [billing, jinja2, templates, css, responsive, progressive-enhancement, dead-code-removal]

# Dependency graph
requires:
  - phase: 05-tarify
    plan: 03
    provides: "plan_axes / PlanAxis / AXIS_ORDER / AXIS_LABELS — четыре оси числами; limit is None означает безлимит"
  - phase: 05-tarify
    plan: 04
    provides: "Контекст GET /billing: subscription / usage / plans / payments / payments_truncated; POST /billing/purchase; PAYMENT_LIST_CAP"
  - phase: 05-tarify
    plan: 01
    provides: "Settings.plan_limits с машинными ценами формата ЮKassa; POST /billing/subscribe"
  - phase: 01-interfeysnyy-fundament
    provides: "components/card, badge, mono, progress, table, empty_state; примитивы data-row / data-rowhead / data-cell-label; виджет квоты в сайдбаре"
  - phase: 04-dashbord-i-istoriya
    provides: "[data-metrics] / [data-metric-line] / [data-metric-value] — образец формы правила сетки и раскладки по базовой линии"
provides:
  - "app/templates/billing/includes/plan_card.html — макрос карточки тарифного плана"
  - "app/templates/billing/includes/usage_meters.html — макрос метра одной оси"
  - "app/templates/billing/includes/payment_row.html — макрос строки журнала платежей"
  - "format_amount — Jinja-глобал денежной подписи (машинная строка → «1 490 ₽»)"
  - "plan_axis_order / plan_axis_labels — порядок и подписи осей в разметке из модуля 05-03"
  - "[data-plans] — сетка карточек планов, складывающаяся в одну колонку"
  - "Раздел /billing целиком без JavaScript: обе оплаты — формы POST"
affects: [05-06, 06-admin]

actuals:
  tokens: 22000
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - "Паршал раздела — МАКРОС с явными параметрами и комментарием-докстрингом, живущий в <раздел>/includes/, а не в общей библиотеке компонентов"
    - "Форматирование денег — глобал ПОКАЗА; машинная строка платёжного API из конфига не трогается"
    - "Названия осей приезжают в разметку глобалом из модуля-владельца, а не второй копией в шаблоне"
    - "Безлимит рисуется знаком бесконечности и не рисует шкалы вовсе — деление выполняется только под условием"
    - "Снос неподключённого шаблона ВМЕСТЕ с его проверкой исходника; отсутствие файла закрепляется новой регрессией"
    - "Подпись элемента интерфейса приводится к его источнику данных, а источник не трогается"

key-files:
  created:
    - app/templates/billing/includes/plan_card.html
    - app/templates/billing/includes/usage_meters.html
    - app/templates/billing/includes/payment_row.html
  modified:
    - app/templates/billing/balance.html
    - app/templates/base.html
    - app/static/css/app.css
    - app/pages/common.py
    - app/application/billing/plan_usage.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_billing_section.py
  deleted:
    - app/templates/billing/plans.html

key-decisions:
  - "Разделитель разрядов и отбивка перед знаком рубля — НЕРАЗРЫВНЫЕ пробелы; ожидания в тестах выписаны escape-последовательностью, а не невидимым символом"
  - "Порядок и подписи осей доезжают до макросов ГЛОБАЛАМИ окружения: импортированный макрос контекста вызывающего не получает, а вторая копия подписей разъехалась бы молча"
  - "Макрос строки платежа получил два параметра сверх сигнатуры плана: словарь подписей статуса (план требует держать его у вызывающего) и карту первых платежей по планам"
  - "«Первый платёж» отличается от «продления» по САМОЙ РАННЕЙ строке плана в уже загруженном журнале — второго запроса ради одной подписи не заведено"
  - "Форма продления у истёкшего срока рисуется только если текущий план ЕСТЬ в конфиге: кнопка на несуществующий план обещала бы оплату, а обработчик вернул бы в раздел"
  - "REQUIREMENTS.md не правится: отметку BILL-05/06/07 закрывает план 05-06, как и предписано волной"

patterns-established:
  - "Два слоя утверждений о разделе: контекст (контракт «обработчик → разметка») и HTML (что нарисовали). Ни один не заменяет другой"
  - "Названная граница проверки выписывается комментарием В ТЕСТОВОМ ФАЙЛЕ, чтобы зелёный прогон не приняли за доказательство отрисовки"

requirements-completed: []

coverage:
  - id: D1
    description: "Три карточки планов по макету: имя с моношрифтовым тегом, крупная цена с «/ мес», четыре строки лимитов, кнопка внизу; текущий выделен рамкой"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_plan_card_marks_the_current_plan_and_offers_renewal, #test_billing_plan_card_draws_infinity_for_an_unlimited_limit, #test_billing_free_plan_card_carries_no_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_screen_draws_three_plan_cards"
        status: pass
    human_judgment: false
  - id: D2
    description: "Четыре метра показывают потребление; безлимитная ось рисует знак бесконечности, не делит на ноль и шкалы не рисует (D-09, A2)"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_usage_meter_draws_no_denominator_for_an_unlimited_axis, #test_billing_usage_meter_over_the_limit_reports_the_real_numbers"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_screen_draws_all_four_axes"
        status: pass
    human_judgment: false
  - id: D3
    description: "История платежей: дата, сумма и статус; «отклонён» / «проведён» — те же слова, что в макете админки (D-14, D-16)"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_a_canceled_payment_is_named_rejected, #test_a_succeeded_payment_is_named_completed_with_a_human_amount, #test_the_screen_names_a_truncated_payment_list"
        status: pass
    human_judgment: false
  - id: D4
    description: "Сумма показана человеческим форматом, а машинная строка ЮKassa на экран не выходит и в конфиге не меняется (A3)"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_amount_format_is_a_display_concern_only"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_a_succeeded_payment_is_named_completed_with_a_human_amount (assert «1490.00» not in html)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Истёкшая подписка помечена явно и сопровождается предложением продлить; ничего не отключено (D-07)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_an_expired_subscription_is_marked_and_offered_a_renewal, #test_a_live_subscription_is_not_marked_expired"
        status: pass
    human_judgment: false
  - id: D6
    description: "При выключенных платежах карточки и метры видны, кнопки оплаты нет, на её месте подпись про администратора (D-21)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_screen_shows_the_showcase_but_no_payment_form_when_disabled"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_plan_card_without_payments_names_the_administrator"
        status: pass
    human_judgment: false
  - id: D7
    description: "Обе оплаты работают без JavaScript: ни браузерного диалога, ни асинхронного запроса из скрипта, только формы POST (D-20, T-05-31)"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_section_markup_carries_no_script_at_all, #test_both_payments_are_real_forms_and_degrade_without_alpine; tests/test_pages/test_responsive_markup.py#test_billing_has_no_event_handler_on_a_button"
        status: pass
    human_judgment: false
  - id: D8
    description: "Виджет сайдбара подписан балансом сообщений; источник данных не изменился, новых запросов на 26 рендеров не появилось (D-22, T-05-29)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_the_sidebar_widget_names_the_message_balance_not_the_plan, #test_the_shell_did_not_gain_a_query_for_the_widget"
        status: pass
    human_judgment: false
  - id: D9
    description: "Неподключённый шаблон удалён вместе со своей проверкой исходника; ссылок на него в app/ не осталось (D-19)"
    requirement: BILL-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_the_unwired_plans_template_is_gone"
        status: pass
    human_judgment: false
  - id: D10
    description: "Табличные данные раздела построены на примитивах строки; библиотека общих компонентов не выросла"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_no_table_markup, #test_billing_component_library_did_not_grow, #test_template_inventory, #test_billing_payment_labels_ride_with_the_values"
        status: pass
    human_judgment: false
  - id: D11
    description: "Раздел пригоден к использованию на мобильных ширинах: карточки складываются в одну колонку, подписи колонок едут со значениями, горизонтальной прокрутки нет"
    requirement: BILL-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_plans_grid_is_declared_folding, #test_list_page_no_utility_classes[billing]"
        status: partial
    human_judgment: true
    rationale: "Backstop-истина плана. Браузерных и e2e-тестов в проекте нет (блокер STATE.md), поэтому проверки закрепляют ОБЪЯВЛЕНИЕ сетки (repeat(auto-fit, minmax(260px, 1fr))) и наличие подписей колонок, но НЕ отрисовку на настоящей мобильной ширине. Граница выписана комментарием в самом тестовом файле, чтобы зелёный прогон не приняли за доказательство. Требуется человеческий осмотр в UAT."

duration: 70min
completed: 2026-08-15
status: complete
---

# Phase 05 Plan 05: Раздел «Тарифы» по макету Summary

**Данные, посчитанные планами 05-01…05-04, впервые стали экраном: три карточки планов, четыре метра, денежный журнал — и раздел перестал быть последним местом проекта, где оплата зависит от одного тега скрипта.**

## Performance

- **Duration:** ~70 мин (из них ~31 мин — два прогона полной суиты)
- **Tasks:** 3
- **Files modified:** 11 (3 создано, 7 изменено, 1 удалён)
- **Tests added:** +30 (суита выросла с 1526 до 1556)

## Accomplishments

- **Покупка пакета снова работает.** План `05-04` снёс JSON-маршрут, а кнопка «Купить» продолжала звать его скриптом — раздел был оставлен в заведомо сломанном состоянии, предписанном последовательностью планов. Кнопка переведена на форму `POST /billing/purchase`; блок скрипта с `fetch` и `alert` удалён целиком. **В разделе не осталось ни одного тега скрипта, ни одного обработчика события на кнопке, ни одного браузерного диалога.**
- **Четыре оси и три плана впервые видны пользователю.** До этого плана `plan_axes` считала числа, которые никто не показывал, а карточки планов существовали только в неподключённом шаблоне. Безлимитная ось рисует знак бесконечности и **не рисует шкалы вовсе**: залитая до конца шкала сообщила бы «израсходовано всё» там, где израсходовать нельзя.
- **Денежный журнал получил разметку.** Дата в зоне пользователя, назначение, сумма подписью, статус бейджем теми же словами, что увидит администратор в Фазе 6 (`проведён` / `отклонён` / `в обработке`). Сработавший потолок называет себя текстом, а не выражается тихой обрезкой.
- **Сумма перестала быть машинной строкой на экране — и осталась ею в платеже.** `format_amount` живёт на стороне показа; в конфиге и в `amount.value` ЮKassa остаётся `"1490.00"`. Регрессия проверяет ОБА направления: `«1 490 ₽» in html` и `"1490.00" not in html`.
- **Виджет сайдбара перестал врать.** Он был подписан тарифом, а рисовал `used / limit` **баланса сообщений**. Правится только подпись: перенаправление на тарифную ось добавило бы запрос по журналу отправок во все 26 рендеров страниц ради метрики, у которой теперь есть свой полноценный экран.
- **Отложенное решение проекта закрыто.** `billing/plans.html` — файл без маршрута, ссылавшийся на переменные, которых нет ни в одном контексте, — удалён вместе со своей проверкой исходника. Его содержимое (три оси и защита от деления на ноль) переехало в живые паршалы, у которых есть поведенческие проверки.

## Task Commits

1. **Task 1: Три паршала раздела и сетка карточек** — `0a8f7ca` (test, RED: 12 failed) → `a6565b6` (feat, GREEN)
2. **Task 2: Переверстать balance.html и убрать скрипт покупки** — `ae7fb92` (test, RED: 10 failed) → `01a0c3c` (feat, GREEN)
3. **Task 3: Снос шаблона, честная подпись, адаптивные регрессии** — `7232b56` (test, RED: 2 failed) → `752db3a` (feat, GREEN)
4. **Сверх задач:** `28b9c7b` (style) — имя плана перестало рисоваться тем же крупным кеглем, что и цена

_TDD-гейты соблюдены всеми тремя задачами: каждый `feat` предваряется `test`-коммитом, красным на своём дереве (задача 1 — `TemplateNotFound` и отсутствие глобала, задача 2 — 10 падений на разметке, которой ещё нет, задача 3 — виджет по-прежнему подписан тарифом и снесённый шаблон на месте). Коммит `28b9c7b` помечен `style`, а не `feat`, намеренно: он меняет кегль, а не поведение._

## Files Created/Modified

**Создано:**
- `app/templates/billing/includes/plan_card.html` — макрос `plan_card(plan, current_plan, payments_enabled)`
- `app/templates/billing/includes/usage_meters.html` — макрос `usage_meter(axis)`
- `app/templates/billing/includes/payment_row.html` — макрос `payment_row(payment, user, cols, labels, first_payment_at)`

**Изменено:**
- `app/templates/billing/balance.html` — переверстан под пять блоков; скрипт покупки удалён; кнопка «Купить» стала формой
- `app/templates/base.html` — виджет сайдбара подписан балансом сообщений; контракт переменных `quota` не тронут
- `app/static/css/app.css` — `[data-plans]`, `[data-plans] .card--current`, `[data-plan-limits]`, `[data-plan-name]`
- `app/pages/common.py` — глобалы `format_amount`, `plan_axis_order`, `plan_axis_labels`
- `app/application/billing/plan_usage.py` — докстринг перестал указывать на снесённый файл
- `tests/test_pages/test_responsive_markup.py` — +18 тестов, −1 (снятый вместе с файлом)
- `tests/test_pages/test_billing_section.py` — +13 тестов разметки, обновлён докстринг файла

**Удалено:**
- `app/templates/billing/plans.html` — неподключённый шаблон (D-19)

## Decisions Made

### Подписи осей доезжают до макросов глобалами окружения

Модуль `plan_usage.py` (план `05-03`) объявляет `AXIS_ORDER` и `AXIS_LABELS` и прямо запрещает вторую копию подписей в разметке. Но карточка плана — **макрос**, а импортированным макросам Jinja контекст вызывающего не передаёт: протащить список параметром значило бы менять сигнатуру макроса и все его вызовы. Приём уже установлен в проекте — так в разметку приезжают `messenger_labels` и `AD_STATUS_*` (`app/pages/common.py`). Заведены `plan_axis_order` / `plan_axis_labels`.

Цикла импорта не возникает: `plan_usage` не импортирует `app.pages` на верхнем уровне, а `send_analytics` рвёт свою половину отложенным импортом внутри функции.

### Разделитель разрядов — неразрывный пробел, а ожидание — escape-последовательность

Обычный пробел перенёс бы «1» и «490» на разные строки узкой карточки. Неразрывный пробел в **литерале теста** невидим: следующий читатель принял бы его за обычный и «починил» первым же редактором, а тест покраснел бы без объяснимой причины. Поэтому в обоих тестовых файлах заведены именованные константы, выписанные `" "`, и рядом — причина.

### Макрос строки платежа получил два параметра сверх сигнатуры плана

План называет сигнатуру `payment_row(payment, user, cols)` и **одновременно** требует, чтобы словарь подписей статуса жил у вызывающего (контракт `components/badge.html`: единого enum статусов в проекте нет). Два требования исполнимы только вместе с четвёртым параметром — `labels`.

Пятый (`first_payment_at`) появился из требования различать «<План> · продление» и «<План> · первый платёж». Из одной строки журнала это неразличимо, а второй запрос ради подписи — цена, которой раздел не стоит. Развязка: журнал отсортирован по дате убыванием, поэтому **самая ранняя строка плана в уже загруженном списке и есть его первый платёж**; карта «план → эта дата» строится в вызывающем шаблоне одним проходом по тому же списку. Идентификаторы платежей при этом не используются вовсе — ни ключом, ни значением.

### Форма продления у истёкшего срока — только для плана, который есть в конфиге

Подписка может нести план, которого в `Settings.plan_limits` нет (в тестах это `business`). Кнопка «Продлить» на такой план обещала бы оплату, а обработчик `POST /billing/subscribe` вернул бы в раздел без платежа — то есть кнопка молча не работала бы. Проверка `plans|selectattr('id','equalto', subscription.plan)` стоит в разметке, а название тарифа бейджем показывается в любом случае.

### Ссылка виджета переименована вместе с подписью

План предписывает править «только подпись» и сохранить ссылку. Ссылка (`href="/billing"`) сохранена дословно, а её **текст** — «ПОВЫСИТЬ ЛИМИТЫ →» — изменён на «ТАРИФЫ И ПОПОЛНЕНИЕ →»: под подписью «Баланс сообщений» призыв повысить лимиты называл бы виджет тем же, чем он назывался до правки. Прохибиция плана запрещает подписывать элемент величиной, которой он не показывает; текст призыва — часть подписи. Ни один тест на прежний текст не опирался.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Докстринг модуля осей указывал на снесённый файл**

- **Found during:** Task 3
- **Issue:** `app/application/billing/plan_usage.py:6` ссылался на `billing/plans.html` прозой. После сноса файла ссылка стала указывать в пустоту, а приёмочный критерий задачи 3 требует, чтобы ссылок на удалённый шаблон не осталось.
- **Fix:** абзац переписан по факту: «неподключённый шаблон тарифов (снесённый планом 05-05 …) знал три оси». История сохранена, путь к несуществующему файлу убран.
- **Files modified:** `app/application/billing/plan_usage.py` (вне `<files>` задачи 3)
- **Commit:** `752db3a`

**2. [Rule 1 - Bug] Имя плана рисовалось тем же крупным кеглем, что и цена**

- **Found during:** проверка соответствия макету после задачи 2
- **Issue:** первая редакция карточки использовала `data-metric-value` и для имени плана, и для цены. Макет (962-992) даёт имени размер заголовка, а цене — крупное число; два элемента одного кегля отнимают у цены её роль, а истина плана прямо называет цену «крупной».
- **Fix:** заведён `[data-plan-name]` с размером заголовка карточки; `data-metric-value` остался у цены.
- **Files modified:** `app/templates/billing/includes/plan_card.html`, `app/static/css/app.css`
- **Commit:** `28b9c7b`

### Отступления от буквы плана

**3. Правил CSS добавлено четыре, а не одно**

План называет `[data-plans]` «единственным новым правилом CSS, обязательным фазе». Обязательным оно и осталось, но три истины плана требуют оформления, которого в проекте не было: «текущий план выделен рамкой акцентного цвета» (`[data-plans] .card--current`), «четыре строки «подпись → значение»» (`[data-plan-limits]` и вложенное правило), «крупная цена» в паре с именем меньшего кегля (`[data-plan-name]`, отступление №2). Все четыре — **скоупленные**, ни одно не переопределяет существующего; `[data-metrics]` остался единственным объявлением с прежним минимумом 210px, что закреплено тестом.

**4. Тесты задачи 1 живут в `tests/test_pages/test_responsive_markup.py`, которого нет в её `<files>`**

`<files>` задачи 1 перечисляет только исходники, а `<acceptance_criteria>` требует поведенческих проверок форматирования суммы и обеих веток метра. Файл выбран тот, который сама задача запускает в `<verify>` (`-k "billing or template_inventory"`), — и он же входит в `files_modified` плана.

**5. Перечень «строк без шапки» вырос с пяти до шести**

`payment_row.html` вызывает `row_open` и шапку не рисует (её рисует вызывающий), поэтому попадает в инвентаризацию `test_row_templates_without_header_are_accounted_for`. Файл внесён в `ROW_TEMPLATES_WITHOUT_HEADER` первым классом («макрос строки внутри объединения `billing/balance.html`»), объявленное число поднято до шести с выписанной причиной — по той же схеме, по какой прошлые планы это число **уменьшали**.

**6. Докстринг `tests/test_pages/test_billing_section.py` переписан**

Он утверждал: «Разметки: её заводит план 05-05. Поэтому утверждения идут по КОНТЕКСТУ шаблона, а не по HTML». После этого плана в файле два слоя утверждений, и оставить прежнюю формулировку значило бы солгать следующему читателю о содержимом файла.

**7. Блок «Баланс сообщений» переехал из плитки в карточку**

Прежняя разметка показывала «Текущий тариф» и «Баланс сообщений» двумя плитками в общей сетке наверху экрана. По макету раздела сверху стоит блок тарифа со сроком, а баланс — четвёртым блоком; плитка баланса стала карточкой с тем же числом и той же шкалой. Данные и их источник не изменились.

---

**Total deviations:** 2 auto-fixed (Rule 2 и Rule 1) + 5 задокументированных отступлений от буквы плана
**Impact on plan:** Все `must_haves.truths` выполнены, кроме `verification: backstop` (мобильные ширины — требует человеческого осмотра, см. `coverage` D11). За пределы `files_modified` плана вышел один файл — `app/application/billing/plan_usage.py`, и только докстрингом. Файлы соседних планов не открывались; `app/pages/billing.py` не тронут ни строкой — контракт контекста плана `05-04` принят как есть.

## Issues Encountered

- **Полная суита идёт ~15,5 минут** (1556 тестов). Промежуточные прогоны резались по файлам, финальные вынесены в фоновый процесс. Та же проблема окружения, что отмечена в `05-01`…`05-04`.
- **Комментарий в шаблоне уронил тест на отсутствие скрипта.** Первая редакция `balance.html` объясняла снос словами «терял приём денег вместе с одним тегом `<script>`» — и приёмочный греп `grep -c '<script'` честно нашёл его в комментарии. Формулировка переписана без имени тега. Это не дефект проверки: она обязана читать сырой текст, иначе запрет обходится переносом разметки в комментарий (тот же случай, что у сторожа границ модуля в `05-03`).
- **Единственная оставшаяся в проекте строка `plans.html`** — константа `REMOVED_PLANS_TEMPLATE` в тесте, который проверяет ОТСУТСТВИЕ файла. Приёмочный греп задачи 3 по `app/` и `tests/` из-за неё не пуст; сканирование в самом тесте намеренно ограничено `app/`, потому что упоминание пути в страже его отсутствия — не остаточная ссылка.
- **`graphify update .` не выполнялся:** каталога `graphify-out/` в worktree нет (он не отслеживается git). Обновление графа принадлежит основному дереву.

## Known Stubs

Заглушек нет: каждый блок экрана подключён к настоящему источнику — оси к `plan_axes`, планы к `Settings.plan_limits`, деньги к журналу платежей, сообщения к балансу и журналу операций, срок к контексту шелла. Ни одного жёстко зашитого пустого значения, ни одной подписи «скоро появится».

Границы, ЯВНО отданные соседям (не заглушки):

| Что | Кем закрывается |
|---|---|
| Отметка `BILL-05` / `BILL-06` / `BILL-07` в `REQUIREMENTS.md` | `05-06` (документационный долг фазы) |
| Выкат ревизии `0017` на боевую базу и настройка вебхука в кабинете | `05-06` |
| Осмотр раздела на настоящей мобильной ширине (backstop-истина D11) | UAT фазы |
| Применение лимитов — гейты на создание (долг `BILL-02`, D-08/D-13) | отдельная работа, фазой не закрывается |

## Ответ волне: BILL-05, BILL-06 и BILL-07 стали истинными со стороны пользователя

Все три требования сформулированы от лица пользователя, и планы `05-02` и `05-04` сознательно не отмечали их, пока не было разметки. Разметка есть:

- **BILL-05** («может продлить текущую подписку») — карточка текущего платного плана несёт форму «Продлить», а истёкший срок помечен и сопровождается тем же предложением. Кнопка ведёт в `POST /billing/subscribe`, покрытый планом `05-01`.
- **BILL-06** («видит потребление и остаток по четырём осям») — четыре метра на экране, подписи из модуля осей, безлимит показан бесконечностью, а не нулём.
- **BILL-07** («видит историю своих платежей») — журнал денег с датой, назначением, суммой и статусом; чужие платежи не видны (предикат запроса, план `05-04`), потолок называет себя.

**`REQUIREMENTS.md` этим планом НЕ правится** — ни чекбоксы, ни таблица прослеживаемости: задачи плана этого не предписывают, а документационный долг фазы закрывает `05-06`. Эта секция существует ровно для того, чтобы `05-06` не пришлось выводить истинность заново.

## Threat Flags

Новой поверхности сверх `<threat_model>` плана не появилось. Все шесть `mitigate`-диспозиций реализованы:

- **T-05-27** (XSS через данные платежа) — автоэкранирование Jinja2 не отключается нигде: фильтра `safe` и `Markup` в трёх новых паршалах нет ни одного, клиентская разметка узлами DOM в разделе не строится — новый JS фаза не добавляет вовсе, а существующий убран.
- **T-05-28** (цена или лимит скрытым полем формы) — в форме карточки плана ровно одно скрытое поле, `plan`; в форме пакета ровно одно, `package_index`. Закреплено `test_both_payments_are_real_forms_and_degrade_without_alpine`.
- **T-05-29** (виджет, подписанный не тем, что показывает) — подпись приведена к источнику, источник не тронут, новых запросов на 26 рендеров нет.
- **T-05-30** (тихая обрезка журнала) — потолок выводится текстом с двумя числами.
- **T-05-31** (оплата недоступна без JavaScript) — обе оплаты формы POST, именованная регрессия деградации заведена.
- **T-05-SC** (installs) — зависимости не тронуты: `pyproject.toml` и `uv.lock` в диффе отсутствуют.

Отдельно исполнено предупреждение плана `05-04` (`threat_flag: note`): макрос строки платежа **не печатает** `yookassa_payment_id` ни значением, ни атрибутом, ни комментарием; регрессия `test_the_screen_never_prints_the_yookassa_payment_id` зелёная.

Новых флагов нет.

## Self-Check: PASSED

Файлы на месте:
- `app/templates/billing/includes/plan_card.html` — FOUND
- `app/templates/billing/includes/usage_meters.html` — FOUND
- `app/templates/billing/includes/payment_row.html` — FOUND
- `app/templates/billing/balance.html` — FOUND
- `app/templates/billing/plans.html` — **ОТСУТСТВУЕТ (снесён намеренно)**

Коммиты в истории ветки: `0a8f7ca`, `a6565b6`, `ae7fb92`, `01a0c3c`, `7232b56`, `752db3a`, `28b9c7b` — все FOUND.

Проверки приёмки:
- `uv run pytest tests/ -q` → **1556 passed, exit code 0** (928 с)
- `uv run pytest tests/test_pages/test_responsive_markup.py tests/test_pages/test_shell.py -q` → 233 passed
- `uv run pytest tests/test_pages/test_billing_section.py tests/test_pages/test_responsive_markup.py -q` → 157 passed
- `uv run pytest tests/test_templates tests/test_pages/test_dashboard.py tests/test_pages/test_https_asset_scheme.py tests/test_pages/test_billing_section.py -q` → 129 passed
- `grep -c '<script' app/templates/billing/balance.html` → **0**; `alert(` → **0**; `fetch(` → **0**; `onclick` → **0**
- `grep -Ec '<table|<td|<th |<thead|<tbody' app/templates/billing/balance.html` → **0**; в `payment_row.html` → **0**
- `grep -Ec 'action="/billing/(subscribe|purchase)"' app/templates/billing/balance.html` → **2**
- `grep -c 'parsed_plan_limits' app/templates/billing/balance.html` → **0**
- `grep -c 'data-cell-label' app/templates/billing/includes/payment_row.html` → **3**
- `grep -c 'progress(' app/templates/billing/includes/usage_meters.html` → **1**
- `ls app/templates/components/*.html | wc -l` → **13**
- `grep -c 'Тариф {{' app/templates/base.html` → **0**; `quota.get(` на месте, `href="/billing"` на месте
- `grep -c 'data-plans' app/static/css/app.css` → 2; `[data-metrics] {` → **1** (не переопределено), `minmax(210px, 1fr)` на месте
- `grep -rn 'plans.html' app/ tests/` → одна строка: константа стража отсутствия файла в тесте
- `git diff --stat` не содержит `pyproject.toml` / `uv.lock` — зависимости не тронуты

---
*Phase: 05-tarify*
*Completed: 2026-08-15*

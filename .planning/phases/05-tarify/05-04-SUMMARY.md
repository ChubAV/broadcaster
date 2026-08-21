---
phase: 05-tarify
plan: 04
subsystem: billing
tags: [billing, payments, yookassa, csrf, fastapi, jinja2, dead-code-removal]

# Dependency graph
requires:
  - phase: 05-tarify
    plan: 01
    provides: "is_same_origin в app/pages/common.py, Settings.parsed_plan_limits, Payment.kind / Payment.plan, create_payment(kind=...)"
  - phase: 05-tarify
    plan: 02
    provides: "Терминальный статус canceled — третье значение Payment.status, которое обязан покрыть экран"
  - phase: 05-tarify
    plan: 03
    provides: "plan_axes(db, user=, limits=, nav_counts=) — четыре оси тарифа числами"
  - phase: 01-interfeysnyy-fundament
    provides: "get_shell_context — quota.plan / quota.expires_at и nav_counts, читаемые обработчиком из request.state.shell"
  - phase: 04-dashbord-i-istoriya
    provides: "normalize_utc; приём «потолок проверяется до конструирования и называет себя» (выгрузка истории)"
provides:
  - "GET /billing — все пять блоков раздела одним маршрутом (D-18): тариф и срок, четыре оси, планы, баланс и пакеты, история платежей"
  - "POST /billing/purchase — покупка пакета сообщений настоящей формой, без JS"
  - "get_payment_history / count_payments в app/services/billing_service.py — журнал ДЕНЕГ владельца с потолком"
  - "PAYMENT_LIST_CAP в app/constants.py — потолок списка платежей (200)"
  - "Контракт контекста раздела для разметки плана 05-05: subscription / usage / plans / payments / payments_truncated"
  - "Гард источника объявлен ОДИН раз на проект: приватная копия в app/pages/history.py снята"
  - "JSON-маршрут покупки пакета удалён вместе с моделью тела запроса (D-24)"
affects: [05-05, 05-06, 06-admin]

actuals:
  tokens: 17000
  tasks: 3
  commits: 8

tech-stack:
  added: []
  patterns:
    - "Потолок списка сверяется ОТДЕЛЬНЫМ счётом ДО выборки: из длины обрезанного списка срабатывание не выводится"
    - "Журнал денег и журнал сообщений — два разных блока экрана, а не один склеенный"
    - "Страничная форма никогда не отвечает 422: поле принимается строкой с пустым умолчанием и разбирается в обработчике"
    - "Снос мёртвой JSON-поверхности вместе с её моделью тела запроса; читающие входы сохраняются отдельным решением"

key-files:
  created:
    - tests/test_pages/test_billing_section.py
  modified:
    - app/pages/billing.py
    - app/pages/history.py
    - app/pages/common.py
    - app/routes/billing.py
    - app/services/billing_service.py
    - app/constants.py
    - tests/test_services/test_billing_service.py
    - tests/test_routes/test_billing.py
    - tests/test_pages/test_history_retry.py

key-decisions:
  - "get_payment_history возвращает СТРОКИ МОДЕЛИ, а не словари с isoformat: разметке нужен настоящий datetime для глобала форматирования в зоне пользователя"
  - "Признак срабатывания потолка считается отдельным count_payments, а не сравнением len(payments) с потолком"
  - "Индекс пакета принимается строкой с пустым умолчанием: обязательное поле формы, пришедшее пустым, FastAPI считает отсутствующим и отвечает 422"
  - "Идентификатор плана в форме подписки получил то же пустое умолчание — обе формы раздела делят один порядок проверок целиком"
  - "BILL-05 / BILL-06 / BILL-07 в REQUIREMENTS.md НЕ отмечаются: до разметки плана 05-05 пользователь ничего из этого не видит"

patterns-established:
  - "Контракт «обработчик → разметка» проверяется по КОНТЕКСТУ шаблона подменой метода отрисовки, когда разметки ещё нет"
  - "Запрет на показ секрета, живущего в контексте, держится регрессией по телу ответа, а не аккуратностью автора будущего шаблона"

requirements-completed: []

coverage:
  - id: D1
    description: "Журнал платежей: владение предикатом запроса, порядок по дате убыванием, все три статуса, потолок"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_billing_service.py — 7 тестов get_payment_history / count_payments"
        status: pass
    human_judgment: false
  - id: D2
    description: "Сортировка идёт по дате и НИКОГДА по сумме: amount_value — строка, и «999.00» встало бы выше «1490.00»"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_billing_service.py#test_get_payment_history_never_sorts_by_the_amount"
        status: pass
    human_judgment: false
  - id: D3
    description: "Один экран отдаёт все пять блоков раздела и четыре оси в порядке макета (D-18, D-09)"
    requirement: BILL-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_section_carries_every_block_of_the_screen, #test_the_section_carries_the_four_axes_in_the_layout_order, #test_the_section_carries_the_plans_from_the_config"
        status: pass
    human_judgment: false
  - id: D4
    description: "Чужие платежи на /billing не видны (T-05-20)"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_section_shows_only_the_owners_payments"
        status: pass
    human_judgment: false
  - id: D5
    description: "Потолок списка называет себя и не выражается тихой обрезкой; ровно на потолке список не помечается неполным (D-17)"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_payment_list_cap_names_itself, #test_a_full_list_at_the_cap_is_not_reported_truncated, #test_the_handler_names_the_project_cap_and_checks_it_before_building"
        status: pass
    human_judgment: false
  - id: D6
    description: "Истёкшая подписка помечается и НИЧЕГО не отключает: 200, оси и планы на месте (D-07)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_an_expired_subscription_is_reported_not_enforced, #test_a_live_subscription_is_not_reported_expired, #test_a_user_without_a_subscription_is_not_reported_expired"
        status: pass
    human_judgment: false
  - id: D7
    description: "GET /billing не пишет в БД ни при каких условиях, включая возврат с ЮKassa (D-05, T-05-24)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_screen_creates_neither_a_subscription_nor_a_payment, #test_the_get_handler_contains_no_write_path"
        status: pass
    human_judgment: false
  - id: D8
    description: "Покупка пакета формой POST: 302 на confirmation_url, цена и число сообщений из конфига, чужой Origin → 403 без платежа, непригодный индекс → 302 без платежа, выключенные платежи → 302 без платежа (T-05-22, T-05-23)"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py — 8 тестов POST /billing/purchase, включая параметризацию непригодных индексов и структурную проверку порядка проверок"
        status: pass
    human_judgment: false
  - id: D9
    description: "JSON-маршрут покупки не отвечает; три читающих входа и вебхук с IP-гардом сохранены (D-24, T-05-21)"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_routes/test_billing.py#test_the_json_purchase_route_no_longer_answers + три существующих теста чтений; tests/test_routes/test_billing_webhook_source.py (8 тестов) зелёные"
        status: pass
    human_judgment: false
  - id: D10
    description: "Идентификатор платежа не выходит в тело ответа раздела"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_the_screen_never_prints_the_yookassa_payment_id"
        status: pass
    human_judgment: false
  - id: D11
    description: "Гард источника объявлен один раз на проект; поведение повтора отправки не изменилось"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py (61 тест, включая две структурные проверки на новом месте объявления); grep -c 'def _is_same_origin' app/pages/history.py → 0"
        status: pass
    human_judgment: false
  - id: D12
    description: "Пользователь, вернувшийся с ЮKassa до прихода вебхука, понимает, что платёж в обработке"
    requirement: BILL-07
    verification: []
    human_judgment: true
    rationale: "Backstop-истина плана: понятность формулировки автотестом не доказывается. Механическая половина закреплена — строка pending создаётся при инициации оплаты и попадает в контекст раздела (D1, D8). Словесная половина принадлежит разметке плана 05-05 и UAT фазы."

duration: 55min
completed: 2026-08-15
status: complete
---

# Phase 05 Plan 04: Раздел «Тарифы» одним экраном Summary

**`/billing` перестал быть страницей баланса: один маршрут отдаёт тариф со сроком, четыре оси, планы, пакеты и денежный журнал владельца, обе оплаты идут настоящими формами POST, а единственный маршрут проекта, отдававший идентификатор платежа в браузер, удалён вместе со своей моделью тела запроса.**

## Performance

- **Duration:** ~55 мин (из них 16 мин — финальный прогон полной суиты)
- **Tasks:** 3
- **Files modified:** 10 (1 создан, 9 изменено)
- **Tests added:** +35 (суита выросла до 1526)

## Accomplishments

- **Раздел стал разделом.** До плана `app/pages/billing.py` — 38 строк из 114, отдававших баланс сообщений и историю операций в штуках; ни подписки, ни осей, ни планов, ни денежного журнала на экране не было вовсе. Теперь один маршрут собирает все пять блоков макета — без табов и без второго пути.
- **Журнал ДЕНЕГ появился и принадлежит владельцу.** `BalanceTransaction` рублёвой суммы не знает — колонки под неё в таблице нет, — поэтому история платежей строится по `Payment` (D-14). Владение закреплено предикатом запроса, а не фильтром у вызывающего: забытое условие в шаблоне не может показать чужие деньги.
- **Потолок списка называет себя.** Общее число считается отдельным запросом ДО выборки. Вывести срабатывание из длины уже обрезанного списка нельзя по построению: ровно на потолке список полон, и «показано не всё» стало бы неотличимо от «столько и есть».
- **Покупка пакета работает без JavaScript.** Была единственным действием проекта, доступным только из скрипта и сообщавшим об ошибке браузерным диалогом. Стала формой с тем же порядком проверок, что у покупки тарифа и у повтора отправки.
- **Утечка, которой держался вебхук, закрыта.** `POST /api/billing/purchase` возвращал `yookassa_payment_id` прямо покупателю — тот самый «секрет», которым до плана `05-01` был защищён неаутентифицированный приём уведомлений об оплате. Маршрута больше нет.
- **Гард источника перестал существовать в двух экземплярах.** План `05-01` завёл публичное имя и честно записал дубль в свои границы; здесь приватная копия снята, и правка правила больше не требует помнить о второй половине.

## Task Commits

1. **Task 1: Гард источника и журнал платежей** — `ec4b78a` (test, RED) → `06893a6` (feat, GREEN) → `0ad4272` (refactor, снятие дубля гарда)
2. **Task 2: Страничный роутер раздела** — `e6882bd` (test, RED: 20 failed) → `53d33b4` (feat, GREEN)
3. **Task 3: Снос JSON-поверхности покупки** — `1ebaa78` (test, RED) → `0f6b040` (feat, GREEN)
4. **Сверх задач:** `7d1f55a` (test) — регрессия на непопадание идентификатора платежа в тело ответа

_TDD-гейты соблюдены всеми тремя задачами: каждый `feat` предваряется `test`-коммитом, красным на своём дереве (задача 1 — `ImportError` на `PAYMENT_LIST_CAP`, задача 2 — 20 падений на отсутствующих ключах контекста и маршруте покупки, задача 3 — маршрут отвечал отказом доступа вместо 404). Коммит `0ad4272` помечен `refactor`, а не `feat`, намеренно: он меняет место объявления правила, а не поведение._

## Files Created/Modified

**Создано:**
- `tests/test_pages/test_billing_section.py` — 25 тестов: пять блоков контекста, четыре оси, изоляция платежей по владельцу, потолок и его граница, истёкший/живой/отсутствующий срок, отсутствие записи в БД, восемь тестов формы покупки, две структурные проверки порядка

**Изменено:**
- `app/pages/billing.py` — GET переписан под пять блоков; новый `POST /billing/purchase`; `TRANSACTION_LIST_LIMIT` вынесен из литерала
- `app/services/billing_service.py` — `get_payment_history`, `count_payments`
- `app/constants.py` — `PAYMENT_LIST_CAP = 200` с выписанным обоснованием
- `app/pages/history.py` — приватный `_is_same_origin` снят, вызов переведён на общий; `urlsplit` из импортов ушёл вместе с ним
- `app/pages/common.py` — докстринг `is_same_origin` перестал обещать несуществующий дубль
- `app/routes/billing.py` — `POST /purchase` и `PurchaseRequest` удалены, на их месте — выписанная причина; `BaseModel` и `create_payment` ушли из импортов
- `tests/test_services/test_billing_service.py` — +9 тестов журнала платежей
- `tests/test_routes/test_billing.py` — +1 тест отсутствия маршрута, докстринг файла
- `tests/test_pages/test_history_retry.py` — две структурные регрессии переведены на новое место объявления гарда

## Decisions Made

### `get_payment_history` возвращает строки модели, а не словари

Соседний `get_transaction_history` отдаёт словари с `created_at` в `isoformat()` — и это правильно для него: его читает JSON-маршрут. Журнал платежей читает ТОЛЬКО разметка, а разметка (план `05-05`) форматирует дату существующим глобалом в зоне пользователя, которому нужен настоящий `datetime`. Строку ISO пришлось бы разбирать обратно — то есть завести второй формат даты в проекте ради одного шаблона.

**Следствие, за которым нужно следить:** объект `Payment` несёт в контекст ВСЕ колонки, включая `yookassa_payment_id`. Разметка его не печатает, но полагаться на это нельзя — поэтому заведена регрессия `test_the_screen_never_prints_the_yookassa_payment_id`, которая старше самой разметки и переживёт её написание.

### Срабатывание потолка считается отдельным запросом

`len(payments) == PAYMENT_LIST_CAP` — не признак обрезки: ровно на потолке список полон. Поэтому `count_payments` считает общее число ДО выборки, и структурный тест сторожит этот порядок в исходнике: поведенчески «посчитали до» и «посчитали после» на клиенте неразличимы, а разница определяет, соврёт экран или нет.

### Поля обеих форм раздела принимают пустое умолчание

`Form(...)` объявляет поле обязательным, и FastAPI считает ПУСТУЮ строку отсутствующим значением — отвечает 422 ещё до входа в обработчик. Для JSON-клиента это верно, для человека, нажавшего кнопку, — страница разбора запроса вместо возврата в раздел. Индекс пакета вдобавок принимается строкой и разбирается в обработчике: объявление его целым дало бы тот же 422 на нечисловом значении. Любое непригодное значение — пустое, нечисловое, отрицательное, вне диапазона — возвращает в раздел и НИКОГДА не выбирает умолчание по смыслу: умолчание продало бы не то, что нажали.

Правка распространена и на `POST /billing/subscribe` плана `05-01`: два соседних входа одного раздела обязаны отвечать на непригодный ввод одинаково.

### Требования не отмечаются выполненными

`BILL-05`, `BILL-06` и `BILL-07` остаются `Pending` в `REQUIREMENTS.md`. Все три формулируются от лица пользователя («видит», «может продлить»), а до разметки плана `05-05` пользователь не видит ни осей, ни карточек планов, ни истории платежей: контекст к ним готов, шаблон — нет. Отметка сейчас была бы ровно тем видом неправды, против которого написано само `BILL-07`. Прецедент — решение плана `05-02` по тому же требованию.

**Прямой ответ на вопрос волны:** этот план закрывает ОБРАБОТЧИКОВУЮ половину истории платежей (запрос, владение, потолок, контекст), но не экранную. `BILL-07` остаётся полуоткрытым; закрывает его `05-05`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Предсказание плана «существующие тесты повтора проходят без правок» не сбылось**

- **Found during:** Task 1
- **Issue:** План (`<behavior>` задачи 1) утверждает: «Существующие тесты повтора отправки продолжают проходить без правок». Фактически два теста в `tests/test_pages/test_history_retry.py` — структурные, читают ИСХОДНИК и ищут в нём `_is_same_origin`: `test_retry_origin_check_runs_before_the_record_is_read` (греп по телу обработчика) и `test_retry_origin_check_documents_its_boundary` (греп по докстрингу в `HISTORY_PY`). Снятие приватной копии ломает оба по построению.
- **Fix:** первый переведён на `is_same_origin(` — подстроку, верную и до, и после переезда; второй читает `COMMON_PY`, потому что докстринг обязан проверяться там, где живёт код. Утверждения тестов не ослаблены: оба по-прежнему падают, если сверка источника исчезнет или перестанет стоять до побочного эффекта.
- **Files modified:** `tests/test_pages/test_history_retry.py` (вне `<files>` задачи 1)
- **Commit:** `0ad4272`

**2. [Rule 2 - Missing] Докстринг общего гарда обещал дубль, которого не стало**

- **Found during:** Task 1
- **Issue:** `is_same_origin` в `app/pages/common.py` содержал: «до него в `history.py` остаётся его собственная копия, и это ЕДИНСТВЕННЫЙ известный дубль правила». В момент снятия копии это утверждение стало ложным, а ложь в докстринге гарда безопасности — худший её сорт: следующий читатель пошёл бы искать вторую копию.
- **Fix:** абзац «РАМКИ» переписан по факту — три потребителя, копии нет, остаток (формы удаления без гарда) назван отдельно.
- **Files modified:** `app/pages/common.py` (вне `<files>` задачи 1)
- **Commit:** `0ad4272`

### Отступления от буквы плана

**3. Тесты задачи 1 живут в `tests/test_services/test_billing_service.py`, которого нет в её `<files>`**

Список файлов задачи 1 перечисляет только три исходника, а `<acceptance_criteria>` требует четырёх поведенческих проверок («при 5 платежах владельца и 3 чужих возвращает ровно 5» и далее) и называет прогон этого файла в `<verify>`. Проверить поведение, не написав теста, нельзя; файл выбран тот, который план сам и запускает.

**4. Заведена регрессия сверх плана: идентификатор платежа не попадает в тело ответа**

`<verification>` плана содержит пункт «Ни один маршрут проекта больше не отдаёт `yookassa_payment_id` в тело ответа», но ни одна задача его тестом не закрывает — задача 3 закрывает его сносом маршрута. После решения возвращать строки модели (см. «Decisions») идентификатор снова оказался В КОНТЕКСТЕ, хоть и не в разметке. Пункт верификации фазы закреплён регрессией по телу ответа, коммит `7d1f55a`.

**5. `POST /billing/subscribe` получил пустое умолчание поля**

План задачи 2 обработчик подписки не упоминает вовсе. Правка на одно слово сделана ради того, чтобы два входа одного раздела не расходились в ответе на пустое поле формы. Ни один тест плана `05-01` не изменился.

**6. Литерал лимита истории операций вынесен в именованную константу**

`get_transaction_history(db, user.id, limit=20)` при переписывании обработчика получил имя `TRANSACTION_LIST_LIMIT` — рядом с потолком платежей, чтобы два потолка одного экрана были видны как два разных решения, а не как число и константа.

---

**Total deviations:** 2 auto-fixed (Rule 3 и Rule 2, оба — следствие снятия дубля гарда) + 4 задокументированных отступления от буквы плана
**Impact on plan:** Все `must_haves.truths` выполнены, кроме `verification: backstop`, которая автотестом и не проверяется. За пределы `files_modified` плана выходят три файла: `tests/test_pages/test_history_retry.py` и `app/pages/common.py` (оба — обязательное следствие задачи 1) и `tests/test_services/test_billing_service.py` (файл, который план сам запускает в `<verify>`). Файлы соседнего плана `05-05` (`app/templates/billing/**`, `app/static/css/app.css`) не открывались.

## Issues Encountered

- **Полная суита идёт ~16 минут** (1526 тестов). Промежуточные прогоны резались по файлам, финальный вынесен в фоновый процесс. Та же проблема окружения, что отмечена в `05-01`…`05-03`.
- **Контекст шаблона недоступен из ответа httpx.** Транспорт ASGI отдаёт только тело; расширение Starlette, кладущее контекст рядом с ответом, им не включается. Заведён контекстный менеджер `rendered_context`, подменяющий РОВНО метод отрисовки и зовущий настоящий: страница рендерится по-честному, а тест видит уехавшее в неё. Иначе контракт «обработчик → разметка» пришлось бы проверять по HTML, которого до плана `05-05` нет.
- **Пустое поле формы у FastAPI — не пустая строка, а отсутствие.** Обнаружено красным тестом на `package_index=""`, ожидавшим 302 и получившим 422. Разбор — в «Decisions».
- **`graphify update .` не выполнялся:** каталога `graphify-out/` в worktree нет (он не отслеживается git). Обновление графа принадлежит основному дереву.

## Known Stubs

Заглушек нет: каждый блок контекста подключён к настоящему источнику — оси к `plan_axes`, деньги к `payments`, сообщения к `message_balances` и `balance_transactions`, планы к `Settings.plan_limits`.

Границы, ЯВНО отданные соседям (не заглушки):

| Что | Кем закрывается |
|---|---|
| Разметка всех пяти блоков: карточки планов, метры осей, строки платежей, пометка истёкшего срока, сообщение о сработавшем потолке | `05-05` |
| Перевод кнопки «Купить» в `billing/balance.html` на форму `POST /billing/purchase` и снос скрипта покупки | `05-05` |
| Отметка `BILL-05` / `BILL-06` / `BILL-07` в `REQUIREMENTS.md` | `05-05` (после разметки) |
| Выкат ревизии `0017` на боевую базу | `05-06` |

⚠️ **Известное промежуточное состояние между планами.** Кнопка «Купить» в `billing/balance.html` до сих пор зовёт скриптом снесённый JSON-маршрут — то есть покупка пакета из разметки сейчас не работает. Это последовательность, предписанная планом (`05-04` сносит маршрут, `05-05` сносит скрипт и ставит форму), а не дефект; серверная половина покупки работает и покрыта восемью тестами. Оставлять раздел в этом состоянии дольше, чем до `05-05`, нельзя.

## Threat Flags

Новой поверхности сверх `<threat_model>` плана не появилось. Все семь `mitigate`-диспозиций реализованы: T-05-20 (владение предикатом + именованный тест), T-05-21 (JSON-маршрут снесён + регрессия на тело ответа), T-05-22 (из формы только индекс), T-05-23 (`is_same_origin` на изменяющем входе), T-05-24 (у GET нет пути записи — проверено и поведением, и структурно), T-05-25 (`limit` равен константе, потолок называет себя), T-05-26 (строка `pending` видна сразу после возврата).

| Flag | File | Description |
|---|---|---|
| threat_flag: note | `app/pages/billing.py` | Контекст раздела несёт строки `Payment` ЦЕЛИКОМ, включая `yookassa_payment_id`. В тело ответа он не попадает (закреплено регрессией), но макрос строки платежа плана `05-05` не имеет права его печатать — ни в атрибуте, ни в комментарии разметки. |

## Next Phase Readiness

**Готово к плану `05-05` (разметка раздела).** Контракт контекста `GET /billing`:

| Ключ | Форма | Замечание |
|---|---|---|
| `subscription` | `{plan: str, expires_at: datetime \| None, expired: bool}` | `expired` уже посчитан; разметка НЕ сравнивает даты сама |
| `usage` | `list[PlanAxis]` в `AXIS_ORDER` | `limit is None` — безлимит, рисовать «без ограничений», не «0»; `percent` клампован |
| `plans` | `list[dict]` из конфига | Уже разобран; `settings.parsed_plan_limits` из Jinja звать нельзя |
| `balance_info`, `transactions`, `packages` | как прежде | Блок сообщений остаётся ОТДЕЛЬНЫМ от оси «Отправок в месяц» (D-10) |
| `payments` | `list[Payment]` | Строки модели: `created_at` — настоящий `datetime`, `status` принимает `pending`/`succeeded`/`canceled` |
| `payments_total`, `payments_cap`, `payments_truncated` | `int`, `int`, `bool` | При `payments_truncated` экран ОБЯЗАН сказать, что показаны не все, и назвать `payments_cap` |
| `payments_enabled` | `bool` | Гасит кнопки, а не витрину: планы и оси приезжают и при выключенных платежах |

**Что знать плану `05-05`:** формы обеих оплат — `POST /billing/subscribe` (поле `plan`) и `POST /billing/purchase` (поле `package_index`). Оба принимают пустое значение и отвечают на него редиректом в раздел, поэтому скрытое поле без значения даст возврат на экран, а не страницу ошибки.

## Self-Check: PASSED

Файлы на месте:
- `app/pages/billing.py` — FOUND
- `app/services/billing_service.py` — FOUND
- `app/constants.py` — FOUND
- `tests/test_pages/test_billing_section.py` — FOUND

Коммиты в истории ветки: `ec4b78a`, `06893a6`, `0ad4272`, `e6882bd`, `53d33b4`, `1ebaa78`, `0f6b040`, `7d1f55a` — все FOUND.

Проверки приёмки:
- `uv run pytest tests/ -q` → **1526 passed, exit code 0** (947 с)
- `uv run pytest tests/test_pages/test_history_retry.py tests/test_services/test_billing_service.py -q` → 82 passed
- `uv run pytest tests/test_pages/test_billing_section.py -q` → 25 passed
- `uv run pytest tests/test_routes/test_billing.py tests/test_routes/test_billing_webhook_source.py tests/test_pages/test_billing_section.py -q` → 36 passed
- `grep -c 'def _is_same_origin' app/pages/history.py` → **0**; `is_same_origin` присутствует импортируемым именем (строки 38, 913)
- `grep -c 'order_by(Payment.amount_value' app/services/billing_service.py` → **0**
- `app/constants.py:69` → `PAYMENT_LIST_CAP: int = 200`
- `grep -c 'parsed_plan_limits' app/pages/billing.py` → 3; в `app/templates/billing/balance.html` → **0**
- `grep -Ec '(db|session)\.(add|commit|flush)\(' app/pages/billing.py` → **0**
- `grep -c 'PurchaseRequest' app/routes/billing.py` → **0**; `@router.post("/purchase")` → **0**
- `@router.post("/webhook")` → 1; три `@router.get` чтения → 3
- `yookassa_payment_id` вне `app/models/payment.py` встречается только в комментариях и в сервисе платежей — ни один маршрут его не отдаёт

---
*Phase: 05-tarify*
*Completed: 2026-08-15*

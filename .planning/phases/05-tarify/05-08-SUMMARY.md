---
phase: 05-tarify
plan: 08
subsystem: payments
tags: [yookassa, sqlalchemy, compare-and-swap, concurrency, webhook, sqlite, postgresql]

# Dependency graph
requires:
  - phase: 05-tarify (план 05-06)
    provides: колонка `payments.kind`, константы KIND_*, ветвление вебхука по предмету покупки
  - phase: 05-tarify (план 05-07)
    provides: гард источника вебхука — закрывает вход, пока этот план закрывает расчётную часть
provides:
  - "`_claim_payment` — атомарная заявка на обработку платежа условным UPDATE (compare-and-swap)"
  - "`_mirror_claim` — отзеркаливание выигранной заявки на объект платежа без второго UPDATE"
  - "приращение баланса выражением на стороне СУБД в `add_messages` (RETURNING)"
  - "`with_for_update()` на выборке платежа — сериализация доставок на PostgreSQL"
  - "ключ журнала `webhook_claim_lost` и `webhook_package_without_messages_count`"
  - "регрессия на КОНКУРЕНТНУЮ доставку двумя сессиями поверх файловой базы SQLite"
affects: [06-admin, billing, subscription-management]

actuals:
  tokens: 15050
  tasks: 1
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Compare-and-swap заявкой: условие входит в тот же оператор, что и запись — зазора между проверкой и записью не остаётся вовсе"
    - "Приращение счётчиков выражением на стороне СУБД вместо чтения-изменения-записи в Python"
    - "`set_committed_value` для отзеркаливания Core-UPDATE на ORM-объект без пометки грязным"
    - "Детерминированное наложение доставок в тесте подменой `execute` у сессии, а не `asyncio.gather`"

key-files:
  created:
    - tests/test_services/test_payment_concurrency.py
  modified:
    - app/services/payment_service.py
    - app/services/billing_service.py
    - app/pages/billing.py

key-decisions:
  - "Заявка стоит ПЕРЕД любым начислением и в той же транзакции, что и оно: единственный commit ветки остаётся единственным, платёж не может оказаться помеченным проведённым без выданного ресурса"
  - "Проигравшая заявку доставка возвращает True, а не 5xx: отказ спровоцировал бы новую попытку ЮKassa по уже проведённому платежу"
  - "Проверка пустого `messages_count` поставлена ДО заявки, а не после (план допускал оба места): заявить платёж проведённым и затем отказаться значило бы пометить выданным то, что не выдано"
  - "Отзеркаливание статуса на ORM-объект через `set_committed_value`, а не присваиванием: присваивание дало бы на коммите второй UPDATE тех же колонок"
  - "Наложение в тесте задаётся подменой `execute` у сессии первой доставки, а не подменой `_claim_payment`: этот сеам существует и в СТАРОМ коде, поэтому RED падает на настоящем дефекте, а не на отсутствии новой функции"

patterns-established:
  - "Заявка на обработку внешнего уведомления: условный UPDATE по неконечному статусу, rowcount как исход, проигравший выходит тихо и успешно"
  - "Регрессия на конкурентность живёт на ФАЙЛОВОЙ базе SQLite: содержимое базы в памяти между соединениями не сохраняется"

requirements-completed: []

coverage:
  - id: D1
    description: "Две наложившиеся доставки одного пакетного платежа начисляют ровно один раз: баланс 100, а не 200"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_concurrency.py#test_overlapping_deliveries_credit_the_package_exactly_once"
        status: pass
    human_judgment: false
  - id: D2
    description: "Журнал операций и баланс не расходятся: по одному payment_id ровно одна строка BalanceTransaction"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_concurrency.py#test_overlapping_deliveries_write_one_balance_transaction"
        status: pass
    human_judgment: false
  - id: D3
    description: "Две наложившиеся доставки подписочного платежа дают одну строку subscriptions и сдвиг ровно на один месяц"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_concurrency.py#test_overlapping_deliveries_extend_subscription_by_one_month"
        status: pass
    human_judgment: false
  - id: D4
    description: "Проигравшая заявку доставка возвращает True и оставляет след в журнале ключом webhook_claim_lost"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_concurrency.py#test_the_losing_delivery_answers_accepted"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_payment_concurrency.py#test_the_losing_delivery_is_visible_in_the_log"
        status: pass
    human_judgment: false
  - id: D5
    description: "Пакетный платёж с пустым messages_count не начисляет и не роняет обработчик TypeError (WR-04, T-05-39)"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_concurrency.py#test_a_package_payment_without_a_count_credits_nothing"
        status: pass
    human_judgment: false
  - id: D6
    description: "Восемь существующих тестов идемпотентности зелёные БЕЗ правки их текста; суита целиком зелёная"
    verification:
      - kind: unit
        ref: "uv run pytest tests/ -q → 1562 passed, exit 0"
        status: pass
    human_judgment: false
  - id: D7
    description: "with_for_update() на выборке платежа сериализует доставки на PostgreSQL"
    requirement: BILL-05
    verification: []
    human_judgment: true
    rationale: "SQLite молча опускает FOR UPDATE — суита проекта живёт на SQLite и проверить эту половину защиты НЕ МОЖЕТ в принципе. Подтверждение требует прогона на PostgreSQL, которого у исполнителя нет."
  - id: D8
    description: "Решение об уникальности активной подписки на уровне схемы (ревизия 0018) — задачи 2-3 плана"
    verification: []
    human_judgment: true
    rationale: "НЕ ВЫПОЛНЕНО. Плановый чекпойнт `checkpoint:decision` с gate=blocking; исполнение остановлено на нём и решение владельца не принято."

# Metrics
duration: 40min
completed: 2026-08-16
status: halted
---

# Phase 05 Plan 08: Атомарная заявка на обработку платежа Summary

**Compare-and-swap заявка `_claim_payment` условным UPDATE плюс приращение баланса выражением на стороне СУБД — наложившиеся доставки одного уведомления ЮKassa начисляют ровно один раз на обоих диалектах.**

## ⚠️ План ОСТАНОВЛЕН на чекпойнте — выполнена 1 задача из 3

Задача 2 — `checkpoint:decision` с `gate="blocking"`, `autonomous: false`, `workflow.auto_advance = false`.
Исполнитель ОБЯЗАН остановиться и НЕ вправе выбрать вариант за владельца. Задача 3 ветвится
по этому решению и потому не начиналась.

**Что требует решения:** делать ли двойную активную подписку невозможной на уровне схемы —
частичный уникальный индекс по `subscriptions.user_id` при `is_active` новой ревизией `0018`.
Варианты: `constraint-now` | `constraint-plus-backfill-guard` | `app-only`.
Полный контекст, цена и риск выката — в задаче 2 файла `05-08-PLAN.md`.

## Performance

- **Duration:** ~40 min (из них ~18 min — прогон полной суиты при трёх параллельных агентах на одной машине)
- **Started:** 2026-08-16T11:14Z
- **Completed (задача 1):** 2026-08-16T11:54Z
- **Tasks:** 1 из 3
- **Files modified:** 4 (3 изменено, 1 создан)

## Accomplishments

- **Подтверждённый гэп 2 закрыт целиком.** Заявка `_claim_payment` — условный UPDATE по
  `yookassa_payment_id` И неконечному статусу. Условие входит в ТОТ ЖЕ оператор, что и запись,
  поэтому между проверкой и записью не остаётся зазора вовсе. Проигравший видит `rowcount == 0`,
  делает `rollback`, пишет `webhook_claim_lost` и возвращает `True`.
- **Потерянное обновление баланса стало недостижимым, а не маловероятным.** `add_messages`
  считает приращение выражением `MessageBalance.balance + amount` на стороне СУБД и берёт новый
  баланс через `RETURNING`. Чтения-изменения-записи в Python в этой функции больше нет как приёма.
- **Регрессия проверяет НАЛОЖЕНИЕ, а не последовательность.** Новый файл на 6 тестов: две
  независимые сессии поверх одной файловой базы SQLite, порядок задан детерминированно.
- **RED был настоящим.** До правки тесты падали ровно симптомами отчёта верификации:
  баланс `200 вместо 100`, `2` строки BalanceTransaction вместо одной, срок подписки сдвинут
  на `2026-10-16` вместо `2026-09-16`, ключа `webhook_claim_lost` в журнале нет,
  `TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'`.
- **Вход WR-04 закрыт с обеих сторон.** Оба вызова `create_payment` в `app/pages/billing.py`
  переведены на константы `KIND_SUBSCRIPTION` / `KIND_PACKAGE`, а пакетная ветка вебхука
  проверяет `messages_count` до заявки.
- **Суита целиком зелёная:** `uv run pytest tests/ -q` → **1562 passed**, exit 0. Восемь
  существующих тестов идемпотентности прошли БЕЗ единой правки их текста.

## Task Commits

1. **Task 1 (RED): регрессия на конкурентную доставку** — `a7c8063` (test)
2. **Task 1 (GREEN): заявка и приращение на стороне СУБД** — `ed1d1b0` (feat)
3. **Task 2: чекпойнт решения** — НЕ ВЫПОЛНЕНА (блокирующая остановка)
4. **Task 3: исполнение решения** — НЕ НАЧИНАЛАСЬ (ветвится по задаче 2)

Фазы REFACTOR не потребовалось: правка легла в существующую структуру ветвей `handle_webhook`,
чистить после GREEN было нечего.

## Files Created/Modified

- `tests/test_services/test_payment_concurrency.py` (создан, 276 строк) — 6 тестов наложения
  доставок; докстринг объясняет три неочевидных выбора: файловая база вместо базы в памяти,
  детерминированное наложение вместо `asyncio.gather`, и почему подмена `execute` не упирается
  в блокировки SQLite.
- `app/services/payment_service.py` — `_claim_payment`, `_mirror_claim`, `with_for_update()` на
  выборке, заявка в обеих терминальных ветвях, проверка пустого `messages_count`, переписанный
  докстринг `handle_webhook`.
- `app/services/billing_service.py` — `add_messages` считает приращение на стороне СУБД.
  `reset_free_monthly` НЕ ТРОНУТА намеренно (см. Решения).
- `app/pages/billing.py` — оба вызова `create_payment` на константах `KIND_*`.

## Проверка критериев приёмки задачи 1

| Критерий | Факт |
|----------|------|
| `pytest` трёх файлов задачи, код 0 | ✅ 43 passed |
| `uv run pytest tests/ -q`, код 0 | ✅ 1562 passed, exit 0 |
| `grep -c 'with_for_update' app/services/payment_service.py` >= 1 | ✅ 2 |
| `grep -c '_claim_payment' app/services/payment_service.py` >= 2 | ✅ 4 |
| `grep -c 'webhook_claim_lost' app/services/payment_service.py` >= 1 | ✅ 2 |
| `grep -c 'synchronize_session' app/services/payment_service.py` >= 1 | ✅ 3 |
| `grep -c 'MessageBalance.balance + ' app/services/billing_service.py` >= 1 | ✅ 1 |
| `grep -n 'bal\.balance += amount'` не даёт вывода | ✅ пусто |
| `grep -c 'bal\.balance += free_limit'` == 1 | ✅ 1 |
| `grep -c 'KIND_SUBSCRIPTION' app/pages/billing.py` >= 1 | ✅ 2 |
| `grep -c 'KIND_PACKAGE' app/pages/billing.py` >= 1 | ✅ 2 |
| `grep -c 'kind="subscription"' app/pages/billing.py` == 0 | ✅ 0 |
| Восемь тестов идемпотентности зелёные без правки | ✅ файл не менялся вовсе |

## Decisions Made

**1. Сеам для наложения — `execute` сессии, а не `_claim_payment`.**
План предлагал подменять `_claim_payment`. Так RED падал бы `AttributeError` («функции ещё нет»),
то есть по причине «не реализовано», а не «дефект воспроизведён». Подмена `execute` у сессии
первой доставки — сеам, существующий и в СТАРОМ коде: первый `execute` в `handle_webhook` это
выборка платежа. Поэтому RED показал НАСТОЯЩИЕ симптомы дефекта (баланс 200, две строки журнала,
два месяца), а не отсутствие новой функции. Боевого крючка ради теста по-прежнему не добавлено.

**2. Проверка пустого `messages_count` стоит ДО заявки, а не после.**
План говорил «в ветке пакета, перед начислением». Формально это допускало место и после заявки.
Выбрано «до»: заявить платёж `succeeded` и затем вернуть `False` значило бы пометить платёж
проведённым, ничего не выдав, — ровно тот исход, который труть №10 плана запрещает.

**3. Отзеркаливание через `set_committed_value`, а не присваиванием.**
План говорил «отзеркалить `status` и `confirmed_at` на объекте `db_payment` в Python».
Простое присваивание пометило бы объект грязным, и ORM выдала бы на `commit` ВТОРОЙ UPDATE тех же
колонок — лишний оператор, притворяющийся, что запись сделал он. То же соображение применено в
`add_messages` к объекту баланса, где присваивание было бы уже не косметикой, а ПОВТОРНЫМ
приращением поверх посчитанного СУБД.

**4. Проигравшая доставка делает `rollback` перед выходом.**
План этого не называл. Без отката сессия остаётся с открытой транзакцией: на PostgreSQL она
держала бы блокировку строки, взятую `with_for_update`, до закрытия сессии. Записей в транзакции
нет (UPDATE задел ноль строк), поэтому откат ничего не теряет.

**5. `reset_free_monthly` не тронута.** Она делает такое же приращение в Python, но к гэпу 2
отношения не имеет: конкурентных доставок одного ежемесячного начисления не бывает — его
инициирует единственная задача Celery. Правка была бы работой за пределами плана.

**6. Ключевое слово `type` в `add_messages` не переименовано** (IN-01) — см. Долги ниже.

## Deviations from Plan

Отклонений по правилам 1-3 не потребовалось: дефектов вне плана в затронутом коде не встретилось.
Четыре уточнения плана выше (Решения 1-4) — выбор из мест, которые план оставлял на исполнителя,
и одно добавление (`rollback`), необходимое для корректности на PostgreSQL.

**Total deviations:** 0 auto-fixed. 1 добавление сверх текста плана (`rollback` проигравшего) —
правило 2, критично для корректности блокировок на боевом диалекте.
**Impact on plan:** расширения объёма нет; `reset_free_monthly` и восемь тестов идемпотентности
не тронуты, как и требовал критерий приёмки.

## Известные щели и долги

Эти записи предназначались для `.planning/STATE.md` §Blockers/Concerns задачей 3.
**Записать их некуда:** исполнение остановлено на задаче 2, а STATE.md в режиме worktree правит
оркестратор, не исполнитель. Перечисляю здесь, чтобы они не растворились.

| # | Запись | Статус |
|---|--------|--------|
| CR-02 | Гэп 2 (двойное начисление) — механизм: заявка `_claim_payment` + приращение на стороне СУБД + `with_for_update` на PostgreSQL. Регрессия: `tests/test_services/test_payment_concurrency.py` | 🟢 **закрыт планом 05-08** |
| T-05-38 | Два РАЗНЫХ платежа одного пользователя внахлёст при отсутствующей подписке дают ДВЕ строки `subscriptions`; читатель шелла увидит одну, продление будет двигать другую — молча и без ошибки в журнале | 🟡 **открыт, ждёт решения чекпойнта задачи 2** |
| WR-03 | Ревизия `0017` молча теряет `ON DELETE CASCADE` на SQLite; фикстура round-trip слабее, чем обещает докстринг. Отложено: прод — PostgreSQL, где batch-режим вырождается в обычный `ALTER` и внешний ключ не трогается; правка означала бы смену текста УЖЕ ОТГРУЖЕННОЙ ревизии, стоящей в очереди на выкат | 🟡 долг к работам по выкату очереди ревизий |
| IN-02 | `server_default='package'` остаётся на `payments.kind` навсегда. Та же причина отсрочки — правка текста отгруженной ревизии `0017`. Половина связки (защита ветки от пустого `messages_count`) закрыта задачей 1 | 🟡 долг того же раздела |
| IN-05 | Свежий ключ идемпотентности на каждый вызов `create_payment` — двойной клик создаёт ДВА разных платежа ЮKassa. Другой класс дефекта: два разных идентификатора, а не двойная обработка одного; оплачен будет один, в журнале появится вторая строка «в обработке» — неопрятно, но денег не теряет | 🟡 мелкий долг |
| IN-01 | `type` в подписи `add_messages` не переименован: смена ключевого слова правит все вызовы (`app/pages/admin.py`, `app/services/payment_service.py`, 6 мест в тестах) и к гэпу отношения не имеет | 🟡 косметический долг |

## Known Stubs

Заглушек нет. Пропущенных тестов не оставлено. Все `<verify>` выполненной задачи прогнаны.

**Непроведённая ключевая связь (честная формулировка).** Связь `must_haves.key_links`
«уникальность `subscriptions.user_id` → невозможность второй строки подписки **(условно)**»
остаётся **непроведённой**: её условие («условно» — по решению чекпойнта задачи 2) не разрешилось
вовсе, потому что чекпойнт не пройден. Это НЕ «трута не выполнена» — труты про уникальность в
плане нет; это объявленная условной связь, чьё условие пока не наступило. Остальные три
`key_links` проведены и покрыты тестами.

**Труть, непокрываемая суитой в принципе.** «На PostgreSQL выборка платежа берёт блокировку
строки» — код есть (`with_for_update()`), но SQLite молча опускает `FOR UPDATE`, поэтому суита
проекта эту половину не проверяет и проверить не может. Ровно по этой причине вторым, портируемым
и покрытым механизмом сделана заявка: защита не зависит от диалекта.

## Threat Flags

Нового поверхностного риска вне `<threat_model>` плана не добавлено. Диспозиции задачи 1
исполнены: T-05-35 (заявка), T-05-36 (приращение на стороне СУБД), T-05-39 (пустой
`messages_count`), T-05-40 (`webhook_claim_lost`). T-05-38 и T-05-41 ждут решения чекпойнта.

## Issues Encountered

- **Полная суита идёт ~18 минут** при трёх параллельных агентах на одной машине (три процесса
  pytest по 97% CPU). Прогон вынесен в фон и дождан; результат — 1562 passed, exit 0.

## User Setup Required

None — новых внешних сервисов и переменных окружения план не вводит. Ни одного пакета не
установлено: `pyproject.toml` не менялся.

## Next Phase Readiness

**Блокер:** решение владельца по чекпойнту задачи 2. До него задача 3 не может начаться, а
остаточная щель T-05-38 остаётся открытой.

Готово к продолжению: расчётная часть вебхука защищена и покрыта регрессией; ревизия `0018`
(если владелец выберет `constraint-*`) встанет на `down_revision = "0017"` — история ревизий
этим планом не тронута.

---
*Phase: 05-tarify*
*Halted at checkpoint: 2026-08-16*
</content>

---
phase: 05-tarify
plan: 11
subsystem: payments
tags: [yookassa, subscription, webhook, upgrade-only, pytest, fastapi, sqlalchemy]

# Dependency graph
requires:
  - phase: 05-tarify (план 05-10)
    provides: "Правило `upgrade-only` на стадии намерения: `PLAN_ORDER`, гард формы `POST /billing/subscribe`, четвёртое состояние CTA карточки, помощники тестов `_seed_live_subscription`/`_subscription_rows`/`_aware`"
  - phase: 05-tarify (планы 05-01, 05-08)
    provides: "`next_expiry` (остаток не сжигается), заявка `_claim_payment` и единственный `commit` подписочной ветки"
provides:
  - "`app/application/billing/plan_switch.py` — единственное объявление правила перехода между тарифами (`switch_is_refused`)"
  - "Сверка ранга на СТАДИИ ПРИМЕНЕНИЯ: подтверждённый платёж младшего тарифа больше не понижает действующий старший"
  - "Ключ журнала `subscription_plan_preserved` (уровень `warning`) — расхождение уплаченного и действующего тарифа оставляет след"
  - "Регрессия на стадию применения: повышение, понижение, продление, пустой план, план без ранга, первая покупка с Free"
  - "Докстринг `_extend_subscription`, совпадающий с исполняемым кодом"
affects: [05-verification-round-3, admin-payments, billing-ui]

# Actuals (#2632)
actuals:
  tokens: 11000
  tasks: 2
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Правило, стоящее денег, объявляется в `app/application/` — слое, видном обоим потребителям (`app/pages/` и `app/services/`), потому что прямой переиспользование замкнуло бы цикл импорта"
    - "Единственность объявления проверяется по ОБЪЕКТАМ модулей (`a.f is b.f`), а не по тексту исходника"
    - "Границы модуля прикладного слоя проверяются двумя способами: отсутствие протёкших атрибутов и разбор импортов через `ast`"

key-files:
  created:
    - app/application/billing/plan_switch.py
    - tests/test_application/test_plan_switch.py
  modified:
    - app/services/payment_service.py
    - app/pages/billing.py
    - tests/test_pages/test_billing_payment_errors.py

key-decisions:
  - "Правило `upgrade-only` вынесено в `app/application/billing/plan_switch.py` вместо переиспользования гарда формы: `app/pages/billing.py` уже импортирует `app/services/payment_service.py`, и обратный импорт замкнул бы цикл (T-05-56)"
  - "На стадии применения отказ означает НЕ отклонение платежа, а сохранение действующего тарифа: срок двигается всегда, план только повышается — оба ограничения (не взять деньги молча / не сжечь оплаченный остаток) удовлетворяются одновременно"
  - "Уровень `warning`, а не `info`, у ключа `subscription_plan_preserved`: платёж принят и дни выданы, но уплаченный тариф применён не был — это исход, по которому к нам придёт человек"
  - "Ветка ПЕРВОЙ вставки подписки сверки ранга не получила: подписки нет, защищать нечего, а сравнение ранга с пустотой отвергло бы первую же покупку"
  - "Логика сравнения рангов при переносе НЕ переписана — переехало только место объявления; переписывание верной и покрытой логики завело бы новый класс расхождения вместо закрытия старого"

patterns-established:
  - "Двухстадийное правило: одно объявление, два читателя (НАМЕРЕНИЕ — продавать ли; ПРИМЕНЕНИЕ — что делать с уже уплаченным), и разная цена отказа на каждой стадии"
  - "Отказ по умолчанию у незнакомого плана держится зеркальными тестами на ОБЕИХ стадиях"

requirements-completed: [BILL-05, BILL-06]

coverage:
  - id: D1
    description: "Подтверждённый платёж младшего тарифа не понижает действующий старший: два платежа (`pro`, затем `basic`) у пользователя без подписки оставляют `plan == 'pro'` и срок, сдвинутый дважды"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_confirmed_lower_plan_does_not_strip_the_higher_one_at_the_apply_stage"
        status: pass
    human_judgment: false
  - id: D2
    description: "Правило `upgrade-only` объявлено ОДИН раз и читается обеими стадиями; второй реализации сравнения рангов в `app/` не существует"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_switch.py#test_both_stages_read_the_same_declaration_of_the_rule"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_plan_switch.py#test_the_only_import_of_the_rule_is_the_declared_plan_order"
        status: pass
    human_judgment: false
  - id: D3
    description: "Сохранение старшего тарифа оставляет собственный след в журнале — ключ `subscription_plan_preserved` с уплаченным и сохранённым планом"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_the_preserved_plan_is_visible_in_the_log"
        status: pass
    human_judgment: false
  - id: D4
    description: "Повышение на стадии применения применяется; продление своего тарифа и первая покупка с Free не изменились"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_confirmed_higher_plan_is_applied_at_the_apply_stage"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_renewing_the_own_plan_still_moves_the_date_at_the_apply_stage"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_the_first_subscription_still_takes_its_plan_from_the_payment"
        status: pass
    human_judgment: false
  - id: D5
    description: "Незнакомый план ранга не получает на ОБЕИХ стадиях: действующий план сохраняется, срок двигается, отказ записан журналом"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_switch.py#test_an_unranked_plan_is_refused_from_either_side"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_paid_plan_without_a_rank_keeps_the_live_plan_at_the_apply_stage"
        status: pass
    human_judgment: false
  - id: D6
    description: "Значение `subscription.plan`, по лимитам которого рисуются четыре метра BILL-06, больше не портится на записи"
    requirement: BILL-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_confirmed_lower_plan_does_not_strip_the_higher_one_at_the_apply_stage"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py (22 теста, план 05-03, зелёные)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Докстринг `_extend_subscription` совпадает с исполняемым кодом: называет обе стадии, исход подтверждённого платежа младшего тарифа и ключ журнала расхождения"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_billing_payment_errors.py#test_the_switch_semantics_are_named_in_the_place_that_moves_the_date"
        status: pass
    human_judgment: false
  - id: D8
    description: "Человек, оплативший младший тариф и оставшийся на старшем, видит строку истории «Basic · продление» рядом с бейджем действующего тарифа «Pro». Понятность этого сочетания — суждение человека; интерфейсной работы план не вёл (граница объёма)"
    requirement: BILL-06
    verification: []
    human_judgment: true
    rationale: "Прохибиция BILL-06/transparency остаётся `unresolved`: разметка не может доказать, что сочетание строки истории и бейджа читается верно. Требует UAT владельца"
  - id: D9
    description: "Настоящее уведомление ЮKassa о подтверждённом платеже проходит новую сверку ранга без отказа"
    verification: []
    human_judgment: true
    rationale: "Боевого доступа к API ЮKassa у исполнителя нет — всё покрытие на моках (перенесено из human_verification 05-VERIFICATION.md, D-26)"

# Metrics
duration: 42min
completed: 2026-08-16
status: complete
---

# Phase 05 Plan 11: Правило `upgrade-only` доходит туда, где приходят деньги — Summary

**Сравнение рангов тарифов вынесено в единственное объявление `app/application/billing/plan_switch.py` и подключено к стадии ПРИМЕНЕНИЯ: подтверждённый платёж младшего тарифа больше не снимает уплаченный старший, а сохранение тарифа пишет `subscription_plan_preserved`.**

## Performance

- **Duration:** ~42 min (без учёта 17-минутного прогона полной суиты)
- **Tasks:** 2
- **Files modified:** 5 (2 создано, 3 изменено)
- **Тесты:** `uv run pytest tests/ -q` — **1665 passed**, код выхода 0

## Accomplishments

- **Закрыт блокер денежного пути (гэп 1, `05-VERIFICATION.md`).** Дефект воспроизведён тестом ДО правки: пользователь без подписки заводил два платежа — `pro`, затем `basic`; гард формы не участвовал ни в одном нажатии (действующей подписки на тот момент не было), и оплаченный месяц старшего тарифа становился днями младшего. Красный тест падал ровно на `assert 'basic' == 'pro'`.
- **Правило объявлено один раз.** `switch_is_refused` живёт в `app/application/billing/plan_switch.py`; `app/pages/billing.py` потерял приватную копию `_switch_is_refused` и импорт `PLAN_ORDER`, `app/services/payment_service.py` получил вызов того же объявления. Единственность проверяется по объектам модулей, а не по тексту.
- **Расхождение перестало быть невидимым.** `subscription_plan_preserved` уровня `warning` с `user_id`, `yookassa_id`, сохранённым и уплаченным планом выходит РАНЬШЕ `subscription_payment_succeeded` по потоку, поэтому пара читается однозначно.
- **Стадия применения получила регрессию, которой не было ни одной.** Семь новых сценариев: понижение, повышение, продление своего тарифа, пустой план платежа, план вне `PLAN_ORDER`, первая покупка с Free, запись в журнал.
- **Докстринг перестал вводить в заблуждение.** Абзац «⚠️ ГАРД СТОИТ НА ВХОДЕ, А НЕ ЗДЕСЬ» — тот самый, который верификатор назвал вводящим в заблуждение, — заменён описанием исполняемого поведения; подстроки `upgrade-only` и `05-01` уцелели, к ним добавлена проверка на ключ журнала.

## Task Commits

1. **Task 1 (tracer, TDD): правило доходит туда, где приходят деньги**
   - `aeaf93b` (test) — RED: воспроизведение верификатора + требование ключа журнала; параметр `payment_id` протянут через `_post`/`_subscribe`
   - `aa6f628` (feat) — GREEN: новый модуль правила, оба потребителя на нём, сверка ранга в `_apply_extension`
2. **Task 2 (TDD): соседние случаи, границы модуля и докстринг**
   - `b93636d` (test) — RED: таблица решений, границы модуля, соседние случаи стадии применения, утверждение о ключе в докстринге
   - `b752c8d` (docs) — GREEN: докстринг `_extend_subscription` приведён в соответствие с кодом

_TDD-последовательность соблюдена в обеих задачах: `test(...)` → реализация. Красный тест каждый раз падал по предмету проверки, а не по постороннему поводу._

## Files Created/Modified

- `app/application/billing/plan_switch.py` **(создан)** — `switch_is_refused`, единственное объявление правила перехода между тарифами. Единственный импорт — `app.constants`.
- `tests/test_application/test_plan_switch.py` **(создан)** — 10 собранных тестов: таблица решений (7 случаев), границы модуля (атрибуты + разбор импортов через `ast`), единственность объявления.
- `app/services/payment_service.py` — импорт правила; `_apply_extension` получил докстринг, сверку ранга и запись `subscription_plan_preserved`; последний абзац докстринга `_extend_subscription` переписан.
- `app/pages/billing.py` — `_switch_is_refused` удалён, оба вызова переведены на общее объявление, импорт `PLAN_ORDER` ушёл вместе с правилом.
- `tests/test_pages/test_billing_payment_errors.py` — раздел «СТАДИЯ ПРИМЕНЕНИЯ» (7 тестов), помощники `_confirm` и `_seed_subscription_payment`, необязательный `payment_id` у `_post`/`_subscribe`.

## Decisions Made

- **Порядок двух действий в `_apply_extension` — правило, а не оформление.** Срок двигается ВСЕГДА и первым; решение о плане принимается отдельно и не имеет права отменить начисление дней. Прохибиция плана 05-01 соблюдена ровно тем, что строка с `next_expiry` не изменилась.
- **Пустой план платежа выходит из функции ДО сверки.** Без явного выхода `switch_is_refused("pro", "")` вернул бы `True`, и ветка начала бы писать в журнал строку о расхождении, которого не было. Это закреплено отдельным тестом.
- **Проверка единственности объявления — по объектам, а не по тексту.** Текстовая проверка зеленела бы на второй реализации под другим именем и краснела бы от упоминания имени в комментарии, то есть ловила бы не то.
- **Границы нового модуля проверяются `ast`-разбором импортов.** Это не текстовое совпадение: предмет проверки — что модуль ИМПОРТИРУЕТ, а упоминание `app.pages` в докстринге импортом не является.

## Deviations from Plan

### 1. `graphify update .` не выполнен — артефакт вне worktree (перенесено, не отброшено)

- **Найдено в:** Task 2, шаг 4
- **Ситуация:** `graphify-out/` не отслеживается git (`git ls-files graphify-out` → 0 файлов) и в worktree отсутствует; граф лежит в основном рабочем каталоге `/source/broadcaster/graphify-out/graph.json`.
- **Решение:** команда НЕ запускалась в worktree. Прогон здесь построил бы новый граф по изолированной копии дерева, который был бы уничтожен вместе с worktree при снятии, а основной граф остался бы нетронутым и устаревшим. Трогать основной каталог из изолированного агента нельзя — и бессмысленно: правки этого плана туда ещё не влиты.
- **Что требуется:** выполнить `graphify update .` в основном каталоге ПОСЛЕ вливания ветки. Единственный незакрытый пункт критериев приёмки Task 2.
- **Тем же ограничением объясняется** отсутствие ориентирования через `graphify query`: графа в worktree нет, использовались Read/Grep (как и предписано инструкцией на этот случай).

### 2. Две новых теста получили фикстуру `authed_client`, которой не было в замысле

- **Найдено в:** Task 2, шаг 2
- **Проблема:** `test_a_payment_without_a_plan_moves_the_date_and_leaves_the_plan_alone` и `test_a_paid_plan_without_a_rank_keeps_the_live_plan_at_the_apply_stage` ходят только в БД и были написаны с одним `db_session`. Оба падали `NoResultFound`: владельца платежа заводит фикстура `authed_client` (регистрацией), и без неё `_current_user` не находит строки.
- **Исправление [Rule 3 — блокирующее]:** фикстура добавлена в оба теста, причина записана в докстринг помощника `_seed_subscription_payment`, чтобы следующий читатель не счёл параметр лишним.
- **Проверка:** оба теста зелёные; предмет проверки не изменился.
- **Коммит:** `b93636d`

---

**Итого отклонений:** 1 перенесённый пункт (внешний артефакт), 1 автоисправление (Rule 3, блокирующее).
**Влияние на план:** объём не расширен. Ни одного нового пакета, ни одной ревизии Alembic, ни одной правки `pyproject.toml`/`uv.lock` — проверено диффом относительно базы.

## Issues Encountered

- **Одинаковый идентификатор платежа ломал воспроизведение до его написания.** `_healthy_sdk` принимал `payment_id`, но `_post` его не прокидывал и всегда отдавал `"yoo_1"`. Два платежа одного пользователя с одним `yookassa_payment_id` дали бы в `handle_webhook` не воспроизведение дефекта, а `MultipleResultsFound`. Параметр протянут со значением по умолчанию `"yoo_1"`, поэтому 32 существующих теста не изменились ни строкой.
- **Порядок действий в воспроизведении оказался предметом проверки.** Оба платежа обязаны заводиться ДО первого уведомления: заведи второй платёж после подтверждения первого — сработал бы гард формы (подписка уже действует), вернул бы 302 и строки платежа не создал, то есть тест проверял бы вход вместо стадии применения.

## Известные заглушки

Нет. Заглушек, TODO и пропущенных тестов план не оставил.

## Threat Flags

Новой поверхности не добавлено. Схема БД, состав вызовов SDK и контракты маршрутов не менялись; `payment_data` в `_apply_extension` по-прежнему не передаётся (T-05-53 — сигнатура функции не расширена).

## Прохибиции и человеческие проверки — состояние

| Прохибиция | Тир | Состояние |
|---|---|---|
| BILL-05 / fairness | judgment | **`unresolved`, как и предписано планом.** Денежная половина закрыта тестом: оплаченный остаток старшего тарифа больше не превращается в дни младшего. Половина «слово пользователю ДО нажатия кнопки» в воспроизведённом сценарии недостижима — действующей подписки на момент нажатия нет, поэтому ни `DOWNGRADE_CARD_CAPTION`, ни гард формы не участвуют. Решение за владельцем; флаг `unverified-prohibition — human review recommended` сохраняется |
| BILL-05 / transparency | test | **`resolved`** — `subscription_plan_preserved`, тест `test_the_preserved_plan_is_visible_in_the_log` |
| BILL-06 / transparency | judgment | **`unresolved`** — сочетание строки истории «Basic · продление» с бейджем «Pro» требует суждения человека; интерфейсной работы план не вёл |

Перенесённые человеческие проверки (задачами НЕ становились): мобильная ширина 375px, настоящий платёж в тестовом магазине ЮKassa (D-26), статус отменённого платежа (D-27), читаемость формулировок.

## User Setup Required

Нет — новых переменных окружения, ключей конфига и внешних настроек план не вводит.

## Next Phase Readiness

- **Три пункта `missing:` гэпа 1 закрыты полностью:** сверка ранга стоит в `_apply_extension` и читает то же объявление, что гард формы; сохранение старшего тарифа оставляет строку журнала; регрессия на стадию применения существует.
- **Связь `PLAN_ORDER → switch_is_refused → _apply_extension`, помеченная `✗ NOT_WIRED` в `05-VERIFICATION.md`, теперь существует;** связь `PLAN_ORDER → switch_is_refused → subscribe_to_plan` уцелела при переносе (проверено тестами карточек и гарда без правки их тел).
- **Открытые пункты для следующего круга:** `graphify update .` в основном каталоге после вливания; две прохибиции тира `judgment` (BILL-05/fairness, BILL-06/transparency) — решение владельца в UAT.
- **Ограничение окружения:** боевого доступа к API ЮKassa нет, всё покрытие на моках. Первое настоящее уведомление после выката остаётся backstop-ом.

## Self-Check: PASSED

Файлы (5/5 на месте):
- FOUND: `app/application/billing/plan_switch.py`
- FOUND: `tests/test_application/test_plan_switch.py`
- FOUND: `app/services/payment_service.py`
- FOUND: `app/pages/billing.py`
- FOUND: `tests/test_pages/test_billing_payment_errors.py`

Коммиты (4/4 в истории ветки): `aeaf93b`, `aa6f628`, `b93636d`, `b752c8d`

Критерии приёмки, проверенные командами:
- `uv run pytest tests/ -q` → **1665 passed**, код 0
- `grep -c 'def switch_is_refused' app/application/billing/plan_switch.py` → 1
- `grep -c 'switch_is_refused' app/services/payment_service.py` → 3 (≥2)
- `grep -c 'switch_is_refused' app/pages/billing.py` → 4 (≥3)
- `grep -c 'subscription_plan_preserved' app/services/payment_service.py` → 1
- `grep -c '^from app.constants import PAYMENT_LIST_CAP$' app/pages/billing.py` → 1
- Единственность объявления по объектам модулей → код 0
- Границы нового модуля → код 0
- Докстринг содержит `upgrade-only`, `05-01`, `subscription_plan_preserved` → код 0
- `tests/test_application/test_plan_switch.py --collect-only -q` → **10 собранных** (≥7)
- `git diff --stat <base> HEAD -- pyproject.toml uv.lock` → пусто
- `git diff --name-only <base> HEAD -- alembic/` → пусто

Единственный незакрытый критерий: `graphify update .` — перенесён в основной каталог (см. «Deviations from Plan», п. 1).

---
*Phase: 05-tarify*
*Completed: 2026-08-16*

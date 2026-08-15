---
phase: 05-tarify
plan: 02
subsystem: payments
tags: [yookassa, webhook, alembic, subscription, billing, tdd]

# Dependency graph
requires:
  - phase: 05-tarify
    plan: 01
    provides: "Payment.kind / Payment.plan, ревизия 0017, ветка подписки и _extend_subscription в handle_webhook, IP-гард вебхука"
provides:
  - "Ветка события отмены в handle_webhook: отменённый платёж получает терминальный статус и ничего не начисляет (D-16)"
  - "TERMINAL_STATUSES — защита от повторной обработки распространена на второй терминал, одной копией на все ветки"
  - "KNOWN_EVENTS — знакомые события множеством КОНСТАНТ SDK, без строковых литералов (T-05-12)"
  - "tests/test_migrations/test_0017_payment_kind_and_plan.py — доказанная обратимость ревизии 0017 (закрывает human_judgment-долг D6 плана 05-01)"
  - "Обе половины D-04 закреплены точными регрессиями на уровне обработчика, а не только юнит-тестами арифметики"
affects: [05-04, 05-05, 05-06, 06-admin]

actuals:
  tokens: 11861
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Знакомые события вебхука — множество констант SDK; строковых литералов имён событий в сервисе нет"
    - "Идемпотентность написана через множество ТЕРМИНАЛЬНЫХ статусов, а не перечислением в каждой ветке"
    - "Ветка терминального исхода, которая ничего не начисляет, проверяется с двух сторон: «не позвали» и «баланс не изменился»"
    - "Снятие NOT NULL проверяется И объявлением (PRAGMA), И настоящей вставкой NULL — на SQLite это разные утверждения"
    - "Половина утверждения «до ревизии было иначе» пишется отдельным тестом, иначе парный тест не доказывает, что ревизия что-то изменила"

key-files:
  created:
    - tests/test_migrations/test_0017_payment_kind_and_plan.py
  modified:
    - app/services/payment_service.py
    - tests/test_services/test_payment_service.py

key-decisions:
  - "Момент отмены пишется в существующую колонку confirmed_at: её смысл — «когда платёж перешёл в терминальное состояние», второй колонки D-15 не заводит"
  - "Причина отмены (cancellation_details) не разбирается, не пишется и не логируется (T-05-13)"
  - "Проверка терминального статуса стоит ДО ветки отмены — платёж в succeeded не откатывается в canceled (T-05-10)"
  - "BILL-07 в REQUIREMENTS.md НЕ отмечается выполненным: экран истории платежей делают планы 05-04/05-05"
  - "Наследник лгавшего теста написан в RED-коммите задачи 1, оригинал снят коммитом задачи 2 — рерайт разложен по двум гейтам одного плана"

patterns-established:
  - "Тест, чьё утверждение отменено решением фазы, снимается вместе с именем, а не подгоняется под новый результат"
  - "Точка отсчёта, вычисляемая ВНУТРИ обработчика, проверяется окном между двумя замерами времени вокруг вызова, а не приблизительным «больше 27 дней»"

requirements-completed: []

coverage:
  - id: D1
    description: "Вебхук отмены даёт pending-платежу терминальный статус и момент решения"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_canceled_webhook_gives_a_pending_payment_a_terminal_status"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ветка отмены ничего не начисляет: add_messages и invalidate_balance_cache не зовутся, баланс не меняется"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_canceled_package_payment_credits_nothing"
        status: pass
    human_judgment: false
  - id: D3
    description: "Отмена платежа за тариф не создаёт подписку и не двигает срок действующей"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_canceled_subscription_payment_creates_no_subscription"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_canceled_subscription_payment_does_not_move_an_existing_expiry"
        status: pass
    human_judgment: false
  - id: D4
    description: "Терминальный статус обрабатывается один раз; проведённый платёж не откатывается уведомлением об отмене (T-05-10, T-05-11)"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_repeated_canceled_webhook_writes_nothing_twice"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_canceled_webhook_does_not_roll_back_a_succeeded_payment"
        status: pass
    human_judgment: false
  - id: D5
    description: "Неизвестные обработчику события (refund.succeeded, payment.waiting_for_capture) возвращают False и не меняют статус платежа"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_handle_webhook_ignores_an_event_it_does_not_know (2 параметра)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Обе половины D-04: действующая подписка продлевается от своего срока, истёкшая — от сегодня"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_an_active_subscription_is_extended_from_its_own_expiry"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_an_expired_subscription_is_extended_from_today"
        status: pass
    human_judgment: false
  - id: D7
    description: "Двойной вебхук по платежу подписки двигает срок один раз; первая покупка берёт план из платежа, а не из умолчания модели"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_a_repeated_subscription_webhook_moves_the_expiry_once"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_payment_service.py#test_the_first_purchase_takes_the_plan_from_the_payment"
        status: pass
    human_judgment: false
  - id: D8
    description: "Ревизия 0017 применяется и откатывается на схеме уровня 0016 без потери строк; backfill проставляет kind='package'; messages_count принимает NULL после и не принимал до (T-05-14)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0017_payment_kind_and_plan.py (7 тестов, настоящие alembic upgrade/downgrade)"
        status: pass
    human_judgment: false
  - id: D9
    description: "Настоящая отмена настоящего платежа в тестовом магазине ЮKassa доходит до истории пользователя терминальным статусом"
    requirement: BILL-07
    verification: []
    human_judgment: true
    rationale: "Требует боевого контура ЮKassa и настроенного notification URL; автоматизации в проекте нет. Экранная половина утверждения принадлежит планам 05-04/05-05."

duration: 25min
completed: 2026-08-15
status: complete
---

# Phase 05 Plan 02: Честный набор статусов платежа Summary

**Отменённый ЮKassa платёж перестал вечно висеть «в обработке»: у него появился терминальный статус, который ничего не начисляет, — а ревизия `0017` впервые доказана обратимой тестом внутри суиты.**

## Performance

- **Duration:** ~25 мин работы + 16 мин финального прогона полной суиты
- **Started:** 2026-08-15T17:47:00Z
- **Completed:** 2026-08-15T18:28:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 изменено, 1 создан)
- **Tests added:** +19 (суита 1449 → 1468)

## Accomplishments

- **Журнал платежей перестал врать.** До этого плана `handle_webhook` возвращал `False` на всё, кроме успеха, поэтому платёж, который ЮKassa отменила, навсегда оставался `pending`. Это не «нет данных», а неправда о них: экран показывал бы «в обработке» там, где денег не взяли вовсе (прохибиция BILL-07, T-05-15).
- **Ветка отмены не может ничего выдать.** Она проставляет статус и момент решения — и всё. Свойство проверено с двух сторон: `add_messages` не позван (мок) И баланс не изменился (настоящий запрос), чтобы начисление в обход мока тоже не прошло.
- **Уже проведённый платёж защищён от припоздавшей отмены.** Проверка терминального статуса стоит ДО ветвления по исходу, поэтому уведомление об отмене платежа в `succeeded` не отнимает выданное (T-05-10) — закреплено именованным тестом.
- **Идемпотентность не размножена.** Защита `status == "succeeded"` обобщена до множества `TERMINAL_STATUSES`. Это то же самое свойство, распространённое на второй терминал, а не второй экземпляр защиты.
- **Ревизия `0017` доказанно обратима.** План `05-01` закрывал это разовым прогоном вне репозитория и честно пометил `human_judgment: true`. Долг закрыт: 7 тестов гоняют настоящие `alembic upgrade`/`downgrade`.

## Task Commits

1. **Task 1: Ветка `payment.canceled`** — `5484be8` (test, RED: 6 failed) → `0ffd689` (feat, GREEN)
2. **Task 2: Снятие лгавшего теста + обе половины D-04** — `4738a09` (test)
3. **Task 3: Round-trip ревизии 0017** — `aae9561` (test)

_TDD-гейт задачи 1 соблюдён: `feat` предваряется `test`-коммитом, красным на своём дереве (6 failed, 7 passed). Задачи 2 и 3 производственного поведения не добавляют — они закрепляют уже существующее регрессиями, поэтому у них по одному `test`-коммиту и `feat`-гейта им не положено._

## Files Created/Modified

**Создано:**
- `tests/test_migrations/test_0017_payment_kind_and_plan.py` — 7 тестов: обе колонки, backfill `kind='package'`, `messages_count` NULL до/после, симметричный откат, сохранность строк, одна линия истории

**Изменено:**
- `app/services/payment_service.py` — `KNOWN_EVENTS`, `TERMINAL_STATUSES`, константы статусов, ветка отмены в `handle_webhook`
- `tests/test_services/test_payment_service.py` — +12 тестов (4 → 16), хелперы посева, снят лгавший тест

## Decisions Made

### Момент отмены пишется в `confirmed_at`

Колонка времени в таблице одна, и её смысл — «когда платёж перешёл в терминальное состояние». Заводить вторую колонку под отмену D-15 не велит, а расширять решение владельца этот план не вправе. Имя колонки после D-16 читается чуть шире буквального, и это выписано комментарием в коде, чтобы следующий читатель не принял запись за ошибку.

### Причина отмены не сохраняется

`cancellation_details` из тела уведомления не разбирается, в БД не пишется и не логируется (T-05-13). Ни требование, ни макет её не называют, а разбор чужой структуры ради неиспользуемого поля — лишний контракт с внешним форматом, который придётся чинить при его изменении.

### `payment.waiting_for_capture` игнорируется — и это верно именно у нас

Событие означает «деньги захолдированы, ждём подтверждения». `create_payment` создаёт платежи с `capture: True`, то есть двухстадийной оплаты в проекте не бывает, и уведомление такого рода приходить не должно. Игнорирование — не пробел, а соответствие настройке; тест на него стоит сторожем на случай, если `capture` когда-нибудь станет `False`.

### BILL-07 не отмечается выполненным

Требование о прозрачности истории закрывается экраном, который делают планы `05-04`/`05-05`. Этот план дал половину — терминальный статус в данных. Отметка «выполнено» сейчас была бы ровно тем видом неправды, против которого само требование и написано, поэтому `REQUIREMENTS.md` не трогался.

## Deviations from Plan

### 1. Предсказание `<known_test_breakage>` не сбылось — и это оказалось важнее самой поломки

План предупреждал: `test_handle_webhook_wrong_event` **сломается намеренно** после реализации D-16, красный прогон — ожидаемый шаг.

**Тест не сломался. Он продолжил проходить — по другой причине.** После GREEN-коммита задачи 1 полный прогон файла дал `13 passed`, ноль падений. Разбор: тест звал обработчик с `payment_data={"object": {"id": "yoo_789"}}`, а платежа с таким идентификатором в базе теста не было. До D-16 `False` возвращала проверка события; после D-16 — проверка «строка платежа не найдена». Утверждение `assert processed is False` осталось верным, а предмет проверки подменился молча.

Это **хуже** предсказанной поломки: красный тест зовёт разобраться, а тихо сменивший смысл — нет. Он остался бы в суите как страж проверки события, не проверяя её вовсе, и снятие всей ветки `if event not in KNOWN_EVENTS` не уронило бы ни одного теста. Именно поэтому задача 2 сняла его целиком, а не «починила»: наследник берёт СУЩЕСТВУЮЩИЙ платёж и дополнительно утверждает, что после неизвестного события его статус остался `pending` — то есть падает, если проверка события исчезнет.

### 2. Рерайт лгавшего теста разложен по двум гейтам вместо одного

План отдал рерайт задаче 2 целиком. Фактически наследник (`test_handle_webhook_ignores_an_event_it_does_not_know`, параметризован `refund.succeeded` и `payment.waiting_for_capture`) написан **RED-коммитом задачи 1**: оба этих события перечислены в `<behavior>` задачи 1, а RED требует писать тесты до реализации. Оригинал снят коммитом задачи 2. Дублирования в дереве не возникло ни на одном шаге; распределение по коммитам отличается от буквы плана, набор тестов — нет.

### 3. Упоминание старого имени убрано из докстринга ради грепа приёмки

Приёмка задачи 2 требует `grep -c 'test_handle_webhook_wrong_event' … == 0`. Первая редакция наследника называла предшественника по имени в докстринге (полезно для `git log -S`), из-за чего греп давал `1`. Формулировка переписана без литерала, с сохранением смысла; происхождение теста зафиксировано здесь — как план и предписывал («в SUMMARY зафиксировать, что тест изменён по D-16, а не подогнан под результат»). Та же форма отступления, что №3 в SUMMARY плана `05-01`.

### 4. Тест «до ревизии было иначе» добавлен сверх плана

План требовал проверить, что после `upgrade` `messages_count` принимает NULL. Добавлен парный `test_messages_count_rejects_null_before_the_upgrade`. Без него утверждение о снятии ограничения прошло бы и на схеме, где ограничения не было изначально, — то есть не доказывало бы, что ревизия что-то изменила. Формально это расширение объёма задачи 3 на один тест; по существу — половина того же утверждения (Rule 2: без неё проверка не проверяет заявленного).

---

**Total deviations:** 0 auto-fixed багов + 4 задокументированных отступления (одно из них — несбывшееся предсказание плана, разобранное выше)
**Impact on plan:** Ни одного файла вне `files_modified` плана не тронуто. Файлы соседнего плана `05-03` (`send_analytics.py`, `plan_usage.py`, `test_plan_usage.py`) не открывались.

## Issues Encountered

- **Полная суита идёт 15,5 минут** (1468 тестов). Промежуточные прогоны резались по файлам, финальный вынесен в фоновый процесс — та же проблема окружения, что отмечена в `05-01`.
- **`.venv` в worktree отсутствует**, `uv run` собрал его заново (104 пакета, 136 мс). Ни одного нового пакета не добавлено.
- **Сравнение времён из SQLite** требует приведения к aware-UTC в самих тестах: колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её naive. В файле заведён хелпер `_utc` с выписанной причиной — иначе тест падал бы TypeError только на одном из двух диалектов.

## Known Stubs

Заглушек нет. Ветка отмены подключена к настоящей строке платежа, ревизия исполняется настоящими командами Alembic на настоящем файле базы.

Границы, явно отданные соседям (не заглушки):

| Что | Кем закрывается |
|---|---|
| Экран истории платежей, где терминальный статус виден пользователю (вторая половина BILL-07) | `05-04` / `05-05` |
| Выкат `0017` на боевую базу (пятая в очереди, за необратимой `0013`) | `05-06` |
| Проверка отмены на боевом контуре ЮKassa (D9, `human_judgment`) | UAT фазы |

## Threat Flags

Новой поверхности сверх `<threat_model>` плана не появилось.

| Flag | File | Description |
|---|---|---|
| threat_flag: note | `app/services/payment_service.py` | Обработчик по-прежнему доверяет полю `object.id` тела уведомления как ключу поиска — подлинность источника держит только IP-гард плана `05-01`. Ветка отмены расширила множество исходов, которыми может распорядиться подлинный отправитель, но не добавила нового входа: неизвестный `id` возвращает `False`, известный в терминальном статусе — не меняется. |

## Next Phase Readiness

**Готово для планов `05-04` / `05-05`.** `Payment.status` теперь принимает три значения — `pending`, `succeeded`, `canceled`, — и подпись бейджа в истории платежей обязана покрывать все три. Значение `canceled` появляется только через вебхук.

**Что знать соседним планам:**
- Знакомые события живут в `KNOWN_EVENTS` (константы SDK). Добавляя третье, добавлять туда, а не литералом в условие.
- Терминальные статусы — `TERMINAL_STATUSES`. Новый терминальный исход добавляется в это множество, иначе повторный вебхук по нему запишет второй раз.
- `confirmed_at` у отменённого платежа заполнен. Формулировка на экране не имеет права называть его «дата оплаты» — это дата терминального решения.

## Self-Check: PASSED

Файлы на месте, коммиты в истории ветки:

- `5484be8` test(05-02) — RED задачи 1 (6 failed, 7 passed)
- `0ffd689` feat(05-02) — GREEN задачи 1
- `4738a09` test(05-02) — задача 2
- `aae9561` test(05-02) — задача 3

Проверки приёмки:
- `uv run pytest tests/test_services/test_payment_service.py -k "canceled or succeeded" -q` → **8 passed**, exit 0
- `uv run pytest tests/test_services/test_payment_service.py -q` → **16 passed**, exit 0
- `uv run pytest tests/test_migrations/test_0017_payment_kind_and_plan.py -q` → **7 passed**, exit 0
- `uv run pytest tests/ -q` → **1468 passed**, exit 0 (933 с)
- `grep -c 'PAYMENT_CANCELED' app/services/payment_service.py` → 2
- `grep -Ec '"payment\.(succeeded|canceled)"' app/services/payment_service.py` → **0** (имена событий не захардкожены)
- `grep -c 'test_handle_webhook_wrong_event' tests/test_services/test_payment_service.py` → **0**
- `grep -c '"head"' tests/test_migrations/test_0017_payment_kind_and_plan.py` → **0**
- `grep -c ':memory:' tests/test_migrations/test_0017_payment_kind_and_plan.py` → **0**
- Ни один тест проекта не утверждает, что отмена платежа — неизвестное событие (проверено грепом по `tests/`)

---
*Phase: 05-tarify*
*Completed: 2026-08-15*
</content>

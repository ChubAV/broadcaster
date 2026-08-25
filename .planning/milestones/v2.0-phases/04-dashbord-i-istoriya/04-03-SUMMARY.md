---
phase: 04-dashbord-i-istoriya
plan: 03
subsystem: worker
tags: [celery, redis, dispatch, retry, tdd, whatsapp, max, telegram]

# Dependency graph
requires:
  - phase: 02-obyavleniya-i-raspisaniya
    provides: "collect_due_schedules с веткой черновика и DispatchTask как формой задачи отправки"
  - phase: 03-gruppy-akkaunta
    provides: "жанр общего хелпера (group_resync) и пропуск выключенной группы в подборе расписаний"
provides:
  - "build_dispatch_task — единственное определение сборки задачи отправки на проект"
  - "Celery-таск retry_send (app.worker.tasks.retry_send) — вход повтора на все три канала"
  - "DispatchTask.schedule_id и send_message_once расширены до int | None"
affects: [04-09, 04-10, история, повтор отправки]

actuals:
  tokens: 24700
  tasks: 2
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Сборка полезной нагрузки очереди вынесена в чистый хелпер, вызываемый и планировщиком, и повтором"
    - "Повтор вливается в существующую dispatch_send_tasks, а не в вход одного канала"
    - "Тест Celery-таска захватывает корутину подменой asyncio.run и выполняет её в цикле фикстуры"

key-files:
  created: []
  modified:
    - app/application/scheduling/use_cases.py
    - app/worker/tasks.py
    - tests/test_application/test_scheduling_use_cases.py
    - tests/test_worker/test_tasks.py

key-decisions:
  - "Точка вливания повтора — dispatch_send_tasks, а не send_telegram_message: последняя есть вход одного канала из трёх, и повтор WA-записи ушёл бы по непроверенному маршруту"
  - "schedule_id проходит как None, а не подставляется нулём: колонка журнала nullable и внешним ключом не является, ноль создал бы ссылку на несуществующее расписание"
  - "Аккаунт выводится через Group.account_id — у SendLog колонки аккаунта нет"
  - "Владение записью проверяется ВНУТРИ таска повторно: аргументы приходят из брокера, а не из HTTP-запроса"
  - "max_retries=0: автоматический перезапуск превратил бы одно нажатие пользователя в серию неотзываемых отправок"

patterns-established:
  - "Сборка задачи отправки: одно определение, два вызывающих (планировщик и повтор)"
  - "Повтор не заводит второго пути отправки — переиспользует существующую диспетчеризацию целиком"
  - "Тесты маршрутизации смотрят, В КАКУЮ ОЧЕРЕДЬ легла задача, а не подменяют диспетчеризацию"

requirements-completed: [HIST-04]

coverage:
  - id: D1
    description: "build_dispatch_task — одно определение сборки задачи отправки; планировщик зовёт его и ведёт себя ровно как раньше"
    requirement: "HIST-04"
    verification:
      - kind: unit
        ref: "tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_tg_user_leaves_wa_fields_empty"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_fills_queue_fields"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_expands_images_to_urls"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_keeps_empty_images_as_is"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/ -q (1116 passed) — существующие тесты подбора расписаний как регрессия на нулевое изменение поведения"
        status: pass
    human_judgment: false
  - id: D2
    description: "retry_send ставит повтор в правильный транспорт для каждого из трёх типов аккаунта: wa/max — в Redis-очередь аккаунта, tg_user — в Celery-очередь telegram"
    requirement: "HIST-04"
    verification:
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_routes_queue_channels_to_redis"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_routes_telegram_to_celery"
        status: pass
    human_judgment: false
  - id: D3
    description: "Чужая запись, отсутствующая сущность и неактивный аккаунт останавливают повтор до диспетчеризации и не пишут в журнал"
    requirement: "HIST-04"
    verification:
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_rejects_foreign_log"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_ignores_unknown_log"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_stops_when_entity_gone"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_stops_when_account_not_active"
        status: pass
    human_judgment: false
  - id: D4
    description: "Второго пути отправки не создано: формат полезной нагрузки WA/MAX не изменён, send_message_once и адаптеры мессенджеров из таска не вызываются"
    requirement: "HIST-04"
    verification:
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_routes_queue_channels_to_redis — состав ключей payload проверяется поимённо, Celery-очередь telegram остаётся пустой"
        status: pass
      - kind: other
        ref: "grep: dispatch_send_tasks не менялась (git diff по app/worker/tasks.py — только добавление retry_send); в теле retry_send нет rpush, json.dumps и send_message_once"
        status: pass
    human_judgment: false
  - id: D5
    description: "Повтор доезжает до живого получателя: задача, положенная в Redis-очередь, реально подхватывается контейнером wa_worker/max_worker и доставляется в группу"
    requirement: "HIST-04"
    verification: []
    human_judgment: true
    rationale: "Сквозной путь пересекает границу процесса — задачу читает wa_worker/index.js в отдельном контейнере, которого в тестовой среде нет. Формат нагрузки закреплён тестом, но факт доставки проверяется только вручную на живом аккаунте. Вход пользователя в этот путь появится только с планом 04-09, поэтому проверка возможна не раньше него."

# Metrics
duration: 48 min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 03: Повтор отправки в воркере Summary

**`build_dispatch_task` как единственное определение сборки задачи отправки и Celery-таск `retry_send`, вливающий повтор в существующую `dispatch_send_tasks` — с маршрутизацией wa/max в Redis-очереди аккаунта и tg_user в Celery-очередь telegram**

## Performance

- **Duration:** 48 min
- **Started:** 2026-08-14T05:02:00Z
- **Completed:** 2026-08-14T05:50:07Z
- **Tasks:** 2 (обе TDD)
- **Files modified:** 4

## Accomplishments

- Сборка `DispatchTask` вместе с заполнением WA/MAX-полей вынесена из `collect_due_schedules` в чистый хелпер `build_dispatch_task`; заполнение полей очереди встречается в проекте ровно один раз
- Заведён Celery-таск `retry_send(log_id, user_id)`, который переиспользует существующую диспетчеризацию на все три канала и второго пути отправки не создаёт
- Точка вливания повтора смещена с `send_telegram_message` (вход одного канала) на `dispatch_send_tasks` (маршрутизация по типу аккаунта) — WA-повтор уходит `rpush`-ем в `wa:queue:{account_id}`, а не в Celery-очередь `telegram`
- `DispatchTask.schedule_id` и `send_message_once` расширены до `int | None`: повтор записи без расписания проходит без подстановки нуля
- Вторая линия защиты D-21 внутри таска: пропавшие объявление, группа или аккаунт и неактивный аккаунт останавливают повтор ДО диспетчеризации, не создавая записи в журнале

## Task Commits

Каждая задача исполнена циклом RED → GREEN:

1. **Task 1: build_dispatch_task (RED)** - `efece02` (test)
2. **Task 1: build_dispatch_task (GREEN)** - `d8ede0e` (feat)
3. **Task 2: retry_send (RED)** - `17cb8e4` (test)
4. **Task 2: retry_send (GREEN)** - `91de236` (feat)

Фазы REFACTOR не потребовалось: вынос блока в Task 1 сам по себе есть рефакторинг, выполненный под зелёными существующими тестами, а тело `retry_send` состоит из последовательности проверок без дублирования.

## Files Created/Modified

- `app/application/scheduling/use_cases.py` — добавлен `build_dispatch_task`; `collect_due_schedules` зовёт его вместо инлайн-блока; `DispatchTask.schedule_id` и `send_message_once` расширены до `int | None`
- `app/worker/tasks.py` — добавлен Celery-таск `retry_send`; импортирован `build_dispatch_task`
- `tests/test_application/test_scheduling_use_cases.py` — 12 тестов хелпера на транзиентных ORM-объектах (без движка: хелпер чистый)
- `tests/test_worker/test_tasks.py` — 10 тестов повтора, проверяющих транспорт по факту попадания задачи в очередь

## Decisions Made

- **Точка вливания — `dispatch_send_tasks`, а не `send_telegram_message`.** D-18 называл последнюю, но это вход одного канала из трёх: WhatsApp и MAX диспетчеризуются `rpush`-ем в Redis-очереди аккаунта. Повтор WA-записи через telegram-таск ушёл бы по второму, непроверенному маршруту — прямой запрет жёстких рамок milestone.
- **`schedule_id` проходит как `None`.** `send_logs.schedule_id` nullable и внешним ключом не является (ревизия `0005_sendlog_remove_fk_add_snapshots`); подстановка нуля создала бы в журнале ссылку на несуществующее расписание. В JSON-нагрузке WA/MAX ключ принимает `null`, и `wa_worker/index.js` передаёт его дальше без интерпретации.
- **Аккаунт выводится через `Group.account_id`.** У `SendLog` колонки аккаунта нет, и заводить её ради повтора не требуется.
- **Владение проверяется внутри таска повторно.** Первая проверка встанет в HTTP-обработчик плана 04-09, но аргументы таска приходят из брокера — это своя граница доверия (T-04-08).
- **Тесты не подменяют `dispatch_send_tasks`.** Подменяются Redis и Celery ПОД ней, и тест смотрит, в какую очередь легла задача. Подмена самой диспетчеризации зеленела бы и на неверном маршруте — то есть не поймала бы ровно тот дефект, ради которого сместилась точка вливания.
- **Регрессия «сборка не изменилась» — существующие тесты, а не новые.** Тесты подбора расписаний гоняют `collect_due_schedules` целиком и не переписывались; их зелёность и есть доказательство поведенческой нулевой правки.

## Deviations from Plan

None - plan executed exactly as written.

Отдельно отмечено, поскольку выглядит как отклонение, но им не является: план предписывал форму таска, скопированную с `check_schedules` (собственный engine, внутренняя `async def _run()`, запуск через `asyncio.run`, `finally: await engine.dispose()`). Форма сохранена дословно. Тестируемость обеспечена не изменением формы, а подменой `app.worker.tasks.asyncio.run` захватом корутины: тело таска выполняется в ТОМ ЖЕ цикле событий, где живёт SQLite-движок фикстуры (свой цикл оторвал бы соединение `aiosqlite`). Тем же приёмом файл уже пользуется для `asyncio.sleep` в тестах фоновой синхронизации.

**Total deviations:** 0
**Impact on plan:** нет.

## Issues Encountered

None.

## Threat Flags

Нового не найдено. Диспозиции `mitigate` из `<threat_model>` плана реализованы и закреплены тестами:

| Threat ID | Реализация | Тест |
|-----------|------------|------|
| T-04-08 | `log.user_id != user_id` → выход без диспетчеризации | `test_retry_send_rejects_foreign_log` |
| T-04-09 | задача отдаётся `dispatch_send_tasks`; `send_message_once` и адаптеры не вызываются | `test_retry_send_routes_queue_channels_to_redis` (Celery-очередь `telegram` пуста) |
| T-04-10 | таск payload не строит — передаёт `DispatchTask` в существующую диспетчеризацию | состав ключей нагрузки проверяется поимённо в том же тесте |
| T-04-11 | проверки наличия сущностей и статуса аккаунта ДО диспетчеризации | `test_retry_send_stops_when_entity_gone`, `test_retry_send_stops_when_account_not_active` (число записей журнала не растёт) |
| T-04-12 | `engine.dispose()` в `finally`, `max_retries=0` | форма закреплена grep-критерием приёмки |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `retry_send` зарегистрирован автоматически через `imports=["app.worker.tasks"]` и уезжает в очередь `default` — как `check_schedules` и обе задачи синхронизации; отдельного `task_routes`-правила не требуется.
- Вход пользователя в повтор (HTTP-обработчик, предупреждение о текущем контенте объявления по D-17) — за планом 04-09. До него таск боевым путём не вызывается.
- `HIST-04` заявлен также планами 04-01, 04-09 и 04-10 — отметка требования отложена до их завершения (shared-ID gate); `REQUIREMENTS.md` этим планом не менялся.

## Verification Results

- `uv run pytest tests/test_application/ tests/test_worker/ -q` — 136 passed, exit 0
- `uv run pytest tests/ -q` — 1116 passed, exit 0 (базовая линия до плана — 1106 passed; +22 новых теста, ни одного упавшего)
- `grep -c 'build_dispatch_task' app/application/scheduling/use_cases.py` — 2 (определение + вызов из планировщика)
- Заполнение WA/MAX-полей `DispatchTask` встречается в `app/` ровно в одном месте — внутри `build_dispatch_task`
- В теле `retry_send` нет `send_message_once(`, `rpush` и `json.dumps` — полезную нагрузку он не формирует

## Self-Check: PASSED

- Все изменённые файлы существуют на диске: `app/application/scheduling/use_cases.py`, `app/worker/tasks.py`, `tests/test_application/test_scheduling_use_cases.py`, `tests/test_worker/test_tasks.py`
- Все четыре коммита задач присутствуют в истории: `efece02`, `d8ede0e`, `17cb8e4`, `91de236`
- Критерии приёмки обеих задач перепроверены после завершения плана — все PASS
- Заглушек не обнаружено: `TODO`/`FIXME`/`placeholder` в изменённом исходном коде отсутствуют

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-14*

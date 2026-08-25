---
phase: 06-admin-panel
plan: 04
subsystem: api
tags: [incidents, sqlalchemy, pytest, tdd, admin]

requires:
  - phase: 04-dashboard
    provides: "модуль аналитики отправок — множество неуспешных статусов и приведение момента к единой зоне"
  - phase: 05-billing
    provides: "срок давности незакрытого намерения и множество терминальных статусов платежа"
provides:
  - "Пять признаков инцидента как вычисляемое состояние: подъём, снятие, вид, время последнего следа и адрес «куда чинить»"
  - "Сборка блока над базой: пять запросов независимо от числа инцидентов, порядок по свежести следа, потолок с честной пометкой"
  - "Контракт входа живости воркеров значениями (`WorkerLiveness`) — без импорта клиента брокера"
affects: [06-01-ops-state, 06-10-overview]

actuals:
  tokens: 16000
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - "Вычисляемое состояние вместо таблицы событий: условие снятия — единственный способ инциденту исчезнуть"
    - "Вход значениями вместо клиента: живость приезжает словарём, поэтому суита идёт без внешних служб"
    - "Отрицательный контроль импортов разбором дерева модуля"

key-files:
  created:
    - app/application/admin/__init__.py
    - app/application/admin/incidents.py
    - tests/test_application/test_incidents.py
    - .planning/phases/06-admin-panel/deferred-items.md
  modified:
    - .planning/phases/06-admin-panel/06-CONTEXT.md

key-decisions:
  - "D-51: порог всплеска отказов — доля за час с нижней границей объёма (60 мин / 20 отправок / 30%), цена названа величиной"
  - "Порог свежести heartbeat в модуле НЕ объявляется: живость приходит решённой (`heartbeat_fresh`), иначе здесь появился бы второй порог"
  - "Просрочка планировщика выведена из объявления его же интервала (`Settings.model_fields`), а не назначена числом"
  - "Потолок блока — 20 строк с отдельным полем `capped`; длина перечня признаком срабатывания не считается"

patterns-established:
  - "Признак = пара «условие подъёма + условие снятия», и обе стороны закреплены отдельными тестами (D-44)"
  - "Число обращений к базе фиксировано и проверяется тестом на независимость от числа найденных строк"
  - "Адрес «куда чинить» объявлен отображением вид→корень и проверяется на полноту, а не выписан в шаблоне"

requirements-completed: [ADMIN-11]

coverage:
  - id: D1
    description: "Пять признаков инцидента поднимаются своим условием и снимаются своим условием снятия, без ручного закрытия"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_a_worker_with_work_and_a_stale_heartbeat_raises_the_incident"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_a_return_to_active_clears_the_account_incident"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_a_terminal_status_clears_the_payment_incident"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_moving_the_next_run_forward_clears_the_beat_incident"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_a_ratio_falling_below_the_threshold_clears_the_spike"
        status: pass
    human_judgment: false
  - id: D2
    description: "Возраст незакрытого платежа считается от момента создания, а отбор идёт по отсутствию терминального статуса"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_a_fresh_unclosed_payment_does_not_raise_the_incident"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_application/test_incidents.py -q -k payment"
        status: pass
    human_judgment: false
  - id: D3
    description: "Нижняя граница объёма всплеска существует и не «уточняется» до нуля"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_the_same_ratio_below_the_volume_floor_does_not_raise_the_spike"
        status: pass
    human_judgment: false
  - id: D4
    description: "Время инцидента отвечает последнему НАБЛЮДЁННОМУ следу отказа, а не моменту смены статуса"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_the_account_incident_time_is_the_last_observed_disconnect_trace"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_without_a_disconnect_trace_the_account_time_is_the_last_sync"
        status: pass
    human_judgment: false
  - id: D5
    description: "Модуль проверяется на SQLite без единой внешней службы и не импортирует их клиентов"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_the_module_imports_no_client_of_an_external_service"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_every_signal_survives_the_naive_moments_sqlite_returns"
        status: pass
    human_judgment: false
  - id: D6
    description: "Сборка блока: пустота валидна, порядок по свежести следа, потолок называет себя, число запросов не растёт"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_a_healthy_service_returns_an_empty_board"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_incidents_are_ordered_by_the_freshest_trace_first"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_the_cap_truncates_and_names_itself_in_its_own_field"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_the_number_of_queries_does_not_grow_with_the_number_of_incidents"
        status: pass
    human_judgment: false
  - id: D7
    description: "Адреса «куда чинить» ведут туда, где инцидент действительно чинится (D-48)"
    requirement: ADMIN-11
    verification:
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_every_incident_carries_a_destination_declared_for_its_kind"
        status: pass
    human_judgment: true
    rationale: >-
      Тест доказывает, что адрес непуст и совпадает с объявленным корнем своего вида.
      Он НЕ доказывает, что подраздел по этому адресу существует и что администратор,
      придя туда, увидит нужный ему предмет: четыре из пяти подразделов на момент этого
      плана ещё не написаны (планы 06-05…06-10). Совпадение адреса с живым маршрутом
      судится человеком после того, как подразделы отгружены.

duration: 64 min
completed: 2026-08-22
status: complete
---

# Phase 6 Plan 04: Признаки инцидента Summary

**Пять признаков инцидента как вычисляемое из БД состояние с обязательным условием снятия: чистые функции над значениями плюс сборка пятью запросами, порядок по свежести следа, потолок с честной пометкой и адрес «куда чинить» у каждой строки.**

## Performance

- **Duration:** 64 min
- **Started:** 2026-08-22T06:38Z
- **Completed:** 2026-08-22T07:50Z
- **Tasks:** 3
- **Files modified:** 5 (4 создано, 1 изменён)

## Accomplishments

- **Решение владельца D-51 записано** с обоими числами, окном, ценой, названной величиной, и тремя отвергнутыми вариантами с причиной отказа у каждого.
- **`app/application/admin/incidents.py`** объявляет пять видов инцидента поимённо, у каждого — условие подъёма, условие снятия, адрес перехода и время последнего наблюдённого следа. Ручного закрытия нет ни в каком виде.
- **Модуль не знает ни одного клиента внешней службы.** Живость воркеров приезжает словарём значений (`WorkerLiveness`), и это держится не договорённостью, а разбором дерева модуля в суите: `grep -Ec 'redis|docker|httpx'` равно нулю, и тест краснеет в момент добавления импорта.
- **Числа взяты, а не назначены.** Срок давности незакрытого платежа и множество терминальных статусов — у платёжного сервиса; множество неуспешных статусов отправки — у модуля аналитики; просрочка планировщика выведена из объявления его же интервала.
- **Сборка блока готова к показу:** пять запросов независимо от числа инцидентов, порядок по убыванию времени следа, потолок 20 строк с отдельным полем `capped`, пустой перечень как валидный ответ здорового сервиса.
- **28 тестов** на файл (при требовании плана — не менее восемнадцати), все зелёные.

## Task Commits

1. **Задача 1: решение владельца о пороге всплеска отказов** — `d3240e1` (docs)
2. **Задача 2: пять признаков — подъём, снятие, вид и время следа** — `fee5dba` (test, RED) → `9e7f3f2` (feat, GREEN) → `0ba86d3` (refactor)
3. **Задача 3: сборка блока — порядок, потолок, пустота, адреса** — `f5d2f01` (test, RED) → `a2876d0` (feat, GREEN)

Дополнительно: `92e3f8d` (docs) — запись предсуществующего красного теста в реестр отложенного.

## Files Created/Modified

- `app/application/admin/incidents.py` — пять признаков, их условия снятия, виды, адреса, время следа и сборка над базой (602 строки)
- `app/application/admin/__init__.py` — пакет прикладной логики админки (пуст, по образцу пакета аналитики)
- `tests/test_application/test_incidents.py` — 28 тестов: подъём и снятие каждого признака, возраст платежа от правильной колонки, время следа, переносимость арифметики над временем, отрицательный контроль импортов, сборка блока
- `.planning/phases/06-admin-panel/06-CONTEXT.md` — решение D-51
- `.planning/phases/06-admin-panel/deferred-items.md` — заведён; описан предсуществующий красный тест вне предмета плана

## Decisions Made

- **D-51 (решение владельца):** вариант A — доля за час с нижней границей объёма. `FAILURE_SPIKE_WINDOW_MIN = 60`, `FAILURE_SPIKE_MIN_TOTAL = 20`, `FAILURE_SPIKE_RATIO = 0.30`. Причина существования нижней границы выписана комментарием рядом с константой и закреплена отдельным тестом: правка, «уточняющая» её до нуля, краснит прогон, а не возвращает вечный горящий инцидент молча.
- **Порог свежести heartbeat в этом модуле НЕ объявлен.** Живость приходит уже решённой (`heartbeat_fresh: bool`), а не сырым возрастом. Иначе здесь появился бы второй порог свежести рядом с тем, что объявлен там, где heartbeat читается, — и разошёлся бы с ним молча. Побочно это единственный способ не импортировать модуль, тянущий клиент Docker.
- **Просрочка планировщика выведена из объявления настройки** (`Settings.model_fields["celery_beat_interval"].default`), а не из живого экземпляра настроек: создание экземпляра требует окружения (адрес базы и ключ подписи обязательны), а модуль обязан импортироваться и проверяться без окружения вовсе. Развёртывание, поднявшее интервал переменной среды, передаёт его аргументом `beat_interval_sec`.
- **След отвала аккаунта ищется по паре «владелец и канал».** Журнал отправок хранит владельца и канал, но не аккаунт; это самая узкая связь, которую даёт схема, и заводить ради подписи колонку значило бы заводить миграцию (D-47 прямо это запрещает).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Убран помощник, обрезавший таймзону у границы окна**

- **Found during:** Задача 3 (чтение образца «восемь чисел одним round-trip» перед сборкой)
- **Issue:** Реализация задачи 2 проводила границы окон через собственный помощник `_as_column_moment`, обрезавший таймзону «ради SQLite». Прогон-зонд показал, что SQLite сравнивает aware-границу верно и БЕЗ обрезки (модуль аналитики так и делает), а на боевом драйвере naive-момент против колонки с зоной поднял бы ошибку. То есть помощник чинил несуществующее и ломал настоящее — ровно тот класс дефекта, против которого написан Pitfall 1, только с обратным знаком.
- **Fix:** Помощник удалён, границы окон уходят в запрос aware — как в модуле аналитики.
- **Files modified:** `app/application/admin/incidents.py`
- **Verification:** `uv run pytest tests/test_application/test_incidents.py -q` — 22 зелёных на момент правки
- **Committed in:** `0ba86d3`

**2. [Rule 1 - Bug] Комментарий утверждал о `max()` то, чего прогон не показал**

- **Found during:** Задача 3 (тот же зонд)
- **Issue:** `_parse_moment` разбирал строку и объяснял это тем, что «`max()` на SQLite возвращает СТРОКУ». Прогон показал обратное: возвращается `datetime`. Объявление, утверждающее то, чего код рядом с ним не делает, — это класс дефекта, за который проект получил три раунда верификации подряд и завёл машинный гейт (`tests/test_application/test_declared_invariants.py`).
- **Fix:** Ветка разбора строки убрана, комментарий приведён к тому, что проверено прогоном: тип сохраняется, зона — нет, поэтому приведение обязательно.
- **Files modified:** `app/application/admin/incidents.py`
- **Verification:** тот же прогон, зелёный
- **Committed in:** `0ba86d3`

---

**Total deviations:** 2 auto-fixed (обе — Rule 1, дефект)
**Impact on plan:** Обе правки внутри предмета задачи и уменьшают код, а не расширяют его. Первая снимает отказ, который случился бы только на боевом драйвере, то есть у пользователя, а не в суите.

## Issues Encountered

**`just test` не зелёный: один предсуществующий красный тест вне предмета плана.**

`tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` падает в общем прогоне (1 failed, 1787 passed) и проходит в одиночку и целым файлом.

Причастность плана ПРОВЕРЕНА, а не предположена: контрольный прогон того же среза с `--ignore=tests/test_application/test_incidents.py` даёт тот же красный тест (1 failed, 1085 passed). Падение воспроизводится без единой строки, написанной этим планом.

Не чинится здесь по границе предмета: план не трогает ни рендер, ни настройки S3. Записано в `.planning/phases/06-admin-panel/deferred-items.md` и в реестр `.planning/WINDOWS.md` (запись 1, статус open) — чтобы к моменту отгрузки фазы это не потерялось.

Остальные три команды `<verification>` плана зелёные:
- `uv run pytest tests/test_application/test_incidents.py -q` — 28 passed
- `uv run pytest tests/test_application/test_incidents.py -q -k payment` — 3 passed
- `uv run pytest tests/test_application -q` — 219 passed

## Known Stubs

Нет. Заглушек, пропущенных тестов и незапущенных проверок план не оставил.

## TDD Gate Compliance

Обе задачи с `tdd="true"` прошли последовательность гейтов:

| Задача | RED | GREEN | REFACTOR |
|--------|-----|-------|----------|
| 2 | `fee5dba` | `9e7f3f2` | `0ba86d3` |
| 3 | `f5d2f01` | `a2876d0` | — (правок не потребовалось) |

RED каждый раз подтверждён прогоном: первый — `ModuleNotFoundError` на несуществующем модуле, второй — ошибка сборки на несуществующих `INCIDENT_LIST_CAP` / `INCIDENT_DESTINATIONS`.

## User Setup Required

None — внешних служб план не касается, установок пакетов нет.

## Next Phase Readiness

- Модуль готов к потреблению планом 06-10 («Обзор»): `collect_incidents(session, liveness, now=…, beat_interval_sec=…)` возвращает `IncidentBoard` с готовым к показу перечнем и полем `capped`.
- **Стык с планом 06-01 (сервис оперативного состояния) требует внимания при слиянии:** этот модуль ждёт на входе `Mapping[int, WorkerLiveness]`, где `heartbeat_fresh` уже решён, а `queue_depth` — число. Если сервис оперативного состояния отдаёт другую форму, переходник пишется на стороне потребителя (06-10), а не внутри модуля признаков: импорт сервиса сюда вернул бы зависимость суиты от поднятого стенда.
- Адреса «куда чинить» ведут в подразделы, четыре из пяти которых ещё не написаны. Совпадение адреса с живым маршрутом проверяется человеком после отгрузки подразделов (coverage D7).

## Self-Check: PASSED

- `app/application/admin/incidents.py` — FOUND
- `app/application/admin/__init__.py` — FOUND
- `tests/test_application/test_incidents.py` — FOUND
- `.planning/phases/06-admin-panel/deferred-items.md` — FOUND
- Коммиты `d3240e1`, `fee5dba`, `9e7f3f2`, `0ba86d3`, `f5d2f01`, `a2876d0`, `92e3f8d` — FOUND
- Критерии приёмки задач 2 и 3 перепрогнаны: `INCIDENT_KIND_` — 10 строк (≥5), `redis|docker|httpx` — 0, `confirmed_at` — 0, `normalize_utc` — 11 строк (≥4), `PENDING_INTENT_TTL_HOURS` / `TERMINAL_STATUSES` / `FAILED_STATUSES` / `capped` — найдены

---
*Phase: 06-admin-panel*
*Completed: 2026-08-22*

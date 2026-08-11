---
phase: 02-obyavleniya-i-raspisaniya
plan: 14
subsystem: api
tags: [fastapi, pydantic, jinja2, sqlalchemy, json-column]

requires:
  - phase: 02-obyavleniya-i-raspisaniya (plan 02-09)
    provides: "ужесточение update_schedule — get_for_user, owned_group_ids, единое определение полноты"
provides:
  - "reject_explicit_null: 422 на явный null в group_ids/days_of_week/times_of_day/timezone до какой-либо записи в модель (CR-03, главная линия)"
  - "Вторая линия в разметке: (s.days_of_week or []) / (s.times_of_day or []) в schedule_row.html и sched_card.html — испорченная до фикса строка не выключает экраны владельца"
  - "Регрессии: tests/test_routes/test_schedules_api_null.py, tests/test_pages/test_schedules_poisoned_row.py"
affects: [02-verification, schedules, ads-editor]

actuals:
  tokens: 5519
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "field_validator на нескольких полях Optional-схемы патча: None внутри валидатора означает присланный null (валидаторы не запускаются на значениях по умолчанию) — отказ на нечитаемый вход без сужения exclude_unset-контракта"
    - "Тотальность рендера по данным базы: членство и итерация в шаблонах только по подстрахованным спискам (or [])"

key-files:
  created:
    - tests/test_routes/test_schedules_api_null.py
    - tests/test_pages/test_schedules_poisoned_row.py
  modified:
    - app/routes/schedules.py
    - app/templates/schedules/includes/schedule_row.html
    - app/templates/ads/includes/sched_card.html

key-decisions:
  - "Отказ на явный null реализован schema-уровнем (field_validator → 422 силами FastAPI), тем же классом отказа, что существующий validate_timezone — состав маршрутов и контракт JSON-API не изменены (D-15)"
  - "Страничная регрессия редактора идёт на РАЗВЁРНУТУЮ карточку (?sched={id}) — адрес, на который ведёт действие сводного списка: свёрнутый рендер не покрывает итерацию времён (:181) и дней (:171)"

patterns-established:
  - "reject_explicit_null: общий валидатор четырёх полей patch-схемы — образец для других Optional-патчей с JSON-колонками"

requirements-completed: [ADS-07, SCH-04, SCH-05]

coverage:
  - id: D1
    description: "PUT /api/schedules/{id} с явным null в любом из четырёх полей → 422, строка не изменена, GET /api/schedules после отказа — 200; валидный частичный патч работает как прежде"
    requirement: ADS-07
    verification:
      - kind: unit
        ref: "tests/test_routes/test_schedules_api_null.py#test_explicit_null_is_rejected_before_any_write[group_ids|days_of_week|times_of_day|timezone]"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_schedules_api_null.py#test_valid_partial_patch_still_updates_exactly_that_field"
        status: pass
    human_judgment: false
  - id: D2
    description: "GET /schedules и GET /ads/{id}/edit?sched={id} отвечают 200 при строке с None в days_of_week/times_of_day/group_ids — оба экрана владельца живы (вторая линия)"
    requirement: SCH-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_poisoned_row.py#test_poisoned_paused_row_keeps_both_owner_screens_alive[days_of_week|times_of_day|group_ids]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Тумблер испорченной строки размечен как у неполного расписания: на паузе заблокирован с подсказкой, у активной пауза доступна (SCH-05, D-08)"
    requirement: SCH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_poisoned_row.py#test_poisoned_paused_row_keeps_both_owner_screens_alive (маркеры schedule-toggle-{id} disabled + подсказка)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_poisoned_row.py#test_poisoned_active_row_keeps_the_pause_available"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-08-11
status: complete
---

# Phase 02 Plan 14: Явный null в патче расписания Summary

**Закрыт CR-03 двумя линиями: field_validator `reject_explicit_null` отвергает явный null во всех четырёх полях UpdateScheduleRequest с 422 до первого setattr, а четыре подстраховки `or []` в schedule_row.html и sched_card.html держат оба экрана владельца живыми на строках, испорченных до фикса.**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-08-11T10:45:14Z
- **Completed:** 2026-08-11T10:56:00Z
- **Tasks:** 2 (TDD: RED → GREEN)
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments

- **RED (воспроизведённые 500):** 7 из 9 новых тестов красные по причине дефекта — `PUT {"<field>": null}` давал 500 (ResponseValidationError) и коммитил порчу для group_ids/days_of_week/times_of_day (timezone падал в compute_next_run_at до коммита); `GET /schedules` падал TypeError в schedule_row.html:108 (`d in None`), развёрнутый редактор — в sched_card.html:66/171/181.
- **GREEN (валидатор + четыре места разметки):** `reject_explicit_null` на `@field_validator("group_ids", "days_of_week", "times_of_day", "timezone")` — ValueError при `v is None` → 422 силами FastAPI до какой-либо записи; разметка: `d in (s.days_of_week or [])` (schedule_row:108), `(s.days_of_week or [])|sort` (sched_card:66), `d in (s.days_of_week or [])` (sched_card:171), `for t in (s.times_of_day or [])` (sched_card:181).
- Контракт частичного патча (D-15) не сужен: валидаторы pydantic не запускаются на значениях по умолчанию, отсутствующий ключ по-прежнему означает «не трогать» — контрольный тест и все регрессии 02-09 зелёные.
- Тумблер испорченной строки утверждён явными маркерами: на паузе `id="schedule-toggle-{id}" value="1" disabled>` с подсказкой «Возобновить нельзя: расписание не заполнено», у активной — `value="1" checked>` (SCH-05, D-08).
- Соседние контракты не задеты: 111 тестов зелёные (test_schedules_api_null, test_schedules_poisoned_row, test_schedules_api_ownership, test_schedules_list, test_schedule_ownership, test_ads_editor).

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): регрессии явного null и испорченной строки** - `1cfa111` (test)
2. **Task 2 (GREEN): отказ 422 и вторая линия в разметке** - `c89bc37` (feat)

## Files Created/Modified

- `app/routes/schedules.py` - валидатор `reject_explicit_null` в UpdateScheduleRequest (главная линия CR-03)
- `app/templates/schedules/includes/schedule_row.html` - защита сетки дней от None (:108, вторая линия)
- `app/templates/ads/includes/sched_card.html` - защита сортировки дней (:66), чекбоксов дней (:171) и итерации времён (:181)
- `tests/test_routes/test_schedules_api_null.py` - параметризованная регрессия null по четырём полям + контроль валидного патча
- `tests/test_pages/test_schedules_poisoned_row.py` - регрессия страничного слоя: оба экрана 200, маркеры тумблера по SCH-05/D-08

## Decisions Made

- Редактор в страничной регрессии запрашивается с развёрнутой карточкой (`/ads/{ad_id}/edit?sched={id}`) — это адрес действия «Открыть объявление» из сводного списка, то есть настоящий путь восстановления; свёрнутый рендер не исполняет :171/:181 и не воспроизводил дефект для times_of_day.
- CreateScheduleRequest не тронут: его поля не Optional, null там и так 422 (по плану).

## TDD Gate Compliance

- RED gate: `1cfa111` `test(02-14): ...` — 7 failed / 2 passed, красные по причине воспроизведённого дефекта (500/TypeError), не ошибок засева.
- GREEN gate: `c89bc37` `feat(02-14): ...` — все 9 тестов задачи 1 плюс 102 соседних зелёные.
- Порядок гейтов верифицирован: `git log --grep="02-14"` — test предшествует feat.

## Deviations from Plan

**1. [Уточнение RED] Страничная регрессия редактора направлена на развёрнутую карточку**
- **Found during:** Task 1 (прогон красного гейта)
- **Issue:** План формулировал `GET /ads/{ad_id}/edit`; свёрнутый рендер карточки не исполняет sched_card.html:171/:181, и случай times_of_day=None оставался зелёным до фикса — красный гейт не воспроизводил дефект.
- **Fix:** Запрос редактора идёт с `?sched={id}` (развёрнутая карточка) — тот же адрес, что у действия сводного списка; times_of_day стал красным, регрессия строже.
- **Files modified:** tests/test_pages/test_schedules_poisoned_row.py
- **Verification:** до фикса 7 красных, после — все зелёные
- **Committed in:** `1cfa111`

**2. [Ожидаемая зелень на RED] Случай group_ids=None на страницах зелёный до фикса**
- **Found during:** Task 1 (прогон красного гейта)
- **Issue:** План ожидал «все новые тесты красные»; расследование (по правилу fail-fast TDD) показало: разметка уже защищает group_ids везде — `chosen = s.group_ids or []` (sched_card:65, план сам называет его образцом формы защиты) и истинностные проверки в schedule_row.
- **Fix:** Тест оставлен как регрессия, закрепляющая существующую вторую линию для этого поля; красный гейт несут остальные 7 тестов (в т.ч. group_ids на API-слое — 500 на PUT и на чтении списка).
- **Files modified:** нет (изменений кода не потребовалось)
- **Verification:** API-случай group_ids красный до фикса, зелёный после
- **Committed in:** `1cfa111`

---

**Total deviations:** 2 (оба — уточнения красного гейта в тестах, кода приложения не касались)
**Impact on plan:** Ноль scope creep; регрессия стала строже задуманной (развёрнутая карточка), контракты не изменены.

## Issues Encountered

None — план исполнен по написанному; middleware проекта превращает исключения шаблонов в 500-ответы, поэтому красные тесты падали на статус-ассертах, как и описано в плане.

## Threat Model Disposition

- T-02-14-01 (Tampering/DoS, high, mitigate) — закрыт: `reject_explicit_null` стоит до какой-либо записи в модель.
- T-02-14-02 (DoS, medium, mitigate) — закрыт: четыре подстраховки `or []` в двух шаблонах.
- T-02-14-03 (Elevation, low, accept) — владение записью и группами (02-09) не изменено; регрессии владения в прогоне зелёные.

Нового security-поверхностного кода нет — новых маршрутов, моделей и миграций план не создаёт.

## Known Stubs

None — заглушек, плейсхолдеров и пропущенных тестов нет.

## Next Phase Readiness

- CR-03 закрыт в ширине, установленной верификатором: ни один вход не порождает нечитаемую запись, существующие испорченные строки не выключают экраны.
- Named-известные WR-09 (`times_of_day: ["nope"]` на JSON-входе → 500) и WR-10 (POST создаёт активное незаполненное) остаются вне этого плана — следующий цикл верификации.

## Self-Check: PASSED

- Файлы: tests/test_routes/test_schedules_api_null.py, tests/test_pages/test_schedules_poisoned_row.py, 02-14-SUMMARY.md — FOUND
- Коммиты: 1cfa111 (test), c89bc37 (feat) — FOUND
- Прогон: 111 passed (новые регрессии + соседние контракты 02-09, список, владение, редактор)

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-11*

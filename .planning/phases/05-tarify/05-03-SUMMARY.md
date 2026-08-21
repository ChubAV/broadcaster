---
phase: 05-tarify
plan: 03
subsystem: billing
tags: [billing, plan-limits, analytics, sqlalchemy, timezone, calendar]

# Dependency graph
requires:
  - phase: 04-dashbord-i-istoriya
    provides: "app/application/analytics/send_analytics.py — модуль-владелец журнала отправок (D-35), normalize_utc, составной индекс (user_id, sent_at) ревизии 0016"
  - phase: 01-interfeysnyy-fundament
    provides: "get_shell_context — nav_counts.ads / nav_counts.accounts, числители двух осей"
  - phase: 05-tarify
    plan: 01
    provides: "app/application/billing/ как пакет, Settings.parsed_plan_limits — знаменатели четырёх осей"
provides:
  - "app/application/billing/plan_usage.py — plan_axes: четыре оси тарифа числами (BILL-06)"
  - "PlanAxis / AXIS_ORDER / AXIS_LABELS — контракт осей для разметки плана 05-05"
  - "axis_percent — единственное место, где считается процент оси (безлимит и ноль дают 0)"
  - "send_analytics.current_month_bounds_utc — календарный месяц читателя в UTC"
  - "send_analytics.sends_in_current_month / sends_in_current_month_query — счёт отправок за месяц запросом и подзапросом"
affects: [05-05, 05-06, 06-admin]

actuals:
  tokens: 11800
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Предикат окна определён ОДИН раз, а исполняется двумя способами: builder запроса + async-обёртка над ним"
    - "Числители, уже посчитанные шеллом, не пересчитываются вторым запросом"
    - "Календарные границы считаются в Python, в базу уходит обычное сравнение"
    - "Безлимит — None; ноль остаётся валидным нулевым лимитом"

key-files:
  created:
    - app/application/billing/plan_usage.py
    - tests/test_application/test_plan_usage.py
  modified:
    - app/application/analytics/send_analytics.py

key-decisions:
  - "Ось отправок берёт у модуля аналитики ЗАПРОС (sends_in_current_month_query), а не результат: иначе один round-trip и «звать модуль аналитики» противоречат друг другу"
  - "plan_axes принимает `user` (нужен ради таймзоны), владение уходит в запрос предикатом user_id == user.id"
  - "Отсутствующий ключ в limits читается как безлимит, а не как падение: перечень тарифов правится через окружение"
  - "Обоснование «модуль не читает объект HTTP-запроса» выписано БЕЗ имени типа — границу держит греп приёмки по сырому тексту"

patterns-established:
  - "Тест-сторож границ модуля по сырому тексту: диалектная календарная группировка + путь записи + знание про HTTP"
  - "Регрессия счётчика запросов ловит не изменение чисел, а появление второго источника одного числа"

requirements-completed: [BILL-06]

coverage:
  - id: D1
    description: "Календарный месяц пользователя: границы в его зоне, декабрь, високосный февраль, битая строка зоны, naive `now`"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py — 6 тестов current_month_bounds_utc"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ось «Отправок в месяц» считает все статусы (D-25), режет соседние месяцы строгой верхней границей и не видит чужих отправок"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py — 5 тестов sends_in_current_month"
        status: pass
    human_judgment: false
  - id: D3
    description: "Четыре оси в порядке макета (D-09); «Объявления» и «Аккаунты» равны счётчикам шелла, включая черновики (D-23) и отключённые сессии"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py#test_plan_axes_returns_four_axes_in_the_layout_order, #test_plan_axes_ads_axis_equals_the_shell_counter_including_drafts, #test_plan_axes_accounts_axis_counts_created_accounts_not_online_ones"
        status: pass
    human_judgment: false
  - id: D4
    description: "Безлимит (None), нулевой лимит и превышение не роняют счёт и не блокируют ничего (D-08)"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py#test_plan_axes_unlimited_axis_reports_none_and_zero_percent, #test_plan_axes_zero_limit_does_not_divide_by_zero, #test_plan_axes_over_the_limit_is_not_an_error, #test_plan_usage_module_writes_nothing_and_knows_nothing_about_http"
        status: pass
    human_judgment: false
  - id: D5
    description: "Один round-trip на четыре оси; изоляция по владельцу; граница месяца в зоне читателя через plan_axes"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py#test_plan_axes_takes_exactly_one_query, #test_plan_axes_isolates_every_axis_from_another_user, #test_plan_axes_month_boundary_uses_the_users_timezone"
        status: pass
    human_judgment: false
  - id: D6
    description: "Переносимость: ни одной календарной группировки средствами диалекта ни в модуле осей, ни в модуле аналитики после правки"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_plan_usage.py#test_plan_usage_module_has_no_dialect_specific_calendar_functions; tests/test_application/test_send_analytics.py#test_module_has_no_dialect_specific_calendar_functions"
        status: pass
    human_judgment: false
  - id: D7
    description: "Оси, посчитанные на боевом PostgreSQL, совпадают с посчитанными на SQLite тестов"
    requirement: BILL-06
    verification: []
    human_judgment: true
    rationale: "Суита идёт на SQLite; PostgreSQL-прогон в проекте не автоматизирован. Риск снижен по построению — календарной арифметики средствами диалекта нет ни строки, в базу уходит только сравнение `sent_at` с посчитанными в Python границами, и это закреплено тест-сторожами обоих модулей."

duration: 45min
completed: 2026-08-15
status: complete
---

# Phase 05 Plan 03: Модуль четырёх осей тарифа Summary

**Четыре оси тарифа — Объявления, Группы, Отправок в месяц, Аккаунты — впервые считаются числами: календарный месяц режется в зоне читателя, безлимит кодируется `None`, превышение показывается честно, и все четыре оси стоят ровно один round-trip.**

## Performance

- **Duration:** ~45 мин (из них 16 мин — финальный прогон полной суиты)
- **Tasks:** 3
- **Files modified:** 3 (2 создано, 1 изменено)
- **Tests added:** 25 (суита выросла с 1449 до 1474)

## Accomplishments

- **«Лимит тарифа» стал наблюдаемой величиной.** До этого плана тарифных лимитов в коде проекта не существовало вовсе: единственный лимит (`app/services/billing_cache.py`) разрешает всё, кроме `send`, а неподключённый `billing/plans.html` знал три оси и брал их из переменных, которых нет ни в одном контексте.
- **Календарный месяц читателя появился в модуле-владельце журнала.** `send_metrics` умел только скользящее окно, `history_count` — только `today`/`7d`/`30d`. Теперь окно календарного месяца в зоне пользователя (D-11) живёт рядом с остальными запросами к `send_logs`, а не в новом разделе своим запросом (D-35).
- **Оси не могут разойтись со счётчиками рядом.** «Объявления» и «Аккаунты» берутся из `nav_counts` того же запроса шелла — второго источника этих чисел не заведено, и регрессия счётчика запросов ловит будущую попытку его завести.
- **Гейтов не появилось ни одного.** Ни один боевой путь создания объявления, группы, аккаунта или отправки не тронут: модуль не имеет пути записи, и это проверяется грепом по сырому тексту.

## Task Commits

1. **Task 1: Календарный месяц в таймзоне пользователя** — `eb5fa5e` (test, RED) → `f9e1e71` (feat, GREEN)
2. **Task 2: Модуль четырёх осей тарифа** — `b7a5acc` (test, RED) → `a041f00` (feat, GREEN)
3. **Task 3: Регрессии владения, экономии запросов и границы месяца** — `aba786e` (test)

_TDD-гейты соблюдены обеими задачами, производящими поведение: каждый `feat` предваряется `test`-коммитом, красным на своём дереве (задача 1 — `ImportError` на `current_month_bounds_utc`, задача 2 — `ModuleNotFoundError` на `plan_usage`). Задача 3 поведения не добавляет — она целиком тестовая, и `feat`-половины у неё нет по построению._

## Files Created/Modified

**Создано:**
- `app/application/billing/plan_usage.py` — `PlanAxis`, `AXIS_*` константы, `axis_percent`, `plan_axes`
- `tests/test_application/test_plan_usage.py` — 25 тестов: границы месяца, счёт отправок, четыре оси, безлимит/ноль/превышение, один запрос, изоляция по владельцу, два сторожа границ модуля

**Изменено:**
- `app/application/analytics/send_analytics.py` — `import calendar`, `current_month_bounds_utc`, `sends_in_current_month_query`, `sends_in_current_month` (правка чисто аддитивная: ни одна существующая функция не тронута)

## Decisions Made

### Ось отправок берёт ЗАПРОС, а не результат

План требует двух вещей одновременно: ось отправок обязана идти через модуль аналитики (D-35), а `plan_axes` обязана укладываться в **один** round-trip. Асинхронная функция, исполняющая свой запрос, даёт второй round-trip и делает требования взаимоисключающими.

Развязка: модуль аналитики отдаёт **builder** — `sends_in_current_month_query(user, *, user_id, now)` возвращает `Select`, не исполняя его. Экран тарифов вкладывает его скалярным подзапросом в общий запрос осей (один round-trip), а любой одиночный вызывающий берёт `sends_in_current_month`, которая тот же builder исполняет. Определение предиката остаётся ОДНО — ровно то, что обещает D-35 («одно определение предиката, а не одно физическое чтение», формулировка `get_shell_context`). Тест `test_plan_axes_sends_axis_counts_the_current_calendar_month` сверяет оба пути на одних данных.

### `plan_axes` принимает `user`, а владение уходит предикатом

Сигнатура плана — `plan_axes(db, *, user, limits, nav_counts, now=None)`, а `<threat_model>` описывает владельца как именованный `user_id`. Оба выполнены: `user` нужен ради таймзоны окна (без него календарный месяц не посчитать), а в запрос уходит `Group.user_id == user.id` и `SendLog.user_id == user.id`. Ветки «по всем пользователям» в модуле нет.

### Отсутствующий ключ лимитов — безлимит, а не падение

`limits.get(key, None)`. Перечень тарифов правится переменной окружения `PLAN_LIMITS`, и опечатка в ней обязана стоить одной ненарисованной шкалы, а не пятисотки на странице тарифов. Закреплено тестом `test_plan_axes_tolerates_a_plan_without_an_axis_key`.

## Deviations from Plan

### Auto-fixed Issues

Автоправок не потребовалось: дефектов, попадающих под правила 1-3, в затронутом коде не встретилось.

### Отступления от буквы плана

**1. Ось отправок подключена через builder запроса, а не через `async def sends_in_current_month`**

План (задача 2) пишет: «Отправки берутся `sends_in_current_month` из модуля аналитики (задача 1), а не собственным запросом к `send_logs`» — и одновременно требует одного round-trip и скалярных подзапросов. Буквальное исполнение первой фразы делает вторую невыполнимой. Обе функции существуют и обе покрыты тестами; `plan_usage.py` импортирует `sends_in_current_month_query`. Приёмочный греп плана (`содержит sends_in_current_month`) выполняется — имя builder'а его содержит, — и, что важнее, выполняется его смысл: собственного обращения к `send_logs` в модуле осей нет.

**2. Формулировка одного докстринга подогнана под греп приёмки**

Приёмка требует `grep -Ec '\bRequest\b|request\.' app/application/billing/plan_usage.py == 0`, а перечень границ модуля обязан сказать, что модуль не читает объект HTTP-запроса. Обоснование переписано без имени типа, с сохранением смысла и с прямой оговоркой, ПОЧЕМУ имя не названо, — чтобы следующий читатель не «починил» формулировку обратно. Тот же приём применён планом 05-01 к `subscription_period.py`. Импорта FastAPI в модуле нет.

**3. Тест-сторож диалектных имён заведён в задаче 2, а не в задаче 3**

План называет его в обеих задачах (задача 2: «Завести в новом тестовом файле тест-сторож…», задача 3: «Плюс тест-сторож…»). Заведён один раз, вместе с модулем, который он сторожит.

---

**Total deviations:** 0 auto-fixed + 3 задокументированных отступления от буквы плана
**Impact on plan:** Все `must_haves.truths` и оба приёмочных списка выполнены. Ни одного файла вне `files_modified` плана не тронуто; файлы плана 05-02 (`payment_service.py` и его тесты, тест ревизии 0017) не открывались.

## Issues Encountered

- **Полная суита идёт ~16 минут** (1474 теста). Промежуточные прогоны резались по файлам, финальный вынесен в фоновый процесс. Проблема сборки окружения, не кода.
- **Сторож границ модуля снимает только строчные комментарии, но не докстринги.** Первая редакция `plan_usage.py` падала на собственном обосновании — см. отступление №2. Это не дефект сторожа: сторож обязан читать сырой текст, иначе запрет обходится переносом кода в строку документации.

## Known Stubs

Заглушек нет. Все четыре оси подключены к настоящим источникам: два числителя — к счётчикам шелла, два — к запросу по `groups` и `send_logs`, знаменатели приходят готовым отображением из `Settings.parsed_plan_limits`.

Названные границы, отданные соседним планам (не заглушки):

| Что | Кем закрывается |
|---|---|
| Вызов `plan_axes` из страничного маршрута и передача `nav_counts` из `request.state.shell` | `05-05` |
| Разметка карточек тарифов и метров осей | `05-05` |
| Применение лимитов (гейты на создание) — долг BILL-02, фазой не закрывается (D-08/D-13) | отдельная работа |

## Threat Flags

Новой поверхности сверх `<threat_model>` плана не появилось. Обе `mitigate`-диспозиции, адресованные этому плану, реализованы: T-05-16 (изоляция по владельцу — предикат запроса плюс именованный тест), T-05-17 (`nav_counts` — обязательный именованный аргумент, модуль не знает про HTTP), T-05-19 (пути записи нет, D-08 выписан в докстринге как названная граница).

## Next Phase Readiness

**Готово к плану 05-05 (разметка раздела).** Контракт, на который он опирается:

- `plan_axes(db, *, user, limits, nav_counts, now=None) -> list[PlanAxis]`; `PlanAxis` = `key`, `label`, `used`, `limit` (`int | None`), `percent` (`int`, уже клампован в 0..100).
- Порядок осей — `AXIS_ORDER`; подписи — `AXIS_LABELS` (второй копии подписей в разметке заводить нельзя).
- `limits` — запись тарифа из `Settings.parsed_plan_limits`, `nav_counts` — из `request.state.shell["nav_counts"]`. Передавать `nav_counts` из тела запроса нельзя: это T-05-17.
- Безлимит приезжает `limit is None` — разметка обязана рисовать «без ограничений», а не «0».

## Self-Check: PASSED

Файлы на месте:
- `app/application/billing/plan_usage.py` — FOUND
- `app/application/analytics/send_analytics.py` — FOUND
- `tests/test_application/test_plan_usage.py` — FOUND

Коммиты в истории ветки: `eb5fa5e`, `f9e1e71`, `b7a5acc`, `a041f00`, `aba786e` — все FOUND.

Проверки приёмки:
- `uv run pytest tests/ -q` → **1474 passed, exit code 0** (956 с)
- `uv run pytest tests/test_application/test_plan_usage.py -q` → 25 passed
- `uv run pytest tests/test_application/test_send_analytics.py -q` → 60 passed (сторож диалектных имён зелёный после правки модуля)
- `grep -Ec 'func\.(strftime|date_trunc|extract|to_char|julianday)' app/application/billing/plan_usage.py` → 0
- `grep -Ec '(db|session)\.(add|commit|flush)\(' app/application/billing/plan_usage.py` → 0
- `grep -Ec '\bRequest\b|request\.' app/application/billing/plan_usage.py` → 0
- `grep -c 'accounts_online' app/application/billing/plan_usage.py` → 0
- `grep -c 'sends_in_current_month' app/application/billing/plan_usage.py` → 3
- `send_analytics.py` содержит `def current_month_bounds_utc(`, `async def sends_in_current_month(`, `calendar.monthrange`
- В диффе плана нет ни одного удаления файла

---
*Phase: 05-tarify*
*Completed: 2026-08-15*

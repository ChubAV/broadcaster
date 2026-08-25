---
phase: 04-dashbord-i-istoriya
plan: 01
subsystem: analytics
tags: [sqlalchemy, fastapi, jinja2, aggregation, dashboard, history, timezone]

requires:
  - phase: 01-interfejsnyj-fundament
    provides: "компоненты card/mono, примитивы [data-metrics]/[data-metric-value], шелл base.html с <div data-body>"
  - phase: 03-gruppy-akkaunta
    provides: "форма модуля слоя application (app/application/accounts/group_resync.py) — докстринг-контракт и раздел «чего модуль не делает»"
provides:
  - "app/application/analytics/send_analytics.py — публичный контракт аналитики отправок для дашборда, истории и Фазы 6 (D-35)"
  - "send_metrics: восемь чисел плиток одним round-trip, скользящее окно суток с дельтой к предыдущим суткам"
  - "Константы статусов журнала STATUS_OK/STATUS_FAIL/STATUS_ACCOUNT_DISCONNECTED/FAILED_STATUSES — единственный источник на проект"
  - "HISTORY_PERIODS + apply_history_filters/history_filter_params/history_count — единственное определение фильтров истории"
  - "normalize_utc — приведение sent_at к aware-UTC на обоих диалектах"
  - "Макрос metric_tile и атрибуты разметки [data-metric-line]/[data-metric-delta]/data-tone"
affects: [04-02, 04-03, 04-04, 04-05, 04-06, 04-07, 04-08, 04-09, 04-10, phase-6-admin]

actuals:
  tokens: 43846
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Условные агрегаты func.sum(case(...)) — два окна одним запросом вместо двух round-trip"
    - "COUNT(DISTINCT CASE WHEN ... THEN col END) — счёт различных значений внутри окна без второго запроса"
    - "Отложенный импорт хелпера страничного слоя для разрыва цикла pages → dashboard → analytics → pages"
    - "Слой application не владеет календарной группировкой средствами БД — бакетирование в Python ради переносимости SQLite/PostgreSQL"

key-files:
  created:
    - app/application/analytics/__init__.py
    - app/application/analytics/send_analytics.py
    - app/templates/dashboard/includes/metric_tile.html
    - tests/test_application/test_send_analytics.py
    - tests/test_pages/test_dashboard.py
  modified:
    - app/pages/dashboard.py
    - app/pages/history.py
    - app/pages/admin.py
    - app/templates/dashboard.html
    - app/static/css/app.css

key-decisions:
  - "«Ошибок» считается как «не ok», а не как членство в FAILED_STATUSES: иначе неизвестный статус выпал бы из обеих плиток и сумма молча разошлась бы с итогом (прохибиция P-04-01)"
  - "_get_timezone_for_user импортируется ОТЛОЖЕННО, в теле функции: верхнеуровневый импорт app.pages.common из слоя application замыкает цикл через app/pages/__init__.py"
  - "Определения фильтров истории оказались в коммите задачи 1 вместе с модулем (один новый файл), а коммит задачи 2 несёт перевод потребителей и снятие приватных копий"
  - "Период today отсчитывается от локальной полуночи ЧИТАТЕЛЯ экрана: в админке в фильтры передаётся admin, а не target_user"
  - "Кэша агрегатов в модуле нет (D-37) — инвалидация потребовала бы канала связи воркера с web-слоем на каждую отправку"

patterns-established:
  - "Модуль аналитики — единственный владелец определения; страницы его ВЫЗЫВАЮТ и не держат копий"
  - "Все восемь чисел плиток проходят через int(... or 0): func.sum над пустым набором отдаёт NULL"
  - "Тело страницы в тестах вырезается по <div data-body> — навигация шелла несёт те же слова, что и снятые подписи"

requirements-completed: [DASH-01, HIST-01]

coverage:
  - id: D1
    description: "Дашборд рендерит четыре плитки отправок за скользящие сутки и не рендерит в теле страницы счётчики объявлений, аккаунтов и групп (D-01, D-02)"
    requirement: "DASH-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_renders_four_send_tiles"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_body_has_no_entity_counters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_tile_counts_last_day_sends"
        status: pass
    human_judgment: false
  - id: D2
    description: "Плитка «Ошибок» считает и fail, и account_disconnected; сумма «Успешно» и «Ошибок» равна плитке «Отправок за сутки», и неклассифицируемая запись из счёта не выпадает (P-04-01)"
    requirement: "DASH-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_account_disconnected_counts_as_failed"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_unclassifiable_status_is_still_counted"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_tiles_split_ok_and_failed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Окно — скользящие сутки с включающей границей, дельта считается к предыдущим суткам, оба окна берутся одним запросом (D-02, D-03, D-38)"
    requirement: "DASH-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_send_metrics_splits_current_and_previous_window"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_send_metrics_window_boundary_belongs_to_current"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_previous_window_fields_are_filled"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_tiles_carry_a_delta"
        status: pass
    human_judgment: false
  - id: D4
    description: "Плитка «Групп охвачено» не падает на записях с пустым group_id и не считает их за отдельную группу"
    requirement: "DASH-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_record_without_group_counts_in_total_but_not_in_groups"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_survives_send_log_without_group"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ни одна функция модуля не отдаёт чужие записи: user_id — обязательный именованный параметр, ветки «все пользователи» нет (T-04-01)"
    requirement: "DASH-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_other_users_records_are_invisible"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_history_count_ignores_other_users"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_hides_other_users_sends"
        status: pass
    human_judgment: false
  - id: D6
    description: "Фильтры истории имеют единственное определение в модуле аналитики; его импортируют и история, и админка (D-35), и перенос поведенчески нулевой"
    requirement: "HIST-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_apply_history_filters_filters_by_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_filters_survive_pagination"
        status: pass
      - kind: other
        ref: "grep -rn 'def apply_history_filters(' app/ tests/ -> ровно один файл"
        status: pass
    human_judgment: false
  - id: D7
    description: "Период today отсчитывается от локальной полуночи пользователя, а не от UTC-полуночи (D-30); неизвестное значение периода отсечки не применяет и не поднимает исключения (V5)"
    requirement: "HIST-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_period_today_cuts_at_user_local_midnight"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_apply_history_filters_unknown_period_applies_nothing"
        status: pass
    human_judgment: false
  - id: D8
    description: "history_count с данным набором фильтров возвращает ровно то число записей, которое отдаёт список с тем же набором (D-31)"
    requirement: "HIST-01"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_history_count_matches_list_length"
        status: pass
    human_judgment: false
  - id: D9
    description: "Агрегация окна не использует диалект-специфичных SQL-функций календарной группировки — она одинаково исполняется на SQLite и PostgreSQL"
    verification:
      - kind: other
        ref: "! grep -vE '^\\s*#' app/application/analytics/send_analytics.py | grep -qE 'func\\.(strftime|date_trunc|extract|to_char|julianday)'"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_module_has_no_dialect_specific_calendar_functions"
        status: pass
    human_judgment: true
    rationale: "Проверяется только отсутствие запрещённых имён на SQLite; фактическое исполнение запроса на PostgreSQL в CI не воспроизводится — подтверждение остаётся за накатом на боевой стек (чекпоинт плана 04-10)"
  - id: D10
    description: "Плитки читаются на мобильных ширинах: сетка [data-metrics] и строка значения с дельтой не ломаются на 320px"
    verification: []
    human_judgment: true
    rationale: "Браузерных/e2e-тестов в проекте нет; адаптивность подтверждается вручную — пункт 5 чекпоинта плана 04-10"

duration: 37 min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 01: Модуль аналитики отправок и живые плитки дашборда Summary

**Модуль `app/application/analytics/send_analytics.py` считает восемь чисел плиток одним запросом по скользящим суткам с дельтой к предыдущим, дашборд перешёл с трёх счётчиков сущностей на четыре плитки отправок, а определение фильтров истории переехало туда же и получило период `today` от локальной полуночи и счётчик `history_count`.**

## Performance

- **Duration:** 37 min
- **Started:** 2026-08-14T05:17:00Z
- **Completed:** 2026-08-14T05:54:22Z
- **Tasks:** 2
- **Files modified:** 10 (5 создано, 5 изменено)

## Accomplishments

- Заведён единственный владелец агрегатов журнала (D-35): его вызывают дашборд, история и админка, и ни один потребитель не держит копии определения.
- Четыре плитки отправок за скользящие сутки живы на дашборде и считаются одним round-trip на восемь чисел (D-38); счётчики объявлений, аккаунтов и групп из тела страницы сняты (D-01), в боковом меню остались нетронутыми.
- Закрыт дефект «два разных ответа на вопрос сколько было ошибок»: `account_disconnected` теперь считается ошибкой, а расчёт от UTC-полуночи заменён скользящим окном (D-02).
- Фильтры истории существуют ровно в одном файле проекта, знают период `today` от локальной полуночи читателя (D-30) и сопровождаются `history_count`, отдающим то же число, что и список (D-31).
- Два новых файла тестов (46 тестов) закрепили окно, три статуса, охват групп, изоляцию по владельцу, перенос фильтров и переносимость агрегации.

## Task Commits

1. **RED — тесты обеих задач** — `5517ba2` (test)
2. **Task 1: сквозной срез — модуль аналитики, метрики за сутки, плитки на дашборде** — `6ae8ddc` (feat)
3. **Task 2: фильтры истории и счётчик переезжают в модуль аналитики** — `59993f6` (refactor)

_Плитки и модуль исполнены как TDD-задачи: RED-коммит на оба набора тестов, затем GREEN-коммит реализации; задача 2 — поведенчески нулевой перенос, поэтому её коммит помечен `refactor`._

## Files Created/Modified

- `app/application/analytics/send_analytics.py` — контракт аналитики: константы статусов и периодов, `normalize_utc`, `SendMetrics`, `send_metrics`, `history_filter_params`, `apply_history_filters`, `history_count`
- `app/application/analytics/__init__.py` — пакет модуля
- `app/templates/dashboard/includes/metric_tile.html` — макрос плитки с mono-меткой, крупным значением и дельтой; спарклайн макета не реализуется (D-03)
- `app/pages/dashboard.py` — три запроса счётчиков и расчёт от UTC-полуночи удалены, в контекст уходит `metrics`
- `app/templates/dashboard.html` — блок `data-metrics` переписан на четыре вызова `metric_tile`; тон дельты для «Ошибок» инвертирован
- `app/static/css/app.css` — правила `[data-metric-line]` и `[data-metric-delta][data-tone]`, `tabular-nums` у значения
- `app/pages/history.py` — приватные определения фильтров удалены, обработчики зовут модуль и передают `user`; `_parse_account_id` остался как разбор HTTP-параметра
- `app/pages/admin.py` — импорт приватных имён страничного модуля истории заменён на публичные имена модуля аналитики
- `tests/test_application/test_send_analytics.py` — 28 юнит-тестов модуля
- `tests/test_pages/test_dashboard.py` — 8 интеграционных тестов дашборда (собственного файла у него не было)

## Decisions Made

- **«Ошибок» = «не ok», а не членство в `FAILED_STATUSES`.** При проверке членства запись с неизвестным статусом не попала бы ни в «Успешно», ни в «Ошибки», и сумма двух плиток молча разошлась бы с итогом — то есть неклассифицируемая запись исчезла бы из счёта ради ровных чисел. `FAILED_STATUSES` остаётся именем двух известных неуспешных значений и уходит фильтрам и разметке.
- **Отложенный импорт `_get_timezone_for_user`.** Верхнеуровневый импорт `app.pages.common` из слоя application замыкает цикл: `app/pages/__init__.py` собирает роутеры → `app.pages.dashboard` → `send_analytics` → `app.pages.common` → снова `app.pages`. Копия хелпера завела бы второй источник одного правила, поэтому импорт отложен в тело функции периода.
- **В админке в фильтры передаётся `admin`, а не `target_user`.** Записи принадлежат просматриваемому пользователю, но границу «сегодня» задаёт часовой пояс того, кто смотрит на экран.
- **Кэша нет (D-37).** Любая отправка любого воркера меняет ответ, поэтому кэш потребовал бы инвалидации из воркера на каждую запись журнала — нового канала связи воркера с web-слоем ради экономии одного индексированного запроса.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Циклический импорт слоя application и страничного слоя**
- **Found during:** Task 1 (проектирование модуля), подтверждено при написании периода `today`
- **Issue:** План предписывает брать таймзону через `_get_timezone_for_user` из `app/pages/common.py`. Верхнеуровневый импорт этого имени замыкает цикл: импорт `app.pages.common` тянет пакет `app.pages`, чей `__init__.py` собирает роутеры разделов и импортирует `app.pages.dashboard`, который импортирует ещё не доисполненный `send_analytics`. Любой вход, начинающийся с модуля аналитики (в том числе файл тестов), падал бы на ImportError.
- **Fix:** Импорт отложен в тело `_period_cutoff` — единственного места, которому таймзона нужна; причина выписана комментарием рядом.
- **Files modified:** app/application/analytics/send_analytics.py
- **Verification:** `uv run pytest tests/test_application/test_send_analytics.py -q` — 28 passed; полная суита 1130 passed
- **Committed in:** 6ae8ddc

**2. [Rule 1 - Bug] Пример поведения периода `today` в плане внутренне противоречив**
- **Found during:** Task 2 (написание теста локальной полуночи)
- **Issue:** Блок `<behavior>` утверждает, что для пользователя в UTC+3 запись в 01:00 UTC того же дня в выборку НЕ попадает. При отсечке по локальной полуночи (граница = 21:00 UTC предыдущего дня) такая запись попадает всегда; утверждение верно только для отсечки по UTC-полуночи, то есть описывает ровно тот дефект, который D-30 чинит. Вторая половина примера (22:00 UTC предыдущего дня попадает) контракту соответствует.
- **Fix:** Реализован объявленный контракт — граница есть локальная полночь пользователя, переведённая в UTC. Тест построен на паре записей вокруг вычисленной той же формулой границы (`+1 минута` попадает, `−1 минута` нет): такая пара краснеет на реализации от UTC-полуночи в ЛЮБОЙ час суток, тогда как буквальный пример плана нельзя было бы удовлетворить вместе со второй его половиной.
- **Files modified:** app/application/analytics/send_analytics.py, tests/test_application/test_send_analytics.py
- **Verification:** `test_period_today_cuts_at_user_local_midnight`, `test_period_today_without_user_falls_back_to_utc_midnight` — passed
- **Committed in:** 5517ba2 (тест), 6ae8ddc (реализация)

**3. [Rule 2 - Missing Critical] Неизвестный статус выпадал бы из обеих плиток**
- **Found during:** Task 1 (реализация `send_metrics`)
- **Issue:** Буквальная реализация «`failed` = статус входит в `FAILED_STATUSES`» оставляет запись с любым другим статусом посчитанной в `total`, но не посчитанной ни в «Успешно», ни в «Ошибках». Труть «сумма Успешно и Ошибок равна плитке Отправок за сутки» перестала бы держаться, а прохибиция P-04-01 запрещает ронять неклассифицируемую запись ради ровных чисел.
- **Fix:** Предикат ошибки — дополнение к `ok` (`status != STATUS_OK`); сторона отказа выбрана несимметрично по образцу `effective_ad_status`. Добавлен именованный тест `test_unclassifiable_status_is_still_counted`.
- **Files modified:** app/application/analytics/send_analytics.py, tests/test_application/test_send_analytics.py
- **Verification:** `test_unclassifiable_status_is_still_counted`, `test_account_disconnected_counts_as_failed` — passed
- **Committed in:** 5517ba2 (тест), 6ae8ddc (реализация)

**4. [Rule 3 - Blocking] Неиспользуемый импорт `mono` в dashboard.html**
- **Found during:** Task 1 (переписывание блока плиток)
- **Issue:** После переезда меток в макрос плитки `mono` в самом `dashboard.html` не вызывается ни разу — импорт остался бы висеть и вводил бы в заблуждение при следующей правке.
- **Fix:** Импорт снят; `mono` вызывается внутри `metric_tile.html`, куда и переехал.
- **Files modified:** app/templates/dashboard.html
- **Verification:** `uv run pytest tests/test_pages/ tests/test_templates/ -q` — 573 passed
- **Committed in:** 6ae8ddc

### Отступления от границы задач (не автопочинка)

**5. Модульная половина задачи 2 попала в коммит задачи 1.** `apply_history_filters`, `history_filter_params` и `history_count` физически живут в том же новом файле, который задача 1 обязана была создать целиком, чтобы её собственная проверка (`pytest tests/test_application/test_send_analytics.py`) стала зелёной. Разделять один файл на два коммита частичным индексированием — хуже читаемой истории, чем сдвиг границы, поэтому коммит задачи 2 (`59993f6`) несёт ровно то, что делает перенос наблюдаемым: перевод обоих потребителей на публичные имена и снятие приватных копий из `app/pages/history.py`.

**6. `app/application/accounts/__init__.py`, названный планом образцом, в дереве отсутствует.** Пакеты внутри `app/` — неявные (namespace), файла инициализации нет ни у `accounts`, ни у `scheduling`. `app/application/analytics/__init__.py` создан, потому что объявлен артефактом плана и указан в `files_modified`; для импорта он безвреден и с соседями-namespace-пакетами уживается.

---

**Total deviations:** 4 auto-fixed (1 bug, 1 missing critical, 2 blocking) + 2 задокументированных отступления от границы задач
**Impact on plan:** Все автопочинки обязательны для корректности либо для самой возможности импортировать модуль. Объём не расширен: ни одного символа сверх перечисленных в «Artifacts this phase produces» не заведено.

## Issues Encountered

None — обе задачи прошли без откатов; красных прогонов, кроме запланированной фазы RED, не было.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Готово для остальных планов фазы:** публичный контракт модуля зафиксирован и покрыт тестами. От него зависят 04-02 (индекс `(user_id, sent_at)`), 04-04 (`activity_heatmap`), 04-05 (`recent_feed`, `upcoming_sends`), 04-06 (чипсы периодов читают `HISTORY_PERIODS`), 04-08 (экспорт зовёт `apply_history_filters` и `history_count`).
- **Точка внимания для 04-02:** `send_metrics` и `history_count` корректны без индекса, но обе бьют по `send_logs` — самой растущей таблице (T-04-03). Составной индекс приходит ревизией 0016.
- **Открыто для 04-10:** исполнение агрегатов на PostgreSQL и адаптивность плиток на мобильных ширинах автотестами не подтверждаются — оба пункта уходят в чекпоинт плана 04-10.
- **Не тронуто намеренно:** блок `recent_sends` дашборда остался прежним — его заменяет план 04-05; JSON-API `app/routes/history.py` выравнивается планом 04-10.

## Self-Check: PASSED

- Все пять созданных файлов присутствуют на диске.
- Все три коммита задач присутствуют в истории ветки (`5517ba2`, `6ae8ddc`, `59993f6`).
- Критерии приёмки обеих задач перепроверены командами: `async def send_metrics(` и `FAILED_STATUSES` в модуле — есть; `from app.application.analytics.send_analytics import` в `dashboard.py`, `history.py`, `admin.py` — есть; `macro metric_tile` — есть; `replace(` с обнулением часа в `dashboard.py` — нет; `def _apply_history_filters(` / `def _history_filter_params(` в проекте — нет; `def apply_history_filters(` — ровно в одном файле.
- Проверка плана: `! grep -vE '^\s*#' app/application/analytics/send_analytics.py | grep -qE 'func\.(strftime|date_trunc|extract|to_char|julianday)'` — совпадений нет.
- Прогоны: `tests/test_application/test_send_analytics.py` + `tests/test_pages/test_dashboard.py` — 36 passed; `tests/test_pages/` + `tests/test_templates/` — 573 passed; вся суита `uv run pytest tests/ -q` — **1130 passed**.
- Заглушек не заведено: `## Known Stubs` отсутствует за отсутствием предмета.
- Новых поверхностей вне `<threat_model>` не появилось: модуль не заводит ни одного маршрута, читает только под обязательным `user_id`, разметка плиток печатает числа обычным экранированным выводом.

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-14*

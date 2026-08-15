---
phase: 04-dashbord-i-istoriya
plan: 04
subsystem: analytics
tags: [sqlalchemy, jinja2, css-grid, timezone, heatmap, dashboard, scheduling]

requires:
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-01: модуль app/application/analytics/send_analytics.py, normalize_utc, конвенция «сессия первым позиционным, остальное keyword-only», запрет календарной группировки средствами диалекта"
  - phase: 01-interfejsnyj-fundament
    provides: "макросы card_open/card_close, mono, badge, empty_state, примитив .day-grid как образец фиксированной сетки"
  - phase: 02-obyavleniya-i-raspisaniya
    provides: "адрес редактора объявления с параметром sched и якорем, effective_ad_status, формулировка бейджа «Объявление в черновике»"
provides:
  - "activity_heatmap + HeatmapView — сетка активности days×24 в таймзоне читателя, потоковое чтение окна"
  - "upcoming_sends + UpcomingSend — ближайшие отправки с пометками трёх причин несрабатывания"
  - "SHORT_WEEKDAYS, REASON_AD_DRAFT/REASON_ACCOUNT_OFF/REASON_GROUPS_OFF, UPCOMING_LIMIT, HEATMAP_YIELD_PER"
  - "dashboard_next_step — чистая функция следующего шага пользователя по счётчикам шелла"
  - "Макросы heatmap и upcoming_row; атрибуты разметки [data-heatmap]/[data-heatcell]/[data-uprow]"
affects: [04-05, 04-06, 04-10, phase-6-admin]

actuals:
  tokens: 98078
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Потоковое чтение окна проекцией одной колонки: session.stream(...).execution_options(yield_per=N) вместо выборки ORM-сущностей"
    - "Календарная раскладка по (сутки, локальный час) в Python над проекцией — переносимость SQLite/PostgreSQL"
    - "Явные join/outerjoin вместо relationship-атрибутов там, где связь объявлена lazy=\"raise\""
    - "Один запрос на блок по объединению идентификаторов вместо запроса на строку — названное отступление от D-38 с guard-тестом на число запросов"
    - "Ступень визуальной шкалы приезжает в разметку атрибутом (data-level), красит её CSS — инлайн-стилей нет"

key-files:
  created:
    - app/templates/dashboard/includes/heatmap.html
    - app/templates/dashboard/includes/upcoming_row.html
  modified:
    - app/application/analytics/send_analytics.py
    - app/pages/dashboard.py
    - app/templates/dashboard.html
    - app/static/css/app.css
    - tests/test_application/test_send_analytics.py
    - tests/test_pages/test_dashboard.py
    - tests/test_pages/test_responsive_markup.py

key-decisions:
  - "Ряды heatmap — сутки СКОЛЬЗЯЩЕГО окна (offset//24 от local_origin), а не календарные дни: таймзона меняет колонку (локальный час) и подписи, но не границы рядов"
  - "Запись на правом краю окна КЛАМПИТСЯ в последний ряд, а не отбрасывается — прохибиция плана запрещает молчаливое выбрасывание"
  - "`now` в upcoming_sends принят для единообразия сигнатур и НИЧЕГО не фильтрует: отсечка назад спрятала бы просроченные расписания и опустошила бы блок при остановленном воркере"
  - "group_count — размер СОСТАВА расписания, а не число включённых групп: расхождение с редактором лечит D-35, а о несрабатывании сообщает пометка причины"
  - "Формулировки причин совпадают с бейджем карточки раздела расписаний ДОСЛОВНО — один факт на двух экранах называется одними словами"
  - "Пустой состав групп даёт ту же причину «Все группы выключены»: четвёртая причина сверх трёх, названных D-15, не заводится"
  - "Время строки показывается С ДАТОЙ вопреки макету: у блока нет ограничения вперёд (D-14), и «10:00» без даты соврало бы о дне отправки"
  - "«Нет аккаунтов» на дашборде ведёт на /accounts, а не в подключение Telegram, как пустое состояние самого раздела: канал пользователь ещё не выбирал"

patterns-established:
  - "Признак пустоты агрегата берётся из уже посчитанного поля (view.peak), а не вторым обходом данных средствами Jinja"
  - "Запрещённые имена SQL-функций перечисляются только в СТРОЧНОМ комментарии: инвентаризационный тест ищет их по сырому тексту модуля вместе с докстрингами"
  - "Пустые состояния поблочные: у каждого блока свой текст, призыв к действию общий и следует за тем, чего не хватает"

requirements-completed: [DASH-02, DASH-04]

coverage:
  - id: D1
    description: "Heatmap раскладывает отправки по локальному часу читателя: один набор записей у пользователя в UTC+3 и в UTC попадает в разные ячейки (D-10)"
    requirement: "DASH-04"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_same_records_land_in_different_cells_per_timezone"
        status: pass
    human_judgment: false
  - id: D2
    description: "Heatmap работает на naive-датах SQLite и на aware-датах PostgreSQL — нормализация живёт в модуле аналитики, а не в шаблоне"
    requirement: "DASH-04"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_reads_naive_dates_without_raising"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_module_has_no_dialect_specific_calendar_functions"
        status: pass
      - kind: other
        ref: "! grep -vE '^\\s*#' app/application/analytics/send_analytics.py | grep -qE 'func\\.(strftime|date_trunc|extract|to_char|julianday)'"
        status: pass
    human_judgment: true
    rationale: "Исполнение запроса на PostgreSQL в CI не воспроизводится: проверяется только отсутствие запрещённых имён и поведение на SQLite. Подтверждение остаётся за накатом на боевой стек — чекпоинт плана 04-10 (тот же пункт унаследован от 04-01)"
  - id: D3
    description: "Окно heatmap — последние 7 суток скользящим окном, подписи дней следуют окну, а не фиксированному ПН-ВС (D-12)"
    requirement: "DASH-04"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_row_labels_follow_the_window_not_a_fixed_monday"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_ignores_records_outside_the_window"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_window_width_follows_the_days_argument"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ячейка считает все отправки часа, насыщенность берётся относительно самого горячего часа окна, неклассифицируемая запись из сетки не выпадает (D-11, прохибиция плана)"
    requirement: "DASH-04"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_cell_counts_every_send_of_the_hour_and_peak_is_the_max"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_counts_record_without_group_or_messenger"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сетка 7×24 отрисована без элементов таблицы и без utility-классов, ступень насыщенности приходит атрибутом (D-09)"
    requirement: "DASH-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_dashboard_heatmap_is_a_grid_without_table_elements"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_dashboard_heatmap_cells_carry_a_saturation_step"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_template_inventory"
        status: pass
    human_judgment: false
  - id: D6
    description: "Ближайшие отправки отсортированы по next_run_at, одна строка на расписание с подписью «N групп» и бейджем канала (D-13)"
    requirement: "DASH-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_orders_by_next_run_at"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_row_renders_data"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_is_sorted_by_next_run_at"
        status: pass
    human_judgment: false
  - id: D7
    description: "Чтение расписаний не поднимает lazy=\"raise\": объявление и аккаунт берутся явными join, а расписание с отвязанным аккаунтом не теряется внутренним join (D-15)"
    requirement: "DASH-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_does_not_trip_lazy_raise"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_keeps_schedule_with_detached_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_survives_lazy_raise_relationships"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_marks_detached_account"
        status: pass
    human_judgment: false
  - id: D8
    description: "Три причины несрабатывания помечаются, а здоровое расписание пометки не несёт (D-15)"
    requirement: "DASH-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_marks_draft_ad"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_marks_disconnected_account"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_marks_all_groups_off"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_leaves_a_healthy_schedule_unmarked"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_marks_draft_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_marks_all_groups_off"
        status: pass
    human_judgment: false
  - id: D9
    description: "Показываются ближайшие 5-8 расписаний без ограничения по времени вперёд; пауза и пустой next_run_at в список не попадают (D-14)"
    requirement: "DASH-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_has_no_forward_time_bound"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_respects_the_limit"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_skips_inactive_and_unscheduled"
        status: pass
    human_judgment: false
  - id: D10
    description: "Клик по строке ближайшей отправки ведёт в редактор объявления обычной ссылкой, работающей без JS (D-16)"
    requirement: "DASH-02"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_upcoming_row_links_to_the_ad_editor"
        status: pass
    human_judgment: false
  - id: D11
    description: "Плитки видны всегда со значением ноль, а heatmap и ближайшие отправки при отсутствии данных заменяются пустым состоянием со своим текстом (D-39)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_tiles_render_zeros_on_completely_empty_data"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_empty_grid_is_replaced_by_an_empty_state"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_empty_upcoming_block_has_its_own_text"
        status: pass
    human_judgment: false
  - id: D12
    description: "Пустое состояние ведёт по тому, чего не хватает: нет аккаунта, нет объявлений, нет расписаний — три разных призыва, дальше призыва нет (D-40)"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_next_step_without_accounts_leads_to_connecting_one"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_next_step_with_account_but_no_ads_leads_to_creating_an_ad"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_next_step_with_ads_but_no_schedules_leads_to_the_ads_section"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_next_step_is_empty_when_everything_is_set_up"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_empty_blocks_lead_to_creating_an_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_empty_blocks_lead_to_the_ads_section_without_schedules"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_empty_state_has_no_action_when_everything_is_set_up"
        status: pass
    human_judgment: false
  - id: D13
    description: "Флаги групп берутся одним запросом на блок — обращения к БД внутри цикла нет (T-04-19, отступление от D-38 ограничено)"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_takes_two_queries_regardless_of_group_count"
        status: pass
    human_judgment: false
  - id: D14
    description: "Ни одна из двух новых функций не отдаёт чужие данные: heatmap — по SendLog.user_id, ближайшие отправки — по Ad.user_id (T-04-13)"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_heatmap_ignores_other_users"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_upcoming_sends_ignores_other_users"
        status: pass
    human_judgment: false
  - id: D15
    description: "Дашборд пригоден к использованию на мобильных ширинах: сетка 7×24 прокручивается, строка ближайшей отправки перестраивается средствами CSS"
    verification: []
    human_judgment: true
    rationale: "Браузерных/e2e-тестов в проекте нет, медиазапросы автотестами не исполняются. Адаптивность подтверждается вручную — тот же пункт чекпоинта плана 04-10, что и у плиток из 04-01"

duration: 65 min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 04: Heatmap активности и ближайшие отправки Summary

**Сетка 7×24 считает отправки в локальных часах читателя потоковым чтением окна недели, блок ближайших отправок показывает по строке на расписание со ссылкой в редактор объявления и честной пометкой того, почему отправка не выстрелит, а пустые блоки ведут пользователя по первому недостающему шагу.**

## Performance

- **Duration:** 65 min
- **Started:** 2026-08-14T06:31:19Z
- **Completed:** 2026-08-14T07:36:39Z
- **Tasks:** 3
- **Files modified:** 9 (2 создано, 7 изменено)

## Accomplishments

- Heatmap 7×24 живёт на дашборде и отвечает на вопрос «в какие ЧАСЫ идут мои отправки», а не «сколько всего за день»: раскладка идёт по локальному часу читателя, поэтому один и тот же набор записей у пользователя в UTC+3 и в UTC даёт разные ячейки — это закреплено прямым тестом двух таймзон.
- Окно недели читается ПРОЕКЦИЕЙ одной колонки через `session.stream` с `yield_per`: ни одного ORM-объекта на самой растущей таблице системы не создаётся, память держится порядка батча (T-04-14).
- Блок «Ближайшие отправки» перестал быть слепым пятном продукта: расписание с отвязанным аккаунтом, расписание объявления-черновика и расписание со всеми выключенными группами ВИДНЫ и помечены причиной, а не теряются внутренним join или молча показываются как готовые к отправке (D-15).
- Строка блока целиком — обычная ссылка в редактор объявления по тому же адресу, что и карточка раздела расписаний (D-16): работает без JS, открывается средним щелчком, попадает под Tab.
- Пустой дашборд перестал быть одинаковым для всех: призыв следует за первым недостающим шагом (канал → объявление → расписание), а у пользователя, у которого заведено всё, призыва нет вовсе — только объяснение (D-40).
- 43 новых теста: 23 юнит-теста модуля, 18 интеграционных тестов дашборда, 2 разметочных. Полная суита — **1200 passed**.

## Task Commits

Каждая задача исполнена как TDD-пара «красный набор → реализация»:

1. **Task 1 RED — тесты heatmap** — `b1b4ce7` (test)
2. **Task 1 GREEN — heatmap 7×24 в таймзоне читателя** — `83fef17` (feat)
3. **Task 2 RED — тесты ближайших отправок** — `00ce7e5` (test)
4. **Task 2 GREEN — ближайшие отправки с пометками причин** — `06c099a` (feat)
5. **Task 3 RED — тесты пустых состояний** — `e88d7e6` (test)
6. **Task 3 GREEN — поблочные пустые состояния** — `3a76087` (feat)

## Files Created/Modified

- `app/application/analytics/send_analytics.py` — `HeatmapView`/`activity_heatmap`, `UpcomingSend`/`upcoming_sends`, константы `SHORT_WEEKDAYS`, `HEATMAP_YIELD_PER`, `UPCOMING_LIMIT` и три формулировки причин
- `app/templates/dashboard/includes/heatmap.html` — макрос `heatmap`: CSS Grid 25×N, пять ступеней насыщенности от пика окна, шкала часов блоками по шесть
- `app/templates/dashboard/includes/upcoming_row.html` — макрос `upcoming_row`: строка-ссылка с mono-временем, полоской канала, обрезаемым названием, подписью состава и бейджем причины
- `app/pages/dashboard.py` — вызовы `activity_heatmap` (с таймзоной пользователя) и `upcoming_sends`, чистая функция `dashboard_next_step`
- `app/templates/dashboard.html` — два новых блока и поблочные пустые состояния; плитки условием не обёрнуты
- `app/static/css/app.css` — правила `[data-heatmap]`/`[data-heatcell]` с прокруткой контейнера и `[data-uprow]` с перестроением на 400px
- `tests/test_application/test_send_analytics.py` — 23 новых юнит-теста (было 28, стало 51)
- `tests/test_pages/test_dashboard.py` — 18 новых интеграционных тестов (было 8, стало 26)
- `tests/test_pages/test_responsive_markup.py` — 2 разметочных теста сетки

## Decisions Made

- **Ряды heatmap — сутки скользящего окна, а не календарные дни.** Ряд `i` считается как `offset_hours // 24` от `local_origin`, поэтому таймзона меняет КОЛОНКУ (локальный час) и подписи рядов, но не границы рядов: границы суть одни и те же моменты времени в любой зоне. Это ровно то, что предписал план, и оно самосогласовано с D-12: окно скользящее, значит и «сутки» отсчитываются от `now - 7 суток`, а не от локальной полуночи.
- **Запись на правом краю окна кламается в последний ряд.** Отправка ровно в `now` даёт смещение `days*24` и индекс на один больше последнего. Пропуск такой записи был бы молчаливым выбрасыванием, которое прохибиция плана запрещает прямым текстом, поэтому ветка кламает индекс, а не делает `continue`.
- **`now` в `upcoming_sends` ничего не фильтрует.** Параметр принят для единообразия сигнатур модуля, и это выписано в докстринге прямым текстом. Ограничения вперёд нет по D-14, а отсечка назад (`next_run_at >= now`) спрятала бы просроченные расписания — то есть ровно те, о которых пользователю важнее всего узнать, — и при остановленном воркере опустошила бы блок целиком у пользователя с активными расписаниями.
- **`group_count` — размер состава расписания, а не число включённых групп.** Число обязано совпадать с тем, что пользователь видит в редакторе; подменённое на «сколько реально получит» оно завело бы второй ответ на один вопрос — болезнь, которую лечит D-35. О том, что отправка не уйдёт, сообщает пометка причины.
- **Формулировки причин совпадают с бейджем раздела расписаний дословно.** «Объявление в черновике» уже существует в `schedules/includes/schedule_row.html`; два разных слова для одного факта на двух экранах — та же болезнь в миниатюре. Строки живут в модуле аналитики как названия трёх СОСТОЯНИЙ, рядом с `SHORT_WEEKDAYS`.
- **Пустой состав групп даёт ту же причину «Все группы выключены».** Расписание без групп не отправит ничего; отдельное слово для этого случая было бы четвёртой причиной сверх трёх, названных D-15.
- **Время строки показывается с датой вопреки макету.** Макет рисует «10:00» в колонке 46px, но у блока нет ограничения вперёд (D-14): расписание может выстрелить через месяц, и время без даты соврало бы о дне отправки.
- **«Нет аккаунтов» ведёт на `/accounts`, а не в подключение Telegram.** Пустое состояние самого раздела аккаунтов ведёт сразу в `tg_user`-поток — там выбор каналов уже на экране. Пользователь дашборда канал ещё не выбирал, и решать за него значило бы отвечать не на его вопрос. Остальные два адреса повторяют пустые состояния разделов дословно.
- **Признак пустоты сетки — `view.peak`.** Он равен нулю тогда и только тогда, когда пусты все 168 ячеек; второго обхода сетки средствами Jinja этот признак не стоит.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Запрещённые имена SQL-функций в докстринге краснили инвентаризационный тест**
- **Found during:** Task 1 (реализация `activity_heatmap`)
- **Issue:** Докстринг функции перечислял запрещённые функции календарной группировки (`strftime`, `date_trunc`, `extract`) как объяснение запрета. Тест `test_module_has_no_dialect_specific_calendar_functions` снимает со ИСХОДНИКА только СТРОЧНЫЕ комментарии и ищет имена по остатку — то есть вместе с докстрингами. Объяснение запрета само нарушало запрет.
- **Fix:** Перечень имён перенесён в строчный комментарий над запросом (его тест снимает), а докстринг ссылается на этот комментарий и объясняет, почему имён в нём нет. Проверка плана `! grep -vE '^\s*#' ... | grep -qE 'func\.(...)'` проходит по той же причине.
- **Files modified:** app/application/analytics/send_analytics.py
- **Verification:** `test_module_has_no_dialect_specific_calendar_functions` — passed; grep-проверка плана совпадений не даёт
- **Committed in:** 83fef17

**2. [Rule 1 - Bug] Разметка элементов таблицы в комментарии шаблона краснила `test_template_inventory`**
- **Issue:** Докстринг `heatmap.html` называл элемент таблицы как пример того, чего в файле быть не должно. `test_template_inventory` читает СЫРОЙ текст каждого шаблона, включая комментарии, и упомянутый в комментарии пример считается нарушением наравне с настоящей разметкой.
- **Found during:** Task 1 (первый полный прогон `tests/test_pages/`)
- **Fix:** Пример из комментария снят, а сам факт «тест ищет по сырому тексту, поэтому примера здесь нет даже в комментарии» выписан — иначе следующая правка вернула бы пример обратно.
- **Files modified:** app/templates/dashboard/includes/heatmap.html
- **Verification:** `test_template_inventory` — passed
- **Committed in:** 83fef17

**3. [Rule 1 - Bug] Три ожидания рядов в моих же тестах heatmap были посчитаны неверно**
- **Found during:** Task 1 (первый прогон GREEN)
- **Issue:** В трёх тестах ряд ячейки был выписан «на глаз» по календарному дню записи, тогда как ряд считается смещением В ЧАСАХ от начала окна (окно открывается в 12:00, а не в полночь). Реализация давала ряды 5, 5 и 4, тесты ожидали 6, 6 и 5. Ошибка была в ТЕСТАХ, а не в коде: ожидание по календарному дню противоречило бы D-12, ради которого окно и сделано скользящим.
- **Fix:** Ожидания исправлены на верные, и рядом с каждым выписана арифметика («13.05 12:00 → 19.05 07:15 = 139 часов, 139 // 24 = 5») — иначе следующий читатель повторит ту же ошибку при первой правке.
- **Files modified:** tests/test_application/test_send_analytics.py
- **Verification:** все 10 тестов heatmap — passed
- **Committed in:** 83fef17

**4. [Rule 3 - Blocking] Константы под статус аккаунта в проекте нет**
- **Found during:** Task 2 (определение причины «аккаунт отключён»)
- **Issue:** Первая редакция ветки сравнивала `account.status` с именованной константой `ACCOUNT_STATUS_ACTIVE`, которой в проекте не существует: и `collect_due_schedules`, и счётчики шелла сравнивают со строковым литералом `"active"`.
- **Fix:** Взят тот же литерал с комментарием, объясняющим отказ от новой константы: заведённая здесь, она стала бы ВТОРЫМ источником одного значения, не сняв ни одного из существующих литералов. Введение общей константы — отдельная работа по всем трём местам сразу, и в объём этого плана она не входит.
- **Files modified:** app/application/analytics/send_analytics.py
- **Verification:** `test_upcoming_sends_marks_disconnected_account` — passed
- **Committed in:** 06c099a

---

**Total deviations:** 4 auto-fixed (3 bug, 1 blocking)
**Impact on plan:** Три из четырёх — починка собственных артефактов задачи (докстрингов и тестов), обнаруженная существующими инвентаризационными тестами ровно так, как эти тесты и задуманы. Объём не расширен: ни одного символа сверх перечисленных в «Artifacts this phase produces» не заведено.

### Отступления от буквы плана (не автопочинка)

**5. Второй запрос в блоке ближайших отправок — отступление от D-38, объявленное самим планом.** Флаги групп берутся одним `select(Group.id, Group.is_active)` по объединению идентификаторов не более чем восьми строк. Отступление выписано в докстринге функции и ограничено guard-тестом `test_upcoming_sends_takes_two_queries_regardless_of_group_count`, который утверждает РОВНО два SELECT на блок независимо от числа групп в расписаниях: без него отступление однажды выродилось бы в N+1 (T-04-19).

**6. Адрес призыва «нет расписаний» ведёт в раздел объявлений, а не «в настройку расписания».** План называет шаг «настройка расписания», но отдельной страницы создания расписания в продукте нет (D-14): расписания создаются в редакторе объявления, и пустое состояние самого раздела расписаний ведёт туда же — на `/ads` с подсказкой «Расписания создаются в редакторе объявления». Изобрести здесь свой адрес значило бы дать два разных ответа на один вопрос.

**7. Блок ближайших отправок стоит одиночной карточкой, а не левой половиной пары.** Вторая половина пары («Живая лента») приходит планом 04-05; до неё сетка из двух колонок состояла бы из одной заполненной и одной пустой. Место в порядке блоков занято правильное — над лентой последних отправок и heatmap, как в макете.

## Issues Encountered

None — откатов не было; красных прогонов, кроме трёх запланированных фаз RED и четырёх автопочинок выше, не случилось.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Готово для 04-05:** блок «Живая лента» встаёт правой половиной пары рядом с «Ближайшими отправками»; примитив строки (`[data-uprow]`) и приём «строка целиком — ссылка» переиспользуемы как есть.
- **Готово для Фазы 6:** `activity_heatmap` принимает `tz` и `days` параметрами, поэтому админка зовёт ту же функцию с зоной администратора и другой шириной окна, не заводя своей раскладки. Ступени насыщенности и способ шкалы зафиксированы в докстринге макроса.
- **Точка внимания для 04-02:** `activity_heatmap` читает окно недели по `(user_id, sent_at)` — тот же составной индекс ревизии 0016, что нужен плиткам и счётчику истории.
- **Открыто для 04-10 (чекпоинт):** исполнение агрегатов на PostgreSQL и адаптивность двух новых блоков на мобильных ширинах автотестами не подтверждаются — оба пункта уходят в чекпоинт того же плана, что и плитки из 04-01.
- **Не тронуто намеренно:** блок `recent_sends` остался прежним (его заменяет 04-05); граф `graphify-out/` в этом worktree отсутствует, поэтому `graphify update .` не выполнялся — граф обновляется в основном рабочем дереве после слияния.

## Known Stubs

None — заглушек не заведено. Все три блока читают настоящие данные, каждое пустое состояние наступает только при действительно пустом наборе.

## Self-Check: PASSED

- Оба созданных файла присутствуют на диске: `app/templates/dashboard/includes/heatmap.html`, `app/templates/dashboard/includes/upcoming_row.html`.
- Все шесть коммитов задач присутствуют в истории ветки: `b1b4ce7`, `83fef17`, `00ce7e5`, `06c099a`, `e88d7e6`, `3a76087`.
- Критерии приёмки перепроверены командами: `async def activity_heatmap(`, `class HeatmapView`, `session.stream(`, `yield_per`, `async def upcoming_sends(`, `class UpcomingSend`, `join(Ad,`, `outerjoin(MessengerAccount` — есть; `macro heatmap`, `data-heatcell`, `macro upcoming_row` — есть; элементов таблицы в `heatmap.html` — нет; `def dashboard_next_step(` — есть; `empty_state(` в `dashboard.html` — три вызова, собственной разметки пустого состояния нет.
- Проверка плана: `! grep -vE '^\s*#' app/application/analytics/send_analytics.py | grep -qE 'func\.(strftime|date_trunc|extract|to_char|julianday)'` — совпадений нет.
- Обращений к `Schedule.ad`/`Schedule.account` как к атрибутам в модуле нет: единственное упоминание — в докстринге, объясняющем запрет.
- Прогоны: `tests/test_application/ tests/test_pages/` — 653 passed; `tests/test_pages/ tests/test_templates/` — 593 passed; вся суита `uv run pytest tests/ -q` — **1200 passed**.
- Гейты TDD соблюдены на каждой задаче: коммит `test(...)` предшествует коммиту `feat(...)`, оба присутствуют трижды.
- Новых поверхностей вне `<threat_model>` не появилось: новых маршрутов не заведено, обе функции читают только под обязательным `user_id`, названия объявлений и подписи выводятся обычным экранированным выводом Jinja.

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-14*

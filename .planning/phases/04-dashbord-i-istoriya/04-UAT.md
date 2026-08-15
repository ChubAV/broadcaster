---
status: complete
phase: 04-dashbord-i-istoriya
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md, 04-04-SUMMARY.md, 04-05-SUMMARY.md, 04-06-SUMMARY.md, 04-07-SUMMARY.md, 04-08-SUMMARY.md, 04-09-SUMMARY.md, 04-10-SUMMARY.md]
started: 2026-08-14T00:00:00Z
updated: 2026-08-15T00:00:00Z
coverage_mode: coverage
auto_covered: 84
---

## Current Test

[testing complete]

## Tests

### 1. Холодный старт с нуля
expected: Остановить приложение и воркеры, очистить эфемерное состояние (контейнеры, кэш, Redis). Поднять стек с нуля. Приложение стартует без ошибок, ревизии `0013`-`0016` накатываются до головы `0016` (это названный блокер T-04-43/R-04-05), дашборд открывается и показывает живые данные, а не пустой экран и не 500. Вёрстка дашборда соответствует макету `new_broadcaster_design.html`.
result: pass
retested: 2026-08-15
source: human
coverage_id: 04-02·D5(prereq)
requirement: T-04-43 / R-04-05
note: |
  Перепроверка после правок. В прошлой сессии: старт стека и накат ревизий прошли
  БЕЗ ОШИБОК, дефект был в вёрстке дашборда (гэпы G-04-1, G-04-2 — оба fixed_in_place).
  Исправлено: размер глифов каналов в бейджах, высота ячеек сетки активности,
  пара «Ближайшие отправки» / «Живая лента» в две колонки, бар-чарт активности
  вместо сетки 7×24, единая шапка блоков без разделителя.

### 2. Живая лента тикает бессрочно — и только она
expected: Открыть дашборд и оставить вкладку открытой заметно дольше нескольких интервалов опроса. Лента последних событий продолжает обновляться сама, без перезагрузки страницы, и не замирает после первых тиков. При этом плитки метрик за сутки, график активности за неделю и список ближайших отправок посчитаны один раз при загрузке и опросом НЕ обновляются (D-04).
result: pass
source: human
coverage_id: 04-05·D10, 04-05·D11
requirement: DASH-03

### 3. Копирование текста ошибки
expected: В истории найти неуспешную отправку и нажать копирование в диагностическом блоке. Текст ошибки попадает в буфер обмена одним действием. Проверить и в защищённом контексте (HTTPS/localhost), и без него — запасной путь копирования должен сработать тоже.
result: pass
source: human
coverage_id: 04-07·D13
requirement: HIST-02

### 4. Двойное нажатие «Повторить» не отправляет повтор дважды
expected: В истории у неуспешной записи нажать «Повторить», в открывшейся панели подтверждения быстро нажать подтверждение ДВА раза подряд. При поднявшемся Alpine ставится ровно одна задача повтора, не две.
result: pass
source: human
coverage_id: 04-09·D12
requirement: HIST-04

### 5. Повтор доезжает до живого получателя
expected: На живом аккаунте с поднятым контейнером воркера повторить неуспешную отправку из истории. Задача проходит через очередь, подхватывается контейнером `wa_worker`/`max_worker` (или Celery для `tg_user`) и сообщение реально доставляется в группу мессенджера.
result: pass
source: human
coverage_id: 04-03·D5, 04-09·D13
requirement: HIST-04

### 6. Файл выгрузки открывается в табличном редакторе
expected: Отфильтровать историю, выгрузить результат и открыть файл в табличном редакторе с русской локалью. Кириллица целая (не «кракозябры»), поля разложены по отдельным колонкам, а значение, начинающееся с `=`, показано текстом, а не исполнено как формула.
result: pass
source: human
coverage_id: 04-08·D11
requirement: HIST-03

### 7. Сессия БД переживает поток выгрузки на боевом стеке
expected: На боевом стеке приложения выгрузить историю с крупным набором строк. Файл скачивается целиком, соединение с БД не рвётся посреди потока, и после выгрузки приложение продолжает обслуживать запросы (сессия закрылась корректно, соединения не утекли).
result: pass
source: human
coverage_id: 04-08·D12
requirement: HIST-03

### 8. Адаптивность дашборда — 320/860/900/1080
expected: Открыть дашборд на ширинах 320, 860, 900 и 1080 px. Сетка плиток и строка значения с дельтой не ломаются и не съезжают на 320px; пара «Ближайшие отправки» / «Живая лента» схлопывается в одну колонку; столбцы графика активности сжимаются по ширине и не рвут страницу (прокрутки этому блоку больше не нужно — столбец долевой); строка ближайшей отправки перестраивается; текст события в живой ленте обрезается многоточием, а подпись времени сохраняет позицию. Горизонтальной прокрутки всей страницы нет.
result: pass
source: human
coverage_id: 04-01·D10, 04-04·D15, 04-05·D12
requirement: DASH-01/03/04

### 9. Адаптивность истории — 320/860/900/1080
expected: Открыть историю на ширинах 320, 860, 900 и 1080 px. Полоса чипсов фильтров ПЕРЕНОСИТСЯ на следующую строку, а не прокручивается горизонтально; ограниченный по высоте блок ошибки и раскрытие читаемы; кнопка повтора и её объяснение помещаются в метаколонку карточки рядом с копированием и «Подробнее»; страница отдельной записи переверстана и читаема.
result: pass
source: human
coverage_id: 04-06·D14, 04-07·D14, 04-09·D14
requirement: HIST-01/02/04

### 10. Агрегации считаются верно на боевом PostgreSQL
expected: На боевом стеке с PostgreSQL открыть дашборд. Плитки за скользящие сутки, дельта к предыдущим суткам и график активности за неделю считаются без ошибок SQL и показывают те же числа, что и ожидается по данным. Модуль аналитики не использует диалект-специфичных календарных функций, поэтому запрос обязан исполниться одинаково на SQLite и PostgreSQL, а часовая сетка (её сворачивает график) — корректно отработать aware-даты PostgreSQL.
result: pass
source: human
coverage_id: 04-01·D9, 04-04·D2
requirement: DASH-01 / DASH-04

### 11. Накат ревизии 0016 не блокирует запись в send_logs
expected: Накатить ревизию `0016` (составной индекс `ix_send_logs_user_id_sent_at`) на боевую PostgreSQL с реальным объёмом `send_logs`. Заметного окна недоступности записи в журнал отправок не возникает — отправки в момент наката не теряются и не висят.
result: pass
source: human
coverage_id: 04-02·D5
requirement: DASH-01 / HIST-01

### 12. Дашборд рендерит четыре плитки отправок за скользящие сутки и не рендерит в теле страницы счётчики объявлений, аккаунтов и групп (D-01, D-02)
expected: Дашборд рендерит четыре плитки отправок за скользящие сутки и не рендерит в теле страницы счётчики объявлений, аккаунтов и групп (D-01, D-02)
result: pass
source: automated
coverage_id: 04-01·D1
requirement: DASH-01
covered_by: tests/test_pages/test_dashboard.py#test_dashboard_renders_four_send_tiles; tests/test_pages/test_dashboard.py#test_dashboard_body_has_no_entity_counters; tests/test_pages/test_dashboard.py#test_dashboard_tile_counts_last_day_sends

### 13. Плитка «Ошибок» считает и fail, и account_disconnected; сумма «Успешно» и «Ошибок» равна плитке «Отправок за сутки», и неклассифицируемая запись из счёта не выпадает (P-04-01)
expected: Плитка «Ошибок» считает и fail, и account_disconnected; сумма «Успешно» и «Ошибок» равна плитке «Отправок за сутки», и неклассифицируемая запись из счёта не выпадает (P-04-01)
result: pass
source: automated
coverage_id: 04-01·D2
requirement: DASH-01
covered_by: tests/test_application/test_send_analytics.py#test_account_disconnected_counts_as_failed; tests/test_application/test_send_analytics.py#test_unclassifiable_status_is_still_counted; tests/test_pages/test_dashboard.py#test_dashboard_tiles_split_ok_and_failed

### 14. Окно — скользящие сутки с включающей границей, дельта считается к предыдущим суткам, оба окна берутся одним запросом (D-02, D-03, D-38)
expected: Окно — скользящие сутки с включающей границей, дельта считается к предыдущим суткам, оба окна берутся одним запросом (D-02, D-03, D-38)
result: pass
source: automated
coverage_id: 04-01·D3
requirement: DASH-01
covered_by: tests/test_application/test_send_analytics.py#test_send_metrics_splits_current_and_previous_window; tests/test_application/test_send_analytics.py#test_send_metrics_window_boundary_belongs_to_current; tests/test_application/test_send_analytics.py#test_previous_window_fields_are_filled; tests/test_pages/test_dashboard.py#test_dashboard_tiles_carry_a_delta

### 15. Плитка «Групп охвачено» не падает на записях с пустым group_id и не считает их за отдельную группу
expected: Плитка «Групп охвачено» не падает на записях с пустым group_id и не считает их за отдельную группу
result: pass
source: automated
coverage_id: 04-01·D4
requirement: DASH-01
covered_by: tests/test_application/test_send_analytics.py#test_record_without_group_counts_in_total_but_not_in_groups; tests/test_pages/test_dashboard.py#test_dashboard_survives_send_log_without_group

### 16. Ни одна функция модуля не отдаёт чужие записи: user_id — обязательный именованный параметр, ветки «все пользователи» нет (T-04-01)
expected: Ни одна функция модуля не отдаёт чужие записи: user_id — обязательный именованный параметр, ветки «все пользователи» нет (T-04-01)
result: pass
source: automated
coverage_id: 04-01·D5
requirement: DASH-01
covered_by: tests/test_application/test_send_analytics.py#test_other_users_records_are_invisible; tests/test_application/test_send_analytics.py#test_history_count_ignores_other_users; tests/test_pages/test_dashboard.py#test_dashboard_hides_other_users_sends

### 17. Фильтры истории имеют единственное определение в модуле аналитики; его импортируют и история, и админка (D-35), и перенос поведенчески нулевой
expected: Фильтры истории имеют единственное определение в модуле аналитики; его импортируют и история, и админка (D-35), и перенос поведенчески нулевой
result: pass
source: automated
coverage_id: 04-01·D6
requirement: HIST-01
covered_by: tests/test_application/test_send_analytics.py#test_apply_history_filters_filters_by_account; tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters; tests/test_pages/test_responsive_markup.py#test_history_filters_survive_pagination; grep -rn 'def apply_history_filters(' app/ tests/ -> ровно один файл

### 18. Период today отсчитывается от локальной полуночи пользователя, а не от UTC-полуночи (D-30); неизвестное значение периода отсечки не применяет и не поднимает исключения (V5)
expected: Период today отсчитывается от локальной полуночи пользователя, а не от UTC-полуночи (D-30); неизвестное значение периода отсечки не применяет и не поднимает исключения (V5)
result: pass
source: automated
coverage_id: 04-01·D7
requirement: HIST-01
covered_by: tests/test_application/test_send_analytics.py#test_period_today_cuts_at_user_local_midnight; tests/test_application/test_send_analytics.py#test_apply_history_filters_unknown_period_applies_nothing

### 19. history_count с данным набором фильтров возвращает ровно то число записей, которое отдаёт список с тем же набором (D-31)
expected: history_count с данным набором фильтров возвращает ровно то число записей, которое отдаёт список с тем же набором (D-31)
result: pass
source: automated
coverage_id: 04-01·D8
requirement: HIST-01
covered_by: tests/test_application/test_send_analytics.py#test_history_count_matches_list_length

### 20. Ревизия 0016 создаёт составной индекс ix_send_logs_user_id_sent_at на send_logs (user_id, sent_at)
expected: Ревизия 0016 создаёт составной индекс ix_send_logs_user_id_sent_at на send_logs (user_id, sent_at)
result: pass
source: automated
coverage_id: 04-02·D1
requirement: DASH-01
covered_by: tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_upgrade_creates_composite_index

### 21. downgrade снимает составной индекс и не трогает строки журнала отправок
expected: downgrade снимает составной индекс и не трогает строки журнала отправок
result: pass
source: automated
coverage_id: 04-02·D2
requirement: HIST-01
covered_by: tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_downgrade_removes_composite_index; tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_rows_survive_upgrade_and_downgrade

### 22. Одиночные индексы user_id, task_id и sent_at переживают ревизию — она добавляет, а не заменяет
expected: Одиночные индексы user_id, task_id и sent_at переживают ревизию — она добавляет, а не заменяет
result: pass
source: automated
coverage_id: 04-02·D3
requirement: HIST-03
covered_by: tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_upgrade_keeps_the_single_column_indexes

### 23. История ревизий остаётся одной линией: 0016 продолжает 0015, голова одна
expected: История ревизий остаётся одной линией: 0016 продолжает 0015, голова одна
result: pass
source: automated
coverage_id: 04-02·D4
requirement: DASH-04
covered_by: tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_revision_0016_continues_0015; uv run alembic heads → '0016 (head)'

### 24. build_dispatch_task — одно определение сборки задачи отправки; планировщик зовёт его и ведёт себя ровно как раньше
expected: build_dispatch_task — одно определение сборки задачи отправки; планировщик зовёт его и ведёт себя ровно как раньше
result: pass
source: automated
coverage_id: 04-03·D1
requirement: HIST-04
covered_by: tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_tg_user_leaves_wa_fields_empty; tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_fills_queue_fields; tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_expands_images_to_urls; tests/test_application/test_scheduling_use_cases.py#test_build_dispatch_task_keeps_empty_images_as_is; uv run pytest tests/ -q (1116 passed) — существующие тесты подбора расписаний как регрессия на нулевое изменение поведения

### 25. retry_send ставит повтор в правильный транспорт для каждого из трёх типов аккаунта: wa/max — в Redis-очередь аккаунта, tg_user — в Celery-очередь telegram
expected: retry_send ставит повтор в правильный транспорт для каждого из трёх типов аккаунта: wa/max — в Redis-очередь аккаунта, tg_user — в Celery-очередь telegram
result: pass
source: automated
coverage_id: 04-03·D2
requirement: HIST-04
covered_by: tests/test_worker/test_tasks.py#test_retry_send_routes_queue_channels_to_redis; tests/test_worker/test_tasks.py#test_retry_send_routes_telegram_to_celery

### 26. Чужая запись, отсутствующая сущность и неактивный аккаунт останавливают повтор до диспетчеризации и не пишут в журнал
expected: Чужая запись, отсутствующая сущность и неактивный аккаунт останавливают повтор до диспетчеризации и не пишут в журнал
result: pass
source: automated
coverage_id: 04-03·D3
requirement: HIST-04
covered_by: tests/test_worker/test_tasks.py#test_retry_send_rejects_foreign_log; tests/test_worker/test_tasks.py#test_retry_send_ignores_unknown_log; tests/test_worker/test_tasks.py#test_retry_send_stops_when_entity_gone; tests/test_worker/test_tasks.py#test_retry_send_stops_when_account_not_active

### 27. Второго пути отправки не создано: формат полезной нагрузки WA/MAX не изменён, send_message_once и адаптеры мессенджеров из таска не вызываются
expected: Второго пути отправки не создано: формат полезной нагрузки WA/MAX не изменён, send_message_once и адаптеры мессенджеров из таска не вызываются
result: pass
source: automated
coverage_id: 04-03·D4
requirement: HIST-04
covered_by: tests/test_worker/test_tasks.py#test_retry_send_routes_queue_channels_to_redis — состав ключей payload проверяется поимённо, Celery-очередь telegram о; grep: dispatch_send_tasks не менялась (git diff по app/worker/tasks.py — только добавление retry_send); в теле retry_send нет rpush, json.dumps и send

### 28. Heatmap раскладывает отправки по локальному часу читателя: один набор записей у пользователя в UTC+3 и в UTC попадает в разные ячейки (D-10)
expected: Heatmap раскладывает отправки по локальному часу читателя: один набор записей у пользователя в UTC+3 и в UTC попадает в разные ячейки (D-10)
result: pass
source: automated
coverage_id: 04-04·D1
requirement: DASH-04
covered_by: tests/test_application/test_send_analytics.py#test_heatmap_same_records_land_in_different_cells_per_timezone

### 29. Окно heatmap — последние 7 суток скользящим окном, подписи дней следуют окну, а не фиксированному ПН-ВС (D-12)
expected: Окно heatmap — последние 7 суток скользящим окном, подписи дней следуют окну, а не фиксированному ПН-ВС (D-12)
result: pass
source: automated
coverage_id: 04-04·D3
requirement: DASH-04
covered_by: tests/test_application/test_send_analytics.py#test_heatmap_row_labels_follow_the_window_not_a_fixed_monday; tests/test_application/test_send_analytics.py#test_heatmap_ignores_records_outside_the_window; tests/test_application/test_send_analytics.py#test_heatmap_window_width_follows_the_days_argument

### 30. Ячейка считает все отправки часа, насыщенность берётся относительно самого горячего часа окна, неклассифицируемая запись из сетки не выпадает (D-11, прохибиция плана)
expected: Ячейка считает все отправки часа, насыщенность берётся относительно самого горячего часа окна, неклассифицируемая запись из сетки не выпадает (D-11, прохибиция плана)
result: pass
source: automated
coverage_id: 04-04·D4
requirement: DASH-04
covered_by: tests/test_application/test_send_analytics.py#test_heatmap_cell_counts_every_send_of_the_hour_and_peak_is_the_max; tests/test_application/test_send_analytics.py#test_heatmap_counts_record_without_group_or_messenger

### 31. График активности отрисован без элементов таблицы и без utility-классов, признак заливки приходит атрибутом
expected: График активности отрисован без элементов таблицы и без utility-классов, признак заливки приходит атрибутом
result: pass
source: automated
coverage_id: 04-04·D5
requirement: DASH-04
superseded: "Формулировка обновлена вместе с отменой D-09 (сетка 7×24 → бар-чарт макета, gap G-04-2). Прежние покрывающие тесты сетки не сняты, а переписаны под новую форму блока."
covered_by: tests/test_pages/test_responsive_markup.py#test_dashboard_activity_chart_renders_bars_without_table_elements; tests/test_pages/test_responsive_markup.py#test_dashboard_chart_bars_carry_height_but_never_inline_colour; tests/test_pages/test_responsive_markup.py#test_template_inventory

### 32. Ближайшие отправки отсортированы по next_run_at, одна строка на расписание с подписью «N групп» и бейджем канала (D-13)
expected: Ближайшие отправки отсортированы по next_run_at, одна строка на расписание с подписью «N групп» и бейджем канала (D-13)
result: pass
source: automated
coverage_id: 04-04·D6
requirement: DASH-02
covered_by: tests/test_application/test_send_analytics.py#test_upcoming_sends_orders_by_next_run_at; tests/test_pages/test_dashboard.py#test_dashboard_upcoming_row_renders_data; tests/test_pages/test_dashboard.py#test_dashboard_upcoming_is_sorted_by_next_run_at

### 33. Чтение расписаний не поднимает lazy=\"raise\": объявление и аккаунт берутся явными join, а расписание с отвязанным аккаунтом не теряется внутренним join (D-15)
expected: Чтение расписаний не поднимает lazy=\"raise\": объявление и аккаунт берутся явными join, а расписание с отвязанным аккаунтом не теряется внутренним join (D-15)
result: pass
source: automated
coverage_id: 04-04·D7
requirement: DASH-02
covered_by: tests/test_application/test_send_analytics.py#test_upcoming_sends_does_not_trip_lazy_raise; tests/test_application/test_send_analytics.py#test_upcoming_sends_keeps_schedule_with_detached_account; tests/test_pages/test_dashboard.py#test_dashboard_upcoming_survives_lazy_raise_relationships; tests/test_pages/test_dashboard.py#test_dashboard_upcoming_marks_detached_account

### 34. Три причины несрабатывания помечаются, а здоровое расписание пометки не несёт (D-15)
expected: Три причины несрабатывания помечаются, а здоровое расписание пометки не несёт (D-15)
result: pass
source: automated
coverage_id: 04-04·D8
requirement: DASH-02
covered_by: tests/test_application/test_send_analytics.py#test_upcoming_sends_marks_draft_ad; tests/test_application/test_send_analytics.py#test_upcoming_sends_marks_disconnected_account; tests/test_application/test_send_analytics.py#test_upcoming_sends_marks_all_groups_off; tests/test_application/test_send_analytics.py#test_upcoming_sends_leaves_a_healthy_schedule_unmarked; tests/test_pages/test_dashboard.py#test_dashboard_upcoming_marks_draft_ad; tests/test_pages/test_dashboard.py#test_dashboard_upcoming_marks_all_groups_off

### 35. Показываются ближайшие 5-8 расписаний без ограничения по времени вперёд; пауза и пустой next_run_at в список не попадают (D-14)
expected: Показываются ближайшие 5-8 расписаний без ограничения по времени вперёд; пауза и пустой next_run_at в список не попадают (D-14)
result: pass
source: automated
coverage_id: 04-04·D9
requirement: DASH-02
covered_by: tests/test_application/test_send_analytics.py#test_upcoming_sends_has_no_forward_time_bound; tests/test_application/test_send_analytics.py#test_upcoming_sends_respects_the_limit; tests/test_application/test_send_analytics.py#test_upcoming_sends_skips_inactive_and_unscheduled

### 36. Клик по строке ближайшей отправки ведёт в редактор объявления обычной ссылкой, работающей без JS (D-16)
expected: Клик по строке ближайшей отправки ведёт в редактор объявления обычной ссылкой, работающей без JS (D-16)
result: pass
source: automated
coverage_id: 04-04·D10
requirement: DASH-02
covered_by: tests/test_pages/test_dashboard.py#test_dashboard_upcoming_row_links_to_the_ad_editor

### 37. Плитки видны всегда со значением ноль, а heatmap и ближайшие отправки при отсутствии данных заменяются пустым состоянием со своим текстом (D-39)
expected: Плитки видны всегда со значением ноль, а heatmap и ближайшие отправки при отсутствии данных заменяются пустым состоянием со своим текстом (D-39)
result: pass
source: automated
coverage_id: 04-04·D11
covered_by: tests/test_pages/test_dashboard.py#test_dashboard_tiles_render_zeros_on_completely_empty_data; tests/test_pages/test_dashboard.py#test_dashboard_empty_grid_is_replaced_by_an_empty_state; tests/test_pages/test_dashboard.py#test_dashboard_empty_upcoming_block_has_its_own_text

### 38. Пустое состояние ведёт по тому, чего не хватает: нет аккаунта, нет объявлений, нет расписаний — три разных призыва, дальше призыва нет (D-40)
expected: Пустое состояние ведёт по тому, чего не хватает: нет аккаунта, нет объявлений, нет расписаний — три разных призыва, дальше призыва нет (D-40)
result: pass
source: automated
coverage_id: 04-04·D12
covered_by: tests/test_pages/test_dashboard.py#test_next_step_without_accounts_leads_to_connecting_one; tests/test_pages/test_dashboard.py#test_next_step_with_account_but_no_ads_leads_to_creating_an_ad; tests/test_pages/test_dashboard.py#test_next_step_with_ads_but_no_schedules_leads_to_the_ads_section; tests/test_pages/test_dashboard.py#test_next_step_is_empty_when_everything_is_set_up; tests/test_pages/test_dashboard.py#test_dashboard_empty_blocks_lead_to_creating_an_ad; tests/test_pages/test_dashboard.py#test_dashboard_empty_blocks_lead_to_the_ads_section_without_schedules; tests/test_pages/test_dashboard.py#test_dashboard_empty_state_has_no_action_when_everything_is_set_up

### 39. Флаги групп берутся одним запросом на блок — обращения к БД внутри цикла нет (T-04-19, отступление от D-38 ограничено)
expected: Флаги групп берутся одним запросом на блок — обращения к БД внутри цикла нет (T-04-19, отступление от D-38 ограничено)
result: pass
source: automated
coverage_id: 04-04·D13
covered_by: tests/test_application/test_send_analytics.py#test_upcoming_sends_takes_two_queries_regardless_of_group_count

### 40. Ни одна из двух новых функций не отдаёт чужие данные: heatmap — по SendLog.user_id, ближайшие отправки — по Ad.user_id (T-04-13)
expected: Ни одна из двух новых функций не отдаёт чужие данные: heatmap — по SendLog.user_id, ближайшие отправки — по Ad.user_id (T-04-13)
result: pass
source: automated
coverage_id: 04-04·D14
covered_by: tests/test_application/test_send_analytics.py#test_heatmap_ignores_other_users; tests/test_application/test_send_analytics.py#test_upcoming_sends_ignores_other_users

### 41. Маршрут паршала ленты объявлен вне страничного роутера и не тянет контекст шелла на каждый тик
expected: Маршрут паршала ленты объявлен вне страничного роутера и не тянет контекст шелла на каждый тик
result: pass
source: automated
coverage_id: 04-05·D1
requirement: DASH-03
covered_by: tests/test_pages/test_dashboard.py#test_dashboard_feed_does_not_load_the_shell_context; tests/test_pages/test_dashboard.py#test_dashboard_feed_response_is_a_fragment_not_a_page

### 42. Лента отдаёт не более limit строк владельца по убыванию времени отправки; чужие записи не попадают (T-04-17)
expected: Лента отдаёт не более limit строк владельца по убыванию времени отправки; чужие записи не попадают (T-04-17)
result: pass
source: automated
coverage_id: 04-05·D2
requirement: DASH-03
covered_by: tests/test_pages/test_dashboard.py#test_recent_feed_returns_newest_first; tests/test_pages/test_dashboard.py#test_recent_feed_respects_the_limit; tests/test_pages/test_dashboard.py#test_recent_feed_row_carries_the_fields_of_the_record; tests/test_pages/test_dashboard.py#test_recent_feed_ignores_other_users; tests/test_pages/test_dashboard.py#test_dashboard_feed_requires_authentication

### 43. Строка ленты — обычная ссылка в запись истории и работает без JavaScript (D-08)
expected: Строка ленты — обычная ссылка в запись истории и работает без JavaScript (D-08)
result: pass
source: automated
coverage_id: 04-05·D3
requirement: DASH-03
covered_by: tests/test_pages/test_dashboard.py#test_dashboard_feed_row_links_to_the_history_record; tests/test_pages/test_dashboard.py#test_dashboard_feed_returns_rows

### 44. Страница несёт адрес паршала и объявление интервала, а паршал не несёт ни одного атрибута опроса — парная половина (D-06, D-07)
expected: Страница несёт адрес паршала и объявление интервала, а паршал не несёт ни одного атрибута опроса — парная половина (D-06, D-07)
result: pass
source: automated
coverage_id: 04-05·D4
requirement: DASH-03
covered_by: tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_container_polls; tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_partial_carries_no_polling_attributes

### 45. Опрос не самоостанавливается: ветки, в которой атрибуты покидают DOM, в разметке нет
expected: Опрос не самоостанавливается: ветки, в которой атрибуты покидают DOM, в разметке нет
result: pass
source: automated
coverage_id: 04-05·D5
requirement: DASH-03
covered_by: tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_polling_survives_an_empty_feed; tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_polling_has_no_stop_branch; tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_swaps_inside_the_container

### 46. Существующий механизм остановки опроса на экране аккаунтов не тронут — три самоостанавливающихся опроса проекта остались зелёными
expected: Существующий механизм остановки опроса на экране аккаунтов не тронут — три самоостанавливающихся опроса проекта остались зелёными
result: pass
source: automated
coverage_id: 04-05·D6
covered_by: tests/test_pages/test_htmx_preserved.py#test_sync_polling_stops; tests/test_pages/test_htmx_preserved.py#test_sync_polling_continues_while_syncing

### 47. Блок «Последние отправки» со страницы исчез, а шаблон его строки в проекте больше не достижим и снят с обоих инвентаризационных перечней
expected: Блок «Последние отправки» со страницы исчез, а шаблон его строки в проекте больше не достижим и снят с обоих инвентаризационных перечней
result: pass
source: automated
coverage_id: 04-05·D7
covered_by: tests/test_pages/test_responsive_markup.py#test_row_templates_without_header_are_accounted_for; tests/test_pages/test_responsive_markup.py#test_rowhead_pages_all_have_a_parametrization_entry; test ! -f app/templates/dashboard/includes/recent_send_card.html

### 48. Дашборд показывает число воркеров онлайн из контракта шелла; число равно числу активных messenger-аккаунтов, ноль показывается, а не прячется (DASH-05)
expected: Дашборд показывает число воркеров онлайн из контракта шелла; число равно числу активных messenger-аккаунтов, ноль показывается, а не прячется (DASH-05)
result: pass
source: automated
coverage_id: 04-05·D8
requirement: DASH-05
covered_by: tests/test_pages/test_shell.py#test_dashboard_shows_the_sessions_indicator; tests/test_pages/test_shell.py#test_dashboard_sessions_number_counts_active_accounts; tests/test_pages/test_shell.py#test_dashboard_sessions_number_is_zero_without_active_accounts

### 49. В пути рендера дашборда нет обращения к Docker ни при каких условиях, и второго источника числа воркеров не появилось (T-04-21)
expected: В пути рендера дашборда нет обращения к Docker ни при каких условиях, и второго источника числа воркеров не появилось (T-04-21)
result: pass
source: automated
coverage_id: 04-05·D9
requirement: DASH-05
covered_by: tests/test_pages/test_shell.py#test_dashboard_render_path_never_touches_docker; tests/test_pages/test_shell.py#test_dashboard_page_has_no_second_source_of_the_sessions_number

### 50. Статус, канал и период выбираются чипсами одним действием без кнопки «Применить» (D-29), и выбор меняет выборку
expected: Статус, канал и период выбираются чипсами одним действием без кнопки «Применить» (D-29), и выбор меняет выборку
result: pass
source: automated
coverage_id: 04-06·D1
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_status_chip_filters_the_list; tests/test_pages/test_history.py#test_messenger_chip_filters_the_list; tests/test_pages/test_history.py#test_account_disconnected_chip_filters_the_list

### 51. Чипсы — обычные ссылки: смена фильтра работает при выключенном JavaScript
expected: Чипсы — обычные ссылки: смена фильтра работает при выключенном JavaScript
result: pass
source: automated
coverage_id: 04-06·D2
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_chips_are_links_and_need_no_javascript

### 52. Чипсы статуса покрывают все три значения журнала, включая отключённый аккаунт; чипсы канала — все три канала проекта
expected: Чипсы статуса покрывают все три значения журнала, включая отключённый аккаунт; чипсы канала — все три канала проекта
result: pass
source: automated
coverage_id: 04-06·D3
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_status_chips_cover_all_three_journal_statuses; tests/test_pages/test_history.py#test_messenger_chips_cover_all_three_channels; tests/test_pages/test_history.py#test_messenger_chips_match_the_channel_axis_of_the_project

### 53. Фильтр по аккаунту сохранён выпадающим списком рядом с чипсами и переживает смену чипса (D-29)
expected: Фильтр по аккаунту сохранён выпадающим списком рядом с чипсами и переживает смену чипса (D-29)
result: pass
source: automated
coverage_id: 04-06·D4
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_account_dropdown_survives_a_chip_switch; tests/test_pages/test_history.py#test_account_filter_cannot_reach_another_users_records

### 54. Варианты периода — сегодня, 7 дней, 30 дней, всё время; произвольного диапазона нет, «сегодня» отсчитывается от локальной полуночи пользователя (D-30)
expected: Варианты периода — сегодня, 7 дней, 30 дней, всё время; произвольного диапазона нет, «сегодня» отсчитывается от локальной полуночи пользователя (D-30)
result: pass
source: automated
coverage_id: 04-06·D5
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_period_chips_cover_four_options; tests/test_pages/test_history.py#test_period_today_cuts_at_user_local_midnight; tests/test_pages/test_history.py#test_period_chips_cover_every_period_the_module_knows

### 55. Переход по чипсу сохраняет остальные активные фильтры, а вариант «все» снимает только свою ось; активный чипс размечен и он в группе один
expected: Переход по чипсу сохраняет остальные активные фильтры, а вариант «все» снимает только свою ось; активный чипс размечен и он в группе один
result: pass
source: automated
coverage_id: 04-06·D6
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_chip_link_keeps_the_other_filters; tests/test_pages/test_history.py#test_all_chip_drops_only_its_own_filter; tests/test_pages/test_history.py#test_active_chip_is_marked_and_the_others_are_not

### 56. Неизвестное значение оси в адресе не роняет страницу и не применяется (T-04-23); полоса чипсов не остаётся без активного варианта
expected: Неизвестное значение оси в адресе не роняет страницу и не применяется (T-04-23); полоса чипсов не остаётся без активного варианта
result: pass
source: automated
coverage_id: 04-06·D7
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_unknown_filter_values_do_not_break_the_page; tests/test_pages/test_history.py#test_unknown_filter_value_leaves_the_all_chip_active

### 57. Запись со старым пустым значением канала не совпадает ни с одним чипсом конкретного канала и остаётся видимой при варианте «все»
expected: Запись со старым пустым значением канала не совпадает ни с одним чипсом конкретного канала и остаётся видимой при варианте «все»
result: pass
source: automated
coverage_id: 04-06·D8
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_record_without_messenger_survives_the_all_chip

### 58. Над списком показывается точное число найденного отдельным запросом с теми же фильтрами, и оно совпадает с числом записей полной выборки тех же фильтров (D-31)
expected: Над списком показывается точное число найденного отдельным запросом с теми же фильтрами, и оно совпадает с числом записей полной выборки тех же фильтров (D-31)
result: pass
source: automated
coverage_id: 04-06·D9
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_counter_matches_the_full_selection_of_the_same_filters; tests/test_pages/test_history.py#test_counter_counts_beyond_the_first_page; tests/test_pages/test_history.py#test_counter_follows_the_filters; tests/test_pages/test_history.py#test_counter_shows_the_number_of_found_records

### 59. Счётчик не считает чужих записей: условие владения стоит в базовом запросе счётчика (T-04-22)
expected: Счётчик не считает чужих записей: условие владения стоит в базовом запросе счётчика (T-04-22)
result: pass
source: automated
coverage_id: 04-06·D10
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_counter_ignores_other_users; tests/test_application/test_send_analytics.py#test_history_count_ignores_other_users

### 60. Пустой результат фильтров даёт отдельный текст со сбросом, отличный от текста «отправок вообще нет» (D-41)
expected: Пустой результат фильтров даёт отдельный текст со сбросом, отличный от текста «отправок вообще нет» (D-41)
result: pass
source: automated
coverage_id: 04-06·D11
requirement: HIST-01
covered_by: tests/test_pages/test_history.py#test_empty_filter_result_differs_from_the_empty_journal; tests/test_pages/test_history.py#test_empty_journal_keeps_the_old_text

### 61. Активный набор фильтров переживает бесконечную прокрутку — разметка сентинела на странице и в паршале идентична
expected: Активный набор фильтров переживает бесконечную прокрутку — разметка сентинела на странице и в паршале идентична
result: pass
source: automated
coverage_id: 04-06·D12
covered_by: tests/test_pages/test_history.py#test_infinite_scroll_sentinel_is_identical_in_page_and_partial; tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters; tests/test_pages/test_responsive_markup.py#test_history_filters_survive_pagination

### 62. Новый файл шаблона положен вне каталога компонентов — инвентаризация библиотеки компонентов не сдвинута
expected: Новый файл шаблона положен вне каталога компонентов — инвентаризация библиотеки компонентов не сдвинута
result: pass
source: automated
coverage_id: 04-06·D13
covered_by: tests/test_pages/test_history.py#test_filter_chips_template_lives_outside_the_component_library; tests/test_pages/test_responsive_markup.py#test_template_inventory

### 63. Текст ошибки неуспешной записи виден в карточке списка всегда и не спрятан за кликом (D-32)
expected: Текст ошибки неуспешной записи виден в карточке списка всегда и не спрятан за кликом (D-32)
result: pass
source: automated
coverage_id: 04-07·D1
requirement: HIST-02
covered_by: tests/test_pages/test_responsive_markup.py#test_history_card_shows_error_text_in_full; tests/test_pages/test_history.py#test_error_block_stays_copyable_without_the_button

### 64. Текст ошибки выводится экранированным: разметка из данных мессенджера не исполняется (T-04-26)
expected: Текст ошибки выводится экранированным: разметка из данных мессенджера не исполняется (T-04-26)
result: pass
source: automated
coverage_id: 04-07·D2
requirement: HIST-02
covered_by: tests/test_pages/test_responsive_markup.py#test_history_card_escapes_error_text; tests/test_pages/test_responsive_markup.py#test_admin_history_escapes_error_text

### 65. Длинный текст ошибки в карточке списка ограничен по высоте с возможностью раскрыть, и раскрытие не требует JavaScript
expected: Длинный текст ошибки в карточке списка ограничен по высоте с возможностью раскрыть, и раскрытие не требует JavaScript
result: pass
source: automated
coverage_id: 04-07·D3
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_error_block_is_height_limited_only_in_the_list_card; tests/test_pages/test_history.py#test_clamp_expansion_needs_no_javascript

### 66. Примитив длинного текста не изменён: ограничение живёт модификатором и действует только в карточке списка
expected: Примитив длинного текста не изменён: ограничение живёт модификатором и действует только в карточке списка
result: pass
source: automated
coverage_id: 04-07·D4
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_long_text_primitive_is_untouched

### 67. На странице записи и в админской истории текст ошибки остаётся полным без ограничения по высоте
expected: На странице записи и в админской истории текст ошибки остаётся полным без ограничения по высоте
result: pass
source: automated
coverage_id: 04-07·D5
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_error_block_is_height_limited_only_in_the_list_card; tests/test_pages/test_responsive_markup.py#test_history_detail_shows_error_text; tests/test_pages/test_responsive_markup.py#test_admin_history_detail_shows_error_text

### 68. Кнопка копирования не рендерится при выключенном Alpine и страница при этом остаётся рабочей (D-34)
expected: Кнопка копирования не рендерится при выключенном Alpine и страница при этом остаётся рабочей (D-34)
result: pass
source: automated
coverage_id: 04-07·D6
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_copy_button_is_absent_without_alpine; tests/test_pages/test_history.py#test_history_detail_offers_the_same_copy_button

### 69. Базовый путь копирования без JavaScript работает выделением блока ошибки одним действием
expected: Базовый путь копирования без JavaScript работает выделением блока ошибки одним действием
result: pass
source: automated
coverage_id: 04-07·D7
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_error_block_stays_copyable_without_the_button

### 70. Кнопка копирования кладёт в буфер диагностический блок: время, канал, группу, объявление, идентификатор задачи и текст ошибки (D-33)
expected: Кнопка копирования кладёт в буфер диагностический блок: время, канал, группу, объявление, идентификатор задачи и текст ошибки (D-33)
result: pass
source: automated
coverage_id: 04-07·D8
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_copy_button_carries_the_whole_diagnostic_block

### 71. Кнопка копирования проверяет доступность буфера обмена перед обращением к нему и не сообщает об успехе, которого не было (T-04-29)
expected: Кнопка копирования проверяет доступность буфера обмена перед обращением к нему и не сообщает об успехе, которого не было (T-04-29)
result: pass
source: automated
coverage_id: 04-07·D9
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_copy_handler_checks_the_clipboard_before_reaching_for_it; tests/test_pages/test_history.py#test_copy_handler_never_claims_a_copy_that_did_not_happen

### 72. Клиентский код кнопки строит узлы DOM и не присваивает строки разметки (T-04-30)
expected: Клиентский код кнопки строит узлы DOM и не присваивает строки разметки (T-04-30)
result: pass
source: automated
coverage_id: 04-07·D10
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_copy_handler_builds_dom_not_markup

### 73. У успешной записи блока ошибки и кнопки копирования нет; у ЛЮБОЙ неуспешной, включая запись с неизвестным статусом, кнопка есть
expected: У успешной записи блока ошибки и кнопки копирования нет; у ЛЮБОЙ неуспешной, включая запись с неизвестным статусом, кнопка есть
result: pass
source: automated
coverage_id: 04-07·D11
covered_by: tests/test_pages/test_history.py#test_successful_record_has_neither_error_block_nor_copy_button; tests/test_pages/test_history.py#test_every_unsuccessful_record_offers_the_copy_button

### 74. Страница записи истории сохранена и переверстана по макету; владение на входе не ослаблено (D-24, T-04-27)
expected: Страница записи истории сохранена и переверстана по макету; владение на входе не ослаблено (D-24, T-04-27)
result: pass
source: automated
coverage_id: 04-07·D12
requirement: HIST-02
covered_by: tests/test_pages/test_history.py#test_history_detail_shows_the_whole_record; tests/test_pages/test_history.py#test_history_detail_shows_the_content_snapshot; tests/test_pages/test_history.py#test_history_detail_reuses_the_record_primitive_and_adds_no_view_switch; tests/test_pages/test_history.py#test_history_detail_inherits_the_shell_and_draws_no_section_heading; tests/test_pages/test_history.py#test_history_detail_of_another_users_record_redirects_to_the_list; tests/test_pages/test_history.py#test_history_detail_of_a_missing_record_redirects_to_the_list

### 75. Выгрузка отдаёт именно отфильтрованный результат: маршрут применяет ту же функцию фильтрации, что список и счётчик (HIST-03)
expected: Выгрузка отдаёт именно отфильтрованный результат: маршрут применяет ту же функцию фильтрации, что список и счётчик (HIST-03)
result: pass
source: automated
coverage_id: 04-08·D1
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_honours_the_status_filter; tests/test_pages/test_history_export.py#test_export_honours_the_period_filter; tests/test_pages/test_history_export.py#test_export_ignores_an_unknown_filter_value; tests/test_pages/test_history_export.py#test_export_carries_the_account_of_the_group

### 76. Число строк в файле равно числу, которое показывает счётчик над списком с тем же набором фильтров
expected: Число строк в файле равно числу, которое показывает счётчик над списком с тем же набором фильтров
result: pass
source: automated
coverage_id: 04-08·D2
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_row_count_matches_the_counter

### 77. Файл начинается с метки порядка байтов UTF-8, чтобы кириллица открывалась без искажений (D-25)
expected: Файл начинается с метки порядка байтов UTF-8, чтобы кириллица открывалась без искажений (D-25)
result: pass
source: automated
coverage_id: 04-08·D3
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_body_starts_with_the_byte_order_mark; tests/test_pages/test_history_export.py#test_export_returns_a_csv_attachment

### 78. Колонки файла — время, канал, аккаунт, группа, заголовок объявления, статус, текст ошибки, идентификатор задачи; снапшот тела объявления не включается (D-28)
expected: Колонки файла — время, канал, аккаунт, группа, заголовок объявления, статус, текст ошибки, идентификатор задачи; снапшот тела объявления не включается (D-28)
result: pass
source: automated
coverage_id: 04-08·D4
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_header_has_eight_columns; tests/test_pages/test_history_export.py#test_export_header_carries_no_ad_body_column; tests/test_pages/test_history_export.py#test_export_row_matches_the_header_length; tests/test_pages/test_history_export.py#test_export_row_omits_the_ad_body_snapshot; tests/test_pages/test_history_export.py#test_export_first_line_is_the_header

### 79. Значение, начинающееся с символа формулы, экранируется и не интерпретируется табличным редактором как формула (T-04-16)
expected: Значение, начинающееся с символа формулы, экранируется и не интерпретируется табличным редактором как формула (T-04-16)
result: pass
source: automated
coverage_id: 04-08·D5
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_cell_defuses_a_formula_value; tests/test_pages/test_history_export.py#test_export_cell_defuses_a_formula_in_every_value_bearing_column; tests/test_pages/test_history_export.py#test_export_defuses_a_formula_coming_from_the_messenger

### 80. Потолок числа строк проверяется ДО начала потока: превышение даёт объяснение и предложение сузить период, а не обрезанный файл (D-27, T-04-33)
expected: Потолок числа строк проверяется ДО начала потока: превышение даёт объяснение и предложение сузить период, а не обрезанный файл (D-27, T-04-33)
result: pass
source: automated
coverage_id: 04-08·D6
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_cap_gives_no_file_when_exceeded; tests/test_pages/test_history_export.py#test_export_cap_explains_and_offers_to_narrow_the_period; tests/test_pages/test_history_export.py#test_export_cap_keeps_the_active_filters_in_the_explanation; tests/test_pages/test_history_export.py#test_export_cap_lets_the_boundary_selection_through; tests/test_pages/test_history_export.py#test_export_cap_is_checked_before_the_streaming_response

### 81. Маршрут выгрузки объявлен выше маршрута записи истории и не перехватывается им как значение параметра пути
expected: Маршрут выгрузки объявлен выше маршрута записи истории и не перехватывается им как значение параметра пути
result: pass
source: automated
coverage_id: 04-08·D7
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_route_order_precedes_the_record_route_in_the_source; tests/test_pages/test_history_export.py#test_export_route_order_survives_the_record_route_at_runtime

### 82. Выгрузка работает обычной ссылкой при выключенном JavaScript (D-26), и ссылка несёт те же фильтры, что адрес списка
expected: Выгрузка работает обычной ссылкой при выключенном JavaScript (D-26), и ссылка несёт те же фильтры, что адрес списка
result: pass
source: automated
coverage_id: 04-08·D8
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_link_needs_no_javascript; tests/test_pages/test_history_export.py#test_export_link_carries_the_active_filters; tests/test_pages/test_history_export.py#test_export_link_absent_when_there_is_nothing_to_export

### 83. Выгрузка отдаёт только записи текущего пользователя: условие владения стоит в базовом запросе (T-04-31)
expected: Выгрузка отдаёт только записи текущего пользователя: условие владения стоит в базовом запросе (T-04-31)
result: pass
source: automated
coverage_id: 04-08·D9
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_hides_other_users_records; tests/test_pages/test_history_export.py#test_export_requires_login

### 84. Чтение строк идёт потоком, поэтому память не растёт пропорционально размеру выборки (T-04-32)
expected: Чтение строк идёт потоком, поэтому память не растёт пропорционально размеру выборки (T-04-32)
result: pass
source: automated
coverage_id: 04-08·D10
requirement: HIST-03
covered_by: tests/test_pages/test_history_export.py#test_export_reads_the_selection_as_a_stream

### 85. Повторить можно только неуспешную запись: сервер отклоняет повтор успешной, а интерфейс кнопки не рисует (D-19)
expected: Повторить можно только неуспешную запись: сервер отклоняет повтор успешной, а интерфейс кнопки не рисует (D-19)
result: pass
source: automated
coverage_id: 04-09·D1
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_of_a_successful_record_is_refused_by_the_server; tests/test_pages/test_history_retry.py#test_successful_record_offers_no_retry_launcher; tests/test_pages/test_history_retry.py#test_history_detail_offers_no_retry_for_a_successful_record; tests/test_pages/test_history_retry.py#test_retry_is_eligible_for_an_unknown_status; tests/test_pages/test_history_retry.py#test_retry_is_eligible_for_a_disconnected_account_status

### 86. Повтор чужой записи отклоняется: владение проверяется на входе обработчика (T-04-35)
expected: Повтор чужой записи отклоняется: владение проверяется на входе обработчика (T-04-35)
result: pass
source: automated
coverage_id: 04-09·D2
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_of_another_users_record_is_refused_by_ownership; tests/test_pages/test_history_retry.py#test_retry_of_a_missing_record_queues_nothing; tests/test_pages/test_history_retry.py#test_retry_requires_login; tests/test_pages/test_history_retry.py#test_admin_history_offers_no_retry_launcher

### 87. Исчезнувшие объявление, группа или аккаунт останавливают повтор ДО очереди, и записи в журнал не появляется (D-21, T-04-39)
expected: Исчезнувшие объявление, группа или аккаунт останавливают повтор ДО очереди, и записи в журнал не появляется (D-21, T-04-39)
result: pass
source: automated
coverage_id: 04-09·D3
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_ad_is_gone; tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_group_is_gone; tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_account_is_gone; tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_account_is_not_active; tests/test_pages/test_history_retry.py#test_retry_precheck_runs_before_the_queue; tests/test_pages/test_history_retry.py#test_retry_availability_names_each_missing_entity

### 88. Исчерпанный лимит отправок отклоняет повтор до постановки в очередь и объясняется пользователю (T-04-36)
expected: Исчерпанный лимит отправок отклоняет повтор до постановки в очередь и объясняется пользователю (T-04-36)
result: pass
source: automated
coverage_id: 04-09·D4
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_is_refused_when_the_balance_is_exhausted; tests/test_pages/test_history_retry.py#test_retry_explains_the_exhausted_balance_to_the_user; tests/test_pages/test_history_retry.py#test_retry_balance_gate_runs_before_the_queue; tests/test_pages/test_history_retry.py#test_retry_does_not_touch_billing_itself

### 89. Повтор ставится тем же механизмом диспетчеризации, что боевая рассылка, и второго пути отправки не создаёт (D-18)
expected: Повтор ставится тем же механизмом диспетчеризации, что боевая рассылка, и второго пути отправки не создаёт (D-18)
result: pass
source: automated
coverage_id: 04-09·D5
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_of_an_eligible_record_queues_exactly_one_task — постановка по имени app.worker.tasks.retry_send с ар; tests/test_worker/test_tasks.py#test_retry_send_routes_queue_channels_to_redis (план 04-03) — маршрутизация трёх каналов; здесь НЕ дублируется

### 90. Запрос повтора с чужого источника отклоняется ДО любых действий (T-04-38, ASVS L1 V4.2.2)
expected: Запрос повтора с чужого источника отклоняется ДО любых действий (T-04-38, ASVS L1 V4.2.2)
result: pass
source: automated
coverage_id: 04-09·D6
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_rejects_a_cross_site_origin; tests/test_pages/test_history_retry.py#test_retry_rejects_a_cross_site_fetch_context; tests/test_pages/test_history_retry.py#test_retry_accepts_its_own_origin; tests/test_pages/test_history_retry.py#test_retry_lets_a_headerless_request_through; tests/test_pages/test_history_retry.py#test_retry_origin_check_runs_before_the_record_is_read; tests/test_pages/test_history_retry.py#test_retry_origin_check_documents_its_boundary

### 91. Одно действие пользователя порождает не более одной постановки: перенаправление после формы плюс заявка в памяти процесса (T-04-37)
expected: Одно действие пользователя порождает не более одной постановки: перенаправление после формы плюс заявка в памяти процесса (T-04-37)
result: pass
source: automated
coverage_id: 04-09·D7
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_answers_with_a_redirect_not_a_page; tests/test_pages/test_history_retry.py#test_retry_of_a_busy_record_queues_no_second_task; tests/test_pages/test_history_retry.py#test_retry_releases_the_slot_after_success; tests/test_pages/test_history_retry.py#test_retry_releases_the_slot_after_an_exception; tests/test_pages/test_history_retry.py#test_retry_slot_claim_is_synchronous; tests/test_pages/test_history_retry.py#test_retry_slot_release_is_a_discard_in_a_finally_block

### 92. Подтверждение идёт общей панелью проекта с настоящей формой, и текст называет отправку ТЕКУЩЕГО содержимого объявления (D-23, D-17, T-04-40)
expected: Подтверждение идёт общей панелью проекта с настоящей формой, и текст называет отправку ТЕКУЩЕГО содержимого объявления (D-23, D-17, T-04-40)
result: pass
source: automated
coverage_id: 04-09·D8
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_confirmation_panel_carries_a_real_form; tests/test_pages/test_history_retry.py#test_retry_confirmation_panel_names_the_current_ad_content; tests/test_pages/test_history_retry.py#test_retry_uses_the_shared_confirmation_panel; tests/test_templates/test_components.py#test_modal_guard_is_inherited_by_every_consumer; tests/test_pages/test_responsive_markup.py#test_no_rendered_page_calls_browser_dialog — браузерного диалога не появилось

### 93. Панель эмитится вне разметки записи и переживает подмену бесконечной прокруткой
expected: Панель эмитится вне разметки записи и переживает подмену бесконечной прокруткой
result: pass
source: automated
coverage_id: 04-09·D9
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_panel_is_emitted_outside_the_record_markup; tests/test_pages/test_history_retry.py#test_history_detail_panel_is_outside_the_record_markup; tests/test_pages/test_history_retry.py#test_retry_launcher_survives_the_infinite_scroll_partial

### 94. Инвентаризация мест подтверждения пересчитана счётом по файлам после правки шаблонов
expected: Инвентаризация мест подтверждения пересчитана счётом по файлам после правки шаблонов
result: pass
source: automated
coverage_id: 04-09·D10
requirement: HIST-04
covered_by: tests/test_templates/test_components.py#test_modal_site_inventory — 9 импортёров, 6 имён события, 15 мест; grep -rl 'components/modal.html' app/templates → 9 файлов; grep -o 'modal-open-[a-z-]*' минус компонент → 15 вхождений, 6 различных имён

### 95. Признак доступности повтора считает сервер, и число запросов не растёт с числом записей
expected: Признак доступности повтора считает сервер, и число запросов не растёт с числом записей
result: pass
source: automated
coverage_id: 04-09·D11
requirement: HIST-04
covered_by: tests/test_pages/test_history_retry.py#test_retry_availability_takes_a_bounded_number_of_queries; tests/test_pages/test_history_retry.py#test_retry_availability_ignores_successful_records; tests/test_pages/test_history_retry.py#test_retry_availability_is_computed_by_the_server

## Summary

total: 95
passed: 95
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-04-1
  truth: "Дашборд отрисован по макету new_broadcaster_design.html"
  status: fixed_in_place
  reason: "User reported: страница дашборда не соответствует шаблону (скрин 2026-08-14_19-04-23.png)"
  severity: blocker
  test: 1
  root_cause: |
    Три независимых дефекта CSS/раскладки, все — расхождение с макетом, не с данными.
    Данные на странице верные: числа плиток, строки ближайших отправок, лента и
    подписи сетки приходят и отрисовываются.
  artifacts:
    - path: "app/static/css/app.css"
      issue: "[data-upbadge] не задавал размер .msg__glyph. Макрос messenger_icon вызывается с size='' по уговору «размер задаёт раздел» (его докстринг); раздел истории свою половину уговора выполняет правилом [data-hrow] [data-area=head] svg {13px}, дашборд — не выполнял. svg с одним viewBox без width/height растягивается до контейнера: иконки каналов выросли в разы, высота строки «Ближайших отправок» — следом, подпись канала уехала за правый край (на скрине обрезана до «Tele», «Wha»)."
    - path: "app/static/css/app.css"
      issue: "[data-heatcell] не задавал высоту. Ячейка — пустой span, а на [data-heatmap] стоит align-items: center (ради центрирования подписей дней), поэтому высота считалась по содержимому и равнялась нулю: сетка активности показывала подписи дней и часов над пустым местом (видно на скрине)."
    - path: "app/templates/dashboard.html"
      issue: "«Ближайшие отправки» и «Живая лента» лежали прямыми детьми вертикальной стопки [data-stack] и занимали полную ширину каждая. Оба шаблона называют себя «левой» и «правой половиной пары» в комментариях, но в макете это сетка repeat(auto-fit, minmax(330px, 1fr)) — пара существовала в комментариях и не существовала на экране."
  missing:
    - "[data-upbadge]: размер глифа 11px + пилюля макета (mono 10px, padding 4px 8px 4px 6px, radius 6px), тон — атрибутом data-channel"
    - "[data-heatcell]: явные width/height 14px, не зависящие от выравнивания родителя"
    - "[data-dashpair]: сетка в две колонки вокруг пары, схлопывание — средствами auto-fit, без медиазапроса"
  resolved_by: "исправлено напрямую в этой сессии по указанию пользователя «исправляй верстку» (без gap-плана)"
  resolved_at: 2026-08-14

- gap_id: G-04-2
  truth: "Дашборд отрисован по макету — вторая сверка по скриншоту 2026-08-14_20-35-16.png"
  status: fixed_in_place
  reason: "Владелец: «мне не нравится блок Активность за неделю», плюс сплошная сверка всех элементов с макетом по его просьбе"
  severity: major
  test: 1
  root_cause: |
    Сплошная сверка дашборда с new_broadcaster_design.html дала два расхождения
    сверх исправленных в G-04-1. Плитки, пара блоков, строки отправок, бейджи,
    точки статуса, пульс real-time, токены фона/рамки/радиуса — совпали точно.
  artifacts:
    - path: "app/templates/dashboard/includes/heatmap.html"
      issue: "Сетка 7×24 (решение D-09) вместо бар-чарта макета. Ячейка жёстко 14px при width: max-content — блок занимал ~440px в карточке ~1550px, справа мёртвое поле в треть экрана."
    - path: "app/templates/dashboard.html"
      issue: "«Ближайшие отправки» шли через card_open(title=...) и получали разделительную линию .card__head, которой в макете нет ни у одной карточки дашборда. Соседняя «Живая лента» линии не имела — две карточки одной пары выглядели по-разному."
  missing:
    - "Бар-чарт макета: 28 столбцов (7 суток × 4 доли по 6 часов), высота 120px, долевая ширина столбца, подписи суток снизу"
    - "activity_chart() — чистая свёртка часовой сетки в столбцы, без второго запроса"
    - "[data-blockhead] — одна шапка на три блока дашборда, без разделителя"
  decisions:
    - "D-09 ОТМЕНЕНО владельцем: бар-чарт вместо сетки 7×24 (запись в 04-CONTEXT.md)"
    - "D-10, D-11, D-12 остались в силе; activity_heatmap не удалён — доступен Фазе 6"
    - "Подпись единицы честная («отправок за 6 часов»), а не «отправок в час» из макета: столбец покрывает шесть часов"
  open:
    - "DASH-04 и критерий 2 в ROADMAP.md говорят «heatmap», экран показывает бар-чарт — расхождение с буквой критерия НЕ закрыто, решение за владельцем"
  resolved_by: "исправлено напрямую в этой сессии по решению владельца в чекпоинте"
  resolved_at: 2026-08-14

## Deferred Follow-Ups

[none]

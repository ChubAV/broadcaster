---
phase: 04-dashbord-i-istoriya
verified: 2026-08-15T07:57:52Z
status: gaps_found
score: 8/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Пользователь, открывший дашборд, видит ... то, какие воркеры его аккаунтов сейчас онлайн (SC-1, третий пункт; DASH-05)"
    status: partial
    reason: "Дашборд отвечает ЧИСЛОМ, а не перечнем. Индикатор шелла печатает «воркеров онлайн · N» и несёт data-sessions-online / data-sessions-total; какой именно аккаунт онлайн, а какой отвалился, с дашборда не прочитать. Источник — счёт MessengerAccount.status == 'active' скалярным подзапросом, поаккаунтной разбивки в контракт шелла не заведено."
    artifacts:
      - path: app/pages/common.py
        issue: "get_shell_context отдаёт только скаляры sessions_online / sessions_total (строки 302-309, 362-363) — перечня аккаунтов с их статусами в контракте нет"
      - path: app/templates/base.html
        issue: "строки 104-112: единственная пилюля с агрегатом; поаккаунтного блока нет"
      - path: app/templates/dashboard.html
        issue: "в теле дашборда блока воркеров нет вовсе — критерий закрывается индикатором шапки шелла"
    missing:
      - "Поаккаунтный срез состояния воркеров на дашборде (какой аккаунт онлайн / офлайн), либо принятый override с формулировкой, что агрегатного индикатора достаточно"
  - truth: "Повторное нажатие «Повторить» в пределах одного процесса не ставит вторую задачу (04-09; прохибиция «MUST NOT let one user retry action dispatch more than one send ... double submit, a refresh, or a back-button POST»)"
    status: failed
    reason: "_release_retry_slot стоит в finally, который закрывается сразу после celery.send_task и ДО отправки 302. Заявка держится только на время самого обработчика, поэтому она останавливает лишь ПЕРЕСЕКАЮЩИЕСЯ во времени запросы, а два последовательных нажатия ставят две необратимые отправки. Собственный тест проекта это и утверждает: test_retry_releases_the_slot_after_success ассертит len(env.queued) == 2. Тест запущен верификатором и ЗЕЛЁНЫЙ — то есть поведение подтверждено, а не предположено. Докстринг обработчика при этом утверждает обратное."
    artifacts:
      - path: app/pages/history.py
        issue: "строки 769-771 — докстринг «второе нажатие в пределах процесса второй задачи не ставит»; строки 790-835 — заявка занимается и освобождается внутри одного обработчика; строки 349-360 — комментарий подаёт многопроцессность как ЕДИНСТВЕННОЕ ограничение реестра"
      - path: tests/test_pages/test_history_retry.py
        issue: "строки 703-720: тест закрепляет две поставленные задачи на два последовательных POST и называется «releases the slot after success» — спецификация утверждает ровно то, что прохибиция запрещает"
    missing:
      - "Либо окно удержания заявки (cooldown) со снятием освобождения с успешного пути, либо честный докстринг/комментарий и переформулированная прохибиция — сейчас код и его собственное описание расходятся"
      - "Тест, закрепляющий выбранное поведение под своим именем (сейчас имя теста скрывает, что он проверяет ДВЕ отправки)"
deferred: []
---

# Phase 4: Дашборд и история — Verification Report

**Phase Goal:** Пользователь видит, что происходит с его рассылками прямо сейчас и что произошло раньше, и может действовать по неудачным отправкам.
**Verified:** 2026-08-15T07:57:52Z
**Status:** gaps_found
**Re-verification:** No — initial verification (previous VERIFICATION.md отсутствовал, #2868)

## Goal Achievement

### Observable Truths

Источники must-haves: ROADMAP Success Criteria (контракт, 5 пунктов) + must_haves.truths из frontmatter десяти планов (сведены к пяти несущим утверждениям, не покрытым SC напрямую).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC-1: дашборд показывает метрики за сутки, ближайшие отправки И то, какие воркеры аккаунтов онлайн | ✗ FAILED (частично) | Метрики и ближайшие отправки — VERIFIED (см. ниже). Третий пункт закрыт АГРЕГАТОМ: `base.html:111` печатает «воркеров онлайн · {{ sessions_online }}», `common.py:302-309` считает `MessengerAccount.status == 'active'` одним числом. Какие именно воркеры онлайн — с экрана не прочитать |
| 2 | SC-2: живая лента обновляется без перезагрузки + график активности за неделю | ✓ VERIFIED | `dashboard.html:116` — `hx-get="/dashboard/feed" hx-trigger="every 20s"` на стабильном `#dash-feed`; `partial_feed.html` не несёт ни одного атрибута опроса; маршрут `dashboard_feed.py:54`; `activity_chart` даёт 28 столбцов. Тесты `test_dashboard_feed_container_polls`, `test_dashboard_feed_partial_carries_no_polling_attributes`, `test_dashboard_feed_polling_has_no_stop_branch` — зелёные (запущены верификатором). Ручная приёмка UAT #2 — pass |
| 3 | SC-3: фильтр по каналу/статусу/периоду + выгрузка ИМЕННО отфильтрованного | ✓ VERIFIED | Три оси чипсов (`list.html:56-63`), значения строятся из констант аналитики; список, счётчик и выгрузка навешивают условия ОДНОЙ функцией `apply_history_filters`; `/history/export` объявлен выше `/history/{log_id}`. Тесты `test_export_row_count_matches_the_counter`, `test_export_honours_the_status_filter`, `test_export_route_order_survives_the_record_route_at_runtime` — зелёные. Ручная приёмка UAT #6 — pass |
| 4 | SC-4: прочитать текст ошибки, скопировать одним действием, повторить из записи | ✓ VERIFIED | `history_card.html:203-216` — полный экранированный текст + `data-clamp` (раскрытие без JS, CSS `app.css:996-1013`); `copy_button` собирает диагностический блок и не сообщает об успехе при неудаче (`mark(done)` выходит при `!done`); повтор: форма → `/history/{id}/retry` → `celery.send_task` → `retry_send` → `build_dispatch_task` → `dispatch_send_tasks` (три канала). Ручная приёмка UAT #3 и #5 — pass (реальная доставка в группу) |
| 5 | SC-5: дашборд и история пригодны на мобильных ширинах | ✓ VERIFIED | 250 тестов `test_responsive_markup.py` + `test_shell.py` + `test_components.py` зелёные (запущены верификатором); ручная приёмка UAT #8 и #9 на 320/860/900/1080 px — pass после закрытия G-04-1/G-04-2 |
| 6 | 04-09: повторное нажатие в пределах одного процесса не ставит вторую задачу | ✗ FAILED | Заявка освобождается в `finally` ДО отправки 302; собственный тест проекта `test_retry_releases_the_slot_after_success` ассертит `len(env.queued) == 2` и ЗЕЛЁНЫЙ при запуске верификатором. Докстринг `history.py:769-771` утверждает обратное |
| 7 | 04-01/04-35: у аналитики и фильтров истории ровно одно определение, его импортируют история и админка | ✓ VERIFIED | `app/pages/history.py:10-19` и `app/pages/admin.py:10-13` импортируют `apply_history_filters` / `history_filter_params` из `send_analytics`; собственных копий условий нет |
| 8 | 04-03: повтор идёт тем же диспетчером, второго пути отправки нет, все три канала | ✓ VERIFIED | `tasks.py:400-407` — `build_dispatch_task(...)` → `dispatch_send_tasks([task])`; сам диспетчер маршрутизирует `tg_user` в Celery-очередь `telegram`, `wa`/`max` — `rpush`-ем в Redis-очередь аккаунта; формат payload не изменён. `send_message_once` и адаптеры из `retry_send` не зовутся |
| 9 | 04-10: у вопроса «сколько было ошибок» один ответ; JSON-сводка считает три статуса | ✓ VERIFIED | `app/routes/history.py:63` зовёт `send_metrics`; `fail_count = metrics.failed`, где `failed` = «не ok». Второго определения сводки в `SendLogRepository` не осталось |
| 10 | 04-02: ревизия 0016 — составной индекс (user_id, sent_at), down_revision 0015, одна линия истории | ✓ VERIFIED | `alembic/versions/0016_send_logs_user_sent_at.py:43-54`; имя `ix_send_logs_user_id_sent_at`; тест миграции зелёный |

**Score:** 8/10 truths verified (0 present, behavior-unverified)

### Прохибиции (must-NOT), judgment-tier

| # | Прохибиция | План | Статус | Evidence |
|---|-----------|------|--------|----------|
| P1 | MUST NOT silently exclude unclassifiable send records from tile counts | 04-01 | ✓ VERIFIED | `send_metrics`: `failed = (status != ok)`, а не членство в перечне; `groups` считает distinct `group_id`, запись с пустой группой из `total` не выпадает (`send_analytics.py:178-206`) |
| P2 | MUST NOT silently exclude unclassifiable records from the activity grid | 04-04 | ✓ VERIFIED | `activity_heatmap`: клампы вместо `continue` (`send_analytics.py:352-360`); тест `test_heatmap_counts_record_without_group_or_messenger` |
| P3 | MUST NOT indicate a successful copy when the clipboard write did not occur | 04-07 | ✓ VERIFIED | `mark(done)` выходит при `!done`; запасной путь через `document.execCommand` возвращает реальный результат (`history_card.html:107-112`) |
| P4 | MUST NOT present retry as re-sending the archived snapshot | 04-09 | ✓ VERIFIED | Текст панели: «Уйдёт ТЕКУЩЕЕ содержимое объявления из базы, а не то, что показано в этой записи» (`history_card.html:178`); тот же смысл в `RETRY_NOTICES[queued]` |
| P5 | MUST NOT dispatch a send for a cross-site request | 04-09 | ✓ VERIFIED | `_is_same_origin` сверяет `Sec-Fetch-Site`, затем хост `Origin`; отказ — 403 ДО чтения записи. Названная граница (оба заголовка отсутствуют → пропуск) выписана в докстринге и в 04-SECURITY.md |
| P6 | MUST NOT let one user retry action dispatch more than one send (double submit / refresh / back-button POST) | 04-09 | ⚠️ FLAGGED — unverified-prohibition, human review recommended | Обновление страницы закрыто перенаправлением после POST; двойной клик закрыт ПАНЕЛЬЮ Alpine (ручная приёмка UAT #4 — pass). Серверная линия НЕ держит: два последовательных POST ставят две задачи, и это закреплено собственным тестом проекта. См. gap 2 |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/application/analytics/send_analytics.py` | публичный контракт аналитики | ✓ VERIFIED | 800 строк; `send_metrics`, `activity_heatmap`, `activity_chart`, `upcoming_sends`, `recent_feed`, `apply_history_filters`, `history_count`; импортируется дашбордом, историей, админкой и `routes/history.py` |
| `app/templates/dashboard/includes/metric_tile.html` | макрос плитки с дельтой | ✓ VERIFIED | `macro metric_tile`; зовётся четырежды из `dashboard.html:43-54` |
| `app/templates/dashboard/includes/heatmap.html` | сетка 7×24 (D-09) | ⚠️ УДАЛЁН НАМЕРЕННО | D-09 отменён владельцем на приёмке; показ заменён `activity_chart.html`. Часовая раскладка `activity_heatmap` в коде сохранена для Фазы 6. ROADMAP/REQUIREMENTS переформулированы (коммит 0e5148b) — не gap |
| `app/templates/dashboard/includes/activity_chart.html` | бар-чарт 28 столбцов | ✓ VERIFIED | `macro activity_chart`; импортируется `dashboard.html:5`, зовётся при `chart_view.peak` |
| `app/templates/dashboard/includes/upcoming_row.html` | строка ближайшей отправки | ✓ VERIFIED | `macro upcoming_row`; ссылка в редактор объявления + бейдж причины |
| `app/pages/dashboard_feed.py` | маршрут ленты вне страничного роутера | ✓ VERIFIED | 77 строк; включён напрямую `app/main.py:91`, ДО `pages_router`; собственный гард `get_user_from_cookie` |
| `app/templates/dashboard/partial_feed.html` | только строки, без атрибутов опроса | ✓ VERIFIED | Ни одного `hx-trigger`/`hx-get`; пустое состояние внутри паршала |
| `app/templates/dashboard/includes/feed_row.html` | строка-ссылка в запись истории | ✓ VERIFIED | `macro feed_row`, `<a href="/history/{{ row.id }}">` |
| `app/templates/dashboard/includes/recent_send_card.html` | — | ⚠️ УДАЛЁН НАМЕРЕННО | Блок «Последние отправки» заменён лентой; недостижимого шаблона не оставлено. Файл числится в `files_reviewed_list` 04-REVIEW.md ошибочно — не gap |
| `app/templates/history/includes/filter_chips.html` | макрос чипсов-ссылок | ✓ VERIFIED | `macro filter_chips`; импортируется `list.html:8`; чипсы — `<a>`, работают без JS |
| `app/templates/history/includes/history_card.html` | блок ошибки + clamp + копирование + повтор | ✓ VERIFIED | 230 строк; `data-clamp`, `copy_button`, `retry_trigger`, `retry_modal` |
| `app/templates/history/detail.html` | страница записи, полный текст ошибки | ✓ VERIFIED | 99 строк; `data-clamp` отсутствует намеренно; те же макросы копирования и повтора |
| `app/pages/history.py` | фильтры, выгрузка, повтор | ✓ VERIFIED | 964 строки; `/history/export` объявлен выше `/history/{log_id}` |
| `app/worker/tasks.py` → `retry_send` | вход повтора на три канала | ✓ VERIFIED | `tasks.py:271-415`; повторная проверка владения, целости тройки, статуса аккаунта, черновика и `group.is_active` |
| `alembic/versions/0016_send_logs_user_sent_at.py` | составной индекс | ✓ VERIFIED | 54 строки; `down_revision = "0015"` |
| `.planning/phases/04-dashbord-i-istoriya/04-SECURITY.md` | сводный регистр угроз | ✓ VERIFIED | Существует, 54 КБ, содержит T-04-38 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `app/pages/dashboard.py` | `send_analytics.py` | импорт `send_metrics`, `activity_heatmap`, `activity_chart`, `upcoming_sends`, `recent_feed` | ✓ WIRED | `dashboard.py:5-11`, вызовы на строках 79, 90-92, 97, 106 |
| `app/pages/history.py` | `send_analytics.py` | `apply_history_filters` / `history_filter_params` / `history_count` | ✓ WIRED | `history.py:10-19`; список, паршал, счётчик и выгрузка зовут одни функции |
| `app/pages/admin.py` | `send_analytics.py` | импорт фильтров вместо приватных имён истории | ✓ WIRED | `admin.py:10-13` |
| `app/main.py` | `app/pages/dashboard_feed.py` | `include_router` мимо страничного роутера | ✓ WIRED | `main.py:27` (импорт), `main.py:91` (включение до `pages_router`) |
| `app/templates/dashboard.html` | `/dashboard/feed` | `hx-get` + `hx-trigger` | ✓ WIRED | `dashboard.html:116` |
| `app/templates/dashboard.html` | `activity_chart.html` | импорт макроса | ✓ WIRED | `dashboard.html:5`, вызов на 133 |
| `app/templates/history/list.html` | `filter_chips.html` | импорт макроса | ✓ WIRED | `list.html:8`, три вызова на 57-59 |
| `app/templates/history/list.html` | `/history/export` | ссылка с теми же параметрами фильтра | ✓ WIRED | `list.html:101` — цикл проброса `filter_params` |
| `app/pages/history.py` | `app/worker/tasks.py` | `celery.send_task("app.worker.tasks.retry_send")` | ✓ WIRED | `history.py:269, 829-831`; локальный импорт сохранён |
| `app/pages/history.py` | `app/services/billing_cache.py` | `check_balance_cached` в предпроверке | ✓ WIRED | `history.py:38, 819`; стоит ДО `send_task` (тест `test_retry_balance_gate_runs_before_the_queue`) |
| `history_card.html` | `components/modal.html` | подтверждение общей панелью | ✓ WIRED | `history_card.html:40, 173-178` |
| `history_card.html` | `app/static/css/app.css` | модификатор `data-clamp` поверх `data-longtext` | ✓ WIRED | `app.css:996-1013` |
| `app/worker/tasks.py` | `app/application/scheduling/use_cases.py` | `build_dispatch_task` | ✓ WIRED | `tasks.py:400`; определение — `use_cases.py:69`, зовётся и планировщиком |
| `app/routes/history.py` | `send_analytics.py` | JSON-сводка зовёт `send_metrics` | ✓ WIRED | `routes/history.py:7, 63` |
| `alembic/0016` | `alembic/0015` | `down_revision` | ✓ WIRED | `down_revision = "0015"` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `dashboard.html` плитки | `metrics` | `send_metrics` → один `select` с условными агрегатами по `send_logs` | Да | ✓ FLOWING |
| `dashboard.html` график | `chart_view` | `activity_chart(await activity_heatmap(...))` → `session.stream(select(SendLog.sent_at))` | Да | ✓ FLOWING |
| `dashboard.html` ближайшие | `upcoming` | `upcoming_sends` → `select(Schedule, Ad, MessengerAccount)` + запрос флагов групп | Да | ✓ FLOWING |
| `partial_feed.html` | `feed` | `recent_feed` → `select(...).order_by(sent_at.desc()).limit(8)` | Да | ✓ FLOWING |
| `base.html` индикатор | `sessions_online` | `get_shell_context` → `count(MessengerAccount where status='active')` | Да (но только агрегат) | ⚠️ FLOWING, НО НЕПОЛНО для SC-1 |
| `history/list.html` линейка | `history_total` | `history_count` с теми же фильтрами | Да | ✓ FLOWING |
| `history/list.html` карточки | `logs` | `select(SendLog, Group)` + `retry_availability` | Да | ✓ FLOWING |
| CSV-выгрузка | строки файла | `db.stream(query)` → `export_row` | Да | ✓ FLOWING |
| `history_card.html` кнопка повтора | `can_retry` / `retry_reason` | `retry_availability` → два запроса по `Ad.status` и `MessengerAccount.status` | Да | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Свёртка часовой сетки в 28 столбцов | `python -c "activity_chart(HeatmapView(...))"` | `bars_len 28`, `first_bucket 5`, `last_bucket 3`, `peak 5` | ✓ PASS |
| Экранирование формулы в ячейке файла | `export_cell("=1+1")`, `export_cell("\t=x")` | `'=1+1`, `'\t=x` — ведущий апостроф проставлен | ✓ PASS |
| Метка порядка байтов и восемь колонок | `len(EXPORT_HEADER)`, `EXPORT_BOM` | `8`, `'\ufeff'` (U+FEFF) | ✓ PASS |
| Хронологический порядок столбцов через локальную полночь (CR-03) | `pytest ...::test_chart_bars_run_in_chronological_order_across_local_midnight` | 1 passed | ✓ PASS |
| Подпись дня соответствует своему столбцу | `pytest ...::test_chart_bar_falls_under_its_own_day_label` | 1 passed | ✓ PASS |
| Занятая заявка не даёт второй постановки (при пересечении) | `pytest ...::test_retry_of_a_busy_record_queues_no_second_task` | 1 passed | ✓ PASS |
| Два ПОСЛЕДОВАТЕЛЬНЫХ повтора ставят ДВЕ задачи | `pytest ...::test_retry_releases_the_slot_after_success` | 1 passed — тест ассертит `len(env.queued) == 2` | ✗ FAIL (прохибиция P6) |
| Повтор черновика не доезжает до очереди (CR-01) | `pytest ...::test_retry_of_a_draft_ad_does_not_reach_the_queue` | 1 passed | ✓ PASS |
| Кнопка называет черновик и выключенную группу (CR-01/CR-02) | `pytest ...::test_availability_names_the_draft_ad_and_the_switched_off_group` | 1 passed | ✓ PASS |
| Число строк файла равно счётчику | `pytest ...::test_export_row_count_matches_the_counter` | 1 passed | ✓ PASS |
| Маршрут выгрузки не перехватывается маршрутом записи | `pytest ...::test_export_route_order_survives_the_record_route_at_runtime` | 1 passed | ✓ PASS |
| Опрос ленты: атрибуты на странице, не в паршале | `pytest ...::test_dashboard_feed_container_polls`, `...::test_dashboard_feed_partial_carries_no_polling_attributes` | 2 passed | ✓ PASS |
| Фильтры переживают бесконечную прокрутку | `pytest ...::test_infinite_scroll_keeps_filters` | passed | ✓ PASS |
| Индикатор воркеров на дашборде | `pytest ...::test_dashboard_shows_the_sessions_indicator` | 1 passed (проверяет присутствие пилюли и подпись, НЕ перечень) | ✓ PASS (но см. gap 1) |
| Файлы тестов фазы целиком | `pytest test_send_analytics test_dashboard test_history test_history_export test_history_retry test_htmx_preserved test_routes/test_history test_0016 test_worker/test_tasks test_scheduling_use_cases -q` | **330 passed**, exit 0 | ✓ PASS |
| Разметка/шелл/компоненты | `pytest test_responsive_markup test_shell test_components -q` | **250 passed**, exit 0 | ✓ PASS |
| Полная суита `uv run pytest tests/` | — | ? SKIP — прогон превысил 900 с и был снят по таймауту песочницы; заменён двумя целевыми прогонами выше (580 тестов, 0 падений) | ? SKIP |
| `session.get(MessengerAccount, None)` (WR-02) | inline python | Возвращает `None` с SAWarning, не исключение — гард `if not account` его ловит | ✓ PASS (info) |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| — | `find scripts -path '*/tests/probe-*.sh'` | Проб в проекте нет; ни один PLAN/SUMMARY фазы их не объявляет | n/a — SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DASH-01 | 04-01, 04-02, 04-10 | Метрики отправок за последние сутки | ✓ SATISFIED | `send_metrics` со скользящим окном 24 ч + дельта; четыре плитки в `dashboard.html:43-54` |
| DASH-02 | 04-04, 04-10 | Список ближайших запланированных отправок | ✓ SATISFIED | `upcoming_sends` + `upcoming_row`; сортировка по `next_run_at`, пометки причин, лимит 8 |
| DASH-03 | 04-05, 04-10 | Живая лента последних событий отправки | ✓ SATISFIED | `/dashboard/feed` + `hx-trigger every 20s`; UAT #2 pass |
| DASH-04 | 04-02, 04-04, 04-10 | График активности отправок за неделю | ✓ SATISFIED | `activity_chart` — 28 столбцов, окно 7 суток с якорем на локальную полночь; формулировка требования приведена к бар-чарту владельцем |
| DASH-05 | 04-05, 04-10 | Какие воркеры аккаунтов сейчас онлайн | ✗ BLOCKED (частично) | Показано ЧИСЛО активных сессий, а не перечень. См. gap 1. Решение о источнике («Фаза 1 D-19») задокументировано в `04-CONTEXT.md:17`, но «какие» им не закрывается |
| HIST-01 | 04-01, 04-02, 04-06, 04-10 | Фильтр по каналу, статусу и периоду | ✓ SATISFIED | Три оси чипсов + выпадающий список аккаунта; три статуса, три канала, четыре периода |
| HIST-02 | 04-07, 04-10 | Текст ошибки виден и копируется | ✓ SATISFIED | Полный экранированный текст + clamp без JS + кнопка копирования с проверкой доступности буфера; UAT #3 pass |
| HIST-03 | 04-02, 04-08, 04-10 | Выгрузка отфильтрованной истории | ✓ SATISFIED | Потоковый CSV, BOM, `;`, экранирование формул, потолок 50 000 ДО потока; UAT #6, #7 pass |
| HIST-04 | 04-03, 04-09, 04-10 | Повтор отправки из записи истории | ✓ SATISFIED | Полный путь до реальной доставки (UAT #5 pass). Остаток по защите от двойной постановки — gap 2, самой возможности повтора не отменяет |

**Осиротевших требований нет:** все девять идентификаторов, отнесённых REQUIREMENTS.md к Фазе 4, объявлены как минимум одним планом; лишних идентификаторов планы не объявляют.

⚠️ **Бухгалтерия трассируемости не обновлена.** В `.planning/REQUIREMENTS.md` все девять требований Фазы 4 остаются `- [ ]` (строки 97-108) и `Pending` в таблице (строки 221-229), хотя фаза исполнена 10/10 и UAT закрыт. 04-05-SUMMARY объясняет это тем, что отметка ждала завершения 04-10 — 04-10 завершён. Это учётный остаток, а не дефект кода.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` | — | Ни одного маркера долга ни в одном из файлов фазы (сплошной обход прикладных модулей, шаблонов и ревизии) |
| `app/repositories/send_log.py` | 37 | Мёртвый метод `list_for_user_with_details` без потребителей | ℹ️ Info | WR-11 из 04-REVIEW; на поведение не влияет |
| `app/pages/history.py` | 649-683 | Исключение внутри генератора выгрузки даёт обрезанный файл со статусом 200 | ⚠️ Warning | WR-10; форма ответа потокового CSV не позволяет сменить код после первого фрагмента — остаток назван, но не закрыт |
| `app/pages/history.py` | 415-439 | Вторичные запросы `Ad.id.in_(...)` / `MessengerAccount.id.in_(...)` без предиката владельца | ⚠️ Warning | WR-07. Идентификаторы приходят ИЗ записей самого пользователя, поэтому утечки на сегодняшних данных нет; предикат отсутствует как второй слой |
| `app/application/analytics/send_analytics.py` | 539-545 | То же по `Group.id.in_(...)` в `upcoming_sends` | ⚠️ Warning | WR-07, та же оценка |
| `app/pages/history.py` | 769-771 | Докстринг утверждает свойство, которого код не даёт | 🛑 Blocker | Часть gap 2: описание расходится с поведением, закреплённым собственным тестом |
| `app/templates/history/detail.html` | 47 | `messenger_icon` зовётся без ограничения известными типами (в карточке ограничение есть) | ℹ️ Info | Потенциальный utility-класс на неизвестном типе; инвентаризационные тесты зелёные |

**Замечания code review, закрытые к моменту верификации:** CR-01 (черновик объявления в очередь) — закрыт на всех трёх слоях (`history.py:807-814`, `tasks.py:381-383`, `retry_availability:445`); CR-02 (`group.is_active`) — закрыт там же (`history.py:811`, `tasks.py:389-395`, `retry_availability:449`); CR-03 (порядок столбцов графика) — закрыт якорем на локальную полночь (`send_analytics.py:317-329`) и подтверждён двумя названными тестами.

### Human Verification Required

Статус фазы — `gaps_found`, поэтому раздел не является точкой выхода. Одна позиция всё же требует решения человека, а не доработки кода:

#### 1. Достаточно ли агрегата для DASH-05 (gap 1)

**Test:** Открыть дашборд с двумя активными и одним отвалившимся messenger-аккаунтом.
**Expected:** По формулировке SC-1 и REQUIREMENTS.md пользователь должен увидеть, КАКИЕ воркеры онлайн. Фактически он видит «воркеров онлайн · 2» без указания, какой именно аккаунт отвалился.
**Why human:** Решение об источнике («Фаза 1 D-19, читаем `MessengerAccount.status` через шелл») зафиксировано в `04-CONTEXT.md:17` как не подлежащее переобсуждению, но оно отвечает на вопрос «откуда брать», а не «сколько показывать». Приемлемость агрегата вместо перечня — продуктовое решение владельца.

**Это выглядит намеренным.** Чтобы принять отступление, добавьте во frontmatter этого файла:

```yaml
overrides:
  - must_have: "Пользователь видит, какие воркеры его аккаунтов сейчас онлайн (DASH-05, SC-1)"
    reason: "Агрегатного индикатора шелла (воркеров онлайн · N из MessengerAccount.status, контракт Фазы 1 D-19) достаточно; поаккаунтный срез живёт в разделе аккаунтов, а состояние контейнеров по каналам — в Фазе 6"
    accepted_by: "{имя}"
    accepted_at: "{ISO timestamp}"
```

и перезапустите верификацию.

### Gaps Summary

Фаза построена и работает: пять из шести несущих контрактов ROADMAP выполнены целиком, все девять артефактных цепочек проведены от запроса к базе до разметки, 580 тестов фазы зелёные, ручная приёмка закрыта 95/95, три критических замечания code review (CR-01/02/03) действительно исправлены в коде, а не только в отчёте. Ни одного маркера долга в файлах фазы нет.

Два остатка мешают признать цель достигнутой без решения человека.

**Первый — DASH-05 отвечает не на тот вопрос.** SC-1 и REQUIREMENTS.md обещают «какие воркеры онлайн», а дашборд показывает одно число. Это не забытая работа, а перенесённое из Фазы 1 решение об источнике данных, доведённое до экрана в агрегатной форме. Дефекта в коде нет — есть расхождение между формулировкой требования и построенным. Закрывается либо поаккаунтным срезом, либо override-ом.

**Второй — серверная защита повтора от двойной постановки не работает, и код утверждает обратное.** Заявка `_RETRY_IN_FLIGHT` держится только внутри обработчика и снимается в `finally` до отправки 302, поэтому останавливает лишь пересекающиеся во времени запросы. Два последовательных нажатия ставят две необратимые отправки в стороннюю группу и тратят два сообщения баланса — и это не гипотеза: собственный тест проекта `test_retry_releases_the_slot_after_success` ассертит ровно `len(env.queued) == 2`, верификатор запустил его и получил зелёный. Прохибиция плана 04-09 при этом запрещает дублирование «by a double submit, a refresh, or a back-button POST». Обновление страницы закрыто перенаправлением, двойной клик закрыт панелью Alpine и подтверждён ручной приёмкой (UAT #4), но при выключенном JavaScript — а именно этот путь фаза объявляет рабочим по всему разделу — не остаётся ни одной линии защиты. Опаснее самого поведения то, что докстринг обработчика (строки 769-771) и комментарий над реестром (строки 349-360) описывают несуществующую гарантию: следующий, кто будет менять этот код, поверит описанию.

Оба остатка были известны до верификации (WR-01 в 04-REVIEW.md; DASH-05 — в 04-CONTEXT.md) и оставлены нерешёнными. Верификация их не открывает заново, а переводит из «замечание отчёта» в «условие приёмки фазы».

Остальные открытые предупреждения (WR-07 — отсутствие предиката владельца у вторичных запросов; WR-10 — обрезанный CSV со статусом 200; мёртвый метод репозитория; незакрытые галочки в REQUIREMENTS.md) ни одного критерия успеха не блокируют и остаются учтённым техдолгом.

---

_Verified: 2026-08-15T07:57:52Z_
_Verifier: Claude (gsd-verifier)_

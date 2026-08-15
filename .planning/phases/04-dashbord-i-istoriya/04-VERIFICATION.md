---
phase: 04-dashbord-i-istoriya
verified: 2026-08-15T11:36:19Z
status: passed
score: 10/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2026-08-15T07:57:52Z — 8/10
  gaps_closed:
    - "SC-1 / DASH-05: дашборд отвечает ПЕРЕЧНЕМ аккаунтов с состоянием каждого, а не одним числом (план 04-11)"
    - "HIST-04 / прохибиция P6: два ПОСЛЕДОВАТЕЛЬНЫХ нажатия «Повторить» ставят ровно одну задачу — окно удержания переживает ответ 302 (план 04-12)"
  gaps_remaining: []
  regressions: []
gaps: []
deferred: []
warnings:
  - item: "Бухгалтерия трассируемости не обновлена: все девять требований Фазы 4 в .planning/REQUIREMENTS.md остаются `- [ ]` (строки 97-108) и `Pending` в таблице (строки 221-229)"
    severity: warning
    impact: "Учётный остаток, не дефект кода. Ни один критерий успеха не блокирует. Подлежит закрытию до ship."
  - item: "ROADMAP.md, строка `**Plans**: 12/12 plans executed (10/10 исполнены; 2 плана закрытия остатков верификации — ожидают исполнения)` устарела — оба плана закрытия исполнены и отмечены [x]; статус фазы в таблице прогресса — `In Progress`"
    severity: warning
    impact: "Бухгалтерия. Подлежит обновлению при закрытии фазы."
  - item: "T-04-G2-05 — реестр удержания повтора живёт в памяти ОДНОГО процесса"
    severity: warning
    impact: "На сегодняшней топологии дефекта нет (проверено: prod — один uvicorn без --workers, `container_name: web-broadcaster` исключает масштабирование сервиса). Граница выписана в коде и в 04-SECURITY.md. Станет реальной при переходе на несколько веб-процессов."
  - item: "WR-07 — вторичные запросы `Ad.id.in_(...)` / `MessengerAccount.id.in_(...)` / `Group.id.in_(...)` без предиката владельца"
    severity: warning
    impact: "Идентификаторы приходят из записей самого пользователя — утечки на сегодняшних данных нет; отсутствует как второй слой. Принятый техдолг."
  - item: "WR-10 — исключение внутри генератора выгрузки даёт обрезанный CSV со статусом 200"
    severity: warning
    impact: "Форма потокового ответа не позволяет сменить код после первого фрагмента. Принятый техдолг."
---

# Phase 4: Дашборд и история — Verification Report

**Phase Goal:** Пользователь видит, что происходит с его рассылками прямо сейчас и что произошло раньше, и может действовать по неудачным отправкам.
**Verified:** 2026-08-15T11:36:19Z
**Status:** passed
**Re-verification:** Да — после закрытия двух остатков отчёта от 2026-08-15T07:57:52Z (планы 04-11 и 04-12)

## Режим прогона

Повторная верификация. Must-haves взяты из предыдущего отчёта (10 несущих утверждений: 5 Success Criteria ROADMAP + 5 утверждений из frontmatter планов, не покрытых SC напрямую). Два ранее провалившихся пункта проверены по полной трёхуровневой схеме плюс поведенческим прогоном; восемь ранее пройденных — регрессионной проверкой (существование артефактов, целость связок, отсутствие дрейфа исходников).

**Дрейф исходников отсутствует.** `git diff --name-only 3568901..HEAD` даёт только `.planning/ROADMAP.md`, `.planning/STATE.md` и два SUMMARY. Ни один файл под `app/`, `tests/`, `alembic/` не менялся с момента прогона полной суиты (1402 passed, exit 0), поэтому её результат действителен для проверяемого дерева.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC-1: дашборд показывает метрики за сутки, ближайшие отправки И то, КАКИЕ воркеры аккаунтов онлайн | ✓ VERIFIED | **Закрыт (gap 1).** `common.py:327-346` — отдельное чтение `select(MessengerAccount.id, .type, .status).where(user_id == user.id).order_by(id)`; из него строится `sessions` с булевым `is_online` по единому предикату `WORKER_ONLINE_STATUS` (строка 263). `common.py:397-400` кладёт в контракт перечень и ОБА агрегата, выведенных из него (`sessions_online` = `sum(...)`, `sessions_total` = `len(sessions)`, `nav_counts.accounts` = `len(sessions)`), — двух скалярных подзапросов по `messenger_accounts` больше нет, второму источнику числа взяться неоткуда. `dashboard.py:127` пробрасывает `sessions`; `dashboard.html:76-93` рендерит блок «Воркеры аккаунтов» строкой на аккаунт через макрос. Поведение подтверждено прогоном верификатора: `test_dashboard_lists_each_account_with_its_worker_state` ассертит `rows == {wa.id: "true", tg.id: "false", mx.id: "true"}` — три аккаунта, каждый со СВОИМ состоянием, — и что пилюля шапки при этом равна `2`. Метрики и ближайшие отправки — регрессия зелёная |
| 2 | SC-2: живая лента обновляется без перезагрузки + график активности за неделю | ✓ VERIFIED (регрессия) | `dashboard.html` — `hx-get="/dashboard/feed" hx-trigger="every 20s"` на стабильном контейнере; `partial_feed.html` (45 строк) не несёт ни одного атрибута опроса; маршрут `app/pages/dashboard_feed.py` (77 строк) на месте; `activity_chart.html` (64 строки) даёт 28 столбцов. Ручная приёмка UAT #2 — pass |
| 3 | SC-3: фильтр по каналу/статусу/периоду + выгрузка ИМЕННО отфильтрованного | ✓ VERIFIED (регрессия) | `filter_chips.html` (66 строк) на месте; список, счётчик и выгрузка навешивают условия одной функцией `apply_history_filters`; `/history/export` объявлен выше `/history/{log_id}`. Ручная приёмка UAT #6 — pass |
| 4 | SC-4: прочитать текст ошибки, скопировать одним действием, повторить из записи | ✓ VERIFIED (регрессия) | `history_card.html` (230 строк) и `detail.html` (99 строк) на месте; путь повтора цел (см. truth 6 и 8). Ручная приёмка UAT #3 и #5 — pass (реальная доставка в группу) |
| 5 | SC-5: дашборд и история пригодны на мобильных ширинах | ✓ VERIFIED | Регрессия после появления четвёртого блока: перепись шапок в `test_responsive_markup.py` поднята 2 → 3, файл зелёный в полной суите. Ширина 320 px для нового перечня — **человеческая приёмка, принята пользователем 2026-08-15** (блокирующий чекпоинт задачи 4 плана 04-11, элемент покрытия D9 `human_judgment: true`). Ранее — UAT #8 и #9 на 320/860/900/1080 px, pass |
| 6 | 04-09/HIST-04: повторное нажатие «Повторить» не ставит вторую задачу | ✓ VERIFIED | **Закрыт (gap 2).** `history.py:399` — `_RETRY_IN_FLIGHT: dict[int, float]`; `:365` — `RETRY_COOLDOWN_SECONDS = 60.0`; `_claim_retry_slot` (`:498-517`) синхронна и проставляет срок `monotonic() + COOLDOWN` ВПЕРЁД, поэтому окно переживает ответ; в обработчике заведён локальный признак `queued = False` (`:856`), снятие в `finally` стало УСЛОВНЫМ — `if not queued: _release_retry_slot(...)` (`:897-899`). Прогон верификатора: `test_two_sequential_retries_queue_exactly_one_task` — 1 passed; тело теста прочитано и ассертит по существу: `assert log.id in _RETRY_IN_FLIGHT` после первого POST («окно пережило ответ»), затем `assert len(env.queued) == 1` на два ПОСЛЕДОВАТЕЛЬНЫХ реальных POST через обработчик, плюс `retry=RETRY_BUSY` в `location` второго ответа. Ранее закреплявший дефект `test_retry_releases_the_slot_after_success` (ассертил `== 2`) в файле отсутствует |
| 7 | 04-01/04-35: у аналитики и фильтров истории ровно одно определение | ✓ VERIFIED (регрессия) | `app/application/analytics/send_analytics.py` — 800 строк, не менялся; история и админка импортируют `apply_history_filters` / `history_filter_params` оттуда |
| 8 | 04-03: повтор идёт тем же диспетчером, второго пути отправки нет, все три канала | ✓ VERIFIED (регрессия) | `tasks.py` → `build_dispatch_task(...)` → `dispatch_send_tasks([task])`; страж единственного пути постановки цел — `grep -c "celery.send_task"` в `history.py` = 1 (`:895`) |
| 9 | 04-10: у вопроса «сколько было ошибок» один ответ | ✓ VERIFIED (регрессия) | `app/routes/history.py` зовёт `send_metrics`; второго определения сводки в `SendLogRepository` нет |
| 10 | 04-02: ревизия 0016 — составной индекс `(user_id, sent_at)`, `down_revision = "0015"` | ✓ VERIFIED (регрессия) | `alembic/versions/0016_send_logs_user_sent_at.py` — 54 строки, не менялся |

**Score:** 10/10 truths verified (0 present, behavior-unverified)

### Прохибиции (must-NOT), judgment-tier

| # | Прохибиция | План | Статус | Evidence |
|---|-----------|------|--------|----------|
| P1 | MUST NOT silently exclude unclassifiable send records from tile counts | 04-01 | ✓ VERIFIED | `send_metrics`: `failed = (status != ok)`, а не членство в перечне |
| P2 | MUST NOT silently exclude unclassifiable records from the activity grid | 04-04 | ✓ VERIFIED | `activity_heatmap`: клампы вместо `continue`; тест `test_heatmap_counts_record_without_group_or_messenger` |
| P3 | MUST NOT indicate a successful copy when the clipboard write did not occur | 04-07 | ✓ VERIFIED | `mark(done)` выходит при `!done`; запасной путь возвращает реальный результат |
| P4 | MUST NOT present retry as re-sending the archived snapshot | 04-09 | ✓ VERIFIED | Текст панели не менялся ни на символ (04-12 подтверждает и код это показывает); новый текст `RETRY_BUSY` содержимого отправки не обещает |
| P5 | MUST NOT dispatch a send for a cross-site request | 04-09 | ✓ VERIFIED | `_is_same_origin` вызывается ПЕРВЫМ после гарда входа (`history.py:838-839`), до чтения записи; отказ — 403. Функция планом 04-12 не тронута |
| P6 | MUST NOT let one user retry action dispatch more than one send (double submit / refresh / back-button POST) | 04-09 | ✓ VERIFIED | **Снят флаг предыдущего отчёта.** Три линии: (а) перенаправление после POST закрывает обновление страницы и кнопку возврата; (б) панель Alpine закрывает двойной клик при включённом JS; (в) **новое** — серверное окно удержания на 60 с, переживающее ответ, закрывает два последовательных нажатия при ВЫКЛЮЧЕННОМ JS. Автоматически: `test_two_sequential_retries_queue_exactly_one_task` (прогнан). Вне процесса: **пользователь принял 2026-08-15** блокирующий чекпоинт — два нажатия при выключенном JavaScript дали ОДНУ реальную доставку и ОДНО списание баланса (элемент покрытия D7, `human_judgment: true`). Названная граница (один процесс) проверена против топологии: prod поднимает один `uvicorn` без `--workers`, а `container_name: web-broadcaster` в `docker-compose.prod.yml` исключает масштабирование сервиса — на сегодняшнем развёртывании граница не достигается |

Все шесть прохибиций разрешены. Позиций со статусом `unverified` / `flagged` не осталось.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/templates/dashboard/includes/worker_row.html` | макрос строки перечня воркеров | ✓ VERIFIED | **Создан 04-11.** 40 строк; `macro worker_row(session)`; три ветки состояния (`active` → «Онлайн», `disconnected` → «Отключён», иначе — СЫРОЕ значение статуса); собственный словарь `MESSENGER_LABELS`; несёт `data-worker`, `data-worker-id`, `data-worker-online` |
| `app/pages/common.py` → `get_shell_context` | перечень `sessions` + производные агрегаты | ✓ VERIFIED | `WORKER_ONLINE_STATUS` (`:263`); чтение (`:327-337`); построение перечня (`:338-346`); `sessions_online` (`:347`); контракт (`:397-400`) |
| `app/pages/history.py` → реестр удержания | `dict[int, float]` + окно + условное снятие | ✓ VERIFIED | `:365`, `:399`, `:498-517`, `:520-534`, `:848-849`, `:856`, `:897-899` |
| `app/application/analytics/send_analytics.py` | публичный контракт аналитики | ✓ VERIFIED | 800 строк, регрессия |
| `app/pages/dashboard_feed.py` | маршрут ленты вне страничного роутера | ✓ VERIFIED | 77 строк, регрессия |
| `app/templates/dashboard/partial_feed.html` | только строки, без атрибутов опроса | ✓ VERIFIED | 45 строк, регрессия |
| `app/templates/dashboard/includes/activity_chart.html` | бар-чарт 28 столбцов | ✓ VERIFIED | 64 строки, регрессия |
| `app/templates/dashboard/includes/metric_tile.html` | макрос плитки с дельтой | ✓ VERIFIED | 31 строка, регрессия |
| `app/templates/dashboard/includes/upcoming_row.html` | строка ближайшей отправки | ✓ VERIFIED | 59 строк, регрессия |
| `app/templates/dashboard/includes/feed_row.html` | строка-ссылка в запись истории | ✓ VERIFIED | 40 строк, регрессия |
| `app/templates/history/includes/filter_chips.html` | макрос чипсов-ссылок | ✓ VERIFIED | 66 строк, регрессия |
| `app/templates/history/includes/history_card.html` | блок ошибки + clamp + копирование + повтор | ✓ VERIFIED | 230 строк, регрессия |
| `app/templates/history/detail.html` | страница записи, полный текст ошибки | ✓ VERIFIED | 99 строк, регрессия |
| `alembic/versions/0016_send_logs_user_sent_at.py` | составной индекс | ✓ VERIFIED | 54 строки, регрессия |
| `app/templates/dashboard/includes/heatmap.html` | сетка 7×24 (D-09) | ⚠️ УДАЛЁН НАМЕРЕННО | D-09 отменён владельцем на приёмке; ROADMAP/REQUIREMENTS переформулированы. Не gap |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `app/pages/__init__.py` | `get_shell_context` | `router = APIRouter(dependencies=[Depends(load_shell_context)])` | ✓ WIRED | `__init__.py:21-41` — `request.state.shell` заполняется на КАЖДОМ страничном маршруте |
| `app/pages/dashboard.py` | контракт шелла | `getattr(request.state, "shell", {}).get("sessions") or []` | ✓ WIRED | `dashboard.py:127`; собственного запроса страница не делает |
| `app/templates/dashboard.html` | `worker_row.html` | импорт макроса + цикл | ✓ WIRED | `dashboard.html:8` (импорт), `:82` (`{% for s in sessions %}{{ worker_row(s) }}{% endfor %}`) |
| `app/templates/base.html` | тот же `sessions` | `sessions_online` / `sessions_total` из `shell` | ✓ WIRED | `base.html:21-22, 108-111`; оба числа выведены из ТОГО ЖЕ списка в `common.py` — разойтись перечню и пилюле не с чем |
| `app/pages/history.py` (обработчик повтора) | `_claim_retry_slot` / `_release_retry_slot` | занятие до асинхронной работы, снятие только при `not queued` | ✓ WIRED | `:848`, `:897-899` |
| `app/pages/history.py` | `app/worker/tasks.py` | `celery.send_task(RETRY_TASK_NAME, ...)` | ✓ WIRED | `:895`; локальный импорт сохранён (`:893`), страж единственного пути = 1 |
| `app/pages/history.py` | `app/services/billing_cache.py` | `check_balance_cached` ДО `send_task` | ✓ WIRED | `:883`; на отказе баланса окно снимается (`queued` остаётся `False`) |
| `app/pages/dashboard.py` | `send_analytics.py` | импорт пяти функций аналитики | ✓ WIRED | регрессия |
| `app/main.py` | `app/pages/dashboard_feed.py` | `include_router` мимо страничного роутера | ✓ WIRED | регрессия |
| `app/templates/history/list.html` | `/history/export` | ссылка с теми же параметрами фильтра | ✓ WIRED | регрессия |
| `alembic/0016` | `alembic/0015` | `down_revision` | ✓ WIRED | регрессия |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `dashboard.html` блок «Воркеры аккаунтов» | `sessions` | `get_shell_context` → `select(MessengerAccount.id, .type, .status).where(user_id == user.id)` → список словарей → `request.state.shell` → `dashboard.py:127` → цикл макроса | Да | ✓ FLOWING |
| `base.html` пилюля | `sessions_online` / `sessions_total` | ТОТ ЖЕ `sessions` (`sum(...)` и `len(...)`), а не второй запрос | Да | ✓ FLOWING |
| боковое меню, счётчик аккаунтов | `nav_counts.accounts` | `len(sessions)` — скалярный подзапрос снят | Да | ✓ FLOWING |
| `dashboard.html` плитки | `metrics` | `send_metrics` → один `select` с условными агрегатами | Да | ✓ FLOWING |
| `dashboard.html` график | `chart_view` | `activity_chart(await activity_heatmap(...))` → `session.stream(select(SendLog.sent_at))` | Да | ✓ FLOWING |
| `dashboard.html` ближайшие | `upcoming` | `upcoming_sends` → `select(Schedule, Ad, MessengerAccount)` | Да | ✓ FLOWING |
| `partial_feed.html` | `feed` | `recent_feed` → `select(...).order_by(sent_at.desc()).limit(8)` | Да | ✓ FLOWING |
| `history/list.html` карточки и линейка | `logs` / `history_total` | `select(SendLog, Group)` + `history_count` с теми же фильтрами | Да | ✓ FLOWING |
| CSV-выгрузка | строки файла | `db.stream(query)` → `export_row` | Да | ✓ FLOWING |
| Реестр удержания повтора | `_RETRY_IN_FLIGHT[log.id]` | `monotonic() + RETRY_COOLDOWN_SECONDS`, живёт между запросами | Да | ✓ FLOWING |

Захардкоженных значений, статических возвратов и пустых пропов на пути рендера не обнаружено. `sessions` в `dashboard.py:127` имеет запасное `or []`, но это не HOLLOW_PROP: зависимость `load_shell_context` навешена на роутер целиком, ветка достижима только для неаутентифицированного запроса, который до рендера дашборда не доходит.

### Behavioral Spot-Checks

Прогнаны верификатором в собственном процессе; полная суита не перезапускалась (дрейфа исходников нет, см. «Режим прогона»).

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Все проверки повтора после закрытия gap 2 | `pytest -p no:randomly tests/test_pages/test_history_retry.py -q` | **57 passed**, 50.72s | ✓ PASS |
| Два последовательных нажатия ставят РОВНО ОДНУ задачу | `...::test_two_sequential_retries_queue_exactly_one_task` | passed; тело ассертит `len(env.queued) == 1` + наличие удержания после первого ответа + `retry=busy` | ✓ PASS |
| Дефектный тест старого контракта отсутствует | `grep -c "def test_retry_releases_the_slot_after_success"` | `0` | ✓ PASS |
| Пересекающиеся запросы по-прежнему дают одну постановку | `...::test_retry_of_a_busy_record_queues_no_second_task` | passed (`env.queued == []`) | ✓ PASS |
| Окно истекает — это не замок | `...::test_retry_becomes_possible_again_after_the_cooldown_window` | passed | ✓ PASS |
| Отказ предпроверки / баланса окна не оставляет | `...::test_a_refused_retry_arms_no_cooldown`, `...::test_a_balance_refusal_arms_no_cooldown` | passed | ✓ PASS |
| Удержание ключуется по конкретной записи | `...::test_retry_cooldown_is_keyed_per_record` | passed | ✓ PASS |
| Исключение снимает удержание | `...::test_retry_releases_the_slot_after_an_exception` | passed | ✓ PASS |
| Описание кода не расходится с механизмом | `...::test_retry_handler_description_matches_the_mechanism`, `...::test_retry_slot_registry_documents_its_limit`, `...::test_retry_busy_notice_states_the_real_guarantee` | passed | ✓ PASS |
| Перечень воркеров: 13 названных проверок | `pytest -p no:randomly tests/test_pages/test_shell.py -k "worker or sessions or dashboard_lists or aggregate" -q` | **13 passed**, 12.40s | ✓ PASS |
| Пользователь читает, КАКОЙ аккаунт онлайн | `...::test_dashboard_lists_each_account_with_its_worker_state` | passed; ассерт `rows == {wa: "true", tg: "false", max: "true"}` + пилюля `2` | ✓ PASS |
| Незнакомый статус остаётся видимым | `...::test_dashboard_worker_list_keeps_an_unrecognised_status_visible` | passed | ✓ PASS |
| Пустое состояние без аккаунтов | `...::test_dashboard_worker_list_shows_an_empty_state_without_accounts` | passed | ✓ PASS |
| Чужой аккаунт не попадает в перечень и счёт | `...::test_dashboard_worker_list_excludes_another_users_account` | passed | ✓ PASS |
| Секреты в перечень не попадают | `...::test_shell_worker_list_carries_no_secrets`, `...::test_shell_worker_entries_expose_only_the_declared_keys` | passed; независимо подтверждено grep-ом: `credentials` / `session_data` в `worker_row.html`, `dashboard.html`, `dashboard.py` не встречаются | ✓ PASS |
| Нет N+1 на пути рендера | `...::test_shell_reads_worker_state_in_a_single_query` | passed | ✓ PASS |
| Число и перечень не могут разойтись | `...::test_shell_aggregate_is_derived_from_the_worker_list`, `...::test_dashboard_page_has_no_second_source_of_the_sessions_number` | passed | ✓ PASS |
| Топология развёртывания против границы «один процесс» | чтение `docker-compose.prod.yml`, `Dockerfile` | один `uvicorn` без `--workers`; `container_name` исключает `scale` | ✓ PASS |
| Полная суита | `uv run python -m pytest tests/ -q` на коммите 3568901 | **1402 passed**, exit 0 | ✓ PASS (унаследовано; исходники не менялись) |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| — | `find scripts -path '*/tests/probe-*.sh'` | Проб в проекте нет; ни один PLAN/SUMMARY фазы их не объявляет | n/a — SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DASH-01 | 04-01, 04-02, 04-10, 04-11 | Метрики отправок за последние сутки | ✓ SATISFIED | `send_metrics` со скользящим окном 24 ч + дельта; четыре плитки |
| DASH-02 | 04-04, 04-10, 04-11 | Список ближайших запланированных отправок | ✓ SATISFIED | `upcoming_sends` + `upcoming_row`; сортировка по `next_run_at`, пометки причин |
| DASH-03 | 04-05, 04-10, 04-11 | Живая лента последних событий отправки | ✓ SATISFIED | `/dashboard/feed` + `hx-trigger every 20s`; UAT #2 pass |
| DASH-04 | 04-02, 04-04, 04-10, 04-11 | График активности отправок за неделю | ✓ SATISFIED | `activity_chart` — 28 столбцов, якорь на локальную полночь; формулировка приведена к бар-чарту владельцем |
| DASH-05 | 04-05, 04-10, **04-11** | Какие воркеры аккаунтов сейчас онлайн | ✓ SATISFIED | **Было BLOCKED — закрыто.** Перечень по строке на аккаунт с состоянием каждого; агрегат шапки выведен из того же списка. 13 названных тестов зелёные |
| HIST-01 | 04-01, 04-02, 04-06, 04-10, 04-12 | Фильтр по каналу, статусу и периоду | ✓ SATISFIED | Три оси чипсов + выпадающий список аккаунта |
| HIST-02 | 04-07, 04-10, 04-12 | Текст ошибки виден и копируется | ✓ SATISFIED | Полный экранированный текст + clamp без JS + кнопка с проверкой доступности буфера; UAT #3 pass |
| HIST-03 | 04-02, 04-08, 04-10, 04-12 | Выгрузка отфильтрованной истории | ✓ SATISFIED | Потоковый CSV, BOM, `;`, экранирование формул, потолок до потока; UAT #6, #7 pass |
| HIST-04 | 04-03, 04-09, 04-10, **04-12** | Повтор отправки из записи истории | ✓ SATISFIED | Полный путь до реальной доставки (UAT #5 pass); защита от двойной постановки закрыта окном удержания и подтверждена приёмкой с выключенным JS |

**Осиротевших требований нет.** Все девять идентификаторов, отнесённых REQUIREMENTS.md к Фазе 4, объявлены как минимум одним планом; лишних идентификаторов планы не объявляют. Оба плана закрытия (04-11, 04-12) объявляют во frontmatter `requirements-completed` те же девять в сумме, новых не вводят.

⚠️ **Бухгалтерия трассируемости по-прежнему не обновлена** (перенесено из предыдущего отчёта, не закрыто): в `.planning/REQUIREMENTS.md` все девять требований остаются `- [ ]` (строки 97-108) и `Pending` в таблице (строки 221-229). Оба плана закрытия намеренно не трогали этот файл (04-11 отмечает это в разделе «Область не расширена»). Это учётный остаток, а не дефект кода, и ни одного критерия успеха он не блокирует — но закрыть его следует до `ship`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` | — | **Ни одного маркера долга** ни в одном из девяти файлов, затронутых планами 04-11 и 04-12 (сплошной обход: `common.py`, `dashboard.py`, `history.py`, `dashboard.html`, `worker_row.html`, `app.css`, три файла тестов). Гейт маркеров долга пройден |
| `app/pages/history.py` | 649-683 | Исключение внутри генератора выгрузки даёт обрезанный файл со статусом 200 | ⚠️ Warning | WR-10; форма потокового ответа не позволяет сменить код после первого фрагмента. Планом 04-12 намеренно не тронут |
| `app/pages/history.py` | ~415-439 | Вторичные запросы `Ad.id.in_(...)` / `MessengerAccount.id.in_(...)` без предиката владельца | ⚠️ Warning | WR-07. Идентификаторы приходят ИЗ записей самого пользователя — утечки нет; отсутствует как второй слой |
| `app/application/analytics/send_analytics.py` | 539-545 | То же по `Group.id.in_(...)` в `upcoming_sends` | ⚠️ Warning | WR-07, та же оценка |
| `app/pages/history.py` | 368-398 | Реестр удержания в памяти одного процесса | ⚠️ Warning (info на сегодняшней топологии) | T-04-G2-05. Граница названа в коде ЯВНО (пункт 2 комментария) и в 04-SECURITY.md. Проверено против развёртывания: prod — один процесс, масштабирование сервиса исключено `container_name` |
| `app/repositories/send_log.py` | 37 | Мёртвый метод `list_for_user_with_details` без потребителей | ℹ️ Info | WR-11; на поведение не влияет |
| `app/templates/history/detail.html` | 47 | `messenger_icon` зовётся без ограничения известными типами | ℹ️ Info | Инвентаризационные тесты зелёные |

**Проверка на подмену вместо починки (ключевой адверсарный вопрос повторной верификации):** ни одно из двух закрытий не удержано зелёным за счёт ослабления проверок.
- Дефектный тест `test_retry_releases_the_slot_after_success` не удалён «под ковёр», а ПЕРЕПИСАН под верное утверждение и переименован; тело прочитано верификатором — оно ассертит одну задачу, а не отсутствие проверки. Литерал `len(env.queued) == 2` в файле отсутствует.
- Структурный тест `test_retry_slot_release_is_a_discard_in_a_finally_block` не удержан литералом в комментарии (прямо запрещённый обход), а исправлен на ассерт по выполняемому коду (`.pop(` со значением по умолчанию); негативный ассерт и оба ассерта про `finally:` сохранены.
- В 04-11 запрет `test_dashboard_body_has_no_entity_counters` (D-01) НЕ ослаблялся: исполнитель изменил СВОЙ заголовок пустого состояния, а не чужой тест.
- Автоузная фикстура изоляции реестра в тестах повтора прочитана: она чистит модульный словарь до/после теста и ничего не маскирует — ключ реестра равен `send_logs.id`, который у пофункционной базы в памяти в каждом тесте снова равен 1.

### Human Verification Required

**Нет открытых позиций.** Раздел пуст намеренно, и это условие статуса `passed`.

Обе позиции, недостижимые для автоматики, закрыты человеком и повторному запросу не подлежат:

1. **Ширина 320 px для нового перечня воркеров** (04-11, элемент покрытия D9, `human_judgment: true`, `verification: backstop`) — блокирующий чекпоинт задачи 4, **принят пользователем 2026-08-15**. Совпадение состояний на экране с разделом `/accounts` проверено глазами на живом сервере.
2. **Одна доставка и одно списание баланса при выключенном JavaScript** (04-12, элемент покрытия D7, `human_judgment: true`) — блокирующий чекпоинт задачи 4, **принят пользователем 2026-08-15**. Главный ассерт (одна РЕАЛЬНАЯ доставка в стороннюю группу и одно списание РЕАЛЬНОГО баланса) внутрипроцессным тестом не наблюдаем: клиент очереди в тестах подменён, а доставка и биллинг живут за границей веб-процесса. Именно этот путь UAT #4 не поймал, потому что проходил с включённым JS.

Ранее закрытая приёмка фазы (UAT 95/95, включая #2, #3, #4, #5, #6, #7, #8, #9) остаётся в силе — исходники после неё менялись только двумя планами закрытия, чьи собственные чекпоинты приняты.

### Gaps Summary

**Gaps нет.** Оба остатка отчёта от 2026-08-15T07:57:52Z закрыты по существу, а не переописаны.

**Gap 1 (SC-1 / DASH-05) — закрыт сменой ответа, а не формулировки.** Дашборд больше не отвечает числом: `get_shell_context` читает состояние поаккаунтно одним запросом по индексированному `user_id`, а блок «Воркеры аккаунтов» печатает строку на каждый аккаунт с его состоянием. Существенно, что закрытие сделано не добавлением второго источника данных рядом с прежним счётчиком, а ЗАМЕНОЙ: два скалярных подзапроса по `messenger_accounts` сняты, и `sessions_online`, `sessions_total`, `nav_counts.accounts` теперь выводятся из того же прочитанного списка. Пилюля шапки и строка перечня физически не могут показать разное. Побочно закрыт риск, которого в исходной постановке gap не было: проекция трёх колонок вместо ORM-объекта означает, что `credentials` и `session_data` в словарь, печатаемый на каждой из 26 страниц, не попадают вовсе — верификатор подтвердил это и тестами, и независимым grep-ом по пути рендера.

**Gap 2 (HIST-04 / прохибиция P6) — закрыт механизмом, и описание приведено к правде.** Реестр сменил смысл с «заявка на время обработчика» на «срок, до которого повтор отклоняется»: тип стал `dict[int, float]`, срок проставляется на 60 секунд вперёд, а снятие ушло из безусловного `finally` под признак `queued` и отрабатывает только там, где задача в очередь не ушла. Два последовательных POST через реальный обработчик дают одну постановку — верификатор прогнал именно этот тест и прочитал его тело, потому что переименованный тест мог бы оказаться ослабленным; он не ослаблен, а усилен (кроме счёта задач, он ассертит наличие удержания сразу после первого ответа — то есть проверяет ПРИЧИНУ, а не только следствие). Отдельно проверено то, что предыдущий отчёт назвал опаснее самого дефекта: докстринг обработчика, комментарий реестра и текст плашки `RETRY_BUSY` больше не обещают гарантию, которой нет, и обе границы окна (оно истекает; оно живёт в одном процессе) выписаны явно. Названная многопроцессная граница проверена против фактического развёртывания и на нём не достигается.

**Регрессий нет.** Ни одно из восьми ранее пройденных утверждений не пострадало: артефакты на месте, связки целы, полная суита на этом дереве — 1402 passed. Единственное изменение в чужих тестах — перепись шапок блоков дашборда 2 → 3 в `test_responsive_markup.py`, вынужденная появлением четвёртого блока; смысл утверждения сохранён (собственная шапка в обход общего атрибута это число не увеличила бы).

**Что остаётся открытым — и почему это не gaps.** Пять предупреждений (учётные галочки REQUIREMENTS.md; устаревшая строка `Plans:` и статус `In Progress` в ROADMAP; многопроцессная граница реестра; WR-07; WR-10) не блокируют ни одного критерия успеха. Первые два — бухгалтерия, которую следует закрыть при переводе фазы в Complete; остальные три — названный и принятый техдолг с выписанными границами. Ни одно из них не является невыполненной работой фазы.

**Цель фазы достигнута.** Пользователь видит, что происходит с его рассылками прямо сейчас — метрики за сутки, ближайшие отправки, живую ленту без перезагрузки, график активности и теперь поимённо, какой из его каналов онлайн, а какой отвалился. Он видит, что произошло раньше, — историю с фильтрами по трём осям и выгрузкой ровно отфильтрованного. И он может действовать по неудачным отправкам — прочитать ошибку, скопировать её одним действием и повторить отправку, причём одно намерение теперь порождает ровно одну отправку даже без JavaScript.

---

_Verified: 2026-08-15T11:36:19Z_
_Verifier: Claude (gsd-verifier)_

---
phase: 06-admin-panel
verified: 2026-08-24T00:00:00Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
behavior_unverified_items: []  # оба закрыты человеческой приёмкой 2026-08-24 — см. resolved_by_uat ниже
behavior_previously_unverified:
  - truth: "Администратор видит состояние контейнеров по каналам в «Воркерах», состояние очереди задач по каналам в «Очереди» и логи приложения и воркеров в «Логах» (критерий 4)."
    test: "Поднять стенд (`just dev` + `just monitoring-start`). 1) Дождаться живого WA-воркера, `docker kill <контейнер>` без штатного завершения, подождать > 90 с, открыть `/admin/workers`. 2) Остановить мониторинг, открыть `/admin/logs`. 3) Открыть `/admin/queue` при непустой очереди."
    expected: "1) Строка воркера показывает простой при пустой очереди и «отключён» при непустой — не «в работе». 2) Плашка с названной причиной и командой подъёма мониторинга, а не пустой список. 3) Три канала с реальными глубинами, прочитанными из живого Redis."
    why_human: "Ни одно значение подразделов «Воркеры», «Очередь» и «Логи» никогда не читалось из ЖИВОГО Redis или живого Loki: вся суита идёт на подменённых клиентах. Тесты доказывают контракт приложения ПРИ данном ответе источника, но не имена ключей, имена контейнеров и метки потоков в бою. Планы 06-05 и 06-08 объявили эти утверждения `verification: backstop` сами; реестр требований по той же причине держит ADMIN-07 и ADMIN-09 в статусе Partial."
  - truth: "Все подразделы админ-панели пригодны к использованию на мобильных ширинах (критерий 5, вторая половина)."
    test: "Открыть каждый из шести адресов (`/admin`, `/admin/users`, `/admin/workers`, `/admin/queue`, `/admin/logs`, `/admin/payments`) в браузере при ширине окна 375 px."
    expected: "Горизонтального переполнения нет; шесть вкладок достижимы; обе колонки состояния «Воркеров» читаются; строки очереди и лога не рвут раскладку; журнал платежей читается; блок инцидентов не наезжает на плитки; кнопки перезапуска и снятия нажимаемы."
    why_human: "Утверждение объявлено `verification: backstop` тремя планами (06-01, 06-05, 06-14) и говорит о ЧЕЛОВЕЧЕСКОЙ пригодности. Машинное свидетельство есть, но оно другого рода: `test_admin_no_utility_classes` и `test_admin_pages_use_row_primitives` проверяют, что разметка построена на адаптивных примитивах проекта, а `[data-subtabs]` несёт `flex-wrap: wrap` с записанным доводом против горизонтальной прокрутки. Ни один тест не рендерит вьюпорт 375 px и не измеряет переполнение. Пункт 1 таблицы приёмки плана 06-14 записан как ❌ НЕ ПРОВЕДЕНО."
resolved_by_uat: ".planning/phases/06-admin-panel/06-UAT.md (2026-08-24, 8/8 pass, 0 issues)"
human_verification_resolved:
  - test: "Шесть подразделов админ-панели на ширине 375 px в браузере"
    expected: "Нет горизонтального переполнения, вкладки и элементы управления достижимы на всех шести адресах"
    why_human: "Критерий сформулирован о человеческой пригодности; машинное свидетельство — только утверждения о разметке, не рендер вьюпорта"
  - test: "Простой воркера на живом стенде: `docker kill` контейнера WA-воркера, ожидание > 90 с, `/admin/workers`"
    expected: "Строка показывает простой при пустой очереди и «отключён» при непустой, а не «в работе»"
    why_human: "Возрастной предикат свежести heartbeat проверен против подменённого Redis; живого чтения не было ни разу"
  - test: "Плашка недоступного источника логов: остановить мониторинг, открыть `/admin/logs`"
    expected: "Плашка с названной причиной и командой подъёма, а не пустой список"
    why_human: "Недоступность источника доказана подменённым клиентом; настоящего недоступного Loki подраздел не видел"
  - test: "Имя контейнера службы канала telegram в метках источника: `docker ps --format '{{.Names}}'` на стенде, сверка с `LOG_SOURCES`"
    expected: "Имена совпадают со словарём источников подраздела «Логи»"
    why_human: "Допущение исследования о среде исполнения; репозиторий его подтвердить не может"
  - test: "Формат журналирования в бою: открыть «Логи», выбрать чип уровня, убедиться, что выдача не пуста"
    expected: "Выдача непуста — метка `level` присутствует у строк в Loki"
    why_human: "Контракт сборщик→источник наблюдаем только на стенде. ⚠️ Вопреки записи в REQUIREMENTS.md, `monitoring/promtail.yml` метку `level` СОЗДАЁТ — см. WR ниже; проверка нужна для подтверждения, а не для поиска дефекта"
  - test: "Видимость очередей воркеров из веб-процесса: `redis-cli --scan --pattern 'wa:queue:*'` с того же адреса брокера, что читает веб-процесс"
    expected: "Ключи очередей видны"
    why_human: "Допущение исследования о топологии брокера"
  - test: "РЕШЕНИЕ ВЛАДЕЛЬЦА: исправить запись о `monitoring/promtail.yml` в `.planning/REQUIREMENTS.md` (строки 283, 297, 324) и в `06-14-SUMMARY.md`"
    expected: "Вторая из двух названных причин статуса `Partial` у ADMIN-09 снята как не подтвердившаяся; решить, остаётся ли ADMIN-09 `Partial` по одной оставшейся причине (живое чтение не проводилось)"
    why_human: "Реестр требований — постоянный артефакт проекта; правка его вердикта есть решение владельца, а не работа верификатора"
  - test: "РЕШЕНИЕ ВЛАДЕЛЬЦА по записи 3 журнала `.planning/WINDOWS.md`: `must_haves` плана 06-11 требуют `def monthly_revenue` внутри `app/application/admin/payments_query.py`"
    expected: "Подтвердить, что править надо must_haves плана (функция живёт в `overview_stats.py`, три условия — в `paying_subscription_clauses`), а не код"
    why_human: "Запись открыта самим исполнителем с просьбой о решении владельца; альтернатива — переезд кода — ослабила бы машинный гейт `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`"
prohibitions_flagged:
  count: 34
  tier: judgment
  disposition: "unverified-prohibition — human review recommended"
  judge_verdict: "НЕ АВТОРИТЕТНО. Выборочно проверено 12 из 34 разбором кода и разметки — нарушений не найдено (см. раздел «Прохибиции»). Остальные 22 не опровергнуты, но и не проверены поимённо."
---

# Phase 6: Админ-панель — Verification Report

**Phase Goal:** Администратор ведёт поддержку и эксплуатацию сервиса из одной админ-панели с подразделами вместо разрозненных админ-страниц.
**Verified:** 2026-08-24 (человеческая приёмка проведена)
**Status:** passed
**Re-verification:** Да — обновление начальной проверки после закрытия человеческих пунктов

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Администратор переключается между шестью подразделами внутри одной админ-панели; «Обзор» показывает ключевые показатели | ✓ VERIFIED | Шесть маршрутов в `app/pages/admin.py` (`""`:495, `/users`:586, `/workers`:673, `/queue`:963, `/logs`:1151, `/payments`:1225). `_tabs.html` — только `<a href>`, ни одного `hx-*`/`x-*`. Признак активности `data-subtab-active` свой, не переиспользует `is-active` шелла. Перечень вкладок один (`ADMIN_TABS`), в шаблоне не дублирован. «Обзор» рисует 4 плитки из живых запросов (`user_totals`, `paying_total`, `send_metrics`, `_ops_snapshot`) — `overview.html:44-100`. Прогнаны и зелены: `test_six_subsections_answer_the_admin`, `test_six_subsections_denied_for_regular_user`, `test_subsection_navigation_degrades_without_js`, `test_tabs_render_six_real_links`, `test_active_subsection_is_marked_exactly_once`, `test_all_six_subsection_templates_include_the_same_tabs`, `test_no_docker_client_on_the_render_path` |
| 2 | Администратор может найти пользователя поиском и фильтрами, заблокировать и разблокировать его | ✓ VERIFIED | `app/application/admin/users_query.py` — выдача и счётчик одним выражением; 39 тестов `test_admin_users.py` зелены, включая `test_the_counter_over_the_list_equals_the_list`, `test_the_search_folds_cyrillic_case_both_ways`, `test_both_axes_and_the_search_apply_together`, `test_an_underscore_in_the_search_matches_an_underscore`. Блокировка ДЕЙСТВУЕТ на трёх путях: страничный вход `app/pages/auth.py:132`, JSON-поверхность `app/dependencies.py:410`, сбор рассылки `app/application/scheduling/use_cases.py:156`. Маршрут `POST /admin/users/{id}/block` (admin.py:1776) инвертирует признак и несёт гард происхождения. Зелены `test_the_admin_toggle_blocks_a_user`, `test_a_blocked_user_gets_no_cookie_from_the_page_login`, `test_a_blocked_user_is_refused_on_a_closed_json_route`, `test_a_blocked_user_dispatches_nothing_and_keeps_the_schedule`, `test_unblocking_returns_the_schedule_to_the_selection` |
| 3 | Администратор может войти под пользователем и вернуться в свою учётную запись, не теряя админ-доступ | ✓ VERIFIED | Один токен, признак `act` (`auth_service.py:21,73-74`); `require_admin` читает ДЕЙСТВУЮЩЕЕ ЛИЦО первой веткой (`dependencies.py:127-140`); возврат `POST /impersonation/stop` (`auth.py:441`) перезаписывает cookie тем же набором атрибутов; полоса возврата в `base.html:71-74` на каждой странице. 37 названных тестов `test_impersonation.py` зелены, в том числе `test_admin_access_survives_under_the_other_identity`, `test_the_return_rewrites_the_cookie_with_the_same_attribute_set`, `test_a_blocked_actor_is_logged_out_by_the_return_not_re_admitted`, `test_no_second_identity_cookie_appears`. Гейт запретов `test_impersonation_gate.py` с доказанными зубами зелен |
| 4 | Администратор видит состояние контейнеров по каналам в «Воркерах», состояние очереди по каналам в «Очереди» и логи в «Логах» | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | ПРИСУТСТВУЕТ И СВЯЗАНО: два блока «Воркеров», порог `MAX_HEARTBEAT_STALE_SEC = 90` возрастным предикатом, паршал опроса `/admin/workers/partial` на `partials_router` (зарегистрирован `main.py:203`), единственное обращение к Docker — в обработчике перезапуска (admin.py:935). «Очередь»: три канала, отложенность ПО КАНАЛУ, снятие ровно одной задачи, «очистить очередь» отсутствует. «Логи»: названная недоступность отдельным полем, `LOG_LINE_CAP = 200` с подписью, три окна, вход из строки воркера. 96 тестов `test_admin_panel.py`, 39 `test_ops_state.py`, `test_queue_rows.py`, `test_loki_client.py` — все зелены. НЕ ДОКАЗАНО: ни одно значение не читалось из ЖИВОГО Redis или живого Loki — суита идёт на подменённых клиентах. Планы 06-05 и 06-08 объявили это `verification: backstop`; реестр требований держит ADMIN-07 и ADMIN-09 в статусе Partial по той же причине. См. Human Verification |
| 5 | Администратор видит сводку платёжных операций в «Платежах» и текущие инциденты; все подразделы пригодны к использованию на мобильных ширинах | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | ПЕРВЫЕ ДВЕ ТРЕТИ ДОКАЗАНЫ: регулярная выручка без льготных — три условия в `paying_subscription_clauses` (`app/repositories/user.py:111-115`); «истекло и не продлено за 30 дней» вместо доли; тарифного плана и среднего чека нет ни в разметке, ни в коде (только комментарии, объясняющие отсутствие); пять видов инцидента с подъёмом И снятием, у каждого адрес «куда чинить» (`incidents.py:99-104`); `test_admin_payments.py` (обе половины) и `test_incidents.py` зелены. ТРЕТЬЯ ТРЕТЬ НЕ ДОКАЗАНА: «пригодны к использованию на мобильных ширинах» объявлено `verification: backstop` тремя планами; машинное свидетельство — только утверждения о разметке (`test_admin_no_utility_classes`, `test_admin_pages_use_row_primitives`) и `flex-wrap: wrap` у `[data-subtabs]` (`app/static/css/app.css:915-920`). Вьюпорт 375 px не рендерился ни разу; пункт 1 таблицы приёмки плана 06-14 записан ❌ НЕ ПРОВЕДЕНО |

**Score:** 3/5 truths verified (2 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/services/ops_state.py` | Ленивый клиент Redis, предикат свежести возрастом, сводка живости одним pipeline | ✓ VERIFIED | 479 строк, `MAX_HEARTBEAT_STALE_SEC` присутствует, вызывается из `admin.py` |
| `app/templates/admin/includes/_tabs.html` | Вкладки шести подразделов ссылками | ✓ VERIFIED | Только `<a>`, перечень приходит извне, включён всеми шестью шаблонами |
| `app/templates/admin/workers.html` | Два блока, колонки «Сессия» и «Воркер» | ✓ VERIFIED | Разметка опроса `hx-get="/admin/workers/partial"` (стр. 42) |
| `app/templates/admin/includes/workers_partial.html` | Паршал опроса без шелла | ✓ VERIFIED | Отдаётся `partials_router` (admin.py:709-731) |
| `app/application/admin/incidents.py` | Пять признаков, условия снятия, вид и адрес | ✓ VERIFIED | 687 строк, `INCIDENT_KIND_*` × 5, `INCIDENT_DESTINATIONS` полон |
| `app/application/admin/queue_rows.py` | Разбор тела задачи, три состояния, отложенность по каналу | ✓ VERIFIED | 213 строк, `def queue_row_state` присутствует |
| `app/application/admin/users_query.py` | Фильтры, поиск, страница и счётчик одним выражением | ✓ VERIFIED | 229 строк, `def apply_user_filters` присутствует |
| `app/services/loki_client.py` | Окно логов с таймаутом, названной недоступностью и честным потолком | ✓ VERIFIED | 489 строк, `LOG_LINE_CAP = 200`, `LOG_READ_LIMIT = CAP + 1` |
| `app/application/admin/payments_query.py` | `def monthly_revenue` внутри файла | ⚠️ ДЕВИАЦИЯ | Файл существует (368 строк) и содержит `apply_payment_filters`, `expired_not_renewed`, `payment_ledger`. `monthly_revenue` живёт в `app/application/admin/overview_stats.py:94`, три условия — в `app/repositories/user.py:111-115`. ФУНКЦИОНАЛЬНОСТЬ НА МЕСТЕ; неверно объявление must_have плана. Записано журналом (WINDOWS.md, запись 3, `open`) с просьбой о решении владельца: переезд функции в `payments_query.py` ослабил бы машинный гейт `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision` |
| `app/dependencies.py` | `forbid_when_impersonating` | ✓ VERIFIED | 420 строк, зависимость на месте, `_presented_tokens` обходит ВСЕ носители (починка CR-01) |
| `app/templates/components/filter_chips.html` | Макрос с ОБЯЗАТЕЛЬНЫМ базовым адресом | ✓ VERIFIED | `macro filter_chips` присутствует, импортируется из `history/list.html` и `admin/users.html` |
| Тестовые артефакты 14 планов | min_lines и contains | ✓ VERIFIED | 13 из 14 планов: `verify.artifacts` `all_passed: true` |

### Key Link Verification

| From | To | Via | Status |
|------|-----|-----|--------|
| `app/pages/admin.py` | `app/services/ops_state.py` | сводка живости, а не собственный Redis | ✓ WIRED |
| шесть шаблонов подразделов | `_tabs.html` | общий include | ✓ WIRED |
| `app/pages/admin.py` | `app/services/wa_container_manager.py` | ЕДИНСТВЕННОЕ обращение к Docker — из обработчика перезапуска (admin.py:935) | ✓ WIRED |
| `app/templates/admin/workers.html` | `/admin/workers/partial` | маршрут зарегистрирован через `partials_router` (main.py:203) | ✓ WIRED |
| `app/pages/admin.py` | `app/services/loki_client.py` | `query_range`, `build_logql`, `clean_source`, `clean_window` (admin.py:112-114, 1183-1188) | ✓ WIRED |
| `app/pages/admin.py` | `app/application/analytics/send_analytics.py` | `send_metrics(db, user_id=None, ...)` — общесистемный вход, второй агрегации нет | ✓ WIRED |
| `app/pages/admin.py` | `app/application/admin/incidents.py` | `collect_incidents(db, liveness, now=)` | ✓ WIRED |
| `app/pages/common.py` | `app/services/auth_service.py` | `require_admin` читает `act` первой веткой | ✓ WIRED |
| `app/templates/base.html` | `app/pages/common.py` | `shell.get('impersonation')` → `impersonation_view` | ✓ WIRED |
| `app/main.py` | `app/dependencies.py` | денежный роутер целиком получает `forbid_when_impersonating` | ✓ WIRED |
| `app/pages/auth.py` | `app/config.py` | `cookie_secure` из настройки, не литералом | ✓ WIRED |
| `app/templates/history/list.html` | `app/templates/components/filter_chips.html` | импорт из библиотеки, базовый адрес явно | ✓ WIRED |

`gsd-tools query verify.key-links` — `all_verified: true` на всех 14 планах (24/24 связи).

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `admin/overview.html` | `users`, `paying`, `mrr` | `user_totals`, `paying_total` → `select(func.count(...))` над БД | Да | ✓ FLOWING |
| `admin/overview.html` | `metrics` | `send_metrics(db, user_id=None)` — модуль аналитики | Да | ✓ FLOWING |
| `admin/overview.html` | `queue_total`, `board` | `_ops_snapshot(db)` → Redis pipeline; `collect_incidents(db, ...)` | Да (Redis подменён в суите) | ✓ FLOWING |
| `admin/users.html` | строки, счётчик | `users_page` → одно выражение фильтров над БД | Да | ✓ FLOWING |
| `admin/workers.html` | строки аккаунтов, инфраструктура | `worker_liveness` → Redis heartbeat + БД аккаунтов | Да (Redis подменён в суите) | ✓ FLOWING |
| `admin/queue.html` | глубины и строки | `ops_state` → Redis LLEN/LRANGE, разбор `queue_rows` | Да (Redis подменён в суите) | ✓ FLOWING |
| `admin/logs.html` | строки журнала | `query_range(build_logql(...))` → HTTP к Loki | Да (клиент подменён в суите) | ✓ FLOWING |
| `admin/payments.html` | выручка, журнал | `paying_total`, `monthly_revenue`, `payment_ledger` над БД | Да | ✓ FLOWING |

Статических возвратов, зашитых литералов и данных макета в путях показа не найдено. Прогнан целевой тест `test_no_mockup_placeholder_numbers_reached_the_subsections` — зелен.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Все тестовые файлы фазы 06 | `uv run pytest` по 18 файлам фазы (перечень в отчёте) | **454 passed, 0 failed** за 264 с | ✓ PASS |
| `monthly_revenue` существует и вызывается | `grep -n "def monthly_revenue" app/application/admin/overview_stats.py` + вызовы admin.py:542,1276 | Найдено | ✓ PASS |
| `/admin/workers/partial` — живой маршрут | `grep -n "partials_router" app/main.py` → `app.include_router(admin_partials_router)` (стр. 203) | Зарегистрирован | ✓ PASS |
| Метка `level` создаётся сборщиком | Полное чтение `monitoring/promtail.yml` | Три блока `match` поднимают `level` в метку Loki; значения сходятся с `LEVEL_CHIPS` (`error/critical/fatal`, `warn/warning`, `info`) | ✓ PASS |
| Метки `level` существовали до фазы | `git show 4fee745:monitoring/promtail.yml \| grep -n level` | Присутствовали на базовом коммите; ни один коммит фазы файл не трогал | ✓ PASS |
| Живое чтение Redis и Loki | — | Стенда нет (Docker и брокер недоступны верификатору) | ? SKIP → Human |
| Рендер вьюпорта 375 px | — | Браузерного стенда в суите нет | ? SKIP → Human |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| `scripts/*/tests/probe-*.sh` | `find scripts -path '*/tests/probe-*.sh'` | Ни одного файла; ни один PLAN/SUMMARY фазы probe не объявляет | ? N/A — проб в проекте нет |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADMIN-03 | 06-01, 06-10, 06-14 | Подраздел «Обзор» с ключевыми показателями | ✓ SATISFIED | Шесть маршрутов + четыре плитки из живых запросов; критерий 1 |
| ADMIN-04 | 06-03, 06-09, 06-14 | «Пользователи» с поиском и фильтрами | ✓ SATISFIED | `users_query.py`, 39 тестов; критерий 2 |
| ADMIN-05 | 06-06, 06-14 | Блокировка и разблокировка | ✓ SATISFIED | Три пути принуждения + тумблер с гардом; критерий 2 |
| ADMIN-06 | 06-02, 06-12, 06-13, 06-14 | Вход под пользователем и возврат | ✓ SATISFIED | Один токен с `act`, `require_admin` по актору, возврат перезаписью cookie, гейт запретов; критерий 3 |
| ADMIN-07 | 06-01, 06-05, 06-14 | «Воркеры» с состоянием контейнеров по каналам | ? NEEDS HUMAN | Код отгружен и доказан машиной; живого чтения Redis не было. Реестр держит `Partial` — **отметка обоснована, рассуждение выдерживает проверку** |
| ADMIN-08 | 06-07, 06-14 | «Очередь» с состоянием по каналам | ✓ SATISFIED | Отложенность по каналу, три состояния, снятие одной задачи, потолок с полем срабатывания |
| ADMIN-09 | 06-03, 06-08, 06-14 | «Логи» приложения и воркеров | ? NEEDS HUMAN | Код отгружен и доказан машиной; живого чтения источника не было. Реестр держит `Partial` — **первая из двух названных причин выдерживает проверку, ВТОРАЯ НЕ ПОДТВЕРДИЛАСЬ** (см. WR-01 ниже) |
| ADMIN-10 | 06-11, 06-14 | «Платежи» со сводкой операций | ✓ SATISFIED | Выручка без льготных, «истекло и не продлено», без тарифа и среднего чека |
| ADMIN-11 | 06-04, 06-10, 06-14 | Инциденты сервиса | ✓ SATISFIED | Пять признаков с подъёмом и снятием, адреса «куда чинить» |
| CR-01 (долг 05.1) | 06-06 | Блокировка не действовала | ✓ SATISFIED | Три пути закрыты; `get_current_user_id` не получила параметра сессии (гейт зелен) |
| CR-02 (долг 05.1) | 06-02 | Предсказуемые коды сброса | ✓ SATISFIED | `test_reset_code_source.py` — утверждение об ИСТОЧНИКЕ по синтаксическому дереву, зелено |
| CR-03 (долг 05.1) | 06-02 | Cookie сессии без `secure` | ✓ SATISFIED | Признак из настройки `cookie_secure`, аварийный выключатель `COOKIE_SECURE` объявлен |

**Orphaned requirements:** нет. `ADMIN-01`, `OPS-01`, `OPS-02`, `OPS-03` помечены в реестре `Complete (baseline)` — предсуществующие, не предмет фазы. `ADMIN-02` (`Partial`, 06-01, D-05) не стоит в перечне требований фазы, но покрыт явным утверждением must_have плана 06-01 и закреплён тестом `test_groups_info_gone_from_templates_and_routes` — учтено, а не осиротело.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` в 24 файлах, тронутых фазой | — | **Ни одного вхождения.** Гейт долговых маркеров чист |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` в путях показа | — | **Ни одного.** Два вхождения `placeholder=` — атрибуты HTML-полей ввода (`users.html:63`, `logs.html:64`), не заглушки |
| — | — | Данные макета («18 д 4 ч», «MRR 621 000 ₽», «восстановлен после рестарта») | — | **Ни одного.** Закреплено `test_no_mockup_placeholder_numbers_reached_the_subsections` |
| — | — | Мёртвые действия («Остановить воркер», «Очистить очередь», «Продлить доступ», тарифный план, средний чек) | — | **Ни одного в разметке и маршрутах.** Все совпадения grep — комментарии, объясняющие отсутствие; закреплено `test_no_stop_action_exists_in_markup_or_in_routes`, `test_no_wholesale_queue_wipe_exists_in_the_markup_or_in_the_routes`, `test_no_manual_extension_of_access_exists`, `test_the_dead_tariff_plan_never_reaches_the_markup` |

### Прохибиции (34, все judgment-tier)

**НЕ АВТОРИТЕТНЫЙ вердикт LLM-судьи: нарушений не найдено.** Проверено разбором кода и разметки 12 из 34; остальные 22 не опровергнуты, но и не проверены поимённо. Флаг: `unverified-prohibition — human review recommended`.

Проверены предметно: данные макета в подразделах (нет); «офлайн» на штатном состоянии (три состояния разведены, `test_workers_subsection_shows_offline_only_with_pending_queue`); `secure` безусловным литералом (нет — из настройки); доказательство источника кода сравнением значений (нет — по AST); константы инвентаризации отдельным коммитом (правлены вместе); инцидент без условия снятия (все пять снимаются); единая формула отложенности для обоих каналов (нет — канал обязательный аргумент); пустой список при недоступном источнике (нет — отдельное поле `unavailable`); фильтр уровня из одного слова (нет — `warn` покрывает `warn` и `warning`); вторая агрегация отправок в админке (нет — `test_admin_uses_analytics.py` зелен); тарифный план и средний чек (нет); чёрный список маршрутов в гейте (нет — три объявленных множества с доказанными зубами).

### Human Verification Required

См. `human_verification` во frontmatter — восемь пунктов: шесть неисполненных пунктов человеческой приёмки плана 06-14 (журнал `.planning/WINDOWS.md`, запись 5, `open`) и два решения владельца.

### Warnings

**WR-01 (нужно решение владельца). `.planning/REQUIREMENTS.md` несёт фактически неверное утверждение о кодовой базе.** Строки 283, 297 и 324 реестра — и таблица человеческой приёмки в `06-14-SUMMARY.md` (строка 185) — утверждают, что `monitoring/promtail.yml` метку потока `level` не создаёт ни одним правилом и что его `pipeline_stages` состоят из одного `- docker: {}`. **Проверено мной чтением всего файла: это неверно.** За стадией `- docker: {}` идут ТРИ блока `match`, каждый из которых извлекает `level` из тела строки и поднимает его в метку Loki: compose-сервисы (структурированный лог Python, `level` строкой), `broadcaster_role="wa-worker"` (Pino, числовой уровень переводится шаблоном 10…60 в слова) и `broadcaster_role="max-worker"`. Значения сходятся с `LEVEL_CHIPS` клиента (`loki_client.py:114-119`) с обеих сторон: `error/critical/fatal`, `warn/warning`, `info`. `git show 4fee745:monitoring/promtail.yml` показывает те же правила НА БАЗОВОМ КОММИТЕ фазы, и ни один коммит фазы этот файл не трогал — то есть находка была неверна и в момент её записи. Журнал `.planning/WINDOWS.md` эту запись (id 6) уже снял как `waived`; **реестр требований и сводка плана 06-14 остались неисправленными.** Последствие: одна из двух названных причин статуса `Partial` у ADMIN-09 недействительна, и следующий читатель пойдёт чинить работающий конфиг. Правка реестра — решение владельца, не работа верификатора.

**WR-02 (нужно решение владельца). Объявление артефакта в `must_haves` плана 06-11 расходится с кодом.** План требует `def monthly_revenue` внутри `app/application/admin/payments_query.py`; функция живёт в `app/application/admin/overview_stats.py:94`, а три условия платящей подписки — в `app/repositories/user.py:111-115`. Это ЕДИНСТВЕННАЯ непройденная проверка артефактов на 14 планах. **Продуктовое утверждение при этом выполнено:** выручка считается без льготных по трём условиям, и переезд функции в `payments_query.py` ослабил бы машинный гейт `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`. Записано журналом (`WINDOWS.md`, запись 3, `open`) самим исполнителем с просьбой о решении владельца.

**WR-03 (принятая цена, знать до выката).** Инфраструктурный блок «Воркеров» будет показывать «отключён» до перевыката трёх celery-контейнеров: признак живости пишут сами процессы обработчиками `beat_init`/`worker_init` раз в 30 с (D-52, `WINDOWS.md` запись 7, `open`). Это отсутствие ещё не выкаченного источника, а не ложное показание, — но на экране выглядит аварией.

**WR-04 (предсуществующее, вне предмета фазы).** Grafana проксируется наружу обоими шаблонами nginx с паролем `admin/admin` по умолчанию, а переменная `GRAFANA_ADMIN_PASSWORD` в `.env.example` не упомянута (`WINDOWS.md` запись 8, `open`; найдено код-ревью как IN-04). Проксирование предшествует фазе 6; фаза трогала шаблоны только ради HSTS.

**WR-05 (пробел покрытия, малый).** Направление РАЗБЛОКИРОВКИ через маршрут `POST /admin/users/{id}/block` не проходится ни одним тестом: `test_the_admin_toggle_blocks_a_user` проверяет постановку признака, а `test_unblocking_returns_the_schedule_to_the_selection` снимает признак напрямую, минуя маршрут. Обработчик — симметричный `is_blocked = not is_blocked`, поэтому риск невелик, но критерий 2 называет разблокировку прямо. Не блокер.

**WR-06 (предсуществующее).** `tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` краснеет в полном прогоне — единственная причина ненулевого кода возврата у `just test`. Воспроизводится на базовом коммите фазы `4fee745` двумя минимальными наборами; причина названа проектом (`templates` — модульный синглтон на процесс). `WINDOWS.md` запись 1, `open`; `deferred-items.md` несёт разбор.

### Gaps Summary

**Блокирующих разрывов не найдено.** Цель фазы — «одна админ-панель с подразделами вместо разрозненных админ-страниц» — достигнута в коде: шесть подразделов достижимы отдельными маршрутами, вкладки суть ссылки и переживают выключенный JS, справочник групп снесён, все восемь путей показа тянут данные из живых источников, а не из литералов. Долги безопасности, свёрнутые в фазу решением D-49, закрыты все три (CR-01, CR-02, CR-03), и оба блокера код-ревью (обход гарда имперсонации произвольным заголовком `Authorization`; отсутствие гарда происхождения на блокировке, удалении и выдаче льготы) исправлены и закреплены — второй машинным гейтом с доказанными зубами, а не докстрингом. Прогон 18 тестовых файлов фазы дал 454 passed, 0 failed.

**Фаза не `passed` по двум причинам, и обе честные, а не бухгалтерские.**

Первая: критерии 4 и 5 наполовину опираются на утверждения, которые сами планы объявили `verification: backstop`, — живое чтение Redis и Loki и пригодность вёрстки на 375 px. Ни одно значение подразделов «Воркеры», «Очередь» и «Логи» никогда не читалось из живого источника: вся суита идёт на подменённых клиентах и доказывает контракт приложения ПРИ данном ответе источника, но не имена ключей, имена контейнеров и метки потоков в бою. Вьюпорт 375 px не рендерился ни разу — машинное свидетельство есть, но оно другого рода (утверждения о разметке, а не измерение переполнения), и подменять им критерий, чья формулировка говорит о человеческой пригодности, значило бы отчитаться о непроверенном как о проверенном. Ровно это записал и сам план 06-14, пометив все шесть своих пунктов приёмки ❌ НЕ ПРОВЕДЕНО, и ровно поэтому реестр держит ADMIN-07 и ADMIN-09 в статусе `Partial`. **Консервативная отметка обоснована и поднимать её вверх не следует** — до прогона стенда.

Вторая: реестр требований несёт фактически неверное утверждение о `monitoring/promtail.yml` (WR-01). Я прочитал файл целиком и его версию на базовом коммите фазы: метку `level` сборщик создаёт тремя блоками `match`, значения сходятся с `LEVEL_CHIPS` клиента с обеих сторон, и правила эти существовали ДО фазы. Находка была неверна в момент записи — автор дочитал конвейер до первой стадии. Журнал это уже снял, реестр и сводка плана 06-14 — нет. Оставленная как есть, запись отправит следующего читателя чинить работающий конфиг и держит вторую, недействительную причину под статусом `Partial` у ADMIN-09.

Плюс два открытых решения владельца (WR-02 — расхождение объявления артефакта плана 06-11 с местом функции; WR-01 — правка реестра) и два предсуществующих долга вне предмета фазы (WR-04 Grafana, WR-06 порядковая зависимость суиты).

---

_Verified: 2026-08-23T16:49:38Z_
_Verifier: Claude (gsd-verifier)_

---

## Закрытие человеческих пунктов — UAT 2026-08-24

Этот отчёт был выпущен 2026-08-23 со статусом `human_needed`. Он не нашёл дефектов:
код обоих незакрытых утверждений был отгружен и зелен, а `human_needed` стоял по
одной названной причине — **исполнитель работал в изолированном рабочем дереве без
живого стенда**, и пять поведений фазы никогда не наблюдались против живых Redis и
Loki. Сессия `/gsd-verify-work 6` от 2026-08-24 провела эти наблюдения.

| # | Пункт | Результат |
|---|-------|-----------|
| 1 | Шесть подразделов на ширине 375 px в браузере | ✅ pass |
| 2 | Простой воркера: `docker kill`, ожидание > 90 с, `/admin/workers` | ✅ pass |
| 3 | Плашка недоступного источника логов при остановленном мониторинге | ✅ pass |
| 4 | Имена контейнеров против словаря `LOG_SOURCES` | ✅ pass |
| 5 | Метка уровня у строк в бою — чип уровня даёт непустую выдачу | ✅ pass |
| 6 | Видимость `wa:queue:*` из веб-процесса | ✅ pass |
| 7 | РЕШЕНИЕ ВЛАДЕЛЬЦА: запись о `monitoring/promtail.yml` | ✅ pass |
| 8 | РЕШЕНИЕ ВЛАДЕЛЬЦА: запись 3 журнала окон (план 06-11) | ✅ pass |

**Итог: 8/8 pass, 0 дефектов.** Оба утверждения из `behavior_previously_unverified`
закрыты: критерий 4 — пунктами 2, 3, 5 и 6; критерий 5 — пунктом 1.

### Что из этого последовало в других артефактах

- **ADMIN-07 и ADMIN-09 переведены `Partial` → `Complete`** в `.planning/REQUIREMENTS.md`.
  Единственной причиной `Partial` у обоих было непроведённое живое чтение; за правкой
  не стоит ни одной изменённой строки продукта.
- **`must_haves` плана 06-11 исправлены, код НЕ тронут** (решение владельца, пункт 8):
  `monthly_revenue` живёт в `overview_stats.py:94` рядом со счётом платящих, который
  её кормит, а три условия — в `paying_subscription_clauses`. Переезд функции ослабил
  бы гейт `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`.
- **Отозванная находка о `promtail.yml` подтверждена отозванной уже стендом**, а не
  только чтением репозитория (пункт 5).

### Что этот отчёт по-прежнему НЕ утверждает

⚠️ **`prohibitions_flagged` не изменился и остаётся таким, каким был выпущен.** Вердикт
судьи «НЕ АВТОРИТЕТНО» стоит в силе: выборочно проверено 12 из 34 прохибиций,
нарушений не найдено; **остальные 22 не опровергнуты, но и не проверены поимённо.**
Человеческая приёмка эту цифру не двигала — она проверяла поведение на стенде, а не
прохибиции, и записывать её как закрытие прохибиций было бы подменой предмета.

⚠️ Свежесть отчёта была нарушена доку-правкой: `06-14-SUMMARY.md` (16:54) оказался
новее отчёта (16:52) из-за коммита `e4704cd`, снявшего ложную запись о `promtail.yml`.
Причиной был отзыв документации, а не новый код; настоящая правка — этот раздел.

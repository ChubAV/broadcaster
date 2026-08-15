---
phase: 04-dashbord-i-istoriya
plan: 11
subsystem: ui
tags: [dashboard, jinja2, sqlalchemy, shell-context, dash-05, gap-closure]

# Dependency graph
requires:
  - phase: 01-shell
    provides: "get_shell_context — публичный контракт живых данных шелла (D-09/D-19)"
  - phase: 04-dashbord-i-istoriya
    provides: "04-01 (плитки, next_step), 04-05 (индикатор сессий и оба структурных запрета)"
provides:
  - "Ключ sessions в контракте шелла — перечень messenger-аккаунтов с состоянием каждого"
  - "sessions_online / sessions_total / nav_counts.accounts как ПРОИЗВОДНЫЕ от перечня"
  - "Блок «Воркеры аккаунтов» в теле дашборда с пустым состоянием"
  - "Макрос worker_row — единственное определение разметки строки перечня"
  - "Запрет Docker на пути рендера расширен на модуль контекста шелла"
affects: [phase-06-admin, worker-state, shell-contract]

# Actuals (#2632)
actuals:
  tokens: 9522
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Один источник, три представления: перечень и оба его агрегата считаются из одного чтения"
    - "Колоночная проекция вместо ORM-объекта как граница секретов на пути в шаблон"
    - "Запрет на пути рендера следует за модулем-владельцем чтения, а не за именем страницы"

key-files:
  created:
    - app/templates/dashboard/includes/worker_row.html
  modified:
    - app/pages/common.py
    - app/pages/dashboard.py
    - app/templates/dashboard.html
    - app/static/css/app.css
    - tests/test_pages/test_shell.py
    - tests/test_pages/test_responsive_markup.py

key-decisions:
  - "Перечень живёт в теле дашборда, а не в шапке шелла: шапка рендерится на всех 26 маршрутах, и перечень аккаунтов был бы шумом на 25 экранах, к DASH-05 отношения не имеющих"
  - "Агрегаты переведены в производные от перечня: сняты два скалярных подзапроса по messenger_accounts, оба числа считаются на стороне Python из одного прочитанного списка"
  - "Проекция трёх колонок (id, type, status) вместо ORM-объекта — credentials и session_data физически не попадают в словарь, который печатается на каждой странице"
  - "Незнакомый статус показывает СЫРОЕ значение и остаётся в перечне; онлайном не считается"
  - "Заголовок пустого состояния — «Каналы не подключены», а не «Аккаунты не подключены»: слово «Аккаунты» в теле дашборда запрещено D-01, и обходить запрет переписыванием его теста было бы подменой"
  - "Тест числа запросов утверждает N-инвариантность, а не константу упоминаний таблицы: блок DASH-02 присоединяет messenger_accounts своим запросом независимо от перечня"

patterns-established:
  - "WORKER_ONLINE_STATUS: предикат «воркер онлайн» объявлен один раз и используется и перечнем, и агрегатом"
  - "Строка перечня — макрос с явным параметром и собственным словарём подписей; страница делегирует, а не рисует"

requirements-completed: [DASH-05, DASH-01, DASH-02, DASH-03, DASH-04]

coverage:
  - id: D1
    description: "Пользователь читает с дашборда, КАКОЙ из его аккаунтов онлайн, а какой нет — перечнем, а не одним числом"
    requirement: DASH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_lists_each_account_with_its_worker_state"
        status: pass
    human_judgment: false
  - id: D2
    description: "Аккаунт с незнакомым статусом остаётся в перечне и показывает своё сырое значение"
    requirement: DASH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_worker_list_keeps_an_unrecognised_status_visible"
        status: pass
    human_judgment: false
  - id: D3
    description: "Пользователь без аккаунтов видит на месте перечня пустое состояние с призывом подключить канал"
    requirement: DASH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_worker_list_shows_an_empty_state_without_accounts"
        status: pass
    human_judgment: false
  - id: D4
    description: "Аккаунты другого пользователя в перечень и в счёт не попадают"
    requirement: DASH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_worker_list_excludes_another_users_account"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ни учётные данные, ни строка сессии messenger-аккаунта на дашборд не выводятся"
    requirement: DASH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_shell_worker_list_carries_no_secrets"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_shell_worker_entries_expose_only_the_declared_keys"
        status: pass
    human_judgment: false
  - id: D6
    description: "Число в пилюле шелла и перечень не могут разойтись: оба выведены из одного прочитанного списка"
    requirement: DASH-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_shell_aggregate_is_derived_from_the_worker_list"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_page_has_no_second_source_of_the_sessions_number"
        status: pass
    human_judgment: false
  - id: D7
    description: "Поаккаунтное чтение стоит одно обращение и не растёт с числом аккаунтов (нет N+1 на пути рендера)"
    requirement: DASH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_shell_reads_worker_state_in_a_single_query"
        status: pass
    human_judgment: false
  - id: D8
    description: "Путь рендера дашборда, включая новый модуль-владелец чтения состояния воркеров, не обращается к Docker"
    requirement: DASH-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_dashboard_render_path_never_touches_docker"
        status: pass
    human_judgment: false
  - id: D9
    description: "Перечень читается на ширине 320 px без горизонтальной прокрутки; состояния на экране совпадают с разделом /accounts"
    requirement: DASH-05
    verification: []
    human_judgment: true
    rationale: "Автоматической проверки ширины в проекте нет — план объявил это утверждение backstop-ом. Совпадение экрана с /accounts и поведение при отключении аккаунта проверяются глазами на живом сервере (задача 4, блокирующий чекпоинт)."

# Metrics
duration: 35 min
completed: 2026-08-15
status: halted
---

# Phase 04 Plan 11: Перечень воркеров аккаунтов на дашборде Summary

**Дашборд отвечает на DASH-05 перечнем: строка на каждый messenger-аккаунт с его состоянием, выведенная из одного чтения контракта шелла, из которого теперь считаются и оба числа пилюли.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-08-15T09:16:19Z
- **Completed:** 2026-08-15T09:51:19Z
- **Tasks:** 3 из 4 (задача 4 — блокирующий чекпоинт ручной приёмки, не выполнялся)
- **Files modified:** 7 (1 создан, 6 изменены)

_Метод `actuals.tokens`: chars/4 по РЕАЛИЗОВАННОМУ ДИФФУ (38 089 символов → 9 522). Для сведения: те же chars/4 по ПОЛНОМУ содержимому семи затронутых файлов дают 100 136. Оценка плана — 62 000. Две шкалы дают числа по обе стороны от оценки, поэтому метод назван явно: сравнивать актуал с оценкой можно только на одной из них._

## Accomplishments

- `get_shell_context` отдаёт перечень `sessions` (`id`, `type`, `status`, `is_online`) одним запросом по индексированному `user_id`; из склейки счётчиков сняты ДВА скалярных подзапроса по `messenger_accounts`, и `sessions_online`, `sessions_total`, `nav_counts.accounts` стали производными от перечня — второму источнику числа взяться неоткуда.
- Блок «Воркеры аккаунтов» в теле дашборда: строка на аккаунт с точкой состояния, подписью канала, идентификатором и подписью «Онлайн» / «Отключён» / сырым значением незнакомого статуса. Аккаунт со статусом, которого интерфейс не знает, из перечня НЕ выпадает.
- Пустое состояние вместо перечня у пользователя без аккаунтов; сам блок условием не обёрнут — спрятанная карточка читалась бы как сломанная страница.
- Запрет Docker на пути рендера расширен с трёх модулей до четырёх: `app/pages/common.py` вошёл в `DASHBOARD_RENDER_PATH`, потому что именно он теперь владеет чтением состояния воркеров. Ни один существующий ассерт двух структурных тестов не снят и не ослаблен.
- Девять новых тестов; в файле было 102 `assert`, стало 134.

## Task Commits

1. **Задача 1 (tracer, TDD RED): падающие тесты перечня** — `1fc0b35` (test)
2. **Задача 1 (tracer, TDD GREEN): поаккаунтное чтение в контракте шелла** — `650a2e9` (feat)
3. **Задача 2: ширина перечня — все ветки статуса, пустое состояние, стили** — `2f0382d` (feat)
4. **Задача 3: запрет Docker следует за кодом; цена закреплена тестами** — `34e42d2` (test)

## Files Created/Modified

- `app/templates/dashboard/includes/worker_row.html` — **создан.** Макрос `worker_row(session)`: единственное определение разметки строки, три ветки подписи состояния, собственный словарь подписей каналов.
- `app/pages/common.py` — `WORKER_ONLINE_STATUS`; поаккаунтное чтение колоночной проекцией; агрегаты выведены из перечня; докстринг дополнен (объяснение запрета Docker сохранено дословно).
- `app/pages/dashboard.py` — проброс `sessions` из `request.state.shell` с пустым списком по умолчанию; собственного запроса страница по-прежнему не делает.
- `app/templates/dashboard.html` — блок перечня между плитками и парой макета, импорт и вызов макроса, пустое состояние.
- `app/static/css/app.css` — `.worker-list` (прокрутка вместо обрезки), `.worker-row` и модификаторы; точка перечня внесена в `prefers-reduced-motion`.
- `tests/test_pages/test_shell.py` — девять тестов, расширенный посев, четвёртый модуль в `DASHBOARD_RENDER_PATH`.
- `tests/test_pages/test_responsive_markup.py` — перепись шапок блоков страницы: 2 → 3.

## Decisions Made

См. `key-decisions` во фронтматтере. Несущее: перечень и оба его числа считаются из ОДНОГО чтения, поэтому разойтись им физически не с чем; секреты не попадают в контракт не по договорённости, а потому что проекция их не выбирает.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Неверный путь в команде проверки задачи 2**

- **Found during:** Задача 2
- **Issue:** `<verify>` называет `tests/test_pages/test_components.py`; такого файла нет — он лежит в `tests/test_templates/test_components.py`. Pytest завершался с ошибкой сбора, не выполнив НИ ОДНОГО теста (`1 warning in 0.00s`), то есть проверка молча не проверяла ничего.
- **Fix:** Использован фактический путь. Файлы и их содержимое не менялись.
- **Verification:** `uv run pytest tests/test_pages/test_shell.py tests/test_pages/test_dashboard.py tests/test_pages/test_responsive_markup.py tests/test_templates/test_components.py -q` → 292 passed.
- **Committed in:** `2f0382d`

**2. [Rule 1 - Bug] Заголовок пустого состояния нарушал запрет D-01**

- **Found during:** Задача 2
- **Issue:** Заголовок «Аккаунты не подключены», названный планом дословно, содержит слово «Аккаунты», запрещённое в теле дашборда решением D-01 (снятые плитки-счётчики дублировали боковое меню). Тест `test_dashboard_body_has_no_entity_counters` покраснел.
- **Fix:** Заголовок изменён на «Каналы не подключены» — смысл сохранён, слово-счётчик из тела ушло. Существующий запрет НЕ ослаблялся: править чужой тест ради своей формулировки значило бы снять действующее решение фазы, а не починить свой блок. В шаблоне оставлен комментарий с причиной.
- **Files modified:** `app/templates/dashboard.html`, `tests/test_pages/test_shell.py` (собственный ассерт нового теста)
- **Verification:** `test_dashboard_body_has_no_entity_counters` зелёный.
- **Committed in:** `2f0382d`

**3. [Rule 1 - Bug] Перепись шапок блоков дашборда разошлась с числом блоков**

- **Found during:** Задача 2
- **Issue:** `test_dashboard_blocks_share_one_head_without_a_divider` утверждает `page.count("data-blockhead") == 2`. Новый блок — четвёртый на странице и несёт ту же общую шапку, поэтому счёт стал 3.
- **Fix:** Ожидаемое число поднято до 3 с комментарием, что это ПЕРЕПИСЬ блоков страницы. Смысл утверждения сохранён и не ослаблен: собственная шапка в обход общего атрибута это число НЕ увеличила бы, то есть тест по-прежнему краснеет ровно на том дефекте, ради которого написан. Остальные его ассерты (запрет `card_open(title=)`, отсутствие копий правила, наличие разделителя как примитива) не тронуты.
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Verification:** тест зелёный; `uv run pytest tests/test_pages/ -q` → 723 passed.
- **Committed in:** `2f0382d`

**4. [Rule 1 - Bug] Тест числа запросов в формулировке плана не мог пройти никогда**

- **Found during:** Задача 3
- **Issue:** План требует утверждать, что число обращений, ЧЕЙ ТЕКСТ УПОМИНАЕТ `messenger_accounts`, равно единице. На рендере дашборда таких обращений два, и второе к перечню отношения не имеет: блок ближайших отправок (DASH-02) присоединяет `messenger_accounts` к расписаниям своим запросом. Утверждение краснело бы на исправном коде и — что хуже — не поймало бы N+1, если бы кто-то снял блок DASH-02.
- **Fix:** Тест утверждает ДВЕ вещи, обе про перечень: (а) собственное чтение состояния воркеров (`FROM messenger_accounts`) ровно одно; (б) число обращений к таблице НЕ РАСТЁТ при переходе с трёх аккаунтов на шесть. Пункт (б) и есть настоящая проверка на N+1: запрос на строку константой не ловится. Цель теста из плана (T-04-G1-03) сохранена и усилена.
- **Files modified:** `tests/test_pages/test_shell.py`
- **Verification:** `test_shell_reads_worker_state_in_a_single_query` зелёный; проверено, что при трёх и шести аккаунтах счёт одинаков.
- **Committed in:** `34e42d2`

---

**Total deviations:** 4 auto-fixed (1 blocking, 3 bugs)
**Impact on plan:** Область не расширена, ни один существующий запрет не ослаблен. Два отступления (2 и 4) — расхождения самого плана с уже действующими решениями фазы (D-01) и с фактическим составом запросов страницы; оба разрешены в пользу действующего кода, а не в пользу буквы плана.

## Issues Encountered

**Тест секретов проходил ДО реализации (наблюдение по TDD-гейту).** В фазе RED задачи 1 два теста поведения упали, как и требовалось, а `test_shell_worker_list_carries_no_secrets` прошёл сразу: пока перечня нет, утечке взяться неоткуда. Тест не переписывался и не удалялся — это страж границы (T-04-G1-02), чья ценность вся в том, что он останется зелёным ПОСЛЕ появления перечня; ложным зелёным он был ровно один прогон. Оба теста поведения (`..._lists_each_account_with_its_worker_state`, `..._excludes_another_users_account`) прошли полный цикл RED → GREEN.

**`graphify update .` не выполнялся — перенесён в основной чекаут.** Правило `CLAUDE.md` требует обновлять граф после правки кода, но `graphify-out/` в этом worktree отсутствует (артефакт не под контролем версий и живёт только в основном чекауте). Обновление графа здесь построило бы его с нуля во временном каталоге, который будет удалён вместе с worktree, и не попало бы ни в один коммит. Команду следует выполнить в основном чекауте после слияния ветки.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Задачи 1-3 выполнены и закоммичены, весь страничный слой зелёный (723 passed).
- **Задача 4 — блокирующий чекпоинт ручной приёмки — НЕ выполнялась.** Отсюда `status: halted`: план завершён по коду, но его собственная проверка (`<verification>` п. 4: «чекпоинт закрыт словом approved») не закрыта. После приёмки статус подлежит переводу в `complete`.
- Контракт шелла остаётся публичным и готов к переиспользованию Фазой 6: состояние по контейнерам и по каналам в него НЕ вводилось, перечень по-прежнему читает только `MessengerAccount.status` (D-19).

## Self-Check: PASSED

- `app/templates/dashboard/includes/worker_row.html` — FOUND на диске.
- Все четыре коммита задач присутствуют в истории ветки (`1fc0b35`, `650a2e9`, `2f0382d`, `34e42d2`).
- Критерии приёмки задач 1-3 прогнаны поштучно и зелёные, включая дискриминирующий `1 0` (на исходном дереве — `1 2`), перепись `DASHBOARD_RENDER_PATH` = 4, дословное присутствие всех четырёх ассертов двух структурных тестов и рост числа `assert` со 102 до 134.
- Проверки плана: `tests/test_pages/` → 723 passed; связка из `<verify>` задачи 2 (с исправленным путём) → 292 passed.
- Область не расширена: `app/pages/history.py`, `app/repositories/send_log.py`, `.planning/REQUIREMENTS.md` не изменялись.

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-15*

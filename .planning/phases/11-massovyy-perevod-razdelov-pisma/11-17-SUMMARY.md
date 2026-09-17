---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 17
subsystem: ui
tags: [htmx, fastapi, jinja2, hx-location, form_wrapper, in-flight-claim, id-bounds]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-16 — accounts_retry_sync на слое ответа; 11-02 — PostIdPath и id_in_column; 11-08/11-15 — respond()"
provides:
  - "accounts_sync_groups на respond(): восемь выходов, на htmx 204 + HX-Location, без htmx прежний 302"
  - "заявка _SYNC_IN_FLIGHT освобождается на каждом выходе после занятия — доказано поведением и двумя мутантами"
  - "форма запуска синхронизации на экране групп через form_wrapper без цели подмены, data-syncing на обёртке"
  - "accounts_delete, accounts_retry_sync, accounts_sync_groups на PostIdPath; окно 51 8 → 5"
affects: [11-18, 11-19, 11-20, phase-11-verification, phase-15]

actuals:
  tokens: 14915
  tasks: 3
  commits: 5
plan_head_before: 69de8506b8fffc9d2065d3b0f58ce81082b164ca

tech-stack:
  added: []
  patterns:
    - "Утечка внутрипроцессной заявки ловится ПОВЕДЕНИЕМ: после htmx-выхода следующая синхронизация того же аккаунта обязана дойти до мессенджера"
    - "Выход до занятия заявки не освобождает чужую заявку — отдельный тест с заранее занятым реестром"
    - "Атрибут, который форма несла сама (data-syncing), переезжает на обёртку-предка; CSS адресуется носителем без имени тега"

key-files:
  created: []
  modified:
    - app/pages/accounts.py
    - app/templates/account_groups/list.html
    - app/static/css/app.css
    - tests/test_routes/test_sync_groups.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_identifier_bounds.py

key-decisions:
  - "11-17: все восемь выходов accounts_sync_groups — respond(redirect=…); выходы после _claim_sync_slot стоят ВНУТРИ внешнего try (AST: между занятием и try ноль операторов, return после try нет, единственный _release_sync_slot в finally)"
  - "11-17: освобождение заявки доказано поведением по четырём исходам (успех, отказ моста, неожиданное исключение, конфликт уникальности) и двумя незакоммиченными мутантами: освобождение только без htmx краснит 4/4 исхода при зелёных трёх случаях пар; освобождение на выходе «заявка занята» краснит только новый тест занятой заявки"
  - "11-17: data-syncing переехал на <div> вокруг вызова form_wrapper; оба правила app.css — [data-acct-head] [data-syncing] .btn__icon; рендер до/после в active и syncing: у старой формы только method, action, data-syncing, признак один на экране, кнопка байт в байт"
  - "11-17: id_in_column — первое использование account_id в трёх входах аккаунтов; у синхронизации групп до занятия заявки, у удаления после сверки источника; вне колонки — ветка «аккаунта нет» (/accounts)"

patterns-established:
  - "Тест освобождения заявки: реестр пуст после ответа И следующая синхронизация доходит до мессенджера"

requirements-completed: [FORM-04, FORM-08]

coverage:
  - id: D1
    description: "Синхронизация групп отвечает на htmx 204 + HX-Location на всех выходах (экран групп, /accounts, /login), без htmx — прежний 302 на тот же адрес"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_groups_over_htmx_releases_the_claim_on_every_exit"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_groups_over_htmx_exits_before_the_claim"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[accounts_sync_groups-*]"
        status: pass
    human_judgment: false
  - id: D2
    description: "Заявка _SYNC_IN_FLIGHT освобождается на каждом выходе после занятия и не освобождается отказанным запросом"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_groups_over_htmx_releases_the_claim_on_every_exit"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_groups_over_htmx_busy_claim_is_not_released_by_the_refused_request"
        status: pass
    human_judgment: false
  - id: D3
    description: "Форма запуска синхронизации идёт через form_wrapper без цели подмены; data-syncing на обёртке, правила CSS адресуются обёрткой"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (77 правил, в т.ч. number_of_hidden_callers, no_caller_declares_a_blocking_target)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_header_carries_the_sync_form"
        status: pass
    human_judgment: false
  - id: D4
    description: "Три входа модуля аккаунтов на PostIdPath: величина вне колонки идёт веткой «аккаунта нет», окно 51 8 → 5"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_post_identifier_is_checked_before_its_first_use"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_validation_refusal_divergences_is_declared"
        status: pass
    human_judgment: false
  - id: D5
    description: "В браузере «Синхронизировать всё» обновляет экран групп без перезагрузки, иконка крутится при syncing, Back не предлагает повторить POST"
    requirement: FORM-04
    verification: []
    human_judgment: true
    rationale: "Ручной UAT фазы, пункты 5 и 7 — поведение htmx-перехода, анимация и история браузера тестами не наблюдаются"

duration: 69min
completed: 2026-09-17
status: complete
---

# Phase 11 Plan 17: Синхронизация групп на HX-Location с освобождением заявки Summary

**`accounts_sync_groups` отвечает `HX-Location` на всех восьми выходах, не оставляя заявку `_SYNC_IN_FLIGHT` занятой (доказано поведением и двумя мутантами); форма шапки экрана групп на `form_wrapper` без цели с `data-syncing` на обёртке; три входа аккаунтов на `PostIdPath` — окно 51 8 → 5**

## Performance

- **Duration:** 69 min
- **Started:** 2026-09-17T01:20:58Z
- **Completed:** 2026-09-17T02:29:48Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- **Обработчик.** Все восемь выходов `accounts_sync_groups` идут через `respond(request, redirect=…)`: «нет сессии» — `/login`; «аккаунта нет» (включая чужой и вне колонки) — `/accounts`; тип не поддержан, статус `syncing`, заявка занята, отказ моста, неожиданное исключение и финальный выход (успех либо конфликт уникальности) — экран групп. `RedirectResponse` в обработчике 0. Добавлена докстрока с правилом Pitfall 8.
- **Заявка, проверено по AST на итоговом дереве:** `_claim_sync_slot` — оператор 9 тела, внешний `try` — оператор 10, между ними операторов нет; `return` внутри `try` три, после `try` ни одного; `_release_sync_slot` вызывается один раз, в `finally`; `id_in_column` (строка 839) стоит до `execute` (840) и до занятия заявки (916).
- **Заявка, проверено поведением:** `test_sync_groups_over_htmx_releases_the_claim_on_every_exit` на четырёх исходах проверяет 204 + `HX-Location`, след ветки на аккаунте (что ветка действительно пройдена), пустой реестр, а затем отправляет ещё один htmx-запрос синхронизации и требует, чтобы он дошёл до мессенджера. `test_sync_groups_over_htmx_busy_claim_is_not_released_by_the_refused_request` проверяет, что отказанный запрос не освобождает чужую заявку ни на одном транспорте. `test_sync_groups_over_htmx_exits_before_the_claim` проверяет четыре выхода до заявки: реестр остаётся нетронутым.
- **Мутанты (не закоммичены, откатывались `git checkout -- app/pages/accounts.py`):**
  - (A) в `finally` освобождение только без `HX-Request`: 4 failed / 71 passed. Упали все четыре исхода («htmx-выход оставил заявку занятой»), а три случая пар синхронизации групп остались зелёными: проверка только 204 + заголовка утечку не видит. На том же мутанте при отключённом утверждении по реестру (правка тестового файла, тоже откачена) поведенческое утверждение само дало «следующая синхронизация не дошла до мессенджера» для «успеха», «отказа моста» и «неожиданного исключения». Строку для «конфликта уникальности» и итоговую строку отрезал мой фильтр `head`.
  - (B) выход «заявка занята» вызывает `_release_sync_slot`: 1 failed / 5 passed. Упал только новый тест занятой заявки («htmx: отказанный запрос освободил ЧУЖУЮ заявку»), старый вложенный тест `test_second_sync_during_a_running_sync_does_not_reach_the_messenger` остался зелёным.
- **Разметка.** Форма стала вызовом `form_wrapper(action='/accounts/' ~ account_id ~ '/sync-groups')` без цели (`hx-swap="none"`) внутри `<div>` с условным `data-syncing`. Комментарий «Кнопка при выполнении НЕ отключается» получил следующее поколение: блокировка только на время запроса, защиту даёт серверный guard. Два правила `app.css` (вращение и `prefers-reduced-motion`) теперь адресуются `[data-acct-head] [data-syncing] .btn__icon`, `form[data-syncing]` больше не встречается.
- **Сохранность атрибутов** проверена рендером `/accounts/{id}/groups` до и после в статусах `active` и `syncing` (временный тестовый файл, удалён). У старой формы были только `method="POST"`, `action` и `data-syncing`, атрибутов `x-*`, `@…` и `:…` не было. После правки `data-syncing` встречается на экране один раз (как и раньше) на обёртке, кнопка байт в байт та же, регистр метода стал `post`.
- **Окно 51.** `accounts_delete`, `accounts_retry_sync` и `accounts_sync_groups` перешли на `PostIdPath`, и первым использованием `account_id` стал `id_in_column`. Для удаления проверка стоит после сверки источника, для синхронизации групп — до занятия заявки. Ложный результат ведёт в ветку «аккаунта нет».

## Task Commits

1. **Задача 1: синхронизация групп на слое ответа.** RED `3897b6d` (test), GREEN `a1a561d` (feat)
2. **Задача 2: форма на обёртке, data-syncing на обёртке.** `133561f` (feat)
3. **Задача 3: окно 51, три входа аккаунтов.** RED `36538f9` (test), GREEN `f80c5df` (feat)

## TDD Gate Compliance

- **Задача 1 RED.** Команда `pytest tests/test_routes/test_sync_groups.py tests/test_pages/test_htmx_post_pairs.py`, rc=1: 75 тестов, 13 падений. Целевой тест `test_sync_groups_over_htmx_releases_the_claim_on_every_exit[отказ моста]` упал с `AssertionError: отказ моста: 302 / assert 302 == 204`. Остальные падения: ещё три исхода и пять выходов до заявки (`assert 302 == 204`), три случая пар («слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ»), реестр `40 == 37`. Причина в дереве — литерал `RedirectResponse` на `accounts.py:930`. `check tdd-red-evidence` → `RED_EVIDENCE_OK`. Первая попытка дала `INVALID_RED (no_target_test_failure)`: мой конвертер JUnit→TAP сравнивал `\uXXXX`-экранированные имена параметров с декодированной целью. После декодирования обеих сторон — OK. Это дефект конвертера, прогон был в порядке.
- **Задача 1 GREEN** `a1a561d` после `3897b6d`: 278 passed.
- **Задача 3 RED.** Команда `pytest tests/test_pages/test_identifier_bounds.py tests/test_pages/test_htmx_post_pairs.py`, rc=1: 65 тестов, 3 падения. Целевой `test_every_bounded_input_refuses_a_value_outside_the_column` выдал «Несогласных строк 9 из 81»: ровно три входа × три величины (2147483648, 26 девяток, 0), все `422 (ожидалось 302 /accounts)`. Пара вне колонки получила «путь деградации ответил 422 вместо 302», реестр — `41 == 40`. `RED_EVIDENCE_OK`.
- **Задача 3 GREEN** `f80c5df` после `36538f9`: 226 passed.
- Задача 2 не TDD (`type="auto"`). REFACTOR не понадобился.

## Числа (каждое поставлено прогоном покрасневшего правила, летопись с дословным отказом)

| Константа | Было → стало | Отказ |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 16 → 15 | `число непереведённых обработчиков стало 15, а в файле записано 16` |
| `POST_PAIR_CASES_DECLARED` | 37 → 40 → 41 | `случаев пар в реестре 40, объявлено 37`; `… 41, объявлено 40` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 63 → 71 | `вызовов слоя ответа БЕЗ фрагмента найдено 71, а объявлено 63`; карта назначений не изменилась |
| `MACRO_DEFINITION_SITES_CALLERS_DECLARED` | 20 → 21 | `за перечнем мест определения макросов спрятано вызывающих 21, объявлено 20` |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 12 → 13 | `блоков вызова макроса-обёртки разобрано 13, объявлено 12` |
| `SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED` | 60 → 61 | `подстановка вернула 61 объявлений вместо измеренных 60` (план это число не называл) |
| `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` | 8 → 5 | `расхождений формы отказа валидации стало 5, а объявлено 8` |

## Files Created/Modified

- `app/pages/accounts.py`: `accounts_sync_groups` на `respond()` с докстрокой; три входа на `PostIdPath` + `id_in_column`.
- `app/templates/account_groups/list.html`: импорт `form_wrapper`, форма через обёртку, `data-syncing` на `<div>`, поколение комментария.
- `app/static/css/app.css`: два селектора признака идущей синхронизации адресуются обёрткой.
- `tests/test_routes/test_sync_groups.py`: три новых теста (4 + 1 + 4 случая).
- `tests/test_pages/test_htmx_post_pairs.py`: четыре случая (синхронизация групп ×3, повторная синхронизация вне колонки), число 41.
- `tests/test_pages/test_htmx_gates.py`: ключ снят из `NOT_YET_CONVERTED` (15), три записи сняты из окна 51 (5).
- `tests/test_pages/test_hx_location_destinations.py`: 71.
- `tests/test_templates/test_htmx_markup_gates.py`: вызывающий `account_groups/list.html` (21), блоки (13).
- `tests/test_pages/test_account_groups.py`: 61; метод формы сличается без учёта регистра.
- `tests/test_pages/test_identifier_bounds.py`: `outside="302 /accounts"` у трёх строк матрицы и поколение комментария.

## Decisions Made

См. `key-decisions` во frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Правка `tests/test_pages/test_account_groups.py` (нет в `files_modified`)**
- **Found during:** задача 2
- **Issue:** `test_header_carries_the_sync_form` искал литерал `<form method="POST"`, а макрос печатает `method="post"`. `SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED` поднялось на единицу: форма шапки стала ещё одним местом с `hx-post`.
- **Fix:** сличение без учёта регистра (свойство то же: HTML регистр метода не различает). Число 60 → 61 поставлено прогоном с летописью.
- **Verification:** задача 2 — 532 passed, включая весь `tests/test_templates/`.
- **Committed in:** `133561f`

**2. [Rule 2 - Missing Critical] Два теста сверх §behavior задачи 1**
- **Found during:** задача 1 (указание оркестратора о выходах до заявки)
- **Issue:** план требовал только параметризованный тест четырёх исходов после заявки. Свойство «выход до заявки не трогает её» ничем не охранялось, и мутант B это показал: старый вложенный тест на нём зеленел.
- **Fix:** `test_sync_groups_over_htmx_busy_claim_is_not_released_by_the_refused_request` и `test_sync_groups_over_htmx_exits_before_the_claim`.
- **Committed in:** `3897b6d`

**3. [Rule 2] Случай пар «синхронизация групп — уже идёт» взят через статус `syncing`, а не через занятую заявку**
- Пара запускает обе половины на своих аккаунтах, а внутрипроцессную заявку из обхода пар не занять без вмешательства в модуль. Ступень «заявка занята» на обоих транспортах покрыта тестом занятой заявки в `test_sync_groups.py`.

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 missing critical). **Impact:** расширено покрытие T-11-28, объём продукта не менялся.

## Issues Encountered

- `INVALID_RED` на первой сборке записи RED задачи 1 — дефект моего конвертера (экранированные имена параметров). Исправлен, прогон не повторялся.
- Широкий прогон `tests/test_pages tests/test_routes tests/test_templates tests/test_messengers` (33:48, до конца, не прерван): **1 failed, 2409 passed**. Единственное падение — `tests/test_pages/test_admin_panel.py::test_the_overview_error_number_matches_the_users_own_dashboard` с `assert '2' == '0'`: известное ночное окно (прогон шёл около 01:55–02:29 UTC), не относится к плану, не трогалось. `uv run python -m compileall -q app main.py tests` — без ошибок. `graphify update .` выполнен.

## Threat Flags

Нет. Новых поверхностей нет: T-11-28 закрыт тестами освобождения, T-11-29 — той же веткой «не найден» на обоих транспортах, T-11-30 — guard не тронут, T-11-40 — `id_in_column` первым использованием.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Готов 11-18 (`accounts_connect_max_start`). Ни этот обработчик, ни `accounts_retry_sync` сверх `PostIdPath` не тронуты.
- В окне 51 осталось 5 записей (`account_groups` ×4, `history` ×1) — это план 11-19.
- Ручной UAT, пункты 5 и 7 (синхронизация на экране групп), не проводился — это конец фазы.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-17*

## Self-Check: PASSED

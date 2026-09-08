---
phase: 10-rychag-components-modal-html
plan: 29
subsystem: api
tags: [fastapi, pydantic, validation, identifiers, admin, ast-gate, htmx]

requires:
  - phase: 10-rychag-components-modal-html
    provides: "план 10-28 — матрица «вход → снятый код» на семнадцать продуктовых входов в `tests/test_pages/test_identifier_bounds.py`, девять записей реестра расхождения и `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 17`"
  - phase: 10-rychag-components-modal-html
    provides: "план 10-24 — нейтральный модуль `app/pages/identifiers.py` (`ID_MAX`, `IdPath`, `IdForm`, `OptionalIdForm`) и разрешение псевдонимов границы по всему дереву `app/`"
  - phase: 10-rychag-components-modal-html
    provides: "план 10-22 — реестр `VALIDATION_REFUSAL_DIVERGENCES` и три его правила (полноты, обоснований, авторства)"
provides:
  - "одиннадцать идентификаторов ПУТИ административного модуля `app/pages/admin.py` под общей границей `IdPath` — включая вход под пользователем, блокировку, безлимит и удаление пользователя"
  - "админская половина матрицы входов: два поля `_BoundedEntry` (`identity`, `body`), явное взятие личности `_assume`, отдельный посеянный пользователь-цель и его запись журнала"
  - "матрица «вход → снятый код» выросла 17 → 28 входов: отказ вне диапазона, смежность на границе, антивакуум на живой величине — под ДВУМЯ личностями"
  - "шесть записей реестра расхождения (с восемнадцатой по двадцать третью) с ИЗМЕРЕННОЙ достижимостью, названной ДВУМЯ независимыми способами сужения, и `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 23`"
  - "четвёртая строка летописи объявленного числа с фразой о закрытии перечня ПО ВСЕМУ СТРАНИЧНОМУ СЛОЮ"
  - "контроль зубов правила полноты на ШЕСТИ новых входах — прежний ронял только первую запись перечня"
  - "ПОВТОР НАХОДКИ окна 60: плановая команда снимает ОДИН узел внутрипланового долга, а долг краснит ДВА"
affects: [10-30, 10-31, 10-32, Фаза 11]

actuals:
  tokens: 11465
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "личность обращения есть ПОЛЕ ВХОДА матрицы, а не фикстура правила: две личности живут в одной матрице, потому что предмет у них один"
    - "тело POST-запроса подаётся полем входа там, где обработчик несёт обязательное поле формы — иначе отказ валидации приходит за отсутствие поля, а не за границу"
    - "достижимость входа сужается ДВУМЯ независимыми способами (сборкой и правами), и обоснование обязано назвать их порознь"

key-files:
  created: []
  modified:
    - app/pages/admin.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_htmx_gates.py

key-decisions:
  - "Личность обращения объявлена ПОЛЕМ ВХОДА матрицы (`identity`), а админские входы поставлены в ТУ ЖЕ матрицу, а не в отдельную: предмет у обеих половин один — граница величины идентификатора"
  - "Личность берётся ЯВНЫМ входом (`_assume`), а не порядком разрешения фикстур: `authed_client` и `admin_client` возвращают ОДИН объект клиента"
  - "Антивакуум берёт личность заново перед КАЖДЫМ входом, а не при смене группы: удавшаяся имперсонация перевыписывает ту же cookie на личность цели"
  - "Достижимость каждого админского входа названа ДВУМЯ независимыми сужениями — сборкой и правами: они снимаются порознь, и склеивание их в слово «нулевая» скрыло бы это"
  - "Перечень расхождения вырос на ШЕСТЬ при ОДИННАДЦАТИ закрытых входах: пять стоят на GET-маршрутах, а предмет перечня — контракт формы ответа POST-обработчика (G-2)"

patterns-established:
  - "Отдельный посеянный пользователь-цель для необратимых входов над личностью (T-10-29-05): прогон, подавший саму административную личность, оставил бы следующие строки матрицы без личности"
  - "Контроль зубов правила полноты отбирает записи ПО ВЛАДЕЛЬЦУ (модулю), а не по позиции в перечне: зелёный на первой записи о новом модуле не говорит ничего"

requirements-completed: [FORM-06]

coverage:
  - id: D1
    description: "Одиннадцать идентификаторов пути административного модуля отвечают отказом валидации на величине вне диапазона колонки"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
    human_judgment: false
  - id: D2
    description: "Величина, равная границе, не отвергается ни на одном из двадцати восьми входов"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_admits_the_value_at_the_column"
        status: pass
    human_judgment: false
  - id: D3
    description: "Антивакуум под административной личностью: каждый закрытый вход продолжает работать на живой величине"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_still_admits_a_live_value"
        status: pass
    human_judgment: false
  - id: D4
    description: "Реестр расхождения закрыт по всему страничному слою: обе разности с замером пусты, объявленное число равно двадцати трём"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_framework_bounded_input_is_declared_as_a_divergence"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_declared_validation_refusal_divergences_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D5
    description: "Правило полноты показывает зубы на ШЕСТИ новых входах административного модуля"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_dropping_the_admin_entries_reddens_the_completeness_rule"
        status: pass
    human_judgment: false
  - id: D6
    description: "Поведение боевого драйвера PostgreSQL на НЕОГРАНИЧЕННОМ входе"
    verification: []
    human_judgment: true
    rationale: "У суиты драйвер ОДИН (`sqlite+aiosqlite:///:memory:`); наблюдается отказ на границе приложения, до драйвера. Предмет окна 39 реестра `.planning/WINDOWS.md`, оно остаётся открытым"

duration: 2h 5m
completed: 2026-09-08
status: complete
---

# Phase 10 Plan 29: Административный модуль под общей границей идентификатора — Summary

**Одиннадцать идентификаторов пути `app/pages/admin.py` (вход под пользователем, блокировка, безлимит, удаление) закрыты общим `IdPath` нейтрального модуля, матрица выросла до двадцати восьми входов под двумя личностями, а реестр расхождения закрыт по ВСЕМУ страничному слою: обе разности с замером пусты при объявленном числе 23.**

## Performance

- **Duration:** 2h 5m
- **Started:** 2026-09-08T13:21:00Z
- **Completed:** 2026-09-08T15:26:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- **Самая привилегированная поверхность продукта закрыта той же границей, что и продуктовая.** Одиннадцать целочисленных параметров пути административного модуля переведены на общий псевдоним `IdPath` из `app/pages/identifiers.py`. Тела обработчиков не тронуты ни одной строкой.
- **Граница встала ВЫШЕ гардов админского модуля.** У шести изменяющих маршрутов гард происхождения и проверка прав стоят В ТЕЛЕ, и на негодной величине управление до них не доходило: приведение к целому удавалось, отказ случался позже, уже в SQLAlchemy. По оси ВЕЛИЧИНЫ здесь жила ровно та асимметрия, которую ревизия Фазы 6 (`CR-02`) закрыла по оси ИСТОЧНИКА.
- **Матрица приняла вторую личность, не разделившись надвое.** `_BoundedEntry` получил поля `identity` и `body`; личность берётся явным входом, а не порядком разрешения фикстур.
- **Реестр расхождения закрыт по всему страничному слою:** 17 → 23, обе разности «измеренные ↔ объявленные» пусты, число POST-обработчиков не сдвинуто.

## Task Commits

1. **Задача 1 (RED): админская половина матрицы** — `dc9f84f` (test)
2. **Задача 1 (GREEN): одиннадцать идентификаторов под общей границей** — `a5eb19d` (feat)
3. **Задача 2: реестр расхождения 17 → 23** — `3022a44` (test)

## Files Created/Modified

- `app/pages/admin.py` — одиннадцать параметров пути (`account_id`, `user_id`, `log_id`) переведены с `int` на `IdPath`; ввезён псевдоним нейтрального модуля с записанным основанием
- `tests/test_pages/test_identifier_bounds.py` — одиннадцать админских строк матрицы, поля `identity`/`body`, помощник `_assume`, посев отдельного пользователя-цели и его записи журнала
- `tests/test_pages/test_htmx_gates.py` — шесть записей реестра с измеренной достижимостью, четвёртая строка летописи, `DECLARED = 23`, контроль зубов на шести новых входах

## Замеры, которых требуют критерии приёмки

### 1. КРАСНЫЙ ДО ПРАВКИ — дословно, со всеми несогласными строками

Прогон `uv run pytest tests/test_pages/test_identifier_bounds.py::test_every_bounded_input_refuses_a_value_outside_the_column` на дереве ДО правки сигнатур:

```
AssertionError: ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА СТОИ́Т НЕ НА ВСЕХ ВХОДАХ. Несогласных строк 33 из 84:
    app/pages/admin.py::POST /admin/workers/{account_id}/restart → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /admin/workers/2147483648/restart)
    app/pages/admin.py::POST /admin/workers/{account_id}/restart → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /admin/workers/99999999999999999999999999/restart)
    app/pages/admin.py::POST /admin/workers/{account_id}/restart → адрес account_id ← 0 = 302 (ожидалось 422; POST /admin/workers/0/restart)
    app/pages/admin.py::POST /admin/queue/{account_id}/drop → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /admin/queue/2147483648/drop)
    app/pages/admin.py::POST /admin/queue/{account_id}/drop → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /admin/queue/99999999999999999999999999/drop)
    app/pages/admin.py::POST /admin/queue/{account_id}/drop → адрес account_id ← 0 = 302 (ожидалось 422; POST /admin/queue/0/drop)
    app/pages/admin.py::GET /admin/users/{user_id} → адрес user_id ← 2147483648 = 302 (ожидалось 422; GET /admin/users/2147483648)
    app/pages/admin.py::GET /admin/users/{user_id} → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /admin/users/99999999999999999999999999)
    app/pages/admin.py::GET /admin/users/{user_id} → адрес user_id ← 0 = 302 (ожидалось 422; GET /admin/users/0)
    app/pages/admin.py::GET /admin/users/{user_id}/history → адрес user_id ← 2147483648 = 302 (ожидалось 422; GET /admin/users/2147483648/history)
    app/pages/admin.py::GET /admin/users/{user_id}/history → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /admin/users/99999999999999999999999999/history)
    app/pages/admin.py::GET /admin/users/{user_id}/history → адрес user_id ← 0 = 302 (ожидалось 422; GET /admin/users/0/history)
    app/pages/admin.py::GET /admin/users/{user_id}/history/partial → адрес user_id ← 2147483648 = 302 (ожидалось 422; GET /admin/users/2147483648/history/partial)
    app/pages/admin.py::GET /admin/users/{user_id}/history/partial → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /admin/users/99999999999999999999999999/history/partial)
    app/pages/admin.py::GET /admin/users/{user_id}/history/partial → адрес user_id ← 0 = 302 (ожидалось 422; GET /admin/users/0/history/partial)
    app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес user_id ← 2147483648 = 302 (ожидалось 422; GET /admin/users/2147483648/history/2)
    app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /admin/users/99999999999999999999999999/history/2)
    app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес user_id ← 0 = 302 (ожидалось 422; GET /admin/users/0/history/2)
    app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес log_id ← 2147483648 = 302 (ожидалось 422; GET /admin/users/3/history/2147483648)
    app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес log_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /admin/users/3/history/99999999999999999999999999)
    app/pages/admin.py::GET /admin/users/{user_id}/history/{log_id} → адрес log_id ← 0 = 302 (ожидалось 422; GET /admin/users/3/history/0)
    app/pages/admin.py::POST /admin/users/{user_id}/unlimited → адрес user_id ← 2147483648 = 302 (ожидалось 422; POST /admin/users/2147483648/unlimited)
    app/pages/admin.py::POST /admin/users/{user_id}/unlimited → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /admin/users/99999999999999999999999999/unlimited)
    app/pages/admin.py::POST /admin/users/{user_id}/unlimited → адрес user_id ← 0 = 302 (ожидалось 422; POST /admin/users/0/unlimited)
    app/pages/admin.py::POST /admin/users/{user_id}/impersonate → адрес user_id ← 2147483648 = 302 (ожидалось 422; POST /admin/users/2147483648/impersonate)
    app/pages/admin.py::POST /admin/users/{user_id}/impersonate → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /admin/users/99999999999999999999999999/impersonate)
    app/pages/admin.py::POST /admin/users/{user_id}/impersonate → адрес user_id ← 0 = 302 (ожидалось 422; POST /admin/users/0/impersonate)
    app/pages/admin.py::POST /admin/users/{user_id}/block → адрес user_id ← 2147483648 = 302 (ожидалось 422; POST /admin/users/2147483648/block)
    app/pages/admin.py::POST /admin/users/{user_id}/block → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /admin/users/99999999999999999999999999/block)
    app/pages/admin.py::POST /admin/users/{user_id}/block → адрес user_id ← 0 = 302 (ожидалось 422; POST /admin/users/0/block)
    app/pages/admin.py::POST /admin/users/{user_id}/delete → адрес user_id ← 2147483648 = 302 (ожидалось 422; POST /admin/users/2147483648/delete)
    app/pages/admin.py::POST /admin/users/{user_id}/delete → адрес user_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /admin/users/99999999999999999999999999/delete)
    app/pages/admin.py::POST /admin/users/{user_id}/delete → адрес user_id ← 0 = 302 (ожидалось 422; POST /admin/users/0/delete)
```

**33 из 84 — это РОВНО одиннадцать админских входов на три негодные величины, и ни одной продуктовой строки.** Продуктовая половина матрицы, закрытая планом 10-28, осталась зелёной: правка не задела того, что уже стояло.

### 2. Перечень закрытых параметров — поимённо, снят разбором сигнатур

Замер (`ast`) по `app/pages/admin.py`: параметры, объявленные целыми и стоящие местозаполнителями в пути маршрута.

| # | строка | метод | маршрут (без префикса `/admin`) | обработчик | параметр |
|---|--------|-------|----------------------------------|------------|----------|
| 1 | 873 | POST | `/workers/{account_id}/restart` | `admin_restart_worker` | `account_id` |
| 2 | 1071 | POST | `/queue/{account_id}/drop` | `admin_drop_task` | `account_id` |
| 3 | 1306 | GET | `/users/{user_id}` | `admin_user_detail` | `user_id` |
| 4 | 1355 | GET | `/users/{user_id}/history` | `admin_user_history` | `user_id` |
| 5 | 1464 | GET | `/users/{user_id}/history/partial` | `admin_user_history_partial` | `user_id` |
| 6 | 1551 | GET | `/users/{user_id}/history/{log_id}` | `admin_user_history_detail` | `user_id` |
| 7 | 1552 | GET | `/users/{user_id}/history/{log_id}` | `admin_user_history_detail` | `log_id` |
| 8 | 1583 | POST | `/users/{user_id}/unlimited` | `admin_toggle_free_access` | `user_id` |
| 9 | 1685 | POST | `/users/{user_id}/impersonate` | `admin_impersonate` | `user_id` |
| 10 | 1798 | POST | `/users/{user_id}/block` | `admin_toggle_block` | `user_id` |
| 11 | 1843 | POST | `/users/{user_id}/delete` | `admin_delete_user` | `user_id` |

**ЗАМЕР ИСПОЛНИТЕЛЯ СОШЁЛСЯ С ОРИЕНТИРОМ ПЛАНИРОВЩИКА: одиннадцать против одиннадцати, расхождения нет.** Одиннадцать входов на ДЕСЯТИ маршрутах — маршрут карточки записи журнала несёт два идентификатора.

**Маршрут карточки записи журнала покрыт матрицей ПО ОБОИМ идентификаторам порознь: строк матрицы, приходящихся на него, — ДВЕ** (замер: отбор строк матрицы по `"/history/{log_id}" in key` среди админских даёт `2`).

### 3. Антивакуум — под административной личностью, по всему перечню

**Фикстура личности:** `admin_client` (`tests/conftest.py:290`) — регистрирует пользователя с почтой `settings.admin_email` и входит под ним; сама почта берётся из фикстуры `test_settings` (`admin_email="admin@test.com"`), а не выписывается второй копией.

**Живых величин прогнано: 28 — ровно число входов матрицы** (17 продуктовых + 11 админских). Админская половина, снятая замером:

```
ЖИВАЯ POST /admin/workers/1/restart        = 302
ЖИВАЯ POST /admin/queue/2/drop             = 302
ЖИВАЯ GET  /admin/users/5                  = 200
ЖИВАЯ GET  /admin/users/6/history          = 200
ЖИВАЯ GET  /admin/users/7/history/partial  = 200
ЖИВАЯ GET  /admin/users/8/history/12       = 200
ЖИВАЯ GET  /admin/users/9/history/14       = 200
ЖИВАЯ POST /admin/users/10/unlimited       = 302
ЖИВАЯ POST /admin/users/11/impersonate     = 302
ЖИВАЯ POST /admin/users/12/block           = 302
ЖИВАЯ POST /admin/users/13/delete          = 302
```

**Живая величина ДОЕЗЖАЕТ ДО ТЕЛА обработчика, и это снято, а не предположено.** Читающие входы отдают `200` (настоящая отрисованная страница), изменяющие — переход с ИМЕНОВАННЫМ исходом тела: `/admin/workers?notice=worker_no_container`, `/admin/queue?result=unknown_account`, `/dashboard` для удавшегося входа под пользователем. Ни один из одиннадцати не упёрся в `403` гарда происхождения и ни один не отдал `422`.

**Личностей в прогоне матрицы участвует ТРИ, и это не две:** объявленных матрицей — две (`user`, `admin`, поле `identity`), а третья — ОТДЕЛЬНЫЙ ПОСЕЯННЫЙ ПОЛЬЗОВАТЕЛЬ-ЦЕЛЬ, заводимый посевом на каждый вход с уникальной почтой. Он есть митигация `T-10-29-05`: вход под пользователем и удаление действуют НАД личностью, и прогон, подавший им саму административную, оставил бы следующие строки матрицы без личности вовсе.

### 4. Смежность — на каждом входе, двумя числами

| проверка | число | равно числу входов |
|----------|-------|--------------------|
| величина, РАВНАЯ границе (`2147483647`) | 28 | да |
| величина на границе ПЛЮС ЕДИНИЦА (`2147483648`) | 28 | да |

Админская половина замером — на границе `302` (годная величина, строки нет), на границе плюс единица `422` на всех одиннадцати входах:

```
POST /workers/{account_id}/restart          → адрес account_id: граница = 302; граница+1 = 422
POST /queue/{account_id}/drop               → адрес account_id: граница = 302; граница+1 = 422
GET  /users/{user_id}                       → адрес user_id:    граница = 302; граница+1 = 422
GET  /users/{user_id}/history               → адрес user_id:    граница = 302; граница+1 = 422
GET  /users/{user_id}/history/partial       → адрес user_id:    граница = 302; граница+1 = 422
GET  /users/{user_id}/history/{log_id}      → адрес user_id:    граница = 302; граница+1 = 422
GET  /users/{user_id}/history/{log_id}      → адрес log_id:     граница = 302; граница+1 = 422
POST /users/{user_id}/unlimited             → адрес user_id:    граница = 302; граница+1 = 422
POST /users/{user_id}/impersonate           → адрес user_id:    граница = 302; граница+1 = 422
POST /users/{user_id}/block                 → адрес user_id:    граница = 302; граница+1 = 422
POST /users/{user_id}/delete                → адрес user_id:    граница = 302; граница+1 = 422
```

### 5. Величины постраничного вывода — не тронуты

Разбор сигнатур `app/pages/admin.py` после правки: `offset: int = Query(default=0, ge=0)` (`admin_user_history`), `offset: int = Query(0, ge=0)` и `limit: int = Query(PAGE_SIZE, ge=1, le=100)` (`admin_user_history_partial`). Верхней границы ИДЕНТИФИКАТОРА (`ID_MAX`) на них нет и не заводилось: они не есть идентификатор, и отказ по ним ничего не говорит о владении строкой. **Действующее правило модуля, подающее в постраничный вывод набор негодных величин** (`test_the_page_number_from_the_address_never_breaks_the_subsection`, `tests/test_pages/test_admin_users.py:800`), **осталось зелёным** — прогон трёх админских суит дал `203 passed`.

### 6. Долг реестра ВНУТРИ плана — числом и поимённо

Прогон жалоб правила полноты ПОСЛЕ задачи 1, до задачи 2 — дословно:

```
жалоб правила полноты: 6
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::POST /queue/{account_id}/drop → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::POST /users/{user_id}/block → адрес user_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::POST /users/{user_id}/delete → адрес user_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::POST /users/{user_id}/impersonate → адрес user_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::POST /users/{user_id}/unlimited → адрес user_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::POST /workers/{account_id}/restart → адрес account_id (псевдоним IdPath)
RC=0
```

Все шесть — POST-входы `app/pages/admin.py`, все одного вида («НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН»); жалоб иного вида и иного модуля нет, то есть ни одна из семнадцати записей планов 10-24 и 10-28 не задета. **Долг закрыт задачей 2 ЭТОГО ЖЕ плана, и число жалоб совпало с ростом объявленного числа: шесть жалоб — рост 17 → 23.**

### 7. Шесть ключей реестра — сняты прогоном замера, вписаны дословно

Разность «измеренные минус объявленные» ДО правки перечня — те же шесть строк, что в разделе 6, дословно.

### 8. ОБЕ разности после правки — пусты

```
измеренных входов: 23
объявленных записей: 23 | объявленное число: 23
РАЗНОСТЬ «измеренные минус объявленные»: []
РАЗНОСТЬ «объявленные минус измеренные»: []
```

**Перечень равен дереву, и это снято прогоном, а не объявлено.**

### 9. Таблица «вход → путь разметки → строка» и чем сужена достижимость

| # | вход | путь разметки → строка | чем сужена достижимость |
|---|------|------------------------|--------------------------|
| 18 | `POST /queue/{account_id}/drop → адрес account_id` | `app/templates/admin/includes/queue_row.html:87` (адрес формы), `app/templates/admin/queue.html:146` (аргумент `action` панели подтверждения) | **ОБОИМИ И ЕЩЁ ТРЕТЬИМ.** СБОРКОЙ: из `account.id` отрисованной строки очереди. ПРАВАМИ: раздел закрыт `require_admin`. ТРЕТЬЕ, СВОЁ: форма рисуется только под условием `row.task_id` — у задачи без идентификатора на её месте прочерк |
| 19 | `POST /users/{user_id}/block → адрес user_id` | `app/templates/admin/user_detail.html:149` | **ОБОИМИ.** СБОРКОЙ: из `target_user.id` открытой карточки. ПРАВАМИ: карточка закрыта `require_admin`. Величина стои́т в разметке РОВНО ОДИН РАЗ — подтверждающей панели у тумблера нет (UI-контракт E5) |
| 20 | `POST /users/{user_id}/delete → адрес user_id` | `app/templates/admin/user_detail.html:175` (форма-триггер), `:195` (аргумент `action` панели) | **ОБОИМИ, И ПРАВА ЗДЕСЬ ДВОЙНЫЕ.** СБОРКОЙ: обе строки одним выражением с `target_user.id`. ПРАВАМИ: `require_admin` плюс запрет под чужой личностью (`forbid_when_impersonating`, D-22) |
| 21 | `POST /users/{user_id}/impersonate → адрес user_id` | `app/templates/admin/user_detail.html:164` (форма-триггер), `:188` (аргумент `action` панели) | **ОБОИМИ, И ПРАВА ДВОЙНЫЕ.** СБОРКОЙ: обе строки из `target_user.id`. ПРАВАМИ: `require_admin` плюс запрет вложенного входа (`forbid_when_impersonating`, D-22) |
| 22 | `POST /users/{user_id}/unlimited → адрес user_id` | `app/templates/admin/user_detail.html:145` | **ОБОИМИ, И ПРАВА ДВОЙНЫЕ.** СБОРКОЙ: из `target_user.id`; панели подтверждения нет, поэтому величина в разметке ОДНА. ПРАВАМИ: `require_admin` плюс запрет под чужой личностью — это ДЕНЬГИ (D-22) |
| 23 | `POST /workers/{account_id}/restart → адрес account_id` | `app/templates/admin/includes/worker_row.html:108` (адрес формы), `app/templates/admin/workers.html:58` (аргумент `action` панели) | **ОБОИМИ И ЕЩЁ ТРЕТЬИМ.** СБОРКОЙ: из `account.id` отрисованной строки воркеров. ПРАВАМИ: подраздел закрыт `require_admin`. ТРЕТЬЕ, СВОЁ: форма рисуется только под условием `account.type in RESTARTABLE_CHANNELS` |

**ПОЧЕМУ ДВА СПОСОБА НАЗВАНЫ ПОРОЗНЬ, А НЕ СКЛЕЕНЫ В СЛОВО «НУЛЕВАЯ».** Они снимаются независимо: права, ослабленные завтра (второй администратор, делегирование раздела), достижимость по сборке не увеличили бы; сборка, заменённая на поле ввода, дала бы достижимость при нетронутых правах. Склеенное «нулевая» скрыло бы, какое из двух сужений исчезло, — и следующий читатель разбирал бы не то.

### 10. Фаза-сниматель — проверена ЧТЕНИЕМ РОАДМАПА

**Названная константой `LIFTING_CONDITION_VALIDATION_REFUSAL` фаза НАКРЫВАЕТ административный раздел, и это видно двумя строками роадмапа:**

- `.planning/ROADMAP.md:73` — `**Phase 11: Массовый перевод разделов письма** - schedules + ads → admin → accounts последним; billing не первым`
- `.planning/ROADMAP.md:391` — `**Порядок внутри фазы (не переставлять):** schedules + ads → admin (три файла admin/includes/* обязаны получить id и макросы) → accounts последним ...`

Административный модуль назван ОТДЕЛЬНЫМ ЗВЕНОМ порядка, а не подразумевается. Находки нет: подгонять текст не потребовалось.

### 11. Число POST-обработчиков — не сдвинуто, снято замером

| момент | значение |
|--------|----------|
| ДО плана (`e233f0c`) | **36** |
| ПОСЛЕ задачи 1 | **36** |

Снято разбором дерева `app/pages/*.py` на атрибут `.post` любого объекта (та же ось, что у гейта). Маршрутов не добавлялось и не снималось — менялись только сигнатуры.

## Прогоны верификации

| команда | исход |
|---------|-------|
| `uv run pytest tests/test_pages/test_identifier_bounds.py -q` | `11 passed` (было `1 failed, 10 passed` до правки сигнатур) |
| `uv run pytest tests/test_pages/test_admin_panel.py tests/test_pages/test_admin_users.py tests/test_pages/test_impersonation.py -q` | `203 passed` |
| `uv run pytest tests/test_pages/ -q --deselect ...` (два снятых узла, см. деривацию 1) | `1535 passed, 2 deselected` |
| `uv run pytest tests/test_pages/test_htmx_gates.py -q -k "validation_refusal or divergence"` | `4 passed, 32 deselected` — фильтр собрал ЧЕТЫРЕ правила реестра, зелёный не пустым множеством |
| `uv run pytest tests/test_pages/test_htmx_gates.py -q` | `36 passed` |
| `uv run pytest tests/ -q -m "not planning"` | `2855 passed, 28 deselected` за 35:09 |
| `uv run python -m compileall -q app main.py tests` | `RC=0` |
| проверка чисел (`DECLARED == 23`, `POST_HANDLERS == 36`) | `RC=0` |

## Decisions Made

1. **Личность объявлена ПОЛЕМ ВХОДА, а обе половины живут в ОДНОЙ матрице.** Предмет у них один — граница величины идентификатора; разведение по личности было бы разведением по внешнему признаку ровно так же, как разведение по способу передачи (основание, записанное планом 10-28 у курсора постраничного вывода).
2. **Личность берётся ЯВНЫМ входом (`_assume`), а не порядком разрешения фикстур.** Замер устройства фикстур: `authed_client` и `admin_client` возвращают ОДИН объект клиента, различаясь только тем, чью cookie оставили на нём последней. Правило, заказавшее обе и положившееся на порядок, утверждало бы о порядке фикстур.
3. **Антивакуум берёт личность заново перед КАЖДЫМ входом, а не при смене группы.** Удавшаяся имперсонация перевыписывает ту же cookie на личность цели; проверка «личность та же, что была заказана» здесь солгала бы.
4. **Тело POST-запроса стало полем входа.** `admin_drop_task` несёт обязательное `task_id`, и на пустом теле отказ валидации пришёл бы ЗА ОТСУТСТВИЕ ПОЛЯ: строка матрицы зеленела бы, не сказав ни слова о границе, а антивакуум краснел бы по той же причине.
5. **Достижимость названа ДВУМЯ независимыми сужениями у каждой из шести записей** (см. раздел 9).
6. **Контроль зубов отбирает записи ПО ВЛАДЕЛЬЦУ, а не по позиции.** Прежний контроль ронял ПЕРВУЮ запись перечня (план 10-22), и его зелёный об административном модуле не говорил ничего.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Плановая широкая команда задачи 1 снимала ОДИН узел внутрипланового долга, а долг краснит ДВА**

- **Found during:** Задача 1, прогон `uv run pytest tests/test_pages/ -q --deselect ...test_every_framework_bounded_input_is_declared_as_a_divergence`
- **Issue:** Прогон дал `1 failed, 1533 passed`. Упавший узел — `test_control_a_shortened_exception_list_reddens_the_completeness_rule`: его ЗАКЛЮЧИТЕЛЬНОЕ утверждение сличает БОЕВОЙ перечень с замером («подмена не протекла за границу контроля»), то есть несёт ровно тот же внутриплановый долг, что и снятый узел. Красен ОН тоже ПО ПОСТРОЕНИЮ, а не по дефекту.
- **Fix:** В прогон добавлен второй `--deselect` того же класса; предмет обоих узлов измерен отдельной командой раздела 6 с проверкой владения каждой жалобой, и оба узла прогнаны ЗЕЛЁНЫМИ после задачи 2 (`36 passed` целиком по модулю).
- **Files modified:** нет — правка команды прогона, не дерева
- **Verification:** `1535 passed, 2 deselected` на исправленной команде; `36 passed` на модуле гейтов после задачи 2
- **⚠️ ЭТО ПОВТОР, А НЕ НОВАЯ НАХОДКА, И ЭТО ХУЖЕ.** Ровно то же расхождение зафиксировано планом 10-28 как **окно 60** реестра `.planning/WINDOWS.md` (запись открыта). В текст плана 10-29 находка предшественника не перенесена, и плановая команда воспроизвела ту же неполноту дословно. Записано в реестр окон повторно, со ссылкой на окно 60.

**2. [Rule 1 - Bug] Два `ERROR` в собственном инструментальном прогоне — артефакт флага, а не дефект дерева**

- **Found during:** Задача 1, первый широкий прогон
- **Issue:** `tests/test_pages/test_blocked_user.py` дал два `ERROR` вида `fixture 'caplog' not found`. Причина — флаг `-p no:logging`, добавленный ИСПОЛНИТЕЛЕМ ради сокращения вывода: он отключает плагин, поставляющий `caplog`. Планового флага в командах нет.
- **Fix:** Флаг снят из всех прогонов; `uv run pytest tests/test_pages/test_blocked_user.py -q` без него — `20 passed`.
- **Files modified:** нет
- **Verification:** `20 passed`; полная суита `2855 passed`
- **Урок записан здесь, а не проглочен:** флаг, добавленный ради читаемости вывода, изменил СОСТАВ ФИКСТУР и произвёл красное, к предмету плана отношения не имевшее. Инструментальный флаг есть часть измерения, и молчаливое его добавление делает измерение не тем, о котором отчитываются.

---

**Total deviations:** 2 auto-fixed (1 блокирующий прогон, 1 дефект собственного измерения)
**Impact on plan:** Ни одна правка не коснулась дерева и не изменила предмета плана. Обе относятся к КОМАНДАМ ПРОГОНА, и обе названы числом.

## Known Stubs

Нет. Заглушек, пропущенных правил и непрогнанных `<verify>` план не оставил: все команды раздела «Прогоны верификации» исполнены, исходы приведены числами.

## Issues Encountered

**Правило `test_every_bounded_input_still_admits_a_live_value` было ЗЕЛЁНЫМ и ДО правки сигнатур, и это не дефект RED.** Антивакуум по построению обязан быть зелёным с обеих сторон правки: его предмет — «граница не отвергает годного», и до границы отвергать было нечему. Красным по построению обязано быть и было ровно правило ОТКАЗА (раздел 1). Проверено отдельно, что антивакуум не вакуумен: живые исходы админской половины сняты замером и содержат `200` на читающих входах и ИМЕНОВАННЫЕ исходы тела на изменяющих (раздел 3), то есть тело обработчика достигается, а не подменяется отказом гарда.

## User Setup Required

None — внешних служб план не трогает, зависимостей не вводит (`pyproject.toml` не в `files_modified`).

## Next Phase Readiness

- **Страничный слой закрыт границей ПОЛНОСТЬЮ, и это утверждение, а не впечатление:** обе разности «измеренные ↔ объявленные» пусты, и пустота снята прогоном.
- **План 10-30 (гейт полноты границы по всему каталогу) может встать:** он обязан стоять ПОСЛЕ закрытия последнего входа, и последний вход закрыт этим планом. До него гейт краснел бы по построению всю волну.
- **Что остаётся открытым и почему:**
  - **Окно 39** (поведение боевого драйвера PostgreSQL на неограниченном входе) — у суиты драйвер один; наблюдается отказ на границе приложения, до драйвера. Открыто.
  - **Окно 60 и его повтор** — неполнота плановых команд снятия внутрипланового долга. Открыто.
  - **Решение о законности расхождения формы отказа с запертым D-01** — состояние всех двадцати трёх записей остаётся `ЖДЁТ ВЛАДЕЛЬЦА`. Планом не чеканилось: изъятие из запертого решения принадлежит владельцу (прецедент D-08).
  - **Вселенная гейта полноты административных маршрутов** — не тронута намеренно, фаза-владелец НЕ НАЗНАЧЕНА.

---
*Phase: 10-rychag-components-modal-html*
*Completed: 2026-09-08*

## Self-Check: PASSED

- Три изменённых файла на месте (`app/pages/admin.py`, `tests/test_pages/test_identifier_bounds.py`, `tests/test_pages/test_htmx_gates.py`).
- Три коммита задач найдены в истории: `dc9f84f`, `a5eb19d`, `3022a44`.
- Все команды `<verify>` обеих задач прогнаны; исходы приведены числами в разделе «Прогоны верификации».

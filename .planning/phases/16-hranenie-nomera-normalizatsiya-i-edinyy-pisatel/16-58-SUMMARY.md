---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 58
subsystem: database
tags: [sqlalchemy, before_cursor_execute, engine-events, runtime-guard, single-writer, bulk, upsert, O-25, CR-08, WR-36, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-51 — app/models/phone_guard.py (writer_scope, _WRITER_ACTIVE, PhoneWriteOutsideWriter, три линии, регистрация в app/models/__init__.py) и модуль защиты в тестах (FOREIGN_WRITES 16, LEGITIMATE_WRITES 7, ROUND_TEN_WRITER_FORMS 6); 16-55 — правило гейта писателя о входе в разрешение и о снятии слушателя"
provides:
  - "Четвёртая линия защиты: _refuse_unscoped_cursor — слушатель before_cursor_execute на классе sqlalchemy.engine.Engine (последняя строка модуля); помощники _target_table, _cursor_columns; константа _ACCOUNTS_TABLE_NAME"
  - "Вторая линия (_refuse_unscoped_flush) судит session.new по значениям state.dict (WR-36); правило истории сохранено"
  - "Шапка защиты: четыре линии, где стоит линия движка, граница по замеру исполнения, цена «отказ в закрытую», летопись снятой фразы"
  - "Модуль защиты в тестах: трасер списка строк, правило класса Engine, FOREIGN_WRITES 26 (+10), LEGITIMATE_WRITES 14 (+7), CLOSED_FAILING_WRITES 2, правило второй линии, ENGINE_LINE_RED, расширенное правило шапки (GUARD_HEADER_NAMES +10, RETIRED_PROMISE / CHRONICLE_HEAD / CHRONICLE_CAUSES)"
affects: [16-61, 16-62, 16-64, "Фазы 18–20 (любая запись колонок номера мимо писателя через bulk_*, соединение, Core, upsert отказывает на курсоре)"]

actuals:
  tokens: 10257   # chars/4: дифф c1d726af..db8f0d67 — 41 027 байт (wc -c); оценка плана 95 000 включала чтение контекста
  tasks: 3
  commits: 6      # git rev-list --count c1d726af..HEAD до коммита сводки
plan_head_before: c1d726afa40ad839598e6ce24b5f04800b3c0e94
plan_head_after: db8f0d672ae97297a8594287555221a8ad58798b

tech-stack:
  added: []
  patterns:
    - "Линия защиты на курсоре: слушатель класса Engine с быстрым путём O(1) — признак INSERT/UPDATE контекста, тип скомпилированного оператора, имя таблицы, затем разрешение писателя — и только потом разбор колонок"
    - "Таблица судится по имени (TableClause.name), а не по тождеству объекта; Alias разворачивается"
    - "UPDATE и ON CONFLICT DO UPDATE SET — по колонкам при любом значении; INSERT — по значениям compiled_parameters; несудимое значение — отказ в закрытую"
    - "Ветка upsert распознаётся isinstance-проверкой классов OnConflictDoUpdate / OnConflictDoNothing SQLite и PostgreSQL, без getattr со строкой"

key-files:
  created: []
  modified:
    - app/models/phone_guard.py
    - tests/test_application/test_phone_writer_runtime_guard.py

key-decisions:
  - "Ветка после VALUES у вставки в messenger_accounts, которую линия не читает (не OnConflictDoUpdate / OnConflictDoNothing SQLite и PostgreSQL), судится как задающая обе колонки номера — отказ в закрытую (сверх плана, Rule 2)"
  - "Вторая линия для session.new: суд по значениям ДОБАВЛЕН к прежнему суду по истории, а не заменил его — ни один прежний отказ не потерян (заметка 12)"
  - "Порядок быстрого пути линии движка: context.isinsert/isupdate → compiled → тип оператора → имя таблицы → _WRITER_ACTIVE → разбор; оператор ради суда не компилируется и не превращается в строку"
  - "Шапка: обещание переписано через механизм; слово «Летопись» стоит один раз, в последнем абзаце; граница — по замеру исполнения этого плана (зонд .pytest_cache/checks/boundary_probe.py)"

patterns-established:
  - "Новая строка таблицы защиты — асинхронная функция над db_session и посеянным аккаунтом; утверждение строки FOREIGN_WRITES — отказ защиты и прежнее _state после rollback"

requirements-completed: [PHONE-02]   # копия requirements плана; REQUIREMENTS.md этот план не трогает (заметка 5 оркестратора)

coverage:
  - id: D1
    description: "Подложенное дозаполнение Фазы 20 списком строк (цикл → bulk_update_mappings через run_sync) отказывает на курсоре, строка прежняя (None, False); писатель затем пишет (NUMBER, False); линия стоит на классе Engine и работает на движке, созданном после ввоза моделей"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_planted_backfill_with_a_list_of_rows_is_refused_and_the_writer_writes, #test_the_engine_line_stands_on_the_engine_class"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пути мимо событий ORM — B1–B6 верификатора раунда 11, лёгкая таблица через сессию и соединение, bulk_save_objects и set_committed_value на новом объекте + add — отказывают; 16 прежних строк FOREIGN_WRITES — прежний ответ"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_foreign_write_is_refused (26)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Законные пути не отказывают: статус через соединение и bulk, вставки без номера (bulk, Core с phone=None), три аккаунта одним add_all, фильтр по номеру, удаление через соединение; 7 прежних строк — прежний ответ; широкий прогон 62 суит — 2762 passed, 0 отказов"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_legitimate_write_passes (14)"
        status: pass
      - kind: integration
        ref: "uv run pytest @.pytest_cache/checks/breadth_files.txt -q -p no:randomly (62 пути) — 2762 passed"
        status: pass
    human_judgment: false
  - id: D4
    description: "Цена «отказ в закрытую»: многострочный values([…]) и выражение SQL для номера отказывают без номера (CLOSED_FAILING_WRITES)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_write_whose_values_cannot_be_judged_is_refused_closed (2)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Вторая линия судит новый объект по значениям (WR-36)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_new_account_is_judged_by_its_values_before_the_flush"
        status: pass
    human_judgment: false
  - id: D6
    description: "Шапка защиты называет четыре линии, место регистрации, границу по замеру и цену; прежняя фраза обещания — только в летописи рядом с CR-08 и WR-36"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_the_guard_module_names_what_it_refuses_and_its_boundary"
        status: pass
    human_judgment: true
    rationale: "Правило сверяет имена и место фразы; правдивость прозы шапки относительно поведения судит верификатор раунда 12 (О-26 (а))"

duration: 54min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 58: линия движка `before_cursor_execute` и суд нового объекта по значениям — Summary

**Четвёртая линия защиты писателя на классе `sqlalchemy.engine.Engine` отказывает UPDATE / upsert / INSERT колонок номера таблицы `messenger_accounts` мимо событий ORM (`bulk_*`, соединение, Core, лёгкая таблица) вне `writer_scope()`; `before_flush` судит новый объект по `state.dict` (WR-36); шапка защиты называет четыре линии и границу по замеру (CR-08, О-25 (а))**

## Performance

- **Duration:** 54 мин (из них широкий прогон — 23 мин 18 с)
- **Started:** 2026-10-26T07:09:32Z
- **Completed:** 2026-10-26T08:03Z
- **Tasks:** 3 (по циклу RED → GREEN каждая)
- **Files modified:** 2

## Accomplishments

- Слушатель `_refuse_unscoped_cursor` на классе `Engine`: подложенное дозаполнение списком строк (`rows.append(...)` → `bulk_update_mappings`) отказывает на курсоре, строка прежняя; писатель после этого пишет.
- Закрыты все формы гэпа 3 раунда 11: B1–B6 верификатора, лёгкая `sqlalchemy.table("messenger_accounts", …)` (на базе прошла бы и линию `do_orm_execute`, сравнивающую тождество), `bulk_save_objects`, `set_committed_value` на новом объекте.
- Вторая линия судит `session.new` по значениям; правило истории для `session.new` / `session.dirty` осталось.
- Цена «отказ в закрытую» закреплена таблицей `CLOSED_FAILING_WRITES`.
- Шапка: обещание через механизм, четыре линии, где стоит линия движка, граница по замеру исполнения (`text(…)`, `exec_driver_sql`, сырое соединение DBAPI, процесс без `app.models`, `set_committed_value` на сохранённом объекте), цена, летопись снятой фразы.

## Task Commits

1. **Задача 1 (трасер): список строк отказывает на курсоре; линия на классе `Engine`**
   - RED `1da1b36a` — `test(16-58): add failing tracer for a list-of-rows backfill refused at the cursor`
   - GREEN `a75f30be` — `feat(16-58): refuse a phone write past ORM events at the cursor on the Engine class`
2. **Задача 2: пути мимо событий ORM, законные пути, отказ в закрытую; новый объект по значениям**
   - RED `f4565b38` — `test(16-58): add rows for writes past ORM events and a failing second-line value rule`
   - GREEN `f4ee8a3b` — `feat(16-58): judge a new account by its values in the before_flush line`
3. **Задача 3: шапка по замеру; широкий прогон и сквозные гейты**
   - RED `52ec6e5d` — `test(16-58): require the guard header to name the engine line and its measured boundary`
   - GREEN `db8f0d67` — `feat(16-58): name four guard lines and the measured engine-line boundary in the header`

REFACTOR-коммитов нет (менять было нечего).

## TDD: RED-улики (три совпадения + классификатор)

Улики — JUnit XML в `.pytest_cache/gsd-red/` (gitignored), записи `{command, exitCode, targetTest, output, …}` поданы в `check tdd-red-evidence` — все три `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | Цель | `FAILED …::<цель>` | Последняя строка | Причинный литерал | Семантическая оценка |
|---|---|---|---|---|---|
| 1 | `test_a_planted_backfill_with_a_list_of_rows_is_refused_and_the_writer_writes` | да | `2 failed, 36 deselected` | `ENGINE_LINE_RED` «запись номера мимо событий ORM не отказала на курсоре (CR-08)»; исход `NoneType` | цель исполнилась и упала на своём утверждении: запись списком строк прошла, слушателя курсора нет; соседнее правило класса `Engine` — на утверждении «в модуле защиты нет слушателя курсора» (`vars(...).get`, не `AttributeError`) |
| 2 | `test_a_new_account_is_judged_by_its_values_before_the_flush` | да | `1 failed, 57 deselected` | `SECOND_LINE_RED` «… не отказал во второй линии — before_flush судит историю, а не значения (WR-36)» | вторая линия вызвана напрямую, линия движка не участвует; 10 строк путей мимо событий ORM уже зелёные с задачи 1 — закрепки |
| 3 | `test_the_guard_module_names_what_it_refuses_and_its_boundary` | да | `1 failed, 57 deselected` | `HEADER_RED` «шапка защиты не называет, что отказывает и где её граница» | недостающие: `before_cursor_execute`, `Engine`, `on_conflict_do_update`, `exec_driver_sql`, `сырое соединение DBAPI`, `CLOSED_FAILING_WRITES`, `О-25 (а)`, фраза обещания вне летописи (`messenger_accounts`, `bulk_insert_mappings`, `text(` в шапке раунда 10 уже были) |

## Замеры (база — замер оркестратора на `c1d726af`)

| Проверка | База | После плана |
|---|---|---|
| модуль защиты `test_phone_writer_runtime_guard.py` | 36 | 58 (+22: трасер, правило `Engine`, 10 + 7 + 2 строки, правило второй линии) |
| задача 1 / 2 (модуль защиты, писатель 24, гонка 4, CHECK 10) | — | 76 / 96 passed |
| базовый модуль защиты (`git show c1d726af:…` → `.pytest_cache/r11diff/base_guard_test.py`) против итоговой защиты | 36 | **36 passed** — ни один прежний отказ не потерян |
| идентификаторы `19c99ffb` ⊆ HEAD | — | `FOREIGN_WRITES` 16 ⊆ 26; `LEGITIMATE_WRITES` 7 ⊆ 14; `ROUND_TEN_WRITER_FORMS` 6 ⊆ 6 |
| набор фазы (11 путей `<verification>`) | 1675, 84 с | 1697 (+22), 88,8 с |
| гейт приватности + гейт писателя + паритет | 345 + 661 + 139 = 1145 | 1145 (после задачи 1 и после задачи 3) |
| живые строки | приватность `app` 102/227, `scripts` 4/68, `max_worker` 2/93, 0; канал приватности 108, 0; JS `wa_worker` 1/68, 0; канал писателя 106, 0 | без изменений (5 правил + `entered_only_by_the_writer` = 6 passed) |
| писатель живое дерево (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` |
| модуль защиты гейтами (`judged_offences`, канал с обоими `BANNED_GETATTR_NAMES` после реестра, вызовы журнала) | — | `OK` (0 / 0 / 0), `PHONE_WRITER_EXCEPTIONS` — ровно писатель |
| `tests/test_worker` + `tests/test_models` | 91 + 56 | 147 passed |
| сквозные гейты (htmx post pairs, htmx gates, templates, declared invariants) | 576 | 576 passed (2 мин 50 с) |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строки | exit 0, 934 строки, биекция |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| **широкий прогон** (62 пути: 61 суита с `MessengerAccount` / `messenger_accounts` вне `tests/test_planning` + `tests/test_migrations`; список совпал с предвычисленным оркестратором) | прототип планирования: 2740 | **2762 passed, 0 failed**, 1397,7 с (23 мин 18 с); отказов защиты на законных путях — 0 |

**Цена линии движка** (зонд `.pytest_cache/checks/cost_probe.py`, SQLite в памяти, синхронный движок, 20 000 операторов, лучший из трёх; слушатель снят/возвращён только в зонде): SELECT — 116,9 мкс со слушателем против 121,8 мкс без (−4,9, в шуме); UPDATE чужой таблицы `users` — +2,6 мкс; UPDATE `messenger_accounts` по `status` (путь разбора колонок) — +12,6 мкс на оператор. Набор фазы — 88,8 с против 84 с базы при +22 правилах; широкий прогон — 23 мин 18 с против 32 мин прототипа планирования (другие условия: прототип шёл с плагином маски 16-60).

**Граница по замеру исполнения** (зонд `.pytest_cache/checks/boundary_probe.py`): синхронный и async-движки, созданные ДО ввоза `app.models`, — Core `update` колонки номера `REFUSED`; `text("UPDATE messenger_accounts SET phone = …")` через сессию и через соединение — `PASSED`; `exec_driver_sql` — `PASSED`; сырое соединение DBAPI (`get_raw_connection()` → `_ConnectionFairy`) — мимо движка. Это и записано в шапке.

**Что широкий прогон НЕ покрыл:** суиты, не упоминающие `MessengerAccount` / `messenger_accounts` (≈ 2 500 правил полного `just test`), и `tests/test_planning` вне переписи; их покрывает пост-мерж `just test` оркестратора. Ветка PostgreSQL (asyncpg) не исполнялась (граница проекта D-26).

## Files Created/Modified

- `app/models/phone_guard.py` — линия движка `_refuse_unscoped_cursor` (+ `_target_table`, `_cursor_columns`, `_ACCOUNTS_TABLE_NAME`, регистрация последней строкой), суд нового объекта по значениям в `_refuse_unscoped_flush`, шапка.
- `tests/test_application/test_phone_writer_runtime_guard.py` — трасер, правило класса `Engine`, 10 + 7 строк, `CLOSED_FAILING_WRITES`, правило второй линии, расширенное правило шапки.

## Decisions Made

См. `key-decisions`. Главное: линия движка стоит одна на классе `Engine` (без регистрации в `app/database.py` / `tests/conftest.py`), её быстрый путь не разбирает SQL и не компилирует оператор; суд второй линии по значениям добавлен к суду по истории, а не заменил его.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, тест] Правило `CLOSED_FAILING_WRITES` читало `account.user_id` после `rollback`**
- **Found during:** задача 2, до RED-коммита
- **Issue:** `rollback` гасит объект; чтение атрибута вне greenlet дало `MissingGreenlet` вместо утверждения правила.
- **Fix:** `user_id` берётся до записи.
- **Files modified:** `tests/test_application/test_phone_writer_runtime_guard.py`
- **Verification:** обе строки `CLOSED_FAILING_WRITES` зелёные под линией движка; RED задачи 2 — ровно одно правило второй линии.
- **Committed in:** `f4565b38`

**2. [Rule 2 - Missing Critical] Нечитаемая ветка после `VALUES` у вставки — отказ в закрытую**
- **Found during:** задача 1 (GREEN)
- **Issue:** план называет ветку upsert через `update_values_to_set`; иная ветка `_post_values_clause` (не `ON CONFLICT DO UPDATE` / `DO NOTHING` SQLite и PostgreSQL) молча прошла бы — нарушение запрета «MUST NOT молча пропускать вставку, значение колонки номера в которой на курсоре не судимо».
- **Fix:** такая ветка судится как задающая обе колонки номера; классы распознаются `isinstance` (ввоз `OnConflictDoUpdate` / `OnConflictDoNothing` из `sqlalchemy.dialects.sqlite.dml` и `…postgresql.dml`), без `getattr` со строкой (заметка 9).
- **Files modified:** `app/models/phone_guard.py`
- **Verification:** строка `upsert-on-conflict-set-from-a-variable` отказывает; гейты и канал — 0 в модуле защиты.
- **Committed in:** `a75f30be`

**3. [Rule 2 - сохранение прежнего] Вторая линия: суд по значениям добавлен, а не заменил суд по истории для `session.new`**
- **Found during:** задача 2 (GREEN)
- **Issue:** план велит судить `session.new` по значениям, а `session.dirty` — по истории; замена для `session.new` сняла бы прежний отказ (значение `None`, поставленное под разрешением и сброшенное без него).
- **Fix:** сначала суд по значениям `session.new`, затем прежний цикл истории по `session.new` и `session.dirty`.
- **Verification:** базовый модуль защиты — 36 passed против итоговой защиты.
- **Committed in:** `f4ee8a3b`

### Подстановки команд (та же логика, те же утверждения)

- Однострочники `python -c` плана (гейты модуля защиты, слушатель на `Engine`, разбор `ast` таблиц, шапка) записаны дословно в `.pytest_cache/checks/{t1_gates,t1_listener,t2_rows,t3_header}.py` и исполнены с `PYTHONPATH=.`; сверка подмножества идентификаторов — `t2_subset.py` над `git show 19c99ffb:… > .pytest_cache/r11_base_guard_tests.py`.
- Широкий прогон: `$(grep …)` плана заменён списком `@.pytest_cache/checks/breadth_files.txt` (62 пути); грeп плана пересчитан в дереве исполнителя — список совпал.
- Базовый модуль защиты лежит вне `tests/`, поэтому запущен с `-p tests.conftest` (фикстура `db_session`); `REPO_ROOT = parents[2]` у пути `.pytest_cache/r11diff/…` — корень дерева.
- Все pytest и тяжёлые скрипты — под общим `flock`.
- `tests/test_planning` из `<verify>` задачи 3 — после коммита сводки (заметка 5 оркестратора), а не до GREEN задачи 3.
- `graphify update .` не запускался (оркестратор после слияния); полный `just test` не запускался (пост-мерж гейт оркестратора).

---

**Total deviations:** 3 (1 Rule 1 в тесте, 2 Rule 2 в защите) + названные подстановки.
**Impact on plan:** обе правки Rule 2 строже плана и не меняют ни одного ответа строк; размах — два файла плана.

## Issues Encountered

Нет. Гейт-модули, писатель `app/application/accounts/phone.py`, прочие суиты и реестр не тронуты.

## Threat Flags

Нет новых поверхностей вне модели угроз плана: линия движка — T-16-134 (mitigate), риск отказа законной записи — T-16-135 (широкий прогон — 0 отказов).

## Deferred

Нет (в `deferred-items.md` не писалось).

## User Setup Required

None — внешних сервисов нет.

## Next Phase Readiness

- 16-61 (волна 2) правит модуль защиты и тестовый модуль поверх этого: `FOREIGN_WRITES` — 26 строк, `LEGITIMATE_WRITES` — 14, `CLOSED_FAILING_WRITES` — 2; помощники тестов `_seed`, `_state`, `_columns`, `_accounts_of`, `_status_of`, `_refusal_of`, `_refusal_of_call`, `_is_guard_refusal`, `_guard`; слушатели атрибута и их регистрация не тронуты; раздел ГРАНИЦА шапки — список, к которому дописываются строки `merge`, разрешения у порождённой задачи и сырого SQL из параметра.
- 16-62 цитирует строку `event.listen(Engine, "before_cursor_execute", _refuse_unscoped_cursor)` (последняя строка `app/models/phone_guard.py`) и «план 16-58».
- 16-64: GREEN CR-08 — `a75f30be`, `f4ee8a3b`, `db8f0d67`; GREEN WR-36 — `f4ee8a3b`.
- После слияния линия движка живёт и в подпроцессе зонда Celery плана 16-57 (ввоз `app.models`); на SELECT и записях других таблиц она выходит на быстром пути.

## Self-Check: PASSED

- Файлы на месте: `app/models/phone_guard.py`, `tests/test_application/test_phone_writer_runtime_guard.py`, эта сводка.
- Коммиты на HEAD: `1da1b36a`, `a75f30be`, `f4565b38`, `f4ee8a3b`, `52ec6e5d`, `db8f0d67`, сводка `16552feb`.
- `uv run pytest tests/test_planning -q -p no:randomly` после коммита сводки — 218 passed, 2 skipped (база — так же).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

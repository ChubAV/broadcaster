---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 61
subsystem: database
tags: [sqlalchemy, attribute-events, merge, autoflush, contextvars, runtime-guard, single-writer, WR-37, IN-23, IN-24, O-25, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-58 — линия движка _refuse_unscoped_cursor, суд нового объекта по значениям, шапка с четырьмя линиями; модуль защиты в тестах (FOREIGN_WRITES 26, LEGITIMATE_WRITES 14, CLOSED_FAILING_WRITES 2, ROUND_TEN_WRITER_FORMS 6); 16-51 / 16-55 — writer_scope, _WRITER_ACTIVE, правило входа в разрешение"
provides:
  - "Слушатель _refuse_attribute_set(target, value, oldvalue, initiator) события set обеих колонок номера: пропуск только при загруженном старом значении простого типа, равном новому (WR-37); remove / modified — прежний _refuse_attribute_write"
  - "Операторы UPDATE писателя (_fill_if_unknown, set_manual_phone) исполняются с autoflush=False (IN-23)"
  - "Шапка защиты: сравнение у set, писатель без автосброса, снятие разрешения только в текущем контексте и копия в задаче (IN-24), граница по таблице GUARD_BOUNDARY_WRITES с причиной и рубежом каждой строки, цена merge поверх истёкшей копии"
  - "Модуль защиты в тестах: LEGITIMATE_WRITES +2 (16), FOREIGN_WRITES +8 (34), CLOSED_FAILING_WRITES +1 (3), конструктор +2, правило автосброса, GUARD_BOUNDARY_WRITES (4) и правило измеренной границы, расширенное правило шапки"
affects: [16-62, 16-64, "Фазы 18–20 (перенос объекта в задачу Celery через merge больше не отказывает; отложенные изменения сессии вызывающего не сбрасываются оператором писателя)"]

actuals:
  tokens: 9362    # chars/4: дифф 14b8cfbe..39c04a34 — 37 450 байт (wc -c); кириллица по 2 байта, оценка плана 70 000 включала чтение контекста
  tasks: 3
  commits: 6      # git rev-list --count 14b8cfbe..HEAD до коммита сводки
plan_head_before: 14b8cfbe1f7735f10a873a2ec9f491006444d494
plan_head_after: 39c04a3437be8d71f875dfa68ccd65cf28a841bb

tech-stack:
  added: []
  patterns:
    - "Слушатель set без active_history сравнивает с oldvalue из словаря объекта: NO_VALUE / NEVER_SET — отказ, значение не простого типа (выражение SQL) — отказ, иначе пропуск только при равенстве"
    - "Оператор писателя под разрешением — с execution_options(autoflush=False): разрешение покрывает ровно оператор писателя, а не автосброс чужих изменений"
    - "Таблица измеренной границы: строка исполнением ПИШЕТ номер и называется шапкой; отказ строки — сигнал «граница закрылась», а не поломка"

key-files:
  created: []
  modified:
    - app/models/phone_guard.py
    - app/application/accounts/phone.py
    - tests/test_application/test_phone_writer_runtime_guard.py

key-decisions:
  - "Сравнение у set — только для значений простого типа (str, bool, int, None), сравнение по точному типу: выражение SQL (sqlalchemy.null()) сравнением дало бы TypeError или ложную истину вместо отказа (сверх плана, Rule 2; строка assignment-of-a-sql-expression)"
  - "merge в сессию, где копия того же аккаунта лежит с истёкшим номером, отказывает и при неизменном значении — названо ценой «отказ в закрытую» и закреплено строкой CLOSED_FAILING_WRITES, а не послаблено (active_history не включается)"
  - "Слово «Летопись» в шапке защиты — по-прежнему одно, в последнем абзаце: строка летописи о прежней фразе finally стоит там, а не в разделе ЧЕМ РАЗРЕШЕНО"

patterns-established:
  - "Соседи каждого послабления защиты — строки FOREIGN_WRITES рядом с законной строкой: другой номер, новый объект, только признак, тот же номер мимо событий атрибута"

requirements-completed: [PHONE-02]   # копия requirements плана; REQUIREMENTS.md этот план не трогает (заметка 5 оркестратора)

coverage:
  - id: D1
    description: "Перенос загруженного аккаунта (merge при load=True) с прежними значениями и присваивание загруженному атрибуту того же значения проходят без отказа и без UPDATE (WR-37)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_legitimate_write_passes[merge-of-a-loaded-account], [same-value-assignment-of-a-loaded-account]"
        status: pass
    human_judgment: false
  - id: D2
    description: "Соседи послабления отказывают: merge с другим номером, merge только признака, merge нового объекта с номером, присваивание истёкшему атрибуту, выражение SQL, то же значение поверх set_committed_value на новом объекте, тот же номер через bulk_update_mappings и через update() соединения; конструктор с None / False; merge поверх истёкшей копии — отказ в закрытую"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_foreign_write_is_refused (34), #test_a_constructor_argument_of_a_phone_column_is_refused (4), #test_a_write_whose_values_cannot_be_judged_is_refused_closed (3)"
        status: pass
      - kind: unit
        ref: "git show 14b8cfbe:tests/test_application/test_phone_writer_runtime_guard.py против итоговой защиты — 58 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Чужое отложенное изменение колонок номера не сбрасывается под разрешением писателя: коммит отказывает, обе строки (None, False); число и порядок операторов писателя прежние (IN-23)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_foreign_pending_change_is_not_flushed_under_the_writer_scope"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_race.py (4; 21 утверждение — как на 19c99ffb), tests/test_application/test_account_phone_writer.py (24)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Измеренная граница: text() через сессию, exec_driver_sql, сырое соединение DBAPI и задача, порождённая внутри writer_scope(), исполнением пишут номер, и шапка защиты называет каждую строку"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_named_boundary_of_the_guard_is_measured_and_named (4)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Шапка защиты и абзац писателя называют сравнение у set, autoflush=False, снятие разрешения только в текущем контексте и границу по замеру"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_the_guard_module_names_what_it_refuses_and_its_boundary"
        status: pass
    human_judgment: true
    rationale: "Правило сверяет имена и соседство слов; правдивость прозы шапки относительно поведения судит верификатор финального раунда (О-26 (а))"

duration: 42min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 61: сравнение значения у события `set`, писатель без автосброса и измеренная граница защиты — Summary

**Слушатель `set` колонок номера сравнивает новое значение с уже загруженным, поэтому `merge` загруженного аккаунта с прежним номером больше не отказывает, а `merge` с другим номером, новый объект, истёкший атрибут и выражение SQL отказывают как прежде (WR-37). Операторы UPDATE писателя исполняются с `autoflush=False`, и чужое отложенное изменение номера больше не сбрасывается под разрешением (IN-23). Шапка защиты называет каждую строку таблицы измеренной границы `GUARD_BOUNDARY_WRITES`, включая задачу, которая уносит разрешение из `writer_scope()` (IN-24).**

## Performance

- **Duration:** 42 мин (из них широкий прогон — 24 мин 9 с)
- **Started:** 2026-10-26T09:01:24Z
- **Completed:** 2026-10-26T09:43:36Z
- **Tasks:** 3, каждая по циклу RED → GREEN
- **Files modified:** 3

## Accomplishments

- `_refuse_attribute_set(target, value, oldvalue, initiator)` на событии `set` обеих колонок. Запись пропускается, только если старое значение загружено (не `NO_VALUE` / `NEVER_SET`), оба значения простого типа и равны. `remove` и `modified` по-прежнему отказывают всегда. `active_history` не включается.
- Операторы писателя `_fill_if_unknown` и `set_manual_phone` идут с `.execution_options(synchronize_session=False, autoflush=False)`. Число, порядок, условия операторов и точки ожидания прежние.
- Модуль защиты в тестах: 58 → 76 правил. Добавлены законные строки `merge` / то же значение, 8 соседних строк отказа, 2 строки конструктора, строка цены, правило автосброса, 4 строки границы и расширенное правило шапки.
- Шапка защиты и абзац писателя «ЗАЩИТА НА ИСПОЛНЕНИИ» описывают защиту по замеру. Докстринг `writer_scope()` называет текущий контекст.

## Task Commits

1. **Задача 1 (трасер): `merge` и то же значение (WR-37)**
   - RED `9940ec11` — `test(16-61): add failing rows for a merge and a same-value assignment of a loaded account`
   - GREEN `c278d839` — `feat(16-61): compare the set event with the loaded value so a merge of an unchanged account passes`
   - Гейт трасера: интерактивный прогон, `end-of-phase`, проверка только `<automated>`. Повторный прогон зелёный, переход к расширению.
2. **Задача 2: автосброс писателя (IN-23), таблица границы (IN-24)**
   - RED `29caa899` — `test(16-61): add a failing pending-change rule and the measured guard boundary table`
   - GREEN `c31e077a` — `feat(16-61): run the writer UPDATE statements without autoflush under the writer scope`
3. **Задача 3: шапка и абзац писателя по замеру**
   - RED `c926c0a1` — `test(16-61): require the guard header and writer paragraph to name the set comparison, autoflush and the measured boundary`
   - GREEN `39c04a34` — `feat(16-61): name the set comparison, writer autoflush and the measured guard boundary in the headers`

Коммитов REFACTOR нет: менять было нечего. Для 16-64: GREEN WR-37 — `c278d839`, IN-23 — `c31e077a`, тексты WR-37 / IN-23 / IN-24 — `39c04a34`.

## TDD: RED-улики (три совпадения + классификатор)

Улики лежат в `.pytest_cache/gsd-red/t{1,2,3}.{xml,out,json}` (gitignored). Записи `{command, exitCode, targetTest, output, …}` поданы в `check tdd-red-evidence`. Все три вернули `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | Цель | `FAILED …::<цель>` | Последняя строка | Причинный литерал | Семантическая оценка |
|---|---|---|---|---|---|
| 1 | `test_a_legitimate_write_passes[merge-of-a-loaded-account]` | да (и `[same-value-assignment-of-a-loaded-account]`) | `2 failed, 5 passed, 64 deselected, 1 warning in 1.04s` | `LEGITIMATE_RED` «законная запись аккаунта отказала или дала не тот итог; исход: PhoneWriteOutsideWriter» | Цель исполнилась и упала на своём утверждении: безусловный слушатель `set` отказал переносу с неизменными значениями. 5 зелёных строк — закрепки отказа (`merge` с другим номером, только признак, новый объект, поверх истёкшей копии). Весь модуль на базе: `2 failed, 69 passed` |
| 2 | `test_a_foreign_pending_change_is_not_flushed_under_the_writer_scope` | да | `1 failed, 75 deselected, 1 warning in 0.44s` | `PENDING_RED` «чужое отложенное изменение номера сброшено под разрешением писателя (IN-23); исход: NoneType» | Коммит прошёл: автосброс оператора писателя под `writer_scope()` записал чужой номер. Строки границы на RED: 3 зелёные, `task-spawned-inside-the-writer-scope` упала только половиной шапки («create_task»), сама запись прошла |
| 3 | `test_the_guard_module_names_what_it_refuses_and_its_boundary` | да | `2 failed, 3 passed, 71 deselected, 1 warning in 0.78s` | `HEADER_RED` «шапка защиты не называет, что отказывает и где её граница» | Недостающие имена — ровно те, что добавляет этот план: `merge`, `autoflush=False`, `create_task`, `IN-23`, `IN-24`, `WR-37`, `GUARD_BOUNDARY_WRITES`, `finally` без «текущем», в абзаце писателя — `autoflush=False`, `IN-23`. Вторая упавшая — строка задачи таблицы границы (её шапочная половина) |

## Таблица измеренной границы (`GUARD_BOUNDARY_WRITES`) — для 16-62

Замер — правило `test_a_named_boundary_of_the_guard_is_measured_and_named` на итоговом дереве. Каждая строка после `commit` даёт колонки `(NUMBER, False)`, отказа нет.

| id строки | Запись | Фраза шапки | Почему защита не видит | Что держит |
|---|---|---|---|---|
| `text-update-through-the-session` | `session.execute(text("UPDATE messenger_accounts SET phone = :phone WHERE id = :id"), {...})` | `text(` | `compiled.statement` — это `TextClause`, признаки INSERT / UPDATE ложны | статический гейт писателя (литерал SQL, вид 5) и канал запрета (текст из имени или вычисленный) |
| `exec-driver-sql-update` | `(await session.connection()).exec_driver_sql("UPDATE … ?", (NUMBER, id))` | `exec_driver_sql` | оператор без компиляции, `context.compiled is None` | то же, что у `text(` |
| `raw-dbapi-driver-connection-update` | `(await (await session.connection()).get_raw_connection()).driver_connection.execute("UPDATE … ?", …)` | `сырое соединение DBAPI` | идёт мимо движка, событий нет | литерал SQL держит предикат гейта писателя; текст SQL из параметра не держит ни один рубеж (граница гейта писателя, план 16-62) |
| `task-spawned-inside-the-writer-scope` | `asyncio.create_task(…)` внутри `with writer_scope():`, после выхода — `update(MessengerAccount)…values(phone=NUMBER)` | `create_task` | задача копирует контекст вместе с `_WRITER_ACTIVE = True`, а `finally` снимает переменную только в текущем контексте | правило плана 16-55 «в разрешение входит только писатель»; писатель задач и потоков не порождает |

Шапка вне таблицы называет ещё два пункта границы: `set_committed_value` на сохранённом объекте (оператора нет) и процесс без `app.models`.

## Замеры (база — замер оркестратора на `14b8cfbe`)

| Проверка | База | После плана |
|---|---|---|
| модуль защиты `test_phone_writer_runtime_guard.py` | 58 | 76 (+18: 2 законные, 8 отказ, 2 конструктор, 1 цена, автосброс 1, граница 4) |
| задача 1 / задача 2 (модуль защиты + писатель 24 + гонка 4 + CHECK 10) | 96 | 109 / 110 (+ 4 строки границы вне `-k`) |
| **базовый модуль защиты** (`git show 14b8cfbe:…` → `.pytest_cache/r11diff/base_guard_test.py`) против итоговой защиты | 58 | **58 passed** — ни один прежний отказ не потерян |
| утверждения теста гонки против `19c99ffb` | 21 | `OK 21` |
| сырых находок в писателе (`phone_write_offences`) / `autoflush=False` в `_fill_if_unknown`, `set_manual_phone` | 6 / — | `raw 6 OK` (по одному у каждого) |
| писатель, живое дерево (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` (первое число прежнее: комментарий и параметр исполнения сырых записей не добавляют) |
| гейт приватности + гейт писателя + паритет | 345 + 661 + 143 = 1149 | 1149 (после задачи 1 и в наборе фазы после задачи 3) |
| живые строки | приватность `app` 102/227, `scripts` 4/68, `max_worker` 2/93, 0; канал приватности 108, 0; JS `wa_worker` 1/68, 0; канал писателя 106, 0 | без изменений (6 passed: 5 правил живых деревьев + `entered_only_by_the_writer`) |
| набор фазы, вторая команда задачи 3 (9 путей, без модулей 16-60: план ещё не слит) | — | 1629 passed, 92,7 с |
| сквозные гейты (htmx post pairs, htmx gates, templates, declared invariants) | 576 | 576 passed (2 мин 50 с) |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строки | exit 0, 934 строки, биекция |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| **широкий прогон** (62 пути: grep плана в дереве исполнителя совпал с предвычисленным списком оркестратора) | 2762 (после 16-58) | **2784 passed, 0 failed**, 1448,9 с (24 мин 9 с). +22 = +18 правил этого плана + 4 правила паритета плана 16-59 (139 → 143). Отказов защиты на законных путях после `autoflush=False` нет |
| `tests/test_planning` (после коммита сводки) | 218 passed, 2 skipped | см. итоговое сообщение исполнителя |

**Замер прототипа WR-37** (зонд `.pytest_cache/checks/wr37_probe.py`, SQLite в памяти, слушатель подменён только в зонде). `merge` при `load=True` в сессию с загруженной копией и в свежую сессию — `PASSED`, строка `(None, False)`. То же значение — `PASSED`, `history.has_changes()` — `False`. `merge` с другим номером, только признака, нового объекта с номером — `PhoneWriteOutsideWriter`. Присваивание после `expire` и `sqlalchemy.null()` — отказ. Конструктор с `phone=None` — отказ. **`merge` в сессию, где копия лежит с истёкшим `phone`, — отказ**: `ColumnProperty.merge` не загружает истёкшее значение, и `oldvalue` равен `NO_VALUE`. Этот отказ назван ценой (см. отклонение 2).

## Files Created/Modified

- `app/models/phone_guard.py` — слушатель `_refuse_attribute_set`, регистрация (`set` → сравнение, `remove` / `modified` → прежний), шапка (линия 1, ЧЕМ РАЗРЕШЕНО, ПИСАТЕЛЬ БЕЗ АВТОСБРОСА, ГРАНИЦА по `GUARD_BOUNDARY_WRITES`, ЦЕНА, летопись), докстринг `writer_scope()`.
- `app/application/accounts/phone.py` — `autoflush=False` у двух операторов UPDATE с комментарием; абзац «ЗАЩИТА НА ИСПОЛНЕНИИ».
- `tests/test_application/test_phone_writer_runtime_guard.py` — строки и правила, перечисленные выше.

## Decisions Made

См. `key-decisions`. Главное: послабление касается ровно одного случая — старое значение загружено и равно новому. Всё остальное в линии атрибута по-прежнему отказывает. Неудобный остаток, `merge` поверх истёкшей копии, назван ценой и не послаблен: иначе пришлось бы загружать старое значение.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Сравнение только для значений простого типа; строка `assignment-of-a-sql-expression`**
- **Found during:** задача 1, прототип GREEN
- **Issue:** план велит сравнивать `value == oldvalue`. Для выражения SQL (`account.phone = sqlalchemy.null()`) оператор `==` строит `BinaryExpression`, и `bool()` от неё даёт `TypeError` или ложную истину. Прежний отказ `PhoneWriteOutsideWriter` подменился бы чужим исключением или потерялся бы.
- **Fix:** пропуск только при `type(value)` и `type(oldvalue)` из `(str, bool, int, NoneType)` и равенстве. Добавлена строка `FOREIGN_WRITES` `assignment-of-a-sql-expression`.
- **Files modified:** `app/models/phone_guard.py`, `tests/test_application/test_phone_writer_runtime_guard.py`
- **Verification:** строка отказывает и на базе, и после GREEN.
- **Committed in:** `9940ec11` (строка), `c278d839` (слушатель)

**2. [Rule 2 - честная граница] `merge` поверх истёкшей копии — строка `CLOSED_FAILING_WRITES` и фраза ЦЕНЫ**
- **Found during:** задача 1, зонд `wr37_probe.py`
- **Issue:** план называет «незагруженное или истёкшее старое значение — отказ» только для присваивания. Зонд показал тот же отказ для `merge` в сессию, где истекла копия того же аккаунта: ложный отказ при неизменном номере. Шапка о нём молчала бы.
- **Fix:** добавлена строка `merge-into-a-session-holding-an-expired-copy` в `CLOSED_FAILING_WRITES`. Докстринг правила расширен с «цены линии движка» до «цены защиты». Фраза об этом отказе добавлена в раздел ЦЕНА шапки. Поведение не послаблено.
- **Files modified:** `tests/test_application/test_phone_writer_runtime_guard.py`, `app/models/phone_guard.py`
- **Committed in:** `9940ec11`, `39c04a34`

**3. [Заметка 10 оркестратора] Соседи послабления в `FOREIGN_WRITES` сверх двух строк плана**
- Добавлены: `merge-changing-only-the-manual-flag`, `merge-of-a-new-object-carrying-a-number`, `same-value-over-a-committed-number-on-a-new-object` (линия 1 теперь пропускает, отказывает линия 2 по значениям), `bulk-update-mappings-of-the-same-number` и `connection-update-of-the-same-number` (посев номером писателя, отказывает линия движка). В правило конструктора добавлены `phone-none` и `phone-is-manual-false` (истина плана: «аргумент конструктора … в том числе `None`»). Все отказывают и на базе, и после плана.
- **Committed in:** `9940ec11`

**4. [Текст] Шапка: «текущем» строчными, летопись — в последнем абзаце**
- Правило плана ищет «текущем» с учётом регистра, поэтому шапка пишет «только в текущем контексте», а не «в ТЕКУЩЕМ». Правило не ослаблялось: исправлен текст.
- План ставит строку «Летопись: до плана 16-61 …» в раздел ЧЕМ РАЗРЕШЕНО. Строка стоит в последнем абзаце летописи. Так слово «Летопись» остаётся одним, как установил 16-58. Иначе правило шапки сочло бы летописью всё от раздела ЧЕМ РАЗРЕШЕНО.
- В абзац писателя добавлена фраза: прочие отложенные изменения сессии вызывающего теперь сбрасываются не перед оператором писателя, а на следующем сбросе или коммите. Это прямое следствие `autoflush=False`, названное для Фаз 18–20.
- **Committed in:** `39c04a34`

### Подстановки команд (та же логика, те же утверждения)

- RED задачи 1: `-k "merge or same-value"` вместо `-k "merge or same_value"`. Идентификатор строки пишется через дефис (`same-value-assignment-of-a-loaded-account`), и вариант плана её не выбирает. С ним сводка дала бы `1 failed` при пороге плана `N ≥ 2`.
- Однострочники `python -c` (`<automated>` задач 1 и 2, критерий гонки, критерий шапки задачи 3) записаны дословно в `.pytest_cache/checks/{t1_listener,t2_writer,t2_race,t3_header}.py` и исполнены с `PYTHONPATH=.` или из корня дерева. Выводы: `OK`, `raw 6 OK`, `OK 21`, `OK`.
- Базовый модуль защиты лежит вне `tests/`, поэтому запущен с `PYTHONPATH=. … -p tests.conftest -p no:cacheprovider`.
- Широкий прогон: `$(grep …)` плана заменён списком `@.pytest_cache/checks/breadth_files.txt` (62 пути). Grep плана пересчитан в этом дереве, список совпал (`diff` пуст).
- Все pytest и тяжёлые скрипты шли под общим `flock`.
- `tests/test_planning` из `<verify>` задачи 3 — после коммита сводки (заметка 5), а не до GREEN.
- `graphify update .` не запускался: граф обновит оркестратор после слияния. Ориентация — `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- Полный `just test` не запускался: это пост-мерж гейт оркестратора. Набор фазы взят без модулей плана 16-60, он ещё не слит.

---

**Total deviations:** 4: 2 по Rule 2 (сравнение простых типов; честная цена `merge` поверх истёкшей копии), 1 по заметке 10 (соседние строки), 1 текстовое. Плюс названные подстановки.
**Impact on plan:** все отклонения строже или честнее плана. Ни одна прежняя строка не сменила ответ, базовый модуль защиты — 58 из 58. Изменения только в трёх файлах плана.

## Issues Encountered

Нет. Гейт-модули, `app/models/__init__.py`, суиты гонки и CHECK, реестр запретов и записи `.planning/` (кроме этой сводки) не тронуты.

## Known Stubs

Нет.

## Threat Flags

Новых поверхностей вне модели угроз плана нет. Сделано: T-16-141 (сравнение у `set`, строки `merge`), T-16-142 (`autoflush=False`, правило автосброса), T-16-143 (accept: названо шапкой и закреплено строкой `task-spawned-inside-the-writer-scope`).

## Deferred

Нет. `deferred-items.md` не создавался.

## User Setup Required

Нет: внешних сервисов план не трогает.

## Next Phase Readiness

- 16-62 может цитировать имя таблицы `GUARD_BOUNDARY_WRITES`, четыре идентификатора её строк, таблицу границы выше и фразы шапки защиты: «сырое соединение DBAPI (`get_raw_connection().driver_connection`) — мимо движка, событий нет: литерал SQL держит предикат гейта писателя, а текст SQL из параметра не держит ни один рубеж (граница гейта писателя, план 16-62)». Имя «RAW_SQL_BOUNDARY_FORMS» этот план не вводит, оно за 16-62.
- 16-64 записывает GREEN: WR-37 — `c278d839` (и тексты `39c04a34`), IN-23 — `c31e077a` (и тексты `39c04a34`), IN-24 — `39c04a34`.
- Фазы 18–20: перенос объекта в задачу Celery через `merge` больше не отказывает, если номер не менялся и в целевой сессии нет истёкшей копии.

## Self-Check: PASSED

- Файлы на месте: `app/models/phone_guard.py`, `app/application/accounts/phone.py`, `tests/test_application/test_phone_writer_runtime_guard.py`, эта сводка.
- Коммиты на HEAD: `9940ec11`, `c278d839`, `29caa899`, `c31e077a`, `c926c0a1`, `39c04a34`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

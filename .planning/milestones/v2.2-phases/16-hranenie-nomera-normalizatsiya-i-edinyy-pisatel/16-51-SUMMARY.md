---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 51
subsystem: database
tags: [single-writer, runtime-guard, sqlalchemy-events, before_flush, do_orm_execute, contextvar, phone, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "модуль-писатель app/application/accounts/phone.py (16-05…16-49), CHECK ck_messenger_accounts_manual_requires_phone, тест гонки с контролем-отрицанием D-08, статический гейт писателя D-13"
provides:
  - "app/models/phone_guard.py — защита единственного писателя на исполнении: GUARDED_COLUMNS, PHONE_WRITE_OUTSIDE_WRITER, PhoneWriteOutsideWriter, writer_scope(), _WRITER_ACTIVE; слушатели set/remove/modified обеих колонок, before_flush и do_orm_execute класса Session; _statement_columns()"
  - "регистрация защиты последней строкой app/models/__init__.py — в каждом процессе, где есть модель"
  - "писатель исполняет ровно два своих UPDATE под writer_scope(); абзац шапки «ЗАЩИТА НА ИСПОЛНЕНИИ»"
  - "tests/test_application/test_phone_writer_runtime_guard.py — трасер, FOREIGN_WRITES (16), LEGITIMATE_WRITES (7), ROUND_TEN_WRITER_FORMS (6), пути репозитория, отрицание гонки без разрешения, правило шапки — 36 правил"
  - "правила CHECK и отрицание гонки строят состояния под writer_scope(), утверждения прежние"
affects: [16-53, 16-55, 16-56, phase-18, phase-19, phase-20]

actuals:
  tokens: 11837   # chars/4: дифф a8fb02c9..e1eb00b4 — 47 348 знаков (wc -m)
  tasks: 3
  commits: 6      # git rev-list --count a8fb02c9..e1eb00b4 (до коммита сводки)
plan_head_before: a8fb02c958fe0b9c7768331375f66bb30d6211ec
plan_head_after: e1eb00b4e834d7d9ea46037952f6ef94a72cfafc

tech-stack:
  added: []
  patterns:
    - "Защита инварианта колонки на исполнении: слушатели событий атрибута + before_flush + do_orm_execute, разрешение — ContextVar под contextmanager с reset(token) в finally"
    - "Регистрация слушателей ввозом из пакета моделей (последняя строка __init__), разрешение — в модуле защиты, чтобы не было цикла ввоза"
    - "Колонки оператора читаются по типу (isinstance Update/Insert, ColumnElement, QueryableAttribute) и индексом attrs[…], без getattr со строкой и без dunder-атрибутов"
    - "RED-литерал через ручной перехват исключения (_refusal_of) и утверждение с сообщением: без модуля защиты правило падает утверждением, а не ошибкой сбора"

key-files:
  created:
    - app/models/phone_guard.py
    - tests/test_application/test_phone_writer_runtime_guard.py
  modified:
    - app/models/__init__.py
    - app/application/accounts/phone.py
    - app/models/messenger_account.py
    - tests/test_models/test_messenger_account_phone_check.py
    - tests/test_application/test_account_phone_race.py

key-decisions:
  - "Таблица оператора сверяется is_derived_from(sa_inspect(MessengerAccount).local_table), а не именем с __tablename__: без dunder-атрибута (запрет плана 16-53) и с учётом псевдонимов таблицы"
  - "Оператор INSERT … from_select([…]) с колонкой номера тоже отказывает (_select_names) — строка orm-insert-from-select сверх 15 строк плана"
  - "Граница защиты в шапке дополнена правдиво: text(\"UPDATE …\") и через Session.execute (у текста is_update ложен) и ветка ON CONFLICT DO UPDATE SET — вне защиты, их держат гейт и запрет конструкции"
  - "Запись проверяется по истории added в before_flush, а события атрибута отказывают всегда вне разрешения — писатель событий атрибута не порождает (set_committed_value событий не даёт)"

patterns-established:
  - "Тест, строящий невозможное состояние ради доказательства ограничения базы, входит в writer_scope() сам — моделирует писателя с ошибкой, а не обходит защиту"
  - "Формы ревью/верификации исполняются exec над настоящей моделью с подменой носителя прямым вызовом: правило судит запись, а не поток"

requirements-completed: []   # PHONE-02 в requirements плана; отметку Complete не ставим — вердикт фазы gaps_found, учёт ведёт оркестратор (заметка 5)

coverage:
  - id: D1
    description: "Запись колонок phone / phone_is_manual вне писателя отказывает PhoneWriteOutsideWriter на каждом пути ORM (атрибут, конструктор, setattr, set_attribute, дескриптор, object.__setattr__, del, flag_modified, сброс, UPDATE/INSERT сессии), строка прежняя"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_foreign_write_is_refused (16 строк), #test_a_constructor_argument_of_a_phone_column_is_refused (2)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Сквозной срез: подложенный сценарий дозаполнения с account.phone = … отказывает до оператора записи, fill_reported_phone тот же номер пишет"
    requirement: PHONE-02
    verification:
      - kind: integration
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_planted_backfill_assigning_the_phone_is_refused_and_the_writer_writes"
        status: pass
    human_judgment: false
  - id: D3
    description: "Законные пути (создание без номера, правка статуса атрибутом и оператором, выборка по номеру, репозиторий без колонок номера, DELETE) не отказывают; широкий прогон суит с MessengerAccount — 0 отказов защиты"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_legitimate_write_passes (7)"
        status: pass
      - kind: integration
        ref: "uv run pytest @<57 файлов grep -rl MessengerAccount tests> -q -p no:randomly — 2448 passed"
        status: pass
    human_judgment: false
  - id: D4
    description: "Формы раунда 10 стороны писателя (WR-33, V10-1, V10-2) и пути репозитория отказывают исполнением; форма set_committed_value колонку в базе не пишет"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_a_round_ten_writer_form_is_safe_at_run_time (6), #test_the_repository_paths_of_a_phone_column_are_refused"
        status: pass
    human_judgment: false
  - id: D5
    description: "Правила CHECK и отрицание гонки сохраняют смысл под writer_scope(); без разрешения отрицание отказывает защитой; разрешение закрыто после исключения"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_models/test_messenger_account_phone_check.py (10), tests/test_application/test_account_phone_race.py (4), #test_a_read_check_write_outside_the_writer_scope_is_refused, #test_the_scope_is_closed_after_an_exception_inside_it"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_race_asserts.py — утверждения теста гонки против c9da79b2: OK 21"
        status: pass
    human_judgment: false
  - id: D6
    description: "Шапка защиты, абзац писателя и комментарий модели называют защиту, разрешение и границу; гейты не считают модуль защиты писателем и журналом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_writer_runtime_guard.py#test_the_guard_module_names_what_it_refuses_and_its_boundary"
        status: pass
      - kind: other
        ref: "writer_live.py — OK 6 105 offences 0; privacy live trees — 225 / 68 / 93, находок 0"
        status: pass
    human_judgment: false

duration: 1h 14m
completed: 2026-10-23
status: complete
---

# Phase 16 Plan 51: Защита единственного писателя на исполнении — Summary

**Запись колонок `phone` / `phone_is_manual` вне `app/application/accounts/phone.py` отказывает в момент записи тремя линиями SQLAlchemy (события атрибута `set`/`remove`/`modified`, `before_flush`, `do_orm_execute` UPDATE/INSERT), а писатель пишет под `writer_scope()` на `ContextVar`; защита регистрируется пакетом моделей в каждом процессе.**

## Performance

- **Duration:** 1h 14m (из них ≈24 мин — широкий прогон, ≈25 мин — ожидание замка за прогоном оркестратора)
- **Started:** 2026-10-23T06:51:54Z
- **Completed:** 2026-10-23T08:05:59Z
- **Tasks:** 3 (трасер + 2), все RED → GREEN
- **Files modified:** 7 (2 созданы, 5 изменены)

## Accomplishments

- Новый модуль `app/models/phone_guard.py`: `PhoneWriteOutsideWriter(RuntimeError)` с постоянным текстом без номера (D-11), `writer_scope()` (снимается токеном в `finally`), слушатели атрибута обеих колонок, `before_flush` (история `added` у `MessengerAccount` из `new | dirty`) и `do_orm_execute` (колонки из `_values`, `_ordered_values`, `_multi_values`, `_select_names` и параметров исполнения). Ни одной запрещённой планом 16-53 конструкции, ни одного вызова журнала.
- Регистрация последней строкой `app/models/__init__.py`; писатель обернул в `writer_scope()` ровно два оператора (UPDATE `_fill_if_unknown`, UPDATE `set_manual_phone`) — порядок и число операторов прежние (тест гонки зелёный, гейт писателя: в модуле-писателе 6 сырых, как на базе).
- Новый тестовый модуль — 36 правил: трасер, конструктор (2), разрешение после исключения, `FOREIGN_WRITES` (16), `LEGITIMATE_WRITES` (7), `ROUND_TEN_WRITER_FORMS` (6), пути репозитория, отрицание гонки вне разрешения, правило шапки.
- Правила CHECK и отрицание гонки строят состояния под `writer_scope()`; утверждения не изменены (AST-сверка утверждений теста гонки с `c9da79b2`: `OK 21`).
- Широкий прогон суит с `MessengerAccount` — 2448 passed (база оркестратора 2412 на 56 файлах + 36 правил нового модуля в 57-м), отказов защиты на законных путях — ноль.

## Task Commits

1. **Задача 1 (трасер): сквозной срез, слушатели атрибута, регистрация, разрешение писателя, CHECK под разрешением**
   - RED `6b702427` — `test(16-51): add failing tracer for the runtime single-writer guard`
   - GREEN `69d73441` — `feat(16-51): refuse a phone column write outside the writer at run time`
2. **Задача 2: `before_flush` и `do_orm_execute`; таблицы чужих и законных записей, формы раунда 10, репозиторий, отрицание гонки**
   - RED `9cad8c76` — `test(16-51): add failing tables of foreign and legitimate phone writes`
   - GREEN `85af8e2f` — `feat(16-51): refuse unscoped phone writes at flush and in session statements`
3. **Задача 3: шапка защиты, абзац писателя, комментарий модели; широкий прогон и сквозные гейты**
   - RED `6a858726` — `test(16-51): add failing rule for the runtime guard header and its boundary`
   - GREEN `e1eb00b4` — `feat(16-51): name the runtime guard, its writer scope and its boundary in the headers`

REFACTOR-коммитов нет (не понадобились).

## TDD: RED-улики (три совпадения + верб)

Улики — `.pytest_cache/gsd-red/task{1,2,3}-red.{out,xml,json}` (gitignored); каждая запись `{command, exitCode, targetTest, output=JUnit XML}` прошла `check tdd-red-evidence` → `RED_EVIDENCE_OK`, `target_test_failed`.

| Задача | Команда | Строка `FAILED` | Последняя строка | Причинный литерал |
|--------|---------|-----------------|------------------|-------------------|
| 1 | `uv run pytest tests/test_application/test_phone_writer_runtime_guard.py -q -p no:randomly --junit-xml=…` (exit 1) | `FAILED …::test_a_planted_backfill_assigning_the_phone_is_refused_and_the_writer_writes` | `4 failed, 1 warning in 0.40s` | «присваивание номера атрибуту вне писателя не отказало защитой на исполнении — сценарий записал колонку мимо app/application/accounts/phone.py; исход: NoneType» |
| 2 | то же, `-k "test_a_foreign_write_is_refused or outside_the_writer_scope"` (exit 1) | `FAILED …::test_a_foreign_write_is_refused[orm-update-values]` | `10 failed, 7 passed, 18 deselected, 1 warning in 1.84s` | «запись колонки номера вне писателя не отказала защитой на исполнении; исход: NoneType» (9 строк) и «отрицание гонки вне разрешения писателя не отказало …» (правило 5) |
| 3 | то же, `-k test_the_guard_module_names_what_it_refuses_and_its_boundary` (exit 1) | `FAILED …::test_the_guard_module_names_what_it_refuses_and_its_boundary` | `1 failed, 35 deselected, 1 warning in 0.25s` | «шапка защиты не называет, что отказывает и где её граница: […16 имён…]» |

**Семантическая оценка RED.** Задача 1: целевое правило исполнилось и упало на утверждении планируемого поведения — сценарий закоммитил номер, исключения не было (`refusal is None`); три других правила упали тем же отсутствием отказа (конструктор) и `ImportError` модуля защиты (правило разрешения — до GREEN модуля нет; это не цель). Задача 2: все 10 падений — утверждения с литералом (`_is_guard_refusal(None)`); семь строк атрибута зелены с задачи 1 — закрепки; правило 5 красно на RED (слушателя операторов не было), зелено после GREEN; отрицание гонки под `scope=writer_scope` зелено и до, и после GREEN. Задача 3: правило исполнилось и назвало 16 недостающих имён. Ошибок сбора, пустых выборок, падений фикстур нет ни в одной улике.

**GREEN.** Задача 1 — модуль защиты со слушателями атрибута, регистрация, разрешение писателя, CHECK под разрешением: 38 passed. Задача 2 — `before_flush` и `do_orm_execute`: 73 passed. Задача 3 — тексты: модуль защиты 36 passed.

## Files Created/Modified

- `app/models/phone_guard.py` (создан) — защита: константы, исключение, `writer_scope()`, три линии слушателей, `_statement_columns()`; шапка «ЗАЧЕМ / ЧТО ОТКАЗЫВАЕТ / ЧЕМ РАЗРЕШЕНО / ПОЧЕМУ В ПАКЕТЕ МОДЕЛЕЙ / ГРАНИЦА».
- `app/models/__init__.py` — последней строкой ввоз `phone_guard` с доводом; `__all__` не изменён.
- `app/application/accounts/phone.py` — ввоз `writer_scope`, два UPDATE под разрешением, абзац «ЗАЩИТА НА ИСПОЛНЕНИИ».
- `app/models/messenger_account.py` — комментарий колонки `phone` называет `app/models/phone_guard.py`; определения колонок не тронуты.
- `tests/test_application/test_phone_writer_runtime_guard.py` (создан) — 36 правил защиты.
- `tests/test_models/test_messenger_account_phone_check.py` — построение и `flush` под `writer_scope()`, абзац докстринга, фраза главного правила дополнена «под разрешением защиты на исполнении».
- `tests/test_application/test_account_phone_race.py` — `read_check_write(…, *, scope=writer_scope)`, UPDATE в `with scope():`, абзацы докстрингов.

## Замеры на финальном дереве (`e1eb00b4`, все под общим замком)

| Проверка | База (оркестратор) | Здесь |
|----------|--------------------|-------|
| `<automated>` задачи 1: модуль защиты + писатель + CHECK | — (план: ≥ 35) | 38 passed |
| `<automated>` задачи 1: гонка + `tests/test_migrations` | — | 141 passed |
| `<automated>` задачи 1: гейты не судят модуль защиты, реестр писателя — ровно писатель | — | `OK` |
| Слушатели зарегистрированы (`event.contains` × 6) | — | `OK` |
| `<automated>` задачи 2: защита + гонка + писатель + CHECK | — (план: ≥ 69) | 73 passed |
| AST: `scope` / `with scope():` в `read_check_write` | — | `OK` |
| Утверждения теста гонки против `c9da79b2` | — | `OK 21` |
| Модуль защиты целиком | — (план: ≥ 35) | 36 passed |
| Набор фазы (quick run, 9 путей) | 1364 (8 путей) | 1400 passed |
| Оба гейта + паритет | 960 | 960 passed (после задачи 1 и на финале) |
| Живые деревья приватности | `app` файлов 100, вызовов 225; `scripts` 4 / 68; `max_worker` 2 / 93; находок 0 | `app` файлов 101, вызовов 225; `scripts` 4 / 68; `max_worker` 2 / 93; находок 0; JS `wa_worker` 1 / 68, 0 |
| Живое дерево писателя (`writer_live.py`) | `OK 6 104 offences 0` | `OK 6 105 offences 0` |
| `tests/test_application` | 907 | 943 passed (+36) |
| `tests/test_models` | 56 | 56 passed |
| Широкий прогон суит с `MessengerAccount` | 2412 passed (56 файлов) | 2448 passed (57 файлов: +36 нового модуля), 0 failed |
| Сквозные гейты (`htmx_post_pairs`, `htmx_gates`, `test_templates`, `declared_invariants`, `test_logging_config`) | 576 + 3 | 579 passed |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `prohibitions_census.py --check` | exit 0, 913 строк, биекция | exit 0, 913 строк, биекция |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `tests/test_planning` | 218 passed, 2 skipped | гонится после коммита сводки (заметка 5) |

**Широкий прогон — что покрыт и что нет.** Покрыт: все 57 файлов `tests/**/test_*.py`, ссылающихся на `MessengerAccount` (страницы, маршруты, воркеры, приложение, модели, миграции, гейты), из корня worktree, один раз — разница с базой ровно +36 правил нового модуля, новых падений ноль. Не покрыт: остальные ≈2 800 правил суиты, не упоминающих `MessengerAccount` по имени (в том числе суиты, создающие аккаунт через фабрики других модулей без имени класса в тексте) — их покрывает пост-мердж `just test` оркестратора.

## Decisions Made

- Таблица оператора — `statement.table.is_derived_from(sa_inspect(MessengerAccount).local_table)` вместо сравнения имени с `__tablename__` (план, задача 2): так модуль защиты не держит dunder-атрибутов, которые запрет 16-53 судит как служебный протокол атрибутов, и узнаёт таблицу и под псевдонимом. Замер до кода: `True` для `update(MessengerAccount)` (AnnotatedTable), `update(MessengerAccount.__table__)` (Table), `insert(MessengerAccount)`.
- Ключ колонки оператора читается по типу: `str` — как есть, `ColumnElement` / `QueryableAttribute` — `.key`; замер: ORM-`values(phone=…)` и `values({MessengerAccount.phone: …})` дают `AnnotatedColumn`, Core-`update(table).values(phone=…)` — `str`, `from_select` — `str`.
- Сообщение утверждения о `raises` — литерал RED: вместо `pytest.raises(PhoneWriteOutsideWriter)` правила перехватывают исход (`_refusal_of`) и утверждают с сообщением-литералом; затем сверяют `isinstance`, текст `PHONE_WRITE_OUTSIDE_WRITER` и отсутствие цифр номера — те же утверждения, что у `pytest.raises` с текстом.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `INSERT … from_select([…])` с колонкой номера тоже отказывает**
- **Found during:** Задача 2 (замер атрибутов оператора до GREEN)
- **Issue:** план перечисляет `_values`, `_ordered_values`, `_multi_values` и параметры; у `insert(MessengerAccount).from_select(["…", "phone"], select(…))` колонки лежат в `_select_names`, и такой INSERT прошёл бы мимо третьей линии.
- **Fix:** `_statement_columns` читает и `_select_names` у `Insert`; строка `orm-insert-from-select` в `FOREIGN_WRITES` (16 строк вместо 15).
- **Files modified:** `app/models/phone_guard.py`, `tests/test_application/test_phone_writer_runtime_guard.py`
- **Verification:** строка красна на RED `9cad8c76` (10 failed вместо 9 по плану), зелена на GREEN `85af8e2f`.
- **Committed in:** `9cad8c76` (RED), `85af8e2f` (GREEN)

**2. [Rule 1 - Truthfulness] Граница защиты в шапке названа полнее плана**
- **Found during:** Задача 3
- **Issue:** граница плана не называла `text("UPDATE …")` через `Session.execute` (слушатель срабатывает, но `is_update` у текста ложен) и ветку `ON CONFLICT DO UPDATE SET …` (колонки вне `values(…)`).
- **Fix:** оба пункта дописаны в «ГРАНИЦА, НАЗВАННАЯ ПРЯМО» рядом с пунктами плана; закрыть их — забота статического гейта и запрета конструкции, как и прочие пути в обход.
- **Files modified:** `app/models/phone_guard.py`
- **Committed in:** `e1eb00b4`

### Расхождения замера с планом (замер выигрывает; строк и утверждений не убавлено)

- `tests/test_models/test_messenger_account_phone_check.py` — 10 правил pytest (8 функций, одна параметризована тремя парами), а не 7: `<fails_when>` задачи 1 «≥ 35» → замер 38; задачи 2 «≥ 69» → 73 (ещё +1 — строка `orm-insert-from-select`); модуля защиты «≥ 35» → 36; набора фазы «≥ 1399» → 1400.
- RED задачи 2: `10 failed` (план: ≥ 9) — та же причина (+1 строка).
- RED задачи 1: правило разрешения падает `ImportError` модуля защиты (не утверждением): ввоз внутри тела правила, как велит план, даёт до GREEN ошибку ввоза в теле, а не ошибку сбора; цель RED — трасер, он падает утверждением с литералом.
- Признак таблицы — `is_derived_from(local_table)`, а не имя с `__tablename__` (см. Decisions).

### Подстановки исполнения (те же проверки, другая форма вызова)

- Каждая `uv run python -c "…"` из `<automated>` / `<acceptance_criteria>` записана дословно в `.pytest_cache/checks/*.py` (`t1_gates_judge_guard.py`, `t1_listeners_registered.py`, `t2_race_scope.py`, `t2_race_asserts.py`, `t3_header.py`) и исполнена с `PYTHONPATH=.`.
- Широкий прогон: `$(grep -rl …)` под `flock` песочница отвергла — список файлов записан в `.pytest_cache/checks/sweep_files.txt` (тот же `grep -rl --include='test_*.py' MessengerAccount tests`, 57 строк) и подан pytest файлом аргументов `@.pytest_cache/checks/sweep_files.txt`.
- Журнал базы плана (протокол 0c) записан в `.pytest_cache/plan-head-before-16-51`, а не в каталог git worktree: песочница отвергла запись по пути `.git/worktrees/…`; `commits:` измерен `git rev-list --count a8fb02c9..HEAD` от той же базы.
- `graphify update .` в worktree не запускался (заметка оркестратора: граф обновляет оркестратор после слияния); ориентация — `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- Полный `just test` не запускался (заметка 4): его гонит пост-мердж гейт оркестратора на слитом дереве.

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1 — правдивость шапки) + названные расхождения счёта и подстановки.
**Impact on plan:** обе правки расширяют закрытое и названное, не сужая ни одного правила плана; модули гейтов и предикаты распознавания не тронуты.

## Issues Encountered

- Прогон RED задачи 1 ≈25 минут ждал общего замка за широким прогоном оркестратора (базовая строка `### messengeraccount_suites`); черновики GREEN всё это время лежали вне дерева (`.pytest_cache/drafts/`), чтобы RED исполнялся на RED-коде.

## Known Stubs

Нет.

## Threat Flags

Нет новых поверхностей вне `<threat_model>` плана: модуль защиты — компонент T-16-116…T-16-118, сетевых путей, путей файлов и схемы не добавлено.

## Для следующих волн

- **16-53** (запрет динамики): в `app/models/phone_guard.py` нет `sys.modules`, `importlib`, `__import__`, `globals()` / `locals()` / `vars()`, `__dict__`, `eval` / `exec` / `compile`, `methodcaller` / `attrgetter`, `getattr` / `setattr` / `delattr` / `hasattr`, `__getattribute__` / `__getattr__` / `__setattr__`, `__tablename__` / `__table__`, вычисленного SQL — проверено поиском по исходнику; слова `setattr` и `object.__setattr__` встречаются только прозой в докстринге (перечень того, что отказывает).
- **16-55** (правило входа в разрешение): `writer_scope` и `_WRITER_ACTIVE` в `app/` / `scripts/` упоминаются только в `app/application/accounts/phone.py`, в самом модуле защиты и в регистрации `app/models/__init__.py` (ввоз `phone_guard`); `event.remove` нигде.
- **16-56**: GREEN-коммиты задачи — `69d73441`, `85af8e2f`, `e1eb00b4` (темы `feat(16-51): …` дословно выше).
- После слияния с 16-52 живое дерево писателя — 106 файлов (здесь — 105).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Защита на исполнении стоит; волна 2 (16-53) судит модуль защиты наравне с прочими файлами `app/`. Фаза по-прежнему `gaps_found` до верификации партии раунда 10.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-23*

## Self-Check: PASSED

- FOUND: `app/models/phone_guard.py`, `tests/test_application/test_phone_writer_runtime_guard.py`
- FOUND (ancestors of HEAD): `6b702427`, `69d73441`, `9cad8c76`, `85af8e2f`, `6a858726`, `e1eb00b4`

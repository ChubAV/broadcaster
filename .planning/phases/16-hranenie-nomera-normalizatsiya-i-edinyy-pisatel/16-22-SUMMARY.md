---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 22
subsystem: testing
tags: [ast, sqlalchemy, single-writer-gate, pytest, wr-12]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт единственного писателя планов 16-03/16-09/16-12/16-17 (JUDGED_PARAMETERS, _judge_call, _phone_column, _pair_candidates, _module_aliases, LITERAL_FORM_CASES, LEGITIMATE_CASES)"
provides:
  - "_phone_column: производная колонки номера любой цепочкой атрибутов и индексов (после прямых наименований); конструктор с именем любым литеральным связыванием (позиция, *[…], text=, **{…}); поиск по имени (.get / .get_property / .__getitem__, позицией и key=); строковая константа, склейка + констант, f-строка без подстановок"
  - "имя атрибута у писателей по имени судится через _phone_column (setattr(account, MessengerAccount.phone.key, x))"
  - "from_select: перечень в любом литеральном контейнере (_pair_candidates) и в любом позиционном аргументе; COPY asyncpg: таблица в любом позиционном аргументе"
  - "_api_aliases / _canonical_call / _api_alias_targets: псевдоним пишущего API в том же модуле (ввоз as, X = имя, X = объект.имя, цепочка) судится как сам API, с получателем, если связан с атрибутом"
  - "IDENTIFICATION_CARRIERS + _rename_aliases: псевдонимы methodcaller и getattr в том же модуле; methodcaller(…)(obj) подаёт получателя; InstrumentedAttribute.__set__(M.phone, …)"
  - "_forwarded_arguments: распаковка не-литерала за ссылкой подаётся синтетическому вызову API на месте"
  - "ColumnNaming / COLUMN_NAMINGS (32), ColumnContext / COLUMN_CONTEXTS (714) и правило-матрица test_every_column_naming_in_every_judged_context_is_a_write"
  - "правила test_a_planted_backfill_with_attribute_keys_reddens_the_gate, test_an_aliased_writer_api_in_the_same_module_is_judged; 47 строк LITERAL_FORM_CASES, 15 строк LEGITIMATE_CASES"
  - "шапка: заявление «через механизм» прежнее; виды 3, 4, 8 и абзац опознания расширены; пункты (1), (2), (4) границы с правдивой причиной; летопись WR-12 и решения О-10 (а)"
affects: [phase-18, phase-19, phase-20, 16-25]

actuals:
  tokens: 22736
  tasks: 3
  commits: 18
plan_head_before: 99002b1608ed3954cbd76147be6f04d069d61071
plan_head_after: 80153e32f5728781c670102b1207b3e2f3f2d1bf

tech-stack:
  added: []
  patterns:
    - "Ось «как названа колонка» — таблица COLUMN_NAMINGS крест-накрест с COLUMN_CONTEXTS в одном параметризованном правиле: одна красная строка на наименование со всеми промахами"
    - "Производная колонки проверяется ПОСЛЕ прямых наименований (ловушка порядка: иначе t.c[\"phone\"] уходит в рекурсию)"
    - "Псевдонимы носителей опознания (methodcaller, getattr) переименовываются в дереве до разбора; псевдонимы пишущих API канонизируются синтетическим вызовом"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Заявление шапки гейта единственного писателя прежнее (решение владельца О-10 (а)); каждая найденная форма под ним закрыта циклом RED/GREEN, а не границей"
  - "Матрица в суите — 714 контекстов (каждый контейнер строк со строкой-словарём, каждая форма строки в списке); полный крест форм строки × контейнеров (2114 контекстов) — в самопроверке исполнителя, ради времени модуля"
  - "Имя колонки, вычисленное ВЫЗОВОМ над строкой (\"PHONE\".lower(), \"{}\".format(\"phone\"), \"\".join(…), str(\"phone\")), — граница (2) с причиной «предикат вызовов не исполняет»; склейка + констант и f-строка без подстановок — ловятся (как в виде 5 у SQL)"
  - "Параметры, судимые позицией у from_select и COPY asyncpg, ищутся в каждом позиционном аргументе: метод через класс с явным self сдвигает позицию"

patterns-established:
  - "Самопроверка по двум осям скрещивает наименования колонки с полным крестом контекстов и формы опознания API с каждым базовым контекстом; формы, которые невозможно исполнить (run_sync(M, rows, fn=ref) — TypeError), в контексты не входят"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Подложенный скрипт дозаполнения с ключом MessengerAccount.phone.key в строках bulk_update_mappings в синтетическом scripts/ краснит гейт; одиннадцать форм WR-12 — находки ожидаемого вида"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_attribute_keys_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (152 строки)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_an_aliased_writer_api_in_the_same_module_is_judged"
        status: pass
    human_judgment: false
  - id: D2
    description: "Правило-матрица COLUMN_NAMINGS (32) × COLUMN_CONTEXTS (714): ровно одна находка ожидаемого вида в каждой ячейке"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_column_naming_in_every_judged_context_is_a_write (32 наименования)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Живое дерево app/ + scripts/ — 0 судимых находок; в модуле-писателе 6 сырых записей (5 × KIND_KEYWORD + 1 × KIND_SETATTR); реестр — ровно app/application/accounts/phone.py; законные упоминания — ноль находок"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_exception_registry_names_only_the_writer_module"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write (68 строк)"
        status: pass
      - kind: other
        ref: "третья команда <automated> задачи 3 — OK 6 104"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта: заявление «через механизм» прежнее, граница (1)/(2)/(4) — только с правдивой причиной, летопись WR-12 и О-10 (а)"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "критерии приёмки задач 2 и 3 (ast.get_docstring: «Ловится всякая запись…», «слепота предиката…», пункт (1) без «s.bulk_update_mappings; fn(»)"
        status: pass
    human_judgment: true
    rationale: "Правдивость прозы границы и летописи (что каждая причина верна, а заявление не сужено) оценивает человек или верификатор; автомат проверяет только присутствие фраз"

duration: 55min
completed: 2026-10-13
status: complete
---

# Phase 16 Plan 22: колонка номера, названная производной, псевдонимы пишущих API и ось наименований — правило-матрица Summary

**Гейт единственного писателя теперь видит колонку номера в любой производной (`.key`, `.name`, `.expression`, `.property.key`, `.property.columns[0]`), в поиске по имени, в конструкторе при любом литеральном связывании и в константной склейке. Он видит перечень `from_select` в любом контейнере и пишущий API под псевдонимом того же модуля, включая псевдонимы `methodcaller` и `getattr`. Ось «как названа колонка» держит в суите правило-матрица 32 × 714. Самопроверка 205 680 форм по обеим осям даёт ноль промахов; заявление шапки прежнее (О-10 (а)).**

## Performance

- **Duration:** ≈55 min
- **Started:** 2026-10-13T09:56:46Z
- **Completed:** 2026-10-13T10:51:32Z
- **Tasks:** 3 (плюс 6 циклов самопроверки)
- **Files modified:** 1

## Accomplishments

- Трасер WR-12: подложенный `scripts/backfill_attribute_key.py` с `[{"id": a.id, MessengerAccount.phone.key: n} for a, n in rows]` в `bulk_update_mappings` находится обходом и даёт `scripts/backfill_attribute_key.py:2 — ключ словаря строк — bulk_update_mappings([{MessengerAccount.phone.key: …}])`.
- Все одиннадцать форм WR-12 ловятся строками `LITERAL_FORM_CASES`. Форма `bum = Session.bulk_update_mappings` тоже ловится, и пункт (1) границы её больше не называет.
- Правило-матрица `COLUMN_NAMINGS` (32 наименования) × `COLUMN_CONTEXTS` (714 контекстов), ≈10 с на модуль. Контексты: каждый судимый параметр `JUDGED_PARAMETERS`, несущий колонку, и API без именованного параметра, каждый — во всех формах контейнера.
- Самопроверка по обеим осям (3 захода, 205 680 форм на последнем) нашла 6 классов слепоты сверх плана; каждый закрыт своим циклом RED/GREEN.
- Живое дерево: 104 файла, 0 судимых находок. В модуле-писателе 6 сырых записей, реестр — ровно модуль-писатель. Реальной записи номера вне писателя расширенный предикат не нашёл.

## Task Commits

1. **Задача 1: трасер `.key` / `.name`, имя атрибута через `_phone_column`.** RED `c3942090` (test), GREEN `ecd1be76` (feat).
2. **Задача 2: контейнер `from_select`, псевдонимы пишущих API, пункт (1).** RED `26beae2f` (test), GREEN `4d6f286e` (feat).
3. **Задача 3: матрица наименований, производная цепочкой, шапка.** RED `e0e2f081` (test), GREEN `9f50ed19` (feat).
4. **Самопроверка, заход 1:**
   - класс A — наименования: `9847fd01` / `878b4679`;
   - класс B-ref — `*` за ссылкой: `37ec629e` / `dbe22dcc`;
   - класс B-index — вызов через класс: `755c2351` / `a973ea55`;
   - класс B-receiver — получатель `__set__` / `__init__`: `9fe17694` / `ddbb33f7`.
5. **Самопроверка, заход 2:**
   - класс D — связывание имени у конструктора и поиска: `1a613249` / `a4c49b66`;
   - класс E — псевдонимы носителей: `764751d7` / `80153e32`.

**Plan metadata:** коммит этой сводки — `docs(16-22): …` (следующий после `80153e32`).

## TDD: RED / GREEN

RED каждого цикла засчитан тремя совпадениями: строка `FAILED …::<цель>`, итог `N failed` и причинный литерал. Каждая улика прошла `check tdd-red-evidence` с вердиктом `RED_EVIDENCE_OK` (JUnit XML; записи лежат в gitignored `.pytest_cache/gsd-red/`, не коммитятся). Семантическая оценка: каждая цель исполнилась и упала на утверждении «гейт ничего не нашёл» (`[]` / `0 находок`). Ошибок сбора, импорта и пустых выборок нет.

| Цикл | Цель RED | Итог | Причинный литерал |
|------|----------|------|-------------------|
| 1 | `test_a_planted_backfill_with_attribute_keys_reddens_the_gate` | `1 failed` | «ключ MessengerAccount.phone.key в строках bulk_update_mappings не найден» |
| 2 | `test_an_aliased_writer_api_in_the_same_module_is_judged` | `1 failed` | «псевдоним пишущего API в том же модуле не опознан» |
| 3 | `test_every_column_naming_in_every_judged_context_is_a_write[property-key]`, `[property-columns-index]`, `[expression]` | `3 failed, 17 passed` | «наименование колонки не опознано» (714 из 714 у каждого) |
| A | матрица `[column-text-keyword]` … `[constant-f-string]` | `8 failed, 20 passed` | «наименование колонки не опознано» |
| B-ref | `test_a_literal_write_form_is_a_write[to-thread-ordered-values-starred-comprehension]` | `2 failed` | «дала 0 находок вместо одной: []» |
| B-index | `…[unbound-from-select]` | `4 failed` | «дала 0 находок вместо одной: []» |
| B-receiver | `…[bound-alias-descriptor-set]` | `5 failed, 6 passed` | «дала 0 находок вместо одной: []» |
| D | матрица `[column-starred]` | `8 failed` | «наименование колонки не опознано» |
| E | `…[methodcaller-import-alias]` | `3 failed, 3 passed` | «дала 0 находок вместо одной: []» |

REFACTOR-коммитов нет: правок без смены поведения не потребовалось.

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py`: предикат, таблицы, матрица, строки, шапка (+1233 / −60 строк).

## Самопроверка исполнителя (задача 3; урок 16-12 и 16-17; О-10 (а))

Скрипт `selfcheck.py` лежит в scratchpad и в репозиторий не коммитится. Он подаёт `phone_write_offences(…, "scripts/x.py")` и требует ровно одну находку ожидаемого вида, предмет которой называет вызов и колонку.

- **Ось A, «как названа колонка».** Все `COLUMN_NAMINGS` и наименования сверх них: `.prop.key`, `__mapper__.c.phone`, `inspect(M).attrs.phone.key`, `aliased(M).phone`, `__table__.columns["phone"]`, `.get("phone")`, `get_property("phone").key`, `column(text=…)`, `column(*[…])`, `column(**{…})`, `"pho" + "ne"`, `f"phone"`, `models.MessengerAccount.phone`, `.comparator.key` и другие. Каждое — в ПОЛНОМ кресте контекстов (2114): 10 контекстов отображения × 5 форм; 50 контекстов строк (каждая строка `JUDGED_PARAMETERS` вида строк × 4 формы связывания, `run_sync` позицией и `fn=`) × 8 контейнеров × 5 форм строки; пары; имя атрибута (5 строк `JUDGED_PARAMETERS` × 4 связывания); `from_select` (4 связывания × 6 форм перечня).
- **Ось B, «как назван API».** Прямое имя, `getattr`-строка, `run_sync`, `partial(…)(…)`, `to_thread`, `run_in_executor`, `partial` внутри `run_in_executor`, псевдоним `partial`, `methodcaller(…)(obj)`, псевдоним ввоза или связанного атрибута, цепочка `Y = X`, присваивание имени, псевдоним атрибута модуля или класса, вызов через атрибут модуля или класса; на заходе 2 добавлены псевдонимы `methodcaller` (ввоз и присваивание) и `getattr`. Формы поданы для каждого базового контекста (666 контекстов матрицы без `run_sync` и 8 контекстов дескриптора, `__init__`, COPY и именованных колонок) и пяти наименований.
- **Отдельно — имена, вычисленные вызовом.** `"PHONE".lower()`, `"{}".format("phone")`, `"".join([…])`, `str("phone")` — 8 456 форм, ни одна не поймана. Это граница (2) с причиной «предикат вызовов не исполняет», так и названная в шапке.

| Заход | HEAD, время (UTC) | Форм подано | `[]` / не та находка под заявлением | Кратных | Закрыто коммитами |
|-------|-------------------|-------------|--------------------------------------|---------|-------------------|
| 1 | `9f50ed19`, 2026-10-13 10:25 | 151 272 (A: 51 × 2114 = 107 814; B: 43 458) + 8 456 вызовных | A: 16 912 (8 наименований: `column(text=)`, `literal_column(text=)`, `t.c.get`, `columns.get`, `get_property(…).key` ×2, `"pho" + "ne"`, `f"phone"`); B: 252 — B-ref 120 (`*[(…) for …]` за ссылкой у `ordered_values`), B-index 124 (`Insert.from_select(stmt, …)`, `Connection.copy_*_to_table(conn, …)` и их псевдонимы атрибута класса), B-receiver 8 (`__set__` / `__init__` за псевдонимом атрибута, `methodcaller(…)(obj)`, `InstrumentedAttribute.__set__`); ещё 44 — артефакт проверяющего, а не промах | 0 | `9847fd01`/`878b4679`, `37ec629e`/`dbe22dcc`, `755c2351`/`a973ea55`, `9fe17694`/`ddbb33f7` |
| 2 | `ddbb33f7`, 2026-10-13 ≈10:36 | 197 224 (A: 68 × 2114 = 143 752; B: 53 472) + 8 456 | A: 8 456 (4 наименования: `column(*["phone"])`, `column(**{"text": …})`, `t.c.get(key=…)`, `get_property(key=…).key`); B: 10 014 — только формы с псевдонимом `methodcaller` / `getattr` | 0 | `1a613249`/`a4c49b66`, `764751d7`/`80153e32` |
| 3 (итог) | `80153e32`, 2026-10-13 10:43 | 205 680 (A: 72 × 2114 = 152 208; B: 53 472) + 8 456 | **0** | **0** | — |

Пояснение к 44 формам захода 1: псевдоним модели (`zz = MessengerAccount; zz(**{…})`) даёт ровно одну находку вида `KIND_KEYWORD`, но предмет называет псевдоним, как в прежней строке `model-attribute-alias`. Проверяющий требовал имя `MessengerAccount` в предмете; на заходе 2 он исправлен.

**Замер записи** (SQLite в памяти, отдельная модель, SQLAlchemy 2.0.46, `writeprobe.py`). Каждая из 13 форм записала колонку (`+7NEW` / `+7SEL`): `values({M.phone.expression: v})`, `{M.phone.property.key: v}`, `{M.phone.property.columns[0]: v}`, `{t.c.get("phone"): v}`, `{t.c.get(key="phone"): v}`, `{column(text="phone"): v}`, `{literal_column(**{"text": "phone"}): v}`, `{"pho" + "ne": v}`, `bulk_update_mappings(M, [{inspect(M).get_property("phone").key: v}])`, `InstrumentedAttribute.__set__(M.phone, a, v)`, `methodcaller("__set__", a, v)(M.phone)`, вызов псевдонима `M.phone.__set__`, `Insert.from_select(insert(M), [...], sel)`. Не-записей среди найденных форм нет, пункт (5) не менялся.

## Decisions Made

- Заявление шапки прежнее (О-10 (а)). Вариант (б) не реализован, запреты 16-09 №2, 16-12 №2, 16-17 №2 и запрет №2 этого плана не нарушены: каждая форма под заявлением, найденная самопроверкой, закрыта предикатом.
- Матрица в суите — 714 контекстов: строки поданы «каждый контейнер со словарём» и «каждая форма строки в списке». Полный крест (2114) гоняет самопроверка; на нём ноль промахов.
- Вызов над строкой как имя колонки — граница (2). Склейка констант и f-строка без подстановок — ловятся, как у SQL в виде 5.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающая строгость] Самопроверка нашла шесть классов форм под заявлением, не пойманных предикатом задач 1–3**
- **Found during:** обязательная самопроверка задачи 3, заходы 1–2.
- **Issue / Fix:** классы A, B-ref, B-index, B-receiver, D и E (таблица выше), каждый — свой цикл `test(16-22)` / `feat(16-22)`. Добавлены 12 строк `COLUMN_NAMINGS`, 26 строк `LITERAL_FORM_CASES` и 10 строк `LEGITIMATE_CASES`. Новые помощники: `COLUMN_LOOKUP_METHODS`, `COLUMN_NAME_KEYWORDS`, `_constant_text`, `_forwarded_arguments`, `_api_alias_targets`, `IDENTIFICATION_CARRIERS`, `_rename_aliases`.
- **Verification:** заход 3 — 205 680 форм, 0 промахов, 0 кратных; модуль гейта 412 passed.

**2. [Rule 1 — дефект собственного черновика] Контекст `run_sync(M, rows, fn=ref)` неисполним**
- **Found during:** задача 3, пробный прогон матрицы до RED.
- **Issue:** `run_sync(MessengerAccount, rows, fn=Session.bulk_update_mappings)` падает `TypeError: got multiple values for argument 'fn'` (замер 16-17). Значит, это не запись, а не слепота предиката.
- **Fix:** контекст заменён исполнимой формой `run_sync(fn=Session.bulk_update_mappings, mapper=MessengerAccount, mappings=ROWS)`.

**3. [Rule 1 — предмет находки] У имени-склейки предмет не называл колонку**
- **Found during:** GREEN класса A.
- **Issue / Fix:** `set_attribute(…, 'pho' + 'ne', …)` теперь показывается как `set_attribute(…, 'phone', …)`: для строкового выражения предмет показывает колонку, как уже делал `_mapping_key_text`.

**4. [Расширение, не нарушение] Числа строк выше порогов плана**
- `COLUMN_NAMINGS` — 32 (план ≥ 16). На задаче 3 сверх перечня добавлены `string-is-manual`, `model-attribute-is-manual`, `module-column`, `property-columns-index`, остальные 12 — самопроверкой. Поэтому RED задачи 3 — 3 failed: критерий требовал N ≥ 2.
- Выборки `-k` задач: 222, 222, 255 (пороги 171, 184, 206).
- Критерии `OK 113 56` и `OK 123 59` измерены на своих задачах. Итог: 152 строки форм (105 + 47), 68 законных (53 + 15).

**5. [Процесс] Сообщение RED-коммита `37ec629e` называет «140 self-check forms»** — это оценка до подсчёта. Замер: класс B-ref — 120 форм захода 1. Коммиты не переписываются; число здесь — замеренное.

---

**Total deviations:** 5 (Rule 2 — 1, Rule 1 — 2, расширение — 1, процесс — 1).
**Impact on plan:** гейт строже буквы плана на шесть классов форм. Реестр, 105 прежних строк форм, 53 законные, сторож сигнатур и матрица связываний 32 × 4 не ослаблены; `JUDGED_PARAMETERS` — прежние 34 строки.

## Issues Encountered

- Время модуля гейта выросло с 2,4 с до ≈13 с: матрица 32 × 714 ≈ 22,8 тыс. форм, ≈10 с.
- Песочница worktree отказывала составным командам с `git` и переменными в путях; команды разбиты на простые, обхода не было.

## Gates (финальное дерево `80153e32`, под общим замком)

| Гейт | Итог | База |
|------|------|------|
| `tests/test_application/test_phone_single_writer_gate.py` | 412 passed | 316 |
| `-k "attribute_keys or literal_write_form or phone_mention or live_tree"` | 222 passed (≥ 171) | — |
| `-k "aliased_writer_api or literal_write_form or phone_mention or live_tree"` | 222 passed (≥ 184) | — |
| `-k "column_naming or … or assignment_inside_the_writer"` | 255 passed (≥ 206) | — |
| третья команда задачи 3 (писатель, реестр, живое дерево) | `OK 6 104` | — |
| quick-run фазы (7 путей) | 952 passed | 856 |
| `tests/test_application` | 697 passed | 601 |
| сквозные гейты чтения исходников (htmx-пары, htmx-гейты, шаблоны, declared invariants) | 576 passed (2 мин 37 с) | 576 |
| `python -m compileall -q app main.py tests` | exit 0 | 0 |
| `scripts/prohibitions_census.py --check` | exit 0, реестр 802 строки, биекция | 0 |
| `tests/test_planning` | гоняется после коммита сводки (в итоговом сообщении) | 218 passed, 2 skipped |

**Подстановки.** Полный `just test` (≈45 мин) не гонялся: его гоняет пост-мердж гейт оркестратора на объединённом дереве волны. `graphify update .` не гонялся: в worktree нет `graphify-out/`, граф обновляет оркестратор после слияния. Волна-сосед 16-21 правит докстринг и пробелы в `app/services/phone.py`. Докстринги исключены из судимых узлов, комментариев в AST нет, поэтому его правка находкой стать не может; на объединённом дереве это проверит прогон оркестратора.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Гэп 2 четвёртой верификации (истина 18, WR-12) закрыт предикатом и правилом-матрицей. Шапка обещает ровно то, что видит предикат; формы вне охвата — пункты (1)–(5) с правдивой причиной.
- Для 16-25 (диспозиция WR-12): решение — предикат, заявление прежнее, О-10 (а).
- `deferred-items.md` не создавался; отложенного нет. Реальных записей номера вне писателя в `app/` + `scripts/` нет.

## Self-Check: PASSED

- `tests/test_application/test_phone_single_writer_gate.py` — FOUND; все 18 коммитов `c3942090` … `80153e32` — FOUND (предки HEAD, `git log 99002b16..HEAD`).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-13*

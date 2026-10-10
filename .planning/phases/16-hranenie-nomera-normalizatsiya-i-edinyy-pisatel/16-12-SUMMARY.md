---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 12
subsystem: testing
tags: [ast-gate, single-writer, phone, sqlalchemy, raw-sql, tdd, gap-closure, wr-08]

requires:
  - phase: 16-09
    provides: "tests/test_application/test_phone_single_writer_gate.py — writer_sources(root), phone_write_offences / judged_offences, tree_offences, _literal_mappings, KIND_ROW_MAPPING / KIND_UPSERT_SET, LITERAL_FORM_CASES, реестр PHONE_WRITER_EXCEPTIONS"
provides:
  - "Гейт писателя: грамматика литерального контейнера `_literal_mappings` (список/кортеж/набор, comprehension и генератор, `|`/`+`, условное выражение, `*`, `:=`, обёртки `list(…)`, `{**{…}}`, `dict({…})`, `dict(**{…})`) и та же грамматика для перечней пар (`_pair_candidates`)"
  - "Гейт писателя: `parameters=` и Alembic `op.bulk_insert` в строках executemany; восьмой вид KIND_POSITIONAL_COLUMN («колонка позицией» — `ordered_values`, `from_select`); `__setattr__` / `set_attribute`; устаревший `Query.update({…})`; MySQL `on_duplicate_key_update`; псевдонимы модели в модуле (`_module_model_aliases`); колонка как `table.c[\"phone\"]` / `getattr(X, \"phone\")`"
  - "Гейт писателя: сырой SQL по механизму — `SET` с кавычками (`\"…\"`, `` `…` ``, `[…]`), строчный конструктор `SET (…) =`, голова `INSERT [OR …] / IGNORE / REPLACE / UPSERT / MERGE INTO` перед таблицей с кавычками и схемой, загрузка `COPY … FROM` / `LOAD DATA … INTO TABLE`, склейка `+` констант (`_folded_string`), asyncpg `copy_records_to_table` / `copy_to_table` (ROW_COPY_CALL_NAMES)"
  - "Шапка гейта: восемь видов, граница через механизм с пятью недостижимыми формами и причинами, летопись WR-01 / WR-08"
affects: [phase 18 manual form, phase 19 capture on connect, phase 20 backfill]

actuals:
  tokens: 13554     # chars/4 над добавленными строками реализованного диффа (54214 символа), шкала estimate
  tasks: 3
  commits: 8        # git rev-list --count plan_head_before..plan_head_after (до коммита этой сводки)
plan_head_before: 625bcec58ed2aaad13cad29b7382d281b6d7dd6e
plan_head_after: e168d3dd22eb94fcd5f3de24c4f190be22182bc3

tech-stack:
  added: []
  patterns:
    - "Литеральный контейнер разбирается ГРАММАТИКОЙ, а не перечнем выражений: один помощник для отображений (`_literal_mappings`) и один для перечней пар (`_pair_candidates`), общий для всех видов"
    - "Пишущий SQL судится по механизму записи (присваивание в SET, голова пишущего оператора перед таблицей, загрузка), а не по одной форме строки"
    - "Колонка, названная литералом, — один предикат `_phone_column` (строка, атрибут, индекс `c[…]`, `getattr` с константой) для ключей, пар и перечней колонок"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Сверх 35 строк плана добавлено 16 строк LITERAL_FORM_CASES и 4 строки LEGITIMATE_CASES: формы, подпадающие под новое заявление шапки через механизм, которые иначе снова сделали бы её шире предиката (третий повтор WR-01/WR-08). Каждая прошла свой RED"
  - "Строка плана `raw-sql-merge-into` (ветка `WHEN MATCHED THEN UPDATE SET phone =`) ловилась и прежним шаблоном — замер планирования «каждая дала []» для неё неверен; добавлена строка `raw-sql-merge-insert-branch` (ветка вставки), которая на прежнем шаблоне действительно давала []"
  - "Перечни пар (`ordered_values(*[…])`, `on_duplicate_key_update([… for …])`, `dict([…])`) разбираются той же грамматикой контейнера, что отображения, — иначе заявление «в его аргументе-контейнере» было бы неверно для видов 7 и 8"
  - "Реестр не тронут: PHONE_WRITER_EXCEPTIONS — ровно app/application/accounts/phone.py; на живом дереве 0 судимых находок, в модуле-писателе прежние 6 сырых записей"

patterns-established:
  - "Перед закрытием плана, расширяющего заявление шапки, исполнитель гоняет собственный перебор форм под новым механизмом и закрывает найденное RED/GREEN-циклом, а не сужением шапки"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Скрипт дозаполнения с `conn.execute(update(MessengerAccount), parameters=[{… \"phone\": n} for a, n in rows])` в синтетическом scripts/ находится обходом writer_sources(root) и краснит гейт с файлом, строкой 2 и видом «ключ словаря строк»"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_parameters_and_a_comprehension_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Девять форм WR-08 и формы тех же семейств (51 новая строка LITERAL_FORM_CASES, всего 60) — ровно одна находка ожидаемого вида каждая; подложенный сырой SQL с кавычками и схемой в synthetic app/ краснит гейт; пара ordered_values — вид «колонка позицией»"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (60 параметров)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_raw_sql_write_with_quoted_identifiers_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_an_ordered_values_pair_of_a_phone_column_is_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "Законные места не краснят (33 строки LEGITIMATE_CASES, из них 17 новых: фильтры, выгрузка COPY … TO, другие таблицы и колонки, псевдоним другой модели, __setattr__ другого атрибута); живое дерево app/ + scripts/ (104 файла) — 0 судимых находок; реестр — ровно модуль-писатель; присваивание в писателе по-прежнему краснит"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write (33 параметра)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_exception_registry_names_only_the_writer_module"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_control_an_assignment_inside_the_writer_module_still_reddens"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта называет границу через механизм и пять недостижимых форм с причиной; прежнее заявление «Всё, что видно литералом в исходнике, ловится» осталось только цитатой в летописи (WR-01, WR-08). Правдивость прозы относительно предиката тестом не утверждается"
    requirement: PHONE-02
    verification: []
    human_judgment: true
    rationale: "Соответствие прозы шапки поведению предиката (запрет 16-09 №2 и запрет 16-12 №2, judgment-tier, flagged-unverified) — суждение верификатора, а не утверждение теста"

duration: 29min
completed: 2026-10-10
status: complete
---

# Phase 16 Plan 12: Гейт единственного писателя видит то, что обещает шапка (WR-08) Summary

**Предикат гейта писателя разбирает литеральный контейнер грамматикой (comprehension, генератор, слияние, `*`, `:=`, вложенные `dict`), судит `parameters=`, `op.bulk_insert`, `ordered_values` / `from_select`, `__setattr__`, `Query.update`, MySQL upsert и псевдонимы модели, ловит пишущий SQL по механизму (кавычки трёх видов, схема, `INSERT OR`/`REPLACE`/`MERGE`/`UPSERT`, `COPY … FROM`, `LOAD DATA`, склейка, asyncpg COPY); шапка заявляет охват через механизм, а не «всё»**

## Performance

- **Duration:** 29 min
- **Started:** 2026-10-10T05:18:58Z
- **Completed:** 2026-10-10T05:48:20Z
- **Tasks:** 3 (плюс один дополнительный RED/GREEN-цикл самопроверки)
- **Files modified:** 1

## Accomplishments

- Естественная форма скрипта дозаполнения Фазы 20 — строки в comprehension под `parameters=` — краснит гейт с файлом, строкой и видом, найденная тем же обходом, что и живое дерево.
- Все девять форм верификатора (WR-08) и формы тех же семейств — 51 новая строка `LITERAL_FORM_CASES` (план: 35), каждая ровно одна находка ожидаемого вида.
- 17 новых законных строк (план: 13) без находок; живое дерево — 0 судимых находок, реестр прежний.
- Шапка: восемь видов, «цена строгости» для `dict.update({...})` и псевдонимов по всему модулю, граница через механизм с пятью недостижимыми формами и их причинами, летопись WR-01 / WR-08.

## Task Commits

1. **Задача 1 (трасер): `parameters=`, `op.bulk_insert`, грамматика контейнера**
   - RED `9c186b8b` — `test(16-12): add failing tracer for executemany rows in a comprehension under parameters=`
   - GREEN `f10abdd7` — `feat(16-12): judge executemany rows under parameters= and in literal-container grammar`
2. **Задача 2: сырой SQL по механизму**
   - RED `7547e62a` — `test(16-12): add failing rule for raw SQL with quoted identifiers and schema prefix`
   - GREEN `2ccdb4d2` — `feat(16-12): judge raw SQL phone writes by mechanism, with quotes, schema and folding`
3. **Задача 3: колонка позицией, запись по имени, `Query.update`, MySQL upsert, псевдонимы; шапка**
   - RED `98b12d00` — `test(16-12): add failing rule for an ordered_values pair of a phone column`
   - GREEN `6c862686` — `feat(16-12): judge positional columns, named-attribute dunders, legacy and MySQL upserts, model aliases`
4. **Самопроверка исполнителя (отклонение 2): формы под механизмом, которые предикат задачи 3 не ловил**
   - RED `986bb2ba` — `test(16-12): add failing rows for mechanism-covered forms found by executor self-probe`
   - GREEN `e168d3dd` — `feat(16-12): follow the container grammar for pair lists and name more literal column forms`

**Plan metadata:** коммит этой сводки (`docs(16-12): …`).

## TDD Gate Compliance

Четыре цикла, у каждого `test(16-12)` предшествует `feat(16-12)`; REFACTOR-коммитов нет (чистка не понадобилась).

| Цикл | Цель RED | `FAILED …::<цель>` | Итог | Причинный литерал | Классификатор |
|------|----------|--------------------|------|-------------------|---------------|
| 1 | `test_a_planted_backfill_with_parameters_and_a_comprehension_reddens_the_gate` | есть | `1 failed, 60 deselected` | «строки executemany в comprehension под parameters= не найдены» | `RED_EVIDENCE_OK` (`target_test_failed`, JUnit) |
| 2 | `test_a_raw_sql_write_with_quoted_identifiers_reddens_the_gate` | есть | `1 failed, 80 deselected` | «сырой SQL с кавычками и схемой не найден» | `RED_EVIDENCE_OK` |
| 3 | `test_an_ordered_values_pair_of_a_phone_column_is_a_write` | есть | `1 failed, 104 deselected` | «пара ordered_values с колонкой номера не найдена» | `RED_EVIDENCE_OK` |
| 4 | `test_a_literal_write_form_is_a_write[ordered-values-starred-pairs]` | есть | `1 failed, 118 deselected` | «литеральная форма записи `ordered_values(… phone …)` дала 0 находок вместо одной» | `RED_EVIDENCE_OK` |

**Семантическая оценка RED.** Во всех четырёх циклах цель исполнилась и упала на запланированном утверждении — предикат вернул `[]` (`AssertionError: … []`); ошибок сбора, импорта, фикстур и посторонних падений нет. Во всех RED-прогонах всего файла прежние правила зелены: 49 / 69 / 86 / 109 passed при 12 / 12 / 19 / 10 failed — падают только новые цель и строки. Улики (`--junit-xml`, записи `{command, exitCode, targetTest, output}`) лежат в gitignored `.pytest_cache/gsd-red/t1…t4.*` worktree и не коммитились.

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py` — предикат, константы (`KIND_POSITIONAL_COLUMN`, `POSITIONAL_COLUMN_CALL_NAMES`, `LITERAL_CONTAINER_WRAPPERS`, `ROW_COPY_CALL_NAMES`, `MODEL_NAME`, расширенные `ROW_MAPPING_KEYWORDS`, `ROW_MAPPING_CALL_NAMES`, `NAMED_ATTRIBUTE_WRITERS`, `UPSERT_CALL_NAMES`, `RAW_SQL_PHONE_WRITE`), помощники (`_folded_string`, `_is_concatenation`, `_positional_phone_columns`, `_module_model_aliases`, `_phone_column`, `_pair_candidates`, `_phone_pairs`, `_phone_pairs_among`; переписанный `_literal_mappings`), три новых правила, 51 новая строка `LITERAL_FORM_CASES`, 17 новых `LEGITIMATE_CASES`, шапка. Тестов в файле: 48 → 119.

## Decisions Made

- Шапка формулирует охват через механизм: «колонка номера — или таблица аккаунтов во вставке, загрузке и слиянии — названа литералом в самом пишущем вызове, в его аргументе-контейнере (грамматика `_literal_mappings`) или в строковой константе SQL (и в склейке `+` констант)». Вне охвата пять форм с причиной: (1) значение, пришедшее именем или результатом другого вызова (поток данных); (2) имя колонки или SQL, вычисленные во время исполнения; (3) вставка позиционным кортежем без имён колонок; (4) пишущий API без имени или под псевдонимом из другого модуля; (5) `__dict__` / `vars()` — не запись в колонку.
- Склейка `+` судится один раз на внешнем свёртываемом узле и только если ни одна её константа не совпала сама.
- Псевдоним модели — по всему модулю без учёта областей видимости, с цепочкой `Y = X`; цена названа в шапке.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — неверный замер планирования] Строка `raw-sql-merge-into` зелена и на прежнем шаблоне**
- **Found during:** задача 2 (RED).
- **Issue:** текст строки содержит `WHEN MATCHED THEN UPDATE SET phone = s.phone`, а прежняя альтернатива `UPDATE … SET … phone =` его уже ловила; замер планирования «каждая из 26 форм дала []» для этой строки неверен.
- **Fix:** строка плана оставлена дословно; добавлена `raw-sql-merge-insert-branch` (`WHEN NOT MATCHED THEN INSERT (id, phone) …`), которая на прежнем шаблоне давала `[]` и ловится только головой `MERGE INTO <таблица аккаунтов>`.
- **Committed in:** `7547e62a` (RED), `2ccdb4d2` (GREEN).

**2. [Rule 2 — недостающая строгость] Формы под механизмом новой шапки, не пойманные предикатом плана**
- **Found during:** после задачи 3 GREEN — собственный перебор исполнителя (21 форма) и разбор грамматики при задаче 3.
- **Issue:** новое заявление шапки было бы неверно для: `{**{"phone": x}}`, `dict(**{…})`, `dict({…})`, `dict([("phone", x)])`, `rows := [...]` (найдены при задаче 3, вошли в её RED/GREEN); `ordered_values(*[…])`, `on_duplicate_key_update([… for …])`, `dict([… for …])`, ключи `table.c["phone"]` и `getattr(X, "phone")`, идентификаторы SQL в обратных кавычках и квадратных скобках (их принимает SQLite, на которой гоняется суита), `LOAD DATA … INTO TABLE` (найдены перебором после задачи 3, отдельный RED/GREEN-цикл). Оставить их значило бы в третий раз назвать границу шире предиката.
- **Fix:** грамматика `_literal_mappings` расширена вложенными отображениями и `:=`; новая `_pair_candidates` даёт перечням пар ту же грамматику контейнера; `_phone_column` узнаёт индекс и `getattr`; `RAW_SQL_PHONE_WRITE` — класс кавычек `_SQL_QUOTE` и загрузка `LOAD DATA`. 15 строк `LITERAL_FORM_CASES` и 4 законные строки; каждая форма прошла RED.
- **Verification:** все 21 форма перебора — ровно одна находка; живое дерево — 0 судимых находок, 6 сырых в писателе.
- **Committed in:** `98b12d00` / `6c862686` (первые 5), `986bb2ba` / `e168d3dd` (остальные 10).

**3. [Rule 3 — процесс] Отбор `-k` законных строк — по `phone_mention`**
- **Issue:** песочница worktree отказывает командам с подстрокой `git` («le**git**imate»), как в 16-09.
- **Fix:** наборы плана уже выбирали законные строки по `phone_mention`; отклонения в командах нет, фиксация для полноты.

---

**Total deviations:** 3 (1 — Rule 1, 1 — Rule 2, 1 — Rule 3 процесс).
**Impact on plan:** гейт строже буквы плана на 16 литеральных форм; реестр, прежние строки находок и прежние правила не тронуты. Счёты `-k` выше порогов плана (39 / 57 / 77) на число добавленных строк: на финальном дереве 95 / 95 / 97 passed.

## Measurements (финальное дерево `e168d3dd`, всё под общим `flock`)

| Прогон | Результат |
|--------|-----------|
| `tests/test_application/test_phone_single_writer_gate.py` | 119 passed |
| `-k` задачи 1 (`backfill_with_parameters or literal_write_form or phone_mention or live_tree`) | 95 passed (порог плана 39) |
| `-k` задачи 2 (`quoted_identifiers or …`) | 95 passed (порог 57) |
| `-k` задачи 3 (`ordered_values_pair or … or registry_names_only or assignment_inside_the_writer`) | 97 passed (порог 77) |
| quick run фазы (`test_phone.py`, `test_account_phone_writer.py`, `test_account_phone_race.py`, гейт писателя, гейт приватности, `test_messenger_account_phone_check.py`, `tests/test_migrations`) | 492 passed |
| оба гейта фазы (`test_phone_privacy_gate.py` + гейт писателя) | 191 passed |
| `tests/test_application` | 397 passed (база 326 + 71 новый тест гейта) |
| сквозные гейты (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`) | 576 passed (как на базе) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 |
| реестр (однострочник критерия задачи 3) | `OK` — ровно `app/application/accounts/phone.py` |
| живое дерево `app/` + `scripts/` (зонд в scratchpad) | 104 файла, 0 судимых находок, 0 сырых вне писателя, 6 сырых в писателе (виды «именованный аргумент» ×5 и «запись атрибута по имени» ×1, строки 112, 159, 174, 177) — как до плана |
| `tests/test_planning` | гоняется после коммита этой сводки; счёт — в ответе оркестратору |

## Substitutions (явно названные)

- **Полную суиту (`just test`, ~45 мин) не гонял** — требование оркестратора; её гоняет гейт после слияния на объединённом дереве (вместе с волной 16-11, 16-13, 16-14).
- **`graphify update .` не запускал** — `graphify-out/` в worktree нет; граф обновляет оркестратор после слияния.
- **Реестр долгов `.planning/WINDOWS.md` не пополнял** — заглушек, пропущенных тестов и неисполненных `<verify>` нет; запись отклонений туда в параллельной волне оркестратор запретил (единственная запись в `.planning/` — эта сводка).
- **`deferred-items.md` не заводил** — по указанию оркестратора; отложенного нет.

## Issues Encountered

None.

## Next Phase Readiness

- Гейт писателя готов к Фазам 18–20: второй писатель в любой литеральной форме executemany, сырого SQL, upsert, записи по имени или позицией краснит суиту с файлом, строкой и видом.
- Оркестратору: перепрогнать расширенный гейт на объединённом дереве волны (16-14 меняет `app/application/accounts/phone.py`; ожидание — 0 судимых находок, реестр прежний).
- Вердикт фазы по-прежнему `gaps_found`; PHONE-02 в REQUIREMENTS.md не отмечался.

## Self-Check: PASSED

- `tests/test_application/test_phone_single_writer_gate.py` — FOUND.
- Коммиты `9c186b8b`, `f10abdd7`, `7547e62a`, `2ccdb4d2`, `98b12d00`, `6c862686`, `986bb2ba`, `e168d3dd` — FOUND (предки HEAD, `git log 625bcec5..HEAD`).
- Критерии приёмки задач 1–3 перепрогнаны на финальном дереве: греп-счёты 1/2/1/1/11, 1/1/14/11, 1/1/2/4/4/13, шапка 15/3/1/1 — все в пределах; реестр `OK`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-10*

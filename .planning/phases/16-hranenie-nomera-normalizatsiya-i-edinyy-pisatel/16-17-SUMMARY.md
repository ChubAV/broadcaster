---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 17
subsystem: testing
tags: [ast, gate, single-writer, sqlalchemy, inspect-signature, run_sync, tdd]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel (16-09, 16-12)
    provides: гейт единственного писателя (`phone_write_offences`, виды 1–8, `_literal_mappings`, `LITERAL_FORM_CASES`, `LEGITIMATE_CASES`, реестр)
provides:
  - опознание пишущего API по ссылке (`run_sync`, `fn=`, `partial(…)(…)`, `to_thread`, `run_in_executor`, `partial(ref)` внутри другого вызова, псевдонимы `partial` в модуле), по `getattr`-строке и `methodcaller`
  - таблица `JUDGED_PARAMETERS` (34 строки) — связывание судимого параметра позицией, именем, `**{…}`, `*[…]`; правило-сторож сигнатур; правило-матрица 32 × 4
  - вид 1 по грамматике (`Attribute` в `Store`), дескриптор `__set__`, повторный `MessengerAccount.__init__`, `column()` / `literal_column()` в ключе, `flag_modified`
  - шапка гейта: граница через механизм, опознание API и связывание; вне охвата — пять пунктов с правдивой причиной и замером; летопись WR-01 → WR-08 → WR-10
affects: [phase-18, phase-19, phase-20, 16-VERIFICATION gap 2, WR-10]

actuals:
  tokens: 28498        # chars/4 над реализованным диффом (113991 символ); весь файл — 162347 символов
  tasks: 3
  commits: 12          # git rev-list --count plan_head_before..plan_head_after (до коммита сводки)
plan_head_before: e9141128e929fca8d4ed3ab7cbe75d743d3c068d
plan_head_after: e53d9320662d24bf079581c8fe08b7db638b13fb

tech-stack:
  added: []
  patterns:
    - "Одна таблица — три потребителя: JUDGED_PARAMETERS питает предикат (_judged_bindings / _bound_arguments), сторож inspect.signature и матрицу связываний"
    - "Синтетический вызов: ссылка на пишущий API разворачивается в ast.Call на месте исходного вызова и судится теми же ветками _judge_call"
    - "Вид 1 по грамматике Python: Attribute в контексте Store, а не перечень операторов присваивания"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "flag_modified(account, \"phone\") — запись (замер: после __dict__-записи пишет x; у устаревшего объекта затёр ручной +7MANUAL значением +70), поэтому он в NAMED_ATTRIBUTE_WRITERS и 34-й строкой JUDGED_PARAMETERS, а не в пункте (5) границы, как предполагал план"
  - "Ключ-конструктор колонки в строках executemany ([{column(\"phone\"): p}]) на SQLite 2.0.46 не пишет (замер), но судится — названо ценой строгости шестого вида"
  - "partial(ref, …), поданный другому вызову и разобранный им как носитель ссылки, сам не судится (множество consumed) — одна находка на запись"
  - "Позиции за распаковкой не-литерала не связываются (_bound_arguments), но литеральные аргументы после неё судятся ветками без позиции — без регресса прежних форм"

patterns-established:
  - "Самопроверка исполнителя перебором: API × способ опознания × контейнер × форма колонки (29 298 форм) плюс второй заход по осям ссылок и псевдонимов (261 форма)"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Скрипт дозаполнения через run_sync(Session.bulk_update_mappings, …) в синтетическом scripts/ краснит гейт; пишущий API опознаётся по ссылке, getattr-строке, methodcaller и partial внутри другого вызова"
    requirement: "PHONE-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_through_run_sync_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (105 строк)"
        status: pass
    human_judgment: false
  - id: D2
    description: "JUDGED_PARAMETERS сверена с установленными сигнатурами; каждая литеральная форма связывания судимого параметра — ровно одна находка"
    requirement: "PHONE-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_judged_parameters_name_the_installed_signatures"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_literal_binding_of_a_judged_parameter_is_judged (128)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_query_update_with_values_as_a_keyword_is_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "Вид 1 по грамматике Store; живое дерево — ноль находок; в писателе — прежние 6 сырых записей; реестр — ровно модуль-писатель; законные формы — без находок"
    requirement: "PHONE-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_phone_attribute_bound_as_a_loop_target_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_exception_registry_names_only_the_writer_module"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write (53 строки)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта заявляет охват через механизм, опознание API и связывание; каждая форма вне охвата названа с правдивой причиной; запреты 16-09 №2 и 16-12 №2 не нарушены"
    requirement: "PHONE-02"
    verification: []
    human_judgment: true
    rationale: "Правдивость прозы шапки относительно предиката — суждение верификатора; машинно закреплены только формы (строки и матрица) и самопроверка исполнителя"

duration: 45min
completed: 2026-10-12
status: complete
---

# Phase 16 Plan 17: Гейт единственного писателя судит API по ссылке и каждый параметр при любом связывании Summary

**Предикат гейта писателя опознаёт пишущий API по ссылке, `getattr`-строке, `methodcaller` и `partial`, судит каждый параметр 34-строчной таблицы `JUDGED_PARAMETERS` (сверена с `inspect.signature`) позицией, именем, `**{…}` и `*[…]` и судит вид 1 по `Store`. Пять форм WR-10 и ещё три класса, найденные самопроверкой (`flag_modified`, `partial` внутри другого вызова, псевдонимы `partial` и модели в модуле), — находки. Живое дерево — ноль, писатель — 6 сырых.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-10-12T18:21:19Z
- **Completed:** 2026-10-12T19:06Z
- **Tasks:** 3 (+ 3 цикла самопроверки)
- **Files modified:** 1

## Accomplishments

- WR-10 закрыт предикатом, а не сужением шапки: все пять форм ревью (`Query.update(values=…)`, `set_attribute(…, key=…)`, `set_committed_value(…, key=…)`, `run_sync(Session.bulk_update_mappings, …)`, `values(**{"phone": n for …})`) — строки `LITERAL_FORM_CASES` с одной находкой ожидаемого вида.
- Класс закрыт перебором: `JUDGED_PARAMETERS` (33 строки планирования + `flag_modified`), правило-сторож сигнатур (имя на индексе, `POSITIONAL_ONLY` ровно у `setattr` / `object.__setattr__`), правило-матрица 32 × 4 = 128 связываний — ноль промахов.
- Исполняющие вызовы `scalar`, `scalars`, `stream`, `stream_scalars`, `exec_driver_sql` и `rows=` Alembic судятся как `execute`; `{"phone": v for …}` — литеральное отображение.
- Вид 1 по грамматике (`for` / `async for` / `with … as` / comprehension); дескриптор `__set__`, повторный `MessengerAccount.__init__`, `column("phone")` / `literal_column(…)` в ключе.
- Шапка: граница через механизм, опознание API, связывание, пять пунктов вне охвата с правдивой причиной и замером не-записей; летопись WR-01 → WR-08 → WR-10.

## Task Commits

1. **Задача 1 (tracer): опознание API по ссылке / getattr / methodcaller** — RED `4aac9144` (test), GREEN `9b074697` (feat). Шлюз трасера (интерактивный режим, `end-of-phase`, verify только `<automated>`): verify перепрогнан — 137 passed, `-k` 112, quick run 577, писатель `OK 6`, живое дерево 0 → расширение.
2. **Задача 2: `JUDGED_PARAMETERS`, связывание, исполняющие вызовы, `DictComp`** — RED `1769a712` (test), GREEN `417229e7` (feat).
3. **Задача 3: вид 1 по `Store`, `__set__`, `__init__`, `column()`; шапка** — RED `6a2c3364` (test), GREEN `282c16d7` (feat).
4. **Самопроверка, класс 1 — `flag_modified`** — RED `70861b52`, GREEN `b7a1e127`.
5. **Самопроверка, класс 2 — `partial(ref)` внутри другого вызова** — RED `ec47679d`, GREEN `e3f46b63`.
6. **Самопроверка, класс 3 — псевдонимы `partial` и модели в модуле** — RED `16f810e1`, GREEN `e53d9320`.

**Plan metadata:** коммит этой сводки (`docs(16-17)`).

## TDD Gate Compliance

| Цикл | RED (`test(16-17)`) | Цель RED | Улика (`check tdd-red-evidence`, JUnit XML) | GREEN (`feat(16-17)`) |
|------|--------------------|----------|---------------------------------------------|-----------------------|
| Задача 1 | `4aac9144` | `test_a_planted_backfill_through_run_sync_reddens_the_gate` | `RED_EVIDENCE_OK`; `FAILED …::test_a_planted_backfill_through_run_sync_reddens_the_gate`, `1 failed, 136 deselected`, литерал «строки bulk_update_mappings, поданные через run_sync, не найдены» | `9b074697` |
| Задача 2 | `1769a712` | `test_a_query_update_with_values_as_a_keyword_is_a_write` | `RED_EVIDENCE_OK`; `FAILED …::test_a_query_update_with_values_as_a_keyword_is_a_write`, `1 failed, 278 deselected`, литерал «Query.update(values=…) с ключом номера не найден» | `417229e7` |
| Задача 3 | `6a2c3364` | `test_a_phone_attribute_bound_as_a_loop_target_is_a_write` | `RED_EVIDENCE_OK`; `FAILED …::test_a_phone_attribute_bound_as_a_loop_target_is_a_write`, `1 failed, 295 deselected`, литерал «цель цикла account.phone не найдена» | `282c16d7` |
| Класс 1 | `70861b52` | `test_a_literal_write_form_is_a_write[flag-modified-phone]` | `RED_EVIDENCE_OK`; `1 failed, 304 deselected`, «дала 0 находок вместо одной: []» | `b7a1e127` |
| Класс 2 | `ec47679d` | `…[to-thread-partial-bulk-update]` | `RED_EVIDENCE_OK`; `1 failed, 310 deselected`, «дала 0 находок вместо одной: []» | `e3f46b63` |
| Класс 3 | `16f810e1` | `…[partial-import-alias-nested]` | `RED_EVIDENCE_OK`; `1 failed, 315 deselected`, «дала 0 находок вместо одной: []» | `e53d9320` |

Семантическая оценка каждой RED: цель исполнялась и упала на запланированном утверждении («гейт вернул `[]`»), а не на сборе, импорте или фикстуре. Форма RED прогона всего файла совпадала с планом: задача 1 — 12 failed (трасер + 11 строк), 6 законных строк зелены; задача 2 — 105 failed (цель, 14 строк, 90 из 124 ячеек матрицы — 34 судились и до плана), сторож сигнатур зелен; задача 3 — 10 failed. Улики — `.pytest_cache/gsd-red/*.json` (gitignored, не коммитятся). REFACTOR-коммитов нет.

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py` — предикат (`_judge_call`, `_referenced_calls`, `_bound_reference`, `_reference_name`, `_getattr_literal`, `_callee_receiver`, `_positional_arguments`, `_named_arguments`, `_bound_arguments`, `_judged_bindings`, `_module_aliases`), константы (`JudgedParameter`, `JUDGED_PARAMETERS`, `REFERENCE_KEYWORDS`, `NAMED_ATTRIBUTE_KEY_KEYWORDS`, `COLUMN_CONSTRUCTORS`, `PARTIAL_NAMES`, `DESCRIPTOR_SET`, `MODEL_INIT`, `KIND_BY_REFERENCE`), правила (трасер `run_sync`, `values=`, сторож сигнатур, матрица, цель цикла), 45 новых строк `LITERAL_FORM_CASES` (60 → 105), 20 новых строк `LEGITIMATE_CASES` (33 → 53), шапка. `_assigned_attributes` удалён (вид 1 — по `Store`).

## Decisions Made

- **Одна таблица — три потребителя** (как в плане): `_judged_bindings(name)` берёт позиции и имена параметров из `JUDGED_PARAMETERS`; сторож и матрица читают ту же таблицу.
- **Ссылка — синтетический вызов**: `_referenced_calls` строит `ast.Call` на месте исходного вызова (`ast.copy_location`), поэтому строка находки настоящая, а ветки `_judge_call` общие. `methodcaller` судится у себя, применённый `partial(…)(…)` — у применения, поглощённый другим вызовом `partial` — у потребителя.
- **Вызов, имя которого само судимо, ссылкой не разбирается** — иначе `execute(values, rows)` дал бы две находки.
- **Имя пишущего API, поданное позицией любому вызову, судится как вызов этого API** (`handler(update, {"phone": x})`) — цена строгости, названа в шапке рядом с `dict.update`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающая строгость] Самопроверка исполнителя: три класса форм под новым заявлением, не пойманные предикатом задач 1–3**
- **Found during:** самопроверка задачи 3 (обязательна по плану; урок 16-12, отклонение 2).
- **Самопроверка, заход 1** (`selfcheck.py` в scratchpad, не коммитится): 23 API (таблица, `values`, `ordered_values`, `on_duplicate_key_update`, конструктор модели, `flag_modified`) × способы опознания (прямо, `getattr`, `run_sync`, `partial(…)(…)`, `w = partial(…)`, `to_thread`, `run_in_executor`, `methodcaller`, и вложенные `to_thread(partial(ref), …)`, `run_sync(partial(ref), …)`, `run_in_executor(None, partial(ref), …)`, `partial(partial(ref), …)()`) × контейнеры (`{…}`, `{… for …}`, `{**{…}}`, `|`, `dict({…})`, условное, `dict(phone=…)`, `dict([(…)])`, `dict(**{…})`; строки — одиночно, список, comprehension, генератор, `list(…)`, `[*[…]]`, `+`) × формы колонки (`"phone"`, `M.phone`, `t.c["phone"]`, `getattr(M, "phone")`, `column("phone")`), плюс 30 целей вида 1 и 14 форм дескриптора / `__init__` — **29 298 форм**. На дереве задачи 3 GREEN: 8 981 промах — `flag_modified` (20) и вложенный `partial(ref)` (8 961); кратных находок 0.
- **Самопроверка, заход 2** (`selfcheck2.py`, 261 форма): `*[ref, …]`, `ref, *[…]`, `**{"fn": ref}`, `to_thread(*(…))`, именованный исполнитель `run_in_executor(pool, …)`, псевдонимы `partial` (ввоз и присваивание), `ft.partial`, `getattr`-ссылка в `run_sync` / `partial`, именованные связывания через ссылку, псевдонимы модели (атрибутом, цепочкой, `AnnAssign`, ссылкой, `__init__`, `__set__`), `methodcaller` для `__setattr__` / `values` / `update(values=…)`, лямбда и вложенная функция в `run_sync`, `bulk_save_objects` / `merge` / `add_all`, `super(M, a).__setattr__`, `setattr(*…)`, `**{"key": …}`, `**{"set_": …}`, `**{"table_name": …}`, кортеж у `from_select`. Промахов 31: псевдонимы `partial` во вложенной позиции (28), `Model = models.MessengerAccount` (1) и 2 невыполнимые формы (ниже).
- **Замеры записи** (SQLite в памяти, отдельная модель, SQLAlchemy 2.0.46; `writeprobe.py`, `writeprobe2.py`): пишут — цель `for` / `with` / comprehension, `M.phone.__set__`, `type(a).phone_is_manual.__set__`, `M.__init__(a, phone=…)`, `values({column("phone"): …})`, `values({literal_column(…): …})`, `set_attribute(…, key=…)`, **`flag_modified(a, "phone")` после `__dict__` / `instance_dict` / `vars().update`** и **`flag_modified` на устаревшем объекте (ручной `+7MANUAL` затёрт значением `+70` — гонка D-07)**; не пишут — `del` / `delattr` / `del_attribute` (`KeyError` на flush), `instance_dict(a)[…] = …` и `__dict__` сами по себе, `__dict__` + `flag_dirty`, `set_committed_value` (только зеркало состояния — гейт судит его, как прежде), строки executemany с ключом `column("phone")` (ядро: `StatementError`, ORM: колонка не меняется), `setattr(a, name=…)` (`TypeError`), `run_sync(M, rows, **{"fn": ref})` (`TypeError: got multiple values for argument 'fn'`).
- **Fix:** три цикла RED/GREEN — класс 1 `flag_modified` (`70861b52` / `b7a1e127`: `NAMED_ATTRIBUTE_WRITERS`, 34-я строка таблицы, 3 строки форм, 2 законные); класс 2 вложенный `partial` (`ec47679d` / `e3f46b63`: `_bound_reference`, множество `consumed`, 5 строк форм, 1 законная); класс 3 псевдонимы (`16f810e1` / `e53d9320`: `_module_aliases`, `PARTIAL_NAMES`, 3 строки форм, 2 законные). Пункт (5) границы шапки: `flag_modified` убран из не-записей (план ставил его туда по замеру «колонка не меняется» на свежем объекте) и назван в виде 4.
- **Итог:** заход 1 — 29 298 форм, 0 промахов, 0 кратных; заход 2 — 261 форма, 2 промаха, обе формы невыполнимы (`TypeError`, замер), то есть не запись. Под новым заявлением шапки непойманных форм нет.
- **Files modified:** `tests/test_application/test_phone_single_writer_gate.py`.

**2. [Rule 1 — неверная проза плана] Пункт (5) границы: `flag_modified` — запись, а не «колонка не меняется»**
- Замер планирования верен только для `flag_modified` на свежем объекте без изменений (UPDATE пишет то же значение). С изменением через `__dict__` и на устаревшем объекте колонка меняется. Шапка исправлена в `282c16d7`, гейт — в `b7a1e127` (см. п. 1).

**3. [Следствие п. 1] Критерий приёмки задачи 2 `assert len(rows) == 33` даёт `AssertionError: 34`**
- 34-я строка `JUDGED_PARAMETERS` (`sqlalchemy.orm.attributes.flag_modified`, `key`, индекс 1) добавлена по собственной политике плана («новый пишущий API библиотеки, которого нет в таблице, — повод дописать строку», `<scope_note>` Flagged assumptions) и по истине must_haves «таблица перечисляет каждый судимый параметр». Те же проверки на финальном дереве: 33 строки планирования + `flag_modified` и надмножество вызовов — `OK`; правило-сторож требует ≥ 33 и зелено. Счёт матрицы — 32 × 4 = 128 (план: 31 × 4 = 124).

**4. [Rule 3 — процесс] RED-цели самопроверки выбирались `-k "<id строки>"`**, потому что песочница worktree отказывает команде `flock … pytest "<путь>::<узел>[…]"`. Законные строки — по `phone_mention` (подстрока `git` в «legitimate», как в 16-09 / 16-12).

---

**Total deviations:** 4 (Rule 2 — 1, Rule 1 — 1, следствие с отменённым буквальным критерием — 1, Rule 3 процесс — 1).
**Impact on plan:** гейт строже буквы плана на три класса форм (25 строк / 8 991 форма перебора). Реестр, прежние 60 строк находок, 33 законные строки и прежние правила не тронуты. Пороги `-k` превышены на число добавленных строк.

## Self-check (план, задача 3)

| Заход | Форм подано | `[]` под заявлением найдено | Закрыто коммитами |
|-------|-------------|-----------------------------|-------------------|
| 1 (`selfcheck.py`) | 29 298 | 8 981 (класс 1 — 20, класс 2 — 8 961) | `70861b52` / `b7a1e127`, `ec47679d` / `e3f46b63` |
| 2 (`selfcheck2.py`) | 261 | 29 (класс 3); ещё 2 — невыполнимые формы, не запись | `16f810e1` / `e53d9320` |
| Итог на `e53d9320` | 29 559 | 0 под заявлением (2 невыполнимые, `TypeError`) | — |

## Measurements (финальное дерево `e53d9320`, все pytest под общим `flock`)

| Прогон | Результат |
|--------|-----------|
| `tests/test_application/test_phone_single_writer_gate.py` | 316 passed (база 119) |
| `-k` задачи 1 (`through_run_sync or literal_write_form or phone_mention or live_tree`) | 160 passed (порог 112) |
| `-k` задачи 2 (`values_as_a_keyword or installed_signatures or literal_binding_of_a_judged_parameter or …`) | 289 passed (порог 253) |
| `-k` задачи 3 (`loop_target or … or assignment_to_a_phone_attribute`) | 166 passed (порог 150) |
| однострочник писателя (третья команда задачи 3) | `OK 6` — 5 «именованный аргумент» (`:112`, `:190` ×2, `:193` ×2) и 1 «запись атрибута по имени» (`:175`); реестр — ровно `app/application/accounts/phone.py` |
| однострочник таблицы (задача 2) | `AssertionError: 34` — см. отклонение 3; с учётом 34-й строки — `OK` |
| живое дерево `app/` + `scripts/` (зонд) | 104 файла, 0 судимых находок, 0 сырых вне писателя, 6 сырых в писателе |
| quick run фазы (7 путей) | 756 passed (база 559 + 197 новых тестов гейта) |
| `tests/test_application` | 599 passed (база 402 + 197) |
| сквозные гейты (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`) | 576 passed (как на базе) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 |
| `tests/test_planning` (после коммита сводки `83b2100b`) | 218 passed, 2 skipped (как на базе) |

**Зависимость от текста писателя (для слияния с 16-19):** вердикт «6 сырых в писателе, 0 вне» зависит только от форм ВЫЗОВОВ модуля-писателя: `values(phone=…, phone_is_manual=…)` и `set_committed_value(account, "phone", …)`. Константы, тексты отказов и строки сообщений в счёт не входят, если только строка не содержит пишущий SQL по `RAW_SQL_PHONE_WRITE` (например, `UPDATE messenger_accounts SET phone =`). Новое правило ссылки судило бы имя пишущего API, поданное позицией (`f(update, …)`); в нынешнем писателе таких нет. Правка 16-19 (тексты `ACCOUNT_NOT_IN_SESSION`, `ACCOUNT_WITHOUT_ID_AFTER_FLUSH`) счёт менять не должна. Оркестратор перепроверяет на объединённом дереве.

## Substitutions (явно названные)

- **Полную суиту (`just test`, ~45 мин) не гонял** — требование оркестратора; её гоняет гейт после слияния на объединённом дереве.
- **`graphify update .` не запускал** — `graphify-out/` в worktree нет; граф обновляет оркестратор после слияния.
- **`deferred-items.md` не заводил** — по указанию оркестратора; отложенного нет.
- **Реестр `.planning/WINDOWS.md` не пополнял** — заглушек, пропущенных тестов и неисполненных `<verify>` нет; единственная запись в `.planning/` — эта сводка.
- **STATE.md, ROADMAP.md, REQUIREMENTS.md не трогал**, `requirements.mark-complete` не звал (фаза — `gaps_found`); `requirements-completed` — только в этой сводке.

## Issues Encountered

- Первый GREEN задачи 1 оставил `methodcaller(…)(session)` непойманным: вызов `methodcaller` сам применён, и правило «судить у применения» его пропускало. Исправлено до коммита: `methodcaller` судится у себя.
- Песочница worktree отказывает составным командам с `git`, `sed` с `/` и путям `::узел[…]` под `flock`; команды разбиты, вставка блоков — скриптом `splice.py` в scratchpad.

## Known Stubs

Нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Гэп 2 третьей верификации (WR-10) закрыт предикатом; шапка называет настоящую границу. Перед `/gsd-verify-work` — полный `just test` на объединённом дереве волны (16-16…16-20).
- Для верификатора: отклонение 3 (34 строки вместо 33) — сознательное; D4 (правдивость прозы шапки) — суждение человека/верификатора.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-12*

## Self-Check: PASSED

- FOUND: `tests/test_application/test_phone_single_writer_gate.py`, `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-17-SUMMARY.md`.
- FOUND (на ветке после `e9141128`): `4aac9144`, `9b074697`, `1769a712`, `417229e7`, `6a2c3364`, `282c16d7`, `70861b52`, `b7a1e127`, `ec47679d`, `e3f46b63`, `16f810e1`, `e53d9320`, `83b2100b`.
- Критерии приёмки задач 1–3 перепрогнаны на `e53d9320`: все проходят, кроме буквального `len(rows) == 33` задачи 2 (отклонение 3; 34 строки — сознательно).

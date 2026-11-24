---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 09
subsystem: testing
tags: [ast-gate, single-writer, privacy-gate, phone, structlog, sqlalchemy, tdd, gap-closure]

requires:
  - phase: 16-06
    provides: "tests/test_application/test_phone_single_writer_gate.py — writer_sources(root), phone_write_offences / judged_offences, tree_offences, реестр PHONE_WRITER_EXCEPTIONS"
  - phase: 16-04
    provides: "tests/test_phone_privacy_gate.py — python_sources(root), python_log_calls, _judge_arguments, scan_python_trees, PHONE_LOG_EXCEPTIONS (пуст, потолок 0)"
provides:
  - "Гейт писателя: виды KIND_ROW_MAPPING («ключ словаря строк») и KIND_UPSERT_SET («set_ при конфликте»); `**{…}` в пишущих вызовах → KIND_KEYWORD; `values(dict(phone=…))` → KIND_DICT_KEY"
  - "Гейт писателя: ROW_MAPPING_CALL_NAMES, ROW_MAPPING_KEYWORDS, UPSERT_CALL_NAMES, _literal_mappings, _mapping_phone_keys, _mapping_key_text, LITERAL_FORM_CASES (9 строк), 6 новых строк LEGITIMATE_CASES"
  - "Гейт приватности: CONTEXT_BINDERS (bind_contextvars, bound_contextvars), _is_context_binding; привязка контекста structlog — вызов журнала при любом получателе"
affects: [phase 18 manual form, phase 19 capture on connect, phase 20 backfill, phases 17-20 privacy]

actuals:
  tokens: 4330      # chars/4 над добавленными строками реализованного диффа (17323 символа), шкала estimate
  tasks: 3
  commits: 6        # git rev-list --count plan_head_before..plan_head_after
plan_head_before: 2b9f64bd410a815000fc2cbac595bbbb5f53721b
plan_head_after: 6ed63a95e3e191be4a4e407fbe961eab0aadeab6

tech-stack:
  added: []
  patterns:
    - "Литеральное отображение (`{…}`, `dict(...)`, они же в списке/кортеже) разбирается одним помощником `_literal_mappings` для всех видов записи — values, executemany, upsert, `**`-распаковка"
    - "`execute` судится по ключам строк, а не по первому аргументу: `stmt = update(...); execute(stmt, rows)` не уходит из охвата"
    - "Привязка контекста structlog судится по имени вызова при любом получателе — как `bind`"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Строки executemany судятся и под именованными аргументами `params=` / `mappings=` (не только позиционно) — иначе `execute(stmt, params=[{'phone': p}])`, литерал в исходнике, прошёл бы вопреки новой границе шапки; закреплено строкой `execute-params-keyword`"
  - "Предмет находки для словаря `values` прежний (`values({'phone': …})`), для `dict(...)` — `values(dict(phone=…))`; строки находок прежних видов не изменились"
  - "Формулировка реестра «исключение снимает виды 2–5» заменена на «все виды, кроме присваивания»: видов стало семь, а NEVER_EXEMPT_KINDS прежний"
  - "Реестры не тронуты: PHONE_WRITER_EXCEPTIONS — ровно модуль-писатель; PHONE_LOG_EXCEPTIONS = {}, потолок 0"

patterns-established:
  - "Шапка гейта называет границу и ведёт её летопись: прежняя формулировка и причина её пересмотра (ревью WR-01 / WR-02)"

requirements-completed: [PHONE-02, PHONE-21]

coverage:
  - id: D1
    description: "ORM bulk UPDATE по первичному ключу в синтетическом scripts/ находится обходом writer_sources и краснит гейт писателя с файлом, строкой и видом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_bulk_update_by_primary_key_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Все пять литеральных форм WR-01 (плюс execute(params=[…])) — находки гейта писателя ожидаемого вида; upsert set_ — вид «set_ при конфликте»"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_an_upsert_set_of_a_phone_column_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (9 параметров)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Законные места с ключом phone не краснят (контекст TemplateResponse, select-фильтр в execute, render(**{…}), upsert и bulk над другими колонками, строки execute без номера); живое дерево — ноль, реестр прежний"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write (16 параметров)"
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
    description: "bind_contextvars / bound_contextvars с номером краснят гейт приватности при любом получателе; подложенная привязка в синтетическом app/ находится обходом python_sources"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_context_binding_in_app_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (3 новых параметра)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Живые привязки app/middleware.py и app/worker/tasks.py распознаны как вызовы журнала (app: 213 → 215) и не краснят; phone_set-признак в привязке чист; unbind_contextvars — не журнал; реестр пуст, потолок 0"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half (4 новых параметра)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_exception_registry_stays_under_its_ceiling"
        status: pass
    human_judgment: false

duration: 18min
completed: 2026-10-09
status: complete
---

# Phase 16 Plan 09: Литеральные формы записи и привязка контекста в гейтах фазы — Summary

**Гейт единственного писателя теперь ловит executemany по первичному ключу, `dict(...)`, `**{…}`, `set_` у `on_conflict_do_update` и `bulk_*_mappings` (ревью WR-01). Гейт приватности считает вызовом журнала `bind_contextvars` / `bound_contextvars` при любом получателе (WR-02). Живые деревья по-прежнему дают ноль находок, реестры исключений не менялись.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-09T14:24:56Z
- **Completed:** 2026-10-09T14:42:45Z
- **Tasks:** 3 (три цикла RED → GREEN)
- **Files modified:** 2

## Accomplishments

- **Гейт писателя, вид 6 «ключ словаря строк».** Ключ номера в словаре или `dict(...)` в строках `execute` / `bulk_update_mappings` / `bulk_insert_mappings` — это запись. Строки могут стоять позиционно, прямо или внутри списка/кортежа, а также под `params=` / `mappings=`. Подложенный `scripts/backfill_planted.py` находится тем же обходом `writer_sources(root)`, что и живое дерево. Находка: `scripts/backfill_planted.py:2 — ключ словаря строк — execute([{'phone': …}])`.
- **Гейт писателя, вид 7 «set_ при конфликте».** Добавлены ещё две формы:
  - `**{…}` / `**dict(...)` в `values` / `update` / `insert` / `MessengerAccount` попадает в прежний вид «именованный аргумент»;
  - `values(dict(phone=…))` попадает в прежний вид «ключ словаря values».
  
  Таблица `LITERAL_FORM_CASES` из 9 строк закрепляет каждую форму ревью отдельным случаем. Шесть новых законных строк не краснят.
- **Шапка гейта писателя.**
  - В перечне видов теперь семь пунктов.
  - Добавлен абзац «цена строгости шестого вида»: параметр `:phone` в словаре `execute` при ЧТЕНИИ тоже краснеет.
  - Граница переписана: вне охвата остаются только значения, собранные во время исполнения. Прежняя формулировка сохранена как летопись с причиной (WR-01).
- **Гейт приватности.**
  - `CONTEXT_BINDERS` и `_is_context_binding`: `python_log_calls` теперь отбирает и привязки контекста.
  - Отрицательные контроли: три новых, все краснят.
  - Положительные контроли: четыре новых, ложных срабатываний нет. Живые привязки распознаны (app: 213 → 215 вызовов) и находок не дают.
  - Шапка называет правило и ведёт летопись (WR-02).

## Task Commits

1. **Задача 1 (трасер): executemany по первичному ключу в `scripts/`**
   - `9d7a3be2` test (RED)
   - `a97179ab` feat (GREEN)
2. **Задача 2: остальные литеральные формы WR-01, законные места, шапка**
   - `0129d37c` test (RED)
   - `78495634` feat (GREEN)
3. **Задача 3: привязка контекста structlog в гейте приватности**
   - `aa007112` test (RED)
   - `6ed63a95` feat (GREEN)

REFACTOR-коммитов нет: после GREEN чистить было нечего.

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py`. Шапка (виды 6–7, цена строгости, граница, летопись). Добавлены `ROW_MAPPING_CALL_NAMES`, `ROW_MAPPING_KEYWORDS`, `UPSERT_CALL_NAMES`, `KIND_ROW_MAPPING`, `KIND_UPSERT_SET`, `_literal_mappings`, `_is_dict_call`, `_mapping_phone_keys`, `_mapping_key_text`. `_values_dict_keys` теперь строится на них. Добавлены правила `test_a_planted_bulk_update_by_primary_key_reddens_the_gate`, `test_an_upsert_set_of_a_phone_column_is_a_write`, `test_a_literal_write_form_is_a_write`, таблица `LITERAL_FORM_CASES` и 6 строк `LEGITIMATE_CASES`. Число правил с параметрами выросло с 31 до 48.
- `tests/test_phone_privacy_gate.py`. Шапка (абзац «ЧТО СЧИТАЕТСЯ ВЫЗОВОМ ЖУРНАЛА» и летопись). Добавлены `CONTEXT_BINDERS`, `_is_context_binding`, правило `test_a_planted_context_binding_in_app_reddens_the_gate`, 3 строки `NEGATIVE_CONTROLS` и 4 строки `POSITIVE_CONTROLS`. Число правил выросло с 64 до 72.

## TDD: RED / GREEN

Все три RED-прогона: `uv run pytest <файл> -q -p no:randomly -k <цель> --junit-xml=.pytest_cache/gsd-red/redN.xml` под замком хоста. Каждая запись подана в `check tdd-red-evidence` в виде camelCase `{command, exitCode, targetTest, output=JUnit XML, …}`. Вердикт везде `RED_EVIDENCE_OK` / `target_test_failed`, `format: junit`, `report_errors: []`. Перегонять в TAP не понадобилось. Улики лежат в gitignored `.pytest_cache/gsd-red/` worktree и не коммитились. Сборщик записей — scratchpad `mkred1609.py`.

**RED задачи 1.** Exit 1. Три совпадения:
- `FAILED tests/test_application/test_phone_single_writer_gate.py::test_a_planted_bulk_update_by_primary_key_reddens_the_gate`;
- `1 failed, 31 deselected`;
- `AssertionError: executemany по первичному ключу не найден: … гейт пропустил: []`.

semanticAssessment: цель исполнилась. Утверждение «обход нашёл ровно `scripts/backfill_planted.py`» прошло, а запланированное утверждение о находке упало: у предиката ещё не было шестого вида (в RED добавлена только константа `KIND_ROW_MAPPING`). Ошибок сбора и импорта нет. Весь файл: `1 failed, 31 passed`. **GREEN:** весь файл `32 passed`, отбор задачи — `3 passed`.

**RED задачи 2.** Exit 1. Три совпадения:
- `FAILED tests/test_application/test_phone_single_writer_gate.py::test_an_upsert_set_of_a_phone_column_is_a_write`;
- `1 failed, 47 deselected`;
- `AssertionError: set_ при конфликте с номером не найден: []`.

semanticAssessment: цель упала на первом, запланированном утверждении. В RED добавлена только константа `KIND_UPSERT_SET`, предикат не менялся. Весь файл: `7 failed, 41 passed`, строк ERROR нет. Упали цель и шесть строк `LITERAL_FORM_CASES` для ещё не реализованных форм. Строки вида 6 и все законные строки прошли. **GREEN:** `48 passed`, отбор задачи — `29 passed` (≥ 28).

**RED задачи 3.** Exit 1. Три совпадения:
- `FAILED tests/test_phone_privacy_gate.py::test_a_planted_context_binding_in_app_reddens_the_gate`;
- `1 failed, 71 deselected`;
- `AssertionError: привязка номера к контексту structlog не найдена: гейт обошёл синтетическое дерево (app: файлов 1, вызовов 0, …) … []`.

semanticAssessment: обход нашёл подложенный файл (файлов 1), распознаватель увидел в нём 0 вызовов. Падение то самое, ради которого написана цель. Весь файл: `7 failed, 65 passed`. Упали цель, три отрицательные строки и три положительные строки с `is_log_call=True`. Строка `unbinding-is-not-a-log` прошла. **GREEN:** `72 passed`, отбор задачи — `11 passed` (≥ 11).

## TDD Gate Compliance

| Задача | RED | GREEN | REFACTOR |
|--------|-----|-------|----------|
| 1 | `9d7a3be2` test(16-09) | `a97179ab` feat(16-09) | — |
| 2 | `0129d37c` test(16-09) | `78495634` feat(16-09) | — |
| 3 | `aa007112` test(16-09) | `6ed63a95` feat(16-09) | — |

Нарушений нет. Каждому `feat(16-09)` предшествует свой `test(16-09)`.

## Проверки на конечном дереве (под замком хоста)

| Набор | Результат |
|-------|-----------|
| `<automated>` задачи 1: файл гейта писателя; `-k "bulk_update_by_primary_key or live_tree or registry_names_only"` | 48 passed (на коммите задачи 1: 32); 3 passed |
| `<automated>` задачи 2: файл; `-k "upsert_set or literal_write_form or phone_mention or live_tree or registry_names_only or assignment_inside_the_writer"` | 48 passed; 29 passed |
| `<automated>` задачи 3: `tests/test_phone_privacy_gate.py`; `-k "context_binding or contextvars or binding or live_trees or under_its_ceiling"` | 72 passed; 11 passed |
| `tests/test_application tests/test_phone_privacy_gate.py tests/test_services/test_phone.py` | 500 passed (база 306 + 64 + 105 = 475; прибавка +17 и +8 — новые правила) |
| Сквозные гейты `test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants` | 576 passed (как на базе) |
| Набор фазы из `<verification>` плана (phone, writer, race, оба гейта, CHECK модели, `tests/test_migrations`) | 390 passed |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0, «реестр: 764 строк, биекция с переписью — согласие» |
| `tests/test_planning -q` | после коммита сводки — см. отчёт исполнителя |

**Строка `-s` живого правила приватности.** До: `app: файлов 100, вызовов 213, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 89; находок 0`. После: `app: файлов 100, вызовов 215, …; находок 0`. Прибавка +2 — это две живые привязки: `app/middleware.py` и `app/worker/tasks.py`.

## Обход на двух корнях (только чтение)

Проверка шла скриптом `.pytest_cache/gsd-red/walkproof.py` в gitignored кэше worktree. Он импортирует оба модуля гейтов из worktree и только читает файлы.

| Корень | `writer_sources` | находок писателя | `python_sources` | находок приватности | вызовы по деревьям |
|--------|------------------|------------------|------------------|---------------------|--------------------|
| worktree `/source/broadcaster/.claude/worktrees/agent-a0346854505e1ff96` | 104 | 0 | 106 | 0 | app 215, scripts 68, max_worker 89 |
| основная копия `/source/broadcaster` | 104 | 0 | 106 | 0 | app 215, scripts 68, max_worker 89 |

Наборы файлов на двух корнях совпадают (`identical=True`, разностей нет в обе стороны). Причины две: `__pycache__/` хранит `.pyc`, а не `.py`; `.claude/worktrees/` лежит вне `app/` и `scripts/`.

**Снимок правок соседей по волне (только чтение, на момент проверки).** Скрипт `.pytest_cache/gsd-red/wavemates.py` прогнал расширенные предикаты по изменённым соседями файлам.
- `app/application/accounts/phone.py` 16-08 (`agent-a9d542303fef2d34d`): 6 сырых записей прежних видов (условные `values(phone=…)`, зеркало `set_committed_value`, ручная запись и очистка). Новые виды не срабатывают: проба существования строк с ключом номера не несёт. Судимых находок 0, находок приватности 0.
- `app/services/phone.py` 16-07 (`agent-a0b2bf027f7fa2edb`): записей 0, находок приватности 0.

Это снимок незавершённой работы соседей. Окончательный прогон на объединённом дереве за оркестратором.

## Decisions Made

См. `key-decisions` во фронтматтере. Главное:
- строки executemany судятся и под `params=` / `mappings=`;
- строки находок прежних видов не менялись;
- реестры не тронуты.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающая строгость] `execute(stmt, params=[…])` и `bulk_*_mappings(mapper, mappings=[…])`**
- **Found during:** задача 1 (GREEN), закреплено в задаче 2.
- **Issue:** план судит только ПОЗИЦИОННЫЕ аргументы. Тогда литеральная форма `execute(stmt, params=[{"phone": p}])` осталась бы видна в исходнике и прошла бы молча, а это противоречит новой границе шапки «всё, что видно литералом, ловится» и запрету плана выдавать слепоту за границу.
- **Fix:** константа `ROW_MAPPING_KEYWORDS = {"params", "mappings"}`. Значения этих аргументов судятся так же, как позиционные. В `LITERAL_FORM_CASES` добавлена девятая строка `execute-params-keyword`, поэтому строк 9 при плановых «не меньше 8».
- **Verification:** строка зелёная, живое дерево — ноль находок на обоих корнях.
- **Committed in:** `78495634`.

**2. [Rule 1 — устаревшая проза] «Исключение снимает виды 2–5»**
- **Found during:** задача 1 (GREEN).
- **Issue:** у гейта стало семь видов. Шапка, докстринг `judged_offences`, докстринг и сообщение правила реестра называли диапазон «2–5», и с шестым видом он перестал быть верным. `NEVER_EXEMPT_KINDS` не менялся.
- **Fix:** формулировка «все виды, кроме присваивания». Докстринг `_phone_writes` теперь говорит «видов шапки» вместо «пяти видов».
- **Committed in:** `a97179ab`.

**3. [Rule 3 — процесс] Отбор `-k` задачи 2: `legitimate` заменено на `phone_mention`**
- **Issue:** песочница worktree отказывает командам, где встречается подстрока `git`, а она есть в слове «le**git**imate».
- **Fix:** тот же набор правил выбран по `phone_mention`: правило называется `test_a_legitimate_phone_mention_is_not_a_write`, и других совпадений нет. Счёт `29 passed` совпадает с ожиданием плана (28 плюс строка из отклонения 1).

---

**Total deviations:** 3 (1 — Rule 2, 1 — Rule 1, 1 — Rule 3 процесс).
**Impact on plan:** гейт строже буквы плана на одну литеральную форму. Реестры и прежние строки находок не тронуты.

## Substitutions (явно названные)

- **Полную суиту (`just test`, около 45 мин) не гонял.** Это требование оркестратора: полный прогон делает его гейт после слияния на объединённом дереве.
- **`graphify update .` не запускал.** `graphify-out/` в worktree нет, граф обновляет оркестратор после слияния.
- **Ruff не запускал.** В `.venv` worktree его нет (`Failed to spawn: ruff`). Вместо него — `compileall` (exit 0) и полный прогон обоих файлов.

## Issues Encountered

None.

## Known Stubs

None. Оба файла — модули тестов: заготовок, данных-пустышек и TODO в них нет.

## Threat Flags

None. Изменены только модули тестов, новой поверхности нет. T-16-27, T-16-28 и T-16-29 из `<threat_model>` закрыты, как предписано: виды и строки закреплены, реестры не тронуты, цена строгости названа в шапке.

## User Setup Required

None.

## Next Phase Readiness

- Сквозные гейты фазы видят литеральные формы записи и привязку контекста, поэтому у писателей Фаз 17–20 нет молчаливого обхода через executemany, upsert или `bind_contextvars`.
- Объединённое дерево волны 16-07…16-09 оркестратор должен прогнать обоими гейтами поимённо. Сниженный снимок соседей находок не дал.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-09*

## Self-Check: PASSED

- FOUND: tests/test_application/test_phone_single_writer_gate.py
- FOUND: tests/test_phone_privacy_gate.py
- FOUND: 9d7a3be2, a97179ab, 0129d37c, 78495634, aa007112, 6ed63a95 (предки HEAD)

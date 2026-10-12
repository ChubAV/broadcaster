---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 18
subsystem: testing
tags: [privacy-gate, ast, logging, structlog, PHONE-21, IN-09, tdd]

requires:
  - phase: 16-13
    provides: "ModuleLogNames / module_log_names (неподвижная точка связываний), CONTEXT_BINDERS, LOGGER_FACTORIES, граница IN-06"
provides:
  - "Гейт приватности опознаёт журнал по ввозу (функции `logging`, `root`, фабрика под псевдонимом), по связыванию в модуле (присваивание, аннотированное, `:=`, тело класса через `self.`/`cls.`, второе связывание, кортеж попарно, ссылка на фабрику) и по ссылке на метод опознанного журнала (`getattr`-строка, `partial`, `info = logger.info`, `out = print`)"
  - "Начальные значения фабрики (`get_logger(__name__, phone=…)`, `wrap_logger(base, phone=…)`, `LoggerAdapter(logger, {…})`) судятся, как `bind` (D-11)"
  - "«ГРАНИЦА СРЕДСТВА» называет только формы с правдивой причиной (поток данных, имя во время исполнения, область видимости, рамка D-17); прежний довод — летописью"
affects: [phase-17, phase-18, phase-19, phase-20, privacy-gate]

actuals:
  tokens: 11000
  tasks: 2
  commits: 4
plan_head_before: e9141128e929fca8d4ed3ab7cbe75d743d3c068d
plan_head_after: 5a7cc660b12ba01c8032b9f1dfebb0dad861e758

tech-stack:
  added: []
  patterns:
    - "Доступ к члену унифицирован: `X.name` и `getattr(X, \"name\")` — одно и то же для получателя, метода, привязки и фабрики (`_member`, `_last_name`)"
    - "Связывание классифицируется по значению в порядке «ссылка на фабрику → получатель → вызываемое журнала»; имя в теле класса идёт и в атрибуты"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Сверх буквы плана пойманы формы той же оси (опознание по ввозу, фабрике или связыванию в модуле): `logging.root` и `from logging import root`; классы журнала, созданные напрямую (`Logger`, `RootLogger`, `PrintLogger`, `WriteLogger`, `BytesLogger`, `BoundLogger`); вызываемое журнала, связанное с атрибутом или в теле класса (поле `log_function_attributes`); кортеж попарно; ссылка на фабрику без вызова; фабрика через `getattr`; `builtins.print`. Запрет плана №2 не даёт назвать их в границе вместо поимки"
  - "Начальное значение фабрики — второй позиционный аргумент или именованный вне `FACTORY_CONFIGURATION_KEYWORDS` (`name`, `level`, `file`, `processors`, `wrapper_class`, `context_class`, `cache_logger_on_first_use`, `logger_factory_args`; сигнатуры `logging` 3.12 и structlog 25.5.0); `getLogger(name=\"x\")` вызовом журнала не считается"
  - "`LOG_METHODS` не расширен: низкоуровневое API (`logger._log`, `makeRecord`/`handle`, `logging.makeLogRecord`) названо в границе в разделе «вне списка D-17» вместе с `sys.stdout.write`, `warnings.warn`, `traceback.print_*`, `pprint`, `os.write` и текстом исключения: расширение списка — решение владельца"

patterns-established:
  - "Граница гейта проверяется зондом: каждая названная форма — `[]` и до, и после плана; каждая заявленная в охвате — находка"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Функция `logging`, ввезённая в модуль (и под псевдонимом), — вызов журнала; подложенный файл в синтетическом `app/` краснит гейт; одноимённая функция без ввоза — нет"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_logging_function_import_in_app_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found[logging-function-import|logging-function-import-alias|logging-log-function-import|logging-exception-function-import]"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half[logging-config-import-is-not-a-log|logging-function-presence-flag|info-without-logging-import-is-not-a-log]"
        status: pass
    human_judgment: false
  - id: D2
    description: "Журнал из тела класса через `self.`/`cls.`, `:=`, второе связывание, фабрика под псевдонимом, `getattr`-строка, `LoggerAdapter`/`wrap_logger`, начальные значения фабрики, `partial` и ссылки на методы — находки гейта; законные формы — нет"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_logger_bound_in_a_class_body_is_found_through_self_and_cls"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (68 строк)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half (35 строк)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Живые деревья: прежние 215 / 68 / 89 вызовов и 0 находок; множества распознанных вызовов всех 106 файлов совпадают с базой по строке и столбцу; реестр пуст, потолок 0"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_exception_registry_stays_under_its_ceiling"
        status: pass
    human_judgment: false
  - id: D4
    description: "«ГРАНИЦА СРЕДСТВА» называет только формы с правдивой причиной; прежний довод и пункт `importlib` записаны летописью"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "зонд scratchpad cmp1618/probe.py: 18 форм границы — `[]` до и после плана; 10 форм охвата — находка"
        status: pass
    human_judgment: true
    rationale: "Правдивость прозы шапки (каждая причина верна по сути) — суждение верификатора; зонд доказывает только, что названное действительно не ловится"

duration: 23min
completed: 2026-10-12
status: complete
---

# Phase 16 Plan 18: IN-09 — гейт приватности опознаёт журнал по ввозу, связыванию и ссылке Summary

**Гейт приватности PHONE-21 теперь ловит номер, переданный функции `logging`, ввезённой в модуль (`from logging import info` / `warning as warn_`), журналу из тела класса через `self.lg` / `cls.lg`, журналу, связанному `:=`, вторым связыванием, фабрикой под псевдонимом, обёрткой `LoggerAdapter` / `wrap_logger`, через `getattr`-строку, `functools.partial` или ссылку на метод, а также в начальных значениях фабрики. «ГРАНИЦА СРЕДСТВА» названа заново: в ней остались только формы с правдивой причиной. Живые деревья: прежние 215 / 68 / 89 вызовов и 0 находок.**

## Performance

- **Duration:** 23 min
- **Started:** 2026-10-12T18:21:55Z
- **Completed:** 2026-10-12T18:45Z
- **Tasks:** 2 (два цикла RED/GREEN)
- **Files modified:** 1 (`tests/test_phone_privacy_gate.py`, +750 / −83)

## Accomplishments

- IN-09 (гэп 3 верификации раунда 3) закрыт поимкой, а не называнием. Пять форм ревью краснят гейт, каждая закреплена строкой поимённо: `from logging import info`, `warning as warn_`, `self.lg` и `cls.lg` из тела класса, `:=`.
- Аудит прежней границы: пять пунктов с неверным доводом теперь ловятся (`LoggerAdapter`, `partial`, `getattr`-строка, `a = lg`, фабрика под псевдонимом). Пункт `importlib` убран: такая привязка ловилась всегда, теперь это закреплено строкой `importlib-binder`.
- Начальные значения фабрики судятся, как `bind` (D-11). Фабрика без них вызовом журнала не считается.
- Шапка переписана. Охват разложен на «по ввозу / по связыванию / по ссылке / начальные значения». В границе остались поток данных, имя, вычисленное во время исполнения, область видимости, сторонние журналы, `PHONE`/`phone.txt`, значение без имени `phone`, `wa_bridge/`. Отдельный раздел «вне списка D-17» с причиной «рамка владельца».

## Task Commits

1. **Задача 1 (трасер): функция `logging`, ввезённая в модуль.** RED `b55da91b` (test), GREEN `38727536` (feat).
2. **Задача 2: тело класса, `:=`, второе связывание, псевдоним фабрики, `getattr`, обёртки, начальные значения, `partial`, ссылки; граница.** RED `b33d19e4` (test), GREEN `5a7cc660` (feat).

REFACTOR-коммита нет: чистка не понадобилась.

## TDD Gate Compliance

| Цикл | RED | GREEN | Улика RED |
|------|-----|-------|-----------|
| Задача 1 | `b55da91b` | `38727536` | `FAILED tests/test_phone_privacy_gate.py::test_a_planted_logging_function_import_in_app_reddens_the_gate`; `1 failed, 101 deselected`; литерал «функция журнала, ввезённая из logging, не распознана»; `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`, JUnit, tests 1 / fail 1) |
| Задача 2 | `b33d19e4` | `5a7cc660` | `FAILED tests/test_phone_privacy_gate.py::test_a_logger_bound_in_a_class_body_is_found_through_self_and_cls`; `1 failed, 138 deselected`; литерал «журнал, связанный в теле класса, не распознан через self»; `RED_EVIDENCE_OK` (`target_test_failed`, JUnit, tests 1 / fail 1) |

**Семантическая оценка RED.** Задача 1: цель исполнилась. Обход нашёл ровно подложенный файл (`app: файлов 1, вызовов 0`). Упало планируемое утверждение: находок `[]`, потому что `warn_` из `logging` не распознан. Ошибок сбора, ввоза и фикстур нет. В полном прогоне файла краснели ровно шесть новых строк (трасер, 4 отрицательных, `logging-function-presence-flag`). Задача 2: цель исполнилась. Упало утверждение для `self.lg` (находок `[]`: имя из тела класса лежало только в `receiver_names`). В полном прогоне краснели ровно 28: цель и все 27 новых отрицательных строк. Девять новых положительных строк были зелёными уже на RED, как и должно быть: они сторожат ложные срабатывания. Улики лежат в gitignored `.pytest_cache/gsd-red/` (`t1-red.{xml,out,json}`, `t2-red.{xml,out,json}`) и в репозиторий не внесены.

Две строки добавлены на GREEN, без собственного RED-прогона в коммите:
- `bound-logger-constructed-context`. Её RED показан зондом на версии гейта из `b33d19e4`: `python_log_offences` → `[]`; на GREEN → находка `'phone'`.
- `importlib-binder`. Она закрепляет прежнее поведение и была бы зелёной и до плана, как сказано в её комментарии.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`. Новые константы: `LOGGING_MODULES`, `LOGGING_MODULE_LOGGERS`, `FACTORY_CONFIGURATION_KEYWORDS`, `PARTIAL_NAMES`, `PRINT_MODULES`. `LOGGER_FACTORIES` расширен. Новые поля `ModuleLogNames`: `log_functions`, `factories`, `log_function_attributes`. Новые помощники: `_getattr_literal`, `_member`, `_last_name`, `_is_factory_reference`, `_is_factory_call`, `_log_method_reference`, `_binder_reference`, `_is_print_reference`, `_log_function_reference`, `_is_log_partial`, `_is_log_callable`, `_binding_pairs`, `_bind`, `_is_log_function_call`, `_carries_initial_values`. Переписаны `module_log_names`, `_is_log_receiver`, `_is_log_method_call`, `_is_context_binding`, `_is_print`, `python_log_calls`. Два новых правила. Строк `NEGATIVE_CONTROLS` было 35, стало 68; `POSITIVE_CONTROLS` — было 23, стало 35. Шапка переписана.

## Decisions Made

См. `key-decisions` во frontmatter. Главное: формы той же оси, найденные при работе, пойманы, а не названы в границе. Их можно опознать по ввозу, фабрике или связыванию, и запрет плана №2 не даёт называть их вместо поимки. Рамка D-17 угадыванием не расширена. Это закрепляют строки `info-attribute-after-logging-import-is-not-a-log`, `root-attribute-of-non-logger`, `class-body-non-logger`, `factory-name-keyword-is-not-a-log` и `info-without-logging-import-is-not-a-log`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Формы той же оси, которых не называли ни охват, ни граница**
- **Found during:** задача 2 (проектирование и зонд живого дерева)
- **Issue:** у ряда форм журнал опознаётся по ввозу, фабрике или связыванию в модуле, но новый распознаватель плана их бы пропускал: `logging.root.info(…)`, `from logging import root`, `logging.Logger("x")`, `structlog.PrintLogger()`, `structlog.stdlib.BoundLogger(base, [], {…})`, `self.out = logger.info` → `self.out(…)`, `out = print` в теле класса, `lg, n = logging.getLogger(), 1`, `gl = logging.getLogger` → `gl()`, `getattr(logging, "getLogger")()`, `builtins.print(…)`. Назвать их в границе нельзя (запрет 2 плана), а промолчать значило бы повторить IN-09.
- **Fix:** все они пойманы. Добавлены `LOGGING_MODULE_LOGGERS`, классы журнала в `LOGGER_FACTORIES`, поле `ModuleLogNames.log_function_attributes` (с умолчанием) и `PRINT_MODULES`. Связывание кортежем разбирается попарно, ссылка на фабрику делает имя фабрикой. Каждая форма закреплена отрицательной строкой (12 строк сверх плана, считая `importlib-binder`). Против ложных срабатываний добавлены три положительные строки.
- **Files modified:** `tests/test_phone_privacy_gate.py`
- **Verification:** 141 passed. Живые 215 / 68 / 89 и 0 находок. Множества вызовов всех 106 файлов совпадают с базой `e9141128` по строке и столбцу.
- **Committed in:** `b33d19e4` (строки), `5a7cc660` (распознаватель)

**2. [Rule 2 - Missing Critical] Раздел границы «вне списка D-17» шире буквы плана**
- **Found during:** задача 2 (зонд границы)
- **Issue:** план называет `sys.stdout.write`, `sys.stderr.write`, `warnings.warn`, `traceback.print_*` и текст исключения. Зонд показал, что так же не ловятся `pprint`, `os.write` и низкоуровневые методы журнала `logger._log`, `makeRecord`/`handle`, `logging.makeLogRecord`. Список методов — рамка D-17/D-11.
- **Fix:** все они названы в том же пункте с той же причиной: «рамка владельца, а не слепота предиката».
- **Files modified:** `tests/test_phone_privacy_gate.py`
- **Committed in:** `5a7cc660`

---

**Total deviations:** 2 auto-fixed (оба Rule 2).
**Impact on plan:** охват расширен только внутри оси «опознание по ввозу, фабрике или связыванию». Рамка D-17 не расширена, реестр `{}` и потолок 0 прежние, живое дерево прежнее.

## Issues Encountered

None.

## Gates (final tree `5a7cc660`, under the shared `flock`)

| Gate | Result |
|------|--------|
| `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | 141 passed (база 94, после задачи 1 — 102) |
| `-k "logging_function_import or number_handed_to_a_python_log_call or recommended_form_does_not_redden_the_python_half or live_trees or under_its_ceiling"` (после задачи 1) | 68 passed (порог плана 68) |
| `-k "class_body_is_found or number_handed_to_a_python_log_call or recommended_form_does_not_redden_the_python_half or live_trees or under_its_ceiling"` | 106 passed (порог плана 91; +15 — строки сверх плана) |
| `-s -k live_trees` | `app: файлов 100, вызовов 215, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 89; находок 0` |
| Быстрый прогон фазы (7 путей, `-p no:randomly`) | 606 passed (база 559; 567 после задачи 1) |
| Оба гейта фазы | 260 passed |
| `tests/test_application -q -p no:randomly` | 402 passed (как в базе) |
| Сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (как в базе) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `uv run python scripts/prohibitions_census.py --check` | exit 0, реестр 788 строк, согласие |
| `tests/test_planning -q` | прогоняется после коммита этой сводки, итог — в ответе оркестратору |
| Acceptance greps задач 1 и 2 | все совпали (`LOGGING_MODULES` 1, `log_functions` ≥3, `IN-09` ≥1, 7 и 17/6 id, 4 помощника, `PARTIAL_NAMES` 1, `ast.NamedExpr`/`ast.ClassDef` ≥1, `sys.stdout.write`/`warnings.warn`/«вне списка D-17» ≥1, реестр и потолок прежние) |

**Чем заменены шаги плана в этом прогоне.** Полный `just test` не гонялся: его по указанию оркестратора гоняет пост-мерж-гейт на объединённом дереве. `graphify update .` тоже не гонялся: в worktree нет `graphify-out/`, граф обновит оркестратор после слияния.

**Атрибуция живых чисел для пост-мержа.** Числа 215 / 68 / 89 — это вызовы журнала, распознанные в живых `app/` (100 файлов), `scripts/` (4) и `max_worker/` (2) этого worktree. Измерены на дереве `e9141128` плюс правка одного `tests/test_phone_privacy_gate.py`. Соседи по волне меняют `app/services/phone.py` (16-16) и `app/application/accounts/phone.py` (16-19): оба файла входят в дерево `app`, и любой вызов журнала, добавленный ими, сдвинет число `app`. 16-17 трогает только `tests/`, на эти числа не влияет. Расхождение `app` после слияния надо приписывать 16-16 / 16-19, а не распознавателю: в этом worktree множества вызовов всех 106 файлов совпадают с базой.

## Known Stubs

None.

## Threat Flags

None. Правка только в `tests/`, новых поверхностей нет. T-16-47 и T-16-48 закрыты, как в `<threat_model>`: 33 новые отрицательные строки (4 задачи 1, 17 задачи 2, 12 сверх плана; план требовал 21) и 12 положительных (план требовал 9), подложенный файл в синтетическом `app/`; реестр и потолок прежние.

## Deferred Items

None. `deferred-items.md` в этой параллельной волне не создавался.

## User Setup Required

None. Внешних сервисов нет.

## Next Phase Readiness

- Сквозной гейт приватности готов для Фаз 17–20. Писатель номера, который передаст номер журналу в одной из пойманных форм, получит красный гейт.
- Что гейт по-прежнему не видит, названо в «ГРАНИЦЕ СРЕДСТВА» с причиной, и каждая названная форма проверена зондом: `[]` и до, и после плана.

## Self-Check: PASSED

- FOUND: `tests/test_phone_privacy_gate.py`, `16-18-SUMMARY.md`
- FOUND (ancestors of HEAD): `b55da91b`, `38727536`, `b33d19e4`, `5a7cc660`, `93407329` (коммит сводки)
- Изменены только `tests/test_phone_privacy_gate.py` и эта сводка: STATE.md, ROADMAP.md, REQUIREMENTS.md и реестр запретов не тронуты

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-12*

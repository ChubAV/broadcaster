---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 13
subsystem: testing
tags: [ast-gate, privacy-gate, phone, structlog, logging, celery, tdd, gap-closure]

requires:
  - phase: 16-09
    provides: "tests/test_phone_privacy_gate.py — python_sources(root), python_log_calls, _judge_arguments, scan_python_trees, CONTEXT_BINDERS, _is_context_binding, PHONE_LOG_EXCEPTIONS (пуст, потолок 0)"
provides:
  - "Гейт приватности: ModuleLogNames (binders, receiver_names, receiver_attributes), NO_MODULE_LOG_NAMES, module_log_names(tree) — имена журнала, связанные в модуле ввозом или присваиванием (неподвижная точка)"
  - "CONTEXT_BINDERS += bind_threadlocal, bound_threadlocal, tmp_bind; LOGGER_FACTORIES += get_task_logger"
  - "Необязательный параметр names у _is_log_receiver, _is_log_method_call, _is_context_binding; python_log_calls считает имена модуля один раз"
  - "Правила test_a_planted_aliased_binding_in_app_reddens_the_gate (трасер), test_a_number_handed_to_a_logger_bound_by_assignment_is_found; 13 строк NEGATIVE_CONTROLS, 7 строк POSITIVE_CONTROLS"
  - "Шапка гейта: получатели модуля, цена области видимости «модуль», ГРАНИЦА СРЕДСТВА с семью пунктами IN-06, летопись IN-06"
affects: [phase 17 display, phase 18 manual form, phase 19 capture on connect, phase 20 backfill, phases 17-20 privacy]

actuals:
  tokens: 4280      # chars/4 над изменёнными строками реализованного диффа (17120 символов), шкала estimate
  tasks: 2
  commits: 4        # git rev-list --count plan_head_before..plan_head_after (до коммита SUMMARY)
plan_head_before: 625bcec58ed2aaad13cad29b7382d281b6d7dd6e
plan_head_after: 58550bb3

tech-stack:
  added: []
  patterns:
    - "Имена журнала модуля собираются одним обходом (`module_log_names`) и передаются распознавателям параметром; без параметра распознаватели ведут себя как до плана"
    - "Присваивания разбираются до неподвижной точки: `lg = logging.getLogger()` → `bound = lg.bind(...)` — оба журнала"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Псевдоним ввоза привязки распознаётся только у голого вызова имени (`bind_ctx(...)`): атрибутная форма уже ловится по последнему имени"
  - "Связывания разбираются до неподвижной точки (сверх буквы плана): `lg2 = lg.bind(...)`, где `lg` из фабрики, — тоже журнал; это распознавание привязанного журнала внутри рамки D-17, живые множества вызовов прежние"
  - "Фабрика, ввезённая под псевдонимом (`from logging import getLogger as gl`), не распознаётся и названа в ГРАНИЦЕ СРЕДСТВА: класс ModuleLogNames по плану несёт три поля, а поле фабрик-псевдонимов было бы расширением артефакта"
  - "Реестры не тронуты: PHONE_LOG_EXCEPTIONS = {}, PHONE_LOG_EXCEPTIONS_CEILING = 0"

patterns-established:
  - "Распознавание журнала только по фабрике, имени журнала и ввозу (рамка D-17); всё, что так не опознать, называется в ГРАНИЦЕ СРЕДСТВА, а не ловится догадкой по любому имени"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Привязка номера под псевдонимом ввоза в синтетическом app/ находится обходом python_sources(root) и краснит гейт с файлом, строкой и именем"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_aliased_binding_in_app_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Привязки structlog.threadlocal (bind_threadlocal, bound_threadlocal, tmp_bind) и псевдонимы bind/bound_contextvars и bind_threadlocal — находки гейта; clear_threadlocal и псевдоним unbind_threadlocal — не вызовы журнала"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (6 новых строк задачи 1)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half (4 новые строки задачи 1)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Номер, переданный журналу, связанному с фабрикой (простое и аннотированное присваивание, атрибут, привязанный журнал, get_task_logger) или ввезённому под псевдонимом (import logging as L, logger as lg), — находка гейта; настройка такого журнала и признак наличия не краснят"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_logger_bound_by_assignment_is_found"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (7 новых строк задачи 2)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half (3 новые строки задачи 2)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Живые деревья: прежние числа вызовов (app 215, scripts 68, max_worker 89), ноль находок, все 106 пофайловых множеств вызовов прежние; реестр пуст, потолок 0"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: other
        ref: "scratchpad cmp_1613.py: python_log_calls базы 625bcec5 против нового гейта по 106 файлам — 0 различий"
        status: pass
    human_judgment: false
  - id: D5
    description: "ГРАНИЦА СРЕДСТВА называет каждую оставшуюся форму с причиной, и рамка D-17 не расширена догадкой"
    requirement: PHONE-21
    verification: []
    human_judgment: true
    rationale: "Полнота и честность прозы границы шапки — суждение ревьюера; тесты закрепляют распознаваемые формы, а не текст границы"

duration: 18min
completed: 2026-10-10
status: complete
---

# Phase 16 Plan 13: Псевдонимы привязок и получатели журнала в гейте приватности — сводка

**Гейт приватности PHONE-21 видит номер в привязке, ввезённой под псевдонимом (`bind_ctx`), в привязках `structlog.threadlocal` (`bind_threadlocal` / `bound_threadlocal` / `tmp_bind`) и в журнале, связанном в модуле с фабрикой (`lg = logging.getLogger()`, `self.lg = structlog.get_logger()`, `get_task_logger`) или ввезённом под псевдонимом (`import logging as L`, `logger as lg`). Средство — `module_log_names`. Живые деревья дают прежние 215/68/89 вызовов и 0 находок, реестр пуст.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-10T05:20:00Z
- **Completed:** 2026-10-10T05:38:00Z
- **Tasks:** 2 (оба RED → GREEN)
- **Files modified:** 1

## Accomplishments

- IN-06 закрыт по решению владельца О-6. Все четыре воспроизведённые формы и их родственники стали находками гейта, каждая закреплена строкой поимённо: псевдоним ввоза привязки, `bind_threadlocal`, `tmp_bind` и получатель `lg` из фабрики.
- Подложенный файл с псевдонимом в синтетическом `tmp_path/app/` находится тем же обходом `python_sources(root)`, что и живое дерево (трасер).
- Шапка: раздел «ЧТО СЧИТАЕТСЯ ВЫЗОВОМ ЖУРНАЛА» называет получателей модуля и цену области видимости «модуль». В «ГРАНИЦЕ СРЕДСТВА» добавлены семь пунктов: параметр функции, `LoggerAdapter`, `functools.partial`, `getattr`, `a = lg`, контейнер или чужой атрибут, фабрика под псевдонимом, привязка через `getattr` / `importlib`, область видимости. Довод у них общий: опознать такой журнал без угадывания нельзя. Летопись IN-06 записана.
- Живые деревья: `app: файлов 100, вызовов 215, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 89; находок 0`. Это прежние числа. Пофайловое сравнение с базой `625bcec5` дало 106 файлов и 0 изменённых множеств вызовов. Живые `_l` / `_lg` в `max_worker/main.py` вызовами журнала не стали.

## Task Commits

1. **Задача 1 (трасер): привязка под псевдонимом ввоза, `structlog.threadlocal`, `tmp_bind`**
   - RED `8c31ebb8` — `test(16-13): add failing rules for aliased and threadlocal context bindings`
   - GREEN `3bd2e6a0` — `feat(16-13): recognise aliased and threadlocal context bindings in the privacy gate`
2. **Задача 2: получатель журнала из фабрики или под псевдонимом; ГРАНИЦА СРЕДСТВА**
   - RED `19a40170` — `test(16-13): add failing rules for loggers bound by assignment or aliased import`
   - GREEN `58550bb3` — `feat(16-13): recognise loggers bound by assignment or aliased import in the privacy gate`

REFACTOR-коммитов нет: убирать после GREEN было нечего.

## TDD Gate Compliance

| Цикл | RED | GREEN | Улика RED |
|------|-----|-------|-----------|
| Задача 1 | `8c31ebb8` | `3bd2e6a0` | `FAILED tests/test_phone_privacy_gate.py::test_a_planted_aliased_binding_in_app_reddens_the_gate`; `1 failed, 82 deselected`; литерал «привязка номера под псевдонимом ввоза не найдена»; `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`, JUnit, tests 1 / fail 1) |
| Задача 2 | `19a40170` | `58550bb3` | `FAILED tests/test_phone_privacy_gate.py::test_a_number_handed_to_a_logger_bound_by_assignment_is_found`; `1 failed, 93 deselected`; литерал «получатель журнала из фабрики под нестандартным именем не распознан»; `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`, JUnit) |

**Семантическая оценка RED.** Задача 1: цель исполнилась. Обход нашёл ровно подложенный файл (`app: файлов 1, вызовов 0`), а упало планируемое утверждение: находок `[]`, потому что псевдоним `bind_ctx` вызовом журнала не распознан. Ошибок сбора, ввоза и фикстур нет. Задача 2: цель исполнилась, упало планируемое утверждение (находок `[]`, получатель `lg` не распознан), сбой окружения исключён. В полном прогоне файла на каждом RED краснели только новые строки плана, по 9 падений. Не-журнальные контроли (`clear_threadlocal`, псевдоним `unbind_threadlocal`, `handlers.clear()`, `setLevel`) зеленели уже на RED, как и положено. Улики лежат в gitignored `.pytest_cache/gsd-red/` (`t1-red.{xml,out,json}`, `t2-red.{xml,out,json}`) и в репозиторий не внесены.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`:
  - `CONTEXT_BINDERS` (+3) и `LOGGER_FACTORIES` (+1);
  - `ModuleLogNames`, `NO_MODULE_LOG_NAMES`, `_is_logger_name`, `module_log_names`;
  - параметр `names` у трёх распознавателей;
  - два новых правила, 13 отрицательных и 7 положительных строк;
  - шапка: получатели, граница, летопись.

## Decisions Made

См. `key-decisions` во фронтматтере. Главное:
- Неподвижная точка присваиваний сверх буквы плана — см. «Отступления».
- Фабрика под псевдонимом ввоза названа в границе, а не распознана: это потребовало бы четвёртого поля `ModuleLogNames`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Связывания журнала разбираются до неподвижной точки**
- **Found during:** задача 2 (GREEN)
- **Issue:** при одном проходе `lg = logging.getLogger(); bound = lg.bind(x=1); bound.info(..., phone)` оставлял `bound` нераспознанным. Порядок `ast.walk` не гарантирует, что `lg` уже известен, когда разбирается присваивание `bound`.
- **Fix:** `module_log_names` повторяет разбор присваиваний, пока множества растут. Связывание без вызова (`a = lg`) по-прежнему вне охвата и названо в границе.
- **Files modified:** `tests/test_phone_privacy_gate.py`
- **Verification:** все 94 правила файла зелёные; живые числа прежние; 106 пофайловых множеств вызовов прежние.
- **Committed in:** `58550bb3`

**2. [Rule 2 - Missing Critical] В ГРАНИЦЕ СРЕДСТВА добавлен пункт «фабрика под псевдонимом ввоза»**
- **Found during:** задача 2 (GREEN)
- **Issue:** `from logging import getLogger as gl; lg = gl(__name__)` распознавателем не видна, а план её не называл ни в охвате, ни в границе. Молчание выдавало бы слепоту за охват (урок запрета 16-09 №2).
- **Fix:** форма названа в границе с причиной.
- **Files modified:** `tests/test_phone_privacy_gate.py`
- **Committed in:** `58550bb3`

---

**Total deviations:** 2 auto-fixed (оба Rule 2).
**Impact on plan:** охват не сужен, рамка D-17 не расширена; живое дерево прежнее.

## Gates (final tree, under the shared `flock`)

| Gate | Result |
|------|--------|
| `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | 94 passed (было 72 до плана: +22 = 2 правила + 13 отрицательных + 7 положительных строк) |
| `-k "aliased_binding or number_handed_to_a_python_log_call or recommended_form_does_not_redden_the_python_half or live_trees or under_its_ceiling"` (после задачи 1) | 51 passed (порог плана 51) |
| `-k "bound_by_assignment or number_handed_to_a_python_log_call or recommended_form_does_not_redden_the_python_half or live_trees or under_its_ceiling"` | 61 passed (порог плана 61) |
| `-s -k live_trees` | `app: файлов 100, вызовов 215, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 89; находок 0` |
| Быстрый прогон фазы (7 путей, `-p no:randomly`) | 443 passed (432 после задачи 1) |
| Оба гейта фазы поимённо (`test_phone_privacy_gate.py`, `test_phone_single_writer_gate.py`) | 142 passed |
| `tests/test_application -q -p no:randomly` | 326 passed |
| Сквозные гейты (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`) | 576 passed (2 мин 28 с) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| Критерии приёмки (grep) обеих задач | все PASS (`"bind_threadlocal"` 1, `"tmp_bind"` 1, `ModuleLogNames` 1, `module_log_names` 1, `IN-06` 6, id задачи 1 — 10, `"get_task_logger"` 1, `receiver_attributes` 8, `LoggerAdapter` 1, `functools.partial` 1, id задачи 2 — 10, реестр и потолок по 1) |
| `tests/test_planning -q` | гонится после коммита этой сводки; итог — в финальном сообщении оркестратору |

**Замены (названы прямо):**
- Полная суита (`just test`, ~4300 тестов, ~45 мин) не гонялась: по указанию оркестратора её гонит гейт после слияния.
- `graphify update .` не запускался: в worktree нет `graphify-out/`, граф обновляет оркестратор после слияния.

## Issues Encountered

- Однократный сбой собственного скрипта сравнения в scratchpad: `dataclass` требует регистрации модуля в `sys.modules` при загрузке через `importlib`. Исправлен в скрипте и к гейту отношения не имеет.

## Known Stubs

Нет.

## Deferred Items

Нет.

## Threat Flags

Нет: правка затрагивает только тестовый гейт и новой поверхности не открывает. T-16-36 и T-16-37 смягчены, как предписано планом.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Сквозной гейт приватности готов для Фаз 17–20. Писатель номера, положивший номер в привязку под псевдонимом или в журнал с нестандартным именем из фабрики, краснит его.
- Оркестратору: перегнать расширенный гейт на объединении волны. 16-14 правит `app/application/accounts/phone.py`, 16-11 — `app/services/phone.py`. Ожидание — ноль находок при пустом реестре.

## Self-Check: PASSED

- FOUND: `tests/test_phone_privacy_gate.py`
- FOUND: `8c31ebb8`, `3bd2e6a0`, `19a40170`, `58550bb3` (все предки HEAD)
- TDD-гейт: `test(16-13)` × 2 и `feat(16-13)` × 2 в журнале ветки

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-10*

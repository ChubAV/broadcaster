---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 23
subsystem: testing
tags: [privacy-gate, structlog, logging, ast, phone, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "Python-половина гейта приватности после 16-18 (LOG_METHODS, ModuleLogNames, module_log_names, _is_log_receiver, _is_log_method_call, _log_method_reference, NEGATIVE_CONTROLS 68, POSITIVE_CONTROLS 35)"
provides:
  - "ASYNC_LOG_METHODS (восемь асинхронных уровней structlog) в LOG_METHODS и сторож против dir(structlog.stdlib.BoundLogger)"
  - "Охват по получателю (D-17 logger.*): любой метод опознанного журнала — вызов журнала, кроме вызова фабрики"
  - "LOGGER_RETURNING_METHODS (getChild, unbind, try_unbind) — привязки; LOGGER_ATTRIBUTE_LOGGERS (root, parent) — журналы-члены"
  - "Правдивая «ГРАНИЦА СРЕДСТВА»: без приписанного D-17 списка методов; летопись WR-13"
affects: [phase-17, phase-18, phase-19, phase-20, privacy-gate]

actuals:
  tokens: 10683      # chars/4 над diff 99002b16..978a9408 (42 732 символа)
  tasks: 2
  commits: 6         # git rev-list --count 99002b16..HEAD на момент записи сводки
plan_head_before: 99002b1608ed3954cbd76147be6f04d069d61071
plan_head_after: 978a9408b28d5b52b7888c5f02b74ea9e4d4b454

tech-stack:
  added: []
  patterns:
    - "Охват по получателю: метод не сверяется со списком, судится получатель (D-17)"
    - "Сторож набора против установленной библиотеки (dir()), чтобы подъём версии краснил суиту"
    - "Независимое связывание: цель — получатель и/или вызываемое журнала, а не одно из двух"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Член опознанного журнала — его метод, но получателем остаётся и по шаблону имени журнала (logger._logger): буквальная схема плана теряла logger._logger.info(…), который база ловит"
  - "module_log_names связывает получателя и вызываемое журнала независимо: emit = logger._log — функция журнала, x = logger._logger — получатель"
  - "logger.parent — журнал-член (LOGGER_ATTRIBUTE_LOGGERS = root | parent): найден самопроверкой, пойман циклом test/feat, а не назван в границе (запрет плана №2)"

patterns-established:
  - "Самопроверка исполнителя перебором форм опознания × методы dir() × формы аргумента × формы вызова до закрытия плана"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Номер, переданный асинхронному уровню structlog (журнал модуля, тело класса через self., getattr-строка, ссылка, alog, aexception), краснит гейт; подложенный файл в tmp_path/app/ находится обходом python_sources"
    requirement: "PHONE-21"
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_async_level_call_in_app_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found[async-*]"
        status: pass
    human_judgment: false
  - id: D2
    description: "ASYNC_LOG_METHODS сверен с асинхронными уровнями установленного structlog 25.5.0"
    requirement: "PHONE-21"
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_async_level_methods_match_the_installed_structlog"
        status: pass
    human_judgment: false
  - id: D3
    description: "Любой метод опознанного журнала (_log, makeRecord, handle, callHandlers, _proxy_to_logger, logging.makeLogRecord, process, setLevel) судится; getChild / unbind / try_unbind — привязки; logger.parent и logger._logger — журналы"
    requirement: "PHONE-21"
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_any_method_of_an_identified_logger_is_a_log_call"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (90 строк)"
        status: pass
      - kind: other
        ref: "scratchpad selfcheck.py: 18 490 форм, 0 промахов (HEAD 978a9408, 2026-10-13)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Живые деревья: ноль находок; новые вызовы — ровно настройка журнала app/logging_config.py и max_worker/main.py; прежние строки контроля — прежний ответ"
    requirement: "PHONE-21"
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: other
        ref: "scratchpad callsets.py + rowdiff.py: 106 файлов по строке и столбцу; 68/68 NEGATIVE прежние, 4/35 POSITIVE сменили флаг"
        status: pass
    human_judgment: false
  - id: D5
    description: "«ГРАНИЦА СРЕДСТВА» не приписывает D-17 список методов; каждая оставшаяся форма — с правдивой причиной"
    requirement: "PHONE-21"
    verification:
      - kind: other
        ref: "uv run python -c '…ast.get_docstring…' (критерий приёмки задачи 2) — OK"
        status: pass
    human_judgment: true
    rationale: "Правдивость прозы границы относительно D-17 — суждение верификатора; машинная проверка ловит только отсутствие прежнего довода"

duration: 25min
completed: 2026-10-13
status: complete
---

# Phase 16 Plan 23: Privacy gate sees structlog async levels and judges any method of an identified logger

**Гейт приватности теперь видит асинхронные уровни structlog (`await logger.ainfo(…, phone=…)`) со сторожем против установленной версии. Охват стал тем, что пишет D-17: любой метод опознанного журнала (`_log`, `makeRecord`, `handle`, `getChild`-привязка, `logger.parent`) судится. Самопроверка перебором: 18 490 форм, ноль промахов, живые деревья по-прежнему без находок.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-10-13T09:57:41Z
- **Completed:** 2026-10-13T10:22:08Z
- **Tasks:** 2 (плюс один цикл самопроверки test/feat)
- **Files modified:** 1

## Accomplishments

- `ASYNC_LOG_METHODS = {adebug, ainfo, awarning, aerror, aexception, acritical, afatal, alog}` входит в `LOG_METHODS`. Сторож `test_the_async_level_methods_match_the_installed_structlog` сверяет набор с `dir(structlog.stdlib.BoundLogger)`. Замер на structlog 25.5.0 дал ровно восемь имён; `addHandler` отсекается правилом хвоста.
- Охват по получателю. `_is_log_method_call` считает вызовом журнала вызов любого метода опознанного получателя, кроме вызова фабрики. `_log_method_reference` распознаёт ссылку на любой метод (`emit = logger._log`, `partial(logger._log, 20)`). Результат вызова считается журналом только у фабрики и у методов из `LOG_METHODS` и `LOGGER_RETURNING_METHODS`. Поэтому `handler = logging.StreamHandler(…)` журналом не становится.
- `LOGGER_RETURNING_METHODS = {getChild, unbind, try_unbind}` работают как привязки. `LOGGER_ATTRIBUTE_LOGGERS = {root, parent}` — члены, которые сами журнал.
- Шапка переписана: раздел «ЧТО СЧИТАЕТСЯ ВЫЗОВОМ ЖУРНАЛА» описывает охват по получателю. Абзац о настройке теперь говорит «вызов журнала без находок», а атрибуты (`handlers`, `propagate`) названы не методами получателя. Цена строгости названа (`log.mark_failed` у `SendLog`). Из «ГРАНИЦЫ СРЕДСТВА» убраны методы журнала и довод «D-17 задаёт гейт списком получателей и методов». В ней остались вывод мимо журнала и текст исключения с причиной «получатель вне списка D-17». Летопись WR-13 стоит отдельным абзацем среди прочих летописей.
- Новые строки: 22 в `NEGATIVE_CONTROLS` (6 асинхронных, 14 по охвату получателя, 2 из самопроверки) и 4 в `POSITIVE_CONTROLS`. Четыре строки настройки журнала переименованы, флаг у них сменился на `True`, находок по-прежнему ноль.

## Task Commits

1. **Задача 1, RED:** трасер асинхронного уровня, сторож, 6+2 строки — `5f632375` (test)
2. **Задача 1, GREEN:** `ASYNC_LOG_METHODS` влит в `LOG_METHODS`, шапка — `1852b951` (feat)
3. **Задача 2, RED:** правило «любой метод опознанного журнала», 14 строк, 4 переименования, 2 положительные строки — `61115c0b` (test)
4. **Задача 2, GREEN:** охват по получателю, `LOGGER_RETURNING_METHODS`, шапка и граница — `e54fd6e3` (feat)
5. **Самопроверка, RED:** строка `logger-parent-attribute` и закрепка `wrapped-structlog-logger-attribute` — `00cecdc0` (test)
6. **Самопроверка, GREEN:** `LOGGER_ATTRIBUTE_LOGGERS = root | parent` — `978a9408` (feat)

**Plan metadata:** коммит `docs(16-23)` этой сводки.

## TDD Gate Compliance

Последовательность `test(16-23)` → `feat(16-23)` соблюдена в каждом из трёх циклов. Улики RED — JUnit XML в gitignored `.pytest_cache/gsd-red/` (`t1`, `t2`, `t3`). Все три прошли `check tdd-red-evidence` с вердиктом `RED_EVIDENCE_OK` (`target_test_failed`).

| Цикл | Цель RED | Три совпадения | Смысловая оценка |
|------|----------|----------------|------------------|
| 1 | `test_a_planted_async_level_call_in_app_reddens_the_gate` | `FAILED tests/test_phone_privacy_gate.py::test_a_planted_async_level_call_in_app_reddens_the_gate`; `1 failed, 150 deselected`; литерал «асинхронный уровень structlog не распознан» | Цель собрана и исполнена. Обход нашёл ровно подложенный файл (`app: файлов 1, вызовов 0`), и упало утверждение о находке (`[]`), а не сбор или фикстура. Весь файл: 8 failed — ровно новые строки, сторож зелёный. |
| 2 | `test_any_method_of_an_identified_logger_is_a_log_call` | `FAILED …::test_any_method_of_an_identified_logger_is_a_log_call`; `1 failed, 167 deselected`; литерал «метод опознанного журнала вне списка уровней не судится» | Упало утверждение на первом исходнике (`logger._log(…)` → `[]`). Весь файл: 21 failed — 14 новых отрицательных строк, цель, 4 переименованные и 2 новые положительные. Прочие 147 зелёные. |
| 3 | `test_a_number_handed_to_a_python_log_call_is_found[logger-parent-attribute]` | `FAILED …[logger-parent-attribute]`; `1 failed, 169 deselected`; литерал «номер в вызове журнала не найден» | Упало утверждение строки (`logger.parent.info(account.phone)` → `[]`). Закрепка `_logger` зелёная, как и задумано. Весь файл: 1 failed. |

## Самопроверка исполнителя (обязательная, задача 2)

- **Скрипт:** `scratchpad/p1623/selfcheck.py`, не коммитится. Он подаёт `python_log_offences(source, "app/x.py")` и ищет предмет в находках.
- **Перебор:** 43 формы опознания получателя × 43 метода × 5 форм аргумента × 2 формы вызова = **18 490 форм**.
  - Формы опознания получателя: имена `logger` / `log` / `*_logger`; `self.log` / `self.logger`; модуль `logging`; `logging.root`, `logger.root`, `from logging import root`, `getattr(logging, "root")`; вызовы фабрик stdlib, structlog, Celery и через `getattr`; связывание, аннотированное, `:=`, второе связывание (`a = lg`, `a = logger`), кортеж; псевдонимы `import logging as L`, `from … import logger as lg`, `getLogger as gl`, `get_logger as gl`; ссылка на фабрику; `LoggerAdapter`, `wrap_logger`, `logging.Logger(…)`, `structlog.PrintLogger()`; `bind`-цепочка, `bind`-связывание, `new`; `getChild` — связывание и цепочка; `unbind`, `try_unbind`; `getattr(logger, "bind")(…)`; тело класса через `self.` и `cls.`; `self.lg` из `__init__`; `logger._logger`, `adapter.logger`, `logger.parent`.
  - Методы: все вызываемые не-dunder члены `dir()` у `logging.Logger`, `logging.LoggerAdapter` и `structlog.stdlib.BoundLogger`, а также `LOG_METHODS` и `makeLogRecord`. В их числе 12 синхронных имён, 8 асинхронных, `_log`, `makeRecord`, `handle`, `callHandlers`, `_proxy_to_logger`, `_process_event`, `_dispatch_to_sync`, `setLevel`, `addHandler`, `process` и другие.
  - Формы аргумента: `phone=p`, `account.phone`, f-строка, ключ словаря, литерал `+79991234567`.
- **Результат по прогонам:**
  - База `99002b16`: 13 930 промахов.
  - После задачи 2 (`e54fd6e3`): **430 промахов, все `logger.parent.<метод>(…)`** — 43 метода × 5 × 2. В базе эти 430 форм тоже промахивались.
  - После цикла самопроверки (`978a9408`): **0 промахов**.
- **Коммиты, вызванные самопроверкой:** `00cecdc0` (test) и `978a9408` (feat).
- **Дата и HEAD прогона:** 2026-10-13, HEAD `978a9408`.

## Живые деревья и сверка множеств вызовов

Команда: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -s -k live_trees`

- После задачи 1 (HEAD `1852b951`): `Python-половина гейта приватности: app: файлов 100, вызовов 215, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 89; находок 0`
- Финальное дерево (HEAD `978a9408`): `Python-половина гейта приватности: app: файлов 100, вызовов 221, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0`

Сверка по файлам. `scratchpad/p1623/callsets.py` снял множества `(строка, столбец)` распознанных вызовов всех 106 файлов: под базовым модулем гейта (`99002b16`) и под финальным. Различаются ровно два файла, удалений нет:
- `app/logging_config.py`: добавлены `(46,14)` `logging.StreamHandler`, `(51,4)` `root.addHandler`, `(52,4)` `root.setLevel`, `(55,4)`, `(56,4)`, `(57,4)` `setLevel` — это +6;
- `max_worker/main.py`: добавлены `(98,11)` `logging.StreamHandler`, `(101,0)` `logging.root.setLevel`, `(119,0)`, `(120,0)` `setLevel` — это +4.

Остальные 104 файла совпадают по строке и столбцу. Числа совпадают с замером планирования (221 / 68 / 93), поэтому подгонки нет. Строка `parent` живых чисел не сдвинула.

Прежние строки контроля проверены `scratchpad/p1623/rowdiff.py`: базовые строки под базовым и финальным модулем.
- 68 из 68 `NEGATIVE_CONTROLS` дают прежний ответ.
- Из 35 `POSITIVE_CONTROLS` флаг сменили ровно 4 строки: `set-level-is-not-a-log`, `factory-assigned-receiver-set-level-is-not-a-log`, `logging-config-import-is-not-a-log`, `getattr-configuration-method` (`False` → `True`).
- Ни одна базовая положительная строка не получила находку.
- JS-половина не правилась: семь функций совпадают с `cce988cb` по `ast.get_source_segment`.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py` — константы `ASYNC_LOG_METHODS`, `LOGGER_RETURNING_METHODS`, `LOGGER_ATTRIBUTE_LOGGERS`. Изменены `LOG_METHODS`, `_log_method_reference`, `_is_log_receiver`, `_is_log_method_call`, `module_log_names`. Новые правила: трасер, сторож, правило «любой метод». Строки контроля, шапка и граница.

## Decisions Made

- **Член опознанного журнала — метод, но получателем остаётся по шаблону имени журнала.** По букве плана такой член журналом не считается, кроме `root` и связанных атрибутов. Тогда `logger._logger.info(account.phone)` ушёл бы мимо гейта, хотя база ловит его по шаблону `_logger`. Член теперь одновременно и метод, и получатель. Это строже базы и закреплено строкой `wrapped-structlog-logger-attribute`.
- **Связывание независимо.** В `module_log_names` прежний `elif` («получатель и не ссылка на метод», иначе «вызываемое») заменён двумя независимыми проверками. Поэтому `emit = logger._log` даёт функцию журнала, а `x = logger._logger` — получателя.
- **`parent` пойман, а не назван в границе.** Запрет плана №2 не разрешает называть в границе форму, опознаваемую по методу или члену опознанного получателя.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Буквальная схема «член опознанного получателя — не журнал» теряла `logger._logger.*`**
- **Found during:** задача 2 (проектирование GREEN)
- **Issue:** по букве плана член опознанного получателя журналом не считается, кроме `root` и связанных атрибутов. Тогда `logger._logger.info(…)` перестал бы краснеть, хотя база его ловит по шаблону `_logger`. Это ослабление гейта.
- **Fix:** `_is_log_receiver` для члена оставлен прежним (шаблон имени, `receiver_attributes`, `root`). Ссылкой на метод считается любой член, кроме журналов-атрибутов и фабрик. Связывание в `module_log_names` стало независимым.
- **Files modified:** `tests/test_phone_privacy_gate.py`
- **Verification:** самопроверка — `wrapped-structlog-logger` дал 0 промахов из 430; строка-закрепка `wrapped-structlog-logger-attribute` зелёная.
- **Committed in:** `e54fd6e3` (логика), `00cecdc0` (закрепка)

**2. [Rule 2 - Missing Critical] `logger.parent.<метод>(…)` не судился — найден самопроверкой**
- **Found during:** самопроверка задачи 2
- **Issue:** 430 из 18 490 форм промахивались, все `logger.parent.*`. `parent` — журнал-член `logging.Logger` и `BoundLogger`. Опознаётся по получателю, значит назвать его в границе нельзя.
- **Fix:** `LOGGER_ATTRIBUTE_LOGGERS = LOGGING_MODULE_LOGGERS | {"parent"}`; ввоз `from logging import root` по-прежнему по `LOGGING_MODULE_LOGGERS`. Отдельный цикл test/feat со строкой `logger-parent-attribute`.
- **Files modified:** `tests/test_phone_privacy_gate.py`
- **Verification:** 0 промахов из 18 490; живые числа не сдвинулись.
- **Committed in:** `00cecdc0` (RED), `978a9408` (GREEN)

**3. [Учёт] Числа строк выше буквы критерия приёмки**
- Критерий задачи 2 печатает `OK 88 39`. Так он и печатал на коммите GREEN `e54fd6e3`. На финальном дереве он печатает `OK 90 39` из-за двух строк самопроверки, которые план предписывает («свой цикл… со строкой `NEGATIVE_CONTROLS`»).
- По той же причине выборка `-k "identified_logger or …"` даёт 132 вместо порога 130, выборка задачи 1 — 133 вместо 115, весь файл — 170.

---

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2) и 1 учётное расхождение.
**Impact on plan:** охват только расширен, в сторону строгости. Реестр `{}` и потолок 0 прежние. Прежние строки дают прежний ответ, кроме четырёх названных. JS-половина не тронута.

## Issues Encountered

- Песочница worktree отказала в node id с квадратными скобками (`…::test[logger-parent-attribute]`) под `flock`. Выборка переписана на `-k "logger-parent-attribute"`, обход песочницы не делался. Составные команды с `git` и heredoc в `uv` тоже отклонялись: они разбиты на простые, правка вынесена в скрипт scratchpad.

## Gates (final tree `978a9408`, под общим `flock`)

| Gate | Result |
|------|--------|
| `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | 170 passed (база 141; 151 после задачи 1; 168 после задачи 2) |
| `-k "async_level or number_handed… or recommended_form… or live_trees or under_its_ceiling"` | 133 passed (после задачи 1 — 115, порог 115) |
| `-k "identified_logger or number_handed… or recommended_form… or live_trees or under_its_ceiling"` | 132 passed (на `e54fd6e3` — 130, порог 130) |
| `-s -k live_trees` | `app: файлов 100, вызовов 221, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0` |
| Быстрый прогон фазы (7 путей, `-p no:randomly`) | 885 passed (база 856; 866 после задачи 1; 883 после задачи 2) |
| Оба гейта фазы (`test_phone_privacy_gate.py` + `test_phone_single_writer_gate.py`) | 486 passed |
| `tests/test_application -q -p no:randomly` | 601 passed (как в базе) |
| Сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (как в базе), 2 мин 36 с |
| `tests/test_logging_config.py` | 3 passed |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `uv run python scripts/prohibitions_census.py --check` | exit 0 (реестр 802 строки, биекция) |
| `tests/test_planning -q` | гонится после коммита сводки — итог в финальном сообщении |

**Подстановки (названы):** полный `just test` (~4850 тестов) не гонялся: его гонит пост-мердж гейт оркестратора на объединённом дереве. `graphify update .` не запускался: worktree без `graphify-out/`, граф обновит оркестратор после слияния.

## Known Stubs

Нет.

## Threat Flags

Нет: изменён только тестовый гейт, новой поверхности нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Гейт приватности готов для писателей номера Фаз 17–20, которые пишут асинхронный код. Называть его поимённо: `uv run pytest tests/test_phone_privacy_gate.py -q`.
- Оркестратору: после слияния волны перегнать `-s -k live_trees` на объединённом дереве. Ожидаются те же 221 / 68 / 93 и 0 находок: 16-21 вызовов журнала в `app/services/phone.py` не добавляет.
- Находок номера в живых деревьях нет. Отложенного нет.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-13*

## Self-Check: PASSED

- FOUND: `tests/test_phone_privacy_gate.py`
- FOUND: `5f632375`, `1852b951`, `61115c0b`, `e54fd6e3`, `00cecdc0`, `978a9408` (предки HEAD)

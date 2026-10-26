---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 57
subsystem: logging
tags: [celery, structlog, log-masking, phone-privacy, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "маска на исполнении — `NumberMaskingFilter`, процессор `mask_numbers_in_event`, `setup_logging` (планы 16-52…16-55)"
provides:
  - "получатель `setup_celery_logging` сигнала `celery.signals.setup_logging` в `app/worker/celery_app.py` (ввоз `celery_setup_logging`)"
  - "модуль `tests/test_worker/test_celery_log_mask.py`: `NUMBER`, `NUMBER_DIGITS`, `MASK`, `GROUP_ID`, `CELERY_PROBE`, `_run_celery_probe(target, tmp_path)`; правила `test_a_celery_worker_prints_a_mask_not_a_number`, `test_celery_beat_prints_a_mask_not_a_number`, `test_a_prefork_pool_child_keeps_the_mask`, `test_the_worker_neither_hijacks_the_root_nor_redirects_print`, `test_control_without_the_receiver_the_worker_prints_the_number`"
affects: [16-60, 16-63, 16-64]

actuals:
  tokens: 3766
  tasks: 2
  commits: 3
plan_head_before: c1d726afa40ad839598e6ce24b5f04800b3c0e94
plan_head_after: 377a9b506a405f8d848423cd56050e4e5590fc8d

tech-stack:
  added: []
  patterns:
    - "Настройка журнала процесса Celery — получателем сигнала `celery.signals.setup_logging`: Celery корень не захватывает и `stdout` не перенаправляет"
    - "Зонд процесса Celery — отдельный интерпретатор `-I` из пустого `tmp_path` с SQLite в памяти, тестовым `SECRET_KEY` и таймаутом; признак живости отсоединяется в зонде, продукт не правится"
    - "Утверждение о номере — через признак (`number_printed = …`) и скрытый кадр помощника (`__tracebackhide__`): отчёт pytest не печатает вывод зонда с номером (D-11)"

key-files:
  created:
    - tests/test_worker/test_celery_log_mask.py
  modified:
    - app/worker/celery_app.py

key-decisions:
  - "Маска в Celery — получатель сигнала `setup_logging`, а не `worker_hijack_root_logger=False` (решение планирования, исполнено как записано)"
  - "Правила ищут цифры номера во всём выводе зонда (stdout + stderr): обработчик Celery пишет в `sys.__stderr__`, и замер контроля нашёл номер там, а не в `stdout`, как сказано в плане"
  - "Ранний получатель `worker_init` оставлен: он настраивает журнал до первой строки признака живости; вторая настройка идемпотентна"

patterns-established:
  - "Процесс, в котором библиотека перенастраивает журнал после проекта, проверяется настоящим конструктором библиотеки в отдельном процессе, с контролем-отрицанием без получателя"

requirements-completed: []  # план несёт PHONE-21; по указанию оркестратора (вердикт фазы `gaps_found`) требование не отмечается

coverage:
  - id: D1
    description: "В настоящем воркере Celery проекта, в `celery beat` и в дочернем процессе пула prefork событие structlog и запись stdlib с номером печатаются маской `+7 *** ***-**-67`; цифр номера в выводе нет, `group_id` виден"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_worker/test_celery_log_mask.py#test_a_celery_worker_prints_a_mask_not_a_number"
        status: pass
      - kind: integration
        ref: "tests/test_worker/test_celery_log_mask.py#test_celery_beat_prints_a_mask_not_a_number"
        status: pass
      - kind: integration
        ref: "tests/test_worker/test_celery_log_mask.py#test_a_prefork_pool_child_keeps_the_mask"
        status: pass
    human_judgment: false
  - id: D2
    description: "Механизм измерен: у воркера `_custom_logging` истинно и на корне один обработчик; контроль-отрицание без получателя печатает номер и видит `ColorFormatter` Celery"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_worker/test_celery_log_mask.py#test_the_worker_neither_hijacks_the_root_nor_redirects_print"
        status: pass
      - kind: integration
        ref: "tests/test_worker/test_celery_log_mask.py#test_control_without_the_receiver_the_worker_prints_the_number"
        status: pass
    human_judgment: false
  - id: D3
    description: "Прежнее не ослаблено: гейт приватности 0 находок (app 102/227, scripts 4/68, max_worker 2/93, wa_worker 1/68), каналы 108 / 106 — 0, писатель `OK 6 106 offences 0`, перенастройка журнала вне `app/logging_config.py` — 0"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py -q -p no:randomly -s -k \"live_tree or live_trees or dynamic_construct_in_the\""
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_logging_reconfiguration_outside_the_logging_config"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 57: Маска номера в процессах Celery — Summary

**Получатель сигнала Celery `setup_logging` (`setup_celery_logging`) держит маску номера в воркере, `celery beat` и дочерних процессах пула prefork. Правила строят настоящий `Worker` проекта, `Beat.setup_logging()` и `fork` + `process_initializer` в отдельном процессе; контроль без получателя печатает номер целиком.**

## Performance

- **Duration:** ~17 мин (992 с)
- **Started:** 2026-10-26T07:07:46Z
- **Completed:** 2026-10-26T07:24:18Z
- **Tasks:** 2
- **Files modified:** 2 (1 создан, 1 изменён)

## Accomplishments

- CR-06 закрыт в коде (О-25 (а), свойство 1). После конструктора `Worker(app=ca.celery, …)` корень — `[["StreamHandler", ["NumberMaskingFilter"], "ProcessorFormatter"]]`. Событие печатается так: `{"phone": "+7 *** ***-**-67", "group_id": "-1001234567890", "event": "wa_phone_reported", …}`, запись stdlib — `{"event": "raw number +7 *** ***-**-67"}`. До плана корень был `[["StreamHandler", [], "ColorFormatter"]]`, и номер печатался целиком.
- `beat` и дочерний процесс пула замаскированы и закреплены правилами. В дочернем процессе `process_initializer` возвращается по `already_setup` и обработчик наследуется при `fork`.
- Механизм измерен, правила не вакуумны. С получателем — `CUSTOM_LOGGING True`, `ROOT_HANDLERS 1`. Без получателя тот же зонд даёт `CUSTOM_LOGGING False`, корень `ColorFormatter`, цифры номера — в `stderr`.
- Комментарий-довод в `app/worker/celery_app.py` называет четыре вещи. Зачем: CR-06, О-25 (а), PHONE-21. Механизм: Celery 5.6.2 `setup_logging_subsystem`, ветка `worker_hijack_root_logger`, `Logging.setup` / `Worker.on_start` без перенаправления `stdout`, граница `print`. Где действует: воркер, beat, дочерние процессы. Чего не задевает: `celery flower`, признак живости, `app.conf.update`. Там же — почему сигнал, а не `worker_hijack_root_logger=False`.

## Task Commits

1. **Задача 1 (трасер, TDD): маска в воркере, `beat` и дочернем процессе пула**
   - RED — `f7d53a5e` (`test(16-57): add failing Celery log-mask probe for worker, beat and prefork child`)
   - GREEN — `d0c777be` (`feat(16-57): mask phone numbers in Celery worker, beat and pool children via setup_logging signal`)
2. **Задача 2: механизм и контроль-отрицание** — `377a9b50` (`test(16-57): pin the Celery mask mechanism and add the no-receiver control`)

REFACTOR не понадобился.

## TDD Gate Compliance

- **RED** (`f7d53a5e`). Прогон `uv run pytest tests/test_worker/test_celery_log_mask.py -q -p no:randomly --junit-xml=.pytest_cache/gsd-red/16-57-red.xml` дал все три совпадения:
  - строка `FAILED tests/test_worker/test_celery_log_mask.py::test_a_celery_worker_prints_a_mask_not_a_number` (и две другие правила);
  - последняя строка сводки `3 failed, 1 warning in 4.01s`;
  - причинный литерал `AssertionError: в процессе Celery номер напечатан целиком: настройку журнала проекта сняла настройка Celery (CR-06); обработчики корня: [['StreamHandler', [], 'ColorFormatter']]` — у всех трёх правил.
- **Верб.** `check tdd-red-evidence` над записью `{command, exitCode, targetTest, output = JUnit XML}` вернул `RED_EVIDENCE_OK` (`target_test_failed`, tests 3, fail 3, `report_errors: []`). Улика лежит в gitignored `.pytest_cache/gsd-red/16-57-red.{xml,out,json}`.
- **Семантическая оценка.** Все три правила исполнились (0 skipped, 0 errors). Код возврата зонда 0. Каждое правило упало на утверждении маски, а строка ROOT показывает захват корня Celery. Это и есть планируемая причина: не сбор, не ввоз, не фикстура. Модуль на RED ввозит на уровне модуля только stdlib.
- **GREEN** (`d0c777be`): `3 passed`. В git-журнале `test(16-57)` стоит перед `feat(16-57)`.

## Files Created/Modified

- `app/worker/celery_app.py`. Изменения:
  - новый ввоз `from celery.signals import setup_logging as celery_setup_logging` (прежняя строка ввоза не тронута);
  - получатель `setup_celery_logging(**kwargs)` с `@celery_setup_logging.connect` и комментарием-доводом;
  - докстринг `setup_worker_logging` дописан одной фразой.

  Тело `setup_worker_logging`, оба признака живости и `app.conf.update` байт в байт прежние: в диффе удалена одна строка, однострочный докстринг.
- `tests/test_worker/test_celery_log_mask.py` — зонд `CELERY_PROBE` с пятью целями (`worker`, `worker-state`, `worker-without-receiver`, `beat`, `child`), помощник `_run_celery_probe` и пять правил.

## Замеры (база оркестратора на `c1d726af` → итоговое дерево)

| Проверка | База | После плана |
|----------|------|-------------|
| Набор фазы (`<verification>`, 11 путей → 12 с новым модулем) | 1675 passed (84 с) | 1680 passed (93 с) |
| Оба гейта + паритет + `test_logging_config` + `test_log_masking` | 1235 | 1235 passed (78,6 с) |
| `tests/test_worker` | 91 passed (11 с) | 96 passed (18,2 с) |
| `tests/test_worker/test_celery_log_mask.py` | — | 5 passed (7,1 с) |
| Сквозные гейты (htmx pairs/gates, templates, declared invariants) | 576 | 576 passed (161 с) |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строки, биекция | exit 0, 934 строки, биекция |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| Приватность, Python | app 102/227, scripts 4/68, max_worker 2/93, 0 | app 102/227, scripts 4/68, max_worker 2/93, находок 0 |
| Приватность, JS | wa_worker 1/68, 0 | wa_worker 1/68, находок 0 |
| Канал запрета приватности / писателя | 108 / 106, 0 | 108 / 106, находок 0 |
| Писатель, живое дерево (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` |
| Перенастройка журнала вне `app/logging_config.py` | 0 | файлов 106; находок 0 |

**Время зондов** (`--durations`, вызов правила вместе со стартом интерпретатора и ввозом приложения):

| Правило | Время |
|---------|-------|
| `worker` | 1,54–1,60 с |
| `child` | 1,66–1,73 с |
| `beat` | 0,47–0,48 с |
| `worker-state` | 1,56 с |
| `worker-without-receiver` | 1,53 с |

Ожидание планирования — до 1,5 с на время внутри зонда (0,9–1,2 с). Целиком правило воркера и дочернего процесса превышает 1,5 с на 0,05–0,23 с за счёт старта интерпретатора `-I`. Таймаут каждого зонда — 60 с.

`tests/test_planning -q -p no:randomly` гоняется ПОСЛЕ коммита этой сводки (указание оркестратора 5), и его итог назван в финальном сообщении исполнителя, а не здесь.

## Decisions Made

- Получатель — сигнал Celery, не `worker_hijack_root_logger=False`. Решение планирования исполнено как записано: без получателя Celery ставит свой обработчик рядом с обработчиком маски.
- Ранний `worker_init` оставлен. Повторная настройка идемпотентна: `setup_logging` очищает корень и ставит один обработчик, и замер показывает `ROOT_HANDLERS 1`.
- В зонде `HOME` — пустой `tmp_path`, а не домашний каталог пользователя. План оставил значение многоточием; так из зонда не читается никакой пользовательской конфигурации.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Отчёт pytest печатал номер из вывода зонда**
- **Found during:** задача 1 (RED).
- **Issue:** первый прогон RED показал в отчёте разбор утверждения pytest (`'9991234567' is contained here: number +79991234567`) и аргумент `result` кадра помощника с выводом зонда. Это противоречит D-11 и запрету плана класть номер в текст сообщений.
- **Fix:** утверждения о номере и группе идут через признак (`number_printed`, `group_visible`, `masks`). Кадр `_assert_masked` скрыт `__tracebackhide__`. Вывод в сообщениях отказа — через `_redacted` с вычеркнутыми цифрами.
- **Files modified:** `tests/test_worker/test_celery_log_mask.py`.
- **Verification:** повторный RED — `grep -c 9991234567` по выводу прогона даёт `0`. Литерал и `3 failed` на месте.
- **Committed in:** `f7d53a5e` (до коммита RED).

**2. [Замер против плана] Номер в контроле — в `stderr`, а не в `stdout`**
- **Found during:** задача 2.
- **Issue:** план велит искать `NUMBER_DIGITS` «в `stdout`» зонда без получателя. Замер: обработчик Celery (`_detect_handler`) пишет в `sys.__stderr__`; `digits in stdout False`, `digits in stderr True`.
- **Fix:** контроль и правила маски ищут цифры во всём выводе зонда (`stdout + stderr`). Для правил маски это строже плана: номер не может спрятаться в `stderr`. Маска и `group_id` по-прежнему утверждаются в `stdout`, где пишет обработчик проекта. Утверждение контроля — наличие (`assert number_printed`); ни одно утверждение не ослаблено.
- **Files modified:** `tests/test_worker/test_celery_log_mask.py`.
- **Committed in:** `f7d53a5e`, `377a9b50`.

**3. [Замер против плана] Что различает «один обработчик корня»**
- **Found during:** задача 2.
- **Issue:** без получателя Celery очищает корень и тоже оставляет ровно один обработчик (`ROOT_HANDLERS 1`, корень `ColorFormatter`). Поэтому условие «ровно один обработчик» различает только альтернативу `worker_hijack_root_logger=False`: там обработчиков два, маска и Celery рядом.
- **Resolution:** отсутствие получателя различает `CUSTOM_LOGGING`. Отдельный замер с отсоединённым получателем в цели `worker-state` (выброшенный скрипт в `.pytest_cache/checks/peek_task2.py`, не в репозитории) дал `CUSTOM_LOGGING False`. Правило механизма утверждает оба условия, и сообщение второго называет именно «свой обработчик рядом».

---

**Total deviations:** 1 auto-fixed (Rule 1), 2 записи «замер против плана». Утверждения не удалены и не ослаблены.
**Impact on plan:** нет расширения объёма; файлы — ровно `files_modified` плана.

## Подстановки исполнителя (названы по указаниям оркестратора)

- Полная суита `just test` не гонялась: её гонит гейт оркестратора после слияния волны (указание 4).
- `graphify update .` не запускался в worktree: его запускает оркестратор после слияния. `graphify query` не понадобился: файлы задачи названы планом и прочитаны напрямую.
- Проверки `<automated>` гонялись под общим замком `flock …/pytest.lock`. Выводы — в `.pytest_cache/checks/*.out`. Запись RED-улики собрана скриптом `.pytest_cache/checks/red_record.py`. Хелпер писателя скопирован в `.pytest_cache/checks/writer_live.py` и запущен с `PYTHONPATH=.`.
- `tests/test_planning` из `<verify>` задачи 2 перенесён в самый конец, после коммита сводки (указание 5).
- Требование PHONE-21 не отмечено Complete; STATE.md, ROADMAP.md, REQUIREMENTS.md, реестр и записи фазы не тронуты (указание 5).

## Threat Model

- T-16-132 (номер в журнале Celery целиком) — mitigate исполнено: получатель сигнала плюс пять правил над настоящими `Worker`, `Beat` и дочерним процессом.
- T-16-133 (получатель кладёт воркер) — mitigate исполнено: зонд строит `Worker` и `Beat` с кодом возврата 0. Получатель повторяет вызов, который уже исполнял `worker_init`.
- Новой поверхности (эндпойнтов, путей доступа, схемы) нет.

## Issues Encountered

Песочница отказала в составной команде с подстановкой `uv run python -c` вокруг `os.path.dirname`. Путь Celery взят прямо из `.venv/lib/python3.12/site-packages/celery`.

## Known Stubs

Нет.

## User Setup Required

Нет.

## Next Phase Readiness

- 16-60 (волна 2) может опираться на получатель `setup_celery_logging`: граница `print` и `flower` — в его шапке маски.
- 16-63 цитирует `setup_celery_logging` (сигнал `celery.signals.setup_logging`) и правила `test_a_celery_worker_prints_a_mask_not_a_number`, `test_celery_beat_prints_a_mask_not_a_number`, `test_a_prefork_pool_child_keeps_the_mask` — имена сохранены как в плане.
- 16-64 записывает GREEN CR-06 хешем `d0c777be` (RED `f7d53a5e`, закрепка механизма `377a9b50`).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

## Self-Check: PASSED

- FOUND: `tests/test_worker/test_celery_log_mask.py`, `app/worker/celery_app.py`
- FOUND: `f7d53a5e`, `d0c777be`, `377a9b50` (предки HEAD)

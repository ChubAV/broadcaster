---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 60
subsystem: logging
tags: [log-masking, phone-privacy, structlog, denial-of-service, unicode, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "маска на исполнении (16-52…16-55), получатель Celery `setup_celery_logging` (16-57)"
provides:
  - "линейный поиск кандидатов маски: `_SPACED_NUMBER_START`, `_RIGHT_EDGE`, `_last_edges`, `_spaced_spans`, `_run_spans`, `_apply_spans`, `_mask_pass`; префиксы 7…15 цифр нарастающим счётом"
  - "`MASK_JUDGMENT_BUDGET: int = 64`, память судов `_Judgments`, `_closed_mask(text: str) -> str` (отказ в закрытую)"
  - "свёртка `_FOLDED_DIGIT_ZEROS` (67 нулей `Nd`), `_FOLDED_SEPARATORS` (22 разделителя + U+FF0B), `_NUMBER_FOLD`; второй проход по свёрнутой копии"
  - "`NumberMaskingFilter(*, formatter_masks_event_dicts: bool = False)` и `attach_number_masking(handler, *, formatter_masks_event_dicts: bool = False)`; корень `setup_logging` — с `True`"
  - "тесты: `MASK_JUDGMENT_BUDGET`, `MASK_FIELD_TIME_BOUND_SECONDS`, `MASK_COST_INPUTS`, `MASK_BOUNDARY_CHARACTERS`, `MASK_BOUNDARY_SUBSTRINGS`, `PROCESSES_WITHOUT_SETUP_LOGGING`, `LONG_SPLIT_REQUEST_PATHS` и восемь правил плана"
affects: [16-63, 16-64]

actuals:
  tokens: 15720
  tasks: 3
  commits: 11
plan_head_before: 14b8cfbe1f7735f10a873a2ec9f491006444d494
plan_head_after: 442aec1baf8de4a41b5cfe97a19e58a0d93010ab

tech-stack:
  added: []
  patterns:
    - "Стоимость маски — линейный проход: концы цепочек и последний допустимый край — один раз на поле, цифры префикса — по массиву позиций цифр (`bisect`), суды — память и бюджет на вызов"
    - "Свёртка вторым проходом: первый проход судит текст как есть (ответ базы), второй — свёрнутую копию и только при наличии знаков свёртки; края найденного номера свёртка не меняет"
    - "Правило-замер времени меряет только сам запрос и маску: клиент построен, стек middleware прогрет, мусор собран до окна"
    - "Сверка «база ↔ HEAD» маски по оси «замаскировано на базе ⇒ замаскировано на HEAD», судья — `normalize_manual`, корпус в `.pytest_cache/r11diff/`"

key-files:
  created: []
  modified:
    - app/services/log_masking.py
    - app/logging_config.py
    - tests/test_services/test_log_masking.py
    - tests/test_logging_config.py

key-decisions:
  - "Серии разделителей не ограничены тремя (отступ от плана): нормализатор читает `+7    999    123    45    67`, база маскировала 504 из 572 таких читаемых форм семейства (b); предел «три» их потерял бы. Линейность держит ограничение по цифрам (7…15) и предвычисление краёв"
  - "Свёртка — вторым проходом, а не одним проходом по свёрнутой копии (отступ от буквы плана): один проход печатал бы `+79991234567‑x`, `+79991234567–`, `call +79991234567—now`, `–+79991234567`, которые база маскирует (свёрнутое тире ломает `_RIGHT`/`_LEFT`)"
  - "Формы с началом вне грамматики (`8)999)123)45)67`, `(999123) 45 67`) названы строками границы, а не добавлены в грамматику: расширение начала изменило бы ответ маски на ASCII (сверка 20 000 строк), а база их тоже не маскировала"
  - "`MASK_FIELD_TIME_BOUND_SECONDS` определён в `tests/test_services/test_log_masking.py` и ввезён в `tests/test_logging_config.py` — один источник предела"

patterns-established:
  - "Сужение грамматики маски меряется корпусом потерь, а не только приобретений: семейства (a)–(e), `OPEN_REGRESSIONS=<n>`"

requirements-completed: []  # план несёт PHONE-21; по указанию оркестратора (вердикт фазы `gaps_found`) требование не отмечается

coverage:
  - id: D1
    description: "Стоимость маски ограничена (CR-07): путь запроса 1 801 и 7 999 знаков через настоящий `setup_logging` и `RequestIdMiddleware` — в предел 0,25 с; восемь полей по 8 000 знаков — в предел и в бюджет 64 суда; сверх бюджета — отказ в закрытую"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_logging_config.py#test_a_long_split_request_path_is_logged_in_bounded_time"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_the_mask_judges_at_most_the_budget_per_field"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_a_long_split_field_is_masked_in_bounded_time"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_beyond_the_budget_a_candidate_is_masked_closed"
        status: pass
    human_judgment: false
  - id: D2
    description: "Знаки, которые нормализатор читает в номере (22 разделителя, U+FF0B, 67 блоков `Nd`), маскируются; девять знаков границы и 11 строк границы названы и видны (WR-39)"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_a_number_the_normalizer_recognises_is_masked"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_a_named_boundary_substring_stays_visible_and_is_named"
        status: pass
    human_judgment: false
  - id: D3
    description: "Словарь в `msg` на обработчике uvicorn, поставленном до `setup_logging`, печатается маской; через корень — одна маска (IN-25)"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_logging_config.py#test_a_dict_message_on_a_handler_set_up_before_the_app_is_masked"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка маски называет по замеру, где маска стоит (веб, Celery, beat, prefork) и где нет (print, процессы без `setup_logging`, строки границы), стоимость, бюджет, цену и отказ в обслуживании"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_the_masking_module_names_what_it_masks_and_its_boundary"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_the_processes_without_setup_logging_are_measured_and_named"
        status: pass
      - kind: integration
        ref: "tests/test_worker/test_celery_log_mask.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Прежнее не ослаблено: три таблицы маски — прежний ответ; 20 000 строк ASCII — ноль расхождений с базой; детерминированный корпус — OPEN_REGRESSIONS=0; гейты и живые строки — базовые числа"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/equal20000.py (EQUAL 20000)"
        status: pass
      - kind: other
        ref: ".pytest_cache/r11diff/mask_corpus.py (OPEN_REGRESSIONS=0)"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py -q -p no:randomly"
        status: pass
    human_judgment: false

duration: 89min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 60: Стоимость и края маски номера — Summary

**Маска номера в журнале стала линейной: кандидат ограничен 7…15 цифрами с нарастающим счётом, суды — бюджетом 64 с отказом в закрытую; путь запроса из 1 801 знака стоит 5–8 мс вместо 2,45 с. Знаки, которые нормализатор читает в номере (NBSP, U+2011, полноширинные и прочие цифры `Nd`), свёрнуты вторым проходом; словарь в `msg` на обработчике uvicorn маскируется; шапка называет границу по замеру.**

## Performance

- **Duration:** 89 мин
- **Started:** 2026-10-26T08:59:46Z
- **Completed:** 2026-10-26T10:28:35Z
- **Tasks:** 3 (RED→GREEN каждой; к задаче 3 — дополнительная пара RED→GREEN строк границы)
- **Files modified:** 4

## Accomplishments

- **CR-07 (T-16-137).** Поиск кандидатов маски линеен: конец цепочки разбивки и её последний допустимый край (`_RIGHT`) считаются один раз на поле (`_last_edges`), цифры префикса — по массиву позиций цифр, судятся только префиксы 7…15 цифр (длиннее судья не признаёт никогда). Память судов на вызов и `MASK_JUDGMENT_BUDGET = 64`; сверх него новый кандидат получает `_closed_mask` (каждая цифра `*`). Выход строится из спанов, порядок прежний.
- **WR-39.** `_NUMBER_FOLD` (67 нулей `Nd`, 22 разделителя, U+FF0B → `+`). `mask_numbers` делает первый проход по тексту как есть (ровно ответ базы) и второй — по свёрнутой копии, только если в тексте есть знаки свёртки; маска ложится на исходные позиции.
- **IN-25.** `NumberMaskingFilter(formatter_masks_event_dicts=…)`: на обработчиках вне корня словарь в `msg` заменяется маскированным (`_guarded`); корень `setup_logging` ставит фильтр с `True` — словарь там маскирует процессор форматтера.
- **Шапка маски** пересобрана по замеру: СВЁРТКА, СТОИМОСТЬ, вторая цена (отказ в закрытую, T-16-140), ГДЕ СТОИТ (веб, Celery и `beat` через `setup_celery_logging` 16-57, пул prefork), ГРАНИЦА (`print`, процессы без `setup_logging` — `scripts/`, Alembic, `flower`, `max_worker`, `wa_worker`; строки `MASK_BOUNDARY_SUBSTRINGS`; поздние обработчики; отчёт о сбое рендерера). Докстринг `setup_logging` называет получатель Celery и флаг.

## Task Commits

1. **Задача 1 (трасер, CR-07):** RED `c86bdda1` (test) → GREEN `8e06c203` (feat)
2. **Задача 2 (WR-39, IN-25):** RED `51358926` (test) → GREEN `20dc5717` (feat)
3. **Задача 3 (шапка, процессы):** RED `e606439d` (test) → GREEN `5f3cb073` (feat); уточнение замера в шапке `2189a1e5` (feat); строки границы с началом вне грамматики — RED `f95da65e` (test) → GREEN `443be2b8` (feat); окно правил стоимости `0f67597e` (test); диапазон пути в шапке `442aec1b` (feat)

Для 16-64 (CR-07): GREEN задачи 1 — `8e06c203` (`feat(16-60): bound the log mask candidate and judge budget so a long split field masks in linear time (CR-07)`).

## TDD Gate Compliance

RED-улики — `.pytest_cache/gsd-red/` (gitignored): JUnit XML прогона, вывод консоли и запись `{command, exitCode, targetTest, output, semanticAssessment}`; классификатор `check tdd-red-evidence` — `RED_EVIDENCE_OK` у всех четырёх.

| RED | Цель | Три совпадения | Семантика |
|-----|------|----------------|-----------|
| `c86bdda1` | `test_a_long_split_request_path_is_logged_in_bounded_time[1801-chars]` | `FAILED tests/test_logging_config.py::test_a_long_split_request_path_is_logged_in_bounded_time[1801-chars]`; `2 failed, 90 deselected, 1 warning in 3.29s`; «цена маски не ограничена» | путь 2,349 с > 0,25 с; правило бюджета — судов 4465 / 1608 / 1072 / 3728 / 40, константа модуля `None` (`vars().get`, не `AttributeError`) |
| `51358926` | `test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named` | `FAILED tests/test_services/test_log_masking.py::test_every_character_…`; `4 failed, 1 passed, 116 deselected …`; «маска не маскирует и граница его не называет» | 22 разделителя читаются и не маскируются; строки NBSP не замаскированы; словарь uvicorn печатает номер (IN-25); `1 passed` — строка-закрепка `narrow-nbsp-split`, видимая и на базе |
| `e606439d` | `test_the_masking_module_names_what_it_masks_and_its_boundary` | `FAILED …::test_the_masking_module_names_what_it_masks_and_its_boundary`; `2 failed, 100 deselected …`; «шапка маски не называет, что маскирует и где её граница» | нет новых терминов и строк границы; правило процессов: замеры всех пяти держатся, падает только на именах Alembic и flower |
| `f95da65e` | то же правило шапки | `FAILED …::test_the_masking_module_names_what_it_masks_and_its_boundary`; `1 failed, 103 deselected …`; тот же литерал | не названы ровно две новые строки границы |

Цепочка: каждый `test(16-60)` стоит перед своим `feat(16-60)`. `refactor` нет.

## Замеры

**Время на дереве GREEN** (`442aec1b`, под общим замком; поле — лучшее из трёх, путь — пять запросов):

| Вход | Длина | HEAD | Судов | База |
|------|-------|------|-------|------|
| путь `"/" + "(1)%20" * 300` через `setup_logging` + `RequestIdMiddleware` | 1 801 | 5,6–7,5 мс | — | 2,45 с (план); 2,25 с в окне правила |
| путь `"/" + "(1)%20" * 1333` | 7 999 | 22,1–29,4 мс | — | — (куб: минуты) |
| `"(1) " * 2000` | 8 000 | 13,8 мс | 9 | — |
| `"8 " * 4000` | 8 000 | 3,4 мс | 6 | — |
| `"(12)" * 2000` | 8 000 | 3,5 мс | 3 | — |
| случайные `(d) ` (зерно 11) | 8 000 | 3,6 мс | 64 | — |
| случайные `8 d ` | 8 000 | 7,2 мс | 64 | — |
| случайные `(dd)` | 8 000 | 5,7 мс | 64 | — |
| случайные `8 (ddd) ` | 8 000 | 5,3 мс | 64 | — |
| цепочки из 9 цифр | 8 000 | 5,2 мс | 64 | — |

Все выходы идемпотентны. Время RED-прогона задачи 1 — 3,29 с (из них 2,35 с — путь из 1 801 знака).

**Сверка 20 000 строк ASCII** (команда плана, зерно 7, против `19c99ffb` = `14b8cfbe` побайтно): `EQUAL 20000` — после GREEN задачи 1, после GREEN задачи 2 и на итоговом дереве.

**Детерминированный корпус** (`.pytest_cache/r11diff/mask_corpus.py`, база — `.pytest_cache/r11diff/base_log_masking.py` из `14b8cfbe`, судья — `normalize_manual`; вывод — `.pytest_cache/r11diff/mask_corpus.out`):

| Семейство | Записей | Номеров судилось | Регрессий | Приобретений |
|-----------|---------|------------------|-----------|--------------|
| (a) строки `MASKED_SUBSTRINGS`, `VISIBLE_SUBSTRINGS`, `NAMED_COST_SUBSTRINGS` | 74 | 51 | 0 | 8 |
| (b) `+d` / `8` / `(d…)` 1–6 цифр, всего 10–16 цифр, серии разделителей 1–6 (до 12 у двузначных), 5 контекстов | 38 220 | 5 220 | 0 | 0 |
| (c) 2 / 3 / 10 номеров в поле, номер дважды, 20 знаков вплотную | 3 052 | 4 648 | 0 | 0 |
| (d) 20…300 кандидатов-мусора (4 вида), затем номер | 640 | 608 | 0 | 0 |
| (e) свёрнутые знаки по краям и внутри, 5 блоков цифр, U+FF0B | 8 176 | 7 412 | 0 | 2 312 |
| **Итого** | **50 162** | **17 939** | **0** | |

Напечатанная строка: `OPEN_REGRESSIONS=0`. У HEAD ни одного исключения и ни одного неидемпотентного вывода.

**За пределами плана** (`.pytest_cache/r11diff/beyond_bounds.py`, голые формы семейства (b)):

| Класс | Форм | Читает нормализатор | Маска базы | Маска HEAD | База да, HEAD нет |
|-------|------|---------------------|------------|------------|-------------------|
| в пределах плана | 1 692 | 451 | 439 | 439 | 0 |
| серия разделителей > 3 | 5 530 | 572 | 504 | 504 | 0 |
| цифр > 15 | 1 092 | 1 | 1 | 1 | 0 |
| шесть цифр в скобках начала | 588 | 77 | 0 | 0 | 0 |

## Проверки на итоговом дереве (`442aec1b`), рядом с базой `14b8cfbe`

| Проверка | База | HEAD |
|----------|------|------|
| набор фазы (12 путей плана) | 1 706 | 1 740 (+34 правила плана) |
| `tests/test_services/test_log_masking.py` + `tests/test_logging_config.py` | 73 + 17 | 129 с `test_celery_log_mask.py` (5): 104 + 20 |
| гейт приватности + писателя + паритет | 345 + 661 + 143 = 1 149 | 1 149 |
| `tests/test_worker` | 96 | 96 (5 правил 16-57 зелёные с новой маской) |
| суиты, читающие журнал (команда задачи 3) | — | 344 passed |
| сквозные гейты | 576 | 576 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строк | exit 0, 934 строк |
| `python -m compileall -q app main.py tests` | exit 0 | exit 0 |
| писатель, живое дерево | `OK 6 106 offences 0` | `OK 6 106 offences 0` |

Живые строки (те же, что на базе): «Python-половина гейта приватности: app: файлов 102, вызовов 227, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0», «Канал запрета гейта приватности: файлов 108; находок 0», «JS-половина гейта приватности: wa_worker: файлов 1, вызовов 68; находок 0», «Канал запрета гейта писателя: файлов 106; находок 0». Вызовов журнала в модуле маски нет; запрещённых динамических конструкций в правленых файлах `app/` нет (канал — 0 находок).

## Files Created/Modified

- `app/services/log_masking.py` — линейный поиск кандидатов, бюджет и память судов, `_closed_mask`, свёртка вторым проходом, флаг фильтра, шапка по замеру
- `app/logging_config.py` — корневой фильтр с `formatter_masks_event_dicts=True`; докстринг называет получатель Celery
- `tests/test_services/test_log_masking.py` — 8 строк свёртки в `MASKED_SUBSTRINGS`, `MASK_COST_INPUTS` (8), `MASK_BOUNDARY_CHARACTERS` (9), `MASK_BOUNDARY_SUBSTRINGS` (11), `PROCESSES_WITHOUT_SETUP_LOGGING` (5), правила бюджета, стоимости, отказа в закрытую, перебора знаков, строк границы, процессов; расширенный `HEADER_TERMS`
- `tests/test_logging_config.py` — правило пути запроса (1 801 и 7 999 знаков) и правило словаря в `msg` на обработчике uvicorn

## Decisions Made

См. `key-decisions`. Сверх них: строка `square-bracket-split` — `+7[999]123[45]67` (нормализатор читает, маска оставляет); правило шапки узнаёт строку границы по тексту строки, по `U+XXXX` её знака или по знаку в обратных кавычках.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Серии разделителей не ограничены тремя**
- **Found during:** задача 1 (замер до GREEN)
- **Issue:** предел «не больше трёх разделителей подряд» из `must_haves` и `<action>` терял номера, которые база маскировала и нормализатор читает: `+7    999    123    45    67`, `8    999    1234567`, `+7 999-----1234567` и т. п. Замер: 572 читаемые формы с серией > 3, база маскировала 504 — с пределом «три» все 504 печатались бы (заметка 10 оркестратора: OPEN_REGRESSIONS ≠ 0 — красное)
- **Fix:** линейность держит граница по цифрам (7…15) и предвычисление краёв, а не длина серии; ответ базы сохранён полностью
- **Files modified:** `app/services/log_masking.py`
- **Verification:** `EQUAL 20000`; корпус — `OPEN_REGRESSIONS=0`; стоимость — таблица выше
- **Committed in:** `8e06c203`

**2. [Rule 1 - Bug] Свёртка вторым проходом, а не одним проходом по свёрнутой копии**
- **Found during:** задача 2
- **Issue:** один проход по свёрнутой копии (буква `<action>`) меняет края: `+79991234567‑x`, `+79991234567–`, `call +79991234567—now`, `–+79991234567` база маскирует, а свёрнутое тире `-` не проходит `_RIGHT` / `_LEFT` — номер печатался бы (замер `claims_probe.py`)
- **Fix:** первый проход — по тексту как есть, второй — по свёрнутой копии результата и только при наличии знаков свёртки
- **Files modified:** `app/services/log_masking.py`
- **Verification:** корпус, семейство (e) — 0 регрессий и 2 312 приобретений
- **Committed in:** `20dc5717`

**3. [Rule 2 - Missing critical] Названы формы с началом вне грамматики**
- **Found during:** сверка «база ↔ HEAD» после задачи 3
- **Issue:** `8)999)123)45)67` и `(999123) 45 67` нормализатор читает как `+79991234567`, маска не маскирует (и на базе); «ГРАНИЦА» их не называла — шапка обещала больше, чем делает
- **Fix:** две строки `MASK_BOUNDARY_SUBSTRINGS` (`eight-before-closing-bracket`, `six-digit-bracket-start`) и пункт «ГРАНИЦЫ»; грамматика не расширена — изменила бы ответ на ASCII
- **Files modified:** `tests/test_services/test_log_masking.py`, `app/services/log_masking.py`
- **Committed in:** `f95da65e` (RED), `443be2b8` (GREEN)

**4. [Rule 1 - Bug] Окно правил стоимости — только запрос и маска**
- **Found during:** итоговый прогон набора фазы
- **Issue:** правило пути из 1 801 знака упало один раз: 0,296 с внутри прогона 1 740 правил (одно — 5 мс). Окно держало построение `AsyncClient` (контекст SSL), сборку стека middleware первым запросом и сборку мусора большой кучи — не цену маски
- **Fix:** клиент строится и стек прогревается запросом `GET /x` до окна, `gc.collect()` — перед окном; то же `gc.collect()` у правила поля. Предел 0,25 с не тронут. База в новом окне — 2,25 с (красное сохраняется)
- **Files modified:** `tests/test_logging_config.py`, `tests/test_services/test_log_masking.py`
- **Verification:** набор фазы дважды подряд — 1 740 passed
- **Committed in:** `0f67597e`

**5. [Rule 1 - Bug] Последнее событие `request`, а не последняя строка журнала**
- **Found during:** задача 1 (RED)
- **Issue:** httpx пишет `HTTP Request: GET …` уровня INFO после события `request`; «последняя строка» плана — строка httpx
- **Fix:** правило берёт последнее событие с `event == "request"`
- **Committed in:** `c86bdda1`

**6. Шапка уточнялась по замеру дважды** — `2189a1e5` (поле 3–14 мс вместо 3–12) и `442aec1b` (путь 20–30 мс в окне правила). Отдельные коммиты `feat(16-60)`: правка — только докстринг.

---

**Total deviations:** 6 (4 — Rule 1, 1 — Rule 2, 1 — уточнение текста шапки замером)
**Impact on plan:** отступы 1 и 2 — от буквы плана в пользу его же запрета «MUST NOT ослабить прежнее»: план мерил только приобретения; корпус потерь показал, что буква плана теряла номера. Именованные сущности плана (`MASK_JUDGMENT_BUDGET`, `_closed_mask`, `_FOLDED_DIGIT_ZEROS`, `_FOLDED_SEPARATORS`, `_NUMBER_FOLD`, `MASK_BOUNDARY_CHARACTERS`, `MASK_BOUNDARY_SUBSTRINGS` с id `narrow-nbsp-split` и `thin-space-split`, `PROCESSES_WITHOUT_SETUP_LOGGING`, флаг) — ровно как предписано. Имя `_SPACED_NUMBER` заменено `_SPACED_NUMBER_START` (выражение начала, тело ищется проходом).

## Подстановки исполнения

- Однострочники `python -c` из `<automated>` / критериев приёмки записаны дословно в `.pytest_cache/checks/*.py` и запущены с `PYTHONPATH=.` (`equal20000.py`, `budget_const.py`, `fold_accept.py`, `header_accept.py`); `git show 19c99ffb:… > …` — отдельной командой.
- Heredoc для дописывания теста отказан песочницей — дописано инструментом Edit.
- Набор фазы — списком `@.pytest_cache/checks/phase_set.txt`.
- `graphify update .` в дереве не запускался (запускает оркестратор после слияния); ориентация — `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- Полный `just test` не запускался — его гоняет пост-мердж гейт оркестратора; вместо него — набор фазы, суиты журнала, сквозные гейты, перепись, `tests/test_worker`.
- `tests/test_planning` — один раз после коммита этой сводки (заметка 5).
- Реестр «разбитых окон» (`gsd_run windows append`) не пополнялся: единственная запись в `.planning/` — эта сводка (заметка 5).

## Deferred / наблюдения

- **Формы с началом вне грамматики** названы границей (отступ 3), не исправлены: 100 голых форм семейства (b) — `8)…`, `8))…`, `(dddddd) …` — нормализатор читает, база и HEAD не маскируют. Адресат — 16-64 (диспозиция) и ревью фаз 17–20 по О-26 (а).
- `deferred-items.md` не создавался.

## Issues Encountered

Общий замок держал одну проверку RED задачи 3 около 10 мин (занят соседом); ожидание — `flock -w 590 … true`.

## User Setup Required

None — внешней настройки нет.

## Next Phase Readiness

Волна 3 (16-63) получает имена: `PROCESSES_WITHOUT_SETUP_LOGGING` (`scripts/`, `Alembic`, `max_worker`, `flower`, `wa_worker`), `MASK_BOUNDARY_CHARACTERS` (`*`, `.`, `/`, `[`, `]`, U+FF0E, U+FF0F, U+FF3B, U+FF3D), `MASK_BOUNDARY_SUBSTRINGS` (`narrow-nbsp-split` — U+202F, `thin-space-split` — U+2009; всего 11 строк), `MASK_JUDGMENT_BUDGET` (64). Корпус сверки — `.pytest_cache/r11diff/` для ревьюера и верификатора.

## Self-Check: PASSED

- Файлы: `app/services/log_masking.py`, `app/logging_config.py`, `tests/test_services/test_log_masking.py`, `tests/test_logging_config.py`, эта сводка, `.pytest_cache/r11diff/mask_corpus.py` и `.out` — FOUND.
- Коммиты `c86bdda1`, `8e06c203`, `51358926`, `20dc5717`, `e606439d`, `5f3cb073`, `2189a1e5`, `f95da65e`, `443be2b8`, `0f67597e`, `442aec1b` и коммит сводки `0df36a8e` — предки HEAD.
- Счёт `commits: 11` измерен `git rev-list --count 14b8cfbe..442aec1b` до коммита сводки.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

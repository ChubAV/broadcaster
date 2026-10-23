---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 52
subsystem: logging
tags: [structlog, logging, privacy, phonenumbers, uvicorn, runtime-guard, D-10, D-11, O-23, O-24]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "нормализатор `app/services/phone.py` (normalize_reported, normalize_manual, format_phone, mask_phone) — судья маски"
provides:
  - "app/services/log_masking.py — mask_numbers, mask_numbers_in_event, NumberMaskingFilter, attach_number_masking; шапка О-23 (а) / О-24 (а) с видимым, ценой и границей"
  - "app/logging_config.py — процессор маски в цепочке ProcessorFormatter корня после format_exc_info; фильтр на корне и на обработчиках существующих журналов (uvicorn); уровень через getLevelNamesMapping"
  - "правдивый абзац D-11 в докстринге mask_phone"
  - "tests/test_services/test_log_masking.py (73 правила) и tests/test_logging_config.py (17 правил): таблицы О-24, фильтр, конвейер в двух режимах, uvicorn, ROUND_TEN_PRIVACY_FORMS"
affects: [16-53, 16-54, 16-56, "Фазы 17–20 (любой номер в журнале — маской на выводе)"]

actuals:
  tokens: 12013
  tasks: 3
  commits: 6
plan_head_before: a8fb02c958fe0b9c7768331375f66bb30d6211ec
plan_head_after: e3ab5e03d607d796fab573779973ab7b277f5678

tech-stack:
  added: []
  patterns:
    - "Защита на исполнении журнала: процессор structlog в цепочке ProcessorFormatter корня + фильтр stdlib на обработчиках; судья «похоже на номер» — нормализатор фазы, а не длина цепочки"
    - "Фикстура restored_logging: снимок корня, обработчиков, уровней, propagate, disabled, фильтров и копии списка процессоров structlog с возвратом после правила"

key-files:
  created:
    - app/services/log_masking.py
    - tests/test_services/test_log_masking.py
  modified:
    - app/logging_config.py
    - app/services/phone.py
    - tests/test_logging_config.py

key-decisions:
  - "Разбивка, которую судья не признал целиком, судится префиксами по границам групп цифр: «номер и хвост» (`+7 999 123-45-67 5`) маскирует номер, таблица «видно» О-24 остаётся верной целиком"
  - "Фильтр маскирует и уже посчитанный `exc_text` (его мог закэшировать чужой форматтер раньше), а при собственном сбое снимает и `exc_info` / `exc_text` / `stack_info` — отказ в закрытую"
  - "Контейнер без номера возвращается тем же объектом; множество становится списком только когда в нём что-то замаскировано"
  - "Число распознанных гейтом приватности вызовов журнала: `app/logging_config.py` 6 → 7 (не 6 → 5, как в прототипе): `logging.getLevelNamesMapping()` гейт считает вызовом `logging.*`"

patterns-established:
  - "Номер в журнале — только маской на выводе: место вызова по-прежнему несёт лишь `phone_set` (D-11); маска — последний рубеж"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Номер в любом поле события structlog доходит до строки JSON маской, ID группы `-100…` виден (трасер)"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_logging_config.py#test_a_number_in_a_structlog_field_is_masked_in_the_rendered_line"
        status: pass
    human_judgment: false
  - id: D2
    description: "Таблицы О-24 (а): 34 формы «маска», 28 форм «видно» (значения владельца дословно), 4 строки названной цены; идемпотентность; маска не поднимает исключения"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_log_masking.py (MASKED_SUBSTRINGS, VISIBLE_SUBSTRINGS, NAMED_COST_SUBSTRINGS, test_masking_is_idempotent, test_masking_never_raises)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Процессор проходит любое поле (str, int-номер → строка маски, вложенные контейнеры, positional_args, repr объекта, ключ); фильтр сохраняет типы аргументов `%d`, маскирует exc_text и stack_info, отчёт `--- Logging error ---` без номера, не падает"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_the_processor_masks_every_kind_of_value, #test_the_filter_*"
        status: pass
    human_judgment: false
  - id: D4
    description: "Конвейер: запись stdlib через корень, IntegrityError с параметрами в обоих путях, обработчики uvicorn до setup_logging, режим console, каждая строка JSON разбирается, неизвестное имя уровня → INFO, фильтр ставится один раз"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_logging_config.py (7 правил конвейера)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Формы раунда 10 стороны приватности (CR-05 ×4, WR-32, WR-33), исполненные через настоящий конвейер, печатают маску"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_logging_config.py#test_a_round_ten_privacy_form_prints_a_mask_not_a_number"
        status: pass
    human_judgment: false
  - id: D6
    description: "Шапка модуля маски и докстринг mask_phone правдивы (О-23 (а), О-24 (а), граница; D-11 — «последний рубеж»)"
    verification:
      - kind: unit
        ref: "tests/test_services/test_log_masking.py#test_the_masking_module_names_what_it_masks_and_its_boundary"
        status: pass
    human_judgment: false

duration: 71min
completed: 2026-10-23
status: complete
---

# Phase 16 Plan 52: Защита журнала на исполнении — маска номера Summary

**Процессор structlog в цепочке корня и фильтр stdlib на корне и на обработчиках uvicorn маскируют формой `mask_phone` любую подстроку, которую нормализатор фазы признаёт номером (О-23 (а), свойство 2; О-24 (а)). ID групп `-100…`, JID групп и метки времени остаются видны, цена названа таблицей.**

## Performance

- **Duration:** 71 мин (включая ожидание общей блокировки pytest)
- **Started:** 2026-10-23T06:50:48Z
- **Completed:** 2026-10-23T08:02:29Z
- **Tasks:** 3 (трасер + 2), все RED → GREEN
- **Files modified:** 5 (2 созданы, 3 изменены)

## Accomplishments

- `app/services/log_masking.py`. Две грамматики кандидатов: цепочка `_DIGIT_RUN` из 7…15 цифр с необязательным `+` и разбивка `_SPACED_NUMBER`. Судья `_recognised` проверяет по порядку: `normalize_reported`, затем `normalize_manual` с перехватом `PhoneError`, затем `normalize_reported` над цифрами разбивки с `+` (разбивка показа `format_phone`). Замена — `mask_phone(<E.164>)`; непредвиденная ошибка разбора даёт маску.
- Процессор `mask_numbers_in_event` возвращает новый словарь и проходит любое значение. Номер-целое становится строкой маски, ID группы-целое остаётся целым; маскируются вложенные `dict` / `list` / `tuple` / `set`, `positional_args`, ключи-строки и `repr` / `str` объекта.
- Фильтр `NumberMaskingFilter` всегда возвращает `True`. Строковые аргументы он маскирует на месте, прочие сохраняют тип. Если номер остался в тексте, он сворачивает запись в маскированный текст. При ошибке подстановки маскирует сообщение и аргументы текстом; маскирует `exc_text` и `stack_info`; при собственном сбое ставит `[number-mask-error]`.
- `attach_number_masking` идемпотентен.
- `app/logging_config.py`. Цепочка теперь `remove_processors_meta → format_exc_info → mask_numbers_in_event → renderer`. Фильтр стоит на корневом обработчике и на каждом обработчике каждого существующего `logging.Logger` (uvicorn). Уровень берётся через `logging.getLevelNamesMapping().get(..., INFO)`; `getattr(logging, …)` снят. Докстринг называет маску и ссылается на шапку.
- Шапка модуля маски называет: зачем (О-23 (а), второй рубеж), что «похоже на номер» (О-24 (а)), что видно, названную цену, где стоит и границу. Абзац D-11 в `mask_phone` стал правдивым: место вызова номер не кладёт, маска в журнале — только последний рубеж.

## Task Commits

1. **Задача 1 (трасер): номер в поле structlog → маска в строке JSON**
   - RED `982f53ce` — `test(16-52): add failing tracer for a number in a structlog field reaching the JSON line`
   - GREEN `535c4f20` — `feat(16-52): mask a number in any structlog event field before the root renderer`
2. **Задача 2: грамматика О-24, фильтр stdlib, конвейер, уровень без getattr**
   - RED `b30772be` — `test(16-52): add failing O-24 tables, stdlib filter and pipeline rules for the number mask`
   - GREEN `0e74bf6c` — `feat(16-52): stdlib number-masking filter on the root and on pre-existing handlers, level by name without getattr`
3. **Задача 3: формы раунда 10 исполнением; шапка маски и абзац D-11**
   - RED `7469df55` — `test(16-52): add round-ten privacy forms through the real pipeline and the masking header rule`
   - GREEN `e3ab5e03` — `feat(16-52): truthful masking header and D-11 paragraph of mask_phone; rule loggers enabled during pipeline rules`

REFACTOR-коммитов нет.

## TDD: RED-улики (три совпадения + `gsd-tools check tdd-red-evidence`)

Улики лежат в `.pytest_cache/gsd-red/` (gitignored): `task{1,2,3}.xml` (JUnit), `.out` (консоль), `.json` (запись `{command, exitCode, targetTest, output}`). Классификатор вернул `RED_EVIDENCE_OK` / `target_test_failed` на всех трёх.

- **Задача 1.** Команда: `-k test_a_number_in_a_structlog_field_is_masked_in_the_rendered_line`.
  - В выводе есть `FAILED tests/test_logging_config.py::test_a_number_in_a_structlog_field_is_masked_in_the_rendered_line`, последняя строка — `1 failed, 3 deselected, 1 warning in 0.14s`.
  - Литерал: «номер в поле события structlog дошёл до строки журнала без маски».
  - Семантика: цель исполнилась и упала на запланированном утверждении — `phone_raw` дошёл до JSON как `79991234567`, процессора в цепочке нет. Это не ошибка сбора: тест модуль маски не ввозит.
- **Задача 2.** Команда: `-k "filter or uvicorn or stdlib or exception"`.
  - В выводе есть `FAILED tests/test_logging_config.py::test_uvicorn_handlers_set_up_before_the_app_are_masked`, последняя строка — `5 failed, 1 passed, 77 deselected` (N = 5 ≥ 5).
  - Литерал: «запись обработчика uvicorn, поставленного до setup_logging, напечатала номер».
  - Семантика: все пять падений — утверждения. Три правила фильтра падают на «фильтра stdlib `NumberMaskingFilter` нет…»: класс ищется утверждением, а не ввозом, поэтому `ImportError` нет. Правило записи через корень падает на номере в отчёте `--- Logging error ---`, uvicorn — на номере в выводе обработчика.
  - Вне выборки падали ещё два правила: `test_an_unknown_level_name_falls_back_to_info` (`getattr(logging, "BASIC_FORMAT")` → `ValueError` в `setLevel`) и `test_masking_is_attached_once`.
  - Закрепки, зелёные с задачи 1: 34 + 28 + 4 строки таблиц, идемпотентность, «не падает», процессор, `IntegrityError` в обоих путях, `console`, «каждая строка JSON».
- **Задача 3.** Команда: `-k test_the_masking_module_names_what_it_masks_and_its_boundary`.
  - В выводе есть `FAILED tests/test_services/test_log_masking.py::test_the_masking_module_names_what_it_masks_and_its_boundary`, последняя строка — `1 failed, 72 deselected`.
  - Литерал: «шапка маски не называет, что маскирует и где её граница».
  - Семантика: шапка была одной строкой, в докстринге `mask_phone` стояла прежняя фраза.
  - Шесть строк `ROUND_TEN_PRIVACY_FORMS` зелёные с RED — это закрепки, поведение дали задачи 1–2. Так и предусматривает план.

## Замер для плана 16-54: живые числа гейта приватности

| | app | scripts | max_worker | находок |
|---|---|---|---|---|
| база `a8fb02c9` (`.pytest_cache/checks/log_call_sites.py`; совпадает с замером оркестратора) | файлов 100, вызовов 225 | 4 / 68 | 2 / 93 | 0 |
| после плана (`-s -k live_trees`) | **файлов 101, вызовов 227** | 4 / 68 | 2 / 93 | 0 |

Строка после плана: «Python-половина гейта приватности: app: файлов 101, вызовов 227, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0».

Сверка множеств мест вызова база ↔ HEAD (`python_log_calls` по всем `.py` трёх деревьев: 386 → 388) — изменения только в двух файлах плана:

- `app/logging_config.py`, 6 → 7 вызовов:
  - сдвинуты строками: `logging.StreamHandler(sys.stdout)` 46 → 56; `root.addHandler(handler)` 51 → 62; `logging.getLogger('uvicorn.access'|'celery'|'telethon').setLevel(logging.WARNING)` 55–57 → 72–74;
  - `root.setLevel(getattr(logging, …))` :52 стал `root.setLevel(logging.getLevelNamesMapping().get(…))` :63;
  - **новый** `logging.getLevelNamesMapping()` :63:18.
- `app/services/log_masking.py`, 0 → 1: `logging.Formatter()` :276 (внутри `…formatException(record.exc_info)`).
- В остальных файлах `app/`, `scripts/`, `max_worker/` множество мест не изменилось.

Для 16-54: все вызовы перенастройки журнала (`addHandler`, `setFormatter`, `handlers.clear()`, `setLevel`, `structlog.configure`) — только в `app/logging_config.py`. В `app/services/log_masking.py` есть только `handler.addFilter(...)` и чтение `handler.filters`. Присваиваний `.handlers` / `.filters` / `.propagate` и вызовов `removeFilter` / `removeHandler` там нет.

## Гейты на конечном дереве (под общей блокировкой)

| Прогон | Итог | База |
|---|---|---|
| `tests/test_logging_config.py` (задача 1) | 4 passed | 3 |
| проверка находок гейтов в `log_masking.py` и `logging_config.py` (`<automated>` задачи 1) | `OK` | — |
| оба модуля плана (задачи 2 и 3) | 83 → **90 passed** | — |
| `<automated>` задачи 2 о таблице «видно» | `OK 28` | — |
| проверка AST «`getattr` с нелитеральным именем» в `app/logging_config.py` | `OK` | — |
| проверка AST докстринга `mask_phone` | `OK` | — |
| quick run фазы + два модуля плана (10 путей) | **1454 passed** (= 1364 + 90) | 1364 |
| оба гейта и паритет поимённо | **960 passed** | 960 |
| живые деревья приватности `-s -k live_trees` | 1 passed, находок 0 (числа выше) | находок 0 |
| живое дерево писателя (`writer_live.py`) | **`OK 6 105 offences 0`** (105 — с `log_masking.py`) | `OK 6 104 offences 0` |
| выборка, читающая журнал (`<automated>` плана, отдельно) | **344 passed** | 344 |
| оба модуля плана ВМЕСТЕ с выборкой, одним процессом, модули первыми | **434 passed** (= 90 + 344) | — |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | **576 passed** | 576 |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0, «реестр: 913 строк, биекция с переписью — согласие» | exit 0 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | гоняется ПОСЛЕ коммита этой сводки (оркестратор, п. 5); итог — в финальном сообщении исполнителя | 218 passed, 2 skipped |

Выборка, читающая журнал, — 344 / 344, как на базе, новых падений нет. Прогон модулей плана вместе с ней (434) доказывает изоляцию: `restored_logging` не оставляет конвейер правила соседям.

## Files Created/Modified

- `app/services/log_masking.py` (создан) — маска текста, процессор, фильтр, установка фильтра; шапка-обоснование.
- `app/logging_config.py` — процессор и `format_exc_info` в цепочке корня, фильтр на корне и на обработчиках существующих журналов, уровень через `getLevelNamesMapping`, докстринг.
- `app/services/phone.py` — правдивый абзац D-11 в докстринге `mask_phone`; код не менялся.
- `tests/test_services/test_log_masking.py` (создан) — 73 правила: 34 / 28 / 4 строки таблиц, идемпотентность, «не падает», процессор, 3 правила фильтра, правило шапки.
- `tests/test_logging_config.py` — фикстура `restored_logging` (autouse), трасер, 7 правил конвейера, 6 строк `ROUND_TEN_PRIVACY_FORMS`; 3 прежних правила сохранены.

## Decisions Made

- **Префиксы разбивки.** Жадная разбивка захватывает соседние цифры: в `+7 999 123-45-67 5 apples` она даёт 12 цифр, и судья её не признаёт. Поэтому судятся префиксы по концам групп цифр, от длинного к короткому: номер маскируется, хвост остаётся. Таблица «видно» верна целиком: ни одна её строка не начинает разбивку.
- **Края грамматики.** Слева блокируют буква, цифра, `+`, `.`, `-`; подчёркивание НЕ блокирует, поэтому `session_79991234567` маскируется. Начало `(цифры)` требует закрывающей скобки, поэтому кортеж `(79991234567, 5)` не теряет `(`.
- **Видимое и цена — замером.** Все значения О-24 (а) видны. Цена совпала с планом буква в букву (`+51 ******89`, `+1 ******89`, `+1 ****67`, `+49 **** **67`). Шапка честно называет ещё одну форму цены: секундная метка времени из 10 цифр (`1729500000` → `+1 *******00`).
- **Счётчик RED задачи 2 — утверждениями.** Правило записи stdlib через корень утверждает и отчёт `--- Logging error ---` о падении подстановки (истина 4). До фильтра этот отчёт печатал `Arguments: ('+79991234567',)`, то есть это настоящая утечка через корень, которую закрывает только фильтр.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Изоляция правил конвейера от журналов, выключенных чужой суитой**
- **Found during:** задача 3, quick run фазы одним процессом: 3 падения в `tests/test_logging_config.py` (`IndexError`, `assert 1 == 2`, `assert 4 == 6`). Отдельно модуль был зелёным.
- **Issue:** `fileConfig` в `alembic/env.py` (суита `tests/test_migrations`) вызывается с `disable_existing_loggers` по умолчанию и выключает существующие журналы, в том числе `telethon`. Записи моих правил до обработчика не доходили. Маска не виновата — это унаследованное состояние процесса.
- **Fix:** `restored_logging` после снимка включает журналы правил (`RULE_LOGGERS`); прежний `disabled` возвращается вместе со всем снимком.
- **Files modified:** `tests/test_logging_config.py`.
- **Verification:** quick run 1454 passed, выборка вместе с модулями 434 passed.
- **Committed in:** `e3ab5e03`.

**2. [Rule 2 — Missing critical] Префиксы разбивки и отказ в закрытую у фильтра**
- **Found during:** задачи 1–2.
- **Issue:** по букве плана номер с хвостом цифр через пробел уходил бы без маски. И ещё: `exc_text`, уже посчитанный чужим форматтером, фильтр не трогал бы, а при собственном сбое фильтра текст исключения печатался бы.
- **Fix:** префиксы по границам групп; маска существующего `exc_text`. Во внешнем `except` фильтр, кроме `msg` / `args`, снимает `exc_info` / `exc_text` / `stack_info`.
- **Files modified:** `app/services/log_masking.py`.
- **Committed in:** `535c4f20`, `0e74bf6c`.

**3. [Отступление от буквы плана] Контейнеры без номера — тем же объектом**
- План пишет «множество — списком». Процессор превращает множество в список только когда в нём что-то замаскировано; контейнер без номера возвращается тем же объектом, чтобы не менять вывод событий без номера. Кроме `repr` объекта судится и `str` (рендерер `console` печатает нестроковое `event` через `str`). Правило `test_the_processor_masks_every_kind_of_value` утверждает `tags == [MASK]`.

**4. [Замер против плана] Числа гейта приватности.** Прототип планирования ожидал `app/logging_config.py` 6 → 5 и +1 в модуле маски, итого `app` 225. Замер: 6 → 7 и +1, итого **227**. Гейт отдельным вызовом журнала считает `logging.getLevelNamesMapping()` (получатель `logging.*`, D-17), а прежний `getattr(logging, …)` отдельным вызовом не считался. Находок 0, модули гейтов не тронуты. Действует замер.

### Подстановки исполнения (записаны по требованию оркестратора)

- `python -c "…"` под `flock` песочница отвергла. Каждая проверка записана дословно в `.pytest_cache/checks/{t1_gates,t2_visible,t2_getattr,t3_maskdoc}.py` и исполнена с `PYTHONPATH=.`: та же логика, те же `assert`.
- Запись плана `plan_head_before` в git-каталог worktree песочница отвергла. Она лежит в `.pytest_cache/gsd-plan-head-before-16-52`; счёт `commits` измерен `git rev-list --count a8fb02c9..HEAD` = 6.
- Предварительные зонды маски (`probe_mask.py`, `probe_table.py`) исполнялись интерпретатором `/source/broadcaster/.venv/bin/python -B` только на чтение, до сборки `.venv` worktree. Все выводы, вошедшие в таблицы, перепроверены правилами под `uv run`.
- `graphify update .` в worktree не запускался (нет `graphify-out/`); граф пересоберёт оркестратор после слияния.
- Полный `just test` не запускался: его гонит пост-мердж гейт оркестратора. Команда quick run без двух модулей плана отдельно не гонялась: тот же набор с модулями плана последними дал 1454 = 1364 + 90.
- `tests/test_planning` гоняется после коммита сводки (п. 5 оркестратора).

---

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2), 1 отступление от буквы, 1 замер против плана.
**Impact on plan:** все правки — в сторону маски или изоляции правил; таблицы О-24 и модули гейтов не подгонялись.

## Для следующих волн

- **16-51 (слияние).** Во всех правилах `account` — заглушка `types.SimpleNamespace(phone="+79991234567")`; `MessengerAccount` с номером нигде не строится и не присваивается. Живое дерево писателя в моём worktree — 105 файлов; после слияния с защитой писателя будет 106, его меряет оркестратор.
- **16-53 (запрет динамики).** В `app/services/log_masking.py` и `app/logging_config.py` нет `getattr` / `setattr` / `hasattr` / `delattr`, `__dict__`, `vars()`, `globals()`, `locals()`, `sys.modules`, `importlib`, `__import__`, `eval` / `exec` / `compile` (встроенных), `methodcaller` / `attrgetter`, протокола `__getattr__` / `__setattr__`. Есть `re.compile` (как в живом `app/services/schedule_rules.py:57`) и кортеж `(repr, str)` встроенных функций, перебираемый в `_masked_text` — это не рефлексия по имени, но называю явно.
- **16-54.** См. замер выше. `.addFilter` и чтение `.filters` — только в модуле маски; вся перенастройка — в `app/logging_config.py`.
- **16-56.** Хэши GREEN для строки CR-05: `535c4f20`, `0e74bf6c`, `e3ab5e03` (`feat(16-52): …`).

## Issues Encountered

- Общая блокировка pytest долго держалась прогонами оркестратора и соседа по волне: первый замер базы ждал около 15 минут. Задач это не меняло.

## Known Stubs

Нет. `[number-mask-error]` — намеренная метка отказа в закрытую при сбое самого фильтра, не заглушка.

## User Setup Required

None — внешних сервисов нет.

## Next Phase Readiness

- Защита на исполнении (свойство 2 О-23 (а)) стоит в процессах, вызывающих `setup_logging`: веб, воркеры и beat Celery.
- Граница названа в шапке модуля: `print` и потоки мимо журнала, обработчики после вызова, скрипты без `setup_logging`, `max_worker`, `wa_worker`, край грамматики (`+7.999.123.45.67`, номер вплотную к букве), отчёт `--- Logging error ---` о сбое конвейера события structlog.
- Требование PHONE-21 этим планом в REQUIREMENTS.md не отмечается: вердикт фазы — `gaps_found`, отметки ведёт оркестратор.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-23*

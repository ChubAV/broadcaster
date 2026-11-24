---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 38
subsystem: testing
tags: [ast, phone, privacy-gate, writer-gate, shared-grammar, elementwise-carrier, row-carrier, keep-iterables, methodcaller, base-head-differential, tdd, cr-02, wr-25]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль после 16-36 / 16-37 (`reference_arguments`, `wrapper_applications`, `ELEMENTWISE_CARRIERS = {map}`); гейт приватности на общей семантике обёртки; инструмент сверки `.pytest_cache/r7diff/` 16-37"
provides:
  - "`reference_arguments(…, keep_iterables=False)`: у поэлементного носителя гейт приватности получает итерируемые целиком — не-литерал выражением, comprehension с источником итерации, `*name` узлом `Starred`; гейт писателя зовёт без параметра, его ответ прежний"
  - "одно правило носителей для обоих гейтов: `ELEMENTWISE_CARRIERS` = `map`, `imap`, `imap_unordered`, `map_async`; `ROW_CARRIERS` = `starmap`, `starmap_async`; построчное прочтение у обоих гейтов без флага; сторож правила-паритета против stdlib"
  - "`wrapper_applications(…, keep_iterables=False)`: обёртка журнала, поданная поэлементному носителю, получает и элементы, и итерируемые целиком (самопроверка, заход 1)"
  - "путь `methodcaller` гейта приватности — `every_reading=True`, как у гейта писателя: `starmap(mc, [(logger,)])` и `partial(threading.Thread, target=mc)(args=(logger,))` — находки"
  - "трасер `test_a_planted_log_reference_mapped_over_an_account_attribute_reddens_the_gate`; `NEGATIVE_CONTROLS` 126 → 145, `POSITIVE_CONTROLS` 50 → 51, `LITERAL_FORM_CASES` 244 → 246; сторож `test_the_elementwise_and_row_carriers_name_the_installed_apis`"
  - "шапки обоих гейтов: одно правило носителей, суд итерируемой целиком, граница «судится само выражение» снова правда, летопись CR-02 / WR-25 с регрессией `c6953017`"
  - "инструмент сверки для 16-39: seed 38, семейство (д) `e-wrapper-read-1637`, (е) `selfcheck_1638.py` / `selfcheck_cells.json` (9 180 форм)"
affects: [16-39, 16-40, phase-17, phase-18, phase-19, phase-20]

actuals:
  tokens: 13371
  tasks: 3
  commits: 10
plan_head_before: 9a92efd9936cfbb3b7082501551ff5bc24ac7769
plan_head_after: 9ce79852a2e35d5c945e3fb470f0f2d206bcf640

tech-stack:
  added: []
  patterns:
    - "Различие гейтов на общей функции — параметр прочтения (`keep_iterables` у приватности, `every_reading` у писателя и в пути `methodcaller` приватности), а не копия семантики в модуле гейта"
    - "Таблица носителей сверяется сторожем с установленным stdlib (`dir()` объектов с `map`), по образцу сторожа асинхронных уровней structlog"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_phone_privacy_gate.py
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_gates_parity.py

key-decisions:
  - "`keep_iterables` заменяет у поэлементного носителя элементы итерируемыми целиком, а не добавляет второе прочтение: поддерево литеральной итерируемой содержит те же узлы-элементы, находки стоят на тех же узлах; число вызовов живых деревьев прежнее (225 / 68 / 93)"
  - "Построчный носитель сохраняет общее прочтение (итерируемая целиком у обоих гейтов) и получает построчное без флага; литеральные кортежи прочих носителей — по-прежнему только под `every_reading`"
  - "Обёртке, поданной поэлементному носителю, — оба прочтения (элементы и целиком): из элементов путь `methodcaller` берёт получателя, а `[logger for _ in …]` целиком получателя не даёт"
  - "Путь `methodcaller` гейта приватности — `every_reading=True`: получатель лежит там, где его подаёт любое прочтение; цена — в сторону лишней находки, получатель обязан быть опознанным журналом (D-17)"

patterns-established:
  - "Сверка «база ↔ HEAD» гоняется заново после того, как в корпус вошла самопроверка (е): так нашлась регрессия GREEN задачи 2, которую исходный корпус не видел"

requirements-completed: [PHONE-21, PHONE-02]

coverage:
  - id: D1
    description: "Подложенный отчёт `app/services/phone_report.py` с `list(map(logger.info, account.phones))` краснит гейт приватности: ровно одна находка `:7 — имя — phones`"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_log_reference_mapped_over_an_account_attribute_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Семь форм CR-02 и две формы WR-25 — строки `NEGATIVE_CONTROLS` с находкой `phone`; `map(logger.info, account.names)` — вызов журнала без находки; закрепки `imap` / `imap_unordered` / `map_async` / `pool.starmap` и строки циклов самопроверки и сверки"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half"
        status: pass
    human_judgment: false
  - id: D3
    description: "Одно правило поэлементных и построчных носителей для обоих гейтов, сверенное с stdlib 3.12; гейт писателя — прежний ответ на прежних строках, две закрепки"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_elementwise_and_row_carriers_name_the_installed_apis"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/tables_t2.py (OK ['imap', 'imap_unordered', 'map', 'map_async'] ['starmap', 'starmap_async']), writer_reading_t1.py (OK writer reading unchanged)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапки: абзац носителя называет `ELEMENTWISE_CARRIERS` / `ROW_CARRIERS`, суд целиком, `methodcaller` в строке; граница «судится само выражение» на месте; летопись CR-02 / WR-25 с `c6953017`; заявление писателя прежнее; докстринг `reference_arguments` правдив"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/header_t3.py (OK), docstring_t2.py (OK)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сверка «база ↔ HEAD»: 32 970 ячеек, `BASE 9a92efd9 -> HEAD 9ce79852` без регрессий, `OPEN_REGRESSIONS=0`, `SELFTEST` 43 и 52; самопроверка 9 180 форм — 0 промахов на HEAD, 1 548 на базе плана"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "bash .pytest_cache/r7diff/run.sh 16-38 (выход 0, HEAD 9ce79852)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Прежнее не ослаблено: 117 / 49 строк `65e5c692` на месте; живые деревья 225 / 68 / 93, находок 0; писатель 104 файла, 6 сырых, 0 судимых; реестры прежние; JS-половина не тронута"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: ".pytest_cache/checks/rows_t1.py (OK 117 49 145 51), registry_t3.py (OK), writer_live.py (OK 6 104), js_t3.py (OK 23 0)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
    human_judgment: false

duration: 61min
completed: 2026-10-19
status: complete
---

# Phase 16 Plan 38: Итерируемая поэлементного и построчного носителя — Summary

**Гейт приватности снова судит итерируемую поэлементного носителя целиком. Параметр общей функции `reference_arguments(…, keep_iterables=True)` снимает регрессию `c6953017`: `list(map(logger.info, account.phones))`, `ex.map`, `pool.map`, comprehension, `iter(…)`, `*phone_lists` и имя, связанное с номерами, — находки. Гейт писателя зовёт ту же функцию без параметра, его ответ прежний. Какие носители поэлементны (`map`, `imap`, `imap_unordered`, `map_async`) и построчны (`starmap`, `starmap_async`), решает одно правило общего модуля для обоих гейтов, и сторож сверяет его с установленным stdlib. `methodcaller` у `starmap` получает получателя из строки. Самопроверка (9 180 форм) нашла ещё два места той же оси, сверка «база ↔ HEAD» — регрессию GREEN задачи 2. Всё закрыто своими циклами: `OPEN_REGRESSIONS=0`, `BASE … regressions=0`.**

## Performance

- **Duration:** ≈61 мин
- **Started:** 2026-10-19T09:59:35Z
- **Completed:** 2026-10-19T11:01Z
- **Tasks:** 3, и сверх них два цикла: заход 1 самопроверки и цикл сверки
- **Files modified:** 4

## Accomplishments

- **Общий модуль (`tests/phone_gate_grammar.py`):**
  - `reference_arguments(…, keep_iterables=False)` и `_carried_by(…, keep_iterables)`. При `keep_iterables=True` поэлементный носитель подаёт ссылке итерируемые как есть: не-литерал выражением, comprehension целиком, `*name` узлом `Starred`. Докстринг, правило 8, называет параметр, его потребителя и регрессию `c6953017`;
  - `ELEMENTWISE_CARRIERS = {map, imap, imap_unordered, map_async}`, новая `ROW_CARRIERS = {starmap, starmap_async}`, комментарий с замером stdlib 3.12;
  - построчное прочтение у обоих гейтов без флага. Литеральные кортежи прочих носителей — по-прежнему только под `every_reading`;
  - `wrapper_applications(…, keep_iterables=False)`: при параметре поданная поэлементному носителю обёртка получает оба прочтения (самопроверка, заход 1);
  - докстринг `reference_arguments`: правило 5 называет обе таблицы. Правило 7 больше не утверждает, что гейту приватности лишние прочтения бесполезны: оно говорит, какое прочтение какому гейту нужно.
- **Гейт приватности:**
  - `_carried_log_calls` зовёт `reference_arguments(…, keep_iterables=True)`;
  - `wrapper_applications(…, keep_iterables=True)`;
  - `_applied_log_methodcaller` зовёт общую функцию с `every_reading=True` (цикл сверки);
  - трасер;
  - `NEGATIVE_CONTROLS` 126 → 145, `POSITIVE_CONTROLS` 50 → 51;
  - правило шапки получило места проверки;
  - шапка: абзац носителя, пример `methodcaller`, летопись CR-02 / WR-25, комментарий ввоза.
- **Гейт писателя:** две закрепки `LITERAL_FORM_CASES` (244 → 246), фраза шапки об одном правиле носителей, места проверки в правиле шапки, ввоз `ROW_CARRIERS`.
- **Правило-паритет:** `ROW_CARRIERS` / `_ROW_CARRIERS` в `GRAMMAR_TABLES`, `MAP_CARRIER_OWNERS`, сторож `test_the_elementwise_and_row_carriers_name_the_installed_apis` (15 → 16 правил).

## Task Commits

1. **Задача 1 (трасер): суд итерируемой целиком, CR-02** — `1da1b993` (test, RED), `3a7fe75b` (feat, GREEN).
2. **Задача 2: одно правило носителей, `methodcaller` в строке, WR-25** — `3b503f81` (test, RED), `b953ce0d` (feat, GREEN).
3. **Задача 3: шапки и летопись** — `0b50a4de` (test, RED), `d7013797` (feat, GREEN).
4. **Самопроверка, заход 1: обёртка журнала над не-литералом** — `9f804a44` (test, RED), `85ac9a2e` (feat, GREEN). Этот же GREEN закрыл регрессию GREEN задачи 2 (см. сверку).
5. **Цикл сверки: `methodcaller` именованной ссылкой применённой обёртки** — `269b9218` (test, RED, вместе с двумя закрепками регрессии), `9ce79852` (feat, GREEN).

**Plan metadata:** коммит `docs(16-38)` с этой сводкой. Первый коммит плана — `1da1b993`, база — `9a92efd9`.

Гейт трасера после задачи 1. Режим `end-of-phase`, у трасера только проверки `<automated>`. Все четыре прогнаны и зелёные:
- `257 passed`;
- `OK 117 49 133 51`;
- гейт писателя `574 passed`;
- `run.sh 16-38` — выход 0, `OPEN_REGRESSIONS=0`.

После этого план перешёл к задачам 2 и 3.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored). Записи — `t1.json`, `t2.json`, `t3.json`, `s1.json`, `s2.json`. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`) на всех пяти.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_log_reference_mapped_over_an_account_attribute_reddens_the_gate` | `8 failed, 1 passed, 233 deselected` | «итерируемая поэлементного носителя не судится» | Трасер исполнился: файл найден обходом, вызовов > 0, находок в файле `[]`. Семь строк CR-02 упали на «номер в вызове журнала не найден». Строка `account.names` зелёная до GREEN — закрепка. |
| Задача 2 | `test_the_elementwise_and_row_carriers_name_the_installed_apis` | `3 failed, 261 deselected` | «носитель с `map` не классифицирован как поэлементный или построчный» | Сторож упал на утверждении: в таблицах нет пяти методов stdlib. Две строки WR-25 — «номер в вызове журнала не найден». Шесть закрепок зелёные до GREEN: четыре у приватности, две у писателя. |
| Задача 3 | `test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` и `…writer_gate_header…` | `2 failed, 822 deselected` | «шапка гейта приватности не называет носителя ссылки и общую грамматику» | Приватность — 6 мест: в абзаце носителя нет пяти слов, в шапке нет `c6953017`. Писатель — 2 места. Пункт «судится само выражение» уже на месте — закрепка. |
| Заход 1 | `…is_found[carrier-wrapper-mapped-over-a-phone-attribute]` | `2 failed, 248 deselected` | «номер в вызове журнала не найден» | Обе строки повторяют класс 432 промахов самопроверки. |
| Цикл сверки | `…is_found[methodcaller-keyword-reference-in-an-applied-thread-wrapper]` | `2 failed, 2 passed, 250 deselected` | «номер в вызове журнала не найден» | Две строки `methodcaller` — RED. Две закрепки регрессии задачи 2 зелёные: их закрыл `85ac9a2e`. |

## Самопроверка исполнителя (задача 3; О-16 (а))

Скрипт `.pytest_cache/r7diff/selfcheck_1638.py` лежит в gitignored-каталоге и в репозиторий не коммитится. Он однопроцессный и работает под общим `flock`. Прогон итогового захода — 2026-10-19 ≈10:36 UTC, HEAD `9ce79852` (код `85ac9a2e` + путь `methodcaller`).

**Оси:**
- **Носитель (9):** `map`, `ex.map`, `pool.map`, `pool.imap`, `pool.imap_unordered`, `pool.map_async` (с `.get()`), `itertools.starmap`, `pool.starmap`, `pool.starmap_async`.
- **Форма итерируемой (10):**
  - литеральный список, кортеж, `list([…])`;
  - comprehension и генератор над `phone`-источником;
  - `iter(name)`, имя с `phone`, атрибут с `phone`, `*name`;
  - имя без `phone`.
- **Значение опознания:** пять значений `LOG_IDENTIFICATION_VALUES` (`methodcaller` — с получателем в элементе у поэлементного носителя и в строке у построчного). Шестое — обёртка носителя `partial(contextvars.copy_context().run, logger.info)`.
- **Форма:** 12 `BINDING_FORMS`.

**Охват гейтов:**
- **Гейт приватности:** полный крест, 9 × 10 × 6 × 12 = **6 480** форм.
- **Гейт писателя:** судимые API 16-34 с колонкой позиционным литералом (`setattr`, `set_committed_value`, `flag_modified`) × пять видов значения (имя, атрибут, getattr-строка, `partial`, `methodcaller`) × 9 × 10. Ось формы — ротацией в два прохода: **2 700** форм.

**Ожидание:**
- **Приватность:**
  - номер или имя с `phone` в итерируемой — находки называют `phone`, место не повторяется (5 400);
  - итерируемая без `phone` — вызов журнала без находки (540);
  - `methodcaller` с получателем из не-литерала — ноль: получатель не опознан, угадывания нет, D-17 (540).
- **Писатель:**
  - литеральная итерируемая на месте колонки — ровно одна находка с `phone` (1 350);
  - не-литерал — ни одной находки «место — вид» сверх базы с несвязанной ссылкой (1 242). У формы `direct` база держит значение отдельной строкой и сравнивается по видам (108), как база источника (г).

| Заход | HEAD | Подано (приватность / писатель) | Промахов | Итог |
|-------|------|---------------------------------|----------|------|
| 1 | `d7013797` | 9 180 (6 480 / 2 700) | **432**: обёртка носителя × 6 поэлементных носителей × 6 форм (comprehension, генератор, `iter`, имя, атрибут, `*name`) × 12 форм | цикл `9f804a44` / `85ac9a2e` |
| 2 | `85ac9a2e` | 9 180 | **0** | ячейки ушли в корпус (е) |
| 3 (итог) | `9ce79852` | 9 180 | **0** | — |
| контроль против вакуума | дерево базы `9a92efd9` | 9 180 | **1 548**: приватность 1 332, писатель 216 | генератор видит дефект базы |

**Найдено:**
- **Заход 1:** обёртка журнала, поданная поэлементному носителю, получала от `wrapper_applications` только элементы. Это класс CR-02 на оси обёртки, закрыт `85ac9a2e`.
- **Ложные промахи генератора** (исправлен генератор, не гейт): 27 ячеек писателя `methodcaller` × `direct` × не-литерал. Значение и есть ссылка, и подмена ссылки убирала из базы саму находку значения.
- **Состав контроля на базе:**
  - приватность — `map` / `ex.map` / `pool.map` × пять значений (CR-02);
  - `starmap` × `methodcaller` (WR-25);
  - `imap` × `methodcaller`;
  - писатель — `imap`, `imap_unordered`, `map_async` с comprehension, генератором и `list([…])` на месте колонки. Эти формы гейт писателя на базе не читал: тогда они не были поэлементными. Задача 2 их поймала; это улучшение, а не смена прежнего ответа.

**По осям (итог):** носители — по 1 020; формы итерируемой — по 918; значения приватности — по 1 080; значения писателя — по 180; формы связывания — от 764 до 766.

**Полный крест писателя без ротации:** 9 × 10 × 3 × 5 × 12 = 8 100. Он не прогонялся, прогнана ротация (2 700).

## Сверка «база ↔ HEAD» (свойство 7 О-16 (а); пункт 5 договора `16-36-PLAN.md`)

**Инструмент.** За основу взята копия 16-37 (`scratchpad/r7diff-16-37/`). Каждая часть сверена с договором `<scope_note>` 16-36 и этого плана: `corpus.py`, `judge.py`, `run.sh <план>`, git зовётся только из `run.sh`, кеш деревьев и вердиктов, `SELFTEST` на двух парах. Изменения этого плана:
- `SEED = 38`, шапка `corpus.py`;
- новое семейство (д) `e-wrapper-read-1637`: оси самопроверки 16-37 полным крестом (смешанное основание вместо ротации), ожидание `phone_unique` / `zero`, как у 16-37;
- (е) — `selfcheck_cells.json` этого плана. Файл (е) плана 16-37 переименован в `selfcheck_cells_1637.json` и в корпус целиком не входит: его оси держит выборка семейства (д);
- помощники `inspect_ids.py`, `classify_ids.py`, `inspect_self.py`.

`run.sh` уже принимал план аргументом.

**Корпус итогового прогона** (HEAD `9ce79852`, 32 970 ячеек, `corpus.json` sha256 `8466850d12874a55fc7c3325bd4386b7a8457a1147c2606d0b3a4b1da7cd3bde`):

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 246, `LEGITIMATE_CASES` 98, `NEGATIVE_CONTROLS` 145, `POSITIVE_CONTROLS` 51 | 540 |
| (б) ячейки матриц | 12 `BINDING_FORMS` × 5 значений × (прямой вызов + 11 `REFERENCE_CARRIERS` + 9 кандидатных строк раунда 7) × 2 гейта | 2 520 |
| (в) формы ревью раунда 7 | CR-02 (7 + 3), CR-03 (4 + 3), WR-26 (4 + 3), WR-25 (2 + 1), WR-24 (2 + 1) | 30 |
| (г) дифференциал ревьюера / верификатора | 5 значений × 7 форм аргументов × 10 носителей × 2 гейта | 700 |
| (д) выборка самопроверок 16-27…16-34, 16-36, 16-37 | 10 семейств по 2 000 | 20 000 |
| (е) самопроверка этого плана | итоговый заход | 9 180 |

**Правило выборки (д):** равномерно, без повторов, `random.Random(38)` (seed — номер плана), ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием, полный перебор не материализуется.

| Семейство (план) | Полный перебор генератора | Прогнано |
|------------------|---------------------------|----------|
| ось B (16-27) | 43 120 | 2 000 |
| ось A (16-22, 16-28) | 48 264 | 2 000 |
| ось SQL (16-28) | 11 390 | 2 000 |
| носитель журнала (16-29) | 234 900 | 2 000 |
| кратность связывания (16-31) | 191 160 | 2 000 |
| способ подачи ссылки (16-32, 16-34) | 272 400 | 2 000 |
| лексика SQL (16-33) | 26 940 | 2 000 |
| класс конструктора колонки (16-33) | 154 224 | 2 000 |
| где прочитано имя обёртки, писатель (16-36) | 5 765 760 | 2 000 |
| где прочитано имя обёртки, приватность (16-37) | 4 193 280 | 2 000 |

**Не прогнано выборкой:** 10 921 438 форм полного перебора генераторов (10 941 438 − 20 000). Кроме того, только выборкой вошли:
- самопроверки 16-27…16-34 в прежнем виде — ≈550 000 форм;
- (е) 16-36 — 34 243 формы;
- (е) 16-37 — 16 634 формы.

Самопроверка этого плана (е) прогнана целиком.

**Строки итогового прогона** (`bash .pytest_cache/r7diff/run.sh 16-38`, HEAD `9ce79852`, 2026-10-19 ≈10:37–10:52 UTC, выход 0) — дословно:

```
SELFTEST 1bebbbf7 -> c6953017: cells=2550 regressions=43 fixed=192 changed=235
SELFTEST 5e32c335 -> 147f5e46: cells=2550 regressions=52 fixed=145 changed=198
DIFF 1da1b993 -> 3a7fe75b: cells=32970 regressions=0 fixed=962 changed=962
DIFF 3b503f81 -> b953ce0d: cells=32970 regressions=219 fixed=506 changed=725
DIFF 0b50a4de -> d7013797: cells=32970 regressions=0 fixed=0 changed=0
DIFF 9f804a44 -> 85ac9a2e: cells=32970 regressions=0 fixed=436 changed=436
DIFF 269b9218 -> 9ce79852: cells=32970 regressions=0 fixed=8 changed=8
BASE 9a92efd9 -> HEAD 9ce79852: cells=32970 regressions=0 fixed=1693 changed=1693
OPEN_REGRESSIONS=0
```

**Регрессия GREEN задачи 2 (`b953ce0d`): 219 ячеек**, верных у родителя `3b503f81` и неверных на `b953ce0d`:
- 216 ячеек (е): обёртка журнала × `pool.imap` / `pool.imap_unordered` / `pool.map_async` × 6 не-литеральных форм × 12 форм связывания;
- три строки `NEGATIVE_CONTROLS`: `named-carrier-wrapper-imapped-over-a-comprehension-of-phones`, `carrier-wrapper-imap-unordered-over-a-phone-attribute`, `carrier-wrapper-map-async-over-a-phone-name`.

Причина: задача 2 сделала эти носители поэлементными, и поданная им обёртка потеряла итерируемую целиком. До плана они судились целиком как «прочие» носители.

Закрыл GREEN `85ac9a2e` (заход 1, RED `9f804a44` со строкой `imap`). Строки, повторяющие ячейки двух других носителей, — закрепки в RED `269b9218`. На HEAD все 219 верны (`OPEN_REGRESSIONS=0`).

Исходный корпус без (е) регрессию не видел: прогоны после задач 1–3 дали по каждому `DIFF` `regressions=0`. Она проявилась, когда в корпус вошла самопроверка.

**Промежуточные прогоны** (все с выходом 0):

| После | HEAD | Корпус | sha | Строки |
|-------|------|--------|-----|--------|
| GREEN задачи 1 | `3a7fe75b` | 23 776 | `eca07b9b…` | `DIFF 1da1b993 -> 3a7fe75b: regressions=0 fixed=98`; `BASE … regressions=0`; `OPEN_REGRESSIONS=0` |
| GREEN задачи 2 | `b953ce0d` | 23 784 | `7bf2f8da…` | `DIFF 3b503f81 -> b953ce0d: regressions=0 fixed=38 changed=38`; `BASE … regressions=0 fixed=136` |
| GREEN задачи 3 | `d7013797` | 23 784 | — | `DIFF 0b50a4de -> d7013797: regressions=0 fixed=0`; `BASE … regressions=0` |
| GREEN захода 1 | `85ac9a2e` | 32 966, (е) вошла | `be124ffd…` | `DIFF 3b503f81 -> b953ce0d: regressions=217`; `DIFF 9f804a44 -> 85ac9a2e: regressions=0 fixed=434`; `BASE … regressions=0 fixed=1685`; `OPEN_REGRESSIONS=0` |

**Неверные ячейки на HEAD — не регрессии, неверны и на базе:**
- **(г): 50 ячеек `methodcaller` с получателем из не-литерала** (comprehension, `iter`, имя, `*`, `**`; 10 носителей). Ожидание источника (г) «имя с `phone` во фрагменте — находка» для значения `methodcaller` шире заявления: итерируемая подаёт получателей, а получатель из потока данных не опознан. По D-17 угадывания нет, поэтому это вне заявления, а не непойманная форма.
- **(д) «способ подачи ссылки»: 23 ячейки — артефакт реконструкции генератора.** В исходнике нет `phone`: строка `starmap` / `apply` собрана как `[('x',)]` / `['x']` без аргумента с номером, а у писателя — `insert(MessengerAccount)` без `.values(phone=…)`. Ожидание «находка» ложно. Генератор унаследован от 16-36 и не правился, чтобы не менять семейство посреди сверки.

## Files Created/Modified

- `tests/phone_gate_grammar.py`:
  - `ELEMENTWISE_CARRIERS` (4), `ROW_CARRIERS` (2) с комментарием;
  - `keep_iterables` в `_carried_by`, `reference_arguments`, `wrapper_applications`;
  - построчное прочтение без флага;
  - докстринги правил 5, 7, 8 и правила 4 `wrapper_applications`.
- `tests/test_phone_privacy_gate.py`:
  - `keep_iterables=True` в правиле носителя и в применениях обёртки, `every_reading=True` в пути `methodcaller`;
  - ввоз `ROW_CARRIERS`, комментарий ввоза;
  - трасер, 19 строк `NEGATIVE_CONTROLS`, 1 строка `POSITIVE_CONTROLS`;
  - места проверки в правиле шапки;
  - шапка: абзац носителя, пример `methodcaller`, летопись CR-02 / WR-25.
- `tests/test_application/test_phone_single_writer_gate.py` — ввоз `ROW_CARRIERS`, 2 строки `LITERAL_FORM_CASES`, фраза шапки, места проверки в правиле шапки.
- `tests/test_phone_gates_parity.py` — `ROW_CARRIERS` / `_ROW_CARRIERS` в `GRAMMAR_TABLES`, `MAP_CARRIER_OWNERS`, сторож.

## Decisions Made

См. `key-decisions`. Гейт писателя получил по таблицам и улучшение: `imap` / `imap_unordered` / `map_async` с comprehension, генератором или `list([…])` на месте колонки теперь ловятся. На базе 216 форм самопроверки промахивались. Ответ прежних строк и ячеек писателя не изменился: в каждом `DIFF` `changed` = `fixed` + `regressions`, а все 219 регрессий — у приватности.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающая функциональность] Обёртка журнала, поданная поэлементному носителю, не судила итерируемую целиком**
- **Found during:** задача 3, самопроверка, заход 1 (432 промаха).
- **Issue:** `wrapper_applications` подавала обёртке только элементы, поэтому `list(map(partial(ctx.run, logger.info), account.phones))` давал `[]`. Это то же заявление «итерируемые таких носителей гейт судит ЦЕЛИКОМ» на оси обёртки.
- **Fix:** `wrapper_applications(…, keep_iterables=False)` в общем модуле; гейт приватности зовёт её с `True`, и обёртка получает оба прочтения.
- **Files modified:** `tests/phone_gate_grammar.py`, `tests/test_phone_privacy_gate.py`.
- **Commit:** `9f804a44` / `85ac9a2e`.

**2. [Rule 1 — ошибка] Путь `methodcaller` гейта приватности уже, чем у гейта писателя: `partial(threading.Thread, target=mc)(args=(logger,))`**
- **Found during:** сверка «база ↔ HEAD» после задачи 2. Корпус (д) «способ подачи ссылки» дал 6 неверных ячеек; 16-37 передал их объёму 16-38.
- **Issue:** гейт писателя форму-двойник ловит, гейт приватности — нет. Это класс WR-25; верификатор предлагал `every_reading=True`.
- **Fix:** `_applied_log_methodcaller` зовёт `reference_arguments(…, every_reading=True)`. Правило 7 докстринга называет это прочтение вместо формулы плана «построчное прочтение в пути `methodcaller`»: построчное у обоих гейтов есть и так. Проверка докстринга плана (`docstring_t2.py`) — `OK`.
- **Files modified:** `tests/phone_gate_grammar.py` (докстринг), `tests/test_phone_privacy_gate.py`.
- **Commit:** `269b9218` / `9ce79852`.

**3. Регрессия GREEN задачи 2 (219 ячеек) — свой цикл, найдена (е)** — описана в разделе сверки. Закрыта `85ac9a2e`, строки-повторы — `269b9218`.

**4. Числа плана и замер (замер правит, строки не тронуты):**

| Что | План | Замер |
|-----|------|-------|
| гейт писателя после задачи 1 | ≥ 571 | **574** (прибавка 16-36) |
| три модуля после задачи 2 | ≥ 837 | **840** (писатель 576) |
| три модуля итог | ≥ 837 | **846** (приватность 254, паритет 16, писатель 576) |
| quick run фазы | ≥ 1241 | **1250** |
| `NEGATIVE_CONTROLS` / `LITERAL_FORM_CASES` | ≥ 139 / ≥ 243 | **145 / 246** |
| `POSITIVE_CONTROLS` | ≥ 51 | **51** |

**5. Ледгер плана** (`gsd-plan-head-before-16-38`, протокол 0c) записан в `.pytest_cache/`, а не в git-dir worktree: тот лежит под `.git` главного checkout, писать туда orchestrator_notes 2 запрещают. База — `9a92efd9`.

**6. Инструмент сверки (gitignored, коммитов нет):** seed 38, семейство `e-wrapper-read-1637`, (е) `selfcheck_1638.py`, помощники. Изменения перечислены в разделе сверки.

---

**Total deviations:** 2 исправлены автоматически (Rule 2, Rule 1). Оба — своими циклами test/feat с `run.sh` после каждого. Ещё одна регрессия закрыта циклом. Расхождение чисел плана и инструмент описаны выше.
**Impact on plan:** правки только в `files_modified`. Реестры, заявления шапок, прежние строки и JS-половина не тронуты.

## Замены команд (песочница worktree, хост)

- Команды `<automated>` / `acceptance_criteria` с `python -c` записаны дословно в `.pytest_cache/checks/*.py` и запущены с `PYTHONPATH=.`: `rows_t1.py`, `acc_rows_t1.py`, `writer_reading_t1.py`, `tables_t2.py`, `rows_t2.py`, `docstring_t2.py`, `header_t3.py`, `registry_t3.py`. Логика та же. Добавлены `writer_live.py` (`OK 6 104`), `js_t3.py` (`OK 23 0`: 23 JS-символа модуля равны базе плана) и `probe_s2.py` (зонд цикла сверки).
- Песочница отклонила: составную команду с git (сторожа 0a/0b шли отдельными командами) и цикл `for` вокруг `uv run`. Цепочка `git show 65e5c692:… > …; python -c` разделена на две простые команды.
- Полную суиту (~46 мин) не гнал: её гоняет оркестратор после слияния.
- `graphify update .` не запускал (orchestrator_notes). Ориентация — `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.

## Гейты на итоговом дереве (`9ce79852`, 2026-10-19, под `flock`)

| Гейт | Итог | До плана |
|------|------|----------|
| `test_phone_privacy_gate.py` + гейт писателя + `test_phone_gates_parity.py` | 846 passed | 822 |
| гейт писателя отдельно | 576 passed | 574 |
| гейт приватности отдельно | 254 passed | 233 |
| правило-паритет отдельно | 16 passed | 15 |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| живое дерево писателя | `OK 6 104` | то же |
| quick run фазы (8 путей) | 1250 passed | 1226 |
| `tests/test_application` | 861 passed | 859 |
| сквозные гейты (htmx_post_pairs, htmx_gates, test_templates, declared_invariants) | 576 passed | 576 |
| `tests/test_logging_config.py` | 3 passed | 3 |
| `compileall -q app main.py tests` | код 0 | код 0 |
| `scripts/prohibitions_census.py --check` | код 0, «реестр: 856 строк, биекция с переписью — согласие» | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| task-1 #2 / acceptance | `OK 117 49 133 51` (задача 1), `OK 117 49 145 51` (итог) / `OK 145 51`, `OK writer reading unchanged` | — |
| task-2 #2 / acceptance | `OK ['imap', 'imap_unordered', 'map', 'map_async'] ['starmap', 'starmap_async']` / `OK 145 246`, `OK` | — |
| task-3 #2 / реестр / JS | `OK` / `OK` / `OK 23 0` | — |
| `run.sh 16-38` | выход 0, `OPEN_REGRESSIONS=0` | — |
| `tests/test_planning` | гонится после коммита сводки (финальное сообщение) | 218 passed, 2 skipped |

## TDD Gate Compliance

- `git log --grep='^test(16-38)'` — 5 коммитов: `1da1b993`, `3b503f81`, `0b50a4de`, `9f804a44`, `269b9218`.
- `--grep='^feat(16-38)'` — 5 коммитов: `3a7fe75b`, `b953ce0d`, `d7013797`, `85ac9a2e`, `9ce79852`.
- Каждый `test` стоит перед своим `feat`. REFACTOR-коммитов нет. Нарушений нет.

## Issues Encountered

Регрессия GREEN задачи 2 на оси обёртки. Ни правила суиты, ни исходный корпус сверки её не видели. Её показал корпус после входа самопроверки (е); закрыта до закрытия плана (см. сверку).

## Остатки и открытое (deferred-items.md не создавался — orchestrator_notes 5)

1. **(г): 50 ячеек `methodcaller` с получателем из не-литерала.** Ожидание источника шире заявления (D-17). 16-39 стоит сузить ожидание (г) для значения `methodcaller` до литеральных получателей или пометить такие ячейки «ноль».
2. **(д) «способ подачи ссылки»: 23 ячейки — артефакт генератора** (без `phone` в исходнике). 16-39 стоит поправить реконструкцию строк `starmap` / `apply` и API `insert`.
3. **Кандидатные строки словаря `starmap`, `apply-async`, `map-named-iterable`** — объём 16-39. Их ячейки (б) на HEAD верны у обоих гейтов.

## Known Stubs

Нет.

## Threat Flags

Нет: правились только тестовые гейты и общий модуль тестов.

## User Setup Required

None — внешней настройки нет.

## Next Phase Readiness

- **Вход 16-39:** общий модуль с `ROW_CARRIERS` и `keep_iterables`. Инструмент сверки лежит в `.pytest_cache/r7diff/`: `corpus.py` (seed 38, 10 семейств (д)), `judge.py`, `run.sh`, `selfcheck_1638.py`, `selfcheck_cells.json` (9 180), `selfcheck_cells_1637.json`, `trees/`, `judged/`.
- Фаза остаётся в `gaps_found` до 16-39, 16-40 и повторной верификации. PHONE-21 и PHONE-02 в REQUIREMENTS.md не отмечались.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-19*

## Self-Check: PASSED

- Файлы на месте: `tests/phone_gate_grammar.py`, `tests/test_phone_privacy_gate.py`, `tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_gates_parity.py`, `.pytest_cache/r7diff/{corpus.py,judge.py,run.sh,selfcheck_1638.py,selfcheck_cells.json}`.
- Коммиты плана в истории ветки: `1da1b993`, `3a7fe75b`, `3b503f81`, `b953ce0d`, `0b50a4de`, `d7013797`, `9f804a44`, `85ac9a2e`, `269b9218`, `9ce79852`. `git rev-list --count 9a92efd9..9ce79852` = 10.

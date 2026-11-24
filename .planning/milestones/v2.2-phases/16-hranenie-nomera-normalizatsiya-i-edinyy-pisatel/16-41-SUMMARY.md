---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 41
subsystem: testing
tags: [phone-privacy-gate, wr-27, count-axis, r8diff, ast, pytest, tdd]
status: complete

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-37 — `python_log_offences` с дедупликацией по тексту тройки (`51d0d766`); 16-39 — инструмент r7diff и словарь седьмого круга"
provides:
  - "Гейт приватности: место находки — узел подачи (строка, столбец, вид, предмет); две подачи на одной строке — две находки, одна подача по двум путям — одна"
  - "`NEGATIVE_CONTROL_PLACES`, `place_count_mismatch`, правило строк, считающее места, правило-контроль против дедупликации по тексту"
  - "Четыре строки `NEGATIVE_CONTROLS` WR-27 и трасер подложенного отчёта с двумя номерами"
  - "Матрица приватности — ровно одна находка на ячейку"
  - "Шапка гейта приватности: место «строка, столбец, вид, предмет», летопись WR-27"
  - "Инструмент `.pytest_cache/r8diff/` (gitignored): сверка «база ↔ HEAD» с осью счёта на обоих гейтах, `SELFTEST-COUNT`, `HEAD_WRONG`, `count_regressions`, `REPAIRED`"
affects: [16-42, 16-43, 16-44, 16-45]

actuals:
  tokens: 39415   # chars/4: диф `tests/test_phone_privacy_gate.py` (28 989 симв.) + файлы инструмента r8diff (128 671 симв., gitignored)
  tasks: 2
  commits: 4      # git rev-list --count fb8fef72..3d7dfd86 (до коммита сводки)
plan_head_before: fb8fef72bc4cdb034bd7e1e99b951cd993667825
plan_head_after: 3d7dfd8627964ed57a34eb292da8be3a81c0a8d1

tech-stack:
  added: []
  patterns:
    - "Место находки гейта приватности — четвёрка (lineno, col_offset, вид, предмет) узла; дедупликация — по четвёрке"
    - "Правило счёта сверяет число находок с таблицей ожидаемых мест, выведенной чтением исходника, а не выход той же дедупликации"
    - "Сверка «база ↔ HEAD» с двумя осями: наличие и число находок; против вакуума — SELFTEST (наличие) и SELFTEST-COUNT (счёт)"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Место находки — узел (строка и столбец), текст находки прежний: две находки одной строки печатаются одинаково, как у гейта писателя"
  - "Ожидание по числу у семейств (д) прежних инструментов: `phone_unique` → число вставленных узлов с номером; `phone` / `subject_all` / `base*` / `equal` → `parent`"
  - "Самопроверка оси счёта — полный крест 20 160 форм (18 438 годных) с безопасными двойниками, а не ротация"

patterns-established:
  - "r8diff: `expect.count` — `exact` / `range` / `twin` / `parent`; прежнее числовое поле `count` переехало в `n`"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Место находки гейта приватности — узел подачи: четыре формы WR-27 — по две находки, форма WR-24 — одна, каждая из 1 260 ячеек матрицы — одна; подложенный отчёт — две находки на одной строке"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_report_with_two_numbers_on_one_line_reddens_the_gate_twice"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (149 строк)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_every_binding_form_of_a_log_reference_is_judged (12 форм)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK [2, 2, 2, 2] 1260"
        status: pass
    human_judgment: false
  - id: D2
    description: "Правило строк считает места по `NEGATIVE_CONTROL_PLACES`; контроль доказывает, что дедупликация по тексту места его краснит"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_place_count_rule_reddens_a_text_triple_dedupe"
        status: pass
    human_judgment: false
  - id: D3
    description: "Шапка и докстринг называют место «строка, столбец, вид, предмет»; летопись WR-27"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_header.py → OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Сверка «база ↔ HEAD» по обеим осям: SELFTEST 47 / 56, SELFTEST-COUNT 1 237, DIFF и BASE — ноль обеих осей, OPEN_REGRESSIONS=0"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "bash .pytest_cache/r8diff/run.sh 16-41 (HEAD 3d7dfd86, выход 0)"
        status: pass
    human_judgment: false

duration: 42min
completed: 2026-10-19
---

# Фаза 16, план 41: место находки гейта приватности — узел подачи (WR-27) — сводка

**Находка гейта приватности стоит на узле подачи номера — четвёрка (строка, столбец, вид, предмет). Две подачи на одной строке дают две находки, одна подача, судимая по двум путям, — одну. Правило строк считает места по `NEGATIVE_CONTROL_PLACES`, и возврат дедупликации по тексту его краснит. Инструмент r8diff сверяет каждый GREEN с родителем по наличию и по числу находок у обоих гейтов.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-10-19T20:03:53Z
- **Completed:** 2026-10-19T20:45:26Z
- **Tasks:** 2 (оба `tdd`; циклов самопроверки и сверки — ноль: регрессий и промахов нет)
- **Files modified:** 1 (`tests/test_phone_privacy_gate.py`)

## Accomplishments

- `_judge_arguments` возвращает четвёрки `(строка, столбец, вид, предмет)`: столбец — `col_offset` узла находки. Это имя, атрибут, строковая константа, ключ словаря, `mask_phone(…)` или именованный аргумент. Синтетический `ast.keyword` несёт место ключа.
- `python_log_offences` не повторяет четвёрку. Обёртка, судимая на месте связывания и на месте применения, указывает на тот же узел — одна находка (WR-24 не возвращается). Разные узлы одной строки — разные находки (WR-27 закрыт). Текст находки прежний.
- Четыре строки `NEGATIVE_CONTROLS` WR-27: `two-numbers-in-one-log-call`, `log-call-and-print-on-one-line`, `print-of-two-numbers`, `two-log-calls-on-one-line`. Каждая даёт ровно две находки.
- Таблица `NEGATIVE_CONTROL_PLACES` — 14 строк: девять «ключ `phone=` и значение» и четыре WR-27 — по 2, `log-wrapper-with-arguments-called-once-per-place` — 1. Помощник `place_count_mismatch`. Правило строк сверяет число находок с числом мест.
- Правило-контроль `test_the_place_count_rule_reddens_a_text_triple_dedupe`: выход, слитый по тексту места, даёт расхождение на всех четырёх строках WR-27.
- Матрица приватности требует ровно одну находку на ячейку, как у гейта писателя.
- Трасер `test_a_planted_report_with_two_numbers_on_one_line_reddens_the_gate_twice` проверяет `app/services/phone_report.py:7 — имя — phone (владелец report)` дважды.
- Шапка: предложение «Одно место — одна находка» определяет место как «строка, столбец, вид, предмет». Добавлена летопись WR-27.
- Инструмент `.pytest_cache/r8diff/` собран по договору `<scope_note>`, оставлен в worktree для 16-42…16-44.

## Task Commits

1. **Задача 1, RED** — `597f1220` `test(16-41): add failing place-count rules for two submissions on one line (WR-27)`
2. **Задача 1, GREEN** — `41f07251` `feat(16-41): place a privacy finding on its submission node, line and column (WR-27)`
3. **Задача 2, RED** — `87d2c5d1` `test(16-41): require the privacy header to name the place as line, column, kind, subject (WR-27)`
4. **Задача 2, GREEN** — `3d7dfd86` `feat(16-41): name the privacy finding place as line, column, kind, subject in the header (WR-27)`

Коммит сводки — `docs(16-41)`, следующий за этими.

## TDD: RED / GREEN

### Задача 1

**RED.** Команда: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k "two_numbers_on_one_line or two-numbers or one-line or print-of-two" --junit-xml=.pytest_cache/gsd-red/task1-red.xml`, выход 1. Все три признака на месте:
- строка `FAILED tests/test_phone_privacy_gate.py::test_a_planted_report_with_two_numbers_on_one_line_reddens_the_gate_twice`;
- последняя строка сводки — `5 failed, 255 deselected, 1 warning in 0.69s`;
- литерал правила счёта — `число находок строки не равно числу её мест: строка `two-numbers-in-one-log-call`: мест 2, находок 1`. Литерал трасера — «две подачи номера на одной строке слиты в одну находку».

Улика — `.pytest_cache/gsd-red/task1-red.json` (JUnit внутри, gitignored). `gsd-tools check tdd-red-evidence` вернул `RED_EVIDENCE_OK` / `target_test_failed`, цель — трасер.

Смысловая оценка: цель исполнилась и упала на утверждении о числе находок — одна вместо двух. Это не ошибка сбора и не ошибка ввоза. Четыре строки WR-27 упали на том же утверждении правила счёта.

Весь модуль на RED: `6 failed, 271 passed`. Шестой красный — правило-контроль: его часть (в) требует, чтобы настоящий выход строк WR-27 не расходился с числом мест. Закрепки (зелёные до GREEN):
- строка WR-24 `log-wrapper-with-arguments-called-once-per-place`;
- девять строк «ключ и значение»;
- матрица — 12 форм, все 1 260 ячеек по одной находке.

**GREEN.** Место — четвёрка узла. Модули приватности и паритета — `277 passed`.

### Задача 2

**RED.** Команда: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier --junit-xml=.pytest_cache/gsd-red/task2-red.xml`, выход 1. Признаки:
- `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier`;
- `1 failed, 259 deselected, 1 warning in 0.50s`;
- литерал «шапка гейта приватности не называет носителя ссылки и общую грамматику» — шесть пунктов: определение места, WR-27, `51d0d766`, О-18 (а), столбец в предложении об одном месте, летопись WR-27.

`RED_EVIDENCE_OK` (`.pytest_cache/gsd-red/task2-red.json`). Цель упала на утверждении о шапке.

Закрепка: проверка докстринга `python_log_offences` уже зелёная. Докстринг переписал GREEN задачи 1 — так требует действие задачи 1 плана.

**GREEN.** Текст шапки. Три модуля гейтов — `853 passed`.

## Самопроверка исполнителя (задача 2; О-18 (а), свойства 4, 5)

Скрипт — `.pytest_cache/r8diff/selfcheck_1641.py` (gitignored, в репозиторий не коммитится). Он однопроцессный и гонится под общим `flock`. Каждая форма подаётся в `python_log_offences(…, "app/x.py")`. Прогон — 2026-10-19, ≈20:26 UTC, HEAD `3d7dfd86`.

**Оси (полный крест, без ротации — 8 × 2 × 21 × 5 × 12 = 20 160 сочетаний):**
- **Форма пары (8):**
  - два номера в одном вызове;
  - два вызова журнала через `;`;
  - вызов журнала и `print` через `;`;
  - `print`-форма двух номеров без формата;
  - одна подача дважды;
  - именованный `phone=` с номером;
  - два именованных с номером (`phone=`, `phone_number=`);
  - словарь `extra=` с двумя ключами `phone*`.
- **Раскладка (2):** одна строка; две строки. У пар из двух операторов — второй оператор с отступом места, у пар внутри вызова — перенос аргументов внутри скобок.
- **Способ подачи (21):** прямой вызов и 20 `REFERENCE_CARRIERS`.
- **Значение опознания (5):** `LOG_IDENTIFICATION_VALUES`. Пара — в аргументах применения; у `partial` первый аргумент связан в `partial`; у `methodcaller` пара — в его аргументах.
- **Форма (12):** `BINDING_FORMS`.

**Ожидание** — точное число мест, которое считает генератор. Это число вставленных им узлов с номером и ключей `phone*` в исходнике формы: регулярное выражение `INSERTED` по тексту, а не выход гейта. Номер, вставленный один раз в значение связывания, — одно место при любом числе применений. Безопасный двойник (номера и ключи заменены не-номером) — ноль.

| Заход | Дерево | Форм (под заявлением / двойников) | Ожидание 0 / 1 / 2 / 4 | Промахов | Итог |
|-------|--------|-----------------------------------|------------------------|----------|------|
| 1 | HEAD `3d7dfd86` | 36 876 (18 438 / 18 438) | 36 / 440 / 15 661 + 117 с ожиданием 3 / 2 184 | 117 | артефакт ожидания генератора (ниже) |
| 2 (итог) | HEAD `3d7dfd86` | **36 876 (18 438 / 18 438)** | 36 / 440 / 15 778 / 2 184 | **0** | ячейки ушли в корпус (е) |
| контроль против вакуума | дерево `597f1220` (родитель GREEN задачи 1) | 36 876 | — | 6 252 | генератор видит WR-27 там, где он был |

Контроль по классам:
- `two-in-call` — 1 200 (ожидание 2, гейт 1);
- `two-keywords` — 1 092 (4 / 3);
- `two-calls` — 1 016;
- `call-and-print` — 980;
- `print-two` — 980 + 4;
- `same-twice` — 980.

Все на одной строке.

**Заход 1 — артефакт ожидания, а не дефект гейта.** Подмена значения `partial` в генераторе была `functools.partial(helper.noop, {first})`. У пары `print-two` первым аргументом стоит `a.phone`, и номер попадал в подмену — не-журнальный вызов форм `rebound*`. Генератор считал этот узел, гейт законно молчал: 117 форм `print-two × partial × rebound*`, ожидание 3, гейт 2. Подмена стала `functools.partial(helper.noop, "x")`. Гейт не правился, цикла RED/GREEN нет.

Там же 36 форм с ожиданием 0 получили вид `zero`: `starmap` теряет именованные аргументы, и пара не вставляется.

**По осям (заход 2, обе стороны):**
- пары — от 3 920 (`same-twice`) до 4 992 (`two-in-call`);
- раскладки — 18 496 / 18 380;
- способы — по 1 876, у `map-named-iterable` 624, у `starmap` 1 372, у носителей с `{positional}` / `{keywords}` 1 732;
- значения — 6 800 (`methodcaller`), 6 820 (`partial`), по 7 752;
- формы — по 3 066, у `direct` 3 150.

Не собрано 1 722 сочетания: `partial` без позиционного остатка; разнос, невозможный внутри скобок.

**Найдено:** ничего. Циклов самопроверки нет. В корпус (е) вошла равномерная выборка 20 000 из 36 876 форм (`random.Random(41)`). Целиком самопроверка прогнана отдельно, оба захода выше.

## Сверка «база ↔ HEAD» с осью счёта (свойство 6 О-18 (а); пункт 5 договора `<scope_note>`)

**Инструмент.** Основа — копия r7diff 16-39 (`scratchpad/seed/r7diff-16-39/`: `corpus.py`, `judge.py`, `run.sh`, `selfcheck_1639.py`). Каждая часть сверена с договором `<scope_note>` этого плана. Изменения:
- **`corpus.py`.**
  - `SEED = 41`.
  - У каждой ячейки `expect.count` — `exact` / `range` / `twin` / `parent`. Прежнее числовое поле `count` ожиданий `count` и `equal` переехало в `n`.
  - (а) строки `NEGATIVE_CONTROLS` — `exact` из `NEGATIVE_CONTROL_PLACES` дерева HEAD. У дерева без таблицы — 2 у девяти строк «ключ и значение», иначе 1.
  - (б) кандидаты раунда 8: форма `getattr-read` и значение `methodcaller-receiver` у обоих гейтов, API писателя `__set__`. Таблицы `API_IDENTIFICATION_CALLS` на дереве нет — по договору `set_committed_value`.
  - (в) шестнадцать форм раунда 8.
  - Новые семейства: (ж) `g-double`, (з) `h-safe`, (д) `e-final-1639` (генератор `fam1639.py` — копия `selfcheck_1639.py` без суда).
  - Ожидания `unique` / `phone_unique` заменены числом мест (`derived_count`: у `phone_unique` — число вставленных узлов с номером).
- **`judge.py`.**
  - Вердикт — наличие И число; двойник судится тем же деревом.
  - `--compare` печатает `count_regressions`, `repaired_overcount` и перечни `REGRESSED` / `COUNT_REGRESSED` / `REPAIRED`.
  - Новые режимы `--wrong` (`HEAD_WRONG`) и `--open`.
- **`run.sh`.**
  - `SELFTEST` на семействах (б) и (в).
  - `SELFTEST-COUNT 51d0d766^ -> 51d0d766` на (а) строках приватности, (в) и (ж).
  - `DIFF` по каждому `feat(16-41)`, `BASE`, `HEAD_WRONG`, `OPEN_REGRESSIONS` с родительским числом находок в `regressed.tsv`.
  - Режимы `--against` и `--against-batch`.
  - Код выхода 1: при нуле `SELFTEST` / `SELFTEST-COUNT`; при регрессиях любой оси в `BASE` или `AGAINST`; при `OPEN_REGRESSIONS > 0`; если нет GREEN.

Деревья и кеш вердиктов — `.pytest_cache/r8diff/trees/` и `judged/`. Они оставлены на месте для 16-42…16-44.

**Корпус итогового прогона:** HEAD `3d7dfd86`, 58 394 ячейки, `corpus.json` sha256 `43719bc3754cee29e812d948b41b00ab85b44eb878ab6f7a2123230592283631`.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 246, `LEGITIMATE_CASES` 98, `NEGATIVE_CONTROLS` 149, `POSITIVE_CONTROLS` 51 | 544 |
| (б) матрицы | `b-matrix`: 12 `BINDING_FORMS` × 5 значений × 21 способ × 2 гейта = 2 520; `b-candidate`: (`getattr-read` × 6 значений + 12 форм × `methodcaller-receiver`) × 21 × 2 = 756 | 3 276 |
| (в) формы ревью | раунд 7 — 30, раунд 8 — 16 (WR-28 W-1, W-2, W-c1, W-c2, P-1, P-2, P-c; WR-27-1…4 и их двойники на двух строках; IN-20) | 46 |
| (г) дифференциал | 5 значений × 7 форм аргументов × 10 носителей × 2 гейта, по числу — `parent` | 700 |
| (д) выборка самопроверок | 12 семейств по 2 000 | 24 000 |
| (ж) две подачи на одной строке | для каждой ячейки (б): D1 (подачи различаются; `twin` + `exact` 2) — писатель 1 134, приватность 1 134; D2 (совпадают; `twin`, `exact` null) — 504 + 504 | 3 276 |
| (з) безопасные двойники | (б) 3 276 + (ж) 3 276, `exact` 0 | 6 552 |
| (е) самопроверка 16-41 | выборка 20 000 из 36 876 (seed 41) | 20 000 |

Виды ожидания по числу: `exact` 47 843, `twin` 3 276, `parent` 7 223, `range` 52.

**Правило выборки (д):** равномерно, без повторов, `random.Random(41)`, ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием. Семейство 16-39 материализуется и выбирается по позиции.

| Семейство (план) | Полный перебор | Прогнано |
|------------------|----------------|----------|
| ось B (16-27) | 70 840 | 2 000 |
| ось A (16-22, 16-28) | 48 264 | 2 000 |
| ось SQL (16-28) | 11 390 | 2 000 |
| носитель журнала (16-29) | 234 900 | 2 000 |
| кратность связывания (16-31) | 191 160 | 2 000 |
| способ подачи ссылки (16-32, 16-34) | 272 400 | 2 000 |
| лексика SQL (16-33) | 26 940 | 2 000 |
| класс конструктора колонки (16-33) | 154 224 | 2 000 |
| где прочитано имя обёртки, писатель (16-36) | 5 765 760 | 2 000 |
| где прочитано имя обёртки, приватность (16-37) | 4 193 280 | 2 000 |
| итерируемая носителя (16-38) | 22 680 | 2 000 |
| итог партии раунда 7, части A, B, C (16-39) | 82 035 | 2 000 |

**Не прогнано выборкой:** 11 049 873 формы полного перебора генераторов (11 073 873 − 24 000). Ещё 16 876 форм самопроверки 16-41 не вошли в корпус; сама самопроверка прогнана целиком.

**Строки итогового прогона** (`bash .pytest_cache/r8diff/run.sh 16-41`, HEAD `3d7dfd86`, 2026-10-19 20:27:58–20:37:54 UTC, выход 0) — дословно:

```
CORPUS_SHA256=43719bc3754cee29e812d948b41b00ab85b44eb878ab6f7a2123230592283631 HEAD=3d7dfd8627964ed57a34eb292da8be3a81c0a8d1
SELFTEST 1bebbbf7 -> c6953017: cells=3322 regressions=47 count_regressions=47 fixed=208 repaired_overcount=0 changed=255
SELFTEST 5e32c335 -> 147f5e46: cells=3322 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3522 regressions=831 count_regressions=1237 fixed=26 repaired_overcount=2 changed=1317
DIFF 597f1220 -> 41f07251: cells=58394 regressions=0 count_regressions=0 fixed=4536 repaired_overcount=0 changed=7015
DIFF 87d2c5d1 -> 3d7dfd86: cells=58394 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE fb8fef72 -> HEAD 3d7dfd86: cells=58394 regressions=0 count_regressions=0 fixed=4536 repaired_overcount=0 changed=7015
HEAD_WRONG=130
OPEN_REGRESSIONS=0
```

**Промежуточный прогон** — после GREEN задачи 1. HEAD `41f07251`, корпус 38 394 ячейки без (е), sha `5d2215ee6a35fa30ba7b859cac01fc534405839ed33d4c97eec5f0cf59cc0be2`, 20:16:09–20:21:32 UTC, выход 0:
- те же `SELFTEST` 47 / 56;
- `SELFTEST-COUNT … count_regressions=1237 repaired_overcount=2`;
- `DIFF 597f1220 -> 41f07251: cells=38394 regressions=0 count_regressions=0 fixed=1142`;
- `BASE fb8fef72 -> HEAD 41f07251: … regressions=0 count_regressions=0`;
- `HEAD_WRONG=130`, `OPEN_REGRESSIONS=0`.

**SELFTEST-COUNT видит ровно класс WR-27:**
- `COUNT_REGRESSED`:
  - строки `a-negative`: `two-numbers-in-one-log-call`, `log-call-and-print-on-one-line`, `print-of-two-numbers`, `two-log-calls-on-one-line` (2 → 1);
  - формы `c-review` WR-27-1…4 (2 → 1);
  - 1 229 ячеек (ж) приватности.
- `REPAIRED` (класс WR-24 — одно место дважды, задуманная починка `51d0d766`):
  - `a-negative::log-wrapper-with-arguments-called-once-per-place` 2 → 1;
  - `c-review::WR-24-2` 2 → 1.

Это совпадает с замером верификатора раунда 8: 954 ячейки с меньшим числом находок, из них 2 — задуманная починка WR-24.

**Регрессий нет** ни на одном GREEN, ни по наличию, ни по счёту. `REPAIRED` на GREEN плана — 0. Циклов сверки не было.

**`DIFF 597f1220 -> 41f07251`: fixed 4 536** — ячейки, неверные у родителя и верные у GREEN:
- (ж) D1 приватности — 1 134;
- четыре строки WR-27;
- четыре формы WR-27 (в);
- 3 394 ячейки выборки (е).

Остальные из `changed` 7 015 — рост числа находок у ячеек `parent` / `range`, например `phone=a.phone, phone_number=b.phone`: 3 → 4.

**Неверные ячейки на HEAD (`HEAD_WRONG=130`)** — только WR-28, объём следующих планов партии:
- `b-candidate` писателя `getattr-read × methodcaller-receiver` — 21, и (ж) D2 той же оси — 21. Это 16-42 (один читатель имени) и 16-44 (значение `methodcaller-receiver` в таблице писателя).
- `b-candidate` приватности `getattr-read × methodcaller` и `× methodcaller-receiver` — 42, и (ж) D2 — 42. Это 16-43 (и 16-44 для словаря).
- `c-review::WR-28-W-1`, `WR-28-W-2` — 16-42; `WR-28-P-1`, `WR-28-P-2` — 16-43.

Контроли WR-28 (`W-c1`, `W-c2`, `P-c`) на HEAD верны. Семейства (а), (б) из словаря, (г), (д), (з) и (е) неверных ячеек не имеют.

## Гейты на итоговом дереве (`3d7dfd86`, под общим `flock`)

| Проверка | Итог | База (`8aabdb38` / `fb8fef72`) |
|----------|------|--------------------------------|
| `<automated>` задачи 1 №1: приватность + паритет | `277 passed` | 271 |
| `<automated>` задачи 1 №2 (`t1_rows.py`) | `OK 145 51 149 51` | — |
| `<automated>` задачи 1 №3 (`t1_forms.py`) | `OK [2, 2, 2, 2] 1260` | — |
| приёмка задачи 1, таблица мест (`t1_places.py`) | `OK 149 14` | — |
| `<automated>` задачи 1 №4: гейт писателя | `576 passed` | 576 |
| `<automated>` задачи 2 №1: три модуля гейтов | `853 passed` | 847 |
| `<automated>` задачи 2 №2 (`t2_header.py`) | `OK` | — |
| quick run фазы (8 путей) | `1257 passed` | 1251 |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| живое дерево писателя (`writer_live.py`) | `OK 6 104` | то же |
| реестр (`t2_registry.py`): `PHONE_LOG_EXCEPTIONS == {}`, потолок 0 | `OK` | то же |
| JS-половина (`t2_js.py`) | `OK 27 0` | — |
| `tests/test_application` | `861 passed` | 861 |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `test_templates`, `test_declared_invariants`) | `576 passed` | 576 |
| `tests/test_logging_config.py` | `3 passed` | 3 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, реестр 875 строк, биекция | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | `110 passed` | 110 |
| `run.sh 16-41` | выход 0 (строки выше) | — |

`tests/test_planning` гонится после коммита сводки; итог — в финальном сообщении исполнителя оркестратору.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`:
  - `_judge_arguments` — четвёрки;
  - `python_log_offences` — дедупликация по четвёрке, новый докстринг;
  - четыре строки WR-27, `NEGATIVE_CONTROL_PLACES`, `place_count_mismatch`;
  - правило строк со счётом мест, `WR27_ROWS`, `_merged_by_place_text`, правило-контроль;
  - матрица — ровно одна находка;
  - трасер;
  - шапка — предложение об одном месте и летопись WR-27;
  - правило шапки — пункты WR-27.

Инструмент сверки (gitignored, не коммитится, оставлен в worktree):
- `.pytest_cache/r8diff/` — `corpus.py`, `judge.py`, `run.sh`, `fam1639.py`, `selfcheck_1641.py`, `selfcheck_cells.json`, `wrongs.py`, `stats_r8.py`, `trees/`, `judged/`;
- `.pytest_cache/checks/*.py` — дословные `python -c` плана.

## Decisions Made

- Место — узел, текст находки прежний. Прежние правила, сверяющие текст находки, остались зелёными. Две находки одной строки печатаются одинаково, как у гейта писателя.
- Ожидание по числу у семейств (д) прежних инструментов выводится из ожидания по наличию. Там, где числа прежнее ожидание не несло (`phone`, `subject_all`, `base`, `base_kinds`, `equal`), стоит `parent`: судится только сравнение с родителем. `phone_unique` стал числом вставленных узлов с номером. На HEAD ни одна ячейка (д) с таким ожиданием не неверна.
- Самопроверка — полный крест осей, а не ротация: при 42 с на прогон крест дешевле.

## Deviations from Plan

### Расхождения «план ↔ замер» (записаны, ничего не ослаблено)

**1. Правило-контроль на RED красное, а не закрепка.** План (приёмка задачи 1) относил `test_the_place_count_rule_reddens_a_text_triple_dedupe` к закрепкам. Его часть (в) — «настоящий выход строк WR-27 расхождения не даёт» — до GREEN не выполняется: гейт давал одну находку. На RED замерено `6 failed`, на выборке `-k` приёмки — `5 failed` (N ≥ 5 выполнено). Правило не ослаблялось.

**2. Проверка докстринга `python_log_offences` в RED задачи 2 зелёная до GREEN.** Действие задачи 1 требует назвать место в докстринге, и GREEN задачи 1 это сделал. В RED задачи 2 эта часть — закрепка, красны шесть пунктов шапки.

**3. [Rule 1 — артефакт ожидания инструмента] Подмена `partial` в генераторе самопроверки несла номер.**
- Найдено: самопроверка задачи 2, заход 1, 117 форм.
- Исправлено в `selfcheck_1641.py` (gitignored). Гейт не правился, коммита нет.
- Проверка: заход 2 — 0 промахов, контроль на `597f1220` — 6 252.

### Замены команд (песочница worktree, заметки оркестратора 3, 4)

- `python -c` из `<automated>` и приёмки записаны дословно в `.pytest_cache/checks/` (`t1_rows.py`, `t1_forms.py`, `t1_places.py`, `t2_header.py`, `t2_js.py`, `t2_registry.py`, `writer_live.py`). Запуск — с `PYTHONPATH=.`.
- `git show 8aabdb38:tests/test_phone_privacy_gate.py > .pytest_cache/r8_base_privacy.py` — простой командой.
- Песочница отклонила heredoc и составные команды с `sed`-программами. Скрипты написаны инструментом Write, разбор — скриптами `wrongs.py` / `stats_r8.py`.
- `graphify query` и `graphify update .` не запускались: ориентация — чтением файлов по номерам строк плана. Обновление графа — за оркестратором после слияния.
- Полная суита (`just test`, ≈46 мин) не гонялась — её гонит пост-мердж гейт оркестратора на слитом дереве.

---

**Total deviations:** 3 записанных расхождения (2 — «план ↔ замер» без ослабления, 1 — артефакт ожидания инструмента), плюс замены команд.
**Impact on plan:** код гейта и ожидания строк не ослаблены, объём плана не превышен. Правились только `tests/test_phone_privacy_gate.py` и gitignored-инструмент.

## Issues Encountered

None — сверх отступлений выше проблем не было.

## Known Stubs

Нет.

## Threat Flags

Нет: правка только тестового гейта, новых поверхностей нет.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 16-42 (волна 2) начинает с копии инструмента `.pytest_cache/r8diff/`: `run.sh <план>` берёт план аргументом.
- Неверные на HEAD ячейки (130) расписаны по 16-42 / 16-43 / 16-44 выше. После 16-44 условие закрытия — `HEAD_WRONG=0`.
- Когда в общем модуле появятся `getattr-read` и `methodcaller-receiver`, кандидаты (б) перейдут в `b-matrix` сами: `in_dictionary` сверяет словарь дерева HEAD. С появлением `API_IDENTIFICATION_CALLS` (16-44) `writer_api` возьмёт API из таблицы.
- Отложенного нет; `deferred-items.md` не создавался.

## Self-Check: PASSED

- `tests/test_phone_privacy_gate.py` — FOUND; `.pytest_cache/r8diff/{corpus.py,judge.py,run.sh}` — FOUND.
- Коммиты `597f1220`, `41f07251`, `87d2c5d1`, `3d7dfd86` — предки HEAD (FOUND).
- `git rev-list --count fb8fef72..3d7dfd86` = 4; изменений вне коммитов нет (`git status --short` пуст).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-19*

---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 44
subsystem: testing
tags: [phone-single-writer-gate, phone-privacy-gate, parity, wr-28, in-18, in-19, getattr-read, methodcaller-receiver, r8diff, ast, pytest, tdd]
status: complete

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-41 — место находки приватности (узел), инструмент r8diff с осью счёта; 16-42 — `reading_name`, гейт писателя на нём; 16-43 — гейт приватности на `reading_name`, IN-20"
provides:
  - "Общий словарь: строка `BINDING_FORMS` `getattr-read` (чтение имени getattr-строкой) — 13 форм; обе матрицы и правило-паритет держат её для каждого значения и носителя"
  - "Значение опознания `methodcaller-receiver` у обоих гейтов на одной позиции; таблица `API_IDENTIFICATION_CALLS` гейта писателя — её читают правило-матрица и `_writer_finds` паритета; 13 × 6 × 21 = 1 638 ячеек на гейт"
  - "Правила-паритет `test_the_shared_dictionary_holds_the_round_eight_axes`, `test_the_parity_docstring_names_what_it_checks` (IN-19), `test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens` (IN-18)"
  - "Комментарии строк `named-wrapper-bound-handed` / `map-named-iterable`, летописи словаря седьмого круга и докстринг паритета разводят регрессии по матрицам; летопись словаря восьмого круга в обеих шапках"
  - "Итоговая самопроверка партии раунда 8 — 66 690 форм (писатель 33 480, приватность 33 210), 0 промахов; сверка «база ↔ HEAD» партии против базы партии, `1c243203` и `2f8c1656` — ноль регрессий обеих осей, `HEAD_WRONG=0`"
  - "Инструмент `.pytest_cache/r8diff/` (gitignored): режим `run.sh --rows`, `rows.py`, `selfcheck_1644.py`, (д) закреплён на словаре прежних самопроверок, ожидание по числу у D2 (ж)"
affects: [16-45]

actuals:
  tokens: 21600   # chars/4: диф четырёх файлов (47 965 симв.) + новые файлы инструмента (31 429) + правки corpus.py / run.sh (~7 000), gitignored-инструмент включён
  tasks: 3
  commits: 6      # git rev-list --count 24f644c4..dbc73537 (до коммита сводки)
plan_head_before: 24f644c46ed16d93598934915fa888310f5c0bb4
plan_head_after: dbc73537afd55f8129ac27a57a634c4600f1bd4e

tech-stack:
  added: []
  patterns:
    - "API, который называет находка ячейки матрицы писателя, — таблица модуля гейта `API_IDENTIFICATION_CALLS` без умолчания; правило-паритет читает её, своей копии не держит"
    - "Перечни докстринга правила-паритета сверяются с объектами самого модуля (имена таблиц и функции `test_*`), а не с константами правила"
    - "Источники (г) и (д) корпуса r8diff судят словарь своих самопроверок (12 форм, 5 значений): рост общего словаря не меняет их перебор и выборку"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_privacy_gate.py
    - tests/test_phone_gates_parity.py

key-decisions:
  - "Предикаты не правились: на базе плана `24f644c4` все 66 690 форм итоговой самопроверки и все 1 638 ячеек на гейт нового словаря уже верны (16-42 / 16-43); GREEN плана — строки словаря, таблица API и тексты"
  - "Семейства (д) и дифференциал (г) инструмента закреплены на 12 формах и 5 значениях: их генераторы читают таблицы дерева HEAD, и новая строка словаря меняла их полный перебор и выборку seed 42 (генератор 16-39 падал на значении без колонки-литерала)"
  - "Ожидание по числу у D2 (ж) — 1 место у писателя и число узлов номера у приватности вместо `exact: null` договора 16-41: строже прежнего; с ним сверка против `1c243203` и `2f8c1656` видит 2 → 1 класса WR-24 как REPAIRED (одно место, напечатанное у каждого применения), а не как регрессию счёта"
  - "Получатель журнала под именем модуля, прочитанный getattr-строкой, — по-прежнему открыт: оси восьмого круга его не порождают, план его не правит (16-43 — не место оси, починка ломает `logger.log`)"

patterns-established:
  - "Итоговая самопроверка партии раунда 8: чтение имени (4) × значение (6) × форма (13) × способ (21); две подачи на одной строке (D1, D2) и двойник на двух строках — тоже ячейки; безопасные двойники; суд — `judge.py` любым деревом"

requirements-completed: [PHONE-02, PHONE-21]

coverage:
  - id: D1
    description: "Форма `getattr-read` в общем словаре; обе матрицы и правило-паритет держат её для каждого значения и носителя; обе шапки её называют"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_shared_dictionary_holds_the_round_eight_axes"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_binding_form_of_a_writer_api_alias_is_judged[getattr-read]"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_every_binding_form_of_a_log_reference_is_judged[getattr-read]"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_agree_on_every_binding_form_identification_and_carrier[getattr-read]"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms_1644.py → OK 13 126"
        status: pass
    human_judgment: false
  - id: D2
    description: "Значение `methodcaller-receiver` у обоих гейтов на одной позиции, таблица `API_IDENTIFICATION_CALLS` полна; 1 638 ячеек на гейт без промахов"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_shared_dictionary_holds_the_round_eight_axes"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_matrix_1644.py → OK 1638"
        status: pass
    human_judgment: false
  - id: D3
    description: "IN-18 и IN-19: правила докстринга паритета и летописей словаря; числа IN-18 — с основанием и замером `run.sh --rows`"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_parity_docstring_names_what_it_checks"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens"
        status: pass
      - kind: other
        ref: "bash .pytest_cache/r8diff/run.sh --rows named-wrapper-bound-handed,map-named-iterable --at 147f5e46^,147f5e46,c6953017^,c6953017,HEAD (выход 0)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Итоговая самопроверка партии: 66 690 форм, 0 промахов на HEAD; контроль на базе партии — 21 125"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: ".pytest_cache/r8diff/selfcheck_1644.py + judge.py (рабочее дерево = dbc73537) → 66 690 / 66 690 верны"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сверка «база ↔ HEAD» партии: три DIFF, BASE и три AGAINST — ноль регрессий обеих осей; HEAD_WRONG=0, OPEN_REGRESSIONS=0; SELFTEST 48 / 56, SELFTEST-COUNT 885"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "bash .pytest_cache/r8diff/final_chain.sh (run.sh 16-44 && --against-batch 16-41 && --against 1c243203 && --against 2f8c1656), HEAD dbc73537, CHAIN_EXIT=0"
        status: pass
    human_judgment: false

duration: 2h37m
completed: 2026-10-20
---

# Фаза 16, план 44: словарь восьмого круга (`getattr-read`, `methodcaller-receiver`), IN-18 / IN-19 и итог партии раунда 8 — сводка

**Общий словарь матриц и правила-паритета читает связанное имя getattr-строкой (строка `getattr-read`, 13 форм), а значение `methodcaller-receiver` ставит колонку в получатель `methodcaller` у гейта писателя (с парой над журналом из вызова фабрики у гейта приватности). API значения писателя называет таблица `API_IDENTIFICATION_CALLS`; её читают правило-матрица и паритет. Матрицы: 1 638 ячеек на гейт, ноль промахов. Правила паритета держат IN-18 (какая регрессия какую матрицу краснит) и IN-19 (докстринг называет ровно проверяемое). Партия раунда 8 закрыта: итоговая самопроверка — 66 690 форм без промахов; сверка «база ↔ HEAD» против базы партии, `1c243203` и `2f8c1656` — ноль регрессий обеих осей и ноль неверных на HEAD ячеек.**

## Performance

- **Duration:** 2h37m
- **Started:** 2026-10-20T01:28:22Z
- **Completed:** 2026-10-20T04:05Z
- **Tasks:** 3 (все `tdd`); дополнительных циклов RED/GREEN нет — промахов и регрессий не найдено
- **Files modified:** 4 (`tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`)

## Accomplishments

- **Форма `getattr-read`** — строка `BINDING_FORMS` после строк повторного связывания. Класс `W`; в `__init__` — `self.f = {value}`; в `run` — `{use}`; ссылка `getattr(self, "f")`. Над строкой — летопись оси «где прочитано имя» (WR-28, О-18 (а), свойство 3). Обе матрицы и правило-паритет получили по параметру `[getattr-read]`.
- **Значение `methodcaller-receiver`:**
  - писатель — `operator.methodcaller("__set__", account, x)` с `(MessengerAccount.phone)`, подмена `operator.methodcaller("noop")`;
  - приватность — `operator.methodcaller("info", "x %s", account.phone)` с `(structlog.get_logger())`, та же позиция и `id`.
- **Таблица `API_IDENTIFICATION_CALLS: dict[str, str]`** гейта писателя: `set_committed_value` у пяти прежних значений, `__set__` у `methodcaller-receiver`. Правило-матрица писателя требует в предмете `API_IDENTIFICATION_CALLS[value.id]` и `phone`. `_writer_finds(source, call)` паритета получает API из таблицы; своей копии у паритета нет.
- **Правило `test_the_shared_dictionary_holds_the_round_eight_axes`** держит:
  - форму: ссылку, связывание в `__init__`, `{use}` в другом методе, чтение getattr-строкой в ячейке;
  - значение: обе позиции, `methodcaller("__set__", …)` над `MessengerAccount.phone`, номер в аргументах `methodcaller` у приватности;
  - полноту таблицы API без лишних ключей.
- **IN-19.** Правило `test_the_parity_docstring_names_what_it_checks` выводит перечни из объектов модуля: `REQUIRED_SHARED_NAMES`, `CARRIER_SEMANTICS`, `GRAMMAR_TABLES` без вариантов с подчёркиванием, `MAP_CARRIER_OWNERS` и каждую функцию `test_*` верхнего уровня исходника. Докстринг называет `wrapper_applications`, `ROW_CARRIERS`, сторожа stdlib и каждое из 11 правил.
- **IN-18.** Правило `test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens` проверяет четыре текста:
  - комментарий `named-wrapper-bound-handed`: «матрицу гейта писателя» и `147f5e46`, без «обе матрицы»; гейт приватности назван только зелёным;
  - комментарий `map-named-iterable`: «матрицу гейта приватности» и `c6953017`;
  - абзац докстринга паритета о словаре седьмого круга;
  - летописи словаря седьмого круга обеих шапок — `147f5e46` рядом с «матрицу гейта писателя», `c6953017` рядом с «матрицу гейта приватности», без «краснят обе матрицы».

  Числа с основанием: замер верификатора — 48 и 36 из 60; замер `run.sh --rows` этого плана — 52 и 39 из 78.
- **Обе шапки:**
  - абзац форм связывания называет `getattr-read` и значения опознания матрицы с `methodcaller-receiver`;
  - летопись словаря седьмого круга разведена по матрицам;
  - новая «Летопись словаря восьмого круга» называет 16-44, обе строки словаря, меру «база ↔ HEAD» и число находок, О-18 (а).
- **Итоговая самопроверка партии** — 66 690 форм, ноль промахов (раздел ниже).
- **Сверка «база ↔ HEAD» партии** по обеим осям — ноль регрессий против базы партии, `1c243203` и `2f8c1656`; `HEAD_WRONG=0` (раздел ниже).

## Task Commits

1. **Задача 1, RED** — `53f2483b` `test(16-44): require the getattr-read form in the shared dictionary and both gate headers (WR-28, O-18 (a) property 3)`
2. **Задача 1, GREEN** — `a3c8f299` `feat(16-44): add the getattr-read form to the shared dictionary and name it in both gate headers (WR-28, O-18 (a) property 3)`
3. **Задача 2, RED** — `cf27c862` `test(16-44): require the methodcaller-receiver value at both gates and a complete API_IDENTIFICATION_CALLS (WR-28, O-18 (a) property 3)`
4. **Задача 2, GREEN** — `ecfe3566` `feat(16-44): add the methodcaller-receiver value to both gates and the writer API table (WR-28, O-18 (a) property 3)`
5. **Задача 3, RED** — `c13c119b` `test(16-44): require the parity docstring to name what it checks and the chronicles to split the regressions by matrix (IN-18, IN-19)`
6. **Задача 3, GREEN** — `dbc73537` `feat(16-44): split the regressions by matrix and name every parity check; eighth-round dictionary chronicle (IN-18, IN-19, O-19)`

Коммит сводки — `docs(16-44)`, следующий за этими.

## TDD: RED / GREEN

Улики лежат в `.pytest_cache/gsd-red/` (gitignored): JUnit-отчёт, вывод консоли и запись JSON (`make_red.py`). `gsd-tools check tdd-red-evidence` вернул `RED_EVIDENCE_OK` / `target_test_failed` для каждого RED.

### Задача 1 (трасер; режим `end-of-phase`, `<verify>` только `<automated>` — повторён, «Tracer verified end-to-end — expanding»)

**RED.** Команда: `uv run pytest tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py -q -p no:randomly -k "round_eight_axes or header_names_the_shared"`, выход 1. Признаки:
- `FAILED tests/test_phone_gates_parity.py::test_the_shared_dictionary_holds_the_round_eight_axes`;
- `FAILED tests/test_application/test_phone_single_writer_gate.py::test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier`;
- `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier`;
- последняя строка сводки — `3 failed, 883 deselected, 1 warning in 0.94s`;
- литерал «шапка гейта писателя не называет общую грамматику связывания» (2 вхождения в выводе; в дереве до плана есть). Литерал этой задачи: «словарь матриц и паритета не держит ось восьмого круга» с пунктом «в `BINDING_FORMS` нет формы `getattr-read`».

Смысловая оценка: все три цели исполнились и упали на утверждениях плана: формы нет, шапки её не называют («нет формы словаря восьмого круга: нет «`getattr-read`»» — единственный пункт у каждой шапки). Ошибок сбора нет.

**GREEN.** Три модуля — `889 passed` (писатель 598, приватность 271, паритет 20). `t1_forms_1644.py` → `OK 13 105`.

### Задача 2

**RED.** Команда приёмки: `uv run pytest tests/test_phone_gates_parity.py -q -p no:randomly -k test_the_shared_dictionary_holds_the_round_eight_axes`, выход 1:
- `FAILED tests/test_phone_gates_parity.py::test_the_shared_dictionary_holds_the_round_eight_axes`;
- последняя строка сводки — `1 failed, 19 deselected, 1 warning in 0.53s`;
- литерал правила, записанного RED-коммитом задачи 1, — «словарь матриц и паритета не держит ось восьмого круга». Пункты: нет `methodcaller-receiver` у писателя, у приватности, нет таблицы `API_IDENTIFICATION_CALLS`.

Широкий прогон (`-k "round_eight_axes or header_names_the_shared"`) — `3 failed, 886 deselected`. Шапки — «нет значения словаря восьмого круга: нет «`methodcaller-receiver`»». Форма задачи 1 — закрепка, зелёная.

**GREEN.** Три модуля — `889 passed` (число правил не изменилось: значение — ячейки внутри прежних параметров). `t2_matrix_1644.py` → `OK 1638`.

### Задача 3

**RED.** Команда приёмки: `uv run pytest tests/test_phone_gates_parity.py -q -p no:randomly -k "docstring_names_what_it_checks or chronicles_name_which_matrix"`, выход 1:
- `FAILED tests/test_phone_gates_parity.py::test_the_parity_docstring_names_what_it_checks`;
- `FAILED tests/test_phone_gates_parity.py::test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens`;
- последняя строка сводки — `2 failed, 20 deselected, 1 warning in 0.60s`;
- литералы, записанные этим RED: «докстринг правила-паритета называет меньше, чем модуль проверяет (ревью IN-19)» и «летописи словаря не разводят, какая регрессия какую матрицу краснит (ревью IN-18)».

Смысловая оценка: RED дословно воспроизвёл находки ревью.
- IN-19: нет `wrapper_applications` (в обоих перечнях), `ROW_CARRIERS`, трёх объектов `MAP_CARRIER_OWNERS` и семи правил модуля.
- IN-18: комментарий `named-wrapper-bound-handed` говорит «обе матрицы» и не называет «матрицу гейта писателя». Три текста не разводят регрессии и говорят «краснят обе матрицы».

Правила шапок (`-k header_names_the_shared`) — `2 failed, 867 deselected`, «нет «Летопись словаря восьмого круга»».

**GREEN.** Три модуля — `891 passed` (писатель 598, приватность 271, паритет 22). `t3_header_1644.py` → `OK`.

Первый прогон GREEN задачи 3 дал `2 failed`: «летопись словаря восьмого круга не называет «число находок»». Текст говорил «по числу находок». Фраза дописана — «число находок у обоих гейтов не меньше, чем у родителя и у базы, кроме исправленного пересчёта одного места — класс WR-24». Коммит — после зелёного прогона.

## Замер `run.sh --rows` (IN-18)

Режим `run.sh --rows <строки> --at <ревизии>` (новый, `rows.py`) работает так:
- ячейки названных строк `REFERENCE_CARRIERS` собирают таблицы дерева HEAD: 13 форм × 6 значений = 78 на гейт;
- каждая ревизия судит их своим деревом в отдельном процессе;
- ячейка верна, как в правиле-матрице;
- `ROWS-NEW` печатается только у пары «родитель → коммит».

Прогон на итоговом HEAD `dbc73537` (2026-10-20 ≈03:52 UTC, выход 0) — дословно:

```
ROWS 147f5e46^: named-wrapper-bound-handed writer=1/78 privacy=2/78
ROWS 147f5e46^: map-named-iterable writer=1/78 privacy=41/78
ROWS 147f5e46: named-wrapper-bound-handed writer=53/78 privacy=2/78
ROWS 147f5e46: map-named-iterable writer=1/78 privacy=41/78
ROWS-NEW 147f5e46^ -> 147f5e46: named-wrapper-bound-handed writer=52 privacy=0
ROWS-NEW 147f5e46^ -> 147f5e46: map-named-iterable writer=0 privacy=0
ROWS c6953017^: named-wrapper-bound-handed writer=1/78 privacy=2/78
ROWS c6953017^: map-named-iterable writer=1/78 privacy=2/78
ROWS c6953017: named-wrapper-bound-handed writer=1/78 privacy=2/78
ROWS c6953017: map-named-iterable writer=1/78 privacy=41/78
ROWS-NEW c6953017^ -> c6953017: named-wrapper-bound-handed writer=0 privacy=0
ROWS-NEW c6953017^ -> c6953017: map-named-iterable writer=0 privacy=39
ROWS HEAD: named-wrapper-bound-handed writer=0/78 privacy=0/78
ROWS HEAD: map-named-iterable writer=0/78 privacy=0/78
```

Числа комментариев IN-18 — красные на коммите регрессии и зелёные на его родителе:
- `named-wrapper-bound-handed` на `147f5e46` — 52 из 78 у писателя, 0 у приватности;
- `map-named-iterable` на `c6953017` — 39 из 78 у приватности, 0 у писателя.

Фоновые красные старых деревьев — WR-28 (класс, закрытый 16-42 / 16-43): 1 у писателя (`getattr-read × methodcaller-receiver`), 2 у приватности (`getattr-read × methodcaller` и `× methodcaller-receiver`). Строка `map-named-iterable` красна на `147f5e46^`, потому что `c6953017` — его предок (как в таблице верификатора). Замер верификатора на 12 формах × 5 значениях — 48 / 0 и 0 / 36 из 60 — назван рядом в каждом тексте.

## Итоговая самопроверка партии (задача 3; О-18 (а))

Скрипт `.pytest_cache/r8diff/selfcheck_1644.py` — генератор; он лежит в gitignored-каталоге и в репозиторий не коммитится. Ячейки собирают таблицы дерева HEAD в формате корпуса. Судит их `judge.py` любым деревом, в отдельном процессе и под общим `flock`. Обе оси: наличие и число. Прогон — 2026-10-20 03:14–03:26 UTC (заход 2), код предикатов — HEAD `dbc73537` (рабочее дерево).

**Оси (полный крест, композиция под заявлениями обоих гейтов):**
- **Часть A.**
  - Чтение имени (4): как в форме; getattr-строкой (`self.f` → `getattr(self, "f")`, `cls.f` → `getattr(cls, "f")`, `f` → `getattr(sys.modules[__name__], "f")`); getattr-строкой с умолчанием `None`; цепочкой `g = getattr(<obj>, "f"); …g…`.
  - × каждое значение опознания гейта (6).
  - × каждая форма `BINDING_FORMS` (13).
  - × прямой вызов и каждый из 20 носителей.
- **Часть B.** Две подачи на одной строке × те же чтения, значения, формы и носители. Вторая подача: `account` → `other`, у писателя ещё `x` → `y`. D1 — подачи различаются, D2 — совпадают. Двойник на двух строках — тоже ячейка.
- **Часть C.** Безопасные двойники частей A и B:
  - писатель — `"phone"` → `"status"`, `MessengerAccount.phone` → `MessengerAccount.status`;
  - приватность — `.phone(s)` → `.name(s)`.

**Ожидание:**
- писатель:
  - A — ровно одна находка `KIND_SETATTR`, называющая API значения (`API_IDENTIFICATION_CALLS`) и `phone`;
  - B — все находки того же вида, число равно числу у двойника; D1 — ровно 2, D2 — ровно 1 (запись целиком в значении связывания — одно место);
  - C — ноль;
- приватность:
  - A и B — находки называют `phone`, их число равно числу мест: узлов номера `account.phone(s)` и `other.phone(s)` в исходнике; B — ещё и числу у двойника;
  - C — вызов журнала (`python_log_calls` непуст) без находки.

| Заход | Дерево | Форм (писатель / приватность) | Неверных | Итог |
|-------|--------|-------------------------------|----------|------|
| 1 | HEAD `dbc73537` (рабочее дерево) | 66 690 (33 480 / 33 210) | **0** | у D2 писателя ожидание было `twin` без числа — см. отступление 4 |
| 2 (итог) | HEAD `dbc73537` | **66 690 (33 480 / 33 210)** | **0** | D2 писателя — `exact` 1; ячейки ушли в корпус (е) |
| контроль против вакуума | база партии `fb8fef72` | 66 690 | **21 125** | генератор видит WR-27 и WR-28 там, где они были |
| контроль | база плана `24f644c4` | 66 690 | 0 | новый словарь ловился и до плана (16-42, 16-43) |

**По частям (на гейт):**

| Часть | Писатель | Приватность |
|-------|----------|-------------|
| A | 5 580 | 5 535 |
| B, на одной строке | 5 580 (D1 4 158, D2 2 016 до отбора повторов) | 5 535 |
| B, двойник на двух строках | 5 580 | 5 535 |
| C (двойники A, B на одной строке, B на двух) | 16 740 | 16 605 |
| итого | **33 480** | **33 210** |

**Число находок на HEAD** (под заявлением):
- писатель — A: 5 580 по одной; B: 3 820 по две (D1) и 1 760 по одной (D2) в каждой из двух раскладок;
- приватность — A: 5 535 по одной; B: 3 775 по две и 1 760 по одной.

**Не собрано и отброшено как повтор исходника:**
- у формы `direct` нет имени — только «как в форме», по 18 сочетаний на гейт;
- повторы — писатель 594, приватность 639 в части A (столько же в B):
  - 504 — форма `getattr-read` в каждом чтении дословно совпадает с `attribute-in-method`, прочитанной getattr-строкой;
  - 90 / 135 — `map-named-iterable` совпадает с `map` у значений с одним позиционным аргументом (у писателя 2 таких значения, у приватности 3).

**Контроль на `fb8fef72` по осям** (неверных):
- писатель: A 1 133, B 1 133 + 1 133, C 0;
- приватность: A 2 374, B 4 655 + 4 655, C 2 014 × 3;
- по значениям — писатель: имя / атрибут / getattr-строка по 693, `methodcaller-receiver` 1 320; приватность: имя / атрибут / getattr-строка по 3 402, `methodcaller` и `methodcaller-receiver` по 2 680, `partial` 2 160;
- по чтениям — писатель: цепочка 2 079, getattr и getattr с умолчанием по 660; приватность: как в форме 2 072, getattr и с умолчанием по 6 098, цепочка 3 458.

**Найдено:** ничего. Непойманных форм и неверных чисел под заявлениями нет; циклов самопроверки нет. Заход 1 → 2 — правка ожидания генератора, а не гейта (отступление 4).

**Вне осей (открыто, не правилось этим планом).** Пункт 16-43 — получатель журнала, связанный с ИМЕНЕМ модуля и прочитанный getattr-строкой. Зонд на HEAD `dbc73537` (`probe_receiver_module_getattr.py`):
- `lg = logging.getLogger(); getattr(sys.modules[__name__], "lg").info("x %s", account.phone)` → `[]`;
- `emit(getattr(sys.modules[__name__], "lg"))` при `emit = operator.methodcaller("info", "x %s", account.phone)` → `[]`;
- контроль `lg.info(…)` → одна находка.

Оси восьмого круга этой формы не порождают: получатель журнала не входит ни в форму `getattr-read`, ни в значение `methodcaller-receiver`. План её в объём не берёт; 16-43 отнёс получатель к не-местам оси, а очевидная починка ломает `_log_method_reference` у `logger.log`. Статус прежний: открыт. Адресат — владелец и ревью, ось «как опознан журнал».

## Сверка «база ↔ HEAD» партии (свойство 6 О-18 (а); пункт 5 договора `16-41-PLAN.md`)

**Инструмент.** Основа — копия r8diff 16-43 от оркестратора (`scratchpad/tools/r8diff-16-43/`, `cp -a` в `.pytest_cache/r8diff/`). Договор (а)–(з) пересверен с `<scope_note>` 16-41 и §«Сверка» плана. Изменения:
- **`run.sh`** — режим `--rows <строки> --at <ревизии>` (`rows.py`). Прочие режимы прежние.
- **`corpus.py`:**
  - `SEED = 42` — прежний (отступление 6);
  - (д) — семейство `e-self-1643`: самопроверка 16-43, `selfcheck_cells.json` → `selfcheck_cells_1643.json`, 16 464 формы, позиционная выборка;
  - (б) — форма `getattr-read` и значение `methodcaller-receiver` перешли из `b-candidate` в `b-matrix` сами (`in_dictionary` сверяет словарь HEAD). API значения писателя — из `API_IDENTIFICATION_CALLS` HEAD;
  - (г) и (д) судят словарь своих самопроверок — 12 форм и 5 значений (отступление 2);
  - (д) `e-final-1639` — ожидание класса из 6 ячеек (отступление 3);
  - (ж) D2 — `exact` 1 у писателя и число узлов номера у приватности (отступление 4);
  - (е) — итоговая самопроверка партии, `selfcheck_cells.json`.
- **`judge.py`** не менялся.

**Корпус итогового прогона:** HEAD `dbc73537`, **64 483 ячейки**, `corpus.json` sha256 `fd55d46711cad9493e5d387472f811873738f33a3a804f53dfa14e8e44755c43`.

**Строки итогового прогона** (`bash .pytest_cache/r8diff/final_chain.sh`: `run.sh 16-44 && run.sh --against-batch 16-41 && run.sh --against 1c243203 && run.sh --against 2f8c1656`, каждый под общим `flock`; HEAD `dbc73537`, 2026-10-20 03:26:02–03:52:50 UTC, `CHAIN_EXIT=0`) — дословно, без перечней `REPAIRED`:

```
CORPUS_SHA256=fd55d46711cad9493e5d387472f811873738f33a3a804f53dfa14e8e44755c43 HEAD=dbc73537afd55f8129ac27a57a634c4600f1bd4e
SELFTEST 1bebbbf7 -> c6953017: cells=3382 regressions=48 count_regressions=48 fixed=208 repaired_overcount=0 changed=256
SELFTEST 5e32c335 -> 147f5e46: cells=3382 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3591 regressions=831 count_regressions=885 fixed=378 repaired_overcount=354 changed=1317
DIFF 53f2483b -> a3c8f299: cells=64483 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF cf27c862 -> ecfe3566: cells=64483 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF c13c119b -> dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE 24f644c4 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
HEAD_WRONG=0
OPEN_REGRESSIONS=0
AGAINST fb8fef72 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=8974 repaired_overcount=65 changed=7751
AGAINST 1c243203 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=13488 repaired_overcount=948 changed=11648
AGAINST 2f8c1656 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=23366 repaired_overcount=777 changed=20878
```

Строки `SELFTEST` и `SELFTEST-COUNT` печатаются и в каждом из трёх прогонов `--against`. Там они те же: 48 / 56 / 885.

**`SELFTEST-COUNT … count_regressions=885 … repaired_overcount=354`** — у 16-41…16-43 было 1 237 / 2. Разница — 352 ячейки (ж) D2 приватности: с `exact` из числа узлов номера (отступление 4) они переходят в `REPAIRED` у `51d0d766` — это и есть задуманная починка WR-24. Ось счёта по-прежнему видит регрессию WR-27 (`count_regressions` 885 > 0).

**`DIFF` по каждому GREEN — `changed=0`.** План не правил предикатов. Его GREEN — строка словаря, значение и таблица API, тексты. Ячейки этих строк HEAD судил верно и до GREEN (кандидаты (б) с 16-43 верны). `BASE 24f644c4 -> HEAD` — тоже `changed=0`.

**Ячейки `REPAIRED` против трёх баз — все названы с классом.** Классы сверены скриптами `repaired_class.py` / `judged_twice.py` по находкам дерева базы и HEAD:

| База | REPAIRED | Одно место повторено (WR-24) | Одна запись, судимая дважды (WR-24, класс 16-42) | Оба сразу (3 → 1) | Снятая ложная находка законной строки |
|------|----------|-------------------------------|--------------------------------------------------|-------------------|---------------------------------------|
| `fb8fef72` (база партии) | 65 | 0 | 65: `a-literal` 2, `c-review` 3, `e-self-1642` 60 | 0 | 0 |
| `1c243203` | 948 | 889: приватность (ж) 406, (е) 447, `e-self-1641` 20, `e-wrapper-read-1637` 10, `a-negative` 1, `c-review` 1; писатель `e-self-1642` 3, `e-axis-b` 1 | 57: `a-literal` 2, `c-review` 3, `e-self-1642` 51, `e-wrapper-read-1636` 1 | 2: `e-self-1642` | 0 |
| `2f8c1656` | 777 | 724: писатель (ж) 198, (е) 228; приватность (ж) 144, (е) 146, `e-self-1641` 8 | 52: `a-literal` 2, `c-review` 3, `e-self-1642` 47 | 0 | 1: `a-legitimate::raw-sql-where-between-two-double-quoted-spans-is-a-filter` (1 → 0) |

Пояснения к классам:
- «Одно место повторено» — у базы находки того же текста на той же строке; разных текстов не больше `exact`. Примеры:
  - (ж) D2 приватности `f = methodcaller("info", "x %s", account.phone); f(logger); f(logger)` — 2 или 4 находки у `1c243203`, одна у HEAD; узел номера один;
  - (ж) D2 писателя `f = methodcaller("set_committed_value", account, "phone", x); f(attributes); f(attributes)` — две одинаковые находки `scripts/x.py:1` у `2f8c1656`, одна у HEAD, «одна находка на (строка, столбец, вид)».
- «Одна запись, судимая дважды» — `partial` с колонкой или обёртка с аргументами записи, прочитанные getattr-строкой. У базы находки на строке связывания и на строке применения; HEAD оставляет место применения. Это класс 16-42 (`340d5939`, его REPAIRED 463).
- Законная строка — ложную находку сняли ещё до партии (замер верификатора раунда 8).

Ни одна ячейка ни одной базы не дала регрессии наличия. Регрессий счёта вне этих классов нет.

**Промежуточные прогоны:**

| После | HEAD | Корпус | sha | Строки | Выход |
|-------|------|--------|-----|--------|-------|
| GREEN задачи 1 | `a3c8f299` | 44 483 без (е); (д) ещё судили 13 форм | `f0c1e605…` | `DIFF 53f2483b -> a3c8f299: regressions=0 count_regressions=0 changed=0`; `BASE 24f644c4 -> HEAD a3c8f299: … changed=0`; `HEAD_WRONG=1` (`e-final-1639::86400`, отступление 3; на базе плана тот же ответ); `OPEN_REGRESSIONS=0` | 0 |
| GREEN задачи 2, заход 1 | `ecfe3566` | — | — | `corpus.py` упал: генератор 16-39 и значение без колонки-литерала (`StopIteration`) | 1 |
| GREEN задачи 2, заход 2 | `ecfe3566` | 44 483, (г) и (д) на прежнем словаре | `8ff36119…` | `DIFF 53f2483b -> a3c8f299` и `DIFF cf27c862 -> ecfe3566` — 0 / 0; `BASE … 0 / 0`; `HEAD_WRONG=0`; `OPEN_REGRESSIONS=0` | 0 |
| GREEN задачи 3, цепочка 1 (02:18:59–02:43:36) | `dbc73537` | 64 483 с (е) | `b33683e4…` | `run.sh 16-44` — как в итоге; `AGAINST fb8fef72 … 0 / 0`; `AGAINST 1c243203 … regressions=0 count_regressions=352` → отступление 4 (приватность) | 1 |
| цепочка 2 (02:45:37–03:12:13) | `dbc73537` | 64 483 | `4df18d25…` | `AGAINST 1c243203 … 0 / 0 repaired_overcount=948`; `AGAINST 2f8c1656 … regressions=0 count_regressions=426` → отступление 4 (писатель) | 1 |
| цепочка 3 (итог) | `dbc73537` | 64 483 | `fd55d467…` | строки выше | 0 |

Кратко о цепочке 1:
- все 352 ячейки — (ж) D2 приватности со значениями `methodcaller` / `methodcaller-receiver`;
- 330 из них 2 → 1, 22 — 4 → 1 (носитель `named-wrapper-called`);
- у `1c243203` и двойник на двух строках давал 2 / 4 одинаковых находки;
- узел номера один, у HEAD — одна находка.

Кратко о цепочке 2:
- все 426 ячеек — D2 писателя со значениями `methodcaller` / `methodcaller-receiver`: (ж) 198 и (е) 228;
- у `2f8c1656` — две одинаковые находки на строке связывания, у HEAD — одна.

Обе цепочки — правка ожидания инструмента, а не гейта: число стало строже, предикаты не трогались.

### Корпус сверки партии раунда 8: что прогнано и что нет

Запись для владельца. Инструмент gitignored и переживает только worktree; от сверки останется этот раздел.

**Итоговый корпус:** HEAD `dbc73537`, 64 483 ячейки, sha256 `fd55d46711cad9493e5d387472f811873738f33a3a804f53dfa14e8e44755c43`.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 259, `LEGITIMATE_CASES` 105, `NEGATIVE_CONTROLS` 156, `POSITIVE_CONTROLS` 53 | 573 |
| (б) матрицы | `b-matrix`: 13 `BINDING_FORMS` × 6 значений × 21 способ × 2 гейта; `b-candidate` — 0 (кандидаты раунда 8 — строки словаря) | 3 276 |
| (в) формы ревью | раунд 7 — 30, раунд 8 — 16, 16-42 — 33, 16-43 — 27 | 106 |
| (г) дифференциал раунда 7 | 5 значений × 7 форм аргументов × 10 носителей × 2 гейта (прежний словарь) | 700 |
| (д) выборка самопроверок | 15 семейств по 2 000 (seed 42) | 30 000 |
| (ж) две подачи на одной строке | для каждой ячейки (б): D1 — 1 134 + 1 134 (`twin` + `exact` 2); D2 — 504 + 504 (`twin` + `exact` 1 у писателя, число узлов номера = 1 у приватности) | 3 276 |
| (з) безопасные двойники | (б) 3 276 + (ж) 3 276, `exact` 0 | 6 552 |
| (е) итоговая самопроверка партии | выборка 20 000 из 66 690 (seed 42) | 20 000 |

**Правило выборки (д):** равномерно, без повторов, `random.Random(42)`, ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием. Семейства 16-39, 16-41, 16-42, 16-43 материализуются и выбираются по позиции. Генераторы (д) и (г) судят словарь своих самопроверок (12 форм, 5 значений), поэтому выборка 14 прежних семейств совпадает с выборкой 16-42 / 16-43.

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
| самопроверка 16-41 | 36 876 | 2 000 |
| самопроверка 16-42 | 22 512 | 2 000 |
| самопроверка 16-43 | 16 464 | 2 000 |

**Не прогнано выборкой:** 11 119 725 форм полного перебора генераторов (11 149 725 − 30 000). Ещё 46 690 форм итоговой самопроверки 16-44 не вошли в корпус (е). Сама самопроверка прогнана целиком: 66 690 на HEAD и на двух контролях. Строки таблиц, ячейки матриц, формы ревью, дифференциал, (ж) и (з) прогнаны целиком.

**Регрессировавшие ячейки партии раунда 8 и закрывшие их коммиты** (по сводкам 16-41…16-44):

| План | GREEN, давший регрессию | Ячеек | Что | Закрыл |
|------|-------------------------|-------|-----|--------|
| 16-41 | — | 0 | — | — |
| 16-42 | — | 0 | — | — |
| 16-43 | — | 0 | — | — |
| 16-44 | — | 0 | — | — |

**`REPAIRED` на GREEN партии** (против родителя):
- 16-42: `340d5939` — 463 ячейки класса «одна запись, судимая дважды» (`partial` с колонкой, прочитанный getattr-строкой, судился на связывании и на применении, 2 → 1);
- 16-41, 16-43, 16-44 — 0.

`REPAIRED` против трёх баз — таблица выше. Регрессия счёта WR-27 (`51d0d766`, до партии) закрыта 16-41 (`41f07251`). Против `1c243203` она не видна, потому что закрыта.

## Гейты на итоговом дереве (`dbc73537`, под общим `flock`)

| Проверка | Итог | До плана (`24f644c4`) |
|----------|------|------------------------|
| `<automated>` задач 1–2 №1, приёмка задачи 3: три модуля гейтов поимённо (писатель, приватность, паритет) | `891 passed` (писатель 598, приватность 271, паритет 22) | 885 (597 / 270 / 18) |
| `<automated>` задачи 1 №2 (`t1_forms_1644.py`) | `OK 13 126` (после задачи 1 — `OK 13 105`) | — |
| `<automated>` задачи 2 №2 (`t2_matrix_1644.py`) | `OK 1638` | — |
| `<automated>` задачи 3 №1: quick run фазы (8 путей) | `1295 passed` | 1289 |
| `<automated>` задачи 3 №2 (`t3_header_1644.py`) | `OK` | — |
| `<automated>` задачи 3 №3: сквозные гейты + `test_logging_config` | `576 passed` + `3 passed` | 576 + 3 |
| `<automated>` задачи 3 №4: четыре прогона `run.sh` | `CHAIN_EXIT=0` (строки выше) | — |
| `<automated>` задачи 3 №5: `run.sh --rows …` | 10 строк `ROWS`, выход 0 | — |
| предусловие задачи 1 (`precondition.py`) | `OK` | `OK` |
| живые деревья приватности (`-s -k live_trees`) | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| живое дерево писателя и реестры (`t3_live_registry_1644.py`) | `OK` (писатель 6 сырых, 104 файла, 0 находок; `PHONE_LOG_EXCEPTIONS == {}`, потолок 0; реестр — ровно писатель) | то же |
| строки `8aabdb38` (`rows_8aabdb38.py`, `ast.unparse` по `id`) | `OK 246 98`, `OK 145 51` | — |
| `tests/test_application` | `883 passed` | 882 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, «реестр: 875 строк, биекция с переписью — согласие» | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | `110 passed` | 110 |

`tests/test_planning` гонится после коммита сводки. Итог — в финальном сообщении исполнителя оркестратору.

## Files Created/Modified

- `tests/phone_gate_grammar.py`:
  - строка `BINDING_FORMS` `getattr-read` с летописью;
  - комментарии строк `named-wrapper-bound-handed` (IN-18: `147f5e46` — матрица писателя) и `map-named-iterable` (`c6953017` — матрица приватности) с двумя основаниями чисел.
- `tests/test_application/test_phone_single_writer_gate.py`:
  - значение `methodcaller-receiver`, таблица `API_IDENTIFICATION_CALLS`;
  - правило-матрица по таблице;
  - шапка — абзац форм связывания (`getattr-read`, значения матрицы), летопись седьмого круга по матрицам, «Летопись словаря восьмого круга»;
  - правило шапки — места словаря восьмого круга.
- `tests/test_phone_privacy_gate.py`:
  - значение `methodcaller-receiver`;
  - шапка — абзац «ПО СВЯЗЫВАНИЮ» (`getattr-read`, значения), летопись седьмого круга по матрицам, «Летопись словаря восьмого круга»;
  - правило шапки — те же места.
- `tests/test_phone_gates_parity.py`:
  - `_writer_finds(source, call)` по `API_IDENTIFICATION_CALLS`;
  - три правила: `test_the_shared_dictionary_holds_the_round_eight_axes`, `test_the_parity_docstring_names_what_it_checks`, `test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens`;
  - докстринг «ЧТО ПРОВЕРЯЕТСЯ» — каждое имя и каждое правило, словари седьмого и восьмого круга.

Инструмент сверки (gitignored, не коммитится, оставлен в worktree для оркестратора):
- `.pytest_cache/r8diff/`:
  - `corpus.py`, `judge.py`, `run.sh` (режим `--rows`), `rows.py`, `selfcheck_1644.py`;
  - `selfcheck_cells.json` (самопроверка 16-44, 66 690), `selfcheck_cells_1643.json`;
  - `final_chain.sh`, `sc_chain.sh`, `final-chain.out` (итог), `final-chain-run1.out`, `final-chain-run2.out`, `final-rows.out`;
  - разбор: `sc_report.py`, `sc_axes.py`, `sc_dups.py`, `classify_against*.py`, `repaired_class.py`, `judged_twice.py`, `same_place.py`, `d2_privacy.py`, `d2_writer.py`, `probe_1639_count.py`, `show_cell.py`;
  - `trees/`, `judged/`, `rows/`.
- `.pytest_cache/checks/*.py` — дословные `python -c` плана и зонд получателя.

## Decisions Made

- Предикаты не правились. Замер прототипа плана подтвердился: на базе плана `24f644c4` все 1 638 ячеек на гейт нового словаря и все 66 690 форм самопроверки верны. 16-42 и 16-43 уже читают имя getattr-строкой у обоих гейтов.
- `API_IDENTIFICATION_CALLS` без умолчания. Правило словаря восьмого круга требует запись у каждого `id` и запрещает лишние. Правило-матрица и паритет падают `KeyError`, если значение добавят без API.
- Пара значения у приватности — `methodcaller` над журналом из вызова фабрики `structlog.get_logger()`, как решил планировщик. Правило словаря проверяет, что номер в аргументах `methodcaller`, а получатель номера не несёт.
- Числа IN-18 названы с обоими основаниями: замер верификатора на 12 × 5 и замер `--rows` на таблицах HEAD 13 × 6. Число `--rows` — ячейки, красные на коммите регрессии и зелёные на его родителе.

## Deviations from Plan

### Расхождения «план ↔ замер» (записаны, ничего не ослаблено)

**1. Числа правил и прогонов выше плановых.**
- Три модуля: план — ≥ 868 после задач 1–2 и ≥ 870 после задачи 3 (писатель 582, приватность 266, паритет 22). Замер — 889 и 891 (598 / 271 / 22): база плана — 885, а не 844 прототипа на `8aabdb38`.
- Quick run: план — ≥ 1 274, замер — 1 295.
- `tests/test_application`: 883 (882 + параметр матрицы).
- `t1_forms_1644.py`: после задачи 2 печатает `OK 13 126` (6 значений), после задачи 1 — `OK 13 105`.

Пороги «не меньше» выполнены. Строки не удалялись: `OK 246 98` / `OK 145 51` против `8aabdb38`.

**2. [Rule 3 — инструмент] Источники (г) и (д) закреплены на словаре своих самопроверок.**
- Найдено: прогон `run.sh 16-44` после GREEN задачи 1. Генераторы (д) читают `BINDING_FORMS` дерева HEAD. Новая строка меняла полный перебор (ось B 70 840 → 74 382, итог 16-39 82 035 → 88 863) и выборку seed 42. После GREEN задачи 2 генератор 16-39 упал на значении без колонки-литерала (`StopIteration`, выход 1).
- Исправлено в `corpus.py` (gitignored): до (г) модули `grammar` / `writer` / `privacy` заменены заместителями с 12 формами и 5 значениями.
- Проверка: полный перебор (д) снова равен замеру 16-43, выборка 14 прежних семейств — та же.
- Новые строки словаря держат (б), (ж), (з) и (е).

**3. [Rule 1 — артефакт ожидания инструмента] Ячейка `e-final-1639::86400`, `HEAD_WRONG=1`.**
- Найдено: прогон после GREEN задачи 1, на сдвинутой выборке (отступление 2).
- Причина: `derived_count` 16-41 у `phone_unique` считает вставленные узлы номера. Класс — часть C самопроверки 16-39, приватность, обёртка «связанная формой» у формы `direct`, чтение «список и подача» / «`return` и подача», `methodcaller`. Второй литерал `methodcaller` ничему не применён. По правилу самой 16-39 («`methodcaller` с получателем из не-литерала — ноль (D-17)») это не подача; гейт законно даёт 1.
- Замер по ВСЕМУ семейству (88 863 ячейки): ровно 6 ячеек этого класса, у прочих число совпадает. На базе плана ответ тот же.
- Исправлено: у этих 6 ячеек `exact` 1. Гейт не правился, коммита нет.

**4. [Rule 1 — артефакт ожидания инструмента] Ожидание по числу у D2 «двух подач на одной строке» — `exact`, а не `null` договора 16-41.**
- Найдено:
  - цепочка 1 — `AGAINST 1c243203: count_regressions=352`: все — (ж) D2 приватности, `methodcaller` / `methodcaller-receiver`, один узел номера в значении связывания, 2 или 4 одинаковые находки у базы и одна у HEAD;
  - цепочка 2 — `AGAINST 2f8c1656: count_regressions=426`: все — D2 писателя ((ж) 198, (е) 228), две одинаковые находки `scripts/x.py:1` у базы и одна у HEAD;
  - у обоих классов база печатала одно место у каждого применения. Двойник на двух строках давал у базы то же 2 / 4, так что это не сливание разных подач (WR-27), а двойной счёт одного места (WR-24).
- Решение О-18 (а), свойство 4: «двойной счёт WR-24 не возвращается»; свойство 6 исключает заявленную починку WR-24 из регрессий счёта. Механизм договора (`REPAIRED`) требует `exact`, а D2 его не нёс.
- Сам план называет число D2: «D2 — 504 по одной (номер или колонка в значении связывания — одно место)».
- Исправлено в `corpus.py` (ж) и `selfcheck_1644.py`: у приватности D2 `exact` — число узлов номера (у всех 504 — 1), у писателя — 1. Проверка `twin` осталась. Это строже прежнего: число теперь утверждается.
- Проверка:
  - на HEAD все ячейки D2 дают ровно это число: 504 / 504 приватности, 504 + 1 035 писателя;
  - цепочка 3 — `AGAINST` 0 / 0 у всех трёх баз;
  - `SELFTEST-COUNT` остаётся > 0 (885).
- Прототип плана «81 / 55 по две» у D2 на HEAD не воспроизвёлся: на `dbc73537` по две у D2 — ни одной ячейки. Измерение главнее.

**5. Сверка против `1c243203` не дала нуль «из коробки».** План ждал там ноль: «число находок приватности на ней было верным». Замер: верно по наличию, но у `1c243203` одно место печаталось у каждого применения `methodcaller` — отступление 4. После уточнения ожидания — ноль регрессий обеих осей, `REPAIRED` 948 с классами.

**6. Seed выборки (д) — 42, а не номер плана.** Договор 16-41 велит `random.Random(<номер плана>)`, заметка оркестратора 8 — seed 42. Принят 42: выборка прежних семейств совпадает с 16-42 / 16-43. Так же записали 16-43 и 16-42 / 16-43 (е).

**7. Нумерация строк плана.** План называл строки на `8aabdb38`. Символы найдены по имени на `24f644c4`.

### Замены команд (песочница worktree, заметки оркестратора 3, 4)

- `python -c` из `<automated>` и приёмки записаны дословно в `.pytest_cache/checks/`: `precondition.py`, `t1_forms_1644.py`, `t2_matrix_1644.py`, `t3_header_1644.py`, `t3_live_registry_1644.py`, `rows_8aabdb38.py`. Запуск — с `PYTHONPATH=.`.
- Четыре прогона `run.sh` через `&&` и `--rows` — скриптом `final_chain.sh`, каждый под `flock`. Песочница отклонила составные команды с вычисляемыми путями и `bash -c` с `timeout`. Ожидание — циклом `until grep …` в отдельных вызовах.
- `git show 8aabdb38:… > .pytest_cache/r8_base_*.py` — простой командой.
- Журнал плана `gsd-plan-head-before-16-44` лежит в `.pytest_cache/`, как у 16-43.
- `graphify query` гонялся по графу основного дерева (`--graph /source/broadcaster/graphify-out/graph.json`). `graphify update .` не запускался — за оркестратором после слияния.
- Полная суита (`just test`, ≈46 мин) не гонялась — её гонит пост-мердж гейт оркестратора.

---

**Total deviations:** 7 записанных расхождений: 1 — числа выше плана; 3 — правки инструмента (закрепление словаря (г) / (д), ожидание класса 16-39, ожидание D2), все строже или прежние по смыслу, гейты не правились; 1 — «план ↔ замер» у `1c243203`; 2 — seed и нумерация. Плюс замены команд.
**Impact on plan:** заявления шапок не сужены, реестры прежние (`PHONE_LOG_EXCEPTIONS = {}`, потолок 0, писатель — ровно модуль-писатель). Живые деревья — 225 / 68 / 93 и 6 / 104, находок 0. JS-половина не тронута. Правились только четыре файла плана и gitignored-инструмент.

## Issues Encountered

- Первая цепочка итоговых прогонов остановилась на `AGAINST 1c243203` (`CHAIN_EXIT=1`), вторая — на `AGAINST 2f8c1656`. Обе — артефакт ожидания D2 (отступление 4). Каждая регрессия разобрана поячеечно до правки: класс, число узлов, находки базы и HEAD. Третья цепочка прошла целиком.

## Known Stubs

Нет.

## Threat Flags

Нет: правка только тестовых гейтов и общего модуля тестов, новых поверхностей нет.

## TDD Gate Compliance

У каждой задачи `test(16-44)` стоит перед своим `feat(16-44)`: `53f2483b` → `a3c8f299`, `cf27c862` → `ecfe3566`, `c13c119b` → `dbc73537`. REFACTOR-коммитов нет. Нарушений нет.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 16-45 (волна 5, документы) получает:
  - пять находок с закрывшими коммитами партии. WR-28 — словарь `a3c8f299`, `ecfe3566`; предикаты — 16-42 / 16-43. IN-18 и IN-19 — `dbc73537` (правила — `c13c119b`);
  - запреты этого плана в `must_haves.prohibitions` — не правились.
- Открыто: получатель журнала, связанный с именем модуля и прочитанный getattr-строкой (`getattr(sys.modules[__name__], "lg").info(…)`) — `[]` на HEAD, как на `4f1e3b7c` и `1c243203` (16-43). Адресат — владелец и ревью; объём словаря восьмого круга его не включает.
- Инструмент `.pytest_cache/r8diff/` оставлен на месте (итоговые строки — `final-chain.out`).
- `deferred-items.md` не создавался.

## Self-Check: PASSED

- `tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py` — FOUND.
- `.pytest_cache/r8diff/{corpus.py,judge.py,run.sh,rows.py,selfcheck_1644.py,selfcheck_cells.json,final-chain.out}` — FOUND.
- Коммиты `53f2483b`, `a3c8f299`, `cf27c862`, `ecfe3566`, `c13c119b`, `dbc73537` — предки HEAD (FOUND).
- `git rev-list --count 24f644c4..dbc73537` = 6; изменений вне коммитов нет (`git status --short` пуст).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-20*

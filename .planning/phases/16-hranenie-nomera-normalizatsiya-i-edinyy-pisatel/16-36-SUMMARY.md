---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 36
subsystem: testing
tags: [ast, phone, single-writer-gate, carrier-wrapper, shared-grammar, base-head-differential, tdd, cr-03, wr-26]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль `tests/phone_gate_grammar.py` (`reference_arguments`, `carrier_wrapper_bindings`, `applied_wrapper` — 16-32, 16-34), гейт писателя после 16-34 (555 правил, строки 228 / 96), гейт приватности (222), правило-паритет (15)"
provides:
  - "общий модуль: `named_wrappers`, `WrapperApplication` (`read`, `wrapper`, `application`), `wrapper_applications` (вызванная и поданная обёртка, рекурсивно, с защитой от цикла), рекурсивный предикат `is_carrier_wrapper`; `carrier_wrapper_bindings(…, nested=True)` — неподвижная точка с вложенными обёртками"
  - "гейт писателя: обёртка носителя судится на каждом чтении её имени через `wrapper_applications`; поглощение суда на месте связывания — только когда каждое чтение судится как применение (регрессия `147f5e46` снята); литерал обёртки, прочитанный применением, судится один раз"
  - "гейт писателя ввозит по имени все пять имён семантики обёртки (`carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`, `is_carrier_wrapper`, `wrapper_applications`) — те же объекты общего модуля, своих одноимённых помощников нет (вход плана 16-37)"
  - "трасер `test_a_planted_backfill_with_a_context_run_wrapper_handed_to_an_executor_reddens_the_gate`; 16 строк `LITERAL_FORM_CASES` (244), 2 строки `LEGITIMATE_CASES` (98); шапка — суд на каждом чтении, цена, летопись седьмого круга"
  - "инструмент сверки «база ↔ HEAD» `.pytest_cache/r7diff/` (`corpus.py`, `judge.py`, `run.sh`; gitignored) по договору `<scope_note>` — для планов 16-37…16-39"
affects: [16-37, 16-38, 16-39, 16-40, phase-18, phase-19, phase-20]

actuals:
  tokens: 14643
  tasks: 3
  commits: 8
plan_head_before: 1c2432032fe88d191e58728c043e763bc0d5dbd0
plan_head_after: 4ffef0c1a72252ffbf15db378cf02dbae9e12178

tech-stack:
  added: []
  patterns:
    - "Семантика обёртки носителя — функции общего модуля: гейт даёт только имена `partial` и свой предикат ссылки (`is_carrier_wrapper`), какие обёртки называет узел (`named_wrappers`) и где они применены (`wrapper_applications`)"
    - "Каждое применение обёртки судится той же функцией гейта, что и обычный носитель (`_referenced_calls`), на месте внешнего вызова; одно место — одна находка"
    - "Сверка «база ↔ HEAD» после каждого GREEN: корпус (а)–(е), суд ревизий в отдельном процессе по `git archive`, `SELFTEST` против вакуума на двух замеренных регрессиях"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Обёртка поглощается (не судится на месте связывания), только если КАЖДОЕ чтение имён, связанных с ней, — применение, которое гейт судит, или звено цепочки `h = w`; звено сверяется по месту узла (строка, столбец, конец), потому что getattr-строка в значении связывания — синтетический `Attribute` на месте вызова `getattr`"
  - "Литерал обёртки, поданный носителю, поглощается, если запись нашло применение его самого или обёртки, вложенной в него; иначе каждый уровень `partial(partial(…))` судил бы ту же запись у себя (регрессия `44452e68`, найденная сверкой «база ↔ HEAD» самопроверки — 798 ячеек)"
  - "Ветка «вызов имени обёртки» ушла из `_referenced_calls` в общую `wrapper_applications`; `_carrier_wrappers` возвращает отображение вместе с предикатом обёртки, `_methodcaller_receivers` проходит каждое применение `wrapper_applications`"
  - "Цена шапки уточнена замером: «по находке на каждое место». Вид, чья находка стоит на узле аргумента (ключ строки, именованный аргумент), у связывания и у применения указывает на один литерал — место одно; вид на месте вызова — два места"

patterns-established:
  - "Сверка «база ↔ HEAD» — шаг плана: `bash .pytest_cache/r7diff/run.sh <план>` после каждого GREEN; регрессия — свой цикл `test` / `feat` со строкой, повторяющей ячейку; план закрывается на `OPEN_REGRESSIONS=0`, `BASE … regressions=0` и `SELFTEST` > 0 у обеих пар"
  - "Самопроверка оси «где прочитано имя обёртки»: представление обёртки × носитель обёртки × где аргументы записи × способ чтения × значение опознания × API × форма `BINDING_FORMS`; ожидание у ячеек цены — диапазон «по находке на место», у неиспользованной обёртки без аргументов — ответ значения, поданного носителю без аргументов"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Подложенный скрипт дозаполнения с телом `asyncio.to_thread` — `functools.partial(ctx.run, setattr, account, \"phone\", number)`, поданный `run_in_executor`, — в синтетическом `scripts/` краснит гейт писателя с файлом, строкой 11 и видом; у файла ровно одна находка"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_context_run_wrapper_handed_to_an_executor_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Четыре формы CR-03, четыре формы WR-26, контроль «без использования», три вложенные формы и `methodcaller` в поданной обёртке, три формы цикла сверки — строки LITERAL_FORM_CASES по одной находке; поданная обёртка с чужим атрибутом и цикл обёрток без писателя — ноль"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write"
        status: pass
      - kind: other
        ref: "task-2 <automated> #2 плана 16-36 (OK cycles and depth)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Семантика обёртки — функции общего модуля; гейт писателя держит пять имён по имени теми же объектами; оба гейта и паритет — 811 правил"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "acceptance задачи 2 плана 16-36 (OK 5)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта писателя: суд обёртки везде, где прочитано её имя, `wrapper_applications`, цена «по находке на место», летопись седьмого круга с регрессией `147f5e46` и О-16 (а); заявление прежнее"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: "task-3 <automated> #2 плана 16-36 (OK)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сверка «база ↔ HEAD»: 54 001 ячейка, по каждому из четырёх GREEN — `DIFF`, `BASE 1c243203 -> HEAD 4ffef0c1` без регрессий, `OPEN_REGRESSIONS=0`, `SELFTEST` 43 и 52"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "bash .pytest_cache/r7diff/run.sh 16-36 (выход 0, HEAD 4ffef0c1)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Прежнее не ослаблено: 228 / 96 строк `65e5c692` на месте; живое дерево писателя — 0 судимых находок в 104 файлах, в писателе 6 сырых, реестр — ровно писатель; гейт приватности — 222, живые деревья 225 / 68 / 93, находок 0, реестр пуст, потолок 0"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "task-1 <automated> #2 и #3 плана 16-36 (OK 228 96 244 98; OK 6 104); acceptance задачи 3 (OK)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
    human_judgment: false

duration: 114min
completed: 2026-10-19
status: complete
---

# Phase 16 Plan 36: Обёртка носителя судится на каждом чтении, сверка «база ↔ HEAD» — Summary

**Гейт единственного писателя теперь судит обёртку носителя везде, где прочитано её имя: вызванную, поданную исполнителю, потоку или очереди, вложенную в ещё один `partial`. Дословное тело `asyncio.to_thread` — `functools.partial(ctx.run, setattr, account, "phone", x)`, поданный `run_in_executor`, — снова краснит гейт: регрессия `147f5e46` снята. Раскрывают обёртку функции общего модуля `wrapper_applications`, `named_wrappers` и `is_carrier_wrapper` — рекурсивно, с защитой от цикла. План завёл инструмент сверки «база ↔ HEAD» и гонял его после каждого GREEN. Сверка корпуса самопроверки нашла собственную регрессию плана: на `44452e68` вложенный литерал с аргументами записи давал две находки вместо одной, 798 ячеек. Она закрыта своим циклом. Итог: `OPEN_REGRESSIONS=0`, база плана без регрессий, заявление шапки прежнее.**

## Performance

- **Duration:** ≈114 мин
- **Started:** 2026-10-19T05:46:14Z
- **Completed:** 2026-10-19T07:40Z
- **Tasks:** 3 (плюс 1 цикл сверки «база ↔ HEAD»)
- **Files modified:** 2

## Accomplishments

- **Общий модуль (`tests/phone_gate_grammar.py`):**
  - `named_wrappers(node, is_wrapper, bound)` — обёртки, которые называет узел: литерал, имя, атрибут, getattr-строка;
  - `WrapperApplication(read, wrapper, application)` и `wrapper_applications(call, wrappers_of, not_carriers, every_reading)`:
    - вызываемое `w(…)` / `self.w(…)` / `getattr(obj, "w")(…)`;
    - обёртка, поданная носителю позицией, `*[…]`, любым именованным аргументом или внутри `X(…)(…)`;
    - рекурсия по каждому применению, защита от цикла по `id` обёртки на пути;
  - `is_carrier_wrapper(value, partial_names, is_reference, not_carriers, known)` — рекурсивный предикат: обёртка поверх обёртки литералом любой глубины и именем из `known`;
  - `carrier_wrapper_bindings(…, nested=True)` — неподвижная точка видит уже найденные связывания; при `nested=False` ответ прежний.
- **Гейт писателя:**
  - каждое применение `wrapper_applications` судится `_referenced_calls` как носитель на месте внешнего вызова;
  - правило поглощения «каждое чтение судится» — `_absorbed_carrier_wrappers`. Поглощение по любому `Load` (`147f5e46`) снято;
  - литерал обёртки, поданный носителю, судится один раз;
  - `_carrier_wrappers` построен на общем предикате, своей проверки «аргументы содержат ссылку» в модуле гейта нет;
  - `_methodcaller_receivers` проходит каждое применение: `methodcaller` в поданной обёртке получает получателя от внешнего носителя.
- **Строки:** трасер; `LITERAL_FORM_CASES` 228 → 244 (+16: 9 задачи 1, 4 задачи 2, 3 цикла сверки); `LEGITIMATE_CASES` 96 → 98.
- **Шапка:** общий абзац (суд на каждом чтении, раскрытие поданной и вложенной обёртки, три функции общего модуля), перечень пойманного в «ГРАНИЦЕ ПРЕДИКАТА», абзац цены, летопись седьмого круга. Фраза «судится как применённая на месте вызова `w(…)`» ушла; пункт (1) поданную обёртку не называет. Заявление прежнее.
- **Инструмент сверки** `.pytest_cache/r7diff/` (`corpus.py`, `judge.py`, `run.sh` по договору; вспомогательные `selfcheck_1636.py`, `stats.py`, `changed.py`, `show.py`, `rows_at.py`). Деревья ревизий лежат в `trees/`, вердикты — в `judged/`. Не удалены: оркестратор копирует инструмент для 16-37…16-39.

## Task Commits

1. **Задача 1 (трасер): суд обёртки на каждом чтении, `wrapper_applications`** — `388ed1a9` (test, RED), `b67495dc` (feat, GREEN).
2. **Задача 2: рекурсивный `is_carrier_wrapper`, `methodcaller` в поданной обёртке** — `8e1f2ebf` (test, RED), `44452e68` (feat, GREEN).
3. **Задача 3: шапка** — `ec639a54` (test, RED), `b8d557f0` (feat, GREEN).
4. **Цикл сверки «база ↔ HEAD» (регрессия `44452e68`): вложенный литерал с аргументами записи** — `a5b43616` (test, RED), `4ffef0c1` (feat, GREEN).

**Plan metadata:** коммит `docs(16-36)` с этой сводкой. Первый коммит плана — `388ed1a9`, база — `1c243203`.

Гейт трасера после задачи 1: режим `end-of-phase`, у трасера только проверки `<automated>`. Все четыре команды `<verify>` прогнаны и зелёные (`565 passed`, `OK 228 96 237 96`, `OK 6 104`, `OPEN_REGRESSIONS=0`). После этого план перешёл к задачам 2 и 3.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored, не закоммичено). По каждому есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех четырёх записях (`t1.json`…`t4.json`).

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_backfill_with_a_context_run_wrapper_handed_to_an_executor_reddens_the_gate` | `9 failed, 1 passed, 555 deselected` | «обёртка носителя под именем, поданная, а не вызванная, не судится» | Цель исполнилась: обход нашёл файл, находок `[]`. Упали трасер и восемь строк. `carrier-wrapper-with-arguments-unused` зелёная до GREEN — закрепка (одна находка на месте связывания), не RED-свидетель. |
| Задача 2 | `test_a_literal_write_form_is_a_write[methodcaller-in-a-handed-carrier-wrapper]` (`-k "nested or over-a-named or in-a-handed"`) | `4 failed, 16 passed, 551 deselected` | «дала 0 находок вместо одной» | Четыре новые строки дали `[]`; 16 прежних строк, совпавших по `-k`, зелёные. Обе законные строки зелёные до GREEN — закрепки (`2 passed`). |
| Задача 3 | `test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` | `1 failed, 570 deselected` | «шапка гейта писателя не называет общую грамматику связывания» | Нет шести мест (суд на каждом чтении, `wrapper_applications`, CR-03, WR-26, `147f5e46`, О-16 (а)), и осталась сужающая фраза «судится как применённая на месте вызова `w(…)`». |
| Цикл сверки | `test_a_literal_write_form_is_a_write[nested-carrier-wrapper-with-arguments-handed]` (`-k nested-carrier-wrapper-with-arguments`) | `3 failed, 571 deselected` | «дала 2 находок вместо одной» | Три строки повторяют ячейки регрессии: на `44452e68` — две находки, под предикатами `8e1f2ebf` (родитель) и `1c243203` (база) — одна (замер `rows_at.py`). |

## Самопроверка исполнителя (задача 3; урок 16-12…16-34; О-16 (а))

Скрипт `.pytest_cache/r7diff/selfcheck_1636.py` лежит в gitignored-каталоге worktree и в репозиторий не коммитится. Он однопроцессный, работает под общим `flock`. Каждая форма подаётся в `phone_write_offences(…, "scripts/x.py")`.

**Оси:**
- **Представление обёртки (10):** литерал; вложенный в `partial` глубины 1, 2, 3; имя `w`; атрибут `holder.w`; цепочка `h = w`; getattr-строка `getattr(holder, "w")`; именованная вложенная `w = partial(partial(…))`; имя поверх имени (`w0 = …; w = partial(asyncio.to_thread, w0)`).
- **Носитель обёртки (4):** `asyncio.to_thread`, `contextvars.copy_context().run`, `ctx.run`, `loop.run_in_executor, None`.
- **Где аргументы записи (2):** в обёртке; у чтения.
- **Способ чтения (13):**
  - вызов;
  - подача позицией, `target=`, `fn=`, выдуманным ключом `job=`;
  - `map`, `call_soon`, `append`, `Thread(target=…)`, `run_in_executor`;
  - чтение вне вызова — список и `return` — вместе с подачей;
  - без использования.
- **Значение опознания (7):** имя, атрибут, getattr-строка, `partial` без привязки и с привязкой, `methodcaller`, псевдоним ввоза `as`.
- **Судимый API (22, как в 16-34):** `setattr`, `set_committed_value`, `set_attribute`, `flag_modified`, `object.__setattr__`; `execute`, `scalars`, `bulk_update_mappings`, `bulk_insert_mappings`, `op.bulk_insert`; `values` словарём и именованным, `Query.update`, `insert`, `from_select`, `ordered_values`, `on_conflict_do_update`, `on_duplicate_key_update`; модель, псевдоним модели, `MessengerAccount.__init__`, дескриптор `__set__`.
- **Форма связывания:** 12 `BINDING_FORMS`.
- **Ось (API, форма)** перебирается ротацией по ядру «представление × носитель × режим × чтение × значение» (7 280 сочетаний), 3 прохода со сдвигом, а не полным крестом.
- **Ожидание:**
  - под заявлением — ровно одна находка, называющая `phone`;
  - у ячеек цены (чтение вне вызова и подача, запись — в обёртке или в самом значении) — от одной до двух, по находке на место;
  - у неиспользованной обёртки без аргументов — ответ значения, поданного носителю без аргументов;
  - законные (не-пишущая ссылка `helper.noop`, чужой атрибут `"status"`) — ноль.

| Заход | HEAD, время (UTC) | Подано (под заявлением / законные) | `[]` | Кратных | Законные с находкой | Итог |
|-------|-------------------|-------------------------------------|------|---------|---------------------|------|
| 1 (2 прохода) | `b8d557f0`, ≈06:20–06:32 | 24 919 (9 527 / 15 392) | 289 → 7 → 0 | 555 → 548 | 0 | Два класса «меньше» — артефакты ожидания (ниже); 548 кратных — один настоящий класс |
| 2 (3 прохода) | `b8d557f0`, ≈06:36–06:39 | 34 243 (14 290 / 19 953) | 0 | 822 | 0 | Ячейки ушли в корпус (е). `run.sh`: `DIFF 8e1f2ebf -> 44452e68` — 796 регрессий, класс тот же → цикл `a5b43616` / `4ffef0c1` |
| 3 | `4ffef0c1`, ≈06:59–07:02 | 34 243 | 0 | 21 | 0 | 21 — артефакт ожидания у дескриптора (ниже) |
| 4 (итог) | `4ffef0c1`, 07:02–07:05 | **34 243 (14 290 / 19 953)** | **0** | **0** | **0** | Находок другого вида на месте — 0 |

**Артефакты ожидания (поправлено ожидание, не предикат):**
- Чтение вне вызова и подача при записи в обёртке: у вида, чья находка стоит на узле аргумента (ключ строки, именованный аргумент), связывание и применение указывают на один литерал. Место одно — одна находка. Ожидание «ровно две» заменено на «по находке на место» (1–2).
- Неиспользованная обёртка без аргументов: значение может нести запись само (`methodcaller` со всеми аргументами, `partial(<дескриптор>, account)`, ссылка `MessengerAccount.phone.__set__`). Ожидание — ответ значения, поданного носителю без аргументов (`runner.call(R)`). Это прежняя цена шапки «имя пишущего API, поданное другому вызову, судится как вызов этого API».

**По осям на заходе 4:**
- представления — от 3 025 (вложенная глубины 2) до 3 700 (цепочка);
- носители — по ≈8 560;
- режимы — 16 999 / 17 244;
- способы чтения — от 1 270 (`map`) до 3 088;
- значения — от 2 844 (ввоз `as`) до 6 153 (`methodcaller`);
- API — от 894 (дескриптор) до 2 008;
- формы — по ≈2 850.

Запись на SQLite формами задачи 2 и цикла сверки не замерялась. Та же механика носителя, что у форм, замеренных верификатором раунда 7 (`+71`…`+75`).

## Сверка «база ↔ HEAD» (свойство 7 О-16 (а); пункт 5 договора `<scope_note>`)

**Инструмент.**
- `corpus.py <дерево HEAD> <corpus.json> [selfcheck_cells.json]` собирает корпус из таблиц и функций дерева HEAD.
- `judge.py <дерево> <corpus.json> <out>` в отдельном процессе ставит дерево первым в `sys.path` и судит каждую ячейку `phone_write_offences` / `python_log_offences`. Исключение предиката — тоже вердикт.
- `judge.py --compare` печатает строку сравнения и перечень регрессий.
- `run.sh <план>`:
  - деревья ревизий берёт `git archive <rev> -- <5 файлов> | tar -x`, кеш — в `trees/`;
  - вердикты кешируются по ревизии и `sha256` корпуса;
  - печатает `SELFTEST` по источникам (б) и (в), `DIFF` по каждому `feat(<план>)`, `BASE` (родитель первого `test(<план>)` → HEAD) и последней строкой `OPEN_REGRESSIONS`;
  - выходит с кодом 1 при `K > 0`, при регрессиях `BASE`, при `SELFTEST` с нулём и без GREEN.
- Регрессия — ячейка, верная у родителя и неверная у GREEN.

**Корпус итогового прогона** (HEAD `4ffef0c1`, 54 001 ячейка, `corpus.json` sha256 `42d8eeabc352542417f1e09d746d734a0d9715776b32a35cb03d72b7e6ee6537`):

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 244, `LEGITIMATE_CASES` 98, `NEGATIVE_CONTROLS` 117, `POSITIVE_CONTROLS` 49 | 508 |
| (б) ячейки матриц | 12 `BINDING_FORMS` × 5 значений × (прямой вызов + 11 `REFERENCE_CARRIERS` + 9 кандидатных строк раунда 7) × 2 гейта | 2 520 |
| (в) формы ревью раунда 7 | CR-02 (7 + 3), CR-03 (4 + 3), WR-26 (4 + 3), WR-25 (2 + 1), WR-24 (2 + 1) | 30 |
| (г) дифференциал ревьюера / верификатора | 5 значений × 7 форм аргументов × 10 носителей × 2 гейта; ожидание по месту номера, иначе — база по видам | 700 |
| (д) выборка самопроверок 16-27…16-34 | 8 семейств по 2 000 | 16 000 |
| (е) самопроверка этого плана | заход 4 | 34 243 |

**Правило выборки (д):** равномерно, без повторов, `random.Random(36)` (seed — номер плана), ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием, поэтому полный перебор не материализуется. Генераторы семейств собраны по сводкам 16-27…16-34 (скрипты тех планов ушли вместе с их worktree). Это реконструкция осей, а не прежние скрипты.

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

**Не прогнано выборкой:** 966 398 форм полного перебора генераторов (982 398 − 16 000). Самопроверки 16-27…16-34 в прежнем виде — ≈550 000 форм, замер планирования; в корпус они вошли только выборкой. Самопроверка этого плана (е) прогнана целиком.

**Строки итогового прогона** (`bash .pytest_cache/r7diff/run.sh 16-36`, HEAD `4ffef0c1`, 2026-10-19 ≈07:15–07:31 UTC, выход 0) — дословно:

```
SELFTEST 1bebbbf7 -> c6953017: cells=2550 regressions=43 fixed=192 changed=235
SELFTEST 5e32c335 -> 147f5e46: cells=2550 regressions=52 fixed=145 changed=198
DIFF 388ed1a9 -> b67495dc: cells=54001 regressions=0 fixed=4885 changed=5097
DIFF 8e1f2ebf -> 44452e68: cells=54001 regressions=798 fixed=2384 changed=3406
DIFF ec639a54 -> b8d557f0: cells=54001 regressions=0 fixed=0 changed=0
DIFF a5b43616 -> 4ffef0c1: cells=54001 regressions=0 fixed=798 changed=798
BASE 1c243203 -> HEAD 4ffef0c1: cells=54001 regressions=0 fixed=7269 changed=7697
OPEN_REGRESSIONS=0
```

`SELFTEST` дал 43 и 52 — ровно замер планирования на тех же 2 550 ячейках.

**Регрессии и закрывшие их коммиты.** На `44452e68` — 798 ячеек, все закрыты `4ffef0c1` (`DIFF a5b43616 -> 4ffef0c1: fixed=798`, на HEAD верны все):
- самопроверка (е), вложенный литерал с аргументами записи в обёртке: `nested-named` — 211, `nested-2` — 183, `nested-3` — 179, `nested-1` — 139;
- с аргументами у чтения: 22 + 21 + 21 + 19;
- три строки `a-literal` цикла: `nested-carrier-wrapper-with-arguments-handed`, `named-nested-carrier-wrapper-with-arguments-called`, `nested-carrier-wrapper-with-arguments-unused`.

**Промежуточные прогоны:**
- после GREEN задачи 1 (HEAD `b67495dc`, корпус 19 749, sha `f5a92f57…`) — `DIFF 388ed1a9 -> b67495dc: regressions=0 fixed=208`, `BASE … regressions=0`, `OPEN_REGRESSIONS=0`;
- после GREEN задачи 2 (`44452e68`, корпус 19 755, sha `8426e960…`) — `DIFF 8e1f2ebf -> 44452e68: regressions=0 fixed=4`, `BASE … regressions=0`, `OPEN_REGRESSIONS=0`;
- после GREEN задачи 3 (`b8d557f0`, тот же корпус) — `DIFF ec639a54 -> b8d557f0: regressions=0 fixed=0`, `OPEN_REGRESSIONS=0`;
- с корпусом (е) захода 2 (`b8d557f0`, 53 998 ячеек, sha `60abb5fa…`) — `DIFF 8e1f2ebf -> 44452e68: regressions=796` (класс выше) и `DIFF 388ed1a9 -> b67495dc: regressions=5`. Пять ячеек `b67495dc` — ячейки цены: getattr-обёртка, значение `partial(<дескриптор>, …)`, чтение в списке или `return` вместе с подачей. Родитель давал одну находку на месте связывания и не судил подачу. GREEN нашёл и запись на месте подачи, то есть два места. Это не потеря находки: ожидание этих ячеек по договору — «по находке на место», и на итоговом прогоне они верны. В этом прогоне `run.sh` упал кодом 141 до строки `OPEN_REGRESSIONS` (отступление 4).

## Files Created/Modified

- `tests/phone_gate_grammar.py` — `is_carrier_wrapper`, `named_wrappers`, `WrapperApplication`, `wrapper_applications`; `carrier_wrapper_bindings(…, nested=…)`.
- `tests/test_application/test_phone_single_writer_gate.py`:
  - `_phone_writes` — применения обёрток и правило поглощения;
  - `_absorbed_carrier_wrappers`;
  - `_carrier_wrappers` на общем предикате;
  - `_methodcaller_receivers` по применениям;
  - `_referenced_calls` без ветки имени обёртки;
  - трасер, строки, правило шапки, шапка.

## Decisions Made

- Поглощение по судимым чтениям и литерал, поданный носителю, — см. `key-decisions`.
- В общем предикате первым позиционным `partial` проверяется предикат ссылки гейта целиком, включая `methodcaller`. До плана гейт проверял здесь только `_bound_reference`. Ответ матриц, строк, живого дерева и всех 54 001 ячейки сверки от этого не ухудшился: регрессий `BASE` 0.
- Имена помощников модуля гейта не совпадают с функциями общего модуля (`_absorbed_carrier_wrappers`, `_carrier_wrappers`). Пять имён семантики обёртки ввезены по имени. План 16-37 может вписать их в `REQUIRED_SHARED_NAMES` / `CARRIER_SEMANTICS`, не правя модуль гейта писателя.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Регрессия `44452e68`: вложенный литерал обёртки с аргументами записи — две находки вместо одной**
- **Found during:** задача 3, самопроверка → сверка «база ↔ HEAD» с корпусом (е).
- **Issue:** рекурсивный предикат сделал `partial(partial(<носитель>, setattr, account, "phone", x))` обёрткой на каждом уровне. Каждый литерал, прочитанный применением, судил ту же запись ещё раз у себя. На родителе `8e1f2ebf` и на базе `1c243203` — одна находка, на `44452e68` — две (798 ячеек).
- **Fix:** литерал обёртки, прочитанный применением, поглощается, если запись нашло применение его самого или обёртки, вложенной в него.
- **Files modified:** `tests/test_application/test_phone_single_writer_gate.py`.
- **Verification:** 3 строки цикла, `DIFF a5b43616 -> 4ffef0c1: regressions=0 fixed=798`, `OPEN_REGRESSIONS=0`.
- **Committed in:** `a5b43616` (test) / `4ffef0c1` (feat).

**2. [Rule 2 - Missing Critical] Литеральная обёртка, поданная носителю, судилась бы дважды**
- **Found during:** задача 1, GREEN.
- **Issue:** у `run_in_executor(None, partial(ctx.run, setattr, account, "phone", x))` запись нашло бы и применение на месте внешнего вызова, и сам литерал у себя.
- **Fix:** такой литерал поглощается (в цикле 1 уточнено вложенностью). Одно место — одна находка.
- **Committed in:** `b67495dc`.

**3. Числа плана и замер (замер правит, строки не тронуты):**
- гейт писателя 571 → **574**: +3 строки цикла сверки;
- оба гейта с паритетом 808 → **811**;
- quick run 1212 → **1215**;
- `LITERAL_FORM_CASES` 241 → **244**;
- `tests/test_application` 840 → **859**: +19 правил гейта писателя.

**4. [Rule 3 - Blocking] Инструмент сверки: `run.sh` падал кодом 141.**
- `echo … | head -1` под `pipefail` закрывал канал при длинном перечне регрессий, и скрипт выходил до строки `OPEN_REGRESSIONS`.
- Заменено на `printf … | sed -n 1p`. Итоговый прогон — выход 0, все строки на месте.
- Правка внутри gitignored-инструмента, коммита нет.

---

**Total deviations:** 2 исправлены автоматически (Rule 1 — 1, Rule 2 — 1), 1 правка инструмента (Rule 3), расхождения чисел описаны выше.
**Impact on plan:** правки только в файлах `files_modified`. Реестры, потолок, заявление шапки и прежние строки не тронуты. Модуль гейта приватности и правило-паритет не правились.

## Замены команд (песочница worktree, хост)

- `flock … uv run python -c "…"` песочница отклоняет. Команды `<automated>` и `acceptance_criteria` с `python -c` записаны дословно в `.pytest_cache/checks/*.py` (`live_writer.py`, `rows_task1.py`, `rows_task2.py`, `shared_names.py`, `cycles_depth.py`, `header_task3.py`, `registries_task3.py`). Запуск — с `PYTHONPATH=.`: у файла-скрипта `sys.path[0]` — каталог скрипта, а не cwd, как у `-c`. Логика та же.
- Команда «строки на месте» (`git show 65e5c692:… > .pytest_cache/r7_base_writer.py && uv run python -c …`) прошла как есть, без `flock`: она лёгкая.
- `run.sh` зовёт `git log` / `git archive` изнутри bash, песочница его не отклоняла.
- `pkill -f run_selfcheck1.log` попал в собственную оболочку (код 144). Правка `run.sh` сделана заново инструментом Edit.
- Полную суиту (~46 мин) не гнал: её гоняет оркестратор после слияния. `graphify update .` не запускал (orchestrator_notes): граф обновит оркестратор.

## Гейты на итоговом дереве (`4ffef0c1`, 2026-10-19, под `flock`)

| Гейт | Итог | База плана |
|------|------|------------|
| `tests/test_application/test_phone_single_writer_gate.py` | 574 passed | 555 |
| оба гейта + паритет | 811 passed | 792 |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| quick run фазы (8 путей) | 1215 passed | 1196 |
| `tests/test_application` | 859 passed | 840 |
| сквозные гейты (htmx_post_pairs, htmx_gates, test_templates, declared_invariants) | 576 passed | 576 |
| `tests/test_logging_config.py` | 3 passed | 3 |
| `compileall -q app main.py tests` | код 0 | код 0 |
| `scripts/prohibitions_census.py --check` | код 0, «реестр: 856 строк, биекция с переписью — согласие» | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| task-1 #2 / #3 | `OK 228 96 244 98` / `OK 6 104` | — |
| task-2 #2 / имена общего модуля | `OK cycles and depth` / `OK 5` | — |
| task-3 #2 / реестры | `OK` / `OK` | — |
| `run.sh 16-36` | выход 0, `OPEN_REGRESSIONS=0` | — |
| `tests/test_planning` | гонится после коммита сводки (финальное сообщение) | 218 passed, 2 skipped |

## TDD Gate Compliance

`git log --grep='^test(16-36)'` — 4 коммита (`388ed1a9`, `8e1f2ebf`, `ec639a54`, `a5b43616`); `--grep='^feat(16-36)'` — 4 коммита (`b67495dc`, `44452e68`, `b8d557f0`, `4ffef0c1`). Каждый `test` стоит перед своим `feat`. REFACTOR-коммитов нет. Нарушений нет.

## Issues Encountered

- Ожидания самопроверки и корпуса (д) пришлось уточнять по разбору ячеек:
  - в (д): шаблон `**{…}` терял именованные аргументы; у видов (в) / (г) лексики SQL предмет называет таблицу, а не колонку; у кратности учтено второе правдивое толкование 16-31;
  - в (е): цена «по находке на место»; ответ значения, поданного носителю без аргументов.
- Каждая правка ожидания проверена чтением ячеек. Ни одна не меняла ответ предиката.
- Все неверные ячейки корпуса на HEAD — на стороне гейта приватности:
  - (б): 288 ячеек кандидатных строк;
  - (в): 14 форм CR-02 / WR-24 / WR-25 / WR-26;
  - (г): 99;
  - (д) «способ подачи ссылки»: 42 (`methodcaller` у `starmap` и применённой обёртки).
- Это гэпы 2 и 3 — объём 16-37…16-39. Сторона писателя на HEAD верна во всех ячейках (а)–(д).

## Остатки и открытое (deferred-items.md не создавался — orchestrator_notes 5)

1. **Гейт приватности на той же семантике обёртки** — план 16-37. Перечисленные выше неверные ячейки — готовый вход его сверки.
2. **Корпус (д) — реконструкция осей по сводкам**, не прежние скрипты: их скрипты ушли вместе с worktree. Планы 16-37…16-39 получают инструмент от оркестратора и сверяют его с договором.

## Known Stubs

Нет.

## Threat Flags

Нет: правились только тестовый гейт и общий модуль тестов.

## User Setup Required

None — внешней настройки нет.

## Next Phase Readiness

- Вход плана 16-37:
  - гейт писателя держит по имени `carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`, `is_carrier_wrapper`, `wrapper_applications` — те же объекты общего модуля;
  - одноимённых помощников с подчёркиванием и без в модуле гейта нет;
  - `carrier_wrapper_bindings` без `nested` отвечает как прежде.
- Инструмент сверки в `.pytest_cache/r7diff/` оставлен вместе с `trees/` и `judged/`.
- Фаза остаётся в `gaps_found` до 16-37…16-40 и повторной верификации. PHONE-02 в REQUIREMENTS.md не отмечался.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-19*

## Self-Check: PASSED

- Файлы на месте: `tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`, `.pytest_cache/r7diff/{corpus.py,judge.py,run.sh}`.
- Коммиты плана в истории ветки: `388ed1a9`, `b67495dc`, `8e1f2ebf`, `44452e68`, `ec639a54`, `b8d557f0`, `a5b43616`, `4ffef0c1`. `git rev-list --count 1c243203..4ffef0c1` = 8.

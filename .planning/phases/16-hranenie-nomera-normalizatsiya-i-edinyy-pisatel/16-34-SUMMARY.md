---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 34
subsystem: testing
tags: [ast, phone, single-writer-gate, carrier-semantics, shared-grammar, parity, tdd, wr-19, wr-20, in-15]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль `tests/phone_gate_grammar.py` с семантикой носителя (`reference_arguments`, `literal_keyword_arguments`, `iterable_elements`, `getattr_literal` — 16-32), гейт писателя после 16-31 / 16-33 (537 правил, строки 215 / 92), гейт приватности 16-32 (222), правило-паритет 16-29 / 16-31 (14)"
provides:
  - "гейт писателя судит ссылку функцией общего модуля `reference_arguments` (с `every_reading=True`): позицией, `*`-распаковкой, ЛЮБЫМ именованным аргументом, в применённой обёртке; литеральные аргументы того же вызова — по общему правилу О-14 (а)"
  - "общий модуль: шесть строк `REFERENCE_CARRIERS` (11 носителей), `REFERENCE_KEYWORDS` выведен; `reference_arguments(every_reading=…)` — прочтение «как есть», каждая ссылка носителя, общее правило над позиционными литералами, `starmap`, именованная ссылка без позиционных обёртки; `carrier_wrapper_bindings`, `applied_wrapper`"
  - "гейт писателя без копий семантики носителя (`_iterable_elements`, `_getattr_literal`, `_expanded_arguments`, `_forwarded_arguments`, `_elementwise_arguments`, `_UNJUDGED_ELEMENT`, своя `LITERAL_CONTAINER_WRAPPERS` сняты)"
  - "правило-паритет: `GRAMMAR_FUNCTIONS` (24 имени), `GRAMMAR_TABLES` (7), `REQUIRED_SHARED_NAMES` (6); докстринги называют проверяемое; контроль `test_the_structural_half_reddens_a_redefined_grammar_point`"
  - "трасер `test_a_planted_backfill_with_a_threaded_writer_reference_reddens_the_gate`; 13 строк `LITERAL_FORM_CASES`, 4 строки `LEGITIMATE_CASES`; шапка — общее правило, цена, граница (1) по `args=row`, летопись WR-20 / IN-15"
affects: [16-35, phase-17, phase-18, phase-19, phase-20]

actuals:
  tokens: 24500
  tasks: 3
  commits: 10
plan_head_before: ab57357acb1458a0c1e33fa583849e11deda9f01
plan_head_after: 21d463f051880ad6bba53fb9905730e9840cf4a2

tech-stack:
  added: []
  patterns:
    - "Предикат ссылки — гейта, извлечение аргументов — общего модуля: гейт писателя подаёт `reference_arguments` предикат «узел через `_bound_reference` называет судимый API» и `IDENTIFICATION_CARRIERS` как не-носители"
    - "Альтернативные прочтения одного носителя (`every_reading`): «как есть» первым, общее правило следом, затем общее правило над позиционными литералами и `starmap`; одно место — одна находка (`readings` в `_phone_writes`)"
    - "Обёртка носителя под именем — общая `carrier_wrapper_bindings` (неподвижная точка по общей грамматике связывания) и `applied_wrapper`; предикат обёртки — гейта"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_gates_parity.py
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Прочтение «как есть» у носителя, который подаёт ссылке именованные аргументы без разбора (`run_sync(fn=…, mappings={…})`), судится ПЕРВЫМ, общее правило О-14 (а) — следом: иначе общее правило разбирало `mappings={\"id\": 1, \"phone\": p}` в `id=1, phone=p`, и две прежние ячейки матрицы наименований теряли находку"
  - "Новые прочтения — флагом `every_reading` функции общего модуля; гейт приватности зовёт её без флага, и его ответ прежний (222, живые деревья 225 / 68 / 93)"
  - "Обёртка носителя под именем (передано планом 16-32) закрыта у гейта писателя общей функцией `carrier_wrapper_bindings`; копия гейта приватности `_carrier_wrappers` осталась — модуль гейта приватности план правит только строкой ввоза (запрет №4)"
  - "Общее правило «по всем литеральным аргументам того же вызова» применено и к позиционным литералам за ссылкой (`pool.apply_async(setattr, (…), {})`) и к `starmap` — у гейта приватности те же формы с журналом ловятся (асимметрия О-12 (а))"

patterns-established:
  - "Самопроверка оси «как подана ссылка» у гейта писателя: 64 способа подачи × 7 значений опознания × 22 судимых API × 12 форм `BINDING_FORMS`; граница — аргументы нелитералом против базы «то же значение без аргументов»; законные — не-пишущая ссылка и чужой атрибут"

requirements-completed: [PHONE-02, PHONE-21]

coverage:
  - id: D1
    description: "Подложенный `threading.Thread(target=setattr, args=(account, \"phone\", number)).start()` в синтетическом `scripts/` краснит гейт писателя с файлом, строкой и видом; у вызова ровно одна находка"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_threaded_writer_reference_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пять форм WR-20 и общего правила, пять форм захода 1 и три формы зонда захода 2 самопроверки — строки LITERAL_FORM_CASES по одной находке; идиома Celery, чужой атрибут, обёртка под именем с не-пишущей ссылкой, `apply_async` с чужим атрибутом — ноль"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "Семантика носителя — один модуль: копий в гейте писателя нет, `REFERENCE_KEYWORDS` выведен, 11 носителей, обе матрицы и паритет — 720 ячеек без промахов и расхождений; структурная половина краснеет на каждом из 31 названного имени"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_structural_half_reddens_a_redefined_grammar_point"
        status: pass
      - kind: other
        ref: "task-2 <automated> #2 (OK 11 12 24) и #3 (OK) плана 16-34"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта писателя: любой именованный аргумент, литеральный кортеж / словарь, `reference_arguments`, цена `handler(fn=update, data={…})`, пункт (1) — `args=row`, летопись WR-20 / IN-15; заявление прежнее"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: "task-3 <automated> #2 плана 16-34 (OK)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Прежнее не ослаблено: 190 / 84 строк 4cd68671 и 215 / 92 строк старта плана на месте; живое дерево писателя — 0 судимых находок в 104 файлах, в писателе 6 сырых, реестр — ровно писатель; гейт приватности — 222, живые деревья 225 / 68 / 93, находок 0"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
    human_judgment: false

duration: 61min
completed: 2026-10-16
status: complete
---

# Phase 16 Plan 34: Гейт писателя на общей семантике носителя, ссылка в любом именованном аргументе — Summary

**Гейт единственного писателя теперь ищет ссылку на пишущий API функцией общего модуля `reference_arguments`, той же, что гейт приватности. Ссылка, поданная любым именованным аргументом (`target=`, `job=` и т. д.), судится вместе с литеральными аргументами того же вызова, и `threading.Thread(target=setattr, args=(account, "phone", x))` краснит гейт. Своих копий семантики носителя гейт писателя больше не держит, закрытая таблица ключа ссылки `REFERENCE_KEYWORDS` выведена. Общий словарь вырос до 11 носителей, правило-паритет говорит ровно то, что проверяет. Самопроверка прошла 98 952 формы композицией, нашла пять классов промахов, все закрыты двумя циклами RED/GREEN. Среди них обёртка носителя под именем, переданная планом 16-32.**

## Performance

- **Duration:** ≈61 мин
- **Started:** 2026-10-16T11:24:46Z
- **Completed:** 2026-10-16T12:26:16Z
- **Tasks:** 3 (плюс 2 цикла самопроверки)
- **Files modified:** 4

## Accomplishments

- **Гейт писателя на общей функции (WR-20, О-14 (а)):**
  - `_referenced_calls` и `_methodcaller_receivers` ищут ссылку через `reference_arguments`;
  - предикат ссылки остаётся у гейта: узел через `_bound_reference` называет судимый API;
  - привязанные аргументы `partial` по-прежнему идут впереди;
  - получатель `methodcaller` — первый аргумент, который носитель подаст ссылке.
- **Новые прочтения в общем модуле** — флаг `reference_arguments(every_reading=True)`, его использует только гейт писателя:
  - прочтение «как есть» — первым;
  - каждая позиционная и каждая именованная ссылка носителя;
  - общее правило над позиционными литералами за ссылкой (`pool.apply_async(func, (…), {…})`);
  - `starmap` — элементы каждого литерального кортежа;
  - именованная ссылка без позиционных аргументов обёртки.
- **Обёртка носителя под именем:** общие функции `carrier_wrapper_bindings` и `applied_wrapper`. У гейта писателя их зовёт `_carrier_wrappers`. Связывание по `module_bindings`, цепочки до неподвижной точки, у связывания повторной находки нет.
- **Копии сняты (IN-15, О-15):** `_iterable_elements`, `_getattr_literal`, `_expanded_arguments`, `_forwarded_arguments`, `_elementwise_arguments`, `_UNJUDGED_ELEMENT` и своя `LITERAL_CONTAINER_WRAPPERS`. Гейт ввозит общие объекты.
  - `_positional_arguments` — тонкая обёртка над `expanded_arguments`;
  - `_getattr_string` берёт строку у общего `getattr_literal`.
- **`REFERENCE_KEYWORDS` выведен:**
  - константа снята из общего модуля, на её месте летопись в комментарии;
  - снята из ввоза обоих гейтов; у гейта приватности это одна строка, `git diff --stat 83fac8e6^..HEAD -- tests/test_phone_privacy_gate.py` = `1 deletion`;
  - снята из `REQUIRED_SHARED_NAMES`;
  - `BINDING_CASES` отбирают строки `run_sync` по `KIND_BY_REFERENCE`.
- **Общий словарь:** шесть строк `REFERENCE_CARRIERS` — `starred`, `partial-wrapped`, `map-wrapped-iterable`, `thread-target`, `timer-args`, `invented-keyword`. Итого 11 носителей и 12 форм. Обе матрицы и паритет держат по 720 ячеек.
- **Правило-паритет:**
  - `GRAMMAR_FUNCTIONS` — грамматика связывания и семантика носителя, каждое имя с подчёркиванием и без (24 имени);
  - `GRAMMAR_TABLES` — 7 таблиц;
  - `REQUIRED_SHARED_NAMES` — 6 имён;
  - докстринг модуля и правила построения: названные точки не переопределены, копию под другим именем видит только поведенческая половина;
  - новый контроль `test_the_structural_half_reddens_a_redefined_grammar_point`.
- **Строки и правила:** трасер; `LITERAL_FORM_CASES` +13 (5 задачи 1, 5 захода 1, 3 зонда захода 2); `LEGITIMATE_CASES` +4 (2 задачи 1, 2 захода 1).
- **Шапка гейта писателя:**
  - общее правило именованного аргумента;
  - прочтение «как есть», позиционные литералы, каждая ссылка, обёртка под именем, `starmap`;
  - функция `reference_arguments`;
  - цена `handler(fn=update, data={"phone": x})`;
  - пункт (1): аргументы нелитералом (`args=row`, `kwargs=opts`, `*rows`);
  - летопись WR-20 / IN-15. Заявление прежнее.

## Task Commits

1. **Задача 1 (трасер): гейт писателя на `reference_arguments`** — `83fac8e6` (test, RED), `94b6c25d` (feat, GREEN).
2. **Задача 2: копии сняты, `REFERENCE_KEYWORDS` выведен, шесть носителей, паритет** — `9dc72673` (test, RED), `a28d6efc` (feat, GREEN).
3. **Задача 3: шапка** — `59b56ab1` (test, RED), `e5987a35` (feat, GREEN).
4. **Самопроверка, цикл 1: обёртка под именем, позиционные литералы, каждая ссылка** — `5e32c335` (test, RED), `147f5e46` (feat, GREEN).
5. **Самопроверка, цикл 2: именованная ссылка применённой обёртки, `starmap`** — `8e960227` (test, RED), `21d463f0` (feat, GREEN).

**Plan metadata:** коммит `docs(16-34)` с этой сводкой. Первый коммит плана — `83fac8e6`.

Гейт трасера после задачи 1: режим `end-of-phase`, у трасера только проверки `<automated>`. Все три команды `<verify>` прогнаны повторно и зелёные (`545 passed`, `OK 190 84`, `OK 6 104`), после чего план перешёл к задачам 2 и 3.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored, не закоммичено). По каждому есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех пяти записях.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_backfill_with_a_threaded_writer_reference_reddens_the_gate` | `1 failed, 544 deselected` | «ссылка на пишущий API, поданная именованным аргументом, не опознана» | Цель исполнилась: обход нашёл файл, находок `[]`. Весь модуль — 6 failed: трасер и пять новых строк, законные зелёные. |
| Задача 2 | `test_both_gates_take_the_binding_grammar_and_carriers_from_one_module` и `test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` (`-k "one_module or header_names_the_shared"`) | `2 failed, 558 deselected` | «гейты номера не делят одну грамматику связывания» и «шапка гейта писателя не называет общую грамматику связывания» | Гейт писателя определял 5 функций и 2 таблицы и не держал `getattr_literal` / `iterable_elements`. В шапке не было 5 имён носителей. Первый прогон упал на `AttributeError` (не на утверждении): RED поправлен до коммита, см. отступление 3. |
| Задача 3 | `test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` | `1 failed, 544 deselected` | «шапка гейта писателя не называет общую грамматику связывания» | 6 недостающих мест: `args=row` в пункте (1), «любым именованным аргументом», «литеральный кортеж», «литеральный словарь», «`reference_arguments`», «IN-15». |
| Цикл 1 | `test_a_literal_write_form_is_a_write[carrier-wrapper-bound-to-a-name-setattr]` (`-k "carrier-wrapper-bound or apply or after-a-judged"`) | `4 failed, 3 passed, 545 deselected` | «дала 0 находок вместо одной» | Четыре строки записи дали `[]`. Строка `apply-literal-argument-list-bulk-update` зелёная до GREEN (вид 6 находит словарь во вложенном списке) — это закрепка, а не RED-свидетель. Две законные строки зелёные. |
| Цикл 2 | `test_a_literal_write_form_is_a_write[starmap-literal-argument-tuples-setattr]` (`-k "application-args or starmap"`) | `2 failed, 1 passed, 552 deselected` | «дала 0 находок вместо одной» | `partial(threading.Thread, target=setattr)(args=(…))` и `itertools.starmap(setattr, [(…)])` дали `[]`. Строка `starmap-…-bulk-update` зелёная до GREEN — закрепка. |

## Самопроверка исполнителя (задача 3; урок 16-12, 16-17, 16-22, 16-27; О-14 (а))

Скрипт `.pytest_cache/1634_selfcheck.py` лежит в gitignored-каталоге worktree и в репозиторий не коммитится. Он однопроцессный и работает под общим `flock`; HEAD передаётся аргументом. Каждая форма подаётся в `phone_write_offences(…, "scripts/x.py")`. Под заявлением требуется ровно одна находка ожидаемого вида, предмет которой называет `phone`.

**Оси (итоговый заход 3):**
- **Способы подачи (64):**
  - позицией (`runner.call(R, …)`), после исполнителя (`loop.run_in_executor(None, R, …)`);
  - `*[…]` и `*(…)` — одной ссылкой, после других аргументов, целиком;
  - применённая обёртка `functools.partial(asyncio.to_thread, R)(…)`, она же через псевдоним `bind = functools.partial`;
  - обёртка носителя под именем (`w = …; w(…)`), под атрибутом (`self.w = partial(loop.run_in_executor, None, R)`), цепочкой (`h = w`), с привязанным аргументом;
  - `Timer(1.0, R, args=…, kwargs=…)`, `pool.apply_async(R, (…), {…})`, `pool.apply(R, […])`, `itertools.starmap`, `pool.starmap`;
  - применённая и именованная обёртка `partial(threading.Thread, target=R)(args=…)`;
  - `map` с `[…]`, `list([…])`, `tuple([…])`, `iter([…])`;
  - именованная ссылка `fn=`, `target=`, `function=`, `initializer=`, выдуманные `job=` / `payload=` × 7 форм аргументов: позиционные носителя, литеральный кортеж + словарь, список + `dict(…)`, пары `**{…}`, смесь, выдуманные ключи аргументов (`data=`, `options=`), ссылка парой `**{"<ключ>": R}`.
- **Значения опознания (7):** имя, атрибут, `getattr`-строка, `partial` с привязкой и без, `methodcaller` (применённый к получателю), псевдоним ввоза `as`.
- **Судимые API (22):**
  - `setattr`, `set_committed_value`, `set_attribute`, `flag_modified`, `object.__setattr__`;
  - строки `execute`, `scalars`, `bulk_update_mappings`, `bulk_insert_mappings`, `op.bulk_insert`;
  - `values` (словарём и именованным), `Query.update`, `insert`, `from_select`, `ordered_values`, `on_conflict_do_update`, `on_duplicate_key_update`;
  - конструктор модели, псевдоним модели, `MessengerAccount.__init__`, дескриптор `__set__`.
- **Формы связывания:** 12 `BINDING_FORMS`, включая `rebound*` 16-31 с безобидной подменой того же вида.
- **Граница (1):** аргументы нелитералом — `Thread(target=R, args=row)`, `args=row, kwargs=opts`, `job=R, data=row`, `to_thread(R, *rows)`, `*rows, **opts`, `*rows` перед именованной ссылкой. Ячейка сравнивается с базой «то же значение без аргументов»: учитывается только находка сверх базы.
- **Законные:** не-пишущая ссылка всех видов значений во всех способах; `setattr` с чужим атрибутом `"status"`.

| Заход | HEAD, время (UTC) | Под заявлением: подано / `[]` | Кратных | Граница: подано / сверх базы | Законные: подано / с находкой | Закрыто коммитами |
|-------|-------------------|-------------------------------|---------|------------------------------|-------------------------------|-------------------|
| 1 | `e5987a35`, 2026-10-16 11:50–11:55 | 92 064 / **5 832** — три класса (ниже) | 0 | 2 394 / 0 | 76 056 / 1 104 — все `insert`: цена шапки (ниже) | `5e32c335` / `147f5e46` |
| 2 | `147f5e46`, 12:03–12:08 | 92 064 / **0**; 48 — одна находка другого вида (ниже) | 0 | 2 394 / 0 | 76 056 / 0 (+ 1 104 цены) | зонд вне осей: два класса → `8e960227` / `21d463f0` |
| 3 (итог) | `21d463f0`, 12:12–12:18 | **98 952 / 0**; 48 — другой вид | **0** | **2 394 / 0** | **81 588 / 0** (+ 1 152 цены) | — |

**Классы захода 1 (5 832 формы, каждая под заявлением):**
- обёртка носителя под именем, атрибутом и цепочкой — 3 456 (по 1 128 + по 24 у `methodcaller`). Это и есть форма, переданная планом 16-32;
- литеральный кортеж или список ПОЗИЦИОННЫХ аргументов за ссылкой (`pool.apply_async(setattr, (account, "phone", x), {})`, `pool.apply(…, […])`) — 1 224. У гейта приватности та же форма с журналом ловится;
- именованная ссылка за позиционным аргументом, который сам судимое имя (`pool.call(MessengerAccount, rows, target=bulk_update_mappings)`): модель «выигрывала» как ссылка — 1 152.

**Зонд вне осей после захода 2** (гейт приватности обе формы с журналом ловит):
- `functools.partial(threading.Thread, target=setattr)(args=(…))` и её именованная обёртка: первый позиционный `partial` шёл ссылке аргументом;
- `itertools.starmap(setattr, [(…)])`, `pool.starmap(…)`.

Обе формы вошли в способы подачи захода 3.

**48 «другого вида»** — `pool.apply_async(values, (), {"phone": x})`. Прочтение «как есть» судит `values({"phone": x})` (ключ словаря values), общее правило — `values(phone=x)` (именованный аргумент). Место одно, находка одна, первым стоит «как есть». Это запись, пойманная на своём месте, а не слепота.

**Цена в законных (1 104 / 1 152 формы, только API `insert`):** `runner.call(helper.noop, MessengerAccount, phone=x)`. Модель среди аргументов носителя рядом с `phone=` судится как вызов модели. Это цена, названная в шапке до плана («имя пишущего API, поданное другому вызову, … судится как вызов этого API»).

**По осям на заходе 3:**
- формы связывания — по 8 246 на каждую из 12;
- способы: именованные 65 232, позиционные литералы 6 876, `*` 6 384, обёртка под именем 7 680, применённая обёртка 4 788, `map` 4 800, позиционные 3 192;
- значения: `methodcaller` 17 160, `partial` без привязки 16 320, с привязкой 15 564, атрибут и `getattr` — по 15 708, имя 14 064, ввоз `as` 4 428;
- API — от 2 628 (псевдоним модели) до 5 460 форм.

## Перенесённое от 16-32: обёртка носителя под именем — ЗАКРЫТО у гейта писателя

`w = functools.partial(asyncio.to_thread, setattr); w(account, "phone", x)` на старте плана давал `[]` (зонд `.pytest_cache/1634_probe.py`). Та же форма на месте давала находку. Закрыто циклом 1 (`5e32c335` / `147f5e46`):
- общий модуль получил `carrier_wrapper_bindings` и `applied_wrapper`, их имена вошли в `GRAMMAR_FUNCTIONS` паритета;
- гейт писателя судит вызов `w(…)` как применённую обёртку;
- строки `carrier-wrapper-bound-to-a-name-setattr` и `carrier-wrapper-bound-to-an-attribute-setattr`;
- заход 3 — ноль промахов на 7 680 формах оси.

**Остаётся открытым (с причиной):** гейт приватности держит ту же семантику своей функцией `_carrier_wrappers` (16-32, цикл 2) и на общую не переведён. Причина — запрет №4 плана: «модуль гейта приватности правится только строкой ввоза». Это копия под другим именем, которую структурная половина паритета по построению не видит; так и записано в комментарии `CARRIER_SEMANTICS` правила-паритета и в докстринге `carrier_wrapper_bindings`. Адресат — следующий план, правящий модуль гейта приватности.

## Живые деревья и реестры

- Гейт писателя: `OK 6 104`. В модуле-писателе 6 сырых находок (5 × именованный аргумент + 1 × запись атрибута по имени), живое дерево — 104 файла, 0 судимых находок. `PHONE_WRITER_EXCEPTIONS` — ровно `app/application/accounts/phone.py`.
- Гейт приватности: `Python-половина гейта приватности: app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0`. `PHONE_LOG_EXCEPTIONS == {}`, потолок 0.
- Строки (`.pytest_cache/1634_rows_check.py`): `OK 190 84 215 92 228 96`. Первые два числа — 4cd68671, вторые — старт плана, третьи — итог. Ни одна прежняя строка не потеряна и не изменена.

## Files Created/Modified

- `tests/phone_gate_grammar.py`:
  - шесть строк `REFERENCE_CARRIERS`;
  - `REFERENCE_KEYWORDS` → летопись в комментарии;
  - `_verbatim_keywords`, `_spread_arguments`, `_dump`;
  - `_carried_by` с прочтениями `every_reading`;
  - `reference_arguments(…, every_reading=False)`;
  - `carrier_wrapper_bindings`, `applied_wrapper`.
- `tests/test_application/test_phone_single_writer_gate.py`:
  - ввоз общих функций и таблиц;
  - копии сняты;
  - `_referenced_calls`, `_methodcaller_receivers`, `_carrier_wrappers`, `_getattr_string`;
  - `BINDING_CASES` по `KIND_BY_REFERENCE`;
  - трасер, строки, правило шапки, шапка.
- `tests/test_phone_gates_parity.py`:
  - `CARRIER_SEMANTICS`, `GRAMMAR_FUNCTIONS`, `GRAMMAR_TABLES`, `REQUIRED_SHARED_NAMES`;
  - сверка объектов терпит имя, которого в общем модуле нет;
  - докстринги;
  - правило-контроль.
- `tests/test_phone_privacy_gate.py`: снята строка ввоза `REFERENCE_KEYWORDS` (1 удалённая строка).

## Decisions Made

- **Прочтение «как есть» — первым.** У `run_sync(fn, *arg, **kw)` и `partial` ключ литерального аргумента — имя параметра ссылки. Без этого прочтения общее правило теряло две ячейки матрицы наименований (`run-sync-fn-bulk_*_mappings-bare-dict`). Первым оно стоит, чтобы прежние строки сохранили прежний вид находки.
- **Флаг вместо смены поведения общего модуля для обоих гейтов.** Гейт приватности судит номер в любом аргументе, и лишние прочтения ему ничего не добавляют. Без флага его ответ (222, живые деревья 225 / 68 / 93) прежний по построению, а не по замеру удачи.
- **Предикат обёртки — гейта, неподвижная точка — общая.** `partial` над судимым API — это `_partial_aliases` (псевдоним с привязкой), а не обёртка носителя. Обёртка носителя — `partial` над носителем, в аргументах которого `reference_arguments` находит ссылку на судимый API или `methodcaller`.
- **Шапка называет каждую форму захода 1 и зонда.** Ни одна из них не названа в границе.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Прочтение «как есть» у `reference_arguments`**
- **Found during:** задача 1, GREEN.
- **Issue:** общее правило разбирало литеральный словарь `mappings={"id": 1, "phone": p}` у `run_sync(fn=Session.bulk_update_mappings, …)` в `id=1, phone=p`. Две прежние ячейки `test_every_column_naming_in_every_judged_context_is_a_write[string]` / `[string-is-manual]` дали `[]` — прежний ответ потерян, а это запрещает запрет №4.
- **Fix:** флаг общего модуля, прочтение «как есть» первым, общее правило следом.
- **Files modified:** `tests/phone_gate_grammar.py` (в `<files>` задачи 1 его нет, в `files_modified` плана — есть).
- **Verification:** 781 passed на трёх модулях; строки `OK 190 84`; `OK 6 104`.
- **Committed in:** `94b6c25d`.

**2. [Rule 2 - Missing critical] Самопроверка, цикл 1: обёртка носителя под именем, позиционные литералы, каждая ссылка носителя**
- **Found during:** задача 3, самопроверка, заход 1 (5 832 формы `[]`).
- **Issue:** три класса выше. Каждая форма под заявлением; у гейта приватности первые два ловятся (асимметрия О-12 (а)).
- **Fix:** `carrier_wrapper_bindings` / `applied_wrapper`; `every_reading` — каждая ссылка и `_spread_arguments`; шапка называет формы. 5 строк `LITERAL_FORM_CASES` (одна — закрепка, зелёная до GREEN) и 2 строки `LEGITIMATE_CASES`.
- **Files modified:** все три файла плана, кроме модуля гейта приватности.
- **Verification:** 789 passed; заход 2 — 0 `[]`.
- **Committed in:** `5e32c335` (RED), `147f5e46` (GREEN).

**3. [Rule 1 - Bug] RED задачи 2 падал не на утверждении**
- **Found during:** задача 2, RED.
- **Issue:** сверка «тот же объект» звала `getattr(grammar, name)` для `_UNJUDGED_ELEMENT` гейта писателя, которого в общем модуле нет. Правило упало `AttributeError`, а это INVALID_RED.
- **Fix:** `getattr(grammar, name, None)`. Своя таблица под таким именем — «не объект общего модуля». Та же поправка нужна и после вывода `REFERENCE_KEYWORDS`.
- **Committed in:** `9dc72673` (RED, до прогона классификатора).

**4. [Rule 2 - Missing critical] Самопроверка, цикл 2 (зонд вне осей после захода 2)**
- **Found during:** задача 3, зонд.
- **Issue:** `functools.partial(threading.Thread, target=setattr)(args=(…))` и `starmap` давали `[]`; у гейта приватности обе формы с журналом ловятся.
- **Fix:** `every_reading` — именованная ссылка и без позиционных носителя, `starmap` поэлементно по кортежам. 3 строки `LITERAL_FORM_CASES` (одна — закрепка).
- **Committed in:** `8e960227` (RED), `21d463f0` (GREEN).

### Отклонения план → замер (замер побеждает, строки не снимались)

| Что | План | Замер | Почему |
|-----|------|-------|--------|
| гейт писателя после задачи 1 | ≥ 530 | 545 | база 537, а не 522 (строки самопроверок 16-31 / 16-33) |
| три модуля после задачи 2 | ≥ 763 | 782 | 545 + 222 + 15 |
| три модуля итог | — | 792 (база 773) | +19: строки циклов 1–2 и контроль паритета |
| гейт писателя итог | — | 555 (база 537) | +18 |
| quick run фазы | ≥ 1167 | 1196 (база 1177) | +19 |
| `LITERAL_FORM_CASES` / `LEGITIMATE_CASES` | 190 / 84 прежних | 228 / 96 (215 / 92 на старте) | +5 / +2 задачи 1, +5 / +2 цикла 1, +3 / 0 цикла 2 |
| RED задачи 2 | матрицы и паритет краснеют на 36 ячейках каждой строки с ключами | краснели только две цели | GREEN задачи 1 уже перевёл гейт писателя на общую функцию; 720 ячеек зелёные уже в RED задачи 2 |
| `GRAMMAR_FUNCTIONS` | — | 24 (20 после задачи 2) | +2 имени цикла 1 × 2 написания |
| самопроверка | ≥ 10 000 | 98 952 под заявлением | — |

---

**Total deviations:** 4 исправлены автоматически (2 — Rule 1, 2 — Rule 2), плюс расхождения чисел, описанные выше.
**Impact on plan:** все правки — в файлах `files_modified`. Модуль гейта приватности изменён одной удалённой строкой ввоза. Реестры, потолок, заявление и прежние строки не тронуты.

## Остатки и открытое (deferred-items.md не создавался — orchestrator_notes 6)

1. **Копия `_carrier_wrappers` гейта приватности** — см. раздел о перенесённом. Открыто из-за запрета №4.
2. **Комментарий гейта приватности `tests/test_phone_privacy_gate.py:362`** всё ещё говорит, что ввоз держит `REFERENCE_KEYWORDS` для правила-паритета. Строку ввоза план снял, а комментарий поправить нельзя по тому же запрету №4 (правка — только строка ввоза, `git diff --stat` не больше двух строк). Адресат — тот же следующий план.
3. **Формы самопроверки вне словаря `REFERENCE_CARRIERS`.** Обёртка под именем, `apply_async` с позиционными литералами, `starmap`, применённая обёртка с именованной ссылкой закреплены строками гейта писателя; у гейта приватности — его строками 16-32, кроме `starmap`. Поведенческая половина паритета их не держит: словарь план зафиксировал на 11 носителях (`OK 11 12`). Кандидаты в строки словаря — для плана, который будет его расширять.

## Замены команд (песочница worktree, хост)

- **Критерий задачи 1 «прежние строки»** (`git show` внутри `python -c`): эталоны сохранены простыми командами — `git show 4cd68671:… > .pytest_cache/1634_base_writer_4cd68671.py` и `git show ab57357a:… > .pytest_cache/1634_head_writer_ab57357a.py`. Та же логика сравнения исполнена скриптом `.pytest_cache/1634_rows_check.py`.
- **Третья команда задачи 1** исполнена дословно скриптом `.pytest_cache/1634_live_check.py`.
- **RED задачи 2** — команда критерия приёмки дословно в `.pytest_cache/1634_red_t2.sh` под тем же `flock`.
- **Самопроверка:** HEAD передаётся скрипту аргументом, без вызова `git` из Python.
- **Полная суита** (~5162 теста, ~46 мин) не гонялась: её гонит пост-мердж гейт оркестратора.
- **`graphify update .`** не запускался: граф обновит оркестратор после слияния. Ориентация шла по `graphify query … --graph /source/broadcaster/graphify-out/graph.json` (только чтение).
- **`.planning/WINDOWS.md`, `deferred-items.md`, STATE.md, ROADMAP.md, REQUIREMENTS.md** не писались (orchestrator_notes 6). Отложенное перечислено в «Остатках».

## Гейты на итоговом дереве (`21d463f0`, 2026-10-16, под `flock`)

- **Задача 1 `<automated>`:** #1 — гейт писателя `555 passed`; #2 — `OK 190 84` (с прежними строками старта — `OK 190 84 215 92 228 96`); #3 — `OK 6 104`.
- **Задача 1 критерии:** `grep -c` трасера = 1; `reference_arguments` = 13; `WR-20` = 14; ID строк — `OK`.
- **Задача 2 `<automated>`:** #1 — три модуля `792 passed`; #2 — `OK 11 12 24`; #3 — `OK`. `grep -c` контроля паритета = 1. Модуль гейта приватности: `1 file changed, 1 deletion(-)` от `83fac8e6^`.
- **Задача 3 `<automated>`:** #1 — `792 passed`; #2 — фразы шапки `OK`; #3 — quick run фазы `1196 passed`. Живые деревья и реестры — `OK`.
- **Оба гейта и паритет поимённо:** `792 passed` (база 773). Строка живых деревьев приватности — 225 / 68 / 93, находок 0.
- **`tests/test_application`:** `840 passed`. База на слитом дереве не мерилась; 822 — замер 16-33 в его worktree, разница +18 — ровно правила гейта писателя.
- **Сквозные гейты** `test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`: `576 passed` (2 мин 40 с). `tests/test_logging_config.py`: `3 passed`.
- **`uv run python -m compileall -q app main.py tests`:** код выхода 0.
- **`scripts/prohibitions_census.py --check`:** код выхода 0, «реестр: 837 строк, биекция с переписью — согласие». `tests/test_planning/test_plan_prohibitions_census.py`: `110 passed`.
- **`tests/test_planning`** гонится после коммита этой сводки, число — в финальном сообщении исполнителя.

## TDD Gate Compliance

- **RED:** `test(16-34)` — `83fac8e6`, `9dc72673`, `59b56ab1`, `5e32c335`, `8e960227`.
- **GREEN:** `feat(16-34)` — `94b6c25d`, `a28d6efc`, `e5987a35`, `147f5e46`, `21d463f0`.
- **REFACTOR:** не понадобился.
- Каждый RED предшествует своему GREEN; нарушений нет.

## Issues Encountered

Нет нерешённых в границах плана. Открытое — в «Остатках»: пункты 1–2 закрыть нельзя из-за запрета №4, пункт 3 — вне зафиксированного словаря.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

План 16-35 пишет строки диспозиции WR-18…WR-23 и IN-15 и пересевает реестр запретов. Для WR-20 и IN-15 коммиты этого плана:
- `94b6c25d` — гейт писателя на `reference_arguments`, любой ключ;
- `a28d6efc` — копии сняты, `REFERENCE_KEYWORDS` выведен, паритет называет проверяемое (IN-15);
- `e5987a35` — шапка;
- `147f5e46`, `21d463f0` — циклы самопроверки.

WR-19 на стороне писателя закрыт строками словаря (`9dc72673`).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-16*

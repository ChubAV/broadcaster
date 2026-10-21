---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 49
subsystem: testing
tags: [single-writer-gate, privacy-gate, phone, ast, shared-dictionary, collision-of-kinds, module-object, receiver, named-cost, base-head-diff, foreign-corpora, tdd]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "предикаты обоих гейтов после 16-46…16-48 (суд каждого толкования, объект модуля, узел получателя, суд каждого толкования вызова); инструмент r9diff 16-48 (копия оркестратора)"
provides:
  - "общий словарь девятого круга: IdentificationValue.rival и IdentificationValue.method, место {rival} у формы и носителя, восемь строк BINDING_FORMS (collision-*, module-object-*), две строки REFERENCE_CARRIERS (carrier-name-bound-to-a-rival, executor-name-bound-to-a-rival), значение receiver у обоих гейтов, API_IDENTIFICATION_CALLS[receiver] — 21 × 7 × 23 = 3 381 ячейка на гейт"
  - "правила-паритет test_the_shared_dictionary_holds_the_round_nine_axes и test_the_dictionary_chronicles_name_what_the_measure_compared (IN-21); летописи словаря восьмого и девятого круга обеих шапок называют корпус меры"
  - "названная цена kw_ext по решению владельца 2026-10-21: абзац цены строгости шапки писателя и закрепка NAMED_COST_CASES (3 строки по две находки)"
  - "инструмент .pytest_cache/r9diff/ (gitignored): вердикт v2 и правило пункта 9 для ячеек без точного ожидания (T11c), dup_control, режим --dictionary, семейства (к11)/(к12) «одно имя — две роли» у обоих гейтов, итоговая самопроверка партии (66 116 форм), улика kw / kw_ext, учёт изменённых ячеек"
affects: [16-50]

actuals:
  tokens: 35100   # chars/4: отслеживаемый дифф 86 538 знаков (≈21 600) + своё в gitignored-инструменте ≈54 000 знаков (≈13 500)
  tasks: 3
  commits: 6      # git rev-list --count c51755fc..e5090ac8 (до коммита сводки)
plan_head_before: c51755fc8e0325ed5ccbd2e036c9d1a7bbba2974
plan_head_after: e5090ac8e5a559d6e83d0cff7ba00ece9fb2684e

tech-stack:
  added: []
  patterns:
    - "Соперник другого вида — поле значения опознания (как decoy); формы коллизии видов и носители с соперником берут его местом {rival}, пустой соперник — вакуум"
    - "Метод значения-получателя — поле значения; binding_form_source дописывает .method к ссылке формы"
    - "Названная цена закрепляется строкой таблицы с числом цены, а не числом мест: правка, меняющая число, видна"
    - "Летопись меры называет корпус, его оси, размеры и sha256, а не свойство гейтов"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_privacy_gate.py
    - tests/test_phone_gates_parity.py

key-decisions:
  - "Соперник приватности — print, писателя — update (без пары kw_ext в матрице); пара receiver у писателя — account.__setattr__(\"phone\", x) (колонка в применении)"
  - "kw_ext — названная цена по решению владельца 2026-10-21: шапка называет механику, охват и решение; три строки NAMED_COST_CASES закрепляют ровно две находки; в инструменте — группа цены, не дефект"
  - "Правило пункта 9 договора r9diff для ячеек без точного ожидания: сжатие повторов текста — REPAIRED, если множество текстов то же, у ревизии каждый текст один раз и число не ниже «пола мест» (узлы phone в исходнике)"
  - "Семейство «одно имя — две роли» у обоих гейтов через общую грамматику: роль другого гейта (вызываемое журнала у писателя, пишущий API у приватности) под именем носителя (к11) и под именем связывания (к12)"

patterns-established:
  - "run.sh --dictionary --at <ревизии>: строки словаря девятого круга по таблицам HEAD судятся деревом каждой ревизии (DICT)"
  - "Учёт изменённых ячеек сверки по классу и направлению (changed_by.py) и сверка текстов (texts_dump.py)"

requirements-completed: []   # PHONE-02, PHONE-21 в requirements плана; отметку Complete не ставим — вердикт фазы gaps_found, учёт ведёт оркестратор (заметка 5)

coverage:
  - id: D1
    description: "Восемь форм девятого круга (коллизия видов, чтение через объект модуля) с соперником значения: обе матрицы и паритет держат их на каждом значении и носителе"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_shared_dictionary_holds_the_round_nine_axes; #test_both_gates_agree_on_every_binding_form_identification_and_carrier[collision-*, module-object-*]"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK 21 1008"
        status: pass
    human_judgment: false
  - id: D2
    description: "Значение receiver у обоих гейтов, поле method, два носителя с соперником, API_IDENTIFICATION_CALLS полна; 3 381 ячейка на гейт по одной находке"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_binding_form_of_a_writer_api_alias_is_judged; tests/test_phone_privacy_gate.py#test_every_binding_form_of_a_log_reference_is_judged"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_cells.py → OK 3381"
        status: pass
    human_judgment: false
  - id: D3
    description: "IN-21: летописи восьмого круга называют корпус меры раунда 8 и чего в нём не было; летопись девятого круга — так же; решение владельца о kw_ext в шапке писателя и в строках NAMED_COST_CASES"
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_dictionary_chronicles_name_what_the_measure_compared; tests/test_application/test_phone_single_writer_gate.py#test_a_named_cost_form_gives_its_named_count"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t3_docs.py → OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Итог меры партии раунда 9: run.sh 16-49 и четыре прогона «против» — 0 / 0, HEAD_WRONG=0, EXTERNAL HEAD defects=0, COST kw=281 attr=122, kw_ext с уликой; итоговая самопроверка 66 116 форм — 0 неверных на HEAD"
    verification:
      - kind: other
        ref: "bash .pytest_cache/r9diff/run.sh 16-49 / --against-batch 16-46 / --against fb8fef72 / 1c243203 / 2f8c1656 (все rc=0, 2026-10-21 18:16–18:46 UTC)"
        status: pass
    human_judgment: false

duration: 224min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 49: словарь девятого круга (коллизия видов, объект модуля, получатель, носитель с соперником), летописи меры IN-21 и закрытие партии раунда 9 — Summary

**Общий словарь получил соперника другого вида и метод значения. В нём пять форм коллизии видов, три формы чтения через объект модуля, значение-получатель `receiver` у обоих гейтов и два носителя, чьё имя связано с соперником. Это 21 × 7 × 23 = 3 381 ячейка на гейт; обе матрицы и паритет держат каждую ровно одной находкой. Летописи восьмого круга обеих шапок больше не записывают итог меры как свойство гейтов: они называют корпус (64 483 ячейки, `fd55d467…`) и то, чего в нём не было. Летопись девятого круга написана так же. Владелец принял `kw_ext` как цену: решение названо в шапке писателя и закреплено тремя строками по две находки. Партия раунда 9 закрыта мерой с чужими корпусами: против базы партии, `fb8fef72`, `1c243203` и `2f8c1656` — ноль регрессий обеих осей, `HEAD_WRONG=0`, `EXTERNAL … defects=0`. T11c теперь `REPAIRED` по правилу пункта 9, а контроль доказывает, что правило не вакуумно.**

## Performance

- **Duration:** ~224 мин
- **Started:** 2026-10-21T15:30:07Z
- **Completed:** 2026-10-21T19:14Z (до коммита сводки)
- **Tasks:** 3 (у каждой RED и GREEN; циклов самопроверки и дифференциальной регрессии не понадобилось)
- **Files modified:** 4 отслеживаемых (+619 / −34)

## Accomplishments

- **Словарь девятого круга (задачи 1–2).** `IdentificationValue.rival` и `IdentificationValue.method`; `binding_form_source` ставит `{rival}` в шаблон формы и носителя и дописывает `.method` к ссылке. Пустой соперник — `AssertionError`, как у `{decoy}`. Добавлены:
  - `BINDING_FORMS`: `collision-module`, `collision-in-function`, `collision-rebound`, `collision-other-init`, `collision-class-body`, `module-object-getattr`, `module-object-attribute`, `module-object-bound`;
  - `REFERENCE_CARRIERS`: `carrier-name-bound-to-a-rival`, `executor-name-bound-to-a-rival`;
  - значения `receiver`: у приватности `logging.getLogger()` + `.info("x %s", account.phone)`, у писателя `account` + `.__setattr__("phone", x)`;
  - соперник `print` у каждого значения приватности и `update` — у каждого значения писателя; `API_IDENTIFICATION_CALLS["receiver"] = "__setattr__"`.
- **Предикаты не правились.** Все 3 381 ячейки на гейт пойманы предикатами 16-46…16-48: `OK 3381`. Режим `--dictionary` на дереве `1163ae39`: писатель 210 промахов, приватность 153 — ровно замер планирования.
- **IN-21 (задача 3).** Правило-паритет `test_the_dictionary_chronicles_name_what_the_measure_compared`. Летописи словаря восьмого круга переписаны, летописи девятого круга добавлены в обе шапки.
- **`kw_ext` — решение владельца.** Абзац цены строгости шапки писателя называет пару kw, её расширение на ось носителя, охват и решение 2026-10-21. `NAMED_COST_CASES` — три строки, по одной на соперника (`setattr`, `set_committed_value`, `flag_modified`), ровно две находки на одном узле колонки.
- **Инструмент.**
  - Вердикт v2 и правило пункта 9 для ячеек без точного ожидания (T11c) с контролем `dup_control.sh`.
  - Режим `--dictionary`.
  - Семейства (к11) / (к12) «одно имя — две роли» у обоих гейтов через общую грамматику.
  - Итоговая самопроверка партии — 66 116 форм.
  - Улика `kw` / `kw_ext` в `cost_evidence.py`, перечень 281 id `COST-KW`.
  - Учёт изменённых ячеек (`changed_by.py`, `texts_dump.py`, `ups_by.py`, `repaired_classes.py`).

## Task Commits

1. **Задача 1 (трасер): RED** — `6b4c0d52` (test)
2. **Задача 1: GREEN** — `f7948e5b` (feat)
3. **Задача 2: RED** — `ca8f5c0d` (test)
4. **Задача 2: GREEN** — `8138ba46` (feat)
5. **Задача 3: RED** — `e8fdf4c6` (test)
6. **Задача 3: GREEN** — `e5090ac8` (feat)

**Plan metadata:** коммит этой сводки (`docs(16-49)`).

## TDD: RED и GREEN

**RED задачи 1** (`6b4c0d52`). Прогон `uv run pytest tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py -q -p no:randomly -k "round_nine_axes or header_names_the_shared" --junit-xml=.pytest_cache/gsd-red/16-49-t1.xml`, 15:43:53Z.
- Строки `FAILED tests/test_phone_gates_parity.py::test_the_shared_dictionary_holds_the_round_nine_axes` и `FAILED …::test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` (и правило шапки приватности) есть.
- Последняя строка сводки: `3 failed, 929 deselected, 1 warning in 1.02s`.
- Литерал «шапка гейта писателя не называет общую грамматику связывания» — 2 вхождения (в дереве до плана он есть). Литерал RED этой задачи — «словарь матриц и паритета не держит ось девятого круга», 2 вхождения.
- `gsd check tdd-red-evidence .pytest_cache/gsd-red/16-49-t1.json` → `RED_EVIDENCE_OK` (`target_test_failed`; tests 3, fail 3).
- Смысловая оценка: цель исполнилась и упала на утверждении словаря. В `BINDING_FORMS` не было восьми форм, у двенадцати значений не было соперника, шапки не называли две формы. Ошибок сбора, ввоза и фикстур нет.
- Модули целиком на RED: `3 failed, 929 passed`.

**GREEN задачи 1** (`f7948e5b`): поле `rival`, место `{rival}`, восемь строк `BINDING_FORMS`, соперники значений, тексты шапок. После коммита — трасер проверен целиком: три модуля 956 passed, `OK 21 1008`, `run.sh 16-49` rc=0.

**RED задачи 2** (`ca8f5c0d`). Прогон плана `uv run pytest tests/test_phone_gates_parity.py -q -p no:randomly -k test_the_shared_dictionary_holds_the_round_nine_axes --junit-xml=.pytest_cache/gsd-red/16-49-t2.xml`, 16:18:22Z.
- `FAILED tests/test_phone_gates_parity.py::test_the_shared_dictionary_holds_the_round_nine_axes`.
- Последняя строка: `1 failed, 30 deselected, 1 warning in 0.65s`.
- Литерал правила задачи 1 «словарь матриц и паритета не держит ось девятого круга» — 2 вхождения. Провалы: `receiver` не последнее значение у обоих гейтов; `API_IDENTIFICATION_CALLS` у `receiver` — `None`; нет двух строк `REFERENCE_CARRIERS`.
- `RED_EVIDENCE_OK`. Правила шапок — отдельный прогон `-k header_names_the_shared --junit-xml=…16-49-t2h.xml` (16:18:35Z): `2 failed, 923 deselected`, литерал «шапка гейта писателя не называет общую грамматику связывания» (2 вхождения), `RED_EVIDENCE_OK`.

**GREEN задачи 2** (`8138ba46`): поле `method`, `{rival}` в шаблоне носителя, две строки носителей, значения `receiver`, `API_IDENTIFICATION_CALLS["receiver"]`, тексты шапок.

**RED задачи 3** (`e8fdf4c6`). Прогон плана `uv run pytest tests/test_phone_gates_parity.py -q -p no:randomly -k "chronicles_name_what_the_measure_compared" --junit-xml=.pytest_cache/gsd-red/16-49-t3.xml`, 17:05:01Z.
- `FAILED tests/test_phone_gates_parity.py::test_the_dictionary_chronicles_name_what_the_measure_compared`.
- Последняя строка: `1 failed, 31 deselected, 1 warning in 0.68s`.
- Литерал RED этой задачи «летописи словаря не называют, что мера сверяла» — 2 вхождения. У обоих гейтов: нет летописи девятого круга; в летописи восьмого круга нет «64 483», «fd55d467», «корпус», а фраза-итог есть.
- `RED_EVIDENCE_OK`.
- Правила шапок и закрепки — прогон `-k "header_names_the_shared or named_cost_form" --junit-xml=…16-49-t3h.xml` (17:07:18Z): `2 failed, 3 passed, 923 deselected`, `RED_EVIDENCE_OK`. Три строки `NAMED_COST_CASES` зелёные до GREEN: это закрепки цены, а не заявление.

**GREEN задачи 3** (`e5090ac8`): тексты двух летописей в обеих шапках, абзац цены строгости писателя, абзац докстринга паритета. Предикаты не тронуты.

## TDD Gate Compliance

В каждой задаче `test(16-49)` стоит перед своим `feat(16-49)`: `6b4c0d52` → `f7948e5b`, `ca8f5c0d` → `8138ba46`, `e8fdf4c6` → `e5090ac8`. `refactor` нет. Нарушений в истории нет; процессная оговорка задачи 3 — в отступлении 8.

## Итоговая самопроверка партии раунда 9 (задача 3; О-20 (а), свойства 6, 8; О-21 (а), свойство 4)

Генератор — `.pytest_cache/r9diff/selfcheck_1649.py` (gitignored). Ячейки — `sc1649_cells.json`, sha256 `17265433d8cd892f6d38ebba7840b48c544f18736bef7e559291e3901a087e8c`; это теперь `selfcheck_cells.json`. Ячейку собирает `binding_form_source` дерева HEAD (`8138ba46` = код предикатов итогового HEAD `e5090ac8`). Суд — `judge.py` в отдельном процессе под общим `flock`, 2026-10-21 17:12–17:19 UTC.

**Части:**
- **A — соперник × место × значение × форма × способ.**
  - Соперник: у приватности 5 вызываемых журнала, у писателя `setattr`, `update`, `set_committed_value`, `flag_modified`, `functools.partial(setattr, other)`. Он же — поле `rival` значения ячейки: его берут формы коллизии и носители с соперником.
  - Место: модуль, функция, повторное связывание после формы, `__init__` другого класса, тело другого класса — под именем `f`; последнее имя вызова носителя.
  - Значение — 7, форма — 21, способ — 23.
  - Полный крест — 101 430 на гейт. Взято по 6 пар «соперник × место» на ячейку матрицы по кругу `(i·7 + 5k) mod 30`: каждая ячейка — шесть пар, каждая пара — у каждой пятой ячейки.
- **B — чтение через объект модуля** (getattr, с умолчанием, атрибут, связанное имя `me`, цепочка `me2 = me`) × значение × способ × номер / двойник: 1 610 на гейт.
- **C — две подачи на одной строке** (D1 / D2) с двойником на двух строках: 3 381 на гейт.
- **D — безопасные двойники** части A (первая пара каждой ячейки) и части C.

**Итого 66 116 форм** — приватность 32 980, писатель 33 136 (≥ 15 000 на гейт). Повторов исходника отброшено 364.

**Ожидание** — число мест генератора (`kfam.p_expect` / `kfam.w_expect`: узлы номера / колонки в исходнике). Названные цены — отдельными классами с допустимым числом: `kw` (513 размечено) и `kw_ext` (503).

| Дерево | Форм | Неверных | Цена | Число находок (ожидание → найдено) |
|--------|------|----------|------|-------------------------------------|
| HEAD (`8138ba46`, код = `e5090ac8`) | 66 116 | **0** | 617: `kw` 490, `kw_ext` 127 | приватность: A 1→1 21 315; B 0→0 770, 1→1 790; C 1→1 880, 2→2 2 438; D 0→0 6 787. Писатель: A 1→1 20 698, 1→2 617 (цена); B 0→0 795, 1→1 795; C 1→1 440, 2→2 2 899; D 0→0 6 892 |
| контроль против вакуума: база партии `d31d86db` | 66 116 | **5 557** | 562 | приватность A 1 621 (1→0), B 125, C 153; писатель A 2 958 (1→0; носитель с соперником и пр.), B 50, C 650 (D2 2→1 440 — WR-31; D1 2→0 210) |

**Ячейки цены на HEAD (`sc_cost_check.py`):** все 617 — ровно механика цены, `bad=0`. Две находки на одной строке: `<соперник>(…, MessengerAccount.phone, …)` и `MessengerAccount.phone.__set__(…)`.
- `kw`: 490 из 513 размеченных дают 2, остальные 23 — 1 (допустимый ответ).
- `kw_ext`: 127 из 503 дают 2, только у носителей `to_thread`, `run_sync`, `Context.run`, `to_thread(*[…])` и у словарного `carrier-name-bound-to-a-rival` (тоже `to_thread`). Это охват, замеренный 16-48.

**Найдено:** первый прогон дал 30 неверных ячеек писателя — формы `collision-*` × `methodcaller-receiver` × соперник `functools.partial(setattr, other)` на месте «имя носителя». Ручная проверка: две находки на одной строке, пара kw. Форма коллизии сама связывает соперника под `f`, а генератор размечал цену kw только у прочих мест. Это дефект разметки генератора, а не гейта (отступление 6). После правки — 0. Циклов RED/GREEN не понадобилось. Выборка 3 000 из 66 116 (seed 49) вошла в корпус источником (е) `f-self-check`. Самопроверка 16-48 стала `f-self-1648`: та же выборка 3 000 из 29 328, seed 48.

## Улика исполнения названных цен

`.pytest_cache/r9diff/cost_evidence.py`, строки печатает `run.sh 16-49` (CONTROL — в stderr). Ячейки kw / kw_ext исполняются с настоящей моделью `MessengerAccount`: объект транзиентный, без базы и без `.env`. Записи колонки `phone` считает слушатель SQLAlchemy; `other` — пустой объект.

```
EVIDENCE attr: file='+79991234567' log='' cell=class-body/print
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/partial
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logging.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/print
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/partial
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logging.info
EVIDENCE kw: writes=1 column=phone value='+79991234567' other_untouched=True findings=2
EVIDENCE kw_ext: api=setattr findings=2 sets=1 phone='+79991234567'
EVIDENCE kw_ext: api=set_committed_value findings=2 sets=1 phone='+79991234567'
EVIDENCE kw_ext: api=flag_modified findings=2 sets=1 phone='+79991234567'
```

Контроли (stderr):
- `CONTROL kw_ext: api=<…> unapplied findings=0 sets=0` ×3;
- `CONTROL kw_ext: plain (без связывания имени носителя) findings=1 sets=1 phone='+79991234567'`;
- 10 строк `CONTROL attr: … log='+79991234567…'`.

Итог по ценам:
- **kw** — одна запись при двух находках, `other` не тронут.
- **kw_ext** — одна запись при двух находках у каждого из трёх соперников.
- **attr** — номер в файле, журнал пуст.

## Сверка «база ↔ HEAD» партии раунда 9 (пункт 10 договора `16-46-PLAN.md`; свойства 3, 7 О-21 (а))

### Чужие входы

Копия оркестратора: `cp -a` трёх каталогов в `.pytest_cache/`. Пути на удалённые worktree встречаются только в старых отчётах `r9diff-src/r8diff/*.report.json` и `sc_chain.sh`, а не в скриптах. `sha256sum -c --quiet MANIFEST.sha256` — 62 файла, совпадение (`INPUTS_OK files=62` в каждом прогоне). Корпуса — те же, что у 16-46…16-48:

| Файл | Байт | sha256 | Ячеек |
|------|------|--------|-------|
| `verify-r9/corpus.json` | 9 880 738 | `5c6c4527733eef1541fe88f144c1a4fd97e74907cfb401b32c8c32fba6acb7f5` | 20 769 |
| `verify-r9/hand.json` | 13 135 | `9812cb4780a8201c1abb6774ccf652e4d6a2e1e625f165078261600edb7afd69` | 39 |
| `review-r8/corpusK.json` | 2 639 220 | `2ee9e5f2998a3606527efaaf2c80197c631af9e0d058e3afbae843c13a08481b` | 6 600 |
| `review-r8/corpusKC.json` | 654 066 | `5ae59c54cfc0ca5058e3d45c634828397b6da9202860b073a05f4ed7b8c249f7` | 2 106 |
| `review-r8/hand.json` | 37 454 | `b1e6dc9f04c8d80581999488373437405dcf1db0fe28a94d5b6180cea0a8a0a4` | 115 |
| `review-r8/rows.json` | 98 393 | `761690482879a829f2a4da9f8ec8bfbb6402645f0b5909f647b53f428b47766e` | 312 |
| итого | | | **29 941** |

### Корпус сверки партии раунда 9: что прогнано и что нет

Итоговый корпус — HEAD `e5090ac8`, **156 352 ячейки**, `corpus.json` sha256 `204f02d870a8c4fc53e977ca3e46e267fa86bdc662c56ec59c781832151cabc3`. Корпус рос до доверия каждому GREEN (заметка оркестратора 8):
- с `--precommit` задачи 1 — 147 325 ячеек (`a42278e6…`): формы девятого круга в (б)/(ж)/(з), (к11), (к12), вердикт v2;
- задачи 2 — 153 349 (`b97f7ea7…`): значение `receiver` и носители;
- задачи 3 — 156 352: итоговая самопроверка партии, `f-self-1648`, строки `a-cost`.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 268, `LEGITIMATE_CASES` 107, **`NAMED_COST_CASES` 3 (`a-cost`, новое: ожидание — один узел колонки, цена `kw_ext` 2)**, `NEGATIVE_CONTROLS` 173, `POSITIVE_CONTROLS` 61 | 612 |
| (б) матрица `b-matrix` | 21 форма × 7 значений × 23 способа × 2 гейта | 6 762 |
| (ж) две подачи `g-double` | | 6 762 |
| (з) безопасные двойники `h-safe` | | 13 524 |
| (в) формы ревью | | 106 |
| (г) дифференциал раунда 7 | словарь закреплён на 12 формах и 5 значениях | 700 |
| (д) выборка самопроверок | 15 семейств по 2 000 (seed 42) | 30 000 |
| (е) `f-self-1644` / `f-self-1646` / `f-self-1647` | 20 000 из 66 690 / 6 000 из 84 750 / 3 000 из 12 444 | 29 000 |
| (е) `f-self-1648` (новое имя) | самопроверка 16-48: 3 000 из 29 328 (seed 48) — прежний `f-self-check` корпуса `f22ae991…` | 3 000 |
| (е) `f-self-check` | **итоговая самопроверка партии раунда 9: 3 000 из 66 116 (seed 49)** | 3 000 |
| (и) чужие корпуса | шесть файлов целиком | 29 941 |
| (к1)…(к5), (к8) | 3 000, 1 590, 600, 2 050, 3 000, 1 560 | 11 800 |
| (к6) | 4 000 из 4 672 (вырос с 3 856 новыми носителями и значением) | 4 000 |
| (к7) | целиком (4 200, потолок поднят до 5 000) | 4 200 |
| (к9) | 4 000 из 17 323 | 4 000 |
| (к10) | целиком | 945 |
| **(к11) «одно имя — две роли», имя носителя, оба гейта** (новое) | последнее имя вызова носителя связано с ролью ДРУГОГО гейта: у писателя — с вызываемым журнала (5), у приватности — с пишущим API (5); 4 места × носитель × значение опознания гейта (HEAD) × форма `assign` × номер / двойник; 4 000 из 15 050 | 4 000 |
| **(к12) «одно имя — две роли», имя связывания, оба гейта** (новое) | имя `f` связано с ролью другого гейта в 5 местах × форма (`assign`, `attribute-in-method`, `class-body`, `getattr-read`) × значение × прямой вызов и каждый носитель × номер / двойник; 4 000 из 57 400 | 4 000 |

**Не прогнано выборкой** — и что прогнано целиком отдельно:
- (д) — 11 119 725 форм полного перебора генераторов.
- `f-self-1644` — 46 690; `f-self-1646` — 78 750; `f-self-1647` — 9 444; `f-self-1648` — 26 328. Эти самопроверки их планы прогнали целиком.
- `f-self-check` — 63 116 (самопроверка 16-49 прогнана целиком: 66 116 на HEAD и на `d31d86db`).
- (к1) 6 000, (к5) 6 000.
- (к6) 672 и (к9) 13 323. Оба семейства судились целиком отдельно (`kfam_full2.sh`): (к6) 4 672 — HEAD 0 неверных (`kw_ext` 30), база партии 1 095; (к9) 17 323 — HEAD 0 (`kw_ext` 120), база 4 678.
- (к11) 11 050 и (к12) 53 400. Оба судились целиком отдельно (`kfam_full.py`, 72 450 ячеек):
  - HEAD — 0 неверных;
  - база партии `d31d86db` — 0;
  - `a77263ad` — 0;
  - `2f8c1656` — 26 085 неверных (5 760 + 20 325), и все они — прежние пропуски носителей-обёрток раунда 7 (`wrapper-handed`, `named-wrapper-handed`, …), а не коллизия.

  **Значит, семейство не нашло ни одного дерева, где роль другого гейта под общим именем закрывает путь.** Это охрана общей грамматики от такого возврата, а не замер найденного дефекта.

Целиком: строки таблиц, матрица, формы ревью, дифференциал, (ж), (з), чужие корпуса, (к2), (к3), (к4), (к7), (к8), (к10).

### Строки итогового прогона и прогонов «против»

`bash .pytest_cache/r9diff/run.sh 16-49` под общим `flock`, HEAD `e5090ac8`, 2026-10-21 18:16:42–18:18:17 UTC, **rc=0**. Дословно, без `EXTERNAL-CELLS` и `CORPUS` (stderr):

```
INPUTS_OK files=62
CORPUS_SHA256=204f02d870a8c4fc53e977ca3e46e267fa86bdc662c56ec59c781832151cabc3 HEAD=e5090ac8e5a559d6e83d0cff7ba00ece9fb2684e
SELFTEST 1bebbbf7 -> c6953017: cells=6868 regressions=81 count_regressions=81 fixed=360 repaired_overcount=0 changed=441
SELFTEST 5e32c335 -> 147f5e46: cells=6868 regressions=109 count_regressions=109 fixed=373 repaired_overcount=0 changed=483
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=7102 regressions=1590 count_regressions=1682 fixed=682 repaired_overcount=644 changed=2456
SELFTEST-CR04 e1d6587e -> a77263ad: cells=18221 regressions=1510 count_regressions=1510 fixed=0 repaired_overcount=0 changed=1510
REPRODUCE fb8fef72 K: cells=6600 mismatch=0
REPRODUCE fb8fef72 KC: cells=2106 mismatch=0
REPRODUCE e1d6587e K: cells=6600 mismatch=0
REPRODUCE e1d6587e KC: cells=2106 mismatch=0
REPRODUCE a77263ad K: cells=6600 mismatch=0
REPRODUCE a77263ad KC: cells=2106 mismatch=0
REPRODUCE 1c243203 K: cells=6600 mismatch=0
REPRODUCE dbc73537 K: cells=6600 mismatch=0
REPRODUCE dbc73537 KC: cells=2106 mismatch=0
DIFF 6b4c0d52 -> f7948e5b: cells=156352 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF ca8f5c0d -> 8138ba46: cells=156352 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF e8fdf4c6 -> e5090ac8: cells=156352 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE c51755fc -> HEAD e5090ac8: cells=156352 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
EXTERNAL c51755fc: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
EXTERNAL HEAD e5090ac8: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
COST kw=281 attr=122
COST-OWN kw=225 attr=480 kw_ext=78
COST-ATTR-IDS n=122 sha256=deaa985492817b71e9c917fa4b79205c3e41de1c9da97d117fcdba0cb000b3da
COST-KW-IDS n=281 sha256=61dfde10d51caa73ec06a22643fe5e574e7e48c8ff39fed4505380ec90f784e9
EVIDENCE attr: … (10 строк — выше)
EVIDENCE kw: writes=1 column=phone value='+79991234567' other_untouched=True findings=2
EVIDENCE kw_ext: api=setattr findings=2 sets=1 phone='+79991234567'
EVIDENCE kw_ext: api=set_committed_value findings=2 sets=1 phone='+79991234567'
EVIDENCE kw_ext: api=flag_modified findings=2 sets=1 phone='+79991234567'
HEAD_WRONG=0
OPEN_REGRESSIONS=0
```

Прогоны «против» — под общим `flock`, корпус `204f02d8…`. В каждом: `INPUTS_OK files=62`, четыре строки самопроверки и девять `REPRODUCE` — те же, что выше.

```
AGAINST d31d86db -> HEAD e5090ac8: cells=156352 regressions=0 count_regressions=0 fixed=11092 repaired_overcount=1991 changed=15741
EXTERNAL d31d86db: cells=29941 wrong=2754 cost_kw=281 cost_attr=122 defects=2351
EXTERNAL HEAD e5090ac8: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
AGAINST fb8fef72 -> HEAD e5090ac8: cells=156352 regressions=0 count_regressions=0 fixed=28684 repaired_overcount=67 changed=29394
EXTERNAL fb8fef72: cells=29941 wrong=5958 cost_kw=231 cost_attr=122 defects=5605
EXTERNAL HEAD e5090ac8: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
AGAINST 1c243203 -> HEAD e5090ac8: cells=156352 regressions=0 count_regressions=0 fixed=41090 repaired_overcount=1856 changed=39049
EXTERNAL 1c243203: cells=29941 wrong=7944 cost_kw=231 cost_attr=122 defects=7591
EXTERNAL HEAD e5090ac8: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
AGAINST 2f8c1656 -> HEAD e5090ac8: cells=156352 regressions=0 count_regressions=0 fixed=63980 repaired_overcount=1616 changed=58098
EXTERNAL 2f8c1656: cells=29941 wrong=14932 cost_kw=162 cost_attr=122 defects=14648
EXTERNAL HEAD e5090ac8: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
```

Коды выхода и время:
- `--against-batch 16-46` (база партии `d31d86db` = родитель первого `test(16-46)`) — rc=0, 18:18–18:26. Повтор с нейтральной меткой `REPAIRED` (отступление 4) — rc=0, 19:03, строки те же.
- `--against fb8fef72` — rc=0, 18:26–18:34.
- `--against 1c243203` — **rc=0**, 18:34–18:40. Заметка оркестратора 1 (а) закрыта, раздел ниже.
- `--against 2f8c1656` — rc=0, 18:40–18:46.

`SELFTEST` выросли против строк 16-48 (48 / 56 / 885 → 81 / 109 / 1 682) потому, что выросли семейства самопроверки: матрица и две подачи несут строки девятого круга. Известные регрессии краснят и новые строки. `SELFTEST-CR04` прежний — 1 510: правило пункта 9 не проглотило ни одной ячейки.

### Режим `--dictionary` (числа летописи девятого круга)

`bash .pytest_cache/r9diff/run.sh --dictionary --at 1163ae39,HEAD`, rc=0, 18:46:19–18:46:34 UTC:

```
DICT 1163ae39 1163ae39: writer=210/1743 privacy=153/1743
DICT HEAD e5090ac8: writer=0/1743 privacy=0/1743
```

Разбивка (stderr):
- `1163ae39`, писатель по способу: `carrier-name-bound-to-a-rival` 105, `executor-name-bound-to-a-rival` 105. Все 210 — на носителях с соперником.
- `1163ae39`, приватность: на носителях с соперником 40 + 40, прочие способы 73 (формы коллизии и объекта модуля). По осям: коллизия 30, объект модуля 75, носитель 48.
- HEAD — пусто.

1 743 ячейки на гейт — ячейки строк девятого круга из 3 381. Совпадает с замером планирования (153 / 210).

### Регрессировавшие и `REPAIRED` ячейки всей партии

**Регрессий наличия и счёта в строках `DIFF` / `BASE` партии нет ни у одного плана:**
- 16-46 — `DIFF 2a1ac33d -> cbcf07e1`, `d5223cb7 -> 472e30f6`;
- 16-47 — `771ed639 -> 16573223`, `850c4a6f -> 7c077803`;
- 16-48 — `3b0d912f -> 36248d38`, `4a192880 -> 533eb042`, `709e25d2 -> 6d932a97`;
- 16-49 — три строки выше.

Закрывать нечего.

**`REPAIRED` в `DIFF` / `BASE`:**
- 16-46 — 0;
- 16-47 — 1 991, класс WR-29 (снята ложная находка на методе чужого объекта), закрыл `16573223`; перечень `.pytest_cache/r9diff/repaired_1647.tsv`, sha256 `db7aeeede253d543589b05c79ceeb2a1d4a5f2eec929cfb022d42cbd473545d5`;
- 16-48 — 0;
- 16-49 — 0.

**`REPAIRED` против баз** (`repaired_classes.py`; метка — правило, класс — по семейству):

| Против | Всего | Гейты | Сдвиги | Классы |
|--------|-------|-------|--------|--------|
| `d31d86db` (база партии) | 1 991 | приватность | 1→0 1 391, 2→1 600 | WR-29 — ровно набор 16-47: (к8) 1 200, `x-r8-FP` 300, (к3) 240, `x-v9-fp` 120, `f-self-1647` 119, по 4 — `a-positive`, `x-v9-x`, `x-r8-X` |
| `fb8fef72` | 67 | писатель | 2→1 | класс 16-42 (одна запись, судимая дважды): `e-self-1642` 60, `c-review` 3, `a-literal` 2, `x-v9-a` 2 — как у 16-48 |
| `1c243203` | 1 856 | приватность 1 791, писатель 65 | 2→1 1 587, 4→2 169, 4→1 97, 3→1 2, 6→2 1 | WR-24 (одно место дважды; починка `51d0d766`) и класс 16-42 по точному ожиданию — 1 855; **сжатие повторов текста — 1: `x-r8h::T11c 4 -> 2 rule=повтор-текста`** |
| `2f8c1656` | 1 616 | писатель 892, приватность 724 | 2→1 1 603, 3→1 11, 1→0 2 | WR-24 и класс 16-42; 1→0 — законная строка `raw-sql-where-between-two-double-quoted-spans-is-a-filter` и `a-legitimate` (как у 16-48) |

### T11c — правило пункта 9 для ячеек без точного ожидания (заметка оркестратора 1 (а))

- **Было.** `run.sh --against 1c243203` у 16-48 выходил с rc=1: `count_regressions=1` на `x-r8h::T11c 4 -> 2`. Ожидание ревьюера — `expect: null`. Источник: `w = functools.partial(asyncio.to_thread, logger.info, "x", kwargs={"phone": a.phone}); w()`. На `1c243203` у ячейки четыре находки — две пары повторов текста; на HEAD каждый текст один раз. Вердикт хранил число и отпечаток, а не тексты.
- **Сделано (инструмент, gitignored).**
  - Вердикт формата v2: к прежним полям добавлены число разных текстов находок и отпечаток их множества. Имя кеша вердиктов несёт `-v2`, весь кеш пересужен под замком.
  - Правило `dup_collapse` в `judge.py`: у ячейки без точного ожидания падение числа — `REPAIRED` (`rule=повтор-текста`), если выполнены все четыре условия:
    1. множество текстов у ревизии то же, что у родителя;
    2. у ревизии каждый текст встречается один раз;
    3. число находок меньше, чем у родителя;
    4. число находок не ниже «пола мест» — числа узлов `phone*` в исходнике ячейки.

    Условие 4 нужно против класса WR-27: два РАЗНЫХ узла с одним текстом (место без столбца) так не сжимаются.
- **Против вакуума** — `dup_control.sh`: мини-корпус с `expect: null` на настоящих деревьях и построенные пары вердиктов.

  ```
  DUPCTL T11c: before=4 distinct=2 after=2 distinct=2 -> REPAIRED dupctl::T11c 4 -> 2 WR-24/повтор-текста
  DUPCTL WR27-merge: before=2 distinct=1 after=1 distinct=1 -> COUNT_REGRESSED dupctl::WR27-merge 2 -> 1
  DUPCTL CR04-lost: before=1 distinct=1 after=0 distinct=0 -> COUNT_REGRESSED dupctl::CR04-lost 1 -> 0
  DUPCTL synthetic «повтор → один раз (те же тексты)»: count_regressed=False (ожидалось False)
  DUPCTL synthetic «разные тексты: 2 → 1»: count_regressed=True (ожидалось True)
  DUPCTL synthetic «повтор, но у ревизии тоже повтор»: count_regressed=True (ожидалось True)
  DUPCTL synthetic «ниже пола мест (два узла, один текст)»: count_regressed=True (ожидалось True)
  DUPCTL synthetic «ячейка с exact — правило не применяется»: dup_collapse=False (ожидалось False)
  DUPCTL OK
  ```

  Контроль на настоящих деревьях:
  - `WR27-merge` — `logger.info("%s %s", a.phone, b.phone)` на `a6c87597 → 51d0d766`: два узла с одним текстом слиты в один. Правило оставляет это регрессией счёта.
  - `CR04-lost` — `e1d6587e → a77263ad`: настоящая потеря находки, число разных текстов упало. Регрессия счёта.

  Метка класса в строках `DUPCTL` осталась от прогона до переименования меток (отступление 4).
- **Итог.** `--against 1c243203` → rc=0, `count_regressions=0`. Правило сработало ровно на одной ячейке из 4 × 156 352 сравнений — на T11c. `SELFTEST-COUNT` и `SELFTEST-CR04` не уменьшились от правила. Чужое ожидание не правилось, id не выделялся, ось счёта глобально не ослаблялась.

### Учёт каждой изменённой ячейки (заметка оркестратора 1 (б))

`changed_by.py` раскладывает каждую ячейку `changed` (различие числа, отпечатка или числа двойника) по классу и направлению; `texts_dump.py` сверяет тексты у класса «то же число, другие тексты».

**Строки плана 16-48** — его корпус `f22ae991…` (копия оркестратора в основном дереве, только чтение) и его вердикты v1:
- `DIFF 3b0d912f -> 36248d38`, `changed=6396`: `fixed` 1 888 + `ok→ok:texts` 4 508;
- `DIFF 4a192880 -> 533eb042`, `changed=2319`: всё `fixed`;
- `BASE 5c7377cc -> 6d932a97`, `changed=8715`: `fixed` 4 207 + `ok→ok:texts` 4 508.

Роста и падения числа у верных ячеек нет, `wrong→wrong` нет. Все 4 508 `ok→ok:texts` различаются **только строкой места**: число и предмет те же. Это перенос места WR-31 со строки связывания на строку применения, например `app/x.py:1 — … MessengerAccount.phone.__set__(…)` → `app/x.py:2 — …`. Самые крупные семейства: `x-v9` 1 985, (к5) 1 027, (к6) 316, (к9) 300, `f-self-1644` 262, `b-matrix` 252.

**Вся партия на итоговом корпусе** — `AGAINST d31d86db -> HEAD`, `changed=15741`:
- `fixed` 10 638;
- `ok→ok:texts` 5 102 — все 5 102 только строка места, тот же перенос WR-31, включая (к11) 157, (к12) 140, `a-cost` 3;
- `ok→ok:up` 1 — `f-self-check::A/writer/collision-class-body/methodcaller-receiver/executor-name-bound-to-a-rival/partial-setattr/other-body/0`, 1 → 2. Это переход в названную цену `COST-KW`: пара `partial(setattr, other)` и `methodcaller("__set__", …)` под одним именем стала судиться на каждом толковании вызова (16-48). Находки на HEAD — механика цены (проверено `sc_cost_check.py`).

Ещё 454 ячейки `fixed` без изменения числа и текстов: верность вернулась по флагу вызова журнала (`zero_call` / `positive`), находок ноль на обеих сторонах. Это WR-29 — метод чужого объекта перестал быть вызовом журнала.

**Против старых баз** — рост и падение у ячеек, верных на обеих сторонах (`ups_by.py`):

| Против | Рост / падение | Классы |
|--------|----------------|--------|
| `fb8fef72` | 182 / 0 | переход 1 → 2 в названную цену (`ok→cost`): `x-v9-kw` 50 (`COST-KW`), (к5) 30 (kw), (к9) 16, `f-self-check` 5, `f-self-1648` 1 (`kw_ext`); `x-v9-k …:two` 80 — `range [1, ∞)`, 1 → 2: два узла номера с одним текстом, починка WR-27 (16-41), правда — 2 |
| `1c243203` | 113 / 1 | `ok→cost` 103 (`x-v9-kw` 50, (к5) 32, (к9) 16, `f-self-check` 4, `f-self-1648` 1); `e-wrapper-read-1636` 9 — `range [1, 2]`, 1 → 2: обёртка, прочитанная и вне вызова, и подачей, судится на двух местах (названная цена шапки, 16-36); `e-axis-b` 1 — `parent`, 0 → 1: `MessengerAccount(phone=x)`, поданная носителю в обёртке, — пропуск наличия старого дерева, закрытый до партии (модель среди аргументов носителя — судимое имя); падение — T11c 4 → 2 (`REPAIRED`, выше) |
| `2f8c1656` | 119 / 0 | `ok→cost` 89 (`x-v9-kw` 35, (к5) 24, (к9) 16, `f-self-check` 9, `f-self-1648` 5); `e-wrapper-read-1636` 17 и `e-final-1639` 11 — та же цена обёртки (два места); `e-axis-b` 2 — тот же пропуск наличия |

Ни один класс не регрессия ни по одной оси, циклов не понадобилось. Против базы партии рост один — переход в названную цену.

### Названные цены

- **`COST-KW` (свойство 8 О-20).** Перечень `.pytest_cache/r9diff/cost_kw_ids.txt`: **281** строка, sha256 `61dfde10d51caa73ec06a22643fe5e574e7e48c8ff39fed4505380ec90f784e9`. Это 280 `x-v9::kw::*:partial-setattr:*:receiver` и `x-v9h::x::KW-partial-setattr-dual`. Улика — `EVIDENCE kw`.
- **`COST-ATTR` (О-22 (а)).** Перечень `.pytest_cache/r9diff/cost_attr_ids.txt`: **122** строки, sha256 `deaa985492817b71e9c917fa4b79205c3e41de1c9da97d117fcdba0cb000b3da`. Улика — `EVIDENCE attr`.
- **`kw_ext` (решение владельца 2026-10-21, «Принять как цену»).** Группа своих семейств, никогда не дефект, не регрессия и не `REPAIRED`.
  - Перечень ячеек со статусом цены на HEAD — `.pytest_cache/r9diff/kw_ext_ids.txt`: **78**, sha256 `03406b50ba8ab98eab6d75d2c240ccb973f4232ec98e37df26841a558add487d`. По семействам: (к6) 28, (к9) 27, `f-self-1648` 14, `f-self-check` 6, `a-cost` 3.
  - Размечено ценой 687 ячеек; остальные дают одну находку, это допустимый ответ.
  - Улика — `EVIDENCE kw_ext` ×3.
  - В корпусе: `COST-OWN kw=225 attr=480 kw_ext=78`.

## Гейты на итоговом дереве (под общим `flock`)

| Проверка | Итог | План / база |
|----------|------|-------------|
| задача 1, №1 / задача 2, №1: три модуля гейтов | 956 passed (после задач 1 и 2) | план 954 |
| задача 1, №2: формы девятого круга | `OK 21 1008` | 1 008 |
| задача 2, №2: полный словарь | `OK 3381` | ≥ 3 381 |
| задача 3, №1: quick run фазы | **1 364 passed** | план ≥ 1 359, поправка оркестратора ≥ 1 361 (база 1 335 + 29) |
| задача 3, №2: места шапок | `OK` | — |
| задача 3, №3: сквозные гейты + `test_logging_config` | 576 passed + 3 passed (двумя командами) | 576 + 3 |
| задача 3, №4: `cost_evidence.py` | `EVIDENCE kw: writes=1 …`, 3 × `EVIDENCE kw_ext`, 10 × `EVIDENCE attr: file='+79991234567' log=''`, выход 0 | — |
| задача 3, №5: `run.sh 16-49 && --against-batch 16-46 && --against fb8fef72 && --against 1c243203 && --against 2f8c1656` | все rc=0, строки выше | — |
| задача 3, №6: `--dictionary --at 1163ae39,HEAD` | строки `DICT` выше; совпадают с летописью | — |
| оба гейта и паритет поимённо | **960 passed** (писатель 622, приватность 306, паритет 32) | план ≥ 955; база 931 |
| гейт писателя отдельно | 622 passed | база 611 (+8 матрица, +3 `NAMED_COST_CASES`) |
| живое дерево писателя (команда приёмки) | `OK`: в писателе 6 сырых, находок 0, файлов 104, реестр — ровно `app/application/accounts/phone.py`; `PHONE_LOG_EXCEPTIONS = {}`, потолок 0 | `OK 6 104` |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| строки `1163ae39` | `OK 259 105` и `OK 156 53` (14 строк `NEGATIVE_CONTROL_PLACES`) | — |
| `tests/test_application` | 907 passed | база 896 (+11) |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, «реестр: 894 строк, биекция с переписью — согласие» | 894 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | гонится после коммита этой сводки (заметка оркестратора 5) | 218 / 2 skipped |

Полная суита (`just test`, ≈46 мин) не гонялась: её гонит пост-мердж гейт оркестратора. `graphify update .` не запускался — его делает оркестратор после слияния. `graphify query` гонялся с `--graph /source/broadcaster/graphify-out/graph.json`.

## Decisions Made

- **Соперник — поле значения.** Это сделано, как у `decoy`: матрицы, паритет и генераторы инструмента зовут `binding_form_source(form, value, carrier)` без новых параметров. У приватности соперник `print` — класс CR-04. У писателя `update`: с ним пары `kw_ext` в матрице нет, ячейка даёт ровно одну находку.
- **Метод значения-получателя — тоже поле.** Пара `receiver` писателя — `account.__setattr__("phone", x)`: колонка названа в применении, поэтому ячейка от связывания не зависит. Это написано в комментарии над значением.
- **`kw_ext` закреплена отдельной таблицей с числом цены.** Отдельная таблица `NAMED_COST_CASES` с `NAMED_COST_FINDINGS = 2`, а не `LITERAL_FORM_PLACES`: число мест там — узлы колонки, а узел у этих строк один. В корпусе строки судятся ожиданием «одно место» с ценой 2.
- **Тексты летописей правятся только в GREEN задачи 3.** Числа `--dictionary` сняты до GREEN — после GREEN задачи 2 (17:02 UTC), когда словарь был полон. Итоговый прогон дал те же числа.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — инструмент] Заместители (г)/(д) `corpus.py` падали на выросшем словаре.**
- Найдено: первый `--precommit` задачи 1. `assert len(grammar.BINDING_FORMS) == 12` дал 20. Этот случай план называет во «Flagged assumptions».
- Исправлено: из заместителей (г)/(д) исключены восемь форм девятого круга, значение `receiver` и два носителя. Выборка (д) seed 42 прежняя; новые строки держат (б), (ж), (з), (к11), (к12), (е).
- Значение из корпуса не исключено.

**2. [Rule 3 — инструмент] `kfam.carrier_call_names` падал `KeyError` на шаблоне с `{rival}`.** Шаблон получает заместителя `RIVAL`, а его имя вызовом не считается. Ячейки семейств (к) со значениями без соперника на формах и носителях с `{rival}` не собираются: `render` даёт `None`. Эти оси держат (б), (ж), (з) и (к11)/(к12).

**3. [Rule 2 — заметка оркестратора 8] Корпус вырос до доверия первому GREEN.**
- Добавлены семейства (к11) / (к12) «одно имя — две роли» через общую грамматику у ОБОИХ гейтов. Состав — в таблице корпуса.
- Адресаты `k11`, `k12`, `a-cost` и самопроверки 16-49 — в `ADDRESSEES` `judge.py`.
- Потолок (к7) поднят до 5 000: семейство вырастало до 4 200, а 16-48 держало его целиком.
- (к6) выросло до 4 672 и в корпусе берётся выборкой 4 000. Целиком оно судилось отдельно: 0 неверных на HEAD.

**4. [Rule 2 — заметка оркестратора 1 (а)] Правило пункта 9 для `expect: null` (T11c).**
- Сделаны вердикт v2, `dup_collapse` и `dup_control.sh`; подробности — в разделе выше. Кеш вердиктов пересужен целиком.
- Метка `REPAIRED` сначала называла класс (`WR-24/exact`). У ячеек WR-29 это было неверно, поэтому метка заменена на правило (`rule=exact` / `rule=повтор-текста`). Класс назначается по семейству в этой сводке.
- `--against-batch` повторён с новой меткой, строки те же. Строки `DUPCTL` сняты до замены метки.

**5. [Решение владельца] Строки `NAMED_COST_CASES` и правило `test_a_named_cost_form_gives_its_named_count`.**
- По пункту 3 решения владельца — по одной строке на соперника, ровно две находки на одной строке: соперник и `__set__`.
- Добавлено +3 правила гейта писателя; в плане их не было.
- В корпус строки входят семейством `a-cost`.

**6. [Rule 1 — инструмент] Разметка цены kw в генераторе самопроверки.**
- Первый суд дал 30 неверных ячеек на HEAD. Ручная проверка показала пару kw: две находки на одной строке, `setattr(…)` и `__set__(…)`.
- Генератор размечал kw только у мест соперника, кроме «имени носителя», а форма коллизии связывает соперника под `f` сама.
- Разметка исправлена, самопроверка пересужена: 0 неверных.
- Ещё сбой моего скрипта: первый суд базы упал на относительном пути дерева. Повторён с абсолютным.

**7. [План против замера] Числа.**

| Проверка | План | Замер |
|----------|------|-------|
| три модуля | 955 | 960 |
| писатель | 617 | 622 (база 611 вместо 609, +3 строки цены) |
| quick run | ≥ 1 359 | 1 364 |
| `tests/test_application` | — | 907 |

- `SELFTEST` выросли вместе с семействами самопроверки: 81 / 109 / 1 682 против 48 / 56 / 885. `SELFTEST-CR04` — прежний 1 510.
- Самопроверка — 66 116 форм: композиция по кругу 6 пар из 30, полный крест — 101 430 на гейт в части A.

**8. [Процесс TDD] Тексты GREEN задачи 3 написаны до коммита её RED.**
- Чтобы RED и GREEN остались раздельными коммитами, GREEN-копии файлов сохранены в `.pytest_cache/green-t3/`.
- Тексты шапок и докстринга паритета возвращены к виду RED. Дифф RED-коммита — только правила, места и таблица закрепки.
- RED перепроверен (`3 failed, 3 passed`) и закоммичен (`e8fdf4c6`), затем GREEN-копии возвращены (`e5090ac8` — только тексты).
- RED-улика снималась на дереве RED (17:05–17:07); запись `16-49-t3h.json` пересобрана из того же XML.

### Замены команд (песочница worktree)

- Проверки `python -c` записаны дословно в `.pytest_cache/checks/*.py` и гнались с `PYTHONPATH=.`: `t1_forms.py`, `t2_cells.py`, `t3_docs.py`, `writer_live.py`, `rows_1163.py`.
- Составная начальная проверка HEAD и `git` в составных командах отклонены. Проверка ветки и базы — отдельными командами, протокол коммита — скриптом `.pytest_cache/checks/guard.sh` (шаги 0a, 0, 0c).
- `run.sh` гнался обёрткой `.pytest_cache/checks/run_rc.sh`: код выхода и время пишутся рядом. Закрывающие прогоны шли подряд через `run_close.sh`, гейты — через `gates.sh`.
- Вставки через heredoc не использовались: удаление строк для вида RED — скриптом `cut_lines.py`.
- Ожидание длинных прогонов — `flock -w 590 <lock> true`.
- Задача 3, `<automated>` №3 (сквозные гейты и `test_logging_config` одной командой) — двумя командами: 576 + 3.
- RED-улика собиралась `red_record.py` из JUnit XML.

---

**Total deviations:** 8. Правка инструмента по правилам 1 и 3 — четыре (1, 2, 6 и часть 4). Рост корпуса и правило T11c по заметкам оркестратора — два (3, 4). Одна закрепка по решению владельца (5). Одно расхождение плана с замером (7). Одна процессная оговорка TDD (8).
**Impact on plan:** предикаты гейтов не правились — их ответ прежний на всех строках и живых деревьях. Сверх плана — три строки-закрепки `kw_ext` по решению владельца и правило пункта 9 в инструменте.

## Issues Encountered

- **Копия корпуса во время прогона.** Первая копия `corpus.json` для учёта изменённых ячеек снята в момент, когда прогон «против» его пересобирал, — JSON был обрезан. Копия перенесена под замок и сверяется по sha256. Тот же класс записан в сводке 16-48.
- **Правка `run.sh` во время прогона.** Строку `cost_ids.py` в `run.sh` я правил, пока шёл `--precommit` задачи 3. Правка стояла ниже точки исполнения, и прогон её прочёл; дальше скрипт во время прогонов не правился.

## Known Stubs

Нет.

## Threat Flags

Нет: правки — тестовые гейты и общий словарь; новых сетевых точек, путей и схем нет. T-16-112 и T-16-113 закрыты, как в плане.

## Next Phase Readiness

- **16-50** записывает диспозиции пяти находок, решение владельца о `kw_ext` и пересевает реестр запретов.
- **Инструмент для ревьюера и верификатора раунда 10** оставлен на месте:
  - `.pytest_cache/r9diff/` — с `trees/`, кешем вердиктов v2, `corpus.json` (`204f02d8…`), `selfcheck_cells.json` (16-49), `selfcheck_cells_1648.json`;
  - `.pytest_cache/r9diff-src/`;
  - `.pytest_cache/r9-inputs/` — не правился.
- **По О-21 (а), свойство 6**, их корпуса — свои, независимые: этот корпус стал входом исполнителей.
- **(к11)/(к12)** не нашли дерева, где роль другого гейта под общим именем закрывает путь. Если ревьюер построит такую форму, это новая ось, а не возврат.
- **Учёт.** Отметки PHONE-02 / PHONE-21 и `STATE.md` / `ROADMAP.md` не трогались (заметка оркестратора 5). `deferred-items.md` не заводился.

## Self-Check: PASSED

- Коммиты `6b4c0d52`, `f7948e5b`, `ca8f5c0d`, `8138ba46`, `e8fdf4c6`, `e5090ac8` — предки HEAD (`git rev-list --count c51755fc..e5090ac8` = 6).
- Файлы на месте:
  - отслеживаемые — `tests/phone_gate_grammar.py`, оба модуля гейтов, `tests/test_phone_gates_parity.py`, эта сводка;
  - инструмент — `run.sh`, `judge.py`, `dict.py`, `dup_control.py`, `dup_control.sh`, `selfcheck_1649.py`, `changed_by.py`, `kfam_full.py`, `cost_kw_ids.txt`, `cost_attr_ids.txt`, `kw_ext_ids.txt`.
- Удалений в коммитах нет: 4 файла, +619 / −34.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-21*

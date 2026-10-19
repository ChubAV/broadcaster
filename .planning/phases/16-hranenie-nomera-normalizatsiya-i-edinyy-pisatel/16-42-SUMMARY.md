---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 42
subsystem: testing
tags: [phone-single-writer-gate, wr-28, reading-name, methodcaller, getattr, r8diff, ast, pytest, tdd]
status: complete

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-41 — инструмент r8diff (ось счёта, SELFTEST-COUNT, HEAD_WRONG), место находки приватности — узел; 16-36…16-39 — `named_wrappers`, `wrapper_applications`, словарь седьмого круга"
provides:
  - "Общий модуль: `reading_name(node) -> str | None` — один читатель имени связанного (имя, `Attribute.attr`, строка `getattr_literal`); `named_wrappers` читает имя через неё"
  - "Гейт писателя ввозит `reading_name` по имени; своих читателей имени нет (`_reference_name` и `_getattr_string` сняты); 13 мест чтения имени переведены на `reading_name`"
  - "Трасер подложенного `scripts/backfill_descriptor.py`; 13 строк `LITERAL_FORM_CASES` и 7 строк `LEGITIMATE_CASES` оси «где прочитано имя»"
  - "Шапка гейта писателя: `methodcaller` на каждом чтении имени одним читателем `reading_name`; перечень пойманного границы; летопись WR-28 (восьмой круг)"
  - "Инструмент `.pytest_cache/r8diff/` для 16-43: seed 42, семейство (д) `e-self-1641`, (в) — 33 формы 16-42, (е) — самопроверка 16-42 (22 512 форм, в корпусе 20 000)"
affects: [16-43, 16-44, 16-45]

actuals:
  tokens: 17277   # chars/4: диф двух файлов (48 603 симв.) + selfcheck_1642.py (12 260) + правка corpus.py (8 243), gitignored-инструмент включён
  tasks: 2
  commits: 10     # git rev-list --count d1743b4a..96c3eb65 (до коммита сводки)
plan_head_before: d1743b4a15a06c3740fdef0f97cb887d15913bfc
plan_head_after: 96c3eb65631482faf106ed3dd887630adb79a2c8

tech-stack:
  added: []
  patterns:
    - "Один читатель имени связанного в месте чтения — `reading_name` общего модуля; цель связывания читает `binding_name`"
    - "Место чтения имени — вызываемое, ссылка, звено цепочки, получатель, переименование псевдонима, множество использованных имён: каждое через `reading_name`"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "`_reference_name` и `_getattr_string` сняты, а не оставлены делегатами: у гейта писателя не осталось ни одного своего читателя имени"
  - "Ось «где прочитано имя» закрыта по оси целиком, а не только по двум формам WR-28: два зонда исполнителя нашли ещё 12 давних форм на той же оси (псевдонимы носителей и API, цепочки, поглощение `partial`, получатель `__init__`, цепочка дескриптора) — три дополнительных цикла RED/GREEN"
  - "REPAIRED 463 на `340d5939` — класс «одна запись, судимая дважды»: `partial` с колонкой, прочитанный getattr-строкой, давал находку и на связывании, и на применении; 2 → 1 у ячеек с `exact` 1 — задуманная починка, не регрессия счёта"

patterns-established:
  - "Самопроверка оси «где прочитано имя»: значение × форма связывания (12 + `getattr-read`) × чтение имени (5) × способ (21), законные двойники «чужая колонка» и «не-пишущее значение»"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Две формы WR-28 стороны писателя и девять вариантов чтения имени, связанного с `methodcaller`, — ровно одна находка `__set__` с `phone`; законные — ноль; подложенный скрипт находится обходом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_methodcaller_read_by_a_getattr_string_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (259 строк)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write (105 строк)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK 11"
        status: pass
    human_judgment: false
  - id: D2
    description: "Один читатель имени `reading_name` в общем модуле; гейт писателя ввозит его по имени и своих читателей не держит; живое дерево — 0 находок в 104 файлах, в писателе 6 сырых"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py (`w.reading_name is m.reading_name`)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/writer_live.py → OK 6 104"
        status: pass
    human_judgment: false
  - id: D3
    description: "Шапка гейта писателя называет `reading_name` у `methodcaller`, перечень пойманного границы и летопись WR-28"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_header.py → OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Сверка «база ↔ HEAD» по обеим осям: SELFTEST 47 / 56, SELFTEST-COUNT 1 237, пять DIFF и BASE — ноль регрессий обеих осей, OPEN_REGRESSIONS=0; самопроверка 7 504 формы под заявлением — 0 промахов"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "bash .pytest_cache/r8diff/run.sh 16-42 (HEAD 96c3eb65, выход 0)"
        status: pass
      - kind: other
        ref: ".pytest_cache/r8diff/selfcheck_1642.py (HEAD 340d5939 = код 96c3eb65) → misses=0"
        status: pass
    human_judgment: false

duration: 73min
completed: 2026-10-19
---

# Фаза 16, план 42: один читатель имени `reading_name` для гейта писателя (WR-28) — сводка

**Имя, связанное с `operator.methodcaller`, гейт писателя теперь читает везде, где читается имя связанного, в том числе getattr-строкой. Читает его одна функция общего модуля `reading_name`. Своих читателей имени у гейта больше нет: на неё переведены 13 мест чтения, включая те, что нашли два зонда исполнителя. Формы WR-28 и ещё 12 давних форм той же оси дают ровно одну находку. Сверка «база ↔ HEAD» по обеим осям не нашла регрессий.**

## Performance

- **Duration:** 73 min
- **Started:** 2026-10-19T21:37:01Z
- **Completed:** 2026-10-19T22:50:13Z
- **Tasks:** 2 (оба `tdd`). Сверх них — 3 цикла зонда и самопроверки: псевдонимы, места второго зонда, летопись
- **Files modified:** 2 (`tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`)

## Accomplishments

- В общем модуле появилась функция `reading_name(node)`. Она возвращает `Name.id`, `Attribute.attr` или строку `getattr(<obj>, "<имя>")` (два или три позиционных аргумента, по `getattr_literal`); у прочих узлов и у `None` — `None`. `named_wrappers` читает имя через неё, ответ прежний.
- Гейт писателя ввозит `reading_name` по имени. `methodcallers_of` и `is_reference` читают имя через неё. `_reference_name` и `_getattr_string` сняты.
- Трасер подложил `scripts/backfill_descriptor.py`. Гейт находит в нём одну находку `KIND_SETATTR` на строке 8 (`self.apply = …`), предмет называет `__set__` и `phone`.
- Формы WR-28-W-1 и WR-28-W-2 — строки `LITERAL_FORM_CASES`. Девять вариантов чтения из замера планирования и контроль атрибутом дают по одной находке. Законные двойники дают ноль.
- Зонд исполнителя нашёл на той же оси 12 давних форм, которые гейт пропускал (две из них давали лишнюю находку). Все они закрыты своими циклами:
  - псевдоним `operator.methodcaller`, прочитанный getattr-строкой;
  - цепочки псевдонимов `methodcaller` и `setattr` через атрибут и через getattr-строку;
  - `partial` с колонкой, прочитанный getattr-строкой: было две находки, стала одна;
  - псевдоним модели получателем `__init__`;
  - цепочка псевдонима дескриптора колонки.
- В шапке значение `methodcaller` читается одним читателем `reading_name`. Перечень пойманного «ГРАНИЦЫ ПРЕДИКАТА» называет его. Пункты границы `methodcaller` не называют. Добавлена летопись WR-28.

## Task Commits

1. **Задача 1, RED** — `e62799d3` `test(16-42): require a methodcaller name read by a getattr string to be judged (WR-28)`
2. **Задача 1, GREEN** — `e61ab80d` `feat(16-42): read a methodcaller-bound name with one shared reader, getattr string too (WR-28)`
3. **Цикл зонда 1, RED** — `56d13690` `test(16-42): require an alias read by a getattr string or a chain link to be judged (WR-28 axis)`
4. **Цикл зонда 1, GREEN** — `cc7fbce7` `feat(16-42): read an alias name through the shared reader in renames and chains (WR-28 axis)`
5. **Задача 2, RED** — `68c68d97` `test(16-42): require the writer header to name the one shared name reader and the WR-28 chronicle`
6. **Задача 2, GREEN** — `52729753` `feat(16-42): name the one shared name reader and the WR-28 chronicle in the writer header`
7. **Цикл зонда 2, RED** — `ec96cf2e` `test(16-42): require partial use, model-alias receiver and descriptor chain read by getattr string or attribute (WR-28 axis)`
8. **Цикл зонда 2, GREEN** — `340d5939` `feat(16-42): read partial use, model-alias receiver and descriptor chains through the shared reader (WR-28 axis)`
9. **Цикл летописи, RED** — `8cac1bac` `test(16-42): require the WR-28 chronicle to name every read place moved to the shared reader`
10. **Цикл летописи, GREEN** — `96c3eb65` `feat(16-42): name every read place moved to the shared reader in the WR-28 chronicle`

Коммит сводки — `docs(16-42)`, следующий за этими.

## TDD: RED / GREEN

Улики лежат в `.pytest_cache/gsd-red/` (gitignored): JUnit-отчёт, вывод консоли и запись JSON. `gsd-tools check tdd-red-evidence` вернул `RED_EVIDENCE_OK` / `target_test_failed` для каждого RED.

### Задача 1

**RED.** Команда: `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly -k "methodcaller_read_by_a_getattr_string or methodcaller-receiver-read or noop-methodcaller"`, выход 1. Все три признака на месте:
- `FAILED tests/test_application/test_phone_single_writer_gate.py::test_a_planted_backfill_with_a_methodcaller_read_by_a_getattr_string_reddens_the_gate`;
- последняя строка сводки — `3 failed, 2 passed, 576 deselected, 1 warning in 0.50s`;
- литерал правила строк — `литеральная форма записи `__set__(… phone …)` дала 0 находок вместо одной: []` (у двух строк WR-28). Литерал трасера — «имя, связанное с `operator.methodcaller` и прочитанное getattr-строкой, гейт не читает».

Смысловая оценка: цель исполнилась и упала на утверждении «гейт ничего не нашёл». Это не ошибка сбора. Закрепки, зелёные до GREEN: `methodcaller-receiver-read-by-a-getattr-string-other-column` и `noop-methodcaller-read-by-a-getattr-string`.

**GREEN.** Три модуля гейтов — `858 passed`. `t1_forms.py` → `OK 11`, `t1_rows.py` → `OK 246 98 248 100`, `writer_live.py` → `OK 6 104`.

### Цикл зонда 1 (псевдонимы)

**RED.** Выборка `-k "methodcaller-alias or setattr-alias-chained"`, выход 1:
- пять строк `FAILED …test_a_literal_write_form_is_a_write[…]`;
- `5 failed, 4 passed, 579 deselected`;
- литерал «дала 0 находок вместо одной: []».

Закрепки: две новые законные строки, а также прежние `rebound-methodcaller-alias` и `methodcaller-alias-other-method`.

**GREEN.** `865 passed`.

### Задача 2

**RED.** Выборка `-k test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier`, выход 1:
- `FAILED tests/test_application/test_phone_single_writer_gate.py::test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier`;
- `1 failed, 587 deselected, 1 warning in 0.61s`;
- литерал «шапка гейта писателя не называет общую грамматику связывания» (в дереве до плана — 1).

Красны пять мест: `reading_name`, WR-28, О-18 (а), летопись WR-28, читатель в перечне пойманного. Закрепка: «пункты границы не называют `methodcaller`».

**GREEN.** `865 passed`, `t2_header.py` → `OK`.

### Цикл зонда 2 (поглощение `partial`, получатель `__init__`, цепочка дескриптора)

**RED.** Выход 1:
- шесть строк `FAILED`;
- `6 failed, 3 passed, 588 deselected`;
- литералы «дала 2 находок вместо одной» (`partial` с колонкой, getattr-строка) и «дала 0 находок вместо одной: []».

Закрепки — три законные строки.

**GREEN.** `874 passed`.

### Цикл летописи

**RED.** `1 failed, 596 deselected`. Тот же литерал правила шапки; красны три места: «поглощени», «`__init__`», «`_api_alias_targets`».

**GREEN.** `874 passed`.

## Перепись мест чтения имени гейта писателя (задача 1; свойство 2 О-18 (а))

**Переведено на `reading_name`:**

| Место | Что читалось до плана | Коммит |
|-------|----------------------|--------|
| `named_wrappers` (общий модуль) | имя, атрибут, getattr-строка своими ветками | `e61ab80d` |
| `_methodcaller_receivers.methodcallers_of` | только `Name` / `Attribute` | `e61ab80d` |
| `_carrier_wrappers.is_reference` | только `Name` / `Attribute` | `e61ab80d` |
| `_bound_reference` (был `_reference_name`, снят) | имя, атрибут, getattr-строка — своя копия | `e61ab80d` |
| `_call_name` (был `_getattr_string`, снят) | имя, атрибут, getattr-строка — своя копия | `e61ab80d` |
| звено цепочки `_partial_aliases` | `Name` / `Attribute` + `_reference_name` | `e61ab80d` |
| звено цепочки `_methodcaller_aliases` | `Name` / `Attribute` + `_reference_name` | `e61ab80d` |
| чтения в `_absorbed_carrier_wrappers` | `binding_name` у `Load` + `getattr_literal` | `e61ab80d` |
| звено цепочки `_module_aliases` | имя; атрибут — только с исходным именем | `cc7fbce7` |
| `_rename_aliases` | `Name` / `Attribute`; getattr-строку не читал | `cc7fbce7` |
| `_api_aliases`, имена значений связывания | `Name.id` / `Attribute.attr`, ответ прежний | `cc7fbce7` |
| множество `used` (поглощение `partial` у использования) | `Name` / `Attribute`; getattr-строку не читал | `340d5939` |
| получатель `MODEL_INIT` и текст предмета | только `Name` | `340d5939` |
| `_api_alias_targets`: фильтр значений и звено цепочки | цепочка только через `Name` | `340d5939` |
| `link_targets` в `_absorbed_carrier_wrappers` | `Name` / `Attribute`, ответ прежний | `340d5939` |

**Не места чтения** (с причиной):
- `binding_name(binding.target)` во всех помощниках. Это цель связывания: её читает `binding_name`, а не `reading_name`.
- `_callee_receiver`. Возвращает узел-объект `X` у `X.attr(…)` и у `getattr(X, "attr")(…)`, а не имя.
- `_canonical_call`, сравнение `target.attr == original`. Сверяет имя пишущего API цели-атрибута с исходным API, а не читает имя связанного.
- `_phone_column` и `node.attr in PHONE_COLUMNS`. Это ось «как названа колонка»: колонка, а не связанное имя.
- `func.attr in COLUMN_LOOKUP_METHODS`. Это методы поиска колонки.
- `func.id in LITERAL_CONTAINER_WRAPPERS`, `func.id == "dict"`, `getattr_literal`. Опознание встроенных по литералу. Псевдонимы `getattr` переименовывает `_rename_aliases`.

Гейт приватности (`_methodcaller_calls`) — объём 16-43; этот план его не правил.

## Самопроверка исполнителя (задача 2; О-18 (а), свойство 2)

Скрипт — `.pytest_cache/r8diff/selfcheck_1642.py` (gitignored, в репозиторий не коммитится). Он однопроцессный и гонится под общим `flock`. Каждая форма подаётся в `phone_write_offences(…, "scripts/x.py")`. Дерево подаётся аргументом: экспорт `git archive` ревизии.

**Оси (полный крест):**
- **Значение (8):**
  - `methodcaller("__set__", account, x)` с `(MessengerAccount.phone)`;
  - `methodcaller("set_committed_value", account, "phone", x)` с `(attributes)`;
  - `setattr`;
  - `functools.partial(setattr, account)`;
  - `attributes.set_committed_value`;
  - с захода 2 — `functools.partial(setattr, account, "phone")`, `MessengerAccount.phone.__set__`, `MessengerAccount` с `.__init__(account, phone=x)` (только прямой вызов: носитель подал бы модель конструктором).
- **Форма связывания (13):** 12 `BINDING_FORMS` и кандидат `getattr-read`.
- **Чтение имени (5):**
  - как в форме;
  - getattr-строка (`self.f` → `getattr(self, "f")`, `cls.f` → `getattr(cls, "f")`, `f` → `getattr(sys.modules[__name__], "f")`);
  - getattr-строка с умолчанием `None`;
  - цепочка `g = getattr(<obj>, "f"); …g…`;
  - получатель-колонка `getattr(MessengerAccount, "phone")` — только у `methodcaller` с получателем.
- **Способ (21):** прямой вызов и 20 `REFERENCE_CARRIERS`.
- **Законные двойники каждой ячейки:** чужая колонка (`MessengerAccount.status`, `"status"`, `status=`, `Group`) и не-пишущее значение того же вида (`methodcaller("noop")`, `helper.noop`, `partial(helper.noop, …)`).

**Ожидание:** под заявлением — ровно одна находка ожидаемого вида, которая называет API значения и `phone`; законные — ноль.

| Заход | Дерево | Форм (под заявлением / законных) | Промахов | Итог |
|-------|--------|----------------------------------|----------|------|
| 0 (зонд) | рабочее дерево, код `e61ab80d` | 16 191 (5 397 / 10 794) | 504: `setattr` и `attributes.set_committed_value` × цепочка getattr-строкой, по 252 | класс цикла `56d13690` / `cc7fbce7` (выявлен и зондом формами) |
| 1 | `52729753` | 16 191 (5 397 / 10 794) | **0** | — |
| контроль | `e62799d3` (код базы) | 16 191 | 1 050 | генератор видит WR-28 там, где он был |
| 2 (8 значений) | `340d5939` (код `96c3eb65`) | **22 512 (7 504 / 15 008)** | **0** | ячейки ушли в корпус (е) |
| контроль | `d1743b4a` (база) | 22 512 | 1 869 | — |

Классы контроля на базе:
- `mc-receiver` × getattr и getattr с умолчанием — по 252;
- `mc-receiver` × `getattr-read` как в форме и получатель getattr-строкой — по 21;
- `partial-setattr-column` × getattr и getattr с умолчанием — по 252, × `getattr-read` — 21;
- цепочка getattr-строкой у `setattr`, `attributes.set_committed_value` и псевдонима дескриптора — по 252;
- псевдоним модели — 6 + 12 + 12 + 12.

**По осям (заход 2, под заявлением):**
- значения — по 1 029, у `mc-receiver` 1 281, у псевдонима модели 49;
- чтения — 1 924 как в форме, по 1 776 у getattr, getattr с умолчанием и цепочки, 252 у получателя getattr-строкой;
- формы — по 613, у `direct` 148;
- способы — от 355 до 404.

Не собрано 3 416 сочетаний: у формы `direct` нет имени, получатель getattr-строкой бывает только у `mc-receiver`, псевдоним модели — только прямым вызовом.

Каждая из 7 504 форм под заявлением на HEAD дала ровно одну находку (`claim:1 = 7504`). Кратных нет, у законных находок нет.

**Зонд мест чтения** (`.pytest_cache/checks/probe_alias.py`, `probe_sites.py`) прогонялся на HEAD каждого цикла. На `52729753` он нашёл семь форм; на базе `d1743b4a` те же семь давали тот же ответ — давние пропуски, не регрессии. Цикл `ec96cf2e` / `340d5939`.

Прогоны: 2026-10-19, ≈21:47–22:36 UTC.

## Сверка «база ↔ HEAD» с осью счёта (свойство 6 О-18 (а); пункт 5 договора `16-41-PLAN.md`)

**Инструмент.** Основа — копия r8diff 16-41 от оркестратора (`scratchpad/tools/r8diff-16-41/`, `cp -a` в `.pytest_cache/r8diff/`). Изменения:
- **`corpus.py`:**
  - `SEED = 42`;
  - семейство (д) `e-self-1641` — самопроверка 16-41, `selfcheck_cells_1641.json`, 36 876 форм, позиционная выборка;
  - в (в) — 33 формы 16-42: девять вариантов чтения, контроль атрибутом и получатель getattr-строкой; две законные; семь форм псевдонимов; тринадцать форм второго зонда;
  - (е) — `selfcheck_cells.json` самопроверки 16-42.
- **`judge.py` и `run.sh`** не менялись.

Договор (а)–(з) пересверен с текстом `<scope_note>` 16-41.

**Корпус итогового прогона:** HEAD `96c3eb65`, 60 447 ячеек, `corpus.json` sha256 `cf5093f3b07ab48e1472ac40b55ba962a7012efcb373347bfb363d0c80ad3145`.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 259, `LEGITIMATE_CASES` 105, `NEGATIVE_CONTROLS` 149, `POSITIVE_CONTROLS` 51 | 564 |
| (б) матрицы | `b-matrix` 2 520 + `b-candidate` 756 | 3 276 |
| (в) формы ревью | раунд 7 — 30, раунд 8 — 16, план 16-42 — 33 | 79 |
| (г) дифференциал | — | 700 |
| (д) выборка самопроверок | 13 семейств по 2 000 | 26 000 |
| (ж) две подачи на одной строке | — | 3 276 |
| (з) безопасные двойники | — | 6 552 |
| (е) самопроверка 16-42 | выборка 20 000 из 22 512 (seed 42) | 20 000 |

**Правило выборки (д):** равномерно, без повторов, `random.Random(42)`, ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием. Семейства 16-39 и 16-41 материализуются и выбираются по позиции.

Полный перебор семейств (д):
- ось B — 70 840;
- ось A — 48 264;
- SQL — 11 390;
- носитель журнала — 234 900;
- кратность — 191 160;
- способ подачи — 272 400;
- лексика SQL — 26 940;
- конструктор колонки — 154 224;
- обёртка писателя (16-36) — 5 765 760;
- обёртка приватности (16-37) — 4 193 280;
- итерируемая (16-38) — 22 680;
- итог 16-39 — 82 035;
- самопроверка 16-41 — 36 876.

**Не прогнано выборкой:** 11 084 749 форм (11 110 749 − 26 000). Ещё 2 512 форм самопроверки 16-42 не вошли в корпус; сама самопроверка прогнана целиком (заход 2).

**Строки итогового прогона** (`bash .pytest_cache/r8diff/run.sh 16-42`, HEAD `96c3eb65`, 2026-10-19 22:39:38–22:44:08 UTC, выход 0) — дословно, без перечней `REPAIRED`:

```
CORPUS_SHA256=cf5093f3b07ab48e1472ac40b55ba962a7012efcb373347bfb363d0c80ad3145 HEAD=96c3eb65631482faf106ed3dd887630adb79a2c8
SELFTEST 1bebbbf7 -> c6953017: cells=3355 regressions=47 count_regressions=47 fixed=208 repaired_overcount=0 changed=255
SELFTEST 5e32c335 -> 147f5e46: cells=3355 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3555 regressions=831 count_regressions=1237 fixed=26 repaired_overcount=2 changed=1317
DIFF e62799d3 -> e61ab80d: cells=60447 regressions=0 count_regressions=0 fixed=551 repaired_overcount=0 changed=551
DIFF 56d13690 -> cc7fbce7: cells=60447 regressions=0 count_regressions=0 fixed=472 repaired_overcount=0 changed=472
DIFF 68c68d97 -> 52729753: cells=60447 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF ec96cf2e -> 340d5939: cells=60447 regressions=0 count_regressions=0 fixed=722 repaired_overcount=463 changed=722
DIFF 8cac1bac -> 96c3eb65: cells=60447 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE d1743b4a -> HEAD 96c3eb65: cells=60447 regressions=0 count_regressions=0 fixed=1745 repaired_overcount=463 changed=1745
HEAD_WRONG=86
OPEN_REGRESSIONS=0
```

**Промежуточные прогоны** (каждый — выход 0, `OPEN_REGRESSIONS=0`, `SELFTEST` 47 / 56, `SELFTEST-COUNT … count_regressions=1237`):

1. После GREEN задачи 1. HEAD `e61ab80d`, корпус 40 418 ячеек без (е), sha `7292ec28b32ebb15ca247a1878ce6ac3c612ace1ac9441e58cef749d229f9d78`:
   - `DIFF e62799d3 -> e61ab80d: cells=40418 regressions=0 count_regressions=0 fixed=55`;
   - `BASE d1743b4a -> HEAD e61ab80d: … regressions=0 count_regressions=0 fixed=55`;
   - `HEAD_WRONG=91` (86 приватности и пять форм псевдонимов — до цикла зонда 1).
2. После цикла зонда 1. HEAD `cc7fbce7`, корпус 56 616 с (е) 16 191, sha `897c93b2e2d22770c153f46ee3d2b84cc32cc0da830e000e1b1ef24c529bcf2d`:
   - `DIFF 56d13690 -> cc7fbce7: … regressions=0 count_regressions=0 fixed=514`;
   - `BASE … fixed=1115`;
   - `HEAD_WRONG=86`.
3. После GREEN задачи 2. HEAD `52729753`, тот же корпус: `DIFF 68c68d97 -> 52729753: … changed=0`, `BASE … regressions=0 count_regressions=0`, `HEAD_WRONG=86`.
4. После цикла зонда 2. HEAD `340d5939`, корпус 60 447, sha `cf5093f3…`: строки как в итоговом прогоне без последнего `DIFF`.

**`REPAIRED` (463, только на `340d5939`).** Класс — «одна запись, судимая дважды», как WR-24. `partial` с колонкой в связывании, прочитанный getattr-строкой, судился и на месте связывания, и на месте применения: множество использованных имён getattr-строку не видело. Ячейки:
- 458 ячеек (е) `claim/partial-setattr-column/*/getattr*/*`;
- `c-review::16-42/partial-col-getattr`, `…-getattr-default`, `…-getattr-handed`;
- `a-literal::partial-with-column-read-by-a-getattr-string`, `…-handed-to-to-thread`.

Все 2 → 1 при `exact` 1. Закрыл их `340d5939`. Ячейки цены 16-36 (`range` [1, 2]) счёт не потеряли: `count_regressions=0` на всех `DIFF`.

**Регрессий нет** ни на одном GREEN, ни по наличию, ни по счёту. Циклов сверки не было; все дополнительные циклы — из зонда и самопроверки.

**`HEAD_WRONG=86`** — только сторона приватности WR-28, объём 16-43 (и 16-44 для словаря):
- `b-candidate` приватности `getattr-read × methodcaller` и `× methodcaller-receiver` — 42;
- (ж) D2 той же оси — 42;
- `c-review::WR-28-P-1`, `WR-28-P-2`.

Ячейки писателя из 130 ячеек 16-41 сняты все:
- `b-candidate` писателя `getattr-read × methodcaller-receiver` — 21;
- (ж) D2 — 21;
- `WR-28-W-1`, `WR-28-W-2`.

Неверных ячеек писателя на HEAD — 0.

## Гейты на итоговом дереве (`96c3eb65`, под общим `flock`)

| Проверка | Итог | До плана |
|----------|------|----------|
| `<automated>` задачи 1 №1 и задачи 2 №1: писатель + приватность + паритет | `874 passed` (писатель 597, приватность 260, паритет 17) | 853 |
| `<automated>` задачи 1 №2 (`t1_rows.py`) | `OK 246 98 259 105` | — |
| `<automated>` задачи 1 №3 (`t1_forms.py`) | `OK 11` | — |
| `<automated>` задачи 1 №4 (`writer_live.py`) | `OK 6 104` | то же |
| приёмка задачи 1 (`t1_ids.py`) | `OK 259 105` | — |
| `<automated>` задачи 2 №2 (`t2_header.py`) | `OK` | — |
| приёмка задачи 2, реестры (`t2_registry.py`) | `OK` | то же |
| quick run фазы (8 путей) | `1278 passed` | 1257 |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| `tests/test_application` | `882 passed` | 861 |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `test_templates`, `test_declared_invariants`) | `576 passed` | 576 |
| `tests/test_logging_config.py` | `3 passed` | 3 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, реестр 875 строк, биекция | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | `110 passed` | 110 |
| `run.sh 16-42` | выход 0 (строки выше) | — |

`tests/test_planning` гонится после коммита сводки; итог — в финальном сообщении исполнителя оркестратору.

## Files Created/Modified

- `tests/phone_gate_grammar.py` — `reading_name`; `named_wrappers` читает имя через неё.
- `tests/test_application/test_phone_single_writer_gate.py`:
  - ввоз `reading_name`;
  - 15 мест чтения на `reading_name`, `_reference_name` и `_getattr_string` сняты;
  - трасер;
  - 13 строк `LITERAL_FORM_CASES`, 7 строк `LEGITIMATE_CASES`;
  - шапка — общий абзац, перечень пойманного, летопись WR-28;
  - правило шапки — места WR-28.

Инструмент сверки (gitignored, не коммитится, оставлен в worktree для 16-43):
- `.pytest_cache/r8diff/` — `corpus.py` (seed 42, (д) `e-self-1641`, (в) 16-42), `judge.py`, `run.sh`, `fam1639.py`, `selfcheck_1641.py`, `selfcheck_cells_1641.json`, `selfcheck_1642.py`, `selfcheck_cells.json` (самопроверка 16-42, 22 512), `selfcheck_report_1642.json`, `trees/`, `judged/`, `run-1642-*.out|err`;
- `.pytest_cache/checks/*.py` — дословные `python -c` плана и зонды.

## Decisions Made

- `_reference_name` и `_getattr_string` сняты, а не оставлены делегатами. Запрет плана — «своего читателя имени у гейта нет». Снятие делает это проверяемым грепом: `def _reference_name`, `def _getattr_string` и любое `reading_name` в модуле гейта, кроме ввоза, — 0.
- Ось закрыта по оси. Зонд исполнителя прошёл по всем местам модуля, где по узлу чтения берётся имя связанного. Каждое найденное расхождение (12 форм) — свой цикл со строками таблицы. Заявление шапки не сужено.
- Сохранены прежние ответы, которые меняться не должны: `t1_rows.py` → прежние 246 и 98 строк на месте, живое дерево — 104 / 6. `getattr`-псевдоним, переименованный в `getattr`, даёт тот же ответ, что литеральная форма на базе. Пример: `getattr(account, "phone").__set__(account, x)` — 1 находка и на `d1743b4a`.

## Deviations from Plan

### Расхождения «план ↔ замер» (записаны, ничего не ослаблено)

**1. [Rule 2 — та же ось] Три цикла сверх двух задач.** Найдено зондом и самопроверкой: 12 давних форм оси «где прочитано имя». На базе `d1743b4a` они давали тот же ответ, что и до плана: регрессий нет, есть давние пропуски, и две формы давали две находки вместо одной. Циклы:
- `56d13690` / `cc7fbce7` — псевдонимы `operator.methodcaller` и `setattr`;
- `ec96cf2e` / `340d5939` — поглощение `partial`, получатель `__init__`, цепочка дескриптора;
- `8cac1bac` / `96c3eb65` — летопись называет новые места.

Каждый цикл сверен `run.sh`. Затронуты только файлы плана.

**2. Числа плана меньше замера.**
- Писатель: план — 581 правило, замер — 597. Сверх плана — 13 строк `LITERAL_FORM_CASES` вместо 2 и 7 `LEGITIMATE_CASES` вместо 2.
- Quick run: план — ≥ 1262, замер — 1278.
- Задача 2 №1: план — ≥ 858, замер — 874.
- `tests/test_application`: замер 882 (861 + 21).

Пороги «не меньше» выполнены. Строки не удалялись и не правились.

**3. Самопроверка расширена.** Заход 2 добавил три значения второго зонда: 7 504 формы под заявлением, больше 5 000 плана. В корпус (е) — выборка 20 000 из 22 512 (seed 42).

**4. Нумерация строк плана.** План называл строки на `8aabdb38`. Сверено на `d1743b4a`: код гейта писателя после 16-41 не менялся, номера совпали.

### Замены команд (песочница worktree, заметки оркестратора 3, 4)

- `python -c` из `<automated>` и приёмки записаны дословно в `.pytest_cache/checks/` (`t1_rows.py`, `t1_forms.py`, `t1_ids.py`, `writer_live.py`, `t2_header.py`, `t2_registry.py`). Запуск — с `PYTHONPATH=.`. `;` первой строки заменён переводом строки, логика та же.
- `git show 8aabdb38:… > .pytest_cache/r8_base_writer.py` — простой командой.
- Песочница отклонила heredoc и составную команду с `git` внутри `flock … ; echo`. Скрипты написаны инструментом Write, `run.sh` запускался без хвоста.
- Деревья самопроверки (`trees/sc-head`, `trees/sc-head2`) — `git archive … > tar` и `tar -x` отдельными шагами.
- `graphify query` гонялся по графу основного дерева (`--graph /source/broadcaster/graphify-out/graph.json`). `graphify update .` не запускался — за оркестратором после слияния.
- Полная суита (`just test`, ≈46 мин) не гонялась — её гонит пост-мердж гейт оркестратора.

---

**Total deviations:** 4 записанных расхождения (1 — дополнительные циклы той же оси по правилу 2, 3 — «план ↔ замер» без ослабления), плюс замены команд.
**Impact on plan:** заявление шапки не сужено, реестры прежние, гейт приватности и паритет — прежний ответ (260 / 17, живые деревья 225 / 68 / 93). Правились только два файла плана и gitignored-инструмент.

## Issues Encountered

Первый прогон зонда мест упал на `receiver.id`: после перевода получателя `__init__` на `reading_name` получатель-атрибут дошёл до текста предмета. Текст предмета взят через `reading_name` в том же GREEN `340d5939` до коммита.

## Known Stubs

Нет.

## Threat Flags

Нет: правка только тестового гейта и общего модуля тестов, новых поверхностей нет.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 16-43 (волна 3) получает `reading_name` в общем модуле под этим именем. Гейт писателя ввозит его по имени, помощников с этим именем (и с подчёркиванием) в модуле гейта нет. 16-43 переводит на неё `_methodcaller_calls` приватности и вписывает имя в `REQUIRED_SHARED_NAMES` и `CARRIER_SEMANTICS`.
- Инструмент `.pytest_cache/r8diff/` оставлен в worktree:
  - самопроверку 16-42 16-43 переносит в (д) так же, как здесь перенесена 16-41 (`selfcheck_cells.json` → `selfcheck_cells_1642.json`, семейство `e-self-1642`);
  - seed — номер плана.
- `HEAD_WRONG=86` — только приватность (16-43, 16-44).
- Отложенного нет; `deferred-items.md` не создавался.

## Self-Check: PASSED

- `tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py` — FOUND; `.pytest_cache/r8diff/{corpus.py,judge.py,run.sh,selfcheck_1642.py,selfcheck_cells.json}` — FOUND.
- Коммиты `e62799d3`, `e61ab80d`, `56d13690`, `cc7fbce7`, `68c68d97`, `52729753`, `ec96cf2e`, `340d5939`, `8cac1bac`, `96c3eb65` — предки HEAD (FOUND).
- `git rev-list --count d1743b4a..96c3eb65` = 10; изменений вне коммитов нет (`git status --short` пуст).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-19*

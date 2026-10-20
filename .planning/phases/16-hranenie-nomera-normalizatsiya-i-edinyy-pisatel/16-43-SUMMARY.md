---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 43
subsystem: testing
tags: [phone-privacy-gate, wr-28, in-20, reading-name, methodcaller, getattr, r8diff, ast, pytest, tdd]
status: complete

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-42 — `reading_name` в общем модуле и гейт писателя на нём; 16-41 — инструмент r8diff (ось счёта), место находки приватности — узел"
provides:
  - "Гейт приватности ввозит `reading_name` по имени: `_methodcaller_calls`, `_last_name`, `_wrapper_aliases`, `_applied_carriers`, `_log_function_reference` читают имя связанного им; своего читателя имени у гейта нет"
  - "Трасер подложенного `app/services/phone_audit.py`; строки `NEGATIVE_CONTROLS` WR-28-P-1 / P-2, IN-20 и четыре строки цикла самопроверки; две строки `POSITIVE_CONTROLS`"
  - "Правило-паритет: `reading_name` в `REQUIRED_SHARED_NAMES` и `CARRIER_SEMANTICS`; правило `test_the_partial_value_place_is_pinned_by_a_privacy_row`"
  - "Докстринг `ReferenceCarrier.last` правдив (D-17 — только получатель `methodcaller`, у `partial` — выбор словаря); шапка приватности называет `reading_name` и летопись WR-28"
  - "Инструмент `.pytest_cache/r8diff/` для 16-44: (д) `e-self-1642`, (в) — 27 форм 16-43, (е) — самопроверка 16-43 (16 464 формы)"
affects: [16-44, 16-45]

actuals:
  tokens: 14600   # chars/4: диф трёх файлов (43 460 симв.) + selfcheck_1643.py (8 789) + правка corpus.py (4 597) + скрипты проверок (~1 500), gitignored-инструмент включён
  tasks: 3
  commits: 8      # git rev-list --count 4f1e3b7c..a77263ad (до коммита сводки)
plan_head_before: 4f1e3b7ca08930ef107d472dbf6a43d527f89795
plan_head_after: a77263adea291aa08900f63bfb40f81262aae66d

tech-stack:
  added: []
  patterns:
    - "Имя связанного в месте чтения у гейта приватности читает только общий `reading_name` (через `_last_name`-делегат тоже)"
    - "Имя, связанное со ссылкой на вызываемое журнала, читается и последним звеном члена — плоская область, как имя `methodcaller` и обёртки"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py
    - tests/test_phone_gates_parity.py
    - tests/phone_gate_grammar.py

key-decisions:
  - "`_last_name` стал делегатом `reading_name`, а не остался своей копией: поведение тождественно (имя, атрибут, getattr-строка), и каждое чтение последнего имени идёт через одного читателя"
  - "Самопроверка нашла давний класс той же оси — вызываемое журнала, связанное с ИМЕНЕМ модуля и прочитанное getattr-строкой у `sys.modules[__name__]` (1 512 форм под заявлением); закрыт циклом e1d6587e / a77263ad плоским чтением, как у `methodcaller` и обёртки; живые деревья прежние"
  - "Получатель журнала, связанный с именем модуля и прочитанный getattr-строкой, план не правил: план относит получатель к не-местам этой оси; найдено зондом, записано ниже с адресатом"
  - "Seed выборки (д) — 42 (заметка оркестратора 8), а не номер плана, как в договоре 16-41: выборка 13 прежних семейств совпадает с выборкой 16-42"

patterns-established:
  - "Самопроверка оси «где прочитано имя» гейта приватности: значение (4 + `methodcaller` × 4 получателя) × форма (12 + `getattr-read`) × чтение (4) × способ (21), двойник `account.name` — вызов журнала без находки"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Две формы WR-28 стороны приватности, девять вариантов чтения и подложенная служба — по одной находке `phone`; тот же `methodcaller` над `account.name` — вызов журнала без находки"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_audit_with_a_methodcaller_read_by_a_getattr_string_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (156 строк)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half (53 строки)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK 9"
        status: pass
    human_judgment: false
  - id: D2
    description: "Один читатель имени у обоих гейтов: `reading_name` в `REQUIRED_SHARED_NAMES` и `CARRIER_SEMANTICS`, оба гейта держат его тем же объектом"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_take_the_binding_grammar_and_carriers_from_one_module"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_structural_half_reddens_a_redefined_grammar_point"
        status: pass
    human_judgment: false
  - id: D3
    description: "IN-20: довод `ReferenceCarrier.last` правдив, строка `partial-log-reference-mapped-over-a-phone-attribute` не ловится деревом `1c243203` и ловится на HEAD"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_partial_value_place_is_pinned_by_a_privacy_row"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_base_blind.py → BASE-BLIND OK; t2_head.py → HEAD OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта приватности называет `reading_name`, чтение getattr-строкой и летопись WR-28; граница прежняя"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t3_header.py → OK"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сверка «база ↔ HEAD» по обеим осям: SELFTEST 48 / 56, SELFTEST-COUNT 1 237, четыре DIFF и BASE — ноль регрессий, HEAD_WRONG=0, OPEN_REGRESSIONS=0; самопроверка 8 232 формы под заявлением — 0 промахов"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "bash .pytest_cache/r8diff/run.sh 16-43 (HEAD a77263ad, выход 0)"
        status: pass
      - kind: other
        ref: ".pytest_cache/r8diff/selfcheck_1643.py (рабочее дерево = a77263ad) → misses=0"
        status: pass
    human_judgment: false

duration: 60min
completed: 2026-10-20
---

# Фаза 16, план 43: гейт приватности читает имя `methodcaller` общим `reading_name` (WR-28), довод IN-20 правдив — сводка

**Имя, связанное с `operator.methodcaller`, гейт приватности теперь читает общим читателем `reading_name` — тем же, что у гейта писателя, getattr-строкой тоже. Своего читателя имени у гейта больше нет. Правило-паритет требует `reading_name` у обоих гейтов. Довод `ReferenceCarrier.last` исправлен: D-17 относится только к получателю `methodcaller`, у `partial` места нет по выбору словаря, а форму держит строка таблицы. Самопроверка нашла и закрыла ещё один давний класс той же оси. Сверка «база ↔ HEAD» по обеим осям регрессий не нашла, неверных ячеек на HEAD — ноль.**

## Performance

- **Duration:** 60 min
- **Started:** 2026-10-19T23:39:13Z
- **Completed:** 2026-10-20T00:39:35Z
- **Tasks:** 3 (все `tdd`); сверх них — один цикл самопроверки
- **Files modified:** 3 (`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/phone_gate_grammar.py`)

## Accomplishments

- Гейт приватности ввозит `reading_name` по имени. `_methodcaller_calls` берёт литеральный вызов `methodcaller(…)` по последнему имени вызываемого, а иначе читает имя через `reading_name` — у `Name`, `Attribute` и getattr-строки (с умолчанием тоже).
- Подложенная служба `app/services/phone_audit.py` находится обходом. Находка ровно одна: `app/services/phone_audit.py:9 — имя — phone (владелец run)`.
- Формы WR-28-P-1 и WR-28-P-2 — строки `NEGATIVE_CONTROLS`. Девять вариантов чтения из `<automated>` задачи 1 дают по одной находке `phone`. Тот же `methodcaller` над `account.name` — вызов журнала без находки.
- Правило-паритет: `reading_name` вошёл в `CARRIER_SEMANTICS` (а значит, и в `GRAMMAR_FUNCTIONS`, с подчёркиванием и без) и в `REQUIRED_SHARED_NAMES`. Докстринг называет его в обоих перечнях.
- IN-20:
  - строка `partial-log-reference-mapped-over-a-phone-attribute`: на HEAD одна находка, деревом `1c243203` — `[]`;
  - правило `test_the_partial_value_place_is_pinned_by_a_privacy_row` держит строку и довод;
  - докстринг `ReferenceCarrier` и комментарий строки `map-named-iterable` называют строку.
- Шапка приватности: абзац о `methodcaller` называет чтение getattr-строкой и `reading_name`. Летопись WR-28 называет седьмой круг оси. Граница прежняя: пункт о вычисленном имени `getattr(logger, name)(…)` на месте, чтение имени `methodcaller` getattr-строкой в ней не названо.
- Цикл самопроверки закрыл ещё один давний класс оси. Вызываемое журнала (`logger.info`, `print`, `getattr(logger, "info")`, `partial(logger.info, …)`), связанное с ИМЕНЕМ модуля и прочитанное getattr-строкой (`getattr(sys.modules[__name__], "f")`, с умолчанием, цепочкой), уходило мимо. Это 1 512 форм под заявлением. Гейт писателя ту же форму ловит.

## Task Commits

1. **Задача 1, RED** — `c253f8bb` `test(16-43): require a methodcaller name read by a getattr string to be judged by the privacy gate (WR-28)`
2. **Задача 1, GREEN** — `b0f3c3e1` `feat(16-43): read a methodcaller-bound name with the shared reading_name in the privacy gate (WR-28)`
3. **Задача 2, RED** — `3e112260` `test(16-43): require the partial value place to be pinned by a privacy row and a true last argument (IN-20)`
4. **Задача 2, GREEN** — `4aef7f97` `feat(16-43): state the true ReferenceCarrier.last argument and name the pinning privacy row (IN-20)`
5. **Задача 3, RED** — `7b2f470e` `test(16-43): require the privacy header to name the shared reading_name and the WR-28 chronicle`
6. **Задача 3, GREEN** — `4de6555f` `feat(16-43): name the shared reading_name and the WR-28 chronicle in the privacy header`
7. **Цикл самопроверки 1, RED** — `e1d6587e` `test(16-43): require a log callable bound to a module name and read by a getattr string to be judged (self-check cycle 1)`
8. **Цикл самопроверки 1, GREEN** — `a77263ad` `feat(16-43): read a log callable bound to a module name by its last name, getattr string too (self-check cycle 1)`

Коммит сводки — `docs(16-43)`, следующий за этими.

## TDD: RED / GREEN

Улики лежат в `.pytest_cache/gsd-red/` (gitignored): JUnit-отчёт, вывод консоли и запись JSON. `gsd-tools check tdd-red-evidence` вернул `RED_EVIDENCE_OK` / `target_test_failed` для каждого RED.

### Задача 1

**RED.** Команда: `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly -k "methodcaller_read_by_a_getattr_string or methodcaller-read-by-a-getattr-string or one_module"`, выход 1. Все три признака на месте:
- `FAILED tests/test_phone_privacy_gate.py::test_a_planted_audit_with_a_methodcaller_read_by_a_getattr_string_reddens_the_gate`;
- `FAILED tests/test_phone_gates_parity.py::test_both_gates_take_the_binding_grammar_and_carriers_from_one_module`;
- последняя строка сводки — `5 failed, 276 deselected, 1 warning in 0.96s`;
- литерал правила-паритета — «гейты номера не делят одну грамматику связывания» с пунктом «`tests.test_phone_privacy_gate`: не держит общее имя `reading_name`» (в дереве до плана литерал есть — 1). Литерал трасера: «имя, связанное с `operator.methodcaller` и прочитанное getattr-строкой, гейт приватности не читает».

Смысловая оценка: все пять целей исполнились и упали на утверждениях плана. Трасер — `[]` вместо находки. Две строки — «номер в вызове журнала не найден». Строка `POSITIVE_CONTROLS` — «распознаватель не увидел вызов». Паритет — нет общего имени. Ошибок сбора нет. Прочие правила двух модулей зелёные: `5 failed, 276 passed`.

**GREEN.** Три модуля гейтов — `878 passed`. `t1_forms.py` → `OK 9`, `t1_rows.py` → `OK 145 51 151 52`, `t1_ids.py` → `OK 151 52`. Живые деревья прежние, `writer_live.py` → `OK 6 104`.

### Задача 2

**RED.** Выборка `-k test_the_partial_value_place_is_pinned_by_a_privacy_row`, выход 1:
- `FAILED tests/test_phone_gates_parity.py::test_the_partial_value_place_is_pinned_by_a_privacy_row`;
- последняя строка сводки — `1 failed, 17 deselected, 1 warning in 0.37s`;
- литерал, записанный этим RED: «место значения `partial` у `map` над не-литеральной итерируемой не закреплено строкой гейта приватности, или довод `ReferenceCarrier.last` ложен».

Красны три места:
- докстринг не называет строку;
- докстринг относит D-17 к `partial`;
- нет «по выбору словаря».

Строка `NEGATIVE_CONTROLS` — закрепка, зелёная до GREEN.

**GREEN.** Три модуля — `880 passed`. `t2_base_blind.py` → `BASE-BLIND OK`, `t2_head.py` → `HEAD OK`.

### Задача 3

**RED.** Выборка `-k test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier`, выход 1:
- `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier`;
- `1 failed, 264 deselected, 1 warning in 0.45s`;
- литерал — прежнее сообщение правила «шапка гейта приватности не называет носителя ссылки и общую грамматику» (в дереве до плана).

Красны пять мест: `reading_name`, WR-28, getattr-строка и `reading_name` в абзаце о `methodcaller`, «Летопись WR-28». Закрепки: граница не называет `getattr(self, "emit")`, пункт `getattr(logger, name)(…)` на месте.

**GREEN.** `880 passed`, `t3_header.py` → `OK`, `t3_registry.py` → `OK`, `t3_js.py` → `OK 27 0`.

### Цикл самопроверки 1 (вызываемое журнала под именем модуля, getattr-строка)

**RED.** Выборка `-k "bound-to-a-module-name"`, выход 1:
- пять строк `FAILED`, среди них `FAILED tests/test_phone_privacy_gate.py::test_a_number_handed_to_a_python_log_call_is_found[log-method-bound-to-a-module-name-read-by-a-getattr-string]`;
- `5 failed, 265 deselected, 1 warning in 0.63s`;
- литерал «номер в вызове журнала не найден» (четыре строки) и «распознаватель не увидел вызов» (двойник).

**GREEN.** `885 passed`. Живые деревья — те же 225 / 68 / 93 вызова, находок 0. Самопроверка — 0 промахов.

## Перепись мест чтения имени гейта приватности (задача 1; свойство 2 О-18 (а))

**Переведено на `reading_name`:**

| Место | Что читалось до плана | Коммит |
|-------|----------------------|--------|
| `_methodcaller_calls` — имя, связанное с `methodcaller(…)` | только `Name` / `Attribute` своими ветками | `b0f3c3e1` |
| `_last_name` — последнее имя (фабрика, привязка, псевдоним `partial`, литеральный `methodcaller`, исключение носителя у `_applied_log_methodcaller`) | своя копия: `Name` + `_member` (атрибут и getattr-строка); ответ прежний, теперь делегат `reading_name` | `b0f3c3e1` |
| `_wrapper_aliases` — имя значения псевдонима `partial` / `methodcaller` | `isinstance(Name, Attribute)` + `_last_name`; ответ прежний (значения связывания приходят через `getattr_as_attribute`) | `b0f3c3e1` |
| `_applied_carriers` — имя вызываемого `X` в `X(…)(…)` | `_callee_name`: только `Name` / `Attribute` | `b0f3c3e1` |
| `_log_function_reference` — имя члена, связанного с вызываемым журнала | `_member(node)[1]`; ответ прежний, плюс цель-имя модуля читается членом (цикл 1) | `a77263ad` |
| `_log_wrappers_of` → `named_wrappers` — имя обёртки носителя | общая `named_wrappers` с плана 16-37, через `reading_name` с плана 16-42 | — |

**Не места чтения этой оси** (с причиной):
- `_member`. Возвращает пару «объект, имя» для получателя и метода журнала (`logger.info`, `getattr(logger, "info")`): нужен объект-получатель, а имя — имя метода журнала, а не имя связанного значения. getattr-строку читает общая `getattr_literal`.
- `_is_log_receiver`. Имя получателя журнала. План относит его к не-местам оси (имя журнала).
- `_is_print_reference`. Опознание встроенного `print` / `builtins.print` по литералу.
- Ветки `Name` у `_binder_reference` и `_log_function_reference`. Голое имя ввоза (`from logging import info`, псевдоним привязки): ввезённое имя зовут только голым.
- `_bind`, `binding_name(target)` в `module_log_names`. Это цель связывания, её читает не `reading_name`.
- `_callee_name` у `MASK_FUNCTION`. Опознание `mask_phone` по имени.
- `_judge_arguments` (`Name.id` / `Attribute.attr` с `phone`). Это ось «как назван номер», предмет находки.
- `value.func.id == "bool"` у признака присутствия. Встроенный `bool`.

Помощников с именем `reading_name` или `_reading_name` в модуле гейта нет: структурная половина паритета краснела бы.

## Самопроверка исполнителя (задача 3; О-18 (а), свойство 2)

Скрипт — `.pytest_cache/r8diff/selfcheck_1643.py` (gitignored, в репозиторий не коммитится). Он однопроцессный и гонится под общим `flock`. Каждая форма подаётся в `python_log_offences(…, "app/x.py")`. Дерево подаётся аргументом.

**Оси (полный крест, без ротации):**
- **Значение (8 точек):** `print`, `logger.info`, `getattr(logger, "info")`, `functools.partial(logger.info, "x %s")` — и `operator.methodcaller("info", "x %s", account.phone)` с получателем `logger`, `self.log`, `logging`, `structlog.get_logger()` (у прочих значений получатель — в самом значении).
- **Форма связывания (13):** 12 `BINDING_FORMS` и кандидат `getattr-read` договора 16-41.
- **Чтение имени (4):** как в форме; getattr-строка (`self.f` → `getattr(self, "f")`, `cls.f` → `getattr(cls, "f")`, `f` → `getattr(sys.modules[__name__], "f")`); getattr-строка с умолчанием `None`; цепочка `g = getattr(<obj>, "f"); …g…`.
- **Способ (21):** прямой вызов и 20 `REFERENCE_CARRIERS`.
- **Безопасный двойник каждой ячейки:** `account.name` / `account.names` вместо номера.

**Ожидание:**
- под заявлением — находки непусты, каждая называет `phone`;
- число находок равно числу мест, посчитанному генератором: вставки `account.phone` / `account.phones` в исходник, каждая вставка — свой узел. У всех 8 232 форм оно равно 1;
- двойник — вызов журнала (`python_log_calls` непуст) без находки.

**Размер.** Полный крест — 8 × 13 × 4 × 21 = 8 736 сочетаний. Не собрано 504: у формы `direct` нет имени, поэтому только «как в форме». Итого 8 232 формы под заявлением и 8 232 двойника — 16 464 формы, все прогнаны.

| Заход | Дерево | Форм (под заявлением / двойников) | Промахов | Итог |
|-------|--------|-----------------------------------|----------|------|
| 1 | `4aef7f97` (GREEN задачи 2) | 16 464 (8 232 / 8 232) | 2 646: 1 512 под заявлением + 1 134 двойника | класс цикла `e1d6587e` / `a77263ad` |
| контроль против вакуума | `4f1e3b7c` (база плана) | 16 464 | 6 846: 3 612 под заявлением + 3 234 двойника | генератор видит WR-28 там, где он был |
| 2 (итог) | рабочее дерево = `a77263ad` | **16 464 (8 232 / 8 232)** | **0** | ячейки ушли в корпус (е) |

**Класс захода 1.** Шесть форм связывания с целью-именем модуля (`assign`, `annotated`, `tuple-pair`, `walrus`, `rebound`, `rebound-reversed`) × три чтения getattr-строкой × 21 способ — по 126 на класс. Под заявлением 12 классов: `name`, `attribute`, `getattr-string`, `partial`. Двойников 9 классов: у `partial` связывание само — вызов журнала. Имя, связанное с вызываемым журнала, гейт клал в `log_functions`, а член объекта сверял только с `log_function_attributes`. На базе `4f1e3b7c` и на `1c243203` — тот же `[]` (зонд `probe_writer_module_getattr.py`): давний пропуск, не регрессия. Гейт писателя ту же форму (`f = setattr; getattr(sys.modules[__name__], "f")(account, "phone", x)`) ловит.

**Контроль на базе по классам** (под заявлением):
- тот же класс — 1 512;
- `methodcaller` × getattr-строка и getattr-строка с умолчанием — по 252 на получатель;
- `methodcaller` × `getattr-read` как в форме — по 21 на получатель.

Итого 4 × 525 = 2 100 форм WR-28.

**По осям (заход 2, под заявлением):**
- значения — по 1 029;
- чтения — 2 184 как в форме, по 2 016 у трёх getattr-чтений;
- формы — по 672, у `direct` 168;
- способы — по 392.

Каждая из 8 232 форм под заявлением дала ровно одну находку (`claim:1 = 8232`). Двойники — вызов журнала без находки.

**Найдено вне осей самопроверки (зонд, не правилось).** Получатель журнала, связанный с ИМЕНЕМ модуля и прочитанный getattr-строкой:
- `lg = logging.getLogger(); getattr(sys.modules[__name__], "lg").info("x %s", account.phone)`;
- `emit(getattr(sys.modules[__name__], "lg"))` при `emit = operator.methodcaller("info", "x %s", account.phone)`.

Обе формы дают `[]` на HEAD, на базе `4f1e3b7c` и на `1c243203` — давний пропуск. План относит получатель журнала к не-местам оси «где прочитано имя» (`_last_name`, `_member` — «имя журнала, а не имя связанного значения»). Плоское чтение `receiver_attributes` по образцу цикла 1 поменяло бы смысл `_log_method_reference`: `logger.log` при `log = logging.getLogger()` перестал бы быть ссылкой на метод. Поэтому правки нет. Адресат — владелец и следующее ревью: ось «как опознан журнал», получатель, прочитанный членом модуля. 16-44 этого не закрывает: строк словаря тут нет.

Прогоны: 2026-10-20, ≈00:11–00:14 UTC.

## Сверка «база ↔ HEAD» с осью счёта (свойство 6 О-18 (а); пункт 5 договора `16-41-PLAN.md`)

**Инструмент.** Основа — копия r8diff 16-42 от оркестратора (`scratchpad/tools/r8diff-16-42/`, `cp -a` в `.pytest_cache/r8diff/`). Договор (а)–(з) пересверен с `<scope_note>` 16-41. Изменения:
- **`corpus.py`:**
  - `SEED = 42` — прежний (см. отклонение 3);
  - (д) — семейство `e-self-1642`: самопроверка 16-42 (`selfcheck_cells.json` → `selfcheck_cells_1642.json`, 22 512 форм), позиционная выборка;
  - (в) — 27 форм 16-43: одиннадцать вариантов чтения имени `methodcaller` над журналом (девять плана, получатель getattr-строкой, контроль атрибутом) и одиннадцать их двойников над `account.name`, трасер, две строки WR-28 стороны приватности дословно, строка IN-20 и её двойник `account.names`;
  - (е) — `selfcheck_cells.json` самопроверки 16-43.
- **`judge.py` и `run.sh`** не менялись.

**Корпус итогового прогона:** HEAD `a77263ad`, 58 947 ячеек, `corpus.json` sha256 `4c0be8601f8f60fe2a6f5494e8c6ef825b9a4accf6a89c8582beb318e3f72a1f`.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 259, `LEGITIMATE_CASES` 105, `NEGATIVE_CONTROLS` 156, `POSITIVE_CONTROLS` 53 | 573 |
| (б) матрицы | `b-matrix` 2 520 + `b-candidate` 756 | 3 276 |
| (в) формы ревью | раунд 7 — 30, раунд 8 — 16, план 16-42 — 33, план 16-43 — 27 | 106 |
| (г) дифференциал | — | 700 |
| (д) выборка самопроверок | 14 семейств по 2 000 | 28 000 |
| (ж) две подачи на одной строке | — | 3 276 |
| (з) безопасные двойники | — | 6 552 |
| (е) самопроверка 16-43 | целиком, 16 464 ≤ 20 000 | 16 464 |

**Правило выборки (д):** равномерно, без повторов, `random.Random(42)`, ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием. Семейства 16-39, 16-41 и 16-42 материализуются и выбираются по позиции.

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
- самопроверка 16-41 — 36 876;
- самопроверка 16-42 — 22 512.

**Не прогнано выборкой:** 11 105 261 форма (11 133 261 − 28 000). Самопроверка 16-43 вошла в (е) целиком.

**Строки итогового прогона** (`bash .pytest_cache/r8diff/run.sh 16-43`, HEAD `a77263ad`, 2026-10-20 00:15:26–00:32:32 UTC, выход 0) — дословно:

```
CORPUS_SHA256=4c0be8601f8f60fe2a6f5494e8c6ef825b9a4accf6a89c8582beb318e3f72a1f HEAD=a77263adea291aa08900f63bfb40f81262aae66d
SELFTEST 1bebbbf7 -> c6953017: cells=3382 regressions=48 count_regressions=48 fixed=208 repaired_overcount=0 changed=256
SELFTEST 5e32c335 -> 147f5e46: cells=3382 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3591 regressions=831 count_regressions=1237 fixed=26 repaired_overcount=2 changed=1317
DIFF c253f8bb -> b0f3c3e1: cells=58947 regressions=0 count_regressions=0 fixed=4310 repaired_overcount=0 changed=2200
DIFF 3e112260 -> 4aef7f97: cells=58947 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF 7b2f470e -> 4de6555f: cells=58947 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
DIFF e1d6587e -> a77263ad: cells=58947 regressions=0 count_regressions=0 fixed=2651 repaired_overcount=0 changed=1516
BASE 4f1e3b7c -> HEAD a77263ad: cells=58947 regressions=0 count_regressions=0 fixed=6961 repaired_overcount=0 changed=3716
HEAD_WRONG=0
OPEN_REGRESSIONS=0
```

`SELFTEST 1bebbbf7 -> c6953017` — 48, у 16-42 было 47: в (в) выросли формы ревью, и регрессию `c6953017` видит ещё одна ячейка. Перечней `REGRESSED`, `COUNT_REGRESSED`, `REPAIRED` в выводе нет: на каждом GREEN и в `BASE` они пусты.

**`fixed` по семействам** (`fixed_by_family.py`):
- `DIFF c253f8bb -> b0f3c3e1`:
  - `b-candidate` приватности `getattr-read × methodcaller` и `× methodcaller-receiver` — 42;
  - (ж) D2 той же оси — 42;
  - (в) — 23: `WR-28-P-1`, `WR-28-P-2`, трасер, две строки дословно, девять вариантов чтения 16-43 и их двойники;
  - (а) — 3: две строки `NEGATIVE_CONTROLS` и строка `POSITIVE_CONTROLS` задачи 1;
  - (е) — 4 200;
- `DIFF e1d6587e -> a77263ad` — (а) 5 (строки цикла 1), (е) 2 646;
- `BASE` — (а) 8, (б) 42, (в) 23, (ж) 42, (е) 6 846.

**Промежуточные прогоны** (каждый — выход 0, `OPEN_REGRESSIONS=0`, `SELFTEST` 48 / 56, `SELFTEST-COUNT … count_regressions=1237`):
1. После GREEN задачи 1. HEAD `b0f3c3e1`, корпус 42 477 без (е), sha `2dcbb1fecba8458426f40069d833278bfa9afa245c676ffc8e5410727e5f0940`, 23:48:59–23:54:18 UTC:
   - `DIFF c253f8bb -> b0f3c3e1: cells=42477 regressions=0 count_regressions=0 fixed=110 repaired_overcount=0 changed=100`;
   - `BASE 4f1e3b7c -> HEAD b0f3c3e1: … regressions=0 count_regressions=0 fixed=110`;
   - `HEAD_WRONG=0`.
2. После GREEN задачи 2. HEAD `4aef7f97`, корпус 42 478, sha `8729c24db89f8889c22eb96f4261b0254213320b235be0a37f8c42e612de7f8c`, 23:56:33–00:04:34 UTC: `DIFF 3e112260 -> 4aef7f97: … changed=0`, `BASE … regressions=0 count_regressions=0 fixed=110`, `HEAD_WRONG=0`.
3. После GREEN задачи 3. HEAD `4de6555f`, тот же корпус, 00:08:24–00:11:34 UTC: `DIFF 7b2f470e -> 4de6555f: … changed=0`, `BASE … regressions=0 count_regressions=0`, `HEAD_WRONG=0`.
4. После цикла 1 — итоговый прогон выше: корпус с (е), 58 947.

**Регрессий нет** ни на одном GREEN, ни по наличию, ни по счёту. `REPAIRED` — 0. Циклов сверки не было; дополнительный цикл — из самопроверки.

**`HEAD_WRONG=0`.** Из 86 ячеек, неверных на HEAD после 16-42, 86 — ячейки приватности этого плана:
- `b-candidate` — 42;
- (ж) D2 — 42;
- `WR-28-P-1`, `WR-28-P-2`.

Все сняты задачей 1 (`b0f3c3e1`). Неверных ячеек для 16-44 не осталось. Словарь (`getattr-read` в `BINDING_FORMS`, `methodcaller-receiver`) этот план не трогал: кандидаты судятся корпусом и на HEAD верны.

## Гейты на итоговом дереве (`a77263ad`, под общим `flock`)

| Проверка | Итог | До плана |
|----------|------|----------|
| `<automated>` задачи 1 №1 (приватность + паритет) — в составе трёх модулей ниже | приватность 270, паритет 18 | 260 / 17 |
| три модуля гейтов поимённо (приватность, писатель, паритет) | `885 passed` (приватность 270, писатель 597, паритет 18) | 874 |
| `<automated>` задачи 1 №2 (`t1_rows.py`) | `OK 145 51 156 53` | — |
| `<automated>` задачи 1 №3 (`t1_forms.py`) | `OK 9` | — |
| `<automated>` задачи 1 №4 (писатель) | 597 в составе 885 | 597 |
| приёмка задачи 1 (`t1_ids.py`) | `OK 156 53` | — |
| `<automated>` задачи 2 №2 (`t2_base_blind.py`, `t2_head.py`) | `BASE-BLIND OK`, `HEAD OK` | — |
| `<automated>` задачи 3 №2 (`t3_header.py`) | `OK` | — |
| приёмка задачи 3 (`t3_registry.py`, `t3_js.py`) | `OK`; `OK 27 0` | — |
| предусловие (`precondition.py`) | `OK` | `OK` |
| quick run фазы (8 путей) | `1289 passed` | 1278 |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| живое дерево писателя (`writer_live.py`) | `OK 6 104` | то же |
| `tests/test_application` | `882 passed` | 882 |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `test_templates`, `test_declared_invariants`) | `576 passed` | 576 |
| `tests/test_logging_config.py` | `3 passed` | 3 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, «реестр: 875 строк, биекция с переписью — согласие» | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | `110 passed` | 110 |
| `run.sh 16-43` | выход 0 (строки выше) | — |

`tests/test_planning` гонится после коммита сводки; итог — в финальном сообщении исполнителя оркестратору.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`:
  - ввоз `reading_name` с комментарием;
  - `_methodcaller_calls`, `_last_name`, `_wrapper_aliases`, `_applied_carriers`, `_log_function_reference` переведены на `reading_name`;
  - цель-имя вызываемого журнала идёт и в `log_function_attributes`;
  - трасер;
  - 7 строк `NEGATIVE_CONTROLS`, 2 строки `POSITIVE_CONTROLS`;
  - шапка — абзац о `methodcaller` и летопись WR-28;
  - правило шапки — места WR-28.
- `tests/test_phone_gates_parity.py` — `reading_name` в `CARRIER_SEMANTICS` и `REQUIRED_SHARED_NAMES`; правило `test_the_partial_value_place_is_pinned_by_a_privacy_row`; докстринг называет имя и правило.
- `tests/phone_gate_grammar.py` — докстринг `ReferenceCarrier` (поле `last`), комментарий строки `map-named-iterable`, докстринг `reading_name` называет оба гейта.

Инструмент сверки (gitignored, не коммитится, оставлен в worktree для 16-44):
- `.pytest_cache/r8diff/`:
  - `corpus.py` — (д) `e-self-1642`, (в) 16-43;
  - `judge.py`, `run.sh`;
  - `selfcheck_1643.py`, `selfcheck_cells.json` (самопроверка 16-43, 16 464), `selfcheck_report_1643.json`;
  - `selfcheck_cells_1642.json`, `fixed_by_family.py`, `trees/`, `judged/`, `run-1643-*.out|err`;
- `.pytest_cache/checks/*.py` — дословные `python -c` плана и зонды.

## Decisions Made

- `_last_name` — делегат `reading_name`. Поведение тождественно: `Name.id`, `Attribute.attr`, строка `getattr_literal`. Теперь каждое чтение последнего имени у гейта идёт через одного читателя. Своей копии чтения не осталось.
- Плоское чтение вызываемого журнала (цикл 1). Имя, связанное со ссылкой на вызываемое журнала, читается и последним звеном члена, как имя `methodcaller` и обёртки: у них оно плоское с плана 16-31 / 16-37. Ввезённое из `logging` имя — по-прежнему только голым (угадывания по имени метода нет, D-17). Живые деревья те же: 225 / 68 / 93, находок 0.
- Получатель журнала не правился (см. «Найдено вне осей самопроверки»).

## Deviations from Plan

### Расхождения «план ↔ замер» (записаны, ничего не ослаблено)

**1. [Rule 2 — та же ось] Цикл самопроверки сверх трёх задач.** Найдено самопроверкой: вызываемое журнала, связанное с именем модуля и прочитанное getattr-строкой, — 1 512 форм под заявлением. На базе `4f1e3b7c` и на `1c243203` то же: давний пропуск, не регрессия. Цикл `e1d6587e` / `a77263ad`: четыре строки `NEGATIVE_CONTROLS` и строка `POSITIVE_CONTROLS`. Сверен `run.sh`. Затронут только файл плана.

**2. Числа плана меньше замера.**
- Писатель: план — 581, замер на базе и после — 597.
- Задача 1 №1: план — ≥ 281, замер — 282 после задачи 1, 288 итог.
- Задачи 2–3 №1: план — ≥ 864, замер — 880 / 885.
- Quick run: план — ≥ 1268, замер — 1289.
- Таблицы: план — ≥ 151 / 52, замер — 156 / 53.

Пороги «не меньше» выполнены. Строки не удалялись и не правились: `OK 145 51 …` против `8aabdb38`.

**3. Seed выборки (д) — 42, а не номер плана.** Договор 16-41 велит `random.Random(<номер плана>)`, заметка оркестратора 8 — seed 42. Принят seed 42: выборка 13 прежних семейств совпадает с выборкой 16-42.

**4. Нумерация строк плана.** План называл строки на `8aabdb38`. Символы найдены по имени на `4f1e3b7c`.

### Замены команд (песочница worktree, заметки оркестратора 3, 4)

- `python -c` из `<automated>` и приёмки записаны дословно в `.pytest_cache/checks/` (`t1_rows.py`, `t1_forms.py`, `t1_ids.py`, `t2_base_blind.py`, `t2_head.py`, `t3_header.py`, `t3_registry.py`, `t3_js.py`, `precondition.py`, `writer_live.py`). Запуск — с `PYTHONPATH=.` (у `t2_base_blind.py` — `python -I`, как в плане).
- `git show 8aabdb38:… > .pytest_cache/r8_base_privacy.py` — простой командой. `git archive -o …tar 1c243203 -- …` и `tar -xf` — отдельными шагами.
- Песочница отклонила составную команду с `git rev-parse --git-dir` для записи журнала плана. Журнал `gsd-plan-head-before-16-43` лежит в `.pytest_cache/`, а не в git-каталоге worktree. Запуск `flock` с `$PWD` тоже отклонён — путь написан литералом.
- `graphify query` гонялся по графу основного дерева (`--graph /source/broadcaster/graphify-out/graph.json`). `graphify update .` не запускался — его гонит оркестратор после слияния.
- Полная суита (`just test`, ≈46 мин) не гонялась — её гонит пост-мердж гейт оркестратора.

---

**Total deviations:** 4 записанных расхождения (1 — дополнительный цикл той же оси по правилу 2, 3 — «план ↔ замер» без ослабления), плюс замены команд.
**Impact on plan:** заявление шапки не сужено, граница прежняя, реестр `{}`, потолок 0, JS-половина не тронута (`OK 27 0`), гейт писателя — прежний ответ (597, `OK 6 104`). Правились только три файла плана и gitignored-инструмент.

## Issues Encountered

Нет.

## Known Stubs

Нет.

## Threat Flags

Нет: правка только тестовых гейтов и общего модуля тестов, новых поверхностей нет.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 16-44 (волна 4) получает:
  - `HEAD_WRONG=0`;
  - инструмент `.pytest_cache/r8diff/`: seed 42, (д) с `e-self-1642`, (в) с формами 16-43, (е) — самопроверка 16-43. Её 16-44 переносит в (д) так же (`selfcheck_cells.json` → `selfcheck_cells_1643.json`, семейство `e-self-1643`).
- Условие закрытия 16-44 `HEAD_WRONG=0` на этом корпусе уже выполнено. Строки словаря (`getattr-read`, `methodcaller-receiver`) и сверки `--against-batch 16-41`, `--against 1c243203`, `--against 2f8c1656` — объём 16-44.
- Открытым остаётся найденное вне осей: получатель журнала под именем модуля, прочитанный getattr-строкой. Адресат — владелец и ревью: ось «как опознан журнал».
- `deferred-items.md` не создавался.

## Self-Check: PASSED

- `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/phone_gate_grammar.py` — FOUND; `.pytest_cache/r8diff/{corpus.py,judge.py,run.sh,selfcheck_1643.py,selfcheck_cells.json}` — FOUND.
- Коммиты `c253f8bb`, `b0f3c3e1`, `3e112260`, `4aef7f97`, `7b2f470e`, `4de6555f`, `e1d6587e`, `a77263ad` — предки HEAD (FOUND).
- `git rev-list --count 4f1e3b7c..a77263ad` = 8; изменений вне коммитов нет (`git status --short` пуст).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-20*

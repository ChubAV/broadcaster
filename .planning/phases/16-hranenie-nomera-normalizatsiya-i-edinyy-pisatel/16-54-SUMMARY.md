---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 54
subsystem: testing
tags: [ast, static-gate, privacy, ban-channel, runtime-mask, logging, O-23, O-24, CR-05, WR-32, WR-33, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "канал запрета `dynamic_construct_findings` и `dynamic_construct_scan` гейта приватности (16-53); маска номера на исполнении `app/services/log_masking.py` и `app/logging_config.py` (16-52)"
provides:
  - "tests/test_phone_privacy_gate.py — `ROUND_TEN_BANNED_FORMS` (18 строк: 14 CR-05, 2 WR-32, 2 WR-33) и правило `test_a_round_ten_form_is_red_as_a_banned_construct`; трасер `test_a_planted_notice_through_the_module_object_is_red_as_a_banned_construct` с таблицей `PLANTED_BANNED_SERVICES`"
  - "tests/test_phone_privacy_gate.py — `LOGGING_CONFIG_MODULE`, `logging_reconfigurations`, `logging_reconfiguration_scan`, правило `test_no_logging_reconfiguration_outside_the_logging_config` и контроль `test_a_planted_logging_reconfiguration_reddens_the_rule` (14 форм)"
  - "tests/test_phone_privacy_gate.py — раздел шапки «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ», согласование прежних запретов, летописи CR-05 / WR-32 / WR-33, оговорки прежних обещаний, правило `test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask`"
affects: [16-56, "Фазы 17–20 (перенастройка журнала вне app/logging_config.py краснит гейт приватности; любая форма CR-05 / WR-32 / WR-33 краснит канал)"]

actuals:
  tokens: 12979   # chars/4: дифф d9b38e21..b758f763 — 51 914 знаков (wc -m)
  tasks: 3
  commits: 6      # git rev-list --count d9b38e21..HEAD до коммита сводки
plan_head_before: d9b38e21f7147f8b86ce9ac7e5a53f1096e23fae
plan_head_after: b758f7635e1e2f0e1d1f4ef4f2e3e3c3c1e0b1c3

tech-stack:
  added: []
  patterns:
    - "Строка формы судится тем же путём, что живое дерево: `dynamic_construct_scan` над синтетическим `app/`, вид — по замеру канала, место — строка-маркер, однозначная в теле"
    - "Перенастройка журнала живёт в одном модуле: правило по `ast` с исключением ровно `LOGGING_CONFIG_MODULE` и антивакуумом — тот же помощник находит настройку в исходнике этого модуля под чужим путём"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Вид строки `cr05-getattr-sys-modules` — «имя запрещённой роли строкой», прочих 13 строк CR-05 — «объект модуля», строк WR-32 / WR-33 — «отложенный вызов по имени»: по замеру канала 16-53, как и требовал оркестратор"
  - "Трасер берёт подложенную службу из таблицы `PLANTED_BANNED_SERVICES`: RED — пустая таблица (канал уже стоит), GREEN — запись службы"
  - "Правило перенастройки журнала судит сверх буквы плана `configure_once`, правку списков `.handlers` / `.filters` на месте, `del`, составное присваивание и `setattr` со строкой — у каждого написания строка контроля"
  - "`setattr(self, \"f\", logger.info)` с литеральным именем каналу не конструкция (замер): шапка оставляет его границей предиката и не называет запрещённым, вопреки букве плана"

patterns-established:
  - "Оговорка О-23 (а) к прежнему обещанию полноты написаний ставится рядом с фразой, а не переписывает её: прежние фразы держит правило шапки 16-09…16-49"

requirements-completed: [PHONE-21]   # копия requirements плана; REQUIREMENTS.md этот план не трогает (заметка 5 оркестратора)

coverage:
  - id: D1
    description: "Подложенная служба `app/services/phone_notice_via_module.py` (журнал через `self.me = sys.modules[__name__]`) краснит канал ровно одной находкой «объект модуля» на :11"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_notice_through_the_module_object_is_red_as_a_banned_construct"
        status: pass
    human_judgment: false
  - id: D2
    description: "18 форм раунда 10 (CR-05 ×14, WR-32 ×2, WR-33 ×2), подложенные в синтетическое `app/`, краснят канал находкой ожидаемого вида на строке конструкции"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_round_ten_form_is_red_as_a_banned_construct"
        status: pass
    human_judgment: false
  - id: D3
    description: "Перенастройка журнала вне `app/logging_config.py` краснит гейт; живые `app/` и `scripts/` — 106 файлов, 0 находок; контроль — 14 форм"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_logging_reconfiguration_outside_the_logging_config, #test_a_planted_logging_reconfiguration_reddens_the_rule"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта правдива об обещании после О-23 (а): раздел запрета и маски, исключения, граница маски, согласование запретов, летописи, D-11, живые числа"
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask"
        status: pass
    human_judgment: false
  - id: D5
    description: "Прежнее не ослаблено: предикаты распознавания и JS-функции — тела как на `c9da79b2`; строки 173 / 61 / 14; живое дерево — находок 0"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/base_predicates.py (вторая <automated> задачи 3) и .pytest_cache/checks/base_rows.py — после каждого GREEN"
        status: pass
    human_judgment: false

duration: 38min
completed: 2026-10-23
status: complete
---

# Phase 16 Plan 54: Формы раунда 10 как запрещённые конструкции, правило перенастройки журнала и правдивая шапка гейта приватности Summary

**В гейте приватности 18 форм CR-05 / WR-32 / WR-33 стали строками канала запрета, и каждая краснит его на своей строке. Подложенная служба, читающая журнал через `self.me = sys.modules[__name__]`, даёт ровно одну находку «объект модуля». Перенастройка журнала вне `app/logging_config.py` теперь краснит гейт, и маску на исполнении нельзя молча выключить. Шапка говорит, что гейт обещает после О-23 (а): что запрещено, что исключено, что ловит маска и где её граница.**

## Performance

- **Duration:** 38 мин
- **Started:** 2026-10-23T10:30:09Z
- **Completed:** 2026-10-23T11:08Z
- **Tasks:** 3 (трасер + 2), все RED → GREEN
- **Files modified:** 1 (`tests/test_phone_privacy_gate.py`; продуктовый код, общий модуль, гейт писателя и паритет не тронуты)

## Accomplishments

- **Формы раунда 10 — строки канала (задача 1).** `RoundTenBannedForm(id, body, marker, kind)`, общая шапка тел `ROUND_TEN_FORM_HEADER` и 18 строк `ROUND_TEN_BANNED_FORMS`:
  - 13 написаний CR-05 и получатель `self.me.lg.info(…)`;
  - WR-32 — `to_thread = operator.methodcaller("noop")` и `run = operator.methodcaller("run")`;
  - WR-33 — `to_thread = operator.methodcaller` и `partial = operator.methodcaller`.

  Правило `test_a_round_ten_form_is_red_as_a_banned_construct` подкладывает тело в синтетическое `app/x.py`. Маркер строки должен стоять в теле ровно один раз. Канал (`dynamic_construct_scan`) обязан дать находку ожидаемого вида на этой строке.
- **Трасер.** `test_a_planted_notice_through_the_module_object_is_red_as_a_banned_construct` проверяет службу `app/services/phone_notice_via_module.py` из таблицы `PLANTED_BANNED_SERVICES`. Её строки дословно взяты из `<behavior>`. Итог: ровно одна находка `…:11 — запрещённая конструкция — объект модуля — sys.modules`.
- **Правило перенастройки журнала (задача 2).** Добавлены `LOGGING_CONFIG_MODULE = "app/logging_config.py"`, `LOGGING_RECONFIGURATION_TREES = ("app", "scripts")`, помощник `logging_reconfigurations(source, path)` и обход `logging_reconfiguration_scan(root)`. Помощник находит:
  - `structlog.configure` / `configure_once` / `reset_defaults`;
  - `basicConfig`;
  - `dictConfig` / `fileConfig` / `listen` у `config` и ввезённые из `logging.config`;
  - `addHandler` / `removeHandler` / `removeFilter` / `setFormatter` у любого получателя;
  - присваивание, `del`, составное присваивание и `setattr` со строкой для `handlers` / `filters` / `propagate`;
  - правку списков `.handlers` / `.filters` на месте.

  Сам `LOGGING_CONFIG_MODULE` даёт ноль. Антивакуум: тот же исходник под путём `app/x.py` даёт четыре находки — `structlog.configure`, `setFormatter`, `root.handlers.clear()`, `addHandler`.
- **Правдивая шапка (задача 3).**
  - Новый раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ» стоит перед границей. В нём:
    - обещание свойства 1 и правило свойства 5;
    - девять видов, у каждого пример, сверенный замером;
    - шесть исключений поимённо;
    - маска `app/services/log_masking.py` (О-24 (а)): что видно, цена, граница — `print`, `max_worker`, `wa_worker`, процессы без `setup_logging`, обработчики после настройки, край грамматики;
    - правило `LOGGING_CONFIG_MODULE`;
    - «второй рубеж» и необязательность меры «база ↔ HEAD» (WR-35);
    - абзац «СОГЛАСОВАНИЕ ПРЕЖНИХ ЗАПРЕТОВ» с группами С1 / С2 / У таблицы `16-56-PLAN.md`, приведёнными дословно по составу.
  - Летописи CR-05, WR-32, WR-33.
  - Оговорки О-23 (а) к фразам «каждое толкование узла», «Связанное имя читается и через объект модуля», «поданный ЛЮБОМУ» и к трём пунктам границы.
  - Абзац D-11 вступления теперь называет маску «последним рубежом».
  - «Живые числа»: 227 / 68 / 93, прежние 225 / 68 / 93 оставлены летописью с причиной сдвига.
  - Докстринг `ModuleLogNames` называет два написания объекта модуля и запрет остальных.

## Task Commits

1. **Задача 1 (трасер): подложенная служба через атрибут-объект модуля; формы раунда 10 — строки канала**
   - RED `a2f3d247` — `test(16-54): add failing tracer for a planted notice through the module object and the round-ten banned-form rows`
   - GREEN `270ad907` — `feat(16-54): planted module-object notice red as a banned construct; round-ten CR-05, WR-32, WR-33 forms as ban-channel rows`
2. **Задача 2: перенастройка журнала только в `app/logging_config.py`**
   - RED `26d11d56` — `test(16-54): add failing rule that only the logging config module reconfigures logging, and its seven-form control`
   - GREEN `eb4154dc` — `feat(16-54): logging reconfiguration outside app/logging_config.py reddens the privacy gate`
3. **Задача 3: правдивая шапка**
   - RED `88e18441` — `test(16-54): add failing rule that the privacy gate header names the ban channel and the runtime mask`
   - GREEN `b758f763` — `feat(16-54): truthful privacy gate header - ban channel, runtime mask and its boundary, CR-05/WR-32/WR-33 chronicles, reconciliation of prior prohibitions`

REFACTOR-коммитов нет. Хэш GREEN задачи 1 для строк CR-05, WR-32, WR-33 плана 16-56 — `270ad907`. Шапку (CR-05: «шапка правдива») закрывает `b758f763`.

## TDD: RED-улики (три совпадения + `gsd-tools check tdd-red-evidence`)

Улики лежат в `.pytest_cache/gsd-red/` (gitignored): `task{1,2,3}.xml` (JUnit), `.out` (консоль с `rc=`), `.json` (запись `{command, exitCode, targetTest, output, expected, actual, semanticAssessment}`). Классификатор на всех трёх вернул `RED_EVIDENCE_OK` / `target_test_failed`.

- **Задача 1.** Команда: `-k test_a_planted_notice_through_the_module_object_is_red_as_a_banned_construct`.
  - В выводе есть `FAILED tests/test_phone_privacy_gate.py::test_a_planted_notice_through_the_module_object_is_red_as_a_banned_construct`. Последняя строка — `1 failed, 328 deselected, 1 warning in 0.51s`.
  - Литерал: «подложенная служба, читающая журнал модуля через атрибут-объект модуля, не красна запретом конструкции: служба None, находки файла []».
  - Семантика: цель исполнилась и упала на запланированном утверждении. RED свидетельствует о зависимости трасера от таблицы подложенных служб: поведение канала поставил план 16-53, так и предписано `<tdd_notes>`.
  - **Закрепки:** все 18 строк `ROUND_TEN_BANNED_FORMS` зелёные с первого прогона (`-k round_ten`: 18 passed). Их предмет — держать запрет, а не доказывать его новизну.
- **Задача 2.** Команда: `-k logging_reconfiguration`.
  - В выводе есть `FAILED …::test_a_planted_logging_reconfiguration_reddens_the_rule[basic-config]` и ещё шесть параметров, а также `FAILED …::test_no_logging_reconfiguration_outside_the_logging_config`. Последняя строка — `8 failed, 329 deselected` (N = 8 ≥ 7).
  - Литерал: «подложенная перенастройка журнала `…` вне app/logging_config.py не краснит правило».
  - Семантика: все 8 падений — `AssertionError`. Заглушка помощника в RED-коммите возвращала `[]`, ошибок сбора и ввоза не было.
- **Задача 3.** Команда: `-k test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask`.
  - В выводе есть `FAILED …::test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask`. Последняя строка — `1 failed, 344 deselected`.
  - Литерал: «шапка гейта приватности не называет запрет динамики и защиту на исполнении (13)». Недостачи: раздела нет, трёх летописей нет, нет «последним рубежом», нет оговорок трёх фраз и трёх пунктов границы, `ModuleLogNames` без оговорки и без «запрещ», «Живые числа» без «16-52» и «227».
  - Модуль в RED: 1 failed, 344 passed.

## Ответ прежнего предиката на строках форм (справочно, в коде не утверждается — свойство 5 О-23)

Ответ `python_log_offences(source, "app/x.py")` на HEAD плана (`.pytest_cache/checks/t1_prior_predicate.py`):

| Строка | находок прежнего предиката | вид канала |
|---|---|---|
| `cr05-self-attribute`, `cr05-getattr-self`, `cr05-class-body-self`, `cr05-class-body-class-name` | 0 | объект модуля |
| `cr05-sys-alias`, `cr05-sys-alias-bound`, `cr05-from-sys-import-modules`, `cr05-from-sys-import-modules-as`, `cr05-sys-modules-get` | 0 | объект модуля |
| `cr05-getattr-sys-modules` | 0 | имя запрещённой роли строкой |
| `cr05-importlib`, `cr05-from-importlib`, `cr05-importlib-bound` | 0 | объект модуля |
| `cr05-receiver-through-self-module-object` | 0 | объект модуля |
| `wr32-methodcaller-under-a-carrier-name`, `wr32-methodcaller-under-run` | 0 | отложенный вызов по имени |
| `wr33-operator-methodcaller-under-a-carrier-name` | 0 | отложенный вызов по имени |
| `wr33-partial-alias-of-methodcaller` | 1 (`app/x.py:7 — имя — phone (владелец go)`) | отложенный вызов по имени |
| трасер `phone_notice_via_module.py` | 0 | объект модуля |

17 из 18 строк прежний предикат не ловит, и это ровно гэп раунда 10. Строку `wr33-partial-alias-of-methodcaller` он ловит: у этой формы журнал подан литералом `logger.info` в `functools.partial`. Каждую строку краснит канал.

## Гейты на конечном дереве (под общей блокировкой)

| Прогон | Итог | База / ожидание плана |
|---|---|---|
| `test_phone_privacy_gate.py` + `test_phone_gates_parity.py` (задача 1) | **468 passed** | база 449 (310 + 139); пол плана 435 |
| вторая `<automated>` задачи 1 (`t1_forms.py`) | `OK 18` | ≥ 18 |
| `-k logging_reconfiguration` (задача 2) | **15 passed** | ≥ 8 |
| acceptance задачи 2 (`t2_config.py`) | `OK` | `OK` |
| три модуля гейтов (приватность, паритет, писатель), конечное дерево | **1109 passed** | база 1074 (+19 +15 +1) |
| сверка предикатов и JS-функций с `c9da79b2` (вторая `<automated>` задачи 3) | `OK 19`, после каждого GREEN | `OK` |
| сверка прежних строк и функций с `c9da79b2` (`base_rows.py`) | `OK {'NEGATIVE_CONTROLS': 173, 'POSITIVE_CONTROLS': 61, 'NEGATIVE_CONTROL_PLACES': 14}`, 91 функция и 9 таблиц без изменений, после каждого GREEN | 173 / 61 / 14 |
| набор фазы (11 путей, третья `<automated>` задачи 3) | **1639 passed** | 1604 + 35 |
| живые деревья `-s -k "live_tree or live_trees or dynamic_construct or logging_reconfiguration_outside"` | 7 passed. Строки: «app: файлов 102, вызовов 227, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0»; «Канал запрета гейта приватности: файлов 108; находок 0»; «Перенастройка журнала вне app/logging_config.py: файлов 106; находок 0» | находок 0 |
| `tests/test_logging_config.py` + `tests/test_services/test_log_masking.py` | **90 passed** | 90 |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`, `test_logging_config`) | **593 passed** | 593 |
| `tests/test_application` | **946 passed** | 946 |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0, «реестр: 913 строк, биекция с переписью — согласие» | exit 0, 913 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | гонится после коммита сводки (заметка 5 оркестратора); итог — в финальном сообщении | 218 passed, 2 skipped |

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`:
  - ввоз `DYNAMIC_CONSTRUCT_EXCEPTIONS`, `DYNAMIC_CONSTRUCT_KINDS`, `DYNAMIC_KIND_BANNED_ROLE_STRING`, `DYNAMIC_KIND_DEFERRED_CALL`;
  - блок форм раунда 10 и трасер;
  - блок правила перенастройки журнала;
  - правило шапки;
  - тексты шапки и докстринга `ModuleLogNames`.

## Decisions Made

- **Таблица — каналом.** Строка формы судится `dynamic_construct_scan` над синтетическим `app/`, а не вызовом `dynamic_construct_findings` напрямую. Так строка проверяет обещание тем же путём, что живое дерево (решение планирования).
- **Место — строкой-маркером.** У форм с несколькими находками канала (ввоз `importlib` рядом с `importlib.import_module`, второй `methodcaller`) правило требует находку ожидаемого вида на строке, отличающей форму. Прочие находки оно не запрещает.
- **RED трасера — пустая таблица подложенных служб.** Канал уже стоит, поэтому падение утверждением возможно только так, как велит `<tdd_notes>`. В RED-коммите стоят и строки форм, все они — закрепки.
- **Абзац согласования приводит группы С1 / С2 / У таблицы 16-56 полным составом.** Список истины 6 плана — подмножество С1. Полный перечень взят, чтобы не разойтись с шапкой гейта писателя (16-55), которая ссылается на ту же таблицу.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical] Правило перенастройки журнала судит больше написаний, чем перечислено в плане**
- **Found during:** задача 2.
- **Issue:** по букве плана маску молча выключали бы `root.handlers.append(h)`, `h.filters.clear()`, `del root.handlers[0]`, `root.handlers += [h]`, `setattr(root, "propagate", False)`, ввезённый `dc = dictConfig` и `structlog.configure_once` (угроза T-16-125: снятый фильтр или свой обработчик).
- **Fix:** помощник судит и их. Контроль получил 7 строк сверх семи плановых, всего 14. На живом дереве находок 0: единственное чтение `.filters` — в `app/services/log_masking.py:290`, это чтение, а не правка.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Committed in:** `eb4154dc`.

**2. [Rule 1 — Bug в собственном правиле] Правило шапки проверяло `ModuleLogNames` только по первому вхождению фразы**
- **Found during:** задача 3, GREEN.
- **Issue:** в докстринге `ModuleLogNames` фраза «любой формой общей грамматики» стоит дважды: у `module_objects` и у `methodcallers`. Проверка первого вхождения пропустила бы второе без оговорки.
- **Fix:** правило судит каждое вхождение, у каждого в 80 знаках перед ним должна стоять пометка «До плана 16-54». Пункт `methodcallers` получил оговорку о запрете `operator.methodcaller` каналом, прежняя фраза осталась летописью. Правка ужесточает новое правило, а не ослабляет прежнее.
- **Committed in:** `b758f763`.

### Замер против плана

- **`setattr(self, "f", logger.info)` — не конструкция канала.** План (действие задачи 3) называет его «с плана 16-53 — запрещённая конструкция». Замер (`.pytest_cache/checks/t3_boundary_forms.py`): канал краснит `globals()[…]`, `vars(obj)[…]` («пространство имён»), `operator.attrgetter(…)` («отложенный вызов по имени») и `getattr(logger, name)` / `getattr(structlog.contextvars, attr)` («вычисленное имя атрибута»). `setattr` с литеральным именем, `staticmethod(logger.info)`, контейнер `fns["i"]`, `lambda` и цель `for` дают `[]`. Шапка говорит правду: первые формы запрещены, `setattr` с литералом и прочие остаются границей предиката, их ловит только маска, если вывод идёт через журнал. Общий модуль этот план не правит (заметка 0 оркестратора), см. «Для верификатора».
- **Числа.** Приватность + паритет на базе — 449 (310 + 139). План считал паритет 106, отсюда пол 435. После задачи 1 — 468.
- **Живые числа.** План ссылался на 225. Действует замер оркестратора и этого дерева: `app` 227 вызовов в 102 файлах. 102, а не 101, как в сводке 16-52: после слияния добавился `app/models/phone_guard.py` (16-51), вызовов журнала в нём нет. `scripts` — 68 в 4, `max_worker` — 93 в 2, находок 0.
- **Место оговорки «Связанное имя читается и через объект модуля».** Полная оговорка в конце пункта стояла в 922 знаках от фразы, а окно правила — 900. Рядом с фразой поставлена короткая скобка «(в двух написаниях; прочие — запрещённые конструкции канала, см. конец пункта)». Правило не расширялось.

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1 в новом правиле), 4 сверки «замер против плана». Ни одна прежняя строка, таблица, предикат, реестр или JS-функция не тронуты; `PHONE_LOG_EXCEPTIONS = {}`, потолок 0; `DYNAMIC_CONSTRUCT_EXCEPTIONS` не расширен.

### Подстановки исполнения (по требованию оркестратора)

- Проверки `python -c "…"` записаны дословно в `.pytest_cache/checks/` и исполнены `PYTHONPATH=. uv run python …` под `flock`: `precondition.py`, `t1_forms.py`, `t2_config.py`, `base_predicates.py` (вторая `<automated>` задачи 3). Логика и `assert` те же.
- Добавлены вспомогательные проверки `base_rows.py` (строки и функции `c9da79b2`), `t1_prior_predicate.py`, `t3_boundary_forms.py`, `t3_examples.py` (примеры видов в шапке) и `t3_window.py`.
- Эталон `c9da79b2` — `.pytest_cache/r10_base_privacy.py` (`git show … >`).
- Леджер `plan_head_before` — `.pytest_cache/gsd-plan-head-before-16-54`. `commits` измерен `git rev-list --count d9b38e21..HEAD` = 6.
- `graphify update .` в worktree не запускался (нет `graphify-out/`). Запросы шли к `/source/broadcaster/graphify-out/graph.json` только на чтение, граф пересоберёт оркестратор.
- Полный `just test` не запускался: его гонит пост-мердж гейт оркестратора. Сверка «база ↔ HEAD» инструментом `r9diff` в раунде 10 не обязательна (свойство 4 О-23 (а)), её заменяют обе сверки с `c9da79b2` после каждого GREEN.
- `.venv` worktree создан `uv run` (gitignored).

## Для верификатора

- **Граница, которую партия не закрывает запретом.** `setattr(self, "f", logger.info); self.f("x %s", account.phone)` не ловит ни предикат (давний пункт границы, зонд 16-29), ни канал: `setattr` с литеральным именем каналу не конструкция. Так же ведут себя `staticmethod(logger.info)`, контейнер и `lambda`. Шапка называет это прямо. Номер в выводе через `logging` / structlog закроет маска 16-52, `print` — нет. Расширить перечень видов — решение владельца по шапке канала («динамика вне перечня — повод владельцу расширить перечень»).
- **16-56:** CR-05 / WR-32 / WR-33, сторона приватности — GREEN `270ad907` (строки форм) и `b758f763` (шапка).

## Issues Encountered

None.

## Known Stubs

Нет. RED-заглушка `logging_reconfigurations` снята GREEN задачи 2 (`eb4154dc`); пустая `PLANTED_BANNED_SERVICES` — GREEN задачи 1 (`270ad907`).

## User Setup Required

None — внешних сервисов нет.

## Next Phase Readiness

- Сторона приватности партии раунда 10 исполнена: формы красны каналом, маску не выключить перенастройкой журнала, шапка правдива. Волна 4 (16-56) записывает диспозиции с хэшами выше.
- PHONE-21 в REQUIREMENTS.md этот план не отмечает: отметки ведёт оркестратор.

## Self-Check: PASSED

- Файлы на месте: `tests/test_phone_privacy_gate.py`, эта сводка.
- Коммиты на ветке worktree (`git log d9b38e21..HEAD`): `a2f3d247`, `270ad907`, `26d11d56`, `eb4154dc`, `88e18441`, `b758f763`.
- Шлюз TDD: на каждую задачу есть `test(16-54)` перед `feat(16-54)`; все три RED-улики — `RED_EVIDENCE_OK`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-23*

---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 53
subsystem: testing
tags: [ast, static-gate, privacy, single-writer, ban-channel, O-23, IN-22, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "волна 1 партии раунда 10: app/models/phone_guard.py (16-51), app/services/log_masking.py и app/logging_config.py без getattr по вычисленному имени (16-52); общий модуль tests/phone_gate_grammar.py и оба гейта номера (16-09…16-49)"
provides:
  - "tests/phone_gate_grammar.py — канал запрета: DynamicConstruct, девять видов DYNAMIC_CONSTRUCT_KINDS (константы DYNAMIC_KIND_*), BANNED_ATTRIBUTE_NAMES, dynamic_construct_findings, dynamic_construct_key, exempt_dynamic_constructs, format_dynamic_construct, реестр DYNAMIC_CONSTRUCT_EXCEPTIONS (6) и потолок DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING = 6, таблицы DYNAMIC_CONSTRUCT_CASES (76) и JUDGEABLE_TWINS (26); комментарий-шапка канала"
  - "tests/test_phone_privacy_gate.py — BANNED_GETATTR_NAMES, dynamic_construct_scan(root), правило test_no_dynamic_construct_in_the_python_trees и антивакуум по трём деревьям"
  - "tests/test_application/test_phone_single_writer_gate.py — BANNED_GETATTR_NAMES, dynamic_construct_scan(root), правило test_no_dynamic_construct_in_the_writer_trees и антивакуум по двум деревьям"
  - "tests/test_phone_gates_parity.py — трасер, правила таблиц, двойников, покрытия видов, реестра и его контроля, правило текстов канала; dynamic_construct_findings в REQUIRED_SHARED_NAMES; правдивый пункт словаря девятого круга (IN-22)"
affects: [16-54, 16-55, 16-56, "Фазы 17–20 (любая динамическая конструкция в app/ и scripts/ краснит оба гейта)"]

actuals:
  tokens: 19796   # chars/4: дифф 8fb271fb..03880243 — 79 184 знака (wc -m)
  tasks: 3
  commits: 6      # git rev-list --count 8fb271fb..HEAD до коммита сводки
plan_head_before: 8fb271fbe823538188fea364b71e213d4d266760
plan_head_after: 0388024352919cddaa82f852614c976daccfd58e

tech-stack:
  added: []
  patterns:
    - "Запрет конструкции вместо распознавания написаний: обход ast.walk с картой родителей и владельцев, вид — по имени самого узла, одна находка на узел, отдельный список находок, а не строки прежних предикатов"
    - "Имена запрещённой роли подаёт гейт (judged_names = BANNED_GETATTR_NAMES из его наборов), общий модуль гейтов не ввозит"
    - "Реестр исключений с ключом <путь>::<владелец>::<вид>, правило правдивости (файл, владелец, живая конструкция, причина) и контроль седьмой записью одним помощником"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_phone_privacy_gate.py
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_gates_parity.py

key-decisions:
  - "Вид getattr со строкой из BANNED_ATTRIBUTE_NAMES — «имя запрещённой роли строкой» у обоих гейтов, по букве истины 1; поэтому строка CR-05 `getattr(sys, \"modules\")[__name__]` несёт этот вид, а не «объект модуля»"
  - "Функции отражения узнаются именем и атрибутом `builtins` (`builtins.getattr`) — по пункту плана «и любое ast.Attribute с этими attr у builtins»; связывание имени getattr (Store) находкой не считается"
  - "Канал судит модуль-писатель наравне с прочими файлами: PHONE_WRITER_EXCEPTIONS канала не снимает (у писателя set_committed_value с литеральным ключом — находки нет)"
  - "Сверх плана — правило test_the_dynamic_construct_tables_cover_every_kind (девять видов, не меньше трёх написаний на вид, не меньше 20 двойников, уникальные id), названное в докстринге паритета"

patterns-established:
  - "Новое правило канала — в докстринге паритета (пункт канала) и в BAN_CHANNEL_RULES; иначе краснеют оба правила докстринга"

requirements-completed: [PHONE-02, PHONE-21]   # копия requirements плана; REQUIREMENTS.md этот план не трогает (заметка 5 оркестратора), отметки ведёт оркестратор

coverage:
  - id: D1
    description: "Подложенный скрипт scripts/phone_backfill_dynamic.py с getattr(sys.modules[__name__], \"lg\").info(…, account.phone) краснит оба гейта одной функцией общего модуля: ровно одна находка «объект модуля» на :8 у каждого"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_a_planted_module_object_read_reddens_both_gates"
        status: pass
    human_judgment: false
  - id: D2
    description: "Живые деревья обоих гейтов — ноль находок канала вне реестра (приватность 108 файлов, писатель 106), антивакуум подложенным import importlib в каждом дереве"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_dynamic_construct_in_the_python_trees, #test_a_planted_dynamic_construct_is_found_in_each_python_tree"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_dynamic_construct_in_the_writer_trees, #test_a_planted_dynamic_construct_is_found_in_each_writer_tree"
        status: pass
    human_judgment: false
  - id: D3
    description: "Все девять видов: 76 строк таблицы видов краснят гейты своего поля gates ожидаемым видом; 26 судимых двойников молчат у обоих гейтов; у каждого вида не меньше трёх написаний"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_every_dynamic_construct_case_is_banned_by_both_gates, #test_a_judgeable_twin_is_not_banned, #test_the_dynamic_construct_tables_cover_every_kind"
        status: pass
    human_judgment: false
  - id: D4
    description: "Реестр шести измеренных исключений с причиной под потолком 6; седьмая (устаревшая) запись краснит правило"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_dynamic_construct_exceptions_are_named_and_under_their_ceiling, #test_a_seventh_dynamic_construct_exception_reddens_the_ceiling"
        status: pass
    human_judgment: false
  - id: D5
    description: "Тексты канала правдивы: шапка канала общего модуля, пункт канала и пункт словаря девятого круга докстринга паритета без утверждения шире словаря (IN-22)"
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_the_parity_docstring_names_the_ban_channel_truthfully, #test_the_parity_docstring_names_what_it_checks"
        status: pass
    human_judgment: false
  - id: D6
    description: "Прежнее не ослаблено: строки таблиц c9da79b2 на месте (173 / 61 / 268 / 107), прежние живые правила — 0 находок, privacy 227 / 68 / 93, writer OK 6 106"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t1_rows.py (вторая команда <automated> задачи 1); -s -k \"live_tree or live_trees or dynamic_construct\"; .pytest_cache/checks/writer_live.py"
        status: pass
    human_judgment: false

duration: 33min
completed: 2026-10-23
status: complete
---

# Phase 16 Plan 53: Канал запрета динамических конструкций Summary

**В общем модуле гейтов теперь один канал запрета: `dynamic_construct_findings` обходит `ast` и краснит саму конструкцию динамического чтения или вызова по закрытому перечню из девяти видов, а не опознанные написания. Оба гейта номера судят им свои живые деревья. Шесть измеренных исключений — в реестре с причиной, потолок 6. Докстринг паритета больше не утверждает класс шире словаря (IN-22).**

## Performance

- **Duration:** 33 мин
- **Started:** 2026-10-23T09:03:07Z
- **Completed:** 2026-10-23T09:35:55Z
- **Tasks:** 3 (трасер + 2), все RED → GREEN
- **Files modified:** 4 (все — тестовые модули; продуктовый код не тронут)

## Accomplishments

- **Канал** (`tests/phone_gate_grammar.py`). `DynamicConstruct(path, line, column, kind, owner, text)`; девять видов в порядке истины 1. Константы: `DYNAMIC_KIND_MODULE_OBJECT`, `…_NAMESPACE`, `…_TEXT_EXECUTION`, `…_DEFERRED_CALL`, `…_REFLECTION_VALUE`, `…_COMPUTED_ATTRIBUTE`, `…_BANNED_ROLE_STRING`, `…_ATTRIBUTE_PROTOCOL`, `…_COMPUTED_SQL`. Метки дословно:
  - «объект модуля», «пространство имён», «исполнение текста»;
  - «отложенный вызов по имени», «отражение как значение», «вычисленное имя атрибута»;
  - «имя запрещённой роли строкой», «служебный протокол атрибутов», «вычисленный текст SQL».
- **Обход.** `ast.walk` с картой родителей и картой владельцев (квалифицированное имя ближайших `def` / `class` через точку, `<module>` на уровне модуля), одна находка на узел. Вид определяется по имени самого узла, поэтому псевдоним `sys` и имя, под которым связан результат, на находку не влияют.
- **Реестр.** `BANNED_ATTRIBUTE_NAMES` = `modules`, `import_module`, `__import__`, `__dict__`, `__globals__`, `__builtins__`, `methodcaller`, `attrgetter` и семь имён протокола. `DYNAMIC_CONSTRUCT_EXCEPTIONS` — шесть записей замера, ключи и причины дословно; `DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING = 6`.
- **Таблицы.** `DYNAMIC_CONSTRUCT_CASES` — 76 строк: объект модуля 15, имя роли строкой 11, вычисленное имя 10, SQL 9, пространство имён 8, протокол 7, отложенный вызов 6, отражение 6, исполнение текста 4. `JUDGEABLE_TWINS` — 26.
- **Оба гейта.** Каждый держит:
  - ввоз канала (`dynamic_construct_findings`, `exempt_dynamic_constructs`, `format_dynamic_construct`, `DYNAMIC_KIND_MODULE_OBJECT`);
  - `BANNED_GETATTR_NAMES` по формуле плана из своих наборов, без копии значений;
  - `dynamic_construct_scan(root)` над прежним обходом (`python_sources` / `writer_sources`);
  - правило живых деревьев и параметризованный антивакуум: подложенный `import importlib` в каждом дереве.
- **Правило-паритет.**
  - `dynamic_construct_findings` — в `REQUIRED_SHARED_NAMES`.
  - Трасер и правила таблиц, двойников, покрытия видов, реестра с контролем седьмой записью.
  - Правило текстов канала.
  - Пункт канала в «ЧТО ПРОВЕРЯЕТСЯ» и правдивый пункт словаря девятого круга (IN-22).
- **Шапка канала** в общем модуле: ЗАЧЕМ, ОБЕЩАНИЕ (свойство 1, раунд финальный), ПЕРЕЧЕНЬ видов с критерием, ПОЧЕМУ ПО ИМЕНИ КОНСТРУКЦИИ, ИСКЛЮЧЕНИЯ (ключ, потолок 6, подъём — решение владельца), ГРАНИЦА.

## Task Commits

1. **Задача 1 (трасер): подложенный скрипт с объектом модуля краснит оба гейта**
   - RED `34aa7007` — `test(16-53): add failing tracer for a planted module-object log read reddening both gates`
   - GREEN `ec3ef62e` — `feat(16-53): ban-channel module-object and deferred-call kinds shared by both gates`
2. **Задача 2: весь перечень видов, реестр шести исключений, таблица видов и двойников**
   - RED `617d2683` — `test(16-53): add failing kind table, judgeable twins and exception registry rules for the ban channel`
   - GREEN `0cae6ec4` — `feat(16-53): all nine ban-channel kinds, BANNED_ATTRIBUTE_NAMES and the six-entry exception registry`
3. **Задача 3: правдивые тексты канала (IN-22)**
   - RED `1fc363c6` — `test(16-53): add failing rule that the parity docstring and channel header name the ban channel truthfully`
   - GREEN `03880243` — `feat(16-53): truthful ban-channel header and parity docstring (IN-22)`

REFACTOR-коммитов нет. Для строки CR-05 плана 16-56 хэши GREEN: `ec3ef62e`, `0cae6ec4`, `03880243`.

## TDD: RED-улики (три совпадения + `gsd-tools check tdd-red-evidence`)

Улики лежат в `.pytest_cache/gsd-red/` (gitignored): `task{1,2,3}.xml` (JUnit), `.out` (консоль с `rc=`), `.json` (запись `{command, exitCode, targetTest, output, expected, actual, semanticAssessment}`). Классификатор на всех трёх вернул `RED_EVIDENCE_OK` / `target_test_failed`.

- **Задача 1.** Команда — `-k test_a_planted_module_object_read_reddens_both_gates`.
  - В выводе есть `FAILED tests/test_phone_gates_parity.py::test_a_planted_module_object_read_reddens_both_gates`; последняя строка — `1 failed, 32 deselected, 1 warning in 0.73s`.
  - Литерал: «подложенное чтение журнала через объект модуля не краснит правило живых деревьев обоих гейтов», фактическое значение — `{'приватности': [], 'писателя': []}`.
  - Семантика: цель исполнилась и упала на запланированном утверждении. Заглушка канала (тот же RED-коммит) возвращала `[]`; ошибки сбора не было.
  - Три модуля в RED: 6 failed (трасер и 3 + 2 параметра антивакуума), 962 passed.
- **Задача 2.** Команда — `-k test_every_dynamic_construct_case_is_banned_by_both_gates`.
  - В выводе есть `FAILED tests/test_phone_gates_parity.py::test_every_dynamic_construct_case_is_banned_by_both_gates[setattr-computed-field]` (и `[getattr-computed-log-method]` — строки вида «вычисленное имя атрибута»); последняя строка — `55 failed, 21 passed, 62 deselected, 1 warning in 2.50s` (N = 55 ≥ 21).
  - Литерал: «строка таблицы видов не краснит гейт ожидаемым видом».
  - Семантика: все 55 падений — `AssertionError` одного правила, это строки семи видов, ещё не судимых каналом.
  - Закрепки, зелёные до GREEN: 21 строка видов задачи 1 (15 + 6) и все 26 двойников, а также `test_the_dynamic_construct_tables_cover_every_kind`.
  - Вне выборки в RED падали правило реестра и его контроль: потолка ещё не было, реестр пуст. Итог трёх модулей — 57 failed, 1016 passed.
- **Задача 3.** Команда — `-k test_the_parity_docstring_names_the_ban_channel_truthfully`.
  - В выводе есть `FAILED tests/test_phone_gates_parity.py::test_the_parity_docstring_names_the_ban_channel_truthfully`; последняя строка — `1 failed, 138 deselected, 1 warning in 0.31s`.
  - Литерал: «докстринг паритета утверждает класс шире словаря или не называет канал».
  - Перечень проблем RED: прежняя фраза IN-22, нет соперников `print` / `update` и двух написаний, нет «запрещённ», у шапки нет обещания, исключений и потолка.
  - Три модуля в RED: 1 failed, 1073 passed.

## Замер: модули волны 1 и живые деревья

- **Модули волны 1** (`app/models/phone_guard.py`, `app/services/log_masking.py`, `app/logging_config.py`) — ноль находок канала, подтверждено AST-замером.
  - Слова `setattr`, `object.__setattr__`, `sys.modules`, `importlib`, `operator.methodcaller`, `text("UPDATE …")` стоят в докстрингах и комментариях, а канал их не судит.
  - `re.compile` (`log_masking.py:81, 85`) — атрибут, а не встроенная `compile`; находки нет.
  - Кортеж `(repr, str)` в `_masked_text` — не функция отражения; находки нет.
- **Сырой канал на живых деревьях** до исключений — ровно шесть находок вида «вычисленное имя атрибута», по одной у каждого владельца. Это ровно замер планирования:

| Находка | Владелец |
|---|---|
| `app/pages/accounts.py:61` `getattr(module, macro)` | `_connect_status` |
| `app/pages/common.py:615` `setattr(user, IMPERSONATOR_ATTR, actor)` | `get_user_from_cookie` |
| `app/pages/common.py:632` `getattr(user, IMPERSONATOR_ATTR, None)` | `actor_of` |
| `app/repositories/base.py:43` `setattr(entity, field, value)` | `BaseRepository.update` |
| `app/routes/schedules.py:371` `setattr(schedule, field, value)` | `update_schedule` |
| `max_worker/main.py:101` `getattr(logging, LOG_LEVEL, logging.INFO)` | `<module>` (только дерево приватности) |

- **После исключений:** гейт приватности — файлов 108, находок 0; гейт писателя — файлов 106, находок 0. Проверка реестра (acceptance задачи 2) печатает `OK {'_connect_status': 1, 'get_user_from_cookie': 1, 'actor_of': 1, 'BaseRepository.update': 1, 'update_schedule': 1, '<module>': 1}`.

## Гейты на конечном дереве (под общей блокировкой)

| Прогон | Итог | База |
|---|---|---|
| три модуля (паритет + приватность + писатель), задача 1 | **968 passed** | 960 |
| вторая `<automated>` задачи 1: прежние строки `c9da79b2` | `OK {'NEGATIVE_CONTROLS': 173, 'POSITIVE_CONTROLS': 61, 'LITERAL_FORM_CASES': 268, 'LEGITIMATE_CASES': 107}` — после каждого GREEN | те же |
| проверка тождества канала у гейтов (acceptance задачи 1) | `OK` | — |
| три модуля, задача 2 | **1073 passed** (≥ 1040) | — |
| вторая `<automated>` задачи 2 | `OK 76 26` | — |
| три модуля, задача 3 (конечное дерево) | **1074 passed** (≥ 1041) | — |
| набор фазы (11 путей с модулями волны 1) | **1604 passed** (= 1490 + 114 новых правил) | 1490 |
| живые деревья `-s -k "live_tree or live_trees or dynamic_construct"` | 10 passed. Приватность: «app: файлов 102, вызовов 227, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0». Канал: приватность — файлов 108, находок 0; писатель — файлов 106, находок 0 | 227 / 68 / 93, находок 0 |
| живое дерево писателя (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` |
| `tests/test_application` | **946 passed** | — |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`, `test_logging_config`) | **593 passed** (576 + 17 правил `test_logging_config.py`) | 576 + 17 |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0, «реестр: 913 строк, биекция с переписью — согласие» | exit 0, 913 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | — гонится после коммита сводки (заметка 5 оркестратора), итог — в финальном сообщении | 218 passed, 2 skipped |

Прибавка новых правил — 114. Задача 1 дала 8: трасер, 1 + 3 правила приватности, 1 + 2 правила писателя. Задача 2 — 105: 76 строк видов, 26 двойников, правило покрытия видов, правило реестра и его контроль. Задача 3 — 1 правило текстов.

## Files Created/Modified

- `tests/phone_gate_grammar.py` — канал запрета: типы, виды, наборы имён, обход, реестр с потолком, таблицы видов и двойников, шапка канала.
- `tests/test_phone_privacy_gate.py` — ввоз канала, `BANNED_GETATTR_NAMES`, `dynamic_construct_scan`, правило живых деревьев и антивакуум по `PYTHON_TREES`.
- `tests/test_application/test_phone_single_writer_gate.py` — ввоз канала, `BANNED_GETATTR_NAMES`, `dynamic_construct_scan`, правило живых деревьев и антивакуум по `WRITER_TREES`.
- `tests/test_phone_gates_parity.py`:
  - трасер и правила таблиц, двойников, покрытия видов, реестра с контролем, правило текстов;
  - `REQUIRED_SHARED_NAMES`;
  - пункт канала докстринга и пункт словаря девятого круга (три строки прежнего текста заменены).

## Decisions Made

- **Вид у `getattr` со строкой из `BANNED_ATTRIBUTE_NAMES`.** Это «имя запрещённой роли строкой» у обоих гейтов, по букве истины 1 («и `BANNED_ATTRIBUTE_NAMES` у обоих»). Поэтому строка CR-05 `getattr(sys, "modules")[__name__]` (`cr05-getattr-sys-modules`) ожидает этот вид. Прочие 12 написаний CR-05 и `__import__` / `importlib.util` — вид «объект модуля». Это заметка для 16-54 и 16-55: строка `ROUND_TEN_BANNED_FORMS` с `getattr(sys, "modules")` найдёт этот вид.
- **Порядок видов на одном узле** (одна находка на узел):
  1. ввоз — «объект модуля» / «пространство имён» / «отложенный вызов»;
  2. `def` протокола — «служебный протокол атрибутов»;
  3. имя или атрибут узла — объект модуля, пространство имён, исполнение текста, отложенный вызов, протокол;
  4. функция отражения не в позиции вызываемого;
  5. вызов — вычисленное имя, затем имя роли строкой, писатель по ключу, вычисленный SQL.
- **Отражение.** `builtins.getattr` (атрибут модуля `builtins`) судится как `getattr`. Цель `getattr = …` (контекст `Store`) находкой не считается.
- **Вычисленный SQL.** Первый аргумент вызова SQL берётся позиционно, иначе — по именованному из `SQL_TEXT_KEYWORDS` (`text`, `statement`, `sql`, `query`, `sql_script`). Распаковка `*args` — находка.
- **Канал судит модуль-писатель** наравне с прочими файлами (`PHONE_WRITER_EXCEPTIONS` канал не снимает). В писателе находок нет: `set_committed_value(account, "phone", e164)` — литеральный ключ.
- **Заглушка в RED задачи 1** — `dynamic_construct_findings`, возвращающая `[]`, внесённая RED-коммитом (вариант `<tdd_notes>`). Сканеры гейтов и пустой реестр с `exempt_dynamic_constructs` — там же, как обвязка правил.
- **Имена правил в RED-коммитах.** Имена новых правил вписаны в докстринг паритета уже в RED-коммитах: так прежнее правило `test_the_parity_docstring_names_what_it_checks` не краснеет, и в RED падает только цель. Полный абзац канала и правда IN-22 — в GREEN задачи 3.

## Deviations from Plan

### Отступления от буквы плана

**1. [Сверх плана] Правило `test_the_dynamic_construct_tables_cover_every_kind`**
- **Found during:** задача 2.
- **Issue:** требование «у каждого из девяти видов — не меньше трёх написаний» стояло в `<behavior>`, но ни одно правило плана его не держало: вторая `<automated>` проверяет только, что каждый вид представлен.
- **Fix:** отдельное правило-паритет — девять видов, ≥ 3 написаний на вид, ≥ 20 двойников, уникальные `id`. Оно названо в докстринге паритета и в `BAN_CHANNEL_RULES`.
- **Files modified:** `tests/test_phone_gates_parity.py`. **Committed in:** `617d2683`.

**2. [Имена, которых план не называл]**
- Правила антивакуума названы `test_a_planted_dynamic_construct_is_found_in_each_python_tree` и `test_a_planted_dynamic_construct_is_found_in_each_writer_tree`: план требовал «параметризацию по дереву», но имени не дал. Оба имени попадают под `-k dynamic_construct`.
- Контроль реестра назван `test_a_seventh_dynamic_construct_exception_reddens_the_ceiling`. Седьмая синтетическая запись в нём одновременно сверх потолка и устаревшая, поэтому контроль доказывает обе ветви помощника `_dynamic_exception_problems`.
- Помощник ключа `dynamic_construct_key` — лишнее имя общего модуля: им пользуются `exempt_dynamic_constructs` и правило реестра.

**3. [Замер против плана] Числа**
- Пол задачи 1 (968) совпал точно.
- Задача 2 дала 1073 при поле 1040: 76 строк против ≥ 50, 26 двойников против ≥ 20, плюс правило покрытия видов.
- Набор фазы — 1604. Сквозные гейты — 593: оркестратор называл 576–579 без `tests/test_logging_config.py`, а команда плана включает его (+17).

**Total deviations:** 0 auto-fixed по правилам 1–3; 1 правило сверх плана, 3 имени, не названных планом, 1 сверка чисел. Ни одна прежняя строка, матрица, реестр или предикат не тронуты; реестр не расширен, потолок не поднят.

### Подстановки исполнения (по требованию оркестратора)

- Проверки `python -c "…"` записаны дословно в файлы `.pytest_cache/checks/{t1_rows,t1_identity,t2_live,t2_registry}.py` и исполнены командой `PYTHONPATH=. uv run python …`: та же логика, те же `assert`.
- Сценарий `writer_live.py` скопирован из scratchpad оркестратора в `.pytest_cache/checks/`.
- Сводные heredoc-команды песочница отвергла. Фрагменты кода записаны в `.pytest_cache/proto/*.txt` инструментом Write и вставлены простыми сценариями `append.py` / `replace_block.py` / `insert_tables.py`.
- Таблицы видов и двойников сначала проверены прототипом канала (`.pytest_cache/proto/channel.py`, `check_tables.py`: 0 промахов, 0 ложных находок). Затем источник таблиц сгенерирован из прототипа (`gen_tables.py`), чтобы в коммит ушли ровно измеренные строки.
- Леджер `plan_head_before` лежит в `.pytest_cache/gsd-plan-head-before-16-53`; `commits` измерен `git rev-list --count 8fb271fb..HEAD` = 6.
- `graphify update .` в worktree не запускался (нет `graphify-out/`); граф пересоберёт оркестратор после слияния.
- Полный `just test` не запускался: его гонит пост-мердж гейт оркестратора. Сверка `r9diff` «база ↔ HEAD» в этом раунде не обязательна (план, `<verification>`; О-23 (а), свойство 4). Её заменяет вторая `<automated>` задачи 1 после каждого GREEN.
- `tests/test_planning` гоняется после коммита сводки (заметка 5 оркестратора).

## Для следующих волн

- **16-54 / 16-55.** Имена и метки — дословно как выше. Строки `ROUND_TEN_BANNED_FORMS` судите функцией `dynamic_construct_findings(source, path, judged_names=<гейт>.BANNED_GETATTR_NAMES)` или сканером `<гейт>.dynamic_construct_scan(root)`, сверяя вид по `DYNAMIC_KIND_*`.
- **Вид формы `getattr(<x>, "<s>")`.** При `s` из `BANNED_ATTRIBUTE_NAMES` (в том числе `"modules"`) — «имя запрещённой роли строкой». Атрибут `x.modules`, ввоз `importlib` и `__import__` — «объект модуля». `getattr(self, "f")` при `self.f = setattr` даёт «отражение как значение» на `self.f = setattr` (V10-2); сама getattr-строка `"f"` находкой не является.
- **Узлы.** Находка встаёт на узел конструкции. У трасера это атрибут `sys.modules` на строке вызова: строка совпадает, столбец — начало `sys.modules`.
- **16-56.** Хэши GREEN для строки CR-05: `ec3ef62e`, `0cae6ec4`, `03880243` (`feat(16-53): …`).

## Issues Encountered

None.

## Known Stubs

Нет. RED-заглушка `dynamic_construct_findings` снята GREEN задачи 1 (`ec3ef62e`).

## User Setup Required

None — внешних сервисов нет.

## Next Phase Readiness

- Свойство 1 О-23 (а) исполнено каналом обоих гейтов. Волна 3 (16-54, 16-55) пишет шапки гейтов и свои `ROUND_TEN_BANNED_FORMS` поверх этого канала.
- Фаза по-прежнему `gaps_found` до верификации партии раунда 10. PHONE-02 и PHONE-21 в REQUIREMENTS.md этот план не отмечает: отметки ведёт оркестратор.

## Self-Check: PASSED

- Файлы на месте: `tests/phone_gate_grammar.py`, `tests/test_phone_privacy_gate.py`, `tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_gates_parity.py`, эта сводка.
- Коммиты на ветке worktree (`git merge-base --is-ancestor`): `34aa7007`, `ec3ef62e`, `617d2683`, `0cae6ec4`, `1fc363c6`, `03880243`.
- Шлюз TDD: на каждую задачу есть `test(16-53)` перед `feat(16-53)`; все три RED-улики — `RED_EVIDENCE_OK`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-23*

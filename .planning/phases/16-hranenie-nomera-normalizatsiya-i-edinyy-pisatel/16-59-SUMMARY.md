---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 59
subsystem: testing
tags: [phone-gates, ban-channel, registry, ast, pytest, wr-38]

requires:
  - phase: 16
    provides: "канал запрета `dynamic_construct_findings` и реестр `DYNAMIC_CONSTRUCT_EXCEPTIONS` (план 16-53), правило реестра и контроль седьмой записи"
provides:
  - "`DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` — закреплённые текст и число конструкций каждой записи реестра канала"
  - "счётное исключение `exempt_dynamic_constructs`: новая конструкция того же вида у исключённого владельца и повтор закреплённой сверх числа — находки канала у обоих гейтов"
  - "правило `test_every_dynamic_construct_exception_pins_its_construct_texts`, контроль `test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule`, трасер `test_an_extra_construct_in_an_exempt_owner_is_red`; помощник `_dynamic_exception_problems(registry, ceiling, pinned=None)`"
affects: [16-62, 16-63, 16-64]

actuals:
  tokens: 7700
  tasks: 2
  commits: 4
plan_head_before: c1d726afa40ad839598e6ce24b5f04800b3c0e94
plan_head_after: 06f46a81475ca70d4e43372e0adf6761fed2c1ae

tech-stack:
  added: []
  patterns:
    - "Исключение реестра закрепляет текст и число конструкций, а не только ключ `<путь>::<владелец>::<вид>`"
    - "Мера «база ↔ HEAD» через само исключение: корпус строк на путях и владельцах реестра, ось числа и коллизии"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_phone_gates_parity.py

key-decisions:
  - "Закреплён текст (`DynamicConstruct.text`) и число: текст отличает новую конструкцию того же вида, число — повтор закреплённой; счётчик закреплённых текстов на ключ, ведётся на один вызов `exempt_dynamic_constructs`, снимаются первые по порядку находки"
  - "Счётчик — словарь списков вручную, без ввоза `collections` в общий модуль: AST-сверка определений с базой видит только `exempt_dynamic_constructs` и новую таблицу"
  - "Помощник реестра называет и ключ без закрепления («закрепления нет»), а не только лишнюю и недостающую конструкцию; прежние проверки (потолок, файл, владелец, вид, причина, «устарела») без изменений"
  - "Граница закрепления названа по замеру корпуса в шапке канала: закрепление синтаксическое — тот же текст над переприсвоенным получателем и двойник, отличный после 80-го знака (у текста длиннее 80), снимаются как закреплённые, если ЗАМЕНЯЮТ закреплённую; рядом с ней — красные"

patterns-established:
  - "Корпус исключения: строки на путях/владельцах реестра, семейства a–e, сверка числа находок база ↔ HEAD у обоих гейтов, печать OPEN_REGRESSIONS"

requirements-completed: [PHONE-02, PHONE-21]

coverage:
  - id: D1
    description: "Вторая конструкция того же вида в теле исключённого владельца (`getattr(self.session, op)(…)` или повтор `setattr(entity, field, value)` в `BaseRepository.update`) — ровно одна находка канала у обоих гейтов"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_an_extra_construct_in_an_exempt_owner_is_red"
        status: pass
    human_judgment: false
  - id: D2
    description: "Правило реестра сверяет закреплённые тексты и число в обе стороны; контроль доказывает лишнюю, недостающую и прежний исход седьмой записи"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_every_dynamic_construct_exception_pins_its_construct_texts"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule"
        status: pass
    human_judgment: false
  - id: D3
    description: "Прежнее не ослаблено: 130 строк × 2 гейта EQUAL с базой `19c99ffb`, AST определений OK, корпус исключения OPEN_REGRESSIONS=0, живые деревья 0 находок"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/r11_equal130.py (команда <verify> плана дословно) → EQUAL 130 rows x 2 gates"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/r11_astdefs.py (команда <verify> плана дословно) → OK"
        status: pass
      - kind: other
        ref: ".pytest_cache/r11diff/exempt_corpus.py → OPEN_REGRESSIONS=0, UNEXPECTED=0"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly → 1149 passed"
        status: pass
    human_judgment: false

duration: 21min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 59: закрепление текста и числа конструкций у записей реестра канала запрета — Summary

**Запись `DYNAMIC_CONSTRUCT_EXCEPTIONS` снимает теперь только закреплённые за ней конструкции (таблица `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`, текст и число, счётное `exempt_dynamic_constructs`); новая `getattr(self.session, op)(…)` или повтор `setattr(entity, field, value)` в `BaseRepository.update` — находка канала у обоих гейтов, правило реестра краснит лишнюю и недостающую конструкцию (WR-38; О-25 (а), свойство 6).**

## Performance

- **Duration:** ~21 мин
- **Started:** 2026-10-26T07:11:10Z
- **Completed:** 2026-10-26T07:32Z
- **Tasks:** 2 из 2
- **Files modified:** 2 (`tests/phone_gate_grammar.py`, `tests/test_phone_gates_parity.py`)

## Accomplishments

- `tests/phone_gate_grammar.py`: таблица `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` сразу после потолка — ключи ровно ключи реестра, по одному тексту у каждой из шести записей (замер на базе совпал со `<scope_note>` у обоих гейтов: `getattr(module, macro)`, `setattr(user, IMPERSONATOR_ATTR, actor)`, `getattr(user, IMPERSONATOR_ATTR, None)`, `setattr(entity, field, value)`, `setattr(schedule, field, value)`, `getattr(logging, LOG_LEVEL, logging.INFO)`); счётное исключение; шапка «ИСКЛЮЧЕНИЯ» с закреплением, измеренной границей и летописью WR-38; комментарий над реестром ссылается на таблицу.
- `tests/test_phone_gates_parity.py`: трасер (2 параметра), правило закрепления, контроль, помощник `_dynamic_exception_problems(registry, ceiling, pinned=None)` с чтением таблицы в момент вызова; докстринг модуля (абзац о реестре с летописью, пункт канала называет три новых правила), докстринг правила реестра, `BAN_CHANNEL_RULES` дополнен.
- Реестр, потолок 6, причины, `dynamic_construct_findings`, виды, `BANNED_*` и строки `DYNAMIC_CONSTRUCT_CASES` / `JUDGEABLE_TWINS` / `ROUND_TEN_BANNED_FORMS` не тронуты (AST-сверка — `OK`).

## Task Commits

1. **Задача 1 (трасер), RED:** `2110e925` — `test(16-59): add failing tracer for an extra construct in an exempt owner (WR-38)`
2. **Задача 1, GREEN:** `65f6f5fe` — `feat(16-59): pin construct texts and count per ban-channel exception (WR-38)`
3. **Задача 2, RED:** `817a0701` — `test(16-59): add failing control for missing or extra pinned constructs (WR-38)`
4. **Задача 2, GREEN:** `06f46a81` — `feat(16-59): registry rule checks pinned construct texts and count both ways (WR-38)`

REFACTOR-коммитов нет (правок после GREEN не было).

## TDD: RED / GREEN

**RED задачи 1.** `uv run pytest tests/test_phone_gates_parity.py -q -p no:randomly -k extra_construct_in_an_exempt_owner --junit-xml=.pytest_cache/gsd-red/t1-red.xml` — exit 1; три совпадения: `FAILED tests/test_phone_gates_parity.py::test_an_extra_construct_in_an_exempt_owner_is_red[a-new-construct-of-the-same-kind]` и `…[the-pinned-construct-repeated]`; последняя строка сводки `2 failed, 139 deselected, 1 warning in 0.86s`; литерал «конструкция в теле исключённого владельца снята реестром молча (WR-38)» — в выводе 4 раза, в JUnit XML 6. `gsd-tools check tdd-red-evidence` на записи по каждому параметру (`t1-red-new.json`, `t1-red-repeat.json`) — `RED_EVIDENCE_OK`. Семантика: оба параметра исполнились и упали на плановом утверждении — `dynamic_construct_scan` обоих гейтов вернул `{'приватности': [], 'писателя': []}` (ключ снимал все конструкции вида); сбоев сбора, ввоза, фикстур нет; остальные 139 правил паритета зелёные.

**GREEN задачи 1.** Таблица и счётное исключение; трасер 2/2, правило живых деревьев обоих гейтов — 0 находок.

**RED задачи 2.** `uv run pytest tests/test_phone_gates_parity.py -q -p no:randomly -k missing_or_extra_pinned_construct --junit-xml=.pytest_cache/gsd-red/t2-red.xml` — exit 1; `FAILED tests/test_phone_gates_parity.py::test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule`; последняя строка `1 failed, 142 deselected, 1 warning in 0.63s`; литерал «закрепление реестра не краснит лишнюю и недостающую конструкцию (WR-38)» — 2 раза. Классификатор — `RED_EVIDENCE_OK` (`t2-red.json`). Семантика: контроль упал на первом (плановом) утверждении — помощник с подменённой таблицей вернул `[]`, он таблицу ещё не читал; правило закрепления на RED зелёное (по ключам), остальные 142 правила зелёные.

**GREEN задачи 2.** Сверка в помощнике; параметр `pinned`; шапка и докстринги.

Улики — gitignored `.pytest_cache/gsd-red/` (`t1-red.{txt,xml,json}`, `t1-red-new.json`, `t1-red-repeat.json`, `t2-red.{txt,xml,json}`).

## Сверка «база ↔ HEAD»

| Мера | Итог |
|------|------|
| 130 строк плана (`DYNAMIC_CONSTRUCT_CASES`, `JUDGEABLE_TWINS`, `ROUND_TEN_BANNED_FORMS` обоих гейтов) × 2 гейта | `EQUAL 130 rows x 2 gates` |
| AST определений общего модуля против `19c99ffb` | `OK` (изменено только `exempt_dynamic_constructs`, добавлено `=DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`) |
| Корпус исключения (заметка оркестратора 9), 130 строк × 2 гейта = 260 ячеек | `OPEN_REGRESSIONS=0`, `UNEXPECTED=0`, расхождения только в семействах b, c, e |

Корпус `.pytest_cache/r11diff/exempt_corpus.py` (в рабочем дереве, не закоммичен): строки посажены НА пути и владельцев реестра (исходники шести владельцев — `git show 19c99ffb:<путь>`), каждая сверяется по числу находок после исключения между копией базы `.pytest_cache/r11_base_grammar.py` и HEAD для имён обоих гейтов; у каждой строки ожидаемые числа базы и HEAD.

| Семейство | Строк | Ячеек | база ≠ HEAD | Ожидание и итог |
|-----------|-------|-------|-------------|-----------------|
| a — живые файлы шести владельцев | 6 | 12 | 0 | 0 и 0 |
| b — лишняя конструкция того же вида с другим текстом (`getattr(planted_receiver, planted_name)`, `setattr(…, …, …)`) у каждого владельца | 12 | 24 | 24 | база 0, HEAD 1 |
| c — закреплённая повторена: второй строкой (HEAD 1), дважды в одной строке (HEAD 2), владелец определён дважды в том же файле — тот же квалифицированный владелец (HEAD 1) | 18 | 36 | 36 | база 0, HEAD как указано |
| d — коллизии: закреплённый текст у другого владельца того же файла; тот же квалифицированный владелец на другом пути (`<дерево>/x.py`, `<путь>_copy.py`); вложенная `def` с последним именем владельца; верхняя `def` с последним именем у `BaseRepository.update`; другой вид в теле владельца (`vars(…)`); синтетическая находка с путём, владельцем и закреплённым текстом, но другим видом (8 видов × 6) | 78 | 156 | 0 | база = HEAD = 1 |
| e — граница текста: двойник иного написания с тем же `unparse` рядом с закреплённой (HEAD 1); тот же текст над переприсвоенным получателем (`<получатель> = planted_rebound_object` перед строкой) — **граница**, HEAD 0; синтетическая длинная запись (реестры обоих модулей подменены в памяти, закреплены первые 80 знаков): оригинал один — 0/0, двойник рядом — 0/1, двойник ВМЕСТО оригинала — **граница**, 0/0, без подмены — 1/1 | 16 | 32 | 14 | как указано |
| **Итого** | **130** | **260** | **74** | `OPEN_REGRESSIONS=0` |

Измеренная граница текстового закрепления (названа в шапке «ИСКЛЮЧЕНИЯ»): закрепление синтаксическое — конструкция, которая ЗАМЕНЯЕТ закреплённую и совпадает с ней по `DynamicConstruct.text`, снимается как закреплённая: (1) тот же текст над переприсвоенным получателем (12 ячеек `same-text-rebound-receiver-replaces-meaning` — 0/0), (2) у текста длиннее 80 знаков — двойник, отличный после 80-го знака (2 ячейки `long-pin::twin-replaces-original` — 0/0). Рядом с закреплённой любой такой двойник — сверх числа и красен. Все шесть закреплённых текстов короче 80 знаков и однострочны, так что граница (2) у живых записей сегодня недостижима; граница по второй строке `ast.unparse` следует из построения `_construct_text` и корпусом не замерена (у шести текстов `unparse` однострочен).

## Проверки — счёт рядом с базой

| Проверка | База (оркестратор, 06:58–07:06Z) | Итог плана |
|----------|-----------------------------------|------------|
| `tests/test_phone_gates_parity.py` | 139 | 143 (+ трасер 2, правило, контроль) |
| паритет + оба гейта (`<verify>` задачи 2, порог ≥ 1149) | 139 + 345 + 661 = 1145 | 1149 passed (79 с) |
| живые строки (`-s -k "live_tree or live_trees or dynamic_construct_in_the"`) | 5 passed; канал приватности 108 / 0, канал писателя 106 / 0, Python-половина 102/227, 4/68, 2/93 — 0, JS 1/68 — 0 | 5 passed; те же строки дословно |
| писатель вживую (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` |
| сквозные гейты | 576 | 576 passed (156 с) |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строки, биекция | exit 0, 934 строки, биекция |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `tests/test_planning` | 218 passed, 2 skipped | прогон после коммита SUMMARY (заметка 5) — итог в финальном сообщении исполнителя |

## Decisions Made

- Закреплены текст и число, а не одно число: текст отличает новую конструкцию того же вида, число — повтор.
- Отдельная таблица, а не смена типа реестра: шапки и правила обоих гейтов читают `DYNAMIC_CONSTRUCT_EXCEPTIONS` прежним `dict[str, str]`.
- Счётчик — словарь списков, без нового ввоза в общий модуль.
- Ключ без закрепления — проблема помощника (седьмая синтетическая запись теперь даёт и «закрепления нет», прежние «выше потолка» и «устарела» сохранены).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Новые правила названы в докстринге модуля и в `BAN_CHANNEL_RULES` уже в RED-коммитах**
- **Found during:** задачи 1 и 2 (RED)
- **Issue:** `test_the_parity_docstring_names_what_it_checks` требует, чтобы докстринг называл каждое правило `test_*` модуля; без этого RED краснел бы ещё и чужим правилом, и улика перестала бы быть чистой.
- **Fix:** пункт канала докстринга и `BAN_CHANNEL_RULES` называют трасер (`2110e925`), правило закрепления и контроль (`817a0701`); абзац о реестре с летописью — в GREEN `06f46a81`.
- **Verification:** на каждом RED красна только цель (139 / 142 прочих правил паритета зелёные).

**2. [Rule 2 - Missing Critical] Граница закрепления и корпус исключения (заметка оркестратора 9)**
- **Found during:** задача 2
- **Issue:** 130 строк плана сажаются на `app/x.py` / `scripts/x.py`, путь без ключа реестра, — мера по построению не видит исключение.
- **Fix:** добавлен корпус исключения (130 строк × 2 гейта на путях и владельцах реестра, семейства a–e); измеренная граница текстового закрепления названа в шапке «ИСКЛЮЧЕНИЯ».
- **Files modified:** `tests/phone_gate_grammar.py` (комментарий); корпус — gitignored `.pytest_cache/r11diff/exempt_corpus.py`.
- **Verification:** `OPEN_REGRESSIONS=0`, `UNEXPECTED=0`.

**3. [Уточнение] Трасер идёт через правило живых деревьев гейтов**
- Трасер кладёт подложенный `app/repositories/base.py` в `tmp_path` и зовёт `dynamic_construct_scan` каждого гейта — это и есть `dynamic_construct_findings` + `exempt_dynamic_constructs` с именами гейта (план называет эти две функции); так трасер проверяет и путь гейта. Утверждение: ровно одна находка на подложенной строке, вид «вычисленное имя атрибута», текст начинается ожидаемым.

### Замены команд (среда песочницы, заметки оркестратора 3–5)

- `<automated>` / acceptance `python -c` записаны дословно в `.pytest_cache/checks/` (`t1_accept.py`, `r11_equal130.py`, `r11_astdefs.py`) и запущены с `PYTHONPATH=.`; логика и утверждения те же.
- Полная суита (`just test`) не запускалась — её гоняет пост-мердж гейт оркестратора.
- `graphify update .` в рабочем дереве не запускался — его запускает оркестратор после слияния.
- `uv run pytest tests/test_planning -q -p no:randomly` — после коммита SUMMARY (заметка 5), а не внутри задачи 2.
- Все прогоны pytest и тяжёлых скриптов — под общим `flock`.

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical) + 1 уточнение. **Impact:** вне `files_modified` ничего не правилось; реестр, потолок, причины и строки таблиц прежние.

## Issues Encountered

- `gsd-tools check tdd-red-evidence` с целью без параметра ответил `INVALID_RED (no_target_test_failure)`: у параметризованного правила классификатору нужно точное имя с параметром. Записи переписаны по параметру — обе `RED_EVIDENCE_OK`.
- Первая длинная синтетическая конструкция корпуса была ровно 80 знаков — утверждение корпуса это поймало, имя удлинено.

## Known Stubs

Нет.

## Threat Flags

Нет: правка — только тестовые модули; T-16-136 смягчён (закреплённые текст и число, правило в обе стороны, трасер, обе меры «база ↔ HEAD»).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Планы 16-62 и 16-63 (волна 3) могут называть `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` и правила `test_an_extra_construct_in_an_exempt_owner_is_red`, `test_every_dynamic_construct_exception_pins_its_construct_texts`, `test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule` в шапках гейтов; 16-64 записывает GREEN-коммиты `65f6f5fe` и `06f46a81` для WR-38.
- После слияния волны 1 живые каналы должны читать 0 (писатель 106, приватность 108): закреплённая таблица не зависит от правок 16-57 / 16-58 (ни `app/worker/celery_app.py`, ни `app/models/phone_guard.py` не владельцы реестра).
- Корпус для ревьюера и верификатора — `.pytest_cache/r11diff/exempt_corpus.py` в этом рабочем дереве.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

## Self-Check: PASSED

- FOUND: tests/phone_gate_grammar.py, tests/test_phone_gates_parity.py, .pytest_cache/r11diff/exempt_corpus.py
- FOUND (предки HEAD): 2110e925, 65f6f5fe, 817a0701, 06f46a81

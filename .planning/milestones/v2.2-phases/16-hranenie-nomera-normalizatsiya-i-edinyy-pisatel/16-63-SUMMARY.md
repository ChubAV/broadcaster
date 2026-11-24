---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 63
subsystem: testing
tags: [phone-privacy, log-masking, celery, gate-header, chronicles, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "получатель `setup_celery_logging` и правила `tests/test_worker/test_celery_log_mask.py` (16-57); `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` (16-59); таблицы `PROCESSES_WITHOUT_SETUP_LOGGING`, `MASK_BOUNDARY_CHARACTERS`, `MASK_BOUNDARY_SUBSTRINGS`, `MASK_JUDGMENT_BUDGET` и помощник `_boundary_names` (16-60)"
provides:
  - "правило `test_the_privacy_gate_header_names_the_measured_mask_boundary` и константа `MASK_BOUNDARY_TABLES_MODULE = \"tests.test_services.test_log_masking\"`"
  - "пункт «Защита на исполнении» шапки приватности по замеру: где стоит (веб, Celery, `beat`, пул prefork), граница маски (все процессы, знаки и 11 строк таблиц 16-60), стоимость (`MASK_JUDGMENT_BUDGET` (64), отказ в закрытую), держатели «только маски» по процессам"
  - "летописи CR-06, WR-39, CR-07; «второй / единственный рубеж» по процессам; «Исключения» с закреплением `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`"
affects: [16-64]

actuals:
  tokens: 4881
  tasks: 2
  commits: 4
plan_head_before: 05ba9334c07062f69c77a823d19c8ef214a8902b
plan_head_after: fb80ea82d571a5147dc7fb3ec615559a2961c45b

tech-stack:
  added: []
  patterns:
    - "Шапка гейта сверяется с таблицами модуля, который владеет фактом (ввоз в момент вызова), а не с перечнем в правиле: строка, добавленная в таблицу маски, краснит шапку приватности"
    - "Пункт шапки делится на части маркерами («Где стоит маска», «Граница маски», «Стоимость маски»), и каждая часть сверяется отдельно — имя, сказанное не в той части, не засчитывается"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Строку `MASK_BOUNDARY_SUBSTRINGS` правило узнаёт помощником 16-60 `_boundary_names` (текст строки, `U+XXXX` её знака или знак в обратных кавычках) — то же узнавание, что у правила шапки маски, а не своё"
  - "Знак ASCII из `MASK_BOUNDARY_CHARACTERS` засчитывается только в обратных кавычках или кодом `U+XXXX`: голая `.` или `/` нашлась бы в любом тексте, и проверка была бы вакуумной"
  - "Знак свёртки (`_FOLDED_SEPARATORS`), названный в части «Граница маски», краснит: маска его сворачивает, граница о нём лгала бы"
  - "Летописи плана стоят внутри раздела запрета, перед пунктом «Статический гейт»; правило шапки обрезает их абзацы там, потому что `_chronicle_segment` (AST-неприкосновенна) дотянула бы последнюю летопись до конца шапки"
  - "Пункт «ГРАНИЦЫ СРЕДСТВА» о держателях «только маски» дописан, а не переписан: прежняя фраза цела, к ней добавлено, в каких процессах её держит маска и где — ничто"

patterns-established:
  - "Правило сверки шапки с таблицами доказывается двумя зондами: мутация шапки (8 мутаций — 8 красных) и расширение таблицы в памяти (новый процесс и новый знак — красные)"

requirements-completed: [PHONE-21]  # скопировано из плана; `requirements.mark-complete` не запускался (указание оркестратора 5)

coverage:
  - id: D1
    description: "Пункт «Защита на исполнении» шапки приватности называет, где маска стоит (веб, воркеры Celery, `beat`, пул prefork; `celery.signals.setup_logging`, `tests/test_worker/test_celery_log_mask.py`) и где её нет (каждый процесс `PROCESSES_WITHOUT_SETUP_LOGGING`, каждый знак `MASK_BOUNDARY_CHARACTERS`, каждая из 11 строк `MASK_BOUNDARY_SUBSTRINGS`, в том числе U+202F, U+2009, `8)999)123)45)67`, `(999123) 45 67`), стоимость (`MASK_JUDGMENT_BUDGET` (64), отказ в закрытую) и держателей по процессам — сверено правилом с таблицами модулей маски"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_measured_mask_boundary"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_mutation_probe.py (8 мутаций шапки — 8 RED, без мутаций — GREEN; PROBE_OK)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_table_probe.py (процесс и знак, добавленные в таблицы, — RED)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Летописи CR-06, WR-39, CR-07 называют прежнее с причиной; «второй рубеж» — в процессах с `setup_logging`, «единственный рубеж» — без неё; «Исключения» называют закрепление `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask"
        status: pass
    human_judgment: false
  - id: D3
    description: "Прежнее не ослаблено: AST определений модуля против `05ba9334` и `19c99ffb` — изменено только правило шапки, добавлены правило сверки и константа; оба гейта и паритет 1 150; живые строки прежние"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/astdefs_plan.py (команда <verify> плана дословно, база 19c99ffb) → OK 179 definitions"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/astdefs_base.py 05ba9334 → OK"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py -q -p no:randomly → 1150 passed"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 63: Шапка гейта приватности о маске — по замеру Summary

**Пункт «Защита на исполнении» шапки `tests/test_phone_privacy_gate.py` называет по замеру, где маска стоит (веб, воркеры Celery, `beat`, пул prefork) и где её нет (пять процессов, девять знаков и 11 строк таблиц 16-60, включая U+202F, U+2009, `8)999)123)45)67`, `(999123) 45 67`), её стоимость (`MASK_JUDGMENT_BUDGET` (64), отказ в закрытую) и держателей «только маски» по процессам. Новое правило сверяет пункт с таблицами модулей маски, которые ввозит в момент вызова; прежняя граница перешла в летописи CR-06, WR-39, CR-07.**

## Performance

- **Duration:** ~17 мин
- **Started:** 2026-10-26T11:26:54Z
- **Completed:** 2026-10-26T11:43:53Z
- **Tasks:** 2 (RED→GREEN каждой)
- **Files modified:** 1 (`tests/test_phone_privacy_gate.py`, +182 / −12)

## Accomplishments

- **CR-06, WR-39, CR-07 в шапке приватности (О-25 (а), свойства 1–3, 5; О-26 (а)).** Пункт «Защита на исполнении» разделён на четыре части.
  - «Где стоит маска»: веб-процесс; воркеры Celery, `celery beat` и дочерние процессы пула prefork — через получатель `setup_celery_logging` сигнала `celery.signals.setup_logging` (план 16-57) и правила `tests/test_worker/test_celery_log_mask.py`; свёрнутые знаки (план 16-60).
  - «Граница маски»:
    - `print` и `sys.stdout`, в том числе в Celery;
    - поздние обработчики;
    - `PROCESSES_WITHOUT_SETUP_LOGGING`: `scripts/`, Alembic, `celery flower`, `max_worker`, `wa_worker`;
    - знаки и строки `MASK_BOUNDARY_SUBSTRINGS`;
    - обе формы с началом вне грамматики.
  - «Стоимость маски»: 7…15 цифр, бюджет `MASK_JUDGMENT_BUDGET` (64), отказ в закрытую, путь из 1 801 знака стоит 5–8 мс.
  - Держатели «только маски» сказаны по процессам.
- **Правило сверки** `test_the_privacy_gate_header_names_the_measured_mask_boundary` ввозит `MASK_BOUNDARY_TABLES_MODULE` в момент вызова. Оно требует в части «Граница маски» каждое имя процесса, каждый знак и каждую строку таблиц, а в части «Где стоит» — Celery, `beat` и `prefork`. Знак свёртки в границе краснит. Три правила Celery обязаны существовать.
- **Летописи (D-30, D-32).**
  - CR-06: прежняя граница маски пересказана дословно; маску в воркерах снимал Celery (`553933d8`, истины 28, 131, 159, 180).
  - WR-39: до 16-60 краем назван только `+7.999.123.45.67`; NBSP U+00A0, U+2011 и полноширинные цифры маска не маскировала.
  - CR-07: кубическая стоимость `535c4f20` — 2,45 с.
- «Статический гейт» — второй рубеж в процессах с `setup_logging` и единственный рубеж без неё. «Исключения» называют закрепление `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` (16-59, WR-38).
- В «ГРАНИЦЕ СРЕДСТВА» к фразе о держателях дописано, где их держит маска и где не держит ничто; прежняя фраза цела.

## Task Commits

1. **Задача 1 (трасер): пункт «Защита на исполнении» сверен с таблицами маски**
   - RED — `1887f5c7` (`test(16-63): add failing rule reconciling the privacy header's mask boundary with the mask tables`)
   - GREEN — `45bd5667` (`feat(16-63): name where the log mask stands and where it does not in the privacy header (CR-06, WR-39, CR-07)`)
2. **Задача 2: летописи, рубеж по процессам, закрепление реестра**
   - RED — `03e13ab7` (`test(16-63): require the CR-06, WR-39, CR-07 chronicles and the pinned registry in the privacy header`)
   - GREEN — `fb80ea82` (`feat(16-63): chronicle CR-06, WR-39, CR-07 and say the static gate's line of defence per process`)

REFACTOR не понадобился. Для 16-64 (CR-06 / CR-07 / WR-39, шапка приватности): GREEN `45bd5667` и `fb80ea82`.

## TDD Gate Compliance

Улики лежат в gitignored `.pytest_cache/gsd-red/`: `t1-red.{txt,xml,json}`, `t2-red.{txt,xml,json}`. Классификатор `check tdd-red-evidence` дал `RED_EVIDENCE_OK` (`target_test_failed`, tests 1, fail 1) обеим.

| RED | Цель | Три совпадения | Семантика |
|-----|------|----------------|-----------|
| `1887f5c7` | `test_the_privacy_gate_header_names_the_measured_mask_boundary` | строка `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_measured_mask_boundary`; последняя строка сводки `1 failed, 345 deselected, 1 warning in 0.70s`; литерал «шапка приватности называет границу маски не по замеру её модулей» — в выводе 2 раза, в XML 3 раза | Правило исполнилось и упало на плановом утверждении. Не названы Celery, `beat`, `prefork`, Alembic, `flower`, девять знаков, десять из 11 строк, стоимость и держатели. Названные на базе `print`, `max_worker`, `wa_worker`, `scripts/` и `+7.999.123.45.67` в перечень не попали. Ввоз таблиц прошёл. Весь модуль: `1 failed, 345 passed`. |
| `03e13ab7` | `test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask` | строка `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask`; последняя строка `1 failed, 345 deselected, 1 warning in 0.65s`; литерал «шапка гейта приватности не называет запрет динамики и защиту на исполнении» — в выводе 2 раза, в XML 3 раза | Правило упало ровно на пяти новых требованиях: `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`, «единственный рубеж» и три летописи. `celery.signals.setup_logging` уже назван GREEN задачи 1. Прежние проверки правила зелёные. |

Цепочка: каждый `test(16-63)` стоит перед своим `feat(16-63)`. Номер в выводе прогонов: `grep -c 9991234567` — 0.

Трасер (задача 1): `auto_advance=false`, `human_verify_mode=end-of-phase`, а в `<verify>` только `<automated>`. Поэтому `<verify>` перегнан (`2 passed`), и задача 2 начата без чекпойнта.

## Сверка определений с базой (заметка оркестратора 9)

Сравнивались AST всех `FunctionDef` / `AsyncFunctionDef` / `ClassDef` любой глубины, присваиваний уровня модуля и ввозов, без докстрингов:

| База | Определений | Изменено | Снято | Добавлено | Итог |
|------|-------------|----------|-------|-----------|------|
| `05ba9334` (`astdefs_base.py`) | 181 → 183 | `test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask` | — | `=MASK_BOUNDARY_TABLES_MODULE`, `test_the_privacy_gate_header_names_the_measured_mask_boundary` | `OK` |
| `19c99ffb` (`astdefs_base.py`) | 181 → 183 | то же | — | то же | `OK` |
| `19c99ffb` (команда `<verify>` плана дословно, `astdefs_plan.py`) | 179 | то же | — | то же | `OK 179 definitions` |

Без изменений остались:
- предикаты распознавания и канал;
- `NEGATIVE_CONTROLS`, `POSITIVE_CONTROLS`, `NEGATIVE_CONTROL_PLACES`, `ROUND_TEN_BANNED_FORMS`, `LOGGING_RECONFIGURATION_CONTROLS`;
- `js_log_offences` и вся JS-половина;
- `_chronicle_segment`;
- `PHONE_LOG_EXCEPTIONS = {}` и `PHONE_LOG_EXCEPTIONS_CEILING = 0`.

`tests/phone_gate_grammar.py`, `tests/test_services/test_log_masking.py`, `app/`, паритет и гейт писателя не тронуты: `git diff --stat 05ba9334 HEAD` показывает один файл.

## Проверки на итоговом дереве (`fb80ea82`), рядом с базой оркестратора `05ba9334`

| Проверка | База | HEAD |
|----------|------|------|
| `tests/test_phone_privacy_gate.py` | 345 | 346 (+1 правило плана) |
| гейт приватности + гейт писателя + паритет | 345 + 661 + 143 = 1 149 | 1 150 passed (79 с) |
| Python-половина, живая строка | «app: файлов 102, вызовов 227, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | дословно та же |
| канал запрета приватности | файлов 108; находок 0 | файлов 108; находок 0 |
| JS-половина | wa_worker: файлов 1, вызовов 68; находок 0 | то же |
| канал запрета писателя | файлов 106; находок 0 | файлов 106; находок 0 |
| перенастройка журнала вне `app/logging_config.py` | файлов 106; находок 0 | файлов 106; находок 0 |
| живые правила (`-s -k "live_tree or live_trees or dynamic_construct_in_the or logging_reconfiguration"`) | — | 20 passed |
| сквозные гейты (htmx pairs/gates, templates, declared invariants) | 576 | 576 passed (165 с) |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строк | exit 0, «реестр: 934 строк, биекция с переписью — согласие» |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `python -m compileall -q app main.py tests` | exit 0 | exit 0 |
| `tests/test_planning` | 218 passed, 2 skipped | прогон после коммита этой сводки (заметка 5), итог — в финальном сообщении исполнителя |

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`:
  - шапка: пункт «Защита на исполнении», летописи CR-06 / WR-39 / CR-07, «Исключения», «Статический гейт», фраза о держателях в «ГРАНИЦЕ СРЕДСТВА»;
  - правило `test_the_privacy_gate_header_names_the_measured_mask_boundary` и константа `MASK_BOUNDARY_TABLES_MODULE`;
  - правка правила `test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask`: новые имена раздела, три летописи, обрезка их абзацев перед «Статический гейт» и докстринг.

## Decisions Made

См. `key-decisions`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Правило сверки строже буквы `<behavior>`**
- **Found during:** задача 1 (RED).
- **Issue:** буквальная проверка «знак ASCII — буквально» вакуумна: `.` и `/` есть в любом тексте. Перечень «U+202F и U+2009» из плана называл не все строки таблицы.
- **Fix:**
  - знак ASCII засчитывается только в обратных кавычках или кодом `U+XXXX`;
  - каждая строка `MASK_BOUNDARY_SUBSTRINGS` узнаётся помощником 16-60 `_boundary_names`;
  - знак свёртки `_FOLDED_SEPARATORS` в границе краснит (решение планирования: «знаки свёртки — нет как граница»);
  - значение бюджета берётся из таблицы — `({MASK_JUDGMENT_BUDGET})`;
  - три правила Celery обязаны существовать в `tests/test_worker/test_celery_log_mask.py`;
  - держатели требуются словами `staticmethod`, `lambda`, «ничто».
- **Verification:** мутационный зонд (8 мутаций шапки — 8 RED, без мутаций GREEN, `PROBE_OK`). Зонд таблиц: процесс `celery events` и знак U+2024, добавленные в память, краснят.
- **Committed in:** `1887f5c7`.

**2. [Rule 2 - Missing critical] Абзацы новых летописей обрезаны перед «Статический гейт»; два лишних литерала**
- **Found during:** задача 2 (RED).
- **Issue:** `_chronicle_segment` кончает абзац на следующей «Летописи», «РЕЕСТР ИСКЛЮЧЕНИЙ» или «ЧТО КРАСНИТ», а после летописи CR-07 их нет. Её абзац тянулся бы до конца шапки, и литералы находились бы где угодно. Саму функцию менять нельзя: AST-сверка.
- **Fix:** правило шапки делает `.split("Статический гейт", 1)[0]` над абзацем. Литералы сверх плана: `+7.999.123.45.67` у WR-39 и «2,45 с» у CR-07.
- **Committed in:** `03e13ab7`.

**3. [Замер против плана] Строк `MASK_BOUNDARY_SUBSTRINGS` — 11, и две из них — формы, которых план не предвидел**
- **Issue:** план ждал от 16-60 «ид строк с U+202F и U+2009». Замер: 11 строк.
  - `full-stop-split`, `asterisk-split`, `solidus-split`, `square-bracket-split`, `fullwidth-full-stop-split`;
  - `narrow-nbsp-split`, `thin-space-split`;
  - `number-after-a-letter`, `plus-after-a-letter`;
  - `eight-before-closing-bracket`, `six-digit-bracket-start`.
  
  Последние две — граница, названная исполнением 16-60.
- **Resolution:** граница маски называет все 11 строк, правило читает таблицу целиком. `PROCESSES_WITHOUT_SETUP_LOGGING` (`scripts/`, `Alembic`, `max_worker`, `flower`, `wa_worker`), `MASK_BOUNDARY_CHARACTERS` (девять знаков) и `MASK_JUDGMENT_BUDGET` (64) совпали с ожиданием плана.

**4. [Rule 2 - Missing critical] Пункт «ГРАНИЦЫ СРЕДСТВА» о держателях**
- **Issue:** фраза «их ловит только маска на исполнении, если вывод идёт через журнал» оставалась без процессов (истина 2 плана, гэп 1 — истина 159).
- **Fix:** дописано, без удаления прежнего: в процессах с `setup_logging` их держит маска, в процессах без неё — ничто.
- **Committed in:** `45bd5667`.

**5. [Уточнение] База AST-сверки**
- План сверяет с `19c99ffb`, оркестратор — с `05ba9334`. Прогнаны обе, обе дали `OK`: модуль на них совпадает по определениям.

---

**Total deviations:** 3 auto-fixed (Rule 2), 1 «замер против плана», 1 уточнение. Утверждения не удалены и не ослаблены, предикаты не тронуты.
**Impact on plan:** вне `files_modified` ничего не правилось.

## Подстановки исполнения

- Команда `<automated>` с AST-сверкой (`python -c` с `git` внутри) записана дословно в `.pytest_cache/checks/astdefs_plan.py` и запущена файлом. Расширенная сверка с печатью списков — `.pytest_cache/checks/astdefs_base.py <база>`.
- Зонды с `python -c` под `flock` песочница отказала. Они записаны в `.pytest_cache/checks/t1_table_probe.py` и `t1_mutation_probe.py` и запущены с `PYTHONPATH=.`.
- `tests/test_planning` из `<verify>` задачи 2 перенесён в самый конец, после коммита сводки (заметка 5).
- Полный `just test` не запускался: его гоняет пост-мердж гейт оркестратора (заметка 4). Вместо него прогнаны оба гейта, паритет, живые строки, сквозные гейты, перепись и `compileall`.
- `graphify update .` в рабочем дереве не запускался, его запускает оркестратор после слияния. Ориентация — `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- Помощника `writer_live.py` («OK 6 106 offences 0») в этом дереве нет. Живая строка писателя взята из его собственного правила: «Канал запрета гейта писателя: файлов 106; находок 0». Гейт писателя в прогоне 1 150 зелёный, файл не тронут.
- Реестр «разбитых окон» (`windows append`) не пополнялся: единственная запись в `.planning/` — эта сводка (заметка 5). Заглушек, пропущенных тестов и непрогнанных `<verify>` нет.

## Deferred / наблюдения

- **Шапка модуля маски называет «22 разделителя», а таблица `_FOLDED_SEPARATORS` держит 18 (и плюс U+FF0B).** Источник — `app/services/log_masking.py`, абзац «СВЁРТКА»; то же число стоит в сводке 16-60 (D2). Замер `.pytest_cache/checks/fold_count.py`: `entries 19 separators 18 plus ['U+FF0B']`; перечень шапки — те же 18 кодов. Файл не мой (заметка 0), поэтому не правился. Шапка приватности числа не называет и ссылается на таблицу. Адресат — 16-64 (диспозиция) или ревью.
- `deferred-items.md` не создавался.

## Threat Model

T-16-146 (шапка называет границу маски по замыслу) — mitigate исполнено. Правило сверяет шапку с таблицами модулей маски и с правилами Celery. Летописи называют прежнее с причиной, «второй / единственный рубеж» сказан по процессам. Новой поверхности нет: правится только тестовый модуль.

## Known Stubs

Нет.

## Issues Encountered

Нет.

## User Setup Required

None — внешней настройки нет.

## Next Phase Readiness

- 16-64 получает GREEN-коммиты `45bd5667` и `fb80ea82` (темы `feat(16-63): …` дословно выше) для заголовков CR-06 / CR-07 / WR-39 и наблюдение о «22 разделителях».
- Правило сверки читает таблицы 16-60 при вызове. Новая строка границы маски или новый процесс без `setup_logging` в `tests/test_services/test_log_masking.py` краснит шапку приватности, пока её не назовут.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

## Self-Check: PASSED

- FOUND: `tests/test_phone_privacy_gate.py`, `.pytest_cache/gsd-red/t1-red.json`, `.pytest_cache/gsd-red/t2-red.json`
- FOUND (предки HEAD): `1887f5c7`, `45bd5667`, `03e13ab7`, `fb80ea82`; удалений файлов в коммитах нет
- Счёт `commits: 4` измерен `git rev-list --count 05ba9334..HEAD` до коммита сводки

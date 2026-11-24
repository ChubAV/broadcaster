---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 04
subsystem: testing
tags: [privacy, pii, logging, ast, tokenizer, cross-cutting-gate, structlog, pino]

requires: []
provides:
  - "tests/test_phone_privacy_gate.py — сквозной гейт PHONE-21: номер не попадает в вызовы журнала app/, scripts/, max_worker/ (ast) и wa_worker/ (собственный токенизатор JS)"
  - "GATE_TREES, PYTHON_TREES, JS_TREES; python_sources(root), js_sources(root), python_log_calls, python_log_offences(source, path), js_log_calls, js_log_offences(source, path), phone_like, PHONE_LIKE_LITERAL, scan_gate(root)"
  - "PHONE_LOG_EXCEPTIONS (пуст) и PHONE_LOG_EXCEPTIONS_CEILING = 0, _ceiling_offence(registry, ceiling)"
affects: [phase-17, phase-18, phase-19, phase-20]

actuals:
  tokens: 10476
  tasks: 2
  commits: 4
plan_head_before: 1a0c1bb5e17a77e9b41b22f3d2d985d70b019f6d
plan_head_after: 27e79d277dca91a9a0a3c8961a99aeab4e62a86c

tech-stack:
  added: []
  patterns:
    - "Сквозной гейт с параметром root: один обход для живого и синтетического дерева (tmp_path), антивакуум по каждому дереву с числами в тексте правила"
    - "JS без стороннего парсера: код-вид исходника (комментарии/строки/регэкспы — пробелы, ${…} — код), баланс скобок по код-виду"
    - "Реестр исключений «путь::функция-владелец» с потолком 0 и контролем подавления только своей функции"

key-files:
  created:
    - tests/test_phone_privacy_gate.py
  modified: []

key-decisions:
  - "Обход — os.walk с отсечением node_modules/__pycache__ вместо rglob: тот же вывод из дерева, но в node_modules главной рабочей копии обход не спускается вовсе (0,89 с на /source/broadcaster)"
  - "Получатель журнала распознаётся шире перечня плана: любое имя или атрибут с окончанием _log/_logger и цепочка logger.bind(...).info(...) — строже, а не слабее; живые числа совпали с разведкой (213/68/89)"
  - "Строка-ключ объекта JS ('phone': x) возвращается в код именем: ключ судится так же, как ключ словаря в Python"
  - "Расширения JS — .js, .mjs, .cjs: будущий модуль воркера в ESM-форме не выпадет из обхода"
  - "Подложенная строка проверяется в каждом из четырёх деревьев D-09 отдельным параметром (test_a_planted_number_line_is_found_in_every_gate_tree), сверх трасера в app/"

patterns-established:
  - "Гейт приватности называется поимённо в каждом плане фаз 17–20: uv run pytest tests/test_phone_privacy_gate.py -q"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Python-половина: номер в вызове журнала app/, scripts/, max_worker/ — по имени, f-строке, именованному аргументу, bind, ключу extra, литералу трёх форм, через phone_set=номер или mask_phone — краснит; булев phone_set и маска в print под scripts/ — нет"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_number_line_in_a_synthetic_tree_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (19 параметров)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half (12 параметров)"
        status: pass
    human_judgment: false
  - id: D2
    description: "JS-половина по wa_worker/: шаблонные строки ${…}, конкатенация, многострочный вызов, носители sock.user / creds.me, литералы, baileysLogger, log.child краснят; комментарии, слово phone в тексте, булев phone_set/phoneSet, регэксп с кавычкой — нет; node_modules не обходится"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_template_string_carrying_a_number_reddens_the_js_half"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_js_log_call_is_found (12 параметров)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_js_half (9 параметров)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_js_walk_skips_node_modules_and_finds_the_planted_file"
        status: pass
    human_judgment: false
  - id: D3
    description: "Подложенная строка находится в каждом из четырёх деревьев D-09; живое дерево — ноль находок при ненулевом обходе каждого дерева; две половины обходят ровно GATE_TREES"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_number_line_is_found_in_every_gate_tree (4 параметра)"
        status: pass
      - kind: integration
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: integration
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_js_log_call_in_the_live_tree"
        status: pass
      - kind: integration
        ref: "tests/test_phone_privacy_gate.py#test_every_gate_tree_is_walked"
        status: pass
    human_judgment: false
  - id: D4
    description: "Реестр исключений PHONE_LOG_EXCEPTIONS пуст под потолком 0; синтетическая запись при потолке 0 названа _ceiling_offence; исключение гасит только свою функцию-владельца"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_exception_registry_stays_under_its_ceiling"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_registered_exception_silences_only_its_own_function"
        status: pass
    human_judgment: false

duration: 18min
completed: 2026-10-08
status: complete
---

# Phase 16 Plan 04: Гейт приватности PHONE-21 Summary

**Сквозной гейт `tests/test_phone_privacy_gate.py`: AST-разбор вызовов журнала в `app/`, `scripts/`, `max_worker/` и собственный токенизатор JS для `wa_worker/` (шаблонные `${…}` — код, носители `sock.user`/`creds.me`) краснят на номере по имени, литералу, ключу или маске; живое дерево — 0 находок при 370 + 68 распознанных вызовах; реестр исключений пуст под потолком 0.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-08T16:15:43Z
- **Completed:** 2026-10-08T16:33:19Z
- **Tasks:** 2 (оба `tdd="true"`, задача 1 — трасер)
- **Files modified:** 1 (создан `tests/test_phone_privacy_gate.py`, 64 теста)

## Accomplishments

- Python-половина: распознаватель вызова журнала (`print`, `logger`/`log`/`logging`/`self.log`/`get_logger()` на уровнях журнала и `bind`/`new`, цепочки `logger.bind(...).info`) и предикат (а) литерал трёх форм, (б) имя/атрибут/ключевой аргумент/ключ словаря с `phone`, кроме булева `phone_set`, (в) `mask_phone` в журнале и в `print` вне `scripts/`.
- JS-половина: `_lex_js` без стороннего парсера — комментарии, строки и регэкспы уходят из код-вида, `${…}` на любой вложенности остаётся кодом; аргументы — до парной скобки; правила имён, носителей JID и литералов.
- Антивакуум: подложенная строка находится тем же обходом в каждом из четырёх деревьев; живые правила печатают число файлов и вызовов по дереву.
- Реестр `PHONE_LOG_EXCEPTIONS` («путь::функция» → причина, только Python) пуст, `PHONE_LOG_EXCEPTIONS_CEILING = 0`, `_ceiling_offence`; шапка называет сквозной статус для фаз 17–20 и границу средства (сторонние журналы, `PHONE`/`phone.txt` у MAX, значения без имени, `wa_bridge/`).

## Task Commits

1. **Задача 1 (трасер): Python-половина** — RED `91fa20ef` (test), GREEN `95252fd9` (feat)
2. **Задача 2: JS-половина, реестр, шапка** — RED `730f47a4` (test), GREEN `27e79d27` (feat)

REFACTOR-коммитов нет — правок после GREEN не понадобилось.

## Живые замеры: две рабочие копии (orchestrator note 1)

Тот же модуль из рабочей копии агента, вызовы `scan_gate(root)` / `python_sources(root)` / `js_sources(root)`
скриптом в scratchpad (не закоммичен), только чтение `/source/broadcaster`:

| Дерево | Рабочая копия агента: файлов / вызовов | Главная рабочая копия `/source/broadcaster`: файлов / вызовов |
|---|---|---|
| `app` | 98 / 213 | 98 / 213 |
| `scripts` | 4 / 68 | 4 / 68 |
| `max_worker` | 2 / 89 | 2 / 89 |
| `wa_worker` | 1 / 68 | 1 / 68 |
| находок | 0 | 0 |
| время обхода | 0,88 с | 0,89 с |

`wa_worker/node_modules/` есть только в главной рабочей копии (`is_dir() = True`); обход взял из неё 0 файлов.
Числа совпадают с разведкой (Python 213/68/89 = 370, JS 68). Сиблинги волны 1 добавят `app/services/phone.py`
(16-02) и колонки модели (16-03) — Python-файлов в `app` станет больше; находок в них быть не должно, это
проверит пост-мердж прогон оркестратора. Дополнительный зонд токенизатора на наследии `wa_bridge/index.js`
(вне D-09): 44 вызова (как в разведке), баланс скобок код-вида 0 для обоих JS-файлов.

## TDD Gate Compliance

| Цикл | RED | GREEN | REFACTOR |
|---|---|---|---|
| Задача 1 | `91fa20ef` test(16-04) | `95252fd9` feat(16-04) | — |
| Задача 2 | `730f47a4` test(16-04) | `27e79d27` feat(16-04) | — |

**RED задачи 1.** Команда: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k test_a_planted_number_line_in_a_synthetic_tree_reddens_the_gate --junit-xml=<scratchpad>/1604-red1.xml`, exit 1.
Три совпадения: `FAILED tests/test_phone_privacy_gate.py::test_a_planted_number_line_in_a_synthetic_tree_reddens_the_gate`;
`1 failed, 32 deselected`; `AssertionError: подложенная строка с номером не найдена: гейт обошёл синтетическое дерево (app: файлов 1, вызовов 0, …)`.
`check tdd-red-evidence`: `RED_EVIDENCE_OK` / `target_test_failed` на неизменённом JUnit XML (`format: junit`) и на его
механическом перегоне в node:test TAP (`format: tap`), `report_errors: []` в обоих.
**semanticAssessment:** цель исполнилась (обход нашёл подложенный файл — первое утверждение прошло) и упала на
запланированном утверждении о пустых находках, с причинным литералом; сбора, импорта и фикстур-ошибок нет.

**RED задачи 2.** Команда: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k test_a_template_string_carrying_a_number_reddens_the_js_half --junit-xml=<scratchpad>/1604-red2.xml`, exit 1.
Три совпадения: `FAILED tests/test_phone_privacy_gate.py::test_a_template_string_carrying_a_number_reddens_the_js_half`;
`1 failed, 63 deselected`; `AssertionError: шаблонная строка с номером не найдена: …`.
`check tdd-red-evidence`: `RED_EVIDENCE_OK` для JUnit и TAP, `report_errors: []`.
**semanticAssessment:** цель исполнилась и упала на утверждении «находок нет» при заготовке `js_log_offences → []`;
в том же RED-прогоне всего модуля 25 падений — все утверждения, 39 тестов задачи 1 зелёные, ошибок сбора нет.

Записи улик лежали в `.venv/red-evidence/` рабочей копии (gitignored, классификатор требует путь внутри
проекта) и умирают с рабочей копией; скрипт перегона — в scratchpad, не закоммичен.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py` — гейт PHONE-21: обе половины, реестр с потолком 0, 64 теста (контроли отрицательные/положительные поимённо по `id`, трасер, подложенные строки в четырёх деревьях, живые правила с числами).

## Decisions Made

- `os.walk` с отсечением `node_modules`/`__pycache__` вместо `rglob` — тот же обход, но без перебора чужих тысяч файлов в главной рабочей копии.
- Получатель журнала шире перечня (`*_log`, `*_logger`, цепочки) — гейт строже; на живом дереве ложных срабатываний 0.
- Ключ-строка JS-объекта судится как имя; ключ словаря Python — тоже (`extra={"phone": …}`).
- Расширения JS `.js/.mjs/.cjs`.
- Подложенная строка — в каждом из четырёх деревьев отдельным параметром (критерий успеха 1).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Положительный контроль `regex-literal-with-a-quote` и разбор литералов регулярных выражений в токенизаторе**
- **Found during:** Задача 2
- **Issue:** `wa_worker/index.js` содержит литералы регулярных выражений (`/@s\.whatsapp\.net$/`, `/wait of (\d+) seconds? is required/i`); план называл пропуск строк и комментариев, но не регэкспов. Кавычка или непарная скобка внутри регэкспа сдвинула бы разбор всех последующих вызовов.
- **Fix:** эвристика «`/` в позиции выражения открывает регэксп» (после оператора, открывающей скобки или ключевого слова), класс `[...]` учитывается; контроль с `/'/g` в аргументах.
- **Files modified:** tests/test_phone_privacy_gate.py
- **Verification:** контроль зелёный; код-вид `wa_worker/index.js` и `wa_bridge/index.js` сбалансирован по всем трём видам скобок, длина и число строк совпадают с исходником.
- **Committed in:** `730f47a4` (контроль), `27e79d27` (реализация)

**2. [Rule 2 - Missing Critical] Контроль подавления реестром только своей функции**
- **Found during:** Задача 2
- **Issue:** план требовал, чтобы находки с ключом из реестра не судились, но контроля, что ключ гасит ровно свою функцию, не было — реестр мог бы молча гасить весь файл.
- **Fix:** `test_a_registered_exception_silences_only_its_own_function` (через `monkeypatch.setitem`, реестр после теста пуст).
- **Files modified:** tests/test_phone_privacy_gate.py
- **Committed in:** `730f47a4` / `27e79d27`

---

**Total deviations:** 2 auto-fixed (2 missing critical). **Impact on plan:** обе правки усиливают гейт против вакуума и сдвига разбора; предмет и сигнатуры плана не изменены.

## Verification

- `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` — 64 passed.
- `… -k "planted or live_trees"` — 2 passed; `tests/test_phone_privacy_gate.py tests/test_logging_config.py -k "template or live_tree or ceiling or every_gate_tree or logging"` — 13 passed.
- Сквозные гейты (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`) — **576 passed** (как замер планирования), 162 с.
- `tests/test_planning` — **15 failed, 193 passed**, ровно как база 1a0c1bb5 по замеру оркестратора: 2 × `test_deferred_items_are_idempotent.py`, 9 × `test_plan_prohibitions_census.py` (сироты биекции — запреты планов фазы 16, реестр сеет 16-01), 4 × `test_requirement_completion_follows_verification.py`. Ни одно сообщение переписи не называет `test_phone_privacy_gate`; дифф плана от базы — один файл `tests/`.
- `uv run python -m compileall -q app main.py tests` — ок.
- Все `<acceptance_criteria>` обеих задач — PASS (grep: 3/1, 3/1/1/1/1/11; RED-улики выше).

**Подмены (названы):** полная суита (`just test`, ~40 мин) не гонялась — пост-мердж гейт оркестратора;
`graphify update .` не запускался в рабочей копии агента (вывод gitignored и умрёт с ней) — оркестратор
запускает его в главной рабочей копии после слияния; прогон гейта на дереве после слияния волны 1 — тоже
за оркестратором.

## Issues Encountered

- Heredoc-дописывание и составные команды отклоняются защитой изоляции рабочей копии — правки сделаны инструментом Edit, команды разбиты на простые.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы фаз 17–20 называют `uv run pytest tests/test_phone_privacy_gate.py -q` поимённо (D-09; фраза в шапке гейта).
- Реестр исключений пуст; если писатель номера фаз 17–20 положит номер в журнал, гейт покраснеет — подъём потолка только решением владельца.
- Вне охвата (кандидат в бэклог, CONTEXT §Deferred): `PHONE` и `phone.txt` у MAX, журналы Baileys/pymax/Telethon.

## Self-Check: PASSED

- FOUND: tests/test_phone_privacy_gate.py
- FOUND: 91fa20ef, 95252fd9, 730f47a4, 27e79d27 (предки HEAD)

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-08*

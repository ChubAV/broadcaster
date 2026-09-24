---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 01
subsystem: planning-records
tags: [prohibitions, census, registry, yaml, ast, tdd, tracer, criterion-6]

requires:
  - phase: 10-rychag-components-modal-html
    provides: "321 запрет Фазы 10 в блоках `must_haves.prohibitions` — область решений D-02; образец `10-PROHIBITIONS-SUBJECT.md` (форма шапки `status: subject`, запрет поля вердикта)"
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-06 — входное условие фазы: `tests/test_planning/` зелен целиком"
provides:
  - "scripts/prohibitions_census.py — единственный прибор переписи запретов планов: --check, --list [--phase N], --breakdown, --reconcile, --seed-registry"
  - "tests/test_planning/test_plan_prohibitions_census.py — принуждающая половина, 34 правила, маркер planning; ПЕРВЫЙ в проекте читатель блока must_haves.prohibitions (D-06)"
  - "15-prohibitions-registry.yaml — 697 строк тождеств, биекция с переписью, class unclassified / disposition unresolved, declared_rule у 61 запрета D-05"
  - "перечень диспозиций DISPOSITIONS = {enforced, permitted, unresolved}, DISPOSITIONS_DECLARED = 3"
  - "воспроизведение четырёх исторических сетей 374 / 76 / 57 / 38 со слагаемыми расхождения"
affects: [15-12, 15-13, phase-15-verification, criterion-6]

actuals:
  tokens: 54209
  tasks: 3
  commits: 5
plan_head_before: 0cfea6c57a6c75be7d4dda1ebd62c176ddd971aa

tech-stack:
  added: []
  patterns:
    - "прибор = чистая функция от отображения «путь → текст»; человеческая половина в scripts/, принуждающая в tests/, разборщик один"
    - "ключевание по БЛОКУ шапки (yaml), тождество = путь плана + индекс в блоке"
    - "слагаемые расхождения снимаются независимо от числа сети; остатка среди слагаемых нет"
    - "вселенная правил суиты подаётся параметром; разбор ast кэшируется по ТЕКСТУ исходника"

key-files:
  created:
    - scripts/prohibitions_census.py
    - tests/test_planning/test_plan_prohibitions_census.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-01-SUMMARY.md
  modified: []

key-decisions:
  - "Число вехи снято прибором 2026-09-24: 697 элементов на 156 планах (с планами Фазы 15, 47 элементов в 14 планах); 650 (2026-09-23, 142 плана) не вычеркнуто — утверждается правилом над подмножеством без каталога Фазы 15"
  - "Перечень диспозиций {enforced, permitted, unresolved}, число 3; четвёртое значение («принуждается частично») вводит план 15-12. Ни одна строка реестра не несёт диспозиции, кроме засеянной unresolved; решения по запретам этим планом НЕ ПРИНИМАЛИСЬ (D-03)"
  - "Вселенная правил D-05 = имена функций ∪ имена модулей суиты: 10-44#3 объявляет модуль test_requirement_completion_follows_verification, и одни функции объявили бы его отсутствующим"
  - "Разница сетей verification: test 76 − 61 = 15 разложена счётом как 10 truths + 0 assumptions + 1 проза шапки + 4 проза тела (все пять — 10-47-PLAN.md), а не «соседние блоки» целиком; поправка записана летописью рядом с прежней формулировкой"
  - "Разбор YAML через libyaml CSafeLoader при наличии (результат посимвольно равен yaml.safe_load на всех 157 документах, в 10 раз быстрее) — иначе модуль шёл 18.6 s против бюджета T-15-06"

patterns-established:
  - "Реестр тождеств с двумя носителями числа: rows_declared в шапке реестра и литерал с именем фазы в модуле теста"
  - "Поле строки реестра судится ПРИНАДЛЕЖНОСТЬЮ объявленному перечню полей, а не запретом конкретного имени — иначе правило знало бы сегодняшнее состояние"

requirements-completed: ["критерий-6"]

coverage:
  - id: D1
    description: "Прибор переписи: 697 элементов блока must_haves.prohibitions по вехе (с Фазой 15), разбивка 07:31 08:24 09:153 10:321 11:68 12:22 13:8 14:23 15:47, 0 отказов разбора; 650 на 142 планах без Фазы 15 воспроизведено; разложение наивной сети до единицы (650−24+102+17=745; 697−24+119+17=809)"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_census_of_the_milestone_matches_the_declared_number"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_naive_line_net_decomposes_to_the_unit_before_phase_15_plans"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → exit 0, «фаза 10: 321»"
        status: pass
    human_judgment: false
  - id: D2
    description: "Реестр 15-prohibitions-registry.yaml в биекции с переписью; диспозиция каждой строки из объявленного перечня; поля строки из объявленного перечня; отпечаток формулировки ловит правку; ни одного поля permit_*"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_census_and_the_registry_are_a_bijection"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_disposition_belongs_to_the_declared_vocabulary"
        status: pass
      - kind: other
        ref: "python -c … sum(k.startswith('permit')) → 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "D-05: 61 запрет Фазы 10 с verification: test несёт declared_rule (2 имени, 59 признаков «не объявлено»); существование объявленных имён предъявлено ast; три значения поля сходятся к 321; контроли от вакуума"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_declared_rule_exists_in_the_suite_tree"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_negative_a_declared_rule_absent_from_the_suite_is_named"
        status: pass
    human_judgment: false
  - id: D4
    description: "Человеческая половина: --list/--breakdown/--reconcile; четыре исторические сети 374/76/57/38 воспроизведены на 57 планах Фазы 10 со слагаемыми; засев идемпотентен"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_historic_nets_are_reproduced_by_the_instrument"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --list --phase 10 | wc -l → 321"
        status: pass
    human_judgment: false

duration: 23min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 01: Прибор переписи запретов планов Summary

**Один исполняемый прибор переписи (`yaml` по блоку `must_haves.prohibitions`, тождество «путь плана + индекс»): 697 элементов вехи на 156 планах, биекция с реестром из 697 строк, 61 запрет D-05 с предъявленным `ast` существованием объявленных правил и воспроизведением четырёх исторических сетей 374 / 76 / 57 / 38 до слагаемых.**

## Performance

- **Duration:** 23 min
- **Started:** 2026-09-24T06:17:21Z
- **Completed:** 2026-09-24T06:40:23Z
- **Tasks:** 3
- **Files created:** 3 (плюс эта сводка)

## Число вехи и его летопись

- **Снято прибором 2026-09-24: 697** элементов блока `must_haves.prohibitions` на 156 файлах `.planning/phases/*/[0-9]*-PLAN.md`, 0 отказов разбора. Разбивка: 07:31 08:24 09:153 10:321 11:68 12:22 13:8 14:23 **15:47**.
- **Летопись `650 → 697`:** 650 — веха без планов Фазы 15 (замер 2026-09-23 на 142 планах, воспроизведён дважды); 697 — с планами Фазы 15. Причина роста: 14 планов Фазы 15 несут 47 элементов собственных блоков запретов и входят в область прибора по построению. 650 не было ошибкой — оно устарело внутри своей фазы. Оно не вычеркнуто: правило `test_the_census_reproduces_the_measurement_taken_before_phase_15_plans` воспроизводит его над подмножеством без каталога Фазы 15.
- **Область решений D-02 не меняется:** Фаза 10, 321 (`PROHIBITIONS_IN_DECISION_SCOPE`).
- **Перечень диспозиций:** `DISPOSITIONS = {enforced, permitted, unresolved}`, `DISPOSITIONS_DECLARED = 3`. Четвёртое значение («принуждается частично») вводит план 15-12.
- ⚠️ **Решения по запретам этим планом НЕ ПРИНИМАЛИСЬ (D-03).** Все 697 строк реестра несут засеянные `class: unclassified` и `disposition: unresolved`; полей `permit_*` и полей вердикта в реестре нет. Предмет решения — план 15-12 (классы + чекпойнт владельца), решения — план 15-13.

## Accomplishments

- `scripts/prohibitions_census.py` — прибор: `census()`, `decomposition()`, `historic_nets()`, `reconcile_lines()`, засев/загрузка реестра; режимы `--check`, `--list [--phase N]`, `--breakdown`, `--reconcile`, `--seed-registry` (идемпотентен по тождествам).
- `tests/test_planning/test_plan_prohibitions_census.py` — 34 правила под маркером `planning`: перепись и разбивка, тождество, порядок ключей, соседние блоки, разложение сети до единицы (две вселенные), биекция, согласие строки с элементом (отпечаток), перечни полей и диспозиций, D-05, четыре исторические сети, идемпотентность засева; контроли от вакуума положительные, отрицательные и пустые.
- `15-prohibitions-registry.yaml` — строка YAML на запрет (697), `rows_declared: 697`, `measured: '2026-09-24'`.
- Слагаемые расхождения сетей сняты независимо от числа сети. Разбор блоков против счёта строк. Остатка среди слагаемых нет, и контроль `test_control_historic_decomposition_reddens_on_an_unattributed_block` доказывает, что незнакомый блок ломает равенство:

| Сеть | Множество | Число | Слагаемые |
|---|---|---:|---|
| разбор блока | веха без Фазы 15 | 650 | перепись |
| `^\s*- statement:` | веха без Фазы 15 | 745 | 650 − 24 + 102 truths + 17 assumptions |
| разбор блока | веха целиком | 697 | перепись |
| `^\s*- statement:` | веха целиком | 809 | 697 − 24 + 119 truths + 17 assumptions |
| `^\s*- statement:` | Фаза 10, 57 планов | 374 | 321 − 0 + 45 truths + 8 assumptions + 0 тело |
| `verification: test` | Фаза 10 | 76 | 61 + 10 truths + 0 assumptions + 1 проза шапки + 4 проза тела |
| `^\s*prohibitions:` | Фаза 10 | 57 | 57 планов с блоком (блоки, не элементы) + 0 тело |
| `MUST NOT\|НЕ ДОЛЖ\|ЗАПРЕЩ` | Фаза 10 | 38 | 2 перепись + 1 truths + 0 assumptions + 35 тело |

## Task Commits

1. **Задача 1 (tracer): сквозной срез переписи.** RED `e0f9036e` (test), GREEN `66c42fef` (feat).
2. **Задача 2: D-05, существование объявленного правила.** RED `a774f1d9` (test), GREEN `7c9fed2f` (feat).
3. **Задача 3: человеческая половина и сличение с историческими сетями.** `f39f2bd0` (feat).

**Plan metadata:** коммит сводки и коммит трекинга следуют за этим файлом.

## TDD Gate Compliance

- Оба RED-шага прошли проверку штатным вербом. Запись собрана из `--junit-xml` того же прогона. Разовый скрипт в scratchpad (не закоммичен) перегнал её в node:test TAP.
  - **RED задачи 1:** `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly --junit-xml=<scratchpad>/red1.xml`. Итог: exit 1, 13 failed / 6 passed. Цель `test_the_census_of_the_milestone_matches_the_declared_number` упала на `AssertionError: перепись дала 0 элементов … объявлено 697`. Вердикт `check tdd-red-evidence`: **`RED_EVIDENCE_OK` / `target_test_failed`**.
  - **RED задачи 2:** та же команда (`red2.xml`). Итог: exit 1, 2 failed / 25 passed. Цель `test_every_phase_10_verification_test_row_carries_a_declared_rule` упала на `AssertionError: строки реестра без поля declared_rule (61)`. Вердикт: **`RED_EVIDENCE_OK` / `target_test_failed`**. Второй упавший тест не был целью: он требует признак `tool.RULE_UNDECLARED`, который появился только в GREEN.
- Гейты по журналу: `test(15-01)` ×2, `feat(15-01)` ×3, `refactor(15-01)` нет (не требовался).
- Задача 3 — `type="auto"` без `tdd`: её правила вошли в один коммит `feat` с реализацией.
- **Tracer feedback gate** после задачи 1: интерактивный прогон, `end-of-phase`, `<verify>` только автоматический. `<verify>` перепрогнан на закоммиченном дереве: 19 passed / 63 passed / `--check` 0 / compile молчит. Итог: «⚡ Tracer verified end-to-end — expanding».

## Files Created/Modified

- `scripts/prohibitions_census.py`. Прибор, человеческая половина и единственный разборщик.
- `tests/test_planning/test_plan_prohibitions_census.py`. Принуждающая половина. Докстринг несёт:
  - летопись D-01 («ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ»);
  - летопись `650 → 697`;
  - абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» с обеими половинами D-06;
  - абзац D-33;
  - границу переезда в архив;
  - риск транзитивного PyYAML.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml`. Реестр тождеств.
- `tests/conftest.py` **не тронут**: маркер `planning` уже зарегистрирован.

## Decisions Made

См. `key-decisions` во фронтматтере. Главное:
- 697 как число вехи с именем фазы в литерале. 650 сохранено правилом.
- Вселенная правил D-05 — функции ∪ модули суиты.
- Разница 76 − 61 = 15 разложена счётом.
- libyaml ради бюджета.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Разница сетей `verification: test` 76 − 61 = 15 — не «те же соседние блоки» целиком**
- **Found during:** задача 3
- **Issue:** план (задача 3) и 15-RESEARCH.md Ф-03 относят всю разницу 15 к блокам `truths`/`assumptions`. Счёт даёт 10 (ключи элементов `truths`) + 0 (`assumptions`) + 1 (строковый элемент `must_haves.key_links`, `10-47-PLAN.md:52`) + 4 (проза тела `10-47-PLAN.md`).
- **Fix:** утверждены четыре литерала слагаемых и их сумма 15. Поправка записана летописью рядом с прежней формулировкой, она не вычеркнута.
- **Files modified:** `tests/test_planning/test_plan_prohibitions_census.py`, `scripts/prohibitions_census.py`
- **Committed in:** `f39f2bd0`

**2. [Rule 1 - Bug] Вселенная правил D-05 из одних функций объявила бы существующее правило отсутствующим**
- **Found during:** задача 2 (замер объявленных имён)
- **Issue:** из 61 запрета с `verification: test` имя правила объявляют два:
  - `10-36#1` — функция `test_control_a_missing_anchor_is_named_by_the_rule`;
  - `10-44#3` — модуль `test_requirement_completion_follows_verification` (файл `tests/test_planning/…py`), который запрет прямо называет «правилом».

  Вселенная из одних `ast.FunctionDef` покраснела бы на работе, а не на дефекте.
- **Fix:** вселенная = имена функций ∪ основы имён модулей, чей исходник разбирается `ast`. Существование по-прежнему снимается деревом, не текстом.
- **Committed in:** `a774f1d9`, `7c9fed2f`

**3. [Rule 1 - Bug] `--list | head` падал `BrokenPipeError`**
- **Found during:** задача 3 (проверка `--list --phase 10`)
- **Fix:** закрытый канал завершает прибор кодом 0 без трассы.
- **Committed in:** `f39f2bd0`

**4. [Rule 2 - Missing critical] Бюджет T-15-06: чистый `yaml.safe_load` вывел модуль на 18.6 s**
- **Found during:** задача 1 (GREEN)
- **Issue:** один проход вселенной занимал ~1 s (880 КБ шапок). Правила проходят вселенную многократно, а перепись разбирала каждую шапку дважды.
- **Fix:**
  - однопроходный `_sweep`;
  - `_safe_yaml` — libyaml `CSafeLoader`, когда он есть, иначе `yaml.safe_load`. Замер: посимвольно равный результат на всех 157 документах (156 шапок + реестр), 0.14 s против 1.39 s;
  - разбор `ast` суиты кэшируется по ТЕКСТУ исходника (`lru_cache`), так что подменённая копия есть другой ключ.

  Модуль: 18.6 s → 4.3 s (34 правила). Прогон `tests/test_planning/ tests/test_templates/`: 19.1 s.
- **Committed in:** `66c42fef`, `a774f1d9`

**5. [Rule 2 - Missing critical] Скелет интерфейса скрипта в RED-коммите задачи 1**
- **Issue:** без модуля `scripts/prohibitions_census.py` сбор теста падал бы на импорте. По tdd.md и вербу это `INVALID_RED` (отказ загрузки), а не падение цели.
- **Fix:** RED-коммит несёт скелет интерфейса без поведения: каждая функция возвращает пустое. Цель упала на `AssertionError` о числе.
- **Committed in:** `e0f9036e`

**6. [Rule 2 - Missing critical] Правила сверх десяти названных планом**
- **Состав:**
  - согласие строки реестра с элементом (фаза, `verification`, `statement_digest`) — без него поле отпечатка ничего не обнаруживало бы;
  - перечень полей строки `REGISTRY_ROW_FIELDS` вместо утверждения «нет `permit_*`». Такое утверждение знало бы сегодняшнее состояние и покраснело бы на законной работе плана 15-13;
  - отказ разбора называется;
  - контроль разложения исторической сети;
  - идемпотентность засева правилом.
- **Committed in:** `e0f9036e`, `f39f2bd0`

---

**Total deviations:** 6 auto-fixed (3 Rule 1, 3 Rule 2)
**Impact on plan:**
- Все поправки нужны для верности числа или для бюджета прогона.
- Область плана не расширена.
- Решений по запретам не принималось.

## Issues Encountered

- Уточнение, не отказ. Литералы плана `NAIVE_LINE_NET_DECLARED = 745`, `TRUTHS_DECLARED = 102`, `ASSUMPTIONS_DECLARED = 17` сняты на 142 планах. Они сохранены и утверждаются над подмножеством без Фазы 15. Для вселенной целиком добавлены `NAIVE_LINE_NET_AT_PHASE_15 = 809` и `TRUTHS_AT_PHASE_15 = 119`: `assumptions` и дефис на чужом ключе планами Фазы 15 не пополнились.
- `requirements.ready-ids` (только чтение) для `критерий-6`: `{"ready": [], "blocked": ["критерий-6"]}`. Этот ID объявлен и сестринскими планами. `requirements.mark-complete` не вызывался: отметки ставит закрытие фазы.

## Known Stubs

Нет. `class: unclassified` и `disposition: unresolved` во всех 697 строках — не заглушки, а засеянный ПРЕДМЕТ решения. Его заполняют планы 15-12 и 15-13 по D-03, и так записано в шапке реестра и в докстринге.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Половина (а) критерия 6 закрыта: перечень запретов определён одним прибором и воспроизводим.
- План 15-12 может:
  - вводить классы и четвёртую диспозицию, поднимая `DISPOSITIONS_DECLARED` с летописью;
  - строить чекпойнт владельца над `--list --phase 10` (321 строка).
- План 15-13 пишет решения в строки реестра. Поля `permit_*` при этом вносятся в `REGISTRY_ROW_FIELDS` с летописью.
- Граница: закрытие вехи переносит `.planning/phases/` в архив. Правила переписи тогда покраснеют пустой вселенной, и переезд области прибора делается вместе с реестром.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

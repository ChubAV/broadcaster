---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 15
subsystem: planning-records
tags: [prohibitions, census, registry, fixed-set, wr-04, in-06, pyyaml, ast, criterion-6]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-01: прибор переписи и реестр на 697 строк; планы 15-12/15-13: классы, ответ владельца `class_decisions`, диспозиции 321 запрета Фазы 10; коммит планирования 1c747b5a: файлы планов 15-15…15-33 (окно красноты — 6 правил переписи)"
provides:
  - "числа с именем Фазы 15 (697 / 47 / 119 / 809) меряются над ФИКСИРОВАННЫМ НАБОРОМ `through_fixed_set` — планы по 15-14 включительно, 156 файлов; значения не подняты"
  - "растущая половина без литерала: биекция переписи всей вселенной с реестром, строки планов после набора засеяны вне области решений, разложение наивной сети сходится на всей вселенной"
  - "реестр пересеян: 697 → 741 строк, 44 новые строки планов 15-15…15-33 (`unclassified` / `unresolved`)"
  - "IN-06: PyYAML остаётся транзитивной — запись в `.planning/STATE.md` `### Decisions`; круг прямых импортёров объявлен `YAML_DIRECT_IMPORTERS` (3), новый импортёр краснит правило по `ast`"
affects: [15-16, 15-17, 15-18, 15-19, 15-20, 15-21, 15-22, 15-23, 15-24, 15-25, 15-26, 15-27, 15-28, 15-29, 15-30, 15-31, 15-32, 15-33, phase-15-verification, criterion-6]

actuals:
  tokens: 9866
  tasks: 2
  commits: 3
plan_head_before: 13f13abf7c40b7ebfff7dbb217e8127964e205a8

tech-stack:
  added: []
  patterns:
    - "объявленное число меряется над набором, заданным НОМЕРАМИ фазы и плана (`through_fixed_set`), а не над растущей вселенной обхода; всё новое держит правило без литерала — биекция и принадлежность"
    - "перечень прямых импортёров необъявленной зависимости снимается `ast` (узлы `Import` / `ImportFrom`), множество РАВНО перечню; строка и комментарий импортом не считаются"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-15-SUMMARY.md
  modified:
    - scripts/prohibitions_census.py
    - tests/test_planning/test_plan_prohibitions_census.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
    - .planning/STATE.md

key-decisions:
  - "15-15: числа переписи с именем Фазы 15 (697 / 47 / 119 / 809) НЕ подняты — сдвинута объявленная вселенная: фиксированный набор `through_fixed_set` (фаза < 15 либо 15 с планом ≤ 14; 156 файлов), летопись D-30/D-32 в докстринге модуля; планы 15-15 и далее держит растущая половина без литерала числа (WR-04)"
  - "15-15: IN-06 — ветвь (б): PyYAML остаётся транзитивной через `uvicorn[standard]>=0.41.0` → экстра `standard` → `pyyaml>=5.1` (uv.lock 6.0.3), запись в `### Decisions`; ветвь (а) «объявить в dev» отвергнута рамкой «0 новых зависимостей» и отсутствием строки аудита легитимности; прямых импортёров 3, объявлены `YAML_DIRECT_IMPORTERS`"
  - "15-15: подсказка отказа `count_offence` переписана — прежняя велела «поднять литерал вместе с летописью», то есть ровно ту ложь, которую план запрещает; теперь она называет фиксированные наборы и засев"

patterns-established:
  - "Фиксированный набор + растущая половина: литерал с именем фазы судит только набор, определённый номерами; вселенная, растущая после него, судится биекцией и принадлежностью"
  - "Любой следующий план, добавляющий `import yaml` в `app/`, `scripts/`, `tests/` или `main.py`, обязан расширить `YAML_DIRECT_IMPORTERS` (с летописью числа) — иначе `tests/test_planning/` краснеет"
  - "Каждый следующий план с блоком `must_haves.prohibitions`, легший на диск, требует `--seed-registry`; число его запретов не утверждается нигде"

requirements-completed: ["критерий-6"]

coverage:
  - id: D1
    description: "Числа Фазы 15 (697 / 47 / 119 / 809) и число файлов набора (156) утверждаются над фиксированным набором `through_fixed_set`; литералы не подняты; отбор не зависит от порядка подачи"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_census_of_the_milestone_matches_the_declared_number"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_naive_line_net_decomposes_to_the_unit_with_phase_15_plans"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_fixed_set_is_chosen_by_phase_and_plan_number_not_by_order"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_reconcile_table_carries_the_historic_and_the_census_numbers"
        status: pass
    human_judgment: false
  - id: D2
    description: "Растущая половина без литерала: биекция всей вселенной с реестром, строки планов после набора засеяны вне области решений, разложение наивной сети на всей вселенной; контроль синтетическим планом 15-99"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_plans_after_the_fixed_set_only_add_rows_outside_the_decision_scope"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_naive_line_net_decomposes_to_the_unit_on_the_whole_universe"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_plan_after_the_fixed_set_is_named_by_the_bijection"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_census_and_the_registry_are_a_bijection"
        status: pass
    human_judgment: false
  - id: D3
    description: "Реестр пересеян прибором: 741 строка, 44 новые, прежние не сдвинуты; `--check` — согласие, область решений 321"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_reconcile_seed_of_the_registry_is_idempotent_by_identity"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_registry_declares_its_own_length"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие», код 0; --breakdown → «сумма по классам области решений: 321»"
        status: pass
    human_judgment: false
  - id: D4
    description: "IN-06: запись решения в `### Decisions` STATE.md; круг прямых импортёров PyYAML равен перечню `YAML_DIRECT_IMPORTERS`; новый импортёр называется поимённо"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_undeclared_yaml_dependency_has_only_the_declared_direct_importers"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_new_direct_yaml_importer_is_named"
        status: pass
      - kind: other
        ref: "git diff --stat 13f13abf..HEAD -- pyproject.toml uv.lock → пусто"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 15: Фиксированный набор для чисел Фазы 15 и круг импортёров PyYAML Summary

**Числа переписи с именем Фазы 15 (697 / 47 / 119 / 809) теперь утверждаются над фиксированным набором из 156 файлов `through_fixed_set` (планы по 15-14 включительно). Ни одно значение не поднято. Планы 15-15 и далее держит растущая половина без литерала: биекция с реестром, засеянные строки вне области решений и разложение наивной сети на всей вселенной. Реестр пересеян 697 → 741 (44 строки). Находка IN-06 закрыта записью решения: PyYAML остаётся транзитивной через `uvicorn[standard]`, а круг из трёх прямых импортёров объявлен перечнем, который судит `ast`.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-25T05:45:02Z
- **Completed:** 2026-09-25T05:54:03Z
- **Tasks:** 2
- **Files modified:** 4 (+ сводка)

## Accomplishments

- **Прибор.** Заведены `FIXED_SET_PHASE = "15"`, `FIXED_SET_LAST_PLAN = 14`, `plan_number_of` (имя не формы `NN-MM-PLAN.md` даёт `CensusError`) и чистая `through_fixed_set`. Отбор идёт кортежем `(фаза, план) <= (15, 14)`, фаза берётся из каталога, номер плана из имени файла. `reconcile_lines` печатает третью вселенную «веха по план 15-14 включительно» (156 планов, 697 и 809) между двумя прежними. Раздел режимов докстринга и абзац шапки реестра о `rows_declared` дополнены летописью.
- **Гейт.** Литералы прежние. Добавлен `PLAN_FILES_THROUGH_PLAN_15_14 = 156` и фикстуры `fixed_sources` / `fixed_census`. На набор переведены правила числа, разложения с 697 и области решений. Правило длины реестра теперь утверждает три вещи: `rows_declared` равно длине строк, длина равна переписи всей вселенной, строк набора ровно 697. Контроли переписаны: синтетика над набором называет 698, биекция над вселенной даёт ровно одну сироту, в пустой вселенной лишних строк `rows_declared`. Новые правила: `test_the_naive_line_net_decomposes_to_the_unit_on_the_whole_universe`, `test_plans_after_the_fixed_set_only_add_rows_outside_the_decision_scope`, `test_the_fixed_set_is_chosen_by_phase_and_plan_number_not_by_order` и контроль `test_control_a_plan_after_the_fixed_set_is_named_by_the_bijection` (синтетический 15-99). В докстринг добавлен абзац «ВСЕЛЕННАЯ ОБЪЯВЛЕННЫХ ЧИСЕЛ — ФИКСИРОВАННЫЙ НАБОР», абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» дополнен.
- **Пересев.** Вывод прибора: «реестр записан: 741 строк». До пересева `--check` называл 44 строки «запрет без строки реестра» (15-15#0…15-33#2) при длине реестра 697. Diff пересева: +44 строки планов 15-15…15-33, все `class: unclassified`, `disposition: unresolved`, без полей решения. Удалены только 4 строки: абзац шапки о `rows_declared` (2), `measured` 2026-09-24 → 2026-09-25 и `rows_declared` 697 → 741. Ни одна прежняя строка не сдвинута.
- **IN-06.** Запись в `.planning/STATE.md` `### Decisions` добавлена правкой, а не вербом. В гейте заведены `YAML_DIRECT_IMPORTERS` (3 пути), правило по `ast` над `app/`, `scripts/`, `tests/` и `main.py` и контроль. Докстринг прибора ссылается на запись решения.

## Окно красноты: до и после

Замер до правки (2026-09-25, дерево 13f13abf, `uv run pytest tests/test_planning/ -q -p no:randomly --junit-xml=…`): **`6 failed, 102 passed`**. Красны ровно шесть правил из `<red_window_measured>`, числа прибора 741 / фаза 15: 91 / 44 сироты совпали с замером планирования.

| # | Правило | До | После коммита гейта 49ca9ddf | После пересева e040b8b8 |
|---|---|---|---|---|
| 1 | `test_the_census_of_the_milestone_matches_the_declared_number` | FAILED (741 ≠ 697) | PASSED | PASSED |
| 2 | `test_the_naive_line_net_decomposes_to_the_unit_with_phase_15_plans` | FAILED (855 ≠ 809) | PASSED | PASSED |
| 3 | `test_the_census_and_the_registry_are_a_bijection` | FAILED (44 сироты) | FAILED (44 сироты) | PASSED |
| 4 | `test_control_negative_a_synthetic_prohibition_is_found_and_named` | FAILED (742, сирот 45) | FAILED (сирот 45) | PASSED |
| 5 | `test_reconcile_table_carries_the_historic_and_the_census_numbers` | FAILED (нет `\| 697 \|`) | PASSED | PASSED |
| 6 | `test_reconcile_seed_of_the_registry_is_idempotent_by_identity` | FAILED (+44 строки) | FAILED (+44 строки) | PASSED |

Итоговое дерево: `uv run pytest tests/test_planning/ -q -p no:randomly` дал **114 passed, 0 failed**. Было 108 правил, план добавил 6. `-v` показывает все шесть правил таблицы как `PASSED`. Правила 3, 4 и 6 (плюс новые правила длины и растущей половины) после первого коммита оставались красными только из-за 44 отсутствующих строк реестра. Сообщение отказа называло каждую строку поимённо. Числовые правила 1, 2 и 5 позеленели от правки гейта, а не от пересева, что и требовал порядок коммитов плана.

## Task Commits

1. **Задача 1 (сквозной срез), гейт и прибор:** `49ca9ddf` (test)
2. **Задача 1, пересев реестра:** `e040b8b8` (chore)
3. **Задача 2, IN-06: запись решения и перечень импортёров:** `ba36fced` (test)

**Plan metadata:** коммит `docs(15-15)` со сводкой, STATE.md, ROADMAP.md и state.json следует за этой сводкой.

## TDD

План `type: execute`, режим `workflow.tdd_mode: true`. Поведение добавляет **задача 1** (сквозной срез): отбор фиксированного набора в приборе и растущие правила в гейте. Её RED — шесть правил окна красноты, измеренные на дереве 13f13abf ДО любой правки. Улика записана так: junit-прогон `tests/test_planning/` конвертирован в node:test TAP одноразовым скриптом в scratchpad (не закоммичен), целевое правило `test_the_census_of_the_milestone_matches_the_declared_number`. `gsd-tools check tdd-red-evidence` вернул **`RED_EVIDENCE_OK`** (`target_test_failed`, 6 fail / 108 tests). Форма записи изменена, измеренный результат нет. GREEN — коммиты 49ca9ddf (гейт + прибор) и e040b8b8 (пересев). Коммит `feat(15-15)` отсутствует: правка — в инструменте записи и его гейте, а тип коммита задан планом («`test(15-15)`, затем `chore(15-15)`»). Задача 2 добавляет правило-перечень, которое зеленеет по прибытии. Это сторож текущего состояния, а не RED. Его зубы доказаны контролем `test_control_a_new_direct_yaml_importer_is_named`.

Tracer feedback gate: интерактивный прогон, `human_verify_mode: end-of-phase`, `<verify>` только `<automated>`. Все три команды перепрогнаны после пересева и прошли: `tests/test_planning/` 112 passed на тот момент, `--check` дал код 0 и «согласие», `--reconcile | grep -c '| 697 |'` вернул 1.

## Files Created/Modified

- `scripts/prohibitions_census.py`: фиксированный набор (`FIXED_SET_*`, `plan_number_of`, `through_fixed_set`), третья вселенная сличения, летопись абзаца шапки реестра о `rows_declared`, ссылка на запись IN-06.
- `tests/test_planning/test_plan_prohibitions_census.py`: правила над набором, растущие правила и контроли, `PLAN_FILES_THROUGH_PLAN_15_14`, `YAML_DIRECT_IMPORTERS` с правилом по `ast`, летописи в докстринге.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml`: пересеян, 741 строка.
- `.planning/STATE.md`: запись решения IN-06 в `### Decisions`, затем учёт позиции.

## Decisions Made

- **Выбор ветви IN-06: (б), записать отступление; ветвь (а) «объявить `pyyaml` в группе `dev`» не выбрана.** Три довода:
  1. Рамка REQUIREMENTS §Out of Scope гласит «Веха получает 0 новых зависимостей».
  2. Установка через менеджер пакетов потребовала бы строки аудита легитимности, а в `15-RESEARCH.md` §Package Legitimacy Audit объявлен ноль пакетов.
  3. Прямых импортёров три: модуль прибора и два модуля суиты. В рантайм приложения (`app/`, `main.py`) PyYAML не входит, это измерено тем же правилом.

  Обратимость полная: объявить зависимость позже — одна строка `pyproject.toml` и пересборка замка.
- **Уточнение замером.** Сам модуль гейта `import yaml` не несёт, разбор идёт через прибор. Фраза докстринга «`import yaml` голый» верна о приборе и прецеденте, не о модуле. Это записано летописью, фраза не правлена.
- **Отбор набора.** Фаза берётся из каталога (как у `phase_of` и разбивки), номер плана из имени файла. Имя не формы `NN-MM-PLAN.md` даёт отказ, а не пропуск: глоб вселенной `[0-9]*-PLAN.md` пропустил бы, например, `15-draft-PLAN.md`.
- **Растущее правило не утверждает непустоту множества планов после набора.** При переезде вехи в архив оно законно опустеет. От вакуума защищает контроль синтетическим планом 15-99.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Подсказка отказа `count_offence` велела поднять литерал**
- **Found during:** задача 1
- **Issue:** хвост сообщения гласил «поднимите литерал ВМЕСТЕ С ЛЕТОПИСЬЮ». После плана это прямое указание нарушить его же запрет MUST NOT о литерале с именем фазы.
- **Fix:** хвост переписан. Теперь он говорит, что числа меряются над фиксированными наборами и новый план их не двигает (его держит биекция, `--seed-registry`), а расхождение значит правку плана внутри набора или самого набора. Префикс «N элементов», на который опирается контроль, сохранён.
- **Files modified:** `tests/test_planning/test_plan_prohibitions_census.py`
- **Committed in:** 49ca9ddf

**2. [Rule 1 — Bug] Абзац шапки реестра о `rows_declared` стал ложным**
- **Found during:** задача 1
- **Issue:** `REGISTRY_HEADER` называл `rows_declared` «вторым носителем числа переписи (первый — литерал модуля теста)». После пересева `rows_declared` равно 741, а литерал 697.
- **Fix:** абзац дополнен действующей формулировкой и летописью D-30/D-32 с прежним текстом. Такая же летопись стоит у комментария к `PROHIBITIONS_DECLARED_AT_PHASE_15`. Шапка входит в текст реестра, поэтому пришла в файл пересевом.
- **Files modified:** `scripts/prohibitions_census.py`, реестр
- **Committed in:** 49ca9ddf, e040b8b8

**3. [Rule 3 — Blocking] Критерий `grep -c '^YAML_DIRECT_IMPORTERS'` = 1**
- **Found during:** задача 2
- **Issue:** счётчик перечня по идиоме `…_DECLARED` назывался `YAML_DIRECT_IMPORTERS_DECLARED`, и grep критерия находил две строки.
- **Fix:** счётчик назван `YAML_IMPORTERS_DECLARED`.
- **Committed in:** ba36fced

**Сверх перечня артефактов плана** (в пределах его предмета): правило `test_the_fixed_set_is_chosen_by_phase_and_plan_number_not_by_order` держит истину «набор не зависит от порядка подачи» (`verification: backstop`) и границу 15-14 / 15-15. Вердикт `ast` по файлу мемоизирован `lru_cache` по ключу (путь, текст), потому что контроль перепарсивал всё дерево: каталог шёл ~11 с, стал ~9.6 с.

---

**Total deviations:** 3 auto-fixed (2 Rule 1, 1 Rule 3).
**Impact on plan:** все три правки держат гейт честным к его собственному запрету. Сфера не расширена.

## Issues Encountered

- Верб `check tdd-red-evidence` сначала вернул `INVALID_RED` / `zero_tests_discovered`: в TAP не было строк node:test `# tests / # pass / # fail`. Строки добавлены из того же junit-прогона (108 / 102 / 6), после чего верб дал `RED_EVIDENCE_OK`.

## Verification

- `uv run pytest tests/test_planning/ -q -p no:randomly` → 114 passed, 0 failed.
- `uv run pytest tests/test_templates/test_htmx_inventory.py -q` → 30 passed. Модуль упоминает прибор текстом. Других импортёров `scripts/prohibitions_census.py` в суите нет.
- `uv run python scripts/prohibitions_census.py --check` → код 0, «реестр: 741 строк, биекция с переписью — согласие». Вселенная 741 > 697.
- `--reconcile | grep -c '| 697 |'` → 1. `--breakdown` → «сумма по классам области решений: 321», «сумма по диспозициям области решений: 321».
- `uv run python -m compileall -q scripts tests/test_planning` → без вывода.
- Все grep-критерии приёмки обеих задач прошли: 697 / 119 / 809 по одной строке, `"15": 47,` = 1, `PLAN_FILES_THROUGH_PLAN_15_14 = 156` = 1, `def through_fixed_set` = 1, два растущих правила по 1, `^YAML_DIRECT_IMPORTERS` = 1. Число `IN-06` в STATE.md выросло 2 → 3, строка `uvicorn[standard]>=0.41.0` стоит на 638 при `### Decisions` на 297 и `### Pending Todos` на 640. `git diff --stat -- pyproject.toml uv.lock` пуст.
- **Замена полного прогона:** `just test` исполнитель не запускал по указанию оркестратора. Полную суиту гонит оркестратор после волны (после 15-19) над деревом с коммитами учёта. Запись в `.planning/WINDOWS.md` об этом не заводилась.

## Known Stubs

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `tests/test_planning/` зелен. Следующие исполнители партии (15-16…15-33) опираются на это.
- **Следующим планам:**
  - (1) план, добавляющий `import yaml` в `app/`, `scripts/`, `tests/` или `main.py`, обязан расширить `YAML_DIRECT_IMPORTERS` с летописью числа;
  - (2) новый файл плана с блоком `must_haves.prohibitions` требует `uv run python scripts/prohibitions_census.py --seed-registry`, а литерал числа не заводится;
  - (3) правка формулировки запрета в плане набора (по 15-14) краснит правило отпечатка и числа. Это по построению.
- Требования не отмечались: `requirements.mark-complete` не вызывался, вердикт фазы `gaps_found`.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

## Self-Check: PASSED

---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 22
subsystem: planning-records
tags: [prohibitions-census, registry, record-mode, ast, permit-scope-uncovered, criterion-6, g-1, d-04, d-05, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-13 — мера покрытия по 61 запрету D-05 (`rule_name`, `rule_site`, `coverage_note`), `unresolved_reason`, `permit_scope`; план 15-12 — блок `class_decisions`; план 15-15 — фиксированный набор; план 15-20 — отказ по имени на испорченном реестре (`CensusError`, строка `ОТКАЗ:`)"
provides:
  - "форма нескольких правил в строке реестра: `rule_name` и `rule_site` через `RULE_SEPARATOR = \"; \"` равной длины, пары по позиции, каждое правило судится `ast` в файле своей координаты"
  - "режим прибора `--record` и функция `record_coverage` — единственное место записи меры покрытия; правило каждой ссылки `tests/…py::имя` найдено разбором `ast`, любой отказ — `CensusError` до первой записи"
  - "поле строки `permit_scope_uncovered` (= класс строки) у 23 частичных строк разрешённых классов; `REGISTRY_ROW_FIELDS_DECLARED = 14`"
  - "решение планирования о 23 частичных строках записано дословно в докстринге правила `test_every_permit_scope_uncovered_names_the_permitted_class_of_its_partial_row`"
affects: [15-24, 15-25, 15-26, 15-27, 15-28, 15-29, 15-30, 15-31, 15-33, критерий-6]

actuals:
  tokens: 28215
  tasks: 2
  commits: 4
plan_head_before: 4df0a7f149de23c47346d81822deb02558cff3b2

tech-stack:
  added: []
  patterns:
    - "Запись в реестр идёт одним путём (`record_coverage`), и гейт повторяет её проверку независимо: координата вычислена тем же разбором `ast`, которым `_rule_site_offences` её судит"
    - "Отказ до первой записи: все проверки прежде мутации, документ либо изменён целиком, либо не изменён; правило утверждает это на копии живого реестра"
    - "Координата правила есть день замера: перезапись того же правила в том же файле её не перемеряет"

key-files:
  created: []
  modified:
    - scripts/prohibitions_census.py
    - tests/test_planning/test_plan_prohibitions_census.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-22: строка реестра называет несколько правил через `RULE_SEPARATOR = \"; \"`; `rule_name` и `rule_site` делятся на равное число частей и сличаются по позиции; одиночная форма читается, как прежде"
  - "15-22: `record_coverage` сохраняет записанную координату правила, которое строка уже называет в том же файле, а новому правилу ставит координату, снятую разбором `ast`. Основание: 4 из 23 перезаписываемых строк несли сдвинувшиеся координаты, и свежий замер нарушил бы критерий приёмки «дифф — только добавленное поле»; гейт номер строки не утверждает"
  - "15-22: частичная строка класса с ветвью `permit-class`, записанная без `--permit-uncovered`, — отказ `CensusError`: иначе прибор записал бы строку, которую гейт назовёт (остаток не закрыт ничем)"
  - "15-22 (решение планирования по поручению Г-1, исполнено): непокрытая часть частичной строки разрешённого класса покрыта разрешением ЭТОГО класса и стоит полем строки `permit_scope_uncovered` = имя класса; у `product-invariant` (`require-enforcement`) поля нет"
  - "15-22: шапка реестра не правилась, чтобы дифф реестра был ровно 23/23 строк; поле описано в модуле теста (летопись 13 → 14) и в докстринге прибора"

patterns-established:
  - "Режим записи: `--record ТОЖДЕСТВО --disposition D --rule tests/…::имя [--rule …] [--coverage-note ТЕКСТ] [--permit-uncovered]`; планы 15-24…15-31 пишут меру покрытия только им"

requirements-completed: ["критерий-6"]

coverage:
  - id: D1
    description: "Строка реестра может назвать несколько правил: `rule_name`/`rule_site` через `; ` равной длины, пары по позиции, каждое правило судится `ast` в файле своей координаты; одиночная форма читается, как прежде"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_multi_rule_row_of_unequal_length_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_one_absent_rule_of_two_is_named_alone"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_single_rule_row_reads_as_before"
        status: pass
    human_judgment: false
  - id: D2
    description: "Режим `--record` / `record_coverage` пишет меру покрытия только с правилом, найденным `ast`, и отказывает по имени на всём, чего записывать нельзя; запись проходит гейт; координата уже названного правила сохраняется"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_record_mode_writes_only_what_the_tree_proves"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_record_mode_keeps_the_coordinate_of_a_rule_it_already_names"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_record_mode_refuses_an_ambiguous_identity_tail"
        status: pass
      - kind: integration
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_main_records_the_row_or_refuses_by_name"
        status: pass
    human_judgment: false
  - id: D3
    description: "Поле `permit_scope_uncovered` у 23 частичных строк разрешённых классов, равное классу; у 9 частичных строк `product-invariant` его нет; форму судит правило гейта, пишет только режим записи"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_permit_scope_uncovered_names_the_permitted_class_of_its_partial_row"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_permit_scope_uncovered_offences_are_named_for_every_kind"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_record_mode_writes_permit_scope_uncovered_only_for_a_permitted_class"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --breakdown → «частичных строк области решений с `permit_scope_uncovered`: 23; без поля: 9»"
        status: pass
    human_judgment: false
  - id: D4
    description: "Решение планирования о 23 частичных строках (разрешение класса покрывает названный остаток) записано дословно в докстринге правила и в этой сводке"
    requirement: "критерий-6"
    verification: []
    human_judgment: true
    rationale: "Запись решения проверяема, но верно ли оно читает поручение Г-1 и достаточно ли для половины (б) критерия 6, решает владелец (`chubav`) и верификатор фазы; решение принято планированием, а не владельцем своими словами"

duration: 13min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 22: Несколько правил в строке, режим записи `--record` и разрешение остатка 23 частичных строк Summary

**Строка реестра запретов теперь называет несколько правил (`rule_name`/`rule_site` через `; `). Режим прибора `--record` пишет меру покрытия только для правил, которые разбор `ast` находит в их файле. 23 частично принуждённые строки разрешённых классов несут машинно читаемое `permit_scope_uncovered` = имя класса; 9 строк `product-invariant` его не несут.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-25T11:13:14Z
- **Completed:** 2026-09-25T11:26:21Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- **Форма нескольких правил.** `RULE_SEPARATOR = "; "` живёт в приборе, гейт его ввозит. `_coverage_offences` требует непустые части равной длины. `_rule_site_offences` судит каждую пару по файлу её координаты и называет ровно отсутствующее правило. Летопись группы: до плана 15-22 строка называла одно правило.
- **Режим записи.** `record_coverage(document, records, identity, disposition, rules, coverage_note, permit_uncovered, suite_root)` — единственное место записи меры покрытия. Тождество принимается полным путём или уникальным хвостом (`10-33-PLAN.md#2`); требуются область решений (D-02) и диспозиция `enforced`/`partially-enforced`. Каждая ссылка `tests/…py::имя` ищется разбором `ast`. Непокрытая часть обязательна у частичной и запрещена у полной. Запись снимает `unresolved_reason` и `permit_scope`. Каждый отказ — `CensusError` до первой записи, и CLI печатает `ОТКАЗ:` с кодом 1, не трогая файл.
- **Поле `permit_scope_uncovered`.** `REGISTRY_ROW_FIELDS` 13 → 14 с летописью; поле входит в `ROW_DECISION_FIELDS`. Правило формы: поле стоит только у `partially-enforced` строки области решений, равно её классу, и класс получил `permit-class`. Каждая такая строка поле несёт, у `require-enforcement` его нет. `--breakdown` печатает 23 / 9.
- **Реестр.** Поле поставлено 23 строкам одноразовым циклом через `record_coverage`, у каждой строки — свои правила, координаты и заметка. Дифф реестра над базой плана — 23 строки убрано, 23 добавлено. Каждая пара отличается только хвостом `, permit_scope_uncovered: <класс>}`; сверено программно, 23 из 23.

### Решение о частичных строках — дословно (истина 3 плана)

> РЕШЕНИЕ ПЛАНИРОВАНИЯ О 23 ЧАСТИЧНЫХ СТРОКАХ РАЗРЕШЁННЫХ КЛАССОВ (записано здесь и в докстринге правила, по поручению Г-1): непокрытая часть частично принуждённого запрета класса с ветвью `permit-class` покрыта разрешением ЭТОГО класса, и это стоит машинно читаемым полем СТРОКИ `permit_scope_uncovered` = имя класса — каждая строка несёт свою запись (D-04), а не выводится из блока `class_decisions` молча. D-05 соблюдён: существование правила предъявлено (оно покрывает часть), разрешение закрывает лишь названный остаток

⚠️ Разрешение не есть соблюдение: остаток этих 23 строк разрешён, а не принуждён.

### 23 строки с полем

| Строка | Класс |
|---|---|
| 10-33-PLAN.md#2 | plan-file-scope |
| 10-34-PLAN.md#0 | self-certification |
| 10-34-PLAN.md#1 | self-certification |
| 10-35-PLAN.md#2 | plan-file-scope |
| 10-35-PLAN.md#4 | self-certification |
| 10-36-PLAN.md#0 | gate-integrity |
| 10-38-PLAN.md#0 | gate-integrity |
| 10-38-PLAN.md#4 | plan-file-scope |
| 10-39-PLAN.md#1 | self-certification |
| 10-43-PLAN.md#2 | gate-integrity |
| 10-44-PLAN.md#1 | record-immutability |
| 10-44-PLAN.md#3 | requirement-flag |
| 10-45-PLAN.md#0 | plan-file-scope |
| 10-45-PLAN.md#2 | self-certification |
| 10-46-PLAN.md#0 | self-certification |
| 10-46-PLAN.md#1 | self-certification |
| 10-46-PLAN.md#2 | self-certification |
| 10-46-PLAN.md#5 | record-immutability |
| 10-47-PLAN.md#1 | record-immutability |
| 10-47-PLAN.md#3 | self-certification |
| 10-48-PLAN.md#0 | self-certification |
| 10-48-PLAN.md#1 | self-certification |
| 10-49-PLAN.md#0 | plan-file-scope |

Итог по классам: gate-integrity 3, plan-file-scope 5, record-immutability 3, requirement-flag 1, self-certification 11 — ровно разбивка плана. Без поля — 9 частичных строк `product-invariant` (ветвь `require-enforcement`).

### Пример вызова `--record`

```bash
# полное принуждение двумя правилами вместе; тождество — уникальным хвостом
uv run python scripts/prohibitions_census.py --record 10-50-PLAN.md#3 --disposition enforced \
  --rule tests/test_pages/test_shell.py::test_the_summary_node_is_a_top_level_child_of_the_response \
  --rule tests/test_pages/test_shell.py::test_the_ad_summary_markup_has_exactly_one_source

# частичное принуждение строки разрешённого класса: остаток назван и разрешён классом строки
uv run python scripts/prohibitions_census.py --record 10-33-PLAN.md#2 --disposition partially-enforced \
  --rule tests/test_pages/test_shell.py::test_failure_banner_has_single_source \
  --coverage-note "половины «обёртка не правится» и «тексты не правятся» не покрыты ничем" \
  --permit-uncovered
```

Отказ (правила нет в файле, строка вне области, частичная без заметки, флаг у `require-enforcement` и т. п.) печатает `ОТКАЗ: …` в поток ошибок, код 1, и реестр не меняется ни на символ. Ссылки в примере — формы вызова; какое правило действительно стережёт какой запрет, решают планы 15-24…15-31.

## Task Commits

1. **Задача 1: несколько правил в строке и режим `--record`**
   - `586dba09` — test(15-22): RED — контроли формы нескольких правил, правило режима записи, CLI-контроль
   - `b7d0988a` — feat(15-22): GREEN — `RULE_SEPARATOR`, `record_coverage`, `--record`, гейт делит поля
2. **Задача 2: поле `permit_scope_uncovered` у 23 строк**
   - `e823c356` — test(15-22): RED — поле в перечнях (13 → 14), правило формы с решением дословно, контроли, тест флага
   - `a2fa9cb5` — feat(15-22): GREEN — порядок поля, `--permit-uncovered`, строка `--breakdown`, поле у 23 строк реестра

**Plan metadata:** коммит сводки `docs(15-22)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute` при `workflow.tdd_mode: true`: гейт TDD на таком плане инертен, поэтому здесь прямо сказано, какая задача добавляет поведение и где её RED. **Поведение добавляют обе задачи**, и каждая прошла RED → GREEN отдельными коммитами `test(15-22)` → `feat(15-22)`.

- **Задача 1, RED `586dba09`.** Цель — `test_control_a_multi_rule_row_of_unequal_length_is_named`: `FAILED …::test_control_a_multi_rule_row_of_unequal_length_is_named`, последняя строка `1 failed`. Причинный литерал: `assert [] == ['.planning/p...01-PLAN.md#3']` — прежний `_coverage_offences` не называл ни одной строки разной длины. Верб `check tdd-red-evidence` дал `RED_EVIDENCE_OK` (`target_test_failed`); запись для него собрана из `--junit-xml` одноразовым скриптом в scratchpad. Остальные тесты того же коммита падали на отсутствующем атрибуте `tool.record_coverage` / имени `RULE_SEPARATOR`. Такой отказ — «поведения ещё нет», а не проваленное утверждение, и уликой RED он **не** заявлен.
- **Задача 2, RED `e823c356`.** Цель — `test_every_permit_scope_uncovered_names_the_permitted_class_of_its_partial_row`: `FAILED …`, `1 failed`. Причинный литерал: `AssertionError: нарушения формы \`permit_scope_uncovered\` (23)`, каждая строка — «частичная строка разрешённого класса … без `permit_scope_uncovered` — остаток её предмета не закрыт ничем». Верб дал `RED_EVIDENCE_OK`. Второй тест коммита упал на заглушке прибора «ещё не объявлено» — это тоже не улика.
- REFACTOR-коммитов нет.

## Files Created/Modified

- `scripts/prohibitions_census.py` — `RULE_SEPARATOR`, `RULE_REFERENCE_SEPARATOR`, `record_coverage` с помощниками (`_resolve_identity`, `_definition_line`, `_rule_pairs`, `_measured_rules`, `_permit_uncovered_fields`), режим `--record` с `--disposition`/`--rule`/`--coverage-note`/`--permit-uncovered`, поле в `REGISTRY_FIELD_ORDER`, строка `--breakdown`, докстринг модуля.
- `tests/test_planning/test_plan_prohibitions_census.py` — разделитель ввезён из прибора; `_coverage_offences`/`_rule_site_offences` делят поля (летопись группы); поле в перечнях (13 → 14, летопись); `_permit_scope_uncovered_offences` и правило с решением дословно; 10 новых тестов.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поле `permit_scope_uncovered` у 23 строк, больше ничего.

## Decisions Made

1. **Координата уже названного правила сохраняется.** `record_coverage` снимает координату разбором `ast` только для нового правила. Если строка уже называет то же правило в том же файле, записанная координата остаётся: это координата дня замера, и гейт номер строки не утверждает. Иначе перезапись одной строки двигала бы номер у любой строки, чей файл вырос, и в диффе записи оказались бы чужие поля.
2. **Частичная строка разрешённого класса без флага — отказ.** План велит флагу отказывать при неверной ветви или диспозиции. Обратный случай прибор тоже отказывает, иначе записал бы строку, которую гейт тут же назовёт.
3. **Шапка реестра не правилась.** Так дифф реестра остался ровно 23/23 по критерию приёмки. Поле описано в модуле теста и в докстринге прибора.
4. **Отказ до первой записи.** Все проверки выполняются прежде мутации; правило утверждает, что копия после каждого из 11 видов отказа равна оригиналу.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Свежий замер координаты противоречил критерию приёмки Задачи 2**
- **Found during:** Задача 1, до кода — сверка записанных `rule_site` с разбором `ast`
- **Issue:** 8 записанных координат сдвинулись с дня замера плана 15-13, из них 4 среди 23 перезаписываемых строк (`10-44#1`, `10-46#5`, `10-47#1`, `10-49#0`). `record_coverage`, всегда снимающий координату заново, сдвинул бы `rule_site` у этих строк. Критерий «23 удалённые и 23 добавленные строки, отличающиеся только полем» тогда не выполнился бы.
- **Fix:** координата правила, которое строка уже называет в том же файле, сохраняется; новое правило получает координату `ast`. Поведение закреплено `test_the_record_mode_keeps_the_coordinate_of_a_rule_it_already_names`.
- **Files modified:** scripts/prohibitions_census.py, tests/test_planning/test_plan_prohibitions_census.py
- **Verification:** программная сверка диффа — 23 из 23 пар отличаются только полем
- **Committed in:** `586dba09`, `b7d0988a`

**2. [Rule 2 - Missing Critical] Отказ записи частичной строки разрешённого класса без `--permit-uncovered`**
- **Found during:** Задача 2
- **Issue:** без этого отказа прибор мог записать строку, которую правило гейта называет («остаток не закрыт ничем»). Запись и гейт разошлись бы, и был бы нарушен связующий узел плана «координата вычислена тем же разбором, которым гейт её проверяет».
- **Fix:** `_permit_uncovered_fields` отказывает по имени и советует флаг
- **Files modified:** scripts/prohibitions_census.py
- **Verification:** `test_the_record_mode_writes_permit_scope_uncovered_only_for_a_permitted_class` (отказ «частичная строка разрешённого класса без флага»)
- **Committed in:** `a2fa9cb5`

**3. [Rule 1 - Bug] Собственный тест RED-коммита сравнивал строки несимметрично**
- **Found during:** Задача 2, GREEN
- **Issue:** `test_the_record_mode_writes_permit_scope_uncovered_only_for_a_permitted_class` снимал поле только с записанной строки. После простановки поля в реестре сравнение стало ложно красным.
- **Fix:** поле снимается с обеих сторон (`without_field`)
- **Files modified:** tests/test_planning/test_plan_prohibitions_census.py
- **Verification:** `tests/test_planning/` — 140 passed
- **Committed in:** `a2fa9cb5`

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 missing critical, 1 bug)
**Impact on plan:** все три держат согласие записи с гейтом и минимальность диффа реестра; области плана не расширяют.

## Issues Encountered

- `-k "coverage or rule_site or record"` из `<verify>` Задачи 1 не выбирает три контроля формы нескольких правил: их имена несут `multi_rule`, `one_absent_rule`, `single_rule_row`. Отбор дал `9 passed`, и контроли прогнаны отдельно (`7 passed` вместе с тестами режима записи). Второй `<verify>` (каталог целиком) их включает. Имена не менялись, чтобы улика RED ссылалась на существующий тест.
- `--disposition` в CLI ограничен `choices` (`enforced`, `partially-enforced`). Иная диспозиция в командной строке — ошибка разбора аргументов (код 2), а не `ОТКАЗ:`. Сама функция `record_coverage` отказывает по имени, и это утверждает правило режима записи.
- `--check` печатает ключей `permit*` 225 вместо 202: `permit_scope_uncovered` начинается признаком разрешения и честно им является. Это печать, не суждение.
- Флаг `--permit-uncovered` появился в CLI Задачи 1 (план перечисляет его в форме режима), но до Задачи 2 функция отказывала на нём заглушкой «ещё не объявлено». Задача 2 дала флагу смысл вместе с полем, и заглушки в дереве нет.

## Verification

- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed` (было 130; новых тестов 10).
- `uv run pytest tests/test_templates/test_htmx_inventory.py -q -p no:randomly` → `30 passed`.
- `uv run python scripts/prohibitions_census.py --check` → код 0, «реестр: 741 строк, биекция с переписью — согласие».
- `--breakdown` → сумма области решений 321; «частичных строк области решений с `permit_scope_uncovered`: 23; без поля: 9».
- `test_reconcile_seed_of_the_registry_is_idempotent_by_identity` зелен: засев не двигает ни одного поля.
- Приёмка: `grep -c 'def record_coverage'` → 1; `--help` перечисляет `--record`; `grep -c permit_scope_uncovered` в реестре → 23; `^REGISTRY_ROW_FIELDS_DECLARED = 14$` — одна строка (строка 374); дифф реестра `PLAN_BASE..HEAD` сохранён в scratchpad (`registry.diff`), 23 `-` / 23 `+`.
- Новый `import yaml` не заведён (`YAML_DIRECT_IMPORTERS` не менялся); новый импорт прибора — `ast`, stdlib.
- **Подмена полного прогона названа:** полную суиту (`just test`, ~40 мин) по указанию оркестратора запускает сам оркестратор после волны 7 (после 15-23). Здесь её заменяют каталог `tests/test_planning/` целиком и `test_htmx_inventory.py`. Окна в WINDOWS.md для этого не открыто.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-24…15-31 записывают меру покрытия одной командой `--record`. Несколько правил выражаются повторением `--rule`, и запись без правила, найденного `ast`, невозможна.
- План 15-33 (сильная форма закрывающего правила) получил машинно читаемое основание: у 23 частичных строк остаток закрыт полем, у 9 строк `product-invariant` — нет, они ждут принуждения.
- Требование `критерий-6` в REQUIREMENTS.md не отмечалось, и вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: scripts/prohibitions_census.py, tests/test_planning/test_plan_prohibitions_census.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: 586dba09, b7d0988a, e823c356, a2fa9cb5 (ledger `4df0a7f1..HEAD` = 4 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

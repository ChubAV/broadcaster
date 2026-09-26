---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 33
subsystem: planning-records
tags: [prohibitions-census, registry, closing-rule, strong-form, criterion-6, g-1, row-decisions, permit-scope-uncovered, d-05, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-13 — слабая (безусловная) форма закрывающего правила и артефакт `15-PROHIBITIONS-SUBJECT.md`; план 15-22 — `permit_scope_uncovered` и решение о частичных строках; планы 15-24…15-31 — мера покрытия режимом `--record`; план 15-32 — ответ владельца по 16 строкам (`superseded_by`, блок `row_decisions`), `unresolved` в области решений 0"
provides:
  - "закрывающее правило критерия 6 в СИЛЬНОЙ форме: ни одной строки области решений вне `DECIDED_DISPOSITIONS` (причина законной не считается), частичная — остаток закрыт разрешением класса или ответом по строке, разрешённая — не `verification: test` и с разрешением, закрывающим её"
  - "RED-цель и три контроля сильной формы на копиях живого реестра; два контроля слабой формы переписаны с летописью"
  - "`15-PROHIBITIONS-SUBJECT.md` приведён к реестру: шапка (93 / 25 / 203 / 0), свод на 2026-09-26, 117 строк таблицы, летописи находок и закрывающего утверждения"
  - "`work_addressee` класса `product-invariant` — планы 15-24…15-32 (решение Г-1) с прежним значением дословно; летопись абзаца ДИСПОЗИЦИИ в `REGISTRY_HEADER`"
affects: [phase-15-verification, критерий-6, 15-VALIDATION]

actuals:
  tokens: 31604
  tasks: 2
  commits: 3
plan_head_before: 26c47961bfeb1089d6ac963c646bcda90bec360d

tech-stack:
  added: []
  patterns:
    - "Закрывающее правило судит ДОКУМЕНТ реестра (`_document_closing_offences`): строки, ответ по классам и ответ по строкам вместе; помощник по строкам без ответа по строкам строже, а не слабее"
    - "Строку закрывает только ФОРМА — правило, разрешение класса, запись ответа владельца по строке; литерала тождества в исполняемых строках помощника нет"
    - "Летопись строки таблицы — прежний итог машинным значением (`unresolved`, причина …), чтобы человеческая метка «неразобрано —» не стояла ни в одной строке"

key-files:
  created: []
  modified:
    - tests/test_planning/test_plan_prohibitions_census.py
    - scripts/prohibitions_census.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-PROHIBITIONS-SUBJECT.md

key-decisions:
  - "15-33: частичная строка класса `require-enforcement` закрыта, если её остаток разрешён ЗАПИСЬЮ ответа владельца по строке (`permit_scope_uncovered` = тождество при записи `row_decisions`); это форма, а не исключение по тождеству. На дереве такая строка одна — `10-03#6` (ответ (а′)+(б) плана 15-32). Истина 1 плана («ни одна `partially-enforced` строка не лежит в классе с ветвью `require-enforcement`») буквально не выполнена этой строкой"
  - "15-33: частичная строка разрешённого класса также закрывается записью по строке (не только полем = класс): форма ответа владельца едина для частичной и разрешённой строки, как её уже судит `_row_decision_offences`"
  - "15-33: имя правила и имена двух переписанных контролей оставлены прежними — их цитируют `15-VALIDATION.md`, сводки и артефакт; строка `15-VALIDATION.md` не правилась (её переписывает `/gsd-validate-phase`)"
  - "15-33: летопись изменённой строки таблицы артефакта записана машинным значением (`unresolved`, причина `enforcement-required`), а не человеческой меткой — иначе критерий «`неразобрано —` в строках `| 10-` → 0» мерил бы летопись, а не итог"

patterns-established:
  - "Сильная форма правила вводится рядом со слабой: абзац слабой формы сохраняется дословно под заголовком «Летопись: …», новый абзац называет решение владельца, работу и причину сохранить имя"

requirements-completed: []

coverage:
  - id: D1
    description: "Закрывающее правило критерия 6 в сильной форме: зелено на живом реестре, красно на строке с причиной, на частичной без разрешения остатка, на разрешённой без разрешения, на засеянной копии (все 321)"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_closing_rule_of_criterion_6_every_phase_10_row_is_decided_or_names_its_reason"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_the_strong_closing_rule_reddens_on_a_reasoned_unresolved_row"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_the_strong_closing_rule_names_a_partial_row_whose_remainder_is_not_permitted"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_the_strong_closing_rule_names_a_permitted_row_without_its_permission"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_the_closing_rule_reddens_on_the_seeded_registry_and_on_a_reasonless_row"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_every_reason_is_judged_against_its_row"
        status: pass
    human_judgment: false
  - id: D2
    description: "Обоснование слабой формы сохранено дословно под «Летопись: слабая форма, план 15-13»; рядом — сильная форма, решение Г-1, решение 15-22 дословно, причина сохранить имя"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "grep -c 'Летопись: слабая форма, план 15-13' → 1; абзац «КАКАЯ ИЗ ДВУХ ФОРМ…» сличён diff'ом с `59916ec5` — побайтно равен (13 строк)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Приём строки `10-03#6` (частичная `product-invariant` с остатком, разрешённым ответом владельца по строке) сильной формой — суждение, расходящееся с буквой истины 1 плана"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_the_strong_closing_rule_names_a_permitted_row_without_its_permission (без блока `row_decisions` названы ровно `10-03#6` и `10-18#3`)"
        status: pass
    human_judgment: true
    rationale: "Принимает ли решение владельца по строке (план 15-32, ветвь (б)) частичную строку класса `require-enforcement` в сильной форме — вопрос прочтения решения Г-1; исполнитель выбрал прочтение оркестратора («lacking its permit»), судит владелец и верификатор фазы"
  - id: D4
    description: "`15-PROHIBITIONS-SUBJECT.md` и `work_addressee` приведены к реестру летописью, без стирания прежнего"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "grep -c '^| 10-' → 321; строк `| 10-` с `неразобрано —` → 0; `^status: subject` → 1; `^### Отметка` → 0; `Г-1` в реестре → 2; удалённые строки вне таблицы — только 11 строк счётчиков, у каждого прежнее значение комментарием"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_class_decision_has_the_declared_form_and_agrees_with_the_registry"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_reconcile_seed_of_the_registry_is_idempotent_by_identity"
        status: pass
    human_judgment: true
    rationale: "Верность летописных абзацев (находки 1, 3–6, закрывающее утверждение) — чтение человеком; числа сличены с `--breakdown`, слова — нет"

duration: 14min
completed: 2026-09-26
status: complete
---

# Phase 15 Plan 33: Сильная форма закрывающего правила критерия 6 и человеческий реестр, приведённый к сделанному Summary

**Правило `test_the_closing_rule_of_criterion_6_every_phase_10_row_is_decided_or_names_its_reason` теперь в сильной форме. Ни одна строка Фазы 10 не может стоять `unresolved`, даже с законной причиной. Частичная строка закрывает остаток только разрешением: классом или записью ответа владельца по строке. Разрешённая строка не может нести `verification: test` и должна нести разрешение, которое её закрывает. На живом реестре правило зелено. Три новых контроля на копиях краснеют, называя строку. Артефакт `15-PROHIBITIONS-SUBJECT.md` и адресат `product-invariant` приведены к реестру летописью.**

## Состояние критерия 6

⚠️ Одна строка не проходит по букве истины 1 плана. `10-03-PLAN.md#6` — частичная строка класса `product-invariant` (ветвь `require-enforcement`). Её остаток разрешён ответом владельца по строке (план 15-32, ветвь (б), запись `row_decisions`). Сильная форма принимает её по форме записи, а не по тождеству. Так же работает описание нарушения у оркестратора: «partially-enforced row in a class with a require-enforcement branch **lacking its permit**». Правило не ослаблено: без записи `row_decisions` эта строка названа, и контроль это утверждает. Решает владелец и верификатор (D3 в `coverage`).

Требование `критерий-6` не отмечалось, вердикт фазы не выносился. Строка `15-VALIDATION.md` для правила не правилась. ⚠️ **РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ.** 203 разрешённых запрета не принуждаются ничем, у 25 частичных принуждена только часть.

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-26T08:13:08Z
- **Completed:** 2026-09-26T08:27:09Z
- **Tasks:** 2
- **Files modified:** 4

## Предусловие

`uv run python scripts/prohibitions_census.py --breakdown` дал раздел «причины «unresolved» в области решений» пустым. Распределение: `enforced 93`, `partially-enforced 25`, `permitted 203`, сумма 321. Причины `owner-kept-open` в перечне нет: план 15-32 её не заводил, ветвь (в) не выбрана. Предусловие выполнено, сильная форма заведена.

## Сильная форма — что утверждает

`_closing_offences(rows, decisions, row_permits)`. В области решений у каждой строки:
1. диспозиция принадлежит `DECIDED_DISPOSITIONS`, и причины «неразобрано» у строки нет;
2. если строка `partially-enforced`, то `permit_scope_uncovered` равно классу при ветви `permit-class` либо тождеству строки при записи `row_decisions`;
3. если строка `permitted`, у неё нет `verification: test` (D-05, решение Г-1), а `permit_scope` равно классу при ветви `permit-class` либо тождеству при записи.

Вне области решений полей решения нет. Правило передаёт `row_permits` из блока `row_decisions`, антивакуум прежний: 321 строка и непустой блок по классам. Литерала тождества в исполняемых строках помощника нет.

## Распределение диспозиций области решений после партии (2026-09-26)

| Класс | Запретов | `test` | Ветвь | Полностью (преемником) | Частично — остаток классом | Частично — остаток строкой | Разрешено — класс | Разрешено — строка | Неразобрано |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `gate-integrity` | 61 | 10 | `permit-class` | 7 (0) | 3 | 0 | 51 | 0 | 0 |
| `live-environment-safety` | 5 | 1 | `permit-class` | 0 | 1 | 0 | 4 | 0 | 0 |
| `owner-decision-reserved` | 23 | 0 | `permit-class` | 0 | 0 | 0 | 23 | 0 | 0 |
| `plan-file-scope` | 39 | 17 | `permit-class` | 12 (0) | 5 | 0 | 22 | 0 | 0 |
| `product-invariant` | 70 | 12 | `require-enforcement` | 68 (5) | 0 | 1 | 0 | 1 | 0 |
| `record-immutability` | 22 | 5 | `permit-class` | 2 (0) | 3 | 0 | 17 | 0 | 0 |
| `requirement-flag` | 12 | 1 | `permit-class` | 0 | 1 | 0 | 11 | 0 | 0 |
| `self-certification` | 45 | 14 | `permit-class` | 3 (0) | 11 | 0 | 31 | 0 | 0 |
| `superseded-text-kept` | 20 | 0 | `permit-class` | 0 | 0 | 0 | 20 | 0 | 0 |
| `vendored-runtime-and-dependencies` | 7 | 0 | `permit-class` | 0 | 0 | 0 | 7 | 0 | 0 |
| `work-owned-elsewhere` | 17 | 1 | `permit-class` | 1 (0) | 0 | 0 | 16 | 0 | 0 |
| **Сумма** | **321** | **61** | | **93 (5)** | **24** | **1** | **202** | **1** | **0** |

Мера покрытия D-05 (61): полностью 37, частично 24, без правила 0.

## Счётчики артефакта — прежние и новые

| Поле шапки `15-PROHIBITIONS-SUBJECT.md` | 2026-09-24 (план 15-13) | 2026-09-26 (план 15-33) |
|---|---:|---:|
| `measured` | 2026-09-24 | 2026-09-26 |
| `prohibitions_milestone` / `_plans` | 697 / 156 | 741 / 175 |
| `prohibitions_fully_enforced` | 2 | 93 |
| `prohibitions_partially_enforced` | 32 | 25 |
| `prohibitions_permitted` | 202 | 203 |
| `prohibitions_unresolved_declared_rule_absent` | 27 | 0 |
| `prohibitions_unresolved_enforcement_required` | 58 | 0 |
| `prohibitions_unresolved_awaiting_owner` | 0 | 0 |
| `prohibitions_unresolved_total` | 85 | 0 |
| `enforcement_work_addressee` | не назначен | планы 15-24…15-32 (Г-1), прежнее дословно |
| новые: `…_remainder_permitted_by_class` / `_by_row`, `prohibitions_enforced_by_successor`, `permit_row_decisions` | — | 24 / 1, 5, 2 |

Прежнее значение каждого изменённого поля стоит комментарием рядом с ним. Таблица перегенерирована у 117 строк: 85 бывших `unresolved` и 32 бывших частичных. Прежний итог назван в скобках машинным значением. 204 строки генератор воспроизвёл побайтно. Это 202 строки, разрешённые классом, и 2 строки, принуждённые полностью ещё планом 15-13. Генератор — одноразовый скрипт в scratchpad, не в дереве.

## Task Commits

1. **Задача 1: сильная форма закрывающего правила**
   - `906ef532` — test(15-33): RED — RED-цель, два новых контроля, переписанные контроли, сигнатура `row_permits` (тело слабое)
   - `1de049c9` — feat(15-33): GREEN — тело сильной формы, докстринг с летописью, тест записи разрешения строки добавляет запись к живому блоку
2. **Задача 2: человеческий реестр и адресат** — `48792174` (chore)

**Plan metadata:** коммит этой сводки `docs(15-33)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute` при `workflow.tdd_mode: true`. Гейт TDD на таком плане инертен, поэтому RED назван здесь. Задача 1 (`tdd="true"`) прошла RED → GREEN отдельными коммитами.

- **RED `906ef532`.** Цель — `test_control_the_strong_closing_rule_reddens_on_a_reasoned_unresolved_row`. Команда: `uv run pytest -q -p no:randomly --junit-xml=<scratch> tests/test_planning/test_plan_prohibitions_census.py::test_control_the_strong_closing_rule_reddens_on_a_reasoned_unresolved_row`, `exit=1`. Вывод: `FAILED tests/test_planning/test_plan_prohibitions_census.py::test_control_the_strong_closing_rule_reddens_on_a_reasoned_unresolved_row`, строка `1 failed, 1 warning in 0.77s`. Причинный литерал: `assert [] == ['.planning/p...01-PLAN.md#0']` — слабая форма молчит на `10-01#0`, возвращённой в копии к `unresolved` с причиной `enforcement-required`. Запись `{command, exitCode, targetTest, output}` собрана из junit-xml в форме node:test TAP одноразовым `junit2red.py` (scratchpad, не в дереве). `check tdd-red-evidence` дал `RED_EVIDENCE_OK / target_test_failed`. В том же коммите на assertion'ах сильной формы красны ещё четыре теста, не упав ни на импорте, ни на фикстуре. Это два новых контроля и два переписанных. Их литералы: `assert [] == ['.planning/p...01-PLAN.md#0']` ×2, `assert [] == ['.planning/p...36-PLAN.md#1']` и синтетика `range(4, 10)` против `(0,1,2,4…9)`. Уликой они не заявлены. Остальные 203 теста каталога зелены.
- **GREEN `1de049c9`.** `-k "closing or strong or reason"` → `6 passed`; `tests/test_planning/` → `208 passed`.
- REFACTOR не было.

## Files Created/Modified

- `tests/test_planning/test_plan_prohibitions_census.py` — `_closing_offences` в сильной форме с летописью слабой; `_document_closing_offences`, `_named`; докстринг правила (сильная форма, решение 15-22 дословно, «Летопись: слабая форма, план 15-13» с абзацем того дня дословно); 3 новых теста; 2 переписанных контроля; 3 вызова переведены на помощник документа.
- `scripts/prohibitions_census.py` — летопись абзаца ДИСПОЗИЦИИ в `REGISTRY_HEADER`.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — шапка (по `REGISTRY_HEADER`) и `work_addressee` решения `product-invariant`.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-PROHIBITIONS-SUBJECT.md` — шапка, летописи разделов, свод на 2026-09-26, 117 строк таблицы.

## Decisions Made

См. `key-decisions`. Главное — прочтение истины 1 для `10-03#6`, раздел «Состояние критерия 6».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Тест записи разрешения строки ЗАМЕНЯЛ живой блок `row_decisions` одной синтетической записью**
- **Found during:** Задача 1, GREEN
- **Issue:** `test_the_record_mode_writes_a_row_permission_only_with_its_record` ставил `answered[ROW_DECISIONS_KEY] = [_row_permit(identity)]`. Живые записи `10-03#6` и `10-18#3` пропадали. Слабая форма этого не видела, сильная назвала обе строки.
- **Fix:** синтетическая запись добавляется к живому блоку. Летопись записана рядом.
- **Files modified:** `tests/test_planning/test_plan_prohibitions_census.py`
- **Verification:** `tests/test_planning/` — 208 passed
- **Committed in:** `1de049c9`

**2. [Rule 3 - Blocking] Два теста режима записи звали закрывающий помощник без ответа по строкам**
- **Found during:** Задача 1, RED (до коммита)
- **Issue:** `test_the_record_mode_writes_only_what_the_tree_proves` и тест записи разрешения строки звали `_closing_offences(rows, decisions)` на полной копии реестра. В сильной форме без `row_permits` они назвали бы `10-03#6` и `10-18#3`.
- **Fix:** переведены на `_document_closing_offences(document)`, который передаёт ответ по строкам.
- **Committed in:** `906ef532`

**3. [Rule 1 - Bug] Летопись строки таблицы нарушала бы критерий приёмки**
- **Found during:** Задача 2
- **Issue:** первая генерация писала прежний итог человеческой меткой (`было: «неразобрано — …»`). Критерий `grep -c 'неразобрано —'` по строкам `| 10-` дал бы 85 вместо 0.
- **Fix:** файл восстановлен `git checkout` и перегенерирован. Прежний итог теперь записан машинным значением (`было на 2026-09-24, план 15-13: \`unresolved\`, причина \`enforcement-required\``).
- **Committed in:** `48792174`

### Отклонения от буквы плана (не авто-правки)

- **Истина 1 / критерий приёмки 3, «`partially-enforced` только в разрешённых классах»,** буквально не выполнены одной строкой — `10-03-PLAN.md#6`. Разбор — раздел «Состояние критерия 6». Исключения по тождеству в правиле нет. Правило не ослаблено относительно ответа владельца.
- **Критерий `grep -c '### Отметка'` → `0`:** без якоря даёт `2`, как и на `HEAD` до плана. Оба вхождения — цитаты формулировок запретов в ячейках таблицы (`10-34#0`, `10-54#2`), а не заголовки. С якорем, в форме плана 15-13, `grep -c '^### Отметка'` → `0`.
- **«Закрыто планами 15-15…15-32 (2026-09-25)»:** в артефакте написано «(2026-09-25 — 2026-09-26)», потому что план 15-32 закрыт 2026-09-26.
- **Происхождение 24-й частичной строки разрешённого класса:** докстринг правила сначала назвал план 15-30. По `git log -S` это план 15-31 (`7a3f73e5`), исправлено до коммита `1de049c9`.

---

**Total deviations:** 3 auto-fixed (2 bug, 1 blocking) и 4 названных отклонения от буквы
**Impact on plan:** правило не ослаблено ни одной правкой. Два фикса делают тесты верными к живому ответу владельца. Область файлов плана не расширена.

## Issues Encountered

- `ruff` в окружении не установлен (прецедент 15-30…15-32), линтер не прогонялся.
- `graphify update .` выполнен, каталог `graphify-out/` в дереве не отслеживается.

## Verification

- `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k "closing or strong or reason"` → `6 passed, 103 deselected`.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `208 passed` (было 205, новых тестов 3) на итоговом дереве `48792174`.
- `uv run pytest tests/test_templates/test_htmx_inventory.py -q -p no:randomly` → `30 passed`.
- `--check` → код 0, «реестр: 741 строк, биекция с переписью — согласие». `--breakdown` → код 0, `unresolved` в области решений 0, сумма 321. `--seed-registry` → «реестр не изменился», `cmp` побайтно равен.
- Нового `import yaml` нет, `YAML_DIRECT_IMPORTERS` не менялся. `git diff 26c47961..HEAD -- app/ '.planning/phases/*/*-PLAN.md'` пуст. Ни один `*-PLAN.md` и ни один дескриптор исполненного плана не правился.
- **Подмена полного прогона названа.** Полную суиту (`just test`) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют `tests/test_planning/` целиком и `test_htmx_inventory.py`. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Все 33 плана Фазы 15 исполнены. Дальше повторная верификация фазы оркестратором. Гэп критерия 6 (б) закрыт работой, кроме прочтения `10-03#6`: его решают владелец и верификатор.
- Строку `15-VALIDATION.md` для закрывающего правила переписывает `/gsd-validate-phase`.
- Требование `критерий-6` не отмечалось.

## Self-Check: PASSED

- FOUND: все четыре файла `key-files.modified`
- FOUND commits: 906ef532, 1de049c9, 48792174 (ledger `26c47961..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-26*

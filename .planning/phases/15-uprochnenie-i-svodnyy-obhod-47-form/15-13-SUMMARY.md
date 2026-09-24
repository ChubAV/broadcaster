---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 13
subsystem: planning-records
tags: [prohibitions, census, registry, yaml, ast, dispositions, coverage, owner-decision, criterion-6]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-01: прибор переписи, реестр на 697 строк, группа D-05; план 15-12: 11 классов, четыре диспозиции, ответ владельца по классам (блок `class_decisions`)"
  - phase: 10-rychag-components-modal-html
    provides: "321 запрет Фазы 10 (область решений D-02); образец `10-PROHIBITIONS-SUBJECT.md` (шапка `status: subject`, мера покрытия по форме `:118-160`)"
provides:
  - "диспозиция у каждого из 321 запрета Фазы 10: 2 полностью, 32 частично, 202 разрешено, 85 неразобрано с названной причиной (27 `declared-rule-absent`, 58 `enforcement-required`)"
  - "мера покрытия по 61 запрету с `verification: test`: имя правила, координата по `ast`, непокрытая часть у частичных"
  - "закрывающее утверждение критерия 6 в безусловной форме: ни одной строки «неразобрано» без причины из `UNRESOLVED_REASONS`, согласной со строкой"
  - "артефакт `15-PROHIBITIONS-SUBJECT.md`: шапка `status: subject` с полями `permit_*` и `prohibitions_fully_enforced`, таблица сличения, построчная таблица на 321 запрет, шесть находок"
affects: [15-14, phase-15-verification, criterion-6]

actuals:
  tokens: 81710
  tasks: 3
  commits: 3
plan_head_before: aff6bd0636c9b4be7bfd4ae02f22727c0679ddff

tech-stack:
  added: []
  patterns:
    - "мера покрытия — человеческое суждение, записанное полем; машина утверждает форму записи и существование правила в файле координаты разбором `ast`"
    - "координата правила снимается `ast`, а не набирается; номер строки — координата дня замера и не утверждается"
    - "нетерминальность строки — отрицание принадлежности `DECIDED_DISPOSITIONS`, причина — из перечня и согласна со строкой"
    - "человеческий артефакт генерируется из реестра и переписи, поэтому расходиться с машинной половиной ему нечем"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-PROHIBITIONS-SUBJECT.md
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-13-SUMMARY.md
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
    - tests/test_planning/test_plan_prohibitions_census.py
    - scripts/prohibitions_census.py

key-decisions:
  - "Мера покрытия по 61 запрету с `verification: test` снята чтением предмета запрета и предмета правила: 2 полностью, 32 частично, 27 без правила. По подмножеству образца (25 записей 10-35…10-40) счёт тот же, что у образца: 0 / 8 / 17"
  - "У 61 диспозиции «разрешено» не стоит ни одной (D-05). 26 находок без правила лежат в разрешённых классах, разрешение класса их не закрывает"
  - "Причины «неразобрано» — перечень из трёх: `declared-rule-absent`, `enforcement-required`, `awaiting-owner-decision`. Последняя сегодня не стоит ни у одной строки: ответ получен по всем 11 классам"
  - "Сильная форма закрытия («ни одного `unresolved`») не заведена, хотя все классы ответили: ответ по `product-invariant` — `require-enforcement`, а находки D-05 разрешением не закрываются. Выбрана безусловная форма; это объявлено в докстринге правила"
  - "Поле `uncovered_part` (объявлено планом 15-12 заранее) переименовано в `coverage_note` по плану 15-13 с летописью; ни одна строка прежнего имени не несла"
  - "Добавлено поле `rule_name` сверх перечня плана: без имени координата не даёт предъявить существование правила разбором `ast`"

patterns-established:
  - "Строка «принуждается» несёт имя и координату правила, строка «частично» — ещё и непокрытую часть; у прочих диспозиций этих полей нет"
  - "Поля решения строки стоят только в области решений; вне её — ни одного (D-02 принадлежностью)"

requirements-completed: ["критерий-6"]

coverage:
  - id: D1
    description: "Мера покрытия по 61 запрету с `verification: test`: 2 полностью, 32 частично с названной непокрытой частью, 27 без правила. Существование правила — по `ast` в файле координаты, «разрешено» у 61 не стоит ни у одной строки"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_phase_10_declared_test_exists_or_is_recorded_absent"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_coverage_rule_exists_at_its_site_by_the_tree"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_partially_enforced_disposition_names_its_uncovered_part"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_coverage_rule_absent_from_its_site_is_named"
        status: pass
    human_judgment: false
  - id: D2
    description: "Диспозиция у всех 321 запрета; «неразобрано» только с причиной из перечня, согласной со строкой; «разрешено» только с `permit_scope` именем класса; закрывающее правило красно до работы и зеленеет работой"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_closing_rule_of_criterion_6_every_phase_10_row_is_decided_or_names_its_reason"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_the_closing_rule_reddens_on_the_seeded_registry_and_on_a_reasonless_row"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_permitted_disposition_carries_its_class_as_permit_scope"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --breakdown → «сумма по диспозициям области решений: 321»"
        status: pass
    human_judgment: false
  - id: D3
    description: "Артефакт `15-PROHIBITIONS-SUBJECT.md`: `status: subject` без полей вердикта, 321 строка таблицы, сличение названного с измеренным, находки; вне вселенной правила самозаверения"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "grep -c '^status: subject' → 1; grep -c '^### Отметка' → 0; grep -c '^| 10-' → 321"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_the_walkthrough_cannot_self_certify.py#test_the_declared_vocabularies_and_exemptions_agree"
        status: pass
    human_judgment: false
  - id: D4
    description: "Верность каждого итога меры покрытия (полностью / частично / нет правила) и формулировка непокрытой части — человеческое суждение"
    verification: []
    human_judgment: true
    rationale: "По плану (задача 1, D-33) сравнение предмета запрета с предметом правила машиной не выводится; гейт утверждает форму и существование, а не верность суждения. Проверяет человек по колонкам «Итог» и «Непокрытая часть» артефакта"

duration: 17min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 13: Диспозиции 321 запрета Фазы 10 и закрывающее утверждение критерия 6 Summary

**Каждый из 321 запрета Фазы 10 получил диспозицию. По 61 запрету с `verification: test` мера покрытия снята чтением: 2 полностью, 32 частично с названной непокрытой частью, 27 без правила (находка D-05). 202 запрета разрешены по ответу владельца с `permit_scope` именем класса. 58 запретов `product-invariant` остаются открытыми по его решению. Закрывающее правило: «неразобрано» только с причиной из перечня. Человеческий реестр — `15-PROHIBITIONS-SUBJECT.md`.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-24T17:40:50Z
- **Completed:** 2026-09-24T17:57:50Z
- **Tasks:** 3
- **Files modified:** 4 (реестр, модуль теста, прибор, новый артефакт), плюс эта сводка

## Распределение диспозиций по классам (область решений, Фаза 10)

| Класс | Запретов | `test` | Ответ владельца | Полностью | Частично | Разрешено | Неразобрано: нет правила | Неразобрано: требуется принуждение |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `gate-integrity` | 61 | 10 | `permit-class` | 0 | 3 | 51 | 7 | 0 |
| `live-environment-safety` | 5 | 1 | `permit-class` | 0 | 0 | 4 | 1 | 0 |
| `owner-decision-reserved` | 23 | 0 | `permit-class` | 0 | 0 | 23 | 0 | 0 |
| `plan-file-scope` | 39 | 17 | `permit-class` | 0 | 5 | 22 | 12 | 0 |
| `product-invariant` | 70 | 12 | `require-enforcement` | 2 | 9 | 0 | 1 | 58 |
| `record-immutability` | 22 | 5 | `permit-class` | 0 | 3 | 17 | 2 | 0 |
| `requirement-flag` | 12 | 1 | `permit-class` | 0 | 1 | 11 | 0 | 0 |
| `self-certification` | 45 | 14 | `permit-class` | 0 | 11 | 31 | 3 | 0 |
| `superseded-text-kept` | 20 | 0 | `permit-class` | 0 | 0 | 20 | 0 | 0 |
| `vendored-runtime-and-dependencies` | 7 | 0 | `permit-class` | 0 | 0 | 7 | 0 | 0 |
| `work-owned-elsewhere` | 17 | 1 | `permit-class` | 0 | 0 | 16 | 1 | 0 |
| **Сумма** | **321** | **61** | 11 из 11 | **2** | **32** | **202** | **27** | **58** |

⚠️ **РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ.** Полностью принуждены правилами 2 запрета из 321, и ни один — разрешением. В артефакте `prohibitions_fully_enforced: 2` стоит отдельно от `prohibitions_permitted: 202`.

Полностью принуждены:
- `10-49#3` — `test_the_failure_banner_guard_lives_on_the_node_it_wires`;
- `10-50#2` — `test_the_ad_summary_markup_has_exactly_one_source`.

## Находка фазы: 27 запретов объявили `verification: test`, а правила нет

Записаны диспозицией `unresolved` с причиной `declared-rule-absent`, а не разрешением. 26 из них лежат в разрешённых классах: по D-05 разрешение класса их не закрывает.

`10-36#1`, `10-36#2`, `10-36#3`, `10-37#0`, `10-37#3`, `10-37#5`, `10-38#1`, `10-38#2`, `10-38#3`, `10-38#5`, `10-39#2`, `10-39#4`, `10-39#5`, `10-40#1`, `10-40#2`, `10-40#3`, `10-40#4`, `10-44#2`, `10-44#5`, `10-46#3`, `10-48#3`, `10-48#4`, `10-49#4`, `10-50#3`, `10-50#4`, `10-51#0`, `10-51#1`.

Три из них стоит назвать отдельно:
- `10-36#1` объявляет имя `test_control_a_missing_anchor_is_named_by_the_rule`. Имя в суите есть, но это жертва запрета, а не его сторож.
- `10-38#1`: буква опровергнута деревом и сегодня. Ввоз `_template_chain` стоит в `tests/test_pages/test_shell.py:8054`.
- `10-37#5` и `10-51#1`: литерал слоя стоит в исполняемом коде правил, `test_shell.py:6789` и `:7402`.

## Классы без ответа владельца

**Ни одного: 0 классов, 0 запретов.** Ответ получен по всем 11 классам (план 15-12). Причина `awaiting-owner-decision` объявлена в перечне, но сегодня не стоит ни у одной строки.

## Закрывающее утверждение: какая форма выбрана и почему

Выбрана **безусловная форма**. Правило `test_the_closing_rule_of_criterion_6_every_phase_10_row_is_decided_or_names_its_reason` утверждает:
- каждая строка области решений либо решена (`enforced`, `partially-enforced`, `permitted`), либо несёт причину из `UNRESOLVED_REASONS`;
- причина согласна со строкой: `declared-rule-absent` только при `verification: test`, `enforcement-required` только у класса `require-enforcement`, `awaiting-owner-decision` только у класса без ответа;
- вне области решений полей решения нет.

**Сильная форма («ни одного `unresolved`») не заведена, хотя все классы ответили.** Причины:
- владелец ответил `require-enforcement` по `product-invariant`, то есть сам оставил класс открытым;
- по D-05 находки без правила разрешением не закрываются.

Сильная форма стояла бы красной на законном дереве. Критерий 6 закрыт настолько, насколько получены ответы и написаны правила. Остаток — **85** (27 + 58). Он назван в артефакте и в этой сводке, но ни в одном `assert` не стоит. Докстринг правила говорит это прямо.

## Проверка направления краснения

| Состояние | Результат |
|---|---|
| Живой реестр ДО задачи 2 (после задачи 1: причин и разрешений нет) | **красно**, 287 нарушений; отказ доложил распределение по всем четырём диспозициям по классам |
| После задачи 2 | **зелено** |
| Мутация файла A: одна строка `permitted` → `unresolved` без причины | **красно**, 1 нарушение, названо тождество `10-01#7` |
| Мутация файла B: у одной строки `enforcement-required` снята причина | **красно**, 1 нарушение, `10-01#0` |
| Файл восстановлен | `cmp` — побайтно тот же, правило зелено |
| Контроль суиты: засеянная копия («возврат работы назад») | красно на всех 321 строке, работу назад не зеленит |
| Контроль суиты: несогласная причина; поле решения вне области | названа ровно одна строка |

## Сличение с формулировками плана

Прежние числа плана не переписывались. Замеры записаны рядом:
- **«329 вне области решений»** снято до планов Фазы 15. Сегодня вне области **376** (697 − 321): планы Фазы 15 входят в область прибора по построению. Ни одно правило ни одного из двух чисел не утверждает.
- **«582 / 24 / 13» по вехе** совпадает на вселенной без Фазы 15; 31 элемент Фазы 07 не несёт `status`, и вместе сумма равна 650. С Фазой 15 первое число — **629**.
- **Уникальность «299 из 321»** (15-CONTEXT.md) не воспроизведена ни одной из пяти нормализаций: 314 / 314 / 291 / 281 / 311. Повторы покрывают 12 запретов, а не 35.
- **«76 − 61 = 15 — соседние блоки»**: разбивка 10 + 0 + 1 + 4, где 5 — проза. Эта поправка плана 15-01 не менялась.
- **«Существование правила по полю `declared_rule`»**: только 2 из 61 запретов объявляют имя, у 59 стоит `<undeclared>`. Правило для каждого найдено чтением: индекс имён функций по `ast` плюс сводки планов Фазы 10. Существование утверждается по `ast` в файле координаты.

## Accomplishments

- Мера покрытия по 61 запрету записана полями `rule_name`, `rule_site`, `coverage_note`. Правила формы, существования по `ast` и «ни одного разрешения у D-05» с контролями.
- Диспозиции у всех 321 запрета, причины «неразобрано» и `permit_scope` именем класса. Закрывающее правило критерия 6, правило области разрешения, две синтетические группы контролей и контроль направления на копиях живого реестра.
- `15-PROHIBITIONS-SUBJECT.md` сгенерирован из реестра и переписи: 321 строка таблицы, 27 находок, сличение из восьми строк.
- `--breakdown` печатает диспозиции области решений по классам, причины и меру покрытия D-05.
- Модуль вырос с 53 правил до 64; `tests/test_planning/` вырос с 97 до 108.

## Task Commits

1. **Задача 1: мера покрытия по 61 запрету** — `2ac7d7b5` (test)
2. **Задача 2: диспозиции и закрывающее правило критерия 6** — `59916ec5` (feat)
3. **Задача 3: человеческий реестр `15-PROHIBITIONS-SUBJECT.md`** — `b9008a6f` (docs)

**Plan metadata:** коммит сводки и коммит трекинга следуют за этим файлом.

## Files Created/Modified

- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml`: поля решения у 321 строки Фазы 10. Шапка дополнена абзацем о диспозициях, первая фраза абзаца о полях разрешения дополнена летописью.
- `tests/test_planning/test_plan_prohibitions_census.py`:
  - `REGISTRY_ROW_FIELDS` 8 → 13 с летописью;
  - `COVERED_DISPOSITIONS`, `DECIDED_DISPOSITIONS`, `UNRESOLVED_REASONS` (3);
  - `_coverage_offences`, `_rule_site_offences`, `_closing_offences`, `_permit_scope_offences`, `_disposition_distribution`;
  - 11 новых правил и контролей.
- `scripts/prohibitions_census.py`: порядок новых полей, текст шапки реестра, разделы `--breakdown`.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-PROHIBITIONS-SUBJECT.md`: новый артефакт.

## Decisions Made

См. `key-decisions`. Главное: безусловная форма закрытия с тремя причинами, согласными со строкой, и мера покрытия как записанное суждение. Существование правила по `ast` проверяется в файле координаты, номер строки не утверждается.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Имя поля непокрытой части: `uncovered_part` → `coverage_note`**
- **Found during:** задача 1
- **Issue:** план 15-12 заранее объявил поле как `uncovered_part`. План 15-13 называет его `coverage_note`, и его проверка (`grep -c 'coverage_note'`) ищет именно это имя.
- **Fix:** константа `UNCOVERED_PART_FIELD` получила значение `coverage_note`, прежнее имя названо летописью. Ни одна строка прежнего имени не несла.
- **Committed in:** `2ac7d7b5`

**2. [Rule 3 - Blocking] Критерий `grep -c 'in source'` → 0 был красен до работы**
- **Found during:** задача 1
- **Issue:** 3 ложных вхождения давал обход словаря вида `… in sources.items()` в прежнем коде модуля.
- **Fix:** параметр отображения переименован в `suite` / `plan_texts`, поведение не изменилось. Критерий теперь меряет то, что задумано: существование не проверяется вхождением подстроки.
- **Committed in:** `2ac7d7b5`

**3. [Rule 2 - Missing critical] Поле `rule_name` сверх перечня плана**
- **Found during:** задача 1
- **Issue:** план требует `rule_site` («путь:строка») и существование имени по `ast`, но имени правила не хранит нигде: `declared_rule` у 59 из 61 равно `<undeclared>`.
- **Fix:** добавлено поле `rule_name`. Существование судится по `ast` файла из координаты: имя из чужого файла не засчитывается. Номер строки не утверждается, иначе правило краснело бы на любой правке файла выше определения. Это касается и трёх строк, указывающих в сам модуль переписи.
- **Committed in:** `2ac7d7b5`, координаты пересняты в `59916ec5`

**4. [Rule 2 - Missing critical] Правка `scripts/prohibitions_census.py` (нет в `files_modified`)**
- **Found during:** задачи 1-2
- **Issue:**
  - проверка задачи требует в `--breakdown` сумму диспозиций по области решений, а прибор печатал только вехе целиком;
  - первая фраза шапки реестра («полей разрешения в СТРОКАХ исполнитель не пишет») стала бы неправдой после задачи 2.
- **Fix:**
  - разделы `--breakdown` добавлены;
  - шапка дополнена по идиоме D-30/D-32: прежняя формулировка процитирована, а не стёрта;
  - добавлен порядок новых полей для воспроизводимого засева.
- **Committed in:** `2ac7d7b5`, `59916ec5`

**5. [Rule 1 - Bug] Числа плана, пережившие свой замер**
- **Found during:** задачи 2-3
- **Issue и Fix:** «329», «582 / 24 / 13», «299», «61 по `declared_rule`» — замеры записаны рядом, слова плана не правились (см. «Сличение с формулировками плана»).

---

**Total deviations:** 5 auto-fixed (1 Rule 1, 2 Rule 2, 2 Rule 3)
**Impact on plan:** все поправки нужны, чтобы проверки плана меряли задуманное, а запись оставалась правдивой. Область решений не расширена. Разрешений без ответа владельца нет.

## TDD Gate Compliance

План `type: execute`, задачи `type="auto"` без `tdd="true"`, поэтому RED/GREEN-гейты к нему не применяются. Задача 1 закоммичена типом `test`: её предмет — правила записи и реестр, а не поведение продукта. Правила написаны вместе с записью. Их зубы показаны синтетическими контролями и прогоном закрывающего правила на реестре до работы: красно, 287 нарушений.

## Issues Encountered

- `requirements.ready-ids` (только чтение) для `критерий-6`: «1/1 requirement(s) ready to mark complete». `requirements.mark-complete` не вызывался по указанию оркестратора: ID фазы 15 остаются Pending до верификации. Кроме того, `критерий-6` не является ID `REQUIREMENTS.md`.
- `ruff` в окружении не установлен. `python -m compileall -q scripts tests/test_planning` проходит молча.

## Вопросы владельцу (не решены исполнителем)

1. **Адресат работы по `product-invariant` не назначен.** Долг — 68 запретов, не принуждённых целиком: 58 без правила по вашему требованию, 1 находка D-05 (`10-50#3`), 9 частично. План говорит только «будущие фазы», а фазу вы не назвали. Нужен номер фазы или вехи.
2. **Адресат 376 запретов вне Фазы 10 не назначен** (D-02). Назначить его можно при планировании следующей вехи.
3. **27 находок D-05** требуют решения: писать правила или снять дескриптор `test`. Снимать его в исполненных планах запрещено их же запретами, так что форма решения — за вами.

## Known Stubs

Нет. 85 строк `unresolved` — не заглушки, а записанный остаток с названной причиной. Их число названо в артефакте.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Половина (б) критерия 6 закрыта в безусловной форме. Остаток 85 назван причинами, вопросы адресата переданы владельцу.
- План 15-14 обещает полную суиту. `tests/test_planning/` на закоммиченном дереве задачи 3: 108 passed.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `15-PROHIBITIONS-SUBJECT.md`, `15-13-SUMMARY.md`, `15-prohibitions-registry.yaml`, `tests/test_planning/test_plan_prohibitions_census.py`, `scripts/prohibitions_census.py`
- FOUND: `2ac7d7b5`, `59916ec5`, `b9008a6f`
- `git rev-list --count aff6bd06..HEAD` → 3 до коммита сводки
- `tests/test_planning/` → 108 passed на закоммиченном дереве задачи 3

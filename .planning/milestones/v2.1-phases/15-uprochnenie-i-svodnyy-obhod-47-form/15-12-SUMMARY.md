---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 12
subsystem: planning-records
tags: [prohibitions, census, registry, yaml, classes, dispositions, owner-decision, criterion-6]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-01 — прибор переписи `scripts/prohibitions_census.py`, реестр тождеств на 697 строк, перечень диспозиций из трёх значений, группа D-05"
  - phase: 10-rychag-components-modal-html
    provides: "321 запрет Фазы 10 (область решений D-02); образец `10-PROHIBITIONS-SUBJECT.md` — форма полей `permit_*` и построчная таблица с итогом «принуждается частично»"
provides:
  - "перечень диспозиций из четырёх значений (`enforced`, `partially-enforced`, `permitted`, `unresolved`), `DISPOSITIONS_DECLARED = 4` с летописью 3 → 4"
  - "перечень 11 классов предмета `PROHIBITION_CLASSES`; поле `class` записано у всех 321 запрета Фазы 10, у 376 строк вне области осталось `unclassified`"
  - "режим `--draft-classes` (все кандидаты, только для человека) и разбивка `--breakdown` по классам с ветвью ответа владельца"
  - "блок реестра `class_decisions` — ответ владельца по каждому из 11 классов, записанный полями (10 разрешений с `permit_scope` = имя класса, одно решение `require-enforcement`)"
affects: [15-13, phase-15-verification, criterion-6]

actuals:
  tokens: 29456
  tasks: 3
  commits: 3
plan_head_before: bdb1a804daa21c1af1e6e3d6d1d7948cc1fe09ed

tech-stack:
  added: []
  patterns:
    - "класс — записанное поле реестра, а не вывод в момент прогона; черновик ключевыми словами гейт не зовёт (проверяется разбором `ast` модуля)"
    - "ответ владельца — отдельный блок документа реестра после шапки замера; засев его переносит, но не пишет"
    - "решение, не являющееся разрешением, записано полями без признака `permit` в имени"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-12-SUMMARY.md
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
    - scripts/prohibitions_census.py
    - tests/test_planning/test_plan_prohibitions_census.py

key-decisions:
  - "Перечень диспозиций расширен до четырёх значений по замеру образца `10-PROHIBITIONS-SUBJECT.md:118-160`. Число поднято летописью 3 → 4. Частичная диспозиция обязана называть непокрытую часть полем `uncovered_part`"
  - "11 классов предмета выведены чтением всех 321 формулировки. Поле записано один раз; гейт утверждает полноту разнесения, а не его правильность (D-33 не переоткрыт)"
  - "Ответ владельца `chubav` 2026-09-24 по классам: `product-invariant` (70) → `require-enforcement`; остальные десять классов (251) → `permit-class`; `row-by-row` не выбран ни для одного класса. Основания своими словами владелец не дал"
  - "Ответ записан блоком документа `class_decisions`, а не в строки: засев оставляет в документе только `measured`/`rows_declared`/`rows`. Засев переносит блок; число ключей документа поднято 3 → 4 с летописью"
  - "Адресат работы по `product-invariant` не назначен. План называет только «будущие фазы» без номера, владелец фазу тоже не назвал; так и записано в поле `work_addressee`"

patterns-established:
  - "Форма ответа владельца по классу судится принадлежностью объявленной форме полей и согласием объявленного числа с реестром — а не числом разрешённых классов"
  - "Разрешение класса несёт оба флага распространения `false`: область — класс, а не фаза и не веха"

requirements-completed: ["критерий-6"]

coverage:
  - id: D1
    description: "Перечень диспозиций из четырёх значений с определением каждого. Летопись 3 → 4 с оговоркой «ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ». Рядом процитировано «РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ». Частичная диспозиция требует `uncovered_part`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_disposition_vocabulary_declares_four_values_with_the_partial_one"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_control_a_partial_disposition_without_the_uncovered_part_is_named"
        status: pass
    human_judgment: false
  - id: D2
    description: "Класс записан полем у всех 321 запрета Фазы 10 (11 классов, сумма 321). Вне области решений — `unclassified`, это утверждается принадлежностью. Правило `statement_digest` ловит правку формулировки. Гейт черновик не зовёт"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_row_class_is_complete_for_the_decision_scope"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_the_gate_never_calls_the_draft_classifier"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --breakdown → «сумма по классам области решений: 321 (классов 11)»"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ответ владельца записан полями блока `class_decisions`: 10 разрешений (`permit_scope` = имя класса, флаги распространения false), одно `require-enforcement` (70). Форма и число судятся правилами; строки «разрешено» без разрешения класса называются"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_every_class_decision_has_the_declared_form_and_agrees_with_the_registry"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py#test_no_row_is_permitted_unless_its_class_was_permitted"
        status: pass
      - kind: other
        ref: "grep -c 'permit_scope' 15-prohibitions-registry.yaml → 10 (число разрешённых классов); grep -c 'prohibitions_fully_enforced' → 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "Верность отнесения каждого из 321 запрета к своему классу — человеческое суждение. Гейт утверждает только полноту разнесения"
    verification: []
    human_judgment: true
    rationale: "По плану (must_haves.truths, D-33) верность класса машинно не судится; её проверяет человек чтением `--list --phase 10 --class NAME`"

duration: 37min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 12: Классы предмета запретов и ответ владельца по классам Summary

**321 запрет Фазы 10 разнесён по 11 классам: класс записан полем реестра, а не выводится регулярным выражением. Перечень диспозиций расширен до четырёх значений по замеру образца. Ответ владельца по каждому классу записан полями: `product-invariant` (70) — требовать принуждения, остальные десять классов (251) — разрешить класс.**

## Performance

- **Duration:** 37 min, включая ожидание ответа владельца на чекпойнте
- **Started:** 2026-09-24T16:19:15Z
- **Completed:** 2026-09-24T16:56Z
- **Tasks:** 3 (задачи 1-2 исполнил первый агент, задачу 3 — агент-продолжатель после чекпойнта)
- **Files modified:** 3 (реестр, прибор, модуль теста), плюс эта сводка

## Перечень классов (область решений, Фаза 10)

| Класс | Запретов | Из них `verification: test` | Ответ владельца |
|---|---:|---:|---|
| `product-invariant` | 70 | 12 | `require-enforcement` |
| `gate-integrity` | 61 | 10 | `permit-class` |
| `self-certification` | 45 | 14 | `permit-class` |
| `plan-file-scope` | 39 | 17 | `permit-class` |
| `owner-decision-reserved` | 23 | 0 | `permit-class` |
| `record-immutability` | 22 | 5 | `permit-class` |
| `superseded-text-kept` | 20 | 0 | `permit-class` |
| `work-owned-elsewhere` | 17 | 1 | `permit-class` |
| `requirement-flag` | 12 | 1 | `permit-class` |
| `vendored-runtime-and-dependencies` | 7 | 0 | `permit-class` |
| `live-environment-safety` | 5 | 1 | `permit-class` |
| **Сумма** | **321** | **61** | 11 классов; 12 классов и больше не понадобилось |

Число классов (11) лежит в границе обозримости 5-12, поэтому находки «больше двенадцати» нет.

## Улика разнесения: `--draft-classes`

Черновик ключевыми словами печатает ВСЕ классы-кандидаты. Вывод детерминирован:

| Кандидатов на запрет | Запретов |
|---:|---:|
| 0 | 15 |
| 1 | 154 |
| 2 | 111 |
| 3 | 34 |
| 4 | 5 |
| 5 | 2 |

- Многозначных (кандидатов 2 и больше): **152**. Без кандидата: **15**.
- Записанный класс входит в кандидаты черновика у **281 из 321**. Остальные 40 разнесены чтением формулировки.
- Эти числа нельзя сравнивать с 139/64 из Ф-04: там была восьмиклассовая сеть с другими образцами.
- Гейт черновик не зовёт. Правило `test_the_gate_never_calls_the_draft_classifier` проверяет это разбором `ast` модуля.

## Летопись поднятия `DISPOSITIONS_DECLARED` (задача 1)

Текст летописи в модуле теста (`tests/test_planning/test_plan_prohibitions_census.py`, над `DISPOSITIONS`) дословно:

> ЛЕТОПИСЬ ЧИСЛА: 3 → 4, план 15-12, задача 1. План 15-01 объявил перечень `frozenset({"enforced", "permitted", "unresolved"})` и `DISPOSITIONS_DECLARED = 3` — по схеме, которую разведка (15-RESEARCH.md Ф-03) набросала сама и сама назвала наброском. ЧЕМ СНЯТО ЧЕТВЁРТОЕ ЗНАЧЕНИЕ — ЗАМЕРОМ, а не вкусом: построчная таблица действующего образца `10-PROHIBITIONS-SUBJECT.md:118-160` (39 запретов седьмой партии) применяет итог «принуждается частично», и среди записей, у которых правило вообще есть, он единственный: свод образца по 25 записям с дескриптором `test` даёт «принуждается» 0, «принуждается частично» 8, «не принуждается» 17. […] ⚠️ ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей записи он был верным, и правится не он, а числа, которые он пережил.

Определение четвёртого значения: **`partially-enforced`** («принуждается частично») означает, что правило есть, но покрывает только часть предмета. Непокрытая часть названа полем строки реестра `uncovered_part`, а не подразумевается. Рядом с перечнем процитировано «⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ».

## Вопрос владельцу (задача 3) — дословно

> Запреты Фазы 10 (321) разнесены по 11 классам предмета; каждый запрет записан в реестр со своим классом. По каждому классу назовите ветвь: `permit-class` (разрешить класс), `require-enforcement` (требовать принуждения) или `row-by-row` (разобрать построчно). Можно одной строкой на несколько классов с одинаковой ветвью. Если отвечать сейчас не нужно — скажите; классы без ответа останутся «неразобрано» с причиной «ожидает решения владельца».

Оркестратор задал вопрос вместе с таблицей всех 11 классов: число запретов, число с `verification: test`, примеры формулировок. К таблице шли описания трёх ветвей плана, включая «⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ».

## Ответ владельца — полями

Ответ получен через AskUserQuestion 2026-09-24T16:45Z в `/gsd-execute-phase 15`. Отвечал `chubav`, владелец проекта.

Владелец **выбрал вариант**. Формулировка варианта принадлежит **оркестратору, а не владельцу**. Дословно:

> «Split: 1 enforce, 2–11 permit — product-invariant (70) → require-enforcement, handed on as a number; the ten process classes (251) → permit-class. Allowed ≠ enforced; this is recorded.»

⚠️ **Основания своими словами владелец не дал**, он только выбрал вариант. Рядом с вопросом оркестратор пояснил: классы 2-11 касаются того, как исполнялись (уже завершённые) планы Фазы 10, а класс 1 несёт правила продукта. Это пояснение оркестратора, а не довод владельца, и основанием решения оно здесь не записано. Каждое поле основания в реестре (`permit_basis`, `decision_basis`) говорит ровно это и ссылается на эту сводку.

Запись в `15-prohibitions-registry.yaml`, блок `class_decisions` (после шапки замера, перед строками):

- **10 записей разрешения** по форме образца `10-PROHIBITIONS-SUBJECT.md:1-36`:
  - `permit_branch: permit-class`, `permitted_by: chubav`, `permitted_on: '2026-09-24'`;
  - `permit_basis` — см. выше;
  - `permit_scope` — ИМЯ КЛАССА;
  - `permit_applies_to_phase: false`, `permit_applies_to_milestone: false`;
  - `permit_covers_prohibitions` — число запретов класса.
  - Поле `permit_covers_plans` образца не перенесено: область здесь — класс, а не партия планов.
- **1 запись иного решения**, без признака `permit` в именах полей:
  - `decision_branch: require-enforcement`, `decided_by: chubav`, `decided_on: '2026-09-24'`;
  - `decision_basis`;
  - `decision_scope: product-invariant`;
  - `decision_covers_prohibitions: 70`;
  - `work_addressee`.
- `grep -c 'permit_scope'` по реестру → **10**, это число разрешённых классов. `grep -c 'prohibitions_fully_enforced'` → **0**.

## Классы без ответа — входное условие плана 15-13

**Классов без ответа нет: 0 классов, 0 запретов.** Ответ получен по всем 11.

Что план 15-13 получает на вход:
- **`require-enforcement`: `product-invariant`, 70 запретов.** Долг передаётся числом. **Адресат работы не назначен**: план 15-12 называет только «будущие фазы» без номера, владелец фазу тоже не назвал. Поле `work_addressee` говорит это прямо, а назначить адресата может только владелец.
- **`permit-class`: 10 классов, 251 запрет.** ⚠️ Среди них **49** несут `verification: test`. По D-05 и задаче 1 плана 15-13 им ставится диспозиция по мере покрытия правилом, а не разрешение. Эту развилку решает 15-13, а не этот план. У `product-invariant` таких **12** из 70.
- Наблюдение для закрывающего правила 15-13, не решение. Все классы ответили, поэтому по букве 15-13 сильная форма («ни одного `unresolved`») допустима. Но 70 запретов `require-enforcement` по ответу остаются «неразобрано» с названной причиной. Сильная форма покраснела бы на них, пока правила не написаны.

## Что этот план НЕ делал

- **Диспозиции не менялись:** все 697 строк реестра несут `disposition: unresolved` (`--breakdown`: `unresolved: 697`). Построчные решения — работа плана 15-13.
- **Полей `permit_*` исполнитель не писал ни в задаче 1, ни в задаче 2.** В задаче 3 они записаны только по полученному ответу владельца, как предписывает задача, и только в блок `class_decisions`. В строках реестра ключей разрешения **0** (`--check`).
- Вердикта за владельца не выносилось: ни одного поля вердикта в реестре нет, и ключ вне объявленного перечня документа краснит правило.
- Требования в `REQUIREMENTS.md` не отмечались: `requirements.mark-complete` не вызывался по указанию оркестратора.

## Accomplishments

- Перечень диспозиций из четырёх значений с определением каждого и летописью 3 → 4.
- Поле `class` записано у 321 строки области решений. Перечень `PROHIBITION_CLASSES` из 11 классов с антивакуумом. Правила полноты разнесения, `statement_digest` и «решение не раньше класса».
- Режим `--draft-classes` (все кандидаты) и разбивка `--breakdown` по классам с ветвью ответа.
- Блок ответа владельца в реестре. Засев его переносит. Семь новых правил и контролей: форма решения, согласие числа с реестром, ни одного «разрешено» без разрешения класса, ключи документа, засев. Направление краснения проверено временной правкой копии реестра:
  - число покрытия 61 → 60 краснит правило формы;
  - `permit_applies_to_milestone: true` краснит правило формы;
  - строка `product-invariant` с `permitted` краснит правило разрешения строк;
  - ключ вердикта в шапке документа краснит перечень ключей и идемпотентность засева.

  Реестр восстановлен посимвольно.

## Task Commits

1. **Задача 1: перечень диспозиций — четыре значения по замеру образца.** `ffd0c34f` (test)
2. **Задача 2: класс записан полем по каждому из 321 запрета.** `23a42dfe` (feat)
3. **Задача 3: ответ владельца по классам записан полями.** `999e7a5f` (feat)

**Plan metadata:** коммит сводки и коммит трекинга следуют за этим файлом.

## Files Created/Modified

- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml`:
  - `class` у 321 строки Фазы 10;
  - блок `class_decisions`;
  - шапка с летописью абзаца «полей `permit_*` здесь нет».
- `scripts/prohibitions_census.py`:
  - `--draft-classes` и `--list --class`;
  - разбивка по классам с ветвью ответа;
  - перенос блока ответа засевом;
  - печать ответа в `--check`.
- `tests/test_planning/test_plan_prohibitions_census.py`:
  - `DISPOSITIONS` (4), `PROHIBITION_CLASSES` (11);
  - `REGISTRY_DOCUMENT_KEYS` (4), `CLASS_DECISION_BRANCHES` (3);
  - формы полей решения;
  - правила и контроли. Модуль вырос с 34 правил до 53, каталог `tests/test_planning/` — с 78 до 97.

## Decisions Made

См. `key-decisions`. Главное — форма записи ответа. Задача 3 требует полей `permit_*` с `permit_scope` именем класса. Засев (`seed_registry`) оставляет в документе только `measured`/`rows_declared`/`rows`, поэтому новый блок покраснил бы правило идемпотентности. Выбрана минимальная форма, совместимая с биекцией и идемпотентностью 15-01:
- отдельный ключ документа `class_decisions`;
- засев переносит его без изменений;
- перечень ключей документа поднят 3 → 4 с летописью;
- `REGISTRY_ROW_FIELDS` не тронут.

Поля строк `permit_*` вводит план 15-13 вместе с диспозициями.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Диф задачи 1 удаляет две строки, а не одну**
- **Found during:** задача 1
- **Issue:** критерий плана допускал удаление одной строки, прежнего значения `DISPOSITIONS_DECLARED`. Удалены две: однострочный литерал множества и прежнее число.
- **Fix:** прежнее множество дословно процитировано в летописи. Ничего не потеряно молча.
- **Committed in:** `ffd0c34f`

**2. [Rule 1 - Bug] «Частичность доминирует» верно только среди записей с правилом**
- **Found during:** задача 1
- **Issue:** план пишет, что «принуждается частично» в таблице образца ДОМИНИРУЕТ. Это верно среди записей, у которых правило вообще есть (8 из 8). По всем 25 записям `test` счёт 0 / 8 / 17.
- **Fix:** замер записан рядом со словом плана, слово не правилось.
- **Committed in:** `ffd0c34f`

**3. [Rule 2 - Missing critical] Частичная диспозиция обязана называть непокрытую часть**
- **Found during:** задача 1
- **Fix:** поле `uncovered_part` и правило `test_every_partially_enforced_disposition_names_its_uncovered_part` с контролем. Иначе «частично» стало бы способом не сказать ничего.
- **Committed in:** `ffd0c34f`

**4. [Rule 1 - Bug] «Все строки сохраняют `unresolved`» — проверено один раз, а не постоянным правилом**
- **Found during:** задача 2
- **Issue:** такое постоянное правило было бы литералом незакрытого состояния, который план запрещает, и покраснело бы на законной работе 15-13.
- **Fix:** проверено один раз, 697 `unresolved`. Вместо правила стоят `test_no_disposition_is_decided_before_its_class` и правило «строки вне области остаются `unclassified`/`unresolved`».
- **Committed in:** `23a42dfe`

**5. [Rule 1 - Bug] Вне области решений 376 строк, а не 329**
- **Found during:** задача 2
- **Issue:** 329 = 650 − 321 посчитано до планов Фазы 15. На вехе целиком 697 − 321 = 376.
- **Fix:** ни одно правило не утверждает ни одно из этих чисел; строки вне области судятся принадлежностью.
- **Committed in:** `23a42dfe`

**6. [Rule 3 - Blocking] Ответу владельца не было места в реестре**
- **Found during:** задача 3
- **Issue:**
  - засев сохраняет только три ключа, поэтому новый блок покраснил бы идемпотентность;
  - `REGISTRY_ROW_FIELDS` не знает имён `permit_*`;
  - шапка реестра утверждала «ПОЛЕЙ `permit_*` … НЕТ НАМЕРЕННО».
- **Fix:**
  - ключ документа `class_decisions`, засев его переносит;
  - `REGISTRY_DOCUMENT_KEYS` 3 → 4 с летописью;
  - абзац шапки переписан с летописью прежней формулировки: она процитирована, а не стёрта.
- **Files modified:** реестр, `scripts/prohibitions_census.py`, модуль теста
- **Committed in:** `999e7a5f`

**7. [Rule 2 - Missing critical] Форма ответа владельца не судилась ничем**
- **Found during:** задача 3
- **Fix:** добавлены правила:
  - форма решения (две формы полей, ветвь, класс из перечня, класс решён не дважды, флаги распространения `false`);
  - согласие объявленного числа с реестром;
  - «разрешено» только в разрешённом классе (T-15-04);
  - перечень ключей документа;
  - перенос засевом.

  К каждому правилу есть контроль. Ни одно правило не знает, сколько классов разрешено.
- **Committed in:** `999e7a5f`

---

**Total deviations:** 7 auto-fixed (4 Rule 1, 2 Rule 2, 1 Rule 3)
**Impact on plan:** все поправки нужны для верности записи и для того, чтобы правила остались зелёными на законной работе. Область плана не расширена, диспозиции не тронуты.

## Issues Encountered

- `ruff` в окружении не установлен, поэтому линт не прогонялся. `python -m compileall -q scripts tests/test_planning` проходит молча.

## Known Stubs

Нет. `disposition: unresolved` во всех 697 строках — засеянный предмет решения. Его заполняет план 15-13 по D-03, и это записано в шапке реестра.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 15-13 может ставить диспозиции: класс записан у всех 321 запрета, ответ владельца есть по всем 11 классам.
- Для 15-13: 49 запретов с `verification: test` лежат в разрешённых классах, 12 — в `product-invariant`. Для `product-invariant` адресат работы не назначен.
- Проверка сводки: `uv run pytest tests/test_planning/ -q -p no:randomly` → 97 passed. `--breakdown` → сумма 321 по 11 классам. `--check` → 0 ключей разрешения в строках, 10 разрешённых классов.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `15-prohibitions-registry.yaml`, `scripts/prohibitions_census.py`, `tests/test_planning/test_plan_prohibitions_census.py`, `15-12-SUMMARY.md`
- FOUND: `ffd0c34f`, `23a42dfe`, `999e7a5f`
- `git rev-list --count bdb1a804..HEAD` → 3 до коммита сводки
- `tests/test_planning/` → 97 passed на закоммиченном дереве задачи 3

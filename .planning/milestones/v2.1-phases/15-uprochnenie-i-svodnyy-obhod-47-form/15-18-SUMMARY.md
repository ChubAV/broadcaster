---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 18
subsystem: testing
tags: [pytest, jinja, parser, htmx, gate, in-03, split_top_level, QUAL-04, GATE-09]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-10: группа связки модалок (D-07) и её разборщик в гейте разметки; план 15-11: реестр решений `hx-push-url` и его разборщик в гейте страниц; план 15-14 — предшественник по `depends_on`"
provides:
  - "единственный `_split_top_level` суиты — в `tests/test_templates/test_htmx_markup_gates.py`: разделитель любой длины (`startswith`), вложенность `()`, `[]`, `{}`, кавычки обоих видов; пустой разделитель — `ValueError`"
  - "три правила поведения на синтетических строках: `test_split_top_level_divides_by_a_multi_character_separator`, `test_split_top_level_ignores_separators_inside_three_kinds_of_brackets`, `test_split_top_level_ignores_separators_inside_quotes`"
  - "гейт страниц (`test_htmx_gates.py`) и гейт компонентов (`test_components.py`) ввозят его; собственные определения сняты, на их местах — комментарии-летописи"
affects: [15-19, phase-15-verification, QUAL-04, GATE-09]

actuals:
  tokens: 2918
  tasks: 2
  commits: 4
plan_head_before: 5b902dd31b2678334cc6261559c68792928b6cf6

tech-stack:
  added: []
  patterns:
    - "одноимённый помощник разбора живёт в одном модуле и ввозится; поведение закреплено правилами на синтетике, а тождество потребителей замерено на дереве до правки"
    - "замер тождества разборщиков — обёртка над живыми вызовами (старый и новый исход на каждом вызове), а не рассуждение о формах выражений"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-18-SUMMARY.md
  modified:
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_templates/test_components.py

key-decisions:
  - "15-18: единый разборщик = форма разборщика гейта страниц (`startswith` + продвижение на длину разделителя) + скобки трёх видов и кавычки гейта разметки; исходы потребителей замерены до правки: гейт страниц 740 живых вызовов (` else ` 370, `~` 350, ` if ` 20), гейт разметки 2020 (`~` 1758, `,` 262) — ноль расхождений частей"
  - "15-18: третий `_split_top_level` в `test_components.py` (один аргумент, только запятая, без кавычек) плану не был известен, но держал его критерий «одно определение в `tests/`» невыполнимым — сведён туда же отклонением: на дереве 4 из 14 вызовов дали иные ЧАСТИ (старый рвал `body='…, …'` на кириллические обрывки), а ИСХОДЫ потребителей тождественны — имена сигнатуры и именованных аргументов панели по всем шаблонам, 11 файлов, 55 имён"
  - "15-18: направление ввоза — из гейта разметки в гейт страниц и в соседний модуль того же пакета; `tests/test_templates/` ничего из `tests/test_pages/` не ввозит"

patterns-established:
  - "Помощник разбора, которому верят два гейта, определяется один раз; второе определение с тем же именем — дефект, даже если сегодня исходы совпадают"

requirements-completed: [QUAL-04, GATE-09]

coverage:
  - id: D1
    description: "Единый разборщик делит по многосимвольному разделителю, не рвёт части внутри трёх видов скобок и внутри кавычек"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k split_top_level (3 passed)"
        status: pass
      - kind: unit
        ref: "RED на прежнем разборщике гейта разметки: FAILED tests/test_templates/test_htmx_markup_gates.py::test_split_top_level_divides_by_a_multi_character_separator, 1 failed (check tdd-red-evidence → RED_EVIDENCE_OK)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Одно определение `_split_top_level` в суите; гейт страниц и гейт компонентов ввозят его, потребители зелены без правки ожиданий"
    verification:
      - kind: other
        ref: "grep -rn 'def _split_top_level' tests/ | wc -l → 1; grep -c '_split_top_level' tests/test_pages/test_htmx_gates.py → 5"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_templates/ tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_shell.py -q -p no:randomly (799 passed)"
        status: pass
      - kind: other
        ref: "замер живых вызовов (scratch-плагин, не закоммичен): гейт страниц 740/0 расхождений, гейт разметки 2020/0; гейт компонентов — исходы `_modal_signature_names`/`_modal_call_kwargs` по всем шаблонам до == после"
        status: pass
    human_judgment: false

duration: 22min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 18: Один разборщик `_split_top_level` на суиту (IN-03) Summary

**Три одноимённых разборщика выражений шаблонизатора с разным поведением сведены к одному в гейте разметки — разделитель любой длины, скобки `()[]{}`, кавычки; гейты страниц и компонентов его ввозят, исходы всех потребителей замерены тождественными до правки.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-25T07:14:20Z
- **Completed:** 2026-09-25T07:36:25Z
- **Tasks:** 2 (+1 отклонение)
- **Files modified:** 3

## Accomplishments

- `_split_top_level` гейта разметки переписан: сравнение разделителя через `text.startswith(separator, index)` с пропуском его длины (форма прежнего разборщика гейта страниц), вложенность по `([{` / `)]}`, кавычки обоих видов. Докстринг называет его единственным определением суиты, предмет и границу (экранированная кавычка в литерале шаблонизатора не разбирается); пустой разделитель — `ValueError` вместо бесконечного цикла.
- Три правила поведения на синтетических строках; каждое различает прежние формы: ` else ` не делился у гейта разметки, `{'k': 1, 'm': 2}` рвался бы у гейта страниц, `"("` в кавычках сдвигал глубину у гейта компонентов.
- Гейт страниц ввозит разборщик в действующем блоке `from tests.test_templates.test_htmx_markup_gates import (`; определение снято, на его месте летопись.
- Гейт компонентов — то же (отклонение, см. ниже).

## RED

`uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k test_split_top_level_divides_by_a_multi_character_separator` на прежнем разборщике, exit 1:

```
FAILED tests/test_templates/test_htmx_markup_gates.py::test_split_top_level_divides_by_a_multi_character_separator
1 failed, 124 deselected, 1 warning in 0.44s
```

Причина — литерал правила: `разборщик НЕ ДЕЛИТ по многосимвольному разделителю ` else `: … — ['a if b else c']`. Запись переведена из `--junit-xml` в TAP одноразовым скриптом в scratchpad (не закоммичен); `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`). На полном `-k split_top_level` прежний разборщик дал `3 failed` по одной и той же причине: второе и третье правила несут по утверждению с ` else ` (скобки `{}` и кавычки под многосимвольным разделителем — ровно форма потребителя гейта страниц); их однобуквенные утверждения, стоящие первыми, прошли.

## Прогон обоих гейтов и потребителей

- `-k split_top_level` → `3 passed`; `tests/test_templates/` → `362 passed` (после задачи 1).
- `tests/test_pages/test_htmx_gates.py` → `84 passed`; `tests/test_pages/test_htmx_post_pairs.py tests/test_templates/` → `447 passed` (после задачи 2).
- Все модули, ввозящие любой из трёх затронутых: `tests/test_templates/ tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_shell.py` → `799 passed` (после отклонения, финальное дерево кода).
- `tests/test_planning/` → `114 passed`.
- Считающие гейты не сдвинулись: `PAIRED_302_ASSERTIONS_DECLARED` 190, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5 — их модули в прогоне зелены, объявления не правились.

**Находки о разошедшихся исходах:** у потребителей — нет. Замер до правки: scratch-плагин обернул все три `_split_top_level` и на каждом живом вызове сравнил прежний исход с единым. Гейт страниц: 740 вызовов, 0 расхождений частей. Гейт разметки: 2020 вызовов, 0. Гейт компонентов: 14 вызовов, 4 расхождения ЧАСТЕЙ (панели `queue_drop`, `user-imp`, `worker-restart`, `history-retry`: прежний разборщик резал текст `body='…, …'` по запятым внутри кавычек), но ИСХОДЫ потребителей (`_modal_signature_names`, `_modal_call_kwargs` по всем шаблонам) тождественны — обрывки начинались кириллицей, и `KWARG_NAME_RE` их не брал. Это латентный дефект прежнего разборщика, а не сдвиг гейта: обрывок, начавшийся латиницей со знаком `=`, выдумал бы имя аргумента.

## Task Commits

1. **Задача 1 RED** — `a0c7839f` (test)
2. **Задача 1 GREEN** — `a7c240cc` (feat)
3. **Задача 2: гейт страниц ввозит разборщик** — `184411da` (refactor)
4. **Отклонение: гейт компонентов ввозит разборщик** — `2091e642` (refactor)

**Plan metadata:** docs(15-18) — коммит сводки и трекинга.

## Files Created/Modified

- `tests/test_templates/test_htmx_markup_gates.py` — единый `_split_top_level` и три правила его поведения
- `tests/test_pages/test_htmx_gates.py` — ввоз вместо определения, летопись
- `tests/test_templates/test_components.py` — ввоз вместо третьего определения, вызовы с явным `","`, летопись

## Decisions Made

См. `key-decisions`: форма единого разборщика; третий разборщик сведён отклонением по замеру; направление ввоза.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Третий `_split_top_level` в `tests/test_templates/test_components.py`**
- **Found during:** Задача 1 (разметка потребителей, `grep -rn _split_top_level tests/`)
- **Issue:** План и ревью IN-03 знали два разборщика; третий (`_split_top_level(argument_text)`: одна запятая, три вида скобок, без кавычек) жил в гейте компонентов с плана 10-01. Критерий задачи 2 `grep -rn 'def _split_top_level' tests/ | wc -l` = `1` и истина плана «в суите ОДИН разборщик» без него невыполнимы.
- **Fix:** определение снято, имя добавлено в действующий ввоз `from tests.test_templates.test_htmx_markup_gates import (` (модуль того же пакета — запрет плана о направлении не задет), два вызова передают `","` явно; на месте определения — летопись с механизмом прежнего дефекта.
- **Files modified:** `tests/test_templates/test_components.py`
- **Verification:** исходы потребителей замерены до правки тождественными (11 файлов, 55 имён); прогон всех ввозящих модулей `799 passed`; `grep -rn 'def _split_top_level' tests/ | wc -l` → `1`.
- **Committed in:** `2091e642`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Ожидания ни одного правила-потребителя не менялись. Файл вне `files_modified` плана — названо здесь.

## Issues Encountered

- Номера строк плана устарели незначительно: определение гейта страниц было на `test_htmx_gates.py:7009` (совпало), гейта разметки — на `test_htmx_markup_gates.py:9496` (совпало); после правки единый разборщик стоит там же, `:9496`, правила — сразу за ним.
- Полная суита (`just test`, ~40 мин) не запускалась по указанию оркестратора: она его, после волны (после 15-19). Подстановка — прогон всех модулей, ввозящих любой из трёх затронутых файлов (`799 passed`), и `tests/test_planning/` (`114 passed`).
- `requirements-completed` скопирован из плана по шаблону; REQUIREMENTS.md не правился, `requirements.mark-complete` не вызывался (указание оркестратора).

## TDD Gate Compliance

RED `a0c7839f` (`test(15-18)`) → GREEN `a7c240cc` (`feat(15-18)`) → `refactor(15-18)` `184411da`, `2091e642`. Нарушений нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Готов к 15-19. Блокеров нет.

## Self-Check: PASSED

- FOUND: `tests/test_templates/test_htmx_markup_gates.py`, `tests/test_pages/test_htmx_gates.py`, `tests/test_templates/test_components.py`
- FOUND: `a0c7839f`, `a7c240cc`, `184411da`, `2091e642`
- `git rev-list --count 5b902dd3..HEAD` → 4 до коммита сводки

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 06
subsystem: planning-records
tags: [uat, self-certification, requirements, chronicle, gate-08, fetch-03]

requires:
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-UAT.md — артефакт обхода с 9 таблицами отметок и шапкой `status: complete`"
  - phase: 09
    provides: "план 09-13 — закрытие записи `INCLUDE_TARGET_EXCEPTIONS['group-list-sentinel']`"
provides:
  - "входное условие Фазы 15 закрыто: `tests/test_planning/` зелен целиком (44 passed)"
  - "14-UAT.md в нетерминальном состоянии `human_needed` с абзацем отзыва объявления"
  - "летопись отставшего утверждения REQUIREMENTS.md:270 (group-list-sentinel закрыт планом 09-13)"
  - "летопись имени `test_no_manual_fetch_remains` у GATE-08 и находка об отметке GATE-08"
affects: [15-04, 15-09, 15-14, phase-15-verification, gsd-ship-14]

actuals:
  tokens: 1781
  tasks: 3
  commits: 3
plan_head_before: ed82f990f970314869ed685d40e3c40495e120f3

tech-stack:
  added: []
  patterns:
    - "отзыв объявления обхода возвратом шапки в нетерминальное состояние, без заполнения отметок"
    - "летопись рядом с отставшим утверждением (идиома D-30/D-32), чистое добавление строк"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-06-SUMMARY.md
  modified:
    - .planning/phases/14-avtorizatsiya-na-htmx/14-UAT.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "14-UAT.md: `status: complete` → `status: human_needed` по решению владельца chubav 2026-09-23 (Open Questions #4); отметки не заполнены, `checks_declared: 9` и 9 таблиц сохранены"
  - "Имя функции-запрета FETCH-03 в летописи GATE-08 не выдумано: план 15-04 не исполнен, имя вписывается по его сводке"
  - "Отметка GATE-08 не снята и клетки таблицы состояний не тронуты: отметка следует вердикту отчёта фазы, смена требует нового решения владельца"

patterns-established:
  - "Отзыв самозаверенного обхода: одно поле шапки + абзац над первым разделом проверки, называющий прежнее и новое значение"

requirements-completed: [GATE-09, FETCH-03]

coverage:
  - id: D1
    description: "Входное условие фазы: шапка 14-UAT.md нетерминальна, правило самозаверения зелено, отметки пусты, число проверок/разделов/таблиц сохранено"
    requirement: GATE-09
    verification:
      - kind: unit
        ref: "tests/test_planning/test_the_walkthrough_cannot_self_certify.py (5 passed)"
        status: pass
      - kind: other
        ref: "uv run pytest tests/test_planning/ -q -p no:randomly → 44 passed"
        status: pass
      - kind: other
        ref: "grep -c: ^### Отметка=9, ^## Проверка=9, ^status: human_needed=1, ^status: complete=0, ^checks_declared: 9=1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Летопись отставшего утверждения REQUIREMENTS.md:270 с тремя координатами замера и указанием на противоречие со строкой 335 того же файла"
    verification:
      - kind: other
        ref: "git show --numstat --format= 67560f79 -- .planning/REQUIREMENTS.md → 1 0"
        status: pass
      - kind: other
        ref: "grep -c 'INCLUDE_TARGET_EXCEPTIONS_DECLARED = 0' tests/test_pages/test_account_groups.py → 1"
        status: pass
    human_judgment: false
  - id: D3
    description: "Летопись имени test_no_manual_fetch_remains у GATE-08 и находка об отметке GATE-08; отметка не снята, имя не подогнано"
    requirement: FETCH-03
    verification:
      - kind: other
        ref: "grep -rc 'test_no_manual_fetch_remains' tests/ | grep -v ':0' | wc -l → 0"
        status: pass
      - kind: other
        ref: "git show --numstat --format= 0f069bce -- .planning/REQUIREMENTS.md → 2 0; удалённых строк 0"
        status: pass
    human_judgment: true
    rationale: "Запись 1 намеренно оставляет имя новой функции-запрета невписанным до сводки плана 15-04; полнота летописи судится после 15-04, а верность прозы летописи — чтением человека (D-33: проза записи машиной не судится)"

duration: 4min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 06: Входное условие фазы и три отставших утверждения записи Summary

**Шапка `14-UAT.md` переведена `complete` → `human_needed` с абзацем отзыва и пустыми отметками, что вернуло `tests/test_planning/` из `1 failed, 43 passed` в `44 passed`; в `REQUIREMENTS.md` дописаны три строки летописи (group-list-sentinel закрыт планом 09-13; имя `test_no_manual_fetch_remains` у GATE-08; находка об отметке GATE-08), ни одна строка не удалена**

## Performance

- **Duration:** ~4 min (по часам системы)
- **Started:** 2026-09-24T06:09:02Z
- **Completed:** 2026-09-24T06:12:56Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- **Входное условие фазы закрыто.** Поле состояния `14-UAT.md`: было `status: complete`, стало `status: human_needed` (нетерминально по перечню `TERMINAL_WALKTHROUGH_STATES = frozenset({"complete", "passed"})`; перечень и `TERMINAL_STATES_DECLARED = 2` не тронуты).
- **Прогон каталога записи ДО и ПОСЛЕ:**
  - до: `uv run pytest tests/test_planning/ -q -p no:randomly` → `1 failed, 43 passed` (`FAILED …::test_no_walkthrough_declares_itself_passed_with_empty_marks`);
  - после задачи 1: `44 passed`; после задач 2 и 3: `44 passed`.
- **Ноль заполненных отметок подтверждён разборщиком самого правила:** `walkthrough_counts(14-UAT.md)` → `WalkthroughCounts(state='human_needed', declared_checks=9, check_sections=9, mark_tables=9, filled_marks=0)`. Ни одна клетка девяти таблиц «Отметка о закрытии» не тронута.
- **Абзац отзыва** стоит на строке 12, выше первого `## Проверка` (строка 126): называет прежнее и новое значение, владельца `chubav`, дату 2026-09-23, план `15-06`, цитирует решение владельца и предписание правила дословно («Заполнение отметок ради зелени правила есть самозаверение, а не приёмка»).
- **Три записи летописи в `REQUIREMENTS.md`, чистое добавление.** `git show --numstat --format= HEAD -- .planning/REQUIREMENTS.md` по задачам: `1 0` (67560f79), `2 0` (0f069bce); по плану целиком `git diff --numstat ed82f990 HEAD` → `3 0 .planning/REQUIREMENTS.md`, `29 1 .planning/phases/14-avtorizatsiya-na-htmx/14-UAT.md` (единственная удалённая строка плана — `status: complete`).
- **Отметка GATE-08 НЕ снималась, и текст требований не двигался ни на символ.** Добавленных строк вида `- [x]`/`- [ ]` — 0; удалённых строк в `REQUIREMENTS.md` — 0; клетки `| FETCH-03 | Phase 15 | Pending |` и `| GATE-08 | Phase 8 | Complete |` на месте.

## Task Commits

1. **Задача 1: шапка `14-UAT.md` → нетерминальная, объявление отозвано** — `f2361428` (docs)
2. **Задача 2: летопись отставшего утверждения `REQUIREMENTS.md:270`** — `67560f79` (docs)
3. **Задача 3: летопись имени `test_no_manual_fetch_remains` и находка об отметке GATE-08** — `0f069bce` (docs)

**Plan metadata:** коммит сводки и коммит учёта STATE/ROADMAP следуют за этой сводкой.

## Files Created/Modified

- `.planning/phases/14-avtorizatsiya-na-htmx/14-UAT.md` — одно поле шапки (`status`) + абзац отзыва (29 добавлено / 1 удалено)
- `.planning/REQUIREMENTS.md` — строка 271 (летопись после «остаётся открытой»), строки 73–74 (летопись имени и находка у GATE-08)

## Decisions Made

- Абзац отзыва оформлен блок-цитатой между frontmatter и H1, без заголовков и таблиц — так разборщик не может прочесть его ни как раздел `## Проверка N`, ни как таблицу под `### Отметка`.
- В летописи задачи 2 строка 335 названа с оговоркой «по нумерации до вставок плана 15-06», потому что сама вставка сдвигает её на 336 (после задачи 3 — на 338); предмет назван и по содержанию (третий круг, «Опорный признак обхода», пункт «исход»), чтобы ссылка пережила сдвиг.
- Имя функции-запрета FETCH-03 не вписано: план 15-04 на день записи не исполнен (сводки `15-04-SUMMARY.md` нет), а его план лишь запрещает имя `test_no_manual_fetch_remains`, не фиксируя нового. По прямому указанию задачи 3 имя не выдумывается.

## Deviations from Plan

None - plan executed exactly as written.

(Сдвиг задачи 3 «сослаться на план 15-04 по номеру и вписать имя после» — это ветвь, предусмотренная самим планом, а не отклонение.)

## Issues Encountered

- **Названо, не решено: тело `14-UAT.md` несёт словесный вердикт.** В разделе `## Tests` все девять проверок имеют `result: pass` / `reported: "pass"`, а `## Summary` — `passed: 9`; `STATE.md` (блокер Фазы 14) записывает их как «словесный вердикт владельца на приёмке 2026-09-23». Решение владельца #4 при этом говорит «обход Фазы 14 глазами не делался». План эти поля не трогал (правило самозаверения их не считает, а правка была бы вынесением вердикта), и абзац отзыва называет их прямо, без вердикта. Согласовать словесный вердикт с отсутствием обхода глазами — вопрос владельцу, а не исполнителю.
- Первая редакция абзаца отзыва разбила дословную цитату предписания переносом строки, и `grep -c` дал 0; строки перенесены так, чтобы цитата стояла одной строкой, до коммита задачи 1.

## TDD Gate Compliance

План `type: execute`, все три задачи `type="auto"` без `tdd="true"`; правится только запись (`.planning/`), ни одного файла кода или теста. Задач, добавляющих поведение, нет, поэтому RED/GREEN-цикла нет и RED-улика не изготавливалась. Коммиты несут область `docs(15-06)`.

## Requirements

`requirements.ready-ids` (только чтение) для `[GATE-09, FETCH-03]` → `0/2 requirement(s) ready to mark complete`: оба ID объявлены и соседними планами фазы (15-04 — FETCH-03; 15-05, 15-07, 15-09, 15-14 — GATE-09), у которых сводок ещё нет. `requirements.mark-complete` НЕ вызывался (по указанию оркестратора отметки ставит закрытие фазы). `requirements-completed` во frontmatter — копия поля `requirements` плана по контракту шаблона, а не отметка завершённости.

## Known Stubs

- `.planning/REQUIREMENTS.md:73` — летопись имени у GATE-08 не называет имя новой функции-запрета FETCH-03: оно вписывается следующей строкой той же летописи по сводке плана 15-04. Намеренно, по тексту задачи 3 («НЕ выдумывать имя»); адресат — исполнитель плана 15-04 или закрытие Фазы 15.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Обещание «полная суита зелена» в Фазе 15 теперь исполнимо: каталог записи зелен (`44 passed`). Полный прогон `just test` обещает план 15-14, а не этот.
- План 15-04 обязан после своего исполнения дописать имя функции-запрета в летопись GATE-08 (`REQUIREMENTS.md:73`).
- Для `/gsd-ship 14` отметки `14-UAT.md` по-прежнему пусты: закрыть их может только человек, действительно проведший обход, и тогда же вернуть шапку в терминальное состояние.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

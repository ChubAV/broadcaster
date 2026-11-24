---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 40
subsystem: planning-records
tags: [review-disposition, code-review, round-7, prohibitions-census, records]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "исправляющие коммиты партии раунда 7: 16-36 (`b67495dc`, `44452e68`, `b8d557f0`, `4ffef0c1`), 16-37 (`51d0d766`, `2d59adff`, `0a4e4411`), 16-38 (`3a7fe75b`, `b953ce0d`, `d7013797`, `85ac9a2e`, `9ce79852`), 16-39 (`59654f01`, `7a3a7b46`, `defeaae4`) и итоги сверки «база ↔ HEAD» из их сводок"
provides:
  - "`16-REVIEW-DISPOSITION.md`: семь находок повторного ревью раунда 6 (CR-02, CR-03, WR-24, WR-25, WR-26, IN-16, IN-17) — `fixed` с названными исправляющими коммитами партии раунда 7 и решениями владельца О-16 (а) / О-17; регрессии партии раунда 6 CR-02 («c6953017») и CR-03 («147f5e46») названы регрессиями с итогом сверки «база ↔ HEAD» закрывшего плана и партии; frontmatter `open: 0`, `total: 46`"
  - "тридцать девять прежних строк и их записи frontmatter — без изменений против `b1b41431`, метка «(not in the current review)» на месте"
  - "реестр запретов пересеян штатным `--seed-registry`: файл не изменился (856 строк), `--check` — код 0"
affects: [16-verification-round-8, phase-16-code-review, phase-17, phase-18]

actuals:
  tokens: 2429
  tasks: 2
  commits: 2
plan_head_before: 6e306a6341308932c996cb8185284de0faf44b28
plan_head_after: dcf972bcd5c72cfe2f89d6652020f983598b766a

tech-stack:
  added: []
  patterns:
    - "Строка словаря, вписанная коммитом теста и зеленеющая с GREEN, называется в клетке так же, как у WR-19 (16-34): коммит теста — в «ёлочках», GREEN — в обратных кавычках только у строки, чей план его исполнил"

key-files:
  created: []
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md

key-decisions:
  - "В клетках `fixed` в обратных кавычках стоят только GREEN-коммиты плана, чью тему проверка допускает для строки; GREEN других планов (`59654f01` у CR-03, `7a3a7b46` у CR-02 и WR-24), коммиты RED и регрессий — в «ёлочках»"
  - "Строки словаря 16-39 вписаны коммитами теста «f684dc45» / «bb6ce1be» и зеленеют с GREEN `59654f01` / `7a3a7b46`; клетки говорят это прямо, а не приписывают строки GREEN-коммиту"
  - "В клетку CR-03 добавлены строка словаря `named-wrapper-bound-handed` (16-39 задача 1) и итог сверки партии: форма CR-03 стала строкой общего словаря, и верификатор раунда 8 должен это видеть"

patterns-established: []

requirements-completed: ["диспозиция-ревью-16"]

coverage:
  - id: D1
    description: "CR-03 — `fixed` с GREEN `b67495dc`, `b8d557f0`, `4ffef0c1` плана 16-36, регрессия «147f5e46» и итог «BASE 1c243203 -> HEAD 4ffef0c1 … regressions=0», «OPEN_REGRESSIONS=0»; прочие строки прежние; `open: 6` на коммите задачи 1"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "task-1 <automated> #1 плана 16-40 (OK), прогнан дословно"
        status: pass
      - kind: other
        ref: "git merge-base --is-ancestor b67495dc / b8d557f0 / 4ffef0c1 HEAD (код 0), темы `feat(16-36)`"
        status: pass
    human_judgment: false
  - id: D2
    description: "Шесть строк CR-02, WR-24, WR-25, WR-26, IN-16, IN-17 — `fixed` с 17 вхождениями хешей; у каждого хеша тема `feat(<план>)` строки и предок `HEAD`; 39 прежних строк и записей frontmatter равны `b1b41431`; frontmatter равен таблице, `open: 0`, `total: 46`"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "task-2 <automated> #1 плана 16-40 (OK 20 commits), прогнан дословно"
        status: pass
      - kind: other
        ref: "acceptance задачи 2: ни одной строки `open` из 46 (OK); git diff b1b41431 — 15 строк, только семь строк таблицы, семь `disposition` и `open:`"
        status: pass
    human_judgment: false
  - id: D3
    description: "Реестр запретов: `--seed-registry` — «реестр не изменился: 856 строк»; `--check` — код 0, биекция с переписью"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check (код 0)"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py (110 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Суита записей зелена после коммитов учёта плана"
    requirement: "диспозиция-ревью-16"
    verification: []
    human_judgment: true
    rationale: "`tests/test_planning` по orchestrator_notes 5 гонится один раз — после коммита этой сводки; результат стоит в финальном сообщении исполнителя, а не здесь"

duration: 12min
completed: 2026-10-19
status: complete
---

# Phase 16 Plan 40: Диспозиции семи находок повторного ревью раунда 6 — Summary

**Все семь находок повторного ревью раунда 6 записаны `fixed` с названными исправляющими коммитами партии раунда 7. Каждый хеш в обратных кавычках — предок `HEAD` с темой `feat(<план>)` плана, который строка называет: 20 вхождений, проверка дословная. CR-02 и CR-03 названы регрессиями партии раунда 6 («c6953017», «147f5e46»). У каждой — итог сверки «база ↔ HEAD» закрывшего плана и партии (`OPEN_REGRESSIONS=0`, «AGAINST 1c243203 -> HEAD defeaae4 … regressions=0»). Тридцать девять прежних строк и их записи во frontmatter байт в байт совпадают с `b1b41431`; `open: 0`, `total: 46`. Реестр запретов пересеян штатно, файл не изменился, `--check` — код 0.**

## Performance

- **Duration:** ≈12 мин
- **Started:** 2026-10-19T14:32:53Z
- **Completed:** 2026-10-19T14:44:45Z
- **Tasks:** 2
- **Files modified:** 1 (`16-REVIEW-DISPOSITION.md`; реестр запретов засев не изменил)

## Accomplishments

- **CR-03** (задача 1, трасер):
  - `16-36` задачи 1 и 3, GREEN `b67495dc`, `b8d557f0`; цикл сверки — GREEN `4ffef0c1`;
  - решение О-16 (а), регрессия «147f5e46»;
  - суд обёртки на каждом чтении и поглощение только по судимым чтениям; общая `wrapper_applications`; трасер и строки;
  - собственная регрессия плана «44452e68» закрыта циклом сверки;
  - итог «BASE 1c243203 -> HEAD 4ffef0c1: cells=54001 regressions=0», «OPEN_REGRESSIONS=0»;
  - в задаче 2 добавлены строка словаря `named-wrapper-bound-handed` (16-39 задача 1) и итог сверки партии.
- **CR-02:**
  - `16-38` задачи 1 и 3, GREEN `3a7fe75b`, `d7013797`; цикл самопроверки — GREEN `85ac9a2e`;
  - регрессия «c6953017»;
  - `keep_iterables`, писатель прежний;
  - строка `map-named-iterable` с полем `last` (16-39);
  - итоги «BASE 9a92efd9 -> HEAD 9ce79852 … regressions=0», «OPEN_REGRESSIONS=0» и итог партии.
- **WR-24:**
  - `16-37` GREEN `51d0d766`, `2d59adff`, `0a4e4411`;
  - О-16 (а), свойство 5, и О-15;
  - копия семантики обёртки снята, пять общих имён, одно место — одна находка;
  - `REQUIRED_SHARED_NAMES` «11»; свойство 8;
  - итог «BASE df9cea19 -> HEAD 0a4e4411 … regressions=0».
- **WR-25:**
  - `16-38` GREEN `b953ce0d`, `85ac9a2e`, `9ce79852`;
  - одно правило `ELEMENTWISE_CARRIERS` / `ROW_CARRIERS`, `methodcaller` у `starmap`, правдивый докстринг, `every_reading` в пути `methodcaller`;
  - `16-39` GREEN `7a3a7b46` — строки `starmap`, `apply-async`;
  - О-16 (а), свойства 4 и 6.
- **WR-26:**
  - сторона писателя — `16-36` GREEN `b67495dc`, `44452e68`, `4ffef0c1`;
  - сторона приватности — `16-37` GREEN `2d59adff`;
  - строки словаря `wrapper-handed`, `wrapper-of-wrapper`, `named-wrapper-handed` — `16-39` GREEN `7a3a7b46`;
  - О-16 (а), свойство 3. Названа пробелом композиции, а не регрессией, как в ревью.
- **IN-16 и IN-17:** `16-37` задача 3, GREEN `0a4e4411`, решение О-17:
  - комментарий ввоза без выведенной `REFERENCE_KEYWORDS`, с путём `methodcaller`;
  - строки плана 16-34 — в прошедшем времени.
- **Frontmatter:** у семи строк `disposition: fixed`, `open: 7 → 6 → 0`, `total: 46`. Заголовки, тяжести и `recorded` прежние.
- **Реестр запретов:** `--seed-registry` — «реестр не изменился: 856 строк». Оркестратор засеял строки планов 16-36…16-40 при коммите планов. `--check` — код 0. Коммита `chore(16-40)` нет: менять было нечего.

## Task Commits

1. **Задача 1 (трасер): CR-03 — `fixed` с коммитами GREEN 16-36 и итогом сверки** — `c5d28203` (docs).
2. **Задача 2: CR-02, WR-24, WR-25, WR-26, IN-16, IN-17; frontmatter; пересев реестра** — `dcf972bc` (docs).

**Plan metadata:** коммит `docs(16-40)` с этой сводкой. База плана — `6e306a63`.

Гейт трасера после задачи 1:
- режим `end-of-phase`, авто-режим выключен (`auto_advance: false`, `_auto_chain_active: false`), у трасера только `<automated>`;
- первая команда `<verify>` прогнана заново после коммита — `OK`;
- вторую (`tests/test_planning`) orchestrator_notes 5 велит гнать один раз, в конце (отступление 2);
- план перешёл к задаче 2.

## Сверка хешей (договор диспозиций, запрет №1 плана)

Каждый GREEN сверен с разделом коммитов своей сводки и с `git log --grep='^feat(16-3[6-9])'` — 15 коммитов, у всех тема `feat(16-3N)`. Проверка задачи 2 дала `OK 20 commits` и подтвердила для каждого вхождения три вещи: тема начинается с `feat(<план строки>)`, `git merge-base --is-ancestor <хеш> HEAD` возвращает 0, `git log -1` читает коммит.

| Строка | Хеши в обратных кавычках | Темы | Вне обратных кавычек («ёлочки») |
|--------|--------------------------|------|----------------------------------|
| CR-03 | `b67495dc`, `b8d557f0`, `4ffef0c1` | `feat(16-36)` | регрессия «147f5e46»; «44452e68» (своя регрессия плана), RED «a5b43616», «388ed1a9», «ec639a54»; 16-39 — «f684dc45», «59654f01» |
| CR-02 | `3a7fe75b`, `d7013797`, `85ac9a2e` | `feat(16-38)` | регрессия «c6953017»; 16-39 — «bb6ce1be», «7a3a7b46»; RED «1da1b993», «0b50a4de», «9f804a44» |
| WR-24 | `51d0d766`, `2d59adff`, `0a4e4411` | `feat(16-37)` | «5e57325d»; 16-39 — «bb6ce1be», «7a3a7b46»; RED «a6c87597», «fa786d20» |
| WR-25 | `b953ce0d`, `85ac9a2e`, `9ce79852`, `7a3a7b46` | `feat(16-38)`, `feat(16-39)` | «bb6ce1be»; RED «3b503f81», «269b9218», «bb6ce1be» |
| WR-26 | `b67495dc`, `44452e68`, `4ffef0c1`, `2d59adff`, `7a3a7b46` | `feat(16-36)`, `feat(16-37)`, `feat(16-39)` | «bb6ce1be»; RED «388ed1a9», «8e1f2ebf», «a5b43616», «a53126a7», «bb6ce1be» |
| IN-16 | `0a4e4411` | `feat(16-37)` | RED «fa786d20» |
| IN-17 | `0a4e4411` | `feat(16-37)` | RED «fa786d20» |

Строки словаря 16-39 вписаны коммитами теста. Это замерено `git log -S`:
- `named-wrapper-bound-handed` — «f684dc45»;
- `named-wrapper-getattr`, `map-named-iterable` и прочие строки задачи 2 — «bb6ce1be».

GREEN `59654f01` модуль словаря не трогает (`git show --stat`: только две шапки). Поэтому клетки говорят «вписана коммитом теста, зеленеет с GREEN», как строка WR-19 о 16-34.

## Сохранность прежних строк (запрет №2 плана)

- `git diff --stat b1b41431 HEAD` по файлу до плана был пуст. Планирование и волны 1–4 файл не правили.
- После плана `git diff -U0 b1b41431` — 15 изменённых строк и только они:
  - семь `disposition: open → fixed` во frontmatter;
  - `open: 7 → 0`;
  - семь строк таблицы.
- Тридцать девять прежних строк таблицы и их записи frontmatter (`id`, `severity`, `disposition`, `title`) совпадают с `b1b41431`. Это утверждают обе проверки `<automated>`. Метка «(not in the current review)» и суффикс заголовков IN-01…IN-05 на месте.
- В каждой из семи новых строк ровно пять символов `|`. Голого `|` в клетках нет, и следующий прогон `code_review_gate` ничего не экранирует.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md` — семь строк `fixed`, frontmatter в согласии с таблицей.
- `.planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — засев прогнан, файл не изменился.

## Decisions Made

См. `key-decisions`.

## Deviations from Plan

### Отступления

**1. [Rule 2 — полнота записи] Клетки называют, каким коммитом вписаны строки словаря 16-39**
- **Found during:** задача 2.
- **Issue:** форма реестра `<scope_note>` приписывает строки словаря `wrapper-handed`, `starmap` и прочие задаче 2 плана 16-39 с GREEN. Замер `git log -S` показал другое: строки вписаны коммитами теста «f684dc45» / «bb6ce1be», а GREEN `59654f01` / `7a3a7b46` делают их зелёными (шапки, поле `ReferenceCarrier.last`). Клетка «GREEN — строки словаря» была бы неточной.
- **Fix:** GREEN по-прежнему в обратных кавычках там, где тема строки это допускает (WR-25, WR-26). Рядом сказано «вписаны коммитом теста «bb6ce1be» и зеленеют с этим GREEN», по прецеденту строки WR-19.
- **Files modified:** `16-REVIEW-DISPOSITION.md`.
- **Commit:** `dcf972bc`.

**2. Прогон `tests/test_planning` перенесён в конец плана (orchestrator_notes 5)**
- `<verify>` обеих задач и критерии зовут суиту записей после коммита каждой задачи. Оркестратор велит гнать её один раз, после коммита сводки. Прогон — в финальном сообщении исполнителя.
- Остальные проверки `<verify>` прогнаны после каждой задачи.

**3. Замены команд — не понадобились**
- Обе команды `<automated>` с `subprocess.run(['git', …])` внутри `uv run python -c` песочница пропустила. Они прогнаны дословно, без файлов-скриптов.
- Копия `b1b41431` (`.pytest_cache/disposition_b1b41431.md`) сохранена простой командой про запас и не понадобилась.
- `pytest` шёл под `flock`, проверки без `pytest` — без него. Составную проверку ветки с git песочница отклонила, и сторожа выполнены отдельными простыми командами.

**4. Ледгер плана** (`gsd-plan-head-before-16-40`, протокол 0c) записан в `.pytest_cache/`, а не в git-dir worktree. Git-dir лежит под `.git` главного checkout, писать туда orchestrator_notes 2 запрещают. Прецедент — 16-38, 16-39. База — `6e306a63`.

---

**Total deviations:** 1 по существу записи (Rule 2), 3 процедурных.
**Impact on plan:** правился только `16-REVIEW-DISPOSITION.md`. Не тронуты STATE.md, ROADMAP.md, REQUIREMENTS.md, планы, VALIDATION, VERIFICATION, REVIEW, шапка и формулировки реестра. `deferred-items.md` не создавался.

## Гейты на итоговом дереве (`dcf972bc`, 2026-10-19, под `flock`)

| Гейт | Итог | До плана |
|------|------|----------|
| task-1 `<automated>` #1 | `OK` | — |
| task-2 `<automated>` #1 | `OK 20 commits` | — |
| acceptance задачи 2 (нет строк `open`) | `OK` | — |
| `scripts/prohibitions_census.py --seed-registry` | «реестр не изменился: 856 строк» | — |
| `scripts/prohibitions_census.py --check` | код 0, «реестр: 856 строк, биекция с переписью — согласие» | то же |
| оба гейта + паритет поимённо | 847 passed | 847 |
| живые деревья приватности (`-s -k live_trees`) | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| quick run фазы (8 путей) | 1251 passed | 1251 |
| сквозные гейты (htmx_post_pairs, htmx_gates, test_templates, declared_invariants) | 576 passed | 576 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | гонится после коммита сводки (финальное сообщение) | 218 passed, 2 skipped |

План кода не трогает. Числа гейтов не сдвинулись.

## Issues Encountered

Нет.

## Known Stubs

Нет.

## Threat Flags

Нет. Угрозы T-16-94 и T-16-95 закрыты так, как требует план:
- предусловия задач проверены;
- 46 строк, хеши — предки с темами планов;
- прежние строки и записи frontmatter равны `b1b41431`;
- засев только штатный, `--check` — код 0.

## User Setup Required

None — внешней настройки нет.

## Next Phase Readiness

- Все 46 находок ревью фазы 16 разобраны: 41 `fixed`, 5 `deferred` (IN-01…IN-05, О-4), `open: 0`.
- Вход оркестратора: пост-мердж гейт, ревью кода, регрессия и верификация раунда 8. Клетки семи строк — улика для верификатора: хеши, регрессии партии раунда 6 и итоги сверки.
- PHONE-* в REQUIREMENTS.md не отмечались (orchestrator_notes 5). Фаза остаётся в `gaps_found` до повторной верификации.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-19*

## Self-Check: PASSED

- Файл на месте: `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`.
- Коммиты плана в истории ветки: `c5d28203`, `dcf972bc`. `git rev-list --count 6e306a63..dcf972bc` = 2.
- Каждый хеш в обратных кавычках семи клеток — коммит, предок `HEAD`, с темой `feat(<план>)` строки. Проверка задачи 2: `OK 20 commits`.

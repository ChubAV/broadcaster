---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 45
subsystem: planning-records
tags: [review-disposition, wr-27, wr-28, in-18, in-19, in-20, prohibitions-census, records]
status: complete

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-41 — WR-27 (`41f07251`, `3d7dfd86`); 16-42 — сторона писателя WR-28; 16-43 — сторона приватности WR-28 и IN-20; 16-44 — словарь восьмого круга WR-28, IN-18, IN-19 и итог сверки партии раунда 8"
provides:
  - "`16-REVIEW-DISPOSITION.md`: пять находок повторного ревью раунда 7 — `fixed` с исправляющими коммитами `feat(16-41…16-44)`, каждый — предок `HEAD`; 46 прежних строк и их записи во frontmatter байт в байт равны `90052e5c`; `open: 0`, `total: 51`"
  - "Реестр запретов пересеян штатно: «реестр не изменился: 875 строк», `--check` — код 0"
affects: [16-review-round-9, 16-verification]

actuals:
  tokens: 3579    # chars/4 по дифу задач (14 314 симв.: `16-REVIEW-DISPOSITION.md`), без этой сводки
  tasks: 2
  commits: 2      # git rev-list --count b8aaf72d..90eaa74c (до коммита сводки)
plan_head_before: b8aaf72d2d9ee236e01f42186935e2a931c61146
plan_head_after: 90eaa74ca3ebd050f20536cf57fdaa81651e744d

tech-stack:
  added: []
  patterns:
    - "Клетка `fixed`: в обратных кавычках — только GREEN-коммиты плана, чью тему проверка допускает для строки; RED, базы, ревизии ревью и числа — в «ёлочках»"

key-files:
  created: []
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md

key-decisions:
  - "WR-27 названа регрессией счёта партии раунда 7 («51d0d766» против «1c243203»), с итогом сверки по оси счёта: «SELFTEST-COUNT» 16-41 и 16-44 и строки «AGAINST» партии"
  - "WR-28 названа давним пропуском, а не регрессией (форма давала ноль находок на «2f8c1656», «1c243203» и «52fcbadc»); клетка называет все три стороны — писатель 16-42, приватность 16-43, словарь 16-44"
  - "У IN-20 строка `NEGATIVE_CONTROLS` вписана коммитом теста «3e112260» и зелена уже до GREEN — клетка говорит это словами; GREEN `4aef7f97` — правдивый довод и называние строки"
  - "Реестр запретов не изменился — коммита `chore(16-45)` нет: оркестратор засеял строки планов 16-41…16-45 при их коммите"

patterns-established: []

requirements-completed: ["диспозиция-ревью-16"]

coverage:
  - id: D1
    description: "WR-27 — `fixed` с GREEN `41f07251`, `3d7dfd86` (`feat(16-41)`), регрессия счёта названа с итогом сверки по оси счёта; прочие строки прежние; `open: 4` после задачи 1"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t1_disp_1645.py (дословный `python -c` задачи 1) → OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "WR-28, IN-18, IN-19, IN-20 — `fixed`; 15 различных хешей в обратных кавычках (16 вхождений) с темой `feat(<план>)` строки и предки `HEAD`; 46 прежних строк и их frontmatter равны `90052e5c`; `open: 0`, `total: 51`; ни одной строки `open`"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t2_disp_1645.py (дословный `python -c` задачи 2) → OK 16 commits"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_noopen_1645.py (приёмка задачи 2) → OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "Реестр запретов: `--seed-registry` — «реестр не изменился: 875 строк»; `--check` — код 0, биекция"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → exit 0"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py (110 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Суита записей `tests/test_planning` после коммитов учёта — ноль failed"
    requirement: "диспозиция-ревью-16"
    verification: []
    human_judgment: true
    rationale: "`tests/test_planning` по orchestrator_notes 5 гонится один раз — после коммита этой сводки; итог стоит в финальном сообщении исполнителя, а не здесь"

duration: 12min
completed: 2026-10-20
---

# Фаза 16, план 45: диспозиции пяти находок повторного ревью раунда 7 — сводка

**Все пять находок повторного ревью раунда 7 записаны `fixed` с названными исправляющими коммитами партии раунда 8. Каждый хеш в обратных кавычках — коммит, предок `HEAD`, с темой `feat(<план>)` плана, который строка называет: 15 различных хешей, 16 вхождений. WR-27 названа регрессией счёта партии раунда 7 («51d0d766» против «1c243203»), с итогом сверки «база ↔ HEAD» по оси счёта. WR-28 названа давним пропуском. Сорок шесть прежних строк и их записи во frontmatter байт в байт совпадают с `90052e5c`; `open: 0`, `total: 51`. Реестр запретов пересеян штатно, файл не изменился, `--check` — код 0.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-20T04:53:16Z
- **Completed:** 2026-10-20T05:05Z
- **Tasks:** 2 (задача 1 — трасер, задача 2 — `auto`)
- **Files modified:** 1 (`16-REVIEW-DISPOSITION.md`); реестр запретов не изменился

## Accomplishments

- **WR-27 — `fixed`** (задача 1, трасер):
  - GREEN `41f07251`, `3d7dfd86` плана 16-41;
  - названа регрессией счёта партии раунда 7: «51d0d766», 16-37 задача 1, дедупликация по тексту тройки сливала две подачи одной строки, на «1c243203» их было две;
  - итог сверки по оси счёта — строки 16-41 и 16-44 (раздел «Сверка» ниже).
- **WR-28 — `fixed`.** Клетка называет три стороны:
  - писатель — 16-42, `e61ab80d`, `52729753` и циклы `cc7fbce7`, `340d5939`, `96c3eb65`;
  - приватность — 16-43 задачи 1 и 3 и цикл самопроверки, `b0f3c3e1`, `4de6555f`, `a77263ad`;
  - словарь — 16-44 задачи 1–2, `a3c8f299`, `ecfe3566`.

  Это давний пропуск, а не регрессия: восьмой круг оси «где прочитано имя» у гейта писателя и седьмой — у гейта приватности.
- **IN-18, IN-19 — `fixed`:** 16-44 задача 3, GREEN `dbc73537`; правила и числа `--rows` названы.
- **IN-20 — `fixed`:** 16-43 задача 2, GREEN `4aef7f97`. Строка `partial-log-reference-mapped-over-a-phone-attribute` вписана коммитом теста «3e112260» и зелена уже до GREEN — клетка говорит это словами.
- Frontmatter согласован с таблицей: пять записей `disposition: fixed`, `open: 0`, `total: 51`. Заголовки, тяжести и `recorded` прежние.
- Реестр запретов: «реестр не изменился: 875 строк», `--check` — код 0.

## Task Commits

1. **Задача 1 (трасер): WR-27** — `fba083af` `docs(16-45): record WR-27 fixed by plan 16-41 with the count-axis base-HEAD reconciliation`
2. **Задача 2: WR-28, IN-18, IN-19, IN-20; пересев реестра** — `90eaa74c` `docs(16-45): record WR-28, IN-18, IN-19, IN-20 fixed by plans 16-42, 16-43, 16-44`

Коммита `chore(16-45)` нет: `--seed-registry` файл не изменил. Коммит сводки — `docs(16-45)`, следующий за этими.

## Хеши клеток `fixed` (проверены до записи)

Каждый хеш проверен тремя способами:
- `git log --no-walk --format='%h %s'` — тема;
- присутствие в `git log fb8fef72..HEAD`;
- после записи — дословной проверкой задачи 2: `git log -1 --format=%s` и `git merge-base --is-ancestor <хеш> HEAD` для каждого вхождения.

| Строка | В обратных кавычках | Тема | В «ёлочках» (не исправляющие) |
|--------|---------------------|------|-------------------------------|
| WR-27 | `41f07251`, `3d7dfd86` | `feat(16-41)` | «51d0d766», «1c243203», «a6c87597», «fb8fef72», «dbc73537»; RED «597f1220», «87d2c5d1» |
| WR-28 | `e61ab80d` (дважды), `52729753`, `cc7fbce7`, `340d5939`, `96c3eb65` / `b0f3c3e1`, `4de6555f`, `a77263ad` / `a3c8f299`, `ecfe3566` | `feat(16-42)` / `feat(16-43)` / `feat(16-44)` | «2f8c1656», «1c243203», «52fcbadc», «dbc73537»; RED «e62799d3», «56d13690», «68c68d97», «ec96cf2e», «8cac1bac», «c253f8bb», «7b2f470e», «e1d6587e», «53f2483b», «cf27c862» |
| IN-18 | `dbc73537` | `feat(16-44)` | «147f5e46», «c6953017»; RED «c13c119b» |
| IN-19 | `dbc73537` | `feat(16-44)` | RED «c13c119b» |
| IN-20 | `4aef7f97` | `feat(16-43)` | «1c243203», «52fcbadc»; RED «3e112260» |

Итог проверки задачи 2: `OK 16 commits` — 16 вхождений, 15 различных хешей. Нижняя граница приёмки — 7.

## Сверка «база ↔ HEAD» — строки, на которые ссылаются клетки

Цитаты дословные, из сводок. Сам план сверку не гонял: он кода не трогает.

**16-41** (`16-41-SUMMARY.md`, итоговый прогон `run.sh 16-41`, HEAD `3d7dfd86`):

```
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3522 regressions=831 count_regressions=1237 fixed=26 repaired_overcount=2 changed=1317
BASE fb8fef72 -> HEAD 3d7dfd86: cells=58394 regressions=0 count_regressions=0 fixed=4536 repaired_overcount=0 changed=7015
OPEN_REGRESSIONS=0
```

**16-44, итог партии раунда 8** (`16-44-SUMMARY.md`, `final_chain.sh` на `dbc73537`, `CHAIN_EXIT=0`):

```
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3591 regressions=831 count_regressions=885 fixed=378 repaired_overcount=354 changed=1317
HEAD_WRONG=0
OPEN_REGRESSIONS=0
AGAINST fb8fef72 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=8974 repaired_overcount=65 changed=7751
AGAINST 1c243203 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=13488 repaired_overcount=948 changed=11648
AGAINST 2f8c1656 -> HEAD dbc73537: cells=64483 regressions=0 count_regressions=0 fixed=23366 repaired_overcount=777 changed=20878
```

«885» меньше «1237» 16-41, потому что 16-44 дал ячейкам D2 (ж) точное число. Его сводка, отступление 4: 352 ячейки D2 приватности перешли в `REPAIRED` у `51d0d766` — это задуманная починка WR-24. Ось счёта по-прежнему видит регрессию WR-27: «885» > 0. Клетка WR-27 называет это словами.

Регрессировавших ячеек партии раунда 8 нет ни у одного GREEN (16-44-SUMMARY, таблица «Регрессировавшие ячейки партии»).

## Гейты на итоговом дереве (`90eaa74c`, под общим `flock`)

| Проверка | Итог | До плана (после волн 1–4) |
|----------|------|---------------------------|
| `<automated>` задачи 1 №1 (`t1_disp_1645.py`) | `OK` | — |
| `<automated>` задачи 2 №1 (`t2_disp_1645.py`) | `OK 16 commits` | — |
| приёмка задачи 2, ни одной `open` (`t2_noopen_1645.py`) | `OK` | — |
| `scripts/prohibitions_census.py --seed-registry` | «реестр не изменился: 875 строк» | 875 |
| `scripts/prohibitions_census.py --check` | код 0, «реестр: 875 строк, биекция с переписью — согласие» | код 0 |
| `tests/test_planning/test_plan_prohibitions_census.py` | `110 passed` | 110 |
| оба гейта + паритет поимённо | `891 passed` | 891 |
| живые деревья приватности (`-s -k live_trees`) | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| quick run фазы (8 путей) | `1295 passed` | 1295 |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `test_templates`, `test_declared_invariants`) | `576 passed` | 576 |
| `tests/test_planning` | гонится после коммита сводки (финальное сообщение) | 218 passed, 2 skipped |

План кода не трогает. Числа гейтов совпадают с замером после волн 1–4, сдвигов нет.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`:
  - пять строк таблицы `open` → `fixed` с клетками Source;
  - пять записей frontmatter `disposition: fixed`;
  - `open: 5` → `0`.
- `.planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — не изменился: засев идемпотентен, строки планов 16-41…16-45 оркестратор засеял при их коммите.

Проверки (gitignored): `.pytest_cache/checks/t1_disp_1645.py`, `t2_disp_1645.py`, `t2_noopen_1645.py`. Журнал плана — `.pytest_cache/gsd-plan-head-before-16-45`.

## Decisions Made

- **Клетка WR-27** называет регрессию «51d0d766» против «1c243203» и обе меры оси счёта:
  - «SELFTEST-COUNT» видит регрессию у 16-41 («1237») и у итога партии («885»);
  - «BASE» плана и «AGAINST» партии — ноль регрессий обеих осей.

  Объяснение разницы «1237» → «885» дано в самой клетке, чтобы верификатор раунда 9 не прочёл её как потерю чувствительности.
- **Клетка WR-28** называет все GREEN трёх планов, включая циклы зонда, летописи и самопроверки той же оси (16-42 — три цикла, 16-43 — один). Их темы — `feat(16-42)` / `feat(16-43)`, проверка допускает все три темы строки.
- **IN-20.** Строку `NEGATIVE_CONTROLS` вписал коммит теста «3e112260», и она зелена до GREEN: форму гейт ловит со времени партии раунда 7, ревью замерило одну находку на «52fcbadc». Клетка говорит это словами, по прецеденту WR-19 и отступления 1 сводки 16-40.
- **Открытый пункт вне пяти находок — не строка диспозиции.** Это получатель журнала, связанный с ИМЕНЕМ модуля и прочитанный getattr-строкой: `getattr(sys.modules[__name__], "lg").info("x %s", account.phone)`. Он даёт `[]` на HEAD, на базе партии и на «1c243203» (16-43-SUMMARY, 16-44-SUMMARY). В пять находок ревью он не входит и клетки WR-28 не касается: WR-28 — об имени, связанном с `methodcaller`. Адресат — владелец и следующее ревью, ось «как опознан журнал». Строкой таблицы он не записан.

## Deviations from Plan

### Отступления

**1. Прогон `tests/test_planning` перенесён в конец плана (orchestrator_notes 5).**
- Проверки задач 1 и 2 называют `uv run pytest tests/test_planning -q -p no:randomly`. Заметка оркестратора велит гнать его один раз — после коммита сводки.
- Трасер задачи 1 проверен повторным прогоном первой проверки. Режим `end-of-phase`, прогон интерактивный, в `<verify>` только `<automated>` — «Tracer verified end-to-end — expanding».
- Итог `tests/test_planning` — в финальном сообщении оркестратору.

**2. Замены команд (песочница worktree, orchestrator_notes 3).** Однострочники `python -c` из `<automated>` и приёмки записаны дословно в `.pytest_cache/checks/*.py` и запущены `PYTHONPATH=. uv run python <файл>`. Логика и утверждения те же, `;` заменены переводами строк. `git` изнутри Python песочница не отклонила, поэтому `subprocess.run(['git', 'show', '90052e5c:…'])` остался как в плане, без сохранения эталона в файл. Составная команда с `git` в цикле `for` отклонена. Хеши проверены простыми командами: `git log --no-walk` и `git log fb8fef72..HEAD`. Проверка предков — в скрипте задачи 2.

**3. Журнал плана в `.pytest_cache/`.** Файл `gsd-plan-head-before-16-45` лежит не в git-каталоге worktree, как у 16-43 и 16-44.

---

**Total deviations:** 3 записанных отступления (порядок прогона по заметке оркестратора, замены команд, место журнала). Ничего не ослаблено.
**Impact on plan:** правился только `16-REVIEW-DISPOSITION.md`. Реестр не изменился. STATE.md, ROADMAP.md, REQUIREMENTS.md, PLAN/VALIDATION/VERIFICATION/REVIEW не тронуты, `deferred-items.md` не создавался.

## Issues Encountered

Нет.

## Known Stubs

Нет.

## Threat Flags

Нет: правка одного файла учёта, новых поверхностей нет. T-16-104 закрыт проверкой задачи 2. T-16-105 закрыт штатным засевом без правки и `--check` с кодом 0.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Партия раунда 8 закрыта по записи: 51 из 51 находки имеет диспозицию, ни одной `open`.
- Дальше — работа оркестратора: пост-мердж гейт, ревью кода, регрессия и верификация раунда 9.
- Владельцу и следующему ревью: открытый пункт о получателе журнала под именем модуля, прочитанном getattr-строкой (см. «Decisions Made»).
- `human_verification` 1 `16-VERIFICATION.md` (сверка 115 вердиктов запретов) — акт владельца в обходе `/gsd-verify-work`; план его не исполнял.

## Self-Check: PASSED

- `16-REVIEW-DISPOSITION.md` — FOUND; `.pytest_cache/checks/{t1_disp_1645.py,t2_disp_1645.py,t2_noopen_1645.py}` — FOUND.
- Коммиты `fba083af`, `90eaa74c` — предки HEAD (FOUND).
- `git rev-list --count b8aaf72d..90eaa74c` = 2; изменений вне коммитов нет до записи этой сводки.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-20*

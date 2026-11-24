---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 35
subsystem: planning-records
tags: [code-review-disposition, prohibitions-registry, records, wr-18, wr-19, wr-20, wr-21, wr-22, wr-23, in-15]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "исправляющие коммиты партии раунда 6 — 16-31 (WR-18), 16-32 (WR-19, WR-20, IN-15), 16-33 (WR-21, WR-22, WR-23), 16-34 (WR-19, WR-20, IN-15); реестр диспозиций на `749ddfc5` (семь строк раунда 5 — `open`)"
provides:
  - "`16-REVIEW-DISPOSITION.md`: семь строк повторного ревью раунда 5 — `fixed` с 19 различными хешами GREEN («26» ссылок), поправка довода клетки WR-16 — в клетке WR-21; 32 прежние строки и их записи frontmatter байт в байт с `749ddfc5`; frontmatter `open: 0`, `total: 39`"
  - "реестр запретов: `--seed-registry` оставил файл без изменений (837 строк), `--check` — код 0"
affects: [16-verify-work, 16-code-review, phase-17]

actuals:
  tokens: 3864
  tasks: 2
  commits: 2
plan_head_before: daf5a5666663d351ed447212dd39171cf0d65749
plan_head_after: ce2af977028af2df65387ea781d4bf8ccecb7a4d

tech-stack:
  added: []
  patterns:
    - "Клетка Source `fixed` называет GREEN хешами в обратных кавычках, а коммиты теста (RED и коммит, вписавший строки словаря) — в «ёлочках», чтобы проверка хешей не читала их как исправляющие"
    - "Остаток, записанный исполнившим планом сверх находки ревью, называется одной фразой в клетке закрытой находки, без новых строк и записей frontmatter"

key-files:
  created:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-35-SUMMARY.md
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md

key-decisions:
  - "WR-19: строки `REFERENCE_CARRIERS` вписал коммит теста «9dc72673» (тема `test(16-34)`), а GREEN — `a28d6efc`; в клетке GREEN в обратных кавычках, коммит теста — в «ёлочках» (16-34-SUMMARY называл «9dc72673» коммитом строк)"
  - "IN-15 закрыт как его написало ревью (структурная половина и докстринг; копии `_iterable_elements` / `_getattr_literal`), но клетка называет остаток 16-34 (а)–(в): своя `_carrier_wrappers` гейта приватности, комментарий `:362` о `REFERENCE_KEYWORDS`, формы самопроверки вне `REFERENCE_CARRIERS`"
  - "Сверх списка задач плана в клетки добавлены GREEN циклов самопроверки, где сводки их называют: WR-21 — `e72a8e53`, `c5e82453`; WR-22 — `e72a8e53` (`_SQL_HEAD_GAP` головы (в) / (г)); WR-23 — шапка задачи 3 `6fbc414c`"

patterns-established: []

requirements-completed: ["диспозиция-ревью-16"]

coverage:
  - id: D1
    description: "WR-18 — `fixed`, клетка Source называет 16-31 задачи 1–3 и цикл самопроверки, четыре GREEN-хеша — предки HEAD с темой `feat(16-31)`; прочие 38 строк прежние, `open: 6` после задачи 1"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "task-1 <automated> #1 плана 16-35 (скрипт `.pytest_cache/1635/check_task1.py`, та же логика) — OK"
        status: pass
      - kind: other
        ref: "git merge-base --is-ancestor d3304aab / 0b7a503b / 2a506aea / ebe466ac HEAD — код 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "WR-19, WR-20, WR-21, WR-22, WR-23, IN-15 — `fixed` с хешами `feat(<план>)` названных планов; клетка WR-21 несёт поправку довода WR-16; 32 прежние строки и их frontmatter равны `749ddfc5`; frontmatter равен таблице, `open: 0`, `total: 39`"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "task-2 <automated> #1 плана 16-35 (скрипт `.pytest_cache/1635/check_task2.py`, те же утверждения) — OK 26 commits"
        status: pass
      - kind: other
        ref: "критерий «ни одной строки open» (python -c плана дословно) — OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "Реестр запретов согласован: засев идемпотентен (файл не изменился), перепись и суита записей зелёные"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check — код 0, 837 строк"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py — 110 passed"
        status: pass
      - kind: unit
        ref: "tests/test_planning — 218 passed, 2 skipped"
        status: pass
    human_judgment: false
  - id: D4
    description: "Правдивость клеток: каждая клетка не утверждает больше, чем сделали коммиты (в том числе остаток 16-34 в клетке IN-15)"
    verification: []
    human_judgment: true
    rationale: "Соответствие прозы клеток содержанию коммитов машина не судит: проверка хешей подтверждает только существование, предков и темы; смысл фраз сверяют ревью и верификатор"

duration: 12min
completed: 2026-10-16
status: complete
---

# Phase 16 Plan 35: Диспозиции семи находок повторного ревью раунда 5 — Summary

**Семь находок `16-REVIEW.md` раунда 5 (WR-18…WR-23, IN-15) записаны в `16-REVIEW-DISPOSITION.md` как `fixed`. Клетка каждой называет план, задачи и GREEN-хеши партии раунда 6: 19 различных коммитов, 26 ссылок; каждый хеш — предок HEAD с темой `feat(<план>)`. Неверный довод клетки WR-16 исправлен записью в клетке WR-21. Тридцать две прежние строки перенесены байт в байт с `749ddfc5`, frontmatter `open: 0`, `total: 39`. Пересев реестра запретов файл не изменил.**

## Performance

- **Duration:** ≈12 мин
- **Started:** 2026-10-16T13:20:24Z
- **Completed:** 2026-10-16T13:32:19Z
- **Tasks:** 2
- **Files modified:** 1 (плюс эта сводка)

## Accomplishments

- **WR-18** (задача 1, трасер). Клетка называет `16-31` задачи 1–3 (GREEN `d3304aab`, `0b7a503b`, `2a506aea`) и цикл самопроверки (GREEN `ebe466ac`), решение О-14 (а). Суть: многозначные карты псевдонимов гейта писателя, одна находка на место, каждый кандидат `methodcaller` у гейта приватности, три строки `rebound*` с полем `decoy`. Число самопроверки — «134 460» форм. RED-коммиты стоят в «ёлочках».
- **WR-19.** `16-32` задачи 1–3 (`c6953017`, `50d6e5cf`, `8a28d2e7`) и циклы (`6231a0b3`, `5e57325d`). Строки носителей и паритет — `16-34` задача 2 (`a28d6efc`). Сами строки вписал коммит теста «9dc72673» (см. «Решения»).
- **WR-20.** Сторона приватности — `16-32` задача 1 (`c6953017`). Сторона писателя — `16-34` задачи 1–3 (`94b6c25d`, `a28d6efc`, `e5987a35`) и циклы (`147f5e46`, `21d463f0`). Клетка называет общее правило именованного аргумента, вывод `REFERENCE_KEYWORDS`, снятое расхождение на `Timer(…, args=…)`, цену и пункт (1) границы.
- **WR-21.** `16-33` задачи 1 и 3 (`e478c8c2`, `6fbc414c`) и циклы (`e72a8e53`, `c5e82453`). Четвёртый вид кавычек; разбор отрезков `_sql_scan` для ключевых слов; цена однословной строки по замеру 16-33. Поправка клетки WR-16 — по форме `<scope_note>`, с замером «+78». Строка WR-16 не тронута.
- **WR-22.** `16-33` задача 1 (`e478c8c2`) и цикл 1 (`e72a8e53`, `_SQL_HEAD_GAP`): головы (в) / (г) судятся по видимому SQL.
- **WR-23.** `16-33` задача 2 (`8aba9962`), шапка вида 3 — задача 3 (`6fbc414c`). `Column` / `ColumnClause`, `name`, три наименования и две позиции имени.
- **IN-15.** `16-32` задача 2 (`50d6e5cf`) и `16-34` задача 2 (`a28d6efc`), решение О-15. Остаток 16-34 (а)–(в) назван одной фразой (раздел ниже).
- **Frontmatter.** У семи записей `disposition: fixed`, `open: 7 → 6 → 0`, `total: 39`. Заголовки, `recorded`, `titles: json` не тронуты.
- **Реестр запретов.** `--seed-registry` вывел «реестр не изменился: 837 строк», `git status` чист по файлу реестра. Оркестратор засеял строки 16-31…16-35 коммитом `2b0c9ec1`.

## Task Commits

1. **Задача 1 (трасер): WR-18 → `fixed`** — `d2133c20` (docs).
2. **Задача 2: WR-19…WR-23, IN-15 → `fixed`, frontmatter, пересев реестра** — `ce2af977` (docs).

**Plan metadata:** коммит `docs(16-35)` с этой сводкой.

Гейт трасера после задачи 1. Атрибута `gate` нет, `auto_advance: false`, режим `end-of-phase`, у задачи только `<automated>`. Обе команды прогнаны повторно на закоммиченном дереве: `OK` и `218 passed, 2 skipped`. После этого план перешёл к задаче 2.

## Сверка хешей (19 различных, 26 ссылок)

Каждый хеш в обратных кавычках проверен двумя путями:
- **Скрипт задачи 2** (логика плана): тема начинается с допустимого `feat(<план>)` строки, хеш есть в `git rev-list HEAD`.
- **Прямой `git merge-base --is-ancestor <хеш> HEAD`** по каждому из 19: код 0.

| Строка | Хеши (GREEN) | Темы |
|--------|--------------|------|
| WR-18 | `d3304aab`, `0b7a503b`, `2a506aea`, `ebe466ac` | `feat(16-31)` × 4 |
| WR-19 | `c6953017`, `50d6e5cf`, `8a28d2e7`, `6231a0b3`, `5e57325d`, `a28d6efc` | `feat(16-32)` × 5, `feat(16-34)` × 1 |
| WR-20 | `c6953017`, `94b6c25d`, `a28d6efc`, `e5987a35`, `147f5e46`, `21d463f0` | `feat(16-32)` × 1, `feat(16-34)` × 5 |
| WR-21 | `e478c8c2`, `6fbc414c`, `e72a8e53`, `c5e82453` | `feat(16-33)` × 4 |
| WR-22 | `e478c8c2`, `e72a8e53` | `feat(16-33)` × 2 |
| WR-23 | `8aba9962`, `6fbc414c` | `feat(16-33)` × 2 |
| IN-15 | `50d6e5cf`, `a28d6efc` | `feat(16-32)`, `feat(16-34)` |

Коммиты теста («a9e1f6a1», «8e411e06», «97434b5b», «c7c297ed», «9dc72673») записаны в «ёлочках»: проверка их как исправляющие не читает.

## Остаётся открытым — остаток 16-34 (не находки `16-REVIEW.md`)

Эти три пункта — не находки ревью раунда 5. Поэтому у них нет новых строк и записей frontmatter: таблица закреплена планом на семи находках. Клетка IN-15 называет их одной фразой со ссылкой на 16-34-SUMMARY («Остаётся открытым»). Оркестратору — для code review и верификатора:

- **(а)** Гейт приватности держит свою `_carrier_wrappers` (`tests/test_phone_privacy_gate.py:882`). Это семантика именованной обёртки носителя, которую гейт писателя берёт из общего модуля (`carrier_wrapper_bindings` / `applied_wrapper`, `147f5e46`). Запрет №4 плана 16-34 разрешал ему только строку ввоза. Копия под другим именем — структурная половина паритета её по построению не видит.
- **(б)** Комментарий `tests/test_phone_privacy_gate.py:362` всё ещё называет выведенную `REFERENCE_KEYWORDS` (замер на этом дереве: строка 362 — «… как и `ELEMENTWISE_CARRIERS` и `REFERENCE_KEYWORDS`»).
- **(в)** Формы самопроверки 16-34 закреплены строками гейта писателя, но не строками `REFERENCE_CARRIERS` (на дереве 11 носителей). Это именованная обёртка носителя, позиционные кортежи `apply_async`, `starmap`. Поведенческая половина правила-паритета их поэтому не держит.

Клетка IN-15 не утверждает, что «копий семантики носителя в модулях гейтов нет». Она говорит, что сняты копии `_iterable_elements` / `_getattr_literal` и прочие копии гейта писателя, а докстринг паритета называет проверяемое. Клетка WR-19 о копиях не говорит.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`: семь строк таблицы и семь записей frontmatter, `open: 0`.
- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-35-SUMMARY.md` — эта сводка.
- Реестр `.planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — засев прогнан, файл не изменился.

## Decisions Made

- **Коммит строк WR-19 — RED, а не GREEN.** 16-34-SUMMARY пишет: «WR-19 на стороне писателя закрыт строками словаря (`9dc72673`)». Замер `git show --stat 9dc72673`: тема `test(16-34): add six REFERENCE_CARRIERS rows …`. Шесть строк вписал этот коммит, а зеленеют они с GREEN `a28d6efc`. Хеш в обратных кавычках с темой `test(…)` нарушил бы договор О-4 («`fixed` только с исправляющим коммитом `feat(<план>)`»). Поэтому `a28d6efc` стоит в обратных кавычках, а «9dc72673» — в «ёлочках» с пояснением. То же в клетке IN-15: имена в `GRAMMAR_FUNCTIONS` / `GRAMMAR_TABLES` и правило-контроль вписал «9dc72673», докстринги паритета — `a28d6efc`.
- **Числа `GRAMMAR_FUNCTIONS` — на итоговом дереве.** «24» имени и «7» таблиц — после цикла самопроверки 16-34 (после задачи 2 было 20 имён). Клетка IN-15 так и пишет: «на итоговом дереве 16-34». Замер на этом дереве: `24 7 6`, `REFERENCE_CARRIERS` — 11, `BINDING_FORMS` — 12, `REFERENCE_KEYWORDS` отсутствует.
- **Хеши циклов самопроверки — в клетках находок, которые они закрывали.** Сводки называют циклы явно, и каждый закрывал класс той же оси. Нижняя граница плана (≥ 10) — пол, а не цель.

## Deviations from Plan

### Auto-fixed Issues

None — содержимое записей по плану. Ниже — только замены команд под песочницу worktree; логика и утверждения прежние.

### Замены команд (песочница worktree, orchestrator_notes 3)

- **Task-1 `<automated>` #1** (`git show` внутри `python -c`). Эталон сохранён простой командой `git show 749ddfc5:<p> > .pytest_cache/1635/disposition_749ddfc5.md`. Та же логика исполнена скриптом `.pytest_cache/1635/check_task1.py`. До правок `diff` эталона с файлом пуст (`IDENTICAL`).
- **Task-2 `<automated>` #1** (`git show`, `git log -1`, `git merge-base` внутри `python -c`). Темы читаются из `.pytest_cache/1635/log_head.tsv` (`git log --format=%H%x09%s -n 600`). Предки — из `.pytest_cache/1635/revlist_head.txt` (`git rev-list HEAD`, 3434 коммита). Хеш без единственного полного совпадения падает, как `check=True` на не-коммите. Скрипт `.pytest_cache/1635/check_task2.py` держит те же утверждения. Дополнительно прогнан прямой `git merge-base --is-ancestor` по каждому из 19 хешей двумя цепочками `&&` (без `for`).
- **Precondition-проверка `git log --grep='^feat(16-3N)'`** отвергнута песочницей как сложная. Её заменил `git log --oneline --grep=feat.16-3 -n 40`: напечатал 19 коммитов `feat(16-31)`…`feat(16-34)`. Сводки 16-31…16-34 на месте.
- Всё в `.pytest_cache/` (gitignored), в репозиторий не коммитится.

---

**Total deviations:** 0 auto-fixed; 3 замены команд, названные выше.
**Impact on plan:** нет. Код, тесты, STATE.md, ROADMAP.md, REQUIREMENTS.md, планы и VALIDATION / VERIFICATION / REVIEW не тронуты.

## Гейты на итоговом дереве (`ce2af977`, 2026-10-16, под `flock`)

- Task-2 `<automated>` #1 (скрипт) — `OK 26 commits`. Строки: WR-18 4, WR-19 6, WR-20 6, WR-21 4, WR-22 2, WR-23 2, IN-15 2.
- Критерий «ни одной строки `open`» (python -c плана дословно) — `OK`.
- `scripts/prohibitions_census.py --seed-registry` — «реестр не изменился: 837 строк». `--check` — код 0, «реестр: 837 строк, биекция с переписью — согласие».
- `tests/test_planning/test_plan_prohibitions_census.py` — `110 passed`.
- Оба гейта и паритет поимённо (`test_phone_privacy_gate.py`, `test_phone_single_writer_gate.py`, `test_phone_gates_parity.py`) — `792 passed`, как в 16-34: дрейфа нет.
- Замер приватности `-s -k live_trees`: «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0».
- Quick run фазы (8 путей с модулем паритета) — `1196 passed`, как в 16-34.
- Сквозные гейты `test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py` — `576 passed` (2 мин 43 с).
- `tests/test_planning`: `218 passed, 2 skipped` после коммита задачи 1 и после коммита задачи 2. Прогон после коммита этой сводки — в финальном сообщении исполнителя.
- Полная суита не гонялась: её гонит оркестратор (orchestrator_notes 6). `graphify update .` не запускался.

## Issues Encountered

Нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Все 39 находок фаз 16 разобраны: 34 `fixed`, 5 `deferred`, 0 `open`. Отметку `- [x]` плана в ROADMAP, `progress.completed_plans` и прозу счёта планов правит оркестратор после слияния.
- Остаток 16-34 (а)–(в) — для code review и верификатора раунда 7 (раздел выше).
- Перед `/gsd-verify-work` — полный `just test` (гейт фазы), затем `/gsd-validate-phase 16`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-16*

## Self-Check: PASSED

- FOUND: .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md
- FOUND (ancestors of HEAD): d2133c20, ce2af977
- FOUND (ancestors of HEAD, cited in cells): d3304aab, 0b7a503b, 2a506aea, ebe466ac, c6953017, 50d6e5cf, 8a28d2e7, 6231a0b3, 5e57325d, a28d6efc, 94b6c25d, e5987a35, 147f5e46, 21d463f0, e478c8c2, 6fbc414c, e72a8e53, c5e82453, 8aba9962

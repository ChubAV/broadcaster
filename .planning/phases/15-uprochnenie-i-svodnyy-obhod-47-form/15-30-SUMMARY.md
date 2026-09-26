---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 30
subsystem: planning-records
tags: [prohibitions-census, registry, record-mode, git-history, d-05, criterion-6, g-1, d-16, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-13 — 27 находок D-05 `declared-rule-absent`; план 15-22 — режим `--record` и `record_coverage`; план 15-29 — предыдущий план волны, протокол записи"
  - phase: 10-rychag-components-modal-html
    provides: "четырнадцать исторических запретов «этим планом путь X не правится» с `verification: test` (планы 10-36…10-51) и коммиты этих планов в истории"
provides:
  - "модуль `tests/test_planning/test_executed_plans_kept_their_scope.py`: журнал git «коммит → тема → пути», прочитанный один раз; чистые `_parse_journal`, `_plan_commits`, `_path_offences`; отказ `HistoryRefusal` на мелком клоне, пустом отборе, пустом перечне и отборе без путей"
  - "`HISTORY_FACTS` — 14 записей (область темы + запрещённые пути по полной формулировке); правило `test_every_declared_history_fact_holds_over_its_plans_commits` (14 случаев) и правило согласия `test_every_history_fact_names_a_phase_10_prohibition_by_identity`"
  - "14 строк реестра D-05 записаны `enforced` через `--record`; `declared-rule-absent` в области решений 26 → 12"
affects: [15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 14460
  tasks: 2
  commits: 4
plan_head_before: 5d12fd6b51501e541b13b39b5c839a1ad4854d9c

tech-stack:
  added: []
  patterns:
    - "Исторический факт плана держится его собственными коммитами: отбор по ОБЛАСТИ В ТЕМЕ `тип(Ф-П):` (без ведущих нулей), пути через `--name-only --no-renames`; тело сообщения журнал не несёт"
    - "Живой ввод читается один раз (`functools.cache`), а всё суждение — чистые функции поданного журнала; каждое свойство показано контролем на синтетическом журнале, направление — на копии живого журнала с добавленным коммитом"
    - "Полнота истории — предусловие, а не пропуск: `--is-shallow-repository` обязан ответить ровно `false`, иначе отказ с названной причиной ДО чтения журнала"

key-files:
  created:
    - tests/test_planning/test_executed_plans_kept_their_scope.py
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-30: «ПРОДУКТ» в формулировках `10-39#5`, `10-40#4`, `10-44#5`, `10-48#4` прочитан как все отслеживаемые корни сборки и запуска (22 корня, `git ls-tree HEAD` 2026-09-26), а не только `app/`, как в таблице планирования: план велит брать полную формулировку. Не продукт — `.planning/`, `CLAUDE.md`, `README.md`, `design/`, `new_broadcaster_design.html`, `.gitignore`"
  - "15-30: все 14 строк записаны `enforced`, частичных нет. Каждая формулировка сводится к «эти пути планом не тронуты»; хвосты после двоеточия (способ «контроли доктóрят копии» у `10-38#3`, «ветвь отказа объявляет расхождение» у `10-40#4`) — обоснование, а не второй предмет. `10-40#3` и `10-37#0`/`10-38#3` держатся строже буквы: файл целиком вместо одной записи или одного объявления"
  - "15-30: правило согласия утверждает одно направление реестра — каждая строка, называющая несущее правило, имеет запись в `HISTORY_FACTS`. Обратное (каждая запись названа строкой) не утверждается: лишняя запись — лишняя проверка, а не ложное принуждение. Двустороннее равенство сделало бы красным коммит `feat` до записи реестра"

patterns-established:
  - "Правило над историей git называет четыре границы в докстринге: полная история (мелкий клон — отказ), коммиты без области в теме невидимы, переписанная история вне области, слияния путей не несут"

requirements-completed: []

coverage:
  - id: D1
    description: "Инструмент исторических фактов: журнал читается один раз, отбор по области темы точен (коммит `docs(10): … (10-44)` чужой), путь назван с коммитом, пустой отбор / пустой перечень / отбор без путей / мелкий клон — отказ, а не зелень"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_the_journal_text_parses_into_hash_subject_and_paths"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_the_plan_commits_are_selected_by_the_subject_scope_only"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_forbidden_path_is_named_with_its_commit_and_an_allowed_one_is_not"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_an_empty_commit_selection_is_a_refusal_not_a_green"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_shallow_clone_is_refused_before_the_journal_is_parsed"
        status: pass
    human_judgment: false
  - id: D2
    description: "Четырнадцать исторических запретов Фазы 10 держатся проверкой коммитов своих планов; синтетический коммит на запрещённом пути краснит запись; каждый ключ — тождество записи переписи Фазы 10 с `verification: test`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_every_declared_history_fact_holds_over_its_plans_commits"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_every_history_fact_names_a_phase_10_prohibition_by_identity"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_executed_plans_kept_their_scope.py#test_control_a_synthetic_commit_on_a_forbidden_path_reddens_10_44_5"
        status: pass
    human_judgment: false
  - id: D3
    description: "14 строк реестра записаны `enforced` только через `--record`; биекция 741 строки в согласии; каталог Фазы 10 не тронут"
    requirement: "критерий-6"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --list --phase 10 | grep -E '<14 тождеств>' | grep -c 'disposition=enforced' → 14"
        status: pass
      - kind: other
        ref: "git diff --stat 5d12fd6b..HEAD -- .planning/phases/10-rychag-components-modal-html/ → пусто"
        status: pass
      - kind: unit
        ref: "tests/test_planning/test_plan_prohibitions_census.py (весь модуль, в составе tests/test_planning/ → 161 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Прочтение формулировок в перечни путей: «ПРОДУКТ» = 22 корня сборки и запуска, все 14 строк полные, а не частичные"
    requirement: "критерий-6"
    verification: []
    human_judgment: true
    rationale: "Перевод прозы запрета в перечень путей — суждение исполнителя, записанное комментарием над каждой записью `HISTORY_FACTS`. Верно ли оно читает формулировки, решают владелец (`chubav`) и верификатор фазы"

duration: 10min
completed: 2026-09-26
status: complete
---

# Phase 15 Plan 30: Исторические запреты Фазы 10 держатся коммитами своих планов Summary

**Новый модуль правил читает журнал git один раз и отбирает коммиты плана по области в теме `тип(10-NN):`. Он проверяет, что ни один из них не коснулся пути, объявленного запретом нетронутым. Четырнадцать запретов D-05 с предметом «пути» (10-36…10-51) записаны `enforced`. Мелкий клон и пустой отбор дают отказ с названной причиной, а не зелень.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-26T00:07:36Z
- **Completed:** 2026-09-26T00:17:29Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- **Задача 1 (TDD).** Модуль `tests/test_planning/test_executed_plans_kept_their_scope.py` с маркером `planning` и докстрингом D-16. В докстринге названы четыре границы истории и абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ». Журнал снимается одним вызовом `git -c core.quotePath=false log --no-renames --name-only --format=%x1e%H%x1f%s HEAD`, кэшируется, и дальше его разбирают чистые функции. Пять контролей на синтетическом журнале: разбор; отбор по теме (`docs(10): … (10-44)`, соседний `10-4` и `fix:` без области не отбираются, `docs(010-044):` отбирается); путь назван с коммитом; три антивакуумных отказа; мелкий клон отказывает до запроса журнала.
- **Задача 2.** `HISTORY_FACTS` — 14 записей, над каждой прочтение формулировки. Несущее правило параметризовано 14 тождествами. Правило согласия сверяет каждый ключ с переписью (фаза 10, `verification: test`, область = номер плана) и требует, чтобы каждая строка реестра, называющая несущее правило, имела запись. Контроль направления стоит на живом журнале.
- **Реестр.** 14 строк переведены из `unresolved` (`declared-rule-absent`) в `enforced` через `--record`. `declared-rule-absent` в области решений 26 → 12. `product-invariant` не затронут: ни одна строка группы не этого класса (классы: `plan-file-scope` 10, `gate-integrity`, `record-immutability`, `self-certification`, `work-owned-elsewhere` по 1). Биекция 741 строки в согласии.

## Таблица фактов

| Тождество | Класс | Запрещённые пути (по полной формулировке) | Коммитов плана | Путей в них | Нарушений | Синтетический коммит |
|---|---|---|---|---|---|---|
| `10-36#2` | gate-integrity | `app/templates/` | 6 | 9 | 0 | красный |
| `10-37#0` | plan-file-scope | `app/static/css/app.css` | 8 | 10 | 0 | красный |
| `10-38#2` | plan-file-scope | `app/templates/` | 6 | 9 | 0 | красный |
| `10-38#3` | plan-file-scope | `app/static/css/app.css` | 6 | 9 | 0 | красный |
| `10-39#4` | work-owned-elsewhere | `tests/test_pages/test_shell.py`, `app/static/css/app.css` | 6 | 9 | 0 | красный |
| `10-39#5` | plan-file-scope | ПРОДУКТ (22 корня) + `tests/` | 6 | 9 | 0 | красный |
| `10-40#3` | record-immutability | `…/10-CONTEXT.md` | 2 | 4 | 0 | красный |
| `10-40#4` | plan-file-scope | ПРОДУКТ + `tests/` | 2 | 4 | 0 | красный |
| `10-44#2` | self-certification | `…/10-VERIFICATION.md` | 7 | 11 | 0 | красный |
| `10-44#5` | plan-file-scope | ПРОДУКТ + `tests/` | 7 | 11 | 0 | красный |
| `10-48#4` | plan-file-scope | ПРОДУКТ | 4 | 6 | 0 | красный |
| `10-49#4` | plan-file-scope | `app/static/css/app.css` | 4 | 8 | 0 | красный |
| `10-50#4` | plan-file-scope | `…/htmx_error_banner.html`, `…/modal.html`, `app/static/css/app.css` | 5 | 10 | 0 | красный |
| `10-51#0` | plan-file-scope | `app/templates/` | 5 | 9 | 0 | красный |

«Путей в них» — сумма путей по коммитам плана, с повторами. «Синтетический коммит» — копия живого журнала плюс `feat(<область>): x` на первом запрещённом пути записи (для каталога — `<каталог>x.py`). У всех 14 назван ровно добавленный коммит.

## Замер журнала правилом

- `git rev-parse --is-shallow-repository` → `false`. Журнал — 2983 коммита (2982 до первого коммита плана), чтение 0,15 с.
- Отбор по области темы воспроизвёл замер планирования: 10-36 — 6, 10-37 — 8, 10-38 — 6, 10-39 — 6, 10-40 — 2, 10-44 — 7, 10-48 — 4, 10-49 — 4, 10-50 — 5, 10-51 — 5. У 10-36 среди них есть `fix(10-36):`, поэтому тип в шаблоне — любой `[a-z]+`, а не перечень.
- Настоящий мелкий клон (`git clone --depth 1`, scratchpad, удалён): ответ `true`, `_read_journal` отказал «мелкий клон: …» до запроса журнала.
- Зубы правила согласия (scratchpad, дерево не менялось). Снятая запись `10-49#4` при записанном реестре даёт красное «строка реестра … называет `test_every_declared_history_fact_holds_over_its_plans_commits`, а записи нет». Лишний ключ `10-49-PLAN.md#9` даёт красное «тождество … вне переписи».

Частичными не записана ни одна строка.

## Task Commits

1. **Задача 1: инструмент исторических фактов** — `18cbebd7` (test, RED), `734244e1` (feat, GREEN).
2. **Задача 2: четырнадцать фактов** — `cc3bc039` (feat): записи и два правила; `f01d0a4d` (chore): 14 строк реестра.

**Plan metadata:** коммит сводки `docs(15-30)`, следом коммит учёта STATE/ROADMAP.

## TDD

План имеет `type: execute`, задача 1 — `tdd="true"`.

- **RED** `18cbebd7`: модуль с пятью контролями и помощниками без тел (возвращают пустое). Каждый контроль прогнан отдельно: `uv run pytest -q -p no:randomly --junit-xml=… <модуль>::<контроль>`. Все пять дали `FAILED …::<контроль>`, `1 failed, 1 warning`, `exit=1`. Причинные литералы: `assert () == (Commit(…` (разбор), «коммиты плана 10-44 отобраны не по области темы» (отбор), `assert [] == [PathOffence(…` (пути), `DID NOT RAISE <class '…HistoryRefusal'>` (антивакуум, мелкий клон). Запись `{command, exitCode, targetTest, output}` собрана из junit-xml в форме node:test TAP одноразовым `junit2red.py` (scratchpad, не в дереве). `check tdd-red-evidence` → `RED_EVIDENCE_OK / target_test_failed` ×5.
- **GREEN** `734244e1`: тела помощников, `5 passed`.
- REFACTOR не было. Коммит `feat` задачи 2 (`cc3bc039`) расширяет модуль правилами над живым журналом. RED у них — синтетический коммит на запрещённом пути (замер выше), а не отдельный коммит `test`: правило над историей красно на живом дереве быть не может, история чиста.

## Files Created/Modified

- `tests/test_planning/test_executed_plans_kept_their_scope.py` — новый модуль (470 строк): 5 контролей, 2 правила (одно на 14 случаев), 1 контроль направления.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — 14 строк, записаны только через `--record` (дифф 14/14).

## Decisions Made

См. `key-decisions`. Главное — прочтение «ПРОДУКТ» шире таблицы планирования. На вердикт замера оно не влияет: коммиты четырёх затронутых планов касались только `.planning/…` и (у 10-48) `tests/`.

## Deviations from Plan

None - plan executed exactly as written. Расширение перечня «ПРОДУКТ» план предусмотрел сам: «если полная формулировка называет больше — берётся полная».

## Issues Encountered

- `ruff` в окружении не установлен (`uv run ruff` → «Failed to spawn»), модуль линтером не прогнан. Сборка и суита каталога зелены.
- Граница 2 — существенное ограничение, а не формальность. Правка запрещённого пути коммитом оркестратора без области плана (`fix: …`, `docs(phase-10): …`) этим правилом не ловится. Она названа в докстринге и здесь.

## Verification

- `uv run pytest tests/test_planning/test_executed_plans_kept_their_scope.py -q -p no:randomly` → `21 passed` (14 случаев несущего правила).
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `161 passed` (было 140, +21). С `tests/test_templates/test_htmx_inventory.py` → `191 passed`.
- `grep -c 'is-shallow-repository' …` → 4; `grep -c 'pytest.skip' …` → 0. Гейт независимости от вердикта → `3 passed`.
- `--list --phase 10 | grep -E '<14 тождеств>' | grep -c 'disposition=enforced'` → `14`, частичных 0, сумма 14.
- `git diff --stat 5d12fd6b..HEAD -- .planning/phases/10-rychag-components-modal-html/` → пусто. Ни один `*-PLAN.md` не правился.
- `--check` → «реестр: 741 строк, биекция с переписью — согласие».
- Нового `import yaml` нет (модуль ввозит прибор, а не PyYAML). `YAML_DIRECT_IMPORTERS` не менялся.
- `graphify update .` выполнен.
- **Подмена полного прогона названа:** полную суиту (`just test`) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют `tests/test_planning/` целиком и `tests/test_templates/test_htmx_inventory.py`. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None — заглушек в модуле нет. Тела помощников RED-коммита заменены в GREEN-коммите.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 15-31 закрывает остаток `declared-rule-absent` (12 строк). Образец этого плана подходит к любому запрету с предметом «этим планом не правится»: запись в `HISTORY_FACTS` плюс `--record`.
- Правило читает историю от `HEAD`. Новые коммиты с областью `(10-NN)` оно увидит, коммиты `15-30` и учёта — нет, поэтому после учётного коммита оно остаётся зелёным.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился. Плану 15-32 ничего не передано: ни одна формулировка группы не утверждает замещённого состояния.

## Self-Check: PASSED

- FOUND: tests/test_planning/test_executed_plans_kept_their_scope.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: 18cbebd7, 734244e1, cc3bc039, f01d0a4d (ledger `5d12fd6b..HEAD` = 4 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-26*

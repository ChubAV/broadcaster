---
phase: 18-ruchnaya-pravka-nomera
plan: 06
subsystem: accounts
tags: [dataclass, kw_only, tdd, wr-03, sync-status]

requires:
  - phase: 18-ruchnaya-pravka-nomera
    provides: "18-01 — признак `phone_is_manual` и решение «без умолчания» у `AccountRow`; 18-03 — пометка «указан вручную» во фрагменте опроса"
provides:
  - "`SyncStatusView` — датакласс `kw_only=True` без умолчаний: забытое поле падает `TypeError`"
  - "`get_sync_status_view` собирает ответ одним конструктором"
affects: [18-05, 18-07]

plan_head_before: 889019ccfc2d072f8731fb63506b5aea8927c28f
plan_head_after: d3834d3be44a36b823f623e66d8393d738741884
actuals:
  tokens: 1500
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Обязательные ключевые-только поля DTO вместо умолчаний: потерянный признак падает громко (как `AccountRow`)"

key-files:
  created: []
  modified:
    - app/application/accounts/dto.py
    - app/application/accounts/use_cases.py
    - tests/test_pages/test_account_label_accounts.py

key-decisions:
  - "`kw_only=True`, а не перестановка полей: умолчание `False` у `phone_is_manual` было следствием порядка полей, а не решением (WR-03); умолчания сняты у всех трёх полей после `status`"
  - "Абзац докстринга об умолчании не стёрт, а помечен «СНЯТО планом 18-06» (идиома D-30/D-32)"
  - "Тест четырёх статусов (18-01) не переписан: остаётся проверкой значений по статусам, включая `connecting` → `other`"

requirements-completed: [PHONE-08]

coverage:
  - id: D1
    description: "У SyncStatusView нет ни одного умолчания; конструктор без phone_is_manual падает TypeError"
    requirement: "PHONE-08"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_label_accounts.py#test_sync_status_view_has_no_defaults"
        status: pass
    human_judgment: false
  - id: D2
    description: "get_sync_status_view собирает ответ одним конструктором; карточки active/sync_failed/syncing/other ведут себя прежде"
    requirement: "PHONE-08"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_label_accounts.py#test_sync_status_view_carries_the_manual_flag_in_all_four_constructors"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py tests/test_pages/test_account_label_sweep.py tests/test_routes/test_wa_sync_status.py"
        status: pass
    human_judgment: false

duration: 37min
completed: 2026-11-22
status: complete
---

# Phase 18 Plan 06: SyncStatusView без умолчаний Summary

**`SyncStatusView` — `kw_only` датакласс без единого умолчания (забытый `phone_is_manual` теперь `TypeError`), а `get_sync_status_view` собирает ответ одним конструктором вместо четырёх одинаковых.**

## Performance

- **Duration:** 37 min
- **Started:** 2026-11-22T06:10:00Z
- **Completed:** 2026-11-22T06:48:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Собственная защита фазы от тихой потери пометки «указан вручную» (D-10) теперь держится на типе, а не на одном тесте, знающем только четыре статуса (WR-03, угроза T-18-22).
- `get_sync_status_view`: локальная `status` (`active` / `sync_failed` / `syncing` как есть, прочее — `other`) и один `return SyncStatusView(...)`; запросов не прибавилось.

## TDD Cycle

- **RED** (`485f4c10`): `test_sync_status_view_has_no_defaults` — ни у одного поля `dataclasses.fields(SyncStatusView)` нет `default`/`default_factory`, вызов без `phone_is_manual` поднимает `TypeError`. Упал на утверждении `у поля SyncStatusView есть умолчание: messenger_type`; 23 остальных теста модуля зелены. Улика: `gsd check tdd-red-evidence` вернула `RED_EVIDENCE_OK` (`target_test_failed`, формат `junit`, 24 теста / 23 прошли / 1 упал); запись и XML — в `.gsd/tdd-evidence/18-06/` (самоигнорируемый каталог, вместе с worktree не сохраняется). Семантическая оценка: целевой тест выполнился и упал именно на запланированном утверждении, без ошибок импорта/фикстур.
- **GREEN** (`d769f90f`): `@dataclass(slots=True, kw_only=True)`, поля `messenger_type`, `phone`, `phone_is_manual` без умолчаний; абзац докстринга помечен «СНЯТО планом 18-06 (WR-03)». Тест модуля — 24 passed; соседние модули (`test_account_phone_links`, `test_account_label_sweep`, `test_wa_sync_status`, `tests/test_application`) — 1128 passed.
- **REFACTOR** (`d3834d3b`): сведение четырёх конструкторов в один; 1714 passed (модули плана + `tests/test_templates` + `test_responsive_markup`).

## Task Commits

1. **Task 1: сквозной срез — у `SyncStatusView` нет умолчаний** — `485f4c10` (test, RED), `d769f90f` (feat, GREEN)
2. **Task 2: один конструктор в `get_sync_status_view`** — `d3834d3b` (refactor)

**Plan metadata:** следующий коммит `docs(18-06): complete …` (SUMMARY.md)

## Files Created/Modified

- `app/application/accounts/dto.py` — `SyncStatusView` без умолчаний, `kw_only=True`, докстринг с пометкой о снятии умолчания.
- `app/application/accounts/use_cases.py` — один конструктор `SyncStatusView` в `get_sync_status_view`.
- `tests/test_pages/test_account_label_accounts.py` — тест `test_sync_status_view_has_no_defaults` (+ импорты `dataclasses`, `SyncStatusView`).

## Decisions Made

См. `key-decisions` во frontmatter: `kw_only`, помета «СНЯТО» вместо стирания, тест четырёх статусов не тронут.

## Deviations from Plan

None - plan executed exactly as written.

Замечания о ходе, не отклонения от плана:

- Два прогона `<verify>` задачи 2 объединены в один вызов pytest с тем же набором модулей (1714 passed).
- Леджер `gsd-plan-head-before-18-06` (протокол 0c) не удалось записать в git-каталог worktree (песочница запрещает запись вне дерева); база плана взята из проверки спавна (`889019ccfc2d072f8731fb63506b5aea8927c28f`, она же `plan_head_before`), копия — в scratchpad. `commits: 3` измерено `git log 889019cc..HEAD` до коммита SUMMARY.
- Сводка `plan_head_after` — HEAD перед коммитом SUMMARY (`d3834d3b`).

## Verification

- `grep -c "kw_only=True" dto.py` = 1; `grep -c "phone_is_manual: bool = False" dto.py` = 0.
- `grep -c "return SyncStatusView(" use_cases.py` = 1; `grep -c "phone_is_manual=account.phone_is_manual" use_cases.py` = 1.
- Конструкторов `SyncStatusView` вне `get_sync_status_view` в `app/` и `tests/` нет (`grep -rn SyncStatusView app tests`); `TypeError` нигде не появился.
- Сквозные гейты исполнителя: `test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `tests/test_services/test_account_label.py`, `tests/test_application/test_account_label_rows.py`, `tests/test_pages/test_account_label_*.py`, гейты номера Фазы 16 — 1574 passed; `compileall -q app main.py tests` — rc 0.

## Known Stubs

None.

## Threat Flags

None - новых поверхностей нет; T-18-22 смягчён типом (`kw_only`, без умолчаний) и одним конструктором.

## Issues Encountered

Общая блокировка pytest с двумя параллельными исполнителями удлиняла прогоны (ожидание очереди). `graphify update .` не запускался в worktree (граф-артефакты `graphify-out/` не отслеживаются; обновление остаётся за оркестратором при необходимости).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Волна 4 (план 18-06) закончена; PHONE-08 остаётся `Pending` до вердикта фазы (records-гейт). `tests/test_planning` прогнан после коммита метаданных (см. возврат).

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-22*

## Self-Check: PASSED

- FOUND: app/application/accounts/dto.py, app/application/accounts/use_cases.py, tests/test_pages/test_account_label_accounts.py
- FOUND commits: 485f4c10, d769f90f, d3834d3b
- TDD gates: test(18-06) -> feat(18-06) -> refactor(18-06) in order

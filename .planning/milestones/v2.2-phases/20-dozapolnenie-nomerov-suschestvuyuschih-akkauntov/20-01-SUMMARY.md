---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 01
subsystem: scripts
tags: [backfill, phone, sqlalchemy, pytest, tdd]

requires:
  - phase: 16
    provides: "fill_reported_phone / PhoneWrite (единый писатель), normalize_reported, mask_phone, гейты номера"
provides:
  - "scripts/backfill_account_phones.py: Outcome, KINDS, WRITE_OUTCOMES, RunOptions, AccountRow, SourceReply, AccountSource, RunSummary, select_candidates, run"
  - "Протокол AccountSource.poll(row, options) -> SourceReply для планов 20-02..20-05"
  - "Основа режима просмотра: писатель не вызывается, строка «было бы заполнено» с маской"
  - "tests/test_scripts/test_backfill_account_phones.py: файловая база, RecordingSource, _count_writer, _snapshot"
affects: [20-02, 20-03, 20-04, 20-05, 20-06, 20-07]

plan_head_before: 8b5e37076e297f10209a0b88cd3f496f6a6dbc0f
plan_head_after: 48a6f66e26029f37aa54534acee4dc803f96bcfd

actuals:
  tokens: 5900
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Ядро с внедряемыми источниками (Protocol), исключение по одному аккаунту = его исход"
    - "Сессия и коммит на аккаунт; писатель не коммитит"
    - "Итог обходом перечисления Outcome; печать только маской прямо внутри print"

key-files:
  created:
    - scripts/backfill_account_phones.py
    - tests/test_scripts/test_backfill_account_phones.py
  modified: []

key-decisions:
  - "Исход FILLED принадлежит только ядру: источник, вернувший его, получает исход «сбой по аккаунту (InvalidSourceReply)», а не падение mask_phone(None)"
  - "Ответ, прошедший писатель или просмотр, сохраняет reported: строка «заполнено» нормализует его для маски"
  - "from sqlalchemy import exists не ввозится: он нужен предсказанию просмотра плана 20-07, ввоз добавит он"

requirements-completed: []
requirements-addressed: [PHONE-17, PHONE-18]

coverage:
  - id: D1
    description: "Номер от источника записывается только единым писателем, коммитится сессией аккаунта и печатается маской"
    requirement: "PHONE-17"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_tracer_a_reported_number_is_written_committed_and_printed_masked"
        status: pass
    human_judgment: false
  - id: D2
    description: "Выборка: без номера и не ручные при любом статусе, по id; фильтры kinds/account_id/limit"
    requirement: "PHONE-17"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_selection_skips_manual_and_filled_and_ignores_status"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_selection_filters_by_kind_account_and_limit"
        status: pass
    human_judgment: false
  - id: D3
    description: "Статус, credentials, type, user_id не меняются ни при одном исходе; повторный прогон ничего не меняет"
    requirement: "PHONE-17"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_status_unchanged_by_any_outcome"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_idempotent_second_run_changes_nothing"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ручной номер во время прогона не затирается; удалённый аккаунт назван отдельным исходом"
    requirement: "PHONE-17"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_manual_entered_during_the_run_is_kept"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_account_deleted_during_the_run_is_counted_gone"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сбой одного аккаунта (источник, писатель) не обрывает и не откатывает прогон; отмена не глотается"
    requirement: "PHONE-17"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_one_failing_account_does_not_stop_or_undo_the_run"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_one_failing_account_cancellation_is_not_swallowed_and_keeps_written"
        status: pass
    human_judgment: false
  - id: D6
    description: "Просмотр не вызывает писателя и не меняет строк (D-06), доказано считающей обёрткой с положительным контролем"
    requirement: "PHONE-18"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_dry_run_never_calls_the_writer"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 01: Ядро дозаполнения номеров Summary

**Ядро разовой команды дозаполнения: выборка колонками (без номера, не ручные, любой статус), опрос внедряемого `AccountSource` по одному аккаунту, запись только `fill_reported_phone` с коммитом на аккаунт, просмотр без вызова писателя, строка на аккаунт с маской и итог обходом `Outcome`.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-11-23T13:23:16Z
- **Completed:** 2026-11-23T13:34:30Z
- **Tasks:** 2 (tracer + закрепляющие правила)
- **Files modified:** 2 (оба новые)

## Accomplishments

- `scripts/backfill_account_phones.py`: `Outcome` (восемь исходов), `KINDS`, `WRITE_OUTCOMES`, `RunOptions`, `AccountRow`, `SourceReply`, `AccountSource`, `RunSummary`, `select_candidates`, `run`. Единственный путь записи номера — `fill_reported_phone(session, row.id, reply.reported)` в сессии аккаунта с немедленным `commit`; при исключении — `rollback` и исход «сбой по аккаунту» с именем класса.
- Просмотр (`dry_run`) с первого коммита не вызывает писателя: значение нормализуется `normalize_reported`, строка — `было бы заполнено +7 *** ***-**-67`, заголовок итога — `Итог просмотра (ничего не записано):`.
- Тесты (12) на файловой SQLite: трасер, выборка, фильтры, неизменность статуса, идемпотентность, ручной номер во время прогона (вторая сессия), удалённый аккаунт, сбой источника / писателя, отмена, правило «просмотр не вызывает писателя» с обёрткой `_count_writer` и положительным контролем.
- Гейты номера зелены без новых записей в списках изъятий (`git diff` по файлам гейтов пуст).

## Task Commits

1. **Task 1 (tracer): ядро** — RED `3b306e77` (`test(20-01)`), GREEN `d547d73b` (`feat(20-01)`)
2. **Task 2: критерии 1-2 и D-06** — `48a6f66e` (`test(20-01)`; все правила зелены на коде задачи 1, правки ядра не потребовались — закрепляющие правила с отрицательными контролями)

**Plan metadata:** коммит `docs(20-01)` с этой сводкой (следует за `plan_head_after`).

## TDD

### RED (задача 1)

Тест `test_tracer_a_reported_number_is_written_committed_and_printed_masked` + объявительный каркас модуля (`run` возвращал пустой `RunSummary`). Команда: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly --junitxml=.gsd/tdd-evidence/20-01/red-1.xml`, код выхода 1.

Три совпадения вывода: `FAILED tests/test_scripts/test_backfill_account_phones.py::test_tracer_a_reported_number_is_written_committed_and_printed_masked`; итог `1 failed, 1 warning`; причинный литерал `AssertionError: номер не записан писателем Фазы 16` (`assert (None, False) == ('+79991234567', False)`).

`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `reason: target_test_failed`, `format: junit`, `matched_test` = целевой тест.
`semanticAssessment`: целевой тест собран и исполнен, упал на первом запланированном утверждении (номер не записан писателем), потому что `run` — заглушка; ошибок сбора, ввоза и фикстур нет.

### GREEN

`select_candidates` и `run` наполнены (выборка колонками, опрос по одному, запись писателем с коммитом на аккаунт, просмотр без писателя, печать маской, итог). Трасер и три `<verify>` задачи 1 зелены (`⚡ Tracer verified end-to-end — expanding`).

### REFACTOR

Не потребовался.

### Задача 2

Все правила зелены сразу (тип `auto`, закрепляющие). RED-улика не требовалась: ни одно правило не было красным на коде задачи 1.

## Отрицательные контроли (мутация скрипта, прогон `--tb=line`, правка снята и не коммитилась)

1. Условие `status == "active"` в выборке → `test_selection_skips_manual_and_filled_and_ignores_status`: `assert [1] == [1, 2, 3, 4]`.
2. Убрано условие `phone_is_manual` → `test_selection_skips_manual_and_filled_and_ignores_status`: `assert [1, 2, 3, 4, 7] == [1, 2, 3, 4]` (см. «Отклонения», п. 1: первая версия правила контроль не убивала).
3. Один общий коммит после цикла вместо коммита на аккаунт → красны `test_one_failing_account_in_the_writer_does_not_stop_or_undo_the_run` и `test_one_failing_account_cancellation_is_not_swallowed_and_keeps_written`: `assert (None, False) == ('+79991234567', False)`.
4. `PhoneWrite.MISSING` → «ручной / уже заполнен» → `test_account_deleted_during_the_run_is_counted_gone`: `assert 0 == 1`.
5. Исключение источника не ловится по аккаунту → красны `test_status_unchanged_by_any_outcome` (`RuntimeError: boom`) и `test_one_failing_account_does_not_stop_or_undo_the_run` (`RuntimeError: secret detail ...`).
6. В ветке просмотра вызван `fill_reported_phone` в сессии аккаунта с откатом вместо коммита → `FAILED tests/test_scripts/test_backfill_account_phones.py::test_dry_run_never_calls_the_writer`: `AssertionError: просмотр вызвал писатель Фазы 16` (снимок такую запись не видит, журнал обёртки видит).

## Files Created/Modified

- `scripts/backfill_account_phones.py` — ядро скрипта дозаполнения (единственный файл кода фазы)
- `tests/test_scripts/test_backfill_account_phones.py` — тесты ядра; помощники `_count_writer`, `_snapshot`, `RecordingSource` для планов 20-02…20-07

## Decisions Made

- Исход `FILLED` принадлежит только ядру. Источник, вернувший его, получает `FAILED (InvalidSourceReply)`: иначе `mask_phone(None)` обрывал бы прогон. Покрыто `test_a_source_claiming_the_core_outcome_filled_is_a_failed_account`.
- `from sqlalchemy import exists` не ввозится (в плане он назван, но ничего не использует до предсказания просмотра плана 20-07; тот добавит ввоз сам).
- Устаревание, названное планом (решение владельца O-3 (а), файл не правится): поручение `16-CONTEXT.md` D-01 о переносе «номера из формы» MAX из `credentials` и комментарий `app/models/messenger_account.py:81-82` про такой перенос **устарели** — перенос не делается.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Правило выборки не убивало отрицательный контроль (2)**
- **Found during:** Задача 2, отрицательный контроль (2)
- **Issue:** при удалённом условии `phone_is_manual` правило `test_selection_skips_manual_and_filled_and_ignores_status` оставалось зелёным: у ручного аккаунта номер не пуст, а состояние «признак без номера» таблица запрещает (`ck_messenger_accounts_manual_requires_phone`). Условие выборки на признак было не защищено тестом.
- **Fix:** в правило добавлена строка «признак без номера», построенная в обход CHECK через `PRAGMA ignore_check_constraints` (тест, сырой SQL допустим, гейты тесты не судят). Контроль (2) теперь красный.
- **Files modified:** `tests/test_scripts/test_backfill_account_phones.py`
- **Verification:** `-k selection_skips_manual` зелёное на коде, красное на мутации
- **Committed in:** `48a6f66e`

**2. [Rule 2 - Missing critical] Защита от ответа источника с исходом «заполнено»**
- **Found during:** Задача 1, GREEN
- **Issue:** источник, вернувший `Outcome.FILLED` без значения, довёл бы строку «заполнено» до `mask_phone(None)` и оборвал прогон на одном аккаунте — нарушение D-14.
- **Fix:** `_poll` превращает такой ответ в `FAILED` с заметкой `InvalidSourceReply`; добавлен тест.
- **Files modified:** `scripts/backfill_account_phones.py`, `tests/test_scripts/test_backfill_account_phones.py`
- **Committed in:** `d547d73b`, `48a6f66e`

**3. [Rule 1 - Bug] Потеря значения при передаче между ветками**
- **Found during:** Задача 1, GREEN (до коммита)
- **Issue:** `_write` и `_preview` возвращали ответ без `reported`, строка «заполнено» нормализовала `None`.
- **Fix:** `reported=reply.reported` сохраняется в возвращаемом ответе.
- **Committed in:** `d547d73b`

---

**Total deviations:** 3 auto-fixed (2 bug, 1 missing critical)
**Impact on plan:** все правки внутри `files_modified`, гейты вне плана не менялись; сверх плана — один дополнительный тест (правило 9).

## Issues Encountered

None.

## Known Stubs

None. (Источники `WorkerStatusSource`, `TelegramSource` и оболочка CLI — планы 20-02…20-06 по плану.)

## Threat Flags

None. Новых сетевых точек, путей авторизации и схем нет; скрипт читает и пишет базу только через единого писателя.

## User Setup Required

None - no external service configuration required.

## Gates

- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py` — 1161 passed; списки изъятий не тронуты.
- `tests/test_scripts/ tests/test_pages/test_htmx_post_pairs.py tests/test_services/test_log_masking.py tests/test_application/test_declared_invariants.py tests/test_application/test_phone_writer_runtime_guard.py` — 314 passed.
- `uv run python -m compileall -q scripts tests/test_scripts` — код 0.
- `graphify update .` не запускался (по поручению оркестратора — после слияния на основной копии); `tests/test_planning` и `just test` — гейты оркестратора.

## TDD Gate Compliance

RED `3b306e77` (`test(20-01)`) → GREEN `d547d73b` (`feat(20-01)`) в порядке предков; REFACTOR не потребовался.

## Next Phase Readiness

Протокол `AccountSource` и ядро готовы: планы 20-02…20-05 подключают источники без правки ядра; 20-07 переиспользует `_count_writer` и добавляет предсказание просмотра. Записи PHONE-17…PHONE-20 остаются `Pending` до проверки фазы.

## Self-Check: PASSED

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

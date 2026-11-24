---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 03
subsystem: scripts
tags: [backfill, phone, whatsapp, max, docker, wake, pytest, tdd]

requires:
  - phase: 20-01
    provides: "AccountSource / SourceReply / Outcome / RunOptions / run"
  - phase: 20-02
    provides: "WorkerStatusSource, classify_status, CONTAINER_MANAGERS, STATUS_TIMEOUT, страж настоящего Docker, помощники теста"
provides:
  - "scripts/backfill_account_phones.py: RunOptions.wake, подъём остановленного воркера WA/MAX в WorkerStatusSource, queue_key, окна ожидания, остановка поднятого в finally, опрос MAX до connected"
  - "Тесты: трасер подъёма WA, матрица условий O-1 (WA и MAX), D-16, просмотр, строгая очерёдность, граница 45 попыток MAX, окна 90/30, остановка при отказе и отмене"
affects: [20-06, 20-07]

plan_head_before: 9a4e3659c8812de16ded617cbd860f34b521d883
plan_head_after: f15c98caaf4fb5528d833507c5b38d1f03705e44

actuals:
  tokens: 5350
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - "Подъём воркера — try/finally: `started` ставится только после ответа менеджера, остановка только при всё ещё пустой очереди; отказ остановки — заметка, а не потеря ответа"
    - "Синхронные функции менеджеров Docker и чтение длины очереди Redis — через asyncio.to_thread; опрос MAX считает попытки, а не часы"
    - "Двойники подъёма с общим журналом events: ('start', id), ('wait', id, timeout), ('ask', id), ('stop', id); пауза — асинхронный двойник с журналом"

key-files:
  created: []
  modified:
    - scripts/backfill_account_phones.py
    - tests/test_scripts/test_backfill_account_phones.py

key-decisions:
  - "Заметка ответа источника доходит до строки аккаунта и при записи, и при просмотре (`_write` / `_preview` передают `note`): оператор видит, что поднятый контейнер оставлен, даже когда номер записан"
  - "Отказ `stop_container` не прячет ответ воркера и не заменяет исключение прогона: заметка «контейнер оставлен: остановка не удалась (<класс>)», текст исключения Docker в вывод не идёт"
  - "Чтение длины очереди записано в двух местах (до подъёма и в `_stop_if_idle`) без общего помощника: критерий приёмки требует два вызова `asyncio.to_thread(self._queue_len` и ловит сброс одного из них"

requirements-completed: []
requirements-addressed: [PHONE-19, PHONE-18]

coverage:
  - id: D1
    description: "По флагу остановленный активный WA-воркер с пустой очередью поднимается, один раз отвечает на /status, номер записывается и маскируется, контейнер гасится"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_tracer_wake_starts_polls_and_stops_a_stopped_worker"
        status: pass
    human_judgment: false
  - id: D2
    description: "Условия O-1 (а) для WA и MAX: статус active, очередь 0/1 до подъёма, очередь не прочитана, уже работающий контейнер, отказ подъёма, воркер не ответил"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_conditions_matrix"
        status: pass
    human_judgment: false
  - id: D3
    description: "D-16: чужой контейнер не гасится; поднятый оставляется при непустой или непрочитанной очереди после опроса; под просмотром ни одного контейнера; строго по одному"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_never_stops_a_container_it_did_not_start"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_leaves_the_container_when_the_queue_filled"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_with_dry_run_in_the_core_starts_nothing"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_one_container_at_a_time"
        status: pass
    human_judgment: false
  - id: D4
    description: "Край boundary PHONE-19 для MAX: connected на 45-й попытке — ровно 45 запросов и 44 паузы по 2.0; без подключения — ровно 45 запросов; «сессия мертва» заканчивает опрос; окна WA 90.0 и MAX 30.0"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_max_polls_until_connected_within_attempts"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_wa_and_max_ready_windows"
        status: pass
    human_judgment: false
  - id: D5
    description: "Поднятый контейнер гасится при отказе транспорта, отказе ожидания и CancelledError (отмена проходит наружу); отказ остановки не прячет номер"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_stops_the_container_on_failure_and_cancellation"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_stop_failure_keeps_the_number_and_names_the_container"
        status: pass
    human_judgment: false
  - id: D6
    description: "Подъём настоящего воркера в боевом Docker (вход связанного устройства; удаление файлов сессии на 401/403/405) — поведение боевого стенда, тестами с двойниками не измеряется"
    requirement: "PHONE-19"
    verification: []
    human_judgment: true
    rationale: "Допущения RESEARCH A3/A4 (код 405 у Baileys, отдаёт ли MAX номер при восстановлении сессии) остаются наблюдением первого боевого прогона владельца после выката; флаг CLI и справка — план 20-06"

duration: 11min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 03: Подъём остановленного воркера WA и MAX по флагу Summary

**`WorkerStatusSource` поднимает остановленный воркер WA/MAX только при `RunOptions.wake` без просмотра, только для статуса `active`, только при прочитанной пустой очереди и только если контейнер не работает; опрашивает его собственным `/status` (MAX — до `connected: true`, не более 45 попыток через 2.0 с) и гасит только поднятый скриптом контейнер в `finally`, и только при всё ещё пустой очереди.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-11-23T15:28:16Z
- **Completed:** 2026-11-23T15:39:24Z (последний код; сводка — после)
- **Tasks:** 3 (tracer + 2 закрепляющих)
- **Files modified:** 2 (оба из 20-01)

## Accomplishments

- `RunOptions.wake: bool = False`; параметры `WorkerStatusSource(..., start, stop, wait_ready, running_now, queue_len, sleep)` — по умолчанию функции `CONTAINER_MANAGERS[kind]`; `queue_len` умолчания не имеет (нет подключения — «очередь не прочитана — не будится»; боевой Redis — план 20-06).
- Ветка подъёма в `poll`: работающий по списку Docker опрашивается как раньше; остановленный без `wake` или под `dry_run` — «воркер не запущен» (D-06); иначе `_wake`: статус не `active` → «статус не active — не будится»; очередь не прочитана → «очередь не прочитана — не будится»; длина не `0` → «в очереди есть задачи — не будится»; `get_container_endpoint` вернул адрес → опрос без подъёма и без остановки (D-16); иначе `_wake_and_ask`.
- `_wake_and_ask`: `start` (MAX без второго аргумента) → `wait_ready` (`WA_READY_TIMEOUT = 90.0` / `MAX_READY_TIMEOUT = 30.0`) → WA один `_ask`, MAX `_ask_until_connected` (`range(MAX_CONNECT_ATTEMPTS)`, `MAX_POLL_INTERVAL`, без паузы после последней попытки, без часов); `finally` — `_stop_if_idle` только при `started`: очередь `0` → `stop`; не `0` → «контейнер оставлен: в очереди появились задачи»; не прочитана → «… проверьте just wa-workers / just max-workers»; отказ `stop` → заметка, не потеря ответа.
- `queue_key(kind, id)` = `f"{kind}:queue:{id}"` (тот же ключ, что в `app/worker/tasks.py`); `NOTE_NOT_CONNECTED` заменил литерал в `classify_status`.
- Ни `asyncio.gather` / `create_task`, ни `time.monotonic` в скрипте; `git diff -- app/ max_worker/ wa_worker/` пуст.

## Task Commits

1. **Task 1 (tracer)** — RED `e661cf3b` (`test(20-03)`), GREEN `11607b2e` (`feat(20-03)`)
2. **Task 2** — RED `a7a76cc6` (`test(20-03)`; красным был `test_wake_leaves_the_container_when_the_queue_filled`), GREEN `78f6507c` (`feat(20-03)`)
3. **Task 3** — RED `d1e24200` (`test(20-03)`; красным был `test_wake_max_polls_until_connected_within_attempts`), GREEN `47484dbe` (`feat(20-03)`)
4. Добавочный тест `f15c98ca` (`test(20-03)`): отказ `stop_container` не прячет номер и не течёт текстом исключения (зелёный на готовом коде; закреплён мутацией).

**Plan metadata:** коммит `docs(20-03)` с этой сводкой (следует за `plan_head_after`).

## TDD

### RED (задача 1, трасер)

`test_tracer_wake_starts_polls_and_stops_a_stopped_worker` + объявления `RunOptions.wake` и параметров источника (принимаются, не используются). Команда: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly --junitxml=.gsd/tdd-evidence/20-03/red-1.xml`, код выхода 1.
Три совпадения: `FAILED …::test_tracer_wake_starts_polls_and_stops_a_stopped_worker`; итог `1 failed, 51 passed`; причинный литерал `поднятый по флагу воркер не дал номер` (2 вхождения в XML).
`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `target_test_failed`, `format: junit`, 52 теста, 1 падение.
`semanticAssessment`: цель собрана и исполнена, упала на утверждении о записи номера (колонки `None`, а не `+79991234567`): каркас игнорирует `wake` и отвечает «воркер не запущен»; ошибок сбора, ввоза и фикстур нет.

### RED (задача 2)

Красными на коде задачи 1 были 4 случая `test_wake_leaves_the_container_when_the_queue_filled` (`tasks-appeared` и `unreadable-after` × WA/MAX). Условия подъёма и остановки уже работали: проверка журнала `events` (остановки нет) прошла, упала проверка заметки — ядро (`_write`, `_preview`) отбрасывало `note` ответа с номером, и строка `#1 wa: заполнено +7 *** ***-**-67` не говорила, что контейнер оставлен. Остальные 77 тестов зелёные.
Целевой случай записи: `…::test_wake_leaves_the_container_when_the_queue_filled[tasks-appeared-wa]`; `RED_EVIDENCE_OK`, `target_test_failed`, 81 тест, 4 падения (`.gsd/tdd-evidence/20-03/red-2.xml`). Первая попытка с именем без параметрического идентификатора дала `INVALID_RED / no_target_test_failure` (имя цели не совпало с параметризованным) — запись пересобрана с полным именем, тест не менялся.
`semanticAssessment`: утверждение о заметке — запланированное; падение по причине, названной в плане («строка содержит «контейнер оставлен» / «just wa-workers»).

### RED (задача 3)

Красными на коде задачи 2 (MAX спрашивает один раз) были все три случая `test_wake_max_polls_until_connected_within_attempts`: `connected-on-45th` — `AssertionError: MAX не дождался подключения`; `never-connected-45-asks` и `dead-session-ends-the-poll` — `число запросов опроса MAX не по границе 45`. Команда та же, `--junitxml=…/red-3.xml`; `RED_EVIDENCE_OK`, цель `…[connected-on-45th]`, 91 тест, 3 падения; литерал «MAX не дождался подключения» — 1 вхождение.
`semanticAssessment`: цель исполнена, упала на запланированном утверждении (номер не записан, один запрос вместо 45); `test_wake_wa_and_max_ready_windows` и `test_wake_stops_the_container_on_failure_and_cancellation` зелёные сразу (окна и `finally` уже были в коде задачи 1) и закреплены отрицательными контролями.

### GREEN / REFACTOR

Задача 1: подъём, `queue_key`, константы — трасер и весь файл (52), три гейта номера (1161) зелёны — `⚡ Tracer verified end-to-end — expanding`. Задача 2: `note` проходит через `_write` и `_preview`. Задача 3: `_ask_until_connected`. REFACTOR не потребовался.

## Отрицательные контроли (мутация скрипта, `--tb=line`, правка снята `git checkout --`; не коммитились)

Задача 2:
1. Снята проверка статуса (`if row.status != "active"` → `if False`) → красны случаи `status-*` матрицы: `AssertionError: журнал подъёма не по условиям O-1`.
2. Очередь сравнивается `> 1` вместо `!= 0` → красен `queue-one`: `журнал подъёма не по условиям O-1` (2 падения: WA и MAX).
3. Снята повторная проверка «уже работает» → красен `already-running-is-asked-not-started` (2 падения): `журнал подъёма не по условиям O-1`.
4. Гасить без проверки очереди после опроса (`if length != 0` → `if False` в `_stop_if_idle`) → красен `tasks-appeared` (2 падения): `контейнер погашен при непустой или непрочитанной очереди`.
5. Убрано условие просмотра (`or options.dry_run`) → красны оба случая `test_wake_with_dry_run_in_the_core_starts_nothing`: `под просмотром поднят, опрошен или погашен контейнер`.

Задача 3:
1. `range(MAX_CONNECT_ATTEMPTS + 1)` → красен `never-connected-45-asks`: `число запросов опроса MAX не по границе 45` (1 падение).
2. Пауза и после последней попытки → красен `never-connected-45-asks`: `assert [2.0, 2.0, …] == [2.0, 2.0, …]` (45 пауз вместо 44).
3. Остановка перенесена из `finally` в ветку успеха → красны 6 случаев `test_wake_stops_the_container_on_failure_and_cancellation` (включая `cancelled`): `поднятый контейнер не погашен`.
4. Окно `MAX_READY_TIMEOUT` для обоих типов (WA получает 30.0) → красен `test_wake_wa_and_max_ready_windows`: журнал WA не равен цепочке с `90.0`.

Добавочное: `except Exception` вокруг `stop` заменён на `except ZeroDivisionError` → красен `test_wake_stop_failure_keeps_the_number_and_names_the_container`: `отказ остановки спрятал номер`.

## Files Created/Modified

- `scripts/backfill_account_phones.py` — `RunOptions.wake`, константы окон, `NOTE_NOT_CONNECTED`, `queue_key`, ветка подъёма (`_wake`, `_wake_and_ask`, `_ask_until_connected`, `_stop_if_idle`), передача `note` в `_write` / `_preview`
- `tests/test_scripts/test_backfill_account_phones.py` — `_wake_doubles`, `_chain`, трасер, матрица, правила D-16, просмотр, очерёдность, граница MAX, окна, отказы и отмена; 41 новый тест (с параметризацией), файл — 92 теста

## Decisions Made

См. `key-decisions`. Отдельно: окно ожидания и порядок шагов — строго по плану; пауза опроса MAX внедряется (`sleep`), настоящих пауз в тестах нет; `CancelledError`, поднятая синхронным двойником внутри `asyncio.to_thread`, проходит наружу из `run` (проверено).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ядро отбрасывало заметку ответа, несущего номер**
- **Found during:** Задача 2 (правило `test_wake_leaves_the_container_when_the_queue_filled`)
- **Issue:** `_write` и `_preview` строили новый `SourceReply` без `note`; поэтому «контейнер оставлен: …» терялось именно в главном случае — когда номер записан, а контейнер оставлен из-за очереди (оператор не узнавал о работающем контейнере).
- **Fix:** `note=reply.note` в трёх возвратах (`_write`, оба в `_preview`). Нотам без номера поведение не менялось; у ответов без заметки строка прежняя.
- **Files modified:** `scripts/backfill_account_phones.py` (файл плана 20-01, в `files_modified` этого плана)
- **Verification:** весь файл (92), три гейта номера, `tests/test_scripts/`
- **Committed in:** `78f6507c`

**2. [Rule 2 - Missing critical] Отказ `stop_container` не должен прятать номер и подменять исключение**
- **Found during:** Задача 1 (проектирование `finally`)
- **Issue:** план не называл исход отказа остановки; необработанное исключение в `finally` заменило бы ответ воркера (номер потерян, аккаунт «сбой») или исходное исключение.
- **Fix:** `_stop_if_idle` ловит `Exception` вокруг `stop`, в заметку — только имя класса (текст исключения Docker в вывод не идёт); тест `test_wake_stop_failure_keeps_the_number_and_names_the_container`.
- **Files modified:** `scripts/backfill_account_phones.py`, `tests/test_scripts/test_backfill_account_phones.py`
- **Committed in:** `11607b2e`, `f15c98ca`

**3. [Plan text vs tree] Каркас RED объявил только поле и параметры**
- Константы окон, `queue_key` и `NOTE_NOT_CONNECTED` добавлены в GREEN (`11607b2e`): трасер RED их не использует. Критерии плана (`grep` = 1, значения окон) проверены после GREEN.

**4. [Plan text vs tree] Отрицательный контроль 4 задачи 3 — окно для обоих типов**
- Вместо «общее окно 30.0 для WA» мутировано `timeout = MAX_READY_TIMEOUT` без условия по типу — это тот же дефект (WA получает 30.0); отказ записан выше.

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical), 2 заметки о границе плана и дереву.
**Impact on plan:** файлы вне `files_modified` не менялись (`git diff -- app/ max_worker/ wa_worker/` пуст); границы O-1 (а) и D-16 не сдвинуты.

## Issues Encountered

Правка теста скриптом по ошибочному якорю (`FAILURES = [` совпало с `TRANSPORT_FAILURES = [`) обрезала файл теста; незакоммиченный блок задачи 3 восстановлен из истории и контекста (`git checkout --` файла теста на закоммиченную версию, блок записан заново), на коммиты это не повлияло.

## Known Stubs

None. Флаг CLI `--wake`, предупреждение в справке, отказ под просмотром и боевое подключение `queue_len` к Redis — план 20-06 по плану; без подключения (`queue_len=None`) подъём отвергается и ничего не поднимается.

## Threat Flags

None. Новых точек доступа нет: поднятие и остановка контейнеров через уже существующие функции менеджеров по явному флагу, чтение длины очереди через внедряемое вызываемое, GET `/status` по адресу менеджера. Тела ответов и тексты исключений в вывод не идут (T-20-10…T-20-13 закрыты тестами выше; остаточный риск 405 на живой сессии принят владельцем в O-1 (а)).

## User Setup Required

None - no external service configuration required.

## Gates

- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py` + `tests/test_scripts/` + `tests/test_wa_container_manager.py` — 1290 passed (до добавочного теста); `tests/test_scripts/test_backfill_account_phones.py` — 92 passed.
- `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_schedule_invariants.py tests/test_services/test_log_masking.py tests/test_application/test_declared_invariants.py tests/test_application/test_phone_writer_runtime_guard.py` — 295 passed.
- `tests/test_max_container_manager.py tests/test_messengers/test_whatsapp.py tests/test_messengers/test_max.py` — 73 passed.
- `uv run python -m compileall -q scripts tests/test_scripts` — код 0.
- grep-гейты: `def queue_key` = 1; `wake: bool = False` = 1; `asyncio.to_thread(self._queue_len` = 2; `asyncio.gather|create_task` = 0; `range(MAX_CONNECT_ATTEMPTS)` = 1; `time.monotonic` = 0; значения окон `(90.0, 30.0, 45, 2.0)`.
- `graphify update .` не запускался (по поручению оркестратора); `just test` не запускался; записи PHONE-17…PHONE-20 остаются `Pending`.

## TDD Gate Compliance

Задача 1: RED `e661cf3b` → GREEN `11607b2e`; задача 2: RED `a7a76cc6` → GREEN `78f6507c`; задача 3: RED `d1e24200` → GREEN `47484dbe`, в порядке предков; `f15c98ca` — тестовый коммит поверх готового кода; REFACTOR не потребовался.

## Next Phase Readiness

План 20-06 подключает `queue_len` к Redis (`llen(queue_key(kind, id))` — ключ уже в `queue_key`), флаг `--wake` и отказ под просмотром; план 20-07 — предсказание просмотра. `WorkerStatusSource` готов принять боевые `queue_len` и менеджеры без правок.

## Self-Check: PASSED

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

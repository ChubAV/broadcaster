---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 02
subsystem: scripts
tags: [backfill, phone, whatsapp, max, docker, httpx, pytest, tdd]

requires:
  - phase: 20-01
    provides: "AccountSource / SourceReply / Outcome / RunOptions / run, помощники теста RecordingSource, _snapshot, _count_writer"
  - phase: 19
    provides: "reported_phone_from_status (разбор поля phone ответа /status)"
provides:
  - "scripts/backfill_account_phones.py: WorkerStatusSource, classify_status, CONTAINER_MANAGERS, STATUS_TIMEOUT"
  - "Источник номера WA / MAX по умолчанию: работающий воркер определяет только Docker, номер — собственный запрос /status"
  - "Тесты: страж настоящего Docker, трасер WA, таблица A6 для WA и MAX, край precision, гарантии «не будить»"
affects: [20-03, 20-06, 20-07]

plan_head_before: 41b16df4609959711627e858feb13e267b0b5753
plan_head_after: e7e77d0b9d5269e497d91d24ec6913be254bd831

actuals:
  tokens: 6800
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Карта работающих контейнеров читается лениво один раз на экземпляр источника; отказ Docker кэшируется и становится исходом каждого аккаунта типа"
    - "Транспорт /status — httpx.AsyncClient на запрос с внедряемым MockTransport; заметки только из имени класса, кода или фразы таблицы"
    - "Страж настоящего Docker — autouse-фикстура с утверждением на разборке"

key-files:
  created: []
  modified:
    - scripts/backfill_account_phones.py
    - tests/test_scripts/test_backfill_account_phones.py

key-decisions:
  - "Аккаунт без работающего контейнера получает «воркер недоступен (воркер не запущен)» без запроса и без подъёма; подъём по флагу — план 20-03"
  - "connected принимается только как настоящее true; phone читается только у подключённой сессии; отсутствие ключа phone — «номера нет (образ воркера без поля phone)»"
  - "Целое phone из JSON пишется точно как +<цифры>; дробное и bool — «номера нет» (делает reported_phone_from_status, закреплено правилом precision)"

requirements-completed: []
requirements-addressed: [PHONE-17, PHONE-18, PHONE-19]

coverage:
  - id: D1
    description: "Работающий воркер WA/MAX опрашивается одним запросом /status по адресу из Docker; номер пишется единым писателем и печатается маской"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_tracer_running_worker_status_fills_the_number"
        status: pass
    human_judgment: false
  - id: D2
    description: "Таблица A6: не-объект, отказ транспорта, не 200, не JSON, connected не true, сессия мертва, нет поля phone, пустой/мусорный phone — исходы по таблице для WA и MAX"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_classify_status_table"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_classify_status_transport_failures_are_unreachable"
        status: pass
    human_judgment: false
  - id: D3
    description: "Край precision: целое phone пишется точно, дробное и bool — «номера нет»"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_classify_status_precision_of_the_phone_field"
        status: pass
    human_judgment: false
  - id: D4
    description: "Путь по умолчанию опрашивает только работающие воркеры; Docker читается один раз на тип; отказ Docker — исход аккаунта"
    requirement: "PHONE-19"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_default_polls_only_running_workers"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_docker_listing_is_read_once_per_kind"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_docker_unavailable_is_a_per_account_outcome"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ни один контейнер не поднимается ни в записи, ни в просмотре; адаптеры и их помощники не вызываются; просмотр не меняет строк"
    requirement: "PHONE-18"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_never_wakes_through_adapters"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_dry_run_starts_no_container"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_running_max_not_connected_is_polled_once"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 02: Источник номера WA и MAX по статусу воркера Summary

**`WorkerStatusSource` для WA и MAX: «работает ли воркер» решает только Docker (контейнер `<тип>-worker-<id>` со статусом `running`), номер берётся собственным запросом `/status` по адресу из имени контейнера с разбором по таблице A6; ни один контейнер не поднимается, адаптеры не используются.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-11-23T14:20:00Z
- **Completed:** 2026-11-23T14:37:10Z
- **Tasks:** 3 (tracer + 2 закрепляющих)
- **Files modified:** 2 (оба из 20-01)

## Accomplishments

- `WorkerStatusSource(kind, *, list_containers=None, transport=None)`: ленивая карта `{account_id: name}` только для статуса `running`, один вызов `list_worker_containers` через `asyncio.to_thread` на экземпляр; адрес `http://<name>:<DEFAULT_PORT>/api/sessions/<id>/status`; отказ списка Docker кэшируется и даёт каждому аккаунту типа `воркер недоступен (Docker недоступен: <класс>)`.
- `classify_status(body)` по таблице A6: не-объект, `connected` не `true` (с `exists: false` — «сессия мертва»), нет ключа `phone` («образ воркера без поля phone»), `reported_phone_from_status(body)`; `_ask` — отказ транспорта, код не 200, тело не JSON — «воркер недоступен» без текста исключения и тела ответа.
- `CONTAINER_MANAGERS = {"wa": wa_container_manager, "max": max_container_manager}`, `STATUS_TIMEOUT = httpx.Timeout(10.0, connect=3.0)`; адаптеры, фабрика, `get_own_phone`, помощники подъёма и ключи Redis `*:endpoint:*` не используются (grep-гейты = 0).
- Тесты: страж `_no_real_docker`, трасер, 32 случая `classify_status` (таблица ×2 типа, precision ×2, отказы транспорта ×2), шесть правил «не будить». Файл теста — 51 тест, зелёный.

## Task Commits

1. **Task 1 (tracer)** — RED `2451632f` (`test(20-02)`), GREEN `d3132040` (`feat(20-02)`)
2. **Task 2** — `5cbfa7dc` (`test(20-02)`; все правила зелены на коде задачи 1, правок источника не потребовалось)
3. **Task 3** — `e7e77d0b` (`test(20-02)`; все правила зелены на коде задачи 1, правок источника не потребовалось)

**Plan metadata:** коммит `docs(20-02)` с этой сводкой (следует за `plan_head_after`).

## TDD

### RED (задача 1)

Тест `test_tracer_running_worker_status_fills_the_number` + каркас `WorkerStatusSource` (`poll` возвращал `UNREACHABLE`) и пустая `classify_status`. Команда: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly --junitxml=.gsd/tdd-evidence/20-02/red-1.xml`, код выхода 1.

Три совпадения: `FAILED tests/test_scripts/test_backfill_account_phones.py::test_tracer_running_worker_status_fills_the_number`; итог `1 failed, 12 passed, 1 warning`; причинный литерал `номер работающего воркера не записан` (3 вхождения в JUnit XML).

`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `reason: target_test_failed`, `format: junit`, `matched_test` = целевой тест (13 тестов, 12 pass, 1 fail).
`semanticAssessment`: целевой тест собран и исполнен, упал на запланированном утверждении (номер работающего воркера не записан), потому что источник — каркас с исходом «воркер недоступен»; ошибок сбора, ввоза и фикстур нет, остальные 12 тестов зелёные.

### GREEN

`WorkerStatusSource` и `classify_status` наполнены; ввозы `httpx`, `reported_phone_from_status`, менеджеры контейнеров. Трасер, весь файл (13 тестов) и три гейта номера (1161) зелены — `⚡ Tracer verified end-to-end — expanding`.

### REFACTOR

Не потребовался.

### Задачи 2 и 3

Правила закрепляющие (тип `auto`): ни одно не было красным на коде задачи 1, поэтому RED-улика не требовалась; каждое правило проверено отрицательным контролем мутацией (мутации не коммитились).

## Отрицательные контроли (мутация скрипта, прогон `--tb=line`, правка снята)

Задача 2:
1. `connected` по истинности (`if not body.get("connected")`) → красны `test_classify_status_table[string-true-is-not-connected-wa|max]`: `AssertionError: исход воркер недоступен не получен: #1 wa: заполнено +7 *** ***-**-67`.
2. `note=str(exc)` вместо имени класса → красны `test_classify_status_transport_failures_are_unreachable[connect-error|read-timeout × wa|max]`: `assert '#1 wa: ворке...-79991234567)' == '#1 wa: ворке...ConnectError)'`.
3. Целое `phone` через `str(float(...))` до разбора → красны `test_classify_status_precision_of_the_phone_field[integer-is-exact-wa|max]`: `assert (None, False) == ('+79991234567', False)`.

Задача 3:
1. Снят кэш карты (`if self._loaded` → `if False`) → `test_docker_listing_is_read_once_per_kind`: `AssertionError: список контейнеров wa прочитан не один раз`.
2. Отказ списка Docker пробрасывается из `poll` → `test_docker_unavailable_is_a_per_account_outcome`: `assert '#1 wa: сбой ...kerException)' == '#1 wa: ворке...kerException)'`.
3. `start_container(row.id)` для остановленного аккаунта → красны `test_never_wakes_through_adapters` и `test_dry_run_starts_no_container` (`Expected 'start_container' to not have been called. Called 2 times.` / `1 times.`), а также `test_default_polls_only_running_workers`.
4. «Работает» — любой статус, кроме `exited` → красны `test_default_polls_only_running_workers` (`опрошен не только работающий воркер`) и `test_never_wakes_through_adapters` (`оба прогона обязаны опросить оба работающих воркера`).

## Files Created/Modified

- `scripts/backfill_account_phones.py` — `WorkerStatusSource`, `classify_status`, `CONTAINER_MANAGERS`, `STATUS_TIMEOUT`
- `tests/test_scripts/test_backfill_account_phones.py` — страж, помощники `_container`, `_listing`, `_status_url`, `_status_transport`, `_poll_one_running`, `_line`, `_patch_wake_paths`; 38 новых тестов (с параметризацией)

## Decisions Made

- Для остановленного воркера заметка — `воркер не запущен`; метка `Docker недоступен: <класс>` — только для отказа списка. Тексты исключений Docker в вывод не идут (проверено секретом внутри `DockerException`).
- Допустимый `kind` проверяется по `CONTAINER_MANAGERS` (то же множество `wa`/`max`, что в плане), чтобы тип и менеджер не расходились.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Критерий `assert_not_called` ≥ 4 не выполнялся цикловой формой**
- **Found during:** Задача 3, проверка критериев приёмки
- **Issue:** две проверки `for mock in mocks: mock.assert_not_called()` давали 2 вхождения вместо ≥ 4 и скрывали, какой из четырёх путей подъёма сработал.
- **Fix:** моки распакованы по именам (`wa_start`, `max_start`, `wa_ensure`, `max_ensure`), каждый проверяется отдельной строкой — 8 вхождений, при отказе видно имя пути.
- **Files modified:** `tests/test_scripts/test_backfill_account_phones.py`
- **Committed in:** `e7e77d0b`

**2. [Plan text vs tree] Каркас RED вне плана объявил только класс и функцию**
- Ввозы, `CONTAINER_MANAGERS` и `STATUS_TIMEOUT` добавлены в GREEN (`d3132040`), а не в RED: каркас RED не использует их, а неиспользуемые ввозы краснили бы линтер без пользы. На RED-улику это не влияет.

---

**Total deviations:** 1 auto-fixed (bug в форме проверки теста), 1 заметка о границе RED/GREEN.
**Impact on plan:** файлы вне `files_modified` не менялись; `git diff -- app/` пуст.

## Issues Encountered

None.

## Known Stubs

None. Подъём по флагу `--wake` (поле `RunOptions.wake`) — план 20-03 по плану; на пути по умолчанию контейнер не поднимается.

## Threat Flags

None. Новых точек доступа нет: чтение списка контейнеров с меткой роли и GET `/status` работающего воркера по уже существующему внутреннему адресу; тело ответа и текст исключений в вывод не идут (T-20-06…T-20-09 закрыты тестами выше).

## User Setup Required

None - no external service configuration required.

## Gates

- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py` — 1161 passed (после задач 1, 2, 3).
- `tests/test_scripts/ tests/test_messengers/test_whatsapp.py tests/test_messengers/test_max.py` — 139 passed.
- `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_schedule_invariants.py tests/test_services/test_log_masking.py tests/test_application/test_declared_invariants.py tests/test_application/test_phone_writer_runtime_guard.py` — 295 passed.
- `uv run python -m compileall -q scripts tests/test_scripts` — код 0.
- grep-гейты: `class WorkerStatusSource` = 1; `reported_phone_from_status(body)` = 1; адаптеры/помощники = 0; `:endpoint:` = 0.
- `graphify update .` не запускался (по поручению оркестратора); `tests/test_planning` и `just test` — гейты оркестратора; записи PHONE-17…PHONE-20 остаются `Pending`.

## TDD Gate Compliance

RED `2451632f` (`test(20-02)`) → GREEN `d3132040` (`feat(20-02)`) в порядке предков; задачи 2 и 3 — только тестовые коммиты `test(20-02)` (правила зелёные на готовом коде, закреплены отрицательными контролями); REFACTOR не потребовался.

## Next Phase Readiness

План 20-03 расширяет `WorkerStatusSource` флагом подъёма (`start`, `stop`, `wait_ready`, …) на ветке «воркер не запущен»; план 20-06 собирает боевые источники через `CONTAINER_MANAGERS`.

## Self-Check: PASSED

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

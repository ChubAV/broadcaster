---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 05
subsystem: scripts
tags: [backfill, phone, telegram, celery, inspect, redis, kombu, busy-probe, pytest, tdd]

requires:
  - phase: 20-04
    provides: "TelegramSource, контракт busy_probe(account_id) -> bool | None (True, None и исключение — «занят»), двойник клиента TelegramWorld"
provides:
  - "scripts/backfill_account_phones.py: TelegramBusyProbe, SEND_TASK, TELEGRAM_QUEUE, ACCOUNT_ARG_INDEX, INSPECT_TIMEOUT"
  - "Тесты: двойники FakeInspector и FakeRedis, трасер «занят», матрица отказа в закрытую (13 случаев), настоящее сообщение kombu через memory://, правила против дрейфа, снимок на аккаунт"
affects: [20-06, 20-07]

plan_head_before: 25127fd3a91776d31258b62f1ecf8f0eaf4d2174
plan_head_after: 047e53b16cc66f456fd55550de5eb5cae5b1a758

actuals:
  tokens: 6000
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Признак «занят» = задача отправки аккаунта в active ∪ reserved снимка Celery inspect либо в списке Redis `telegram`; только чтение (inspect, LRANGE)"
    - "Отказ в закрытую: None на любой неопределённости; требуется ответ каждого воркера очереди `telegram` (состав — active_queues один раз за прогон, active/reserved — на каждый аккаунт)"
    - "Форма сообщения брокера берётся у самого Celery (send_task через memory://), а не пишется руками"

key-files:
  created: []
  modified:
    - scripts/backfill_account_phones.py
    - tests/test_scripts/test_backfill_account_phones.py

key-decisions:
  - "Нечитаемая задача отправки (args не список, короче индекса, не целое; нечитаемое сообщение списка) помечает прогон «неизвестно» и сканирование продолжается: найденное True важнее, итог без True — None, а не False"
  - "timeout хранится открытым атрибутом `probe.timeout` для боевой фабрики инспектора плана 20-06 (`inspect(timeout=...)`); сам признак получает готовый инспектор из фабрики без аргументов"
  - "Тест констант задаёт DATABASE_URL/SECRET_KEY через monkeypatch и сбрасывает кэш get_settings до и после: в чистом дереве без .env ввоз celery_app падал на настройках"

requirements-completed: []
requirements-addressed: [PHONE-20]

coverage:
  - id: D1
    description: "Аккаунт с задачей отправки в active, reserved снимка Celery или в списке telegram признан занятым: TelegramSource не строит клиента, свободный аккаунт заполняется в том же прогоне"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_tracer_busy_probe_sees_an_active_send_and_blocks_the_connection"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_busy_probe_answers_by_task_and_account"
        status: pass
    human_judgment: false
  - id: D2
    description: "Любая неопределённость (нет ответа инспектора, ответил не воркер telegram, отказ фабрики или Redis, нечитаемое сообщение или аргументы) — None, то есть «занят»"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_busy_probe_fails_closed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Настоящее сообщение kombu из очереди telegram читается признаком; константы SEND_TASK, TELEGRAM_QUEUE и ACCOUNT_ARG_INDEX сверены с task_routes и сигнатурой send_telegram_message; состав воркеров читается раз за прогон, снимок — на каждый аккаунт"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_busy_probe_reads_a_real_kombu_message_from_the_telegram_list"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_busy_probe_constants_match_the_send_task"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_busy_probe_reads_worker_queues_once_per_run"
        status: pass
    human_judgment: false
  - id: D4
    description: "Признак на боевых Celery и Redis (воркер celery-worker-telegram отвечает на inspect за INSPECT_TIMEOUT; сообщения в боевом списке telegram той же формы) — поведение боевого брокера, тестами с двойниками не измеряется; боевую фабрику инспектора подставляет план 20-06"
    requirement: "PHONE-20"
    verification: []
    human_judgment: true
    rationale: "Допущения A2 и A8 RESEARCH проверяются первым боевым прогоном владельца из контейнера web; форма сообщения измерена на memory:// и по коду kombu, но не на боевом Redis"

duration: 10min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 05: Признак «TG-аккаунт занят рассылкой» Summary

**`TelegramBusyProbe` отвечает `True`, если задача `send_telegram_message` аккаунта выполняется, предзагружена (Celery `inspect` active ∪ reserved) или ждёт в списке Redis `telegram`, и `None` («занят») при любой неопределённости, включая молчание воркера очереди `telegram`; он только читает (`inspect`, `LRANGE`), а форма сообщения проверена настоящей отправкой Celery через `memory://`.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-11-23T17:45:00Z (приблизительно)
- **Completed:** 2026-11-23T17:56:00Z
- **Tasks:** 2 (трасер + закрепляющие правила)
- **Files modified:** 2 (оба из `files_modified`; `app/worker/` не тронут)

## Accomplishments

- `TelegramBusyProbe(*, inspector_factory, redis_client, timeout=INSPECT_TIMEOUT)`, `async __call__(account_id) -> bool | None` (`asyncio.to_thread` над синхронным `_check`).
- `_check`: состав воркеров очереди `telegram` из `active_queues()` (один раз за прогон, кэш); `active()` и `reserved()` на каждый аккаунт; каждый воркер очереди обязан быть в обоих ответах; задачи `SEND_TASK` сверяются по `args[ACCOUNT_ARG_INDEX]`; затем `lrange("telegram", 0, -1)`, `json.loads(headers["argsrepr"])`. Нечитаемое — «неизвестно» (итог `None`, если `True` не найдено).
- Константы `SEND_TASK`, `TELEGRAM_QUEUE = "telegram"`, `ACCOUNT_ARG_INDEX = 2`, `INSPECT_TIMEOUT = 2.0`; тест сверяет их с `celery.conf.task_routes` и сигнатурой `send_telegram_message.run`.
- Форма сообщения подтверждена и по коду: `kombu/transport/redis.py` `Channel._put` — `client.lpush(self._q_for_pri(queue, pri), dumps(message))`, при приоритете по умолчанию ключ — `telegram`.

## Task Commits

1. **Task 1 (tracer)** — RED `d0f20f9f` (`test(20-05)`), GREEN `d74fccf4` (`feat(20-05)`)
2. **Task 2** — `047e53b1` (`test(20-05)`): пять правил закрепляют уже работающее поведение (см. TDD)

**Plan metadata:** коммит `docs(20-05)` с этой сводкой (следует за `plan_head_after`).

## TDD

### RED (задача 1, трасер)

`test_tracer_busy_probe_sees_an_active_send_and_blocks_the_connection`; `TelegramBusyProbe` объявлен каркасом, возвращающим `False` (так велит `tdd_notes`). Команда: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly --tb=line --junitxml=.gsd/tdd-evidence/20-05/red-1.xml`, код выхода 1.
Три совпадения: `FAILED …::test_tracer_busy_probe_sees_an_active_send_and_blocks_the_connection`; итог `1 failed, 117 passed`; причинный литерал «занятый аккаунт получил подключение» (1 вхождение в XML; значение с строкой `#1 tg_user: заполнено +7 *** ***-**-67` вместо «занят, повторите позже (идёт рассылка)»).
`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `target_test_failed`, `format: junit`, 118 тестов, 1 падение.
`semanticAssessment`: цель собрана и исполнена, упала на утверждении об исходе (каркас ответил «не занят», аккаунт подключён и заполнен); ошибок сбора, ввоза и фикстур нет.

### GREEN / REFACTOR

Задача 1: `TelegramBusyProbe._check` и константы — весь файл (118), три гейта номера (1161) зелёны — `⚡ Tracer verified end-to-end — expanding`. REFACTOR не потребовался.

### Задача 2 — без RED

Пять правил зелёные сразу на коде задачи 1 (так допускает план: «если правило красно…»): они закоммичены как закрепляющие `test(20-05)`, каждое проверено отрицательным контролем (ниже). GREEN-коммита у задачи нет, гейт «RED перед GREEN» к ней не применим.

## Отрицательные контроли (мутация скрипта, `--tb=line`, правка снята `git checkout --`; не коммитились)

1. Снято требование ответа воркера очереди `telegram` (удалена проверка `worker not in active or … reserved`) → красны `test_busy_probe_fails_closed[only-default-answered-active]` и `[only-default-answered-reserved]`: `неопределённость принята за «не занят»`.
2. Внешний `except` отдаёт `False` вместо `None` → красны `test_busy_probe_fails_closed[inspector-factory-raises]` и `[lrange-raises]`.
3. `ACCOUNT_ARG_INDEX = 1` (номер из `args[1]`) → красны правила 2, 3, 4 (`answers_by_task_and_account`, `reads_a_real_kombu_message…`, `constants_match_the_send_task`), трасер и `fails_closed[reserved-send-with-short-args]`.
4. Состав воркеров не кэшируется → красен `test_busy_probe_reads_worker_queues_once_per_run`: `состав воркеров читается не один раз`.
5. Кэшируется и снимок `active` → красен тот же тест: `снимок active берётся не на каждый аккаунт`.

## Files Created/Modified

- `scripts/backfill_account_phones.py` — ввоз `json`; `SEND_TASK`, `TELEGRAM_QUEUE`, `ACCOUNT_ARG_INDEX`, `INSPECT_TIMEOUT`; `_account_of`; `TelegramBusyProbe`
- `tests/test_scripts/test_backfill_account_phones.py` — ввоз `json`; `FakeInspector`, `FakeRedis`, `_inspector`, `_probe`, `_list_item`, `_real_kombu_item`; трасер и пять правил `test_busy_probe_*`; файл — 135 тестов

## Decisions Made

См. `key-decisions`. Отдельно: порядок опроса внутри `_check` — снимки Celery раньше списка Redis, `True` из любого источника возвращается сразу; `timeout` вызывающему плану 20-06 отдан атрибутом, а не нужен признаку внутри.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Тест констант не ввозился в чистом дереве**
- **Found during:** Task 2
- **Issue:** `from app.worker.celery_app import celery` при ввозе вызывает `get_settings()`; в дереве без `.env` (рабочее дерево исполнителя, чистый CI) падало с `ValidationError` на `database_url`/`secret_key`.
- **Fix:** тест через `monkeypatch.setenv` задаёт `DATABASE_URL` и `SECRET_KEY`, кэш `get_settings` сбрасывается до и после ввоза.
- **Files modified:** `tests/test_scripts/test_backfill_account_phones.py`
- **Verification:** `-k busy_probe` — 18 passed; весь файл и `tests/test_scripts/` зелены.
- **Committed in:** `047e53b1`

**2. [Plan text vs tree] Нечитаемое помечает «неизвестно», а не обрывает сканирование**
- План: любой разбор, поднявший исключение, — сразу `None`. Реализация различает «чья задача — неизвестно» (продолжает поиск `True`, итог `None`) и структурные отказы (инспектор, Redis, форма ответов — сразу `None`). Исход тот же («занят»); отличие только в том, что `True` не теряется за нечитаемой строкой.

**3. [Plan text vs tree] Задача 2 без RED**
- Пять правил зелёные на коде задачи 1 (см. «Задача 2 — без RED»).

**4. [Environment] Не удалось применить составные команды**
- Песочница отказывается от составных команд с `git` и heredoc; правки вносились инструментом Edit, улика RED собрана вспомогательным скриптом `.gsd/tdd-evidence/20-05/make_record.py` (каталог игнорируется `.gitignore`, в коммиты не попал).

---

**Total deviations:** 1 auto-fixed (Rule 3), 3 заметки о плане, дереве и среде.
**Impact on plan:** файлы вне `files_modified` не менялись (`git diff -- app/worker/` пуст); границы D-09, D-07 не сдвинуты.

## Issues Encountered

Первый прогон правила констант красный по среде (нет `.env` в рабочем дереве) — устранён, см. отклонение 1. Остаточный риск T-20-21 (окно «проверили — подключились», подключения синхронизации групп TG из `web`) принят планом и кодом не закрывается.

## Known Stubs

None. Боевая фабрика инспектора (`celery.control.inspect(timeout=INSPECT_TIMEOUT)`), клиент Redis и подключение `TelegramBusyProbe` в `build_sources` — план 20-06; без них признак принимает внедряемые `inspector_factory` и `redis_client`.

## Threat Flags

None. Новых сетевых точек нет: признак читает брокер (inspect, LRANGE) через внедряемые объекты; запрещённые команды изменения брокера (`lpop|rpop|brpop|.delete(|.revoke(|.purge(`) в скрипте — 0 вхождений (T-20-18…T-20-20 закрыты тестами выше).

## User Setup Required

None - no external service configuration required.

## Gates

- `tests/test_scripts/test_backfill_account_phones.py` — 135 passed.
- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py` — 1161 passed (после каждой задачи).
- `tests/test_scripts/ tests/test_worker/test_tasks.py` — 204 passed; `tests/test_worker_tasks.py tests/test_worker/ tests/test_services/test_ops_state.py` — 161 passed.
- `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_schedule_invariants.py tests/test_services/test_log_masking.py tests/test_application/test_declared_invariants.py tests/test_application/test_phone_writer_runtime_guard.py` — 295 passed.
- `uv run python -m compileall -q scripts tests/test_scripts` — код 0.
- grep-гейты: `class TelegramBusyProbe` = 1; `^ACCOUNT_ARG_INDEX = 2$` = 1; `lpop|rpop|brpop|.delete(|.revoke(|.purge(` = 0; `def test_busy_probe_` = 5; `memory://` в тестах = 2; `git diff --stat -- app/worker/` пуст.
- `graphify update .` и `just test` не запускались (по поручению оркестратора); записи PHONE-17…PHONE-20 остаются `Pending`; `tests/test_planning` — после коммита сводки (результат — в возврате).

## TDD Gate Compliance

Задача 1: RED `d0f20f9f` → GREEN `d74fccf4`, в порядке предков. Задача 2: только закрепляющий `test(20-05)` `047e53b1` без GREEN (поведение уже реализовано); REFACTOR не потребовался.

## Next Phase Readiness

План 20-06 подставляет боевые `inspector_factory` (`celery.control.inspect(timeout=probe.timeout)`) и `redis_client` (`redis.Redis.from_url(settings.redis_url)`), строит `TelegramBusyProbe` в `build_sources` и запускает только из контейнера `web`. План 20-07 не зависит от этого файла-признака.

## Self-Check: PASSED

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 04
subsystem: scripts
tags: [backfill, phone, telegram, telethon, session, busy-probe, pytest, tdd]

requires:
  - phase: 20-01
    provides: "AccountSource / SourceReply / Outcome / RunOptions / run, помощники теста"
  - phase: 20-03
    provides: "WorkerStatusSource как образец внедрения; заметка ответа источника доходит до строки аккаунта"
provides:
  - "scripts/backfill_account_phones.py: TelegramSource, parse_session, TELEGRAM_PAUSE; карта ошибок Telethon по классам"
  - "Тесты: двойник клиента Telethon со счётчиком одновременных подключений, трасер TG, карта исходов, «занят», строгая очерёдность, просмотр"
affects: [20-05, 20-06, 20-07]

plan_head_before: e8f1ecc5c580134f11298d944b020854dcb64bd3
plan_head_after: b520663163a74b510d12ec3219ad994998a0888a

actuals:
  tokens: 5281
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Порядок до сети в TG: разбор строки сессии, наличие api_id/api_hash, признак «занят», только затем клиент; ни один отказ до сети клиента не строит"
    - "Клиент TG — внедряемая фабрика `(session, api_id, api_hash, *, receive_updates)`; `receive_updates=False`; `connect -> is_user_authorized -> get_me`; `disconnect` в `finally` под собственным try"
    - "Двойник клиента с общим состоянием `TelegramWorld`: журнал событий (имя, номер клиента), счётчики `open_now` / `max_open`, сценарий (authorized, me, raise_on, yield_loop)"

key-files:
  created: []
  modified:
    - scripts/backfill_account_phones.py
    - tests/test_scripts/test_backfill_account_phones.py

key-decisions:
  - "Фабрика клиента вызывается только после трёх отказов до сети (строка сессии, учётные данные API, признак «занят»): `AuthKeyDuplicated` необратим, а пустая строка сессии выпустила бы новый ключ"
  - "Пауза TELEGRAM_PAUSE — после `finally` отключения и только на обычном завершении (ответ получен); исключение, не названное картой, пауз не делает"
  - "Признак «занят» опрашивается ПЕРЕД построением клиента; `True`, `None` и исключение — один исход «занят», отличаются заметкой («идёт рассылка» / «статус рассылки не определён» [: класс])"

requirements-completed: []
requirements-addressed: [PHONE-20, PHONE-17]

coverage:
  - id: D1
    description: "Годная сессия TG отдаёт номер короткому подключению: клиент без обновлений, один connect/is_user_authorized/get_me/disconnect, интерактивный вход не вызывается, номер записан писателем и печатается маской"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_tracer_telegram_number_reaches_the_writer_without_updates"
        status: pass
    human_judgment: false
  - id: D2
    description: "Исходы Telethon по классам (AuthKeyError/UnauthorizedError — сессия мертва; FloodWait/OSError/TimeoutError — недоступен; не авторизована, get_me None, нет номера, прочее) и disconnect ровно один раз на каждом пути"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_outcomes_map"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_disconnect_awaited_on_every_path"
        status: pass
    human_judgment: false
  - id: D3
    description: "Негодная строка сессии и незаданные TELEGRAM_API_ID / TELEGRAM_API_HASH не доходят до сети; в выводе нет строки сессии и текстов исключений"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_bad_session_string_never_connects"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_missing_api_credentials_never_connect"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_output_carries_no_session_or_exception_text"
        status: pass
    human_judgment: false
  - id: D4
    description: "Занятый, неопределённый и упавший признак «занят» — ни одного подключения; опрос строго по одному клиенту; просмотр опрашивает TG и ничего не пишет"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_busy_account_is_never_connected"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_busy_unknown_fails_closed"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_sequential_one_client_at_a_time"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_telegram_dry_run_polls_but_writes_nothing"
        status: pass
    human_judgment: false
  - id: D5
    description: "Короткое подключение боевым TelegramClient к боевой сессии не даёт AUTH_KEY_DUPLICATED (RESEARCH A1) и MAX/Telegram отдают номер на живом стенде — поведение боевого Telegram, тестами с двойниками не измеряется"
    requirement: "PHONE-20"
    verification: []
    human_judgment: true
    rationale: "Допущение A1 — наблюдение первого боевого прогона владельца после выката (план 20-06 даёт боевую фабрику и запуск из контейнера, 20-05 — настоящий признак «занят»); в критерии фазы не входит"

duration: 25min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 04: Источник номера Telegram Summary

**`TelegramSource` берёт номер Telegram коротким последовательным подключением: строка сессии разбирается до сети, занятый или неопределённый аккаунт пропускается в закрытую, клиент строится фабрикой с `receive_updates=False`, `connect → is_user_authorized → get_me`, ошибки Telethon разнесены по классам (AuthKeyError/UnauthorizedError — «сессия мертва», FloodWait/OSError/TimeoutError — «недоступен»), `disconnect` — в `finally`, в выводе только имена классов.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-23T16:16:00Z (приблизительно)
- **Completed:** 2026-11-23T16:41:21Z
- **Tasks:** 3 (tracer + 2 закрепляющих)
- **Files modified:** 2 (оба из 20-01)

## Accomplishments

- `parse_session(credentials)`: не строка, пусто или пробелы → `None`; `StringSession(credentials)` в `try`, любой отказ разбора → `None` (пустая строка выпустила бы новый ключ авторизации — Pitfall 4).
- `TelegramSource(*, api_id, api_hash, busy_probe, client_factory, pause=TELEGRAM_PAUSE)`; `poll`: негодная строка → «сессия мертва» (заметка «строка сессии пуста или не разбирается»); нет `api_id`/`api_hash` → «воркер недоступен»; признак `True` → «занят» («идёт рассылка»), `None` или исключение → «занят» («статус рассылки не определён[: класс]»); затем клиент, `connect → is_user_authorized → get_me`, `reported_phone_of(me)`; `finally` — `disconnect` под собственным `try/except Exception`; пауза при `pause > 0`.
- Карта исключений вокруг блока: `AuthKeyError` (включая `AuthKeyDuplicatedError`) и `UnauthorizedError` → «сессия мертва»; `FloodWaitError`, `OSError`, `TimeoutError` → «воркер недоступен»; прочее ядро делает «сбоем по аккаунту». В заметке только `type(exc).__name__`.
- Интерактивный вход, давний метод проверки соединения адаптера, `TelegramPool` и `client.session` в скрипте не используются; `git diff -- app/` пуст.

## Task Commits

1. **Task 1 (tracer)** — RED `43015914` (`test(20-04)`), GREEN `1bcc0298` (`feat(20-04)`)
2. **Task 2** — RED `a8c5cc84` (`test(20-04)`), GREEN `346d2d05` (`feat(20-04)`)
3. **Task 3** — `b5206631` (`test(20-04)`): четыре правила закрепляют уже работающее поведение (см. ниже, TDD)

**Plan metadata:** коммит `docs(20-04)` с этой сводкой (следует за `plan_head_after`).

## TDD

### RED (задача 1, трасер)

`test_tracer_telegram_number_reaches_the_writer_without_updates`, двойник `FakeTelegramClient` + `TelegramWorld`, каркас `TelegramSource.poll` → `SourceReply(Outcome.UNREACHABLE)`. Команда: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly --tb=line --junitxml=.gsd/tdd-evidence/20-04/red-1.xml`, код выхода 1.
Три совпадения: `FAILED …::test_tracer_telegram_number_reaches_the_writer_without_updates`; итог `1 failed, 92 passed`; причинный литерал «номер Telegram не записан» (1 вхождение в XML).
`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `target_test_failed`, `format: junit`, 93 теста, 1 падение.
`semanticAssessment`: цель собрана и исполнена, упала на утверждении о записи (колонки `(None, False)` вместо `(+79991234567, False)`): каркас отвечает «воркер недоступен»; ошибок сбора, ввоза и фикстур нет.

### RED (задача 2)

Красными на коде задачи 1 были 7 случаев: `test_telegram_outcomes_map[auth-key-duplicated | session-revoked | session-revoked-on-get-me | flood-wait | os-error | timeout]` и `test_telegram_output_carries_no_session_or_exception_text` (в строке «сбой по аккаунту» вместо карты A3: исключение не перехватывалось, ядро делало его сбоем). Остальные 105 зелёные.
Цель записи: `test_telegram_outcomes_map[auth-key-duplicated]`; `RED_EVIDENCE_OK`, `target_test_failed`, 112 тестов, 7 падений (`red-2.xml`); литерал «AuthKeyDuplicated не названа мёртвой сессией» — в сообщении утверждения.
`semanticAssessment`: цель исполнена и упала на запланированном утверждении об исходе (`сбой по аккаунту (AuthKeyDuplicatedError)` вместо `сессия мертва (AuthKeyDuplicatedError)`); не ошибка сбора, не фикстура.

### Задача 3 — без RED

Четыре правила задачи 3 (`test_telegram_busy_account_is_never_connected`, `test_telegram_busy_unknown_fails_closed`, `test_telegram_sequential_one_client_at_a_time`, `test_telegram_dry_run_polls_but_writes_nothing`) зелёные сразу: признак «занят» до клиента, отказ в закрытую и `disconnect` в `finally` уже стоят в GREEN задачи 1 (так требует `<action>` задачи 1), строгую очерёдность и просмотр даёт ядро 20-01. План допускает такой исход («если правило красно…»): они закоммичены как `test(20-04)` закрепляющими, каждое проверено отрицательным контролем (ниже). Гейт «RED перед GREEN» для задачи 3 не применим: GREEN-коммита у задачи нет.

### GREEN / REFACTOR

Задача 1: `parse_session`, `TelegramSource`, константа — трасер и весь файл (93), три гейта номера (1161) зелёны — `⚡ Tracer verified end-to-end — expanding`. Задача 2: три ветки `except` вокруг блока — весь файл (112). REFACTOR не потребовался.

## Отрицательные контроли (мутация скрипта, `--tb=line`, правка снята `git checkout --`; не коммитились)

Задача 2:
1. `FloodWaitError` присоединён к ветке мёртвой сессии → красен `test_telegram_outcomes_map[flood-wait]`: `исход Telethon назван не по карте A3`.
2. Из `parse_session` снята проверка пустой строки → красен `test_telegram_bad_session_string_never_connects[]`: `assert False` (фабрика вызвана на `""`; `"   "`, `"pending"`, `"creds"`, `"1abc"` отсекает сам разбор Telethon).
3. `disconnect` перенесён из `finally` в `else` (только успешный путь) → красны 7 случаев `test_telegram_outcomes_map` (все пути с исключением). Первая попытка (отдельный блок после `try/finally`) оказалась слабой: красной была лишь `other-exception` — пойманные исключения всё равно доходили до отключения; мутация заменена на `else`.
4. `f"{type(exc).__name__}: {exc}"` в заметке «недоступен» → красен `test_telegram_output_carries_no_session_or_exception_text`: `'secret-79991234567' not in …`.

Задача 3:
1. Ветка `if busy is None` отключена → красен `test_telegram_busy_unknown_fails_closed[none]` (клиент построен, номер записан).
2. Клиент строится до опроса признака → красны `test_telegram_busy_account_is_never_connected` («фабрика вызвана для занятого аккаунта») и `…unknown_fails_closed[none]`.
3. В ядре опрос всех аккаунтов сбором корутин (`asyncio.gather`) → красен `test_telegram_sequential_one_client_at_a_time`: `одновременно подключено больше одного клиента Telegram`.
4. Режим просмотра пишет (`_write` вместо `_preview`) → красен `test_telegram_dry_run_polls_but_writes_nothing`: `просмотр изменил строки аккаунтов`.

## Files Created/Modified

- `scripts/backfill_account_phones.py` — `TELEGRAM_PAUSE`, `parse_session`, `TelegramSource`; ввозы `StringSession`, `telethon.errors`, `reported_phone_of`
- `tests/test_scripts/test_backfill_account_phones.py` — `_valid_session_string`, `_seed_tg`, `FakeTelegramClient`, `TelegramWorld`, `_busy_probe`, `_telegram_source`; трасер, карта исходов (10 случаев), строка сессии (5), реквизиты API (2), `disconnect`, вывод без утечек, «занят» (3), очерёдность, просмотр; файл — 117 тестов

## Decisions Made

См. `key-decisions`. Отдельно: `TelegramClient` в скрипт не ввозится — боевую фабрику подставляет план 20-06 (иначе неиспользуемый ввоз); тест двойника принимает фабрику вызываемым `world.factory`, а не классом, потому что общее состояние (счётчик подключений, журнал) должно быть общим для всех клиентов прогона.

## Deviations from Plan

### Auto-fixed Issues

**1. [Plan text vs tree] Двойник клиента — фабрика-метод, а не класс**
- План называет `client_factory=FakeTelegramClient`; общий счётчик `open_now` / `max_open` и журнал живут в `TelegramWorld`, фабрика — `world.factory`. Класс `FakeTelegramClient` существует с той же сигнатурой аргументов (плюс `world` первым).

**2. [Plan text vs tree] Признак «занят» уже в GREEN задачи 1**
- `<action>` задачи 1 требует признак до построения клиента (пункт 3), поэтому задача 3 не имела красного кода: см. «Задача 3 — без RED». Правила закреплены отрицательными контролями.

**3. [Plan text vs tree] Отрицательный контроль 3 задачи 2 переделан**
- Первая форма мутации (отдельный `try` после `finally`) красила один случай из десяти; заменена на `else` — красны все семь путей с исключением. Отказ записан выше.

**4. [Environment] Леджер головы плана не записан**
- Файл `gsd-plan-head-before-20-04` в общем каталоге `.git` песочница запретила писать; `plan_head_before` взят из проверки HEAD на старте (`e8f1ecc5…`, совпадает с базой, названной оркестратором). `commits: 5` измерено `git rev-list --count e8f1ecc5..HEAD`.

---

**Total deviations:** 0 auto-fixed (Rules 1–3), 4 заметки о плане, дереве и среде.
**Impact on plan:** файлы вне `files_modified` не менялись (`git diff -- app/` пуст); границы D-05, D-09, D-12, D-17 не сдвинуты.

## Issues Encountered

Песочница не принимает составные команды (`source`, heredoc рядом с `flock`) — запись улики RED сделана вспомогательным скриптом в `.gsd/tdd-evidence/20-04/` (игнорируется `.gitignore`, в коммиты не попал).

## Known Stubs

None. Боевая фабрика `TelegramClient` и запуск только из боевого контейнера — план 20-06; настоящий признак «занят» (Celery + Redis) — план 20-05; без них источник принимает внедряемые `client_factory` и `busy_probe`.

## Threat Flags

None. Новых точек доступа нет: короткое подключение к Telegram идёт через внедряемую фабрику (в тестах — двойник), строка сессии не пишется назад и не печатается, текст исключений не выводится (T-20-14…T-20-17 закрыты тестами выше).

## User Setup Required

None - no external service configuration required.

## Gates

- `tests/test_scripts/test_backfill_account_phones.py` — 117 passed.
- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py` + `tests/test_scripts/` + `tests/test_pages/test_htmx_post_pairs.py` + `tests/test_pages/test_schedule_invariants.py` + `tests/test_services/test_log_masking.py` + `tests/test_application/test_declared_invariants.py` + `tests/test_application/test_phone_writer_runtime_guard.py` — 1595 passed.
- Telegram-модули: `tests/test_services/test_messenger_factory.py tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py` — 107 passed.
- `uv run python -m compileall -q scripts tests/test_scripts` — код 0.
- grep-гейты: `class TelegramSource` = 1; `receive_updates=False` = 2 (код и строка документации); `reported_phone_of(me)` = 1; `\.start(` = 0; `check_connection` = 0; `TelegramPool` = 0; `AuthKeyError|UnauthorizedError|FloodWaitError` = 3; `max_open` в тестах = 4; `git diff --stat -- app/` пуст.
- `graphify update .` не запускался (по поручению оркестратора); `just test` не запускался; записи PHONE-17…PHONE-20 остаются `Pending`; `tests/test_planning` — после коммита сводки (результат — в возврате).

## TDD Gate Compliance

Задача 1: RED `43015914` → GREEN `1bcc0298`; задача 2: RED `a8c5cc84` → GREEN `346d2d05`, в порядке предков. Задача 3: только закрепляющий `test(20-04)` `b5206631` без GREEN (поведение уже реализовано, см. выше); REFACTOR не потребовался.

## Next Phase Readiness

План 20-05 даёт настоящий `TelegramBusyProbe` (`async def __call__(self, account_id) -> bool | None`), план 20-06 — боевую фабрику `TelegramClient` и подключение `TelegramSource` в `build_sources`; контракт `busy_probe(account_id)` и `client_factory(session, api_id, api_hash, *, receive_updates)` зафиксирован тестами.

## Self-Check: PASSED

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

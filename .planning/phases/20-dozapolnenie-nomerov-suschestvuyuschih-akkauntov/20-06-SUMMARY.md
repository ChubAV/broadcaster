---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
plan: 06
subsystem: scripts
tags: [backfill, phone, cli, argparse, just, docker-compose, telegram, redis, celery, pytest, tdd]

requires:
  - phase: 20-05
    provides: "TelegramBusyProbe с открытым probe.timeout, INSPECT_TIMEOUT"
  - phase: 20-04
    provides: "TelegramSource, контракт client_factory(session, api_id, api_hash, *, receive_updates)"
  - phase: 20-03
    provides: "WorkerStatusSource с queue_len, queue_key, RunOptions.wake"
provides:
  - "scripts/backfill_account_phones.py: build_parser, options_from, TelegramOutsideContainerSource, build_sources, amain, блок __main__, полная шапка"
  - "justfile: рецепты backfill-phones и prod-backfill-phones (запуск без флагов ПИШЕТ; боевой рецепт идёт через exec -T web с --telegram-from-container)"
  - "Тесты: рецепты через just --dry-run и just --list, --help настоящим процессом, коды выхода 0/1/2, отказы аргументов, страж Telegram, сборка боевых источников"
affects: [20-07]

plan_head_before: c41ee1b5b4f889c83e43e38dccd1f444f9bda860
plan_head_after: a2bb57579b34452cff180f53b2782e1a16629710

actuals:
  tokens: 6400
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Запуск без флагов пишет (D-08): сказано в справке, шапке, комментариях рецептов (`WRITES by default`) и первой строке вывода `РЕЖИМ ЗАПИСИ`"
    - "Отказы аргументов (`parser.error`, код 2) — до базы, источников и вывода"
    - "Приложение Celery ввозится внутри build_sources и только на пути Telegram: `--help` и ввоз скрипта не требуют `.env`"
    - "Telegram опрашивается только при явном `--telegram-from-container`, который передаёт один боевой рецепт; без флага — источник-страж без клиента"

key-files:
  created: []
  modified:
    - scripts/backfill_account_phones.py
    - justfile
    - tests/test_scripts/test_backfill_account_phones.py

key-decisions:
  - "Каркас build_sources (NotImplementedError) объявлен в GREEN-коммите задачи 1, потому что amain его вызывает; боевая сборка — GREEN задачи 2"
  - "Длина очереди WA/MAX — два явных лямбда-вызова с литералом типа, а не цикл с поздним связыванием"
  - "amain создаёт движок и собирает источники внутри try: отказ настроек или Redis даёт код 1 и `Прогон прерван: <класс>`, текст исключения не печатается"

requirements-completed: []
requirements-addressed: [PHONE-17, PHONE-18, PHONE-19, PHONE-20]

coverage:
  - id: D1
    description: "Одна команда `just`: backfill-phones (локально, без Docker и без флага Telegram) и prod-backfill-phones (docker compose exec -T web с --telegram-from-container); у обоих `WRITES by default`"
    requirement: "PHONE-17"
    verification:
      - kind: integration
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_recipes_prod_uses_exec_t_web_and_local_has_no_docker"
        status: pass
      - kind: integration
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_recipes_say_they_write_by_default"
        status: pass
    human_judgment: false
  - id: D2
    description: "Справка настоящим процессом: код 0, говорит ПИШЕТ, --dry-run, --wake с 401/403/405, --type, --account-id, --limit, --telegram-from-container; первая строка прогона называет режим"
    requirement: "PHONE-17"
    verification:
      - kind: integration
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_script_help_runs_and_says_it_writes"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_tracer_amain_parses_runs_and_exits_zero"
        status: pass
    human_judgment: false
  - id: D3
    description: "--wake вместе с --dry-run отвергается кодом 2 до выборки и до вызова источника; --type повторяем и ограничен tg_user/wa/max; --account-id и --limit — положительные целые"
    requirement: "PHONE-18"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_wake_with_dry_run_is_rejected_before_any_source_call"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_argument_errors_exit_two"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_type_filter_can_repeat"
        status: pass
    human_judgment: false
  - id: D4
    description: "Коды выхода D-15: 0 при исходах «воркер недоступен», «занят», «номера нет»; 1 и `Прогон прерван: <класс>` без текста исключения при отказе базы; 2 при ошибке аргументов"
    requirement: "PHONE-17"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_exit_code_zero_even_when_nothing_was_filled"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_run_failure_exits_one_with_the_class_name"
        status: pass
    human_judgment: false
  - id: D5
    description: "Telegram опрашивается только из боевого контейнера: без флага аккаунт tg_user получает «воркер недоступен» с заметкой `just prod-backfill-phones`, клиент не строится; боевая сборка связывает WorkerStatusSource, TelegramSource, TelegramBusyProbe и TelegramClient, ни к чему не подключаясь"
    requirement: "PHONE-20"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_build_sources_guards_telegram_outside_the_container"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_backfill_account_phones.py#test_build_sources_wires_the_real_sources"
        status: pass
    human_judgment: false
  - id: D6
    description: "Боевой прогон из контейнера web на настоящих Docker, Redis, Celery, Telegram, WhatsApp и MAX (допущения A1, A3, A4 RESEARCH) — шаг владельца после выката, тестами с двойниками не измеряется"
    requirement: "PHONE-20"
    verification: []
    human_judgment: true
    rationale: "Короткое подключение Telegram без AuthKeyDuplicated, код 405 у Baileys при --wake и отдаёт ли MAX номер при восстановлении сессии видны только на бою"

duration: 35min
completed: 2026-11-23
status: complete
---

# Phase 20 Plan 06: Оболочка команды дозаполнения номеров Summary

**Разовая команда дозаполнения номеров доведена до запуска: `just backfill-phones` и `just prod-backfill-phones` (через `exec -T web`, единственный путь опроса Telegram) над скриптом с разбором аргументов и отказами до начала работы, кодами выхода 0/1/2, стражем Telegram вне контейнера и боевой сборкой источников без подключений; запуск без флагов пишет — и это сказано в справке, шапке, рецептах и первой строке вывода.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-11-23T18:20:00Z (приблизительно)
- **Completed:** 2026-11-23T18:56:00Z
- **Tasks:** 2 (трасер + закрепляющие правила)
- **Files modified:** 3 (все из `files_modified`)

## Accomplishments

- `build_parser` (`--dry-run`, `--wake`, `--type` с `choices=KINDS` и `action="append"`, `--account-id`, `--limit`, `--telegram-from-container`), `options_from`, `amain(argv, *, session_factory, sources) -> int`, блок `__main__`; описание начинается «ЗАПУСК БЕЗ ФЛАГОВ ПИШЕТ В БАЗУ».
- Полная шапка модуля: формы вызова, «пишет по умолчанию» в отличие от `--apply` соседних скриптов, чего скрипт не делает никогда, предупреждение подъёма (вход в WhatsApp/MAX, 401/403/405 — воркер сам удалит файлы сессии), коды выхода, порядок выката, проверка `just wa-workers` / `just max-workers` после обрыва, неисправимость номера из формы MAX (ревью 19 IN-03), устаревание поручения о переносе `credentials` (O-3 (а)).
- `amain`: `parser.error` (код 2) для `--wake` с `--dry-run`, `--account-id <= 0`, `--limit <= 0` до всякой работы; движок и сборка источников внутри `try` — отказ даёт код 1 и `Прогон прерван: <имя класса>`.
- `TelegramOutsideContainerSource` (исход «воркер недоступен», заметка называет `just prod-backfill-phones`) и `build_sources(settings, *, telegram_from_container)`: синхронный клиент Redis (ленивый), `WorkerStatusSource` для `wa` и `max` с `queue_len` по `queue_key`, `TelegramSource` с `TelegramClient` и `TelegramBusyProbe(inspector_factory=lambda: celery.control.inspect(timeout=INSPECT_TIMEOUT), …)`; приложение Celery ввозится внутри функции и только на пути Telegram.
- `justfile`: два рецепта после пары `prod-recompress-attachments`, прочие не тронуты.

## Task Commits

1. **Task 1 (tracer)** — RED `37eec3a7` (`test(20-06)`), GREEN `b5ba2c6b` (`feat(20-06)`; в нём же рецепты `justfile`)
2. **Task 2** — RED `17df42db` (`test(20-06)`), GREEN `a2bb5757` (`feat(20-06)`)

**Plan metadata:** коммит `docs(20-06)` с этой сводкой (следует за `plan_head_after`).

## TDD

### RED, задача 1 (трасер)

`test_tracer_amain_parses_runs_and_exits_zero`; каркас `amain` возвращает `0` без прогона, `build_parser` знает только `--dry-run` (разбор через `parse_known_args`, чтобы трасер дошёл до утверждения, а не упал на `SystemExit`). Команда: `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly --tb=line --junitxml=.gsd/tdd-evidence/20-06/red-1.xml`, код выхода 1.
Три совпадения: `FAILED …::test_tracer_amain_parses_runs_and_exits_zero` (среди четырёх красных: ещё два рецепта и справка); итог `4 failed, 135 passed`; причинный литерал «amain не провёл прогон» (в XML).
`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `target_test_failed`, `format: junit`, 139 тестов, 4 падения.
`semanticAssessment`: цель собрана и исполнена, упала на утверждении о колонках номера (каркас вернул 0 без прогона); ошибок сбора, ввоза и фикстур нет.

### GREEN / REFACTOR, задача 1

Парсер, `amain`, шапка, рецепты: файл тестов — 139 passed; `just --dry-run prod-backfill-phones --account-id 7` печатает `docker compose -f docker-compose.prod.yml exec -T web uv run python scripts/backfill_account_phones.py --telegram-from-container --account-id 7`; три гейта номера — 1161 passed. `⚡ Tracer verified end-to-end — expanding`. REFACTOR не потребовался.

### RED, задача 2

Цель — `test_wake_with_dry_run_is_rejected_before_any_source_call`. Красны шесть: цель, `test_argument_errors_exit_two[limit-zero|limit-negative|account-zero]`, оба `test_build_sources_*` (каркас `build_sources` и отсутствие `TelegramOutsideContainerSource`; на них опирается GREEN). Итог `6 failed, 144 passed`; причинный литерал «--wake принят вместе с --dry-run» (1 вхождение в XML, `red-2.xml`).
`gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK`, `target_test_failed`, 150 тестов, 6 падений.
`semanticAssessment`: цель исполнена и упала на планируемом утверждении (`SystemExit` не поднят, прогон пошёл, код выхода 0); остальные красные правила — по той же причине, что и план (отсутствие отказов и сборки); ошибок сбора и фикстур у цели нет.

### GREEN, задача 2

Отказы аргументов, `TelegramOutsideContainerSource`, `build_sources`: файл — 150 passed; три гейта номера — 1161 passed; `test_account_phone_writer`/`test_account_phone_race`/`test_log_masking` с `-k "phone or without_setup_logging"` — 33 passed.

### Отрицательные контроли (мутация скрипта, `--tb=line`, правка снята `git checkout --`; не коммитились)

1. Отказ `--wake` с `--dry-run` отключён (`if False and …`) → красен `test_wake_with_dry_run_is_rejected_before_any_source_call`: `--wake принят вместе с --dry-run (код выхода 0)`.
2. Код `1` при исходе «воркер недоступен» → красен `test_exit_code_zero_even_when_nothing_was_filled` (`1 failed`).
3. Без флага контейнера строится настоящий `TelegramSource` → красен `test_build_sources_guards_telegram_outside_the_container`: `AssertionError: assert False` (первая версия мутации ввозила Celery и падала на настройках — слабый контроль; повторена без ввоза Celery).
4. В строку прерывания добавлен `str(exc)` → красен `test_run_failure_exits_one_with_the_class_name`: `в строку прерывания попал текст исключения`.
5. Снят `choices` у `--type` → красен `test_argument_errors_exit_two[unknown-type]`: `DID NOT RAISE <class 'SystemExit'>` (остальные четыре параметра зелёные).

## Files Created/Modified

- `scripts/backfill_account_phones.py` — полная шапка; ввозы `argparse`, `redis`, `TelegramClient`, `get_settings`, `get_engine`, `get_session_factory`; `build_parser`, `options_from`, `TelegramOutsideContainerSource`, `build_sources`, `amain`, блок `__main__`
- `justfile` — рецепты `backfill-phones *args` и `prod-backfill-phones *args`
- `tests/test_scripts/test_backfill_account_phones.py` — `_just`, `_recipe_line`, `empty_factory`; трасер и 11 правил оболочки (рецепты, справка, отказы, коды выхода, страж Telegram, сборка); файл — 150 тестов

## Decisions Made

См. `key-decisions`. Отдельно: на задаче 1 `amain` обращается к `build_sources`, поэтому каркас с `NotImplementedError` объявлен в её GREEN-коммите и заменён боевой сборкой на задаче 2; ни в одном коммите нет пути, где он молча возвращает пустое.

## Deviations from Plan

### Auto-fixed Issues

**1. [Plan text vs tree] Каркас RED разбирает аргументы через `parse_known_args`**
- **Found during:** Task 1 (RED)
- **Issue:** план велит каркасу `build_parser` с одним `--dry-run`; трасер передаёт `--type` и `--account-id`, и `parse_args` каркаса падал бы `SystemExit(2)` — не утверждением, а значит недействительным RED.
- **Fix:** каркас вызывает `parse_known_args`; трасер доходит до утверждения «amain не провёл прогон».
- **Files modified:** `scripts/backfill_account_phones.py` (RED-коммит `37eec3a7`, заменён в GREEN `b5ba2c6b`)
- **Verification:** `RED_EVIDENCE_OK`.

**2. [Rule 3 - Blocking] Тест сборки источников задаёт настройки через `monkeypatch`**
- **Found during:** Task 2 (тест 7)
- **Issue:** `from app.worker.celery_app import celery` внутри `build_sources` читает `get_settings()`; в дереве без `.env` падало бы `ValidationError` (то же, что в 20-05). Клиент Redis подменяется `monkeypatch.setattr(script.redis, "from_url", …)`, чтобы сборка не ходила в настоящий Redis.
- **Fix:** `DATABASE_URL`/`SECRET_KEY` через `monkeypatch.setenv`, `get_settings.cache_clear()` до и после; утечки настроек в другие модули нет.
- **Files modified:** `tests/test_scripts/test_backfill_account_phones.py`
- **Verification:** файл 150 passed; `tests/test_scripts/` зелён.
- **Committed in:** `17df42db`

**3. [Plan text vs tree] Составные команды в песочнице**
- Песочница отказывается от составных команд с `git`/heredoc; правки шли через Write/Edit и небольшие вспомогательные скрипты в `.gsd/tdd-evidence/20-06/` (каталог игнорируется `.gitignore`, в коммиты не попал). Улика RED собрана тем же способом.

---

**Total deviations:** 1 auto-fixed (Rule 3), 2 заметки о плане и среде.
**Impact on plan:** файлы вне `files_modified` не менялись (`git diff -- app/ wa_worker/ max_worker/ docker-compose*.yml Dockerfile` пуст); границы D-08, D-10, D-15, PHONE-20 не сдвинуты.

## Issues Encountered

None.

## Known Stubs

None. Каркас `build_sources` задачи 1 заменён боевой сборкой в задаче 2.

## Threat Flags

None. Новой сетевой поверхности нет: скрипт запускает администратор на хосте (`just` → `docker compose exec -T web`); аргументы ограничены `choices` и проверкой положительных целых (T-20-22…T-20-24 закрыты тестами выше; T-20-25 принят планом — копия боевой базы не делается).

## User Setup Required

None - no external service configuration required.

## Для владельца (после выката, вне критериев фазы)

**Порядок выката и первого боевого прогона** (в фазе не исполнялся; ни одного `just prod-*`, боевого `web` и копии боевой базы):

1. Выкатить образ приложения: скрипт попадает в боевой `web` только после пересборки образа (`COPY . .`, код не монтируется).
2. Пересобрать образы воркеров WA и MAX и перезапустить работающие воркеры.
3. `just prod-backfill-phones --dry-run --account-id <id>` — по одному аккаунту каждого типа (`tg_user`, `wa`, `max`).
4. Прогон с записью — порциями (`--type`, `--account-id`, `--limit`). ЗАПУСК БЕЗ `--dry-run` ПИШЕТ.
5. После обрыва прогона с `--wake` проверить `just wa-workers` и `just max-workers`: поднятый воркер мог остаться запущенным. `--wake` — вход в WhatsApp/MAX; при ответе 401/403/405 воркер сам удалит файлы сессии.

**Что видно только на бою:**
- A1 — короткое подключение Telegram из `web` без `AuthKeyDuplicated`.
- A3 — код 405 у Baileys при `--wake`.
- A4 — отдаёт ли MAX номер при восстановлении сессии (на 2026-11-23 после PyMax 2.5.0 — по записи владельца отдаёт).

**Устаревшее:** поручение `16-CONTEXT.md` D-01 о переносе номера из `credentials` MAX и комментарий `app/models/messenger_account.py:81-82` устарели (O-3 (а)); номер, введённый в форму MAX, хранится как автоматический и исправляется только вручную (ревью 19 IN-03). Файл не правился.

## Gates

- `tests/test_scripts/test_backfill_account_phones.py` — 150 passed.
- `tests/test_scripts/ tests/test_wa_worker_deployment.py tests/test_max_worker_deployment.py` — 181 passed.
- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py` — 1161 passed (после обеих задач).
- `tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_services/test_log_masking.py -k "phone or without_setup_logging"` — 33 passed.
- `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_schedule_invariants.py tests/test_services/test_log_masking.py tests/test_application/test_declared_invariants.py tests/test_application/test_phone_writer_runtime_guard.py` — 295 passed.
- `tests/test_planning` — 218 passed, 2 skipped (до сводки; после коммита сводки — в возврате).
- `uv run python -m compileall -q scripts tests/test_scripts` — код 0; `grep -rn "\.cte(\|add_cte\|exec_driver_sql\|INSERT OR REPLACE\|prefix_with"` по скрипту — пусто.
- `just --dry-run prod-backfill-phones --dry-run` и `just --dry-run backfill-phones --dry-run` — команды печатаются, ничего не исполняется.
- grep-гейты: `^backfill-phones \*args:$` = 1; `^prod-backfill-phones \*args:$` = 1; `exec -T web uv run python scripts/backfill_account_phones.py --telegram-from-container` = 1; `WRITES by default` = 2; `exec web uv run python` = 3; `async def amain(` = 1; `class TelegramOutsideContainerSource` = 1; `def build_sources` = 1; правил оболочки задачи 2 в тестах = 7.
- `graphify update .` и `just test` не запускались (по поручению оркестратора); записи PHONE-17…PHONE-20 остаются `Pending`.

## Next Phase Readiness

Готов план 20-07 (последний в фазе): ветка предсказания просмотра в ядре `run`. Оболочка опирается на уже существующий `RunOptions.dry_run`, новых имён для 20-07 не нужно.

## Self-Check: PASSED

---
*Phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov*
*Completed: 2026-11-23*

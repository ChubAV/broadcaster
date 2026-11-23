---
phase: "20"
slug: "dozapolnenie-nomerov-suschestvuyuschih-akkauntov"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-23"
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `20-RESEARCH.md` §Validation Architecture (замеры 2026-11-23). Карту задач ниже
> заполняет планировщик по своим планам (строка на задачу).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio ≥ 1.3.0; `db_session` из `tests/conftest.py` (SQLite in-memory); для гонки критерия 2 — файловая база с двумя независимыми сессиями (образец `tests/test_application/test_account_phone_race.py:97-100`); Docker, HTTP воркеров и Telethon — только двойники внедряемых источников ядра `run(...)`: тесты не касаются ни Docker, ни Telegram, ни сети |
| **Config file** | отдельного нет (pytest в dev-зависимостях `pyproject.toml`); фикстуры `tests/conftest.py`; образец теста скрипта — `tests/test_scripts/test_recompress_attachments.py` (`tests/test_scripts/__init__.py` уже есть) |
| **Quick run command** | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly` |
| **Full suite command** | `just test` (≈46 мин, 6143 passed на закрытии Фазы 19; только гейт фазы, таймаут 5400 с, исполнители её не гоняют) |
| **Estimated runtime** | быстрый прогон задачи — секунды; гейты номера — ≈65 с (1161 passed, замер 2026-11-23); записи — ≈22 с (218 passed, 2 skipped) |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly` + гейты номера (ниже) для любой задачи, трогающей файл скрипта
- **After every plan wave (гейты поимённо, в `<automated>` каждого плана — D-07):**
  - гейты номера: `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`
  - писатель и маска: `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_services/test_log_masking.py -k "phone or without_setup_logging" -q -p no:randomly`
  - скрипты: `uv run pytest tests/test_scripts/ -q -p no:randomly`
  - сквозной гейт 302-пар (фаза число не двигает, но исполнители его пропускают): `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q -p no:randomly`
- **Records:** `uv run pytest tests/test_planning -q -p no:randomly` (≈22 с) — явно, после каждой правки ROADMAP/STATE (исполнители записи отключают)
- **Before `/gsd-verify-work`:** полная суита зелёная (`just test`, таймаут 5400 с); `grep -rn "\.cte(\|add_cte\|exec_driver_sql\|INSERT OR REPLACE\|prefix_with" app/ scripts/ --include=*.py` без шапок гейтов — пусто (долг (i) части C RESEARCH: границы О-26 скрипт не задевает)
- **Max feedback latency:** 120 секунд на задачу

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 20-01 | 1 | PHONE-17 | T-20-01, T-20-02 | значение источника пишет только `fill_reported_phone`, коммит сессией аккаунта, строка «заполнено» — маской | unit (трасер ядра, файловая база) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k test_tracer_a_reported_number` | ❌ W0 | ⬜ pending |
| 20-01-02 | 20-01 | 1 | PHONE-17, PHONE-18 | T-20-01, T-20-03, T-20-04, T-20-05 | выборка без ручных и заполненных при любом статусе; статус не меняется; повтор ничего не меняет; ручной номер во время прогона не затёрт; удалённый — отдельный исход; сбой одного не обрывает и не откатывает; просмотр не вызывает писателя (журнал `_count_writer` пуст, снимок равен; та же обёртка видит вызовы в прогоне записи — D-06 в волне 1) | unit + integration (две сессии одной файловой базы) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "selection or status_unchanged or idempotent or manual_entered_during_the_run or deleted_during_the_run or one_failing_account or dry_run_never_calls_the_writer"` | ❌ W0 | ⬜ pending |
| 20-02-01 | 20-02 | 2 | PHONE-19 | T-20-06 | адрес только из списка Docker `running`, собственный запрос `/status`, номер — писателем | unit (трасер WA) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k test_tracer_running_worker` | ❌ W0 | ⬜ pending |
| 20-02-02 | 20-02 | 2 | PHONE-19 | T-20-07, T-20-08 | таблица A6 для WA и MAX; целое `phone` точно, дробное и `bool` — «номера нет»; отказы транспорта — классом без текста | unit (параметризация) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k classify_status` | ❌ W0 | ⬜ pending |
| 20-02-03 | 20-02 | 2 | PHONE-19, PHONE-18 | T-20-06, T-20-09 | путь по умолчанию: ноль `start_container`, адаптеры и их помощники не вызываются, один список на тип, отказ Docker — исход аккаунта | unit | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "default_polls_only_running or docker_listing or docker_unavailable or never_wakes_through_adapters or starts_no_container or polled_once"` | ❌ W0 | ⬜ pending |
| 20-03-01 | 20-03 | 3 | PHONE-19 | T-20-10, T-20-11 | по флагу: подъём → ожидание `/health` 90 с → `/status` → запись → остановка | unit (трасер подъёма) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k test_tracer_wake` | ❌ W0 | ⬜ pending |
| 20-03-02 | 20-03 | 3 | PHONE-19, PHONE-18 | T-20-10, T-20-11, T-20-13 | условия O-1 (а): только `active`, очередь 0 / 1 до и после, чужой контейнер не гасится, просмотр не будит, по одному | unit (параметризация) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "wake_conditions_matrix or never_stops or queue_filled or wake_with_dry_run_in_the_core or one_container_at_a_time"` | ❌ W0 | ⬜ pending |
| 20-03-03 | 20-03 | 3 | PHONE-19 | T-20-12 | MAX: до 45 попыток `/status` с паузой 2 с; окна WA 90 с / MAX 30 с; остановка при отказе и `CancelledError` | unit | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "polls_until_connected or ready_windows or stops_the_container_on_failure"` | ❌ W0 | ⬜ pending |
| 20-04-01 | 20-04 | 4 | PHONE-20 | T-20-14 | клиент с `receive_updates=False`, без интерактивного входа, `connect → is_user_authorized → get_me`, `disconnect` | unit (трасер TG, двойник Telethon) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k test_tracer_telegram` | ❌ W0 | ⬜ pending |
| 20-04-02 | 20-04 | 4 | PHONE-20 | T-20-15, T-20-16, T-20-17 | карта исходов Telethon по классам (D-17); плохая строка сессии — до сети; `disconnect` на каждом пути; в выводе нет строки сессии и текста исключений | unit (параметризация) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "telegram_outcomes or bad_session_string or disconnect_awaited or missing_api_credentials or no_session_or_exception_text"` | ❌ W0 | ⬜ pending |
| 20-04-03 | 20-04 | 4 | PHONE-20, PHONE-18 | T-20-14 | занятый и неопределённый — ни одного подключения; не больше одного клиента одновременно; просмотр опрашивает и не пишет | unit | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "telegram_busy or telegram_sequential or telegram_dry_run"` | ❌ W0 | ⬜ pending |
| 20-05-01 | 20-05 | 5 | PHONE-20 | T-20-18 | задача отправки аккаунта в снимке `inspect` → «занят», клиент не строится | unit (трасер признака) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k test_tracer_busy_probe` | ❌ W0 | ⬜ pending |
| 20-05-02 | 20-05 | 5 | PHONE-20 | T-20-18, T-20-19, T-20-20 | отказ в закрытую; ответ воркера `telegram` обязателен; настоящее сообщение kombu из списка `telegram`; маршрут и позиция `account_id` сверены | unit | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k busy_probe` | ❌ W0 | ⬜ pending |
| 20-06-01 | 20-06 | 6 | PHONE-17, PHONE-20 | T-20-22, T-20-23 | `prod-backfill-phones` — `exec -T web` с флагом Telegram, локальный — без Docker; `WRITES by default`; `--help` настоящим процессом; `amain` → 0 | unit + CLI (`just --dry-run`, `just --list`) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "test_tracer_amain or recipes or help_runs"` и `just --dry-run prod-backfill-phones --account-id 7` | ❌ W0 | ⬜ pending |
| 20-06-02 | 20-06 | 6 | PHONE-18, PHONE-19, PHONE-20 | T-20-23, T-20-24 | `--wake` с `--dry-run` — код 2 до любой работы; коды выхода 0 / 1 / 2; Telegram без флага контейнера не опрашивается; боевые источники собраны без подключений | unit | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "wake_with_dry_run_is_rejected or argument_errors or type_filter or exit_code_zero or run_failure_exits_one or build_sources"` | ❌ W0 | ⬜ pending |
| 20-07-01 | 20-07 | 7 | PHONE-18 | T-20-05 | просмотр предсказывает «ручной / уже заполнен», «удалён во время прогона», «номера нет» чтением строки; писатель не вызывается ни в каком виде | unit (трасер предсказания; файловая база, вторая сессия в крюке источника) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k test_dry_run_predicts_kept_and_gone_by_reading` | ❌ W0 | ⬜ pending |
| 20-07-02 | 20-07 | 7 | PHONE-18, PHONE-17 (PHONE-21) | T-20-02, T-20-05 | просмотр не вызывает писателя и не меняет строк; итог всех восьми исходов в порядке `Outcome`; в выводе нет 7+ цифр, маска есть, текста исключений и `credentials` нет | unit | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "dry_run_writes_nothing or summary_counts or output_masks"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Каждый каркас создаёт задача-трасер своего плана (RED-коммит несёт тест и объявительный каркас кода,
чтобы RED был отказом утверждения, а не ошибкой сбора):

- [ ] `tests/test_scripts/test_backfill_account_phones.py` — новый (20-01, задача 1); дополняется планами 20-02…20-07: все строки карты «Phase Requirements → Test Map» из `20-RESEARCH.md` (PHONE-17 выборка / идемпотентность / ручной номер во время прогона / итог; PHONE-18 `--dry-run` и отказ `--wake` под ним; PHONE-19 только работающие, подъём по флагу, классификация `/status`, адаптеры не будят; PHONE-20 последовательность TG, «занят», карта ошибок, рецепты; PHONE-21 маска вывода с антивакуумом)
- [ ] фикстура `factory` — файловая база во `tmp_path` с независимыми сессиями (образец `tests/test_application/test_account_phone_race.py:97-100`), двойник источника `RecordingSource` с крюком `before_reply` — для критерия 2 (20-01, задача 1)
- [ ] страж `_no_real_docker` (журнал обращений к `_get_docker_client` обоих менеджеров, пустой на разборке), `_status_transport` на `httpx.MockTransport` (20-02, задача 1); двойники подъёма / ожидания / остановки / очереди с общим журналом событий (20-03, задача 1)
- [ ] двойник Telethon-клиента `FakeTelegramClient` со счётчиком одновременных подключений `max_open`, `start` и давней проверкой соединения адаптера с `assert_not_called()`, `disconnect` с проверкой ожидания в `finally`; годная строка сессии без сети (20-04, задача 1)
- [ ] двойники инспектора Celery и Redis; настоящее сообщение kombu через транспорт `memory://` (20-05, задачи 1–2)
- [ ] помощник `_just(*words)` поверх `just --dry-run` / `just --list` (20-06, задача 1)

*Новых зависимостей и каркаса нет — `pytest`, `pytest-asyncio`, `httpx`, `just` существуют.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

Вне критериев фазы и не ручная проверка фазы (CONTEXT §Phase Boundary; ответ владельца O-4 (а), 2026-11-23): боевой прогон — шаг владельца после выката (деплой-гейт). Порядок: образ приложения → образы воркеров → перезапуск работающих воркеров → `just prod-backfill-phones --dry-run --account-id <один>` по одному аккаунту каждого типа → прогон с записью. Там же видны допущения RESEARCH, которые тестами не измерить: A4 (отдаёт ли MAX `contact.phone` при восстановлении сессии), A3 (код 405 у Baileys при `--wake`), A1 (короткое подключение TG без `AuthKeyDuplicated`).

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

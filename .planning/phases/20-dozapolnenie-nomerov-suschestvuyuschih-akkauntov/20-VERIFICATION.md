---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
verified: 2026-11-23T21:30:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-01-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-01-SUMMARY.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-02-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-02-SUMMARY.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-03-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-03-SUMMARY.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-04-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-04-SUMMARY.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-05-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-05-SUMMARY.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-06-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-06-SUMMARY.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-07-PLAN.md
  - .planning/phases/20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov/20-07-SUMMARY.md
  - justfile
  - scripts/backfill_account_phones.py
  - tests/test_scripts/test_backfill_account_phones.py
covered_digest: "v4:sha256:21a67b26de6d90d4a83ca23dae5dad9814f682a477121a245d1a183d7818aa40"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 20: Дозаполнение номеров существующих аккаунтов Verification Report

**Phase Goal:** аккаунты, подключённые до вехи, получают номер одной командой администратора — без риска разлогинить сессию, разбудить спящий воркер или затереть ручное значение
**Verified:** 2026-11-23
**Status:** passed (с четырьмя предупреждениями по коду, ни одно не опровергает критерий; см. «Предупреждения»)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Одна команда `just`: аккаунты без номера получают номер, ручные и заполненные не трогаются, статус не меняется; итог по исходам; номера маскированы | ✓ VERIFIED | `justfile:178-183` рецепты `backfill-phones` / `prod-backfill-phones`. `select_candidates` (`scripts/backfill_account_phones.py:182-209`) выбирает КОЛОНКИ `phone IS NULL AND phone_is_manual IS FALSE`, ORM-сущностей в сессию не попадает. В скрипте нет ни `update(`, ни присваивания `phone`/`status`/`phone_is_manual` (grep пуст). Итог: `run()` `:658-700` печатает счётчик на каждый член `Outcome` (заполнено / ручной / номера нет / сессия мертва / воркер недоступен / занят / удалён / сбой). Номер печатается только `mask_phone(normalize_reported(...))` (`:690`). Тесты: `test_selection_skips_manual_and_filled_and_ignores_status`, `test_status_unchanged_by_any_outcome`, `test_output_masks_numbers_and_has_a_filled_line`. |
| 2 | Повтор ничего не меняет; ручной номер, введённый во время прогона, не затирается — только условная запись Фазы 16 | ✓ VERIFIED | Единственная запись — `fill_reported_phone` (`:222-232`), внутри один `UPDATE … WHERE id=? AND phone IS NULL AND NOT phone_is_manual` (`app/application/accounts/phone.py:111-150`, прочитан). Тесты на файловой базе с двумя сессиями: `test_manual_entered_during_the_run_is_kept`, `test_idempotent_second_run_changes_nothing`. Гейты `test_application/test_phone_single_writer_gate.py`, `test_phone_privacy_gate.py`, `test_phone_gates_parity.py` зелёные, имя скрипта в изъятиях не значится (grep). |
| 3 | `--dry-run`: показывает, ничего не пишет, ни одного контейнера | ✓ VERIFIED | `_preview` (`:235-266`) не зовёт писателя, предсказывает исход двумя `exists()`-чтениями. `WorkerStatusSource.poll` (`:342-351`): `if not options.wake or options.dry_run` -> «воркер не запущен», `_wake` недостижим; `--wake --dry-run` — отказ аргументов до любой работы (`amain`, `:812-814`). Реальный запуск `--wake --dry-run` дал `error: --wake несовместим с --dry-run`, код выхода 2. Тесты: `test_dry_run_never_calls_the_writer`, `test_dry_run_starts_no_container`, `test_wake_with_dry_run_in_the_core_starts_nothing`, `test_wake_with_dry_run_is_rejected_before_any_source_call`, `test_dry_run_writes_nothing_and_predicts`. |
| 4 | По умолчанию только работающие WA/MAX; остановленный поднимается лишь по флагу и гасится после опроса | ✓ VERIFIED | Путь по умолчанию: «работает» решает только Docker (`list_worker_containers`, статус `running`), адрес из имени контейнера; нет работающего контейнера -> «воркер недоступен», `start_container` не зовётся (`:337-351`). Адаптеры, которые сами будят воркер, не используются (`test_never_wakes_through_adapters`). По `--wake`: только `status == "active"`, очередь прочитана и `== 0`, по одному (`_wake`, `:353-378`); `_wake_and_ask` гасит поднятый в `finally` (`:380-410`), в т. ч. при отказе опроса и `CancelledError` (`test_wake_stops_the_container_on_failure_and_cancellation`). Источник — настоящий `/api/sessions/:id/status` воркеров (`wa_worker/index.js:747-765` отдаёт `phone`, `max_worker/main.py:1014`). Оговорки — WR-01…WR-03 ниже. |
| 5 | TG: строго последовательно, изнутри боевого контейнера (`exec -T web`), без `start()`, без приёма обновлений, `disconnect` в `finally` | ✓ VERIFIED (механизмы); исход на бою — шаг владельца (O-4 (а)) | `prod-backfill-phones` = `docker compose -f docker-compose.prod.yml exec -T web … --telegram-from-container`; без флага источник — `TelegramOutsideContainerSource`, клиент не строится (`:741-755`). `TelegramSource.poll` (`:469-541`): разбор строки сессии до сети, `receive_updates=False`, `connect -> is_user_authorized -> get_me`, нет `start()`, `disconnect` в `finally`, ошибки Telethon разобраны по классам (D-17, `check_connection` не используется). Занятость — `TelegramBusyProbe` (Celery `inspect` active ∪ reserved + список Redis `telegram`), отказ в закрытую. Тесты: `test_telegram_disconnect_awaited_on_every_path`, `test_telegram_sequential_one_client_at_a_time`, `test_telegram_busy_account_is_never_connected`, `test_telegram_busy_unknown_fails_closed`, `test_busy_probe_*` (в т. ч. настоящее сообщение kombu). |

**Score:** 5/5 истин подтверждены (0 присутствуют, но поведение не проверено).

Дополнительные истины планов (D-01, D-05, D-07, D-08, D-14, D-15, D-16, D-17) проверены в тех же местах: единый писатель, коммит на аккаунт (`_write`, `:222-232`), исключение по аккаунту становится исходом (`_poll`, `:212-219`), коды выхода 0/1/2 (`amain`), «пишет по умолчанию» в справке, docstring и комментариях рецептов (`test_recipes_say_they_write_by_default`, `test_script_help_runs_and_says_it_writes`, сверено вручную `--help`).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/backfill_account_phones.py` | ядро, источники WA/MAX/TG, оболочка (840 строк) | ✓ VERIFIED | Содержательный, подключён: рецепты `just`, `--help` исполняется, `amain` собирает боевые источники |
| `justfile` (`backfill-phones`, `prod-backfill-phones`) | локальный и боевой рецепты | ✓ VERIFIED | `just --dry-run prod-backfill-phones --account-id 7` -> `docker compose … exec -T web uv run python scripts/backfill_account_phones.py --telegram-from-container --account-id 7`; `uv`, `httpx`, `redis`, `telethon`, `docker`, `celery` — основные зависимости образа (`Dockerfile:9,17,20`) |
| `tests/test_scripts/test_backfill_account_phones.py` | 63 теста тел., 155 с параметрами | ✓ VERIFIED | Исполнены мной |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| скрипт | `fill_reported_phone` | `_write` | WIRED | единственный путь записи в колонку |
| скрипт | `/status` воркеров WA/MAX | `WorkerStatusSource._ask` + `classify_status` + `reported_phone_from_status` | WIRED | путь и поле `phone` существуют в `wa_worker/index.js` и `max_worker/main.py` |
| скрипт | `start_container` / `stop_container` / `get_container_endpoint` / `wait_for_container_ready` / `list_worker_containers` | менеджеры, `asyncio.to_thread` | WIRED | сигнатуры сверены с `app/services/*_container_manager.py` (`timeout=` — keyword-only, совпадает) |
| скрипт | задача отправки TG и очередь `telegram` | `SEND_TASK`, `ACCOUNT_ARG_INDEX`, `TELEGRAM_QUEUE` | WIRED | `test_busy_probe_constants_match_the_send_task` сверяет с `celery_app.task_routes` |
| `prod-backfill-phones` | `--telegram-from-container` | рецепт | WIRED | см. выше |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| `run()` | `reply.reported` | `/status.phone` воркера / `User.phone` Telethon (`reported_phone_of`) | да: поле реально отдают оба воркера, TG — `get_me()` | ✓ FLOWING |
| `run()` | кандидаты | SQL-выборка колонок `MessengerAccount` | да | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Тесты скрипта и три гейта номера | `flock … pytest tests/test_scripts/test_backfill_account_phones.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q` | 1316 passed, 1 warning, 71 с | ✓ PASS |
| Справка говорит «пишет по умолчанию» | `uv run python scripts/backfill_account_phones.py --help` | выход 0, текст «ЗАПУСК БЕЗ ФЛАГОВ ПИШЕТ В БАЗУ» | ✓ PASS |
| `--wake --dry-run` отвергается | `… --wake --dry-run` | `error: --wake несовместим с --dry-run`, выход 2 | ✓ PASS |
| Боевой рецепт | `just --dry-run prod-backfill-phones --account-id 7` | `exec -T web … --telegram-from-container --account-id 7` | ✓ PASS |

Полную суиту не запускал (данные оркестратора: 6298 passed, 2 skipped, 0 failed на `c0ef8fe1`; после — только `.planning/`).

### Probe Execution

SKIPPED: фаза не объявляет проб `scripts/*/tests/probe-*.sh`.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| PHONE-17 | 20-01, 20-02, 20-04, 20-06, 20-07 | одна команда `just`, ручные/заполненные не трогаются, повтор идемпотентен, итог по исходам | ✓ SATISFIED | критерии 1, 2 |
| PHONE-18 | 20-01, 20-02, 20-03, 20-06, 20-07 | `--dry-run`: ничего не пишет, контейнеры не поднимает | ✓ SATISFIED | критерий 3 |
| PHONE-19 | 20-02, 20-03, 20-06 | по умолчанию только работающие; остановленные — по флагу и гасятся | ✓ SATISFIED (с WR-01…WR-03) | критерий 4 |
| PHONE-20 | 20-04, 20-05, 20-06 | TG последовательно, изнутри боевого контейнера, без риска `AuthKeyDuplicatedError` | ✓ SATISFIED (механизмы; бой — O-4 (а)) | критерий 5 |

Все четыре ID присутствуют в `requirements:` планов и в `REQUIREMENTS.md:46-49`; осиротевших требований нет (PHONE-21 принадлежит Фазе 16, `Complete`). В `REQUIREMENTS.md` PHONE-17…20 остаются `Pending` — ожидаемо до прохождения верификации, это не пробел.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `scripts/backfill_account_phones.py` | `TBD` / `FIXME` / `XXX` | — | не найдено |
| `scripts/backfill_account_phones.py` | пустые реализации, заглушки | — | не найдено; все `except Exception` объяснены и превращаются в исход аккаунта |

### Предупреждения (оценка находок 20-REVIEW.md по исходникам)

Все восемь находок записаны `open` в `20-REVIEW-DISPOSITION.md`. Ни одна не опровергает критерий и не ломает цель фазы; четыре предупреждения WARNING стоит разобрать владельцу до выката `--wake`.

- **WR-01 (подтверждено, WARNING).** `stop_container` обоих менеджеров ловит `APIError` сам и возвращает `False` (`wa_container_manager.py:85-100`, `max_container_manager.py:94-109`), а `_stop_if_idle` (`scripts/backfill_account_phones.py:431-438`) результат `to_thread(self._stop, …)` отбрасывает и возвращает `""`. При отказе Docker поднятый воркер остаётся без заметки «контейнер оставлен». Тест `test_wake_stop_failure_keeps_the_number_and_names_the_container` моделирует отказ через `raise`, чего реальный менеджер не делает, поэтому набор его не видит. Критерий 4 в штатном пути не нарушен (гашение происходит), но это дефект сообщения оператору и тест закрепляет неверную модель отказа. Правка мала: `if stopped is False` + тест с двойником, возвращающим `False`.
- **WR-02 (подтверждено, WARNING).** Идея «очередь пуста = воркер свободен» в `_wake` (`:359-368`) и `_stop_if_idle` (`:418-438`) не видит задачу, уже снятую воркером. Окно до ~90 с (WA) / ~120 с (MAX) на аккаунт и только под `--wake`; условия «active + пустая очередь + до и после» — выбор владельца O-1 (а), и они выполнены как заданы. Остаточный риск: оборванная на середине отправка на одном аккаунте. Критерию не противоречит (формулировка критерия 4 — «гасится после опроса»), но владельцу стоит принять риск осознанно либо запускать `--wake` в окно без рассылок.
- **WR-03 (подтверждено, WARNING; D-16 не нарушен в заявленной формулировке).** Истина плана 20-03 — «контейнер, поднятый чужими руками между списком и подъёмом (`get_container_endpoint` вернул адрес), не гасится» — выполнена (`:371-378`, тест `test_wake_never_stops_a_container_it_did_not_start`). Остаётся окно между `get_container_endpoint` и `start_container` и ветка MAX «409 -> вернуть адрес» (`max_container_manager.py:88-92`), в которых `started=True` ставится для чужого контейнера. Охранник пустой очереди перед остановкой сужает окно: чужой подъём обычно означает задачу в очереди. Узко, но буква D-16 «никогда» без оговорок не гарантирована.
- **WR-04 (подтверждено, WARNING; удобство).** `--limit` берёт первых N кандидатов по `id`; неудачные аккаунты остаются кандидатами, порции не продвигаются (`:182-209`). Критериев не затрагивает; порции по `--account-id` работают. Docstring рекомендует `--limit` в порядке выката — либо добавить `--after-id`, либо поправить текст.
- **IN-01…IN-04** (FloodWait без ожидания; `--wake` без охраны «только из контейнера»; окно между пробой «занят» и `connect()` и невидимость держателей сессии, кроме отправок Celery; гигиена). IN-02 и IN-03 прямо касаются слов цели («разбудить спящий воркер», «разлогинить сессию»): первый срабатывает только при локальном `.env` на боевую базу и явном `--wake`, второй — гонка миллисекунд и внешний замер (RESEARCH A1: 243 пересечения без `AuthKeyDuplicated`). Оба стоит назвать в порядке выката владельца.

### Заметка о записях

`20-VALIDATION.md` во frontmatter хранит `nyquist_compliant: false`, тогда как блок «Approval» сообщает, что флаг выставлен `true`. Не влияет на вердикт; поправить при закрытии фазы.

### Human Verification Required

Нет. Боевой прогон (допущения A1, A3, A4 RESEARCH: короткое подключение TG без `AuthKeyDuplicated`, код 405 у Baileys при `--wake`, отдача номера MAX при восстановлении сессии) — шаг владельца после выката по ответу O-4 (а) и в критерии фазы не входит (`20-CONTEXT.md` §Phase Boundary, `20-VALIDATION.md` Manual-Only).

### Gaps Summary

Пробелов нет. Все пять критериев ROADMAP подтверждены исходниками и прогоном тестов; все четыре требования учтены. Единственная запись номера идёт через единого писателя Фазы 16, гейты номера зелёные без новых изъятий. Рекомендация владельцу до первого `--wake` на бою: разобрать WR-01 (дешёвая правка плюс тест с реальной моделью отказа) и принять или закрыть WR-02/WR-03.

---

_Verified: 2026-11-23_
_Verifier: Claude (gsd-verifier)_

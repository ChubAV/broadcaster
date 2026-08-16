---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Redesign
current_phase: 05
current_phase_name: tarify
status: executing
stopped_at: Phase 05 UI-SPEC approved
last_updated: "2026-08-16T10:57:31.941Z"
last_activity: 2026-08-15
last_activity_desc: Phase 04 UAT round 2 complete — 22/22 passed, 0 issues (04-11, 04-12 и волна WR-01…WR-17)
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 62
  completed_plans: 58
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-13)

**Core value:** Надёжно выполнять периодические рекламные рассылки в группы нескольких мессенджеров по заданному пользователем расписанию.
**Current focus:** Phase 05 — tarify

## Current Position

Phase: 05 (tarify) — EXECUTING
Plan: 1 of 6
Status: Ready to execute
Last activity: 2026-08-15 — Phase 05 execution started

Progress: [█████████████░░░░░░░] 52/52 plans (100%) — Phases 1–4 of 6 complete (67% фаз milestone v2.0)

## Performance Metrics

**Velocity:**

- Total plans completed: 12 (milestone v2.0)
- Average duration: N/A
- Total execution time: N/A

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Интерфейсный фундамент | 13/13 | - | - |
| 2. Объявления и расписания | 15/15 | - | - |
| 3. Группы аккаунта | 12/12 | - | - |
| 04 | 12 | - | - |

**Recent Trend:**

- Тренда пока нет: v1 был ретроспективной документацией без plan-артефактов, v2.0 — первый milestone, исполняемый через GSD.

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- Milestone v2.0: редизайн реализуется на Jinja2 + точечных HTMX/Alpine, без SPA.
- Milestone v2.0: настройка расписаний переезжает в редактор объявления; список расписаний становится сводным с включением и паузой.
- Milestone v2.0: адаптивность — критерий приёмки каждой фазы, а не отдельная фаза.
- Roadmap v2.0: нумерация фаз перезапущена с 1 (`--reset-phase-numbers`), так как фазы v1 были ретроспективной документацией уже отгруженной системы.
- Phase 1: htmx и Alpine вендорены файлами, Tailwind удалён — внешних ресурсов в проекте 0, build-шаг не вводится.
- Phase 1: браузерный `confirm()` заменён собственной панелью подтверждения с настоящей формой POST в 13 местах — путь удаления сохраняется без Alpine.
- Phase 2: долги Фазы 1 (CR-01, CR-02, WR-01/T-10-04) закрыты планом 02-02 — владение `ad_id`/`account_id`, сигнатурная проверка типа загрузки, владение ключом изображения.
- Phase 2: черновик объявления — колонка `ads.status` (миграция `0013`), планировщик пропускает черновики; выкат `0013` на целевую базу — решение владельца.
- Phase 2: автосохранение — create-or-update по `ad_id` на сервере + очередь `this:queue last` на форме; наложение с «Сохранить» удержано именованной регрессией.
- Phase 2: счётчик длины предупреждает (1024 с вложениями / 3686 без), но не блокирует сохранение и не режет текст.
- Phase 3: глобальный раздел «Группы» снесён — группы живут только на экране конкретного аккаунта; старые адреса перенаправляются на `/accounts`.
- Phase 3: GRP-08 (ручное добавление группы) снят, а не реализован — протокола синхронизации одной группы у воркеров нет, вход нёс дыру проверки владения.
- Phase 3: выключенная группа пропускается тихо — без записи в SendLog, `next_run_at` продолжает двигаться.
- Phase 3: повторный запуск синхронизации закрыт внутрипроцессной заявкой `_claim_sync_slot`, а не флагом в БД.
- Phase 3: R-03-09 — раскрытие текста стороннего httpx-исключения в плашке синхронизации принято владельцем как риск severity medium.

### Pending Todos

None.

### Blockers/Concerns

- ⚠️ [Phase 2 → Phase 5] Боевая база остаётся на ревизии `0012`; невыкаченный долг вырос до пяти ревизий: `0013`, `0014`, `0015`, `0016`, `0017`. Решение владельца D-26 (`defer-deploy`, 05-06) — фаза принята на тестовом стенде, выкат отложен. Последствия: колонок `ads.status` и `payments.kind`/`plan` в живой схеме нет, `messages_count` остаётся `NOT NULL`, поэтому подписка на проде не записывается и критерий 1 фазы 5 в проде НЕ выполнен — кнопка оплаты упирается в ошибку записи. `0013_ad_status.py` необратим: его `downgrade` возвращает `ads.is_active` со `server_default=true`, и какое объявление было черновиком, восстановить неоткуда. Guard по `hostname`/`port`/`dbname` и дамп `ads` отработаны в 02-12; round-trip `0017` доказан 7 тестами из 05-02.
- ⚠️ [Phase 5] Подписка на событие `payment.canceled` в кабинете ЮKassa не подтверждена (D-27). Ветка `payment.canceled` из 05-02 зелёная в тестах и непроверенная в проде: пока подписка не включена (Интеграция → HTTP-уведомления, URL на `POST /api/billing/webhook` боевого домена), отменённые платежи навсегда остаются `pending`.
- 🔴 [Phase 5, CR-01] Перед выкатом обязателен `YOOKASSA_WEBHOOK_CLIENT_IP_HEADER=X-Real-IP` в прод-`.env`. **Отказ по умолчанию небезопасен, а не безопасен** (уточнено код-ревью 05-REVIEW.md; в 05-01 режим отказа был описан неверно). `app/config.py:94` даёт значение `""`, в репозитории его никто не задаёт, и пустая настройка уводит в ветку `return client.host` (`app/routes/billing.py:82-83`). Но uvicorn запущен с `--forwarded-allow-ips=*`, из-за чего `always_trust` переписывает `scope["client"]` ЛЕВЫМ элементом `X-Forwarded-For`. Значит `request.client.host` — не адрес nginx-контейнера, а то, что прислал вызывающий: настоящие уведомления проходят И подделанные тоже (`curl -H 'X-Forwarded-For: 77.75.156.11'` минует гард). Правильная логика чтения справа в `_webhook_client_ip` присутствует — прод до неё просто не доходит. Тест `test_without_a_configured_header_the_peer_address_is_used` этого не ловит: он видит только пира тестового транспорта. Правки nginx и docker-compose не нужны. Аварийный выключатель: `YOOKASSA_WEBHOOK_VERIFY_IP=false`.
- 🔴 [Phase 5, CR-02] Защита от двойного зачисления — check-then-act без блокировки: `select(Payment)` без `with_for_update()`, проверка терминального статуса, коммит много позже. Две одновременные доставки видят `pending`, `add_messages` делает `bal.balance += amount` в Python на двух отдельно загруженных строках — зачисление проходит дважды и одна запись теряется; `_extend_subscription` может вставить две строки `Subscription` (уникального индекса по `user_id` нет). Напрямую усиливается через CR-01.
- Brownfield-риск: система живая и покрыта тестами; протоколы отправки Telegram, WhatsApp и MAX трогать нельзя.
- ⚠️ [Phase 3] Браузерных/e2e-тестов в проекте нет: рантайм-поведение Alpine (гард повторной отправки в общем макросе подтверждения, 12 мест) держится на ручной проверке. Регрессия автотестами не поймается.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260803-l8h | обновить версию Baileys до v7.0.0-rc14 | 2026-08-03 | c9c2721 | [260803-l8h-baileys-v7-0-0-rc14](./quick/260803-l8h-baileys-v7-0-0-rc14/) |
| 260803-pb6 | переделать работу с MAX под последнюю версию библиотеки maxapi-python | 2026-08-03 | 0879a75 | [260803-pb6-max-maxapi-python](./quick/260803-pb6-max-maxapi-python/) |
| 260803-rqt | Исправить зависание MAX worker: Redis BLPOP timeout, корректный shutdown, heartbeat health-check контейнера и маскирование REDIS_URL | 2026-08-03 | 3f3b175 | [260803-rqt-max-worker-redis-blpop-timeout-shutdown-](./quick/260803-rqt-max-worker-redis-blpop-timeout-shutdown-/) |
| 260804-8wh | исправить проблемы контейнеров MAX: ложные Redis BLPOP timeout, падение синхронизации групп на CONTACT без contactId и утечку Redis credentials в логах | 2026-08-04 | 61c4121 | [260804-8wh-max-redis-blpop-timeout-contact-contacti](./quick/260804-8wh-max-redis-blpop-timeout-contact-contacti/) |
| 260807-pq7 | issue 35: при удалении аккаунта мессенджера расписания не удаляются, а переходят в статус приостановлено | 2026-08-07 | 95babd3 | [260807-pq7-issue-35](./quick/260807-pq7-issue-35/) |

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| v2.1 | Email-уведомления NOTIF-01..04 | Отложено, вне roadmap v2.0 | 2026-08-08 |
| v2.1 | Прогрев аккаунтов и автопауза WARM-01..02 | Отложено, вне roadmap v2.0 | 2026-08-08 |
| Future scope | Reliability and hardening suggestions в research/SUMMARY.md (v1-era) | Не активно; требует отдельного решения по milestone | 2026-08-03 |
| Phase 2 | CR-01 — владение `ad_id`/`account_id` при постановке в расписание | ✓ Закрыто планом 02-02 (2026-08-11) | 2026-08-10 |
| Phase 2 | CR-02 — клиентский Content-Type при загрузке, SVG на origin хранилища | ✓ Закрыто планом 02-02 (2026-08-11) | 2026-08-10 |
| Phase 2 | WR-01 / T-10-04 — владение ключом изображения при сохранении объявления | ✓ Закрыто планом 02-02 (2026-08-11) | 2026-08-10 |
| Phase 5 | `billing/plans.html` не подключён ни к одному маршруту | Решение о маршруте или переносе содержимого — за Фазой 5 | 2026-08-09 |
| Phase 3 | R-03-09 / T-03-17 — текст стороннего httpx-исключения в плашке ошибки синхронизации | Принято владельцем как риск severity medium (2026-08-13); сужение текста — при желании отдельной задачей | 2026-08-13 |

## Session Continuity

Last session: 2026-08-16T09:50:33.767Z
Stopped at: Phase 05 UI-SPEC approved
Resume file: .planning/phases/05-tarify/05-UI-SPEC.md

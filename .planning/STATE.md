---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Redesign
current_phase: 5
current_phase_name: Тарифы
status: planning
stopped_at: Phase 5 not started
last_updated: "2026-08-15T13:45:00.000Z"
last_activity: 2026-08-15
last_activity_desc: "Phase 04 UAT round 2 complete — 22/22 passed, 0 issues (04-11, 04-12 и волна WR-01…WR-17)"
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 52
  completed_plans: 52
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-13)

**Core value:** Надёжно выполнять периодические рекламные рассылки в группы нескольких мессенджеров по заданному пользователем расписанию.
**Current focus:** Phase 05 — Тарифы

## Current Position

Phase: 5 — Тарифы
Plan: Not started
Status: Ready to plan
Last activity: 2026-08-15 — Phase 04 UAT раунд 2 принят (22/22), фаза закрыта окончательно

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

- ⚠️ [Phase 2] Целевая база остаётся на ревизии `0012` — колонки `ads.status` в живой схеме нет. Выкат `0013` — решение владельца (guard по `hostname`/`port`/`dbname` и дамп `ads` отработаны в 02-12); до выката черновики не наблюдаемы в проде.
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

Last session: 2026-08-13T17:07:20.817Z
Stopped at: Phase 4 context gathered
Resume file: .planning/phases/04-dashbord-i-istoriya/04-CONTEXT.md

---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Redesign
status: planning
last_updated: "2026-08-09T00:00:00.000Z"
last_activity: 2026-08-09
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-08)

**Core value:** Надёжно выполнять периодические рекламные рассылки в группы нескольких мессенджеров по заданному пользователем расписанию.
**Current focus:** Phase 1 — Интерфейсный фундамент (дизайн-система, новый шелл и навигация из макета).

## Current Position

Phase: 1 of 6 (Интерфейсный фундамент)
Plan: — (phase not planned yet)
Status: Ready to plan
Last activity: 2026-08-09 — Roadmap v2.0 создан, нумерация фаз начата заново с 1

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 0 (milestone v2.0 только начат)
- Average duration: N/A
- Total execution time: N/A

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Интерфейсный фундамент | Not planned | N/A | N/A |

**Recent Trend:**

- Тренда пока нет: v1 был ретроспективной документацией без plan-артефактов, v2.0 — первый milestone, исполняемый через GSD.

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- Milestone v2.0: редизайн реализуется на Jinja2 + точечных HTMX/Alpine, без SPA.
- Milestone v2.0: настройка расписаний переезжает в редактор объявления; список расписаний становится сводным с включением и паузой.
- Milestone v2.0: адаптивность — критерий приёмки каждой фазы, а не отдельная фаза.
- Roadmap v2.0: нумерация фаз перезапущена с 1 (`--reset-phase-numbers`), так как фазы v1 были ретроспективной документацией уже отгруженной системы.

### Pending Todos

None.

### Blockers/Concerns

- Счётчик в REQUIREMENTS.md указывал 38 требований v2.0, фактических REQ-ID — 39. Счётчики исправлены на 39; смысловых требований не добавлялось и не удалялось.
- Фаза 1 — жёсткая зависимость всех остальных фаз: пока новый шелл и компоненты не готовы, остальные фазы планировать можно, а исполнять нет.
- ADS-04 (черновик объявления) требует миграции схемы: поля `status` у `Ad` сейчас нет.
- Brownfield-риск: система живая и покрыта тестами; протоколы отправки Telegram, WhatsApp и MAX трогать нельзя.

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

## Session Continuity

Last session: 2026-08-09
Stopped at: Создан roadmap v2.0 Redesign — 6 фаз, 39 требований распределены, traceability заполнена.
Resume file: None

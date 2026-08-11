---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Redesign
current_phase: 02
current_phase_name: obyavleniya-i-raspisaniya
status: executing
stopped_at: Phase 2 UI-SPEC approved
last_updated: "2026-08-11T04:51:14.612Z"
last_activity: 2026-08-11
last_activity_desc: Phase 02 execution started
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 25
  completed_plans: 20
  percent: 17
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-10)

**Core value:** Надёжно выполнять периодические рекламные рассылки в группы нескольких мессенджеров по заданному пользователем расписанию.
**Current focus:** Phase 02 — obyavleniya-i-raspisaniya

## Current Position

Phase: 02 (obyavleniya-i-raspisaniya) — EXECUTING
Plan: 1 of 12
Status: Executing Phase 02
Last activity: 2026-08-11 — Phase 02 execution started

Progress: [████████████████████] 13/13 plans (100%) — Phase 1 of 6 complete (17% фаз milestone v2.0)

## Performance Metrics

**Velocity:**

- Total plans completed: 13 (milestone v2.0 только начат)
- Average duration: N/A
- Total execution time: N/A

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Интерфейсный фундамент | 13/13 | - | - |

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
- Phase 1: CR-01, CR-02 и WR-01/T-10-04 отнесены в Фазу 2 (решение UAT 2026-08-10); T-10-04 принята как риск R-01 в `01-SECURITY.md`.

### Pending Todos

None.

### Blockers/Concerns

- Счётчик в REQUIREMENTS.md указывал 38 требований v2.0, фактических REQ-ID — 39. Счётчики исправлены на 39; смысловых требований не добавлялось и не удалялось.
- ⚠️ [Phase 1] Гейт код-ревью открыт: `01-REVIEW.md` — `status: issues_found`, `critical: 2`. CR-01 (владение `ad_id`/`account_id` в `app/pages/schedules.py:204-213,314-315`), CR-02 (клиентский Content-Type в `app/routes/uploads.py:48-52`) и WR-01/T-10-04 (владение ключом изображения в `app/pages/ads.py:133-135,183-187`) перенесены в Фазу 2. Фаза 01 отгружена с этими находками открытыми (решение 2026-08-10): ship-гейты GSD — security (`threats_open: 0`) и broken-windows (`open_count: 0`) — оба прошли, код-ревью ship-гейтом не является. **Починить в Фазе 2 до релиза.**
- ⚠️ [Phase 1] `/ads/new` и `/ads/{id}/edit` не рендерятся ни одним тестом суиты — глобал `s3_public_url` в `app/pages/common.py:38` собирает `Settings()` в обход подмены зависимостей. Дефект на базовом коммите фазы, не внесён перевёрсткой; развилка ADS-07.
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
| Phase 2 | CR-01 — владение `ad_id`/`account_id` при постановке в расписание | Решение UAT: чинить в Фазе 2 | 2026-08-10 |
| Phase 2 | CR-02 — клиентский Content-Type при загрузке, SVG на origin хранилища | Решение UAT: чинить в Фазе 2 | 2026-08-10 |
| Phase 2 | WR-01 / T-10-04 — владение ключом изображения при сохранении объявления | Принята как риск R-01 в `01-SECURITY.md`; чинить в Фазе 2 | 2026-08-10 |
| Phase 5 | `billing/plans.html` не подключён ни к одному маршруту | Решение о маршруте или переносе содержимого — за Фазой 5 | 2026-08-09 |

## Session Continuity

Last session: 2026-08-10T06:02:53.672Z
Stopped at: Phase 2 UI-SPEC approved
Resume file: .planning/phases/02-obyavleniya-i-raspisaniya/02-UI-SPEC.md

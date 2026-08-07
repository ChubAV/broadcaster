# Broadcaster

## What This Is

Broadcaster — действующая SaaS-платформа для малого бизнеса и маркетинговых агентств, которая автоматизирует периодическую отправку рекламных объявлений в группы мессенджеров. Пользователь подключает аккаунты Telegram, WhatsApp или MAX, синхронизирует группы, создаёт объявления и расписания, после чего платформа выполняет рассылки и сохраняет результаты.

## Core Value

Надёжно выполнять периодические рекламные рассылки в группы нескольких мессенджеров по заданному пользователем расписанию.

## Business Context

- **Customer**: малый бизнес и маркетинговые агентства
- **Revenue model**: SaaS-тарифы Free, Basic и Pro с лимитами использования и пополняемым балансом сообщений
- **Success metric**: доля запланированных отправок, успешно выполненных в заданное время
- **Strategy notes**: текущее состояние продукта зафиксировано по реализации и README репозитория

## Requirements

### Validated

- ✓ Пользователь может зарегистрироваться, подтвердить email, войти по JWT и восстановить пароль — existing
- ✓ Пользователь может создавать и редактировать рекламные объявления, включая изображения в S3/MinIO — existing
- ✓ Пользователь может подключать Telegram-аккаунты через Telethon userbot — existing
- ✓ Пользователь может подключать WhatsApp-аккаунты через отдельные Baileys-воркеры — existing
- ✓ Пользователь может подключать MAX-аккаунты через отдельные pymax-воркеры — existing
- ✓ Пользователь может синхронизировать и выбирать группы подключённых мессенджеров — existing
- ✓ Пользователь может задавать периодические расписания по дням недели, времени и своей таймзоне — existing
- ✓ Celery автоматически обнаруживает наступившие расписания и распределяет отправки — existing
- ✓ Платформа сохраняет журнал отправок со статусами и снапшотами контента — existing
- ✓ Тарифы и баланс сообщений ограничивают доступное использование платформы — existing
- ✓ Администратор может управлять пользователями, подписками и просматривать операционные данные — existing
- ✓ Система предоставляет метрики Prometheus, дашборды Grafana и централизованные логи Loki — existing

### Active

(Новых требований пока нет — текущая цель состоит в фиксации реализованного состояния.)

### Out of Scope

(Явные исключения пока не определены.)

## Context

- Проект уже реализован и покрыт автоматическими тестами; это brownfield-система, а не новая разработка с нуля.
- Основное приложение построено на Python 3.12, FastAPI, асинхронном SQLAlchemy и PostgreSQL.
- Периодические и фоновые задачи выполняются Celery с Redis.
- Web UI отрисовывается сервером через Jinja2.
- Telegram интегрирован как userbot через Telethon и пул сессий.
- WhatsApp использует Baileys и динамический контейнер `wa_worker` на каждый аккаунт; legacy `wa_bridge` сохранён как справочная реализация.
- MAX использует отдельный Python/FastAPI `max_worker` на базе pymax и динамические контейнеры аккаунтов.
- Изображения объявлений хранятся в S3-совместимом хранилище.
- Развёртывание предусмотрено через Docker Compose и Nginx; наблюдаемость обеспечивают Prometheus, Grafana и Loki.
- Тесты используют pytest, asyncio, httpx и SQLite in-memory.

## Constraints

- **Tech stack**: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Celery и Redis — установленная архитектура действующего продукта
- **Messenger dependencies**: Telethon, Baileys и pymax зависят от внешних протоколов и ограничений соответствующих платформ
- **Deployment**: основное приложение и account-specific воркеры должны работать в Docker-окружении — текущая модель эксплуатации
- **Compatibility**: изменения не должны нарушать существующие Telegram, WhatsApp и MAX сценарии — продукт уже поддерживает все три канала
- **Reliability**: отправки, история и биллинг должны оставаться согласованными при фоновой и повторной обработке задач — основная ценность продукта зависит от надёжности расписаний

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Использовать Telegram userbot через Telethon | Отправка выполняется от подключённого пользовательского аккаунта | ✓ Good |
| Выделять WhatsApp и MAX аккаунты в отдельные динамические контейнеры | Изоляция сессий и жизненного цикла каждого аккаунта | — Pending |
| Выполнять расписания через Celery и Redis | Отделение фоновой отправки от web-приложения и поддержка периодических задач | ✓ Good |
| Использовать серверный Jinja2 UI | Единое FastAPI-приложение без отдельного SPA-фронтенда | — Pending |
| Применять тарифы и баланс сообщений | Контроль потребления и монетизация SaaS | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-03 after initialization*

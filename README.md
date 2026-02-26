# Broadcaster

SaaS-платформа для планирования и отправки рекламных объявлений в группы мессенджеров. Поддерживает Telegram (userbot через Telethon) и WhatsApp (через Baileys bridge).

## Features

- **Multi-messenger** -- Telegram userbot (Telethon) и WhatsApp (Baileys, чистый WebSocket)
- **Управление объявлениями** -- создание, редактирование, загрузка изображений (S3/MinIO)
- **Управление группами** -- подключение и синхронизация групп мессенджеров
- **Планировщик** -- гибкое расписание по дням недели и времени с автоматическим расчётом следующего запуска
- **Автоматическая отправка** -- Celery Beat проверяет расписания, Celery workers рассылают сообщения
- **История и статистика** -- полный журнал отправок со снапшотами контента
- **Биллинг** -- тарифы Free / Basic / Pro с лимитами на объявления, группы и отправки
- **Админ-панель** -- управление пользователями и подписками
- **Мониторинг** -- Prometheus метрики + Grafana дашборды + Loki логи
- **Поддержка таймзон** -- индивидуальная таймзона в профиле пользователя
- **JWT-аутентификация** -- регистрация и вход
- **Web UI** -- серверный рендеринг на Jinja2

## Tech Stack

- **Python 3.12** + [uv](https://docs.astral.sh/uv/) для управления зависимостями
- **FastAPI** -- async web framework
- **SQLAlchemy 2.0** (async) -- ORM с PostgreSQL (asyncpg)
- **Alembic** -- миграции БД
- **Celery + Redis** -- очередь задач для отложенных отправок
- **Jinja2** -- серверные HTML-шаблоны
- **Docker Compose** -- оркестрация (dev / prod / monitoring стеки)
- **WhatsApp Bridge** -- Node.js + Express + Baileys (чистый WebSocket, без Chromium)
- **Telethon** -- Telegram userbot с QR-авторизацией
- **S3/MinIO** -- хранилище изображений
- **Prometheus + Grafana + Loki** -- мониторинг и логирование
- **Nginx** -- reverse proxy с Let's Encrypt SSL

## Quick Start (Docker Compose)

1. Клонировать репозиторий:
   ```bash
   git clone <repo-url>
   cd broadcaster
   ```

2. Создать `.env` файл (см. `.env.example`):
   ```env
   DATABASE_URL=postgresql+asyncpg://broadcaster:broadcaster@db:5432/broadcaster
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=change-me-to-a-random-string
   TELEGRAM_API_ID=...
   TELEGRAM_API_HASH=...
   ```

3. Запустить все сервисы:
   ```bash
   docker compose up -d
   ```

4. Открыть http://localhost:8000

### Development Mode

Dev-режим с hot-reload и debug-логированием:

```bash
just dev
# или
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Development Setup (Local)

1. Установить [uv](https://docs.astral.sh/uv/getting-started/installation/) и [just](https://github.com/casey/just).

2. Установить зависимости:
   ```bash
   just sync
   ```

3. Поднять PostgreSQL и Redis:
   ```bash
   docker compose up db redis -d
   ```

4. Создать `.env` файл:
   ```env
   DATABASE_URL=postgresql+asyncpg://broadcaster:broadcaster@localhost:5432/broadcaster
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=dev-secret-key
   ```

5. Применить миграции:
   ```bash
   just upgrade
   ```

6. Запустить приложение:
   ```bash
   just run
   ```

7. В отдельных терминалах запустить Celery:
   ```bash
   just worker
   just beat
   # или одной командой:
   just celery
   ```

8. Запустить тесты:
   ```bash
   just test
   ```

## Just Commands

Проект использует [just](https://github.com/casey/just) как command runner. `just` -- список всех команд.

| Command | Description |
|---------|-------------|
| `just run` | Dev-сервер с hot-reload |
| `just test` | Запуск тестов |
| `just test-cov` | Тесты с покрытием |
| `just dev` | Docker dev-окружение |
| `just down` | Остановить Docker-контейнеры |
| `just migrate "msg"` | Создать Alembic-миграцию |
| `just upgrade` | Применить миграции |
| `just worker` | Celery worker |
| `just beat` | Celery beat |
| `just celery` | Worker + beat вместе |
| `just sync` | Синхронизировать uv-окружение |
| `just add <pkg>` | Добавить зависимость |
| `just prod-start` | Запустить prod |
| `just prod-stop` | Остановить prod |
| `just prod-deploy` | Деплой (build + deploy) |
| `just prod-hard-deploy` | Деплой с --no-cache |
| `just prod-logs [svc]` | Логи prod-сервисов |
| `just monitoring-start` | Запустить стек мониторинга |
| `just monitoring-down` | Остановить мониторинг |

## Project Structure

```
broadcaster/
├── app/
│   ├── config.py              # Pydantic settings (@lru_cache singleton)
│   ├── database.py            # SQLAlchemy async engine/session
│   ├── dependencies.py        # FastAPI dependencies (auth, db)
│   ├── exceptions.py          # Custom exceptions + global handlers
│   ├── constants.py           # App-wide constants
│   ├── logging_config.py      # Structlog configuration
│   ├── middleware.py          # FastAPI middleware
│   ├── metrics.py             # Prometheus metrics
│   ├── main.py                # App factory
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── ad.py
│   │   ├── group.py
│   │   ├── messenger_account.py
│   │   ├── schedule.py
│   │   ├── send_log.py
│   │   ├── subscription.py
│   │   └── telegram_auth_session.py
│   ├── repositories/          # Data access layer
│   │   ├── base.py            # Generic BaseRepository[T]
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── ad.py
│   │   ├── group.py
│   │   ├── schedule.py
│   │   └── send_log.py
│   ├── routes/                # FastAPI API routers
│   │   ├── auth.py
│   │   ├── ads.py
│   │   ├── accounts.py
│   │   ├── groups.py
│   │   ├── schedules.py
│   │   ├── history.py
│   │   ├── billing.py
│   │   └── uploads.py
│   ├── pages/                 # Server-rendered HTML pages
│   │   ├── common.py          # Shared utilities (get_user_from_cookie)
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── ads.py
│   │   ├── accounts.py
│   │   ├── groups.py
│   │   ├── schedules.py
│   │   ├── history.py
│   │   ├── billing.py
│   │   ├── admin.py
│   │   └── profile.py
│   ├── services/
│   │   ├── auth_service.py    # Password hashing, JWT
│   │   ├── billing_service.py # Plan limits and usage checks
│   │   ├── billing_cache.py   # Billing cache layer
│   │   ├── schedule_service.py # Next-run computation
│   │   ├── messenger_factory.py # Messenger adapter factory
│   │   └── s3.py              # S3/MinIO image storage
│   ├── messengers/            # Messenger adapters
│   │   ├── base.py            # Abstract base class
│   │   ├── telegram_user.py   # Telegram userbot (Telethon)
│   │   ├── telegram_pool.py   # Telegram session pool
│   │   └── whatsapp.py        # WhatsApp via Baileys bridge
│   ├── application/           # DDD use cases
│   │   ├── accounts/          # Account management
│   │   └── scheduling/        # Scheduling logic
│   ├── domain/                # Domain interfaces
│   │   └── repositories.py
│   ├── infrastructure/        # Infrastructure implementations
│   │   └── uow.py            # Unit of Work
│   ├── worker/                # Celery tasks
│   │   ├── celery_app.py      # Celery configuration
│   │   ├── tasks.py           # Schedule checker and send tasks
│   │   └── wa_consumer.py     # WhatsApp webhook consumer
│   └── templates/             # Jinja2 HTML templates (21 files)
├── wa_bridge/                 # WhatsApp bridge (Node.js + Baileys)
│   ├── index.js               # Express server with Baileys integration
│   ├── Dockerfile
│   └── package.json
├── monitoring/                # Monitoring stack configs
│   ├── prometheus.yml
│   ├── loki.yml
│   ├── promtail.yml
│   └── grafana/               # Grafana provisioning & dashboards
├── nginx/                     # Reverse proxy configs
│   ├── nginx.conf.template    # HTTPS template
│   └── nginx-http.conf.template
├── scripts/
│   └── cleanup_schedules.py   # Schedule maintenance script
├── tests/                     # pytest suite (52 files)
├── docker-compose.yml         # Base stack (web, celery, redis, db, wa-bridge)
├── docker-compose.dev.yml     # Dev overrides (hot-reload, debug)
├── docker-compose.prod.yml    # Production (+ nginx, certbot)
├── docker-compose.monitoring.yml # Prometheus + Grafana + Loki
├── justfile                   # Task runner commands
├── Dockerfile                 # Python 3.12 + uv image
├── entrypoint.sh              # Docker entrypoint (runs migrations)
└── pyproject.toml             # Project metadata and dependencies
```

## Docker Services

### Base stack (`docker-compose.yml`)
- **web** -- FastAPI app (port 8000)
- **celery-worker-telegram** -- Celery workers для Telegram (2 replicas)
- **celery-worker-whatsapp** -- Celery workers для WhatsApp (2 replicas)
- **celery-worker-default** -- Celery worker для общих задач
- **celery-beat** -- Celery Beat scheduler
- **wa-bridge** -- WhatsApp Baileys bridge (port 3000, 512MB)
- **db** -- PostgreSQL 16
- **redis** -- Redis
- **flower** -- Celery monitoring (port 5555)

### Production (`docker-compose.prod.yml`)
Adds: **nginx** (80/443), **certbot** (Let's Encrypt SSL)

### Monitoring (`docker-compose.monitoring.yml`)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Loki + Promtail**: log aggregation

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход, получение JWT |
| GET/POST | `/api/ads` | Список / создание объявлений |
| GET/PUT/DELETE | `/api/ads/{id}` | CRUD объявления |
| GET/POST | `/api/accounts` | Список / создание аккаунтов |
| DELETE | `/api/accounts/{id}` | Удаление аккаунта |
| GET | `/api/accounts/{id}/status` | Статус подключения |
| GET/POST | `/api/groups` | Список / создание групп |
| DELETE | `/api/groups/{id}` | Удаление группы |
| PATCH | `/api/groups/{id}/toggle` | Переключение активности |
| GET/POST | `/api/schedules` | Список / создание расписаний |
| PUT/DELETE | `/api/schedules/{id}` | Обновление / удаление расписания |
| POST | `/api/schedules/{id}/toggle` | Переключение активности |
| GET | `/api/history` | История отправок |
| GET | `/api/history/stats` | Статистика |
| GET | `/api/billing/plans` | Тарифные планы |
| GET | `/api/billing/usage` | Текущее использование и лимиты |
| POST | `/api/uploads/image` | Загрузка изображения |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

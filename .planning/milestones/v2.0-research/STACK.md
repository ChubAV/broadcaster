# Stack Research

**Domain:** Brownfield SaaS for scheduled multi-messenger advertising delivery
**Researched:** 2026-08-03
**Confidence:** MEDIUM

## Recommended Stack

This milestone should preserve the implemented stack. It already maps well to the workload: a transactional web application schedules durable work in PostgreSQL, then isolated workers perform network-bound sends. Upgrade within these major lines only behind contract and integration tests; do not use the documentation exercise to re-platform a working product.

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 (required) | Main application and MAX worker runtime | The repository baseline; a single modern Python runtime supports FastAPI, async I/O, Celery and the test suite. Keep it pinned as the deployed compatibility floor. |
| FastAPI | 0.129.0 (locked) | HTTP API and server-rendered application entry point | A good fit for async HTTP integrations and Pydantic-backed request validation. FastAPI explicitly supports `async def` endpoints for awaitable dependencies and is deployment-neutral, matching the existing Compose deployment. [FastAPI async docs](https://fastapi.tiangolo.com/async/) [MEDIUM] |
| SQLAlchemy async + asyncpg | 2.0.46 + 0.31.0 (locked) | ORM, transactions and PostgreSQL asynchronous driver | Retain one `AsyncSession` per request/task unit of work. SQLAlchemy documents `create_async_engine("postgresql+asyncpg://…")` and `async_sessionmaker`; this is the correct durable state boundary for schedules, billing and send logs. [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html) [MEDIUM] |
| PostgreSQL | 16-alpine image | Source of truth for users, ads, schedules, billing and send logs | Use it for transactions, constraints and audit history. PostgreSQL remains the only authority for send state; neither Redis nor messenger workers should become a competing store of record. |
| Celery + Redis | 5.6.2 + Redis 7-alpine | Periodic dispatch, queue routing and retryable background work | The current split between Beat, Telegram workers and default workers is appropriate. Celery 5.6 classifies Redis as a stable broker/result backend, but cautions that it is for small, rapid messages and memory/persistence need deliberate handling. [Celery brokers](https://docs.celeryq.dev/en/latest/getting-started/backends-and-brokers/index.html) [MEDIUM] |
| Jinja2 | 3.1.6 (locked) | Server-rendered web UI | Keep the integrated UI layer for this brownfield application. It avoids a separate frontend runtime and deployment surface while existing templates and FastAPI routes remain the product UI. |
| Docker Compose + Nginx | Compose; nginx:alpine | Repeatable multi-service deployment and TLS/reverse proxy | Preserve Compose as the operational composition boundary. Existing health-gated `depends_on` for PostgreSQL and Redis reflects Docker guidance: `service_healthy` waits for readiness, whereas normal startup ordering does not. [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) [MEDIUM] |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Telethon | 1.42.0 (locked; 1.x line) | Telegram MTProto userbot, QR/session login, group discovery and sends | Keep behind the Telegram adapter/pool. Persist sessions as secrets and convert `FloodWait`/permission/network failures to explicit send outcomes and retry policies. Telethon exposes a wait value and a configurable flood-sleep threshold. [Telethon errors](https://docs.telethon.dev/en/stable/concepts/errors.html) [MEDIUM] |
| `@whiskeysockets/baileys` | 7.0.0-rc.9 (locked in `wa_worker`) | WhatsApp Web multi-device client in a dedicated Node worker | Keep a worker/container per account, with Redis only as the command channel. Persist every credential/key update to a protected mounted volume or encrypted external store. Baileys says its multi-file helper is an example, not production storage, and session material is long-lived credential material. [Baileys README](https://github.com/WhiskeySockets/Baileys/blob/master/README.md) [MEDIUM] [Baileys security guidance](https://github.com/WhiskeySockets/Baileys/security) [MEDIUM] |
| `maxapi-python` / `pymax` | `>=1.2.0` in `max_worker` — **pin an exact tested release** | MAX account session client inside the dedicated Python/FastAPI worker | Retain the container boundary and its HTTP/Redis protocol. This is a third-party user-session wrapper, distinct from MAX’s official Bot API library; treat it as a volatile integration and test QR, reconnect, group sync and send flows before every upgrade. The published package currently requires Python 3.10+; ecosystem evidence is materially thinner than the core stack. [PyPI package](https://pypi.org/project/maxapi-python/1.2.5/) [MEDIUM] |
| aiobotocore | 3.1.3 (locked) | Async S3-compatible advertisement-image storage | Retain it rather than adding synchronous Boto3 to async request paths. Use one configured endpoint client and short-lived signed access where direct browser access is required; AWS documents temporary access through presigned URLs and custom endpoint support is available through the SDK client configuration. [Boto3 presigned URLs](https://docs.aws.amazon.com/boto3/latest/guide/s3-presigned-urls.html) [MEDIUM] [S3 examples](https://docs.aws.amazon.com/boto3/latest/guide/s3-examples.html) [MEDIUM] |
| Alembic | 1.18.4 (locked) | Versioned database migrations | Use for every schema change; run migrations once as a deployment operation, never opportunistically in each web/worker replica. |
| Pydantic Settings + `python-jose` + Passlib/bcrypt | 2.13.0 + 3.5.0 + 1.7.4 / `<4.1` | Typed configuration, JWT handling and password hashing | Preserve current auth/configuration choices. Treat the bcrypt upper bound as a compatibility pin to revisit only through an explicit security-maintenance change. |
| Prometheus instrumentator + Grafana/Loki/Promtail | 7.1.0; Compose images currently `latest` | Metrics, dashboards and centralized logs | Keep telemetry separate from the request/dispatch path. Replace floating monitoring image tags with tested versions when the deployment baseline is next changed. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Dependency locking and execution | Use `uv sync` for reproducible local environments and commit the existing `uv.lock`; install no dependencies ad hoc in production containers. |
| pytest + pytest-asyncio + HTTPX | Async unit/integration tests | Maintain SQLite in-memory coverage, but run PostgreSQL/Redis/worker smoke tests for transaction, queue and migration changes because SQLite cannot reproduce all production behavior. |
| Docker Compose | Local and production service orchestration | Keep database/Redis healthchecks and test `docker compose config` after compose changes. Do not infer readiness solely from container start. |
| Flower | Celery observability | Keep it restricted to trusted operators; it is an operational console, not a public application endpoint. |

## Installation

This is a documentation milestone: the recommendation is to reproduce the locked implementation, not install replacements.

```bash
# Python application and development dependencies
uv sync

# Run the existing verification suite
uv run pytest tests/ -v

# WhatsApp worker dependencies (only when its lockfile/package manifest changes)
cd wa_worker && npm ci

# Compose deployment uses the repository's existing manifests
docker compose up --build
```

For `max_worker`, create and lock a dedicated Python environment from `max_worker/requirements.txt` before the next code change; its current lower-bound-only requirements are not reproducible enough for an external-protocol worker.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| FastAPI + Jinja2 | SPA frontend plus independent API/BFF | Only if a validated product requirement needs rich client-side interaction that the server-rendered UI cannot provide. It is not justified by state documentation. |
| SQLAlchemy async + asyncpg + PostgreSQL | Django ORM / synchronous ORM layer | Only during a deliberate rewrite with product value that offsets migration risk. The existing async FastAPI and repositories already fit SQLAlchemy. |
| Celery + Redis | RabbitMQ + Celery | Consider only if large/high-throughput broker payloads or stronger broker operations become a measured bottleneck. Celery notes RabbitMQ handles larger messages better; continue sending identifiers, never ad/image payloads, through Redis today. [Celery brokers](https://docs.celeryq.dev/en/latest/getting-started/backends-and-brokers/index.html) [MEDIUM] |
| Account-specific Baileys/MAX containers | One shared process for all external accounts | Only if a future managed connection service provides equivalent isolation and recovery. Current separate containers appropriately isolate QR/session state and crashes. |
| Telethon userbot | Telegram Bot API | Only for new capabilities that can operate as a bot. It cannot be substituted where the business flow requires the connected user account's groups and permissions. |
| aiobotocore + S3-compatible storage | Database BLOBs / local container filesystem | Only for tiny, non-user assets. Advertisement images need durable, shareable storage independent of web and worker container lifecycles. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| In-process FastAPI background tasks for scheduled sends | They do not survive web-process restart and offer no durable retry/audit boundary for billed sends. | Celery task dispatch with PostgreSQL-backed idempotency and send logs. |
| Multiple Celery Beat replicas for the same schedule | Celery warns that multiple schedulers can enqueue duplicate periodic tasks. | One active Beat leader; make dispatcher/send tasks idempotent and use a lock where overlap is possible. [Celery periodic tasks](https://docs.celeryq.dev/en/v5.4.0/userguide/periodic-tasks.html) [MEDIUM] |
| Redis as the system of record or a carrier for media payloads | Redis broker messages are best kept small and Redis result persistence is memory-bound. | PostgreSQL for state/audit, S3 for media, Redis for task identifiers and ephemeral coordination. [Celery Redis](https://docs.celeryq.dev/en/v5.6.2/getting-started/backends-and-brokers/redis.html) [MEDIUM] |
| Baileys `useMultiFileAuthState` as a production credential store or embedding sessions in images | The maintainers explicitly describe it as a guide and credential contents can hijack an account. | Account-scoped protected volume or encrypted store; persist credentials on every update and never log or commit them. [Baileys README](https://github.com/WhiskeySockets/Baileys/blob/master/README.md) [MEDIUM] |
| Floating `latest` images and unpinned MAX worker dependencies | They make incident rollback and protocol integration debugging non-reproducible. | Exact tested image/package versions plus scheduled upgrade validation. |
| Telethon 2.0 alpha migration during routine maintenance | The app is built on 1.x and the documented 2.0 API/error model differs; it needs a dedicated migration plan. | Keep the tested 1.x line until a compatibility spike and integration suite pass. |

## Stack Patterns by Variant

**If a send is due:**
- Read/claim it transactionally in PostgreSQL, enqueue only immutable identifiers and snapshot references, then let the messenger-specific worker perform the external operation.
- Because database state remains authoritative while retries and redelivery are expected with external protocols.

**If one messenger account fails or needs re-authentication:**
- Mark that account/send outcome without stopping other accounts, retain the account-scoped worker/session volume, and expose a reconnection/QR recovery state.
- Because Telegram, WhatsApp and MAX have independent credentials, rate limits and protocol failures.

**If deployment starts or an infrastructure dependency restarts:**
- Gate Compose dependencies with healthchecks and keep application reconnect/retry bounds.
- Because Compose dependency ordering alone does not establish database or Redis readiness. [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) [MEDIUM]

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.12 | FastAPI 0.129.0, SQLAlchemy 2.0.46, asyncpg 0.31.0, Celery 5.6.2 | Exact versions are confirmed in `uv.lock`; retain the lockfile as the implementation baseline. |
| SQLAlchemy 2.0.46 | PostgreSQL 16 via asyncpg 0.31.0 | Uses `postgresql+asyncpg://`; test migrations and prepared-statement/cache behavior against PostgreSQL, not only SQLite. [SQLAlchemy PostgreSQL dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) [MEDIUM] |
| Celery 5.6.2 | Redis 7 | Current production pairing. Set visibility/retry/timeout values against the longest bounded external send; Redis transport's documented default visibility timeout is one hour. [Celery Redis](https://docs.celeryq.dev/en/v5.6.2/getting-started/backends-and-brokers/redis.html) [MEDIUM] |
| Telethon 1.42.0 | Python 3.12 | Stay on the current 1.x API until an intentional v2 migration; validate account authorization, flood waits and session serialization. |
| Node 20 | Baileys 7.0.0-rc.9, ioredis 5.4, Express 4.18 | Present worker combination. Baileys is pre-release and the upstream repository now publishes later RCs, so upgrade only from an exact tagged release after account-flow tests. [Baileys releases](https://github.com/WhiskeySockets/Baileys/releases) [MEDIUM] |
| Python 3.12 | `maxapi-python` / `pymax` | The package advertises Python 3.10+; lock an exact version and exercise the worker image rather than assuming compatibility from its lower bound. [PyPI package](https://pypi.org/project/maxapi-python/1.2.5/) [MEDIUM] |

## Sources

- Local implementation evidence: [`PROJECT.md`](../PROJECT.md), `pyproject.toml`, `uv.lock`, `docker-compose.yml`, `wa_worker/package.json`, and `max_worker/requirements.txt` — exact deployed/locked choices [HIGH].
- [FastAPI async documentation](https://fastapi.tiangolo.com/async/) and [deployment documentation](https://fastapi.tiangolo.com/deployment/) — async and deployment model [MEDIUM].
- [SQLAlchemy asyncio documentation](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html) and [PostgreSQL dialect documentation](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) — async session/driver behavior [MEDIUM].
- [Celery brokers](https://docs.celeryq.dev/en/latest/getting-started/backends-and-brokers/index.html), [Redis transport](https://docs.celeryq.dev/en/v5.6.2/getting-started/backends-and-brokers/redis.html), and [periodic tasks](https://docs.celeryq.dev/en/v5.4.0/userguide/periodic-tasks.html) — queue, Redis and Beat constraints [MEDIUM].
- [Telethon error handling](https://docs.telethon.dev/en/stable/concepts/errors.html), [Baileys README](https://github.com/WhiskeySockets/Baileys/blob/master/README.md), and [Baileys security guidance](https://github.com/WhiskeySockets/Baileys/security) — external messenger integration handling [MEDIUM].
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) and [Boto3 S3 presigned URLs](https://docs.aws.amazon.com/boto3/latest/guide/s3-presigned-urls.html) — operational dependency and S3 access practices [MEDIUM].

---
*Stack research for: Broadcaster*
*Researched: 2026-08-03*

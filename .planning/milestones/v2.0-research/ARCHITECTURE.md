# Architecture Research

**Domain:** Multi-messenger scheduled advertising SaaS (brownfield current state)
**Researched:** 2026-08-03
**Confidence:** HIGH for the implemented topology; MEDIUM for general reliability guidance.

## Standard Architecture

### System Overview

Broadcaster is a modular monolith for the control plane with asynchronous delivery workers. PostgreSQL is the source of business truth; Redis is both Celery broker/result backend and the transport for account-specific WhatsApp/MAX work. The integration boundary is deliberately different by messenger: Telegram is handled in the Python Celery worker using Telethon, while WhatsApp and MAX each get an isolated, on-demand container per account.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Edge and control plane                                                   │
│ Nginx → FastAPI (routes + Jinja pages) → services/application use cases │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│ Stateful core                                                            │
│ PostgreSQL: users, accounts, groups, ads, schedules, balances, send logs │
│ S3-compatible storage: ad image objects                                  │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ due schedules / dispatch payloads
┌──────────────────────────────────▼──────────────────────────────────────┐
│ Orchestration                                                            │
│ Celery Beat → default worker (schedule scan, worker management, results)│
│ Redis → Celery telegram queue and wa:/max: per-account queues/results   │
└───────────────┬──────────────────────────┬──────────────────────────────┘
                │                          │
        ┌───────▼────────┐         ┌───────▼─────────────────────┐
        │ Telegram queue │         │ One dynamic worker/account  │
        │ Telethon send  │         │ WhatsApp Baileys / MAX pymax │
        └───────┬────────┘         └───────┬─────────────────────┘
                │                          │ result event
                └──────────────┬───────────┘
                               ▼
                  SendLog + balance transaction + metrics
```

### Component Responsibilities

| Component | Responsibility | Typical/actual implementation |
|---|---|---|
| Edge/UI | HTTP, auth, server-rendered UI, API endpoints, static operational metrics | Nginx, FastAPI routers/pages, Jinja2, JWT/cookie auth |
| Application/domain boundary | Cross-entity use cases and transactional orchestration that must not depend on a transport | `app/application/`, `AbstractUnitOfWork`, scheduling use cases |
| Service/repository layer | Business operations and data access around accounts, billing, schedules, S3, and container lifecycle | `app/services/`, `app/repositories/`, async SQLAlchemy |
| Scheduler/dispatcher | Determines due schedules, advances `next_run_at`, checks cached quota, and fans out one unit of delivery per group | Celery Beat plus `check_schedules` / `collect_due_schedules` |
| Messenger adapters | Normalises send, group-sync, and connection operations behind `BaseMessenger` | `TelegramUserMessenger`, `WhatsAppMessenger`, `MaxMessenger` via `create_messenger` |
| Delivery executors | Own protocol sessions, rate limiting, retry classification, and outbound requests | Telegram Celery worker; dynamic `wa_worker` Node containers; dynamic `max_worker` Python containers |
| Result projector | Converts completion payloads into immutable delivery history, balance deductions, and group error state | periodic `process_wa_results` / `process_max_results` tasks |
| Operations | Request IDs, structured logs, metrics collection, queues/worker visibility, dashboards | structlog, Prometheus, Flower, Loki, Grafana |

## Recommended Project Structure

The existing structure is appropriate for this product and should be preserved rather than replaced with microservices. The correct evolution is to make transport contracts and delivery-state ownership more explicit inside the current modules.

```
app/
├── routes/             # JSON endpoints; transport/auth validation only
├── pages/              # server-rendered Jinja page controllers
├── application/        # use cases that coordinate repositories/UoW
│   ├── accounts/       # account lifecycle/read models
│   └── scheduling/     # due-schedule selection and single-send workflow
├── domain/             # abstractions and rules that do not know FastAPI/Celery
├── models/             # SQLAlchemy persistence model and business-state schema
├── repositories/       # persistence queries and aggregates
├── infrastructure/     # SQLAlchemy Unit of Work implementation
├── services/           # billing, S3, adapter factory, worker-container control
├── messengers/         # protocol adapters implementing BaseMessenger
├── worker/             # Celery entry points, dispatch, result projection
└── templates/          # UI views and reusable partials

wa_worker/              # one Baileys process/session per WhatsApp account
max_worker/             # one pymax process/session per MAX account
monitoring/             # Prometheus, Loki/Promtail, Grafana provisioning
```

### Structure Rationale

- **`routes/` and `pages/`:** retain thin HTTP responsibilities; put shared business changes below this boundary so API and HTML flows do not diverge.
- **`application/scheduling/`:** already isolates `collect_due_schedules` and `send_message_once` from Celery. Treat this as the authoritative delivery-use-case seam.
- **`messengers/`:** keep external-platform failure classification in adapters, not in route handlers or ORM models.
- **`worker/`:** should own only scheduling cadence, queue routing, retry mechanics, and result consumption; it must call the application layer for business state.
- **`wa_worker/` and `max_worker/`:** isolate mutable protocol sessions, protocol library versions, rate limits, and crash domains by account. Their Redis payload is an internal versioned contract, not an ad-hoc copy of a web request.

## Architectural Patterns

### Pattern 1: Control Plane / Per-Account Delivery Plane

**What:** Keep product configuration, schedules, balances, and delivery history in the Python control plane. Give connection-oriented messengers their own disposable, account-scoped workers with persisted session volumes.

**When to use:** A messenger session is stateful, uses a non-Python runtime, has a distinct rate limit, or must not allow one account failure to interrupt another account.

**Trade-offs:** This avoids a broad protocol outage and allows independent rate limiting, but requires lifecycle management, health/heartbeat visibility, and durable hand-off semantics.

**Existing comparison:** Broadcaster follows this for WhatsApp/MAX. Container managers create named `wa-worker-{account}` / `max-worker-{account}` containers on the Docker network, mount separate session volumes, cap memory at 256 MB, and let idle workers exit. Telegram appropriately remains a routed Celery workload because the adapter can open and close a Telethon session for one send.

### Pattern 2: Schedule Claim → Fan-out → Completion Projection

**What:** A periodic scheduler should atomically claim a due schedule occurrence, create one durable delivery command for every selected group, then advance the next occurrence. Workers send the command; a completion projector records final result and billing exactly once.

**When to use:** Any schedule can fan out across groups and delivery is asynchronous or retried.

**Trade-offs:** A durable outbox/delivery-command table costs schema and migration work, but joins database state and queue publication without a gap and supplies a natural idempotency key.

**Existing comparison:** `collect_due_schedules` reads due rows, builds in-memory `DispatchTask`s, advances `next_run_at`, commits, then `dispatch_send_tasks` publishes jobs. This protects schedules from being repeatedly due in the normal case, but it leaves a commit-to-publish gap: a process failure after the commit can lose an occurrence. The current `SendLog` stores `task_id` but has no uniqueness constraint, so it is audit history rather than a deduplication boundary.

**Preferred delivery identity:** `schedule_id + scheduled_for + group_id` (or a generated immutable delivery ID) must be carried through Celery/Redis, the protocol worker, SendLog, and the balance transaction. Use a database unique constraint plus an outbox/projector transaction to reject duplicate completion and duplicate billing.

### Pattern 3: Adapter-Owned Error Classification, Worker-Owned Retries

**What:** Adapters report a normal outcome shape (`ok`, `error`, `no_retry`) while the executor owns retry scheduling and platform-specific throttling. Fatal access errors update group state without retry; transient transport errors retry with bounded backoff.

**When to use:** External APIs give heterogeneous failures and uncertain delivery outcomes.

**Trade-offs:** Separating classification makes transport policy testable, but only works when every executor implements the same delivery identity and terminal-result protocol.

**Existing comparison:** WhatsApp and MAX workers serialize per-account sends, rate limit to eight/minute, use bounded retry delay arrays, and publish a terminal result. Telegram has a queue-level rate limit (`20/m`) and adapter-level `no_retry` classification; despite its docstring saying “Auto-retries with backoff”, the current Celery decorator has no `autoretry_for` or explicit `self.retry`, so raised transient Telegram errors are terminal Celery failures.

### Pattern 4: Short-Lived Async Resource Scope

**What:** Initialise application-scoped resources at FastAPI lifespan; create a database session per request/task and dispose task-local engines/clients after work.

**When to use:** An async API process shares configuration and connection pools but individual requests/tasks need isolated transaction scopes.

**Trade-offs:** It limits leaked connections and makes tests controllable. Creating a new engine for each Celery task has overhead, but keeps worker event-loop lifetimes simple in the current design.

**Existing comparison:** FastAPI creates the engine/session factory and UoW factory in `lifespan`; `get_db` yields an async session. Celery task functions create their engine/session factory within the task and dispose the engine in `finally`.

## Data Flow

### Request Flow

```
Browser/API request
    ↓
FastAPI router or page controller → dependency auth/session → service/use case
    ↓                                                       ↓
Jinja/JSON response              ← transaction/repository ← PostgreSQL
    ↓
S3 upload/download URL generation for advertisement images (when applicable)
```

### Scheduled Delivery Flow

```
Celery Beat
    ↓ periodic check
default worker: query active schedules where next_run_at <= UTC now
    ↓ quota/account checks; compute and commit new next_run_at
DispatchTask per selected group
    ├─ Telegram: Celery `telegram` queue → Telethon adapter → SendLog + deduct balance
    ├─ WhatsApp: Redis `wa:queue:{account}` → Baileys account container
    │               → Redis `wa:results` → result projector → SendLog + deduct balance
    └─ MAX: Redis `max:queue:{account}` → pymax account container
                    → Redis `max:results` → result projector → SendLog + deduct balance
```

### Account Connection and Group-Sync Flow

1. An account is persisted with a connecting/syncing status.
2. A messenger adapter starts or locates the account worker; its session files live in the messenger-specific Docker volume.
3. The worker performs QR/session lifecycle and group discovery, with bounded retry/backoff.
4. A Celery sync task polls worker status, upserts unseen groups, and transitions the account to `active` or `sync_failed`.
5. Scheduling only dispatches for accounts in `active` state.

### State Management

PostgreSQL is the authoritative state for configuration, account status, balances, next run time, and history. Redis should be treated as volatile transport/cache state: Celery queues/results, per-account work queues, active-account sets, endpoint TTLs, and billing cache. S3 stores immutable media objects; delivery payloads use derived public URLs for isolated workers while SendLog retains the original S3 keys.

## Reliability Patterns and Gaps

| Concern | Existing control | Gap / required guardrail |
|---|---|---|
| Schedule cadence | UTC `next_run_at`, user-timezone calculation, beat scan, commit after scan | Multiple beat instances or overlapping scans have no visible DB claim/lock; use row locking/lease or a unique occurrence command. |
| Queue isolation | Telegram queue separated from default work; WA/MAX queues partitioned by account | Redis lists use `LPOP`/`BLPOP`; a worker crash after pop and before result publish loses in-flight work. Use a processing queue/visibility timeout or a durable outbox. |
| Back pressure | Telegram rate limit; WA/MAX per-account serialized sends and eight/minute limiter | Queue depth and oldest-message age are not shown as Prometheus business metrics; alert before backlog breaks timeliness. |
| Transient failures | WA/MAX bounded retries and non-retryable classification | Telegram has no configured retry despite the task docstring; make retry policy explicit and delivery idempotent first. |
| Exactly-once business effects | Atomic balance decrement prevents negative balance | Duplicate results can create duplicate SendLogs and deduct multiple messages because no unique delivery key is enforced. |
| Account failure isolation | Per-account containers, session volumes, restart-on-failure, heartbeats, idle shutdown | Manager only checks queue length/containers; add stale-heartbeat detection and a recovery policy for stuck containers. |
| Observability | Request/task IDs, JSON logs, Prometheus app metrics, Flower, Loki/Grafana | Trace IDs are carried for worker messages but result-to-log correlation needs a durable delivery ID and metrics for retries, terminal errors, and lag. |

## Scaling Considerations

| Scale | Architecture adjustments |
|---|---|
| 0–1k users | Keep the modular monolith and current Compose topology. Separate the default and Telegram queues, tune worker concurrency conservatively, and monitor account-worker counts. |
| 1k–100k users | Introduce durable delivery commands/outbox, atomic schedule claiming, queue-depth/lag alerts, and autoscaled worker pools. Run a singleton/leased scheduler. Move dynamic worker lifecycle from Docker-socket calls toward an orchestrator-managed worker service if container churn becomes material. |
| 100k+ users | Partition delivery by tenant/account, use a durable broker with acknowledged processing semantics, deploy horizontally separated control-plane, scheduler, and delivery services, and isolate the protocol workers in an orchestrator. PostgreSQL remains the source of truth but needs partitioning/read optimisation around delivery history. |

### Scaling Priorities

1. **First bottleneck: reliable fan-out and recovery.** Fix schedule claim/outbox and result idempotency before adding concurrency; otherwise more workers increase duplicate/lost delivery risk.
2. **Second bottleneck: account-worker churn and backlog visibility.** Measure active containers, queue age, retry rate, and messenger success rate before introducing a container orchestration platform.

## Anti-Patterns

### Anti-Pattern 1: Treating Redis List Messages as Durable Delivery Records

**What people do:** Commit `next_run_at`, push a JSON task into a Redis list, then infer delivery from a later result list.

**Why it's wrong:** Commit and publish are not atomic, `BLPOP` removes work before it is durably acknowledged, and result projection can be repeated. A crash produces a lost send, duplicate send, or duplicate billing scenario that a SendLog index alone cannot resolve.

**Do this instead:** Add a database-backed delivery command/outbox with a unique occurrence ID. Publish it transactionally/out-of-band, claim it with a lease, and make result projection/billing insert-once by that ID.

### Anti-Pattern 2: Retrying External Sends Without an Idempotency Boundary

**What people do:** Add Celery `autoretry` or requeue a task after a timeout without knowing whether the messenger accepted the original request.

**Why it's wrong:** A timeout after provider acceptance can send the advertisement twice and charge twice.

**Do this instead:** Persist attempt state before the external call, retain provider message IDs when available, distinguish “unknown outcome” from “safe retry”, and make all completion projection idempotent.

### Anti-Pattern 3: Allowing Web Requests to Own Long-Lived Messenger Sessions

**What people do:** Perform QR login, group sync, or bulk sending directly in FastAPI request handlers.

**Why it's wrong:** Requests become long-lived, process restarts discard session state, and one platform's dependency/runtime contaminates the control plane.

**Do this instead:** Retain the current worker/container boundary; web actions should create durable state and request work, then poll/display status.

## Integration Points

### External Services

| Service | Integration pattern | Notes |
|---|---|---|
| Telegram | Telethon userbot in routed Celery task | One task opens/closes a session; platform access/slow-mode failures are classified as non-retryable today. |
| WhatsApp | Baileys in a dynamically created Node container per account | Redis queue/result contract; persistent session volume; rate limiter, serial session lock, group locks, heartbeat, idle shutdown. |
| MAX | pymax in a dynamically created FastAPI/Python container per account | Mirrors WhatsApp topology with its own queue/result namespace, locks, session volume, retry and heartbeat. |
| Redis | Celery broker/backend, account queues, result lists, endpoint/heartbeat keys, billing cache | A shared critical dependency; separate namespaces and monitor memory/availability. |
| PostgreSQL | Async SQLAlchemy primary store | Owns durable business state; use DB constraints for delivery identity and billing atomicity. |
| S3-compatible storage | Images uploaded by control plane, public URL sent to external workers | Persist keys, not derived URLs, in durable history. |
| Docker Engine | Container managers start/stop account workers through mounted Docker socket | Operationally powerful; restrict socket access and treat this as a privileged control-plane boundary. |

### Internal Boundaries

| Boundary | Communication | Notes |
|---|---|---|
| routes/pages ↔ application/services | Direct async calls and dependencies | Keep HTTP-specific validation/response mapping above the boundary. |
| application ↔ repositories/UoW | Interfaces and async session/UoW | New cross-aggregate writes should use a single transaction. |
| worker ↔ application scheduling | Direct function invocation for `collect_due_schedules` and `send_message_once` | Good seam; avoid moving domain decisions into Celery decorators. |
| dispatcher ↔ WA/MAX workers | Versioned JSON command/result payload in Redis | Add schema/version and immutable delivery ID before changing either side. |
| messengers ↔ external protocols | `BaseMessenger` result contract | Preserve `ok/error/no_retry`, but enrich it with provider correlation and outcome certainty. |

## Dependency and Build-Order Implications

1. **Establish delivery identity and schema first.** A `delivery_commands`/outbox model, unique occurrence key, and idempotent result/billing projection must exist before changing retries or throughput.
2. **Then make scheduler ownership explicit.** Implement a DB claim/lease and publisher so a committed occurrence is eventually dispatched exactly once from the database perspective.
3. **Then unify execution contracts.** Pass the same delivery ID through Celery, Redis, WhatsApp, MAX, and Telegram; make Telegram retry policy explicit only after the duplicate guard is live.
4. **Then add recovery and observability.** Processing leases/dead-letter handling, heartbeat expiry, queue-age metrics, retry/lag dashboards, and alerts depend on the delivery lifecycle states above.
5. **Only then revisit scale topology.** Container orchestration or a separate delivery service is a later operational decision; current component boundaries should survive that migration.

## Sources

- Repository implementation: `app/main.py`, `app/worker/celery_app.py`, `app/worker/tasks.py`, `app/application/scheduling/use_cases.py`, `app/messengers/`, `app/services/*_container_manager.py`, `wa_worker/index.js`, `max_worker/main.py`, Docker Compose and monitoring configuration. **HIGH** — direct current-state evidence, inspected 2026-08-03.
- [Celery task and periodic-task guidance](https://docs.celeryq.dev/en/stable/userguide/tasks.html) and [Celery optimisation guidance](https://docs.celeryq.dev/en/stable/userguide/optimizing.html). **MEDIUM** — official documentation retrieved through Context7; supports the idempotency, late acknowledgement, and overlap guidance.
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/) and [advanced dependencies](https://fastapi.tiangolo.com/advanced/advanced-dependencies/). **MEDIUM** — official documentation retrieved through Context7; supports the resource/session-scope guidance.

---
*Architecture research for: Broadcaster*
*Researched: 2026-08-03*

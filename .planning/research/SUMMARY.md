# Project Research Summary

**Project:** Broadcaster
**Domain:** Brownfield SaaS for scheduled advertising posts to Telegram, WhatsApp, and MAX groups
**Researched:** 2026-08-03
**Confidence:** MEDIUM-HIGH

## Executive Summary

Broadcaster is an implemented multi-messenger, group-first advertising scheduler for small businesses and agencies. Its control plane is a Python/FastAPI modular monolith backed by PostgreSQL, while Celery/Redis coordinate scheduled delivery. Telegram sends run through Telethon in the Python worker; WhatsApp and MAX use isolated, account-specific workers. The validated product already includes identity, account connection and group sync, reusable ad/media authoring, timezone-aware recurring schedules, delivery history, usage/billing controls, administration, and operational tooling.

The recommended path is to preserve this topology rather than re-platform or expand into an adjacent CRM, inbox, AI-content, or one-to-one marketing product. If a future milestone elects to improve the present system, start at the durable delivery boundary: assign every schedule occurrence/group send a stable identity, make claiming, publication, completion projection, and billing idempotent, then add explicit retry/recovery and observability. This order controls the highest-value risk: an external send can be duplicated, lost, or charged inconsistently at the PostgreSQL/Redis/worker boundary.

The major operating risks are platform enforcement and session failures, ambiguous external outcomes, timezone/DST behavior, account-worker backlog, sensitive session/media exposure, and dashboards that do not reveal late delivery. Mitigation is conditional future work, not an assertion of an active requirement: durable outbox/settlement records, classified connector errors and pacing, defined calendar semantics, per-account health/queue-lag signals, secret/data controls, and end-to-end delivery SLOs.

## Key Findings

### Recommended Stack

The implemented stack is well matched to the workload and should remain the baseline. PostgreSQL is the durable authority for product and audit state; Redis is transport/cache state only; S3-compatible storage holds advertisement images. Retain the modular monolith and account-isolated connector workers instead of introducing microservices or a separate SPA without a validated product need. Preserve locked dependencies and upgrade only with contract and integration coverage.

**Core technologies:**

- **Python 3.12, FastAPI 0.129.0, and Jinja2 3.1.6:** existing control plane and server-rendered UI — avoids needless frontend/runtime expansion.
- **SQLAlchemy async 2.0.46 with asyncpg and PostgreSQL 16:** transactional source of truth for schedules, accounts, balances, and history.
- **Celery 5.6.2 with Redis 7:** periodic dispatch and short identifier-based work messages — not a durable business record or media transport.
- **Telethon 1.42.0:** Telegram user-account integration — keep behind the existing adapter/pool and preserve explicit flood/session failure handling.
- **Baileys 7.0.0-rc.9 and pymax/maxapi-python:** WhatsApp/MAX account workers — keep each account's session and process isolated; pin/test protocol-worker versions before upgrades.
- **Docker Compose/Nginx plus Prometheus, Grafana, and Loki:** current deployment and operational boundary — replace floating monitoring tags when the deployment baseline is next intentionally changed.

### Expected Features

The table-stakes workflow is already implemented: authentication and recovery; messenger account connection; group synchronization/selection; reusable text/image ads; recurring, timezone-aware schedules; automated per-group delivery records; searchable history and dashboard statistics; balance/subscription controls; admin support; and baseline monitoring. The current differentiator is one group-posting workflow across Telegram, WhatsApp, and MAX, with account-specific worker isolation and content/group snapshots for support and billing evidence.

**Validated table stakes:**

- Identity, recovery, and authenticated SaaS access.
- Connected messenger accounts, synchronized groups, ad/media authoring, and recurring schedules.
- Automated per-destination execution, history, balance/subscription enforcement, administration, and monitoring.

**Validated differentiators:**

- One recurring-ad workflow spanning Telegram, WhatsApp, and MAX group destinations.
- Group-first targeting, account-scoped connector isolation, and snapshot-rich send logs.

**Future-only / defer unless activated:**

- Calendar/campaign planning UX and expanded reporting.
- Agency/client workspaces, approval chains, or finer roles.
- One-to-one marketing consent/template management.
- CRM, shared inbox, chatbots, AI content generation, or broad cross-channel analytics.

### Architecture Approach

Keep the existing control-plane/delivery-plane split. HTTP pages/routes remain thin over application use cases, services, repositories, and an async unit of work. The scheduling use case should remain the authoritative seam for due occurrence collection and single-send orchestration; adapters own platform error classification; workers own queueing, pacing, retry mechanics, and result consumption. The missing future guardrail is a durable, immutable delivery command/outbox that bridges schedule claim, queue publication, result projection, and billing.

**Major components:**

1. **FastAPI/Jinja control plane** — user/admin UI, APIs, authorization, configuration, and lifecycle requests.
2. **PostgreSQL and S3-compatible storage** — durable business/audit state and advertisement image objects.
3. **Celery Beat/default/Telegram workers and Redis** — schedule scanning, routed work, and connector-result coordination.
4. **Messenger adapters and per-account WA/MAX containers** — account sessions, group sync, pacing, sends, and protocol-specific outcomes.
5. **Result projection, billing, and operations** — immutable send evidence, balance settlement, structured logs, metrics, dashboards, and alerts.

### Critical Pitfalls

1. **Duplicate, lost, or uncertain sends** — introduce a stable delivery ID, database uniqueness, durable outbox/inbox or acknowledged transport, idempotent completion/billing, and crash-injection verification before increasing retries or throughput.
2. **Billing and delivery drift** — authorize/reserve or settle each destination against the durable delivery ID; do not treat cached balance checks as final authorization; reconcile successful sends to exactly one balance transaction.
3. **Platform enforcement and connector health** — classify permanent vs transient errors, retain pacing, expose re-auth/group-health states, and do not retry policy/session failures indiscriminately.
4. **Unseen account-worker backlog and late delivery** — track worker heartbeat, queue age, retries, terminal outcomes, and due-to-terminal lateness; alert and expose useful customer status.
5. **Credential/content/media exposure** — protect sessions at rest, restrict Docker/backup/volume access, redact logs, validate tenant ownership, and review object access policy.

Timezone/DST semantics are also a material correctness risk whenever recurrence or schedule UX changes: document the chosen policy, display local and UTC next runs, and test IANA-zone transition cases.

## Implications for Roadmap

This is a suggested reliability-improvement sequence only. `PROJECT.md` has no active new requirements, so none of these phases should be treated as approved implementation scope until a milestone activates them.

### Phase 1: Delivery Identity and Durable Dispatch Foundation

**Rationale:** Every later reliability improvement depends on distinguishing one logical schedule occurrence/group delivery from retries and projections.

**Delivers:** A schema-backed immutable delivery identity; unique occurrence/group invariant; transactional schedule claim/lease and outbox/publisher path; versioned connector payload carrying the delivery ID.

**Addresses:** Existing scheduled multi-group dispatch, send history, and multi-messenger delivery.

**Avoids:** Commit-to-publish loss, Beat overlap duplicates, destructive Redis-pop ambiguity, and duplicate `SendLog` records.

### Phase 2: Idempotent Settlement, Billing Integrity, and Connector Retry Contract

**Rationale:** Once a durable identity exists, all channels can safely distinguish terminal, retryable, and uncertain outcomes before retry policy is changed.

**Delivers:** Insert-once result projection; delivery-to-transaction reconciliation; defined charge event/reservation or atomic authorization; explicit Telegram retry behavior; normalized outcome certainty and provider correlation where available.

**Addresses:** Per-group outcomes, balance/subscription enforcement, Telegram/WA/MAX delivery paths.

**Avoids:** Double charging, unbilled success, retry-caused duplicate sends, and treating a timeout as proof of non-delivery.

### Phase 3: Scheduling Correctness and Delivery-State UX

**Rationale:** Users need a truthful schedule/delivery lifecycle after the underlying command model is reliable.

**Delivers:** Documented DST policy, recurrence input validation, local/UTC next-run visibility, and customer-visible pending/terminal/uncertain states with actionable connector errors.

**Addresses:** Current timezone schedules, account/group status, history, and dashboards.

**Avoids:** Wrong-time sends, ambiguous “scheduled” or generic “failed” states, and harmful blind retries.

### Phase 4: Account-Worker Resilience and Operational SLOs

**Rationale:** Reliable settlement states make queue age, heartbeat, retry exhaustion, and lateness measurable and recoverable.

**Delivers:** Bounded worker lifecycle/re-auth recovery, stale-heartbeat and per-account queue-lag detection, end-to-end delivery metrics, dashboards, alerts, and recovery rehearsal.

**Addresses:** Existing WA/MAX isolation, monitoring, and support operations.

**Avoids:** Healthy-web/failed-delivery blind spots, stuck account containers, and unbounded late schedules.

### Phase 5: Security and Data-Governance Hardening

**Rationale:** Existing session credentials and customer content are high-impact assets; hardening should precede enterprise expansion or broader data-sharing scope.

**Delivers:** Verified secret-at-rest protection, session revocation/rotation, least-privilege worker/backup/storage access, log redaction/retention, and tenant-isolation tests.

**Addresses:** Existing connected accounts, ad assets, history, and administrative operations.

**Avoids:** Account takeover, cross-tenant exposure, public-media leakage, and sensitive-log/backup disclosure.

### Phase Ordering Rationale

- The architecture explicitly requires delivery identity and durable dispatch before retries, concurrency, billing changes, or scaling; otherwise those changes amplify duplicate/lost-send risk.
- Settlement and billing follow the delivery identity because they share the same idempotency boundary.
- UX correctness and SLOs become trustworthy only after delivery states are durable and reconciled.
- Security is independent enough to be pulled forward if risk assessment requires it, but should not be coupled to unvalidated product expansion.
- No feature-suite phase is recommended: proposed CRM, inbox, AI, collaboration, and recipient-messaging work is future-only and requires separate discovery/compliance validation.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 1:** Database/outbox/lease design and the actual Celery/Redis/WA/MAX contract need repository-specific migration and crash-recovery research.
- **Phase 2:** Messenger idempotency guarantees, outcome certainty, pricing settlement, and provider receipt capabilities differ by channel.
- **Phase 3:** DST policy is a product decision; supported IANA zones and calendar behavior need explicit validation.
- **Phase 5:** Encryption/key management, data retention, storage access, and privacy obligations depend on the deployment and customer context not established in current research.

Phases with standard patterns (may skip a separate research phase after code inspection):

- **Phase 4:** Prometheus/Grafana/Loki alerting and heartbeat/queue-lag monitoring use established patterns, though metric names and thresholds must be derived from actual workloads.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Exact current dependencies/topology are repository-verified; future upgrade and external-library advice relies on official documentation/current ecosystem evidence. |
| Features | HIGH | Implemented-state claims are verified from project documentation and inspected models/routes/workers; positioning is only medium-confidence context. |
| Architecture | HIGH | Current topology and delivery-flow gaps were inspected directly; general reliability guidance is medium-confidence. |
| Pitfalls | HIGH | Failure modes derive from observed scheduler, Redis, worker, billing, and credential-handling paths; platform-policy interpretation is medium-confidence. |

**Overall confidence:** MEDIUM-HIGH. The present product inventory and technical-risk ordering are well supported; no future product scope has been validated.

### Gaps to Address

- **Production behavior evidence:** Current research did not establish real queue volumes, delivery latency, incident history, or actual platform-account enforcement rates. Baseline these before choosing scale thresholds/SLO targets.
- **Delivery semantics:** Provider receipt/idempotency behavior and exact accepted-vs-delivered meaning need connector-specific verification before promising exactly-once or delivery guarantees.
- **Billing policy:** The business rule for reservation, unsuccessful/uncertain sends, refunds, and reconciliation exceptions needs explicit product/finance ownership before implementation.
- **Security deployment controls:** Encryption, key rotation, backup access, Docker socket restrictions, and S3 policy may exist outside the inspected code and need an environment review.
- **Timezone policy:** The intended behavior for ambiguous/nonexistent local time has not been set; decide it before schedule behavior changes.
- **Compliance:** Group-posting policy posture and any future recipient-messaging capability require legal/policy review; no such expansion is implied by current research.

## Sources

### Primary (HIGH confidence)

- [PROJECT.md](../PROJECT.md) — validated current product scope, constraints, and no active new requirements.
- [STACK.md](STACK.md) — locked stack and deployment inventory.
- [FEATURES.md](FEATURES.md) — implemented feature inventory, dependencies, and future-only scope.
- [ARCHITECTURE.md](ARCHITECTURE.md) — observed topology, data flow, boundaries, and build-order implications.
- [PITFALLS.md](PITFALLS.md) — code-observed failure modes, safeguards, and verification topics.

### Secondary (MEDIUM confidence)

- Official FastAPI, SQLAlchemy, Celery, Docker Compose, Telethon, Baileys, AWS S3, WhatsApp, and Telegram documentation cited in the four detailed research files — framework behavior, integration constraints, and platform-policy context.

---
*Research completed: 2026-08-03*
*Ready for roadmap: yes — as a current-state/reliability decision aid, not a declaration of active implementation requirements.*

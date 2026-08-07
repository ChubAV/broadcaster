# Pitfalls Research

**Domain:** SaaS for scheduled advertising posts to Telegram, WhatsApp, and MAX groups
**Researched:** 2026-08-03
**Confidence:** HIGH for code-observed failure modes; MEDIUM for platform-policy interpretation

## Scope and Evidence

This is a brownfield risk register, not a statement that an incident has occurred or a request to expand scope. “Current control” refers only to behavior inspected in the repository. “Phase to address” names a future *roadmap topic* that should be included only if the roadmap elects to improve that risk.

## Critical Pitfalls

### Pitfall 1: Platform enforcement or account limitation treated as an ordinary transient failure

**What goes wrong:**
An account is restricted, logged out, removed from a group, or receives platform rate limits after advertising activity. Retrying indistinguishably can worsen the restriction and leave schedules appearing active while messages no longer reach their destinations.

**Why it happens:**
The product sends through external accounts and protocols whose policy, group-admin decisions, reputation signals, and session lifecycle are outside its control. The current code correctly marks some forbidden/session failures as non-retryable and records group errors, but delivery cannot be guaranteed by the scheduler.

**How to avoid:**
Preserve per-account/group health, classify permanent versus retryable errors, pace sends per account, pause or surface unhealthy destinations, and keep a support/re-auth path. Do not market the service as a way to bypass platform policies. Before any future one-to-one WhatsApp capability, design consent, opt-out, template, category, and policy-review controls separately; those rules are not automatically satisfied by the current group workflow.

**Warning signs:**
Growing `forbidden`, session-unavailable, slow-mode/rate-limit, or sync-failed errors; repeated account reconnections; a sharp success-rate drop for one account; user reports of blocks or removed group access.

**Phase to address:**
Connector health and delivery reliability, if a future roadmap phase changes sending behavior or platform integrations.

---

### Pitfall 2: Duplicate or lost sends at the scheduler/queue boundary

**What goes wrong:**
The same scheduled group post can be dispatched twice, retried after it was accepted by a messenger, or recorded/charged twice. Conversely, a worker can pop a queue/result item and crash before the outcome reaches the database, making a delivered or failed send invisible.

**Why it happens:**
The execution path crosses database commits, Celery/Redis queues, per-account workers, and external messenger calls. The scheduler advances `next_run_at` before dispatch; WA/MAX consumers use Redis `BLPOP`, retry by re-enqueueing, and their result processors use destructive `LPOP` before committing database writes. `SendLog.task_id` is indexed but has no uniqueness constraint or observed “already processed” guard. An external API can succeed immediately before a process failure or timeout makes the caller uncertain.

**How to avoid:**
Treat delivery as at-least-once. Persist a stable dispatch ID before enqueueing; enforce an idempotency key/unique invariant for one logical schedule occurrence + group; make result consumption recoverable (acknowledged stream or durable inbox/outbox); reconcile pending dispatches; and make retries consult the recorded terminal state before sending or billing. Test crashes at every boundary, including after messenger acceptance and before DB commit.

**Warning signs:**
Two successful `SendLog` rows with the same task/logical occurrence; a report of duplicate group content; queue/result depth drops without matching logs; balances and successful sends diverge; schedules repeatedly due after Beat overlap or restart.

**Phase to address:**
Dispatch idempotency and reconciliation—before adding volume, channels, retry changes, or billing changes.

---

### Pitfall 3: Timezone and daylight-saving behavior surprises users

**What goes wrong:**
An ad fires an hour early/late around a daylight-saving transition, skips a nonexistent local time, or appears not to run because the user selected no days/times. The business impact is higher than for a normal reminder because the user is paying for advertising timing.

**Why it happens:**
Schedules combine local weekday/time inputs with a stored IANA timezone and convert the next occurrence to UTC. That is the correct broad model, but Python’s construction of local datetimes must have explicitly tested semantics for ambiguous and nonexistent civil times. The current `compute_next_run_at` is deliberately simple: it creates local candidate datetimes and selects the first strictly future time; it does not document a DST policy. Empty day/time arrays result in `next_run_at = None`.

**How to avoid:**
State the product rule for DST (for example, whether the first/second repeated time is used and what happens to skipped times), validate schedule input, render the next run in both user-local time and UTC, recalculate after edits/account changes, and include boundary tests for supported zones. Avoid hard-coding offset calculations.

**Warning signs:**
Support reports localized to DST weekends; a mismatch between rendered `next_run_at` and expected wall time; active schedules with `next_run_at` null; recurring sends one hour apart from the user’s expectation.

**Phase to address:**
Scheduling correctness, if calendars, new recurrence rules, or timezone UX are changed.

---

### Pitfall 4: Balance, quota, and delivery fall out of sync

**What goes wrong:**
A customer receives more sends than their balance permits, is charged more than once for a logical delivery, or sees a stale “allowed” result when a large due batch fans out across groups.

**Why it happens:**
There is a good current control: `deduct_message` performs a conditional atomic decrement and writes a balance transaction. However, allowance is first cached per user and checked while scheduling, then messages are sent externally, and the decrement return value is not used to prevent a later successful send from remaining successful. Multiple group tasks can therefore be authorized from one cached pre-check; duplicate result processing would also create another deduction absent a task-id uniqueness/reconciliation rule.

**How to avoid:**
Define the charge event explicitly (normally one successfully accepted group send), reserve or atomically authorize each unit before dispatch, associate every reservation/settlement with the durable dispatch ID, make settlement idempotent, invalidate/check cache only as an optimization rather than authorization truth, and provide a reconciliation report for delivery logs versus balance transactions.

**Warning signs:**
Negative/incorrect balances, more successful log rows than billable balance transactions, clusters of sends immediately around a balance boundary, or repeated transactions associated with one task ID.

**Phase to address:**
Billing and dispatch integrity—before changing pricing, quotas, or batch throughput.

---

### Pitfall 5: Per-account worker lifecycle becomes an unobserved delivery bottleneck

**What goes wrong:**
WA/MAX queues build up because a container cannot start, has lost its session, exits after idle, or repeatedly reconnects. The main app remains healthy while messages are delayed indefinitely or a newly queued task waits for the container manager cycle.

**Why it happens:**
The isolation model intentionally uses a container, session volume, heartbeat, queue, retry delays, and idle shutdown per account. This reduces cross-account blast radius but introduces orchestration state that the main process cannot infer merely from “schedule due.” The current workers have rate limiting, reconnect attempts, heartbeats, cleanup, and container management, but no code-observed end-to-end alert tying queue age, heartbeat freshness, account status, and delivery latency together.

**How to avoid:**
Use a lifecycle state machine with bounded startup/reconnect failure, inspect heartbeat age and queue age, alert on stuck/absent consumers, expose worker health and queue lag beside customer-visible status, and rehearse restart/re-auth/replay recovery. Keep account-scoped rate limits; do not scale consumers for the same account without preserving ordering/session safety.

**Warning signs:**
Increasing `wa:max:queue:<account>` length, missing/stale heartbeat, endpoint key churn, sync failures, containers restarting, or a gap between due schedule time and `SendLog.sent_at`.

**Phase to address:**
Worker lifecycle observability and resilience, if operational scale/reliability work is prioritized.

---

### Pitfall 6: Messenger credentials, advertising content, and assets are treated as ordinary application data

**What goes wrong:**
A database backup, overly broad admin/log access, exposed session volume, or public media configuration exposes a Telegram session string, a WhatsApp/MAX session, customer ad copy, group names, or uploaded images. Compromise of a connected account can lead to spam, account loss, and customer harm.

**Why it happens:**
Messenger sessions are authentication material. The inspected `MessengerAccount` model stores `credentials` and `session_data` as text, and account pages assign session strings/phone values directly. This review found no application-level field encryption in those paths; deployment-level encryption may exist but was not verified. Image delivery derives URLs from an `s3_public_url` configuration, so access policy must be intentional. Worker logs also include task/group identifiers and shortened message captions.

**How to avoid:**
Encrypt session secrets at rest with managed/key-rotatable encryption, narrowly restrict DB/backups/worker volumes and Docker access, redact credentials and ad text from logs, set retention/deletion rules, use least-privilege storage access (private objects with controlled URLs when appropriate), and force re-auth/revoke sessions on account deletion or suspected exposure. Validate cross-tenant authorization for every account, group, history, and asset operation.

**Warning signs:**
Session strings/QR payloads in logs, unexpected account activity, public object listing/access, credentials present in backups or support exports, cross-tenant IDs returning data, or long-lived sessions surviving an intended revocation.

**Phase to address:**
Security and data-governance hardening, before enterprise expansion or any broader data-sharing feature.

---

### Pitfall 7: Aggregate metrics hide a broken delivery path

**What goes wrong:**
Prometheus/Grafana/Loki are available, but a delivery outage is noticed from customers rather than alerts because only broad counts are visible. A growing backlog, stale worker heartbeat, repeated retry, policy rejection, or late execution can be masked by a still-healthy web service.

**Why it happens:**
The current business metrics aggregate active schedules/users and total send-log counts by messenger/status. They do not, in inspected code, model freshness, queue depth/age, dispatch-to-send latency, retry count, result-consumer loss, or expected-versus-actual occurrences. Logs have task IDs, but an end-to-end correlation/alert contract is not documented.

**How to avoid:**
Define SLOs around the project success metric—scheduled sends completed at the intended time—then emit metrics/alerts for due schedules, dispatches, queue lag, worker heartbeat, retries, terminal outcomes, lateness, and reconciliation gaps. Keep high-cardinality identifiers in logs/traces rather than metric labels.

**Warning signs:**
Flat success totals alongside increased queue depth, long delay from `next_run_at` to `sent_at`, high retry/reconnect activity, absence of results during business hours, or a sudden channel-specific success-rate drop.

**Phase to address:**
Operational observability and SLOs, before increased customer volume or stricter reliability commitments.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Redis lists with `BLPOP`/`LPOP` as the only work/result transport | Simple queue code and low operational overhead. | No acknowledgement/in-flight recovery; worker or result-processor crashes create duplicate/lost-state ambiguity. | Only while accompanied by a documented reconciliation process; not acceptable for an exactly-once billing claim. |
| Task ID recorded but not uniquely constrained | Cheap troubleshooting correlation. | Cannot make result settlement or duplicate prevention deterministic. | Never for billable terminal delivery records once retries/crash recovery are enabled. |
| A TTL balance cache used before batch fan-out | Fewer database reads. | A stale authorization decision can permit more tasks than balance can cover. | As a display/read optimization, not as the only authorization or settlement guard. |
| One simple recurrence calculator | Easy to reason about for weekly schedules. | DST policy and complex recurrence expectations remain implicit. | Appropriate for the current narrow recurrence model if DST behavior is tested and disclosed. |
| Plain text session fields relying on deployment security | Fast integration with connector libraries. | A database/backup/support-access incident becomes messenger-account compromise. | Only temporarily with strong compensating encryption and access controls verified; otherwise avoid. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Telegram userbot / Telethon | Treating a user account as an unlimited broadcast credential; retrying spam/forbidden errors. | Respect platform limits and group permissions; classify permanent errors, surface account health, and require re-auth when sessions fail. |
| WhatsApp / Baileys | Equating a working QR session with policy authorization or assuming a transient network error means no message was delivered. | Preserve task identity across retries, pace per account, distinguish uncertain delivery, and apply the relevant WhatsApp policy before any user-contact messaging feature. |
| MAX / pymax | Assuming a separate worker removes all lifecycle/session risk. | Monitor session, queue, heartbeat, and container state jointly; preserve account-scoped serialization and recovery paths. |
| Redis | Using destructive pops without a durable in-flight/acknowledged record. | Use a durable inbox/outbox, streams/consumer acknowledgements, or an equivalent replay/reconciliation design. |
| S3-compatible image storage | Treating a public URL as authorization and retrying without validating object availability. | Verify bucket/object ACLs, use controlled URLs when needed, and make media failures visible in the per-send result. |
| YooKassa / billing provider | Trusting the redirect/return page as final payment state. | Process authenticated provider notifications idempotently and reconcile payment IDs to balance transactions. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| One due-schedule query expands every group into in-memory tasks | Beat runs take longer and Redis receives large bursts; next checks overlap. | Bound due batches, lock/claim schedule occurrences, and observe dispatch duration/backlog. | At a single large schedule or when many schedules become due in the same interval; exact threshold depends on groups per schedule and worker capacity. |
| Per-account serialized sending plus fixed low rate limits | Queue age grows even though container health is green. | Forecast capacity per account, show planned/actual delay, retain pacing as a safety control. | Whenever a schedule’s group fan-out exceeds what its account can send during the desired window. |
| Requeueing delayed tasks back into the same list | Workers repeatedly pop/requeue not-yet-ready work, creating churn and potentially delaying fresh work. | Use a delayed-queue mechanism or scheduled retry store; monitor retry queue age. | Under sustained rate limits or external outages. |
| Database scans/aggregations for every metrics update | Metrics loop adds DB load as send-log history grows. | Index/aggregate deliberately and measure the metrics job. | At materially larger history volume; do not pre-optimize until metrics show it. |
| One global results list per messenger | A noisy account can delay reconciliation for others; a poison result can affect batch processing. | Partition/stream by account or robustly isolate failures and alert on per-account lag. | With many simultaneously active accounts or a prolonged connector outage. |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Persisting messenger sessions without verified encryption/access controls | Account takeover and unauthorized posting. | Encrypt secrets at rest, restrict worker/session volumes and backup access, rotate/revoke sessions. |
| Logging message previews or identifiers without a data classification/retention policy | Leakage of customer campaign content and group metadata. | Redact/minimize logs, protect Loki access, and set retention/export controls. |
| Assuming public object URLs are safe because keys are random | Media can be shared indefinitely or discovered through logs/referrers. | Review bucket policy; prefer controlled delivery where confidentiality matters. |
| Failing to enforce tenant ownership on every indirect identifier | One customer can manipulate another customer’s account/group/schedule/history. | Use ownership checks at API/use-case boundaries and cross-tenant authorization tests. |
| Reusing a weak/shared JWT secret or overlong session handling | Impersonation and persistent access after compromise. | Rotate a high-entropy secret, protect cookies/tokens, expire/revoke appropriately, and audit admin access. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing “scheduled” without the exact next local time, timezone, and account/group count | Users assume a post will occur when it may be paused, empty, late, or unsendable. | Display next run in the chosen timezone, UTC where useful, status, and destination count. |
| Hiding policy/session/group-permission failures behind generic “failed” status | Customers retry blindly and may damage account health. | Use actionable classified errors: re-authenticate, re-sync, removed from group, rate limited, policy/support review. |
| Treating a queued task as delivered | Users cannot distinguish accepted, pending, delivered/failed, or uncertain outcomes. | Model visible lifecycle states and explain retries/late delivery. |
| Recording history but not allowing reconciliation from a schedule occurrence to every group send | Agencies cannot prove what happened or resolve billing disputes. | Keep stable occurrence/task IDs and link schedule, destinations, attempts, terminal status, and transaction. |

## "Looks Done But Isn't" Checklist

- [ ] **Scheduled dispatch:** verify one logical schedule occurrence cannot be claimed by concurrent Beat/worker processes twice and is recoverable after a crash.
- [ ] **Retries:** verify an external send that succeeds just before a timeout is not posted/charged again on retry.
- [ ] **WA/MAX result processing:** verify a result popped from Redis is durably recorded or replayed after a process/database failure.
- [ ] **Billing:** verify multi-group fan-out at a one-message balance boundary has a defined, tested outcome and no unbilled success.
- [ ] **Timezone scheduling:** verify selected zones on DST spring-forward/fall-back boundaries and empty recurrence input behavior.
- [ ] **Account lifecycle:** verify re-auth, logout/ban, container restart, idle shutdown, and group re-sync reach a visible customer and operator state.
- [ ] **Media:** verify each stored image remains reachable to the connector at execution time and storage access matches data sensitivity.
- [ ] **Observability:** verify alerts cover late schedules, queue age, stale heartbeat, retry exhaustion, and channel-specific delivery-rate drops—not only web uptime.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Platform account limitation | HIGH | Stop automatic retries for the affected account, preserve error evidence, guide re-auth/appeal per platform process, re-sync groups, and do not replay uncertain sends without customer review. |
| Duplicate or uncertain delivery | HIGH | Quarantine the logical occurrence, deduplicate by stable dispatch ID and messenger receipt when available, correct logs/balance transaction idempotently, and explain the outcome to the customer. |
| Result lost after Redis pop | MEDIUM | Identify pending dispatches without terminal records, replay from durable source once implemented or reconcile manually from worker/messenger logs, then repair history/balance. |
| Worker/container unavailable | MEDIUM | Alert from heartbeat/queue age, restart only the affected account worker, validate session/group health, and drain/reconcile pending work at safe pacing. |
| Wrong local send time | MEDIUM | Pause the schedule, preserve the occurrence audit, correct timezone/recurrence, communicate whether a compensating send is appropriate, and add a regression test. |
| Credential/data exposure | HIGH | Revoke sessions, rotate secrets/keys, restrict compromised storage/log/backups, assess affected data, notify/act under applicable obligations, and audit access. |

## Pitfall-to-Phase Mapping

These are recommended research/verification topics, not pre-approved roadmap phases.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Platform enforcement/account health | Connector reliability | Simulate rate-limit, forbidden, logged-out, and sync-failed responses; ensure pacing, non-retry classification, visible status, and safe recovery. |
| Duplicate/lost send | Dispatch idempotency and reconciliation | Crash-injection tests around claim, enqueue, external acceptance, result publish, and DB commit; assert exactly one terminal settlement per dispatch ID. |
| Timezone/DST errors | Scheduling correctness | Table-driven tests across supported IANA zones and both DST transitions; compare displayed local next run with UTC execution. |
| Billing mismatch | Billing and dispatch integrity | Concurrent/fan-out tests at the balance boundary; reconcile every success to exactly one transaction and prove duplicate results are harmless. |
| Worker lifecycle backlog | Worker resilience and observability | Kill/restart a worker, expire heartbeat, create backlog, and verify bounded recovery plus alerts and customer-visible state. |
| Credential/data exposure | Security/data governance | Secret-at-rest and authorization review; test tenant isolation, log redaction, session revocation, storage policy, and backup access. |
| Silent late/outage detection | Operational SLOs | Alert tests for queue age, heartbeat freshness, retry exhaustion, and percentile lateness from due time to terminal outcome. |

## Sources

- Internal implementation evidence: [`PROJECT.md`](/root/broadcaster/.planning/PROJECT.md), [`scheduling use cases`](/root/broadcaster/app/application/scheduling/use_cases.py), [`worker tasks`](/root/broadcaster/app/worker/tasks.py), [`schedule service`](/root/broadcaster/app/services/schedule_service.py), [`billing service`](/root/broadcaster/app/services/billing_service.py), [`WA worker`](/root/broadcaster/wa_worker/index.js), [`MAX worker`](/root/broadcaster/max_worker/main.py), [`container manager`](/root/broadcaster/app/services/wa_container_manager.py), and [`metrics`](/root/broadcaster/app/metrics.py). **HIGH** confidence for code-observed statements.
- [Celery task documentation](https://docs.celeryq.dev/en/stable/userguide/tasks.html) and [Celery FAQ](https://docs.celeryq.dev/en/stable/faq.html). **MEDIUM** confidence; official guidance establishes the retry/idempotency model but does not audit this application.
- [WhatsApp Business Messaging Policy](https://whatsappbusiness.com/policy/). **MEDIUM** confidence; current official policy says policy violations, negative feedback, low quality, or unauthorized scaled messaging can limit/remove access, and specifies opt-in/template rules for the Business Platform.
- [Telegram Spam FAQ](https://telegram.org/faq_spam). **MEDIUM** confidence; current official guidance confirms reports/unwanted group advertising can lead to temporary or longer account limitations.

---
*Pitfalls research for: Broadcaster — scheduled advertising posts to messenger groups*
*Researched: 2026-08-03*

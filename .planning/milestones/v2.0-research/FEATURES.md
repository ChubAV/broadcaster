# Feature Research

**Domain:** SaaS for scheduled advertising posts to messenger groups
**Researched:** 2026-08-03
**Confidence:** HIGH for implemented state; MEDIUM for ecosystem positioning

## Scope and Evidence

This is a brownfield inventory, not a proposal for a new product. “Implemented” is verified against `PROJECT.md`, the README, and the application models, routes, pages, and worker code. Market observations are limited to positioning and compliance boundaries; they do **not** create active requirements.

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Account registration, email verification, JWT login, password reset | A SaaS customer needs a secure self-service entry point. | MEDIUM | **Implemented.** Recorded in `PROJECT.md`; auth pages and API routes exist. |
| Connect and manage messenger accounts | Sending must originate from a customer-controlled account. | HIGH | **Implemented.** Telegram QR/userbot, WhatsApp worker and MAX worker connection flows are present. |
| Synchronize, inspect, and select destination groups | Users cannot schedule reliable posts without selecting the actual groups available to each connected account. | HIGH | **Implemented.** Groups are synced per account and stored with messenger type. |
| Create and maintain reusable ads with images | Reusable text-and-media content is the minimum authoring workflow for recurring ads. | MEDIUM | **Implemented.** Ad records contain title, text, active state, and S3/MinIO-backed image URLs. |
| Recurring scheduling with days, times, pause/resume, and timezone | The product’s core promise is automatic posting at the intended local time. | HIGH | **Implemented.** Schedules persist group IDs, weekdays, times, timezone, active flag, and `next_run_at`. |
| Automated execution and per-destination outcomes | Scheduled work has to run without an open browser and show whether each group was reached. | HIGH | **Implemented.** Celery dispatches Telegram tasks and account-specific Redis queues for WhatsApp/MAX; `SendLog` records status, task ID, errors, and snapshots. |
| Searchable delivery history and basic account/dashboard statistics | Operators need to diagnose failed sends and verify work happened. | MEDIUM | **Implemented.** History is filterable by status, messenger, account, and 7/30-day period; dashboard/account views show counts and recent results. |
| Usage limits, message balance, subscriptions, and admin controls | A multi-tenant paid product needs an enforceable service boundary and support tooling. | HIGH | **Implemented.** Free/Basic/Pro limits, atomic send deductions, transaction history, subscriptions, and administration are documented and present. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| One recurring-ad workflow across Telegram, WhatsApp, and MAX group destinations | A small business or agency avoids rebuilding the same recurring campaign separately for each supported messenger. | HIGH | **Implemented.** This is the clearest product differentiator; each channel has a dedicated adapter/worker path. |
| Group-first targeting rather than a customer-contact CRM | Directly supports the stated use case—posting advertising content into groups where the account participates—without requiring lead import or customer data management. | MEDIUM | **Implemented.** Schedules target stored group IDs, not a contact audience database. |
| Per-account WhatsApp and MAX worker isolation | Separates account session/lifecycle concerns and limits one unstable external session’s blast radius. | HIGH | **Implemented.** Dynamic account-specific containers and Redis queues are part of the current deployment model. |
| Immutable-looking send context in history | Ad title/text/images, group name, messenger type, error, and task ID stay visible even if the live ad or group later changes. | MEDIUM | **Implemented.** `SendLog` carries content and group snapshots; valuable for support and billing disputes. |
| Built-in operations visibility | Prometheus, Grafana, and Loki make the scheduled-service workload operable without an external observability product. | MEDIUM | **Implemented.** This is an operational differentiator rather than a customer-facing marketing-suite feature. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Unrestricted contact-list bulk messaging / scraping | It appears to increase reach quickly. | It changes a group-posting scheduler into a CRM/recipient-data product and raises consent, privacy, and platform-policy risk. WhatsApp’s policy materials and Telegram’s Spam FAQ make abuse/account restrictions a material concern. | Preserve customer-controlled group targeting; treat any future recipient messaging as a separately validated compliance product. |
| “Send everywhere now” with no account/group health gate | It reduces clicks in the UI. | It hides external permissions, session state, slow-mode/rate limits, and group removal failures—the exact states that need visible outcomes. | Keep account status, group sync, scheduled dispatch, and per-send logs as explicit workflow stages. |
| Full omnichannel CRM, shared inbox, chatbot, and AI-content suite | Adjacent marketing tools bundle these functions. | They require a different data model, inbound-message ownership, consent model, support workflow, and policy review; none is an active requirement. | Maintain the focused recurring group-posting workflow; assess such products only after a separate discovery decision. |
| Cross-tenant agency/client workspaces and approval chains | Agencies often request client collaboration. | Roles, ownership, auditability, white-labeling, and content approvals substantially expand the tenancy model. | Current admins manage operational data; scope a client-workspace capability only when it becomes an active requirement. |

## Feature Dependencies

```
Authenticated user
    └──requires──> Messenger account connection
                         └──requires──> Account session/worker health
                         └──enables──> Group synchronization
                                             └──enables──> Group selection

Reusable ad (text + optional images) ──together with──> Group selection
    └──enables──> Recurring schedule (days, times, timezone)
                         └──requires──> Background dispatcher
                                              └──creates──> Per-group send log
                                                                  └──feeds──> History and dashboard statistics

Message balance/subscription ──gates──> Scheduled dispatch
```

### Dependency Notes

- **Schedules require a valid ad, messenger account, and selected groups:** those identifiers are persisted on every schedule; the platform cannot calculate useful work without all three.
- **Group selection requires account connection and synchronization:** groups are messenger-account resources, not user-entered destination strings.
- **History requires execution, not merely a schedule:** a `SendLog` is created by dispatch/send processing and contains the observed result and snapshot data.
- **Billing gates dispatch:** the worker checks/deducts message balance around sending, so billing consistency is a core workflow dependency, not just a pricing-page concern.
- **Multi-messenger is not a superficial toggle:** Telegram uses Celery-delivered work while WhatsApp and MAX use per-account Redis queues/workers; connector lifecycle remains part of delivery behavior.

## Product Definition for the Current Brownfield State

### Present Product (implemented)

- [x] Identity and account recovery — necessary to operate a customer SaaS safely.
- [x] Messenger account connection and group synchronization — defines valid destinations.
- [x] Ad/media authoring — defines reusable outbound content.
- [x] Timezone-aware recurring schedules and background execution — delivers the core value.
- [x] Per-group send logs, history filters, and dashboard/account statistics — makes execution inspectable.
- [x] Subscription/message-balance controls, administration, and monitoring — supports sustainable operation.

### Not Active Requirements (possible future scope only)

- [ ] Calendar/queue visual planning and campaign-level reporting — adjacent scheduling UX; no active requirement or implementation was found.
- [ ] Formal approval workflow, agency/client workspaces, and role granularity — plausible agency extension, but materially changes tenancy and has not been requested.
- [ ] Official-API-specific consent/template management for one-to-one marketing — compliance-sensitive and distinct from the current group-posting model.
- [ ] CRM, unified inbound inbox, chatbot, AI generation, or cross-channel analytics — broad marketing-suite capabilities deliberately not inferred from competitor feature lists.

## Feature Prioritization Matrix

This matrix records the importance of current capabilities; it is **not** a new build backlog.

| Feature | User Value | Implementation Cost | Current Priority / State |
|---------|------------|---------------------|--------------------------|
| Account connection plus group sync | HIGH | HIGH | P1 — implemented |
| Ad/media authoring | HIGH | MEDIUM | P1 — implemented |
| Timezone-aware recurring schedules | HIGH | HIGH | P1 — implemented |
| Reliable dispatch with send logs | HIGH | HIGH | P1 — implemented |
| Balance/subscription enforcement | HIGH | HIGH | P1 — implemented |
| Three-messenger delivery | HIGH | HIGH | P2 differentiator — implemented |
| Operations monitoring | MEDIUM | MEDIUM | P2 — implemented |
| CRM/inbox/AI/approval suite | UNCERTAIN | HIGH | P3 — future-only, no requirement |

**Priority key:** P1 = indispensable to the documented core value; P2 = valuable implemented differentiation; P3 = intentionally uncommitted future scope.

## Ecosystem Positioning

Comparable marketing automation products commonly market centralized campaign authoring, scheduling, multi-account/channel handling, analytics, and collaboration. Broadcaster already covers the subset aligned with its declared value: reusable ads, connected accounts/groups, recurring time-based execution, and per-send history. It should not be evaluated as incomplete merely because it does not offer a contact CRM, shared inbox, AI authoring, or approval boards—those solve different workflows and would require explicit product validation.

## Sources

- Internal implementation evidence: [`PROJECT.md`](/root/broadcaster/.planning/PROJECT.md), [`README.md`](/root/broadcaster/README.md), [`Schedule`](/root/broadcaster/app/models/schedule.py), [`SendLog`](/root/broadcaster/app/models/send_log.py), [`Celery tasks`](/root/broadcaster/app/worker/tasks.py), and [`history pages`](/root/broadcaster/app/pages/history.py). **HIGH** confidence for implemented-state claims.
- [WhatsApp Business Policy](https://whatsappbusiness.com/policy/) and [WhatsApp’s business-chat announcement](https://about.fb.com/news/2025/04/ways-to-manage-your-businesses-chats-on-whatsapp/). **MEDIUM** confidence for compliance-boundary observations; policy interpretation should be revisited before any recipient-messaging feature.
- [Telegram Spam FAQ](https://telegram.org/faq_spam) and [Telegram FAQ](https://telegram.org/faq). **MEDIUM** confidence for account-risk observations.
- Public competitor marketing pages found through web research. **MEDIUM** confidence for broad ecosystem positioning only; no feature is inferred as a requirement from them.

---
*Feature research for: Broadcaster — scheduled advertising posts to messenger groups*
*Researched: 2026-08-03*

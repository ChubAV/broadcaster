# Roadmap: Broadcaster

## Overview

This retrospective roadmap records the implemented v1 baseline as six complete, vertical user capabilities. It is a current-state map, not a plan for new work: all listed requirements are already delivered, and no future reliability, hardening, or expansion work is included.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): retrospective baseline capabilities.
- Decimal phases (2.1, 2.2): reserved for any future approved insertions.

- [x] **Phase 1: Secure Access & Scheduling Profile** - Users can establish and recover authenticated access with a personal scheduling timezone.
- [x] **Phase 2: Advertisement Library** - Users can manage reusable advertising content and its images.
- [x] **Phase 3: Messenger Accounts & Group Targeting** - Users can connect supported messengers and select synchronized groups.
- [x] **Phase 4: Scheduled Multi-Messenger Delivery** - Users can schedule advertisements and see their automated delivery outcomes.
- [x] **Phase 5: Subscription & Message Balance** - Users can understand and fund the usage controls that govern the service.
- [x] **Phase 6: Administration & Operations** - Administrators and operators can manage the service and observe its operation.

## Phase Details

### Phase 1: Secure Access & Scheduling Profile
**Goal**: Users can securely access their account and set the timezone used for their schedules.
**Mode:** mvp
**Depends on**: Nothing (retrospective baseline entry point)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, PROF-01
**Success Criteria** (what must be TRUE):
  1. A user can register with an email and password, then confirm that email with a code.
  2. A user can sign in and retain an authenticated session.
  3. A user who has forgotten a password can reset it using a code sent by email.
  4. A user can choose the timezone applied when their schedules are evaluated.
**Plans**: Baseline complete (retrospective; no plan artifacts)
**UI hint**: yes

### Phase 2: Advertisement Library
**Goal**: Authenticated users can create and maintain the reusable advertisement content they will send.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: ADS-01, ADS-02, ADS-03
**Success Criteria** (what must be TRUE):
  1. A user can create and edit their advertising announcements.
  2. A user can attach an image stored in the S3-compatible media store to an announcement.
  3. A user can browse and delete only their own announcements.
**Plans**: Baseline complete (retrospective; no plan artifacts)
**UI hint**: yes

### Phase 3: Messenger Accounts & Group Targeting
**Goal**: Users can connect supported messenger accounts and choose the synchronized groups that will receive advertisements.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: ACCT-01, ACCT-02, ACCT-03, ACCT-04, GRP-01, GRP-02, GRP-03
**Success Criteria** (what must be TRUE):
  1. A user can connect Telegram, WhatsApp, or MAX accounts through their respective supported account flows.
  2. A user can see an owned account's connection state and disconnect it when needed.
  3. A user can synchronize the groups available to a connected messenger account and see diagnostics from the synchronization.
  4. A user can browse and select the synchronized groups to use as advertising destinations.
**Plans**: Baseline complete (retrospective; no plan artifacts)
**UI hint**: yes

### Phase 4: Scheduled Multi-Messenger Delivery
**Goal**: Users can schedule an advertisement to selected groups and inspect the outcome of automated delivery across supported messengers.
**Mode:** mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: SCH-01, SCH-02, SCH-03, SEND-01, SEND-02, SEND-03, SEND-04
**Success Criteria** (what must be TRUE):
  1. A user can create a schedule that links one advertisement to chosen messenger groups.
  2. A user can set recurring send days and times in their own timezone, and can enable, disable, edit, or delete the schedule.
  3. When a schedule becomes due, the system queues and sends the advertisement to its Telegram, WhatsApp, and MAX group destinations through the appropriate adapters or workers.
  4. A user can view each delivery's resulting status in history, including the advertisement and recipient snapshots captured at send time.
**Plans**: Baseline complete (retrospective; no plan artifacts)
**UI hint**: yes

### Phase 5: Subscription & Message Balance
**Goal**: Users can select and fund the service capacity available for their advertising workflow.
**Mode:** mvp
**Depends on**: Phase 1, Phase 2, Phase 3, Phase 4
**Requirements**: BILL-01, BILL-02, BILL-03, BILL-04
**Success Criteria** (what must be TRUE):
  1. A user can view the Free, Basic, and Pro plans alongside their current subscription.
  2. The service applies the subscription's available limits to advertisements, groups, and platform usage.
  3. A user can add message credit through the integrated payment flow.
  4. The service records the message-balance deductions and related balance operations.
**Plans**: Baseline complete (retrospective; no plan artifacts)
**UI hint**: yes

### Phase 6: Administration & Operations
**Goal**: Administrators can support the service and operators can observe its application and delivery infrastructure.
**Mode:** mvp
**Depends on**: Phase 3, Phase 4, Phase 5
**Requirements**: ADMIN-01, ADMIN-02, OPS-01, OPS-02, OPS-03
**Success Criteria** (what must be TRUE):
  1. An administrator can view users and manage their account states and subscriptions.
  2. An administrator can inspect delivery history and the group information collected by the service.
  3. An operator can inspect application and background-process metrics in Prometheus and Grafana, and investigate centralized logs in Loki.
  4. An operator can run the system in development or production using the provided Docker Compose and Nginx deployment configurations.
**Plans**: Baseline complete (retrospective; no plan artifacts)
**UI hint**: yes

## Progress

**Execution Order:** Historical baseline capabilities are recorded in dependency order: 1 → 2 → 3 → 4 → 5 → 6.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Secure Access & Scheduling Profile | Baseline (no plans) | Complete | 2026-08-03 |
| 2. Advertisement Library | Baseline (no plans) | Complete | 2026-08-03 |
| 3. Messenger Accounts & Group Targeting | Baseline (no plans) | Complete | 2026-08-03 |
| 4. Scheduled Multi-Messenger Delivery | Baseline (no plans) | Complete | 2026-08-03 |
| 5. Subscription & Message Balance | Baseline (no plans) | Complete | 2026-08-03 |
| 6. Administration & Operations | Baseline (no plans) | Complete | 2026-08-03 |

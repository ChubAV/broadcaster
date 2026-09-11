---
status: investigating
trigger: "Расписание для Telegram не сработало в 17:30 по Москве (14:30 UTC); check_schedules выполняется, но возвращает due_count: 0."
created: 2026-08-03
updated: 2026-09-11T06:26:15Z
audit_acknowledged:
  milestone: v2.0
  at: 2026-08-25
  status: investigating
---

# Debug Session: Telegram schedule not due

## Symptoms

- expected_behavior: Telegram schedule executes at 17:30 Europe/Moscow, corresponding to 14:30 UTC.
- actual_behavior: Celery Beat dispatches check-schedules every 30 seconds, but the default worker logs due_count=0 and no_tasks_to_dispatch at and after 14:30 UTC.
- error_messages: No exception is present in the supplied logs.
- timeline: Production deployment is newly started; whether this schedule path worked previously is unknown.
- reproduction: Create/enable a Telegram schedule for 17:30 Moscow and observe check_schedules around 14:30 UTC.

## Current Focus

- hypothesis: >-
    SPLIT INTO TWO, because the production census of 2026-09-11 answered one question and
    raised another. (1) FOR THE 2026-08-03 OCCURRENCE — UNDECIDABLE. Dispatch is healthy today
    (34572 sends in 7 days, latest 2s before measurement), every account is active, no schedule
    is overdue, and the 17:30 Moscow row of that day cannot be identified five weeks on. Neither
    branch (A) nor (B) can be confirmed for that occurrence by any measurement still available.
    (2) A LIVE DEFECT OF THE SAME SHAPE WAS FOUND WHILE LOOKING — sched=48 is is_active=true
    with next_run_at=NULL and days_of_week=[]; compute_next_run_at returns None on an empty day
    list, the due predicate never matches NULL, and the suppression branch that would recompute
    next_run_at never runs because the row is never selected. The row is permanently dead while
    the interface shows it active.
- test: >-
    For (2): confirm no constraint, repair job, or interface warning forbids or surfaces
    `is_active = true AND next_run_at IS NULL`, and decide the owner's repair for sched=48.
- expecting: >-
    For (1): nothing further — the evidence is gone, and any root cause recorded for it would be
    inference. For (2): a gate that makes the dead combination impossible or visible.
- next_action: >-
    OWNER DECISION, not investigation. Either close this session as not-reproducible and open a
    fresh one scoped to the sched=48 class, or re-scope this session to that class. Separately,
    sched=48 is a real production row that will never fire until its days_of_week is set.
- bug_class: >-
    (1) unclassifiable — no longer observable. (2) bohrbug — deterministic and permanent for any
    row that reaches the state.
- reasoning_checkpoint:
- tdd_checkpoint:

## Evidence

- timestamp: 2026-08-03T00:00:00Z
  checked: Phase 0 semantic recall and durable debug knowledge base.
  found: The mempalace CLI is unavailable, no MemPalace wing is configured, and .planning/debug/knowledge-base.md does not exist.
  implication: No known-pattern candidate is available; proceed with direct code-path evidence. This is a logged fallback, not a silent skip.

- timestamp: 2026-08-03T00:00:01Z
  checked: Codebase identifier search for due_count, due queries, next_run_at, schedule creation, and check_schedules.
  found: Production checking flows through app.worker.tasks.check_schedules_async to app.application.scheduling.use_cases.collect_due_schedules; schedules are written from both API and page routes using app.services.schedule_service.compute_next_run_at. A separate repository due query exists but is not on the logged worker path.
  implication: Trace the application use case first and compare both production writer paths; repository-only fixes would not affect the reported execution path.

- timestamp: 2026-08-03T00:00:02Z
  checked: Complete schedule model, next-run calculator, API/page writers, worker checker, due collector, repository, and directly relevant tests.
  found: collect_due_schedules queries only is_active=true and next_run_at<=now. However check_schedules_async logs due_count=len(tasks), after due schedules can be consumed without tasks because the account is absent/inactive, billing denies sending, or group_ids is empty. Every such due schedule is advanced to its next occurrence before due_count=0 is logged.
  implication: The supplied log cannot distinguish a time/query miss from downstream suppression; the original inference that failure is necessarily before due selection is unsupported.

- timestamp: 2026-08-03T00:00:03Z
  checked: Existing scheduling coverage.
  found: Tests verify Moscow conversion and worker dispatch separately, but no test reproduces a fixed Moscow schedule from creation-time computation through the due collector at its exact UTC firing time; fixtures directly force next_run_at into the past and supply active accounts, populated group_ids, and allowed billing.
  implication: Run an exact fixed-time reproduction. Spectrum-based fault localization is skipped because there is no known failing test/per-test coverage spectrum yet.

- timestamp: 2026-08-03T00:00:04Z
  checked: Initial relevant pytest run and repository status.
  found: pytest could not start because uv attempted to create a lock under the read-only global cache. The worktree also contains numerous pre-existing staged/untracked planning files unrelated to this debug session.
  implication: Re-run with a writable task-specific cache and preserve all unrelated user changes; the failure is test infrastructure, not evidence about the scheduling hypothesis.

- timestamp: 2026-08-03T00:00:05Z
  checked: Relevant pytest retry with a writable uv cache.
  found: uv next attempted to create its managed Python directory under read-only /home/orca/.local/share/uv/python, so tests still did not start.
  implication: Use the existing project interpreter/virtualenv if present or redirect uv's managed-Python directory; this remains an environment-only test blocker.

- timestamp: 2026-08-03T00:00:06Z
  checked: Available Python runtimes.
  found: System Python is 3.14.4, the project pins Python 3.12, no .venv exists, and uv cannot find an installed 3.12 interpreter.
  implication: A task-specific uv-managed Python installation is required to execute the project tests faithfully.

- timestamp: 2026-08-03T00:00:07Z
  checked: Relevant schedule service, due collector, and worker tests under the project-pinned Python 3.12 environment.
  found: All 17 selected tests pass. uv provisioned an ignored project .venv plus task-specific caches to make execution possible.
  implication: Existing coverage detects no regression, but it does not reproduce the exact reported fixed-time path; proceed with the fixed-time experiment.

- timestamp: 2026-08-03T00:00:08Z
  checked: compute_next_run_at for Monday 2026-08-03 at 14:00 UTC with days=[Monday], times=[17:30], timezone=Europe/Moscow.
  found: The function returns exactly 2026-08-03T14:30:00+00:00.
  implication: Timezone conversion in the calculator is correct for the reported date; the calculator portion of the normalization hypothesis is falsified.

- timestamp: 2026-08-03T00:00:09Z
  checked: Temporary fixed-time integration test tests/test_application/test_telegram_due_repro_tmp.py.
  found: The test process produced no output and did not complete within approximately 60 seconds; it was interrupted. The earlier 17-test subset completed successfully, so this is not a general Python provisioning failure.
  implication: Run one bounded verbose attempt to locate the hang; do not wait indefinitely or interpret the hang as scheduling evidence.

- timestamp: 2026-08-03T00:00:10Z
  checked: Bounded verbose retry of the fixed-time collector reproduction.
  found: pytest collected the single test and entered test_moscow_1730_is_due_at_1431_utc, but timed out after 15 seconds (exit 124) before reaching an assertion.
  implication: The local test is blocked inside setup/execution and cannot currently confirm PostgreSQL/collector behavior. A checkpoint is required rather than waiting further.

- timestamp: 2026-08-03T00:00:12Z
  checked: Bounded retry with pytest --setup-show under the provisioned Python 3.12 virtualenv.
  found: The test timed out after 20 seconds while pytest displayed SETUP F _function_scoped_runner; db_session setup and the test body were never entered.
  implication: The hang is in the pytest-asyncio fixture runner/harness before scheduling code, so it is not evidence for or against due selection. One self-contained test can bypass this specific blocker.

- timestamp: 2026-08-03T00:00:13Z
  checked: Self-contained fixed-time test using its own in-memory async engine rather than the shared db_session fixture.
  found: Pytest again timed out after 20 seconds while executing the test under _function_scoped_runner; no assertion result was produced.
  implication: Removing the shared fixture did not remove the blocker. A direct asyncio invocation is the last bounded discriminator before requesting production evidence.

- timestamp: 2026-08-03T00:00:14Z
  checked: Direct asyncio.run invocation of the identical self-contained reproduction, outside pytest.
  found: The coroutine produced no output and timed out after 15 seconds (exit 124).
  implication: The blocker is not limited to pytest-asyncio; this environment cannot currently execute the async database reproduction. Stop local retries and require production row/state evidence to distinguish the remaining branches.

- timestamp: 2026-08-03T00:00:15Z
  checked: Exact production models and billing decision path for checkpoint preparation.
  found: The due predicate uses schedules.is_active and schedules.next_run_at; downstream suppression depends on messenger_accounts.status, schedules.group_ids, and check_balance_cached. Billing permits only message_balances.is_unlimited=true or balance>0, but Redis key balance:<user_id> can supply the cached decision.
  implication: One read-only joined row plus the optional Redis cache value is sufficient to distinguish every remaining branch without changing production state.

- timestamp: 2026-08-03T14:31:05Z
  observation: Celery Beat dispatches app.worker.tasks.check_schedules and the default worker executes it successfully.
  implication: Beat routing and the default worker are operational.

- timestamp: 2026-08-03T14:31:05Z
  observation: check_schedules logs now=2026-08-03T14:31:05+00:00 and due_count=0.
  implication: Failure occurs before dispatch to the Telegram queue.


- timestamp: 2026-09-11T06:26:15Z
  checked: >-
    Read-only production census requested by the 2026-08-03 checkpoint, executed against the
    live database (working tree and prod share one DATABASE_URL). 104 schedules joined to
    messenger_accounts and ads; SendLog counted by age.
  found: >-
    DISPATCH IS HEALTHY TODAY. 147936 send-log rows total; 4851 in the last 24h, 34572 in the
    last 7 days. The most recent row landed 2 seconds before the measurement (sched=43). Every
    messenger_account is status=active (max 4, tg_user 4, wa 4) — the account-status suppression
    sub-branch of hypothesis (B) does not hold on today's tree. Zero schedules are overdue
    (is_active AND next_run_at <= now), and zero active schedules are cut by the
    account/ad/group filter.
  implication: >-
    The originally reported symptom (due_count=0 while a schedule was believed active) is NOT
    reproducible on today's tree by either branch as originally framed.

- timestamp: 2026-09-11T06:26:15Z
  checked: The specific 17:30 Europe/Moscow row named by the original report.
  found: >-
    Two schedules now carry a 17:3x time — sched=88 (times 09:00, 12:30, 14:30, 17:30, tz
    Europe/Moscow, tg_user/active, 63 groups, next_run_at 2026-09-11T09:30Z) and sched=41
    (17:33, tg_user/active, 18 groups, next_run_at 2026-09-11T07:45Z). BOTH are healthy and
    advancing. Whether either IS the row from 2026-08-03 cannot be established: schedules carry
    no creation stamp in this schema and five weeks have passed.
  implication: >-
    ⚠️ THE ORIGINAL INCIDENT'S EVIDENCE HAS EXPIRED. Branch (A) vs (B) cannot be discriminated
    FOR THE 2026-08-03 OCCURRENCE by any measurement available today. Any root cause recorded
    for that occurrence would be inference, not observation, and this session must not pretend
    otherwise.

- timestamp: 2026-09-11T06:26:15Z
  checked: >-
    Census cross-check of is_active against next_run_at, looking for rows the due predicate can
    never select.
  found: >-
    ANOMALY, AND IT IS A LIVE INSTANCE OF BRANCH (A). next_run_at IS NULL on 40 rows while
    is_active=False on 39 — exactly one row is ACTIVE with a NULL next_run_at: sched=48
    (ad=14, acct=28 max/active, 1 group, times ['09:00','15:15'], tz Europe/Moscow) and
    CRUCIALLY days_of_week=[] — an EMPTY day list.
  implication: >-
    This row can never be dispatched and can never repair itself. The due query filters
    `is_active = true AND next_run_at <= now`; in SQL `NULL <= now` is never true, so the row is
    never selected. Because it is never selected, the suppression branch of
    collect_due_schedules — the only code path that RECOMPUTES next_run_at — never runs on it
    either. The row is permanently and silently dead while the interface shows it as active.

- timestamp: 2026-09-11T06:26:15Z
  checked: app/services/schedule_service.py compute_next_run_at, by reading the source.
  found: >-
    `if not days_of_week or not times_of_day: return None` (lines 16-17). An empty day list
    yields None, which is persisted to schedules.next_run_at.
  implication: >-
    MECHANISM IDENTIFIED for the sched=48 class: a schedule saved active with an empty
    days_of_week gets next_run_at=NULL and falls out of the due predicate forever. The gap is
    that nothing forbids the combination `is_active=true` + `next_run_at IS NULL`, and nothing
    surfaces it — neither a constraint, nor a periodic repair, nor an interface warning.
    ⚠️ THIS IS NOT PROOF THAT THE 2026-08-03 OCCURRENCE HAD THIS CAUSE: that row's
    days_of_week/next_run_at at the time were never captured. It is a live defect of the same
    SHAPE the session was hunting, found while looking for that one.

## Eliminated

- hypothesis: Europe/Moscow conversion computes a time other than 14:30 UTC for Monday 17:30.
  evidence: A fixed call at 2026-08-03 14:00 UTC returned exactly 2026-08-03T14:30:00+00:00.
  timestamp: 2026-08-03T00:00:08Z

- hypothesis: Celery Beat is not running.
  reason: Logs show check-schedules dispatched every 30 seconds.

- hypothesis: check-schedules is routed to a missing worker.
  reason: celery-worker-default executes the task and logs its result.

## Resolution

- root_cause:
- fix:
- verification:
- files_changed:

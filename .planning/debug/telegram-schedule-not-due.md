---
status: investigating
trigger: "Расписание для Telegram не сработало в 17:30 по Москве (14:30 UTC); check_schedules выполняется, но возвращает due_count: 0."
created: 2026-08-03
updated: 2026-08-03T00:00:15Z
---

# Debug Session: Telegram schedule not due

## Symptoms

- expected_behavior: Telegram schedule executes at 17:30 Europe/Moscow, corresponding to 14:30 UTC.
- actual_behavior: Celery Beat dispatches check-schedules every 30 seconds, but the default worker logs due_count=0 and no_tasks_to_dispatch at and after 14:30 UTC.
- error_messages: No exception is present in the supplied logs.
- timeline: Production deployment is newly started; whether this schedule path worked previously is unknown.
- reproduction: Create/enable a Telegram schedule for 17:30 Moscow and observe check_schedules around 14:30 UTC.

## Current Focus

- hypothesis: The production schedule was either (A) not selected because its persisted is_active/next_run_at state failed the due predicate, or (B) selected and advanced but emitted no task because its account was absent/inactive, group_ids was empty, or the cached billing decision denied sending.
- test: Run the read-only schedule/account/balance join supplied in the checkpoint for the affected 17:30 Moscow schedule, and read Redis key balance:<user_id> if present.
- expecting: A next_run_at later than the missed occurrence together with zero tasks confirms selection plus suppression; an unchanged next_run_at at/before 14:30 UTC confirms the due query failed to return the row. The joined account/group/balance fields and Redis value discriminate the suppression branches.
- next_action: Human action required: return the read-only SQL row and optional Redis balance cache value from production; do not apply a code fix until one branch is observed.
- bug_class: bohrbug (leading classification; due_count=0 is deterministic for the persisted schedule at a known timestamp)
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

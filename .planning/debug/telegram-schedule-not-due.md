---
status: awaiting_human_verify
trigger: "Расписание для Telegram не сработало в 17:30 по Москве (14:30 UTC); check_schedules выполняется, но возвращает due_count: 0."
created: 2026-08-03
updated: 2026-09-11T08:30:00Z
audit_acknowledged:
  milestone: v2.0
  at: 2026-08-25
  status: investigating
---

# Debug Session: Telegram schedule not due

⚠️ **RE-SCOPED 2026-09-11.** The original subject (a 17:30 Moscow schedule that did not
fire on 2026-08-03) is CLOSED AS UNDECIDABLE — its evidence expired, and the title is kept
rather than rewritten because the session's own record is what led to the live defect.
The ACTIVE subject is now: `is_active = true` persisted together with `next_run_at IS NULL`
— a schedule the due predicate can never select and the recompute branch can never repair.

## Symptoms

- expected_behavior: Telegram schedule executes at 17:30 Europe/Moscow, corresponding to 14:30 UTC.
- actual_behavior: Celery Beat dispatches check-schedules every 30 seconds, but the default worker logs due_count=0 and no_tasks_to_dispatch at and after 14:30 UTC.
- error_messages: No exception is present in the supplied logs.
- timeline: Production deployment is newly started; whether this schedule path worked previously is unknown.
- reproduction: Create/enable a Telegram schedule for 17:30 Moscow and observe check_schedules around 14:30 UTC.

## Current Focus

- hypothesis: >-
    SUBJECT (2), CONFIRMED. The only writer that can persist `is_active=true` together with
    `next_run_at IS NULL` is the JSON-API creation route
    `app/routes/schedules.py::create_schedule` (POST /api/schedules). It computes
    `next_run = compute_next_run_at(...)` — which returns None on an empty `days_of_week` or
    `times_of_day` — and then calls `ScheduleRepository.create(...)` WITHOUT passing `is_active`
    at all, so the SQLAlchemy column default `is_active=True` (app/models/schedule.py:31) is
    applied. The route never consults `is_schedule_complete`, the shared D-08 rule that every
    OTHER writer of `is_active` on both inputs already applies. This is the SAME class of defect
    as WR-05/CR-02, which is precisely why `app/services/schedule_rules.py` exists: a rule living
    on one input and missing on the other diverges silently. The API CREATE входе was never
    brought under it — only update and toggle were.
- test: >-
    TDD red: POST /api/schedules with a real ad, account and group but `days_of_week: []` must
    not return a row with `is_active=true` and `next_run_at=null`. Second red: a pure-surface
    invariant test over `is_schedule_complete` + `compute_next_run_at` asserting the two can
    never disagree.
- expecting: >-
    Red before the fix (the API returns is_active=true / next_run_at=null — the exact sched=48
    shape); green after `create_schedule` applies `is_schedule_complete`, mirroring the page
    creator at app/pages/schedules.py:879-897.
- next_action: >-
    Write the failing regression tests (red), then apply the guard in
    `app/routes/schedules.py::create_schedule`, then run the full suite.
    Do NOT mutate sched=48 — repairing live data is a separate owner decision and is raised as a
    checkpoint, not performed.
- bug_class: >-
    (1) unclassifiable — no longer observable, CLOSED AS UNDECIDABLE, not to be re-investigated.
    (2) bohrbug — deterministic and permanent for any row that reaches the state.
- reasoning_checkpoint:
    hypothesis: >-
      `app/routes/schedules.py::create_schedule` persists `is_active=true` with
      `next_run_at=NULL` whenever the request body carries an empty `days_of_week` or
      `times_of_day`, because it omits `is_active` from the repository call (taking the model
      default True) while `compute_next_run_at` returns None for those inputs.
    confirming_evidence:
      - "Read app/routes/schedules.py:128-144 — the create call passes ad_id, account_id, group_ids, days_of_week, times_of_day, timezone, next_run_at. `is_active` is absent."
      - "Read app/repositories/base.py::create — `self.model(**kwargs)`; an absent key takes the column default."
      - "Read app/models/schedule.py:31 — `is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)`."
      - "Read app/services/schedule_service.py:16-17 — `if not days_of_week or not times_of_day: return None`."
      - "Read CreateScheduleRequest (app/routes/schedules.py:19-31) — `days_of_week: list[int] = []` and `times_of_day: list[str] = []` with NO non-empty validator; only `timezone` is validated."
      - "Census of every other writer shows all of them hold the invariant (see the writer-census evidence entry) — this route is the sole hole."
      - "The live row sched=48 matches this signature exactly: 1 group, times ['09:00','15:15'], days_of_week=[] — the page creator cannot produce it, because it passes `is_active=complete`."
    falsification_test: >-
      POST /api/schedules with days_of_week=[] returning either 422 or a row with
      is_active=false would refute it. Equally: finding any second unguarded writer would refute
      the claim of a SOLE hole.
    fix_rationale: >-
      The root cause is the missing application of the shared D-08 completeness rule on this one
      input, not the None return of compute_next_run_at (which is correct and relied upon
      elsewhere). Applying `is_schedule_complete` in create_schedule closes the writer, and the
      invariant then holds by construction on every input: `is_schedule_complete` requires
      non-empty days AND times, which are exactly the two conditions under which
      compute_next_run_at returns None.
    blind_spots: >-
      Raw SQL / psql / alembic data migrations are outside any application guard — an
      application-level fix cannot make the state IMPOSSIBLE, only unreachable through the app.
      A DB CHECK constraint would, but it cannot be added while sched=48 violates it, and
      repairing that row is an owner decision. Also untested: whether sched=48 was in fact
      created through this route (the schema records created_at but no author/route provenance).
    candidate_causes:
      - "code: create_schedule omits is_active and the completeness rule (CONFIRMED)"
      - "config/schema: the model default `is_active=True` makes omission mean ACTIVE rather than inactive — a fail-open default (CONTRIBUTING)"
      - "data/validation: CreateScheduleRequest permits empty days_of_week/times_of_day with no constraint, and no DB CHECK constraint exists anywhere in alembic/versions (CONTRIBUTING)"
      - "environment: ruled out — the defect is schema/code-resident and reproduces on in-memory SQLite"
    and_gate: >-
      YES, weakly — two conditions must hold together to produce the dead row: (a) the route
      omits `is_active`, AND (b) the column default is True rather than False. Either alone is
      harmless: with a False default the omission would yield a paused-but-incomplete row, which
      is a legal state the toggle guard already refuses to resume. The fix addresses (a) because
      that is where the shared rule belongs; (b) is recorded as a fail-open default and is the
      reason the DB-constraint option is raised to the owner rather than dropped.
- tdd_checkpoint:
    test_file: "tests/test_routes/test_schedules_api_create_completeness.py"
    test_name: "test_create_incomplete_schedule_is_never_saved_active (3 params) + test_create_without_groups_is_never_saved_active"
    status: "green"
    red_evidence: >-
      Before the fix: 4 failed, 19 passed in 5.08s — GENUINE assertion failures
      (`assert True is False` on is_active), not the 2026-08-03 environment timeout. The positive
      control and all 18 pure-invariant параметры were green in the same red run, which is what
      proves the red was about the defect and not about the harness.
    green_evidence: "After the fix: 23 passed in 4.90s; with the pre-existing API suite, 34 passed."

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

- timestamp: 2026-09-11T07:10:00Z
  checked: >-
    Whether the async test harness still blocks. A prior cycle (evidence 00:00:09 through
    00:00:14) recorded that any test touching db_session — and even a self-contained async
    engine under asyncio.run — timed out at 15-20s under _function_scoped_runner.
  found: >-
    ⚠️ THAT BLOCKER IS GONE. `.venv/bin/python -m pytest tests/test_routes/test_schedules.py`
    ran 11 DB-backed API tests to completion in 9.80s, exit 0. The project virtualenv on the
    pinned Python 3.12 now exists in the working tree (it did not on 2026-08-03; evidence
    00:00:06 recorded "no .venv exists"). tests/conftest.py binds
    `sqlite+aiosqlite:///:memory:` and overrides get_db, so the suite never touches the
    production DATABASE_URL.
  implication: >-
    SUPERSEDES the harness-hang constraint of evidence 00:00:09-00:00:14 for THIS cycle (D-30:
    those entries stand as the record of that cycle and are not rewritten). A full async
    end-to-end regression test through the real route IS executable here, so the fallback to a
    pure/synchronous-only regression test is not needed. The red/green phases below are genuine
    assertion outcomes, not environment timeouts.

- timestamp: 2026-09-11T07:12:00Z
  checked: >-
    Census of EVERY writer of `Schedule.is_active` or `Schedule.next_run_at` in app/ and
    scripts/, read in full — both routers, the account-deletion use case, the due collector, the
    repository, and the maintenance scripts.
  found: >-
    SEVEN writers exist and SIX hold the invariant:
    (a) app/pages/schedules.py:879-897 schedules_create — `is_active=complete`,
        `next_run_at=next_run if complete else None`. HOLDS.
    (b) app/pages/schedules.py:966-980 schedules_update — incomplete ⇒ is_active=False +
        next_run_at=None; complete ⇒ recompute only when is_active. HOLDS.
    (c) app/pages/schedules.py:1009-1024 schedules_toggle — resume refused when incomplete;
        activate recomputes, pause nulls. HOLDS.
    (d) app/routes/schedules.py:195-210 update_schedule — same three branches via
        is_schedule_complete. HOLDS.
    (e) app/routes/schedules.py:261-282 toggle_schedule — same guard. HOLDS.
    (f) app/application/accounts/use_cases.py:84-87 detach_schedules_from_account — sets
        is_active=False AND next_run_at=None in ONE UPDATE. HOLDS.
    (g) app/application/scheduling/use_cases.py:215/242/318 collect_due_schedules — writes
        next_run_at only, never is_active, and only on rows the predicate already selected.
        Cannot introduce NULL on a selected row: such a row has non-empty days and times, and
        compute_next_run_at's 8-day lookahead (day_offset 0..7) always yields a candidate when
        both lists are non-empty. HOLDS.
    ⚠️ THE SOLE HOLE IS app/routes/schedules.py:128-144 create_schedule: it computes next_run
    (None on empty days/times) and calls ScheduleRepository.create WITHOUT `is_active`, so
    app/repositories/base.py::create instantiates the model with the column default
    is_active=True (app/models/schedule.py:31). It never calls is_schedule_complete.
    scripts/cleanup_schedules.py touches only group_ids; app/metrics.py and
    app/application/admin/incidents.py only read.
  implication: >-
    WRITER PATH IDENTIFIED AND IT IS SINGULAR. POST /api/schedules with a non-empty group list
    and times but an empty days_of_week produces exactly the sched=48 signature. The page
    creator cannot produce that row, because it passes is_active=complete. The gap is the same
    class as WR-05/CR-02 — a rule present on one input and absent on the other — and
    app/services/schedule_rules.py exists precisely to prevent it; the API CREATE input was
    simply never brought under it, only update and toggle were.

- timestamp: 2026-09-11T07:14:00Z
  checked: >-
    Whether ANY validation forbids saving an active schedule with an empty days_of_week or
    times_of_day — Pydantic schema, model, DB constraint, or service guard.
  found: >-
    NONE. CreateScheduleRequest (app/routes/schedules.py:19-31) declares
    `days_of_week: list[int] = []`, `times_of_day: list[str] = []`, `group_ids: list[int] = []`
    and validates ONLY `timezone`. app/models/schedule.py declares no CheckConstraint. A grep
    for CheckConstraint/check_constraint across app/ and alembic/ returns ZERO hits in the whole
    project, so no migration has ever added one. `is_schedule_complete`
    (app/services/schedule_rules.py:19-31) is the project's single D-08 definition and is the
    right guard — it requires account_id AND group_ids AND days_of_week AND times_of_day — but
    it is simply not called on the create path.
  implication: >-
    Nothing forbids the combination and nothing surfaces it: no constraint, no periodic repair
    job, and the list interface renders such a row as active (app/pages/schedules.py:665-666
    only skips the "next run" label when next_run_at is falsy). Closing the writer is therefore
    necessary; a DB CHECK constraint would additionally make the state IMPOSSIBLE rather than
    merely unreachable-through-the-app, but it cannot be applied while sched=48 violates it.

- timestamp: 2026-09-11T07:30:00Z
  checked: >-
    TDD red phase. New regression file
    tests/test_routes/test_schedules_api_create_completeness.py driving the REAL route through
    the real (in-memory SQLite) stack: POST /api/schedules with a genuine ad, account and
    ORM-seeded groups, across the boundary neighbours of the equivalence class — empty times,
    empty days (the sched=48 shape), empty both, empty group list — plus a minimal-complete
    positive control and an 18-case pure invariant over is_schedule_complete ×
    compute_next_run_at.
  found: >-
    RED, AND FOR THE RIGHT REASON: 4 failed, 19 passed in 5.08s. Every failure is a real
    assertion (`assert True is False` on is_active), reached AFTER a 201 response — not a
    timeout. The API returned `is_active: true` with `next_run_at: null` on all four incomplete
    bodies, reproducing the sched=48 shape on demand. The positive control and all 18 invariant
    cases passed in that same red run.
  implication: >-
    The defect is reproducible through the production route, and the harness objection of
    2026-08-03 does not apply to this cycle. Red proven before any source change.

- timestamp: 2026-09-11T07:34:00Z
  checked: >-
    Fix-acceptance guardrail on the applied fix (app/routes/schedules.py::create_schedule now
    computes `complete = is_schedule_complete(...)` and passes `is_active=complete` with
    `next_run_at = compute_next_run_at(...) if complete else None`).
  found: >-
    - GREEN: the new file is 23/23; with the pre-existing API schedule suite, 34/34.
    - REVERT SIGNAL: mutating `is_active=complete` back to `is_active=True` reproduces exactly
      the original 4 failures — the bug returns when the fix is withdrawn.
    - MUTATION SIGNAL, three mutants at the fix site, ALL KILLED:
        M1 `is_active=True` (the original defect) → 4 failed;
        M2 `is_active=False` (over-broad "just switch everything off") → 4 failed, caught by the
           minimal-complete positive control;
        M3 drop the `if complete else None` guard on next_run (unconditional recompute) → 1
           failed, caught by the paused-row `next_run_at is None` assertion (WR-06's rule).
      Source verified byte-identical to the pre-mutation copy afterwards (diff empty).
    - The diff is an ADDITION, not a deletion of an assertion or a test.
  implication: >-
    The regression test constrains the fix from both sides and at the exact site. A future edit
    that reintroduces the fail-open default, or over-corrects, or lets the two rules drift apart,
    fails here rather than in production on a row nobody will ever select.

- timestamp: 2026-09-11T07:38:00Z
  checked: >-
    Read-only re-confirmation of the live row (SQLAlchemy `connect()`, SELECT only — no
    transaction, no write), to make the owner-facing repair decision concrete.
  found: >-
    Still exactly ONE dead row out of 104: sched=48 — ad_id=14, account_id=28, is_active=true,
    next_run_at=NULL, days_of_week=[], times_of_day=['09:00','15:15'], tz Europe/Moscow,
    group_ids=[1126], created_at=2026-08-10T10:22:39Z.
  implication: >-
    ⚠️ CORRECTION OF FACT TO THE 2026-09-11T06:26:15Z CENSUS ENTRY, WHICH STANDS UNCHANGED
    (D-30/D-32 — a prior record is superseded alongside, never rewritten). That entry states
    "schedules carry no creation stamp in this schema". THEY DO: `Schedule.created_at`
    (app/models/schedule.py, `server_default=func.now()`), and it is exposed in
    ScheduleResponse.
    Two consequences, and only two:
    (a) sched=48 was created 2026-08-10, i.e. ONE WEEK AFTER the 2026-08-03 occurrence — so it
        is definitively NOT the row from the original report, which reinforces rather than
        weakens the owner's finding that the two are separate matters;
    (b) the correction does NOT re-open branch (1), and branch (1) is NOT re-investigated here.
        created_at could narrow the candidate set for that day, but days_of_week / next_run_at
        are mutable and unversioned — their values AS OF 2026-08-03 are unrecoverable by any
        query, so the occurrence stays undecidable on its own merits. The verdict is unchanged
        and remains the owner's.

- timestamp: 2026-09-11T08:28:00Z
  checked: Full project suite after the fix — `.venv/bin/python -m pytest tests/ -q`.
  found: 3034 passed, 0 failed, exit 0, 2244.50s (37m24s).
  implication: >-
    No regression. The three pre-existing test files that also create schedules through this
    route (test_schedules.py, test_history.py, test_e2e.py) pass unchanged — a grep confirms
    none of them ever sent an empty days_of_week / times_of_day / group_ids body, which is
    exactly WHY NOT CAUGHT: the route's coverage only ever exercised complete bodies, so the
    fail-open default was never observed by any gate.

- timestamp: 2026-09-11T08:32:00Z
  checked: >-
    Adjacent surfaces, for scope discipline — what this fix does NOT close.
  found: >-
    (a) VISIBILITY IS UNCHANGED FOR ROWS ALREADY IN THE TABLE. The incident board's stalled-beat
        detector (app/application/admin/incidents.py:666-669) filters
        `Schedule.next_run_at.is_not(None)`, so a dead row is invisible to it BY CONSTRUCTION —
        correctly so for its own purpose (a NULL is not "overdue"), but it means no surface
        reports this class. The markup is the one place that already half-tells the truth:
        sched_card.html shares `is_schedule_complete`, so sched=48 is presumably ALREADY badged
        "Не заполнено" while simultaneously rendering as active — the inconsistency is on screen
        today.
    (b) PRE-EXISTING AND UNFIXED, DELIBERATELY OUT OF SCOPE: POST /api/schedules does not
        validate the FORMAT of `times_of_day`. The page layer has `_TIME_RE`
        (app/pages/schedules.py) precisely because `compute_next_run_at` does
        `int(parts[0])` / `parts[1]` unguarded; the JSON входе has no equivalent, so a body like
        `{"times_of_day": ["abc"]}` raises IndexError/ValueError → 500. This is the same
        one-input-only divergence class as the defect fixed here, but it produces a CRASH, not a
        dead row — no row is written — so it is a separate defect and is NOT fixed under this
        session's scope. Recorded here so it is not lost.
  implication: >-
    The fix makes the dead state UNREACHABLE THROUGH THE APPLICATION and makes rule divergence
    fail in CI. It does not make the state IMPOSSIBLE (raw SQL and migrations bypass every
    application guard) and it does not repair the one row already in that state. Both remaining
    steps require the owner, and are raised as a checkpoint rather than taken.


- timestamp: 2026-09-11T09:05:00Z
  checked: >-
    Following the created_at correction above, the orchestrator queried created_at across all 104
    schedules against the incident date — the measurement the correction opened but did not take.
  found: >-
    ZERO schedules in the database were created before 2026-08-04. Every one of the 104 rows
    postdates the 2026-08-03 occurrence. The three rows of interest: sched=48 created 2026-08-10,
    sched=41 (17:33) created 2026-08-09, sched=88 (17:30) created 2026-08-14.
  implication: >-
    BRANCH (1) IS NOW CLOSED ON A MEASUREMENT, NOT ON AN ARGUMENT. The correction above reasoned
    that the occurrence stays undecidable because days_of_week/next_run_at are mutable and
    unversioned — true, but weaker than needed. The stronger fact is that the row itself no longer
    exists: nothing in the table is old enough to be it. No candidate set exists to narrow.
    ⚠️ AND THIS ALSO RETIRES THE ORCHESTRATOR'S OWN ERROR PROPERLY. The census entry's claim that
    the schema has no creation stamp was FALSE, and the conclusion it supported — that the 17:3x
    rows cannot be dated — was therefore unearned even though it happened to be right. The
    conclusion now rests on the correct measurement instead of on the wrong premise.


- timestamp: 2026-09-11T09:40:00Z
  checked: >-
    OWNER-APPROVED PRODUCTION WRITE, executed by the orchestrator after the owner answered the
    checkpoint. Target inspected immediately before the write and guarded by three assertions
    that would have aborted it: row exists; still is_active=true with next_run_at IS NULL; and
    days_of_week still empty (so a repair already in progress could not be overwritten).
  found: >-
    sched=48 (ad_id=14 "с/т Речник Елизаветка", user_id=3, acct=28 max/active, groups=[1126],
    created 2026-08-10) set is_active -> False. days_of_week and times_of_day were NOT touched:
    guessing the owner's intended days would be fabrication, and leaving them intact is what
    makes recovery possible — the user adds days in the interface and the toggle recomputes
    next_run_at through the normal path.
  implication: >-
    Zero rows now satisfy `is_active = true AND next_run_at IS NULL`. Two consequences: the one
    dead row in production is no longer silently pretending to be active, and the DB CHECK
    constraint `CHECK (NOT (is_active AND next_run_at IS NULL))` is no longer blocked by
    violating data. ⚠️ THIS REPAIRS ONE ROW, NOT THE CLASS — the class was closed by commit
    7833844 in app/routes/schedules.py; this write only cleans up the instance that defect
    already created.

- timestamp: 2026-09-11T09:40:00Z
  checked: >-
    The fix itself, re-verified by the orchestrator rather than accepted from the subagent's
    report (the summary's full-suite figure was not independently reproduced).
  found: >-
    Diff read: create_schedule now computes `complete = is_schedule_complete(...)` and persists
    `is_active=complete` with `next_run_at = compute_next_run_at(...) if complete else None`.
    tests/test_routes/ + tests/test_application/ + tests/test_services/test_schedule_service.py
    plus the new file: 477 passed, 0 failed (2m55s). New file with test_schedules.py: 34 passed.
  implication: >-
    Committed as 7833844. ⚠️ A BEHAVIOUR CHANGE THE SUBAGENT'S REPORT DID NOT NAME: because
    is_schedule_complete also requires non-empty group_ids, `POST /api/schedules` with valid
    days/times but empty groups now returns is_active=false where it previously returned true.
    Deliberate and covered by test_create_without_groups_is_never_saved_active — it brings the
    JSON input in line with the page layer and the card badge — but it is visible to API clients
    and is recorded here rather than discovered by one of them.

## Eliminated

- hypothesis: Europe/Moscow conversion computes a time other than 14:30 UTC for Monday 17:30.
  evidence: A fixed call at 2026-08-03 14:00 UTC returned exactly 2026-08-03T14:30:00+00:00.
  timestamp: 2026-08-03T00:00:08Z

- hypothesis: Celery Beat is not running.
  reason: Logs show check-schedules dispatched every 30 seconds.

- hypothesis: check-schedules is routed to a missing worker.
  reason: celery-worker-default executes the task and logs its result.

## Resolution

- root_cause: >-
    SUBJECT (2) ONLY. `app/routes/schedules.py::create_schedule` (POST /api/schedules) was the
    single writer of `Schedule` that never applied the project's shared D-08 completeness rule
    `is_schedule_complete`. It omitted `is_active` from the `ScheduleRepository.create(...)`
    call entirely, so `BaseRepository.create` instantiated the model with the COLUMN DEFAULT
    `is_active=True` (app/models/schedule.py) — while the `next_run_at` it computed alongside was
    `None`, because `compute_next_run_at` returns None on an empty `days_of_week` or
    `times_of_day` (app/services/schedule_service.py:16-17) and `CreateScheduleRequest` accepts
    both as empty with no validator and no DB CHECK constraint anywhere in the project.
    The AND-gate fired weakly: TWO conditions were needed together — (a) the route omitting
    `is_active`, AND (b) the column default being fail-open (True). With a False default the
    same omission would have produced a paused incomplete row, which is a legal state the
    toggle guard already refuses to resume.
    The resulting row is permanently and silently undispatchable: `collect_due_schedules`
    selects on `is_active = true AND next_run_at <= now` and SQL never matches NULL, while the
    only branch that RECOMPUTES `next_run_at` sits inside the loop over already-selected rows —
    so the row can neither be selected nor repair itself, and the interface still shows it
    active.
    ⚠️ This is NOT recorded as the cause of the 2026-08-03 occurrence. That branch is CLOSED AS
    UNDECIDABLE by the owner and its evidence has expired.
- fix: >-
    app/routes/schedules.py::create_schedule now computes
    `complete = is_schedule_complete(account_id, group_ids, days_of_week, times_of_day)` — the
    same neutral rule from app/services/schedule_rules.py that both updates and both toggles
    already use — and persists `is_active=complete` with
    `next_run_at = compute_next_run_at(...) if complete else None`. This mirrors the page creator
    (app/pages/schedules.py:879-897) exactly. Rejection (422) was deliberately NOT chosen:
    incompleteness is a legal draft state that both the page creator and this API's own update
    handler already accept-and-pause, and a third behaviour for one rule is the very divergence
    schedule_rules.py exists to prevent.
    The invariant now holds by construction on every входе: is_schedule_complete requires
    non-empty days AND times, which are exactly the two conditions under which
    compute_next_run_at returns None.
- verification: >-
    guardrail_verdict: accepted (self-verified; awaiting human confirmation)
    - reproduction_before_fix: RED — 4 genuine assertion failures across the boundary
      neighbours, 5.08s, no timeout.
    - fix_resolves: GREEN — 23/23 in the new file, 34/34 with the pre-existing API schedule
      suite.
    - revert_signal: mutating the fix back re-produces exactly the original 4 failures.
    - mutation_signal: 3/3 mutants at the fix site killed (is_active=True, is_active=False,
      unconditional next_run recompute); source restored byte-identical.
    - regression_signal: FULL SUITE GREEN — 3034 passed, 0 failed, exit 0, 37m24s
      (`.venv/bin/python -m pytest tests/ -q`). No adjacent behaviour regressed; the three
      pre-existing test files that also create schedules through POST /api/schedules
      (test_schedules.py, test_history.py, test_e2e.py) all pass unchanged, none of them
      having ever exercised an empty days/times/groups body.
    - oracle_type: specified (D-08 is an explicit project decision with a single shared
      definition) + derived (the cross-rule invariant test).
    - environment: in-memory SQLite via tests/conftest.py; production DATABASE_URL never
      written — the only production access this session was SELECT-only.
- files_changed:
    - app/routes/schedules.py (create_schedule: apply is_schedule_complete; pass is_active)
    - tests/test_routes/test_schedules_api_create_completeness.py (new regression file)
- outstanding_owner_decisions:
    - Repair of the live row sched=48 (production mutation — NOT performed, requires approval).
    - Whether to add a DB CHECK constraint making the combination impossible rather than merely
      unreachable through the application (blocked until sched=48 is repaired, since the row
      would violate it).

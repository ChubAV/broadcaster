---
status: awaiting_human_verify
trigger: "Расписание для Telegram не сработало в 17:30 по Москве (14:30 UTC); check_schedules выполняется, но возвращает due_count: 0."
created: 2026-08-03
updated: 2026-09-11T13:05:00Z
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

<!-- CYCLE 3 (2026-09-11, post-checkpoint). Items A and B only. The prior cycle's focus block is
     superseded here; its record survives in Evidence and Resolution (D-30/D-32). -->

- subject: >-
    ITEM A — DB CHECK constraint `NOT (is_active AND next_run_at IS NULL)` on `schedules`
    (model + Alembic revision, CREATED NOT APPLIED). ITEM B — the adjacent value-domain defect
    on the JSON input of `POST /api/schedules`.
- hypothesis: >-
    ⚠️ ITEM B IS WIDER THAN THE CHECKPOINT NAMED, AND THE EXTRA PART RE-OPENS THE DEFECT THIS
    SESSION JUST CLOSED. The JSON input does not constrain `times_of_day` FORMAT (known: 500) and
    does not constrain `days_of_week` RANGE (NEW). Out-of-range days are non-empty, so
    `is_schedule_complete` answers True, while `compute_next_run_at` finds no candidate weekday in
    its 8-day window and returns None — producing `is_active=true` + `next_run_at=NULL`, the exact
    sched=48 shape, THROUGH THE ROUTE FIXED BY 7833844. The Resolution's claim that the invariant
    "holds by construction on every input" is therefore FALSE as written; it holds only for
    in-range days and well-formed times.
- test: >-
    TDD red, two files. (B) tests/test_routes/test_schedules_api_value_domain.py — POST/PUT with
    days [9]/[-1] must not save an active row with a null next run, and with times "abc"/"25:00"/
    "12:99"/"9:00" must answer 422 instead of crashing. (A) a model-level constraint test (INSERT
    of active+NULL must raise IntegrityError on the schema built from the model) plus a revision
    test driving real Alembic.
- expecting: >-
    (B) red as an assertion: days=[9] returns 201 with is_active=true/next_run_at=null; malformed
    times raise ValueError out of the ASGI transport (converted to an explicit pytest.fail so the
    red reads as an assertion, not as an environment error).
    (A) red as an assertion: the INSERT succeeds today where the test demands IntegrityError.
- next_action: >-
    DONE — both items implemented, full suite green (3163/0/exit 0). Nothing is committed: the
    changes sit in the working tree for the orchestrator to review, commit and independently
    verify. THE ONE ACTION LEFT IS THE OWNER'S AND IT IS NOT MINE TO TAKE: applying the Alembic
    queue. Production is on 0019, so 0020, 0021 and 0022 are all unapplied; revision 0022 has been
    run against NO database, only against throwaway SQLite files under pytest's tmp_path.
- bug_class: >-
    bohrbug, both items — deterministic and reproducible on demand from the input alone.
- reasoning_checkpoint:
    hypothesis: >-
      One RULE — the set of values `compute_next_run_at` can actually consume — lives on the page
      input only (`_TIME_RE`, `_clean_ints(low=0, high=6)`) and is absent from the JSON input.
      The two consequences differ only in which side of `compute_next_run_at` the bad value hits:
      a malformed TIME crashes the parser (500, no row written), an out-of-range DAY passes the
      parser and returns no candidate (201, dead row written).
    confirming_evidence:
      - "Measured, not inferred: days [9] and [-1] give is_schedule_complete=True with compute_next_run_at=None (probe output recorded in Evidence)."
      - "Measured: times 'abc' -> ValueError from int(parts[0]); '25:00' -> 'hour must be in 0..23'; '12:99' -> 'minute must be in 0..59'; '' -> ValueError. The session file previously said IndexError — true only for a value like '12' with no colon, where int(parts[0]) succeeds first."
      - "app/pages/schedules.py:854-855 cleans days with low=0/high=6 and times with _TIME_RE before saving; app/routes/schedules.py CreateScheduleRequest validates ONLY timezone."
      - "All 33 Schedule constructions in tests and every time/day literal in the suite are already in-domain, so the strict rule breaks no existing expectation."
    falsification_test: >-
      A 422 (or an is_active=false row) from POST with days=[9] today would refute it; so would
      finding an existing validator anywhere on the JSON path that already constrains the domain.
    fix_rationale: >-
      The rule is lifted into app/services/schedule_rules.py — the neutral module that exists
      precisely because a rule living on one input diverges silently (WR-05/CR-02) — and each
      input keeps the POLICY it already has for a malformed field value: the JSON layer answers
      422 (exactly what it already does for `timezone`), the page layer discards and keeps the
      rest (exactly what `_clean_times`/`_clean_ints` already do, because a form posts repeated
      fields and one bad value must not lose the others). ONE rule, two policies — not the
      WR-05 divergence, which was two different RULES. This is also why 422 is right here and was
      wrong for completeness: an incomplete schedule is a legal draft state, "abc" is not a time.
    blind_spots: >-
      The CHECK constraint is CREATED, NOT APPLIED — nothing here proves it runs on the boiler.
      Prod is on 0019 per the 0021 docstring, so 0020, 0021 and now 0022 are all unapplied; the
      queue is the owner's to run. Also: the constraint makes the dead row impossible but turns
      any remaining writer of that shape into a 500 IntegrityError, which is WHY item B's
      day-range half must land with it and not after it.
    candidate_causes:
      - "code: the JSON request models carry no value-domain validator (CONFIRMED, both fields)"
      - "code: is_schedule_complete tests only non-emptiness, so it disagrees with compute_next_run_at on out-of-range days (CONFIRMED, and this is what makes the dead row survivable)"
      - "config/schema: no DB constraint forbids the combination — nothing outside the application enforces it (CONFIRMED, item A)"
      - "data: rows already carrying out-of-domain values would violate the new constraint at upgrade time (addressed by the revision's backfill, not by hope)"
    and_gate: >-
      YES for the dead-row half: BOTH the missing range check AND the completeness rule's
      non-emptiness-only definition must hold together. Either alone is harmless — an in-range day
      always yields a candidate, and a stricter completeness rule would turn the bad day list into
      a paused row rather than a dead one. The fix takes the boundary because that is where the
      out-of-domain value enters; the constraint takes the other side so the combination is
      impossible rather than merely unreachable.
- tdd_checkpoint:
    test_file: "tests/test_routes/test_schedules_api_value_domain.py + tests/test_models/test_schedule_active_requires_next_run.py + tests/test_migrations/test_0022_schedules_active_requires_next_run.py"
    status: "green"
    red_evidence: >-
      31 failed / 78 passed in 30.46s BEFORE any source change, every failure a genuine assertion
      in three shapes: `Failed: DID NOT RAISE IntegrityError` (x3, the schema half),
      `assert not (True and None is None)` (the dead row through POST and through PUT), and
      `assert 500 == 422` (the crash on a malformed time). Positive controls and the 72-case pure
      invariant were green in that SAME red run, which is what proves the red was the defect and
      not the harness.
    red_evidence_migration_half: >-
      ⚠️ ORDERING STATED HONESTLY. The revision test file was written AFTER the revision, not
      before — only the MODEL half of item A got a written-first red. Its red is therefore
      demonstrated by reverting rather than by authoring order: emptying `upgrade()` to `pass`
      reproduces 5 failures, and four further mutants at the other load-bearing sites are killed
      too (see the 11:35 evidence entry). That is equivalent evidence of teeth, but it is not the
      same thing as a test written first, and it is not reported as if it were.
    green_evidence: >-
      value-domain file 102/102; model-constraint file 7/7; revision file 20/20; whole migration
      suite 122/122; tests/test_application 256/256. Full-suite figures under `full_suite_cycle_3`.

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

- timestamp: 2026-09-11T10:05:00Z
  checked: >-
    CYCLE 3, ITEM B. Direct probe of the two rules against the value domain, run under the project
    virtualenv against the real functions (no mocks): is_schedule_complete(1,[1],days,times)
    alongside compute_next_run_at(days, times, "Europe/Moscow").
  found: >-
    ⚠️ THE DEAD ROW IS STILL REACHABLE THROUGH THE ROUTE FIXED BY 7833844, AND THIS IS A
    MEASUREMENT, NOT AN INFERENCE. Probe output verbatim:
      days [9]      -> complete=True  next_run=None   DEAD_ROW=True
      days [-1]     -> complete=True  next_run=None   DEAD_ROW=True
      times ['abc'] -> complete=True  RAISED ValueError: invalid literal for int() with base 10: 'abc'
      times ['25:00'] -> RAISED ValueError: hour must be in 0..23
      times ['12:99'] -> RAISED ValueError: minute must be in 0..59
      times ['']      -> RAISED ValueError: invalid literal for int() with base 10: ''
      days 0..6 + ['09:00'] -> complete=True next_run=2026-09-12T06:00:00+00:00 (control, healthy)
    An out-of-range day number is NON-EMPTY, so `is_schedule_complete` answers True; but
    `compute_next_run_at` scans day_offset 0..7, never matches the weekday, and returns None at
    `if not candidates`.
  implication: >-
    ⚠️ CORRECTION OF FACT TO THE Resolution.fix TEXT, WHICH STANDS UNCHANGED ALONGSIDE (D-30/D-32).
    It claims "the invariant now holds by construction on every input: is_schedule_complete
    requires non-empty days AND times, which are exactly the two conditions under which
    compute_next_run_at returns None." THE SECOND HALF IS FALSE. Emptiness is not the only
    condition under which the function returns None — an out-of-range day list is the other, and
    nothing on the JSON input rejects it. The fix of 7833844 remains correct and necessary; its
    claimed COMPLETENESS was overstated. Consequence for scope: the day-range half is not
    "adjacent", it re-opens this session's own root-cause symptom, and it must land WITH the CHECK
    constraint rather than after it — otherwise the constraint converts a silent dead row into a
    500 IntegrityError on that input.

- timestamp: 2026-09-11T10:06:00Z
  checked: >-
    CYCLE 3, ITEM A. The checkpoint's stated premise — that
    tests/test_migrations/test_model_matches_head.py "requires the model and the migration to move
    together" — read against the file itself.
  found: >-
    THE PREMISE IS TRUE IN SPIRIT AND FALSE IN LETTER, AND THE DIFFERENCE CHANGES THE WORK. That
    test compares ONE table — `payments` — and only its COLUMN NAMES; its own docstring names the
    boundary ("Сверяется ОДНА таблица"). It would not notice a `schedules` constraint present in
    the model and absent from the queue, nor any constraint at all. What it WILL do is BREAK:
    `SCHEMA_AT_START` is a hand-written snapshot at revision 0019 containing only users,
    subscriptions, message_balances, balance_transactions and payments — there is no `schedules`
    table in it, so a revision that alters `schedules` makes `command.upgrade(config, "head")`
    fail with "no such table", and both tests in that file go red for a reason unrelated to their
    subject.
  implication: >-
    Two consequences. (a) The snapshot must gain a `schedules` table at its 0019 shape — which is
    exactly the documented idiom of that file ("в снимке лежит ровно то, без чего очередь не
    проходит"), not an expansion of its subject. (b) Model/queue parity for the CONSTRAINT has no
    existing gate at all, so the revision needs its own test in the per-revision idiom of
    test_0021 — the parity claim cannot be delegated to a file that only reads payment columns.

- timestamp: 2026-09-11T10:07:00Z
  checked: >-
    CYCLE 3, ITEM A. Blast radius of a MODEL-level CheckConstraint, measured by parsing every
    `Schedule(` construction in tests/ and classifying those that would violate it. tests/conftest.py
    builds the schema with `Base.metadata.create_all`, and SQLite enforces CHECK natively, so a
    model constraint bites the whole suite, not only the new tests.
  found: >-
    33 constructions total, of which 15 are active (explicitly or by the column default) with no
    `next_run_at` — they would raise IntegrityError the moment the constraint exists: 
    test_models/test_schedule.py (3), test_models/test_send_log.py (2), test_pages/test_account_groups.py (2),
    test_pages/test_ads_status.py, test_pages/test_htmx_preserved.py, test_pages/test_identifier_bounds.py,
    test_pages/test_responsive_markup.py (3), test_pages/test_schedule_ownership.py,
    test_schedule_relationships.py.
    Separately: every `times_of_day` literal in the suite is strict HH:MM and every `days_of_week`
    literal is within 0..6, so the item B rules break no existing expectation.
  implication: >-
    The constraint has teeth, and the 15 fixtures are the proof: each of them describes a row
    shaped exactly like the production defect. They are repaired by supplying the missing
    `next_run_at`, which is the minimal change that preserves each test's own subject — not by
    weakening the constraint. This cost is recorded BEFORE the work so the size of the diff is a
    decision and not a surprise.


- timestamp: 2026-09-11T10:40:00Z
  checked: >-
    CYCLE 3, TDD RED for both items, run under .venv on the pinned Python 3.12:
    tests/test_models/test_schedule_active_requires_next_run.py +
    tests/test_routes/test_schedules_api_value_domain.py.
  found: >-
    RED, 31 failed / 78 passed in 30.46s, AND EVERY FAILURE IS A GENUINE ASSERTION — not one
    timeout, not one collection error. Three distinct failure shapes, quoted verbatim:
      - `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` (x3) — the schema accepts
        the dead row today;
      - `AssertionError: ... сохранена МЁРТВАЯ СТРОКА ... assert not (True and None is None)` —
        POST and PUT with days [9]/[7]/[-1] return is_active=true with next_run_at=null;
      - `AssertionError: ... ожидался отказ формы. Получен 500. assert 500 == 422` — malformed
        times crash the route.
    The 78 passing in the same red run include the positive controls and the 72-case pure
    invariant, which is what proves the red was about the defect and not about the harness.
  implication: >-
    ⚠️ NOTE ON THE 500: the crash surfaces as an HTTP 500 RESPONSE, not as an exception escaping
    the ASGI transport — the application has a global handler. The test's crash-to-pytest.fail
    wrapper therefore never fires, and the red reads as a plain `assert 500 == 422`. Also a
    correction to the 10:05 probe entry, which stands unchanged alongside: `["abc"]` raises
    ValueError from `int(parts[0])`, not IndexError; IndexError needs a value like `"12"` where
    the int() succeeds and `parts[1]` is then missing. Both are 500.

- timestamp: 2026-09-11T11:20:00Z
  checked: >-
    CYCLE 3, ITEM A. Whether the Alembic revision survives SQLite's batch recreate intact —
    measured with PRAGMA index_list / foreign_key_list on a real upgrade, not assumed.
  found: >-
    ⚠️ TWO SILENT LOSSES, BOTH FOUND BY MEASUREMENT, BOTH FIXED BEFORE THE TEST WAS WRITTEN.
      (a) On REFLECTION the recreate dropped the foreign-key rules: `ad_id` fell from
          ON DELETE CASCADE and `account_id` from ON DELETE SET NULL to `NO ACTION`. SQLAlchemy's
          SQLite reflection does not carry ON DELETE at all. Losing the second one is a silent
          REVERSAL OF REVISION 0012 and a return of issue #35 — deleting a messenger account
          would cascade away the schedules instead of detaching them. Fixed with an explicit
          `copy_from` table definition.
      (b) After switching to `copy_from`, BOTH INDEXES vanished instead. Cause read from the
          library source, not guessed: `alembic/operations/batch.py::_gather_indexes_from_both_tables`
          skips any index carrying `_column_flag`, which is exactly what the `Column(..., index=True)`
          shorthand produces. One of the two was `ix_schedules_next_run_at` — the index the due
          query itself runs on. Fixed by declaring both indexes as explicit `sa.Index` objects.
    Neither loss emitted a warning of any kind.
  implication: >-
    Both are now pinned by named tests in the revision test file, and both were re-proved by
    mutation (M4, M5 below). ⚠️ SCOPE OF THE LOSSES, STATED HONESTLY: production is PostgreSQL and
    takes the `op.create_check_constraint` branch — no recreate, no foreign keys involved — so
    neither loss ever threatened the boiler in any version of this revision. The SQLite branch
    exists for the suite; but a suite that claims to run the same schema as production has to
    actually run it.

- timestamp: 2026-09-11T11:35:00Z
  checked: >-
    CYCLE 3, ITEM A. Whether the revision test has teeth, proved by mutation rather than
    asserted. The test file was written AFTER the revision (the model half was written before —
    see the 10:40 red), so its red is demonstrated by reverting the revision, five ways.
  found: >-
    ALL FIVE MUTANTS KILLED, source restored byte-identical afterwards (`diff` empty):
      M1 `upgrade()` emptied to `pass` (the revision reverted outright) → 5 failed;
      M2 backfill disabled, constraint still created → 14 failed (the upgrade itself now aborts
         on the dirty row, which is precisely the mid-queue break the ordering exists to prevent);
      M3 backfill DELETEs instead of deactivating → 4 failed, caught by the
         "does not invent days or times" and "rows survive" assertions;
      M4 explicit `sa.Index` objects replaced by the `index=True` shorthand → 2 failed, both
         index-survival tests;
      M5 `copy_from` removed → 1 failed, the ON DELETE rules test.
  implication: >-
    The test constrains the revision at every site that matters and each mutant is killed by the
    assertion written for it, not by collateral damage. M2 is the most informative: it shows the
    backfill is load-bearing and not decorative.

- timestamp: 2026-09-11T11:45:00Z
  checked: >-
    CYCLE 3. The checkpoint's own premise about test_model_matches_head.py, verified by running
    it rather than by reading it.
  found: >-
    CONFIRMED BROKEN, exactly as predicted at 10:06: `sqlite3.OperationalError: no such table:
    schedules` — the revision's own backfill query is the statement that fails, because the
    hand-written snapshot at 0019 has no `schedules` table. Repaired by adding `schedules` at its
    0019 shape plus minimal `ads` and `messenger_accounts` for the foreign keys to point at; the
    file's own documented idiom ("в снимке лежит ровно то, без чего очередь не проходит"). Its
    subject is untouched — it still compares the columns of `payments` alone.
  implication: >-
    The whole migration suite is green afterwards: 122 passed. The parity claim for the CONSTRAINT
    is carried by the new revision test, not by this file, because this file cannot carry it.

- timestamp: 2026-09-11T12:05:00Z
  checked: >-
    CYCLE 3. Blast radius of the model constraint, resolved rather than predicted: the 15 fixtures
    forecast at 10:07 were repaired one by one and the affected suites re-run.
  found: >-
    12 of the 15 took a one-line `next_run_at=...`, which only makes each fixture describe a row
    shape that can actually exist. THE OTHER THREE ARE IN tests/test_models/test_schedule.py AND
    ONE OF THEM IS SUBSTANTIVE: `test_schedule_default_values` asserted
    `is_active is True` AND `next_run_at is None` — IT ASSERTED THE DEAD ROW AS THE DOCUMENTED
    DEFAULT BEHAVIOUR OF THE MODEL. That is the fail-open default named as contributing cause (b)
    in the root cause's AND-gate, written down as an expectation and green since the table was
    created. It is rewritten to keep testing the default (`is_active` still comes back True when
    not passed) while no longer asserting the forbidden pair; the refusal itself is now asserted
    by the new model test.
  implication: >-
    ⚠️ THIS IS THE STRONGEST "WHY NOT CAUGHT" EVIDENCE OF THE WHOLE SESSION, AND IT IS BETTER THAN
    THE ONE RECORDED AT 08:28. That entry said the route's coverage only ever exercised complete
    bodies. True, but this is sharper: the suite did not merely fail to test the dead row — it
    ENCODED IT AS CORRECT. No gate could have caught a state that a green test asserted was the
    expected default. tests/test_models/test_schedule.py:47 (as it stood) is the answer to "which
    existing gate should have caught it": that one, and it was pointed the wrong way.

- timestamp: 2026-09-11T12:20:00Z
  checked: >-
    CYCLE 3. Read-only production census (SQLAlchemy `connect()`, SELECT only — no transaction, no
    write), asking the three questions the deploy decision actually turns on.
  found: >-
    PRODUCTION IS CLEAN ON ALL THREE, 104 schedules:
      - rows violating `is_active AND next_run_at IS NULL`: 0 (confirms the owner's sched=48
        deactivation held);
      - rows carrying an OUT-OF-RANGE day number: 0;
      - rows carrying a MALFORMED time string: 0.
  implication: >-
    Three consequences for the owner. (a) Revision 0022 will apply with a backfill of ZERO — it
    changes schema only, and the logged count will say so. (b) The constraint cannot be violated
    by any row now in the table. (c) THE RESIDUAL I WAS LOOKING FOR IS ABSENT: a LEGACY row with
    out-of-range days would pass the toggle's completeness guard (non-empty), compute a None next
    run, and hit the new constraint as a 500 IntegrityError on a user's toggle click. There is no
    such row. Had there been one, the constraint would have needed to wait.


- timestamp: 2026-09-11T12:45:00Z
  checked: >-
    CYCLE 3. Four ERRORS that appeared at ~13% of the full-suite run and were NOT present when the
    same directories were run alone. Chased before being reported as a regression.
  found: >-
    ⚠️ THEY WERE MY OWN MEASUREMENT ARTIFACT, NOT A REGRESSION. I had been running with
    `-p no:logging` to keep output readable; that plugin PROVIDES the `caplog` fixture, so four
    tests in tests/test_messengers that request `caplog` errored at SETUP. The same selection run
    WITHOUT the flag: 67 passed, 0 failed, 0.42s.
  implication: >-
    The authoritative full-suite run was restarted with the project's own command
    (`pytest tests/ -q`, no plugin suppression). Recorded rather than quietly dropped: a figure
    produced under a flag that changes which fixtures exist is not the figure the project's gate
    produces, and reporting the first one as "the suite" would have been wrong in the same way the
    relayed 3034/37m24s figure was wrong — asserted rather than reproduced.


- timestamp: 2026-09-11T09:22:34Z
  checked: >-
    CYCLE 3 regression gate. The project's own command, no plugin suppression, run to completion
    in this working tree: `.venv/bin/python -m pytest tests/ -q`.
  found: >-
    3163 passed, 0 failed, 0 errors, EXIT CODE 0, 2350.79s (39m10s).
    Started 2026-09-11T08:43:11Z, finished 2026-09-11T09:22:34Z. Figures quoted as figures, from
    the captured output, not characterised.
  implication: >-
    No regression anywhere in the suite from either item, including the constraint's effect on
    the 16 seed fixtures that had to be repaired.
    ⚠️ AN ARITHMETIC CROSS-CHECK WORTH RECORDING. The cycle-2 report claimed 3034 passed and was
    filed as relayed-not-verified. This cycle adds exactly 129 tests (102 + 7 + 20), and
    3034 + 129 = 3163 EXACTLY. That does not turn the earlier figure into a verified one — it was
    never reproduced and its status stands — but the two are arithmetically consistent, which is
    weak corroboration rather than none.


- timestamp: 2026-09-11T13:10:00Z
  checked: >-
    CYCLE 3, final. Proof that nothing was applied to any database, plus the real queue position —
    read-only, `connect()`, three SELECTs against the live database.
  found: >-
    - `SELECT version_num FROM alembic_version` -> **0021**;
    - `ck_schedules_active_requires_next_run` in `pg_constraint`: **ABSENT**;
    - rows violating the constraint: **0**.
  implication: >-
    Two things. (a) THE MIGRATION WAS NOT APPLIED — the constraint does not exist on the boiler,
    exactly as instructed; it has only ever run against throwaway SQLite files under pytest's
    tmp_path. (b) ⚠️ A STALE OPERATIONAL CLAIM WAS CAUGHT BY THIS MEASUREMENT AND CORRECTED.
    The first draft of the 0022 docstring said it was "the third unapplied revision", copying the
    2026-08-21 state recorded in the docstrings of 0021 and test_model_matches_head.py (production
    on 0019). Production has since moved to 0021, so 0022 is the ONLY unapplied revision. The 0022
    docstring is corrected to the measurement; the two older docstrings are NOT rewritten (D-30/
    D-32 — they are the record of their own moment, and what was wrong was carrying their number
    forward into today, not the number itself).



- timestamp: 2026-09-11T10:15:00Z
  checked: >-
    ORCHESTRATOR'S INDEPENDENT RE-VERIFICATION of cycle 3's falsifying claim, taken by stashing
    the working tree so the measurement ran against commit 7833844 EXACTLY AS COMMITTED — not
    against the tree that already contains the wider fix.
  found: >-
    THE CLAIM HOLDS. days=[9] -> is_schedule_complete True, compute_next_run_at None, dead row.
    Same for [-1] and for [7] (weekday() yields 0..6, so 7 is out of range too). days=[0] is
    healthy; days=[] is correctly incomplete.
  implication: >-
    ⚠️ COMMIT 7833844 IS PARTIAL, AND THE ORCHESTRATOR SAID OTHERWISE — both in its commit
    message and, worse, in a SOURCE COMMENT it committed into app/routes/schedules.py claiming
    "согласованность двух правил держится по построению". That sentence was false when written.
    The empty-list half was closed; the out-of-range half was not. The comment is corrected in
    cycle 3's tree by naming the old claim mistaken rather than deleting it. This entry exists so
    the partiality is recorded against the commit itself and is not discoverable only by reading
    a later cycle's prose.

- timestamp: 2026-09-11T10:15:00Z
  checked: >-
    Orchestrator's independent verification of cycle 3's production and test figures, rather
    than accepting the subagent's report.
  found: >-
    PRODUCTION (read-only): alembic_version = 0021, so revision 0022 is unapplied — confirms the
    correction of the stale 0019 in older docstrings. No CHECK constraint on schedules. Rows
    violating `is_active AND next_run_at IS NULL`: 0. Rows carrying a day outside 0..6: 0. Rows
    carrying a time not matching ^[0-9]{2}:[0-9]{2}$: 0 — so the new 422 rejects no existing data.
    MIGRATION 0022 read: explicit copy_from with ondelete CASCADE (ads) and SET NULL
    (messenger_accounts) plus explicit sa.Index for both indexes — the two silent defects the
    subagent reported catching are in fact fixed in the file.
    TESTS: tests/test_models/ + tests/test_routes/ + tests/test_migrations/ +
    test_schedule_relationships.py + test_schedule_service.py = 492 passed, 0 failed (3m26s).
  implication: >-
    Everything checkable at proportionate cost checks out. STILL RELAYED, NOT VERIFIED: the
    3163-passed / 39m10s full-suite figure, the 5/5 revision mutants, and the RED-phase counts.
    They are recorded as the subagent's figures, not as the orchestrator's.

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

---

## Resolution — CYCLE 3 (items A and B)

<!-- ⚠️ ЭТОТ РАЗДЕЛ ДОБАВЛЕН РЯДОМ, А НЕ ВМЕСТО. The cycle-2 Resolution above stands
     unchanged and is still the record of what 7833844 fixed (D-30/D-32). One claim inside
     it is corrected below by name; the rest is unaffected. -->

- supersedes_nothing: >-
    The cycle-2 root cause, fix and verification are unchanged and remain correct. What follows
    extends them and corrects EXACTLY ONE SENTENCE of the cycle-2 `fix` field.

- correction_to_cycle_2: >-
    The cycle-2 `fix` field ends: "The invariant now holds by construction on every входе:
    is_schedule_complete requires non-empty days AND times, which are exactly the two conditions
    under which compute_next_run_at returns None." ⚠️ THE CLAUSE AFTER THE COLON IS FALSE.
    Emptiness is NOT the only condition under which `compute_next_run_at` returns None: a
    NON-EMPTY list of out-of-range day numbers returns None too, because the 8-day scan never
    matches such a weekday. Measured, not argued (evidence 10:05). Consequence: the dead-row shape
    remained reachable through POST /api/schedules AFTER 7833844, and PUT could additionally kill
    a LIVE schedule the same way. The claim is true NOW — but because the input rejects
    out-of-domain values before the calculation, not because the two rules agree by themselves.

- root_cause_item_b: >-
    The rule defining WHICH VALUES the scheduler can actually execute — day ∈ 0..6, time matching
    HH:MM — lived only on the page input (`_TIME_RE` and `_clean_ints(low=0, high=6)` in
    app/pages/schedules.py) and was absent from the JSON input entirely. Same divergence class as
    WR-05/CR-02, same class as the cycle-2 root cause; a third instance of "one rule, one input".
    Two consequences, differing only in which side of the string parse the bad value lands on:
    a malformed TIME breaks `int(parts[0])`/`parts[1]` (HTTP 500, no row written), while an
    out-of-range DAY passes the parse and yields no candidate (HTTP 201, DEAD ROW written).

- fix_item_b: >-
    The RULE moved to app/services/schedule_rules.py — `DAY_OF_WEEK_MIN`/`DAY_OF_WEEK_MAX`,
    `TIME_OF_DAY_RE`, `is_valid_day_of_week`, `is_valid_time_of_day` — the neutral module that
    exists for precisely this failure mode. Each input keeps the POLICY it already had:
      - JSON (`CreateScheduleRequest` and `UpdateScheduleRequest`): 422 via `field_validator`,
        naming the offending values. This is the behaviour this input ALREADY has for a malformed
        field value (`timezone` not in VALID_TIMEZONES; explicit null per CR-03) — not a third
        behaviour.
      - Page (`_clean_times`, `_clean_ints`): unchanged — discard the bad value, keep the rest,
        because a form posts repeated fields and one bad value must not lose the others.
    ⚠️ WHY 422 HERE AND NOT FOR COMPLETENESS: different questions. An incomplete schedule is a
    legal draft state that two other writers already accept-and-pause. "abc" is not a time and 9
    is not a weekday — no such state exists in the domain at all.

- fix_item_a: >-
    `CheckConstraint("NOT (is_active AND next_run_at IS NULL)",
    name="ck_schedules_active_requires_next_run")` on app/models/schedule.py, plus Alembic
    revision 0022 carrying the same condition word-for-word (the revision does not import from
    app.* — project rule — so the two texts are pinned equal by a test instead).
    The revision deactivates any violating row BEFORE creating the constraint and logs the count:
    `is_active -> false`, days and times UNTOUCHED. That repeats the owner's manual sched=48
    decision rather than inventing one — guessing the intended days would be fabrication, and
    leaving days/times intact is what makes recovery through the editor possible.
    ⚠️ CREATED, NOT APPLIED. The revision has not been run against any database. Production is on
    0019 per the 0021 docstring, so 0020, 0021 and 0022 are all unapplied; running the queue is
    the owner's action.

- verification_cycle_3: >-
    - reproduction_before_fix: RED — 31 failed / 78 passed in 30.46s, every failure a genuine
      assertion in three shapes: `DID NOT RAISE IntegrityError` (x3),
      `assert not (True and None is None)` (the dead row, POST and PUT), and `assert 500 == 422`
      (the crash). Positive controls and the 72-case invariant green in the SAME red run.
    - fix_resolves: GREEN — value-domain file 102/102; model-constraint file 7/7; revision file
      20/20; whole migration suite 122/122.
    - mutation_signal (revision): 5/5 mutants killed — revision reverted to no-op (5 failed),
      backfill disabled (14 failed), backfill DELETEs instead of deactivating (4 failed),
      `index=True` shorthand restored (2 failed), `copy_from` removed (1 failed). Source restored
      byte-identical (`diff` empty).
    - two_defects_found_by_the_guardrail_itself: the SQLite batch recreate silently dropped
      (a) the ON DELETE rules — a silent reversal of revision 0012 and a return of issue #35 — and
      (b) both indexes, including the one the due query runs on. Both were found by measuring
      PRAGMA output, both fixed before the test was written, both now pinned by named tests.
    - regression_signal: FULL SUITE GREEN — 3163 passed, 0 failed, 0 errors, exit 0,
      2350.79s (39m10s), `.venv/bin/python -m pytest tests/ -q`, started 08:43:11Z and
      finished 09:22:34Z. 3034 (the cycle-2 relayed count) + 129 new tests = 3163 exactly.
    - oracle_type: specified (D-08 / D-12 are explicit project decisions with single shared
      definitions) + derived (the completeness-implies-computable invariant) + implicit
      (IntegrityError from the schema).
    - environment: in-memory SQLite via tests/conftest.py for the suite; file-backed SQLite via
      real Alembic for the revision tests. The only production access this cycle was SELECT-only
      through `connect()`.

- production_readiness: >-
    Read-only census at 12:20 on the live database: 104 schedules, ZERO violating the constraint,
    ZERO with an out-of-range day, ZERO with a malformed time. Therefore (a) revision 0022 will
    apply with a backfill of zero, (b) no existing row can violate it, and (c) the one residual I
    was hunting is absent — a legacy out-of-range-day row would have passed the toggle's
    completeness guard, computed a None next run, and turned a user's toggle click into a 500
    against the new constraint. There is no such row.

- files_changed_cycle_3:
    source:
      - app/services/schedule_rules.py (day/time value domain lifted here; one rule, both inputs)
      - app/routes/schedules.py (422 validators on BOTH request models; stale "by construction" comment corrected)
      - app/pages/schedules.py (delegates to the shared rule; page discard policy unchanged)
      - app/models/schedule.py (CheckConstraint + the condition/name constants)
      - alembic/versions/0022_schedules_active_requires_next_run.py (NEW — created, NOT applied)
    tests_new:
      - tests/test_routes/test_schedules_api_value_domain.py
      - tests/test_models/test_schedule_active_requires_next_run.py
      - tests/test_migrations/test_0022_schedules_active_requires_next_run.py
    tests_repaired_by_the_constraint:
      - tests/test_migrations/test_model_matches_head.py (snapshot gained schedules/ads/messenger_accounts so the queue passes; subject unchanged)
      - tests/test_models/test_schedule.py, test_send_log.py, tests/test_metrics.py,
        tests/test_schedule_relationships.py, tests/test_application/test_send_analytics.py,
        tests/test_pages/{test_account_groups,test_ads_status,test_htmx_preserved,test_identifier_bounds,test_responsive_markup,test_schedule_ownership,test_editor_schedules,test_schedules_list,test_schedules_poisoned_row}.py

- why_not_caught: >-
    ⚠️ SHARPER THAN THE CYCLE-2 ANSWER, AND WORSE. Cycle 2 recorded "the route's coverage only
    ever exercised complete bodies". True, but the real answer is that the suite ENCODED THE DEAD
    ROW AS CORRECT: `tests/test_models/test_schedule.py::test_schedule_default_values` asserted
    `is_active is True` AND `next_run_at is None` as the documented model default, and
    `test_send_analytics.py::test_upcoming_sends_skips_inactive_and_unscheduled` deliberately
    seeded that same pair to prove the dashboard hides it. Both were green for the life of the
    table. No gate can catch a state that a passing test declares expected. Those two files are
    the gate that should have caught it, and they were pointed the wrong way.

- recurrence_guard: >-
    Four artifacts, in increasing order of strength:
    (1) tests/test_routes/test_schedules_api_value_domain.py — the input can no longer accept a
        value the scheduler cannot execute (both inputs, both fields, boundary neighbours);
    (2) tests/test_models/test_schedule_active_requires_next_run.py — the model-level refusal,
        including the column-default path that caused 7833844;
    (3) tests/test_migrations/test_0022_schedules_active_requires_next_run.py — the revision
        carries the same constraint, the backfill is ordered before it, and the batch recreate
        keeps the indexes and the ON DELETE rules;
    (4) the DB constraint itself — the only artifact that makes the state IMPOSSIBLE rather than
        merely unreachable through the application. ⚠️ It is only an artifact once the owner
        applies the migration; until then (1)-(3) are what hold.

- residuals_named: >-
    - The migration is NOT applied. Until it is, raw psql / data migrations can still write the
      dead row on the boiler.
    - VISIBLE TO API CLIENTS: `times_of_day: ["9:00"]` (single-digit hour) previously SUCCEEDED on
      this input and now returns 422. HH:MM with a two-digit hour is the project's single
      definition of the format; accepting two spellings of one time would be a second definition.
      Named here rather than discovered by a client.
    - `Schedule.next_run_at.isnot(None)` inside `upcoming_sends` is now defence-in-depth rather
      than an independently reachable branch; it can no longer be exercised through the database,
      and the test that used to exercise it says so in its own docstring instead of pretending.
    - The incident board still cannot see this class by construction (it filters
      `next_run_at IS NOT NULL`). Unchanged from cycle 2, and out of scope here.

- landed: >-
    ⚠️ APPENDED BY THE ORCHESTRATOR 2026-09-11 AFTER THE OWNER'S DECISIONS — the fields above are
    NOT rewritten (D-30/D-32), and one of them is now known to be partial. Commits, in order:
    7833844 (empty-list half, PARTIAL — see the 10:15 evidence entry and the note below),
    8b96136 (out-of-range days and malformed times rejected at the input, which is what made
    7833844 partial), d46780b (model constraint + alembic revision 0022 + fixture repairs across
    15 test files).
- correction_to_the_fix_field: >-
    The `fix` field above describes commit 7833844 and its final sentence — that
    is_schedule_complete and compute_next_run_at agree by construction — IS FALSE. An
    out-of-range day number is non-empty, so completeness passed while compute_next_run_at
    returned None. Verified by the orchestrator against the stashed tree at exactly 7833844:
    days=[9], [-1] and [7] all reproduce the dead-row shape. The same false claim was committed
    into app/routes/schedules.py as a source comment and is corrected there by 8b96136, named as
    mistaken rather than deleted.
- verification: >-
    ORCHESTRATOR-RUN, not relayed: tests/test_models/ + tests/test_routes/ +
    tests/test_migrations/ + test_schedule_relationships.py + test_schedule_service.py =
    492 passed, 0 failed. Intermediate state with only 8b96136 staged = 458 passed, the sole 4
    failures belonging to the constraint half's own untracked test file. Production (read-only):
    alembic_version 0021, no CHECK constraint, 0 violating rows, 0 out-of-range days, 0 malformed
    times — so revision 0022 applies cleanly and the new 422 rejects no existing data.
    RELAYED AND NOT INDEPENDENTLY VERIFIED: the subagent's 3163-passed / 39m10s full suite, its
    5/5 revision mutants, and its RED-phase counts.
- not_done_deliberately: >-
    REVISION 0022 IS NOT APPLIED TO ANY DATABASE. Owner's decision: it travels with the code
    deploy, because schema and code must move together. Production remains on 0021, and until the
    deploy the guarantee is the input validation alone — strong enough that the application
    cannot produce the state, not strong enough to make it impossible.
- superseded_production_write: >-
    The manual deactivation of sched=48 (evidence 09:40) was later made redundant by revision
    0022, whose upgrade deactivates dead rows itself. Not an error — the revision did not exist
    at the time, and deactivating that row is what unblocked the constraint decision — but it is
    recorded rather than left to look deliberate.

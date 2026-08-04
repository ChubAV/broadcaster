---
phase: quick-max-worker-liveness
plan: 01
subsystem: worker-liveness
tags: [redis, docker, max, pymax, celery, reliability]
requires:
  - phase: quick-260803-pb6
    provides: PyMax 2.3.1 MAX worker foundation
provides:
  - Separated BLPOP and Redis socket deadlines with expiring MAX heartbeats
  - Bounded PyMax shutdown and fail-closed Redis URL logging
  - Heartbeat-aware Docker MAX worker recovery for queued work
affects: [max-worker, celery-container-manager, redis-liveness]
tech-stack:
  added: []
  patterns: [bounded async cleanup, expiring liveness records, fail-closed container replacement]
key-files:
  created: [tests/test_max_container_manager.py]
  modified:
    - max_worker/main.py
    - app/services/max_container_manager.py
    - app/worker/tasks.py
    - tests/test_worker/test_max_worker.py
    - tests/test_worker_tasks.py
key-decisions:
  - "Use a six-second Redis socket budget for five-second BLPOP polls."
  - "Treat absent, malformed, future, and over-90-second MAX heartbeats as unhealthy."
actuals:
  tokens: 4577
  tasks: 2
  commits: 6
requirements-completed: []
coverage:
  - id: D1
    description: Bounded and credential-safe MAX worker Redis, heartbeat, and shutdown handling.
    verification:
      - kind: unit
        ref: "uv run --with 'maxapi-python==2.3.1' pytest -q tests/test_worker/test_max_worker.py -k 'redis or consumer or shutdown or heartbeat or redacts' -x"
        status: pass
    human_judgment: false
  - id: D2
    description: Heartbeat-aware MAX Docker reuse and recovery for pending queues.
    verification:
      - kind: unit
        ref: "uv run pytest -q tests/test_max_container_manager.py tests/test_worker_tasks.py -k 'max_container or heartbeat or manage_max' -x"
        status: pass
    human_judgment: false
duration: 9min
completed: 2026-08-03
status: complete
---

# Phase quick-max-worker-liveness Plan 01: MAX Worker Liveness Summary

**MAX workers now avoid BLPOP read-timeout loops, expire their liveness signals, exit through a bounded PyMax cleanup path, and are replaced when queued work finds a dead heartbeat.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-08-03T21:06:30Z
- **Completed:** 2026-08-03T21:15:33Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Gave the blocking Redis connection a deadline beyond its five-second BLPOP poll, with normal idle polling left on the non-error path.
- Added a shared 90-second-expiring heartbeat writer, bounded PyMax client close, and fail-closed Redis URL rendering for startup logs.
- Made queued MAX container management reuse only fresh heartbeats and stop stale workers before starting a replacement.

## Task Commits

1. **Task 1: Consume one idle BLPOP cycle and terminate a stuck PyMax shutdown safely**
   - `9ba0977` test: add RED regression coverage
   - `2b34d3b` feat: implement bounded worker liveness handling
2. **Task 2: Replace a Docker-running MAX worker when its heartbeat is dead**
   - `e3fbf16` test: add RED manager and orchestration coverage
   - `5f22bf7` feat: implement heartbeat-aware recovery
   - `6a33a2d` test: guard stale endpoint withdrawal
   - `3f3b175` fix: remove endpoints when recovery cannot proceed

## Files Created/Modified

- `max_worker/main.py` — Redis timeout separation, safe URL display, expiring heartbeats, and bounded client close.
- `app/services/max_container_manager.py` — Docker/Redis liveness assurance and fail-closed replacement.
- `app/worker/tasks.py` — Celery manager wiring for heartbeat-aware assurance.
- `tests/test_worker/test_max_worker.py` — Offline worker regressions.
- `tests/test_max_container_manager.py` — Offline Docker liveness regressions.
- `tests/test_worker_tasks.py` — Pending-queue and idle-queue orchestration coverage.

## Decisions Made

- The BLPOP socket read budget is six seconds, leaving a one-second guard over the server-side five-second poll timeout.
- Worker heartbeat TTL is three 30-second intervals; the manager declares a running container unhealthy at 90 seconds, on malformed data, or on a future timestamp.
- A failed stale-container stop returns no endpoint and never starts a competing replacement.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test bug] Restored a pre-existing Redis-close assertion to its original test scope.**
- **Found during:** Task 2 verification
- **Issue:** The newly inserted tests split an existing assertion from its WhatsApp dispatch test, causing a `NameError` in the empty-queue test.
- **Fix:** Returned the original assertion to the dispatch test and asserted the correct MAX Redis mock in the new test.
- **Files modified:** `tests/test_worker_tasks.py`
- **Verification:** Focused manager/task suite passed (9 passed).
- **Committed in:** `5f22bf7`

**2. [Rule 2 - Safety] Withdrew stale endpoints after failed container recovery.**
- **Found during:** Final behavior audit
- **Issue:** A failed stop correctly prevented replacement but could leave a previous endpoint key advertising the unhealthy worker.
- **Fix:** Delete `max:endpoint:{account_id}` whenever the heartbeat-aware assurance function returns no usable endpoint.
- **Files modified:** `app/worker/tasks.py`, `tests/test_worker_tasks.py`
- **Verification:** Focused manager/task suite passed (10 passed).
- **Committed in:** `6a33a2d`, `3f3b175`

**Total deviations:** 2 auto-fixed (Rule 1, Rule 2).

## Issues Encountered

The initial TDD RED commit accidentally included a pre-staged set of unrelated planning files. With explicit user approval, it was safely rewritten before implementation; the repaired history contains only the intended task files.

## User Setup Required

None — all coverage uses offline mocks; no Redis, Docker, or MAX service is required.

## Self-Check: PASSED

All six planned source/test files and all four task commits exist.

---
phase: quick-max-worker-liveness
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - max_worker/main.py
  - app/services/max_container_manager.py
  - app/worker/tasks.py
  - tests/test_worker/test_max_worker.py
  - tests/test_max_container_manager.py
  - tests/test_worker_tasks.py
autonomous: true
estimate:
  tokens: 38000
  raw_tokens: 38000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - "An idle MAX worker does not turn a normal five-second BLPOP wait into repeated Redis read-timeout errors, and it still checks the idle deadline at the configured cadence."
    - "Shutdown reaches process exit even when PyMax client close never completes; Redis liveness/endpoint keys and connections are still cleaned up on the bounded path."
    - "MAX worker startup logs identify the Redis endpoint without exposing the REDIS_URL username or password."
    - "When a MAX queue has pending work, the manager reuses a running container only while its Redis heartbeat is fresh and replaces a running container whose heartbeat is missing, stale, or malformed."
    - "Fresh workers are not restarted, failed container stops are not followed by conflicting starts, and existing MAX queue/endpoint key contracts remain unchanged."
  artifacts:
    - path: "max_worker/main.py"
      provides: "Separated BLPOP/socket time budgets, bounded PyMax shutdown, expiring heartbeats, and safe Redis URL rendering"
      contains: "BLPOP_TIMEOUT"
    - path: "app/services/max_container_manager.py"
      provides: "Docker-status plus Redis-heartbeat liveness decision and stale-container replacement"
      contains: "max:heartbeat:"
    - path: "app/worker/tasks.py"
      provides: "Celery manager wiring that uses heartbeat-aware MAX container assurance for pending queues"
      contains: "manage_max_containers"
    - path: "tests/test_worker/test_max_worker.py"
      provides: "Regression coverage for Redis blocking configuration, redaction, and a PyMax close that never returns"
      contains: "test_graceful_shutdown"
    - path: "tests/test_max_container_manager.py"
      provides: "Fresh, missing, stale, malformed, and failed-replacement heartbeat coverage"
      contains: "heartbeat"
    - path: "tests/test_worker_tasks.py"
      provides: "MAX manager task coverage for the pending-queue liveness path"
      contains: "manage_max_containers"
  key_links:
    - from: "max_worker/main.py"
      to: "redis.asyncio"
      via: "The dedicated redis_blpop connection has a socket read budget strictly greater than the server-side BLPOP timeout"
      pattern: "socket_timeout|blpop"
    - from: "max_worker/main.py"
      to: "app/services/max_container_manager.py"
      via: "Both sides use max:heartbeat:{account_id} millisecond timestamps and the manager allows multiple heartbeat intervals before declaring a timestamp stale"
      pattern: "max:heartbeat:"
    - from: "app/worker/tasks.py"
      to: "app/services/max_container_manager.py"
      via: "manage_max_containers delegates pending-queue container reuse/replacement to the heartbeat-aware assurance function"
      pattern: "ensure.*container|manage_max_containers"
    - from: "max_worker/main.py"
      to: "tests/test_worker/test_max_worker.py"
      via: "Async fakes exercise a never-finishing PyMax close, Redis cleanup, process exit, and URL redaction without live services"
      pattern: "graceful_shutdown|REDIS_URL|connect_redis"
---

<objective>
Eliminate the confirmed MAX worker hang by separating Redis BLPOP and socket timeouts, bounding shutdown, monitoring Redis heartbeat freshness, and redacting REDIS_URL in startup output.

Purpose: A queued MAX send must not remain behind a Docker container that is technically running but stuck after idle shutdown, and production logs must not disclose Redis credentials.
Output: A self-terminating MAX worker, heartbeat-aware container replacement, and offline regression coverage of the observed production failure chain.
</objective>

<execution_context>
@/source/broadcaster/.codex/gsd-core/workflows/execute-plan.md
@/source/broadcaster/.codex/gsd-core/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@max_worker/main.py
@app/services/max_container_manager.py
@app/worker/tasks.py
@app/worker/celery_app.py
@tests/test_worker/test_max_worker.py
@tests/test_wa_container_manager.py
@tests/test_worker_tasks.py

<interfaces>
Confirmed production failure evidence:
- The deployed redis-py 8.1 connection has an effective five-second socket read timeout while `BLPOP_TIMEOUT` is also five seconds. The equal deadlines produce repeated `Timeout reading` errors instead of clean BLPOP `None` results.
- After those errors reach the idle deadline, the worker logs idle shutdown and then remains inside PyMax client close; the Docker container remains in `running` state.
- `manage_max_containers` runs every 15 seconds, but `start_container` currently reuses every Docker-running container without consulting `max:heartbeat:{account_id}`.

Existing worker contracts to preserve:
- `connect_redis()` creates `redis_cmd` for ordinary commands and a dedicated `redis_blpop` connection for `BLPOP`.
- `start_consumer()` calls `redis_blpop.blpop(QUEUE_KEY, timeout=BLPOP_TIMEOUT)`, treats `None` as the normal poll boundary, and uses that boundary to check `IDLE_SHUTDOWN_SEC`.
- `heartbeat_loop()` and lifespan startup write millisecond timestamps to `HEARTBEAT_KEY`; task completion refreshes the same key.
- `graceful_shutdown(reason)` is idempotent through `shutting_down`, disables the consumer, deletes `HEARTBEAT_KEY` and `ENDPOINT_KEY`, closes PyMax and Redis, then calls `os._exit(0)`.
- The startup log is the only intentional log of `REDIS_URL`; it must retain useful scheme/host/port/database context while replacing user-info and must fall back to a fixed redacted value if parsing fails.

Existing manager contracts to preserve:
- `start_container(account_id, phone="") -> str | None`, `stop_container(account_id) -> bool`, and `_container_endpoint(name)` are synchronous Docker helpers used by `MaxMessenger` and Celery.
- `manage_max_containers()` reads `max:active_accounts`, checks `max:queue:{account_id}`, and refreshes `max:endpoint:{account_id}` with a 420-second expiry when a pending queue has a usable worker.
- Empty queues retain the current cleanup behavior: remove the active-account membership and endpoint key, leaving the worker's own idle shutdown policy unchanged.

Implementation constraints:
- Keep the command Redis client and blocking Redis client separate. Give only the blocking client's socket read a named timeout that is strictly greater than `BLPOP_TIMEOUT`; do not lengthen the server-side BLPOP poll because idle checks depend on it.
- Use three heartbeat intervals as the stale threshold so timestamp jitter does not recycle a healthy worker. Treat missing and non-numeric heartbeat values as unhealthy when queued work is waiting.
- No live Redis, Docker, or MAX service is permitted in the regression tests; use the existing AsyncMock/MagicMock patterns.
- The worktree already contains unrelated modifications and untracked planning/graph files. Limit edits and commits to `files_modified` above and do not revert, stage, or reformat unrelated work.
</interfaces>
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Consume one idle BLPOP cycle and terminate a stuck PyMax shutdown safely</name>
  <files>max_worker/main.py, tests/test_worker/test_max_worker.py</files>
  <behavior>
    - Redis connection contract: `redis_cmd` remains the normal command client, while `redis_blpop` is constructed with a socket timeout strictly greater than the five-second BLPOP timeout.
    - Normal idle poll: a BLPOP result of `None` remains a non-error path that checks the idle clock without the five-second retry sleep used for real Redis failures.
    - Stuck PyMax close: a client close coroutine that never completes is abandoned after a named short shutdown budget in tests; the worker clears session state, closes both Redis clients, logs completion/timeout without credentials, and reaches `os._exit(0)` exactly once.
    - Successful close: the existing graceful-shutdown behavior still awaits a cooperative client, preserves `session.db`, deletes heartbeat/endpoint keys, and closes Redis connections.
    - Credential redaction: a REDIS_URL containing username and password renders a safe startup value with neither credential present; a malformed value returns a fixed safe fallback rather than the original input.
    - Heartbeat expiry: startup, periodic, and post-task heartbeat writes use one shared helper/TTL so abandoned heartbeat keys cannot remain authoritative indefinitely.
  </behavior>
  <action>Write the regression tests before changing the worker. In `connect_redis()`, keep the dedicated BLPOP client but pass it a named socket timeout with a guard margin above `BLPOP_TIMEOUT`; retain the five-second Redis command timeout so `start_consumer()` still checks idleness every five seconds. Extract one heartbeat writer used by lifespan startup, `heartbeat_loop()`, and post-task refresh; store the existing millisecond timestamp with an expiry covering three heartbeat intervals. Refactor the PyMax portion of `graceful_shutdown()` so client close has a named bounded wait, a timeout is logged as a shutdown condition rather than propagated, `session` is cleared in all cases, Redis cleanup still runs, and process exit remains the final guaranteed action. Preserve idempotence and session-file semantics. Add a pure REDIS_URL rendering helper using standard-library URL parsing: retain non-secret endpoint context, replace any user-info, and return a constant redacted fallback on malformed input. Call that helper from the startup log and never include the raw URL in exception messages. Exercise both cooperative and never-finishing closes, the connection timeout relationship, heartbeat expiry calls, normal `None` polling, and redaction with offline mocks.</action>
  <verify>
    <automated>uv run --with 'maxapi-python==2.3.1' pytest -q tests/test_worker/test_max_worker.py -k 'redis or consumer or shutdown or heartbeat or redacts' -x</automated>
  </verify>
  <done>A five-second BLPOP poll has a longer socket-read budget, idle polling remains prompt, PyMax cannot hold the shutdown path indefinitely, Redis state is cleaned, heartbeat records expire, startup output contains no Redis credentials, and focused MAX worker tests pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Replace a Docker-running MAX worker when its heartbeat is dead</name>
  <files>app/services/max_container_manager.py, app/worker/tasks.py, tests/test_max_container_manager.py, tests/test_worker_tasks.py</files>
  <behavior>
    - Fresh heartbeat: a running container with a numeric `max:heartbeat:{account_id}` timestamp no older than three worker heartbeat intervals is reused and its endpoint is refreshed.
    - Dead heartbeat: a running container with a missing, malformed, or older timestamp is stopped/removed before a replacement is started when its queue has pending work.
    - Failed stop: if Docker cannot stop/remove the unhealthy named container, no replacement start is attempted and no healthy endpoint is advertised for that pass.
    - Non-running container: the existing `start_container()` path removes/recreates stopped containers and handles not-found containers without requiring a heartbeat.
    - Empty queue: the manager removes active-account and endpoint bookkeeping and does not restart a container solely because its heartbeat is stale.
    - Stable boundary: queue, active-account, endpoint, and heartbeat key names remain `max:queue:{id}`, `max:active_accounts`, `max:endpoint:{id}`, and `max:heartbeat:{id}`.
  </behavior>
  <action>Write a dedicated MAX container-manager test module by following the Docker mock patterns in `tests/test_wa_container_manager.py`, then add Celery orchestration coverage to `tests/test_worker_tasks.py`. In `app/services/max_container_manager.py`, add one synchronous assurance function that combines Docker running state with the Redis heartbeat: parse the worker's millisecond timestamp defensively, compare it with a named 90-second stale threshold, return the existing endpoint for a fresh running container, and for missing/stale/malformed heartbeat stop the existing container before calling `start_container()`. If the stop fails, return `None` so the caller cannot publish an endpoint that routes to the stuck process. In `manage_max_containers()`, use this heartbeat-aware function only for accounts with `queue_len > 0`, refresh the endpoint expiry only when it returns a usable endpoint, and keep empty-queue cleanup plus exited-container cleanup unchanged. Tests must prove the fresh reuse, every dead-heartbeat classification, stop-before-start ordering, failed-stop guard, pending-queue wiring, and empty-queue non-restart behavior without live Docker or Redis.</action>
  <verify>
    <automated>uv run pytest -q tests/test_max_container_manager.py tests/test_worker_tasks.py -k 'max_container or heartbeat or manage_max' -x</automated>
  </verify>
  <done>The 15-second manager loop distinguishes live from merely running MAX workers, automatically replaces a heartbeat-dead container for queued work, avoids recycling fresh workers or starting through a failed stop, preserves empty-queue behavior, and all manager/task regressions pass offline.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Environment to worker logs | `REDIS_URL` enters from deployment configuration and may contain reusable Redis credentials. |
| Worker to Redis | Blocking queue responses and heartbeat timestamps cross the network and control idle/shutdown/liveness decisions. |
| Celery manager to Docker daemon | Redis liveness data determines whether the manager stops, removes, reuses, or recreates a named container. |
| PyMax library to worker process | Third-party close behavior can delay or prevent worker termination. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-Q-RQT-01 | Information Disclosure | `max_worker/main.py` startup logging | high | mitigate | Render REDIS_URL through a fail-closed redaction helper and assert username/password never appear for valid or malformed inputs. |
| T-Q-RQT-02 | Denial of Service | `start_consumer()` and `graceful_shutdown()` | high | mitigate | Separate BLPOP and socket deadlines, retain prompt idle polling, bound PyMax close, continue Redis cleanup, and prove process exit with a never-finishing close fake. |
| T-Q-RQT-03 | Tampering | `max:heartbeat:{account_id}` parsing | medium | mitigate | Accept only numeric millisecond timestamps within the named freshness window; classify absent, malformed, and stale values as unhealthy and cover each case. |
| T-Q-RQT-04 | Denial of Service | Heartbeat-driven Docker replacement | medium | mitigate | Require pending queue work before replacement, allow three heartbeat intervals of timestamp age, stop before start, and fail closed when the old container cannot be removed. |
| T-Q-RQT-05 | Repudiation | Automatic stale-container recycling | low | accept | Existing structured container lifecycle events carry account id; targeted tests assert the decision path, and additional durable audit storage is outside this internal recovery loop's risk level. |
</threat_model>

<verification>
Run `uv run --with 'maxapi-python==2.3.1' pytest -q tests/test_worker/test_max_worker.py tests/test_max_container_manager.py tests/test_worker_tasks.py tests/test_messengers/test_max.py -x`. Review `git diff -- max_worker/main.py app/services/max_container_manager.py app/worker/tasks.py tests/test_worker/test_max_worker.py tests/test_max_container_manager.py tests/test_worker_tasks.py` to confirm the implementation is confined to the MAX worker liveness path and tests. Confirm no raw REDIS_URL value is logged and no unrelated dirty file is staged. Run `graphify update .` after the source changes, as required by AGENTS.md, but do not include generated graph changes in the quick-task code commits unless they were already explicitly tracked for this task.
</verification>

<success_criteria>
- The blocking Redis socket deadline is strictly longer than the server-side BLPOP timeout, so an empty five-second poll returns normally instead of producing the confirmed read-timeout loop.
- Both cooperative and non-returning PyMax close paths reach Redis cleanup and process exit within a bounded shutdown path while persisted MAX session files remain intact.
- Startup logging exposes no REDIS_URL username or password, including on malformed input.
- Heartbeats are refreshed with an expiry, and the manager combines Docker state with a three-interval Redis timestamp freshness check for pending queues.
- A heartbeat-dead running container is stopped before replacement; a fresh container is reused; failed stops and empty queues do not trigger unsafe replacement.
- The targeted worker, manager, Celery task, and MaxMessenger suites pass without live Redis, Docker, or MAX access.
</success_criteria>

## Source Coverage Audit

| Source | ID | Feature/Requirement | Plan | Status | Notes |
|--------|----|---------------------|------|--------|-------|
| GOAL | — | Stop redis-py 8.1 BLPOP/socket timeout collisions | 01, Task 1 | COVERED | Separate named deadlines and normal idle-poll coverage are required. |
| GOAL | — | Guarantee correct shutdown when PyMax close hangs | 01, Task 1 | COVERED | Bounded close, cleanup, exit, and a never-finishing close regression are required. |
| GOAL | — | Mask credentials in REDIS_URL startup output | 01, Task 1 | COVERED | Fail-closed redaction and credential-absence assertions are required. |
| GOAL | — | Add heartbeat-aware health checking and recovery for MAX containers | 01, Task 2 | COVERED | Fresh reuse, dead replacement, stop failure, and empty queue behavior are required. |
| GOAL | — | Include regression tests | 01, Tasks 1-2 | COVERED | Worker, service, and Celery task suites cover the production chain offline. |
| REQ | — | Quick work has no ROADMAP requirement IDs | — | N/A | No phase requirement is assigned to this quick task. |
| RESEARCH | — | No quick-task RESEARCH.md was provided | — | N/A | The confirmed production evidence in the invoking prompt is captured in plan context and mapped to both tasks. |
| CONTEXT | — | No quick-task CONTEXT.md decisions were provided | — | N/A | The user description and explicit constraints define the scope. |

<output>
Create `.planning/quick/260803-rqt-max-worker-redis-blpop-timeout-shutdown-/260803-rqt-SUMMARY.md` with `status: complete` when done.
</output>

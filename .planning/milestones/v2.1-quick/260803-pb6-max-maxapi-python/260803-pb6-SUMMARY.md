---
phase: quick-max-maxapi-python
plan: "01"
subsystem: messaging-worker
tags: [max, pymax, maxapi-python, fastapi, redis, pytest]
requires: []
provides:
  - "A MAX worker pinned to maxapi-python 2.3.1 and its public pymax WebClient API."
  - "Offline regression coverage for QR auth, persisted sessions, group sync, and media delivery."
affects: [max-worker, max-messenger, celery-max-delivery]
actuals:
  tokens: 6178
  tasks: 2
  commits: 2
tech-stack:
  added: ["maxapi-python==2.3.1"]
  patterns: ["Read-only SQLite session compatibility", "strictly decreasing MAX chat pagination markers"]
key-files:
  created: [tests/test_worker/test_max_worker.py]
  modified: [max_worker/main.py, max_worker/requirements.txt]
key-decisions:
  - "Use the public pymax WebClient, ExtraConfig, Photo, and ChatType interfaces only."
  - "Keep persisted session inspection read-only and reserve deletion for explicit account removal."
requirements-completed: []
coverage:
  - id: D1
    description: "PyMax 2.3.1 worker lifecycle and QR authentication."
    verification:
      - kind: unit
        ref: "tests/test_worker/test_max_worker.py#test_pymax_2_3_1_contract"
        status: pass
    human_judgment: false
  - id: D2
    description: "Session reuse, group synchronization, text/image sends, and the stable MaxMessenger boundary."
    verification:
      - kind: integration
        ref: "uv run --with 'maxapi-python==2.3.1' pytest -q tests/test_worker/test_max_worker.py tests/test_messengers/test_max.py -x"
        status: pass
    human_judgment: false
duration: 16min
completed: 2026-08-03
status: complete
---

# Quick Task 260803-pb6: MAX PyMax 2.3.1 Worker Summary

**MAX account lifecycle and delivery now use the public PyMax 2.3.1 WebClient contract with durable session reuse and offline behavior coverage.**

## Performance

- **Duration:** 16 min
- **Completed:** 2026-08-03T18:31:06Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Pinned the isolated MAX worker to `maxapi-python==2.3.1` and migrated it from removed legacy client APIs to `pymax.WebClient`.
- Preserved QR capture, session reuse, explicit deletion, HTTP/Redis boundaries, and text/image delivery using the supported API.
- Added 16 offline worker tests, including malformed pagination marker termination.

## Task Commits

1. **Task 1: Authenticate one MAX account and send text through PyMax 2.3.1** — `fea8b6a` (`feat`)
2. **Task 2: Preserve sessions, synchronize groups, and deliver image ads on the upgraded client** — `0879a75` (`test`)

## Verification

- `uv run --with 'maxapi-python==2.3.1' pytest -q tests/test_worker/test_max_worker.py tests/test_messengers/test_max.py -x` — **40 passed**
- `graphify update .` — updated the local graph; its untracked outputs were not added because this repository does not track them.

## Decisions Made

- Session databases are inspected via SQLite read-only mode; token and device values are never logged.
- Chat pagination only continues with a strictly decreasing integer timestamp marker, preventing malformed remote data from retry loops.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Terminated pagination safely for malformed timestamp values**
- **Found during:** Task 2
- **Issue:** A non-integer remote `last_event_time` could raise during marker construction and turn a terminal page into a retry.
- **Fix:** Added a guarded marker helper and offline regression coverage.
- **Files modified:** `max_worker/main.py`, `tests/test_worker/test_max_worker.py`
- **Verification:** Group synchronization tests pass.
- **Committed in:** `fea8b6a` (implementation), `0879a75` (coverage)

## Issues Encountered

- The restricted sandbox could not create uv cache temporary files; verification completed after approved cache access.

## Next Steps

The MAX worker and its existing MaxMessenger adapter are ready for offline regression use. Live MAX authentication remains intentionally outside the test suite.

## Self-Check: PASSED

- Confirmed all three task files exist and both task commits are present.

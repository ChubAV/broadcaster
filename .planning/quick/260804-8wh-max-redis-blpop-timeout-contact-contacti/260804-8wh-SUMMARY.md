---
phase: quick-260804-8wh
plan: 01
subsystem: max-worker-runtime-and-deployment
tags: [max, pymax, pydantic, redis, docker, just]
requires:
  - phase: quick-260803-pb6
    provides: "PyMax 2.3.1 MAX worker migration"
  - phase: quick-260803-rqt
    provides: "Redis reliability and safe diagnostics in the MAX worker"
provides:
  - "Version-scoped CONTACT attachment compatibility for PyMax 2.3.1"
  - "Revision-labelled MAX worker images rebuilt before production teardown"
  - "Safe runtime source and PyMax version diagnostics"
affects: [max-worker, production-deploy, max-container-manager]
actuals:
  tokens: 3674
  tasks: 2
  commits: 6
tech-stack:
  added: []
  patterns:
    - "Idempotent compatibility seam tied to an audited dependency version"
    - "Offline Just dry-run deployment contracts"
key-files:
  created:
    - max_worker/pymax_compat.py
    - tests/test_max_worker_deployment.py
  modified:
    - max_worker/main.py
    - max_worker/Dockerfile
    - justfile
    - tests/test_worker/test_max_worker.py
key-decisions:
  - "Mutate only PyMax 2.3.1 ContactAttachment.contact_id when it remains required, then rebuild dependent schemas."
  - "Use the image's git revision and installed PyMax version as safe stale-image diagnostics."
requirements-completed: []
coverage:
  - id: D1
    description: "MAX group synchronization accepts PyMax CONTACT payloads that omit contactId without weakening unrelated attachment validation."
    verification:
      - kind: integration
        ref: "uv run --with 'maxapi-python==2.3.1' pytest -q tests/test_worker/test_max_worker.py tests/test_max_worker_deployment.py tests/test_max_container_manager.py tests/test_messengers/test_max.py -x"
        status: pass
    human_judgment: false
  - id: D2
    description: "Production recipes rebuild a revision-labelled dynamic MAX image before worker teardown and expose its identity safely at runtime."
    verification:
      - kind: unit
        ref: "tests/test_max_worker_deployment.py and tests/test_worker/test_max_worker.py"
        status: pass
      - kind: other
        ref: "just --dry-run prod-build; just --dry-run prod-deploy; just --dry-run prod-hard-deploy"
        status: pass
    human_judgment: false
duration: 20min
completed: 2026-08-04
status: complete
---

# Quick Task 260804-8wh: MAX Redis BLPOP Timeout, CONTACT Compatibility, and Image Freshness Summary

**PyMax 2.3.1 CONTACT parsing compatibility, MAX image rebuild-before-teardown recipes, and credential-safe revision diagnostics**

## Performance

- **Duration:** 20 min
- **Completed:** 2026-08-04T07:31:50Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Added an idempotent, fail-closed PyMax 2.3.1 seam that accepts only missing CONTACT `contactId` values and rebuilds the dependent Message, Chat, and LoginResponse schemas.
- Proved raw chat/login payload parsing and MAX group synchronization continue normally while supplied contact IDs and unrelated attachment validation remain intact.
- Rebuilt `broadcaster-max-worker:latest` before dynamic worker teardown in every production path, including no-cache hard deploys, and exposed revision/PyMax version through the image, health endpoint, and startup diagnostics.

## Task Commits

1. **Task 1: Synchronize one MAX group whose latest message has an incomplete CONTACT attachment**
   - `ce62d61` test(260804-8wh): cover incomplete MAX contact payloads
   - `35bad07` feat(260804-8wh): tolerate incomplete MAX contact attachments
2. **Task 2: Rebuild and identify the MAX image in every production deploy path**
   - `49c0cbc` test(260804-8wh): specify MAX image deployment provenance
   - `d079396` test(260804-8wh): preserve redacted Redis endpoint assertion
   - `c254059` test(260804-8wh): capture just dry-run diagnostics
   - `61c4121` feat(260804-8wh): rebuild and identify MAX worker images

## Files Created/Modified

- `max_worker/pymax_compat.py` — narrow, idempotent PyMax 2.3.1 CONTACT compatibility.
- `max_worker/main.py` — activates the seam before client parsing and reports safe runtime identity.
- `max_worker/Dockerfile` — records the source revision in OCI metadata and runtime environment.
- `justfile` — builds the dynamic MAX image before production worker removal.
- `tests/test_worker/test_max_worker.py` — raw PyMax payload, group sync, health, and startup-redaction coverage.
- `tests/test_max_worker_deployment.py` — offline recipe ordering, no-cache, image metadata, and tag/context contracts.

## Decisions Made

- Kept `maxapi-python==2.3.1`; no unreviewed dependency substitution is available or needed.
- The compatibility function fails clearly for an unreviewed version that still exposes the incompatible required field, and is a no-op if upstream has already made it optional.
- Kept `broadcaster-max-worker:latest` and the container-manager API stable; the image now carries verifiable revision metadata.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test harness] Corrected offline deployment output capture and redaction expectation**
- **Found during:** Task 2
- **Issue:** `just --dry-run` writes its command trace to stderr, and the first assertion incorrectly rejected the intentionally safe Redis endpoint hostname.
- **Fix:** Combined stdout/stderr in the offline test helper and required the rendered endpoint while continuing to reject username/password values.
- **Files modified:** `tests/test_max_worker_deployment.py`, `tests/test_worker/test_max_worker.py`
- **Verification:** Full requested MAX test scope passed (62 tests).
- **Committed in:** `d079396`, `c254059`

**Total deviations:** 1 auto-fixed (Rule 1 test harness correction)

## Issues Encountered

- The sandbox's default uv cache was read-only and the exact PyMax package was not cached. The dependency was installed into `/tmp` using the exact plan-pinned coordinate after approval; no package choice changed.

## User Setup Required

None.

## Next Phase Readiness

The deployed MAX worker can now prove its image revision and PyMax release, while group synchronization survives the observed partial CONTACT payload.

## Self-Check: PASSED

- Required implementation and deployment test files exist.
- All six task commits are present in git history.
- No task stub, skipped test, or unrun requested verification remains.

---
*Quick task: 260804-8wh*
*Completed: 2026-08-04*

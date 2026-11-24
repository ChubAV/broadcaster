---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 04
subsystem: infra
tags: [just, docker, wa-worker, deploy, tdd]

requires:
  - phase: 19-zahvat-nomera-pri-podklyuchenii
    provides: "19-01 wave 1 (Telegram number capture); this plan is independent of it in code and only follows the wave order (D-13)"
provides:
  - "just recipe wa-worker-build *args: passing arguments to docker build with the tag broadcaster-wa-worker:latest"
  - "WA worker image rebuilt in prod-deploy, prod-hard-deploy (--no-cache) and prod-build, always before the WA worker containers are stopped"
  - "tests/test_wa_worker_deployment.py: offline just --dry-run contracts for the WA image recipes"
affects: [19-02, 19-08, deploy]

actuals:
  tokens: 3200
  tasks: 2
  commits: 4

plan_head_before: f65ed0f516177d79ffe433df74f7a1823fcb6b21
plan_head_after: c05910ee

tech-stack:
  added: []
  patterns:
    - "Offline deploy-recipe contracts: just --dry-run output is asserted on substring order, never executed"

key-files:
  created:
    - tests/test_wa_worker_deployment.py
  modified:
    - justfile

key-decisions:
  - "Separate test module for WA instead of editing tests/test_max_worker_deployment.py: the MAX module stays untouched and its five rules stay green"
  - "WA build is inserted right after the MAX build and before the first WA teardown line, because the recipes stop WA containers before MAX ones"
  - "prod-build also builds the WA image (owner decision OQ2), so no recipe builds MAX without WA"

requirements-completed: []

coverage:
  - id: D1
    description: "prod-deploy rebuilds the WA worker image before any WA worker container is stopped"
    requirement: PHONE-16
    verification:
      - kind: unit
        ref: "tests/test_wa_worker_deployment.py#test_prod_deploy_builds_the_wa_image_before_any_wa_worker_teardown"
        status: pass
    human_judgment: false
  - id: D2
    description: "prod-hard-deploy rebuilds the WA worker image with --no-cache before teardown; the soft deploy has no --no-cache build"
    requirement: PHONE-16
    verification:
      - kind: unit
        ref: "tests/test_wa_worker_deployment.py#test_prod_hard_deploy_rebuilds_the_wa_image_without_cache_before_teardown"
        status: pass
    human_judgment: false
  - id: D3
    description: "wa-worker-build hands its arguments to docker build and tags the image exactly as WA_WORKER_IMAGE"
    requirement: PHONE-16
    verification:
      - kind: unit
        ref: "tests/test_wa_worker_deployment.py#test_wa_worker_build_hands_its_arguments_to_docker_build_with_the_manager_tag"
        status: pass
    human_judgment: false
  - id: D4
    description: "prod-build builds the WA image after compose, next to MAX (owner decision OQ2)"
    verification:
      - kind: unit
        ref: "tests/test_wa_worker_deployment.py#test_prod_build_builds_the_wa_image_after_compose_next_to_max"
        status: pass
    human_judgment: false
  - id: D5
    description: "New WA worker containers actually start on the rebuilt image on the production stand"
    requirement: PHONE-16
    verification: []
    human_judgment: true
    rationale: "Live half of criterion 5 needs the production stand; it is check 1 of the 19-08 walkthrough (D-11) and the owner's deploy gate (D-26)"

duration: 12min
completed: 2026-11-22
status: complete
---

# Phase 19 Plan 04: WA worker image rebuild in deploy recipes Summary

**The three deploy recipes (prod-deploy, prod-hard-deploy, prod-build) now rebuild the WA worker image, with --no-cache in the hard deploy and always ahead of the WA container teardown, pinned by offline just --dry-run tests.**

## Performance

- **Duration:** 12 min
- **Tasks:** 2 (both TDD: RED then GREEN each)
- **Files modified:** 2 (`justfile`, new `tests/test_wa_worker_deployment.py`)

## Accomplishments

- `wa-worker-build` became `wa-worker-build *args:` (pattern of `max-worker-build *args`); `just wa-worker-build --no-cache` expands to `docker build --no-cache -t broadcaster-wa-worker:latest ./wa_worker`, and the tag is asserted equal to `WA_WORKER_IMAGE` from `app/services/wa_container_manager.py`.
- `prod-deploy` runs `just wa-worker-build` right after `just max-worker-build`; `prod-hard-deploy` runs `just wa-worker-build --no-cache`; `prod-build` runs `just wa-worker-build` after the MAX build.
- Order rule: the build substring precedes the first `label=broadcaster.role=wa-worker` substring in the dry-run output of both deploy recipes. The soft deploy has no `--no-cache` WA build, the hard one has.
- Existing steps were not moved or removed: `label=broadcaster.role=wa-worker` count is still 11, `just max-worker-build` count is 3.

## Task Commits

1. **Task 1 (tracer): prod-deploy rebuilds the WA image** - RED `612f0abc` (test), GREEN `6ca1f28d` (feat)
2. **Task 2: hard deploy without cache and prod-build (OQ2)** - RED `a1c86cef` (test), GREEN `c05910ee` (feat)

**Plan metadata:** committed as `docs(19-04): complete WA worker image deploy plan` right after this file.

## TDD

### RED evidence

- **Task 1.** Command: `uv run pytest tests/test_wa_worker_deployment.py -q -p no:randomly --junit-xml=.gsd/tdd-evidence/19-04/red1.xml`, exit code 1, `2 failed`. Target `test_prod_deploy_builds_the_wa_image_before_any_wa_worker_teardown` failed on `AssertionError: prod-deploy не пересобирает образ WA-воркера`. `gsd_run check tdd-red-evidence` on the camelCase record (JUnit XML as `output`) returned `RED_EVIDENCE_OK` (`target_test_failed`). Semantic assessment: the target ran and failed on the planned assertion (the recipe lacks `just wa-worker-build`); the sibling test failed because `just` rejects an argument for an argument-less recipe, which is the Pitfall 10 cause itself.
- **Task 2.** Same command shape with `red2.xml`, exit code 1, `2 failed, 2 passed`. Target `test_prod_hard_deploy_rebuilds_the_wa_image_without_cache_before_teardown` failed on `AssertionError: prod-hard-deploy не пересобирает образ WA-воркера без кэша`; `check tdd-red-evidence` returned `RED_EVIDENCE_OK`. The sibling `test_prod_build_builds_the_wa_image_after_compose_next_to_max` failed with `ValueError` (substring `just wa-worker-build` absent from `prod-build`), the intended cause.
- Evidence files live in the self-ignoring `.gsd/tdd-evidence/19-04/` of the worktree and are removed with it; this section is the durable record.

### GREEN

- Task 1: `wa-worker-build *args:` plus one line in `prod-deploy`; `7 passed` (2 WA tests + 5 MAX tests).
- Task 2: one line in `prod-hard-deploy`, two lines and a comment in `prod-build`; `9 passed` (4 WA + 5 MAX).

### REFACTOR

None needed; no refactor commit.

### TDD Gate Compliance

RED (`test(19-04)`) precedes GREEN (`feat(19-04)`) for both tasks; gate sequence satisfied.

## Verification

- `uv run pytest tests/test_wa_worker_deployment.py tests/test_max_worker_deployment.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_declared_invariants.py tests/test_planning/test_executed_plans_kept_their_scope.py -q -p no:randomly` (under the shared flock): `1233 passed`.
- `just --dry-run prod-deploy`, `just --dry-run prod-hard-deploy`, `just --dry-run wa-worker-build --no-cache` give the expected substrings; no recipe was executed.
- Acceptance counts: `wa-worker-build \*args:` 1; `just wa-worker-build` 3; `just wa-worker-build --no-cache` 1; `just max-worker-build` 3; `label=broadcaster.role=wa-worker` 11.

## Decisions Made

- Separate module `tests/test_wa_worker_deployment.py` with its own `dry_run(*words)` helper, so the MAX module and its five rules stay untouched.
- WA build placed right after the MAX build; order anchored on the first `label=broadcaster.role=wa-worker` substring (the WA teardown precedes the MAX one in the recipes).

## Deviations from Plan

None - plan executed exactly as written.

CLAUDE.md note (no edit made): its command list names `just wa-worker-build` under "WA Worker -> Build image"; the recipe keeps that name and now also accepts arguments, and prod recipes now build the WA image as well. The orchestrator may refresh that line if wanted.

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None - no new network endpoint, auth path or schema; only deploy recipe lines. T-19-12 and T-19-13 are mitigated by the WA build in all three recipes ahead of the teardown and by the order rule.

## User Setup Required

None - no external service configuration required. Rolling the change out to the production stand is the owner's deploy gate (D-26); the live half of criterion 5 is check 1 of the 19-08 walkthrough.

## Next Phase Readiness

PHONE-16 stays Pending in REQUIREMENTS.md by instruction (closes at phase verification). 19-02 (`wa_worker/index.js`) now reaches production through `prod-deploy` / `prod-hard-deploy`.

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

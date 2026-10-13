---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 24
subsystem: testing
tags: [pytest, import-hygiene, phone-writer, gap-closure]

# Dependency graph
requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "plan 16-19: ACCOUNT_WITHOUT_ID_AFTER_FLUSH in app/application/accounts/phone.py and the rule test_each_refusal_of_the_recorder_names_its_own_cause (RED 80347a94 read the constant through the module object)"
provides:
  - "The writer test imports both refusal constants of record_reported_phone one way, by name from app.application.accounts.phone"
  - "The second import path (the writer module object under the alias writer_module) is removed together with its only use"
affects: [phase-19-connection-wizard, 16-25-review-disposition]

# Actuals (#2632): estimateTokens scale (chars/4 over the realized diff)
actuals:
  tokens: 301        # 1204 chars of `git diff 99002b16 d9cfd6c4` / 4
  tasks: 1
  commits: 1         # MEASURED: git rev-list --count 99002b16..HEAD at SUMMARY write
plan_head_before: 99002b1608ed3954cbd76147be6f04d069d61071
plan_head_after: d9cfd6c4ec865b4db8f8cfb8bc4ce3228e97b9ed

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A test reads every constant of a module under test through one import path (by name), never mixed with a module-object alias"

key-files:
  created: []
  modified:
    - tests/test_application/test_account_phone_writer.py

key-decisions:
  - "IN-12 closed by owner decision O-11 as a separate type: execute plan: import hygiene with no RED by construction, committed as refactor(16-24)"

patterns-established:
  - "Import hygiene: constants of the writer module come in by name, next to their siblings, in one from-import block"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "ACCOUNT_WITHOUT_ID_AFTER_FLUSH is imported by name next to ACCOUNT_NOT_IN_SESSION; the writer module object is no longer imported (IN-12, O-11)"
    requirement: "PHONE-02"
    verification:
      - kind: other
        ref: "uv run python -c \"import ast, pathlib; ... assert {'ACCOUNT_NOT_IN_SESSION', 'ACCOUNT_WITHOUT_ID_AFTER_FLUSH'} <= named; assert module_objects == []; print('OK')\" -> OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "Assertions are unchanged: the refusal rule compares with the same writer-module constant and is green; 24 writer rules and 4 race rules all pass; writer module and race test untouched"
    requirement: "PHONE-02"
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly -> 28 passed"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py -k 'names_its_own_cause or outside_this_session or never_added or pending_member' -> 8 passed, 16 deselected"
        status: pass
      - kind: other
        ref: "pytest tests/test_application/test_account_phone_writer.py --co -> 24 tests collected"
        status: pass
      - kind: other
        ref: "git diff --quiet cce988cb -- app/application/accounts/phone.py -> 0; git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py -> 0"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-10-13
status: complete
---

# Phase 16 Plan 24: Writer-test refusal constants imported by name Summary

**The writer test now imports `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` by name from `app.application.accounts.phone`, next to `ACCOUNT_NOT_IN_SESSION`. The `writer_module` alias import, left over from RED commit `80347a94`, is gone. The refusal rule compares with the same constant object, all 24 writer rules stay green, and the writer module and race test are byte-identical to before (IN-12, owner decision O-11).**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-13T09:58:23Z
- **Completed:** 2026-10-13T10:04:38Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` is in the `from app.application.accounts.phone import (…)` block, in alphabetical order right after `ACCOUNT_NOT_IN_SESSION`.
- `from app.application.accounts import phone as writer_module` is removed. Its only use, the comparison in `test_each_refusal_of_the_recorder_names_its_own_cause`, now reads the by-name constant. A by-name import binds the same object, so the assertion is unchanged.
- No assertions, messages or other rules changed. `app/application/accounts/phone.py` and `tests/test_application/test_account_phone_race.py` are untouched, so the D-08 race test and its read-check-write negation still stand.

## Task Commits

1. **Task 1 (tracer): import `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` by name, drop the module-object import** - `d9cfd6c4` (refactor)

**Plan metadata:** the `docs(16-24)` commit that carries this SUMMARY.

## TDD Gate Compliance

`phase.tdd-applicable` is true only because `workflow.tdd_mode=true`. The plan itself is `type: execute`, with one `type="tracer"` task and no `tdd="true"` task. Its frontmatter comment explains why: this is import hygiene that changes no behaviour or assertion, so it has no RED by construction, and it is not `type: tdd` because the `tdd.review-checkpoint` gate judges `tdd` plans by RED/GREEN pairs. So there is no RED/GREEN pair, and none was manufactured. The only code commit is `refactor(16-24)`, which is the type the plan names.

**Tracer feedback gate:** this run is interactive (`auto_advance: false`, `_auto_chain_active: false`) with `human_verify_mode: end-of-phase`, and the tracer's `<verify>` has only `<automated>` steps (row 3 of the chain). The `<verify>` was re-run green just before the commit, in the same `&&` chain, so no checkpoint was raised. There are no expansion tasks.

## Verification (all on the final tree `d9cfd6c4`, under the shared pytest lock)

| Check | Result |
|-------|--------|
| `<automated>` 1: `pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly` | 28 passed (24 writer + 4 race) |
| `<automated>` 2: AST import check | prints `OK` |
| `<automated>` 3: `-k "names_its_own_cause or outside_this_session or never_added or pending_member"` | 8 passed, 16 deselected |
| Acceptance: `--co` on the writer test | `24 tests collected` |
| Acceptance: `git diff --quiet cce988cb -- app/application/accounts/phone.py` | exit 0 |
| Acceptance: `git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py` | exit 0 |
| Acceptance: `git log --format=%s cce988cb..HEAD -- tests/test_application/test_account_phone_writer.py` | exactly one line, `refactor(16-24): import ACCOUNT_WITHOUT_ID_AFTER_FLUSH by name in the writer test` |
| Phase quick-run set (`test_phone.py`, writer, race, single-writer gate, privacy gate, `test_messenger_account_phone_check.py`, `tests/test_migrations`) | 856 passed (base: 856) |
| `tests/test_application -q -p no:randomly` | 601 passed (base: 601) |
| Cross-cutting source-reading gates (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`) | 576 passed in 2:36 (base: 576) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `uv run python scripts/prohibitions_census.py --check` | exit 0; registry 802 rows, bijection with the census |
| `tests/test_planning -q` | run after this SUMMARY commit, as the orchestrator requires. The count is in the executor's final message, because the SUMMARY cannot be amended. |

Both phase gates (`tests/test_phone_privacy_gate.py`, `tests/test_application/test_phone_single_writer_gate.py`) are in the quick-run set above and passed there. The edit is in `tests/`, so neither gate's live tree changes.

## Files Created/Modified

- `tests/test_application/test_account_phone_writer.py`: the by-name import block now holds both refusal constants, the `writer_module` alias import is removed, and the one comparison reads the by-name constant (2 insertions, 2 deletions).

## Decisions Made

None beyond the plan, which follows owner decision O-11: close IN-12 as part of this round instead of deferring it to the backlog.

## Deviations from Plan

None - plan executed exactly as written.

**Substitutions the orchestrator directed (not deviations):**
- `graphify update .` was not run. The worktree has no `graphify-out/`, and the orchestrator updates the graph after the merge.
- The full suite (`just test`) was not run. The orchestrator's post-merge gate runs it on the merged tree.
- No `deferred-items.md` was created, and nothing was deferred.

## Issues Encountered

None. The worktree sandbox rejected two compound shell commands: one ran `git` inside a conditional chain, the other passed a shell-variable path to `sed`. Both were rerun as plain commands. No guard was bypassed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- IN-12 is closed in code. Plan 16-25 records its disposition row, under the real topic of commit `d9cfd6c4`.
- Phase 19's connection wizard, the first product caller of `record_reported_phone`, now relies on a writer specification that reads both refusal constants one way. If either constant changes, the rule that pins it fails.

## Self-Check: PASSED

- FOUND: `tests/test_application/test_account_phone_writer.py` (modified, committed in `d9cfd6c4`)
- FOUND: `d9cfd6c4` is HEAD of `worktree-agent-afa7af8fa5b52f23f`, measured with `git rev-parse HEAD` → `d9cfd6c4ec865b4db8f8cfb8bc4ce3228e97b9ed`
- Commit count measured from the ledger: `git rev-list --count 99002b16..HEAD` → 1
- Post-commit deletion check: no deletions

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-13*

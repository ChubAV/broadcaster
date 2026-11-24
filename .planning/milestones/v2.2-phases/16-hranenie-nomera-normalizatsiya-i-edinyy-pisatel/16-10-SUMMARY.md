---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 10
subsystem: planning-records
tags: [code-review, disposition, state, prohibitions-registry, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "GREEN commits of 16-07 (CR-01, WR-03, WR-04), 16-08 (WR-05), 16-09 (WR-01, WR-02)"
provides:
  - "16-REVIEW-DISPOSITION.md: 11/11 findings disposed — 6 fixed with verified commit hashes, 5 deferred with reason and addressee; open 0, total 11"
  - "STATE.md Deferred Items row 'Phase 16 → Phase 18' for IN-01 (blank manual input clears the manual number; PHONE_ERROR_BLANK unreachable through the writer)"
  - "Prohibitions registry confirmed in step with plans 16-07…16-10 (reseed no-op, 764 rows, census --check exit 0)"
affects: [phase-18-planning, code-review-gate-rerun, verify-work-16]

actuals:
  tokens: 2375      # chars/4 over the realized diff be0bf54e..14e60e75 (9498 chars)
  tasks: 2
  commits: 2        # MEASURED: git rev-list --count be0bf54e..HEAD at SUMMARY write
plan_head_before: be0bf54eda5548d854032c12d375e874e4975d06
plan_head_after: 14e60e75cb96a8f2b94116e7c67e2aedb2095f51

tech-stack:
  added: []
  patterns:
    - "Disposition table is the record the code_review_gate re-reads; frontmatter is derived from the table in the same commit"
    - "A finding addressed to a later phase is duplicated into STATE.md Deferred Items, because later planners do not read phase review files"

key-files:
  created:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-10-SUMMARY.md
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md
    - .planning/STATE.md

key-decisions:
  - "WR-04's Source cell carries the named boundary П-1 from 16-07 (a 7-digit TOO_SHORT fragment like «1234567» is still accepted on the auto path; owner refused a code-888 special case under О-1), so the `fixed` mark does not hide what remains open by design"
  - "Example numbers inside Source cells are written in guillemets, not backticks: the plan's hash check reads every backticked 7–40 hex-digit token as a commit"
  - "Registry reseed left the file unchanged (orchestrator had seeded 16-07…16-10 rows when the plans were committed); no chore commit was made"

patterns-established:
  - "fixed row form: `<plan>` задача N, GREEN `<hash>` — one phrase on what changed"

requirements-completed: ["диспозиция-ревью-16"]

coverage:
  - id: D1
    description: "All 11 findings of 16-REVIEW.md have a disposition: CR-01 and WR-01…WR-05 fixed with their GREEN commits named, IN-01…IN-05 deferred with reason and addressee; no open row; frontmatter agrees (open 0, total 11)"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "Task 2 <automated> table check (11 rows, dispositions, git cat-file -e on each hash) — printed `OK 8 commits`"
        status: pass
      - kind: other
        ref: "grep -c '| open |' 16-REVIEW-DISPOSITION.md → 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "IN-01 addressed to Phase 18 in STATE.md §Deferred Items, a single new row with no other STATE.md change"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "Task 1 <automated> IN-01 row check — printed `OK`; grep -c 'IN-01 ревью фазы 16' .planning/STATE.md → 1; git diff --numstat STATE.md → 1 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Prohibitions registry in bijection with the census including plans 16-07…16-10; records suite green after this plan's own commits"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → exit 0, 'реестр: 764 строк, биекция с переписью — согласие'"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_planning -q -p no:randomly → 218 passed, 2 skipped (after each task commit)"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-09
status: complete
---

# Phase 16 Plan 10: Review Finding Dispositions Summary

**All 11 phase 16 review findings now have a recorded outcome. Six are `fixed`, each naming the GREEN commit that closed it, and every named commit was checked with `git cat-file`. Five are `deferred` with a reason and an addressee. IN-01 is also recorded in STATE.md for the Phase 18 planner.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-09T15:32:55Z
- **Completed:** 2026-10-09T15:39:56Z
- **Tasks:** 2 (1 tracer, 1 auto)
- **Files modified:** 2, plus this SUMMARY

## Accomplishments

- `16-REVIEW-DISPOSITION.md` has 11 rows and none is `open`:

  | Finding | Disposition | Closing commit(s) |
  |---|---|---|
  | CR-01 | fixed | `97e62918` (16-07 task 1) |
  | WR-04 | fixed | `ae44c1d0` (16-07 task 2), with boundary П-1 named |
  | WR-03 | fixed | `fdb12dd5` (16-07 task 3) |
  | WR-05 | fixed | `67a25113`, `bee23ee2` (16-08 tasks 1–2) |
  | WR-01 | fixed | `a97179ab`, `78495634` (16-09 tasks 1–2) |
  | WR-02 | fixed | `6ed63a95` (16-09 task 3) |

  - IN-01 is deferred to Phase 18.
  - IN-02 goes to the owner / backlog (the exact pin).
  - IN-03 is a note with no work attached (an untested redundant predicate).
  - IN-04 goes to the backlog, to the owner of `scripts/prohibitions_census.py`.
  - IN-05 goes to the backlog (the header of the migration-0023 test).
  - The frontmatter matches the table: `open: 0`, `total: 11`, titles unchanged.
- **Each hash was checked three ways before it was written:**
  - `git log --no-walk`: the subject starts with `feat(16-NN)` of the right plan.
  - `git show --stat`: the commit touches the file the finding names.
  - `git branch --contains`: the commit is reachable from HEAD.
- `.planning/STATE.md` §Deferred Items has one new row, `Phase 16 → Phase 18`, for IN-01. It covers two problems: blank manual input clears a manual number with no confirmation, and `PHONE_ERROR_BLANK` cannot be reached through `set_manual_phone`. The Phase 18 form must choose between an explicit "clear" action and showing that text. Today D-07 / PHONE-10 prescribe the behaviour. The diff to STATE.md is exactly one added line, and no `state.*` verb was used.
- The prohibitions registry is unchanged. `--seed-registry` reported `реестр не изменился: 764 строк` ("registry unchanged: 764 rows"), and `--check` exited 0 with bijection agreement. No wording of the prohibitions in plans 16-07…16-10 was touched.

## Task Commits

1. **Task 1 (tracer): IN-01 deferred to Phase 18 in the disposition and in STATE.md**: `fb490e3e` (docs)
2. **Task 2: remaining ten dispositions; registry reseed and records suite**: `14e60e75` (docs)

There was no registry `chore(16-10)` commit, because the reseed was a no-op.

**Tracer feedback gate:** interactive run, `human_verify_mode` = end-of-phase, and the tracer's `<verify>` is automated-only. So the verify was re-run after the Task 1 commit (`tests/test_planning`: 218 passed, 2 skipped), and execution continued to Task 2 without a checkpoint.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`: 11 disposition rows with Source cells. The frontmatter dispositions are derived from the table, and `open` is 0.
- `.planning/STATE.md`: one row in the first §Deferred Items table, placed before `### Подтверждено при закрытии вехи v2.0` (the section for items confirmed at the v2.0 close).
- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-10-SUMMARY.md`: this file.

## Verification Run (final tree, under the pytest lock)

| Gate | Result |
|---|---|
| Task 1 `<automated>` IN-01 row check | `OK` |
| Task 2 `<automated>` table check | `OK 8 commits` (CR-01 1, WR-01 2, WR-02 1, WR-03 1, WR-04 1, WR-05 2) |
| `grep -c "\| open \|" 16-REVIEW-DISPOSITION.md` | `0` |
| `uv run python scripts/prohibitions_census.py --check` | exit 0, 764 rows, bijection agreement |
| `uv run pytest tests/test_planning -q -p no:randomly` | 218 passed, 2 skipped (after Task 1 commit and after Task 2 commit) |
| `tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py` | 120 passed |
| `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_templates tests/test_application/test_declared_invariants.py` | 576 passed (2:29) |

The full suite was not run, per the orchestrator's host limits. `just test` stays the phase gate before `/gsd-verify-work`.

## Decisions Made

- **WR-04 is `fixed`, and its cell names П-1.** 16-07 closed the finding as reported: the floor is now 7, local-only numbers are refused, and the pinned junk row was rewritten with a chronicle. One boundary remains on purpose. A 7-digit `TOO_SHORT` fragment such as «1234567» is still stored, because telling it apart from Fragment would need a code-888 special case, which the owner refused under О-1. The cell says this, so the `fixed` mark does not reopen CR-01/WR-04 and does not hide the boundary either.
- **The frontmatter is derived from the table by a script** that matches each row by id. The two cannot drift, and titles and other keys are left alone (21 changed lines: 10 rows, 10 `disposition:` lines and `open`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] An example number in the WR-04 Source cell was read as a commit hash**
- **Found during:** Task 2, first run of its `<automated>` check (before any commit)
- **Issue:** My WR-04 cell quoted the П-1 fragment as a backticked `1234567`. The check reads every backticked 7–40 hex-digit token in a `fixed` row as a commit, so `git cat-file -e 1234567^{commit}` failed (exit 128).
- **Fix:** The number is now written in guillemets («1234567»), so the only backticked hex tokens left in `fixed` rows are real commits.
- **Files modified:** `16-REVIEW-DISPOSITION.md`
- **Verification:** The check re-ran and printed `OK 8 commits`, with the per-finding hash map shown.
- **Committed in:** `14e60e75` (Task 2 commit)

**Total deviations:** 1 auto-fixed (1 bug, introduced and caught within this plan before commit).
**Impact on plan:** None on scope. Also, the WR-04 cell carries more text than the `<scope_note>` registry entry: the П-1 boundary was added at the orchestrator's request ("carry, not hide").

## Issues Encountered

None.

## Known Stubs

None. This plan touches only records and no product code.

## User Setup Required

None. No external service configuration is needed.

## Next Phase Readiness

- The gap-closure batch 16-07…16-10 is fully executed. The phase verdict stays `gaps_found` until re-verification. No requirement was marked Complete, and REQUIREMENTS.md, ROADMAP.md, PLAN files, 16-REVIEW.md and VERIFICATION/VALIDATION were not touched.
- Next steps, in order:
  1. Full `just test` (the phase gate).
  2. `/gsd-verify-work 16`.
  3. `/gsd-validate-phase 16`, since the batch rows in `16-VALIDATION.md` are still `⬜ pending`.
- When the code-review gate runs again, it will keep these table rows, because the table, not the frontmatter, is what it re-reads.
- The Phase 18 planner should read the new STATE.md Deferred Items row about IN-01 before planning the form.

## Self-Check: PASSED

- FOUND: `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-10-SUMMARY.md`
- FOUND: `fb490e3e` and `14e60e75` are both ancestors of HEAD, and so are all 8 fixing commits named in the disposition table.
- After the SUMMARY commit `9fe44e0c`:
  - `tests/test_planning`: 218 passed, 2 skipped.
  - `prohibitions_census.py --check`: 764 rows, bijection agreement.
  - The working tree is clean.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-09*

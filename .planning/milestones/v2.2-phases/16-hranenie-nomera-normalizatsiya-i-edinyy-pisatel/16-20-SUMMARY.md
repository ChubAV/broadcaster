---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 20
subsystem: planning-records
tags: [code-review-disposition, prohibitions-registry, gap-closure, records]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "GREEN commits of round-3 gap closure: 16-16 (333bf8e0, 5c3ffb94), 16-17 (9b074697, 417229e7, 282c16d7, self-check b7a1e127, e3f46b63, e53d9320), 16-18 (38727536, 5a7cc660), 16-19 (b2758f43; guard 27cfc105)"
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-REVIEW-DISPOSITION.md as it stands at 7a4ee433 (16 prior rows, five round-2 rows at open)"
provides:
  - "16-REVIEW-DISPOSITION.md: WR-09, WR-10, IN-08, IN-09, IN-10 recorded as fixed. Each Source cell names its plan, task(s) and verified GREEN commit(s). open 0, total 21"
  - "Proof that the 16 prior rows and their frontmatter entries are byte-identical to 7a4ee433, including the tool's «(not in the current review)» tag and the deferred IN-01…IN-05 with their owners"
  - "Prohibitions registry confirmed in step with plans 16-16…16-20 without a reseed (census --check exit 0, 788 rows)"
affects: [phase-16-reverification, code_review_gate, gsd-verify-work]

actuals:
  tokens: 2526
  tasks: 2
  commits: 2
plan_head_before: a5173e03814fc82abf5d6dc72bf26b1ee8ec569b
plan_head_after: 4268ad700ed908ce7a455c240f7f43fff85c7ddc

tech-stack:
  added: []
  patterns:
    - "A `fixed` Source cell states the boundary its fixing SUMMARY measured, not the plan's prose. Germany is +1/+2, not 1–4. JUDGED_PARAMETERS has 34 rows, not 33. flag_modified is a write"

key-files:
  created:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-20-SUMMARY.md
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md

key-decisions:
  - "WR-10's Source cell names all six GREEN commits of 16-17: tasks 1–3 plus the three executor self-check cycles (b7a1e127, e3f46b63, e53d9320). Every backticked hash has a feat(16-17) subject"
  - "IN-10's cell names the guard-test commit «27cfc105» in guillemets, not backticks. Its subject is test(16-19), and the hash check reads every backticked hex token as a feat commit"
  - "The prohibitions registry was not reseeded (orchestrator note 3). --check was already green before any edit: exit 0, 788 rows, bijection agrees. The registry already holds plan 16-20's three prohibition rows. The file is unchanged"

patterns-established: []

requirements-completed: ["диспозиция-ревью-16"]

coverage:
  - id: D1
    description: "All five round-2 re-review findings (WR-09, WR-10, IN-08, IN-09, IN-10) are fixed in 16-REVIEW-DISPOSITION.md. Each Source cell names its plan, task(s) and GREEN commit(s). All 11 backticked hashes are ancestors of HEAD whose subject starts with feat(<that plan>). The frontmatter matches the table: open 0, total 21"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "Task 2 <automated> python check (verbatim from the plan) -> 'OK 11 commits'"
        status: pass
      - kind: other
        ref: "Task 1 <automated> python check (WR-09 row, open 4) -> 'OK', before commit f3be32f3"
        status: pass
      - kind: other
        ref: "grep -c '| open |' 16-REVIEW-DISPOSITION.md -> 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "The 16 prior rows (WR-06…WR-08, IN-06, IN-07, IN-01…IN-05, CR-01, WR-01…WR-05) and their frontmatter entries are byte-identical to 7a4ee433"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "Task 2 <automated> check: moved == [] and old frontmatter rows equal"
        status: pass
      - kind: other
        ref: "git diff --numstat 7a4ee433 -- 16-REVIEW-DISPOSITION.md -> 11/11: five rows, five dispositions, open"
        status: pass
    human_judgment: false
  - id: D3
    description: "Prohibitions registry in step with plans 16-16…16-20, and the records suite is green"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check -> exit 0, 788 rows"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_planning -q -p no:randomly -> 218 passed, 2 skipped (before each task commit and after f3be32f3)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Source cell wording is faithful to the fixes. Each cell summarises its fixing plan's SUMMARY and the shipped code, including the deviations wave 1 recorded"
    verification: []
    human_judgment: true
    rationale: "Fidelity of prose to the fix is a reading judgement. The automated check proves the hashes and dispositions, not the accuracy of each sentence"

duration: 8min
completed: 2026-10-12
status: complete
---

# Phase 16 Plan 20: Round-2 Review Dispositions Recorded as Fixed Summary

**The five round-2 re-review findings (WR-09, WR-10, IN-08, IN-09, IN-10) now read `fixed` in `16-REVIEW-DISPOSITION.md`. Their cells name 11 verified `feat(16-1N)` GREEN commits from the round-3 batch. The 16 prior rows are byte-identical to `7a4ee433`: open 0, total 21. The prohibitions registry was already in step at 788 rows.**

## Performance

- **Duration:** about 8 min
- **Started:** 2026-10-12T19:54:30Z
- **Completed:** 2026-10-12T20:02:15Z
- **Tasks:** 2 of 2
- **Files modified:** 1, plus this SUMMARY

## Accomplishments

- **WR-09.** Cell: 16-16 task 1, GREEN `333bf8e0`, owner decision О-7 (а).
  - Fix: a manual number is accepted only if its length is possible for an account type.
  - Boundary: the docstring names Germany +1/+2 and Israel +2/+3.
- **IN-08.** Cell: 16-16 task 3, GREEN `5c3ffb94`, О-8.
  - Fix: the header names both accepted classes, «400 из 558» and «583 из 1935».
- **WR-10.** Cell: 16-17 tasks 1–3, GREENs `9b074697`, `417229e7`, `282c16d7`.
  - Also named: the three self-check GREENs `b7a1e127`, `e3f46b63`, `e53d9320`.
  - Cell facts: `JUDGED_PARAMETERS` has 34 rows; `flag_modified` is a write.
- **IN-09.** Cell: 16-18 tasks 1–2, GREENs `38727536`, `5a7cc660`.
  - The same-axis forms that 16-18 caught beyond its plan are named.
- **IN-10.** Cell: 16-19 task 1, GREEN `b2758f43`, О-8.
  - The guard-test commit «27cfc105» is named in guillemets.
- **Frontmatter.** It matches the table: five dispositions are `fixed`, `open: 0`, `total: 21`. Titles and `recorded` are unchanged.

## Task Commits

1. **Task 1 (tracer): WR-09 fixed** — `f3be32f3` (docs).
   - Tracer gate: interactive run, `end-of-phase`, verify is `<automated>`-only.
   - The verify was re-run after the commit and passed (218 passed, 2 skipped). Then I expanded to Task 2.
2. **Task 2: IN-08, WR-10, IN-09, IN-10 fixed; registry confirmed** — `4268ad70` (docs).

**Plan metadata:** the `docs(16-20)` commit that carries this SUMMARY.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`. Five rows and their frontmatter changed from `open` to `fixed`, and `open` went from 5 to 0. The diff against `7a4ee433` is 11 lines.
- `.planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` was **not modified**. See Decisions.

## Decisions Made

- **Cells follow the measured truth from wave 1, not the plan's prose:**
  - WR-09 names Germany +1/+2, with +3/+4 refused by the E.164 limit. The plan's scope_note said "Germany and Israel with 2+".
  - WR-10 names 34 `JUDGED_PARAMETERS` rows (33 planned plus `flag_modified`) and records `flag_modified` as a write.
  - IN-09 names the extra same-axis forms.
- **Commit hashes.** All 11 backticked hashes were checked with three tests: `git cat-file -e`, `merge-base --is-ancestor HEAD`, and a subject that starts with `feat(<plan>)`. The `test(16-19)` guard commit is in guillemets.
- **No registry reseed.** `--check` gave exit 0 with 788 rows before any edit and again on the final tree. The registry already holds plan 16-20's rows, so `--seed-registry` was not run just to go through the motions (orchestrator note 3). The registry header was not touched.

## Deviations from Plan

**1. [Orchestrator directive] `--seed-registry` was not run**
- **Plan step:** Task 2 step 4 says to run `--seed-registry`, then `--check`.
- **Why not:** the orchestrator said not to reseed when `--check` is already green. The plan itself expects the file to stay unchanged.
- **Measured:** `--check` exit 0 with 788 rows ("биекция с переписью — согласие"). `15-prohibitions-registry.yaml` is unchanged.

**Total deviations:** 1 (a process directive). **Impact:** none. The registry outcome is identical to an idempotent reseed.

## Gates on the Final Tree

All pytest runs used the shared `flock` on `scratchpad/pytest.lock`.

| Gate | Result | Base |
|------|--------|------|
| Task 1 `<automated>` (WR-09 row, `open: 4`) | `OK` | — |
| Task 2 `<automated>` (21 rows, carry, hashes, frontmatter) | `OK 11 commits` (floor 8) | — |
| `grep -c "\| open \|"` | 0 | — |
| Pipe count per row | 21 of 21 rows have exactly 5 | — |
| Both phase gates (`test_phone_privacy_gate.py`, `test_phone_single_writer_gate.py`) | 457 passed | — |
| Phase quick-run set (7 paths) | 856 passed | 856 |
| Cross-cutting gates (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (2:32) | 576 |
| `scripts/prohibitions_census.py --check` | exit 0, 788 rows | exit 0, 788 |
| `tests/test_planning` (before each task commit, and after `f3be32f3`) | 218 passed, 2 skipped | 218 / 2 |
| `tests/test_planning` after this SUMMARY commit | reported in the executor's return message | 218 / 2 |

**Substitutions:**
- I did not run the full suite (`just test`). The orchestrator ran it on the merged base `15b12ad1`: 4841 passed, 2 skipped. This plan changes no code.
- I did not run `graphify update .`.
- I did not create `deferred-items.md`.
- I did not touch STATE.md, ROADMAP.md or REQUIREMENTS.md. No `requirements.mark-complete` and no `state.*` / `roadmap.*` verbs were used.

## Issues Encountered

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- All 21 findings of the phase 16 review have a disposition.
- Next steps belong to the orchestrator:
  - set the ROADMAP `- [x]` mark for 16-20 and update `progress.completed_plans`;
  - run the full `just test`;
  - run `/gsd-validate-phase 16`;
  - run `/gsd-verify-work` (round 4).
- `human_verification` 1 (35 prohibition verdicts) remains an owner act.

## Self-Check: PASSED

- FOUND: `16-REVIEW-DISPOSITION.md`, `16-20-SUMMARY.md`
- FOUND commits (ancestors of HEAD): `f3be32f3`, `4268ad70`
- FOUND GREEN hashes: all 11 cited hashes are ancestors with `feat(16-1N)` subjects. The guard `27cfc105` is an ancestor with a `test(16-19)` subject.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-12*

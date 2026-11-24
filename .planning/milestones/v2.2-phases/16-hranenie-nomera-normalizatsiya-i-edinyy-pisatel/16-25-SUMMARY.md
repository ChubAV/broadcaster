---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 25
subsystem: planning-records
tags: [review-disposition, code-review-gate, prohibitions-census, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "plans 16-21…16-24 (wave 1 of gap-closure round 4): fixing commits for WR-11, WR-12, WR-13, IN-11, IN-12"
provides:
  - "16-REVIEW-DISPOSITION.md: all five findings of the round-3 re-review (WR-11, WR-12, WR-13, IN-11, IN-12) are `fixed`, each Source cell naming the plan, the tasks, the fixing commits and the owner decision"
  - "The WR-11 cell records the correction of the narrow WR-09 wording (the real O-7 (a) remainder is «56 из 976» inputs in 36 regions); the WR-09 row itself is unchanged"
  - "The 21 prior rows and their frontmatter entries are byte-for-byte as at cce988cb, including the tool marker «(not in the current review)» and the IN-01…IN-05 title suffix"
  - "Frontmatter agrees with the table: open 0, total 26"
  - "Prohibitions registry checked: --seed-registry left it unchanged (802 rows), --check exit 0, bijection"
affects: [16-verification-round-5, code_review_gate, phase-16-close]

actuals:
  tokens: 2126       # chars/4 over `git diff 2d6f2cb5..d08308ef` (8502 characters)
  tasks: 2
  commits: 2         # MEASURED: git rev-list --count 2d6f2cb5..HEAD before the SUMMARY commit
plan_head_before: 2d6f2cb5c2de6f75f59b7e468c79f907a6a2144f
plan_head_after: d08308efe9fb6e265acbbd2e455e488f16071d52

tech-stack:
  added: []
  patterns:
    - "A `fixed` disposition cell names its fixing commits in backticks (checked as commits: ancestor of HEAD, real subject); test, RED and baseline hashes and all example numbers go in «ёлочки» so the hash check does not read them as fixing commits"

key-files:
  created: []
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md

key-decisions:
  - "WR-12 cites all nine GREENs of 16-22 (three task GREENs and six self-check GREENs); the RED commits, including 37ec629e whose body says «140» self-check forms against the measured «120», are named in «ёлочки» only"
  - "WR-13 cites the self-check GREEN 978a9408 (logger.parent) next to the two task GREENs, and records 16-23's deviation that a member of an identified logger stays a receiver by name pattern (stricter than the plan's literal design)"
  - "The IN-11 cell names the cce988cb AST baseline in «ёлочки», not backticks: a backticked hex token would be read as a fixing commit whose subject must start with refactor(16-21)"
  - "The registry was not reseeded for form: --seed-registry reported «реестр не изменился: 802 строк», so the registry file is not in any commit"

patterns-established: []

requirements-completed: ["диспозиция-ревью-16"]

coverage:
  - id: D1
    description: "Five findings of the round-3 re-review are `fixed`, each with existing fixing commits that are ancestors of HEAD and carry the expected subject (feat(16-21/22/23), refactor(16-21), refactor(16-24)); 15 hashes in total"
    verification:
      - kind: other
        ref: "task 2 <automated> one-liner (26 rows, moved old rows, hash subjects, ancestors, frontmatter) → OK 15 commits"
        status: pass
      - kind: other
        ref: "grep -c '| open |' 16-REVIEW-DISPOSITION.md → 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "The WR-11 cell records the correction of the narrow WR-09 wording; the WR-09 row is byte-for-byte as at cce988cb"
    verification:
      - kind: other
        ref: "task 1 <automated> one-liner → OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "The 21 prior rows and their frontmatter entries are unchanged; only the five rows, five disposition lines and the open line differ from cce988cb"
    verification:
      - kind: other
        ref: "diff against `git show cce988cb:…16-REVIEW-DISPOSITION.md` saved to the scratchpad: 11 changed lines, all expected; «(not in the current review)» count 21 = 21"
        status: pass
    human_judgment: false
  - id: D4
    description: "Prohibitions registry agrees with the census; records suite green"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → exit 0, «реестр: 802 строк, биекция с переписью — согласие»"
        status: pass
      - kind: unit
        ref: "tests/test_planning -q -p no:randomly → 218 passed, 2 skipped (before the task 2 commit; re-run after this SUMMARY commit is reported in the executor's return)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The prose of each Source cell states the wave-1 fixes and deviations truthfully (no paraphrase beyond the SUMMARYs)"
    verification: []
    human_judgment: true
    rationale: "Whether each cell's prose is faithful to 16-21…16-24 SUMMARYs is a reading judgement for the round-5 verifier; automation checks only hashes, subjects, ancestry and row shape"

duration: 9min
completed: 2026-10-13
status: complete
---

# Phase 16 Plan 25: Review disposition of the round-3 re-review — five findings fixed with named commits Summary

**All 26 findings in `16-REVIEW-DISPOSITION.md` now have a decision. WR-11, WR-12, WR-13, IN-11 and IN-12 are `fixed`, and each Source cell names its wave-1 commits (15 hashes, all ancestors of HEAD, with the real `feat(16-2N)` or `refactor(16-21/24)` subject). The WR-11 cell records the correction of WR-09's narrow wording; WR-09 and the other 20 prior rows are byte-for-byte as at `cce988cb`. The registry is unchanged at 802 rows, and `--check` is green.**

## Performance

- **Duration:** about 9 min
- **Started:** 2026-10-13T11:44:06Z
- **Completed:** 2026-10-13T11:53:29Z
- **Tasks:** 2 of 2
- **Files modified:** 1

## Accomplishments

- **WR-11** is `fixed`: 16-21 task 1, GREEN `dd164d6e`, owner decision O-9 (a). The cell names:
  - the measured remainder: «56 из 976» inputs in 36 regions, causes by account type (MOBILE / VOIP only / FIXED_LINE classes), and «15 из 56» valid per metadata;
  - the live-recount rule;
  - RED «71957ec1» and the test-text commit «93632304».

  It also records that WR-09's «граница названа в пункте 5 — Германия … и Израиль …» named two regions out of thirty-six.
- **WR-12** is `fixed`: 16-22. It cites GREENs `ecd1be76`, `4d6f286e`, `9f50ed19` and six self-check GREENs (`878b4679`, `dbe22dcc`, `a973ea55`, `ddbb33f7`, `a4c49b66`, `80153e32`), under O-10 (a). Wave-1 deviations recorded truthfully:
  - boundary (2) now names column names computed by a call («8 456» forms) as not caught;
  - the body of RED commit «37ec629e» says «140» forms, while the measured figure is «120».
- **WR-13** is `fixed`: 16-23. It cites GREENs `1852b951`, `e54fd6e3` and self-check GREEN `978a9408`, under the pass default. Also recorded:
  - the name-pattern receiver rule that is stricter than the plan;
  - the live numbers «221/68/93», 0 findings;
  - the row counts above the literal criterion («OK 90 39», «170»).
- **IN-11** is `fixed` by `9711cb39`, and **IN-12** by `d9cfd6c4`. Both use their real `refactor(…)` subjects and owner decision O-11.
- Frontmatter: five `disposition: fixed`, `open: 0`, `total: 26`. Titles, `recorded` and all other keys are unchanged.

## Task Commits

1. **Task 1 (tracer): WR-11 end-to-end.** `4d748089` (docs)
2. **Task 2: WR-12, WR-13, IN-11, IN-12, and the registry check.** `d08308ef` (docs)

**Plan metadata:** the `docs(16-25)` commit that carries this SUMMARY.

**Tracer feedback gate:** the run is interactive (`auto_advance: false`, `_auto_chain_active: false`) with `human_verify_mode: end-of-phase`, and the tracer's `<verify>` is automated-only (row 3). After the commit, `tests/test_planning` was re-run (218 passed, 2 skipped), and execution continued without a checkpoint.

## Verification (final tree `d08308ef`, under the shared pytest lock)

| Check | Result | Base |
|-------|--------|------|
| Task 1 `<automated>` (WR-11 row, WR-09 row vs `cce988cb`, `open: 4`) | `OK` (on the task 1 tree) | — |
| Task 2 `<automated>` (26 rows, 21 unmoved, hashes, subjects, ancestors, frontmatter) | `OK 15 commits` (needs ≥ 8) | — |
| `grep -c "\| open \|"` on the disposition file | `0` | 5 |
| Textual diff vs `cce988cb` | 11 lines: 5 disposition lines, `open`, 5 rows | — |
| «(not in the current review)» count | 21 | 21 |
| `prohibitions_census.py --seed-registry` | «реестр не изменился: 802 строк» | 802 |
| `prohibitions_census.py --check` | exit 0, «реестр: 802 строк, биекция с переписью — согласие» | exit 0 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | — |
| Both phase gates (`test_phone_privacy_gate.py`, `test_phone_single_writer_gate.py`) | 582 passed | — |
| Privacy gate `-s -k live_trees` | «app: файлов 100, вызовов 221, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | same |
| Phase quick-run set (7 paths) | 982 passed | 982 |
| Cross-cutting gates (htmx pairs, htmx gates, templates, declared invariants) | 576 passed (2:38) | 576 |
| `tests/test_planning -q -p no:randomly` | 218 passed, 2 skipped, before the task 1 commit, after it, and before the task 2 commit; the run after this SUMMARY commit is in the executor's return | 218 passed, 2 skipped |

**Substitutions (orchestrator notes 4 and 6):**
- The full suite (`just test`) was not run. The orchestrator ran it on the merged wave-1 tree (4967 passed, 2 skipped). This plan changes no code.
- `graphify update .` was not run.
- The plan commit ledger was kept in the scratchpad, not in the worktree's git dir.
- The plan's two `<automated>` one-liners, which call `git show` / `git log` / `git merge-base` from Python, ran as written. The sandbox did not refuse them, so they needed no substitution.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`: five rows and five frontmatter dispositions moved to `fixed`, `open` 5 → 4 → 0.
- `.planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml`: not changed. The reseed was idempotent, and the orchestrator had already seeded rows for 16-21…16-25.

## Decisions Made

- WR-12 lists all nine GREENs, because the plan asks for the self-check GREENs too. All RED and test commits are in «ёлочки», so the hash check reads only fixing commits.
- In the IN-11 cell, the AST baseline «cce988cb» is in «ёлочки». In backticks it would count as a fixing commit with the wrong subject.
- The registry was not reseeded for form. `--check` was already green, and the seed reported no change.

## Deviations from Plan

None. The plan was executed as written.

**Total deviations:** 0. **Impact:** none.

## Issues Encountered

- The sandbox refused one `git log` query with unquoted `(` in `--grep` patterns, calling it too complex to verify. The query was rerun with a quoted ERE pattern, and the logic was unchanged.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- The review ledger of phase 16 has 26 decided rows: 21 `fixed`, 5 `deferred`, and 0 `open`. The next `code_review_gate` run will carry all of them.
- The phase verdict is still `gaps_found` until round-5 verification. No requirement was marked Complete. STATE.md, ROADMAP.md and REQUIREMENTS.md are left to the orchestrator.
- `human_verification` item 1 of `16-VERIFICATION.md` (the 47 prohibition verdicts) is an owner act. It was not touched.

## Self-Check: PASSED

- FOUND: `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`
- FOUND: `4d748089`, `d08308ef`, both on this branch (`git rev-list --count 2d6f2cb5..HEAD` → 2)
- FOUND: all 15 cited fixing hashes are ancestors of HEAD and carry the expected subjects (task 2 `<automated>`)
- Post-commit deletion check: no deletions in either commit

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-13*

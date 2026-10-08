---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
plan: 06
subsystem: planning-records
tags: [roadmap, requirements, chronicle, d-30-d-32, fetch-02]

requires:
  - phase: 13-01
    provides: "four routes on respond(), complete removed, POST poll, GET qr-status 405, MANUAL_FETCH 5 -> 0, POLLING_FRAGMENTS blind spot measured"
  - phase: 13-04
    provides: "QRAuthState.user_id, _owned, status gone, byte-equal foreign/unknown answers, impersonation subject binding"
  - phase: 13-05
    provides: "criterion-2 gate closed by template branch with six negative controls, 20 POLLING_CASES rows"
provides:
  - "Chronicles beside criteria 1, 2, 3 and 5 of Phase 13 in .planning/ROADMAP.md"
  - "FETCH-02 chronicle in .planning/REQUIREMENTS.md (ownership check introduced, premise false)"
  - "Documentary record of criterion 5 with the base measurement (this SUMMARY)"
affects: [phase-13-verification, milestone-audit, 15-FETCH-03]

actuals:
  tokens: 1775     # chars/4 over the added lines of ROADMAP.md + REQUIREMENTS.md; this SUMMARY excluded
  tasks: 2
  commits: 2       # git rev-list --count d746c177..HEAD, measured before this SUMMARY commit
plan_head_before: d746c17754ac1b64a8f4a676d58365d9a0bf07ed

tech-stack:
  added: []
  patterns:
    - "Chronicle beside an unchanged criterion: for an outdated premise «НЕ БЫЛА ОШИБКОЙ — УСТАРЕЛА», for a false premise «НЕ УСТАРЕЛА — БЫЛА ЛОЖНОЙ»"

key-files:
  created:
    - .planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-06-SUMMARY.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Phase 13-06: the criterion-3 and FETCH-02 chronicles call the premise «сохранена» FALSE from the start, not outdated. They use a separate formula «ПОСЫЛКА НЕ УСТАРЕЛА — ОНА БЫЛА ЛОЖНОЙ» instead of the D-30/D-32 «не была ошибкой — устарела» (D-04)"
  - "Phase 13-06: FETCH-02 stays [ ] / Pending although requirements.ready-ids reports it ready. The mark follows phase verification, per the plan's must-have and test_requirement_completion_follows_verification.py"

requirements-completed: [FETCH-02]  # copied verbatim from the plan's `requirements` field; NOT marked Complete in REQUIREMENTS.md, see «FETCH-02 mark deferred»

coverage:
  - id: D1
    description: "Chronicles beside criteria 1, 2, 3 and 5 of Phase 13; criterion texts unchanged"
    requirement: FETCH-02
    verification:
      - kind: other
        ref: "grep -c '^\\*\\*Летопись критерия N: .*(Фаза 13, план 13-06' .planning/ROADMAP.md -> 1 for N = 1, 2, 3, 5"
        status: pass
      - kind: other
        ref: "git diff 344dc789 -- .planning/ROADMAP.md | grep -c '^-  [1-5]\\. ' -> 0 (54-line diff, not empty)"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_planning -q (44 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "FETCH-02 chronicle in REQUIREMENTS.md; checkbox [ ] and Pending cell untouched; .planning/research/* untouched"
    requirement: FETCH-02
    verification:
      - kind: other
        ref: "grep -c '^  \\*\\*Летопись FETCH-02: .*(Фаза 13, план 13-06, D-04)' .planning/REQUIREMENTS.md -> 1; '^- \\[ \\] \\*\\*FETCH-02\\*\\*' -> 1; '| FETCH-02 | Phase 13 | Pending |' -> 1; git diff --quiet 344dc789 -- .planning/research/ -> exit 0"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_planning -q -k 'requirement or flag_and_the_status' (16 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Criterion 5 recorded as documentary evidence with the base measurement"
    requirement: FETCH-02
    verification:
      - kind: other
        ref: "f=$(mktemp) && git show \"$(git merge-base HEAD master)\":app/templates/accounts/connect_tg_user.html > \"$f\" && grep -c '<form' \"$f\" -> 0"
        status: pass
    human_judgment: true
    rationale: "Criterion 5 is a documentary record by definition. Whether the wording is adequate for the milestone audit is a reader's judgment."

duration: 2min
completed: 2026-09-21
status: complete
---

# Phase 13 Plan 06: chronicles of criteria 1, 2, 3, 5 and FETCH-02 Summary

**The Phase 13 records now match what was built, and no criterion or requirement text was rewritten.** ROADMAP has four chronicles beside the criteria:
- **Criterion 1:** four routes answer fragments, `complete` was removed by D-01, and the poll moved from GET to POST.
- **Criterion 2:** the poller lives inside the waiting fragment, and the criterion is held by the rule over rendered responses, because the markup gate cannot see it.
- **Criterion 3:** the ownership check was INTRODUCED. The premise «сохранена» was false from the start, not outdated.
- **Criterion 5:** the wizard had no no-JS path before the phase either. The measured base page has zero forms.

REQUIREMENTS.md has the matching FETCH-02 chronicle. FETCH-02 stays unmarked until phase verification.

## Performance

- **Duration:** about 2 min from the start mark to this SUMMARY. The required reading of the five SUMMARYs, CONTEXT and ROADMAP ran before the mark.
- **Started:** 2026-09-21T16:29:42Z
- **Completed:** 2026-09-21T16:32Z
- **Tasks:** 2
- **Files modified:** 2 (`.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`), plus this SUMMARY

## Accomplishments

- **Criterion 1 chronicle (D-01, D-12).**
  - `complete` was removed, not converted, and GET `qr-status` answers 405.
  - The four routes (`start-qr`, `qr-status`, `verify-2fa`, `refresh-qr`) answer fragments from one template behind `#tg-connect-step`.
  - `NOT_YET_CONVERTED_COUNT` went 14 → 10.
  - Removed from the page: the 152-line script, the three `onclick` attributes (R-08-02) and the hidden sections.
  - The ~3 s window is accepted by the owner.
  - `MANUAL_FETCH_*` is a named zero. Today's `fetch(` count in `app/templates/` is 0, but the ban on it is FETCH-03, Phase 15.
  - The chronicle carries the idiom «ПОСЫЛКА НЕ БЫЛА ОШИБКОЙ — ОНА УСТАРЕЛА» and «НЕ ПРАВЯТСЯ».
- **Criterion 2 chronicle (D-05).**
  - The poller is the `form_wrapper` form inside the waiting fragment, and it targets `#tg-connect-step`. This corrects D-05's premise, which would have polled forever.
  - The poll answers 204 while waiting.
  - `POLLING_FRAGMENTS = 10` did not move: the markup gate cannot see a poller born from a macro.
  - The criterion is held by `test_polling_stops_by_a_response_without_trigger` (20 rows), closed over six template branches, with six negative controls.
- **Criterion 3 chronicle (D-04).**
  - Before the phase, `QRAuthState` stored no user.
  - The premise was false, and `FEATURES.md:241` was false too.
  - 13-04 added the owner binding (the subject under impersonation) and `_owned` before any mutation.
  - A foreign `session_id` gets a response byte-equal to the unknown case on all three handlers.
- **Criterion 5 chronicle (D-11):** the base measurement and the button quoted verbatim. The section below has the details.
- **FETCH-02 chronicle** in REQUIREMENTS.md, cross-referenced with the criterion-3 chronicle.

## Критерий 5: деградации без JS нет и сегодня

Base measurement. The phase base is `git merge-base HEAD master` = `344dc789178a02240def9259dbb72f5822a06a5f`.

```
$ f=$(mktemp) && git show "$(git merge-base HEAD master)":app/templates/accounts/connect_tg_user.html > "$f" && grep -c '<form' "$f"
0
```

(`grep -c` exits 1 when nothing matches. The printed `0` is the measurement.)

The pre-phase start button, from `git show 344dc789:app/templates/accounts/connect_tg_user.html | grep -n '<button'`, line 32:

```
<button class="btn btn--primary" type="button" id="start-btn" onclick="startQR()"><span class="btn__label">Начать подключение</span></button>
```

- The pre-phase page had no form. The start button was `type="button"` and worked only through the script, which made five `fetch(` calls and used `setInterval`. The wizard was 100 % JS-only, so the milestone cannot regress it here.
- After the phase, every POST of the wizard without JavaScript lands 302 on `/accounts/connect/tg_user` (the `respond()` degradation path, FOUND-04; 13-01…13-03 test it for each handler).
- The phase does not build a wizard that works without JavaScript. Without polling that wizard is impossible, and the phase adds no capability that did not exist before (D-11).
- The audit may not record a failure here.
- The same record, with the same command, stands as «Летопись критерия 5» in `.planning/ROADMAP.md`, Phase 13 section.

## FETCH-02 mark deferred

`requirements.ready-ids` reports FETCH-02 ready once this SUMMARY exists, because 13-06 is the last plan that declares it. **I did not call `requirements.mark-complete FETCH-02`.** Why:
- The plan's must-have says «FETCH-02 НЕ отмечен выполненным: флажок `[ ]` и ячейка `Pending` не тронуты — отметка следует за верификацией фазы».
- `tests/test_planning/test_requirement_completion_follows_verification.py::test_no_requirement_is_marked_complete_before_its_phase_verification_passed` would fail: phase 13 has no `*-VERIFICATION.md` with a `passed` verdict. Phase 12 hit this (commit `a17052f9` reverted the premature FETCH-01 mark).

The mark is made by `phase.complete` after verification passes.

## Task Commits

1. **Task 1: chronicles of criteria 1, 2, 3, 5 in ROADMAP.** `a0f0e441` (docs)
2. **Task 2: FETCH-02 chronicle in REQUIREMENTS.** `71e478fb` (docs)

TDD is not applicable. The plan is `type: execute`, and both tasks are record-only `type="auto"` with no `tdd="true"` (`is_behavior_adding=false`), so the RED/GREEN exemption for doc-only work applies knowingly.

## Verification

- Task 1: all four `grep -c '^\*\*Летопись критерия N: .*(Фаза 13, план 13-06'` checks returned 1.
  - The diff against `344dc789` has 54 lines, and `grep -c '^-  [1-5]\. '` on it returned 0.
  - `uv run pytest tests/test_planning -q`: 44 passed. The `-k prose_plan_counts` selection: 1 passed.
- Task 2:
  - The FETCH-02 chronicle grep returned 1, the `[ ]` line grep 1 and the `Pending` row grep 1.
  - `git diff --quiet 344dc789 -- .planning/research/` exited 0.
  - `uv run pytest tests/test_planning -q`: 44 passed. The `-k "requirement or flag_and_the_status"` selection: 16 passed.
- The `test_the_machine_readable_progress_is_derived_from_the_roadmap` rule did not go red at any point in tasks 1–2.

## Decisions Made

See `key-decisions`. Numbers in the chronicles come from the five SUMMARYs, or from the tree with the command named in the text. None comes from a plan's prediction:
- `NOT_YET_CONVERTED_COUNT = 10`, `MANUAL_FETCH_* = 0`, `POLLING_FRAGMENTS = 10` and `TOP_LEVEL_BINDING_EXEMPTIONS_DECLARED = 0` were read from `tests/`.
- `fetch(` in `app/templates/` = 0 was measured with `grep -rn`.
- The five `@router` lines of the wizard were read from `app/pages/accounts.py`.

## Deviations from Plan

### Acceptance-criterion discrimination (reported, not auto-fixed)

**1. The criterion-1 «НЕ ПРАВЯТСЯ» check returns 2, not 1, and it did not discriminate before the edit**
- **Found during:** Task 1 acceptance
- **Issue:** `awk '/^\*\*Летопись критерия 1: .*Фаза 13/' .planning/ROADMAP.md | grep -c 'НЕ ПРАВЯТСЯ'` also matches Phase 11's criterion-1 chronicle (ROADMAP line 467). That line mentions «четыре обработчика QR-мастера — Фаза 13» and carries its own «НЕ ПРАВЯТСЯ». On HEAD before the edit (`d746c177`) the check already returned **1**. After the edit it returns **2**.
- **Resolution:** The property is proven by the tighter check `grep '^\*\*Летопись критерия 1: .*(Фаза 13, план 13-06' .planning/ROADMAP.md | grep -c 'НЕ ПРАВЯТСЯ'`, which returns **1**. Phase 11's line is outside this plan's scope and was not touched.
- **Files modified:** none

### Scope note

- Task 2 action item 3 says «`.planning/STATE.md` этот план не правит». In this run the orchestrator dispatched the plan sequentially and made the executor the owner of STATE/ROADMAP tracking. The tracking updates after this SUMMARY follow the orchestrator's instruction, not the plan's own prose.

---

**Total deviations:** 0 auto-fixed, plus 1 non-discriminating criterion reported and proven another way. **Impact:** no scope creep. No file under `app/`, `tests/` or `.planning/research/` changed.

## Issues Encountered

None.

## Known Stubs

None. The plan is record-only.

## Threat Flags

None. T-13-17 is mitigated: the criterion-3 and FETCH-02 chronicles name the check as introduced. T-13-18 is mitigated: FETCH-02 is still `[ ]` / `Pending`.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- All 6 plans of Phase 13 are executed. Phase verification is next. The verifier should read criteria 1, 2, 3 and 5 together with their chronicles.
- **Criterion 4 (live Telethon UAT) is NOT passed. It is still pending for the human:**
  - a phone scan
  - a refresh of an expired code
  - 2FA

  The human-judgment deliverables are 13-01 D5, 13-02 D6 and 13-03 D6.
- FETCH-02 is marked by `phase.complete` after verification passes.

## Self-Check: PASSED

- FOUND: .planning/ROADMAP.md (4 chronicles), .planning/REQUIREMENTS.md (FETCH-02 chronicle), this SUMMARY
- FOUND commits: a0f0e441, 71e478fb (`git rev-list --count d746c177..HEAD` = 2 before this SUMMARY commit)

---
*Phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah*
*Completed: 2026-09-21*

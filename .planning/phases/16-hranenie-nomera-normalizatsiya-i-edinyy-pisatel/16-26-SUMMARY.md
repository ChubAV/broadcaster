---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 26
subsystem: testing
tags: [phonenumbers, phonenumberslite, normalize_manual, docstring, pytest, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "item 5 of the normalize_manual docstring with its live-recounted remainder; MANUAL_BOUNDARY_EXAMPLES, _manual_item_five, _boundary_cause_holds and the item-5 reconciliation rule (plan 16-21)"
provides:
  - "_item_five_groups(item): the three region lists of item 5 by cause (MOBILE, VOIP_ONLY, FIXED_LINE); a list that is not found is absent from the dict"
  - "_item_five_boundary_problems(item, enumeration): the old checks (three numbers, each table region named, accepted, cause confirmed) plus each list equal to the table's regions with that cause in both directions, and reverse inclusion over the remainder segment («У кодов, отличных от 7» … «Замер:»)"
  - "Controls over in-memory mutations: TW moved into the MOBILE bracket, and RS in the VOIP bracket or in the remainder sentence, each redden the rule"
  - "_manual_docstring_item(number) and test_item_seven_points_to_its_remainder_in_item_five: item 7 refers to item 5 and repeats no remainder numbers or table regions"
  - "One phrase in item 7 of the normalize_manual docstring pointing to the remainder in item 5; normalize_manual code AST-identical to 33a31ee3"
affects: [16-30-review-disposition, phase-18-manual-phone-edit-form, phonenumberslite-pin-bump-IN-02]

actuals:
  tokens: 3148
  tasks: 2
  commits: 4

plan_head_before: e6ab315252d0612b4dc59aa160e54411a34a3ad2
plan_head_after: ce5d2378724664ab335e699687c7ab9f4741acc6

tech-stack:
  added: []
  patterns:
    - "A docstring-recount rule is a pure function over the text (`_item_five_boundary_problems`); the live rule calls it on the real item and controls call it on the item mutated in memory"

key-files:
  created: []
  modified:
    - tests/test_services/test_phone.py
    - app/services/phone.py

key-decisions:
  - "The bracket patterns and the remainder anchors are module constants (ITEM_FIVE_GROUP_PATTERNS, ITEM_FIVE_REMAINDER_ANCHORS) next to the helpers, so the rule and its controls read one grammar"
  - "Reverse inclusion uses Unicode word boundaries (`(?<!\\w)[A-Z]{2}(?!\\w)`) ∩ phonenumbers.SUPPORTED_REGIONS over the remainder segment only; RU and CR (from «CR-01») stand earlier in item 5 and are outside the segment"
  - "_manual_item_five is kept (16-21 SUMMARY cites it) and now delegates to _manual_docstring_item(5), same grammar"
  - "The item-7 phrase carries no numbers (owner allowed either path in O-13); no second recount rule is needed"

patterns-established:
  - "Teeth of a prose-recount rule are proven by controls over in-memory mutations of the prose, with an anti-vacuum `mutated != item` assert"

requirements-completed: [PHONE-01]

coverage:
  - id: D1
    description: "The item-5 rule judges which bracket each remainder region stands in and compares each bracket with MANUAL_BOUNDARY_EXAMPLES both ways; a region code in the remainder sentence must be a table key (IN-13)"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_item_five_rule_reddens_a_region_filed_under_another_cause"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_item_five_rule_reddens_a_region_named_without_a_table_row[in_the_voip_bracket]"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_item_five_rule_reddens_a_region_named_without_a_table_row[in_the_remainder_sentence]"
        status: pass
      - kind: other
        ref: "task-1 verify script (plan one-liner as a scratchpad file) → OK 56 976 36"
        status: pass
    human_judgment: false
  - id: D2
    description: "Item 7 of the normalize_manual docstring points to its remainder in item 5 without repeating numbers or table regions (IN-14)"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_item_seven_points_to_its_remainder_in_item_five"
        status: pass
      - kind: other
        ref: "uv run python -c \"... _manual_docstring_item(7) ... пункт(?:е|а)? 5 ... not \\d+ из \\d+\" → OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "Normalizer behaviour unchanged: normalize_manual body without docstring, all other functions and module-level statements AST-equal to 33a31ee3; normalize_reported source byte-identical"
    requirement: "PHONE-01"
    verification:
      - kind: other
        ref: "AST comparison against `git show 33a31ee3:app/services/phone.py` saved to .pytest_cache/gsd-red/ → OK 7"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py (229 passed; the 225 earlier rules unchanged in their assertions)"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-14
status: complete
---

# Phase 16 Plan 26: Item-5 bracket check and item-7 pointer Summary

**The item-5 reconciliation rule now parses the three region brackets of the `normalize_manual` docstring and compares each one with `MANUAL_BOUNDARY_EXAMPLES` in both directions, with reverse inclusion over the remainder sentence. Item 7 points to its remainder in item 5 without repeating any number. The normalizer code is unchanged (IN-13, IN-14, owner decision O-13).**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-14T08:28:59Z
- **Completed:** 2026-10-14T08:39:13Z
- **Tasks:** 2 (both TDD, RED then GREEN)
- **Files modified:** 2

## Accomplishments

- **IN-13 closed.** Two helpers carry the work.
  - `_item_five_groups` parses the region lists after «сам `MOBILE` (», after «только `VOIP` (», and between «у » and « — `FIXED_LINE`».
  - `_item_five_boundary_problems` keeps all the old checks: «56 из 976», «36 регион», «15 из 56», each table region named and accepted, and each cause confirmed by `_boundary_cause_holds`. It adds three new checks:
    - each bracket must be found;
    - each bracket must equal the table's regions with that cause, both ways;
    - every region code standing alone in the remainder segment must be a table key.
  - The verifier's mutations are now controls, and both redden the rule: TW moved into the MOBILE bracket, and RS added inside or outside the brackets.
- **IN-14 closed.** Item 7 has one added phrase. It says that the extra-digits remainder, which the account-type rule cannot close, is named with its live measurement in item 5. A new rule pins this: item 7 must refer to item 5 and must contain no «N из M» and no table region.
- **Behaviour unchanged.** The AST of `normalize_manual` (docstring stripped), of every other function, and of every module-level statement equals `33a31ee3`.

## Task Commits

1. **Task 1 (tracer, TDD): item-5 brackets judged both ways (IN-13)**
   - RED `a501f826`, `test(16-26)`. Moves the old logic into `_item_five_boundary_problems` without changing it, and adds the two controls.
   - GREEN `d51dc5b2`, `feat(16-26)`. Adds `_item_five_groups`, the bracket comparison, reverse inclusion, and the comment and docstring updates.
2. **Task 2 (TDD): item 7 points to item 5 (IN-14)**
   - RED `ab206ce9`, `test(16-26)`. Adds `_manual_docstring_item` and the item-7 rule.
   - GREEN `ce5d2378`, `feat(16-26)`. Adds the docstring phrase in `app/services/phone.py`.

**Plan metadata:** the `docs(16-26)` SUMMARY commit that follows these.

No REFACTOR commits: nothing needed cleanup after GREEN.

## TDD Gate Compliance

- **Task 1 RED** (`a501f826`). Ran `uv run pytest tests/test_services/test_phone.py -q -p no:randomly -k "reddens_a_region" --junit-xml=.pytest_cache/gsd-red/16-26-t1-red.xml`. The output had all three conjuncts:
  - `FAILED tests/test_services/test_phone.py::test_the_item_five_rule_reddens_a_region_filed_under_another_cause` (the two parametrized rows of the table-row control also failed);
  - `3 failed, 225 deselected`;
  - the causal literal «мутация не покраснила правило пункта 5», with `проблемы []` in each failure.

  `check tdd-red-evidence` was given the JUnit record (camelCase, in the gitignored `.pytest_cache/gsd-red/`, not committed). It returned `RED_EVIDENCE_OK`, reason `target_test_failed`, 3 tests and 3 failures.

  **Semantic assessment:** each control ran past its anti-vacuum asserts (the anchor is unique and the mutation changed the text). Each then failed on the planned assertion, because the old logic returned `[]` for the mutated text. There was no collection, import or fixture fault. The whole file at RED was `3 failed, 225 passed`, so the reconciliation rule stayed green after its logic moved into the helper.
- **Task 1 GREEN** (`d51dc5b2`). 228 passed.
- **Task 2 RED** (`ab206ce9`). Ran `uv run pytest tests/test_services/test_phone.py -q -p no:randomly -k test_item_seven_points_to_its_remainder_in_item_five --junit-xml=.pytest_cache/gsd-red/16-26-t2-red.xml`. The output had:
  - `FAILED tests/test_services/test_phone.py::test_item_seven_points_to_its_remainder_in_item_five`;
  - `1 failed, 228 deselected`;
  - the literal «пункт 7 не ссылается на свой остаток в пункте 5: ['нет ссылки на пункт 5']».

  The classifier returned `RED_EVIDENCE_OK`, reason `target_test_failed`.

  **Semantic assessment:** the anti-vacuum assert passed (item 7 found). The test then failed only on the missing reference. No number or region check fired.
- **Task 2 GREEN** (`ce5d2378`). 229 passed.

## Tracer feedback gate

Task 1 is `type="tracer"`. Auto mode was off and `human_verify_mode` was `end-of-phase`, and the verify step is automated only, so row 3 applied. After the GREEN commit, verify was re-run (228 passed, `OK 56 976 36`), the tracer was verified end to end, and task 2 continued.

## Files Created/Modified

- `tests/test_services/test_phone.py`
  - Added: `ITEM_FIVE_GROUP_PATTERNS`, `ITEM_FIVE_REMAINDER_ANCHORS`, `_item_five_groups`, `_item_five_boundary_problems`, `_manual_docstring_item`, and the rules `test_the_item_five_rule_reddens_a_region_filed_under_another_cause`, `test_the_item_five_rule_reddens_a_region_named_without_a_table_row` (2 rows) and `test_item_seven_points_to_its_remainder_in_item_five`.
  - Changed: the reconciliation rule calls the helper and its docstring has one extra sentence; `_manual_item_five` delegates to `_manual_docstring_item(5)`; the comment above `MANUAL_BOUNDARY_EXAMPLES` names the helper and keeps the old wording as a chronicle «до плана 16-26 …».
  - Not changed: the table, the enumeration and `_boundary_cause_holds`.
- `app/services/phone.py`: one phrase added to item 7 of the `normalize_manual` docstring (3 lines added, 1 line changed). There is no code change: no logging, I/O, DB or validator. The module stays pure for the privacy and writer gates.

## Measurement (live, phonenumberslite 9.0.41, 2026-10-14)

The results match the plan's measurement exactly, so there is nothing to record as plan vs measured:

- The groups parsed are MOBILE {NL, FI, ID, MY, AT}, VOIP_ONLY {TW, ZW} and FIXED_LINE {DE, IL, IT}, the same sets as the table by cause.
- The remainder segment has exactly the ten table codes. The whole item has two more, `CR` and `RU`, which are outside the segment.
- The enumeration still gives 56 of 976 accepted, in 36 regions.
- Problems for the mutations:
  - TW moved: «в скобке причины MOBILE лишние против таблицы: ['TW']» and «в скобке причины VOIP_ONLY недостаёт регионов таблицы: ['TW']».
  - RS in the bracket: the extra-in-VOIP problem and the reverse-inclusion problem.

## Gates (final tree `ce5d2378`, under the shared flock)

| Gate | Result | Base |
|------|--------|------|
| `tests/test_services/test_phone.py` | 229 passed | 225 |
| Task-1 verify script | `OK 56 976 36` | — |
| AST comparison vs `33a31ee3` | `OK 7` | — |
| Item-7 acceptance one-liner | `OK` | — |
| `git diff --quiet 33a31ee3 -- app/services/phone.py` after task-1 GREEN | exit 0 | — |
| Phase quick-run set | 986 passed | 982 |
| Privacy live-tree line | app: файлов 100, вызовов 221, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0 | same |
| `tests/test_application` | 697 passed | 697 |
| Cross-cutting gates (htmx pairs/gates, templates, declared invariants) | 576 passed (2:42) | 576 |
| `compileall -q app main.py tests` | exit 0 | 0 |
| `scripts/prohibitions_census.py --check` | exit 0, registry 819 rows, bijection | same |
| `tests/test_planning` | run after this SUMMARY commit (reported in the executor's return) | 218 passed, 2 skipped |

**Substitutions (orchestrator notes 3–4):**

- The full suite (`just test`) was not run. The orchestrator's post-merge gate runs it on the merged tree.
- `graphify update .` was not run. The orchestrator runs it after merge.

## Decisions Made

- The patterns and anchors are module constants beside the helpers. The plan named only the helpers; the constants add no behaviour.
- Reverse inclusion uses Unicode `\w` boundaries ∩ `SUPPORTED_REGIONS`. This is the plan's «не буква, не цифра и не `_`», with Cyrillic letters counting as letters.
- `_manual_item_five` keeps its name and delegates to the new generic cutter.
- The item-7 phrase has no number.

## Deviations from Plan

None in substance. Both tasks were executed as written. The following were execution-mechanics substitutions:

1. **Sandbox (orchestrator note 3).** The task-1 inline `python -c` check names `_manual_extra_digit_enumeration`, and `digit` contains the refused substring. It was run as a scratchpad script with the same logic, plus one extra assert that the remainder segment holds exactly the ten table codes.
2. **AST check source.** The task-2 one-liner calls `git show` from inside Python, which the sandbox refuses. `git show 33a31ee3:app/services/phone.py` was saved with a plain command to `.pytest_cache/gsd-red/phone-33a31ee3.py` (gitignored), and the same comparison ran against that file. A non-empty assert and a byte-identity check of the `normalize_reported` source segment were added.
3. **Plan commit ledger.** The ledger (`plan_head_before` e6ab3152) was kept in the scratchpad, not in the git dir.

**Total deviations:** 0 auto-fixed. **Impact:** none.

## Issues Encountered

None. Nothing was deferred, and no `deferred-items.md` was created (orchestrator note 5).

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- IN-13 and IN-14 are closed on this branch.
- 16-30 can record IN-13 as `fixed` with `feat(16-26)` `d51dc5b2`, and IN-14 as `fixed` with `feat(16-26)` `ce5d2378`.
- Phase 18 readers of item 7 now see that the account-type rule has a remainder, and where it is measured.

## Self-Check: PASSED

- FOUND: tests/test_services/test_phone.py, app/services/phone.py
- FOUND commits on this branch: a501f826, d51dc5b2, ab206ce9, ce5d2378
- `commits: 4` measured with `git rev-list --count e6ab3152..HEAD` before the SUMMARY commit

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-14*

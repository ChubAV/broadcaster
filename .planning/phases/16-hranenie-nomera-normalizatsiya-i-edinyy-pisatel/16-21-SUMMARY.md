---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 21
subsystem: testing
tags: [phonenumbers, phonenumberslite, e164, normalize_manual, docstring, pytest, tdd]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "normalize_manual with the account-type refusal (plan 16-16, O-7 (a)); _auto_path_enumeration pattern of a live-recount rule"
provides:
  - "Item 5 of the normalize_manual docstring names the real O-7 (a) remainder outside code 7 with its live measurement: «56 из 976» inputs, 36 regions, causes by account type, «15 из 56» valid"
  - "ManualExtraDigitEnumeration, _manual_extra_digit_enumeration(), MANUAL_BOUNDARY_EXAMPLES and the rule test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement, which recount every number and example region of item 5"
  - "Test texts (module header, comment above FOREIGN_EXTRA_DIGIT_BASES, docstring of the foreign extra-digit rule) point to item 5 and the rule, with no remainder numbers"
  - "IN-11 closed: `e164 = phonenumbers.format_number(...)`"
affects: [phase-18-manual-phone-edit-form, 16-25-review-disposition, phonenumberslite-pin-bump-IN-02]

actuals:
  tokens: 5343
  tasks: 2
  commits: 4

plan_head_before: 99002b1608ed3954cbd76147be6f04d069d61071
plan_head_after: 9711cb39c85550bdf33bb855528b052e5d32f0af

tech-stack:
  added: []
  patterns:
    - "A prose boundary carries its numbers only where a test rule recounts them live from metadata; other texts refer to the rule instead of repeating the numbers"

key-files:
  created: []
  modified:
    - app/services/phone.py
    - tests/test_services/test_phone.py

key-decisions:
  - "Item 5 is cut from ast.get_docstring(normalize_manual) as the lines from «5. » to «6. », joined with spaces; region codes are matched with ASCII-letter lookarounds, so `ID`/`IT` cannot match inside other words"
  - "Example regions sit in the MANUAL_BOUNDARY_EXAMPLES table, not parsed from prose; each region's cause class (MOBILE / VOIP_ONLY / FIXED_LINE) is checked against the measured admitting types"
  - "The test calls is_valid_number; the module never does (D-05 covers the phone module only; the same argument as _auto_path_enumeration)"

patterns-established:
  - "A live-recount rule for a docstring item: the helper enumerates, the rule asserts f-strings of the measured counts in the item text and lists every mismatch in one message"

requirements-completed: [PHONE-01]

coverage:
  - id: D1
    description: "Item 5 of the normalize_manual docstring names the measured O-7 (a) remainder (56 of 976, 36 regions, causes by type, 15 of 56 valid), and a test rule recounts it live"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement"
        status: pass
    human_judgment: false
  - id: D2
    description: "Behaviour unchanged: owner outcome O-9 (a) reproduced, normalize_manual code AST-identical to cce988cb, normalize_reported byte-identical"
    requirement: "PHONE-01"
    verification:
      - kind: other
        ref: "uv run python -c \"... normalize_manual('+31 6 12345678 12') ... '+375 29 123 45 67 1' ...\" → OK ['+3161234567812', True]"
        status: pass
      - kind: other
        ref: "AST comparison of normalize_manual body[1:] and source segment of normalize_reported against cce988cb → OK"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py (225 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Test texts name the boundary by reference to item 5 and the rule, without remainder numbers; no remainder input stands in MANUAL_ACCEPTED"
    requirement: "PHONE-01"
    verification:
      - kind: other
        ref: "AST check: «56 из 976» appears in tests/test_services/test_phone.py only inside the reconciliation rule → OK"
        status: pass
      - kind: other
        ref: "Check that MANUAL_ACCEPTED ∩ (MOBILE example + tails) = ∅ → OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "IN-11 closed by a separate refactor(16-21) commit"
    verification:
      - kind: other
        ref: "git log --format=%s cce988cb..HEAD -- app/services/phone.py → refactor(16-21) and feat(16-21)"
        status: pass
    human_judgment: false

duration: 14min
completed: 2026-10-13
status: complete
---

# Phase 16 Plan 21: Measured O-7 (a) remainder in item 5 of normalize_manual Summary

**Item 5 of the `normalize_manual` docstring now names the real remainder outside code 7: «56 из 976» inputs in 36 regions, with causes by account type (MOBILE in NL/FI/ID/MY/AT, VOIP only in TW/ZW, FIXED_LINE classes in DE/IL/IT) and «15 из 56» valid per metadata. A test rule recounts every number and example region from `phonenumbers` metadata at test time. Behaviour unchanged; IN-11 closed.**

## Performance

- **Duration:** about 14 min
- **Started:** 2026-10-13T09:56:15Z
- **Completed:** 2026-10-13T10:10Z
- **Tasks:** 2 of 2
- **Files modified:** 2

## Accomplishments

- WR-11 / gap 1 of verification round 4 closed under owner decision O-9 (a). Item 5 no longer presents coverage as closure of the class. Outside code 7 the class «номер плюс лишние цифры» is closed only where no account type admits the length. Where a type admits it, a length rule cannot close it, and part of that remainder is valid even per metadata, so the validator D-05 forbids could not tell it apart either. The former DE/IL wording is kept as a chronicle «до 2026-10-13 (ревью WR-11, верификация раунда 4, 2026-10-12)». The Germany 3–4 extra digits / E.164 limit (item 8) sentence is kept.
- The live-recount rule `test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement` checks three things against `_manual_extra_digit_enumeration()`:
  - item 5 contains «{accepted} из {total}», «{regions} регион» and «{valid} из {accepted}»;
  - each region in `MANUAL_BOUNDARY_EXAMPLES` is named and is in the accepted set;
  - each region's cause class is confirmed by the measured admitting types.

  A metadata bump (IN-02) will turn the suite red instead of leaving the prose stale.
- The three test texts point to item 5 and the rule, with no remainder numbers.
- IN-11 (O-11) is closed in its own commit.

## Task Commits

1. **Task 1 (tracer, TDD): item 5 names the measured remainder; live-recount rule**
   - RED `71957ec1` (test): helper, NamedTuple, table, rule; failed on the planned assertion
   - GREEN `dd164d6e` (feat): new item 5 text
2. **Task 2: test texts + IN-11**
   - `93632304` (test): module header, `FOREIGN_EXTRA_DIGIT_BASES` comment, foreign-rule docstring
   - `9711cb39` (refactor): `e164 = …` whitespace (IN-11)

**Plan metadata:** the docs(16-21) SUMMARY commit that follows these.

## TDD Gate Compliance

- **RED** `71957ec1`. Ran `uv run pytest tests/test_services/test_phone.py -q -p no:randomly -k test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement --junit-xml=.pytest_cache/gsd-red/16-21-red.xml`. Output had all three required conjuncts:
  - `FAILED tests/test_services/test_phone.py::test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement`
  - `1 failed, 224 deselected`
  - the causal literal «пункт 5 не называет замер остатка», listing 13 mismatches: `нет «56 из 976»`, `нет «36 регион»`, `нет «15 из 56»`, and each of the ten regions «не назван».

  `gsd-tools check tdd-red-evidence` was fed the JUnit XML record (camelCase, in the gitignored `.pytest_cache/gsd-red/`, not committed) and returned `RED_EVIDENCE_OK`, reason `target_test_failed`.

  **Semantic assessment:** the target ran. Its anti-vacuum asserts passed first (item 5 found, total 976 ≥ 900, accepted 56 > 0), and it then failed on the planned assertion. There was no collection, import or fixture fault.
- **GREEN** `dd164d6e`. The target and the full file passed: 225 passed, up from 224.
- **REFACTOR** `9711cb39` is IN-11 whitespace only. The AST of `normalize_manual` is identical to `cce988cb`, and 225 passed.

## Files Created/Modified

- `app/services/phone.py`: changes only the item 5 text in the `normalize_manual` docstring and the IN-11 space. Code is AST-identical to `cce988cb`, and `normalize_reported` is byte-identical. The module stays pure (no logging, I/O or validator).
- `tests/test_services/test_phone.py`:
  - added: `MANUAL_EXTRA_DIGIT_TAILS`, `ManualExtraDigitEnumeration`, `_manual_extra_digit_enumeration()`, `MANUAL_BOUNDARY_EXAMPLES`, the helpers `_manual_item_five()` and `_boundary_cause_holds()`, the new rule, and `import re`;
  - rewritten: the header paragraph, the `FOREIGN_EXTRA_DIGIT_BASES` comment and the foreign-rule docstring paragraph.

## Measurement (live, phonenumberslite 9.0.41, 2026-10-13)

The measured numbers match the plan exactly, so there is no discrepancy to record:
- 976 inputs, 56 accepted, 36 regions, 15 valid;
- the accepted region set is the one named in the plan and Ф-6;
- the cause classes of all ten table regions are confirmed (NL `+12` {MOBILE, FIXED_LINE_OR_MOBILE}; TW `+1`/`+12` {VOIP}; ZW `+1` {VOIP}; DE/IL/IT only FIXED_LINE + FIXED_LINE_OR_MOBILE; AT all four types).

The enumeration was run as a scratchpad script (not committed) before RED, and again by the rule itself.

## Gates (final tree, under the shared flock)

| Gate | Result | Base |
|------|--------|------|
| Task 1 selection (`-k` 5 rule groups) | 30 passed | — |
| Owner outcome O-9 (a) one-liner | `OK ['+3161234567812', True]` | — |
| AST check vs `cce988cb` (+ IN-11 assert) | OK | — |
| Remainder not in `MANUAL_ACCEPTED` | OK (12 rows vs 948 distinct remainder candidates) | — |
| `tests/test_services/test_phone.py` | 225 passed | 224 |
| Phase quick-run set | 857 passed | 856 |
| `tests/test_application` | 601 passed | 601 |
| Cross-cutting gates (htmx pairs/gates, templates, declared invariants) | 576 passed (2:40) | 576 |
| `compileall -q app main.py tests` | exit 0 | 0 |
| `scripts/prohibitions_census.py --check` | exit 0, registry 802 rows, bijection | same |
| `tests/test_planning` | run after this SUMMARY commit (reported in the executor's return) | 218 passed, 2 skipped |

**Substitutions (orchestrator notes 3–4):**
- The full suite (`just test`) was not run. The orchestrator's post-merge gate runs it on the merged tree.
- `graphify update .` was not run. The orchestrator runs it after merge.

## Decisions Made

- **How the rule finds item 5:** the docstring lines from «5. » to «6. », joined with spaces. Region codes are matched with ASCII lookarounds.
- **Example regions as a table:** they come from a table, not from parsing prose. Their causes are confirmed by measured types.
- **Validator calls:** only the test calls `is_valid_number`. The module never does.

## Deviations from Plan

None in substance. The plan was executed as written. The following were execution-mechanics substitutions, not changes to behaviour or scope:

1. **Sandbox selector rephrasing (orchestrator note 3).** The worktree sandbox refuses command text containing the substring `git`, and `digit` contains it. Changes made:
   - Task 1's `-k` selector `manual_path_names_its_extra_digit_boundary or … or non_geographic` was run as `manual_path_names_its_extra or … or non_geo`. It is the same 30 tests.
   - The grep criteria for the `…_extra_digit_…` names used `di.it` in the pattern.
   - The inline python checks whose text named the rule were run as scratchpad scripts with the same logic.
2. **AST check source.** The plan's one-liner calls `subprocess.run(['git', 'show', 'cce988cb:…'])` inline, which the sandbox refuses. Instead, `git show cce988cb:app/services/phone.py` was written to a scratchpad file with a plain command (429 lines, non-empty assert). The same AST and segment comparison then ran against that file.
3. **Plan commit ledger.** The sandbox also refused a write into the worktree's git dir, so the ledger (`plan_head_before` 99002b16) was kept in the scratchpad.
4. **Extra self-check (stricter than the plan).** Besides «56 из 976», the check also asserted that «15 из 56», «36 регион» and «976» appear nowhere in the test file outside the rule. It passed.

**Total deviations:** 0 auto-fixed. **Impact:** none.

## Issues Encountered

None. Nothing was deferred, and no `deferred-items.md` was created (orchestrator note 5).

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Gap 1 (WR-11) and advisory IN-11 are closed on this branch.
- 16-25 can record WR-11 and IN-11 as `fixed` with `feat(16-21)` `dd164d6e` and `refactor(16-21)` `9711cb39`.
- Phase 18 planners reading item 5 now see the real remainder: NL/FI/IT-style numbers with extra digits are stored as manual, not refused.

## Self-Check: PASSED

- FOUND: app/services/phone.py, tests/test_services/test_phone.py
- FOUND commits on this branch (`git log 99002b16..HEAD`): 71957ec1, dd164d6e, 93632304, 9711cb39
- `commits: 4` measured with `git rev-list --count 99002b16..HEAD` before the SUMMARY commit

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-13*

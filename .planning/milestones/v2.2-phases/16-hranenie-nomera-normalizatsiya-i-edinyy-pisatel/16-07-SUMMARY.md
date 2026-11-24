---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 07
subsystem: services
tags: [phonenumberslite, phonenumbers, e164, normalization, privacy, mask, tdd, gap-closure]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-02 app/services/phone.py (normalize_manual, normalize_reported, mask_phone) and its table spec"
provides:
  - "app/services/phone.py: constant RU_KZ_COUNTRY_CODE = 7; normalize_manual refuses country code 7 with a leading-zero national part (CR-01, owner O-3 (a))"
  - "app/services/phone.py: REPORTED_MIN_DIGITS = 7 (was 5, chronicled); normalize_reported returns None on IS_POSSIBLE_LOCAL_ONLY (WR-04)"
  - "app/services/phone.py: mask_phone hides every national digit when the national part has <= 2 digits (WR-03)"
  - "tests/test_services/test_phone.py: three new rules, 7 cr01_* rows, Italy control, 5 refused + 2 accepted auto-path rows, 2 mask rows, rewritten mask leak rule (133 tests)"
affects: [16-08 writer, phase 18 manual form, phase 19 wizard, phase 20 backfill script, 16-VERIFICATION re-verify]

actuals:
  tokens: 4902      # chars/4 over the realized diff (19607 chars); whole changed files are 36625 chars (~9156)
  tasks: 3
  commits: 6        # git rev-list --count plan_head_before..plan_head_after (code commits; the SUMMARY commit follows)
plan_head_before: 2b9f64bd410a815000fc2cbac595bbbb5f53721b
plan_head_after: fdb12dd56408640022f66476f286939dad5eef63

tech-stack:
  added: []
  patterns:
    - "Refuse on a parse attribute (country_code == 7 and italian_leading_zero), never on the validity validator (D-05)"
    - "Auto path asks the possibility reason only to refuse IS_POSSIBLE_LOCAL_ONLY; TOO_SHORT stays accepted for Fragment"
    - "Changed bounds keep a chronicle of the old value beside the new one (D-30/D-32 idiom)"

key-files:
  created: []
  modified:
    - app/services/phone.py
    - tests/test_services/test_phone.py

key-decisions:
  - "Outcome (a) of human_verification 1 is implemented: normalize_manual('00 44 7911 123456') raises PhoneError('Не похоже на номер телефона. Пример: +7 999 123-45-67'). Variant (b), reading 00 as +, was rejected by the owner and is not implemented in any form."
  - "The refusal is limited to country code 7. italian_leading_zero is legitimately True for Italy (+39 06 ...), and the row italian_leading_zero_is_not_plus_seven pins that."
  - "Auto-path floor 7 plus an IS_POSSIBLE_LOCAL_ONLY refusal (planning flag P-1). A 7-digit TOO_SHORT fragment ('1234567' -> '+1234567') still passes. The module header states this boundary, and no table row asserts it as correct."
  - "The mask threshold uses the literal 2 already present in mask_phone. No undeclared module constant was added, because the plan's artifact list for 16-07 names only RU_KZ_COUNTRY_CODE."

patterns-established:
  - "A table row that pinned a defect as correct is moved to the opposite table under a new id. A comment names the old id and value instead of deleting the row silently."

requirements-completed: [PHONE-01, PHONE-21]

coverage:
  - id: D1
    description: "Manual input parsed into country code 7 with a leading-zero national part (00 prefix, foreign local numbers) is refused with PHONE_ERROR_NOT_A_NUMBER instead of saved as +7 0... (CR-01, O-3 (a))"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_with_the_00_prefix_is_refused_not_saved_as_plus_seven_zero"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_by_hand_is_refused_with_an_explanation (7 cr01_* rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_every_refusal_text_is_a_declared_constant_with_the_example (7 cr01_* rows)"
        status: pass
      - kind: other
        ref: "uv run python -c \"from app.services.phone import normalize_manual; print(normalize_manual('00 44 7911 123456'))\" -> exit 1, empty stdout, last stderr line 'app.services.phone.PhoneError: Не похоже на номер телефона. Пример: +7 999 123-45-67'"
        status: pass
    human_judgment: false
  - id: D2
    description: "The refusal takes nothing away from accepted spellings: Italy +39 06 1234 5678 -> +390612345678, every prior MANUAL_ACCEPTED row and both O-1 rows unchanged; the closed set of four refusal texts and the purity rule hold"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_by_hand_is_normalized_to_e164 (18 rows incl. italian_leading_zero_is_not_plus_seven)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_refusal_texts_are_exactly_four_distinct_russian_constants"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_module_is_pure_and_never_asks_validity"
        status: pass
    human_judgment: false
  - id: D3
    description: "Auto path no longer stores a digit fragment: floor 7 digits, IS_POSSIBLE_LOCAL_ONLY refused; Niue/Tokelau 7-digit numbers and Fragment +888 still accepted (WR-04)"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_short_fragment_from_a_source_is_not_stored_as_a_number"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_garbage_from_a_source_leaves_the_number_unknown (15 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_reported_number_is_normalized_to_e164 (10 rows)"
        status: pass
      - kind: integration
        ref: "tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py (18 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Mask of a parseable number with <= 2 national digits shows none of them ('+88812' -> '+888 ***', '+712' -> '+7 ***'); D-10 forms unchanged; the leak rule now judges short numbers (WR-03)"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_short_national_part_is_masked_entirely"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_stored_number_is_masked_for_a_human (9 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_mask_shows_only_the_country_code_and_two_last_digits (7 rows incl. short_national_part_*)"
        status: pass
    human_judgment: false

duration: 14min
completed: 2026-10-09
status: complete
---

# Phase 16 Plan 07: Normalizer refuses invented +7 0 numbers, auto-path fragments and short-number mask leaks Summary

**`normalize_manual` refuses country code 7 with a leading-zero national part (`00 44 …` gets `PHONE_ERROR_NOT_A_NUMBER`, not `+700447911123456`). The auto path now needs 7 digits and refuses `IS_POSSIBLE_LOCAL_ONLY`. `mask_phone('+88812')` now gives `+888 ***`. This closes CR-01, WR-04 and WR-03 with three RED/GREEN cycles.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-10-09T14:22:57Z
- **Completed:** 2026-10-09T14:37:04Z
- **Tasks:** 3 (task 1 is the tracer)
- **Files modified:** 2

## Accomplishments

- **CR-01 closed with outcome (a).** Manual input that parses into `+7` with a national part starting with `0` is refused with the existing `PHONE_ERROR_NOT_A_NUMBER` text. Seven inputs are pinned by name: four `00 …` prefixes, a Ukrainian local number, a Belarus `8 0…` and `+7 0…`. The Italian `+39 06 1234 5678` still gives `+390612345678`.
- **WR-04 closed.** `REPORTED_MIN_DIGITS` went from 5 to 7, with a chronicle of the old value. `normalize_reported` returns `None` for `IS_POSSIBLE_LOCAL_ONLY`. `12345`, `123456`, `88812`, `4412345` and `71234567` now give `None`. Niue `6831234`, Tokelau `6901234`, Fragment `88801234567` / `888012345678` and Russian numbers are still accepted. The row `five_digits_lower_bound` moved to `REPORTED_REFUSED` as `five_digits_fragment_was_the_lower_bound`, and a chronicle comment names it.
- **WR-03 closed.** A parseable number with a national part of two digits or fewer is masked as `+<code> ***`. The D-10 forms are unchanged. The leak rule now counts national digits from `format_phone` and expects zero visible national digits for short numbers. Before, it only checked numbers with 8+ national digits.
- The module header now states the remaining auto-path boundary (P-1): a 7-digit `TOO_SHORT` fragment such as `1234567` is not told apart from Fragment.

## Task Commits

1. **Task 1 (tracer): manual `00…` / leading-zero refusal**: RED `673053e2` (test), GREEN `97e62918` (feat)
2. **Task 2: auto-path floor 7 and local-only refusal**: RED `a8486cb2` (test), GREEN `ae44c1d0` (feat)
3. **Task 3: short national part fully masked**: RED `128ed8f9` (test), GREEN `fdb12dd5` (feat)

No REFACTOR commit, because no cleanup was warranted.

## TDD Gate Compliance

Every cycle has a `test(16-07)` commit before its `feat(16-07)` commit. `git log -E --grep="^(test|feat|refactor)\(0*16-0*7\):"` lists all six in order. Each RED run used the single target test with `--junit-xml` written to the worktree's gitignored `.pytest_cache/gsd-red/`. The runs had measured start times. The records were not committed. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`, tests 1, fail 1) for all three.

- **RED 1**: `uv run pytest tests/test_services/test_phone.py::test_a_number_typed_with_the_00_prefix_is_refused_not_saved_as_plus_seven_zero -q -p no:randomly --junit-xml=.pytest_cache/gsd-red/red1.xml`, exit 1. Output contains `FAILED tests/test_services/test_phone.py::test_a_number_typed_with_the_00_prefix_is_refused_not_saved_as_plus_seven_zero`, `1 failed, 1 warning in 0.18s` and `Failed: DID NOT RAISE <class 'app.services.phone.PhoneError'>`. *Semantic assessment:* the target ran and failed on its planned `pytest.raises(PhoneError)`, because `normalize_manual` had no code-7 leading-zero check. There was no collection, import or fixture fault. The whole file at RED gave `15 failed, 106 passed`: the tracer plus 7 `cr01_*` rows in each of two rules. All were behavioural, with no ERROR rows. The Italy row already passed, as a positive control should.
- **RED 2**: target `test_a_short_fragment_from_a_source_is_not_stored_as_a_number`, exit 1. Output contains `FAILED tests/test_services/test_phone.py::test_a_short_fragment_from_a_source_is_not_stored_as_a_number`, `1 failed, 1 warning in 0.18s` and `assert '+12345' is None`. *Semantic assessment:* the planned assertion failed because the floor was still 5. The whole file gave `6 failed, 122 passed`: the target plus the 5 new refused rows. The Niue and Tokelau rows already passed.
- **RED 3**: target `test_a_short_national_part_is_masked_entirely`, exit 1. Output contains `FAILED tests/test_services/test_phone.py::test_a_short_national_part_is_masked_entirely`, `1 failed, 1 warning in 0.21s` and `assert '+888 12' == '+888 ***'`. *Semantic assessment:* the planned equality failed because the parseable branch had no floor. The whole file gave `5 failed, 128 passed`: the target, 2 `MASKED` rows and 2 leak-rule rows. So the rewritten leak rule does see the short case, and all old rows pass under it.

## Files Created/Modified

- `app/services/phone.py`: `RU_KZ_COUNTRY_CODE` and the code-7 leading-zero refusal, with the `normalize_manual` checklist renumbered to 7 items and the O-3 chronicle. `REPORTED_MIN_DIGITS = 7` with its chronicle. `IS_POSSIBLE_LOCAL_ONLY` refusal in `normalize_reported`, with an updated docstring. In the header: `7…15`, the old `5…15` named, and the P-1 boundary. Short-national-part threshold in `mask_phone`, with the WR-03 chronicle.
- `tests/test_services/test_phone.py`: three new target rules. Table rows: 7 `cr01_*`, `italian_leading_zero_is_not_plus_seven`, 5 new `REPORTED_REFUSED`, 2 new `REPORTED_ACCEPTED`, 2 new `MASKED`. Also the chronicle comment over `REPORTED_ACCEPTED`, the rewritten `test_a_mask_shows_only_the_country_code_and_two_last_digits`, and updated header and docstrings.

## Decisions Made

See `key-decisions` in the frontmatter. In short: outcome (a) only, the refusal is limited to code 7, floor 7 plus the local-only refusal (P-1), and no undeclared constant was added for the mask.

## Deviations from Plan

### Acceptance-criterion counts that the plan miscounted (intent met, code not bent to the number)

**1. `grep -c "o1_fragment_by_hand_refused"` and `grep -c "o1_fragment_without_plus_becomes_russian"` return 2, the plan expects 1**
- **Found during:** Task 1 acceptance check
- **Issue:** At base `2b9f64bd` each id already occurs twice: the `pytest.param` row and a docstring mention (base lines 189/198 and 215/239).
- **Disposition:** The criterion's intent is that the O-1 rows are untouched. That holds: `id="o1_…"` occurs once each, and both rows match the base byte for byte. Nothing was changed to hit the number.

**2. `grep -c "five_digits_fragment_was_the_lower_bound"` returns 2, the plan expects 1**
- **Found during:** Task 2 acceptance check
- **Issue:** The plan's own `<behavior>` item 4 prescribes a chronicle comment that names the new id ("…под именем `five_digits_fragment_was_the_lower_bound`…"). The comment plus the row make 2.
- **Disposition:** The prescribed comment text was followed. The row itself occurs once.

**3. The `-q … -v` listing check printed no names**
- **Found during:** Task 3 acceptance check
- **Issue:** `-q` and `-v` cancel out, which leaves default verbosity (dots only).
- **Disposition:** Re-ran with `-p no:randomly -v` alone. Both `test_a_mask_shows_only_the_country_code_and_two_last_digits[short_national_part_two_digits]` and `[...short_national_part_russia]` are listed as PASSED, and so are the matching `test_a_stored_number_is_masked_for_a_human` rows.

**Total deviations:** 0 auto-fixes to code. 3 acceptance-criterion literal mismatches recorded; each one's intent is verified as shown above.
**Impact on plan:** None. No scope creep.

## Substitutions (named, per orchestrator notes)

- **Full suite not run.** `just test` (about 4300 tests, about 45 min) is left to the orchestrator's post-merge gate on the merged tree, per host limits.
- **`graphify update .` not run.** The worktree has no `graphify-out/`, and the orchestrator updates the graph after merge.
- No STATE.md, ROADMAP.md or REQUIREMENTS.md writes, no `state.*`, `roadmap.*` or `requirements.*` verbs, and no registry edits. The orchestrator owns those.

## Gates run on the final tree (`fdb12dd5`, under the shared pytest lock)

| Gate | Result |
|------|--------|
| `tests/test_services/test_phone.py -q -p no:randomly` | 133 passed |
| `tests/test_services/test_phone.py -q -p no:randomly -k "refused_not_saved or cr01 or italian_leading_zero or o1_fragment"` | 19 passed (≥ 19 required) |
| Task 2 `<automated>` normalize_reported one-liner | `OK` |
| Task 3 `<automated>` mask_phone one-liner | `OK` |
| `tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py` | 18 passed |
| `tests/test_services/test_phone.py tests/test_application tests/test_phone_privacy_gate.py -q -p no:randomly` | 503 passed (133 + 306 + 64; base 105 + 306 + 64) |
| Cross-cutting: `tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_templates tests/test_application/test_declared_invariants.py` | 576 passed (equals base) |
| `tests/test_models/test_messenger_account_phone_check.py tests/test_migrations` | 147 passed |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 (764 rows, bijection with the census agrees) |
| `tests/test_planning -q` | run after the SUMMARY commit; result reported in the executor's return |

Wave-mate notes 16-08 and 16-09 were respected. The module still writes no logs and no structlog bindings, and passes no dict or kwargs carrying `phone` / `phone_is_manual` into any write call. `app/services/phone.py` imports only `phonenumbers`, and the purity rule is green.

## Issues Encountered

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- The verification gap `gaps[0]` items 1–4 are addressed in code and tests. A re-verification should reproduce `human_verification` 1 and get outcome (a).
- The P-1 boundary remains, by design and stated in the module header: a 7-digit auto-path fragment with verdict `TOO_SHORT` (`1234567`, `7999123`) is still stored. Closing it would need a special case for code 888, which the owner rejected under O-1.

## Self-Check: PASSED

- FOUND: app/services/phone.py, tests/test_services/test_phone.py
- FOUND commits on this branch: 673053e2, 97e62918, a8486cb2, ae44c1d0, 128ed8f9, fdb12dd5

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-09*

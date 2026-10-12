---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 16
subsystem: phone-normalization
tags: [phonenumberslite, e164, normalizer, tdd, gap-closure, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "app/services/phone.py from 16-02/16-07/16-11 (normalize_manual with the code-7 predicate _is_impossible_zone_seven, normalize_reported with REPORTED_REFUSED_VERDICTS, the module header boundary paragraph)"
provides:
  - "ACCOUNT_NUMBER_TYPES = (MOBILE, FIXED_LINE, FIXED_LINE_OR_MOBILE, VOIP) and the length-only predicate _is_possible_for_an_account_type (is_possible_number_for_type_with_reason == IS_POSSIBLE, no validity check, D-05)"
  - "normalize_manual item 7: a manual number whose length is impossible for every account type is refused with PHONE_ERROR_NOT_A_NUMBER; owner outcome O-7 (a) reproduced letter for letter (WR-09)"
  - "The module header boundary paragraph names both auto-path accepted classes with live-checked measurements: possible values INCLUDING INVALID ones (400 of 558) and TOO_SHORT outside code 7 (583 of 1935) (IN-08, O-8)"
  - "Guards: 830 metadata example numbers of the four account types accepted by hand; the non-geographic split pinned; the bare per-type possibility check forbidden in the module"
affects: [phase-17-display, phase-18-manual-edit-form, phase-19-wizard, phase-20-backfill-script]

actuals:
  tokens: 8353
  tasks: 3
  commits: 6
plan_head_before: e9141128e929fca8d4ed3ab7cbe75d743d3c068d
plan_head_after: 8b30aaedc69d5eac4a8e23b08a6ceb93afe78872

tech-stack:
  added: []
  patterns:
    - "Manual-path refusal by account-shaped number types: a per-type length check (…_with_reason == IS_POSSIBLE) over a named type set, never the validity check and never the bare per-type check"
    - "A prose measurement in a module docstring is pinned by a test that recomputes it live, so a metadata bump reddens the suite instead of leaving the header stale"

key-files:
  created: []
  modified:
    - app/services/phone.py
    - tests/test_services/test_phone.py

key-decisions:
  - "The account-type rule is item 7 of normalize_manual, right after strict possibility (item 6); the E.164 limit becomes item 8. Items 1-6 keep their numbers, so the 16-07 and 16-11 chronicle references to item 5 stay correct"
  - "TOLL_FREE is deliberately excluded from ACCOUNT_NUMBER_TYPES (a toll-free number is never an account; with it the set would again admit every WR-09 input); PREMIUM_RATE, SHARED_COST, UAN, PAGER, PERSONAL_NUMBER are excluded too"
  - "The remaining boundary is named in item 5 of the normalize_manual docstring with the execution measurement, not pinned by a table row: Germany +49 151 23456789 with 1 and 2 extra digits and Israel +972 50 123 4567 with 2 and 3 stay accepted (variable FIXED_LINE length). Germany +3/+4 pass item 7 but are refused by the E.164 limit (item 8)"
  - "The header boundary paragraph is checked by a test against a live enumeration helper (_auto_path_enumeration), not just reworded"

patterns-established:
  - "Foreign-zone class enumeration with its own anti-vacuum (the base is accepted and possible as MOBILE), kept separate from the code-7 enumeration whose anti-vacuum asserts a +7 base"

requirements-completed: [PHONE-01]

coverage:
  - id: D1
    description: "A foreign mobile number with extra digits typed by hand (BY, UA, KG, TR, CN with 1..5 extra digits; IL with one) is refused with PHONE_ERROR_NOT_A_NUMBER; owner outcome O-7 (a): '+375 29 123 45 67 1' and '+380 50 123 4567 1' refused, '+375 29 123 45 67' -> '+375291234567', '8-800-555-35-35' -> '+78005553535'"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_foreign_number_with_an_extra_digit_typed_by_hand_is_refused"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_foreign_number_with_extra_digits_typed_by_hand_is_refused_whatever_their_count (25 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_by_hand_is_refused_with_an_explanation[wr09_*] (8 rows) and test_every_refusal_text_is_a_declared_constant_with_the_example[wr09_*] (8 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_by_hand_is_normalized_to_e164[*_mobile] (6 rows)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The account-type refusal loses no metadata example number: 830 examples of MOBILE, FIXED_LINE, FIXED_LINE_OR_MOBILE, VOIP across SUPPORTED_REGIONS are accepted by hand with the same E.164; non-geographic examples split as decided (+800, +808, +888, +979 refused; +870, +878, +881, +882, +883 accepted)"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_every_account_type_example_number_of_the_metadata_is_accepted_by_hand"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_non_geographic_examples_split_by_account_type"
        status: pass
    human_judgment: false
  - id: D3
    description: "The module stays pure: the validity check, the bare possibility check and the bare per-type possibility check are forbidden; the account-type rule must use the …_with_reason form"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_module_is_pure_and_never_asks_validity"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_ast_rule_catches_a_validity_call_and_a_database_import"
        status: pass
    human_judgment: false
  - id: D4
    description: "The module header names the real auto-path accepted set (possible values including invalid ones, 400 of 558; TOO_SHORT outside code 7, 583 of 1935), checked live against the enumeration; normalize_reported unchanged byte for byte"
    requirement: "PHONE-01"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_module_header_names_the_auto_path_boundary_with_its_measurement"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_auto_path_never_stores_a_verdict_the_owner_refused"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_auto_path_refuses_what_the_owner_named_before_execution"
        status: pass
    human_judgment: false
  - id: D5
    description: "The remaining manual-path boundary (Germany +1/+2, Israel +2/+3 extra digits stay accepted) is named in item 5 of the normalize_manual docstring and pinned by no table row"
    requirement: "PHONE-01"
    verification:
      - kind: other
        ref: "uv run python -c (plan acceptance: no MANUAL_ACCEPTED row starts with +4915123456789 / +972501234567 and is longer than 14 chars) -> OK"
        status: pass
    human_judgment: true
    rationale: "Whether the boundary prose is accurate and sufficient for the planners of phases 18-20 is a reader's judgment; no test asserts the wording of item 5"

duration: 19min
completed: 2026-10-12
status: complete
---

# Phase 16 Plan 16: Account-type refusal for foreign manual numbers and an honest auto-path header Summary

**A manual number is accepted only if its length is possible for an account-shaped type (MOBILE, FIXED_LINE, FIXED_LINE_OR_MOBILE, VOIP). That closes WR-09: foreign numbers with unmarked extra digits are now refused. The module header now states that the auto path also stores possible but invalid values (400 of 558); a test recomputes that number live.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-10-12T18:21:04Z
- **Completed:** 2026-10-12T18:40Z
- **Tasks:** 3 (Task 1 tracer, TDD; Task 2 guard; Task 3 TDD)
- **Files modified:** 2

## Accomplishments

- Owner outcome O-7 (a), named before execution, is reproduced exactly. `normalize_manual('+375 29 123 45 67 1')` and `('+380 50 123 4567 1')` raise `PhoneError(PHONE_ERROR_NOT_A_NUMBER)`. `('+375 29 123 45 67')` returns `'+375291234567'` and `('8-800-555-35-35')` returns `'+78005553535'`.
- The class is closed, not just the two inputs. Belarus, Ukraine, Kyrgyzstan, Turkey and China mobiles with 1…5 extra digits are refused whatever the count (25-row enumeration). Israel with one extra digit is refused too.
- No real number is lost:
  - every old `MANUAL_ACCEPTED` row still passes;
  - all 830 metadata example numbers of the four account types are accepted by hand with the same E.164.
- The non-geographic side effect is pinned as a decision:
  - refused: `+800`, `+808`, `+888` (OCHA sample), `+979`;
  - accepted: `+870`, `+878`, `+881`, `+882`, `+883`.
- IN-08 is closed. The header boundary paragraph names two classes: possible values *including invalid ones* (400 of 558) and `TOO_SHORT` outside code 7 (583 of 1935). A test checks both numbers against a live enumeration. `normalize_reported` is unchanged byte for byte against `7a4ee433`.

## Task Commits

1. **Task 1 (tracer): foreign numbers with extra digits refused**
   - RED `073e7f65` (test)
   - GREEN `333bf8e0` (feat)
2. **Task 2: sentinel, non-geographic split, purity rule** — `b23f14e6` (test; no RED by construction, the behaviour comes from Task 1)
3. **Task 3: header names the real auto-path set (IN-08)**
   - RED `bb3d8239` (test)
   - GREEN `5c3ffb94` (feat)
   - REFACTOR `8b30aaed` (refactor: wraps one long assertion message, no behaviour change)

**Plan metadata:** the `docs(16-16)` commit that carries this SUMMARY.

## TDD Gate Compliance

- **Task 1.** RED `073e7f65` came before GREEN `333bf8e0`.
  - Command: `uv run pytest tests/test_services/test_phone.py -q -p no:randomly -k test_a_foreign_number_with_an_extra_digit_typed_by_hand_is_refused --junit-xml=.pytest_cache/gsd-red/16-16-t1.xml`, exit 1.
  - The three conjuncts were present:
    - `FAILED tests/test_services/test_phone.py::test_a_foreign_number_with_an_extra_digit_typed_by_hand_is_refused`
    - `1 failed, 220 deselected`
    - `Failed: DID NOT RAISE <class 'app.services.phone.PhoneError'>`
  - `gsd-tools check tdd-red-evidence`: `RED_EVIDENCE_OK` (`format: junit`, `target_test_failed`).
  - Semantic assessment: the named target ran and failed on its planned assertion; a foreign number with one extra digit was still saved. There was no collection, import or fixture fault.
  - Whole-file footprint before GREEN: `24 failed, 197 passed`. That is the tracer, 7 enumeration rows and 8 `wr09_*` rows × 2 rules. The six `*_mobile` controls already passed.
- **Task 3.** RED `bb3d8239` came before GREEN `5c3ffb94`.
  - Command: `… -k test_the_module_header_names_the_auto_path_boundary_with_its_measurement --junit-xml=.pytest_cache/gsd-red/16-16-t3.xml`, exit 1.
  - The three conjuncts were present:
    - `FAILED tests/test_services/test_phone.py::test_the_module_header_names_the_auto_path_boundary_with_its_measurement`
    - `1 failed, 223 deselected`
    - `AssertionError: шапка не называет замер «400 из 558» …`
  - `RED_EVIDENCE_OK` (`format: junit`).
  - Semantic assessment: the `583 из 1935` assertion passed and the failure came from the planned `400 из 558` assertion. Whole file: `1 failed, 223 passed`, so the refactored enumeration rule stayed green.
- **Task 2** is a guard with no RED by construction, as the plan specifies. Its commit is `test(16-16)`.
- The evidence files are kept in the gitignored `.pytest_cache/gsd-red/` and are not committed.

## Files Created/Modified

- `app/services/phone.py`
  - `PhoneNumberType` import; `ACCOUNT_NUMBER_TYPES`; `_is_possible_for_an_account_type`.
  - Item 7 of `normalize_manual`: the check, plus its chronicle (WR-09, O-7 (a), option (b) rejected by the owner).
  - The non-geographic side effect is named, and the DE / IL boundary is named in item 5. The E.164 limit is renumbered to item 8.
  - The header boundary paragraph is rewritten (two classes, 400 of 558, 583 of 1935) and a third chronicle paragraph is added (IN-08, O-8).
- `tests/test_services/test_phone.py`
  - New tests: the tracer; 8 `wr09_*` rows; 6 `*_mobile` controls; `FOREIGN_EXTRA_DIGIT_BASES` with its enumeration rule; the 830-example sentinel; the non-geographic split rule.
  - Purity rule: `FORBIDDEN_CALLS` now includes `is_possible_number_for_type`, with a `…_with_reason` anti-vacuum and an extended planted control.
  - Header check: the `AutoPathEnumeration` / `_auto_path_enumeration()` helper, which the old enumeration rule now uses with unchanged assertions, and the header-measurement rule.
  - Spec header bullets updated.

## Decisions Made

See `key-decisions` in the frontmatter. In short:
- The rule is item 7, so the earlier item references stay valid.
- `TOLL_FREE` is excluded for the same reason as `RU_KZ_NATIONAL_DIGITS`.
- The DE / IL boundary is named in item 5 and not pinned by any table row.
- The IN-08 header is pinned by a live-computing test.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Accuracy] The Germany boundary is "+1 and +2 extra digits", not "+1…+4"**
- **Found during:** Task 1 (pre-implementation measurement).
- **Issue:** The plan's truth 5 and the Task 1 action say Germany `+49 151 23456789` with 1…4 extra digits stays accepted. Measured with `normalize_manual` on 9.0.41:
  - the type rule alone admits +1…+4;
  - +3 and +4 are already refused today, by the E.164 limit (`PHONE_ERROR_TOO_LONG`).

  The 16-REVIEW.md WR-09 table agrees: DE +3 and +4 are refused. Writing "1…4 stay accepted" into the docstring would have stated something false.
- **Fix:** Item 5 now says Germany with one and two extra digits stays accepted. It adds that item 7 would also pass +3/+4 and that the E.164 limit (item 8) refuses them. The test-module header bullet says the same. Israel +2/+3 matched the plan.
- **Files modified:** `app/services/phone.py`, `tests/test_services/test_phone.py`
- **Verification:** Probe output for `+49 151 23456789 1`, `… 12`, `… 123` and `… 1234`: the first two give `+49151234567891` and `+491512345678912`; the last two give `ERR: Слишком длинный ввод`. The plan acceptance grep `+49 151 23456789` returns 1.
- **Committed in:** `333bf8e0`

**2. [Rule 1 - Accuracy] Pre-plan count of saved foreign rows is 7 of 25, not 8**
- **Found during:** Task 1 (RED run).
- **Issue:** The plan says 8 of 25 enumeration rows were saved before the plan. The measured count is 7: BY +1, +2; UA +1; KG +1; TR +2, +3; CN +1. The RED run confirms it: 7 enumeration rows failed.
- **Fix:** The rule's docstring states the execution measurement ("до плана 16-16 из 25 строк сохранялись 7"). The plan's other numbers were confirmed exactly: 830 examples with 0 lost, the 9-code non-geographic split, and the enumeration figures 1935 / 583 / 558 / 400.
- **Files modified:** `tests/test_services/test_phone.py`
- **Committed in:** `073e7f65`

---

**Total deviations:** 2 auto-fixed (both Rule 1, accuracy of a stated measurement).
**Impact on plan:** Behaviour is exactly as planned. Only two prose figures were corrected to the measured truth. No scope creep.

**Additions, not deviations:**
- The REFACTOR commit `8b30aaed` (cosmetic line wrap).
- Spec-header bullets in the test module for the new rules.
- A `wr09_*` paragraph in the docstring of the refusal rule.

## Gates on the final tree (2026-10-12, all under the shared pytest lock)

| Gate | Result | Baseline |
|------|--------|----------|
| `tests/test_services/test_phone.py` | 224 passed | 173 |
| Task 1 `-k "wr09 or foreign or …_mobile"` | 48 passed | — (plan floor 48) |
| Task 1 owner-outcome one-liner | `OK [True, True, '+375291234567', '+78005553535']` | — |
| Task 2 `-k "account_type_example or non_geographic or pure_and_never or ast_rule_catches"` | 4 passed | — (floor 4) |
| Task 2 `-s -k account_type_example` | exit 0 | — |
| Task 3 `-k "header_names… or never_stores… or owner_named… or example_number_of_the_metadata"` | 5 passed | — (floor 4) |
| Phase quick-run set (7 paths) | 610 passed | 559 |
| `tests/test_application/test_phone_single_writer_gate.py` | 119 passed | 119 |
| `tests/test_application/test_account_phone_writer.py` | 22 passed | 22 |
| `tests/test_phone_privacy_gate.py` | 94 passed | 94 |
| `tests/test_application` | 402 passed | 402 |
| Cross-cutting gates (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (2:37) | 576 |
| `uv run python -m compileall -q app main.py tests` | exit 0 | — |
| `scripts/prohibitions_census.py --check` | exit 0, registry 788 rows, bijection agrees | exit 0, 788 |
| Acceptance: old table rows untouched (`git diff 7a4ee433`, no `-    pytest.param`) | OK | — |
| Acceptance: no DE / IL 2+ extra-digit row in `MANUAL_ACCEPTED` | OK | — |
| Acceptance: `normalize_reported` byte for byte against `7a4ee433` | OK | — |
| `tests/test_planning` | run after this SUMMARY commit; result in the executor's return message | 218 passed, 2 skipped |

The module stays pure for the wave-mates. It has no logging import, call or binding (16-18's pinned counts do not move) and no dict or kwargs carrying a `phone` key. The privacy and single-writer gates are unchanged at 94 and 119.

**Substitutions (named, not hidden):**
- The full suite (`just test`, about 4300 tests and 45 min) was not run. The orchestrator's post-merge gate runs it on the merged tree.
- `graphify update .` was not run in the worktree, because `graphify-out/` is gitignored and absent here. The orchestrator runs it after merge.
- No `deferred-items.md` was created (parallel wave rule). Nothing was deferred.

## Issues Encountered

The worktree isolation checker refused a few compound shell commands (loops containing `git`, sed with a variable path). They were re-run as plain commands or as a scratch Python counter, `scratchpad/ac_16_16.py`. No effect on results.

## Known Stubs

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Phase 18 (manual-edit form) can rely on `normalize_manual` to refuse foreign numbers with unmarked extra digits, using the existing four refusal texts. The remaining DE / IL boundary is named in item 5.
- Phases 19 and 20 can read the header boundary paragraph as an accurate statement of what the auto path stores, including possible-but-invalid values.
- The owner act `human_verification` 1 (the 35 prohibition verdicts) is outside this plan.

## Self-Check: PASSED

- FOUND: `app/services/phone.py`, `tests/test_services/test_phone.py`.
- FOUND on this branch: `073e7f65`, `333bf8e0`, `b23f14e6`, `bb3d8239`, `5c3ffb94`, `8b30aaed`. `gsd-tools check evaluation-scope --plan 16-16 --commits-only` returned `status: resolved` with all six.
- Every acceptance criterion of Tasks 1–3 was re-run on the final tree and passed (see the table above).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-12*

---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 02
subsystem: services
tags: [phonenumberslite, phonenumbers, e164, normalization, privacy, tdd]

requires: []
provides:
  - "app/services/phone.py — PhoneError, normalize_manual, normalize_reported, format_phone, mask_phone; constants MANUAL_REGION, MANUAL_INPUT_MAX_CHARS, E164_MAX_DIGITS, REPORTED_MIN_DIGITS, EXAMPLE_PHONE, PHONE_ERROR_BLANK/TOO_LONG/EXTENSION/NOT_A_NUMBER, PHONE_ERROR_MESSAGES"
  - "tests/test_services/test_phone.py — criterion-3 table test by name (105 rows/tests)"
  - "phonenumberslite==9.0.41 pinned in pyproject.toml / uv.lock"
affects: [16-05 single writer, phase 17 caption, phase 18 manual form, phase 20 script, 16-04 privacy gate]

actuals:
  tokens: 7601      # chars/4 over the realized diff (30406 chars), same scale as the estimate
  tasks: 3          # task 1 resolved checkpoint (no commit) + tasks 2-3
  commits: 6        # git rev-list --count plan_head_before..plan_head_after
plan_head_before: 1a0c1bb5e17a77e9b41b22f3d2d985d70b019f6d
plan_head_after: c8fd4e96c461720c7d351e2117da5aaf3fde85c4

tech-stack:
  added: ["phonenumberslite 9.0.41"]
  patterns:
    - "One rule, per-entry policy: manual path raises PhoneError with a constant Russian text, automatic path returns None"
    - "Refusals raised outside the NumberParseException handler (_parse_or_none) so PhoneError has no __cause__/__context__"

key-files:
  created:
    - app/services/phone.py
    - tests/test_services/test_phone.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Owner approved phonenumberslite 9.0.41 on 2026-10-08 (~16:38 UTC), in his words: «пакет проверен, ставить 9.0.41». This matches the roadmap pin, so there is no deviation."
  - "Manual refusals are raised outside the except block (via _parse_or_none). `from None` alone still leaves __context__ set, so it would fail the plan's own test that __context__ is None."
  - "Each MANUAL_REJECTED row pins its exact refusal constant (measured against the library before RED), not only membership in PHONE_ERROR_MESSAGES"

patterns-established:
  - "Phone form is decided only in app/services/phone.py; writers and pages call it, never re-implement it"

requirements-completed: [PHONE-01, PHONE-21]

coverage:
  - id: D1
    description: "Messenger number (string or int) normalizes to E.164; source garbage (JID, brackets, 4/16 digits, None, bool, unknown country) gives None; Fragment +888 passes"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_an_automatic_number_lands_in_e164_and_shows_in_the_display_form"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_reported_number_is_normalized_to_e164 (9 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_garbage_from_a_source_leaves_the_number_unknown (10 rows)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Display form per country (RU, KZ, Fragment, UZ, US, DE); unparseable stored value shown as is"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_stored_number_is_shown_in_the_international_form (11 rows)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Manual free-form input normalizes to E.164 (criterion 3); local-only, extension, garbage, >32 chars refused; O-1 pinned (manual +888 refused, 888... becomes +788...)"
    requirement: PHONE-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_by_hand_is_normalized_to_e164 (17 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_number_typed_by_hand_is_refused_with_an_explanation (20 rows)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Refusal texts are a closed set of four Russian constants with the example; no input, no __cause__/__context__ (D-18)"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_every_refusal_text_is_a_declared_constant_with_the_example (20 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_refusal_texts_are_exactly_four_distinct_russian_constants"
        status: pass
    human_judgment: false
  - id: D5
    description: "mask_phone: +79991234567 -> '+7 *** ***-**-67'; only country code + two last digits visible"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_stored_number_is_masked_for_a_human (7 rows)"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_a_mask_shows_only_the_country_code_and_two_last_digits (5 rows)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Module purity: only phonenumbers + stdlib imports, no is_valid_number, no bare is_possible_number (ast)"
    verification:
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_module_is_pure_and_never_asks_validity"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_phone.py#test_the_ast_rule_catches_a_validity_call_and_a_database_import"
        status: pass
    human_judgment: false
  - id: D7
    description: "phonenumberslite==9.0.41 installed via just add after the owner's legitimacy answer; locked wheel matches the audited file"
    verification:
      - kind: other
        ref: "uv run python -c \"import phonenumbers; print(phonenumbers.__version__)\" -> 9.0.41"
        status: pass
      - kind: other
        ref: "uv.lock wheel phonenumberslite-9.0.41-py2.py3-none-any.whl size 473205 sha256 33347389a9105f4f..."
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-08
status: complete
---

# Phase 16 Plan 02: Phone normalization module Summary

**Pure `app/services/phone.py` on phonenumberslite 9.0.41. It turns a typed number (`8 999 123-45-67`, `+7 (999) …`, full-width digits, `tel:`) or a number reported by a messenger (a string or an int, including Fragment `+888…`) into a single E.164 string. It shows stored numbers in each country's international format and masks them as `+7 *** ***-**-67`. Every manual refusal comes from a closed set of four Russian constant texts that never contain the input.**

## Performance

- **Duration:** about 10 min (continuation run; Task 1 was resolved earlier by the owner)
- **Started:** 2026-10-08T16:39:43Z
- **Completed:** 2026-10-08T16:50:10Z
- **Tasks:** 3 (Task 1 resolved checkpoint, Tasks 2–3 executed)
- **Files modified:** 4

## Task 1 — resolved checkpoint (no commit)

`checkpoint:human-verify gate="blocking-human"`: is `phonenumberslite==9.0.41` legitimate? The gsd guard returned SUS (`too-new`, `unknown-downloads`, `no-repository`).

- **Owner's answer, verbatim:** «пакет проверен, ставить 9.0.41» ("package checked, install 9.0.41")
- **Date:** 2026-10-08, ~16:38 UTC
- **Chosen version:** 9.0.41 (matches the roadmap pin; no deviation)
- **Facts shown to the owner first:** the checkpoint executor re-measured them read-only at 2026-10-08 16:12 UTC, and the orchestrator checked them again independently.
  - Wheel `phonenumberslite-9.0.41-py2.py3-none-any.whl`: 473205 bytes, uploaded 2026-10-08T10:50:52Z, not yanked, sha256 prefix `33347389a9105f4f`.
  - Author: David Drysdale <dmd@lurklurk.org>.
  - The full `phonenumbers 9.0.41` was uploaded at 10:51:07Z.
  - GitHub tag `v9.0.41` points to commit e9214709.
  - pypistats: 304189/day, 1684566/week, 4953252/month.
  - Fallback 9.0.40 (2026-09-24) was offered and not chosen.
- **Check after install:** the `uv.lock` wheel entry matches the audited file (size 473205, sha256 `33347389a9105f4f5bd002d60ad9e721e5233950aa6219fb35c20ea2acf8e68f`, upload-time 2026-10-08T10:50:52.137Z).

## Accomplishments

- **Automatic path `normalize_reported`:**
  - Accepts a string or int with or without a leading `+`.
  - Drops `bool` and `None`.
  - Requires ASCII digits only, 5 to 15 of them, then calls `parse("+" + digits, None)`.
  - Runs no possibility check, so Fragment `+888…` survives. Garbage returns `None` silently.
- **Display `format_phone`:** each country gets its own `INTERNATIONAL` grouping. An unparseable stored value is returned as is (D-06).
- **Manual path `normalize_manual`:** parses with region `RU` and rejects input in this order:
  1. more than 32 raw characters,
  2. blank input,
  3. input the library cannot parse,
  4. an extension,
  5. any result other than strict `IS_POSSIBLE` (this rejects `IS_POSSIBLE_LOCAL_ONLY`, so `123-45-67` does not become `+71234567`),
  6. more than 15 E.164 digits.
- **Owner decision O-1** is pinned by named rows: manual `+888 0123 4567` is refused; manual `88801234567` becomes `+78801234567`.
- **Mask `mask_phone`** follows the display form: it keeps `+`, the country code and the last two digits. An unparseable value becomes `+`, then stars, then the last two digits; with fewer than four digits it is `+***`.
- **Purity:** an `ast` rule checks that the module imports only `phonenumbers` and stdlib, and never calls `is_valid_number` or bare `is_possible_number`. A planted negative control proves the rule catches both.

## Task Commits

1. **Task 1: legitimacy checkpoint.** Resolved by the owner; no commit.
2. **Task 2 (tracer): reported number to display form**
   - RED `7e7688f5` `test(16-02): add failing tracer test for reported number to display form`
   - dependency `d2f486e5` `chore(16-02): add phonenumberslite 9.0.41 after owner legitimacy check`
   - GREEN `4c880148` `feat(16-02): implement reported-number normalization and display form`
3. **Task 3: manual input, refusals, mask, purity**
   - RED `0abee69d` `test(16-02): add failing tests for manual input, refusal texts, mask and module purity`
   - GREEN `fd4c88d4` `feat(16-02): implement manual normalization with Russian refusals and D-10 mask`
   - REFACTOR `c8fd4e96` `refactor(16-02): route every parse in phone.py through _parse_or_none`

## TDD Gate Compliance

Both cycles have a RED commit before their GREEN commit, and the optional REFACTOR commit is present.

**RED, Task 2.** Run with `uv run pytest tests/test_services/test_phone.py::test_an_automatic_number_lands_in_e164_and_shows_in_the_display_form -q -p no:randomly --junit-xml=.pytest_cache/gsd-red/red1.xml`, started 2026-10-08T16:40:59Z, exit 1. The output has all three required matches:
- `FAILED tests/test_services/test_phone.py::test_an_automatic_number_lands_in_e164_and_shows_in_the_display_form`
- `1 failed, 1 warning in 0.15s`
- `E       assert None == '+79991234567'`

`check tdd-red-evidence` on the JUnit record returned `RED_EVIDENCE_OK` (`target_test_failed`, format `junit`, tests 1, fail 1). Semantic check: the target ran and failed on its first planned assertion, because the stub `normalize_reported` returned `None`. There was no collection, import or fixture fault.

**RED, Task 3.** Run with `uv run pytest tests/test_services/test_phone.py::test_a_russian_number_typed_by_hand_lands_in_e164 -q -p no:randomly --junit-xml=.pytest_cache/gsd-red/red2.xml`, started 2026-10-08T16:44:32Z, exit 1. The three required matches:
- `FAILED tests/test_services/test_phone.py::test_a_russian_number_typed_by_hand_lands_in_e164`
- `1 failed, 1 warning in 0.20s`
- `E       assert '8 999 123-45-67' == '+79991234567'`

The verb returned `RED_EVIDENCE_OK`. Semantic check: the target failed on the planned assertion, because the stub `normalize_manual` returned its input. A whole-file run at that point gave `68 failed, 37 passed` with no ERROR rows; every failure was a behavioral assertion in the new tables.

**GREEN.** Task 2: 31 passed. Task 3: 105 passed, and the `-k "by_hand or refusal_text or mask or pure"` selection gave 72 passed, 33 deselected. After REFACTOR: 105 passed.

## Files Created/Modified

- `app/services/phone.py`: the pure phone-form module (5 public functions, constants, the `_parse_or_none` helper), with a Russian header explaining the reasons.
- `tests/test_services/test_phone.py`: table tests for criterion 3, D-05/D-06/D-10/D-14/D-18 and O-1, plus the `ast` purity rule and its negative control.
- `pyproject.toml`, `uv.lock`: the `phonenumberslite==9.0.41` pin, added via `just add` and not edited by hand.

## Decisions Made

- **Refusals are raised outside the `except` block** (helper `_parse_or_none`). The plan's action says "raised `from None`". Inside a handler, `from None` clears `__cause__` but leaves `__context__` set, which fails the plan's own behavior 4 (`__context__ is None`). Raising outside the handler meets both, and `from None` is kept on that raise anyway.
- **`MANUAL_REJECTED` pins the exact constant for each row.** For example, extension rows give `PHONE_ERROR_EXTENSION`, blank rows give `PHONE_ERROR_BLANK`, and the 33-character rows give `PHONE_ERROR_TOO_LONG`. These expectations come from a read-only probe of the library run before RED, and the results matched the RESEARCH tables row for row.
- **Unparseable mask digits are counted as ASCII `0`–`9` only**, so non-ASCII "digits" never show up in the mask.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `raise … from None` inside the handler would fail the plan's own `__context__` assertion**
- **Found during:** Task 3 GREEN
- **Issue:** `from None` sets `__suppress_context__`, but `__context__` still holds the `NumberParseException`.
- **Fix:** parse through `_parse_or_none` and raise `PhoneError` after the handler has exited.
- **Files modified:** `app/services/phone.py`
- **Verification:** `test_every_refusal_text_is_a_declared_constant_with_the_example`, 20 rows green
- **Committed in:** `fd4c88d4`

**2. [Rule 2 - Test strength] Extra assertions beyond the plan's list**
- **Found during:** Task 3 RED
- **Added:**
  - an exact constant for each `MANUAL_REJECTED` row,
  - `test_the_length_boundary_rows_are_exactly_at_and_over_the_limit` (the 32 and 33 boundary strings really have those lengths),
  - `test_the_refusal_texts_are_exactly_four_distinct_russian_constants`,
  - a planted negative control for the `ast` rule.
- **Files modified:** `tests/test_services/test_phone.py`
- **Committed in:** `0abee69d`

### Procedural deviations (orchestrator instructions / tooling)

- **The dependency got its own `chore(16-02)` commit** between Task 2 RED and GREEN, as the orchestrator instructed. The plan had placed it in GREEN step 1.
- **RED records live in `.pytest_cache/gsd-red/`.** That directory is gitignored and sits inside the worktree, and nothing there was committed. `check tdd-red-evidence` refuses a record outside the project (`path escapes its allowed directory`). A first RED run written to the scratchpad was thrown away because its `runStartedAt` had been estimated, not measured. RED was re-run with a measured start time, and only that re-run is cited above. The record-builder script stayed in the scratchpad.
- **Acceptance grep `grep -c 'name = "phonenumberslite"' uv.lock` returns `3`, not `1`.** The pattern is unanchored, so it also matches the two dependency references `{ name = "phonenumberslite" }` / `{ name = "phonenumberslite", specifier = "==9.0.41" }`. The anchored `grep -c '^name = "phonenumberslite"' uv.lock` returns `1`: there is exactly one package entry. The lock is correct; only the criterion's pattern is loose.

**Total deviations:** 2 auto-fixed (1 bug, 1 test-strength) and 3 procedural.
**Impact on plan:** none on scope. The `__context__` fix is needed for the D-18 guarantee to hold.

## Verification Run (final tree)

- `tests/test_services/test_phone.py`: 105 passed.
- Cross-cutting gates (`tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_templates tests/test_application/test_declared_invariants.py -q -p no:randomly`): **576 passed** in 156 s.
- `tests/test_services/`: **398 passed**.
- `tests/test_planning`: **15 failed, 193 passed**, the same count as the base.
  - The failing set is 2 in `test_deferred_items_are_idempotent.py`, 9 in `test_plan_prohibitions_census.py` and 4 in `test_requirement_completion_follows_verification.py`.
  - These are the 6 milestone-start rules plus the 9 census rules that plan 16-01 fixes.
  - This plan touches no file under `.planning/` except this SUMMARY.
- `uv run python -m compileall -q app main.py tests`: OK.
- `uv run python -c "import phonenumbers; print(phonenumbers.__version__)"` prints `9.0.41`.

**Substitutions, named:**
- The full suite (`just test`) was not run. It is the orchestrator's post-merge gate.
- `graphify update .` was not run in the worktree. The orchestrator runs it after merge.
- `tests/test_phone_privacy_gate.py` belongs to sibling 16-04 and is absent here, so it runs on the merged tree. By `grep`, `app/services/phone.py` has no log or print call, and every `PhoneError(...)` is built from a module constant.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None. The worker images are not affected (`max_worker` has its own `requirements.txt`; `wa_worker` is Node).

## Next Phase Readiness

- 16-05 (the single writer) can import `normalize_reported` / `normalize_manual` / `PhoneError` directly.
- Phases 17, 18 and 20 can use `format_phone`, `PHONE_ERROR_MESSAGES` and `mask_phone`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-08*

## Self-Check: PASSED

- FOUND: app/services/phone.py, tests/test_services/test_phone.py, pyproject.toml, uv.lock
- FOUND on branch (1a0c1bb5..HEAD): 7e7688f5, d2f486e5, 4c880148, 0abee69d, fd4c88d4, c8fd4e96

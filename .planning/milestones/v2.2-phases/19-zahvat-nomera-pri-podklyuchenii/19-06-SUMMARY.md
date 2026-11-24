---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 06
subsystem: accounts
tags: [max, phone, normalize_manual, htmx, 422, fastapi, jinja2]

requires:
  - phase: 19-zahvat-nomera-pri-podklyuchenii
    provides: "19-05: capture_connect_phone and reported_phone_from_status already in app/pages/accounts.py; 19-01: module logger and the Phase 16 writer"
provides:
  - "accounts_connect_max_start parses the phone field with normalize_manual; credentials and start_session get E.164"
  - "invalid and empty numbers answer 422 through the existing respond_field_error path with a PhoneError constant text"
  - "hint under the MAX phone field that names the fallback purpose without a number"
affects: [19-07, 19-08]

actuals:
  tokens: 5580
  tasks: 2
  commits: 4

plan_head_before: e6ff050ec295dcac9c59d13aa268097a1a3b9242
plan_head_after: 5d4f605ad62004d19dc4a6d345288ac7cc0918ea

tech-stack:
  added: []
  patterns:
    - "PhoneError -> respond_field_error(request, page=_page, fragment=_fragment) with builders passed by name, single call site"
    - "form number kept only in credentials of the connecting row as E.164; the phone column is not written at start"

key-files:
  created: []
  modified:
    - app/pages/accounts.py
    - app/templates/accounts/includes/max_connect_step.html
    - tests/test_pages/test_max_connect_transport.py

key-decisions:
  - "Blank field answers PHONE_ERROR_BLANK; MAX_EMPTY_PHONE_ERROR deleted after a remeasure showed three uses in app/pages/accounts.py and none in tests or scripts"
  - "Form number lives between POST and polling only in account.credentials as E.164 (D-10); a stored phone column would block the number MAX reports (plan 19-07)"

requirements-completed: [PHONE-14]

coverage:
  - id: D1
    description: "Free-form number in the MAX form (8 999 123 45 67, the placeholder) reaches credentials and start_session as +79991234567; the phone column stays NULL at start"
    requirement: PHONE-14
    verification:
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_a_free_form_number_starts_the_session_with_the_normalized_value"
        status: pass
    human_judgment: false
  - id: D2
    description: "Invalid (abc, 33 chars, hostile markup) and empty numbers answer 422 on both transports with PhoneError text and escaped echo; no QR, no start_session, no account"
    requirement: PHONE-14
    verification:
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_an_invalid_number_answers_422_and_opens_no_qr"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_a_hostile_phone_never_reaches_the_response_raw"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_an_empty_phone_answers_422_with_the_echo_on_both_transports"
        status: pass
    human_judgment: false
  - id: D3
    description: "Hint under the MAX phone field explains why the number is asked, with no digits"
    requirement: PHONE-14
    verification:
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_the_phone_field_explains_why_the_number_is_asked"
        status: pass
    human_judgment: true
    rationale: "Wording and placement of the hint under the field is a UX judgment; the test only proves presence, node and absence of digits"

duration: 22min
completed: 2026-11-22
status: complete
---

# Phase 19 Plan 06: MAX form number normalization Summary

**MAX connect form parses the phone field with `normalize_manual` (free-form input becomes E.164 in `credentials` and `start_session`), rejects bad or empty input with a 422 `PhoneError` text before the QR opens, and carries a hint about the fallback number.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-11-22T18:15:00Z
- **Completed:** 2026-11-22T18:37:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `accounts_connect_max_start` reads `str(form.get("phone") or "")` and parses it with `normalize_manual`; `8 999 123 45 67` and the field placeholder `+7 999 123-45-67` reach `account.credentials` and `start_session(phone=…)` as `+79991234567`. The `phone` column is not written at start (D-10).
- `PhoneError` (blank, not a number, too long) answers 422 through the single existing `respond_field_error(request, page=_page, fragment=_fragment)` call; the input is echoed in the field (autoescaped) and never placed in the error text. `MAX_EMPTY_PHONE_ERROR` is gone.
- `hint='Покажем его в списке аккаунтов, если MAX не сообщит номер сам'` under the field; the form `action`/`method`/`target` are unchanged.

## Task Commits

1. **Task 1 (tracer): free-form number reaches credentials and worker as E.164**
   - RED `5db16c8b` (test)
   - GREEN `3385dc0a` (feat)
2. **Task 2: PhoneError 422 pinned with echo, hint under the field**
   - RED `554b7864` (test)
   - GREEN `5d4f605a` (feat)

**Plan metadata:** the docs commit that carries this file.

## TDD

### Task 1 RED

- Command: `uv run pytest tests/test_pages/test_max_connect_transport.py -q -p no:randomly --junit-xml=.gsd/tdd-evidence/19-06/red1.xml`, exit code 1, `2 failed, 5 passed`.
- Failing lines: `FAILED tests/test_pages/test_max_connect_transport.py::test_a_free_form_number_starts_the_session_with_the_normalized_value[8 999 123 45 67]` and `[+7 999 123-45-67]`.
- Causal literal: `AssertionError: форма MAX положила в credentials ненормализованный номер` with `assert '8 999 123 45 67' == '+79991234567'`.
- Classifier: `check tdd-red-evidence` on the camelCase record built from the JUnit XML (target `…normalized_value[8 999 123 45 67]`) returned `RED_EVIDENCE_OK / target_test_failed`. The first attempt with the unparametrized name returned `INVALID_RED / no_target_test_failure` (the report names parametrized ids with brackets), so the record uses the full id.
- `semanticAssessment`: the target test executed, reached the `credentials` assertion on the planned behavior, and failed because the stored value was the raw input; no setup, import or fixture fault.

### Task 2 RED

- Command: same file, exit code 1, `1 failed, 9 passed`.
- `FAILED tests/test_pages/test_max_connect_transport.py::test_the_phone_field_explains_why_the_number_is_asked`, literal `AssertionError: под полем номера MAX нет подсказки о запасном номере`.
- Classifier: `RED_EVIDENCE_OK / target_test_failed`.
- `semanticAssessment`: the GET page of the wizard lacked the hint text (the first assertion), the planned reason. The pinning tests in the same commit were green already, as the plan states (behavior delivered by task 1).

### Negative controls (mutations, not committed, `git checkout --` after each)

| Mutation | Result |
|---|---|
| (2) old short blank text `Введите номер телефона` in the handler | `test_an_empty_phone_answers_422_with_the_echo_on_both_transports` red |
| (3) `start_session` awaited before the number is parsed | six tests red (`test_max_start_over_htmx_returns_the_step_container`, both tracer params, hostile, both invalid params) |
| (4) `field_error = f"{exc} ({submitted})"` | first run stayed GREEN (10 passed): the hostile test only checked that a `PhoneError` text was present. Test strengthened to assert the escaped hostile mark appears exactly once (the field echo); the same mutation then turned `test_a_hostile_phone_never_reaches_the_response_raw` red |
| (5) raw `submitted` into `credentials` | both tracer params red |

### Gate sequence

`test(19-06)` RED precedes `feat(19-06)` GREEN in both tasks; no refactor commit (nothing to clean).

## Files Created/Modified
- `app/pages/accounts.py` - `normalize_manual`/`PhoneError` import, field parsing, 422 branch via `PhoneError`, rewritten docstring paragraphs (earlier text quoted as "до Фазы 19"), constant removed.
- `app/templates/accounts/includes/max_connect_step.html` - `hint=` on the phone field and the explaining template comment.
- `tests/test_pages/test_max_connect_transport.py` - tracer test, `PHONE_ERROR_BLANK` import instead of the local literal, `test_an_invalid_number_answers_422_and_opens_no_qr`, rewritten `test_a_hostile_phone_never_reaches_the_response_raw`, hint test, module header paragraph rewritten by generation.

## Decisions Made
- Followed the plan: blank and invalid input share one `try: normalize_manual / except PhoneError` branch.
- `MAX_EMPTY_PHONE_ERROR` remeasure before deletion: `grep -rn MAX_EMPTY_PHONE_ERROR app tests scripts` printed only `app/pages/accounts.py:849, 931, 939`; after deletion it prints nothing.
- `PYTHONPATH=.` is needed for the plan's `ast` acceptance one-liner when run from a script file; it returned exit 0 (`normalize_manual(submitted)` present, no `account.phone`, no `reported_phone(`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in the plan's test design] Hostile test did not catch the input substituted into the error text**
- **Found during:** Task 2 (negative control 4)
- **Issue:** the plan's rewritten rule checked only the presence of a `PHONE_ERROR_MESSAGES` text; mutation 4 stayed green.
- **Fix:** the rule asserts the escaped hostile string occurs exactly once in the 422 body (the field echo).
- **Files modified:** `tests/test_pages/test_max_connect_transport.py`
- **Verification:** mutation 4 reddens the rule; unmutated run green.
- **Committed in:** `5d4f605a`

**2. [Rule 3 - Blocking] RED evidence target name for a parametrized test**
- **Found during:** Task 1 RED
- **Issue:** the classifier returned `no_target_test_failure` for the bare test name; the JUnit report carries `name[param]`.
- **Fix:** the record names the parametrized id. No file change.

### Plan text versus the tree
- The plan predates merges 19-01 and 19-05; `app/pages/accounts.py` already had `logger` and `capture_connect_phone` imports. They were not touched; line numbers were located by name.

**Total deviations:** 2 (1 test-design fix, 1 evidence-format workaround). **Impact:** none on scope.

## Verification Results
- `tests/test_pages/test_max_connect_transport.py`: 10 passed.
- Phone gates (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`, `test_phone_writer_runtime_guard`) plus `test_impersonation_gate`: 1253 passed.
- `test_htmx_post_pairs`, `test_htmx_gates`, `test_impersonation_gate`, `test_htmx_validation_sink`, `test_htmx_preserved`, `test_money_perimeter_gate`: 234 passed (task 1 run).
- `tests/test_templates`, `test_responsive_markup`, `test_htmx_post_pairs`, `test_htmx_gates`, `test_shell`, `test_declared_invariants`, `test_notices_registry`, `test_connect_phone_capture`, `test_max_connect_transport`: 1031 passed.
- `compileall -q app tests`: exit 0. `scripts/prohibitions_census.py --check`: exit 0.
- Acceptance greps: `normalize_manual(submitted)` = 1; `respond_field_error(request, page=_page, fragment=_fragment)` = 2; `MAX_EMPTY_PHONE_ERROR` absent; hint text = 1; `form_wrapper(action='/accounts/connect/max/start'` = 1; `PHONE_ERROR_BLANK` in the test file = 4; old local literal = 0.
- `graphify update .` was NOT run (orchestrator instruction: the graph lives in the main checkout).

## Issues Encountered
- Test runs through `flock` of the shared pytest lock are slow (the largest gate run took 6.5 min); no failures.

## Known Stubs
None.

## Threat Flags
None: the plan's register (T-19-19, T-19-22, T-19-23) is covered by the tests above; no new surface.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 19-07 can read the fallback number from `credentials` of the `connecting` row; it is E.164 for rows written after this plan, and legacy rows with raw input simply give no fallback.
- PHONE-14 stays `Pending` in REQUIREMENTS.md by instruction (verification owns completion).

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

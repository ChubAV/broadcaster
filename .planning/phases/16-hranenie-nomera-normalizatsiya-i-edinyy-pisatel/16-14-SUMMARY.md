---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 14
subsystem: application
tags: [sqlalchemy, session-membership, phone, single-writer, tdd, gap-closure, IN-07]

requires:
  - phase: 16-08
    provides: "ACCOUNT_NOT_IN_SESSION, the post-flush id refusal in record_reported_phone, the _count_executes counter and the never-added rule"
provides:
  - "record_reported_phone: first line `if inspect(account).session is not session.sync_session: raise ValueError(ACCOUNT_NOT_IN_SESSION)`, before normalize_reported. No statement, no flush"
  - "ACCOUNT_NOT_IN_SESSION text rewritten to 'аккаунт не принадлежит сессии писателя: добавьте его через session.add'. Same symbol, no phone value (PHONE-21)"
  - "test_recording_an_account_never_added_to_the_session_raises parametrized none / empty / garbage / parseable"
  - "test_recording_an_account_outside_this_session_raises[detached]: an expunged account is refused with zero statements and its row is unchanged"
  - "test_recording_garbage_for_a_pending_member_issues_nothing: guards the no-statement mechanism (UNPARSEABLE, 0 statements, id stays None)"
affects: [phase 19 capture on connect (wizard contract with record_reported_phone), 16-15 review disposition IN-07]

actuals:
  tokens: 2595      # chars/4 over the realized diff of the two changed files (10378 chars), same scale as the estimate (35000)
  tasks: 2
  commits: 3        # git rev-list --count plan_head_before..plan_head_after, measured before the SUMMARY commit
plan_head_before: 625bcec58ed2aaad13cad29b7382d281b6d7dd6e
plan_head_after: 1fad15e3e59d336f909e6a50a12403b85cb3fad4

tech-stack:
  added: []
  patterns:
    - "Session-membership check without a statement: compare sqlalchemy.inspect(obj).session with AsyncSession.sync_session before any work"
    - "A caller error is refused before input normalization, so the refusal does not depend on what the source sent"

key-files:
  created: []
  modified:
    - app/application/accounts/phone.py
    - tests/test_application/test_account_phone_writer.py

key-decisions:
  - "The membership check is `inspect(account).session is not session.sync_session` as the first line, before normalize_reported. Flushing and then checking id before normalization was rejected: the flush would run other pending inserts early and would flush the object itself on the garbage path"
  - "The refusal now covers any object outside the writer's session: never-added, detached (expunge) and foreign-session objects. Before this plan a detached object got a conditional UPDATE by id in the writer's session, and the value was mirrored onto the detached object"
  - "The post-flush `if account.id is None: raise` is kept as a second line of defence. With it, `UPDATE … WHERE id IS NULL` cannot run, whatever the reasoning about the flush"
  - "Narrowing the docstring to 'parseable number only' and writing overrides was not chosen. This follows the pass default from 16-RESEARCH.md"

patterns-established:
  - "A writer refuses a foreign or unattached ORM object before touching input or the database"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "record_reported_phone with an account never added to the session raises ValueError(ACCOUNT_NOT_IN_SESSION) for None, '', 'garbage' and a parseable number. Zero statements; account.id stays None"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_an_account_never_added_to_the_session_raises[none|empty|garbage|parseable]"
        status: pass
    human_judgment: false
  - id: D2
    description: "A detached (expunged) account is refused with the same ValueError and zero statements; its row stays (None, False)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_an_account_outside_this_session_raises[detached]"
        status: pass
    human_judgment: false
  - id: D3
    description: "A pending session member with garbage input still gets UNPARSEABLE with zero statements and no flush (id stays None). This pins the no-statement mechanism"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_account_phone_writer.py#test_recording_garbage_for_a_pending_member_issues_nothing"
        status: pass
    human_judgment: false
  - id: D4
    description: "Race test untouched and green; the production writer keeps the manual number in every position, and the read-check-write negation still reddens position 2. Single-writer and privacy gates are green with the changed module"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: "git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py (exit 0)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_account_phone_race.py -k 'control_read_check_write or every_position or beyond_the_writer' (3 passed)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py (green within 124 passed)"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-10
status: complete
---

# Phase 16 Plan 14: Session-membership refusal in record_reported_phone Summary

**`record_reported_phone` now checks `inspect(account).session is not session.sync_session` before normalizing. The check issues no statement and does not flush. A forgotten `session.add` therefore fails loudly with `ValueError(ACCOUNT_NOT_IN_SESSION)` on every source input, including the old worker's `None`. Detached and foreign-session objects get the same refusal (IN-07, gap 4).**

## Performance

- **Duration:** about 10 min
- **Started:** 2026-10-10T05:20:27Z
- **Completed:** 2026-10-10T05:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- The Phase 19 wizard contract now holds on every input. A never-added account raises on `None`, `''`, `'garbage'` and `'79991234567'`. Before this plan, the first three silently returned `UNPARSEABLE`.
- Objects outside the writer's session (detached or from another session) are refused. Before, they got a conditional UPDATE by `id` in the writer's session, and the value was mirrored onto the object.
- A guard rule pins the chosen mechanism: a pending member with garbage input is neither flushed nor queried.
- The race test is unchanged (D-08), and both phase gates are green with the changed module.

## Task Commits

1. **Task 1 RED: parametrized never-added rule plus detached rule** - `8daff5dc` (test)
2. **Task 1 GREEN: membership check before normalization** - `164a0276` (feat)
3. **Task 2: pending-member garbage guard** - `1fad15e3` (test)

**Plan metadata:** the SUMMARY commit (docs) follows these.

## TDD Gate Compliance

- **RED** `8daff5dc`: `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly -k "never_added_to_the_session or outside_this_session"` ran under the lock with `--junit-xml` (kept in the gitignored `.pytest_cache/gsd-red/`). All three conjuncts were present:
  - `FAILED tests/test_application/test_account_phone_writer.py::test_recording_an_account_never_added_to_the_session_raises[none]`, plus `[empty]`, `[garbage]` and `test_recording_an_account_outside_this_session_raises[detached]`
  - summary `4 failed, 1 passed, 16 deselected`
  - causal literal `Failed: DID NOT RAISE <class 'ValueError'>`, four times
  - `check tdd-red-evidence` on the JUnit record returned `RED_EVIDENCE_OK` (`target_test_failed`, tests 5, fail 4, pass 1, format junit).
  - **Semantic assessment:** the target ran and failed on the planned `pytest.raises(ValueError)` assertion. The writer normalized first and returned `UNPARSEABLE` (none/empty/garbage), or ran an UPDATE by id on the detached object. There was no collection, import or fixture fault. `parseable` passed, as planning measured, because the post-flush id check already caught it.
- **GREEN** `164a0276`: the same selection gave `5 passed`; the whole file gave `21 passed`.
- **REFACTOR:** none needed.
- Task 2 is a `type="auto"` guard with no RED of its own, by construction (see the plan's `<scope_note>`). It is committed as `test(16-14)`. `git log --grep='^test(16-14)'` shows 2 lines.
- **Tracer feedback gate (Task 1):** the run is interactive (`auto_advance` false, `_auto_chain_active` false), the mode is `end-of-phase`, and `<verify>` is automated-only. I re-ran all four `<verify>` commands and they were green, so execution continued to Task 2 without a checkpoint.

## Files Created/Modified

- `app/application/accounts/phone.py`: added `inspect` to the imports, rewrote the `ACCOUNT_NOT_IN_SESSION` text, and made the membership check the first line of `record_reported_phone`. The docstring now states the contract and records the WR-05 → IN-07 history. The post-flush id check is kept.
- `tests/test_application/test_account_phone_writer.py`: four-row parametrization of the never-added rule, the new detached rule, and the new pending-member guard. The file goes from 17 to 22 rules.

## Gate Results (final tree `1fad15e3`, all under the shared flock)

| Gate | Result |
|------|--------|
| `tests/test_application/test_account_phone_writer.py` | 22 passed (17 at base: +3 rows, +1 detached, +1 guard) |
| `-k "never_added_to_the_session or outside_this_session"` | 5 passed |
| `-k pending_member` | 1 passed |
| `git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py` | exit 0 |
| race `-k "control_read_check_write or every_position or beyond_the_writer"` | 3 passed |
| race + single-writer gate + privacy gate | 124 passed |
| phase quick run (`test_phone.py`, writer, race, writer gate, privacy gate, CHECK model, `tests/test_migrations`) | 426 passed (425 after task 1) |
| `tests/test_application` | 331 passed (326 at base, +5) |
| wide `app/` source gates (6 files) | 130 passed |
| cross-cutting gates (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (= base) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 |
| `tests/test_planning -q` (after the SUMMARY commit) | measured after commit; reported in the executor's final message |

**Substitutions (named):** I did not run the full suite (`just test`, about 45 min, roughly 4300 tests); the orchestrator's post-merge gate runs it on the merged tree (orchestrator note 4). I did not run `graphify update .`, because there is no graph in the worktree; the orchestrator runs it after the merge (orchestrator note 3).

## Decisions Made

- I used the membership check with no statement (`inspect(account).session is not session.sync_session`) instead of flushing and checking `id` before normalizing. The reasons are in key-decisions above.
- The refusal is wider than "never added": it covers any object outside the writer's session. The constant text was rewritten because the old text ("после flush у него нет id") would be false once the check moved before the flush.
- The foreign-session case is not modeled in tests. The `:memory:` fixture does not guarantee a second session on the same database. The planner's measurement covers that case, the docstring names it, and the detached rule pins the same signal.

## Deviations from Plan

None. The plan was executed as written.

## Issues Encountered

None. The worktree isolation hook rejected compound shell commands, so I split them into plain commands. This did not change anything that was run or measured.

## Threat Flags

None. The change narrows accepted inputs. It adds no network, auth, file or schema surface. T-16-38 and T-16-39 are mitigated as the plan's threat register specifies.

## Deferred Items

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Gap 4 (IN-07) is closed in code and tests. The IN-07 disposition row belongs to 16-15.
- Wave-mate interaction: 16-11 tightens `normalize_reported` for over-long `+7` input. None of these rules depends on that acceptance; the parseable input `79991234567` is a valid 11-digit number. The module adds no log call, binding, `print` or phone-bearing exception text, so it does not trip the widened 16-13 privacy gate. Its only number write is still the existing conditional UPDATE (16-12 gate).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-10*

## Self-Check: PASSED

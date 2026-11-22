---
phase: 19-zahvat-nomera-pri-podklyuchenii
plan: 02
subsystem: messengers
tags: [whatsapp, baileys, wa-worker, phone-capture, lid, tdd]

requires:
  - phase: 19-zahvat-nomera-pri-podklyuchenii
    provides: "19-01 Telegram capture (context only; the WA seam is independent of it)"
provides:
  - ownPhoneFromMe(me, { isPnUser, jidDecode }) — pure parser of Baileys creds.me into digits or null, no Baileys import
  - GET /api/sessions/:id/status of a live WA session carries phone (digits without '+', or null)
  - tests/test_worker/test_wa_worker_own_phone.py — JS unit through run_node_script, outside the worker image
affects: [19-05, 19-08]

actuals:
  tokens: 3700
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "parser module with injected library functions: testable without node_modules and without starting main()"
    - "JS harness verdict carries booleans only, never the digits of a number"

key-files:
  created:
    - wa_worker/own_phone.js
    - tests/test_worker/test_wa_worker_own_phone.py
  modified:
    - wa_worker/index.js

key-decisions:
  - "Number source in /status is session.sock?.user (Baileys getter over creds.me): authState is not kept in the session state, the socket is"
  - "The 'no session' answer gets no phone field (RESEARCH B5): the app reads a missing field as null, so old and new worker images read the same way"
  - "Test goes through tests/conftest.py::run_node_script (Node absence fails loudly) instead of the node --test runner"

requirements-completed: [PHONE-13, PHONE-15]

duration: 22min
completed: 2026-11-22
status: complete

plan_head_before: f65ed0f516177d79ffe433df74f7a1823fcb6b21
plan_head_after: b25065f73482bc409ba6d56362b5a6f6100c6540
commits: 3

coverage:
  - id: D1
    description: "ownPhoneFromMe on the four D-03 inputs: PN with device and PN without device give digits, LID and empty id give null"
    requirement: PHONE-13
    verification:
      - kind: unit
        ref: "tests/test_worker/test_wa_worker_own_phone.py#test_the_own_number_is_taken_only_from_a_pn_jid"
        status: pass
    human_judgment: false
  - id: D2
    description: "index.js wires the real Baileys isPnUser/jidDecode into the live /status answer as phone; the 'no session' answer stays without it"
    requirement: PHONE-13
    verification:
      - kind: unit
        ref: "tests/test_worker/test_wa_worker_own_phone.py#test_index_wires_the_baileys_functions_into_the_status_answer"
        status: pass
    human_judgment: false
  - id: D3
    description: "The parser is total (garbage me/id, throwing or empty isPnUser/jidDecode, hosted server -> null) and writes nothing to the console"
    requirement: PHONE-15
    verification:
      - kind: unit
        ref: "tests/test_worker/test_wa_worker_own_phone.py#test_the_parser_never_throws_and_answers_null_on_garbage"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_wa_worker_own_phone.py#test_the_parser_writes_nothing_to_the_console"
        status: pass
    human_judgment: false
  - id: D4
    description: "Stubs stay honest: the Baileys pin is exactly 7.0.0-rc14 and own_phone.js imports nothing"
    requirement: PHONE-13
    verification:
      - kind: unit
        ref: "tests/test_worker/test_wa_worker_own_phone.py#test_the_stubs_are_honest_only_while_baileys_is_pinned_to_rc14"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_wa_worker_own_phone.py#test_the_parser_module_imports_nothing"
        status: pass
    human_judgment: false
  - id: D5
    description: "A real WhatsApp server hands out creds.me.id as a PN jid (<digits>:<device>@s.whatsapp.net), not a LID (assumption A2 of the research)"
    requirement: PHONE-13
    verification: []
    human_judgment: true
    rationale: "The unit uses stubs that copy the rc14 source; the real server answer needs a live account. Walkthrough W-3 of plan 19-08. If a LID arrives instead, the number stays unknown, which is correct per D-03."
---

# Phase 19 Plan 02: WhatsApp worker reports the own number Summary

**The WhatsApp worker now returns the account's own number in `/status` as `phone`, taken only through Baileys' `isPnUser` + `jidDecode(...).user` in a pure, never-throwing, silent module — LID digits are cut off in the worker.**

## Performance

- **Duration:** 22 min
- **Completed:** 2026-11-22T16:03:00Z
- **Tasks:** 2 (tracer + auto, both TDD)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `wa_worker/own_phone.js`: `export function ownPhoneFromMe(me, { isPnUser, jidDecode })` — `try`: `me.id` must be a string and `isPnUser(id)` true, then `jidDecode(id)?.user` must match `^[0-9]+$`, else `null`; `catch` gives `null`. No imports, no console, no string cutting (D-03, D-05, D-07).
- `wa_worker/index.js`: Baileys import line extended with `isPnUser, jidDecode`, `import { ownPhoneFromMe } from './own_phone.js'`, and `phone: ownPhoneFromMe(session.sock?.user, { isPnUser, jidDecode })` in the live-session `/status` answer (D-14). The "no session" answer, `BAILEYS_LOG_LEVEL || 'warn'` and `baileysLogger` are untouched.
- `tests/test_worker/test_wa_worker_own_phone.py`: 7 rules — four D-03 inputs, the `index.js` wiring, garbage totality (12 cases), agent suffix, console silence over all cases, Baileys pin `7.0.0-rc14`, module imports nothing.

## Task Commits

1. **Task 1 (tracer): `creds.me.id` through Baileys functions to the `phone` field of `/status`**
   - RED `393e3d55` (test)
   - GREEN `babfe18f` (feat)
2. **Task 2: totality, console silence, Baileys pin**
   - Pinning tests `b25065f7` (test) — green on arrival, see TDD Gate Compliance

Tracer verified end-to-end — expanding (task 1 `<verify>` re-run green before task 2).

## TDD Gate Compliance

`test(19-02)` `393e3d55` precedes `feat(19-02)` `babfe18f`. Task 2 is a pinning task: the five rules were green on task 1's code (the plan allows this: a GREEN fix is needed only "if a rule turns out red"), so there is no second `feat` commit; each rule was instead proven able to fail by a mutation (below). No `refactor(19-02)` commit — nothing to clean up. `wa_worker/` is untouched by task 2 (`git diff --stat -- wa_worker` empty after it).

### RED evidence

Record `.gsd/tdd-evidence/19-02/red-task1.json` (JUnit XML from `pytest --junit-xml`, camelCase record) validated by `gsd_run check tdd-red-evidence` -> `RED_EVIDENCE_OK`, reason `target_test_failed`.

- **Task 1:** `uv run pytest tests/test_worker/test_wa_worker_own_phone.py -q -p no:randomly -k test_the_own_number_is_taken_only_from_a_pn_jid` — exit 1, line `FAILED tests/test_worker/test_wa_worker_own_phone.py::test_the_own_number_is_taken_only_from_a_pn_jid`, summary `1 failed, 1 deselected`, cause literal `ERR_MODULE_NOT_FOUND ... wa_worker/own_phone.js` (Node stderr carried by `run_node_script`'s `pytest.fail`). Semantic assessment: the target executed; the run failed on the Node import of the module that does not exist yet — the planned RED for a new module (tdd_notes of the plan), not a syntax, fixture or collection fault. The sibling wiring test was also red at RED and went green with the same GREEN commit.

### Negative controls of the pinning tests (mutation of `own_phone.js` or the test, not committed)

| # | Mutation | Result |
|---|----------|--------|
| 1 | `try/catch` removed from `ownPhoneFromMe` | FAILED `test_the_parser_never_throws_and_answers_null_on_garbage` (1 failed, 6 passed) |
| 2 | `jidDecode(id)?.user` replaced by the digits cut out before `@` | FAILED `test_the_own_number_is_taken_only_from_a_pn_jid`, `…never_throws…`, `test_the_agent_suffix_is_dropped_by_jid_decode` (3 failed) |
| 3 | `console.log('x')` added inside the function | FAILED `test_the_parser_writes_nothing_to_the_console` (1 failed, 6 passed) |
| 4 | expected pin in the test changed to `7.0.0-rc15` | FAILED `test_the_stubs_are_honest_only_while_baileys_is_pinned_to_rc14` (1 failed) |
| 5 | `import … from '@whiskeysockets/baileys'` added at the top of the module | FAILED `test_the_parser_module_imports_nothing` (plus the four harness rules, which cannot load the module without `node_modules`; 5 failed) |

All mutations were reverted with `git checkout -- <file>` / `sed` back; the final tree equals the committed one.

## Files Created/Modified

- `wa_worker/own_phone.js` — pure parser, no imports (new)
- `wa_worker/index.js` — Baileys functions imported, `phone` added to the live `/status` answer
- `tests/test_worker/test_wa_worker_own_phone.py` — 7 rules via `run_node_script`, outside the worker image (new)

## Verification run

- `uv run pytest tests/test_worker/test_wa_worker_own_phone.py -q -p no:randomly`: 7 passed.
- `node --check wa_worker/index.js && node --check wa_worker/own_phone.js`: OK.
- `tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_worker`: 1264 passed.
- Other modules reading `wa_worker/` (`test_ops_state`, `test_queue_rows`, `test_log_masking`) plus `test_declared_invariants`: 158 passed.
- Acceptance greps: `export function ownPhoneFromMe` 1, baileys in own_phone.js 0, non-comment `.split(` 0, `isPnUser, jidDecode` in index.js 2, `from './own_phone.js'` 1, `BAILEYS_LOG_LEVEL || 'warn'` 1, `git ls-files -- 'wa_worker/*test*'` empty, `^def test_` 7, `7.0.0-rc14` in the test file 3.

## Decisions Made

- `session.sock?.user` is the source of `me` in `/status` (Baileys getter over `creds.me`), as the plan fixed.
- The `console` methods are replaced by a counter inside the harness, so the silence rule counts calls of the real function without printing anything; the verdict is serialised and checked for the digits of the number.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. (A mutation run waited several minutes on the shared pytest lock held by sibling executors; not a failure.)

## Assumptions not proven here

- A2: a real WhatsApp server returns `creds.me.id` as a PN jid. The unit stands on stubs copied from the rc14 source; the live check is walkthrough W-3 of plan 19-08. A LID there would leave the number unknown, which is the correct outcome by D-03.
- `phone` reaches the app only after plan 19-05 reads it; until then the extra field is ignored by the app.

## Known Stubs

None.

## Threat Flags

None - the only new surface is one response field on an existing endpoint, covered by T-19-06..T-19-08 of the plan's register.

## User Setup Required

None - no external service configuration required. The worker image must be rebuilt for `/status` to carry `phone` (plan 19-04 owns the rebuild recipe).

## Next Phase Readiness

- Plan 19-05 can read `body.get("phone")` from the worker `/status`; absence of the field equals `null`.
- PHONE-13 and PHONE-15 stay `Pending` in REQUIREMENTS.md: the live walkthrough (19-08) and the app side (19-05) close them.

---
*Phase: 19-zahvat-nomera-pri-podklyuchenii*
*Completed: 2026-11-22*

## Self-Check: PASSED

- FOUND: wa_worker/own_phone.js, tests/test_worker/test_wa_worker_own_phone.py
- FOUND commits: 393e3d55, babfe18f, b25065f7 (ancestors of HEAD)

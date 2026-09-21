---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
plan: 05
subsystem: testing
tags: [htmx, polling, gates, jinja2, negative-controls, named-zero]

requires:
  - phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
    provides: "13-01…13-04: the step include with six branches, the four wizard handlers on respond(), POLLING_CASES grown state by state, ownership (_owned)"
provides:
  - "Criterion-2 gate closed by template branch: STEP_MARKS, branch parse of tg_connect_step.html, test_every_wizard_step_is_reached_by_a_polling_case, test_every_polling_fragment_has_a_terminal_pair"
  - "Pure rule helpers over parameters (_polling_violations, _pairing_violations, _anchor_in_fragment, _unreached_steps) with six negative controls on synthetic input"
  - "TOP_LEVEL_BINDING_EXEMPT_TEMPLATES as a named zero (TOP_LEVEL_BINDING_EXEMPTIONS_DECLARED = 0) and the subject rule test_the_connect_screen_declares_no_top_level_binding"
  - "Phase 13 chronicles with tree measurements in test_htmx_markup_security.py (R-08-02) and test_components.py (_strip_js_comments)"
affects: [13-06, 15-FETCH-03, 15-hardening]

actuals:
  tokens: 10209
  tasks: 2
  commits: 2
plan_head_before: 43de5e2d145f96e5c2452c5bfcd763438f0bcfd7

tech-stack:
  added: []
  patterns:
    - "Closure by template branch: branches read from the template text (literals, `step in (…)` enumerations, the step chain's `{% else %}` fall-through), each branch confirmed by a structural response mark"
    - "Named zero for an exemption list: equality with a declared number replaces a non-emptiness rule, and a rule on the SUBJECT replaces a loop over the list"

key-files:
  created: []
  modified:
    - tests/test_routes/test_tg_user_auth.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_security.py
    - tests/test_templates/test_components.py

key-decisions:
  - "The start/error branch is the step chain's `{% else %}` plus an inline `if step == \"start\"`, not one condition with an enumeration as the plan said. The parser reads step literals anywhere and adds FALLBACK_STEP = \"error\" when a chain opened by a step condition has an `{% else %}`; enumeration support is kept and proven by a control."
  - "Each POLLING_CASES row declares its branch, and the rule asserts the response carries EXACTLY that branch's mark (not just its own mark). This makes the marks mutually exclusive and turns a mislabelled row into a red rule."
  - "The pair rule reads the poller's own route: a polling fragment's pair is a POST to qr-status answering 200 without a trigger."
  - "The vacuous connect-screen rule was rewritten onto its subject: the six-link chain of accounts/connect_tg_user.html declares zero top-level bindings. The rule that exemptions are never transition destinations moved into the per-entry checks of the exemption rule."
  - "thumb.html's onerror is named as outside R-08-02. Bringing plain event attributes into a counted inventory is left to Phase 15 (hardening)."

patterns-established:
  - "Gate rule on parameters + a control calling the SAME function with synthetic input, plus a working-copy mutant of the product file to quote the real rule's failure text"

requirements-completed: [FETCH-02]

coverage:
  - id: D1
    description: "Every step branch of tg_connect_step.html (start, waiting, qr_expired, password, connected, error) is reached by a POLLING_CASES row and confirmed by its mark; a new branch without a row is named (criterion 2, D-05)"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "tests/test_routes/test_tg_user_auth.py#test_every_wizard_step_is_reached_by_a_polling_case"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py#test_polling_stops_by_a_response_without_trigger (20 rows)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every polling fragment has a terminal pair (a 200 poll without hx-trigger), generalising test_sync_polling_stops (criterion 2)"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "tests/test_routes/test_tg_user_auth.py#test_every_polling_fragment_has_a_terminal_pair"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each gate rule has a negative control on synthetic input that reddens it"
    requirement: FETCH-02
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly -k control (6 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "TOP_LEVEL_BINDING_EXEMPT_TEMPLATES is a named zero; the non-emptiness and connect-screen rules no longer pass vacuously; reinstating the wizard script on the screen reddens the subject rule (D-12, Pitfall 4, T-13-16)"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_hx_location_destinations.py -q -p no:randomly -k 'exempt or connect_screen' (3 passed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "R-08-02 prose and the _strip_js_comments docstring carry Phase 13 chronicles with tree measurements"
    verification:
      - kind: other
        ref: "grep -c 'Фаза 13' tests/test_templates/test_htmx_markup_security.py (1) / tests/test_templates/test_components.py (1); both 0 on 43de5e2d"
        status: pass
    human_judgment: false

duration: 14min
completed: 2026-09-21
status: complete
---

# Phase 13 Plan 05: criterion-2 gate closed by template branch, stale wizard records cleaned up Summary

**`POLLING_CASES` is now closed by the branches of `tg_connect_step.html` rather than by states. The branches are read from the template text. Each row declares the branch it renders and must carry exactly that branch's mark. Every polling fragment must have a terminal poll pair. A new template branch without a row is named by the rule. Each rule runs on parameters and has a negative control on synthetic input. The wizard's top-level-binding exemption is a named zero, backed by a rule on its subject. The two gate docstrings carry Phase 13 chronicles with tree measurements.**

## Performance

- **Duration:** about 14 min
- **Started:** 2026-09-21T16:12:11Z
- **Completed:** 2026-09-21T16:26Z
- **Tasks:** 2 (task 1 `tdd="true"`)
- **Files modified:** 4, exactly the plan's `files_modified`. No product file under `app/` changed: `git diff 43de5e2d..HEAD -- app/` is empty.

## Accomplishments

- **Gate header** at the gate block in `test_tg_user_auth.py`. It names:
  - that the gate generalises `test_sync_polling_stops`
  - why the gate lives here and not in `test_htmx_inventory.py`: the markup polling gate cannot see a poller born from a macro, as 13-01 measured (§Инвентарь row 19, A2)
  - the D-05 correction: the poller lives inside the waiting fragment and not on the anchor
- **`STEP_MARKS`** maps each branch to a structural mark:
  - `start`: «Начать подключение»
  - `error`: «Начать заново»
  - `waiting`: `hx-trigger="every 3s"`
  - `qr_expired`: `hx-post=".../refresh-qr"`
  - `password`: `name="password"`
  - `connected`: «Подключено»
- **Branch parse.** It reads `step == "…"` literals, `step in (…)` enumerations, and the `{% else %}` of a chain opened by a step condition, which gives `error`. It has a six-branch anti-vacuum: zero branches is reported as «разбор веток не нашёл ни одной», and fewer than six as «разбор ослеп».
- **Registry.**
  - `_PollingCase` gained `step` and `method`.
  - All 19 existing rows now declare their branch.
  - A new row `page-start` (GET of the wizard page) is the only path to `start`. The rule reads it through `_content_of_the_wizard`, because the shell carries its own triggers.
- **Per-row rule.** `test_polling_stops_by_a_response_without_trigger` now also checks two things. It calls `_anchor_in_fragment` on every POST fragment. It calls `_polling_violations`: exactly one poller when the row polls, otherwise no `hx-trigger`, and the set of branch marks in the response must equal `{step}`.
- **New rules:**
  - `test_every_wizard_step_is_reached_by_a_polling_case`
  - `test_every_polling_fragment_has_a_terminal_pair`
  - The existing `test_the_polling_registry_holds_both_sides_of_the_pair` is kept.
- **Six controls**, each calling the same helper:
  - a terminal fragment with a trigger
  - a response of another branch
  - a registry without terminal polls
  - the anchor inside a fragment
  - a template branch without a case. This control also covers an enumerated pair and a chain without a fall-through.
  - a blind parse
- **Named zero.** `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES = {}` with `TOP_LEVEL_BINDING_EXEMPTIONS_DECLARED = 0` and a chronicle (1 in Phase 10, 1 → 0 in Phase 13, plan 13-05).
  - The non-emptiness rule became equality with the declared number. The per-entry checks stay, and the check that no exemption is also a destination moved in with them.
  - The vacuous `test_the_connect_screen_is_not_a_transition_destination_today` became `test_the_connect_screen_declares_no_top_level_binding`, a rule over the screen's six-link chain, with the control `test_control_a_reinstated_wizard_script_reddens_the_connect_screen_rule`.
- **Chronicles:**
  - «ДОПОЛНЕНИЕ ФАЗЫ 13» in the R-08-02 boundary prose, with the two grep commands and their output verbatim.
  - A Phase 13 chronicle in `_strip_js_comments`, with the measurement: 7 script bodies and 80 `//` lines, all of them comments, and 0 inside string literals. The string-aware parse therefore stays as a protection and does not reflect today's tree.

## Task Commits

1. **Task 1 (tdd="true"): criterion-2 gate closed by template branch.** `d0328bd2` (test)
2. **Task 2: named zero and chronicles.** `c669334b` (test)

No REFACTOR commit was needed.

## TDD Gate Compliance

**Disclosure: the task 1 rules were GREEN on the live tree from their first run.** The behaviour they guard shipped in 13-01…13-04, and the plan's `<behavior>` says so: «Правила этого плана зелены на прибытии». There is therefore no RED commit on the live tree, and none was manufactured. There is no `feat(13-05)` commit, because no product code changed. The single task 1 commit is `test(13-05)` `d0328bd2`, which the brief allows for GREEN.

Non-vacuity is proven in two ways, measured on the task 1 tree:

**A. Negative controls in the committed suite** (`-k control`: 6 passed). Each control calls the same helper as its rule, first with the clean input, which must pass, and then with the synthetic input, which must fail.

**B. Working-copy mutants against the REAL rules.** For each run the product template was edited in the working copy, the rule was run, and the file was restored from a scratchpad copy. Afterwards `git status --short app/` was empty. The failing assertion text is quoted from each run:

| Mutant | Rule run | Result and failing assertion |
|---|---|---|
| M1: `hx-trigger="every 3s"` on the `connected` branch div | `-k polling_stops` | **2 failed** (poll-success, verify-success): `AssertionError: опрос — успех, «Подключено»: / ответ несёт триггер — опрос не остановится / ответ несёт метки веток ['connected', 'waiting'] вместо ровно ветки 'connected'` |
| M3: `id="tg-connect-step"` on the waiting branch div | `-k polling_stops` | **2 failed** (start-waiting, refresh-success): `AssertionError: старт — QR и опросчик: фрагмент несёт идентификатор якоря — опрос переживёт свой ответ и не остановится (поправка D-05)` |
| M4: a new branch `{% elif step == "sms_code" %}` | `-k every_wizard_step` | **1 failed**: `AssertionError: реестр \`POLLING_CASES\` не замкнут по веткам \`accounts/includes/tg_connect_step.html\`: / ветки шаблона без метки в STEP_MARKS: ['sms_code'] / ветки шаблона, которых не достигает ни одна запись POLLING_CASES: ['sms_code']` |
| M2: registry with every terminal `qr-status` row removed (a throwaway script outside the repo sets the module global and calls the real test functions) | pair rule and closure | pair: `пара опроса не замкнута: / start-waiting: фрагмент с опросом без терминальной пары на /accounts/connect/tg_user/qr-status (200 без триггера) — останов не доказан / refresh-success: …`. Closure also went red: `ветки шаблона, которых не достигает ни одна запись POLLING_CASES: ['qr_expired']` |

I did not use the `check tdd-red-evidence` verb. There is no live-tree RED to record, and the brief says an exit code without a named failing assertion is not RED.

## Task 2 measurements

- **Pitfall 4 prediction, measured.** The HEAD version of the module was loaded from `git show HEAD:…` and its registry cleared:
  - `test_every_exempt_template_carries_a_non_empty_rationale` FAILED with `перечень изъятий пуст — правило непустоты стало бы вакуумным`. It was red by construction.
  - `test_the_connect_screen_is_not_a_transition_destination_today` PASSED on the empty registry. It was vacuous.
- **The new rules redden:**
  - One synthetic exemption entry gave `изъятий 1, объявлено 0: запись изъятия приходит вместе с летописью числа, а не молча`.
  - A working-copy mutant of `connect_tg_user.html` with the pre-phase `let` pair gave `AssertionError: на экране подключения Telegram вернулись объявления верхнего уровня инлайн-скрипта … accounts/connect_tg_user.html:15: let currentSessionId / …:16: let pollInterval`. The file was restored, and `git status --short app/` was empty.
- **Subject measurement:**
  - The live chain of the connect screen has 6 links and `[]` bindings.
  - The pre-phase page (`git show f21a6316:app/templates/accounts/connect_tg_user.html`) has `[(62, 'let', 'currentSessionId'), (63, 'let', 'pollInterval')]`. With the old exemption applied, the chain parse returned `[]`, so the exemption hid exactly these two bindings.
- **R-08-02 measurement, as quoted in the docstring:**
  - `grep -rnE "\bon(click|submit)=" app/templates/ | wc -l` gives `0`.
  - `grep -rnoE "\son[a-z]+=" app/templates/` gives `app/templates/components/thumb.html:34: onerror=`.

## Verification

- Task 1 verify:
  - full module: **56 passed**
  - `-k control`: **6 passed** (≥ 4 required)
  - `-k polling`: 28 passed
- Task 2 verify:
  - three-file run: **119 passed**
  - named-zero check: exit 0
  - `-k "exempt or connect_screen"`: 3 passed
- Wave gates (11 files): **395 passed** in 207 s, exit 0, with no registry red. The previous count was 385: +9 in the TG module (2 rules, 6 controls and the `page-start` row) and +1 control in the destinations module.
- `uv run python -m compileall -q app main.py tests` is clean. `graphify update .` was run.
- I did not run the full suite. The plan does not require it, and the orchestrator runs it after 13-06.

## Decisions Made

See `key-decisions`. The branch marks are required to be mutually exclusive. That is stricter than the plan, which only required each row's own mark. Without exclusivity, M1 would still have been caught by the trigger check, but a row mislabelled as `error` on a `connected` response would not have been caught.

## Deviations from Plan

### Auto-fixed Issues

**1. [Plan premise vs tree] The start/error branch is not «one condition with an enumeration»**
- **Found during:** Task 1, reading `tg_connect_step.html`.
- **Issue:** The plan says «Ветка `start`/`error` объявлена одним условием с перечислением — разбор обязан её прочесть как две ветки». In the tree it is the step chain's `{% else %}` plus an inline `'Начать подключение' if step == "start" else 'Начать заново'`. There is no `error` literal anywhere.
- **Fix:**
  - The parser reads step literals anywhere, so `start` comes from the inline condition, and adds `FALLBACK_STEP = "error"` when a step chain has `{% else %}`. The six-branch anti-vacuum holds.
  - Enumeration parsing (`step in (…)`) is still implemented. The control proves it reads two branches from one condition, and that removing the fall-through removes `error`.
- **Files modified:** tests/test_routes/test_tg_user_auth.py
- **Committed in:** `d0328bd2`

**2. [Rule 1 - found before commit] Two drafting defects, fixed before commit**
- The first draft of the connect-screen mutant anchored on the first `{% endblock %}`, which is the title block. It now anchors on `</div>\n{% endblock %}`, the content block.
- The R-08-02 docstring is not a raw string. The quoted grep patterns needed doubled backslashes: `\b` would have become a backspace and `\s` a SyntaxWarning. I checked the docstring value with `ast.get_docstring`.
- **Committed in:** `d0328bd2` / `c669334b`

### Acceptance-criterion discrimination (reported as the brief asks)

- **Task 1:**
  - The four grep criteria (`test_every_wizard_step…`, `test_every_polling_fragment…`, `def test_control_` ≥ 4, `STEP_MARKS` ≥ 2) were all **0 on `43de5e2d`** and are now 1, 1, 6 and 8.
  - `-k "polling"` green and non-empty was **already satisfied on HEAD**, because `test_polling_stops_by_a_response_without_trigger` and the pair test existed. On its own it does not measure the change. The change is proven by mutants M1–M4 and the six controls.
- **Task 2:**
  - The named-zero exit code was 1 on HEAD: there was one entry and no declared number.
  - `grep -c 'Фаза 13'` was 0 in both docstring files on HEAD and is now 1 in each.
  - `-k "exempt or connect_screen"` green was **already satisfied on HEAD**, by the two old rules. What proves the change are the measurements above: the old non-emptiness rule is red on the empty list, the old loop is vacuous, and the new rule is red on the mutant.

---

**Total deviations:** 1 plan-premise correction and 1 pair of drafting defects fixed before commit, plus 2 non-discriminating criteria reported, each proven another way. **Impact:** no scope creep. No registry moved, no product file changed, and every edit is inside `files_modified`.

## Issues Encountered

- None blocking. No gate registry reddened in the wave run: `NOT_YET_CONVERTED_COUNT` 10, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 17, `POST_PAIR_CASES_DECLARED` 58, `PAIRED_302_ASSERTIONS_DECLARED` 167, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 77 and `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 19 are unchanged.

## Threat Flags

None. T-13-07 (a new branch with a poller and no pair) is mitigated by the closure, the pair rule, the anchor guard and their controls. T-13-16 (the inline script returning to the connect screen) is mitigated by the subject rule and its control. No new surface was added.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- 13-06 writes the ROADMAP/REQUIREMENTS criterion chronicles. This plan did not touch those files.
- FETCH-02 is **not** marked Complete: 13-06 also declares it and has no SUMMARY yet.
- For Phase 15: `components/thumb.html:34` `onerror` is the one plain event attribute left in `app/templates/`. It is named in the R-08-02 prose as the boundary of a counted inventory.

## Self-Check: PASSED

- FOUND: tests/test_routes/test_tg_user_auth.py, tests/test_pages/test_hx_location_destinations.py, tests/test_templates/test_htmx_markup_security.py, tests/test_templates/test_components.py
- FOUND commits: d0328bd2, c669334b (`git rev-list --count 43de5e2d..HEAD` = 2 before this SUMMARY commit)

---
*Phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah*
*Completed: 2026-09-21*

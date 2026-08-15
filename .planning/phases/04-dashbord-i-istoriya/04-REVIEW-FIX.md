---
phase: 04-dashbord-i-istoriya
fixed_at: 2026-08-15T13:35:00Z
review_path: .planning/phases/04-dashbord-i-istoriya/04-REVIEW.md
iteration: 1
findings_in_scope: 17
fixed: 17
skipped: 0
status: all_fixed
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-08-15T13:35:00Z
**Source review:** `.planning/phases/04-dashbord-i-istoriya/04-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 17 (all WARNING-tier: WR-01 … WR-17)
- Fixed: 17
- Skipped: 0

**Scope note.** `fix_scope` was `critical_warning`. The review reports 0 critical
findings, 17 warnings and 5 info items (IN-01 … IN-05). The five `IN-*` findings
carry the label "Severity: WARNING (cosmetic)" in their bodies but are filed
under Info IDs and under the report's `## Info` heading, so they fall outside
this scope and were not attempted.

**Verification.** Every fix was verified by (1) re-reading the edited region,
(2) an `ast.parse` syntax check for Python files, and (3) the affected pytest
files. After the last commit the **full suite was run in the isolated worktree**
(`.claude/worktrees/rf-04-…`) against the main checkout's `.venv`:
**1420 passed, 0 failed (15m10s)**. The worktree has no `node_modules`/`.venv` of
its own; the interpreter came from `/source/broadcaster/.venv`, so the numbers
are reproducible from the main checkout after the branch fast-forward.

## Fixed Issues

### WR-01: Retry cooldown registry never evicted expired keys

**Files modified:** `app/pages/history.py`, `tests/test_pages/test_history_retry.py`
**Commit:** `3d0534d`
**Applied fix:** `_claim_retry_slot` now sweeps every entry whose deadline has
passed before reading its own key, so the dict is sized by *live* holds rather
than by lifetime retry count. The registry's comment block gains a third named
limit. New test `test_retry_slot_registry_does_not_grow_with_expired_holds`
claims 50 slots, expires them, claims one more, and asserts `len(...) == 1` —
structure, not prose.

### WR-02: "Busy" notice promised a queued task that one interleaving never queued

**Files modified:** `app/pages/history.py`, `tests/test_pages/test_history_retry.py`
**Commit:** `b2235b9`
**Applied fix:** `RETRY_BUSY` now reads "Повтор этой отправки уже запущен или
запускался только что — второй раз он не уйдёт. Повторите через минуту. Если
повтор ушёл в очередь, результат появится новой записью истории." The hold is
still claimed before the entity/balance checks (the concurrency window the plan
deliberately closed stays closed); the *text* now describes only what the guard
guarantees, and the history record is promised conditionally. The comment
enumerates the third reachable case the old one missed. The existing test was
retargeted from the old wording to the two invariants (refusal is stated;
the new-record promise is conditional).

### WR-03: `queued` set only after `send_task` returned, re-arming a double send

**Files modified:** `app/pages/history.py`, `tests/test_pages/test_history_retry.py`
**Commit:** `c4450f3`
**Applied fix:** `queued = True` is now set **before** the broker call; only
`celery.exceptions.OperationalError` (kombu's connection-failure class, raised
before the message is handed over) clears it. Any other exception keeps the
hold — an extra minute of waiting is cheaper than a second irreversible send.
The handler docstring gained a "граница у самого брокера" paragraph. Two new
tests pin both directions: an unknown exception keeps the hold, `OperationalError`
releases it.

### WR-04: "Worker is online" had a second definition in the macro

**Files modified:** `app/templates/dashboard/includes/worker_row.html`, `tests/test_pages/test_shell.py`
**Commit:** `967fd3a`
**Applied fix:** The visible state word now branches on `session.is_online`
(the shell-contract boolean derived from `WORKER_ONLINE_STATUS`) instead of
re-testing `session.status == 'active'`. New helper `_worker_states()` parses
the visible text, and `test_dashboard_lists_each_account_with_its_worker_state`
now asserts dot and word agree per account — the pairing the old
`data-worker-online`-only parse could not see.

### WR-05: Fourth copy of the messenger label map

**Files modified:** `app/constants.py`, `app/pages/history.py`, `app/pages/common.py`, `app/templates/dashboard/includes/worker_row.html`
**Commit:** `e5b7022`
**Applied fix:** `MESSENGER_LABELS` moved to `app/constants.py` (the project's
existing home for values both Python and Jinja read — importing it into
`common.py` from `history.py` would have been circular). `MESSENGER_CHIPS` is
now built from it, `history.MESSENGER_LABELS` is the same object, and
`templates.env.globals["messenger_labels"]` is bound next to `AD_STATUS_DRAFT`
so the macro can drop its literal while staying independent of caller context.

### WR-06: Shell materialised every messenger account on all 26 page routes

**Files modified:** `app/pages/common.py`, `app/pages/dashboard.py`, `app/templates/dashboard.html`, `tests/test_pages/test_shell.py`
**Commit:** `f17eb61`
**Applied fix:** The list query gained `.limit(WORKER_LIST_CAP)` (100). The two
aggregates (`sessions_total`, `sessions_online`) and `nav_counts.accounts` moved
back into the **existing** counts round-trip as scalar subqueries, so they stay
exact past the cap and cost no extra DB round-trip. `sessions_truncated` is
plumbed to the dashboard, which renders a `data-worker-truncated` note. The
single-predicate property D-35 actually protects (`WORKER_ONLINE_STATUS` used
identically by row and aggregate) is preserved; the docstring and
`test_shell_aggregate_is_derived_from_the_worker_list` were reworded to state
that invariant rather than "one physical read".
`test_shell_reads_worker_state_in_a_single_query` now distinguishes the list
read from the aggregate read and asserts the aggregates ride in the shared
counts statement.

### WR-07: Retry balance gate existed only in the web handler

**Files modified:** `app/worker/tasks.py`, `tests/test_worker/test_tasks.py`
**Commit:** `4da39de`
**Applied fix:** `retry_send` re-checks `check_balance_cached(session, user_id,
"send")` after the draft/disabled-group checks and before `build_dispatch_task`,
with the same silent return as the other second-line checks. `_run_retry` gained
a `balance_allowed` switch patching `app.worker.tasks.check_balance_cached` (the
pattern already used by the scheduler tests), and a new parametrised test asserts
an exhausted balance dispatches nothing on all three channels and writes no log
row.

### WR-08: `dispatch_send_tasks` dropped an unknown account type silently

**Files modified:** `app/worker/tasks.py`, `tests/test_worker/test_tasks.py`
**Commit:** `593b1dd`
**Applied fix:** The routing loop gained an `else` branch that logs
`dispatch_unknown_account_type` at ERROR and collects the task into `unrouted`;
the function's return type changed from `None` to `int` (tasks actually
dispatched). `retry_send` now checks that number and logs
`retry_send_not_dispatched` instead of asserting a dispatch that did not happen.
New test drives a `DispatchTask(type="signal")` and pins the returned count.

### WR-09: Admin history routes skipped `_clean_choice`

**Files modified:** `app/pages/admin.py`, `app/pages/history.py`, `tests/test_admin.py`
**Commit:** `b508002`
**Applied fix:** `_clean_choice` promoted to `clean_choice` (public, since four
entry points read the same axes) and applied to `status`/`messenger`/`period` in
both `admin_user_history` and `admin_user_history_partial`. Three new
behavioural tests assert that a garbage axis value selects nothing rather than
filtering to an empty screen, and that the raw string does not reach the markup.
**Verified the tests catch the regression:** with `app/pages/admin.py` reverted
they fail (3 failed), with the fix they pass.

### WR-10: `admin.py` imported a private name across a module boundary

**Files modified:** `app/pages/history.py`, `app/pages/admin.py`
**Commit:** `dda968e`
**Applied fix:** `_parse_account_id` renamed to `parse_account_id` at its
definition and all seven call sites; its docstring now records that the public
name is part of the contract because `app/pages/admin.py` calls it across the
module boundary.

### WR-11: No upper time bound on metrics/heatmap windows; stale clamp comment

**Files modified:** `app/application/analytics/send_analytics.py`, `tests/test_application/test_send_analytics.py`
**Commit:** `abbb6b7`
**Applied fix:** `SendLog.sent_at <= now` added to both the `send_metrics`
aggregate query and the `activity_heatmap` stream query (inclusive, matching the
lower bound). The clamp comment was rewritten to say what is now true: with the
local-midnight anchor the upper clamp is unreachable for in-window records, and
both clamps survive as defence in depth against clock skew. Two new tests seed
records at `now`, `now+1s` and `now+2/3 days` and assert only the in-window one
is counted / plotted.

### WR-12: Analytics and retry helper lookups were not user-scoped

**Files modified:** `app/pages/history.py`, `app/application/analytics/send_analytics.py`, `tests/test_pages/test_history_retry.py`
**Commit:** `d070929`
**Applied fix:** `upcoming_sends` adds `Group.user_id == user_id`;
`retry_availability` takes the owner id as a third parameter and adds
`Ad.user_id == user_id` and `MessengerAccount.user_id == user_id`;
`history_retry` re-checks `user_id` on each of the three `db.get(...)` results
and treats a mismatch as "entity gone". All three call sites and six test call
sites were updated. New test
`test_retry_availability_does_not_see_another_users_entities` points a log at a
stranger's ad and asserts the verdict is "Объявление удалено" rather than a
live retry button. Both comments record the SQLite `max(rowid)+1` id-reuse
asymmetry that made the old invariant untestable.

### WR-13: Page size duplicated as a literal in four scroll sentinels

**Files modified:** `app/pages/history.py`, `app/pages/admin.py`, `app/templates/history/list.html`, `app/templates/history/partial_cards.html`, `app/templates/admin/user_history.html`, `app/templates/admin/history_partial_cards.html`
**Commit:** `903c348`
**Applied fix:** All four sentinels now emit `&limit={{ page_size }}`.
`page_size` was added to the two partial contexts (set to the `limit` that
selected *that* batch, so it can never disagree with `next_offset`).
`admin.py` imports `PAGE_SIZE` from `app.pages.history` and uses it for both
`page_size = PAGE_SIZE` and `Query(PAGE_SIZE, ...)`. Sentinels belonging to
other sections (ads, schedules, accounts, groups) were left alone — they are
outside this finding.

### WR-14: List rows carried `ad_text`/`ad_images` no list template renders

**Files modified:** `app/pages/history.py`, `app/pages/admin.py`
**Commit:** `00cc351`
**Applied fix:** Both keys dropped from all four list-row builders
(`history_partial`, `history_list`, `admin_user_history`,
`admin_user_history_partial`) with a comment recording that only the detail
screens render them and that they receive the ORM entity. Verified against
`grep` that no list template touches either key.

### WR-15: A mid-stream export failure produced a truncated file with HTTP 200

**Files modified:** `app/pages/history.py`, `tests/test_pages/test_history_export.py`
**Commit:** `eb3fa24`
**Applied fix:** The export generator wraps the stream loop in `try/except`,
logs `history_export_stream_failed` with `exc_info`, writes a new
`EXPORT_TRUNCATED_MARKER` row ("ВЫГРУЗКА ОБОРВАНА — ФАЙЛ НЕПОЛНЫЙ"), yields it,
and re-raises. `structlog` logger added to the module. The test drives the
route function directly and iterates `response.body_iterator` — going through
the ASGI test client would have been useless here, because an exception inside
a streaming body drops the already-yielded chunks before they reach the client
(observed; the first attempt at this test passed vacuously and was rewritten).
A second test asserts a healthy export carries no marker.

### WR-16: Dead code in `SendLogRepository`

**Files modified:** `app/repositories/send_log.py`
**Commit:** `72e093d`
**Applied fix:** `list_for_user_with_details` deleted (no caller in `app/` or
`tests/`; it also embedded `or "—"` presentation defaults in the data layer) and
the never-passed `status_filter` parameter removed from `list_for_user`. A
comment records both removals and ties them to the same reasoning that removed
`get_stats` from this class.

### WR-17: `retry_availability`'s "account gone" branch is unreachable in production

**Files modified:** `app/pages/history.py`
**Commit:** `06b22e7`
**Applied fix:** Kept as defence in depth (the review's preferred option) with a
comment stating why it is unreachable under FK enforcement (`groups.account_id`
is NOT NULL with `ondelete="CASCADE"`), that SQLite does not enforce FKs by
default, and that after WR-12 the branch also covers a foreign account excluded
by the new owner predicate — a case in which "Аккаунт удалён" is true.

## Notes for the developer

**Requires human confirmation of intent, not correctness** (all are green under
tests, but they change user-visible or contract-level behaviour):

- **WR-02** changes a user-facing Russian string. The wording is mine; the
  invariants it must satisfy are pinned by test, the phrasing is not.
- **WR-03** deliberately biases toward *keeping* the cooldown on an unknown
  broker exception. That is a behaviour change: a user hitting an unrelated
  server error during retry now waits out the minute instead of retrying at
  once. This is the conservative side of an at-least-once delivery guarantee,
  but it is a trade-off worth confirming.
- **WR-06** changes where `sessions_total` / `sessions_online` /
  `nav_counts.accounts` are computed (SQL aggregates instead of `len(sessions)`).
  Numbers are identical below the 100-account cap; above it the list is short
  and the counts are not, which is the intended new behaviour.
- **WR-12** changes `retry_availability`'s signature (third positional
  `user_id`). Any caller added outside this diff must pass it.
- **WR-08** changes `dispatch_send_tasks`'s return type from `None` to `int`.
  Existing callers ignore the value; new ones should not.

**Not attempted (out of `critical_warning` scope):** IN-01 (stale
`heatmap.html` cross-reference), IN-02 (`session.get` guard spelling differs
between the two retry paths), IN-03 (raw `&` in generated hrefs — note WR-13
touched those same four sentinel lines but deliberately did not change `&` to
`&amp;`), IN-04 (bare numeric account id in the export column), IN-05
(`.replace(hour=0, ...)` on a zone-aware datetime, in two places).

---

_Fixed: 2026-08-15T13:35:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

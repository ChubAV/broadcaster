---
phase: 4
slug: dashbord-i-istoriya
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: true
# This phase has NO Wave 0: every test file is authored in-task, in the same task as the code it
# covers (in-task TDD via tdd="true" + <behavior>). true means "no outstanding Wave 0 debt", not
# "a Wave 0 ran" — false would advertise a scaffolding wave that no plan implements.
wave_0_complete: true
created: 2026-08-13
updated: 2026-08-13
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded by `/gsd-plan-phase 4` from `04-RESEARCH.md` § Validation Architecture.
> The Per-Task Verification Map was seeded at requirement level and is now BOUND to real plan and
> task IDs (plans `04-01`…`04-10` exist).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio ≥1.3.0 (strict mode: no config file, every async test carries `@pytest.mark.asyncio`) |
| **Config file** | none — neither `pytest.ini` nor `[tool.pytest.ini_options]` in `pyproject.toml`; fixtures live in `tests/conftest.py` |
| **Quick run command** | `uv run pytest tests/test_application/ tests/test_pages/ -q` (directory-level on purpose: `test_dashboard.py`, `test_history.py`, `test_history_export.py` and `test_history_retry.py` do not exist until the tasks that author them run, and naming a missing path makes pytest exit 4 before collecting anything) |
| **Full suite command** | `just test` (= `uv run pytest tests/ -v`) |
| **Estimated runtime** | ~30 s quick · full suite over 1094 collected tests |
| **Baseline** | **1094 tests collected** (`uv run pytest tests/ -q --collect-only`, research session 2026-08-13) |
| **DB** | `sqlite+aiosqlite:///:memory:`, full schema per test (`tests/conftest.py:38-40`) |
| **Fixtures** | `client`, `authed_client`, `admin_client`, `db_session`, `auth_headers`, `test_settings`, `seed_group` |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_application/ tests/test_pages/ -q` (plus the task's own `<automated>` commands, which name the exact new file)
- **After every plan wave:** Run `uv run pytest tests/test_pages/ tests/test_templates/ tests/test_application/ tests/test_migrations/ -q`
- **Before `/gsd-verify-work`:** `just test` fully green (baseline 1094 + new)
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

Bound to real plan and task IDs (revision 2026-08-13). `Task ID` reads `{plan}·T{n}` — e.g. `04-01·T1` is Task 1 of `04-01-PLAN.md`. `File Exists` describes the state of the test file **before** the phase runs; every ❌ file is authored **inside the task that owns the row** (see § Test Authoring below), not by a separate scaffolding wave.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01·T1 | 04-01 | 1 | DASH-01 | T-04-01 | Four tiles count sends over a rolling 24 h; `account_disconnected` lands in "Errors"; delta computed against the prior day | unit | `uv run pytest tests/test_application/test_send_analytics.py -x` | ❌ authored in 04-01·T1 | ⬜ pending |
| 04-01·T1 | 04-01 | 1 | DASH-01 | T-04-01 | "Groups reached" tile does not double-count `group_id IS NULL` rows and does not crash on them | unit | `uv run pytest tests/test_application/test_send_analytics.py -k groups -x` | ❌ authored in 04-01·T1 | ⬜ pending |
| 04-01·T1 | 04-01 | 1 | DASH-01 | T-04-04 | Dashboard renders the four new tiles and does **not** render the old entity counters | integration | `uv run pytest tests/test_pages/test_dashboard.py -k metrics -x` | ❌ authored in 04-01·T1 | ⬜ pending |
| 04-04·T2 | 04-04 | 2 | DASH-02 | T-04-13, T-04-19 | Upcoming sends sorted by `next_run_at`, never trip `lazy="raise"`, show a reason for draft / detached account / disabled groups | integration | `uv run pytest tests/test_pages/test_dashboard.py -k upcoming -x` | ❌ authored in 04-01·T1, extended in 04-04·T2 | ⬜ pending |
| 04-05·T2 | 04-05 | 3 | DASH-03 | T-04-18 | Page carries `hx-get` + `hx-trigger="every ...s"`; partial returns rows; **polling does not self-stop** (paired test) | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -k feed -x` | ⚠️ file exists, feed tests added in 04-05·T2 | ⬜ pending |
| 04-05·T1 | 04-05 | 3 | DASH-03 | T-04-17, T-04-20 | Feed row is a link to `/history/{id}` (works without JS) | integration | `uv run pytest tests/test_pages/test_dashboard.py -k feed -x` | ⚠️ authored in 04-01·T1, extended in 04-05·T1 | ⬜ pending |
| 04-04·T1 | 04-04 | 2 | DASH-04 | T-04-13, T-04-14 | Heatmap buckets sends by the user's local hour (UTC+3 vs UTC yields different cells); works on SQLite naive datetimes | unit | `uv run pytest tests/test_application/test_send_analytics.py -k heatmap -x` | ⚠️ authored in 04-01·T1, extended in 04-04·T1 | ⬜ pending |
| 04-04·T1 | 04-04 | 2 | DASH-04 | — | 7×24 grid rendered without table elements and without utility classes | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -k heatmap -x` | ⚠️ file exists, extended in 04-04·T1 | ⬜ pending |
| 04-05·T3 | 04-05 | 3 | DASH-05 | T-04-21 | Dashboard shows `sessions_online` from `get_shell_context`; no Docker access anywhere in the dashboard render path | integration | `uv run pytest tests/test_pages/test_shell.py -k sessions -x` | ⚠️ file exists, extended in 04-05·T3 | ⬜ pending |
| 04-06·T1 | 04-06 | 4 | HIST-01 | T-04-23, T-04-24, T-04-25 | Status/channel/period chips change the selection; `today` counted from local midnight; filters survive pagination | integration | `uv run pytest tests/test_pages/test_history.py -k filters -x` | ❌ authored in 04-06·T1 | ⬜ pending |
| 04-01·T2 | 04-01 | 1 | HIST-01 | T-04-01 | Existing guarantee not broken by moving filters into the analytics module | regression | `uv run pytest tests/test_pages/test_htmx_preserved.py::test_infinite_scroll_keeps_filters -x` | ✅ | ⬜ pending |
| 04-06·T2 | 04-06 | 4 | HIST-01 | T-04-22 | Result counter matches the filtered list; empty result explains itself | integration | `uv run pytest tests/test_pages/test_history.py -q` | ⚠️ authored in 04-06·T1, extended in 04-06·T2 | ⬜ pending |
| 04-07·T1 | 04-07 | 5 | HIST-02 | T-04-26 | Error text visible in the list card in full and escaped | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -k error -x` | ✅ (extended in 04-07·T1) | ⬜ pending |
| 04-07·T1 | 04-07 | 5 | HIST-02 | T-04-29, T-04-30 | Copy button does not render without Alpine and does not break the page | integration | `uv run pytest tests/test_pages/test_history.py -k copy -x` | ⚠️ authored in 04-06·T1, extended in 04-07·T1 | ⬜ pending |
| 04-08·T2 | 04-08 | 5 | HIST-03 | T-04-31, T-04-34 | Export returns CSV with BOM, the same filters as the list, and the same row count as the D-31 counter | integration | `uv run pytest tests/test_pages/test_history_export.py -x` | ❌ authored in 04-08·T1 | ⬜ pending |
| 04-08·T2 | 04-08 | 5 | HIST-03 | — | `GET /history/export` is not swallowed by `GET /history/{log_id}` | integration | `uv run pytest tests/test_pages/test_history_export.py -k route_order -x` | ❌ authored in 04-08·T1 | ⬜ pending |
| 04-08·T2 | 04-08 | 5 | HIST-03 | T-04-32, T-04-33 | Exceeding the cap yields an explanation, not a truncated file | integration | `uv run pytest tests/test_pages/test_history_export.py -k cap -x` | ❌ authored in 04-08·T1 | ⬜ pending |
| 04-08·T1 | 04-08 | 5 | HIST-03 | T-04-16 (CSV formula injection) | A field starting with `=`/`+`/`-`/`@` is escaped | unit | `uv run pytest tests/test_pages/test_history_export.py -k formula -x` | ❌ authored in 04-08·T1 | ⬜ pending |
| 04-09·T1, 04-09·T2 | 04-09 | 6 | HIST-04 | — | Retry button does not render for `ok`; POST against an `ok` record is rejected server-side | integration | `uv run pytest tests/test_pages/test_history_retry.py -k eligible -x` | ❌ authored in 04-09·T1 | ⬜ pending |
| 04-09·T1 | 04-09 | 6 | HIST-04 | T-04-35 (ownership) | Retrying another user's record is rejected (ownership checked at the entry point) | integration | `uv run pytest tests/test_pages/test_history_retry.py -k ownership -x` | ❌ authored in 04-09·T1 | ⬜ pending |
| 04-09·T1 | 04-09 | 6 | HIST-04 | **T-04-38 (CSRF)** | A retry request whose declared source is another site is rejected with 403 before any side effect; a same-origin request and a header-less request pass | integration | `uv run pytest tests/test_pages/test_history_retry.py -k origin -x` | ❌ authored in 04-09·T1 | ⬜ pending |
| 04-09·T1 | 04-09 | 6 | HIST-04 | T-04-39 | With ad/group/account missing, the task is **not** queued and no journal row is written (D-21) | integration | `uv run pytest tests/test_pages/test_history_retry.py -k precheck -x` | ❌ authored in 04-09·T1 | ⬜ pending |
| 04-03·T2 | 04-03 | 1 | HIST-04 | T-04-09, T-04-10 | Retrying a WA record routes to the Redis queue, not the Celery `telegram` queue | unit | `uv run pytest tests/test_worker/test_tasks.py -k retry -x` | ⚠️ file exists, extended in 04-03·T2 | ⬜ pending |
| 04-09·T1 | 04-09 | 6 | HIST-04 | T-04-36 (balance-gate bypass) | Exhausted balance rejects the retry before it reaches the queue | integration | `uv run pytest tests/test_pages/test_history_retry.py -k balance -x` | ❌ authored in 04-09·T1 | ⬜ pending |
| 04-03·T1 | 04-03 | 1 | HIST-04 | T-04-08, T-04-11 | One definition of dispatch-task assembly; retry re-checks ownership inside the task and writes no journal row for an impossible send | unit | `uv run pytest tests/test_application/ tests/test_worker/ -q` | ✅ (extended in 04-03·T1) | ⬜ pending |
| 04-02·T1, 04-02·T2 | 04-02 | 1 | D-36 | T-04-05, T-04-06, T-04-07 | Revision 0016 creates the index, downgrade drops it, history stays a single line | unit | `uv run pytest tests/test_migrations/test_0016_send_logs_user_sent_at.py -x` | ❌ authored in 04-02·T1 (RED, before the revision exists) | ⬜ pending |
| 04-09·T2 | 04-09 | 6 | cross-cutting | — | Inventories (modals, components, utility classes) reconcile after edits — recounted from files, never forecast | regression | `uv run pytest tests/test_templates/test_components.py tests/test_pages/test_responsive_markup.py -q` | ✅ (constants updated in 04-09·T2) | ⬜ pending |
| 04-01·T1, 04-04·T1 | 04-01, 04-04 | 1, 2 | cross-cutting | — | Responsiveness: dashboard and history free of utility classes, free of tables, inheriting the shell | regression | `uv run pytest tests/test_pages/test_responsive_markup.py -q` | ✅ | ⬜ pending |
| 04-10·T1 | 04-10 | 7 | cross-cutting | T-04-41 | The journal summary has ONE definition: the JSON API counts three statuses through the analytics module | integration | `uv run pytest tests/test_routes/test_history.py tests/test_e2e.py -q` | ✅ (assertions updated in 04-10·T1) | ⬜ pending |
| 04-10·T2 | 04-10 | 7 | cross-cutting | T-04-42 | Whole suite green at ≥ 1094 collected; phase security report written with accepted risks, residuals, and the separate-task recommendation | regression | `just test` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*`File Exists` legend: ✅ exists today · ⚠️ exists today but the row's assertions are added by the named task · ❌ does not exist today, created by the named task.*

---

## Test Authoring — in-task, no Wave 0

**This phase has no Wave 0 and needs none.** Every plan that produces code produces its tests in
the *same* task, via in-task TDD (`tdd="true"` + a `<behavior>` block listing the expected cases
before the `<action>` describes the implementation). A separate scaffolding wave would buy
nothing here: there is no test framework to install (pytest 9.0.2 and pytest-asyncio are already
in `pyproject.toml:38-39`), no harness to stand up, and no cross-plan test contract to agree on
in advance. It would only add a wave in which nothing is observable.

Consequence for the map above: no row depends on a wave that does not exist. Each ❌ / ⚠️ row
names the task that authors or extends its file, and that task's own `<verify>` runs it.

| Test file | Authored / extended by | Covers | Note |
|-----------|------------------------|--------|------|
| `tests/test_application/test_send_analytics.py` | created 04-01·T1; extended 04-01·T2, 04-04·T1, 04-04·T2 | DASH-01, DASH-02, DASH-04, HIST-01 | windows, three statuses, timezone, naive dates |
| `tests/test_pages/test_dashboard.py` | created 04-01·T1; extended 04-04·T2, 04-04·T3, 04-05·T1 | DASH-01, DASH-02, DASH-03 | the dashboard has no test file of its own today |
| `tests/test_pages/test_history.py` | created 04-06·T1; extended 04-06·T2, 04-07·T1, 04-07·T2 | HIST-01, HIST-02 | history assertions are smeared across `test_responsive_markup.py` and `test_htmx_preserved.py` today |
| `tests/test_pages/test_history_export.py` | created 04-08·T1; extended 04-08·T2 | HIST-03 | row composition first, then route + cap |
| `tests/test_pages/test_history_retry.py` | created 04-09·T1; extended 04-09·T2 | HIST-04 | eligibility, ownership, **request origin (T-04-38)**, precheck, balance, single dispatch |
| `tests/test_migrations/test_0016_send_logs_user_sent_at.py` | created 04-02·T1 (RED, before the revision exists) | D-36 | scaffold copied from `tests/test_migrations/test_0013_ad_status.py` — file-backed SQLite, synchronous test, stamp the starting revision |
| `tests/test_application/test_scheduling_use_cases.py` | extended 04-03·T1 | HIST-04 | one definition of dispatch-task assembly |
| `tests/test_worker/test_tasks.py` | extended 04-03·T2 | HIST-04 | **not** `tests/test_worker_tasks.py` — both files exist in this repo, and the flat one collects zero retry tests |
| `tests/test_pages/test_shell.py` | extended 04-05·T3 | DASH-05 | no second source of the online-worker count |
| `tests/test_pages/test_htmx_preserved.py` | extended 04-05·T2 | DASH-03 | **paired** tests for indefinite feed polling |
| `tests/test_pages/test_responsive_markup.py` | extended 04-01·T1, 04-04·T1, 04-05·T2, 04-07·T1, 04-09·T2 | cross-cutting | includes `len(components)` (`:1881`) |
| `tests/test_templates/test_components.py` | updated 04-09·T2 | cross-cutting | constants `MODAL_IMPORTERS` / `MODAL_EVENT_NAMES` / `MODAL_PLACES` (`:799-801`) — recounted from files, never forecast |
| `tests/test_routes/test_history.py`, `tests/test_e2e.py` | updated 04-10·T1 | cross-cutting | summary semantics shift to three statuses |

*No framework install required.*

---

## Manual-Only Verifications

Each row is declared in a plan as a `verification: backstop` truth and lands in a numbered item of
the blocking checkpoint `04-10·T3`. Ten backstop markers across the plans reduce to six distinct
behaviors, and none is left without a human step.

| Behavior | Requirement | Declared in | Why Manual | Where verified |
|----------|-------------|-------------|------------|----------------|
| Polling really keeps ticking indefinitely in an open tab | DASH-03 | 04-05, 04-10 | No browser/e2e tests exist in the project (`STATE.md:88`) | `04-10·T3` item 1 — open the dashboard, leave the tab open past five poll intervals, confirm the feed keeps refreshing |
| The retry confirmation panel prevents a double send with Alpine live | HIST-04 | 04-09, 04-10 | Alpine runtime is hand-verified | `04-10·T3` item 2 — open a failed record, trigger retry, double-click confirm, confirm one send |
| CSV opens in a spreadsheet without mojibake and in separate columns | HIST-03 | 04-08, 04-10 | Excel is not available in the environment | `04-10·T3` item 3 — export a filtered result and open it |
| The DB session survives the export stream on the production stack | HIST-03 | 04-08, 04-10 | `tests/conftest.py:54` overrides `get_db` with a non-generator, so the suite cannot exercise the FastAPI exit-stack boundary | `04-10·T3` item 4 — run the export against the real stack with a result large enough to stream |
| Dashboard and history are usable at mobile widths | cross-cutting | 04-10 | Rendered layout at real widths is not measurable from markup assertions | `04-10·T3` item 5 — 320 / 860 / 900 / 1080 px |
| Revision 0016 does not create a noticeable write-lock window on the production DB | D-36 | 04-02 | No production PostgreSQL in this environment; `send_logs` size is unmeasurable here | `04-10·T3` closing paragraph — rollout window is the owner's decision, the phase does not apply revisions |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify — all 22 executable tasks across `04-01`…`04-10` carry a `<verify>` block with at least one `<automated>` command; the only task without one is `04-10·T3`, a blocking human checkpoint
- [x] No `MISSING —` placeholder in any plan, therefore no Wave 0 dependency to satisfy
- [x] Every test file that does not exist today is authored by a named task (§ Test Authoring), and that task's own `<verify>` runs it
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] No watch-mode flags
- [x] Feedback latency < 30 s for the quick command
- [x] `nyquist_compliant: true` set in frontmatter
- [ ] Reconciled by `/gsd-validate-phase` after execution — flips `status: draft` → `validated` and fills the Status column with real results

**Approval:** pending — the boxes above are authoring-time facts about the plans; execution results are still ⬜.

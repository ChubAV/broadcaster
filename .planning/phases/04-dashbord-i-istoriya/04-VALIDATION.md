---
phase: 4
slug: dashbord-i-istoriya
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-13
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded by `/gsd-plan-phase 4` from `04-RESEARCH.md` § Validation Architecture.
> The Per-Task Verification Map is seeded at requirement level; task IDs are bound by `/gsd-validate-phase` once plans exist.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio ≥1.3.0 (strict mode: no config file, every async test carries `@pytest.mark.asyncio`) |
| **Config file** | none — neither `pytest.ini` nor `[tool.pytest.ini_options]` in `pyproject.toml`; fixtures live in `tests/conftest.py` |
| **Quick run command** | `uv run pytest tests/test_application/ tests/test_pages/test_dashboard.py tests/test_pages/test_history.py -q` |
| **Full suite command** | `just test` (= `uv run pytest tests/ -v`) |
| **Estimated runtime** | ~30 s quick · full suite over 1094 collected tests |
| **Baseline** | **1094 tests collected** (`uv run pytest tests/ -q --collect-only`, research session 2026-08-13) |
| **DB** | `sqlite+aiosqlite:///:memory:`, full schema per test (`tests/conftest.py:38-40`) |
| **Fixtures** | `client`, `authed_client`, `admin_client`, `db_session`, `auth_headers`, `test_settings`, `seed_group` |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_application/ tests/test_pages/test_dashboard.py tests/test_pages/test_history.py -q`
- **After every plan wave:** Run `uv run pytest tests/test_pages/ tests/test_templates/ tests/test_application/ tests/test_migrations/ -q`
- **Before `/gsd-verify-work`:** `just test` fully green (baseline 1094 + new)
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

Seeded at requirement level. `Task ID` / `Plan` / `Wave` / `Threat Ref` are bound by `/gsd-validate-phase` after plans exist.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | DASH-01 | — | Four tiles count sends over a rolling 24 h; `account_disconnected` lands in "Errors"; delta computed against the prior day | unit | `uv run pytest tests/test_application/test_send_analytics.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DASH-01 | — | "Groups reached" tile does not double-count `group_id IS NULL` rows and does not crash on them | unit | `uv run pytest tests/test_application/test_send_analytics.py -k groups -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DASH-01 | — | Dashboard renders the four new tiles and does **not** render the old entity counters | integration | `uv run pytest tests/test_pages/test_dashboard.py -k metrics -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DASH-02 | — | Upcoming sends sorted by `next_run_at`, never trip `lazy="raise"`, show a reason for draft / detached account / disabled groups | integration | `uv run pytest tests/test_pages/test_dashboard.py -k upcoming -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DASH-03 | — | Page carries `hx-get` + `hx-trigger="every ...s"`; partial returns rows; **polling does not self-stop** (paired test) | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -k feed -x` | ⚠️ file exists, no feed tests | ⬜ pending |
| TBD | TBD | TBD | DASH-03 | — | Feed row is a link to `/history/{id}` (works without JS) | integration | `uv run pytest tests/test_pages/test_dashboard.py -k feed_row -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DASH-04 | — | Heatmap buckets sends by the user's local hour (UTC+3 vs UTC yields different cells); works on SQLite naive datetimes | unit | `uv run pytest tests/test_application/test_send_analytics.py -k heatmap -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DASH-04 | — | 7×24 grid rendered without table elements and without utility classes | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -k heatmap -x` | ⚠️ file exists | ⬜ pending |
| TBD | TBD | TBD | DASH-05 | — | Dashboard shows `sessions_online` from `get_shell_context`; no Docker access anywhere in the dashboard render path | integration | `uv run pytest tests/test_pages/test_shell.py -k sessions -x` | ⚠️ file exists | ⬜ pending |
| TBD | TBD | TBD | HIST-01 | — | Status/channel/period chips change the selection; `today` counted from local midnight; filters survive pagination | integration | `uv run pytest tests/test_pages/test_history.py -k filters -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-01 | — | Existing guarantee not broken by moving filters into the analytics module | regression | `uv run pytest tests/test_pages/test_htmx_preserved.py::test_infinite_scroll_keeps_filters -x` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HIST-02 | — | Error text visible in the list card in full and escaped | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -k error_text -x` | ✅ (extend) | ⬜ pending |
| TBD | TBD | TBD | HIST-02 | — | Copy button does not render without Alpine and does not break the page | integration | `uv run pytest tests/test_pages/test_history.py -k copy_degrades -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-03 | — | Export returns CSV with BOM, the same filters as the list, and the same row count as the D-31 counter | integration | `uv run pytest tests/test_pages/test_history_export.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-03 | — | `GET /history/export` is not swallowed by `GET /history/{log_id}` | integration | `uv run pytest tests/test_pages/test_history_export.py -k route_order -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-03 | — | Exceeding the cap yields an explanation, not a truncated file | integration | `uv run pytest tests/test_pages/test_history_export.py -k cap -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-03 | CSV formula injection | A field starting with `=`/`+`/`-`/`@` is escaped | unit | `uv run pytest tests/test_pages/test_history_export.py -k formula -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-04 | — | Retry button does not render for `ok`; POST against an `ok` record is rejected server-side | integration | `uv run pytest tests/test_pages/test_history_retry.py -k eligible -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-04 | ownership | Retrying another user's record is rejected (ownership checked at the entry point) | integration | `uv run pytest tests/test_pages/test_history_retry.py -k ownership -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-04 | — | With ad/group/account missing, the task is **not** queued and no journal row is written (D-21) | integration | `uv run pytest tests/test_pages/test_history_retry.py -k precheck -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HIST-04 | — | Retrying a WA record routes to the Redis queue, not the Celery `telegram` queue | unit | `uv run pytest tests/test_worker_tasks.py -k retry -x` | ⚠️ file exists | ⬜ pending |
| TBD | TBD | TBD | HIST-04 | balance-gate bypass | Exhausted balance rejects the retry before it reaches the queue | integration | `uv run pytest tests/test_pages/test_history_retry.py -k balance -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-36 | — | Revision 0016 creates the index, downgrade drops it, history stays a single line | unit | `uv run pytest tests/test_migrations/test_0016_send_logs_user_sent_at.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | cross-cutting | — | Inventories (modals, components, utility classes) reconcile after edits | regression | `uv run pytest tests/test_templates/test_components.py tests/test_pages/test_responsive_markup.py -q` | ✅ (update constants) | ⬜ pending |
| TBD | TBD | TBD | cross-cutting | — | Responsiveness: dashboard and history free of utility classes, free of tables, inheriting the shell | regression | `uv run pytest tests/test_pages/test_responsive_markup.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_application/test_send_analytics.py` — covers DASH-01, DASH-04 (windows, three statuses, timezone, naive dates)
- [ ] `tests/test_pages/test_dashboard.py` — covers DASH-01, DASH-02, DASH-03 (whole page; the dashboard has no test file of its own today)
- [ ] `tests/test_pages/test_history.py` — covers HIST-01, HIST-02 (history tests are currently smeared across `test_responsive_markup.py` and `test_htmx_preserved.py`)
- [ ] `tests/test_pages/test_history_export.py` — covers HIST-03 in full
- [ ] `tests/test_pages/test_history_retry.py` — covers HIST-04 in full
- [ ] `tests/test_migrations/test_0016_send_logs_user_sent_at.py` — covers D-36; scaffold copied from `tests/test_migrations/test_0013_ad_status.py` (file-backed SQLite, synchronous test, stamp the starting revision)
- [ ] Extend `tests/test_pages/test_htmx_preserved.py` — **paired** tests for indefinite feed polling
- [ ] Update constants `MODAL_IMPORTERS` / `MODAL_EVENT_NAMES` / `MODAL_PLACES` (`tests/test_templates/test_components.py:799-801`) and `len(components)` (`tests/test_pages/test_responsive_markup.py:1881`)

*No framework install required: pytest and pytest-asyncio are already in `pyproject.toml:38-39`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Polling really keeps ticking indefinitely in an open tab | DASH-03 | No browser/e2e tests exist in the project (`STATE.md:88`) | Open the dashboard, leave the tab open past several poll intervals, confirm the feed keeps refreshing and never stops |
| The retry confirmation panel prevents a double send with Alpine live | HIST-04 | Same — Alpine runtime is hand-verified | Open a failed record, trigger retry, double-click the confirm control, confirm only one send is dispatched |
| CSV opens in Excel without mojibake and as a single column | HIST-03 | Excel is not available in the environment | Export a filtered result, open the file in Excel, confirm Cyrillic renders and fields land in separate columns |
| The DB session survives the export stream on the production stack | HIST-03 | `tests/conftest.py:54` overrides `get_db` with a non-generator, so the suite cannot exercise the FastAPI exit-stack boundary | Run the export against the real stack (FastAPI ≥0.129.0) with a result large enough to stream, confirm no closed-session error |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

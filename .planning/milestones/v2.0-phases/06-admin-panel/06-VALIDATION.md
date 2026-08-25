---
phase: 6
slug: admin-panel
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-21
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded by plan-phase from `06-RESEARCH.md` § Validation Architecture.
> Per-task rows are filled once PLAN.md task IDs exist (validate-phase §6).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 [VERIFIED: pyproject.toml:36-37] |
| **Config file** | `pyproject.toml` (`[dependency-groups] dev`); suite DB is `sqlite+aiosqlite:///:memory:`, schema created per test [VERIFIED: tests/conftest.py:41-52] |
| **Quick run command** | `uv run pytest tests/test_pages/test_admin_panel.py tests/test_services/ -x -q` |
| **Full suite command** | `just test` (`uv run pytest tests/ -v`) |
| **Estimated runtime** | ~60-120 seconds (895+ tests as of Phase 2) |
| **Existing fixtures** | `client`, `db_session`, `auth_headers`, `authed_client`, `expired_client`, `comped_client`, `admin_client` [VERIFIED: tests/conftest.py:245-262]; helper `seed_group` |
| **Test doubles** | `unittest.mock.patch` on a named module-level accessor — no new dev dependencies. Docker: `_get_docker_client`; Redis: `_get_redis`; Loki: `_client`. New services MUST expose a lazy named client accessor for this reason. |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_pages/test_admin_panel.py tests/test_services/ -x -q`
- **After every plan wave:** `just test`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

> Populated by validate-phase §6 once PLAN.md task IDs are assigned.
> The requirement→behavior→command mapping below is lifted from `06-RESEARCH.md`
> § Validation Architecture → "Phase Requirements → Test Map" and is authoritative
> for which automated command proves which requirement.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 0 | ADMIN-03 | — | six subsection routes answer 200 to admin, 403 to non-admin | unit | `pytest tests/test_pages/test_admin_panel.py -k tabs -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-03 | — | tabs are links; work without JS | unit | `pytest tests/test_pages/test_admin_panel.py -k degrades -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-03 | — | Overview calls the analytics module, not its own SELECT (AST) | unit | `pytest tests/test_application/test_admin_uses_analytics.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-04 | — | filters+count+page in one expression; "N of M" matches contents | unit | `pytest tests/test_pages/test_admin_users.py -k count -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-04 | — | Cyrillic search (Pitfall 6) | unit | `pytest tests/test_pages/test_admin_users.py -k search -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-05 | T-06-BLOCK | blocking closes BOTH entry paths and the broadcast path | integration | `pytest tests/test_pages/test_blocked_user.py -x` | ❌ W0 (rewrites tests/test_admin.py:541) | ⬜ pending |
| TBD | TBD | 0 | ADMIN-05 | — | `get_current_user_id` still has no `db` param (AST) — regression guard | unit | `pytest tests/test_pages/test_access_gate.py -k untouched -x` | ✅ exists | ⬜ pending |
| TBD | TBD | 0 | ADMIN-06 | T-06-IMP | login-as-user, `check_is_admin` via `act`, return path | integration | `pytest tests/test_pages/test_impersonation.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-06 | — | token WITHOUT `act` yields byte-identical prior payload (D-21) | unit | `pytest tests/test_services/test_auth_token.py -k without_act -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-06 | — | login-as a BLOCKED user is permitted (D-26) | integration | `pytest tests/test_pages/test_impersonation.py -k blocked -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-06 | T-06-IMP | machine gate: a mutating route missing the dependency turns red | unit | `pytest tests/test_pages/test_impersonation_gate.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-07 | — | "no heartbeat + empty queue" = "idle", not "offline" | unit | `pytest tests/test_services/test_ops_state.py -k idle -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-07 | — | stale TTL-less heartbeat reads as dead (Ф-6) | unit | `pytest tests/test_services/test_ops_state.py -k stale -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-07 | — | no subsection handler calls the Docker SDK (AST/grep over app/pages/) | unit | `pytest tests/test_pages/test_admin_panel.py -k no_docker_on_render -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-08 | — | `_delay_until` parsed per channel: ms for wa, s for max (Ф-7) | unit | `pytest tests/test_application/test_queue_rows.py -k delay -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-08 | — | fresh task without `_retry_count`/`_delay_until` renders "waiting" | unit | `pytest tests/test_application/test_queue_rows.py -k fresh -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-08 | — | `LREM` removes exactly one task | unit | `pytest tests/test_services/test_ops_state.py -k drop -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-09 | — | unreachable Loki → banner, NOT an empty list | unit | `pytest tests/test_services/test_loki_client.py -k unavailable -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-09 | — | WARN chip covers both `warn` and `warning` (Ф-8) | unit | `pytest tests/test_services/test_loki_client.py -k level -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-09 | — | hitting the 200 cap is named, not silently truncated | unit | `pytest tests/test_services/test_loki_client.py -k capped -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-10 | — | MRR excludes comped users (D-38) | unit | `pytest tests/test_application/test_admin_payments.py -k mrr -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-10 | — | `plan` never appears in the ledger markup (D-42) | unit | `pytest tests/test_pages/test_admin_payments.py -k no_plan -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-11 | — | each of the five signals both raises AND clears on its clear condition (D-44) | unit | `pytest tests/test_application/test_incidents.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | ADMIN-11 | — | stuck-payment age measured from `created_at`, not `confirmed_at` | unit | `pytest tests/test_application/test_incidents.py -k payment -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | CR-02 | T-06-RND | reset code sourced from `secrets`, not `random` — SOURCE assertion (AST) | unit | `pytest tests/test_pages/test_reset_code_source.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | CR-03 | T-06-COOK | `secure` read from settings; login still works in HTTP mode (Ф-9) | unit | `pytest tests/test_pages/test_cookie_flags.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | D-05 | — | no template and no route references `groups-info` | unit | `pytest tests/test_pages/test_admin_panel.py -k groups_info_gone -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pages/test_admin_panel.py` — six-subsection shell, ADMIN-03
- [ ] `tests/test_pages/test_admin_users.py` — ADMIN-04
- [ ] `tests/test_pages/test_blocked_user.py` — ADMIN-05 / CR-01; **replaces** `tests/test_admin.py:541`, whose name asserts more than its body checks
- [ ] `tests/test_pages/test_impersonation.py` + `tests/test_pages/test_impersonation_gate.py` — ADMIN-06 / D-23
- [ ] `tests/test_services/test_ops_state.py` — ADMIN-07 / ADMIN-08
- [ ] `tests/test_services/test_loki_client.py` — ADMIN-09
- [ ] `tests/test_application/test_queue_rows.py`, `test_incidents.py`, `test_admin_payments.py` — ADMIN-08 / ADMIN-10 / ADMIN-11
- [ ] `tests/test_pages/test_cookie_flags.py`, `tests/test_pages/test_reset_code_source.py` — CR-02 / CR-03
- [ ] Redis and Loki test doubles — `unittest.mock.patch` on named module accessors (no new packages)

*Framework install NOT required: `pytest`, `pytest-asyncio`, `aiosqlite` are already in the dev group.*

---

## Manual-Only Verifications

Redis and Loki are unavailable in the development environment. This does not block planning or
execution (the whole suite runs on in-memory SQLite with no external services), but the following
are provable only by a human on a live stand and MUST become UAT items.

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| A worker row genuinely shows "простаивает" against a live Redis | ADMIN-07 | Redis not available in dev env; heartbeat freshness is a live-state property | Start the stand, stop a WA worker without graceful shutdown, wait > 90s, open Воркеры |
| The unreachable-Loki banner renders | ADMIN-09 | Loki not available in dev env | Start the stand with Loki down, open Логи, confirm the banner (not an empty list) |
| All six subsections are usable at 375px | ADMIN-03 | Visual/responsive property; no automated viewport harness in the suite | Open each subsection at 375px width, confirm no horizontal overflow and reachable controls |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 1
slug: interfeysnyy-fundament
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-09
planner_filled: 2026-08-09
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from `01-RESEARCH.md` § Validation Architecture. Per-task rows are filled by the planner.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-cov 7.0.0 (already in dev group — no install needed) |
| **Config file** | none — no `pytest.ini` / `setup.cfg` / `[tool.pytest.ini_options]`. Async mode is therefore **strict**: every async test needs `@pytest.mark.asyncio` |
| **Quick run command** | `uv run pytest tests/test_pages/ -q` |
| **Full suite command** | `just test` (`uv run pytest tests/ -v`, 393 tests) |
| **Estimated runtime** | ~16 seconds quick · full suite longer |
| **Baseline** | green — 27 passed in `tests/test_pages/`, 393 collected without errors |

**Fixture trap.** `auth_headers` returns a Bearer header (`tests/conftest.py:67`), but page routes authenticate by
httpOnly cookie (`request.cookies.get("access_token")`, `app/pages/common.py:67`). HTML page tests must take
`auth_headers` (which creates the user), then POST `/login` to set the cookie, then GET. Pattern established in
`tests/test_pages/test_profile.py:29-42`.

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_pages/ -q`
- **After every plan wave:** Run `just test`
- **After every plan:** Run `just test` — D-07 requires the app to stay working after each plan, so the full
  suite runs at plan boundaries, not only at phase exit
- **Before `/gsd-verify-work`:** Full suite green + manual visual pass
- **Max feedback latency:** ~16 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | UI-01 | T-01-04 | Worker read never touches Docker SDK from the request path | checkpoint | _decision gate — no automated check_ | n/a | ⬜ pending |
| 01-01-T2 | 01 | 1 | UI-01, UI-02, UI-03, UI-06 | T-01-01, T-01-02, T-01-04 | StaticFiles only; admin nav stays behind the permission check; no blocking Docker call | integration | `uv run pytest tests/test_pages/test_shell.py -x -q` | ❌ W0 → created here | ⬜ pending |
| 01-01-T3 | 01 | 1 | UI-01 | T-01-05 | Fonts self-hosted; no third-party font request remains | integration | `uv run pytest tests/test_pages/test_shell.py -x -q` | ✅ after T2 | ⬜ pending |
| 01-02-T1 | 02 | 2 | UI-01, UI-04 | T-02-01 | Macros take text/number/bool only; escaping invariant intact | unit | `uv run pytest tests/test_templates/test_components.py -x -q` | ❌ W0 → created here | ⬜ pending |
| 01-02-T2 | 02 | 2 | UI-04 | T-02-04 | Modal replaces the confirm dialog, not the POST form | unit | `uv run pytest tests/test_templates/test_components.py -x -q` | ✅ after T1 | ⬜ pending |
| 01-02-T3 | 02 | 2 | UI-02, UI-04 | T-02-02, T-02-03 | Form `name`/`method`/`action` preserved; auth shell renders no nav | integration | `uv run pytest tests/test_pages/test_registration.py tests/test_pages/test_password_reset.py -q` | ✅ | ⬜ pending |
| 01-03-T1 | 03 | 3 | UI-05 | T-03-03 | Polling self-terminates; paired test prevents vacuous green | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -x -q` | ❌ W0 → created here | ⬜ pending |
| 01-03-T2 | 03 | 3 | UI-05, UI-06 | T-03-04 | Branch collapsed before file deletion; layout param stays accepted | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -x -q` | ✅ after T1 | ⬜ pending |
| 01-03-T3 | 03 | 3 | UI-04, UI-05, UI-06 | T-03-01, T-03-02 | Delete route/method unchanged; ad title escaped | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ❌ W0 → created here | ⬜ pending |
| 01-04-T1 | 04 | 4 | UI-04, UI-05, UI-06 | T-04-03, T-04-04 | Toggle routes unchanged; owner filter untouched | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ✅ | ⬜ pending |
| 01-04-T2 | 04 | 4 | UI-04 | T-04-03 | Schedule form field contract preserved | integration | `uv run pytest tests/test_pages/ -q` | ✅ | ⬜ pending |
| 01-04-T3 | 04 | 4 | UI-04, UI-05, UI-06 | T-04-01, T-04-02 | Filter loop carried verbatim; group names escaped | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -x -q` | ✅ | ⬜ pending |
| 01-05-T1 | 05 | 5 | UI-05, UI-06 | T-05-03 | Filter params escaped into the sentinel URL | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ✅ | ⬜ pending |
| 01-05-T2 | 05 | 5 | UI-04 | T-05-01, T-05-02 | Error text shown in full under autoescape; owner check intact | integration | `uv run pytest tests/test_pages/ -q` | ✅ | ⬜ pending |
| 01-05-T3 | 05 | 5 | UI-02, UI-04 | T-05-04 | Profile form contract preserved | integration | `uv run pytest tests/test_pages/test_profile.py -x -q` | ✅ | ⬜ pending |
| 01-06-T1 | 06 | 6 | UI-04, UI-05, UI-06 | T-06-04, T-06-05 | Swap anchor stays on the request-bearing element | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -x -q` | ✅ | ⬜ pending |
| 01-06-T2 | 06 | 6 | UI-05 | T-06-01 | Conditional HTMX attributes preserved — polling still stops | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -x -q` | ✅ | ⬜ pending |
| 01-06-T3 | 06 | 6 | UI-04, UI-05 | T-06-02, T-06-03 | Connect-wizard field contract and secret exposure unchanged | integration | `uv run pytest tests/test_pages/ -q` | ✅ | ⬜ pending |
| 01-07-T1 | 07 | 7 | UI-04, UI-06 | T-07-04 | Billing owner filter untouched; table → row primitives | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ✅ | ⬜ pending |
| 01-07-T2 | 07 | 7 | UI-04, UI-06 | T-07-01, T-07-02 | Admin permission check not weakened; PII columns unchanged | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ✅ | ⬜ pending |
| 01-07-T3 | 07 | 7 | UI-04, UI-06 | T-07-03 | External group names escaped | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ✅ | ⬜ pending |
| 01-08-T1 | 08 | 8 | UI-04, UI-06 | T-08-01, T-08-02 | Admin detail pages denied to regular users; PII set unchanged | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | ✅ | ⬜ pending |
| 01-08-T2 | 08 | 8 | UI-04, UI-05, UI-06 | T-08-03 | Last live scroll chain intact; error text escaped | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -x -q` | ✅ | ⬜ pending |
| 01-08-T3 | 08 | 8 | UI-01…UI-06 | T-08-04, T-08-05 | No external CDN anywhere; static links versioned | integration | `just test` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → test map (from research)

| Req ID | Behavior | Test Type | Automated Command | File Exists |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | `/static/css/app.css` served, contains `:root`, contains no tailwind | unit | `uv run pytest tests/test_pages/test_shell.py::test_app_css_served -x` | ❌ W0 |
| UI-01 | No page loads an external CDN (`cdn.tailwindcss.com`, `unpkg.com`, `fonts.googleapis.com`) | integration | `uv run pytest tests/test_pages/test_shell.py::test_no_external_cdn -x` | ❌ W0 |
| UI-02 | All static GET pages render in the new shell (`data-shell`) | integration | `uv run pytest tests/test_pages/test_shell.py::test_all_pages_render_new_shell -x` | ❌ W0 |
| UI-02 | 7 auth screens render in the auth shell and contain no `data-side` | integration | `uv run pytest tests/test_pages/test_shell.py::test_auth_shell -x` | ❌ W0 |
| UI-03 | Active section highlighted on every page | integration | `uv run pytest tests/test_pages/test_shell.py::test_active_nav_highlight -x` | ❌ W0 |
| UI-04 | Components render from `components/` macros | unit | `uv run pytest tests/test_templates/test_components.py -x` | ❌ W0 |
| UI-04 | No `\|safe` introduced in templates | unit | `uv run pytest tests/test_templates/test_components.py::test_no_unsafe_escaping -x` | ❌ W0 |
| UI-05 | Infinite scroll: second partial carries the next sentinel with a larger `offset` | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py::test_infinite_scroll_chain -x` | ❌ W0 |
| UI-05 | Sync-status polling stops when `status != 'syncing'` | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py::test_sync_polling_stops -x` | ❌ W0 |
| UI-05 | Swap anchors preserved (`id="account-row-…"`, `id="wa-status"`, `id="max-status"`) | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py::test_swap_anchors_present -x` | ❌ W0 |
| UI-06 | Lists carry responsive primitives (`data-row`/`data-hrow`) and no paired rows/cards | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x` | ❌ W0 |
| UI-06 | Mobile tabs present in shell markup | integration | `uv run pytest tests/test_pages/test_shell.py::test_mobile_tabs_present -x` | ❌ W0 |
| regression | Existing 393 tests stay green | full | `just test` | ✅ |

**Smoke-test routes.** 38 page GET routes exist. Parameter-free routes suitable for a parametrized smoke test:
`/`, `/dashboard`, `/ads`, `/ads/new`, `/ads/partial`, `/accounts`, `/accounts/partial`,
`/accounts/connect/tg_user`, `/accounts/connect/wa`, `/accounts/connect/max`, `/groups`, `/groups/partial`,
`/schedules`, `/schedules/new`, `/schedules/partial`, `/history`, `/history/partial`, `/billing`, `/profile`,
`/admin`, `/admin/users`, `/admin/groups-info`, `/login`, `/register`, `/forgot-password`.
Parametrized routes need data fixtures and should be covered pointwise.

**Auth-screen coverage limit.** Only 3 of the 7 auth templates have a GET route (`/login`, `/register`,
`/forgot-password`). The other four (`register_verify`, `register_complete`, `forgot_password_verify`,
`forgot_password_reset`) render only from POST handlers, so a GET smoke test cannot reach them. Existing
`tests/test_pages/test_registration.py` and `test_password_reset.py` already drive those flows end-to-end —
they are the safety net for D-08 and must not be broken.

---

## Wave 0 Requirements

- [ ] `tests/test_pages/test_shell.py` — covers UI-01, UI-02, UI-03, UI-06 (tabs)
- [ ] `tests/test_pages/test_htmx_preserved.py` — covers UI-05 (chain, polling, anchors)
- [ ] `tests/test_pages/test_responsive_markup.py` — covers UI-06
- [ ] `tests/test_templates/test_components.py` + `tests/test_templates/__init__.py` — covers UI-04
- [ ] `authed_client` fixture in `tests/conftest.py` — encapsulates `auth_headers` → POST `/login` → cookie so the
      four new files don't each re-copy the pattern
- [ ] `admin_client` fixture — `/admin*` needs a user whose `email == settings.admin_email` (`admin@test.com`)

Framework install not required — pytest, pytest-asyncio and pytest-cov are already in the dev group.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fidelity to the mockup | UI-01, UI-02 | "Looks like the design" is not machine-checkable | Compare each migrated section against `design/new_broadcaster_design.unpacked.html` |
| Cyrillic legibility in the chosen typeface | UI-01 / D-17 | Rendering quality is a visual judgement | Open pages with long Russian strings; confirm IBM Plex Sans is applied, not a system fallback |
| Bottom tabs on a real device | UI-06 / D-12 | `env(safe-area-inset-bottom)` behaves only on real hardware | Open on an iOS/Android device at <860px; confirm tabs clear the home indicator |
| No layout shift on partial load | UI-05 | Requires observing paint | Trigger infinite scroll and sync polling; watch for jumps |
| Dark-theme contrast | UI-01 / D-10 | Contrast against real content needs eyes | Check text/badges/tables against `#08080b` background |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

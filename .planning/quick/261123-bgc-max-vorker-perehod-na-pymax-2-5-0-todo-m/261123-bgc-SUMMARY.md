---
phase: quick-261123-bgc-max-worker-pymax-2-5-0
plan: 01
subsystem: max-worker
tags: [pymax, max, worker, upgrade, shims, session-migration]
requires: []
provides:
  - "MAX worker on PyMax 2.5.0 (pin in image, dev group and uv.lock)"
  - "pymax_compat.py reduced to one shim (frame size), re-audited for 2.5.0"
  - "contract tests for 2.5.0 and for the 2.3.1 -> 2.5.0 session transfer"
affects: [max_worker, tests/test_worker/test_max_worker.py]
tech-stack:
  added: ["maxapi-python 2.5.0 (was 2.3.1)"]
  patterns: ["version-scoped shim with fail-closed audit", "pristine-library assertions in a clean interpreter"]
key-files:
  created: []
  modified:
    - max_worker/requirements.txt
    - pyproject.toml
    - uv.lock
    - max_worker/pymax_compat.py
    - max_worker/main.py
    - tests/test_worker/test_max_worker.py
key-decisions:
  - "Frame-size shim kept (2.5.0 caps at 10 MiB, a 2.7 MB login frame already measured and growing); photo, CONTACT and STICKER shims removed"
  - "relogin and telemetry left at 2.5.0 defaults (the configuration that got the QR in the measurement)"
status: complete
commits: 3
plan_head_before: 807ab2ca800660adf297b96f63f4723645979ffb
plan_head_after: e0ce7d320770de7dae70517d2076618c8a2e3e51
actuals:
  tokens: 12400
  tasks: 2
  commits: 3
requirements-completed: [QUICK-MAX-PYMAX-2-5-0]
completed: 2026-11-23
---

# Quick 261123-bgc: MAX worker moved to PyMax 2.5.0 Summary

The worker code of this branch now runs on PyMax 2.5.0 and receives the MAX login QR in a disposable container, where the same probe on the HEAD code (pin 2.3.1) does not; three of the four 2.3.1 shims are gone because 2.5.0 fixed those defects, the fourth (frame size) is kept and re-audited.

## Commits

| Hash | Message |
|------|---------|
| d2588e0a | test(quick-261123-bgc): pin the PyMax 2.5.0 contract (RED measured on 2.3.1) |
| 7153c9fb | feat(quick-261123-bgc): move the MAX worker to PyMax 2.5.0 |
| e0ce7d32 | test(quick-261123-bgc): pin the 2.3.1 to 2.5.0 session transfer |

## End-to-end QR probe (disposable `docker run --rm`, code mounted read-only from this worktree, 45 s wait)

- RED, code at HEAD (pin 2.3.1): `MAX_QR_PROBE result=no_qr pymax=2.3.1 code=/probe/max_worker`
- GREEN, branch code (pin 2.5.0): `MAX_QR_PROBE result=qr_captured pymax=2.5.0 code=/probe/max_worker`

The QR link was never printed or logged (the probe prints only whether one exists; the log `.pytest_cache/gsd-orch/max-qr-probe.log` has 9 lines and no URL). The production image `broadcaster-max-worker:latest` and running containers were not touched.

## RED evidence (contract tests)

`bgc-red.xml` on the 2.3.1 environment: 11 failures, all assertion failures (version `'2.3.1' == '2.5.0'`, pristine CONTACT/STICKER parse, remaining-shim log marker, `photos=` URL, frame-size 10 MiB, fail-closed message, requirement pin). No ImportError or collection error. 50 others passed because the 2.3.1 shims were still active.

## 2.5.0 facts re-checked against the installed `.venv`

| Fact (plan) | Installed 2.5.0 | Verdict |
|---|---|---|
| transport `max_size` 10 MiB on both branches, `Origin("https://web.max.ru")` | `transport/websocket.py:21-27` | confirmed |
| photo id from `photos` or `photoIds`; no id -> exactly one result entry | `api/uploads/service.py:100`, `:182` | confirmed |
| `contact_id: int | None = None` | `types/domain/attachments/contact.py:27` | confirmed |
| `set_id: int | None = None` | `types/domain/attachments/sticker.py:45` | confirmed |
| `ExtraConfig.url` default `wss://api.oneme.ru/websocket`, `relogin: bool = True`, `telemetry: bool = True` | `config.py:256`, `:262`, `:273` (line 172 `telemetry=False` is the internal `ClientConfig`, not `ExtraConfig`) | confirmed |
| `sessions` DDL has `user_agent`; `_ensure_column` migrates in place | `session/store.py:100-111`, `:120` | confirmed |
| revoked token + `relogin` -> restart auth | `base.py:205-236` (`relogin(start=False)`) | confirmed |
| `Profile.contact.phone: int | None` | `types/domain/user.py:71` | confirmed |
| `show_qr(self, qr_url)`; `WebClient(session_name, work_dir, extra_config, auth_flow, qr_provider)` | `auth/providers.py:79`, `client_web.py:34-41` | confirmed |
| telemetry goes through the same MAX socket, opcode LOG | `telemetry/service.py:145-155` | confirmed |
| `configure_logging` touches only the `pymax` logger | `logging.py:55-100` | confirmed; worker clear-list unchanged |
| session DB at `work_dir/session_name`; legacy `device_id` reaches the saved session | `app.py:43` + `store.py:84`; `base.py:122` + `app.py:124` | confirmed (also asserted by test) |

One real difference found by the tests: the PHOTO_UPLOAD request payload in 2.5.0 carries `type` and `uploaderType` in addition to `count`/`profile`; the album test now asserts `count == 1` and `profile is False` per upload instead of the exact dict.

## Shim decisions

- Photo upload: removed. Untouched 2.5.0 `UploadService` passes through real `MessageService`/`UploadService` with only the MAX socket and upload HTTP faked: URL without ids + one entry -> that token; `photoIds=777` -> 777; `photos=777` with two entries -> 777; no id + two entries (or none) -> `UploadError`.
- CONTACT, STICKER: removed. Clean-interpreter tests parse `Chat`/`LoginResponse` with absent `contactId`/`setId`; other attachment fields still validate; group sync tests unchanged and green.
- Frame size: kept. 2.5.0 raised 1 MiB to 10 MiB but the login frame grows with the account (2.7 MB measured); shim passes `max_size=None`, same `Origin` and proxy branch, fails closed on any other version (tested with `2.5.1`).

## Session transfer (task 2)

New tests: a `session.db` in the exact 2.3.1 DDL is judged reusable by the worker, the real 2.5.0 `SessionStore` reads the same token and device_id (`user_agent` None), adds the `user_agent` column in place, loses no row; legacy 1.x parameters built by the worker are accepted by the real `ExtraConfig` (`relogin is True`); the real `WebClient` built by `create_client` has `work_dir/session_name == session_db_path()` and the legacy device_id in its config (via private `_prepare_config`). No worker defect found, so no `fix` commit.

Negative controls (fixtures restored, verified identical afterwards):
- (a) empty token in the 2.3.1 fixture: `assert False is True` on `has_reusable_session()` -> RED.
- (b) `ExtraConfig(**kwargs, relogin=False)`: two failures `assert False is True` on `relogin` -> RED. An unknown extra key is NOT rejected by `ExtraConfig` 2.5.0 (`DID NOT RAISE`), so the plan's fallback (relogin substitution) was used and the "rejects unknown keys" test was dropped.

## Gates

- `uv run pytest tests/test_worker/test_max_worker.py tests/test_max_worker_deployment.py tests/test_max_container_manager.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_services/test_log_masking.py -q` -> 673 passed.
- `-k "session or legacy or relogin or health or pymax"` -> 21 passed.
- `uv.lock` composition gate: changed packages `['maxapi-python']` at 2.5.0; wheel sha256 `20dcf9bf...f479` present once.
- `graphify update .` -> exit 0 (32307 nodes, 53627 edges).
- Full suite and `tests/test_planning/` not run (out of scope for a quick task).

## Owner path (not executed)

1. Rebuild the MAX image: `just prod-build` or `just prod-deploy`.
2. Probe the BUILT image before restarting workers (no code mount, no pip):
   `mkdir -p .pytest_cache/gsd-orch && timeout 300 docker run --rm -w /app -e ACCOUNT_ID=qr-probe -e SESSIONS_DIR=/tmp/qr-probe-sessions -e PYTHONDONTWRITEBYTECODE=1 --entrypoint timeout broadcaster-max-worker:latest 240 python -c "import sys, os, asyncio; import max_worker.main as m; L = asyncio.new_event_loop(); asyncio.set_event_loop(L); s = L.run_until_complete(m.create_client('')); L.run_until_complete(asyncio.sleep(45)); print('MAX_QR_PROBE result=%s pymax=%s code=%s' % ('qr_captured' if s.qr_code else 'no_qr', m.pymax.__version__, os.path.dirname(m.__file__)), flush=True); os._exit(0)"`
   Expected line: `MAX_QR_PROBE result=qr_captured pymax=2.5.0 code=/app/max_worker`. Read logs, not the exit code (2.5.0 swallows `SystemExit` in `show_qr`).
3. Restart the MAX workers.
4. Account #19: either `connected` on the old token (the session DB migrates in place), or, if MAX rejects the token, 2.5.0 `relogin` deletes the session row and the worker shows a QR; rescan.
5. `/gsd-verify-work 19` for W-1/W-2 and question A3 (does MAX report the number itself).

Owner decision, telemetry: 2.5.0 sends synthetic navigation telemetry (opcode LOG) over the same MAX socket by default (`ExtraConfig.telemetry=True`). The worker keeps the default because the QR measurement used it. Disabling is `telemetry=False` in `config_kwargs`, as a separate task.

## Deviations from Plan

- [Rule 1 - Bug in test] The first draft of `test_pymax_2_5_0_contract` imported `max_worker.main` without `ACCOUNT_ID` and died with `SystemExit`; switched to the `worker` fixture before the RED commit. Not a product change.
- [Rule 1 - 2.5.0 behavior] Album test asserted the exact PHOTO_UPLOAD payload; relaxed to the fields that matter (see above).
- The "unknown keys rejected" half of the negative control for (b) was impossible (`ExtraConfig` accepts them); substituted `relogin=False` as the plan allowed.

## Known Stubs

None.

## Threat Flags

None. Mitigations T-QUICK-BGC-01 (hash and uv.lock composition gate), -02 (probe prints no link), -05 (session transfer tests), -06 (disposable read-only probe), -07 (privacy gates green) applied as planned.

## Self-Check: PASSED

Commits d2588e0a, 7153c9fb, e0ce7d32 are ancestors of HEAD; modified files exist; the untracked `.dockerignore` mentioned in the plan was not present in this worktree and nothing outside `files_modified` was changed.

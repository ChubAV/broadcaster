---
status: awaiting_human_verify
trigger: "не удается подключить аккаунт max; контейнер после обновления падает с ModuleNotFoundError: No module named 'max_worker'"
created: 2026-08-04
updated: 2026-08-04T08:39:00Z
audit_acknowledged:
  milestone: v2.0
  at: 2026-08-25
  status: awaiting_human_verify
---

# Debug Session: MAX worker import after update

## Symptoms

- expected_behavior: MAX account connects successfully and the MAX worker container remains running.
- actual_behavior: The MAX worker container exits during startup and repeatedly restarts.
- error_messages: `ModuleNotFoundError: No module named 'max_worker'` at `/app/main.py:34` while importing `max_worker.pymax_compat`.
- timeline: Regression started after an update; the MAX account connection worked before that update.
- reproduction: Start the MAX worker container while connecting a MAX account, then inspect its logs.

## Current Focus

- hypothesis: Confirmed — the new package-qualified import and the flattened script-mode Docker layout jointly make `max_worker` unresolvable at startup.
- test: Human verifies the corrected image in the real deploy/account-connection workflow.
- expecting: Rebuild/deploy starts a MAX worker that remains running, no longer logs `ModuleNotFoundError: No module named 'max_worker'`, and exposes its health/QR flow normally.
- next_action: Ask the user to rebuild/deploy the MAX worker image and reconnect the affected MAX account, then report `confirmed fixed` or the remaining failure/log.
- bug_class: bohrbug
- reasoning_checkpoint:
    hypothesis: "`from max_worker.pymax_compat ...` fails because the Docker image copies the contents of `max_worker/` directly into `/app` and executes `/app/main.py`, leaving no importable top-level `max_worker` package."
    confirming_evidence:

      - "Production traceback reaches `/app/main.py:34` and reports exactly `No module named 'max_worker'`."
      - "`find_spec('max_worker.pymax_compat')` succeeds from the repository root, fails with the production error from the flattened worker directory, and `find_spec('pymax_compat')` succeeds there."
      - "Commit `35bad07` introduced the package-qualified import without changing the pre-existing flattened Docker COPY/entrypoint."
    falsification_test: "The hypothesis would be false if a Docker-equivalent `/app` containing only `main.py` and `pymax_compat.py` could resolve `max_worker.pymax_compat`, or if the built image preserved `/app/max_worker` and launched it as a module."
    fix_rationale: "Preserve the worker as `/app/max_worker` and invoke `python -m max_worker.main`, aligning production with the package import already exercised by unit tests and removing the import-context mismatch rather than adding dual-mode fallback logic."
    blind_spots: "The local root environment lacks the image-only PyMax dependency, so full worker startup must be verified through focused tests and, if Docker is available, an image-level smoke check; Redis/network behavior is downstream of this pre-startup failure."
    candidate_causes:

      - "code: commit `35bad07` added a package-qualified `max_worker.pymax_compat` import."
      - "config: the Docker build context, `COPY . .`, and `python main.py` flatten and script-run the package contents."
      - "environment: missing PyMax or stale image was considered, but production reached the line after PyMax imports and reports the new line 34."
      - "data: account/session data cannot influence module resolution before configuration/session handling begins."
    and_gate: "yes — either condition alone works (the package import works from repository root; the flattened image worked before the new import), but together they deterministically fail."

- tdd_checkpoint:

## Evidence

- timestamp: 2026-08-04T00:00:00Z
  checked: User-provided production container log and regression timeline.
  found: Startup deterministically fails at `/app/main.py:34` importing `max_worker.pymax_compat`; failure began after an update.
  implication: Investigate the updated import against the Docker image's filesystem and Python module search path.

- timestamp: 2026-08-04T00:00:01Z
  checked: Existing project knowledge graph query for MAX worker package, compatibility module, deployment test, Docker layout, and entrypoint relationships.
  found: The graph identifies `max_worker/main.py`, `max_worker/pymax_compat.py`, MAX deployment tests, and the recent PyMax compatibility change as the directly related code area.
  implication: Scope the investigation to MAX worker packaging/import behavior and its deployment regression coverage.

- timestamp: 2026-08-04T07:59:30Z
  checked: Debug knowledge-base and graph work-memory recall.
  found: `.planning/debug/knowledge-base.md` does not exist and graph reflection contains zero prior memories.
  implication: No known-pattern resolution can be reused; test the packaging hypothesis from first principles.

- timestamp: 2026-08-04T08:00:00Z
  checked: Constrained query expansion against `graphify-out/graph.json` vocabulary.
  found: Exact graph tokens exist for `max`, `worker`, `dockerfile`, `import`, `pymax`, `compat`, `copy`, `entrypoint`, `deployment`, `container`, `module`, and `main`.
  implication: A vocabulary-grounded traversal can inspect the relevant packaging path without relying on invented search terms.

- timestamp: 2026-08-04T08:02:00Z
  checked: BFS traversal of the existing project graph for the audited MAX worker packaging vocabulary.
  found: The graph has an extracted import edge from `max_worker/main.py:34` to `max_worker/pymax_compat.py`, and identifies `tests/test_max_worker_deployment.py` plus `tests/test_worker/test_max_worker.py` as adjacent coverage.
  implication: Read the source, image construction, and those tests as the smallest relevant slice; the graph does not itself prove the runtime filesystem layout.

- timestamp: 2026-08-04T08:07:00Z
  checked: Complete `max_worker/main.py`, `max_worker/pymax_compat.py`, `max_worker/Dockerfile`, `tests/test_worker/test_max_worker.py`, and `tests/test_max_worker_deployment.py`.
  found: `main.py:34` imports `max_worker.pymax_compat`; Docker build context is `./max_worker`, `COPY . .` flattens its contents into `/app`, and `CMD ["python", "main.py"]` runs with `/app` as the script directory. Unit tests import `max_worker.main` from the repository root; deployment tests assert build order/revision metadata but never test container-layout importability.
  implication: The same source is importable in tests because the repository parent is on `sys.path`, but the production entrypoint lacks that parent. Existing coverage missed the layout-specific import contract.

- timestamp: 2026-08-04T08:08:00Z
  checked: SBFL preconditions for the deterministic MAX startup failure.
  found: Focused tests exist, but there is not yet a checked-in failing regression test with per-test coverage for the Docker-layout import path.
  implication: SBFL is skipped because no failing/passing per-test coverage spectrum exists; use direct deterministic reproduction and differential debugging.

- timestamp: 2026-08-04T08:10:00Z
  checked: Git commit `35bad07` and its parent Dockerfile/main import block.
  found: Commit `35bad07` added only `max_worker/pymax_compat.py` and `from max_worker.pymax_compat ...` plus invocation/logging in `main.py`; it did not change the pre-existing flattened `COPY . .` and `CMD ["python", "main.py"]` image layout.
  implication: The regression boundary is the newly package-qualified import introduced into a script-mode container; later image revision changes are not required to explain the startup failure.

- timestamp: 2026-08-04T08:10:30Z
  checked: First paired local import reproduction.
  found: Both runs were blocked before Python startup because uv attempted to write its cache under read-only `/home/orca/.cache/uv`.
  implication: This is an investigation-environment constraint, not evidence for or against the import hypothesis; rerun with `UV_CACHE_DIR` under `/tmp`.

- timestamp: 2026-08-04T08:13:00Z
  checked: Paired full imports after redirecting uv cache to `/tmp`.
  found: Both local contexts stop earlier at `import pymax` because the root uv environment lacks the MAX worker's image-only dependency.
  implication: Full local startup is not a valid discriminator here. Production logs reached line 34, proving its image has PyMax; isolate Python module resolution without importing dependencies.

- timestamp: 2026-08-04T08:15:00Z
  checked: Python module-spec resolution from repository-root and Docker-equivalent flattened working directories.
  found: Root context resolves `max_worker.pymax_compat` to the compatibility file; flattened context raises `ModuleNotFoundError: No module named 'max_worker'`; the same flattened context resolves top-level `pymax_compat` to that file.
  implication: The import failure is deterministic and caused by module search path/layout, not the compatibility module contents.

- timestamp: 2026-08-04T08:20:00Z
  checked: Agent-authored regression test `test_max_worker_image_preserves_package_layout_for_module_entrypoint` before the fix.
  found: The test fails on the expected assertion because the Dockerfile contains `COPY . .` and `CMD ["python", "main.py"]`.
  implication: The test is RED for the exact root-cause contract and can drive/guard the minimal Dockerfile correction.

- timestamp: 2026-08-04T08:23:00Z
  checked: Target regression after preserving the package directory and switching the entrypoint to module mode.
  found: `test_max_worker_image_preserves_package_layout_for_module_entrypoint` passes (1 passed).
  implication: The minimal Dockerfile change satisfies the specified packaging oracle.

- timestamp: 2026-08-04T08:26:00Z
  checked: Full adjacent deployment test file and scoped diff.
  found: All 5 deployment tests pass; `git diff --check` passes; the scoped diff is two behavior-preserving Dockerfile substitutions plus one new regression test, not a deletion/short-circuit.
  implication: Adjacent deployment contracts remain intact and the no-op/behavior-deletion guard passes.

- timestamp: 2026-08-04T08:26:30Z
  checked: Mutation-testing configuration for the Docker/Python deployment contract.
  found: No Stryker, mutmut, Cosmic Ray, or other mutation runner is configured; the only text match is the compatibility function's prose.
  implication: Automated mutation signal is explicitly skipped as unavailable; the driving test directly asserts both changed Dockerfile lines and the revert/reconfirm signal will test causality.

- timestamp: 2026-08-04T08:27:00Z
  checked: Docker daemon availability for an image-level smoke test.
  found: Docker client and server 29.7.1 are available after approved daemon access.
  implication: After guardrail causality checks, build the corrected MAX image and inspect its filesystem/entrypoint without starting Redis-dependent application behavior.

- timestamp: 2026-08-04T08:30:30Z
  checked: Revert-and-reconfirm guardrail for the exact Dockerfile fix.
  found: With only the two Dockerfile lines reverted, the target test fails on the missing package-preserving COPY assertion; after reapplying the exact two-line fix, the same test passes.
  implication: The Dockerfile change is causally necessary and sufficient for the specified deployment contract.

- timestamp: 2026-08-04T08:35:00Z
  checked: Built-image configuration and non-networking import smoke test.
  found: Disposable image build succeeds; image workdir is `/app`, command is `["python", "-m", "max_worker.main"]`, revision label is present, and `import max_worker.main` succeeds from `/app/max_worker/main.py` while applying the PyMax compatibility shim.
  implication: The actual image filesystem and Python runtime now satisfy the previously failing import contract; Redis/account behavior remains for human end-to-end verification.

- timestamp: 2026-08-04T08:37:30Z
  checked: Required project knowledge-graph refresh after source changes.
  found: `graphify update .` completed, rebuilding the code graph to 8,379 nodes and 14,152 edges; it warned that community labels changed and that doc/paper/image changes require a separate semantic update.
  implication: The Dockerfile/test source changes are represented in the project graph; the labeling warning does not affect the fix or verification.

- timestamp: 2026-08-04T08:38:00Z
  checked: Cleanup of the exact disposable verification image tag.
  found: `broadcaster-max-worker:debug-import-fix` was untagged and its disposable image deleted after successful verification.
  implication: Verification left no debug image behind; the production `broadcaster-max-worker:latest` image was not modified by the smoke test.

- timestamp: 2026-08-04T08:38:30Z
  checked: Final scoped worktree state.
  found: `git diff --check` passes and the source fix remains limited to `max_worker/Dockerfile` plus `tests/test_max_worker_deployment.py`; unrelated pre-existing user changes remain untouched.
  implication: Automated verification is complete and accepted; only real-workflow human confirmation remains before resolution/archive.

## Eliminated

- hypothesis: The production image is missing the PyMax dependency.
  evidence: The production traceback reaches `main.py:34`, after `import pymax` and its submodule imports at lines 24 and 31-32 completed.
  timestamp: 2026-08-04T08:16:00Z

- hypothesis: MAX account or session data triggers the crash.
  evidence: The crash occurs while Python resolves module imports, before `ACCOUNT_ID`, session files, Redis, or account data are evaluated.
  timestamp: 2026-08-04T08:16:30Z

- hypothesis: A later image-revision/deployment commit introduced the import crash.
  evidence: Git shows commit `35bad07` added the failing import while leaving the already-existing Docker layout unchanged; this is sufficient to reproduce the regression.
  timestamp: 2026-08-04T08:17:00Z

## Resolution

- root_cause: "Code: commit `35bad07` introduced `from max_worker.pymax_compat ...`; Config: the MAX Docker image flattens that directory into `/app` and launches `main.py` as a script, so `/app` has no importable `max_worker` parent package."
- fix: "Copy the MAX worker build context into `/app/max_worker` and launch `python -m max_worker.main`; add a deployment regression test asserting both package layout and module-mode entrypoint."
- verification:
    target_test: {result: pass, command: "pytest tests/test_max_worker_deployment.py::test_max_worker_image_preserves_package_layout_for_module_entrypoint -q"}
    mutation_check: {result: skipped, reason_if_skipped: "No Python/Docker mutation runner is configured; the regression directly asserts both changed Dockerfile lines.", mutant_killed: null}
    no_op_deletion: {result: pass, deletion_justified_by_rca: false}
    adjacent_tests: {result: pass, suites_run: ["tests/test_max_worker_deployment.py — 5 passed"]}
    revert_and_reconfirm: {result: pass, bug_returned_on_revert: true, fixed_on_reapply: true}
    image_smoke: {result: pass, detail: "Built image imports max_worker.main from /app/max_worker/main.py and preserves module-mode CMD."}
    guardrail_verdict: accepted

- files_changed: [max_worker/Dockerfile, tests/test_max_worker_deployment.py]
- oracle_type: specified — the deployment contract requires a preserved Python package layout and module-mode entrypoint; this asserts both root-cause conditions rather than merely checking that startup does not crash.

---
status: resolved
trigger: "исправить issue 34"
created: 2026-08-07
updated: 2026-08-07
---

# Debug Session: max-group-sync-sticker

## Symptoms

**Source:** GitHub issue #34 "Синхронизация групп в месанджере MAX" (ChubAV, 2026-08-07T11:13:30Z)
Repo: https://github.com/ChubAV/broadcaster — `gh api repos/ChubAV/broadcaster/issues/34`

**Expected behavior:**
After a MAX account connects (QR auth completes), `group_sync` fetches the account's chats and
persists the groups so the user can select them for schedules. `sync-status` should report success.

**Actual behavior:**
Worker starts fine, QR auth succeeds (`client started profile=35316857 chats=40`,
`connected account_id=26`), `group_sync_start account_id=26 delay_sec=30` fires — but every
`group_fetch_attempt` fails with a pydantic validation error while parsing a `Chat`. All 4 attempts
retry at 30 s intervals and groups are never synced; the UI keeps polling `/api/sessions/26/sync-status`.

**Error message (verbatim from container log, max-worker-26, build_revision=c44e22fe1eebc4a0d0794578353d7f39dace5590, pymax_version=2.3.1):**
```
group_fetch_failed account_id=26 attempt=1 max_attempts=4 error=2 validation errors for Chat
lastMessage.attaches.0.tagged-union[PhotoAttachment,VideoAttachment,FileAttachment,ContactAttachment,StickerAttachment,AudioAttachment,ControlAttachment,InlineKeyboardAttachment,ShareAttachment,CallAttachment].STICKER.setId
  Field required [type=missing, input_value={'authorType': 'USER', '_...54954683, 'height': 170}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
lastMessage.attaches.0.UnknownAttachment
  Value error, Known attachment type should be parsed by its own model [type=value_error, input_value={'authorType': 'USER', '_...54954683, 'height': 170}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/value_error
```

**Timeline:**
User reports it broke recently — MAX group sync worked before, stopped after recent changes
(pymax upgrade / max-worker image rebuild). Recent commits touching this area:
`c44e22f docs(quick-260804-8wh): fix MAX container runtime problems`,
`61c4121 feat(260804-8wh): rebuild and identify MAX worker images`.

**Reproduction:**
Connect MAX account 26 in prod, wait for `group_sync_start`; any chat whose `lastMessage` carries a
STICKER attachment without a `setId` field triggers the failure. No local repro exists yet.

**Verification constraints (user decision):**
Fix must be verified by a regression test run locally (`uv run pytest tests/ -v`) — write a test that
feeds a sticker attachment payload without `setId` through the parsing path. No prod-server access is
to be used for verification in this session; do NOT attempt to deploy or touch the prod host.

## Relevant context

- `max_worker/pymax_compat.py` already contains a compatibility shim for `ContactAttachment`
  (applied at `max_worker/main.py:97`, logged as `pymax_contact_attachment_compatibility_applied`) —
  the same class of upstream-schema-strictness problem. It rebuilds models for
  `ContactAttachment, Message, Chat, LoginResponse`.
- Group sync lives in the max_worker service; the log messages `group_sync_start`,
  `group_fetch_attempt`, `group_fetch_failed`, `group_fetch_retry` are emitted by `max_worker`.

## Current Focus

hypothesis: CONFIRMED — pymax 2.3.1 declares `StickerAttachment.set_id: int` (required, camel alias
  `setId`) while MAX emits STICKER attachments without it; the discriminated union then fails both
  branches (STICKER: missing setId; UnknownAttachment: rejects known types) and the whole `Chat`
  fails to parse, aborting every `group_fetch_attempt`.
test: reproduced locally against real pymax 2.3.1 — byte-identical error to prod.
expecting: extending the existing version-scoped shim to relax `set_id` makes the payload parse.
next_action: awaiting user confirmation that MAX group sync succeeds in prod after redeploy of the
  max-worker image (local RED->GREEN and the fix-acceptance guardrail are complete).

reasoning_checkpoint:
  hypothesis: "pymax 2.3.1's StickerAttachment marks set_id (alias setId) as required; MAX omits it
    for some stickers, so Chat.lastMessage.attaches tagged-union validation fails and group sync
    never returns any chats."
  confirming_evidence:
    - "Direct read of the installed model: .venv/.../pymax/types/domain/attachments/sticker.py has
       `set_id: int` with no default; CamelModel supplies the `setId` alias."
    - "Local reproduction with a setId-less STICKER payload produces the exact 2-error prod message
       (STICKER.setId missing + UnknownAttachment value_error)."
    - "Upstream agrees on the semantics: maxapi-python 2.4.0 changed the field to
       `set_id: int | None = None` — i.e. upstream itself treats 2.3.1's requirement as a bug."
    - "Timeline matches: commit fea8b6a changed max_worker/requirements.txt from
       `maxapi-python>=1.2.0` to `==2.3.1`. Group sync worked on the 1.2.x schema."
    - "Same failure shape as the already-shimmed ContactAttachment.contactId case."
  falsification_test: "If a setId-less STICKER payload still failed after relaxing only set_id, or
    if some other required STICKER field were also missing from the prod payload, the hypothesis
    would be wrong. The prod log lists exactly one missing field: setId."
  fix_rationale: "The root cause is an over-strict upstream field declaration, not worker logic. The
    fix relaxes exactly that field (matching upstream 2.4.0's own fix) via the existing version-pinned
    shim, then rebuilds the schemas that embed the attachment union. Nothing catches or skips the
    error — the chat parses correctly, so no data is silently dropped."
  blind_spots: "Only set_id is relaxed. If MAX also omits other STICKER fields (url, stickerId,
    width, time, stickerType, audio, height) on other payloads, a new failure of the same class would
    appear. Prod evidence shows only setId. Other attachment types (AUDIO/SHARE/CALL/...) may carry
    the same latent strictness; not addressed here (no evidence, would widen the seam)."
  candidate_causes:
    - "code (dependency): pymax 2.3.1 declares set_id required — CONFIRMED"
    - "data (upstream service): MAX server emits STICKER attachments without setId — CONFIRMED"
    - "config: pinned version bump >=1.2.0 -> ==2.3.1 in max_worker/requirements.txt (fea8b6a) is
       what exposed the strict schema — CONFIRMED as the trigger"
    - "environment: image rebuild alone — ELIMINATED, rebuild only materialized the version pin"
  and_gate: "yes — the failure needs BOTH conditions simultaneously: pymax requiring setId AND MAX
    omitting it. Neither alone breaks sync. Fixing either side resolves it; only the pymax side is
    under our control."

tdd_checkpoint:
  test_file: "tests/test_worker/test_max_worker.py"
  test_names:
    - "test_unmodified_pymax_rejects_sticker_without_set_id"
    - "test_sticker_compatibility_parses_chat_in_a_clean_interpreter"
    - "test_sticker_compatibility_accepts_raw_chat_and_login_payloads_idempotently"
    - "test_sticker_compatibility_preserves_set_ids_and_other_sticker_validation"
    - "test_worker_applies_sticker_compatibility_on_import"
    - "test_group_sync_accepts_pymax_chat_with_set_id_less_sticker"
  status: "green (was red before the shim — see Evidence)"

## Evidence

- checked: local test env for pymax availability (`uv run pytest tests/test_worker/test_max_worker.py`)
  found: `ModuleNotFoundError: No module named 'pymax'` — `maxapi-python` is only in
    `max_worker/requirements.txt` (image-only), never in `pyproject.toml`; `git log -S maxapi-python`
    on pyproject/uv.lock returns nothing.
  implication: the existing PyMax compatibility tests have never actually run locally. The local
    verification the user requires needs the dependency added to the dev group first.

- checked: `max_worker/pymax_compat.py` + `max_worker/main.py:34-37,96-97`
  found: shim mutates `ContactAttachment.model_fields["contact_id"]` to `int | None` / default None,
    then `model_rebuild(force=True)` on `(ContactAttachment, Message, Chat, LoginResponse)`. Applied
    at import time of `max_worker.main`, before any client is created. Version-pinned to 2.3.1,
    fails closed on other versions, idempotent (returns False when already optional).
  implication: exact same mechanism applies to STICKER; the union rebuild list is already correct.

- checked: RED verification — restored `max_worker/pymax_compat.py` and `max_worker/main.py` to HEAD
    (pre-fix) with the new sticker tests in place, ran `uv run pytest tests/test_worker/test_max_worker.py -k sticker`
  found: 5 failed, 1 passed. `test_group_sync_accepts_pymax_chat_with_set_id_less_sticker` raised the
    exact prod signature:
      `2 validation errors for Chat`
      `lastMessage.attaches.0.tagged-union[PhotoAttachment,...,StickerAttachment,...].STICKER.setId`
        `Field required [type=missing, ...]`
      `lastMessage.attaches.0.UnknownAttachment`
        `Value error, Known attachment type should be parsed by its own model [type=value_error, ...]`
    Only cosmetic delta vs prod: pydantic docs URL 2.12 (local) vs 2.13 (prod image) — same model shape.
    The 1 pass was `test_unmodified_pymax_rejects_sticker_without_set_id`, which asserts pristine
    PyMax rejects the payload and therefore holds with or without the shim (by design).
  implication: the tests are genuinely RED without the fix and reproduce the prod defect at the
    group_sync altitude, not just at the model altitude. No silent skip — pymax now installs locally.

- checked: GREEN verification — restored the shim, reran the sticker selection and then the whole
    max_worker surface (`tests/test_worker/test_max_worker.py tests/test_max_worker_deployment.py`)
  found: 6/6 sticker tests pass; 38/38 max_worker + deployment tests pass.
  implication: the shim resolves the defect and breaks nothing in the worker's own suite.

- checked: fix-acceptance guardrail signal — mutation testing at the fix site (3 mutants)
  found: all 3 killed. M1 (drop `field.default = None`, annotation-only) -> 4 failed. M2 (rebuild only
    the attachment model, skipping `_ATTACHMENT_UNION_SCHEMAS`) -> 4 failed, proving the union-rebuild
    step is load-bearing and asserted. M3 (widen the shim to every StickerAttachment field) -> caught by
    `test_sticker_compatibility_preserves_set_ids_and_other_sticker_validation` with `DID NOT RAISE`.
  implication: no surviving mutants; the regression tests pin both the fix's presence and its narrowness
    (the documented blind_spot about not over-broadening is actively enforced, not just noted).

- checked: full suite `uv run pytest tests/ -v` -> 26 failed, 348 passed, 2 errors. Triaged the
    failures against a clean HEAD worktree (`git worktree add --detach /tmp/bcast-baseline HEAD`) with
    HEAD's own dependency set.
  found: clean HEAD baseline = 40/40 pass on exactly those files, so the failures are NOT from HEAD source.
    Isolating the real variable: moving the developer's local `/source/broadcaster/.env` aside and
    rerunning the same 8 files in the working tree gave 39 passed / 1 failed. So 25 of the 26 failures
    are local `.env` pollution (e.g. `test_s3_settings_defaults` asserts `''` but reads the real
    `https://s3.twcstorage.ru`; DB/auth settings likewise leak into the in-memory-SQLite fixtures).
    The `.env` is gitignored and absent from the worktree, which is why the baseline looked clean.
  implication: not a regression from this fix; a pre-existing local-environment hazard.

- checked: the 1 remaining failure `tests/test_whatsapp_routing.py::TestEnsureWaContainer::test_returns_existing_endpoint`
    — ran HEAD source against the NEW dependency set (`/source/broadcaster/.venv` with maxapi-python
    2.3.1 + aiohttp bumped 3.13.3 -> 3.14.3) via `cd /tmp/bcast-baseline && .venv/bin/python -m pytest tests/test_whatsapp_routing.py`
  found: 9/9 pass. The new dependencies are therefore exonerated; the failure tracks the uncommitted
    working-tree edits to `app/messengers/whatsapp.py` from unrelated prior work.
  implication: the `pyproject.toml` dev-dependency addition (and its transitive aiohttp bump) causes no
    regression. The whatsapp failure belongs to whoever owns that dirty file, not to this fix.

## Eliminated

- hypothesis: "adding maxapi-python to the dev dependency group regresses the rest of the suite
    (it pulls aiohttp 3.13.3 -> 3.14.3 plus aiofiles/msgpack/python-socks/zstandard)"
  evidence: HEAD source run against the new dependency set passes 9/9 on the only non-`.env` failure,
    and the other 25 failures reproduce from the local `.env` alone. Deps are not the variable.
  timestamp: 2026-08-07

## Resolution

root_cause: pymax (maxapi-python) 2.3.1 declares `StickerAttachment.set_id: int` as required (camel
  alias `setId`); MAX emits STICKER attachments with no `setId`. Both conditions are required — the
  AND-gate fired. The strict field makes the STICKER branch of the attachment tagged union fail, the
  UnknownAttachment fallback then refuses a known type, so the entire `Chat` fails to validate and
  every `group_fetch_attempt` aborts. Exposed by commit fea8b6a pinning `maxapi-python>=1.2.0` ->
  `==2.3.1`; upstream itself corrected this in 2.4.0 with `set_id: int | None = None`.

fix: extended the existing version-scoped compatibility shim rather than adding a new mechanism.
  `_relax_required_field()` was factored out of the CONTACT shim (same mutate-then-rebuild pattern:
  set the field annotation to `int | None`, default `None`, then `model_rebuild(force=True)` on the
  attachment model plus every schema embedding the union — `Message`, `Chat`, `LoginResponse`). New
  `apply_sticker_attachment_compatibility()` applies it to `StickerAttachment.set_id` only, and
  `max_worker/main.py` invokes it at import time (before any client exists), logging
  `pymax_sticker_attachment_compatibility_applied`. Pinned to 2.3.1, fails closed on any other
  version, idempotent. `maxapi-python==2.3.1` was added to the dev dependency group so the compat
  tests actually execute locally instead of erroring on a missing module.

verification:
  guardrail_verdict: accepted
  oracle_type: specified (upstream 2.4.0 declares set_id optional — the intended contract is known,
    not merely "does not crash")
  signal_1_regression_test: PASS — RED before the fix with the byte-identical prod 2-error signature,
    GREEN after. 6 sticker tests.
  signal_2_revert: PASS — reverting only `pymax_compat.py` + `main.py` brings the defect back, so the
    fix (not an incidental environment change) is what resolves it.
  signal_3_mutation: PASS — 3/3 mutants killed at the fix site, including an over-broadening mutant.
  signal_4_not_deletion_only: PASS — the fix adds a narrow, documented shim; nothing was deleted or
    silenced, and no exception is swallowed (the chat parses correctly, no data is dropped).
  signal_5_full_suite: PASS with documented attribution — 26 pre-existing failures all traced to the
    local `.env` (25) and an unrelated dirty `app/messengers/whatsapp.py` (1); both reproduce
    independently of this change.
  boundary_neighbors: set_id 0 (falsy — guards a naive truthiness implementation), 1, and 54954683 all
    round-trip; each of the 7 other required STICKER fields still raises when absent.
  not_verified_here: prod behaviour. Per the user's constraint no deploy was performed, so
    end-to-end MAX group sync on account 26 is unconfirmed and needs a max-worker image rebuild.

files_changed:
  - max_worker/pymax_compat.py: extracted `_relax_required_field()`; added
      `apply_sticker_attachment_compatibility()` and `_ATTACHMENT_UNION_SCHEMAS`
  - max_worker/main.py: import + apply the sticker shim at module import; log when applied
  - tests/test_worker/test_max_worker.py: 6 sticker regression tests incl. the group_sync-level one
  - pyproject.toml: added `maxapi-python==2.3.1` to the dev group (matches max_worker/requirements.txt)
  - uv.lock: regenerated for the dev dependency

human_verification: accepted on local evidence (user decision, 2026-08-07). The user accepted the
  local RED->GREEN + mutation verification as sufficient and explicitly kept the prod host
  off-limits for this session. No GitHub action was taken on issue #34 by request.

## Prevention

why_not_caught: A gate existed but could not fire. `tests/test_worker/test_max_worker.py` already
  held PyMax compatibility tests for the identical ContactAttachment failure class — but
  `maxapi-python` lived only in `max_worker/requirements.txt` (image-only) and never in
  `pyproject.toml`, so those tests raised `ModuleNotFoundError` and had never actually executed
  locally or in CI. The dependency pin bump (fea8b6a, `>=1.2.0` -> `==2.3.1`) therefore changed the
  validation schema with zero test coverage watching it. The deeper why: the worker's runtime
  dependency set was not represented in the dev environment, so "the tests pass" was never a
  statement about the worker's actual dependency graph.

recurrence_guard:
  - regression test: `tests/test_worker/test_max_worker.py::test_group_sync_accepts_pymax_chat_with_set_id_less_sticker`
    (prod-altitude: runs the payload through `start_group_sync`, not just the model)
  - inverted guard: `tests/test_worker/test_max_worker.py::test_unmodified_pymax_rejects_sticker_without_set_id`
    shells into a clean interpreter with pristine PyMax and asserts the failure still exists. This
    keeps the RED condition permanently checkable, so the shim can never become silently vestigial —
    it starts failing the day the pin moves to a release that fixed the field, which is the signal
    to delete the shim.
  - dependency guard: `maxapi-python==2.3.1` added to the dev group, so every PyMax compat test now
    genuinely executes instead of erroring on a missing module.
  - fail-closed version pin: the shim raises on any PyMax version other than the audited 2.3.1 when
    it finds the field still required, so an unreviewed upgrade cannot silently widen the seam.

## Outstanding follow-ups (not done in this session, by user constraint)

- **Prod deploy required for the user-visible fix.** The shim ships *inside the max-worker image*.
  MAX account 26 does not recover until that image is rebuilt and the account's worker recycled.
  On deploy, confirm both `pymax_contact_attachment_compatibility_applied` and
  `pymax_sticker_attachment_compatibility_applied` at startup, then that `group_sync_start` is
  followed by a clean `group_fetch_attempt` and `/api/sessions/26/sync-status` reports ready.
- **Retire the shim at PyMax 2.4.0+.** Upstream fixed this with `set_id: int | None = None`. When
  the pin moves, `apply_sticker_attachment_compatibility()` returns False without raising, and
  `test_unmodified_pymax_rejects_sticker_without_set_id` will fail — that failure is the delete signal.
- **Unrelated observation — the full suite is not a usable green bar.** The gitignored local
  `.env` bleeds into `uv run pytest tests/ -v` and produces ~25 failures (e.g.
  `test_s3_settings_defaults` asserts `''` but reads the real `https://s3.twcstorage.ru`; DB/auth
  settings leak into the SQLite fixtures). A clean HEAD worktree passes 40/40 on the touched files.
  Worth isolating in `conftest.py`. Separately, the uncommitted `app/messengers/whatsapp.py` edits
  leave `test_whatsapp_routing.py::TestEnsureWaContainer::test_returns_existing_endpoint` red.

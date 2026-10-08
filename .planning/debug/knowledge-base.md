---
audit_acknowledged:
  milestone: v2.0
  at: 2026-08-25
  status: unknown
---

# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## max-group-sync-sticker — MAX group sync died on every chat whose lastMessage carried a setId-less STICKER

- **Date:** 2026-08-07
- **Error patterns:** `validation errors for Chat`, `lastMessage.attaches.0.tagged-union[...].STICKER.setId`, `Field required [type=missing]`, `UnknownAttachment`, `Known attachment type should be parsed by its own model [type=value_error]`, `group_fetch_failed`, `group_fetch_retry`, group sync never completes, `sync-status` polls forever, pydantic discriminated union, pymax, maxapi-python
- **Root cause(s):** pymax (maxapi-python) 2.3.1 declares `StickerAttachment.set_id: int` as required (camel alias `setId`); MAX emits STICKER attachments with no `setId`. AND-gated — both conditions are needed. The strict field makes the STICKER branch of the attachment tagged union fail, the `UnknownAttachment` fallback then refuses a known type, so the entire `Chat` fails to validate and every `group_fetch_attempt` aborts. Exposed by commit fea8b6a pinning `maxapi-python>=1.2.0` -> `==2.3.1`; upstream corrected it in 2.4.0 with `set_id: int | None = None`.
- **Fix:** Extended the existing version-scoped compatibility shim instead of adding a new mechanism. `_relax_required_field()` was factored out of the CONTACT shim (mutate-then-rebuild: set annotation to `int | None`, default `None`, then `model_rebuild(force=True)` on the attachment model plus every schema embedding the union — `Message`, `Chat`, `LoginResponse`). New `apply_sticker_attachment_compatibility()` applies it to `StickerAttachment.set_id` only; `max_worker/main.py` invokes it at import time before any client exists, logging `pymax_sticker_attachment_compatibility_applied`. Pinned to 2.3.1, fails closed on other versions, idempotent. `maxapi-python==2.3.1` added to the dev group so the compat tests actually execute.
- **Files changed:** max_worker/pymax_compat.py, max_worker/main.py, tests/test_worker/test_max_worker.py, pyproject.toml, uv.lock
- **Why not caught:** A gate existed but could not fire. Compat tests for the identical ContactAttachment failure class already lived in `tests/test_worker/test_max_worker.py`, but `maxapi-python` was only in `max_worker/requirements.txt` (image-only) and never in `pyproject.toml` — so those tests raised `ModuleNotFoundError` and had never actually run. The dependency pin bump changed the validation schema with zero coverage watching it. Generalized: the worker's runtime dependency set was not represented in the dev environment, so "tests pass" was never a statement about the worker's real dependency graph.
- **Recurrence guard:** Regression test `tests/test_worker/test_max_worker.py::test_group_sync_accepts_pymax_chat_with_set_id_less_sticker` (prod-altitude, runs through `start_group_sync`). Plus an inverted guard, `::test_unmodified_pymax_rejects_sticker_without_set_id`, which shells into a clean interpreter with pristine PyMax and asserts the defect still exists — keeping the RED condition permanently checkable so the shim cannot become silently vestigial, and failing the day the pin moves to a fixed release as the delete signal. Plus the dev-group dependency pin so PyMax compat tests genuinely execute, and the fail-closed version check that raises on any unaudited PyMax version still declaring the field required.
- **Reusable pattern:** When a pinned third-party pydantic model over-declares a field as required and upstream data omits it, relax exactly that one field via a version-pinned, fail-closed, idempotent shim and rebuild every schema embedding the discriminated union — a tagged-union member failure surfaces as a confusing *two*-error message (the member's own missing-field error plus an `UnknownAttachment`-style "should be parsed by its own model" error), which points at the union, not at the fallback type.

---

## max-photo-upload-no-photoids — every MAX send with images failed: "Photo upload URL does not contain photoIds"

- **Date:** 2026-10-08
- **Error patterns:** `Photo upload URL does not contain photoIds`, `KeyError: 'photoIds'`, `pymax/api/uploads/service.py:79`, `UploadError`, `upload_photo`, `Uploading photo` followed by failure within ~60ms, MAX photo ads fail while text-only ads succeed, `iu.oneme.ru/uploadImage?r=`, pymax, maxapi-python
- **Root cause(s):** AND-gated. MAX changed the PHOTO_UPLOAD reply (staged from 2026-09-25, 100% from 2026-10-02) to a one-shot URL `https://iu.oneme.ru/uploadImage?r=<token>` with no `photoIds` query param; pymax (maxapi-python) 2.3.1 `UploadService.upload_photo` unconditionally does `parse_qs(...)["photoIds"][0]` — used only as the key into the POST result — and raises before uploading. 2.4.1 has the same code. Nothing changed on our side (image built 2026-08-26).
- **Fix:** New version-scoped shim `apply_photo_upload_compatibility()` in max_worker/pymax_compat.py replaces `upload_photo` with a 2.3.1 copy differing only in token resolution: `photoIds` present -> keyed lookup as before; absent -> the single entry of the count=1 POST result, UploadError on 0 or >1 entries. Pinned to 2.3.1, fails closed, idempotent; applied at import in max_worker/main.py (log `pymax_photo_upload_compatibility_applied`). Commit 73b9bd98. Upstream: PyMax PR #107 (same approach, unmerged), issue MaxApiTeam/PyMax#108.
- **Files changed:** max_worker/pymax_compat.py, max_worker/main.py, tests/test_worker/test_max_worker.py
- **Why not caught:** External protocol change by MAX; no code or dependency change on our side. Tests fake the MAX socket and upload HTTP, so they cannot observe server-side URL shape changes.
- **Recurrence guard:** `tests/test_worker/test_max_worker.py::test_photo_send_survives_upload_url_without_photo_ids` (drives real pymax send_message -> upload -> MSG_SEND), plus 0/2-entry refusal tests, old-URL keyed-lookup guards, and inverted guard `::test_unmodified_pymax_rejects_upload_url_without_photo_ids` (turns red when pymax is fixed — delete-the-shim signal). Verified live 2026-10-08: post-rebuild MAX photo sends status=ok.
- **Reusable pattern:** When a sudden 100% failure of one MAX feature appears with no deploy on our side, suspect a MAX protocol change: compare send_logs step-change date against image build date, check upstream PyMax PRs/issues, and patch via the same fail-closed version-pinned shim in pymax_compat.py while keeping the old payload shape supported (rollouts are staged).

---

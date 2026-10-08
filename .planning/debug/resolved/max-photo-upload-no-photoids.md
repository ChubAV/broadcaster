---
status: resolved
trigger: |
  DATA_START
  посмотри эти ошибку ВРЕМЯ: 08.10.2026 12:49:23
  КАНАЛ: max
  ГРУППА: 🍀Дома и квартиры без АВИТО Краснодар
  ОБЪЯВЛЕНИЕ: дружелюбный
  ЗАДАЧА: a1455ae2-a2e0-4dbc-a1eb-f0e2f25de270
  ОШИБКА: Photo upload URL does not contain photoIds
  DATA_END
created: 2026-10-08
updated: 2026-10-08
---

# Debug Session: MAX photo upload — "Photo upload URL does not contain photoIds"

## Symptoms

- expected_behavior: Scheduled ad "дружелюбный" (with photo) is delivered to MAX group "🍀Дома и квартиры без АВИТО Краснодар".
- actual_behavior: Send task a1455ae2-a2e0-4dbc-a1eb-f0e2f25de270 failed on 2026-10-08 12:49:23 (channel: max); the failure is shown in the user-facing error notification/history.
- error_messages: `Photo upload URL does not contain photoIds`
- timeline: Not provided by user. Error string is NOT present in repo source — likely raised inside the `maxapi-python==2.3.1` (pymax) library used by `max_worker/` (photo upload path), or relayed from MAX server response. Check prod logs / SendLog for frequency and whether other MAX photo sends succeed.
- reproduction: Not provided. Presumably: schedule an ad with image(s) to a MAX group via MAX account; the max_worker container processes the send task and fails during photo upload.

## Initial evidence (orchestrator)

- `grep -rn photoIds` over repo (excluding node_modules/.git/graphify-out): no hits → message originates outside project code.
- max_worker/requirements.txt pins `maxapi-python==2.3.1`; max_worker/pymax_compat.py already patches pymax attachment behaviour (contact, sticker) — a photo-upload compat patch may be the fix shape.
- Relevant code: max_worker/main.py (process_task, create_client), app/messengers/max.py (MaxMessenger), app/services/image_upload.py.
- Prod access: `just prod-logs [service]` exists; MAX worker containers per account.

## Current Focus

- known_pattern_candidate: "max-group-sync-sticker — pymax 2.3.1 strictness vs. real MAX payload shape" (same library, different code path — analogous fix shape: version-scoped shim in pymax_compat.py)
- bug_class: Bohrbug (deterministic: 100% of photo sends, every retry, both accounts, since Oct 2)
- hypothesis: CONFIRMED — since 2026-09-25 (fully from 2026-10-02) MAX answers PHOTO_UPLOAD with a one-shot URL without a `photoIds` query param (`https://iu.oneme.ru/uploadImage?r=<token>`); pymax 2.3.1 UploadService.upload_photo unconditionally does `parse_qs(urlparse(url).query)["photoIds"][0]` and raises UploadError("Photo upload URL does not contain photoIds") before uploading.
- test: TDD red DONE — tests drive real pymax 2.3.1 MessageService.send_message -> _upload_attachments -> UploadService.upload_photo -> MSG_SEND (after importing max_worker.main via the `worker` fixture, i.e. with all worker shims applied); only MAX socket (`app.invoke`) and upload HTTP (`aiohttp.ClientSession`) are faked.
- expecting: GREEN after shim: MSG_SEND attaches == [{"_type": PHOTO, "photoToken": <token>}]
- next_action: none — resolved 2026-10-08 (owner confirmed photos delivered after max-worker rebuild).
- fix_plan:
    - "max_worker/pymax_compat.py: new apply_photo_upload_compatibility(). Idempotent via marker attr `_broadcaster_photo_upload_patched` on pymax.api.uploads.service.UploadService (return False if set). Fail closed: if PYMAX_VERSION != AUDITED_PYMAX_VERSION raise RuntimeError naming the found version (test sets pymax_compat.PYMAX_VERSION='2.4.1' and expects RuntimeError + '2.4.1' in stderr — so read the module-global PYMAX_VERSION at call time, as the existing shims do)."
    - "Replace UploadService.upload_photo with a reimplementation identical to 2.3.1 (same PHOTO_UPLOAD request UploadPayload(profile=...).model_dump(), same url/validate/read/FormData/POST/status/json/PhotoUploadResponse handling and UploadError messages, use module-level `aiohttp.ClientSession` attribute lookup so tests' monkeypatch applies) EXCEPT token resolution: if urlparse(url).query has photoIds -> keyed lookup model.photos[photoIds[0]] (miss -> UploadError(f'Photo upload response does not contain token for photo_id={photo_id}')); else -> exactly one entry required, else UploadError(f'Photo upload response holds {n} photo(s), expected exactly 1')."
    - "max_worker/main.py: import it, `PHOTO_UPLOAD_COMPATIBILITY_APPLIED = apply_photo_upload_compatibility()` next to the other three, and `if PHOTO_UPLOAD_COMPATIBILITY_APPLIED: log.info(\"pymax_photo_upload_compatibility_applied\")` next to the other compat log lines."
    - "Do NOT touch the pymax pin (2.4.1 has the same defect)."
- reasoning_checkpoint:
    hypothesis: "Every MAX photo send fails because MAX's PHOTO_UPLOAD reply URL no longer carries `photoIds`, and pymax 2.3.1 upload_photo requires that param purely to key into the POST result, raising UploadError before any upload."
    confirming_evidence:
      - "Prod traceback: KeyError 'photoIds' at pymax/api/uploads/service.py:79, ~60ms after 'Uploading photo' (before POST), on task a1455ae2 x4 retries"
      - "send_logs: 0 photoIds fails Sep 18-24 with ~391 ok photo/day; step change on 2026-09-25 06:31 UTC; 0 ok photo since Oct 2; text sends unaffected throughout"
      - "Deployed image (built 2026-08-26) and service.py hash unchanged across the onset -> change is on MAX's side"
      - "Independent upstream report PyMax PR #107 (2026-10-04): official-client capture shows url https://iu.oneme.ru/uploadImage?r=<token> and POST result {'photos': {'0': {'token': ...}}}"
      - "pymax 2.3.1 code: photo_id used only as dict key into PhotoUploadResponse.photos; each Photo uploaded via its own count=1 request"
    falsification_test: "If the shimmed upload still fails in prod after deploy (e.g. POST to the new URL returns non-200, or result has !=1 entries / different shape), the hypothesis that only the photoIds lookup is broken is wrong."
    fix_rationale: "Root cause is the hard dependency on a URL param MAX removed. The fix resolves the token from the upload result itself: by photoIds when MAX still sends it (exact old behaviour), otherwise from the single entry of a count=1 result, failing loudly on 0 or >1 entries. This removes the dependency instead of masking the error."
    blind_spots: "Cannot observe the live new URL in our logs (pymax logs it at DEBUG; workers run INFO) — URL shape comes from upstream capture. Cannot verify the POST to the new URL + MSG_SEND with the resulting token without a live MAX call (prod is read-only for this session) -> human verification after max-worker rebuild. The ~55 ok photo/day Sep 25-Oct 1 suggests staged rollout; old URL shape must stay supported."
    candidate_causes:
      - "code: pymax 2.3.1 upload_photo hard-requires photoIds (confirmed)"
      - "environment: MAX server protocol change removed photoIds from PHOTO_UPLOAD url (confirmed, external trigger)"
      - "config/env on our side: deploy/pin change (eliminated — image unchanged since 2026-08-26)"
      - "data: specific image/ad/group (eliminated — fails pre-upload, all ads/groups, both accounts)"
    and_gate: "yes — both are required: MAX's protocol change (trigger) AND pymax's brittle hard lookup (defect). Either alone would not fail: old URLs worked with pymax; new URLs would work with positional lookup. We can only change our side, so the fix targets the pymax lookup."
- tdd_checkpoint:
    test_file: "tests/test_worker/test_max_worker.py"
    test_name: "test_photo_send_survives_upload_url_without_photo_ids[0|4242] (primary); plus test_photo_album_without_photo_ids_uploads_each_photo_on_its_own_url, test_photo_upload_without_photo_ids_refuses_to_guess_the_token[no-entry|two-entries], test_worker_applies_photo_upload_compatibility_on_import, test_photo_upload_compatibility_is_idempotent_and_fails_closed_on_unaudited_pymax"
    status: "green"
    green_output: "44 passed in ~7s (uv run pytest tests/test_worker/test_max_worker.py -q)"
    failure_output: |
      >           raise UploadError("Photo upload URL does not contain photoIds") from e
      E           pymax.exceptions.UploadError: Photo upload URL does not contain photoIds
      .venv/lib/python3.12/site-packages/pymax/api/uploads/service.py:83: UploadError
      (preceded by E KeyError: 'photoIds' at service.py:79 — identical to the prod traceback)
      7 failed, 37 passed (all 33 pre-existing tests in the file pass)
    guards_green_before_fix: "test_photo_send_still_keys_token_by_photo_ids_when_url_carries_them, test_photo_ids_url_whose_id_is_missing_from_the_result_still_fails (old-URL behaviour must be preserved — kill a 'always positional' mutant), test_unmodified_pymax_rejects_upload_url_without_photo_ids (inverted guard in clean interpreter: pristine pymax still has the defect; fails = delete-the-shim signal)"

## Evidence

- timestamp: 2026-10-08
  checked: .planning/debug/knowledge-base.md
  found: KB match on [pymax, maxapi-python, 2.3.1] -> max-group-sync-sticker. Root cause was pymax 2.3.1 strict schema vs. MAX's real payload (StickerAttachment.set_id required). Fix was version-scoped shim in max_worker/pymax_compat.py, fail-closed on other versions. maxapi-python==2.3.1 is in pyproject dev group so it is installed in .venv.
  implication: pymax source available locally at .venv/lib/python3.12/site-packages/pymax; fix shape precedent exists.

- timestamp: 2026-10-08
  checked: .venv/.../pymax/api/uploads/service.py (pymax 2.3.1)
  found: UploadService.upload_photo invokes Opcode.PHOTO_UPLOAD, takes payload["url"], then `photo_id = str(parse_qs(urlparse(url).query)["photoIds"][0])`; KeyError/IndexError -> logger.exception("Photo upload URL does not contain photoIds") + logger.debug("Invalid photo upload URL=%s", url) + raise UploadError("Photo upload URL does not contain photoIds"). photo_id is later used only to index `PhotoUploadResponse.photos[photo_id].token` after the HTTP POST.
  implication: Error raised BEFORE any bytes are uploaded — it depends only on the URL MAX returns for PHOTO_UPLOAD, not on the image itself. photo_id is only a lookup key into the POST response.

- timestamp: 2026-10-08
  checked: docker logs max-worker-19 (started 09:40 UTC today) — task a1455ae2
  found: task a1455ae2 group -73450518859927 image_count=1 failed 4 times (retry 0..3, 09:42, 09:44, 09:46, 09:49 UTC) with KeyError 'photoIds' at pymax/api/uploads/service.py:79, then task_retries_exhausted + result_published status=fail. Failure is ~60ms after "Uploading photo" (i.e. right after PHOTO_UPLOAD reply, before HTTP POST). In this container 64/64 sending_images attempts failed with this error; 0 photo successes.
  implication: Not a one-off for this ad/group — every photo send on this account fails deterministically.

- timestamp: 2026-10-08
  checked: Loki (172.18.0.6:3100), {container_name=~"max-worker-.*"}, full retained window 2026-10-01 09:00 UTC .. now, paginated (37015 lines)
  found: photo sends OK = 0 on both max-worker-19 and max-worker-28 for every day Oct 1..8. photoIds failures every day on both accounts (e.g. worker-19 ~1408/day, worker-28 ~296/day). Text-only sends succeed every day (worker-19 ~33/day, worker-28 ~128/day). No other pymax upload error messages appear. Failure exists from the first retained log line, so onset predates 2026-10-01.
  implication: Systematic, account-independent, 100% of MAX photo sends fail; session/auth/connection are fine (text works). Points at a change in what MAX returns for PHOTO_UPLOAD vs. what pymax 2.3.1 expects — a protocol-shape issue, not data/env/transient. Bug class: Bohrbug.

- timestamp: 2026-10-08
  checked: prod send_logs (read-only SELECT via web-broadcaster app venv, SET TRANSACTION READ ONLY), messenger_type='max', daily buckets from 2026-09-18
  found: Sep 18-24: ~391 ok photo sends/day, 0 photoIds failures. Sep 25 (first photoIds fail 06:31 UTC): ok photo drops to 56, photoIds fails 381. Sep 25-Oct 1: ~55 ok photo/day vs ~382 fails (staged rollout — some accounts/requests still on old URL). Last ok photo send 2026-10-01 08:15 UTC; Oct 2..8: 0 ok photo, ~426 photoIds fails/day. Total photoIds fails: 5219. Text-only ok steady at ~161/day throughout.
  implication: Onset is an external step change on 2026-09-25 with no deploy correlation needed (text path unaffected, same pymax pin throughout). Fix must accept BOTH URL shapes (old with photoIds — some requests still got it until Oct 1 — and new without).

- timestamp: 2026-10-08
  checked: pymax upstream — PyPI (latest 2.4.1, 2026-08-24) and GitHub MaxApiTeam/PyMax; diffed 2.3.1 vs 2.4.1 uploads/service.py (wheel unpacked in scratchpad, not executed)
  found: 2.4.1 upload_photo has the identical `parse_qs(...)["photoIds"][0]` lookup (only change: request payload adds type=0/uploaderType=0). Open upstream PR #107 (2026-10-04, unmerged): "MAX stopped returning a photoIds query parameter on the photo upload URL ... every photo upload fails ... reported 2026-09-30". Captured official-client exchange: PHOTO_UPLOAD {"count":1} -> {"url": "https://iu.oneme.ru/uploadImage?r=<token>"}; POST -> 200 {"photos": {"0": {"token": "..."}}}. Fix there: read token from the single entry of the result; raise if 0 or >1 entries.
  implication: Upgrading the pin does NOT fix it (2.4.1 has the same defect, no release contains the fix). A compat shim on 2.3.1 is required. External report independently matches our symptom and onset window.

- timestamp: 2026-10-08
  checked: pymax 2.3.1 api/messages/service.py _upload_attachments; api/uploads/models.py
  found: each Photo attachment is uploaded via its own upload_photo call (UploadPayload count=1), sequentially; PhotoUploadResponse = {photos: dict[str, {token}]}. photo_id from the URL is used ONLY as the key into that dict.
  implication: With count=1 the result holds exactly one entry, so positional extraction is exact; multi-image ads (worker passes N Photo objects) remain N independent uploads.

- timestamp: 2026-10-08
  checked: deployed image broadcaster-max-worker:latest (offline `docker run --rm --network none --entrypoint sh`, no prod service touched)
  found: image Created 2026-08-26T12:11Z; pymax 2.3.1; api/uploads/service.py sha256 f3756b98...b2af identical to local .venv copy; pymax_compat has contact/sticker/websocket shims only.
  implication: Worker code and library unchanged since a month before onset (photos sent fine Sep 18-24 with this exact image) -> no deploy/config/env change on our side; the trigger is external (MAX server response shape).

- timestamp: 2026-10-08
  checked: new tests in tests/test_worker/test_max_worker.py, `uv run pytest tests/test_worker/test_max_worker.py -q`
  found: 7 failed / 37 passed. Primary RED test_photo_send_survives_upload_url_without_photo_ids fails with KeyError 'photoIds' at pymax service.py:79 -> UploadError "Photo upload URL does not contain photoIds" (service.py:83) — the exact prod traceback, reached through real pymax MessageService.send_message. Old-URL guards and the pristine-pymax inverted guard pass; all 33 pre-existing tests pass.
  implication: Bug reproduced offline and deterministically at prod altitude; root cause confirmed by test.

- timestamp: 2026-10-08
  checked: GREEN phase — apply_photo_upload_compatibility() in max_worker/pymax_compat.py, wired in max_worker/main.py; `uv run pytest tests/test_worker/test_max_worker.py -q`
  found: 44 passed (was 7 failed / 37 passed at RED). Diff is additive (pymax_compat +213/-1 where -1 is the widened pydantic import; main.py +4).
  implication: Target tests green with no test edits; old-URL guards and pristine-pymax inverted guard still green.

- timestamp: 2026-10-08
  checked: manual mutation pass at fix site (no Stryker/mutmut for Python; 8 hand-seeded mutants, each run against `-k photo` driving tests, file restored from backup after each, cmp-verified)
  found: 8/8 KILLED — M1 accept >1 entries, M2 accept 0 entries, M3 always positional, M4 always keyed, M5 never read photoIds, M6 no idempotency marker, M7 no fail-closed version check, M8 token not taken from result.
  implication: Driving tests assert the root-cause behaviour (token resolution per URL shape), not the symptom.

- timestamp: 2026-10-08
  checked: revert-and-reconfirm — `git stash push -- max_worker/pymax_compat.py max_worker/main.py`, run test file, `git stash pop`, rerun
  found: reverted -> exactly the 7 RED tests fail again (37 passed); reapplied -> 44 passed.
  implication: This change, and only it, fixes the reproduced failure.

- timestamp: 2026-10-08
  checked: offline run inside deployed image broadcaster-max-worker:latest (`docker run --rm --network none`, working-tree max_worker mounted read-only; no prod service touched) — import max_worker.main + UploadService.upload_photo with faked socket/HTTP
  found: IMAGE_CHECK_OK pymax 2.3.1 aiohttp 3.14.3 python 3.12.14 — PHOTO_UPLOAD_COMPATIBILITY_APPLIED True; new URL -> single-entry token, POST to that URL with aiohttp.FormData; old photoIds URL -> keyed token from 2-entry result; 0-entry result -> UploadError "expected exactly 1"; logs still under logger pymax.api.uploads.service.
  implication: Shim imports and behaves correctly against the exact library set the image ships (aiohttp is a declared maxapi-python dependency, so the new top-level import needs no requirements change).

## Eliminated

- hypothesis: Problem specific to this ad's image / this group (data)
  evidence: Error is raised before the image bytes are read or POSTed (service.py:79 precedes validate_photo/read); every photo send on both MAX accounts fails since Oct 2 regardless of ad/group; text sends to the same groups succeed.
  timestamp: 2026-10-08

- hypothesis: Our deploy / pymax pin change introduced it (environment/config)
  evidence: Deployed max-worker image built 2026-08-26, unchanged; identical service.py hash; photo sends succeeded with that image through Sep 24 (~391/day).
  timestamp: 2026-10-08

- hypothesis: Upgrading pymax to latest (2.4.1) fixes it
  evidence: 2.4.1 upload_photo contains the same `parse_qs(...)["photoIds"][0]` lookup; fix exists only in unmerged upstream PR #107.
  timestamp: 2026-10-08

- hypothesis: Transient / session-startup issue (MAX not ready right after connect)
  evidence: Failures persist for days across reconnects, 100% rate, 4 spaced retries (15s/60s/180s) all fail identically; text path on the same session works.
  timestamp: 2026-10-08

## Resolution

- root_cause: MAX changed its PHOTO_UPLOAD reply (staged from 2026-09-25, complete by 2026-10-02) to a one-shot upload URL without a `photoIds` query parameter; pymax 2.3.1 UploadService.upload_photo unconditionally parses `photoIds` from that URL (only to key the POST result) and raises UploadError("Photo upload URL does not contain photoIds") before uploading — so 100% of MAX sends with images fail; latest pymax 2.4.1 has the same defect.
- fix: New version-scoped shim `apply_photo_upload_compatibility()` in max_worker/pymax_compat.py replaces pymax 2.3.1 `UploadService.upload_photo` with a line-for-line copy whose only change is token resolution (`_resolve_photo_token`): URL with `photoIds` -> exact 2.3.1 keyed lookup (missing id still UploadError); URL without it -> token of the single entry of the count=1 POST result, UploadError("Photo upload response holds N photo(s), expected exactly 1") on 0 or >1. Idempotent via `UploadService._broadcaster_photo_upload_patched`; fail-closed RuntimeError on any pymax != 2.3.1. Wired in max_worker/main.py as `PHOTO_UPLOAD_COMPATIBILITY_APPLIED` with startup log `pymax_photo_upload_compatibility_applied`. pymax pin untouched.
- oracle_type: derived (protocol contract) — PHOTO_UPLOAD is requested with count=1 and yields a single-entry `photos` result whose token must reach MSG_SEND attaches as {"_type": "PHOTO", "photoToken": ...}; contract taken from pymax 2.3.1's own models/_upload_attachments plus the official-client capture in upstream PR #107. Assertions check the token that reaches MSG_SEND and the URL POSTed to, not "no exception".
- boundary_neighbors: result entries 0 / 1 / 2 around "exactly one" (no-entry, two-entries rejected; one accepted); single-entry key "0" vs arbitrary "4242"; URL with photoIds (keyed lookup kept, even with 2 entries) vs without; photoIds present but missing from result (still an error, no positional fallback); album of 2 = 2 independent count=1 uploads in order.
- verification:
    target_test: { result: pass, detail: "tests/test_worker/test_max_worker.py 44 passed (RED was 7 failed / 37 passed)" }
    mutation_check: { result: pass, tool: "manual (no Stryker/mutmut for Python) — 8 hand-seeded mutants at fix site", mutant_killed: "8/8" }
    no_op_deletion: { result: pass, deletion_justified_by_rca: n/a, detail: "additive diff; no branch removed, no assertion weakened, tests not edited in green phase" }
    adjacent_tests: { result: pass, suites_run: ["tests/ full suite: 4095 passed, 2 skipped, exit 0 (42m54s, uv run pytest tests/ -q)"] }
    revert_and_reconfirm: { result: pass, bug_returned_on_revert: true, fixed_on_reapply: true }
    image_offline_check: { result: pass, detail: "broadcaster-max-worker:latest libs (pymax 2.3.1, aiohttp 3.14.3), --network none, prod untouched" }
    live_max_send: { result: pass, detail: "2026-10-08 max-worker image rebuilt from 73b9bd98; max-worker-19 logs pymax_photo_upload_compatibility_applied; tasks 545fdf1c (1 image) and 3bee97f2 (2 images) -> send_logs status=ok; 0 MAX failures after container start 11:19:33 UTC (last photoIds failure 11:10:58 UTC on old image)" }
    human_verify: { result: confirmed, owner_words: "фото дошли, закрывай сессию", at: 2026-10-08 }
    guardrail_verdict: accepted
- files_changed: [max_worker/pymax_compat.py, max_worker/main.py, tests/test_worker/test_max_worker.py]
- commit: 73b9bd98 "fix(max-worker): upload photos to MAX URLs that no longer carry photoIds" (pushed to origin/master 2026-10-08)
- upstream: issue MaxApiTeam/PyMax#108 filed 2026-10-08 (links unmerged PR #107). Delete the shim when the pin moves to a fixed release — `test_unmodified_pymax_rejects_upload_url_without_photo_ids` turns red as the signal.

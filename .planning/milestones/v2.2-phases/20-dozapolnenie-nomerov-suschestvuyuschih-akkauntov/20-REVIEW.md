---
phase: 20-dozapolnenie-nomerov-suschestvuyuschih-akkauntov
reviewed: 2026-11-23T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - justfile
  - scripts/backfill_account_phones.py
  - tests/test_scripts/test_backfill_account_phones.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
  necessity: 0
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-11-23
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

I reviewed the backfill script, its test file and the two new `justfile` recipes. I read the call targets the script depends on: `fill_reported_phone`, the WA and MAX container managers, `TelegramClient`/Telethon error classes, the Celery task routing and dispatch code, and `manage_wa_containers`/`manage_max_containers`. I ran the test file under the orchestrator flock: 155 passed. ruff and pyflakes are not installed in the environment, so no lint was run.

The core safety properties hold.
- The only write path is `fill_reported_phone`, with one session and one commit per account.
- Dry-run never reaches the writer. It predicts the outcome with read-only `exists()` queries.
- Selection reads columns, not ORM entities.
- Only exception class names reach the output.
- Phone numbers are printed only through `mask_phone`.
- Telegram is polled sequentially, with the busy probe failing closed and `disconnect` in `finally`.
- The Telegram client is built with `receive_updates=False` and nothing from the session is written back.

I found no Critical issues. The defects are in the `--wake` stop path, in how it interacts with the real container managers, and in the usability of the staged rollout the docstring prescribes. The tests model the container manager's failure mode differently from how the real one fails, so they cannot see WR-01.

## Warnings

### WR-01: A failed container stop is silent. The script ignores `stop_container`'s return value.

**File:** `scripts/backfill_account_phones.py:431-438`
**Issue:** The real `wa_container_manager.stop_container` and `max_container_manager.stop_container` catch `APIError` themselves and return `False`. Only `NotFound` (returns `True`) and success (returns `True`) are otherwise reported. They never raise on an API failure (`app/services/wa_container_manager.py:85-100`, `app/services/max_container_manager.py:94-109`). `_stop_if_idle` does `await asyncio.to_thread(self._stop, account_id)`, discards the result, and returns `""`. So when Docker refuses the stop, which is the one failure the manager actually reports, the account's line carries no "контейнер оставлен" note. The operator is told nothing, and a woken WA/MAX worker with a live session stays up. It then only dies via its own `IDLE_SHUTDOWN_SEC=300`. The docstring promises `just wa-workers` / `just max-workers` guidance for exactly this case.

The test `test_wake_stop_failure_keeps_the_number_and_names_the_container` (test file `:1457-1476`) models the failure as `raise RuntimeError`. That is not how the real manager fails, so the suite passes while the real path is untested.

**Fix:**
```python
try:
    stopped = await asyncio.to_thread(self._stop, account_id)
except Exception as exc:
    return f"контейнер оставлен: остановка не удалась ({type(exc).__name__}), проверьте just wa-workers / just max-workers"
if stopped is False:
    return "контейнер оставлен: остановка не удалась, проверьте just wa-workers / just max-workers"
return ""
```
Add a test whose stop double returns `False`, matching the real contract.

### WR-02: "Queue is empty" is used as proof of "worker is idle". A task already popped by the worker is killed mid-send.

**File:** `scripts/backfill_account_phones.py:418-438` (also the pre-wake check at `:359-368`)
**Issue:** `_stop_if_idle` stops the container whenever `LLEN {kind}:queue:{id} == 0`. During the wake window the script keeps a worker up for up to 90 s (WA) or about 120 s (MAX: 30 s of health wait plus 45 polls at 2 s). If the schedule dispatcher pushes a task for this account in that window, the worker is already up and pops it at once. `manage_wa_containers` / `manage_max_containers` then run `start_container`, which sees a running container and leaves it. The queue reads 0, the script's check passes, and `container.stop(timeout=10)` kills a worker that is mid-send. The send is lost, or sent without its result being recorded. A zero queue length says nothing about in-flight work. The check in `_wake` has the same blind spot: it cannot see a task the worker is processing.

**Fix:** Do not infer idleness from `LLEN` alone. Options: re-check after a short grace period, or require an observable "worker idle" signal (the `/status` body or the `{kind}:heartbeat:*` keys). At minimum, document the residual window and have `_stop_if_idle` keep the container whenever the account was dispatched to during the wake. For example, compare `{kind}:active_accounts` membership taken before and after.

### WR-03: The script can stop a container it did not start (D-16 violated in a small window).

**File:** `scripts/backfill_account_phones.py:371-387`
**Issue:** `_wake` checks `_running_now` and then calls `_start` as two separate steps. `start_container` returns the endpoint of an already-running container without distinguishing "created by me" from "found existing". `max_container_manager.start_container` additionally returns the endpoint on a Docker 409 "name conflict", meaning another process created it a moment earlier. In both cases the script sets `started = True` and the `finally` block stops a container that someone else (beat, a user action, a concurrent run) started. D-16 and the docstring say "stopped only if this script started it". The empty-queue check in `_stop_if_idle` narrows this window but does not close it.

**Fix:** Establish ownership from fact, not from the return value. For example, re-read the container list or `get_container_endpoint` immediately before `_start` and treat a pre-existing container as not ours. The window cannot be closed without changing the manager, so the alternative is to document it as a known limit and keep the empty-queue guard.

### WR-04: The staged-rollout instruction (`--limit`) cannot make progress past unfillable accounts.

**File:** `scripts/backfill_account_phones.py:182-209`, docstring `:44-50`
**Issue:** The docstring tells the owner to "run in portions (`--type`, `--account-id`, `--limit`)". The `--limit` selection is `ORDER BY id LIMIT n` over accounts that still have no number. Accounts that end in "номера нет", "воркер недоступен", "сессия мертва" or "занят" are not written, so they remain candidates. Every `--limit 20` run re-polls the same first 20 stubborn accounts, and the later accounts are never reached. For Telegram this means repeated connections to the same dead sessions. There is no `--after-id`/offset or "skip already attempted" option, so a portioned rollout stalls on the first batch of failures.

**Fix:** Add `--after-id N` (`MessengerAccount.id > N`), and print the last processed id in the summary so the next run can resume. Or document that `--limit` is for smoke-testing only and portions must be cut with `--account-id`.

## Info

### IN-01: The FloodWait wait time is not honoured; the next account is polled after a fixed 1 s.

**File:** `scripts/backfill_account_phones.py:529-531, 537-538`
**Issue:** `FloodWaitError` is mapped to "воркер недоступен" and the loop moves to the next account after `TELEGRAM_PAUSE = 1.0`. The server's demanded wait (`exc.seconds`) is dropped. Further polls then go out under the same `api_id` while a flood wait is in force. The code comment says the pause exists "against FloodWait", but a fixed 1 s does not respond to an actual one.
**Fix:** On `FloodWaitError`, either abort the Telegram kind for this run (record the rest as "источник недоступен") or `await asyncio.sleep(min(exc.seconds, cap))` before the next account.

### IN-02: `--wake` has no guard against being run outside the production container.

**File:** `scripts/backfill_account_phones.py:775-805`, `justfile:177-183`
**Issue:** Telegram is protected from a local `.env` that points at the production database (`TelegramOutsideContainerSource`). `--wake` is not. `just backfill-phones --wake` with such a `.env` uses the local Docker daemon. It starts worker containers with the production `REDIS_URL` and an empty local sessions volume. Those workers would consume production queues or ask for a new QR. Locally the container list is also empty, so the default path just reports "воркер не запущен" for every account. The docstring warns only about 401/403/405.
**Fix:** Take `--wake` only together with `--telegram-from-container` (rename it to something like `--in-container`), or refuse `--wake` when that flag is absent.

### IN-03: The Telegram busy probe covers Celery sends only. There is also a probe-to-connect gap.

**File:** `scripts/backfill_account_phones.py:499-509, 597-635`
**Issue:** "Busy" is derived only from `send_telegram_message` tasks. Other holders of the same Telegram session are invisible to it. One example is `TelegramUserMessenger` in the web process (`app/pages/accounts.py:1339`). The probe-to-connect gap is also unguarded: a send can be dispatched between `busy is False` and `client.connect()`, and there is no re-check. The cost of such a collision is the revoked authorization key the code comments describe as irreversible. Both gaps are small, and fail-closed handling elsewhere in the probe is thorough. They should be named in the docstring's rollout notes (run in a window without sends; no one working in the accounts page).
**Fix:** Document both limits. Optionally re-run the probe immediately before `connect()`.

### IN-04: Minor hygiene in selection and source construction.

**File:** `scripts/backfill_account_phones.py:189-209, 782-805`
**Issue:**
- `select_candidates` loads `credentials` for every kind, though only `tg_user` needs it. Session strings and MAX/WA credentials for all candidates sit in memory for the whole run.
- `build_sources` creates a sync `redis.Redis` that is never closed.
- The Celery app, whose import reads settings, is created even in dry-run.

None of these is incorrect.
**Fix:** Select `credentials` only when `tg_user` is among the kinds (otherwise `literal(None)`). Close the Redis client in `amain`'s `finally`.

---

_Reviewed: 2026-11-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

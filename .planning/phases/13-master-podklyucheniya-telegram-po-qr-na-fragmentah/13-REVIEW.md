---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
reviewed: 2026-09-21T17:40:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - app/messengers/telegram_user.py
  - app/pages/accounts.py
  - app/templates/accounts/connect_tg_user.html
  - app/templates/accounts/includes/tg_connect_step.html
  - tests/test_messengers/test_telegram_user.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_impersonation_gate.py
  - tests/test_routes/test_tg_user_auth.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_htmx_markup_security.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-09-21T17:40:00Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

I reviewed the phase diff (`2579930882^..HEAD`) for the session layer, the four converted handlers, the step template and the gate/registry tests.

The main claimed properties hold when read against the source:
- `_owned` runs before every `pop`, `cancel`, `recreate` and `sign_in`.
- A foreign `session_id` gets the same `gone` response as an unknown one.
- `complete_auth` has no `await` between the status/ownership check and the `pop`, and callers reach it with no yield after the check.
- `refresh_qr` is limited to `qr_expired` within `QR_SESSION_TTL`.
- The session and the account are bound to the subject under impersonation.
- The 2FA password is never put in the template context, and the `field` macro renders `value=""`.
- The poller exists only in the `waiting` branch and targets the anchor. The anchor itself has no trigger.
- Autoescape covers every reflected value, including the attacker-controlled `session_id` that is echoed back on the 422 password step.

I found no critical defects. The four warnings are:
- The "recreate only from `qr_expired`" guard is check-then-await and does not hold under concurrency.
- The new `asyncio.TimeoutError` branch catches timeouts after the scan and reports them as "code expired".
- The scan result is destroyed before the DB commit that persists it.
- A route race test passes against the exact defect it names. I confirmed this by running mutants.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `refresh_qr` "only from `qr_expired`" guard is check-then-await — concurrent refreshes both recreate

**File:** `app/messengers/telegram_user.py:162-178`
**Issue:** The status guard (`if state.status != "qr_expired": return None`) runs before `await state.qr_login.recreate()`. The status only changes to `"waiting"` after that await returns. Two refresh requests from the owner can both pass the guard and both call `ExportLoginTokenRequest`. Possible sources are two tabs, a no-JS resubmit, or a replayed form. The disabled button only protects one htmx tab.

The second request to resume overwrites `qr_login._resp`, cancels the first request's freshly created wait task, and starts its own. The two HTTP responses carry different QR images, and whichever arrives last is rendered. The user can end up looking at a code that the running wait task no longer times against. So the layer invariant that the docstring and D-03 rely on ("пересоздание пускается ТОЛЬКО из «код истёк»") does not hold under concurrency. `complete_auth` defends against the same race by avoiding any await, but `refresh_qr` has no equivalent.
**Fix:** Claim the transition before awaiting, and roll it back on failure:
```python
if state.status != "qr_expired":
    return None
if time.time() - state.created_at > QR_SESSION_TTL:
    return None
state.status = "refreshing"          # claimed synchronously, no await before this line
try:
    await state.qr_login.recreate()
except Exception as e:
    state.status = "qr_expired"      # let the owner retry
    logger.error("qr_refresh_error", session_id=session_id, error=str(e))
    return None
state.status = "waiting"
state.created_at = time.time()
...
```
`get_qr_status` would report `refreshing` to a concurrent poll. The qr-status handler's fall-through would then show "Ошибка авторизации", so map `refreshing` to the 204 "unchanged" branch as well. Add a unit test that gathers two `refresh_qr` calls against a `recreate` that yields, and asserts `recreate.await_count == 1`.

### WR-02: The `asyncio.TimeoutError` branch reports a post-scan timeout as "code expired"

**File:** `app/messengers/telegram_user.py:93-101`
**Issue:** `QRLogin.wait()` (telethon `tl/custom/qrlogin.py`) does more than wait for the token event. After `UpdateLoginToken` fires, it sends `ExportLoginTokenRequest` again. On `LoginTokenMigrateTo` it also calls `self._client._switch_dc(...)`, which reconnects through telethon's connection layer with `asyncio.wait_for(..., timeout)`. A connect timeout there is also an `asyncio.TimeoutError`.

The new branch catches every `TimeoutError` from the whole call. So a user who already scanned, and whose account lives on another DC, sees "QR-код истёк" instead of an error. They then press "Обновить", which calls `recreate()` on a client in a half-switched DC state. The comment says a `wait()` timeout means the code expired. That is only true for the timeout of the event wait, not for timeouts after the event.
**Fix:** Separate "the token expired" from "a timeout happened". The simplest check uses the token's own deadline:
```python
except asyncio.TimeoutError:
    expires = getattr(state.qr_login, "expires", None)
    if expires is not None and datetime.now(timezone.utc) >= expires:
        state.status = "qr_expired"
    else:
        state.status = "error"
        state.error = "Таймаут соединения с Telegram"
        logger.error("qr_auth_error", session_id=session_id, error="timeout after scan", exc_info=True)
```
Add a test where `wait()` raises `asyncio.TimeoutError` while `expires` is still in the future, and assert `status == "error"`.

### WR-03: The scan result is destroyed before the commit that persists it

**File:** `app/pages/accounts.py:410-414`, `app/pages/accounts.py:573-577`, `app/pages/accounts.py:276-293`
**Issue:** Both save paths call `complete_auth` first. It `pop`s the state, cancels the wait task, disconnects the client, and returns the only copy of `session_string`. `_save_tg_account` runs after that and does `db.add` + `await db.commit()`.

If the commit fails, the exception bubbles up as a 500 and the session string is gone. Possible causes are a DB outage, a constraint error, or cancellation of the request mid-commit. By then the Telegram account already has a live authorization for this app's client, which appears in the user's Telegram device list. That authorization is orphaned, and the user sees the generic failure banner instead of a step.

Popping before persisting is what gives "one scan, one account" (Pitfall 3). Keep it, but the failure path needs handling. This helper was written in this phase and is the single write site for both paths, so the gap is in scope.
**Fix:** Catch the failure around the save and answer with the error step, not a 500. Also log the failure without the session string:
```python
if session_string:
    try:
        await _save_tg_account(db, user, session_string)
    except Exception as e:
        await db.rollback()
        structlog.get_logger().error("tg_account_save_failed", error_type=type(e).__name__)
        error = TG_AUTH_FAILED_MESSAGE
    else:
        step, error = "connected", None
```
Optionally, on failure, log out the orphaned authorization with a short-lived `TelegramClient(StringSession(session_string), ...)` calling `log_out()`.

### WR-04: The route-level poll race test passes against the defect it names

**File:** `tests/test_routes/test_tg_user_auth.py:1325-1352` (also `1271-1322`)
**Issue:** `test_two_concurrent_polls_after_success_save_one_account` claims to cover D-01 ("два конкурентных опроса после успеха — ОДИН аккаунт"). It has no rendezvous, so the second request is still inside `get_user_from_cookie` / `request.form()` when the first request finishes `complete_auth`. It sees `gone` and never races.

I measured this with a pytest plugin that swaps `complete_auth` in both `app.messengers.telegram_user` and `app.pages.accounts` for mutants:
- With `await asyncio.sleep(0)` between the check and the `pop`, the poll race test passes and only the 2FA test fails.
- With `await state.client.disconnect()` moved before the `pop`, **both** route race tests pass on three runs out of three. The 2FA test's `_seed_2fa_state` client is a bare `AsyncMock`, whose `disconnect` never yields, so the reordering is invisible to it.

The unit test `test_concurrent_completes_yield_one_session_string` does catch the reorder mutant. So the property is guarded, but by the unit test only. The two route tests add no discriminating power while their docstrings claim they do. That is the vacuous-green pattern the project's gates are built to reject.
**Fix:**
- In the poll race test, make both requests reach `get_qr_status` before either reaches `complete_auth`. One way is to patch `app.pages.accounts.get_qr_status` with a wrapper that counts entries and awaits an `Event` set by the second entry, as `sign_in` does in the 2FA test. Then assert `entered == 2`.
- In `_seed_2fa_state`'s race use, give `client.disconnect` a yielding side effect (`async def _d(): await asyncio.sleep(0)`), so the reorder mutant reddens there too.

## Info

### IN-01: `ValueError` / `RuntimeError` branches in verify-2fa also catch unrelated telethon errors and echo their text

**File:** `app/pages/accounts.py:563-567`; `app/messengers/telegram_user.py:193-198`
**Issue:** `submit_2fa` maps only `PasswordHashInvalidError` to `ValueError`. However, telethon's `sign_in(password=...)` can itself raise `ValueError`: `pwd_mod.compute_check` rejects bad server parameters. The handler would show that internal English text at the password field as a 422. The `RuntimeError` branch is also effectively dead for its intended purpose. The handler checks ownership synchronously just before `submit_2fa`, so the layer's refusal cannot fire there. Only a stray `RuntimeError` from telethon/asyncio can reach it, and its raw text would be rendered.
**Fix:** Raise a dedicated exception type from `submit_2fa` (for example `class WrongPassword(ValueError)`) and catch only that at the field. Let other exceptions fall through to the logged generic branch, which shows `TG_AUTH_FAILED_MESSAGE`.

### IN-02: `submit_2fa` does not enforce `needs_2fa` at the layer, unlike its sibling functions

**File:** `app/messengers/telegram_user.py:186-202`
**Issue:** `complete_auth` enforces `success` and `refresh_qr` enforces `qr_expired` inside the layer, and the phase documents both as layer invariants. `submit_2fa` relies only on the handler's `get_qr_status` check. Any future caller could send a password against a `waiting`/`success` session and flip `status` to `success`.
**Fix:** Add `if not state or state.status != "needs_2fa": raise RuntimeError(...)` next to the `_owned` check.

### IN-03: Abandoned sessions keep a connected (possibly authorized) telethon client

**File:** `app/messengers/telegram_user.py:48-54`; `app/pages/accounts.py:334-338`
**Issue:** Several paths leave a session in `_qr_sessions` with a connected client, including an authorized one after a late scan: each "Начать заново", every no-JS `start-qr` (acknowledged in the docstring), and every terminal error step. `_cleanup_expired_sessions` later cancels the task but never disconnects. This predates the phase, and D-13 intentionally bounds changes to this function. I note it here so the owner-accepted residual window (scan, then close the tab) is known to also leave a live Telegram authorization.
**Fix:** (Deferred per D-13.) When the session layer is next opened, disconnect in `_cleanup_expired_sessions` and drop the caller's previous session in `start_qr_auth`.

---

_Reviewed: 2026-09-21T17:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

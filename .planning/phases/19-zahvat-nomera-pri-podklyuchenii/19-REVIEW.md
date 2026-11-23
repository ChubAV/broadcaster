---
phase: 19-zahvat-nomera-pri-podklyuchenii
reviewed: 2026-11-23T00:00:00Z
depth: standard
files_reviewed: 21
files_reviewed_list:
  - app/application/accounts/connect_phone.py
  - app/messengers/base.py
  - app/messengers/max.py
  - app/messengers/telegram_user.py
  - app/messengers/whatsapp.py
  - app/pages/accounts.py
  - app/templates/accounts/includes/max_connect_step.html
  - justfile
  - max_worker/main.py
  - tests/test_application/test_connect_phone.py
  - tests/test_messengers/test_max.py
  - tests/test_messengers/test_telegram_user.py
  - tests/test_messengers/test_whatsapp.py
  - tests/test_pages/test_connect_phone_capture.py
  - tests/test_pages/test_max_connect_transport.py
  - tests/test_routes/test_tg_user_auth.py
  - tests/test_wa_worker_deployment.py
  - tests/test_worker/test_max_worker.py
  - tests/test_worker/test_wa_worker_own_phone.py
  - wa_worker/index.js
  - wa_worker/own_phone.js
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-11-23
**Depth:** standard
**Files Reviewed:** 21
**Status:** issues_found

## Summary

Reviewed the Phase 19 diff (`4ca2f7dd..HEAD`, planning artifacts excluded). Application code, the WA/MAX worker changes and the tests were read in full for the changed regions. The phase's own test files for the application helper, page handlers, MAX/WA messengers (91 tests) pass.

Checked and found sound:
- `@whiskeysockets/baileys@7.0.0-rc14` really exports `isPnUser` and `jidDecode` from the package root (`lib/index.js` -> `WABinary/index.js`; `jid-utils.js:30,65`). `sock.user` is a live getter (`socket.js:931`). The new named ESM import therefore cannot crash worker start-up.
- PyMax 2.3.1: `client.me` is a `Profile`, `me.contact.phone` is `int | None`, and `me` is set before `on_start` fires. `ExtraConfig.url` exists. `own_phone_of` matches the library.
- `expire_on_commit=False`, so `account.id` after `commit()` in `_save_tg_account` is safe.
- The WA/MAX handlers read `account.id` and `account.credentials` before the savepoint can expire the instance. The post-rollback assignments to `credentials` and `status` do not need a lazy load.
- The writer's UPDATE uses `synchronize_session=False`, and the later ORM flush touches only `credentials` and `status`, so the captured phone is not overwritten.
- Number values are kept out of logs on every new path.

No security vulnerabilities or crashes were found. One robustness defect (WR-01) and three minor items follow.

## Warnings

### WR-01: Telegram QR path has no savepoint, so a phone-capture DB failure loses the already-consumed session (D-05 not honoured)

**File:** `app/pages/accounts.py:326-335` (called from `:453-455` and `:616-618`)
**Issue:** WA and MAX capture goes through `capture_connect_phone`, which wraps the writer in `begin_nested()` and swallows failures so that the connection is never broken (D-05). `_save_tg_account` instead calls `record_reported_phone(db, account, result.phone)` bare, in the same transaction as the account INSERT. The docstring justifies this only by "a loud `ValueError` for an account outside the session must stay loud". That `ValueError` cannot occur here, because the account was `db.add`-ed two lines earlier. Any other failure inside the writer is a database error: deadlock, connection loss, the `phone` CHECK/guard, or the `phone_guard`. It propagates as a 500, and the INSERT of the account rolls back with it.

By then `complete_auth` has already popped and disconnected the Telegram session, so the session string is gone. On the QR path the user must rescan. On the 2FA path the user must also re-enter the password. Telegram has by then created an authorization for the aborted login, and the Telegram-side session is orphaned.

The design intent (phone is best-effort, connection must survive) is applied to two of the three connect flows only.
**Fix:** Take the savepoint here too, while keeping the programmer-error `ValueError` loud:
```python
db.add(account)
await db.flush()  # account.id is known; INSERT is in the outer transaction
try:
    async with db.begin_nested():
        outcome = await record_reported_phone(db, account, result.phone)
except ValueError:
    raise
except Exception as exc:
    logger.warning("tg_phone_capture_failed", account_id=account.id, error_type=type(exc).__name__)
    outcome = None
await db.commit()
```
Alternatively reuse `capture_connect_phone(db, account.id, result.phone)` after `flush()`. It already provides the savepoint, the swallow and the PHONE-21-safe log.

## Info

### IN-01: `QrAuthResult` hides the phone from `repr` but prints the Telegram session string

**File:** `app/messengers/telegram_user.py:174-184`
**Issue:** `phone` is `field(repr=False)`, but `session_string` is a default dataclass field. `repr(QrAuthResult(...))` or `"%r"` in a log line or traceback frame prints a full Telegram account credential. Nothing logs it today, and the new test `test_the_number_stays_out_of_the_state_and_result_repr` asserts only the phone. Before this phase `complete_auth` returned a bare `str`, so the type change introduces the possibility. `QRAuthState.session_string` already has the same property, so this is an extension of an existing hazard rather than a new class.
**Fix:** `session_string: str = field(repr=False)`, and extend the repr test to assert the session string is absent as well.

### IN-02: `get_own_phone` is duplicated verbatim in `WhatsAppMessenger` and `MaxMessenger`

**File:** `app/messengers/whatsapp.py:145-163`, `app/messengers/max.py:135-153`
**Issue:** The two bodies are identical apart from the docstring: GET `status`, 200 check, `reported_phone_from_status`, and the same swallow and log. The shared parsing already lives in `base.py`, so the transport half drifting in one class (for example a changed timeout or log key) is a latent inconsistency.
**Fix:** Move the method to a mixin or a helper in `base.py`, such as `async def fetch_own_phone(client, url, log)`, and let both messengers delegate to it.

### IN-03: A typed MAX number is stored as an automatic number and is never self-correcting (owner-decided residual)

**File:** `app/pages/accounts.py:1038-1055` (with `app/application/accounts/connect_phone.py:74-75`)
**Issue:** When MAX reports nothing (an old worker image, or `me.contact.phone` empty), the number typed in the form is written through `fill_reported_phone`. It is stored with `phone_is_manual = False`, so it looks like a MAX-reported number. Because automatic sources fill only a NULL phone, a typo or someone else's number can never be corrected by the Phase 20 backfill or a later reported value. Only an explicit manual edit fixes it. This follows owner decision OQ1/D-10 and is documented, so it is not a defect in the implementation. The only code-level inconsistency is that `max_worker/main.py:213-216` says a typed number "must not pass for a reported one", while the app side deliberately does exactly that. Aligning the two comments avoids misleading the next reader.
**Fix:** No code change needed unless the owner revisits OQ1. Reword the worker comment to say only that the *worker* never serves the form number. Optionally record the "typed number is not auto-correctable" consequence in the Phase 20 notes.

---

_Reviewed: 2026-11-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

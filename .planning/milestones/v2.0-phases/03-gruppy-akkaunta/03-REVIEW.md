---
phase: 03-gruppy-akkaunta
reviewed: 2026-08-13T00:00:00Z
depth: standard
files_reviewed: 50
files_reviewed_list:
  - alembic/versions/0014_sync_result_and_group_missing.py
  - app/application/accounts/dto.py
  - app/application/accounts/group_resync.py
  - app/application/scheduling/use_cases.py
  - app/domain/repositories.py
  - app/main.py
  - app/models/group.py
  - app/models/messenger_account.py
  - app/pages/__init__.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/groups.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/group_row.html
  - app/templates/account_groups/list.html
  - app/templates/account_groups/partial_cards.html
  - app/templates/account_groups/partials/sync_result.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/components/modal.html
  - app/worker/tasks.py
  - tests/conftest.py
  - tests/test_application/test_account_deletion_schedules.py
  - tests/test_application/test_collect_due_inactive_group.py
  - tests/test_application/test_group_resync.py
  - tests/test_e2e.py
  - tests/test_migrations/test_0013_ad_status.py
  - tests/test_migrations/test_0014_sync_result_columns.py
  - tests/test_models/test_sync_result_columns.py
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedules_detached_account.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_history.py
  - tests/test_routes/test_limits.py
  - tests/test_routes/test_schedules.py
  - tests/test_routes/test_schedules_api_null.py
  - tests/test_routes/test_schedules_api_ownership.py
  - tests/test_routes/test_schedules_toggle_detached.py
  - tests/test_routes/test_sync_groups.py
  - tests/test_templates/test_components.py
  - tests/test_worker/test_tasks.py
findings:
  critical: 3
  warning: 8
  info: 8
  total: 19
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-08-13
**Depth:** standard
**Files Reviewed:** 50
**Status:** issues_found

## Summary

The phase's central refactor — collapsing three copies of group re-inventory into
`app/application/accounts/group_resync.py` and pointing the page handler plus both
Celery tasks at it — is sound in shape and unusually well argued in-comment. The
in-process sync claim (`_SYNC_IN_FLIGHT`) added by 03-09 is correctly paired: the
claim sits after the ownership check, and the `finally` covers all four handler
exits including the `IntegrityError` branch where the session is unusable. Four
negative tests in `tests/test_routes/test_sync_groups.py` prove each exit releases
the slot. The modal double-submit guard is inherited by all seven consumers and is
enforced two-way by `test_modal_guard_is_inherited_by_every_consumer`.

The defects are on the edges the phase did not re-open:

1. **The T-03-17 mitigation (no internal detail in user-visible summaries) is
   provably incomplete.** The broad `except` was hardened to a fixed string; the
   narrow `MessengerFetchError` branch was left writing the exception verbatim on
   the premise that narrow-branch texts are "ours and controlled". They are not —
   one of the two constructions in the adapters embeds a raw third-party exception.
2. **`accounts_retry_sync` — the *other* route that starts a sync — received none
   of the hardening.** No re-entrancy guard, no error handling, unbounded Celery
   task spawn from a single authenticated form POST.
3. **The Telegram QR auth session is not bound to a user.** Four endpoints accept
   a `session_id` from the client with only an is-logged-in check, and one of them
   persists the resulting Telegram session string as the *caller's* account.

Two whole-file rewrites (`app/pages/groups.py` shim, `app/domain/repositories.py`
Protocol removal) are clean: the deleted `GroupRepository` Protocol and
`app/repositories/group.py` have no remaining references anywhere in `app/`,
`tests/` or `scripts/` (`app/pages/admin.py` imports `GroupInfoRepository`, a
different class). Migrations 0014/0015 are correct on both dialects, including the
`CASE`-instead-of-`MIN(boolean)` and `false`-instead-of-`0` details.

## Critical Issues

### CR-01: Narrow sync-failure branch writes an uncontrolled third-party exception string to the user-visible summary (T-03-17 hole)

**File:** `app/pages/accounts.py:900-912`
**Issue:**
The broad `except Exception` immediately below was hardened to write
`UNEXPECTED_FAILURE_MESSAGE`, with a comment stating "Тексты УЗКИХ веток
(`MessengerFetchError`, состояние моста, таймаут) остаются своими — они
формируются нами и подконтрольны"
(`app/application/accounts/group_resync.py:90-92`). That premise is false for one
of the two `MessengerFetchError` constructions:

```python
# app/messengers/whatsapp.py:128-130  (identical at app/messengers/max.py:118-120)
except Exception as e:
    self.log.error("get_groups_error", error=str(e), exc_info=True)
    raise MessengerFetchError(f"{type(e).__name__}: {e}") from e
```

`e` here is whatever `httpx` raises against `self._url("groups")` — the internal
per-account worker endpoint resolved from Redis. `httpx.UnsupportedProtocol`,
`httpx.InvalidURL`, `httpx.ProxyError` and `httpx.RemoteProtocolError` all embed
the request URL in `str(e)`. The handler then does:

```python
await record_sync_failure(db, account, str(e) or e.__class__.__name__)
```

and `app/templates/account_groups/list.html:116-117` renders it verbatim:

```jinja
{{- alert('Синхронизация не удалась: ' ~ sync_result.get('error') ~ ...) -}}
```

`tests/test_routes/test_sync_groups.py:695` (`assert "502" in result["error"]`)
locks in the pass-through, so the hole is currently *asserted* rather than caught.
Autoescaping prevents XSS; it does not prevent disclosure of internal container
addresses and library internals.

**Fix:** Give the narrow branch a controlled message and keep the raw text in the
log only, matching the discipline already applied to the broad branch:

```python
except MessengerFetchError as e:
    import structlog
    structlog.get_logger().error(
        "sync_groups_fetch_failed",
        account_id=account_id, account_type=account.type,
        error=str(e), exc_info=True,
    )
    await record_sync_failure(db, account, FETCH_FAILURE_MESSAGE)
    await db.commit()
    return RedirectResponse(url=account_groups_url, status_code=302)
```

Alternatively, sanitise at the source so `MessengerFetchError` only ever carries
project-authored text (`f"мост вернул HTTP {response.status_code}"` already is;
`f"{type(e).__name__}: {e}"` is not — reduce it to `type(e).__name__`).

---

### CR-02: `accounts_retry_sync` has no re-entrancy guard and no error handling — unbounded background task spawn and silent loss of due sends

**File:** `app/pages/accounts.py:702-741`
**Issue:**
This is the second of the three routes that start a group sync, and it received
none of the hardening 03-09 applied to `accounts_sync_groups`. The handler:

```python
account = result.scalar_one_or_none()
if not account:
    return RedirectResponse(url="/accounts", status_code=302)

session_id = str(account.id)
messenger = MaxMessenger(...) if account.type == "max" else WhatsAppMessenger(...)
await messenger.retry_sync()          # no try/except

account.status = "syncing"
await db.commit()

celery.send_task(task_name, args=[account.id])   # no dedup, no guard
```

Three provable consequences:

1. **No `status == "syncing"` check and no slot claim.** The form at
   `accounts/list.html:96-98`, `accounts/partial_cards.html:68-70` and
   `accounts/partials/sync_status_card.html:88-90` is a plain POST with *no*
   modal and *no* double-submit guard (`test_components.py:740-753` deliberately
   inventories only the *delete* forms). N clicks dispatch N
   `sync_wa_groups` / `sync_max_groups` tasks for the same account, each of which
   polls the bridge for up to `POLL_INTERVAL * MAX_POLLS = 600 s`
   (`app/worker/tasks.py:282-283`). There is no rate limiting on the route. An
   authenticated user can saturate the `celery-worker-telegram` replicas with a
   held-down Enter key.
2. **`status = "syncing"` for up to 10 minutes silently drops every due send for
   that account.** `app/application/scheduling/use_cases.py:95-107` matches
   `account.status != "active"`, recomputes `next_run_at` forward and `continue`s
   — no `SendLog` row, no trace. The 03-09 comment block at
   `app/pages/accounts.py:816-832` identifies exactly this as "регрессия хуже
   закрываемого дефекта" and refuses to introduce it on the page path, while the
   route 60 lines above does it on every click.
3. **`await messenger.retry_sync()` is unprotected.** Any bridge failure escapes
   to `generic_error_handler` (`app/main.py:108-119`) and returns
   `{"detail": "Internal server error"}` as raw JSON to a browser that submitted
   an HTML form — precisely the failure mode the `IntegrityError` branch was added
   to eliminate (`app/pages/accounts.py:947-959`).

**Fix:**

```python
if account.status == "syncing":
    return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)

if not _claim_sync_slot(account_id):
    return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)
try:
    try:
        await messenger.retry_sync()
    except Exception as e:
        structlog.get_logger().error(
            "retry_sync_failed", account_id=account_id, error=str(e), exc_info=True
        )
        await record_sync_failure(db, account, UNEXPECTED_FAILURE_MESSAGE)
        account.status = "sync_failed"
        await db.commit()
        return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)

    account.status = "syncing"
    await db.commit()
    celery.send_task(task_name, args=[account.id])
finally:
    _release_sync_slot(account_id)
```

Note the slot must be released here because the actual work runs in Celery, not in
the request — the claim only needs to cover the dispatch window. The
`status == "syncing"` check is what covers the long tail.

---

### CR-03: Telegram QR auth session is never bound to the authenticated user — any logged-in caller can drive and harvest another user's session

**File:** `app/pages/accounts.py:242-347`
**Issue:**
Four endpoints take `session_id` straight from the request and pass it to the
process-global `_qr_sessions` registry with no ownership check whatsoever:

| Line | Route | `session_id` source | Ownership check |
|------|-------|--------------------|-----------------|
| 242-253 | `GET  /accounts/connect/tg_user/qr-status` | `Query(...)` | none |
| 256-275 | `POST /accounts/connect/tg_user/refresh-qr` | JSON body | none |
| 278-315 | `POST /accounts/connect/tg_user/verify-2fa` | JSON body | none |
| 318-347 | `POST /accounts/connect/tg_user/complete` | JSON body | none |

Every handler calls `get_user_from_cookie` and returns on `None` — that is an
*authentication* check, not an *authorization* check. The phase's own rule, stated
twice in `app/pages/account_groups.py:8-12` ("ВЛАДЕНИЕ ПРОВЕРЯЕТСЯ НА КАЖДОМ
ВХОДЕ … `account_id` приходит из URL, то есть от недоверенного клиента"), is not
applied here even though `session_id` arrives by exactly the same route.

The worst of the four is `complete` (lines 318-347): it fetches the Telegram
session string belonging to whoever started that QR flow and persists it as the
**caller's** `MessengerAccount`:

```python
session_string = await complete_auth(session_id)
...
account = MessengerAccount(
    user_id=user.id,           # <-- caller, not the session's originator
    type="tg_user",
    credentials=session_string,
    status="active",
)
```

`verify-2fa` (lines 278-315) is additionally an unauthenticated-in-effect password
oracle against another user's Telegram 2FA: it accepts arbitrary `password` values
for any `session_id`, has no attempt counter, and returns the failure reason
verbatim (`return {"error": str(e)}`).

The only thing standing between an attacker and another user's Telegram session is
the secrecy of `uuid.uuid4().hex[:16]` (`app/messengers/telegram_user.py:57`) —
64 bits, which is not brute-forceable, but it is the *sole* control and it is
never rotated, never scoped, and is handed back to the client in the
`start-qr` JSON response where it can leak via logs, referrers or a shared
browser profile.

**Fix:** Bind the session to its originator at creation and verify on every use:

```python
# start-qr
session_id, login_url = await start_qr_auth(...)
_qr_session_owner[session_id] = user.id

# every other handler, immediately after the auth check
if _qr_session_owner.get(session_id) != user.id:
    return {"error": "Сессия не найдена"}   # same text as "missing" — no oracle
```

Store the owner alongside the session in `telegram_user._qr_sessions` (add a
`user_id` field to `QRAuthState`) so the binding is cleaned up by the existing
`_cleanup_expired_sessions`. Independently, add an attempt counter to `submit_2fa`
and collapse its error text to a single non-distinguishing string.

## Warnings

### WR-01: `_SYNC_IN_FLIGHT` is process-global mutable state with no reset hook — order-dependent test failures and silent degradation

**File:** `app/pages/accounts.py:747-771`
**Issue:** Two distinct problems with the same root:

*Tests.* `tests/conftest.py` and the `sync_setup` fixture in
`tests/test_routes/test_sync_groups.py:17-52` build a fresh in-memory database per
test, so `MessengerAccount.id` restarts at 1 every time. `_SYNC_IN_FLIGHT` does
not: it is module state on `app.pages.accounts`, shared by every app instance in
the pytest process. No fixture clears it. A single leaked entry — from a future
`return` accidentally placed between `_claim_sync_slot` and the `try`, or from a
test that patches the handler — silently converts every later test's
`POST /accounts/1/sync-groups` into an early 302, and the failure surfaces as an
unrelated assertion in a different file. The four "slot is released" tests
(`test_sync_groups.py:841-1002`) prove the happy paths but cannot catch cross-test
leakage.

*Runtime.* The comment at lines 840-856 correctly bounds the guard to one uvicorn
worker and to the HTTP path only. It does not degrade *loudly*: with a second
process the guard silently becomes per-process and the only remaining backstop is
`uq_groups_account_external`, which stops duplicate rows but not the duplicate
outbound `get_groups()` call against the messenger.

**Fix:** Add an autouse fixture, and make the degradation observable:

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def _clear_sync_slots():
    from app.pages import accounts
    accounts._SYNC_IN_FLIGHT.clear()
    yield
    accounts._SYNC_IN_FLIGHT.clear()
```

```python
# app/pages/accounts.py
if not _claim_sync_slot(account_id):
    structlog.get_logger().info("sync_slot_busy", account_id=account_id)
    return RedirectResponse(url=account_groups_url, status_code=302)
```

The log line is what tells operations that the in-process guard is doing work; its
absence in a multi-worker deployment is the signal that the guard has degenerated.

---

### WR-02: `await db.commit()` inside the `except` branches is itself unguarded — the branch can raise the very 500 it exists to prevent

**File:** `app/pages/accounts.py:911, 936, 978`
**Issue:** All three failure branches end with a bare `await db.commit()`:

```python
except Exception as e:
    ...
    await record_sync_failure(db, account, UNEXPECTED_FAILURE_MESSAGE)
    await db.commit()                       # line 936
    return RedirectResponse(...)
```

If the exception that landed in the broad `except` originated from the session
itself (an autoflush error, a lost connection, a `DataError` on a value already in
the identity map), the session is in a failed state and `commit()` raises
`PendingRollbackError`. That escapes the handler entirely, reaches
`generic_error_handler` (`app/main.py:108-119`) and returns
`{"detail": "Internal server error"}` — the exact raw-JSON-to-an-HTML-form outcome
the branch's own comment (lines 953-959) says it was written to eliminate. The
`finally` still releases the slot, so this is a correctness hole rather than a
lock leak, but the stated contract is unmet.

**Fix:** Roll back first, then write, and swallow a failed write:

```python
except Exception as e:
    ...log...
    try:
        await db.rollback()
        account = await db.get(MessengerAccount, account_id)
        if account:
            await record_sync_failure(db, account, UNEXPECTED_FAILURE_MESSAGE)
            await db.commit()
    except Exception:
        structlog.get_logger().error("sync_failure_not_recorded", account_id=account_id, exc_info=True)
    return RedirectResponse(url=account_groups_url, status_code=302)
```

---

### WR-03: A failed or rejected sync leaves `MessengerAccount.status` inconsistent across the three call sites

**File:** `app/pages/accounts.py:910, 935, 975` and `app/worker/tasks.py:331-342`
**Issue:** `record_sync_failure` and `account.status` are set together in the
background paths and never together in the page path:

| Call site | `record_sync_failure` | `status = "sync_failed"` |
|-----------|----------------------|--------------------------|
| `tasks.py:357-361` (bridge failure) | yes | yes |
| `tasks.py:372-376` (timeout) | yes | yes |
| `tasks.py:390-394` (unexpected) | yes | yes |
| `accounts.py:910` (fetch error) | yes | **no** |
| `accounts.py:935` (unexpected) | yes | **no** |
| `accounts.py:975` (uniqueness conflict) | yes | **no** |

Consequence for a `tg_user` account whose page sync just failed: `status` stays
`active`, so `accounts/list.html:120` renders the green "Активно" badge and
`accounts/list.html:94-102` never renders the "Повторить" form — the user has no
retry affordance on the accounts list at all. On the groups screen the same
account shows a green "Активно" badge (`account_groups/partials/sync_result.html:51`)
directly above a red "Синхронизация не удалась" alert
(`account_groups/list.html:116`).

Separately, `tasks.py:331-342` sets `account.status = "active"` **before** checking
`result.error`, so a sync the helper *refused to apply* (`MALFORMED_RESPONSE_MESSAGE`
or `EMPTY_RESPONSE_MESSAGE`) also lands the account in `active` with a red plaque.
The `log.warning("sync_response_rejected", ...)` two lines later confirms the code
knows the sync did not succeed.

**Fix:** In `accounts.py`, set `account.status = "sync_failed"` next to each
`record_sync_failure`. In `tasks.py`, branch on the result:

```python
result = await apply_group_resync(session, account, groups, messenger_type=messenger_type)
account.status = "sync_failed" if result.error else "active"
await session.commit()
```

---

### WR-04: `allow_full_wipe` has no caller — an account whose groups were genuinely all removed can never be reconciled

**File:** `app/application/accounts/group_resync.py:135, 263-272`
**Issue:** The degenerate-response guard trips whenever `existing` is non-empty and
`seen` is empty, and `allow_full_wipe` defaults to `False` with no call site
anywhere setting it (`app/pages/accounts.py:942`, `app/worker/tasks.py:331`, both
omit it). The docstring acknowledges this ("ни один существующий вызывающий его не
снимает") but the operational consequence is not stated: once a user genuinely
leaves every chat on an account, that account enters a permanent state where

- every sync returns `EMPTY_RESPONSE_MESSAGE` and a red plaque,
- `missing_since` is never set on any row, so the "не найдена при синке" mark that
  D-11 exists to provide never appears,
- `last_synced_at` is never advanced, so the groups-screen header reads
  "синхронизация ещё не выполнялась" forever, and
- the stale rows remain `is_active` and keep receiving sends
  (`app/application/scheduling/use_cases.py:171-177` only skips *inactive* groups)
  until the user deletes each one by hand.

That last point is the sharp edge: the guard trades "one bridge glitch marks
everything missing" for "a real emptying keeps sending to chats the user has left".

**Fix:** Distinguish "the messenger answered with an authoritative empty list" from
"the messenger did not answer". Since `MessengerFetchError` now makes a *fetch*
failure distinguishable (adapters no longer return `[]` on error), the page path
can safely pass `allow_full_wipe=True` for `tg_user`, where `get_groups()` raises
on failure and `[]` means exactly "no groups":

```python
await apply_group_resync(
    db, account, fetched_groups,
    messenger_type=messenger_type,
    allow_full_wipe=(messenger_type == "tg_user"),
)
```

The WA/MAX background path must keep the guard, because there the composition comes
from the `groups` field of `get_sync_status()` where `null`/absent is a valid
answer — which is the case the docstring at lines 253-258 actually describes.
Failing that, add an escape hatch (a "подтвердить, что групп не осталось" action)
so the state is reachable at all.

---

### WR-05: Raw exception text is rendered to the user on all three connect screens — the same T-03-17 class the sync path just hardened

**File:** `app/pages/accounts.py:233-234, 410-411, 594-595`
**Issue:** Three sites interpolate an arbitrary exception into user-facing output:

```python
except Exception as e:
    return {"error": f"Ошибка запуска QR авторизации: {e}"}          # :234, JSON to browser

except Exception as e:
    error = f"Ошибка подключения к WA Bridge: {e}"                    # :411, into connect_wa.html

except Exception as e:
    error = f"Ошибка подключения к MAX: {e}"                          # :595, into connect_max.html
```

Lines 411 and 595 sit directly around `messenger.start_session()` /
`messenger.get_qr()`, whose first action is to resolve `bridge_url`; that property
raises `RuntimeError` carrying the internal container endpoint — the exact leak
`UNEXPECTED_FAILURE_MESSAGE` was introduced to stop
(`app/application/accounts/group_resync.py:79-92` names it explicitly:
"`RuntimeError` менеджера контейнеров с внутренним адресом моста"). Line 234 is a
Telethon exception returned as JSON.

Note by contrast that `accounts_connect_wa_status:476-479` and
`accounts_connect_max_status:662-665` *do* it correctly — fixed user text, raw text
to the log with `exc_info=True`. The three sites above are the ones that were
missed.

**Fix:** Apply the pattern already used 40 lines below in the same file:

```python
except Exception as e:
    structlog.get_logger().error("wa_connect_start_error", error=str(e), exc_info=True)
    error = "Не удалось подключиться к WhatsApp. Повторите попытку."
```

---

### WR-06: `fetched_groups` / `messenger_type` can be unbound — the `if/elif/elif` chain has no `else`

**File:** `app/pages/accounts.py:881-898`
**Issue:**

```python
if account.type == "tg_user":
    ...
    fetched_groups = await messenger.get_groups()
    messenger_type = "tg_user"
elif account.type == "wa":
    ...
elif account.type == "max":
    ...
# no else
```

Both names are then used unconditionally at line 942. Correctness rests entirely on
the membership test 80 lines earlier (line 800,
`if account.type not in ("tg_user", "wa", "max")`). Adding a fourth messenger to
that tuple without adding a branch here produces `UnboundLocalError` inside the
`try`, which is caught by the broad `except` at line 914 — so the user gets
"Синхронизация не удалась из-за внутренней ошибки" on a *supported* messenger, and
the real cause is a name error buried in the log. The two conditions are 80 lines
and one comment block apart, which is exactly the distance at which they drift.

**Fix:** Close the chain so the failure is immediate and named:

```python
else:  # pragma: no cover — guarded at line 800
    raise AssertionError(f"unsupported account type reached fetch: {account.type!r}")
```

Better still, derive both from a single mapping so the guard at line 800 and the
dispatch here cannot disagree:

```python
_FETCHERS = {
    "tg_user": lambda acc, s: TelegramUserMessenger(
        session_string=acc.credentials, api_id=s.telegram_api_id, api_hash=s.telegram_api_hash
    ),
    "wa": lambda acc, s: WhatsAppMessenger(session_id=str(acc.id)),
    "max": lambda acc, s: MaxMessenger(session_id=str(acc.id)),
}
if account.type not in _FETCHERS:
    return RedirectResponse(url=account_groups_url, status_code=302)
```

---

### WR-07: Modal double-submit guard never resets `sending` on close — the second POST it exists to stop is still reachable

**File:** `app/templates/components/modal.html:90-91, 104`
**Issue:** `sending` is cleared only in `show()`; `hide()` deliberately does not
touch it (documented at lines 62-64). That is correct for the bfcache case the
comment describes, but it leaves this sequence open:

1. User confirms → `sending = true`, confirm button disabled, navigation starts.
2. Before the new document commits, the user presses `Esc` (line 97,
   `x-on:keydown.escape.window="hide()"`) or clicks the overlay (line 100).
   `hide()` runs; `sending` stays `true` but the panel is closed.
3. User re-opens the same panel → `show()` sets `sending = false`.
4. User confirms again → a second POST for the same destructive action, both in
   flight.

The docstring's answer — "Защитой от повторной отправки на этом пути служит
идемпотентность самих маршрутов удаления" — covers the *no-Alpine* path, not this
one. For `POST /accounts/{id}/delete` the second request is harmless; for
`POST /schedules/{id}/delete` with a `return_to` field
(`ads/includes/sched_card.html:257`) it is a redirect to an editor for a schedule
that no longer exists.

**Fix:** Latch on navigation rather than on panel visibility, so closing and
reopening cannot clear it:

```js
show() { this.opener = document.activeElement; this.open = true;
         this.$nextTick(() => this.$refs.cancel.focus()); },
```

and reset `sending` from `pageshow` instead, which is the event bfcache actually
fires:

```html
x-on:pageshow.window="sending = false"
```

That keeps the bfcache guarantee the current code is reaching for while closing the
close-and-reopen path.

---

### WR-08: `app/pages/groups.py` catch-all answers GET only; bookmarked POST deep links get a JSON 405

**File:** `app/pages/groups.py:33-44`
**Issue:** The shim's docstring says "любая старая глубокая ссылка отвечает
перенаправлением" and "Обработчиков POST в модуле нет ни одного: тумблер и
удаление живут на маршрутах экрана аккаунта". Those two statements are in tension
for the failure they are meant to prevent. `POST /groups/12/toggle` — a resubmitted
form from a cached page, or a browser restoring a POST on back — now matches the
path but not the method, so Starlette returns `405` with
`{"detail": "Method Not Allowed"}`. The stated goal ("Ответ об отсутствии страницы
на них был бы потерей без нужды") is not met for exactly the requests that carry
user intent.

**Fix:** Register the same handler for the methods the retired section actually
exposed, and answer POST with `303 See Other` so the browser converts to GET:

```python
@router.api_route("/groups", methods=["GET", "POST"])
@router.api_route("/groups/{deep_link:path}", methods=["GET", "POST"])
async def groups_retired(request: Request, deep_link: str = "") -> RedirectResponse:
    code = 303 if request.method == "POST" else 302
    return RedirectResponse(url="/accounts", status_code=code)
```

## Info

### IN-01: Unknown account statuses are shown to the user as raw latin identifiers

**File:** `app/templates/accounts/list.html:122`, `app/templates/accounts/partial_cards.html:94`
**Issue:** `{{ badge(account.status, 'warning') }}` prints the DB column verbatim
for anything that is not `active`/`disconnected`. `connecting` is a real, reachable
status (`app/pages/accounts.py:391, 574`), so a Russian-language UI shows the badge
"connecting".
**Fix:** Add a `STATUS_LABELS` dict next to `MESSENGER_LABELS` in all three row
files and fall back to a generic "Неизвестно" rather than to the raw value.

---

### IN-02: `components/filters.html` still documents the removed `/groups` section

**File:** `app/templates/components/filters.html:2-8`
**Issue:** The header comment says "Применений три: группы (План 04) …" and the
usage example is `{% call filters('groups-filters', action='/groups') %}`. The
section was removed in 03-08. `tests/test_templates/test_components.py:405-408`
explicitly warns that leftover addresses of the removed section give false
positives to grep checks — this is one.
**Fix:** Update the example to `action='/accounts/1/groups'` and correct the
"Применений три" count.

---

### IN-03: Five function-local `import structlog` statements in one module

**File:** `app/pages/accounts.py:477, 663, 901, 927, 965`
**Issue:** `structlog` has no import cycle with this module (`app/worker/tasks.py:2`
imports it at module level and binds `logger` once). The repeated local imports are
noise that obscures the genuinely necessary local imports of `celery` and `asyncio`
in the same file.
**Fix:** `import structlog` at the top, `logger = structlog.get_logger(__name__)`
once, and use `logger` at all five sites.

---

### IN-04: `record_sync_failure` is `async` with no `await` in its body

**File:** `app/application/accounts/group_resync.py:298-333`
**Issue:** The docstring defends the choice on symmetry grounds. The cost is real
though: the signature forces all six call sites to be async contexts and hides
that the function never touches the session it is handed, which is why nobody
noticed it also never sets `status` (see WR-03).
**Fix:** No change required if the symmetry argument is accepted, but drop the
unused `session` parameter — it is the misleading part, not the `async`.

---

### IN-05: Group name fallback uses truthiness, so a legitimately falsy name becomes the external id

**File:** `app/application/accounts/group_resync.py:218-219`
**Issue:** `name = (str(raw_name) if raw_name else external_id)[:_NAME_MAX]`. A
chat literally named `0` (or `""`, or a JSON `false`) is stored under its external
id instead of its name.
**Fix:** `name = external_id if raw_name is None else (str(raw_name) or external_id)`.

---

### IN-06: Hard-coded 5-second sleep with a function-local `import asyncio` in a request handler

**File:** `app/pages/accounts.py:587-589`
**Issue:**
```python
await messenger.start_session(phone=phone)
import asyncio
await asyncio.sleep(5)
qr_data = await messenger.get_qr()
```
A magic number with no named constant and no comment explaining why 5. Every MAX
connect request holds a connection open for at least five seconds regardless of
whether the worker is ready.
**Fix:** Hoist `asyncio` to the module imports, name the constant
(`MAX_QR_WARMUP_SECONDS = 5`), and prefer polling `get_qr()` with a short interval
and a deadline over a fixed sleep.

---

### IN-07: `account` is rebound after rollback, shadowing the ownership-checked object

**File:** `app/pages/accounts.py:973`
**Issue:** `account = await db.get(MessengerAccount, account_id)` reuses the name
of the object that was loaded with the `user_id == user.id` filter at line 785. The
new fetch has no ownership predicate. It is safe today because `account_id` was
already authorized on line 795, but the shadowing hides that dependency from anyone
reading only the `except` block.
**Fix:** Bind a new name (`refreshed = await db.get(...)`) so the ownership-checked
object and the unchecked reload are visibly different.

---

### IN-08: `test_sync_groups_always_uses_settings_credentials` duplicates the whole fixture inline

**File:** `tests/test_routes/test_sync_groups.py:194-261`
**Issue:** 68 lines re-implement `sync_setup` verbatim just to vary
`telegram_api_id`/`telegram_api_hash`. Any future change to the fixture (engine
options, dependency overrides, teardown) must be made in two places, and this copy
will silently keep testing the old shape.
**Fix:** Parameterize the fixture:

```python
@pytest_asyncio.fixture
async def sync_setup(request):
    overrides = getattr(request, "param", {})
    settings = Settings(_env_file=None, ..., **overrides)
    ...

@pytest.mark.parametrize(
    "sync_setup", [{"telegram_api_id": 0, "telegram_api_hash": ""}], indirect=True
)
async def test_sync_groups_always_uses_settings_credentials(sync_setup): ...
```

---

_Reviewed: 2026-08-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

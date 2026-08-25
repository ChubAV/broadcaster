---
phase: 04-dashbord-i-istoriya
reviewed: 2026-08-15T12:05:00Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - alembic/versions/0016_send_logs_user_sent_at.py
  - app/application/analytics/__init__.py
  - app/application/analytics/send_analytics.py
  - app/application/scheduling/use_cases.py
  - app/main.py
  - app/pages/admin.py
  - app/pages/common.py
  - app/pages/dashboard.py
  - app/pages/dashboard_feed.py
  - app/pages/history.py
  - app/repositories/send_log.py
  - app/routes/history.py
  - app/static/css/app.css
  - app/templates/dashboard.html
  - app/templates/dashboard/includes/feed_row.html
  - app/templates/dashboard/includes/metric_tile.html
  - app/templates/dashboard/includes/upcoming_row.html
  - app/templates/dashboard/includes/worker_row.html
  - app/templates/dashboard/partial_feed.html
  - app/templates/history/detail.html
  - app/templates/history/includes/filter_chips.html
  - app/templates/history/includes/history_card.html
  - app/templates/history/list.html
  - app/worker/tasks.py
  - tests/test_application/test_scheduling_use_cases.py
  - tests/test_application/test_send_analytics.py
  - tests/test_migrations/test_0015_groups_unique_account_external.py
  - tests/test_migrations/test_0016_send_logs_user_sent_at.py
  - tests/test_pages/test_dashboard.py
  - tests/test_pages/test_history.py
  - tests/test_pages/test_history_export.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_history.py
  - tests/test_templates/test_components.py
  - tests/test_worker/test_tasks.py
findings:
  critical: 0
  warning: 17
  info: 5
  total: 22
status: issues_found
---

# Phase 04: Code Review Report (re-review at phase close)

**Reviewed:** 2026-08-15T12:05:00Z
**Depth:** standard
**Files Reviewed:** 38
**Status:** issues_found

This report **supersedes** the 2026-08-15T06:43:39Z review of the same phase. Prior
finding IDs are cited inline so the two can be reconciled.

## Summary

**The three prior BLOCKERs are genuinely closed, and I verified each fix at the
code level rather than accepting the changelog.**

* CR-01 (draft ads reaching the WA/MAX queues): `retry_send` now calls
  `effective_ad_status(ad) == AD_STATUS_DRAFT` **before** `build_dispatch_task`
  (`app/worker/tasks.py:373-386`), so the check is upstream of the Redis `rpush`
  that `wa_worker/index.js` consumes without touching the DB. The same predicate
  is mirrored in `history_retry` (`app/pages/history.py:871-878`) and named in
  the UI by `retry_availability` (`history.py:483-484`).
* CR-02 (disabled groups): `group.is_active` is now read at all three layers
  (`tasks.py:388-397`, `history.py:875`, `history.py:487-488`).
* CR-03 (activity chart ordering): `activity_heatmap` now anchors on the
  reader's **local midnight** (`send_analytics.py:323-329`) and the query bound
  follows the grid, so column order equals chronological order by construction.
  Crucially, the fix carries two *end-to-end* tests that the previous test set
  could not have failed on (`test_send_analytics.py:1228`, `:1256`).

**Both gap-closure plans do what they claim, with one structural contradiction
each.** Plan 04-11's worker list is correctly tenant-scoped
(`MessengerAccount.user_id == user.id`), projects exactly three columns so
`credentials`/`session_data` cannot reach HTML, and calls no Docker SDK — all
three properties are pinned by tests (`test_shell.py:735-780`). But the macro
then re-derives "is this worker online" from the literal `'active'`
(`worker_row.html:35`), two lines after the module comment in `common.py:259-263`
declares that predicate has exactly one definition. Plan 04-12's cooldown really
does survive the 302 and really is keyed per record — but the registry it lives
in **never evicts an expired key**, so it grows for the life of the process, and
the notice it shows on a rejected second click asserts a queued task that, on one
reachable interleaving, does not exist.

**Nothing rises to BLOCKER in this pass.** I looked specifically for tenant
leaks, injection, and unsafe rendering and found none: every read path carries
`SendLog.user_id == user.id` or `Ad.user_id == user_id`, there is not one `|safe`
in any template in the project, the CSV formula-injection guard and constant
filename are intact, and the retry route checks ownership before it does anything
else. Reporting zero BLOCKERs here is a finding about the fixes, not a failure to
look.

**Eleven of the prior review's findings are still present unchanged.** Two of
those (WR-12, WR-15 below) were deliberately deferred and are re-reported at
their prior tier as instructed. The other nine appear to have been left
unaddressed rather than decided against.

**One prior finding was wrong and I am retracting it.** Prior WR-02 argued that
`session.get(MessengerAccount, None)` is reachable in `retry_send` because
"`Group.account_id` is nullable". It is not: `app/models/group.py:49-51` declares
it `Mapped[int]` with a non-null FK and `ondelete="CASCADE"`. The call is
unreachable for any persisted `Group`. What remains is a real but cosmetic
inconsistency between two sibling code paths — demoted to IN-02.

I did not run the test suite as part of this review; a partial run was killed by
its own timeout. That has no bearing on the findings — every one below is derived
from reading the code, and "tests pass" would not be evidence of correctness in
any case.

## Warnings

### WR-01: The retry cooldown registry never evicts expired keys — it grows for the life of the process

**Severity:** WARNING
**File:** `app/pages/history.py:399`, `app/pages/history.py:498-517`, `app/pages/history.py:897-899`

**Issue:** `_RETRY_IN_FLIGHT: dict[int, float]` gains one entry per *successful*
retry and loses it only on paths where nothing was queued. `_claim_retry_slot`
reads and overwrites the key for the log id it was handed, and never looks at any
other key; `_release_retry_slot` is called only from `finally` when
`queued is False`. There is no sweep, no `TTLCache`, no bound, and no periodic
task — I grepped the whole tree for any other reference and the only ones outside
this module are in the test file.

The registry's own comment block (lines 380-393) names two limits explicitly and
calls them "ДВЕ ГРАНИЦЫ, НАЗВАННЫЕ ЯВНО" — expiry and single-process. Unbounded
growth is a third, and it is the one the reader would most reasonably assume was
handled, because the values *are* deadlines: the data structure looks like it
expires and does not.

Growth is slow and self-limiting in practice (each successful retry spends a
balance message, and each produces a new send-log id), so this is a leak rather
than a live outage. It is also the kind of leak that only shows up on a
long-uptime production process and never in a test run, which is exactly why it
should not be left to be discovered there. The one test that touches the topic
(`test_history_retry.py:1088-1097`, `test_retry_slot_registry_documents_its_limit`)
asserts only that the word "процесс" appears near the declaration — it pins the
prose, not the structure.

**Fix:** Sweep expired keys on claim. This is O(n) only on the claim path, needs
no new dependency, and makes the dict's size proportional to *concurrent* holds
rather than to lifetime retry count:

```python
def _claim_retry_slot(log_id: int) -> bool:
    now = monotonic()
    # Просроченные удержания снимаются ЗДЕСЬ: реестр обязан быть размером с
    # число ДЕЙСТВУЮЩИХ окон, а не с числом повторов за всё время работы
    # процесса. Без этого словарь растёт до перезапуска — молча.
    for stale in [k for k, deadline in _RETRY_IN_FLIGHT.items() if deadline <= now]:
        del _RETRY_IN_FLIGHT[stale]
    deadline = _RETRY_IN_FLIGHT.get(log_id)
    if deadline is not None and now < deadline:
        return False
    _RETRY_IN_FLIGHT[log_id] = now + RETRY_COOLDOWN_SECONDS
    return True
```

and add a test that claims N slots, expires them, claims one more, and asserts
`len(_RETRY_IN_FLIGHT) == 1`.

### WR-02: The "busy" notice tells the user a task was queued when one reachable interleaving queued nothing

**Severity:** WARNING
**File:** `app/pages/history.py:301-311`, `app/pages/history.py:848-849`, `app/pages/history.py:856-899`

**Issue:** The hold is claimed at line 848, *before* the entity-integrity check
(871-878) and the balance gate (883-887). A second request arriving while the
first is still inside that window is refused with `RETRY_BUSY`, whose text is:

> "Повтор этой отправки уже поставлен в очередь — второй раз он не уйдёт.
> Результат появится новой записью истории."

If the first request then fails — draft ad, disabled group, detached account, or
an exhausted balance — it releases the hold and redirects to `RETRY_GONE` /
`RETRY_NO_BALANCE`, and **nothing was ever queued**. The second user (or the same
user in a second tab) has been told a send is in flight and promised a history
record that will never appear.

The comment at 301-305 enumerates the two cases it believes reach this key
("первый повтор, который ещё выполняется" and "второе нажатие, когда первый
повтор уже поставлен") and concludes the text should speak about the state of the
*task*. The third case — first attempt still running and about to be refused —
is not in that list, and it is the one where the text is false. This is the same
class of defect the phase's own prohibition P-04-01 forbids: a plausible lie is
worse than an unhelpful truth.

**Fix:** Either claim the hold *after* the checks that can refuse (which
re-opens a narrow concurrent window the plan deliberately closed), or make the
text describe what the guard actually guarantees:

```python
RETRY_BUSY: (
    "Повтор этой отправки уже запущен или недавно выполнялся — повторите "
    "через минуту. Если он ушёл в очередь, результат появится новой записью "
    "истории.",
    "info",
),
```

### WR-03: `queued` is set only after `send_task` returns, so a lost broker ack re-arms the double send

**Severity:** WARNING
**File:** `app/pages/history.py:893-899`

**Issue:**

```python
celery.send_task(RETRY_TASK_NAME, args=[log.id, user.id])
queued = True
```

`send_task` is at-least-once by construction: a connection reset or timeout after
the broker has accepted the message raises, `queued` stays `False`, the `finally`
block pops the hold, and the user's next click is accepted immediately. That is
precisely the situation the hold exists to prevent — the message *is* in the
queue and a second one is about to join it, producing two irreversible sends to a
third-party group and two balance deductions.

The exception test (`test_history_retry.py:855-884`) pins the opposite
behaviour — that an exception must release the hold — so the current shape is
deliberate for the *balance-gate-raised* case. But that test patches
`check_balance_cached`, not `send_task`; it does not distinguish "failed before
the broker" from "failed after the broker".

**Fix:** Arm the hold *before* the call and release only for failures that
provably preceded it:

```python
queued = True          # окно армируется ДО обращения к брокеру
try:
    celery.send_task(RETRY_TASK_NAME, args=[log.id, user.id])
except celery_exceptions.OperationalError:
    # Отказ СОЕДИНЕНИЯ с брокером: сообщение не принято, удержание снимается.
    queued = False
    raise
```

Any other exception keeps the hold — the conservative side, because an extra
minute of waiting is cheaper than a second irreversible send.

### WR-04: The "worker is online" predicate has a second definition in the template, contradicting the comment that says it has one

**Severity:** WARNING
**File:** `app/templates/dashboard/includes/worker_row.html:35`, `app/pages/common.py:259-263`, `app/pages/common.py:343`

**Issue:** `common.py:259-263` declares:

> "Предикат «воркер онлайн» объявлен ОДИН раз… перечень и агрегат обязаны решать
> «онлайн ли он» одним и тем же сравнением, иначе пилюля шапки и строка перечня
> разошлись бы на одном и том же аккаунте."

`WORKER_ONLINE_STATUS = "active"` then drives `is_online` (line 343) and, through
it, `sessions_online`. But the macro decides the same question a second time:

```jinja
{%- if session.status == 'active' %}Онлайн
```

The macro's own header even claims the opposite — "ПРИЗНАК «ОНЛАЙН» БУЛЕВ и
приходит готовым из контракта шелла" — which is true of the dot
(`session.is_online`, line 31) and false of the word (line 35). Change
`WORKER_ONLINE_STATUS` to anything else and the row renders a grey dot next to
the word "Онлайн", the header pill disagrees with the row it was derived from,
and no test fails: `_worker_rows` in `test_shell.py:683-696` parses only
`data-worker-online`, never the visible state text.

**Fix:** Drive the label from the boolean the contract already supplies, so the
literal appears once in the codebase:

```jinja
{%- if session.is_online %}Онлайн
{%- elif session.status == 'disconnected' %}Отключён
{%- else %}{{ session.status }}{% endif -%}
```

and extend `_worker_rows` to capture the state text so the pairing is pinned.

### WR-05: Fourth copy of the messenger label map

**Severity:** WARNING
**File:** `app/templates/dashboard/includes/worker_row.html:27`

**Issue:** `{'tg_user': 'Telegram', 'wa': 'WhatsApp', 'max': 'MAX'}` now exists in
at least four places: here, `app/pages/history.py:72-77` (`MESSENGER_CHIPS`),
`app/pages/history.py:195` (`MESSENGER_LABELS`, derived from the chips precisely
so the file and the screen cannot disagree), and
`app/templates/includes/messenger_icon.html` (`aria-label` / `msg__label` per
branch). The macro header defends the copy — "макрос обязан быть
самодостаточным, а не рассчитывать на переменную вызывающей страницы" — but that
argues only against reading the *caller's* context, not against a template
global, which this project already uses for exactly this purpose
(`AD_STATUS_DRAFT`, `nav_items`, `plural_ru` are all bound in `common.py:99-137`).

The phase's stated rule is that one fact has one source; the fix for a macro that
cannot see caller context is a global, not a copy.

**Fix:** Bind the map once next to the other template globals and delete the
literal:

```python
# app/pages/common.py, next to the nav globals
from app.pages.history import MESSENGER_LABELS  # или переместить в constants.py
templates.env.globals["messenger_labels"] = MESSENGER_LABELS
```

```jinja
{{ messenger_labels.get(session.type, session.type) }}
```

(If the import direction is awkward, move the map to `app/constants.py` — that is
where the project already keeps single-source values that both Python and Jinja
read.)

### WR-06: The shell now materialises every messenger account on all 26 page routes, with no bound, for data one page consumes

**Severity:** WARNING
**File:** `app/pages/common.py:327-346`, `app/pages/__init__.py:21-41`

**Issue:** `get_shell_context` previously answered "how many accounts" with a
scalar subquery folded into the single counts round-trip. It now issues a
separate `SELECT id, type, status FROM messenger_accounts WHERE user_id = :id
ORDER BY id` with **no `LIMIT`**, builds a list of dicts, and derives both
aggregates from it. `load_shell_context` is a router-level dependency on every
page route (`__init__.py:41`), so this runs on `/ads`, `/billing`, `/profile`,
every admin screen — 25 routes that never read `sessions`.

The row count is user-controlled and unbounded by the schema: nothing caps how
many `MessengerAccount` rows a user may own. The CSS bounds the *visual* height
(`app.css:640`, `max-height: 264px; overflow-y: auto`) and the comment there
explicitly chooses scrolling over truncation "чтобы ни одна строка не выпадала
молча" — a good call for the dashboard, but it means the DOM and the per-request
allocation scale with the account count on every page in the product.

This is not a hot-path performance complaint (that is out of scope); it is an
unbounded, user-influenced allocation on the render path of every route, which is
the shape of a resource-exhaustion issue.

**Fix:** Either restrict the list query to the route that reads it, or bound it
and expose the overflow honestly:

```python
# Перечень нужен ОДНОМУ маршруту из 26. Агрегаты остаются в общем
# round-trip скалярными подзапросами, как было до DASH-05.
WORKER_LIST_CAP = 100
...
.order_by(MessengerAccount.id).limit(WORKER_LIST_CAP)
```

and, if capped, pass `sessions_truncated` into the template so a user past the
cap is told rather than shown a silently short list.

### WR-07: The retry balance gate is still only in the web handler, never re-checked at execution

**Severity:** WARNING (prior WR-03 — still present)
**File:** `app/pages/history.py:883-887`, `app/worker/tasks.py:303-400`

**Issue:** Unchanged since the last review, and now conspicuous: plan 04-11/04-12
added *three* second-line checks to `retry_send` (ownership, draft, group
disabled), each with a comment arguing that broker arguments are their own trust
boundary. The balance gate is the one handler check that was not mirrored. A
retry task can sit behind a backlog and execute after the balance is spent;
`deduct_message` (`app/services/billing_service.py:44-52`) then guards with
`balance > 0`, returns `False`, and the message has **already been sent** — a
free send rather than a negative balance. The scheduler has no such asymmetry:
its gate runs in the same tick as the dispatch (`use_cases.py:187-199`).

**Fix:**

```python
# app/worker/tasks.py, alongside the other second-line checks
from app.services.billing_cache import check_balance_cached

allowed, _reason = await check_balance_cached(session, user_id, "send")
if not allowed:
    log.warning("retry_send_stopped", reason="no_balance")
    return
```

### WR-08: `dispatch_send_tasks` silently drops an unrecognised account type while `retry_send` logs a successful dispatch

**Severity:** WARNING
**File:** `app/worker/tasks.py:65-71`, `app/worker/tasks.py:399-400`

**Issue:** The routing loop has three `elif` branches and no `else`. A
`DispatchTask` whose `type` is not `tg_user`/`wa`/`max` is dropped without a log
line, without an exception, and without a `SendLog` row. `retry_send` then
executes unconditionally:

```python
await dispatch_send_tasks([task])
log.info("retry_send_dispatched", type=task.type, account_id=task.account_id)
```

`dispatch_send_tasks` returns `None` whether it dispatched one task or zero, so
the log entry asserts a dispatch that did not happen — and the user has already
been shown "Повтор поставлен в очередь… Результат появится новой записью
истории", a record that will never be written.

`MessengerAccount.type` is a free `String(20)` with no enum constraint
(`app/models/messenger_account.py`), so the only thing keeping this unreachable is
that no code currently writes a fourth value. That is exactly the "перечень
конечен ровно до появления следующего значения" argument this phase makes
repeatedly in favour of open-ended predicates — applied everywhere except here.

**Fix:** Make the drop loud, and let the caller see it:

```python
else:
    logger.error("dispatch_unknown_account_type", type=task.type,
                 account_id=task.account_id, ad_id=task.ad_id)
    unrouted.append(task)
...
return len(tasks_to_dispatch) - len(unrouted)   # и логировать факт в retry_send
```

### WR-09: Admin history routes still skip the `_clean_choice` normalisation the user-facing routes enforce

**Severity:** WARNING (prior WR-04 — still present)
**File:** `app/pages/admin.py:193-208`, `app/pages/admin.py:280-295`

**Issue:** `history_partial`, `history_list` and `history_export` pass every axis
value through `_clean_choice(...)` before `apply_history_filters`
(`history.py:554-556`, `658-660`, `921-923`); the module docstring at
`history.py:99-113` calls that the point of enforcement. `admin_user_history` and
`admin_user_history_partial` call `apply_history_filters` with the **raw**
`status`, `messenger` and `period`. An unknown value yields an empty list with no
chip marked active, and the raw string is echoed into `filter_params` → the
scroll sentinel and the template context. Not an injection (all values are bound
parameters), but the same "мусор не выбирает ничего" defect the user routes were
written to avoid.

**Fix:**

```python
from app.pages.history import (
    _clean_choice, MESSENGER_VALUES, PERIOD_VALUES, STATUS_VALUES,
)
status = _clean_choice(status, STATUS_VALUES)
messenger = _clean_choice(messenger, MESSENGER_VALUES)
period = _clean_choice(period, PERIOD_VALUES)
```

(Better: promote these to a non-underscore surface — see WR-10.)

### WR-10: `app/pages/admin.py` still imports a private name across a module boundary

**Severity:** WARNING (prior WR-05 — still present)
**File:** `app/pages/admin.py:14`

**Issue:** `from app.pages.history import _parse_account_id`. A leading-underscore
name signals "safe to rename"; renaming it breaks the admin section at import
time. The phase moved the *shared* filter definitions into `send_analytics.py`
precisely so consumers would not reach into each other, then reached anyway for
the one helper left behind.

**Fix:** Rename to `parse_account_id` and export it, or move it next to the other
shared HTTP-parsing helpers.

### WR-11: No upper time bound on the metrics/heatmap windows — and the clamp's justifying comment is now stale

**Severity:** WARNING (prior WR-06 — still present, plus new comment drift)
**File:** `app/application/analytics/send_analytics.py:201-204`, `app/application/analytics/send_analytics.py:337-360`

**Issue:** Both queries bound `sent_at` only from below. A row with `sent_at` in
the future (clock skew between a Celery worker and the DB, or an explicit `now`
from a caller) is counted in the current window by `send_metrics` and clamped
into the newest row by `activity_heatmap`.

The CR-03 fix made the comment at lines 352-355 wrong. It justifies the clamp
with: "запись ровно в `now` даёт смещение `days*24` и индекс на один больше
последнего ряда." That was true when the row origin was the request moment. With
the local-midnight anchor, a record at `now` yields
`offset_hours = (days-1)*24 + local_hour ≤ days*24 - 1`, so `day_index >= days`
is now **unreachable for any record at or before `now`**. The clamp's only
remaining function is to absorb records arbitrarily far in the future into the
last day — a different case, which the comment does not cover and no test
exercises.

**Fix:** Bound both windows above and let the comment describe the surviving case:

```python
).where(
    SendLog.user_id == user_id,
    SendLog.sent_at >= previous_start,
    SendLog.sent_at <= now,
)
```

and add `SendLog.sent_at <= now` to the heatmap stream query, then either drop the
clamp or reword it to say what it now guards.

### WR-12: Lookups inside the analytics/retry helpers are still not user-scoped

**Severity:** WARNING (prior WR-07 — deliberately deferred, re-reported)
**File:** `app/application/analytics/send_analytics.py:539-546`, `app/pages/history.py:453-477`, `app/pages/history.py:858-865`

**Issue:** Unchanged, and the argument is stronger than the prior review stated.
Three secondary queries carry no owner predicate:

* `select(Group.id, Group.is_active).where(Group.id.in_(group_ids))` in
  `upcoming_sends`;
* `select(Ad.id, Ad.status).where(Ad.id.in_(ad_ids))` and
  `select(MessengerAccount.id, MessengerAccount.status).where(...in_(account_ids))`
  in `retry_availability`;
* `db.get(Group, ...)`, `db.get(Ad, ...)`, `db.get(MessengerAccount, ...)` in
  `history_retry`.

The safety of all six rests on ids never being reused. `send_logs.ad_id` and
`send_logs.group_id` are plain `Integer` columns with **no foreign key**
(`app/models/send_log.py:14-15`), so a stale id survives deletion of its target.
On PostgreSQL sequences do not reuse, so no leak. On SQLite — which is what the
entire test suite runs on — an `INTEGER PRIMARY KEY` without `AUTOINCREMENT`
assigns `max(rowid)+1` and **does** reuse ids after the highest row is deleted.
That means the invariant is not merely unasserted, it is one that the test
environment can violate while production cannot: a test could never catch a
regression here, and a future SQLite-backed deployment or fixture would silently
dispatch a message into another user's group.

`Schedule.group_ids` is likewise a JSON list with no FK and no ownership
constraint, so `upcoming_sends`' correctness rests on the schedule editor
validating ownership in another module.

**Fix:** Add the predicate. It costs nothing and makes the invariant local:

```python
select(Group.id, Group.is_active).where(
    Group.id.in_(group_ids), Group.user_id == user_id
)
select(Ad.id, Ad.status).where(Ad.id.in_(ad_ids), Ad.user_id == owner_id)
select(MessengerAccount.id, MessengerAccount.status).where(
    MessengerAccount.id.in_(account_ids), MessengerAccount.user_id == owner_id
)
```

(`retry_availability` needs the owner id threaded in as a parameter.)

### WR-13: Page size is still duplicated as a literal in four infinite-scroll sentinels

**Severity:** WARNING (prior WR-08 — still present, scope larger than reported)
**File:** `app/templates/history/list.html:117`, `app/templates/history/partial_cards.html:6`, `app/templates/admin/user_history.html:63`, `app/templates/admin/history_partial_cards.html:7`, `app/pages/history.py:42`

**Issue:** All four sentinels hard-code `&limit=30` while `PAGE_SIZE = 30` lives
in Python and drives `next_offset = offset + len(logs)` (`history.py:1027`); the
admin routes carry their own third copy as `page_size = 30` (`admin.py:191`) and
`limit: int = Query(30, ...)` (`admin.py:273`). Change any one and the second page
overlaps or skips records — silently, with a healthy-looking screen. This is the
exact failure mode the phase's own comments repeatedly single out ("литерал в
шаблоне разъехался бы с ним молча", `dashboard.py:129-131`).

**Fix:** `page_size` is already in the `history/list.html` context
(`history.py:1025`). Use `&limit={{ page_size }}` in all four templates, add the
key to the two partial contexts and to the admin contexts, and replace
`admin.py`'s literals with an import of `PAGE_SIZE`.

### WR-14: Every history row still carries `ad_text`/`ad_images` that no list template renders

**Severity:** WARNING (prior WR-09 — still present)
**File:** `app/pages/history.py:584-585`, `app/pages/history.py:949-950`, `app/pages/admin.py:221-222`, `app/pages/admin.py:305-306`

**Issue:** `"ad_text": r.ad_text or ""` and `"ad_images": r.ad_images or []` are
built into all four list-row dicts. `history/includes/history_card.html` renders
neither — only `history/detail.html:61-70` and the admin detail template do, and
both receive the ORM entity, not these dicts. Every list render and every
infinite-scroll tick therefore materialises up to 30 full ad-body snapshots
(`ad_text` is `Text`, unbounded) into a context that discards them.

**Fix:** Drop both keys from the four list-row builders.

### WR-15: A failure mid-stream still turns the export into a truncated file with HTTP 200

**Severity:** WARNING (prior WR-10 — deliberately deferred, re-reported)
**File:** `app/pages/history.py:703-747`

**Issue:** The row cap is checked before the response starts, precisely so a
partial file cannot be mistaken for a complete one (`history.py:663-684`). The
generator has no equivalent protection: any exception raised inside `body()`
after the first `yield` (DB error, dropped connection mid-cursor, serialization
error in `export_row`) terminates the body after `200 OK` and
`Content-Disposition` have been flushed. The user gets a CSV that opens, looks
complete and is short — the outcome D-27 exists to prevent, arriving by a
different door. The suite cannot observe it: `db.stream` is never made to fail,
and the docstring at 647-652 concedes the session-lifetime dependency is untested.

**Fix:** Catch inside the generator and make truncation self-announcing:

```python
try:
    result = await db.stream(query)
    async for log, group in result:
        writer.writerow(export_row(log, group, user))
        yield flush()
except Exception:
    logger.error("history_export_stream_failed", user_id=user.id, exc_info=True)
    writer.writerow(["ВЫГРУЗКА ОБОРВАНА — файл неполный"])
    yield flush()
    raise
```

### WR-16: Dead code still in `SendLogRepository`

**Severity:** WARNING (prior WR-11 — still present)
**File:** `app/repositories/send_log.py:37-61`, `app/repositories/send_log.py:20-35`

**Issue:** `list_for_user_with_details` has no caller anywhere in `app/` or
`tests/` (verified by grep across both trees); it also embeds presentation
defaults (`or "—"`) in the data-access layer. `list_for_user`'s `status_filter`
parameter is never passed by its single caller (`app/routes/history.py:82`). The
phase removed `get_stats` from this exact class with a nine-line comment about why
second definitions are forbidden, and left an unreachable method two lines below
it.

**Fix:** Delete `list_for_user_with_details` and the unused `status_filter`
parameter, or state in a comment that it is held for a named future phase.

### WR-17: `retry_availability`'s "account gone" branch cannot be reached in production

**Severity:** WARNING
**File:** `app/pages/history.py:489-490`

**Issue:** `Group.account_id` is a non-null FK with `ondelete="CASCADE"`
(`app/models/group.py:49-51`). Deleting a `MessengerAccount` deletes its groups,
so a state where the group row survives but its account does not cannot exist
under an FK-enforcing database. `verdict[log.id] = RETRY_REASON_ACCOUNT_GONE` is
therefore unreachable on PostgreSQL; such a send log resolves through the
`group is None` branch to `RETRY_REASON_GROUP_GONE` instead.

It *is* reachable under SQLite, where `PRAGMA foreign_keys` is off by default —
meaning any test asserting this branch is asserting behaviour the production
database cannot produce, and the reason string shown to a real user for this
situation will always be "Группа удалена", never "Аккаунт удалён".

This is not harmful, but it is a branch and a user-facing string that will never
execute, sitting in the middle of a chain whose whole purpose is to name causes
precisely (`history.py:402-415`).

**Fix:** Either delete the branch and its constant, or — better — keep it as
defence in depth and say so, so the next reader does not spend the time I did
confirming it is dead:

```python
# НЕДОСТИЖИМО при включённых внешних ключах: groups.account_id объявлен
# NOT NULL с ondelete=CASCADE, и удаление аккаунта уносит группу. Ветка
# оставлена защитой в глубину — SQLite не проверяет FK по умолчанию.
elif not group.account_id or group.account_id not in account_status:
```

## Info

### IN-01: Comment still references a template the phase deleted

**Severity:** WARNING (cosmetic) — prior IN-01, still present
**File:** `app/templates/dashboard/partial_feed.html:27`

**Issue:** "тот же приём уже потребовался в heatmap.html" — `heatmap.html` was
deleted by this phase. A reader following the cross-reference concludes the file
is missing rather than gone by design.

**Fix:** Point at the surviving example (`dashboard/includes/activity_chart.html`)
or drop the clause.

### IN-02: `session.get(MessengerAccount, ...)` guards disagree between the two retry paths

**Severity:** WARNING (cosmetic) — supersedes and downgrades prior WR-02
**File:** `app/worker/tasks.py:337-341`, `app/pages/history.py:861-865`

**Issue:** The worker guards with `if group else None`; the web handler guards
with `if group and group.account_id else None`. The prior review classified this
as a WARNING on the premise that `Group.account_id` is nullable and therefore
`session.get(Model, None)` is reachable. **That premise is wrong** —
`app/models/group.py:49-51` declares it `Mapped[int]` with a non-null FK, so no
persisted `Group` can carry a null `account_id` and the SQLAlchemy
"fully NULL primary key identity" warning cannot fire. What is left is two
spellings of the same guard in sibling code, which costs a reader time and
suggests a nullability that does not exist.

**Fix:** Make them identical — preferably the shorter one, since the extra
conjunct is now known to be dead:

```python
account = await session.get(MessengerAccount, group.account_id) if group else None
```

### IN-03: Raw `&` still used as a query separator in generated hrefs

**Severity:** WARNING (cosmetic) — prior IN-02, still present
**File:** `app/templates/history/includes/filter_chips.html:62`, `app/templates/history/list.html:117`, `app/templates/history/partial_cards.html:6`

**Issue:** `{% if not loop.first %}&{% endif %}` and `&limit=30` emit bare
ampersands inside `href`/`hx-get` attributes. Browsers recover; strict parsers and
HTML validators do not. The export link one line above gets it right
(`&amp;`, `list.html:101`), so the file is internally inconsistent.

**Fix:** Use `&amp;` throughout.

### IN-04: The export's "Аккаунт" column still emits a bare numeric id

**Severity:** WARNING (cosmetic) — prior IN-03, still present
**File:** `app/pages/history.py:252`

**Issue:** `export_cell(group.account_id if group else None)` writes `12` under a
header that reads "Аккаунт", while every screen renders the same value as
`Акк #12` (`history_card.html:196`). The neighbouring `Статус` and `Канал` columns
go to some length to print human labels; this one does not.

**Fix:** `export_cell(f"Акк #{group.account_id}" if group else None)`, or join the
account and export its type, matching the filter dropdown (`list.html:48`).

### IN-05: `.replace(hour=0, ...)` on a zone-aware datetime — now in two places

**Severity:** WARNING (cosmetic, latent) — prior IN-04, scope grew with the CR-03 fix
**File:** `app/application/analytics/send_analytics.py:721-724`, `app/application/analytics/send_analytics.py:323-325`

**Issue:** `datetime.now(tz).replace(hour=0, ...)` keeps the *current moment's*
UTC offset rather than midnight's, so in a DST zone the result is off by the DST
delta on transition days. The CR-03 fix introduced a second instance of the same
construct in `activity_heatmap`, where it is load-bearing: `offset_hours` is
computed from an aware-aware subtraction (true elapsed time) while the column is
`local.hour` (wall-clock hour), and on a 23- or 25-hour day those two disagree —
reintroducing the row/column mismatch CR-03 removed, in miniature.

The project ships 12 DST-free zones (`app/constants.py`), so this is latent, not
live. But the precondition is now relied on by two functions and is stated at
neither call site.

**Fix:** Normalise through the zone in both places, or name the DST-free-zones
precondition in a comment at each:

```python
local_midnight = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
local_midnight = local_midnight.replace(tzinfo=None).replace(tzinfo=tz)
```

Adding a DST zone to `app/constants.py` should be gated on fixing both.

---

## Not findings — verified and sound

Recorded so the next reviewer does not re-derive them:

* **Tenant isolation on the worker list (04-11).** `MessengerAccount.user_id ==
  user.id` in the query (`common.py:334`), pinned end-to-end by
  `test_dashboard_worker_list_excludes_another_users_account`.
* **No credential leakage.** Exactly three columns are projected;
  `credentials`/`session_data` are never loaded. Pinned by
  `test_shell_worker_list_carries_no_secrets`, which asserts against rendered
  HTML rather than intent — the right shape for this check.
* **No Docker SDK on the render path.** `app/pages/common.py` was added to
  `DASHBOARD_RENDER_PATH` in `test_shell.py:583-591`, so the prohibition now
  guards the module where the temptation moved.
* **Unknown worker statuses stay visible** rather than being filtered to a known
  list (`worker_row.html:35-37`), pinned with both a real and an invented status.
* **Cooldown survives the 302 and is keyed per record** (`history.py:498-517`,
  `848-899`), with tests for expiry, per-record keying, and both refusal paths
  arming no window.
* **CSRF, CSV formula injection, constant export filename, cap-before-stream
  ordering, and `retry_availability`'s "not ok" (rather than "in known-failure
  list") predicate** are all intact and correctly reasoned.
* **Migration 0016** is a pure index add/drop with a real round-trip test that
  pins row preservation and single-head history, and `monkeypatch.setenv` guards
  against the migration running against a developer's live database.

---

_Reviewed: 2026-08-15T12:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

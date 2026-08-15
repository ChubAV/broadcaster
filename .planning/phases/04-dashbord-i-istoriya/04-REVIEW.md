---
phase: 04-dashbord-i-istoriya
reviewed: 2026-08-15T06:43:39Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - alembic/versions/0016_send_logs_user_sent_at.py
  - app/application/analytics/__init__.py
  - app/application/analytics/send_analytics.py
  - app/application/scheduling/use_cases.py
  - app/main.py
  - app/pages/admin.py
  - app/pages/dashboard.py
  - app/pages/dashboard_feed.py
  - app/pages/history.py
  - app/repositories/send_log.py
  - app/routes/history.py
  - app/static/css/app.css
  - app/templates/dashboard.html
  - app/templates/dashboard/includes/activity_chart.html
  - app/templates/dashboard/includes/feed_row.html
  - app/templates/dashboard/includes/metric_tile.html
  - app/templates/dashboard/includes/recent_send_card.html
  - app/templates/dashboard/includes/upcoming_row.html
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
  critical: 3
  warning: 11
  info: 5
  total: 19
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-08-15T06:43:39Z
**Depth:** standard
**Files Reviewed:** 38 (one listed file, `app/templates/dashboard/includes/recent_send_card.html`, was deleted by the phase and does not exist)
**Status:** issues_found

## Summary

Multi-tenant isolation on the read paths is genuinely solid: every analytics
function takes `user_id` as a required keyword, every page/route query carries
`SendLog.user_id == user.id` or `Ad.user_id == user_id`, `/dashboard/feed` keeps
its own auth guard after being pulled out from under the shell router, and the
admin history routes scope by the *target* user under `require_admin`. Templates
have no `|safe` anywhere and the error text from external messengers is escaped.
The CSV export's formula-injection guard, the row cap-before-stream ordering, and
the constant filename are correct.

The serious defects are all on the **write** path — the retry feature — and in
the **post-UAT bar chart**.

The retry route re-implements a *subset* of the eligibility rules that
`collect_due_schedules` enforces before any real send. Two of those rules are
missing entirely: the ad-is-a-draft check and the group-is-disabled check. For
WhatsApp/MAX the retry payload goes straight into the Redis queue, bypassing
`send_message_once` (which is where the draft check lives for Telegram), so a
draft ad or a disabled group can be pushed to a third-party group irreversibly.
Neither gap has a single test.

The activity chart, added after UAT, folds the sliding-window heatmap grid into
28 chronologically-ordered bars — but the grid's rows are 24-hour windows
anchored at the *request time*, while its columns are hour-of-day. Folding
hour-of-day columns into a left-to-right timeline scrambles the order within
every day group and mislabels the day. The only tests of `activity_chart` feed it
a synthetic grid, so the end-to-end defect is invisible to the suite.

The module docstrings are unusually thorough, and in several places they assert
properties the code does not have (the double-submit guard; the retry check
list). Those are counted as findings — a docstring that overstates a guarantee is
worse than no docstring, because the next reader stops checking.

## Critical Issues

### CR-01: Retry dispatches DRAFT ads straight to the WhatsApp/MAX queues

**File:** `app/worker/tasks.py:303-376`, `app/pages/history.py:772-798`, `app/pages/history.py:394-436`

**Issue:** `retry_send` loads the ad by id and passes it to `build_dispatch_task`
without ever consulting `effective_ad_status(ad)`. For `account.type in ("wa",
"max")`, `dispatch_send_tasks` `rpush`-es the full payload (`ad_text`,
`ad_title`, resolved image URLs) into `wa:queue:<account_id>` /
`max:queue:<account_id>`; the Node worker reads that payload and sends it — it
never touches the database and has no notion of ad status.

The scheduler path is protected in two places (`collect_due_schedules`
`app/application/scheduling/use_cases.py:160-172` and `send_message_once`
`app/application/scheduling/use_cases.py:315-332`). The retry path reaches
neither for wa/max. For Telegram it happens to be caught by `send_message_once`,
which writes a `fail` log — so the vulnerability is channel-asymmetric and
invisible on the channel the tests exercise most.

The UI compounds it: `retry_availability` only checks that the `Ad` **row
exists**, so the "Повторить" button is rendered for a record whose ad the user
has since unpublished, and `history_retry` only re-checks entity presence and
`account.status`. The result: unpublishing an ad does not stop it from being
sent, and the send is irreversible and billable.

**Fix:** Add the draft predicate to all three layers, using the existing single
definition rather than a new literal.

```python
# app/worker/tasks.py — inside _run(), after the entity/account checks
from app.application.scheduling.use_cases import effective_ad_status
from app.constants import AD_STATUS_DRAFT

if effective_ad_status(ad) == AD_STATUS_DRAFT:
    log.warning("retry_send_stopped", reason="ad_is_draft", ad_id=ad.id)
    return

# app/pages/history.py — history_retry, alongside the existing gone-check
if not ad or effective_ad_status(ad) == AD_STATUS_DRAFT or not group or ...:
    return RedirectResponse(url=f"/history?retry={RETRY_GONE}", status_code=302)

# app/pages/history.py — retry_availability, so the button explains itself
RETRY_REASON_AD_DRAFT = "Объявление в черновике"
...
live_ads = {                      # select id AND status, not id alone
    row_id: status
    for row_id, status in (
        await db.execute(select(Ad.id, Ad.status).where(Ad.id.in_(ad_ids)))
    ).all()
}
```

### CR-02: Retry ignores `group.is_active` — sends into groups the user switched off

**File:** `app/worker/tasks.py:325-376`, `app/pages/history.py:773-798`, `app/pages/history.py:425-436`

**Issue:** `Group.is_active` is the user's own reversible off-switch, and the
scheduler honours it explicitly (`app/application/scheduling/use_cases.py:236-242`
— "D-05: выключенная группа задач отправки не получает"). Neither
`retry_availability`, nor `history_retry`, nor `retry_send` reads the flag. A
user who disables a group to stop sending to it can still push a message into it
from the history screen, and `send_message_once` will not stop it either — that
function never checks `is_active` because the scheduler is supposed to have
filtered already.

`upcoming_sends` in the same phase *does* read the flag (`send_analytics.py:513-535`),
which shows the invariant is known — it just was not carried into the write path.

**Fix:** Treat a disabled group the same way a detached account is treated, at
all three layers:

```python
# app/pages/history.py — retry_availability
RETRY_REASON_GROUP_OFF = "Группа выключена"
...
elif group is None:
    verdict[log.id] = RETRY_REASON_GROUP_GONE
elif not group.is_active:
    verdict[log.id] = RETRY_REASON_GROUP_OFF

# app/pages/history.py — history_retry
if not ad or not group or not group.is_active or not account or account.status != "active":
    return RedirectResponse(url=f"/history?retry={RETRY_GONE}", status_code=302)

# app/worker/tasks.py — second line of defence, silent like the others
if not group.is_active:
    log.warning("retry_send_stopped", reason="group_inactive", group_id=group.id)
    return
```

### CR-03: Activity chart bars are not in chronological order and carry the wrong day label

**File:** `app/application/analytics/send_analytics.py:373-400`, `app/application/analytics/send_analytics.py:304-336`, `app/templates/dashboard/includes/activity_chart.html:41-62`

**Issue:** `activity_heatmap` builds a grid whose **rows** are sliding 24-hour
windows anchored at `local_origin = now - days` (so at whatever local time the
page was requested) and whose **columns** are absolute hour-of-day
(`grid[day_index][local.hour]`, line 336). That is coherent for a heatmap read as
"hour of day × day". `activity_chart` then folds each row left-to-right into four
six-hour buckets (`day_row[start:start+6]`, line 395) and the template renders
those 28 buckets as a chronological timeline with one day label per group of
four.

Those two semantics are incompatible unless `local_origin` falls exactly on local
midnight. Worked example — page opened at 12:00 local, window origin 13.05 12:00
(this is the exact anchoring the suite itself asserts,
`tests/test_application/test_send_analytics.py:665-667`):

* row 6 spans **19.05 12:00 → 20.05 12:00**;
* a send at **20.05 09:00** → `offset 165h` → row 6, hour 9 → **bar 25**;
* a send at **19.05 20:00** → `offset 152h` → row 6, hour 20 → **bar 27**.

The send that happened 13 hours *earlier* is drawn two positions to the *right*.
The bucket "12-17" of that row mixes 19.05 12:00-17:59 with 20.05 12:00-14:59 —
records ~21 hours apart in one bar. And `day_labels[6]` is the weekday of 19.05,
although half of the row's data is from 20.05.

The five `activity_chart` tests (`test_send_analytics.py:1141-1198`) only feed a
hand-built grid to the pure fold, and the page test only counts
`data-chartcol` occurrences (`tests/test_pages/test_responsive_markup.py:701-724`),
so nothing in the suite observes the end-to-end ordering. The module comment at
`send_analytics.py:375-381` ("столбец есть сумма своих шести часов") asserts a
property that does not hold.

**Fix:** Anchor the window on the reader's local midnight so rows are calendar
days and column order equals chronological order. This also makes the day labels
true.

```python
# activity_heatmap
local_now = normalize_utc(now).astimezone(tz)
local_origin = (local_now.replace(hour=0, minute=0, second=0, microsecond=0)
                - timedelta(days=days - 1))
window_start = local_origin.astimezone(timezone.utc)   # query bound follows the grid
```

With that, row `i` is a calendar day, `grid[i][h]` is hour `h` of that day, and
`activity_chart`'s slice fold is chronological by construction. Add a test that
asserts bar index ordering for two sends on either side of local midnight — the
current test set cannot fail on this defect.

## Warnings

### WR-01: The double-submit guard does not stop a double submit, and its docstring says it does

**File:** `app/pages/history.py:344-356`, `app/pages/history.py:769`, `app/pages/history.py:799-800`

**Issue:** `_release_retry_slot` runs in the `finally` block that closes
immediately after `celery.send_task` returns — i.e. the slot is held for the few
milliseconds of the handler and released before the 302 is even sent. Two
sequential clicks therefore queue two sends; the project's own test asserts
exactly that (`tests/test_pages/test_history_retry.py:702-719`,
`assert len(env.queued) == 2`), and the "busy" test only passes because it claims
the slot manually beforehand. The docstring at line 748-750 nonetheless states
"второе нажатие в пределах процесса второй задачи не ставит", and the registry
comment (lines 348-355) presents the multi-process case as the *only* limitation.

**Fix:** Either make the docstring honest (the registry prevents *concurrent*
overlap only, not repeat submissions), or give the guard a time window so it
matches the claim:

```python
_RETRY_IN_FLIGHT: dict[int, float] = {}
RETRY_COOLDOWN_SECONDS = 30

def _claim_retry_slot(log_id: int) -> bool:
    now = time.monotonic()
    claimed_at = _RETRY_IN_FLIGHT.get(log_id)
    if claimed_at is not None and now - claimed_at < RETRY_COOLDOWN_SECONDS:
        return False
    _RETRY_IN_FLIGHT[log_id] = now
    return True
```

and drop `_release_retry_slot` from the success path (keep it for the exception
path only), otherwise the cooldown never applies.

### WR-02: `session.get(MessengerAccount, None)` when the group has no account

**File:** `app/worker/tasks.py:337-341`

**Issue:** The guard is `if group else None`, not `if group and group.account_id
else None`. `Group.account_id` is nullable, so `session.get(MessengerAccount,
None)` is reachable. SQLAlchemy answers a fully-NULL identity with
`util.warn("fully NULL primary key identity cannot load any object. This
condition may raise an error in a future release.")` and returns `None` — so the
behaviour is accidentally correct today, produces log noise, and is documented by
SQLAlchemy as subject to becoming an error. The sibling code in
`app/pages/history.py:776-780` guards it properly, so the two paths disagree.

**Fix:**

```python
account = (
    await session.get(MessengerAccount, group.account_id)
    if group and group.account_id
    else None
)
```

### WR-03: The retry balance gate is only in the web handler, never re-checked at execution

**File:** `app/pages/history.py:786-798`, `app/worker/tasks.py:303-376`

**Issue:** `history_retry` calls `check_balance_cached` before enqueueing, and the
task docstring (`tasks.py:317-321`) explicitly argues that broker arguments are
their own trust boundary and re-checks *ownership* there — but not the balance.
A retry task can sit in a Redis/Celery queue behind a backlog and execute long
after the balance is spent; `deduct_message` then runs unconditionally on success
(`tasks.py:699-701` / `807-809`). The scheduler does not have this asymmetry: its
gate runs in the same tick as the dispatch.

**Fix:** Re-run the gate inside `retry_send` next to the entity checks, using the
same helper the handler uses:

```python
from app.services.billing_cache import check_balance_cached
allowed, _reason = await check_balance_cached(session, user_id, "send")
if not allowed:
    log.warning("retry_send_stopped", reason="no_balance")
    return
```

### WR-04: Admin history routes skip the `_clean_choice` normalisation the user-facing routes enforce

**File:** `app/pages/admin.py:193-208`, `app/pages/admin.py:280-295`

**Issue:** `history_partial`, `history_list` and `history_export` all pass query
values through `_clean_choice(...)` before they reach `apply_history_filters`
(`app/pages/history.py:479-481`, `583-585`, `822-824`) — the module docstring at
`history.py:93-111` calls this the point of enforcement. The two admin history
routes call `apply_history_filters` with the **raw** `status`, `messenger` and
`period` strings. Consequences: an unknown `status` silently produces an empty
list with no chip marked active, and the raw string is echoed back into
`filter_params` → the scroll-sentinel URL and the template context. It is not an
injection (all values are bound parameters), but it is the same class of "mусор
не выбирает ничего" defect the user routes were explicitly written to avoid.

**Fix:** Reuse the existing helpers instead of duplicating them:

```python
from app.pages.history import _clean_choice, MESSENGER_VALUES, PERIOD_VALUES, STATUS_VALUES
...
status = _clean_choice(status, STATUS_VALUES)
messenger = _clean_choice(messenger, MESSENGER_VALUES)
period = _clean_choice(period, PERIOD_VALUES)
```

(Better: promote `_clean_choice` and the three value sets to a non-underscore
public surface — see WR-05.)

### WR-05: `app/pages/admin.py` imports a private name from `app/pages/history.py`

**File:** `app/pages/admin.py:14`

**Issue:** `from app.pages.history import _parse_account_id` — a leading-underscore
name crossing a module boundary. The phase moved the *shared* filter definitions
into `app/application/analytics/send_analytics.py` precisely so consumers would
not reach into each other, and then reached anyway for the one helper that was
left behind. Any future rename of `_parse_account_id` (a name that signals "safe
to rename") breaks the admin section, and only at import time.

**Fix:** Rename to `parse_account_id` and export it, or move it next to the other
shared HTTP-parsing helpers. If it stays private, duplicate the four lines in
admin rather than importing across the underscore.

### WR-06: No upper time bound on the metrics/heatmap windows — future rows are counted and clamped

**File:** `app/application/analytics/send_analytics.py:175-204`, `app/application/analytics/send_analytics.py:313-336`

**Issue:** Both queries bound `sent_at` only from below (`>= previous_start`,
`>= window_start`). A row with `sent_at` in the future (clock skew between the
Celery worker and the DB, or `now` passed explicitly by a caller — which is
exactly what Phase 6 and every test do) is counted in the current window by
`send_metrics`, and is silently clamped into the newest row by
`activity_heatmap` (`day_index >= days → days - 1`, lines 332-333). The clamp
comment justifies clamping the record *exactly at* `now`; it silently also
absorbs records arbitrarily far past `now`, which is a different case.

**Fix:** Bound the window on both sides and keep the boundary record in the last
bucket:

```python
).where(
    SendLog.user_id == user_id,
    SendLog.sent_at >= previous_start,
    SendLog.sent_at <= now,
)
```

and in `activity_heatmap` add `SendLog.sent_at <= now` to the stream query, so
the clamp only ever handles the exact-boundary record it documents.

### WR-07: Lookups inside the analytics/retry helpers are not user-scoped

**File:** `app/application/analytics/send_analytics.py:517-522`, `app/pages/history.py:398-422`, `app/pages/history.py:773-780`

**Issue:** The module docstring states the invariant plainly ("ветки «по всем
пользователям» здесь нет вовсе — её отсутствие и есть проверяемая форма
T-04-01"), and `test_heatmap_ignores_other_users` asserts it. But three
secondary queries break it:

* `select(Group.id, Group.is_active).where(Group.id.in_(group_ids))` — no
  `Group.user_id == user_id`;
* `select(Ad.id).where(Ad.id.in_(ad_ids))` and
  `select(MessengerAccount.id, MessengerAccount.status).where(...in_(account_ids))`
  in `retry_availability` — no owner predicate;
* `db.get(Group, ...)`, `db.get(Ad, ...)`, `db.get(MessengerAccount, ...)` in
  `history_retry`.

Today the ids are all derived from rows the caller already proved it owns, so
nothing leaks. But `Schedule.group_ids` is a JSON list with no FK and no
ownership constraint, which means the safety of `upcoming_sends` rests entirely
on the schedule editor validating group ownership — a property enforced in
another module and not asserted here.

**Fix:** Add the owner predicate; it costs nothing and makes the invariant local.

```python
select(Group.id, Group.is_active).where(
    Group.id.in_(group_ids), Group.user_id == user_id
)
select(Ad.id).where(Ad.id.in_(ad_ids), Ad.user_id == user.id)
select(MessengerAccount.id, MessengerAccount.status).where(
    MessengerAccount.id.in_(account_ids), MessengerAccount.user_id == user.id
)
```

(`retry_availability` needs the owner id threaded in as a parameter.)

### WR-08: Page size is duplicated as a literal in the infinite-scroll sentinel

**File:** `app/templates/history/list.html:117`, `app/pages/history.py:36`

**Issue:** `hx-get="/history/partial?offset={{ next_offset }}&limit=30..."`
hard-codes 30 while `PAGE_SIZE = 30` lives in Python and drives `next_offset =
offset + len(logs)`. Changing `PAGE_SIZE` yields overlapping or skipped records
on the second page — silently, with a healthy-looking screen. This is the exact
failure mode the phase's own comments repeatedly single out ("литерал в шаблоне
разъехался бы с ним молча" — `app/pages/dashboard.py:123-125`), applied
everywhere except here.

**Fix:** Pass the constant into the template context (`"page_size": PAGE_SIZE`
is already in the `history/list.html` context, line 926) and use it:
`&limit={{ page_size }}`. Mirror the change in
`app/templates/history/partial_cards.html`, whose sentinel must stay identical.

### WR-09: Every history row carries `ad_text`/`ad_images` that no list template renders

**File:** `app/pages/history.py:504-524`, `app/pages/history.py:846-864`, `app/pages/admin.py:217-233`, `app/pages/admin.py:300-316`

**Issue:** The row dicts include `"ad_text": r.ad_text or ""` and `"ad_images":
r.ad_images or []`. `history/includes/history_card.html` renders neither — only
`history/detail.html` and `admin/user_history_detail.html` do, and both receive
the ORM entity, not these dicts. So every list render and every infinite-scroll
tick materialises up to 30 full ad-body snapshots into a context that discards
them.

**Fix:** Drop both keys from the four list-row builders. If a future card design
wants a preview, add it back with an explicit truncation.

### WR-10: A failure mid-stream turns the export into a truncated file with HTTP 200

**File:** `app/pages/history.py:628-672`

**Issue:** The row cap is checked before the response starts, precisely so a
partial file cannot be mistaken for a complete one (`history.py:588-593`,
`166-168`). But the generator itself has no such protection: any exception raised
inside `body()` after the first `yield` (DB error, connection drop mid-cursor,
serialization error in `export_row`) terminates the response body after the
status line `200 OK` and the `Content-Disposition` header have already been
flushed. The user gets a CSV that opens, looks complete and is short — the exact
outcome D-27 was written to prevent, arriving by a different door. The suite
cannot see it: `db.stream` is never made to fail, and the docstring itself
concedes the session-lifetime dependency is untested.

(For the record, the framework claim *does* hold on the pinned version:
`fastapi/routing.py:101-108` in 0.129.0 exits the request-scope `AsyncExitStack`
— where `Depends(get_db)` lives — after `await response(scope, receive, send)`.
This is undocumented internal ordering, so the dependency is real and fragile.)

**Fix:** Catch inside the generator and make the truncation self-announcing, and
consider owning the session instead of borrowing the request-scoped one:

```python
async def body():
    ...
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

### WR-11: Dead code left in `SendLogRepository` after the phase removed its consumer

**File:** `app/repositories/send_log.py:20-61`

**Issue:** `list_for_user_with_details` has no caller anywhere in `app/` or
`tests/` (verified by grep across both trees); it also embeds presentation
defaults (`or "—"`) in the data-access layer. `list_for_user`'s `status_filter`
parameter is likewise never passed by its single caller
(`app/routes/history.py:82`). The phase removed `get_stats` from this exact class
with a nine-line comment about why second definitions are forbidden, and left an
unreachable method two lines below it — while `app/pages/dashboard.py:104-105`
states the phase's rule as "недостижимых шаблонов в проекте не оставляют".

**Fix:** Delete `list_for_user_with_details` and the unused `status_filter`
parameter. If it is being kept for a future phase, say so in a comment as was
done for `activity_heatmap`.

## Info

### IN-01: Comment references a template the phase deleted

**File:** `app/templates/dashboard/partial_feed.html:27`

**Issue:** "тот же приём уже потребовался в heatmap.html" — `heatmap.html` was
deleted by this phase. The cross-reference now points at nothing, and a reader
following it will conclude the file is missing rather than gone by design.

**Fix:** Reword to reference the surviving example
(`dashboard/includes/activity_chart.html`, which uses the same "no table markup
even in comments" discipline) or drop the clause.

### IN-02: Raw `&` used as a query separator in generated hrefs

**File:** `app/templates/history/includes/filter_chips.html:62`, `app/templates/history/list.html:117`

**Issue:** `{% if not loop.first %}&{% endif %}` emits a bare ampersand inside an
`href`/`hx-get` attribute. Browsers recover, but it is invalid HTML and will trip
any strict parser or HTML validator in CI. The sibling export link one line above
gets it right (`&amp;`, `list.html:101`), so the file is internally inconsistent.

**Fix:** Use `&amp;` in both places.

### IN-03: The export's "Аккаунт" column emits a bare numeric id

**File:** `app/pages/history.py:246`

**Issue:** `export_cell(group.account_id if group else None)` writes `12` under a
header that says "Аккаунт". Everywhere on screen the same value is rendered as
`Акк #12` (`history/includes/history_card.html:196`). The neighbouring columns
(`Статус`, `Канал`) go to great lengths to print human labels; this one does not.

**Fix:** Either format it consistently (`f"Акк #{group.account_id}"`) or join the
account and export its type/name, matching what the filter dropdown shows
(`history/list.html:48`).

### IN-04: `_period_cutoff("today")` uses `.replace()` on a zone-aware datetime

**File:** `app/application/analytics/send_analytics.py:697-700`

**Issue:** `datetime.now(tz).replace(hour=0, ...)` keeps the *current moment's*
UTC offset rather than midnight's. For a zone with DST this yields a cutoff off
by the DST delta on transition days. The project currently ships 12 DST-free
zones (`app/constants.py`), so this is latent rather than live — but the
constraint is not stated at the call site, and the "today" filter is exactly the
place it would surface.

**Fix:** Normalise through the zone:

```python
local_midnight = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
local_midnight = local_midnight.replace(tzinfo=None).replace(tzinfo=tz)  # or use fold-aware localize
return local_midnight.astimezone(timezone.utc)
```

or add a comment naming the DST-free-zones precondition next to the `.replace()`.

### IN-05: CSRF protection is header-only and scoped to one route

**File:** `app/pages/history.py:302-341`

**Issue:** `_is_same_origin` allows any request that sends neither
`Sec-Fetch-Site` nor `Origin`, and the check exists only on `/history/{id}/retry`
— every other state-changing POST in the project (admin balance/unlimited/block/
delete, all deletion forms) has none. The docstring names both limits honestly.
Worth recording that the actual mitigation carrying the load is
`samesite="lax"` on the auth cookie (`app/pages/auth.py:55,329`), which is not
mentioned in the reasoning; if that attribute is ever relaxed, the header check
alone will not hold. Note also that the cookie is set without `secure=True`.

**Fix:** No change required for this phase. When the project adopts a CSRF
scheme, make it a router-level dependency rather than per-handler, and record the
`samesite="lax"` dependency in the phase security report so the two decisions
stay linked.

---

_Reviewed: 2026-08-15T06:43:39Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 11-massovyy-perevod-razdelov-pisma
reviewed: 2026-09-17T09:01:18Z
depth: standard
files_reviewed: 68
files_reviewed_list:
  - app/main.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/billing.py
  - app/pages/history.py
  - app/pages/htmx.py
  - app/pages/identifiers.py
  - app/pages/notices.py
  - app/pages/profile.py
  - app/pages/schedules.py
  - app/static/css/app.css
  - app/templates/account_groups/list.html
  - app/templates/accounts/connect_max.html
  - app/templates/accounts/includes/max_connect_step.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/admin/includes/user_access_tile.html
  - app/templates/admin/includes/user_actions.html
  - app/templates/admin/includes/user_block_badge.html
  - app/templates/admin/partials/user_actions_response.html
  - app/templates/admin/queue.html
  - app/templates/admin/user_detail.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/partials/sched_card_response.html
  - app/templates/ads/partials/sched_create_response.html
  - app/templates/billing/balance.html
  - app/templates/components/modal.html
  - app/templates/includes/htmx_config.html
  - app/templates/includes/notice_area.html
  - app/templates/includes/profile_settings.html
  - app/templates/profile.html
  - app/templates/schedules/includes/schedule_row.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - app/templates/schedules/partials/schedule_row_response.html
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_billing_payment_errors.py
  - tests/test_pages/test_billing_subscription.py
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_htmx_response_contract.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_htmx_validation_sink.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_max_connect_transport.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_notices_registry.py
  - tests/test_pages/test_profile.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedules_list.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_sync_groups.py
  - tests/test_routes/test_wa_sync_status.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_htmx_markup_security.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-09-17T09:01:18Z
**Depth:** standard
**Files Reviewed:** 68
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

I reviewed the phase diff (`df26e76..HEAD`) for all 68 files, looking at what changed and the code around it. I read the Python page modules and templates with comments and docstrings stripped, so the findings are about code, not prose. For the test modules I looked for vacuous or never-red assertions and checked traversal/sink rules against the code they guard.

The response layer (`app/pages/htmx.py`) holds up under adversarial tracing:
- `_local_path` and `_confirmation_url` reject open-redirect, userinfo, backslash, port, control-character and non-ASCII tricks. `urlsplit`/`.port` failures are `ValueError` and are caught.
- `malformed_request_response` correctly narrows the empty-400 branch to page-layer endpoints.
- `_glue_notice` recomputes `content-length`.
- `respond_field_error` rebuilds a fresh 422 and does not mutate the builder's response.

The claims about the vendored htmx 2.0.10 match the artifact: `HX-Location` is read before `HX-Redirect`, and both are read before `responseHandling`. `expire_on_commit=False` makes the post-commit fragment renders safe. `QUEUE_DROP_NOTICE_CODES[outcome]` is total over what `drop_task` can return.

No blockers. The defects below are:
- a known-open 500 left in a handler the phase converted, although the phase added the one-line helper that closes it;
- a create-response branch keyed on server state that can disagree with the DOM;
- post-commit fragment builders that crash with a 500 after the write has already happened.

Known items were not re-reported: WINDOWS 63/84/85/86/87, and the 11-UI-REVIEW items (MAX failure dead-end, `disabled_elt`, focus loss, 422 banners). Pre-existing unchanged omissions of `is_same_origin` on schedule create/update/toggle and MAX start are also outside this diff.

## Warnings

### WR-01: `POST /ads/new` still sends an unbounded `ad_id` to SQL, so it returns a 500. The handler was converted this phase and `id_in_column` exists.

**File:** `app/pages/ads.py:698-708`
**Issue:** `ads_create` parses the form string with `requested_id = int(ad_id)` and uses it directly in `select(Ad).where(Ad.id == requested_id, ...)`. There is no range check. `ad_id=99999999999999999999999999` raises `OverflowError` on SQLite / `DataError` on asyncpg, which is a 500. The suite has recorded this with `verdict="open"` since 2026-09-08 (`tests/test_pages/test_identifier_bounds.py:1530-1548`).

Phase 11 did three things around this:
- converted this exact handler onto `respond()`;
- introduced `id_in_column` precisely so that out-of-column POST identifiers take the "row missing" branch (D-07);
- added `test_every_post_identifier_is_checked_before_its_first_use`.

That gate only recognises the `Post*` aliases, so a `str` parameter coerced inside the body is invisible to it. The phase's own invariant ("first use of a POST identifier is `id_in_column`") is therefore false for one POST input, and the gate stays green. Worse, the 500 lands on the htmx transport as a banner, not as the `_inaccessible` fragment that every other "not yours / not there" case gets.
**Fix:**
```python
    try:
        requested_id = int(ad_id)
    except ValueError:
        requested_id = None
    if requested_id is not None and id_in_column(requested_id):
        ad = (
            await db.execute(
                select(Ad).where(Ad.id == requested_id, Ad.user_id == user.id)
            )
        ).scalar_one_or_none()
```
Then flip the appendix entry to closed. Better still, widen `_first_use_is_checked` to also cover `int(<param>)` coercions of `str` form fields, so the next one is caught.

### WR-02: Schedule creation picks fragment vs `HX-Location` from the server count, but the form's swap target was frozen when the page rendered. A stale editor silently drops the new card.

**File:** `app/pages/schedules.py:1125-1132`, `app/templates/ads/form.html:203-249, 276-278`
**Issue:** The editor prints the create form with `target='#sched-list' if editor.schedules else none`. With no target, `form_wrapper` emits `hx-swap="none"`. `#sched-list` and `#sched-count` exist only inside `{% if editor.schedules %}`. The handler decides the response shape from `_ad_schedule_count(...) == 1`, i.e. the database after the insert, not from what the requesting document contains.

When the two disagree, the user sees nothing. For example: an editor opened at zero schedules while another tab or session already added one, so the server count is 2. The server returns the card fragment. htmx swaps it nowhere (`hx-swap="none"`), and the OOB `innerHTML:#sched-count` has no target (`htmx:oobErrorNoTarget`). The schedule is committed, but the page still shows the empty state and "+ ДОБАВИТЬ ПЕРВОЕ". The next click creates a duplicate. The code comment explicitly calls "a button that does NOTHING and says nothing" the failure this conditional target was meant to prevent; this path brings it back from the server side.
**Fix:** Let the client tell the server whether an insertion target exists, instead of inferring it. For example, add a hidden `<input type="hidden" name="has_list" value="1">` only when `editor.schedules` is truthy, and branch on it:
```python
    list_on_screen = form_data.get("has_list") == "1"
    if not list_on_screen:
        return await respond(request, redirect=screen_url)
```
The value only selects between two server-built responses of the same outcome, so it grants nothing. Alternatively, keep the count check but also require the flag, so either signal falls back to `HX-Location`.

### WR-03: Fragment builders run after `commit()` and crash when the row is gone, giving a 500 after a successful write.

**File:** `app/pages/schedules.py:1158, 1338, 1525-1530, 1558`
**Issue:** Every deferred fragment re-reads the record it just wrote and assumes it is still there:
- `card = next(s for s in editor["schedules"] if s.id == ...)` has no default. Inside a coroutine, the `StopIteration` becomes `RuntimeError: coroutine raised StopIteration`.
- `_row_fragment` does `row = (...).first()` and then `row.Schedule` (`AttributeError` on `None`).

If the schedule or its ad is deleted between the commit and the fragment read (a second tab, an admin deleting the user, or `delete_account`), the request answers 500 although the toggle, update or create was already committed. `schedules_toggle` (lines 1398-1401) cites the WR-07 rule that "a 500 after a completed write is indistinguishable from nothing happened". These builders reintroduce exactly that on the htmx path.
**Fix:** Fall back to the degradation address when the re-read comes back empty:
```python
        card = next((s for s in editor["schedules"] if s.id == schedule_id), None)
        if card is None:
            return location_response(screen_url)  # or restructure so respond() chooses
```
For `_row_fragment`, add `if row is None: return location_response(screen_url)`. Since `respond()` calls the builder itself, the cleanest version reads the row before calling `respond()` and passes `fragment=None` when it is missing.

## Info

### IN-01: The HTTP hostile-phone test cannot go red for the property it names

**File:** `tests/test_pages/test_max_connect_transport.py:208-224`
**Issue:** `test_a_hostile_phone_never_reaches_the_response_raw` posts `HOSTILE_PHONE`, which is not blank, so the request takes the success/QR branch. That branch never prints the phone at all (`_max_step_markup(step="qr", ...)` gets no `phone`). The assertion passes whether or not escaping works. The echo channel (the 422 branch) is only reachable over HTTP with whitespace-only values, and those cannot carry markup. The real proof is the unit test `test_the_phone_echo_is_autoescaped_in_the_step_markup`.
**Fix:** Delete the HTTP test, or rename it to say what it really checks ("the success step does not reflect the phone"), and add a positive check that the phone value is absent from the QR step.

### IN-02: Schedule-partial test URLs still send the removed `offset` cursor

**File:** `tests/test_pages/test_responsive_markup.py:3373, 4401`
**Issue:** `/schedules/partial` switched from `offset` to `after_id` this phase (`app/pages/schedules.py:811`). These tests still request `?offset=0&limit=30`. FastAPI ignores the unknown parameter, so the tests pass by accident and describe a contract that no longer exists.
**Fix:** Use `/schedules/partial?limit=30`, or pass `after_id`, in both places.

### IN-03: `redirect_external` promises "never a 500" but only catches `ValueError`

**File:** `app/pages/htmx.py:383-391`
**Issue:** The docstring says a failed check yields "a loud log line and a transition with a code, not a 500". `_confirmation_url` and `_host_for_the_journal` handle only `ValueError`. A non-`str` `url` (for example `None` from an unexpected SDK payload) raises `TypeError` in the first `any(ord(char) ...)` loop and escapes as a 500 after the payment intent was created.
**Fix:** Guard the type first: `if not isinstance(url, str): raise ValueError(...)` at the top of `_confirmation_url`, and make `_host_for_the_journal` return `None` for non-`str` input.

---

_Reviewed: 2026-09-17T09:01:18Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 02-obyavleniya-i-raspisaniya
reviewed: 2026-08-11T00:00:00Z
depth: standard
files_reviewed: 52
files_reviewed_list:
  - alembic/versions/0013_ad_status.py
  - app/application/accounts/use_cases.py
  - app/application/scheduling/use_cases.py
  - app/constants.py
  - app/main.py
  - app/models/ad.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/dashboard.py
  - app/pages/schedules.py
  - app/routes/ads.py
  - app/routes/schedules.py
  - app/routes/uploads.py
  - app/services/image_keys.py
  - app/services/schedule_rules.py
  - app/static/css/app.css
  - app/templates/ads/form.html
  - app/templates/ads/includes/ad_card.html
  - app/templates/ads/includes/autosave.html
  - app/templates/ads/includes/autosave_response.html
  - app/templates/ads/includes/preview.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/summary.html
  - app/templates/schedules/includes/schedule_row.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - tests/conftest.py
  - tests/test_application/test_account_deletion_schedules.py
  - tests/test_application/test_collect_due_draft.py
  - tests/test_migrations/__init__.py
  - tests/test_migrations/test_0013_ad_status.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_ads_image_ownership.py
  - tests/test_pages/test_ads_status.py
  - tests/test_pages/test_attachment_history_integrity.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedule_creation_path_exists.py
  - tests/test_pages/test_schedule_ownership.py
  - tests/test_pages/test_schedules_detached_account.py
  - tests/test_pages/test_schedules_list.py
  - tests/test_pages/test_schedules_poisoned_row.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_ads.py
  - tests/test_routes/test_schedules.py
  - tests/test_routes/test_schedules_api_null.py
  - tests/test_routes/test_schedules_api_ownership.py
  - tests/test_routes/test_schedules_profile_timezone.py
  - tests/test_routes/test_schedules_toggle_detached.py
  - tests/test_routes/test_uploads.py
  - tests/test_templates/test_components.py
findings:
  critical: 0
  warning: 2
  info: 7
  total: 9
status: issues_found
---

# Phase 02: Code Review Report (post-gap-closure round)

**Reviewed:** 2026-08-11
**Depth:** standard
**Files Reviewed:** 52
**Status:** issues_found

## Summary

This is the second review round for phase 02, after the gap-closure plans
02-13/02-14 addressed CR-01..CR-04 from the prior review. All 52 listed files
were read; the phase test suite was executed (167 tests in the seven core files,
all passing).

**Prior-finding closure verification — all four closures are complete and sound:**

- **CR-01 (body `ad_id` on `/ads/new`)** — closed. `ads_create`
  (`app/pages/ads.py:427-496`) confirms ownership with a single
  `Ad.id == requested_id AND Ad.user_id == user.id` query, treats non-numeric
  values as nonexistent, and the htmx refusal OOB-resets `#ad-id-field` without
  creating a record. Covered by `test_body_ad_id_from_another_user_is_refused`.
- **CR-02 (group ownership on JSON input / SVG content sniffing on uploads)** —
  closed. `owned_group_ids` (`app/services/schedule_rules.py`) is applied on both
  create and update in `app/routes/schedules.py`; `sniff_image` in
  `app/routes/uploads.py` ignores the client Content-Type entirely, including on
  the write to storage. Test coverage is thorough on both.
- **CR-03 (explicit JSON null poisoning schedules)** — closed on both lines:
  `reject_explicit_null` validator (`app/routes/schedules.py:49-56`) returns 422
  before any `setattr`, and the templates guard with `or []`
  (`sched_card.html:66`, `schedule_row.html:110`). Verified by
  `test_schedules_api_null.py` and `test_schedules_poisoned_row.py`.
- **CR-04 (autosave overlap losing the created draft id)** — closed.
  `hx-sync="this:queue last"` on `#ad-form` (`ads/form.html:66`), queued request
  serialized after the OOB swap of `#ad-id-field`; guarded by
  `test_save_during_autosave_overlap_lands_in_one_published_ad` and the markup
  assertions in `test_editor_form_carries_autosave_and_stays_a_real_form`
  (including the negative `this:replace not in html`).

The remaining findings below are new. No critical issues; two warnings concern
(a) the editor summary promising sends for draft ads — the exact promise the
summary list was explicitly fixed to avoid — and (b) the JSON schedule input
lacking the time/day validation the page layer received in T-02-24/T-02-25,
which violates the phase's own "one rule for both entrances" doctrine.

## Warnings

### WR-01: Editor summary and preview promise sends for a draft ad

**File:** `app/pages/ads.py:166-253` (`_editor_context`),
`app/templates/ads/includes/summary.html:38-46`,
`app/templates/ads/includes/preview.html:27-33`
**Issue:** `_editor_context` computes `next_run_at` (min over the ad's
schedules) and `channels` without consulting `ad.status`. For a **draft** ad
with a complete, active schedule — an easily reachable state, because
`schedules_create` does not gate on ad status and a first-saved ad is a draft
(D-03) — the editor summary renders «Ближайший запуск {дата}» and the preview
renders «Уйдёт в Telegram», both promising a send that D-01 guarantees will
never happen. This is exactly the promise the summary list was fixed to avoid:
`schedule_row.html:128-135` renders «отправок не будет» when `item.is_draft`.
The guard test `test_editor_of_a_draft_ad_says_there_will_be_no_sends`
(tests/test_pages/test_ads_status.py:275) passes only because it seeds a draft
**without** schedules, where `next_run_at` is `None` for an unrelated reason.
The two owner screens now disagree about the same schedule: the summary list
says "no sends", the editor says "next run 15.08 09:00".
**Fix:** apply the same draft guard in the editor context (single source, per
D-02 discipline):

```python
# app/pages/ads.py, _editor_context, after computing runs:
is_draft = ad is not None and ad.status != AD_STATUS_PUBLISHED
next_run_at = None if is_draft else (min(runs) if runs else None)
```

and extend the guard test with a draft ad that has an active schedule (assert
«отправок не будет» still renders and no date is shown). Consider suppressing
the «Уйдёт в …» channel caption for drafts as well (`preview.html`), since it
carries the same promise.

### WR-02: JSON schedule input accepts malformed times/days the page layer rejects — 500s and a toggle-bricking state

**File:** `app/routes/schedules.py:19-33` (`CreateScheduleRequest`),
`app/routes/schedules.py:35-63` (`UpdateScheduleRequest`),
`app/services/schedule_service.py:25-28` (unprotected parse)
**Issue:** T-02-24/T-02-25 added `_TIME_RE` and `_clean_ints(low=0, high=6)` on
the **page** entrance precisely because `compute_next_run_at` parses
`int(parts[0])` / `parts[1]` with no protection. The **JSON** entrance received
no equivalent: `times_of_day: list[str]` and `days_of_week: list[int]` accept
arbitrary content. Consequences, all reproducible by the authenticated owner:

1. `POST /api/schedules` with `times_of_day: ["junk"]` → `ValueError` in
   `compute_next_run_at` → 500 instead of 422 (`"10"` → `IndexError`,
   `"25:00"` → `ValueError`).
2. `PUT /api/schedules/{id}` with `times_of_day: ["junk"]` on a **paused**
   schedule: `is_schedule_complete` is truthy (non-empty list), `is_active` is
   False, so `compute_next_run_at` is never called and the junk value is
   **stored**. After that, every resume attempt — page toggle
   (`app/pages/schedules.py:732`) and API toggle
   (`app/routes/schedules.py:276`) — crashes with 500. The poisoned-row second
   line (CR-03) covers `None`, not junk strings.
3. `days_of_week: [99]` on create passes validation, yields
   `next_run_at=None`, and the schedule is stored `is_active=True` (model
   default) — displayed «Активно» with no next run, silently dead.

This is the same "rule lives on one entrance only" class the phase closed as
WR-05/CR-02, still open for value format.
**Fix:** validate in the schemas, sharing the definition with the page layer
(move `_TIME_RE` into `app/services/schedule_rules.py`):

```python
@field_validator("times_of_day")
@classmethod
def validate_times(cls, v):
    if v is None:
        return v
    bad = [t for t in v if not isinstance(t, str) or not TIME_RE.fullmatch(t.strip())]
    if bad:
        raise ValueError(f"Invalid time values: {bad}")
    return v

@field_validator("days_of_week")
@classmethod
def validate_days(cls, v):
    if v is None:
        return v
    if any(not isinstance(d, int) or not 0 <= d <= 6 for d in v):
        raise ValueError("days_of_week values must be 0..6")
    return v
```

Apply to both request models (create and update).

## Info

### IN-01: LIKE wildcards in schedule search are not escaped

**File:** `app/pages/schedules.py:340-345` (`_apply_filters`)
**Issue:** `pattern = f"%{search}%"` — a user searching `%` or `_` gets
wildcard matching instead of literal matching; searching `%` matches every ad
title. Not an injection (parameterized), only filter accuracy.
**Fix:** escape before interpolating:
`pattern = "%" + search.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_") + "%"`
with `.ilike(pattern, escape="\\")`.

### IN-02: `?sched=abc` on the editor page returns raw 422 JSON

**File:** `app/pages/ads.py:507` (`sched: int | None = Query(None)`)
**Issue:** The phase's own doctrine (T-02-35, and the `sched_error` whitelist
in the same handler) is that query-string values arriving from links and
bookmarks must not break the page. A non-numeric `sched` value in a shared or
corrupted link yields FastAPI's JSON 422 instead of the editor page. Same
handler treats `sched_error` defensively but `sched` strictly.
**Fix:** accept `str | None` and parse with a `try/int/except ValueError:
None`, mirroring the `ad_id` treatment in `ads_create`.

### IN-03: Explicit Save behaves differently with and without JavaScript

**File:** `app/pages/ads.py:387-401` (`_save_from_editor` response branch),
`app/templates/ads/form.html:230`
**Issue:** The no-JS path redirects to `/ads` after explicit Save («завершает
работу и возвращает в список»); the htmx path returns the autosave fragment and
the user stays in the editor. Both are correct code-wise (one code path, two
response forms), but the user-visible outcome of the same click diverges
between base and enhanced paths — the exact divergence the D-09 comments warn
about. If staying in the editor is the intended enhanced behavior, document it;
otherwise send `HX-Redirect: /ads` on the explicit-save htmx branch.

### IN-04: Storage upload failure is swallowed without logging

**File:** `app/routes/uploads.py:162-166`
**Issue:** `except Exception: raise HTTPException(502, ...)` discards the
original S3 error entirely — no log record, no `from exc`. Diagnosing storage
misconfiguration in production requires guesswork. The project logs via
structlog everywhere else (`app/main.py` handlers).
**Fix:** `logger.error("image_upload_failed", exc_info=True)` before raising,
and `raise HTTPException(...) from exc`.

### IN-05: Warn-threshold ratio duplicated as a template literal

**File:** `app/templates/ads/form.html:263` vs `app/pages/ads.py:31`
**Issue:** `TEXT_WARN_AT = {{ (editor.text_limit * 0.9) | round | int | tojson }}`
re-derives the threshold with a literal `0.9` while Python owns
`TEXT_WARN_RATIO = 0.9`. Changing the Python constant silently diverges the
client-side counter from the server-rendered class — the exact "second source"
drift the file's own comments prohibit.
**Fix:** add a `text_warn_plain` key (int(TEXT_LIMIT * TEXT_WARN_RATIO)) to
`_editor_context` and inject it instead of recomputing in the template.

### IN-06: Group count in schedule card summary is not declined

**File:** `app/templates/ads/includes/sched_card.html:78`
**Issue:** `chosen | length ~ ' групп'` renders «1 групп», «2 групп», «3
групп». The same file carefully declines the schedules counter
(`sched_count_label`) because «1 расписаний» is called a visible copywriting
defect (UI-SPEC); the group count in the card header and the delete-confirm
body has the identical defect.
**Fix:** add a `group_count_label(n)` macro with the same 1/2-4/5+ rule, or
reuse the declension pattern from `sched_count_label`.

### IN-07: `next_run_at.astimezone(tz)` misinterprets naive datetimes

**File:** `app/pages/schedules.py:379-380` (`_build_schedule_items`)
**Issue:** `sched.next_run_at.astimezone(tz)` on a naive datetime (SQLite dev
environment; `DateTime(timezone=True)` does not round-trip tzinfo there)
interprets the value as **system-local** time, while the project convention one
step later (`format_datetime_for_user`, `app/pages/common.py:157-159`) is
"naive means UTC". Correct on Postgres (aware values), wrong offsets possible
on SQLite. Also the conversion is redundant: `format_datetime_for_user`
converts to the user timezone itself.
**Fix:** mirror the convention before converting:
`value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value`
— or pass the raw `next_run_at` and let `format_datetime_for_user` do all the
work.

---

_Reviewed: 2026-08-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

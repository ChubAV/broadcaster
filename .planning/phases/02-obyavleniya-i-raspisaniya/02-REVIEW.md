---
phase: 02-obyavleniya-i-raspisaniya
reviewed: 2026-08-11T09:05:00Z
depth: standard
files_reviewed: 50
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
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_ads.py
  - tests/test_routes/test_schedules.py
  - tests/test_routes/test_schedules_api_ownership.py
  - tests/test_routes/test_schedules_profile_timezone.py
  - tests/test_routes/test_schedules_toggle_detached.py
  - tests/test_routes/test_uploads.py
  - tests/test_templates/test_components.py
findings:
  critical: 2
  warning: 7
  info: 7
  total: 16
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-08-11T09:05:00Z
**Depth:** standard
**Files Reviewed:** 50
**Status:** issues_found

## Summary

**Prior findings are genuinely closed.** All eight warnings of the earlier review were
re-verified against the current source and none is carried forward:

- **WR-01** — `app/services/image_keys.py:33,66,70` uses an unanchored pattern with
  `fullmatch` and compares the prefix **as a string**. Trailing-newline and `007/…` keys
  are refused on all four `Ad.images` entrances; a grep for writes to `.images` finds
  exactly `app/routes/ads.py:62,107` and `app/pages/ads.py:361,368`, and all four route
  through `own_image_keys`.
- **WR-02** — `app/routes/uploads.py:108-125` reads in 64 KiB chunks and aborts on the
  first chunk crossing the limit; `tests/test_routes/test_uploads.py:449-483` measures the
  read volume rather than the status code.
- **WR-03** — both `.strip()` sites now type-check first (`app/pages/ads.py:312,325`,
  `app/pages/schedules.py:163`); the `images` file part is a 400, not a 500.
- **WR-04** — the rule lives in a neutral module; `app/routes/ads.py` no longer imports
  from `app/pages/`.
- **WR-05** — one `is_schedule_complete` serves both toggles.
- **WR-06** — `app/routes/schedules.py:178-193` mirrors the page rule.
- **WR-07** — `_ownership_verdict` + `sched_error` return the user to their editor.
- **WR-08** — `ad_status: str | None = Form(None, alias="status")`.
- **IN-06** — the vacuous autosave test is gone; the replacement takes the next address
  from the server's own response (`tests/test_pages/test_ads_editor.py:396-436`).

**CR-01 and CR-02 are closed at the entrances they named — and both left a live residual.**
CR-01's server-side routing is correct, but `hx-sync="this:replace"` on the same form
throws away the very response that carries the new id, so the create path can still emit a
second `ads` row (CR-04). CR-02's group-ownership check is present on create and update,
but nothing re-checks ownership downstream and nothing remediates rows written before the
fix (WR-12).

Two blockers are new and both are reproduced, not inferred. A throwaway probe against the
real app (removed afterwards) produced:

```
PROBE put-null-group_ids:  500      # and the row is now permanently unreadable:
PROBE list-after-null:     500      # GET /api/schedules 500s for this user forever
PROBE malformed-time-create: 500    # POST /api/schedules times_of_day=["nope"]
PROBE empty-create: 201 {'is_active': True, 'next_run_at': None, 'group_ids': []}
```

Targeted run of the phase suite (`test_ads_editor`, `test_schedules_api_ownership`,
`test_uploads`, `test_ads_image_ownership`): **104 passed, 2 warnings**. Green tests are not
evidence here — every finding below sits on an input no test in the suite sends.

## Structural Findings (fallow)

No structural pre-pass was supplied with this review; no `<structural_findings>` block was
present in the prompt. All findings below are narrative.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-03: `PUT /api/schedules/{id}` writes JSON `null` into a list column and permanently breaks the caller's schedule listing

**File:** `app/routes/schedules.py:154-171` (`update_schedule`)
**Severity:** BLOCKER

**Issue:**
Every field of `UpdateScheduleRequest` is `T | None = None`, and the handler assigns
whatever `model_dump(exclude_unset=True)` yields:

```python
update_data = data.model_dump(exclude_unset=True)
...
for field, value in update_data.items():
    setattr(schedule, field, value)
```

`exclude_unset` distinguishes *absent* from *present*, but not *present and null*. A body of
`{"group_ids": null}` is "set", so `schedule.group_ids = None`. SQLAlchemy's `JSON` type has
`none_as_null=False`, so the value is stored as the JSON document `null` — no
`NOT NULL` violation, the commit **succeeds** — and reads back as `None`.

The ownership guard added by this plan does not stop it: `requested = update_data["group_ids"] or []`
turns `None` into `[]`, `owned_group_ids` returns `set()`, and `set([]) - set()` is empty, so
the check passes. The completeness block is equally forgiving (`schedule.group_ids or []`).
The failure surfaces only at response serialization, *after* the write is durable:

```
fastapi.exceptions.ResponseValidationError: 1 validation error:
  {'type': 'list_type', 'loc': ('response', 'group_ids'), 'msg': 'Input should be a valid list', 'input': None}
```

Consequence (both steps observed):
1. `PUT /api/schedules/{id}` `{"group_ids": null}` → **500**, row committed with `null`.
2. `GET /api/schedules` → **500 for every subsequent call**, because `ScheduleResponse.group_ids: list`
   rejects the stored `None` for that one row and the whole collection response fails. The
   caller's JSON schedule list is dead until someone repairs the row.

`days_of_week` and `times_of_day` behave identically. `{"timezone": null}` takes the other
branch — `String(50)` is a real `NOT NULL`, so it raises `IntegrityError` at commit and
returns 500 as well.

No test in the suite sends an explicit null; `tests/test_routes/test_schedules_api_ownership.py`
only ever omits keys.

**Fix:** reject nulls at the schema — the shape of a list field is exactly what the schema
exists to pin — and stop blind `setattr`:

```python
from pydantic import Field, field_validator

class UpdateScheduleRequest(BaseModel):
    group_ids: list[int] | None = None
    ...

    @field_validator("group_ids", "days_of_week", "times_of_day", "timezone")
    @classmethod
    def reject_explicit_null(cls, v, info):
        # Отсутствие ключа означает «не трогать» и до валидатора не доходит
        # (exclude_unset). Явный null — это ПРИСЛАННОЕ значение, и оно не
        # является ни списком, ни строкой: записанный, он ломает чтение записи
        # навсегда.
        if v is None:
            raise ValueError(f"{info.field_name} must not be null")
        return v
```

Add a regression test per field asserting 422 and an unchanged row, plus one asserting that
`GET /api/schedules` still answers 200 afterwards.

---

### CR-04: `hx-sync="this:replace"` discards the response that carries the new `ad_id`, so the create path can still produce a second draft

**File:** `app/templates/ads/form.html:52-58`, `app/pages/ads.py:427-460`
**Severity:** BLOCKER

**Issue:**
02-08 moved the create-vs-update decision to the server, and the decision's only input is the
hidden `ad_id` that arrives **out of band on the response to the create request**
(`autosave_response.html:34`). The same form also carries:

```html
hx-trigger="submit, keyup changed delay:2s, change delay:2s"
hx-sync="this:replace"
hx-swap="none"
```

htmx's default for an element with a request already in flight is `queue:last` — the new
event waits, and by the time it is issued the OOB swap has already filled `#ad-id-field`.
`hx-sync="this:replace"` overrides that default with an abort. In the bundled bundle
(`app/static/js/htmx.min.js`):

```js
if (m === "replace") { ce(g, "htmx:abort") } else if (m.indexOf("queue") === 0) { ... }
...
if (f.xhr) { if (f.abortable) { ce(g, "htmx:abort") } else { /* queuedRequests, p === "last" */ } }
```

The abort is client-side only. The first `POST /ads/new` has already reached the server and
`_save_from_editor` commits the `Ad` regardless; the response — and with it both
`HX-Push-Url` and the OOB `ad_id` — is thrown away. The replacement request is serialized
from the live form, whose hidden field is **still empty**, so `ads_create` takes the create
branch again (`app/pages/ads.py:457`) and inserts a **second** row.

Reachable without an attacker and without a slow network: `submit` carries no delay, so
finishing the sentence and clicking «Сохранить» inside the round-trip window of the pending
autosave is enough. The result is two ads — an orphan draft holding the earlier text, and a
second row that gets `status=published` — which is the same user-visible damage CR-01
described, only narrowed to a race window.

`tests/test_pages/test_ads_editor.py:973` actively locks the cause in place:
`assert 'hx-sync="this:replace"' in html, "отмена устаревшего запроса потеряна"`. The test
issues its two requests strictly sequentially, so it can never observe the overlap.

**Fix:** stop aborting on the one path where the response is load-bearing. Either drop the
attribute (htmx's own default already queues), or make the queueing explicit:

```html
<!-- app/templates/ads/form.html -->
{# Отмена запроса на пути СОЗДАНИЯ недопустима: ответ несёт идентификатор
   созданной записи внеполосно, и отброшенный ответ оставляет форму с пустым
   ad_id — следующее автосохранение создаёт ВТОРУЮ строку (CR-04).
   Очередь сохраняет исходный смысл (лишний промежуточный запрос не летит),
   не теряя ответ. #}
hx-sync="this:queue last"
```

and add a test that issues the second request **without** the id the first response
returned (i.e. simulating the discarded response) and asserts `_ads_count(...) == 1` —
today that test fails.

---

## Warnings

### WR-09: `times_of_day` is validated on the page entrance and not on the JSON entrance — 500 on arbitrary input

**File:** `app/routes/schedules.py:19-24, 111-115, 186-191`
**Issue:** `CreateScheduleRequest.times_of_day: list[str]` has no validator, and
`compute_next_run_at` parses without guarding (`app/services/schedule_service.py:26-28`:
`time(int(parts[0]), int(parts[1]))`). Observed:
`POST /api/schedules {"times_of_day": ["nope"]}` → **500**, `["99:99"]` → **500**
(`ValueError: hour must be in 0..23`). The page layer refuses exactly this class with
`_TIME_RE` and has four regression tests for it
(`tests/test_pages/test_editor_schedules.py:534,574,608,637`); the JSON layer has none.
This is the same "rule present on one entrance, absent on the other" shape that
`app/services/schedule_rules.py` was created to end — the module unified completeness and
group ownership and left time format behind.
**Fix:** move the format rule next to the other two and use it from both entrances:

```python
# app/services/schedule_rules.py
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

def is_valid_time(value: str) -> bool:
    return isinstance(value, str) and _TIME_RE.match(value) is not None
```

```python
# app/routes/schedules.py — на обеих схемах
@field_validator("times_of_day")
@classmethod
def validate_times(cls, v):
    if v is not None and not all(is_valid_time(t) for t in v):
        raise ValueError("times_of_day must be HH:MM")
    return v
```

`app/pages/schedules.py::_clean_times` then filters through the same predicate.

### WR-10: `POST /api/schedules` creates an ACTIVE schedule with nothing filled in — D-08 is enforced on three handlers out of four

**File:** `app/routes/schedules.py:117-127`
**Issue:** `Schedule.is_active` defaults to `True` (`app/models/schedule.py:30`) and
`create_schedule` never consults `is_schedule_complete`. Observed:
`POST /api/schedules {"ad_id":…, "account_id":…}` → `201 {'is_active': True, 'next_run_at': None, 'group_ids': []}`.
The page create path does the opposite two files over — `is_active=complete`
(`app/pages/schedules.py:593,609`) — and both toggles and `update_schedule` now refuse this
state. The row renders `Активно` **and** `Не заполнено` at the same time
(`app/templates/schedules/includes/schedule_row.html:99-101`), which is precisely the
impossible state WR-05 was raised about; the plan closed the toggle entrance and left the
create entrance open.
**Fix:**

```python
complete = is_schedule_complete(
    data.account_id, data.group_ids, data.days_of_week, data.times_of_day
)
schedule = await schedule_repo.create(
    ...,
    is_active=complete,
    next_run_at=next_run if complete else None,
)
```

### WR-11: the completeness rule has two more copies, in the templates the shared module's docstring claims already use it

**File:** `app/templates/ads/includes/sched_card.html:71`,
`app/templates/schedules/includes/schedule_row.html:47`, docstring at
`app/services/schedule_rules.py:25-31`
**Issue:** `is_schedule_complete` documents itself as
"Одно определение на все обработчики обоих входов **и на разметку карточки**
(app/templates/ads/includes/sched_card.html)". The markup does not call it — both templates
re-derive the predicate inline:

```jinja
{%- set complete = s.account_id and chosen and s.days_of_week and s.times_of_day -%}
{%- set complete = s.account_id and s.group_ids and s.days_of_week and s.times_of_day -%}
```

So the rule exists in three places, and the module that was introduced to guarantee one
asserts a fourth-party dependency that does not exist. The next change to the predicate
(e.g. requiring a *published* ad) silently moves the server and leaves both badges behind —
the exact drift D-08 forbids.
**Fix:** expose the predicate as a template global next to `AD_STATUS_*`
(`app/pages/common.py:99-100`) and call it from both templates:

```python
templates.env.globals["is_schedule_complete"] = is_schedule_complete
```

```jinja
{%- set complete = is_schedule_complete(s.account_id, s.group_ids or [], s.days_of_week or [], s.times_of_day or []) -%}
```

If a global is unwanted, at minimum correct the docstring so it stops claiming a property
the code does not have.

### WR-12: CR-02 was closed at the entrances only — pre-existing foreign `group_ids` stay live and the dispatcher still resolves groups by primary key alone

**File:** `app/application/scheduling/use_cases.py:120-144, 172-176`; no data migration in `alembic/versions/`
**Issue:** The fix stops new foreign ids from being written. It does nothing about ids
already stored — `POST /api/schedules` accepted `group_ids` verbatim for the whole life of
the endpoint before this plan — and adds no defence downstream:

```python
group = await session.get(Group, group_id)          # :173 — по первичному ключу, без владельца
...
group_name=group.name, group_id=group_id,           # :283-284 — в SendLog с user_id АТАКУЮЩЕГО
```

`collect_due_schedules` iterates `schedule.group_ids` as given and `send_message_once`
never compares `group.user_id` with `ad.user_id`, so any row written before the fix still
delivers to a foreign `group_external_id` and still writes the victim's group name into the
attacker's history. An entrance check with no remediation and no second line of defence is
half a fix.
**Fix:** two steps.
1. A data revision that nulls out non-owned ids:
   ```sql
   -- для каждой строки schedules оставить только те group_ids,
   -- у которых groups.user_id = ads.user_id И groups.account_id = schedules.account_id
   ```
   (or a one-off script in `scripts/`, in the style of `cleanup_schedules`).
2. Defence in depth in the domain, where the cost is one comparison:
   ```python
   if group.user_id != ad.user_id or (group.account_id and group.account_id != account.id):
       # Тот же исход, что и у остальных отказов по данным: строка журнала, не отправка.
       ... status="fail", error_message=f"Group {group_id} does not belong to the ad owner"
       return
   ```

### WR-13: nothing bounds `Ad.title`, whose column is `String(255)` — on PostgreSQL every autosave of a long title is a 500 the user sees only as «Не сохранено»

**File:** `app/models/ad.py:17`, `app/pages/ads.py:434,551`, `app/routes/ads.py:22,28`
**Issue:** `title: Mapped[str] = mapped_column(String(255))`, while every entrance accepts an
unbounded string: `title: str = Form("")` on both page handlers, `title: str` on both JSON
schemas. The editor deliberately has no `maxlength` and its counter measures `text` only
(`app/templates/ads/form.html:80-82`). A 256-character title — one paste — raises
`DataError: value too long for type character varying(255)` on PostgreSQL, which
`app/main.py:110-121` converts to 500. On the htmx path the form is never re-rendered
(`hx-swap="none"`), so the user gets the generic indicator and keeps typing into a document
that will never save again. The test suite cannot catch this: SQLite does not enforce
`VARCHAR` length, so `tests/` are green on exactly the input that fails in production.
**Fix:** validate at the boundary against the column, in one place, and surface it the way
attachment refusals are surfaced:

```python
# app/pages/ads.py
TITLE_LIMIT = 255  # ровно длина колонки Ad.title

if len(title) > TITLE_LIMIT:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Название длиннее {TITLE_LIMIT} символов. Сократите его и сохраните снова.",
    )
```
(raised inside the same `try` as `own_image_keys`, so the htmx path answers in the indicator),
plus `title: str = Field(max_length=255)` on `CreateAdRequest` / `UpdateAdRequest`.

### WR-14: the "ad is inaccessible" branch blanks the hidden id, so the next debounce silently creates a duplicate ad

**File:** `app/pages/ads.py:480-489`, `app/templates/ads/includes/autosave_response.html:34`
**Issue:** When the submitted `ad_id` resolves to nothing, the handler answers with
`ad=None`, whose OOB swap sets `#ad-id-field` back to empty. The comment argues this is safe
because "Записи при этом не создаётся" — true of *that* request only. Two seconds later the
same editor autosaves again, now with an empty id, and `ads_create` takes the create branch:
a second `Ad` appears carrying the same content. The reachable non-hostile case is a draft
deleted in another tab (or by `POST /ads/{id}/delete` in this one), after which the message
says «Обновите страницу» while the page quietly recreates the record instead. The same swap
also renders preview and summary from `ad=None`, wiping the visible state of an ad that may
still exist.
**Fix:** distinguish "not yours" from "gone", or make the reset terminal: keep the id field
untouched and stop the trigger, e.g. return the error fragment plus
`HX-Trigger: {"autosave-halted": true}` and have the small script remove the autosave
trigger, so recovery is an explicit page reload rather than a silent second row.

### WR-15: a detached schedule can no longer have its groups updated through the JSON API — the new check answers 404 for the caller's own groups

**File:** `app/services/schedule_rules.py:52-53`, `app/routes/schedules.py:161-168`
**Issue:** `owned_group_ids` returns `set()` whenever `account_id is None`, and
`update_schedule` compares against the **stored** `account_id`. For a schedule detached by
`detach_schedules_from_account` (`app/application/accounts/use_cases.py:87-93`, a documented
legitimate state, issue #35), any `PUT` carrying `group_ids` therefore fails with
`404 "Group not found"` — including ids the caller demonstrably owns. Since
`UpdateScheduleRequest` has no `account_id`, the JSON API also offers no way to re-attach an
account, so a detached schedule is unrepairable through the API and the error message names
the wrong object.
**Fix:** answer the actual condition, and keep the message truthful:

```python
if "group_ids" in update_data and requested and schedule.account_id is None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Schedule has no account: attach one in the ad editor before choosing groups",
    )
```
(and consider admitting `account_id` to `UpdateScheduleRequest`, guarded by the same
ownership query `create_schedule` already runs).

---

## Info

### IN-01 (still open): dead query parameter accepted on two routes

**File:** `app/pages/ads.py:92`, `app/pages/schedules.py:397`
**Issue:** `layout: str | None = Query(None)` is parsed and never read; the comment explains
the compatibility reason but records no removal point.
**Fix:** add a milestone/date marker so it is deleted deliberately.

### IN-02 (still open): deprecated `TemplateResponse` call style, inconsistently within the same modules

**File:** `app/pages/ads.py:106,134`, `app/pages/schedules.py:421,475`, `app/pages/dashboard.py:98`
**Issue:** These five call sites still use the legacy
`TemplateResponse(name, {"request": request, ...})` signature while `ads_new`, `ads_edit` and
`_autosave_response` in the same files use the modern form. The targeted suite run for this
review still emits
`Replace TemplateResponse(name, {"request": request}) by TemplateResponse(request, name)`.
**Fix:** convert the five remaining call sites.

### IN-03 (still open): warning threshold duplicated in the template

**File:** `app/templates/ads/form.html:254`
**Issue:** `const TEXT_WARN_AT = {{ (editor.text_limit * 0.9) | round | int | tojson }};`
re-derives the ratio `app/pages/ads.py:31` owns as `TEXT_WARN_RATIO`, while the
server-rendered counter reads `editor.text_warn_at`.
**Fix:** expose the plain-text threshold in `_editor_context` and render it.

### IN-04 (still open): `_build_schedule_items` recomputes the timezone its callers already resolved

**File:** `app/pages/schedules.py:370`, callers `:404-405, 446-447`
**Issue:** Three copies of `user.timezone if ... in VALID_TIMEZONES else "UTC"` in one module.
**Fix:** pass `tz_name` alongside `tz`, or return both from one helper.

### IN-05 (still open): non-mapped attributes attached to ORM instances, then defaulted twice

**File:** `app/pages/ads.py:78-80`, `app/templates/ads/includes/ad_card.html:39-40`
**Issue:** `_enrich_ads_with_stats` sets `sends_count`/`schedules_count` on `Ad` instances
the model does not declare, coalescing with `or 0`; the template coalesces again. A caller
that forgets the enrichment gets an `AttributeError` inside the template.
**Fix:** return a `{ad_id: (sends, schedules)}` mapping, or declare the counters on the model.

### IN-08 (new): page size hardcoded in the two infinite-scroll sentinels

**File:** `app/templates/schedules/list.html:61`, `app/templates/schedules/partial_cards.html:7`
**Issue:** `&limit=30` is written out in both sentinels while `PAGE_SIZE = 30` lives in
`app/pages/schedules.py:26` (and again in `app/pages/ads.py:21`). The two templates are
required to stay byte-identical to each other, which is enforced by comment only; the number
is a third copy that no comment mentions.
**Fix:** pass `page_size` in the context of both handlers and render
`&limit={{ page_size }}`.

### IN-09 (new): a test pins the attribute that causes CR-04

**File:** `tests/test_pages/test_ads_editor.py:973`
**Issue:** `assert 'hx-sync="this:replace"' in html, "отмена устаревшего запроса потеряна"`
turns the abort strategy into a contract, so the CR-04 fix will read as a regression to
whoever runs the suite next.
**Fix:** covered by CR-04 — assert the *queueing* contract instead
(`'hx-sync="this:queue last"' in html`, or drop the assertion and test the behaviour: two
overlapping creates must leave one row).

---

_Reviewed: 2026-08-11T09:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
</content>
</invoke>

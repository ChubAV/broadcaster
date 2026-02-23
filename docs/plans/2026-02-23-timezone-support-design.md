# Timezone Support for Schedules

## Problem

Users mostly work in Moscow time (UTC+3) but the service operates in UTC.
They have to manually subtract 3 hours when setting schedule times.

## Decision

Add a `timezone` column to the `Schedule` model. Each schedule stores its own
timezone. The worker and routes use `schedule.timezone` instead of hardcoded
`"UTC"` when calling `compute_next_run_at()`.

## Design

### Model

`Schedule.timezone: Mapped[str]` with `server_default="UTC"`.
Existing schedules keep UTC (no breakage). New schedules default to
`Europe/Moscow` in the UI form.

### Timezone list

Short list of Russian zones plus UTC:

| IANA name              | Label              |
|------------------------|--------------------|
| Europe/Kaliningrad     | Калининград UTC+2  |
| Europe/Moscow          | Москва UTC+3       |
| Europe/Samara          | Самара UTC+4       |
| Asia/Yekaterinburg     | Екатеринбург UTC+5 |
| Asia/Novosibirsk       | Новосибирск UTC+6  |
| Asia/Krasnoyarsk       | Красноярск UTC+7   |
| Asia/Irkutsk           | Иркутск UTC+8      |
| Asia/Vladivostok       | Владивосток UTC+10  |
| Asia/Kamchatka         | Камчатка UTC+12    |
| UTC                    | UTC                |

### Changes

1. **Alembic migration**: add `timezone VARCHAR NOT NULL DEFAULT 'UTC'` to
   `schedules` table.
2. **Schedule model** (`app/models/schedule.py`): add `timezone` field.
3. **Routes** (`app/routes/schedules.py`): pass `schedule.timezone` to
   `compute_next_run_at()` instead of `"UTC"`.
4. **Pages** (`app/pages/schedules.py`): same; also pass timezone list to
   templates.
5. **Worker** (`app/worker/tasks.py`): use `schedule.timezone` when
   recomputing `next_run_at`.
6. **Form template** (`templates/schedules/form.html`): add `<select
   name="timezone">` dropdown, default `Europe/Moscow` for new schedules.
7. **List template** (`templates/schedules/list.html`): convert `next_run_at`
   from UTC to `schedule.timezone` for display, show zone abbreviation.

### Migration strategy

- `server_default="UTC"` ensures existing rows are safe.
- No data migration needed for `times_of_day` — existing values were entered
  as UTC and will continue to be interpreted as UTC.
- New schedules get `Europe/Moscow` pre-selected in the form.
- Users can edit old schedules to change timezone (and adjust times) at their
  convenience.

### Testing

- Update `test_schedule_service.py` with timezone-aware tests.
- Update `test_tasks.py` to verify worker uses `schedule.timezone`.
- Update schedule route/page tests to verify timezone is saved and passed.

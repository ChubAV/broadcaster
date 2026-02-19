from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def compute_next_run_at(
    days_of_week: list[int],   # 0=Mon, 6=Sun
    times_of_day: list[str],   # ["09:00", "18:00"]
    tz_name: str,              # user timezone, e.g. "UTC"
    now: datetime | None = None,
) -> datetime | None:
    """Compute the next scheduled run time.

    Returns the nearest future datetime matching any (day, time) combination.
    Returns None if days_of_week or times_of_day is empty.
    """
    if not days_of_week or not times_of_day:
        return None

    tz = ZoneInfo(tz_name)
    if now is None:
        now = datetime.now(tz)
    else:
        now = now.astimezone(tz)

    parsed_times = []
    for t_str in times_of_day:
        parts = t_str.split(":")
        parsed_times.append(time(int(parts[0]), int(parts[1])))

    candidates = []
    for day_offset in range(8):  # look ahead up to 7 days (0..7)
        candidate_date = (now + timedelta(days=day_offset)).date()
        weekday = candidate_date.weekday()  # 0=Mon, 6=Sun
        if weekday not in days_of_week:
            continue
        for t in parsed_times:
            candidate_dt = datetime.combine(candidate_date, t, tzinfo=tz)
            if candidate_dt > now:
                candidates.append(candidate_dt)

    if not candidates:
        return None

    # Return the earliest candidate, converted to UTC
    earliest = min(candidates)
    return earliest.astimezone(timezone.utc)

from datetime import datetime, timezone

from app.services.schedule_service import compute_next_run_at


def test_next_run_today_later():
    """Next run is today at a later time."""
    # It's Monday 10:00 UTC, schedule for Mon at 14:00
    now = datetime(2026, 2, 16, 10, 0, tzinfo=timezone.utc)  # Monday
    result = compute_next_run_at(
        days_of_week=[0],  # Monday
        times_of_day=["14:00"],
        tz_name="UTC",
        now=now,
    )
    assert result is not None
    assert result == datetime(2026, 2, 16, 14, 0, tzinfo=timezone.utc)


def test_next_run_tomorrow():
    """Today's times have passed, next run is tomorrow."""
    # It's Monday 20:00 UTC, schedule for Mon/Tue at 09:00
    now = datetime(2026, 2, 16, 20, 0, tzinfo=timezone.utc)  # Monday
    result = compute_next_run_at(
        days_of_week=[0, 1],  # Mon, Tue
        times_of_day=["09:00"],
        tz_name="UTC",
        now=now,
    )
    assert result is not None
    # Should be Tuesday 09:00
    assert result == datetime(2026, 2, 17, 9, 0, tzinfo=timezone.utc)


def test_next_run_next_week():
    """Only one day scheduled and it just passed."""
    # It's Monday 20:00 UTC, schedule for Mon at 09:00 only
    now = datetime(2026, 2, 16, 20, 0, tzinfo=timezone.utc)  # Monday
    result = compute_next_run_at(
        days_of_week=[0],  # Monday only
        times_of_day=["09:00"],
        tz_name="UTC",
        now=now,
    )
    assert result is not None
    # Should be next Monday 09:00
    assert result == datetime(2026, 2, 23, 9, 0, tzinfo=timezone.utc)


def test_empty_days_returns_none():
    """Empty days_of_week returns None."""
    now = datetime(2026, 2, 16, 10, 0, tzinfo=timezone.utc)
    result = compute_next_run_at(
        days_of_week=[],
        times_of_day=["09:00"],
        tz_name="UTC",
        now=now,
    )
    assert result is None


def test_empty_times_returns_none():
    """Empty times_of_day returns None."""
    now = datetime(2026, 2, 16, 10, 0, tzinfo=timezone.utc)
    result = compute_next_run_at(
        days_of_week=[0],
        times_of_day=[],
        tz_name="UTC",
        now=now,
    )
    assert result is None


def test_multiple_times_same_day_picks_earliest_future():
    """Multiple times on the same day: picks earliest future one."""
    # It's Monday 10:30 UTC, schedule for Mon at 09:00, 11:00, 18:00
    now = datetime(2026, 2, 16, 10, 30, tzinfo=timezone.utc)  # Monday
    result = compute_next_run_at(
        days_of_week=[0],  # Monday
        times_of_day=["09:00", "11:00", "18:00"],
        tz_name="UTC",
        now=now,
    )
    assert result is not None
    # 09:00 is past, so earliest future is 11:00
    assert result == datetime(2026, 2, 16, 11, 0, tzinfo=timezone.utc)

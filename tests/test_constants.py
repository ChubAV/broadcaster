from app.constants import TIMEZONE_CHOICES


def test_timezone_choices_is_list_of_tuples():
    assert isinstance(TIMEZONE_CHOICES, list)
    assert len(TIMEZONE_CHOICES) >= 10
    for item in TIMEZONE_CHOICES:
        assert len(item) == 2  # (iana_name, label)


def test_timezone_choices_contains_moscow():
    iana_names = [tz[0] for tz in TIMEZONE_CHOICES]
    assert "Europe/Moscow" in iana_names


def test_timezone_choices_contains_utc():
    iana_names = [tz[0] for tz in TIMEZONE_CHOICES]
    assert "UTC" in iana_names


def test_all_timezone_names_are_valid():
    from zoneinfo import ZoneInfo
    for iana_name, _label in TIMEZONE_CHOICES:
        ZoneInfo(iana_name)  # raises if invalid

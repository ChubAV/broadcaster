from app.constants import (
    AD_STATUS_DRAFT,
    AD_STATUS_PUBLISHED,
    AD_STATUSES,
    TIMEZONE_CHOICES,
    VALID_TIMEZONES,
)


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


def test_valid_timezones_matches_choices():
    assert VALID_TIMEZONES == {tz[0] for tz in TIMEZONE_CHOICES}


def test_invalid_timezone_not_in_set():
    assert "Not/A/Timezone" not in VALID_TIMEZONES


# --- Состояние объявления (D-02) ----------------------------------------------
#
# app/constants.py — единственный источник этих значений: их читают модель,
# доменный подбор расписаний, схемы JSON-API и шаблон карточки. Литералы,
# выписанные в каждом из этих мест по отдельности, разъезжались бы молча —
# объявление не отфильтровалось бы ни как черновик, ни как опубликованное.


def test_ad_status_literals():
    assert AD_STATUS_DRAFT == "draft"
    assert AD_STATUS_PUBLISHED == "published"


def test_ad_statuses_contains_exactly_both():
    assert AD_STATUSES == {AD_STATUS_DRAFT, AD_STATUS_PUBLISHED}


def test_ad_statuses_fit_column_width():
    """Колонка объявлена как String(20) — значения обязаны в неё помещаться."""
    for value in AD_STATUSES:
        assert len(value) <= 20


def test_unknown_ad_status_not_in_set():
    assert "activated" not in AD_STATUSES

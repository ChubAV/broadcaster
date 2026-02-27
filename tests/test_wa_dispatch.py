from dataclasses import asdict

import pytest

from app.application.scheduling.use_cases import DispatchTask


def test_dispatch_task_wa_fields():
    """DispatchTask for WA should carry full payload data."""
    task = DispatchTask(
        type="wa",
        ad_id=1,
        group_id=2,
        account_id=3,
        schedule_id=4,
        user_id=5,
        ad_text="Hello",
        ad_title="Test Ad",
        ad_images=["https://example.com/img.jpg"],
        group_external_id="120363001234@g.us",
        group_name="Test Group",
    )
    d = asdict(task)
    assert d["type"] == "wa"
    assert d["ad_text"] == "Hello"
    assert d["group_external_id"] == "120363001234@g.us"
    assert d["ad_images"] == ["https://example.com/img.jpg"]


def test_dispatch_task_tg_defaults():
    """DispatchTask for TG should have None defaults for WA fields."""
    task = DispatchTask(
        type="tg_user",
        ad_id=1,
        group_id=2,
        account_id=3,
        schedule_id=4,
    )
    assert task.user_id is None
    assert task.ad_text is None
    assert task.group_external_id is None


def test_dispatch_task_slots():
    """DispatchTask uses slots for memory efficiency."""
    task = DispatchTask(type="wa", ad_id=1, group_id=2, account_id=3, schedule_id=4)
    with pytest.raises(AttributeError):
        task.nonexistent_field = "test"

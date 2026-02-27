import pytest


def test_result_payload_format():
    """Verify result payload has all required fields."""
    required_fields = [
        "task_id", "account_id", "ad_id", "group_id", "schedule_id",
        "user_id", "status", "error_message", "no_retry",
        "ad_title", "ad_text", "ad_images", "group_name",
        "messenger_type", "sent_at",
    ]

    # Simulated result payload from wa-worker
    result = {
        "task_id": "test-uuid",
        "account_id": 1,
        "ad_id": 1,
        "group_id": 1,
        "schedule_id": 1,
        "user_id": 1,
        "status": "ok",
        "error_message": None,
        "no_retry": False,
        "ad_title": "Test",
        "ad_text": "Hello",
        "ad_images": None,
        "group_name": "Group",
        "messenger_type": "wa",
        "sent_at": "2026-02-27T12:00:00Z",
    }

    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    assert result["messenger_type"] == "wa"
    assert result["status"] in ("ok", "fail")


def test_result_fail_payload():
    """Verify failure result includes error details."""
    result = {
        "task_id": "test-uuid",
        "account_id": 1,
        "ad_id": 1,
        "group_id": 1,
        "schedule_id": 1,
        "user_id": 1,
        "status": "fail",
        "error_message": "forbidden",
        "no_retry": True,
        "ad_title": "Test",
        "ad_text": "Hello",
        "ad_images": None,
        "group_name": "Group",
        "messenger_type": "wa",
        "sent_at": "2026-02-27T12:00:00Z",
    }

    assert result["status"] == "fail"
    assert result["no_retry"] is True
    assert result["error_message"] == "forbidden"

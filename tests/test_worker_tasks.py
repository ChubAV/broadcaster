import json
import pytest
from unittest.mock import MagicMock, patch, call

from app.application.scheduling.use_cases import DispatchTask
from app.worker.tasks import dispatch_send_tasks


@pytest.mark.asyncio
async def test_dispatch_wa_to_redis_queues():
    """WhatsApp tasks are dispatched to Redis per-account queues."""
    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe

    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://localhost:6379/0"

    with patch("app.worker.tasks.send_telegram_message", MagicMock()):
        with patch("app.worker.tasks.get_settings", return_value=mock_settings):
            with patch("redis.from_url", return_value=mock_redis):
                await dispatch_send_tasks(
                    tasks_to_dispatch=[
                        DispatchTask(type="wa", ad_id=1, group_id=10, account_id=5, schedule_id=1,
                                     user_id=100, ad_text="text1", ad_title="title1",
                                     group_external_id="ext10", group_name="group10"),
                        DispatchTask(type="wa", ad_id=2, group_id=20, account_id=5, schedule_id=2,
                                     user_id=100, ad_text="text2", ad_title="title2",
                                     group_external_id="ext20", group_name="group20"),
                        DispatchTask(type="wa", ad_id=3, group_id=30, account_id=7, schedule_id=3,
                                     user_id=101, ad_text="text3", ad_title="title3",
                                     group_external_id="ext30", group_name="group30"),
                    ],
                )

    # Should push to wa:queue:{account_id} keys
    rpush_calls = [c for c in mock_pipe.method_calls if c[0] == "rpush"]
    assert len(rpush_calls) == 3

    # Verify queue keys
    queue_keys = [c[1][0] for c in rpush_calls]
    assert queue_keys.count("wa:queue:5") == 2
    assert queue_keys.count("wa:queue:7") == 1

    # Verify payloads contain expected fields
    for c in rpush_calls:
        payload = json.loads(c[1][1])
        assert "task_id" in payload
        assert "ad_id" in payload
        assert "created_at" in payload

    # Active accounts set updated
    sadd_calls = [c for c in mock_pipe.method_calls if c[0] == "sadd"]
    assert len(sadd_calls) == 2  # once for account 5, once for account 7

    mock_pipe.execute.assert_called_once()
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_telegram_to_telegram_queue():
    """Telegram tasks are dispatched to the 'telegram' queue."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(kw.get("queue"))

    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://localhost:6379/0"

    with patch("app.worker.tasks.send_telegram_message", mock_task):
        with patch("app.worker.tasks.get_settings", return_value=mock_settings):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    DispatchTask(type="tg_user", ad_id=1, group_id=10, account_id=3, schedule_id=1),
                ],
            )

    assert dispatched == ["telegram"]


@pytest.mark.asyncio
async def test_dispatch_mixed_types():
    """Mixed messenger types: TG to Celery, WA to Redis."""
    tg_dispatched = []

    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: tg_dispatched.append(kw.get("queue"))

    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe

    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://localhost:6379/0"

    with patch("app.worker.tasks.send_telegram_message", mock_tg):
        with patch("app.worker.tasks.get_settings", return_value=mock_settings):
            with patch("redis.from_url", return_value=mock_redis):
                await dispatch_send_tasks(
                    tasks_to_dispatch=[
                        DispatchTask(type="wa", ad_id=1, group_id=10, account_id=5, schedule_id=1,
                                     user_id=100, ad_text="text1", ad_title="title1",
                                     group_external_id="ext10", group_name="group10"),
                        DispatchTask(type="tg_user", ad_id=2, group_id=20, account_id=3, schedule_id=2),
                        DispatchTask(type="wa", ad_id=3, group_id=30, account_id=5, schedule_id=3,
                                     user_id=100, ad_text="text3", ad_title="title3",
                                     group_external_id="ext30", group_name="group30"),
                    ],
                )

    # TG task goes to Celery
    assert tg_dispatched == ["telegram"]

    # WA tasks go to Redis
    rpush_calls = [c for c in mock_pipe.method_calls if c[0] == "rpush"]
    assert len(rpush_calls) == 2
    assert all(c[1][0] == "wa:queue:5" for c in rpush_calls)

    mock_pipe.execute.assert_called_once()

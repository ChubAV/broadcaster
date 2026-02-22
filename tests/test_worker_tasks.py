import pytest
from unittest.mock import MagicMock, patch, call

from app.worker.tasks import dispatch_send_tasks


@pytest.mark.asyncio
async def test_dispatch_wa_to_whatsapp_queue():
    """WhatsApp tasks are dispatched to the 'whatsapp' queue."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(kw.get("queue"))

    with patch("app.worker.tasks.send_whatsapp_message", mock_task):
        with patch("app.worker.tasks.send_telegram_message", MagicMock()):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    {"type": "wa", "ad_id": 1, "group_id": 10, "account_id": 5, "schedule_id": 1},
                    {"type": "wa", "ad_id": 2, "group_id": 20, "account_id": 5, "schedule_id": 2},
                    {"type": "wa", "ad_id": 3, "group_id": 30, "account_id": 7, "schedule_id": 3},
                ],
            )

    assert all(q == "whatsapp" for q in dispatched)
    assert len(dispatched) == 3


@pytest.mark.asyncio
async def test_dispatch_wa_grouped_by_session():
    """WA tasks for the same session are dispatched consecutively."""
    dispatched_args = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched_args.append(kw.get("args", a))

    with patch("app.worker.tasks.send_whatsapp_message", mock_task):
        with patch("app.worker.tasks.send_telegram_message", MagicMock()):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    {"type": "wa", "ad_id": 1, "group_id": 10, "account_id": 5, "schedule_id": 1},
                    {"type": "wa", "ad_id": 9, "group_id": 90, "account_id": 7, "schedule_id": 9},
                    {"type": "wa", "ad_id": 2, "group_id": 20, "account_id": 5, "schedule_id": 2},
                ],
            )

    # Session 5 tasks should be adjacent (grouped), session 7 separate
    account_ids = [args[2] for args in dispatched_args]
    # All tasks for session 5 appear before (or after) session 7
    first_5 = account_ids.index(5)
    last_5 = len(account_ids) - 1 - account_ids[::-1].index(5)
    # No other session's task between first and last of session 5
    for i in range(first_5, last_5 + 1):
        assert account_ids[i] == 5


@pytest.mark.asyncio
async def test_dispatch_telegram_to_telegram_queue():
    """Telegram tasks are dispatched to the 'telegram' queue."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(kw.get("queue"))

    with patch("app.worker.tasks.send_telegram_message", mock_task):
        with patch("app.worker.tasks.send_whatsapp_message", MagicMock()):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    {"type": "tg_user", "ad_id": 1, "group_id": 10, "account_id": 3, "schedule_id": 1},
                ],
            )

    assert dispatched == ["telegram"]


@pytest.mark.asyncio
async def test_dispatch_mixed_types():
    """Mixed messenger types go to correct queues."""
    wa_dispatched = []
    tg_dispatched = []

    mock_wa = MagicMock()
    mock_wa.apply_async = lambda *a, **kw: wa_dispatched.append(kw.get("queue"))
    mock_tg = MagicMock()
    mock_tg.apply_async = lambda *a, **kw: tg_dispatched.append(kw.get("queue"))

    with patch("app.worker.tasks.send_whatsapp_message", mock_wa):
        with patch("app.worker.tasks.send_telegram_message", mock_tg):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    {"type": "wa", "ad_id": 1, "group_id": 10, "account_id": 5, "schedule_id": 1},
                    {"type": "tg_user", "ad_id": 2, "group_id": 20, "account_id": 3, "schedule_id": 2},
                    {"type": "wa", "ad_id": 3, "group_id": 30, "account_id": 5, "schedule_id": 3},
                ],
            )

    assert len(wa_dispatched) == 2
    assert all(q == "whatsapp" for q in wa_dispatched)
    assert tg_dispatched == ["telegram"]

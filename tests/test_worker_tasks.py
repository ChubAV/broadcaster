import pytest
from unittest.mock import MagicMock, patch

from app.worker.tasks import dispatch_send_tasks


@pytest.mark.asyncio
async def test_dispatch_groups_wa_by_session():
    """WhatsApp tasks are dispatched to per-session queues."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(("wa", kw.get("queue")))

    with patch("app.worker.tasks.send_whatsapp_message", mock_task):
        with patch("app.worker.tasks.send_telegram_message", MagicMock()):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    {"type": "wa", "ad_id": 1, "group_id": 10, "account_id": 5, "schedule_id": 1},
                    {"type": "wa", "ad_id": 2, "group_id": 20, "account_id": 5, "schedule_id": 2},
                    {"type": "wa", "ad_id": 3, "group_id": 30, "account_id": 7, "schedule_id": 3},
                ],
            )

    queues = [q for _, q in dispatched]
    assert queues.count("whatsapp.session.5") == 2
    assert queues.count("whatsapp.session.7") == 1


@pytest.mark.asyncio
async def test_dispatch_telegram_to_telegram_queue():
    """Telegram tasks are dispatched to the 'telegram' queue."""
    dispatched = []

    mock_task = MagicMock()
    mock_task.apply_async = lambda *a, **kw: dispatched.append(("tg", kw.get("queue")))

    with patch("app.worker.tasks.send_telegram_message", mock_task):
        with patch("app.worker.tasks.send_whatsapp_message", MagicMock()):
            await dispatch_send_tasks(
                tasks_to_dispatch=[
                    {"type": "tg_user", "ad_id": 1, "group_id": 10, "account_id": 3, "schedule_id": 1},
                ],
            )

    assert dispatched == [("tg", "telegram")]


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
    assert all(q == "whatsapp.session.5" for q in wa_dispatched)
    assert tg_dispatched == ["telegram"]

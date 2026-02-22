import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.worker.wa_consumer import get_active_wa_queues, register_wa_queue, unregister_wa_queue


@pytest.mark.asyncio
async def test_get_active_wa_queues_returns_queue_list():
    """Returns list of active WA queue names from Redis."""
    mock_redis = AsyncMock()
    mock_redis.smembers = AsyncMock(return_value={
        b"whatsapp.session.5",
        b"whatsapp.session.10",
    })

    with patch("app.worker.wa_consumer._get_redis", return_value=mock_redis):
        queues = await get_active_wa_queues()

    assert set(queues) == {"whatsapp.session.5", "whatsapp.session.10"}


@pytest.mark.asyncio
async def test_get_active_wa_queues_returns_empty_on_no_redis():
    """Returns empty list when Redis is unavailable."""
    with patch("app.worker.wa_consumer._get_redis", return_value=None):
        queues = await get_active_wa_queues()
    assert queues == []


@pytest.mark.asyncio
async def test_register_wa_queue():
    """register_wa_queue adds queue name to Redis SET."""
    mock_redis = AsyncMock()
    mock_redis.sadd = AsyncMock()

    with patch("app.worker.wa_consumer._get_redis", return_value=mock_redis):
        await register_wa_queue("whatsapp.session.42")

    mock_redis.sadd.assert_called_once_with("wa:active_queues", "whatsapp.session.42")


@pytest.mark.asyncio
async def test_unregister_wa_queue():
    """unregister_wa_queue removes queue name from Redis SET."""
    mock_redis = AsyncMock()
    mock_redis.srem = AsyncMock()

    with patch("app.worker.wa_consumer._get_redis", return_value=mock_redis):
        await unregister_wa_queue("whatsapp.session.42")

    mock_redis.srem.assert_called_once_with("wa:active_queues", "whatsapp.session.42")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messengers.telegram_pool import TelegramPool


@pytest.mark.asyncio
async def test_pool_reuses_client():
    """Getting the same account_id twice returns the same client."""
    pool = TelegramPool()
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)

    with patch.object(pool, "_create_client", return_value=mock_client):
        client1 = await pool.get(
            account_id=1, session_string="s", api_id=1, api_hash="h"
        )
        client2 = await pool.get(
            account_id=1, session_string="s", api_id=1, api_hash="h"
        )

    assert client1 is client2


@pytest.mark.asyncio
async def test_pool_creates_different_clients_per_account():
    """Different account_ids get different clients."""
    pool = TelegramPool()
    mock_client1 = AsyncMock()
    mock_client1.is_connected = MagicMock(return_value=True)
    mock_client2 = AsyncMock()
    mock_client2.is_connected = MagicMock(return_value=True)

    with patch.object(
        pool, "_create_client", side_effect=[mock_client1, mock_client2]
    ):
        c1 = await pool.get(
            account_id=1, session_string="s1", api_id=1, api_hash="h"
        )
        c2 = await pool.get(
            account_id=2, session_string="s2", api_id=1, api_hash="h"
        )

    assert c1 is not c2


@pytest.mark.asyncio
async def test_pool_disconnect_all():
    """disconnect_all cleans up all clients."""
    pool = TelegramPool()
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    mock_client.disconnect = AsyncMock()

    with patch.object(pool, "_create_client", return_value=mock_client):
        await pool.get(account_id=1, session_string="s", api_id=1, api_hash="h")

    await pool.disconnect_all()
    mock_client.disconnect.assert_called_once()
    assert len(pool._clients) == 0


@pytest.mark.asyncio
async def test_pool_remove_single_client():
    """remove() disconnects and removes a single client."""
    pool = TelegramPool()
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    mock_client.disconnect = AsyncMock()

    with patch.object(pool, "_create_client", return_value=mock_client):
        await pool.get(account_id=1, session_string="s", api_id=1, api_hash="h")

    await pool.remove(1)
    mock_client.disconnect.assert_called_once()
    assert 1 not in pool._clients


@pytest.mark.asyncio
async def test_pool_reconnects_disconnected_client():
    """If stored client is disconnected, pool creates a new one."""
    pool = TelegramPool()
    old_client = AsyncMock()
    old_client.is_connected = MagicMock(return_value=False)
    old_client.disconnect = AsyncMock()

    new_client = AsyncMock()
    new_client.is_connected = MagicMock(return_value=True)

    # First call creates old_client, second call creates new_client
    with patch.object(
        pool, "_create_client", side_effect=[old_client, new_client]
    ):
        c1 = await pool.get(
            account_id=1, session_string="s", api_id=1, api_hash="h"
        )
        # old_client is now stored but reports disconnected
        c2 = await pool.get(
            account_id=1, session_string="s", api_id=1, api_hash="h"
        )

    assert c1 is old_client
    assert c2 is new_client
    # Old client should have been disconnected before replacement
    old_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_pool_remove_nonexistent_account():
    """remove() on a nonexistent account_id is a no-op."""
    pool = TelegramPool()
    # Should not raise
    await pool.remove(999)

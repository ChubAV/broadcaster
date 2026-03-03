import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.billing_cache import check_balance_cached


def _mock_settings():
    s = MagicMock()
    s.redis_url = "redis://localhost:6379/0"
    s.billing_cache_ttl = 60
    return s


@pytest.mark.asyncio
async def test_check_balance_cached_returns_result():
    """check_balance_cached returns (allowed, reason) like check_balance."""
    mock_db = AsyncMock()
    with patch("app.services.billing_cache.check_balance", return_value=(True, "")) as mock_check:
        with patch("app.services.billing_cache._get_redis", return_value=None):
            with patch("app.services.billing_cache.get_settings", return_value=_mock_settings()):
                result = await check_balance_cached(mock_db, user_id=1, action="send")
    assert result == (True, "")
    mock_check.assert_called_once_with(mock_db, 1)


@pytest.mark.asyncio
async def test_check_balance_cached_non_send_always_allows():
    """Non-send actions always return True."""
    mock_db = AsyncMock()
    result = await check_balance_cached(mock_db, user_id=1, action="create_ad")
    assert result == (True, "")


@pytest.mark.asyncio
async def test_check_balance_cached_uses_cache():
    """Second call uses cached result, not DB."""
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value='{"allowed": true, "reason": ""}')

    with patch("app.services.billing_cache._get_redis", return_value=mock_redis):
        with patch("app.services.billing_cache.get_settings", return_value=_mock_settings()):
            with patch("app.services.billing_cache.check_balance") as mock_check:
                result = await check_balance_cached(mock_db, user_id=1, action="send")
    assert result == (True, "")
    mock_check.assert_not_called()


@pytest.mark.asyncio
async def test_check_balance_cached_falls_back_on_redis_error():
    """Falls back to DB when Redis fails."""
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=Exception("Redis down"))

    with patch("app.services.billing_cache._get_redis", return_value=mock_redis):
        with patch("app.services.billing_cache.get_settings", return_value=_mock_settings()):
            with patch("app.services.billing_cache.check_balance", return_value=(False, "empty")) as mock_check:
                result = await check_balance_cached(mock_db, user_id=1, action="send")
    assert result == (False, "empty")
    mock_check.assert_called_once()

import json
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing_service import check_limit
from app.config import get_settings

logger = structlog.get_logger(__name__)

_redis_client = None


def _get_redis():
    """Lazy-init Redis client for billing cache."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio
            settings = get_settings()
            _redis_client = redis.asyncio.from_url(settings.redis_url)
        except Exception:
            logger.warning("billing_cache_redis_unavailable")
            return None
    return _redis_client


async def check_limit_cached(
    db: AsyncSession, user_id: int, action: str
) -> tuple[bool, str]:
    """check_limit with Redis cache. Falls back to DB on cache miss/error."""
    cache_key = f"billing:{user_id}:{action}"
    ttl = get_settings().billing_cache_ttl

    r = _get_redis()
    if r:
        try:
            cached = await r.get(cache_key)
            if cached:
                data = json.loads(cached)
                return data["allowed"], data["reason"]
        except Exception as e:
            logger.debug("billing_cache_read_error", cache_key=cache_key, error=str(e))

    allowed, reason = await check_limit(db, user_id, action)

    if r:
        try:
            await r.setex(
                cache_key,
                ttl,
                json.dumps({"allowed": allowed, "reason": reason}),
            )
        except Exception as e:
            logger.debug("billing_cache_write_error", cache_key=cache_key, error=str(e))

    return allowed, reason

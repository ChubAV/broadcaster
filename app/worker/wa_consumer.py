"""Dynamic queue discovery for WhatsApp session-affinity workers.

WhatsApp workers consume from dynamically-created queues
(whatsapp.session.{id}). This module handles registering/discovering those queues
in Redis.

The check_schedules task routes WA tasks to whatsapp.session.{id} queues.
Celery workers configured with task_create_missing_queues=True will
auto-create these queues when tasks are dispatched.
"""
import logging

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio
            from app.config import get_settings
            _redis_client = redis.asyncio.from_url(get_settings().redis_url)
        except Exception:
            return None
    return _redis_client


async def get_active_wa_queues() -> list[str]:
    """Get list of active WhatsApp session queues from Redis."""
    r = _get_redis()
    if not r:
        return []
    try:
        members = await r.smembers("wa:active_queues")
        return [m.decode() if isinstance(m, bytes) else m for m in members]
    except Exception as e:
        logger.warning("Failed to get active WA queues: %s", e)
        return []


async def register_wa_queue(queue_name: str) -> None:
    """Register a WhatsApp session queue as active."""
    r = _get_redis()
    if r:
        try:
            await r.sadd("wa:active_queues", queue_name)
        except Exception:
            pass


async def unregister_wa_queue(queue_name: str) -> None:
    """Remove a WhatsApp session queue from active set."""
    r = _get_redis()
    if r:
        try:
            await r.srem("wa:active_queues", queue_name)
        except Exception:
            pass

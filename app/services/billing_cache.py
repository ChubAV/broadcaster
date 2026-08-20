import json
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.subscription_service import check_access
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


# ГЕЙТ ДОСТУПА КЭШИРУЕТСЯ ПО ФОРМЕ СНЯТОГО ГЕЙТА ОСТАТКА — ТОЙ ЖЕ ЦЕЛИКОМ, А НЕ
# ПОХОЖЕЙ. Сигнатура `(db, user_id, action) -> tuple[bool, str]` и ранний выход
# по `action != "send"` есть КОНТРАКТ параметра `check_limit` у
# `collect_due_schedules`: только при их сохранении три точки пути отправки
# правились заменой имени, а не правкой поведения.
#
# ⚠️ СТАРАЯ ПАРА ФУНКЦИЙ ОСТАТКА СНЯТА ЗДЕСЬ ВМЕСТЕ С САМИМ СПИСАНИЕМ, И ПОРЯДОК
# БЫЛ НЕСУЩИМ: новый гейт введён планом `05.1-03` РАНЬШЕ, и между двумя
# коммитами путь отправки был закрыт хотя бы одним из двух. Снятие первым
# оставило бы окно, в котором рассылка идёт без гейта вовсе, — то есть истёкший
# доступ рассылал бы бесплатно.
#
# ⚠️ ПРЕЖНЕГО ИМЕНИ КЛЮЧА В ЭТОМ ФАЙЛЕ БОЛЬШЕ НЕТ НИ В ОДНОЙ СТРОКЕ, ВКЛЮЧАЯ
# ЭТУ: регрессия читает файл ТЕКСТОМ, и объяснение, набранное снятым литералом,
# уронило бы собственный запрет (находка плана 05.1-04). Ключи, записанные до
# выката, истекают сами по TTL, и хранимого состояния снятие не оставляет.


async def check_access_cached(
    db: AsyncSession, user_id: int, action: str
) -> tuple[bool, str]:
    """`check_access` с кэшем в Redis. Всё, кроме отправки, разрешено без вопросов.

    ⚠️ КЛЮЧ НАЗЫВАЕТСЯ `access:{user_id}`, И ПЕРЕИМЕНОВАНИЕ ОТНОСИТЕЛЬНО
    ПРЕДШЕСТВЕННИКА БЫЛО РЕШЕНИЕМ, А НЕ ОФОРМЛЕНИЕМ. Значение под ключом сменило
    СМЫСЛ: раньше это был ответ «есть ли сообщения на остатке», теперь — «открыт
    ли доступ». Сохранённое имя дало бы после выката минуту (TTL кэша), в которой
    закэшированные ответы о снятой величине читаются как вердикты авторизации —
    неверные и ничем не отличимые от верных. Старое имя здесь не выписано
    намеренно: регрессия читает файл текстом. Старые ключи истекают сами, и
    хранимого состояния решение не создаёт.

    ОТСУТСТВИЕ REDIS ВЕРДИКТА НЕ ОТМЕНЯЕТ: и чтение, и запись обёрнуты, а расчёт
    идёт в базу. Кэш здесь — экономия запроса, а не источник ответа; гейт
    авторизации, отказывающий при недоступном кэше, останавливал бы рассылку
    всем сразу, а разрешающий — открывал бы её всем сразу.
    """
    if action != "send":
        return True, ""

    cache_key = f"access:{user_id}"
    ttl = get_settings().billing_cache_ttl

    r = _get_redis()
    if r:
        try:
            cached = await r.get(cache_key)
            if cached:
                data = json.loads(cached)
                return data["allowed"], data["reason"]
        except Exception as e:
            logger.debug("access_cache_read_error", cache_key=cache_key, error=str(e))

    allowed, reason = await check_access(db, user_id)

    if r:
        try:
            await r.setex(
                cache_key,
                ttl,
                json.dumps({"allowed": allowed, "reason": reason}),
            )
        except Exception as e:
            logger.debug("access_cache_write_error", cache_key=cache_key, error=str(e))

    return allowed, reason


async def invalidate_access_cache(user_id: int) -> None:
    """Сбросить вердикт доступа после КАЖДОЙ записи `expires_at`.

    Вызывается из подписочной ветки подтверждённого уведомления ЮKassa
    (`app/services/payment_service.py`): без неё оплативший ждал бы до минуты,
    прежде чем доступ откроется, и всё это время видел бы «доступ закрыт» на
    всех страницах и не рассылал бы по расписанию.
    """
    r = _get_redis()
    if r:
        try:
            await r.delete(f"access:{user_id}")
        except Exception as e:
            logger.debug("access_cache_invalidate_error", user_id=user_id, error=str(e))

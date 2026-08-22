"""Единственная точка чтения ОПЕРАТИВНОГО состояния из Redis для веб-процесса.

Форма модуля скопирована с `app/services/billing_cache.py` дословно: модульная
переменная-клиент, ленивая ИМЕНОВАННАЯ функция-получатель `_get_redis`,
возвращающая пустоту при недоступном сервере, и обёртка вокруг каждого
обращения. Именованная точка здесь не украшение и не стиль: суита проекта идёт
на SQLite без единой внешней службы, и подменить чтение Redis в тестах нечем,
кроме именованной точки модуля (`unittest.mock.patch`) — ровно тем же приёмом,
которым в проекте подменяются кэш вердикта доступа и менеджеры контейнеров.
Обработчик, читающий Redis у себя внутри, был бы непроверяем.

Клиент асинхронный (`redis.asyncio`): синхронный в страничном обработчике
заблокировал бы цикл событий на время round-trip, и подраздел с опросом
подвешивал бы весь веб-процесс.

⚠️ ЖИВОСТЬ ИЗМЕРЯЕТСЯ ВОЗРАСТОМ, А НЕ НАЛИЧИЕМ КЛЮЧА. `wa:heartbeat:{id}`
пишется БЕЗ срока жизни (`wa_worker/index.js:965`) и удаляется только при
штатном завершении (`:666`) — WA-воркер, убитый жёстко (OOM, принудительная
остановка, падение хоста), оставляет ключ навсегда. Признак вида `EXISTS` или
`is not None` показывал бы мёртвый воркер живым бессрочно, и именно в аварии,
ради которой подраздел «Воркеры» открывают. У MAX ключ живёт с TTL 90 секунд
(`max_worker/main.py:66-67`) — асимметрия каналов и есть причина, по которой
общий предикат обязан быть возрастным: иначе он верен для одного канала и лжёт
про второй.

⚠️ ПОРОГ НЕ ЗАВОДИТСЯ ЗАНОВО. 90 секунд уже объявлены проектом как ответ на
вопрос «жив ли воркер» (`app/services/max_container_manager.py:20`,
`MAX_HEARTBEAT_STALE_SEC`), и предикат `_has_fresh_heartbeat` (:156-164) —
первообраз здешнего `_is_fresh`. Второе число на тот же вопрос разошлось бы с
первым молча.

⚠️ СОСТОЯНИЙ ТРИ ПЛЮС НЕИЗВЕСТНОСТЬ, А НЕ ДВА. Воркер самоубивается через
`IDLE_SHUTDOWN_SEC = 300`, а менеджер контейнеров поднимает его ТОЛЬКО при
непустой очереди: отсутствие воркера при пустой очереди — ШТАТНОЕ состояние.
Покрашенная красным норма приучает администратора не смотреть в подраздел
вовсе — и тогда настоящий отказ он тоже не увидит.
"""
import time

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


# ТО ЖЕ ЧИСЛО, что `app/services/max_container_manager.py:20`. Дискреционное
# «около 60 секунд» из обсуждения закрывается уже объявленным значением, а не
# новым: два разных порога на один вопрос — ровно тот класс расхождения, который
# проект закрывает вынесением константы.
MAX_HEARTBEAT_STALE_SEC = 90

# Состояния воркера. Строки, а не булево: «нет heartbeat» распадается на два
# РАЗНЫХ ответа, и сведение их в один флаг было бы потерей именно той разницы,
# ради которой подраздел читают.
WORKER_ONLINE = "online"
WORKER_IDLE = "idle"
WORKER_OFFLINE = "offline"
WORKER_UNKNOWN = "unknown"

# Префиксы ключей по фактическому инвентарю (`06-RESEARCH.md` § Redis Key
# Inventory). Ключ конечной точки контейнера НЕ читается: heartbeat отвечает на
# тот же вопрос точнее — конечная точка переживает смерть своего владельца.
CHANNEL_WA = "wa"
CHANNEL_MAX = "max"

_redis_client = None


def _get_redis():
    """Ленивый клиент Redis для чтения оперативного состояния.

    ЕДИНСТВЕННАЯ точка подмены модуля — на ней держится проверяемость всего
    подраздела «Воркеры» без поднятой внешней службы.
    """
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio

            settings = get_settings()
            _redis_client = redis.asyncio.from_url(settings.redis_url)
        except Exception:
            logger.warning("ops_state_redis_unavailable")
            return None
    return _redis_client


def _is_fresh(raw: bytes | str | None) -> bool:
    """Свеж ли heartbeat: ВОЗРАСТ значения против порога, а не факт его наличия.

    Значение — эпоха в МИЛЛИСЕКУНДАХ у обоих каналов (`Date.now()` у WA,
    `int(time.time() * 1000)` у MAX).

    Обе границы несущие. Верхняя — потому что у WA нет TTL и ключ переживает
    жёсткое убийство воркера. Нижняя (`0 <= age_ms`) — потому что heartbeat из
    БУДУЩЕГО при разошедшихся часах иначе читался бы как «только что», то есть
    расхождение часов маскировало бы отказ.
    """
    try:
        beat_ms = int(raw)
    except (TypeError, ValueError):
        return False

    age_ms = int(time.time() * 1000) - beat_ms
    return 0 <= age_ms <= MAX_HEARTBEAT_STALE_SEC * 1000


def _unknown() -> dict:
    """Наблюдатель сломан — про воркера НЕ утверждается ничего.

    Отдать здесь «отключён» значило бы сообщить об аварии воркеров, когда
    сломан наблюдатель: администратор пошёл бы чинить исправное.
    """
    return {"queue_depth": None, "worker": WORKER_UNKNOWN}


def _classify(beat: bytes | str | None, depth: int) -> str:
    """Состояние воркера по свежести heartbeat и глубине его очереди (D-08).

    «Отключён» честен РОВНО при непустой очереди и несвежем heartbeat: работа
    есть, а делать её некому. Пустая очередь без heartbeat — «простаивает»,
    штатное состояние выключенного за ненадобностью воркера.
    """
    if _is_fresh(beat):
        return WORKER_ONLINE
    return WORKER_OFFLINE if depth > 0 else WORKER_IDLE


async def worker_liveness(
    wa_ids: list[int],
    max_ids: list[int],
) -> dict[int, dict]:
    """Живость и глубина очереди для всех аккаунтов — ОДНИМ round-trip.

    Подраздел «Воркеры» обновляется опросом: отдельный запрос на каждый ключ
    умножился бы на число строк И на число тиков, то есть нагрузка росла бы
    произведением, а не суммой.

    Возвращает `{идентификатор аккаунта: {"queue_depth": int|None,
    "worker": состояние}}`. Недоступный Redis и ошибка чтения дают
    «неизвестно» КАЖДОМУ аккаунту и не поднимают исключение: подраздел обязан
    отвечать 200 и при сломанном наблюдателе.
    """
    accounts: list[tuple[str, int]] = [
        *((CHANNEL_WA, account_id) for account_id in wa_ids),
        *((CHANNEL_MAX, account_id) for account_id in max_ids),
    ]
    if not accounts:
        return {}

    client = _get_redis()
    if client is None:
        return {account_id: _unknown() for _, account_id in accounts}

    try:
        pipe = client.pipeline()
        for channel, account_id in accounts:
            pipe.get(f"{channel}:heartbeat:{account_id}")
            pipe.llen(f"{channel}:queue:{account_id}")
        flat = await pipe.execute()
    except Exception as e:
        logger.warning("ops_state_liveness_read_error", error=str(e))
        return {account_id: _unknown() for _, account_id in accounts}

    if flat is None or len(flat) < 2 * len(accounts):
        logger.warning("ops_state_liveness_short_reply", expected=2 * len(accounts))
        return {account_id: _unknown() for _, account_id in accounts}

    out: dict[int, dict] = {}
    for position, (_, account_id) in enumerate(accounts):
        beat = flat[2 * position]
        try:
            depth = int(flat[2 * position + 1] or 0)
        except (TypeError, ValueError):
            depth = 0
        out[account_id] = {"queue_depth": depth, "worker": _classify(beat, depth)}
    return out


# ---------------------------------------------------------------------------
# Живость ИНФРАСТРУКТУРНЫХ служб (D-52, вариант C чекпойнта плана 06-05)
# ---------------------------------------------------------------------------
#
# ⚠️ ИСТОЧНИК — СОБСТВЕННЫЙ heartbeat CELERY-ПРОЦЕССОВ, А НЕ СОСТОЯНИЕ
# КОНТЕЙНЕРА. Контракт Фазы 1 (D-19) и D-07 настоящей фазы держатся буквально:
# демон контейнеров на пути отрисовки не зовётся вовсе, потому что недоступный
# демон вешал бы подраздел ровно в той аварии, ради которой его открывают.
# Широковещательный `celery inspect` отвергнут тем же доводом, которым D-15
# убрал статус «в работе»: запрос с таймаутом на пути рендера подвешивает
# страницу при неотвечающем воркере.
#
# ⚠️ СОСТОЯНИЙ ЗДЕСЬ ТРИ, И «ПРОСТАИВАЕТ» СРЕДИ НИХ НЕТ — ЭТО РЕШЕНИЕ, А НЕ
# ПРОПУСК. Граница D-08 объявлена для воркеров АККАУНТОВ: они самоубиваются
# через `IDLE_SHUTDOWN_SEC = 300`, поэтому их молчание при пустой очереди —
# норма. Celery-процесс по простою не уходит никогда, и его молчание означает
# отказ. Покрасить отказ нейтральным словом «простаивает» было бы той же
# потерей достоверности, что и покрасить норму красным.
INFRA_BEAT = "beat"
INFRA_WORKER_TELEGRAM = "worker-telegram"
INFRA_WORKER_DEFAULT = "worker-default"

# Порядок объявлен ЗДЕСЬ и читается и писателем, и читателем, и разметкой:
# вторая копия перечня разъехалась бы с первой молча — служба поменяла бы имя в
# одном месте, а верхний блок продолжал бы искать ключ по старому.
INFRA_SERVICE_ORDER: tuple[str, ...] = (
    INFRA_BEAT,
    INFRA_WORKER_TELEGRAM,
    INFRA_WORKER_DEFAULT,
)

# Закрытое множество состояний инфраструктурной службы — ПОДМНОЖЕСТВО той же
# четвёрки, которой пользуются воркеры аккаунтов. Пятого состояния не заводится:
# новое слово в колонке состояния требует нового способа его опровергнуть.
INFRA_STATES: frozenset[str] = frozenset(
    {WORKER_ONLINE, WORKER_OFFLINE, WORKER_UNKNOWN}
)

INFRA_HEARTBEAT_KEY_PREFIX = "infra:heartbeat:"


def infra_heartbeat_key(service: str) -> str:
    """Ключ живости инфраструктурной службы.

    Форма ключа объявлена ЗДЕСЬ, в модуле читателя, и импортируется писателем
    (`app/worker/celery_app.py`). Направление выбрано намеренно: писателей три
    процесса, читатель один, и одна выписанная строка на стороне писателя
    разошлась бы с читателем без единого падения — ключ бы просто не нашёлся, а
    верхний блок показал бы «отключён» на живой службе.
    """
    return f"{INFRA_HEARTBEAT_KEY_PREFIX}{service}"


async def infra_liveness() -> dict[str, str]:
    """Состояние трёх инфраструктурных служб — ОДНИМ round-trip.

    Возвращает `{имя службы: состояние}`. Недоступный Redis, ошибка чтения и
    короткий ответ конвейера дают «неизвестно» КАЖДОЙ службе и не поднимают
    исключение: подраздел обязан отвечать 200 и при сломанном наблюдателе —
    иначе он переставал бы открываться ровно тогда, когда нужен.

    ⚠️ «НЕИЗВЕСТНО», А НЕ «ОТКЛЮЧЁН», ПРИ СЛОМАННОМ НАБЛЮДАТЕЛЕ. Разница не
    оформительская: «отключён» отправил бы администратора перезапускать
    исправные службы, пока настоящая причина — недоступный Redis — осталась бы
    ненайденной.
    """
    unknown = {service: WORKER_UNKNOWN for service in INFRA_SERVICE_ORDER}

    client = _get_redis()
    if client is None:
        return unknown

    try:
        pipe = client.pipeline()
        for service in INFRA_SERVICE_ORDER:
            pipe.get(infra_heartbeat_key(service))
        beats = await pipe.execute()
    except Exception as e:
        logger.warning("ops_state_infra_read_error", error=str(e))
        return unknown

    if beats is None or len(beats) < len(INFRA_SERVICE_ORDER):
        logger.warning(
            "ops_state_infra_short_reply", expected=len(INFRA_SERVICE_ORDER)
        )
        return unknown

    return {
        service: (WORKER_ONLINE if _is_fresh(beats[position]) else WORKER_OFFLINE)
        for position, service in enumerate(INFRA_SERVICE_ORDER)
    }

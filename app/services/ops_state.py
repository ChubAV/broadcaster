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
import json
import time
from dataclasses import dataclass

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


# ---------------------------------------------------------------------------
# Содержимое очередей и снятие одной задачи (ADMIN-08, D-13, D-17)
# ---------------------------------------------------------------------------
#
# ⚠️ ЧТЕНИЕ ОЧЕРЕДИ НЕ СНИМАЕТ ЗАДАЧИ, И ЭТО ГЛАВНОЕ ОГРАНИЧЕНИЕ РАЗДЕЛА.
# Подраздел отвечает на вопрос «что ждёт отправки»; чтение, снимающее элементы,
# отняло бы у пользователей оплаченные рассылки просто оттого, что администратор
# открыл страницу. Поэтому здесь есть `LRANGE` и нет ни одного `LPOP`/`BLPOP` —
# отсутствие закреплено грепом в критериях приёмки плана.
#
# ⚠️ ДЛИНА ОЧЕРЕДИ TELEGRAM ЧИТАЕТСЯ ПО ИМЕНИ, БЕЗ РАЗБОРА СОДЕРЖИМОГО (D-14).
# Тело задачи там — конверт брокера с закодированным содержимым; его разбор
# привязал бы админку к внутренностям библиотеки, которые меняются между
# версиями молча. Счёт по длине полон РОВНО ПОКА постановка не передаёт
# приоритет: с ненулевым приоритетом kombu раскладывает задачи по ключам с
# суффиксами (`_q_for_pri`), и подраздел начал бы недосчитывать без единого
# признака. Этот день ловит `test_no_dispatch_call_in_the_project_passes_a_priority`.

# Имя очереди канала telegram — то же, которым постановщик зовёт `apply_async`
# (`app/worker/tasks.py:96-100`). Выписанное здесь вторым литералом, оно
# разъехалось бы с постановщиком молча: подраздел считал бы длину ключа,
# которого никто не пишет, и печатал бы уверенный ноль.
TELEGRAM_QUEUE_KEY = "telegram"

# Исходы снятия задачи. Строки, а не булево: «снял» и «уже нечего снимать» —
# разные ответы администратору, и третий, «наблюдатель сломан», не имеет права
# слиться ни с одним из них. Молчаливый успех при недоступном Redis был бы
# худшим из трёх: администратор решил бы, что отправку остановил.
DROP_REMOVED = "removed"
DROP_MISSING = "missing"
DROP_UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class QueuePage:
    """Прочитанная страница очереди канала.

    `total` — длина ВСЕЙ очереди, а не число прочитанных тел: страница усечена
    потолком, и без полной длины разметка не смогла бы назвать усечение.
    `unavailable` едет ОТДЕЛЬНЫМ полем: пустая очередь и сломанный наблюдатель —
    разные состояния мира, и слитые в одно они сообщили бы «рассылать нечего»
    ровно тогда, когда очередь стоит и её не видно.
    `unreadable` — число тел, которые не разобрались: битая задача не имеет права
    ни уронить подраздел, ни исчезнуть молча, поэтому она считается и называется.
    """

    tasks: tuple[dict, ...]
    total: int | None
    unavailable: bool
    unreadable: int = 0


def queue_key(channel: str, account_id: int) -> str:
    """Ключ очереди аккаунта. Форма — из инвентаря ключей (`06-RESEARCH.md`)."""
    return f"{channel}:queue:{account_id}"


async def _read_raw(client, key: str, limit: int) -> list | None:
    """Сырые тела задач и длина очереди — ОДНИМ конвейером, НЕ снимая элементов.

    `LRANGE` берёт диапазон, а не всё: список Redis неограничен, и очередь
    вставшего канала растёт неограниченно же. Отрисовка всей очереди уложила бы
    подраздел ровно в той аварии, ради которой его открывают (T-06-Q2).
    """
    pipe = client.pipeline()
    pipe.llen(key)
    pipe.lrange(key, 0, limit - 1)
    return await pipe.execute()


async def queue_page(channel: str, account_id: int, limit: int) -> QueuePage:
    """Страница очереди аккаунта: тела задач и полная длина, БЕЗ снятия.

    Недоступный Redis и ошибка чтения не поднимают исключение и не притворяются
    пустой очередью: подраздел обязан отвечать 200 и при сломанном наблюдателе,
    но обязан и назвать его сломанным.
    """
    client = _get_redis()
    if client is None:
        return QueuePage(tasks=(), total=None, unavailable=True)

    key = queue_key(channel, account_id)
    try:
        reply = await _read_raw(client, key, limit)
    except Exception as e:
        logger.warning(
            "ops_state_queue_read_error", key=key, error=str(e)
        )
        return QueuePage(tasks=(), total=None, unavailable=True)

    if reply is None or len(reply) < 2:
        logger.warning("ops_state_queue_short_reply", key=key)
        return QueuePage(tasks=(), total=None, unavailable=True)

    try:
        total = int(reply[0] or 0)
    except (TypeError, ValueError):
        total = 0

    tasks: list[dict] = []
    unreadable = 0
    for raw in reply[1] or []:
        body = _decode_task(raw)
        if body is None:
            unreadable += 1
            continue
        tasks.append(body)

    if unreadable:
        # Битое тело считается и называется разметкой. Пропущенное молча, оно
        # укоротило бы список ровно так же, как потолок, — то есть ответило бы
        # «остальных задач нет» на вопрос, ради которого сюда пришли.
        logger.warning("ops_state_queue_unreadable_bodies", key=key, count=unreadable)

    return QueuePage(
        tasks=tuple(tasks),
        total=total,
        unavailable=False,
        unreadable=unreadable,
    )


def _decode_task(raw) -> dict | None:
    """Сырое тело задачи → словарь. Мусор возвращает пустоту, а не исключение."""
    try:
        body = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return body if isinstance(body, dict) else None


async def telegram_queue_depth() -> int | None:
    """Число задач в очереди канала telegram — ОДНИМ обращением по имени ключа.

    Содержимое не разбирается вовсе (D-14). Недоступность возвращается пустотой,
    и разметка обязана отличать её от нуля: «задач нет» и «сколько задач —
    неизвестно» отвечают на один вопрос противоположным образом.
    """
    client = _get_redis()
    if client is None:
        return None

    try:
        return int(await client.llen(TELEGRAM_QUEUE_KEY) or 0)
    except Exception as e:
        logger.warning("ops_state_telegram_depth_error", error=str(e))
        return None


async def drop_task(
    channel: str, account_id: int, task_id: str, limit: int
) -> str:
    """Снять ОДНУ задачу очереди по её идентификатору. Возвращает исход.

    ⚠️ ФОРМА ПРИСЫЛАЕТ ИДЕНТИФИКАТОР, А ТЕЛО СЕРВЕР БЕРЁТ ИЗ СВОЕГО ЧТЕНИЯ
    (T-06-DROP2). Тело в этих очередях содержит текст чужого объявления и может
    быть большим; доверять клиенту точные байты удаляемого не нужно вовсе. Здесь
    сервер читает страницу очереди сам, находит элемент с совпавшим
    идентификатором и удаляет ИМЕННО ТЕ БАЙТЫ, которые прочитал.

    ⚠️ КОЛИЧЕСТВО УДАЛЯЕМЫХ — ЯВНАЯ ЕДИНИЦА, А НЕ НОЛЬ. Ноль удалил бы ВСЕ
    совпадающие вхождения. Тела содержат `task_id` из uuid4 и потому сегодня
    уникальны, но правило «снять одну» обязано быть ВЫРАЖЕНО, а не выведено из
    свойства данных: свойство завтра может перестать выполняться, а правило —
    нет.

    ⚠️ ЗАПИСИ В ЖУРНАЛ ОТПРАВОК ЗДЕСЬ НЕТ И НЕ БУДЕТ (D-18): журнал отражает
    совершённые попытки отправки, а снятая задача попытки не совершила. След
    остаётся именованной строкой журнала приложения на стороне обработчика.
    """
    client = _get_redis()
    if client is None:
        return DROP_UNAVAILABLE

    key = queue_key(channel, account_id)
    try:
        reply = await _read_raw(client, key, limit)
    except Exception as e:
        logger.warning("ops_state_drop_read_error", key=key, error=str(e))
        return DROP_UNAVAILABLE

    if reply is None or len(reply) < 2:
        logger.warning("ops_state_drop_short_reply", key=key)
        return DROP_UNAVAILABLE

    target = None
    for raw in reply[1] or []:
        body = _decode_task(raw)
        if body is not None and body.get("task_id") == task_id:
            target = raw
            break

    if target is None:
        # Задача ушла из очереди сама, пока администратор читал экран, — это
        # НОРМАЛЬНЫЙ исход, и он называется словами, а не молчаливым возвратом.
        return DROP_MISSING

    try:
        removed = await client.lrem(key, 1, target)
    except Exception as e:
        logger.warning("ops_state_drop_error", key=key, error=str(e))
        return DROP_UNAVAILABLE

    return DROP_REMOVED if removed else DROP_MISSING

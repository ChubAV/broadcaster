"""Сервис оперативного состояния: живость воркера измеряется ВОЗРАСТОМ heartbeat.

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА — `test_stale_heartbeat_without_ttl_reads_dead`.
WA-воркер пишет `wa:heartbeat:{id}` БЕЗ срока жизни (wa_worker/index.js:965) и
удаляет ключ только при штатном завершении (:666). Значит воркер, убитый жёстко
(OOM, `docker kill`, падение хоста), оставляет ключ НАВСЕГДА, и признак живости
вида `EXISTS`/`is not None` показывал бы мёртвый воркер живым бессрочно — ИМЕННО
в аварии, ради которой подраздел «Воркеры» и открывают. Поэтому предикат
сравнивает возраст с порогом, а тест назначает эту границу ДО того, как на неё
начнут опираться остальные планы фазы.

⚠️ НИЖНЯЯ ГРАНИЦА ВОЗРАСТА — ТОЖЕ УТВЕРЖДЕНИЕ, А НЕ ПЕДАНТИЗМ. heartbeat из
будущего (часы веб-процесса и контейнера разошлись) при проверке только сверху
читался бы как «только что», то есть расхождение часов маскировало бы отказ.

⚠️ ТРИ СОСТОЯНИЯ, А НЕ ДВА (D-08). Воркер самоубивается через
`IDLE_SHUTDOWN_SEC = 300`, а менеджер контейнеров поднимает его ТОЛЬКО при
непустой очереди — значит отсутствие контейнера при пустой очереди есть ШТАТНОЕ
состояние, а не отказ. «Отключён» честен ровно при непустой очереди И несвежем
heartbeat. Покрашенная красным норма приучает администратора не смотреть в
подраздел вовсе, и тогда настоящий отказ он тоже не увидит.

Ни один тест здесь не требует поднятого Redis: суита идёт на SQLite без внешних
служб, и подменяется ИМЕНОВАННАЯ ленивая точка получения клиента —
`app.services.ops_state._get_redis`, ровно тем же приёмом, что в
`tests/test_billing_cache.py`.
"""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ops_state import (
    MAX_HEARTBEAT_STALE_SEC,
    WORKER_IDLE,
    WORKER_OFFLINE,
    WORKER_ONLINE,
    WORKER_UNKNOWN,
    _is_fresh,
    worker_liveness,
)


def _beat(age_sec: float) -> str:
    """Значение heartbeat возрастом `age_sec` секунд — эпоха в МИЛЛИСЕКУНДАХ.

    Миллисекунды у обоих каналов: `Date.now()` у WA (wa_worker/index.js:965) и
    `str(int(time.time() * 1000))` у MAX (max_worker/main.py:792-798).
    """
    return str(int((time.time() - age_sec) * 1000))


def _fake_redis(values: list):
    """Двойник клиента с pipeline: `execute` отдаёт плоский список значений."""
    pipe = MagicMock()
    pipe.get = MagicMock(return_value=pipe)
    pipe.llen = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=values)

    client = MagicMock()
    client.pipeline = MagicMock(return_value=pipe)
    return client, pipe


# ---- Предикат свежести ----

def test_fresh_heartbeat_just_written_reads_alive():
    """Только что записанный heartbeat читается свежим."""
    assert _is_fresh(_beat(0)) is True


def test_stale_heartbeat_without_ttl_reads_dead():
    """Ключ ЕСТЬ, а воркер мёртв: возраст больше порога — несвежий (Ф-6).

    Это и есть тот случай, ради которого предикат сравнивает возраст: у WA нет
    TTL, и `EXISTS` вернул бы истину для ключа, пережившего жёсткое убийство.
    """
    assert _is_fresh(_beat(MAX_HEARTBEAT_STALE_SEC + 30)) is False


def test_future_heartbeat_reads_stale_not_just_now():
    """heartbeat из будущего (часы разошлись) — несвежий, а не «только что»."""
    assert _is_fresh(_beat(-3600)) is False


def test_non_numeric_and_missing_heartbeat_read_stale_without_raising():
    """Мусор и отсутствие значения читаются несвежими и НЕ бросают исключение."""
    assert _is_fresh(None) is False
    assert _is_fresh(b"") is False
    assert _is_fresh("not-a-number") is False


def test_heartbeat_in_bytes_reads_alive():
    """Клиент без декодирования отдаёт байты — предикат обязан их принять."""
    assert _is_fresh(_beat(1).encode()) is True


# ---- Три состояния воркера ----

@pytest.mark.asyncio
async def test_stale_heartbeat_with_empty_queue_is_idle_not_offline():
    """Нет heartbeat и очередь ПУСТА — простаивает, а не отключён (D-08).

    Воркер уходит сам через 300 секунд простоя, и менеджер поднимает его только
    при непустой очереди: отсутствие контейнера здесь — норма.
    """
    client, _ = _fake_redis([_beat(MAX_HEARTBEAT_STALE_SEC + 60), 0])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await worker_liveness(wa_ids=[7], max_ids=[])
    assert result[7]["worker"] == WORKER_IDLE
    assert result[7]["queue_depth"] == 0


@pytest.mark.asyncio
async def test_stale_heartbeat_with_pending_queue_is_offline():
    """Нет heartbeat, но очередь НЕПУСТА — отключён: работа есть, делать некому."""
    client, _ = _fake_redis([_beat(MAX_HEARTBEAT_STALE_SEC + 60), 4])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await worker_liveness(wa_ids=[7], max_ids=[])
    assert result[7]["worker"] == WORKER_OFFLINE
    assert result[7]["queue_depth"] == 4


@pytest.mark.asyncio
async def test_fresh_heartbeat_is_online_regardless_of_queue_depth():
    """Свежий heartbeat — «в работе» и при пустой, и при непустой очереди."""
    client, _ = _fake_redis([_beat(1), 0, _beat(1), 9])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await worker_liveness(wa_ids=[1], max_ids=[2])
    assert result[1]["worker"] == WORKER_ONLINE
    assert result[2]["worker"] == WORKER_ONLINE
    assert result[2]["queue_depth"] == 9


# ---- Один round-trip и деградация ----

@pytest.mark.asyncio
async def test_liveness_summary_uses_single_pipeline_round_trip():
    """Сводка по WA- и MAX-аккаунтам уходит ОДНИМ `execute`.

    Подраздел обновляется опросом: запрос на каждый ключ умножился бы на число
    строк И на число тиков.
    """
    client, pipe = _fake_redis([_beat(1), 2, _beat(300), 0, _beat(1), 5])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await worker_liveness(wa_ids=[11, 12], max_ids=[21])

    assert pipe.execute.await_count == 1
    assert client.pipeline.call_count == 1
    assert set(result) == {11, 12, 21}
    # Ключи именуются по фактическому инвентарю каждого канала.
    read_keys = [call.args[0] for call in pipe.get.call_args_list]
    assert read_keys == ["wa:heartbeat:11", "wa:heartbeat:12", "max:heartbeat:21"]
    queue_keys = [call.args[0] for call in pipe.llen.call_args_list]
    assert queue_keys == ["wa:queue:11", "wa:queue:12", "max:queue:21"]


@pytest.mark.asyncio
async def test_liveness_summary_returns_unknown_when_redis_unavailable():
    """Недоступный Redis даёт «неизвестно» каждому аккаунту и НЕ бросает.

    Отдавать здесь «отключён» значило бы сообщить об аварии воркеров, когда
    сломан наблюдатель.
    """
    with patch("app.services.ops_state._get_redis", return_value=None):
        result = await worker_liveness(wa_ids=[1], max_ids=[2])
    assert result[1]["worker"] == WORKER_UNKNOWN
    assert result[2]["worker"] == WORKER_UNKNOWN
    assert result[1]["queue_depth"] is None


@pytest.mark.asyncio
async def test_liveness_summary_survives_redis_error_mid_flight():
    """Упавший `execute` не роняет подраздел — состояние «неизвестно»."""
    client, pipe = _fake_redis([])
    pipe.execute = AsyncMock(side_effect=OSError("connection reset"))
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await worker_liveness(wa_ids=[5], max_ids=[])
    assert result[5]["worker"] == WORKER_UNKNOWN


@pytest.mark.asyncio
async def test_empty_account_lists_do_not_touch_redis():
    """Пустой перечень аккаунтов не порождает ни одного обращения."""
    client, pipe = _fake_redis([])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await worker_liveness(wa_ids=[], max_ids=[])
    assert result == {}
    assert pipe.execute.await_count == 0


# ---- Инфраструктурный heartbeat: писатель и читатель одного контракта (D-52) ----
#
# ⚠️ ПИСАТЕЛЬ ИМПОРТИРУЕТСЯ ЧЕРЕЗ ФИКСТУРУ, А НЕ СВЕРХУ ФАЙЛА, И ЭТО НЕ СТИЛЬ.
# `app/worker/celery_app.py` строит приложение Celery НА УРОВНЕ МОДУЛЯ, а оно
# читает настройки из файла окружения. Файла окружения в суите нет намеренно:
# тесты обязаны идти на чистой машине. Импорт сверху уронил бы ВЕСЬ файл — в том
# числе двенадцать утверждений про читателя, к писателю отношения не имеющих.


@pytest.fixture
def celery_app_module():
    """Модуль приложения Celery, импортируемый без файла окружения.

    Два обязательных поля настроек назначаются заглушками ТОЛЬКО ради импорта:
    предмет проверки — форма ключа heartbeat, его единица и срок жизни, и ни
    адрес базы, ни подпись сессий в них не участвуют. `setdefault` выбран
    вместо присваивания намеренно: настоящее окружение, если оно есть,
    перетирать нельзя.
    """
    import os

    from app.config import get_settings

    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "import-only-not-a-real-secret")
    get_settings.cache_clear()

    import app.worker.celery_app as module

    return module
#
# ⚠️ ПИСАТЕЛЬ И ЧИТАТЕЛЬ ПРОВЕРЯЮТСЯ В ОДНОМ ФАЙЛЕ НАМЕРЕННО. Ключ пишет
# приложение Celery (`app/worker/celery_app.py`), читает веб-процесс
# (`app/services/ops_state.py`), и разъехаться они могут молча: писатель
# продолжит писать, читатель — читать пустоту, и верхний блок покажет
# «отключён» на живых службах. Единственная защита от такого расхождения —
# утверждение, читающее ОБЕ стороны сразу.


def test_infra_ttl_is_the_same_number_the_reader_calls_stale(celery_app_module):
    """Срок жизни ключа равен порогу свежести — второго числа не заведено.

    ⚠️ ЭТО ЗАПРЕТ, А НЕ СОВПАДЕНИЕ. Писатель ставит ключу TTL, читатель
    сравнивает ВОЗРАСТ значения с порогом. Разъехавшись, они дали бы два
    разных ответа на один вопрос «жив ли процесс»: ключ, переживший порог,
    читался бы мёртвым, а ключ, умерший раньше порога, — неизвестным.
    """
    INFRA_HEARTBEAT_INTERVAL_SEC = celery_app_module.INFRA_HEARTBEAT_INTERVAL_SEC
    INFRA_HEARTBEAT_TTL_SEC = celery_app_module.INFRA_HEARTBEAT_TTL_SEC

    assert INFRA_HEARTBEAT_TTL_SEC == INFRA_HEARTBEAT_INTERVAL_SEC * 3, (
        "форма срока жизни разошлась с образцом MAX-воркера "
        "(HEARTBEAT_TTL_SEC = HEARTBEAT_INTERVAL_SEC * 3)"
    )
    assert INFRA_HEARTBEAT_TTL_SEC == MAX_HEARTBEAT_STALE_SEC, (
        "срок жизни ключа разошёлся с порогом свежести читателя — "
        "на вопрос «жив ли процесс» в проекте появилось два числа"
    )


def test_infra_role_comes_from_the_consumed_queue_not_from_a_container_name(
    celery_app_module,
):
    """Роль celery-воркера выводится из ВЫБРАННОЙ очереди (D-52).

    Имя контейнера — свойство развёртывания и переименовывается в
    docker-compose.yml без единой правки кода; очередь — свойство самого
    процесса, объявленное его же командой запуска (`--queues=telegram`).
    """
    from app.services.ops_state import INFRA_WORKER_DEFAULT, INFRA_WORKER_TELEGRAM

    _infra_service_for_queues = celery_app_module._infra_service_for_queues

    assert _infra_service_for_queues(["telegram"]) == INFRA_WORKER_TELEGRAM
    assert _infra_service_for_queues(["default"]) == INFRA_WORKER_DEFAULT
    # Воркер без указанной очереди слушает всё — общие задачи в том числе.
    assert _infra_service_for_queues([]) == INFRA_WORKER_DEFAULT


def test_infra_heartbeat_writer_puts_a_millisecond_epoch_under_the_read_key(
    celery_app_module,
):
    """Писатель кладёт эпоху в МИЛЛИСЕКУНДАХ по тому ключу, который читают.

    Единица не декоративна: `_is_fresh` делит на миллисекунды, и секунды под
    тем же ключом дали бы возраст в пятьдесят с лишним лет, то есть вечное
    «отключён» на живой службе.
    """
    from app.services.ops_state import INFRA_WORKER_TELEGRAM, infra_heartbeat_key

    INFRA_HEARTBEAT_TTL_SEC = celery_app_module.INFRA_HEARTBEAT_TTL_SEC
    _write_infra_heartbeat = celery_app_module._write_infra_heartbeat

    client = MagicMock()
    _write_infra_heartbeat(client, INFRA_WORKER_TELEGRAM)

    (key, value), kwargs = client.set.call_args
    assert key == infra_heartbeat_key(INFRA_WORKER_TELEGRAM)
    assert key == "infra:heartbeat:worker-telegram"
    assert kwargs.get("ex") == INFRA_HEARTBEAT_TTL_SEC
    assert _is_fresh(value) is True


# ---- Чтение живости инфраструктуры (D-52) ----

@pytest.mark.asyncio
async def test_infra_liveness_reads_three_keys_in_one_round_trip():
    """Три службы читаются ОДНИМ конвейером и своими ключами."""
    from app.services.ops_state import (
        INFRA_BEAT,
        INFRA_WORKER_DEFAULT,
        INFRA_WORKER_TELEGRAM,
        infra_liveness,
    )

    client, pipe = _fake_redis([_beat(1), _beat(1), _beat(1)])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await infra_liveness()

    assert pipe.execute.await_count == 1
    assert client.pipeline.call_count == 1
    assert [call.args[0] for call in pipe.get.call_args_list] == [
        "infra:heartbeat:beat",
        "infra:heartbeat:worker-telegram",
        "infra:heartbeat:worker-default",
    ]
    assert result == {
        INFRA_BEAT: WORKER_ONLINE,
        INFRA_WORKER_TELEGRAM: WORKER_ONLINE,
        INFRA_WORKER_DEFAULT: WORKER_ONLINE,
    }


@pytest.mark.asyncio
async def test_infra_stale_heartbeat_is_offline_and_never_idle():
    """Несвежий heartbeat инфраструктуры — «отключён», а НЕ «простаивает».

    ⚠️ ГРАНИЦА D-08 НЕ РАСТЯГИВАЕТСЯ НА ВЕРХНИЙ БЛОК, И ЭТО УТВЕРЖДЕНИЕ.
    `wa-worker` и `max-worker` самоубиваются через `IDLE_SHUTDOWN_SEC = 300`,
    поэтому у них отсутствие heartbeat при пустой очереди — норма. Celery-
    процесс по простою не уходит НИКОГДА: его молчание означает отказ, и
    «простаивает» здесь было бы покрашенной в нейтральный цвет аварией.
    """
    from app.services.ops_state import INFRA_BEAT, infra_liveness

    client, _ = _fake_redis([_beat(600), _beat(600), _beat(600)])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await infra_liveness()

    assert set(result.values()) == {WORKER_OFFLINE}
    assert WORKER_IDLE not in result.values()
    assert result[INFRA_BEAT] == WORKER_OFFLINE


@pytest.mark.asyncio
async def test_infra_liveness_is_unknown_when_the_observer_is_broken():
    """Недоступный Redis и оборванное чтение дают «неизвестно», а не отказ."""
    from app.services.ops_state import infra_liveness

    with patch("app.services.ops_state._get_redis", return_value=None):
        result = await infra_liveness()
    assert set(result.values()) == {WORKER_UNKNOWN}

    client, pipe = _fake_redis([])
    pipe.execute = AsyncMock(side_effect=OSError("connection reset"))
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await infra_liveness()
    assert set(result.values()) == {WORKER_UNKNOWN}

    # Короткий ответ конвейера — тоже сломанный наблюдатель, а не отказ служб.
    client, _ = _fake_redis([_beat(1)])
    with patch("app.services.ops_state._get_redis", return_value=client):
        result = await infra_liveness()
    assert set(result.values()) == {WORKER_UNKNOWN}


def test_infra_states_are_drawn_from_the_existing_four_state_vocabulary():
    """Пятого состояния не заведено: инфраструктура пользуется той же четвёркой."""
    from app.services import ops_state

    allowed = {WORKER_ONLINE, WORKER_IDLE, WORKER_OFFLINE, WORKER_UNKNOWN}
    assert ops_state.INFRA_STATES <= allowed
    assert WORKER_IDLE not in ops_state.INFRA_STATES


# ---- Чтение очередей и снятие одной задачи (ADMIN-08, D-13, D-17) ----
#
# ⚠️ ЧТЕНИЕ ОЧЕРЕДИ НЕ ИМЕЕТ ПРАВА СНИМАТЬ ЗАДАЧИ. Подраздел отвечает на вопрос
# «что ждёт отправки», и чтение, снимающее элементы, отняло бы у пользователей
# оплаченные рассылки просто оттого, что администратор открыл страницу. Поэтому
# двойник клиента ниже держит НАСТОЯЩИЙ список: утверждения адресуются данным, а
# не количеству вызовов — вызов можно сделать правильным и всё равно потерять
# задачу.

class _FakeQueueRedis:
    """Двойник клиента Redis, хранящий очереди настоящими списками.

    Проверять снятие по вызванным методам недостаточно: `LREM` с количеством 0
    удаляет ВСЕ совпадающие вхождения, и утверждение «lrem был вызван» зеленело
    бы ровно в том случае, ради запрета которого тест и написан. Список
    изменяется по-настоящему, и проверяется его содержимое.
    """

    def __init__(self, lists: dict[str, list[bytes]] | None = None):
        self.lists: dict[str, list[bytes]] = lists or {}
        self.lrem_calls: list[tuple] = []
        self.forbidden_calls: list[str] = []

    # -- конвейер --
    def pipeline(self):
        return _FakeQueuePipeline(self)

    # -- одиночные команды --
    async def llen(self, key: str) -> int:
        return len(self.lists.get(key, []))

    async def lrange(self, key: str, start: int, stop: int) -> list[bytes]:
        items = self.lists.get(key, [])
        return items[start:] if stop == -1 else items[start : stop + 1]

    async def lrem(self, key: str, count: int, value: bytes) -> int:
        self.lrem_calls.append((key, count, value))
        items = self.lists.get(key, [])
        removed = 0
        limit = count if count > 0 else len(items)
        out: list[bytes] = []
        for item in items:
            if item == value and removed < limit:
                removed += 1
                continue
            out.append(item)
        self.lists[key] = out
        return removed

    # -- команды, снимающие задачи: их здесь быть не должно --
    async def lpop(self, *args, **kwargs):
        self.forbidden_calls.append("lpop")
        raise AssertionError("чтение очереди сняло задачу через lpop")

    async def rpop(self, *args, **kwargs):
        self.forbidden_calls.append("rpop")
        raise AssertionError("чтение очереди сняло задачу через rpop")

    async def blpop(self, *args, **kwargs):
        self.forbidden_calls.append("blpop")
        raise AssertionError("чтение очереди сняло задачу через blpop")


class _FakeQueuePipeline:
    """Конвейер поверх двойника: команды копятся, `execute` выполняет по порядку."""

    def __init__(self, client: "_FakeQueueRedis"):
        self._client = client
        self._ops: list = []

    def llen(self, key: str):
        self._ops.append(("llen", (key,)))
        return self

    def lrange(self, key: str, start: int, stop: int):
        self._ops.append(("lrange", (key, start, stop)))
        return self

    def get(self, key: str):
        self._ops.append(("get", (key,)))
        return self

    async def execute(self):
        out = []
        for name, args in self._ops:
            out.append(await getattr(self._client, name)(*args))
        return out


def _task_body(task_id: str, **extra) -> bytes:
    """Тело задачи в том же виде, в каком его кладёт постановщик — байтами."""
    import json

    body = {
        "task_id": task_id,
        "ad_id": 11,
        "group_id": 22,
        "account_id": 33,
        "schedule_id": 44,
        "user_id": 55,
        "ad_text": "Текст объявления",
        "ad_title": "Заголовок",
        "ad_images": [],
        "group_external_id": "-100123456789",
        "group_name": "Группа «Барахолка»",
        "created_at": "2026-08-22T10:00:00+00:00",
    }
    body.update(extra)
    return json.dumps(body, ensure_ascii=False).encode()


@pytest.mark.asyncio
async def test_reading_a_queue_page_does_not_shorten_the_queue():
    """Чтение отдаёт тела задач и НЕ уменьшает длину списка.

    Длина до и после совпадает: подраздел отвечает на вопрос «что ждёт
    отправки», а не забирает ответ себе.
    """
    from app.services.ops_state import queue_page

    client = _FakeQueueRedis({"wa:queue:7": [_task_body("a"), _task_body("b")]})

    with patch("app.services.ops_state._get_redis", return_value=client):
        page = await queue_page("wa", 7, limit=50)

    assert [task["task_id"] for task in page.tasks] == ["a", "b"]
    assert page.total == 2
    assert page.unavailable is False
    assert len(client.lists["wa:queue:7"]) == 2
    assert client.forbidden_calls == []


@pytest.mark.asyncio
async def test_reading_an_empty_queue_returns_an_empty_page_without_raising():
    """Пустая очередь — пустой перечень и НЕ исключение."""
    from app.services.ops_state import queue_page

    client = _FakeQueueRedis({})

    with patch("app.services.ops_state._get_redis", return_value=client):
        page = await queue_page("max", 9, limit=50)

    assert page.tasks == ()
    assert page.total == 0
    assert page.unavailable is False


@pytest.mark.asyncio
async def test_an_unreachable_redis_is_named_and_not_shown_as_an_empty_queue():
    """Недоступный Redis возвращает признак недоступности, а не пустоту.

    Пустая очередь и сломанный наблюдатель — РАЗНЫЕ состояния мира. Слитые в
    одно, они сообщили бы «рассылать нечего» ровно тогда, когда очередь стоит и
    её не видно.
    """
    from app.services.ops_state import queue_page

    with patch("app.services.ops_state._get_redis", return_value=None):
        page = await queue_page("wa", 7, limit=50)
    assert page.tasks == ()
    assert page.total is None
    assert page.unavailable is True

    broken = MagicMock()
    broken.llen = MagicMock(return_value=broken)
    broken.lrange = MagicMock(return_value=broken)
    broken.execute = AsyncMock(side_effect=OSError("connection reset"))
    client = MagicMock()
    client.pipeline = MagicMock(return_value=broken)
    with patch("app.services.ops_state._get_redis", return_value=client):
        page = await queue_page("wa", 7, limit=50)
    assert page.unavailable is True


@pytest.mark.asyncio
async def test_dropping_a_task_removes_exactly_one_entry_with_an_explicit_count():
    """Снятие удаляет РОВНО ОДНУ запись, и количество передано явным литералом.

    Два одинаковых тела в очереди — и одно обязано остаться. Количество не
    выводится из того, что идентификаторы уникальны: правило «снять одну»
    обязано быть выражено, а не выведено из свойства данных, которое завтра
    может перестать выполняться.
    """
    from app.services.ops_state import DROP_REMOVED, drop_task

    body = _task_body("dup")
    client = _FakeQueueRedis({"wa:queue:7": [body, body, _task_body("other")]})

    with patch("app.services.ops_state._get_redis", return_value=client):
        outcome = await drop_task("wa", 7, "dup", limit=50)

    assert outcome == DROP_REMOVED
    assert client.lists["wa:queue:7"].count(body) == 1
    assert len(client.lists["wa:queue:7"]) == 2
    assert [call[1] for call in client.lrem_calls] == [1]


@pytest.mark.asyncio
async def test_dropping_a_task_that_is_already_gone_removes_nothing_and_says_so():
    """Снятие несуществующей задачи ничего не удаляет и НАЗЫВАЕТ этот исход.

    Молчаливый успех был бы хуже отказа: администратор решил бы, что снял
    отправку, которая на самом деле уже ушла к получателю.
    """
    from app.services.ops_state import DROP_MISSING, drop_task

    client = _FakeQueueRedis({"wa:queue:7": [_task_body("a")]})

    with patch("app.services.ops_state._get_redis", return_value=client):
        outcome = await drop_task("wa", 7, "no-such-task", limit=50)

    assert outcome == DROP_MISSING
    assert client.lrem_calls == []
    assert len(client.lists["wa:queue:7"]) == 1


@pytest.mark.asyncio
async def test_the_dropped_bytes_come_from_the_servers_own_read_not_from_the_form():
    """Точные байты удаляемого берутся из СВОЕГО чтения очереди (T-06-DROP2).

    Форма присылает только идентификатор задачи. Тело в этих очередях содержит
    текст чужого объявления и может быть большим; доверять клиенту точные байты
    удаляемого не нужно вовсе, и подделать снятие чужой задачи подстановкой тела
    нельзя, потому что тело из запроса не используется ничем.
    """
    from app.services.ops_state import DROP_REMOVED, drop_task

    stored = _task_body("target", _retry_count=2)
    client = _FakeQueueRedis({"max:queue:3": [stored]})

    with patch("app.services.ops_state._get_redis", return_value=client):
        outcome = await drop_task("max", 3, "target", limit=50)

    assert outcome == DROP_REMOVED
    assert client.lrem_calls[0][2] == stored
    assert client.lists["max:queue:3"] == []


@pytest.mark.asyncio
async def test_the_telegram_queue_is_measured_by_length_without_opening_its_envelope():
    """Длина очереди telegram читается по ИМЕНИ очереди, без разбора содержимого.

    Тело задачи там — конверт брокера с закодированным содержимым (D-14). Его
    разбор привязал бы админку к внутренностям библиотеки, которые меняются
    между версиями молча.
    """
    from app.services.ops_state import TELEGRAM_QUEUE_KEY, telegram_queue_depth

    client = _FakeQueueRedis({TELEGRAM_QUEUE_KEY: [b"opaque-1", b"opaque-2"]})

    with patch("app.services.ops_state._get_redis", return_value=client):
        depth = await telegram_queue_depth()
    assert depth == 2

    with patch("app.services.ops_state._get_redis", return_value=None):
        assert await telegram_queue_depth() is None


def test_no_dispatch_call_in_the_project_passes_a_priority():
    """СТРАХОВОЧНАЯ СЕТКА: постановка задач нигде не передаёт приоритет (Ф-13).

    ⚠️ ЭТОТ ТЕСТ ОБЯЗАН ПОКРАСНЕТЬ В ТОТ ДЕНЬ, КОГДА ПРИОРИТЕТ ПОЯВИТСЯ, А НЕ
    ЧЕРЕЗ МЕСЯЦ. Брокер хранит очередь Redis-списком, но при НЕНУЛЕВОМ
    приоритете — в отдельном ключе с суффиксом (`_q_for_pri`,
    kombu/transport/redis.py:1024-1028). Сегодня приоритет не передаётся нигде,
    и именно поэтому длина ключа `telegram` есть ПОЛНОЕ число задач канала. В
    день, когда он появится, задачи разъедутся по ключам с суффиксами, и
    подраздел начнёт недосчитывать МОЛЧА: числу нечем будет себя опровергнуть.

    Обход идёт по синтаксическому дереву, а не поиском подстроки: слово
    `priority` в комментарии или в чужом вызове красило бы тест, ничего не
    сообщая.
    """
    import ast
    from pathlib import Path

    offenders: list[str] = []
    for source in sorted(Path("app").rglob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else None
            if name not in {"apply_async", "delay", "send_task"}:
                continue
            for keyword in node.keywords:
                if keyword.arg == "priority":
                    offenders.append(f"{source}:{node.lineno}")

    assert offenders == [], (
        "постановка задачи передаёт приоритет: длина ключа `telegram` больше не "
        f"есть полное число задач канала — {offenders}"
    )


def test_the_heartbeat_invariant_is_derived_and_not_asserted_at_import(
    celery_app_module,
):
    """Инвариант двух констант ВЫВЕДЕН, а не проверен `assert`-ом на импорте.

    ⚠️ `assert` НА УРОВНЕ МОДУЛЯ ПЛОХ В ОБЕ СТОРОНЫ СРАЗУ (WR-06 ревизии фазы 6).
    Под ключом `-O` он снимается целиком — то есть отсутствует ровно там, где
    числа и разъедутся незамеченными. А сработай он — `AssertionError` на
    импорте кладёт КАЖДЫЙ процесс, читающий модуль: всех воркеров, `celery-beat`
    и всё, что их импортирует. Несовпадение двух констант становится полной
    остановкой пути отправки, то есть худшим из возможных исходов проверки,
    заведённой ради надёжности.

    Утверждение читает ДЕРЕВО исходника: поиск строки считал бы `assert` и в
    объяснении, почему его здесь нет.
    """
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(celery_app_module))

    module_level_asserts = [
        node for node in tree.body if isinstance(node, ast.Assert)
    ]

    assert not module_level_asserts, (
        "на уровне модуля стоит `assert`: под `-O` он исчезает, а сработав — "
        "роняет импорт у всех воркеров и beat разом. Инвариант обязан быть "
        "ВЫВЕДЕН из одного источника, а не сверен с ним"
    )


def test_unreadable_queues_are_named_in_the_journal_not_swallowed(
    celery_app_module,
):
    """Непрочитанный перечень очередей оставляет ИМЕНОВАННУЮ запись (WR-09).

    ⚠️ ЦЕНА МОЛЧАНИЯ ЗДЕСЬ ВЫШЕ, ЧЕМ ВЫГЛЯДИТ. Сорвись чтение на
    telegram-воркере — перечень остаётся пустым, роль сваливается в умолчание, и
    процесс пишет ЧУЖОЙ ключ. Подраздел «Воркеры» показывает после этого
    Telegram вечно отключённым И default живым дважды: ложная тревога и ложное
    «всё в порядке» из одного проглоченного исключения, на блоке, который
    администратор открывает во время аварии. Проглоченное, оно не оставляло ни
    одной строки, по которой это можно было бы установить.

    Поток признака живости здесь подменён: предмет утверждения — запись о
    непрочитанной роли, а не подъём фонового потока с обращением к Redis.
    """
    from unittest.mock import MagicMock, patch

    class _SenderWithoutQueues:
        @property
        def app(self):
            raise RuntimeError("очереди ещё не выбраны")

    logger = MagicMock()

    with patch.object(
        celery_app_module, "_start_infra_heartbeat"
    ) as started, patch(
        "structlog.get_logger", return_value=logger
    ):
        celery_app_module.start_worker_infra_heartbeat(
            sender=_SenderWithoutQueues()
        )

    events = [call.args[0] for call in logger.warning.call_args_list if call.args]
    assert "infra_heartbeat_queues_unreadable" in events, (
        f"непрочитанные очереди проглочены молча: {events} — роль воркера "
        "выбрана не по измерению, и установить это нечем"
    )
    assert started.called, (
        "признак живости не поднят вовсе — процесс стал невидим в подразделе "
        "целиком, а это хуже, чем неверная роль"
    )


def test_readable_queues_leave_no_such_line_and_pick_the_measured_role(
    celery_app_module,
):
    """ГРАНИЦА СВЕРХУ: при читаемых очередях записи нет, а роль — измеренная.

    Без этого утверждения запись, выставляемая ВСЕГДА, прошла бы тест выше и
    объявляла бы роль неизмеренной на каждом исправном запуске.
    """
    from unittest.mock import MagicMock, patch

    from app.services.ops_state import INFRA_WORKER_TELEGRAM

    sender = MagicMock()
    sender.app.amqp.queues.keys.return_value = ["telegram"]
    logger = MagicMock()

    with patch.object(
        celery_app_module, "_start_infra_heartbeat"
    ) as started, patch(
        "structlog.get_logger", return_value=logger
    ):
        celery_app_module.start_worker_infra_heartbeat(sender=sender)

    events = [call.args[0] for call in logger.warning.call_args_list if call.args]
    assert "infra_heartbeat_queues_unreadable" not in events, (
        "исправный запуск объявлен непрочитанным — запись выставляется всегда "
        "и потому ничего не сообщает"
    )
    started.assert_called_once_with(INFRA_WORKER_TELEGRAM)

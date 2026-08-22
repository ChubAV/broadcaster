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

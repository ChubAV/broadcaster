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

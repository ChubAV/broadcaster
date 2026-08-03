from unittest.mock import MagicMock, patch

import pytest
from docker.errors import NotFound

from app.services import max_container_manager as manager


def running_container():
    container = MagicMock()
    container.status = "running"
    return container


@patch("app.services.max_container_manager.time.time", return_value=1_000.0)
@patch("app.services.max_container_manager._get_docker_client")
def test_fresh_heartbeat_reuses_running_container(mock_docker, _mock_time):
    client = MagicMock()
    client.containers.get.return_value = running_container()
    mock_docker.return_value = client
    redis = MagicMock(get=MagicMock(return_value="970000"))

    with patch.object(manager, "start_container") as start, patch.object(manager, "stop_container") as stop:
        endpoint = manager.ensure_container_for_pending_work(7, redis)

    assert endpoint == "http://max-worker-7:3000"
    start.assert_not_called()
    stop.assert_not_called()


@pytest.mark.parametrize("heartbeat", [None, "not-a-timestamp", "909999", "1000001"])
@patch("app.services.max_container_manager.time.time", return_value=1_000.0)
@patch("app.services.max_container_manager._get_docker_client")
def test_unhealthy_heartbeat_stops_running_container_before_replacement(
    mock_docker, _mock_time, heartbeat
):
    client = MagicMock()
    client.containers.get.return_value = running_container()
    mock_docker.return_value = client
    redis = MagicMock(get=MagicMock(return_value=heartbeat))
    calls = []

    with patch.object(manager, "stop_container", side_effect=lambda _: calls.append("stop") or True), patch.object(
        manager, "start_container", side_effect=lambda _: calls.append("start") or "http://replacement:3000"
    ):
        endpoint = manager.ensure_container_for_pending_work(7, redis)

    assert endpoint == "http://replacement:3000"
    assert calls == ["stop", "start"]


@patch("app.services.max_container_manager._get_docker_client")
def test_failed_stop_does_not_start_replacement(mock_docker):
    client = MagicMock()
    client.containers.get.return_value = running_container()
    mock_docker.return_value = client
    redis = MagicMock(get=MagicMock(return_value=None))

    with patch.object(manager, "stop_container", return_value=False), patch.object(manager, "start_container") as start:
        endpoint = manager.ensure_container_for_pending_work(7, redis)

    assert endpoint is None
    start.assert_not_called()


@patch("app.services.max_container_manager._get_docker_client")
def test_stopped_or_missing_container_uses_existing_start_path(mock_docker):
    client = MagicMock()
    stopped = running_container()
    stopped.status = "exited"
    client.containers.get.side_effect = [stopped, NotFound("missing")]
    mock_docker.return_value = client
    redis = MagicMock()

    with patch.object(manager, "start_container", return_value="http://replacement:3000") as start:
        assert manager.ensure_container_for_pending_work(7, redis) == "http://replacement:3000"
        assert manager.ensure_container_for_pending_work(7, redis) == "http://replacement:3000"

    assert start.call_args_list == [((7,), {}), ((7,), {})]

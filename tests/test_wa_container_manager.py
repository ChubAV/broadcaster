from unittest.mock import MagicMock, patch

import pytest
from docker.errors import APIError, NotFound

from app.services.wa_container_manager import (
    cleanup_exited_containers,
    get_container_endpoint,
    get_container_name,
    list_worker_containers,
    start_container,
    stop_container,
)


def test_get_container_name():
    assert get_container_name(123) == "wa-worker-123"
    assert get_container_name(1) == "wa-worker-1"


@patch("app.services.wa_container_manager.get_settings")
@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_new(mock_docker, mock_settings):
    """Start a new container when none exists."""
    mock_settings.return_value = MagicMock(redis_url="redis://localhost:6379/0")
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = NotFound("not found")

    container = MagicMock()
    container.short_id = "abc123"
    client.containers.run.return_value = container

    result = start_container(123)
    assert result == "http://wa-worker-123:3000"
    client.containers.run.assert_called_once()
    call_kwargs = client.containers.run.call_args
    assert call_kwargs.kwargs["name"] == "wa-worker-123"
    assert call_kwargs.kwargs["environment"]["ACCOUNT_ID"] == "123"


@patch("app.services.wa_container_manager.get_settings")
@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_already_running(mock_docker, mock_settings):
    """Return existing endpoint when container already running."""
    mock_settings.return_value = MagicMock(redis_url="redis://localhost:6379/0")
    client = MagicMock()
    mock_docker.return_value = client
    existing = MagicMock()
    existing.status = "running"
    client.containers.get.return_value = existing

    result = start_container(123)
    assert result == "http://wa-worker-123:3000"
    client.containers.run.assert_not_called()


@patch("app.services.wa_container_manager.get_settings")
@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_replace_stopped(mock_docker, mock_settings):
    """Remove stopped container and start new one."""
    mock_settings.return_value = MagicMock(redis_url="redis://localhost:6379/0")
    client = MagicMock()
    mock_docker.return_value = client
    existing = MagicMock()
    existing.status = "exited"
    client.containers.get.return_value = existing

    container = MagicMock()
    container.short_id = "def456"
    client.containers.run.return_value = container

    result = start_container(123)
    existing.remove.assert_called_once_with(force=True)
    client.containers.run.assert_called_once()
    assert result == "http://wa-worker-123:3000"


@patch("app.services.wa_container_manager.get_settings")
@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_api_error(mock_docker, mock_settings):
    """Return None on Docker API error."""
    mock_settings.return_value = MagicMock(redis_url="redis://localhost:6379/0")
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = NotFound("not found")
    client.containers.run.side_effect = APIError("failed")

    result = start_container(123)
    assert result is None


@patch("app.services.wa_container_manager._get_docker_client")
def test_stop_container(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    container = MagicMock()
    client.containers.get.return_value = container

    result = stop_container(123)
    assert result is True
    container.stop.assert_called_once_with(timeout=10)
    container.remove.assert_called_once()


@patch("app.services.wa_container_manager._get_docker_client")
def test_stop_container_not_found(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = NotFound("not found")

    result = stop_container(123)
    assert result is True


@patch("app.services.wa_container_manager._get_docker_client")
def test_stop_container_api_error(mock_docker):
    """Return False on Docker API error during stop."""
    client = MagicMock()
    mock_docker.return_value = client
    container = MagicMock()
    client.containers.get.return_value = container
    container.stop.side_effect = APIError("failed")

    result = stop_container(123)
    assert result is False


@patch("app.services.wa_container_manager._get_docker_client")
def test_list_worker_containers(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client

    c1 = MagicMock()
    c1.labels = {"broadcaster.account_id": "1"}
    c1.name = "wa-worker-1"
    c1.status = "running"
    c1.short_id = "abc"

    c2 = MagicMock()
    c2.labels = {"broadcaster.account_id": "2"}
    c2.name = "wa-worker-2"
    c2.status = "exited"
    c2.short_id = "def"

    client.containers.list.return_value = [c1, c2]

    result = list_worker_containers()
    assert len(result) == 2
    assert result[0]["account_id"] == 1
    assert result[0]["status"] == "running"
    assert result[1]["account_id"] == 2
    assert result[1]["status"] == "exited"


@patch("app.services.wa_container_manager._get_docker_client")
def test_cleanup_exited_containers(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client

    c1 = MagicMock(name="wa-worker-1")
    c2 = MagicMock(name="wa-worker-2")
    client.containers.list.return_value = [c1, c2]

    cleanup_exited_containers()
    c1.remove.assert_called_once()
    c2.remove.assert_called_once()
    client.containers.list.assert_called_once_with(
        all=True,
        filters={"label": "broadcaster.role=wa-worker", "status": "exited"},
    )


@patch("app.services.wa_container_manager._get_docker_client")
def test_get_container_endpoint_running(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    container = MagicMock()
    container.status = "running"
    client.containers.get.return_value = container

    result = get_container_endpoint(123)
    assert result == "http://wa-worker-123:3000"


@patch("app.services.wa_container_manager._get_docker_client")
def test_get_container_endpoint_not_running(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    container = MagicMock()
    container.status = "exited"
    client.containers.get.return_value = container

    result = get_container_endpoint(123)
    assert result is None


@patch("app.services.wa_container_manager._get_docker_client")
def test_get_container_endpoint_not_found(mock_docker):
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = NotFound("not found")

    result = get_container_endpoint(123)
    assert result is None

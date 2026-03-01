import time

import httpx
import structlog
import docker
from docker.errors import NotFound, APIError

from app.config import get_settings

logger = structlog.get_logger()

# Container config constants
MAX_WORKER_IMAGE = "broadcaster-max-worker:latest"
CONTAINER_PREFIX = "max-worker-"
CONTAINER_LABEL = "broadcaster.role=max-worker"
NETWORK_NAME = "broadcaster"
SESSIONS_VOLUME = "broadcaster_max_sessions"
MEMORY_LIMIT = "256m"
DEFAULT_PORT = 3000


def _get_docker_client():
    return docker.from_env()


def get_container_name(account_id: int) -> str:
    return f"{CONTAINER_PREFIX}{account_id}"


def start_container(account_id: int, phone: str = "") -> str | None:
    """Start a max-worker container for the given account.
    Returns the container endpoint URL or None on failure."""
    settings = get_settings()
    client = _get_docker_client()
    name = get_container_name(account_id)

    # Check if container already exists
    try:
        existing = client.containers.get(name)
        if existing.status == "running":
            logger.info("container_already_running", account_id=account_id)
            return _container_endpoint(name)
        # Exists but stopped — remove and recreate
        existing.remove(force=True)
        logger.info("removed_stopped_container", account_id=account_id)
    except NotFound:
        pass

    try:
        environment = {
            "ACCOUNT_ID": str(account_id),
            "REDIS_URL": settings.redis_url,
            "RATE_LIMIT_PER_MINUTE": "8",
            "PORT": str(DEFAULT_PORT),
            "LOG_LEVEL": "info",
        }
        if phone:
            environment["PHONE"] = phone

        container = client.containers.run(
            image=MAX_WORKER_IMAGE,
            name=name,
            detach=True,
            environment=environment,
            volumes={
                SESSIONS_VOLUME: {"bind": "/app/sessions", "mode": "rw"},
            },
            network=NETWORK_NAME,
            mem_limit=MEMORY_LIMIT,
            restart_policy={"Name": "unless-stopped"},
            labels={
                "broadcaster.role": "max-worker",
                "broadcaster.account_id": str(account_id),
            },
            hostname=name,
            log_config=docker.types.LogConfig(
                type="json-file",
                config={"max-size": "10m", "max-file": "3"},
            ),
        )
        logger.info("container_started", account_id=account_id, container_id=container.short_id)
        return _container_endpoint(name)
    except APIError as e:
        logger.error("container_start_failed", account_id=account_id, error=str(e))
        return None


def stop_container(account_id: int) -> bool:
    """Stop and remove a max-worker container."""
    client = _get_docker_client()
    name = get_container_name(account_id)

    try:
        container = client.containers.get(name)
        container.stop(timeout=10)
        container.remove()
        logger.info("container_stopped", account_id=account_id)
        return True
    except NotFound:
        return True
    except APIError as e:
        logger.error("container_stop_failed", account_id=account_id, error=str(e))
        return False


def list_worker_containers() -> list[dict]:
    """List all max-worker containers with their status."""
    client = _get_docker_client()
    containers = client.containers.list(all=True, filters={"label": CONTAINER_LABEL})
    result = []
    for c in containers:
        account_id = c.labels.get("broadcaster.account_id")
        result.append({
            "account_id": int(account_id) if account_id else None,
            "name": c.name,
            "status": c.status,
            "short_id": c.short_id,
        })
    return result


def cleanup_exited_containers():
    """Remove all exited max-worker containers."""
    client = _get_docker_client()
    containers = client.containers.list(
        all=True,
        filters={"label": CONTAINER_LABEL, "status": "exited"},
    )
    for c in containers:
        try:
            c.remove()
            logger.info("cleaned_exited_container", name=c.name)
        except APIError as e:
            logger.warn("cleanup_failed", name=c.name, error=str(e))


def get_container_endpoint(account_id: int) -> str | None:
    """Get the HTTP endpoint for a running max-worker container."""
    client = _get_docker_client()
    name = get_container_name(account_id)
    try:
        container = client.containers.get(name)
        if container.status == "running":
            return _container_endpoint(name)
        return None
    except NotFound:
        return None


def _container_endpoint(container_name: str) -> str:
    return f"http://{container_name}:{DEFAULT_PORT}"


def wait_for_container_ready(
    account_id: int,
    *,
    timeout: float = 30.0,
    interval: float = 1.0,
) -> bool:
    """Poll container /health endpoint until it responds or timeout."""
    endpoint = _container_endpoint(get_container_name(account_id))
    url = f"{endpoint}/health"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=3.0)
            if resp.status_code == 200:
                logger.info("container_ready", account_id=account_id)
                return True
        except httpx.ConnectError:
            pass
        except Exception as e:
            logger.debug("container_health_check_failed", account_id=account_id, error=str(e))
        time.sleep(interval)

    logger.warning("container_ready_timeout", account_id=account_id, timeout=timeout)
    return False

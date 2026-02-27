import asyncio

import httpx
import structlog
import structlog.contextvars

from app.messengers.base import BaseMessenger

logger = structlog.get_logger(__name__)


def get_wa_endpoint(account_id: int) -> str | None:
    """Get the HTTP endpoint for a wa-worker container from Redis."""
    import redis as redis_lib
    from app.config import get_settings
    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)
    try:
        endpoint = r.get(f"wa:endpoint:{account_id}")
        return endpoint.decode() if endpoint else None
    finally:
        r.close()


def ensure_wa_container(account_id: int) -> str | None:
    """Start wa-worker container if not running, return endpoint."""
    from app.services.wa_container_manager import start_container
    endpoint = get_wa_endpoint(account_id)
    if endpoint:
        return endpoint
    return start_container(account_id)


# Module-level shared HTTP client (created lazily, recreated on event loop change)
_http_client: httpx.AsyncClient | None = None
_http_client_loop: asyncio.AbstractEventLoop | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create shared httpx client with connection pooling.

    Recreates the client when the event loop changes (e.g. between
    asyncio.run() calls in Celery worker retries).
    """
    global _http_client, _http_client_loop
    current_loop = asyncio.get_running_loop()
    if _http_client is None or _http_client.is_closed or _http_client_loop is not current_loop:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        _http_client_loop = current_loop
    return _http_client


class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str | None = None, session_id: str = ""):
        self.session_id = session_id
        self._bridge_url = bridge_url.rstrip("/") if bridge_url else None
        self.log = logger.bind(messenger="whatsapp", session_id=session_id)

    @property
    def bridge_url(self) -> str:
        if self._bridge_url:
            return self._bridge_url
        endpoint = ensure_wa_container(int(self.session_id))
        if not endpoint:
            raise RuntimeError(f"Cannot start wa-worker for account {self.session_id}")
        return endpoint.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.bridge_url}/api/sessions/{self.session_id}/{path}"

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        client = get_http_client()
        try:
            payload = {"group_id": group_id, "text": text}
            if images:
                payload["image_urls"] = images
            trace_id = structlog.contextvars.get_contextvars().get("task_id")
            if trace_id:
                payload["trace_id"] = trace_id
            response = await client.post(self._url("send"), json=payload)
            if response.status_code != 200:
                error_msg = ""
                try:
                    body = response.json()
                    error_msg = body.get("error", "")
                except Exception:
                    error_msg = response.text
                error = f"[HTTP {response.status_code}] {error_msg}" if error_msg else f"[HTTP {response.status_code}] empty response"
                self.log.error("send_message_error", group_id=group_id, http_status=response.status_code, error=error)
                # 403 forbidden (kicked/banned) — no point retrying
                if response.status_code == 403:
                    return {"ok": False, "error": error, "no_retry": True}
                return {"ok": False, "error": error}
            self.log.debug("send_message_ok", group_id=group_id)
            return {"ok": True}
        except Exception as e:
            error = f"[Connection] {type(e).__name__}: {e}"
            self.log.error("send_message_error", group_id=group_id, error=error, exc_info=True)
            return {"ok": False, "error": error}

    async def get_groups(self) -> list[dict]:
        client = get_http_client()
        try:
            response = await client.get(self._url("groups"), timeout=600.0)
            if response.status_code == 200:
                return response.json()
            self.log.error("get_groups_error", http_status=response.status_code)
            return []
        except Exception as e:
            self.log.error("get_groups_error", error=str(e), exc_info=True)
            return []

    async def check_connection(self) -> bool:
        client = get_http_client()
        try:
            response = await client.get(self._url("status"))
            return response.status_code == 200 and response.json().get("connected", False)
        except Exception as e:
            self.log.warning("check_connection_failed", error=str(e))
            return False

    async def get_sync_status(self) -> dict:
        """Get group sync status from bridge.
        Returns: {"state": "syncing"|"ready"|"failed"|"none"|"not_found", "groups": [...] | None}
        """
        client = get_http_client()
        try:
            response = await client.get(self._url("sync-status"))
            if response.status_code == 200:
                return response.json()
            self.log.warning("get_sync_status_error", http_status=response.status_code)
            return {"state": "error", "groups": None}
        except Exception as e:
            self.log.error("get_sync_status_error", error=str(e), exc_info=True)
            return {"state": "error", "groups": None}

    async def retry_sync(self) -> dict:
        """Trigger retry of failed group sync."""
        client = get_http_client()
        try:
            response = await client.post(self._url("retry-sync"), json={})
            if response.status_code == 200:
                return response.json()
            return {"status": "error"}
        except Exception as e:
            self.log.error("retry_sync_error", error=str(e), exc_info=True)
            return {"status": "error"}

    async def start_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.post(self._url("start"), json={}, timeout=30)
            if response.status_code == 200:
                return True
            self.log.warning("start_session_error", http_status=response.status_code)
            return False
        except Exception as e:
            self.log.error("start_session_error", error=str(e), exc_info=True)
            return False

    async def destroy_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.delete(
                f"{self.bridge_url}/api/sessions/{self.session_id}"
            )
            return response.status_code == 200
        except Exception as e:
            self.log.error("destroy_session_error", error=str(e), exc_info=True)
            return False

    async def get_qr(self) -> dict:
        client = get_http_client()
        try:
            response = await client.get(self._url("qr"))
            if response.status_code == 200:
                return response.json()
            self.log.warning("get_qr_error", http_status=response.status_code)
            return {"status": "error", "qr": None}
        except Exception as e:
            self.log.error("get_qr_error", error=str(e), exc_info=True)
            return {"status": "error", "qr": None}

import httpx

from app.messengers.base import BaseMessenger


def get_bridge_url(session_id: int, bridge_urls: list[str]) -> str:
    """Consistent routing: same session always goes to same bridge."""
    return bridge_urls[session_id % len(bridge_urls)]


# Module-level shared HTTP client (created lazily)
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create shared httpx client with connection pooling."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _http_client


class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str, session_id: str):
        self.bridge_url = bridge_url.rstrip("/")
        self.session_id = session_id

    def _url(self, path: str) -> str:
        return f"{self.bridge_url}/api/sessions/{self.session_id}/{path}"

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        client = get_http_client()
        try:
            payload = {"group_id": group_id, "text": text}
            if images:
                payload["image_urls"] = images
            response = await client.post(self._url("send"), json=payload)
            if response.status_code != 200:
                return {"ok": False, "error": response.text}
            return {"ok": True}
        except httpx.HTTPError as e:
            return {"ok": False, "error": str(e)}

    async def get_groups(self) -> list[dict]:
        client = get_http_client()
        try:
            response = await client.get(self._url("groups"))
            if response.status_code == 200:
                return response.json()
            return []
        except httpx.HTTPError:
            return []

    async def check_connection(self) -> bool:
        client = get_http_client()
        try:
            response = await client.get(self._url("status"))
            return response.status_code == 200 and response.json().get("connected", False)
        except Exception:
            return False

    async def start_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.post(self._url("start"), timeout=30)
            return response.status_code == 200
        except Exception:
            return False

    async def destroy_session(self) -> bool:
        client = get_http_client()
        try:
            response = await client.delete(
                f"{self.bridge_url}/api/sessions/{self.session_id}"
            )
            return response.status_code == 200
        except Exception:
            return False

    async def get_qr(self) -> dict:
        client = get_http_client()
        try:
            response = await client.get(self._url("qr"))
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "qr": None}
        except Exception:
            return {"status": "error", "qr": None}

import httpx

from app.messengers.base import BaseMessenger


class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str, session_id: str):
        self.bridge_url = bridge_url.rstrip("/")
        self.session_id = session_id

    def _url(self, path: str) -> str:
        return f"{self.bridge_url}/api/sessions/{self.session_id}/{path}"

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            if images and len(images) > 1:
                # Send all images except the last one without caption
                payload = {
                    "group_id": group_id,
                    "text": "",
                    "image_paths": images[:-1],
                }
                response = await client.post(self._url("send"), json=payload)
                if response.status_code != 200:
                    return {"ok": False, "error": response.text}
                # Send the last image with caption
                payload = {
                    "group_id": group_id,
                    "text": text,
                    "image_paths": [images[-1]],
                }
                response = await client.post(self._url("send"), json=payload)
                if response.status_code != 200:
                    return {"ok": False, "error": response.text}
            elif images:
                payload = {
                    "group_id": group_id,
                    "text": text,
                    "image_paths": images,
                }
                response = await client.post(self._url("send"), json=payload)
                if response.status_code != 200:
                    return {"ok": False, "error": response.text}
            else:
                payload = {"group_id": group_id, "text": text}
                response = await client.post(self._url("send"), json=payload)
                if response.status_code != 200:
                    return {"ok": False, "error": response.text}
            return {"ok": True}

    async def get_groups(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self._url("groups"))
            if response.status_code == 200:
                return response.json()
            return []

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._url("status"))
                return response.status_code == 200 and response.json().get("connected", False)
        except Exception:
            return False

    async def start_session(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self._url("start"))
                return response.status_code == 200
        except Exception:
            return False

    async def destroy_session(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.bridge_url}/api/sessions/{self.session_id}"
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_qr(self) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._url("qr"))
                if response.status_code == 200:
                    return response.json()
                return {"status": "error", "qr": None}
        except Exception:
            return {"status": "error", "qr": None}

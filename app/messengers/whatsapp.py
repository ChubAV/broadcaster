import httpx

from app.messengers.base import BaseMessenger


class WhatsAppMessenger(BaseMessenger):
    def __init__(self, bridge_url: str):
        self.bridge_url = bridge_url.rstrip("/")

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            payload = {"group_id": group_id, "text": text}
            if images:
                payload["image_path"] = images[0]
            response = await client.post(f"{self.bridge_url}/api/send", json=payload)
            if response.status_code == 200:
                return {"ok": True}
            return {"ok": False, "error": response.text}

    async def get_groups(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.bridge_url}/api/groups")
            if response.status_code == 200:
                return response.json()
            return []

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.bridge_url}/api/status")
                return response.status_code == 200 and response.json().get("connected", False)
        except Exception:
            return False

from pyrogram import Client

from app.messengers.base import BaseMessenger


class TelegramUserMessenger(BaseMessenger):
    def __init__(self, session_string: str, api_id: int, api_hash: str):
        self.client = Client(
            name="broadcaster_user",
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            in_memory=True,
        )

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        try:
            async with self.client:
                if images:
                    await self.client.send_photo(chat_id=int(group_id), photo=images[0], caption=text)
                else:
                    await self.client.send_message(chat_id=int(group_id), text=text)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_groups(self) -> list[dict]:
        groups = []
        try:
            async with self.client:
                async for dialog in self.client.get_dialogs():
                    if dialog.chat.type in ("group", "supergroup"):
                        groups.append({"id": str(dialog.chat.id), "name": dialog.chat.title})
        except Exception:
            pass
        return groups

    async def check_connection(self) -> bool:
        try:
            async with self.client:
                await self.client.get_me()
            return True
        except Exception:
            return False

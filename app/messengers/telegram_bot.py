from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto

from app.messengers.base import BaseMessenger


class TelegramBotMessenger(BaseMessenger):
    def __init__(self, token: str):
        self.bot = Bot(token=token)

    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        try:
            if images and len(images) == 1:
                photo = FSInputFile(images[0])
                await self.bot.send_photo(chat_id=group_id, photo=photo, caption=text)
            elif images:
                media = [
                    InputMediaPhoto(
                        media=FSInputFile(img),
                        caption=text if i == 0 else None,
                    )
                    for i, img in enumerate(images)
                ]
                await self.bot.send_media_group(chat_id=group_id, media=media)
            else:
                await self.bot.send_message(chat_id=group_id, text=text)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_groups(self) -> list[dict]:
        # Bot API doesn't have a "list groups" method
        # Groups are discovered when bot is added to them
        # Return empty list — groups are managed through the web UI
        return []

    async def check_connection(self) -> bool:
        try:
            await self.bot.get_me()
            return True
        except Exception:
            return False

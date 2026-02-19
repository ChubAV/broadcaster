from abc import ABC, abstractmethod


class BaseMessenger(ABC):
    @abstractmethod
    async def send_message(self, group_id: str, text: str, images: list[str] | None = None) -> dict:
        """Send message to group. Returns {"ok": True} or {"ok": False, "error": "..."}"""
        pass

    @abstractmethod
    async def get_groups(self) -> list[dict]:
        """Returns list of groups: [{"id": "...", "name": "..."}]"""
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """Check if account is connected and working."""
        pass

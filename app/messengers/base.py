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

    async def get_group_details(self, group_external_id: str) -> dict | None:
        """Get detailed info about a group. Returns dict with name, member_count, admins, raw or None."""
        return None

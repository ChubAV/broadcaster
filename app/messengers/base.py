from abc import ABC, abstractmethod


class MessengerFetchError(RuntimeError):
    """Мессенджер не отдал состав групп — это НЕ пустой список.

    Заведено, потому что пустой список от отказа отличить было невозможно: все
    три реализации `get_groups()` глушили исключение и возвращали `[]`, а с
    переходом на полную переинвентаризацию (D-10) вызывающий трактует `[]` как
    авторитетное «групп больше нет» и помечает `missing_since` у ВСЕХ групп
    аккаунта, записав при этом сводку успеха. Отказ обязан быть отличим от
    пустоты на границе адаптера — выше по стеку различить их уже нечем.
    """


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

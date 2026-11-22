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


def reported_phone_from_status(body: object) -> str | None:
    """Номер из тела `/status` воркера: строка как есть или `None` (D-14, D-05).

    Тело ответа воркера — недоверенный JSON. Поле `phone` — строка цифр E.164
    без `+` либо `null`; у образа воркера старой формы поля нет вовсе. Принимается
    только словарь, а в нём непустая строка (возвращается как есть) или целое
    больше нуля (возвращается строкой, `bool` целым не считается); всё прочее —
    «неизвестен». Окончательную нормализацию делает `normalize_reported`
    единственного писателя номера, не эта функция.
    """
    if not isinstance(body, dict):
        return None
    value = body.get("phone")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value) if value > 0 else None
    if isinstance(value, str) and value.strip():
        return value
    return None


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

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, Sequence

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.user import User


class AbstractRepository(ABC):
    """Базовый контракт репозитория на доменном уровне."""

    @abstractmethod
    async def add(self, entity) -> None: ...

    @abstractmethod
    async def remove(self, entity) -> None: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...


class AdRepository(Protocol):
    async def get_by_id(self, ad_id: int) -> Ad | None: ...

    async def list_by_user(self, user_id: int) -> Sequence[Ad]: ...


class AccountRepository(Protocol):
    async def get_by_id(self, account_id: int) -> MessengerAccount | None: ...

    async def list_by_user(self, user_id: int) -> Sequence[MessengerAccount]: ...


class GroupRepository(Protocol):
    async def list_for_account(self, account_id: int, user_id: int) -> Sequence[Group]: ...


class ScheduleRepository(Protocol):
    async def get_for_user(self, schedule_id: int, user_id: int) -> Schedule | None: ...

    async def list_for_user(self, user_id: int) -> Sequence[Schedule]: ...


class SendLogRepository(Protocol):
    async def add_log(self, log: SendLog) -> None: ...


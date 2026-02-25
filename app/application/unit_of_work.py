from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class AbstractUnitOfWork(ABC):
    """Абстракция unit-of-work для доменного слоя."""

    session: AsyncSession

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...


class SupportsUnitOfWorkFactory(Protocol):
    """Контракт фабрики UoW для DI в application-слой."""

    def __call__(self) -> AbstractUnitOfWork: ...


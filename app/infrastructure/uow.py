from __future__ import annotations

from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.unit_of_work import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Unit-of-work поверх AsyncSession.

    Предназначен для использования в application-слое, а не напрямую из роутов.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        assert self.session is not None
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        assert self.session is not None
        await self.session.commit()

    async def rollback(self) -> None:
        assert self.session is not None
        await self.session.rollback()


def create_uow_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], SqlAlchemyUnitOfWork]:
    """Фабрика для DI в application-слой."""

    def _factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory=session_factory)

    return _factory


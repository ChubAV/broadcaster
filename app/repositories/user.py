from sqlalchemy import select, func, or_

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all_users(self) -> list[User]:
        result = await self.session.execute(
            select(User).order_by(User.id)
        )
        return list(result.scalars().all())

    async def search_users(self, query: str) -> list[User]:
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(User)
            .where(or_(User.email.ilike(pattern), User.name.ilike(pattern)))
            .order_by(User.id)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0

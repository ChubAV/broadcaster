from sqlalchemy import select

from app.models.group import Group
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, session):
        super().__init__(session, Group)

    async def list_by_account(self, account_id: int, user_id: int) -> list[Group]:
        result = await self.session.execute(
            select(Group).where(
                Group.account_id == account_id,
                Group.user_id == user_id,
            ).order_by(Group.id)
        )
        return list(result.scalars().all())

    async def get_external_ids(self, account_id: int, user_id: int) -> set[str]:
        result = await self.session.execute(
            select(Group.group_external_id).where(
                Group.account_id == account_id,
                Group.user_id == user_id,
            )
        )
        return {row[0] for row in result}

    async def list_by_user_filtered(
        self, user_id: int, account_id: int | None = None
    ) -> list[Group]:
        query = select(Group).where(Group.user_id == user_id)
        if account_id is not None:
            query = query.where(Group.account_id == account_id)
        query = query.order_by(Group.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

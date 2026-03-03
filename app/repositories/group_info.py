from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_info import GroupInfo
from app.repositories.base import BaseRepository


class GroupInfoRepository(BaseRepository[GroupInfo]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, GroupInfo)

    async def get_by_type_and_external_id(
        self, messenger_type: str, external_id: str
    ) -> GroupInfo | None:
        result = await self.session.execute(
            select(GroupInfo).where(
                GroupInfo.messenger_type == messenger_type,
                GroupInfo.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, messenger_type: str, external_id: str, **kwargs
    ) -> GroupInfo:
        existing = await self.get_by_type_and_external_id(messenger_type, external_id)
        if existing:
            return await self.update(existing, **kwargs)
        return await self.create(
            messenger_type=messenger_type,
            external_id=external_id,
            **kwargs,
        )

    async def search(
        self,
        q: str = "",
        messenger_type: str = "",
        offset: int = 0,
        limit: int = 30,
    ) -> tuple[list[GroupInfo], int]:
        base = select(GroupInfo)
        count_base = select(func.count(GroupInfo.id))

        if messenger_type:
            base = base.where(GroupInfo.messenger_type == messenger_type)
            count_base = count_base.where(GroupInfo.messenger_type == messenger_type)

        if q:
            pattern = f"%{q}%"
            filter_cond = or_(
                GroupInfo.name.ilike(pattern),
                GroupInfo.external_id.ilike(pattern),
            )
            base = base.where(filter_cond)
            count_base = count_base.where(filter_cond)

        total = (await self.session.execute(count_base)).scalar() or 0

        result = await self.session.execute(
            base.order_by(GroupInfo.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def count_by_type(self) -> dict[str, int]:
        result = await self.session.execute(
            select(GroupInfo.messenger_type, func.count(GroupInfo.id)).group_by(
                GroupInfo.messenger_type
            )
        )
        return {row[0]: row[1] for row in result.all()}

    async def list_all_keys(self) -> set[tuple[str, str]]:
        result = await self.session.execute(
            select(GroupInfo.messenger_type, GroupInfo.external_id)
        )
        return {(row[0], row[1]) for row in result.all()}

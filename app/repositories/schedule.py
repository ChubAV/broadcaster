from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.schedule import Schedule
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Schedule)

    async def get_for_user(self, schedule_id: int, user_id: int) -> Schedule | None:
        result = await self.session.execute(
            select(Schedule)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Schedule.id == schedule_id, Ad.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Ad.user_id == user_id)
            .order_by(Schedule.id)
        )
        return list(result.scalars().all())

    async def get_due_schedules(self, now: datetime) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule).where(
                Schedule.is_active == True,
                Schedule.next_run_at <= now,
            )
        )
        return list(result.scalars().all())

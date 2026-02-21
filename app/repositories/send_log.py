from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.repositories.base import BaseRepository


class SendLogRepository(BaseRepository[SendLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SendLog)

    async def get_stats(self, user_id: int, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.count(SendLog.id).label("total_sent"),
                func.sum(case((SendLog.status == "ok", 1), else_=0)).label("success_count"),
                func.sum(case((SendLog.status == "fail", 1), else_=0)).label("fail_count"),
            )
            .join(Schedule, SendLog.schedule_id == Schedule.id)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Ad.user_id == user_id, SendLog.sent_at >= cutoff)
        )
        row = result.one()
        return {
            "total_sent": row.total_sent or 0,
            "success_count": row.success_count or 0,
            "fail_count": row.fail_count or 0,
        }

    async def list_for_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[SendLog]:
        query = (
            select(SendLog)
            .join(Schedule, SendLog.schedule_id == Schedule.id)
            .join(Ad, Schedule.ad_id == Ad.id)
            .where(Ad.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_for_user_with_details(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[dict]:
        query = (
            select(
                SendLog,
                Ad.title.label("ad_title"),
                Group.name.label("group_name"),
            )
            .join(Ad, SendLog.ad_id == Ad.id)
            .join(Group, SendLog.group_id == Group.id)
            .where(Ad.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return [
            {
                "ad_title": r.ad_title,
                "group_name": r.group_name,
                "status": r.SendLog.status,
                "error_message": r.SendLog.error_message,
                "sent_at": r.SendLog.sent_at,
            }
            for r in result
        ]

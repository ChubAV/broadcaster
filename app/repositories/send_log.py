from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

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
            .where(SendLog.user_id == user_id, SendLog.sent_at >= cutoff)
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
            .where(SendLog.user_id == user_id)
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
            select(SendLog)
            .where(SendLog.user_id == user_id)
        )
        if status_filter:
            query = query.where(SendLog.status == status_filter)
        query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return [
            {
                "ad_title": log.ad_title or "—",
                "group_name": log.group_name or "—",
                "status": log.status,
                "error_message": log.error_message,
                "sent_at": log.sent_at,
            }
            for log in result.scalars()
        ]

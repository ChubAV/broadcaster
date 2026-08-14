from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.send_log import SendLog
from app.repositories.base import BaseRepository

# СВОДКИ ПО ЖУРНАЛУ ЗДЕСЬ НЕТ И БЫТЬ НЕ ДОЛЖНО. Метод `get_stats` жил в этом
# классе и считал «ошибками» только статус `fail`, то есть два статуса журнала
# из трёх: отправка, не ушедшая из-за отвалившегося аккаунта, не попадала ни в
# успешные, ни в неуспешные. Это было ВТОРОЕ определение сводки — первое живёт
# в `app/application/analytics/send_analytics.py` и знает, что неуспешная
# отправка есть «не `ok`». Считать агрегаты журнала полагается ТОЛЬКО тем
# модулем; репозиторий отдаёт строки.


class SendLogRepository(BaseRepository[SendLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SendLog)

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

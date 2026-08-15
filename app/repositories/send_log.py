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

    # ЕДИНСТВЕННЫЙ МЕТОД ЧТЕНИЯ, И У НЕГО ЕДИНСТВЕННЫЙ ВЫЗЫВАЮЩИЙ
    # (`app/routes/history.py`). Отсюда убраны две вещи, и обе — по одному
    # рассуждению.
    #
    # 1. Параметр `status_filter`. Его не передавал ни один вызов; ось статуса
    #    живёт в `app/application/analytics/send_analytics.py`, где её знают все
    #    три экрана истории. Второй, никем не используемый способ отфильтровать
    #    тот же журнал — приглашение отфильтровать его ИНАЧЕ, чем остальные.
    #
    # 2. Метод `list_for_user_with_details`. Вызывающих не было ни в `app/`, ни
    #    в `tests/`, и он вдобавок подставлял «—» вместо пустого значения —
    #    оформление экрана внутри слоя доступа к данным. Ровно поэтому из этого
    #    класса уже уехала сводка `get_stats` (см. комментарий выше): считать и
    #    оформлять полагается не здесь.
    async def list_for_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[SendLog]:
        query = (
            select(SendLog)
            .where(SendLog.user_id == user_id)
            .order_by(SendLog.sent_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

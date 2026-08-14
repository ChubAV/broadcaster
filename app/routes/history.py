from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import send_metrics
from app.dependencies import get_current_user_id, get_db
from app.repositories.send_log import SendLogRepository

router = APIRouter(prefix="/api/history", tags=["history"])

# Ширина окна сводки. Число унаследовано от прежнего счёта по репозиторию
# ДОСЛОВНО: план меняет источник чисел и семантику неуспешных, а не период.
STATS_WINDOW = timedelta(days=30)


class SendLogResponse(BaseModel):
    id: int
    schedule_id: int | None
    ad_id: int | None
    group_id: int | None
    ad_title: str | None = None
    ad_text: str | None = None
    ad_images: list | None = None
    group_name: str | None = None
    messenger_type: str | None = None
    status: str
    error_message: str | None
    sent_at: datetime


class StatsResponse(BaseModel):
    total_sent: int
    success_count: int
    fail_count: int


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Сводка по журналу — тем же модулем аналитики, что и плитки дашборда (D-35).

    ПОЧЕМУ ЗДЕСЬ НЕТ СВОЕГО СЧЁТА. До этой правки на вопрос «сколько было
    ошибок» проект отвечал двумя разными числами: плитка дашборда считала
    «не `ok`», а этот маршрут — только `fail`, поэтому отправка с отвалившимся
    аккаунтом (`account_disconnected`) не попадала ни в успешные, ни в
    неуспешные и молча исчезала из ответа. Второго определения сводки в проекте
    больше нет: определение живёт в `send_metrics`, а маршрут его ВЫЗЫВАЕТ.

    ФОРМА ОТВЕТА НЕ ИЗМЕНИЛАСЬ — те же три поля с теми же именами. Перечислить
    внешних потребителей этих JSON-адресов нельзя, а снос публичной поверхности
    ради такого потребителя — дверь в одну сторону, поэтому маршрут выровнен, а
    не удалён (прецедент сноса мёртвых JSON-маршрутов раздела групп сюда не
    переносится именно по этой причине).

    Владение держит `user_id` из зависимости аутентификации: он приезжает в
    модуль аналитики обязательным именованным аргументом, и ветки «по всем
    пользователям» там нет вовсе (T-04-41).
    """
    metrics = await send_metrics(db, user_id=user_id, window=STATS_WINDOW)
    return StatsResponse(
        total_sent=metrics.total,
        success_count=metrics.ok,
        # `failed` — это «не `ok`», а не членство в списке известных неуспешных
        # статусов: неклассифицируемая запись обязана попасть в неуспешные, а не
        # выпасть из обоих чисел ради ровной суммы.
        fail_count=metrics.failed,
    )


@router.get("", response_model=list[SendLogResponse])
async def list_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SendLogRepository(db)
    return await repo.list_for_user(user_id, offset=skip, limit=limit)

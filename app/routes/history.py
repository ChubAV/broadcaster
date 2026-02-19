from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.models.ad import Ad
from app.models.schedule import Schedule
from app.models.send_log import SendLog

router = APIRouter(prefix="/api/history", tags=["history"])


class SendLogResponse(BaseModel):
    id: int
    schedule_id: int
    ad_id: int
    group_id: int
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
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(
            func.count(SendLog.id).label("total_sent"),
            func.sum(case((SendLog.status == "sent", 1), else_=0)).label("success_count"),
            func.sum(case((SendLog.status == "failed", 1), else_=0)).label("fail_count"),
        )
        .join(Schedule, SendLog.schedule_id == Schedule.id)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(
            Ad.user_id == user_id,
            SendLog.sent_at >= thirty_days_ago,
        )
    )
    row = result.one()
    return StatsResponse(
        total_sent=row.total_sent or 0,
        success_count=row.success_count or 0,
        fail_count=row.fail_count or 0,
    )


@router.get("", response_model=list[SendLogResponse])
async def list_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SendLog)
        .join(Schedule, SendLog.schedule_id == Schedule.id)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Ad.user_id == user_id)
        .order_by(SendLog.sent_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

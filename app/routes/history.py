from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.send_log import SendLogRepository

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
    repo = SendLogRepository(db)
    stats = await repo.get_stats(user_id)
    return StatsResponse(**stats)


@router.get("", response_model=list[SendLogResponse])
async def list_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SendLogRepository(db)
    return await repo.list_for_user(user_id, offset=skip, limit=limit)

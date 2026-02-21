from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.ad import AdRepository
from app.repositories.schedule import ScheduleRepository
from app.services.schedule_service import compute_next_run_at

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class CreateScheduleRequest(BaseModel):
    ad_id: int
    account_id: int
    group_ids: list[int] = []
    days_of_week: list[int] = []
    times_of_day: list[str] = []


class UpdateScheduleRequest(BaseModel):
    group_ids: list[int] | None = None
    days_of_week: list[int] | None = None
    times_of_day: list[str] | None = None


class ScheduleResponse(BaseModel):
    id: int
    ad_id: int
    account_id: int
    group_ids: list
    days_of_week: list
    times_of_day: list
    is_active: bool
    next_run_at: datetime | None
    created_at: datetime


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: CreateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ad_repo = AdRepository(db)
    ad = await ad_repo.get_by_id_and_user(data.ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found",
        )

    next_run = compute_next_run_at(
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        tz_name="UTC",
    )

    schedule_repo = ScheduleRepository(db)
    schedule = await schedule_repo.create(
        ad_id=data.ad_id,
        account_id=data.account_id,
        group_ids=data.group_ids,
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        next_run_at=next_run,
    )
    return schedule


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    return await repo.list_for_user(user_id)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: UpdateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Recompute next_run_at
    schedule.next_run_at = compute_next_run_at(
        days_of_week=schedule.days_of_week,
        times_of_day=schedule.times_of_day,
        tz_name="UTC",
    )

    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )
    await repo.delete(schedule)


@router.post("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    schedule.is_active = not schedule.is_active

    if schedule.is_active:
        # Recompute next_run_at when activating
        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name="UTC",
        )
    else:
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    return schedule

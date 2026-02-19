from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.models.ad import Ad
from app.models.schedule import Schedule
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


async def _verify_ad_ownership(ad_id: int, user_id: int, db: AsyncSession) -> Ad:
    """Verify that the ad belongs to the current user."""
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user_id)
    )
    ad = result.scalar_one_or_none()
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found",
        )
    return ad


async def _get_schedule_for_user(
    schedule_id: int, user_id: int, db: AsyncSession
) -> Schedule:
    """Get a schedule, verifying ownership through ad -> user_id."""
    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user_id)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )
    return schedule


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: CreateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _verify_ad_ownership(data.ad_id, user_id, db)

    next_run = compute_next_run_at(
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        tz_name="UTC",
    )

    schedule = Schedule(
        ad_id=data.ad_id,
        account_id=data.account_id,
        group_ids=data.group_ids,
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        next_run_at=next_run,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Ad.user_id == user_id)
        .order_by(Schedule.id)
    )
    return result.scalars().all()


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: UpdateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    schedule = await _get_schedule_for_user(schedule_id, user_id, db)

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
    schedule = await _get_schedule_for_user(schedule_id, user_id, db)
    await db.delete(schedule)
    await db.commit()


@router.post("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    schedule = await _get_schedule_for_user(schedule_id, user_id, db)
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

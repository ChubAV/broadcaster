from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import VALID_TIMEZONES
from app.dependencies import get_current_user_id, get_db
from app.models.messenger_account import MessengerAccount
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
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in VALID_TIMEZONES:
            raise ValueError(f"Invalid timezone: {v}")
        return v


class UpdateScheduleRequest(BaseModel):
    group_ids: list[int] | None = None
    days_of_week: list[int] | None = None
    times_of_day: list[str] | None = None
    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_TIMEZONES:
            raise ValueError(f"Invalid timezone: {v}")
        return v


class ScheduleResponse(BaseModel):
    id: int
    ad_id: int
    # None, если аккаунт был удалён и расписание отвязано (issue #35).
    # CreateScheduleRequest.account_id остаётся обязательным.
    account_id: int | None
    group_ids: list
    days_of_week: list
    times_of_day: list
    timezone: str
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

    # Владение объявлением проверялось здесь с самого начала, владение аккаунтом
    # — нет; асимметрия и была находкой CR-01/D-20: чужой `account_id`
    # принимался, и рассылка ушла бы через чужую подключённую сессию мессенджера.
    # Форма проверки — та же, что строкой выше: чужой идентификатор неотличим от
    # несуществующего и даёт 404, не подтверждая существование чужой записи.
    account = (
        await db.execute(
            select(MessengerAccount.id).where(
                MessengerAccount.id == data.account_id,
                MessengerAccount.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    next_run = compute_next_run_at(
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        tz_name=data.timezone,
    )

    schedule_repo = ScheduleRepository(db)
    schedule = await schedule_repo.create(
        ad_id=data.ad_id,
        account_id=data.account_id,
        group_ids=data.group_ids,
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        timezone=data.timezone,
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
        tz_name=schedule.timezone,
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

    # issue #35: отвязанное расписание нельзя возобновить — оно никогда ничего
    # не отправит. Постановка на паузу активного расписания не блокируется.
    if not schedule.is_active and schedule.account_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала привяжите аккаунт мессенджера к расписанию",
        )

    schedule.is_active = not schedule.is_active

    if schedule.is_active:
        # Recompute next_run_at when activating
        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name=schedule.timezone,
        )
    else:
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    return schedule

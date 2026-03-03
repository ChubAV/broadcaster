from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.group import GroupRepository
from app.repositories.schedule import ScheduleRepository

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    account_id: int
    messenger_type: str
    group_external_id: str
    name: str


class GroupResponse(BaseModel):
    id: int
    account_id: int
    messenger_type: str
    group_external_id: str
    name: str
    is_active: bool
    created_at: datetime


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: CreateGroupRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    group = await repo.create(
        user_id=user_id,
        account_id=data.account_id,
        messenger_type=data.messenger_type,
        group_external_id=data.group_external_id,
        name=data.name,
    )
    return group


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    account_id: int | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    return await repo.list_by_user_filtered(user_id, account_id)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    group = await repo.get_by_id_and_user(group_id, user_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    schedule_repo = ScheduleRepository(db)
    await schedule_repo.remove_group_ids(user_id, {group.id})
    await repo.delete(group)


@router.patch("/{group_id}/toggle", response_model=GroupResponse)
async def toggle_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupRepository(db)
    group = await repo.get_by_id_and_user(group_id, user_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    group = await repo.update(group, is_active=not group.is_active)
    return group

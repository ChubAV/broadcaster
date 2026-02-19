from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.models.group import Group
from app.services.billing_service import check_limit

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
    allowed, reason = await check_limit(db, user_id, "create_group")
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    group = Group(
        user_id=user_id,
        account_id=data.account_id,
        messenger_type=data.messenger_type,
        group_external_id=data.group_external_id,
        name=data.name,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    account_id: int | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(Group).where(Group.user_id == user_id)
    if account_id is not None:
        query = query.where(Group.account_id == account_id)
    query = query.order_by(Group.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user_id)
    )
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    await db.delete(group)
    await db.commit()


@router.patch("/{group_id}/toggle", response_model=GroupResponse)
async def toggle_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user_id)
    )
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    group.is_active = not group.is_active
    await db.commit()
    await db.refresh(group)
    return group

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.models.messenger_account import MessengerAccount

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    type: str  # tg_bot, tg_user, wa
    credentials: str


class AccountResponse(BaseModel):
    id: int
    type: str
    status: str
    created_at: datetime


class AccountStatusResponse(BaseModel):
    id: int
    status: str


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: CreateAccountRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    account = MessengerAccount(
        user_id=user_id,
        type=data.type,
        credentials=data.credentials,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MessengerAccount)
        .where(MessengerAccount.user_id == user_id)
        .order_by(MessengerAccount.id)
    )
    return result.scalars().all()


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MessengerAccount)
        .where(MessengerAccount.id == account_id, MessengerAccount.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    await db.delete(account)
    await db.commit()


@router.get("/{account_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MessengerAccount)
        .where(MessengerAccount.id == account_id, MessengerAccount.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

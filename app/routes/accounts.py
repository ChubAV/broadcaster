from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.use_cases import detach_schedules_from_account
from app.dependencies import get_current_user_id, get_db
from app.repositories.account import AccountRepository

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    type: str  # tg_user, wa
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
    repo = AccountRepository(db)
    account = await repo.create(
        user_id=user_id,
        type=data.type,
        credentials=data.credentials,
    )
    return account


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    return await repo.list_by_user(user_id)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    account = await repo.get_by_id_and_user(account_id, user_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    # issue #35: расписания сохраняются и приостанавливаются, а не удаляются.
    # repo.delete коммитит, поэтому отвязка и удаление попадают в одну транзакцию.
    await detach_schedules_from_account(db, account.id)
    await repo.delete(account)


@router.get("/{account_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AccountRepository(db)
    account = await repo.get_by_id_and_user(account_id, user_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

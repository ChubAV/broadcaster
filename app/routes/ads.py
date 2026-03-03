from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.repositories.ad import AdRepository

router = APIRouter(prefix="/api/ads", tags=["ads"])


class CreateAdRequest(BaseModel):
    title: str
    text: str
    images: list[str] = []


class UpdateAdRequest(BaseModel):
    title: str | None = None
    text: str | None = None
    images: list[str] | None = None
    is_active: bool | None = None


class AdResponse(BaseModel):
    id: int
    title: str
    text: str
    images: list
    is_active: bool
    created_at: datetime


@router.post("", response_model=AdResponse, status_code=status.HTTP_201_CREATED)
async def create_ad(
    data: CreateAdRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.create(
        user_id=user_id,
        title=data.title,
        text=data.text,
        images=data.images,
    )
    return ad


@router.get("", response_model=list[AdResponse])
async def list_ads(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    return await repo.list_by_user(user_id)


@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")
    return ad


@router.put("/{ad_id}", response_model=AdResponse)
async def update_ad(
    ad_id: int,
    data: UpdateAdRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")

    ad = await repo.update(ad, **data.model_dump(exclude_unset=True))
    return ad


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(
    ad_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")

    await repo.delete(ad)

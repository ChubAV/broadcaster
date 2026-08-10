from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_current_user_id, get_db, get_settings
# Правило ключа вложения живёт в одном месте на оба слоя: разъехавшись, они
# оставили бы JSON-вход открытым для ровно того же WR-01, что закрыт на форме.
from app.pages.ads import own_image_keys
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
    # Тип — замкнутое множество, а не str (T-02-11). update_ad присваивает поля
    # напрямую из model_dump(exclude_unset=True), поэтому схема — единственное
    # место, где произвольную строку можно остановить: записанная, она не
    # отфильтровалась бы ни как черновик, ни как опубликованное, и объявление
    # выпало бы разом и из списка к отправке, и из выбора на странице
    # расписаний. Литералы дублируют app.constants сознательно: Literal требует
    # константного выражения на этапе объявления класса.
    status: Literal["draft", "published"] | None = None


class AdResponse(BaseModel):
    id: int
    title: str
    text: str
    images: list
    status: str
    created_at: datetime


@router.post("", response_model=AdResponse, status_code=status.HTTP_201_CREATED)
async def create_ad(
    data: CreateAdRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    repo = AdRepository(db)
    ad = await repo.create(
        user_id=user_id,
        title=data.title,
        text=data.text,
        images=own_image_keys(data.images, user_id, settings.max_images_per_ad),
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
    settings: Settings = Depends(get_settings),
):
    repo = AdRepository(db)
    ad = await repo.get_by_id_and_user(ad_id, user_id)
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")

    fields = data.model_dump(exclude_unset=True)
    # Отсутствие ключа `images` (не передан) и переданный пустой список — разные
    # намерения; `exclude_unset` их уже различает, и проверка это различие
    # сохраняет, иначе правка одного заголовка обнуляла бы вложения.
    if fields.get("images") is not None:
        fields["images"] = own_image_keys(
            fields["images"], user_id, settings.max_images_per_ad
        )

    ad = await repo.update(ad, **fields)
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

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/ads", response_class=HTMLResponse)
async def ads_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc())
    )
    ads = result.scalars().all()
    return templates.TemplateResponse(
        "ads/list.html",
        {"request": request, "user": user, "ads": ads, "active_page": "ads"},
    )


@router.get("/ads/new", response_class=HTMLResponse)
async def ads_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "ad": None, "active_page": "ads"},
    )


@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad = Ad(user_id=user.id, title=title, text=text, images=image_list)
    db.add(ad)
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_edit(
    request: Request,
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "ad": ad, "active_page": "ads"},
    )


@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)

    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad.title = title
    ad.text = text
    ad.images = image_list
    ad.is_active = is_active
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.post("/ads/{ad_id}/delete")
async def ads_delete(
    request: Request,
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if ad:
        await db.delete(ad)
        await db.commit()
    return RedirectResponse(url="/ads", status_code=302)

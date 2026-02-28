from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


async def _enrich_ads_with_stats(db: AsyncSession, ads: list[Ad]) -> None:
    """Добавляет sends_count и schedules_count к каждому объявлению."""
    if not ads:
        return
    ad_ids = [a.id for a in ads]
    # Успешные отправки по ad_id
    sends_result = await db.execute(
        select(SendLog.ad_id, func.count().label("cnt"))
        .where(SendLog.ad_id.in_(ad_ids), SendLog.status == "ok")
        .group_by(SendLog.ad_id)
    )
    sends_map = {r.ad_id: r.cnt for r in sends_result.all()}
    # Расписания по ad_id
    sched_result = await db.execute(
        select(Schedule.ad_id, func.count().label("cnt"))
        .where(Schedule.ad_id.in_(ad_ids))
        .group_by(Schedule.ad_id)
    )
    sched_map = {r.ad_id: r.cnt for r in sched_result.all()}
    for ad in ads:
        ad.sends_count = sends_map.get(ad.id, 0) or 0
        ad.schedules_count = sched_map.get(ad.id, 0) or 0


@router.get("/ads/partial", response_class=HTMLResponse)
async def ads_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    layout: str = Query("table"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc()).offset(offset).limit(limit + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    ads = rows[:limit]
    await _enrich_ads_with_stats(db, ads)
    template = "ads/partial_cards.html" if layout == "cards" else "ads/partial_rows.html"
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "user": user,
            "ads": ads,
            "has_next": has_next,
            "next_offset": offset + limit,
        },
    )


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
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc()).limit(PAGE_SIZE + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    ads = rows[:PAGE_SIZE]
    await _enrich_ads_with_stats(db, ads)
    return templates.TemplateResponse(
        "ads/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "ads": ads,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "ads",
        },
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
        {"request": request, "user": user, "is_admin": check_is_admin(user, settings), "ad": None, "active_page": "ads"},
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
        {"request": request, "user": user, "is_admin": check_is_admin(user, settings), "ad": ad, "active_page": "ads"},
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

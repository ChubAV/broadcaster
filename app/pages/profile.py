from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import TIMEZONE_CHOICES, VALID_TIMEZONES
from app.dependencies import get_db, get_settings
from app.pages.common import check_is_admin, get_user_from_cookie, templates


router = APIRouter(tags=["pages"])


@router.get("/profile", response_class=HTMLResponse)
async def profile_get(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "profile",
            "timezone_choices": TIMEZONE_CHOICES,
        },
    )


@router.post("/profile")
async def profile_post(
    request: Request,
    timezone: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if timezone in VALID_TIMEZONES:
        user.timezone = timezone
        db.add(user)
        await db.commit()
        return RedirectResponse(url="/profile?saved=1", status_code=302)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "profile",
            "timezone_choices": TIMEZONE_CHOICES,
            "error": "Неверный часовой пояс",
        },
        status_code=400,
    )


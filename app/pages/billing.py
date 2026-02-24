from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.services.billing_service import get_user_plan, get_plan_limits, get_usage, PLANS
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    plan = await get_user_plan(db, user.id)
    limits = get_plan_limits(plan)
    usage = await get_usage(db, user.id)
    return templates.TemplateResponse(
        "billing/plans.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "plan": plan,
            "limits": limits,
            "usage": usage,
            "all_plans": PLANS,
            "active_page": "billing",
        },
    )

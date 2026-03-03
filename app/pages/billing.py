from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.services.billing_service import get_balance_info, get_transaction_history
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
    balance_info = await get_balance_info(db, user.id)
    transactions = await get_transaction_history(db, user.id, limit=20)
    packages = settings.parsed_message_packages
    return templates.TemplateResponse(
        "billing/balance.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "balance_info": balance_info,
            "transactions": transactions,
            "packages": packages,
            "active_page": "billing",
        },
    )

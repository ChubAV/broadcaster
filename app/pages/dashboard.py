from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_PUBLISHED
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Stats
    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(
                Ad.user_id == user.id, Ad.status == AD_STATUS_PUBLISHED
            )
        )
    ).scalar() or 0
    accounts_count = (
        await db.execute(
            select(func.count(MessengerAccount.id)).where(
                MessengerAccount.user_id == user.id,
                MessengerAccount.status == "active",
            )
        )
    ).scalar() or 0
    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == user.id, Group.is_active == True  # noqa: E712
            )
        )
    ).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sent_today = (
        await db.execute(
            select(func.count(SendLog.id))
            .join(Ad, SendLog.ad_id == Ad.id)
            .where(Ad.user_id == user.id, SendLog.sent_at >= today_start)
        )
    ).scalar() or 0

    stats = {
        "active_ads": ads_count,
        "active_accounts": accounts_count,
        "active_groups": groups_count,
        "sent_today": sent_today,
    }

    # Recent sends (last 10)
    recent_query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
        .order_by(SendLog.sent_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_query)
    recent_sends = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in recent_result
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "stats": stats,
            "recent_sends": recent_sends,
            "active_page": "dashboard",
        },
    )

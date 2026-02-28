from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/history/{log_id}", response_class=HTMLResponse)
async def history_detail(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user.id:
        return RedirectResponse(url="/history", status_code=302)

    return templates.TemplateResponse(
        "history/detail.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "log": log,
            "active_page": "history",
        },
    )


@router.get("/history", response_class=HTMLResponse)
async def history_list(
    request: Request,
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    page_size = 50

    query = (
        select(SendLog)
        .where(SendLog.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "group_name": r.group_name or "—",
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "logs": logs,
            "status_filter": status,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "active_page": "history",
        },
    )

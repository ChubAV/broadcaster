from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.send_log import SendLog
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


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
        select(
            SendLog,
            Ad.title.label("ad_title"),
            Group.name.label("group_name"),
        )
        .join(Ad, SendLog.ad_id == Ad.id)
        .join(Group, SendLog.group_id == Group.id)
        .where(Ad.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result)

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    logs = [
        {
            "ad_title": r.ad_title,
            "group_name": r.group_name,
            "status": r.SendLog.status,
            "error_message": r.SendLog.error_message,
            "sent_at": r.SendLog.sent_at,
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "logs": logs,
            "status_filter": status,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "active_page": "history",
        },
    )

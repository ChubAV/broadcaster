from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


@router.get("/history/partial", response_class=HTMLResponse)
async def history_partial(
    request: Request,
    status: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > limit
    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "ad_images": r.ad_images or [],
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in rows[:limit]
    ]
    template = "history/partial_cards.html" if layout == "cards" else "history/partial_rows.html"
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "user": user,
            "logs": logs,
            "has_next": has_next,
            "next_offset": offset + limit,
            "status_filter": status,
        },
    )


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

    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(PAGE_SIZE + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > PAGE_SIZE
    rows = rows[:PAGE_SIZE]

    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "ad_images": r.ad_images or [],
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in rows
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
            "page_size": PAGE_SIZE,
            "has_next": has_next,
            "next_offset": offset + len(logs),
            "active_page": "history",
        },
    )

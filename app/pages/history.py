from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


def _parse_account_id(v: str | None) -> int | None:
    if not v or not v.strip():
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _history_filter_params(
    status: str | None,
    messenger_type: str | None,
    account_id: int | None,
    period: str | None,
) -> dict:
    p = {}
    if status:
        p["status"] = status
    if messenger_type:
        p["messenger"] = messenger_type
    if account_id is not None:
        p["account_id"] = account_id
    if period:
        p["period"] = period
    return p


def _apply_history_filters(query, status, messenger_type, account_id, period):
    if status:
        query = query.where(SendLog.status == status)
    if messenger_type:
        query = query.where(SendLog.messenger_type == messenger_type)
    if account_id is not None:
        query = query.where(Group.account_id == account_id)
    if period == "7d":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.where(SendLog.sent_at >= cutoff)
    elif period == "30d":
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.where(SendLog.sent_at >= cutoff)
    return query


@router.get("/history/partial", response_class=HTMLResponse)
async def history_partial(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    account_id_int = _parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = _apply_history_filters(query, status, messenger, account_id_int, period)
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
    filter_params = _history_filter_params(status, messenger, account_id_int, period)
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
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
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

    group = await db.get(Group, log.group_id) if log.group_id else None

    return templates.TemplateResponse(
        "history/detail.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "log": log,
            "group": group,
            "active_page": "history",
        },
    )


@router.get("/history", response_class=HTMLResponse)
async def history_list(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    account_id_int = _parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = _apply_history_filters(query, status, messenger, account_id_int, period)
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

    accounts_result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.user_id == user.id)
    )
    all_accounts = accounts_result.scalars().all()
    filter_params = _history_filter_params(status, messenger, account_id_int, period)

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "logs": logs,
            "all_accounts": all_accounts,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            "offset": offset,
            "page_size": PAGE_SIZE,
            "has_next": has_next,
            "next_offset": offset + len(logs),
            "active_page": "history",
        },
    )

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings, require_admin
from app.models.user import User
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.pages.common import templates
from app.repositories.user import UserRepository
from app.services.billing_service import (
    PLANS,
    get_user_plan,
    get_usage,
    set_user_plan,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_repo = UserRepository(db)
    total_users = await user_repo.count_all()

    total_accounts = (
        await db.execute(select(func.count(MessengerAccount.id)))
    ).scalar() or 0

    total_active_accounts = (
        await db.execute(
            select(func.count(MessengerAccount.id)).where(
                MessengerAccount.status == "active"
            )
        )
    ).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sends_today = (
        await db.execute(
            select(func.count(SendLog.id)).where(
                SendLog.sent_at >= today_start
            )
        )
    ).scalar() or 0

    active_subs = (
        await db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.is_active == True,  # noqa: E712
                Subscription.expires_at > datetime.now(timezone.utc),
            )
        )
    ).scalar() or 0

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "stats": {
                "total_users": total_users,
                "total_accounts": total_accounts,
                "active_accounts": total_active_accounts,
                "sends_today": sends_today,
                "active_subscriptions": active_subs,
            },
        },
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: str = "",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_repo = UserRepository(db)
    if q:
        users = await user_repo.search_users(q)
    else:
        users = await user_repo.get_all_users()

    # Get plan for each user
    user_data = []
    for u in users:
        plan = await get_user_plan(db, u.id)
        user_data.append({"user": u, "plan": plan})

    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "users": user_data,
            "search_query": q,
        },
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    plan = await get_user_plan(db, target_user.id)
    usage = await get_usage(db, target_user.id)

    # Get user's accounts
    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == target_user.id
        )
    )
    accounts = list(accounts_result.scalars().all())

    # Get user's ads count
    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(Ad.user_id == target_user.id)
        )
    ).scalar() or 0

    # Get user's groups count
    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == target_user.id
            )
        )
    ).scalar() or 0

    # Get active subscription details
    sub_result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == target_user.id,
            Subscription.is_active == True,  # noqa: E712
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    active_sub = sub_result.scalar_one_or_none()

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "plan": plan,
            "usage": usage,
            "accounts": accounts,
            "ads_count": ads_count,
            "groups_count": groups_count,
            "active_sub": active_sub,
            "all_plans": PLANS,
        },
    )


@router.get("/users/{user_id}/history", response_class=HTMLResponse)
async def admin_user_history(
    request: Request,
    user_id: int,
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    page_size = 50

    query = select(SendLog).where(SendLog.user_id == user_id)
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    return templates.TemplateResponse(
        "admin/user_history.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "logs": rows,
            "status_filter": status,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
        },
    )


@router.get("/users/{user_id}/history/{log_id}", response_class=HTMLResponse)
async def admin_user_history_detail(
    request: Request,
    user_id: int,
    log_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user_id:
        return RedirectResponse(url=f"/admin/users/{user_id}/history", status_code=302)

    group = await db.get(Group, log.group_id) if log.group_id else None

    return templates.TemplateResponse(
        "admin/user_history_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "log": log,
            "group": group,
        },
    )


@router.post("/users/{user_id}/plan")
async def admin_set_plan(
    request: Request,
    user_id: int,
    plan: str = Form(...),
    expires_days: int = Form(30),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
    await set_user_plan(db, user_id, plan, expires_at)

    return RedirectResponse(
        url=f"/admin/users/{user_id}", status_code=302
    )


@router.post("/users/{user_id}/block")
async def admin_toggle_block(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Don't allow admin to block themselves
    if target_user.id == admin.id:
        return RedirectResponse(
            url=f"/admin/users/{user_id}", status_code=302
        )

    target_user.is_blocked = not target_user.is_blocked
    await db.commit()

    return RedirectResponse(
        url=f"/admin/users/{user_id}", status_code=302
    )


@router.post("/users/{user_id}/delete")
async def admin_delete_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Don't allow admin to delete themselves
    if target_user.id == admin.id:
        return RedirectResponse(
            url=f"/admin/users/{user_id}", status_code=302
        )

    await db.delete(target_user)
    await db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)

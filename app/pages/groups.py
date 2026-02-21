from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.pages.common import get_user_from_cookie, templates

router = APIRouter(tags=["pages"])


@router.get("/groups", response_class=HTMLResponse)
async def groups_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.user_id == user.id).order_by(Group.id)
    )
    groups = result.scalars().all()

    # Load tg_user accounts for sync buttons
    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "tg_user",
        )
    )
    tg_user_accounts = accounts_result.scalars().all()

    # Load WA accounts for sync buttons
    wa_accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "active",
        )
    )
    wa_accounts = wa_accounts_result.scalars().all()

    return templates.TemplateResponse(
        "groups/list.html",
        {
            "request": request,
            "user": user,
            "groups": groups,
            "tg_user_accounts": tg_user_accounts,
            "wa_accounts": wa_accounts,
            "active_page": "groups",
        },
    )


@router.post("/groups/{group_id}/toggle")
async def groups_toggle(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        group.is_active = not group.is_active
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)


@router.post("/groups/{group_id}/delete")
async def groups_delete(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        await db.delete(group)
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)

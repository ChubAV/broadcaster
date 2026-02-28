from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates
from app.repositories.schedule import ScheduleRepository

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


async def _get_group_stats(
    db: AsyncSession, user_id: int, group_ids: list[int]
) -> dict[int, dict]:
    """Статистика по группам: попытки, успехи, расписания, последняя отправка."""
    if not group_ids:
        return {}

    # send_attempts, send_success, last_sent_at
    send_sub = (
        select(
            SendLog.group_id,
            func.count(SendLog.id).label("attempts"),
            func.sum(case((SendLog.status == "ok", 1), else_=0)).label("success"),
            func.max(SendLog.sent_at).label("last_sent"),
        )
        .where(
            SendLog.group_id.in_(group_ids),
            SendLog.user_id == user_id,
        )
        .group_by(SendLog.group_id)
    )
    send_r = await db.execute(send_sub)
    send_map = {
        r.group_id: {
            "attempts": r.attempts or 0,
            "success": int(r.success or 0),
            "last_sent_at": r.last_sent,
        }
        for r in send_r
    }

    # schedules_count — загружаем расписания и считаем в Python (group_ids — JSON)
    sched_r = await db.execute(select(Schedule.group_ids))
    sched_counts: dict[int, int] = {gid: 0 for gid in group_ids}
    for row in sched_r:
        for gid in row.group_ids or []:
            if gid in sched_counts:
                sched_counts[gid] += 1

    result = {}
    for gid in group_ids:
        sm = send_map.get(gid, {})
        result[gid] = {
            "send_attempts": sm.get("attempts", 0),
            "send_success": sm.get("success", 0),
            "schedules_count": sched_counts.get(gid, 0),
            "last_sent_at": sm.get("last_sent_at"),
        }
    return result


def _accounts_by_id(accounts: list) -> dict[int, dict]:
    """Словарь account_id -> {id, type} для отображения в карточках."""
    return {a.id: {"id": a.id, "type": a.type} for a in accounts}


def _parse_filter_account_id(v: str | None) -> int | None:
    if not v or not v.strip():
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _parse_filter_is_active(v: str | None) -> bool | None:
    if not v or not v.strip():
        return None
    if v in ("1", "true", "yes"):
        return True
    if v in ("0", "false", "no"):
        return False
    return None


def _filter_params(account_id, messenger_type, is_active, search) -> dict:
    params = {}
    if account_id is not None:
        params["account_id"] = account_id
    if messenger_type:
        params["messenger_type"] = messenger_type
    if is_active is not None:
        params["is_active"] = "1" if is_active else "0"
    if search and search.strip():
        params["search"] = search.strip()
    return params


def _build_groups_query(Group, user_id, account_id, messenger_type, is_active, search):
    q = select(Group).where(Group.user_id == user_id)
    if account_id is not None:
        q = q.where(Group.account_id == account_id)
    if messenger_type:
        q = q.where(Group.messenger_type == messenger_type)
    if is_active is not None:
        q = q.where(Group.is_active == is_active)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        q = q.where(Group.name.ilike(pattern))
    return q.order_by(Group.id)


@router.get("/groups/partial", response_class=HTMLResponse)
async def groups_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    account_id: str | None = Query(None),
    messenger_type: str | None = Query(None),
    is_active: str | None = Query(None),
    search: str | None = Query(None),
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    account_id_int = _parse_filter_account_id(account_id)
    is_active_bool = _parse_filter_is_active(is_active)
    q = _build_groups_query(Group, user.id, account_id_int, messenger_type, is_active_bool, search)
    result = await db.execute(q.offset(offset).limit(limit + 1))
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    groups = rows[:limit]

    group_stats = await _get_group_stats(db, user.id, [g.id for g in groups])
    account_ids = list({g.account_id for g in groups})
    accounts_r = await db.execute(
        select(MessengerAccount).where(MessengerAccount.id.in_(account_ids))
    )
    accounts_by_id = _accounts_by_id(accounts_r.scalars().all())

    template = "groups/partial_cards.html" if layout == "cards" else "groups/partial_rows.html"
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "user": user,
            "groups": groups,
            "group_stats": group_stats,
            "accounts_by_id": accounts_by_id,
            "has_next": has_next,
            "next_offset": offset + limit,
            "filter_params": _filter_params(account_id_int, messenger_type, is_active_bool, search),
        },
    )


@router.get("/groups", response_class=HTMLResponse)
async def groups_list(
    request: Request,
    account_id: str | None = Query(None),
    messenger_type: str | None = Query(None),
    is_active: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    account_id_int = _parse_filter_account_id(account_id)
    is_active_bool = _parse_filter_is_active(is_active)
    q = _build_groups_query(Group, user.id, account_id_int, messenger_type, is_active_bool, search)
    result = await db.execute(q.limit(PAGE_SIZE + 1))
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    groups = rows[:PAGE_SIZE]

    # Load all accounts for filters and sync buttons
    accounts_result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.user_id == user.id)
    )
    all_accounts = accounts_result.scalars().all()
    tg_user_accounts = [a for a in all_accounts if a.type == "tg_user"]
    wa_accounts = [a for a in all_accounts if a.type == "wa" and a.status == "active"]

    group_stats = await _get_group_stats(db, user.id, [g.id for g in groups])
    accounts_by_id = _accounts_by_id(all_accounts)

    filter_params = _filter_params(account_id_int, messenger_type, is_active_bool, search) or {}

    return templates.TemplateResponse(
        "groups/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "groups": groups,
            "group_stats": group_stats,
            "accounts_by_id": accounts_by_id,
            "tg_user_accounts": tg_user_accounts,
            "wa_accounts": wa_accounts,
            "all_accounts": all_accounts,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "groups",
            "filter_params": filter_params,
            "filter_account_id": account_id_int,
            "filter_messenger_type": messenger_type,
            "filter_is_active": is_active_bool,
            "filter_search": search or "",
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
        schedule_repo = ScheduleRepository(db)
        await schedule_repo.remove_group_ids(user.id, {group.id})
        await db.delete(group)
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)


@router.post("/groups/bulk")
async def groups_bulk(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form = await request.form()
    action = form.get("action")
    group_ids = form.getlist("group_ids")

    if not group_ids or action not in {"deactivate", "delete"}:
        return RedirectResponse(url="/groups", status_code=302)

    try:
        ids = [int(gid) for gid in group_ids]
    except ValueError:
        return RedirectResponse(url="/groups", status_code=302)

    result = await db.execute(
        select(Group).where(Group.user_id == user.id, Group.id.in_(ids))
    )
    groups = result.scalars().all()

    if action == "deactivate":
        for group in groups:
            group.is_active = False
        await db.commit()
    elif action == "delete":
        schedule_repo = ScheduleRepository(db)
        await schedule_repo.remove_group_ids(user.id, {g.id for g in groups})
        for group in groups:
            await db.delete(group)
        await db.commit()

    return RedirectResponse(url="/groups", status_code=302)

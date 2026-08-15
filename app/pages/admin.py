from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings, require_admin
from app.application.analytics.send_analytics import (
    apply_history_filters,
    history_filter_params,
)
from app.pages.history import (
    MESSENGER_VALUES,
    PAGE_SIZE,
    PERIOD_VALUES,
    STATUS_VALUES,
    clean_choice,
    parse_account_id,
)
from app.models.user import User
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.message_balance import MessageBalance
from app.pages.common import templates
from app.repositories.group_info import GroupInfoRepository
from app.repositories.user import UserRepository
from app.services.billing_service import (
    get_balance,
    get_balance_info,
    get_or_create_balance,
    add_messages,
)
from app.services.billing_cache import invalidate_balance_cache

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

    total_balance = (
        await db.execute(
            select(func.coalesce(func.sum(MessageBalance.balance), 0))
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
                "total_balance": total_balance,
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

    user_data = []
    for u in users:
        bal = await get_or_create_balance(db, u.id)
        user_data.append({"user": u, "balance": bal.balance, "is_unlimited": bal.is_unlimited})

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

    balance_info = await get_balance_info(db, target_user.id)

    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == target_user.id
        )
    )
    accounts = list(accounts_result.scalars().all())

    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(Ad.user_id == target_user.id)
        )
    ).scalar() or 0

    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == target_user.id
            )
        )
    ).scalar() or 0

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "balance_info": balance_info,
            "accounts": accounts,
            "ads_count": ads_count,
            "groups_count": groups_count,
        },
    )


@router.get("/users/{user_id}/history", response_class=HTMLResponse)
async def admin_user_history(
    request: Request,
    user_id: int,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Размер страницы — ТОТ ЖЕ, что у пользовательской истории, и берётся у неё
    # же. Своя копия числа здесь и в сентинелях разметки разъехалась бы с
    # `next_offset` молча: вторая страница выдачи начала бы перекрываться с
    # первой или пропускать записи, а экран остался бы исправным на вид.
    page_size = PAGE_SIZE

    # ОТСЕЧКА НЕИЗВЕСТНЫХ ЗНАЧЕНИЙ ОСЕЙ — ТА ЖЕ, ЧТО У ПОЛЬЗОВАТЕЛЬСКИХ
    # МАРШРУТОВ. Значения приезжают строкой запроса — из ссылки, закладки или
    # чужого сообщения. Без отсечки мусорное значение давало бы пустой список,
    # в котором НИ ОДИН чипс не отмечен активным, а сырая строка уезжала бы в
    # `filter_params` — то есть в сентинель прокрутки и в контекст шаблона как
    # действующий фильтр. Инъекции здесь нет (значения связываются параметрами),
    # но экран получается нечитаемым ровно так же, как получался бы у
    # пользователя, — а админка смотрит на ТУ ЖЕ историю.
    status = clean_choice(status, STATUS_VALUES)
    messenger = clean_choice(messenger, MESSENGER_VALUES)
    period = clean_choice(period, PERIOD_VALUES)
    account_id_int = parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user_id)
    )
    # Владелец записей — target_user, но «сегодня» отсчитывается от полуночи
    # ТОГО, КТО СМОТРИТ: границу дня задаёт часовой пояс читателя экрана.
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=admin,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result.all())

    has_next = len(rows) > page_size
    rows = rows[:page_size]

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
        select(MessengerAccount).where(MessengerAccount.user_id == user_id)
    )
    all_accounts = accounts_result.scalars().all()
    filter_params = history_filter_params(status, messenger, account_id_int, period)

    return templates.TemplateResponse(
        "admin/user_history.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "logs": logs,
            "all_accounts": all_accounts,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "next_offset": offset + len(logs),
            "detail_base_path": f"/admin/users/{user_id}/history",
        },
    )


@router.get("/users/{user_id}/history/partial", response_class=HTMLResponse)
async def admin_user_history_partial(
    request: Request,
    user_id: int,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)
    # Отсечка стоит и здесь: паршал прокрутки — ВТОРОЙ вход на те же оси, и
    # значение приезжает к нему из адреса сентинеля. Пропущенная тут, она
    # позволила бы мусору дожить до второй страницы выдачи.
    status = clean_choice(status, STATUS_VALUES)
    messenger = clean_choice(messenger, MESSENGER_VALUES)
    period = clean_choice(period, PERIOD_VALUES)
    account_id_int = parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user_id)
    )
    # Владелец записей — target_user, но «сегодня» отсчитывается от полуночи
    # ТОГО, КТО СМОТРИТ: границу дня задаёт часовой пояс читателя экрана.
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=admin,
    )
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
    filter_params = history_filter_params(status, messenger, account_id_int, period)
    return templates.TemplateResponse(
        "admin/history_partial_cards.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
            "logs": logs,
            "has_next": has_next,
            "next_offset": offset + limit,
            # Размер страницы уезжает в сентинель из контекста — тем же
            # значением, которым выбрана ЭТА порция.
            "page_size": limit,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            "detail_base_path": f"/admin/users/{user_id}/history",
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


@router.post("/users/{user_id}/balance")
async def admin_add_balance(
    request: Request,
    user_id: int,
    amount: int = Form(...),
    description: str = Form(""),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    await add_messages(
        db,
        user_id,
        amount,
        type="admin_adjustment",
        description=description or f"Пополнение администратором ({admin.email})",
    )
    await db.commit()
    await invalidate_balance_cache(user_id)

    return RedirectResponse(
        url=f"/admin/users/{user_id}", status_code=302
    )


@router.post("/users/{user_id}/unlimited")
async def admin_toggle_unlimited(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    bal = await get_or_create_balance(db, user_id)
    bal.is_unlimited = not bal.is_unlimited
    await db.commit()
    await invalidate_balance_cache(user_id)

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


@router.get("/groups-info", response_class=HTMLResponse)
async def admin_groups_info(
    request: Request,
    q: str = "",
    messenger: str = "",
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    page_size = 30
    repo = GroupInfoRepository(db)

    items, total = await repo.search(
        q=q, messenger_type=messenger, offset=offset, limit=page_size
    )
    counts = await repo.count_by_type()
    total_all = sum(counts.values())

    has_next = offset + page_size < total
    has_prev = offset > 0

    return templates.TemplateResponse(
        "admin/groups_info.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "items": items,
            "total": total,
            "total_all": total_all,
            "counts": counts,
            "q": q,
            "messenger": messenger,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    )


@router.get("/groups-info/{item_id}", response_class=HTMLResponse)
async def admin_group_info_detail(
    request: Request,
    item_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = GroupInfoRepository(db)
    item = await repo.get_by_id(item_id)
    if not item:
        return RedirectResponse(url="/admin/groups-info", status_code=302)

    return templates.TemplateResponse(
        "admin/group_info_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "item": item,
        },
    )

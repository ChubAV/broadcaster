from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    activity_heatmap,
    send_metrics,
    upcoming_sends,
)
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.send_log import SendLog
from app.pages.common import (
    _get_timezone_for_user,
    check_is_admin,
    get_user_from_cookie,
    templates,
)

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

    # Плитки. Страница агрегатов НЕ СЧИТАЕТ: восемь чисел приходят одним
    # запросом из модуля аналитики, который зовут и история, и Фаза 6 (D-35).
    # Три счётчика сущностей и отправки «от UTC-полуночи» отсюда сняты по
    # D-01/D-02 — счётчики дублировали боковое меню, а полночь показывала почти
    # ноль в первые часы суток независимо от того, работала система ночью.
    metrics = await send_metrics(db, user_id=user.id)

    # Heatmap активности за неделю (DASH-04). Таймзона приезжает СЮДА, а не
    # берётся внутри модуля: локальный час ячейки — свойство ЧИТАТЕЛЯ экрана, и
    # в админке Фазы 6 тот же модуль позовут с зоной администратора, а не
    # просматриваемого пользователя.
    heatmap_view = await activity_heatmap(
        db, user_id=user.id, tz=_get_timezone_for_user(user)
    )

    # Ближайшие отправки (DASH-02). Пометки причин считает модуль: страница не
    # знает ни про черновик объявления, ни про статус аккаунта, ни про флаги
    # групп — иначе то же правило пришлось бы повторить в Фазе 6.
    upcoming = await upcoming_sends(db, user_id=user.id)

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
            "metrics": metrics,
            "heatmap_view": heatmap_view,
            "upcoming": upcoming,
            "recent_sends": recent_sends,
            "active_page": "dashboard",
        },
    )

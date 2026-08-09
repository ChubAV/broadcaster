from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import TIMEZONE_CHOICES, VALID_TIMEZONES
from app.dependencies import get_db, get_settings
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.services.schedule_service import compute_next_run_at
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


def _build_schedule_items(result, user, tz):
    """Build schedule items with next_run_local from raw query result."""
    items = [
        {"schedule": r.Schedule, "ad_title": r.ad_title, "messenger_type": r.messenger_type}
        for r in result
    ]
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    for item in items:
        sched = item["schedule"]
        if sched.next_run_at:
            item["next_run_local"] = sched.next_run_at.astimezone(tz)
            item["tz_label"] = tz_name.split("/")[-1] if "/" in tz_name else tz_name
        else:
            item["next_run_local"] = None
            item["tz_label"] = ""
    return items


@router.get("/schedules/partial", response_class=HTMLResponse)
async def schedules_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = ZoneInfo(tz_name)
    result = await db.execute(
        select(Schedule, Ad.title.label("ad_title"), MessengerAccount.type.label("messenger_type"))
        .join(Ad, Schedule.ad_id == Ad.id)
        # outer join: расписание с удалённым аккаунтом (account_id IS NULL)
        # должно остаться видимым (issue #35)
        .join(MessengerAccount, Schedule.account_id == MessengerAccount.id, isouter=True)
        .where(Ad.user_id == user.id)
        .order_by(Schedule.id)
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list(result)
    has_next = len(rows) > limit
    schedules = _build_schedule_items(rows[:limit], user, tz)
    return templates.TemplateResponse(
        "schedules/partial_cards.html",
        {
            "request": request,
            "user": user,
            "schedules": schedules,
            "has_next": has_next,
            "next_offset": offset + limit,
        },
    )


@router.get("/schedules", response_class=HTMLResponse)
async def schedules_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = ZoneInfo(tz_name)
    result = await db.execute(
        select(Schedule, Ad.title.label("ad_title"), MessengerAccount.type.label("messenger_type"))
        .join(Ad, Schedule.ad_id == Ad.id)
        # outer join: расписание с удалённым аккаунтом (account_id IS NULL)
        # должно остаться видимым (issue #35)
        .join(MessengerAccount, Schedule.account_id == MessengerAccount.id, isouter=True)
        .where(Ad.user_id == user.id)
        .order_by(Schedule.id)
        .limit(PAGE_SIZE + 1)
    )
    rows = list(result)
    has_next = len(rows) > PAGE_SIZE
    schedules = _build_schedule_items(rows[:PAGE_SIZE], user, tz)
    return templates.TemplateResponse(
        "schedules/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "schedules": schedules,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "schedules",
        },
    )


@router.get("/schedules/new", response_class=HTMLResponse)
async def schedules_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    ads = (
        await db.execute(
            select(Ad).where(Ad.user_id == user.id, Ad.is_active == True)  # noqa: E712
        )
    ).scalars().all()
    accounts = (
        await db.execute(
            select(MessengerAccount).where(MessengerAccount.user_id == user.id)
        )
    ).scalars().all()
    groups = (
        await db.execute(
            select(Group).where(Group.user_id == user.id, Group.is_active == True)  # noqa: E712
        )
    ).scalars().all()

    default_timezone = None
    if user.timezone in VALID_TIMEZONES:
        default_timezone = user.timezone

    return templates.TemplateResponse(
        "schedules/form.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "schedule": None,
            "ads": ads,
            "accounts": accounts,
            "groups": groups,
            "timezone_choices": TIMEZONE_CHOICES,
            "default_timezone": default_timezone,
            "active_page": "schedules",
        },
    )


@router.post("/schedules/new")
async def schedules_create(
    request: Request,
    ad_id: int = Form(...),
    account_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form_data = await request.form()
    group_ids = [int(g) for g in form_data.getlist("group_ids")]
    days_of_week = [int(d) for d in form_data.getlist("days_of_week")]
    times_of_day = [t for t in form_data.getlist("times_of_day") if t]

    # Validate that all groups belong to the selected account
    if group_ids:
        valid_groups = (
            await db.execute(
                select(Group.id).where(
                    Group.id.in_(group_ids),
                    Group.account_id == account_id,
                    Group.user_id == user.id,
                )
            )
        ).scalars().all()
        group_ids = [gid for gid in group_ids if gid in valid_groups]

    tz = form_data.get("timezone", "UTC")
    if tz not in VALID_TIMEZONES:
        tz = "UTC"

    next_run = compute_next_run_at(
        days_of_week=days_of_week, times_of_day=times_of_day, tz_name=tz
    )

    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=group_ids,
        days_of_week=days_of_week,
        times_of_day=times_of_day,
        timezone=tz,
        next_run_at=next_run,
    )
    db.add(schedule)
    await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


@router.get("/schedules/{schedule_id}/edit", response_class=HTMLResponse)
async def schedules_edit(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return RedirectResponse(url="/schedules", status_code=302)

    ads = (
        await db.execute(
            select(Ad).where(Ad.user_id == user.id, Ad.is_active == True)  # noqa: E712
        )
    ).scalars().all()
    accounts = (
        await db.execute(
            select(MessengerAccount).where(MessengerAccount.user_id == user.id)
        )
    ).scalars().all()
    groups = (
        await db.execute(
            select(Group).where(Group.user_id == user.id, Group.is_active == True)  # noqa: E712
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "schedules/form.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "schedule": schedule,
            "ads": ads,
            "accounts": accounts,
            "groups": groups,
            "timezone_choices": TIMEZONE_CHOICES,
            "active_page": "schedules",
        },
    )


@router.post("/schedules/{schedule_id}/edit")
async def schedules_update(
    request: Request,
    schedule_id: int,
    ad_id: int = Form(...),
    account_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return RedirectResponse(url="/schedules", status_code=302)

    form_data = await request.form()
    group_ids = [int(g) for g in form_data.getlist("group_ids")]
    days_of_week = [int(d) for d in form_data.getlist("days_of_week")]
    times_of_day = [t for t in form_data.getlist("times_of_day") if t]

    # Validate that all groups belong to the selected account
    if group_ids:
        valid_groups = (
            await db.execute(
                select(Group.id).where(
                    Group.id.in_(group_ids),
                    Group.account_id == account_id,
                    Group.user_id == user.id,
                )
            )
        ).scalars().all()
        group_ids = [gid for gid in group_ids if gid in valid_groups]

    tz = form_data.get("timezone", schedule.timezone)
    if tz not in VALID_TIMEZONES:
        tz = schedule.timezone

    schedule.ad_id = ad_id
    schedule.account_id = account_id
    schedule.group_ids = group_ids
    schedule.days_of_week = days_of_week
    schedule.times_of_day = times_of_day
    schedule.timezone = tz
    schedule.next_run_at = compute_next_run_at(
        days_of_week=days_of_week, times_of_day=times_of_day, tz_name=tz
    )
    await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


@router.post("/schedules/{schedule_id}/toggle")
async def schedules_toggle(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    # issue #35: отвязанное расписание нельзя возобновить, пока пользователь не
    # привяжет аккаунт на форме редактирования. Пауза активного не блокируется.
    resume_blocked = (
        schedule is not None
        and not schedule.is_active
        and schedule.account_id is None
    )
    if schedule and not resume_blocked:
        schedule.is_active = not schedule.is_active
        if schedule.is_active:
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
            )
        else:
            schedule.next_run_at = None
        await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


@router.post("/schedules/{schedule_id}/delete")
async def schedules_delete(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if schedule:
        await db.delete(schedule)
        await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)

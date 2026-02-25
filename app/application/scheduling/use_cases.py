from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.schedule_service import compute_next_run_at


@dataclass(slots=True)
class DispatchTask:
    type: str
    ad_id: int
    group_id: int
    account_id: int
    schedule_id: int


async def collect_due_schedules(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    check_limit,
) -> list[DispatchTask]:
    """Логика выбора due-расписаний и подготовки задач отправки.

    Поведение повторяет текущее check_schedules_async, но без побочных эффектов вне БД.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    result = await session.execute(
        select(Schedule)
        .options(joinedload(Schedule.ad), joinedload(Schedule.account))
        .where(
            Schedule.is_active == True,  # noqa: E712
            Schedule.next_run_at <= now,
        )
    )
    schedules = result.unique().scalars().all()

    if not schedules:
        return []

    tasks_to_dispatch: list[DispatchTask] = []
    checked_users: dict[int, tuple[bool, str]] = {}

    for schedule in schedules:
        ad = schedule.ad
        account = schedule.account

        if not ad or not account or account.status != "active":
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
                now=now,
            )
            continue

        user_id = ad.user_id
        if user_id not in checked_users:
            checked_users[user_id] = await check_limit(session, user_id, "send")

        allowed, _reason = checked_users[user_id]
        if not allowed:
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
                now=now,
            )
            continue

        for group_id in schedule.group_ids or []:
            tasks_to_dispatch.append(
                DispatchTask(
                    type=account.type,
                    ad_id=schedule.ad_id,
                    group_id=group_id,
                    account_id=schedule.account_id,
                    schedule_id=schedule.id,
                )
            )

        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name=schedule.timezone,
            now=now,
        )

    await session.commit()
    return tasks_to_dispatch


async def send_message_once(
    session: AsyncSession,
    *,
    ad_id: int,
    group_id: int,
    account_id: int,
    schedule_id: int,
    messenger_factory: Any,
    settings: Any,
) -> None:
    """Общая доменная логика отправки одного сообщения.

    Функция не знает о Celery, только о БД и messenger-интерфейсе.
    """
    ad = await session.get(Ad, ad_id)
    group = await session.get(Group, group_id)
    account = await session.get(MessengerAccount, account_id)

    if not ad or not group or not account:
        log_entry = SendLog(
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="fail",
            error_message="Missing ad, group, or account",
        )
        session.add(log_entry)
        await session.commit()
        return

    if account.status != "active":
        log_entry = SendLog(
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="account_disconnected",
            error_message=f"Account {account.id} is {account.status}",
        )
        session.add(log_entry)
        await session.commit()
        return

    images: list[str] | None = None
    if ad.images:
        from app.services.s3 import get_image_url  # локальный импорт чтобы избежать циклов

        s3_public_url = settings.s3_public_url
        images = [get_image_url(img, s3_public_url) for img in ad.images]

    try:
        messenger = messenger_factory(account, settings)
    except ValueError as e:
        # Некорректная конфигурация мессенджера — считаем невосстанавливаемой ошибкой.
        log_entry = SendLog(
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="fail",
            error_message=str(e),
        )
        session.add(log_entry)
        await session.commit()
        return

    result = await messenger.send_message(
        group_id=group.group_external_id,
        text=ad.text,
        images=images,
    )

    log_entry = SendLog(
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="ok" if result.get("ok") else "fail",
        error_message=result.get("error"),
    )
    session.add(log_entry)
    await session.commit()

    # Ошибка с флагом no_retry помечает группу, но не выбрасывает исключение.
    if not result.get("ok"):
        error = result.get("error")
        if result.get("no_retry"):
            group.last_error = error
            group.error_at = datetime.now(timezone.utc)
            await session.commit()
        else:
            raise Exception(f"Send failed: {error}")
    else:
        if group.last_error:
            group.last_error = None
            group.error_at = None
            await session.commit()


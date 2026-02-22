import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_engine, get_session_factory
from app.models.schedule import Schedule
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.config import get_settings
from app.services.messenger_factory import create_messenger
from app.services.schedule_service import compute_next_run_at
from app.services.billing_service import check_limit
from celery import shared_task


async def check_schedules_async(session: AsyncSession):
    """Find all due schedules and dispatch sends."""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Schedule).where(
            Schedule.is_active == True,
            Schedule.next_run_at <= now,
        )
    )
    schedules = result.scalars().all()

    tasks = []
    for schedule in schedules:
        # Check send limit for the ad's user
        ad = await session.get(Ad, schedule.ad_id)
        if ad:
            allowed, reason = await check_limit(session, ad.user_id, "send")
            if not allowed:
                # Update next_run_at even when skipping so we don't retry immediately
                next_run = compute_next_run_at(
                    days_of_week=schedule.days_of_week,
                    times_of_day=schedule.times_of_day,
                    tz_name="UTC",
                    now=now,
                )
                schedule.next_run_at = next_run
                continue  # skip this schedule

        for group_id in schedule.group_ids:
            tasks.append(
                send_ad_to_group_async(
                    session=session,
                    schedule_id=schedule.id,
                    ad_id=schedule.ad_id,
                    group_id=group_id,
                    account_id=schedule.account_id,
                )
            )

        # Update next_run_at
        next_run = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name="UTC",
            now=now,
        )
        schedule.next_run_at = next_run

    await session.commit()

    # Execute all send tasks
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_ad_to_group_async(
    session: AsyncSession,
    schedule_id: int,
    ad_id: int,
    group_id: int,
    account_id: int,
):
    """Send ad to a single group and log the result."""
    # Load data
    ad = await session.get(Ad, ad_id)
    group = await session.get(Group, group_id)
    account = await session.get(MessengerAccount, account_id)

    if not ad or not group or not account:
        log = SendLog(
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="fail",
            error_message="Missing ad, group, or account",
        )
        session.add(log)
        await session.commit()
        return

    if account.status != "active":
        log = SendLog(
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            status="account_disconnected",
            error_message=f"Account {account.id} is {account.status}",
        )
        session.add(log)
        await session.commit()
        return

    # Build S3 URLs for images
    images = None
    if ad.images:
        from app.services.s3 import get_image_url
        s3_public_url = get_settings().s3_public_url
        images = [get_image_url(img, s3_public_url) for img in ad.images]

    # Send via messenger adapter
    messenger = create_messenger(account, get_settings())
    result = await messenger.send_message(
        group_id=group.group_external_id,
        text=ad.text,
        images=images,
    )

    log = SendLog(
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        status="ok" if result["ok"] else "fail",
        error_message=result.get("error"),
    )
    session.add(log)
    await session.commit()


@shared_task(name="app.worker.tasks.check_schedules")
def check_schedules():
    """Celery task: check all due schedules and dispatch sends."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        async with session_factory() as session:
            await check_schedules_async(session)
        await engine.dispose()

    asyncio.run(_run())

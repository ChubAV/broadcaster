import asyncio
import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.billing_cache import check_limit_cached
from app.services.messenger_factory import create_messenger
from app.services.s3 import get_image_url
from app.services.schedule_service import compute_next_run_at

logger = logging.getLogger(__name__)


async def dispatch_send_tasks(
    tasks_to_dispatch: list[dict],
) -> None:
    """Dispatch individual Celery tasks for each send.

    WA tasks are grouped by session_id and dispatched together so they
    appear consecutively in the FIFO queue — the bridge keeps the Chromium
    session loaded while processing the batch.
    """
    from collections import defaultdict

    # Group WA tasks by session for affinity ordering
    wa_by_session: dict[int, list[dict]] = defaultdict(list)
    tg_tasks: list[dict] = []

    for task_info in tasks_to_dispatch:
        if task_info["type"] == "wa":
            wa_by_session[task_info["account_id"]].append(task_info)
        else:
            tg_tasks.append(task_info)

    # Dispatch TG tasks
    for task_info in tg_tasks:
        args = [task_info["ad_id"], task_info["group_id"], task_info["account_id"], task_info["schedule_id"]]
        send_telegram_message.apply_async(args=args, queue="telegram")

    # Dispatch WA tasks grouped by session (FIFO ordering = session affinity)
    for session_id, session_tasks in wa_by_session.items():
        for task_info in session_tasks:
            args = [task_info["ad_id"], task_info["group_id"], task_info["account_id"], task_info["schedule_id"]]
            send_whatsapp_message.apply_async(args=args, queue="whatsapp")


async def check_schedules_async(session: AsyncSession):
    """Find all due schedules and dispatch individual send tasks."""
    now = datetime.now(timezone.utc)

    # Eager load ad and account to avoid N+1
    result = await session.execute(
        select(Schedule)
        .options(joinedload(Schedule.ad), joinedload(Schedule.account))
        .where(
            Schedule.is_active == True,
            Schedule.next_run_at <= now,
        )
    )
    schedules = result.unique().scalars().all()

    if not schedules:
        return

    tasks_to_dispatch = []
    checked_users: dict[int, tuple[bool, str]] = {}

    for schedule in schedules:
        ad = schedule.ad
        account = schedule.account

        if not ad or not account or account.status != "active":
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name="UTC",
                now=now,
            )
            continue

        # Check billing limit (cached per user)
        user_id = ad.user_id
        if user_id not in checked_users:
            checked_users[user_id] = await check_limit_cached(session, user_id, "send")

        allowed, reason = checked_users[user_id]
        if not allowed:
            logger.info("User %d skipped: %s", user_id, reason)
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name="UTC",
                now=now,
            )
            continue

        for group_id in schedule.group_ids:
            tasks_to_dispatch.append({
                "type": account.type,
                "ad_id": schedule.ad_id,
                "group_id": group_id,
                "account_id": schedule.account_id,
                "schedule_id": schedule.id,
            })

        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name="UTC",
            now=now,
        )

    # Batch commit all next_run_at updates
    await session.commit()

    # Dispatch all send tasks
    if tasks_to_dispatch:
        await dispatch_send_tasks(tasks_to_dispatch)
        logger.info("Dispatched %d send tasks", len(tasks_to_dispatch))


async def _send_message(ad_id: int, group_id: int, account_id: int, schedule_id: int):
    """Shared send logic for both Telegram and WhatsApp tasks."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        ad = await session.get(Ad, ad_id)
        group = await session.get(Group, group_id)
        account = await session.get(MessengerAccount, account_id)

        if not ad or not group or not account:
            log = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="fail", error_message="Missing ad, group, or account",
            )
            session.add(log)
            await session.commit()
            return

        if account.status != "active":
            log = SendLog(
                schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
                status="account_disconnected",
                error_message=f"Account {account.id} is {account.status}",
            )
            session.add(log)
            await session.commit()
            return

        images = None
        if ad.images:
            s3_public_url = settings.s3_public_url
            images = [get_image_url(img, s3_public_url) for img in ad.images]

        messenger = create_messenger(account, settings)
        result = await messenger.send_message(
            group_id=group.group_external_id,
            text=ad.text,
            images=images,
        )

        log = SendLog(
            schedule_id=schedule_id, ad_id=ad_id, group_id=group_id,
            status="ok" if result["ok"] else "fail",
            error_message=result.get("error"),
        )
        session.add(log)
        await session.commit()

        if not result["ok"]:
            raise Exception(f"Send failed: {result.get('error')}")

    await engine.dispose()


@shared_task(
    name="app.worker.tasks.send_telegram_message",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="20/m",
)
def send_telegram_message(self, ad_id, group_id, account_id, schedule_id):
    """Send a single Telegram message. Auto-retries with backoff."""
    asyncio.run(_send_message(ad_id, group_id, account_id, schedule_id))


@shared_task(
    name="app.worker.tasks.send_whatsapp_message",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="30/m",
)
def send_whatsapp_message(self, ad_id, group_id, account_id, schedule_id):
    """Send a single WhatsApp message. Auto-retries with backoff."""
    asyncio.run(_send_message(ad_id, group_id, account_id, schedule_id))


@shared_task(name="app.worker.tasks.check_schedules")
def check_schedules():
    """Celery task: check all due schedules and dispatch individual send tasks."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        async with session_factory() as session:
            await check_schedules_async(session)
        await engine.dispose()

    asyncio.run(_run())

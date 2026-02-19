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
from app.messengers.telegram_bot import TelegramBotMessenger
from app.messengers.telegram_user import TelegramUserMessenger
from app.messengers.whatsapp import WhatsAppMessenger
from app.services.schedule_service import compute_next_run_at


def get_messenger(account: MessengerAccount):
    """Factory: create messenger adapter based on account type."""
    if account.type == "tg_bot":
        return TelegramBotMessenger(token=account.credentials)
    elif account.type == "tg_user":
        # For userbot, credentials should contain session_string
        # api_id and api_hash would come from config, but for simplicity
        # we store them in session_data as JSON
        import json
        meta = json.loads(account.session_data or "{}")
        return TelegramUserMessenger(
            session_string=account.credentials,
            api_id=meta.get("api_id", 0),
            api_hash=meta.get("api_hash", ""),
        )
    elif account.type == "wa":
        from app.config import Settings
        settings = Settings()
        return WhatsAppMessenger(bridge_url=settings.wa_bridge_url)
    else:
        raise ValueError(f"Unknown account type: {account.type}")


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

    # Send via messenger adapter
    messenger = get_messenger(account)
    result = await messenger.send_message(
        group_id=group.group_external_id,
        text=ad.text,
        images=ad.images if ad.images else None,
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

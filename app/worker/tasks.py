import asyncio
import structlog
import structlog.contextvars
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
from app.application.scheduling.use_cases import (
    DispatchTask,
    collect_due_schedules,
    send_message_once,
)

logger = structlog.get_logger(__name__)


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
    tasks: list[DispatchTask] = await collect_due_schedules(
        session,
        now=now,
        check_limit=check_limit_cached,
    )
    logger.info("check_schedules_found", now=now.isoformat(), due_count=len(tasks))
    if tasks:
        payloads = [
            {
                "type": task.type,
                "ad_id": task.ad_id,
                "group_id": task.group_id,
                "account_id": task.account_id,
                "schedule_id": task.schedule_id,
            }
            for task in tasks
        ]
        await dispatch_send_tasks(payloads)
        logger.info("send_tasks_dispatched", count=len(tasks))
    else:
        logger.info("no_tasks_to_dispatch")


async def _send_message(ad_id: int, group_id: int, account_id: int, schedule_id: int, task_id: str | None = None):
    """Shared send logic for both Telegram and WhatsApp tasks."""
    log = logger.bind(ad_id=ad_id, group_id=group_id, account_id=account_id, schedule_id=schedule_id)
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        try:
            await send_message_once(
                session,
                ad_id=ad_id,
                group_id=group_id,
                account_id=account_id,
                schedule_id=schedule_id,
                messenger_factory=create_messenger,
                settings=settings,
                task_id=task_id,
            )
            log.info("send_ok")
        except Exception as e:
            log.error("send_failed", error=str(e))
            raise
        finally:
            await engine.dispose()


def _on_send_failure(exc, task_id, args, kwargs, einfo):
    """Log when all retries are exhausted."""
    ad_id, group_id, account_id, schedule_id = args
    logger.error(
        "send_task_final_failure",
        task_id=task_id,
        ad_id=ad_id,
        group_id=group_id,
        account_id=account_id,
        schedule_id=schedule_id,
        error=str(exc),
        exc_info=True,
    )


@shared_task(
    name="app.worker.tasks.send_telegram_message",
    bind=True,
    rate_limit="20/m",
)
def send_telegram_message(self, ad_id, group_id, account_id, schedule_id):
    """Send a single Telegram message. Auto-retries with backoff."""
    task_id = self.request.id
    logger.info(
        "celery_task_start",
        task_name=self.name,
        task_id=task_id,
        queue=getattr(self.request, "delivery_info", {}).get("routing_key"),
    )
    structlog.contextvars.bind_contextvars(task_id=task_id)
    try:
        asyncio.run(_send_message(ad_id, group_id, account_id, schedule_id, task_id=task_id))
    finally:
        structlog.contextvars.unbind_contextvars("task_id")


send_telegram_message.on_failure = _on_send_failure


@shared_task(
    name="app.worker.tasks.send_whatsapp_message",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_backoff_max=30,
    max_retries=3,
    rate_limit="7/m",
)
def send_whatsapp_message(self, ad_id, group_id, account_id, schedule_id):
    """Send a single WhatsApp message. Auto-retries with backoff."""
    task_id = self.request.id
    logger.info(
        "celery_task_start",
        task_name=self.name,
        task_id=task_id,
        queue=getattr(self.request, "delivery_info", {}).get("routing_key"),
    )
    structlog.contextvars.bind_contextvars(task_id=task_id)
    try:
        asyncio.run(_send_message(ad_id, group_id, account_id, schedule_id, task_id=task_id))
    finally:
        structlog.contextvars.unbind_contextvars("task_id")


send_whatsapp_message.on_failure = _on_send_failure


@shared_task(name="app.worker.tasks.check_schedules", bind=True)
def check_schedules(self):
    """Celery task: check all due schedules and dispatch individual send tasks."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        try:
            logger.info(
                "celery_task_start",
                task_name=self.name,
                task_id=self.request.id,
            )
            async with session_factory() as session:
                await check_schedules_async(session)
        except Exception as e:
            logger.error("check_schedules_error", error=str(e), exc_info=True)
            raise
        finally:
            await engine.dispose()

    asyncio.run(_run())


async def _sync_wa_groups_async(account_id: int):
    """Poll bridge for group sync completion, save groups to DB."""
    log = logger.bind(account_id=account_id)
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    from app.messengers.whatsapp import WhatsAppMessenger, get_bridge_url

    POLL_INTERVAL = 15  # seconds
    MAX_POLLS = 40  # 40 * 15s = 10 minutes max

    try:
        bridge_url = get_bridge_url(account_id, settings.wa_bridge_urls)
        messenger = WhatsAppMessenger(bridge_url=bridge_url, session_id=str(account_id))

        for attempt in range(MAX_POLLS):
            sync_data = await messenger.get_sync_status()
            state = sync_data.get("state")
            log.debug("sync_poll", attempt=attempt + 1, state=state)

            if state == "ready":
                groups = sync_data.get("groups") or []
                async with session_factory() as session:
                    account = await session.get(MessengerAccount, account_id)
                    if not account or account.status != "syncing":
                        log.info("sync_skipped", reason="account_not_syncing", status=account.status if account else None)
                        return

                    existing = await session.execute(
                        select(Group.group_external_id).where(
                            Group.account_id == account_id,
                            Group.user_id == account.user_id,
                        )
                    )
                    existing_ids = {row[0] for row in existing}

                    new_count = 0
                    for g in groups:
                        if g["id"] not in existing_ids:
                            session.add(
                                Group(
                                    user_id=account.user_id,
                                    account_id=account_id,
                                    messenger_type="wa",
                                    group_external_id=g["id"],
                                    name=g.get("name") or g["id"],
                                )
                            )
                            new_count += 1

                    account.status = "active"
                    await session.commit()
                    log.info("sync_complete", total_groups=len(groups), new_groups=new_count)
                return

            if state in ("failed", "not_found", "unknown"):
                async with session_factory() as session:
                    account = await session.get(MessengerAccount, account_id)
                    if account and account.status == "syncing":
                        account.status = "sync_failed"
                        await session.commit()
                log.warning("sync_failed", state=state)
                return

            # Still syncing — wait and poll again
            await asyncio.sleep(POLL_INTERVAL)

        # Timeout — max polls reached
        async with session_factory() as session:
            account = await session.get(MessengerAccount, account_id)
            if account and account.status == "syncing":
                account.status = "sync_failed"
                await session.commit()
        log.warning("sync_timeout", max_polls=MAX_POLLS)

    except Exception as e:
        log.error("sync_wa_groups_error", error=str(e), exc_info=True)
        try:
            async with session_factory() as session:
                account = await session.get(MessengerAccount, account_id)
                if account and account.status == "syncing":
                    account.status = "sync_failed"
                    await session.commit()
        except Exception:
            pass
        raise
    finally:
        await engine.dispose()


@shared_task(
    name="app.worker.tasks.sync_wa_groups",
    bind=True,
    max_retries=1,
)
def sync_wa_groups(self, account_id: int):
    """Background task: poll bridge until group sync completes, save to DB."""
    asyncio.run(_sync_wa_groups_async(account_id))

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
from app.services.billing_cache import check_balance_cached, invalidate_balance_cache
from app.services.billing_service import deduct_message
from app.services.messenger_factory import create_messenger
from app.services.s3 import get_image_url
from app.services.schedule_service import compute_next_run_at
from app.application.scheduling.use_cases import (
    DispatchTask,
    collect_due_schedules,
    send_message_once,
)

logger = structlog.get_logger(__name__)


async def dispatch_send_tasks(tasks_to_dispatch: list[DispatchTask]) -> None:
    """Dispatch tasks: Telegram to Celery queue, WhatsApp to Redis per-account queues."""
    import json
    import redis as redis_lib
    from uuid import uuid4

    settings = get_settings()

    tg_tasks: list[DispatchTask] = []
    wa_tasks_by_account: dict[int, list[DispatchTask]] = {}
    max_tasks_by_account: dict[int, list[DispatchTask]] = {}

    for task in tasks_to_dispatch:
        if task.type == "tg_user":
            tg_tasks.append(task)
        elif task.type == "wa":
            wa_tasks_by_account.setdefault(task.account_id, []).append(task)
        elif task.type == "max":
            max_tasks_by_account.setdefault(task.account_id, []).append(task)

    # Dispatch Telegram tasks via Celery (unchanged)
    for task in tg_tasks:
        send_telegram_message.apply_async(
            args=[task.ad_id, task.group_id, task.account_id, task.schedule_id],
            queue="telegram",
        )

    # Dispatch WhatsApp tasks to Redis per-account queues
    if wa_tasks_by_account:
        r = redis_lib.from_url(settings.redis_url)
        try:
            pipe = r.pipeline()
            for account_id, tasks in wa_tasks_by_account.items():
                queue_key = f"wa:queue:{account_id}"
                for task in tasks:
                    task_id = str(uuid4())
                    logger.info("wa_task_created",
                               task_id=task_id,
                               ad_id=task.ad_id,
                               group_id=task.group_id,
                               account_id=task.account_id,
                               schedule_id=task.schedule_id,
                               group_name=task.group_name)
                    payload = json.dumps({
                        "task_id": task_id,
                        "ad_id": task.ad_id,
                        "group_id": task.group_id,
                        "account_id": task.account_id,
                        "schedule_id": task.schedule_id,
                        "user_id": task.user_id,
                        "ad_text": task.ad_text,
                        "ad_title": task.ad_title,
                        "ad_images": task.ad_images,
                        "group_external_id": task.group_external_id,
                        "group_name": task.group_name,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    pipe.rpush(queue_key, payload)
                pipe.sadd("wa:active_accounts", account_id)
            pipe.execute()
            logger.info("wa_tasks_dispatched",
                       account_count=len(wa_tasks_by_account),
                       total_tasks=sum(len(t) for t in wa_tasks_by_account.values()))
        finally:
            r.close()

    # Dispatch MAX tasks to Redis per-account queues
    if max_tasks_by_account:
        r = redis_lib.from_url(settings.redis_url)
        try:
            pipe = r.pipeline()
            for account_id, tasks in max_tasks_by_account.items():
                queue_key = f"max:queue:{account_id}"
                for task in tasks:
                    task_id = str(uuid4())
                    logger.info("max_task_created",
                               task_id=task_id,
                               ad_id=task.ad_id,
                               group_id=task.group_id,
                               account_id=task.account_id,
                               schedule_id=task.schedule_id,
                               group_name=task.group_name)
                    payload = json.dumps({
                        "task_id": task_id,
                        "ad_id": task.ad_id,
                        "group_id": task.group_id,
                        "account_id": task.account_id,
                        "schedule_id": task.schedule_id,
                        "user_id": task.user_id,
                        "ad_text": task.ad_text,
                        "ad_title": task.ad_title,
                        "ad_images": task.ad_images,
                        "group_external_id": task.group_external_id,
                        "group_name": task.group_name,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    pipe.rpush(queue_key, payload)
                pipe.sadd("max:active_accounts", account_id)
            pipe.execute()
            logger.info("max_tasks_dispatched",
                       account_count=len(max_tasks_by_account),
                       total_tasks=sum(len(t) for t in max_tasks_by_account.values()))
        finally:
            r.close()

    total = len(tg_tasks) + sum(len(t) for t in wa_tasks_by_account.values()) + sum(len(t) for t in max_tasks_by_account.values())
    logger.info("send_tasks_dispatched", total=total, tg=len(tg_tasks),
               wa=sum(len(t) for t in wa_tasks_by_account.values()),
               max=sum(len(t) for t in max_tasks_by_account.values()))


async def check_schedules_async(session: AsyncSession):
    """Find all due schedules and dispatch individual send tasks."""
    now = datetime.now(timezone.utc)
    tasks: list[DispatchTask] = await collect_due_schedules(
        session,
        now=now,
        check_limit=check_balance_cached,
    )
    logger.info("check_schedules_found", now=now.isoformat(), due_count=len(tasks))
    if tasks:
        await dispatch_send_tasks(tasks)
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

    from app.messengers.whatsapp import WhatsAppMessenger

    POLL_INTERVAL = 15  # seconds
    MAX_POLLS = 40  # 40 * 15s = 10 minutes max

    try:
        messenger = WhatsAppMessenger(session_id=str(account_id))

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
                    seen = set(existing_ids)
                    for g in groups:
                        if g["id"] not in seen:
                            seen.add(g["id"])
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


async def _sync_max_groups_async(account_id: int):
    """Poll MAX worker for group sync completion, save groups to DB."""
    log = logger.bind(account_id=account_id)
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    from app.messengers.max import MaxMessenger

    POLL_INTERVAL = 15  # seconds
    MAX_POLLS = 40  # 40 * 15s = 10 minutes max

    try:
        messenger = MaxMessenger(session_id=str(account_id))

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
                    seen = set(existing_ids)
                    for g in groups:
                        if g["id"] not in seen:
                            seen.add(g["id"])
                            session.add(
                                Group(
                                    user_id=account.user_id,
                                    account_id=account_id,
                                    messenger_type="max",
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
        log.error("sync_max_groups_error", error=str(e), exc_info=True)
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
    name="app.worker.tasks.sync_max_groups",
    bind=True,
    max_retries=1,
)
def sync_max_groups(self, account_id: int):
    """Background task: poll MAX worker until group sync completes, save to DB."""
    asyncio.run(_sync_max_groups_async(account_id))


@shared_task(name="app.worker.tasks.manage_wa_containers")
def manage_wa_containers():
    """Check Redis queues and start/cleanup wa-worker containers."""
    import redis as redis_lib
    from app.services.wa_container_manager import (
        start_container,
        cleanup_exited_containers,
    )

    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)

    try:
        active_accounts = r.smembers("wa:active_accounts")

        for raw_id in active_accounts:
            account_id = int(raw_id)
            queue_key = f"wa:queue:{account_id}"
            queue_len = r.llen(queue_key)

            if queue_len > 0:
                endpoint = start_container(account_id)
                if endpoint:
                    r.set(f"wa:endpoint:{account_id}", endpoint, ex=420)
                    logger.info("container_ensured", account_id=account_id, queue_len=queue_len)
            else:
                r.srem("wa:active_accounts", account_id)
                r.delete(f"wa:endpoint:{account_id}")

        cleanup_exited_containers()

    except Exception as e:
        logger.error("manage_wa_containers_error", error=str(e), exc_info=True)
    finally:
        r.close()


@shared_task(name="app.worker.tasks.manage_max_containers")
def manage_max_containers():
    """Check Redis queues and start/cleanup max-worker containers."""
    import redis as redis_lib
    from app.services.max_container_manager import (
        ensure_container_for_pending_work,
        cleanup_exited_containers,
    )

    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)

    try:
        active_accounts = r.smembers("max:active_accounts")

        for raw_id in active_accounts:
            account_id = int(raw_id)
            queue_key = f"max:queue:{account_id}"
            queue_len = r.llen(queue_key)

            if queue_len > 0:
                endpoint = ensure_container_for_pending_work(account_id, r)
                if endpoint:
                    r.set(f"max:endpoint:{account_id}", endpoint, ex=420)
                    logger.info("container_ensured", account_id=account_id, queue_len=queue_len)
                else:
                    r.delete(f"max:endpoint:{account_id}")
            else:
                r.srem("max:active_accounts", account_id)
                r.delete(f"max:endpoint:{account_id}")

        cleanup_exited_containers()

    except Exception as e:
        logger.error("manage_max_containers_error", error=str(e), exc_info=True)
    finally:
        r.close()


@shared_task(name="app.worker.tasks.process_wa_results")
def process_wa_results():
    """Read send results from Redis and write SendLog entries to DB."""
    import json
    import redis as redis_lib

    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)

    try:
        results = []
        for _ in range(100):
            raw = r.lpop("wa:results")
            if not raw:
                break
            try:
                results.append(json.loads(raw))
            except json.JSONDecodeError as e:
                logger.error("result_parse_error", raw=str(raw)[:200], error=str(e))

        if not results:
            return

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_process_results_async(results))
        finally:
            loop.close()

    except Exception as e:
        logger.error("process_wa_results_error", error=str(e), exc_info=True)
    finally:
        r.close()


async def _process_results_async(results: list[dict]):
    """Write batch of results to database."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        for result in results:
            try:
                # Use original S3 keys from Ad, not full URLs from wa-worker
                ad_images = result.get("ad_images")
                ad_id = result.get("ad_id")
                if ad_id:
                    ad = await session.get(Ad, ad_id)
                    if ad and ad.images:
                        ad_images = ad.images

                send_log = SendLog(
                    user_id=result["user_id"],
                    schedule_id=result.get("schedule_id"),
                    ad_id=ad_id,
                    group_id=result.get("group_id"),
                    task_id=result.get("task_id"),
                    status=result["status"],
                    error_message=result.get("error_message"),
                    messenger_type="wa",
                    ad_title=result.get("ad_title"),
                    ad_text=result.get("ad_text"),
                    ad_images=ad_images,
                    group_name=result.get("group_name"),
                )
                session.add(send_log)

                if result["status"] == "ok" and result.get("user_id"):
                    await deduct_message(session, result["user_id"])
                    await invalidate_balance_cache(result["user_id"])

                group_id = result.get("group_id")
                if group_id:
                    group = await session.get(Group, group_id)
                    if group:
                        if result.get("no_retry"):
                            group.last_error = result.get("error_message")
                            group.error_at = datetime.now(timezone.utc)
                        elif result["status"] == "ok":
                            group.last_error = None
                            group.error_at = None

            except Exception as e:
                logger.error("result_write_error", task_id=result.get("task_id"), error=str(e))
                continue

            logger.info("wa_result_recorded",
                       task_id=result.get("task_id"),
                       status=result["status"],
                       ad_id=result.get("ad_id"),
                       group_id=result.get("group_id"),
                       account_id=result.get("account_id"),
                       error_message=result.get("error_message"))

        await session.commit()
        logger.info("results_processed", count=len(results))

    await engine.dispose()


@shared_task(name="app.worker.tasks.process_max_results")
def process_max_results():
    """Read send results from Redis and write SendLog entries to DB."""
    import json
    import redis as redis_lib

    settings = get_settings()
    r = redis_lib.from_url(settings.redis_url)

    try:
        results = []
        for _ in range(100):
            raw = r.lpop("max:results")
            if not raw:
                break
            try:
                results.append(json.loads(raw))
            except json.JSONDecodeError as e:
                logger.error("result_parse_error", raw=str(raw)[:200], error=str(e))

        if not results:
            return

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_process_max_results_async(results))
        finally:
            loop.close()

    except Exception as e:
        logger.error("process_max_results_error", error=str(e), exc_info=True)
    finally:
        r.close()


async def _process_max_results_async(results: list[dict]):
    """Write batch of MAX results to database."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        for result in results:
            try:
                # Use original S3 keys from Ad, not full URLs from max-worker
                ad_images = result.get("ad_images")
                ad_id = result.get("ad_id")
                if ad_id:
                    ad = await session.get(Ad, ad_id)
                    if ad and ad.images:
                        ad_images = ad.images

                send_log = SendLog(
                    user_id=result["user_id"],
                    schedule_id=result.get("schedule_id"),
                    ad_id=ad_id,
                    group_id=result.get("group_id"),
                    task_id=result.get("task_id"),
                    status=result["status"],
                    error_message=result.get("error_message"),
                    messenger_type="max",
                    ad_title=result.get("ad_title"),
                    ad_text=result.get("ad_text"),
                    ad_images=ad_images,
                    group_name=result.get("group_name"),
                )
                session.add(send_log)

                if result["status"] == "ok" and result.get("user_id"):
                    await deduct_message(session, result["user_id"])
                    await invalidate_balance_cache(result["user_id"])

                group_id = result.get("group_id")
                if group_id:
                    group = await session.get(Group, group_id)
                    if group:
                        if result.get("no_retry"):
                            group.last_error = result.get("error_message")
                            group.error_at = datetime.now(timezone.utc)
                        elif result["status"] == "ok":
                            group.last_error = None
                            group.error_at = None

            except Exception as e:
                logger.error("result_write_error", task_id=result.get("task_id"), error=str(e))
                continue

            logger.info("max_result_recorded",
                       task_id=result.get("task_id"),
                       status=result["status"],
                       ad_id=result.get("ad_id"),
                       group_id=result.get("group_id"),
                       account_id=result.get("account_id"),
                       error_message=result.get("error_message"))

        await session.commit()
        logger.info("results_processed", count=len(results))

    await engine.dispose()


@shared_task(name="app.worker.tasks.reset_free_monthly_balance")
def reset_free_monthly_balance():
    """Reset free monthly messages for all users."""
    from app.services.billing_service import reset_all_free_monthly

    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        try:
            async with session_factory() as session:
                count = await reset_all_free_monthly(session, settings.free_monthly_messages)
                await session.commit()
                logger.info("free_monthly_reset_complete", users_reset=count)
        except Exception as e:
            logger.error("free_monthly_reset_error", error=str(e), exc_info=True)
            raise
        finally:
            await engine.dispose()

    asyncio.run(_run())


@shared_task(name="app.worker.tasks.send_verification_email")
def send_verification_email_task(email: str, code: str):
    """Send verification code email in background."""
    from app.services.email_service import send_verification_email

    settings = get_settings()
    if not settings.smtp_host:
        logger.warning("smtp_not_configured", email=email)
        return

    asyncio.run(send_verification_email(
        to_email=email,
        code=code,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        smtp_from=settings.smtp_from,
        smtp_use_tls=settings.smtp_use_tls,
    ))
    logger.info("verification_email_sent", email=email)

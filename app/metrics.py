from prometheus_client import Gauge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription

ACTIVE_SCHEDULES = Gauge(
    "broadcaster_active_schedules",
    "Number of active schedules",
)

ACTIVE_USERS = Gauge(
    "broadcaster_active_users",
    "Number of users with active subscription",
)

MESSAGES_SENT = Gauge(
    "broadcaster_messages_sent_total",
    "Total messages sent (from send_logs)",
    ["messenger", "status"],
)


async def update_business_metrics(session: AsyncSession) -> None:
    """Query the database and update Prometheus gauges with current values."""
    # Active schedules
    result = await session.execute(
        select(func.count()).select_from(Schedule).where(Schedule.is_active.is_(True))
    )
    ACTIVE_SCHEDULES.set(result.scalar_one())

    # Active users (users with active subscription)
    result = await session.execute(
        select(func.count()).select_from(Subscription).where(Subscription.is_active.is_(True))
    )
    ACTIVE_USERS.set(result.scalar_one())

    # Messages sent by messenger type and status
    result = await session.execute(
        select(SendLog.messenger_type, SendLog.status, func.count())
        .where(SendLog.messenger_type.is_not(None))
        .group_by(SendLog.messenger_type, SendLog.status)
    )
    for messenger_type, status, count in result.all():
        MESSAGES_SENT.labels(messenger=messenger_type, status=status).set(count)

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

# ⚠️ СМЫСЛ ЭТОГО ПОКАЗАТЕЛЯ ИЗМЕНИЛСЯ РЕВИЗИЕЙ `0020`, А ЗАПРОС — НЕТ.
#
# До плоской модели строка подписки заводилась ТОЛЬКО подтверждённым платежом,
# поэтому счёт активных строк был счётом ПЛАТЯЩИХ. Ревизия `0020` населила
# строкой всех пользователей без подписки (популяция П-о-1), а пробный срок при
# регистрации заводит её каждому новому, — и то же самое число стало счётом ВСЕХ,
# У КОГО ЕСТЬ ДОСТУП: платящих, пробных и открытых администратором вместе.
#
# Имя ряда и запрос НЕ МЕНЯЮТСЯ намеренно: переименование ряда Prometheus рвёт
# историю графика, а два ряда с разным смыслом под одним именем — худший исход,
# чем один ряд с изменившимся смыслом, названным здесь. Скачок вверх в день
# наката ревизии — ожидаемое событие, а не всплеск продаж. Счёт ПЛАТЯЩИХ ряда в
# проекте больше нет; заводить его — работа фазы, владеющей наблюдаемостью.
ACTIVE_USERS = Gauge(
    "broadcaster_active_users",
    "Number of users with an open access period (paying, trial and comped alike)",
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

    # Users with an open access period — see the note above the gauge: the query
    # is unchanged, its meaning is not.
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

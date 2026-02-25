from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.ad import Ad
from app.models.group import Group
from app.models.send_log import SendLog

PLANS = {
    "free": {"max_ads": 3, "max_groups": 5, "max_sends_per_day": 10},
    "basic": {"max_ads": 20, "max_groups": 50, "max_sends_per_day": 200},
    "pro": {"max_ads": 100, "max_groups": 500, "max_sends_per_day": 2000},
}


def get_plan_limits(plan: str) -> dict:
    return PLANS.get(plan, PLANS["free"])


async def get_user_plan(db: AsyncSession, user_id: int) -> str:
    """Get active plan for user. Returns 'free' if no active subscription."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.is_active == True)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if sub:
        now = datetime.now(timezone.utc)
        expires = sub.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires > now:
            return sub.plan
    return "free"


async def get_usage(db: AsyncSession, user_id: int) -> dict:
    """Get current usage stats for a user."""
    ads_count = (await db.execute(
        select(func.count(Ad.id)).where(Ad.user_id == user_id)
    )).scalar() or 0

    groups_count = (await db.execute(
        select(func.count(Group.id)).where(Group.user_id == user_id)
    )).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    sends_today = (await db.execute(
        select(func.count(SendLog.id))
        .where(
            SendLog.user_id == user_id,
            SendLog.sent_at >= today_start,
            SendLog.status == "ok",
        )
    )).scalar() or 0

    return {
        "ads_count": ads_count,
        "groups_count": groups_count,
        "sends_today": sends_today,
    }


async def check_limit(db: AsyncSession, user_id: int, action: str) -> tuple[bool, str]:
    """Check if user can perform action. Returns (allowed, reason)."""
    plan = await get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    usage = await get_usage(db, user_id)

    if action == "create_ad" and usage["ads_count"] >= limits["max_ads"]:
        return False, f"Ad limit reached ({limits['max_ads']} on {plan} plan)"
    if action == "create_group" and usage["groups_count"] >= limits["max_groups"]:
        return False, f"Group limit reached ({limits['max_groups']} on {plan} plan)"
    if action == "send" and usage["sends_today"] >= limits["max_sends_per_day"]:
        return False, f"Daily send limit reached ({limits['max_sends_per_day']} on {plan} plan)"
    return True, ""


async def set_user_plan(
    db: AsyncSession, user_id: int, plan: str, expires_at: datetime
) -> Subscription:
    """Set user plan. Deactivates any existing active subscription first."""
    # Deactivate existing active subscriptions
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    for sub in result.scalars().all():
        sub.is_active = False

    # Create new subscription
    new_sub = Subscription(
        user_id=user_id,
        plan=plan,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(new_sub)
    await db.commit()
    await db.refresh(new_sub)
    return new_sub

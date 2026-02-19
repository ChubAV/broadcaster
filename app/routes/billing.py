from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.billing_service import get_user_plan, get_plan_limits, get_usage, PLANS

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/plan")
async def get_current_plan(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_user_plan(db, user_id)
    limits = get_plan_limits(plan)
    usage = await get_usage(db, user_id)
    return {"plan": plan, "limits": limits, "usage": usage}


@router.get("/plans")
async def list_plans():
    return {"plans": PLANS}

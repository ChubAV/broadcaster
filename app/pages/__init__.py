from fastapi import APIRouter

from app.pages.auth import router as auth_router
from app.pages.dashboard import router as dashboard_router
from app.pages.ads import router as ads_router
from app.pages.accounts import router as accounts_router
from app.pages.groups import router as groups_router
from app.pages.schedules import router as schedules_router
from app.pages.billing import router as billing_router
from app.pages.history import router as history_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(ads_router)
router.include_router(accounts_router)
router.include_router(groups_router)
router.include_router(schedules_router)
router.include_router(billing_router)
router.include_router(history_router)

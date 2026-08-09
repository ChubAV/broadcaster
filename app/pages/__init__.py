from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.pages.common import get_shell_context, get_user_from_cookie

from app.pages.auth import router as auth_router
from app.pages.dashboard import router as dashboard_router
from app.pages.ads import router as ads_router
from app.pages.accounts import router as accounts_router
from app.pages.groups import router as groups_router
from app.pages.schedules import router as schedules_router
from app.pages.billing import router as billing_router
from app.pages.history import router as history_router
from app.pages.admin import router as admin_router
from app.pages.profile import router as profile_router


async def load_shell_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    """Put the live shell data into request.state.shell for every page route.

    Единая точка подмешивания вместо 26 словарей контекста в обработчиках:
    шаблон всегда получает request, поэтому шелл читает request.state.shell
    без изменений в роутерах. На страницах входа (user is None) зависимость
    возвращается без единого запроса к БД.

    Контекст-процессоры Starlette для этого не подходят: в 0.52.1 они
    вызываются синхронно (context.update(context_processor(request))),
    и async-выборку в них не выполнить.
    """
    user = await get_user_from_cookie(request, db, settings)
    request.state.shell = await get_shell_context(db, user)


router = APIRouter(dependencies=[Depends(load_shell_context)])
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(ads_router)
router.include_router(accounts_router)
router.include_router(groups_router)
router.include_router(schedules_router)
router.include_router(billing_router)
router.include_router(history_router)
router.include_router(admin_router)
router.include_router(profile_router)

import asyncio

import structlog
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.logging_config import setup_logging
from app.config import Settings, get_settings
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError, MessengerConnectionError
from app.database import get_engine, get_session_factory
from app.dependencies import get_current_user_id_with_access, init_db
from app.infrastructure.uow import create_uow_factory
from app.middleware import RequestIdMiddleware
from app.pages.common import bind_image_url_globals
from app.routes.auth import router as auth_router
from app.routes.ads import router as ads_router
from app.routes.uploads import router as uploads_router
from app.routes.accounts import router as accounts_router
from app.routes.schedules import router as schedules_router
from app.routes.history import router as history_router
from app.routes.billing import router as billing_router
from app.pages.dashboard_feed import router as dashboard_feed_router
from app.pages import router as pages_router

logger = structlog.get_logger(__name__)

# Каталог отдаётся целиком, поэтому монтируется только app/static и никогда
# app/ — иначе наружу уходит исходный код (T-01-01).
_static_dir = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)
    init_db(session_factory)
    app.state.uow_factory = create_uow_factory(session_factory)

    # Start background business metrics updater
    from app.metrics import update_business_metrics

    async def _metrics_loop():
        while True:
            try:
                async with session_factory() as session:
                    await update_business_metrics(session)
            except Exception:
                logger.warning("metrics_update_failed", exc_info=True)
            await asyncio.sleep(30)

    metrics_task = asyncio.create_task(_metrics_loop())
    yield
    metrics_task.cancel()
    await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()
    # Шаблонные глобалы изображений привязываются к настройкам, которыми
    # приложение уже владеет (D-21). Без этого они собирали Settings() из
    # окружения процесса в обход create_app(settings=...) и подмены
    # зависимостей — см. комментарий в app/pages/common.py.
    bind_image_url_globals(settings)
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    app = FastAPI(title="Broadcaster", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    # name="static" обязателен — именно он включает url_for('static', path=...)
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
    Instrumentator(
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")
    # ГЕЙТ ДОСТУПА НА JSON-ВХОДЕ ВЕШАЕТСЯ ПЕР-РОУТЕРНО И ПЕРЕЧНЕМ — ТОЧНО ТАК
    # ЖЕ, КАК НА СТРАНИЦАХ (`app/pages/__init__.py`). Причина та же: перечень
    # «кого пускать всегда» длиннее и опаснее перечня «кого закрывать» и ГНИЁТ
    # при добавлении маршрута — новый вход по умолчанию оказался бы закрыт
    # вместе с входом в систему и с денежными чтениями, то есть человек не смог
    # бы ни войти, ни узнать, сколько платить (T-05.1-16).
    #
    # ⚠️ ЧТО РОУТЕР, ДОБАВЛЕННЫЙ БУДУЩИМ ПЛАНОМ БЕЗ ЗАВИСИМОСТИ, НЕ ПРОСКОЧИТ
    # МОЛЧА, держит машинный гейт `tests/test_pages/test_access_gate.py`: он
    # читает ЭТОТ ИСХОДНИК, а не собранное приложение — роутер без зависимости в
    # объекте приложения выглядит совершенно обычно (T-05.1-14). Ручное «не
    # забыть» средством защиты не считается.
    app.include_router(auth_router)
    app.include_router(
        ads_router, dependencies=[Depends(get_current_user_id_with_access)]
    )
    app.include_router(
        uploads_router, dependencies=[Depends(get_current_user_id_with_access)]
    )
    app.include_router(
        accounts_router, dependencies=[Depends(get_current_user_id_with_access)]
    )
    app.include_router(
        schedules_router, dependencies=[Depends(get_current_user_id_with_access)]
    )
    app.include_router(
        history_router, dependencies=[Depends(get_current_user_id_with_access)]
    )
    # Денежный роутер НЕ закрывается гейтом доступа НИКОГДА: там живут и чтения
    # раздела оплаты, и вебхук ЮKassa. Закрыть его значило бы запереть человека
    # в продукте, где единственное открывающее действие само требует доступа, а
    # на вебхуке — остановить приём денег отказом 402 в ответ на уведомление о
    # состоявшемся платеже.
    app.include_router(billing_router)
    # Паршал живой ленты включается ОТДЕЛЬНО и ДО страничного роутера: тот
    # объявлен с зависимостью загрузки контекста шелла на каждом маршруте, а
    # ленте шелл не нужен, и при бессрочном опросе эта цена умножалась бы на
    # число открытых вкладок. Обоснование целиком — в докстринге модуля.
    #
    # ⚠️ ГЕЙТА ДОСТУПА НА ЛЕНТЕ НЕТ СОЗНАТЕЛЬНО, И РЕШЕНИЕ ЗАПИСАНО ЗДЕСЬ, А НЕ
    # ОСТАВЛЕНО УМОЛЧАНИЕМ (T-05.1-15, disposition `accept`). Маршрут, выпавший
    # из общей зависимости молча, — ровно та форма обхода, которую соседний
    # перечень и закрывает, поэтому цена названа тремя фактами. Первое: лента
    # ТОЛЬКО ЧИТАЕТ — она не создаёт ни объявлений, ни расписаний, ни отправок,
    # то есть ценности, за которую берут деньги, через неё не производится.
    # Второе: свой гард ВХОДА она держит сама (`get_user_from_cookie`), поэтому
    # открытой для постороннего она не становится. Третье: опрос бессрочный, и
    # запрос к базе за вердиктом доступа умножался бы на число открытых вкладок
    # каждого пользователя на каждом тике — цена, которой закрытая лента не
    # оправдывает. Что просроченный человек видит СВОЮ ленту и не видит ничего
    # чужого, — допущенное следствие, а не упущение.
    app.include_router(dashboard_feed_router)
    app.include_router(pages_router)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: FastAPIRequest, exc: NotFoundError):
        logger.warning("not_found", error=str(exc))
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: FastAPIRequest, exc: ForbiddenError):
        logger.warning("forbidden", error=str(exc))
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(BillingLimitError)
    async def billing_limit_handler(request: FastAPIRequest, exc: BillingLimitError):
        logger.warning("billing_limit", error=str(exc))
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(MessengerConnectionError)
    async def messenger_error_handler(request: FastAPIRequest, exc: MessengerConnectionError):
        logger.error("messenger_connection_error", error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: FastAPIRequest, exc: Exception):
        logger.error(
            "unhandled_exception",
            error=str(exc),
            exc_type=type(exc).__name__,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

import asyncio

import structlog
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.logging_config import setup_logging
from app.config import Settings, get_settings
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError, MessengerConnectionError
from app.database import get_engine, get_session_factory
from app.dependencies import init_db
from app.infrastructure.uow import create_uow_factory
from app.middleware import RequestIdMiddleware
from app.pages.common import bind_image_url_globals
from app.routes.auth import router as auth_router
from app.routes.ads import router as ads_router
from app.routes.uploads import router as uploads_router
from app.routes.accounts import router as accounts_router
from app.routes.groups import router as groups_router
from app.routes.schedules import router as schedules_router
from app.routes.history import router as history_router
from app.routes.billing import router as billing_router
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
    app.include_router(auth_router)
    app.include_router(ads_router)
    app.include_router(uploads_router)
    app.include_router(accounts_router)
    app.include_router(groups_router)
    app.include_router(schedules_router)
    app.include_router(history_router)
    app.include_router(billing_router)
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

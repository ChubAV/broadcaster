import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)

from app.config import Settings, get_settings
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError, MessengerConnectionError
from app.database import get_engine, get_session_factory
from app.dependencies import init_db
from app.routes.auth import router as auth_router
from app.routes.ads import router as ads_router
from app.routes.uploads import router as uploads_router
from app.routes.accounts import router as accounts_router
from app.routes.groups import router as groups_router
from app.routes.schedules import router as schedules_router
from app.routes.history import router as history_router
from app.routes.billing import router as billing_router
from app.pages import router as pages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)
    init_db(session_factory)
    yield
    await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0", lifespan=lifespan)
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
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: FastAPIRequest, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(BillingLimitError)
    async def billing_limit_handler(request: FastAPIRequest, exc: BillingLimitError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(MessengerConnectionError)
    async def messenger_error_handler(request: FastAPIRequest, exc: MessengerConnectionError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    # Serve uploaded files
    upload_dir = settings.upload_dir if settings else "uploads"
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

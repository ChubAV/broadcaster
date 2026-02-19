from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.ads import router as ads_router
from app.routes.uploads import router as uploads_router
from app.routes.accounts import router as accounts_router
from app.routes.groups import router as groups_router
from app.routes.schedules import router as schedules_router
from app.routes.history import router as history_router
from app.routes.billing import router as billing_router
from app.routes.pages import router as pages_router


def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0")
    app.include_router(auth_router)
    app.include_router(ads_router)
    app.include_router(uploads_router)
    app.include_router(accounts_router)
    app.include_router(groups_router)
    app.include_router(schedules_router)
    app.include_router(history_router)
    app.include_router(billing_router)
    app.include_router(pages_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

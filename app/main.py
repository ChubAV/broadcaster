from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.ads import router as ads_router
from app.routes.uploads import router as uploads_router


def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0")
    app.include_router(auth_router)
    app.include_router(ads_router)
    app.include_router(uploads_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

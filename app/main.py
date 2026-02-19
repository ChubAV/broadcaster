from fastapi import FastAPI
from app.routes.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0")
    app.include_router(auth_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

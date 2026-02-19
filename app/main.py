from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Broadcaster", version="0.1.0")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

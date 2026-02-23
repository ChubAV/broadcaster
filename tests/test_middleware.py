import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.middleware import RequestIdMiddleware


@pytest.mark.asyncio
async def test_request_id_header_added():
    """Middleware adds X-Request-ID to response."""
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/test")

    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) == 32


@pytest.mark.asyncio
async def test_request_id_unique_per_request():
    """Each request gets a unique request_id."""
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.get("/test")
        resp2 = await client.get("/test")

    assert resp1.headers["x-request-id"] != resp2.headers["x-request-id"]

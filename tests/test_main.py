import pytest
from httpx import AsyncClient, ASGITransport
from app.config import Settings
from app.main import create_app


def _test_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
        telegram_api_id=12345,
        telegram_api_hash="test_api_hash",
        wa_bridge_urls=["http://localhost:3000"],
    )


@pytest.mark.asyncio
async def test_health_check():
    app = create_app(settings=_test_settings())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_unhandled_exception_returns_500():
    """Generic exceptions return 500 JSON and include request_id."""
    app = create_app(settings=_test_settings())

    @app.get("/explode")
    async def explode():
        raise RuntimeError("Unexpected error")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/explode")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert "x-request-id" in response.headers

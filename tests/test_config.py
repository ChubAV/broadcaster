from app.config import Settings


def test_settings_defaults():
    s = Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret",
    )
    assert s.app_name == "Broadcaster"
    assert s.database_url == "postgresql+asyncpg://u:p@localhost/db"
    assert s.secret_key == "test-secret"

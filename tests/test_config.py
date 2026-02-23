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


def test_log_level_default():
    """LOG_LEVEL defaults to INFO."""
    from app.config import Settings
    s = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
    )
    assert s.log_level == "INFO"
    assert s.log_format == "json"


def test_log_level_override():
    """LOG_LEVEL can be set via env."""
    import os
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOG_FORMAT"] = "console"
    from app.config import Settings
    s = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test",
    )
    assert s.log_level == "DEBUG"
    assert s.log_format == "console"
    del os.environ["LOG_LEVEL"]
    del os.environ["LOG_FORMAT"]

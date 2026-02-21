from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Broadcaster"
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # File uploads
    upload_dir: str = "uploads"
    max_image_size_mb: int = 5
    max_images_per_ad: int = 10

    # Telegram API (shared app-level credentials)
    telegram_api_id: int = 0
    telegram_api_hash: str = ""

    # WA Bridge
    wa_bridge_url: str = "http://wa-bridge:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

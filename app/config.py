from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Broadcaster"
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # File uploads
    max_image_size_mb: int = 5
    max_images_per_ad: int = 10

    # S3 storage
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "broadcaster"
    s3_region: str = ""
    s3_public_url: str = ""  # public base URL for serving images

    # Telegram API (shared app-level credentials)
    telegram_api_id: int = 0
    telegram_api_hash: str = ""

    # WA Bridge — list of bridge URLs for horizontal scaling
    wa_bridge_urls: list[str] = ["http://wa-bridge:3000"]

    # Celery scaling
    celery_beat_interval: int = 30  # seconds
    billing_cache_ttl: int = 60  # seconds

    # Admin
    admin_email: str = ""

    # SMTP (email verification)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    @property
    def wa_bridge_url(self) -> str:
        """Backward-compatible: returns first bridge URL."""
        return self.wa_bridge_urls[0]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

import json
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

    # Billing — message balance
    free_monthly_messages: int = 10
    message_packages: str = '[{"name":"100 сообщений","count":100,"price":"149.00"},{"name":"500 сообщений","count":500,"price":"599.00"},{"name":"1000 сообщений","count":1000,"price":"999.00"}]'

    # Billing — тарифные планы.
    #
    # ЦЕНА — МАШИННАЯ СТРОКА ФОРМАТА ЮKASSA («1490.00»), а не подпись макета.
    # `create_payment` кладёт это значение прямо в `amount.value`, и строка с
    # разделителем разрядов или знаком рубля — отказ платёжного API в проде,
    # которого не поймает ни один мок: моки не валидируют формат суммы.
    #
    # БЕЗЛИМИТ КОДИРУЕТСЯ ИМЕННО `null`, не `0` и не большим числом. Ноль
    # неотличим от нулевого лимита («ни одного объявления не разрешено»), а
    # большое число рано или поздно достигается и превращается в лимит, о
    # котором пользователю обещали, что его нет.
    plan_limits: str = (
        '[{"id":"free","name":"Free","price":"0.00","ads":3,"groups":5,"sends":300,"accounts":1},'
        '{"id":"basic","name":"Basic","price":"1490.00","ads":15,"groups":30,"sends":5000,"accounts":5},'
        '{"id":"pro","name":"Pro","price":"4900.00","ads":null,"groups":null,"sends":50000,"accounts":20}]'
    )

    # YooKassa
    yookassa_enabled: bool = True
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_return_url: str = ""
    # Проверка подлинности уведомления по адресу источника. Включена по
    # умолчанию; `False` — аварийный выключатель на случай, когда сквозной адрес
    # клиента за прокси определить не удаётся и приём денег важнее.
    yookassa_webhook_verify_ip: bool = True
    # Имя заголовка, из которого читается адрес источника за обратным прокси.
    #
    # ПУСТО = ОТКАЗ КАЖДОМУ УВЕДОМЛЕНИЮ, а не «доверять адресу пира». Прежнее
    # умолчание было пустой строкой и уводило гард в ветку `request.client.host`;
    # на бою uvicorn запущен с `--forwarded-allow-ips=*`, и в этой сборке адрес
    # пира — ЛЕВЫЙ элемент `X-Forwarded-For`, то есть значение, которое присылает
    # сам вызывающий. Гард был написан верно и при этом не исполнялся ни разу.
    # Отказ по умолчанию закрывает его, а не открывает.
    #
    # `X-Real-IP` выбран потому, что nginx проекта ставит его `$remote_addr`-ом
    # на КАЖДОМ location (`nginx/nginx.conf.template`), то есть ЗАТИРАЕТ всё,
    # что прислал клиент.
    #
    # ⚠️ ЗАПРЕТ, А НЕ РЕКОМЕНДАЦИЯ: сюда нельзя ставить имя заголовка, который
    # прокси лишь ДОПИСЫВАЕТ (`X-Forwarded-For` через
    # `$proxy_add_x_forwarded_for`). Такой заголовок клиент дополняет сам, и
    # проверка станет декоративной — то есть хуже отсутствующей, потому что о
    # ней отчитываются как о защите. Разбор — в докстринге гарда в
    # app/routes/billing.py.
    yookassa_webhook_client_ip_header: str = "X-Real-IP"

    @property
    def wa_bridge_url(self) -> str:
        """Backward-compatible: returns first bridge URL."""
        return self.wa_bridge_urls[0]

    @property
    def parsed_message_packages(self) -> list[dict]:
        return json.loads(self.message_packages)

    @property
    def parsed_plan_limits(self) -> list[dict]:
        return json.loads(self.plan_limits)

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

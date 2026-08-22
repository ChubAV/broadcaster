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

    # Признак транспортной защиты cookie сессии.
    #
    # ⚠️ УМОЛЧАНИЕ ВЫКЛЮЧЕНО, И ЭТО РЕШЕНИЕ, А НЕ НЕДОСМОТР (D-50, Ф-9).
    # Прод-nginx выбирает шаблон НА ЛЁТУ: при отсутствии сертификата он
    # стартует с `nginx-http.conf.template`, который слушает только порт 80 и
    # редиректа на защищённый порт не делает
    # (`docker-compose.prod.yml`, команда контейнера nginx). Признак `secure`,
    # включённый литералом, в этот момент отменяет вход в продукт ЦЕЛИКОМ:
    # браузер не сохранит cookie, и человеку это видно как «пароль не
    # подходит» — то есть непродлённый сертификат превращается в полную потерю
    # входа для всех пользователей сразу.
    #
    # Поэтому безопасное значение живёт не здесь, а в боевом артефакте
    # (`docker-compose.prod.yml`: `COOKIE_SECURE: ${COOKIE_SECURE:-true}`), где
    # его выключают одной переменной окружения, НЕ выкатывая код. Выключение —
    # названный заранее аварийный выключатель на время, пока сертификат не
    # продлён, а не импровизация в аварии.
    #
    # Умолчание `False` здесь — это ещё и условие живой локальной разработки и
    # суиты: обе ходят по http, и включённое умолчание отняло бы вход у них.
    cookie_secure: bool = False

    # SMTP (email verification)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    # Billing — ЦЕНА ДОСТУПА. Одно число на весь продукт (D-A, критерий 1).
    #
    # ЭТО МАШИННАЯ СТРОКА ФОРМАТА ЮKASSA, А НЕ ПОДПИСЬ МАКЕТА. Значение уезжает
    # прямо в `amount.value` вызова `YooPayment.create`, поэтому «3 000,00»,
    # «3000 ₽» или `float` — ОТКАЗ ПЛАТЁЖНОГО API В ПРОДЕ, которого не поймает
    # ни один мок: моки суиты формат суммы не валидируют. Разделитель разрядов,
    # знак рубля и запятая запрещены здесь.
    #
    # ⚠️ ЭТО ЕДИНСТВЕННОЕ ЧИСЛО ЦЕНЫ В КОНФИГЕ, И ТАК ОНО И ОБЯЗАНО ОСТАТЬСЯ.
    # Прежний прейскурант из трёх записей снят планом 05.1-07 вместе с рангом
    # тарифов: цена перестала зависеть от предмета покупки, и второй источник
    # суммы означал бы, что вопрос «сколько платить» снова имеет два ответа.
    # Возврат снятых имён краснит
    # `tests/test_application/test_no_metering_remains.py`.
    #
    # ⚠️ СУММА БЕРЁТСЯ ОТСЮДА ЦЕЛИКОМ И НЕ СОБИРАЕТСЯ АРИФМЕТИКОЙ. Ни аккаунты,
    # ни группы, ни сообщения на неё не влияют — умножать и складывать нечего, и
    # именно поэтому округлений в цене не возникает вовсе. Форма оплаты не несёт
    # ни одного поля: цену читает СЕРВЕР, покупатель её не называет (T-05.1-06).
    subscription_price: str = "3000.00"

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

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

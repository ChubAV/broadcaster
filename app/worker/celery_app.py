from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_init


def create_celery_app() -> Celery:
    """Create Celery app. Reads config from environment."""
    from app.config import get_settings
    settings = get_settings()

    app = Celery(
        "broadcaster",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        imports=["app.worker.tasks"],
        task_default_queue="default",
        task_create_missing_queues=True,
        task_routes={
            "app.worker.tasks.send_telegram_message": {"queue": "telegram"},
        },
        beat_schedule={
            "check-schedules": {
                "task": "app.worker.tasks.check_schedules",
                "schedule": float(settings.celery_beat_interval),
            },
            "manage-wa-containers": {
                "task": "app.worker.tasks.manage_wa_containers",
                "schedule": 15.0,
            },
            "process-wa-results": {
                "task": "app.worker.tasks.process_wa_results",
                "schedule": 5.0,
            },
            "manage-max-containers": {
                "task": "app.worker.tasks.manage_max_containers",
                "schedule": 15.0,
            },
            "process-max-results": {
                "task": "app.worker.tasks.process_max_results",
                "schedule": 5.0,
            },
            "reset-free-monthly-balance": {
                "task": "app.worker.tasks.reset_free_monthly_balance",
                "schedule": crontab(hour=0, minute=5),
            },
        },
        worker_prefetch_multiplier=1,
    )

    return app


celery = create_celery_app()


@worker_init.connect
def setup_worker_logging(**kwargs):
    """Initialize structlog when Celery worker starts."""
    from app.config import get_settings
    from app.logging_config import setup_logging
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

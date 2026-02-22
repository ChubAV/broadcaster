from celery import Celery


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
        },
        worker_prefetch_multiplier=1,
    )

    return app


celery = create_celery_app()

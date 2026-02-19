from celery import Celery


def create_celery_app() -> Celery:
    """Create Celery app. Reads config from environment."""
    from app.config import Settings
    settings = Settings()

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
        beat_schedule={
            "check-schedules-every-minute": {
                "task": "app.worker.tasks.check_schedules",
                "schedule": 60.0,
            },
        },
    )

    return app


# Module-level instance for celery CLI
# Only created when this module is actually imported with valid env

import threading
import time

from celery import Celery
from celery.signals import beat_init, worker_init

from app.services.ops_state import (
    INFRA_BEAT,
    INFRA_WORKER_DEFAULT,
    INFRA_WORKER_TELEGRAM,
    MAX_HEARTBEAT_STALE_SEC,
    infra_heartbeat_key,
)

# ПРИЗНАК ЖИВОСТИ ИНФРАСТРУКТУРНЫХ СЛУЖБ (D-52, решение владельца).
#
# ⚠️ ПРЕДМЕТ ПРАВКИ — ПРИЗНАК ЖИВОСТИ, А НЕ ПРОТОКОЛ ОТПРАВКИ. Ниже нет ни
# одной строки в пути отправки: только обработчики сигналов запуска и фоновый
# поток, обновляющий один ключ. Правка входит в боевое приложение Celery, и это
# названная цена варианта C — она принята ради того, чтобы упавший `celery-beat`
# был виден в админке, а не только по отсутствию рассылок.
#
# ⚠️ ЗАЧЕМ ВООБЩЕ ОТДЕЛЬНЫЙ heartbeat, КОГДА У CELERY ЕСТЬ `inspect`.
# `celery inspect` — широковещательный запрос с таймаутом: на пути отрисовки
# страницы он подвешивал бы подраздел при неотвечающем воркере. Тем же доводом
# проект уже отказался от статуса «в работе» (D-15). Ключ в Redis читается за
# один конвейер и не зависит ни от доступности демона контейнеров, ни от
# отзывчивости самого воркера.
INFRA_HEARTBEAT_INTERVAL_SEC = 30

# ⚠️ ФОРМА СРОКА ЖИЗНИ ВЗЯТА У MAX-ВОРКЕРА ДОСЛОВНО
# (`max_worker/main.py`: HEARTBEAT_TTL_SEC = HEARTBEAT_INTERVAL_SEC * 3), и
# произведение РАВНО порогу свежести читателя. Второго числа на вопрос «жив ли
# процесс» в проекте не заводится: разъехавшись, срок жизни и порог дали бы два
# разных ответа — ключ, переживший порог, читался бы мёртвым, а умерший раньше
# порога — неизвестным. Равенство закреплено тестом, а не наблюдением.
INFRA_HEARTBEAT_TTL_SEC = INFRA_HEARTBEAT_INTERVAL_SEC * 3
assert INFRA_HEARTBEAT_TTL_SEC == MAX_HEARTBEAT_STALE_SEC


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


def _infra_service_for_queues(queues) -> str:
    """Роль celery-воркера по ВЫБРАННОЙ им очереди, а не по имени контейнера.

    Имя контейнера — свойство развёртывания: его переименуют в
    `docker-compose.yml` без единой правки кода, и верхний блок начнёт искать
    ключ, которого никто не пишет. Очередь — свойство самого процесса,
    объявленное его же командой запуска (`--queues=telegram`), и подделать её
    мимо запуска нельзя.

    Воркер без указанной очереди слушает всё, включая общие задачи, — поэтому
    умолчание здесь `worker-default`, а не «неизвестно»: молчание про роль
    означало бы, что живой процесс не виден в блоке вовсе.
    """
    return (
        INFRA_WORKER_TELEGRAM
        if "telegram" in set(queues or ())
        else INFRA_WORKER_DEFAULT
    )


def _write_infra_heartbeat(client, service: str) -> None:
    """Одна запись признака живости: эпоха в МИЛЛИСЕКУНДАХ со сроком жизни.

    ⚠️ ЕДИНИЦА НЕСУЩАЯ. Читатель (`app/services/ops_state.py::_is_fresh`) делит
    на миллисекунды, потому что в них пишут оба воркера аккаунтов. Секунды под
    тем же ключом дали бы возраст в пятьдесят с лишним лет, то есть вечное
    «отключён» на живой службе — отказ, которого нет, вместо отказа, который
    есть.

    ⚠️ СРОК ЖИЗНИ СТАВИТСЯ, ХОТЯ ЧИТАТЕЛЬ СРАВНИВАЕТ ВОЗРАСТ. Он не заменяет
    возрастную проверку, а убирает мусор: ключ убитого процесса иначе лежал бы
    в Redis вечно, как это и происходит с `wa:heartbeat:{id}`.
    """
    client.set(
        infra_heartbeat_key(service),
        str(int(time.time() * 1000)),
        ex=INFRA_HEARTBEAT_TTL_SEC,
    )


def _start_infra_heartbeat(service: str) -> None:
    """Фоновый поток-демон, обновляющий признак живости службы.

    ⚠️ ПОТОК, А НЕ ОДНА ЗАПИСЬ В ОБРАБОТЧИКЕ СИГНАЛА. Сигнал запуска приходит
    ровно один раз, а признак обязан ПРОТУХАТЬ: ключ, записанный однажды,
    пережил бы смерть процесса и показывал бы мёртвую службу живой ещё
    полторы минуты — то есть ровно тот дефект, ради которого весь предикат
    сделан возрастным.

    ⚠️ ПОТОК ДЕМОНСКИЙ. Он не должен удерживать процесс при завершении: служба
    обязана уметь останавливаться, а её признак — исчезать сам по сроку жизни.

    Ошибка записи ГЛОТАЕТСЯ намеренно и с записью в журнал: недоступный Redis
    не имеет права уронить celery-процесс, потому что предмет этого потока —
    наблюдаемость, а не работа. Обратное означало бы, что установка наблюдения
    сама стала причиной аварии.
    """
    import structlog

    log = structlog.get_logger(__name__)

    def _loop() -> None:
        from app.config import get_settings

        try:
            import redis as redis_lib

            client = redis_lib.from_url(get_settings().redis_url)
        except Exception as e:
            log.warning("infra_heartbeat_client_unavailable", error=str(e))
            return

        while True:
            try:
                _write_infra_heartbeat(client, service)
            except Exception as e:
                log.warning("infra_heartbeat_write_error", service=service, error=str(e))
            time.sleep(INFRA_HEARTBEAT_INTERVAL_SEC)

    thread = threading.Thread(
        target=_loop, name=f"infra-heartbeat-{service}", daemon=True
    )
    thread.start()
    log.info("infra_heartbeat_started", service=service, key=infra_heartbeat_key(service))


@worker_init.connect
def start_worker_infra_heartbeat(sender=None, **kwargs):
    """Признак живости celery-воркера (D-52).

    Роль берётся из очередей, УЖЕ ВЫБРАННЫХ к этому моменту: `setup_queues`
    отрабатывает до отправки `worker_init`, поэтому `app.amqp.queues` здесь
    содержит ровно то, что процесс слушает.
    """
    queues = ()
    try:
        queues = tuple(sender.app.amqp.queues.keys())
    except Exception:
        pass
    _start_infra_heartbeat(_infra_service_for_queues(queues))


@beat_init.connect
def start_beat_infra_heartbeat(sender=None, **kwargs):
    """Признак живости планировщика (D-52).

    ⚠️ У BEAT СВОЙ СИГНАЛ, И ЭТО НЕ ПРИДИРКА. `worker_init` в процессе `celery
    beat` не приходит вовсе: beat — не воркер. Повесив признак планировщика на
    воркерный сигнал, блок показывал бы «отключён» на исправном планировщике
    всегда — и D-09, ради которого верхний блок и заведён, остался бы
    неисполненным именно в своей главной части.
    """
    _start_infra_heartbeat(INFRA_BEAT)

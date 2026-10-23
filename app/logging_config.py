import logging
import sys

import structlog

from app.services.log_masking import attach_number_masking, mask_numbers_in_event


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure structlog + stdlib logging.

    Номер, дошедший до вывода журнала, маскируется на исполнении: процессор
    `mask_numbers_in_event` стоит в цепочке корневого обработчика, фильтр
    `NumberMaskingFilter` — на нём и на обработчиках журналов, существующих к вызову
    (uvicorn). Что маскируется, что остаётся видным и где граница — шапка
    `app/services/log_masking.py` (решение владельца О-23 (а), свойство 2; О-24 (а)).

    Args:
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR).
        log_format: "json" for production, "console" for dev.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            mask_numbers_in_event,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    attach_number_masking(handler)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.getLevelNamesMapping().get(log_level.upper(), logging.INFO))

    # Обработчики, поставленные до вызова (uvicorn: `propagate=False`, корня не достигают).
    for existing in list(logging.root.manager.loggerDict.values()):
        if isinstance(existing, logging.Logger):
            for other in existing.handlers:
                attach_number_masking(other)

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.WARNING)

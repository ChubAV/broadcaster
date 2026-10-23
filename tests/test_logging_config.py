"""Настройка журнала: structlog и stdlib в одном выводе, номер на выводе — только маской.

Защита на исполнении (решение владельца О-23 (а), свойство 2; что «похоже на номер» — О-24 (а);
форма маски — D-10; место вызова номер не кладёт и маской — D-11): номер, дошедший до вывода
журнала любым написанием, маскируется процессором в цепочке корневого обработчика и фильтром
на обработчиках. Предмет правил этого модуля — НАСТОЯЩИЙ конвейер `setup_logging`: событие
structlog и запись stdlib проходят его целиком, вывод читается из потока обработчика.

⚠️ `setup_logging` настраивает журнал всего процесса. Фикстура `restored_logging` (autouse)
снимает снимок корня, обработчиков, уровней и `propagate` журналов, фильтров обработчиков и
конфигурации structlog и возвращает его после правила — конвейер правила не утекает в
соседние модули суиты.
"""

import io
import json
import logging

import pytest
import structlog

from app.logging_config import setup_logging

NAMED_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access", "celery", "telethon", "sqlalchemy.engine")


def _every_logger() -> list[logging.Logger]:
    found = [logging.getLogger()]
    found += [item for item in logging.root.manager.loggerDict.values() if isinstance(item, logging.Logger)]
    return found


@pytest.fixture(autouse=True)
def restored_logging():
    """Снимок настройки журнала процесса до правила и возврат после него."""
    for name in NAMED_LOGGERS:
        logging.getLogger(name)
    config = structlog.get_config()
    # `get_config` отдаёт САМ список процессоров, а `configure` меняет его на месте.
    config["processors"] = list(config["processors"])
    loggers = {
        id(item): (item, list(item.handlers), item.level, item.propagate, item.disabled)
        for item in _every_logger()
    }
    handlers = {
        id(handler): (handler, list(handler.filters))
        for _item, saved, *_rest in loggers.values()
        for handler in saved
    }
    yield
    for item in _every_logger():
        if id(item) not in loggers:
            item.handlers = []
    for item, saved, level, propagate, disabled in loggers.values():
        item.handlers = saved
        item.setLevel(level)
        item.propagate = propagate
        item.disabled = disabled
    for handler, filters in handlers.values():
        handler.filters = filters
    structlog.configure(**config)


def _root_stream() -> io.StringIO:
    """Поток единственного обработчика корня, поставленного `setup_logging`, — в память."""
    stream = io.StringIO()
    (handler,) = logging.getLogger().handlers
    handler.setStream(stream)
    return stream


def test_setup_logging_json_mode():
    """setup_logging configures structlog with JSON output."""
    setup_logging(log_level="INFO", log_format="json")
    logger = structlog.get_logger("test.json")
    assert logger is not None


def test_setup_logging_console_mode():
    """setup_logging configures structlog with console output."""
    setup_logging(log_level="DEBUG", log_format="console")
    logger = structlog.get_logger("test.console")
    assert logger is not None


def test_setup_logging_sets_level():
    """setup_logging sets root logger level."""
    setup_logging(log_level="WARNING", log_format="json")
    root = logging.getLogger()
    assert root.level == logging.WARNING


# --- Сквозной срез: поле события structlog → строка JSON ------------------------------


def test_a_number_in_a_structlog_field_is_masked_in_the_rendered_line(restored_logging):
    """ТРАСЕР (О-23 (а), свойство 2; О-24 (а); D-10, D-11).

    Событие отправки несёт ID группы Telegram (`-100…`, видно по О-24 (а)), номер целым числом
    и номер разбивкой внутри текста. В строке JSON оба номера — маска `mask_phone`, ID группы и
    `account_id` — как были, цифр номера в строке нет.
    """
    setup_logging(log_level="INFO", log_format="json")
    stream = _root_stream()

    structlog.get_logger("app.tracer").info(
        "send_forbidden",
        group_id="-1001234567890",
        account_id=7,
        phone_raw=79991234567,
        note="call +7 999 123-45-67",
    )

    line = stream.getvalue().strip().splitlines()[-1]
    event = json.loads(line)
    assert event["phone_raw"] == "+7 *** ***-**-67", (
        f"номер в поле события structlog дошёл до строки журнала без маски: {line}"
    )
    assert event["note"] == "call +7 *** ***-**-67", f"номер внутри текста поля не замаскирован: {line}"
    assert event["group_id"] == "-1001234567890", f"ID группы спрятан маской (О-24 (а)): {line}"
    assert event["account_id"] == 7, f"`account_id` изменён маской: {line}"
    assert "9991234567" not in line, f"цифры номера остались в строке журнала: {line}"

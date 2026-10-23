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

import asyncio
import copy
import io
import json
import logging
import logging.config
import sys
import types

import pytest
import structlog

from app.logging_config import setup_logging

NUMBER = "+79991234567"
NUMBER_DIGITS = "9991234567"
MASK = "+7 *** ***-**-67"

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


# --- Полный конвейер: запись stdlib, исключения, обработчики uvicorn, режим `console` ---------


def _integrity_error() -> Exception:
    """Ошибка SQLAlchemy с параметрами запроса — так номер попадает в трассировку."""
    from sqlalchemy.exc import IntegrityError

    return IntegrityError(
        "UPDATE messenger_accounts SET phone=? WHERE id=?",
        (NUMBER, 1),
        Exception("UNIQUE constraint failed: messenger_accounts.phone"),
    )


def _uvicorn_logging_before_the_app() -> None:
    """Обработчики uvicorn ставятся ДО `create_app()` — тем же `dictConfig`, что у uvicorn."""
    import uvicorn.config

    logging.config.dictConfig(copy.deepcopy(uvicorn.config.LOGGING_CONFIG))


def _masking_filter_class():
    from app.services import log_masking

    found = log_masking.__dict__.get("NumberMaskingFilter")
    assert found is not None, "фильтра stdlib `NumberMaskingFilter` нет: запись мимо процессора печатает номер"
    return found


def test_a_stdlib_record_through_the_root_is_masked(restored_logging, monkeypatch):
    """Запись stdlib (telethon) через корень — маска; отчёт об ошибке подстановки — без номера."""
    setup_logging(log_level="INFO", log_format="json")
    stream = _root_stream()
    report = io.StringIO()
    monkeypatch.setattr(sys, "stderr", report)

    logging.getLogger("telethon").warning("connection to %s lost", NUMBER)
    logging.getLogger("telethon").warning("bad %d", NUMBER)

    output = stream.getvalue()
    event = json.loads(output.strip().splitlines()[0])
    assert event["event"] == f"connection to {MASK} lost", f"запись stdlib через корень без маски: {output}"
    assert NUMBER_DIGITS not in output, f"номер в выводе корня: {output}"
    text = report.getvalue()
    assert "--- Logging error ---" in text, f"отчёт об ошибке подстановки не напечатан: {text!r}"
    assert NUMBER_DIGITS not in text, f"отчёт `--- Logging error ---` записи через корень напечатал номер: {text}"


def test_an_exception_with_bound_parameters_is_masked_in_both_paths(restored_logging):
    """Трассировка `IntegrityError` с параметрами — маска и у structlog, и у записи stdlib."""
    setup_logging(log_level="INFO", log_format="json")
    stream = _root_stream()

    try:
        raise _integrity_error()
    except Exception:
        structlog.get_logger("app.writer").exception("phone_update_failed", account_id=1)
        logging.getLogger("sqlalchemy.engine").exception("database error")

    output = stream.getvalue()
    events = [json.loads(line) for line in output.strip().splitlines()]
    assert [event["event"] for event in events] == ["phone_update_failed", "database error"], output
    for event in events:
        assert "IntegrityError" in event["exception"], f"трассировка потеряна: {event}"
        assert f"[parameters: ('{MASK}', 1)]" in event["exception"], f"параметры запроса без маски: {event}"
    assert NUMBER_DIGITS not in output, f"номер в трассировке: {output}"


def test_uvicorn_handlers_set_up_before_the_app_are_masked(restored_logging):
    """Обработчики uvicorn (`propagate=False`) корня не достигают — фильтр стоит и на них."""
    _uvicorn_logging_before_the_app()
    setup_logging(log_level="INFO", log_format="json")
    error_stream = io.StringIO()
    access_stream = io.StringIO()
    for handler in logging.getLogger("uvicorn").handlers:
        handler.setStream(error_stream)
    for handler in logging.getLogger("uvicorn.access").handlers:
        handler.setStream(access_stream)
    # Уровень самого uvicorn (`--log-level info`); `setup_logging` опускает его до WARNING.
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    try:
        raise _integrity_error()
    except Exception:
        logging.getLogger("uvicorn.error").error("Exception in ASGI application", exc_info=True)
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %d', "127.0.0.1:50000", "GET", f"/x?phone={NUMBER}", "1.1", 500
    )

    output = error_stream.getvalue() + access_stream.getvalue()
    assert "Exception in ASGI application" in output and "/x?phone=" in output, f"вывод uvicorn пуст: {output!r}"
    assert NUMBER_DIGITS not in output, (
        f"запись обработчика uvicorn, поставленного до setup_logging, напечатала номер: {output}"
    )
    assert MASK in output


def test_the_console_mode_masks_too(restored_logging):
    setup_logging(log_level="INFO", log_format="console")
    stream = _root_stream()

    structlog.get_logger("app.console").info("send_forbidden", group_id="-1001234567890", phone_raw=79991234567)
    logging.getLogger("telethon").warning("connection to %s lost", NUMBER)

    output = stream.getvalue()
    assert NUMBER_DIGITS not in output, f"режим `console` напечатал номер: {output}"
    assert output.count("***-**-67") == 2, f"маска в режиме `console` не на своих местах: {output}"
    assert "-1001234567890" in output, f"ID группы спрятан в режиме `console`: {output}"


def test_every_json_line_parses(restored_logging):
    """Каждая строка вывода корня в режиме `json` — разбираемый JSON, и номер в ней — маска."""
    setup_logging(log_level="INFO", log_format="json")
    stream = _root_stream()

    log = structlog.get_logger("app.lines")
    log.info("send_forbidden", group_id=-1001234567890, phone_raw=79991234567, nested={"a": [NUMBER, 5]})
    log.info("positional %s", NUMBER)
    logging.getLogger("telethon").warning("x %d", 79991234567)
    logging.getLogger("telethon").warning("x %s and %d", NUMBER, 7)
    try:
        raise _integrity_error()
    except Exception:
        log.exception("phone_update_failed")
        logging.getLogger("sqlalchemy.engine").exception("database error")

    lines = stream.getvalue().strip().splitlines()
    assert len(lines) == 6, f"не все события дошли до вывода: {lines}"
    for line in lines:
        event = json.loads(line)
        assert "event" in event, line
        assert NUMBER_DIGITS not in line, f"номер в строке JSON: {line}"
    assert json.loads(lines[0])["group_id"] == -1001234567890


def test_an_unknown_level_name_falls_back_to_info(restored_logging):
    """Уровень по имени — `logging.getLevelNamesMapping()`, а не чтение атрибута модуля `logging`."""
    for name in ("nope", "basic_format", "raiseExceptions"):
        try:
            setup_logging(log_level=name, log_format="json")
        except (TypeError, ValueError) as error:
            raise AssertionError(f"имя уровня {name!r} не свелось к INFO: {error}") from None
        assert logging.getLogger().level == logging.INFO, f"имя уровня {name!r} дало {logging.getLogger().level}"


def test_masking_is_attached_once(restored_logging):
    _uvicorn_logging_before_the_app()
    masking_class = _masking_filter_class()

    setup_logging(log_level="INFO", log_format="json")
    setup_logging(log_level="INFO", log_format="json")

    handlers = logging.getLogger().handlers + logging.getLogger("uvicorn").handlers
    handlers += logging.getLogger("uvicorn.access").handlers
    assert len(handlers) == 3, handlers
    for handler in handlers:
        count = sum(1 for item in handler.filters if isinstance(item, masking_class))
        assert count == 1, f"на обработчике {handler!r} фильтров маски {count}, а не один"


# --- Формы раунда 10 стороны приватности — исполнением через настоящий конвейер ----------

# Исходники форм ревью CR-05, WR-32, WR-33 (16-REVIEW.md), где вызываемое журнала — метод
# настоящего журнала (`out = logger.info`, получатель `lg = logging.getLogger(...)`). Каждая
# форма исполняется по-настоящему: модуль, зарегистрированный в `sys.modules` (так
# `sys.modules[__name__]` и `importlib.import_module(__name__)` находят его), точка входа
# `go(account)`. Статический гейт эти написания не ловил — номер печатался; по решению
# владельца О-23 (а), свойство 4, их закрывает запрет конструкции (планы 16-53, 16-54) и
# защита на исполнении (этот план): в выводе журнала — маска, а не номер. Формы с `out = print`
# — вне защиты на исполнении (`print` пишет в поток мимо журнала), их держит запрет конструкции.
ROUND_TEN_PRIVACY_FORMS = [
    pytest.param(
        "import logging\n"
        "import sys\n"
        "logger = logging.getLogger('app.form')\n"
        "out = logger.info\n"
        "class K:\n"
        "    def __init__(self):\n"
        "        self.me = sys.modules[__name__]\n"
        "    def go(self, account):\n"
        "        self.me.out('x %s', account.phone)\n"
        "def go(account):\n"
        "    K().go(account)\n",
        False,
        id="cr05-self-attribute-module-object",
    ),
    pytest.param(
        "import logging\n"
        "import sys as _s\n"
        "logger = logging.getLogger('app.form')\n"
        "out = logger.info\n"
        "def go(account):\n"
        "    _s.modules[__name__].out('x %s', account.phone)\n",
        False,
        id="cr05-import-alias-module-object",
    ),
    pytest.param(
        "import importlib\n"
        "import logging\n"
        "logger = logging.getLogger('app.form')\n"
        "out = logger.info\n"
        "def go(account):\n"
        "    importlib.import_module(__name__).out('x %s', account.phone)\n",
        False,
        id="cr05-importlib-module-object",
    ),
    pytest.param(
        "import logging\n"
        "import sys\n"
        "lg = logging.getLogger('x')\n"
        "class K:\n"
        "    def __init__(self):\n"
        "        self.me = sys.modules[__name__]\n"
        "    def go(self, account):\n"
        "        self.me.lg.info('x %s', account.phone)\n"
        "def go(account):\n"
        "    K().go(account)\n",
        False,
        id="cr05-receiver-through-module-object",
    ),
    pytest.param(
        "import asyncio\n"
        "import logging\n"
        "import operator\n"
        "logger = logging.getLogger('app.form')\n"
        "to_thread = operator.methodcaller('noop')\n"
        "async def go(account):\n"
        "    f = operator.methodcaller('info', 'x %s', account.phone)\n"
        "    await asyncio.to_thread(f, logger)\n",
        True,
        id="wr32-methodcaller-rival-on-the-carrier",
    ),
    pytest.param(
        "import asyncio\n"
        "import logging\n"
        "import operator\n"
        "logger = logging.getLogger('app.form')\n"
        "to_thread = operator.methodcaller\n"
        "async def go(account):\n"
        "    f = operator.methodcaller('info', 'x %s', account.phone)\n"
        "    await asyncio.to_thread(f, logger)\n",
        True,
        id="wr33-methodcaller-alias-on-the-carrier",
    ),
]


@pytest.mark.parametrize(("source", "is_async"), ROUND_TEN_PRIVACY_FORMS)
def test_a_round_ten_privacy_form_prints_a_mask_not_a_number(restored_logging, request, source, is_async):
    """Форма раунда 10, исполненная после `setup_logging`, печатает маску, а не номер.

    `account` — заглушка `types.SimpleNamespace(phone=...)`, а не `MessengerAccount`: предмет
    правила — вывод журнала, модель ему не нужна, а защита писателя плана 16-51 отказывает
    конструктору `MessengerAccount(phone=…)` вне `writer_scope()`.
    """
    setup_logging(log_level="INFO", log_format="json")
    stream = _root_stream()
    account = types.SimpleNamespace(phone=NUMBER)
    name = "phone_form_" + "".join(ch if ch.isalnum() else "_" for ch in request.node.callspec.id)
    module = types.ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(source, f"<{name}>", "exec"), module.__dict__)
        if is_async:
            asyncio.run(module.go(account))
        else:
            module.go(account)
    finally:
        sys.modules.pop(name, None)

    output = stream.getvalue()
    assert MASK in output, f"форма не дошла до журнала: {output!r}"
    assert NUMBER_DIGITS not in output, f"форма раунда 10 напечатала номер в журнал: {output}"

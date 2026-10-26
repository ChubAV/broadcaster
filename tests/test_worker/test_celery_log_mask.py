"""Маска номера в процессах Celery: воркер, `celery beat`, дочерний процесс пула prefork.

Что доказывается (гэп 1 раунда 11, CR-06; решение владельца О-25 (а), свойство 1; О-23 (а), свойство 2; PHONE-21
«журналы … воркеров»; форма маски — D-10, место вызова номер не кладёт — D-11): событие structlog и запись stdlib с
номером, написанные в процессе Celery проекта, печатаются маской `+7 *** ***-**-67`, а не номером целиком. Получатель
`worker_init` проекта ставит маску, но конструктор `celery.apps.worker.Worker` затем зовёт `app.log.setup`, и Celery
5.6.2 без получателя своего сигнала `setup_logging` очищает обработчики корня (`worker_hijack_root_logger`) и ставит
свой `StreamHandler` с `ColorFormatter` — маска снимается. Правила строят НАСТОЯЩИЙ `Worker` проекта (тот же путь, что
`celery -A app.worker.celery_app worker` в `docker-compose.prod.yml`), `Beat(...).setup_logging()` (путь
`Beat.start_scheduler`) и дочерний процесс после `os.fork()` + `process_initializer` (путь пула prefork) и читают вывод.

⚠️ ПОЧЕМУ ОТДЕЛЬНЫЙ ПРОЦЕСС. `Logging._setup` у Celery — признак класса на процесс, конструктор `Worker` меняет журнал
всего процесса, а `fork` внутри процесса pytest недопустим. Зонд `CELERY_PROBE` идёт отдельным интерпретатором
(`-I`) из пустого рабочего каталога `tmp_path` с `DATABASE_URL` SQLite в памяти и тестовым `SECRET_KEY`: живой `.env` не
читается, брокер не поднимается (конструктор `Worker` к брокеру не подключается, `start()` не вызывается), признак
живости отсоединён от сигналов в самом зонде — продукт ради правила не правится. Каждый запуск ограничен таймаутом:
зависший зонд роняет правило, а не суиту.

Механизм закреплён отдельно: при живом получателе `setup_celery_logging` у воркера `_custom_logging` истинно и на
корне ровно один обработчик (Celery рядом свой не поставил, `stdout` в журнал не перенаправляется — `print` в задаче
идёт в поток процесса мимо журнала). Контроль-отрицание — тот же зонд с отсоединённым получателем печатает номер
целиком: правила воркера видят отказ маски, а не вакуум.

ЧТО НЕ МЕРИТСЯ ЗДЕСЬ. `celery flower` — свой журнал tornado (`flower.command.setup_logging`), `app.log.setup` не
вызывается, получатель там не срабатывает: граница шапки маски (план 16-60). Настоящий пул prefork с брокером — без
брокера его не поднять; путь дочернего процесса пула мерится вызовом, который пул делает в каждом дочернем процессе,
`process_initializer`, после `os.fork()`.

Номер в тексте правил — только константа `NUMBER`, которую правила ищут в выводе; вывод зонда в сообщениях отказа
печатается с вычеркнутыми цифрами номера (D-11).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

NUMBER = "+79991234567"
NUMBER_DIGITS = "9991234567"
MASK = "+7 *** ***-**-67"
GROUP_ID = "-1001234567890"
REPO_ROOT = Path(__file__).resolve().parents[2]

PROBE_TIMEOUT_SECONDS = 60

CR06 = "в процессе Celery номер напечатан целиком: настройку журнала проекта сняла настройка Celery (CR-06)"

# Исходник зонда. Аргументы: корень репозитория, цель, номер, идентификатор группы. Строка `ROOT <json>` в
# `sys.__stderr__` — обработчики корня `[тип, [типы фильтров], тип форматтера]` после настройки Celery.
CELERY_PROBE = r'''
import json
import logging
import os
import sys
import traceback

repo_root, target, number, group_id = sys.argv[1:5]
sys.path.insert(0, repo_root)

import structlog
from celery.apps.beat import Beat
from celery.apps.worker import Worker
from celery.concurrency.prefork import process_initializer
from celery.signals import beat_init, setup_logging, worker_init

import app.worker.celery_app as ca

worker_init.disconnect(ca.start_worker_infra_heartbeat)
beat_init.disconnect(ca.start_beat_infra_heartbeat)

HOSTNAME = "r11@probe"


def flush():
    for stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
        stream.flush()


def root_line():
    described = [
        [type(h).__name__, [type(f).__name__ for f in h.filters], type(h.formatter).__name__]
        for h in logging.getLogger().handlers
    ]
    sys.__stderr__.write("ROOT " + json.dumps(described) + "\n")
    sys.__stderr__.flush()


def write_records(with_event):
    if with_event:
        structlog.get_logger("app.worker.tasks").info("wa_phone_reported", phone=number, group_id=group_id)
    logging.getLogger("app.messengers.whatsapp").warning("raw number %s", number)


def build_worker():
    return Worker(app=ca.celery, loglevel="INFO", no_color=True, hostname=HOSTNAME, quiet=True)


if target == "worker":
    build_worker()
    root_line()
    write_records(True)
elif target == "worker-state":
    worker = build_worker()
    root_line()
    sys.__stderr__.write("CUSTOM_LOGGING " + str(bool(worker._custom_logging)) + "\n")
    sys.__stderr__.write("ROOT_HANDLERS " + str(len(logging.getLogger().handlers)) + "\n")
elif target == "worker-without-receiver":
    setup_logging.disconnect(ca.setup_celery_logging)
    build_worker()
    root_line()
    write_records(True)
elif target == "beat":
    Beat(app=ca.celery, loglevel="INFO", no_color=True, quiet=True).setup_logging()
    root_line()
    write_records(True)
elif target == "child":
    build_worker()
    flush()
    pid = os.fork()
    if pid == 0:
        code = 0
        try:
            process_initializer(ca.celery, HOSTNAME)
            root_line()
            write_records(False)
        except BaseException:
            traceback.print_exc(file=sys.__stderr__)
            code = 1
        flush()
        os._exit(code)
    _, status = os.waitpid(pid, 0)
    child_code = os.waitstatus_to_exitcode(status)
    if child_code:
        sys.exit("child exited with " + str(child_code))
else:
    sys.exit("unknown target " + target)

flush()
logging.getLogger().handlers = []
'''


def _run_celery_probe(target: str, tmp_path) -> subprocess.CompletedProcess:
    """Зонд `CELERY_PROBE` с целью `target` в отдельном процессе из пустого `tmp_path`, без `.env` и брокера."""
    return subprocess.run(
        [sys.executable, "-I", "-c", CELERY_PROBE, str(REPO_ROOT), target, NUMBER, GROUP_ID],
        cwd=tmp_path,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        },
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT_SECONDS,
    )


def _redacted(text: str) -> str:
    """Вывод зонда для сообщения отказа — без цифр номера (D-11)."""
    return text.replace(NUMBER_DIGITS, "<цифры номера>")


def _root_handlers(result: subprocess.CompletedProcess) -> list:
    lines = [line for line in result.stderr.splitlines() if line.startswith("ROOT ")]
    assert len(lines) == 1, f"зонд не напечатал ровно одну строку ROOT:\n{_redacted(result.stderr)[-3000:]}"
    return json.loads(lines[0][len("ROOT "):])


def _assert_masked(result: subprocess.CompletedProcess, *, records: int, with_event: bool) -> None:
    """Код возврата 0; цифр номера нет нигде в выводе; маска — на каждую запись; корень несёт фильтр и процессор маски."""
    # Кадр помощника скрыт из отчёта: pytest печатает аргументы кадра, а `result` несёт вывод зонда с номером (D-11).
    __tracebackhide__ = True
    assert result.returncode == 0, (
        f"зонд Celery упал (код {result.returncode}):\n{_redacted(result.stderr)[-3000:]}"
    )
    root = _root_handlers(result)
    # Сравнение через признак: разбор утверждения pytest иначе напечатал бы вывод зонда с номером в отчёт.
    number_printed = NUMBER_DIGITS in result.stdout + result.stderr
    assert not number_printed, f"{CR06}; обработчики корня: {root}"
    assert any(
        "NumberMaskingFilter" in filters and formatter == "ProcessorFormatter" for _kind, filters, formatter in root
    ), f"{CR06}; на корне нет фильтра и процессора маски: {root}"
    masks = result.stdout.count(MASK)
    assert masks >= records, (
        f"маска напечатана {masks} раз на {records} записей с номером:\n{_redacted(result.stdout)[-3000:]}"
    )
    if with_event:
        group_visible = GROUP_ID in result.stdout
        assert group_visible, f"идентификатор группы не виден в выводе события:\n{_redacted(result.stdout)}"


def test_a_celery_worker_prints_a_mask_not_a_number(tmp_path):
    """Настоящий `Worker(app=…)` проекта: событие structlog и запись stdlib с номером печатаются маской."""
    _assert_masked(_run_celery_probe("worker", tmp_path), records=2, with_event=True)


def test_celery_beat_prints_a_mask_not_a_number(tmp_path):
    """`Beat(app=…).setup_logging()` — вызов `Beat.start_scheduler`: событие и запись печатаются маской."""
    _assert_masked(_run_celery_probe("beat", tmp_path), records=2, with_event=True)


def test_a_prefork_pool_child_keeps_the_mask(tmp_path):
    """Дочерний процесс пула (`os.fork()` + `process_initializer`) печатает запись с номером маской."""
    _assert_masked(_run_celery_probe("child", tmp_path), records=1, with_event=False)


def _stderr_value(result: subprocess.CompletedProcess, key: str) -> str:
    values = [line[len(key) + 1:] for line in result.stderr.splitlines() if line.startswith(key + " ")]
    assert len(values) == 1, f"зонд не напечатал ровно одну строку {key}:\n{_redacted(result.stderr)[-3000:]}"
    return values[0]


def test_the_worker_neither_hijacks_the_root_nor_redirects_print(tmp_path):
    """Механизм маски в воркере: Celery видит настройку проекта (`_custom_logging`) и корень не захватывает.

    Следствие, которое правило закрепляет вместе с механизмом: `stdout` в журнал Celery не перенаправляется, и
    `print` в задаче идёт в поток процесса мимо журнала и маски — граница `print`, её называет шапка маски (план 16-60).
    """
    result = _run_celery_probe("worker-state", tmp_path)
    assert result.returncode == 0, f"зонд Celery упал (код {result.returncode}):\n{_redacted(result.stderr)[-3000:]}"
    custom_logging = _stderr_value(result, "CUSTOM_LOGGING")
    root_handlers = _stderr_value(result, "ROOT_HANDLERS")
    assert custom_logging == "True", (
        f"у воркера `_custom_logging` = {custom_logging}: Celery не увидел настройку журнала проекта — он захватит "
        "корень и перенаправит `stdout` (`print` в задаче) в свой журнал без маски (CR-06)"
    )
    assert root_handlers == "1", (
        f"на корне воркера обработчиков {root_handlers}, а не один: Celery поставил свой обработчик рядом с "
        f"обработчиком маски — часть вывода идёт без маски; корень: {_root_handlers(result)}"
    )


def test_control_without_the_receiver_the_worker_prints_the_number(tmp_path):
    """Контроль-отрицание: без получателя `setup_celery_logging` тот же воркер печатает номер целиком.

    Правило воркера видит отказ маски, а не вакуум: зонд, его цель и вывод — те же, отличается только получатель.
    """
    result = _run_celery_probe("worker-without-receiver", tmp_path)
    assert result.returncode == 0, f"зонд Celery упал (код {result.returncode}):\n{_redacted(result.stderr)[-3000:]}"
    root = _root_handlers(result)
    # Обработчик Celery пишет в `sys.__stderr__`: номер ищется во всём выводе зонда, как и в правилах маски.
    number_printed = NUMBER_DIGITS in result.stdout + result.stderr
    assert number_printed, (
        "без получателя сигнала Celery `setup_logging` номер в выводе воркера не найден — контроль не видит "
        f"захвата корня, и правило воркера ничего не доказывает; корень: {root}"
    )
    assert any(formatter == "ColorFormatter" for _kind, _filters, formatter in root), (
        f"без получателя на корне нет `ColorFormatter` Celery — контроль мерит не тот путь; корень: {root}"
    )

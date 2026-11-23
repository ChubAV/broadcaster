"""Offline compatibility coverage for the MAX worker on PyMax 2.5.0."""

import asyncio
import importlib
import inspect
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def incomplete_contact_chat_payload(*, contact_id: int | None = None) -> dict:
    attachment = {"_type": "CONTACT"}
    if contact_id is not None:
        attachment["contactId"] = contact_id
    return {
        "id": 1,
        "type": "CHAT",
        "status": "ACTIVE",
        "owner": 2,
        "title": "CONTACT group",
        "lastEventTime": 100,
        "lastMessage": {
            "id": 9,
            "time": 100,
            "type": "USER",
            "attaches": [attachment],
        },
    }


def incomplete_sticker_chat_payload(*, set_id: int | None = None) -> dict:
    """A STICKER attachment as MAX actually emits it — every field except ``setId``."""
    attachment = {
        "authorType": "USER",
        "_type": "STICKER",
        "url": "https://st.max.ru/sticker/1.png",
        "stickerId": 54954683,
        "width": 170,
        "time": 1754954683,
        "stickerType": "STATIC",
        "audio": False,
        "height": 170,
    }
    if set_id is not None:
        attachment["setId"] = set_id
    return {
        "id": 1,
        "type": "CHAT",
        "status": "ACTIVE",
        "owner": 2,
        "title": "STICKER group",
        "lastEventTime": 100,
        "lastMessage": {
            "id": 9,
            "time": 100,
            "type": "USER",
            "attaches": [attachment],
        },
    }


def incomplete_contact_login_payload() -> dict:
    return {
        "profile": {"contact": {"id": 42}},
        "chats": [incomplete_contact_chat_payload()],
        "messages": {},
        "contacts": [],
    }


class FakeExtraConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeWebClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.chats = []
        self.start_handler = None
        self.start = AsyncMock()
        self.close = AsyncMock()
        self.fetch_chats = AsyncMock(return_value=[])
        self.send_message = AsyncMock()

    def on_start(self):
        def register(callback):
            self.start_handler = callback
            return callback

        return register


@pytest.fixture
def worker(monkeypatch, tmp_path):
    monkeypatch.setenv("ACCOUNT_ID", "42")
    monkeypatch.setenv("SESSIONS_DIR", str(tmp_path / "sessions"))
    sys.modules.pop("max_worker.main", None)
    module = importlib.import_module("max_worker.main")
    module.SESSIONS_DIR = str(tmp_path / "sessions")
    module.ACCOUNT_ID = "42"
    module.session = None
    module.shutting_down = False
    module.consumer_running = False
    module.redis_cmd = None
    module.redis_blpop = None
    return module


class ThrowingMeWebClient(FakeWebClient):
    """A client whose ``me`` property raises; the message carries a number."""

    @property
    def me(self):
        raise RuntimeError("boom 79991234567")


def install_fake_client(monkeypatch, worker, client_class=FakeWebClient):
    clients = []

    def construct(**kwargs):
        client = client_class(**kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(worker, "WebClient", construct)
    monkeypatch.setattr(worker, "ExtraConfig", FakeExtraConfig)
    return clients


def create_session_db(path: Path, schema: str, values: tuple[str, str] | None = None):
    connection = sqlite3.connect(path)
    if schema == "sessions":
        connection.execute("CREATE TABLE sessions (token TEXT, device_id TEXT, phone TEXT)")
    else:
        connection.execute("CREATE TABLE auth (token TEXT, device_id TEXT)")
    if values:
        table = "sessions" if schema == "sessions" else "auth"
        if schema == "sessions":
            connection.execute(f"INSERT INTO {table} VALUES (?, ?, ?)", (*values, "+79990000000"))
        else:
            connection.execute(f"INSERT INTO {table} VALUES (?, ?)", values)
    connection.commit()
    connection.close()


def test_pymax_2_5_0_contract(worker):
    import pymax
    from pymax import ExtraConfig, Photo, WebClient
    from pymax.auth.providers import QrHandler

    assert pymax.__version__ == "2.5.0"
    for symbol in (WebClient, ExtraConfig, Photo):
        assert symbol is not None
    parameters = inspect.signature(WebClient).parameters
    assert {"session_name", "work_dir", "extra_config", "qr_provider"} <= set(parameters)
    assert ExtraConfig().url == worker.MAX_WEBSOCKET_URL
    assert list(inspect.signature(QrHandler.show_qr).parameters) == ["self", "qr_url"]


def _run_pristine(script: str, *argv: str) -> subprocess.CompletedProcess:
    """Run ``script`` in a clean interpreter that never imports the worker."""
    return subprocess.run(
        [sys.executable, "-c", script, *argv],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )


def test_pristine_pymax_accepts_contact_without_contact_id():
    """2.3.1 rejected a ``contactId``-less CONTACT; 2.5.0 declares it optional — no shim needed."""
    result = _run_pristine(
        "import json, sys; "
        "from pymax.types.domain.attachments import ContactAttachment; "
        "from pymax.types.domain.chat import Chat; "
        "from pymax.types.domain.login import LoginResponse; "
        "chat = Chat.model_validate(json.loads(sys.argv[1])); "
        "assert isinstance(chat.last_message.attaches[0], ContactAttachment); "
        "assert chat.last_message.attaches[0].contact_id is None; "
        "login = LoginResponse.model_validate(json.loads(sys.argv[2])); "
        "assert login.chats[0].last_message.attaches[0].contact_id is None; "
        "ok = Chat.model_validate(json.loads(sys.argv[3])); "
        "assert ok.last_message.attaches[0].contact_id == 7",
        json.dumps(incomplete_contact_chat_payload()),
        json.dumps(incomplete_contact_login_payload()),
        json.dumps(incomplete_contact_chat_payload(contact_id=7)),
    )

    assert result.returncode == 0, result.stderr


def test_pristine_pymax_accepts_sticker_without_set_id():
    """2.3.1 rejected a ``setId``-less STICKER; 2.5.0 declares it optional — no shim needed."""
    result = _run_pristine(
        "import json, sys; "
        "from pymax.types.domain.attachments import StickerAttachment; "
        "from pymax.types.domain.chat import Chat; "
        "chat = Chat.model_validate(json.loads(sys.argv[1])); "
        "assert isinstance(chat.last_message.attaches[0], StickerAttachment); "
        "assert chat.last_message.attaches[0].set_id is None; "
        "assert chat.last_message.attaches[0].sticker_id == 54954683; "
        "ok = Chat.model_validate(json.loads(sys.argv[2])); "
        "assert ok.last_message.attaches[0].set_id == 12",
        json.dumps(incomplete_sticker_chat_payload()),
        json.dumps(incomplete_sticker_chat_payload(set_id=12)),
    )

    assert result.returncode == 0, result.stderr


def test_pristine_pymax_still_validates_the_other_attachment_fields():
    """Relaxing ``contactId``/``setId`` upstream did not turn attachment validation off."""
    result = _run_pristine(
        "import json, sys\n"
        "from pydantic import ValidationError\n"
        "from pymax.types.domain.chat import Chat\n"
        "def rejected(payload):\n"
        "    try:\n"
        "        Chat.model_validate(payload)\n"
        "    except ValidationError:\n"
        "        return True\n"
        "    return False\n"
        "photo = json.loads(sys.argv[1])\n"
        "photo['lastMessage']['attaches'] = [{'_type': 'PHOTO'}]\n"
        "assert rejected(photo), 'PHOTO without fields must still be rejected'\n"
        "for dropped in ('url', 'stickerId', 'width', 'time', 'stickerType', 'audio', 'height'):\n"
        "    sticker = json.loads(sys.argv[2])\n"
        "    del sticker['lastMessage']['attaches'][0][dropped]\n"
        "    assert rejected(sticker), dropped\n",
        json.dumps(incomplete_contact_chat_payload()),
        json.dumps(incomplete_sticker_chat_payload(set_id=1)),
    )

    assert result.returncode == 0, result.stderr


def test_worker_logs_only_the_remaining_frame_size_shim_on_import(tmp_path):
    """Importing the worker applies exactly one shim and names exactly that one in the log.

    Clean interpreter: in-process an earlier test may already have applied the shim,
    which would make the module-level flag ``False`` and the assertion vacuous.
    """
    env = {
        **os.environ,
        "ACCOUNT_ID": "42",
        "SESSIONS_DIR": str(tmp_path / "sessions"),
        "PYTHONPATH": str(REPO_ROOT),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import max_worker.main as worker; "
            "assert worker.WEBSOCKET_FRAME_SIZE_COMPATIBILITY_APPLIED is True",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("pymax_websocket_frame_size_compatibility_applied") == 1
    for lifted in ("contact_attachment", "sticker_attachment", "photo_upload"):
        assert f"pymax_{lifted}_compatibility_applied" not in result.stdout


@pytest.mark.asyncio
async def test_qr_provider_captures_link(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)

    state = await worker.create_client("+79990000000")
    provider = clients[0].kwargs["qr_provider"]
    await provider.show_qr("max://qr/secret-link")

    assert state.qr_code == "max://qr/secret-link"


@pytest.mark.asyncio
async def test_create_client_uses_webclient_contract(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)

    state = await worker.create_client("+79990000000")
    client = clients[0]
    assert client.kwargs["session_name"] == "session.db"
    assert client.kwargs["work_dir"] == str(worker.session_dir())
    assert isinstance(client.kwargs["extra_config"], FakeExtraConfig)
    assert inspect.signature(client.start_handler).parameters.keys() == {"connected_client"}

    await client.start_handler(client)
    assert state.is_connected is True
    assert state.sync_state == "ready"
    assert state.qr_code is None


@pytest.mark.asyncio
async def test_the_own_number_from_client_me_reaches_the_status_answer(worker, monkeypatch):
    """PHONE-14, D-04: the number MAX itself reports leaves the worker in /status."""
    clients = install_fake_client(monkeypatch, worker)
    await worker.create_client("+79990000000")
    client = clients[0]
    client.me = SimpleNamespace(contact=SimpleNamespace(phone=79991234567))

    await client.start_handler(client)
    answer = await worker.get_session_status("42")

    assert answer.get("phone") == "79991234567", "воркер MAX не отдал номер из client.me в /status"
    assert answer["connected"] is True
    assert set(answer) == {"connected", "exists", "syncState", "phone"}


@pytest.mark.asyncio
async def test_the_form_number_never_leaks_into_the_status_answer(worker, monkeypatch):
    """Owner decision OQ1: the number typed into the form is not what MAX reported."""
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("+79990000000")
    client = clients[0]
    client.me = SimpleNamespace(contact=SimpleNamespace(phone=None))

    await client.start_handler(client)
    answer = await worker.get_session_status("42")

    assert state.phone == "+79990000000"
    assert "phone" in answer and answer["phone"] is None


@pytest.mark.parametrize(
    "client",
    [
        pytest.param(FakeWebClient(), id="no-me-attribute"),
        pytest.param(SimpleNamespace(me=None), id="me-none"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=None)), id="contact-none"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone=None))), id="phone-none"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone=True))), id="bool-true"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone=False))), id="bool-false"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone=0))), id="zero"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone=-79991234567))), id="negative"),
        pytest.param(SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone="79991234567"))), id="string"),
    ],
)
def test_own_phone_of_answers_none_at_every_boundary(worker, client):
    assert worker.own_phone_of(client) is None


@pytest.mark.parametrize("number", [79991234567, 999999999999999])
def test_own_phone_of_converts_an_integer_exactly(worker, number):
    client = SimpleNamespace(me=SimpleNamespace(contact=SimpleNamespace(phone=number)))

    result = worker.own_phone_of(client)

    assert result == str(number)
    assert isinstance(result, str)
    assert "." not in result and "e" not in result.lower()
    assert result.isdigit()


def _break_own_phone_of(worker, monkeypatch):
    def explode(client):
        raise RuntimeError("boom 79991234567")

    monkeypatch.setattr(worker, "own_phone_of", explode)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["me-property-raises", "capture-raises"])
async def test_a_failing_capture_does_not_break_the_connection(worker, monkeypatch, failure):
    if failure == "me-property-raises":
        clients = install_fake_client(monkeypatch, worker, ThrowingMeWebClient)
    else:
        clients = install_fake_client(monkeypatch, worker)
        _break_own_phone_of(worker, monkeypatch)
    state = await worker.create_client("+79990000000")
    client = clients[0]

    await client.start_handler(client)

    assert state.is_connected is True
    assert state.ready_event.is_set()
    assert state.sync_state == "ready"
    assert state.own_phone is None
    assert (await worker.get_session_status("42"))["phone"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["number-reported", "me-property-raises", "capture-raises"])
async def test_the_capture_writes_no_number_to_the_log(worker, monkeypatch, caplog, path):
    if path == "me-property-raises":
        clients = install_fake_client(monkeypatch, worker, ThrowingMeWebClient)
    else:
        clients = install_fake_client(monkeypatch, worker)
    if path == "capture-raises":
        _break_own_phone_of(worker, monkeypatch)
    await worker.create_client("")
    client = clients[0]
    if path == "number-reported":
        client.me = SimpleNamespace(contact=SimpleNamespace(phone=79991234567))

    with caplog.at_level("DEBUG"):
        await client.start_handler(client)
        await worker.get_session_status("42")

    messages = [record.getMessage() for record in caplog.records]
    assert not [m for m in messages if "9991234567" in m]
    if path == "capture-raises":
        failures = [m for m in messages if "own_phone_capture_failed" in m]
        assert failures and "error_type=RuntimeError" in failures[0]
        assert "account_id=42" in failures[0]


@pytest.mark.asyncio
async def test_the_no_session_answer_carries_no_phone_field(worker):
    worker.session = None

    answer = await worker.get_session_status("42")

    assert "phone" not in answer


@pytest.mark.asyncio
async def test_existing_v2_session_reuses_library_store(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    directory = worker.session_dir()
    directory.mkdir(parents=True)
    create_session_db(directory / "session.db", "sessions", ("token", "device"))

    await worker.create_client("")

    assert clients[0].kwargs["extra_config"].kwargs.get("token") is None
    assert clients[0].kwargs["extra_config"].kwargs.get("device_id") is None
    assert worker.session_exists_on_disk() is True


@pytest.mark.asyncio
async def test_legacy_session_is_promoted_via_extra_config(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    directory = worker.session_dir()
    directory.mkdir(parents=True)
    database = directory / "session.db"
    create_session_db(database, "auth", ("legacy-token", "legacy-device"))

    await worker.create_client("")

    config = clients[0].kwargs["extra_config"].kwargs
    assert config["token"] == "legacy-token"
    assert config["device_id"] == "legacy-device"
    assert sqlite3.connect(database).execute("SELECT token FROM auth").fetchone() == ("legacy-token",)


MAX_WEBSOCKET_URL = "wss://api.oneme.ru/websocket"


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy", [False, True], ids=["qr-login", "legacy-session"])
async def test_client_dials_the_current_max_websocket_host(worker, monkeypatch, legacy):
    """MAX переехал с ``ws-api.oneme.ru`` на ``api.oneme.ru`` (замер со стенда 2026-11-23).

    Умолчание PyMax 2.3.1 — ``wss://ws-api.oneme.ru/websocket``: со стенда TCP до него не
    соединяется, рукопожатие падает по таймауту, и ни один воркер MAX не подключается
    (у живого аккаунта — с 2026-11-22T02:11Z). Новый адрес отвечает ``101 Switching
    Protocols``; PyMax 2.5.0 сменил на него своё умолчание. Воркер обязан передавать его
    явно на обоих путях входа — по QR и по перенесённой сессии.
    """
    clients = install_fake_client(monkeypatch, worker)
    if legacy:
        directory = worker.session_dir()
        directory.mkdir(parents=True)
        create_session_db(directory / "session.db", "auth", ("legacy-token", "legacy-device"))

    await worker.create_client("")

    config = clients[0].kwargs["extra_config"].kwargs
    assert config.get("url") == MAX_WEBSOCKET_URL, (
        f"воркер MAX подключается не к текущему адресу MAX: {config.get('url')!r}"
    )


def test_pinned_pymax_accepts_the_websocket_url_override():
    """Переопределение — штатный параметр ``ExtraConfig.url`` закреплённой PyMax, не подмена."""
    from pymax import ExtraConfig

    assert ExtraConfig(url=MAX_WEBSOCKET_URL).url == MAX_WEBSOCKET_URL


@pytest.mark.asyncio
@pytest.mark.parametrize("contents", [None, b"", b"not sqlite"])
async def test_empty_or_invalid_session_falls_back_to_qr(worker, monkeypatch, contents):
    clients = install_fake_client(monkeypatch, worker)
    directory = worker.session_dir()
    directory.mkdir(parents=True)
    database = directory / "session.db"
    if contents is not None:
        database.write_bytes(contents)

    await worker.create_client("")

    config = clients[0].kwargs["extra_config"].kwargs
    assert config.get("token") is None
    assert config.get("device_id") is None
    await clients[0].kwargs["qr_provider"].show_qr("max://qr/fallback")
    assert worker.session.qr_code == "max://qr/fallback"


@pytest.mark.asyncio
async def test_graceful_shutdown_closes_client_and_keeps_session(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    database = worker.session_dir() / "session.db"
    database.parent.mkdir(parents=True)
    create_session_db(database, "sessions", ("token", "device"))
    await worker.create_client("")
    worker.redis_cmd = SimpleNamespace(delete=AsyncMock(), aclose=AsyncMock())
    worker.redis_blpop = SimpleNamespace(aclose=AsyncMock())
    monkeypatch.setattr(worker.os, "_exit", lambda code: None)

    await worker.graceful_shutdown("test")

    clients[0].close.assert_awaited_once()
    assert database.exists()
    assert worker.redis_cmd is None
    assert worker.redis_blpop is None


@pytest.mark.asyncio
async def test_connect_redis_gives_blpop_a_socket_deadline_after_its_poll(worker, monkeypatch):
    command_client = SimpleNamespace(ping=AsyncMock())
    blocking_client = SimpleNamespace(ping=AsyncMock())
    from_url = MagicMock(side_effect=[command_client, blocking_client])
    monkeypatch.setattr(worker.aioredis, "from_url", from_url)

    await worker.connect_redis()

    command_options = from_url.call_args_list[0].kwargs
    blocking_options = from_url.call_args_list[1].kwargs
    assert command_options["socket_timeout"] == worker.REDIS_COMMAND_TIMEOUT
    assert blocking_options["socket_timeout"] > worker.BLPOP_TIMEOUT
    assert blocking_options["socket_timeout"] == worker.BLPOP_SOCKET_TIMEOUT


@pytest.mark.asyncio
async def test_consumer_idle_blpop_does_not_take_failure_retry_sleep(worker, monkeypatch):
    async def idle_once(*args, **kwargs):
        worker.consumer_running = False
        return None

    worker.redis_blpop = SimpleNamespace(blpop=idle_once)
    worker.IDLE_SHUTDOWN_SEC = 0
    sleep = AsyncMock()
    monkeypatch.setattr(worker.asyncio, "sleep", sleep)

    await worker.start_consumer()

    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_heartbeat_writer_sets_expiry(worker):
    worker.redis_cmd = SimpleNamespace(set=AsyncMock())

    await worker.write_heartbeat()

    worker.redis_cmd.set.assert_awaited_once()
    key, timestamp = worker.redis_cmd.set.await_args.args
    assert key == worker.HEARTBEAT_KEY
    assert timestamp.isdigit()
    assert worker.redis_cmd.set.await_args.kwargs == {"ex": worker.HEARTBEAT_TTL_SEC}


@pytest.mark.asyncio
async def test_graceful_shutdown_abandons_hanging_client_close_and_exits(worker, monkeypatch):
    async def never_finishes():
        await asyncio.Event().wait()

    client = SimpleNamespace(close=never_finishes)
    worker.session = SimpleNamespace(client=client, intentional_close=False)
    worker.redis_cmd = SimpleNamespace(delete=AsyncMock(), aclose=AsyncMock())
    worker.redis_blpop = SimpleNamespace(aclose=AsyncMock())
    worker.CLIENT_CLOSE_TIMEOUT_SEC = 0.01
    exit_process = MagicMock()
    monkeypatch.setattr(worker.os, "_exit", exit_process)

    await worker.graceful_shutdown("test_hanging_close")

    assert worker.session is None
    assert worker.redis_cmd is None
    assert worker.redis_blpop is None
    exit_process.assert_called_once_with(0)


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        ("redis://user:password@redis.internal:6380/2", "redis://redis.internal:6380/2"),
        ("not a redis url", worker_safe_fallback := "<redacted redis url>"),
    ],
)
def test_redacts_redis_url_credentials_and_fails_closed(worker, raw_url, expected):
    rendered = worker.render_redis_url_for_log(raw_url)

    assert rendered == expected
    assert "user" not in rendered
    assert "password" not in rendered


@pytest.mark.asyncio
async def test_health_and_startup_diagnostics_identify_build_without_redis_credentials(worker, monkeypatch):
    worker.MAX_WORKER_BUILD_REVISION = "abc123"
    worker.REDIS_URL = "redis://operator:secret@redis.internal:6380/2"
    log_info = MagicMock()
    monkeypatch.setattr(worker.log, "info", log_info)

    health = await worker.health()
    worker.log_startup()

    assert health["build_revision"] == "abc123"
    assert health["pymax_version"] == "2.5.0"
    rendered = " ".join(str(value) for call in log_info.call_args_list for value in call.args)
    assert "operator" not in rendered
    assert "secret" not in rendered
    assert "redis://redis.internal:6380/2" in rendered
    assert any("build_revision" in str(call.args[0]) for call in log_info.call_args_list)


def group(chat_id, title, timestamp, chat_type=None):
    from pymax.types.domain.enums import ChatType

    return SimpleNamespace(
        id=chat_id,
        title=title,
        type=chat_type or ChatType.CHAT,
        last_event_time=timestamp,
    )


@pytest.mark.asyncio
async def test_group_sync_merges_cache_and_paginated_groups(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    client = clients[0]
    state.is_connected = True
    client.chats = [group(1, "Cached", 900), group(9, "Dialog", 800, object())]
    client.fetch_chats.side_effect = [[group(1, "Duplicate", 700), group(2, "Paged", 600)], []]
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())

    await worker.start_group_sync()

    assert state.groups == [{"id": "1", "name": "Duplicate"}, {"id": "2", "name": "Paged"}]
    assert client.fetch_chats.await_args_list[0].kwargs == {"marker": None}
    assert client.fetch_chats.await_args_list[1].kwargs == {"marker": 599}


@pytest.mark.asyncio
async def test_group_sync_accepts_pymax_chat_with_incomplete_contact(worker, monkeypatch):
    from pymax.types.domain.chat import Chat

    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    client = clients[0]
    state.is_connected = True
    contact_chat = Chat.model_validate(incomplete_contact_chat_payload())
    client.chats = [contact_chat]
    client.fetch_chats.side_effect = [[contact_chat], []]
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())

    await worker.start_group_sync()

    assert state.sync_state == "ready"
    assert state.groups == [{"id": "1", "name": "CONTACT group"}]


@pytest.mark.asyncio
async def test_group_sync_accepts_pymax_chat_with_set_id_less_sticker(worker, monkeypatch):
    """Issue #34: one setId-less STICKER killed every group_fetch_attempt for the account.

    This is the prod failure at its own altitude — parsing the fetched chat and running it
    all the way through ``start_group_sync`` — not just the model in isolation.
    """
    from pymax.types.domain.chat import Chat

    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    client = clients[0]
    state.is_connected = True
    sticker_chat = Chat.model_validate(incomplete_sticker_chat_payload())
    client.chats = [sticker_chat]
    client.fetch_chats.side_effect = [[sticker_chat], []]
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())

    await worker.start_group_sync()

    assert state.sync_state == "ready"
    assert state.groups == [{"id": "1", "name": "STICKER group"}]


@pytest.mark.asyncio
async def test_group_sync_uses_integer_timestamp_markers_and_stops(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    client = clients[0]
    state.is_connected = True
    client.fetch_chats.side_effect = [[group(1, "First", 100)], [group(2, "No progress", 100)]]
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())

    await worker.start_group_sync()

    markers = [call.kwargs["marker"] for call in client.fetch_chats.await_args_list]
    assert markers == [None, 99]
    assert all(isinstance(marker, int) for marker in markers[1:])


@pytest.mark.asyncio
async def test_group_sync_stops_on_non_integer_timestamp(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    client = clients[0]
    state.is_connected = True
    client.fetch_chats.side_effect = [[group(1, "Malformed timestamp", "unknown")]]
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())

    await worker.start_group_sync()

    assert [call.kwargs["marker"] for call in client.fetch_chats.await_args_list] == [None]


@pytest.mark.asyncio
async def test_text_send_uses_webclient_message_contract(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    state.is_connected = True
    state.connected_at = 0
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())

    await worker.send_message({"task_id": "text", "group_external_id": "17", "ad_text": "Hello"})

    clients[0].send_message.assert_awaited_once_with(chat_id=17, text="Hello")


class FakeResponse:
    headers = {"content-type": "image/png"}
    content = b"png-data"

    def raise_for_status(self):
        return None


class FakeHttpClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, url):
        if self.error:
            raise self.error
        return self.response


@pytest.mark.asyncio
async def test_image_send_uses_photo_attachments_and_cleans_tempfiles(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    state.is_connected = True
    state.connected_at = 0
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(worker.httpx, "AsyncClient", lambda timeout: FakeHttpClient(response=FakeResponse()))

    await worker.send_message({"task_id": "image", "group_external_id": "17", "ad_text": "Caption", "ad_images": ["https://image.test/a"]})

    call = clients[0].send_message.await_args
    assert call.kwargs["chat_id"] == 17
    assert call.kwargs["text"] == "Caption"
    attachments = call.kwargs["attachments"]
    assert len(attachments) == 1
    assert str(attachments[0].path).endswith(".png")
    assert not Path(attachments[0].path).exists()


@pytest.mark.asyncio
async def test_all_failed_images_fall_back_to_text(worker, monkeypatch):
    clients = install_fake_client(monkeypatch, worker)
    state = await worker.create_client("")
    state.is_connected = True
    state.connected_at = 0
    monkeypatch.setattr(worker.asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(worker.httpx, "AsyncClient", lambda timeout: FakeHttpClient(error=httpx.ConnectError("offline")))

    await worker.send_message({"task_id": "fallback", "group_external_id": "17", "ad_text": "Fallback", "ad_images": ["https://image.test/a"]})

    clients[0].send_message.assert_awaited_once_with(chat_id=17, text="Fallback")


# ---- PHOTO_UPLOAD: MAX dropped ``photoIds`` from the one-shot upload URL ----

# The shape MAX has answered PHOTO_UPLOAD with since 2026-09-25 (for every request
# since 2026-10-02): a one-shot URL that names no photo.
UPLOAD_URL_WITHOUT_PHOTO_IDS = "https://iu.oneme.ru/uploadImage?r=one-shot-token"
# The shapes PyMax 2.5.0 reads the photo id from: ``photoIds`` (the original) or ``photos``.
UPLOAD_URL_WITH_PHOTO_IDS = "https://iu.oneme.ru/uploadImage?photoIds=777&r=one-shot-token"
UPLOAD_URL_WITH_PHOTOS_PARAM = "https://iu.oneme.ru/uploadImage?photos=777&r=one-shot-token"


class FakeUploadPost:
    status = 200

    def __init__(self, body):
        self.body = body

    async def json(self):
        return self.body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class FakeUploadSession:
    def __init__(self, results, posted):
        self.results = results
        self.posted = posted

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def post(self, url, data, **kwargs):
        self.posted.append(url)
        return FakeUploadPost(self.results.pop(0))


def pymax_photo_send_harness(monkeypatch, upload_urls, upload_results):
    """Real PyMax 2.5.0 MessageService + UploadService; only MAX's socket and upload HTTP are faked.

    Returns the message service, every (opcode, payload) sent over the socket, and every
    URL the photo bytes were POSTed to.
    """
    import aiohttp
    from pymax.api.messages.service import MessageService
    from pymax.api.uploads.service import UploadService
    from pymax.protocol import Opcode

    urls = list(upload_urls)
    results = list(upload_results)
    invoked = []
    posted = []

    async def invoke(opcode, payload=None):
        invoked.append((opcode, payload))
        if opcode == Opcode.PHOTO_UPLOAD:
            return SimpleNamespace(payload={"url": urls.pop(0)})
        return SimpleNamespace(payload={"id": 9, "time": 100, "type": "USER"})

    monkeypatch.setattr(aiohttp, "ClientSession", lambda **kwargs: FakeUploadSession(results, posted))
    app = SimpleNamespace(
        invoke=invoke,
        config=SimpleNamespace(proxy=None),
        dispatcher=SimpleNamespace(on_internal=lambda event: (lambda handler: handler)),
    )
    app.api = SimpleNamespace(uploads=UploadService(app))
    app.api.messages = MessageService(app)
    return app.api.messages, invoked, posted


def sent_opcodes(invoked):
    return [opcode for opcode, _ in invoked]


def sent_attaches(invoked):
    from pymax.protocol import Opcode

    [payload] = [payload for opcode, payload in invoked if opcode == Opcode.MSG_SEND]
    return payload["message"]["attaches"]


@pytest.mark.asyncio
@pytest.mark.parametrize("result_key", ["0", "4242"])
async def test_photo_send_survives_upload_url_without_photo_ids(monkeypatch, result_key):
    """MAX's upload URL no longer names the photo (2.3.1 failed every send on it).

    PyMax 2.5.0 takes the single entry of a ``count=1`` upload result as our photo
    whatever its key — the behavior the retired shim added.
    """
    from pymax import Photo
    from pymax.types import AttachmentType

    messages, invoked, posted = pymax_photo_send_harness(
        monkeypatch,
        [UPLOAD_URL_WITHOUT_PHOTO_IDS],
        [{"photos": {result_key: {"token": "tok-new"}}}],
    )

    await messages.send_message(
        chat_id=17, text="Caption", attachments=[Photo(raw=b"png-data", name="a.png")]
    )

    assert posted == [UPLOAD_URL_WITHOUT_PHOTO_IDS]
    assert sent_attaches(invoked) == [{"_type": AttachmentType.PHOTO, "photoToken": "tok-new"}]


@pytest.mark.asyncio
async def test_photo_album_without_photo_ids_uploads_each_photo_on_its_own_url(monkeypatch):
    """A multi-image ad is N independent ``count=1`` uploads; tokens keep the photo order."""
    from pymax import Photo
    from pymax.protocol import Opcode

    first = "https://iu.oneme.ru/uploadImage?r=first"
    second = "https://iu.oneme.ru/uploadImage?r=second"
    messages, invoked, posted = pymax_photo_send_harness(
        monkeypatch,
        [first, second],
        [{"photos": {"0": {"token": "tok-1"}}}, {"photos": {"0": {"token": "tok-2"}}}],
    )

    await messages.send_message(
        chat_id=17,
        text="Album",
        attachments=[Photo(raw=b"1", name="1.png"), Photo(raw=b"2", name="2.jpg")],
    )

    assert posted == [first, second]
    upload_requests = [payload for opcode, payload in invoked if opcode == Opcode.PHOTO_UPLOAD]
    # 2.5.0 adds ``type``/``uploaderType`` to the request; what matters is one photo per upload.
    assert len(upload_requests) == 2
    assert all(request["count"] == 1 and request["profile"] is False for request in upload_requests)
    assert [attach["photoToken"] for attach in sent_attaches(invoked)] == ["tok-1", "tok-2"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "photos",
    [{}, {"0": {"token": "tok-a"}, "1": {"token": "tok-b"}}],
    ids=["no-entry", "two-entries"],
)
async def test_photo_upload_without_photo_ids_refuses_to_guess_the_token(monkeypatch, photos):
    """Without an id in the URL only a single-entry result is unambiguous; never attach a guess."""
    from pymax import Photo
    from pymax.exceptions import UploadError
    from pymax.protocol import Opcode

    messages, invoked, _ = pymax_photo_send_harness(
        monkeypatch, [UPLOAD_URL_WITHOUT_PHOTO_IDS], [{"photos": photos}]
    )

    with pytest.raises(UploadError, match=r"Expected one photo in upload response"):
        await messages.send_message(
            chat_id=17, text="Caption", attachments=[Photo(raw=b"png-data", name="a.png")]
        )

    assert Opcode.MSG_SEND not in sent_opcodes(invoked)


@pytest.mark.asyncio
async def test_photo_send_keys_token_by_photo_ids_when_url_carries_them(monkeypatch):
    """MAX rolled the change out gradually; the URL that still names the photo keeps the exact lookup."""
    from pymax import Photo
    from pymax.types import AttachmentType

    messages, invoked, _ = pymax_photo_send_harness(
        monkeypatch,
        [UPLOAD_URL_WITH_PHOTO_IDS],
        [{"photos": {"111": {"token": "someone-else"}, "777": {"token": "tok-777"}}}],
    )

    await messages.send_message(
        chat_id=17, text="Caption", attachments=[Photo(raw=b"png-data", name="a.png")]
    )

    assert sent_attaches(invoked) == [{"_type": AttachmentType.PHOTO, "photoToken": "tok-777"}]


@pytest.mark.asyncio
async def test_photo_send_keys_token_by_photos_parameter_when_url_carries_it(monkeypatch):
    """2.5.0 also reads the id from ``photos=``; it wins over a two-entry result."""
    from pymax import Photo
    from pymax.types import AttachmentType

    messages, invoked, _ = pymax_photo_send_harness(
        monkeypatch,
        [UPLOAD_URL_WITH_PHOTOS_PARAM],
        [{"photos": {"111": {"token": "someone-else"}, "777": {"token": "tok-777"}}}],
    )

    await messages.send_message(
        chat_id=17, text="Caption", attachments=[Photo(raw=b"png-data", name="a.png")]
    )

    assert sent_attaches(invoked) == [{"_type": AttachmentType.PHOTO, "photoToken": "tok-777"}]


@pytest.mark.asyncio
async def test_photo_ids_url_whose_id_is_missing_from_the_result_still_fails(monkeypatch):
    """When MAX does name the photo, a result without that id is an error, not a positional pick."""
    from pymax import Photo
    from pymax.exceptions import UploadError
    from pymax.protocol import Opcode

    messages, invoked, _ = pymax_photo_send_harness(
        monkeypatch, [UPLOAD_URL_WITH_PHOTO_IDS], [{"photos": {"111": {"token": "someone-else"}}}]
    )

    with pytest.raises(UploadError, match=r"does not contain token for photo_id=777"):
        await messages.send_message(
            chat_id=17, text="Caption", attachments=[Photo(raw=b"png-data", name="a.png")]
        )

    assert Opcode.MSG_SEND not in sent_opcodes(invoked)


_FRAME_PROBE = (
    "import asyncio, sys\n"
    "from websockets.asyncio import client\n"
    "from pymax.transport.websocket import WebSocketTransport\n"
    "seen = {}\n"
    "def captured(*args, **kwargs):\n"
    "    seen.clear(); seen['url'] = args[0]; seen.update(kwargs)\n"
    "    return asyncio.sleep(0)\n"
    "client.connect = captured\n"
    "def dial(proxy):\n"
    "    asyncio.run(WebSocketTransport('wss://api.oneme.ru/websocket', proxy).connect())\n"
    "    return dict(seen)\n"
    "def check(expected_max_size):\n"
    "    for proxy in (None, 'http://proxy:8080'):\n"
    "        kw = dial(proxy)\n"
    "        assert kw['max_size'] == expected_max_size, kw\n"
    "        assert str(kw['origin']) == 'https://web.max.ru', kw\n"
    "        assert kw.get('proxy') == proxy, kw\n"
    "check(10 * 1024 * 1024)\n"
    "from max_worker import pymax_compat\n"
    "assert pymax_compat.apply_websocket_frame_size_compatibility() is True\n"
    "assert pymax_compat.apply_websocket_frame_size_compatibility() is False\n"
    "check(None)\n"
)


def test_websocket_frame_size_compatibility_lifts_the_10mib_cap():
    """Pristine 2.5.0 caps frames at 10 MiB; the shim alone removes the cap.

    MAX sends the whole chat list in one login frame (2.7 MB measured on a large
    account) and the frame grows with the account.  The cap is checked on both
    connect branches (with and without a proxy), and the origin is preserved.
    """
    result = _run_pristine(_FRAME_PROBE)

    assert result.returncode == 0, result.stderr


def test_websocket_frame_size_compatibility_fails_closed_on_unaudited_pymax():
    result = _run_pristine(
        "from max_worker import pymax_compat; "
        "pymax_compat.PYMAX_VERSION = '2.5.1'; "
        "pymax_compat.apply_websocket_frame_size_compatibility()"
    )

    assert result.returncode != 0
    assert "RuntimeError" in result.stderr
    assert "2.5.1" in result.stderr
    assert "2.5.0" in result.stderr


def test_requirements_pin_maxapi_2_5_0():
    import tomllib

    requirements = (REPO_ROOT / "max_worker/requirements.txt").read_text().splitlines()
    assert requirements.count("maxapi-python==2.5.0") == 1
    assert not any(line.startswith("maxapi-python>=") for line in requirements)

    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    dev_group = pyproject["dependency-groups"]["dev"]
    assert [item for item in dev_group if item.startswith("maxapi-python")] == ["maxapi-python==2.5.0"]

    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text())
    locked = [package["version"] for package in lock["package"] if package["name"] == "maxapi-python"]
    assert locked == ["2.5.0"]


# ---- Session transfer: a live account's ``session.db`` written by 2.3.1 is opened by 2.5.0 ----

# The exact DDL PyMax 2.3.1 wrote (9 columns, no ``user_agent``) — the format of live sessions.
SESSIONS_DDL_2_3_1 = """
CREATE TABLE sessions (
    token TEXT NOT NULL PRIMARY KEY,
    device_id TEXT NOT NULL,
    phone TEXT NOT NULL,
    mt_instance_id TEXT NOT NULL DEFAULT '',
    chats_sync INTEGER NOT NULL DEFAULT -1,
    contacts_sync INTEGER NOT NULL DEFAULT -1,
    drafts_sync INTEGER NOT NULL DEFAULT -1,
    presence_sync INTEGER NOT NULL DEFAULT -1,
    config_hash TEXT NOT NULL DEFAULT ''
)
"""


def create_session_db_2_3_1(path: Path, token: str, device_id: str) -> None:
    connection = sqlite3.connect(path)
    connection.execute(SESSIONS_DDL_2_3_1)
    connection.execute(
        "INSERT INTO sessions (token, device_id, phone) VALUES (?, ?, ?)", (token, device_id, "")
    )
    connection.commit()
    connection.close()


def session_columns(path: Path) -> list[str]:
    connection = sqlite3.connect(path)
    try:
        return [row[1] for row in connection.execute("PRAGMA table_info(sessions)")]
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_a_2_3_1_session_db_is_read_and_migrated_in_place_by_the_real_2_5_0_store(worker):
    """The live account's token and device_id survive the move; the library adds ``user_agent``."""
    from pymax.session.store import SessionStore

    directory = worker.session_dir()
    directory.mkdir(parents=True)
    database = worker.session_db_path()
    create_session_db_2_3_1(database, "live-token", "live-device")
    assert "user_agent" not in session_columns(database)

    assert worker.has_reusable_session() is True

    store = SessionStore(work_dir=str(directory), db_name="session.db")
    try:
        loaded = await store.load_session()
    finally:
        await store.close()

    assert loaded is not None
    assert loaded.token == "live-token"
    assert loaded.device_id == "live-device"
    assert loaded.user_agent is None
    assert store.conn is None
    assert "user_agent" in session_columns(database)
    connection = sqlite3.connect(database)
    try:
        rows = connection.execute("SELECT token, device_id FROM sessions").fetchall()
    finally:
        connection.close()
    assert rows == [("live-token", "live-device")]
    assert worker.has_reusable_session() is True


@pytest.mark.asyncio
async def test_a_2_3_1_session_row_without_a_token_is_not_reusable(worker):
    """Teeth for the test above: the worker refuses a row that holds no token."""
    directory = worker.session_dir()
    directory.mkdir(parents=True)
    create_session_db_2_3_1(worker.session_db_path(), "", "live-device")

    assert worker.has_reusable_session() is False


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy", [False, True], ids=["qr-login", "legacy-session"])
async def test_worker_extra_config_parameters_are_accepted_by_the_real_2_5_0_extra_config(
    worker, monkeypatch, legacy
):
    from pymax import ExtraConfig

    clients = install_fake_client(monkeypatch, worker)
    if legacy:
        directory = worker.session_dir()
        directory.mkdir(parents=True)
        create_session_db(directory / "session.db", "auth", ("legacy-token", "legacy-device"))

    await worker.create_client("")

    kwargs = clients[0].kwargs["extra_config"].kwargs
    config = ExtraConfig(**kwargs)

    assert config.url == MAX_WEBSOCKET_URL
    assert config.reconnect is True
    # A revoked token restarts QR login instead of crashing the worker (2.5.0 default).
    assert config.relogin is True
    if legacy:
        assert config.token == "legacy-token"
        assert config.device_id == "legacy-device"
    else:
        assert config.token is None
        assert config.device_id is None


@pytest.mark.asyncio
async def test_real_web_client_keeps_the_session_where_the_worker_looks_and_carries_the_legacy_device_id(
    worker,
):
    """No fakes: the WebClient the worker builds stores its session at ``session_db_path()``.

    ``_prepare_config`` is a private PyMax hook; it is the one place the config the library
    will actually run with is observable without opening a connection.
    """
    from pymax.session.store import SessionStore

    directory = worker.session_dir()
    directory.mkdir(parents=True)
    create_session_db(directory / "session.db", "auth", ("legacy-token", "legacy-device"))

    state = await worker.create_client("")
    config = await state.client._prepare_config()

    assert Path(config.work_dir) / config.session_name == worker.session_db_path()
    assert SessionStore(config.work_dir, config.session_name).db_path == str(worker.session_db_path())
    assert config.token == "legacy-token"
    assert config.device.device_id == "legacy-device"
    assert config.relogin is True
    assert state.client.extra_config.url == MAX_WEBSOCKET_URL

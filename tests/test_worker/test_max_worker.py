"""Offline compatibility coverage for the MAX worker's PyMax 2.3.1 migration."""

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


def install_fake_client(monkeypatch, worker):
    clients = []

    def construct(**kwargs):
        client = FakeWebClient(**kwargs)
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


def test_pymax_2_3_1_contract():
    import pymax
    from pymax import ExtraConfig, Photo, WebClient

    assert pymax.__version__ == "2.3.1"
    for symbol in (WebClient, ExtraConfig, Photo):
        assert symbol is not None
    parameters = inspect.signature(WebClient).parameters
    assert {"session_name", "work_dir", "extra_config", "qr_provider"} <= set(parameters)


def test_unmodified_pymax_rejects_contact_without_contact_id():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from pymax.types.domain.chat import Chat; "
            "Chat.model_validate({'id': 1, 'type': 'CHAT', 'status': 'ACTIVE', "
            "'owner': 2, 'lastMessage': {'id': 9, 'time': 100, 'type': 'USER', "
            "'attaches': [{'_type': 'CONTACT'}]}})",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "contactId" in result.stderr


def test_contact_compatibility_accepts_raw_chat_and_login_payloads_idempotently():
    from pymax.types.domain.attachments import ContactAttachment
    from pymax.types.domain.chat import Chat
    from pymax.types.domain.login import LoginResponse

    from max_worker.pymax_compat import apply_contact_attachment_compatibility

    assert apply_contact_attachment_compatibility() is True
    assert apply_contact_attachment_compatibility() is False

    chat = Chat.model_validate(incomplete_contact_chat_payload())
    login = LoginResponse.model_validate(incomplete_contact_login_payload())

    assert isinstance(chat.last_message.attaches[0], ContactAttachment)
    assert chat.last_message.attaches[0].contact_id is None
    assert login.chats[0].last_message.attaches[0].contact_id is None


def test_contact_compatibility_preserves_ids_and_other_attachment_validation():
    from pydantic import ValidationError
    from pymax.types.domain.chat import Chat

    from max_worker.pymax_compat import apply_contact_attachment_compatibility

    apply_contact_attachment_compatibility()
    identified_contact = Chat.model_validate(incomplete_contact_chat_payload(contact_id=7))

    assert identified_contact.last_message.attaches[0].contact_id == 7

    malformed_photo = incomplete_contact_chat_payload()
    malformed_photo["lastMessage"]["attaches"] = [{"_type": "PHOTO"}]
    with pytest.raises(ValidationError):
        Chat.model_validate(malformed_photo)


def test_unmodified_pymax_rejects_sticker_without_set_id():
    """Pristine PyMax 2.3.1 is the reason group sync dies — reproduce it in a clean interpreter."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, sys; "
            "from pymax.types.domain.chat import Chat; "
            "Chat.model_validate(json.loads(sys.argv[1]))",
            json.dumps(incomplete_sticker_chat_payload()),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "setId" in result.stderr


def test_sticker_compatibility_parses_chat_in_a_clean_interpreter():
    """Order-independent proof: the shim alone makes a setId-less STICKER chat parse."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, sys; "
            "from max_worker.pymax_compat import apply_sticker_attachment_compatibility; "
            "assert apply_sticker_attachment_compatibility() is True; "
            "from pymax.types.domain.chat import Chat; "
            "chat = Chat.model_validate(json.loads(sys.argv[1])); "
            "assert chat.last_message.attaches[0].set_id is None; "
            "assert chat.last_message.attaches[0].sticker_id == 54954683",
            json.dumps(incomplete_sticker_chat_payload()),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, result.stderr


def test_sticker_compatibility_accepts_raw_chat_and_login_payloads_idempotently():
    from pymax.types.domain.attachments import StickerAttachment
    from pymax.types.domain.chat import Chat
    from pymax.types.domain.login import LoginResponse

    from max_worker.pymax_compat import apply_sticker_attachment_compatibility

    assert apply_sticker_attachment_compatibility() is True
    assert apply_sticker_attachment_compatibility() is False

    chat = Chat.model_validate(incomplete_sticker_chat_payload())
    login_payload = incomplete_contact_login_payload()
    login_payload["chats"] = [incomplete_sticker_chat_payload()]
    login = LoginResponse.model_validate(login_payload)

    assert isinstance(chat.last_message.attaches[0], StickerAttachment)
    assert chat.last_message.attaches[0].set_id is None
    assert login.chats[0].last_message.attaches[0].set_id is None


def test_sticker_compatibility_preserves_set_ids_and_other_sticker_validation():
    from pydantic import ValidationError
    from pymax.types.domain.chat import Chat

    from max_worker.pymax_compat import apply_sticker_attachment_compatibility

    apply_sticker_attachment_compatibility()

    for set_id in (0, 1, 54954683):
        identified = Chat.model_validate(incomplete_sticker_chat_payload(set_id=set_id))
        assert identified.last_message.attaches[0].set_id == set_id

    # The seam is exactly one field wide: every other required STICKER field still validates.
    for dropped in ("url", "stickerId", "width", "time", "stickerType", "audio", "height"):
        malformed = incomplete_sticker_chat_payload(set_id=1)
        del malformed["lastMessage"]["attaches"][0][dropped]
        with pytest.raises(ValidationError):
            Chat.model_validate(malformed)


def test_worker_applies_sticker_compatibility_on_import(tmp_path):
    """Importing the worker must relax STICKER before any client exists, and say so in the log.

    Runs in a clean interpreter: in-process the shim may already have been applied by an
    earlier test, which would make the module-level flag ``False`` and the assertion vacuous.
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
            "import json, sys; "
            "import max_worker.main as worker; "
            "assert worker.STICKER_ATTACHMENT_COMPATIBILITY_APPLIED is True; "
            "from pymax.types.domain.chat import Chat; "
            "chat = Chat.model_validate(json.loads(sys.argv[1])); "
            "assert chat.last_message.attaches[0].set_id is None",
            json.dumps(incomplete_sticker_chat_payload()),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, result.stderr
    assert "pymax_sticker_attachment_compatibility_applied" in result.stdout


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
    assert health["pymax_version"] == "2.3.1"
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
# The shape PyMax 2.3.1 was written against.
UPLOAD_URL_WITH_PHOTO_IDS = "https://iu.oneme.ru/uploadImage?photoIds=777&r=one-shot-token"


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

    def post(self, url, data):
        self.posted.append(url)
        return FakeUploadPost(self.results.pop(0))


def pymax_photo_send_harness(monkeypatch, upload_urls, upload_results):
    """Real PyMax 2.3.1 MessageService + UploadService; only MAX's socket and upload HTTP are faked.

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
async def test_photo_send_survives_upload_url_without_photo_ids(worker, monkeypatch, result_key):
    """Every MAX photo send failed with "Photo upload URL does not contain photoIds".

    MAX's upload URL no longer names the photo.  A ``count=1`` upload result holds
    exactly one entry, and that entry is our photo whatever its key.
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
async def test_photo_album_without_photo_ids_uploads_each_photo_on_its_own_url(worker, monkeypatch):
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
    assert upload_requests == [{"count": 1, "profile": False}] * 2
    assert [attach["photoToken"] for attach in sent_attaches(invoked)] == ["tok-1", "tok-2"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "photos",
    [{}, {"0": {"token": "tok-a"}, "1": {"token": "tok-b"}}],
    ids=["no-entry", "two-entries"],
)
async def test_photo_upload_without_photo_ids_refuses_to_guess_the_token(worker, monkeypatch, photos):
    """Without an id in the URL only a single-entry result is unambiguous; never attach a guess."""
    from pymax import Photo
    from pymax.exceptions import UploadError
    from pymax.protocol import Opcode

    messages, invoked, _ = pymax_photo_send_harness(
        monkeypatch, [UPLOAD_URL_WITHOUT_PHOTO_IDS], [{"photos": photos}]
    )

    with pytest.raises(UploadError, match=r"expected exactly 1"):
        await messages.send_message(
            chat_id=17, text="Caption", attachments=[Photo(raw=b"png-data", name="a.png")]
        )

    assert Opcode.MSG_SEND not in sent_opcodes(invoked)


@pytest.mark.asyncio
async def test_photo_send_still_keys_token_by_photo_ids_when_url_carries_them(worker, monkeypatch):
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
async def test_photo_ids_url_whose_id_is_missing_from_the_result_still_fails(worker, monkeypatch):
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


def test_unmodified_pymax_rejects_upload_url_without_photo_ids():
    """Pristine PyMax 2.3.1 is why every MAX photo send fails — keep that reproducible.

    Runs in a clean interpreter that never imports the worker.  The day the pin moves
    to a release that no longer needs ``photoIds``, this fails: drop the shim then.
    """
    script = (
        "import asyncio, sys\n"
        "from types import SimpleNamespace\n"
        "from pymax import Photo\n"
        "from pymax.api.uploads.service import UploadService\n"
        "async def invoke(opcode, payload=None):\n"
        "    return SimpleNamespace(payload={'url': sys.argv[1]})\n"
        "app = SimpleNamespace(invoke=invoke, config=SimpleNamespace(proxy=None),\n"
        "    dispatcher=SimpleNamespace(on_internal=lambda event: (lambda handler: handler)))\n"
        "asyncio.run(UploadService(app).upload_photo(Photo(raw=b'png-data', name='a.png')))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, UPLOAD_URL_WITHOUT_PHOTO_IDS],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "UploadError: Photo upload URL does not contain photoIds" in result.stderr


def test_worker_applies_photo_upload_compatibility_on_import(tmp_path):
    """Importing the worker must fix photo uploads before any client exists, and say so in the log.

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
            "assert worker.PHOTO_UPLOAD_COMPATIBILITY_APPLIED is True",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, result.stderr
    assert "pymax_photo_upload_compatibility_applied" in result.stdout


def test_photo_upload_compatibility_is_idempotent_and_fails_closed_on_unaudited_pymax():
    applied = subprocess.run(
        [
            sys.executable,
            "-c",
            "from max_worker import pymax_compat; "
            "assert pymax_compat.apply_photo_upload_compatibility() is True; "
            "assert pymax_compat.apply_photo_upload_compatibility() is False",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
    assert applied.returncode == 0, applied.stderr

    unaudited = subprocess.run(
        [
            sys.executable,
            "-c",
            "from max_worker import pymax_compat; "
            "pymax_compat.PYMAX_VERSION = '2.4.1'; "
            "pymax_compat.apply_photo_upload_compatibility()",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
    assert unaudited.returncode != 0
    assert "RuntimeError" in unaudited.stderr
    assert "2.4.1" in unaudited.stderr


def test_websocket_frame_size_compatibility_lifts_the_1mib_cap():
    """A clean interpreter proves the shim alone removes the frame-size cap.

    Without it, MAX closes the login frame with 1009 "message too big" for any
    account whose chat list exceeds 1 MiB, and the worker reconnect-loops forever.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import asyncio, inspect; "
            "from websockets.asyncio import client; "
            "from pymax.transport.websocket import WebSocketTransport; "
            "assert inspect.signature(client.connect).parameters['max_size'].default == 1048576; "
            "from max_worker.pymax_compat import apply_websocket_frame_size_compatibility; "
            "assert apply_websocket_frame_size_compatibility() is True; "
            "assert apply_websocket_frame_size_compatibility() is False; "
            "seen = {}; "
            "captured = lambda *a, **kw: seen.update(kw) or asyncio.sleep(0); "
            "client.connect = captured; "
            "t = WebSocketTransport('wss://ws-api.oneme.ru/websocket', None); "
            "asyncio.run(t.connect()); "
            "assert seen['max_size'] is None, seen; "
            "t2 = WebSocketTransport('wss://ws-api.oneme.ru/websocket', 'http://proxy:8080'); "
            "asyncio.run(t2.connect()); "
            "assert seen['max_size'] is None and seen['proxy'] == 'http://proxy:8080', seen",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, result.stderr


def test_requirements_pin_maxapi_2_3_1():
    requirements = Path("max_worker/requirements.txt").read_text().splitlines()
    assert requirements.count("maxapi-python==2.3.1") == 1
    assert not any(line.startswith("maxapi-python>=") for line in requirements)

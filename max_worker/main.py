# ============================================================
# max_worker/main.py — Per-account MAX messenger worker
# Manages ONE pymax session, consumes tasks from Redis queue,
# publishes results, self-shuts down after idle timeout.
# ============================================================

import asyncio
import json
import logging
import os
import random
import signal
import socket
import sqlite3
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
import redis.asyncio as aioredis
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pymax import ExtraConfig, Photo, WebClient
from pymax.types.domain.enums import ChatType


# ---- 1. Config (env vars) ----

ACCOUNT_ID = os.environ.get("ACCOUNT_ID")
if not ACCOUNT_ID:
    print("FATAL: ACCOUNT_ID env var is required", file=sys.stderr)
    sys.exit(1)

PORT = int(os.environ.get("PORT", "3000"))
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
SESSIONS_DIR = os.environ.get("SESSIONS_DIR", "./sessions")
IDLE_SHUTDOWN_SEC = int(os.environ.get("IDLE_SHUTDOWN_SEC", "300"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "8"))
PHONE = os.environ.get("PHONE", "")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

MAX_RECONNECT_ATTEMPTS = 5
BLPOP_TIMEOUT = 5  # seconds — short so we can check idle timer frequently
REDIS_COMMAND_TIMEOUT = BLPOP_TIMEOUT
BLPOP_SOCKET_TIMEOUT = BLPOP_TIMEOUT + 1
HEARTBEAT_INTERVAL_SEC = 30
HEARTBEAT_TTL_SEC = HEARTBEAT_INTERVAL_SEC * 3
CLIENT_CLOSE_TIMEOUT_SEC = 5
SESSION_NAME = "session.db"

# Retry delays for failed task sends (seconds)
RETRY_DELAYS = [15, 60, 180]
MAX_RETRIES = len(RETRY_DELAYS)

# Redis key patterns
QUEUE_KEY = f"max:queue:{ACCOUNT_ID}"
RESULTS_KEY = "max:results"
HEARTBEAT_KEY = f"max:heartbeat:{ACCOUNT_ID}"
ENDPOINT_KEY = f"max:endpoint:{ACCOUNT_ID}"

# Logging — JSON format for Promtail/Loki collection
class _JsonFormatter(logging.Formatter):
    def format(self, record):
        obj = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
            "account_id": ACCOUNT_ID,
        }
        if record.exc_info and record.exc_info[0]:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_JsonFormatter())
logging.root.handlers = [_handler]
logging.root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
log = logging.getLogger("max_worker")

# Force all loggers through our JSON formatter (no duplicate plain-text lines)
for _ln in ("uvicorn", "uvicorn.access", "uvicorn.error", "pymax", "pymax.core"):
    _l = logging.getLogger(_ln)
    _l.handlers.clear()
    _l.propagate = True
# Suppress noisy loggers
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Ensure sessions directory exists
Path(SESSIONS_DIR).mkdir(parents=True, exist_ok=True)


# ---- 2. Redis connections ----

redis_cmd: aioredis.Redis | None = None  # Command connection — for SET, RPUSH, etc.
redis_blpop: aioredis.Redis | None = None  # Blocking connection — dedicated to BLPOP


def render_redis_url_for_log(redis_url: str) -> str:
    """Preserve a Redis endpoint for diagnostics without exposing credentials."""
    fallback = "<redacted redis url>"
    try:
        parsed = urlsplit(redis_url)
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            return fallback
        host = parsed.hostname
        if ":" in host:
            host = f"[{host}]"
        netloc = f"{host}:{parsed.port}" if parsed.port is not None else host
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, ""))
    except (TypeError, ValueError):
        return fallback


async def connect_redis():
    global redis_cmd, redis_blpop
    redis_cmd = aioredis.from_url(
        REDIS_URL, decode_responses=True, socket_timeout=REDIS_COMMAND_TIMEOUT
    )
    redis_blpop = aioredis.from_url(
        REDIS_URL, decode_responses=True, socket_timeout=BLPOP_SOCKET_TIMEOUT
    )
    # Verify connections
    await redis_cmd.ping()
    await redis_blpop.ping()
    log.info("redis_connected")


async def close_redis():
    global redis_cmd, redis_blpop
    for conn in (redis_cmd, redis_blpop):
        if conn:
            try:
                await conn.aclose()
            except Exception:
                pass
    redis_cmd = None
    redis_blpop = None


# ---- 3. Rate limiter (sliding window) ----

rate_timestamps: list[float] = []


async def wait_for_rate_limit():
    """Wait until rate limit window allows sending."""
    global rate_timestamps
    while True:
        now = time.time()
        rate_timestamps = [t for t in rate_timestamps if now - t < 60]
        if len(rate_timestamps) < RATE_LIMIT_PER_MINUTE:
            rate_timestamps.append(now)
            return
        oldest = rate_timestamps[0]
        wait_sec = 60 - (now - oldest) + 0.05  # +50ms buffer
        log.info("rate_limit_waiting account_id=%s wait_sec=%.1f", ACCOUNT_ID, wait_sec)
        await asyncio.sleep(wait_sec)


# ---- 4. Send lock (serial sends) ----

_send_lock = asyncio.Lock()


# ---- 5. Session state ----

class SessionState:
    def __init__(self):
        self.client: WebClient | None = None
        self.qr_code: str | None = None
        self.is_connected: bool = False
        self.initializing: bool = False
        self.last_activity: float = time.time()
        self.intentional_close: bool = False
        self.sync_state: str | None = None  # None, 'syncing', 'ready', 'failed'
        self.groups: list[dict] | None = None
        self.phone: str = ""
        self.ready_event: asyncio.Event = asyncio.Event()
        self.error: str | None = None
        self.connected_at: float = 0.0  # timestamp when session connected


session: SessionState | None = None
last_task_time: float = time.time()
consumer_running: bool = False
shutting_down: bool = False


# ---- 6. Session helpers ----

def session_dir() -> Path:
    return Path(SESSIONS_DIR) / str(ACCOUNT_ID)


def session_db_path() -> Path:
    return session_dir() / SESSION_NAME


def session_exists_on_disk() -> bool:
    """Return whether the account's PyMax session database exists.

    Phone metadata and unrelated files are intentionally not session indicators.
    """
    return session_db_path().is_file()


def _read_session_compatibility() -> tuple[bool, tuple[str, str] | None]:
    """Read session metadata without modifying the mounted SQLite database.

    The first result means a usable PyMax 2.x ``sessions`` row is present.  The
    optional pair is a legacy 1.x ``auth`` credential pair that PyMax can promote
    through its public ``ExtraConfig`` API.  Invalid files are simply treated as
    unauthenticated so the normal QR flow remains available.
    """
    database = session_db_path()
    if not database.is_file() or database.stat().st_size == 0:
        return False, None

    try:
        connection = sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
                )
            }
            if "sessions" in tables:
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(sessions)")
                }
                if {"token", "device_id", "phone"} <= columns:
                    row = connection.execute(
                        "SELECT token, device_id FROM sessions "
                        "WHERE token <> ? AND device_id <> ? LIMIT 1",
                        ("", ""),
                    ).fetchone()
                    if row:
                        return True, None
            if "auth" in tables:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(auth)")}
                if {"token", "device_id"} <= columns:
                    row = connection.execute(
                        "SELECT token, device_id FROM auth "
                        "WHERE token <> ? AND device_id <> ? LIMIT 1",
                        ("", ""),
                    ).fetchone()
                    if row:
                        return False, (str(row[0]), str(row[1]))
        finally:
            connection.close()
    except (OSError, sqlite3.Error):
        pass
    return False, None


def has_reusable_session() -> bool:
    v2_session, legacy_credentials = _read_session_compatibility()
    return v2_session or legacy_credentials is not None


def save_phone_to_disk(phone: str):
    """Persist phone number alongside session files for container restarts."""
    d = session_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "phone.txt").write_text(phone.strip())


def load_phone_from_disk() -> str:
    """Read previously saved phone number from session directory."""
    f = session_dir() / "phone.txt"
    if f.exists():
        return f.read_text().strip()
    return ""


def delete_session_files():
    d = session_dir()
    if d.exists():
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        log.info("session_files_deleted account_id=%s", ACCOUNT_ID)


# ---- 7. Group sync ----

async def start_group_sync():
    """Fetch groups from MAX messenger with retry logic."""
    global session

    INITIAL_DELAY = 30  # seconds
    SYNC_RETRY_DELAYS = [30, 60, 120]
    MAX_ATTEMPTS = len(SYNC_RETRY_DELAYS) + 1

    if not session or not session.client:
        return

    session.sync_state = "syncing"
    log.info("group_sync_start account_id=%s delay_sec=%d", ACCOUNT_ID, INITIAL_DELAY)
    await asyncio.sleep(INITIAL_DELAY)

    for attempt in range(MAX_ATTEMPTS):
        if not session or not session.is_connected:
            log.info("group_sync_aborted account_id=%s", ACCOUNT_ID)
            return

        try:
            log.info(
                "group_fetch_attempt account_id=%s attempt=%d max_attempts=%d",
                ACCOUNT_ID, attempt + 1, MAX_ATTEMPTS,
            )

            groups = _group_records(session.client.chats or [])
            marker: int | None = None
            while True:
                result = await session.client.fetch_chats(marker=marker)
                if not result:
                    break
                groups.update(_group_records(result))
                next_marker = _next_chat_marker(result, marker)
                if next_marker is None:
                    break
                marker = next_marker

            groups = list(groups.values())

            session.sync_state = "ready"
            session.groups = groups
            log.info("group_sync_complete account_id=%s count=%d", ACCOUNT_ID, len(groups))
            return

        except Exception as e:
            log.error(
                "group_fetch_failed account_id=%s attempt=%d max_attempts=%d error=%s",
                ACCOUNT_ID, attempt + 1, MAX_ATTEMPTS, str(e),
            )
            if attempt < len(SYNC_RETRY_DELAYS):
                delay = SYNC_RETRY_DELAYS[attempt]
                log.info("group_fetch_retry account_id=%s delay_sec=%d", ACCOUNT_ID, delay)
                await asyncio.sleep(delay)

    if session:
        session.sync_state = "failed"
        log.warning("group_sync_exhausted account_id=%s attempts=%d", ACCOUNT_ID, MAX_ATTEMPTS)


# ---- 8. Create pymax client ----

class WorkerQrProvider:
    """Capture a QR link for the authenticated worker API without logging it."""

    def __init__(self, state: SessionState):
        self.state = state

    async def show_qr(self, qr_url: str) -> None:
        self.state.qr_code = qr_url
        log.info("qr_captured account_id=%s", ACCOUNT_ID)


def _group_records(chats) -> dict[str, dict]:
    groups: dict[str, dict] = {}
    for chat in chats:
        if getattr(chat, "type", None) != ChatType.CHAT:
            continue
        chat_id = str(getattr(chat, "id", ""))
        if chat_id:
            groups[chat_id] = {"id": chat_id, "name": str(getattr(chat, "title", ""))}
    return groups


def _next_chat_marker(chats, marker: int | None) -> int | None:
    """Return the next strictly decreasing chat-page marker, if one exists."""
    timestamps: list[int] = []
    for chat in chats:
        try:
            timestamp = int(getattr(chat, "last_event_time", None))
        except (TypeError, ValueError):
            continue
        if timestamp > 0:
            timestamps.append(timestamp)

    if not timestamps:
        return None
    next_marker = min(timestamps) - 1
    if next_marker < 0 or (marker is not None and next_marker >= marker):
        return None
    return next_marker


async def create_client(phone: str = "") -> SessionState:
    """Create a WebClient, wire up event handlers, and start it."""
    global session

    work_dir = str(session_dir())
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    state = SessionState()
    state.phone = phone
    state.initializing = True

    # Phone remains Broadcaster metadata; QR-authenticated WebClient does not use it.
    if phone:
        save_phone_to_disk(phone)

    _, legacy_credentials = _read_session_compatibility()
    config_kwargs = {"reconnect": True, "log_level": LOG_LEVEL}
    if legacy_credentials:
        config_kwargs.update(token=legacy_credentials[0], device_id=legacy_credentials[1])
    client = WebClient(
        session_name=SESSION_NAME,
        work_dir=work_dir,
        extra_config=ExtraConfig(**config_kwargs),
        qr_provider=WorkerQrProvider(state),
    )
    state.client = client

    # pymax adds its own handlers during __init__; clear them so all output
    # goes through our root JSON formatter (no duplicate plain-text lines)
    for _name in ("pymax", "pymax.core"):
        _lg = logging.getLogger(_name)
        _lg.handlers.clear()
        _lg.propagate = True

    @client.on_start()
    async def on_start(connected_client):
        """Called when client is fully connected and ready."""
        state.is_connected = True
        state.initializing = False
        state.qr_code = None
        state.last_activity = time.time()
        state.connected_at = time.time()
        state.error = None
        state.ready_event.set()
        log.info("connected account_id=%s", ACCOUNT_ID)

        # Start background group sync
        if not state.sync_state or state.sync_state == "failed":
            state.sync_state = "ready"
            asyncio.create_task(_safe_group_sync())

    session = state

    # Start client in background task
    asyncio.create_task(_run_client(client, state))

    return state


async def _run_client(client: WebClient, state: SessionState):
    """Run WebClient.start() in the background and capture startup failures."""
    try:
        await client.start()
    except Exception as e:
        log.error("client_start_error account_id=%s error=%s", ACCOUNT_ID, str(e))
        state.is_connected = False
        state.initializing = False
        state.error = str(e)
        state.ready_event.set()  # unblock waiters with error


async def _safe_group_sync():
    """Wrapper for group sync that catches all exceptions."""
    try:
        await start_group_sync()
    except Exception as e:
        log.error("group_sync_error account_id=%s error=%s", ACCOUNT_ID, str(e))


# ---- 9. Destroy session ----

async def destroy_session():
    global session
    if session and session.client:
        session.intentional_close = True
        try:
            await session.client.close()
        except Exception as e:
            log.error("client_close_error account_id=%s error=%s", ACCOUNT_ID, str(e))
    session = None
    rate_timestamps.clear()
    delete_session_files()
    log.info("session_destroyed account_id=%s", ACCOUNT_ID)


# ---- 10. Send message ----

async def send_message(task: dict):
    """Send a message to a MAX group."""
    global session

    raw_group_id = task.get("group_external_id") or task.get("group_id")
    group_id = int(raw_group_id) if raw_group_id else None
    text = task.get("ad_text", "")
    images = task.get("ad_images") or task.get("image_urls") or []
    task_id = task.get("task_id", "unknown")

    # Wait for session if it's still initializing (e.g. autoload at startup)
    if session and not session.is_connected and session.initializing:
        log.info("waiting_for_session account_id=%s task_id=%s", ACCOUNT_ID, task_id)
        try:
            await asyncio.wait_for(session.ready_event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            raise RuntimeError("MAX session connect timeout")

    if not session or not session.is_connected or not session.client:
        raise RuntimeError("MAX session not available")

    # Grace period after fresh connection — MAX server needs time before uploads work
    STARTUP_GRACE_SEC = 10
    if session.connected_at:
        elapsed = time.time() - session.connected_at
        if elapsed < STARTUP_GRACE_SEC:
            wait = STARTUP_GRACE_SEC - elapsed
            log.info("startup_grace_wait account_id=%s task_id=%s wait=%.1f", ACCOUNT_ID, task_id, wait)
            await asyncio.sleep(wait)

    async with _send_lock:
        # Anti-ban: simulate composing delay
        typing_delay = 1.5 + random.random() * 2.5
        log.info(
            "anti_ban_delay account_id=%s task_id=%s group_id=%s delay=%.1f",
            ACCOUNT_ID, task_id, group_id, typing_delay,
        )
        await asyncio.sleep(typing_delay)

        temp_files: list[str] = []
        try:
            if images:
                log.info(
                    "sending_images account_id=%s task_id=%s group_id=%s image_count=%d text=%.50s",
                    ACCOUNT_ID, task_id, group_id, len(images), text,
                )

                # Download images to temp files
                attachments = []
                async with httpx.AsyncClient(timeout=30.0) as http:
                    for img_url in images:
                        try:
                            resp = await http.get(img_url)
                            resp.raise_for_status()

                            # Determine extension from content type
                            ct = resp.headers.get("content-type", "image/jpeg")
                            ext = ".jpg"
                            if "png" in ct:
                                ext = ".png"
                            elif "gif" in ct:
                                ext = ".gif"
                            elif "webp" in ct:
                                ext = ".webp"

                            tmp = tempfile.NamedTemporaryFile(
                                suffix=ext, delete=False, dir=tempfile.gettempdir()
                            )
                            tmp.write(resp.content)
                            tmp.close()
                            temp_files.append(tmp.name)
                            attachments.append(Photo(path=tmp.name))
                        except Exception as e:
                            log.warning(
                                "image_download_failed account_id=%s task_id=%s url=%s error=%s",
                                ACCOUNT_ID, task_id, img_url, str(e),
                            )

                if attachments:
                    # Send message with images as attachments
                    await session.client.send_message(
                        chat_id=group_id,
                        text=text,
                        attachments=attachments,
                    )
                elif text:
                    # All image downloads failed, send text only
                    await session.client.send_message(
                        chat_id=group_id,
                        text=text,
                    )

                log.info("send_result account_id=%s task_id=%s group_id=%s", ACCOUNT_ID, task_id, group_id)

            else:
                log.info(
                    "sending_text account_id=%s task_id=%s group_id=%s text=%.50s",
                    ACCOUNT_ID, task_id, group_id, text,
                )
                await session.client.send_message(
                    chat_id=group_id,
                    text=text,
                )
                log.info("send_result account_id=%s task_id=%s group_id=%s", ACCOUNT_ID, task_id, group_id)

        finally:
            # Cleanup temp files
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass

    if session:
        session.last_activity = time.time()


# ---- 11. Result publishing ----

async def publish_result(task: dict, status: str, error_message: str | None = None, no_retry: bool = False):
    """Publish task result to Redis."""
    result = {
        "task_id": task.get("task_id"),
        "account_id": task.get("account_id"),
        "ad_id": task.get("ad_id"),
        "group_id": task.get("group_id"),
        "schedule_id": task.get("schedule_id"),
        "user_id": task.get("user_id"),
        "status": status,
        "error_message": error_message,
        "no_retry": no_retry,
        "ad_title": task.get("ad_title"),
        "ad_text": task.get("ad_text"),
        "ad_images": task.get("ad_images") or [],
        "group_name": task.get("group_name"),
        "messenger_type": "max",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await redis_cmd.rpush(RESULTS_KEY, json.dumps(result, ensure_ascii=False))
        log.info("result_published account_id=%s task_id=%s status=%s", ACCOUNT_ID, task.get("task_id"), status)
    except Exception as e:
        log.error("result_publish_failed account_id=%s task_id=%s error=%s", ACCOUNT_ID, task.get("task_id"), str(e))


# ---- 12. Error classification ----

def is_no_retry_error(err_msg: str) -> bool:
    """Determine if an error is non-retryable."""
    err_lower = err_msg.lower()
    if "forbidden" in err_lower:
        return True
    # "session not available" is permanent, but "timeout waiting" is transient
    if "session not available" in err_lower and "timeout" not in err_lower:
        return True
    if "not a member" in err_lower:
        return True
    if "banned" in err_lower:
        return True
    return False


# ---- 13. Queue consumer — BLPOP loop with retry logic ----

async def process_task(task: dict):
    """Process a single task from the queue."""
    task_id = task.get("task_id", "unknown")
    group_id = task.get("group_external_id") or task.get("group_id")
    retry_count = task.get("_retry_count", 0)

    log.info(
        "task_processing account_id=%s task_id=%s group_id=%s retry=%d",
        ACCOUNT_ID, task_id, group_id, retry_count,
    )

    # Wait for rate limit window
    await wait_for_rate_limit()

    try:
        await send_message(task)
        await publish_result(task, "ok")
    except Exception as e:
        err_msg = str(e)
        log.error(
            "task_send_failed account_id=%s task_id=%s error=%s retry=%d",
            ACCOUNT_ID, task_id, err_msg, retry_count,
        )

        # Check for non-retryable errors
        if is_no_retry_error(err_msg):
            await publish_result(task, "fail", err_msg, no_retry=True)
            return

        # Retry logic: re-enqueue with incremented retry count
        if retry_count < MAX_RETRIES:
            delay_sec = RETRY_DELAYS[retry_count]
            log.info(
                "task_retry_scheduled account_id=%s task_id=%s next_retry=%d delay_sec=%d",
                ACCOUNT_ID, task_id, retry_count + 1, delay_sec,
            )
            task["_retry_count"] = retry_count + 1
            task["_delay_until"] = time.time() + delay_sec
            await redis_cmd.rpush(QUEUE_KEY, json.dumps(task, ensure_ascii=False))
        else:
            log.error(
                "task_retries_exhausted account_id=%s task_id=%s max_retries=%d",
                ACCOUNT_ID, task_id, MAX_RETRIES,
            )
            await publish_result(task, "fail", err_msg, no_retry=False)


async def start_consumer():
    """BLPOP consumer loop — runs until shutdown or idle timeout."""
    global consumer_running, last_task_time
    consumer_running = True
    log.info("consumer_started account_id=%s queue=%s", ACCOUNT_ID, QUEUE_KEY)

    while consumer_running:
        try:
            result = await redis_blpop.blpop(QUEUE_KEY, timeout=BLPOP_TIMEOUT)

            if result is None:
                # BLPOP returned None — timeout, check idle
                if IDLE_SHUTDOWN_SEC > 0:
                    idle_sec = time.time() - last_task_time
                    if idle_sec >= IDLE_SHUTDOWN_SEC:
                        log.info("idle_shutdown account_id=%s idle_sec=%d", ACCOUNT_ID, int(idle_sec))
                        await graceful_shutdown("idle")
                        return
                continue

            _, raw_task = result  # (key, value)
            last_task_time = time.time()

            try:
                task = json.loads(raw_task)
            except json.JSONDecodeError as e:
                log.error("task_parse_error account_id=%s error=%s raw=%.200s", ACCOUNT_ID, str(e), raw_task)
                continue

            # Check if task has a delay (retry scheduling)
            delay_until = task.get("_delay_until")
            if delay_until and time.time() < delay_until:
                # Not ready yet — re-enqueue at tail and continue
                await redis_cmd.rpush(QUEUE_KEY, raw_task)
                continue

            await process_task(task)

            # Update heartbeat after each task
            try:
                await write_heartbeat()
            except Exception:
                pass

        except Exception as e:
            if not consumer_running:
                break
            log.error("consumer_loop_error account_id=%s error=%s", ACCOUNT_ID, str(e))

            # Check idle even on errors
            if IDLE_SHUTDOWN_SEC > 0:
                idle_sec = time.time() - last_task_time
                if idle_sec >= IDLE_SHUTDOWN_SEC:
                    log.info("idle_shutdown_on_error account_id=%s idle_sec=%d", ACCOUNT_ID, int(idle_sec))
                    await graceful_shutdown("idle")
                    return

            # Pause before retrying
            await asyncio.sleep(5)


# ---- 14. Heartbeat ----

async def write_heartbeat():
    """Refresh the worker liveness record before its authoritative TTL expires."""
    if redis_cmd:
        await redis_cmd.set(
            HEARTBEAT_KEY,
            str(int(time.time() * 1000)),
            ex=HEARTBEAT_TTL_SEC,
        )


async def heartbeat_loop():
    """Send heartbeat to Redis every HEARTBEAT_INTERVAL_SEC."""
    while not shutting_down:
        try:
            await write_heartbeat()
        except Exception as e:
            log.error("heartbeat_error error=%s", str(e))
        await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)


# ---- 15. Graceful shutdown ----

async def graceful_shutdown(reason: str = "unknown"):
    global shutting_down, consumer_running, session
    if shutting_down:
        return
    shutting_down = True
    consumer_running = False

    log.info("shutdown_start account_id=%s reason=%s", ACCOUNT_ID, reason)

    # Clean up Redis keys
    try:
        if redis_cmd:
            await redis_cmd.delete(HEARTBEAT_KEY)
            await redis_cmd.delete(ENDPOINT_KEY)
            log.info("redis_keys_cleaned account_id=%s", ACCOUNT_ID)
    except Exception as e:
        log.error("redis_cleanup_error account_id=%s error=%s", ACCOUNT_ID, str(e))

    # Close PyMax client within a fixed budget; keep session files on disk.
    current_session = session
    try:
        if current_session and current_session.client:
            current_session.intentional_close = True
            try:
                await asyncio.wait_for(
                    current_session.client.close(), timeout=CLIENT_CLOSE_TIMEOUT_SEC
                )
                log.info("client_close_complete account_id=%s", ACCOUNT_ID)
            except TimeoutError:
                log.warning(
                    "client_close_timeout account_id=%s timeout_sec=%s",
                    ACCOUNT_ID,
                    CLIENT_CLOSE_TIMEOUT_SEC,
                )
            except Exception as e:
                log.error("client_close_error account_id=%s error=%s", ACCOUNT_ID, str(e))
    finally:
        session = None

    # Close Redis connections
    await close_redis()

    log.info("shutdown_complete account_id=%s reason=%s", ACCOUNT_ID, reason)

    # Exit process
    os._exit(0)


# ---- 16. Pydantic models ----

class StartSessionBody(BaseModel):
    phone: str


class SendMessageBody(BaseModel):
    group_id: str
    text: str = ""
    image_urls: list[str] = []
    trace_id: str | None = None


# ---- 17. FastAPI app with lifespan ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Startup
    await connect_redis()

    # Register endpoint in Redis
    hostname = socket.gethostname()
    endpoint = f"http://{hostname}:{PORT}"
    await redis_cmd.set(ENDPOINT_KEY, endpoint)
    log.info("endpoint_registered endpoint=%s key=%s", endpoint, ENDPOINT_KEY)

    # Set initial heartbeat
    await write_heartbeat()

    # Start heartbeat loop
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    # Auto-load session if it exists on disk
    phone = PHONE or load_phone_from_disk()
    if has_reusable_session():
        log.info("session_autoloading account_id=%s", ACCOUNT_ID)
        try:
            await create_client(phone)
        except Exception as e:
            log.error("session_autoload_failed account_id=%s error=%s", ACCOUNT_ID, str(e))

    # Start consumer loop as background task
    consumer_task = asyncio.create_task(start_consumer())

    yield

    # Shutdown
    await graceful_shutdown("lifespan_end")
    heartbeat_task.cancel()
    consumer_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="MAX Worker", lifespan=lifespan)


# ---- 18. HTTP API endpoints ----

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "account_id": ACCOUNT_ID,
        "connected": session.is_connected if session else False,
        "syncState": session.sync_state if session else None,
        "uptime_sec": int(time.time() - _start_time),
        "idle_sec": int(time.time() - last_task_time),
    }


@app.post("/api/sessions/{session_id}/start")
async def start_session(session_id: str, body: StartSessionBody):
    global session

    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if session:
        if session.is_connected:
            return {"status": "connected"}
        if session.initializing:
            return {"status": "initializing"}
        # Stale session — clean up
        try:
            if session.client:
                await session.client.close()
        except Exception:
            pass
        session = None

    try:
        await create_client(body.phone)
        return {"status": "initializing"}
    except Exception as e:
        log.error("session_start_failed account_id=%s error=%s", ACCOUNT_ID, str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    await destroy_session()
    return {"ok": True}


@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if not session:
        exists = session_exists_on_disk()
        return {"connected": False, "exists": exists, "syncState": None}

    return {
        "connected": session.is_connected,
        "exists": True,
        "syncState": session.sync_state,
    }


@app.get("/api/sessions/{session_id}/qr")
async def get_qr_code(session_id: str):
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if not session:
        return {"status": "not_found", "qr": None}
    if session.is_connected:
        return {"status": "connected", "qr": None}
    if not session.qr_code:
        return {"status": "waiting", "qr": None}
    return {"status": "pending", "qr": session.qr_code}


@app.get("/api/sessions/{session_id}/groups")
async def get_groups(session_id: str):
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if not session or not session.is_connected:
        return JSONResponse(
            status_code=503,
            content={"error": "MAX session not available"},
        )

    # Return cached groups if available
    if session.groups is not None:
        return session.groups

    # Try to fetch groups on-demand (deduplicate by id)
    try:
        return list(_group_records(session.client.chats or []).values())
    except Exception as e:
        log.error("groups_error account_id=%s error=%s", ACCOUNT_ID, str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/sessions/{session_id}/sync-status")
async def get_sync_status(session_id: str):
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if not session:
        if has_reusable_session():
            log.info("session_reloading account_id=%s", ACCOUNT_ID)
            try:
                state = await create_client(PHONE or load_phone_from_disk())
                # Wait briefly for connection
                try:
                    await asyncio.wait_for(state.ready_event.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    pass

                if state.is_connected and (not state.sync_state or state.sync_state == "failed"):
                    asyncio.create_task(_safe_group_sync())
                    return {"state": "syncing", "groups": None}
            except Exception as e:
                log.error("session_reload_failed account_id=%s error=%s", ACCOUNT_ID, str(e))

            if not session or not session.is_connected:
                return {"state": "unknown", "groups": None}
        else:
            return {"state": "not_found", "groups": None}

    return {
        "state": session.sync_state or "none",
        "groups": session.groups,
    }


@app.post("/api/sessions/{session_id}/retry-sync")
async def retry_sync(session_id: str):
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if not session or not session.is_connected:
        return JSONResponse(status_code=404, content={"error": "Session not connected"})

    if session.sync_state == "syncing":
        return {"status": "already_syncing"}

    session.sync_state = None
    session.groups = None
    asyncio.create_task(_safe_group_sync())

    return {"status": "sync_started"}


@app.post("/api/sessions/{session_id}/send")
async def send_endpoint(session_id: str, body: SendMessageBody):
    """Direct send endpoint (bypasses queue, for testing or immediate sends)."""
    if str(session_id) != str(ACCOUNT_ID):
        return JSONResponse(
            status_code=403,
            content={"error": f"This worker manages account {ACCOUNT_ID} only"},
        )

    if not session or not session.is_connected:
        return JSONResponse(
            status_code=503,
            content={"error": "MAX session not available"},
        )

    task = {
        "task_id": body.trace_id or f"direct-{int(time.time())}",
        "group_external_id": body.group_id,
        "ad_text": body.text,
        "ad_images": body.image_urls,
    }

    try:
        await wait_for_rate_limit()
        await send_message(task)
        return {"ok": True}
    except Exception as e:
        log.error("send_error account_id=%s error=%s", ACCOUNT_ID, str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})


# ---- 19. Signal handling ----

def _handle_signal(sig, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    reason = "SIGTERM" if sig == signal.SIGTERM else "SIGINT"
    log.info("signal_received signal=%s", reason)
    asyncio.get_event_loop().create_task(graceful_shutdown(reason))


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# ---- 20. Main entry point ----

_start_time = time.time()

if __name__ == "__main__":
    log.info(
        "worker_starting account_id=%s port=%d redis_url=%s idle_shutdown_sec=%d",
        ACCOUNT_ID, PORT, render_redis_url_for_log(REDIS_URL), IDLE_SHUTDOWN_SEC,
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        log_config=None,  # prevent uvicorn from overriding our JSON logging
    )

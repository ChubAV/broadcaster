"""Version-scoped compatibility shims for the audited PyMax 2.5.0.

The 2.3.1 shims for photo upload, CONTACT and STICKER attachments are gone: 2.5.0
fixed those defects itself (photos: the id comes from ``photos`` or ``photoIds`` and a
URL naming neither accepts exactly one result entry; CONTACT/STICKER: ``contactId`` and
``setId`` are optional).  The tests prove each on the untouched library.
"""

from __future__ import annotations

from pymax import __version__ as PYMAX_VERSION
from pymax.transport.websocket import WebSocketTransport


AUDITED_PYMAX_VERSION = "2.5.0"


def apply_websocket_frame_size_compatibility() -> bool:
    """Lift the 10 MiB WebSocket frame cap on the MAX login response.

    ``WebSocketTransport.connect`` passes ``max_size=1024 * 1024 * 10`` to
    ``websockets.asyncio.client.connect`` (2.3.1 left the 1 MiB library default).
    MAX sends the entire chat list inside the single login response frame, so the
    frame grows with the account: a large production account already measured
    2.7 MB, and one that outgrows the cap makes the peer close with 1009 "message
    too big" mid-login.  PyMax then reconnects and the worker spins in a permanent
    reconnect loop that never connects and never syncs groups.  The production
    worker runs without a cap today, so the shim keeps that behavior.

    Frames are read from MAX's own endpoint over TLS after a completed
    handshake, so removing the cap does not widen the trust boundary; the
    incoming payload is still parsed through PyMax's validated models.

    The replacement keeps the same ``Origin`` and the same proxy branch as 2.5.0
    and fails closed on any other PyMax version.
    """
    if getattr(WebSocketTransport, "_broadcaster_frame_size_patched", False):
        return False
    if PYMAX_VERSION != AUDITED_PYMAX_VERSION:
        raise RuntimeError(
            f"PyMax WebSocket frame size compatibility only supports "
            f"{AUDITED_PYMAX_VERSION}; found {PYMAX_VERSION}"
        )

    original_connect = WebSocketTransport.connect

    async def connect(self) -> None:
        from websockets import Origin
        from websockets.asyncio import client

        if self.proxy:
            self.ws = await client.connect(
                self.url,
                origin=Origin("https://web.max.ru"),
                proxy=self.proxy,
                max_size=None,
            )
        else:
            self.ws = await client.connect(
                self.url, origin=Origin("https://web.max.ru"), max_size=None
            )

    connect.__doc__ = original_connect.__doc__
    WebSocketTransport.connect = connect
    WebSocketTransport._broadcaster_frame_size_patched = True
    return True

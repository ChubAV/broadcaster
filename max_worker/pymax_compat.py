"""Version-scoped compatibility shims for the audited PyMax dependency."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from urllib.parse import parse_qs, quote, urlparse

import aiohttp
from pydantic import BaseModel, ValidationError

from pymax import __version__ as PYMAX_VERSION
from pymax.api.response import payload_item
from pymax.api.uploads.models import PhotoUploadResponse
from pymax.api.uploads.payloads import AttachPhotoPayload, UploadPayload
from pymax.api.uploads.service import UploadService
from pymax.exceptions import UploadError
from pymax.files import Photo
from pymax.logging import get_logger
from pymax.protocol import Opcode
from pymax.transport.websocket import WebSocketTransport
from pymax.types.domain.attachments import ContactAttachment, StickerAttachment
from pymax.types.domain.chat import Chat
from pymax.types.domain.login import LoginResponse
from pymax.types.domain.message import Message


AUDITED_PYMAX_VERSION = "2.3.1"

# Every schema that embeds the attachment tagged union.  Relaxing an attachment
# field is invisible until these are rebuilt.
_ATTACHMENT_UNION_SCHEMAS = (Message, Chat, LoginResponse)


def _relax_required_field(
    model: type[BaseModel], field_name: str, annotation: type | object, reason: str
) -> bool:
    """Make one required field optional in the audited PyMax release only.

    Returns whether this invocation applied the mutation.  An already-compatible
    upstream model is left untouched; an unreviewed incompatible release fails
    closed instead of widening the compatibility seam silently.
    """
    field = model.model_fields[field_name]
    if not field.is_required():
        return False
    if PYMAX_VERSION != AUDITED_PYMAX_VERSION:
        raise RuntimeError(
            f"PyMax {reason} compatibility only supports "
            f"{AUDITED_PYMAX_VERSION}; found incompatible required field in {PYMAX_VERSION}"
        )

    field.annotation = annotation
    field.default = None
    for schema in (model, *_ATTACHMENT_UNION_SCHEMAS):
        schema.model_rebuild(force=True)
    return True


def apply_contact_attachment_compatibility() -> bool:
    """Allow an absent CONTACT identifier in the audited PyMax release only.

    MAX sometimes emits a recognized CONTACT attachment without ``contactId``.
    PyMax 2.3.1 marks that field as required, causing nested Chat/LoginResponse
    parsing to fail before the worker can synchronize groups.
    """
    return _relax_required_field(ContactAttachment, "contact_id", int | None, "CONTACT")


def apply_sticker_attachment_compatibility() -> bool:
    """Allow an absent STICKER set identifier in the audited PyMax release only.

    MAX emits recognized STICKER attachments without ``setId`` (stickers that
    belong to no set).  PyMax 2.3.1 marks that field as required, so a single
    such sticker in a chat's ``lastMessage`` fails the whole ``Chat`` parse and
    aborts group synchronization.  Upstream fixed this in 2.4.0 by declaring the
    field ``int | None``; this reproduces that exact change on the audited
    release, so the shim can be dropped when the pin moves to 2.4.0+.
    """
    return _relax_required_field(StickerAttachment, "set_id", int | None, "STICKER")


def apply_websocket_frame_size_compatibility() -> bool:
    """Lift the 1 MiB WebSocket frame cap that truncates large MAX logins.

    ``WebSocketTransport.connect`` calls ``websockets.asyncio.client.connect``
    without ``max_size``, so the library default of 1 MiB applies.  MAX sends the
    entire chat list inside the single login response frame, so any account with
    enough chats or history exceeds that cap: the peer closes with 1009 "message
    too big" mid-login, PyMax reconnects, and the worker spins in a permanent
    reconnect loop that never connects and never syncs groups.  Small accounts
    stay under the cap, which is why only large accounts are affected.

    Frames are read from MAX's own endpoint over TLS after a completed
    handshake, so removing the cap does not widen the trust boundary; the
    incoming payload is still parsed through PyMax's validated models.
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


# PyMax's own upload logger, so the replacement logs exactly where 2.3.1 did.
_upload_logger = get_logger(UploadService.__module__)


def _resolve_photo_token(photo_id: str | None, model: PhotoUploadResponse) -> str:
    """Pick our photo's token out of the upload result.

    A URL that names the photo keeps PyMax 2.3.1's exact keyed lookup.  A URL that
    names none leaves only the result itself: every upload requests ``count=1``,
    so exactly one entry is our photo whatever its key, and any other count is
    ambiguous — refuse it rather than attach a guess.
    """
    logger = _upload_logger
    if photo_id is not None:
        try:
            return model.photos[photo_id].token
        except KeyError as e:
            logger.exception(
                "Photo upload response does not contain token for photo_id=%s",
                photo_id,
            )
            logger.debug("Photo upload model=%r", model)
            raise UploadError(
                f"Photo upload response does not contain token for photo_id={photo_id}"
            ) from e
        except Exception as e:
            logger.exception("Failed to extract photo token")
            logger.debug("Photo upload model=%r", model)
            raise UploadError("Failed to extract photo token") from e

    entries = list(model.photos.values())
    if len(entries) != 1:
        logger.error(
            "Photo upload response holds %s photo(s), expected exactly 1", len(entries)
        )
        logger.debug("Photo upload model=%r", model)
        raise UploadError(
            f"Photo upload response holds {len(entries)} photo(s), expected exactly 1"
        )
    return entries[0].token


async def _upload_photo(
    self: UploadService, photo: Photo, profile: bool = False
) -> AttachPhotoPayload:
    """PyMax 2.3.1 ``UploadService.upload_photo`` minus the hard ``photoIds`` lookup."""
    logger = _upload_logger
    logger.info("Uploading photo")
    logger.debug("Preparing photo upload payload")

    payload = UploadPayload(profile=profile).model_dump()

    try:
        data = await self.app.invoke(
            Opcode.PHOTO_UPLOAD,
            payload=payload,
        )
    except Exception as e:
        logger.exception("Failed to request photo upload URL")
        raise UploadError("Failed to request photo upload URL") from e

    try:
        url = payload_item(data, "url", str)
    except Exception as e:
        logger.exception("Failed to parse photo upload URL from response")
        raise UploadError("Failed to parse photo upload URL from response") from e

    if not url:
        logger.error("No upload URL received")
        logger.debug(
            "Photo upload URL response payload=%r",
            getattr(data, "payload", None),
        )
        raise UploadError("No upload URL received")

    logger.debug("Photo upload URL received")

    try:
        photo_ids = parse_qs(urlparse(url).query).get("photoIds", [])
    except Exception as e:
        logger.exception("Failed to parse photo id from upload URL")
        logger.debug("Invalid photo upload URL=%s", url)
        raise UploadError("Failed to parse photo id from upload URL") from e

    photo_id = str(photo_ids[0]) if photo_ids else None
    if photo_id is None:
        logger.debug("Photo upload URL names no photo; expecting a single-entry result")
    else:
        logger.debug("Photo upload id parsed photo_id=%s", photo_id)

    try:
        photo_data = photo.validate_photo()
    except Exception as e:
        logger.exception("Photo validation crashed")
        raise UploadError("Photo validation crashed") from e

    if not photo_data:
        logger.error("Photo validation failed")
        raise UploadError("Photo validation failed")

    logger.debug(
        "Photo validated extension=%s content_type=%s",
        photo_data[0],
        photo_data[1],
    )

    try:
        photo_bytes = await photo.read()
    except Exception as e:
        logger.exception("Failed to read photo bytes")
        raise UploadError("Failed to read photo bytes") from e

    logger.debug("Photo read complete size=%s", len(photo_bytes))

    form = aiohttp.FormData()
    form.add_field(
        name="file",
        value=photo_bytes,
        filename=f"image.{quote(photo_data[0])}",
        content_type=photo_data[1],
    )

    try:
        async with (
            aiohttp.ClientSession(proxy=self.app.config.proxy) as session,
            session.post(
                url=url,
                data=form,
            ) as response,
        ):
            logger.debug("Photo upload HTTP response status=%s", response.status)

            if response.status != HTTPStatus.OK:
                logger.error("Photo upload failed with status %s", response.status)
                raise UploadError(f"Photo upload failed with status {response.status}")

            try:
                result = await response.json()
            except Exception as e:
                logger.exception("Failed to decode photo upload response JSON")
                raise UploadError("Failed to decode photo upload response JSON") from e

    except UploadError:
        raise
    except aiohttp.ClientError as e:
        logger.exception("HTTP error during photo upload")
        raise UploadError("HTTP error during photo upload") from e
    except asyncio.TimeoutError as e:
        logger.exception("Timed out during photo upload")
        raise UploadError("Timed out during photo upload") from e
    except Exception as e:
        logger.exception("Unexpected error during photo upload")
        raise UploadError("Unexpected error during photo upload") from e

    try:
        model = PhotoUploadResponse.model_validate(result)
    except ValidationError as e:
        logger.exception("Invalid photo upload response model")
        logger.debug("Invalid photo upload response=%r", result)
        raise UploadError("Invalid photo upload response model") from e

    token = _resolve_photo_token(photo_id, model)

    logger.debug("Photo upload complete photo_id=%s", photo_id)
    return AttachPhotoPayload(photo_token=token)


def apply_photo_upload_compatibility() -> bool:
    """Upload photos to MAX's upload URLs that no longer carry ``photoIds``.

    Since 2026-09-25 (every request since 2026-10-02) MAX answers PHOTO_UPLOAD
    with a one-shot URL such as ``https://iu.oneme.ru/uploadImage?r=<token>``
    that names no photo.  PyMax 2.3.1 ``UploadService.upload_photo`` parses
    ``photoIds`` from that URL solely to key the POST result, so it raises
    ``UploadError("Photo upload URL does not contain photoIds")`` before a
    single byte is uploaded and every MAX send with an image fails.  PyMax
    2.4.1 keeps the same lookup; the fix exists only upstream as PyMax PR #107,
    so moving the pin does not help.

    The replacement is the 2.3.1 method unchanged except token resolution (see
    ``_resolve_photo_token``): a URL that still names the photo keeps the exact
    keyed lookup, since MAX rolled the change out gradually; a URL without it
    accepts only the single entry of the ``count=1`` result.  Drop this shim when
    the pin reaches a release that tolerates the missing parameter — the test
    ``test_unmodified_pymax_rejects_upload_url_without_photo_ids`` fails then.
    """
    if getattr(UploadService, "_broadcaster_photo_upload_patched", False):
        return False
    if PYMAX_VERSION != AUDITED_PYMAX_VERSION:
        raise RuntimeError(
            f"PyMax photo upload compatibility only supports "
            f"{AUDITED_PYMAX_VERSION}; found {PYMAX_VERSION}"
        )

    UploadService.upload_photo = _upload_photo
    UploadService._broadcaster_photo_upload_patched = True
    return True

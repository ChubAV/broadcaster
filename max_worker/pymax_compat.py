"""Version-scoped compatibility shims for the audited PyMax dependency."""

from __future__ import annotations

from pydantic import BaseModel

from pymax import __version__ as PYMAX_VERSION
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

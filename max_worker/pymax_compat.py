"""Version-scoped compatibility shims for the audited PyMax dependency."""

from __future__ import annotations

from pymax import __version__ as PYMAX_VERSION
from pymax.types.domain.attachments import ContactAttachment
from pymax.types.domain.chat import Chat
from pymax.types.domain.login import LoginResponse
from pymax.types.domain.message import Message


AUDITED_PYMAX_VERSION = "2.3.1"


def apply_contact_attachment_compatibility() -> bool:
    """Allow an absent CONTACT identifier in the audited PyMax release only.

    MAX sometimes emits a recognized CONTACT attachment without ``contactId``.
    PyMax 2.3.1 marks that field as required, causing nested Chat/LoginResponse
    parsing to fail before the worker can synchronize groups.  This adjusts only
    that field, then rebuilds every schema that captures the attachment union.

    Returns whether this invocation applied the mutation.  An already-compatible
    upstream model is left untouched; an unreviewed incompatible release fails
    closed instead of widening the compatibility seam silently.
    """
    contact_id = ContactAttachment.model_fields["contact_id"]
    if not contact_id.is_required():
        return False
    if PYMAX_VERSION != AUDITED_PYMAX_VERSION:
        raise RuntimeError(
            "PyMax CONTACT compatibility only supports "
            f"{AUDITED_PYMAX_VERSION}; found incompatible required field in {PYMAX_VERSION}"
        )

    contact_id.annotation = int | None
    contact_id.default = None
    for schema in (ContactAttachment, Message, Chat, LoginResponse):
        schema.model_rebuild(force=True)
    return True

"""Защита единственного писателя номера на исполнении (О-23 (а), свойство 3; D-07, D-13)."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from contextvars import ContextVar

from sqlalchemy import event

from app.models.messenger_account import MessengerAccount

# Колонки номера — те же две, что судит статический гейт писателя (`PHONE_COLUMNS`).
GUARDED_COLUMNS: tuple[str, ...] = ("phone", "phone_is_manual")

# Постоянный текст отказа: без значения колонки и без номера (D-11).
PHONE_WRITE_OUTSIDE_WRITER = (
    "колонки номера аккаунта пишет только app/application/accounts/phone.py (D-13)"
)


class PhoneWriteOutsideWriter(RuntimeError):
    """Запись колонки номера вне разрешения писателя `writer_scope()`."""


_WRITER_ACTIVE: ContextVar[bool] = ContextVar("phone_writer_active", default=False)


@contextlib.contextmanager
def writer_scope() -> Iterator[None]:
    """Разрешение писателя: внутри него запись колонок номера не отказывает.

    Снимается токеном в `finally` — и после исключения внутри (T-16-117).
    """
    token = _WRITER_ACTIVE.set(True)
    try:
        yield
    finally:
        _WRITER_ACTIVE.reset(token)


def _refuse_attribute_write(*args: object, **kwargs: object) -> None:
    """Слушатель `set` / `remove` / `modified` колонок номера."""
    if not _WRITER_ACTIVE.get():
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)


_GUARDED_ATTRIBUTES = (MessengerAccount.phone, MessengerAccount.phone_is_manual)
_ATTRIBUTE_EVENTS = ("set", "remove", "modified")

for _attribute in _GUARDED_ATTRIBUTES:
    for _event_name in _ATTRIBUTE_EVENTS:
        event.listen(_attribute, _event_name, _refuse_attribute_write)

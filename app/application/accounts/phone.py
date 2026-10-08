"""Единственный писатель номера телефона аккаунта (D-12) — заготовка RED.

Сигнатуры окончательные; тела — заготовки, которые GREEN заменит.
"""

from __future__ import annotations

import enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount


class PhoneWrite(enum.Enum):
    WRITTEN = "written"
    KEPT = "kept"
    UNPARSEABLE = "unparseable"


async def _fill_if_unknown(session: AsyncSession, account_id: int, e164: str) -> PhoneWrite:
    return PhoneWrite.KEPT


async def fill_reported_phone(session: AsyncSession, account_id: int, raw: object) -> PhoneWrite:
    return PhoneWrite.KEPT


async def record_reported_phone(
    session: AsyncSession, account: MessengerAccount, raw: object
) -> PhoneWrite:
    return PhoneWrite.KEPT


async def set_manual_phone(session: AsyncSession, account_id: int, text: str | None) -> str | None:
    return None

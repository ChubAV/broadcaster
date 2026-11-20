"""Подпись аккаунта на экранах (Фаза 17, D-06): заготовка RED, тела — в GREEN."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import NamedTuple

PHONE_UNKNOWN_TEXT = "Номер неизвестен"


class AccountRow(NamedTuple):
    id: int
    type: str
    phone: str | None


@dataclass(frozen=True, slots=True)
class AccountLabel:
    account_id: int
    channel: str
    phone_text: str | None
    twin: bool

    @property
    def text(self) -> str:
        return ""

    @property
    def plain(self) -> str:
        return ""

    @property
    def plain_with_id(self) -> str:
        return ""


def id_mark(account_id: int) -> str:
    return ""


def shown_phone(stored: str | None) -> str | None:
    return None


def row_of(account: object) -> AccountRow:
    return AccountRow(account.id, account.type, account.phone)  # type: ignore[attr-defined]


def label_of(subject: AccountRow, rows: Iterable[AccountRow]) -> AccountLabel:
    return AccountLabel(subject.id, subject.type, None, False)


def build_labels(rows: Iterable[AccountRow]) -> dict[int, AccountLabel]:
    return {}


def labels_for(accounts: Iterable[object]) -> dict[int, AccountLabel]:
    return {}

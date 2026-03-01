from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AccountInfo:
    id: int
    type: str
    status: str
    created_at: datetime


@dataclass(slots=True)
class SyncStatusView:
    status: str
    group_count: int | None = None
    messenger_type: str | None = None


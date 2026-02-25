from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.unit_of_work import AbstractUnitOfWork
from app.application.accounts.dto import AccountInfo, SyncStatusView
from app.models.group import Group
from app.models.messenger_account import MessengerAccount


@dataclass(slots=True)
class AccountLifecycleService:
    """Доменные правила для жизненного цикла messenger-аккаунтов."""

    @staticmethod
    def can_start_wa_connect(existing_active_or_syncing: bool) -> bool:
        return not existing_active_or_syncing


async def list_accounts_for_user(session: AsyncSession, user_id: int) -> Sequence[AccountInfo]:
    result = await session.execute(
        select(MessengerAccount)
        .where(MessengerAccount.user_id == user_id)
        .order_by(MessengerAccount.id)
    )
    accounts = result.scalars().all()
    return [
        AccountInfo(
            id=a.id,
            type=a.type,
            status=a.status,
            created_at=a.created_at,
        )
        for a in accounts
    ]


async def get_sync_status_view(session: AsyncSession, user_id: int, account_id: int) -> SyncStatusView | None:
    result = await session.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return None

    if account.status == "active":
        group_result = await session.execute(
            select(Group.id).where(
                Group.account_id == account_id,
                Group.user_id == user_id,
            )
        )
        group_count = len(group_result.all())
        return SyncStatusView(status="active", group_count=group_count)

    if account.status == "sync_failed":
        return SyncStatusView(status="sync_failed")

    if account.status == "syncing":
        return SyncStatusView(status="syncing")

    return SyncStatusView(status="other")


async def delete_account(session: AsyncSession, user_id: int, account_id: int) -> bool:
    result = await session.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return False
    await session.delete(account)
    await session.commit()
    return True


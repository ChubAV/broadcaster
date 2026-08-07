from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.unit_of_work import AbstractUnitOfWork
from app.application.accounts.dto import AccountInfo, SyncStatusView
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule


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
        return SyncStatusView(status="active", group_count=group_count, messenger_type=account.type)

    if account.status == "sync_failed":
        return SyncStatusView(status="sync_failed", messenger_type=account.type)

    if account.status == "syncing":
        return SyncStatusView(status="syncing", messenger_type=account.type)

    return SyncStatusView(status="other", messenger_type=account.type)


async def detach_schedules_from_account(session: AsyncSession, account_id: int) -> int:
    """Отвязывает расписания от удаляемого messenger-аккаунта.

    Расписания НЕ удаляются вместе с аккаунтом (issue #35): они сохраняются,
    переводятся в статус «приостановлено» (is_active=False, next_run_at=None)
    и отвязываются от аккаунта (account_id=None). Пользователь может привязать
    новый аккаунт на форме редактирования и возобновить расписание.

    Не коммитит: транзакцией владеет вызывающая сторона, чтобы отвязка и
    удаление аккаунта попали в одну транзакцию.

    Возвращает количество отвязанных расписаний.
    """
    result = await session.execute(
        update(Schedule)
        .where(Schedule.account_id == account_id)
        .values(is_active=False, next_run_at=None, account_id=None)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount or 0


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
    await detach_schedules_from_account(session, account.id)
    await session.delete(account)
    await session.commit()
    return True


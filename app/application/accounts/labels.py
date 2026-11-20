"""Загрузчик строк аккаунтов пользователя для подписи (Фаза 17): заготовка RED."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.account_label import AccountRow


async def load_account_rows(session: AsyncSession, user_id: int) -> list[AccountRow]:
    return []

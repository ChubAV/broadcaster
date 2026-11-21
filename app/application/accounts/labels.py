"""Строки аккаунтов пользователя для подписи (Фаза 17, D-14, D-18).

ЗАЧЕМ МОДУЛЬ. Одна карта «аккаунты пользователя» нужна порциям списка и
истории, фрагменту опроса, экрану групп аккаунта и CSV. Признак двойника
(D-03) считается по ВСЕМ аккаунтам пользователя, поэтому карта читается ПО
ПОЛЬЗОВАТЕЛЮ, а не по `IN (id порции)`: порция из трёх записей увидела бы
двух «неизвестных» двойниками, а следующая — нет, и один и тот же аккаунт
читался бы на экранах по-разному.

ПОЧЕМУ ПРОЕКЦИЯ ЧЕТЫРЁХ КОЛОНОК. `AccountRepository.list_by_user` поднимает
полные ORM-объекты вместе с учётными данными и строкой сессии Telegram — ради
значений, нужных подписи. Здесь читаются только `id`, `type`, `phone` и
`phone_is_manual`; четвёртая — признак ручного номера для пометки «указан
вручную» (Фаза 18, D-10).

ЖИВОЙ АККАУНТ — СТРОКА, КОТОРАЯ СУЩЕСТВУЕТ: флага мягкого удаления в модели
нет, а строки `connecting` / `disconnected` — видимые карточки и входят в счёт
двойников.

Номер модуль только читает: не пишет в колонку (писатель один, Фаза 16) и не
передаёт ни номер, ни подпись в вызовы журнала (D-08).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_account import MessengerAccount
from app.services.account_label import AccountRow


async def load_account_rows(session: AsyncSession, user_id: int) -> list[AccountRow]:
    """Все аккаунты пользователя любого статуса — одной инструкцией, четырьмя колонками."""
    result = await session.execute(
        select(
            MessengerAccount.id,
            MessengerAccount.type,
            MessengerAccount.phone,
            MessengerAccount.phone_is_manual,
        ).where(MessengerAccount.user_id == user_id)
    )
    return [AccountRow(*row) for row in result.all()]

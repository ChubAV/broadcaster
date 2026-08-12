from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("messenger_accounts.id", ondelete="CASCADE")
    )
    messenger_type: Mapped[str] = mapped_column(String(20))
    group_external_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # D-11: «не найдена при последней синхронизации». NULL означает «найдена»;
    # колонку ставит и снимает ТОЛЬКО синхронизация. Группа, не вернувшаяся из
    # мессенджера, помечается, но НЕ удаляется: удаление остаётся решением
    # пользователя.
    #
    # Колонка отдельная, а `last_error`/`error_at` выше НЕ переиспользуются:
    # те про ошибки ОТПРАВКИ (app/application/scheduling/use_cases.py). Общая
    # пара колонок на две разные семантики означала бы, что успешный синк
    # затирает диагностику неудавшейся рассылки, и наоборот.
    missing_since: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

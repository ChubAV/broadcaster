from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    # ОДНА АКТИВНАЯ ПОДПИСКА НА ПОЛЬЗОВАТЕЛЯ — СВОЙСТВО СХЕМЫ (ревизия 0018).
    #
    # Объявление живёт ЗДЕСЬ ТОЖЕ, а не только в ревизии: тестовая суита строит
    # схему через `Base.metadata.create_all` и о существовании Alembic не знает.
    # Ограничение, объявленное лишь в ревизии, суитой не проверялось бы вовсе.
    #
    # Индекс ЧАСТИЧНЫЙ: запрещена вторая АКТИВНАЯ строка, а не вторая строка
    # вообще — деактивированные строки истории подписок пользователя не запирают.
    __table_args__ = (
        Index(
            "uq_subscriptions_active_user",
            "user_id",
            unique=True,
            sqlite_where=text("is_active"),
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    plan: Mapped[str] = mapped_column(String(50), default="free")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

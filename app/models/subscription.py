from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, func, text
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
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Признак бесплатного доступа, назначаемого администратором (ревизия 0020).
    #
    # ЧИТАТЕЛЕЙ У НЕГО ПОКА НЕТ, И ЭТО ПОРЯДОК РАБОТ, А НЕ ЗАБЫВЧИВОСТЬ. Колонка
    # заводится вместе с необратимой правкой схемы, потому что она её часть;
    # предикат доступа, шелл и админский тумблер вводит план `05.1-09`.
    #
    # Умолчание ЛОЖНО у обеих сторон — и у Python, и у СУБД. Разойдись они, строка,
    # вставленная в обход ORM (а именно так её вставляет ревизия популяции без
    # подписки), получила бы другой ответ, чем строка, вставленная приложением.
    has_free_access: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

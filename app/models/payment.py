from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    yookassa_payment_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    amount_value: Mapped[str] = mapped_column(String(50))
    amount_currency: Mapped[str] = mapped_column(String(10), default="RUB")
    # ПРЕДМЕТ ПОКУПКИ ХРАНИТСЯ СВОЕЙ КОЛОНКОЙ, а не выводится из заполненности
    # соседних полей. Обработчик вебхука решает по ней, что выдать, и решение
    # обязано опираться на строку СВОЕЙ базы, а не на `metadata` уведомления:
    # уведомление приезжает извне (T-05-02).
    #
    # String, а не sa.Enum: причина выписана в app/constants.py:24-27 —
    # именованный тип PostgreSQL потребовал бы отдельного шага в downgrade
    # каждой ревизии, и прецедента в проекте нет.
    kind: Mapped[str] = mapped_column(String(50), default="package")
    plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # NULL с появлением подписок: у платежа за тариф сообщений не покупается
    # вовсе, и ноль здесь читался бы как «куплено ноль сообщений».
    messages_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

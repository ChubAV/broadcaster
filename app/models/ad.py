from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import AD_STATUS_PUBLISHED
from app.database import Base


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    images: Mapped[list] = mapped_column(JSON, default=list)
    # D-02: черновик или опубликовано. Умолчание — «опубликовано»: черновиком
    # объявление становится только явным действием пользователя, иначе созданное
    # объявление молча перестало бы отправляться по существующим расписаниям.
    # server_default дублирует default не для симметрии, а ради ревизии 0013:
    # им же заполняются строки, существовавшие до ввода колонки.
    status: Mapped[str] = mapped_column(
        String(20),
        default=AD_STATUS_PUBLISHED,
        server_default=AD_STATUS_PUBLISHED,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

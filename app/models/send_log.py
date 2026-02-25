from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SendLog(Base):
    __tablename__ = "send_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Snapshots
    ad_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ad_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ad_images: Mapped[list | None] = mapped_column(JSON, nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    messenger_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

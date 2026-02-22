from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_id: Mapped[int] = mapped_column(
        ForeignKey("ads.id", ondelete="CASCADE")
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("messenger_accounts.id", ondelete="CASCADE")
    )

    # Relationships for eager loading
    ad = relationship("Ad", lazy="raise")
    account = relationship("MessengerAccount", lazy="raise")

    group_ids: Mapped[list] = mapped_column(JSON, default=list)
    days_of_week: Mapped[list] = mapped_column(JSON, default=list)
    times_of_day: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GroupInfo(Base):
    __tablename__ = "group_info"
    __table_args__ = (
        UniqueConstraint("messenger_type", "external_id", name="uq_group_info_type_ext_id"),
        Index("ix_group_info_messenger_type", "messenger_type"),
        Index("ix_group_info_external_id", "external_id"),
        Index("ix_group_info_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    messenger_type: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    member_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admin_contacts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

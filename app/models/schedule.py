from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ⚠️ ЕДИНСТВЕННОЕ МЕСТО, ГДЕ СЛОВО «НЕВОЗМОЖНО» ПРАВДИВО.
#
# Включённое расписание без момента следующего запуска МЕРТВО НАВСЕГДА И МОЛЧА.
# Отбор к отправке фильтрует `is_active = true AND next_run_at <= now`, а в SQL
# `NULL <= now` не истинно НИКОГДА — строка не выбирается; единственная же ветка,
# которая `next_run_at` ПЕРЕСЧИТЫВАЕТ, живёт ВНУТРИ цикла по уже выбранным
# строкам, то есть на невыбираемой не выполняется тоже. Починить себя такой
# строке нечем, сводка инцидентов ищет ПРОСРОЧЕННЫЕ и потому её не видит, а
# пользователю она показывается ВКЛЮЧЁННОЙ.
#
# Семь прикладных мест записи держат этот инвариант (D-08 + WR-06), но
# прикладная проверка делает состояние НЕДОСТИЖИМЫМ ЧЕРЕЗ ПРИЛОЖЕНИЕ, а не
# НЕВОЗМОЖНЫМ: прямой psql, ручной UPDATE на бою, миграция данных и любой
# будущий восьмой писатель обходят все семь разом. Довод тот же, что в шапке
# ревизии 0021, и он не про платежи, а про класс.
#
# ЗАПРЕЩЕНА РОВНО ОДНА ПАРА ИЗ ЧЕТЫРЁХ. Законны: выключенное без момента
# (обычнейшее состояние — тумблер обнуляет момент), выключенное с сохранённым
# моментом, включённое с моментом.
#
# ⚠️ ГРАНИЦА: О ЗАПОЛНЕННОСТИ (D-08) ОГРАНИЧЕНИЕ НЕ ЗНАЕТ НИЧЕГО и не должно.
# Строка с пустыми группами, выключенная и без момента, для него законна.
# Полноту стерегут входы, схема стережёт одно: включённому расписанию нельзя
# быть без момента, в который оно сработает.
#
# Текст условия ДОСЛОВНО повторён в ревизии `0022` строкой — ревизия по правилу
# проекта не импортирует из `app.*`, потому что описывает схему на СВОЙ момент
# времени. Совпадение двух половин проверяется тестами, а не подразумевается:
# tests/test_models/test_schedule_active_requires_next_run.py и
# tests/test_migrations/test_0022_schedules_active_requires_next_run.py.
ACTIVE_REQUIRES_NEXT_RUN = "NOT (is_active AND next_run_at IS NULL)"
ACTIVE_REQUIRES_NEXT_RUN_NAME = "ck_schedules_active_requires_next_run"


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint(
            ACTIVE_REQUIRES_NEXT_RUN,
            name=ACTIVE_REQUIRES_NEXT_RUN_NAME,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_id: Mapped[int] = mapped_column(
        ForeignKey("ads.id", ondelete="CASCADE")
    )
    # Nullable: при удалении messenger-аккаунта расписание сохраняется и
    # отвязывается (issue #35), а не удаляется каскадом.
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("messenger_accounts.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships for eager loading
    ad = relationship("Ad", lazy="raise")
    account = relationship("MessengerAccount", lazy="raise")

    group_ids: Mapped[list] = mapped_column(JSON, default=list)
    days_of_week: Mapped[list] = mapped_column(JSON, default=list)
    times_of_day: Mapped[list] = mapped_column(JSON, default=list)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", server_default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

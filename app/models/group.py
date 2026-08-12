from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    # Одна строка на одну группу мессенджера внутри аккаунта — гарантия уровня
    # СХЕМЫ, а не порядка вызовов.
    #
    # Без неё два одновременных POST /accounts/{id}/sync-groups читали
    # одинаковый пустой состав, оба делали INSERT для одного и того же
    # внешнего идентификатора, и в таблице появлялись две строки на одну
    # группу: обе видны на экране, обе выбираемы в расписаниях, а выбор обеих
    # означал две отправки в один чат. Прикладной guard такую гонку закрыть не
    # может в принципе — между чтением и записью всегда есть окно.
    #
    # Побочно снимается второй дефект: `apply_group_resync` строит словарь
    # существующих групп по `group_external_id`, поэтому при уже имевшихся
    # дублях одна из строк навсегда выпадала из обработки — её имя не
    # обновлялось и пометка пропажи на неё не ставилась.
    #
    # Гонка теперь заканчивается IntegrityError на коммите одного из двух
    # запросов. Это осознанный размен: редкая пятисотка на повторном нажатии
    # честнее молчаливого дубля, который пользователь обнаружит по двойной
    # отправке рекламы.
    __table_args__ = (
        UniqueConstraint(
            "account_id", "group_external_id", name="uq_groups_account_external"
        ),
    )

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

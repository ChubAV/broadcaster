"""ads.status вместо ads.is_active

Объявление получает состояние «черновик» / «опубликовано» вместо булева флага
активности (D-02). Существующие записи мигрируют в опубликованное состояние:
их заполняет server_default, отдельного UPDATE для этого не требуется — тот же
приём, что в ревизии 0003.

Ревизия снимает колонку с боевыми данными. Это необратимый шаг, принятый
пользователем осознанно; см. комментарий над downgrade.

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"

# Литералы выписаны здесь, а не импортированы из app.constants: ревизия обязана
# описывать схему на СВОЙ момент времени. Импорт связал бы уже применённую
# миграцию с текущим кодом, и переименование константы задним числом изменило
# бы смысл давно выполненного шага.
STATUS_PUBLISHED = "published"


def upgrade():
    op.add_column(
        "ads",
        sa.Column(
            "status",
            sa.String(20),
            server_default=STATUS_PUBLISHED,
            nullable=False,
        ),
    )
    op.create_index("ix_ads_status", "ads", ["status"])
    op.drop_column("ads", "is_active")


def downgrade():
    # ВНИМАНИЕ: откат необратимо теряет данные. Колонка is_active возвращается,
    # но не её значения: какое объявление было черновиком, восстановить
    # неоткуда — состояние хранилось в снимаемой колонке status, а
    # server_default возвращает ВСЕ строки активными. Потеря принята
    # пользователем в D-02 вместе с самой ревизией (T-02-16); альтернатива —
    # держать мёртвую колонку вечно.
    op.add_column(
        "ads",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.drop_index("ix_ads_status", table_name="ads")
    op.drop_column("ads", "status")

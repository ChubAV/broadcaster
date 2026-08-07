"""schedules.account_id nullable + ON DELETE SET NULL

При удалении messenger-аккаунта расписание должно сохраняться и переходить
в статус «приостановлено», а не удаляться каскадом (issue #35).

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"

FK_FALLBACK_NAME = "schedules_account_id_fkey"


def _account_id_fk_name(bind) -> str:
    for fk in sa.inspect(bind).get_foreign_keys("schedules"):
        if fk.get("constrained_columns") == ["account_id"]:
            return fk.get("name") or FK_FALLBACK_NAME
    return FK_FALLBACK_NAME


def upgrade():
    bind = op.get_bind()

    op.alter_column(
        "schedules",
        "account_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # Смена правила внешнего ключа поддерживается только на PostgreSQL
    # (прод по alembic.ini). На прочих диалектах шаг пропускается, чтобы
    # миграция оставалась импортируемой и применимой.
    if bind.dialect.name == "postgresql":
        fk_name = _account_id_fk_name(bind)
        op.drop_constraint(fk_name, "schedules", type_="foreignkey")
        op.create_foreign_key(
            fk_name,
            "schedules",
            "messenger_accounts",
            ["account_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    # ВНИМАНИЕ: откат необратимо теряет данные. Расписания, отвязанные от
    # удалённого аккаунта (account_id IS NULL), невозможно снова привязать —
    # аккаунта уже не существует, поэтому такие строки удаляются, чтобы
    # восстановить ограничение NOT NULL.
    bind = op.get_bind()

    op.execute("DELETE FROM schedules WHERE account_id IS NULL")

    if bind.dialect.name == "postgresql":
        fk_name = _account_id_fk_name(bind)
        op.drop_constraint(fk_name, "schedules", type_="foreignkey")
        op.create_foreign_key(
            fk_name,
            "schedules",
            "messenger_accounts",
            ["account_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.alter_column(
        "schedules",
        "account_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

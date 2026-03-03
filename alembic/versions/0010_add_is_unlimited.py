"""add is_unlimited to message_balances

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"


def upgrade():
    op.add_column(
        "message_balances",
        sa.Column("is_unlimited", sa.Boolean, nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("message_balances", "is_unlimited")

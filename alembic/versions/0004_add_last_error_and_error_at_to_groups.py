"""add last_error and error_at to groups

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "groups",
        sa.Column("error_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("groups", "error_at")
    op.drop_column("groups", "last_error")

"""add schedule timezone

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "schedules",
        sa.Column("timezone", sa.String(length=50), server_default="UTC", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("schedules", "timezone")

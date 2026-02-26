"""add task_id to send_log

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("send_logs", sa.Column("task_id", sa.String(50), nullable=True))
    op.create_index(op.f("ix_send_logs_task_id"), "send_logs", ["task_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_send_logs_task_id"), table_name="send_logs")
    op.drop_column("send_logs", "task_id")

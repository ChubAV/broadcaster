"""add scaling indexes

Revision ID: 56167f76bf64
Revises: a2f85de3c13c
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "56167f76bf64"
down_revision: Union[str, None] = "a2f85de3c13c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_schedules_is_active"), "schedules", ["is_active"])
    op.create_index(op.f("ix_schedules_next_run_at"), "schedules", ["next_run_at"])
    op.create_index(op.f("ix_send_logs_sent_at"), "send_logs", ["sent_at"])
    op.create_index(op.f("ix_ads_user_id"), "ads", ["user_id"])
    op.create_index(op.f("ix_groups_user_id"), "groups", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_groups_user_id"), table_name="groups")
    op.drop_index(op.f("ix_ads_user_id"), table_name="ads")
    op.drop_index(op.f("ix_send_logs_sent_at"), table_name="send_logs")
    op.drop_index(op.f("ix_schedules_next_run_at"), table_name="schedules")
    op.drop_index(op.f("ix_schedules_is_active"), table_name="schedules")

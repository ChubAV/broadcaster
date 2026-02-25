"""sendlog remove fk add snapshots

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column("send_logs", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("send_logs", sa.Column("ad_title", sa.String(255), nullable=True))
    op.add_column("send_logs", sa.Column("ad_text", sa.Text(), nullable=True))
    op.add_column("send_logs", sa.Column("ad_images", sa.JSON(), nullable=True))
    op.add_column("send_logs", sa.Column("group_name", sa.String(255), nullable=True))
    op.add_column("send_logs", sa.Column("messenger_type", sa.String(20), nullable=True))

    # Backfill existing records from related tables
    op.execute("""
        UPDATE send_logs SET
            user_id = ads.user_id,
            ad_title = ads.title,
            ad_text = ads.text,
            ad_images = ads.images,
            group_name = groups.name,
            messenger_type = groups.messenger_type
        FROM ads, groups
        WHERE send_logs.ad_id = ads.id
          AND send_logs.group_id = groups.id
    """)

    # Set user_id=0 for any orphaned records that couldn't be backfilled
    op.execute("UPDATE send_logs SET user_id = 0 WHERE user_id IS NULL")

    # Make user_id non-nullable and add index
    op.alter_column("send_logs", "user_id", nullable=False)
    op.create_index("ix_send_logs_user_id", "send_logs", ["user_id"])

    # Drop foreign key constraints
    op.drop_constraint("send_logs_schedule_id_fkey", "send_logs", type_="foreignkey")
    op.drop_constraint("send_logs_ad_id_fkey", "send_logs", type_="foreignkey")
    op.drop_constraint("send_logs_group_id_fkey", "send_logs", type_="foreignkey")

    # Make id columns nullable
    op.alter_column("send_logs", "schedule_id", nullable=True)
    op.alter_column("send_logs", "ad_id", nullable=True)
    op.alter_column("send_logs", "group_id", nullable=True)


def downgrade() -> None:
    # Make id columns non-nullable (set NULLs to 0 first)
    op.execute("UPDATE send_logs SET schedule_id = 0 WHERE schedule_id IS NULL")
    op.execute("UPDATE send_logs SET ad_id = 0 WHERE ad_id IS NULL")
    op.execute("UPDATE send_logs SET group_id = 0 WHERE group_id IS NULL")
    op.alter_column("send_logs", "schedule_id", nullable=False)
    op.alter_column("send_logs", "ad_id", nullable=False)
    op.alter_column("send_logs", "group_id", nullable=False)

    # Recreate foreign key constraints
    op.create_foreign_key(
        "send_logs_schedule_id_fkey", "send_logs", "schedules",
        ["schedule_id"], ["id"], ondelete="CASCADE",
    )
    op.create_foreign_key(
        "send_logs_ad_id_fkey", "send_logs", "ads",
        ["ad_id"], ["id"], ondelete="CASCADE",
    )
    op.create_foreign_key(
        "send_logs_group_id_fkey", "send_logs", "groups",
        ["group_id"], ["id"], ondelete="CASCADE",
    )

    # Drop new columns
    op.drop_index("ix_send_logs_user_id", "send_logs")
    op.drop_column("send_logs", "messenger_type")
    op.drop_column("send_logs", "group_name")
    op.drop_column("send_logs", "ad_images")
    op.drop_column("send_logs", "ad_text")
    op.drop_column("send_logs", "ad_title")
    op.drop_column("send_logs", "user_id")

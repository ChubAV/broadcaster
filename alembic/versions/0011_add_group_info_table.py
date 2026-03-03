"""add group_info reference table

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"


def upgrade():
    op.create_table(
        "group_info",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("messenger_type", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("member_count", sa.Integer, nullable=True),
        sa.Column("admin_contacts", sa.JSON, nullable=True),
        sa.Column("raw_metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("messenger_type", "external_id", name="uq_group_info_type_ext_id"),
    )
    op.create_index("ix_group_info_messenger_type", "group_info", ["messenger_type"])
    op.create_index("ix_group_info_external_id", "group_info", ["external_id"])
    op.create_index("ix_group_info_name", "group_info", ["name"])


def downgrade():
    op.drop_index("ix_group_info_name", table_name="group_info")
    op.drop_index("ix_group_info_external_id", table_name="group_info")
    op.drop_index("ix_group_info_messenger_type", table_name="group_info")
    op.drop_table("group_info")

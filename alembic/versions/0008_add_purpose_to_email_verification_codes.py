"""add purpose to email_verification_codes

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"

def upgrade():
    op.add_column(
        "email_verification_codes",
        sa.Column("purpose", sa.String(20), nullable=False, server_default="registration"),
    )

def downgrade():
    op.drop_column("email_verification_codes", "purpose")

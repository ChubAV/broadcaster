"""initial schema

Revision ID: 9857e720ea27
Revises:
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9857e720ea27"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Initial schema already exists in database.
    pass


def downgrade() -> None:
    pass

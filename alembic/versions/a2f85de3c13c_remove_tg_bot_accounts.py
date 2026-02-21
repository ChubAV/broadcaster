"""remove tg_bot accounts

Revision ID: a2f85de3c13c
Revises: ff10bc66a187
Create Date: 2026-02-21 12:55:58.427919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2f85de3c13c'
down_revision: Union[str, Sequence[str], None] = 'ff10bc66a187'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM messenger_accounts WHERE type = 'tg_bot'")


def downgrade() -> None:
    pass  # Cannot restore deleted data

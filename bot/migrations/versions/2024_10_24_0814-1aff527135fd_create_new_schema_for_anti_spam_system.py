"""create new schema for anti spam system

Revision ID: 1aff527135fd
Revises: 702d8ae5acc2
Create Date: 2024-10-24 08:14:05.728005+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1aff527135fd'
down_revision: Union[str, None] = '702d8ae5acc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS anti_spam")


def downgrade() -> None:
   op.execute("DROP SCHEMA IF EXISTS anti_spam")
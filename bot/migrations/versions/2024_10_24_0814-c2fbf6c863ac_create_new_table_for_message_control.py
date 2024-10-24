"""create new table for message control

Revision ID: c2fbf6c863ac
Revises: 1aff527135fd
Create Date: 2024-10-24 08:14:26.200117+00:00

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2fbf6c863ac'
down_revision: Union[str, None] = '1aff527135fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'message_control',
        sa.Column('id', sa.Integer),
        sa.Column('user_id', sa.BigInteger),
        sa.Column('created_at', sa.DateTime, default=datetime.now()),
        sa.PrimaryKeyConstraint('id', name='const_id_primary'),
        if_not_exists=True,
        schema='anti_spam'
    )


def downgrade() -> None:
    op.drop_table(
        'message_controll', 
        if_exists=True, 
        schema='anti_spam'
    )
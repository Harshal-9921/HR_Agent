"""add checkbox_label to content

Revision ID: c1a2b3d4e5f6
Revises: 5470a4f1a0af
Create Date: 2026-09-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5470a4f1a0af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('contents', sa.Column('checkbox_label', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('contents', 'checkbox_label')
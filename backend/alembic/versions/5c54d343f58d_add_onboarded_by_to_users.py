"""add onboarded_by to users

Revision ID: 5c54d343f58d
Revises: 2e18300b9b94
Create Date: 2026-08-11 14:31:33.005935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c54d343f58d'
down_revision: Union[str, Sequence[str], None] = '2e18300b9b94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('onboarded_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'users', ['onboarded_by'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'onboarded_by')
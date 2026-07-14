"""merge heads

Revision ID: 2e18300b9b94
Revises: 000c9060865e, ae27e355c17a
Create Date: 2026-07-14 14:24:20.533684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e18300b9b94'
down_revision: Union[str, Sequence[str], None] = ('000c9060865e', 'ae27e355c17a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

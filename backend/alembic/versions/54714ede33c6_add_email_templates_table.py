"""add email_templates table

Revision ID: 54714ede33c6
Revises: 5c54d343f58d
Create Date: 2026-08-13 12:38:32.228285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54714ede33c6'
down_revision: Union[str, Sequence[str], None] = '5c54d343f58d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('email_templates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('template_key', sa.String(), nullable=True),
    sa.Column('subject', sa.String(), nullable=True),
    sa.Column('html_body', sa.String(), nullable=True),
    sa.Column('updated_at', sa.String(), nullable=True),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_templates_id'), 'email_templates', ['id'], unique=False)
    op.create_index(op.f('ix_email_templates_template_key'), 'email_templates', ['template_key'], unique=True)
    # Idempotent — safe whether this column already exists (VM) or not (local)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_archived BOOLEAN")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_archived")
    op.drop_index(op.f('ix_email_templates_template_key'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_id'), table_name='email_templates')
    op.drop_table('email_templates')
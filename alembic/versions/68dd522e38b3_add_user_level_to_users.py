"""add_user_level_to_users

Revision ID: 68dd522e38b3
Revises: 62d845603bb4
Create Date: 2025-12-05 04:15:24.611797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68dd522e38b3'
down_revision: Union[str, None] = '62d845603bb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_level column with default value of 10
    # SQLite doesn't support ALTER COLUMN, so we keep the server_default
    # Check if column already exists (in case of partial migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'user_level' not in columns:
        op.add_column('users', sa.Column('user_level', sa.Integer(), nullable=False, server_default='10'))


def downgrade() -> None:
    op.drop_column('users', 'user_level')

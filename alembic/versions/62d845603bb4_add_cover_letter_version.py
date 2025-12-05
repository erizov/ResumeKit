"""add_cover_letter_version

Revision ID: 62d845603bb4
Revises: 09348e9a293d
Create Date: 2025-12-05 02:04:40.866079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62d845603bb4'
down_revision: Union[str, None] = '09348e9a293d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add version column to tailored_cover_letters table
    op.add_column(
        "tailored_cover_letters",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_tailored_cover_letters_version",
        "tailored_cover_letters",
        ["version"],
    )


def downgrade() -> None:
    # Remove version column
    op.drop_index(
        "ix_tailored_cover_letters_version", table_name="tailored_cover_letters"
    )
    op.drop_column("tailored_cover_letters", "version")

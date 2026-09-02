"""documents pseudonyms

Revision ID: 793407435cd8
Revises: a1c9f3d0e214
Create Date: 2026-09-02 21:06:49.988332

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '793407435cd8'
down_revision: str | None = 'a1c9f3d0e214'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'documents',
        sa.Column(
            'pseudonyms',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{}',
        ),
    )


def downgrade() -> None:
    op.drop_column('documents', 'pseudonyms')

"""palabras / consumo

Revision ID: d3760b82d628
Revises: 793407435cd8
Create Date: 2026-09-02 22:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd3760b82d628'
down_revision: str | None = '793407435cd8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'plans', sa.Column('palabras_mes', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'plans', sa.Column('palabras_max_doc', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'usage', sa.Column('palabras_count', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'documents', sa.Column('palabras', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'analyses',
        sa.Column('costo_estimado', sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column('analyses', 'costo_estimado')
    op.drop_column('documents', 'palabras')
    op.drop_column('usage', 'palabras_count')
    op.drop_column('plans', 'palabras_max_doc')
    op.drop_column('plans', 'palabras_mes')

"""access requests + mfa columns

Revision ID: a1c9f3d0e214
Revises: f88ee93bc697
Create Date: 2026-09-02 17:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1c9f3d0e214'
down_revision: str | None = 'f88ee93bc697'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'users', sa.Column('mfa_secret_enc', sa.Text(), nullable=False, server_default='')
    )
    op.add_column(
        'users',
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('users', 'mfa_secret_enc', server_default=None)
    op.alter_column('users', 'mfa_enabled', server_default=None)

    op.create_table(
        'access_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('organizacion', sa.String(length=255), nullable=False),
        sa.Column('telefono', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('motivo', sa.Text(), nullable=False, server_default=''),
        sa.Column(
            'status',
            sa.Enum('pending', 'approved', 'rejected', name='access_request_status'),
            nullable=False,
            server_default='pending',
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by', sa.UUID(), nullable=True),
        sa.Column('org_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_access_requests_email'), 'access_requests', ['email'])
    op.create_index(op.f('ix_access_requests_status'), 'access_requests', ['status'])


def downgrade() -> None:
    op.drop_index(op.f('ix_access_requests_status'), table_name='access_requests')
    op.drop_index(op.f('ix_access_requests_email'), table_name='access_requests')
    op.drop_table('access_requests')
    op.execute('DROP TYPE IF EXISTS access_request_status')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'mfa_secret_enc')

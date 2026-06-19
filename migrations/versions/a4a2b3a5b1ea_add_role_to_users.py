"""Add role to users

Revision ID: a4a2b3a5b1ea
Revises: 936f24dd2639
Create Date: 2026-06-19 00:14:53.204002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4a2b3a5b1ea'
down_revision: Union[str, Sequence[str], None] = '936f24dd2639'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    userrole = sa.Enum('admin', 'user', name='userrole')
    userrole.create(op.get_bind())

    op.add_column('users', sa.Column('role', userrole, nullable=False, server_default='user'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
    sa.Enum(name='userrole').drop(op.get_bind())

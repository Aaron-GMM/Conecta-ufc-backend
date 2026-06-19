"""add_coordenador_e_descricao

Revision ID: c8db64319122
Revises: f100442d357b
Create Date: 2026-06-19 09:06:15.197825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8db64319122'
down_revision: Union[str, Sequence[str], None] = 'f100442d357b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('oportunidades') as batch_op:
        batch_op.add_column(sa.Column('coordenador', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('descricao', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('oportunidades') as batch_op:
        batch_op.drop_column('descricao')
        batch_op.drop_column('coordenador')

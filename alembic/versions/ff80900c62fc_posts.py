"""posts

Revision ID: ff80900c62fc
Revises: 6a004e993943
Create Date: 2024-04-21 16:30:11.743378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff80900c62fc'
down_revision: Union[str, None] = '6a004e993943'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""empty message

Revision ID: b0dc5576e4a3
Revises: 5528e3ad3416
Create Date: 2025-06-09 18:49:39.791578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0dc5576e4a3'
down_revision: Union[str, None] = '5528e3ad3416'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

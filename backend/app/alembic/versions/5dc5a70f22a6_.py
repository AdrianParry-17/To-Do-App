"""empty message

Revision ID: 5dc5a70f22a6
Revises: b0dc5576e4a3
Create Date: 2025-06-10 08:49:38.734183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dc5a70f22a6'
down_revision: Union[str, None] = 'b0dc5576e4a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

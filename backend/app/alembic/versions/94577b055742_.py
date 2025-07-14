"""empty message

Revision ID: 94577b055742
Revises: 29fab9763fa9
Create Date: 2025-06-10 14:13:05.339582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94577b055742'
down_revision: Union[str, None] = '29fab9763fa9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""empty message

Revision ID: 29fab9763fa9
Revises: 5dc5a70f22a6
Create Date: 2025-06-10 14:11:39.272127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29fab9763fa9'
down_revision: Union[str, None] = '5dc5a70f22a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

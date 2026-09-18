"""enforce execution fill order reference

Revision ID: 3f6ac3ffd14d
Revises: 62972371275e
Create Date: <GENERATED_DATE>
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3f6ac3ffd14d'
down_revision: Union[str, Sequence[str], None] = "62972371275e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "execution_fills",
        "execution_order_id",
        existing_type=sa.UUID(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "execution_fills",
        "execution_order_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
"""add dataset type

Revision ID: a18df4d998c0
Revises: 21b83a4260cf
Create Date: 2026-09-27 11:47:19.259414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a18df4d998c0'
down_revision: Union[str, Sequence[str], None] = '21b83a4260cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column(
            "dataset_type",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE datasets 
        SET dataset_type = 'execution'
        WHERE dataset_type IS NULL
        """
    )

    op.alter_column(
        "datasets",
        "dataset_type",
        nullable=False,
    )

    op.create_index(
        op.f("ix_datasets_dataset_type"),
        "datasets",
        ["dataset_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_datasets_dataset_type"),
        table_name="datasets",
    )

    op.drop_column(
        "datasets",
        "dataset_type",
    )
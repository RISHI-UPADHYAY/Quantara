"""add reproducibility fields to analysis runs

Revision ID: af2f3784f6f5
Revises: ead65f8c2b53
Create Date: 2026-10-08 14:03:31.400502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "af2f3784f6f5"
down_revision: Union[str, Sequence[str], None] = "ead65f8c2b53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "analysis_runs",
        sa.Column(
            "research_workspace_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.add_column(
        "analysis_runs",
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "analysis_runs",
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "analysis_runs",
        sa.Column(
            "reproduced_from_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_analysis_runs_research_workspace_id",
        "analysis_runs",
        "research_workspaces",
        ["research_workspace_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_analysis_runs_reproduced_from_id",
        "analysis_runs",
        "analysis_runs",
        ["reproduced_from_id"],
        ["id"],
    )

    op.create_index(
        "ix_analysis_runs_research_workspace_id",
        "analysis_runs",
        ["research_workspace_id"],
        unique=False,
    )

    op.create_index(
        "ix_analysis_runs_reproduced_from_id",
        "analysis_runs",
        ["reproduced_from_id"],
        unique=False,
    )

    op.execute(
        """
        UPDATE analysis_runs
        SET configuration = '{}'::jsonb
        WHERE configuration IS NULL
        """
    )

    op.execute(
        """
        UPDATE analysis_runs
        SET provenance = '{}'::jsonb
        WHERE provenance IS NULL
        """
    )

    op.alter_column(
        "analysis_runs",
        "configuration",
        nullable=False,
    )

    op.alter_column(
        "analysis_runs",
        "provenance",
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_analysis_runs_reproduced_from_id",
        table_name="analysis_runs",
    )

    op.drop_index(
        "ix_analysis_runs_research_workspace_id",
        table_name="analysis_runs",
    )

    op.drop_constraint(
        "fk_analysis_runs_reproduced_from_id",
        "analysis_runs",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_analysis_runs_research_workspace_id",
        "analysis_runs",
        type_="foreignkey",
    )

    op.drop_column(
        "analysis_runs",
        "reproduced_from_id",
    )

    op.drop_column(
        "analysis_runs",
        "provenance",
    )

    op.drop_column(
        "analysis_runs",
        "configuration",
    )

    op.drop_column(
        "analysis_runs",
        "research_workspace_id",
    )